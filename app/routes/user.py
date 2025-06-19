from typing import Any
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from nuvie_db.nuvie.models.user import User, UserCreate, UserPublic, UsersPublic

from app.core.db import async_session
from app.core.deps import CurrentUser
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/", response_model=UserPublic)
async def create_user(
    user_in: UserCreate,
) -> Any:
    """
    Criar novo usuário.
    """
    async with async_session() as session:
        existing_user_result = await session.exec(
            select(User).where(User.user_name == user_in.user_name)
        )
        existing_user = existing_user_result.first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Usuário com este nome já existe no sistema.",
            )

        user_data = user_in.model_dump()
        if user_data.get("password"):
            user_data["password"] = get_password_hash(user_data["password"])

        db_user = User.model_validate(user_data)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user


@router.get("/", response_model=UsersPublic)
async def read_users(
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = Query(default=100, le=100),
) -> Any:
    """
    Recuperar todos os usuários.
    """
    async with async_session() as session:
        count_result = await session.exec(select(User))
        count = len(count_result.all())

        result = await session.exec(select(User).offset(skip).limit(limit))
        users = result.all()

        return UsersPublic(data=users, count=count)


@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
        user_id: int,
        current_user: CurrentUser,
) -> Any:
    """
    Recuperar usuário por ID.
    """
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado.",
            )
        return user


@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        current_user: CurrentUser,
) -> None:
    """
    Deletar usuário.
    """
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado.",
            )

        await session.delete(user)
        await session.commit()
