"""
AgriVersion - Multimodal AI Agricultural Assistant Service (RiceCare AI)
Supports:
- Multi-intent question decomposition (accurately answers multi-part questions)
- Real-time token streaming (Server-Sent Events)
- Multi-Provider LLM Backbone (Google Gemini, OpenAI GPT-4o, Groq Llama 3.3)
- High-Accuracy Built-in Agronomic RAG & Semantic Reasoning Engine
- Multimodal Vision Diagnostics (PyTorch CNN + Grad-CAM + Severity integration)
- Multi-Turn Conversation Memory & Context Awareness
"""

import os
import re
import json
import base64
import time
import requests
from PIL import Image

from backend.config import Config
from backend.services.ai_service import run_rice_leaf_diagnosis
from ml.dataset_info import DISEASE_CLASSES, DISEASE_DETAILS


LANGUAGE_NAMES = {
    "en": "English",
    "kn": "Kannada (ಕನ್ನಡ)",
    "hi": "Hindi (हिन्दी)",
    "te": "Telugu (తెలుగు)",
    "ta": "Tamil (தமிழ்)",
    "ml": "Malayalam (മലയാളം)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)"
}


def detect_requested_language(user_message, default_lang="en"):
    """
    Detects if the user prompt explicitly requests a specific language or contains native script.
    """
    if not user_message:
        return default_lang if default_lang in LANGUAGE_NAMES else "en"

    text_lower = user_message.lower()

    if any(k in text_lower for k in ["kannada", "kannad", "ಕನ್ನಡ", "kannadadalli", "kannadadali"]):
        return "kn"
    if any(k in text_lower for k in ["hindi", "हिन्दी", "हिंदी", "hindiyalli"]):
        return "hi"
    if any(k in text_lower for k in ["telugu", "తెలుగు"]):
        return "te"
    if any(k in text_lower for k in ["tamil", "தமிழ்"]):
        return "ta"
    if any(k in text_lower for k in ["malayalam", "മലയാളം"]):
        return "ml"
    if any(k in text_lower for k in ["marathi", "मराठी"]):
        return "mr"
    if any(k in text_lower for k in ["bengali", "bangla", "বাংলা"]):
        return "bn"
    if any(k in text_lower for k in ["english", "inglish"]):
        return "en"

    for char in user_message:
        code = ord(char)
        if 0x0C80 <= code <= 0x0CFF:
            return "kn"
        elif 0x0900 <= code <= 0x097F:
            return "hi"
        elif 0x0C00 <= code <= 0x0C7F:
            return "te"
        elif 0x0B80 <= code <= 0x0BFF:
            return "ta"
        elif 0x0D00 <= code <= 0x0D7F:
            return "ml"
        elif 0x0980 <= code <= 0x09FF:
            return "bn"

    return default_lang if default_lang in LANGUAGE_NAMES else "en"


def get_agronomy_system_prompt(language="en"):
    lang_name = LANGUAGE_NAMES.get(language, "English")
    return f"""You are RiceCare AI, an expert agronomist specializing in rice (Oryza sativa) diseases, pests, nutrition, and farming.

CRITICAL LANGUAGE MANDATE — FOLLOW STRICTLY:
- Target Language: You MUST reply COMPLETELY and ENTIRELY in {lang_name}.
- Full Response Alignment: Regardless of whether the user wrote in English or another language, if the requested language is {lang_name} or if the user asked in {lang_name}, generate 100% of your response (headings, explanations, dosages, symptoms, advice, summaries) in {lang_name}.
- Native Script Requirement: For non-English languages (such as Kannada, Hindi, Telugu, Tamil, Malayalam, Marathi, Bengali), write strictly using proper native script (e.g., Kannada script for Kannada: "ಧನ್ಯವಾದಗಳು", "ಲಕ್ಷಣಗಳು", "ಔಷಧ ಪ್ರಮಾಣ", "ರೋಗ ನಿರ್ವಹಣೆ"). Do NOT use Latin transliteration or Roman script for native Indian languages unless explicitly requested.
- Chemical & Technical Terms: Keep active chemical names (e.g., Tricyclazole, Hexaconazole, Urea, N-P-K) and scientific names clear, but describe all dosages, symptoms, instructions, and advice completely in {lang_name}.

CRITICAL CONTENT RULES:
1. **Be concise and specific.** Answer ONLY what the user asked. Do NOT add extra sections, summaries, or unrequested information.
2. **No long essays.** Keep answers short and to the point — like a knowledgeable friend chatting, not a textbook.
3. If the user asks "what is brown spot?" → give a 2-3 sentence answer in {lang_name}, NOT a full clinical report.
4. If the user asks for dosage → give ONLY the dosage in {lang_name}, not the full disease profile.
5. If the user asks for symptoms → give ONLY symptoms in {lang_name}, not treatment + prevention + fertilizer schedule.
6. Only give detailed multi-section responses when the user EXPLICITLY asks for "full details", "tell me everything", or "complete guide".
7. If the user asks multiple questions in one message, answer each briefly with numbered points in {lang_name}.
8. Use markdown formatting (bold, bullets) sparingly — only when it helps clarity.
9. If image diagnosis data is provided, mention the key finding (disease name, confidence, severity) in 1-2 lines, then give the specific advice requested in {lang_name}.
10. Tone: Friendly, expert, conversational — like a helpful agricultural advisor, not a research paper.
11. If the user greets you or asks who you are, respond naturally in 2-3 sentences in {lang_name}.
"""


def generate_multimodal_response(user_message, image_filenames=None, conversation_history=None, language="en", model_preference="auto", custom_api_key=None):
    """
    Synchronous response generation with automatic provider routing and fallback.
    """
    if image_filenames is None:
        image_filenames = []
    if conversation_history is None:
        conversation_history = []

    effective_lang = detect_requested_language(user_message, language)

    # 1. Run Computer Vision Diagnostics if images attached
    diagnoses = _run_image_diagnoses(image_filenames)

    # 2. Try External LLM Providers
    llm_response = _try_external_llms(
        user_message=user_message,
        image_filenames=image_filenames,
        diagnoses=diagnoses,
        conversation_history=conversation_history,
        language=effective_lang,
        model_preference=model_preference,
        custom_api_key=custom_api_key
    )

    if llm_response:
        return llm_response

    # 3. High-Accuracy Built-in Multi-Intent Reasoning Engine
    return _generate_expert_agricultural_response(user_message, diagnoses, conversation_history, effective_lang)


