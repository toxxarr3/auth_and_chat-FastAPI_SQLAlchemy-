from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


class Reg(BaseModel):
    username: str
    password: str

class Base(DeclarativeBase):
    pass