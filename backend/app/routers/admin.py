"""
routers/admin.py
Admin-only CRUD endpoints for courses and FAQs, plus dashboard stats
(total students, total chats, most-asked intents).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.course import Course
from app.models.faq import FAQ
from app.models.user import User
from app.models.chat import ChatHistory
from app.schemas.course_schema import CourseCreate, CourseUpdate, CourseOut
from app.schemas.faq_schema import FAQCreate, FAQUpdate, FAQOut
from app.utils.jwt_handler import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total_students = db.query(User).filter(User.role == "student").count()
    total_courses = db.query(Course).count()
    total_chats = db.query(ChatHistory).count()
    total_seats_available = db.query(func.sum(Course.available_seats)).scalar() or 0

    top_intents = (
        db.query(ChatHistory.intent, func.count(ChatHistory.id).label("count"))
        .group_by(ChatHistory.intent)
        .order_by(func.count(ChatHistory.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_chats": total_chats,
        "total_seats_available": total_seats_available,
        "top_intents": [{"intent": i, "count": c} for i, c in top_intents],
    }


# ---------------------------------------------------------------------------
# Course CRUD
# ---------------------------------------------------------------------------
@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()


# ---------------------------------------------------------------------------
# FAQ CRUD
# ---------------------------------------------------------------------------
@router.post("/faqs", response_model=FAQOut, status_code=201)
def create_faq(payload: FAQCreate, db: Session = Depends(get_db)):
    faq = FAQ(**payload.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.put("/faqs/{faq_id}", response_model=FAQOut)
def update_faq(faq_id: int, payload: FAQUpdate, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)
    db.commit()
    db.refresh(faq)
    return faq


@router.delete("/faqs/{faq_id}", status_code=204)
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()


# ---------------------------------------------------------------------------
# Students list (read-only)
# ---------------------------------------------------------------------------
@router.get("/students")
def list_students(db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").all()
    return [
        {"id": s.id, "name": s.name, "email": s.email, "phone": s.phone, "created_at": s.created_at}
        for s in students
    ]
