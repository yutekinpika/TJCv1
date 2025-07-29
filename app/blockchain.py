# app/blockchain.py

import os
import json
import time
from app.block import Block
from app.user import update_balance, get_user

# --- 定数 ---
BLOCKCHAIN_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'blockchain.json')
DIFFICULTY = 4      # PoWの難易度 (先頭に0が何個並ぶか)

class Blockchain:
    def __init__(self):
        self.chain = self._load_chain()
        self.difficulty = DIFFICULTY
        if not self.chain:
            self._create_genesis_block()

    def _create_genesis_block(self):
        """最初のブロック（ジェネシスブロック）を生成"""
        # ジェネシスブロックはPoW不要とするか、ここで計算する
        genesis_block = Block(index=0, transactions=[], previous_hash="0", difficulty=self.difficulty, nonce=0)
        # ジェネシスブロックのハッシュを確定させる
        genesis_block.hash = genesis_block.calculate_block_hash()
        self.chain.append(genesis_block)
        self._save_chain()

    def get_latest_block(self) -> Block:
        """チェーンの最新ブロックを返す"""
        return self.chain[-1]

    def add_block(self, new_block: Block) -> bool:
        """
        新しいブロックを検証し、チェーンに追加する
        """
        latest_block = self.get_latest_block()

        # 1. ブロックの基本情報を検証
        if new_block.previous_hash != latest_block.hash:
            print("エラー: 前のブロックのハッシュが一致しません。")
            return False
        if new_block.index != latest_block.index + 1:
            print("エラー: ブロックのインデックスが無効です。")
            return False
        
        # 2. PoW（ハッシュの正当性）を検証
        target = "0" * self.difficulty
        if new_block.hash[:self.difficulty] != target:
            print(f"エラー: PoWが無効です。ハッシュが '{target}' で始まっていません。")
            return False

        # 3. ブロック自身のハッシュ値が、その内容から再計算したものと一致するか検証
        if new_block.hash != new_block.calculate_block_hash():
            print("エラー: ブロックのハッシュ値が破損しています。")
            return False

        # 4. 検証が成功したらチェーンに追加
        self.chain.append(new_block)
        self._process_transactions(new_block.transactions)
        self._save_chain()
        return True

    def _process_transactions(self, transactions: list):
        """ブロック内のトランザクションを処理して残高を更新する"""
        for tx in transactions:
            # マイニング報酬（COINBASE）は無いため、送金元・先の更新のみ
            if tx.get('from') and tx.get('to'):
                sender = get_user(tx['from'])
                recipient = get_user(tx['to'])

                # エラーチェックはAPI側で済んでいる前提だが、念のため
                if sender and recipient:
                    update_balance(sender['username'], sender['balance'] - tx['amount'])
                    update_balance(recipient['username'], recipient['balance'] + tx['amount'])

    # --- データ永続化メソッド ---
    def _save_chain(self):
        chain_data = [block.__dict__ for block in self.chain]
        self._save_data(BLOCKCHAIN_FILE, chain_data)

    def _load_chain(self) -> list[Block]:
        chain_data = self._load_data(BLOCKCHAIN_FILE, [])
        return [Block(
            index=b['index'],
            transactions=b['transactions'],
            previous_hash=b['previous_hash'],
            difficulty=b['difficulty'],
            timestamp=b['timestamp'],
            nonce=b['nonce'],
            merkle_root=b['merkle_root'],
            stored_hash=b['hash']
        ) for b in chain_data]

    def _save_data(self, filepath, data):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self, filepath, default):
        if not os.path.exists(filepath): return default
        with open(filepath, 'r') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return default