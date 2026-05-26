import os
import tempfile
import unittest


os.environ["DB_BACKEND"] = ""
os.environ["MYSQL_HOST"] = ""
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

import app as app_module


class BristolBuzzAppTest(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(delete=False)
        self.database_file.close()
        app_module.SQLITE_PATH = self.database_file.name
        app_module.app.config["TESTING"] = True
        app_module.app.secret_key = "test-secret-key"
        app_module.init_db()
        self.client = app_module.app.test_client()

    def tearDown(self):
        os.remove(self.database_file.name)

    def create_account(self, email="student@example.com", password="Secure123"):
        return self.client.post(
            "/api/create-account",
            json={
                "email": email,
                "confirmEmail": email,
                "password": password,
                "confirmPassword": password,
            },
        )

    def sign_in(self, email="student@example.com", password="Secure123"):
        return self.client.post(
            "/api/sign-in",
            json={"email": email, "password": password, "next": "ticket.html"},
        )

    def test_create_account_rejects_weak_password(self):
        response = self.create_account(password="short")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_create_account_rejects_duplicate_email(self):
        first_response = self.create_account()
        second_response = self.create_account()

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)

    def test_signed_in_user_can_book_ticket(self):
        self.assertEqual(self.create_account().status_code, 200)
        self.assertEqual(self.sign_in().status_code, 200)

        response = self.client.post(
            "/api/book-ticket",
            json={
                "eventName": "Bristol Food Festival",
                "attendeeName": "Nehzad Student",
                "attendeeEmail": "student@example.com",
                "ticketQuantity": "2",
                "cardName": "Nehzad Student",
                "cardNumber": "4242424242424242",
                "expiry": "12/30",
                "cvv": "123",
            },
        )

        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertTrue(data["reference"].startswith("BB"))
        self.assertEqual(data["ticketQuantity"], 2)


if __name__ == "__main__":
    unittest.main()
