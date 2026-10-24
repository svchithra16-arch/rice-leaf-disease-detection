/**
 * AgriVersion - Voice Assistant Engine (Speech-to-Text & Text-to-Speech)
 * Supports multilingual STT & TTS across 8 Indian & International languages.
 */

const AgriVoice = (function() {
  let recognition = null;
  let isListening = false;
  let isSpeaking = false;
  let currentUtterance = null;

  // Map application language codes to BCP-47 Speech Recognition / Synthesis tags
  const LANG_BCP47_MAP = {
    "en": "en-IN",
    "kn": "kn-IN",
    "te": "te-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "bn": "bn-IN"
  };

  function initSpeechRecognition(onResultCallback, onEndCallback, onErrorCallback) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Speech Recognition API is not supported in this browser.");
      return null;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResultCallback) onResultCallback(transcript);
    };

    recognition.onend = () => {
      isListening = false;
      if (onEndCallback) onEndCallback();
    };

    recognition.onerror = (event) => {
      isListening = false;
      console.error("Speech Recognition Error:", event.error);
      if (onErrorCallback) onErrorCallback(event.error);
    };

    return recognition;
  }

  function startListening(onResultCallback, onEndCallback, onErrorCallback) {
    if (!recognition) {
      initSpeechRecognition(onResultCallback, onEndCallback, onErrorCallback);
    }

    if (!recognition) {
      if (window.AgriApp) {
        AgriApp.showToast("Speech Recognition is not supported in your browser. Please type your query.", "warning");
      }
      return false;
    }

    const currentLang = window.AgriI18n ? AgriI18n.getCurrentLanguage() : "en";
    recognition.lang = LANG_BCP47_MAP[currentLang] || "en-US";

    try {
      recognition.start();
      isListening = true;
      return true;
    } catch (e) {
      console.warn("Failed to start voice recognition:", e);
      return false;
    }
  }

  function stopListening() {
    if (recognition && isListening) {
      recognition.stop();
      isListening = false;
    }
  }

  function speakText(text, lang = null, onStart = null, onEnd = null) {
    if (!('speechSynthesis' in window)) {
      console.warn("Speech Synthesis API not supported.");
      return false;
    }

    stopSpeaking(); // Cancel any ongoing speech

    if (!text) return false;

    // Clean markdown hashes and symbols before speech synthesis
    const cleanText = text
      .replace(/###\s*/g, '')
      .replace(/\*\*/g, '')
      .replace(/[🔍🦠📊🌱🛡️🌾⚠️#*]/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '')
      .trim();

    if (!cleanText) return false;

    currentUtterance = new SpeechSynthesisUtterance(cleanText);
    
    if (!lang) {
      lang = window.AgriI18n ? AgriI18n.getCurrentLanguage() : "en";
    }
    const bcp47 = LANG_BCP47_MAP[lang] || "en-US";
    currentUtterance.lang = bcp47;
    currentUtterance.rate = 0.95;
    currentUtterance.pitch = 1.0;

    // Try finding a matching native voice
    const voices = window.speechSynthesis.getVoices();
    const matchingVoice = voices.find(v => v.lang === bcp47 || v.lang.startsWith(lang));
    if (matchingVoice) {
      currentUtterance.voice = matchingVoice;
    }

    currentUtterance.onstart = () => {
      isSpeaking = true;
      if (onStart) onStart();
    };

    currentUtterance.onend = () => {
      isSpeaking = false;
      if (onEnd) onEnd();
    };

    currentUtterance.onerror = (e) => {
      isSpeaking = false;
      if (onEnd) onEnd();
    };

    window.speechSynthesis.speak(currentUtterance);
    return true;
  }

  function stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      isSpeaking = false;
    }
  }

  return {
    startListening,
    stopListening,
    speakText,
    stopSpeaking,
    isListening: () => isListening,
    isSpeaking: () => isSpeaking
  };
})();
