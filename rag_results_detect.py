import json
from pathlib import Path


RAG_DIR = Path(__file__).resolve().parent / "rag"

DEFECT_KNOWLEDGE_FILE = RAG_DIR / "defect_knowledge.json"
QUALITY_RULES_FILE = RAG_DIR / "rag_quality_rule.json"


def load_json(file_path):
    return json.loads(file_path.read_text(encoding="utf-8"))


def retrieve_rag_entries(visual_result):
    defect_knowledge = load_json(DEFECT_KNOWLEDGE_FILE)
    quality_rules = load_json(QUALITY_RULES_FILE)

    results = []

    for defect in visual_result.get("defects", []):
        defect_type = str(
            defect.get("defect_type", "")
        ).strip().lower()

        knowledge = defect_knowledge.get(defect_type)
        rule = quality_rules.get(defect_type)

        results.append({
            "defect_type": defect_type,
            "defect_knowledge": knowledge,
            "quality_rule": rule,
            "matched": knowledge is not None and rule is not None,
        })

    return results