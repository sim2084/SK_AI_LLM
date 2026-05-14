import streamlit as st

from rag import prepare_recommendation_context, stream_recommendation

st.set_page_config(
    page_title="AI Wine Sommelier",
    page_icon="🍷",
    layout="centered",
)

st.title("🍷 AI Wine Sommelier")
st.write("음식 이미지 URL을 입력하면, 음식의 풍미를 분석하고 와인 리뷰 데이터에서 어울리는 와인을 찾아 추천합니다.")

with st.expander("사용 방법", expanded=False):
    st.markdown(
        """
1. 음식 이미지 URL을 입력합니다.
2. AI가 이미지를 보고 음식의 재료, 조리 방식, 산미, 지방감, 단맛, 매운맛 등을 영어 풍미 설명으로 변환합니다.
3. 해당 음식 설명으로 Pinecone Vector DB에서 유사한 와인 리뷰를 검색합니다.
4. 검색된 리뷰를 근거로 한국어 와인 추천을 생성합니다.
"""
    )

with st.form(key="image_url_form"):
    image_url_text = st.text_area(
        "음식 이미지 URL",
        height=100,
        placeholder="이미지 URL을 한 줄에 하나씩 입력하세요.",
    )

    submitted = st.form_submit_button("와인 추천 받기")

if submitted:
    image_urls = [
        line.strip()
        for line in image_url_text.splitlines()
        if line.strip()
    ]

    if not image_urls:
        st.warning("이미지 URL을 입력해주세요.")
        st.stop()

    st.subheader("입력한 음식 이미지")

    for image_url in image_urls:
        st.image(image_url, use_container_width=True)

    try:
        with st.spinner("음식 이미지를 분석하고 관련 와인 리뷰를 검색하는 중입니다..."):
            recommendation_context = prepare_recommendation_context(image_urls)

        st.subheader("음식 풍미 설명")
        st.write(recommendation_context["dish_flavor"])

        with st.expander("검색된 와인 리뷰 확인", expanded=False):
            st.text(recommendation_context["wine_reviews"])

        st.subheader("AI 와인 추천")

        with st.spinner("검색된 리뷰를 바탕으로 추천 답변을 생성하는 중입니다..."):
            st.write_stream(stream_recommendation(recommendation_context))

    except Exception as e:
        st.error("처리 중 오류가 발생했습니다.")
        st.exception(e)