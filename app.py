from flask import Flask, render_template
from dotenv import load_dotenv
from config import Config
from models import db
from routes.chat_routes import chat_bp
from flask_login import LoginManager
from routes.auth_routes import auth_bp
import os
from flask_login import login_required, current_user
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    
    app.register_blueprint(auth_bp)
    
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    # -------------------------
    # Initialize RAG System
    # -------------------------
    from src.helpers import (
        download_embeddings,
        load_existing_vector_store,
        create_retriever
    )
    from src.prompt import build_rag_chain

    INDEX_NAME = "medibot"

    print("🔹 Loading embeddings...")
    embeddings = download_embeddings()

    print("🔹 Loading vector store...")
    vector_store = load_existing_vector_store(embeddings, INDEX_NAME)

    print("🔹 Creating retriever...")
    retriever = create_retriever(vector_store)

    print("🔹 Building RAG chain...")
    rag_chain = build_rag_chain(retriever)

    app.config["RAG_CHAIN"] = rag_chain

    print("✅ Chatbot Ready!")

    app.register_blueprint(chat_bp)

    @app.route("/")
    @login_required
    def home():
        return render_template("chat.html", user=current_user)

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()

    app.run(debug=True)
    
app = create_app()
