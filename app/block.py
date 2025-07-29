# app/block.py

import time
from app.utils import calculate_hash, calculate_merkle_root

class Block:
    """
    ブロックの構造を定義するクラス
    """
    def __init__(self, index, transactions, previous_hash, difficulty, timestamp=None, nonce=0, merkle_root=None, stored_hash=None):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.merkle_root = merkle_root if merkle_root is not None else calculate_merkle_root(self.transactions)
        # ファイルから読み込む際は計算済みのハッシュを使い、新規作成時は再計算する
        self.hash = stored_hash if stored_hash is not None else self.calculate_block_hash()

    def calculate_block_hash(self) -> str:
        """ブロック自身のハッシュ値を計算する"""
        return calculate_hash(
            self.index,
            self.timestamp,
            self.merkle_root,
            self.previous_hash,
            self.nonce,
            self.difficulty
        )

    def mine_block(self):
        """
        PoWを実行して、条件を満たすハッシュ（とナンス）を見つける
        """
        target = "0" * self.difficulty
        while self.hash[:self.difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_block_hash()
        print(f"Block Mined! (Nonce: {self.nonce}, Hash: {self.hash})")