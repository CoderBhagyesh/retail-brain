const BACKEND = "http://127.0.0.1:8000";

function showPage(id, el) {
  document.querySelectorAll(".page").forEach(p => p.classList.add("d-none"));
  document.getElementById(id).classList.remove("d-none");

  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  el.classList.add("active");
}

async function uploadFile() {
  const file = document.getElementById("csvFile").files[0];
  if (!file) return alert("Select a file");

  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BACKEND}/upload`, { method: "POST", body: form });
  const data = await res.json();

  document.getElementById("uploadStatus").innerText = JSON.stringify(data, null, 2);
}

async function loadDashboard() {
  const res = await fetch(`${BACKEND}/dashboard/metrics`);
  const data = await res.json();

  document.getElementById("totalRevenue").innerText = data.total_revenue;
  document.getElementById("topProduct").innerText = data.top_product;
  document.getElementById("slowMover").innerText = data.slow_mover;

  const list = document.getElementById("lowStockList");
  list.innerHTML = "";
  data.low_stock_products.forEach(p => {
    const li = document.createElement("li");
    li.innerText = p;
    list.appendChild(li);
  });
}

async function askCopilot() {
  const input = document.getElementById("chatInput");
  const chatBox = document.getElementById("chatBox");

  const userMsg = document.createElement("div");
  userMsg.className = "chat-msg user";
  userMsg.innerText = input.value;
  chatBox.appendChild(userMsg);

  const res = await fetch(`${BACKEND}/copilot/chat?query=${encodeURIComponent(input.value)}`, { method: "POST" });
  const data = await res.json();

  const botMsg = document.createElement("div");
  botMsg.className = "chat-msg bot";
  botMsg.innerText = data.answer;
  chatBox.appendChild(botMsg);

  chatBox.scrollTop = chatBox.scrollHeight;
  input.value = "";
}

async function getForecast() {
  const product = document.getElementById("productName").value;
  const days = document.getElementById("days").value;

  const res = await fetch(`${BACKEND}/forecast?product=${product}&days=${days}`);
  const data = await res.json();

  document.getElementById("forecastResult").innerText = JSON.stringify(data, null, 2);
}
