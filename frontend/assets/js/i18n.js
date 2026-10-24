/**
 * AgriVersion - Multilingual Client-Side Translation Engine (i18n)
 * Supports 8 languages: English, Kannada, Telugu, Hindi, Tamil, Malayalam, Marathi, Bengali.
 */

const AgriI18n = (function() {
  const SUPPORTED_LANGUAGES = {
    "en": { name: "English", native: "English", bcp47: "en-US", flag: "🇬🇧" },
    "kn": { name: "Kannada", native: "ಕನ್ನಡ", bcp47: "kn-IN", flag: "🇮🇳" },
    "te": { name: "Telugu", native: "తెలుగు", bcp47: "te-IN", flag: "🇮🇳" },
    "hi": { name: "Hindi", native: "हिन्दी", bcp47: "hi-IN", flag: "🇮🇳" },
    "ta": { name: "Tamil", native: "தமிழ்", bcp47: "ta-IN", flag: "🇮🇳" },
    "ml": { name: "Malayalam", native: "മലയാളം", bcp47: "ml-IN", flag: "🇮🇳" },
    "mr": { name: "Marathi", native: "मराठी", bcp47: "mr-IN", flag: "🇮🇳" },
    "bn": { name: "Bengali", native: "বাংলা", bcp47: "bn-IN", flag: "🇮🇳" }
  };

  let currentLang = localStorage.getItem("agri_lang") || "en";
  let translations = {};
  const cache = {};

  async function loadTranslations(lang) {
    if (!SUPPORTED_LANGUAGES[lang]) {
      lang = "en";
    }

    if (cache[lang]) {
      translations = cache[lang];
      currentLang = lang;
      localStorage.setItem("agri_lang", lang);
      applyTranslations();
      return translations;
    }

    try {
      const res = await fetch(`/api/translations/${lang}`);
      if (res.ok) {
        translations = await res.json();
        cache[lang] = translations;
        currentLang = lang;
        localStorage.setItem("agri_lang", lang);
        applyTranslations();
      }
    } catch (e) {
      console.warn("Could not load translation file for", lang, e);
    }
    return translations;
  }

  function t(path, defaultVal = "") {
    if (!path) return defaultVal;
    const parts = path.split(".");
    let current = translations;
    for (const part of parts) {
      if (current && current[part] !== undefined) {
        current = current[part];
      } else {
        return defaultVal || path;
      }
    }
    return current || defaultVal || path;
  }

  function applyTranslations() {
    // Translate data-i18n elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const val = t(key);
      if (val && typeof val === "string") {
        el.textContent = val;
      }
    });

    // Translate data-i18n-html elements
    document.querySelectorAll("[data-i18n-html]").forEach(el => {
      const key = el.getAttribute("data-i18n-html");
      const val = t(key);
      if (val && typeof val === "string") {
        el.innerHTML = val;
      }
    });

    // Translate data-i18n-placeholder inputs
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      const val = t(key);
      if (val && typeof val === "string") {
        el.setAttribute("placeholder", val);
      }
    });

    // Update language selector dropdown label
    const activeLangObj = SUPPORTED_LANGUAGES[currentLang] || SUPPORTED_LANGUAGES["en"];
    const labelEl = document.getElementById("currentLangLabel");
    if (labelEl) {
      labelEl.textContent = `🌐 ${activeLangObj.native}`;
    }

    // Dispatch custom event
    document.dispatchEvent(new CustomEvent("languageChanged", {
      detail: { lang: currentLang, translations: translations }
    }));
  }

  function renderLanguageDropdown(containerId = "langSelectorContainer") {
    const container = document.getElementById(containerId);
    if (!container) return;

    const activeLangObj = SUPPORTED_LANGUAGES[currentLang] || SUPPORTED_LANGUAGES["en"];
    let html = `
      <div class="dropdown">
        <button class="lang-selector-btn dropdown-toggle" type="button" id="currentLangLabel" data-bs-toggle="dropdown" aria-expanded="false">
          🌐 ${activeLangObj.native}
        </button>
        <ul class="dropdown-menu dropdown-menu-agri dropdown-menu-end" aria-labelledby="currentLangLabel">
    `;

    for (const [code, info] of Object.entries(SUPPORTED_LANGUAGES)) {
      const activeClass = (code === currentLang) ? "active" : "";
      html += `
        <li>
          <a class="dropdown-item dropdown-item-agri ${activeClass}" href="javascript:void(0)" onclick="AgriI18n.setLanguage('${code}')">
            <span>${info.native}</span>
            <small class="text-muted" style="margin-left:8px;">${info.name}</small>
          </a>
        </li>
      `;
    }

    html += `</ul></div>`;
    container.innerHTML = html;
  }

  async function setLanguage(lang) {
    await loadTranslations(lang);
    // Optionally update user profile on server
    try {
      fetch("/api/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferred_lang: lang })
      });
    } catch (e) {}
  }

  function init() {
    loadTranslations(currentLang).then(() => {
      renderLanguageDropdown();
    });
  }

  return {
    init,
    loadTranslations,
    setLanguage,
    t,
    applyTranslations,
    renderLanguageDropdown,
    getCurrentLanguage: () => currentLang,
    getLanguageInfo: (code) => SUPPORTED_LANGUAGES[code || currentLang],
    SUPPORTED_LANGUAGES
  };
})();

// Auto-initialize i18n on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  AgriI18n.init();
});
