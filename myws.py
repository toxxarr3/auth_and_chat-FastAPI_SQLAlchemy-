from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import sec

rt=APIRouter()

      #{'room': {'user1': 'ws://...', 'user2': 'ws://...'}}
rooms: dict[str, dict[str, WebSocket]] ={}

@rt.websocket('/ws/{room}')
async def wsroom(ws: WebSocket, room: str, token: str):
    await ws.accept()
    

    #print(f'\n\n\nws:\n{ws}\n\nroom:\n{room}\n\ntk:\n{token}\n\n\n') 

    user=sec.read_tk(tk=token)

    if user is None:
        await ws.close(code=4001)
        return
    
    username=user.get('username', 'xz_kto')

    if room not in rooms:
        rooms[room]={}
    rooms[room][username]=ws


    try:
        while 1:
            data: dict= await ws.receive_json()

            #print(f'\n\n{data}\n\n')
            #msg_type = data.get('type') #(public or private) will add later mb

            msg={'type': 'message', "data": {
                'user': username+' sosal',
                'text': data['text'],
                'time': datetime.now().isoformat()
            }}



            #рассылка всем

            await ws.send_json(msg)#сообщение себе

            for us, con in rooms[room].items():
                try:
                    if us!=username:
                        await con.send_json(msg)
                except: pass

    except WebSocketDisconnect:

        if room in rooms:
            if username in rooms[room]:
                del rooms[room][username]
            if not rooms[room]:
                del rooms[room]

        #print('\n\ncon closed\n\n')