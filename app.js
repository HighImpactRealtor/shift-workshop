/* ============================================
   THE SHIFT WORKSHOP — Frontend Logic
   ============================================ */

// API base — works both locally and after deploy
const API = 'https://shift-workshop-api.onrender.com';

// Dark mode toggle
(function () {
  const t = document.querySelector('[data-theme-toggle]');
  const r = document.documentElement;
  let d = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  r.setAttribute('data-theme', d);
  t &&
    t.addEventListener('click', () => {
      d = d === 'dark' ? 'light' : 'dark';
      r.setAttribute('data-theme', d);
      t.setAttribute('aria-label', 'Switch to ' + (d === 'dark' ? 'light' : 'dark') + ' mode');
      t.innerHTML =
        d === 'dark'
          ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    });
})();

// Registration form
(function () {
  const form = document.getElementById('registration-form');
  const btn = document.getElementById('btn-submit');
  const errorEl = document.getElementById('form-error');
  const successEl = document.getElementById('form-success');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.classList.remove('active');
    errorEl.textContent = '';

    // Basic validation
    const firstName = form.first_name.value.trim();
    const lastName = form.last_name.value.trim();
    const email = form.email.value.trim();
    const phone = form.phone.value.trim();

    if (!firstName || !lastName || !email) {
      showError('Please fill in your first name, last name, and email.');
      return;
    }

    if (!isValidEmail(email)) {
      showError('Please enter a valid email address.');
      return;
    }

    // Submit
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Registering...';

    try {
      const res = await fetch(`${API}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email,
          phone: phone || ''
        })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed. Please try again.');
      }

      // Success
      form.classList.add('hidden');
      successEl.classList.add('active');

    } catch (err) {
      showError(err.message || 'Something went wrong. Please try again or email larkin@highimpactrealtor.com directly.');
      btn.disabled = false;
      btn.innerHTML = 'Reserve My Seat';
    }
  });

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('active');
    errorEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
})();

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
