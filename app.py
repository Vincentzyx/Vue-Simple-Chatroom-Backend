from flask import Flask, request, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from functools import wraps
from Exceptions import vException
import json
from AppFunctions import API
import Utils

app = Flask(__name__)
app.secret_key = ' A\xcd!x\xa6a\xffS\xcc\xc9\xdf?\x15\xd7\xbb\xdf\x0b\x9f\x1cy\xdcb\x8b'
socketio = SocketIO(app)


def json_response(func):
    @wraps(func)
    def decorated(*args, **kwargs) -> str:
        res = {
            "code": 0,
            "msg": ""
        }
        data = None
        try:
            data = func(*args, **kwargs)
        except vException as e:
            res["code"] = e.args[0]
            res["msg"] = e.args[1]

        if data is not None:
            res.update({
                "data": data
            })
        return json.dumps(res, default=str, ensure_ascii=False)

    return decorated


def need_user(func):
    @wraps(func)
    def decorated(*args, **kwargs) -> str:
        if "uid" not in session:
            session["uid"] = Utils.gen_str()
            session["name"] = "用户" + session["uid"][:6]
        return func(*args, **kwargs)
    return decorated


def WrapInfo(code: int, msg: str, data=None):
    if data is None:
        data = {}
    return {
        "code": code,
        "msg": msg,
        "data": data
    }


@app.route('/')
@json_response
def index():
    print("test")
    raise vException(-10001, "Wrong usage.")


@socketio.on("message")
@need_user
def handle_message(message):
    uid = session["uid"]
    name = session["name"]
    if "roomid" not in session:
        emit("info", WrapInfo(-1, "请先加入一个房间"), json=True)
        return
    roomId = session["roomid"]
    mid = API.sendMsg(roomId, uid, message)
    msg = {
        "id": mid,
        "user": uid,
        "name": name,
        "msg": message
    }
    emit("message", msg, json=True, broadcast=True)


@socketio.on("create_room")
@need_user
def create_room():
    roomInfo = API.createRoom()
    roomId = roomInfo["roomid"]
    join_room(roomId)
    session["roomid"] = roomId
    emit("info", WrapInfo(1001, "Room created!"), json=True, room=roomId)
    emit("info", WrapInfo(2001, "更新房间信息", roomInfo), json=True, room=roomId)


@socketio.on("join_room")
@need_user
def join_chatroom(roomId):
    roomInfo = API.getRoomInfo(roomId)
    if roomInfo is not None:
        join_room(roomId)
        session["roomid"] = roomId
        emit("info", WrapInfo(1001, "您已加入房间"), json=True, room=roomId)
        emit("info", WrapInfo(2001, "更新房间信息", roomInfo), json=True, room=roomId)
    else:
        info = WrapInfo(-2, "房间不存在！")
        emit("info", info)


with app.test_request_context():
    print("Testing...")

if __name__ == '__main__':
    socketio.run(app)
