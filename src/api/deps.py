from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core import security
from src.api.dependencies import get_db
from src.domain.ledger import models
from src.infra.cache import cache
from src.domain.security import models as security_models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/ledger/auth/login")


async def get_current_account(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])

        user_id = payload.get("sub")
        token_type = payload.get("type")
        account_id = payload.get("account_id")
        jti = payload.get("jti")

        if not user_id or token_type != "access" or not account_id or not jti:
            raise credentials_exception

        try:
            if await cache.is_jti_blacklisted(str(jti)):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token revogado. Faca login novamente."
                )
        except Exception:
            # Se Redis cair, nao trava tudo (dev-friendly). Em prod, pode fail-close em rotas sensiveis.
            pass

    except (PyJWTError, ValueError, TypeError):
        raise credentials_exception

    stmt_sess = select(security_models.Session).where(security_models.Session.jti == str(jti))
    res_sess = await db.execute(stmt_sess)
    sess = res_sess.scalar_one_or_none()
    if sess and sess.revoked:
        raise credentials_exception

    stmt = select(models.Account).options(selectinload(models.Account.owner)).where(
        models.Account.id == int(account_id),
        models.Account.user_id == int(user_id),
    )
    result = await db.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise credentials_exception

    return account
