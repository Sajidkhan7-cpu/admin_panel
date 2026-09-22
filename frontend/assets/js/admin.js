/**
 * admin.js
 * Powers the admin dashboard: auth guard, stats, and CRUD for
 * courses and FAQs via the /api/admin/* endpoints.
 */

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";
const token = localStorage.getItem("admin_token");

if (!token) {
  window.location.href = "admin_login.html";
}

function authHeaders() {
  return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
}

function showError(msg) {
  const banner = document.getElementById("errorBanner");
  banner.textContent = msg;
  banner.style.display = "block";
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("admin_token");
  localStorage.removeItem("admin_user");
  window.location.href = "admin_login.html";
});

// ---------------- Dashboard stats ----------------
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/dashboard/stats`, { headers: authHeaders() });
    if (res.status === 401 || res.status === 403) {
      localStorage.removeItem("admin_token");
      window.location.href = "admin_login.html";
      return;
    }
    const data = await res.json();
    document.getElementById("statStudents").textContent = data.total_students;
    document.getElementById("statCourses").textContent = data.total_courses;
    document.getElementById("statChats").textContent = data.total_chats;
    document.getElementById("statSeats").textContent = data.total_seats_available;
  } catch (err) {
    showError("Could not load dashboard stats. Is the backend running?");
  }
}

// ---------------- Courses ----------------
let coursesCache = [];
let editingCourseId = null;

const addCourseBtn = document.getElementById("addCourseBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const courseFieldIds = ["cName", "cCode", "cDuration", "cTotalSeats", "cAvailSeats", "cFeesYear", "cAdmissionFee", "cEligibility", "cNote"];

async function loadCourses() {
  try {
    const res = await fetch(`${API_BASE}/api/courses/`);
    const courses = await res.json();
    coursesCache = courses;
    const tbody = document.getElementById("coursesTableBody");
    tbody.innerHTML = courses
      .map(
        (c) => `
      <tr>
        <td>${c.name} <span style="color:#94a3b8">(${c.short_code || ""})</span></td>
        <td>${c.available_seats}/${c.total_seats}</td>
        <td>₹${Number(c.fees_per_year).toLocaleString("en-IN")}</td>
        <td>${c.eligibility_percentage}%</td>
        <td>
          <button class="btn-small" data-id="${c.id}" data-action="edit-course">Edit</button>
          <button class="btn-small danger" data-id="${c.id}" data-action="delete-course" style="margin-left:6px">Delete</button>
        </td>
      </tr>`
      )
      .join("");
  } catch (err) {
    showError("Could not load courses.");
  }
}

function fillCourseForm(course) {
  document.getElementById("cName").value = course.name || "";
  document.getElementById("cCode").value = course.short_code || "";
  document.getElementById("cDuration").value = course.duration_years ?? "";
  document.getElementById("cTotalSeats").value = course.total_seats ?? "";
  document.getElementById("cAvailSeats").value = course.available_seats ?? "";
  document.getElementById("cFeesYear").value = course.fees_per_year ?? "";
  document.getElementById("cAdmissionFee").value = course.admission_fee ?? "";
  document.getElementById("cEligibility").value = course.eligibility_percentage ?? "";
  document.getElementById("cNote").value = course.eligibility_note || "";
}

function startEditCourse(id) {
  const course = coursesCache.find((c) => String(c.id) === String(id));
  if (!course) return;

  editingCourseId = course.id;
  fillCourseForm(course);

  addCourseBtn.textContent = "Update Course";
  cancelEditBtn.style.display = "inline-block";
  document.getElementById("cName").scrollIntoView({ behavior: "smooth", block: "center" });
}


function resetCourseForm() {
  editingCourseId = null;
  courseFieldIds.forEach((id) => (document.getElementById(id).value = ""));
  addCourseBtn.textContent = "+ Add Course";
  cancelEditBtn.style.display = "none";
}

addCourseBtn.addEventListener("click", async () => {
  const payload = {
    name: val("cName"),
    short_code: val("cCode"),
    duration_years: numVal("cDuration", 4),
    total_seats: numVal("cTotalSeats", 0),
    available_seats: numVal("cAvailSeats", 0),
    fees_per_year: numVal("cFeesYear", 0),
    total_fees: numVal("cFeesYear", 0) * numVal("cDuration", 4),
    admission_fee: numVal("cAdmissionFee", 0),
    eligibility_percentage: numVal("cEligibility", 0),
    eligibility_note: val("cNote"),
  };

  if (!payload.name) return showError("Course name is required.");

  const isEditing = editingCourseId !== null;
  const url = isEditing ? `${API_BASE}/api/admin/courses/${editingCourseId}` : `${API_BASE}/api/admin/courses`;
  const method = isEditing ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error((await res.json()).detail || `Failed to ${isEditing ? "update" : "add"} course`);
    resetCourseForm();
    loadCourses();
    loadStats();
  } catch (err) {
    showError(err.message);
  }
});

cancelEditBtn.addEventListener("click", () => {
  resetCourseForm();
});

document.getElementById("coursesTableBody").addEventListener("click", async (e) => {
  const editBtn = e.target.closest("button[data-action=edit-course]");
  if (editBtn) {
    startEditCourse(editBtn.dataset.id);
    return;
  }

  const deleteBtn = e.target.closest("button[data-action=delete-course]");
  if (deleteBtn) {
    if (!confirm("Delete this course?")) return;
    await fetch(`${API_BASE}/api/admin/courses/${deleteBtn.dataset.id}`, { method: "DELETE", headers: authHeaders() });
    if (String(editingCourseId) === deleteBtn.dataset.id) resetCourseForm();
    loadCourses();
    loadStats();
  }
});

// ---------------- FAQs ----------------
let faqsCache = [];
let editingFaqId = null;
async function loadFaqs() {
  try {
    const res = await fetch(`${API_BASE}/api/faq/`);
    const faqs = await res.json();
    faqsCache = faqs;
    const tbody = document.getElementById("faqsTableBody");
    tbody.innerHTML = faqs
      .map(
        (f) => `
      <tr>
        <td>${f.question}</td>
        <td>${f.category}</td>
        <td>
          <button class="btn-small" data-id="${f.id}" data-action="edit-faq">Edit</button>
          <button class="btn-small danger" data-id="${f.id}" data-action="delete-faq">Delete</button>
        </td>
      </tr>`
      )
      .join("");
  } catch (err) {
    showError("Could not load FAQs.");
  }
}


// Start editing FAQ
function startEditFaq(id) {
  const faq = faqsCache.find(
    (f) => String(f.id) === String(id)
  );

  if (!faq) return;

  editingFaqId = faq.id;

  document.getElementById("fQuestion").value =
    faq.question || "";

  document.getElementById("fKeywords").value =
    faq.keywords || "";

  document.getElementById("fAnswer").value =
    faq.answer || "";

  const addFaqBtn = document.getElementById("addFaqBtn");

  addFaqBtn.textContent = "Update FAQ";

  document.getElementById("fQuestion").scrollIntoView({
    behavior: "smooth",
    block: "center"
  });
}


// Reset FAQ form
function resetFaqForm() {
  editingFaqId = null;

  document.getElementById("fQuestion").value = "";
  document.getElementById("fKeywords").value = "";
  document.getElementById("fAnswer").value = "";

  document.getElementById("addFaqBtn").textContent =
    "+ Add FAQ";
}


// Add / Update FAQ
document.getElementById("addFaqBtn").addEventListener(
  "click",
  async () => {

    const payload = {
      question: val("fQuestion"),
      keywords: val("fKeywords"),
      answer: val("fAnswer"),
      category: "general",
    };

    if (!payload.question || !payload.answer) {
      return showError(
        "Question and answer are required."
      );
    }

    const isEditing = editingFaqId !== null;

    const url = isEditing
      ? `${API_BASE}/api/admin/faqs/${editingFaqId}`
      : `${API_BASE}/api/admin/faqs`;

    const method = isEditing ? "PUT" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const error = await res.json();

        throw new Error(
          error.detail ||
          `Failed to ${isEditing ? "update" : "add"} FAQ`
        );
      }

      resetFaqForm();
      loadFaqs();

    } catch (err) {
      showError(err.message);
    }
  }
);


// FAQ table buttons
document
  .getElementById("faqsTableBody")
  .addEventListener("click", async (e) => {

    // Edit FAQ
    const editBtn = e.target.closest(
      "button[data-action=edit-faq]"
    );

    if (editBtn) {
      startEditFaq(editBtn.dataset.id);
      return;
    }


    // Delete FAQ
    const deleteBtn = e.target.closest(
      "button[data-action=delete-faq]"
    );

    if (deleteBtn) {

      if (!confirm("Delete this FAQ?")) return;

      try {
        const res = await fetch(
          `${API_BASE}/api/admin/faqs/${deleteBtn.dataset.id}`,
          {
            method: "DELETE",
            headers: authHeaders()
          }
        );

        if (!res.ok) {
          const error = await res.json();

          throw new Error(
            error.detail || "Failed to delete FAQ"
          );
        }

        if (
          String(editingFaqId) ===
          String(deleteBtn.dataset.id)
        ) {
          resetFaqForm();
        }

        loadFaqs();

      } catch (err) {
        showError(err.message);
      }
    }
  });

// ---------------- Students ----------------
async function loadStudents() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/students`, { headers: authHeaders() });
    const students = await res.json();
    const tbody = document.getElementById("studentsTableBody");
    tbody.innerHTML = students
      .map(
        (s) => `<tr><td>${s.name}</td><td>${s.email}</td><td>${s.phone || "-"}</td><td>${new Date(s.created_at).toLocaleDateString()}</td></tr>`
      )
      .join("");
  } catch (err) {
    showError("Could not load students.");
  }
}

function val(id) { return document.getElementById(id).value.trim(); }
function numVal(id, fallback) {
  const v = parseFloat(document.getElementById(id).value);
  return isNaN(v) ? fallback : v;
}

loadStats();
loadCourses();
loadFaqs();
loadStudents();