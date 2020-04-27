import MySQLdb
import Exceptions

SQLConfig = {
    "host": "localhost",
    "user": "chatroom",
    "pwd": "chatroom123",
    "dbName": "chatroom",
}


def connect():
    db = MySQLdb.connect(SQLConfig["host"], SQLConfig["user"], SQLConfig["pwd"], SQLConfig["dbName"], charset="utf8")
    dbCursor = db.cursor()
    dbCursor.execute("SET NAMES utf8mb4")
    dbCursor.execute("SET CHARACTER SET utf8mb4")
    return dbCursor


def fetchAll(sql):
    return execute(sql, returnMode="data")


def fetchOne(sql):
    return execute(sql, returnMode="one")


def insert(sql):
    return execute(sql, returnMode="insert")


def execute(sql, returnMode="bool"):
    if returnMode == "bool":
        try:
            cursor = connect() # type: MySQLdb.cursors.Cursor
            cursor.execute(sql)
            cursor.close()
            return True
        except Exceptions.vException:
            return False
    elif returnMode == "data":
        try:
            cursor = connect()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exceptions.vException:
            return None
    elif returnMode == "one":
        try:
            cursor = connect()
            cursor.execute(sql)
            data = cursor.fetchone()
            cursor.close()
            return data
        except Exceptions.vException:
            return None
    elif returnMode == "insert":
        try:
            cursor = connect() # type: MySQLdb.cursors.Cursor
            cursor.execute(sql)
            id = cursor.lastrowid
            cursor.close()
            return id
        except Exceptions.vException:
            return None

