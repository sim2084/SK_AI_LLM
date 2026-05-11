def make_summary_prompt(text: str,title: str, summary_style: str) -> str:
    return f"""
노래의 제목과 가사를 참고해서 내용을 요약해줘.

노래 제목 : {title}

요약 방식: {summary_style}

조건:   
- 제목의 의미도 함께 고려할 것
- 노래의 주제와 감정을 중심으로 설명할 것
- 핵심 내용 중심으로 정리
- 불필요한 반복 제거
- 자연스러운 문장으로 정리
- 원문을 그대로 길게 복사하지 말 것

가사:
{text}
"""