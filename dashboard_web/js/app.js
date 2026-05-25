/* ═══════════════════════════════════════════════════════
   LexAI Dashboard — Main App (GSAP + Chart.js + API)
   ═══════════════════════════════════════════════════════ */

gsap.registerPlugin(ScrollTrigger, TextPlugin);

// On localhost keep port 9000; on Render/production use the same origin
const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? `${window.location.protocol}//${window.location.hostname}:9000`
  : window.location.origin;
let activeCase = null;
let radarChart = null;
let shapChart  = null;
let gaugeCtx   = null;
let currentTab = 'sections';

/* ══════════════════ INIT ══════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  initSidebar();
  initNavigation();
  initOverviewAnimations();
  await checkApiStatus();
  await loadCases();
  initEvidence();
  initArguments();
  initVerdictControls();
  initResearch();
  initModal();
});

/* ══════════════════ SIDEBAR / TOPBAR ══════════════════ */
function initSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const main    = document.getElementById('mainContent');
  const topbar  = document.querySelector('.topbar');

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('full-width');
    topbar.classList.toggle('full-width');
    gsap.from(main, { opacity: .7, duration: .3 });
  });

  document.getElementById('btnRefresh').addEventListener('click', () => {
    const icon = document.querySelector('#btnRefresh i');
    gsap.to(icon, { rotation: 360, duration: .6, ease: 'power2.inOut', onComplete: () => { icon.style.transform = ''; } });
    loadCases();
    checkApiStatus();
  });
}

/* ══════════════════ NAVIGATION ══════════════════ */
const PAGE_LABELS = {
  overview:  'Overview',
  cases:     'Case Manager',
  evidence:  'Evidence Room',
  arguments: 'Argument Studio',
  verdict:   'Verdict Predictor',
  research:  'Legal Research',
};

function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });
}

function navigateTo(pageId) {
  document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${pageId}"]`)?.classList.add('active');

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(`page-${pageId}`);
  if (page) page.classList.add('active');

  document.getElementById('topbarBreadcrumb').textContent = PAGE_LABELS[pageId] || pageId;

  // Page-specific actions
  if (pageId === 'cases')    loadCases();
  if (pageId === 'evidence') updateEvidenceBadge();
}

