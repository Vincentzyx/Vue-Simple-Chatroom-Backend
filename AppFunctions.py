from typing import *
from functools import wraps
import BVEncode
import json
import Utils
import SqlHelper
from Exceptions import vException
from flask_socketio import SocketIO

MSG_PER_PAGE = 21


def param_sql_escape(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        newArgs = []
        newkwArgs = {}
        for arg in args:
            if arg is str:
                newArgs.append(Utils.sqlEscapeStr(arg))
            else:
                newArgs.append(arg)
        for key in kwargs:
            if kwargs[key] is str:
                newkwArgs.update({key: Utils.sqlEscapeStr(kwargs[key])})
            else:
                newkwArgs.update({key: kwargs[key]})
        result = func(*newArgs, **newkwArgs)
        return result

    return decorated


class Room:
    RoomId = ""
    Name = ""
    Avatar = ""
    Description = ""

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
    Id = ""
    User = ""
    Content = ""

    def __init__(self, id: str, user: str, content: str):
        self.Id = id
        self.User = user
        self.Content = content


class User:
    Id = ""
    Name = ""

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
                "description": result[3]
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
    def setRoomInfo(room: str, name: str, avatar: str, description: str):
        result = SqlHelper.execute(
            "UPDATE `roomlist` SET `name`='%s',`avatar`='%s',`description`='%s' WHERE `roomid`='%s'"
            % (name, avatar, description, room))
        if not result:
            raise vException(-100, "修改房间信息失败！")

    @staticmethod
    @param_sql_escape
    def recordUser(room: str, uid: str, name: str):
        prevRecord = SqlHelper.fetchOne("SELECT `id`,`name`,`room` FROM `user` WHERE `id`='%s' AND `room`='%s'"
                                        % (uid, room))
        if prevRecord is not None:
            if prevRecord[1] != name:
                result = SqlHelper.execute("UPDATE `user` SET `name`='%s' WHERE `room`='%s' AND `id`='%s'"
                                           % (name, room, uid))
                return result
        else:
            result = SqlHelper.execute("INSERT INTO `user`(`id`, `name`, `room`) VALUES ('%s','%s','%s')"
                                       % (uid, name, room))
            return result

    @staticmethod
    @param_sql_escape
    def removeUser(room: str, uid: str):
        result = SqlHelper.execute("DELETE FROM `user` WHERE `room`='%s' AND `id`='%s'"
                                   % (room, uid))
        return result

    @staticmethod
    @param_sql_escape
    def getOnlineList(room: str):
        result = SqlHelper.fetchAll("SELECT DISTINCT `id`, `name` FROM `user` WHERE `room` = '%s'" % room)
        userList = []
        for u in result:
            userList.append({
                "uid": Utils.md5_vsalt(u[0]),
                "name": u[1]
            })
        return userList

    @staticmethod
    @param_sql_escape
    def getChatHistory(room: str, page=1, frommsg=-1):
        sql = "SELECT `id`, `user`, `name`, `msg`, `time` FROM `chat` WHERE `room` = '%s' " % room
        if frommsg is not int:
            frommsg = int(frommsg)
        if page is not int:
            page = int(page)
        if frommsg > 0:
            sql += "AND `id` < %d " % frommsg
        sql += "ORDER BY id DESC LIMIT %d,%d " % ((page - 1) * MSG_PER_PAGE, MSG_PER_PAGE)
        result = SqlHelper.fetchAll(sql)
        msgList = []
        done = False
        for rawMsg in result:
            msgList.append({
                "id": rawMsg[0],
                "user": rawMsg[1],
                "name": rawMsg[2],
                "msg": rawMsg[3],
                "time": rawMsg[4].strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        msgList.reverse()
        if len(msgList) < MSG_PER_PAGE:
            done = True
        else:
            msgList.pop(0)
        return {
            "list": msgList,
            "done": done
        }

    @staticmethod
    @param_sql_escape
    def getFirstMember(room: str):
        result = SqlHelper.fetchOne("SELECT `user`,`name` FROM `chat` WHERE `room`='%s' ORDER BY `id` LIMIT 1" % room)
        if result is not None:
            return {
                "user": result[0],
                "name": result[1]
            }
        else:
            raise vException(-100, "找不到房主！")

    @staticmethod
    @param_sql_escape
    def sendMsg(room: str, user: str, name: str, msg: str) -> str:
        mid = SqlHelper.execute("INSERT INTO `chat`(`user`, `name`, `room`, `msg`) VALUES ('%s','%s','%s','%s')"
                          % (user, name, room, msg), "insert")
        return str(mid)

    @staticmethod
    @param_sql_escape
    def userConnect(room: str, userid: str, username: str):
        SqlHelper.execute()