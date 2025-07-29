from flask import Blueprint, request, jsonify
from datetime import datetime
import hashlib
from app.user import create_user, get_user, update_balance  # ここはappパッケージからimport
from app.wallet import verify_user_signature
from app.utils import load_transactions, save_transaction

bp = Blueprint("api", __name__)

@bp.route("/create_user", methods=["POST"])
def create_user_endpoint():
    data = request.get_json()

    username = data.get("username")
    public_key = data.get("public_key")
    initial_balance = data.get("initial_balance")

    if not username or not public_key or initial_balance is None:
        return jsonify({"error": "username, public_key, initial_balance は必須です"}), 400

    try:
        user = create_user(username, public_key, initial_balance)
        return jsonify({
            "message": "User created",
            "user": {
                "username": username,
                "address": user["address"],
                "balance": user["balance"]
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    from_username = data.get("from_username")
    to_username = data.get("to_username")
    amount = data.get("amount")
    signature = data.get("signature")
    comment = data.get("comment", "")

    if not from_username or not to_username or amount is None or not signature:
        return jsonify({"error": "必須パラメータが不足しています"}), 400

    sender = get_user(from_username)
    recipient = get_user(to_username)

    if not sender:
        return jsonify({"error": "送金元ユーザーが存在しません"}), 404
    if not recipient:
        return jsonify({"error": "送金先ユーザーが存在しません"}), 404
    if sender["balance"] < amount:
        return jsonify({"error": "残高不足です"}), 400

    # 署名検証（例: メッセージは "send:{from_username}->{to_username}:{amount}"）
    message = f"send:{from_username}->{to_username}:{amount}"
    if not verify_user_signature(sender["public_key"], message, signature):
        return jsonify({"error": "署名検証に失敗しました"}), 400

    # 残高更新（簡易的に）
    update_balance(from_username, sender["balance"] - amount)
    update_balance(to_username, recipient["balance"] + amount)

    # トランザクション履歴への保存
    tx = {
        "timestamp": datetime.utcnow().isoformat(),
        "from": from_username,
        "to": to_username,
        "amount": amount,
        "comment": comment,
        "signature": signature,
    }

    # 任意：txid を計算（SHA256ハッシュなど）
    tx["txid"] = hashlib.sha256(
        f"{from_username}{to_username}{amount}{signature}{tx['timestamp']}".encode()
    ).hexdigest()

    save_transaction(tx)

    return jsonify({"message": "送金成功", "comment": comment}), 200


@bp.route("/balance", methods=["GET"])
def balance():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "username パラメータが必要です"}), 400

    user = get_user(username)
    if not user:
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    return jsonify({"username": username, "balance": user["balance"]}), 200

@bp.route("/transactions", methods=["GET"])
def get_transactions():
    username = request.args.get("username")
    txs = load_transactions()
    if username:
        txs = [tx for tx in txs if tx["from"] == username or tx["to"] == username]
    return jsonify(txs)