import pytest
from sqlalchemy import create_engine

from identa.db.roles import RoleError, grant_application_role, role_statements


def rendered(statements) -> list[str]:
    return [repr(statement) for statement in statements]


def test_role_statements_keep_audit_append_only():
    statements = " ".join(rendered(role_statements("identa_app", "senha'com aspas", "identa")))
    assert "REVOKE UPDATE, DELETE ON " in statements
    assert "'audit_log'" in statements
    assert "'alembic_version'" in statements
    assert "senha'com aspas" in statements


def test_role_requires_postgres(tmp_path):
    with pytest.raises(RoleError, match="PostgreSQL"):
        grant_application_role(create_engine(f"sqlite:///{tmp_path / 'x.db'}"), "identa_app", "x" * 20)


@pytest.mark.parametrize(("role", "password", "message"), [("Identa-App", "x" * 20, "inválido"), ("identa_app", "curta", "16")])
def test_role_rejects_bad_input(role, password, message):
    engine = create_engine("postgresql+psycopg://identa@127.0.0.1:1/identa")
    with pytest.raises(RoleError, match=message):
        grant_application_role(engine, role, password)
