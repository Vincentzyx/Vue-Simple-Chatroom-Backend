from typing import *
from functools import wraps
import BVEncode
import json
import Utils
import SqlHelper
from Exceptions import vException
from flask_socketio import SocketIO

MSG_PER_PAGE = 20


def param_sql_escape(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        newArgs = []
        newkwArgs = {}
        for arg in args:
            newArgs.append(Utils.sqlEscapeStr(arg))
        for key in kwargs:
            newkwArgs.update({key: Utils.sqlEscapeStr(kwargs[key])})
        result = func(*newArgs, **newkwArgs)
        return result

    return decorated


class Room:
    RoomId: str
    Name: str
    Avatar: str
    Description: str

    def __init__(self, jsonStr=""):
        if len(jsonStr) > 0:
            jsonInfo = json.loads(jsonStr)
            self.RoomId = jsonInfo["RoomId"]
            self.Name = jsonInfo["Name"]
            self.Avatar = jsonInfo["Avatar"]
            self.Description = jsonInfo["Description"]
        else:
            self.RoomId = BVEncode.gen()
            self.Name = "新建群聊"
            self.Avatar = ""
            self.Description = "群主是条懒狗，什么都没有留下"

    def dumps(self) -> str:
        return json.dumps({
            "RoomId": self.RoomId,
            "Name": self.Name,
            "Avatar": self.Avatar,
            "Description:": self.Description
        })


class Msg:
    Id: str
    User: str
    Content: str

    def __init__(self, id: str, user: str, content: str):
        self.Id = id
        self.User = user
        self.Content = content


class User:
    Id: str
    Name: str

    def __init__(self, id: str = "", name: str = ""):
        if id == "":
            self.Id = Utils.gen_str()
        else:
            self.Id = id
        self.Name = name


class API:

    @staticmethod
    def createRoom():
        room = Room()
        SqlHelper.execute(
            "INSERT INTO `roomlist`(`roomid`, `name`, `avatar`, `description`) VALUES ('%s','%s','%s','%s')"
            % (room.RoomId, room.Name, room.Avatar, room.Description))
        return {
            "roomid": room.RoomId,
            "name": room.Name,
            "avatar": room.Avatar,
            "description": room.Description
        }

    @staticmethod
    @param_sql_escape
    def deleteRoom(room: str):
        result = SqlHelper.execute(
            "DELETE FROM `roomlist` WHERE `roomid` = '%s'"
            % room)
        if not result:
            raise vException(-10000, "删除失败！（聊天室不存在）")

    @staticmethod
    @param_sql_escape
    def getRoomInfo(room: str):
        result = SqlHelper.fetchOne("SELECT `roomid`, `name`, `avatar`, `description` FROM `roomlist` "
                                    "WHERE `roomid` = '%s'" % room)
        if result is not None:
            return {
                "roomid": result[0],
                "name": result[1],
                "avatar": result[2],
                "desciption": result[3]
            }
        else:
            return None

    @staticmethod
    @param_sql_escape
    def setRoomName(room: str, name: str):
        result = SqlHelper.execute(
            "UPDATE `roomlist` SET `name`= '%s' WHERE `roomid` = '%s'"
            % (name, room))

    @staticmethod
    @param_sql_escape
    def setRoomAvatar(room: str, avatar: str):
        result = SqlHelper.execute(
            "UPDATE `roomlist` SET `avatar`= '%s' WHERE `roomid` = '%s'"
            % (avatar, room))

    @staticmethod
    @param_sql_escape
    def setRoomDescription(room: str, description: str):
        result = SqlHelper.execute(
            "UPDATE `roomlist` SET `description`= '%s' WHERE `roomid` = '%s'"
            % (description, room))

    @staticmethod
    @param_sql_escape
    def getOnlineList(room: str) -> List[User]:
        result = SqlHelper.fetchAll("SELECT `id`, `name` FROM `user` WHERE `room` = '%s'" % room)
        userList = []
        for u in result:
            user = User(u[0], u[1])
            userList.append(user)
        return userList

    @staticmethod
    @param_sql_escape
    def getChatHistory(room: str, page: int = 1, frommsg: int = -1) -> List[Msg]:
        sql = "SELECT `id`, `user`, `room`, `msg` FROM `chat` WHERE `room` = '%s' " % room
        if frommsg > 0:
            sql += "`id` < %d " % frommsg
        sql += "LIMIT %d,%d " % ((page - 1) * MSG_PER_PAGE, MSG_PER_PAGE)
        result = SqlHelper.fetchAll(sql)
        msgList = []
        for rawMsg in result:
            msg = Msg(rawMsg[0], rawMsg[1], rawMsg[3])
            msgList.append(msg)

        return msgList

    @staticmethod
    @param_sql_escape
    def sendMsg(room: str, user: str, msg: str) -> str:
        mid = SqlHelper.execute("INSERT INTO `chat`(`user`, `room`, `msg`) VALUES ('%s','%s','%s')"
                          % (user, room, msg), "insert")
        return str(mid)

    @staticmethod
    @param_sql_escape
    def userConnect(room: str, userid: str, username: str):
        SqlHelper.execute()