from app.main import register_user
from app.schemas import UserCreate


class FakeCursor:
    def __init__(self):
        self.lastrowid = 7
        self.query = ""
        self.parameters = ()

    def execute(self, query, parameters=()):
        self.query = query
        self.parameters = parameters

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self, dictionary=False):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_new_accounts_are_always_regular_users():
    connection = FakeConnection()
    payload = UserCreate(username="student", password="strong-password")

    response = register_user(payload, connection)

    assert connection.cursor_instance.parameters[2] == "user"
    assert connection.committed is True
    assert response == {"id": 7, "username": "student", "role": "user"}
