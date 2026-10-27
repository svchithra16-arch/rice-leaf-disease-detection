/**
 * AgriVersion - Online Agri Store Module
 * Clean Green-and-White Theme, Responsive Product Catalog, Sidebar Menu & Search
 * Links to verified shopping portals: BigHaat, AgroStar, IFFCO Bazar, KisanKraft, Amazon Agriculture
 * Zero GPS / Geolocation Dependencies.
 */

const OnlineStore = (function() {
  // Store State
  let allProducts = [];
  let currentCategory = "All";
  let searchQuery = "";
  let currentDisease = "";
  let currentPriceFilter = "all";
  let maxBudgetSlider = 3500;
  let currentSort = "popular";
  let categoryCounts = {};
  let productModalInstance = null;

  /**
   * Initializes the Online Agri Store
   */
  async function init() {
    console.log("Initializing Online Agri Store (Zero GPS)...");

    // 1. Initialize Bootstrap Modal Instance
    const modalEl = document.getElementById("productModal");
    if (modalEl && typeof bootstrap !== "undefined") {
      productModalInstance = new bootstrap.Modal(modalEl);
    }

    // 2. Read query params (e.g. ?disease=Rice+Blast or ?category=Seeds)
    const urlParams = new URLSearchParams(window.location.search);
    const diseaseParam = urlParams.get("disease");
    const categoryParam = urlParams.get("category");
    const queryParam = urlParams.get("query") || urlParams.get("q");

    if (diseaseParam && diseaseParam.trim()) {
      currentDisease = diseaseParam.trim();
      showDiseaseBanner(currentDisease);
      const disSelect = document.getElementById("sidebarDiseaseSelect");
      if (disSelect) {
        // Find matching option or set value
        let found = false;
        for (let opt of disSelect.options) {
          if (opt.value.toLowerCase() === currentDisease.toLowerCase() || opt.value.toLowerCase().includes(currentDisease.toLowerCase())) {
            disSelect.value = opt.value;
            found = true;
            break;
          }
        }
      }
    }

    if (categoryParam && categoryParam.trim()) {
      currentCategory = normalizeCategoryName(categoryParam.trim());
    }

    if (queryParam && queryParam.trim()) {
      searchQuery = queryParam.trim();
      const sInput = document.getElementById("storeSearchInput");
      if (sInput) sInput.value = searchQuery;
      toggleSearchClearBtn(true);
    }

    // 3. Fetch Product Catalog from Backend
    await fetchProductsCatalog();

    // 4. Update UI & Render Products
    applyFiltersAndRender();
  }

  /**
   * Fetches the complete online product catalog from backend API
   */
  async function fetchProductsCatalog() {
    showLoadingSkeleton();

    try {
      const res = await fetch("/api/stores/products");
      const data = await res.json();

      if (data.success && Array.isArray(data.products)) {
        allProducts = data.products;
        categoryCounts = data.category_counts || {};
        updateCategoryCountBadges(categoryCounts);
      } else {
        console.error("Failed to load products:", data);
        renderFallbackProducts();
      }
    } catch (err) {
      console.warn("API network error while loading catalog, rendering local catalog:", err);
      renderFallbackProducts();
    }
  }

  /**
   * Normalizes category names to standard 5 categories
   */
  function normalizeCategoryName(cat) {
    if (!cat) return "All";
    const lower = cat.toLowerCase();
    if (lower === "all" || lower === "all products") return "All";
    if (lower.includes("seed")) return "Seeds";
    if (lower.includes("fert")) return "Fertilizers";
    if (lower.includes("pest") || lower.includes("fung")) return "Pesticides";
    if (lower.includes("tool") || lower.includes("equip") || lower.includes("machin")) return "Tools & Equipment";
    if (lower.includes("organ") || lower.includes("bio")) return "Organic Products";
    return cat;
  }

  /**
   * Updates category count badges in the sidebar
   */
  function updateCategoryCountBadges(counts) {
    const elAll = document.getElementById("countAll");
    const elSeeds = document.getElementById("countSeeds");
    const elFert = document.getElementById("countFertilizers");
    const elPest = document.getElementById("countPesticides");
    const elTools = document.getElementById("countTools");
    const elOrg = document.getElementById("countOrganic");

    if (elAll && counts.All !== undefined) elAll.textContent = counts.All;
    if (elSeeds && counts.Seeds !== undefined) elSeeds.textContent = counts.Seeds;
    if (elFert && counts.Fertilizers !== undefined) elFert.textContent = counts.Fertilizers;
    if (elPest && counts.Pesticides !== undefined) elPest.textContent = counts.Pesticides;
    if (elTools && counts["Tools & Equipment"] !== undefined) elTools.textContent = counts["Tools & Equipment"];
    if (elOrg && counts["Organic Products"] !== undefined) elOrg.textContent = counts["Organic Products"];
  }

  /**
   * Displays the disease prescription banner at the top
   */
  function showDiseaseBanner(disease) {
    const banner = document.getElementById("diseaseAlertBanner");
    const nameEl = document.getElementById("bannerDiseaseName");
    if (banner && nameEl) {
      nameEl.textContent = disease;
      banner.classList.remove("d-none");
    }
  }

  /**
   * Clears the disease filter
   */
  function clearDiseaseFilter() {
    currentDisease = "";
    const banner = document.getElementById("diseaseAlertBanner");
    if (banner) banner.classList.add("d-none");

    const disSelect = document.getElementById("sidebarDiseaseSelect");
    if (disSelect) disSelect.value = "";

    // Remove disease query from URL without reloading
    const url = new URL(window.location);
    url.searchParams.delete("disease");
    window.history.replaceState({}, "", url);

    applyFiltersAndRender();
  }

  /**
   * Category button selection handler
   */
  function selectCategory(catName) {
    currentCategory = normalizeCategoryName(catName);

    // Update active class on sidebar buttons
    const btns = document.querySelectorAll("#categoryBtnList .category-btn");
    btns.forEach(btn => {
      const btnCat = btn.getAttribute("data-category");
      if (normalizeCategoryName(btnCat) === currentCategory) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    applyFiltersAndRender();
  }

  /**
   * Search input handler with debounce
   */
  let searchTimer = null;
  function handleSearchInput(value) {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchQuery = value.trim();
      toggleSearchClearBtn(searchQuery.length > 0);
      applyFiltersAndRender();
    }, 200);
  }

  function clearSearchInput() {
    searchQuery = "";
    const sInput = document.getElementById("storeSearchInput");
    if (sInput) sInput.value = "";
    toggleSearchClearBtn(false);
    applyFiltersAndRender();
  }

  function toggleSearchClearBtn(show) {
    const clearBtn = document.getElementById("searchClearBtn");
    if (clearBtn) {
      clearBtn.style.display = show ? "block" : "none";
    }
  }

  /**
   * Sort dropdown handler
   */
  function handleSort(sortValue) {
    currentSort = sortValue;
    applyFiltersAndRender();
  }

  /**
   * Price radio filter handler
   */
  function handlePriceRadio(radioVal) {
    currentPriceFilter = radioVal;
    applyFiltersAndRender();
  }

  /**
   * Price slider handler
   */
  function handlePriceSlider(sliderVal) {
    maxBudgetSlider = parseInt(sliderVal, 10);
    const label = document.getElementById("maxPriceLabel");
    if (label) label.textContent = `₹${maxBudgetSlider.toLocaleString("en-IN")}`;
    applyFiltersAndRender();
  }

  /**
   * Sidebar disease select dropdown handler
   */
  function handleDiseaseDropdown(diseaseVal) {
    currentDisease = diseaseVal.trim();
    if (currentDisease) {
      showDiseaseBanner(currentDisease);
    } else {
      const banner = document.getElementById("diseaseAlertBanner");
      if (banner) banner.classList.add("d-none");
    }
    applyFiltersAndRender();
  }

  /**
   * Resets all applied filters
   */
  function resetAllFilters() {
    currentCategory = "All";
    searchQuery = "";
    currentDisease = "";
    currentPriceFilter = "all";
    maxBudgetSlider = 3500;
    currentSort = "popular";

    // Reset UI elements
    const sInput = document.getElementById("storeSearchInput");
    if (sInput) sInput.value = "";
    toggleSearchClearBtn(false);

    const priceAllRadio = document.getElementById("priceAll");
    if (priceAllRadio) priceAllRadio.checked = true;

    const slider = document.getElementById("priceRangeSlider");
    if (slider) slider.value = 3500;
    const label = document.getElementById("maxPriceLabel");
    if (label) label.textContent = "₹3,500";

    const disSelect = document.getElementById("sidebarDiseaseSelect");
    if (disSelect) disSelect.value = "";

    const banner = document.getElementById("diseaseAlertBanner");
    if (banner) banner.classList.add("d-none");

    const sortSelect = document.getElementById("storeSortSelect");
    if (sortSelect) sortSelect.value = "popular";

    // Reset category buttons
    const btns = document.querySelectorAll("#categoryBtnList .category-btn");
    btns.forEach(btn => {
      if (btn.getAttribute("data-category") === "All") {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // Clear URL params
    const url = new URL(window.location);
    url.search = "";
    window.history.replaceState({}, "", url);

    applyFiltersAndRender();
  }

  /**
   * Removes a single active filter badge
   */
  function removeFilter(filterType) {
    if (filterType === "category") {
      selectCategory("All");
    } else if (filterType === "search") {
      clearSearchInput();
    } else if (filterType === "disease") {
      clearDiseaseFilter();
    } else if (filterType === "price") {
      const priceAllRadio = document.getElementById("priceAll");
      if (priceAllRadio) priceAllRadio.checked = true;
      currentPriceFilter = "all";
      applyFiltersAndRender();
    }
  }

  /**
   * Applies all filters & sorting, then updates UI
   */
  function applyFiltersAndRender() {
    let filtered = [...allProducts];

    // 1. Filter by Category
    if (currentCategory && currentCategory !== "All") {
      filtered = filtered.filter(p => {
        const cat = normalizeCategoryName(p.category);
        return cat === currentCategory;
      });
    }

    // 2. Filter by Disease
    if (currentDisease) {
      const dLower = currentDisease.toLowerCase();
      filtered = filtered.filter(p => {
        const targets = (p.target_diseases || []).map(t => t.toLowerCase());
        const benefit = (p.disease_benefit || "").toLowerCase();
        const activeIng = (p.active_ingredient || "").toLowerCase();
        return targets.some(t => t.includes(dLower) || dLower.includes(t)) ||
               benefit.includes(dLower) ||
               activeIng.includes(dLower);
      });
    }

    // 3. Filter by Search Query
    if (searchQuery) {
      const qTerms = searchQuery.toLowerCase().split(/\s+/);
      filtered = filtered.filter(p => {
        const searchable = [
          p.name || "",
          p.brand || "",
          p.category || "",
          p.sub_category || "",
          p.active_ingredient || "",
          p.disease_benefit || "",
          p.badge || "",
          ...(p.target_diseases || [])
        ].join(" ").toLowerCase();

        return qTerms.every(term => searchable.includes(term));
      });
    }

    // 4. Filter by Price Radio
    if (currentPriceFilter !== "all") {
      const [minStr, maxStr] = currentPriceFilter.split("-");
      const minP = parseFloat(minStr);
      const maxP = parseFloat(maxStr);
      filtered = filtered.filter(p => p.price >= minP && p.price <= maxP);
    }

    // 5. Filter by Max Budget Slider
    if (maxBudgetSlider < 3500) {
      filtered = filtered.filter(p => p.price <= maxBudgetSlider);
    }

    // 6. Sorting
    if (currentSort === "price_asc") {
      filtered.sort((a, b) => a.price - b.price);
    } else if (currentSort === "price_desc") {
      filtered.sort((a, b) => b.price - a.price);
    } else if (currentSort === "rating") {
      filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0) || (b.reviews_count || 0) - (a.reviews_count || 0));
    } else if (currentSort === "discount") {
      filtered.sort((a, b) => {
        const discA = ((a.original_price - a.price) / a.original_price) || 0;
        const discB = ((b.original_price - b.price) / b.original_price) || 0;
        return discB - discA;
      });
    } else { // popular
      filtered.sort((a, b) => ((b.rating || 0) * (b.reviews_count || 0)) - ((a.rating || 0) * (a.reviews_count || 0)));
    }

    // 7. Update Active Filter Badges
    renderActiveFilterBadges();

    // 8. Update Counter
    const countText = document.getElementById("productsCountText");
    if (countText) {
      const showPrefix = (window.AgriI18n && AgriI18n.t) ? AgriI18n.t("store.showing_products", "Showing certified products") : "Showing certified products";
      countText.textContent = `${showPrefix} (${filtered.length} / ${allProducts.length})`;
    }

    // 9. Render Product Cards Grid or Empty State
    const grid = document.getElementById("productsGrid");
    const emptyBox = document.getElementById("emptyStateBox");

    if (filtered.length === 0) {
      if (grid) grid.innerHTML = "";
      if (emptyBox) emptyBox.classList.remove("d-none");
    } else {
      if (emptyBox) emptyBox.classList.add("d-none");
      if (grid) {
        grid.innerHTML = filtered.map(product => createProductCardHtml(product)).join("");
      }
    }
  }

  /**
   * Generates HTML for an agricultural product card
   */
  function createProductCardHtml(product) {
    const discountPct = Math.round(((product.original_price - product.price) / product.original_price) * 100);
    const savings = product.original_price - product.price;
    const catClass = getCategoryBadgeClass(product.category);
    const iconName = product.image_icon || getCategoryDefaultIcon(product.category);
    const iconColor = product.image_color || "#059669";
    const primaryRetailer = (product.trusted_retailers && product.trusted_retailers.length > 0)
      ? product.trusted_retailers[0]
      : { platform: "BigHaat", url: "https://www.bighaat.com", price: product.price };

    return `
      <div class="col">
        <div class="product-card">
          
          <!-- Product Card Visual Header -->
          <div class="product-visual-box">
            <span class="badge-category-tag">
              ${escapeHtml(product.category)}
            </span>
            ${discountPct > 0 ? `<span class="badge-discount-tag">${discountPct}% OFF</span>` : ''}
            
            <div class="product-icon-avatar" style="color: ${iconColor};">
              <i class="${escapeHtml(iconName)}"></i>
            </div>

            ${product.badge ? `
              <div class="product-badge-strip">
                <i class="fas fa-check-circle text-success me-1"></i> ${escapeHtml(product.badge)}
              </div>
            ` : ''}
          </div>

          <!-- Product Card Body -->
          <div class="product-body">
            <div class="product-brand">${escapeHtml(product.brand || 'Certified Agro Brand')}</div>
            <h3 class="product-title" title="${escapeHtml(product.name)}">${escapeHtml(product.name)}</h3>
            
            <div class="product-ingredient-tag" title="${escapeHtml(product.active_ingredient || '')}">
              <i class="fas fa-flask me-1 text-muted"></i> ${escapeHtml(product.active_ingredient || 'Standard Spec')}
            </div>

            <p class="product-desc-snippet">
              ${escapeHtml(product.disease_benefit || product.sub_category || 'Certified agricultural input for healthy rice crop stand.')}
            </p>

            <div class="product-meta-row">
              <span><i class="fas fa-box me-1 text-muted"></i> ${escapeHtml(product.pack_size || 'Standard Pack')}</span>
              <span class="rating-stars">
                <i class="fas fa-star"></i> ${product.rating || '4.8'} 
                <span class="text-muted fw-normal" style="font-size:0.75rem;">(${product.reviews_count || '120'})</span>
              </span>
            </div>

            <div class="product-price-row">
              <span class="product-price-current">₹${product.price.toLocaleString("en-IN")}</span>
              ${product.original_price > product.price ? `
                <span class="product-price-original">₹${product.original_price.toLocaleString("en-IN")}</span>
                <span class="product-savings-badge">Save ₹${savings}</span>
              ` : ''}
            </div>

            <!-- Action Buttons: View Product + Buy Online -->
            <div class="row g-2 mt-auto">
              <div class="col-6">
                <button class="btn-view-product" onclick="OnlineStore.openProductModal('${product.id}')">
                  <i class="fas fa-eye"></i> ${(window.AgriI18n && AgriI18n.t) ? AgriI18n.t("store.view_product", "View Details") : "View Details"}
                </button>
              </div>
              <div class="col-6">
                <a href="${escapeHtml(primaryRetailer.url)}" target="_blank" rel="noopener noreferrer" class="btn-buy-online" title="Buy on ${escapeHtml(primaryRetailer.platform)}">
                  <i class="fas fa-arrow-up-right-from-square"></i> ${(window.AgriI18n && AgriI18n.t) ? AgriI18n.t("store.buy_now", "Buy Online") : "Buy Online"}
                </a>
              </div>
            </div>

          </div>

        </div>
      </div>
    `;
  }

  /**
   * Opens the Product Details Modal with technical dosage, safety, and all trusted store links
   */
  function openProductModal(productId) {
    const prod = allProducts.find(p => p.id === productId);
    if (!prod) return;

    // 1. Populate Basic Info
    const iconAvatar = document.getElementById("modalIconAvatar");
    if (iconAvatar) {
      iconAvatar.innerHTML = `<i class="${escapeHtml(prod.image_icon || 'fas fa-seedling')}" style="color:${prod.image_color || '#059669'};"></i>`;
    }

    const catBadge = document.getElementById("modalCategoryBadge");
    if (catBadge) catBadge.textContent = prod.category;

    const brandEl = document.getElementById("modalBrand");
    if (brandEl) brandEl.textContent = prod.brand;

    const nameEl = document.getElementById("modalProductName");
    if (nameEl) nameEl.textContent = prod.name;

    // 2. Pricing
    const currPriceEl = document.getElementById("modalCurrentPrice");
    if (currPriceEl) currPriceEl.textContent = `₹${prod.price.toLocaleString("en-IN")}`;

    const origPriceEl = document.getElementById("modalOriginalPrice");
    if (origPriceEl) {
      if (prod.original_price > prod.price) {
        origPriceEl.textContent = `₹${prod.original_price.toLocaleString("en-IN")}`;
        origPriceEl.classList.remove("d-none");
      } else {
        origPriceEl.classList.add("d-none");
      }
    }

    const savingsBadge = document.getElementById("modalSavingsBadge");
    if (savingsBadge) {
      const discountPct = Math.round(((prod.original_price - prod.price) / prod.original_price) * 100);
      if (discountPct > 0) {
        savingsBadge.textContent = `Save ${discountPct}% (₹${prod.original_price - prod.price})`;
        savingsBadge.classList.remove("d-none");
      } else {
        savingsBadge.classList.add("d-none");
      }
    }

    const packSizeEl = document.getElementById("modalPackSize");
    if (packSizeEl) packSizeEl.textContent = `Pack: ${prod.pack_size || 'Standard'}`;

    // 3. Rating & Stock
    const ratingEl = document.getElementById("modalRatingStars");
    if (ratingEl) {
      ratingEl.innerHTML = `<i class="fas fa-star"></i> ${prod.rating || 4.9} <span class="text-muted fw-normal">(${prod.reviews_count || 250} Customer Reviews)</span>`;
    }

    // 4. Active Ingredient & Agronomic Benefits
    const aiEl = document.getElementById("modalActiveIngredient");
    if (aiEl) aiEl.textContent = prod.active_ingredient || "Proprietary Agricultural Formulation";

    const benefitEl = document.getElementById("modalDiseaseBenefit");
    if (benefitEl) benefitEl.textContent = prod.disease_benefit || "Provides targeted agronomic protection and vigorous plant tillering.";

    // 5. Dosage & Instructions
    const doseEl = document.getElementById("modalDosageLabel");
    if (doseEl) doseEl.textContent = prod.dosage_label || "Refer to product package label or consult local Krishi extension officer.";

    // 6. Safety Guidelines
    const safetyEl = document.getElementById("modalSafetyGuidelines");
    if (safetyEl) safetyEl.textContent = prod.safety_guidelines || "Store in cool dry conditions. Wear mask and protective gloves during application.";

    // 7. Render Online Shopping Links (BigHaat, AgroStar, IFFCO, KisanKraft, Amazon)
    const retailersList = document.getElementById("modalRetailersList");
    if (retailersList) {
      let rHtml = "";
      const retailers = (prod.trusted_retailers && prod.trusted_retailers.length > 0)
        ? prod.trusted_retailers
        : [
            { platform: "BigHaat", tag: "Certified Dealer", url: "https://www.bighaat.com", delivery: "3-5 Days Doorstep", price: prod.price },
            { platform: "AgroStar", tag: "Agri Mart", url: "https://www.agrostar.in", delivery: "Doorstep Delivery", price: prod.price + 5 }
          ];

      retailers.forEach(r => {
        const icon = getRetailerIcon(r.platform);
        rHtml += `
          <div class="retailer-buy-card">
            <div>
              <div class="fw-bold text-dark d-flex align-items-center gap-2">
                ${icon}
                <span>${escapeHtml(r.platform)}</span>
                <span class="badge bg-light text-success border border-success-subtle" style="font-size:0.7rem;">${escapeHtml(r.tag || 'Verified')}</span>
              </div>
              <small class="text-muted d-block mt-1">
                <i class="fas fa-truck text-muted me-1"></i> ${escapeHtml(r.delivery || 'Fast Delivery')}
              </small>
            </div>
            <div class="text-end">
              <div class="fw-bold fs-6 text-success mb-1">₹${(r.price || prod.price).toLocaleString("en-IN")}</div>
              <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-success fw-bold px-3 py-1" style="border-radius:6px; font-size:0.8rem;">
                Buy on ${escapeHtml(r.platform.split(' ')[0])} <i class="fas fa-arrow-up-right-from-square ms-1"></i>
              </a>
            </div>
          </div>
        `;
      });

      retailersList.innerHTML = rHtml;
    }

    // 8. Show Modal
    if (productModalInstance) {
      productModalInstance.show();
    } else {
      const modalEl = document.getElementById("productModal");
      if (modalEl && typeof bootstrap !== "undefined") {
        productModalInstance = new bootstrap.Modal(modalEl);
        productModalInstance.show();
      }
    }
  }

  /**
   * Helper to render active filter badges with remove buttons
   */
  function renderActiveFilterBadges() {
    const container = document.getElementById("activeFilterTags");
    const clearAllBtn = document.getElementById("clearAllFiltersBtn");
    if (!container) return;

    let badges = [];

    if (currentCategory && currentCategory !== "All") {
      badges.push(`
        <span class="active-filter-badge">
          <span>Category: <b>${escapeHtml(currentCategory)}</b></span>
          <i class="fas fa-times remove-filter" onclick="OnlineStore.removeFilter('category')"></i>
        </span>
      `);
    }

    if (searchQuery) {
      badges.push(`
        <span class="active-filter-badge">
          <span>Search: "<b>${escapeHtml(searchQuery)}</b>"</span>
          <i class="fas fa-times remove-filter" onclick="OnlineStore.removeFilter('search')"></i>
        </span>
      `);
    }

    if (currentDisease) {
      badges.push(`
        <span class="active-filter-badge">
          <span>Disease: <b>${escapeHtml(currentDisease)}</b></span>
          <i class="fas fa-times remove-filter" onclick="OnlineStore.removeFilter('disease')"></i>
        </span>
      `);
    }

    if (currentPriceFilter !== "all") {
      badges.push(`
        <span class="active-filter-badge">
          <span>Price: <b>${escapeHtml(currentPriceFilter)}</b></span>
          <i class="fas fa-times remove-filter" onclick="OnlineStore.removeFilter('price')"></i>
        </span>
      `);
    }

    if (maxBudgetSlider < 3500) {
      badges.push(`
        <span class="active-filter-badge">
          <span>Budget: <b>≤ ₹${maxBudgetSlider}</b></span>
          <i class="fas fa-times remove-filter" onclick="OnlineStore.handlePriceSlider(3500)"></i>
        </span>
      `);
    }

    if (badges.length > 0) {
      container.innerHTML = badges.join("");
      if (clearAllBtn) clearAllBtn.classList.remove("d-none");
    } else {
      container.innerHTML = `<span class="text-muted small">None (Showing all)</span>`;
      if (clearAllBtn) clearAllBtn.classList.add("d-none");
    }
  }

  /**
   * Loading Skeleton
   */
  function showLoadingSkeleton() {
    const grid = document.getElementById("productsGrid");
    if (!grid) return;
    let cards = "";
    for (let i = 0; i < 6; i++) {
      cards += `
        <div class="col">
          <div class="product-card p-3" style="min-height:360px;">
            <div class="placeholder-glow mb-3">
              <div class="placeholder col-12 rounded" style="height:140px; background:#e2e8f0;"></div>
            </div>
            <div class="placeholder-glow mb-2">
              <span class="placeholder col-4" style="background:#cbd5e1;"></span>
              <span class="placeholder col-8" style="background:#e2e8f0;"></span>
            </div>
            <div class="placeholder-glow mb-3">
              <span class="placeholder col-12" style="background:#f1f5f9;"></span>
              <span class="placeholder col-7" style="background:#f1f5f9;"></span>
            </div>
            <div class="placeholder-glow mt-auto">
              <span class="placeholder col-5 py-3" style="background:#cbd5e1;"></span>
              <span class="placeholder col-6 py-3 ms-2" style="background:#a7f3d0;"></span>
            </div>
          </div>
        </div>
      `;
    }
    grid.innerHTML = cards;
  }

  /**
   * Category helpers
   */
  function getCategoryBadgeClass(category) {
    const cat = (category || "").toLowerCase();
    if (cat.includes("seed")) return "text-warning bg-warning-subtle";
    if (cat.includes("fert")) return "text-info bg-info-subtle";
    if (cat.includes("pest")) return "text-danger bg-danger-subtle";
    if (cat.includes("tool")) return "text-primary bg-primary-subtle";
    if (cat.includes("organ")) return "text-success bg-success-subtle";
    return "text-secondary bg-light";
  }

  function getCategoryDefaultIcon(category) {
    const cat = (category || "").toLowerCase();
    if (cat.includes("seed")) return "fas fa-seedling";
    if (cat.includes("fert")) return "fas fa-cubes";
    if (cat.includes("pest")) return "fas fa-shield-virus";
    if (cat.includes("tool")) return "fas fa-wrench";
    if (cat.includes("organ")) return "fas fa-leaf";
    return "fas fa-bag-shopping";
  }

  function getRetailerIcon(platform) {
    const p = (platform || "").toLowerCase();
    if (p.includes("bighaat")) return `<i class="fas fa-bag-shopping text-success"></i>`;
    if (p.includes("agrostar")) return `<i class="fas fa-star text-warning"></i>`;
    if (p.includes("iffco")) return `<i class="fas fa-building text-info"></i>`;
    if (p.includes("kisankraft")) return `<i class="fas fa-tractor text-danger"></i>`;
    if (p.includes("amazon")) return `<i class="fab fa-amazon text-dark"></i>`;
    return `<i class="fas fa-store text-success"></i>`;
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

  /**
   * Fallback products in case of network issue
   */
  function renderFallbackProducts() {
    allProducts = [
      {
        id: "prod-pest-1",
        name: "Beam 75% WP (Tricyclazole)",
        brand: "Corteva Agriscience",
        category: "Pesticides",
        price: 420,
        original_price: 490,
        pack_size: "120 g",
        rating: 4.9,
        reviews_count: 318,
        badge: "Top Seller for Rice Blast",
        active_ingredient: "Tricyclazole 75% WP",
        target_diseases: ["Rice Blast", "Blast"],
        disease_benefit: "Gold-standard systemic melanin biosynthesis inhibitor specifically targeted against rice leaf and neck blast.",
        dosage_label: "0.6 g per Litre of water (120 g per acre in 200 L water)",
        safety_guidelines: "Waiting period: 30 days before harvest. Spray during early morning.",
        image_icon: "fas fa-shield-virus",
        image_color: "#059669",
        trusted_retailers: [
          { platform: "BigHaat", tag: "Official Dealer", url: "https://www.bighaat.com/search?q=Beam+Tricyclazole", delivery: "3-5 Days Doorstep Delivery", price: 420 },
          { platform: "AgroStar", tag: "Agri Mart", url: "https://www.agrostar.in/search?q=Beam+Tricyclazole", delivery: "Doorstep Delivery", price: 425 }
        ]
      },
      {
        id: "prod-fert-1",
        name: "IFFCO Nano Urea Liquid (500 ml)",
        brand: "IFFCO",
        category: "Fertilizers",
        price: 225,
        original_price: 240,
        pack_size: "500 ml Bottle",
        rating: 4.9,
        reviews_count: 890,
        badge: "Govt Approved - Replaces 1 Bag Urea",
        active_ingredient: "Nano Nitrogen (4.0% w/v Total Nitrogen)",
        target_diseases: ["Nitrogen Deficiency", "Stunted Growth"],
        disease_benefit: "Over 80% nitrogen absorption efficiency via stomata. Prevents lodging and boosts tillering.",
        dosage_label: "2 to 4 ml per Litre of water applied at active tillering.",
        safety_guidelines: "Shake well before use. Compatible with common fungicides.",
        image_icon: "fas fa-tint",
        image_color: "#10b981",
        trusted_retailers: [
          { platform: "IFFCO Bazar", tag: "Direct Manufacturer", url: "https://www.iffcobazar.in", delivery: "Free Delivery Across India", price: 225 },
          { platform: "BigHaat", tag: "Official Partner", url: "https://www.bighaat.com", delivery: "Doorstep Delivery", price: 225 }
        ]
      },
      {
        id: "prod-seed-1",
        name: "Samba Mahsuri (BPT 5204) Certified Seeds",
        brand: "National Seeds Corporation (NSC)",
        category: "Seeds",
        price: 1250,
        original_price: 1400,
        pack_size: "25 kg Bag",
        rating: 4.9,
        reviews_count: 520,
        badge: "Top Sona Masoori Rice Variety",
        active_ingredient: "Certified Foundation Paddy Seed (98%+ Purity)",
        target_diseases: ["Rice Blast Resistance (Moderate)"],
        disease_benefit: "Premier medium-slender fine grain paddy with outstanding cooking quality.",
        dosage_label: "Seed rate: 20-25 kg per acre for transplanted paddy.",
        safety_guidelines: "Pre-treated with fungicide for seed-borne fungal prevention.",
        image_icon: "fas fa-seedling",
        image_color: "#059669",
        trusted_retailers: [
          { platform: "BigHaat", tag: "Certified Seed Depot", url: "https://www.bighaat.com", delivery: "Express Seed Delivery", price: 1250 }
        ]
      },
      {
        id: "prod-tool-1",
        name: "KisanKraft 16L 12V Battery Knapsack Sprayer",
        brand: "KisanKraft",
        category: "Tools & Equipment",
        price: 2890,
        original_price: 3600,
        pack_size: "16 Litre Tank",
        rating: 4.9,
        reviews_count: 680,
        badge: "Top Rated Farmer Sprayer",
        active_ingredient: "HDPE Tank + 12V 12Ah Rechargeable Battery",
        target_diseases: ["Pesticide Application", "Foliar Fertilizer Spray"],
        disease_benefit: "Delivers uniform 0.2-0.4 MPa atomized spray pressure across 25-30 tanks per charge.",
        dosage_label: "Includes telescopic stainless lance and 4 specialized nozzles.",
        safety_guidelines: "Flush pump with clean water after spraying chemical fungicides.",
        image_icon: "fas fa-spray-can-sparkles",
        image_color: "#059669",
        trusted_retailers: [
          { platform: "KisanKraft", tag: "Direct Manufacturer", url: "https://www.kisankraft.com", delivery: "1-Year Warranty & Spares", price: 2890 },
          { platform: "Amazon Agriculture", tag: "Best Seller", url: "https://www.amazon.in", delivery: "Prime Free Delivery", price: 2920 }
        ]
      },
      {
        id: "prod-org-1",
        name: "Bio-Neem 10,000 ppm Azadirachtin EC",
        brand: "Bio-Control Agri Solutions",
        category: "Organic Products",
        price: 540,
        original_price: 650,
        pack_size: "1 Litre Bottle",
        rating: 4.9,
        reviews_count: 340,
        badge: "100% Organic & Export Safe",
        active_ingredient: "Azadirachtin 1% (10,000 ppm) Cold-Pressed Neem EC",
        target_diseases: ["Brown Plant Hopper", "Stem Borer", "Leaf Folder", "Brown Spot"],
        disease_benefit: "Zero-residue organic botanical pest repellent and fungal suppressor.",
        dosage_label: "2.0 to 3.0 ml per Litre of water (400-600 ml per acre).",
        safety_guidelines: "Waiting period: Zero days. Certified for organic rice cultivation.",
        image_icon: "fas fa-leaf",
        image_color: "#059669",
        trusted_retailers: [
          { platform: "IFFCO Bazar", tag: "Co-op Certified", url: "https://www.iffcobazar.in", delivery: "Free Rural Delivery", price: 530 },
          { platform: "BigHaat", tag: "Organic Hub", url: "https://www.bighaat.com", delivery: "3-5 Days Shipping", price: 540 }
        ]
      }
    ];

    categoryCounts = {
      "All": 5,
      "Seeds": 1,
      "Fertilizers": 1,
      "Pesticides": 1,
      "Tools & Equipment": 1,
      "Organic Products": 1
    };
    updateCategoryCountBadges(categoryCounts);
    applyFiltersAndRender();
  }

  /**
   * Submits a new product to the Online Agri Store catalog
   */
  async function submitNewProduct(e) {
    if (e && e.preventDefault) e.preventDefault();

    const name = document.getElementById("newProdName")?.value?.trim();
    const brand = document.getElementById("newProdBrand")?.value?.trim();
    const category = document.getElementById("newProdCategory")?.value;
    const price = parseFloat(document.getElementById("newProdPrice")?.value || "0");
    const origPrice = parseFloat(document.getElementById("newProdOrigPrice")?.value || String(price * 1.15));
    const packSize = document.getElementById("newProdPackSize")?.value?.trim();
    const activeIngredient = document.getElementById("newProdActiveIngredient")?.value?.trim();
    const benefit = document.getElementById("newProdBenefit")?.value?.trim();
    const platform = document.getElementById("newProdPlatform")?.value;
    const url = document.getElementById("newProdUrl")?.value?.trim();

    if (!name || !brand || !price) {
      if (window.AgriApp) AgriApp.showToast("Please fill in required fields (Name, Brand, Price).", "warning");
      return;
    }

    const payload = {
      name,
      brand,
      category,
      price,
      original_price: origPrice,
      pack_size: packSize,
      active_ingredient: activeIngredient,
      disease_benefit: benefit,
      platform,
      url,
      badge: "Verified New Input"
    };

    const submitBtn = document.getElementById("btnSubmitNewProduct");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Adding Product...`;
    }

    try {
      const res = await fetch("/api/stores/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success && data.product) {
        allProducts.unshift(data.product);
        if (categoryCounts[category] !== undefined) {
          categoryCounts[category]++;
        } else {
          categoryCounts[category] = 1;
        }
        categoryCounts["All"] = (categoryCounts["All"] || 0) + 1;
        updateCategoryCountBadges(categoryCounts);

        // Hide Modal
        const modalEl = document.getElementById("addProductModal");
        if (modalEl && typeof bootstrap !== "undefined") {
          const inst = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
          inst.hide();
        }

        // Reset Form
        const form = document.getElementById("addNewProductForm");
        if (form) form.reset();

        // Re-render
        applyFiltersAndRender();
        if (window.AgriApp) AgriApp.showToast(`Product "${name}" added to Online Agri Store catalog!`, "success");
      } else {
        if (window.AgriApp) AgriApp.showToast(data.message || "Failed to add product.", "error");
      }
    } catch (err) {
      console.error("Error adding product:", err);
      if (window.AgriApp) AgriApp.showToast("Network error while adding product.", "error");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fas fa-check-circle me-1"></i> Add Product to Catalog`;
      }
    }
  }

  // Public API
  return {
    init,
    selectCategory,
    handleSearchInput,
    clearSearchInput,
    handleSort,
    handlePriceRadio,
    handlePriceSlider,
    handleDiseaseDropdown,
    clearDiseaseFilter,
    renderCatalog: applyFiltersAndRender,
    applyFiltersAndRender,
    resetAllFilters,
    removeFilter,
    openProductModal,
    submitNewProduct
  };
})();

// Re-render when language changes
document.addEventListener("languageChanged", () => {
  if (typeof OnlineStore !== "undefined" && typeof OnlineStore.applyFiltersAndRender === "function") {
    OnlineStore.applyFiltersAndRender();
  }
});
