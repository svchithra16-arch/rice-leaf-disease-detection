/**
 * AgriVersion - Global Application State, Auth Session & UI Utilities
 */

const AgriApp = (function() {
  let currentUser = null;

  async function checkAuth(requiresAuth = false, requiresAdmin = false) {
    try {
      const res = await fetch("/api/auth/me");
      const data = await res.json();
      
      if (data.authenticated && data.user) {
        currentUser = data.user;
        updateNavUserUI(currentUser);

        // If on login or register page, redirect to next URL or dashboard
        const currentPath = window.location.pathname;
        if (currentPath.endsWith("login.html") || currentPath.endsWith("register.html")) {
          const urlParams = new URLSearchParams(window.location.search);
          const next = urlParams.get("next") || (currentUser.role === "admin" ? "/admin.html" : "/dashboard.html");
          window.location.href = next;
        }

        // If admin page requires admin role
        if (requiresAdmin && currentUser.role !== "admin") {
          showToast("Access Denied: Administrator role required.", "error");
          setTimeout(() => { window.location.href = "/dashboard.html"; }, 1500);
        }

        return currentUser;
      } else {
        currentUser = null;
        updateNavUserUI(null);

        if (requiresAuth) {
          const currentPath = window.location.pathname;
          window.location.href = "/login.html?next=" + encodeURIComponent(currentPath) + "&reason=auth_required";
        }
        return null;
      }
    } catch (e) {
      console.warn("Auth check failed:", e);
      if (requiresAuth) {
        const currentPath = window.location.pathname;
        window.location.href = "/login.html?next=" + encodeURIComponent(currentPath) + "&reason=auth_required";
      }
      return null;
    }
  }

  function updateNavUserUI(user) {
    const authNavContainer = document.getElementById("authNavContainer");
    if (!authNavContainer) return;

    if (user) {
      const isAdmin = (user.role === "admin");
      authNavContainer.innerHTML = `
        <li class="nav-item dropdown">
          <a class="nav-link-agri dropdown-toggle" href="javascript:void(0)" id="userNavDropdown" data-bs-toggle="dropdown" aria-expanded="false">
            <span class="badge ${isAdmin ? 'bg-danger' : 'bg-success'}" style="font-size:0.75rem;margin-right:4px;">${isAdmin ? 'ADMIN' : 'FARMER'}</span>
            <span>${escapeHtml(user.full_name.split(' ')[0])}</span>
          </a>
          <ul class="dropdown-menu dropdown-menu-agri dropdown-menu-end" aria-labelledby="userNavDropdown">
            <li><a class="dropdown-item dropdown-item-agri" href="/profile.html"><i class="fas fa-user-circle me-2 text-emerald"></i> Profile & Settings</a></li>
            ${isAdmin ? '<li><a class="dropdown-item dropdown-item-agri" href="/admin.html"><i class="fas fa-shield-alt me-2 text-warning"></i> Admin Portal</a></li>' : ''}
            <li><hr class="dropdown-divider" style="border-color:rgba(255,255,255,0.1)"></li>
            <li><a class="dropdown-item dropdown-item-agri text-danger" href="javascript:void(0)" onclick="AgriApp.logout()"><i class="fas fa-sign-out-alt me-2"></i> Logout</a></li>
          </ul>
        </li>
      `;
    } else {
      authNavContainer.innerHTML = `
        <a href="/login.html" class="btn-agri-outline me-2" style="padding:0.45rem 1rem;font-size:0.88rem;" data-i18n="nav.login">Login</a>
        <a href="/register.html" class="btn-agri-primary" style="padding:0.45rem 1rem;font-size:0.88rem;" data-i18n="nav.register">Register</a>
      `;
      if (window.AgriI18n) {
        AgriI18n.applyTranslations();
      }
    }
  }

  async function logout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      showToast("Logged out successfully.", "success");
      setTimeout(() => {
        window.location.href = "/index.html";
      }, 800);
    } catch (e) {
      window.location.href = "/login.html";
    }
  }

  function showToast(message, type = "info") {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.className = "agri-toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `agri-toast toast-${type}`;

    let icon = "fa-info-circle text-info";
    if (type === "success") icon = "fa-check-circle text-success";
    else if (type === "error") icon = "fa-exclamation-triangle text-danger";
    else if (type === "warning") icon = "fa-exclamation-circle text-warning";

    toast.innerHTML = `
      <i class="fas ${icon} fa-lg mt-1"></i>
      <div style="flex:1;font-size:0.92rem;">${message}</div>
      <i class="fas fa-times text-muted" style="cursor:pointer;" onclick="this.parentElement.remove()"></i>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 4500);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function renderNavbar() {
    const navPlaceholder = document.getElementById("navbarPlaceholder");
    if (!navPlaceholder) return;

    const currentPath = window.location.pathname;
    const isLinkActive = (path) => currentPath.endsWith(path) ? "active" : "";

    navPlaceholder.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-agri">
        <div class="container-fluid">
          <a class="navbar-brand-agri" href="/index.html">
            <span class="brand-icon">🌾</span>
            <span class="brand-gradient">AgriVersion</span>
          </a>

          <button class="navbar-toggler text-white" type="button" data-bs-toggle="collapse" data-bs-target="#agriNavbarNav" aria-controls="agriNavbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <i class="fas fa-bars"></i>
          </button>

          <div class="collapse navbar-collapse" id="agriNavbarNav">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0 ms-lg-3 gap-1">
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('dashboard.html')}" href="/dashboard.html"><i class="fas fa-chart-pie"></i> <span data-i18n="nav.dashboard">Dashboard</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('detect.html')}" href="/detect.html"><i class="fas fa-microscope"></i> <span data-i18n="nav.detect">Detect Disease</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('camera.html')}" href="/camera.html"><i class="fas fa-camera"></i> <span data-i18n="nav.camera">Live Camera</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('chat.html')}" href="/chat.html"><i class="fas fa-robot"></i> <span data-i18n="nav.chat">RiceCare AI</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('stores.html')}" href="/stores.html"><i class="fas fa-store"></i> <span data-i18n="nav.stores">Agri Stores</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('farms.html')}" href="/farms.html"><i class="fas fa-tractor"></i> <span data-i18n="nav.farms">My Farms</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('history.html')}" href="/history.html"><i class="fas fa-history"></i> <span data-i18n="nav.history">Scan History</span></a></li>
              <li class="nav-item"><a class="nav-link-agri ${isLinkActive('analytics.html')}" href="/analytics.html"><i class="fas fa-chart-line"></i> <span data-i18n="nav.analytics">Analytics</span></a></li>
            </ul>

            <div class="d-flex align-items-center gap-3">
              <div id="langSelectorContainer"></div>
              <div id="authNavContainer" class="d-flex align-items-center"></div>
            </div>
          </div>
        </div>
      </nav>
    `;

    if (window.AgriI18n) {
      AgriI18n.renderLanguageDropdown();
      AgriI18n.applyTranslations();
    }
  }

  function renderFooter() {
    const footerPlaceholder = document.getElementById("footerPlaceholder");
    if (!footerPlaceholder) return;

    footerPlaceholder.innerHTML = `
      <footer class="footer-agri">
        <div class="container text-center">
          <div class="row align-items-center gy-3">
            <div class="col-md-4 text-md-start">
              <div class="fw-bold text-white fs-5">🌾 AgriVersion</div>
              <small class="text-muted">AI-Powered Multilingual Rice Pathology & Diagnosis</small>
            </div>
            <div class="col-md-4 text-center">
              <small class="text-muted">BE/B.Tech Major Project Demonstration & Viva</small><br/>
              <span class="badge bg-success" style="font-size:0.75rem;">Deep CNN (RiceNet) + Grad-CAM + Gemini Multimodal</span>
            </div>
            <div class="col-md-4 text-md-end">
              <small class="text-muted">© 2026 AgriVersion. Empowering Smart Agriculture.</small>
            </div>
          </div>
        </div>
      </footer>
    `;
  }

  // ============================================================================
  // Mobile GPS Synchronization & Multi-Tier Location Resolver
  // ============================================================================
  let cachedLiveLocation = null;
  let preferredLocationSource = localStorage.getItem("agri_location_source") || "laptop";
  let activeMobileSessionId = localStorage.getItem("agri_mobile_gps_session") || null;
  let mobileGpsState = {
    sessionId: activeMobileSessionId,
    status: "idle", // idle, waiting, connected, disconnected, denied
    lat: null,
    lng: null,
    accuracy: null,
    altitude: null,
    heading: null,
    speed: null,
    label: null,
    city: null,
    district: null,
    state: null,
    pincode: null,
    lastSeenSecondsAgo: 999,
    updatesCount: 0,
    errorMessage: null
  };
  let mobilePollTimer = null;
  const mobileLocationListeners = new Set();

  async function reverseGeocode(lat, lng) {
    if (!lat || !lng) return null;
    try {
      const res = await fetch(`/api/stores/reverse-geocode?lat=${lat}&lng=${lng}`);
      const data = await res.json();
      if (data.success && data.location) {
        let loc = data.location;
        let rawCity = loc.city || loc.district || "Local Area";
        let city = rawCity.replace(/\s+(taluk|taluku|district)$/i, '');
        let rawDistrict = loc.district || city;
        let district = rawDistrict.replace(/\s+(district)$/i, '');
        let state = loc.state || "Karnataka";
        let label = (loc.label || `${city}, ${state}`).replace(/\s+taluku?/gi, '');
        return {
          city: city,
          district: district,
          state: state,
          pincode: loc.pincode || "",
          address: loc.address || `${city}, ${state}`,
          label: label
        };
      }
    } catch (e) {
      console.warn("Server reverse geocode failed, trying client fallback:", e);
    }

    try {
      const res = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`);
      const data = await res.json();
      const city = (data.city || data.locality || data.principalSubdivision || "Local Area").replace(/\s+(taluk|taluku|district)$/i, '');
      const state = data.principalSubdivision || "Karnataka";
      return {
        city: city,
        district: city,
        state: state,
        pincode: data.postcode || "",
        address: `${city}, ${state}`,
        label: `${city}, ${state}`
      };
    } catch (e) {
      return null;
    }
  }

  // Mobile GPS Session Manager
  const mobileGps = {
    getState: () => ({ ...mobileGpsState }),
    
    isMobileActive: () => {
      return preferredLocationSource === "mobile" && (mobileGpsState.status === "connected" || mobileGpsState.lat !== null);
    },

    setSourcePreference: (source) => {
      preferredLocationSource = source;
      localStorage.setItem("agri_location_source", source);
      cachedLiveLocation = null;
    },

    subscribe: (fn) => {
      mobileLocationListeners.add(fn);
      return () => mobileLocationListeners.delete(fn);
    },

    notifyListeners: (eventData) => {
      mobileLocationListeners.forEach((fn) => {
        try {
          fn(eventData);
        } catch (e) {
          console.error("Mobile GPS listener callback error:", e);
        }
      });
    },

    initSession: async (forceNew = false) => {
      try {
        let sid = (!forceNew && activeMobileSessionId) ? activeMobileSessionId : null;
        const url = sid ? `/api/location/session/create?session_id=${sid}` : `/api/location/session/create`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.success) {
          activeMobileSessionId = data.session_id;
          localStorage.setItem("agri_mobile_gps_session", activeMobileSessionId);
          mobileGpsState.sessionId = activeMobileSessionId;
          mobileGpsState.mobileUrl = data.mobile_url;
          mobileGpsState.lanIp = data.lan_ip;
          mobileGpsState.port = data.port;
          return data;
        }
      } catch (e) {
        console.error("Failed to init mobile GPS session:", e);
      }
      return null;
    },

    startPolling: (intervalMs = 1500) => {
      if (mobilePollTimer) clearInterval(mobilePollTimer);
      if (!activeMobileSessionId) {
        activeMobileSessionId = localStorage.getItem("agri_mobile_gps_session");
      }
      if (!activeMobileSessionId) return;

      const pollFn = async () => {
        try {
          const res = await fetch(`/api/location/session/${activeMobileSessionId}/status`);
          if (res.status === 404) {
            localStorage.removeItem("agri_mobile_gps_session");
            activeMobileSessionId = null;
            mobileGps.stopPolling();
            return;
          }
          if (!res.ok) return;
          const data = await res.json();
          if (data.success) {
            const prevStatus = mobileGpsState.status;
            const prevLat = mobileGpsState.lat;
            const prevLng = mobileGpsState.lng;

            mobileGpsState.status = data.status;
            mobileGpsState.lat = data.lat;
            mobileGpsState.lng = data.lng;
            mobileGpsState.accuracy = data.accuracy;
            mobileGpsState.altitude = data.altitude;
            mobileGpsState.heading = data.heading;
            mobileGpsState.speed = data.speed;
            mobileGpsState.label = data.label;
            mobileGpsState.city = data.city;
            mobileGpsState.district = data.district;
            mobileGpsState.state = data.state;
            mobileGpsState.pincode = data.pincode;
            mobileGpsState.updatesCount = data.updates_count;
            mobileGpsState.lastSeenSecondsAgo = data.last_seen_seconds_ago;
            mobileGpsState.errorMessage = data.error_message;

            const hasCoordChanged = (data.lat !== null && data.lng !== null) &&
                                    (data.lat !== prevLat || data.lng !== prevLng);
            const hasStatusChanged = (data.status !== prevStatus);

            if (data.lat !== null && data.lng !== null) {
              cachedLiveLocation = {
                lat: data.lat,
                lng: data.lng,
                accuracy: data.accuracy,
                city: data.city || "Live Mobile Area",
                district: data.district || "Live Mobile Area",
                state: data.state || "",
                pincode: data.pincode || "",
                label: data.label || `📍 ${data.lat.toFixed(4)}° N, ${data.lng.toFixed(4)}° E`,
                source: "📱 Mobile Phone GPS",
                isGps: true,
                isMobile: true
              };
            }

            if (hasCoordChanged || hasStatusChanged) {
              mobileGps.notifyListeners({
                type: hasCoordChanged ? "location_update" : "status_change",
                state: { ...mobileGpsState },
                location: cachedLiveLocation
              });
            }
          }
        } catch (e) {
          // background poll network jitter ignore
        }
      };

      pollFn();
      mobilePollTimer = setInterval(pollFn, intervalMs);
    },

    stopPolling: () => {
      if (mobilePollTimer) {
        clearInterval(mobilePollTimer);
        mobilePollTimer = null;
      }
    },

    disconnect: async () => {
      mobileGps.stopPolling();
      if (activeMobileSessionId) {
        try {
          await fetch(`/api/location/session/${activeMobileSessionId}/disconnect`, { method: "POST" });
        } catch (e) {}
      }
      mobileGpsState.status = "disconnected";
      mobileGpsState.lat = null;
      mobileGpsState.lng = null;
      cachedLiveLocation = null;
      mobileGps.notifyListeners({ type: "status_change", state: { ...mobileGpsState } });
    }
  };

  // Automatically start polling if a session exists
  if (activeMobileSessionId) {
    mobileGps.startPolling(1500);
  }

  /**
   * Primary Location Resolver
   * Priority 1: Laptop Browser HTML5 Geolocation & Laptop IP Geolocation (Default)
   * Priority 2: Mobile Phone GPS (only if user explicitly selected mobile source or connected mobile)
   */
  async function getLiveLocation(forceRefresh = false, allowLaptopFallback = true) {
    const isStoredDefaultLocation = cachedLiveLocation && cachedLiveLocation.source === "Laptop Reference Location";
    if (!forceRefresh && cachedLiveLocation && !isStoredDefaultLocation && (preferredLocationSource !== "mobile" || cachedLiveLocation.isMobile)) {
      return cachedLiveLocation;
    }

    // 1. If user explicitly chose mobile GPS and mobile is active/connected
    if (preferredLocationSource === "mobile" && mobileGpsState.lat !== null && mobileGpsState.lng !== null) {
      cachedLiveLocation = {
        lat: mobileGpsState.lat,
        lng: mobileGpsState.lng,
        accuracy: mobileGpsState.accuracy,
        city: mobileGpsState.city || "Live Mobile Area",
        district: mobileGpsState.district || "Live Mobile Area",
        state: mobileGpsState.state || "",
        pincode: mobileGpsState.pincode || "",
        label: mobileGpsState.label || `📍 ${mobileGpsState.lat.toFixed(4)}° N, ${mobileGpsState.lng.toFixed(4)}° E`,
        source: "📱 Mobile Phone GPS",
        isGps: true,
        isMobile: true
      };
      return cachedLiveLocation;
    }

    // 2. Primary Default: Laptop Browser HTML5 Geolocation or Laptop IP Geolocation
    let lat = null;
    let lng = null;
    let isGps = false;
    let source = "💻 Laptop Browser Location";
    let geolocationError = null;

    // Try HTML5 navigator.geolocation first on laptop; keep browser permission states visible
    if (!navigator.geolocation && !allowLaptopFallback) {
      throw new Error("This browser does not support device location.");
    }
    if (navigator.geolocation) {
      try {
        const permissionStatus = await navigator.permissions?.query?.({ name: "geolocation" }).catch(() => null);
        if (permissionStatus && permissionStatus.state === "denied") {
          const warningMsg = "Location access is blocked in this browser. Please allow location permission and click 'Use my live location' again.";
          if (typeof showToast === "function") {
            showToast(warningMsg, "warning");
          }
        }

        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 20000,
            maximumAge: 0
          });
        });
        lat = position.coords.latitude;
        lng = position.coords.longitude;
        isGps = true;
        source = "💻 Laptop Browser GPS";
      } catch (e) {
        geolocationError = e;
        console.warn("Browser device location unavailable:", e);
      }
    }

    // Fallback to backend IP Geolocation if HTML5 not available or failed
    if (allowLaptopFallback && (lat === null || lng === null)) {
      try {
        const res = await fetch("/api/stores/detect-my-location");
        const data = await res.json();
        if (data.success && data.lat && data.lng) {
          lat = data.lat;
          lng = data.lng;
          source = data.source || "💻 Laptop IP Location";
          isGps = true;
        }
      } catch (e) {
        console.warn("Backend IP location failed:", e);
      }
    }

    // Do not substitute approximate/default coordinates for a requested live location.
    if ((lat === null || lng === null) && !allowLaptopFallback) {
      throw geolocationError || new Error("The browser could not determine this device location.");
    }

    // Hard fallback if all fails
    if (lat === null || lng === null) {
      lat = 13.2936;
      lng = 77.5342;
      source = "Laptop Reference Location";
    }

    const geoInfo = await reverseGeocode(lat, lng);
    const city = geoInfo ? geoInfo.city : "Local Area";
    const state = geoInfo ? geoInfo.state : "Karnataka";
    const district = geoInfo ? geoInfo.district : city;
    const label = geoInfo ? geoInfo.label : `${city}, ${state}`;

    cachedLiveLocation = {
      lat: lat,
      lng: lng,
      city: city,
      district: district,
      state: state,
      pincode: geoInfo ? geoInfo.pincode : "",
      label: label,
      source: source,
      isGps: isGps,
      isMobile: false
    };

    return cachedLiveLocation;
  }

  return {
    checkAuth,
    logout,
    showToast,
    escapeHtml,
    renderNavbar,
    renderFooter,
    getLiveLocation,
    reverseGeocode,
    mobileGps,
    getUser: () => currentUser
  };
})();

