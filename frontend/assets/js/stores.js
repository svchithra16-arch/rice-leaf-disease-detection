/**
 * AgriVersion - Local Agricultural Store & Product Availability Script
 * Features:
 * - Interactive Leaflet Map with Custom Glowing Markers
 * - Smart Multi-Tier Geolocation (Real GPS + Fast IP Location Fallback)
 * - Disease-to-Category Product Matching with Strict Safety Disclaimers
 * - Real-Time Stock Availability (In Stock, Limited, Out of Stock)
 * - Inventory Freshness Auditing (Timestamps & Stale Data Warnings)
 * - Retailer Management Portal (1-Click Stock Status Update)
 * - "Notify Me" Availability Demand Requests & Farmer Reviews
 */

let mapInstance = null;
let markersLayer = null;
let userMarker = null;
let currentStores = [];
let activeStore = null;
let currentCategory = "all";
let currentDisease = "";
let currentCoords = { lat: 13.2936, lng: 77.5342, label: "Doddaballapur, Bengaluru Rural" };
let isGpsActive = false;
let isMobileGpsActive = false;
let mobileAccuracyMeters = null;
let qrCodeInstance = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (typeof AgriApp !== "undefined" && AgriApp.checkAuth) {
    await AgriApp.checkAuth(false);
  }
  initMap();
  await loadCategoriesAndDiseases();
  parseUrlParams();
  
  const searchInputEl = document.getElementById("searchInput");
  if (searchInputEl) {
    searchInputEl.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        applySearch();
      }
    });
  }

  // Auto-detect real-time GPS / Live location on initial load
  autoDetectGpsLocationOnLoad();
});

async function autoDetectGpsLocationOnLoad() {
  await useLaptopLocationExplicitly();
}



// ==============================================================================
// 1. Leaflet Interactive Map Initialization
// ==============================================================================

function initMap() {
  const mapContainer = document.getElementById("storeMap");
  if (!mapContainer || mapInstance) return;

  mapInstance = L.map("storeMap", {
    zoomControl: true,
    attributionControl: false
  }).setView([currentCoords.lat, currentCoords.lng], 11);

  // Modern Dark Theme Tile Layer (CartoDB Dark Matter / OSM)
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    subdomains: "abcd"
  }).addTo(mapInstance);

  markersLayer = L.layerGroup().addTo(mapInstance);
}

let userAccuracyCircle = null;

function renderUserLocationMarker(lat, lng, label = "Your Location", accuracy = null, isMobile = false) {
  if (!mapInstance || !markersLayer) return;

  if (userMarker) {
    markersLayer.removeLayer(userMarker);
  }
  if (userAccuracyCircle) {
    markersLayer.removeLayer(userAccuracyCircle);
  }

  const markerColor = isMobile ? "#10b981" : "#3b82f6";
  const markerPulse = isMobile ? "rgba(16, 185, 129, 0.4)" : "rgba(59, 130, 246, 0.35)";
  const markerIconHtml = isMobile
    ? `<i class="fas fa-mobile-alt" style="color:#fff;font-size:13px;"></i>`
    : `<div style="width:8px;height:8px;background:#fff;border-radius:50%;"></div>`;

  const userIcon = L.divIcon({
    className: "custom-user-marker",
    html: `
      <div style="position:relative;width:34px;height:34px;">
        <div style="position:absolute;width:34px;height:34px;background:${markerPulse};border-radius:50%;animation:pulse 2s infinite;"></div>
        <div style="position:absolute;top:5px;left:5px;width:24px;height:24px;background:${markerColor};border:2px solid #fff;border-radius:50%;box-shadow:0 0 15px ${markerColor};display:flex;align-items:center;justify-content:center;">
          ${markerIconHtml}
        </div>
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });

  const radiusMeters = accuracy ? Math.max(accuracy, 25) : (isMobile ? 50 : (isGpsActive ? 300 : 1500));

  userAccuracyCircle = L.circle([lat, lng], {
    radius: radiusMeters,
    color: markerColor,
    fillColor: markerColor,
    fillOpacity: isMobile ? 0.16 : 0.12,
    weight: 1.5,
    dashArray: isMobile ? '3, 5' : '4, 6'
  }).addTo(markersLayer);

  const badgeText = isMobile
    ? `📱 Live Mobile GPS Locked (±${accuracy ? accuracy.toFixed(1) : '5'}m)`
    : (isGpsActive ? 'Laptop GPS' : 'Live Geolocation Reference');

  userMarker = L.marker([lat, lng], { icon: userIcon, zIndexOffset: 1000 })
    .bindPopup(`
      <div style="min-width:190px;">
        <b style="color:${isMobile ? '#34d399' : '#60a5fa'};font-size:0.95rem;">📍 ${escapeHtml(label)}</b><br>
        <span class="badge ${isMobile ? 'bg-success' : (isGpsActive ? 'bg-info text-dark' : 'bg-primary')} my-1">${badgeText}</span><br>
        <small class="text-muted">Coords: ${lat.toFixed(5)}° N, ${lng.toFixed(5)}° E</small>
      </div>
    `)
    .addTo(markersLayer);
}

function updateMapMarkers(stores) {
  if (!mapInstance || !markersLayer) return;

  // Clear existing store markers (keep userMarker & circle)
  markersLayer.clearLayers();
  if (userAccuracyCircle) {
    userAccuracyCircle.addTo(markersLayer);
  }
  if (userMarker) {
    userMarker.addTo(markersLayer);
  }

  const bounds = L.latLngBounds([[currentCoords.lat, currentCoords.lng]]);

  stores.forEach((s) => {
    let pinColor = "#10b981"; // green
    if (s.relevant_stock_status === "limited_stock") pinColor = "#f59e0b"; // yellow
    else if (s.relevant_stock_status === "out_of_stock") pinColor = "#ef4444"; // red
    else if (s.relevant_stock_status === "unknown") pinColor = "#6b7280"; // gray

    const storeIcon = L.divIcon({
      className: "custom-store-pin",
      html: `
        <div style="background:${pinColor};width:32px;height:32px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.5);cursor:pointer;">
          <i class="fas fa-store" style="transform:rotate(45deg);color:#fff;font-size:12px;"></i>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    });

    const lat = s.latitude;
    const lng = s.longitude;
    bounds.extend([lat, lng]);

    const popupHtml = `
      <div style="min-width:200px;">
        <div class="d-flex align-items-center gap-1 mb-1">
          <b style="color:#fff;font-size:0.95rem;">${escapeHtml(s.store_name)}</b>
          ${s.is_verified ? '<span style="color:#34d399;font-size:0.8rem;">✓</span>' : ''}
        </div>
        <div style="font-size:0.8rem;color:#9ca3af;margin-bottom:6px;">
          📍 ${escapeHtml(s.city)} (${s.distance_text || ''})
        </div>
        <div style="font-size:0.8rem;margin-bottom:8px;">
          <span class="badge ${s.relevant_stock_status === 'in_stock' ? 'bg-success' : 'bg-warning'}">${s.relevant_stock_text || 'In Stock'}</span>
        </div>
        <div class="d-flex gap-1">
          <button class="btn btn-sm btn-success py-0 px-2" style="font-size:0.75rem;" onclick="openStoreDetailsModal(${s.id})">
            View Stock
          </button>
          <a class="btn btn-sm btn-outline-info py-0 px-2" style="font-size:0.75rem;" target="_blank" href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}">
            Directions
          </a>
        </div>
      </div>
    `;

    const marker = L.marker([lat, lng], { icon: storeIcon })
      .bindPopup(popupHtml)
      .addTo(markersLayer);

    marker.on("click", () => {
      highlightStoreCard(s.id);
    });
  });

  if (stores.length > 0) {
    mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }
}

