// ── State ─────────────────────────────────────────────────────────────────────
let state           = null;
let marketListings  = [];
let marketHoodOpen  = {};   // tracks which hood sections are expanded; undefined = open
let currentFinTab   = 'bank'; // active sub-tab inside Finances
let currentPage     = 'dashboard';
let pendingUpgrade  = null;
let _applicants     = [];
let _fairRent       = 0;
let _selectedTier   = 2;       // default Average
let _pendingConfirm = null;

// ── Mini-game state ───────────────────────────────────────────────────────────
let _mg             = {};   // active mini-game state
let _pendingRepairs       = [];   // repair events queued after advancing
let _currentRepair        = null; // repair being handled right now
let _pendingJob           = null; // side job being played
let _pendingSquatter      = null; // squatter event queued after repairs
let _pendingMoraleEvents  = [];   // morale-choice events queued after repairs
let _pendingRenewalOffers = [];   // lease renewal offers queued after advancing

// ── Tenant window cache ───────────────────────────────────────────────────────
// Stores the maintenance window day per property, keyed by propId.
// Regenerated when the game day advances so the window stays stable within a day.
const _tenantWindowCache = {};
function getTenantAvailDay(propId) {
  const cached = _tenantWindowCache[propId];
  if (cached && cached.day === state.day) return cached.availDay;
  const availDay = state.day + Math.floor(Math.random() * 28) + 1;
  _tenantWindowCache[propId] = { day: state.day, availDay };
  return availDay;
}

// ── Seasons ───────────────────────────────────────────────────────────────────
const SEASONS = [
  { name: 'Spring', icon: '🌸' },
  { name: 'Summer', icon: '☀️' },
  { name: 'Fall',   icon: '🍂' },
  { name: 'Winter', icon: '❄️' },
];

const DAYS_PER_SEASON = 28;
const MAX_CONDITION   = 250;
const DAILY_ENERGY    = 10;  // fallback only; real max comes from state.max_energy
const DAYS_PER_YEAR   = DAYS_PER_SEASON * 4;  // 112

const PLAYER_HOME_DATA = [
  { key: 'moms_basement', name: "The Shed",         icon: '🛖',  cost:       0, max_energy: 10, recharge:  2, desc: "Your in-laws' backyard shed. No rent, no dignity." },
  { key: 'studio_apt',    name: 'Studio Apartment', icon: '🏠',  cost:    80000, max_energy: 12, recharge:  4, desc: 'Your own place — finally.' },
  { key: 'starter_house', name: 'Starter House',    icon: '🏡',  cost:   150000, max_energy: 14, recharge:  6, desc: 'A real house with a yard. Moving up!' },
  { key: 'modern_condo',  name: 'Modern Condo',     icon: '🏢',  cost:   200000, max_energy: 16, recharge:  8, desc: 'High-rise living with city views.' },
  { key: 'suburban_home', name: 'Suburban Home',    icon: '🏘️',  cost:   500000, max_energy: 18, recharge: 10, desc: 'Quiet neighborhood, big garage.' },
  { key: 'luxury_villa',  name: 'Mansion',          icon: '🏛️',  cost:  1000000, max_energy: 20, recharge: 12, desc: "Sprawling estate. You've made it." },
  { key: 'mansion',       name: 'Castle',           icon: '🏰',  cost: 10000000, max_energy: 30, recharge: 30, desc: 'Absolute excess. Full energy, every single day.' },
];

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
  const prevLevel = state ? (state.level ?? 0) : null;
  state = await api('/state');
  updateHeader();
  if (prevLevel !== null && state.level > prevLevel) {
    showLevelUpToast(state.level);
    await loadMarket();  // reload market since new neighborhoods may have unlocked
    renderMarket();
  }
}

async function loadMarket() {
  const data     = await api('/market');
  marketListings = data.listings;
}

// ── Header ────────────────────────────────────────────────────────────────────
function updateHeader() {
  document.getElementById('hdr-cash').textContent = fmt(state.cash);
  const energy = state.energy ?? DAILY_ENERGY;
  const maxE   = state.max_energy || DAILY_ENERGY;
  const energyEl = document.getElementById('hdr-energy');
  energyEl.textContent = `⚡ ${energy} / ${maxE}`;
  energyEl.style.color = energy === 0 ? 'var(--negative)' : energy <= 3 ? 'var(--warning)' : 'var(--positive)';
  const s = getSeasonInfo(state.day);
  document.getElementById('hdr-day').textContent  = `${s.icon} ${s.name} · Day ${s.seasonDay}`;
  // XP bar
  const lvl    = state.level ?? 0;
  const xpPct  = state.xp_pct ?? 0;
  const levelBadge = document.getElementById('hdr-level');
  const xpBar      = document.getElementById('hdr-xp-bar');
  const xpNextLbl  = document.getElementById('hdr-level-next');
  if (levelBadge) levelBadge.textContent = lvl >= 14 ? '⭐ Max Level' : `Level ${lvl}`;
  if (xpBar)      xpBar.style.width = `${xpPct}%`;
  if (xpNextLbl) {
    if (lvl === 0)       xpNextLbl.textContent = 'Sell your first property';
    else if (lvl >= 14)  xpNextLbl.textContent = 'Fully maxed out!';
    else                 xpNextLbl.textContent = `→ Level ${lvl + 1}`;
  }
}

// ── Level-up ──────────────────────────────────────────────────────────────────
const LEVEL_HOOD_NAMES = ['', 'Midtown', 'Northside', 'Westwood', 'Riverside', 'Newbay'];
const LEVEL_HOME_NAMES = ['', '', 'Studio Apartment', '', 'Starter House', '', 'Modern Condo', '', 'Suburban Home', '', 'Mansion', '', 'Castle', '', ''];

function showLevelUpToast(newLevel) {
  const hood = LEVEL_HOOD_NAMES[newLevel] || null;
  const home = LEVEL_HOME_NAMES[newLevel] || null;
  let unlocks = [];
  if (hood) unlocks.push(`🏙️ ${hood}`);
  if (home) unlocks.push(`🏠 ${home}`);
  const unlockLine = unlocks.length ? `<br><small style="opacity:0.85">Unlocked: ${unlocks.join(' · ')}</small>` : '';
  const el = document.createElement('div');
  el.className = 'toast success level-up-toast';
  el.innerHTML = `<span>⭐</span>Level ${newLevel} Reached!${unlockLine}`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 5000);
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
  if (page === 'finances') renderFinances();
  if (page === 'settings') renderSettings();
}

// ── Render All ────────────────────────────────────────────────────────────────
function renderAll() {
  renderDashboard();
  renderMarket();
  renderProperties();
  if (currentPage === 'settings') renderSettings();
  if (currentPage === 'finances') renderFinances();
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

  // Side jobs
  renderJobs();
}

// ── Market ────────────────────────────────────────────────────────────────────
function renderMarket() {
  const el = document.getElementById('market-list');
  if (!el) return;
  if (state && state.level === 0) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">🔒</div>
      <div class="empty-text">Market Locked</div>
      <div class="empty-sub">Sell your starter Bungalow in Midtown to reach Level 1 and unlock buying.</div>
    </div>`;
    return;
  }
  if (marketListings.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">🏚️</div><div class="empty-text">No listings right now</div><div class="empty-sub">Advance the day to see new properties</div></div>';
    return;
  }

  // Group by neighborhood, preserving unlock order
  const HOOD_ORDER = ['Midtown', 'Northside', 'Westwood', 'Riverside', 'Newbay'];
  const HOOD_META = {
    Midtown:  { emoji: '🏚️', desc: 'Crumbling blocks, forgotten by time' },
    Northside:{ emoji: '🌲', desc: 'Gritty streets, high turnover' },
    Westwood: { emoji: '🏘️', desc: 'Solid middle-class area' },
    Riverside:{ emoji: '🌊', desc: 'Desirable riverside living' },
    Newbay:   { emoji: '🌆', desc: 'Premium downtown district' },
  };
  const grouped = {};
  for (const p of marketListings) {
    if (!grouped[p.neighborhood]) grouped[p.neighborhood] = [];
    grouped[p.neighborhood].push(p);
  }
  const hoodsPresent = HOOD_ORDER.filter(h => grouped[h]);
  const useDropdown  = hoodsPresent.length >= 3;

  const sections = hoodsPresent.map(hood => {
    const meta    = HOOD_META[hood] || { emoji: '🏙️', desc: '' };
    const tier    = grouped[hood][0]?.neighborhood_info?.tier || 'mid';
    const count   = grouped[hood].length;
    const isOpen  = useDropdown ? (marketHoodOpen[hood] !== false) : true;
    const cards   = grouped[hood].map(p => marketCardHtml(p)).join('');
    const chevron = useDropdown
      ? `<span class="market-hood-chevron">${isOpen ? '▼' : '▶'}</span>` : '';
    return `
      <div class="market-hood-section">
        <div class="market-hood-header badge-${tier}${useDropdown ? ' market-hood-toggle' : ''}"
             ${useDropdown ? `onclick="toggleMarketHood('${hood}')"` : ''}>
          <span class="market-hood-emoji">${meta.emoji}</span>
          <div>
            <div class="market-hood-name">${hood}</div>
            <div class="market-hood-desc">${meta.desc}</div>
          </div>
          <span class="market-hood-count">${count} listing${count !== 1 ? 's' : ''}</span>
          ${chevron}
        </div>
        ${isOpen ? `<div class="market-hood-body">${cards}</div>` : ''}
      </div>`;
  }).join('');
  el.innerHTML = sections;
}

function toggleMarketHood(hood) {
  // undefined = open by default; toggling for the first time closes it
  marketHoodOpen[hood] = marketHoodOpen[hood] === false ? true : false;
  renderMarket();
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
        <div class="card-title">${p.address || p.type}</div>
        <div class="card-subtitle">${p.bedrooms}bd / ${p.bathrooms}ba ${p.type} · ${p.sqft.toLocaleString()} sqft</div>
      </div>
    </div>
    <div class="condition-wrap">
      <div class="condition-top">
        <span class="condition-lbl">Condition</span>
        <span class="condition-val" style="color:${tierColor(condTier(p.condition))};font-weight:900">${condTier(p.condition)} Tier</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${condPct(p.condition)}%"></div></div>
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
  if (state.level === 0) { toast('Reach Level 1 first — sell your starter property!', 'error'); return; }
  const listing = marketListings.find(p => p.id === id);
  if (!listing) return;
  if (listing.purchase_price > state.cash) { toast('Not enough cash!', 'error'); return; }
  showConfirmModal(
    `Buy ${listing.bedrooms}bd ${listing.type}?`,
    `${listing.neighborhood} · ${fmt(listing.purchase_price)}`,
    async () => {
      const res = await api('/buy', 'POST', { listing_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      closeModal();
      toast(`Purchased ${listing.type} in ${listing.neighborhood}!`, 'success');
      // Remove the bought listing locally — market only refills on day advance
      marketListings = marketListings.filter(p => p.id !== id);
      await refreshState();
      renderAll();
    }
  );
}

async function refreshMarketListings() {
  const data = await api('/market/refresh', 'POST');
  marketListings = data.listings || [];
  marketHoodOpen = {};   // reset — all sections open after a day advance
  renderMarket();
}

// ── Properties ────────────────────────────────────────────────────────────────
function renderProperties() {
  const el = document.getElementById('property-list');
  if (!el) return;
  const homeCard = playerHomeCardHtml();
  if (!state.properties || state.properties.length === 0) {
    el.innerHTML = homeCard + `<div class="empty-state">
      <div class="empty-icon">🏗️</div>
      <div class="empty-text">No rental properties yet</div>
      <div class="empty-sub">Head to the Market tab to buy your first property</div>
    </div>`;
    return;
  }
  el.innerHTML = homeCard + state.properties.map(p => portfolioCardHtml(p)).join('');
}

function playerHomeCardHtml() {
  const homeKey = state.player_home || 'moms_basement';
  const maxE    = state.max_energy || 10;
  const recharge = state.energy_recharge || 2;
  const home    = PLAYER_HOME_DATA.find(h => h.key === homeKey) || PLAYER_HOME_DATA[0];
  const isMax   = homeKey === 'mansion';
  return `
  <div class="section-header" style="margin-bottom:8px">
    <span class="section-title">🏠 My Home</span>
  </div>
  <div class="card" onclick="showPlayerHomeModal()" style="cursor:pointer;margin-bottom:16px;border:2px solid var(--primary)">
    <div class="card-header">
      <div class="card-icon">${home.icon}</div>
      <div style="flex:1">
        <div class="card-title">${home.name}</div>
        <div class="card-subtitle">${isMax ? '🏆 Max upgrade reached!' : 'Tap to upgrade your home'}</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:13px;font-weight:700;color:var(--positive)">⚡ ${maxE} max</div>
        <div style="font-size:11px;color:var(--text-muted)">+${recharge}/day</div>
      </div>
    </div>
  </div>
  <div class="section-header" style="margin-bottom:8px">
    <span class="section-title">My Portfolio</span>
  </div>`;
}

function showPlayerHomeModal() {
  const homeKey       = state.player_home || 'moms_basement';
  const currentIdx    = PLAYER_HOME_DATA.findIndex(h => h.key === homeKey);
  const current       = PLAYER_HOME_DATA[currentIdx] || PLAYER_HOME_DATA[0];
  const unlockedKeys  = state.unlocked_homes || ['moms_basement'];
  // Show all upgrades above current; mark locked ones
  const allUpgrades   = PLAYER_HOME_DATA.slice(currentIdx + 1);
  const upgrades      = allUpgrades;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🏠 Your Home</div>
    <div class="card" style="margin-bottom:16px;background:var(--surface-2)">
      <div style="display:flex;align-items:center;gap:12px">
        <div style="font-size:36px;line-height:1">${current.icon}</div>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:800">${current.name}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${current.desc}</div>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:12px">
        <div style="flex:1;text-align:center;padding:8px;background:var(--surface);border-radius:8px">
          <div style="font-size:20px;font-weight:900;color:var(--positive)">⚡ ${current.max_energy}</div>
          <div style="font-size:11px;color:var(--text-muted)">Max Energy</div>
        </div>
        <div style="flex:1;text-align:center;padding:8px;background:var(--surface);border-radius:8px">
          <div style="font-size:20px;font-weight:900;color:var(--primary)">+${current.recharge}</div>
          <div style="font-size:11px;color:var(--text-muted)">Energy/Day</div>
        </div>
      </div>
    </div>
    ${upgrades.length === 0
      ? `<div style="text-align:center;padding:20px;color:var(--text-muted)">🏆 You live in the best home possible!</div>`
      : `<div style="font-size:12px;font-weight:700;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:8px">UPGRADE OPTIONS</div>
         ${upgrades.map(h => {
           const isLocked  = !unlockedKeys.includes(h.key);
           const canAfford = !isLocked && state.cash >= h.cost;
           const reqLevel  = PLAYER_HOME_DATA.indexOf(h); // 1-indexed unlock level
           return `
           <div class="card" style="margin-bottom:10px;opacity:${isLocked ? '0.45' : (!canAfford ? '0.6' : '1')}">
             <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
               <div style="font-size:28px;line-height:1">${isLocked ? '🔒' : h.icon}</div>
               <div style="flex:1">
                 <div style="font-size:15px;font-weight:800">${h.name}</div>
                 <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${isLocked ? `Unlocks at Level ${reqLevel}` : h.desc}</div>
               </div>
               <div style="text-align:right;flex-shrink:0">
                 <div style="font-size:14px;font-weight:800;color:var(--primary)">${isLocked ? '🔒' : fmt(h.cost)}</div>
               </div>
             </div>
             <div style="display:flex;gap:8px;margin-bottom:10px">
               <div style="flex:1;text-align:center;padding:6px;background:var(--surface-2);border-radius:6px">
                 <div style="font-size:15px;font-weight:800;color:var(--positive)">⚡ ${h.max_energy}</div>
                 <div style="font-size:10px;color:var(--text-muted)">Max Energy</div>
               </div>
               <div style="flex:1;text-align:center;padding:6px;background:var(--surface-2);border-radius:6px">
                 <div style="font-size:15px;font-weight:800;color:var(--primary)">+${h.recharge}/day</div>
                 <div style="font-size:10px;color:var(--text-muted)">Daily Recharge</div>
               </div>
             </div>
             <button class="btn btn-full ${canAfford ? 'btn-primary' : 'btn-ghost'}"
               ${canAfford ? `onclick="moveIn('${h.key}')"` : 'disabled'}
               style="${!canAfford ? 'cursor:not-allowed' : ''}">
               ${isLocked ? `🔒 Locked — reach Level ${reqLevel}` : canAfford ? `Move In · ${fmt(h.cost)}` : `Need ${fmt(h.cost)} · Have ${fmt(state.cash)}`}
             </button>
           </div>`;
         }).join('')}`
    }
    <button class="btn btn-ghost btn-full mt-8" onclick="closeModal()">Close</button>`);
}