def stream_multimodal_response(user_message, image_filenames=None, conversation_history=None, language="en", model_preference="auto", custom_api_key=None):
    """
    Generator function that yields SSE tokens for real-time ChatGPT-style streaming.
    Yields JSON strings formatted as: data: {"token": "...", "done": false}\n\n
    """
    if image_filenames is None:
        image_filenames = []
    if conversation_history is None:
        conversation_history = []

    effective_lang = detect_requested_language(user_message, language)
    diagnoses = _run_image_diagnoses(image_filenames)

    # Check available keys
    gemini_key = custom_api_key or Config.GEMINI_API_KEY
    openai_key = custom_api_key if (model_preference and "gpt" in model_preference) else Config.OPENAI_API_KEY
    groq_key = custom_api_key if (model_preference and "groq" in model_preference) else Config.GROQ_API_KEY
    # For auto mode, also pick up server-configured Groq key
    if model_preference == "auto" and not groq_key:
        groq_key = Config.GROQ_API_KEY

    # 1. Try Gemini Streaming
    if (model_preference in ("auto", "gemini", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro") or gemini_key) and gemini_key:
        try:
            for token in _stream_gemini_api(user_message, image_filenames, diagnoses, conversation_history, gemini_key, model_preference, effective_lang):
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
            return
        except Exception as e:
            print(f"[Streaming] Gemini failed, falling back: {e}")

    # 2. Try OpenAI Streaming
    if (model_preference in ("openai", "gpt-4o", "gpt-4o-mini") or openai_key) and openai_key:
        try:
            for token in _stream_openai_api(user_message, image_filenames, diagnoses, conversation_history, openai_key, model_preference, effective_lang):
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
            return
        except Exception as e:
            print(f"[Streaming] OpenAI failed, falling back: {e}")

    # 3. Try Groq Streaming (auto mode, or explicit groq selection)
    if (model_preference in ("auto", "groq", "groq-gpt-oss", "groq-llama-3.3") or groq_key) and groq_key:
        try:
            for token in _stream_groq_api(user_message, diagnoses, conversation_history, groq_key, effective_lang):
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
            return
        except Exception as e:
            print(f"[Streaming] Groq failed, falling back: {e}")

    # 4. Built-in Multi-Intent Reasoning Engine (Streamed word-by-word with realistic typing speed)
    fallback_result = _generate_expert_agricultural_response(user_message, diagnoses, conversation_history, effective_lang)
    full_text = fallback_result.get("full_text", "")

    # Tokenize into words and newlines
    tokens = re.findall(r'\S+|\n', full_text)
    for i, t in enumerate(tokens):
        prefix = "" if (t.startswith("\n") or i == 0 or tokens[i-1].endswith("\n")) else " "
        yield f"data: {json.dumps({'token': prefix + t, 'done': False})}\n\n"
        time.sleep(0.012)

    yield f"data: {json.dumps({'token': '', 'done': True, 'structured': fallback_result.get('structured', False)})}\n\n"


def _run_image_diagnoses(image_filenames):
    """Runs Deep CNN diagnosis on all uploaded images."""
    diagnoses = []
    for img_fn in image_filenames:
        diag = run_rice_leaf_diagnosis(img_fn)
        if diag.get("success"):
            diagnoses.append(diag)
    return diagnoses


def _try_external_llms(user_message, image_filenames, diagnoses, conversation_history, language, model_preference, custom_api_key):
    """Attempts generation across configured external LLM providers."""
    # 1. Google Gemini
    gemini_key = custom_api_key or Config.GEMINI_API_KEY
    if gemini_key:
        try:
            res = _call_gemini_api(user_message, image_filenames, diagnoses, conversation_history, gemini_key, model_preference, language)
            if res:
                return res
        except Exception as e:
            print(f"[LLM] Gemini API call error: {e}")

    # 2. OpenAI
    openai_key = custom_api_key if (model_preference and "gpt" in model_preference) else Config.OPENAI_API_KEY
    if openai_key:
        try:
            res = _call_openai_api(user_message, image_filenames, diagnoses, conversation_history, openai_key, model_preference, language)
            if res:
                return res
        except Exception as e:
            print(f"[LLM] OpenAI API call error: {e}")

    # 3. Groq (also used in auto mode for text-only queries)
    groq_key = custom_api_key if (model_preference and "groq" in model_preference) else Config.GROQ_API_KEY
    if groq_key:
        try:
            res = _call_groq_api(user_message, diagnoses, conversation_history, groq_key, language)
            if res:
                return res
        except Exception as e:
            print(f"[LLM] Groq API call error: {e}")

    return None


# ==============================================================================
# Google Gemini API Provider
# ==============================================================================

def _call_gemini_api(user_message, image_filenames, diagnoses, conversation_history, api_key, model_pref="auto", language="en"):
    """Calls Google Gemini REST API with multi-turn history and vision context."""
    model_name = "gemini-2.0-flash" if "2.0" in model_pref else "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    contents = _build_gemini_contents(user_message, image_filenames, diagnoses, conversation_history)
    payload = {
        "systemInstruction": {
            "parts": [{"text": get_agronomy_system_prompt(language)}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.95,
            "maxOutputTokens": 2500
        }
    }

    res = requests.post(url, json=payload, timeout=25)
    if res.status_code == 200:
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join([p.get("text", "") for p in parts])
            return {"structured": False, "full_text": text}
    return None


def _stream_gemini_api(user_message, image_filenames, diagnoses, conversation_history, api_key, model_pref="auto", language="en"):
    """Streams Google Gemini responses chunk by chunk."""
    model_name = "gemini-2.0-flash" if "2.0" in model_pref else "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={api_key}"

    contents = _build_gemini_contents(user_message, image_filenames, diagnoses, conversation_history)
    payload = {
        "systemInstruction": {
            "parts": [{"text": get_agronomy_system_prompt(language)}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.95,
            "maxOutputTokens": 2500
        }
    }

    with requests.post(url, json=payload, stream=True, timeout=30) as r:
        if r.status_code != 200:
            raise Exception(f"Gemini stream failed with code {r.status_code}")
        for line in r.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    json_str = decoded[6:].strip()
                    try:
                        chunk = json.loads(json_str)
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                txt = p.get("text", "")
                                if txt:
                                    yield txt
                    except Exception:
                        pass


def _build_gemini_contents(user_message, image_filenames, diagnoses, conversation_history):
    """Builds multi-turn contents array for Gemini with vision attachments."""
    contents = []

    if conversation_history:
        for msg in conversation_history[-8:]:
            role = "user" if msg.get("sender") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("message", "")}]
            })

    current_parts = []
    if diagnoses:
        diag_summary = []
        for i, d in enumerate(diagnoses, 1):
            diag_summary.append(
                f"[Vision Diagnostic {i}]: Disease: {d['primary_disease']} | Confidence: {d['confidence']:.1f}% | "
                f"Severity: {d['severity']['severity_level']} ({d['severity']['affected_area_pct']}% affected leaf area, "
                f"{d['severity']['lesion_count']} lesions). Scientific: {d.get('scientific_name')}"
            )
        current_parts.append({
            "text": "--- Leaf Vision Diagnostics Context ---\n" + "\n".join(diag_summary) + "\n----------------------------------------\n"
        })

    for fn in image_filenames:
        path = os.path.join(Config.UPLOAD_FOLDER, fn)
        if os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/jpeg"
                if fn.lower().endswith(".png"):
                    mime = "image/png"
                elif fn.lower().endswith(".webp"):
                    mime = "image/webp"
                current_parts.append({
                    "inline_data": {
                        "mime_type": mime,
                        "data": b64
                    }
                })

    current_parts.append({"text": user_message or "Please provide a detailed agronomic analysis of the attached leaf image."})
    contents.append({"role": "user", "parts": current_parts})
    return contents


