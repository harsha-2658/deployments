document.getElementById('domainUrl').innerText = window.location.origin;

async function generateKey() {
  const nameInput = document.getElementById('clientNameInput');
  const btn = document.getElementById('generateBtn');
  const clientName = nameInput.value.trim();

  if (!clientName) {
    alert('Please enter an Application or Developer Name.');
    return;
  }

  btn.disabled = true;
  btn.innerText = 'Generating...';

  try {
    const response = await fetch('/api/v1/generate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_name: clientName })
    });

    const data = await response.json();

    if (response.ok) {
      document.getElementById('apiKeyDisplay').value = data.api_key;
      document.getElementById('resultBox').classList.remove('hidden');
      nameInput.value = '';
    } else {
      alert('Error generating key: ' + (data.detail || 'Unknown error'));
    }
  } catch (err) {
    alert('Failed to connect to backend server.');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Generate Key';
  }
}

function copyKey() {
  const keyInput = document.getElementById('apiKeyDisplay');
  keyInput.select();
  navigator.clipboard.writeText(keyInput.value);
  alert('API Key copied to clipboard!');
}