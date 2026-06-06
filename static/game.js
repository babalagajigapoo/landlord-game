// ── State ─────────────────────────────────────────────────────────────────────
let state           = null;
let marketListings  = [];
let currentPage     = 'dashboard';
let pendingUpgrade  = null;
let _applicants     = [];
let _fairRent       = 0;
let _selectedTier   = 2;       // default Average
let _pendingConfirm = null;

// ── Mini-game state ───────────────────────────────────────────────────────────
let _mg             = {};   // active mini-game state
let _pendingRepairs = [];   // repair events queued after advancing
let _currentRepair  = null; // repair being handled right now

// ── Seasons ───────────────────────────────────────────────────────────────────
const SEASONS = [
  { name: 'Spring', icon: '🌸' },
  { name: 'Summer', icon: '☀️' },
  { name: 'Fall',   icon: '🍂' },
  { name: 'Winter', icon: '❄️' },
];

const DAYS_PER_SEASON = 28;
const DAYS_PER_YEAR   = DAYS_PER_SEASON * 4;  // 112

function getSeasonInfo(day) {
  const d         = Math.max(1, day);
  const yearDay   = (d - 1) % DAYS_PER_YEAR;
  const seasonIdx = Math.floor(yearDay / DAYS_PER_SEASON);
  const seasonDay = (yearDay % DAYS_PER_SEASON) + 1;
  const year      = Math.floor((d - 1) / DAYS_PER_YEAR) + 1;
  return { ...SEASONS[seasonIdx], seasonDay, year };
}

// ── Local Save ────────────────────────────────────────────────────────────────
function getLocalState() {
  try { const s = localStorage.getItem('landlord_save'); return s ? JSON.parse(s) : null; }
  catch { return null; }
}
function saveLocalState(s) {
  try { localStorage.setItem('landlord_save', JSON.stringify(s)); } catch {}
}
function clearLocalState() {
  try { localStorage.removeItem('landlord_save'); } catch {}
}

// ── API ───────────────────────────────────────────────────────────────────────
// Always POST so we can carry _state in the body. Backend returns updated _state.
async function api(path, method = 'GET', body = null) {
  const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
  opts.body  = JSON.stringify({ ...(body || {}), _state: getLocalState() });
  const res  = await fetch('/api' + path, opts);
  const data = await res.json();
  if (data._state) saveLocalState(data._state);
  return data;
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  setupNav();          // nav first — independent of async data
  await refreshState();
  await loadMarket();
  renderAll();
}

async function refreshState() {
  state = await api('/state');
  updateHeader();
}

async function loadMarket() {
  const data     = await api('/market');
  marketListings = data.listings;
}

// ── Header ────────────────────────────────────────────────────────────────────
function updateHeader() {
  document.getElementById('hdr-cash').textContent = fmt(state.cash);
  const s = getSeasonInfo(state.day);
  document.getElementById('hdr-day').textContent  = `${s.icon} ${s.name} · Day ${s.seasonDay}`;
}

// ── Navigation ────────────────────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => navTo(btn.dataset.page));
  });
}

function navTo(page) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const pageEl = document.getElementById('page-' + page);
  const btnEl  = document.querySelector(`.nav-btn[data-page="${page}"]`);
  if (pageEl) pageEl.classList.add('active');
  if (btnEl)  btnEl.classList.add('active');
  if (page === 'bank')     renderBank();
  if (page === 'settings') renderSettings();
}

