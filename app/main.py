import httpx

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status
from sqlalchemy.orm import Session
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


class ComplaintDetail(BaseModel):
    id: int
    text: str
    status: Status
    sentiment: Optional[Sentiment]
    category: Optional[Category]
    timestamp: datetime


class ComplaintStatusUpdate(BaseModel):
    status: Status


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


@app.post(
    "/complaints", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED
)
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


@app.get("/complaints/new", response_model=List[ComplaintDetail])
def get_new_complaints(
    last_id: Optional[int] = Query(
        None,
        description="Return complaints whose id > last_id",
    ),
):
    # Возвращает все open-жалобы с id > last_id. Если last_id не указан - вернёт все open-жалобы
    db: Session = SessionLocal()
    try:
        q = db.query(Complaint).filter(Complaint.status == Status.open)

        if last_id is not None:
            q = q.filter(Complaint.id > last_id)

        q = q.order_by(Complaint.id)
        complaints = q.all()

        return [
            ComplaintDetail(
                id=c.id,
                text=c.text,
                status=c.status,
                sentiment=c.sentiment,
                category=c.category,
                timestamp=c.timestamp,
            )
            for c in complaints
        ]
    finally:
        db.close()


@app.patch("/complaints/{complaint_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def close_complaint(
    complaint_id: int = Path(..., description="Complaint ID to close a complaint by")
):
    # Закрывает жалобу - устанавливает status = closed. Возвращает 204 No Content или 404, если не найдена
    db: Session = SessionLocal()
    try:
        complaint = db.query(Complaint).get(complaint_id)
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        complaint.status = Status.closed
        db.add(complaint)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    finally:
        db.close()
