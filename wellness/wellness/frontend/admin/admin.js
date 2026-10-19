// --- Auth ---
async function checkAuth() {
  const res = await fetch("/api/admin/check");
  const data = await res.json();
  if (data.is_admin) {
    showDashboard();
  }
}

async function doLogin() {
  const password = document.getElementById("passwordInput").value;
  const errEl = document.getElementById("loginError");
  errEl.textContent = "";
  try {
    const res = await fetch("/api/admin/login", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password})
    });
    const data = await res.json();
    if (data.ok) {
      showDashboard();
    } else {
      errEl.textContent = data.error || "Incorrect password";
    }
  } catch (err) {
    errEl.textContent = "Could not reach the server.";
  }
}

async function doLogout() {
  await fetch("/api/admin/logout", {method: "POST"});
  document.getElementById("dashboard").style.display = "none";
  document.getElementById("loginScreen").style.display = "flex";
  document.getElementById("passwordInput").value = "";
}

function showDashboard() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("dashboard").style.display = "block";
  switchTab("analytics");
}

// --- Tabs ---
window.CENTERS_CACHE = [];

function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  document.getElementById("tabAnalytics").style.display = tab === "analytics" ? "block" : "none";
  document.getElementById("tabCenters").style.display = tab === "centers" ? "block" : "none";
  document.getElementById("tabFlags").style.display = tab === "flags" ? "block" : "none";
  if (tab === "analytics") loadAnalytics();
  if (tab === "centers") loadCenters();
  if (tab === "flags") loadFlags();
}

// --- Analytics ---
async function loadAnalytics() {
  const panel = document.getElementById("tabAnalytics");
  panel.innerHTML = `<div class="no-data">Loading...</div>`;
  const res = await fetch("/api/admin/analytics");
  const d = await res.json();

  const catMax = Math.max(...Object.values(d.category_counts));
  const doshaMax = Math.max(...Object.values(d.dosha_counts));

  let html = `
    <div class="stat-grid">
      <div class="stat-card"><div class="num">${d.total_centers}</div><div class="lbl">Total Centers</div></div>
      <div class="stat-card"><div class="num">${d.avg_quality_score}/5</div><div class="lbl">Avg Quality Score</div></div>
      <div class="stat-card"><div class="num">${d.centers_with_flags}</div><div class="lbl">Centers w/ Flagged Reviews</div></div>
      <div class="stat-card"><div class="num">${d.total_flagged_reviews}</div><div class="lbl">Total Flagged Reviews</div></div>
    </div>

    <div class="section-title">Centers by Category</div>
    ${Object.entries(d.category_counts).map(([k,v]) => `
      <div class="bar-row"><span class="bar-label">${k}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(v/catMax*100)}%"></div></div>
        <span class="bar-val">${v}</span></div>
    `).join("")}

    <div class="section-title">Centers by Dosha Focus</div>
    ${Object.entries(d.dosha_counts).map(([k,v]) => `
      <div class="bar-row"><span class="bar-label">${k}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(v/doshaMax*100)}%"></div></div>
        <span class="bar-val">${v}</span></div>
    `).join("")}
  `;

  if (d.model_comparison) {
    html += `
      <div class="section-title">Dosha Classifier - Model Comparison (Development Evaluation)</div>
      <table class="model-table"><thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1-Score</th></tr></thead><tbody>
      ${d.model_comparison.map(m => `<tr><td>${m.Model}</td><td>${m.Accuracy}</td><td>${m.Precision}</td><td>${m.Recall}</td><td>${m["F1-Score"]}</td></tr>`).join("")}
      </tbody></table>
    `;
  }

  if (d.ablation_study) {
    html += `
      <div class="section-title">Ablation Study - Component Contribution (Development Evaluation)</div>
      <table class="data-table"><thead><tr><th>Configuration</th><th>Avg Quality</th><th>Budget Alignment</th><th>Dosha Compatibility</th></tr></thead><tbody>
      ${Object.entries(d.ablation_study).map(([k,v]) => `<tr><td>${k}</td><td>${v.avg_quality}</td><td>${(v.budget_alignment*100).toFixed(1)}%</td><td>${(v.dosha_compatibility*100).toFixed(1)}%</td></tr>`).join("")}
      </tbody></table>
    `;
  }

  panel.innerHTML = html;
}

// --- Centers CRUD ---
async function loadCenters() {
  const panel = document.getElementById("tabCenters");
  panel.innerHTML = `<div class="no-data">Loading...</div>`;
  const res = await fetch("/api/admin/centers");
  const data = await res.json();
  window.CENTERS_CACHE = data.centers;
  renderCentersTable("");
}