// ── Render All ────────────────────────────────────────────────────────────────
function renderAll() {
  renderDashboard();
  renderMarket();
  renderProperties();
  renderLog();
  if (currentPage === 'settings') renderSettings();
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function renderDashboard() {
  if (!state) return;
  document.getElementById('dash-cash').textContent     = fmt(state.cash);
  document.getElementById('dash-networth').textContent = fmt(state.net_worth);
  document.getElementById('dash-props').textContent    = state.property_count;
  document.getElementById('dash-income').textContent   = fmt(state.weekly_income) + '/wk';

  // Season card
  const s = getSeasonInfo(state.day);
  const seasonEl = document.getElementById('dash-season');
  if (seasonEl) {
    seasonEl.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:32px">${s.icon}</span>
        <div>
          <div style="font-size:16px;font-weight:800">${s.name} — Year ${s.year}</div>
          <div style="font-size:12px;color:var(--text-muted)">Day ${s.seasonDay} of ${DAYS_PER_SEASON} · Overall Day ${state.day}</div>
        </div>
      </div>
      <div class="condition-bar" style="margin-top:8px">
        <div class="condition-fill cond-great" style="width:${(s.seasonDay / DAYS_PER_SEASON) * 100}%"></div>
      </div>`;
  }

}

// ── Market ────────────────────────────────────────────────────────────────────
function renderMarket() {
  const el = document.getElementById('market-list');
  if (!el) return;
  if (marketListings.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">🏚️</div><div class="empty-text">No listings</div><div class="empty-sub">Refresh to see new properties</div></div>';
    return;
  }
  el.innerHTML = marketListings.map(p => marketCardHtml(p)).join('');
}

function marketCardHtml(p) {
  const deal    = p.deal;
  const dealTag = deal >= 0
    ? `<span class="deal-tag deal-good">+${fmt(deal)} under value</span>`
    : `<span class="deal-tag deal-bad">${fmt(deal)} over value</span>`;
  const tier = p.neighborhood_info?.tier || 'mid';
  const canAfford = p.purchase_price <= state.cash;

  return `
  <div class="card">
    <div class="card-header">
      <div class="card-icon">${p.icon}</div>
      <div style="flex:1">
        <div class="card-title">${p.bedrooms}bd / ${p.bathrooms}ba ${p.type}</div>
        <div class="card-subtitle">${p.neighborhood} · ${p.sqft.toLocaleString()} sqft</div>
        <div style="margin-top:4px"><span class="card-badge badge-${tier}">${p.neighborhood}</span></div>
      </div>
    </div>
    <div class="condition-wrap">
      <div class="condition-top">
        <span class="condition-lbl">Condition</span>
        <span class="condition-val">${p.condition_label} (${p.condition}/100)</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${p.condition}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Asking Price</span><span class="mr-value">${fmt(p.purchase_price)}</span></div>
    <div class="money-row"><span class="mr-label">Est. Market Value</span><span class="mr-value">${fmt(p.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">Fair Weekly Rent</span><span class="mr-value green">${fmt(p.weekly_rent)}/wk</span></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px">
      ${dealTag}
      <button class="btn btn-primary btn-sm" onclick="buyProperty(${p.id})" ${!canAfford ? 'disabled style="opacity:0.4"' : ''}>
        Buy ${fmt(p.purchase_price)}
      </button>
    </div>
  </div>`;
}

async function buyProperty(id) {
  const listing = marketListings.find(p => p.id === id);
  if (!listing) return;
  if (listing.purchase_price > state.cash) { toast('Not enough cash!', 'error'); return; }
  showConfirmModal(
    `Buy ${listing.bedrooms}bd ${listing.type}?`,
    `${listing.neighborhood} · ${fmt(listing.purchase_price)}`,
    async () => {
      const res = await api('/buy', 'POST', { listing_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      toast(`Purchased ${listing.type} in ${listing.neighborhood}!`, 'success');
      await refreshState();
      await loadMarket();
      renderAll();
    }
  );
}

async function refreshMarket() {
  const btn = document.getElementById('refresh-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>'; }
  const data = await api('/market/refresh', 'POST');
  marketListings = data.listings;
  renderMarket();
  if (btn) { btn.disabled = false; btn.textContent = '🔄 Refresh'; }
  toast('New listings loaded!');
}

// ── Properties ────────────────────────────────────────────────────────────────
function renderProperties() {
  const el = document.getElementById('property-list');
  if (!el) return;
  if (!state.properties || state.properties.length === 0) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">🏗️</div>
      <div class="empty-text">No properties yet</div>
      <div class="empty-sub">Head to the Market tab to buy your first property</div>
    </div>`;
    return;
  }
  el.innerHTML = state.properties.map(p => portfolioCardHtml(p)).join('');
}

function portfolioCardHtml(p) {
  const tenantBadge = p.tenant
    ? `<span class="tenant-chip">${p.tenant.icon || '👤'} ${p.tenant.name} · ${fmt(p.tenant.rent)}/wk</span>`
    : `<span class="vacant-chip">⚪ Vacant</span>`;
  const profit    = p.market_value - p.purchase_price;
  const profitStr = profit >= 0
    ? `<span class="mr-value green">+${fmt(profit)}</span>`
    : `<span class="mr-value red">${fmt(profit)}</span>`;

  return `
  <div class="card" onclick="showPropertyDetail(${p.id})" style="cursor:pointer">
    <div class="card-header">
      <div class="card-icon">${p.icon}</div>
      <div style="flex:1">
        <div class="card-title">${p.bedrooms}bd / ${p.bathrooms}ba ${p.type}</div>
        <div class="card-subtitle">${p.neighborhood} · ${p.sqft.toLocaleString()} sqft</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:16px;font-weight:800">${fmt(p.market_value)}</div>
        <div style="font-size:11px;color:var(--text-muted)">market value</div>
      </div>
    </div>
    <div class="condition-wrap mb-0">
      <div class="condition-top">
        <span class="condition-lbl">Condition · ${p.condition_label}</span>
        <span class="condition-val">${p.condition}/100</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${p.condition}%"></div></div>
    </div>
    <div style="margin-top:10px;display:flex;align-items:center;justify-content:space-between">
      ${tenantBadge}
      <div style="font-size:12px;color:var(--text-muted)">G/L: ${profitStr}</div>
    </div>
  </div>`;
}

// ── Property Detail ───────────────────────────────────────────────────────────
async function showPropertyDetail(id) {
  const prop = state.properties.find(p => p.id === id);
  if (!prop) return;

  const upgData  = await api(`/property/${id}/upgrades`);
  const profit   = prop.market_value - prop.purchase_price;
  const profitStr = profit >= 0
    ? `<span style="color:var(--positive)">+${fmt(profit)}</span>`
    : `<span style="color:var(--negative)">${fmt(profit)}</span>`;

  const tenantSection = prop.tenant
    ? `<div class="card" style="margin-bottom:10px">
        <div class="section-header mb-0"><span class="section-title">Current Tenant</span></div>
        <div style="margin-top:10px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span style="font-size:28px">${prop.tenant.icon || '👤'}</span>
            <div style="flex:1">
              <div style="font-size:15px;font-weight:700">${prop.tenant.name}</div>
              <div style="font-size:12px;color:var(--text-2)">${prop.tenant_days_remaining ?? '?'} days left on lease</div>
              <div style="margin-top:2px">${rentTierBadge(prop.tenant.rent_tier)}</div>
            </div>
            <span style="font-size:18px;font-weight:800;color:var(--positive)">${fmt(prop.tenant.rent)}/wk</span>
          </div>
          <div class="money-row"><span class="mr-label">Total Rent Collected</span><span class="mr-value green">${fmt(prop.total_rent_collected)}</span></div>
          <div class="money-row"><span class="mr-label">Total Repair Costs</span><span class="mr-value red">${fmt(prop.total_repair_costs)}</span></div>
          <div class="btn-row">
            <button class="btn btn-danger btn-sm" onclick="evictTenant(${id})">⚖️ Evict ($1,500)</button>
          </div>
        </div>
      </div>`
    : `<div class="card" style="margin-bottom:10px">
        <div class="section-header mb-0"><span class="section-title">Tenant</span></div>
        <p style="margin-top:8px;font-size:13px;color:var(--text-muted)">This property is vacant.</p>
        <div class="btn-row">
          <button class="btn btn-primary btn-sm" onclick="showTenantsModal(${id})">🔑 Find Tenant</button>
          <button class="btn btn-accent btn-sm" onclick="sellProperty(${id})">💰 Sell Property</button>
        </div>
      </div>`;

  const doneHtml = upgData.done.length > 0
    ? `<div class="upgrade-grid">${upgData.done.map(u =>
        `<div class="upgrade-card done">
          <div class="upgrade-icon">${u.icon}</div>
          <div class="upgrade-name">${u.name}</div>
          <div class="upgrade-quality">✓ Quality ${u.quality}/100</div>
        </div>`).join('')}</div>`
    : '';

  const availHtml = upgData.available.length > 0
    ? `<div class="upgrade-grid">${upgData.available.map(u =>
        `<div class="upgrade-card ${prop.tenant ? 'btn-disabled' : ''}"
          ${!prop.tenant ? `onclick="showContractorModal(${id},'${u.key}')"` : ''}>
          <div class="upgrade-icon">${u.icon}</div>
          <div class="upgrade-name">${u.name}</div>
          <div class="upgrade-cost">from ${fmt(u.costs.budget)}</div>
        </div>`).join('')}</div>`
    : '<p class="text-muted" style="margin-top:4px">All upgrades completed!</p>';

  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <span style="font-size:36px">${prop.icon}</span>
      <div>
        <div style="font-size:18px;font-weight:800;margin-bottom:2px">${prop.bedrooms}bd / ${prop.bathrooms}ba ${prop.type}</div>
        <div style="font-size:13px;color:var(--text-2)">${prop.neighborhood} · ${prop.sqft.toLocaleString()} sqft</div>
      </div>
    </div>
    <div class="condition-wrap">
      <div class="condition-top">
        <span class="condition-lbl">Condition · ${prop.condition_label}</span>
        <span class="condition-val">${prop.condition}/100</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(prop.condition)}" style="width:${prop.condition}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Market Value</span><span class="mr-value">${fmt(prop.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">Purchase Price</span><span class="mr-value">${fmt(prop.purchase_price)}</span></div>
    <div class="money-row"><span class="mr-label">Unrealized Gain/Loss</span><div>${profitStr}</div></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Fair Weekly Rent</span><span class="mr-value green">${fmt(prop.weekly_rent)}/wk</span></div>
    ${tenantSection}
    <div class="section-header"><span class="section-title">Renovations</span></div>
    ${prop.tenant ? '<p class="text-muted" style="margin-bottom:8px">Tenant must vacate before renovating.</p>' : ''}
    ${doneHtml}
    ${upgData.available.length > 0 ? `<div style="margin-top:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:var(--text-muted)">AVAILABLE</div>${availHtml}</div>` : ''}
    <div class="btn-row" style="margin-top:16px">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">← Back</button>
    </div>`);
}

// ── Sell & Evict ──────────────────────────────────────────────────────────────
function sellProperty(id) {
  const prop = state.properties.find(p => p.id === id);
  if (!prop) return;
  showConfirmModal(
    `Sell ${prop.type} in ${prop.neighborhood}?`,
    `Market value ~${fmt(prop.market_value)}. Final price varies ±5%.`,
    async () => {
      const res = await api('/sell', 'POST', { prop_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      const label = res.profit >= 0 ? `+${fmt(res.profit)} profit` : `${fmt(res.profit)} loss`;
      toast(`Sold for ${fmt(res.sale_price)} (${label})`, res.profit >= 0 ? 'success' : 'warning');
      closeModal();
      await refreshState();
      renderAll();
    }
  );
}

function evictTenant(id) {
  const prop = state.properties.find(p => p.id === id);
  if (!prop || !prop.tenant) return;
  showConfirmModal(
    `Evict ${prop.tenant.name}?`,
    `This will cost $1,500 in legal fees.`,
    async () => {
      const res = await api('/evict', 'POST', { prop_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      toast('Tenant evicted.', 'warning');
      closeModal();
      await refreshState();
      renderAll();
    }
  );
}

// ── Tenant Flow ───────────────────────────────────────────────────────────────
async function showTenantsModal(id) {
  const prop = state.properties.find(p => p.id === id);
  openModal(`<div class="modal-handle"></div><div class="modal-title">Find a Tenant</div><p class="text-muted">Loading applicants…</p>`);

  const data  = await api(`/property/${id}/applicants`);
  _applicants = data.applicants;
  _fairRent   = data.fair_weekly_rent;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">Choose a Tenant</div>
    <div class="modal-subtitle">${prop.type} in ${prop.neighborhood} · Fair rent: ${fmt(_fairRent)}/wk</div>
    ${_applicants.map(t => `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})">
        <div class="tenant-header">
          <span class="tenant-icon">${t.icon}</span>
          <div>
            <div class="tenant-name">${t.name}</div>
            <div style="font-size:11px;color:var(--text-muted)">${t.stay_min}–${t.stay_max} day base lease</div>
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label">Reliability</span>
            <span class="stars">${starsHtml(t.pay_chance)}</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Damage Risk</span>
            <span class="tm-value" style="color:${t.damage_label === 'Low' ? 'var(--positive)' : t.damage_label === 'Medium' ? 'var(--warning)' : 'var(--negative)'}">${t.damage_label}</span>
          </div>
        </div>
      </div>`).join('')}
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

// Tier definitions: multiplier of fair rent
const RENT_TIERS = [
  { label: 'Very Low', mult: 0.65, color: 'green',  stay_mult: 2.0, damage_mult: 0.30, pay_adj:  0.02, activeClass: 'active-vlow'  },
  { label: 'Low',      mult: 0.80, color: 'green',  stay_mult: 1.4, damage_mult: 0.60, pay_adj:  0.01, activeClass: 'active-low'   },
  { label: 'Average',  mult: 1.00, color: 'blue',   stay_mult: 1.0, damage_mult: 1.00, pay_adj:  0.00, activeClass: 'active-avg'   },
  { label: 'High',     mult: 1.25, color: 'orange', stay_mult: 0.7, damage_mult: 1.60, pay_adj: -0.08, activeClass: 'active-high'  },
  { label: 'Very High',mult: 1.50, color: 'red',    stay_mult: 0.4, damage_mult: 2.50, pay_adj: -0.18, activeClass: 'active-vhigh' },
];

function showRentSettingModal(propId, applicantIdx) {
  const t = _applicants[applicantIdx];
  if (!t) return;
  _selectedTier = 2; // default Average
  renderRentModal(propId, applicantIdx, t);
}

function renderRentModal(propId, applicantIdx, t) {
  const tier    = RENT_TIERS[_selectedTier];
  const rent    = Math.round(_fairRent * tier.mult);
  const colors  = { green: 'var(--positive)', blue: '#1565C0', orange: 'var(--warning)', red: 'var(--negative)' };
  const color   = colors[tier.color] || 'var(--text)';
  const btnHtml = RENT_TIERS.map((tr, i) =>
    `<button class="tier-pick-btn ${i === _selectedTier ? tr.activeClass : ''}" onclick="selectRentTier(${propId},${applicantIdx},${i})">${tr.label}</button>`
  ).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${t.icon} Set Your Rent</div>
    <div class="modal-subtitle">${t.name} · Fair market rate: ${fmt(_fairRent)}/wk</div>
    <div class="tier-picker">${btnHtml}</div>
    <div style="text-align:center;margin-bottom:12px">
      <div style="font-size:28px;font-weight:800;color:${color}">${fmt(rent)}<span style="font-size:14px;font-weight:600">/wk</span></div>
    </div>
    <div style="background:var(--surface-2);border-radius:var(--radius-sm);padding:12px;border:2px solid ${color};margin-bottom:12px">
      <div style="font-size:14px;font-weight:800;color:${color};margin-bottom:8px">${tier.label} Rent Effects</div>
      <div class="money-row"><span class="mr-label">Tenant Stay</span><span class="mr-value" style="color:${color}">${tier.stay_mult >= 1 ? '+' : ''}${Math.round((tier.stay_mult-1)*100)}% vs average</span></div>
      <div class="money-row"><span class="mr-label">Damage Risk</span><span class="mr-value" style="color:${color}">${tier.damage_mult >= 1 ? '+' : ''}${Math.round((tier.damage_mult-1)*100)}%</span></div>
      <div class="money-row"><span class="mr-label">Pay Reliability</span><span class="mr-value" style="color:${color}">${tier.pay_adj >= 0 ? '+' : ''}${Math.round(tier.pay_adj*100)}%</span></div>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="showTenantsModal(${propId})">← Back</button>
      <button class="btn btn-primary" onclick="confirmRentSetting(${propId},${applicantIdx})">Sign Lease</button>
    </div>`);
}

function selectRentTier(propId, applicantIdx, tierIdx) {
  _selectedTier = tierIdx;
  const t = _applicants[applicantIdx];
  renderRentModal(propId, applicantIdx, t);
}

async function confirmRentSetting(propId, applicantIdx) {
  const tier = RENT_TIERS[_selectedTier];
  const rent = Math.round(_fairRent * tier.mult);
  const res  = await api('/rent', 'POST', { prop_id: propId, applicant_idx: applicantIdx, rent_amount: rent });
  if (res.error) { toast(res.error, 'error'); return; }
  toast('Lease signed! Tenant moved in.', 'success');
  closeModal();
  await refreshState();
  renderAll();
}

function getRentTier(rent, fairRent) {
  if (!fairRent) return { tier: 'Average', color: 'blue', stay_mult: 1, damage_mult: 1, pay_adj: 0 };
  const ratio = rent / fairRent;
  if (ratio < 0.70) return { tier: 'Very Low',  color: 'green',  stay_mult: 2.0, damage_mult: 0.30, pay_adj:  0.02 };
  if (ratio < 0.85) return { tier: 'Low',        color: 'green',  stay_mult: 1.4, damage_mult: 0.60, pay_adj:  0.01 };
  if (ratio < 1.15) return { tier: 'Average',    color: 'blue',   stay_mult: 1.0, damage_mult: 1.00, pay_adj:  0.00 };
  if (ratio < 1.35) return { tier: 'High',       color: 'orange', stay_mult: 0.7, damage_mult: 1.60, pay_adj: -0.08 };
  return               { tier: 'Very High',   color: 'red',    stay_mult: 0.4, damage_mult: 2.50, pay_adj: -0.18 };
}

function rentTierBadge(tier) {
  const map = { 'Very Low': 'badge-premium', 'Low': 'badge-mid', 'Average': 'badge-mid',
                'High': 'badge-budget', 'Very High': 'badge-budget' };
  return tier ? `<span class="card-badge ${map[tier] || 'badge-mid'}">${tier} Rent</span>` : '';
}

// ── Renovation Choice Modal ───────────────────────────────────────────────────
const ALL_MG_TYPES = ['quicktap','sweetspot','sequence','rapidpress','colormatch','reactiontap'];
function randomMgType() { return ALL_MG_TYPES[Math.floor(Math.random() * ALL_MG_TYPES.length)]; }

function launchMgByType(mgType, upgradeKey) {
  if      (mgType === 'quicktap')    launchQuickTap(upgradeKey);
  else if (mgType === 'sweetspot')   launchSweetSpot(upgradeKey);
  else if (mgType === 'sequence')    launchSequence(upgradeKey);
  else if (mgType === 'rapidpress')  launchRapidPress(upgradeKey);
  else if (mgType === 'colormatch')  launchColorMatch(upgradeKey);
  else if (mgType === 'reactiontap') launchReactionTap(upgradeKey);
}

async function showContractorModal(propId, upgradeKey) {
  pendingUpgrade = { propId, upgradeKey };
  const upgData  = await api(`/property/${propId}/upgrades`);
  const upg      = upgData.available.find(u => u.key === upgradeKey);
  if (!upg) return;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${upg.icon} ${upg.name}</div>
    <div class="modal-subtitle">Adds up to +${fmt(upg.value_add)} value · You have ${fmt(upgData.cash)}</div>

    <div class="contractor-card" style="border-color:var(--primary);margin-bottom:8px" onclick="startDIY('${upgradeKey}')">
      <div class="contractor-header">
        <span class="contractor-icon">🧰</span>
        <span class="contractor-name">Do It Yourself</span>
        <span class="contractor-cost" style="color:var(--positive)">FREE</span>
      </div>
      <div class="contractor-desc">Play a random mini-game (6 possible). How well you do = work quality.</div>
      <div class="contractor-quality">Quality range: 0–100 based on your skill</div>
    </div>

    <div style="text-align:center;font-size:11px;color:var(--text-muted);margin-bottom:8px">── or hire a contractor ──</div>

    ${Object.entries(upgData.contractors).map(([key, c]) => `
      <div class="contractor-card" onclick="hireContractor('${key}')">
        <div class="contractor-header">
          <span class="contractor-icon">${c.icon}</span>
          <span class="contractor-name">${c.name}</span>
          <span class="contractor-cost">${fmt(upg.costs[key])}</span>
        </div>
        <div class="contractor-desc">${c.desc}</div>
        <div class="contractor-quality">Quality: ${c.q_min}–${c.q_max}/100</div>
      </div>`).join('')}
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

function startDIY(upgradeKey) {
  if (!pendingUpgrade) return;
  _mg = { isRepair: false };
  launchMgByType(randomMgType(), upgradeKey);
}

async function finishDIY(upgradeKey, score) {
  if (_mg.isRepair) { await finishRepairDIY(score); return; }
  const { propId } = pendingUpgrade;
  const res = await api('/diy_renovate', 'POST', { prop_id: propId, upgrade_key: upgradeKey, quality: score });
  pendingUpgrade = null;
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🧰 DIY Complete!</div>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:40px;font-weight:900;color:${res.quality >= 70 ? 'var(--positive)' : res.quality >= 40 ? 'var(--warning)' : 'var(--negative)'}">${res.quality}<span style="font-size:18px">/100</span></div>
      <div style="font-size:13px;color:var(--text-muted)">work quality</div>
      <div class="mg-score-bar" style="margin:8px 16px"><div class="mg-score-fill" style="width:${res.quality}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">New Condition</span><span class="mr-value">${res.condition}/100</span></div>
    <div class="money-row"><span class="mr-label">New Market Value</span><span class="mr-value green">${fmt(res.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">New Weekly Rent</span><span class="mr-value green">${fmt(res.weekly_rent)}/wk</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Done</button>`);
  await refreshState();
  renderAll();
}

async function hireContractor(contractorKey) {
  if (!pendingUpgrade) return;
  const { propId, upgradeKey } = pendingUpgrade;
  const res = await api('/renovate', 'POST', { prop_id: propId, upgrade_key: upgradeKey, contractor_key: contractorKey });
  if (res.error) { toast(res.error, 'error'); return; }
  pendingUpgrade = null;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🎉 Renovation Complete!</div>
    <div class="money-row"><span class="mr-label">Work Quality</span><span class="mr-value">${res.quality}/100</span></div>
    <div class="money-row"><span class="mr-label">New Condition</span><span class="mr-value">${res.condition}/100</span></div>
    <div class="money-row"><span class="mr-label">New Market Value</span><span class="mr-value green">${fmt(res.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Done</button>`);
  await refreshState();
  renderAll();
}

// ── Mini-game: Quick Tap ──────────────────────────────────────────────────────
// 8 targets appear one at a time. Each shrinks over 1.5s. Tap/click to score.
function launchQuickTap(upgradeKey) {
  _mg = { ..._mg, hits: 0, total: 8, current: 0, active: false, upgradeKey };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🎯 Quick Tap</div>
      <div class="mg-desc">Tap the circles before they shrink away! 8 targets total.</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="qt-hits">0</div><div>Hits</div></div>
        <div><div class="mg-stat-val" id="qt-left">8</div><div>Left</div></div>
      </div>
      <div class="mg-tap-area" id="qt-area"></div>
    </div>
    <button class="btn btn-primary btn-full" id="qt-start-btn" onclick="qtStart()">▶ Start Game</button>`);
}

function qtStart() {
  document.getElementById('qt-start-btn').style.display = 'none';
  _mg.current = 0;
  _mg.hits    = 0;
  qtNextTarget();
}

function qtNextTarget() {
  if (_mg.current >= _mg.total) { qtFinish(); return; }
  const area = document.getElementById('qt-area');
  if (!area) return;
  const size  = 52;
  const areaW = area.offsetWidth  - size - 10;
  const areaH = area.offsetHeight - size - 10;
  const x     = Math.floor(Math.random() * areaW) + 5;
  const y     = Math.floor(Math.random() * areaH) + 5;
  const emojis = ['🔴','🟠','🟡','🟢','🔵','🟣'];
  const emoji  = emojis[_mg.current % emojis.length];

  const el = document.createElement('div');
  el.className = 'mg-target';
  el.style.cssText = `left:${x}px;top:${y}px;width:${size}px;height:${size}px`;
  el.textContent   = emoji;
  el.id            = 'qt-target';
  area.appendChild(el);
  _mg.current++;
  _mg.active = true;

  const miss = setTimeout(() => {
    if (el.parentNode) el.remove();
    _mg.active = false;
    document.getElementById('qt-left').textContent = _mg.total - _mg.current;
    setTimeout(qtNextTarget, 200);
  }, 1500);

  el.addEventListener('click', () => {
    clearTimeout(miss);
    _mg.hits++;
    el.classList.add('hit');
    document.getElementById('qt-hits').textContent = _mg.hits;
    document.getElementById('qt-left').textContent = _mg.total - _mg.current;
    setTimeout(() => { if (el.parentNode) el.remove(); _mg.active = false; setTimeout(qtNextTarget, 150); }, 150);
  });
  el.addEventListener('touchstart', (e) => { e.preventDefault(); el.click(); }, { passive: false });
}

function qtFinish() {
  const score = Math.round((_mg.hits / _mg.total) * 100);
  setTimeout(() => finishDIY(_mg.upgradeKey, score), 400);
}

// ── Mini-game: Sweet Spot ─────────────────────────────────────────────────────
// Oscillating needle. Press LOCK when inside the green zone. 5 rounds, speeds up.
function launchSweetSpot(upgradeKey) {
  _mg = { ..._mg, round: 1, totalRounds: 5, scores: [], upgradeKey, animId: null, pos: 0, dir: 1, speed: 0.6 };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🎯 Sweet Spot</div>
      <div class="mg-desc">Press LOCK IT when the bar is in the green zone. 5 rounds — it speeds up!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="ss-round">1</div><div>Round</div></div>
        <div><div class="mg-stat-val" id="ss-score">—</div><div>Last Score</div></div>
      </div>
      <div class="mg-bar-wrap" id="ss-bar">
        <div class="mg-zone"  id="ss-zone"></div>
        <div class="mg-needle" id="ss-needle"></div>
      </div>
      <button class="mg-lock-btn" id="ss-btn" onclick="ssLock()" style="display:none">🔒 LOCK IT!</button>
    </div>
    <button class="btn btn-primary btn-full" id="ss-start-btn" onclick="ssStart()">▶ Start Game</button>`);
}

function ssStart() {
  document.getElementById('ss-start-btn').style.display = 'none';
  document.getElementById('ss-btn').style.display = 'block';
  const bar   = document.getElementById('ss-bar');
  const zone  = document.getElementById('ss-zone');
  const zoneW = 28; // % of bar width
  zone.style.left  = `${(100 - zoneW) / 2}%`;
  zone.style.width = `${zoneW}%`;
  ssAnimate();
}

function ssAnimate() {
  const needle = document.getElementById('ss-needle');
  if (!needle) return;
  _mg.pos += _mg.dir * _mg.speed;
  if (_mg.pos >= 92) { _mg.pos = 92; _mg.dir = -1; }
  if (_mg.pos <= 2)  { _mg.pos = 2;  _mg.dir =  1; }
  needle.style.left = `${_mg.pos}%`;
  _mg.animId = requestAnimationFrame(ssAnimate);
}

function ssLock() {
  cancelAnimationFrame(_mg.animId);
  const zoneLeft  = 36;  // (100 - 28) / 2
  const zoneRight = 64;  // zoneLeft + 28
  const center    = 50;
  const pos       = _mg.pos;
  let roundScore  = 0;
  if (pos >= zoneLeft && pos <= zoneRight) {
    const dist    = Math.abs(pos - center);
    roundScore    = Math.round(100 - (dist / 14) * 60);  // 40–100 if in zone
  }
  _mg.scores.push(roundScore);
  document.getElementById('ss-score').textContent = roundScore;
  document.getElementById('ss-round').textContent = _mg.round + 1;

  if (_mg.round >= _mg.totalRounds) {
    const avg = Math.round(_mg.scores.reduce((a, b) => a + b, 0) / _mg.scores.length);
    setTimeout(() => finishDIY(_mg.upgradeKey, avg), 400);
    return;
  }
  _mg.round++;
  _mg.speed += 0.25;  // speeds up each round
  setTimeout(() => { _mg.animId = requestAnimationFrame(ssAnimate); }, 500);
}

// ── Mini-game: Sequence ───────────────────────────────────────────────────────
// Watch a color pattern light up. Repeat it in order. 5 rounds, grows longer.
const SEQ_COLORS = ['#E53935','#1E88E5','#43A047','#F9A825'];
const SEQ_EMOJIS = ['🔴','🔵','🟢','🟡'];
const SEQ_LENGTHS = [3, 3, 4, 4, 5];

function launchSequence(upgradeKey) {
  _mg = { ..._mg, round: 0, seq: [], playerSeq: [], totalRounds: 5, correct: 0, showing: false, upgradeKey };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🎯 Sequence</div>
      <div class="mg-desc">Watch the pattern light up, then repeat it in order!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="seq-round">1</div><div>Round</div></div>
        <div><div class="mg-stat-val" id="seq-correct">0</div><div>Correct</div></div>
      </div>
      <div class="mg-seq-grid">
        ${SEQ_COLORS.map((c, i) => `<button class="mg-seq-btn" id="seq-btn-${i}" style="background:${c}" onclick="seqPress(${i})">${SEQ_EMOJIS[i]}</button>`).join('')}
      </div>
      <div id="seq-status" style="text-align:center;font-size:13px;color:var(--text-muted)">Watch the pattern…</div>
    </div>
    <button class="btn btn-primary btn-full" id="seq-start-btn" onclick="seqStart()">▶ Start Game</button>`);
}

function seqStart() {
  document.getElementById('seq-start-btn').style.display = 'none';
  seqNewRound();
}

function seqNewRound() {
  _mg.seq = [];
  const len = SEQ_LENGTHS[_mg.round];
  for (let i = 0; i < len; i++) _mg.seq.push(Math.floor(Math.random() * 4));
  _mg.playerSeq = [];
  _mg.showing   = true;
  document.getElementById('seq-status').textContent = 'Watch carefully…';
  seqShowSequence(0);
}

function seqShowSequence(idx) {
  if (idx >= _mg.seq.length) {
    _mg.showing = false;
    document.getElementById('seq-status').textContent = 'Your turn! Repeat the pattern.';
    return;
  }
  const btn = document.getElementById(`seq-btn-${_mg.seq[idx]}`);
  if (!btn) return;
  setTimeout(() => {
    btn.classList.add('lit');
    setTimeout(() => {
      btn.classList.remove('lit');
      setTimeout(() => seqShowSequence(idx + 1), 250);
    }, 500);
  }, idx === 0 ? 400 : 0);
}

function seqPress(idx) {
  if (_mg.showing) return;
  const btn = document.getElementById(`seq-btn-${idx}`);
  btn.classList.add('active');
  setTimeout(() => btn.classList.remove('active'), 200);

  _mg.playerSeq.push(idx);
  const pos = _mg.playerSeq.length - 1;

  if (_mg.playerSeq[pos] !== _mg.seq[pos]) {
    // Wrong
    btn.classList.add('wrong');
    setTimeout(() => btn.classList.remove('wrong'), 400);
    _mg.round++;
    document.getElementById('seq-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
    if (_mg.round >= _mg.totalRounds) { seqFinish(); return; }
    _mg.showing = true;
    setTimeout(seqNewRound, 800);
    return;
  }

  if (_mg.playerSeq.length === _mg.seq.length) {
    // Correct round
    _mg.correct++;
    document.getElementById('seq-correct').textContent = _mg.correct;
    _mg.round++;
    document.getElementById('seq-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
    if (_mg.round >= _mg.totalRounds) { seqFinish(); return; }
    _mg.showing = true;
    document.getElementById('seq-status').textContent = '✓ Correct! Next round…';
    setTimeout(seqNewRound, 700);
  }
}

function seqFinish() {
  const score = Math.round((_mg.correct / _mg.totalRounds) * 100);
  setTimeout(() => finishDIY(_mg.upgradeKey, score), 400);
}

// ── Mini-game: Rapid Press ────────────────────────────────────────────────────
// Mash the button as fast as possible in 3 seconds. 30 presses = 100%.
function launchRapidPress(upgradeKey) {
  _mg = { ..._mg, presses: 0, target: 30, upgradeKey, running: false, timerId: null };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">💪 Rapid Press</div>
      <div class="mg-desc">Mash the button as fast as you can — 3 seconds!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="rp-count">0</div><div>Presses</div></div>
        <div><div class="mg-stat-val" id="rp-time">3.0</div><div>Seconds</div></div>
      </div>
      <div class="mg-score-bar" style="margin-bottom:12px"><div class="mg-score-fill" id="rp-bar" style="width:0%"></div></div>
      <button class="mg-rapid-btn" id="rp-btn" onclick="rpPress()" style="display:none">PRESS!</button>
    </div>
    <button class="btn btn-primary btn-full" id="rp-start" onclick="rpStart()">▶ Start Game</button>`);
}

function rpStart() {
  document.getElementById('rp-start').style.display = 'none';
  document.getElementById('rp-btn').style.display   = 'block';
  _mg.running = true;
  _mg.presses = 0;
  const end = Date.now() + 3000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, end - Date.now());
    const el = document.getElementById('rp-time');
    if (el) el.textContent = (left / 1000).toFixed(1);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      const btn = document.getElementById('rp-btn');
      if (btn) { btn.textContent = 'Time!'; btn.disabled = true; }
      const score = Math.min(100, Math.round((_mg.presses / _mg.target) * 100));
      setTimeout(() => finishDIY(_mg.upgradeKey, score), 600);
    }
  }, 50);
}

function rpPress() {
  if (!_mg.running) return;
  _mg.presses++;
  const pct = Math.min(100, Math.round((_mg.presses / _mg.target) * 100));
  document.getElementById('rp-count').textContent = _mg.presses;
  const bar = document.getElementById('rp-bar');
  if (bar) bar.style.width = pct + '%';
}

// ── Mini-game: Color Match ────────────────────────────────────────────────────
// A color flashes at the top. Pick the matching button from 4. 8 rounds, speeds up.
const CM_COLORS = [
  { name: 'RED',    bg: '#E53935', label: '🔴 RED'    },
  { name: 'BLUE',   bg: '#1E88E5', label: '🔵 BLUE'   },
  { name: 'GREEN',  bg: '#43A047', label: '🟢 GREEN'  },
  { name: 'YELLOW', bg: '#F9A825', label: '🟡 YELLOW' },
];

function launchColorMatch(upgradeKey) {
  _mg = { ..._mg, round: 0, totalRounds: 8, correct: 0, upgradeKey, waiting: false, timerId: null, timeLimit: 1400 };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🎨 Color Match</div>
      <div class="mg-desc">Tap the button that matches the color shown! Gets faster!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="cm-correct">0</div><div>Correct</div></div>
        <div><div class="mg-stat-val" id="cm-round">1</div><div>Round</div></div>
      </div>
      <div class="mg-color-show" id="cm-show">?</div>
      <div class="mg-color-grid">
        ${CM_COLORS.map((c, i) => `<button class="mg-color-btn" id="cm-btn-${i}" style="background:${c.bg}" onclick="cmPress(${i})">${c.label}</button>`).join('')}
      </div>
    </div>
    <button class="btn btn-primary btn-full" id="cm-start" onclick="cmStart()">▶ Start Game</button>`);
}

function cmStart() {
  document.getElementById('cm-start').style.display = 'none';
  cmNextRound();
}

function cmNextRound() {
  if (_mg.round >= _mg.totalRounds) {
    const score = Math.round((_mg.correct / _mg.totalRounds) * 100);
    setTimeout(() => finishDIY(_mg.upgradeKey, score), 400);
    return;
  }
  _mg.target = Math.floor(Math.random() * 4);
  const c = CM_COLORS[_mg.target];
  const show = document.getElementById('cm-show');
  if (!show) return;
  show.style.background = c.bg;
  show.textContent      = c.name;
  _mg.waiting  = true;
  _mg.timeLimit = Math.max(700, 1400 - _mg.round * 100);
  clearTimeout(_mg.timerId);
  _mg.timerId = setTimeout(() => {
    if (_mg.waiting) {
      _mg.waiting = false;
      CM_COLORS.forEach((_, i) => {
        const b = document.getElementById(`cm-btn-${i}`);
        if (b) b.classList.remove('correct','wrong');
      });
      _mg.round++;
      document.getElementById('cm-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
      setTimeout(cmNextRound, 300);
    }
  }, _mg.timeLimit);
}

function cmPress(idx) {
  if (!_mg.waiting) return;
  _mg.waiting = false;
  clearTimeout(_mg.timerId);
  const btn = document.getElementById(`cm-btn-${idx}`);
  if (idx === _mg.target) {
    _mg.correct++;
    if (btn) btn.classList.add('correct');
    document.getElementById('cm-correct').textContent = _mg.correct;
  } else {
    if (btn) btn.classList.add('wrong');
    const correct = document.getElementById(`cm-btn-${_mg.target}`);
    if (correct) correct.classList.add('correct');
  }
  _mg.round++;
  document.getElementById('cm-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
  setTimeout(() => {
    CM_COLORS.forEach((_, i) => {
      const b = document.getElementById(`cm-btn-${i}`);
      if (b) b.classList.remove('correct','wrong');
    });
    cmNextRound();
  }, 500);
}

// ── Mini-game: Reaction Tap ───────────────────────────────────────────────────
// Traffic light: wait for GREEN then tap as fast as possible. 5 rounds.
function launchReactionTap(upgradeKey) {
  _mg = { ..._mg, round: 0, totalRounds: 5, times: [], upgradeKey, greenAt: 0, waiting: false, timerId: null };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🚦 Reaction Tap</div>
      <div class="mg-desc">Wait for the light to turn GREEN, then tap as fast as possible!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="rt-round">1</div><div>Round</div></div>
        <div><div class="mg-stat-val" id="rt-best">—</div><div>Best (ms)</div></div>
      </div>
      <div class="mg-reaction-light" id="rt-light">🔴</div>
      <button class="mg-reaction-tap-btn" id="rt-tap" onclick="rtTap()" disabled>Wait for green…</button>
    </div>
    <button class="btn btn-primary btn-full" id="rt-start" onclick="rtStart()">▶ Start Game</button>`);
}

function rtStart() {
  document.getElementById('rt-start').style.display = 'none';
  rtNextRound();
}

function rtNextRound() {
  if (_mg.round >= _mg.totalRounds) {
    const avg  = _mg.times.length ? _mg.times.reduce((a,b)=>a+b,0)/_mg.times.length : 2000;
    const score = Math.min(100, Math.max(0, Math.round(100 - (avg - 200) / 12)));
    setTimeout(() => finishDIY(_mg.upgradeKey, score), 400);
    return;
  }
  const light = document.getElementById('rt-light');
  const btn   = document.getElementById('rt-tap');
  if (!light || !btn) return;
  light.className  = 'mg-reaction-light';
  light.textContent = '🔴';
  btn.disabled     = true;
  btn.textContent  = 'Wait for green…';
  _mg.waiting      = false;
  const delay = 1500 + Math.random() * 2500;
  clearTimeout(_mg.timerId);
  _mg.timerId = setTimeout(() => {
    light.className  = 'mg-reaction-light go';
    light.textContent = '🟢';
    btn.disabled     = false;
    btn.textContent  = '⚡ TAP!';
    _mg.greenAt  = Date.now();
    _mg.waiting  = true;
    // auto-fail if too slow (2s)
    _mg.timerId = setTimeout(() => {
      if (_mg.waiting) {
        _mg.waiting = false;
        _mg.times.push(2000);
        _mg.round++;
        document.getElementById('rt-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
        btn.disabled = true;
        light.className = 'mg-reaction-light';
        light.textContent = '❌';
        setTimeout(rtNextRound, 700);
      }
    }, 2000);
  }, delay);
}

function rtTap() {
  if (!_mg.waiting) {
    // Tapped too early!
    const light = document.getElementById('rt-light');
    if (light && !light.classList.contains('go')) {
      light.textContent = '⚠️';
      clearTimeout(_mg.timerId);
      _mg.times.push(2000);
      _mg.round++;
      document.getElementById('rt-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
      setTimeout(rtNextRound, 700);
    }
    return;
  }
  _mg.waiting = false;
  clearTimeout(_mg.timerId);
  const reaction = Date.now() - _mg.greenAt;
  _mg.times.push(reaction);
  const best = Math.min(..._mg.times);
  document.getElementById('rt-best').textContent = best;
  const btn   = document.getElementById('rt-tap');
  const light = document.getElementById('rt-light');
  if (btn)   btn.textContent  = `${reaction}ms!`;
  if (light) light.textContent = reaction < 400 ? '⚡' : '✅';
  _mg.round++;
  document.getElementById('rt-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
  setTimeout(rtNextRound, 800);
}

// ── Advance Time ──────────────────────────────────────────────────────────────
async function advanceDays(days) {
  const res = await api('/advance', 'POST', { days });
  const s   = getSeasonInfo(res.day);
  const eventsHtml = res.events.length === 0
    ? '<p class="text-muted text-center" style="padding:16px 0">Nothing happened.</p>'
    : res.events.map(e => `
      <div class="event-item">
        <div class="event-dot ${e.type}"></div>
        <div class="event-info">
          <div class="event-prop">${e.prop}</div>
          <div class="event-text ${e.type}">${e.text}</div>
        </div>
      </div>`).join('');

  _pendingRepairs = res.repairs || [];
  const repairNote = _pendingRepairs.length > 0
    ? `<div style="background:var(--warning-bg,#FFF8E1);border:2px solid var(--warning);border-radius:var(--radius-sm);padding:10px 12px;margin-top:12px;font-size:13px;font-weight:700">
        🔧 ${_pendingRepairs.length} repair${_pendingRepairs.length > 1 ? 's' : ''} need${_pendingRepairs.length === 1 ? 's' : ''} attention!</div>`
    : '';

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${s.icon} ${s.name} · Day ${s.seasonDay}</div>
    <div class="modal-subtitle">Year ${s.year} · Overall Day ${res.day}</div>
    <div class="money-row"><span class="mr-label">Cash</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Net Worth</span><span class="mr-value green">${fmt(res.net_worth)}</span></div>
    <div class="section-title" style="margin-bottom:8px">Events</div>
    ${eventsHtml}
    ${repairNote}
    <button class="btn btn-primary btn-full mt-8" onclick="continueFromEvents()">
      ${_pendingRepairs.length > 0 ? `Fix Repairs (${_pendingRepairs.length})` : 'Continue'}
    </button>`);

  await refreshState();
  renderAll();
}

function continueFromEvents() {
  if (_pendingRepairs.length > 0) {
    showNextRepair();
  } else {
    closeModal();
  }
}

function showNextRepair() {
  if (_pendingRepairs.length === 0) { closeModal(); return; }
  _currentRepair = _pendingRepairs.shift();
  showRepairModal(_currentRepair);
}

function showRepairModal(repair) {
  const rt = repair.repair_type;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${rt.icon} ${rt.name}</div>
    <div class="modal-subtitle">${repair.prop_name}</div>
    <p style="font-size:13px;color:var(--text-2);margin-bottom:12px">Your tenant reported a problem. Address it now or ignore and let the condition drop.</p>

    <div class="contractor-card" style="border-color:var(--primary);margin-bottom:8px" onclick="startRepairDIY()">
      <div class="contractor-header">
        <span class="contractor-icon">🧰</span>
        <span class="contractor-name">Fix It Yourself</span>
        <span class="contractor-cost" style="color:var(--positive)">FREE</span>
      </div>
      <div class="contractor-desc">Play a random mini-game. Your score = repair quality.</div>
    </div>

    <div style="text-align:center;font-size:11px;color:var(--text-muted);margin-bottom:8px">── or hire a contractor ──</div>

    ${Object.entries(repair.costs).map(([key, cost]) => {
      const cNames = { budget: '🔨 Budget Bob', standard: '🛠️ Standard Steve', premium: '⭐ Premier Pete' };
      return `<div class="contractor-card" onclick="fixRepairContractor('${key}')">
        <div class="contractor-header">
          <span class="contractor-name">${cNames[key] || key}</span>
          <span class="contractor-cost">${fmt(cost)}</span>
        </div>
      </div>`;
    }).join('')}

    <button class="btn btn-danger btn-sm btn-full mt-8" onclick="ignoreRepair()">
      Ignore — Condition −${rt.cond_loss}
    </button>
    ${_pendingRepairs.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingRepairs.length} more repair(s) after this</div>` : ''}`);
}

function startRepairDIY() {
  const types = ['quicktap','sweetspot','sequence','rapidpress','colormatch','reactiontap'];
  const mgType = types[Math.floor(Math.random() * types.length)];
  _mg = { isRepair: true };
  launchMgByType(mgType, null);
}

async function fixRepairContractor(contractorKey) {
  const repair = _currentRepair;
  const res = await api('/repair/fix', 'POST', {
    prop_id: repair.prop_id, repair_key: repair.repair_type.key,
    method: contractorKey,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Repaired! Condition now ${res.condition}/100`, 'success');
  await refreshState();
  renderAll();
  showNextRepair();
}

async function finishRepairDIY(score) {
  const repair = _currentRepair;
  const res = await api('/repair/fix', 'POST', {
    prop_id: repair.prop_id, repair_key: repair.repair_type.key,
    method: 'diy', quality: score,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🔧 Repair Done!</div>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:40px;font-weight:900;color:${res.quality >= 70 ? 'var(--positive)' : res.quality >= 40 ? 'var(--warning)' : 'var(--negative)'}">${res.quality}<span style="font-size:18px">/100</span></div>
      <div style="font-size:13px;color:var(--text-muted)">work quality</div>
      <div class="mg-score-bar" style="margin:8px 16px"><div class="mg-score-fill" style="width:${res.quality}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Property Condition</span><span class="mr-value">${res.condition}/100</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="nextRepairFromResult()">
      ${_pendingRepairs.length > 0 ? `Next Repair (${_pendingRepairs.length})` : 'Done'}
    </button>`);
  await refreshState();
  renderAll();
}

function nextRepairFromResult() {
  showNextRepair();
}

async function ignoreRepair() {
  const repair = _currentRepair;
  const res = await api('/repair/ignore', 'POST', {
    prop_id: repair.prop_id, repair_key: repair.repair_type.key,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Ignored — condition dropped to ${res.condition}`, 'warning');
  await refreshState();
  renderAll();
  showNextRepair();
}

// ── Bank ──────────────────────────────────────────────────────────────────────
async function renderBank() {
  const data = await api('/bank/products');
  const bank = state.bank || { savings: 0, loans: [] };
  const tier = state.savings_tier || data.savings_tiers[0];

  const nextTier  = data.savings_tiers.find(t => t.min > bank.savings);
  const toNextLbl = nextTier ? `${fmt(nextTier.min - bank.savings)} more to ${nextTier.label}` : 'Max tier reached!';
  const tierClass = tier.label === 'Basic' ? 'budget' : tier.label === 'Standard' ? 'mid' : 'premium';

  document.getElementById('bank-savings-section').innerHTML = `
    <div class="section-header"><span class="section-title">💰 Savings Account</span></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div>
          <div style="font-size:26px;font-weight:800;color:var(--positive)">${fmt(bank.savings)}</div>
          <div style="font-size:12px;color:var(--text-muted)">current balance</div>
        </div>
        <div style="text-align:right">
          <div class="card-badge badge-${tierClass}">${tier.label} Tier</div>
          <div style="font-size:13px;font-weight:700;color:var(--positive);margin-top:4px">${tier.apr}% APR</div>
        </div>
      </div>
      <div class="condition-wrap">
        <div class="condition-top"><span class="condition-lbl">Tier Progress</span><span class="condition-val">${toNextLbl}</span></div>
        <div class="condition-bar"><div class="condition-fill cond-great" style="width:${nextTier ? Math.min(100,(bank.savings/nextTier.min)*100) : 100}%"></div></div>
      </div>
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:10px">
        ${data.savings_tiers.map(t => `<span style="margin-right:8px">${t.label}: ${t.apr}% (${fmt(t.min)}+)</span>`).join('')}
      </div>
      <div class="btn-row">
        <button class="btn btn-primary btn-sm" onclick="showDepositModal()">⬆ Deposit</button>
        <button class="btn btn-ghost btn-sm ${bank.savings === 0 ? 'btn-disabled' : ''}" onclick="showWithdrawModal()" ${bank.savings === 0 ? 'disabled' : ''}>⬇ Withdraw</button>
      </div>
    </div>`;

  const loansHtml = bank.loans?.length > 0
    ? bank.loans.map(l => {
        const pct = Math.max(5, Math.min(100, (l.balance / (l.monthly_payment * l.term)) * 100));
        return `<div class="card">
          <div class="card-header">
            <div class="card-icon">${l.icon}</div>
            <div style="flex:1">
              <div class="card-title">${l.product}</div>
              <div class="card-subtitle">${fmt(l.monthly_payment)}/mo · ${l.term - l.months_paid} payments left</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:16px;font-weight:800;color:var(--negative)">${fmt(Math.ceil(l.balance))}</div>
              <div style="font-size:11px;color:var(--text-muted)">remaining</div>
            </div>
          </div>
          <div class="condition-wrap">
            <div class="condition-top"><span class="condition-lbl">Balance</span><span class="condition-val">${Math.round(100-pct)}% paid off</span></div>
            <div class="condition-bar"><div class="condition-fill cond-poor" style="width:${pct}%"></div></div>
          </div>
          <button class="btn btn-ghost btn-sm" onclick="showExtraPaymentModal(${l.id}, ${Math.ceil(l.balance)})">💸 Extra Payment</button>
        </div>`;}).join('')
    : '';

  document.getElementById('bank-loans-section').innerHTML = bank.loans?.length > 0
    ? `<div class="section-header"><span class="section-title">📄 Active Loans</span></div>${loansHtml}`
    : '';

  document.getElementById('bank-products-section').innerHTML = `
    <div class="section-header"><span class="section-title">🏦 Take Out a Loan</span></div>
    ${data.products.map(p => `
      <div class="card" style="cursor:pointer" onclick="showLoanModal('${p.key}')">
        <div class="card-header">
          <div class="card-icon">${p.icon}</div>
          <div style="flex:1">
            <div class="card-title">${p.name}</div>
            <div class="card-subtitle">${p.desc}</div>
          </div>
          <div style="text-align:right;flex-shrink:0">
            <div style="font-size:13px;font-weight:700;color:var(--negative)">${(p.apr*100).toFixed(0)}% APR</div>
            <div style="font-size:11px;color:var(--text-muted)">${p.term} mo term</div>
          </div>
        </div>
        <div class="money-row"><span class="mr-label">Range</span><span class="mr-value">${fmt(p.min)} – ${fmt(p.max)}</span></div>
        <div class="money-row"><span class="mr-label">Example Payment</span><span class="mr-value orange">${fmt(p.sample_payment)}/mo on ${fmt(p.min)}</span></div>
      </div>`).join('')}`;
}

function showLoanModal(productKey) {
  openModal(`<div class="modal-handle"></div><div class="modal-title">Loading…</div>`);
  api('/bank/products').then(data => {
    const p = data.products.find(x => x.key === productKey);
    openModal(`
      <div class="modal-handle"></div>
      <div class="modal-title">${p.icon} ${p.name}</div>
      <div class="modal-subtitle">${p.desc} · ${(p.apr*100).toFixed(0)}% APR · ${p.term} month term</div>
      <div style="margin-bottom:12px">
        <label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">Amount (${fmt(p.min)}–${fmt(p.max)})</label>
        <input id="loan-amount" type="number" min="${p.min}" max="${p.max}" step="500" value="${p.min}"
          style="width:100%;padding:10px;border:2px solid var(--border);border-radius:var(--radius-sm);font-size:16px;font-weight:700"
          oninput="previewLoan('${productKey}')">
      </div>
      <div id="loan-preview" class="card" style="background:var(--surface-2);margin-bottom:12px"></div>
      <div class="btn-row">
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="confirmLoan('${productKey}')">Take Out Loan</button>
      </div>`);
    previewLoan(productKey);
  });
}

async function previewLoan(productKey) {
  const amount = document.getElementById('loan-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/loan/preview', 'POST', { product_key: productKey, amount: parseInt(amount) });
  const el  = document.getElementById('loan-preview');
  if (!el) return;
  if (res.error) { el.innerHTML = `<p style="color:var(--negative);font-size:13px">${res.error}</p>`; return; }
  el.innerHTML = `
    <div class="money-row"><span class="mr-label">Monthly Payment</span><span class="mr-value orange">${fmt(res.monthly_payment)}/mo</span></div>
    <div class="money-row"><span class="mr-label">Term</span><span class="mr-value">${res.term} months</span></div>
    <div class="money-row"><span class="mr-label">Total Repaid</span><span class="mr-value">${fmt(res.total_repaid)}</span></div>
    <div class="money-row"><span class="mr-label">Total Interest</span><span class="mr-value red">${fmt(res.total_interest)}</span></div>`;
}

async function confirmLoan(productKey) {
  const amount = document.getElementById('loan-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/loan/take', 'POST', { product_key: productKey, amount: parseInt(amount) });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Loan approved! ${fmt(res.loan.monthly_payment)}/mo`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

function showExtraPaymentModal(loanId, balance) {
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">💸 Extra Loan Payment</div>
    <div class="modal-subtitle">Remaining: ${fmt(balance)} · Cash: ${fmt(state.cash)}</div>
    <input id="extra-pay-amount" type="number" min="1" max="${Math.min(balance, state.cash)}" step="100" value="${Math.min(balance, state.cash)}"
      style="width:100%;padding:10px;border:2px solid var(--border);border-radius:var(--radius-sm);font-size:16px;font-weight:700;margin-bottom:12px">
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="makeExtraPayment(${loanId})">Pay</button>
    </div>`);
}

async function makeExtraPayment(loanId) {
  const amount = document.getElementById('extra-pay-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/loan/pay', 'POST', { loan_id: loanId, amount: parseFloat(amount) });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(res.remaining <= 0 ? 'Loan fully paid off! 🎉' : `Payment made. ${fmt(res.remaining)} left.`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

function showDepositModal() {
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">⬆ Deposit to Savings</div>
    <div class="modal-subtitle">Cash available: ${fmt(state.cash)}</div>
    <input id="deposit-amount" type="number" min="1" max="${state.cash}" step="100" value="${Math.min(1000, state.cash)}"
      style="width:100%;padding:10px;border:2px solid var(--border);border-radius:var(--radius-sm);font-size:16px;font-weight:700;margin-bottom:12px">
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="doDeposit()">Deposit</button>
    </div>`);
}

async function doDeposit() {
  const amount = document.getElementById('deposit-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/savings/deposit', 'POST', { amount: parseInt(amount) });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Deposited ${fmt(parseInt(amount))} — ${res.tier.apr}% APR`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

function showWithdrawModal() {
  const savings = state.bank?.savings || 0;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">⬇ Withdraw from Savings</div>
    <div class="modal-subtitle">Balance: ${fmt(savings)}</div>
    <input id="withdraw-amount" type="number" min="1" max="${savings}" step="100" value="${savings}"
      style="width:100%;padding:10px;border:2px solid var(--border);border-radius:var(--radius-sm);font-size:16px;font-weight:700;margin-bottom:12px">
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="doWithdraw()">Withdraw</button>
    </div>`);
}

async function doWithdraw() {
  const amount = document.getElementById('withdraw-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/savings/withdraw', 'POST', { amount: parseInt(amount) });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Withdrew ${fmt(parseInt(amount))}`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

// ── Settings ──────────────────────────────────────────────────────────────────
function renderSettings() {
  const el = document.getElementById('page-settings');
  if (!el || !state) return;
  const s = getSeasonInfo(state.day);
  el.innerHTML = `
    <div class="section-header"><span class="section-title">⚙️ Settings</span></div>

    <div class="card">
      <div style="font-size:14px;font-weight:800;margin-bottom:12px">Game Info</div>
      <div class="money-row"><span class="mr-label">Current Day</span><span class="mr-value">${state.day}</span></div>
      <div class="money-row"><span class="mr-label">Season</span><span class="mr-value">${s.icon} ${s.name} — Year ${s.year}</span></div>
      <div class="money-row"><span class="mr-label">Cash on Hand</span><span class="mr-value">${fmt(state.cash)}</span></div>
      <div class="money-row"><span class="mr-label">Properties</span><span class="mr-value">${state.property_count}</span></div>
      <div class="money-row"><span class="mr-label">Net Worth</span><span class="mr-value green">${fmt(state.net_worth)}</span></div>
    </div>

    <div class="card" style="margin-top:12px">
      <div style="font-size:14px;font-weight:800;margin-bottom:8px">⚠️ Danger Zone</div>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px">This will permanently erase all progress and start a fresh game.</p>
      <button class="btn btn-danger btn-full" onclick="confirmReset()">🗑 Start New Game</button>
    </div>`;
}

// ── Reset ─────────────────────────────────────────────────────────────────────
function confirmReset() {
  showConfirmModal(
    'Start a New Game?',
    'This will erase all progress.',
    async () => {
      clearLocalState();
      await api('/reset', 'POST');
      closeModal();
      await refreshState();
      await loadMarket();
      renderAll();
      navTo('dashboard');
      toast('New game started!');
    }
  );
}

// ── Log ───────────────────────────────────────────────────────────────────────
function renderLog() {
  const el = document.getElementById('log-list');
  if (!el) return;
  if (!state.log || state.log.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No history yet</div></div>';
    return;
  }
  el.innerHTML = [...state.log].reverse().map(l => logItemHtml(l)).join('');
}

function logItemHtml(l) {
  return `
  <div class="log-item">
    <div class="log-dot ${l.type}"></div>
    <div class="log-text">${l.text}</div>
    <div class="log-month">Day ${l.day ?? l.month ?? '?'}</div>
  </div>`;
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(html) {
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  _pendingConfirm = null;
}

function runConfirm() {
  if (_pendingConfirm) _pendingConfirm();
}

function showConfirmModal(title, subtitle, onConfirm) {
  _pendingConfirm = onConfirm;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${title}</div>
    <div class="modal-subtitle">${subtitle}</div>
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="runConfirm()">Confirm</button>
    </div>`);
}

document.getElementById('modal-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = '') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  el.innerHTML = `${icons[type] ? `<span>${icons[type]}</span>` : ''}${msg}`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function fmt(n) {
  if (n === undefined || n === null) return '$0';
  const abs  = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1_000_000) return sign + '$' + (abs / 1_000_000).toFixed(1) + 'M';
  if (abs >= 1_000)     return sign + '$' + abs.toLocaleString();
  return sign + '$' + abs;
}

function condClass(c) {
  if (c >= 75) return 'cond-great';
  if (c >= 55) return 'cond-good';
  if (c >= 35) return 'cond-fair';
  return 'cond-poor';
}

function starsHtml(chance) {
  const full  = Math.round(chance * 5);
  const empty = 5 - full;
  return '★'.repeat(full) + '☆'.repeat(empty);
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
