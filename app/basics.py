from flask_restplus import fields, abort
from flask_restplus.model import Model
from flask import request
from functools import wraps
from requests import get, Response
from objects import api

ErrorSchema: Model = api.model("Error", {
    "message": fields.String(readOnly=True)
})

SuccessSchema: Model = api.model("Success", {
    "ok": fields.Boolean(readOnly=True)
})


def require_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'Token' in request.headers:
            token: str = request.headers["Token"]

            session: Response = get(api.app.config["AUTH_API"] + "auth", headers={
                "Token": token
            })

            if session.status_code != 200:
                try:
                    msg: str = session.json()["message"]
                    abort(400, msg)
                except Exception:
                    abort(400, "invalid token")

            kwargs["session"] = session.json()

            return f(*args, **kwargs)
        else:
            abort(400, "token required")

    return wrapper
