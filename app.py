from flask import Flask, request, session, send_from_directory
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from functools import wraps
from Exceptions import vException
import json
from AppFunctions import API
import Utils
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = ' A\xcd!x\xa6a\xffS\xcc\xc9\xdf?\x15\xd7\xbb\xdf\x0b\x9f\x1cy\xdcb\x8b'
socketio = SocketIO(app)


def json_response(func):
    @wraps(func)
    def decorated(*args, **kwargs):
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
        return res  # json.dumps(res, default=str, ensure_ascii=False)

    return decorated


def need_user(func):
    @wraps(func)
    def decorated(*args, **kwargs) -> str:
        if "uid" not in session:
            session["uid"] = Utils.gen_str()
            session["name"] = "用户" + Utils.md5_vsalt(session["uid"])[:6]
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


# @socketio.on_error()
# @json_response
# def handle_error(e):
#     raise vException(-10000, "Wrong params")


@socketio.on('connect')
@need_user
def handle_connect():
    emit('give_id', WrapInfo(0, "Connected", {
        "uid": session["uid"],
        "uidMd5": Utils.md5_vsalt(session["uid"]),
        "name": session["name"]
    }))


@socketio.on('disconnect')
def handle_disconnect():
    if "roomid" in session:
        uidMd5 = Utils.md5_vsalt(session["uid"])
        print(uidMd5, "disconnected.")
        result = API.removeUser(session["roomid"], session["uid"])
        if result:
            emit("user_record", WrapInfo(0, "leave", {
                "uid": uidMd5,
                "name": session["name"]
            }), room=session["roomid"])


@app.route('/')
@json_response
def index():
    raise vException(-10001, "Wrong usage.")


@socketio.on("message")
@json_response
def handle_message(message):
    uid = session["uid"]
    name = session["name"]
    if "roomid" not in session:
        raise vException(-1, "请先加入一个房间")
    roomId = session["roomid"]
    mid = API.sendMsg(roomId, uid, name, message)
    msg = {
        "id": mid,
        "user": Utils.md5_vsalt(uid),
        "name": name,
        "msg": message,
        "time": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    emit("message", WrapInfo(0, "消息", msg), json=True, room=roomId)
    return True


@socketio.on("create_room")
@json_response
def create_room():
    roomInfo = API.createRoom()
    if "roomid" in session:
        leave_room(session["roomid"])
        API.removeUser(session["roomid"], session["uid"])
        emit("user_record", WrapInfo(0, "leave", {
            "uid": Utils.md5_vsalt(session["uid"]),
            "name": session["name"]
        }), room=session["roomid"])
    roomId = roomInfo["roomid"]
    join_room(roomId)
    session["roomid"] = roomId
    API.recordUser(roomId, session["uid"], session["name"])
    return roomInfo


@socketio.on("delete_room")
@json_response
def delete_room(roomId):
    roomInfo = API.getRoomInfo(roomId)
    if roomInfo is not None:
        creator = API.getFirstMember(roomId)
        if creator["user"] == session["uid"]:
            API.deleteRoom(roomId)
            return True
        else:
            raise vException(-2, "你不是群主！")
    else:
        raise vException(-1, "房间不存在！")


@socketio.on("join_room")
@json_response
def join_chatroom(roomId, leavePrev):
    roomInfo = API.getRoomInfo(roomId)
    if roomInfo is not None:
        if leavePrev:
            if "roomid" in session and session["roomid"] != roomId:
                leave_room(session["roomid"])
                API.removeUser(session["roomid"], session["uid"])
                emit("user_record", WrapInfo(0, "leave", {
                    "uid": Utils.md5_vsalt(session["uid"]),
                    "name": session["name"]
                }), room=session["roomid"])
        join_room(roomId)
        session["roomid"] = roomId
        API.recordUser(roomId, session["uid"], session["name"])
        print("record", roomId, session["uid"], session["name"])
        emit("user_record", WrapInfo(0, "join", {
            "uid": Utils.md5_vsalt(session["uid"]),
            "name": session["name"]
        }), room=roomId)
        print("join")
        return roomInfo
    else:
        raise vException(-1, "房间不存在")


@socketio.on("leave_room")
@json_response
def leave_chatroom():
    if "roomid" in session:
        result = API.removeUser(session["roomid"], session["uid"])
        if result:
            emit("user_record", WrapInfo(0, "leave", {
                "uid": Utils.md5_vsalt(session["uid"]),
                "name": session["name"]
            }), room=session["roomid"])
            print("leave")
            return True


@socketio.on("get_online")
@json_response
def get_online():
    if "roomid" in session:
        onlineList = API.getOnlineList(session["roomid"])
        print(session["roomid"])
        print("getonline")
        print(onlineList)
        return onlineList


@socketio.on("msg_history")
@json_response
def msg_history(roomId, page, frommsg):
    roomInfo = API.getRoomInfo(roomId)
    if roomInfo is not None:
        msgList = API.getChatHistory(roomId, page, frommsg)
        for msg in msgList["list"]:
            msg["user"] = Utils.md5_vsalt(msg["user"])
        return msgList
    else:
        raise vException(-1, "房间不存在")


@socketio.on('user_auth')
@json_response
def user_auth(user, name):
    if len(user) == 32:
        session["uid"] = user
        session["name"] = name
        return Utils.md5_vsalt(user)


@socketio.on('modify_roominfo')
@json_response
def modify_roominfo(roomId, newRoomInfo):
    roomInfo = API.getRoomInfo(roomId)
    if roomInfo is not None:
        creator = API.getFirstMember(roomId)
        if creator["user"] == session["uid"]:
            API.setRoomInfo(roomId, newRoomInfo["name"], newRoomInfo["avatar"], newRoomInfo["description"])
            return newRoomInfo
        else:
            raise vException(-2, "你不是群主！")
    else:
        raise vException(-1, "房间不存在！")


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/avatar-upload', methods=['POST'])
@json_response
def upload_avatar():
    if request.method == 'POST':
        if 'file' not in request.files:
            raise vException(-1, "File not found")
        file = request.files['file']
        if file.filename == '':
            raise vException(-2, "Filename is empty.")
        if file and allowed_file(file.filename):
            ext = file.filename.split('.')[-1]
            random_filename = Utils.gen_str()
            file_name = random_filename + "." + ext
            file.save(os.path.join("static", "avatar", file_name))
            return "/avatar/" + file_name
        else:
            raise vException(-3, "File format is not supported.")


def allowed_file2(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'doc', 'pptx', 'ppt', 'xls', 'xlsx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/attachment-upload', methods=['POST'])
@json_response
def upload_attachment():
    if request.method == 'POST':
        if 'file' not in request.files:
            raise vException(-1, "File not found")
        file = request.files['file']
        if file.filename == '':
            raise vException(-2, "Filename is empty.")
        if file and allowed_file2(file.filename):
            ext = file.filename.split('.')[-1]
            random_filename = Utils.gen_str()
            file_name = random_filename + "." + ext
            file.save(os.path.join("static", "attachments", file_name))
            return "/attachments/" + file_name
        else:
            raise vException(-3, "File format is not supported.")


@app.route("/avatar/<path:path>")
def send_avatar(path):
    return send_from_directory("static/avatar", path)


@app.route("/attachments/<path:path>")
def send_attachments(path):
    return send_from_directory("static/attachments", path)


with app.test_request_context():
    print("Testing...")

if __name__ == '__main__':
    socketio.run(app)
