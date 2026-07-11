import uvicorn
from fastapi import FastAPI, Depends, Form, Request, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from schemas import Reg
from typing import Annotated
import sec, database

from myws import rt

app=FastAPI()
app.mount(r"/static",
        StaticFiles(directory="static"),
        name="static")

dep = Annotated[database.AsyncSession, Depends(database.get_db)] #чтобы каждый раз не писать Depends



app.include_router(rt)#подключение вебсокетов



@app.post('/register')
async def register(payload: Reg, db: dep):
    try:
        await database.registration(payload, db)
    except Exception:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='user alr exists')
    return {'user': 'created'}

@app.post('/login')
async def login(
    db: dep,
    username: str = Form(...),
    password: str = Form(...)
):
    u: database.users=await database.login(username, password, db)
    if u is not None:
        tk=sec.create_tk({'userid': u.id, 'username': u.username})
        return {
  "access_token": tk,
  "token_type": "bearer"
}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='someth wrong')
  
@app.get('/me')
async def me(req: Request):
    t=req.headers.get('authorization')
    t=t[7:]
    resp=sec.read_tk(t)
    print(resp)
    return resp


@app.get("/")
def index():
    return FileResponse("static/index.html")


if __name__=='__main__':
    uvicorn.run("main:app", reload=True)