// ==============================================================================
// 2. Data Fetching & Rendering
// ==============================================================================

async function loadCategoriesAndDiseases() {
  try {
    const res = await fetch("/api/stores/categories");
    const data = await res.json();
    if (data.success && data.diseases) {
      const select = document.getElementById("diseaseSelect");
      if (select) {
        data.diseases.forEach(d => {
          const opt = document.createElement("option");
          opt.value = d;
          opt.textContent = `🦠 ${d}`;
          select.appendChild(opt);
        });
      }
    }
  } catch (e) {
    console.warn("Failed to load categories/diseases:", e);
  }
}

function parseUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const diseaseParam = params.get("disease");
  const storeIdParam = params.get("store_id");
  const pincodeParam = params.get("pincode");

  if (diseaseParam) {
    currentDisease = diseaseParam;
    const diseaseSelect = document.getElementById("diseaseSelect");
    if (diseaseSelect) diseaseSelect.value = diseaseParam;

    const banner = document.getElementById("diseaseFilterBanner");
    const bannerName = document.getElementById("bannerDiseaseName");
    if (banner && bannerName) {
      banner.classList.remove("d-none");
      bannerName.textContent = diseaseParam;
    }
  }

  if (pincodeParam) {
    const input = document.getElementById("searchInput");
    if (input) input.value = pincodeParam;
  }

  if (storeIdParam) {
    setTimeout(() => {
      openStoreDetailsModal(parseInt(storeIdParam, 10));
    }, 600);
  }
}

