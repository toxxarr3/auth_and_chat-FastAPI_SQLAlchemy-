import env, asyncio
from sqlalchemy import insert, Text, Column, Table, Integer, String, select, exists, ForeignKey, DateTime, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from schemas import Reg, Base

eng=create_async_engine(url=env.pg_url)

s=async_sessionmaker(bind=eng)

async def get_db():
        async with s() as dtb:
            yield dtb

class users(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    def __repr__(self):
        return f'USER(id={self.id}, usnm={self.username}, pwd={self.password})'

class rooms(Base):
    __tablename__ = 'rooms'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Связь с сообщениями
    messages: Mapped[list["messages"]] = relationship(back_populates="room")

class messages(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID пользователя
    sender_name: Mapped[str] = mapped_column(String, nullable=False)  # для быстрого отображения
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey('rooms.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String, default='public')  # 'public' или 'private'
    recipient_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # для приватных
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Связь с комнатой
    room: Mapped["rooms"] = relationship(back_populates="messages")





async def rebase(db: AsyncSession):
    con=await db.connection()
    await con.run_sync(Base.metadata.drop_all)
    await con.run_sync(Base.metadata.create_all)
    await db.commit()

async def registration(user_info: Reg, db: AsyncSession):
    usr=users(username=user_info.username, password=user_info.password)
    db.add(usr)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise 
    
    await db.refresh(usr)
    return {'status': 'user added'}

async def ins(db: AsyncSession):
    await db.execute(insert(users).values(
        [
    {'username': 'sosal', 'password': 'ruslan'},
    {'username': 'zxcqwe', 'password': 'qwe'},
    {'username': 'sobaka', 'password': 'qweqwe'}
]
))
    await db.commit()

async def login(username: str, password: str, db: AsyncSession):
    q=select(users).where(users.username==username, users.password==password)
    a=await db.scalar(q)
    print(a, type(a))
    return a

async def test(db: AsyncSession):
    q=select(users)
    res=await db.scalars(q)
    return res.all()

async def main():
    async with s() as ss:
        await rebase(db=ss)
        await ins(db=ss)
        e=await test(db=ss)
        for ee in e:
            print(ee)


if __name__=='__main__':
        asyncio.run(main())