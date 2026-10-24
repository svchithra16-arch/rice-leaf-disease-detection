/**
 * AgriVersion - RiceCare AI Multimodal Assistant Script
 * Features:
 * - Real-time SSE Token Streaming with live Markdown rendering
 * - Multi-Model selection (Gemini 2.0 Flash, GPT-4o Mini, Groq Llama 3.3, Built-in RAG)
 * - Custom User API Key support (localStorage persistence)
 * - Interactive ChatGPT-style Prompt Starter Cards
 * - Professional High-Contrast Markdown parser (Tables, Code blocks with Copy, Headers, Lists)
 * - Message Action Bar (Copy message, TTS speech, Regenerate, Feedback)
 * - Multi-image vision attachments & Live Speech Recognition
 */

let activeConversationId = null;
let pendingImageAttachments = [];
let isStreamingActive = false;
let currentAbortController = null;
let selectedModelId = "auto";
let selectedModelLabel = "🌾 RiceCare AI (Auto)";

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true);
  loadSavedSettings();
  loadConversations();
  setupComposerEvents();
  renderWelcomeView();

  // Check URL query params for initial preloaded query or disease
  const urlParams = new URLSearchParams(window.location.search);
  const initialDisease = urlParams.get("disease");
  if (initialDisease) {
    const input = document.getElementById("chatInput");
    if (input) {
      input.value = `Tell me about symptoms, causes, and recommended spray dosage for ${initialDisease}.`;
      sendMessage();
    }
  }
});

// ==============================================================================
// Model & Settings Management
// ==============================================================================

function loadSavedSettings() {
  const savedModel = localStorage.getItem("agri_ai_model");
  const savedLabel = localStorage.getItem("agri_ai_model_label");
  if (savedModel) {
    selectedModelId = savedModel;
    selectedModelLabel = savedLabel || savedModel;
    const lbl = document.getElementById("currentModelLabel");
    if (lbl) lbl.textContent = selectedModelLabel;
  }
}

function selectAiModel(modelId, modelLabel) {
  selectedModelId = modelId;
  selectedModelLabel = modelLabel;
  localStorage.setItem("agri_ai_model", modelId);
  localStorage.setItem("agri_ai_model_label", modelLabel);

  const lbl = document.getElementById("currentModelLabel");
  if (lbl) lbl.textContent = modelLabel;

  // Update active state in dropdown
  document.querySelectorAll("#modelSelectDropdownList .dropdown-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("onclick").includes(`'${modelId}'`));
  });

  AgriApp.showToast(`Active model switched to ${modelLabel}`, "success");
}

function openChatSettingsModal() {
  const sel = document.getElementById("settingModelSelect");
  if (sel) sel.value = selectedModelId || "auto";

  const geminiInput = document.getElementById("settingGeminiKey");
  if (geminiInput) geminiInput.value = localStorage.getItem("agri_custom_gemini_key") || "";

  const openaiInput = document.getElementById("settingOpenaiKey");
  if (openaiInput) openaiInput.value = localStorage.getItem("agri_custom_openai_key") || "";

  const groqInput = document.getElementById("settingGroqKey");
  if (groqInput) groqInput.value = localStorage.getItem("agri_custom_groq_key") || "";

  const streamToggle = document.getElementById("settingStreamToggle");
  if (streamToggle) {
    streamToggle.checked = localStorage.getItem("agri_stream_enabled") !== "false";
  }

  const modalEl = document.getElementById("chatSettingsModal");
  if (modalEl) {
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  }
}

