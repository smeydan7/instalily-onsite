"""Account business logic. Thin over the ORM for now; grows as rules appear."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


def list_accounts(db: Session, *, limit: int = 50, offset: int = 0) -> tuple[list[Account], int]:
    total = db.scalar(select(func.count()).select_from(Account)) or 0
    rows = db.scalars(
        select(Account).order_by(Account.name).limit(limit).offset(offset)
    ).all()
    return list(rows), total


def get_account(db: Session, account_id: int) -> Account | None:
    return db.get(Account, account_id)


def create_account(db: Session, data: AccountCreate) -> Account:
    account = Account(**data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(db: Session, account: Account, data: AccountUpdate) -> Account:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account: Account) -> None:
    db.delete(account)
    db.commit()