/* ══════════════════ API STATUS ══════════════════ */
async function checkApiStatus() {
  const dot  = document.querySelector('.status-dot');
  const text = document.querySelector('.status-text');
  try {
    const r = await fetch(`${API}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      dot.className  = 'status-dot online';
      text.textContent = 'API Online';
    } else throw new Error();
  } catch {
    dot.className  = 'status-dot offline';
    text.textContent = 'API Offline';
  }
}

/* ══════════════════ OVERVIEW ANIMATIONS ══════════════════ */
function initOverviewAnimations() {
  // Hero text
  gsap.from('.hero-title', { opacity: 0, y: 30, duration: 1, ease: 'power3.out', delay: .1 });
  gsap.from('.hero-sub',   { opacity: 0, y: 20, duration: .8, ease: 'power2.out', delay: .4 });

  // KPI cards stagger in
  gsap.from('.kpi-card', {
    opacity: 0, y: 40, scale: .95,
    stagger: .12, duration: .7, ease: 'back.out(1.4)', delay: .5,
    onComplete: animateKPICounters,
  });

  // Feature cards
  gsap.from('.feature-card', {
    opacity: 0, y: 30, stagger: .08, duration: .6, ease: 'power2.out', delay: .9
  });
}

function animateKPICounters() {
  document.querySelectorAll('.kpi-card').forEach((card, i) => {
    const el     = document.getElementById(`kpi${i}`);
    const target = parseInt(card.dataset.val);
    const suffix = card.dataset.suffix || '';
    gsap.to({ val: 0 }, {
      val: target, duration: 1.8, ease: 'power2.out',
      onUpdate: function () {
        el.textContent = Math.round(this.targets()[0].val) + suffix;
      }
    });
  });
}

/* ══════════════════ CASE MANAGER ══════════════════ */
async function loadCases() {
  const tbody = document.getElementById('casesTableBody');
  const list  = document.getElementById('caseList');

  tbody.innerHTML = '<tr><td colspan="7" class="loading-row"><span class="spinner"></span> Loading…</td></tr>';
  list.innerHTML = '';

  try {
    const r = await fetch(`${API}/api/v1/cases/list`);
    const data = await r.json();
    const cases = data.cases || [];

    if (!cases.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No cases yet. Create your first case.</td></tr>';
      return;
    }

    tbody.innerHTML = cases.map(c => `
      <tr>
        <td><code style="color:var(--gold);font-size:11px">${c.case_id}</code></td>
        <td>${c.case_name || '—'}</td>
        <td><span class="badge badge-${(c.case_type||'').toLowerCase()}">${c.case_type||'—'}</span></td>
        <td>${c.court || '—'}</td>
        <td><span class="badge badge-${(c.status||'active').toLowerCase()}">${c.status || 'Active'}</span></td>
        <td style="color:var(--text-muted);font-size:12px">${(c.created_at||'').slice(0,10)}</td>
        <td>
          <button class="action-btn" title="Select" onclick="selectCase('${c.case_id}','${(c.case_name||'').replace(/'/g,"\\'")}')"><i class="fas fa-check-circle"></i></button>
          <button class="action-btn" title="Evidence" onclick="navigateTo('evidence')"><i class="fas fa-microscope"></i></button>
        </td>
      </tr>
    `).join('');

    // Sidebar case list
    list.innerHTML = cases.map(c => `
      <div class="case-item ${activeCase?.id === c.case_id ? 'active' : ''}" onclick="selectCase('${c.case_id}','${(c.case_name||'').replace(/'/g,"\\'")}')">
        <div class="case-item-id">${c.case_id}</div>
        <div class="case-item-name">${c.case_name || c.case_id}</div>
      </div>
    `).join('');

    gsap.from('#casesTable tbody tr', {
      opacity: 0, x: -20, stagger: .05, duration: .4, ease: 'power2.out'
    });

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-row" style="color:var(--red)">Could not reach API — is it running? <code>uvicorn api.main:app --reload</code></td></tr>`;
    list.innerHTML  = '<div style="font-size:11px;color:var(--red);padding:8px">API offline</div>';
  }
}

function selectCase(id, name) {
  activeCase = { id, name };
  toast(`Case selected: ${id}`, 'success');
  document.querySelectorAll('.case-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll(`.case-item`).forEach(el => {
    if (el.querySelector('.case-item-id')?.textContent === id) el.classList.add('active');
  });
  const lbl = document.getElementById('caseSelectorLabel');
  if (lbl) lbl.textContent = name;
  updateEvidenceBadge();
}

/* ══════════════════ MODAL — CREATE CASE ══════════════════ */
function initModal() {
  const modal    = document.getElementById('modalCreateCase');
  const modalBox = modal.querySelector('.modal');

  const open = () => {
    gsap.killTweensOf(modalBox);
    modal.classList.remove('hidden');
    gsap.fromTo(modalBox,
      { opacity: 0, scale: 0.88, y: -16 },
      { opacity: 1, scale: 1,    y: 0, duration: 0.32, ease: 'back.out(1.5)' }
    );
  };

  const close = () => {
    gsap.killTweensOf(modalBox);
    gsap.to(modalBox, {
      opacity: 0, scale: 0.93, y: -8, duration: 0.2, ease: 'power2.in',
      onComplete: () => {
        modal.classList.add('hidden');
        gsap.set(modalBox, { clearProps: 'opacity,scale,y,transform' });
      }
    });
  };

  document.getElementById('btnCreateCase').addEventListener('click', open);
  document.getElementById('btnNewCase').addEventListener('click', open);
  document.getElementById('modalClose').addEventListener('click', close);
  document.getElementById('btnCancelCase').addEventListener('click', close);
  modal.addEventListener('click', e => { if (e.target === modal) close(); });

  document.getElementById('btnSubmitCase').addEventListener('click', createCase);
}

