/**
 * login.js
 * Handles student registration, student login, and admin login forms.
 * Stores the JWT + user info in localStorage on success and redirects.
 */

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

function showMessage(el, text, type) {
  el.textContent = text;
  el.className = `form-msg ${type}`;
}

// ---------------- Admin Registration ----------------
const adminRegisterForm = document.getElementById("adminRegisterForm");
if (adminRegisterForm) {
  adminRegisterForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msgEl = document.getElementById("formMsg");
    const submitBtn = adminRegisterForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    const payload = {
      name: document.getElementById("name").value.trim(),
      email: document.getElementById("email").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      password: document.getElementById("password").value,
    };

   try {
      const res = await fetch(`${API_BASE}/api/auth/admin-register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Admin registration failed");

      showMessage(msgEl, data.message || "Check your email to verify your account.", "success");
      adminRegisterForm.reset();
      // no redirect — the account can't log in until the email link is clicked
    } catch (err) {
      showMessage(msgEl, err.message, "error");
    } finally {
      submitBtn.disabled = false;
    }
  });
}

// ---------------- Admin Login ----------------
const adminLoginForm = document.getElementById("adminLoginForm");
if (adminLoginForm) {
  adminLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msgEl = document.getElementById("formMsg");
    const submitBtn = adminLoginForm.querySelector("button[type=submit]");
    submitBtn.disabled = true;

    const payload = {
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
    };

    try {
      const res = await fetch(`${API_BASE}/api/auth/admin-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Admin login failed");

      localStorage.setItem("admin_token", data.access_token);
      localStorage.setItem("admin_user", JSON.stringify(data.user));

      showMessage(msgEl, "Login successful! Redirecting...", "success");
      setTimeout(() => (window.location.href = "admin_dashboard.html"), 900);
    } catch (err) {
      showMessage(msgEl, err.message, "error");
      submitBtn.disabled = false;
    }
  });
}
