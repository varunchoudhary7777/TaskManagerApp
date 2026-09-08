from collections.abc import Generator
from app.api.dependencies import get_current_user

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.team_member import TeamMember
from app.db.session import Base, get_db
from app.main import app
from app.db.models.user import UserRole

if settings.test_database_url is None:
    raise RuntimeError(
        "TEST_DATABASE_URL is missing from .env"
    )

test_engine=create_engine(settings.test_database_url)
TestingSessionLocal=sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)

@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db=TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(
        db_session: Session,
) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db]=override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
            email="varun123@example.com",
            role=UserRole.ADMIN,
            full_name="varun choudhary",
            password_hash="hash_examplepassword"
        )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_client(
        db_session: Session,
        admin_user: User,
) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db]=override_get_db
    app.dependency_overrides[get_current_user]=override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def developer_user(db_session: Session) -> User:
    user = User(
        email="developer@test.com",
        full_name="Developer",
        password_hash="hash",
        role=UserRole.DEVELOPER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def manager_user(db_session: Session) -> User:
    user = User(
        email="manager@test.com",
        full_name="Manager",
        password_hash="hash",
        role = UserRole.MANAGER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def manager_client(
        db_session: Session,
        manager_user: User,
) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return manager_user

    app.dependency_overrides[get_db]=override_get_db
    app.dependency_overrides[get_current_user]=override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def user_client(
        db_session: Session,
        developer_user: User,
) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return developer_user

    app.dependency_overrides[get_db]=override_get_db
    app.dependency_overrides[get_current_user]=override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def auth_client(db_session: Session):

    def create(user: User):

        def override_get_db():
            yield db_session

        def override_get_current_user():
            return user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        return TestClient(app)

    return create