async function createCase() {
  const name      = document.getElementById('inCaseName').value.trim();
  const caseType  = document.getElementById('inCaseType').value;
  const court     = document.getElementById('inCourt').value.trim();
  const chargeStr = document.getElementById('inCharges').value.trim();
  const plaintiff = document.getElementById('inPlaintiff').value.trim();
  const defendant = document.getElementById('inDefendant').value.trim();

  if (!name) { toast('Case name is required', 'error'); return; }

  const btn = document.getElementById('btnSubmitCase');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px"></span> Creating…';

  try {
    const r = await fetch(`${API}/api/v1/cases/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_name: name, case_type: caseType, court,
        charges: chargeStr ? chargeStr.split(',').map(s => s.trim()).filter(Boolean) : [],
        plaintiff_name: plaintiff, defendant_name: defendant,
      }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Failed');
    toast(`Case ${data.case_id} created!`, 'success');
    const _modal    = document.getElementById('modalCreateCase');
    const _modalBox = _modal.querySelector('.modal');
    gsap.killTweensOf(_modalBox);
    gsap.to(_modalBox, {
      opacity: 0, scale: 0.93, y: -8, duration: 0.2, ease: 'power2.in',
      onComplete: () => {
        _modal.classList.add('hidden');
        gsap.set(_modalBox, { clearProps: 'opacity,scale,y,transform' });
      }
    });
    ['inCaseName','inCourt','inCharges','inPlaintiff','inDefendant'].forEach(id => document.getElementById(id).value = '');
    navigateTo('cases');
    await loadCases();
    selectCase(data.case_id, name);
  } catch (e) {
    toast(`Error: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check"></i> Create';
  }
}

/* ══════════════════ EVIDENCE ROOM ══════════════════ */
function initEvidence() {
  const zone  = document.getElementById('uploadZone');
  const input = document.getElementById('fileInput');
  const btn   = document.getElementById('btnBrowseFiles');

  btn.addEventListener('click', () => input.click());
  input.addEventListener('change', () => handleFiles(Array.from(input.files)));

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('dragover');
    handleFiles(Array.from(e.dataTransfer.files));
  });
}

function updateEvidenceBadge() {
  const badge = document.getElementById('evidenceCaseBadge');
  badge.textContent = activeCase ? activeCase.id : 'No case selected';
  badge.style.color = activeCase ? 'var(--gold)' : '';
}

const EVIDENCE_ICONS = {
  pdf: { icon: 'fas fa-file-pdf',   color: '#ef4444' },
  docx:{ icon: 'fas fa-file-word',  color: '#3b82f6' },
  doc: { icon: 'fas fa-file-word',  color: '#3b82f6' },
  txt: { icon: 'fas fa-file-alt',   color: '#6b7280' },
  jpg: { icon: 'fas fa-image',      color: '#22c55e' },
  jpeg:{ icon: 'fas fa-image',      color: '#22c55e' },
  png: { icon: 'fas fa-image',      color: '#22c55e' },
  mp3: { icon: 'fas fa-microphone', color: '#a855f7' },
  wav: { icon: 'fas fa-microphone', color: '#a855f7' },
  mp4: { icon: 'fas fa-video',      color: '#f59e0b' },
};

async function handleFiles(files) {
  if (!activeCase) { toast('Select a case first', 'error'); navigateTo('cases'); return; }

  for (const file of files) {
    const ext  = file.name.split('.').pop().toLowerCase();
    const meta = EVIDENCE_ICONS[ext] || { icon: 'fas fa-file', color: '#6b7280' };
    const itemId = `ev-${Date.now()}-${Math.random().toString(36).slice(2,6)}`;

    addEvidenceItem(itemId, file.name, ext, meta, 'Uploading…', null);

    try {
      const fd = new FormData();
      fd.append('file', file);
      const r    = await fetch(`${API}/api/v1/cases/${activeCase.id}/upload`, { method: 'POST', body: fd });
      const data = await r.json();

      if (!r.ok) throw new Error(data.error || 'Upload failed');

      const strength = data.evidence_strength ?? data.evidence_analyses?.[0]?.evidence_strength ?? null;
      updateEvidenceItem(itemId, data.summary || 'Processed', strength);
      toast(`${file.name} — analysed`, 'success');
    } catch (e) {
      updateEvidenceItem(itemId, `Error: ${e.message}`, null, true);
      toast(`${file.name}: ${e.message}`, 'error');
    }
  }
}

