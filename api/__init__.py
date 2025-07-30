# api/__init__.py

from flask import Flask

def create_app():
    """Flaskアプリケーションインスタンスを作成して返すファクトリ関数"""
    app = Flask(__name__)

    # --- ここからが重要 ---
    # routes.py で定義したBlueprintをインポート
    from .routes import bp as api_blueprint

    # Blueprintをアプリケーションに登録し、URLの接頭辞（プレフィックス）を指定
    app.register_blueprint(api_blueprint, url_prefix='/api')
    # --- ここまでが重要 ---

    # ルートパスへの簡単な応答を追加
    @app.route("/")
    def index():
        return "<h1>Blockchain API Server is running!</h1>"

    return app