async function moveIn(homeKey) {
  const res = await api('/move_in', 'POST', { home_key: homeKey });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal();
  await refreshState();
  renderAll();
  const home = PLAYER_HOME_DATA.find(h => h.key === homeKey);
  toast(`🏠 Moved into ${home ? home.name : 'new home'}! Energy max & recharge increased.`);
}

function portfolioCardHtml(p) {
  const activePending   = p.pending_reno || p.pending_premium;
  const pendingDaysLeft = activePending ? Math.max(0, activePending.complete_day - state.day) : 0;
  const scheduledWork   = p.scheduled_reno || p.scheduled_premium;
  const scheduledDaysOut = scheduledWork ? Math.max(0, scheduledWork.start_day - state.day) : 0;
  const tenantBadge = p.squatter
    ? `<span class="vacant-chip" style="background:#FFEBEE;color:#C62828;border-color:#EF9A9A">🚨 Squatter</span>`
    : activePending
    ? `<span class="vacant-chip" style="background:#E3F2FD;color:#1565C0;border-color:#90CAF9">🔨 ${activePending.name} · ${pendingDaysLeft}d left</span>`
    : p.tenant && scheduledWork
    ? `<span class="vacant-chip" style="background:#F3E5F5;color:#6A1B9A;border-color:#CE93D8">🗓️ ${scheduledWork.name} · starts in ${scheduledDaysOut}d</span>`
    : p.tenant && p.tenant.is_mystery
    ? `<span class="tenant-chip" style="background:#2d004f;color:#CE93D8;border-color:#7B1FA2;font-weight:800">👤 ??? · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_phil
    ? `<span class="tenant-chip" style="background:#fffde7;color:#b8860b;border-color:gold;font-weight:800">🔱 The Phil · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_baileys
    ? `<span class="tenant-chip" style="background:#FFF3E0;color:#E65100;border-color:#E65100;font-weight:800">👨‍👩‍👧‍👦 The Baileys · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_goldbergs
    ? `<span class="tenant-chip" style="background:#E8F5E9;color:#1B5E20;border-color:#2E7D32;font-weight:800">🎩 The Goldbergs · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && (p.tenant.morale ?? 50) < 20
    ? `<span class="vacant-chip" style="background:#FFEBEE;color:#C62828;border-color:#EF9A9A">😠 ${p.tenant.name} · morale ${p.tenant.morale ?? '?'}%</span>`
    : p.tenant
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
        <div class="card-title">${p.address || p.type}</div>
        <div class="card-subtitle">${p.bedrooms}bd / ${p.bathrooms}ba ${p.type} · ${p.neighborhood}</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:16px;font-weight:800">${fmt(p.market_value)}</div>
        <div style="font-size:11px;color:var(--text-muted)">market value</div>
      </div>
    </div>
    <div class="condition-wrap mb-0">
      <div class="condition-top">
        <span class="condition-lbl">Condition · <span style="color:${tierColor(condTier(p.condition))};font-weight:900">${condTier(p.condition)}</span></span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${condPct(p.condition)}%"></div></div>
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

  const [upgData, premData] = await Promise.all([
    api(`/property/${id}/upgrades`),
    api(`/property/${id}/premium_upgrades`),
  ]);
  const profit   = prop.market_value - prop.purchase_price;
  const profitStr = profit >= 0
    ? `<span style="color:var(--positive)">+${fmt(profit)}</span>`
    : `<span style="color:var(--negative)">${fmt(profit)}</span>`;

  const renoInProgress = prop.pending_reno
    ? `<div class="card" style="margin-bottom:10px;border:2px solid #1565C0">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:30px">🔨</span>
          <div style="flex:1">
            <div style="font-size:15px;font-weight:800;color:#1565C0">Renovation In Progress</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:2px">${prop.pending_reno.icon} ${prop.pending_reno.name}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:22px;font-weight:900;color:#1565C0">${Math.max(0, prop.pending_reno.complete_day - state.day)}</div>
            <div style="font-size:11px;color:var(--text-muted)">days left</div>
          </div>
        </div>
        <p style="font-size:12px;color:var(--text-muted);margin-top:10px">The result will be revealed when the work is done. Advance time to complete it.</p>
      </div>`
    : '';

  const tenantSection = prop.squatter
    ? `<div class="card" style="margin-bottom:10px;border:2px solid #EF9A9A">
        <div class="section-header mb-0"><span class="section-title" style="color:#C62828">🚨 Squatters Present</span></div>
        <p style="margin-top:8px;font-size:13px;color:var(--text-muted)">Someone has moved in without permission and isn't paying rent. You can't rent out or renovate until they're gone.</p>
        <div class="money-row" style="margin-top:10px"><span class="mr-label">Their Asking Price to Leave</span><span class="mr-value" style="color:#C62828">${fmt(prop.squatter.bribe)}</span></div>
        <div class="btn-row" style="margin-top:10px">
          <button class="btn btn-danger btn-sm" onclick="briberSquatter(${id})">💸 Pay ${fmt(prop.squatter.bribe)} to Remove</button>
        </div>
        <p style="font-size:11px;color:var(--text-muted);margin-top:8px">Or wait — they may leave on their own eventually.</p>
      </div>`
    : prop.tenant
    ? (() => {
        const morale      = prop.tenant.morale ?? 50;
        const moraleColor = morale >= 60 ? 'var(--positive)' : morale >= 40 ? 'var(--primary)' : morale >= 20 ? 'var(--warning)' : 'var(--negative)';
        const moraleLabel = morale >= 60 ? '😊 Happy' : morale >= 40 ? '😐 Content' : morale >= 20 ? '😟 Uneasy' : '😠 Unhappy — at risk of leaving!';
        const moraleWarn  = morale < 20 ? `<div style="font-size:12px;color:var(--negative);font-weight:700;margin-top:6px">⚠️ Morale critical — fix repairs before they break lease early!</div>` : '';
        const isPhil      = !!prop.tenant.is_phil;
        const isBaileys   = !!prop.tenant.is_baileys;
        const isGoldbergs = !!prop.tenant.is_goldbergs;
        const isMystery   = !!prop.tenant.is_mystery;
        const isSpecial   = isPhil || isBaileys || isGoldbergs || isMystery;
        const cardBorder  = isMystery   ? ';border:2px solid #7B1FA2'
                          : isPhil      ? ';border:2px solid gold'
                          : isBaileys   ? ';border:2px solid #E65100'
                          : isGoldbergs ? ';border:2px solid #2E7D32'
                          : morale < 20 ? ';border:2px solid var(--negative)' : '';
        const cardBg      = isMystery   ? ';background:linear-gradient(135deg,#1a0030,#2d004f)'
                          : isPhil      ? ';background:linear-gradient(135deg,#fffde7,#fff8e1)'
                          : isBaileys   ? ';background:linear-gradient(135deg,#FFF3E0,#FFF8F0)'
                          : isGoldbergs ? ';background:linear-gradient(135deg,#E8F5E9,#F1F8F1)' : '';
        const badgeHtml   = isMystery   ? '<span style="font-size:11px;background:#7B1FA2;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">👤 MYSTERY</span>'
                          : isPhil      ? '<span style="font-size:11px;background:gold;color:#5d4037;padding:2px 8px;border-radius:8px;font-weight:700">🔱 THE PHIL</span>'
                          : isBaileys   ? '<span style="font-size:11px;background:#E65100;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">👨‍👩‍👧‍👦 THE BAILEYS</span>'
                          : isGoldbergs ? '<span style="font-size:11px;background:#2E7D32;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">🎩 THE GOLDBERGS</span>' : '';
        const nameColor   = isMystery ? '#CE93D8' : isPhil ? '#b8860b' : isBaileys ? '#E65100' : isGoldbergs ? '#1B5E20' : '';
        const subLine     = isPhil      ? '<span style="font-size:11px;color:#b8860b;font-weight:700">+1 condition/day · 25% weekly reno</span>'
                          : isBaileys   ? '<span style="font-size:11px;color:#E65100;font-weight:700">Morale locked at 100% · Never damages</span>'
                          : isGoldbergs ? '<span style="font-size:11px;color:#2E7D32;font-weight:700">10× rent · Short stay</span>'
                          : isMystery   ? '<span style="font-size:11px;color:#CE93D8;font-weight:700">???</span>'
                          : rentTierBadge(prop.tenant.rent_tier);
        const iconStyle   = isMystery ? 'font-size:28px;filter:brightness(0.1)' : 'font-size:28px';
        const moraleHtml  = isMystery
          ? `<div style="margin-bottom:10px">
               <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                 <span style="font-size:12px;font-weight:700;color:#9C27B0">MORALE</span>
                 <span style="font-size:13px;font-weight:800;color:#CE93D8">??? · ???%</span>
               </div>
               <div style="height:8px;background:#3a005a;border-radius:4px;overflow:hidden">
                 <div style="height:100%;width:100%;background:linear-gradient(90deg,#7B1FA2,#CE93D8);border-radius:4px"></div>
               </div>
             </div>`
          : `<div style="margin-bottom:10px">
               <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                 <span style="font-size:12px;font-weight:700;color:var(--text-muted)">MORALE</span>
                 <span style="font-size:13px;font-weight:800;color:${moraleColor}">${moraleLabel} · ${morale}%</span>
               </div>
               <div style="height:8px;background:var(--border);border-radius:4px;overflow:hidden">
                 <div style="height:100%;width:${morale}%;background:${moraleColor};border-radius:4px;transition:width 0.3s"></div>
               </div>
               ${moraleWarn}
             </div>`;
        return `<div class="card" style="margin-bottom:10px${cardBorder}${cardBg}">
        <div class="section-header mb-0"><span class="section-title" style="${isMystery ? 'color:#CE93D8' : ''}">Current Tenant</span>${badgeHtml}</div>
        <div style="margin-top:10px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span style="${iconStyle}">${isMystery ? '👤' : prop.tenant.icon || '👤'}</span>
            <div style="flex:1">
              <div style="font-size:15px;font-weight:700;${nameColor ? 'color:' + nameColor : ''}">${isMystery ? '???' : prop.tenant.name}</div>
              <div style="font-size:12px;color:${isMystery ? '#9C27B0' : 'var(--text-2)'}">${prop.tenant_days_remaining ?? '?'} days left on lease</div>
              <div style="margin-top:2px">${subLine}</div>
            </div>
            <span style="font-size:18px;font-weight:800;color:${isGoldbergs ? '#2E7D32' : 'var(--positive)'}">
              ${fmt(prop.tenant.rent)}/wk${isGoldbergs ? '<div style="font-size:10px;color:#2E7D32;text-align:right">10× rent</div>' : ''}
            </span>
          </div>
          ${moraleHtml}
          <div class="money-row"><span class="mr-label">Total Rent Collected</span><span class="mr-value green">${fmt(prop.total_rent_collected)}</span></div>
          <div class="money-row"><span class="mr-label">Total Repair Costs</span><span class="mr-value red">${fmt(prop.total_repair_costs)}</span></div>
          <div class="btn-row">
            <button class="btn btn-danger btn-sm" onclick="evictTenant(${id})">⚖️ Evict ($1,500)</button>
          </div>
        </div>
      </div>`;
      })()
    : `<div class="card" style="margin-bottom:10px">
        <div class="section-header mb-0"><span class="section-title">Tenant</span></div>
        ${prop.pending_reno
          ? '<p style="margin-top:8px;font-size:13px;color:var(--text-muted)">Renovation in progress — find a tenant once work is complete.</p>'
          : '<p style="margin-top:8px;font-size:13px;color:var(--text-muted)">This property is vacant.</p>'}
        <div class="btn-row">
          ${!prop.pending_reno ? `<button class="btn btn-primary btn-sm" onclick="showTenantsModal(${id})">🔑 Find Tenant</button>` : ''}
          <button class="btn btn-accent btn-sm" onclick="sellProperty(${id})">💰 Sell Property</button>
        </div>
      </div>`;

  const cooldownHtml = (upgData.on_cooldown || []).length > 0
    ? `<div style="margin-bottom:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:var(--text-muted)">ON COOLDOWN</div>
       <div class="upgrade-grid">${upgData.on_cooldown.map(u =>
        `<div class="upgrade-card done" style="opacity:0.7">
          <div class="upgrade-icon">${u.icon}</div>
          <div class="upgrade-name">${u.name}</div>
          <div class="upgrade-quality" style="color:${tierColor(u.quality_tier)};font-weight:800">${u.quality_tier}</div>
          <div class="upgrade-quality">⏳ ${u.days_remaining}d left</div>
        </div>`).join('')}</div></div>`
    : '';

  // Scheduled reno info banner
  const scheduledRenoHtml = prop.scheduled_reno
    ? `<div class="card" style="margin-bottom:10px;border:2px solid #7B1FA2;background:#F3E5F5">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:28px">🗓️</span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#6A1B9A">Renovation Scheduled</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${prop.scheduled_reno.icon} ${prop.scheduled_reno.name}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:20px;font-weight:900;color:#6A1B9A">${Math.max(0, prop.scheduled_reno.start_day - state.day)}</div>
            <div style="font-size:10px;color:var(--text-muted)">days until start</div>
          </div>
        </div>
        <p style="font-size:11px;color:var(--text-muted);margin-top:8px">Contractors will arrive on Day ${prop.scheduled_reno.start_day}. Advance time to get there.</p>
      </div>`
    : '';

  // Each available reno card: vacant → normal click; tenant + no scheduled → schedule click; blocked → dimmed
  const availHtml = upgData.available.length > 0
    ? `<div class="upgrade-grid">${upgData.available.map(u => {
        const fullyBlocked  = prop.squatter || prop.pending_reno;
        const canSchedule   = prop.tenant && !fullyBlocked && !prop.scheduled_reno;
        const canRenovate   = !prop.tenant && !fullyBlocked;
        const clickable     = canRenovate || canSchedule;
        const onclick       = canRenovate  ? `onclick="showContractorModal(${id},'${u.key}')"` :
                              canSchedule  ? `onclick="showScheduleRenoModal(${id},'${u.key}')"` : '';
        return `<div class="upgrade-card ${!clickable ? 'btn-disabled' : ''}" ${onclick}>
          <div class="upgrade-icon">${u.icon}</div>
          <div class="upgrade-name">${u.name}</div>
          ${u.prev_quality_tier
            ? `<div class="upgrade-quality" style="font-size:10px;color:var(--text-muted)">Last: ${u.prev_quality_tier} · Redo</div>`
            : `<div class="upgrade-cost">from ${fmt(u.costs.budget)}</div>`}
          ${canSchedule ? `<div class="upgrade-quality" style="font-size:10px;color:#7B1FA2">📅 Schedule</div>` : ''}
        </div>`;
      }).join('')}</div>`
    : '<p class="text-muted" style="margin-top:4px">All upgrades on cooldown!</p>';

  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <span style="font-size:36px">${prop.icon}</span>
      <div>
        <div style="font-size:18px;font-weight:800;margin-bottom:2px">${prop.address || prop.type}</div>
        <div style="font-size:13px;color:var(--text-2)">${prop.bedrooms}bd / ${prop.bathrooms}ba ${prop.type} · ${prop.neighborhood}</div>
      </div>
    </div>
    <div class="condition-wrap">
      <div class="condition-top">
        <span class="condition-lbl">Condition</span>
        <span class="condition-val" style="color:${tierColor(condTier(prop.condition))};font-weight:900">${condTier(prop.condition)} Tier</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(prop.condition)}" style="width:${condPct(prop.condition)}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Market Value</span><span class="mr-value">${fmt(prop.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">Purchase Price</span><span class="mr-value">${fmt(prop.purchase_price)}</span></div>
    <div class="money-row"><span class="mr-label">Unrealized Gain/Loss</span><div>${profitStr}</div></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Fair Weekly Rent</span><span class="mr-value green">${fmt(prop.weekly_rent)}/wk</span></div>
    ${renoInProgress}
    ${tenantSection}
    <div class="section-header"><span class="section-title">Renovations</span></div>
    ${prop.pending_reno
      ? '<p class="text-muted" style="margin-bottom:8px">Renovation already in progress.</p>'
      : prop.squatter
      ? '<p class="text-muted" style="margin-bottom:8px">Remove squatters before renovating.</p>'
      : prop.tenant && prop.scheduled_reno
      ? '<p class="text-muted" style="margin-bottom:8px">Work is scheduled — one renovation at a time.</p>'
      : prop.tenant
      ? '<p class="text-muted" style="margin-bottom:8px">Tenant in residence — tap an upgrade to schedule a maintenance window. Contractor only.</p>'
      : ''}
    ${scheduledRenoHtml}
    ${cooldownHtml}
    ${upgData.pending_reno ? `<div style="margin-top:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:#1565C0">IN PROGRESS</div>
      <div class="upgrade-grid"><div class="upgrade-card" style="border-color:#1565C0;background:#E3F2FD">
        <div class="upgrade-icon">${upgData.pending_reno.icon}</div>
        <div class="upgrade-name">${upgData.pending_reno.name}</div>
        <div class="upgrade-quality" style="color:#1565C0">🔨 ${Math.max(0, upgData.pending_reno.complete_day - state.day)}d left</div>
      </div></div></div>` : ''}
    ${!prop.pending_reno && upgData.available.length > 0 ? `<div style="margin-top:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:var(--text-muted)">${prop.tenant && !prop.scheduled_reno ? 'TAP TO SCHEDULE' : 'AVAILABLE'}</div>${availHtml}</div>` : ''}
    ${buildPremiumSection(id, premData, state.cash, !!prop.squatter, !!prop.tenant)}
    <div class="btn-row" style="margin-top:16px">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">← Back</button>
    </div>`);
}

// ── Premium Upgrades ─────────────────────────────────────────────────────────
function buildPremiumSection(pid, premData, cash, hasSquatter = false, hasTenant = false) {
  const blocked = hasSquatter || !!(premData.pending_premium);

  if (hasSquatter) {
    return `
    <div class="section-header" style="margin-top:16px">
      <span class="section-title">⭐ Premium Upgrades</span>
    </div>
    <p class="text-muted" style="margin-bottom:8px">Remove squatters before installing premium upgrades.</p>`;
  }

  // Find scheduled premium on the prop (passed via premData)
  const scheduledPrem = premData.scheduled_premium || null;

  const catalog   = premData.catalog || [];
  const installed = catalog.filter(u => u.installed);
  const available = catalog.filter(u => !u.installed);

  const installedHtml = installed.length > 0
    ? installed.map(u => `
      <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:22px">${u.icon}</span>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:700">${u.name}</div>
          <div style="font-size:11px;color:var(--text-muted)">${u.desc}</div>
        </div>
        <span style="font-size:11px;font-weight:700;color:var(--positive);white-space:nowrap">✓ Installed</span>
      </div>`).join('')
    : '';

  const pendingHtml = premData.pending_premium
    ? `<div class="card" style="margin-bottom:8px;border:2px solid #1565C0;background:#E3F2FD">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:26px">${premData.pending_premium.icon}</span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#1565C0">🔨 ${premData.pending_premium.name}</div>
            <div style="font-size:12px;color:var(--text-muted)">Installation in progress</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:20px;font-weight:900;color:#1565C0">${Math.max(0, premData.pending_premium.complete_day - state.day)}d</div>
            <div style="font-size:10px;color:var(--text-muted)">left</div>
          </div>
        </div>
      </div>`
    : '';

  // Scheduled premium banner
  const scheduledPremHtml = scheduledPrem
    ? `<div class="card" style="margin-bottom:8px;border:2px solid #7B1FA2;background:#F3E5F5">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:26px">🗓️</span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#6A1B9A">Upgrade Scheduled</div>
            <div style="font-size:12px;color:var(--text-muted);">${scheduledPrem.icon} ${scheduledPrem.name} · Day ${scheduledPrem.start_day}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:20px;font-weight:900;color:#6A1B9A">${Math.max(0, scheduledPrem.start_day - state.day)}</div>
            <div style="font-size:10px;color:var(--text-muted)">days until start</div>
          </div>
        </div>
      </div>`
    : '';

  const availableHtml = available.map(u => {
    const canSchedule = hasTenant && !blocked && !scheduledPrem && cash >= u.cost;
    const canInstall  = !hasTenant && !blocked && cash >= u.cost;
    const canAfford   = canSchedule || canInstall;
    const fullyBlocked = blocked || (hasTenant && !!scheduledPrem) || (!hasTenant && !canAfford) || (hasTenant && cash < u.cost);
    let btnLabel, btnOnclick;
    if (blocked)             { btnLabel = 'Upgrade in progress'; btnOnclick = 'disabled'; }
    else if (hasTenant && scheduledPrem) { btnLabel = 'Upgrade already scheduled'; btnOnclick = 'disabled'; }
    else if (!canAfford)     { btnLabel = `Need ${fmt(u.cost)} (have ${fmt(cash)})`; btnOnclick = 'disabled'; }
    else if (canSchedule)    { btnLabel = `📅 Schedule · ${fmt(u.cost)}`; btnOnclick = `onclick="showSchedulePremiumModal(${pid},'${u.key}',${u.cost},${u.days},'${u.name}','${u.icon}')"` ; }
    else                     { btnLabel = `🔨 Hire Contractor · ${fmt(u.cost)}`; btnOnclick = `onclick="installPremiumUpgrade(${pid},'${u.key}')"` ; }

    return `
    <div class="card" style="margin-bottom:8px${fullyBlocked ? ';opacity:0.55' : ''}">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <span style="font-size:28px;line-height:1.2">${u.icon}</span>
        <div style="flex:1">
          <div style="font-size:14px;font-weight:800">${u.name}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${u.desc}</div>
          <div style="display:flex;gap:12px;margin-top:6px;font-size:12px">
            <span style="color:var(--positive);font-weight:700">+${fmt(u.rent_bonus)}/wk rent</span>
            <span style="color:var(--accent);font-weight:700">+${fmt(u.value_bonus)} value</span>
            <span style="color:var(--text-muted)">⏱ ${u.days}d</span>
          </div>
        </div>
      </div>
      <button class="btn btn-sm btn-full ${canAfford ? 'btn-primary' : 'btn-ghost'}"
        style="margin-top:10px${btnOnclick === 'disabled' ? ';cursor:not-allowed' : ''}"
        ${btnOnclick === 'disabled' ? 'disabled' : btnOnclick}>
        ${btnLabel}
      </button>
    </div>`;
  }).join('');

  const tenantNote = hasTenant && !premData.pending_premium && !scheduledPrem
    ? `<p class="text-muted" style="margin-bottom:8px;font-size:12px">Tenant in residence — schedule a maintenance window below.</p>`
    : '';

  return `
  <div class="section-header" style="margin-top:16px">
    <span class="section-title">⭐ Premium Upgrades</span>
  </div>
  ${tenantNote}
  ${installedHtml ? `<div class="card" style="margin-bottom:10px;padding:4px 12px">${installedHtml}</div>` : ''}
  ${pendingHtml}
  ${scheduledPremHtml}
  ${!premData.pending_premium && (availableHtml || '<p class="text-muted" style="margin-bottom:8px">All premium upgrades installed!</p>')}`;
}

async function installPremiumUpgrade(pid, key) {
  const res = await api(`/property/${pid}/premium_upgrades`, 'POST', { upgrade_key: key });
  if (res.error) { toast(res.error, 'error'); return; }
  const d = res.duration;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🔨 Work Underway!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div style="font-size:48px">🏗️</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px">${d} Day${d !== 1 ? 's' : ''}</div>
      <div style="font-size:13px;color:var(--text-muted)">until installation complete</div>
    </div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got It</button>`);
  await refreshState();
  renderAll();
}

