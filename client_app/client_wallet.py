# client_wallet.py

import os
import json
import hashlib
import time
import requests
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

# --- 定数 ---
API_BASE_URL = "http://127.0.0.1:5000/api"

# --- サーバー側のロジックと合わせるためのヘルパー関数 ---
def calculate_hash(*args) -> str:
    """
    複数の引数を文字列として連結し、そのSHA256ハッシュを計算する。
    サーバーの block.py と同じロジック。
    """
    string_data = "".join(map(str, args))
    return hashlib.sha256(string_data.encode()).hexdigest()

def calculate_merkle_root(transactions: list[dict]) -> str:
    """
    トランザクションリストからマークルルートを計算する。
    サーバーの utils.py と同じロジック。
    """
    if not transactions:
        return "0" * 64
    tx_hashes = [tx['txid'] for tx in transactions]
    if len(tx_hashes) % 2 != 0: tx_hashes.append(tx_hashes[-1])
    while len(tx_hashes) > 1:
        new_hashes = []
        for i in range(0, len(tx_hashes), 2):
            combined_hash = tx_hashes[i] + tx_hashes[i+1]
            new_hashes.append(hashlib.sha256(combined_hash.encode()).hexdigest())
        tx_hashes = new_hashes
        if len(tx_hashes) % 2 != 0 and len(tx_hashes) > 1:
            tx_hashes.append(tx_hashes[-1])
    return tx_hashes[0]

def pubkey_to_address(public_key_hex: str) -> str:
    """公開鍵からアドレスを生成。サーバーの wallet.py と同じロジック。"""
    sha = hashlib.sha256(bytes.fromhex(public_key_hex)).digest()
    ripemd = hashlib.new('ripemd160')
    ripemd.update(sha)
    return ripemd.hexdigest()

# --- 鍵管理と署名 ---
def generate_user_keys(username: str) -> str:
    """鍵ペアを生成し、ファイルに保存。公開鍵を返す。"""
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    private_key = sk.to_string().hex()
    # サーバーの仕様に合わせ、非圧縮形式の公開鍵を使用
    public_key = vk.to_string("uncompressed").hex()
    
    address = pubkey_to_address(public_key)

    user_dir = os.path.join(os.path.dirname(__file__), "users")
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, f"{username}.json"), "w") as f:
        json.dump({
            "username": username,
            "private_key": private_key,
            "public_key": public_key,
            "address": address
        }, f, indent=2)

    return public_key

def load_user_keys(username: str) -> tuple[str, str]:
    """ファイルから秘密鍵と公開鍵を読み込む。"""
    path = os.path.join(os.path.dirname(__file__), "users", f"{username}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"ユーザー '{username}' のキーファイルが見つかりません。")
    with open(path, "r") as f:
        data = json.load(f)
    return data["private_key"], data["public_key"]

def sign_message(private_key_hex: str, message: str) -> str:
    """メッセージに署名する。"""
    sk = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    return sk.sign(message.encode('utf-8')).hex()

# --- PoW計算（マイニング） ---
def solve_pow(difficulty: int, index: int, previous_hash: str, transactions: list) -> tuple[int, float]:
    """条件を満たす nonce と timestamp を見つけるまで計算する。"""
    print(f"Difficulty: {difficulty}")
    target = '0' * difficulty
    nonce = 0
    merkle_root = calculate_merkle_root(transactions)

    while True:
        timestamp = time.time()
        # サーバー側(Block.calculate_block_hash)と引数の順序を完全に一致させる
        block_hash = calculate_hash(index, timestamp, merkle_root, previous_hash, nonce, difficulty)
        
        if nonce % 200000 == 0: # 計算中の進捗を表示
            print(f"  ...計算中 (Nonce: {nonce}, Hash: {block_hash[:10]}...)")

        if block_hash.startswith(target):
            print(f"発見！ Hash: {block_hash}")
            return nonce, timestamp
        
        nonce += 1

# --- API連携 ---
def create_user_on_server(username: str, initial_balance: int = 1000):
    try:
        public_key = generate_user_keys(username)
        response = requests.post(f"{API_BASE_URL}/create_user", json={
            "username": username, "public_key": public_key, "initial_balance": initial_balance
        })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # エラーレスポンスがJSON形式の場合、その内容を表示する
        error_details = str(e)
        if e.response is not None:
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = e.response.text
        return {"error": f"{e}", "details": error_details}

def send_transaction(from_user: str, to_user: str, amount: int, comment: str = ""):
    try:
        # 1. PoW計算に必要な情報をサーバーから取得
        print("サーバーからPoW情報を取得しています...")
        info_res = requests.get(f"{API_BASE_URL}/info")
        info_res.raise_for_status()
        info = info_res.json()

        # 2. 署名を作成
        private_key, _ = load_user_keys(from_user)
        message = f"send:{from_user}->{to_user}:{amount}"
        signature = sign_message(private_key, message)
        
        # 3. トランザクションを作成
        tx_payload_for_id = {"from": from_user, "to": to_user, "amount": amount, "signature": signature, "comment": comment}
        txid = hashlib.sha256(json.dumps(tx_payload_for_id, sort_keys=True).encode()).hexdigest()
        transaction = {**tx_payload_for_id, "txid": txid}

        # 4. PoW計算（マイニング）を実行
        print("送金承認のため、マイニングを開始します...")
        nonce, timestamp = solve_pow(
            difficulty=info['difficulty'],
            index=info['latest_block_index'] + 1,
            previous_hash=info['latest_block_hash'],
            transactions=[transaction]
        )
        print(f"マイニング成功！ (Nonce: {nonce})")

        # 5. 計算結果を含めてサーバーに送信
        response = requests.post(f"{API_BASE_URL}/send", json={
            "from_username": from_user, "to_username": to_user, "amount": amount,
            "signature": signature, "comment": comment,
            "nonce": nonce, "timestamp": timestamp
        })
        response.raise_for_status()
        return response.json()
    
    except FileNotFoundError as e:
        return {"error": str(e)}
    except requests.exceptions.RequestException as e:
        error_details = str(e)
        if e.response is not None:
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = e.response.text
        return {"error": f"{e}", "details": error_details}

def get_transaction_history(username: str):
    try:
        response = requests.get(f"{API_BASE_URL}/transactions", params={"username": username})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e.response.json()) if e.response else str(e)}

def get_balance(username: str):
    try:
        response = requests.get(f"{API_BASE_URL}/balance", params={"username": username})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e.response.json()) if e.response else str(e)}
    

def get_all_users():
    """サーバーから全ユーザーのリストを取得する"""
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        response.raise_for_status()  # 200番台以外のステータスコードなら例外を発生
        return response.json()
    except requests.exceptions.RequestException as e:
        error_details = str(e)
        if e.response is not None:
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = e.response.text
        return {"error": f"{e}", "details": error_details}