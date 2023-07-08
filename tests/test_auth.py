import asyncio
from typing import Any, Dict, List

import pytest
from httpx import AsyncClient, Response


@pytest.mark.asyncio
class TestAuth:
    username = "string"
    password = "string"
    headers: Dict[str, str] | None = None
    access_token: Any = None
    refresh_token: Any = None

    @property
    def data(self):
        return {"username": TestAuth.username, "password": TestAuth.password}

    async def test_register(self, http_client: AsyncClient):
        response = await http_client.post("/auth/register", json=self.data)
        assert response.status_code == 200
        response = await http_client.post("/auth/register", json=self.data)
        assert response.status_code == 400

    async def test_login(self, http_client: AsyncClient):
        response = await http_client.post("/auth/login", json=self.data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        TestAuth.access_token = response.json()["access_token"]
        TestAuth.refresh_token = response.json()["refresh_token"]
        TestAuth.headers = {"Authorization": "Bearer " + TestAuth.access_token}

        corrupted_data = self.data.copy()
        corrupted_data["username"] = corrupted_data["username"] + "sndjsns"
        response = await http_client.post("/auth/login", json=corrupted_data)
        assert response.status_code == 400

    async def test_auth_and_tokens(self, http_client: AsyncClient):
        response = await http_client.get("/auth/me", headers=TestAuth.headers)
        assert response.status_code == 200
        assert TestAuth.username == response.json()["username"]

        bad_header = {"Authorization": "Bearer " + TestAuth.refresh_token}
        response = await http_client.get("/auth/me", headers=bad_header)
        assert response.status_code == 403

        bad_header = {"Authorization": TestAuth.access_token}
        response = await http_client.get("/auth/me", headers=bad_header)
        assert response.status_code == 403

    @pytest.mark.skip("Reason: this test should be moved as loading test in CI/CD")
    async def test_spam_logins(self, http_client: AsyncClient):
        """Build time for this test is too much. ignore it in makefile."""
        responses: List[Response] = await asyncio.gather(
            *[http_client.post("/auth/login", json=self.data) for _ in range(30)]
        )
        statuses = [response.status_code for response in responses]
        statuses.sort()
        errors = [
            response.json().get("error") for response in responses if response.status_code != 200
        ]
        assert 200 in statuses  # some request didn't block
        assert 400 in statuses  # but some did!
        assert len(errors) > 0
        assert "Too many login attempts recently" in errors[0]

    async def test_refresh_token(self, http_client: AsyncClient):
        await asyncio.sleep(1)
        data = {"refresh_token": TestAuth.refresh_token}
        response = await http_client.post("/auth/refresh", json=data)
        assert response.status_code == 200
        assert response.json()["access_token"] != TestAuth.access_token

        TestAuth.access_token = response.json()["access_token"]
        response = await http_client.get("/auth/me", headers=TestAuth.headers)
        assert response.status_code == 200
