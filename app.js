const form = document.getElementById("registration-form");
const submitButton = document.getElementById("btn-submit");
const errorBox = document.getElementById("form-error");
const successBox = document.getElementById("form-success");

function showError(message) {
  if (!errorBox) return;
  errorBox.textContent = message;
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

    if (!form.reportValidity()) {
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Submitting...";

    try {
      const response = await fetch("/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const rawText = await response.text();
      console.log("Register response status:", response.status);
      console.log("Register response body:", rawText);

      let result = {};
      try {
        result = rawText ? JSON.parse(rawText) : {};
      } catch (e) {
        result = {};
      }

      if (!response.ok) {
        throw new Error(
          result.detail ||
          result.message ||
          rawText ||
          "Registration failed. Please try again."
        );
      }

      form.reset();
      showSuccess();
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
      showError(error.message || "Something went wrong. Please try again.");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Reserve My Seat";
    }
  });
}
