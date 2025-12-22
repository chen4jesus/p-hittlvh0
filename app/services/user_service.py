from app.models import User
from app.extensions import db

class UserService:
    @staticmethod
    def create_user(username: str, email: str) -> User:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        return User.query.get(user_id)

    @staticmethod
    def get_all_users():
        return User.query.all()
