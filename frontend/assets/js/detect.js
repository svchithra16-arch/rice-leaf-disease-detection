/**
 * AgriVersion - Disease Detection & Diagnostic Suite Script
 * Handles image upload, botanical validation, live neural inference,
 * Grad-CAM visualization, quantitative lesion area estimation, and scientific reporting.
 */

// Centralized Confidence Configuration (Configurable)
const CONFIDENCE_LEVELS = {
  HIGH: 85.0,
  MODERATE: 60.0
};

let selectedFile = null;
let lastDiagnosisResult = null;

let currentDetectLocation = null;

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true);
  loadUserFields();
  initUploadZone();
  loadSampleLeavesGallery();
});

async function loadSampleLeavesGallery() {
  try {
    const res = await fetch("/api/detect/sample-leaves");
    const data = await res.json();
    const select = document.getElementById("sampleLeafSelect");
    if (select && data.samples) {
      select.innerHTML = '<option value="">-- Select Rice Condition Sample (20 Available) --</option>';
      data.samples.forEach(s => {
        const opt = document.createElement("option");
        opt.value = JSON.stringify(s);
        opt.textContent = `[Class ${s.class_index.toString().padStart(2, '0')}] ${s.disease_name}`;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.warn("Failed to load sample leaves list:", e);
  }
}

function previewSampleLeaf(valStr) {
  const downloadBtn = document.getElementById("btnDownloadSample");
  const testBtn = document.getElementById("btnTestSample");
  const container = document.getElementById("samplePreviewContainer");
  const imgEl = document.getElementById("samplePreviewImg");
  const titleEl = document.getElementById("samplePreviewTitle");

  if (!valStr) {
    if (downloadBtn) { downloadBtn.classList.add("disabled"); downloadBtn.removeAttribute("href"); }
    if (testBtn) testBtn.disabled = true;
    if (container) container.classList.add("d-none");
    return;
  }

  const item = JSON.parse(valStr);
  if (downloadBtn) {
    downloadBtn.classList.remove("disabled");
    downloadBtn.href = item.download_url;
  }
  if (testBtn) testBtn.disabled = false;
  if (container && imgEl && titleEl) {
    container.classList.remove("d-none");
    imgEl.src = item.view_url;
    titleEl.textContent = `Sample Leaf Preview: ${item.disease_name}`;
  }
}

async function testSelectedSampleLeaf() {
  const select = document.getElementById("sampleLeafSelect");
  if (!select || !select.value) return;
  const item = JSON.parse(select.value);

  if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
    AgriApp.showToast(`Loading sample image for ${item.disease_name}...`, "info");
  }
  try {
    const response = await fetch(item.view_url);
    const blob = await response.blob();
    const file = new File([blob], item.filename, { type: "image/jpeg" });
    handleFileSelected(file);
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast(`Loaded ${item.disease_name} sample image. Click 'Analyze Foliage with AI'!`, "success");
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast(`Failed to load sample image: ${e.message}`, "error");
    }
  }
}

async function initDetectLocation() {}
async function refreshDetectLocation() {}

async function loadUserFields() {
  try {
    const res = await fetch("/api/farms/fields");
    const data = await res.json();
    const select = document.getElementById("fieldSelect");
    if (select && data.fields) {
      data.fields.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = `${f.farm_name ? f.farm_name + ' - ' : ''}${f.name} (${f.crop_variety})`;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.warn("Failed to load user fields:", e);
  }
}

function initUploadZone() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("leafFileInput");
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  if (!file.type.startsWith("image/")) {
    AgriApp.showToast("Please select a valid image file (JPG, PNG, WEBP).", "error");
    return;
  }
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    const previewImg = document.getElementById("leafPreviewImg");
    const previewBox = document.getElementById("previewBox");
    const dropPrompt = document.getElementById("dropPrompt");
    const btnAnalyze = document.getElementById("btnAnalyze");

    if (previewImg) previewImg.src = e.target.result;
    if (previewBox) previewBox.classList.remove("d-none");
    if (dropPrompt) dropPrompt.classList.add("d-none");
    if (btnAnalyze) btnAnalyze.disabled = false;
  };
  reader.readAsDataURL(file);
}

function resetUpload() {
  selectedFile = null;
  lastDiagnosisResult = null;
  const fileInput = document.getElementById("leafFileInput");
  const previewBox = document.getElementById("previewBox");
  const dropPrompt = document.getElementById("dropPrompt");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const resultSection = document.getElementById("resultSection");
  const progressSection = document.getElementById("progressSection");

  if (fileInput) fileInput.value = "";
  if (previewBox) previewBox.classList.add("d-none");
  if (dropPrompt) dropPrompt.classList.remove("d-none");
  if (btnAnalyze) btnAnalyze.disabled = true;
  if (resultSection) resultSection.classList.add("d-none");
  if (progressSection) progressSection.classList.add("d-none");
}

