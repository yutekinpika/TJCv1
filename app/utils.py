# app/utils.py

import hashlib
import json

def calculate_hash(*args) -> str:
    """
    複数の引数を文字列として連結し、そのSHA256ハッシュを計算する。
    Blockクラスとクライアントアプリの両方で使われる共通関数。
    """
    # 全ての引数を文字列に変換して連結する
    string_data = "".join(map(str, args))
    return hashlib.sha256(string_data.encode()).hexdigest()

def calculate_merkle_root(transactions: list[dict]) -> str:
    """
    トランザクションリストからマークルルートを計算する。
    トランザクション辞書内の 'txid' をハッシュとして利用する。
    """
    if not transactions:
        return "0" * 64

    # 各トランザクションのtxidをリストアップ
    tx_hashes = [tx['txid'] for tx in transactions]

    # トランザクション数が奇数の場合、最後の要素を複製して偶数にする
    if len(tx_hashes) % 2 != 0:
        tx_hashes.append(tx_hashes[-1])

    # 2つのハッシュを結合して新しいハッシュを計算するプロセスを、ルートが1つになるまで繰り返す
    while len(tx_hashes) > 1:
        new_hashes = []
        for i in range(0, len(tx_hashes), 2):
            combined_hash = tx_hashes[i] + tx_hashes[i+1]
            new_hashes.append(hashlib.sha256(combined_hash.encode()).hexdigest())
        tx_hashes = new_hashes
        # レベルが上がった後も、要素数が奇数なら最後の要素を複製
        if len(tx_hashes) % 2 != 0 and len(tx_hashes) > 1:
            tx_hashes.append(tx_hashes[-1])
            
    return tx_hashes[0]