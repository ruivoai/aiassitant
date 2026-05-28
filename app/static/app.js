const ingestForm = document.getElementById('ingestForm');
const queryForm = document.getElementById('queryForm');
const refreshBtn = document.getElementById('refreshBtn');

async function refreshDashboard() {
  const res = await fetch('/api/dashboard');
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  document.getElementById('ingestMsg').textContent = data.message || 'Saved';
  ingestForm.reset();
  refreshDashboard();
});

queryForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = document.getElementById('question').value;
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  const data = await res.json();
  document.getElementById('queryResults').textContent = JSON.stringify(data, null, 2);
});

refreshBtn.addEventListener('click', refreshDashboard);
refreshDashboard();
