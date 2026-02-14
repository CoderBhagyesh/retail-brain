const BACKEND = "http://127.0.0.1:8000";

function showPage(id, el) {
  document.querySelectorAll(".page").forEach(p => p.classList.add("d-none"));
  document.getElementById(id).classList.remove("d-none");

  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  el.classList.add("active");

  if (id === "forecast") {
    loadProductOptions();
  }

  if (id === "dashboard") {
    loadDashboard();
  }
}

async function uploadFile() {
  const file = document.getElementById("csvFile").files[0];
  if (!file) return alert("Select a file");

  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BACKEND}/upload`, { method: "POST", body: form });
  const data = await res.json();

  const statusDiv = document.getElementById("uploadStatus");
  statusDiv.innerHTML = `
    <div class="alert alert-info mt-3">
      <strong>Message:</strong> ${data.message}
    </div>
    <div class="alert alert-success">
      <strong>Rows Processed:</strong> ${data.rows}
    </div>
  `;

  loadProductOptions();
}

async function loadDashboard() {
  const res = await fetch(`${BACKEND}/dashboard/metrics`);
  const data = await res.json();

  if (data.error) {
    document.getElementById("topProductsList").innerHTML = `<div class="metric-item"><span class="metric-item-title text-danger">${data.error}</span></div>`;
    return;
  }

  const overview = data.overview || {};
  const leaders = data.leaders || {};
  const inventory = data.inventory || {};
  const highlights = data.highlights || {};

  document.getElementById("totalRevenue").innerText = formatCurrency(overview.total_revenue || 0);
  document.getElementById("totalUnits").innerText = formatNumber(overview.total_units_sold || 0);
  document.getElementById("productCount").innerText = formatNumber(overview.total_products || 0);

  const trend = Number(overview.sales_trend_pct || 0);
  document.getElementById("salesTrend").innerHTML = `${trend >= 0 ? "+" : ""}${trend.toFixed(1)}%`;
  document.getElementById("salesTrend").classList.toggle("text-success", trend >= 0);
  document.getElementById("salesTrend").classList.toggle("text-danger", trend < 0);

  const top = leaders.top_product || {};
  const slow = leaders.slow_product || {};
  document.getElementById("topProduct").innerText = top.name || "--";
  document.getElementById("slowMover").innerText = slow.name || "--";
  document.getElementById("topProductMeta").innerText = `Units: ${formatNumber(top.units_sold || 0)} | Revenue: ${formatCurrency(top.revenue || 0)}`;
  document.getElementById("slowMoverMeta").innerText = `Units: ${formatNumber(slow.units_sold || 0)} | Revenue: ${formatCurrency(slow.revenue || 0)}`;

  const topProductsList = document.getElementById("topProductsList");
  topProductsList.innerHTML = "";
  (data.top_products || []).forEach(item => {
    topProductsList.innerHTML += `
      <div class="metric-item">
        <div>
          <div class="metric-item-title">${item.name}</div>
          <div class="metric-item-meta">${formatNumber(item.units_sold)} units sold</div>
        </div>
        <div class="metric-item-meta">${formatCurrency(item.revenue)}</div>
      </div>
    `;
  });
  if ((data.top_products || []).length === 0) {
    topProductsList.innerHTML = `<div class="metric-item"><span class="metric-item-meta">No product data available.</span></div>`;
  }

  const stockHealth = inventory.stock_health || {};
  document.getElementById("criticalStockCount").innerText = stockHealth.critical || 0;
  document.getElementById("warningStockCount").innerText = stockHealth.warning || 0;
  document.getElementById("healthyStockCount").innerText = stockHealth.healthy || 0;

  const lowStockList = document.getElementById("lowStockList");
  lowStockList.innerHTML = "";
  (inventory.alerts || []).forEach(item => {
    lowStockList.innerHTML += `
      <div class="metric-item">
        <span class="metric-item-title">${item.name}</span>
        <span class="metric-item-meta">${item.stock} units left</span>
      </div>
    `;
  });
  if ((inventory.alerts || []).length === 0) {
    lowStockList.innerHTML = `<div class="metric-item"><span class="metric-item-meta">No critical stock alerts.</span></div>`;
  }

  const bestDay = highlights.best_day;
  document.getElementById("bestDay").innerText = bestDay
    ? `Best day: ${bestDay.date} (${formatCurrency(bestDay.revenue)})`
    : "Best day: --";
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(value || 0));
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function appendMessage(role, message) {
  const chatBox = document.getElementById("chatBox");

  const wrapper = document.createElement("div");
  wrapper.className = `chat ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerHTML = role === "user"
    ? '<i class="bi bi-person-fill"></i>'
    : '<i class="bi bi-stars"></i>';

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerText = message;

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function askCopilot() {
  const input = document.getElementById("chatInput");
  const query = input.value.trim();

  if (!query) return;

  appendMessage("user", query);
  input.value = "";

  try {
    const res = await fetch(`${BACKEND}/copilot/chat?query=${encodeURIComponent(query)}`, { method: "POST" });
    const data = await res.json();
    console.log("Copilot response:", data);
    appendMessage("assistant", data.answer || "I could not generate a response.");
  } catch (error) {
    appendMessage("assistant", "Unable to reach the copilot service right now. Please try again.");
  }
}

