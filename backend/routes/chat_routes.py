"""
AgriVersion - Multimodal AI Chatbot (RiceCare AI) API Routes
Includes:
- Standard synchronous chat (/api/chat/send)
- Real-time Server-Sent Events (SSE) streaming (/api/chat/stream)
- Conversation history CRUD & export (/api/chat/conversations)
- AI model status & available providers (/api/chat/models)
"""

import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.database.db import db
from backend.database.models import Conversation, Message, MessageImage
from backend.services.multimodal_chat_service import generate_multimodal_response, stream_multimodal_response
from backend.utils.auth_helpers import get_current_user, login_required
from backend.utils.file_validators import save_uploaded_image
from backend.config import Config

chat_bp = Blueprint("chat_bp", __name__, url_prefix="/api/chat")


@chat_bp.route("/models", methods=["GET"])
@login_required
def get_available_models():
    """Returns available AI models and their capabilities."""
    has_gemini = bool(Config.GEMINI_API_KEY)
    has_openai = bool(Config.OPENAI_API_KEY)
    has_groq = bool(Config.GROQ_API_KEY)

    models = [
        {
            "id": "auto",
            "name": "🌾 RiceCare AI (Auto / High Precision)",
            "provider": "Hybrid (Best Available + Deep CNN Vision)",
            "vision": True,
            "recommended": True,
            "description": "Automatically chooses the best available engine with multi-intent decomposition and deep PyTorch CNN diagnosis."
        },
        {
            "id": "gemini-2.0-flash",
            "name": "⚡ Google Gemini 2.0 Flash",
            "provider": "Google DeepMind",
            "vision": True,
            "configured": has_gemini,
            "description": "Multimodal visual reasoning with low latency and high accuracy."
        },
        {
            "id": "gpt-4o-mini",
            "name": "🧠 OpenAI GPT-4o Mini",
            "provider": "OpenAI",
            "vision": True,
            "configured": has_openai,
            "description": "State-of-the-art conversational reasoning with multimodal support."
        },
        {
            "id": "groq-gpt-oss",
            "name": "🚀 Groq GPT-OSS (120B)",
            "provider": "Groq",
            "vision": False,
            "configured": has_groq,
            "description": "Ultra-fast text generation with high accuracy."
        },
        {
            "id": "builtin-rag",
            "name": "🔬 Built-in Agronomy Expert Engine",
            "provider": "AgriVersion Offline RAG",
            "vision": True,
            "configured": True,
            "description": "100% offline-ready domain knowledge base for all 20 rice diseases, dosages, and fertilizers."
        }
    ]

    return jsonify({
        "success": True,
        "models": models,
        "server_keys": {
            "gemini": has_gemini,
            "openai": has_openai,
            "groq": has_groq
        }
    })


@chat_bp.route("/conversations", methods=["GET"])
@login_required
def get_conversations():
    user = get_current_user()
    search = request.args.get("q", "").strip()
    
    query = Conversation.query.filter_by(user_id=user.id)
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search}%"))

    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return jsonify({
        "success": True,
        "conversations": [c.to_dict() for c in conversations]
    })


@chat_bp.route("/conversations", methods=["POST"])
@login_required
def create_conversation():
    user = get_current_user()
    data = request.get_json() or {}
    title = data.get("title", "New Rice Crop Analysis").strip()

    conv = Conversation(user_id=user.id, title=title)
    db.session.add(conv)
    db.session.commit()

    return jsonify({"success": True, "conversation": conv.to_dict()}), 201


@chat_bp.route("/conversations/<int:conv_id>", methods=["GET"])
@login_required
def get_conversation_detail(conv_id):
    user = get_current_user()
    conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
    if not conv:
        return jsonify({"success": False, "message": "Conversation not found."}), 404

    messages = [m.to_dict() for m in conv.messages]
    return jsonify({
        "success": True,
        "conversation": conv.to_dict(),
        "messages": messages
    })


