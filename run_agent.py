from pprint import pprint

from agent import run_agent


task = {
    "task_type": "inspect_steel_folder",
    "input_folder": "inputs",
}

agent_result = run_agent(task)

print(f"共完成 {agent_result['total']} 张图片")

for item in agent_result["results"]:
    print(
        f"\n图片："
        f"{item['visual_result']['image_path']}"
    )
    pprint(
        item["report"],
        sort_dicts=False,
    )