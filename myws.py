from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import database
import sec

rt = APIRouter()

rooms: dict[str, dict[str, WebSocket]] = {}


@rt.websocket("/ws/{room}")
async def wsroom(ws: WebSocket, room: str, token: str):
    await ws.accept()

    user = sec.read_tk(tk=token)

    if user is None:
        await ws.close(code=4001)
        return

    username = user.get("username", "xz_kto")

    if room not in rooms:
        rooms[room] = {}
    rooms[room][username] = ws

    async with database.s() as db:
        history = await database.get_history(db, room)
        await ws.send_json({"type": "history", "data": history})

        try:
            while 1:
                data: dict = await ws.receive_json()

                msg = {
                    "type": "message",
                    "data": {
                        "user": username,
                        "text": data["text"],
                        "time": datetime.now(timezone.utc)
                        .replace(tzinfo=None)
                        .isoformat()
                        + "Z",
                    },
                }

                await database.save_message(db, room, username, data["text"])

                await ws.send_json(msg)

                for us, con in rooms[room].items():
                    try:
                        if us != username:
                            await con.send_json(msg)
                    except:
                        pass

        except WebSocketDisconnect:
            if room in rooms:
                if username in rooms[room]:
                    del rooms[room][username]
                if not rooms[room]:
                    del rooms[room]
