from flask import Flask
from flask_socketio import SocketIO, send, emit
from functools import wraps
from Exceptions import vException
import json
from AppFunctions import AppFunctions
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


@app.route('/')
@json_response
def index():
    print("test")
    raise vException(-10001, "Wrong usage.")


@socketio.on("message")
def handle_message(message):
    sessio


with app.test_request_context():
    print("Testing...")


if __name__ == '__main__':
    socketio.run(app)