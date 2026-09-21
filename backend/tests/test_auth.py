import pytest
import re
from unittest.mock import AsyncMock, MagicMock
from app.core.exceptions import BadRequestException
from app.api.v1.endpoints.auth import register
from app.schemas.dto import UserRegister

class DummyUserIn:
    def __init__(self, email, password, full_name):
        self.email = email
        self.password = password
        self.full_name = full_name

@pytest.mark.asyncio
async def test_password_policy_failures():
    # 1. Test short password
    user_in = DummyUserIn("test@corp.com", "Sh1!", "Test User")
    with pytest.raises(BadRequestException) as exc:
        await register(user_in, db=AsyncMock())
    assert exc.value.code == "PASSWORD_TOO_SHORT"

    # 2. Test missing uppercase
    user_in = DummyUserIn("test@corp.com", "lowercaseno1!", "Test User")
    with pytest.raises(BadRequestException) as exc:
        await register(user_in, db=AsyncMock())
    assert exc.value.code == "PASSWORD_NO_UPPERCASE"

    # 3. Test missing lowercase
    user_in = DummyUserIn("test@corp.com", "UPPERCASENO1!", "Test User")
    with pytest.raises(BadRequestException) as exc:
        await register(user_in, db=AsyncMock())
    assert exc.value.code == "PASSWORD_NO_LOWERCASE"

    # 4. Test missing digit
    user_in = DummyUserIn("test@corp.com", "UppercaseNoDigit!", "Test User")
    with pytest.raises(BadRequestException) as exc:
        await register(user_in, db=AsyncMock())
    assert exc.value.code == "PASSWORD_NO_DIGIT"

    # 5. Test missing special character
    user_in = DummyUserIn("test@corp.com", "UppercaseDigit123", "Test User")
    with pytest.raises(BadRequestException) as exc:
        await register(user_in, db=AsyncMock())
    assert exc.value.code == "PASSWORD_NO_SPECIAL"