async function startLeafAnalysis() {
  if (!selectedFile) {
    AgriApp.showToast("Please select or capture a leaf photo first.", "warning");
    return;
  }

  const progressSection = document.getElementById("progressSection");
  const resultSection = document.getElementById("resultSection");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const fieldSelect = document.getElementById("fieldSelect");

  if (btnAnalyze) btnAnalyze.disabled = true;
  if (progressSection) progressSection.classList.remove("d-none");
  if (resultSection) resultSection.classList.add("d-none");

  const formData = new FormData();
  formData.append("image", selectedFile);
  if (fieldSelect && fieldSelect.value) {
    formData.append("field_id", fieldSelect.value);
  }


  try {
    const res = await fetch("/api/detect/upload", {
      method: "POST",
      body: formData
    });

    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      if (progressSection) progressSection.classList.add("d-none");
      if (btnAnalyze) btnAnalyze.disabled = false;
      if (res.status === 401) {
        AgriApp.showToast("Session expired. Please log in to run AI leaf diagnosis.", "warning");
        setTimeout(() => { window.location.href = "/login.html"; }, 1200);
        return;
      }
      const text = await res.text();
      console.error("Non-JSON server response:", res.status, text);
      throw new Error(`Server returned status HTTP ${res.status}`);
    }

    const data = await res.json();
    if (progressSection) progressSection.classList.add("d-none");
    if (btnAnalyze) btnAnalyze.disabled = false;

    if (!data.success) {
      if (data.redirect || res.status === 401) {
        AgriApp.showToast(data.message || "Please log in to run leaf diagnosis.", "warning");
        setTimeout(() => { window.location.href = data.redirect || "/login.html"; }, 1200);
        return;
      }
      if (data.error_type === "invalid_image") {
        AgriApp.showToast(data.message || "Invalid Image: Please upload a clear photo of a rice leaf.", "error");
      } else if (data.error_type === "quality_insufficient") {
        AgriApp.showToast(data.message || "Image Quality Insufficient: Image is too blurry or dark.", "warning");
      } else {
        AgriApp.showToast(data.message || "Diagnosis failed.", "error");
      }
      return;
    }

    lastDiagnosisResult = data;
    renderDiagnosticResults(data);
  } catch (e) {
    if (progressSection) progressSection.classList.add("d-none");
    if (btnAnalyze) btnAnalyze.disabled = false;
    AgriApp.showToast("Server error during diagnosis: " + e.toString(), "error");
  }
}