async function fetchAndRenderStores() {
  const container = document.getElementById("storesCardsContainer");
  const countLabel = document.getElementById("resultsCountText");
  if (container) {
    container.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-agri mb-3"></div>
        <p class="text-muted">Searching nearby registered agricultural stores...</p>
      </div>
    `;
  }

  const searchInput = document.getElementById("searchInput")?.value.trim() || "";
  const verifiedOnly = document.getElementById("verifiedOnlySwitch")?.checked || false;
  const inStockOnly = document.getElementById("inStockOnlySwitch")?.checked || false;
  const maxDistance = document.getElementById("distanceRange")?.value || "20";
  const sortBy = document.getElementById("sortBySelect")?.value || "distance";

  const queryParams = new URLSearchParams({
    lat: currentCoords.lat,
    lng: currentCoords.lng,
    is_gps: (isGpsActive || isMobileGpsActive) ? "true" : "false",
    query: searchInput,
    category: currentCategory,
    disease: currentDisease,
    stock_status: inStockOnly ? "in_stock" : "",
    verified_only: verifiedOnly ? "true" : "false",
    max_distance: maxDistance,
    sort_by: sortBy
  });

  try {
    const res = await fetch(`/api/stores?${queryParams.toString()}`);
    const data = await res.json();

    if (!data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Failed to load stores.", "error");
      }
      return;
    }

    currentStores = data.stores || [];
    if (data.search_center) {
      const newLat = data.search_center.lat;
      const newLng = data.search_center.lng;
      const newLabel = data.search_center.label;

      const hasLocationChanged = (currentCoords.lat !== newLat || currentCoords.lng !== newLng);
      currentCoords.lat = newLat;
      currentCoords.lng = newLng;
      currentCoords.label = newLabel;

      const mapLabel = document.getElementById("mapCenterLabel");
      if (mapLabel) mapLabel.textContent = currentCoords.label;
      renderUserLocationMarker(currentCoords.lat, currentCoords.lng, currentCoords.label);

      if (mapInstance && hasLocationChanged) {
        mapInstance.flyTo([currentCoords.lat, currentCoords.lng], 12, { animate: true, duration: 1.2 });
      }
    }

    if (countLabel) {
      const diseaseText = currentDisease ? ` for ${currentDisease}` : "";
      countLabel.textContent = `Showing ${currentStores.length} participating stores${diseaseText} (${currentCoords.label})`;
    }

    renderStoreCards(currentStores);
    updateMapMarkers(currentStores);
  } catch (e) {
    console.error("Store search error:", e);
    if (container) {
      container.innerHTML = `<div class="alert alert-danger">Error loading store records: ${e.toString()}</div>`;
    }
  }
}


function renderStoreCards(stores) {
  const container = document.getElementById("storesCardsContainer");
  if (!container) return;

  if (!stores || stores.length === 0) {
    container.innerHTML = `
      <div class="glass-card text-center p-5">
        <i class="fas fa-store-slash fa-3x text-muted mb-3"></i>
        <h5 class="text-white fw-bold mb-2">No Participating Stores Found</h5>
        <p class="text-muted mb-3" style="font-size:0.9rem;">
          Try expanding your search radius (slider on top), selecting a different town/PIN code, or clearing category filters.
        </p>
        <button class="btn-agri-outline btn-sm me-2" onclick="resetFilters()">
          <i class="fas fa-redo me-1"></i> Reset Filters
        </button>
        <button class="btn-agri-primary btn-sm" onclick="openNotifyModal()">
          <i class="fas fa-bell me-1"></i> Request Stock Alert ("Notify Me")
        </button>
      </div>
    `;
    return;
  }

  let html = "";
  stores.forEach(s => {
    const isFresh = s.is_inventory_fresh;
    const freshClass = isFresh ? "fresh" : "stale";
    const freshIcon = isFresh ? "fa-check-circle" : "fa-exclamation-triangle";
    const freshText = isFresh
      ? `🟢 Stock updated ${s.inventory_freshness_text}`
      : `⚠️ Availability not recently checked (${s.inventory_freshness_text})`;

    let stockBadgeClass = "stock-badge-in_stock";
    let stockBadgeText = "🟢 In Stock Reported";
    if (s.relevant_stock_status === "limited_stock") {
      stockBadgeClass = "stock-badge-limited_stock";
      stockBadgeText = "🟡 Limited Stock";
    } else if (s.relevant_stock_status === "out_of_stock") {
      stockBadgeClass = "stock-badge-out_of_stock";
      stockBadgeText = "🔴 Out of Stock";
    } else if (s.relevant_stock_status === "unknown") {
      stockBadgeClass = "stock-badge-unknown";
      stockBadgeText = "⚪ Availability Unknown";
    }

    // Products chips preview
    let prodsHtml = "";
    const prods = s.relevant_products || s.products || [];
    if (prods.length > 0) {
      prods.slice(0, 3).forEach(p => {
        const isPInStock = (p.stock_status === "in_stock");
        prodsHtml += `
          <span class="product-pill">
            <i class="fas ${isPInStock ? 'fa-check text-success' : 'fa-info-circle text-warning'}" style="font-size:10px;"></i>
            <b>${escapeHtml(p.product_name)}</b>
          </span>
        `;
      });
      if (prods.length > 3) {
        prodsHtml += `<span class="badge bg-secondary" style="font-size:0.75rem;">+${prods.length - 3} more</span>`;
      }
    }

    const cleanPhone = s.phone ? s.phone.replace(/[^0-9+]/g, "") : "";
    const cleanWhatsapp = s.whatsapp ? s.whatsapp.replace(/[^0-9+]/g, "") : cleanPhone;
    const dirUrl = `https://www.google.com/maps/dir/?api=1&destination=${s.latitude},${s.longitude}`;

    html += `
      <div class="store-card" id="storeCard_${s.id}">
        <div class="d-flex flex-wrap justify-content-between align-items-start mb-2 gap-2">
          <div>
            <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
              <h5 class="text-white fw-bold mb-0">${escapeHtml(s.store_name)}</h5>
              ${s.is_verified ? '<span class="verified-badge">✓ Verified Agri Store</span>' : '<span class="badge bg-secondary">Registered</span>'}
            </div>
            <div class="text-muted" style="font-size:0.85rem;">
              <i class="fas fa-map-marker-alt text-emerald me-1"></i> ${escapeHtml(s.address)}, ${escapeHtml(s.city)}
            </div>
          </div>
          <div class="text-end">
            <span class="badge bg-dark border border-secondary text-emerald mb-1 d-block" style="font-size:0.82rem;">
              <i class="fas fa-route me-1"></i> ${s.distance_text || ''}
            </span>
            <span class="badge ${stockBadgeClass}" style="font-size:0.78rem;">
              ${stockBadgeText}
            </span>
          </div>
        </div>

        <!-- In-Stock Products Chips Preview -->
        ${prodsHtml ? `<div class="d-flex flex-wrap gap-1 align-items-center mb-3 mt-2">${prodsHtml}</div>` : ''}

        <!-- Freshness Tag & Hours -->
        <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 pt-2 border-top" style="border-color:rgba(255,255,255,0.06) !important;font-size:0.8rem;">
          <span class="freshness-tag ${freshClass}">
            <i class="fas ${freshIcon} me-1"></i> ${freshText}
          </span>
          <span class="text-muted">
            <i class="far fa-clock text-info me-1"></i> ${escapeHtml(s.opening_hours || '08:00 AM - 08:00 PM')}
          </span>
        </div>

        <!-- Action Buttons -->
        <div class="d-flex flex-wrap gap-2">
          ${cleanPhone ? `<a href="tel:${cleanPhone}" class="btn btn-sm btn-agri-primary"><i class="fas fa-phone-alt me-1"></i> Call</a>` : ''}
          ${cleanWhatsapp ? `<a href="https://wa.me/${cleanWhatsapp.replace('+', '')}" target="_blank" class="btn btn-sm btn-outline-success text-white"><i class="fab fa-whatsapp text-success me-1"></i> WhatsApp</a>` : ''}
          <a href="${dirUrl}" target="_blank" class="btn btn-sm btn-agri-outline"><i class="fas fa-directions text-info me-1"></i> Directions</a>
          <button class="btn btn-sm btn-outline-light ms-auto" onclick="openStoreDetailsModal(${s.id})">
            <i class="fas fa-boxes me-1"></i> View Full Inventory (${s.total_products || 0})
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function highlightStoreCard(storeId) {
  document.querySelectorAll(".store-card").forEach(c => c.classList.remove("highlighted"));
  const card = document.getElementById(`storeCard_${storeId}`);
  if (card) {
    card.classList.add("highlighted");
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// ==============================================================================
// 3. Store Profile & Inventory Modal
// ==============================================================================

async function openStoreDetailsModal(storeId) {
  try {
    const res = await fetch(`/api/stores/${storeId}`);
    const data = await res.json();
    if (!data.success || !data.store) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Store not found.", "error");
      }
      return;
    }

    activeStore = data.store;
    const s = activeStore;

    document.getElementById("modalStoreName").textContent = s.store_name;
    document.getElementById("modalStoreAddress").textContent = `${s.address}, ${s.city}, ${s.state} - PIN ${s.pincode}`;
    document.getElementById("modalStorePhone").textContent = s.phone || "Not Published";
    document.getElementById("modalStoreHours").textContent = s.opening_hours || "08:00 AM - 08:00 PM";
    document.getElementById("modalStoreRating").textContent = `★ ${s.rating} (${s.reviews_count || 0} Reviews)`;
    document.getElementById("modalStoreLicense").textContent = s.license_number || "Verified Commercial Retailer";

    const verifiedBadge = document.getElementById("modalStoreVerified");
    if (verifiedBadge) {
      verifiedBadge.style.display = s.is_verified ? "inline-flex" : "none";
    }

    const cleanPhone = s.phone ? s.phone.replace(/[^0-9+]/g, "") : "";
    const cleanWhatsapp = s.whatsapp ? s.whatsapp.replace(/[^0-9+]/g, "") : cleanPhone;
    const dirUrl = `https://www.google.com/maps/dir/?api=1&destination=${s.latitude},${s.longitude}`;

    const btnCall = document.getElementById("modalBtnCall");
    const btnWhatsapp = document.getElementById("modalBtnWhatsapp");
    const btnDir = document.getElementById("modalBtnDirections");

    if (btnCall) btnCall.href = `tel:${cleanPhone}`;
    if (btnWhatsapp) btnWhatsapp.href = `https://wa.me/${cleanWhatsapp.replace('+', '')}`;
    if (btnDir) btnDir.href = dirUrl;

    renderModalInventoryTable(s.products || []);
    renderModalReviewsList(s.reviews || []);

    const modalEl = document.getElementById("storeDetailsModal");
    if (modalEl) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  } catch (e) {
    console.error("Failed to open store modal:", e);
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Could not load store details.", "error");
    }
  }
}


