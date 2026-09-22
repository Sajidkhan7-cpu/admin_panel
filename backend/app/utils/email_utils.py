"""
utils/email_utils.py
Sends transactional emails: admin-approval requests (to the developer)
and the resulting decision notice (to the applicant).
"""
import smtplib
from email.message import EmailMessage

from app.config import settings


def _send(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_admin_approval_request(applicant_name: str, applicant_email: str, approve_token: str, reject_token: str) -> None:
    """Sent to DEVELOPER_EMAIL whenever someone registers for an admin account."""
    approve_link = f"{settings.BACKEND_BASE_URL}/api/auth/approve-admin?token={approve_token}"
    reject_link = f"{settings.BACKEND_BASE_URL}/api/auth/reject-admin?token={reject_token}"

    body = (
        f"A new admin account request was submitted for {settings.APP_NAME}.\n\n"
        f"Name: {applicant_name}\n"
        f"Email: {applicant_email}\n\n"
        f"Approve this request:\n{approve_link}\n\n"
        f"Reject this request:\n{reject_link}\n\n"
        f"This link expires in {settings.APPROVAL_TOKEN_EXPIRE_MINUTES // 60} hours."
    )
    _send(settings.DEVELOPER_EMAIL, f"[{settings.APP_NAME}] New admin approval request", body)


def send_applicant_decision_email(applicant_email: str, approved: bool) -> None:
    """Sent to the applicant once the developer approves or rejects them."""
    if approved:
        subject = f"Your {settings.APP_NAME} admin account has been approved"
        body = (
            "Good news — your admin account request has been approved.\n\n"
            f"You can now log in here: {settings.FRONTEND_BASE_URL}/admin_login.html"
        )
    else:
        subject = f"Your {settings.APP_NAME} admin account request was declined"
        body = (
            "Your admin account request was not approved. "
            "If you believe this is a mistake, please contact the site administrator."
        )
    _send(applicant_email, subject, body)