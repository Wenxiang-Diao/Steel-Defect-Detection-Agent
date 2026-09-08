import tempfile
from pathlib import Path

import streamlit as st

from agent import inspect_single_image
from review_tool import save_reviewed_report


st.set_page_config(
    page_title="钢板表面智能质检",
    layout="wide",
)

st.title("钢板表面智能质检 Agent")

uploaded_file = st.file_uploader(
    "上传钢板表面图片",
    type=["jpg", "jpeg", "png", "bmp"],
)
uploaded_folder = st.file_uploader(
    "上传钢板图片文件夹",
)

if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="待检测图片",
    )

    if st.button("开始检测"):
        suffix = Path(uploaded_file.name).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temporary_file:
            temporary_file.write(
                uploaded_file.getbuffer()
            )
            image_path = temporary_file.name

        try:
            with st.spinner("正在进行缺陷检测和质检分析"):
                result = inspect_single_image(
                    image_path
                )

            st.session_state["agent_result"] = result
            st.success("检测完成")

        except Exception as error:
            st.error(f"检测失败：{error}")

        finally:
            Path(image_path).unlink(
                missing_ok=True
            )

if "agent_result" in st.session_state:
    result = st.session_state["agent_result"]
    visual = result["visual_result"]
    report = result["report"]

    st.subheader("视觉检测结果")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "是否存在缺陷",
        "是" if visual["has_defect"] else "否",
    )
    col2.metric(
        "缺陷数量",
        len(visual["defects"]),
    )
    col3.metric(
        "总面积占比",
        f"{visual['overall_area_ratio']:.2%}",
    )

    st.subheader("缺陷明细")

    for defect in report.get("defects", []):
        with st.expander(
            defect.get(
                "defect_type",
                "未知缺陷",
            )
        ):
            st.json(defect)

    st.subheader("AI质检建议")

    st.write(
        "建议结论：",
        report.get("ai_recommendation"),
    )
    st.write(
        "是否需要人工复核：",
        report.get("manual_review_required"),
    )
    st.write(
        "复核原因：",
        report.get("manual_review_reason"),
    )
    st.write(
        "处理建议：",
        report.get(
            "overall_recommended_action"
        ),
    )

    st.subheader("人工复核")

    reviewer_decision = st.selectbox(
        "人工质检结论",
        ["REVIEW", "PASS", "FAIL"],
    )

    reviewer_comment = st.text_area(
        "人工复核说明"
    )

    if st.button("确认并保存质检报告"):
        saved_result = save_reviewed_report(
            agent_result=result,
            reviewer_decision=reviewer_decision,
            reviewer_comment=reviewer_comment,
        )

        st.success(
            "报告已保存："
            f"{saved_result['report_path']}"
        )