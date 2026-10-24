/**
 * AgriVersion - Farm & Field Management Script
 */

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true);
  loadFarms();
});

async function loadFarms() {
  const container = document.getElementById("farmsContainer");
  if (!container) return;

  try {
    const res = await fetch("/api/farms");
    const data = await res.json();

    if (!data.farms || data.farms.length === 0) {
      container.innerHTML = `
        <div class="glass-card text-center p-5">
          <i class="fas fa-tractor fa-3x text-emerald mb-3"></i>
          <h4 data-i18n="farms.no_farms">No farms registered yet.</h4>
          <p class="text-muted">Register your paddy fields to associate AI disease scans and track field health.</p>
          <button class="btn-agri-primary mt-2" data-bs-toggle="modal" data-bs-target="#addFarmModal" data-i18n="farms.add_farm_btn">+ Add New Farm</button>
        </div>
      `;
      return;
    }

    let html = "";
    data.farms.forEach(farm => {
      let fieldsHtml = "";
      if (farm.fields && farm.fields.length > 0) {
        farm.fields.forEach(f => {
          fieldsHtml += `
            <div class="d-flex align-items-center justify-content-between p-2 mb-2 rounded" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05)">
              <div>
                <b class="text-white">${AgriApp.escapeHtml(f.name)}</b>
                <div style="font-size:0.82rem;" class="text-muted">
                  <span class="badge bg-dark me-2">${AgriApp.escapeHtml(f.crop_variety)}</span>
                  ${f.sowing_date ? 'Sown: ' + f.sowing_date : ''}
                </div>
              </div>
              <div class="d-flex align-items-center gap-2">
                <span class="badge bg-success" style="font-size:0.75rem;">${f.scans_count} scans</span>
                <button class="btn btn-sm btn-outline-danger p-1" title="Delete Field" onclick="deleteField(${f.id})"><i class="fas fa-trash"></i></button>
              </div>
            </div>
          `;
        });
      } else {
        fieldsHtml = `<div class="text-muted text-center py-2" style="font-size:0.85rem;">No fields added yet.</div>`;
      }

      html += `
        <div class="col-md-6 mb-4">
          <div class="glass-card h-100">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h4 class="text-white mb-1">🌾 ${AgriApp.escapeHtml(farm.name)}</h4>
                <small class="text-emerald"><i class="fas fa-map-marker-alt me-1"></i>${AgriApp.escapeHtml(farm.location)}</small>
              </div>
              <button class="btn btn-sm btn-outline-danger p-1" title="Delete Farm" onclick="deleteFarm(${farm.id})"><i class="fas fa-trash"></i></button>
            </div>

            <div class="row text-center py-2 mb-3 rounded" style="background:rgba(16,185,129,0.08);">
              <div class="col-6 border-end" style="border-color:rgba(255,255,255,0.1) !important;">
                <small class="text-muted" data-i18n="farms.total_area">Total Area</small>
                <div class="fw-bold text-white fs-6">${farm.total_area} Acres</div>
              </div>
              <div class="col-6">
                <small class="text-muted" data-i18n="farms.soil_type">Soil Type</small>
                <div class="fw-bold text-white fs-6">${AgriApp.escapeHtml(farm.soil_type)}</div>
              </div>
            </div>

            <div class="d-flex justify-content-between align-items-center mb-2">
              <h6 class="text-muted mb-0"><i class="fas fa-layer-group me-1 text-emerald"></i> Fields / Plots (${farm.fields ? farm.fields.length : 0})</h6>
              <button class="btn btn-sm btn-agri-outline py-1 px-2" style="font-size:0.8rem;" onclick="openAddFieldModal(${farm.id})">+ Add Field</button>
            </div>

            <div class="fields-list mt-2">
              ${fieldsHtml}
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (e) {
    console.error("Error loading farms:", e);
  }
}

async function handleCreateFarm(e) {
  e.preventDefault();
  const name = document.getElementById("farmNameInput").value.trim();
  const location = document.getElementById("farmLocationInput").value.trim();
  const area = document.getElementById("farmAreaInput").value;
  const soil = document.getElementById("farmSoilInput").value.trim();

  try {
    const res = await fetch("/api/farms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, location, total_area: area, soil_type: soil })
    });
    const data = await res.json();
    if (data.success) {
      AgriApp.showToast("Farm registered successfully.", "success");
      bootstrap.Modal.getInstance(document.getElementById("addFarmModal")).hide();
      document.getElementById("addFarmForm").reset();
      loadFarms();
    } else {
      AgriApp.showToast(data.message || "Failed to create farm.", "error");
    }
  } catch (err) {
    AgriApp.showToast("Error creating farm.", "error");
  }
}

function openAddFieldModal(farmId) {
  document.getElementById("fieldTargetFarmId").value = farmId;
  new bootstrap.Modal(document.getElementById("addFieldModal")).show();
}

async function handleCreateField(e) {
  e.preventDefault();
  const farmId = document.getElementById("fieldTargetFarmId").value;
  const name = document.getElementById("fieldNameInput").value.trim();
  const variety = document.getElementById("fieldVarietyInput").value.trim();
  const date = document.getElementById("fieldSowingDateInput").value;
  const notes = document.getElementById("fieldNotesInput").value.trim();

  try {
    const res = await fetch(`/api/farms/${farmId}/fields`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, crop_variety: variety, sowing_date: date, notes })
    });
    const data = await res.json();
    if (data.success) {
      AgriApp.showToast("Field added successfully.", "success");
      bootstrap.Modal.getInstance(document.getElementById("addFieldModal")).hide();
      document.getElementById("addFieldForm").reset();
      loadFarms();
    } else {
      AgriApp.showToast(data.message || "Failed to add field.", "error");
    }
  } catch (err) {
    AgriApp.showToast("Error adding field.", "error");
  }
}

async function deleteFarm(farmId) {
  if (!confirm("Are you sure you want to delete this farm and all its associated fields?")) return;
  try {
    await fetch(`/api/farms/${farmId}`, { method: "DELETE" });
    AgriApp.showToast("Farm deleted.", "success");
    loadFarms();
  } catch (e) {
    AgriApp.showToast("Error deleting farm.", "error");
  }
}

async function deleteField(fieldId) {
  if (!confirm("Delete this field?")) return;
  try {
    await fetch(`/api/farms/fields/${fieldId}`, { method: "DELETE" });
    AgriApp.showToast("Field deleted.", "success");
    loadFarms();
  } catch (e) {
    AgriApp.showToast("Error deleting field.", "error");
  }
}

async function detectFarmLocation() {
  const input = document.getElementById("farmLocationInput");
  if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
    AgriApp.showToast("Detecting your live farm location...", "info");
  }
  try {
    const loc = await AgriApp.getLiveLocation(true, true);
    if (loc && input) {
      input.value = `${loc.city}, ${loc.state}`;
      if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
        AgriApp.showToast(`Location set to: ${loc.city}, ${loc.state}`, "success");
      }
    }
  } catch (e) {
    if (typeof AgriApp !== "undefined" && AgriApp.showToast) {
      AgriApp.showToast("Could not detect location. Please type manually.", "warning");
    }
  }
}
