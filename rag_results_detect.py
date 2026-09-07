import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
RULE_FILE = PROJECT_ROOT / "rag" / "rag_quality_rule.md"
VISUAL_RESULTS_DIR = PROJECT_ROOT / "visual_results"
RAG_RESULTS_DIR = PROJECT_ROOT / "rag_results"

RISK_ORDER = {
    "none": 0,
    "unknown": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
}


def calculate_risk(area_ratio):
    if area_ratio is None:
        return "unknown"

    area_ratio = float(area_ratio)

    if area_ratio < 0.01:
        return "low"
    if area_ratio <= 0.05:
        return "medium"
    return "high"


def load_rule_sections():
    text = RULE_FILE.read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))

    sections = {}

    for index, heading in enumerate(headings):
        title = heading.group(1).strip().lower()
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)

        sections[title] = text[start:end].strip()

    return sections


def build_rag_result(visual_result, rules):
    matched_rules = []

    for defect in visual_result.get("defects", []):
        defect_type = str(defect.get("defect_type", "")).strip().lower()
        rule_content = rules.get(defect_type)

        matched_rules.append({
            "defect_type": defect_type,
            "class_id": defect.get("class_id"),
            "area_ratio": defect.get("area_ratio"),
            "location": defect.get("location"),
            "risk_level": calculate_risk(defect.get("area_ratio")),
            "rule_found": rule_content is not None,
            "rag_content": rule_content or "未找到对应的质检规则",
        })

    overall_risk = max(
        (item["risk_level"] for item in matched_rules),
        key=lambda level: RISK_ORDER[level],
        default="none",
    )

    return {
        "retrieval_success": True,
        "overall_risk_level": overall_risk,
        "severity_rules": rules.get("严重程度规则", ""),
        "matched_rules": matched_rules,
        "rule_source": RULE_FILE.name,
    }


def main():
    rules = load_rule_sections()
    visual_files = sorted(VISUAL_RESULTS_DIR.glob("*_visual.json"))

    for visual_file in visual_files:
        visual_result = json.loads(
            visual_file.read_text(encoding="utf-8")
        )

        if visual_result.get("success", True):
            rag_result = build_rag_result(visual_result, rules)
        else:
            rag_result = {
                "retrieval_success": False,
                "reason": "视觉检测失败，因此没有查询质检规则",
                "matched_rules": [],
            }

        output = {
            "visual_result": visual_result,
            "rag_result": rag_result,
        }

        output_name = visual_file.name.replace(
            "_visual.json",
            "_rag.json",
        )
        output_path = RAG_RESULTS_DIR / output_name

        output_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"已生成：{output_path}")

    print(f"处理完成，共生成 {len(visual_files)} 个 RAG 结果")


if __name__ == "__main__":
    main()