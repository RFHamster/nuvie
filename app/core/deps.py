import jwt

from app.core import security
from app.core.config import settings
from app.core.db import async_session
from nuvie_db.nuvie.dto import TokenPayload
from nuvie_db.nuvie.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from typing import Annotated, Type

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f'/api/v1/users/login/access-token')

## README.md
## Deixei esse pattern escrito aqui porque é muito comum em projetos.
## Mas pelo fato de como o FastAPI funciona com o SQLModel
## quando você deixa o unicorn/fastapi gerenciar a abertura de Session do banco (Deps)
## Ele deixa as connections por thread (workes) abertas
## (trabalhar com thread em python é uma bagunça)
## E como queremos microserviços altamente escaláveis,
## essas conections em iddle podem derrubar o banco
async def get_db():
    async with async_session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(token: TokenDep) -> Type[User]:
    async with async_session() as session:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except Exception as e:
            await session.close()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Could not validate credentials',
            )
        user = await session.get(User, token_data.sub)
        await session.close()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
