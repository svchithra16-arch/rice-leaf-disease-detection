/**
 * AgriVersion - Personal Analytics & Diagnostic Insights Script
 */

let diseaseChart = null;
let severityChart = null;

document.addEventListener("DOMContentLoaded", async () => {
  await AgriApp.checkAuth(true);
  loadAnalyticsData();
});

async function loadAnalyticsData() {
  try {
    const res = await fetch("/api/analytics/user-stats");
    const data = await res.json();

    if (!data.success) return;

    // Stat counters
    document.getElementById("statTotalScans").textContent = data.total_scans;
    document.getElementById("statHealthyScans").textContent = data.healthy_scans;
    document.getElementById("statDiseasedScans").textContent = data.diseased_scans;
    document.getElementById("statAvgConf").textContent = `${data.avg_confidence}%`;
    document.getElementById("statTopDisease").textContent = data.top_detected_disease;

    // Render Charts
    renderDiseaseDoughnut(data.disease_distribution);
    renderSeverityBar(data.severity_distribution);
    renderRecentScansTable(data.recent_activity);
  } catch (e) {
    console.warn("Analytics fetch error:", e);
  }
}

function renderDiseaseDoughnut(dist) {
  const ctx = document.getElementById("diseaseDoughnutChart");
  if (!ctx) return;

  const labels = Object.keys(dist);
  const values = Object.values(dist);

  if (labels.length === 0) {
    labels.push("Healthy");
    values.push(1);
  }

  const palette = [
    "#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#06b6d4", "#84cc16"
  ];

  if (diseaseChart) diseaseChart.destroy();

  diseaseChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: palette.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#0b1512'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#d1d5db', font: { family: 'Outfit', size: 12 } }
        }
      }
    }
  });
}

function renderSeverityBar(sev) {
  const ctx = document.getElementById("severityBarChart");
  if (!ctx) return;

  if (severityChart) severityChart.destroy();

  severityChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Healthy', 'Low', 'Mild', 'Moderate', 'Severe'],
      datasets: [{
        label: 'Scans',
        data: [
          sev['Healthy'] || 0,
          sev['Low'] || 0,
          sev['Mild'] || 0,
          sev['Moderate'] || 0,
          sev['Severe'] || 0
        ],
        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { color: '#9ca3af' },
          grid: { color: 'rgba(255,255,255,0.05)' }
        },
        y: {
          ticks: { color: '#9ca3af', stepSize: 1 },
          grid: { color: 'rgba(255,255,255,0.05)' }
        }
      }
    }
  });
}

function renderRecentScansTable(recent) {
  const table = document.getElementById("analyticsRecentTable");
  if (!table) return;

  if (!recent || recent.length === 0) {
    table.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No diagnostic scans recorded yet. Upload a crop leaf image on the <a href="/detect.html" class="text-emerald">Detect Disease</a> page to generate analytics.</td></tr>`;
    return;
  }

  let html = "";
  recent.forEach(r => {
    const diseaseName = AgriApp.escapeHtml(r.disease_name || "Healthy");
    const confVal = typeof r.confidence === "number" ? r.confidence.toFixed(1) : "0.0";
    const sevLevel = r.severity_level ? r.severity_level.toString() : "Healthy";
    const sevCss = sevLevel.toLowerCase().replace(/\s+/g, "_");
    const createdAt = AgriApp.escapeHtml(r.created_at || "Recently");

    html += `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            ${r.image_url ? `<img src="${r.image_url}" style="width:36px;height:36px;object-fit:cover;border-radius:6px;"/>` : '<div style="width:36px;height:36px;background:rgba(255,255,255,0.05);border-radius:6px;display:flex;align-items:center;justify-content:center;">🌾</div>'}
            <b>${diseaseName}</b>
          </div>
        </td>
        <td><b>${confVal}%</b></td>
        <td><span class="badge badge-sev-${sevCss}">${sevLevel.toUpperCase()}</span></td>
        <td><small class="text-muted">${createdAt}</small></td>
        <td class="text-end">
          ${r.report_pdf_url ? `<a href="${r.report_pdf_url}" target="_blank" class="btn btn-sm btn-agri-outline p-1"><i class="fas fa-file-pdf"></i> PDF</a>` : '-'}
        </td>
      </tr>
    `;
  });

  table.innerHTML = html;
}

