import json
import os
import random
from base64 import b64decode, b64encode
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from zlib import crc32

from Crypto.Cipher import AES
from flask import Flask, make_response, render_template, request

app = Flask(__name__)

FLAG = os.environ.get("FLAG", "PWNX{placeholder}")


class ChecksummedCipher:
    """add checksum to be safe from tampering"""

    CRC0 = crc32(b"\0\0\0\0")

    def __init__(self, key: bytes):
        self.key = key

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(8)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        crc = crc32(plaintext)
        return nonce + cipher.encrypt(plaintext + crc.to_bytes(4, "little"))

    def decrypt(self, ciphertext: bytes) -> bytes:
        nonce = ciphertext[:8]
        ciphertext = ciphertext[8:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext)
        if not crc32(plaintext) == self.CRC0:
            raise ValueError("Invalid CRC")
        return plaintext[:-4]


class DoublyChecksummedCipher(ChecksummedCipher):
    """you can never be too safe"""

    def __init__(self, key: bytes):
        key = sha256(key).digest()
        super().__init__(key[16:])
        self.cipher = ChecksummedCipher(key[:16])

    def encrypt(self, plaintext: bytes) -> bytes:
        return self.cipher.encrypt(super().encrypt(plaintext))

    def decrypt(self, ciphertext: bytes) -> bytes:
        return super().decrypt(self.cipher.decrypt(ciphertext))


cc = DoublyChecksummedCipher(bytes.fromhex(os.environ.get("KEY")))


@dataclass
class GameState:
    won: int = 0
    tied: int = 0
    lost: int = 0
    played: int = 0
    id: str = field(default_factory=lambda: b64encode(os.urandom(16)).decode())


def parse_cookie_or_default(cookie: bytes | None) -> GameState:
    try:
        cookie = b64decode(cookie)
        state = cc.decrypt(cookie)
        return GameState(**json.loads(state))
    except Exception:
        return GameState()


@app.route("/", methods=["GET"])
def index():
    state = parse_cookie_or_default(request.cookies.get("session"))
    res = make_response(render_template("page.html", state=state))
    res.set_cookie(
        "session", b64encode(cc.encrypt(json.dumps(asdict(state)).encode())).decode()
    )
    return res


@app.route("/play/<string:user_choice>", methods=["POST"])
def play(user_choice):
    if user_choice not in ["rock", "paper", "scissors"]:
        return "Invalid choice", 400

    server_choice = random.SystemRandom().choice(["rock", "paper", "scissors"])
    state = parse_cookie_or_default(request.cookies.get("session"))
    state.played += 1

    if server_choice == user_choice:
        state.tied += 1
    elif (
        (user_choice == "rock" and server_choice == "scissors")
        or (user_choice == "paper" and server_choice == "rock")
        or (user_choice == "scissors" and server_choice == "paper")
    ):
        state.won += 1
    else:
        state.lost += 1

    json_res = {"choice": server_choice}
    if state.won == state.played == 100:
        json_res["flag"] = FLAG

    res = app.response_class(
        response=json.dumps(json_res), status=200, mimetype="application/json"
    )
    res.set_cookie(
        "session", b64encode(cc.encrypt(json.dumps(asdict(state)).encode())).decode()
    )
    return res


if __name__ == "__main__":
    app.run(port=1337, debug=True)
