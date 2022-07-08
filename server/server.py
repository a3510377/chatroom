from typing import List, Literal, Optional

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_socketio import SocketIO

from data import AuthorizationType, MessageEvent

app = Flask(__name__)
socketio = SocketIO(app)

data_dir = Path("./data")
users_file = data_dir / "users.json"
messages_file = data_dir / "messages.txt"

users: List[str] = []


@app.route("/")
def index():
    return "Hello Word!!"


@app.route("/users", methods=["POST", "GET"])
def users_():
    if request.method == "POST":
        data = request.get_json(silent=True)

        if not (username := data["username"]):
            return jsonify({
                "code": 400,
                "message": "Please enter your username",
            }), 400
        if not (password := data["password"]):
            return jsonify({
                "code": 400,
                "message": "Please enter your password",
            }), 400

        if create_user(username, password):
            return jsonify({"code": 200, "message": "ok"}), 200

        return jsonify({
            "code": 403,
            "message": "Please edit your username"
        }), 400

    headers = request.headers
    if not (username := headers.get("username", None)):
        return jsonify({
            "code": 400,
            "message": "Please enter your username",
        }), 400
    if not (password := headers.get("password", None)):
        return jsonify({
            "code": 400,
            "message": "Please enter your password",
        }), 400
    if check_user(username, password):
        return jsonify({"code": 200, "message": "ok"}), 200
    return jsonify({"code": 401, "message": "error"}), 401


@app.route("/messages", methods=["POST", "GET"])
def message_():
    if request.method == "GET":
        if (limit := int(request.args.get("limit", 10))) > 200 or limit <= 0:
            return "limit must e less than 200", 400
        with messages_file.open("r", encoding="utf8") as message:
            return jsonify([msg.strip() for msg in message.readlines()[-limit:]])  # noqa: E501

    return (data := append_message(
        request.get_data().decode("utf8"),
        AuthorizationType(
            username=request.headers.get("username"),
            password=request.headers.get("password"),
        ))
    ), 200 if data else 401


@socketio.on("connect")
def connect_():
    username = request.headers.get("username", None)
    password = request.headers.get("password", None)

    if username and password and authorization_user(username, password):
        users.append(username)
        send_user_notice(username, "join")
        return
    socketio.emit("disconnect")


@socketio.on("disconnect")
def disconnect_():
    if username := request.headers.get("username", None):
        try:
            users.remove(username)
        except ValueError:
            pass
        else:
            send_user_notice(username, "leave")


def setup_data():
    Path("./data").mkdir(parents=True, exist_ok=True)

    if not users_file.exists():
        users_file.write_text(r"{}")
    if not messages_file.exists():
        messages_file.write_text("")


def send_user_notice(username: str, type: Literal["join", "create", "leave"]):
    type_str = {"join": "加入", "leave": "離開", "create": "初次進入"}[type]
    socketio.emit("message", f"{username} {type_str}了聊天室", broadcast=True)


def check_user(username: str, password: str) -> Optional[str]:
    setup_data()
    with users_file.open("r", encoding="utf8") as user_config:
        data = json.load(user_config)
    try:
        if data[username] == password:
            return True
    except KeyError:
        ...
    return False


def create_user(username: str, password: str) -> Optional[str]:
    setup_data()
    with users_file.open("r", encoding="utf8") as user_config:
        data = json.load(user_config)
    try:
        data[username]
    except KeyError:
        data[username] = password
        with users_file.open("w", encoding="utf8") as user_config:
            json.dump(data, user_config, ensure_ascii=False)
        send_user_notice(username, "create")
        return username
    return None


def authorization_user(username: str, password: str) -> bool:
    with users_file.open("r", encoding="utf8") as user_config:
        data = json.load(user_config)

    try:
        if data[username] == password:
            return True
    except KeyError:
        pass
    return False


def append_message(
    content: str,
    user: Optional[AuthorizationType] = None
) -> Optional[MessageEvent]:
    msg = MessageEvent(
        content=content.replace("\n", " ").replace("\r", "").strip(),
        user_name=None,
        type="user",
        time_str=datetime.now().strftime("%Y/%m/%d-%H:%M:%S"),
    )
    if not user or authorization_user(user["username"], user["password"]):
        if user:
            msg.update(user_name=user["username"])
        else:
            msg.update(type="sys")
        with messages_file.open("a", encoding="utf8") as message_file:
            message = f"{msg['time_str']} | "
            message += "系統訊息" if msg["type"] == "sys" else msg["user_name"]
            message += f" : {msg['content']}"

            socketio.emit("message", message, broadcast=True)
            message_file.write(f"\n{message}")
        return msg
    return None


if __name__ == "__main__":
    socketio.run(app, debug=True, host="127.0.0.1", port=11000)