// ── Schedule Renovations (with tenant) ───────────────────────────────────────
async function showScheduleRenoModal(propId, upgradeKey) {
  const upgData = await api(`/property/${propId}/upgrades`);
  const upg     = upgData.available.find(u => u.key === upgradeKey);
  if (!upg) { toast('Upgrade not found', 'error'); return; }

  // Stable tenant window — same day until the player advances
  const availDay = getTenantAvailDay(propId);
  const daysOut  = availDay - state.day;
  const sInfo    = getSeasonInfo(availDay);

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${upg.icon} ${upg.name}</div>
    <div class="modal-subtitle">Schedule with tenant in residence</div>

    <div class="card" style="margin-bottom:16px;background:#F3E5F5;border:2px solid #CE93D8">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:30px">📅</span>
        <div>
          <div style="font-size:14px;font-weight:800;color:#6A1B9A">Tenant Maintenance Window</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:3px">
            Your tenant is available starting <strong>Day ${availDay}</strong>
            &nbsp;(${sInfo.icon} ${sInfo.name} · in ${daysOut} day${daysOut !== 1 ? 's' : ''})
          </div>
        </div>
      </div>
    </div>

    <div style="text-align:center;font-size:11px;color:var(--text-muted);margin-bottom:10px">── choose a contractor ──</div>

    ${upg.special_contractor ? (() => {
      const sc        = upg.special_contractor;
      const days      = contractorDays('premium', upg.energy_cost || 1);
      const canAfford = state.cash >= sc.cost;
      return `<div class="contractor-card contractor-special" style="${!canAfford ? 'opacity:0.6' : ''}">
        <div class="contractor-special-badge">⚡ SPECIAL — Guaranteed S+</div>
        <div class="contractor-header">
          <span class="contractor-icon">${sc.icon}</span>
          <span class="contractor-name">${sc.name}</span>
          <span class="contractor-cost" style="color:${canAfford ? 'inherit' : 'var(--negative)'}">
            ${canAfford ? fmt(sc.cost) : `Need ${fmt(sc.cost)}`}
          </span>
        </div>
        <div class="contractor-desc">${sc.desc}</div>
        <div class="contractor-quality">Grade: <strong style="color:#7B1FA2">S+</strong> guaranteed · total wait ~${daysOut + days}d</div>
        <button class="btn btn-sm btn-full ${canAfford ? 'btn-primary' : 'btn-ghost'} mt-8"
          style="${!canAfford ? 'cursor:not-allowed' : ''};margin-top:8px"
          ${canAfford ? `onclick="confirmScheduleReno(${propId},'${upgradeKey}','special',${availDay})"` : 'disabled'}>
          ${canAfford ? `📅 Book · ${fmt(sc.cost)}` : `Not enough cash`}
        </button>
      </div>`;
    })() : ''}

    ${Object.entries(upgData.contractors).map(([key, c]) => {
      const cost     = upg.costs[key];
      const days     = contractorDays(key, upg.energy_cost || 1);
      const canAfford = state.cash >= cost;
      return `
      <div class="contractor-card${!canAfford ? '' : ''}" style="${!canAfford ? 'opacity:0.5' : ''}">
        <div class="contractor-header">
          <span class="contractor-icon">${c.icon}</span>
          <span class="contractor-name">${c.name}</span>
          <span class="contractor-cost" style="color:${canAfford ? 'inherit' : 'var(--negative)'}">
            ${canAfford ? fmt(cost) : `Need ${fmt(cost)}`}
          </span>
        </div>
        <div class="contractor-desc">${c.desc}</div>
        <div class="contractor-quality">Finishes ~${days}d after start · total wait ~${daysOut + days}d</div>
        <button class="btn btn-sm btn-full ${canAfford ? 'btn-primary' : 'btn-ghost'} mt-8"
          style="${!canAfford ? 'cursor:not-allowed' : ''};margin-top:8px"
          ${canAfford ? `onclick="confirmScheduleReno(${propId},'${upgradeKey}','${key}',${availDay})"` : 'disabled'}>
          ${canAfford ? `📅 Book · ${fmt(cost)}` : `Not enough cash`}
        </button>
      </div>`;
    }).join('')}

    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

async function confirmScheduleReno(propId, upgradeKey, contractorKey, startDay) {
  const res = await api(`/property/${propId}/schedule_reno`, 'POST', {
    upgrade_key: upgradeKey, contractor_key: contractorKey, start_day: startDay,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  const daysOut = startDay - state.day;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">📅 Renovation Scheduled!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div style="font-size:48px">🗓️</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px;color:#6A1B9A">Day ${startDay}</div>
      <div style="font-size:13px;color:var(--text-muted)">contractors arrive · in ${daysOut} day${daysOut !== 1 ? 's' : ''}</div>
    </div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got It</button>`);
  await refreshState();
  renderAll();
}

function showSchedulePremiumModal(propId, upgradeKey, cost, days, name, icon) {
  // Stable tenant window — same day until the player advances
  const availDay = getTenantAvailDay(propId);
  const daysOut  = availDay - state.day;
  const sInfo    = getSeasonInfo(availDay);
  const canAfford = state.cash >= cost;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${icon} ${name}</div>
    <div class="modal-subtitle">Schedule with tenant in residence</div>

    <div class="card" style="margin-bottom:16px;background:#F3E5F5;border:2px solid #CE93D8">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:30px">📅</span>
        <div>
          <div style="font-size:14px;font-weight:800;color:#6A1B9A">Tenant Maintenance Window</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:3px">
            Your tenant is available starting <strong>Day ${availDay}</strong>
            &nbsp;(${sInfo.icon} ${sInfo.name} · in ${daysOut} day${daysOut !== 1 ? 's' : ''})
          </div>
        </div>
      </div>
    </div>

    <div class="card" style="margin-bottom:12px">
      <div class="money-row"><span class="mr-label">Cost</span><span class="mr-value">${fmt(cost)}</span></div>
      <div class="money-row"><span class="mr-label">Work Duration</span><span class="mr-value">${days} day${days !== 1 ? 's' : ''} after start</span></div>
      <div class="money-row"><span class="mr-label">Total Wait</span><span class="mr-value">~${daysOut + days} days</span></div>
    </div>

    <button class="btn btn-primary btn-full"
      ${canAfford ? `onclick="confirmSchedulePremium(${propId},'${upgradeKey}',${availDay})"` : 'disabled'}
      style="${!canAfford ? 'opacity:0.5;cursor:not-allowed' : ''}">
      ${canAfford ? `📅 Schedule · ${fmt(cost)}` : `Need ${fmt(cost)} — have ${fmt(state.cash)}`}
    </button>
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

async function confirmSchedulePremium(propId, upgradeKey, startDay) {
  const res = await api(`/property/${propId}/schedule_premium`, 'POST', {
    upgrade_key: upgradeKey, start_day: startDay,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  const daysOut = startDay - state.day;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">📅 Upgrade Scheduled!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div style="font-size:48px">🗓️</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px;color:#6A1B9A">Day ${startDay}</div>
      <div style="font-size:13px;color:var(--text-muted)">workers arrive · in ${daysOut} day${daysOut !== 1 ? 's' : ''}</div>
    </div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got It</button>`);
  await refreshState();
  renderAll();
}

// ── Sell & Evict ──────────────────────────────────────────────────────────────
function sellProperty(id) {
  const prop = state.properties.find(p => p.id === id);
  if (!prop) return;
  showConfirmModal(
    `Sell ${prop.address || prop.type} in ${prop.neighborhood}?`,
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
  if (state.level === 0) {
    toast('Reach Level 1 first — sell your starter property!', 'error');
    return;
  }
  const prop = state.properties.find(p => p.id === id);
  openModal(`<div class="modal-handle"></div><div class="modal-title">Find a Tenant</div><p class="text-muted">Loading applicants…</p>`);

  const data  = await api(`/property/${id}/applicants`);
  _applicants = data.applicants;
  _fairRent   = data.fair_weekly_rent;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">Choose a Tenant</div>
    <div class="modal-subtitle">${prop.address || prop.type} · ${prop.neighborhood} · Fair rent: ${fmt(_fairRent)}/wk</div>
    ${_applicants.map(t => t.is_mystery ? `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})"
           style="border:2px solid #7B1FA2;background:linear-gradient(135deg,#1a0030,#2d004f);cursor:pointer">
        <div class="tenant-header">
          <span class="tenant-icon" style="font-size:28px;filter:brightness(0.1)">👤</span>
          <div style="flex:1">
            <div class="tenant-name" style="color:#CE93D8;font-weight:900">???
              <span style="font-size:10px;background:#7B1FA2;color:#fff;padding:2px 6px;border-radius:8px;margin-left:6px;font-weight:700">RARE</span>
            </div>
            <div style="font-size:11px;color:#9C27B0">??? · ???</div>
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label" style="color:#9C27B0">Reliability</span>
            <span class="tm-value" style="color:#CE93D8">???</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label" style="color:#9C27B0">Damage Risk</span>
            <span class="tm-value" style="color:#CE93D8">???</span>
          </div>
        </div>
      </div>` : t.is_phil ? `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})"
           style="border:2px solid gold;background:linear-gradient(135deg,#fffde7,#fff8e1)">
        <div class="tenant-header">
          <span class="tenant-icon">${t.icon}</span>
          <div style="flex:1">
            <div class="tenant-name" style="color:#b8860b;font-weight:900">${t.name}
              <span style="font-size:10px;background:gold;color:#5d4037;padding:2px 6px;border-radius:8px;margin-left:6px;font-weight:700">RARE</span>
            </div>
            <div style="font-size:11px;color:#8d6e63">${t.stay_min}–${t.stay_max} day lease · ${t.desc}</div>
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label">Reliability</span>
            <span class="tm-value" style="color:gold;font-weight:800">★★★★★ Always</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Damage Risk</span>
            <span class="tm-value" style="color:var(--positive)">${t.damage_label}</span>
          </div>
          <div class="tenant-meta-item" style="grid-column:1/-1">
            <span class="tm-label">Special</span>
            <span class="tm-value" style="color:#b8860b">+1 condition/day · 25% weekly renovation</span>
          </div>
        </div>
      </div>` : t.is_baileys ? `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})"
           style="border:2px solid #E65100;background:linear-gradient(135deg,#FFF3E0,#FFF8F0)">
        <div class="tenant-header">
          <span class="tenant-icon">${t.icon}</span>
          <div style="flex:1">
            <div class="tenant-name" style="color:#E65100;font-weight:900">${t.name}
              <span style="font-size:10px;background:#E65100;color:#fff;padding:2px 6px;border-radius:8px;margin-left:6px;font-weight:700">RARE</span>
            </div>
            <div style="font-size:11px;color:#BF360C">${t.stay_min}–${t.stay_max} day lease · ${t.desc}</div>
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label">Reliability</span>
            <span class="tm-value" style="color:#E65100;font-weight:800">★★★★★ Always</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Damage Risk</span>
            <span class="tm-value" style="color:var(--positive)">${t.damage_label}</span>
          </div>
          <div class="tenant-meta-item" style="grid-column:1/-1">
            <span class="tm-label">Special</span>
            <span class="tm-value" style="color:#E65100">Morale locked at 100% · Never damages · Never misses</span>
          </div>
        </div>
      </div>` : t.is_goldbergs ? `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})"
           style="border:2px solid #2E7D32;background:linear-gradient(135deg,#E8F5E9,#F1F8F1)">
        <div class="tenant-header">
          <span class="tenant-icon">${t.icon}</span>
          <div style="flex:1">
            <div class="tenant-name" style="color:#1B5E20;font-weight:900">${t.name}
              <span style="font-size:10px;background:#2E7D32;color:#fff;padding:2px 6px;border-radius:8px;margin-left:6px;font-weight:700">RARE</span>
            </div>
            <div style="font-size:11px;color:#2E7D32">${t.stay_min}–${t.stay_max} day lease · ${t.desc}</div>
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label">Reliability</span>
            <span class="tm-value" style="color:#2E7D32;font-weight:800">★★★★★ Always</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Damage Risk</span>
            <span class="tm-value" style="color:var(--positive)">${t.damage_label}</span>
          </div>
          <div class="tenant-meta-item" style="grid-column:1/-1">
            <span class="tm-label">Special</span>
            <span class="tm-value" style="color:#1B5E20">💰 Pays 10× rent automatically — short stay</span>
          </div>
        </div>
      </div>` : `
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

// Maps renovation/repair/job context → the mini-game that fits the work
const WORK_MG_MAP = {
  // Renovation upgrades
  'paint':       'paintgame',    // Paint the Wall — drag to cover tiles
  'flooring':    'flooringgame', // Lay the Floor — pick a color, tap matching planks
  'windows':     'reactiontap',  // Level It Up — precision fitting
  'hvac':        'sweetspot',    // Tighten the Fitting — mechanical tensioning
  'bathrooms':   'colormatch',   // Match the Tile — tiling
  'roof':        'quicktap',     // Drive the Nails — nailing shingles
  'kitchen':     'sweetspot',    // Tighten the Fitting — plumbing & fittings
  'landscaping': 'landscapegame', // Pull the Weeds — tap weeds before they take over
  // Repair types
  'plumbing':    'sweetspot',
  'electrical':  'sequence',     // Wire It Up — connect wires in order
  'appliance':   'sweetspot',
  'roof_patch':  'quicktap',
  'pest':        'reactiontap',
  'hvac_fix':    'sweetspot',
  // Side job names
  'Paint a Room':        'paintgame',
  'Lay Flooring':        'flooringgame',
  'Patch the Roof':      'quicktap',
  'Fix a Plumbing Leak': 'sweetspot',
  'Install Windows':     'reactiontap',
  'Tile a Bathroom':     'colormatch',
  'Hang Drywall':        'quicktap',
  'Electrical Work':     'sequence',
  'HVAC Maintenance':    'sweetspot',
  'Build a Fence':       'quicktap',
  'Pour Concrete':       'rapidpress',
  'Landscaping Work':    'landscapegame',
  'Power Washing':       'rapidpress',
  'Install Cabinets':    'reactiontap',
  'Repair a Deck':       'quicktap',
};
function selectMgType(context) { return WORK_MG_MAP[context] || randomMgType(); }

function launchMgByType(mgType, upgradeKey) {
  if      (mgType === 'quicktap')    launchQuickTap(upgradeKey);
  else if (mgType === 'sweetspot')   launchSweetSpot(upgradeKey);
  else if (mgType === 'sequence')    launchSequence(upgradeKey);
  else if (mgType === 'rapidpress')  launchRapidPress(upgradeKey);
  else if (mgType === 'colormatch')  launchColorMatch(upgradeKey);
  else if (mgType === 'reactiontap') launchReactionTap(upgradeKey);
  else if (mgType === 'paintgame')    launchPaintGame(upgradeKey);
  else if (mgType === 'landscapegame') launchLandscapeGame(upgradeKey);
  else if (mgType === 'flooringgame')  launchFlooringGame(upgradeKey);
}

async function showContractorModal(propId, upgradeKey) {
  pendingUpgrade = { propId, upgradeKey };
  const upgData  = await api(`/property/${propId}/upgrades`);
  const upg      = upgData.available.find(u => u.key === upgradeKey);
  if (!upg) return;

  const energy     = state.energy ?? DAILY_ENERGY;
  const maxE       = state.max_energy || DAILY_ENERGY;
  const ec         = upg.energy_cost ?? 1;
  const hasEnergy  = energy >= ec;
  const energyDots = `⚡ ${energy}/${maxE} remaining`;
  const ecPips     = '⚡'.repeat(ec) + '<span style="opacity:0.2">⚡</span>'.repeat(Math.max(0, 4 - ec));

  const diyCard = hasEnergy
    ? `<div class="contractor-card" style="border-color:var(--primary);margin-bottom:8px" onclick="startDIY('${upgradeKey}')">
        <div class="contractor-header">
          <span class="contractor-icon">🧰</span>
          <span class="contractor-name">Do It Yourself</span>
          <span class="contractor-cost" style="color:var(--positive)">FREE · ${ecPips}</span>
        </div>
        <div class="contractor-desc">Play a mini-game — how well you do determines the work quality.</div>
        <div class="contractor-quality">${energyDots}</div>
      </div>`
    : `<div class="contractor-card" style="border-color:var(--border);opacity:0.55;margin-bottom:8px">
        <div class="contractor-header">
          <span class="contractor-icon">🧰</span>
          <span class="contractor-name">Do It Yourself</span>
          <span class="contractor-cost" style="color:var(--negative)">Need ⚡${ec} (have ${energy})</span>
        </div>
        <div class="contractor-desc" style="color:var(--negative)">Not enough energy — advance the day to restore.</div>
        <div class="contractor-quality">${energyDots}</div>
      </div>`;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${upg.icon} ${upg.name}</div>
    <div class="modal-subtitle">Adds up to +${fmt(upg.value_add)} value · You have ${fmt(upgData.cash)}</div>

    ${diyCard}

    <div style="text-align:center;font-size:11px;color:var(--text-muted);margin-bottom:8px">── or hire a contractor ──</div>

    ${upg.special_contractor ? (() => {
      const sc   = upg.special_contractor;
      const days = contractorDays('premium', upg.energy_cost || 1);
      return `<div class="contractor-card contractor-special" onclick="hireContractor('special')">
        <div class="contractor-special-badge">⚡ SPECIAL — Guaranteed S+</div>
        <div class="contractor-header">
          <span class="contractor-icon">${sc.icon}</span>
          <span class="contractor-name">${sc.name}</span>
          <span class="contractor-cost">${fmt(sc.cost)}</span>
        </div>
        <div class="contractor-desc">${sc.desc}</div>
        <div class="contractor-quality">Grade: <strong style="color:#7B1FA2">S+</strong> guaranteed · ⏱ ${days} day${days !== 1 ? 's' : ''}</div>
      </div>`;
    })() : ''}

    ${Object.entries(upgData.contractors).map(([key, c]) => {
      const days = contractorDays(key, upg.energy_cost || 1);
      return `
      <div class="contractor-card" onclick="hireContractor('${key}')">
        <div class="contractor-header">
          <span class="contractor-icon">${c.icon}</span>
          <span class="contractor-name">${c.name}</span>
          <span class="contractor-cost">${fmt(upg.costs[key])}</span>
        </div>
        <div class="contractor-desc">${c.desc}</div>
        <div class="contractor-quality">Grade range: ${c.tier_range || 'F – S+'} · ⏱ ${days} day${days !== 1 ? 's' : ''}</div>
      </div>`;
    }).join('')}
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

function startDIY(upgradeKey) {
  if (!pendingUpgrade) return;
  _mg = { isRepair: false };
  launchMgByType(selectMgType(upgradeKey), upgradeKey);
}

async function finishDIY(upgradeKey, score) {
  if (_mg.isRepair) { await finishRepairDIY(score); return; }
  if (_mg.isJob)    { await finishJob(score); return; }
  const { propId } = pendingUpgrade;
  const res = await api('/diy_renovate', 'POST', { prop_id: propId, upgrade_key: upgradeKey, quality: score });
  pendingUpgrade = null;
  if (res.error) { toast(res.error, 'error'); await refreshState(); renderAll(); return; }
  // Update energy immediately from response so header reflects it right away
  if (res._state) state.energy = res._state.energy;
  const tColor    = tierColor(res.quality_tier);
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🧰 DIY Complete!</div>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:64px;font-weight:900;color:${tColor}">${res.quality_tier}</div>
      <div style="font-size:13px;color:var(--text-muted)">work grade</div>
      <div class="mg-score-bar" style="margin:8px 16px"><div class="mg-score-fill" style="width:${res.quality}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">New Condition</span><span class="mr-value" style="color:${tierColor(condTier(res.condition))};font-weight:900">${condTier(res.condition)}</span></div>
    <div class="money-row"><span class="mr-label">New Market Value</span><span class="mr-value green">${fmt(res.market_value)}</span></div>
    <div class="money-row"><span class="mr-label">New Weekly Rent</span><span class="mr-value green">${fmt(res.weekly_rent)}/wk</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Done</button>`);
  await refreshState();
  renderAll();
}

function contractorDays(contractorKey, energyCost) {
  if (contractorKey === 'budget')   return 1;
  if (contractorKey === 'standard') return energyCost <= 2 ? 2 : (energyCost === 3 ? 3 : 4);
  return energyCost <= 2 ? 4 : (energyCost === 3 ? 5 : 6); // premium or special
}

async function hireContractor(contractorKey) {
  if (!pendingUpgrade) return;
  const { propId, upgradeKey } = pendingUpgrade;
  const res = await api('/renovate', 'POST', { prop_id: propId, upgrade_key: upgradeKey, contractor_key: contractorKey });
  if (res.error) { toast(res.error, 'error'); return; }
  pendingUpgrade = null;
  const d = res.duration;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🔨 Work Underway!</div>
    <div class="modal-subtitle">${res.contractor_name} is on the job</div>
    <div style="text-align:center;padding:16px 0">
      <div style="font-size:48px">🏗️</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px">${d} Day${d !== 1 ? 's' : ''}</div>
      <div style="font-size:13px;color:var(--text-muted)">until completion</div>
    </div>
    <p style="font-size:13px;color:var(--text-muted);text-align:center;margin-bottom:16px">Advance time to complete the renovation. The result will be revealed when they finish.</p>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got It</button>`);
  await refreshState();
  renderAll();
}

// ── Side Jobs ─────────────────────────────────────────────────────────────────
function renderJobs() {
  const el      = document.getElementById('dash-jobs');
  const labelEl = document.getElementById('dash-jobs-energy');
  if (!el) return;
  const energy    = state.energy ?? DAILY_ENERGY;
  const maxE      = state.max_energy || DAILY_ENERGY;
  const jobs      = state.jobs  || [];
  const available = jobs.filter(j => energy >= j.energy_cost).length;
  if (labelEl) {
    labelEl.textContent = `⚡ ${energy}/${maxE}`;
    labelEl.style.color = energy === 0 ? 'var(--negative)' : energy <= 3 ? 'var(--warning)' : 'var(--text-muted)';
  }
  el.innerHTML = `
  <div class="card" style="display:flex;align-items:center;gap:14px">
    <div style="font-size:34px;line-height:1">💼</div>
    <div style="flex:1">
      <div style="font-size:15px;font-weight:800">Side Jobs</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:2px">
        ${jobs.length > 0
          ? `${jobs.length} job${jobs.length !== 1 ? 's' : ''} available · ${available} you can take`
          : 'No jobs — advance the day for new listings'}
      </div>
    </div>
    <button class="btn btn-primary btn-sm" onclick="showJobsModal()" ${jobs.length === 0 ? 'disabled style="opacity:0.4"' : ''}>
      Browse →
    </button>
  </div>`;
}

function showJobsModal() {
  const jobs   = state.jobs  || [];
  const energy = state.energy ?? DAILY_ENERGY;
  const maxE   = state.max_energy || DAILY_ENERGY;
  if (jobs.length === 0) {
    openModal(`
      <div class="modal-handle"></div>
      <div class="modal-title">💼 Side Jobs</div>
      <p class="text-muted" style="text-align:center;padding:16px 0">No jobs available — advance the day for fresh listings.</p>
      <button class="btn btn-ghost btn-full" onclick="closeModal()">Close</button>`);
    return;
  }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">💼 Side Jobs</div>
    <div class="modal-subtitle">⚡ ${energy} / ${maxE} energy remaining today</div>
    ${jobs.map(j => {
      const canTake  = energy >= j.energy_cost;
      const minPay   = Math.round(j.base_pay * 0.5);
      const pips     = '⚡'.repeat(j.energy_cost) + '<span style="opacity:0.2">⚡</span>'.repeat(Math.max(0, 4 - j.energy_cost));
      return `
      <div class="card" style="margin-bottom:10px${!canTake ? ';opacity:0.5' : ''}">
        <div class="card-header">
          <div class="card-icon">${j.icon}</div>
          <div style="flex:1">
            <div class="card-title">${j.name}</div>
            <div class="card-subtitle">${j.desc}</div>
          </div>
          <div style="text-align:right;flex-shrink:0;margin-left:8px">
            <div style="font-size:14px;font-weight:800;color:var(--positive)">${fmt(minPay)}–${fmt(j.base_pay)}</div>
            <div style="font-size:12px;margin-top:3px">${pips}</div>
          </div>
        </div>
        <button class="btn btn-sm btn-full ${canTake ? 'btn-primary' : 'btn-ghost'}"
          ${canTake ? `onclick="startJob(${j.id})"` : 'disabled'}
          style="${!canTake ? 'cursor:not-allowed' : ''}">
          ${canTake ? `Take Job · ⚡${j.energy_cost}` : `Need ⚡${j.energy_cost} (have ${energy})`}
        </button>
      </div>`;
    }).join('')}
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="closeModal()">Cancel</button>`);
}

function startJob(jobId) {
  const job = (state.jobs || []).find(j => j.id === jobId);
  if (!job) return;
  closeModal();   // dismiss the jobs picker modal first
  _pendingJob = job;
  _mg = { isJob: true };
  launchMgByType(selectMgType(job.name), 'job');
}

async function finishJob(score) {
  const job   = _pendingJob;
  _pendingJob = null;
  const res   = await api('/jobs/complete', 'POST', { job_id: job.id, quality: score });
  if (res.error) { toast(res.error, 'error'); await refreshState(); renderAll(); return; }
  // Immediately sync energy into local state so header updates before refreshState
  if (res._state) state.energy = res._state.energy;
  updateHeader();
  const qualColor = res.quality >= 75 ? 'var(--positive)' : res.quality >= 40 ? 'var(--warning)' : 'var(--negative)';
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">💼 Job Complete!</div>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:64px;font-weight:900;color:${qualColor}">${res.quality}%</div>
      <div style="font-size:13px;color:var(--text-muted)">work quality</div>
      <div class="mg-score-bar" style="margin:8px 16px"><div class="mg-score-fill" style="width:${res.quality}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Job</span><span class="mr-value">${job.name}</span></div>
    <div class="money-row"><span class="mr-label">Payout</span><span class="mr-value green">${fmt(res.pay)}</span></div>
    <div class="money-row"><span class="mr-label">Cash on Hand</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <div class="money-row"><span class="mr-label">Energy Left</span><span class="mr-value">⚡ ${res.energy} / ${state.max_energy || DAILY_ENERGY}</span></div>
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
    <div class="mg-wrap" style="background:#3E2723">
      <div class="mg-title" style="color:#FFCC80">🔨 Drive the Nails!</div>
      <div class="mg-desc" style="color:#BCAAA4">Tap each nail before it sinks into the wood! 8 nails total.</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#FFAB40" id="qt-hits">0</div><div style="color:#A1887F;font-size:11px">Driven</div></div>
        <div><div class="mg-stat-val" style="color:#FFAB40" id="qt-left">8</div><div style="color:#A1887F;font-size:11px">Left</div></div>
      </div>
      <div class="mg-tap-area" id="qt-area" style="background:#5D4037;border-color:#4E342E"></div>
    </div>
    <button class="btn btn-full" id="qt-start-btn" onclick="qtStart()" style="background:#FF8F00;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">🔨 Grab the Hammer</button>`);
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
  const emojis = ['🔩','🔩','🪛','🔩','🔩','🪛','🔩','🔩'];
  const emoji  = emojis[_mg.current % emojis.length];

  const el = document.createElement('div');
  el.className = 'mg-target';
  el.style.cssText = `left:${x}px;top:${y}px;width:${size}px;height:${size}px;background:#90A4AE;border-color:#546E7A`;
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
    <div class="mg-wrap" style="background:#ECEFF1">
      <div class="mg-title">🔧 Tighten the Fitting</div>
      <div class="mg-desc">Stop the dial in the green zone — perfect tension or it'll leak! 5 rounds, gets trickier.</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="ss-round">1</div><div style="font-size:11px">Round</div></div>
        <div><div class="mg-stat-val" id="ss-score">—</div><div style="font-size:11px">Pressure</div></div>
      </div>
      <div class="mg-bar-wrap" id="ss-bar" style="background:#CFD8DC">
        <div class="mg-zone"  id="ss-zone"></div>
        <div class="mg-needle" id="ss-needle" style="background:#E65100;width:8px"></div>
      </div>
      <button class="mg-lock-btn" id="ss-btn" onclick="ssLock()" style="display:none;background:#BF360C;letter-spacing:2px">🔒 LOCK TENSION!</button>
    </div>
    <button class="btn btn-primary btn-full" id="ss-start-btn" onclick="ssStart()">🔧 Pick Up the Wrench</button>`);
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
// Wire colours — match real electrical wire standards
const SEQ_COLORS  = ['#C62828', '#1565C0', '#2E7D32', '#F9A825'];
const SEQ_EMOJIS  = ['● RED', '● BLUE', '● GREEN', '● YELLOW'];
const SEQ_LENGTHS = [3, 3, 4, 4, 5];

function launchSequence(upgradeKey) {
  _mg = { ..._mg, round: 0, seq: [], playerSeq: [], totalRounds: 5, correct: 0, showing: false, upgradeKey };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap" style="background:#212121">
      <div class="mg-title" style="color:#FFD54F">⚡ Wire It Up!</div>
      <div class="mg-desc" style="color:#9E9E9E">Watch which wires light up, then connect them in the same order!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#FFD54F" id="seq-round">1</div><div style="color:#757575;font-size:11px">Round</div></div>
        <div><div class="mg-stat-val" style="color:#69F0AE" id="seq-correct">0</div><div style="color:#757575;font-size:11px">Correct</div></div>
      </div>
      <div class="mg-seq-grid">
        ${SEQ_COLORS.map((c, i) => `<button class="mg-seq-btn" id="seq-btn-${i}" style="background:${c};font-size:13px;font-weight:900;color:rgba(255,255,255,0.9);letter-spacing:1px" onclick="seqPress(${i})">${SEQ_EMOJIS[i]}</button>`).join('')}
      </div>
      <div id="seq-status" style="text-align:center;font-size:13px;color:#9E9E9E;margin-top:4px">Watch carefully…</div>
    </div>
    <button class="btn btn-full" id="seq-start-btn" onclick="seqStart()" style="background:#F57F17;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">⚡ Open the Panel</button>`);
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

// ── Mini-game: Paint the Wall ────────────────────────────────────────────────
// Drag finger across tiles to paint them before the timer runs out.
// Score = % of tiles covered.
const PAINT_COLORS = [
  { name: 'Cerulean Blue',  color: '#1565C0', dark: '#0D47A1' },
  { name: 'Forest Green',   color: '#2E7D32', dark: '#1B5E20' },
  { name: 'Sunset Orange',  color: '#E65100', dark: '#BF360C' },
  { name: 'Deep Purple',    color: '#6A1B9A', dark: '#4A148C' },
  { name: 'Ruby Red',       color: '#C62828', dark: '#B71C1C' },
  { name: 'Teal',           color: '#00695C', dark: '#004D40' },
  { name: 'Goldenrod',      color: '#F57F17', dark: '#E65100' },
];

const PG_COLS     = 6;
const PG_ROWS     = 8;
const PG_TOTAL    = PG_COLS * PG_ROWS;  // 48 tiles
const PG_DURATION = 2.5;                // seconds

function launchPaintGame(upgradeKey) {
  closeModal();  // dismiss any open modal before going fullscreen
  const paintColor = PAINT_COLORS[Math.floor(Math.random() * PAINT_COLORS.length)];
  _mg = { ..._mg, upgradeKey, painted: new Set(), running: false, timerId: null,
          paintColor, dragActive: false, finalScore: 0, locked: true };

  // Remove any leftover overlay
  const old = document.getElementById('pg-overlay');
  if (old) old.remove();

  const overlay     = document.createElement('div');
  overlay.id        = 'pg-overlay';
  overlay.className = 'pg-overlay';
  overlay.innerHTML = `
    <div class="pg-header">
      <div class="pg-top-row">
        <span class="pg-title">🎨 Paint the Wall!</span>
        <span class="pg-pct-badge" id="pg-pct">0%</span>
      </div>
      <div class="pg-timer-track">
        <div class="pg-timer-fill" id="pg-timer-fill"></div>
      </div>
      <div class="pg-time-label"><span id="pg-time">${PG_DURATION}</span>s remaining</div>
    </div>
    <div class="pg-grid" id="pg-grid"></div>
    <div class="pg-start-screen" id="pg-start-screen">
      <div class="pg-start-card">
        <div class="pg-start-swatch" style="background:${paintColor.color}"></div>
        <div class="pg-start-color">${paintColor.name}</div>
        <div class="pg-start-desc">Drag your finger across every tile<br>before time runs out!</div>
        <button class="pg-start-btn" style="background:${paintColor.color};box-shadow:0 4px 18px ${paintColor.dark}88" onclick="pgStart()">
          🎨 Start Painting!
        </button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Populate grid with unpainted tiles
  const grid = document.getElementById('pg-grid');
  for (let i = 0; i < PG_TOTAL; i++) {
    const tile       = document.createElement('div');
    tile.className   = 'pg-tile';
    tile.dataset.idx = String(i);
    grid.appendChild(tile);
  }

  // Attach drag events to the grid
  grid.addEventListener('touchstart', pgTouchStart, { passive: false });
  grid.addEventListener('touchmove',  pgTouchMove,  { passive: false });
  grid.addEventListener('touchend',   pgTouchEnd,   { passive: false });
  grid.addEventListener('mousedown',  pgMouseDown);
  grid.addEventListener('mousemove',  pgMouseMove);
  grid.addEventListener('mouseup',    pgMouseUp);
  document.addEventListener('mouseup', pgMouseUp);
}

function pgStart() {
  const ss = document.getElementById('pg-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + PG_DURATION * 1000;

  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (PG_DURATION * 1000);
    const fill = document.getElementById('pg-timer-fill');
    const timeEl = document.getElementById('pg-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#4CAF50' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; pgFinish(); }
  }, 50);
}

function pgPaintTile(el) {
  if (!_mg.running || !el || !el.classList.contains('pg-tile') || el.classList.contains('painted')) return;
  el.classList.add('painted');
  el.style.background = _mg.paintColor.color;
  _mg.painted.add(el.dataset.idx);

  const pct   = Math.round((_mg.painted.size / PG_TOTAL) * 100);
  const pctEl = document.getElementById('pg-pct');
  if (pctEl) pctEl.textContent = pct + '%';

  if (_mg.painted.size >= PG_TOTAL) {
    clearInterval(_mg.timerId);
    _mg.running = false;
    setTimeout(pgFinish, 300);
  }
}

function pgTouchStart(e) {
  e.preventDefault();
  _mg.dragActive = true;
  const t = e.touches[0];
  pgPaintTile(document.elementFromPoint(t.clientX, t.clientY));
}
function pgTouchMove(e) {
  e.preventDefault();
  if (!_mg.dragActive) return;
  const t = e.touches[0];
  pgPaintTile(document.elementFromPoint(t.clientX, t.clientY));
}
function pgTouchEnd(e)  { e.preventDefault(); _mg.dragActive = false; }
function pgMouseDown(e) { _mg.dragActive = true;  pgPaintTile(document.elementFromPoint(e.clientX, e.clientY)); }
function pgMouseMove(e) { if (_mg.dragActive) pgPaintTile(document.elementFromPoint(e.clientX, e.clientY)); }
function pgMouseUp()    { _mg.dragActive = false; }

function pgFinish() {
  clearInterval(_mg.timerId);
  document.removeEventListener('mouseup', pgMouseUp);

  const painted = _mg.painted.size;
  const score   = Math.round((painted / PG_TOTAL) * 100);
  _mg.finalScore = score;
  _mg.locked     = false;

  const msg   = score >= 90 ? '🌟 Flawless coverage!'  :
                score >= 70 ? '✅ Solid coat!'           :
                score >= 50 ? '👍 Getting there!'        :
                              '🫤 Needs another coat...';
  const color = _mg.paintColor.color;

  const overlay = document.getElementById('pg-overlay');
  if (overlay) {
    const res       = document.createElement('div');
    res.className   = 'pg-result-overlay';
    res.innerHTML   = `
      <div class="pg-result-card">
        <div class="pg-result-score" style="color:${color}">${score}%</div>
        <div class="pg-result-tiles">${painted} / ${PG_TOTAL} tiles painted</div>
        <div class="pg-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }

  _mg.autoCloseId = setTimeout(pgClose, 2400);
}

function pgClose() {
  clearTimeout(_mg.autoCloseId);
  document.removeEventListener('mouseup', pgMouseUp);
  const overlay = document.getElementById('pg-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Pull the Weeds (Landscaping) ──────────────────────────────────
// Weeds spawn across a grass field and speed up over time.
// Tap them before they expire. Score = weeds pulled (15 = 100%).
const LG_DURATION  = 16;    // seconds
const LG_WEED_LIFE = 1600;  // ms before a weed expires on its own
const LG_TARGET    = 30;    // pulls for 100%
const LG_WEEDS     = ['🌿', '🌱', '🍃', '🌾'];

function launchLandscapeGame(upgradeKey) {
  closeModal();
  _mg = { ..._mg, upgradeKey, pulled: 0, weeds: {}, weedId: 0,
          running: false, timerId: null, spawnId: null,
          startTime: 0, locked: true, finalScore: 0 };

  const old = document.getElementById('lg-overlay');
  if (old) old.remove();

  const overlay     = document.createElement('div');
  overlay.id        = 'lg-overlay';
  overlay.className = 'lg-overlay';
  overlay.innerHTML = `
    <div class="lg-header">
      <div class="lg-top-row">
        <span class="lg-title">🌿 Pull the Weeds!</span>
        <span class="lg-count" id="lg-count">🌿 0</span>
      </div>
      <div class="lg-timer-track">
        <div class="lg-timer-fill" id="lg-timer-fill"></div>
      </div>
      <div class="lg-time-label"><span id="lg-time">${LG_DURATION}</span>s remaining</div>
    </div>
    <div class="lg-field" id="lg-field"></div>
    <div class="lg-start-screen" id="lg-start-screen">
      <div class="lg-start-card">
        <div class="lg-start-icon">🌿</div>
        <div class="lg-start-title">Pull the Weeds!</div>
        <div class="lg-start-desc">Tap every weed as fast as you can<br>before they take over the yard!</div>
        <button class="lg-start-btn" onclick="lgStart()">🌿 Let's Go!</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
}

function lgStart() {
  const ss = document.getElementById('lg-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running   = true;
  _mg.startTime = Date.now();
  const endTime = _mg.startTime + LG_DURATION * 1000;

  // Countdown timer
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (LG_DURATION * 1000);
    const fill = document.getElementById('lg-timer-fill');
    const timeEl = document.getElementById('lg-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#4CAF50' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      clearTimeout(_mg.spawnId);
      _mg.running = false;
      lgFinish();
    }
  }, 50);

  lgScheduleSpawn();
}

function lgScheduleSpawn() {
  if (!_mg.running) return;
  lgSpawnWeed();
  const elapsed  = Date.now() - _mg.startTime;
  const progress = Math.min(1, elapsed / (LG_DURATION * 1000));
  const delay    = Math.max(160, 700 - progress * 720); // 700ms → 160ms (accelerates 50% faster)
  _mg.spawnId    = setTimeout(lgScheduleSpawn, delay);
}

function lgSpawnWeed() {
  const field = document.getElementById('lg-field');
  if (!field || !_mg.running) return;

  const id    = _mg.weedId++;
  const emoji = LG_WEEDS[Math.floor(Math.random() * LG_WEEDS.length)];
  const x     = 8  + Math.random() * 75;  // 8–83% left
  const y     = 8  + Math.random() * 72;  // 8–80% top

  const el       = document.createElement('div');
  el.className   = 'lg-weed';
  el.id          = `lgw-${id}`;
  el.textContent = emoji;
  el.style.left  = x + '%';
  el.style.top   = y + '%';

  el.addEventListener('click', () => lgPullWeed(id));
  el.addEventListener('touchstart', (e) => {
    e.preventDefault();
    e.stopPropagation();
    lgPullWeed(id);
  }, { passive: false });

  field.appendChild(el);
  _mg.weeds[id] = el;

  el._expireId = setTimeout(() => lgExpireWeed(id), LG_WEED_LIFE);
}

function lgPullWeed(id) {
  const el = _mg.weeds[id];
  if (!el || el.classList.contains('pulled') || el.classList.contains('expired')) return;
  clearTimeout(el._expireId);
  el.classList.add('pulled');
  delete _mg.weeds[id];
  _mg.pulled++;

  const countEl = document.getElementById('lg-count');
  if (countEl) countEl.textContent = '🌿 ' + _mg.pulled;

  setTimeout(() => { if (el.parentNode) el.remove(); }, 300);
}

function lgExpireWeed(id) {
  const el = _mg.weeds[id];
  if (!el) return;
  el.classList.add('expired');
  delete _mg.weeds[id];
  setTimeout(() => { if (el.parentNode) el.remove(); }, 400);
}

function lgFinish() {
  clearInterval(_mg.timerId);
  clearTimeout(_mg.spawnId);
  Object.keys(_mg.weeds).forEach(id => lgExpireWeed(Number(id)));
  _mg.locked = false;

  const score    = Math.min(100, Math.round((_mg.pulled / LG_TARGET) * 100));
  _mg.finalScore = score;

  const msg = score >= 90 ? '🌟 Spotless yard!'              :
              score >= 70 ? '✅ Nice work!'                   :
              score >= 50 ? '👍 Getting there!'               :
                            '🌿 Still a jungle out there...';

  const overlay = document.getElementById('lg-overlay');
  if (overlay) {
    const res     = document.createElement('div');
    res.className = 'lg-result-overlay';
    res.innerHTML = `
      <div class="lg-result-card">
        <div class="lg-result-score">${_mg.pulled}</div>
        <div class="lg-result-label">weeds pulled</div>
        <div class="lg-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }

  _mg.autoCloseId = setTimeout(lgClose, 2400);
}

function lgClose() {
  clearTimeout(_mg.autoCloseId);
  const overlay = document.getElementById('lg-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Lay the Flooring ──────────────────────────────────────────────
// Board of planks each tagged with one of 4 colors. Tap a color from the bottom
// palette, then tap matching planks to lay them. Score = planks laid / total.
const FG_COLS     = 4;
const FG_ROWS     = 8;
const FG_TOTAL    = FG_COLS * FG_ROWS;  // 32 planks
const FG_DURATION = 18;                 // seconds
const FG_COLORS   = [
  { id: 0, name: 'Oak',    bg: '#C9974A', dark: '#8A6428', grain: '#DDB96A' },
  { id: 1, name: 'Walnut', bg: '#5A3018', dark: '#321A08', grain: '#7A4828' },
  { id: 2, name: 'Cherry', bg: '#8C2418', dark: '#5C140A', grain: '#B44030' },
  { id: 3, name: 'Ash',    bg: '#C8BEAE', dark: '#9A9080', grain: '#E0DCD2' },
];

function launchFlooringGame(upgradeKey) {
  closeModal();

  // Build balanced board: exactly 8 of each color, shuffled
  const rawTargets = Array.from({ length: FG_TOTAL }, (_, i) => i % FG_COLORS.length);
  for (let i = rawTargets.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [rawTargets[i], rawTargets[j]] = [rawTargets[j], rawTargets[i]];
  }

  _mg = { ..._mg, upgradeKey, placed: 0, selectedColor: null,
          targets: rawTargets, timerId: null, running: false,
          startTime: 0, locked: true, finalScore: 0 };

  const old = document.getElementById('fg-overlay');
  if (old) old.remove();

  // Build board HTML
  let boardHtml = '';
  for (let i = 0; i < FG_TOTAL; i++) {
    const c = FG_COLORS[rawTargets[i]];
    boardHtml += `<div class="fg-plank" id="fgp-${i}" data-idx="${i}" data-target="${rawTargets[i]}"
      style="--fg-target:${c.bg};--fg-grain:${c.grain};--fg-dark:${c.dark}"></div>`;
  }

  // Build palette HTML
  let paletteHtml = '';
  FG_COLORS.forEach(c => {
    paletteHtml += `<button class="fg-color-btn" data-color="${c.id}"
      style="--fg-btn-bg:${c.bg};--fg-btn-dark:${c.dark};--fg-btn-grain:${c.grain}"
      ontouchstart="fgSelectColor(${c.id});event.preventDefault()"
      onclick="fgSelectColor(${c.id})">
      <span class="fg-btn-name">${c.name}</span>
    </button>`;
  });

  const overlay     = document.createElement('div');
  overlay.id        = 'fg-overlay';
  overlay.className = 'fg-overlay';
  overlay.innerHTML = `
    <div class="fg-header">
      <div class="fg-top-row">
        <span class="fg-title">🪵 Lay the Flooring!</span>
        <span class="fg-score" id="fg-score">🪵 0 / ${FG_TOTAL}</span>
      </div>
      <div class="fg-timer-track">
        <div class="fg-timer-fill" id="fg-timer-fill"></div>
      </div>
      <div class="fg-time-label"><span id="fg-time">${FG_DURATION}</span>s remaining</div>
    </div>
    <div class="fg-board" id="fg-board">${boardHtml}</div>
    <div class="fg-palette" id="fg-palette">${paletteHtml}</div>
    <div class="fg-start-screen" id="fg-start-screen">
      <div class="fg-start-card">
        <div class="fg-start-icon">🪵</div>
        <div class="fg-start-title">Lay the Flooring!</div>
        <div class="fg-start-desc">Pick a color from the bottom<br>then tap the matching planks on the board!</div>
        <button class="fg-start-btn" ontouchstart="fgStart();event.preventDefault()" onclick="fgStart()">🪵 Let's Go!</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Attach handlers to planks
  overlay.querySelectorAll('.fg-plank').forEach(el => {
    el.addEventListener('click', () => fgTapPlank(parseInt(el.dataset.idx)));
    el.addEventListener('touchstart', e => {
      e.preventDefault();
      e.stopPropagation();
      fgTapPlank(parseInt(el.dataset.idx));
    }, { passive: false });
  });
}

function fgStart() {
  const ss = document.getElementById('fg-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running   = true;
  _mg.startTime = Date.now();
  const endTime = _mg.startTime + FG_DURATION * 1000;

  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (FG_DURATION * 1000);
    const fill  = document.getElementById('fg-timer-fill');
    const timeEl = document.getElementById('fg-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#FF8C00' : pct > 0.25 ? '#FF6B00' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      fgFinish();
    }
  }, 50);
}

function fgSelectColor(colorId) {
  if (!_mg.running) return;
  _mg.selectedColor = colorId;
  document.querySelectorAll('.fg-color-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.color) === colorId);
  });
}

function fgTapPlank(idx) {
  if (!_mg.running) return;

  // No color selected — shake the palette as a hint
  if (_mg.selectedColor === null) {
    const pal = document.getElementById('fg-palette');
    if (pal) { pal.classList.add('fg-shake'); setTimeout(() => pal.classList.remove('fg-shake'), 400); }
    return;
  }

  const el = document.getElementById(`fgp-${idx}`);
  if (!el || el.classList.contains('fg-placed')) return;

  const target = parseInt(el.dataset.target);

  if (_mg.selectedColor === target) {
    // Correct placement
    const c = FG_COLORS[target];
    el.classList.add('fg-placed');
    el.style.setProperty('--fg-placed-bg',    c.bg);
    el.style.setProperty('--fg-placed-dark',  c.dark);
    el.style.setProperty('--fg-placed-grain', c.grain);
    _mg.placed++;
    const scoreEl = document.getElementById('fg-score');
    if (scoreEl) scoreEl.textContent = `🪵 ${_mg.placed} / ${FG_TOTAL}`;
    // All done early?
    if (_mg.placed >= FG_TOTAL) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      fgFinish();
    }
  } else {
    // Wrong color — flash red
    el.classList.add('fg-wrong');
    setTimeout(() => el.classList.remove('fg-wrong'), 350);
  }
}

function fgFinish() {
  clearInterval(_mg.timerId);
  _mg.locked = false;

  const score    = Math.min(100, Math.round((_mg.placed / FG_TOTAL) * 100));
  _mg.finalScore = score;

  const msg = score >= 90 ? '🌟 Perfect install!'          :
              score >= 70 ? '✅ Looking good!'              :
              score >= 50 ? '👍 Halfway there!'             :
                            '🪵 Back to the hardware store...';

  const overlay = document.getElementById('fg-overlay');
  if (overlay) {
    const res     = document.createElement('div');
    res.className = 'fg-result-overlay';
    res.innerHTML = `
      <div class="fg-result-card">
        <div class="fg-result-score">${_mg.placed}</div>
        <div class="fg-result-label">planks laid</div>
        <div class="fg-result-pct">${score}%</div>
        <div class="fg-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }

  _mg.autoCloseId = setTimeout(fgClose, 2400);
}

function fgClose() {
  clearTimeout(_mg.autoCloseId);
  const overlay = document.getElementById('fg-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Rapid Press ────────────────────────────────────────────────────
// Mash the button as fast as possible in 3 seconds. 30 presses = 100%.
function launchRapidPress(upgradeKey) {
  _mg = { ..._mg, presses: 0, target: 30, upgradeKey, running: false, timerId: null };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap" style="background:#FFF8E1">
      <div class="mg-title">🎨 Roll It Out!</div>
      <div class="mg-desc">Keep that roller moving — cover the whole surface in 3 seconds!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#E65100" id="rp-count">0</div><div style="font-size:11px">Strokes</div></div>
        <div><div class="mg-stat-val" style="color:#E65100" id="rp-time">3.0</div><div style="font-size:11px">Seconds</div></div>
      </div>
      <div style="height:22px;background:#E0E0E0;border-radius:4px;overflow:hidden;margin-bottom:14px">
        <div id="rp-bar" style="width:0%;height:100%;border-radius:4px;background:linear-gradient(90deg,#EF9A9A,#CE93D8,#90CAF9,#A5D6A7,#FFF176);transition:width 0.1s"></div>
      </div>
      <button class="mg-rapid-btn" id="rp-btn" onclick="rpPress()" style="display:none;background:#E65100;font-size:22px">🖌️ ROLL!</button>
    </div>
    <button class="btn btn-full" id="rp-start" onclick="rpStart()" style="background:#F57C00;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">🎨 Dip the Roller</button>`);
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
// Tile colours — earthy construction tones, all legible with white text
const CM_COLORS = [
  { name: 'SLATE',  bg: '#455A64', label: 'Slate'      },
  { name: 'TERRA',  bg: '#BF360C', label: 'Terracotta' },
  { name: 'MOSS',   bg: '#33691E', label: 'Moss'       },
  { name: 'SAND',   bg: '#795548', label: 'Sandstone'  },
];

function launchColorMatch(upgradeKey) {
  _mg = { ..._mg, round: 0, totalRounds: 8, correct: 0, upgradeKey, waiting: false, timerId: null, timeLimit: 1400 };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap">
      <div class="mg-title">🪵 Match the Tile!</div>
      <div class="mg-desc">Tap the tile that matches the sample — it gets faster each round!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="cm-correct">0</div><div style="font-size:11px">Matched</div></div>
        <div><div class="mg-stat-val" id="cm-round">1</div><div style="font-size:11px">Round</div></div>
      </div>
      <div class="mg-color-show" id="cm-show" style="font-size:15px;font-weight:900;letter-spacing:3px;border:4px solid #5D4037;border-radius:8px">SAMPLE</div>
      <div class="mg-color-grid">
        ${CM_COLORS.map((c, i) => `<button class="mg-color-btn" id="cm-btn-${i}" style="background:${c.bg}" onclick="cmPress(${i})">${c.label}</button>`).join('')}
      </div>
    </div>
    <button class="btn btn-primary btn-full" id="cm-start" onclick="cmStart()">🪵 Open the Tile Box</button>`);
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
    <div class="mg-wrap" style="background:#E3F2FD">
      <div class="mg-title" style="color:#1565C0">📐 Level It Up!</div>
      <div class="mg-desc" style="color:#546E7A">Watch the bubble — tap the instant it centers in the tube!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#1565C0" id="rt-round">1</div><div style="color:#546E7A;font-size:11px">Round</div></div>
        <div><div class="mg-stat-val" style="color:#1565C0" id="rt-best">—</div><div style="color:#546E7A;font-size:11px">Best ms</div></div>
      </div>
      <div class="mg-reaction-light" id="rt-light" style="background:#1565C0;border-color:#0D47A1;box-shadow:none">↔️</div>
      <button class="mg-reaction-tap-btn" id="rt-tap" onclick="rtTap()" disabled style="background:#37474F;letter-spacing:1px">Hold steady…</button>
    </div>
    <button class="btn btn-full" id="rt-start" onclick="rtStart()" style="background:#1565C0;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">📐 Get the Level</button>`);
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
  // Waiting — bubble off-center (blue)
  light.dataset.state  = 'waiting';
  light.style.cssText  = 'background:#1565C0;border-color:#0D47A1;box-shadow:none';
  light.textContent    = '↔️';
  btn.disabled         = true;
  btn.textContent      = 'Hold steady…';
  btn.style.background = '#37474F';
  _mg.waiting          = false;
  const delay = 1500 + Math.random() * 2500;
  clearTimeout(_mg.timerId);
  _mg.timerId = setTimeout(() => {
    // Centered — tap now! (green)
    light.dataset.state  = 'go';
    light.style.cssText  = 'background:#2E7D32;border-color:#1B5E20;box-shadow:0 0 30px #4CAF5080';
    light.textContent    = '📐';
    btn.disabled         = false;
    btn.textContent      = '✅ LEVEL!';
    btn.style.background = '#2E7D32';
    _mg.greenAt          = Date.now();
    _mg.waiting          = true;
    // auto-fail if too slow
    _mg.timerId = setTimeout(() => {
      if (_mg.waiting) {
        _mg.waiting          = false;
        _mg.times.push(2000);
        _mg.round++;
        document.getElementById('rt-round').textContent = Math.min(_mg.round + 1, _mg.totalRounds);
        btn.disabled         = true;
        light.dataset.state  = 'missed';
        light.style.cssText  = 'background:#B71C1C;border-color:#7F0000;box-shadow:none';
        light.textContent    = '❌';
        setTimeout(rtNextRound, 700);
      }
    }, 2000);
  }, delay);
}

function rtTap() {
  if (!_mg.waiting) {
    // Tapped too early — bubble not centered yet!
    const light = document.getElementById('rt-light');
    if (light && light.dataset.state === 'waiting') {
      light.style.cssText = 'background:#F57F17;border-color:#E65100;box-shadow:none';
      light.textContent   = '⚠️';
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
  if (btn)   { btn.textContent = `${reaction}ms!`; btn.disabled = true; }
  if (light) { light.dataset.state = 'done'; light.textContent = reaction < 400 ? '⚡' : '📐'; }
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

  _pendingRepairs       = res.repairs        || [];
  _pendingMoraleEvents  = res.morale_events  || [];
  _pendingRenewalOffers = res.renewal_offers || [];
  _pendingSquatter      = (res.events || []).find(e => e.type === 'squatter') || null;
  const totalPending    = _pendingRepairs.length + _pendingMoraleEvents.length + _pendingRenewalOffers.length;
  const repairNote = _pendingRepairs.length > 0
    ? `<div style="background:var(--warning-bg,#FFF8E1);border:2px solid var(--warning);border-radius:var(--radius-sm);padding:10px 12px;margin-top:12px;font-size:13px;font-weight:700">
        🔧 ${_pendingRepairs.length} repair${_pendingRepairs.length > 1 ? 's' : ''} need${_pendingRepairs.length === 1 ? 's' : ''} attention!</div>`
    : '';
  const moraleNote = _pendingMoraleEvents.length > 0
    ? `<div style="background:#F3E5F5;border:2px solid #CE93D8;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        💬 ${_pendingMoraleEvents.length} tenant request${_pendingMoraleEvents.length > 1 ? 's' : ''} waiting!</div>`
    : '';
  const renewalNote = _pendingRenewalOffers.length > 0
    ? `<div style="background:#E8F5E9;border:2px solid #66BB6A;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        🔄 ${_pendingRenewalOffers.length} lease renewal${_pendingRenewalOffers.length > 1 ? 's' : ''} to review!</div>`
    : '';

  const btnLabel = _pendingRepairs.length > 0
    ? `Fix Repairs (${_pendingRepairs.length})`
    : _pendingMoraleEvents.length > 0
      ? `Respond to Requests (${_pendingMoraleEvents.length})`
      : _pendingRenewalOffers.length > 0
        ? `Review Leases (${_pendingRenewalOffers.length})`
        : 'Continue';

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${s.icon} ${s.name} · Day ${s.seasonDay}</div>
    <div class="modal-subtitle">Year ${s.year} · Overall Day ${res.day}</div>
    <div class="money-row"><span class="mr-label">Cash</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Net Worth</span><span class="mr-value green">${fmt(res.net_worth)}</span></div>
    <div class="section-title" style="margin-bottom:8px">Events</div>
    ${eventsHtml}
    ${repairNote}
    ${moraleNote}
    ${renewalNote}
    <button class="btn btn-primary btn-full mt-8" onclick="continueFromEvents()">${btnLabel}</button>`);

  await refreshState();
  await refreshMarketListings();
  renderAll();
}

function continueFromEvents() {
  if (_pendingRepairs.length > 0) {
    showNextRepair();
  } else if (_pendingMoraleEvents.length > 0) {
    showNextMoraleEvent();
  } else if (_pendingRenewalOffers.length > 0) {
    showNextRenewalOffer();
  } else if (_pendingSquatter) {
    const sq = _pendingSquatter;
    _pendingSquatter = null;
    showSquatterModal(sq.prop_id, sq.bribe, sq.prop_name);
  } else {
    closeModal();
  }
}

function showSquatterModal(propId, bribe, propName) {
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🚨 Squatters!</div>
    <div class="modal-subtitle">${propName}</div>
    <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px">
      Someone has moved into your vacant property without permission. They're refusing to leave and not paying a dime. What do you want to do?
    </p>
    <div class="card" style="margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="font-size:30px">💸</span>
        <div>
          <div style="font-size:15px;font-weight:800">Pay Them Off</div>
          <div style="font-size:12px;color:var(--text-muted)">They'll leave immediately — no questions asked.</div>
        </div>
      </div>
      <div class="money-row" style="margin-bottom:10px">
        <span class="mr-label">Their asking price</span>
        <span class="mr-value" style="color:#C62828">${fmt(bribe)}</span>
      </div>
      <button class="btn btn-danger btn-full" onclick="briberSquatter(${propId})">💸 Pay ${fmt(bribe)} to Remove Them</button>
    </div>
    <div class="card">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="font-size:30px">⏳</span>
        <div>
          <div style="font-size:15px;font-weight:800">Wait It Out</div>
          <div style="font-size:12px;color:var(--text-muted)">They might leave eventually. Or they might not. Hard to say.</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-full" onclick="closeModal()">Do Nothing for Now</button>
    </div>`);
}

async function briberSquatter(propId) {
  const res = await api('/squatter/bribe', 'POST', { prop_id: propId });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Squatters gone! Paid ${fmt(res.bribe_paid)}.`);
  closeModal();
  await refreshState();
  renderAll();
}

// ── Morale Events ─────────────────────────────────────────────────────────────
function showNextMoraleEvent() {
  if (_pendingMoraleEvents.length === 0) { continueFromEvents(); return; }
  showMoraleEventModal(_pendingMoraleEvents.shift());
}

function showMoraleEventModal(ev) {
  const damPct = Math.round(ev.damage_chance * 100);
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${ev.icon} Tenant Request</div>
    <div class="modal-subtitle">${ev.prop_name}</div>
    <p style="font-size:14px;color:var(--text-2);margin-bottom:16px">${ev.message}</p>

    <div class="card" style="margin-bottom:10px;border:2px solid var(--positive)">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="font-size:24px">✅</span>
        <div style="flex:1">
          <div style="font-size:14px;font-weight:800">Agree</div>
          <div style="font-size:12px;color:var(--text-muted)">
            Morale +${ev.morale_gain} · ${damPct}% chance of −${ev.damage_pts} condition
          </div>
        </div>
      </div>
      <button class="btn btn-primary btn-full" onclick="respondMoraleEvent(${ev.prop_id},'${ev.key}',true)">
        ${ev.agree_label}
      </button>
    </div>

    <div class="card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="font-size:24px">❌</span>
        <div style="flex:1">
          <div style="font-size:14px;font-weight:800">Decline</div>
          <div style="font-size:12px;color:var(--text-muted)">Tenant morale drops 5–10 points.</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-full" onclick="respondMoraleEvent(${ev.prop_id},'${ev.key}',false)">
        ${ev.decline_label}
      </button>
    </div>

    ${_pendingMoraleEvents.length > 0
      ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingMoraleEvents.length} more request(s) after this</div>`
      : ''}`);
}

async function respondMoraleEvent(propId, eventKey, agree) {
  const res = await api('/tenant_event/respond', 'POST', { prop_id: propId, event_key: eventKey, agree });
  if (res.error) { toast(res.error, 'error'); return; }
  if (agree) {
    if (res.condition_change < 0) {
      toast(`They made a mess! Condition −${Math.abs(res.condition_change)} pts`, 'warning');
    } else {
      toast(`Agreed! Tenant morale +${res.morale_change}`, 'success');
    }
  } else {
    toast(`Declined — tenant morale ${res.morale_change}`, 'warning');
  }
  await refreshState();
  renderAll();
  showNextMoraleEvent();
}

// ── Lease Renewal ─────────────────────────────────────────────────────────────
function showNextRenewalOffer() {
  if (_pendingRenewalOffers.length === 0) { continueFromEvents(); return; }
  showRenewalModal(_pendingRenewalOffers.shift());
}

function showRenewalModal(offer) {
  const missed = offer.missed_payments || 0;
  const missedColor = missed === 0 ? 'var(--positive)' : missed <= 2 ? 'var(--warning)' : 'var(--negative)';
  const missedLabel = missed === 0
    ? '✅ Never missed a payment'
    : missed === 1 ? '⚠️ Late on rent 1 time'
    : `🚨 Late on rent ${missed} times`;
  const stayLabel = offer.new_stay_days >= 90
    ? `~${Math.round(offer.new_stay_days / 28)} seasons`
    : `${offer.new_stay_days} days`;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🔄 Lease Renewal</div>
    <div class="modal-subtitle">${offer.prop_name}</div>

    <div class="card" style="margin-bottom:14px;text-align:center">
      <div style="font-size:32px;margin-bottom:4px">${offer.tenant_icon}</div>
      <div style="font-weight:800;font-size:15px">${offer.tenant_name}</div>
      <div style="font-size:13px;color:var(--text-muted);margin-top:4px">wants to stay for another <strong>${stayLabel}</strong></div>
      <div style="font-size:13px;margin-top:6px">Rent: <strong>${fmt(offer.rent)}/wk</strong></div>
      <div style="font-size:13px;margin-top:4px;color:${missedColor};font-weight:700">${missedLabel}</div>
    </div>

    <div class="card" style="margin-bottom:10px;border:2px solid var(--positive)">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="font-size:24px">✅</span>
        <div><div style="font-size:14px;font-weight:800">Renew Lease</div>
          <div style="font-size:12px;color:var(--text-muted)">They stay for another ${stayLabel} at the same rent</div>
        </div>
      </div>
      <button class="btn btn-primary btn-full" onclick="respondRenewal(${offer.prop_id}, true)">Renew Lease</button>
    </div>

    <div class="card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="font-size:24px">👋</span>
        <div><div style="font-size:14px;font-weight:800">Let Them Go</div>
          <div style="font-size:12px;color:var(--text-muted)">They move out and the property goes vacant</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-full" onclick="respondRenewal(${offer.prop_id}, false)">Let Them Go</button>
    </div>

    ${_pendingRenewalOffers.length > 0
      ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingRenewalOffers.length} more renewal(s) after this</div>`
      : ''}`);
}

async function respondRenewal(propId, agree) {
  const res = await api(`/property/${propId}/renewal_respond`, 'POST', { agree });
  if (res.error) { toast(res.error, 'error'); return; }
  if (agree) {
    toast('Lease renewed! Tenant staying on.', 'success');
  } else {
    toast('Tenant moved out. Property is now vacant.', 'warning');
  }
  await refreshState();
  renderAll();
  showNextRenewalOffer();
}

function showNextRepair() {
  if (_pendingRepairs.length === 0) { continueFromEvents(); return; }
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
  const rt = _currentRepair?.repair_type;
  _mg = { isRepair: true };
  launchMgByType(selectMgType(rt?.key || ''), null);
}

async function fixRepairContractor(contractorKey) {
  const repair = _currentRepair;
  const res = await api('/repair/fix', 'POST', {
    prop_id: repair.prop_id, repair_key: repair.repair_type.key,
    method: contractorKey,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Repaired! Condition: ${condTier(res.condition)} Tier`, 'success');
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
  const tColor = tierColor(condTier(res.condition));
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">🔧 Repair Done!</div>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:64px;font-weight:900;color:${tColor}">${condTier(res.condition)}</div>
      <div style="font-size:13px;color:var(--text-muted)">new condition</div>
      <div class="mg-score-bar" style="margin:8px 16px"><div class="mg-score-fill" style="width:${res.quality}%"></div></div>
    </div>
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
  toast(`Ignored — condition now ${condTier(res.condition)} Tier`, 'warning');
  await refreshState();
  renderAll();
  showNextRepair();
}

// ── Bank ──────────────────────────────────────────────────────────────────────
// ── Finances Tab ──────────────────────────────────────────────────────────────
function switchFinTab(tab) {
  currentFinTab = tab;
  ['bank', 'stocks', 'taxes'].forEach(t => {
    const el  = document.getElementById('fin-' + t);
    const btn = document.querySelector(`.fin-tab[data-fin="${t}"]`);
    if (el)  el.style.display = t === tab ? '' : 'none';
    if (btn) btn.classList.toggle('active', t === tab);
  });
  if (tab === 'bank')   renderBank();
  if (tab === 'stocks') renderStocks();
}

function renderFinances() {
  switchFinTab(currentFinTab);
}

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
        const termWks  = l.term_weeks  || (l.term_seasons || 0) * 4 || (l.term || 0) * 4;
        const paidWks  = l.weeks_paid  || 0;
        const leftWks  = Math.max(0, termWks - paidWks);
        const leftSeas = Math.ceil(leftWks / 4);
        const pctLeft  = termWks > 0 ? Math.max(5, Math.min(95, (leftWks / termWks) * 100)) : 5;
        const orig     = l.original_amount || (l.weekly_payment || 0) * termWks;
        const paidOff  = orig > 0 ? Math.round(((orig - l.balance) / orig) * 100) : 0;
        return `<div class="card">
          <div class="card-header">
            <div class="card-icon">${l.icon}</div>
            <div style="flex:1">
              <div class="card-title">${l.product}</div>
              <div class="card-subtitle">${fmt(l.weekly_payment || 0)}/wk · ${leftSeas} season${leftSeas !== 1 ? 's' : ''} left</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:16px;font-weight:800;color:var(--negative)">${fmt(Math.ceil(l.balance))}</div>
              <div style="font-size:11px;color:var(--text-muted)">remaining</div>
            </div>
          </div>
          <div class="condition-wrap">
            <div class="condition-top"><span class="condition-lbl">Balance</span><span class="condition-val">${paidOff}% paid off</span></div>
            <div class="condition-bar"><div class="condition-fill cond-poor" style="width:${pctLeft}%"></div></div>
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
            <div style="font-size:11px;color:var(--text-muted)">${p.term_seasons} season term</div>
          </div>
        </div>
        <div class="money-row"><span class="mr-label">Range</span><span class="mr-value">${fmt(p.min)} – ${fmt(p.max)}</span></div>
        <div class="money-row"><span class="mr-label">Example Payment</span><span class="mr-value orange">${fmt(p.sample_payment)}/wk on ${fmt(p.min)}</span></div>
      </div>`).join('')}`;
}

function showLoanModal(productKey) {
  openModal(`<div class="modal-handle"></div><div class="modal-title">Loading…</div>`);
  api('/bank/products').then(data => {
    const p = data.products.find(x => x.key === productKey);
    openModal(`
      <div class="modal-handle"></div>
      <div class="modal-title">${p.icon} ${p.name}</div>
      <div class="modal-subtitle">${p.desc} · ${(p.apr*100).toFixed(0)}% APR · ${p.term_seasons}-season term</div>
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
    <div class="money-row"><span class="mr-label">Weekly Payment</span><span class="mr-value orange">${fmt(res.weekly_payment)}/wk</span></div>
    <div class="money-row"><span class="mr-label">Term</span><span class="mr-value">${res.term_seasons} seasons (${res.term_weeks} weeks)</span></div>
    <div class="money-row"><span class="mr-label">Total Repaid</span><span class="mr-value">${fmt(res.total_repaid)}</span></div>
    <div class="money-row"><span class="mr-label">Total Interest</span><span class="mr-value red">${fmt(res.total_interest)}</span></div>`;
}

async function confirmLoan(productKey) {
  const amount = document.getElementById('loan-amount')?.value;
  if (!amount) return;
  const res = await api('/bank/loan/take', 'POST', { product_key: productKey, amount: parseInt(amount) });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Loan approved! ${fmt(res.loan.weekly_payment)}/wk`, 'success');
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
      <div style="font-size:14px;font-weight:800;margin-bottom:8px">🎁 Creator Codes</div>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px">Got a code? Enter it below for special rewards. Or guess one...</p>
      <div style="display:flex;gap:8px">
        <input id="creator-code-input" type="text" placeholder="Enter code…"
          style="flex:1;padding:10px 12px;font-size:14px;border:1.5px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text-primary);outline:none"
          onkeydown="if(event.key==='Enter') redeemCode()" autocomplete="off" autocorrect="off" spellcheck="false" />
        <button class="btn btn-primary" onclick="redeemCode()">Redeem</button>
      </div>
      <div id="creator-code-msg" style="font-size:13px;margin-top:8px;min-height:18px"></div>
    </div>

    <div class="card" style="margin-top:12px">
      <div style="font-size:14px;font-weight:800;margin-bottom:8px">⚠️ Danger Zone</div>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px">This will permanently erase all progress and start a fresh game.</p>
      <button class="btn btn-danger btn-full" onclick="confirmReset()">🗑 Start New Game</button>
    </div>

    <div class="section-header" style="margin-top:16px"><span class="section-title">📋 Activity Log</span></div>
    <div class="card">
      <div id="log-list"></div>
    </div>`;
  renderLog();
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

async function redeemCode() {
  const input = document.getElementById('creator-code-input');
  const msgEl = document.getElementById('creator-code-msg');
  if (!input || !msgEl) return;
  const code = input.value.trim();
  if (!code) return;
  const res = await api('/redeem_code', 'POST', { code });
  if (res.error) {
    msgEl.textContent = '❌ ' + res.error;
    msgEl.style.color = 'var(--negative)';
  } else {
    await refreshState();
    renderSettings();
    // Set message AFTER renderSettings rebuilds the DOM, otherwise it gets wiped
    const msgElAfter = document.getElementById('creator-code-msg');
    const inputAfter = document.getElementById('creator-code-input');
    const isBadWord  = res.cash_after === 0 && !res.level_up && res.reward_desc?.includes('naughty');
    if (msgElAfter) {
      msgElAfter.textContent = (isBadWord ? '🤬 ' : '✅ ') + res.reward_desc;
      msgElAfter.style.color = isBadWord ? 'var(--negative)' : 'var(--positive)';
    }
    if (inputAfter) inputAfter.value = '';
  }
}

// ── Stocks ────────────────────────────────────────────────────────────────────
let stocksData = null;

async function renderStocks() {
  const el = document.getElementById('stocks-list');
  if (!el) return;
  el.innerHTML = '<div class="empty-state"><div class="empty-icon">💹</div><div class="empty-text">Loading…</div></div>';
  const res = await api('/stocks', 'GET');
  if (res.error) { el.innerHTML = `<div class="card">${res.error}</div>`; return; }
  stocksData = res;
  _renderStocksInner(res);
}

function _renderStocksInner(res) {
  const el  = document.getElementById('stocks-list');
  if (!el) return;
  const lvl = res.level ?? (state ? (state.level || 0) : 0);

  // ── Level lock ──
  if (lvl < 5) {
    el.innerHTML = `<div class="card stocks-locked-card">
      <div class="stocks-lock-icon">🔒</div>
      <div class="stocks-lock-msg">Stocks unlock at <strong>Level 5</strong></div>
      <div class="stocks-lock-sub">Keep growing your property empire to gain access to the stock market.</div>
    </div>`;
    return;
  }

  let html = `<div class="stocks-section-header">
    <span class="stocks-section-icon">📈</span>
    <div>
      <div class="stocks-section-title">Stock Market</div>
      <div class="stocks-section-sub">6 companies · prices update each day</div>
    </div>
  </div>`;
  html += res.instruments.map(i => stockCardHtml(i, res.cash)).join('');
  el.innerHTML = html;
}

function stockCardHtml(inst, cash) {
  const { ticker, name, icon, desc, price, history, shares, avg_cost, gain } = inst;
  const spark   = sparklineSvg(history);
  const trend   = history.length >= 2 ? history[history.length - 1] - history[history.length - 2] : 0;
  const trendCls = trend > 0 ? 'stock-up' : trend < 0 ? 'stock-down' : '';
  const trendIcon = trend > 0 ? '▲' : trend < 0 ? '▼' : '–';
  const trendPct  = history.length >= 2 && history[history.length - 2] !== 0
    ? ((trend / history[history.length - 2]) * 100).toFixed(1) + '%' : '0.0%';
  const priceStr  = price < 10 ? '$' + price.toFixed(4) : '$' + price.toFixed(2);
  const gainStr   = gain >= 0 ? `+$${gain.toFixed(2)}` : `-$${Math.abs(gain).toFixed(2)}`;
  const gainCls   = gain > 0 ? 'positive' : gain < 0 ? 'negative' : '';
  const canBuy    = cash >= price;

  return `<div class="card stock-card">
    <div class="stock-card-top">
      <div class="stock-icon-wrap">${icon}</div>
      <div class="stock-info">
        <div class="stock-name">${name} <span class="stock-ticker">${ticker}</span></div>
        <div class="stock-desc">${desc}</div>
      </div>
      <div class="stock-price-wrap">
        <div class="stock-price">${priceStr}</div>
        <div class="stock-trend ${trendCls}">${trendIcon} ${trendPct}</div>
      </div>
    </div>
    <div class="stock-sparkline">${spark}</div>
    ${shares > 0 ? `<div class="stock-holding">
      <span>📦 ${shares} share${shares !== 1 ? 's' : ''}</span>
      <span>Avg cost $${avg_cost.toFixed(2)}</span>
      <span class="${gainCls}">${gainStr}</span>
    </div>` : ''}
    <div class="stock-actions">
      <button class="btn btn-primary btn-sm" onclick="openStockBuyModal('${ticker}')" ${canBuy ? '' : 'disabled'}>Buy</button>
      ${shares > 0 ? `<button class="btn btn-ghost btn-sm" onclick="openStockSellModal('${ticker}')">Sell</button>` : ''}
    </div>
  </div>`;
}

function sparklineSvg(history) {
  if (!history || history.length < 2) return '';
  const w = 260, h = 40, pad = 2;
  const vals = history.slice(-20);
  const min  = Math.min(...vals);
  const max  = Math.max(...vals);
  const range = max - min || 1;
  const pts   = vals.map((v, i) => {
    const x = pad + (i / (vals.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const trend = vals[vals.length - 1] >= vals[0];
  const color = trend ? '#2E7D32' : '#C62828';
  return `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:40px">
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
  </svg>`;
}

function openStockBuyModal(ticker) {
  if (!stocksData) return;
  const inst = stocksData.instruments.find(i => i.ticker === ticker);
  if (!inst) return;
  const price    = inst.price;
  const maxShares = Math.floor(stocksData.cash / price);
  const priceStr  = price < 10 ? price.toFixed(4) : price.toFixed(2);

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${inst.icon} Buy ${inst.name}</div>
    <div class="modal-subtitle">${inst.ticker} · $${priceStr} per share</div>
    <div style="margin:16px 0">
      <label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">Shares to buy</label>
      <input id="buy-shares-input" type="number" min="1" max="${maxShares}" value="1"
        style="width:100%;padding:10px 12px;font-size:16px;border:1.5px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text-primary);box-sizing:border-box;outline:none"
        oninput="updateBuyCost(${price})" />
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Max: ${maxShares} share${maxShares !== 1 ? 's' : ''} (${fmt(stocksData.cash)} available)</div>
    </div>
    <div id="buy-cost-display" style="font-size:15px;font-weight:800;margin-bottom:16px;color:var(--text-primary)">
      Total cost: <span id="buy-cost-value">${fmt(price)}</span>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="confirmBuyStock('${ticker}', ${price})">Buy</button>
    </div>`);
}

