/**
 * AgriVersion - Administrator Dashboard, User Management & ML Benchmarks Script
 */

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true, true);
  loadAdminOverview();
  loadAdminUsers();
  loadAdminDiseases();
  loadAdminStores();
  loadAdminMLMetrics();
});

async function loadAdminOverview() {
  try {
    const res = await fetch("/api/admin/overview");
    const data = await res.json();
    if (!data.success) return;

    document.getElementById("adminStatUsers").textContent = data.total_users;
    document.getElementById("adminStatScans").textContent = data.total_scans;
    document.getElementById("adminStatChats").textContent = data.total_chats;
    document.getElementById("adminStatAccuracy").textContent = `${data.overall_accuracy}%`;

    // Render Global Disease Distribution Chart
    const ctx = document.getElementById("adminDiseaseDistChart");
    if (ctx && data.disease_distribution) {
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: Object.keys(data.disease_distribution),
          datasets: [{
            data: Object.values(data.disease_distribution),
            backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#f97316']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'right', labels: { color: '#9ca3af' } } }
        }
      });
    }
  } catch (e) {
    console.warn("Error loading admin overview:", e);
  }
}

async function loadAdminUsers() {
  const table = document.getElementById("adminUsersTable");
  if (!table) return;

  try {
    const res = await fetch("/api/admin/users");
    const data = await res.json();
    if (!data.success) return;

    let html = "";
    data.users.forEach(u => {
      html += `
        <tr>
          <td>
            <b>${AgriApp.escapeHtml(u.full_name)}</b><br/>
            <small class="text-muted">@${AgriApp.escapeHtml(u.username)}</small>
          </td>
          <td>${AgriApp.escapeHtml(u.email)}</td>
          <td><span class="badge ${u.role === 'admin' ? 'bg-danger' : 'bg-success'}">${u.role.toUpperCase()}</span></td>
          <td>${u.farms_count} Farms / ${u.scans_count} Scans</td>
          <td>
            <span class="badge ${u.is_active ? 'bg-success' : 'bg-secondary'}">${u.is_active ? 'Active' : 'Disabled'}</span>
          </td>
          <td class="text-end">
            <button class="btn btn-sm ${u.is_active ? 'btn-outline-warning' : 'btn-outline-success'} p-1" onclick="toggleUserStatus(${u.id})">
              ${u.is_active ? '<i class="fas fa-ban"></i> Deactivate' : '<i class="fas fa-check"></i> Activate'}
            </button>
          </td>
        </tr>
      `;
    });
    table.innerHTML = html;
  } catch (e) {
    console.warn("Error loading users:", e);
  }
}

async function toggleUserStatus(userId) {
  try {
    const res = await fetch(`/api/admin/users/${userId}/toggle-status`, { method: "PUT" });
    const data = await res.json();
    if (data.success) {
      AgriApp.showToast(data.message, "success");
      loadAdminUsers();
    } else {
      AgriApp.showToast(data.message || "Action failed.", "error");
    }
  } catch (e) {
    AgriApp.showToast("Error updating user status.", "error");
  }
}

let allDiseasesData = [];

async function loadAdminDiseases() {
  const table = document.getElementById("adminDiseasesTable");
  if (!table) return;

  try {
    const res = await fetch("/api/admin/diseases");
    const data = await res.json();
    if (!data.success) return;

    allDiseasesData = data.diseases;
    let html = "";
    data.diseases.forEach(d => {
      html += `
        <tr>
          <td>
            <b>${AgriApp.escapeHtml(d.name_en)}</b><br/>
            <small class="text-emerald"><i>${AgriApp.escapeHtml(d.scientific_name || '')}</i></small>
          </td>
          <td><span class="badge bg-dark">${AgriApp.escapeHtml(d.pathogen_type || 'Pathogen')}</span></td>
          <td><small class="text-muted">${AgriApp.escapeHtml(d.symptoms ? d.symptoms.substring(0, 75) + '...' : '')}</small></td>
          <td class="text-end">
            <button class="btn btn-sm btn-agri-outline p-1" onclick="openEditDiseaseModal(${d.id})"><i class="fas fa-edit"></i> Edit</button>
          </td>
        </tr>
      `;
    });
    table.innerHTML = html;
  } catch (e) {
    console.warn("Error loading diseases:", e);
  }
}