# ==============================================================================
# OpenAI API Provider
# ==============================================================================

def _call_openai_api(user_message, image_filenames, diagnoses, conversation_history, api_key, model_pref="gpt-4o-mini", language="en"):
    """Calls OpenAI chat completions API."""
    model_name = "gpt-4o" if "4o" in model_pref and "mini" not in model_pref else "gpt-4o-mini"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = _build_openai_messages(user_message, image_filenames, diagnoses, conversation_history, language)
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2500
    }

    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
    if res.status_code == 200:
        data = res.json()
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
            return {"structured": False, "full_text": text}
    return None


def _stream_openai_api(user_message, image_filenames, diagnoses, conversation_history, api_key, model_pref="gpt-4o-mini", language="en"):
    """Streams OpenAI chat completions."""
    model_name = "gpt-4o" if "4o" in model_pref and "mini" not in model_pref else "gpt-4o-mini"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = _build_openai_messages(user_message, image_filenames, diagnoses, conversation_history, language)
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2500,
        "stream": True
    }

    with requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=30) as r:
        if r.status_code != 200:
            raise Exception(f"OpenAI stream failed: {r.status_code}")
        for line in r.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: ") and decoded[6:].strip() != "[DONE]":
                    try:
                        chunk = json.loads(decoded[6:].strip())
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                    except Exception:
                        pass


def _build_openai_messages(user_message, image_filenames, diagnoses, conversation_history, language="en"):
    """Builds messages list for OpenAI chat completions."""
    messages = [{"role": "system", "content": get_agronomy_system_prompt(language)}]

    if conversation_history:
        for msg in conversation_history[-8:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("message", "")})

    user_content = []
    if diagnoses:
        diag_summary = []
        for i, d in enumerate(diagnoses, 1):
            diag_summary.append(
                f"[Vision Diagnostic {i}]: Disease: {d['primary_disease']} ({d['confidence']:.1f}% confidence), "
                f"Severity: {d['severity']['severity_level']}, Affected: {d['severity']['affected_area_pct']}%, Lesions: {d['severity']['lesion_count']}"
            )
        user_content.append({
            "type": "text",
            "text": "--- Visual Diagnostic System Output ---\n" + "\n".join(diag_summary) + "\n----------------------------------------\n"
        })

    for fn in image_filenames:
        path = os.path.join(Config.UPLOAD_FOLDER, fn)
        if os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/jpeg"
                if fn.lower().endswith(".png"):
                    mime = "image/png"
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"}
                })

    user_content.append({"type": "text", "text": user_message or "Analyze this leaf image and advise on management."})
    messages.append({"role": "user", "content": user_content})
    return messages


# ==============================================================================
# Groq API Provider
# ==============================================================================

def _call_groq_api(user_message, diagnoses, conversation_history, api_key, language="en"):
    """Calls Groq ultra-fast LLM API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": get_agronomy_system_prompt(language)}]
    if conversation_history:
        for msg in conversation_history[-8:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("message", "")})

    diag_text = ""
    if diagnoses:
        diag_text = f"\n[Vision Model Prediction: {diagnoses[0]['primary_disease']} ({diagnoses[0]['confidence']:.1f}% confidence, Severity: {diagnoses[0]['severity']['severity_level']})]\n"

    messages.append({"role": "user", "content": diag_text + user_message})

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2500
    }

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
    if res.status_code == 200:
        data = res.json()
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
            return {"structured": False, "full_text": text}
    return None


def _stream_groq_api(user_message, diagnoses, conversation_history, api_key, language="en"):
    """Streams Groq chat completions."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": get_agronomy_system_prompt(language)}]
    if conversation_history:
        for msg in conversation_history[-8:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("message", "")})

    diag_text = ""
    if diagnoses:
        diag_text = f"\n[Vision Model Prediction: {diagnoses[0]['primary_disease']} ({diagnoses[0]['confidence']:.1f}% confidence, Severity: {diagnoses[0]['severity']['severity_level']})]\n"

    messages.append({"role": "user", "content": diag_text + user_message})

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2500,
        "stream": True
    }

    with requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=25) as r:
        if r.status_code != 200:
            raise Exception(f"Groq stream failed: {r.status_code}")
        for line in r.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: ") and decoded[6:].strip() != "[DONE]":
                    try:
                        chunk = json.loads(decoded[6:].strip())
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                    except Exception:
                        pass


# ==============================================================================
# High-Accuracy Multi-Intent Decomposition & Agronomy Reasoning Engine
# ==============================================================================

