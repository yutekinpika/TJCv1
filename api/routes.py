# api/routes.py

from flask import Blueprint, request, jsonify, g
from datetime import datetime
import hashlib
import json
import time

# 必要なモジュールを正しくインポートする
from app.user import create_user, get_user, load_users
from app.wallet import verify_user_signature
from app.blockchain import Blockchain
from app.block import Block

bp = Blueprint("api", __name__)

def get_blockchain():
    """リクエスト内で使いまわせるように、gオブジェクトにBlockchainインスタンスを格納"""
    if 'blockchain' not in g:
        g.blockchain = Blockchain()
    return g.blockchain

@bp.route("/create_user", methods=["POST"])
def create_user_endpoint():
    """ユーザー名、公開鍵、そして初期残高を指定してユーザーを作成する。"""
    data = request.get_json()
    username = data.get("username")
    public_key = data.get("public_key")
    initial_balance = data.get("initial_balance")

    if not username or not public_key or initial_balance is None:
        return jsonify({"error": "username, public_key, initial_balance は必須です"}), 400
    
    if not isinstance(initial_balance, int) or initial_balance < 0:
        return jsonify({"error": "initial_balanceは0以上の整数である必要があります"}), 400

    try:
        user = create_user(username, public_key, initial_balance)
        return jsonify({
            "message": "User created successfully",
            "user": user
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/send", methods=["POST"])
def send_and_mine():
    """送金者がPoWを実行し、トランザクションをブロックとして直接チェーンに追加する。"""
    data = request.get_json()
    from_username = data.get("from_username")
    to_username = data.get("to_username")
    amount = data.get("amount")
    signature = data.get("signature")
    nonce = data.get("nonce")
    timestamp = data.get("timestamp")
    comment = data.get("comment", "")

    if not all([from_username, to_username, amount, signature, nonce is not None, timestamp is not None]):
        return jsonify({"error": "必須パラメータ(from_username, to_username, amount, signature, nonce, timestamp)が不足しています"}), 400
    
    sender = get_user(from_username)
    if not sender: return jsonify({"error": "送金元ユーザーが存在しません"}), 404
    if not get_user(to_username): return jsonify({"error": "送金先ユーザーが存在しません"}), 404
    if sender["balance"] < amount: return jsonify({"error": "残高不足です"}), 400

    message = f"send:{from_username}->{to_username}:{amount}"
    if not verify_user_signature(sender["public_key"], message, signature):
        return jsonify({"error": "署名検証に失敗しました。"}), 400

    blockchain = get_blockchain()
    latest_block = blockchain.get_latest_block()

    # トランザクションIDを計算
    tx_payload_for_id = {"from": from_username, "to": to_username, "amount": amount, "signature": signature, "comment": comment}
    txid = hashlib.sha256(json.dumps(tx_payload_for_id, sort_keys=True).encode()).hexdigest()
    tx = {**tx_payload_for_id, "txid": txid}

    # 新しいブロックをクライアントからの情報で構築
    new_block = Block(
        index=latest_block.index + 1,
        transactions=[tx],
        previous_hash=latest_block.hash,
        difficulty=blockchain.difficulty,
        timestamp=timestamp,
        nonce=nonce
    )

    # ブロックをチェーンに追加（この中でPoW検証が行われる）
    if blockchain.add_block(new_block):
        return jsonify({
            "message": "送金成功！ブロックがチェーンに追加されました。",
            "block_hash": new_block.hash
        }), 201
    else:
        return jsonify({"error": "ブロックの検証に失敗しました。PoWが無効か、チェーンが更新された可能性があります。"}), 400

@bp.route("/info", methods=["GET"])
def get_info():
    """クライアントがPoWを計算するのに必要な情報を返す"""
    blockchain = get_blockchain()
    latest_block = blockchain.get_latest_block()
    return jsonify({
        "difficulty": blockchain.difficulty,
        "latest_block_hash": latest_block.hash,
        "latest_block_index": latest_block.index
    })

@bp.route("/balance", methods=["GET"])
def balance():
    username = request.args.get("username")
    if not username: return jsonify({"error": "username パラメータが必要です"}), 400
    user = get_user(username)
    if not user: return jsonify({"error": "ユーザーが見つかりません"}), 404
    return jsonify({"username": username, "balance": user["balance"]}), 200

@bp.route("/chain", methods=["GET"])
def get_full_chain():
    blockchain = get_blockchain()
    chain_data = [block.__dict__ for block in blockchain.chain]
    return jsonify({"chain": chain_data, "length": len(chain_data)}), 200

@bp.route("/transactions", methods=["GET"])
def get_all_transactions():
    """ブロックチェーン全体をスキャンしてトランザクション履歴を返す"""
    blockchain = get_blockchain()
    username = request.args.get("username")
    all_txs = []
    # ジェネシスブロック（index=0）以降の全ブロックを走査
    for block in blockchain.chain[1:]:
        all_txs.extend(block.transactions)
    
    if username:
        user_txs = [tx for tx in all_txs if tx.get("from") == username or tx.get("to") == username]
        return jsonify(user_txs)
        
    return jsonify(all_txs)

@bp.route("/users", methods=["GET"])
def get_user_list():
    """
    登録されている全ユーザーのリスト（ユーザー名、残高、アドレス）を返す。
    """
    try:
        all_users_data = load_users()
        
        # クライアントに返す情報を整形します。
        # (公開鍵のような機密情報は含めません)
        user_list = [
            {"username": username, "balance": data.get("balance", 0), "address": data.get("address", "N/A")}
            for username, data in all_users_data.items()
        ]
        
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"error": "ユーザーリストの取得に失敗しました。", "details": str(e)}), 500