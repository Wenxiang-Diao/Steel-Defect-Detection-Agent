import json
import math
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent / "rag"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _matches(area, band):
    lower = area >= band["min"] if band["include_min"] else area > band["min"]
    upper = area <= band["max"] if band["include_max"] else area < band["max"]
    return lower and upper


def retrieve_rag_entries(visual_result):
    if not isinstance(visual_result, dict):
        raise TypeError("需要单张图片的视觉结果字典")
    defects = visual_result.get("defects")
    if not isinstance(defects, list):
        raise ValueError("defects必须是列表")
    if visual_result.get("success") is False:
        raise ValueError("视觉检测失败")
    if not isinstance(visual_result.get("has_defect"), bool):
        raise ValueError("缺少有效的has_defect")
    if visual_result["has_defect"] != bool(defects):
        raise ValueError("has_defect与defects不一致")
    if not defects:
        total = visual_result.get("overall_area_ratio")
        if isinstance(total, bool) or not isinstance(total, (int, float)) or total != 0:
            raise ValueError("无缺陷结果的overall_area_ratio必须为0")
        return []

    knowledge = load_json(RAG_DIR / "defect_knowledge.json")
    rules = load_json(RAG_DIR / "rag_quality_rule.json")
    results = []
    for defect in defects:
        if not isinstance(defect, dict):
            raise ValueError("缺陷条目必须是字典")
        kind = str(defect.get("defect_type", "")).strip().lower()
        area = defect.get("area_ratio")
        info = knowledge.get(kind)
        category = rules["classes"].get(kind)
        errors = []
        if not info or not category:
            errors.append("缺陷知识或质检规则未匹配")
        valid = (
            not isinstance(area, bool) and isinstance(area, (int, float))
            and math.isfinite(area) and 0 < area <= 1
        )
        if not valid:
            errors.append("面积占比必须为大于0且不超过1的有限数值")
        bands = [b for b in rules["bands"] if _matches(area, b)] if valid else []
        if valid and len(bands) != 1:
            errors.append("面积区间未命中或规则区间重叠")
        band = bands[0] if len(bands) == 1 and not errors else None
        reason = "；".join(errors) if errors else band["review_reason"]
        interval = ""
        if band:
            left = "≤" if band["include_min"] else "<"
            right = "≤" if band["include_max"] else "<"
            interval = f'{band["min"]:.2%} {left} 面积占比 {right} {band["max"]:.2%}'
        results.append({
            "defect_type": kind,
            "defect_knowledge": info,
            "matched": bool(info and category),
            "quality_rule": {
                "rule_id": category["rule_id"] if category else None,
                "rule_version": rules["version"],
                "level": band["id"] if band else "unknown",
                "matched_interval": interval,
                "recommendation": band["recommendation"] if band else "REVIEW",
                "manual_review_required": bool(reason),
                "manual_review_reason": reason,
                "action": band["action"] if band else "核对输入数据及知识库配置后重新检测。",
            },
        })
    return results