function addEvidenceItem(id, name, ext, meta, status, strength) {
  const list = document.getElementById('evidenceList');
  const div  = document.createElement('div');
  div.className = 'evidence-item';
  div.id = id;
  div.innerHTML = `
    <i class="${meta.icon} evidence-icon" style="color:${meta.color}"></i>
    <div class="evidence-info">
      <div class="evidence-name">${name}</div>
      <div class="evidence-meta" id="${id}-meta">${status}</div>
      <div class="strength-bar"><div class="strength-fill" id="${id}-bar" style="width:0%"></div></div>
    </div>
    <div class="evidence-strength" id="${id}-score">${strength !== null ? strength.toFixed(1) : '…'}</div>
  `;
  list.prepend(div);
  gsap.from(div, { opacity: 0, x: -20, duration: .4, ease: 'power2.out' });
}

function updateEvidenceItem(id, meta, strength, isError = false) {
  const metaEl = document.getElementById(`${id}-meta`);
  const scoreEl = document.getElementById(`${id}-score`);
  const barEl   = document.getElementById(`${id}-bar`);
  if (metaEl)  metaEl.textContent = meta;
  if (scoreEl) scoreEl.textContent = strength !== null ? strength.toFixed(1) : (isError ? '—' : '…');
  if (barEl && strength !== null) {
    gsap.to(barEl, { width: `${strength * 10}%`, duration: .8, ease: 'power2.out' });
  }
  if (isError && metaEl) metaEl.style.color = 'var(--red)';
}

/* ══════════════════ ARGUMENT STUDIO ══════════════════ */
function initArguments() {
  document.getElementById('btnGenProsecution').addEventListener('click', () => generateArgument('prosecution'));
  document.getElementById('btnGenDefense').addEventListener('click', () => generateArgument('defense'));
  document.getElementById('btnCrossEx').addEventListener('click', generateCrossEx);
}

