import importlib.util
from pathlib import Path

import pytest
from PIL import Image

from app.auth.security import verify_password
from app.db.enums import UserRole


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_e2e.py"
SPEC = importlib.util.spec_from_file_location("seed_e2e_under_test", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
seed_e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed_e2e)

E2E_ADMIN_PASSWORD = seed_e2e.E2E_ADMIN_PASSWORD
E2E_USER_PASSWORD = seed_e2e.E2E_USER_PASSWORD
application_table_names = seed_e2e.application_table_names
generate_synthetic_assets = seed_e2e.generate_synthetic_assets
maintenance_url = seed_e2e.maintenance_url
synthetic_users = seed_e2e.synthetic_users
validate_e2e_target = seed_e2e.validate_e2e_target


def test_seed_refuses_non_e2e_environment() -> None:
    with pytest.raises(RuntimeError, match="APP_ENV=e2e"):
        validate_e2e_target(
            "test",
            "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e",
        )


@pytest.mark.parametrize("database", ["lost_found", "lost_found_test", "e2e"])
def test_seed_refuses_non_isolated_database_names(database: str) -> None:
    with pytest.raises(RuntimeError, match="must end with _e2e"):
        validate_e2e_target(
            "e2e",
            f"postgresql+asyncpg://app:app@127.0.0.1:55432/{database}",
        )


def test_target_uses_only_lost_found_as_the_maintenance_database() -> None:
    target = validate_e2e_target(
        "e2e",
        "postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e",
    )

    assert target.database == "lost_found_e2e"
    assert maintenance_url(target).database == "lost_found"


def test_reset_scope_contains_only_application_metadata_tables() -> None:
    table_names = application_table_names()

    assert "users" in table_names
    assert "item_records" in table_names
    assert "alembic_version" not in table_names


def test_synthetic_users_use_real_password_hashes_and_roles() -> None:
    admin, user = synthetic_users()

    assert admin.role is UserRole.ADMIN
    assert user.role is UserRole.USER
    assert verify_password(E2E_ADMIN_PASSWORD, admin.password_hash)
    assert verify_password(E2E_USER_PASSWORD, user.password_hash)
    assert E2E_ADMIN_PASSWORD not in admin.password_hash
    assert E2E_USER_PASSWORD not in user.password_hash


def test_generated_assets_are_two_isolated_synthetic_pngs(tmp_path: Path) -> None:
    paths = generate_synthetic_assets(tmp_path)

    assert {path.name for path in paths} == {
        "synthetic-other.png",
        "synthetic-id.png",
    }
    assert {path.parent for path in paths} == {tmp_path}
    for path in paths:
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (960, 600)
            assert image.mode == "RGB"
