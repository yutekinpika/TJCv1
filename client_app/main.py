# main.py

import json
# get_all_users をインポートリストに追加
from client_wallet import (
    create_user_on_server,
    send_transaction,
    get_transaction_history,
    get_balance,
    get_all_users
)

def main():
    while True:
        print("\n=== 窓口アプリ ===")
        print("1. ユーザー作成")
        print("2. 送金")
        print("3. 取引履歴を見る")
        print("4. 残高を確認する")
        # 新しいメニュー項目を追加
        print("5. ユーザー一覧を見る")
        print("0. 終了")
        choice = input("選択: ")

        if choice == "1":
            # ... (変更なし)
            name = input("ユーザー名: ")
            try:
                balance_str = input("初期残高 (デフォルト: 1000): ")
                balance = int(balance_str) if balance_str else 1000
            except ValueError:
                print("エラー: 残高は数値を入力してください。")
                continue
            print(f"ユーザー'{name}'を作成しています...")
            result = create_user_on_server(name, balance)
            print("--- サーバーからの応答 ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("--------------------------")

        elif choice == "2":
            # ... (変更なし)
            from_user = input("送金元: ")
            to_user = input("送金先: ")
            try:
                amount = int(input("金額: "))
                if amount <= 0:
                    print("エラー: 金額は正の整数である必要があります。")
                    continue
            except ValueError:
                print("エラー: 金額は数値を入力してください。")
                continue
            comment = input("コメント: ")
            result = send_transaction(from_user, to_user, amount, comment)
            print("--- サーバーからの応答 ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("--------------------------")

        elif choice == "3":
            # ... (変更なし)
            username = input("履歴を見たいユーザー名: ")
            history = get_transaction_history(username)
            if "error" in history:
                print("エラー:", history["error"])
            elif not history:
                print(f"{username} の取引履歴はありません。")
            else:
                for i, tx in enumerate(history, 1):
                    print(f"\n--- トランザクション {i} ---")
                    print(f"  日時    : {tx.get('timestamp')}")
                    print(f"  送信元  : {tx.get('from')}")
                    print(f"  送信先  : {tx.get('to')}")
                    print(f"  金額    : {tx.get('amount')}")
                    print(f"  コメント: {tx.get('comment')}")
                    if tx.get('txid'):
                      print(f"  TXID    : {tx.get('txid')[:16]}...")

        elif choice == "4":
            # ... (変更なし)
            username = input("ユーザー名を入力してください: ")
            result = get_balance(username)
            if "balance" in result:
                print(f"残高: {result['balance']} TJC")
            else:
                print("エラー:", result.get("error", "残高情報が取得できませんでした"))

        # ▼▼▼ この下のブロックを新しく追加 ▼▼▼
        elif choice == "5":
            print("\nユーザー一覧を取得しています...")
            users = get_all_users()
            
            if isinstance(users, dict) and "error" in users:
                print("エラー: ユーザー一覧の取得に失敗しました。")
                print(f"詳細: {users.get('details', 'N/A')}")
            elif not users:
                print("現在、登録されているユーザーはいません。")
            else:
                # 残高の多い順に並び替え
                sorted_users = sorted(users, key=lambda u: u.get('balance', 0), reverse=True)
                
                print("\n" + "--- ユーザー一覧 (残高順) ---".center(52))
                # 表形式で表示
                print(f"{'No.':>3} | {'ユーザー名':<15} | {'残高':>12} | {'アドレス'}")
                print("-" * 54)
                for i, user in enumerate(sorted_users, 1):
                    username = user.get('username', 'N/A')
                    balance = user.get('balance', 0)
                    address = user.get('address', 'N/A')
                    print(f"{i:>3} | {username:<15} | {balance:>10} TJC | {address[:20]}...")
                print("-" * 54)
        
        elif choice == "0":
            print("アプリを終了します。")
            break
        
        else:
            print("無効な選択です。もう一度入力してください。")

if __name__ == "__main__":
    main()