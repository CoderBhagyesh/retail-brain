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
    appendMessage("assistant", data.answer || "I could not generate a response.");
  } catch (error) {
    appendMessage("assistant", "Unable to reach the copilot service right now. Please try again.");
  }
}

async function getForecast() {
  const product = document.getElementById("productName").value;
  const days = document.getElementById("days").value;

  const res = await fetch(`${BACKEND}/forecast?product=${product}&days=${days}`);
  const data = await res.json();

  document.getElementById("forecastResult").innerText = JSON.stringify(data, null, 2);
}