@chat_bp.route("/conversations/<int:conv_id>", methods=["DELETE"])
@login_required
def delete_conversation(conv_id):
    user = get_current_user()
    conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
    if not conv:
        return jsonify({"success": False, "message": "Conversation not found."}), 404

    db.session.delete(conv)
    db.session.commit()
    return jsonify({"success": True, "message": "Conversation deleted."})


@chat_bp.route("/conversations/<int:conv_id>/rename", methods=["PUT"])
@login_required
def rename_conversation(conv_id):
    user = get_current_user()
    conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
    if not conv:
        return jsonify({"success": False, "message": "Conversation not found."}), 404

    data = request.get_json() or {}
    new_title = data.get("title", "").strip()
    if new_title:
        conv.title = new_title
        db.session.commit()

    return jsonify({"success": True, "conversation": conv.to_dict()})


@chat_bp.route("/conversations/<int:conv_id>/export", methods=["GET"])
@login_required
def export_conversation(conv_id):
    """Exports conversation transcript as Markdown / Text."""
    user = get_current_user()
    conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
    if not conv:
        return jsonify({"success": False, "message": "Conversation not found."}), 404

    lines = [
        f"# AgriVersion RiceCare AI Consultation Log",
        f"**Conversation:** {conv.title}",
        f"**Date:** {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Farmer / User:** {user.full_name} ({user.email})",
        "\n---\n"
    ]

    for m in conv.messages:
        role = "🧑 Farmer" if m.sender == "user" else "🌾 RiceCare AI Assistant"
        timestamp = m.created_at.strftime("%H:%M:%S")
        lines.append(f"### {role} ({timestamp}):")
        lines.append(m.text_content)
        lines.append("\n")

    export_text = "\n".join(lines)
    return jsonify({
        "success": True,
        "title": conv.title,
        "content": export_text
    })


@chat_bp.route("/upload-image", methods=["POST"])
@login_required
def upload_chat_image():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image uploaded."}), 400

    file_storage = request.files["image"]
    saved, filename, err = save_uploaded_image(file_storage)
    if not saved:
        return jsonify({"success": False, "message": err}), 400

    return jsonify({
        "success": True,
        "filename": filename,
        "image_url": f"/uploads/{filename}",
        "original_name": file_storage.filename
    })


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    """Standard synchronous message processing endpoint."""
    user = get_current_user()
    data = request.get_json() or {}
    conv_id = data.get("conversation_id")
    user_text = data.get("message", "").strip()
    image_filenames = data.get("image_filenames", [])
    language = data.get("language", user.preferred_lang or "en")
    model_preference = data.get("model_preference", "auto")
    custom_api_key = data.get("custom_api_key", "").strip() or None

    if not user_text and not image_filenames:
        return jsonify({"success": False, "message": "Message or image attachment required."}), 400

    # Retrieve or create Conversation
    if conv_id:
        conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
        if not conv:
            conv = Conversation(user_id=user.id, title="Rice Leaf Consultation")
            db.session.add(conv)
            db.session.commit()
    else:
        title_snippet = user_text[:35] if user_text else "Leaf Image Analysis"
        conv = Conversation(user_id=user.id, title=f"🌾 {title_snippet}")
        db.session.add(conv)
        db.session.commit()

    # Save User Message
    user_msg = Message(
        conversation_id=conv.id,
        sender="user",
        text_content=user_text or "Please analyze the attached rice leaf image."
    )
    db.session.add(user_msg)
    db.session.commit()

    # Attach images to user message
    for img_fn in image_filenames:
        msg_img = MessageImage(
            message_id=user_msg.id,
            image_filename=img_fn,
            original_filename=img_fn
        )
        db.session.add(msg_img)
    db.session.commit()

    # Build conversation history
    history = []
    for m in conv.messages[:-1]:
        history.append({
            "sender": m.sender,
            "message": m.text_content
        })

    # Generate Multimodal AI Response
    ai_response = generate_multimodal_response(
        user_message=user_text,
        image_filenames=image_filenames,
        conversation_history=history,
        language=language,
        model_preference=model_preference,
        custom_api_key=custom_api_key
    )

    assistant_text = ai_response.get("full_text", "Diagnosis complete.")

    # Save Assistant Message
    assistant_msg = Message(
        conversation_id=conv.id,
        sender="assistant",
        text_content=assistant_text
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "success": True,
        "conversation_id": conv.id,
        "user_message": user_msg.to_dict(),
        "assistant_message": assistant_msg.to_dict(),
        "structured_response": ai_response
    })


