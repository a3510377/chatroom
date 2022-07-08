import asyncio
import os
import time
import getpass

import requests
import socketio


HTTP_SERVER_URL = "http://127.0.0.1:11000"


(cls := lambda x=None: (os.system("cls" if os.name == "nt" else "clear"), x and print(x)))()


def init_print():
    cls("請透過數字選擇操作\n[1]登入\n[2]註冊\n")
    global select_type
    select_type = input("請選擇: ")


init_print()

while True:
    cls()
    if select_type not in ["1", "2"]:
        init_print()
        continue

    name = input("請輸入用戶名: ")
    password = getpass.getpass(prompt="請輸入密碼: ")
    if select_type == "1":
        cls("資料處理中請稍後...")
        if requests.get(f"{HTTP_SERVER_URL}/users", headers={
            "username": name,
            "password": password,
        }).json()["code"] == 200:
            break
        cls("登入錯誤")
        time.sleep(1)
        init_print()
        continue

    elif select_type == "2":
        cls("資料處理中請稍後...")

        status_code = requests.post(f"{HTTP_SERVER_URL}/users", json={
            "username": name,
            "password": password,
        }).json()["code"]

        if status_code == 200:
            cls("註冊成功")
            time.sleep(1)
            break
        elif status_code == 403:
            cls("用戶名已存在")
            time.sleep(1)
            continue

        print("註冊時發生錯誤請稍後再試")
        time.sleep(2)
        exit()

cls("登入成功")

sio = socketio.Client()


@sio.event
def connect():
    print("與伺服器連線完成...\n")

    for msg in requests.get(f"{HTTP_SERVER_URL}/messages").json():
        print(msg)

    asyncio.run(input_msg())


@sio.event
def connect_error():
    print("與伺服器連線時發生錯誤...")


@sio.event
def disconnect():
    print("與伺服器斷開連線...")


@sio.event
def message(msg: str):
    print(msg)


async def input_msg():
    while True:
        print('\033[1A\033[K', end="\r")
        try:
            if (msg := input().strip()):
                if requests.post(
                    f"{HTTP_SERVER_URL}/messages",
                    data=msg.encode("utf-8"),
                    headers={"username": name, "password": password}
                ).status_code != 200:
                    print("訊息發送時發生錯誤")
        except EOFError:
            sio.disconnect()
            exit()
sio.connect(HTTP_SERVER_URL, headers={"username": name, "password": password})
