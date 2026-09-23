"""Offline checks: provider outages must not look like bad credentials."""
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import HTTPException
from app import auth


class VerificationTests(unittest.IsolatedAsyncioTestCase):
    async def verify(self, status=200, body=None, error=None):
        client = AsyncMock()
        client.get.side_effect = error
        client.get.return_value = httpx.Response(status, json=body)
        with patch.object(auth.config, "AUTH_READY", True), patch.object(auth.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value = client
            return await auth.verify_access_token("offline-test-token")

    async def test_valid_user(self):
        self.assertEqual((await self.verify(body={"id": "test-user"}))["id"], "test-user")

    async def test_invalid_token(self):
        with self.assertRaises(HTTPException) as error:
            await self.verify(401)
        self.assertEqual(error.exception.status_code, 401)

    async def test_outages_are_retryable(self):
        for status in (429, 500, 502, 503):
            with self.subTest(status=status), self.assertRaises(HTTPException) as error:
                await self.verify(status)
            self.assertEqual(error.exception.status_code, 503)

    async def test_timeout_is_retryable(self):
        with self.assertRaises(HTTPException) as error:
            await self.verify(error=httpx.ReadTimeout("test timeout"))
        self.assertEqual(error.exception.status_code, 503)

    async def test_unexpected_payload(self):
        with self.assertRaises(HTTPException) as error:
            await self.verify(body=[])
        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
