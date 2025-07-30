# app/user.py

import json
import os

# USERS_FILEのパス設定を修正
USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')

# ユーザーデータの読み込み・保存
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ユーザー登録
def create_user(username: str, public_key_hex: str, initial_balance: int):
    users = load_users()

    if username in users:
        raise ValueError(f"ユーザー名 '{username}' は既に登録されています。")

    from app.wallet import pubkey_to_address
    address = pubkey_to_address(public_key_hex)

    users[username] = {
        "address": address,
        "public_key": public_key_hex,
        "balance": initial_balance
    }

    save_users(users)
    return {"username": username, **users[username]}

# ユーザー取得
def get_user(username: str):
    users = load_users()
    return users.get(username)

# 残高確認
def get_balance(username: str):
    user = get_user(username)
    if user is None:
        raise ValueError(f"ユーザー '{username}' は存在しません。")
    return user["balance"]

# 残高更新
def update_balance(username, new_balance):
    users = load_users()
    if username not in users:
        # 新しいユーザー（例：送金先が未登録）の場合は作成する
        print(f"警告: 残高更新対象のユーザー '{username}' が存在しなかったため、作成はされません。")
        # 本来はエラーだが、ここでは何もしない
        return
    users[username]["balance"] = new_balance
    save_users(users)


# テストコード
if __name__ == "__main__":
    from app.wallet import generate_keypair

    priv, pub = generate_keypair()
    print("秘密鍵:", priv)
    print("公開鍵:", pub)

    try:
        user = create_user("alice", pub, 1000)
        print("ユーザー作成:", user)
    except ValueError as e:
        print("エラー:", e)

    print("残高:", get_balance("alice"))