function renderDiagnosticResults(data) {
  const resultSection = document.getElementById("resultSection");
  if (!resultSection) return;

  resultSection.classList.remove("d-none");
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // 1. Condition Name, Pathogen & Pathogen Type
  const dNameEl = document.getElementById("resDiseaseName");
  const dSciEl = document.getElementById("resScientificName");
  const dTypeEl = document.getElementById("resPathogenType");
  const pathogenBlock = document.getElementById("resPathogenBlock");

  if (dNameEl) dNameEl.textContent = data.primary_disease;
  if (dSciEl) dSciEl.textContent = data.scientific_name || "";
  if (dTypeEl) dTypeEl.textContent = data.pathogen_type || "";

  if (data.primary_disease === "Healthy Rice Leaf" && pathogenBlock) {
    pathogenBlock.innerHTML = `<span class="text-success fw-bold"><i class="fas fa-check-circle me-1"></i> Normal Foliage Morphology (No Pathogens Detected)</span>`;
  } else if (pathogenBlock) {
    pathogenBlock.innerHTML = `
      <span class="text-muted">Causal pathogen: </span>
      <b class="text-emerald">${escapeHtml(data.scientific_name)}</b>
      <span class="text-muted ms-2">&bull;</span>
      <span class="text-info ms-2">${escapeHtml(data.pathogen_type)}</span>
    `;
  }

  // 2. Confidence & Confidence Level Badge
  const confVal = parseFloat(data.confidence) || 0;
  const confTextEl = document.getElementById("resConfidenceText");
  const confLevelTextEl = document.getElementById("resConfidenceLevelText");
  const confBarEl = document.getElementById("resConfProgressBar");
  const confBadgeEl = document.getElementById("resConfidenceLevelBadge");

  // Determine qualitative confidence level
  let confTier = "Low";
  let badgeClass = "badge-conf-low";
  let barColorClass = "bg-danger";

  if (confVal >= CONFIDENCE_LEVELS.HIGH) {
    confTier = "HIGH";
    badgeClass = "badge-conf-high";
    barColorClass = "bg-success";
  } else if (confVal >= CONFIDENCE_LEVELS.MODERATE) {
    confTier = "MODERATE";
    badgeClass = "badge-conf-moderate";
    barColorClass = "bg-warning text-dark";
  } else {
    confTier = "LOW";
    badgeClass = "badge-conf-low";
    barColorClass = "bg-danger";
  }

  if (confTextEl) confTextEl.textContent = `${confVal.toFixed(2)}%`;
  if (confLevelTextEl) confLevelTextEl.textContent = confTier;
  if (confBadgeEl) {
    confBadgeEl.textContent = `CONFIDENCE: ${confTier}`;
    confBadgeEl.className = `badge ${badgeClass} fs-6 px-3 py-2 fw-bold`;
  }
  if (confBarEl) {
    confBarEl.style.width = `${confVal}%`;
    confBarEl.className = `progress-bar ${barColorClass}`;
  }

  // 3. Closely Matched Prediction & Uncertain Alerts
  const closelyMatchedBox = document.getElementById("closelyMatchedAlertBox");
  const closelyMatchedText = document.getElementById("closelyMatchedText");
  if (closelyMatchedBox) {
    if (data.is_closely_matched && data.closely_matched_message) {
      closelyMatchedBox.classList.remove("d-none");
      if (closelyMatchedText) {
        closelyMatchedText.innerHTML = `<b>Closely Matched Prediction:</b> ${escapeHtml(data.closely_matched_message)}`;
      }
    } else {
      closelyMatchedBox.classList.add("d-none");
    }
  }

  const uncertainBox = document.getElementById("uncertainAlertBox");
  if (uncertainBox) {
    if (data.is_uncertain) {
      uncertainBox.classList.remove("d-none");
    } else {
      uncertainBox.classList.add("d-none");
    }
  }

  // 4. Severity Badge & Quantitative Lesion Analysis
  const sev = data.severity || {};
  const dSevBadge = document.getElementById("resSeverityBadge");
  if (dSevBadge && sev.severity_level) {
    dSevBadge.textContent = `${sev.severity_level.toUpperCase()} SEVERITY`;
    dSevBadge.className = `badge badge-sev-${sev.severity_level.toLowerCase()}`;
  }

  const hAreaEl = document.getElementById("resHealthyArea");
  const aAreaEl = document.getElementById("resAffectedArea");
  const lCountEl = document.getElementById("resLesionCount");

  if (hAreaEl) hAreaEl.textContent = `${sev.healthy_area_pct}%`;
  if (aAreaEl) aAreaEl.textContent = `${sev.affected_area_pct}%`;
  if (lCountEl) lCountEl.textContent = (sev.lesion_count !== undefined) ? sev.lesion_count : "0";

  // 5. Observed Symptoms (Dynamically generated from image)
  const sympEl = document.getElementById("resSymptoms");
  if (sympEl) {
    sympEl.innerHTML = `
      <p class="mb-0 text-white" style="font-size:0.92rem; line-height:1.6;">
        ${escapeHtml(data.symptoms || "No visible lesions detected.")}
      </p>
    `;
  }

  // 6. Favorable Environmental Conditions & Contributing Factors
  const favEl = document.getElementById("resFavorableConditions");
  const contEl = document.getElementById("resContributingFactors");
  if (favEl) favEl.textContent = data.favorable_conditions || "Standard agronomic growing conditions.";
  if (contEl) contEl.textContent = data.contributing_factors || "Balanced soil fertility and certified seed.";

  // 7. Prevention, Management & Expert Advice
  const prevEl = document.getElementById("resPrevention");
  const mgmtEl = document.getElementById("resManagement");
  const expEl = document.getElementById("resExpertConsultation");

  if (prevEl) prevEl.textContent = data.prevention || "";
  if (mgmtEl) mgmtEl.textContent = data.management || "";
  if (expEl) expEl.textContent = data.expert_consultation || "";

  // 8. Explainable AI (Grad-CAM) 3-Image View
  const origImg = document.getElementById("resOriginalImg");
  const pureHeatmapImg = document.getElementById("resGradcamPureImg");
  const overlayImg = document.getElementById("resGradcamOverlayImg");
  const maskImg = document.getElementById("resMaskImg");

  if (origImg) origImg.src = data.image_url || "";
  if (pureHeatmapImg) pureHeatmapImg.src = data.gradcam_pure_url || data.gradcam_url || "";
  if (overlayImg) overlayImg.src = data.gradcam_overlay_url || data.gradcam_url || "";
  if (maskImg) maskImg.src = data.severity_mask_url || "";

  // 9. Top Predictions Table
  const topTable = document.getElementById("resTopPredictionsTable");
  if (topTable && data.top_predictions) {
    let tbody = "";
    data.top_predictions.forEach((p, idx) => {
      const isTop = (idx === 0);
      const confNum = parseFloat(p.confidence) || 0;
      tbody += `
        <tr>
          <td>
            <span class="badge ${isTop ? 'bg-success' : 'bg-secondary'} me-2">#${idx + 1}</span>
            <b class="text-white">${escapeHtml(p.disease)}</b>
            <small class="text-muted d-block ms-4" style="font-size:0.75rem;">${escapeHtml(p.pathogen_type || '')}</small>
          </td>
          <td class="text-end" style="width:70px;">
            <b class="${isTop ? 'text-emerald' : 'text-muted'}">${confNum.toFixed(2)}%</b>
          </td>
          <td class="text-end" style="width:90px;">
            <div class="progress" style="height: 6px; width: 80px; display: inline-flex; background:rgba(255,255,255,0.1);">
              <div class="progress-bar ${isTop ? 'bg-success' : 'bg-info'}" style="width: ${confNum}%"></div>
            </div>
          </td>
        </tr>
      `;
    });
    topTable.innerHTML = tbody;
  }

  // 10. PDF Export Link
  const pdfBtn = document.getElementById("btnDownloadReport");
  if (pdfBtn && data.report_pdf_url) {
    pdfBtn.href = data.report_pdf_url;
    pdfBtn.classList.remove("d-none");
  }

  // 11. Render Image Upload Location & Weather Outbreak Risk Banner
  renderLocationAndWeatherBanner(data);

  // 12. Render Local Agri Stores Recommendations
  renderStoreProductCategory(data.actual_classified_disease || data.primary_disease, data.nearby_stores);
}

