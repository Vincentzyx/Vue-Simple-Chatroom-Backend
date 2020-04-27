import hashlib
import datetime
import MySQLdb
import random
import string
import json


def md5(str: str) -> str:
    return hashlib.md5(str.encode()).hexdigest()


def md5_salt(str: str, salt: str) -> str:
    return md5(str + salt)


def md5_vsalt(str: str) -> str:
    return md5_salt(str, "vvvsalt123")


def sqlEscapeStr(str: str) -> str:
    return MySQLdb.escape_string(str).decode()


def gen_str() -> str:
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    return md5(ran_str)


def time_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")