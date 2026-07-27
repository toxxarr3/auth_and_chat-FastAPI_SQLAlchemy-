from typing import Annotated

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import database
import sec
from myws import rt
from schemas import Reg


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.eng.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.mount(r"/static", StaticFiles(directory="static"), name="static")

dep = Annotated[
    database.AsyncSession, Depends(database.get_db)
]  # чтобы каждый раз не писать Depends


app.include_router(rt)  # подключение вебсокетов


@app.post("/register")
async def register(payload: Reg, db: dep):
    try:
        await database.registration(payload, db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user alr exists"
        )
    return {"user": "created"}


@app.post("/login")
async def login(db: dep, username: str = Form(...), password: str = Form(...)):
    u: database.users = await database.login(username, password, db)
    if u is not None:
        tk = sec.create_tk({"userid": u.id, "username": u.username})
        return {"access_token": tk, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="someth wrong")


@app.get("/me")
async def me(req: Request):
    t = req.headers.get("authorization")
    t = t[7:]
    resp = sec.read_tk(t)
    print(resp)
    return resp


@app.get("/")
def index():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