function renderModalInventoryTable(products) {
  const tbody = document.getElementById("modalInventoryTableBody");
  if (!tbody) return;

  if (!products || products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No products listed in this store's inventory yet.</td></tr>`;
    return;
  }

  let html = "";
  products.forEach(p => {
    let stockBadgeClass = "bg-success text-white";
    let stockLabel = "🟢 In Stock";
    if (p.stock_status === "limited_stock") {
      stockBadgeClass = "bg-warning text-dark";
      stockLabel = "🟡 Limited Stock";
    } else if (p.stock_status === "out_of_stock") {
      stockBadgeClass = "bg-danger text-white";
      stockLabel = "🔴 Out of Stock";
    } else if (p.stock_status === "unknown") {
      stockBadgeClass = "bg-secondary text-white";
      stockLabel = "⚪ Unknown";
    }

    const priceText = p.price ? `₹${p.price.toFixed(2)}` : `<span class="text-muted">Inquire Store</span>`;
    const updatedRelative = p.last_updated_relative || "Recently";

    html += `
      <tr>
        <td>
          <b class="text-white">${escapeHtml(p.product_name)}</b><br>
          <small class="text-muted">${escapeHtml(p.manufacturer || '')}</small>
        </td>
        <td>
          <span class="badge bg-dark border border-secondary text-emerald mb-1">${escapeHtml(p.category)}</span><br>
          <small class="text-muted" style="font-size:0.8rem;">${escapeHtml(p.active_ingredient)}</small>
        </td>
        <td><b>${escapeHtml(p.pack_size)}</b></td>
        <td><b class="text-emerald">${priceText}</b></td>
        <td><span class="badge ${stockBadgeClass}" style="font-size:0.8rem;">${stockLabel}</span></td>
        <td>
          <small class="${p.is_fresh ? 'text-success' : 'text-warning'}">
            <i class="fas ${p.is_fresh ? 'fa-check-circle' : 'fa-clock'} me-1"></i> ${updatedRelative}
          </small>
        </td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function filterModalInventory(query) {
  if (!activeStore || !activeStore.products) return;
  const q = query.toLowerCase().trim();
  if (!q) {
    renderModalInventoryTable(activeStore.products);
    return;
  }

  const filtered = activeStore.products.filter(p =>
    p.product_name.toLowerCase().includes(q) ||
    p.active_ingredient.toLowerCase().includes(q) ||
    p.category.toLowerCase().includes(q) ||
    p.manufacturer.toLowerCase().includes(q)
  );
  renderModalInventoryTable(filtered);
}

function renderModalReviewsList(reviews) {
  const container = document.getElementById("modalReviewsList");
  if (!container) return;

  if (!reviews || reviews.length === 0) {
    container.innerHTML = `<p class="text-muted mb-0" style="font-size:0.85rem;">No reviews yet. Be the first farmer to leave feedback!</p>`;
    return;
  }

  let html = "";
  reviews.forEach(r => {
    const stars = "★".repeat(r.rating) + "☆".repeat(5 - r.rating);
    html += `
      <div class="p-2 rounded" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);font-size:0.88rem;">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <b class="text-white">${escapeHtml(r.user_name || 'Local Farmer')}</b>
          <span class="text-warning">${stars}</span>
        </div>
        <p class="text-muted mb-0" style="font-size:0.83rem;">${escapeHtml(r.comment)}</p>
      </div>
    `;
  });
  container.innerHTML = html;
}

async function submitStoreReview() {
  if (!activeStore) return;

  const author = document.getElementById("reviewAuthorInput")?.value.trim() || "Local Farmer";
  const rating = document.getElementById("reviewRatingSelect")?.value || "5";
  const comment = document.getElementById("reviewCommentInput")?.value.trim() || "";

  if (!comment) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Please write a brief comment regarding your experience.", "warning");
    }
    return;
  }

  try {
    const res = await fetch(`/api/stores/${activeStore.id}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: author,
        rating: parseInt(rating, 10),
        comment: comment
      })
    });

    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message, "success");
      }
      document.getElementById("reviewCommentInput").value = "";
      // Refresh modal
      openStoreDetailsModal(activeStore.id);
    } else {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message || "Failed to submit review.", "error");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Server error submitting review.", "error");
    }
  }
}

function openReviewSection() {
  const section = document.getElementById("modalReviewsSection");
  if (section) {
    section.scrollIntoView({ behavior: "smooth" });
    document.getElementById("reviewCommentInput")?.focus();
  }
}

// ==============================================================================
// 4. "Notify Me" Availability Alert
// ==============================================================================

function openNotifyModal() {
  const user = (typeof AgriApp !== "undefined" && AgriApp.getUser) ? AgriApp.getUser() : null;
  if (user) {
    const nameInput = document.getElementById("notifyUserName");
    const phoneInput = document.getElementById("notifyUserPhone");
    if (nameInput) nameInput.value = user.full_name || "";
    if (phoneInput) phoneInput.value = user.phone || "";
  }

  const modalEl = document.getElementById("notifyMeModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}


async function submitStockNotificationRequest() {
  const category = document.getElementById("notifyCategorySelect")?.value;
  const prodName = document.getElementById("notifyProductName")?.value.trim() || "";
  const name = document.getElementById("notifyUserName")?.value.trim() || "";
  const phone = document.getElementById("notifyUserPhone")?.value.trim() || "";

  if (!phone) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Please provide your mobile/WhatsApp number for SMS/notification alerts.", "warning");
    }
    return;
  }

  try {
    const res = await fetch("/api/stores/request-availability", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_category: category,
        product_name: prodName,
        disease_name: currentDisease,
        user_name: name,
        user_phone: phone,
        location: currentCoords.label
      })
    });

    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message, "success");
      }
      const modalEl = document.getElementById("notifyMeModal");
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }
    } else {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message || "Failed to register alert.", "error");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Error registering notification request.", "error");
    }
  }
}

