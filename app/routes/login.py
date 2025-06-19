from app.core.config import settings
from app.core.db import async_session
from app.core.security import (
    verify_password,
    create_access_token,
    set_token_cookie,
)
from datetime import timedelta
from nuvie_db.nuvie.dto import Token
from nuvie_db.nuvie.models.user import User
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from typing import Annotated


router = APIRouter()


@router.post('/access-token')
async def login_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Rota de login com OAuth2, retorna um acess token
    """
    async with async_session() as session:
        print(form_data.username)
        statement = select(User).where(User.user_name == form_data.username)
        result = await session.exec(statement)
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=400, detail='Incorrect email or password'
            )
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=403, detail='Incorrect email or password'
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )

    set_token_cookie(response, access_token)

    return Token(access_token=access_token)