async function generateArgument(side) {
  if (!activeCase) { toast('Select a case first', 'error'); return; }
  const style  = document.getElementById('argStyle').value;
  const btn    = document.getElementById(`btnGen${side.charAt(0).toUpperCase()+side.slice(1)}`);
  const panel  = document.getElementById(`${side}Content`);
  const scoreEl = document.getElementById(`${side}Score`);

  btn.disabled = true;
  const origHTML = btn.innerHTML;
  btn.innerHTML  = '<span class="spinner" style="width:12px;height:12px;border-width:2px"></span> Generating…';
  panel.innerHTML = '<div class="loading-row"><span class="spinner"></span> Building argument…</div>';

  try {
    const r    = await fetch(`${API}/api/v1/arguments/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: activeCase.id, side, style }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Failed');

    const args = data.arguments || data;
    scoreEl.textContent = `${(args.argument_strength_score || 0).toFixed(1)}/10`;
    renderArgument(panel, args, side);

    gsap.from(panel.children, { opacity: 0, y: 15, stagger: .08, duration: .4, ease: 'power2.out' });
    toast(`${side} argument generated`, 'success');
  } catch (e) {
    panel.innerHTML = `<div class="arg-placeholder" style="color:var(--red)"><i class="fas fa-exclamation-triangle"></i><br/>${e.message}</div>`;
    toast(`Error: ${e.message}`, 'error');
  } finally {
    btn.disabled  = false;
    btn.innerHTML = origHTML;
  }
}

function renderArgument(panel, args, side) {
  const color = side === 'prosecution' ? 'var(--red)' : 'var(--blue)';
  let html = '';

  if (args.opening_statement) {
    html += `<div class="arg-section-title" style="color:${color}">Opening Statement</div>
             <div class="arg-section-body">${args.opening_statement}</div>`;
  }
  if (args.key_arguments?.length) {
    html += `<div class="arg-section-title" style="color:${color}">Key Arguments</div>`;
    html += args.key_arguments.map(a => `<div class="arg-item">${a}</div>`).join('');
  }
  if (args.evidence_submissions?.length) {
    html += `<div class="arg-section-title" style="color:${color}">Evidence Submissions</div>`;
    html += args.evidence_submissions.map(a => `<div class="arg-item">${a}</div>`).join('');
  }
  if (args.acquittal_grounds?.length) {
    html += `<div class="arg-section-title" style="color:${color}">Acquittal Grounds</div>`;
    html += args.acquittal_grounds.map(a => `<div class="arg-item">${a}</div>`).join('');
  }
  if (args.closing_statement) {
    html += `<div class="arg-section-title" style="color:${color}">Closing Statement</div>
             <div class="arg-section-body">${args.closing_statement}</div>`;
  }
  panel.innerHTML = html || '<div class="arg-placeholder">No structured content returned.</div>';
}

async function generateCrossEx() {
  const name      = document.getElementById('witnessName').value.trim();
  const statement = document.getElementById('witnessStatement').value.trim();
  const side      = document.getElementById('crossexSide').value;
  const results   = document.getElementById('crossexResults');

  if (!statement) { toast('Paste a witness statement first', 'error'); return; }
  if (!activeCase) { toast('Select a case first', 'error'); return; }

  // Combine name + statement into the witness_statement field the API expects
  const witness_statement = name
    ? `Witness: ${name}. Statement: ${statement}`
    : statement;

  const btn = document.getElementById('btnCrossEx');
  btn.disabled = true;
  const origHTML = btn.innerHTML;
  btn.innerHTML  = '<span class="spinner" style="width:12px;height:12px;border-width:2px"></span> Generating…';
  results.innerHTML = '<div class="loading-row"><span class="spinner"></span> Generating questions…</div>';

  try {
    const r = await fetch(`${API}/api/v1/arguments/cross-examine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: activeCase.id, witness_statement, side }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || data.detail || JSON.stringify(data));

    const questions = data.questions || [];
    if (!questions.length) {
      results.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:12px">No questions generated — try a longer statement.</div>';
      return;
    }
    results.innerHTML = questions.map((q, i) => `
      <div class="crossex-q">
        <span class="crossex-q-num">Q${i+1}</span>
        <span>${q}</span>
      </div>`).join('');

    gsap.from('.crossex-q', { opacity: 0, x: -15, stagger: .05, duration: .3, ease: 'power2.out' });
    toast(`${questions.length} questions generated`, 'success');
  } catch (e) {
    results.innerHTML = `<div style="color:var(--red);font-size:13px;padding:12px"><i class="fas fa-exclamation-circle"></i> ${e.message}</div>`;
    toast(`Error: ${e.message}`, 'error');
  } finally {
    btn.disabled  = false;
    btn.innerHTML = origHTML;
  }
}

/* ══════════════════ VERDICT PREDICTOR ══════════════════ */
const SLIDER_FEATURES = [
  { key: 'evidence_count',            label: 'Evidence Count',            min: 0,  max: 20, step: 1,   def: 5 },
  { key: 'evidence_strength_avg',     label: 'Evidence Strength (avg)',   min: 0,  max: 10, step: .5,  def: 6 },
  { key: 'witness_count',             label: 'Witness Count',             min: 0,  max: 15, step: 1,   def: 3 },
  { key: 'witness_credibility_avg',   label: 'Witness Credibility (avg)', min: 0,  max: 10, step: .5,  def: 6 },
  { key: 'precedent_match_score',     label: 'Precedent Match Score',     min: 0,  max: 1,  step: .05, def: .5 },
  { key: 'charge_severity',           label: 'Charge Severity',           min: 1,  max: 5,  step: 1,   def: 3 },
  { key: 'prosecution_argument_score',label: 'Prosecution Arg. Score',    min: 0,  max: 10, step: .5,  def: 6 },
  { key: 'defense_argument_score',    label: 'Defense Arg. Score',        min: 0,  max: 10, step: .5,  def: 5 },
  { key: 'case_duration_days',        label: 'Case Duration (days)',       min: 30, max: 1825,step: 30, def: 365 },
];