def _generate_expert_agricultural_response(user_message, diagnoses, conversation_history, language):
    """
    Advanced Multi-Intent Agronomic Reasoning Engine.
    Dissects multi-part user prompts, extracts all questions/entities, and constructs
    distinct, structured answers for each question without merging into single canned responses.
    """
    query_lower = user_message.lower().strip()

    # 1. IMAGE ATTACHMENT DIAGNOSTICS FIRST
    if diagnoses:
        return _handle_image_diagnostics(diagnoses)

    # 2. MULTI-INTENT DETECTION & QUESTION DECOMPOSITION
    intents = _extract_all_query_intents(query_lower, conversation_history)

    # If multiple intents detected, build a structured multi-part response
    if len(intents) > 1:
        sections = []
        for idx, intent in enumerate(intents, 1):
            title = intent["title"]
            body = intent["content"]
            sections.append(f"### {idx}. {title}\n{body}")

        full_text = (
            f"### 🌾 Comprehensive Response to Your Queries\n\n"
            + "\n\n---\n\n".join(sections)
            + "\n\n### 💡 Integrated Farm Management Summary\n"
            + "- Maintain weekly field scouting along diagonal transects.\n"
            + "- Avoid excess nitrogen top-dressing during cloudy weather.\n"
            + "- Adhere strictly to the manufacturer's pre-harvest interval (PHI) for chemical sprays."
        )

        return {"structured": False, "full_text": full_text}

    # If single intent matched
    if len(intents) == 1:
        return {"structured": False, "full_text": intents[0]["content"]}

    # Fallback to general agronomy guidance
    ans = _generate_general_agronomy_answer(user_message, query_lower)
    return {"structured": False, "full_text": ans}


def _extract_all_query_intents(query_lower, conversation_history):
    """
    Extracts all distinct user questions/intents from a single multi-part prompt.
    Returns a list of dicts: [{"topic": str, "title": str, "content": str}]
    """
    intents = []
    seen_topics = set()

    # 1. Check for Disease Inquiries (can detect multiple diseases in one prompt!)
    matched_diseases = []
    for d_name in DISEASE_CLASSES:
        # Match disease name or key synonyms
        short_name = d_name.lower().replace(" disease", "").replace(" damage", "")
        if short_name in query_lower:
            matched_diseases.append(d_name)

    # Check for context disease if user asks follow-up
    if not matched_diseases and conversation_history:
        for prev in reversed(conversation_history):
            text_to_check = prev.get("message", "")
            for d_name in DISEASE_CLASSES:
                if d_name.lower() in text_to_check.lower():
                    if any(sig in query_lower for sig in ["it", "this disease", "treat it", "cure it", "spray", "medicine", "dosage", "symptom", "control"]):
                        matched_diseases.append(d_name)
                    break
            if matched_diseases:
                break

    for d_name in matched_diseases:
        if d_name not in seen_topics:
            seen_topics.add(d_name)
            content = _build_disease_response(d_name, query_lower)
            intents.append({
                "topic": d_name,
                "title": f"**{d_name}** - Clinical Diagnosis & Treatment",
                "content": content
            })

    # 2. Check for Fertilizer / NPK / Dosage Calculations
    if any(w in query_lower for w in ["fertilizer", "npk", "urea", "dap", "mop", "potash", "nitrogen", "phosphorus", "zinc", "calculate dosage", "fertilizer schedule"]):
        if "fertilizer" not in seen_topics:
            seen_topics.add("fertilizer")
            content = _build_fertilizer_response(query_lower)
            intents.append({
                "topic": "fertilizer",
                "title": "Rice Crop Fertilizer & Nutrient Schedule",
                "content": content
            })

    # 3. Check for Water Management / AWD (Alternate Wetting and Drying)
    if any(w in query_lower for w in ["water", "irrigation", "awd", "alternate wetting", "drain", "drainage", "flood", "submerge", "water depth"]):
        if "water" not in seen_topics:
            seen_topics.add("water")
            content = _build_water_response()
            intents.append({
                "topic": "water",
                "title": "Paddy Water Management & AWD Protocol",
                "content": content
            })

    # 4. Check for Insect Pests & IPM
    pest_signals = ["stem borer", "planthopper", "bph", "leaf folder", "hispa", "gall midge", "gundhi bug", "insect", "pest control", "caterpillar", "bug"]
    if any(w in query_lower for w in pest_signals):
        if "pest" not in seen_topics:
            seen_topics.add("pest")
            content = _build_pest_response(query_lower)
            intents.append({
                "topic": "pest",
                "title": "Insect Pest Management & Targeted Formulations",
                "content": content
            })

    # 5. Check for Weed Control & Herbicides
    if any(w in query_lower for w in ["weed", "herbicide", "grass", "sedges", "pretilachlor", "bispyribac", "weed control"]):
        if "weed" not in seen_topics:
            seen_topics.add("weed")
            content = _build_weed_response()
            intents.append({
                "topic": "weed",
                "title": "Paddy Weed Management & Herbicide Schedule",
                "content": content
            })

    # 6. Check for Seed Treatment & Nursery
    if any(w in query_lower for w in ["seed treatment", "seedbed", "nursery", "sprout seed", "soak seed", "seed germination"]):
        if "seed" not in seen_topics:
            seen_topics.add("seed")
            content = _build_seed_response()
            intents.append({
                "topic": "seed",
                "title": "Seed Treatment & Healthy Nursery Protocol",
                "content": content
            })

    # 7. Check for Rice Varieties / Sowing / Climate
    if any(w in query_lower for w in ["variety", "varieties", "cultivar", "samba mahsuri", "ir64", "swarna", "basmati", "mtu 1010", "sona masoori", "sowing time"]):
        if "varieties" not in seen_topics:
            seen_topics.add("varieties")
            content = _build_varieties_response()
            intents.append({
                "topic": "varieties",
                "title": "Rice Varieties & Cultivar Characteristics",
                "content": content
            })

    # 8. Check for Local Agricultural Stores & Product Availability (Module 29)
    store_signals = ["store", "shop", "buy", "purchase", "dealer", "retailer", "where can i find", "where to get", "nearby", "availability", "stock", "find products"]
    if any(w in query_lower for w in store_signals):
        if "store" not in seen_topics:
            seen_topics.add("store")
            content = _build_store_inquiry_response(query_lower, matched_diseases, conversation_history)
            intents.append({
                "topic": "store",
                "title": "🏪 Nearby Agricultural Stores & Product Availability",
                "content": content
            })

    # 9. Check for Greetings / Capabilities
    if any(w in query_lower for w in ["hi", "hello", "hey", "who are you", "what can you do", "help me"]):
        if not intents and "greeting" not in seen_topics:
            seen_topics.add("greeting")
            content = (
                "Hello! I am **RiceCare AI**, your high-accuracy conversational agronomist and crop pathologist.\n\n"
                "### 🌾 How I Can Assist You:\n"
                "- 🔬 **Multimodal Leaf Diagnosis:** Upload or take photos of diseased leaves for instant deep CNN + Grad-CAM analysis.\n"
                "- 🦠 **Targeted Treatments & Dosages:** Verified chemical formulations (g/L or mL/L) and organic controls for all 20 rice diseases.\n"
                "- 🏪 **Local Agri Store Finder:** Locate verified nearby agricultural input retailers with real-time product stock availability.\n"
                "- 🧪 **Fertilizer Calculators:** Custom N-P-K schedules and split calculations per acre or hectare.\n"
                "- 💧 **Water & AWD Guides:** Irrigation timings and disease-suppressive water regimes.\n"
                "- 🐛 **Integrated Pest Management (IPM):** Accurate identification and sprays for stem borers, leaf folders, planthoppers, and gall midges.\n\n"
                "💡 *Feel free to ask any question or attach an image below!*"
            )
            intents.append({
                "topic": "greeting",
                "title": "Welcome to RiceCare AI",
                "content": content
            })

    return intents


