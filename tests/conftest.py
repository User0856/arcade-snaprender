from unittest.mock import MagicMock

import pytest

FAKE_KEY = "sk_live_test_key"  # noqa: S105


@pytest.fixture
def mock_context() -> MagicMock:
    context = MagicMock()

    def get_secret(name: str) -> str:
        if name == "SNAPRENDER_API_KEY":
            return FAKE_KEY
        raise ValueError(f"Secret {name} not found")

    context.get_secret = MagicMock(side_effect=get_secret)
    return context
