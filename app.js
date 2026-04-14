const API_BASE = "https://shift-workshop-api.onrender.com";

const form = document.getElementById("registration-form");
const submitButton = document.getElementById("btn-submit");
const errorBox = document.getElementById("form-error");
const successBox = document.getElementById("form-success");

function showError(message) {
  if (!errorBox) return;
  errorBox.textContent = String(message);
  errorBox.style.display = "block";
}

function clearError() {
  if (!errorBox) return;
  errorBox.textContent = "";
  errorBox.style.display = "none";
}

function showSuccess() {
  if (!successBox) return;
  successBox.style.display = "block";
}

function hideSuccess() {
  if (!successBox) return;
  successBox.style.display = "none";
}

if (form) {
  hideSuccess();
  clearError();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    hideSuccess();

    const payload = {
      first_name: document.getElementById("first_name")?.value.trim() || "",
      last_name: document.getElementById("last_name")?.value.trim() || "",
      email: document.getElementById("email")?.value.trim() || "",
      phone: document.getElementById("phone")?.value.trim() || "",
      production_goal: document.getElementById("production_goal")?.value.trim() || "",
      stuck: document.getElementById("stuck")?.value.trim() || "",
      questions: document.getElementById("questions")?.value.trim() || ""
    };

    if (!payload.first_name || !payload.last_name || !payload.email || !payload.phone) {
      showError("Please complete First Name, Last Name, Email Address, and Phone.");
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Submitting...";

    try {
      const response = await fetch(`${API_BASE}/api/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const rawText = await response.text();

      if (!response.ok) {
        let message = rawText || `HTTP ${response.status}`;

        try {
          const parsed = JSON.parse(rawText);

          if (typeof parsed.detail === "string") {
            message = parsed.detail;
          } else if (parsed.detail && typeof parsed.detail.message === "string") {
            message = parsed.detail.message;
          } else if (typeof parsed.message === "string") {
            message = parsed.message;
          } else {
            message = JSON.stringify(parsed);
          }
        } catch (error) {
          // keep raw text
        }

        showError(`Error ${response.status}: ${message}`);
        return;
      }

      form.reset();
      clearError();
      showSuccess();
    } catch (error) {
      showError(`Network error: ${error.message}`);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Reserve My Seat";
    }
  });
}