const CHECKBOX_FEATURES = [
  { key: 'confession_present',   label: 'Confession Present' },
  { key: 'documentary_evidence', label: 'Documentary Evidence' },
  { key: 'forensic_evidence',    label: 'Forensic Evidence' },
];

function initVerdictControls() {
  const sliderContainer   = document.getElementById('featureSliders');
  const checkboxContainer = document.getElementById('featureCheckboxes');

  SLIDER_FEATURES.forEach(f => {
    const div = document.createElement('div');
    div.className = 'slider-group';
    div.innerHTML = `
      <div class="slider-label">
        <span>${f.label}</span>
        <span id="sv-${f.key}">${f.def}</span>
      </div>
      <input type="range" id="sl-${f.key}" min="${f.min}" max="${f.max}" step="${f.step}" value="${f.def}" />
    `;
    sliderContainer.appendChild(div);
    div.querySelector('input').addEventListener('input', function () {
      document.getElementById(`sv-${f.key}`).textContent = this.value;
    });
  });

  CHECKBOX_FEATURES.forEach(f => {
    const label = document.createElement('label');
    label.className = 'checkbox-group';
    label.innerHTML = `<input type="checkbox" id="cb-${f.key}" /> ${f.label}`;
    checkboxContainer.appendChild(label);
  });

  document.getElementById('btnPredict').addEventListener('click', predictVerdict);
}

function getFeatureValues() {
  const features = { ipc_section_severity: 3, judge_type: 1, bail_status: 0 };
  SLIDER_FEATURES.forEach(f => {
    features[f.key] = parseFloat(document.getElementById(`sl-${f.key}`).value);
  });
  CHECKBOX_FEATURES.forEach(f => {
    features[f.key] = document.getElementById(`cb-${f.key}`).checked ? 1 : 0;
  });
  return features;
}