function saveChatSettings() {
  const sel = document.getElementById("settingModelSelect");
  if (sel) {
    const selectedOption = sel.options[sel.selectedIndex];
    selectAiModel(sel.value, selectedOption.text);
  }

  const geminiKey = document.getElementById("settingGeminiKey").value.trim();
  const openaiKey = document.getElementById("settingOpenaiKey").value.trim();
  const groqKey = document.getElementById("settingGroqKey").value.trim();
  const streamEnabled = document.getElementById("settingStreamToggle").checked;

  localStorage.setItem("agri_custom_gemini_key", geminiKey);
  localStorage.setItem("agri_custom_openai_key", openaiKey);
  localStorage.setItem("agri_custom_groq_key", groqKey);
  localStorage.setItem("agri_stream_enabled", streamEnabled ? "true" : "false");

  const modalEl = document.getElementById("chatSettingsModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }

  AgriApp.showToast("Chat settings and API preferences saved successfully.", "success");
}

function getActiveApiKey() {
  if (selectedModelId.includes("gemini")) {
    return localStorage.getItem("agri_custom_gemini_key") || "";
  } else if (selectedModelId.includes("gpt")) {
    return localStorage.getItem("agri_custom_openai_key") || "";
  } else if (selectedModelId.includes("groq")) {
    return localStorage.getItem("agri_custom_groq_key") || "";
  }
  return localStorage.getItem("agri_custom_gemini_key") || localStorage.getItem("agri_custom_openai_key") || localStorage.getItem("agri_custom_groq_key") || "";
}

// ==============================================================================
// Conversation History & Session Management
// ==============================================================================

async function loadConversations(searchQuery = "") {
  try {
    const url = searchQuery ? `/api/chat/conversations?q=${encodeURIComponent(searchQuery)}` : "/api/chat/conversations";
    const res = await fetch(url);
    const data = await res.json();

    const listContainer = document.getElementById("chatHistoryList");
    if (!listContainer) return;

    if (!data.conversations || data.conversations.length === 0) {
      listContainer.innerHTML = `<div class="text-center text-muted p-3" style="font-size:0.85rem;">No conversation history yet.</div>`;
      return;
    }

    let html = "";
    data.conversations.forEach(c => {
      const activeClass = (c.id === activeConversationId) ? "active" : "";
      html += `
        <div class="chat-session-item ${activeClass}" onclick="openConversation(${c.id})">
          <div class="chat-session-title">
            <i class="fas fa-comment-alt me-2 text-emerald"></i>
            <span>${AgriApp.escapeHtml(c.title)}</span>
          </div>
          <div class="chat-session-actions" onclick="event.stopPropagation()">
            <i class="fas fa-edit chat-action-icon" title="Rename" onclick="renameConversation(${c.id})"></i>
            <i class="fas fa-trash-alt chat-action-icon text-danger" title="Delete" onclick="deleteConversation(${c.id})"></i>
          </div>
        </div>
      `;
    });

    listContainer.innerHTML = html;
  } catch (e) {
    console.warn("Failed to load conversations:", e);
  }
}

async function startNewConversation() {
  if (isStreamingActive && currentAbortController) {
    currentAbortController.abort();
    isStreamingActive = false;
  }

  activeConversationId = null;
  pendingImageAttachments = [];
  renderAttachmentPreviews();
  renderWelcomeView();

  document.querySelectorAll(".chat-session-item").forEach(el => el.classList.remove("active"));
  const input = document.getElementById("chatInput");
  if (input) {
    input.value = "";
    input.focus();
  }
}

function renderWelcomeView() {
  const msgContainer = document.getElementById("chatMessages");
  if (!msgContainer) return;

  msgContainer.innerHTML = `
    <div class="chat-welcome-hero">
      <div class="welcome-avatar-wrap">
        <div class="welcome-avatar">🌾</div>
        <div class="welcome-pulse"></div>
      </div>
      <h2 class="welcome-title">RiceCare AI Agricultural Assistant</h2>
      <p class="welcome-subtitle">
        Your high-accuracy expert agronomist & crop pathologist. Ask questions about paddy diseases, multi-part farm calculations, fertilizer schedules, or attach leaf photos for deep CNN diagnostics.
      </p>

      <!-- ChatGPT-Style Starter Prompt Cards -->
      <div class="prompt-starters-grid">
        <div class="starter-card" onclick="triggerStarterPrompt('What is Rice Blast and how to cure it? Also calculate fertilizer for 2 acres, and explain AWD water management.')">
          <div class="starter-icon">🌾</div>
          <div class="starter-text">
            <strong>Multi-Question Farm Advisory</strong>
            <span>Blast treatment + 2-acre fertilizer calc + AWD irrigation</span>
          </div>
        </div>

        <div class="starter-card" onclick="triggerStarterPrompt('How do I identify and treat Rice Blast? What exact fungicide dosage should I use?')">
          <div class="starter-icon">🦠</div>
          <div class="starter-text">
            <strong>Rice Blast Treatment</strong>
            <span>Symptoms, fungicide formulations & dosage per acre</span>
          </div>
        </div>

        <div class="starter-card" onclick="triggerStarterPrompt('Calculate the optimal N-P-K fertilizer and Urea split schedule for 3 acres of rice.')">
          <div class="starter-icon">🧪</div>
          <div class="starter-text">
            <strong>Fertilizer Calculator (3 Acres)</strong>
            <span>Stage-wise DAP, Urea, MOP & Zinc schedule</span>
          </div>
        </div>

        <div class="starter-card" onclick="triggerStarterPrompt('How does Alternate Wetting and Drying (AWD) water management work in rice fields?')">
          <div class="starter-icon">💧</div>
          <div class="starter-text">
            <strong>AWD Irrigation Guide</strong>
            <span>Save water, prevent root rot & suppress sheath blight</span>
          </div>
        </div>

        <div class="starter-card" onclick="triggerStarterPrompt('How can I identify and control Yellow Stem Borer pests in vegetative vs heading stages?')">
          <div class="starter-icon">🐛</div>
          <div class="starter-text">
            <strong>Stem Borer IPM</strong>
            <span>Dead hearts vs Whiteheads and recommended sprays</span>
          </div>
        </div>

        <div class="starter-card" onclick="document.getElementById('chatImageFileInput').click()">
          <div class="starter-icon">📷</div>
          <div class="starter-text">
            <strong>Upload Leaf Photo</strong>
            <span>Deep CNN + Grad-CAM heatmap & severity scan</span>
          </div>
        </div>
      </div>
    </div>
  `;
}

function triggerStarterPrompt(text) {
  const input = document.getElementById("chatInput");
  if (input) {
    input.value = text;
    sendMessage();
  }
}

async function openConversation(convId) {
  if (isStreamingActive && currentAbortController) {
    currentAbortController.abort();
    isStreamingActive = false;
  }

  activeConversationId = convId;
  pendingImageAttachments = [];
  renderAttachmentPreviews();

  try {
    const res = await fetch(`/api/chat/conversations/${convId}`);
    const data = await res.json();
    if (!data.success) return;

    loadConversations();

    const msgContainer = document.getElementById("chatMessages");
    if (!msgContainer) return;

    if (!data.messages || data.messages.length === 0) {
      renderWelcomeView();
      return;
    }

    let html = "";
    data.messages.forEach(m => {
      html += createMessageBubbleHtml(m.sender, m.text_content, m.images, m.id);
    });

    msgContainer.innerHTML = html;
    msgContainer.scrollTop = msgContainer.scrollHeight;
  } catch (e) {
    console.warn("Error opening conversation:", e);
  }
}

async function renameConversation(convId) {
  const newTitle = prompt("Enter new title for this consultation:");
  if (!newTitle || !newTitle.trim()) return;

  try {
    await fetch(`/api/chat/conversations/${convId}/rename`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle.trim() })
    });
    loadConversations();
  } catch (e) {
    AgriApp.showToast("Failed to rename conversation.", "error");
  }
}