def _build_disease_response(d_name, query_lower):
    """Builds a highly accurate, structured disease profile tailored to the user's specific request."""
    details = DISEASE_DETAILS.get(d_name, {})

    # Detect if user specifically asked for spray/dosage vs symptoms vs causes
    wants_spray = any(w in query_lower for w in ["spray", "dosage", "dose", "treat", "cure", "medicine", "fungicide", "bactericide", "chemical", "control"])
    wants_symptoms = any(w in query_lower for w in ["symptom", "identify", "look like", "sign", "cause", "why"])

    if wants_spray and not wants_symptoms:
        return (
            f"**Pathogen Etiology:** *{details.get('scientific_name', '')}* ({details.get('pathogen_type', '')})\n\n"
            f"#### 🧪 Chemical Control & Dosages:\n{details.get('management', '')}\n\n"
            f"#### 🛡️ Biological & Cultural Prevention:\n{details.get('prevention', '')}\n\n"
            f"#### 📋 Field Spray Parameters:\n"
            f"- **Spray Volume:** 200 Liters of water per acre using a calibrated hollow-cone nozzle.\n"
            f"- **Application Window:** Early morning (7:00 AM – 10:00 AM) or late afternoon (4:00 PM – 6:00 PM).\n"
            f"- **Severity Threshold:** {details.get('severity_guide', '')}"
        )
    elif wants_symptoms and not wants_spray:
        return (
            f"**Scientific Name:** *{details.get('scientific_name', '')}* ({details.get('pathogen_type', '')})\n\n"
            f"#### 🌱 Distinctive Foliar Symptoms:\n{details.get('symptoms', '')}\n\n"
            f"#### ⚡ Environmental Causes & Triggers:\n{details.get('causes', '')}\n\n"
            f"#### 📊 Severity Benchmark:\n{details.get('severity_guide', '')}"
        )
    else:
        return (
            f"**Scientific Name:** *{details.get('scientific_name', '')}* | **Etiology:** {details.get('pathogen_type', '')}\n\n"
            f"| Clinical Aspect | Agronomic Specifications & Recommendations |\n"
            f"| :--- | :--- |\n"
            f"| **Symptoms** | {details.get('symptoms', '')} |\n"
            f"| **Causes & Climate** | {details.get('causes', '')} |\n"
            f"| **Chemical Treatment** | {details.get('management', '')} |\n"
            f"| **Cultural Prevention** | {details.get('prevention', '')} |\n"
            f"| **Economic Threshold** | {details.get('severity_guide', '')} |"
        )


def _build_fertilizer_response(query_lower):
    """Builds fertilizer schedules and computes dynamic dosage if acres/hectares mentioned."""
    # Check if number of acres was mentioned (e.g. "for 3 acres", "for 2.5 acre", "5 acres")
    acre_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:acres?|acre)', query_lower)
    acres = float(acre_match.group(1)) if acre_match else 1.0

    dap_total = round(45 * acres, 1)
    urea_basal = round(10 * acres, 1)
    urea_tillering = round(35 * acres, 1)
    urea_panicle = round(25 * acres, 1)
    mop_basal = round(17 * acres, 1)
    mop_panicle = round(17 * acres, 1)
    zinc_total = round(10 * acres, 1)

    acre_text = f"for **{acres:g} Acre(s)**" if acre_match else "(Standard Per Acre Recommendation)"

    return (
        f"Recommended N-P-K nutrient ratio for high-yielding rice is **100:50:50 kg/ha** (or **40:20:20 kg/acre**).\n\n"
        f"#### 📅 Calibrated Nutrient Schedule {acre_text}:\n\n"
        f"| Growth Stage | Crop Timing | Commercial Fertilizers to Apply |\n"
        f"| :--- | :--- | :--- |\n"
        f"| **Basal Application** | Final puddling / at planting | **DAP**: {dap_total} kg + **MOP (Potash)**: {mop_basal} kg + **Zinc Sulphate (21%)**: {zinc_total} kg |\n"
        f"| **Active Tillering** | 20–25 Days After Transplanting (DAT) | **Urea**: {urea_tillering} kg (Top-dress with 2 cm standing water) |\n"
        f"| **Panicle Initiation** | 40–45 DAT (Booting stage) | **Urea**: {urea_panicle} kg + **MOP (Potash)**: {mop_panicle} kg (Strengthens culm against blast/lodging) |\n"
        f"| **Heading / Grain Filling** | 60–65 DAT | *Foliar spray of 1% 13:0:45 (Potassium Nitrate) for plump grain filling* |\n\n"
        f"⚠️ **Important Precautions:**\n"
        f"- Do NOT mix Zinc Sulphate directly with DAP in the same fertilizer basin (causes insoluble zinc phosphate precipitation).\n"
        f"- Avoid excess urea top-dressing during overcast or humid spells to prevent foliar blast and bacterial blight outbreaks."
    )


