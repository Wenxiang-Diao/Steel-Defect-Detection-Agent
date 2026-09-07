from visual_tool.dseg_adapter import inspect_steel_image
from rag_results_detect import retrieve_rag_entries


visual_result = inspect_steel_image("inputs/test_1.jpg")
rag_entries = retrieve_rag_entries(visual_result)

print(rag_entries)