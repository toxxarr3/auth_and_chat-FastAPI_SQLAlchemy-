import asyncio
from datetime import datetime, timezone
from os import getenv

from sqlalchemy import (
    Integer,
    String,
    Text,
    delete,
    insert,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from schemas import Base, Reg

eng = create_async_engine(url=getenv("pg_url", ""))

s = async_sessionmaker(bind=eng)


async def get_db():
    async with s() as dtb:
        yield dtb


class users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"USER(id={self.id}, usnm={self.username}, pwd={self.password})"


class messages(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


async def save_message(db: AsyncSession, room: str, username: str, text: str):
    if room != "general":
        return
    msg = messages(room=room, username=username, text=text)
    db.add(msg)
    await db.commit()

    subq = (
        select(messages.id)
        .where(messages.room == room)
        .order_by(messages.created_at.desc())
        .offset(15)
        .scalar_subquery()
    )
    await db.execute(delete(messages).where(messages.id.in_(subq)))
    await db.commit()


async def get_history(db: AsyncSession, room: str):
    q = (
        select(messages)
        .where(messages.room == room)
        .order_by(messages.created_at.asc())
        .limit(15)
    )
    res = await db.execute(q)
    rows = res.scalars().all()
    return [
        {"user": r.username, "text": r.text, "time": r.created_at.isoformat() + "Z"}
        for r in rows
    ]


async def rebase(db: AsyncSession):
    con = await db.connection()
    await con.run_sync(Base.metadata.drop_all)
    await con.run_sync(Base.metadata.create_all)
    await db.commit()


async def registration(user_info: Reg, db: AsyncSession):
    usr = users(username=user_info.username, password=user_info.password)
    db.add(usr)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(usr)
    return {"status": "user added"}


async def ins(db: AsyncSession):
    await db.execute(
        insert(users).values(
            [
                {"username": "admin", "password": "admin123"},
                {"username": "zxcqwe", "password": "zxcqwe123"},
                {"username": "testuser", "password": "test123"},
            ]
        )
    )
    await db.commit()


async def login(username: str, password: str, db: AsyncSession):
    q = select(users).where(users.username == username, users.password == password)
    a = await db.scalar(q)
    print(a, type(a))
    return a


async def test(db: AsyncSession):
    q = select(users)
    res = await db.scalars(q)
    return res.all()


async def main():
    async with s() as ss:
        await rebase(db=ss)
        await ins(db=ss)
        # e = await test(db=ss)
        # for ee in e:
        #    print(ee)


if __name__ == "__main__":
    asyncio.run(main())
