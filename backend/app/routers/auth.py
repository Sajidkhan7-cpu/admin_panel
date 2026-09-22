"""
routers/auth.py
Student & admin registration and login (JWT-based).

Admin accounts require developer approval: when someone registers for
an admin account, a request is emailed to DEVELOPER_EMAIL with Approve/
Reject links. The account only becomes usable once approved.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserRegister, AdminRegister, UserLogin, UserOut, Token, MessageResponse,
)
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import (
    create_access_token,
    create_approve_token,
    create_reject_token,
    decode_approval_token,
)
from app.utils.email_utils import send_admin_approval_request, send_applicant_decision_email
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _decision_page(title: str, message: str) -> HTMLResponse:
    """Simple standalone HTML shown to the developer after clicking approve/reject."""
    html = f"""
    <!DOCTYPE html>
    <html><head><title>{title}</title>
    <style>
      body {{ font-family: system-ui, sans-serif; background:#0f172a; color:#f1f5f9;
              display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }}
      .card {{ background:#1e293b; padding:2.5rem 3rem; border-radius:12px; text-align:center; max-width:420px; }}
      h1 {{ font-size:1.25rem; margin-bottom:0.5rem; }}
      p {{ color:#94a3b8; }}
    </style>
    </head><body><div class="card"><h1>{title}</h1><p>{message}</p></div></body></html>
    """
    return HTMLResponse(content=html)


@router.post("/admin-register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def admin_register(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Creates an admin account with is_verified=False, then emails the
    developer an approve/reject link. The account can't log in until
    the developer approves it.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="admin",
        is_verified=False,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    approve_token = create_approve_token(admin.id)
    reject_token = create_reject_token(admin.id)

    try:
        send_admin_approval_request(admin.name, admin.email, approve_token, reject_token)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Account created, but email failed: {e}",
        )

    return MessageResponse(
        message="Registration submitted. An administrator will review your request — "
                "you'll be notified by email once it's approved."
    )


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return Token(access_token=token, user=user)


@router.post("/admin-register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def admin_register(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Creates an admin account with is_verified=False, then emails the
    developer an approve/reject link. The account can't log in until
    the developer approves it.
    """

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="admin",
        is_verified=False,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    approve_token = create_approve_token(admin.id)
    reject_token = create_reject_token(admin.id)

    try:
        send_admin_approval_request(admin.name, admin.email, approve_token, reject_token)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Account created, but we couldn't notify the developer for approval. Contact support.",
        )

    return MessageResponse(
        message="Registration submitted. An administrator will review your request — "
                "you'll be notified by email once it's approved."
    )


@router.get("/approve-admin", response_class=HTMLResponse)
def approve_admin(token: str, db: Session = Depends(get_db)):
    user_id = decode_approval_token(token, expected_action="approve")

    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    if not user:
        return _decision_page("Not found", "This admin account no longer exists.")

    if user.is_verified:
        return _decision_page("Already approved", f"{user.email} was already approved.")

    user.is_verified = True
    db.commit()

    try:
        send_applicant_decision_email(user.email, approved=True)
    except Exception:
        pass  # approval already succeeded; email failure shouldn't block it

    return _decision_page("Approved ✓", f"{user.email} has been granted admin access.")


@router.get("/reject-admin", response_class=HTMLResponse)
def reject_admin(token: str, db: Session = Depends(get_db)):
    user_id = decode_approval_token(token, expected_action="reject")

    user = db.query(User).filter(User.id == user_id, User.role == "admin").first()
    if not user:
        return _decision_page("Not found", "This admin account no longer exists.")

    email = user.email
    db.delete(user)
    db.commit()

    try:
        send_applicant_decision_email(email, approved=False)
    except Exception:
        pass

    return _decision_page("Rejected", f"The request from {email} has been rejected and removed.")


@router.post("/admin-login", response_model=Token)
def admin_login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.role == "admin").first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Your admin account is pending approval. You'll be notified by email once it's reviewed.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return Token(access_token=token, user=user)