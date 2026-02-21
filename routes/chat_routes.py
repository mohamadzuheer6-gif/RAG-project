from flask import Blueprint, request, jsonify
from models import db
from models.chat import Chat
from models.message import Message
from flask import request, jsonify, current_app
chat_bp = Blueprint("chat_bp", __name__)
from flask import Response
from flask_login import login_required, current_user



@chat_bp.route("/create_chat", methods=["POST"])
@login_required
def create_chat():
    new_chat = Chat(title="New Chat", user_id=current_user.id)
    db.session.add(new_chat)
    db.session.commit()
    return jsonify({"chat_id": new_chat.id})


@chat_bp.route("/get_chats", methods=["GET"])
@login_required
def get_chats():

    chats = Chat.query.filter_by(
        user_id=current_user.id
    ).order_by(Chat.id.desc()).all()

    return jsonify([
        {
            "id": chat.id,
            "title": chat.title
        }
        for chat in chats
    ])

@chat_bp.route("/get_messages/<int:chat_id>", methods=["GET"])
@login_required
def get_messages(chat_id):

    # 1️⃣ Get chat first
    chat = Chat.query.get(chat_id)

    # 2️⃣ If chat doesn't exist
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # 3️⃣ Check if chat belongs to current user
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # 4️⃣ Now safe to fetch messages
    messages = Message.query.filter_by(chat_id=chat_id) \
        .order_by(Message.timestamp).all()

    return jsonify([
        {
            "sender": msg.sender,
            "content": msg.content
        }
        for msg in messages
    ])


@chat_bp.route("/send_message", methods=["POST"])
@login_required
def send_message():

    chat_id = request.form["chat_id"]
    user_message = request.form["message"]

    # 1️⃣ Get chat first
    chat = Chat.query.get(chat_id)

    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # 2️⃣ Security check
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # 3️⃣ Save user message
    user_msg = Message(
        chat_id=chat_id,
        sender="user",
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # 4️⃣ Auto title (only first message)
    if chat.title == "New Chat":
        chat.title = user_message[:30]
        db.session.commit()

    # 5️⃣ Get RAG chain
    rag_chain = current_app.config["RAG_CHAIN"]

    bot_reply = rag_chain.invoke(
        {"input": user_message},
        config={"configurable": {"session_id": str(chat_id)}}
    )

    # 6️⃣ Save bot reply
    bot_msg = Message(
        chat_id=chat_id,
        sender="bot",
        content=bot_reply
    )
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({"reply": bot_reply})

@chat_bp.route("/delete_chat/<int:chat_id>", methods=["DELETE"])
@login_required
def delete_chat(chat_id):

    # 1️⃣ Get chat
    chat = Chat.query.get(chat_id)

    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # 2️⃣ SECURITY CHECK
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # 3️⃣ Delete chat (messages auto-delete if cascade enabled)
    db.session.delete(chat)
    db.session.commit()

    return jsonify({"message": "Chat deleted"})

@chat_bp.route("/rename_chat/<int:chat_id>", methods=["POST"])
@login_required
def rename_chat(chat_id):

    data = request.get_json()
    chat = Chat.query.get(chat_id)

    # 1️⃣ Check if chat exists
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # 2️⃣ SECURITY CHECK
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # 3️⃣ Validate title
    new_title = data.get("title", "").strip()

    if not new_title:
        return jsonify({"error": "Title cannot be empty"}), 400

    if len(new_title) > 100:
        return jsonify({"error": "Title too long"}), 400

    # 4️⃣ Update title
    chat.title = new_title
    db.session.commit()

    return jsonify({"message": "Renamed"})


from flask import Response, jsonify, current_app, stream_with_context
from flask_login import login_required, current_user

@chat_bp.route("/stream_message")
@login_required
def stream_message():

    chat_id = request.args.get("chat_id")
    user_message = request.args.get("message")

    if not chat_id:
        return jsonify({"error": "Chat ID required"}), 400

    try:
        chat_id = int(chat_id)
    except ValueError:
        return jsonify({"error": "Invalid chat ID"}), 400

    chat = Chat.query.get(chat_id)

    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    # Save user message
    user_msg = Message(
        chat_id=chat_id,
        sender="user",
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    if chat.title == "New Chat":
        chat.title = user_message[:30]
        db.session.commit()

    rag_chain = current_app.config["RAG_CHAIN"]

    @stream_with_context
    def generate():

        full_reply = ""

        for chunk in rag_chain.stream(
            {"input": user_message},
            config={"configurable": {"session_id": str(chat_id)}}
        ):
            chunk_text = str(chunk)
            full_reply += chunk_text
            yield f"data: {chunk_text}\n\n"

        # Now safe to save (context preserved)
        bot_msg = Message(
            chat_id=chat_id,
            sender="bot",
            content=full_reply
        )
        db.session.add(bot_msg)
        db.session.commit()

        yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )