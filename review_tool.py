import json
import uuid
from datetime import datetime
from pathlib import Path


REPORT_DIR = (
    Path(__file__).resolve().parent
    / "reports"
)


def save_reviewed_report(
    agent_result,
    reviewer_decision,
    reviewer_comment,
):
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_id = str(uuid.uuid4())

    final_report = {
        "report_id": report_id,
        "created_at": datetime.now().isoformat(),
        "visual_result": agent_result["visual_result"],
        "rag_entries": agent_result["rag_entries"],
        "ai_report": agent_result["report"],
        "human_review": {
            "decision": reviewer_decision,
            "comment": reviewer_comment,
        },
    }

    output_path = (
        REPORT_DIR / f"{report_id}.json"
    )

    output_path.write_text(
        json.dumps(
            final_report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "report_id": report_id,
        "report_path": str(output_path),
        "final_report": final_report,
    }
