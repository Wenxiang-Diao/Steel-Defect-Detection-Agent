import math

def finalize_report(report, visual_result, rag_entries):
    if not isinstance(report, dict):
        raise ValueError("报告必须是JSON对象")
    defects = visual_result["defects"]
    if len(defects) != len(rag_entries):
        raise ValueError("视觉结果与RAG条目数量不一致")
    generated = report.get("defects", [])
    if not isinstance(generated, list):
        generated = []
    items, corrections = [], []
    for index, (visual, entry) in enumerate(zip(defects, rag_entries)):
        kind = str(visual["defect_type"]).strip().lower()
        if entry["defect_type"] != kind:
            raise ValueError("视觉结果与RAG类别顺序不一致")
        rule = entry["quality_rule"]
        area = visual.get("area_ratio")
        numeric = (
            isinstance(area, (int, float)) and not isinstance(area, bool)
            and math.isfinite(area)
        )
        if rule["level"] == "unknown":
            basis = rule["manual_review_reason"]
        else:
            basis = (
                f'依据{rule["rule_id"]}，面积占比{area * 100:.4f}%，'
                f'命中{rule["matched_interval"]}，等级为{rule["level"]}，'
                f'建议{rule["recommendation"]}。'
            )
        source = generated[index] if index < len(generated) else {}
        if not isinstance(source, dict) or source.get("defect_type") != kind:
            source = {}
        knowledge = entry.get("defect_knowledge") or {}
        fallback = knowledge.get("definition", "缺陷知识未匹配。")
        item = {
            "defect_type": visual["defect_type"],
            "defect_level": rule["level"],
            "area_ratio": area if numeric else None,
            "description": source.get("description") or fallback,
            "rule_basis": basis,
            "ai_recommendation": rule["recommendation"],
            "manual_review_required": rule["manual_review_required"],
            "manual_review_reason": rule["manual_review_reason"],
            "recommended_action": rule["action"],
        }
        if any(source.get(key) != item[key] for key in
               ("defect_level", "area_ratio", "ai_recommendation",
                "manual_review_required")):
            corrections.append(kind)
        items.append(item)
    reasons = [
        f'{x["defect_type"]}：{x["manual_review_reason"]}'
        for x in items if x["manual_review_required"]
    ]
    decision = "REVIEW" if reasons else (
        "FAIL" if any(x["ai_recommendation"] == "FAIL" for x in items) else "PASS"
    )
    return {
        "ai_recommendation": decision,
        "manual_review_required": bool(reasons),
        "manual_review_reason": "；".join(reasons),
        "human_confirmation_required": True,
        "evaluation_scope": "表面图像面积覆盖评价，不代表整件产品合格认证。",
        "defects": items,
        "overall_recommended_action": "；".join(
            f'{x["defect_type"]}：{x["recommended_action"]}' for x in items
        ) or "未检出目标类别缺陷，保留检测记录。",
        "warnings": [
            f'{x["defect_type"]}：{x["manual_review_reason"]}'
            for x in items if x["defect_level"] == "unknown"
        ],
        "validation": {"corrected_defects": corrections},
    }