function renderLocationAndWeatherBanner(data) {
  const locBanner = document.getElementById("resLocationBanner");
  const locNameEl = document.getElementById("resLocationName");
  const locSourceBadge = document.getElementById("resLocationSourceBadge");
  const locCoordsEl = document.getElementById("resLocationCoords");
  const weatherTextEl = document.getElementById("resWeatherText");
  const outbreakRiskEl = document.getElementById("resOutbreakRiskText");

  if (!locBanner) return;

  const loc = data.location_info || {};
  const weather = data.weather_risk || {};
  const currWeather = weather.current || {};
  const outbreak = weather.outbreak_risk || {};

  if (loc.location_name) {
    locBanner.classList.remove("d-none");
    if (locNameEl) locNameEl.textContent = loc.location_name;
    if (locSourceBadge) locSourceBadge.textContent = loc.location_source || "Location Analysis";

    if (locCoordsEl && loc.latitude && loc.longitude) {
      locCoordsEl.textContent = `Coordinates: ${loc.latitude.toFixed(4)}° N, ${loc.longitude.toFixed(4)}° E`;
    }

    if (weatherTextEl && currWeather.temp_c) {
      weatherTextEl.textContent = `🌡️ ${currWeather.temp_c}°C | 💧 ${currWeather.humidity}% Humidity | 🌧️ ${currWeather.rainfall_mm} mm Rain`;
    }

    if (outbreakRiskEl && outbreak.risk_level) {
      const riskBadgeColor = outbreak.risk_level === 'High' ? 'text-danger' : (outbreak.risk_level === 'Moderate' ? 'text-warning' : 'text-emerald');
      outbreakRiskEl.innerHTML = `Disease Outbreak Risk: <b class="${riskBadgeColor}">${outbreak.risk_level.toUpperCase()}</b>`;
    }
  }
}

