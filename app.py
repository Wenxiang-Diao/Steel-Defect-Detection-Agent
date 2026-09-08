import tempfile
import uuid
from pathlib import Path

import streamlit as st

from agent import inspect_single_image
from review_tool import save_reviewed_report


DECISION_NAMES = {
    "REVIEW": "待复核",
    "PASS": "通过",
    "FAIL": "不通过",
}


def reset_batch():
    for key in list(st.session_state):
        if key.startswith(("decision_", "comment_")):
            del st.session_state[key]

    uploaded_files = st.session_state.get("uploaded_images") or []

    st.session_state["images"] = [
        {
            "image_id": uuid.uuid4().hex,
            "original_name": file.name,
            "image_bytes": file.getvalue(),
            "status": "pending",
            "agent_result": None,
            "error": None,
            "review_decision": "REVIEW",
            "review_comment": "",
            "saved_report": None,
        }
        for file in uploaded_files
    ]

    st.session_state["image_index"] = 0


def move_image(offset):
    st.session_state["image_index"] += offset


def remember_review(image_id):
    item = next(
        image
        for image in st.session_state["images"]
        if image["image_id"] == image_id
    )

    item["review_decision"] = st.session_state[
        f"decision_{image_id}"
    ]
    item["review_comment"] = st.session_state[
        f"comment_{image_id}"
    ]


def detect_all(images):
    progress = st.progress(0)
    status_text = st.empty()

    for item in images:
        item.update(
            status="pending",
            agent_result=None,
            error=None,
            review_decision="REVIEW",
            review_comment="",
            saved_report=None,
        )

        st.session_state.pop(
            f"decision_{item['image_id']}", None
        )
        st.session_state.pop(
            f"comment_{item['image_id']}", None
        )

    for index, item in enumerate(images, start=1):
        item["status"] = "running"
        status_text.info(
            f"正在识别 {index}/{len(images)}："
            f"{item['original_name']}"
        )

        image_path = None

        try:
            suffix = Path(item["original_name"]).suffix

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temporary_file:
                temporary_file.write(item["image_bytes"])
                image_path = temporary_file.name

            result = inspect_single_image(image_path)

            result["image_id"] = item["image_id"]
            result["original_name"] = item["original_name"]

            item["agent_result"] = result
            item["status"] = "success"

        except Exception as error:
            item["status"] = "failed"
            item["error"] = str(error)

        finally:
            if image_path is not None:
                Path(image_path).unlink(missing_ok=True)

        progress.progress(index / len(images))

    successful = sum(
        item["status"] == "success" for item in images
    )

    status_text.info(
        f"识别完成：成功 {successful} 张，"
        f"失败 {len(images) - successful} 张"
    )


st.set_page_config(
    page_title="钢板表面智能质检",
    layout="wide",
)

st.title("钢板表面智能质检 Agent")

if "images" not in st.session_state:
    st.session_state["images"] = []
    st.session_state["image_index"] = 0

st.file_uploader(
    "上传一张或多张钢板表面图片",
    type=["jpg", "jpeg", "png", "bmp"],
    accept_multiple_files=True,
    key="uploaded_images",
    on_change=reset_batch,
)

st.caption("更改上传列表会建立新批次，请先保存需要保留的复核报告。")

images = st.session_state["images"]

if not images:
    st.info("请先上传图片。")
    st.stop()

if st.button(
    f"开始识别全部图片（{len(images)}张）",
    type="primary",
):
    detect_all(images)

st.divider()

if len(images) > 1:
    previous, position, following = st.columns([1, 2, 1])

    current_index = st.session_state["image_index"]

    previous.button(
        "上一张",
        on_click=move_image,
        args=(-1,),
        disabled=current_index == 0,
    )

    position.write(
        f"第 {current_index + 1} / {len(images)} 张"
    )

    following.button(
        "下一张",
        on_click=move_image,
        args=(1,),
        disabled=current_index == len(images) - 1,
    )

    st.select_slider(
        "切换图片",
        options=list(range(len(images))),
        format_func=lambda index: (
            f"{index + 1} · {images[index]['original_name']}"
        ),
        key="image_index",
    )

item = images[st.session_state["image_index"]]
image_id = item["image_id"]

st.image(item["image_bytes"], width=700)
st.caption(f"图片名称：{item['original_name']}")

if item["status"] == "pending":
    st.info("该图片尚未识别，请点击上方识别按钮。")
    st.stop()

if item["status"] == "failed":
    st.error(f"该图片识别失败：{item['error']}")
    st.stop()

if item["status"] != "success":
    st.info("该图片正在识别。")
    st.stop()

result = item["agent_result"]
visual = result["visual_result"]
report = result["report"]

st.subheader(f"检测结果：{item['original_name']}")

col1, col2, col3 = st.columns(3)

col1.metric(
    "是否检出缺陷",
    "是" if visual["has_defect"] else "否",
)
col2.metric(
    "检出缺陷类别数",
    len(visual["defects"]),
)
col3.metric(
    "总面积占比",
    f"{visual['overall_area_ratio']:.2%}",
)

st.subheader("缺陷明细")

for defect in report.get("defects", []):
    with st.expander(
        defect.get("defect_type", "未知类别")
    ):
        st.json(defect)

st.subheader("AI质检建议")

decision = report.get("ai_recommendation")

st.write(
    "建议结论：",
    DECISION_NAMES.get(decision, "未知"),
)
st.write(
    "是否需要人工复核：",
    "是" if report.get("manual_review_required") else "否",
)
st.write(
    "复核原因：",
    report.get("manual_review_reason") or "无",
)
st.write(
    "处理建议：",
    report.get("overall_recommended_action", ""),
)

st.subheader("人工复核")

decision_key = f"decision_{image_id}"
comment_key = f"comment_{image_id}"

if decision_key not in st.session_state:
    st.session_state[decision_key] = item["review_decision"]

if comment_key not in st.session_state:
    st.session_state[comment_key] = item["review_comment"]

st.selectbox(
    "人工质检结论",
    ["REVIEW", "PASS", "FAIL"],
    format_func=lambda value: DECISION_NAMES[value],
    key=decision_key,
    on_change=remember_review,
    args=(image_id,),
)

st.text_area(
    "人工复核说明",
    key=comment_key,
    on_change=remember_review,
    args=(image_id,),
)

if st.button(
    "保存当前图片的质检报告",
    key=f"save_{image_id}",
):
    try:
        saved = save_reviewed_report(
            agent_result=result,
            reviewer_decision=item["review_decision"],
            reviewer_comment=item["review_comment"],
        )
        item["saved_report"] = saved
        st.success("当前图片的报告已保存。")

    except Exception as error:
        st.error(f"报告保存失败：{error}")

if item["saved_report"]:
    st.caption(
        "最近保存的报告："
        f"{item['saved_report']['report_path']}"
    )