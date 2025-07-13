import os
from openai import AsyncOpenAI

from app.db import Category

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def classify_category(text):
    try:
        resp = await client.responses.create(
            model="gpt-4o-mini",
            input=f"Ты - помощник службы поддержки. Определи категорию жалобы: '{text}'. Варианты: technical, payment, other. Ответ только одним словом.",
        )

        words = resp.output_text.split(" ")
        categories = [e.value for e in Category]

        category = next(word for word in words if word in categories)

        return category

    except Exception as exc:
        print(exc)
        return None
