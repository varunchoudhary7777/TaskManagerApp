from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories import user_repository
from app.schemas.auth import TokenResponse, UserLogin
from app.schemas.user import UserRegister, UserResponse, UserChangeRole
from app.services import auth_service

from app.schemas.auth import (
    RefreshTokenRequest,
    TokenPairResponse,
)

from app.schemas.user import(
    UserSortBy,
    SortOrder,
)
from collections.abc import Callable
from app.core.rate_limit import rate_limit
RateLimit = Annotated[Callable, Depends(rate_limit)]

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

DbSession = Annotated[
    Session,
    Depends(get_db)
]

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

@router.post("/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("auth:register", 3,60 * 60)),],
)
def register(data: UserRegister, db:DbSession) -> UserResponse:
    return auth_service.register_user(
        db=db,
        data=data,
    )

@router.post(
    "/login",
    response_model=TokenPairResponse,
    dependencies=[
        Depends(rate_limit("auth:login", 5, 60)),
    ],
)
def login(
        data: UserLogin,
        db: DbSession,
) -> TokenResponse:
    return auth_service.login_user(db=db, data=data)

@router.get("/me")
def get_my_profile(
        current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)

@router.put("/change_role/{user_id}",response_model=UserResponse,status_code=status.HTTP_200_OK)
def change_user_role(
        db: DbSession,
        user_id: int,
        data: UserChangeRole,
        current_user: CurrentUser,
):
    return auth_service.change_user_role(db, user_id, data, current_user)

@router.get("/users/", response_model = UserResponse, status_code = status.HTTP_200_OK)
def list_users(
        db: DbSession,
        current_user: CurrentUser,
        limit: int = Query(default=20, ge=1, le=100),
        skip: int = Query(default=0, ge=0),
        role: UserRole | None = Query(defualt=None),
        search: str | None = Query(default=None, min_length=1, max_length=100),
        sort_by: UserSortBy = Query(default=UserSortBy.CREATED_AT),
        sort_order: SortOrder = Query(default=SortOrder.DESC),
) -> list[UserResponse]:
    return user_repository.list_users(
        db=db,
        current_user=current_user,
        limit=limit,
        skip=skip,
        role=role,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

@router.post(
    "/refresh",
    response_model = TokenPairResponse,
    dependencies=[
        Depends(rate_limit("auth:refresh", 10, 60))
    ],
)
def refresh_token(
        db: DbSession,
        data: RefreshTokenRequest,
) -> TokenPairResponse:
    return auth_service.refresh_access_token(
        db = db,
        data = data,
    )

@router.post("/logout", status_code = status.HTTP_204_NO_CONTENT)
def logout(
        db: DbSession,
        data: RefreshTokenRequest,
) -> None:
    auth_service.logout(
        db = db,
        data = data,
    )