// ==============================================================================
// 5. Retailer Portal (Registration & Live Inventory Management)
// ==============================================================================

async function openRetailerPortal() {
  await loadRetailerStores();
  const modalEl = document.getElementById("retailerPortalModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}


async function loadRetailerStores() {
  const select = document.getElementById("retailerStoreSelect");
  if (!select) return;

  try {
    const res = await fetch("/api/stores/my-stores");
    const data = await res.json();
    select.innerHTML = "";

    if (data.success && data.stores && data.stores.length > 0) {
      data.stores.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.store_name} (${s.city})`;
        select.appendChild(opt);
      });
      loadRetailerInventory(data.stores[0].id);
    } else {
      // Fallback: Show all registered stores for demonstration
      currentStores.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.store_name} (${s.city})`;
        select.appendChild(opt);
      });
      if (currentStores.length > 0) {
        loadRetailerInventory(currentStores[0].id);
      }
    }
  } catch (e) {
    console.warn("Could not load retailer stores:", e);
  }
}

async function loadRetailerInventory(storeId) {
  const tbody = document.getElementById("retailerInventoryTableBody");
  if (!tbody || !storeId) return;

  tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">Loading store inventory...</td></tr>`;

  try {
    const res = await fetch(`/api/stores/${storeId}`);
    const data = await res.json();

    if (!data.success || !data.store) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Failed to load inventory.</td></tr>`;
      return;
    }

    const prods = data.store.products || [];
    if (prods.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No products added. Use the accordion above to add products.</td></tr>`;
      return;
    }

    let html = "";
    prods.forEach(p => {
      html += `
        <tr>
          <td>
            <b class="text-white">${escapeHtml(p.product_name)}</b><br>
            <small class="text-muted">${escapeHtml(p.active_ingredient)} (${p.pack_size})</small>
          </td>
          <td><span class="badge bg-secondary">${escapeHtml(p.category)}</span></td>
          <td>
            <input type="number" class="form-control form-control-sm form-control-agri" style="width:90px;" value="${p.price || ''}" placeholder="Price" onchange="quickUpdateProductPrice(${storeId}, ${p.id}, this.value)">
          </td>
          <td>
            <select class="form-select form-select-sm form-control-agri" onchange="quickUpdateProductStock(${storeId}, ${p.id}, this.value)">
              <option value="in_stock" ${p.stock_status === 'in_stock' ? 'selected' : ''}>🟢 In Stock</option>
              <option value="limited_stock" ${p.stock_status === 'limited_stock' ? 'selected' : ''}>🟡 Limited Stock</option>
              <option value="out_of_stock" ${p.stock_status === 'out_of_stock' ? 'selected' : ''}>🔴 Out of Stock</option>
            </select>
          </td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-danger" onclick="deleteProductFromStore(${storeId}, ${p.id})">
              <i class="fas fa-trash-alt"></i>
            </button>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  } catch (e) {
    console.error("Retailer inventory load error:", e);
  }
}

async function quickUpdateProductStock(storeId, prodId, newStock) {
  try {
    const res = await fetch(`/api/stores/${storeId}/products/${prodId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stock_status: newStock })
    });
    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(`Stock updated to ${newStock.toUpperCase()}! Freshness timestamp renewed.`, "success");
      }
      fetchAndRenderStores();
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Failed to update stock status.", "error");
    }
  }
}

async function quickUpdateProductPrice(storeId, prodId, newPrice) {
  try {
    const res = await fetch(`/api/stores/${storeId}/products/${prodId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ price: parseFloat(newPrice) })
    });
    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Product price updated successfully.", "success");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Failed to update price.", "error");
    }
  }
}

async function submitNewProduct() {
  const storeId = document.getElementById("retailerStoreSelect")?.value;
  const name = document.getElementById("newProdName")?.value.trim();
  const category = document.getElementById("newProdCategory")?.value;
  const ingredient = document.getElementById("newProdIngredient")?.value.trim();
  const mfr = document.getElementById("newProdMfr")?.value.trim() || "Agricultural Inputs";
  const pack = document.getElementById("newProdPack")?.value.trim() || "500 g";
  const price = document.getElementById("newProdPrice")?.value;
  const stock = document.getElementById("newProdStock")?.value || "in_stock";

  if (!storeId || !name || !ingredient) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Please fill in Product Name and Active Ingredient.", "warning");
    }
    return;
  }

  try {
    const res = await fetch(`/api/stores/${storeId}/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_name: name,
        category: category,
        active_ingredient: ingredient,
        manufacturer: mfr,
        pack_size: pack,
        price: price ? parseFloat(price) : null,
        stock_status: stock
      })
    });

    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message, "success");
      }
      document.getElementById("newProdName").value = "";
      document.getElementById("newProdIngredient").value = "";
      document.getElementById("newProdPrice").value = "";
      loadRetailerInventory(storeId);
      fetchAndRenderStores();
    } else {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message || "Failed to add product.", "error");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Error adding product.", "error");
    }
  }
}