async function predictVerdict() {
  const btn = document.getElementById('btnPredict');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px"></span> Predicting…';

  const caseId = activeCase?.id || 'DEMO-CASE';
  const features = getFeatureValues();

  try {
    const r    = await fetch(`${API}/api/v1/verdict/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, features }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || data.detail || 'Failed');

    renderGauge(data.conviction_probability, data.verdict);
    renderModelVotes(data.model_votes || {});

    if (data.shap_explanation) renderShap(data.shap_explanation);
    if (activeCase) loadScenarios(caseId, features);

    document.getElementById('modelVotes').classList.remove('hidden');
    toast(`Verdict: ${data.verdict} (${(data.conviction_probability*100).toFixed(0)}%)`, 'info');
  } catch (e) {
    document.getElementById('gaugeVerdict').textContent = `Error: ${e.message}`;
    toast(`Error: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-brain"></i> Predict Verdict';
  }
}

function renderGauge(prob, verdict) {
  const canvas = document.getElementById('gaugeCanvas');
  const ctx    = canvas.getContext('2d');
  const cx = 160, cy = 160, r = 120;

  ctx.clearRect(0, 0, 320, 200);

  // Background arc
  const drawArc = (startAngle, endAngle, color) => {
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 18;
    ctx.lineCap   = 'round';
    ctx.stroke();
  };

  drawArc(Math.PI, Math.PI * 1.4, '#22c55e33');
  drawArc(Math.PI * 1.4, Math.PI * 1.6, '#f59e0b33');
  drawArc(Math.PI * 1.6, Math.PI * 2, '#ef444433');

  // Animated fill
  const targetAngle = Math.PI + prob * Math.PI;
  const fillColor = prob > .6 ? '#ef4444' : prob > .4 ? '#f59e0b' : '#22c55e';

  gsap.to({ angle: Math.PI }, {
    angle: targetAngle, duration: 1.4, ease: 'power2.out',
    onUpdate: function () {
      ctx.clearRect(0, 0, 320, 200);
      drawArc(Math.PI, Math.PI * 1.4, '#22c55e33');
      drawArc(Math.PI * 1.4, Math.PI * 1.6, '#f59e0b33');
      drawArc(Math.PI * 1.6, Math.PI * 2, '#ef444433');
      drawArc(Math.PI, this.targets()[0].angle, fillColor);

      // Needle
      const needle = this.targets()[0].angle;
      const nx = cx + (r - 22) * Math.cos(needle);
      const ny = cy + (r - 22) * Math.sin(needle);
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(nx, ny);
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#fff';
      ctx.fill();

      // Labels
      ctx.font = '11px Inter';
      ctx.fillStyle = '#6b7280';
      ctx.textAlign = 'center';
      ctx.fillText('Acquittal', cx - 90, cy + 20);
      ctx.fillText('Conviction', cx + 90, cy + 20);
    },
  });

  gsap.to({}, { duration: .1, onComplete: () => {
    const labelEl   = document.getElementById('gaugeLabel');
    const verdictEl = document.getElementById('gaugeVerdict');
    verdictEl.textContent = verdict || '—';
    verdictEl.style.color = verdict === 'Conviction' ? 'var(--red)' : 'var(--green)';
    gsap.to({ v: 0 }, {
      v: prob * 100, duration: 1.4, ease: 'power2.out',
      onUpdate: function () { labelEl.textContent = Math.round(this.targets()[0].v) + '%'; }
    });
  }});
}

function renderModelVotes(votes) {
  const list = document.getElementById('voteList');
  list.innerHTML = Object.entries(votes).map(([model, verdict]) => `
    <div class="vote-item">
      <span style="font-weight:500">${model}</span>
      <span class="vote-badge-${verdict.toLowerCase()}">${verdict}</span>
    </div>
  `).join('');
  gsap.from('.vote-item', { opacity: 0, x: 20, stagger: .08, duration: .4 });
}

function renderShap(shapData) {
  const section = document.getElementById('shapSection');
  section.classList.remove('hidden');
  const features = Object.keys(shapData).slice(0, 10);
  const values   = features.map(k => shapData[k]);
  const colors   = values.map(v => v > 0 ? 'rgba(239,68,68,.7)' : 'rgba(34,197,94,.7)');

  if (shapChart) shapChart.destroy();
  shapChart = new Chart(document.getElementById('shapChart'), {
    type: 'bar',
    data: {
      labels: features,
      datasets: [{ data: values, backgroundColor: colors, borderRadius: 4 }]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,.05)' }, ticks: { color: '#6b7280' } },
        y: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 11 } } }
      },
      animation: { duration: 800, easing: 'easeOutQuart' }
    }
  });
}

