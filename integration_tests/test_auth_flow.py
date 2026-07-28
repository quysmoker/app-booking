from integration_tests.base import IntegrationTestBase


class AuthenticationIntegrationTest(
    IntegrationTestBase
):
    def test_register_then_login_successfully(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "email": "newuser@test.com",
                "password": "Test123456",
                "full_name": "New User",
            },
            format="json",
        )

        self.assertIn(
            register_response.status_code,
            [200, 201],
            register_response.data,
        )

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": "newuser@test.com",
                "password": "Test123456",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            200,
            login_response.data,
        )

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "user@test.com",
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [400, 401],
        )

    def test_protected_api_without_token_fails(self):
        self.clear_authentication()

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )
