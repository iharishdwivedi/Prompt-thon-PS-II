// ── Tab Switching ─────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');

    if (tab.dataset.tab === 'registry') loadReportCount();
  });
});

// ── Hash Generation ───────────────────────────────────────────
async function generateHash() {
  const file = document.getElementById('floorImage').files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target.result.split(',')[1] || e.target.result;

    try {
      const res  = await fetch('/api/hash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: base64 })
      });
      const data = await res.json();
      document.getElementById('hashValue').textContent = data.floor_hash;
      document.getElementById('hashValue').style.color = '#a78bfa';
    } catch (err) {
      document.getElementById('hashValue').textContent = 'Error generating hash';
    }
  };
  reader.readAsDataURL(file);
}

// ── Store Report ──────────────────────────────────────────────
async function storeReport() {
  const hashVal = document.getElementById('hashValue').textContent;
  if (!hashVal || hashVal === 'Upload image to generate hash') {
    showResult('storeResult', 'error', '⚠️ Please upload a floor plan image first to generate its hash.');
    return;
  }

  const payload = {
    floor_hash:          hashVal,
    outer_walls:         parseInt(document.getElementById('outerWalls').value) || 0,
    spine_walls:         parseInt(document.getElementById('spineWalls').value) || 0,
    partitions:          parseInt(document.getElementById('partitions').value) || 0,
    top_material_outer:  document.getElementById('matOuter').value,
    top_material_spine:  document.getElementById('matSpine').value,
    top_material_part:   document.getElementById('matPart').value,
    top_material_slab:   document.getElementById('matSlab').value,
    top_material_col:    document.getElementById('matCol').value,
    report_summary:      document.getElementById('reportSummary').value.substring(0, 200),
  };

  showResult('storeResult', 'loading', '<span class="spinner"></span> Anchoring report on Stellar blockchain...');

  try {
    const res  = await fetch('/api/store_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      const compliance = data.compliance
        ? '✅ <strong>COMPLIANT</strong> — Load-bearing walls ≥ partitions'
        : '⚠️ <strong>REVIEW NEEDED</strong> — Insufficient load-bearing walls';

      showResult('storeResult', 'success', `
        ✅ <strong>Report anchored on Stellar blockchain!</strong><br><br>
        🔐 <strong>Floor Hash:</strong> <code>${data.floor_hash}</code><br>
        ⛓ <strong>Transaction:</strong> <code>${data.tx_hash || 'Confirmed'}</code><br>
        🏗 <strong>Structural Compliance:</strong> ${compliance}<br><br>
        <a href="https://stellar.expert/explorer/testnet/tx/${data.tx_hash}"
           target="_blank" style="color:#67e8f9">View transaction on Stellar Explorer ↗</a>
      `);

      // Auto-fill verify and ownership tabs
      document.getElementById('verifyHash').value = data.floor_hash;
      document.getElementById('ownerHash').value  = data.floor_hash;
    } else {
      showResult('storeResult', 'error', `❌ Error: ${data.error}`);
    }
  } catch (err) {
    showResult('storeResult', 'error', `❌ Network error: ${err.message}`);
  }
}

// ── Verify Report ─────────────────────────────────────────────
async function verifyReport() {
  const hash = document.getElementById('verifyHash').value.trim();
  if (!hash) {
    showResult('verifyResult', 'error', '⚠️ Please enter a floor plan hash.');
    return;
  }

  showResult('verifyResult', 'loading', '<span class="spinner"></span> Fetching audit certificate from blockchain...');

  try {
    const res  = await fetch(`/api/get_report/${hash}`);
    const data = await res.json();

    if (data.success) {
      showResult('verifyResult', 'success', `
        🔐 <strong>Audit Certificate Found</strong><br><br>
        <strong>Floor Hash:</strong> <code>${hash}</code><br>
        <strong>Status:</strong> ✅ Verified on Stellar Testnet<br><br>
        <pre>${JSON.stringify(data.report, null, 2)}</pre>
      `);
    } else {
      showResult('verifyResult', 'error', `❌ ${data.error || 'Report not found for this hash.'}`);
    }
  } catch (err) {
    showResult('verifyResult', 'error', `❌ Network error: ${err.message}`);
  }
}

// ── Check Owner ───────────────────────────────────────────────
async function checkOwner() {
  const hash = document.getElementById('ownerHash').value.trim();
  if (!hash) {
    showResult('ownerResult', 'error', '⚠️ Please enter a floor plan hash.');
    return;
  }

  showResult('ownerResult', 'loading', '<span class="spinner"></span> Looking up ownership registry...');

  try {
    const res  = await fetch(`/api/get_owner/${hash}`);
    const data = await res.json();

    if (data.success) {
      showResult('ownerResult', 'success', `
        👤 <strong>Ownership Record Found</strong><br><br>
        <strong>Floor Hash:</strong> <code>${hash}</code><br>
        <strong>Registered Owner:</strong> <code>${data.owner}</code><br>
        <strong>Registry:</strong> ✅ Immutably recorded on Stellar Soroban
      `);
    } else {
      showResult('ownerResult', 'error', `❌ ${data.error || 'No ownership record found for this hash.'}`);
    }
  } catch (err) {
    showResult('ownerResult', 'error', `❌ Network error: ${err.message}`);
  }
}

// ── Load Registry ─────────────────────────────────────────────
async function loadRegistry() {
  showResult('registryResult', 'loading', '<span class="spinner"></span> Loading on-chain registry...');

  try {
    const res  = await fetch('/api/all_hashes');
    const data = await res.json();

    if (data.success) {
      const hashes = data.hashes;
      showResult('registryResult', 'success', `
        📚 <strong>On-Chain Floor Plan Registry</strong><br><br>
        <pre>${hashes}</pre>
      `);
    } else {
      showResult('registryResult', 'error', `❌ ${data.error}`);
    }
  } catch (err) {
    showResult('registryResult', 'error', `❌ Network error: ${err.message}`);
  }
}

async function loadReportCount() {
  try {
    const res  = await fetch('/api/report_count');
    const data = await res.json();
    if (data.success) {
      document.getElementById('reportCount').textContent = data.count;
    }
  } catch (_) {}
}

// ── Helper ────────────────────────────────────────────────────
function showResult(id, type, html) {
  const el = document.getElementById(id);
  el.style.display = 'block';
  el.className = `result-box ${type}`;
  el.innerHTML = html;
}