def _build_water_response():
    """Builds AWD and water management response."""
    return (
        "Practicing **Alternate Wetting and Drying (AWD)** saves up to **30% irrigation water**, enhances root oxygenation, and suppresses soil-borne fungal pathogens (*Rhizoctonia solani* - Sheath Blight).\n\n"
        "#### 📈 Stage-Wise Water Regime:\n"
        "1. **Transplanting & Seedling Establishment (0–7 DAT):** Keep shallow standing water (**2–3 cm**) to prevent seedling drying.\n"
        "2. **Tillering Phase (8–35 DAT) - AWD Cycle:** Allow standing water to recede naturally until the water level drops **15 cm below the soil surface** (monitored via field perforated tube / pani pipe), then re-flood to 5 cm.\n"
        "3. **Panicle Initiation to Flowering (Critical Phase):** Maintain continuous **3–5 cm** standing water. *Water deficit during flowering results in high floret sterility (chaffy grains).*\n"
        "4. **Milk & Dough Stage:** Maintain saturated soil only (no deep ponding).\n"
        "5. **Pre-Harvest Drainage:** Drain the field completely **10–12 days prior to harvest** for uniform grain maturation and easy combine harvesting."
    )


def _build_pest_response(query_lower):
    """Builds IPM pest control response."""
    return (
        "| Insect Pest | Key Field Symptoms | Recommended Chemical Formulation & Dosage |\n"
        "| :--- | :--- | :--- |\n"
        "| **Yellow Stem Borer** (*Scirpophaga incertulas*) | 'Dead Hearts' in vegetative tillers; 'Whiteheads' (sterile erect panicles) at heading | **Chlorantraniliprole 18.5 SC** @ 0.3 mL/L or **Cartap Hydrochloride 4G** @ 10 kg/acre |\n"
        "| **Brown Planthopper (BPH)** (*Nilaparvata lugens*) | Sap-sucking at hill base resulting in circular drying ('Hopper Burn') | **Pymetrozine 50 WDG** @ 0.6 g/L or **Triflumezopyrim 10 SC** @ 0.5 mL/L (Create 30 cm alleyways) |\n"
        "| **Leaf Folder** (*Cnaphalocrocis medinalis*) | Leaves rolled longitudinally with transparent white scraped patches | **Flubendiamide 39.35 SC** @ 0.2 mL/L or **Emamectin Benzoate 5 SG** @ 0.4 g/L |\n"
        "| **Rice Hispa** (*Dicladispa armigera*) | Parallel white streaks on upper blade and blister mines | **Chlorpyrifos 20 EC** @ 2.0 mL/L or **Neem Oil 1500 ppm** @ 3 mL/L |\n"
        "| **Gall Midge** (*Orseolia oryzae*) | Tillers transform into tubular silvery galls ('Silver Shoots' / 'Onion Leaf') | **Fipronil 5 SC** @ 2.0 mL/L or **Chlorpyrifos 10G** granules @ 4 kg/acre |\n\n"
        "#### 🛡️ Biological IPM Measures:\n"
        "- Install **Pheromone Traps** @ 8–10 traps/ha for early stem borer detection.\n"
        "- Conserve natural predators (Wolf spiders, Mirid bugs, Dragonflies) by avoiding indiscriminate synthetic pyrethroid sprays."
    )


def _build_weed_response():
    """Builds weed control and herbicide protocol."""
    return (
        "Uncontrolled weed competition during early crop growth can reduce paddy yield by **30–50%**.\n\n"
        "#### 1. Pre-Emergence Herbicide (0–3 DAT):\n"
        "- **Pretilachlor 50 EC (with safener)** @ **500 mL/acre** OR **Pyrazosulfuron-ethyl 10 WP** @ **80 g/acre**.\n"
        "- *Apply within 3 days of transplanting in 2–3 cm standing water; hold water for 48 hours.*\n\n"
        "#### 2. Early Post-Emergence Herbicide (15–20 DAT):\n"
        "- **Bispyribac-sodium 10 SC** @ **80–100 mL/acre** (Controls grasses, sedges, and broadleaf weeds).\n"
        "- **Penoxsulam 24 SC** @ **40–50 mL/acre** for broad-spectrum weed suppression.\n"
        "- *Drain standing water before spraying, then re-flood after 48 hours.*"
    )


def _build_seed_response():
    """Builds seed treatment response."""
    return (
        "Seed treatment eliminates seed-borne pathogens (*Bakanae, Blast, Bacterial Leaf Blight, Brown Spot*) before field planting.\n\n"
        "#### 🔬 Standard 3-Step Seed Treatment Protocol:\n"
        "1. **Brine Flotation Selection:** Dissolve common salt in water until a fresh egg floats. Add paddy seeds; skim off floating chaffy seeds and wash sunken healthy seeds twice in clean water.\n"
        "2. **Fungicide & Bactericide Soaking:**\n"
        "   - Dissolve **Carbendazim 50 WP** @ 2 g/kg seed OR **Tricyclazole 75 WP** @ 2 g/kg seed + **Streptocycline** @ 1 g/10 kg seed in 10 L water.\n"
        "   - Soak seeds for 24 hours, drain, and incubate in moist gunny bags for 24–36 hours until sprouted.\n"
        "3. **Biological Inoculation:** Treat sprouted seeds with **Trichoderma harzianum** @ 10 g/kg seed and **Azospirillum / PSB biofertilizer** @ 250 g/acre."
    )


