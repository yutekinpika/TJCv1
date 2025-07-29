from client_wallet import (
    create_user_on_server,
    send_transaction,
    get_transaction_history,
    get_balance  
)

def main():
    while True:
        print("\n=== 窓口アプリ ===")
        print("1. ユーザー作成")
        print("2. 送金")
        print("3. 取引履歴を見る")
        print("4. 残高を確認する")
        print("0. 終了")
        choice = input("選択: ")

        if choice == "1":
            name = input("ユーザー名: ")
            try:
                balance = int(input("初期残高: "))
            except ValueError:
                print("数値を入力してください")
                continue
            result = create_user_on_server(name, balance)
            print(result)

        elif choice == "2":
            from_user = input("送金元: ")
            to_user = input("送金先: ")
            try:
                amount = int(input("金額: "))
            except ValueError:
                print("数値を入力してください")
                continue
            comment = input("コメント: ")
            result = send_transaction(from_user, to_user, amount, comment)
            print(result)

        elif choice == "3":
            username = input("履歴を見たいユーザー名: ")
            history = get_transaction_history(username)
            if not history:
                print("履歴がありません。")
            elif "error" in history:
                print("エラー:", history["error"])
            else:
                for i, tx in enumerate(history, 1):
                    print(f"\n--- トランザクション {i} ---")
                    print(f"日時    : {tx.get('timestamp')}")
                    print(f"送信元  : {tx.get('from')}")
                    print(f"送信先  : {tx.get('to')}")
                    print(f"金額    : {tx.get('amount')}")
                    print(f"コメント: {tx.get('comment')}")
                    print(f"TXID    : {tx.get('txid')[:16]}...")

        elif choice == "4":
            username = input("ユーザー名を入力してください: ")
            result = get_balance(username)
            if "balance" in result:
                print(f"{username} の残高: {result['balance']} TJC")
            else:
                print("エラー:", result.get("error", "残高情報が取得できませんでした"))

        elif choice == "0":
            break

if __name__ == "__main__":
    main()