function updateBuyCost(price) {
  const input = document.getElementById('buy-shares-input');
  const disp  = document.getElementById('buy-cost-value');
  if (!input || !disp) return;
  const shares = Math.max(0, parseInt(input.value) || 0);
  const cost   = shares * price;
  disp.textContent = cost < 10 ? '$' + cost.toFixed(4) : fmt(Math.round(cost));
}

async function confirmBuyStock(ticker, price) {
  const input = document.getElementById('buy-shares-input');
  const shares = parseInt(input?.value) || 0;
  if (shares < 1) { toast('Enter at least 1 share', 'error'); return; }
  const res = await api('/stocks/buy', 'POST', { ticker, shares });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal();
  state.cash = res.cash;
  updateHeader();
  // refresh stocks data
  const fresh = await api('/stocks', 'GET');
  stocksData = fresh;
  _renderStocksInner(fresh);
  toast(`Bought ${shares}x ${ticker}!`, 'success');
}

function openStockSellModal(ticker) {
  if (!stocksData) return;
  const inst = stocksData.instruments.find(i => i.ticker === ticker);
  if (!inst) return;
  const price   = inst.price;
  const priceStr = price < 10 ? price.toFixed(4) : price.toFixed(2);
  const maxSell = inst.shares;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${inst.icon} Sell ${inst.name}</div>
    <div class="modal-subtitle">${inst.ticker} · $${priceStr} per share · You own ${maxSell}</div>
    <div style="margin:16px 0">
      <label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">Shares to sell</label>
      <input id="sell-shares-input" type="number" min="1" max="${maxSell}" value="${maxSell}"
        style="width:100%;padding:10px 12px;font-size:16px;border:1.5px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text-primary);box-sizing:border-box;outline:none"
        oninput="updateSellProceeds(${price}, ${inst.avg_cost})" />
    </div>
    <div id="sell-proceeds-display" style="font-size:14px;font-weight:700;margin-bottom:16px">
      <div>Proceeds: <span id="sell-proceeds-value" style="color:var(--text-primary)">${fmt(Math.round(maxSell * price))}</span></div>
      <div id="sell-profit-line" style="font-size:13px;margin-top:2px"></div>
    </div>
    <div class="btn-row">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="confirmSellStock('${ticker}')">Sell</button>
    </div>`);
  updateSellProceeds(price, inst.avg_cost);
}

function updateSellProceeds(price, avgCost) {
  const input   = document.getElementById('sell-shares-input');
  const procEl  = document.getElementById('sell-proceeds-value');
  const profEl  = document.getElementById('sell-profit-line');
  if (!input || !procEl) return;
  const shares   = Math.max(0, parseInt(input.value) || 0);
  const proceeds = shares * price;
  const profit   = proceeds - avgCost * shares;
  procEl.textContent = proceeds < 10 ? '$' + proceeds.toFixed(4) : fmt(Math.round(proceeds));
  if (profEl) {
    const sign = profit >= 0 ? '+' : '';
    profEl.textContent = `P&L: ${sign}${profit < 10 && profit > -10 ? '$' + profit.toFixed(4) : fmt(Math.round(profit))}`;
    profEl.style.color = profit >= 0 ? 'var(--positive)' : 'var(--negative)';
  }
}

async function confirmSellStock(ticker) {
  const input  = document.getElementById('sell-shares-input');
  const shares = parseInt(input?.value) || 0;
  if (shares < 1) { toast('Enter at least 1 share', 'error'); return; }
  const res = await api('/stocks/sell', 'POST', { ticker, shares });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal();
  state.cash = res.cash;
  updateHeader();
  const fresh = await api('/stocks', 'GET');
  stocksData = fresh;
  _renderStocksInner(fresh);
  const profitStr = res.profit >= 0 ? `+${fmt(Math.round(res.profit))}` : fmt(Math.round(res.profit));
  toast(`Sold ${shares}x ${ticker} · P&L ${profitStr}`, res.profit >= 0 ? 'success' : '');
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
  const content = document.getElementById('modal-content');
  content.innerHTML = html;
  document.getElementById('modal-overlay').classList.add('open');
  const handle = content.querySelector('.modal-handle');
  if (handle) handle.addEventListener('click', closeModal, { once: true });
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
  if (_mg.locked) return;   // block dismiss during active mini-game
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

function condTier(c) {
  // thresholds scaled to 250-point system
  if (c >= 225) return 'S+';
  if (c >= 188) return 'S';
  if (c >= 150) return 'A';
  if (c >= 113) return 'B';
  if (c >= 75)  return 'C';
  if (c >= 38)  return 'D';
  return 'F';
}

function condPct(c) { return Math.round((c / MAX_CONDITION) * 100); }

function condClass(c) {
  if (c >= 188) return 'cond-great';
  if (c >= 150) return 'cond-great';
  if (c >= 113) return 'cond-good';
  if (c >= 75)  return 'cond-fair';
  return 'cond-poor';
}

const TIER_COLORS = { 'S+': '#7B1FA2', 'S': '#1565C0', 'A': '#2E7D32', 'B': '#33691E', 'C': '#F57F17', 'D': '#E65100', 'F': '#B71C1C' };
function tierColor(t) { return TIER_COLORS[t] || 'var(--text)'; }

function starsHtml(chance) {
  const full  = Math.round(chance * 5);
  const empty = 5 - full;
  return '★'.repeat(full) + '☆'.repeat(empty);
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