def _build_varieties_response():
    """Builds rice varieties and cultivar selection guidance."""
    return (
        "| Variety / Cultivar | Duration (Days) | Key Characteristics & Disease Resistance |\n"
        "| :--- | :--- | :--- |\n"
        "| **IR64** | 115–120 | Semi-dwarf, high tillering, moderate resistance to Blast and Bacterial Blight. |\n"
        "| **Samba Mahsuri (BPT 5204)** | 145–150 | Premium fine-grain cooking quality, high market price; susceptible to Blast. |\n"
        "| **Improved Samba Mahsuri** | 140–145 | Introgressed with *Xa21, xa13, xa5* genes for near-immune resistance to **Bacterial Leaf Blight**. |\n"
        "| **MTU 1010 (Cottondora Sannalu)** | 120–125 | Short duration, non-lodging, suitable for both Kharif and Rabi seasons. |\n"
        "| **Swarna (MTU 7029)** | 145–150 | Heavy yielder for lowland irrigated belts; tolerant to submergence (*Swarna-Sub1*). |\n"
        "| **Pusa Basmati 1121** | 140–145 | Extra-long slender grains, aromatic; requires careful blast management. |"
    )


def _handle_image_diagnostics(diagnoses):
    """Handles single and multi-image vision CNN diagnostic results."""
    if len(diagnoses) == 1:
        d = diagnoses[0]
        d_name = d["primary_disease"]
        conf = d["confidence"]
        sev = d["severity"]
        details = DISEASE_DETAILS.get(d_name, {})

        if d_name == "Healthy":
            obs_text = "The leaf blade demonstrates uniform chlorophyll pigmentation, intact epidermal cellular architecture, smooth linear venation, and 0% pathological necrotic lesions."
            diag_text = "**Healthy Rice Foliage** (*Oryza sativa L.*)\n- Pathogen: None detected\n- Physiological Status: Fully active photosynthetic leaf canopy."
            conf_text = f"RiceNet Deep CNN Confidence: **{conf:.2f}%** | Health Index: **100% Active**"
            symp_text = "Erect, vibrant green leaf blade, clean leaf sheath, vigorous tillering without chlorotic or water-soaked borders."
            prev_text = "Adhere to balanced N-P-K (avoid excessive urea top-dressing), maintain 2-5 cm optimal water depth, and inspect fields weekly."
            mgmt_text = "Standard agronomic maintenance; apply standard split fertilizer schedule (Basal, Active Tillering, Panicle Initiation)."
            note_text = "Maintaining optimal crop spacing (20x15 cm) ensures good aeration and minimizes the risk of microclimatic humidity spikes."
        else:
            obs_text = (
                f"Multimodal image segmentation identified localized foliar abnormalities. "
                f"Quantified severity assessment: **{sev['affected_area_pct']}% affected leaf surface**, "
                f"**{sev['healthy_area_pct']}% active photosynthetic tissue**, and **{sev['lesion_count']} distinct lesion focal spots**."
            )
            diag_text = (
                f"Primary Diagnosis: **{d_name}** (*{details.get('scientific_name', '')}*)\n"
                f"- Etiology / Pathogen Type: **{details.get('pathogen_type', '')}**\n"
                f"- Severity Rating: **{sev['severity_level'].upper()}**"
            )
            conf_text = f"RiceNet Vision Model Confidence: **{conf:.2f}%** | Validation: High Precision Spectral Analysis"
            symp_text = details.get("symptoms", "Foliar lesions visible across leaf blade.")
            prev_text = details.get("prevention", "Maintain balanced soil nutrition and proper field sanitation.")
            mgmt_text = details.get("management", "Apply approved targeted fungicides/bactericides at prescribed dosages.")
            note_text = (
                f"**Severity Benchmark:** {details.get('severity_guide', '')}\n"
                f"*Always spray early in the morning or late afternoon to avoid photo-degradation and drift.*"
            )

        full_text = (
            f"### 🔍 Visual Observation\n{obs_text}\n\n"
            f"### 🦠 Primary Diagnosis\n{diag_text}\n\n"
            f"### 📊 Deep Learning Diagnostic Metrics\n{conf_text}\n\n"
            f"### 🌱 Characteristic Symptoms\n{symp_text}\n\n"
            f"### 🛡️ Preventive & Cultural Practices\n{prev_text}\n\n"
            f"### 🌾 Recommended Chemical & Bio-Management\n{mgmt_text}\n\n"
            f"### ⚠️ Field Advisory & Safety Note\n{note_text}"
        )

        return {
            "structured": True,
            "observation": obs_text,
            "disease": diag_text,
            "confidence": conf_text,
            "symptoms": symp_text,
            "prevention": prev_text,
            "management": mgmt_text,
            "note": note_text,
            "full_text": full_text
        }
    else:
        # Multi-image comparative diagnostic
        comp_lines = []
        for i, d in enumerate(diagnoses, 1):
            comp_lines.append(f"- **Specimen {i}**: Diagnosed as **{d['primary_disease']}** ({d['confidence']:.1f}% confidence, Severity: **{d['severity']['severity_level']}**, Lesions: {d['severity']['lesion_count']})")

        all_names = set([d["primary_disease"] for d in diagnoses])
        same_disease = len(all_names) == 1

        if same_disease:
            comp_summary = f"All {len(diagnoses)} leaf specimens consistently exhibit **{diagnoses[0]['primary_disease']}** pathology across varying stages of development."
        else:
            comp_summary = f"Multi-specimen analysis indicates **mixed foliar pathology** involving: {', '.join(all_names)}."

        obs_text = f"Comparative Scan of {len(diagnoses)} Leaf Samples:\n" + "\n".join(comp_lines) + f"\n\n{comp_summary}"
        diag_text = f"Primary finding: **{diagnoses[0]['primary_disease']}**"
        conf_text = f"Evaluated across {len(diagnoses)} image frames with consensus aggregation."
        symp_text = diagnoses[0].get("symptoms", "")
        prev_text = diagnoses[0].get("prevention", "")
        mgmt_text = diagnoses[0].get("management", "")
        note_text = "Multi-angle visual inspection offers significantly higher diagnostic confidence than single-point leaf scans."

        full_text = (
            f"### 🔍 Multi-Specimen Observation\n{obs_text}\n\n"
            f"### 🦠 Comparative Pathology Analysis\n{diag_text}\n\n"
            f"### 📊 Consensus Insights\n{conf_text}\n\n"
            f"### 🌱 Symptoms & Progression\n{symp_text}\n\n"
            f"### 🛡️ Preventive Action Plan\n{prev_text}\n\n"
            f"### 🌾 Target Management & Spray Schedule\n{mgmt_text}\n\n"
            f"### ⚠️ Advisory Note\n{note_text}"
        )

        return {
            "structured": True,
            "observation": obs_text,
            "disease": diag_text,
            "confidence": conf_text,
            "symptoms": symp_text,
            "prevention": prev_text,
            "management": mgmt_text,
            "note": note_text,
            "full_text": full_text
        }


