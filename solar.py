"""BookToss v0.0.2 — Solar API 첫 호출.

Upstage Solar는 OpenAI 호환이라, 표준 openai SDK에 base_url만 Solar로 바꿔 쓴다.
실행:  python solar.py   (먼저 .env 에 UPSTAGE_API_KEY 를 채워야 함)
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SOLAR_BASE_URL = "https://api.upstage.ai/v1"
MODEL = "solar-pro2"


def get_client() -> OpenAI:
    """키를 확인하고 Solar에 연결된 OpenAI 클라이언트를 만든다."""
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise SystemExit(
            "UPSTAGE_API_KEY 가 없습니다. .env 에 키를 넣어주세요 (.env.example 참고)."
        )
    return OpenAI(api_key=api_key, base_url=SOLAR_BASE_URL)


def ask_solar(client: OpenAI, prompt: str) -> str:
    """prompt 를 Solar에 보내고 답변 텍스트를 돌려준다."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    client = get_client()
    answer = ask_solar(client, "BookToss 라는 도서관 검색 서비스를 한 문장으로 소개해줘.")
    print("Solar:", answer)
