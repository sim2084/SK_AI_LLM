import os
from functools import lru_cache
from typing import Iterable, Iterator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "winemeg-review-data")
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "3"))


def _require_env(name: str) -> str:
    """필수 환경변수가 비어 있으면 명확한 에러 메시지를 발생시킨다."""
    value = os.getenv(name)

    if not value:
        raise ValueError(f"{name}이 설정되어 있지 않습니다. .env 파일을 확인하세요.")

    return value

# @lru_cache(maxsize=1)는 함수의 결과를 한 번 저장해두고 다음 호출부터 재사용하게 하는 데코레이터이다.
# Streamlit 앱은 화면이 갱신될 때 코드가 다시 실행될 수 있으므로, LLM 객체나 Pinecone retriever처럼 매번 새로 만들 필요가 없는 객체는 캐싱해두는 것이 좋다.
@lru_cache(maxsize=1)
def get_vision_llm() -> ChatOpenAI:
    """음식 이미지를 풍미 설명으로 변환할 이미지 입력 지원 모델을 준비한다."""
    _require_env("OPENAI_API_KEY")

    return ChatOpenAI(
        model=VISION_MODEL,
        temperature=0.2,
    )


@lru_cache(maxsize=1)
def get_recommend_llm() -> ChatOpenAI:
    """검색된 와인 리뷰를 근거로 최종 추천 답변을 생성할 모델을 준비한다."""
    _require_env("OPENAI_API_KEY")

    return ChatOpenAI(
        model=TEXT_MODEL,
        temperature=0.3,
    )


@lru_cache(maxsize=1)
def get_retriever():
    """Pinecone Vector Store에 연결하고 retriever를 생성한다."""
    _require_env("OPENAI_API_KEY")
    pinecone_api_key = _require_env("PINECONE_API_KEY")

    pc = Pinecone(api_key=pinecone_api_key)
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    vector_store = PineconeVectorStore(
        index=pinecone_index,
        embedding=embeddings,
    )

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )


def normalize_image_urls(image_urls: Iterable[str]) -> list[str]:
    """입력된 이미지 URL 목록에서 빈 문자열을 제거한다."""
    return [url.strip() for url in image_urls if url and url.strip()]


def format_wine_docs(docs: list) -> str:
    """검색된 와인 리뷰 Document를 추천 Prompt에 넣기 좋은 문자열로 변환한다."""
    formatted = []

    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        row = doc.metadata.get("row", "unknown")

        formatted.append(
            f"[와인 리뷰 {i}]\n"
            f"source: {source}\n"
            f"row: {row}\n"
            f"content:\n{doc.page_content}"
        )

    return "\n\n".join(formatted)


def describe_dish_flavor(image_urls: Iterable[str]) -> str:
    """음식 이미지 URL 목록을 받아 와인 페어링 검색에 필요한 영어 풍미 설명을 생성한다."""
    image_urls = normalize_image_urls(image_urls)

    if not image_urls:
        raise ValueError("이미지 URL이 비어 있습니다.")

    content = [
        {
            "type": "text",
            "text": (
                "Look at the food image(s) and describe the dish for wine pairing. "
                "Focus on ingredients, cooking method, sauce, texture, intensity, acidity, fat, sweetness, "
                "spiciness, and overall flavor profile. "
                "Write the answer in English because the wine review data is in English. "
                "Keep it concise in 2-3 sentences and include searchable flavor keywords."
            ),
        }
    ]

    # 여러 장의 이미지를 함께 분석할 수 있도록 URL 목록을 이미지 입력으로 추가한다.
    for image_url in image_urls:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            }
        )

    messages = [
        SystemMessage(
            content=(
                "You are a culinary expert who writes concise and useful flavor descriptions "
                "for wine pairing search queries."
            )
        ),
        HumanMessage(content=content),
    ]

    response = get_vision_llm().invoke(messages)
    return response.content


def search_wines(dish_flavor: str) -> dict:
    """음식 풍미 설명과 유사한 와인 리뷰를 Pinecone에서 검색한다."""
    retriever = get_retriever()
    docs = retriever.invoke(dish_flavor)

    return {
        "dish_flavor": dish_flavor,
        "wine_reviews": format_wine_docs(docs),
        "retrieved_docs": docs,
    }


recommend_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a knowledgeable and friendly sommelier.

Your task is to recommend wines that pair well with the given dish.
Use the retrieved wine reviews as the main evidence.
Do not invent specific wines that are not supported by the retrieved reviews.
If the retrieved reviews are insufficient, say that the evidence is limited.

Respond in Korean.
"""
    ),
    (
        "human",
        """
[Dish flavor description]
{dish_flavor}

[Retrieved wine reviews]
{wine_reviews}

[Output format]
1. 추천 와인 스타일:
2. 추천 이유:
3. 근거로 사용한 리뷰 요약:
4. 주의할 점:
"""
    ),
])


def stream_recommendation(retrieval_result: dict) -> Iterator[str]:
    """검색 결과를 바탕으로 최종 추천 답변을 스트리밍한다."""
    chain = recommend_prompt | get_recommend_llm() | StrOutputParser()

    return chain.stream(
        {
            "dish_flavor": retrieval_result["dish_flavor"],
            "wine_reviews": retrieval_result["wine_reviews"],
        }
    )


def prepare_recommendation_context(image_urls: Iterable[str]) -> dict:
    """이미지를 분석하고 관련 와인 리뷰를 검색하여 추천에 필요한 context를 만든다."""
    dish_flavor = describe_dish_flavor(image_urls)
    retrieval_result = search_wines(dish_flavor)

    return retrieval_result