async function loadScenarios(caseId, features) {
  try {
    const r    = await fetch(`${API}/api/v1/verdict/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, features }),
    });
    const data = await r.json();
    if (!r.ok) return;

    const section  = document.getElementById('scenariosSection');
    const grid     = document.getElementById('scenarioGrid');
    const base     = features.conviction_probability || 0;
    const scenarios = data.scenarios || [];

    section.classList.remove('hidden');
    grid.innerHTML = scenarios.map(s => {
      const delta = (s.conviction_probability - (data.base_probability || .5));
      const sign  = delta > 0 ? '+' : '';
      return `
        <div class="scenario-card">
          <div class="scenario-name">${s.scenario}</div>
          <div class="scenario-prob">${(s.conviction_probability * 100).toFixed(0)}%</div>
          <div class="scenario-delta ${delta > 0 ? 'up' : 'down'}">${sign}${(delta * 100).toFixed(0)}% vs base</div>
        </div>`;
    }).join('');

    gsap.from('.scenario-card', { opacity: 0, y: 15, stagger: .05, duration: .35 });
  } catch (_) {}
}

/* ══════════════════ LEGAL RESEARCH ══════════════════ */
function initResearch() {
  document.getElementById('btnSearch').addEventListener('click', runSearch);
  document.getElementById('researchQuery').addEventListener('keydown', e => { if (e.key === 'Enter') runSearch(); });

  document.querySelectorAll('.eq-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('researchQuery').value = btn.dataset.q;
      runSearch();
    });
  });

  document.querySelectorAll('.res-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.res-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTab = tab.dataset.tab;
      runSearch();
    });
  });
}

async function runSearch() {
  const q       = document.getElementById('researchQuery').value.trim();
  const results = document.getElementById('researchResults');
  if (!q) return;

  results.innerHTML = '<div class="loading-row"><span class="spinner"></span> Searching…</div>';

  try {
    let r, data;
    if (currentTab === 'sections') {
      r    = await fetch(`${API}/api/v1/research/sections`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) });
      data = await r.json();
      renderSectionResults(data.results || []);
    } else if (currentTab === 'precedents') {
      r    = await fetch(`${API}/api/v1/research/precedents`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: q }) });
      data = await r.json();
      renderPrecedentResults(data.results || []);
    } else {
      r    = await fetch(`${API}/api/v1/research/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q }) });
      data = await r.json();
      renderAIAnswer(data);
    }
    gsap.from('.result-card, .ai-answer', { opacity: 0, y: 12, stagger: .06, duration: .35, ease: 'power2.out' });
  } catch (e) {
    results.innerHTML = `<div class="research-placeholder" style="color:var(--red)"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;
  }
}

function renderSectionResults(items) {
  const el = document.getElementById('researchResults');
  if (!items.length) { el.innerHTML = '<div class="research-placeholder"><i class="fas fa-search"></i><p>No sections found</p></div>'; return; }
  el.innerHTML = items.map(item => `
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-title">IPC Section ${item.section || '?'} — ${item.title || ''}</div>
        <span class="result-card-tag">§${item.section}</span>
      </div>
      <div class="result-card-body">${(item.description || '').slice(0, 200)}…</div>
      <div class="result-card-meta">
        Punishment: ${item.punishment || '—'} &nbsp;·&nbsp;
        Bailable: ${item.bailable ? 'Yes' : 'No'} &nbsp;·&nbsp;
        <span class="result-score">Score: ${(item.score || 0).toFixed(3)}</span>
      </div>
    </div>`).join('');
}

function renderPrecedentResults(items) {
  const el = document.getElementById('researchResults');
  if (!items.length) { el.innerHTML = '<div class="research-placeholder"><i class="fas fa-landmark"></i><p>No precedents found</p></div>'; return; }
  el.innerHTML = items.map(item => `
    <div class="result-card">
      <div class="result-card-header">
        <div class="result-card-title">${item.case_name || '—'}</div>
        <span class="result-card-tag">${item.year || '—'}</span>
      </div>
      <div class="result-card-body">${(item.legal_principle || item.significance || '').slice(0, 250)}…</div>
      <div class="result-card-meta">
        Court: ${item.court || 'Supreme Court of India'} &nbsp;·&nbsp;
        <span class="result-score">Score: ${(item.score || 0).toFixed(3)}</span>
      </div>
    </div>`).join('');
}

function renderAIAnswer(data) {
  const el = document.getElementById('researchResults');
  el.innerHTML = `
    <div class="ai-answer">
      <div class="ai-answer-header"><i class="fas fa-robot"></i> AI Legal Answer</div>
      <div class="ai-answer-body">${data.answer || JSON.stringify(data)}</div>
      ${data.sources?.length ? `<div class="result-card-meta" style="margin-top:12px">Sources: ${data.sources.slice(0,3).join(' · ')}</div>` : ''}
    </div>`;
}

/* ══════════════════ TOAST ══════════════════ */
function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  const icon = { success: 'check-circle', error: 'exclamation-circle', info: 'info-circle' }[type] || 'info-circle';
  el.innerHTML = `<i class="fas fa-${icon}"></i> ${msg}`;
  container.appendChild(el);
  gsap.from(el, { opacity: 0, x: 40, duration: .35, ease: 'back.out(1.4)' });
  setTimeout(() => {
    gsap.to(el, { opacity: 0, x: 40, duration: .3, ease: 'power2.in', onComplete: () => el.remove() });
  }, 3500);
}
