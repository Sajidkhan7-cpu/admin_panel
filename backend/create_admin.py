"""
create_admin.py
Run this once (after configuring .env and creating the database) to
create the first admin account with a properly bcrypt-hashed password.
Bypasses email verification since it's run by a trusted operator.

Usage:
    cd backend
    python create_admin.py
"""
import getpass
from app.database import SessionLocal, init_db
from app.models.user import User
from app.utils.password import hash_password


def main():
    init_db()  # ensures tables exist
    db = SessionLocal()

    print("=== Create Admin Account ===")
    name = input("Admin name: ").strip() or "Administrator"
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password: ")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"A user with email {email} already exists.")
        return

    admin = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="admin",
        is_verified=True,  # trusted CLI creation skips email verification
    )
    db.add(admin)
    db.commit()
    print(f"Admin account created successfully for {email}.")


if __name__ == "__main__":
    main()