@chat_bp.route("/stream", methods=["POST"])
@login_required
def stream_message():
    """
    Real-time Server-Sent Events (SSE) streaming endpoint for ChatGPT-like token generation.
    """
    user = get_current_user()
    data = request.get_json() or {}
    conv_id = data.get("conversation_id")
    user_text = data.get("message", "").strip()
    image_filenames = data.get("image_filenames", [])
    language = data.get("language", user.preferred_lang or "en")
    model_preference = data.get("model_preference", "auto")
    custom_api_key = data.get("custom_api_key", "").strip() or None

    if not user_text and not image_filenames:
        return jsonify({"success": False, "message": "Message or image attachment required."}), 400

    # Retrieve or create Conversation
    if conv_id:
        conv = Conversation.query.filter_by(id=conv_id, user_id=user.id).first()
        if not conv:
            conv = Conversation(user_id=user.id, title="Rice Leaf Consultation")
            db.session.add(conv)
            db.session.commit()
    else:
        title_snippet = user_text[:35] if user_text else "Leaf Image Analysis"
        conv = Conversation(user_id=user.id, title=f"🌾 {title_snippet}")
        db.session.add(conv)
        db.session.commit()

    # Save User Message
    user_msg = Message(
        conversation_id=conv.id,
        sender="user",
        text_content=user_text or "Please analyze the attached rice leaf image."
    )
    db.session.add(user_msg)
    db.session.commit()

    # Attach images
    for img_fn in image_filenames:
        msg_img = MessageImage(
            message_id=user_msg.id,
            image_filename=img_fn,
            original_filename=img_fn
        )
        db.session.add(msg_img)
    db.session.commit()

    # Build conversation history
    history = []
    for m in conv.messages[:-1]:
        history.append({
            "sender": m.sender,
            "message": m.text_content
        })

    saved_conv_id = conv.id
    user_msg_dict = user_msg.to_dict()

    def generate():
        full_assistant_text = []
        try:
            # Yield metadata header event with conversation_id and user_msg
            meta_event = {
                "type": "meta",
                "conversation_id": saved_conv_id,
                "user_message": user_msg_dict
            }
            yield f"data: {json.dumps(meta_event)}\n\n"

            # Stream tokens
            for sse_line in stream_multimodal_response(
                user_message=user_text,
                image_filenames=image_filenames,
                conversation_history=history,
                language=language,
                model_preference=model_preference,
                custom_api_key=custom_api_key
            ):
                if sse_line.startswith("data: "):
                    try:
                        parsed = json.loads(sse_line[6:].strip())
                        tok = parsed.get("token", "")
                        if tok:
                            full_assistant_text.append(tok)
                    except Exception:
                        pass
                yield sse_line

        except Exception as err:
            print(f"[SSE Stream] Error during streaming: {err}")
        finally:
            complete_text = "".join(full_assistant_text).strip()
            if complete_text:
                try:
                    assistant_msg = Message(
                        conversation_id=saved_conv_id,
                        sender="assistant",
                        text_content=complete_text
                    )
                    db.session.add(assistant_msg)
                    db.session.commit()
                except Exception as e:
                    print(f"Failed to persist streamed assistant message: {e}")

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response
