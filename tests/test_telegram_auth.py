import pytest

from src.telegram.auth import get_or_create_tenant


@pytest.mark.asyncio
async def test_create_new_tenant(db_session):
    tenant, user = await get_or_create_tenant(db_session, telegram_user_id=12345, first_name="Test")
    assert tenant.id is not None
    assert user.telegram_user_id == 12345
    assert user.first_name == "Test"
    assert user.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_existing_tenant_returned(db_session):
    t1, u1 = await get_or_create_tenant(db_session, telegram_user_id=12345, first_name="Test")
    t2, u2 = await get_or_create_tenant(db_session, telegram_user_id=12345, first_name="Test")
    assert t1.id == t2.id
    assert u1.id == u2.id