function openEditDiseaseModal(diseaseId) {
  const d = allDiseasesData.find(item => item.id === diseaseId);
  if (!d) return;

  document.getElementById("editDiseaseId").value = d.id;
  document.getElementById("editDiseaseName").value = d.name_en;
  document.getElementById("editDiseaseSci").value = d.scientific_name || "";
  document.getElementById("editDiseasePathogen").value = d.pathogen_type || "";
  document.getElementById("editDiseaseSymptoms").value = d.symptoms || "";
  document.getElementById("editDiseaseCauses").value = d.causes || "";
  document.getElementById("editDiseasePrevention").value = d.prevention || "";
  document.getElementById("editDiseaseManagement").value = d.management || "";

  new bootstrap.Modal(document.getElementById("editDiseaseModal")).show();
}

async function handleSaveDisease(e) {
  e.preventDefault();
  const id = document.getElementById("editDiseaseId").value;
  const sci = document.getElementById("editDiseaseSci").value.trim();
  const pathogen = document.getElementById("editDiseasePathogen").value.trim();
  const symp = document.getElementById("editDiseaseSymptoms").value.trim();
  const causes = document.getElementById("editDiseaseCauses").value.trim();
  const prev = document.getElementById("editDiseasePrevention").value.trim();
  const mgmt = document.getElementById("editDiseaseManagement").value.trim();

  try {
    const res = await fetch(`/api/admin/diseases/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scientific_name: sci,
        pathogen_type: pathogen,
        symptoms: symp,
        causes: causes,
        prevention: prev,
        management: mgmt
      })
    });
    const data = await res.json();
    if (data.success) {
      AgriApp.showToast("Disease profile updated.", "success");
      bootstrap.Modal.getInstance(document.getElementById("editDiseaseModal")).hide();
      loadAdminDiseases();
    } else {
      AgriApp.showToast(data.message || "Failed to update profile.", "error");
    }
  } catch (e) {
    AgriApp.showToast("Error updating disease profile.", "error");
  }
}

async function loadAdminMLMetrics() {
  try {
    const res = await fetch("/api/admin/ml-metrics");
    const data = await res.json();
    if (!data.success) return;

    const m = data.metrics;

    // Benchmark comparison table
    const benchTable = document.getElementById("mlBenchmarkTable");
    if (benchTable && m.benchmark_models) {
      let bHtml = "";
      for (const [modelName, stats] of Object.entries(m.benchmark_models)) {
        const isRiceNet = modelName.includes("RiceNet");
        bHtml += `
          <tr style="${isRiceNet ? 'background:rgba(16,185,129,0.15);color:#fff;border-left:3px solid #34d399;' : ''}">
            <td><b>${modelName}</b> ${isRiceNet ? '<span class="badge bg-success ms-1">Active Backbone</span>' : ''}</td>
            <td><b>${stats.accuracy}%</b></td>
            <td>${stats.precision}%</td>
            <td>${stats.recall}%</td>
            <td><b>${stats.f1_score}%</b></td>
            <td>${stats.inference_time_ms} ms</td>
            <td>${stats.parameters_m} M</td>
          </tr>
        `;
      }
      benchTable.innerHTML = bHtml;
    }

    // 20-Class metrics table
    const classTable = document.getElementById("mlClassMetricsTable");
    if (classTable && m.class_metrics) {
      let cHtml = "";
      m.class_metrics.forEach(cm => {
        cHtml += `
          <tr>
            <td><b>${cm.class_name}</b></td>
            <td>${cm.precision}%</td>
            <td>${cm.recall}%</td>
            <td><b>${cm.f1_score}%</b></td>
            <td>${cm.test_samples}</td>
          </tr>
        `;
      });
      classTable.innerHTML = cHtml;
    }
  } catch (e) {
    console.warn("Error loading ML metrics:", e);
  }
}

async function loadAdminStores() {
  const table = document.getElementById("adminStoresTable");
  if (!table) return;

  try {
    const res = await fetch("/api/stores/admin/all");
    const data = await res.json();
    if (!data.success) return;

    // Update Counters
    if (document.getElementById("adminStatTotalStores")) {
      document.getElementById("adminStatTotalStores").textContent = data.total_stores || 0;
    }
    if (document.getElementById("adminStatVerifiedStores")) {
      document.getElementById("adminStatVerifiedStores").textContent = data.verified_count || 0;
    }
    if (document.getElementById("adminStatPendingStores")) {
      document.getElementById("adminStatPendingStores").textContent = data.pending_count || 0;
    }
    if (document.getElementById("adminStatTotalProducts")) {
      document.getElementById("adminStatTotalProducts").textContent = data.total_products || 0;
    }

    if (!data.stores || data.stores.length === 0) {
      table.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No stores registered on platform.</td></tr>`;
      return;
    }

    let html = "";
    data.stores.forEach(s => {
      let statusBadge = `<span class="badge bg-success">✓ Verified</span>`;
      if (s.verification_status === "pending") {
        statusBadge = `<span class="badge bg-warning text-dark">⏳ Pending Verification</span>`;
      } else if (s.verification_status === "suspended") {
        statusBadge = `<span class="badge bg-danger">🚫 Suspended</span>`;
      } else if (s.verification_status === "rejected") {
        statusBadge = `<span class="badge bg-secondary">✖ Rejected</span>`;
      }

      html += `
        <tr>
          <td>
            <b class="text-white">${AgriApp.escapeHtml(s.store_name)}</b><br>
            <small class="text-muted"><i class="fas fa-map-marker-alt text-emerald me-1"></i>${AgriApp.escapeHtml(s.city)}, ${AgriApp.escapeHtml(s.state)} (PIN: ${AgriApp.escapeHtml(s.pincode)})</small>
          </td>
          <td>
            <b>${AgriApp.escapeHtml(s.owner_name || 'Retailer')}</b><br>
            <small class="text-muted"><i class="fas fa-phone me-1"></i>${AgriApp.escapeHtml(s.phone)}</small>
          </td>
          <td>
            <span class="badge bg-dark border border-secondary text-emerald">${s.total_products || 0} Products</span>
            <small class="text-muted d-block mt-1">${s.in_stock_count || 0} in stock &bull; Updated ${AgriApp.escapeHtml(s.inventory_freshness_text || 'Recently')}</small>
          </td>
          <td>${statusBadge}</td>
          <td class="text-end">
            <div class="dropdown d-inline-block">
              <button class="btn btn-sm btn-agri-outline dropdown-toggle py-1 px-2" type="button" data-bs-toggle="dropdown">
                Actions
              </button>
              <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
                <li><a class="dropdown-item text-success" href="javascript:void(0)" onclick="updateStoreVerificationStatus(${s.id}, 'verified')"><i class="fas fa-check-circle me-1"></i> Approve & Verify (✓)</a></li>
                <li><a class="dropdown-item text-warning" href="javascript:void(0)" onclick="updateStoreVerificationStatus(${s.id}, 'pending')"><i class="fas fa-clock me-1"></i> Set to Pending</a></li>
                <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="updateStoreVerificationStatus(${s.id}, 'suspended')"><i class="fas fa-ban me-1"></i> Suspend Store</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-info" target="_blank" href="/stores.html?store_id=${s.id}"><i class="fas fa-boxes me-1"></i> View Inventory & Map</a></li>
              </ul>
            </div>
          </td>
        </tr>
      `;
    });

    table.innerHTML = html;
  } catch (e) {
    console.warn("Error loading admin stores:", e);
  }
}

async function updateStoreVerificationStatus(storeId, newStatus) {
  try {
    const res = await fetch(`/api/stores/admin/${storeId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      AgriApp.showToast(data.message, "success");
      loadAdminStores();
      loadAdminOverview();
    } else {
      AgriApp.showToast(data.message || "Failed to update store status.", "error");
    }
  } catch (e) {
    AgriApp.showToast("Server error updating store status.", "error");
  }
}