async function getForecast() {
  const product = document.getElementById("productName").value;
  const days = document.getElementById("days").value;
  const leadTimeDays = document.getElementById("leadTimeDays").value;
  const serviceLevel = document.getElementById("serviceLevel").value;

  if (!product.trim()) return alert("Enter product name");

  const res = await fetch(
    `${BACKEND}/forecast?product=${encodeURIComponent(product)}&days=${encodeURIComponent(days)}&lead_time_days=${encodeURIComponent(leadTimeDays)}&service_level=${encodeURIComponent(serviceLevel)}`
  );
  const data = await res.json();

  const resultDiv = document.getElementById("forecastResult");

  if (data.error) {
    resultDiv.innerHTML = `<p class="text-danger"><i class="bi bi-exclamation-circle"></i> ${data.error}</p>`;
    return;
  }

  const summary = data.summary || {};
  const accuracy = data.accuracy || {};
  const risk = summary.stockout_risk || "unknown";
  const riskClass = risk === "high" ? "text-danger" : risk === "medium" ? "text-warning" : "text-success";
  const coverText = summary.estimated_days_of_cover === null ? "N/A" : `${summary.estimated_days_of_cover} days`;

  let html = `
    <div class="forecast-summary mb-3">
      <div class="row g-3">
        <div class="col-md-3 col-6">
          <small class="text-muted">Average Daily Sales</small>
          <div class="fw-bold">${summary.avg_daily_demand ?? 0}</div>
        </div>
        <div class="col-md-3 col-6">
          <small class="text-muted">Current Stock</small>
          <div class="fw-bold">${summary.current_stock ?? 0}</div>
        </div>
        <div class="col-md-3 col-6">
          <small class="text-muted">When To Reorder (units)</small>
          <div class="fw-bold">${summary.reorder_point ?? 0}</div>
        </div>
        <div class="col-md-3 col-6">
          <small class="text-muted">Suggested Order (units)</small>
          <div class="fw-bold">${summary.suggested_order_qty ?? 0}</div>
        </div>
      </div>
    </div>

    <div class="alert alert-light border mb-3">
      <div><strong>Stockout Risk:</strong> <span class="${riskClass} text-capitalize">${risk}</span></div>
      <div><strong>Days Until Stock Runs Out:</strong> ${coverText}</div>
      <div><strong>Expected Sales (next ${data.forecast_days} days):</strong> ${summary.total_forecast_demand ?? 0}</div>
      <div><strong>Method Used:</strong> ${data.model} | <strong>Typical Error:</strong> ${accuracy.mae ?? 0} units</div>
    </div>

    <table class="table table-sm table-bordered">
      <thead class="bg-light">
        <tr>
          <th>Date</th>
          <th>Forecast</th>
          <th>Low Estimate</th>
          <th>High Estimate</th>
        </tr>
      </thead>
      <tbody>
  `;

  for (const row of (data.daily_forecast || [])) {
    html += `
      <tr>
        <td><strong>${row.date}</strong></td>
        <td><strong>${row.forecast}</strong></td>
        <td>${row.lower}</td>
        <td>${row.upper}</td>
      </tr>
    `;
  }

  html += `
      </tbody>
    </table>
    <small class="text-muted">Safety Level: ${(Number(data.service_level || 0) * 100).toFixed(0)}% | Supplier Delivery Days: ${data.lead_time_days} days</small>
  `;

  resultDiv.innerHTML = html;
}

async function loadProductOptions() {
  const list = document.getElementById("productList");
  if (!list) return;

  try {
    const res = await fetch(`${BACKEND}/products`);
    const data = await res.json();

    list.innerHTML = "";
    (data.products || []).forEach(name => {
      const option = document.createElement("option");
      option.value = name;
      list.appendChild(option);
    });
  } catch (error) {
    console.error("Unable to load product list", error);
  }
}