async function deleteProductFromStore(storeId, prodId) {
  if (!confirm("Are you sure you want to remove this product from store inventory?")) return;

  try {
    const res = await fetch(`/api/stores/${storeId}/products/${prodId}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Product deleted.", "info");
      }
      loadRetailerInventory(storeId);
      fetchAndRenderStores();
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Error removing product.", "error");
    }
  }
}

async function submitStoreRegistration() {
  const storeName = document.getElementById("regStoreName")?.value.trim();
  const ownerName = document.getElementById("regOwnerName")?.value.trim();
  const phone = document.getElementById("regPhone")?.value.trim();
  const whatsapp = document.getElementById("regWhatsapp")?.value.trim();
  const address = document.getElementById("regAddress")?.value.trim();
  const city = document.getElementById("regCity")?.value.trim();
  const district = document.getElementById("regDistrict")?.value.trim();
  const pincode = document.getElementById("regPincode")?.value.trim();
  const hours = document.getElementById("regHours")?.value.trim() || "08:00 AM - 08:00 PM (Mon-Sat)";
  const license = document.getElementById("regLicense")?.value.trim();

  if (!storeName || !phone || !address || !city || !pincode) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Please fill in all mandatory store registration fields.", "warning");
    }
    return;
  }

  try {
    const res = await fetch("/api/stores/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_name: storeName,
        owner_name: ownerName,
        phone: phone,
        whatsapp: whatsapp,
        address: address,
        city: city,
        district: district,
        pincode: pincode,
        opening_hours: hours,
        license_number: license,
        latitude: currentCoords.lat + (Math.random() * 0.01 - 0.005),
        longitude: currentCoords.lng + (Math.random() * 0.01 - 0.005)
      })
    });

    const data = await res.json();
    if (data.success) {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message, "success");
      }
      const modalEl = document.getElementById("retailerPortalModal");
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }
      fetchAndRenderStores();
    } else {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(data.message || "Registration failed.", "error");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Error registering store.", "error");
    }
  }
}

// ==============================================================================
// 6. Real-Time Mobile GPS Location Synchronization & Filter Events
// ==============================================================================

async function reverseGeocodeCoords(lat, lng) {
  if (typeof AgriApp !== "undefined" && AgriApp.reverseGeocode) {
    return await AgriApp.reverseGeocode(lat, lng);
  }
  return null;
}

/**
 * Initializes location on page load.
 * Prioritizes Laptop Geolocation and auto-detects laptop coordinates.
 */
async function autoDetectGpsLocationOnLoad() {
  const citySelect = document.getElementById("cityPresetSelect");
  if (citySelect) citySelect.value = "laptop_gps";

  // Automatically detect and lock onto laptop location
  await useLaptopLocationExplicitly();
}

/**
 * Handles incoming real-time events from the mobile GPS stream.
 */
function handleMobileGpsEvent(event) {
  const state = event.state;

  if (state.status === "connected" && state.lat !== null && state.lng !== null) {
    updateMobileStatusUI("connected", "📱 Mobile Location Connected", `Lat: ${state.lat.toFixed(5)}, Lng: ${state.lng.toFixed(5)} • ${state.label || 'Live GPS'}`);
    applyMobileLocationData(state);
  } else if (state.status === "waiting") {
    updateMobileStatusUI("waiting", "⏳ Waiting for Mobile Connection", "Scan QR code on your phone to transmit live GPS");
  } else if (state.status === "disconnected") {
    updateMobileStatusUI("disconnected", "⚠️ Mobile Location Disconnected", "Mobile GPS broadcast was paused or disconnected");
  } else if (state.status === "denied") {
    updateMobileStatusUI("denied", "❌ Mobile GPS Permission Denied", "Location permission was denied on the mobile browser");
  }

  // Update modal indicators if open
  updateModalGpsDashboard(state);
}

/**
 * Applies received mobile GPS coordinates to the application:
 * - Updates coordinates state
 * - Centers and updates Leaflet map marker & accuracy ring
 * - Updates search center label
 * - Re-queries nearby stores with exact mobile coordinates
 */
function applyMobileLocationData(state) {
  if (!state.lat || !state.lng) return;

  isMobileGpsActive = true;
  isGpsActive = true;
  mobileAccuracyMeters = state.accuracy || null;

  const prevLat = currentCoords.lat;
  const prevLng = currentCoords.lng;
  const hasMoved = (Math.abs(prevLat - state.lat) > 0.0001 || Math.abs(prevLng - state.lng) > 0.0001);

  currentCoords.lat = state.lat;
  currentCoords.lng = state.lng;
  currentCoords.label = state.label || `📍 ${state.lat.toFixed(4)}° N, ${state.lng.toFixed(4)}° E`;

  // Update Map Center Label
  const mapLabel = document.getElementById("mapCenterLabel");
  if (mapLabel) {
    const accText = state.accuracy ? ` (±${state.accuracy.toFixed(1)}m)` : "";
    mapLabel.innerHTML = `📱 <b>${escapeHtml(state.city || 'Live Mobile')}</b>, ${escapeHtml(state.state || '')} <span class="badge bg-success" style="font-size:0.7rem;">Mobile GPS${accText}</span>`;
  }

  // Update dropdown selection
  const citySelect = document.getElementById("cityPresetSelect");
  if (citySelect) citySelect.value = "mobile_gps";

  // Re-render mobile user marker with glowing emerald style
  renderUserLocationMarker(currentCoords.lat, currentCoords.lng, currentCoords.label, mobileAccuracyMeters, true);

  // Pan map smoothly to follow mobile
  if (mapInstance && hasMoved) {
    mapInstance.flyTo([currentCoords.lat, currentCoords.lng], 13, { animate: true, duration: 1.0 });
  }

  // Automatically refresh nearby stores & calculate exact distances
  fetchAndRenderStores();
}

/**
 * Updates status badges, live banner, and button labels across the UI.
 */
function updateMobileStatusUI(status, title, subtitle) {
  const banner = document.getElementById("mobileGpsLiveBanner");
  const bannerTitle = document.getElementById("mobileBannerTitle");
  const bannerSubtitle = document.getElementById("mobileBannerSubtitle");
  const bannerCoords = document.getElementById("bannerCoordsText");
  const bannerBadge = document.getElementById("mobileBannerBadge");
  const bannerPulse = document.getElementById("mobileBannerPulse");
  const headerDot = document.getElementById("headerMobileStatusDot");
  const mobileBtnText = document.getElementById("mobileGpsBtnText");
  const mobileBtn = document.getElementById("mobileGpsBtn");

  if (status === "connected") {
    if (banner) banner.classList.remove("d-none");
    if (bannerTitle) bannerTitle.textContent = title;
    if (bannerSubtitle) bannerSubtitle.textContent = subtitle;
    if (bannerBadge) {
      bannerBadge.className = "badge bg-success";
      bannerBadge.textContent = "Live GPS Active";
    }
    if (bannerPulse) bannerPulse.className = "spinner-grow spinner-grow-sm text-success";
    if (headerDot) {
      headerDot.className = "badge rounded-pill bg-success";
      headerDot.textContent = "📱 Connected";
    }
    if (mobileBtn) {
      mobileBtn.className = "btn btn-success text-white";
    }
    if (mobileBtnText) mobileBtnText.textContent = "Mobile GPS (Live)";
  } else if (status === "waiting") {
    if (banner) banner.classList.remove("d-none");
    if (bannerTitle) bannerTitle.textContent = title;
    if (bannerSubtitle) bannerSubtitle.textContent = subtitle;
    if (bannerBadge) {
      bannerBadge.className = "badge bg-warning text-dark";
      bannerBadge.textContent = "Waiting for Phone";
    }
    if (bannerPulse) bannerPulse.className = "spinner-grow spinner-grow-sm text-warning";
    if (headerDot) {
      headerDot.className = "badge rounded-pill bg-warning text-dark";
      headerDot.textContent = "⏳ Waiting";
    }
    if (mobileBtn) {
      mobileBtn.className = "btn btn-outline-info text-white";
    }
    if (mobileBtnText) mobileBtnText.textContent = "Connect Mobile";
  } else if (status === "disconnected") {
    if (banner) banner.classList.remove("d-none");
    if (bannerTitle) bannerTitle.textContent = title;
    if (bannerSubtitle) bannerSubtitle.textContent = subtitle;
    if (bannerBadge) {
      bannerBadge.className = "badge bg-danger";
      bannerBadge.textContent = "Disconnected";
    }
    if (bannerPulse) bannerPulse.className = "spinner-grow spinner-grow-sm text-danger";
    if (headerDot) {
      headerDot.className = "badge rounded-pill bg-danger";
      headerDot.textContent = "⚠️ Disconnected";
    }
  } else if (status === "denied") {
    if (banner) banner.classList.remove("d-none");
    if (bannerTitle) bannerTitle.textContent = title;
    if (bannerSubtitle) bannerSubtitle.textContent = subtitle;
    if (bannerBadge) {
      bannerBadge.className = "badge bg-danger";
      bannerBadge.textContent = "Permission Blocked";
    }
    if (headerDot) {
      headerDot.className = "badge rounded-pill bg-danger";
      headerDot.textContent = "❌ Blocked";
    }
  }
}

/**
 * Updates elements inside the Mobile GPS Connection Modal.
 */
function updateModalGpsDashboard(state) {
  const badge = document.getElementById("modalMobileStatusBadge");
  const headline = document.getElementById("modalMobileStatusHeadline");
  const message = document.getElementById("modalMobileStatusMessage");
  const latEl = document.getElementById("modalMobileLat");
  const lngEl = document.getElementById("modalMobileLng");
  const accEl = document.getElementById("modalMobileAccuracy");
  const locEl = document.getElementById("modalMobileLocality");
  const lastSeen = document.getElementById("modalMobileLastSeenBadge");

  if (state.lat && state.lng) {
    if (latEl) latEl.textContent = state.lat.toFixed(5);
    if (lngEl) lngEl.textContent = state.lng.toFixed(5);
    if (accEl) accEl.textContent = state.accuracy ? `±${state.accuracy.toFixed(1)} m` : "High";
    if (locEl) locEl.textContent = state.city || state.label || "GPS Locked";
    if (lastSeen) lastSeen.textContent = `Live pings: ${state.updatesCount || 0} (${state.lastSeenSecondsAgo || 0}s ago)`;
  }

  if (state.status === "connected") {
    if (badge) {
      badge.className = "badge bg-success px-2 py-1";
      badge.innerHTML = '<i class="fas fa-check-circle me-1"></i> Mobile Connected';
    }
    if (headline) headline.textContent = "📱 Mobile GPS Live & Synchronized!";
    if (message) message.textContent = "AgriVersion is actively using your mobile phone's real-time satellite coordinates for all calculations.";
  } else if (state.status === "denied") {
    if (badge) {
      badge.className = "badge bg-danger px-2 py-1";
      badge.innerHTML = '<i class="fas fa-lock me-1"></i> Permission Denied';
    }
    if (headline) headline.textContent = "❌ Location Blocked on Mobile";
    if (message) message.textContent = "Please tap the lock/settings icon on your phone browser and change Location to 'Allow'.";
  } else if (state.status === "disconnected") {
    if (badge) {
      badge.className = "badge bg-danger px-2 py-1";
      badge.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Disconnected';
    }
    if (headline) headline.textContent = "⚠️ Mobile Signal Disconnected";
    if (message) message.textContent = "Reopen the connection page on your phone or re-scan the QR code.";
  }
}

/**
 * Opens the Mobile GPS connection modal and generates a unique QR code.
 */
async function openMobileGpsModal() {
  const modalEl = document.getElementById("mobileGpsModal");
  if (!modalEl) return;

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();

  // Initialize or retrieve existing session
  const sessionData = await AgriApp.mobileGps.initSession(false);
  if (sessionData && sessionData.mobile_url) {
    const url = sessionData.mobile_url;
    const urlInput = document.getElementById("mobileDirectUrlInput");
    const openLink = document.getElementById("mobileDirectUrlOpenLink");

    if (urlInput) urlInput.value = url;
    if (openLink) openLink.href = url;

    // Render QR Code
    const qrBox = document.getElementById("modalQrCodeBox");
    if (qrBox) {
      qrBox.innerHTML = "";
      try {
        qrCodeInstance = new QRCode(qrBox, {
          text: url,
          width: 180,
          height: 180,
          colorDark: "#022c22",
          colorLight: "#ffffff",
          correctLevel: QRCode.CorrectLevel.M
        });
      } catch (e) {
        console.warn("QR Code generator fallback:", e);
        qrBox.innerHTML = `<a href="${url}" target="_blank" class="btn btn-sm btn-primary">Open Mobile GPS Link</a>`;
      }
    }

    // Start active polling
    AgriApp.mobileGps.startPolling(1500);

    // Initial state refresh
    updateModalGpsDashboard(AgriApp.mobileGps.getState());
  }
}

/**
 * Copies the mobile connection URL to clipboard.
 */
function copyMobileUrl() {
  const urlInput = document.getElementById("mobileDirectUrlInput");
  if (urlInput && urlInput.value) {
    navigator.clipboard.writeText(urlInput.value).then(() => {
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Mobile GPS connection link copied to clipboard!", "success");
      }
    }).catch(() => {
      urlInput.select();
      document.execCommand("copy");
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast("Link copied!", "success");
      }
    });
  }
}

/**
 * Explicitly applies current mobile location.
 */
function applyMobileLocationNow() {
  AgriApp.mobileGps.setSourcePreference("mobile");
  const state = AgriApp.mobileGps.getState();
  if (state.lat && state.lng) {
    applyMobileLocationData(state);
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Mobile GPS applied as primary location!", "success");
    }
  } else {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Waiting for mobile to transmit coordinates. Scan the QR code with your phone!", "info");
    }
  }
  const modalEl = document.getElementById("mobileGpsModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }
}

/**
 * Disconnects the mobile GPS broadcast and resets state.
 */
async function disconnectMobileGps() {
  if (typeof AgriApp !== "undefined" && AgriApp.mobileGps) {
    await AgriApp.mobileGps.disconnect();
  }
  isMobileGpsActive = false;
  updateMobileStatusUI("disconnected", "⚠️ Mobile Location Disconnected", "Mobile GPS was manually disconnected");
  
  if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
    AgriApp.showToast("Mobile GPS disconnected.", "info");
  }
}

/**
 * Explicit fallback to Laptop IP / Browser Geolocation.
 * ONLY triggered when user deliberately chooses this option.
 */
async function useLaptopLocationExplicitly() {
  isMobileGpsActive = false;
  if (typeof AgriApp !== "undefined" && AgriApp.mobileGps) {
    AgriApp.mobileGps.setSourcePreference("laptop");
  }

  const mapLabel = document.getElementById("mapCenterLabel");
  if (mapLabel) {
    mapLabel.innerHTML = `📍 <b>Finding your live location...</b> <span class="badge bg-warning text-dark" style="font-size:0.7rem;">Locating...</span>`;
  }

  try {
    const loc = await AgriApp.getLiveLocation(true, false);
    if (loc && Number.isFinite(loc.lat) && Number.isFinite(loc.lng) && loc.isGps) {
      document.getElementById("locationPermissionNotice")?.classList.add("d-none");
      isGpsActive = true;
      currentCoords.lat = loc.lat;
      currentCoords.lng = loc.lng;
      currentCoords.label = `📍 ${loc.label}`;

      if (mapLabel) mapLabel.innerHTML = `💻 <b>${escapeHtml(loc.city)}</b>, ${escapeHtml(loc.state)} <span class="badge bg-success" style="font-size:0.7rem;">Laptop Location</span>`;

      const citySelect = document.getElementById("cityPresetSelect");
      if (citySelect) citySelect.value = "laptop_gps";

      renderUserLocationMarker(currentCoords.lat, currentCoords.lng, currentCoords.label, null, false);
      if (mapInstance) {
        mapInstance.flyTo([currentCoords.lat, currentCoords.lng], 13, { animate: true, duration: 1.2 });
      }
      fetchAndRenderStores();

      if (loc.source === "Laptop Reference Location") {
        if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
          AgriApp.showToast("Live location access was not granted. Please allow browser geolocation and retry to use your exact location.", "warning");
        }
      } else if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(`Laptop Location Active: ${loc.city}, ${loc.state}`, "success");
      }
    }
  } catch (e) {
    console.warn("Laptop live location error:", e);
    const notice = document.getElementById("locationPermissionNotice");
    if (notice) notice.classList.remove("d-none");
    if (mapLabel) { mapLabel.textContent = "Live location unavailable"; mapLabel.classList.add("text-warning"); }
    const countLabel = document.getElementById("resultsCountText");
    if (countLabel) countLabel.textContent = "Live location unavailable. Allow browser location or search by town / PIN code.";
    const storesContainer = document.getElementById("storesCardsContainer");
    if (storesContainer) storesContainer.innerHTML = '<div class="alert alert-warning">Nearby stores are not shown until your location is available. Search for a town or PIN code instead.</div>';
    let message = "The browser could not determine this device location.";
    if (e && e.code === 1) message = "Location permission is blocked. Set Location to Allow from the site controls beside the address bar, then retry. Also check Windows Settings > Privacy > Location.";
    else if (e && e.code === 2) message = "Windows could not determine your location. Turn on Windows Location Services and connect to Wi-Fi, then retry.";
    else if (e && e.code === 3) message = "Location lookup timed out. Make sure Windows Location Services and Wi-Fi are on, then retry.";
    else if (e && e.message) message = e.message;
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) AgriApp.showToast(message, "warning");
  }

  const modalEl = document.getElementById("mobileGpsModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }
}

function onCityPresetChange(val) {
  if (val === "mobile_gps") {
    openMobileGpsModal();
    return;
  }
  if (val === "laptop_gps") {
    useLaptopLocationExplicitly();
    return;
  }

  isGpsActive = false;
  isMobileGpsActive = false;
  const input = document.getElementById("searchInput");
  if (input) input.value = val;
  applySearch();
}

function onDiseaseFilterChange(val) {
  currentDisease = val;
  const banner = document.getElementById("diseaseFilterBanner");
  const bannerName = document.getElementById("bannerDiseaseName");

  if (val) {
    if (banner) banner.classList.remove("d-none");
    if (bannerName) bannerName.textContent = val;
  } else {
    if (banner) banner.classList.add("d-none");
  }
  fetchAndRenderStores();
}

function clearDiseaseFilter() {
  currentDisease = "";
  const diseaseSelect = document.getElementById("diseaseSelect");
  if (diseaseSelect) diseaseSelect.value = "";

  const banner = document.getElementById("diseaseFilterBanner");
  if (banner) banner.classList.add("d-none");

  fetchAndRenderStores();
}

function setCategoryFilter(cat) {
  currentCategory = cat;
  const targetCat = cat.toLowerCase();
  document.querySelectorAll(".category-pill").forEach(btn => {
    const btnText = btn.textContent.trim().toLowerCase();
    const isMatch = (targetCat === 'all' && (btnText === 'all' || btnText.includes('all'))) ||
                    (targetCat !== 'all' && (btnText.includes(targetCat) || targetCat.includes(btnText.split('&')[0].trim())));
    btn.classList.toggle("active", isMatch);
    btn.classList.toggle("btn-agri-primary", isMatch);
    btn.classList.toggle("btn-agri-outline", !isMatch);
  });
  fetchAndRenderStores();
}

function onDistanceRangeInput(val) {
  const lbl = document.getElementById("distanceLabel");
  if (lbl) lbl.textContent = `${val} km`;
  fetchAndRenderStores();
}

function applySearch() {
  const searchVal = document.getElementById("searchInput")?.value.trim();
  if (searchVal) {
    isGpsActive = false;
    isMobileGpsActive = false;
  }
  fetchAndRenderStores();
}

function resetFilters() {
  isGpsActive = false;
  isMobileGpsActive = false;
  currentCategory = "all";
  currentDisease = "";
  const searchInput = document.getElementById("searchInput");
  const diseaseSelect = document.getElementById("diseaseSelect");
  const distRange = document.getElementById("distanceRange");
  const inStockSwitch = document.getElementById("inStockOnlySwitch");
  const verifiedSwitch = document.getElementById("verifiedOnlySwitch");
  const banner = document.getElementById("diseaseFilterBanner");
  const citySelect = document.getElementById("cityPresetSelect");

  if (searchInput) searchInput.value = "";
  if (diseaseSelect) diseaseSelect.value = "";
  if (distRange) distRange.value = "20";
  if (inStockSwitch) inStockSwitch.checked = false;
  if (verifiedSwitch) verifiedSwitch.checked = false;
  if (banner) banner.classList.add("d-none");
  if (citySelect) citySelect.value = "laptop_gps";

  onDistanceRangeInput(20);
  setCategoryFilter("all");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

