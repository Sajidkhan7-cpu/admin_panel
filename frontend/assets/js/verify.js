/**
 * verify.js
 * Handles the admin email verification link (verify.html?token=...).
 */
const API_BASE = window.location.port === "8080" ? "" : "http://localhost:8080";

const subEl = document.getElementById("verifySub");
const msgEl = document.getElementById("verifyMsg");
const token = new URLSearchParams(window.location.search).get("token");

function showMessage(el, text, type) {
  el.textContent = text;
  el.className = `form-msg ${type}`;
}

if (!token) {
  subEl.textContent = "";
  showMessage(msgEl, "Missing verification token in the link.", "error");
} else {
  fetch(`${API_BASE}/api/auth/verify-email?token=${encodeURIComponent(token)}`)
    .then(async (res) => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Verification failed");

      subEl.textContent = "";
      showMessage(msgEl, `${data.message} Redirecting to login...`, "success");
      setTimeout(() => (window.location.href = "admin_login.html"), 1800);
    })
    .catch((err) => {
      subEl.textContent = "";
      showMessage(msgEl, err.message, "error");
    });
}