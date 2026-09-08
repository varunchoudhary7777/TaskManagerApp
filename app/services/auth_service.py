from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.config import Settings, settings
from app.core.security import(
        create_access_token,
        hash_password,
        verify_password,
        create_refresh_token,
        hash_refresh_token,
)

from app.db.models.refresh_token import RefreshToken
from app.repositories import refresh_token_repository
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenPairResponse,
)

from app.db.models.user import User, UserRole
from app.repositories import user_repository
from app.schemas.auth import TokenResponse, UserLogin
from app.schemas.user import UserRegister, UserResponse, UserChangeRole

from app.schemas.user import(
    UserSortBy,
    SortOrder,
)

from app.core.cache import (
    delete_cache,
    get_cache_version,
    increment_cache_version,
    get_cache_json,
    set_cache_json,
)

USERS_LIST_CACHE_PREFIX = "users:list"
USERS_LIST_CACHE_VERSION = "users:list:version"

def register_user(
        db:Session,
        data: UserRegister,
) -> UserResponse:
    existing_user= user_repository.get_by_email(
        db,
        data.email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    user=User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
    )

    created_user = user_repository.create(
        db,
        user,
    )

    increment_cache_version(USERS_LIST_CACHE_VERSION)

    return UserResponse.model_validate(created_user)

def login_user(
        db: Session,
        data: UserLogin,
) -> TokenPairResponse:
    user = user_repository.get_by_email(
        db,
        data.email,
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_token_pair(
        db = db,
        user = user,
    )

def change_user_role(
        db: Session,
        user_id: int,
        data: UserChangeRole,
        current_user: User,
) -> UserResponse:
    require_admin(current_user)
    existing_user=user_repository.get_by_id(db, user_id)
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user doesn't exist!"
        )

    user=user_repository.change_user_role(db, existing_user, data.new_role)

    increment_cache_version(USERS_LIST_CACHE_VERSION)

    return UserResponse.model_validate(user)

def get_users_list_cache_key(
        user_id: int,
        version: int,
        search_name: str | None,
        search_email: str | None,
        skip: int,
        limit: int,
        role: UserRole | None,
        created_at: datetime | None,
        sort_by: UserSortBy,
        sort_order: SortOrder,
) -> str:
    normalized_search_name = (search_name or "all").strip().lower()
    normalized_search_email = (search_email or "all").strip().lower()
    normalized_created_at = (
        created_at.isoformat()
        if created_at is not None
        else "all"
    )
    normalized_role = (
        role.value
        if role is not None
        else "all"
    )

    return (
        f"{USERS_LIST_CACHE_PREFIX}:"
        f"user:{user_id}:"
        f"v:{version}:"
        f"search_name:{normalized_search_name}:"
        f"search_email:{normalized_search_email}:"
        f"created_at:{normalized_created_at}:"
        f"role:{normalized_role}:"
        f"skip:{skip}:"
        f"limit:{limit}:"
        f"sort:{sort_by}:{sort_order}"
    )

def list_users(
        db: Session,
        current_user: User,
        limit: int,
        skip: int,
        created_at: datetime | None,
        role: UserRole | None,
        search_name: str | None,
        search_email: str | None,
        sort_by: UserSortBy,
        sort_order: SortOrder,
) -> list[UserResponse]:

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can see the users!"
        )

    # Read the current_cache_version
    version = get_cache_version(USERS_LIST_CACHE_VERSION)

    #Redis.
    cache_key = get_users_list_cache_key(
        user_id=current_user.id,
        version=version,
        search_name=search_name,
        search_email=search_email,
        skip=skip,
        limit=limit,
        role=role,
        created_at=created_at,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    cached_users = get_cache_json(cache_key)

    if cached_users is not None:
        return [
            UserResponse.model_validate(user)
            for user in cached_users
        ]

    users = user_repository.list_users(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        role=role,
        search_name=search_name,
        created_at=created_at,
        search_email=search_email,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    users_response = [
        UserResponse.model_validate(user)
        for user in users
    ]

    set_cache_json(
        key=cache_key,
        value=[
            user.model_dump(mode="json")
            for user in users_response
        ]
    )

    return users_response


def create_token_pair(
        db: Session,
        user: User,
) -> TokenPairResponse:
    access_token = create_access_token(
        subject = str(user.id),
    )
    raw_refresh_token = create_refresh_token()

    refresh_token = RefreshToken(
        token_hash = hash_refresh_token(raw_refresh_token),
        user_id = user.id,
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days)
        ),
    )

    refresh_token_repository.create(
        db,
        refresh_token,
    )

    return TokenPairResponse(
        access_token = access_token,
        refresh_token = raw_refresh_token,
    )

def refresh_access_token(
        db: Session,
        data: RefreshTokenRequest,
) -> TokenPairResponse:
    token_hash = hash_refresh_token(
        data.refresh_token,
    )

    stored_token = refresh_token_repository.get_by_token_hash(
        db,
        token_hash,
    )

    if stored_token is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid refresh token",
        )

    now = datetime.now(timezone.utc)

    if stored_token.revoked_at is not None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid refresh token",
        )

    if stored_token.expires_at <= now:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Refresh token expired",
        )

    user = user_repository.get_by_id(
        db,
        stored_token.user_id,
    )

    if user is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid refresh token",
        )

    #Rotation: invalidate the used refresh token.
    refresh_token_repository.revoke(
        db,
        stored_token,
        now,
    )

    #Create a new access token and a new refresh token.
    return create_token_pair(
        db = db,
        user = user
    )

def logout(
        db: Session,
        data: RefreshTokenRequest,
) -> None:
    token_hash = hash_refresh_token(
        data.refresh_token,
    )

    stored_token = refresh_token_repository.get_by_token_hash(
        db,
        token_hash,
    )

    # Return success even if it is already missing or revoked.
    # This avoids revealing whether a token exist.

    if stored_token is None:
        return

    if stored_token.revoked_at is not None:
        return

    refresh_token_repository.revoke(
        db,
        stored_token,
        datetime.now(timezone.utc),
    )