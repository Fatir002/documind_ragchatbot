"""Try registration and login: python -m scripts.try_auth"""

from app.exceptions import DocuMindError
from app.auth import authenticate, register_user


def main() -> None:
    try:
        user = register_user("alice", "correct-horse-battery", role="admin")
        print(f"✅ Registered: {user}")
    except DocuMindError as exc:
        print(f"registration: {exc.user_message}")

    try:
        user = authenticate("alice", "correct-horse-battery")
        print(f"✅ Login succeeded: {user}")
    except DocuMindError as exc:
        print(f"❌ {exc.user_message}")

    try:
        authenticate("alice", "wrong-password")
        print("❌ This should not have succeeded!")
    except DocuMindError as exc:
        print(f"✅ Correctly rejected: {exc.user_message}")

    try:
        authenticate("ALICE", "correct-horse-battery")
        print("✅ Case-insensitive login works")
    except DocuMindError as exc:
        print(f"❌ Unexpected rejection: {exc.user_message}")


if __name__ == "__main__":
    main()