async function deleteConversation(convId) {
  if (!confirm("Are you sure you want to delete this consultation history?")) return;

  try {
    await fetch(`/api/chat/conversations/${convId}`, { method: "DELETE" });
    if (activeConversationId === convId) {
      startNewConversation();
    }
    loadConversations();
    AgriApp.showToast("Conversation deleted.", "success");
  } catch (e) {
    AgriApp.showToast("Failed to delete conversation.", "error");
  }
}

async function exportCurrentConversation() {
  if (!activeConversationId) {
    AgriApp.showToast("No active conversation to export.", "warning");
    return;
  }

  try {
    const res = await fetch(`/api/chat/conversations/${activeConversationId}/export`);
    const data = await res.json();
    if (data.success && data.content) {
      const blob = new Blob([data.content], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `RiceCare_Consultation_${activeConversationId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      AgriApp.showToast("Conversation exported successfully!", "success");
    } else {
      AgriApp.showToast("Failed to export conversation.", "error");
    }
  } catch (e) {
    AgriApp.showToast("Error exporting conversation transcript.", "error");
  }
}

// ==============================================================================
// Composer & Message Sending (Streaming SSE & Fallback)
// ==============================================================================

function setupComposerEvents() {
  const input = document.getElementById("chatInput");
  const fileInput = document.getElementById("chatImageFileInput");
  const searchInput = document.getElementById("chatSearchInput");

  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 130) + "px";
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      if (e.target.files && e.target.files.length > 0) {
        for (const file of e.target.files) {
          await uploadAttachmentFile(file);
        }
        fileInput.value = "";
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      loadConversations(e.target.value.trim());
    });
  }

  const composerBox = document.querySelector(".chat-composer-box");
  if (composerBox) {
    composerBox.addEventListener("dragover", (e) => {
      e.preventDefault();
      composerBox.classList.add("dragover");
    });
    composerBox.addEventListener("dragleave", () => {
      composerBox.classList.remove("dragover");
    });
    composerBox.addEventListener("drop", async (e) => {
      e.preventDefault();
      composerBox.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        for (const file of e.dataTransfer.files) {
          if (file.type.startsWith("image/")) {
            await uploadAttachmentFile(file);
          }
        }
      }
    });
  }
}

async function uploadAttachmentFile(file) {
  const formData = new FormData();
  formData.append("image", file);

  try {
    const res = await fetch("/api/chat/upload-image", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      pendingImageAttachments.push({
        filename: data.filename,
        url: data.image_url,
        originalName: data.original_name
      });
      renderAttachmentPreviews();
    } else {
      AgriApp.showToast(data.message || "Failed to upload image.", "error");
    }
  } catch (e) {
    AgriApp.showToast("Error attaching image.", "error");
  }
}

function renderAttachmentPreviews() {
  const container = document.getElementById("chatAttachmentPreviews");
  if (!container) return;

  if (pendingImageAttachments.length === 0) {
    container.innerHTML = "";
    return;
  }

  let html = "";
  pendingImageAttachments.forEach((att, idx) => {
    html += `
      <div class="attach-chip">
        <img src="${att.url}" class="attach-chip-img" />
        <span>Image ${idx + 1}</span>
        <i class="fas fa-times-circle attach-chip-remove" onclick="removeAttachment(${idx})"></i>
      </div>
    `;
  });

  container.innerHTML = html;
}

function removeAttachment(index) {
  pendingImageAttachments.splice(index, 1);
  renderAttachmentPreviews();
}

async function sendMessage() {
  const input = document.getElementById("chatInput");
  const text = input ? input.value.trim() : "";
  const filenames = pendingImageAttachments.map(a => a.filename);

  if (!text && filenames.length === 0) return;

  // Clear welcome screen if present
  const msgContainer = document.getElementById("chatMessages");
  if (msgContainer && msgContainer.querySelector(".chat-welcome-hero")) {
    msgContainer.innerHTML = "";
  }

  // Append user bubble to UI immediately
  const userMsgHtml = createMessageBubbleHtml("user", text, pendingImageAttachments);
  if (msgContainer) {
    msgContainer.innerHTML += userMsgHtml;
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  // Clear composer
  if (input) {
    input.value = "";
    input.style.height = "auto";
  }
  const sendingAttachments = [...filenames];
  pendingImageAttachments = [];
  renderAttachmentPreviews();

  const streamEnabled = localStorage.getItem("agri_stream_enabled") !== "false";
  const customKey = getActiveApiKey();
  const currentLang = window.AgriI18n ? AgriI18n.getCurrentLanguage() : "en";

  if (streamEnabled) {
    await sendStreamingMessage(text, sendingAttachments, currentLang, customKey);
  } else {
    await sendStandardMessage(text, sendingAttachments, currentLang, customKey);
  }
}

// ==============================================================================
// Real-Time SSE Token Streaming Flow
// ==============================================================================

async function sendStreamingMessage(text, filenames, currentLang, customKey) {
  const msgContainer = document.getElementById("chatMessages");
  const aiMsgId = "aiMsg_" + Date.now();

  const aiBubbleHtml = `
    <div class="message-wrapper ai-msg" id="${aiMsgId}">
      <div class="message-avatar ai-avatar">🌾</div>
      <div class="message-bubble">
        <div class="stream-content msg-text-content"><span class="typing-cursor"></span></div>
        <div class="ai-msg-actions d-none"></div>
      </div>
    </div>
  `;
  if (msgContainer) {
    msgContainer.innerHTML += aiBubbleHtml;
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  isStreamingActive = true;
  currentAbortController = new AbortController();

  let accumulatedText = "";

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: activeConversationId,
        message: text,
        image_filenames: filenames,
        language: currentLang,
        model_preference: selectedModelId,
        custom_api_key: customKey
      }),
      signal: currentAbortController.signal
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const block of lines) {
        const line = block.trim();
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.substring(6));

            if (data.type === "meta") {
              activeConversationId = data.conversation_id;
              loadConversations();
            } else if (data.token) {
              accumulatedText += data.token;
              updateStreamingBubble(aiMsgId, accumulatedText, true);
              if (msgContainer) msgContainer.scrollTop = msgContainer.scrollHeight;
            } else if (data.done) {
              updateStreamingBubble(aiMsgId, accumulatedText, false);
            }
          } catch (err) {
            console.error("SSE parse error:", err);
          }
        }
      }
    }

    updateStreamingBubble(aiMsgId, accumulatedText, false);
    loadConversations();
  } catch (e) {
    if (e.name === "AbortError") {
      updateStreamingBubble(aiMsgId, accumulatedText + "\n\n*(Generation paused)*", false);
    } else {
      console.error("Streaming error:", e);
      const bubble = document.getElementById(aiMsgId);
      if (bubble) {
        bubble.querySelector(".stream-content").innerHTML = `
          <div class="text-danger fw-bold"><i class="fas fa-exclamation-triangle me-1"></i> Error generating response. Please check network or API settings.</div>
        `;
      }
    }
  } finally {
    isStreamingActive = false;
    currentAbortController = null;
  }
}

function updateStreamingBubble(elementId, text, isStillStreaming) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const contentEl = el.querySelector(".stream-content");
  if (!contentEl) return;

  let parsed = formatMarkdownMessage(text);
  if (isStillStreaming) {
    parsed += `<span class="typing-cursor"></span>`;
  }
  contentEl.innerHTML = parsed;

  if (!isStillStreaming) {
    const actionsEl = el.querySelector(".ai-msg-actions");
    if (actionsEl) {
      actionsEl.classList.remove("d-none");
      actionsEl.innerHTML = `
        <button class="msg-action-btn" title="Copy Response" onclick="copyMessageText(this, \`${escapeForAttribute(text)}\`)">
          <i class="fas fa-copy"></i> Copy
        </button>
        <button class="msg-action-btn" title="Listen (Text-to-Speech)" onclick="AgriVoice.speakText(\`${escapeForSpeech(text)}\`)">
          <i class="fas fa-volume-up"></i> Listen
        </button>
        <button class="msg-action-btn" title="Helpful" onclick="AgriApp.showToast('Thank you for your feedback!', 'success')">
          <i class="far fa-thumbs-up"></i>
        </button>
        <button class="msg-action-btn" title="Not Helpful" onclick="AgriApp.showToast('Feedback noted. We are refining accuracy.', 'info')">
          <i class="far fa-thumbs-down"></i>
        </button>
        <button class="msg-action-btn" title="Regenerate" onclick="regenerateLastResponse()">
          <i class="fas fa-redo-alt"></i> Retry
        </button>
      `;
    }
  }
}

// ==============================================================================
// Synchronous Fallback Flow
// ==============================================================================

async function sendStandardMessage(text, filenames, currentLang, customKey) {
  const msgContainer = document.getElementById("chatMessages");
  const typingId = "aiTypingIndicator_" + Date.now();

  if (msgContainer) {
    msgContainer.innerHTML += `
      <div class="message-wrapper ai-msg" id="${typingId}">
        <div class="message-avatar ai-avatar">🌾</div>
        <div class="message-bubble">
          <span class="spinner-agri me-2" style="width:16px;height:16px;"></span>
          <span class="text-white fw-bold">RiceCare AI is synthesizing clinical diagnosis & recommendations...</span>
        </div>
      </div>
    `;
    msgContainer.scrollTop = msgContainer.scrollHeight;
  }

  try {
    const res = await fetch("/api/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: activeConversationId,
        message: text,
        image_filenames: filenames,
        language: currentLang,
        model_preference: selectedModelId,
        custom_api_key: customKey
      })
    });

    const data = await res.json();
    const typing = document.getElementById(typingId);
    if (typing) typing.remove();

    if (!data.success) {
      AgriApp.showToast(data.message || "Failed to generate AI response.", "error");
      return;
    }

    activeConversationId = data.conversation_id;
    loadConversations();

    const assistantMsg = data.assistant_message;
    const aiBubbleHtml = createMessageBubbleHtml("assistant", assistantMsg.text_content, null, assistantMsg.id);

    if (msgContainer) {
      msgContainer.innerHTML += aiBubbleHtml;
      msgContainer.scrollTop = msgContainer.scrollHeight;
    }
  } catch (e) {
    const typing = document.getElementById(typingId);
    if (typing) typing.remove();
    AgriApp.showToast("Error communicating with AI assistant.", "error");
  }
}

async function regenerateLastResponse() {
  const lastUserMsg = document.querySelector(".chat-messages-container .user-msg:last-of-type");
  if (!lastUserMsg) return;

  const textNode = lastUserMsg.querySelector(".msg-text-content");
  if (textNode) {
    const promptText = textNode.textContent.trim();
    if (promptText) {
      const input = document.getElementById("chatInput");
      if (input) input.value = promptText;
      sendMessage();
    }
  }
}

// ==============================================================================
// High-Accuracy Clean Markdown Parser
// ==============================================================================

function createMessageBubbleHtml(sender, text, images = null, messageId = null) {
  const isUser = (sender === "user");

  let imgHtml = "";
  if (images && images.length > 0) {
    imgHtml = `<div class="message-images-grid">`;
    images.forEach(img => {
      const url = img.image_url || img.url;
      imgHtml += `<img src="${url}" class="msg-thumb-img" onclick="window.open('${url}', '_blank')"/>`;
    });
    imgHtml += `</div>`;
  }

  const parsed = formatMarkdownMessage(text);

  let actionsHtml = "";
  if (!isUser) {
    actionsHtml = `
      <div class="ai-msg-actions">
        <button class="msg-action-btn" title="Copy Response" onclick="copyMessageText(this, \`${escapeForAttribute(text)}\`)">
          <i class="fas fa-copy"></i> Copy
        </button>
        <button class="msg-action-btn" title="Listen (Text-to-Speech)" onclick="AgriVoice.speakText(\`${escapeForSpeech(text)}\`)">
          <i class="fas fa-volume-up"></i> Listen
        </button>
        <button class="msg-action-btn" title="Helpful" onclick="AgriApp.showToast('Thank you for your feedback!', 'success')">
          <i class="far fa-thumbs-up"></i>
        </button>
        <button class="msg-action-btn" title="Not Helpful" onclick="AgriApp.showToast('Feedback noted. We are refining accuracy.', 'info')">
          <i class="far fa-thumbs-down"></i>
        </button>
        <button class="msg-action-btn" title="Regenerate" onclick="regenerateLastResponse()">
          <i class="fas fa-redo-alt"></i> Retry
        </button>
      </div>
    `;
  }

  return `
    <div class="message-wrapper ${isUser ? 'user-msg' : 'ai-msg'}" data-msg-id="${messageId || ''}">
      <div class="message-avatar ${isUser ? 'user-avatar' : 'ai-avatar'}">
        ${isUser ? '👤' : '🌾'}
      </div>
      <div class="message-bubble">
        ${imgHtml}
        <div class="msg-text-content">${parsed}</div>
        ${actionsHtml}
      </div>
    </div>
  `;
}

function formatMarkdownMessage(text) {
  if (!text) return "";

  // 1. Escape HTML
  let out = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // 2. Protect Code Blocks
  const codeBlocks = [];
  out = out.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    const cleanCode = code.trim();
    const html = `
      <div class="code-block-wrapper">
        <div class="code-block-header">
          <span>${lang || 'code'}</span>
          <button class="btn-copy-code" onclick="copyCodeSnippet(this, \`${escapeForAttribute(cleanCode)}\`)">
            <i class="fas fa-copy"></i> Copy
          </button>
        </div>
        <pre><code class="language-${lang}">${cleanCode}</code></pre>
      </div>
    `;
    codeBlocks.push(html);
    return placeholder;
  });

  // 3. Protect Tables
  const tableBlocks = [];
  const tableRegex = /((?:\|[^\n]+\|\r?\n)+)/g;
  out = out.replace(tableRegex, (match) => {
    const rows = match.trim().split("\n");
    if (rows.length < 2) return match;

    let tableHtml = '<div class="table-responsive"><table class="ai-custom-table">';
    let isHeader = true;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i].trim();
      if (/^\|[-:\s|]+\|$/.test(row)) {
        isHeader = false;
        continue;
      }
      const cells = row.split("|").slice(1, -1);
      if (isHeader) {
        tableHtml += '<thead><tr>';
        cells.forEach(c => { tableHtml += `<th>${c.trim()}</th>`; });
        tableHtml += '</tr></thead><tbody>';
      } else {
        tableHtml += '<tr>';
        cells.forEach(c => { tableHtml += `<td>${c.trim()}</td>`; });
        tableHtml += '</tr>';
      }
    }
    tableHtml += '</tbody></table></div>';

    const placeholder = `__TABLE_BLOCK_${tableBlocks.length}__`;
    tableBlocks.push(tableHtml);
    return placeholder;
  });

  // 4. Inline Code
  out = out.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // 5. Section Dividers
  out = out.replace(/^---$/gm, '<hr class="ai-divider"/>');

  // 6. Headings
  out = out.replace(/^### (.*?)$/gm, '<h3 class="ai-section-h3"><i class="fas fa-angle-right me-2 text-emerald"></i>$1</h3>');
  out = out.replace(/^#### (.*?)$/gm, '<h4 class="ai-section-h4">$1</h4>');

  // 7. Bold & Italics
  out = out.replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="text-white"><em>$1</em></strong>');
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>');
  out = out.replace(/\*(.*?)\*/g, '<em class="text-emerald-light">$1</em>');

  // 8. Bullet Lists
  out = out.replace(/^\s*[-•]\s+(.*?)$/gm, '<li class="ai-list-item">$1</li>');
  out = out.replace(/(<li class="ai-list-item">[\s\S]*?<\/li>)+/g, '<ul class="ai-bullet-list">$&</ul>');

  // 9. Numbered Lists
  out = out.replace(/^\s*(\d+)\.\s+(.*?)$/gm, '<li class="ai-num-item"><span class="num-badge">$1</span> <span>$2</span></li>');
  out = out.replace(/(<li class="ai-num-item">[\s\S]*?<\/li>)+/g, '<ol class="ai-num-list">$&</ol>');

  // 10. Paragraph Linebreaks
  out = out.replace(/\n\n/g, '<div class="para-spacer"></div>');
  out = out.replace(/\n/g, '<br/>');

  // 11. Restore Tables and Code Blocks (without corrupting <br/> tags inside them)
  tableBlocks.forEach((tbl, idx) => {
    out = out.replace(`__TABLE_BLOCK_${idx}__`, tbl);
  });
  codeBlocks.forEach((cb, idx) => {
    out = out.replace(`__CODE_BLOCK_${idx}__`, cb);
  });

  return out;
}

// ==============================================================================
// Utilities: Copy, TTS, Voice
// ==============================================================================

function copyMessageText(btnEl, text) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btnEl.innerHTML;
    btnEl.innerHTML = '<i class="fas fa-check text-emerald"></i> Copied!';
    AgriApp.showToast("Message copied to clipboard!", "success");
    setTimeout(() => { btnEl.innerHTML = original; }, 2000);
  });
}

function copyCodeSnippet(btnEl, code) {
  navigator.clipboard.writeText(code).then(() => {
    const original = btnEl.innerHTML;
    btnEl.innerHTML = '<i class="fas fa-check text-emerald"></i> Copied!';
    setTimeout(() => { btnEl.innerHTML = original; }, 2000);
  });
}

function escapeForSpeech(text) {
  if (!text) return "";
  return text.replace(/[`\\$"]/g, '').replace(/###/g, '').replace(/\*\*/g, '').replace(/\|/g, ' ');
}

function escapeForAttribute(text) {
  if (!text) return "";
  return text.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}

function toggleVoiceRecognition() {
  const micBtn = document.getElementById("btnVoiceMic");
  const waveEl = document.getElementById("voiceListeningWave");

  if (AgriVoice.isListening()) {
    AgriVoice.stopListening();
    if (micBtn) micBtn.classList.remove("active-mic");
    if (waveEl) waveEl.classList.add("d-none");
  } else {
    const started = AgriVoice.startListening(
      (transcript) => {
        const input = document.getElementById("chatInput");
        if (input) {
          input.value = transcript;
          input.focus();
        }
        if (micBtn) micBtn.classList.remove("active-mic");
        if (waveEl) waveEl.classList.add("d-none");
      },
      () => {
        if (micBtn) micBtn.classList.remove("active-mic");
        if (waveEl) waveEl.classList.add("d-none");
      },
      (err) => {
        if (micBtn) micBtn.classList.remove("active-mic");
        if (waveEl) waveEl.classList.add("d-none");
      }
    );

    if (started) {
      if (micBtn) micBtn.classList.add("active-mic");
      if (waveEl) waveEl.classList.remove("d-none");
    }
  }
}
