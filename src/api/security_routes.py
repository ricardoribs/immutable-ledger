from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.dependencies import get_db
from src.api import deps
from src.domain.security import schemas, services
from src.domain.security import models as security_models
from src.domain.ledger import models as ledger_models

router = APIRouter(prefix="/security", tags=["Security"])


@router.post("/password/reset/request")
async def request_password_reset(data: schemas.PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    token = await services.SecurityService.request_password_reset(db, data.email)
    return {"status": "ok", "token": token}


@router.post("/password/reset/confirm")
async def confirm_password_reset(data: schemas.PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    ok = await services.SecurityService.confirm_password_reset(db, data.token, data.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Token invalido ou expirado")
    return {"status": "ok"}


@router.get("/devices", response_model=list[schemas.DeviceResponse])
async def list_devices(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(security_models.Device).where(security_models.Device.user_id == current_account.owner.id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/devices/{device_id}/revoke")
async def revoke_device(
    device_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    await services.SecurityService.revoke_device(db, device_id, current_account.owner.id)
    return {"status": "ok"}


@router.get("/sessions", response_model=list[schemas.SessionResponse])
async def list_sessions(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(security_models.Session).where(security_models.Session.user_id == current_account.owner.id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    await services.SecurityService.revoke_session(db, session_id, current_account.owner.id)
    return {"status": "ok"}


@router.get("/alerts", response_model=list[schemas.SecurityAlertResponse])
async def list_alerts(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(security_models.SecurityAlert).where(security_models.SecurityAlert.user_id == current_account.owner.id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/audit", response_model=list[schemas.AuditLogResponse])
async def list_audit_logs(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ledger_models.AuditLog)
        .where(ledger_models.AuditLog.user_id == current_account.owner.id)
        .order_by(ledger_models.AuditLog.id.desc())
        .limit(200)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/otp/request")
async def request_otp(
    data: schemas.OtpRequest,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    code = await services.SecurityService.request_otp(db, current_account.owner.id, data.channel)
    return {"status": "ok", "code": code}


@router.post("/otp/verify")
async def verify_otp(
    data: schemas.OtpVerify,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    ok = await services.SecurityService.verify_otp(db, current_account.owner.id, data.channel, data.code)
    if not ok:
        raise HTTPException(status_code=400, detail="OTP invalido")
    return {"status": "ok"}


@router.post("/questions")
async def add_question(
    data: schemas.SecurityQuestionCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    await services.SecurityService.add_security_question(db, current_account.owner.id, data.question, data.answer)
    return {"status": "ok"}


@router.get("/questions", response_model=list[schemas.SecurityQuestionResponse])
async def list_questions(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(security_models.SecurityQuestion).where(
        security_models.SecurityQuestion.user_id == current_account.owner.id
    )
    res = await db.execute(stmt)
    return res.scalars().all()
