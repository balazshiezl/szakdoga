from flask_login import UserMixin
from models.db import get_connection

class User(UserMixin):
    def __init__(self, id, name, email, password=None, age=None, height=None,weight=None, gender=None, training_intensity=None, training_goal=None, is_subscribed=False, subscription_plan="none"):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.training_intensity = training_intensity
        self.training_goal = training_goal
        self.is_subscribed = is_subscribed
        self.subscription_plan = subscription_plan



def get_user_by_email(email):
    conn = get_connection()
    result = conn.run("SELECT * FROM users WHERE email = :email", email=email)
    conn.close()
    if result:
        row = result[0]
        return User(
            id=row[0],
            name=row[1],
            email=row[2],
            password=row[3],
            age=row[4],
            weight=row[5],
            height=row[6],
            gender=row[7],
            training_intensity=row[8],
            training_goal=row[9],
            is_subscribed=row[10],
            subscription_plan=row[11]
        )
    return None


def email_exists(email):
    conn = get_connection()
    result = conn.run("SELECT 1 FROM users WHERE email = :email", email=email)
    conn.close()
    return bool(result)


def create_user(name, email, hashed_pw):
    conn = get_connection()
    conn.run(
        "INSERT INTO users (name, email, password) VALUES (:name, :email, :password)",
        name=name, email=email, password=hashed_pw
    )
    conn.close()


def load_user_by_id(user_id):
    conn = get_connection()
    result = conn.run("SELECT * FROM users WHERE id = :id", id=int(user_id))
    conn.close()
    if result:
        row = result[0]
        return User(
            id=row[0],
            name=row[1],
            email=row[2],
            password=row[3],
            age=row[4],
            weight=row[5],
            height=row[6],
            gender=row[7],
            training_intensity=row[8],
            training_goal=row[9],
            is_subscribed=row[10],
            subscription_plan=row[11]
        )
    return None
