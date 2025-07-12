import httpx

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from textblob import TextBlob

from app.db import SessionLocal, Complaint, Sentiment, Category, Status
from app.ai import classify_category


app = FastAPI(title="Complaints API")


class ComplaintIn(BaseModel):
    text: str


class ComplaintOut(BaseModel):
    id: int
    status: Status
    sentiment: Sentiment | None
    category: Category | None


def classify_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.15:
        return Sentiment.positive
    if polarity < -0.15:
        return Sentiment.negative
    return Sentiment.neutral


async def get_ip_info(ip):
    print(ip)
    url = f"http://ip-api.com/json/{ip}?fields=status,country,city,query"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                return data if data.get("status") == "success" else None
    except Exception as exc:
        print(exc)
    return None


@app.post("/complaints", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
async def create_complaint(payload: ComplaintIn, request: Request):
    db = SessionLocal()

    try:
        sentiment = classify_sentiment(payload.text)
        category = await classify_category(payload.text)

        if category is None:
            category = Category.other

        complaint = Complaint(
            text=payload.text,
            sentiment=sentiment,
            category=category,
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        # Geolocation
        client_ip = request.client.host
        client_location = await get_ip_info(client_ip)
        print(client_location)

        return ComplaintOut(
            id=complaint.id,
            status=complaint.status,
            sentiment=complaint.sentiment,
            category=complaint.category,
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(500, "Internal Server Error") from exc
    finally:
        db.close()