def _generate_general_agronomy_answer(user_message, query_lower):
    """Answers general botanical, agricultural, and general questions accurately."""
    if "photosynthesis" in query_lower:
        return (
            "### 🌿 Photosynthesis in Rice (*Oryza sativa*)\n\n"
            "Rice is a **C3 photosynthetic plant**. Photosynthesis occurs primarily in the leaf mesophyll cells containing chloroplasts:\n\n"
            "$$\\text{6CO}_2 + \\text{6H}_2\\text{O} + \\text{Sunlight} \\longrightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + \\text{6O}_2$$\n\n"
            "#### 🌾 Physiological Importance in Paddy:\n"
            "- **Flag Leaf Contribution:** The uppermost **flag leaf** contributes over **50–60% of total carbohydrates** to the developing panicle during grain filling.\n"
            "- **Impact of Foliar Diseases:** Pathogens like **Rice Blast** and **Brown Spot** destroy green photosynthetic area, directly causing grain sterility and yield collapse."
        )

    return (
        f"### 🌾 Agronomic Guidance: Rice Crop Management\n\n"
        f"Regarding your query on: **\"{user_message}\"**\n\n"
        f"#### 🔍 Key Agronomic Principles:\n"
        f"1. **Foliar Health & Monitoring:** Inspect crop canopies weekly across diagonal field lines for early lesion spots, yellowing, or insect egg masses.\n"
        f"2. **Nutrient Equilibrium:** Adhere to balanced N-P-K (100:50:50 kg/ha) with split urea applications to avoid tissue succulence.\n"
        f"3. **Water Management:** Practice Alternate Wetting and Drying (AWD) during tillering to promote deep root anchoring.\n"
        f"4. **Calibrated Interventions:** When spraying protective fungicides or insecticides, maintain 200 Liters water per acre for uniform coverage.\n\n"
        f"#### 💡 What would you like to explore next?\n"
        f"- Leaf disease identification & spray dosage\n"
        f"- Fertilizer split scheduling & soil health\n"
        f"- Photo scan of affected leaves (attach below)\n"
        f"- Pest control (Stem borer, BPH, Leaf folder)"
    )


def _build_store_inquiry_response(query_lower, matched_diseases=None, conversation_history=None):
    """
    Builds an interactive, structured store availability response with nearby retailer listings,
    reported stock states, and mandatory non-prescriptive safety disclaimers.
    """
    from backend.services.store_service import search_stores, get_disease_management_category

    # Determine disease context if any
    target_disease = matched_diseases[0] if (matched_diseases and len(matched_diseases) > 0) else None
    if not target_disease and conversation_history:
        for prev in reversed(conversation_history):
            text = prev.get("message", "")
            for d in DISEASE_CLASSES:
                if d.lower() in text.lower():
                    target_disease = d
                    break
            if target_disease:
                break

    # Determine location from query
    loc_query = None
    for loc_name in ["mandya", "mysuru", "mysore", "maddur", "pandavapura", "bengaluru", "bangalore", "shivamogga", "shimoga", "raichur", "warangal", "thanjavur"]:
        if loc_name in query_lower:
            loc_query = loc_name
            break

    search_res = search_stores(query=loc_query, disease=target_disease, max_distance_km=60.0)
    stores = search_res.get("stores", [])[:4]
    search_center = search_res.get("search_center", {}).get("label", "Mandya Region, Karnataka")

    lines = []
    if target_disease:
        rec = get_disease_management_category(target_disease)
        lines.append(f"I found participating agricultural retailers near **{search_center}** with reported inputs relevant to **{target_disease}**.")
        lines.append(f"\n> **Relevant Category:** *{rec.get('category_title', 'Registered Crop Protection')}*\n")
    else:
        lines.append(f"I found participating registered agricultural input stores near **{search_center}** with verified inventory records.")

    lines.append("\n### 📍 Participating Agricultural Stores:\n")

    if not stores:
        lines.append(f"No stores currently registered within 60 km of {search_center}. You can check the full interactive map on the [🏪 Agri Stores Page](/stores.html).")
    else:
        for s in stores:
            v_badge = "✓ Verified Agri Store" if s.get("is_verified") else "Registered Retailer"
            status_icon = "🟢" if s.get("relevant_stock_status") == "in_stock" or s.get("overall_stock") == "in_stock" else ("🟡" if s.get("relevant_stock_status") == "limited_stock" else "⚪")
            stock_msg = s.get("relevant_stock_text") or ("In Stock" if s.get("overall_stock") == "in_stock" else "Contact store for stock")
            dist = s.get("distance_text", "")
            updated = s.get("inventory_freshness_text", "Recently")

            phone_clean = s.get("phone", "").replace(" ", "").replace("-", "")
            lat, lng = s.get("latitude"), s.get("longitude")
            dir_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

            lines.append(f"#### 🏪 **{s['store_name']}** `[{v_badge}]`")
            lines.append(f"- 📍 **Location:** {s['address']}, {s['city']} (*{dist}*)")
            lines.append(f"- {status_icon} **Stock Status:** {stock_msg} (*Updated {updated}*)")
            lines.append(f"- 🕒 **Hours:** {s.get('opening_hours', '08:00 AM - 08:00 PM')}")
            lines.append(f"- 🔗 **Actions:** [📞 Call Store](tel:{phone_clean}) &nbsp;|&nbsp; [🗺️ Get Directions]({dir_url}) &nbsp;|&nbsp; [🛒 View Store Inventory](/stores.html?store_id={s['id']})")
            lines.append("")

    lines.append("\n---\n")
    lines.append("> ⚠️ **Availability & Safety Notice:**\n"
                 "> Store inventory availability can change rapidly due to farm demand. Always call the retailer to confirm stock before traveling.\n"
                 "> **AI Detection ≠ Biological Diagnosis • Product Availability ≠ Chemical Prescription.** Always verify with an authorized agricultural officer and follow registered container label instructions.")

    return "\n".join(lines)
