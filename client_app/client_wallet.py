import os
import json
from ecdsa import SigningKey, SECP256k1
import hashlib
import requests

# 1. client_wallet.py: 鍵生成・署名
def generate_user_keys(username):
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    private_key = sk.to_string().hex()
    public_key = "04" + vk.to_string().hex()  # uncompressed
    
    address = hashlib.sha1(bytes.fromhex(public_key)).hexdigest()

    # 保存（client_app/users/username.json）
    user_dir = os.path.join(os.path.dirname(__file__), "users")
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, f"{username}.json"), "w") as f:
        json.dump({
            "private_key": private_key,
            "public_key": public_key,
            "address": address
        }, f)

    return public_key, private_key, address

# 2. ユーザ作成APIを叩く関数
def create_user_on_server(username, initial_balance=1000):
    public_key, private_key, address = generate_user_keys(username)
    response = requests.post("http://127.0.0.1:5000/create_user", json={
        "username": username,
        "public_key": public_key,
        "initial_balance": initial_balance
    })
    return response.json()

# 3. 送金署名＆送金API送信
def load_user_keys(username):
    path = os.path.join(os.path.dirname(__file__), "users", f"{username}.json")
    with open(path, "r") as f:
        data = json.load(f)
    return data["private_key"], data["public_key"]

def sign_message(private_key_hex, message):
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    return sk.sign(message.encode()).hex()

def send_transaction(from_user, to_user, amount, comment=""):
    private_key, public_key = load_user_keys(from_user)
    message = f"send:{from_user}->{to_user}:{amount}"
    signature = sign_message(private_key, message)

    response = requests.post("http://127.0.0.1:5000/send", json={
        "from_username": from_user,
        "to_username": to_user,
        "amount": amount,
        "signature": signature,
        "comment": comment
    })

    return response.json()

# 4.トランザクション履歴取得
def get_transaction_history(username):
    try:
        response = requests.get("http://127.0.0.1:5000/transactions", params={"username": username})
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# 5.残高の確認
def get_balance(username):
    try:
        response = requests.get("http://127.0.0.1:5000/balance", params={"username": username})
        return response.json()
    except Exception as e:
        return {"error": str(e)}
