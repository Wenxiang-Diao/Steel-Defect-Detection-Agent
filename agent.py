from pathlib import Path
from visual_tool.dseg_adapter import inspect_steel_folder
from visual_tool.dseg_adapter import inspect_steel_image
from rag_results_detect import retrieve_rag_entries
from report_tool import generate_report


def inspect_single_image(image_path):
    image_path = Path(image_path)

    visual_result = inspect_steel_image(
        str(image_path)
    )
    rag_entries = retrieve_rag_entries(
        visual_result
    )

    report = generate_report(
        visual_result,
        rag_entries,
    )

    return {
        "visual_result": visual_result,
        "rag_entries": rag_entries,
        "report": report,
    }

def run_agent(task):
    #image_path = Path(task["image_path"])
    input_folder = Path(task['input_folder'])
#    result_folder = Path(task['result_folder'])

    visual_results = inspect_steel_folder(str(input_folder))

    inspection_results = []

    for visual_result in visual_results:
        rag_entries = retrieve_rag_entries(visual_result)
        report = generate_report(
            visual_result,
            rag_entries,
        )

        inspection_results.append({
            "visual_result": visual_result,
            "rag_entries": rag_entries,
            "report": report,
        })

    return {
        "task_type": "inspect_steel_folder",
        "total": len(inspection_results),
        "results": inspection_results,
    }