# run.py (プロジェクトのルートディレクトリに配置)

from api import create_app

# アプリケーションファクトリからFlaskアプリを生成
app = create_app()

if __name__ == '__main__':
    # データをクリアしたい場合は以下のコメントを外す（デバッグ用）
    # import os
    # files_to_clear = ['data/blockchain.json', 'data/users.json']
    # for f in files_to_clear:
    #     if os.path.exists(f):
    #         os.remove(f)

    app.run(host='0.0.0.0', port=5000, debug=True)