async function renderStoreProductCategory(diseaseName) {
  const catEl = document.getElementById("resProductCategory");
  const aiList = document.getElementById("resActiveIngredientsList");
  const findBtn = document.getElementById("btnFindNearbyStores");
  const previewSection = document.getElementById("nearbyStoresPreviewSection");
  const previewList = document.getElementById("nearbyStoresPreviewList");

  // Get active live location coordinates
  let loc = currentDetectLocation;
  if (!loc && typeof AgriApp !== "undefined" && AgriApp.getLiveLocation) {
    try { loc = await AgriApp.getLiveLocation(false, false); } catch (e) {}
  }

  if (findBtn) {
    findBtn.href = `/stores.html?disease=${encodeURIComponent(diseaseName)}`;
  }

  if (diseaseName === "Healthy Rice Leaf" || diseaseName === "Healthy") {
    if (catEl) catEl.textContent = "Preventive Bio-fertilizers & Micronutrient Amendments (Zinc/Silicon)";
    if (aiList) {
      aiList.innerHTML = `<span class="badge bg-dark border border-secondary text-white p-2" style="font-size:0.8rem;">No chemical intervention required for healthy foliar stand.</span>`;
    }
    if (previewSection) previewSection.classList.add("d-none");
    return;
  }

  try {
    const res = await fetch(`/api/stores/disease-recommendations/${encodeURIComponent(diseaseName)}`);
    const data = await res.json();
    if (data.success && data.recommendations) {
      const rec = data.recommendations;
      if (catEl) catEl.textContent = rec.category_title;

      if (aiList && rec.verified_active_ingredients) {
        let pillsHtml = "";
        rec.verified_active_ingredients.forEach(ai => {
          pillsHtml += `
            <span class="badge bg-dark border border-secondary text-white p-2" style="font-size:0.8rem;text-align:left;">
              <b class="text-emerald">${escapeHtml(ai.name)}</b><br>
              <small class="text-muted">${escapeHtml(ai.mode_of_action || '')}</small><br>
              <small class="text-info"><i class="fas fa-tag me-1"></i>Brands: ${escapeHtml(ai.common_brands || '')} &nbsp;|&nbsp; ⚖️ Dose: ${escapeHtml(ai.label_dosage || '')}</small>
            </span>
          `;
        });
        aiList.innerHTML = pillsHtml;
      }
    }

    // Fetch certified online remedies for this disease
    const prodRes = await fetch(`/api/stores/products?disease=${encodeURIComponent(diseaseName)}`);
    const prodData = await prodRes.json();

    if (prodData.success && prodData.products && prodData.products.length > 0 && previewSection && previewList) {
      previewSection.classList.remove("d-none");
      let prevHtml = `<small class="text-emerald d-block mb-2"><i class="fas fa-shopping-basket me-1"></i> Certified Remedies in Online Agri Store:</small>`;
      
      prodData.products.slice(0, 3).forEach(p => {
        const primaryRetailer = (p.trusted_retailers && p.trusted_retailers.length > 0) ? p.trusted_retailers[0] : null;
        const buyUrl = primaryRetailer ? primaryRetailer.url : `/stores.html?disease=${encodeURIComponent(diseaseName)}`;
        const retailerName = primaryRetailer ? primaryRetailer.platform : 'Online Store';

        prevHtml += `
          <div class="p-2 rounded mb-1" style="background:rgba(255,255,255,0.04);border:1px solid rgba(52,211,153,0.2);font-size:0.85rem;">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-1 mb-1">
              <div>
                <b class="text-white">🌱 ${escapeHtml(p.name)}</b>
                <span class="badge bg-success ms-1" style="font-size:0.72rem;">₹${p.price}</span>
                <span class="badge bg-secondary ms-1" style="font-size:0.7rem;">${escapeHtml(p.brand || '')}</span>
              </div>
              <div>
                <a href="${escapeHtml(buyUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-success py-0 px-2" style="font-size:0.74rem;">
                  <i class="fas fa-cart-shopping me-1"></i>Buy on ${escapeHtml(retailerName)}
                </a>
              </div>
            </div>
            <small class="text-muted d-block" style="font-size:0.75rem;"><i class="fas fa-flask me-1 text-emerald"></i>${escapeHtml(p.active_ingredient || '')} • ${escapeHtml(p.dosage_label || '')}</small>
          </div>
        `;
      });
      previewList.innerHTML = prevHtml;
    }
  } catch (e) {
    console.warn("Could not load disease store recommendations:", e);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function speakDiagnosis() {
  if (!lastDiagnosisResult) return;
  const d = lastDiagnosisResult;
  const text = `Diagnostic assessment: ${d.primary_disease} with ${d.confidence.toFixed(1)} percent confidence, evaluated as ${d.confidence_level} confidence. Estimated visible lesion area is ${d.severity.affected_area_pct} percent. Observed symptoms: ${d.symptoms.substring(0, 180)}.`;
  
  if (AgriVoice.isSpeaking()) {
    AgriVoice.stopSpeaking();
  } else {
    AgriVoice.speakText(text);
  }
}

function openInChat() {
  if (!lastDiagnosisResult) return;
  window.location.href = `/chat.html?disease=${encodeURIComponent(lastDiagnosisResult.actual_classified_disease || lastDiagnosisResult.primary_disease)}`;
}
