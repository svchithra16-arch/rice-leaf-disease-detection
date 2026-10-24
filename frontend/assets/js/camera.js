/**
 * AgriVersion - Live Camera Scanner Script
 */

let videoStream = null;
let currentFacingMode = "environment"; // default to back camera on mobile
let capturedDataUrl = null;

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true);
  startCamera();
});

async function startCamera() {
  const video = document.getElementById("cameraFeed");
  const errorAlert = document.getElementById("cameraErrorAlert");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (errorAlert) {
      errorAlert.textContent = "Camera access is not supported on this device/browser.";
      errorAlert.classList.remove("d-none");
    }
    return;
  }

  stopCamera();

  try {
    const constraints = {
      video: {
        facingMode: currentFacingMode,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    };

    videoStream = await navigator.mediaDevices.getUserMedia(constraints);
    if (video) {
      video.srcObject = videoStream;
      video.play();
    }
    if (errorAlert) errorAlert.classList.add("d-none");
  } catch (err) {
    console.warn("Camera init failed with facingMode, falling back to basic video:", err);
    try {
      videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (video) {
        video.srcObject = videoStream;
        video.play();
      }
      if (errorAlert) errorAlert.classList.add("d-none");
    } catch (e) {
      if (errorAlert) {
        errorAlert.textContent = "Unable to access camera. Please grant camera permissions in your browser.";
        errorAlert.classList.remove("d-none");
      }
    }
  }
}

function stopCamera() {
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }
}

function toggleCameraFacing() {
  currentFacingMode = (currentFacingMode === "environment") ? "user" : "environment";
  startCamera();
}

function captureSnapshot() {
  const video = document.getElementById("cameraFeed");
  const canvas = document.getElementById("snapshotCanvas");
  const capturedImg = document.getElementById("capturedImgPreview");
  const cameraView = document.getElementById("cameraViewContainer");
  const previewView = document.getElementById("capturedPreviewContainer");

  if (!video || !canvas) return;

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  capturedDataUrl = canvas.toDataURL("image/jpeg", 0.92);
  
  if (capturedImg) capturedImg.src = capturedDataUrl;
  if (cameraView) cameraView.classList.add("d-none");
  if (previewView) previewView.classList.remove("d-none");
}

function retakeSnapshot() {
  capturedDataUrl = null;
  const cameraView = document.getElementById("cameraViewContainer");
  const previewView = document.getElementById("capturedPreviewContainer");
  const resultSection = document.getElementById("cameraResultSection");

  if (cameraView) cameraView.classList.remove("d-none");
  if (previewView) previewView.classList.add("d-none");
  if (resultSection) resultSection.classList.add("d-none");

  startCamera();
}

async function analyzeCapturedPhoto() {
  if (!capturedDataUrl) {
    AgriApp.showToast("No snapshot available to analyze.", "warning");
    return;
  }

  const btn = document.getElementById("btnAnalyzeSnap");
  const progress = document.getElementById("cameraProgressSection");
  const resultSection = document.getElementById("cameraResultSection");

  if (btn) btn.disabled = true;
  if (progress) progress.classList.remove("d-none");
  if (resultSection) resultSection.classList.add("d-none");

  try {
    const payload = { image_data: capturedDataUrl };
    try {
      const loc = await AgriApp.getLiveLocation(false, false);
      if (loc && loc.lat && loc.lng) {
        payload.latitude = loc.lat;
        payload.longitude = loc.lng;
        payload.location_name = loc.label;
      }
    } catch (e) {
      console.warn("Camera location skipped:", e);
    }

    const res = await fetch("/api/detect/camera", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const contentType = res.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      if (progress) progress.classList.add("d-none");
      if (btn) btn.disabled = false;
      if (res.status === 401) {
        AgriApp.showToast("Session expired. Please log in to run camera analysis.", "warning");
        setTimeout(() => { window.location.href = "/login.html"; }, 1200);
        return;
      }
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    if (progress) progress.classList.add("d-none");
    if (btn) btn.disabled = false;

    if (!data.success) {
      if (data.redirect || res.status === 401) {
        AgriApp.showToast(data.message || "Please log in to run camera analysis.", "warning");
        setTimeout(() => { window.location.href = data.redirect || "/login.html"; }, 1200);
        return;
      }
      AgriApp.showToast(data.message || "Diagnosis failed.", "error");
      return;
    }

    renderCameraDiagnosis(data);
  } catch (e) {
    if (progress) progress.classList.add("d-none");
    if (btn) btn.disabled = false;
    AgriApp.showToast("Analysis error: " + e.message, "error");
  }
}

function renderCameraDiagnosis(data) {
  const resultSection = document.getElementById("cameraResultSection");
  if (!resultSection) return;

  resultSection.classList.remove("d-none");
  resultSection.scrollIntoView({ behavior: "smooth" });

  document.getElementById("camResDisease").textContent = data.primary_disease;
  
  const confVal = parseFloat(data.confidence) || 0;
  let confTier = "HIGH";
  let confBadgeClass = "bg-success";
  if (confVal < 60.0) {
    confTier = "LOW";
    confBadgeClass = "bg-danger";
  } else if (confVal < 85.0) {
    confTier = "MODERATE";
    confBadgeClass = "bg-warning text-dark";
  }

  const confEl = document.getElementById("camResConf");
  if (confEl) {
    confEl.innerHTML = `${confVal.toFixed(2)}% <span class="badge ${confBadgeClass} ms-1" style="font-size:0.75rem;">${confTier}</span>`;
  }
  
  const badge = document.getElementById("camResSeverity");
  if (badge && data.severity) {
    badge.textContent = `${data.severity.severity_level.toUpperCase()} SEVERITY`;
    badge.className = `badge badge-sev-${data.severity.severity_level.toLowerCase()}`;
  }

  const sympEl = document.getElementById("camResSymptoms");
  if (sympEl) sympEl.textContent = data.symptoms;

  const mgmtEl = document.getElementById("camResManagement");
  if (mgmtEl) mgmtEl.textContent = data.management;

  const gradImg = document.getElementById("camResGradcam");
  if (gradImg) gradImg.src = data.gradcam_overlay_url || data.gradcam_url;

  const pdfBtn = document.getElementById("btnCamPdf");
  if (pdfBtn && data.report_pdf_url) {
    pdfBtn.href = data.report_pdf_url;
    pdfBtn.classList.remove("d-none");
  }
}

window.addEventListener("beforeunload", stopCamera);