function renderCentersTable(filter) {
  const panel = document.getElementById("tabCenters");
  const f = (filter || "").toLowerCase();
  const filtered = window.CENTERS_CACHE
    .map((c, i) => ({...c, _idx: i}))
    .filter(c => c.name.toLowerCase().includes(f) || (c.district || "").toLowerCase().includes(f));

  let rows = filtered.map(c => `
    <tr>
      <td>${c.name}</td>
      <td>${c.category}</td>
      <td>${c.district || "-"}</td>
      <td><span class="badge ${c.verified && c.verified.toLowerCase().includes('yes') ? 'verified' : 'pending'}">${c.verified || "Unverified"}</span></td>
      <td>${c.nlp_quality}/5</td>
      <td class="actions">
        <button class="btn-secondary" onclick="openEditModal(${c._idx})">Edit</button>
        <button class="btn-danger" onclick="deleteCenter(${c._idx})">Delete</button>
      </td>
    </tr>
  `).join("");

  panel.innerHTML = `
    <div class="toolbar">
      <input type="text" class="search-input" placeholder="Search centers..." value="${filter || ''}" oninput="renderCentersTable(this.value)">
      <button class="btn-primary" style="width:auto;" onclick="openAddModal()">+ Add Center</button>
    </div>
    <table class="data-table">
      <thead><tr><th>Name</th><th>Category</th><th>District</th><th>Status</th><th>Quality</th><th>Actions</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="6" class="no-data">No centers match your search.</td></tr>'}</tbody>
    </table>
  `;
}

async function deleteCenter(idx) {
  const c = window.CENTERS_CACHE[idx];
  if (!confirm(`Delete "${c.name}"? This cannot be undone.`)) return;
  await fetch(`/api/admin/centers/${idx}`, {method: "DELETE"});
  loadCenters();
}

// --- Edit/Add Modal ---
window.MODAL_MODE = null; // "edit" | "add"
window.MODAL_IDX = null;

function fieldHtml(label, id, value, type) {
  value = value || "";
  if (type === "textarea") {
    return `<div class="modal-field"><label>${label}</label><textarea id="${id}" rows="2">${value}</textarea></div>`;
  }
  return `<div class="modal-field"><label>${label}</label><input type="text" id="${id}" value="${value}"></div>`;
}

function openEditModal(idx) {
  window.MODAL_MODE = "edit";
  window.MODAL_IDX = idx;
  const c = window.CENTERS_CACHE[idx];
  document.getElementById("modalTitle").textContent = "Edit Center";
  document.getElementById("modalForm").innerHTML =
    fieldHtml("Name", "f_name", c.name) +
    fieldHtml("Category", "f_category", c.category) +
    fieldHtml("District", "f_district", c.district) +
    fieldHtml("Price Tier", "f_price_tier", c.price_tier) +
    fieldHtml("Verification Status", "f_verified", c.verified) +
    fieldHtml("Notes", "f_notes", c.notes, "textarea") +
    fieldHtml("Specializations", "f_conditions_text", c.conditions_text, "textarea");
  document.getElementById("editModal").style.display = "flex";
}

function openAddModal() {
  window.MODAL_MODE = "add";
  window.MODAL_IDX = null;
  document.getElementById("modalTitle").textContent = "Add New Center";
  document.getElementById("modalForm").innerHTML =
    fieldHtml("Name", "f_name", "") +
    fieldHtml("Category", "f_category", "Curative") +
    fieldHtml("District", "f_district", "") +
    fieldHtml("Price Tier", "f_price_tier", "Mid") +
    fieldHtml("Verification Status", "f_verified", "Needs verification") +
    fieldHtml("Notes", "f_notes", "", "textarea") +
    fieldHtml("Specializations", "f_conditions_text", "", "textarea");
  document.getElementById("editModal").style.display = "flex";
}

function closeModal() {
  document.getElementById("editModal").style.display = "none";
}

async function saveModal() {
  const payload = {
    name: document.getElementById("f_name").value,
    category: document.getElementById("f_category").value,
    district: document.getElementById("f_district").value,
    price_tier: document.getElementById("f_price_tier").value,
    verified: document.getElementById("f_verified").value,
    notes: document.getElementById("f_notes").value,
    conditions_text: document.getElementById("f_conditions_text").value,
  };
  if (window.MODAL_MODE === "edit") {
    await fetch(`/api/admin/centers/${window.MODAL_IDX}`, {
      method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
    });
  } else {
    await fetch(`/api/admin/centers`, {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
    });
  }
  closeModal();
  loadCenters();
}

// --- Flagged Reviews ---
async function loadFlags() {
  const panel = document.getElementById("tabFlags");
  panel.innerHTML = `<div class="no-data">Loading...</div>`;
  const res = await fetch("/api/admin/flagged-reviews");
  const data = await res.json();

  if (data.flagged.length === 0) {
    panel.innerHTML = `<div class="no-data">No flagged reviews found across any center.</div>`;
    return;
  }

  panel.innerHTML = data.flagged.map(f => `
    <div class="flag-card">
      <h4>${f.name}</h4>
      <div class="meta">${f.category} &middot; ${f.district || "District not set"} &middot; ${f.flagged_reviews.length} of ${f.total_reviews} reviews flagged</div>
      ${f.flagged_reviews.map(r => `<div class="flag-review">"${r}"</div>`).join("")}
    </div>
  `).join("");
}

checkAuth();
