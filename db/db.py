from api.schemas import UserCreate

users = []


def create_user_in_db(body: UserCreate):
    global users
    users.append(body)
