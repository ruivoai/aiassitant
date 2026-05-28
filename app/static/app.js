const loginForm = document.getElementById('loginForm');
const ingestForm = document.getElementById('ingestForm');
const queryForm = document.getElementById('queryForm');
const refreshBtn = document.getElementById('refreshBtn');

function getToken() {
  return localStorage.getItem('access_token');
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(loginForm);
  const body = new URLSearchParams();
  body.set('username', form.get('username'));
  body.set('password', form.get('password'));

  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  });
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem('access_token', data.access_token);
    document.getElementById('authMsg').textContent = 'Authenticated.';
    refreshDashboard();
  } else {
    document.getElementById('authMsg').textContent = data.detail || 'Login failed';
  }
});

async function refreshDashboard() {
  const res = await fetch('/api/dashboard', { headers: { ...authHeaders() } });
  const data = await res.json();
  document.getElementById('dashboard').textContent = JSON.stringify(data, null, 2);
}

ingestForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(ingestForm);
  const tagsRaw = form.get('tags') || '';
  const payload = {
    source: form.get('source'),
    title: form.get('title'),
    content: form.get('content'),
    tags: tagsRaw.split(',').map((s) => s.trim()).filter(Boolean),
    event_date: form.get('event_date') || null
  };

  const res = await fetch('/api/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  document.getElementById('ingestMsg').textContent = data.message || data.detail || 'Saved';
  if (res.ok) {
    ingestForm.reset();
    refreshDashboard();
  }
});

queryForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = document.getElementById('question').value;
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ question })
  });
  const data = await res.json();
  document.getElementById('queryResults').textContent = JSON.stringify(data, null, 2);
});

refreshBtn.addEventListener('click', refreshDashboard);
