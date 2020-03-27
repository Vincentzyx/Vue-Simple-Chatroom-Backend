from flask import Flask
from functools import wraps
from Exceptions import vException

app = Flask(__name__)
app.secret_key = ' A\xcd!x\xa6a\xffS\xcc\xc9\xdf?\x15\xd7\xbb\xdf\x0b\x9f\x1cy\xdcb\x8b'


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
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()