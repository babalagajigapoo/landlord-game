// ── Pixel Art Icons ───────────────────────────────────────────────────────────
const PIXEL_ICONS = {
  // Property types
  '\u{1F3DA}\uFE0F': 'house-bungalow',   // 🏚️
  '\u{1F3E0}':         'house-ranch',       // 🏠
  '\u{1F3DB}\uFE0F': 'house-colonial',    // 🏛️
  '\u{1F3D9}\uFE0F': 'house-townhouse',   // 🏙️
  '\u{1F3E2}':         'house-condo',       // 🏢
  '\u{1F3D8}\uFE0F': 'house-duplex',      // 🏘️
  '\u{1F3F0}':         'house-mansion',     // 🏰
  '\u{1F3E1}':         'home-bungalow',     // 🏡
  // Seasons
  '\u{1F338}':         'season-spring',     // 🌸
  '\u2600\uFE0F':     'season-summer',     // ☀️
  '\u{1F342}':         'season-fall',       // 🍂
  '\u2744\uFE0F':     'season-winter',     // ❄️
  // Repairs
  '\u{1F527}':         'repair-plumbing',   // 🔧
  '\u26A1':            'repair-electrical', // ⚡
  '\u{1F4E6}':         'repair-appliance',  // 📦
  '\u{1F41B}':         'repair-pest',       // 🐛
  '\u{1F321}\uFE0F': 'repair-hvac',       // 🌡️
  // Upgrades
  '\u{1F33F}':         'upgrade-landscaping',// 🌿
  '\u{1F3A8}':         'upgrade-paint',     // 🎨
  '\u{1FAB5}':         'upgrade-flooring',  // 🪵
  '\u{1FA9F}':         'upgrade-windows',   // 🪟
  '\u{1F6BF}':         'upgrade-bathrooms', // 🚿
  '\u{1F373}':         'upgrade-kitchen',   // 🍳
  // Premium upgrades
  '\u{1F4F1}':         'premium-smarthome', // 📱
  '\u{1F6C1}':         'premium-hottub',    // 🛁
  '\u{1F697}':         'premium-garage',    // 🚗
  '\u{1F3D7}\uFE0F': 'premium-basement',  // 🏗️
  '\u{1F3CA}':         'premium-pool',      // 🏊
  // Neighborhoods
  '\u{1F332}':         'hood-northside',    // 🌲
  '\u{1F30A}':         'hood-riverside',    // 🌊
  '\u{1F306}':         'hood-newbay',       // 🌆
  // Tenant types
  '\u{1F3CB}\uFE0F': 'tenant-gym',        // 🏋️
  '\u{1F3B8}':         'tenant-musician',   // 🎸
  '\u{1F468}\u200D\u{1F373}': 'tenant-chef',      // 👨‍🍳
  '\u{1F468}\u200D\u{1F469}\u200D\u{1F467}\u200D\u{1F466}': 'tenant-family', // 👨‍👩‍👧‍👦
  '\u{1F476}':         'tenant-baby',       // 👶
  '\u{1F474}':         'tenant-elderly',    // 👴
  '\u{1F9D1}\u200D\u{1F467}': 'tenant-single-parent', // 🧑‍👧
  '\u{1F464}':         'tenant-generic',    // 👤
  '\uD83D\uDC64':     'tenant-generic',    // 👤 alt encoding
  // Loans
  '\u{1F4B5}':         'loan-cash',         // 💵
  '\u{1F91D}':         'loan-friend',       // 🤝
  '\u{1F3E6}':         'loan-bank',         // 🏦
  '\u{1F4BC}':         'nav-business',      // 💼
  // Player homes
  '\u{1F6CB}\uFE0F': 'home-rental',       // 🛋️
  // Stats / nav
  '\u{1F4B0}':         'nav-finances',      // 💰
  '\u{1F4CA}':         'nav-dashboard',     // 📊
  '\u{1F3EA}':         'nav-market',        // 🏪
  '\u{1F4B9}':         'stat-stocks',       // 💹
  '\u{1F4C8}':         'stat-networth',     // 📈
  '\u2699\uFE0F':     'settings-gear',     // ⚙️
  // Tools
  '\u{1F6E0}\uFE0F': 'diy-tools',         // 🛠️
  // Special tenants
  '⭐':             'stat-star',         // ⭐
  '😠':             'face-angry',        // 😠
  '⭐':             'stat-star',         // ⭐
  '😠':             'face-angry',        // 😠
  '🔱':        'special-phil',      // 🔱
  '🎩':        'special-goldbergs', // 🎩
  // ── Added in third round ─────────────────────────────────────────────────
  '💸': 'ui-money',
  '🔨': 'tool-hammer',
  '🗓️': 'ui-calendar',
  '📅': 'ui-calendar',
  '🔒': 'ui-lock',
  '🧰': 'tool-box',
  '🚨': 'ui-siren',
  '🧾': 'ui-receipt',
  '📋': 'ui-clipboard',
  '📄': 'ui-clipboard',
  '🔄': 'ui-refresh',
  '✅': 'ui-check',
  '❌': 'ui-cross',
  '👋': 'ui-wave',
  '💬': 'ui-chat',
  '⏳': 'ui-hourglass',
  '🧱': 'ui-brick',
  '🪚': 'ui-saw',
  '🪜': 'ui-ladder',
  '💧': 'ui-water',
  '📐': 'ui-level',
  '🪣': 'ui-bucket',
  '🖌️': 'ui-roller',
  '⚖️': 'ui-gavel',
  '🔑': 'ui-key',
  '🗑': 'ui-trash',
  '🏆': 'stat-star',
  '📊': 'nav-dashboard',
  '💹': 'stat-stocks',
  '📈': 'stat-networth',
  '🦰': 'ui-water',
  '🍴': 'upgrade-kitchen',
  '🚿': 'upgrade-bathrooms',
  '🧱': 'ui-brick',
  '☕': 'store-coffee',
  '🛏️': 'store-bed',
  '🛒': 'ui-cart',
  '📚': 'ui-books',
};

function pxIcon(emoji, size) {
  if (!emoji) return '';
  size = size || 28;
  let name = PIXEL_ICONS[emoji];
  if (!name) {
    // Try stripping variation selectors (U+FE0F / U+FE0E) and zero-width joiners
    const stripped = emoji.replace(/[︎️‍]/g, '');
    name = PIXEL_ICONS[stripped];
  }
  if (!name) return emoji;
  return '<img src="/static/icons/' + name + '.svg" width="' + size + '" height="' + size + '" style="image-rendering:pixelated;vertical-align:middle;display:inline-block" alt="' + emoji + '">';
}

// ── State ─────────────────────────────────────────────────────────────────────
let state           = null;

function starterSquatterActive() {
  return !!(state?.properties?.find(p => p.squatter?.starter));
}
function firstSaleDone() {
  return (state?.level || 0) >= 1;
}
let marketListings  = [];
let marketHoodOpen  = {};   // tracks which hood sections are expanded; undefined = open
let currentFinTab   = 'bank'; // active sub-tab inside Finances
let currentPage     = 'dashboard';
let pendingUpgrade  = null;
let _applicants     = [];
let _fairRent       = 0;
let _selectedTier   = 2;       // default Average
let _pendingConfirm = null;

// ── Neighborhood tier map ─────────────────────────────────────────────────────
const HOOD_TIERS = {
  Midtown: 'budget', Northside: 'budget',
  Westwood: 'mid',
  Riverside: 'premium', Newbay: 'premium',
};

let _prevCash = null;   // tracks last known cash for float animation

// ── Mini-game state ───────────────────────────────────────────────────────────
let _mg             = {};   // active mini-game state
let _modalLocked          = false; // true while event flow is in progress (repairs/morale/tax/etc.)
let _propDetailId         = null;  // id of the property currently open in detail modal
let _inPropSubModal       = false; // true when a sub-modal inside a property detail is open
let _propHoodOpen         = {};    // { 'Maplewood Heights': false } — collapsed neighborhoods
let _propHoodTab          = {};    // { 'Maplewood Heights': 'vacant' } — active sub-tab per hood
let _pendingLevelUp       = null;  // new level number waiting to be shown after all other modals
let _pendingRepairs       = [];   // repair events queued after advancing
let _currentRepair        = null; // repair being handled right now
let _pendingJob           = null; // side job being played
let _pendingSquatter      = null; // squatter event queued after repairs
let _pendingMoraleEvents  = [];   // morale-choice events queued after repairs
let _pendingRenewalOffers = [];   // lease renewal offers queued after advancing
let _pendingTaxEvent      = null; // tax-due event queued after advancing

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
  { key: 'grandmas_basement', name: "Grandma's Basement", icon: '🛋️', cost:       0, max_energy:  8, recharge:  1, unlock_level:  0, desc: "Grandma's got a cot, a leaky fridge, and opinions about your life choices. Free rent — if you can survive the casserole." },
  { key: 'small_apt',         name: 'Small Apartment',    icon: '🏠',  cost:   80000, max_energy: 10, recharge:  3, unlock_level:  1, desc: 'Thin walls, no dishwasher, and a neighbor who practices drums at midnight. Still yours.' },
  { key: 'condo',             name: 'Condo',              icon: '🏢',  cost:  150000, max_energy: 12, recharge:  5, unlock_level:  3, desc: 'An HOA fee and a parking sticker — welcome to adulthood.' },
  { key: 'small_home',        name: 'Small Home',         icon: '🏡',  cost:  250000, max_energy: 15, recharge:  7, unlock_level:  5, desc: 'A real yard. A real mortgage. A real lawn to mow at 7am on a Saturday.' },
  { key: 'suburban_home',     name: 'Suburban Home',      icon: '🏘️',  cost:  400000, max_energy: 18, recharge: 11, unlock_level:  7, desc: 'Cul-de-sac living with a two-car garage and a wave-hello relationship with the neighbors.' },
  { key: 'luxury_villa',      name: 'Luxury Villa',       icon: '🏛️',  cost:  750000, max_energy: 24, recharge: 19, unlock_level:  9, desc: 'Heated floors, a wine cellar, and someone else mows the lawn.' },
  { key: 'mansion',           name: 'Mansion',            icon: '🏰',  cost: 1500000, max_energy: 58, recharge: 60, unlock_level: 12, desc: "You have a butler named Gerald and a room you've never entered. Peak existence." },
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

// ── Forced Reset (one-time tax man wipe) ──────────────────────────────────────
const RESET_FLAG = 'landlord_reset_taxman_v1';

function checkForcedReset() {
  if (localStorage.getItem(RESET_FLAG)) return false;  // already wiped, skip
  if (!localStorage.getItem('landlord_save')) return false;  // brand new player, nothing to wipe
  return true;
}

function showForcedResetScreen() {
  const overlay = document.createElement('div');
  overlay.id = 'taxman-overlay';
  overlay.style.cssText = `
    position:fixed;inset:0;z-index:99999;
    background:linear-gradient(160deg,#1a0a00,#2d1200,#0a0a0a);
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:24px;text-align:center;
  `;
  overlay.innerHTML = `
    <div style="margin-bottom:16px;animation:taxShake 0.6s infinite">${pxIcon('🏛️', 72)}</div>
    <div style="font-size:22px;font-weight:900;color:#FFD700;margin-bottom:12px;letter-spacing:1px">
      NOTICE FROM THE IRS
    </div>
    <div style="max-width:420px;font-size:14px;line-height:1.7;color:#ddd;margin-bottom:24px">
      The tax man came by and noticed you haven't been paying up.<br><br>
      Unfortunately, <strong style="color:#FFD700">Uncle Sam doesn't care</strong> that he's never heard of you,
      that your LLC is definitely legit, or that you've been
      "reinvesting profits" into a very serious vending machine business.<br><br>
      <strong style="color:#FF6B6B">Your entire real estate empire has been seized.<br>
      Every property. Every dollar. Every tenant.</strong><br>
      Even Phil.<br><br>
      <span style="font-size:12px;color:#aaa">
        The government thanks you for your service.<br>
        Please start over and try to be less suspicious this time.
      </span>
    </div>
    <button id="taxman-btn" style="
      background:#FFD700;color:#1a0a00;border:none;border-radius:12px;
      padding:16px 32px;font-size:16px;font-weight:900;cursor:pointer;
      letter-spacing:.5px;box-shadow:0 4px 20px rgba(255,215,0,0.4);
    ">
      🏳️ Accept Defeat &amp; Start Fresh
    </button>
    <div style="font-size:11px;color:#555;margin-top:16px">
      You cannot appeal this decision.
    </div>
  `;
  document.body.appendChild(overlay);

  document.getElementById('taxman-btn').addEventListener('click', () => {
    clearLocalState();
    localStorage.setItem(RESET_FLAG, '1');
    overlay.remove();
    init();
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  if (checkForcedReset()) {
    showForcedResetScreen();
    return;
  }
  setupNav();
  await refreshState();
  if (!state.intro_seen) {
    showIntroScreen();
    return;
  }
  await loadMarket();
  renderAll();
}

function showIntroScreen() {
  if (!document.getElementById('intro-styles')) {
    const s = document.createElement('style');
    s.id = 'intro-styles';
    s.textContent = `
      @keyframes introBtnReveal {
        from { opacity:0; transform:translate(-50%,-50%) scale(0.9); }
        to   { opacity:1; transform:translate(-50%,-50%) scale(1);   }
      }
      @keyframes introBtnPulse {
        0%,100% { opacity:1;    transform:translate(-50%,-50%) scale(1);    }
        50%     { opacity:0.25; transform:translate(-50%,-50%) scale(0.96); }
      }
      #intro-btn.visible {
        animation: introBtnReveal 1.2s ease forwards,
                   introBtnPulse  2.4s ease-in-out 1.2s infinite;
        pointer-events: auto !important;
      }
    `;
    document.head.appendChild(s);
  }

  const overlay = document.createElement('div');
  overlay.id = 'intro-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;height:100svh;height:-webkit-fill-available;z-index:10000;background:#0d0d0d;overflow:hidden;';
  overlay.innerHTML = `
    <div style="height:100%;max-width:480px;margin:0 auto;padding:28px 24px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;">

      <div style="text-align:center">
        <div style="line-height:1;margin-bottom:6px">${pxIcon('🏚️', 40)}</div>
        <div style="font-family:'Rubik Dirt',cursive;font-size:40px;color:#b8a898;line-height:1;letter-spacing:0.01em">SlumLord</div>
        <div style="font-family:'Great Vibes',cursive;font-size:30px;color:#e8ddd0;line-height:1.1">Special</div>
        <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.16em;color:#444;margin-top:5px">Work In Progress</div>
      </div>

      <p style="font-size:11px;color:#444;font-style:italic;text-align:center;margin:0">tap tap tap</p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"Hey. Hey! Wake up."</strong>
      </p>

      <p style="font-size:12px;color:#666;line-height:1.55;margin:0">
        Grandma's at the top of the basement stairs, dish towel over her shoulder, already judging you.
      </p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"You can stay down here as long as you like. This is your home too."</strong> A pause. <strong style="color:#fff">"Lord knows you don't have another one."</strong>
      </p>

      <p style="font-size:12px;color:#666;line-height:1.55;margin:0">
        She reaches into her apron and pulls out a wrinkled envelope.
      </p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"I remember when you were little — you'd point at those beat-up apartments on Elm Street and say you were gonna own all of them someday and charge people too much to live there. You were seven. I was worried. But here we are."</strong>
      </p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"I'm leaving you the deed to my old place in Midtown. There's a squatter in it. Police went by twice — useless. You'll have to handle that yourself."</strong>
      </p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"Get them out and the house is yours. Start that little slumlord empire you always dreamed about."</strong> A slow shake of the head. <strong style="color:#fff">"Still not sure where I went wrong."</strong>
      </p>

      <p style="font-size:12px;color:#666;line-height:1.55;margin:0">She heads back upstairs.</p>

      <p style="font-size:13px;color:#e8e8e8;line-height:1.55;margin:0">
        <strong style="color:#fff">"My casserole's almost ready. Come up when you're done feeling sorry for yourself."</strong>
      </p>

    </div>

    <button id="intro-btn" onclick="dismissIntro()"
      style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
             opacity:0;pointer-events:none;
             padding:20px 56px;background:var(--primary);color:#fff;
             border:none;border-radius:16px;font-size:19px;font-weight:800;
             cursor:pointer;white-space:nowrap;letter-spacing:0.03em;
             box-shadow:0 8px 36px rgba(0,0,0,0.8);
             -webkit-tap-highlight-color:transparent">
      I'm Ready
    </button>`;

  document.body.appendChild(overlay);

  setTimeout(() => {
    const btn = document.getElementById('intro-btn');
    if (btn) btn.classList.add('visible');
  }, 10000);
}

async function dismissIntro() {
  await api('/intro/seen', 'POST');
  const overlay = document.getElementById('intro-overlay');
  if (overlay) overlay.remove();
  await loadMarket();
  renderAll();
}

async function refreshState() {
  const prevLevel = state ? (state.level ?? 0) : null;
  state = await api('/state');
  updateHeader();
  if (prevLevel !== null && state.level > prevLevel) {
    _pendingLevelUp = state.level;
    await loadMarket();
    renderMarket();
    // Show immediately only if no modal is currently open (non-advance flow)
    if (!document.getElementById('modal-overlay').classList.contains('open')) {
      const lvl   = _pendingLevelUp;
      _pendingLevelUp = null;
      showLevelUpModal(lvl);
    }
    // Otherwise: continueFromEvents or closeModal will pick it up
  }
}

async function loadMarket() {
  const data     = await api('/market');
  marketListings = data.listings;
}

// ── Header ────────────────────────────────────────────────────────────────────
function updateHeader() {
  const cashEl  = document.getElementById('hdr-cash');
  const newCash = state.cash;
  if (_prevCash !== null && _prevCash !== newCash) {
    animateCashChange(newCash - _prevCash);
    animateCounter(cashEl, _prevCash, newCash);
  } else {
    cashEl.textContent = fmt(newCash);
  }
  _prevCash = newCash;
  const energy = state.energy ?? DAILY_ENERGY;
  const maxE   = state.max_energy || DAILY_ENERGY;
  const energyEl = document.getElementById('hdr-energy');
  energyEl.textContent = `⚡ ${energy} / ${maxE}`;
  energyEl.style.color = energy === 0 ? 'var(--negative)' : energy <= 3 ? 'var(--warning)' : 'var(--positive)';
  const s = getSeasonInfo(state.day);
  document.getElementById('hdr-day').innerHTML  = `${pxIcon(s.icon, 18)} ${s.name} · Day ${s.seasonDay}`;
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

function animateCashChange(delta) {
  if (!delta || Math.abs(delta) < 1) return;
  const ref = document.getElementById('hdr-cash');
  if (!ref) return;
  const rect = ref.getBoundingClientRect();
  const el   = document.createElement('div');
  el.className   = 'cash-float';
  el.textContent = (delta > 0 ? '+' : '') + fmt(Math.round(delta));
  el.style.color = delta > 0 ? '#81C784' : '#EF9A9A';
  el.style.left  = rect.left + 'px';
  el.style.top   = (rect.top + rect.height / 2) + 'px';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1100);
}

function animateCounter(el, fromVal, toVal, duration = 550) {
  if (!el || fromVal === toVal) return;
  const startTime = performance.now();
  const step = (now) => {
    const t     = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = '$' + Math.round(fromVal + (toVal - fromVal) * eased).toLocaleString();
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = fmt(toVal);
  };
  requestAnimationFrame(step);
}

// ── Level-up ──────────────────────────────────────────────────────────────────
const LEVEL_UNLOCKS = {
  1:  { joke: "I've sold Grandma's old house. I think I'm ready to take these slums over.",
        unlocks: ["🏪 The Market is open — you can now buy properties", "🔨 Renovations unlocked — hire contractors on any property", "🧰 DIY unlocked for Landscaping & Interior Paint", "🏠 Small Apartment available in Personal → Homes ($80,000)", "🌆 Midtown neighborhood open"] },
  2:  { joke: "Two whole levels in. Still no idea what you're doing. Confidence unaffected.",
        unlocks: ["🌆 Northside neighborhood unlocked in the Market", "📚 Flooring Installation Class available in Personal → Skill Classes (⚡10)", "📚 Window Installation Class available in Personal → Skill Classes (⚡10)"] },
  3:  { joke: "An HOA fee and a parking sticker. Congratulations, you're basically an adult.",
        unlocks: ["🌆 Westwood neighborhood unlocked in the Market", "🏢 Condo home available in Personal → Homes ($150,000)", "📚 Remodeling Class available in Personal → Skill Classes (⚡12)", "🏪 Business tab unlocked — buy your first Vending Machine ($1,200+)", "🛒 CostPro Store unlocked — stock up on vending supplies"] },
  4:  { joke: "I'm ready to patch more roofs than I have friends. This is fine.",
        unlocks: ["🌊 Riverside neighborhood unlocked in the Market", "📚 HVAC System Course available in Personal → Skill Classes (⚡14)", "📚 Roof Replacement Course available in Personal → Skill Classes (⚡14)"] },
  5:  { joke: "Premium upgrades unlocked. Because apparently your tenants deserve slightly nicer things.",
        unlocks: ["🌆 Newbay neighborhood unlocked in the Market", "🏡 Small Home available in Personal → Homes ($250,000)", "⭐ Premium Upgrades unlocked on all properties", "🧺 Dirty Money Laundromat unlocked in Business tab ($250,000)"] },
  6:  { joke: "No new shiny things this level. Just respect. And money. Mostly money.",
        unlocks: ["📈 Pure progression — keep building your empire"] },
  7:  { joke: "A cul-de-sac and a two-car garage. You're practically a suburb now.",
        unlocks: ["🏘️ Suburban Home available in Personal → Homes ($400,000)"] },
  8:  { joke: "The bank calls you by your first name. That's either a great sign or a sign you owe them money.",
        unlocks: ["📈 Keep scaling — the premium districts are yours to dominate"] },
  9:  { joke: "Heated floors. A wine cellar. Someone else mows the lawn. You made it.",
        unlocks: ["🏛️ Luxury Villa available in Personal → Homes ($750,000)"] },
  10: { joke: "Double digits. Gerald can already smell the ambition from here.",
        unlocks: ["📈 Endgame territory — maximize every income stream", "🚗 Speedy Suds Car Wash unlocked in Business tab"] },
  11: { joke: "The Mansion is one level away. Try not to trip over your own net worth.",
        unlocks: ["📈 Almost there — one more push for the Mansion"] },
  12: { joke: "There's a room in the Mansion you've never entered. Gerald has been living there.",
        unlocks: ["🏰 Mansion available in Personal → Homes ($1,500,000)"] },
  13: { joke: "Thirteen. The city is basically yours at this point. Don't tell the tenants.",
        unlocks: ["📈 The empire is yours — squeeze every dollar from it"] },
  14: { joke: "Maximum level. You built an empire from a basement casserole. Grandma is complicated about it.",
        unlocks: ["🏆 Max level reached — the empire is complete"] },
};

function showLevelUpModal(newLevel) {
  const data    = LEVEL_UNLOCKS[newLevel] || { joke: "Something unlocked. Probably important.", unlocks: [] };
  const listHtml = data.unlocks.map(u => `
    <div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">
      <span style="font-size:16px;line-height:1.4">${u.split(' ')[0]}</span>
      <span style="font-size:13px;color:var(--text)">${u.split(' ').slice(1).join(' ')}</span>
    </div>`).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="text-align:center;padding:16px 0 8px">
      <div style="line-height:1">${pxIcon('⭐', 52)}</div>
      <div style="font-size:24px;font-weight:900;margin-top:8px;color:var(--primary)">Level ${newLevel}!</div>
      <div style="font-size:13px;color:var(--text-muted);margin-top:6px;font-style:italic">${data.joke}</div>
    </div>
    <div style="margin:12px 0 4px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted)">What's unlocked</div>
    <div style="border-top:1px solid var(--border)">${listHtml}</div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Let's Go! 🚀</button>`);
}

function showLevelRoadmapModal() {
  if (!state) return;
  const currentLvl = state.level ?? 0;

  const rows = Object.entries(LEVEL_UNLOCKS).map(([lvlStr, data]) => {
    const lvl      = parseInt(lvlStr);
    const past     = lvl < currentLvl;
    const current  = lvl === currentLvl;
    const future   = lvl > currentLvl;

    const badgeBg    = past    ? 'var(--positive)'  : current ? 'var(--primary)' : 'var(--surface)';
    const badgeColor = past    ? '#fff'              : current ? '#fff'           : 'var(--text-muted)';
    const badgeBorder= future  ? '2px solid var(--border)' : 'none';
    const rowBg      = current ? 'var(--primary-ghost, rgba(99,102,241,0.07))' : 'transparent';
    const rowBorder  = current ? '1px solid var(--primary)' : '1px solid var(--border)';
    const textColor  = future  ? 'var(--text-muted)' : 'var(--text)';

    const statusIcon = past ? '✅' : current ? '▶' : '🔒';

    const unlockItems = data.unlocks.map(u => {
      const icon = u.split(' ')[0];
      const text = u.split(' ').slice(1).join(' ');
      return `<div style="display:flex;align-items:flex-start;gap:8px;padding:4px 0;opacity:${future ? '0.55' : '1'}">
        <span style="font-size:14px;flex-shrink:0;line-height:1.5">${icon}</span>
        <span style="font-size:12px;color:${textColor};line-height:1.5">${text}</span>
      </div>`;
    }).join('');

    return `
      <div style="border:${rowBorder};border-radius:10px;padding:12px 14px;margin-bottom:8px;background:${rowBg}">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:${data.unlocks.length ? '8px' : '0'}">
          <div style="width:32px;height:32px;border-radius:50%;background:${badgeBg};border:${badgeBorder};display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:${badgeColor};flex-shrink:0">${lvl}</div>
          <div style="flex:1">
            <div style="font-size:13px;font-weight:800;color:${current ? 'var(--primary)' : textColor}">
              ${current ? '▶ Current Level' : past ? `Level ${lvl} — Completed` : `Level ${lvl}`}
            </div>
            ${current ? `<div style="font-size:11px;color:var(--text-muted);margin-top:1px;font-style:italic">${data.joke}</div>` : ''}
          </div>
          <span style="font-size:16px">${statusIcon}</span>
        </div>
        ${data.unlocks.length ? `<div style="padding-left:42px">${unlockItems}</div>` : ''}
      </div>`;
  }).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:10px;padding:12px 0 16px">
      <div style="font-size:22px;font-weight:900;color:var(--primary)">${pxIcon('⭐',24)} Level Roadmap</div>
      <div style="margin-left:auto;font-size:12px;color:var(--text-muted)">You are Level ${currentLvl}</div>
    </div>
    <div style="max-height:60vh;overflow-y:auto;padding-right:2px">${rows}</div>
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got it</button>`);
}

// ── Navigation ────────────────────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => navTo(btn.dataset.page));
  });
  slideNavIndicator('dashboard');
}

function slideNavIndicator(page) {
  const indicator = document.getElementById('nav-indicator');
  if (!indicator) return;
  const btns = Array.from(document.querySelectorAll('.nav-btn'));
  const idx  = btns.findIndex(b => b.dataset.page === page);
  if (idx >= 0) {
    indicator.style.opacity   = '1';
    indicator.style.transform = `translateX(${idx * 100}%)`;
  } else {
    indicator.style.opacity = '0';
  }
}

function navTo(page) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const pageEl = document.getElementById('page-' + page);
  const btnEl  = document.querySelector(`.nav-btn[data-page="${page}"]`);
  if (pageEl) pageEl.classList.add('active');
  if (btnEl)  btnEl.classList.add('active');
  slideNavIndicator(page);
  if (page === 'finances') renderFinances();
  if (page === 'settings') renderSettings();
  if (page === 'personal') renderPersonal();
  if (page === 'business') renderBusiness();
  if (page === 'store')    renderStore();
}

// ── Render All ────────────────────────────────────────────────────────────────
function renderAll() {
  renderDashboard();
  renderMarket();
  renderProperties();
  if (currentPage === 'settings')  renderSettings();
  if (currentPage === 'finances')  renderFinances();
  if (currentPage === 'personal')  renderPersonal();
  if (currentPage === 'business')  renderBusiness();
  if (currentPage === 'store')     renderStore();
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
        <span style="font-size:32px">${pxIcon(s.icon)}</span>
        <div>
          <div style="font-size:16px;font-weight:800">${s.name} — Year ${s.year}</div>
          <div style="font-size:12px;color:var(--text-muted)">Day ${s.seasonDay} of ${DAYS_PER_SEASON} · Overall Day ${state.day}</div>
        </div>
      </div>
      <div class="condition-bar" style="margin-top:8px">
        <div class="condition-fill cond-great" style="width:${(s.seasonDay / DAYS_PER_SEASON) * 100}%"></div>
      </div>`;
  }

  // Advance button lock state
  const advBtn = document.querySelector('.next-month-btn');
  if (advBtn) {
    const locked = starterSquatterActive();
    advBtn.disabled = locked;
    advBtn.style.opacity = locked ? '0.45' : '';
    let note = document.getElementById('squatter-advance-note');
    if (locked && !note) {
      note = document.createElement('div');
      note.id = 'squatter-advance-note';
      note.style.cssText = 'text-align:center;font-size:12px;color:var(--negative);margin-top:6px;font-weight:700';
      note.textContent = '🚨 Get rid of the squatter before advancing time';
      advBtn.insertAdjacentElement('afterend', note);
    } else if (!locked && note) {
      note.remove();
    }
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
      <div class="empty-icon">${pxIcon('🔒',48)}</div>
      <div class="empty-text">Market Locked</div>
      <div class="empty-sub">Sell your starter Bungalow in Midtown to reach Level 1 and unlock buying.</div>
    </div>`;
    return;
  }
  if (marketListings.length === 0) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">${pxIcon('🏚️', 48)}</div><div class="empty-text">No listings right now</div><div class="empty-sub">Advance the day to see new properties</div></div>`;
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
          <span class="market-hood-emoji">${pxIcon(meta.emoji, 32)}</span>
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
      <div class="card-icon">${pxIcon(p.icon)}</div>
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
  renderMarket();
}

// ── Properties ────────────────────────────────────────────────────────────────
function renderProperties() {
  const el = document.getElementById('property-list');
  if (!el) return;
  if (!state.properties || state.properties.length === 0) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">${pxIcon('🏗️', 48)}</div>
      <div class="empty-text">No rental properties yet</div>
      <div class="empty-sub">Head to the Market tab to buy your first property</div>
    </div>`;
    return;
  }

  // Group by neighborhood
  const byHood = {};
  state.properties.forEach(p => {
    if (!byHood[p.neighborhood]) byHood[p.neighborhood] = [];
    byHood[p.neighborhood].push(p);
  });

  el.innerHTML = Object.entries(byHood).map(([hood, props]) => {
    const isOpen  = _propHoodOpen[hood] !== false; // default open
    const rented  = props.filter(p =>  p.tenant);
    const vacant  = props.filter(p => !p.tenant);
    // Default to rented tab if there are rented props, otherwise vacant
    const tab     = _propHoodTab[hood] || (rented.length > 0 ? 'rented' : 'vacant');
    const shown   = tab === 'rented' ? rented : vacant;
    const hoodId  = hood.replace(/\s+/g, '_');

    return `
    <div class="hood-section">
      <div class="hood-header" onclick="toggleHoodSection('${hood}')">
        <span class="hood-name">${hood}</span>
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:11px;color:var(--text-muted)">${props.length} prop${props.length !== 1 ? 's' : ''}</span>
          <span class="hood-chevron">${isOpen ? '▲' : '▼'}</span>
        </div>
      </div>
      ${isOpen ? `
      <div class="hood-tabs">
        <button class="hood-tab ${tab === 'vacant' ? 'active' : ''}" onclick="switchHoodTab('${hood}','vacant');event.stopPropagation()">
          ⚪ Vacant <span class="hood-tab-count">${vacant.length}</span>
        </button>
        <button class="hood-tab ${tab === 'rented' ? 'active' : ''}" onclick="switchHoodTab('${hood}','rented');event.stopPropagation()">
          ${pxIcon('👤',14)} Rented <span class="hood-tab-count">${rented.length}</span>
        </button>
      </div>
      <div class="hood-props">
        ${shown.length === 0
          ? `<div class="hood-empty">No ${tab} properties in ${hood}</div>`
          : shown.map(p => portfolioCardHtml(p)).join('')
        }
      </div>` : ''}
    </div>`;
  }).join('');
}

function toggleHoodSection(hood) {
  _propHoodOpen[hood] = _propHoodOpen[hood] === false ? true : false;
  renderProperties();
}

function switchHoodTab(hood, tab) {
  _propHoodTab[hood] = tab;
  renderProperties();
}

function playerHomeCardHtml() {
  const homeKey  = state.player_home || 'grandmas_basement';
  const maxE     = state.max_energy || 6;
  const recharge = state.energy_recharge || 1;
  const home     = PLAYER_HOME_DATA.find(h => h.key === homeKey) || PLAYER_HOME_DATA[0];
  const isMax    = homeKey === 'mansion';
  return `
  <div class="section-header" style="margin-bottom:8px">
    <span class="section-title">${pxIcon('🏠', 18)} My Home</span>
  </div>
  <div class="card" onclick="showPlayerHomeModal()" style="cursor:pointer;margin-bottom:16px;border:2px solid var(--primary)">
    <div class="card-header">
      <div class="card-icon">${pxIcon(home.icon)}</div>
      <div style="flex:1">
        <div class="card-title">${home.name}</div>
        <div class="card-subtitle">${isMax ? `${pxIcon('🏆',16)} Max upgrade reached!` : 'Tap to upgrade your home'}</div>
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
  const homeKey       = state.player_home || 'grandmas_basement';
  const currentIdx    = PLAYER_HOME_DATA.findIndex(h => h.key === homeKey);
  const current       = PLAYER_HOME_DATA[currentIdx] || PLAYER_HOME_DATA[0];
  const unlockedKeys  = state.unlocked_homes || ['grandmas_basement'];
  const upgrades      = PLAYER_HOME_DATA.slice(currentIdx + 1);

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🏠', 18)} Your Home</div>
    <div class="card" style="margin-bottom:16px;background:var(--surface-2)">
      <div style="display:flex;align-items:center;gap:12px">
        <div style="font-size:36px;line-height:1">${pxIcon(current.icon)}</div>
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
      ? `<div style="text-align:center;padding:20px;color:var(--text-muted)">${pxIcon('🏆',20)} You live in the best home possible!</div>`
      : `<div style="font-size:12px;font-weight:700;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:8px">UPGRADE OPTIONS</div>
         ${upgrades.map(h => {
           const isLocked  = !unlockedKeys.includes(h.key);
           const canAfford = !isLocked && state.cash >= h.cost;
           const reqLevel  = h.unlock_level || 0;
           const hIdx      = PLAYER_HOME_DATA.indexOf(h);
           const prev      = PLAYER_HOME_DATA[hIdx - 1];
           const deltaE    = prev ? h.max_energy - prev.max_energy : h.max_energy;
           const deltaR    = prev ? h.recharge   - prev.recharge   : h.recharge;
           return `
           <div class="card" style="margin-bottom:10px;opacity:${isLocked ? '0.45' : (!canAfford ? '0.6' : '1')}">
             <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
               <div style="font-size:28px;line-height:1">${pxIcon(isLocked ? '🔒' : h.icon)}</div>
               <div style="flex:1">
                 <div style="font-size:15px;font-weight:800">${h.name}</div>
                 <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${isLocked ? `Unlocks at Level ${reqLevel}` : h.desc}</div>
               </div>
               <div style="text-align:right;flex-shrink:0">
                 <div style="font-size:14px;font-weight:800;color:var(--primary)">${isLocked ? pxIcon('🔒',16) : fmt(h.cost)}</div>
               </div>
             </div>
             <div style="display:flex;gap:8px;margin-bottom:10px">
               <div style="flex:1;text-align:center;padding:6px;background:var(--surface-2);border-radius:6px">
                 <div style="font-size:15px;font-weight:800;color:var(--positive)">${deltaE > 0 ? '+' : ''}${deltaE} ⚡ max</div>
                 <div style="font-size:10px;color:var(--text-muted)">Max Energy</div>
               </div>
               <div style="flex:1;text-align:center;padding:6px;background:var(--surface-2);border-radius:6px">
                 <div style="font-size:15px;font-weight:800;color:var(--primary)">${deltaR > 0 ? '+' : ''}${deltaR}/day</div>
                 <div style="font-size:10px;color:var(--text-muted)">Daily Recharge</div>
               </div>
             </div>
             <button class="btn btn-full ${canAfford ? 'btn-primary' : 'btn-ghost'}"
               ${canAfford ? `onclick="moveIn('${h.key}')"` : 'disabled'}
               style="${!canAfford ? 'cursor:not-allowed' : ''}">
               ${isLocked ? `${pxIcon('🔒',14)} Locked — reach Level ${reqLevel}` : canAfford ? `Move In · ${fmt(h.cost)}` : `Need ${fmt(h.cost)} · Have ${fmt(state.cash)}`}
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
  renderPersonal();
  const home = PLAYER_HOME_DATA.find(h => h.key === homeKey);
  toast(`🏠 Moved into ${home ? home.name : 'new home'}! Energy max & recharge increased.`);
}

// ── Personal Tab ──────────────────────────────────────────────────────────────

const STORE_ITEM_DATA = [
  { key: 'coffee_maker', name: 'Coffee Maker', icon: '☕',  cost:  499, bonus: '+2 ⚡ max energy',   desc: 'A decent drip machine. Never run on empty again.' },
  { key: 'new_bed',      name: 'New Bed',       icon: '🛏️', cost: 4999, bonus: '+1 ⚡/day recharge', desc: 'Memory foam. You wake up ready to hustle.' },
];

const DIY_CLASS_DATA = [
  { key: 'flooring_class', name: 'Flooring Installation Class', icon: '🪵', energy: 10, unlock_level: 2, unlocks: ['flooring'],             desc: 'Learn to lay hardwood and tile yourself.' },
  { key: 'windows_class',  name: 'Window Installation Class',   icon: '🪟', energy: 10, unlock_level: 2, unlocks: ['windows'],              desc: 'Master framing, sealing, and fitting new windows.' },
  { key: 'remodel_class',  name: 'Remodeling Class',            icon: '🛠️', energy: 12, unlock_level: 3, unlocks: ['bathrooms', 'kitchen'], desc: 'Full course covering bathroom and kitchen remodels.' },
  { key: 'hvac_class',     name: 'HVAC System Course',          icon: '❄️', energy: 14, unlock_level: 4, unlocks: ['hvac'],                 desc: 'Certification-level HVAC installation and maintenance.' },
  { key: 'roof_class',     name: 'Roof Replacement Course',     icon: '🏠', energy: 14, unlock_level: 4, unlocks: ['roof'],                 desc: 'Safety and technique for full residential roof replacement.' },
];

// Maps upgrade key → the DIY class required; landscaping + paint are always free at lvl 1+
const DIY_REQUIRES_CLASS = {
  flooring:  'flooring_class',
  windows:   'windows_class',
  bathrooms: 'remodel_class',
  kitchen:   'remodel_class',
  hvac:      'hvac_class',
  roof:      'roof_class',
};

function diyUnlocked(upgradeKey) {
  if ((state.level || 0) < 1) return false;
  if (upgradeKey === 'landscaping' || upgradeKey === 'paint') return true;
  const classKey = DIY_REQUIRES_CLASS[upgradeKey];
  return classKey ? !!((state.diy_classes || {})[classKey]) : true;
}

let _personalOpen = { homes: false, classes: false, store: false };

function renderPersonal() {
  const el = document.getElementById('page-personal');
  if (!el || !state) return;

  const homeKey      = state.player_home || 'grandmas_basement';
  const current      = PLAYER_HOME_DATA.find(h => h.key === homeKey) || PLAYER_HOME_DATA[0];
  const currentIdx   = PLAYER_HOME_DATA.indexOf(current);
  const unlockedKeys = state.unlocked_homes || ['grandmas_basement'];
  const ownedItems   = state.owned_items || {};
  const maxE         = state.max_energy || 6;
  const recharge     = state.energy_recharge || 1;
  const curEnergy    = state.energy ?? 0;
  const diyClasses   = state.diy_classes || {};

  // ── Home upgrade rows ─────────────────────────────────────────
  const homeRows = PLAYER_HOME_DATA.map((h, idx) => {
    const isCurrent  = h.key === homeKey;
    const isPast     = idx < currentIdx;
    const isUnlocked = unlockedKeys.includes(h.key);
    const canAfford  = !isCurrent && !isPast && isUnlocked && state.cash >= h.cost;
    const lockLevel  = h.unlock_level || 0;
    const prev       = PLAYER_HOME_DATA[idx - 1];
    const deltaE     = prev ? h.max_energy - prev.max_energy : 0;
    const deltaR     = prev ? h.recharge   - prev.recharge   : 0;

    const opacity = isCurrent ? '1' : isPast ? '0.4' : !isUnlocked ? '0.4' : !canAfford ? '0.65' : '1';

    let badge = '';
    if (isCurrent)     badge = `<span style="background:var(--primary);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">CURRENT</span>`;
    else if (!isUnlocked) badge = `<span style="background:#555;color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">${pxIcon('🔒',12)} LVL ${lockLevel}</span>`;

    let actionBtn = '';
    if (!isCurrent && !isPast) {
      if (!isUnlocked) {
        actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Lvl ${lockLevel}</button>`;
      } else if (!canAfford) {
        actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Need ${fmt(h.cost)}</button>`;
      } else {
        actionBtn = `<button class="btn btn-primary btn-sm" onclick="moveIn('${h.key}')" style="font-size:11px">Move In</button>`;
      }
    }

    const statLine = idx === 0
      ? `⚡${h.max_energy} max · +${h.recharge}/day recharge`
      : `${deltaE >= 0 ? '+' : ''}${deltaE}⚡ max · ${deltaR >= 0 ? '+' : ''}${deltaR}/day recharge`;

    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);opacity:${opacity}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(isUnlocked || isCurrent ? h.icon : '🔒')}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">${h.name}</span>
          ${badge}
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.4">${isUnlocked || isCurrent ? h.desc : `Unlocks at Level ${lockLevel}`}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:3px;font-weight:700">${statLine}</div>
      </div>
      <div style="flex-shrink:0">
        ${h.cost > 0 && !isCurrent && !isPast ? `<div style="font-size:11px;font-weight:800;color:var(--primary);text-align:right;margin-bottom:3px">${fmt(h.cost)}</div>` : ''}
        ${actionBtn}
      </div>
    </div>`;
  }).join('');

  // ── Class rows ─────────────────────────────────────────────────
  const classRows = DIY_CLASS_DATA.map(cls => {
    const owned       = !!diyClasses[cls.key];
    const levelOk     = (state.level || 0) >= cls.unlock_level;
    const hasEnergy   = curEnergy >= cls.energy;
    const canBuy      = !owned && levelOk && hasEnergy;
    const unlockLabel = cls.unlocks.map(k => {
      const names = { landscaping:'Landscaping', paint:'Interior Paint', flooring:'New Flooring',
                      windows:'New Windows', bathrooms:'Bathroom Remodel', kitchen:'Kitchen Remodel',
                      hvac:'HVAC System', roof:'Roof Replacement' };
      return names[k] || k;
    }).join(' & ');

    const opacity = owned ? '0.6' : !levelOk ? '0.4' : '1';

    let badge = '';
    if (owned)        badge = `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">✓ Done</span>`;
    else if (!levelOk) badge = `<span style="background:#555;color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">${pxIcon('🔒',12)} LVL ${cls.unlock_level}</span>`;

    let actionBtn = '';
    if (owned) {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;opacity:0.5">Done</button>`;
    } else if (!levelOk) {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Lvl ${cls.unlock_level}</button>`;
    } else if (canBuy) {
      actionBtn = `<button class="btn btn-primary btn-sm" onclick="buyDiyClass('${cls.key}')" style="font-size:11px">Enroll ⚡${cls.energy}</button>`;
    } else {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;color:var(--negative)">Need ⚡${cls.energy}</button>`;
    }

    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);opacity:${opacity}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(!levelOk ? '🔒' : cls.icon)}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">${cls.name}</span>
          ${badge}
        </div>
        ${levelOk && !owned ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.4">${cls.desc}</div>` : ''}
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;font-weight:700">
          ${!levelOk ? `Unlocks at Level ${cls.unlock_level}` : `Unlocks: ${unlockLabel}`}
        </div>
      </div>
      <div style="flex-shrink:0">${actionBtn}</div>
    </div>`;
  }).join('');

  // ── Store rows ─────────────────────────────────────────────────
  const squatterBlocked = starterSquatterActive();
  const storeRows = STORE_ITEM_DATA.map(item => {
    const owned      = !!ownedItems[item.key];
    const isLocked   = squatterBlocked && !owned;
    const canAfford  = !owned && !isLocked && state.cash >= item.cost;

    let actionBtn = '';
    if (owned) {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;opacity:0.5">Owned</button>`;
    } else if (isLocked) {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">🚨 Later</button>`;
    } else if (canAfford) {
      actionBtn = `<button class="btn btn-primary btn-sm" onclick="buyStoreItem('${item.key}')" style="font-size:11px">Buy ${fmt(item.cost)}</button>`;
    } else {
      actionBtn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Need ${fmt(item.cost)}</button>`;
    }

    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);${owned ? 'opacity:0.6' : ''}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(item.icon)}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">${item.name}</span>
          ${owned ? `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">✓ Owned</span>` : ''}
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:1px">${item.desc}</div>
        <div style="font-size:11px;font-weight:700;color:var(--primary);margin-top:1px">${item.bonus}</div>
      </div>
      <div style="flex-shrink:0">${actionBtn}</div>
    </div>`;
  }).join('');

  // ── Hood-section builder ───────────────────────────────────────
  const personalSection = (id, title, content, meta) => {
    const isOpen = !!_personalOpen[id];
    return `
    <div class="hood-section" style="margin-bottom:10px">
      <div class="hood-header" onclick="togglePersonalSection('${id}')">
        <span class="hood-name">${title}</span>
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:11px;color:var(--text-muted)">${meta}</span>
          <span class="hood-chevron">${isOpen ? '▲' : '▼'}</span>
        </div>
      </div>
      ${isOpen ? `<div>${content}</div>` : ''}
    </div>`;
  };

  const homesUnlocked = unlockedKeys.length;
  const classesCount  = Object.keys(diyClasses).length;
  const storeOwned    = STORE_ITEM_DATA.filter(i => ownedItems[i.key]).length;

  el.innerHTML = `
    <div style="padding:12px;max-width:480px;margin:0 auto">

      <div class="hood-section" style="margin-bottom:10px">
        <div style="padding:14px">
          <div style="display:flex;align-items:center;gap:14px">
            <div style="font-size:34px;line-height:1;flex-shrink:0">${pxIcon(current.icon)}</div>
            <div style="flex:1;min-width:0">
              <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:3px">Your Home</div>
              <div style="font-size:16px;font-weight:900">${current.name}</div>
            </div>
            <div style="text-align:right;flex-shrink:0">
              <div style="font-size:10px;color:var(--text-muted);margin-bottom:2px">Energy</div>
              <div style="font-size:20px;font-weight:900;color:var(--positive);line-height:1">⚡${curEnergy}<span style="font-size:11px;color:var(--text-muted)">/${maxE}</span></div>
            </div>
          </div>
          <div style="display:flex;gap:8px;margin-top:12px">
            <div style="flex:1;padding:7px;background:var(--surface-2);border-radius:8px;text-align:center">
              <div style="font-size:15px;font-weight:900;color:var(--positive)">⚡ ${maxE}</div>
              <div style="font-size:10px;color:var(--text-muted)">Max Energy</div>
            </div>
            <div style="flex:1;padding:7px;background:var(--surface-2);border-radius:8px;text-align:center">
              <div style="font-size:15px;font-weight:900;color:var(--primary)">+${recharge}/day</div>
              <div style="font-size:10px;color:var(--text-muted)">Daily Recharge</div>
            </div>
          </div>
        </div>
      </div>

      ${personalSection('homes',   `${pxIcon('🏡',16)} Home Upgrades`, homeRows,  `${homesUnlocked}/${PLAYER_HOME_DATA.length} unlocked`)}
      ${personalSection('classes', `${pxIcon('📚',16)} Skill Classes`, classRows, `${classesCount}/${DIY_CLASS_DATA.length} done`)}
      ${personalSection('store',   `${pxIcon('🛒',16)} Personal Store`, storeRows, `${storeOwned}/${STORE_ITEM_DATA.length} owned`)}

    </div>`;
}

function togglePersonalSection(id) {
  _personalOpen[id] = !_personalOpen[id];
  renderPersonal();
}

async function buyStoreItem(itemKey) {
  const res = await api('/store/buy_item', 'POST', { item_key: itemKey });
  if (res.error) { toast(res.error, 'warning'); return; }
  await refreshState();
  renderPersonal();
  toast(`${res.item} purchased!`);
}

async function buyDiyClass(classKey) {
  const res = await api('/education/buy_class', 'POST', { class_key: classKey });
  if (res.error) { toast(res.error, 'warning'); return; }
  await refreshState();
  renderPersonal();
  toast(`${res.class_name} completed! New DIY skills unlocked.`);
}

function portfolioCardHtml(p) {
  const tier            = HOOD_TIERS[p.neighborhood] || 'mid';
  const activePending   = p.pending_reno || p.pending_premium;
  const pendingDaysLeft = activePending ? Math.max(0, activePending.complete_day - state.day) : 0;
  const scheduledWork   = p.scheduled_reno || p.scheduled_premium;
  const scheduledDaysOut = scheduledWork ? Math.max(0, scheduledWork.start_day - state.day) : 0;
  const tenantBadge = p.reno_payment_owed
    ? `<span class="vacant-chip" style="background:#FFF3E0;color:#E65100;border-color:#FFCC80;font-weight:800">${pxIcon('💸',14)} Pay Contractor: ${fmt(p.reno_payment_owed.amount)}</span>`
    : p.squatter
    ? `<span class="vacant-chip" style="background:#FFEBEE;color:#C62828;border-color:#EF9A9A">${pxIcon('🚨',14)} Squatter</span>`
    : activePending
    ? `<span class="vacant-chip" style="background:#E3F2FD;color:#1565C0;border-color:#90CAF9">${pxIcon('🔨',14)} ${activePending.name} · ${pendingDaysLeft}d left</span>`
    : p.tenant && scheduledWork
    ? `<span class="vacant-chip" style="background:#F3E5F5;color:#6A1B9A;border-color:#CE93D8">${pxIcon('🗓️',14)} ${scheduledWork.name} · starts in ${scheduledDaysOut}d</span>`
    : p.tenant && p.tenant.is_mystery
    ? `<span class="tenant-chip" style="background:#2d004f;color:#CE93D8;border-color:#7B1FA2;font-weight:800">${pxIcon('👤',18)} ??? · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_phil
    ? `<span class="tenant-chip" style="background:#fffde7;color:#b8860b;border-color:gold;font-weight:800">${pxIcon('🔱',18)} The Phil · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_baileys
    ? `<span class="tenant-chip" style="background:#FFF3E0;color:#E65100;border-color:#E65100;font-weight:800">${pxIcon('👨‍👩‍👧‍👦',18)} The Baileys · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && p.tenant.is_goldbergs
    ? `<span class="tenant-chip" style="background:#E8F5E9;color:#1B5E20;border-color:#2E7D32;font-weight:800">${pxIcon('🎩',18)} The Goldbergs · ${fmt(p.tenant.rent)}/wk</span>`
    : p.tenant && (p.tenant.morale ?? 50) < 20
    ? `<span class="vacant-chip" style="background:#FFEBEE;color:#C62828;border-color:#EF9A9A">${pxIcon('😠', 16)} ${p.tenant.name} · morale ${p.tenant.morale ?? '?'}%</span>`
    : p.tenant
    ? `<span class="tenant-chip">${p.tenant.name} · ${fmt(p.tenant.rent)}/wk</span>`
    : `<span class="vacant-chip">⚪ Vacant</span>`;
  const profit    = p.market_value - p.purchase_price;
  const profitStr = profit >= 0
    ? `<span class="mr-value green">+${fmt(profit)}</span>`
    : `<span class="mr-value red">${fmt(profit)}</span>`;

  const condTierVal = condTier(p.condition);
  const condShine   = ['S', 'S+'].includes(condTierVal) ? ' cond-shining' : '';
  const isSpecialTenant = p.tenant && (p.tenant.is_phil || p.tenant.is_baileys || p.tenant.is_goldbergs || p.tenant.is_mystery);
  const moraleBar = (p.tenant && !isSpecialTenant && !p.squatter && !activePending && !p.reno_payment_owed)
    ? (() => {
        const m      = p.tenant.morale ?? 50;
        const mColor = m >= 70 ? 'var(--positive)' : m >= 40 ? 'var(--warning)' : 'var(--negative)';
        return `<div style="display:flex;align-items:center;gap:5px;margin-top:7px">
          <span style="font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.4px">Morale</span>
          <div style="flex:1;height:3px;background:var(--border);border-radius:99px;max-width:60px">
            <div style="height:100%;width:${m}%;background:${mColor};border-radius:99px;transition:width .4s"></div>
          </div>
          <span style="font-size:10px;font-weight:800;color:${mColor}">${m}%</span>
        </div>`;
      })()
    : '';

  return `
  <div class="card tier-${tier}" onclick="showPropertyDetail(${p.id})" style="cursor:pointer">
    <div class="card-header">
      <div class="prop-icon-circle prop-icon-${tier}">${pxIcon(p.icon)}</div>
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
        <span class="condition-lbl">Condition · <span style="color:${tierColor(condTierVal)};font-weight:900">${condTierVal}</span></span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}${condShine}" style="width:${condPct(p.condition)}%"></div></div>
    </div>
    <div style="margin-top:10px;display:flex;align-items:center;justify-content:space-between">
      ${tenantBadge}
      <div style="font-size:12px;color:var(--text-muted)">G/L: ${profitStr}</div>
    </div>
    ${moraleBar}
  </div>`;
}

// ── Property Detail ───────────────────────────────────────────────────────────
async function showPropertyDetail(id) {
  const prop = state.properties.find(p => p.id === id);
  if (!prop) return;
  _propDetailId   = id;
  _inPropSubModal = false;

  const [upgData, premData] = await Promise.all([
    api(`/property/${id}/upgrades`),
    api(`/property/${id}/premium_upgrades`),
  ]);
  const profit   = prop.market_value - prop.purchase_price;
  const profitStr = profit >= 0
    ? `<span style="color:var(--positive)">+${fmt(profit)}</span>`
    : `<span style="color:var(--negative)">${fmt(profit)}</span>`;

  const contractorPayment = (() => {
    if (!prop.reno_payment_owed) return '';
    const owed       = prop.reno_payment_owed;
    const daysOverdue = Math.max(0, state.day - owed.due_since_day);
    const daysLeft    = Math.max(0, 28 - daysOverdue);
    const canAfford   = state.cash >= owed.amount;
    const urgencyColor = daysLeft <= 7 ? '#C62828' : '#E65100';
    const urgencyNote  = daysLeft <= 7
      ? `<div style="font-size:12px;font-weight:700;color:#C62828;margin-top:6px">⚠️ ${daysLeft} day${daysLeft !== 1 ? 's' : ''} left — contractor destroys the home at day 28!</div>`
      : daysOverdue > 3
      ? `<div style="font-size:12px;color:#E65100;margin-top:6px">📈 Growing 10%/day · ${daysLeft} days until destruction</div>`
      : '';
    return `
      <div class="card" style="margin-bottom:10px;border:2px solid ${urgencyColor};background:#FFF3E0">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
          ${pxIcon('💸',30)}
          <div style="flex:1">
            <div style="font-size:15px;font-weight:800;color:${urgencyColor}">Contractor Payment Due</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:2px">${pxIcon(owed.icon)} ${owed.name} is complete — grade hidden until paid</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:20px;font-weight:900;color:${urgencyColor}">${fmt(owed.amount)}</div>
            <div style="font-size:11px;color:var(--text-muted)">owed</div>
          </div>
        </div>
        ${urgencyNote}
        ${canAfford
          ? `<button class="btn btn-full" style="background:${urgencyColor};color:#fff;font-weight:800;margin-top:8px" onclick="payContractor(${id})">${pxIcon('💸',14)} Pay ${fmt(owed.amount)}</button>`
          : `<button class="btn btn-full" disabled style="opacity:0.5;margin-top:8px;cursor:not-allowed">${pxIcon('💸',14)} Need ${fmt(owed.amount - state.cash)} more to pay</button>`
        }
      </div>`;
  })();

  const renoInProgress = prop.pending_reno
    ? `<div class="card" style="margin-bottom:10px;border:2px solid #1565C0">
        <div style="display:flex;align-items:center;gap:12px">
          ${pxIcon('🔨',30)}
          <div style="flex:1">
            <div style="font-size:15px;font-weight:800;color:#1565C0">Renovation In Progress</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:2px">${pxIcon(prop.pending_reno.icon)} ${prop.pending_reno.name}</div>
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
        <div class="section-header mb-0"><span class="section-title" style="color:#C62828">${pxIcon('🚨',18)} Squatters Present</span></div>
        <p style="margin-top:8px;font-size:13px;color:var(--text-muted)">${prop.squatter.starter
          ? `Grandma left the property to me — but apparently someone settled in before I could get the keys. She said clear them out and it's mine. Honestly, given the condition they've left it in, selling as-is might be the smarter move.`
          : `Someone has moved in without permission and isn't paying rent. You can't rent out or renovate until they're gone.`
        }</p>
        <div class="money-row" style="margin-top:10px"><span class="mr-label">Their Asking Price to Leave</span><span class="mr-value" style="color:#C62828">${fmt(prop.squatter.bribe)}</span></div>
        <div class="btn-row" style="margin-top:10px">
          <button class="btn btn-danger btn-sm" onclick="briberSquatter(${id})">${pxIcon('💸',14)} Pay ${fmt(prop.squatter.bribe)} to Remove</button>
        </div>
        ${prop.squatter.starter ? '' : `<p style="font-size:11px;color:var(--text-muted);margin-top:8px">Or wait — they may leave on their own eventually.</p>`}
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
        const badgeHtml   = isMystery   ? `<span style="font-size:11px;background:#7B1FA2;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">${pxIcon('👤',14)} MYSTERY</span>`
                          : isPhil      ? `<span style="font-size:11px;background:gold;color:#5d4037;padding:2px 8px;border-radius:8px;font-weight:700">${pxIcon('🔱',14)} THE PHIL</span>`
                          : isBaileys   ? `<span style="font-size:11px;background:#E65100;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">${pxIcon('👨‍👩‍👧‍👦',14)} THE BAILEYS</span>`
                          : isGoldbergs ? `<span style="font-size:11px;background:#2E7D32;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700">${pxIcon('🎩',14)} THE GOLDBERGS</span>` : '';
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
            ${isSpecial ? `<span style="${iconStyle}">${pxIcon(isMystery ? '👤' : prop.tenant.icon || '👤')}</span>` : ''}
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
            <button class="btn btn-danger btn-sm" onclick="evictTenant(${id})">${pxIcon('⚖️',14)} Evict ($1,500)</button>
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
          ${!prop.pending_reno ? `<button class="btn btn-primary btn-sm" onclick="showTenantsModal(${id})">${pxIcon('🔑',14)} Find Tenant</button>` : ''}
          ${(() => {
            const daysOwned = prop.purchase_day != null ? (state.day - prop.purchase_day) : 99;
            const daysLeft  = Math.max(0, 3 - daysOwned);
            return daysLeft > 0
              ? `<button class="btn btn-accent btn-sm" disabled style="opacity:0.45;cursor:not-allowed" title="No buyers yet">${pxIcon('💰',14)} No Buyers Yet (${daysLeft}d)</button>`
              : `<button class="btn btn-accent btn-sm" onclick="sellProperty(${id})">${pxIcon('💰',14)} Sell Property</button>`;
          })()}
        </div>
      </div>`;

  const cooldownHtml = (upgData.on_cooldown || []).length > 0
    ? `<div style="margin-bottom:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:var(--text-muted)">ON COOLDOWN</div>
       <div class="upgrade-grid">${upgData.on_cooldown.map(u =>
        `<div class="upgrade-card done" style="opacity:0.7">
          <div class="upgrade-icon">${pxIcon(u.icon)}</div>
          <div class="upgrade-name">${u.name}</div>
          <div class="upgrade-quality" style="color:${tierColor(u.quality_tier)};font-weight:800">${u.quality_tier}</div>
          <div class="upgrade-quality">${pxIcon('⏳',14)} ${u.days_remaining}d left</div>
        </div>`).join('')}</div></div>`
    : '';

  // Scheduled reno info banner
  const scheduledRenoHtml = prop.scheduled_reno
    ? `<div class="card" style="margin-bottom:10px;border:2px solid #7B1FA2;background:#F3E5F5">
        <div style="display:flex;align-items:center;gap:12px">
          ${pxIcon('🗓️',28)}
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#6A1B9A">Renovation Scheduled</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${pxIcon(prop.scheduled_reno.icon)} ${prop.scheduled_reno.name}</div>
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
          <div class="upgrade-icon">${pxIcon(u.icon)}</div>
          <div class="upgrade-name">${u.name}</div>
          ${u.prev_quality_tier
            ? `<div class="upgrade-quality" style="font-size:10px;color:var(--text-muted)">Last: ${u.prev_quality_tier} · Redo</div>`
            : `<div class="upgrade-cost">from ${fmt(u.costs.budget)}</div>`}
          ${canSchedule ? `<div class="upgrade-quality" style="font-size:10px;color:#7B1FA2">${pxIcon('📅',12)} Schedule</div>` : ''}
        </div>`;
      }).join('')}</div>`
    : '<p class="text-muted" style="margin-top:4px">All upgrades on cooldown!</p>';

  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
      <span style="font-size:36px">${pxIcon(prop.icon)}</span>
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
    ${contractorPayment}
    ${renoInProgress}
    ${tenantSection}
    <div class="section-header"><span class="section-title">Renovations</span></div>
    ${state.level < 1
      ? `<div class="card" style="text-align:center;padding:18px 16px;margin-bottom:8px;opacity:0.75">
           <div style="margin-bottom:6px">${pxIcon('🔒',28)}</div>
           <div style="font-weight:800;font-size:14px">Locked</div>
           <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Sell your starter property to reach Level 1 and unlock renovations</div>
         </div>`
      : `${prop.pending_reno
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
            <div class="upgrade-icon">${pxIcon(upgData.pending_reno.icon)}</div>
            <div class="upgrade-name">${upgData.pending_reno.name}</div>
            <div class="upgrade-quality" style="color:#1565C0">${pxIcon('🔨',12)} ${Math.max(0, upgData.pending_reno.complete_day - state.day)}d left</div>
          </div></div></div>` : ''}
        ${!prop.pending_reno && upgData.available.length > 0 ? `<div style="margin-top:8px"><div class="section-title" style="font-size:11px;margin-bottom:6px;color:var(--text-muted)">${prop.tenant && !prop.scheduled_reno ? 'TAP TO SCHEDULE' : 'AVAILABLE'}</div>${availHtml}</div>` : ''}`}
    ${buildPremiumSection(id, premData, state.cash, !!prop.squatter, !!prop.tenant)}
    <div class="btn-row" style="margin-top:16px">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">← Back</button>
    </div>`);
}

// ── Premium Upgrades ─────────────────────────────────────────────────────────
function buildPremiumSection(pid, premData, cash, hasSquatter = false, hasTenant = false) {
  const blocked = hasSquatter || !!(premData.pending_premium);

  if ((state.level || 0) < 5) {
    return `
    <div class="section-header" style="margin-top:16px">
      <span class="section-title">⭐ Premium Upgrades</span>
    </div>
    <div class="card" style="text-align:center;padding:18px 16px;opacity:0.75">
      <div style="margin-bottom:6px">${pxIcon('🔒',28)}</div>
      <div style="font-weight:800;font-size:14px">Locked until Level 5</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Keep leveling up to unlock premium upgrades</div>
    </div>`;
  }

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
        <span style="font-size:22px">${pxIcon(u.icon)}</span>
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
          <span style="font-size:26px">${pxIcon(premData.pending_premium.icon)}</span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#1565C0">${pxIcon('🔨',14)} ${premData.pending_premium.name}</div>
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
          ${pxIcon('🗓️',26)}
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#6A1B9A">Upgrade Scheduled</div>
            <div style="font-size:12px;color:var(--text-muted);">${pxIcon(scheduledPrem.icon)} ${scheduledPrem.name} · Day ${scheduledPrem.start_day}</div>
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
    else if (canSchedule)    { btnLabel = `${pxIcon('📅',14)} Schedule · ${fmt(u.cost)}`; btnOnclick = `onclick="showSchedulePremiumModal(${pid},'${u.key}',${u.cost},${u.days},'${u.name}','${u.icon}')"` ; }
    else                     { btnLabel = `${pxIcon('🔨',14)} Hire Contractor · ${fmt(u.cost)}`; btnOnclick = `onclick="installPremiumUpgrade(${pid},'${u.key}')"` ; }

    return `
    <div class="card" style="margin-bottom:8px${fullyBlocked ? ';opacity:0.55' : ''}">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <span style="font-size:28px;line-height:1.2">${pxIcon(u.icon)}</span>
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
    <div class="modal-title">${pxIcon('🔨',20)} Work Underway!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div>${pxIcon('🏗️',48)}</div>
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
  _inPropSubModal = true;

  // Stable tenant window — same day until the player advances
  const availDay = getTenantAvailDay(propId);
  const daysOut  = availDay - state.day;
  const sInfo    = getSeasonInfo(availDay);

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(upg.icon)} ${upg.name}</div>
    <div class="modal-subtitle">Schedule with tenant in residence</div>

    <div class="card" style="margin-bottom:16px;background:#F3E5F5;border:2px solid #CE93D8">
      <div style="display:flex;align-items:center;gap:12px">
        ${pxIcon('📅',30)}
        <div>
          <div style="font-size:14px;font-weight:800;color:#6A1B9A">Tenant Maintenance Window</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:3px">
            Your tenant is available starting <strong>Day ${availDay}</strong>
            &nbsp;(${pxIcon(sInfo.icon)} ${sInfo.name} · in ${daysOut} day${daysOut !== 1 ? 's' : ''})
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
        <div class="contractor-special-badge">${pxIcon('⚡',14)} SPECIAL — Guaranteed S+</div>
        <div class="contractor-header">
          <span class="contractor-icon">${pxIcon(sc.icon)}</span>
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
          ${canAfford ? `${pxIcon('📅',14)} Book · ${fmt(sc.cost)}` : `Not enough cash`}
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
          <span class="contractor-icon">${pxIcon(c.icon)}</span>
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
          ${canAfford ? `${pxIcon('📅',14)} Book · ${fmt(cost)}` : `Not enough cash`}
        </button>
      </div>`;
    }).join('')}

    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="backToProperty()">Cancel</button>`);
}

async function confirmScheduleReno(propId, upgradeKey, contractorKey, startDay) {
  const res = await api(`/property/${propId}/schedule_reno`, 'POST', {
    upgrade_key: upgradeKey, contractor_key: contractorKey, start_day: startDay,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  _inPropSubModal = true;
  const daysOut = startDay - state.day;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('📅',20)} Renovation Scheduled!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div>${pxIcon('🗓️',48)}</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px;color:#6A1B9A">Day ${startDay}</div>
      <div style="font-size:13px;color:var(--text-muted)">contractors arrive · in ${daysOut} day${daysOut !== 1 ? 's' : ''}</div>
    </div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="backToProperty()">Got It</button>`);
  await refreshState();
  renderAll();
}

function showSchedulePremiumModal(propId, upgradeKey, cost, days, name, icon) {
  _inPropSubModal = true;
  // Stable tenant window — same day until the player advances
  const availDay = getTenantAvailDay(propId);
  const daysOut  = availDay - state.day;
  const sInfo    = getSeasonInfo(availDay);
  const canAfford = state.cash >= cost;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(icon)} ${name}</div>
    <div class="modal-subtitle">Schedule with tenant in residence</div>

    <div class="card" style="margin-bottom:16px;background:#F3E5F5;border:2px solid #CE93D8">
      <div style="display:flex;align-items:center;gap:12px">
        ${pxIcon('📅',30)}
        <div>
          <div style="font-size:14px;font-weight:800;color:#6A1B9A">Tenant Maintenance Window</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:3px">
            Your tenant is available starting <strong>Day ${availDay}</strong>
            &nbsp;(${pxIcon(sInfo.icon)} ${sInfo.name} · in ${daysOut} day${daysOut !== 1 ? 's' : ''})
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
      ${canAfford ? `${pxIcon('📅',14)} Schedule · ${fmt(cost)}` : `Need ${fmt(cost)} — have ${fmt(state.cash)}`}
    </button>
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="backToProperty()">Cancel</button>`);
}

async function confirmSchedulePremium(propId, upgradeKey, startDay) {
  const res = await api(`/property/${propId}/schedule_premium`, 'POST', {
    upgrade_key: upgradeKey, start_day: startDay,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  _inPropSubModal = true;
  const daysOut = startDay - state.day;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('📅',20)} Upgrade Scheduled!</div>
    <div class="modal-subtitle">${res.name}</div>
    <div style="text-align:center;padding:16px 0">
      <div>${pxIcon('🗓️',48)}</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px;color:#6A1B9A">Day ${startDay}</div>
      <div style="font-size:13px;color:var(--text-muted)">workers arrive · in ${daysOut} day${daysOut !== 1 ? 's' : ''}</div>
    </div>
    <div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <button class="btn btn-primary btn-full mt-8" onclick="backToProperty()">Got It</button>`);
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
  _inPropSubModal = true;
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
          <span class="tenant-icon" style="filter:brightness(0.1)">${pxIcon('👤',28)}</span>
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
          <span class="tenant-icon">${pxIcon(t.icon)}</span>
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
          <span class="tenant-icon">${pxIcon(t.icon)}</span>
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
          <span class="tenant-icon">${pxIcon(t.icon)}</span>
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
            <span class="tm-value" style="color:#1B5E20">${pxIcon('💰',14)} Pays 10× rent automatically — short stay</span>
          </div>
        </div>
      </div>` : `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})">
        <div class="tenant-header">
          <div style="flex:1">
            <div class="tenant-name">${t.name}</div>
            ${t.desc ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.4">${t.desc}</div>` : ''}
            <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${t.stay_min}–${t.stay_max} day base lease</div>
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
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="backToProperty()">Cancel</button>`);
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
    <div class="modal-title">${(t.is_phil || t.is_baileys || t.is_goldbergs || t.is_mystery) ? pxIcon(t.icon) + ' ' : ''}Set Your Rent</div>
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
  'windows':     'windowgame',   // Level the Windows — hold to level, they drift back
  'hvac':        'hvacgame',     // Run the HVAC Pipe — drag through attic maze
  'bathrooms':   'plumbinggame', // Tighten the Pipe — tap to stop the burst
  'roof':        'roofgame',     // Roof Replacement — scrape old, tap new
  'kitchen':     'groutgame',    // Grout the Backsplash — drag along every tile joint
  'landscaping': 'landscapegame', // Pull the Weeds — tap weeds before they take over
  // Repair types
  'plumbing':    'plumbinggame',
  'electrical':  'electricalgame', // Wire the Panel — match wire colors to terminals
  'appliance':   'sweetspot',
  'roof_patch':  'roofgame',
  'pest':        'reactiontap',
  'hvac_fix':    'sweetspot',
  // Side job names
  'Paint a Room':        'paintgame',
  'Lay Flooring':        'flooringgame',
  'Patch the Roof':      'roofgame',
  'Fix a Plumbing Leak': 'plumbinggame',
  'Install Windows':     'windowgame',
  'Tile a Bathroom':     'tilegame',
  'Hang Drywall':        'drywallgame',
  'Electrical Work':     'electricalgame',
  'HVAC Maintenance':    'hvacgame',
  'Build a Fence':       'fencegame',
  'Pour Concrete':       'concretegame',
  'Landscaping Work':    'landscapegame',
  'Power Washing':       'washgame',
  'Install Cabinets':    'cabinetgame',
  'Repair a Deck':       'deckgame',
};
function selectMgType(context) { return WORK_MG_MAP[context] || randomMgType(); }

function launchMgByType(mgType, upgradeKey) {
  if      (mgType === 'quicktap')    launchQuickTap(upgradeKey);
  else if (mgType === 'sweetspot')   launchSweetSpot(upgradeKey);
  else if (mgType === 'sequence')    launchSequence(upgradeKey);
  else if (mgType === 'rapidpress')  launchRapidPress(upgradeKey);
  else if (mgType === 'colormatch')  launchColorMatch(upgradeKey);
  else if (mgType === 'tilegame')    launchTileGame(upgradeKey);
  else if (mgType === 'reactiontap') launchReactionTap(upgradeKey);
  else if (mgType === 'paintgame')    launchPaintGame(upgradeKey);
  else if (mgType === 'landscapegame') launchLandscapeGame(upgradeKey);
  else if (mgType === 'flooringgame')  launchFlooringGame(upgradeKey);
  else if (mgType === 'windowgame')    launchWindowGame(upgradeKey);
  else if (mgType === 'hvacgame')      launchHvacGame(upgradeKey);
  else if (mgType === 'plumbinggame')  launchPlumbingGame(upgradeKey);
  else if (mgType === 'roofgame')      launchRoofGame(upgradeKey);
  else if (mgType === 'groutgame')      launchGroutGame(upgradeKey);
  else if (mgType === 'electricalgame') launchElectricalGame(upgradeKey);
  else if (mgType === 'tilegame')       launchTileGame(upgradeKey);
  else if (mgType === 'drywallgame')    launchDrywallGame(upgradeKey);
  else if (mgType === 'fencegame')      launchFenceGame(upgradeKey);
  else if (mgType === 'concretegame')   launchConcreteGame(upgradeKey);
  else if (mgType === 'washgame')       launchWashGame(upgradeKey);
  else if (mgType === 'cabinetgame')    launchCabinetGame(upgradeKey);
  else if (mgType === 'deckgame')       launchDeckGame(upgradeKey);
}

async function showContractorModal(propId, upgradeKey) {
  pendingUpgrade  = { propId, upgradeKey };
  _inPropSubModal = true;
  const upgData   = await api(`/property/${propId}/upgrades`);
  const upg      = upgData.available.find(u => u.key === upgradeKey);
  if (!upg) return;

  const energy     = state.energy ?? DAILY_ENERGY;
  const maxE       = state.max_energy || DAILY_ENERGY;
  const ec         = upg.energy_cost ?? 1;
  const hasEnergy  = energy >= ec;
  const energyDots = `⚡ ${energy}/${maxE} remaining`;
  const ecPips     = '⚡'.repeat(ec) + '<span style="opacity:0.2">⚡</span>'.repeat(Math.max(0, 4 - ec));
  const canDIY     = diyUnlocked(upgradeKey);

  // Find which class unlocks this upgrade (for the locked hint)
  const reqClass   = DIY_CLASS_DATA.find(c => c.unlocks.includes(upgradeKey));

  const diyCard = !canDIY
    ? `<div class="contractor-card" style="border-color:var(--border);opacity:0.6;margin-bottom:8px">
        <div class="contractor-header">
          <span class="contractor-icon">${pxIcon('🔒',28)}</span>
          <span class="contractor-name">Do It Yourself</span>
          <span class="contractor-cost" style="color:var(--text-muted)">Locked</span>
        </div>
        <div class="contractor-desc" style="color:var(--text-muted)">
          ${reqClass
            ? `Complete the <strong>${reqClass.name}</strong> in Personal → Skill Classes to unlock DIY for this.`
            : 'Reach Level 1 to unlock DIY renovations.'}
        </div>
      </div>`
    : hasEnergy
    ? `<div class="contractor-card" style="border-color:var(--primary);margin-bottom:8px" onclick="startDIY('${upgradeKey}')">
        <div class="contractor-header">
          <span class="contractor-icon">${pxIcon('🧰',28)}</span>
          <span class="contractor-name">Do It Yourself</span>
          <span class="contractor-cost" style="color:var(--positive)">FREE · ${ecPips}</span>
        </div>
        <div class="contractor-desc">Play a mini-game — how well you do determines the work quality.</div>
        <div class="contractor-quality">${energyDots}</div>
      </div>`
    : `<div class="contractor-card" style="border-color:var(--border);opacity:0.55;margin-bottom:8px">
        <div class="contractor-header">
          <span class="contractor-icon">${pxIcon('🧰',28)}</span>
          <span class="contractor-name">Do It Yourself</span>
          <span class="contractor-cost" style="color:var(--negative)">Need ⚡${ec} (have ${energy})</span>
        </div>
        <div class="contractor-desc" style="color:var(--negative)">Not enough energy — advance the day to restore.</div>
        <div class="contractor-quality">${energyDots}</div>
      </div>`;

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(upg.icon)} ${upg.name}</div>
    <div class="modal-subtitle">Adds up to +${fmt(upg.value_add)} value · You have ${fmt(upgData.cash)}</div>

    ${diyCard}

    <div style="text-align:center;font-size:11px;color:var(--text-muted);margin-bottom:8px">── or hire a contractor ──</div>

    ${upg.special_contractor ? (() => {
      const sc   = upg.special_contractor;
      const days = contractorDays('premium', upg.energy_cost || 1);
      return `<div class="contractor-card contractor-special" onclick="hireContractor('special')">
        <div class="contractor-special-badge">${pxIcon('⚡',14)} SPECIAL — Guaranteed S+</div>
        <div class="contractor-header">
          <span class="contractor-icon">${pxIcon(sc.icon)}</span>
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
          <span class="contractor-icon">${pxIcon(c.icon)}</span>
          <span class="contractor-name">${c.name}</span>
          <span class="contractor-cost">${fmt(upg.costs[key])}</span>
        </div>
        <div class="contractor-desc">${c.desc}</div>
        <div class="contractor-quality">Grade range: ${c.tier_range || 'F – S+'} · ⏱ ${days} day${days !== 1 ? 's' : ''}</div>
      </div>`;
    }).join('')}
    <button class="btn btn-ghost btn-sm btn-full mt-8" onclick="backToProperty()">Cancel</button>`);
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
  _inPropSubModal = true;
  const tColor    = tierColor(res.quality_tier);
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🧰',20)} DIY Complete!</div>
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
  pendingUpgrade  = null;
  _inPropSubModal = true;
  const d = res.duration;
  const isDeferred = res.deferred_payment;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🔨',20)} Work Underway!</div>
    <div class="modal-subtitle">${res.contractor_name} is on the job</div>
    <div style="text-align:center;padding:16px 0">
      <div>${pxIcon('🏗️',48)}</div>
      <div style="font-size:22px;font-weight:900;margin-top:8px">${d} Day${d !== 1 ? 's' : ''}</div>
      <div style="font-size:13px;color:var(--text-muted)">until completion</div>
    </div>
    ${isDeferred
      ? `<div style="background:#FFF3E0;border:2px solid #E65100;border-radius:var(--radius-sm);padding:10px 12px;margin-bottom:12px;font-size:13px;font-weight:700;color:#E65100">
           ${pxIcon('💸',14)} Payment due when work is complete — come back and pay then.</div>`
      : `<div class="money-row"><span class="mr-label">Cash Remaining</span><span class="mr-value">${fmt(res.cash)}</span></div>`
    }
    <button class="btn btn-primary btn-full mt-8" onclick="closeModal()">Got It</button>`);
  await refreshState();
  renderAll();
}

async function payContractor(propId) {
  const res = await api(`/property/${propId}/pay_contractor`, 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Paid ${fmt(res.amount_paid)} — ${res.upgrade_name} Grade ${res.tier_key}!`, 'success');
  await refreshState();
  renderAll();
  showPropertyDetail(propId);
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
  <div class="card" style="display:flex;align-items:center;gap:14px;opacity:0.6">
    <div style="line-height:1">${pxIcon('💼',34)}</div>
    <div style="flex:1">
      <div style="font-size:15px;font-weight:800">Side Jobs</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:2px">
        🚧 Coming soon — check back later!
      </div>
    </div>
    <button class="btn btn-primary btn-sm" disabled style="opacity:0.4;cursor:not-allowed">
      Locked
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
      <div class="modal-title">${pxIcon('💼',20)} Side Jobs</div>
      <p class="text-muted" style="text-align:center;padding:16px 0">No jobs available — advance the day for fresh listings.</p>
      <button class="btn btn-ghost btn-full" onclick="closeModal()">Close</button>`);
    return;
  }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('💼',20)} Side Jobs</div>
    <div class="modal-subtitle">⚡ ${energy} / ${maxE} energy remaining today</div>
    ${jobs.map(j => {
      const canTake  = energy >= j.energy_cost;
      const minPay   = Math.round(j.base_pay * 0.5);
      const pips     = '⚡'.repeat(j.energy_cost) + '<span style="opacity:0.2">⚡</span>'.repeat(Math.max(0, 4 - j.energy_cost));
      return `
      <div class="card" style="margin-bottom:10px${!canTake ? ';opacity:0.5' : ''}">
        <div class="card-header">
          <div class="card-icon">${pxIcon(j.icon)}</div>
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
    <div class="modal-title">${pxIcon('💼',20)} Job Complete!</div>
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

// ── Business Tab ─────────────────────────────────────────────────────────────
const VM_UPGRADE_META = [
  { key: 'larger_capacity', name: 'Larger Capacity', icon: '📦', cost: 500,  desc: '+2 days per restock cycle.' },
  { key: 'card_reader',     name: 'Card Reader',     icon: '💳', cost: 800,  desc: '+$50/day on top of snack income.' },
  { key: 'premium_slot',    name: 'Premium Slot',    icon: '⭐', cost: 1200, desc: '+25% revenue per cycle.' },
];
const VM_PRICES    = [1200, 2000, 3000, 4200, 5800, 8000];
const VM_LOCATIONS = [
  'Midtown Grocery Entrance', 'Riverside Park', 'Northside Community Center',
  'Westwood Office Lobby', 'Newbay Ferry Terminal', 'Downtown Bus Station',
];
const SNACK_META = {
  cheap:   { name: 'Generic Brand Snacks', icon: '🍬', revenue: 800  },
  mid:     { name: 'Name Brand Snacks',    icon: '🍫', revenue: 2400 },
  premium: { name: 'Artisan Snack Pack',   icon: '🧁', revenue: 4000 },
};

let _bizOpen = { vending: true };

function toggleBiz(id) {
  const wasOpen = !!_bizOpen[id];
  Object.keys(_bizOpen).forEach(k => _bizOpen[k] = false);
  _bizOpen[id] = !wasOpen;
  renderBusiness();
}

function renderBusiness() {
  const el = document.getElementById('page-business');
  if (!el || !state) return;
  const level = state.level || 0;

  const bizDefs = [
    { id: 'vending',    name: 'Vending Machine Entrepreneur', unlockLevel: 3,  icon: 'business-vending',     content: renderVendingContent  },
    { id: 'laundromat', name: 'Dirty Money Laundromat',       unlockLevel: 5,  icon: 'business-laundromat',  content: renderLaundromContent },
    { id: 'carwash',    name: 'Speedy Suds Car Wash',         unlockLevel: 10, icon: null,                   content: null                  },
  ];

  const cards = bizDefs.map(biz => {
    const unlocked = level >= biz.unlockLevel;
    if (!unlocked) {
      return `
        <div style="display:flex;align-items:center;gap:12px;padding:14px;opacity:0.4;background:var(--surface);border:2px solid var(--border);margin-bottom:10px">
          <div style="font-size:18px">🔒</div>
          <div>
            <div style="font-weight:800;font-size:13px">${biz.name}</div>
            <div style="font-size:11px;color:var(--text-muted)">Unlocks at Level ${biz.unlockLevel}</div>
          </div>
        </div>`;
    }
    const isOpen  = !!_bizOpen[biz.id];
    const iconImg = biz.icon
      ? `<img src="/static/icons/${biz.icon}.svg" width="30" height="30" style="image-rendering:pixelated;vertical-align:middle">`
      : `<span style="font-size:22px">💼</span>`;
    const inner   = isOpen && biz.content ? biz.content() : '';
    const headerBg = isOpen ? 'var(--primary)' : 'var(--surface)';
    const headerColor = isOpen ? 'white' : 'inherit';
    const mutedColor  = isOpen ? 'rgba(255,255,255,0.65)' : 'var(--text-muted)';
    return `
      <div style="background:var(--surface);border:2px solid ${isOpen ? 'var(--primary)' : 'var(--border)'};margin-bottom:10px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,0.08)">
        <div onclick="toggleBiz('${biz.id}')" style="display:flex;align-items:center;gap:12px;padding:14px;cursor:pointer;user-select:none;background:${headerBg};color:${headerColor}">
          ${iconImg}
          <div style="flex:1">
            <div style="font-weight:800;font-size:13px">${biz.name}</div>
            <div style="font-size:11px;color:${mutedColor}">Level ${biz.unlockLevel} Business</div>
          </div>
          <div style="font-size:11px;color:${mutedColor}">${isOpen ? '▲' : '▼'}</div>
        </div>
        ${isOpen ? `<div style="padding:0 14px 14px;border-top:2px solid var(--primary)">${inner}</div>` : ''}
      </div>`;
  }).join('');

  el.innerHTML = `<div class="section-header"><span class="section-title">💼 My Businesses</span></div>${cards}`;
}

function renderVendingContent() {
  const vms      = state.vending_machines || [];
  const inv      = state.costpro_inventory || {};
  const vinny    = state.vinny_hired || false;
  const totalInv = (inv.snacks_cheap || 0) + (inv.snacks_mid || 0) + (inv.snacks_premium || 0);

  const invBadges = [['snacks_cheap','Generic'],['snacks_mid','Name Brand'],['snacks_premium','Artisan']]
    .filter(([k]) => (inv[k] || 0) > 0)
    .map(([k, label]) => `<span style="background:var(--surface,var(--card-bg));border:1px solid var(--border);padding:2px 7px;font-size:10px">×${inv[k]} ${label}</span>`)
    .join('');
  const invBar = `
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:10px 0;font-size:12px">
      <span style="color:var(--text-muted)">🎒</span>
      ${totalInv > 0 ? invBadges : `<span style="color:var(--warning);font-size:11px">No snacks — <span style="text-decoration:underline;cursor:pointer" onclick="navTo('store')">visit CostPro</span></span>`}
    </div>`;

  const vmCards = vms.map(vm => {
    const tierMeta       = SNACK_META[vm.snack_tier] || SNACK_META.cheap;
    const canRestock     = vm.status !== 'running' && totalInv > 0;
    const noSnacks       = vm.status !== 'running' && totalInv === 0;
    const installedCount = VM_UPGRADE_META.filter(u => (vm.upgrades || {})[u.key]).length;
    const upgradeLabel   = installedCount === VM_UPGRADE_META.length ? '⭐ Maxed' : `Upgrades (${installedCount}/${VM_UPGRADE_META.length})`;
    const stockPct       = vm.status === 'empty' ? 0 : Math.round((vm.days_remaining / (vm.drain_days || 1)) * 100);
    const barColor       = stockPct > 55 ? 'var(--positive)' : stockPct > 25 ? 'var(--warning)' : 'var(--negative)';
    const stockLabel     = vm.status === 'empty' ? 'Empty' : vm.status === 'low' ? 'Low' : 'Stocked';
    return `
      <div style="border:1px solid var(--border);margin-top:8px;padding:10px">
        <div style="display:flex;align-items:flex-start;gap:10px">
          <img src="/static/icons/business-vending.svg" width="32" height="32" style="image-rendering:pixelated;flex-shrink:0;margin-top:2px">
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">Vending Machine #${vm.slot}</div>
            <div style="font-size:11px;color:var(--text-muted)">📍 ${vm.location}</div>
            <div style="font-size:11px;margin-top:3px">${tierMeta.icon} ${tierMeta.name}</div>
            <div style="margin-top:6px">
              <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);margin-bottom:3px">
                <span>Stock</span><span style="color:${barColor}">${stockLabel}</span>
              </div>
              <div style="background:var(--border);height:6px;width:100%">
                <div style="background:${barColor};height:6px;width:${stockPct}%"></div>
              </div>
            </div>
          </div>
          <div style="text-align:right;flex-shrink:0">
            <div style="font-weight:800;font-size:13px;color:${vm.status !== 'empty' ? 'var(--positive)' : 'var(--text-muted)'}">
              ${vm.status !== 'empty' ? fmt(vm.daily_income) + '/day' : '$0/day'}
            </div>
            <button class="btn btn-sm ${canRestock ? 'btn-primary' : 'btn-ghost'}"
              style="margin-top:4px${vm.status === 'running' ? ';opacity:0.35;cursor:not-allowed' : ''}"
              ${canRestock ? `onclick="showRestockModal(${vm.id})"` : noSnacks ? `onclick="navTo('store')"` : 'disabled'}>
              ${vm.status === 'running' ? 'Full' : noSnacks ? 'Get Snacks' : 'Restock'}
            </button>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" style="margin-top:8px;width:100%;font-size:11px" onclick="showUpgradesModal(${vm.id})">
          🔧 ${upgradeLabel}
        </button>
      </div>`;
  }).join('');

  const nextSlot  = vms.length + 1;
  const buyBtn    = nextSlot <= 6
    ? `<button class="btn btn-primary btn-full" style="margin-top:14px" onclick="showBuyVendingModal()">
         Buy Vending Machine #${nextSlot} — ${fmt(VM_PRICES[nextSlot - 1])}
       </button>`
    : `<div style="text-align:center;font-size:12px;color:var(--text-muted);margin-top:12px;opacity:0.6">All 6 machine slots owned!</div>`;

  const vinnyCard = vms.length > 0 ? `
    <div style="display:flex;align-items:flex-start;gap:12px;padding:12px;border:1px solid var(--border);margin-top:14px">
      <img src="/static/icons/business-vinny.svg" width="40" height="40" style="image-rendering:pixelated;flex-shrink:0">
      <div style="flex:1">
        <div style="font-weight:800">Cousin Vinny</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.5">Auto-restocks your empty machines from your inventory. Charges $200 per restock. If your bag is empty, machines stay empty.</div>
        <div style="font-size:11px;margin-top:5px;color:${vinny ? 'var(--positive)' : 'var(--text-muted)'}">
          ${vinny ? '🟢 On the job' : '⚫ Not hired'}
        </div>
        <button class="btn btn-sm ${vinny ? 'btn-ghost' : 'btn-primary'}" style="margin-top:8px;width:100%" onclick="toggleVinny()">
          ${vinny ? 'Fire Vinny' : 'Hire Vinny — $200/restock'}
        </button>
      </div>
    </div>` : '';

  const empty = vms.length === 0
    ? `<div style="text-align:center;color:var(--text-muted);font-size:12px;padding:14px 0">No machines yet. Buy your first one below!</div>` : '';

  return `${invBar}${vmCards}${empty}${buyBtn}${vinnyCard}`;
}

// ── Dirty Money Laundromat ────────────────────────────────────────────────────
const LAUNDROMAT_MAX_MACHINES    = 12;
const LAUNDROMAT_MACHINE_PRICES  = [15_000, 20_000, 25_000, 30_000, 35_000, 40_000, 45_000, 50_000, 55_000]; // machines 4–12

const LAUNDROMAT_UPGRADES_META = [
  { key: 'heavy_duty',       name: 'Heavy-Duty Motor',  icon: '⚙️',  cost: 2000, desc: 'Breakdown chance 6% → 2%.' },
  { key: 'card_reader',      name: 'Card Reader',        icon: '💳', cost: 1500, desc: '+20% income from this machine.' },
  { key: 'energy_efficient', name: 'Energy Efficient',   icon: '🌿', cost: 1000, desc: 'Soap lasts 10 days instead of 7.' },
];

const LAUNDROMAT_STAFF_META = {
  janitor:   { name: 'Janitor',   icon: '🧹', cost: 175, desc: 'Auto-cleans when cleanliness drops below 75%.' },
  repairman: { name: 'Repairman', icon: '🔧', cost: 225, desc: 'Auto-fixes broken machines every day.' },
};

function renderLaundromContent() {
  const lm = state.laundromat;

  if (!lm) {
    const canAfford = state.cash >= 250000;
    return `
      <div style="text-align:center;padding:16px 0">
        <img src="/static/icons/business-laundromat.svg" width="52" height="52" style="image-rendering:pixelated;margin-bottom:10px">
        <div style="font-weight:800;font-size:14px;margin-bottom:6px">Dirty Money Laundromat</div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:14px;line-height:1.6">
          8 machines · daily income · supplies from CostPro<br>
          Hire staff, buy upgrades, get insurance
        </div>
        <div class="money-row"><span class="mr-label">Purchase Price</span><span class="mr-value" style="color:var(--negative)">${fmt(250000)}</span></div>
        <div class="money-row" style="margin-bottom:14px"><span class="mr-label">Your Cash</span><span class="mr-value">${fmt(state.cash)}</span></div>
        <button class="btn btn-primary btn-full" ${canAfford ? 'onclick="buyLaundromat()"' : 'disabled'}>
          ${canAfford ? 'Buy Laundromat' : 'Need $250,000'}
        </button>
      </div>`;
  }

  // Star rating
  const machineCount = lm.machines.length;
  const working    = lm.machines.filter(m => m.status === 'working').length;
  const broken     = lm.machines.filter(m => m.status === 'broken').length;
  const rawScore   = (working / machineCount) * 0.4 + (lm.cleanliness / 100) * 0.4 + (lm.soap_days > 0 ? 1 : 0) * 0.2;
  const stars      = Math.max(1, Math.min(5, Math.ceil(rawScore * 5)));
  const starStr    = '★'.repeat(stars) + '☆'.repeat(5 - stars);
  const starColor  = stars >= 4 ? 'var(--positive)' : stars >= 3 ? 'var(--warning)' : 'var(--negative)';

  // Cleanliness bar
  const cleanColor = lm.cleanliness > 60 ? 'var(--positive)' : lm.cleanliness > 30 ? 'var(--warning)' : 'var(--negative)';
  const cleanBar   = `
    <div style="margin:10px 0">
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);margin-bottom:3px">
        <span>Cleanliness</span><span style="color:${cleanColor}">${lm.cleanliness}%</span>
      </div>
      <div style="background:var(--border);height:6px">
        <div style="background:${cleanColor};height:6px;width:${lm.cleanliness}%"></div>
      </div>
    </div>`;

  // Regulars bar
  const regBonus = Math.round(lm.regulars * 0.25);
  const regColor = lm.regulars > 60 ? 'var(--positive)' : lm.regulars > 20 ? 'var(--warning)' : 'var(--text-muted)';
  const regBar   = `
    <div style="margin:6px 0 12px">
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);margin-bottom:3px">
        <span>Regulars</span><span style="color:${regColor}">${lm.regulars}/100 (+${regBonus}% income)</span>
      </div>
      <div style="background:var(--border);height:6px">
        <div style="background:${regColor};height:6px;width:${lm.regulars}%"></div>
      </div>
    </div>`;

  // Status summary
  const soapLabel = lm.soap_days > 0 ? `${lm.soap_days}d soap` : 'OUT OF SOAP';
  const soapColor = lm.soap_days > 0 ? 'var(--positive)' : 'var(--negative)';
  const statusRow = `
    <div style="display:flex;flex-wrap:wrap;gap:8px;font-size:11px;margin-bottom:10px;align-items:center">
      <span style="color:${starColor};font-size:13px">${starStr}</span>
      <span style="color:var(--text-muted)">|</span>
      <span>${working}/${machineCount} running${broken > 0 ? ` · <span style="color:var(--negative)">${broken} broken</span>` : ''}</span>
      <span style="color:var(--text-muted)">|</span>
      <span style="color:${soapColor}">🧼 ${soapLabel}</span>
    </div>`;

  // Supplies row
  const supRow = `
    <div style="display:flex;flex-wrap:wrap;gap:8px;font-size:11px;margin-bottom:12px">
      <span>🌸 ${lm.softener_days > 0 ? lm.softener_days + 'd' : '—'}</span>
      <span style="color:var(--text-muted)">|</span>
      <span>🌬️ ${lm.sheets_days > 0 ? lm.sheets_days + 'd' : '—'}</span>
      <span style="color:var(--text-muted)">|</span>
      <span style="cursor:pointer;text-decoration:underline;color:var(--accent)" onclick="navTo('store')">Buy Supplies →</span>
    </div>`;

  // Machine grid (3×4) + buy slot
  const hasSoap    = lm.soap_days > 0;
  const canBuyMore   = machineCount < LAUNDROMAT_MAX_MACHINES;
  const machineCells = lm.machines.map(m => {
    const isBroken  = m.status === 'broken';
    const isRunning = !isBroken && hasSoap;
    const upgCount  = Object.keys(m.upgrades || {}).length;
    const bgColor   = isBroken ? 'rgba(244,67,54,0.08)' : 'transparent';
    const border    = isBroken ? 'var(--negative)' : 'var(--border)';
    const animClass = isBroken ? 'machine-broken' : isRunning ? 'machine-running' : 'machine-idle';
    const onclick   = isBroken
      ? `showLaundroRepairModal(${m.id})`
      : `showLaundroMachineUpgradesModal(${m.id})`;
    return `<div onclick="${onclick}" style="border:1px solid ${border};padding:7px 4px;text-align:center;cursor:pointer;background:${bgColor}">
      <img src="/static/icons/business-laundromat.svg" class="${animClass}" width="30" height="30" style="image-rendering:pixelated">
      <div style="font-size:9px;color:var(--text-muted);margin-top:2px">#${m.id + 1}</div>
      ${isBroken
        ? `<div style="font-size:9px;color:var(--negative);font-weight:800">⚡3</div>`
        : upgCount > 0
          ? `<div style="font-size:9px;color:var(--positive)">⭐${upgCount}</div>`
          : '<div style="font-size:9px"> </div>'}
    </div>`;
  });
  if (canBuyMore) {
    const priceIdx   = machineCount - 3;  // 3 = start machines
    const nextPrice  = LAUNDROMAT_MACHINE_PRICES[priceIdx] ?? LAUNDROMAT_MACHINE_PRICES[LAUNDROMAT_MACHINE_PRICES.length - 1];
    const affordable = state.cash >= nextPrice;
    machineCells.push(`
      <div onclick="${affordable ? 'buyLaundroMachine()' : ''}"
        style="border:1px dashed var(--border);padding:7px 4px;text-align:center;cursor:${affordable ? 'pointer' : 'default'};opacity:${affordable ? '1' : '0.5'}">
        <div style="font-size:20px;line-height:1;margin-bottom:2px">＋</div>
        <div style="font-size:8px;color:var(--text-muted)">${fmt(nextPrice)}</div>
        <div style="font-size:8px;color:var(--text-muted)">#${machineCount + 1}</div>
      </div>`);
  }
  const machineGrid = `
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-bottom:12px">
      ${machineCells.join('')}
    </div>`;

  // Action row
  const insColor  = lm.insurance ? 'var(--positive)' : 'var(--text-muted)';
  const actionRow = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
      <button class="btn btn-sm btn-primary" onclick="showLaundroCleanModal()">🧽 Clean — $75 · ⚡6</button>
      <button class="btn btn-sm ${lm.insurance ? 'btn-ghost' : 'btn-ghost'}" onclick="toggleLaundroInsurance()"
        style="border-color:${insColor};color:${insColor}">
        🛡️ Insurance ${lm.insurance ? 'ON' : 'OFF'}
      </button>
    </div>`;

  // Staff cards
  const staffCards = Object.entries(LAUNDROMAT_STAFF_META).map(([role, meta]) => {
    const hired = (lm.staff || {})[role] || false;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);margin-bottom:6px">
        <div style="font-size:20px">${meta.icon}</div>
        <div style="flex:1">
          <div style="font-weight:800;font-size:12px">${meta.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${meta.desc}</div>
          <div style="font-size:10px;margin-top:2px;color:${hired ? 'var(--positive)' : 'var(--text-muted)'}">
            ${hired ? `🟢 On the job — $${meta.cost}/day` : '⚫ Not hired'}
          </div>
        </div>
        <button class="btn btn-sm ${hired ? 'btn-ghost' : 'btn-primary'}" onclick="toggleLaundroStaff('${role}')">
          ${hired ? 'Fire' : `Hire — $${meta.cost}/day`}
        </button>
      </div>`;
  }).join('');

  const footer = `<div style="font-size:11px;color:var(--text-muted);margin-top:8px;text-align:right">Total Earned: ${fmt(lm.total_earned || 0)}</div>`;

  return `${cleanBar}${regBar}${statusRow}${supRow}${machineGrid}${actionRow}
    <div style="font-size:11px;font-weight:800;margin-bottom:8px">👷 Staff</div>
    ${staffCards}${footer}`;
}

async function buyLaundromat() {
  const res = await api('/laundromat/buy', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Dirty Money Laundromat purchased! Buy soap from CostPro to get started.', 'success');
}

function showLaundroCleanModal() {
  const lm        = state.laundromat;
  const newClean  = Math.min(100, (lm.cleanliness || 0) + 30);
  const hasEnergy = (state.energy ?? 0) >= 6;
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;margin-bottom:14px">🧽 Deep Clean</div>
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:14px;line-height:1.5">Scrub the floors, wipe the machines, freshen the place up. Adds +30% cleanliness.</div>
    <div class="money-row"><span class="mr-label">Cleanliness Now</span><span class="mr-value">${lm.cleanliness}%</span></div>
    <div class="money-row"><span class="mr-label">After Cleaning</span><span class="mr-value" style="color:var(--positive)">${newClean}%</span></div>
    <div class="money-row"><span class="mr-label">Cost</span><span class="mr-value" style="color:var(--negative)">$75</span></div>
    <div class="money-row" style="margin-bottom:14px">
      <span class="mr-label">Energy</span>
      <span class="mr-value" style="color:${hasEnergy ? 'var(--positive)' : 'var(--negative)'}">
        ⚡ 6 &nbsp;(you have ${state.energy ?? 0})
      </span>
    </div>
    <button class="btn btn-primary btn-full" ${hasEnergy ? 'onclick="doLaundroClean()"' : 'disabled'}>
      ${hasEnergy ? 'Clean Now' : 'Not Enough Energy'}
    </button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Cancel</button>`);
}

async function doLaundroClean() {
  closeModal();
  const res = await api('/laundromat/clean', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Laundromat scrubbed clean! +30% cleanliness.', 'success');
}

function showLaundroRepairModal(machineId) {
  const lm        = state.laundromat;
  const cost      = lm.insurance ? 0 : 150;
  const curEnergy = state.energy ?? 0;
  const hasEnergy = curEnergy >= 3;
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;margin-bottom:6px">🔧 Repair Machine #${machineId + 1}</div>
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:14px">This machine broke down and needs repairs before it can earn again.</div>
    <div style="background:${hasEnergy ? 'rgba(76,175,80,0.1)' : 'rgba(244,67,54,0.1)'};border:1px solid ${hasEnergy ? 'var(--positive)' : 'var(--negative)'};padding:10px 12px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:12px;font-weight:800">⚡ Energy Cost</span>
      <span style="font-size:13px;font-weight:800;color:${hasEnergy ? 'var(--positive)' : 'var(--negative)'}">3 &nbsp;(you have ${curEnergy})</span>
    </div>
    <div class="money-row" style="margin-bottom:14px">
      <span class="mr-label">Repair Cost</span>
      <span class="mr-value" style="color:${cost === 0 ? 'var(--positive)' : 'var(--negative)'}">
        ${cost === 0 ? 'FREE (insurance)' : fmt(cost)}
      </span>
    </div>
    <button class="btn btn-primary btn-full" ${hasEnergy ? `onclick="doLaundroRepair(${machineId})"` : 'disabled'}>
      ${hasEnergy ? 'Repair — ⚡3' : 'Not Enough Energy'}
    </button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Cancel</button>`);
}

async function doLaundroRepair(machineId) {
  closeModal();
  const res = await api('/laundromat/repair_machine', 'POST', { machine_id: machineId });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Machine repaired and back online!', 'success');
}

function showLaundroMachineUpgradesModal(machineId) {
  const lm      = state.laundromat;
  const machine = lm.machines.find(m => m.id === machineId);
  if (!machine) return;
  const upgrades = machine.upgrades || {};
  const rows = LAUNDROMAT_UPGRADES_META.map(u => {
    const owned     = !!upgrades[u.key];
    const canAfford = state.cash >= u.cost;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);margin-bottom:8px${owned ? ';opacity:0.55' : ''}">
        <div style="font-size:22px">${u.icon}</div>
        <div style="flex:1">
          <div style="font-weight:800;font-size:12px">${u.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${u.desc}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          ${owned
            ? `<span style="font-size:11px;color:var(--positive)">✓ Installed</span>`
            : `<div style="font-size:12px;font-weight:800">${fmt(u.cost)}</div>
               <button class="btn btn-sm btn-primary" style="margin-top:2px"
                 ${!canAfford ? 'disabled' : `onclick="doLaundroUpgrade(${machineId},'${u.key}')"`}>
                 ${canAfford ? 'Install' : 'Need Cash'}
               </button>`}
        </div>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <div style="font-size:28px">⚙️</div>
      <div>
        <div style="font-weight:800;font-size:15px">Machine #${machineId + 1} Upgrades</div>
        <div style="font-size:11px;color:var(--text-muted)">Dirty Money Laundromat</div>
      </div>
    </div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Close</button>`);
}

async function doLaundroUpgrade(machineId, upgradeKey) {
  closeModal();
  const res = await api('/laundromat/upgrade_machine', 'POST', { machine_id: machineId, upgrade_key: upgradeKey });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Upgrade installed!', 'success');
}

async function toggleLaundroInsurance() {
  const res = await api('/laundromat/insurance', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  const on = state.laundromat?.insurance;
  toast(on ? 'Insurance activated — $400/week, free repairs!' : 'Insurance cancelled.', 'info');
}

async function toggleLaundroStaff(role) {
  const res = await api('/laundromat/hire_staff', 'POST', { role });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  const hired = state.laundromat?.staff?.[role];
  const name  = LAUNDROMAT_STAFF_META[role]?.name || role;
  toast(hired ? `${name} is on the job!` : `${name} let go.`, 'info');
}

async function buyLaundroMachine() {
  const res = await api('/laundromat/buy_machine', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  const count = state.laundromat?.machines?.length || 0;
  toast(`Machine #${count} added to the laundromat!`, 'success');
}

function showBuyVendingModal() {
  const vms      = state.vending_machines || [];
  const inv      = state.costpro_inventory || {};
  const slot     = vms.length + 1;
  if (slot > 6) return;
  const price    = VM_PRICES[slot - 1];
  const location = VM_LOCATIONS[slot - 1];
  const totalInv = (inv.snacks_cheap || 0) + (inv.snacks_mid || 0) + (inv.snacks_premium || 0);

  const tierRows = Object.entries(SNACK_META).map(([key, meta]) => {
    const qty = inv[`snacks_${key}`] || 0;
    return `
      <div style="${qty === 0 ? 'opacity:0.4;' : ''}display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);margin-bottom:8px">
        <div style="font-size:22px">${meta.icon}</div>
        <div style="flex:1">
          <div style="font-weight:800;font-size:12px">${meta.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">→ ${fmt(meta.revenue)}/cycle · ×${qty} in bag</div>
        </div>
        <button class="btn btn-sm btn-primary" ${qty === 0 ? 'disabled' : `onclick="buyVendingMachine('${key}')"`}>Select</button>
      </div>`;
  }).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <img src="/static/icons/business-vending.svg" width="44" height="44" style="image-rendering:pixelated;flex-shrink:0">
      <div>
        <div style="font-weight:800;font-size:15px">Buy Vending Machine #${slot}</div>
        <div style="font-size:11px;color:var(--text-muted)">📍 ${location}</div>
      </div>
    </div>
    <div class="money-row"><span class="mr-label">Purchase Price</span><span class="mr-value" style="color:var(--negative)">${fmt(price)}</span></div>
    <div class="money-row" style="margin-bottom:14px"><span class="mr-label">Your Cash</span><span class="mr-value">${fmt(state.cash)}</span></div>
    <div style="font-weight:800;font-size:12px;margin-bottom:8px">Choose what to stock it with:</div>
    ${totalInv === 0
      ? `<div style="text-align:center;padding:14px;font-size:12px;color:var(--warning)">No snacks in bag!<br><button class="btn btn-sm btn-primary" style="margin-top:8px" onclick="closeModal();navTo('store')">Go to CostPro</button></div>`
      : tierRows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Cancel</button>`);
}

function showRestockModal(vmId) {
  const vm  = (state.vending_machines || []).find(v => v.id === vmId);
  const inv = state.costpro_inventory || {};
  if (!vm) return;
  const rows = Object.entries(SNACK_META).map(([key, meta]) => {
    const qty = inv[`snacks_${key}`] || 0;
    return `
      <div style="${qty === 0 ? 'opacity:0.4;' : ''}display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);margin-bottom:8px">
        <div style="font-size:22px">${meta.icon}</div>
        <div style="flex:1">
          <div style="font-weight:800;font-size:12px">${meta.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">→ ${fmt(meta.revenue)}/cycle · ×${qty} in bag</div>
        </div>
        <button class="btn btn-sm btn-primary" ${qty === 0 ? 'disabled' : `onclick="restockMachine(${vmId},'${key}')"`}>Use</button>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <img src="/static/icons/business-vending.svg" width="40" height="40" style="image-rendering:pixelated;flex-shrink:0">
      <div>
        <div style="font-weight:800;font-size:15px">Restock Machine #${vm.slot}</div>
        <div style="font-size:11px;color:var(--text-muted)">📍 ${vm.location}</div>
      </div>
    </div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Cancel</button>`);
}

async function buyVendingMachine(snackTier) {
  closeModal();
  const res = await api('/vending/buy', 'POST', { snack_tier: snackTier });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Vending machine purchased!', 'success');
}

async function restockMachine(vmId, snackTier) {
  closeModal();
  const res = await api('/vending/restock', 'POST', { vm_id: vmId, snack_tier: snackTier });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Machine restocked!', 'success');
}

async function toggleVinny() {
  const res = await api('/vending/toggle_vinny', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(state.vinny_hired ? 'Cousin Vinny is on the job!' : 'Vinny has been let go.', 'info');
}

function showUpgradesModal(vmId) {
  const vm       = (state.vending_machines || []).find(v => v.id === vmId);
  if (!vm) return;
  const upgrades = vm.upgrades || {};
  const rows = VM_UPGRADE_META.map(u => {
    const owned     = !!upgrades[u.key];
    const canAfford = state.cash >= u.cost;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);margin-bottom:8px${owned ? ';opacity:0.55' : ''}">
        <div style="font-size:22px">${u.icon}</div>
        <div style="flex:1">
          <div style="font-weight:800;font-size:12px">${u.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${u.desc}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          ${owned
            ? `<span style="font-size:11px;color:var(--positive)">✓ Installed</span>`
            : `<div style="font-size:12px;font-weight:800">${fmt(u.cost)}</div>
               <button class="btn btn-sm btn-primary" style="margin-top:2px" ${!canAfford ? 'disabled' : `onclick="buyVmUpgrade(${vmId},'${u.key}')"`}>
                 ${canAfford ? 'Install' : 'Need Cash'}
               </button>`}
        </div>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <img src="/static/icons/business-vending.svg" width="40" height="40" style="image-rendering:pixelated;flex-shrink:0">
      <div>
        <div style="font-weight:800;font-size:15px">Machine #${vm.slot} Upgrades</div>
        <div style="font-size:11px;color:var(--text-muted)">📍 ${vm.location}</div>
      </div>
    </div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Close</button>`);
}

async function buyVmUpgrade(vmId, upgradeKey) {
  closeModal();
  const res = await api('/vending/upgrade', 'POST', { vm_id: vmId, upgrade_key: upgradeKey });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Upgrade installed!', 'success');
}

// ── CostPro Wholesale Store ───────────────────────────────────────────────────
const COSTPRO_SNACKS = [
  { key: 'snacks_cheap',   name: 'Generic Brand Snacks', icon: '🍬', price: 400,   desc: 'Budget snacks. They sell, barely.',            revenue: 800   },
  { key: 'snacks_mid',     name: 'Name Brand Snacks',    icon: '🍫', price: 800,   desc: 'Popular brands. Solid margins.',               revenue: 2400  },
  { key: 'snacks_premium', name: 'Artisan Snack Pack',   icon: '🧁', price: 1200,  desc: "Fancy stuff. Customers pay a premium for it.", revenue: 4000  },
];

const COSTPRO_LAUNDRY = [
  { key: 'soap',     name: 'Laundry Soap',    icon: '🧼', price: 300, desc: 'Required to operate. Lasts 7 days per case (10 with Energy Efficient upgrade).' },
  { key: 'softener', name: 'Fabric Softener', icon: '🌸', price: 500, desc: '+20% daily income. Lasts 10 days per case.' },
  { key: 'sheets',   name: 'Dryer Sheets',    icon: '🌬️', price: 400, desc: '+15% daily income. Lasts 10 days per case.' },
];

const STORE_UNLOCK_LEVEL = 3;

function renderStore() {
  const el  = document.getElementById('page-store');
  if (!el || !state) return;

  if ((state.level || 0) < STORE_UNLOCK_LEVEL) {
    el.innerHTML = `
      <div style="background:var(--primary);color:white;text-align:center;padding:14px 16px">
        <div style="font-family:'Rubik Dirt',cursive;font-size:22px;letter-spacing:2px">CostPro</div>
        <div style="font-size:10px;opacity:0.75;letter-spacing:3px;margin-top:2px">WHOLESALE · BULK · SAVINGS</div>
      </div>
      <div style="text-align:center;padding:48px 24px 32px">
        <div style="font-size:48px;margin-bottom:12px">${pxIcon('🔒',48)}</div>
        <div style="font-size:17px;font-weight:900;color:var(--text);margin-bottom:6px">Store Locked</div>
        <div style="font-size:13px;color:var(--text-muted);line-height:1.5">CostPro unlocks at <strong>Level ${STORE_UNLOCK_LEVEL}</strong> alongside the Business tab.<br>Keep growing your portfolio to unlock bulk supplies.</div>
        <div style="margin-top:20px;background:var(--surface);border:2px solid var(--border);border-radius:10px;padding:14px">
          <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:8px">Unlocks at Level ${STORE_UNLOCK_LEVEL}</div>
          <div style="font-size:12px;color:var(--text);line-height:1.8">🏪 Vending Machine business<br>🍬 Snack inventory — stock your machines<br>🌸 Laundry supplies (when laundromat is owned)</div>
        </div>
      </div>`;
    return;
  }

  const inv  = state.costpro_inventory || {};
  const lm   = state.laundromat;

  const snackCards = COSTPRO_SNACKS.map(item => {
    const held = inv[item.key] || 0;
    return `
    <div class="card" style="margin-bottom:10px">
      <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
        <div style="font-size:28px;line-height:1">${item.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:13px">${item.name}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:1px">${item.desc}</div>
          <div style="font-size:11px;margin-top:3px">
            → <span style="color:var(--positive)">${fmt(item.revenue)}</span> per vending cycle
            · In bag: <strong>${held}</strong>
          </div>
        </div>
        <div style="font-size:15px;font-weight:800;color:var(--primary);flex-shrink:0">${fmt(item.price)}<div style="font-size:10px;font-weight:400;color:var(--text-muted);text-align:right">each</div></div>
      </div>
      <div style="display:flex;gap:6px">
        <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',1)">Buy 1</button>
        <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',3)">Buy 3 · ${fmt(item.price*3)}</button>
        <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',5)">Buy 5 · ${fmt(item.price*5)}</button>
      </div>
    </div>`;
  }).join('');

  // Laundry supplies — only shown when laundromat is owned
  let laundrySection = '';
  if (lm) {
    const laundryCards = COSTPRO_LAUNDRY.map(item => {
      const currentDays = item.key === 'soap'
        ? (lm.soap_days || 0)
        : item.key === 'softener'
          ? (lm.softener_days || 0)
          : (lm.sheets_days || 0);
      return `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
          <div style="font-size:28px;line-height:1">${item.icon}</div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">${item.name}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:1px">${item.desc}</div>
            <div style="font-size:11px;margin-top:3px;color:${currentDays > 0 ? 'var(--positive)' : 'var(--warning)'}">
              ${currentDays > 0 ? `${currentDays} days remaining` : item.key === 'soap' ? '⚠️ OUT — machines idle!' : 'None stocked'}
            </div>
          </div>
          <div style="font-size:15px;font-weight:800;color:var(--primary);flex-shrink:0">${fmt(item.price)}<div style="font-size:10px;font-weight:400;color:var(--text-muted);text-align:right">each</div></div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',1)">Buy 1</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',3)">Buy 3 · ${fmt(item.price*3)}</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',5)">Buy 5 · ${fmt(item.price*5)}</button>
        </div>
      </div>`;
    }).join('');
    laundrySection = `
      <div class="section-header" style="margin-top:14px">
        <span class="section-title">🧺 Laundromat Supplies</span>
      </div>
      ${laundryCards}`;
  }

  el.innerHTML = `
    <div style="background:var(--primary);color:white;text-align:center;padding:14px 16px">
      <div style="font-family:'Rubik Dirt',cursive;font-size:22px;letter-spacing:2px">CostPro</div>
      <div style="font-size:10px;opacity:0.75;letter-spacing:3px;margin-top:2px">WHOLESALE · BULK · SAVINGS</div>
    </div>
    <div class="section-header" style="margin-top:14px">
      <span class="section-title">🍬 Vending Supplies</span>
    </div>
    ${snackCards}
    ${laundrySection}
    <div style="font-size:11px;color:var(--text-muted);text-align:center;padding:8px 0 16px">
      More products unlock with new businesses.
    </div>`;
}

async function buySnacks(itemKey, qty) {
  const res = await api('/costpro/buy', 'POST', { item_key: itemKey, qty });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderStore();
  renderBusiness();
  toast(`×${qty} purchased!`, 'success');
}

// ── Mini-game: Quick Tap ──────────────────────────────────────────────────────
// 8 targets appear one at a time. Each shrinks over 1.5s. Tap/click to score.
function launchQuickTap(upgradeKey) {
  _mg = { ..._mg, hits: 0, total: 8, current: 0, active: false, upgradeKey };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap" style="background:#3E2723">
      <div class="mg-title" style="color:#FFCC80">${pxIcon('🔨',20)} Drive the Nails!</div>
      <div class="mg-desc" style="color:#BCAAA4">Tap each nail before it sinks into the wood! 8 nails total.</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#FFAB40" id="qt-hits">0</div><div style="color:#A1887F;font-size:11px">Driven</div></div>
        <div><div class="mg-stat-val" style="color:#FFAB40" id="qt-left">8</div><div style="color:#A1887F;font-size:11px">Left</div></div>
      </div>
      <div class="mg-tap-area" id="qt-area" style="background:#5D4037;border-color:#4E342E"></div>
    </div>
    <button class="btn btn-full" id="qt-start-btn" onclick="qtStart()" style="background:#FF8F00;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">${pxIcon('🔨',16)} Grab the Hammer</button>`);
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
      <div class="mg-title">${pxIcon('🔧',20)} Tighten the Fitting</div>
      <div class="mg-desc">Stop the dial in the green zone — perfect tension or it'll leak! 5 rounds, gets trickier.</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" id="ss-round">1</div><div style="font-size:11px">Round</div></div>
        <div><div class="mg-stat-val" id="ss-score">—</div><div style="font-size:11px">Pressure</div></div>
      </div>
      <div class="mg-bar-wrap" id="ss-bar" style="background:#CFD8DC">
        <div class="mg-zone"  id="ss-zone"></div>
        <div class="mg-needle" id="ss-needle" style="background:#E65100;width:8px"></div>
      </div>
      <button class="mg-lock-btn" id="ss-btn" onclick="ssLock()" style="display:none;background:#BF360C;letter-spacing:2px">${pxIcon('🔒',16)} LOCK TENSION!</button>
    </div>
    <button class="btn btn-primary btn-full" id="ss-start-btn" onclick="ssStart()">${pxIcon('🔧',16)} Pick Up the Wrench</button>`);
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
      <div class="mg-title" style="color:#FFD54F">${pxIcon('⚡',20)} Wire It Up!</div>
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
    <button class="btn btn-full" id="seq-start-btn" onclick="seqStart()" style="background:#F57F17;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">${pxIcon('⚡',16)} Open the Panel</button>`);
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

const PG_COLS     = 8;
const PG_ROWS     = 10;
const PG_TOTAL    = PG_COLS * PG_ROWS;  // 80 tiles
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
        <span class="pg-title">${pxIcon('🎨',20)} Paint the Wall!</span>
        <span class="pg-pct-badge" id="pg-pct">0%</span>
      </div>
      <div class="pg-timer-track">
        <div class="pg-timer-fill" id="pg-timer-fill"></div>
      </div>
      <div class="pg-time-label"><span id="pg-time">${PG_DURATION}</span>s remaining</div>
    </div>
    <div class="pg-wall-wrap">
      <div class="pg-baseboard pg-baseboard-top"></div>
      <div class="pg-grid" id="pg-grid"></div>
      <div class="pg-baseboard pg-baseboard-bottom"></div>
    </div>
    <div class="pg-start-screen" id="pg-start-screen">
      <div class="pg-start-card">
        <div class="pg-start-swatch" style="background:${paintColor.color}"></div>
        <div class="pg-start-color">${paintColor.name}</div>
        <div class="pg-start-desc">Drag your finger across the whole wall<br>before time runs out!</div>
        <button class="pg-start-btn" style="background:${paintColor.color};box-shadow:0 4px 18px ${paintColor.dark}88" onclick="pgStart()">
          ${pxIcon('🎨',16)} Start Painting!
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
        <div class="pg-result-tiles">${painted} / ${PG_TOTAL} wall sections painted</div>
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
        <span class="lg-title">${pxIcon('🌿',20)} Pull the Weeds!</span>
        <span class="lg-count" id="lg-count">${pxIcon('🌿',16)} 0</span>
      </div>
      <div class="lg-timer-track">
        <div class="lg-timer-fill" id="lg-timer-fill"></div>
      </div>
      <div class="lg-time-label"><span id="lg-time">${LG_DURATION}</span>s remaining</div>
    </div>
    <div class="lg-field" id="lg-field"></div>
    <div class="lg-start-screen" id="lg-start-screen">
      <div class="lg-start-card">
        <div class="lg-start-icon">${pxIcon('🌿',48)}</div>
        <div class="lg-start-title">Pull the Weeds!</div>
        <div class="lg-start-desc">Tap every weed as fast as you can<br>before they take over the yard!</div>
        <button class="lg-start-btn" onclick="lgStart()">${pxIcon('🌿',16)} Let's Go!</button>
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
const FG_COLS     = 8;
const FG_ROWS     = 5;
const FG_TOTAL    = FG_COLS * FG_ROWS;  // 40 planks
const FG_DURATION = 10;                 // seconds
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
        <span class="fg-title">${pxIcon('🪵',20)} Lay the Flooring!</span>
        <span class="fg-score" id="fg-score">${pxIcon('🪵',16)} 0 / ${FG_TOTAL}</span>
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
        <div class="fg-start-icon">${pxIcon('🪵',48)}</div>
        <div class="fg-start-title">Lay the Flooring!</div>
        <div class="fg-start-desc">Pick a color from the bottom<br>then tap the matching planks on the board!</div>
        <button class="fg-start-btn" ontouchstart="fgStart();event.preventDefault()" onclick="fgStart()">${pxIcon('🪵',16)} Let's Go!</button>
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

// ── Mini-game: Level the Windows ─────────────────────────────────────────────
// 6 windows slowly tilt off-level on their own. Hold a window to bring it back
// to level. The moment you let go it starts drifting again. Score = average
// levelness of all 6 windows when time runs out.
const WG_COUNT       = 4;
const WG_MAX_TILT    = 38;  // max degrees off level
const WG_LEVEL_SPEED = 60;  // degrees/sec when held (leveling rate)
const WG_DRIFT_BASE  = 12;  // degrees/sec initial drift
const WG_DRIFT_MAX   = 40;  // degrees/sec at end of timer
const WG_DURATION    = 18;  // seconds

function launchWindowGame(upgradeKey) {
  closeModal();

  // 6 windows: random start tilt ±0–7°, random drift direction, slight speed variation
  const windows = Array.from({ length: WG_COUNT }, () => ({
    tilt:  (Math.random() * 7) * (Math.random() < 0.5 ? 1 : -1),
    dir:   Math.random() < 0.5 ? 1 : -1,
    speed: WG_DRIFT_BASE + Math.random() * 4,
    held:  false,
  }));

  _mg = { ..._mg, upgradeKey, windows, rafId: null, timerId: null,
          running: false, startTime: 0, lastFrame: 0,
          locked: true, finalScore: 0, touches: {} };

  const old = document.getElementById('wg-overlay');
  if (old) old.remove();

  let cardsHtml = '';
  for (let i = 0; i < WG_COUNT; i++) {
    cardsHtml += `
      <div class="wg-card" id="wgw-${i}" data-win="${i}">
        <div class="wg-frame-wrap">
          <div class="wg-frame" id="wgf-${i}">
            <div class="wg-pane"></div><div class="wg-pane"></div>
            <div class="wg-pane"></div><div class="wg-pane"></div>
          </div>
        </div>
        <div class="wg-gauge">
          <div class="wg-gauge-tube">
            <div class="wg-center-tick"></div>
            <div class="wg-bubble" id="wgb-${i}"></div>
          </div>
        </div>
      </div>`;
  }

  const overlay = document.createElement('div');
  overlay.id        = 'wg-overlay';
  overlay.className = 'wg-overlay';
  overlay.innerHTML = `
    <div class="wg-header">
      <div class="wg-top-row">
        <span class="wg-title">${pxIcon('🪟',20)} Level the Windows!</span>
        <span class="wg-hint">Hold to level</span>
      </div>
      <div class="wg-timer-track">
        <div class="wg-timer-fill" id="wg-timer-fill"></div>
      </div>
      <div class="wg-time-label"><span id="wg-time">${WG_DURATION}</span>s remaining</div>
    </div>
    <div class="wg-board">${cardsHtml}</div>
    <div class="wg-start-screen" id="wg-start-screen">
      <div class="wg-start-card">
        <div class="wg-start-icon">${pxIcon('🪟',48)}</div>
        <div class="wg-start-title">Level the Windows!</div>
        <div class="wg-start-desc">Hold each window to level it.<br>They won't stay straight for long!</div>
        <button class="wg-start-btn" ontouchstart="wgStart();event.preventDefault()" onclick="wgStart()">${pxIcon('🪟',16)} Let's Go!</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Attach hold/release handlers to each card
  overlay.querySelectorAll('.wg-card').forEach(card => {
    const winId = parseInt(card.dataset.win);
    card.addEventListener('mousedown',  e => { e.preventDefault(); wgHold(winId); });
    card.addEventListener('mouseup',    ()  => wgRelease(winId));
    card.addEventListener('mouseleave', ()  => wgRelease(winId));
    card.addEventListener('touchstart', e => {
      e.preventDefault();
      e.stopPropagation();
      Array.from(e.changedTouches).forEach(t => {
        if (Object.keys(_mg.touches).length >= 2) return; // max 2 fingers
        _mg.touches[t.identifier] = winId;
        wgHold(winId);
      });
    }, { passive: false });
  });

  // Catch finger lifts anywhere on the overlay
  overlay.addEventListener('touchend', e => {
    Array.from(e.changedTouches).forEach(t => {
      const winId = _mg.touches[t.identifier];
      if (winId !== undefined) {
        delete _mg.touches[t.identifier];
        if (!Object.values(_mg.touches).includes(winId)) wgRelease(winId);
      }
    });
  }, { passive: false });

  overlay.addEventListener('touchcancel', e => {
    Array.from(e.changedTouches).forEach(t => {
      const winId = _mg.touches[t.identifier];
      if (winId !== undefined) {
        delete _mg.touches[t.identifier];
        if (!Object.values(_mg.touches).includes(winId)) wgRelease(winId);
      }
    });
  }, { passive: false });
}

function wgHold(winId)    { if (_mg.running && _mg.windows[winId]) _mg.windows[winId].held = true; }
function wgRelease(winId) { if (_mg.windows[winId]) _mg.windows[winId].held = false; }

function wgStart() {
  const ss = document.getElementById('wg-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running   = true;
  _mg.startTime = Date.now();
  _mg.lastFrame = Date.now();
  const endTime = _mg.startTime + WG_DURATION * 1000;

  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (WG_DURATION * 1000);
    const fill  = document.getElementById('wg-timer-fill');
    const timeEl = document.getElementById('wg-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#2196F3' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      cancelAnimationFrame(_mg.rafId);
      _mg.running = false;
      wgFinish();
    }
  }, 50);

  _mg.rafId = requestAnimationFrame(wgLoop);
}

function wgLoop() {
  if (!_mg.running) return;
  const now      = Date.now();
  const dt       = Math.min((now - _mg.lastFrame) / 1000, 0.05); // cap delta
  _mg.lastFrame  = now;
  const progress = Math.min(1, (now - _mg.startTime) / (WG_DURATION * 1000));

  _mg.windows.forEach((win, i) => {
    if (win.held) {
      // Bring tilt toward 0; flip drift direction when it hits centre
      const move    = WG_LEVEL_SPEED * dt;
      const prevDir = Math.sign(win.tilt) || win.dir;
      if (Math.abs(win.tilt) <= move) {
        win.tilt = 0;
        win.dir  = -prevDir; // now drifts the other way on release
      } else {
        win.tilt -= Math.sign(win.tilt) * move;
      }
    } else {
      // Drift away — accelerates as timer runs down
      const speed = WG_DRIFT_BASE + (WG_DRIFT_MAX - WG_DRIFT_BASE) * progress;
      win.tilt += win.dir * speed * dt;
      if (win.tilt >= WG_MAX_TILT)  { win.tilt =  WG_MAX_TILT; }
      if (win.tilt <= -WG_MAX_TILT) { win.tilt = -WG_MAX_TILT; }
    }
    wgUpdateCard(i);
  });

  _mg.rafId = requestAnimationFrame(wgLoop);
}

function wgUpdateCard(i) {
  const win      = _mg.windows[i];
  const frameEl  = document.getElementById(`wgf-${i}`);
  const bubbleEl = document.getElementById(`wgb-${i}`);
  const cardEl   = document.getElementById(`wgw-${i}`);
  if (!frameEl) return;

  frameEl.style.transform = `rotate(${win.tilt}deg)`;

  // Bubble: 50% = centre, shifts ±42% of tube width
  if (bubbleEl) bubbleEl.style.left = `calc(${50 + (win.tilt / WG_MAX_TILT) * 42}% - 10px)`;

  // Color: green near level, yellow getting off, red bad
  const abs   = Math.abs(win.tilt);
  const color = abs < 4 ? '#4CAF50' : abs < 14 ? '#FF9800' : '#F44336';
  if (cardEl) {
    cardEl.style.borderColor = color;
    cardEl.style.boxShadow   = win.held
      ? `0 0 0 3px ${color}, 0 0 18px ${color}55`
      : `0 0 0 1px ${color}55`;
  }
  if (bubbleEl) bubbleEl.style.background = color;
}

function wgFinish() {
  clearInterval(_mg.timerId);
  cancelAnimationFrame(_mg.rafId);
  _mg.locked = false;

  // Score = average levelness across all 6 windows
  const avg   = _mg.windows.reduce((s, w) =>
    s + Math.max(0, 100 - (Math.abs(w.tilt) / WG_MAX_TILT * 100)), 0) / WG_COUNT;
  const score = Math.round(avg);
  _mg.finalScore = score;

  const msg = score >= 90 ? '🌟 Perfectly plumb!'    :
              score >= 70 ? '✅ Looking straight!'     :
              score >= 50 ? '👍 Getting there!'        :
                            '🪟 Crooked as ever...';

  const overlay = document.getElementById('wg-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'wg-result-overlay';
    res.innerHTML = `
      <div class="wg-result-card">
        <div class="wg-result-score">${score}%</div>
        <div class="wg-result-label">average level</div>
        <div class="wg-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }

  _mg.autoCloseId = setTimeout(wgClose, 2400);
}

function wgClose() {
  clearTimeout(_mg.autoCloseId);
  const overlay = document.getElementById('wg-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Run the HVAC Pipe (HVAC) ──────────────────────────────────────
// Drag through a randomly-generated attic maze. A metallic pipe renders as you
// go — straight sections stay straight, corners automatically round into elbows.
// Score = % of solution path completed (100% only if you reach the END).
const HV_COLS     = 5;   // logical maze columns
const HV_ROWS     = 9;   // logical maze rows
const HV_DURATION = 5;   // seconds
const HV_WALL     = 8;   // wall thickness in logical pixels

// ── Maze generation (recursive backtracker) ──────────────────────────────────
function hvGenMaze(rows, cols) {
  const DIRS = { N: [-1,0], S: [1,0], E: [0,1], W: [0,-1] };
  const OPP  = { N:'S', S:'N', E:'W', W:'E' };
  const grid = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => ({ N:true, S:true, E:true, W:true, v:false }))
  );
  function sh(a) {
    for (let i=a.length-1;i>0;i--) {
      const j=0|Math.random()*(i+1); [a[i],a[j]]=[a[j],a[i]];
    }
    return a;
  }
  function carve(r,c) {
    grid[r][c].v = true;
    for (const d of sh(['N','S','E','W'])) {
      const [dr,dc] = DIRS[d];
      const nr=r+dr, nc=c+dc;
      if (nr>=0&&nr<rows&&nc>=0&&nc<cols&&!grid[nr][nc].v) {
        grid[r][c][d] = false;
        grid[nr][nc][OPP[d]] = false;
        carve(nr,nc);
      }
    }
  }
  carve(0,0);
  grid.forEach(row => row.forEach(c => delete c.v));
  return grid;
}

// ── BFS solver (finds shortest path for scoring) ─────────────────────────────
function hvSolve(maze, rows, cols) {
  const DIRS = { N:[-1,0], S:[1,0], E:[0,1], W:[0,-1] };
  const prev = Array.from({length:rows}, () => Array(cols).fill(null));
  const seen = Array.from({length:rows}, () => Array(cols).fill(false));
  seen[0][0] = true;
  const q = [[0,0]];
  outer: while (q.length) {
    const [r,c] = q.shift();
    for (const [d,[dr,dc]] of Object.entries(DIRS)) {
      const nr=r+dr, nc=c+dc;
      if (!maze[r][c][d] && nr>=0&&nr<rows&&nc>=0&&nc<cols&&!seen[nr][nc]) {
        seen[nr][nc] = true;
        prev[nr][nc] = {r,c};
        if (nr===rows-1&&nc===cols-1) break outer;
        q.push([nr,nc]);
      }
    }
  }
  const path = [];
  let r=rows-1, c=cols-1;
  while (true) {
    path.unshift({row:r,col:c});
    const p = prev[r][c];
    if (!p) break;
    r=p.r; c=p.c;
  }
  return path;
}

// ── Launcher ─────────────────────────────────────────────────────────────────
function launchHvacGame(upgradeKey) {
  closeModal();

  const maze     = hvGenMaze(HV_ROWS, HV_COLS);
  const solution = hvSolve(maze, HV_ROWS, HV_COLS);

  _mg = { ..._mg, upgradeKey, maze, solution,
          path: [{row:0,col:0}],
          running:false, timerId:null, startTime:0,
          locked:true, finalScore:0, complete:false,
          logW:0, logH:0 };

  const old = document.getElementById('hv-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id        = 'hv-overlay';
  overlay.className = 'hv-overlay';
  overlay.innerHTML = `
    <div class="hv-header">
      <div class="hv-top-row">
        <span class="hv-title">${pxIcon('🔧',20)} Run the HVAC Pipe!</span>
        <span class="hv-hint">Drag START → END</span>
      </div>
      <div class="hv-timer-track">
        <div class="hv-timer-fill" id="hv-timer-fill"></div>
      </div>
      <div class="hv-time-label"><span id="hv-time">${HV_DURATION}</span>s remaining</div>
    </div>
    <div class="hv-arena" id="hv-arena">
      <canvas id="hv-canvas"></canvas>
    </div>
    <div class="hv-start-screen" id="hv-start-screen">
      <div class="hv-start-card">
        <div class="hv-start-icon">${pxIcon('🔧',48)}</div>
        <div class="hv-start-title">Run the HVAC Pipe!</div>
        <div class="hv-start-desc">Drag through the attic maze to lay pipe<br>from <span style="color:#4CAF50;font-weight:900">START</span> all the way to <span style="color:#FF5722;font-weight:900">END</span>!</div>
        <button class="hv-start-btn" ontouchstart="hvStart();event.preventDefault()" onclick="hvStart()">${pxIcon('🔧',16)} Let's Go!</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Size canvas after layout
  requestAnimationFrame(() => {
    const arena  = document.getElementById('hv-arena');
    const canvas = document.getElementById('hv-canvas');
    if (!arena || !canvas) return;
    const dpr  = window.devicePixelRatio || 1;
    const logW = arena.clientWidth;
    const logH = arena.clientHeight;
    canvas.width  = logW * dpr;
    canvas.height = logH * dpr;
    canvas.style.width  = logW + 'px';
    canvas.style.height = logH + 'px';
    canvas.getContext('2d').scale(dpr, dpr);
    _mg.logW = logW;
    _mg.logH = logH;
    hvRender();
    hvAttachInput(canvas);
  });
}

// ── Geometry helpers ──────────────────────────────────────────────────────────
function hvMetrics() {
  const cW = (_mg.logW - (HV_COLS+1) * HV_WALL) / HV_COLS;
  const cH = (_mg.logH - (HV_ROWS+1) * HV_WALL) / HV_ROWS;
  return {
    cW, cH,
    cx: c => HV_WALL + c*(cW+HV_WALL) + cW/2,   // cell center x
    cy: r => HV_WALL + r*(cH+HV_WALL) + cH/2,   // cell center y
    ox: c => HV_WALL + c*(cW+HV_WALL),           // cell origin x
    oy: r => HV_WALL + r*(cH+HV_WALL),           // cell origin y
  };
}

function hvPixelToCell(px, py) {
  return {
    col: Math.max(0, Math.min(HV_COLS-1, Math.floor(px / (_mg.logW / HV_COLS)))),
    row: Math.max(0, Math.min(HV_ROWS-1, Math.floor(py / (_mg.logH / HV_ROWS)))),
  };
}

// ── Canvas renderer ───────────────────────────────────────────────────────────
function hvRender() {
  const canvas = document.getElementById('hv-canvas');
  if (!canvas || !_mg.logW) return;
  const ctx = canvas.getContext('2d');
  const { cW, cH, cx, cy, ox, oy } = hvMetrics();
  const W = _mg.logW, H = _mg.logH;

  // Attic background (wall color = dark wood beams)
  ctx.fillStyle = '#2c1a06';
  ctx.fillRect(0, 0, W, H);

  // Open cells + open passages between them (passage color)
  ctx.fillStyle = '#1a0f04';
  for (let r=0; r<HV_ROWS; r++) {
    for (let c=0; c<HV_COLS; c++) {
      ctx.fillRect(ox(c), oy(r), cW, cH);
      if (!_mg.maze[r][c].E && c<HV_COLS-1)
        ctx.fillRect(ox(c)+cW, oy(r), HV_WALL, cH);   // east passage gap
      if (!_mg.maze[r][c].S && r<HV_ROWS-1)
        ctx.fillRect(ox(c), oy(r)+cH, cW, HV_WALL);   // south passage gap
    }
  }

  // Subtle wood-grain lines on walls
  ctx.strokeStyle = 'rgba(80,40,8,0.5)';
  ctx.lineWidth = 1;
  for (let y=0; y<H; y+=18) {
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
  }

  // START / END cell tints
  ctx.fillStyle = 'rgba(76,175,80,0.22)';
  ctx.fillRect(ox(0), oy(0), cW, cH);
  ctx.fillStyle = 'rgba(255,87,34,0.22)';
  ctx.fillRect(ox(HV_COLS-1), oy(HV_ROWS-1), cW, cH);

  // ── Pipe path ──
  const path = _mg.path;
  if (path.length >= 2) {
    const pw = Math.min(cW, cH) * 0.44;
    ctx.lineCap  = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(cx(path[0].col), cy(path[0].row));
    for (let i=1; i<path.length; i++)
      ctx.lineTo(cx(path[i].col), cy(path[i].row));

    ctx.lineWidth = pw;        ctx.strokeStyle = '#37474F'; ctx.stroke(); // shadow
    ctx.lineWidth = pw * 0.68; ctx.strokeStyle = '#90A4AE'; ctx.stroke(); // body
    ctx.lineWidth = pw * 0.28; ctx.strokeStyle = '#ECEFF1'; ctx.stroke(); // shine
  }

  // START / END node circles
  const nr = Math.min(cW, cH) * 0.24;
  ctx.fillStyle = '#4CAF50';
  ctx.beginPath(); ctx.arc(cx(0), cy(0), nr, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle = _mg.complete ? '#FFD700' : '#FF5722';
  ctx.beginPath(); ctx.arc(cx(HV_COLS-1), cy(HV_ROWS-1), nr, 0, Math.PI*2); ctx.fill();

  // Labels
  const fs = Math.round(Math.min(cW,cH) * 0.18);
  ctx.font = `900 ${fs}px system-ui,sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#fff';
  ctx.fillText('START', cx(0), cy(0));
  ctx.fillText('END',   cx(HV_COLS-1), cy(HV_ROWS-1));
}

// ── Touch / mouse input ───────────────────────────────────────────────────────
function hvAttachInput(canvas) {
  function canvasXY(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    return { x: clientX - r.left, y: clientY - r.top };
  }

  function tryMove(px, py) {
    if (!_mg.running || _mg.complete) return;
    const { col, row } = hvPixelToCell(px, py);
    const path = _mg.path;
    const last = path[path.length-1];
    if (row===last.row && col===last.col) return;

    // Backtrack support
    if (path.length >= 2) {
      const prev = path[path.length-2];
      if (row===prev.row && col===prev.col) { path.pop(); hvRender(); return; }
    }

    // Must be exactly one step away
    const dr = row-last.row, dc = col-last.col;
    if (Math.abs(dr)+Math.abs(dc) !== 1) return;
    const dir = dr===-1?'N': dr===1?'S': dc===1?'E':'W';
    if (_mg.maze[last.row][last.col][dir]) return; // wall in the way

    // No loops
    if (path.some(p => p.row===row && p.col===col)) return;

    path.push({row,col});

    // Reached the end?
    if (row===HV_ROWS-1 && col===HV_COLS-1) {
      _mg.complete = true;
      hvRender();
      setTimeout(() => { clearInterval(_mg.timerId); _mg.running=false; hvFinish(); }, 400);
      return;
    }
    hvRender();
  }

  canvas.addEventListener('touchstart', e => {
    e.preventDefault();
    const p = canvasXY(e.touches[0].clientX, e.touches[0].clientY);
    // Tap on START resets path
    const {row,col} = hvPixelToCell(p.x,p.y);
    if (row===0&&col===0) { _mg.path=[{row:0,col:0}]; hvRender(); }
    tryMove(p.x, p.y);
  }, {passive:false});
  canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const p = canvasXY(e.touches[0].clientX, e.touches[0].clientY);
    tryMove(p.x, p.y);
  }, {passive:false});

  // Mouse for desktop testing
  let md = false;
  canvas.addEventListener('mousedown', e => {
    md = true;
    const p = canvasXY(e.clientX,e.clientY);
    const {row,col}=hvPixelToCell(p.x,p.y);
    if (row===0&&col===0) { _mg.path=[{row:0,col:0}]; hvRender(); }
    tryMove(p.x,p.y);
  });
  canvas.addEventListener('mousemove', e => {
    if (!md) return;
    const p = canvasXY(e.clientX,e.clientY);
    tryMove(p.x,p.y);
  });
  canvas.addEventListener('mouseup', () => { md=false; });
}

// ── Timer ─────────────────────────────────────────────────────────────────────
function hvStart() {
  const ss = document.getElementById('hv-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running   = true;
  _mg.startTime = Date.now();
  const endTime = _mg.startTime + HV_DURATION * 1000;

  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (HV_DURATION * 1000);
    const fill  = document.getElementById('hv-timer-fill');
    const timeEl = document.getElementById('hv-time');
    if (fill) {
      fill.style.width      = (pct*100).toFixed(1) + '%';
      fill.style.background = pct>0.5 ? '#FF8F00' : pct>0.25 ? '#E65100' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left/1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running=false; hvFinish(); }
  }, 50);
}

// ── Finish / close ────────────────────────────────────────────────────────────
function hvFinish() {
  clearInterval(_mg.timerId);
  _mg.locked = false;

  const solLen = _mg.solution.length;
  const patLen = _mg.path.length;
  const score  = _mg.complete ? 100
    : Math.min(80, Math.round((patLen / solLen) * 100));
  _mg.finalScore = score;

  const msg = score >= 100 ? '🌟 Pipes are flowing!'      :
              score >= 60  ? '✅ Almost made it!'          :
              score >= 30  ? '👍 Making progress!'         :
                             '🔧 Back to trade school...';

  const overlay = document.getElementById('hv-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'hv-result-overlay';
    res.innerHTML = `
      <div class="hv-result-card">
        <div class="hv-result-score">${score}%</div>
        <div class="hv-result-label">${_mg.complete ? 'pipe fully run!' : 'of route completed'}</div>
        <div class="hv-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }
  _mg.autoCloseId = setTimeout(hvClose, 2400);
}

function hvClose() {
  clearTimeout(_mg.autoCloseId);
  const overlay = document.getElementById('hv-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Tighten the Pipe (Plumbing) ───────────────────────────────────
// A burst pipe sprays water. Tap the screen to tighten the wrench around it.
// Each tap rotates the wrench and reduces water pressure. Score = taps / target.
const PL_TARGET   = 80;   // taps for 100%
const PL_DURATION = 8;    // seconds
const PL_MAX_PTCL = 120;  // max water particles on screen

function launchPlumbingGame(upgradeKey) {
  closeModal();

  _mg = { ..._mg, upgradeKey, taps: 0, running: false, timerId: null,
          rafId: null, particles: [], startTime: 0, lastFrame: 0,
          locked: true, finalScore: 0, logW: 0, logH: 0 };

  const old = document.getElementById('pl-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id        = 'pl-overlay';
  overlay.className = 'pl-overlay';
  overlay.innerHTML = `
    <div class="pl-header">
      <div class="pl-top-row">
        <span class="pl-title">${pxIcon('🔧',20)} Tighten the Pipe!</span>
        <span class="pl-taps" id="pl-taps">0 / ${PL_TARGET}</span>
      </div>
      <div class="pl-timer-track">
        <div class="pl-timer-fill" id="pl-timer-fill"></div>
      </div>
      <div class="pl-time-label"><span id="pl-time">${PL_DURATION}</span>s remaining</div>
    </div>
    <div class="pl-arena" id="pl-arena">
      <canvas id="pl-canvas"></canvas>
      <div class="pl-wrench" id="pl-wrench">🔧</div>
      <div class="pl-tap-hint" id="pl-tap-hint">TAP TO TIGHTEN!</div>
    </div>
    <div class="pl-start-screen" id="pl-start-screen">
      <div class="pl-start-card">
        <div class="pl-start-icon">${pxIcon('💧',48)}</div>
        <div class="pl-start-title">Tighten the Pipe!</div>
        <div class="pl-start-desc">Tap as fast as you can to tighten<br>the wrench and stop the burst!</div>
        <button class="pl-start-btn" ontouchstart="plStart();event.preventDefault()" onclick="plStart()">${pxIcon('🔧',16)} Let's Go!</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  // Tap handler on the arena
  const arena = overlay.querySelector('#pl-arena');
  arena.addEventListener('click', plTap);
  arena.addEventListener('touchstart', e => { e.preventDefault(); plTap(); }, { passive: false });

  // Size canvas after layout
  requestAnimationFrame(() => {
    const arenaEl = document.getElementById('pl-arena');
    const canvas  = document.getElementById('pl-canvas');
    if (!arenaEl || !canvas) return;
    const dpr  = window.devicePixelRatio || 1;
    const logW = arenaEl.clientWidth;
    const logH = arenaEl.clientHeight;
    canvas.width  = logW * dpr;
    canvas.height = logH * dpr;
    canvas.style.width  = logW + 'px';
    canvas.style.height = logH + 'px';
    canvas.getContext('2d').scale(dpr, dpr);
    _mg.logW = logW;
    _mg.logH = logH;

    // Position wrench so its HEAD (upper-left ~15% of emoji) sits on the burst.
    // The handle then swings around that fixed pivot as the player taps.
    const headOff = 13; // px offset to head within the 84px emoji
    const wrenchEl = document.getElementById('pl-wrench');
    if (wrenchEl) {
      wrenchEl.style.left            = `calc(50% - ${headOff}px)`;
      wrenchEl.style.top             = `${Math.round(logH * 0.5 - headOff)}px`;
      wrenchEl.style.transformOrigin = `${headOff}px ${headOff}px`;
      wrenchEl.style.transform       = 'rotate(-30deg)';
    }
    plDrawStatic(); // show pipe before game starts
  });
}

// Draw the scene once so the pipe is visible on the start screen
function plDrawStatic() {
  const canvas = document.getElementById('pl-canvas');
  if (!canvas || !_mg.logW) return;
  const ctx = canvas.getContext('2d');
  _mg.particles = [];
  plDrawScene(ctx, _mg.logW, _mg.logH, 1); // pressure = 1 (full burst)
}

function plTap() {
  if (!_mg.running) return;
  _mg.taps = Math.min(PL_TARGET, _mg.taps + 1);

  // Rotate wrench clockwise: -30° → +220° over PL_TARGET taps
  // transform-origin is set to the head/jaw (13px,13px) so it pivots there, not the center
  const angle    = -30 + (_mg.taps / PL_TARGET) * 250;
  const wrenchEl = document.getElementById('pl-wrench');
  if (wrenchEl) wrenchEl.style.transform = `rotate(${angle}deg)`;

  // Update counter
  const tapsEl = document.getElementById('pl-taps');
  if (tapsEl) tapsEl.textContent = `${_mg.taps} / ${PL_TARGET}`;

  // Finished early?
  if (_mg.taps >= PL_TARGET) {
    clearInterval(_mg.timerId);
    cancelAnimationFrame(_mg.rafId);
    _mg.running = false;
    plFinish();
  }
}

function plStart() {
  const ss = document.getElementById('pl-start-screen');
  if (ss) ss.style.display = 'none';
  const hint = document.getElementById('pl-tap-hint');
  if (hint) hint.style.display = 'block';

  _mg.running   = true;
  _mg.startTime = Date.now();
  _mg.lastFrame = Date.now();
  _mg.particles = [];
  const endTime = _mg.startTime + PL_DURATION * 1000;

  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (PL_DURATION * 1000);
    const fill  = document.getElementById('pl-timer-fill');
    const timeEl = document.getElementById('pl-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#2196F3' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      cancelAnimationFrame(_mg.rafId);
      _mg.running = false;
      plFinish();
    }
  }, 50);

  _mg.rafId = requestAnimationFrame(plLoop);
}

function plLoop() {
  const canvas = document.getElementById('pl-canvas');
  if (!canvas || !_mg.logW) return;

  const ctx      = canvas.getContext('2d');
  const now      = Date.now();
  const dt       = Math.min((now - _mg.lastFrame) / 1000, 0.05);
  _mg.lastFrame  = now;
  const pressure = Math.max(0, 1 - (_mg.taps / PL_TARGET));

  // Spawn new water particles — spray left AND right from burst crack
  if (pressure > 0.01) {
    const count = Math.ceil(pressure * 5);
    for (let i = 0; i < count; i++) {
      if (_mg.particles.length < PL_MAX_PTCL) {
        const dir = Math.random() < 0.5 ? -1 : 1; // half go left, half go right
        _mg.particles.push({
          x:     _mg.logW * 0.5 + (Math.random() - 0.5) * 8,
          y:     _mg.logH * 0.5 + (Math.random() - 0.5) * 12,
          vx:    dir * (80 + Math.random() * 220) * pressure,
          vy:    (Math.random() - 0.5) * 60 * pressure,
          life:  1.0,
          decay: 0.018 + Math.random() * 0.022,
          size:  1.5 + Math.random() * 3 * pressure,
        });
      }
    }
  }

  // Update particles
  _mg.particles = _mg.particles.filter(p => {
    p.x   += p.vx * dt;
    p.y   += p.vy * dt;
    p.vy  += 550 * dt;  // gravity px/s²
    p.life -= p.decay;
    return p.life > 0;
  });

  plDrawScene(ctx, _mg.logW, _mg.logH, pressure);

  if (_mg.running) _mg.rafId = requestAnimationFrame(plLoop);
}

function plDrawScene(ctx, W, H, pressure) {
  // Background — dark utility / basement wall
  ctx.fillStyle = '#141c26';
  ctx.fillRect(0, 0, W, H);

  const pipeX = W * 0.5;
  const pipeW = W * 0.13;   // pipe diameter

  // ── Vertical pipe — left-to-right metallic gradient ──
  const pg = ctx.createLinearGradient(pipeX - pipeW/2, 0, pipeX + pipeW/2, 0);
  pg.addColorStop(0,    '#37474F');
  pg.addColorStop(0.2,  '#78909C');
  pg.addColorStop(0.5,  '#CFD8DC');
  pg.addColorStop(0.75, '#90A4AE');
  pg.addColorStop(1,    '#37474F');
  ctx.fillStyle = pg;
  ctx.fillRect(pipeX - pipeW/2, 0, pipeW, H);

  // Pipe end flanges (top + bottom caps)
  const fh = pipeW * 0.75;   // flange height
  const fw = pipeW * 1.5;    // flange width (wider than pipe)
  ctx.fillStyle = '#546E7A';
  ctx.fillRect(pipeX - fw/2, 0,      fw, fh);
  ctx.fillRect(pipeX - fw/2, H - fh, fw, fh);

  // Flange bolts
  ctx.fillStyle = '#B0BEC5';
  [[pipeX - pipeW*0.3, fh/2], [pipeX + pipeW*0.3, fh/2],
   [pipeX - pipeW*0.3, H - fh/2], [pipeX + pipeW*0.3, H - fh/2]].forEach(([bx, by]) => {
    ctx.beginPath(); ctx.arc(bx, by, 3.5, 0, Math.PI*2); ctx.fill();
  });

  // ── Burst crack — vertical zig-zag at pipe center ──
  const crackY  = H * 0.5;
  const crackSz = pipeW * (0.4 + pressure * 0.7);
  ctx.strokeStyle = '#1a252f';
  ctx.lineWidth   = 1.5 + pressure * 2;
  ctx.lineCap     = 'round';
  ctx.beginPath();
  ctx.moveTo(pipeX - pipeW * 0.15, crackY - crackSz * 0.5);
  ctx.lineTo(pipeX + pipeW * 0.1,  crackY + crackSz * 0.1);
  ctx.lineTo(pipeX - pipeW * 0.2,  crackY + crackSz * 0.45);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(pipeX + pipeW * 0.2,  crackY - crackSz * 0.4);
  ctx.lineTo(pipeX - pipeW * 0.05, crackY + crackSz * 0.15);
  ctx.stroke();

  // ── Water particles ──
  ctx.save();
  _mg.particles.forEach(p => {
    ctx.globalAlpha = p.life * 0.9;
    ctx.fillStyle   = `rgb(56,${Math.round(148 + p.life * 60)},${Math.round(200 + p.life * 55)})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
  ctx.restore();

  // ── "Sealed!" label ──
  if (pressure <= 0.01) {
    ctx.fillStyle    = '#4CAF50';
    ctx.font         = `900 ${Math.round(W * 0.07)}px system-ui,sans-serif`;
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('SEALED! 💧', W / 2, H * 0.15);
  }
}

function plFinish() {
  cancelAnimationFrame(_mg.rafId);
  clearInterval(_mg.timerId);
  _mg.locked = false;

  const score    = Math.min(100, Math.round((_mg.taps / PL_TARGET) * 100));
  _mg.finalScore = score;

  const msg = score >= 100 ? '🌟 No more leaks!'       :
              score >= 75  ? '✅ Almost sealed!'        :
              score >= 40  ? '👍 Slowed it down!'       :
                             '💧 Still flooding...';

  const overlay = document.getElementById('pl-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'pl-result-overlay';
    res.innerHTML = `
      <div class="pl-result-card">
        <div class="pl-result-score">${score}%</div>
        <div class="pl-result-label">pipe tightened</div>
        <div class="pl-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
  }
  _mg.autoCloseId = setTimeout(plClose, 2400);
}

function plClose() {
  clearTimeout(_mg.autoCloseId);
  const overlay = document.getElementById('pl-overlay');
  if (!overlay) return;
  overlay.remove();
  finishDIY(_mg.upgradeKey, _mg.finalScore ?? 0);
}

// ── Mini-game: Roof Replacement ───────────────────────────────────────────────
// Phase 1: drag to scrape off old weathered shingles
// Phase 2: tap every bare spot to lay fresh shingles
// One shared timer across both phases; score = new tiles laid / total
const RF_COLS     = 5;
const RF_ROWS     = 8;
const RF_TOTAL    = RF_COLS * RF_ROWS;  // 40 tiles
const RF_DURATION = 8;                  // seconds

function launchRoofGame(upgradeKey) {
  closeModal();
  _mg = {
    locked: true, upgradeKey,
    phase: 1, scraped: 0, laid: 0,
    running: false, dragging: false,
    timerId: null,
  };

  const overlay = document.createElement('div');
  overlay.id = 'rf-overlay';
  overlay.innerHTML = `
    <div class="rf-hud">
      <div class="rf-hud-top">
        <span class="rf-phase-badge" id="rf-phase-badge">⛏ Scrape Old Shingles</span>
        <span class="rf-time-box"><span id="rf-time">${RF_DURATION}</span>s</span>
      </div>
      <div class="rf-timer-track"><div class="rf-timer-fill" id="rf-timer-fill"></div></div>
      <div class="rf-progress" id="rf-progress">Scraped: 0 / ${RF_TOTAL}</div>
    </div>
    <div class="rf-play-area">
      <div class="rf-ridge-row"></div>
      <div id="rf-grid" class="rf-grid"></div>
    </div>
    <div id="rf-start-screen" class="rf-start-screen">
      <div class="rf-start-card">
        <div class="rf-start-icon">${pxIcon('🏚️',48)}</div>
        <div class="rf-start-title">Roof Replacement</div>
        <div class="rf-start-desc">
          <b>Phase 1:</b> Drag your finger to scrape off all the old shingles<br><br>
          <b>Phase 2:</b> Tap every bare spot to lay fresh shingles
        </div>
        <button class="rf-start-btn" id="rf-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  // Build staggered tile rows
  const grid = overlay.querySelector('#rf-grid');
  for (let r = 0; r < RF_ROWS; r++) {
    const row = document.createElement('div');
    row.className = 'rf-row ' + (r % 2 === 0 ? 'rf-row-even' : 'rf-row-odd');
    row.style.zIndex = RF_ROWS - r; // upper rows (ridge) sit on top — like real shingles
    for (let c = 0; c < RF_COLS; c++) {
      const tile = document.createElement('div');
      tile.className = 'rf-tile rf-old';
      tile.dataset.idx = String(r * RF_COLS + c);
      row.appendChild(tile);
    }
    grid.appendChild(row);
  }

  overlay.querySelector('#rf-start-btn').addEventListener('click', rfStart);
}

function rfStart() {
  const ss = document.getElementById('rf-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running = true;

  const overlay = document.getElementById('rf-overlay');
  const grid    = overlay.querySelector('#rf-grid');

  // ── Unified tile handler: scrape in phase 1, lay in phase 2 ──
  function rfHandle(el) {
    if (!_mg.running || !el || !el.classList.contains('rf-tile')) return;
    if (_mg.phase === 1 && el.classList.contains('rf-old')) {
      el.classList.replace('rf-old', 'rf-scraped');
      _mg.scraped++;
      const prog = document.getElementById('rf-progress');
      if (prog) prog.textContent = `Scraped: ${_mg.scraped} / ${RF_TOTAL}`;
      if (_mg.scraped >= RF_TOTAL) rfPhase2();
    } else if (_mg.phase === 2 && el.classList.contains('rf-scraped')) {
      el.classList.replace('rf-scraped', 'rf-new');
      el.classList.add('rf-pop');
      setTimeout(() => el.classList.remove('rf-pop'), 280);
      _mg.laid++;
      const prog = document.getElementById('rf-progress');
      if (prog) prog.textContent = `Laid: ${_mg.laid} / ${RF_TOTAL}`;
      if (_mg.laid >= RF_TOTAL) {
        clearInterval(_mg.timerId);
        _mg.running = false;
        rfFinish();
      }
    }
  }

  // Touch drag (works for both phases — drag is fine for laying too)
  grid.addEventListener('touchstart', e => {
    e.preventDefault();
    _mg.dragging = true;
    Array.from(e.changedTouches).forEach(t =>
      rfHandle(document.elementFromPoint(t.clientX, t.clientY))
    );
  }, { passive: false });

  grid.addEventListener('touchmove', e => {
    e.preventDefault();
    if (!_mg.dragging) return;
    Array.from(e.changedTouches).forEach(t =>
      rfHandle(document.elementFromPoint(t.clientX, t.clientY))
    );
  }, { passive: false });

  grid.addEventListener('touchend', () => { _mg.dragging = false; });

  // Mouse (desktop testing)
  grid.addEventListener('mousedown', e => { _mg.dragging = true; rfHandle(e.target); });
  grid.addEventListener('mousemove', e => { if (_mg.dragging) rfHandle(e.target); });
  document.addEventListener('mouseup', () => { _mg.dragging = false; });

  // Timer
  const endTime = Date.now() + RF_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (RF_DURATION * 1000);
    const fill  = document.getElementById('rf-timer-fill');
    const timeEl = document.getElementById('rf-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#2196F3' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      rfFinish();
    }
  }, 50);
}

function rfPhase2() {
  if (_mg.phase !== 1) return;
  _mg.phase = 2;

  const badge = document.getElementById('rf-phase-badge');
  if (badge) {
    badge.innerHTML = `${pxIcon('🔨',14)} Lay New Shingles`;
    badge.classList.add('rf-badge-new');
  }
  const prog = document.getElementById('rf-progress');
  if (prog) prog.textContent = `Laid: 0 / ${RF_TOTAL}`;

  // Quick flash to signal the phase change
  const overlay = document.getElementById('rf-overlay');
  overlay.classList.add('rf-phase-flash');
  setTimeout(() => overlay.classList.remove('rf-phase-flash'), 350);
}

function rfFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false;
  _mg.locked  = false;

  // Score weights both phases: finishing scrape = 20%, laying tiles = 80%
  const scrapeContrib = (_mg.scraped / RF_TOTAL) * 20;
  const layContrib    = (_mg.laid    / RF_TOTAL) * 80;
  const score = Math.min(100, Math.round(scrapeContrib + layContrib));

  const msg = score >= 100 ? '🌟 Flawless roof job!'    :
              score >= 75  ? '✅ Solid work!'             :
              score >= 40  ? '👍 Most tiles down!'        :
                             '🏚️ Still some bare spots...';

  const overlay = document.getElementById('rf-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'rf-result-overlay';
    res.innerHTML = `
      <div class="rf-result-card">
        <div class="rf-result-score">${score}%</div>
        <div class="rf-result-label">roof completed</div>
        <div class="rf-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
    setTimeout(() => {
      overlay.remove();
      finishDIY(_mg.upgradeKey, score);
    }, 2200);
  } else {
    finishDIY(_mg.upgradeKey, score);
  }
}

// ── Mini-game: Grout the Backsplash ──────────────────────────────────────────
// Canvas game — drag finger along every grout joint between tiles.
// Dark mortar gaps turn to warm grey grout as you cover them.
// Score = segments filled / total segments.
const GR_COLS     = 5;
const GR_ROWS     = 9;
const GR_GROUT    = 13;  // grout line thickness in logical px
const GR_DURATION = 10;  // seconds

function grMakeTileColors() {
  const whites  = ['#F4F0E8', '#EEEADE', '#F1EBE3', '#EAE4D8'];
  const accents = ['#BFCFBF', '#C4D4DF', '#D4C8B4'];  // sage, soft blue, warm beige
  return Array.from({ length: GR_ROWS }, (_, r) =>
    Array.from({ length: GR_COLS }, (_, c) => {
      const i = r * GR_COLS + c;
      return (i % 9 === 4) ? accents[Math.floor(i / 9) % accents.length]
                           : whites[(r + c) % whites.length];
    })
  );
}

function launchGroutGame(upgradeKey) {
  closeModal();
  const hTotal = (GR_ROWS - 1) * GR_COLS;
  const vTotal = GR_ROWS * (GR_COLS - 1);
  const total  = hTotal + vTotal;

  _mg = {
    locked: true, upgradeKey,
    hGrouted: Array.from({ length: GR_ROWS - 1 }, () => new Array(GR_COLS).fill(false)),
    vGrouted: Array.from({ length: GR_ROWS },     () => new Array(GR_COLS - 1).fill(false)),
    total, filled: 0,
    running: false, timerId: null,
    logW: 0, logH: 0,
    tileColors: grMakeTileColors(),
    lastTouch: null,
  };

  const old = document.getElementById('gr-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'gr-overlay';
  overlay.innerHTML = `
    <div class="gr-hud">
      <div class="gr-hud-top">
        <span class="gr-title">${pxIcon('🧱',20)} Grout the Backsplash!</span>
        <span class="gr-time-box"><span id="gr-time">${GR_DURATION}</span>s</span>
      </div>
      <div class="gr-timer-track"><div class="gr-timer-fill" id="gr-timer-fill"></div></div>
      <div class="gr-progress" id="gr-progress">0 / ${total} lines grouted</div>
    </div>
    <div class="gr-arena" id="gr-arena">
      <canvas id="gr-canvas"></canvas>
    </div>
    <div id="gr-start-screen" class="gr-start-screen">
      <div class="gr-start-card">
        <div class="gr-start-icon">${pxIcon('🧱',48)}</div>
        <div class="gr-start-title">Grout the Backsplash</div>
        <div class="gr-start-desc">Drag your finger along every grout line between the tiles before time runs out!</div>
        <button class="gr-start-btn" id="gr-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  // Size canvas to arena after layout
  requestAnimationFrame(() => {
    const arena  = document.getElementById('gr-arena');
    const canvas = document.getElementById('gr-canvas');
    if (!arena || !canvas) return;
    const dpr  = window.devicePixelRatio || 1;
    const rect = arena.getBoundingClientRect();
    _mg.logW = rect.width;
    _mg.logH = rect.height;
    canvas.width  = Math.round(rect.width  * dpr);
    canvas.height = Math.round(rect.height * dpr);
    canvas.style.width  = rect.width  + 'px';
    canvas.style.height = rect.height + 'px';
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    grDraw(ctx);
  });

  document.getElementById('gr-start-btn').addEventListener('click', grStart);

  const arena = overlay.querySelector('#gr-arena');
  arena.addEventListener('touchstart', e => {
    e.preventDefault();
    if (!_mg.running) return;
    Array.from(e.changedTouches).forEach(t => grHandleXY(t.clientX, t.clientY));
  }, { passive: false });
  arena.addEventListener('touchmove', e => {
    e.preventDefault();
    if (!_mg.running) return;
    Array.from(e.changedTouches).forEach(t => grHandleXY(t.clientX, t.clientY));
  }, { passive: false });
  arena.addEventListener('touchend', () => { _mg.lastTouch = null; grRedraw(); });

  arena.addEventListener('mousedown', e => { if (_mg.running) grHandleXY(e.clientX, e.clientY); });
  arena.addEventListener('mousemove', e => { if (_mg.running && (e.buttons & 1)) grHandleXY(e.clientX, e.clientY); });
  arena.addEventListener('mouseup',   () => { _mg.lastTouch = null; grRedraw(); });
}

function grHandleXY(clientX, clientY) {
  const canvas = document.getElementById('gr-canvas');
  if (!canvas || !_mg.logW) return;
  const rect = canvas.getBoundingClientRect();
  const px = clientX - rect.left;
  const py = clientY - rect.top;
  _mg.lastTouch = { px, py };

  const W = _mg.logW, H = _mg.logH;
  const gw = GR_GROUT;
  const tw = (W - (GR_COLS - 1) * gw) / GR_COLS;
  const th = (H - (GR_ROWS - 1) * gw) / GR_ROWS;
  const cellW = tw + gw;
  const cellH = th + gw;

  const cx = Math.floor(px / cellW);
  const cy = Math.floor(py / cellH);
  if (cx < 0 || cy < 0 || cx >= GR_COLS || cy >= GR_ROWS) { grRedraw(); return; }

  const ox = px - cx * cellW;
  const oy = py - cy * cellH;
  const inTileX  = ox < tw;
  const inTileY  = oy < th;
  const inVGrout = ox >= tw && cx < GR_COLS - 1;
  const inHGrout = oy >= th && cy < GR_ROWS - 1;

  let changed = false;

  if (inVGrout && inTileY) {
    if (!_mg.vGrouted[cy][cx]) { _mg.vGrouted[cy][cx] = true; _mg.filled++; changed = true; }
  }
  if (inHGrout && inTileX) {
    if (!_mg.hGrouted[cy][cx]) { _mg.hGrouted[cy][cx] = true; _mg.filled++; changed = true; }
  }
  // Corner intersection — grout both adjacent segments
  if (inVGrout && inHGrout) {
    if (!_mg.vGrouted[cy][cx])   { _mg.vGrouted[cy][cx] = true;   _mg.filled++; changed = true; }
    if (!_mg.hGrouted[cy][cx])   { _mg.hGrouted[cy][cx] = true;   _mg.filled++; changed = true; }
  }

  grRedraw();

  if (changed) {
    const prog = document.getElementById('gr-progress');
    if (prog) prog.textContent = `${_mg.filled} / ${_mg.total} lines grouted`;
    if (_mg.filled >= _mg.total) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      grFinish();
    }
  }
}

function grRedraw() {
  const canvas = document.getElementById('gr-canvas');
  if (!canvas || !_mg.logW) return;
  grDraw(canvas.getContext('2d'));
}

function grDraw(ctx) {
  const W  = _mg.logW, H = _mg.logH;
  const gw = GR_GROUT;
  const tw = (W - (GR_COLS - 1) * gw) / GR_COLS;
  const th = (H - (GR_ROWS - 1) * gw) / GR_ROWS;

  const UNFILLED = '#1A1410';   // dark mortar/adhesive
  const FILLED   = '#B0A490';   // warm light grey grout
  const CORNER   = '#A89E8C';   // slightly darker at intersections

  // 1. Background = unfilled grout / mortar
  ctx.fillStyle = UNFILLED;
  ctx.fillRect(0, 0, W, H);

  // 2. Filled horizontal segments
  ctx.fillStyle = FILLED;
  for (let r = 0; r < GR_ROWS - 1; r++) {
    for (let c = 0; c < GR_COLS; c++) {
      if (_mg.hGrouted[r][c]) {
        ctx.fillRect(c * (tw + gw), r * (th + gw) + th, tw, gw);
      }
    }
  }
  // Filled vertical segments
  for (let r = 0; r < GR_ROWS; r++) {
    for (let c = 0; c < GR_COLS - 1; c++) {
      if (_mg.vGrouted[r][c]) {
        ctx.fillRect(c * (tw + gw) + tw, r * (th + gw), gw, th);
      }
    }
  }

  // 3. Corner intersections — always drawn as filled grout
  ctx.fillStyle = CORNER;
  for (let r = 0; r < GR_ROWS - 1; r++) {
    for (let c = 0; c < GR_COLS - 1; c++) {
      ctx.fillRect(c * (tw + gw) + tw, r * (th + gw) + th, gw, gw);
    }
  }

  // 4. Tiles
  for (let r = 0; r < GR_ROWS; r++) {
    for (let c = 0; c < GR_COLS; c++) {
      const x = c * (tw + gw);
      const y = r * (th + gw);
      // Tile base
      ctx.fillStyle = _mg.tileColors[r][c];
      ctx.fillRect(x, y, tw, th);
      // Gloss highlight (top ~55%)
      const shine = ctx.createLinearGradient(x, y, x, y + th * 0.55);
      shine.addColorStop(0, 'rgba(255,255,255,0.3)');
      shine.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = shine;
      ctx.fillRect(x, y, tw, th * 0.55);
      // Bottom edge shadow (depth / bevel)
      ctx.fillStyle = 'rgba(0,0,0,0.09)';
      ctx.fillRect(x, y + th * 0.78, tw, th * 0.22);
    }
  }

  // 5. Glowing caulk-gun cursor at last touch point
  if (_mg.lastTouch) {
    const { px, py } = _mg.lastTouch;
    ctx.save();
    ctx.shadowColor = 'rgba(255,210,60,0.8)';
    ctx.shadowBlur  = 10;
    ctx.beginPath();
    ctx.arc(px, py, 7, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,220,70,0.95)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();
  }
}

function grStart() {
  const ss = document.getElementById('gr-start-screen');
  if (ss) ss.style.display = 'none';
  _mg.running = true;

  const endTime = Date.now() + GR_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (GR_DURATION * 1000);
    const fill  = document.getElementById('gr-timer-fill');
    const timeEl = document.getElementById('gr-time');
    if (fill) {
      fill.style.width      = (pct * 100).toFixed(1) + '%';
      fill.style.background = pct > 0.5 ? '#2196F3' : pct > 0.25 ? '#FF9800' : '#F44336';
    }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      grFinish();
    }
  }, 50);
}

function grFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false;
  _mg.locked  = false;

  const score = Math.min(100, Math.round((_mg.filled / _mg.total) * 100));
  const msg = score >= 100 ? '🌟 Perfectly grouted!'      :
              score >= 75  ? '✅ Clean lines!'              :
              score >= 40  ? '👍 Getting there!'            :
                             '🧱 Missed a few spots...';

  const overlay = document.getElementById('gr-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'gr-result-overlay';
    res.innerHTML = `
      <div class="gr-result-card">
        <div class="gr-result-score">${score}%</div>
        <div class="gr-result-label">grouted</div>
        <div class="gr-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
    setTimeout(() => {
      overlay.remove();
      finishDIY(_mg.upgradeKey, score);
    }, 2200);
  } else {
    finishDIY(_mg.upgradeKey, score);
  }
}

// ── Mini-game: Hang Drywall ────────────────────────────────────────────────────
// A panel slides in from the side — tap+hold to press it flat, release on the sweet spot.
const DW_DURATION = 12, DW_PANELS = 8;

function launchDrywallGame(upgradeKey) {
  closeModal();
  _mg = { locked: true, upgradeKey, running: false, timerId: null, placed: 0, panelActive: false };

  const old = document.getElementById('dw-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'dw-overlay';
  overlay.innerHTML = `
    <div class="dw-hud">
      <div class="dw-hud-top">
        <span class="dw-title">${pxIcon('🧱',20)} Hang Drywall</span>
        <span class="dw-time-box"><span id="dw-time">${DW_DURATION}</span>s</span>
      </div>
      <div class="dw-timer-track"><div class="dw-timer-fill" id="dw-timer-fill"></div></div>
      <div class="dw-score" id="dw-score">0 / ${DW_PANELS} panels hung</div>
    </div>
    <div class="dw-arena" id="dw-arena">
      <div class="dw-wall" id="dw-wall"></div>
      <div class="dw-panel-wrap" id="dw-panel-wrap">
        <div class="dw-panel" id="dw-panel"></div>
        <div class="dw-zone-bar">
          <div class="dw-zone-track">
            <div class="dw-zone-sweet"></div>
            <div class="dw-zone-marker" id="dw-marker"></div>
          </div>
        </div>
      </div>
      <div class="dw-instruction" id="dw-instruction">Hold to press flat — release on the green zone!</div>
    </div>
    <div id="dw-start-screen" class="dw-start-screen">
      <div class="dw-start-card">
        <div class="dw-start-icon">${pxIcon('🧱',48)}</div>
        <div class="dw-start-title">Hang Drywall</div>
        <div class="dw-start-desc">Hold the panel to press it flat. Release when the marker hits the green zone!</div>
        <button class="dw-start-btn" id="dw-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const arena = document.getElementById('dw-arena');
  arena.addEventListener('pointerdown', dwPress);
  arena.addEventListener('pointerup',   dwRelease);
  arena.addEventListener('touchstart',  e => { e.preventDefault(); dwPress(); },   { passive: false });
  arena.addEventListener('touchend',    e => { e.preventDefault(); dwRelease(); }, { passive: false });
  document.getElementById('dw-start-btn').addEventListener('click', dwStart);
}

function dwStart() {
  document.getElementById('dw-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + DW_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (DW_DURATION * 1000);
    const fill = document.getElementById('dw-timer-fill');
    const timeEl = document.getElementById('dw-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#78909C' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; dwFinish(); }
  }, 50);
  dwNextPanel();
}

function dwNextPanel() {
  if (!_mg.running || _mg.placed >= DW_PANELS) { dwFinish(); return; }
  const panel = document.getElementById('dw-panel');
  const wrap  = document.getElementById('dw-panel-wrap');
  if (!panel || !wrap) return;

  // Reset panel sliding in from left
  panel.style.transition = 'none';
  panel.style.transform  = 'translateX(-110%)';
  wrap.style.opacity     = '1';

  // Animate slide in
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      panel.style.transition = 'transform 0.5s ease-out';
      panel.style.transform  = 'translateX(0)';
    });
  });

  // Start oscillating marker
  _mg.panelActive = true;
  _mg.holding     = false;
  _mg.markerPos   = 0;
  _mg.markerDir   = 1;
  dwAnimateMarker();

  const inst = document.getElementById('dw-instruction');
  if (inst) inst.textContent = 'Hold to press flat — release on the green zone!';
}

function dwAnimateMarker() {
  if (!_mg.panelActive) return;
  const speed = 1.8 + _mg.placed * 0.25;
  _mg.markerPos += _mg.markerDir * speed;
  if (_mg.markerPos >= 100) { _mg.markerPos = 100; _mg.markerDir = -1; }
  if (_mg.markerPos <= 0)   { _mg.markerPos = 0;   _mg.markerDir = 1;  }
  const marker = document.getElementById('dw-marker');
  if (marker) marker.style.left = _mg.markerPos + '%';
  _mg.markerRaf = requestAnimationFrame(dwAnimateMarker);
}

function dwPress() {
  if (!_mg.running || !_mg.panelActive || _mg.holding) return;
  _mg.holding = true;
  const panel = document.getElementById('dw-panel');
  if (panel) panel.classList.add('dw-panel-pressing');
}

function dwRelease() {
  if (!_mg.running || !_mg.panelActive || !_mg.holding) return;
  _mg.holding     = false;
  _mg.panelActive = false;
  cancelAnimationFrame(_mg.markerRaf);

  const pos = _mg.markerPos;
  const panel = document.getElementById('dw-panel');
  const wrap  = document.getElementById('dw-panel-wrap');
  panel?.classList.remove('dw-panel-pressing');

  // Sweet zone is 35–65
  if (pos >= 35 && pos <= 65) {
    panel?.classList.add('dw-panel-success');
    const inst = document.getElementById('dw-instruction');
    if (inst) inst.textContent = '✅ Perfect fit!';
    _mg.placed++;
    const score = document.getElementById('dw-score');
    if (score) score.textContent = `${_mg.placed} / ${DW_PANELS} panels hung`;
    setTimeout(() => { panel?.classList.remove('dw-panel-success'); if (wrap) wrap.style.opacity = '0'; setTimeout(dwNextPanel, 200); }, 400);
  } else {
    panel?.classList.add('dw-panel-fail');
    const inst = document.getElementById('dw-instruction');
    if (inst) inst.textContent = '❌ Crooked! Try again.';
    setTimeout(() => { panel?.classList.remove('dw-panel-fail'); _mg.panelActive = true; _mg.markerPos = 0; _mg.markerDir = 1; dwAnimateMarker(); }, 500);
  }
}

function dwFinish() {
  cancelAnimationFrame(_mg.markerRaf);
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  const score = Math.min(100, Math.round((_mg.placed / DW_PANELS) * 100));
  const msg   = score >= 100 ? '🌟 Walls done!' : score >= 75 ? '✅ Solid work!' : score >= 40 ? '👍 Coming along!' : '🧱 A few crooked panels...';
  const overlay = document.getElementById('dw-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'dw-result-overlay';
    res.innerHTML = `<div class="dw-result-card"><div class="dw-result-score">${score}%</div><div class="dw-result-label">panels hung</div><div class="dw-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Build a Fence ───────────────────────────────────────────────────
// Posts appear and wobble — tap when they're upright to hammer them in.
const FN_DURATION = 14, FN_POSTS = 10;

function launchFenceGame(upgradeKey) {
  closeModal();
  _mg = { locked: true, upgradeKey, running: false, timerId: null, hammered: 0, postActive: false };

  const old = document.getElementById('fn-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'fn-overlay';
  overlay.innerHTML = `
    <div class="fn-hud">
      <div class="fn-hud-top">
        <span class="fn-title">${pxIcon('🪚',20)} Build a Fence</span>
        <span class="fn-time-box"><span id="fn-time">${FN_DURATION}</span>s</span>
      </div>
      <div class="fn-timer-track"><div class="fn-timer-fill" id="fn-timer-fill"></div></div>
      <div class="fn-score" id="fn-score">0 / ${FN_POSTS} posts set</div>
    </div>
    <div class="fn-arena" id="fn-arena">
      <div class="fn-ground"></div>
      <div class="fn-post-wrap" id="fn-post-wrap">
        <div class="fn-post" id="fn-post">
          <div class="fn-post-top"></div>
          <div class="fn-post-body"></div>
        </div>
        <div class="fn-upright-zone" id="fn-upright-zone"></div>
      </div>
      <div class="fn-instruction" id="fn-instruction">Tap when the post is upright!</div>
    </div>
    <div id="fn-start-screen" class="fn-start-screen">
      <div class="fn-start-card">
        <div class="fn-start-icon">${pxIcon('🪚',48)}</div>
        <div class="fn-start-title">Build a Fence</div>
        <div class="fn-start-desc">Tap the post when it's standing upright to hammer it in!</div>
        <button class="fn-start-btn" id="fn-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const arena = document.getElementById('fn-arena');
  arena.addEventListener('click',      fnTap);
  arena.addEventListener('touchstart', e => { e.preventDefault(); fnTap(); }, { passive: false });
  document.getElementById('fn-start-btn').addEventListener('click', fnStart);
}

function fnStart() {
  document.getElementById('fn-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + FN_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (FN_DURATION * 1000);
    const fill = document.getElementById('fn-timer-fill');
    const timeEl = document.getElementById('fn-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#8D6E63' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; fnFinish(); }
  }, 50);
  fnNextPost();
}

function fnNextPost() {
  if (!_mg.running || _mg.hammered >= FN_POSTS) { fnFinish(); return; }
  const post = document.getElementById('fn-post');
  const wrap = document.getElementById('fn-post-wrap');
  if (!post || !wrap) return;

  wrap.style.display = 'flex';
  post.classList.remove('fn-post-success', 'fn-post-fail');
  _mg.postActive = true;
  _mg.wobbleAngle = 0;
  _mg.wobbleDir   = 1;
  fnWobble();
  const inst = document.getElementById('fn-instruction');
  if (inst) inst.textContent = 'Tap when the post is upright!';
}

function fnWobble() {
  if (!_mg.postActive) return;
  const speed = 1.5 + _mg.hammered * 0.2;
  const maxTilt = Math.max(15, 40 - _mg.hammered * 2);
  _mg.wobbleAngle += _mg.wobbleDir * speed;
  if (_mg.wobbleAngle >= maxTilt)  { _mg.wobbleAngle = maxTilt;  _mg.wobbleDir = -1; }
  if (_mg.wobbleAngle <= -maxTilt) { _mg.wobbleAngle = -maxTilt; _mg.wobbleDir = 1;  }
  const post = document.getElementById('fn-post');
  if (post) post.style.transform = `rotate(${_mg.wobbleAngle}deg)`;
  _mg.wobbleRaf = requestAnimationFrame(fnWobble);
}

function fnTap() {
  if (!_mg.running || !_mg.postActive) return;
  _mg.postActive = false;
  cancelAnimationFrame(_mg.wobbleRaf);

  const angle = Math.abs(_mg.wobbleAngle);
  const post  = document.getElementById('fn-post');
  const inst  = document.getElementById('fn-instruction');

  if (angle <= 12) {
    post?.classList.add('fn-post-success');
    if (inst) inst.textContent = '✅ Hammered in!';
    _mg.hammered++;
    const score = document.getElementById('fn-score');
    if (score) score.textContent = `${_mg.hammered} / ${FN_POSTS} posts set`;
    setTimeout(() => { const wrap = document.getElementById('fn-post-wrap'); if (wrap) wrap.style.display = 'none'; setTimeout(fnNextPost, 250); }, 400);
  } else {
    post?.classList.add('fn-post-fail');
    if (inst) inst.textContent = '❌ Too crooked! Try again.';
    setTimeout(() => { post?.classList.remove('fn-post-fail'); post.style.transform = 'rotate(0deg)'; _mg.wobbleAngle = 0; _mg.wobbleDir = 1; _mg.postActive = true; fnWobble(); }, 500);
  }
}

function fnFinish() {
  cancelAnimationFrame(_mg.wobbleRaf);
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  const score = Math.min(100, Math.round((_mg.hammered / FN_POSTS) * 100));
  const msg   = score >= 100 ? '🌟 Fence is solid!' : score >= 75 ? '✅ Good work!' : score >= 40 ? '👍 Getting there!' : '🪚 A few wobbly posts...';
  const overlay = document.getElementById('fn-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'fn-result-overlay';
    res.innerHTML = `<div class="fn-result-card"><div class="fn-result-score">${score}%</div><div class="fn-result-label">posts set</div><div class="fn-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Pour Concrete ───────────────────────────────────────────────────
// Drag a slider to tilt the bucket — fill each section of the mold evenly.
const CN_DURATION = 18, CN_SECTIONS = 5;

function launchConcreteGame(upgradeKey) {
  closeModal();
  _mg = {
    locked: true, upgradeKey, running: false, timerId: null,
    levels: Array(CN_SECTIONS).fill(0), // 0–100 fill per section
    bucketX: 50, // 0–100 horizontal position
    pouring: false,
    score: 0,
  };

  const old = document.getElementById('cn-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'cn-overlay';
  overlay.innerHTML = `
    <div class="cn-hud">
      <div class="cn-hud-top">
        <span class="cn-title">${pxIcon('🏗️',20)} Pour Concrete</span>
        <span class="cn-time-box"><span id="cn-time">${CN_DURATION}</span>s</span>
      </div>
      <div class="cn-timer-track"><div class="cn-timer-fill" id="cn-timer-fill"></div></div>
      <div class="cn-score" id="cn-score">Fill all sections evenly!</div>
    </div>
    <div class="cn-arena" id="cn-arena">
      <div class="cn-bucket-wrap" id="cn-bucket-wrap">
        <div class="cn-bucket" id="cn-bucket">${pxIcon('🪣',40)}</div>
        <div class="cn-stream" id="cn-stream"></div>
      </div>
      <div class="cn-mold" id="cn-mold">
        ${Array(CN_SECTIONS).fill(0).map((_, i) => `
          <div class="cn-section" id="cn-sec-${i}">
            <div class="cn-fill" id="cn-fill-${i}"></div>
            <div class="cn-overflow" id="cn-overflow-${i}"></div>
          </div>`).join('')}
      </div>
      <div class="cn-slider-wrap">
        <input type="range" id="cn-slider" class="cn-slider" min="0" max="100" value="50">
        <div class="cn-slider-label">← Drag to move bucket →</div>
      </div>
    </div>
    <div id="cn-start-screen" class="cn-start-screen">
      <div class="cn-start-card">
        <div class="cn-start-icon">${pxIcon('🏗️',48)}</div>
        <div class="cn-start-title">Pour Concrete</div>
        <div class="cn-start-desc">Drag the slider to move the bucket. Hold the pour button to fill each section — don't overflow!</div>
        <button class="cn-start-btn" id="cn-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const slider = document.getElementById('cn-slider');
  slider.addEventListener('input', () => { _mg.bucketX = parseFloat(slider.value); cnUpdateBucket(); });

  const arena = document.getElementById('cn-arena');
  arena.addEventListener('pointerdown', e => { if (e.target !== slider) { e.preventDefault(); _mg.pouring = true; cnUpdateStream(true); } });
  arena.addEventListener('pointerup',   () => { _mg.pouring = false; cnUpdateStream(false); });
  arena.addEventListener('touchstart',  e => { if (e.target !== slider) { e.preventDefault(); _mg.pouring = true; cnUpdateStream(true); } }, { passive: false });
  arena.addEventListener('touchend',    () => { _mg.pouring = false; cnUpdateStream(false); });

  document.getElementById('cn-start-btn').addEventListener('click', cnStart);
}

function cnUpdateBucket() {
  const wrap = document.getElementById('cn-bucket-wrap');
  if (wrap) wrap.style.left = _mg.bucketX + '%';
}

function cnUpdateStream(active) {
  const stream = document.getElementById('cn-stream');
  if (stream) stream.style.opacity = active ? '1' : '0';
}

function cnStart() {
  document.getElementById('cn-start-screen').style.display = 'none';
  _mg.running = true;
  cnUpdateBucket();

  const endTime = Date.now() + CN_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (CN_DURATION * 1000);
    const fill = document.getElementById('cn-timer-fill');
    const timeEl = document.getElementById('cn-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#90A4AE' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);

    // Pour into nearest section
    if (_mg.pouring) {
      const secW = 100 / CN_SECTIONS;
      const secIdx = Math.min(CN_SECTIONS - 1, Math.floor(_mg.bucketX / secW));
      if (_mg.levels[secIdx] < 110) {
        _mg.levels[secIdx] += 1.2;
        cnUpdateFill(secIdx);
      }
    }
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; cnFinish(); }
  }, 50);
}

function cnUpdateFill(idx) {
  const fillEl    = document.getElementById(`cn-fill-${idx}`);
  const overflowEl = document.getElementById(`cn-overflow-${idx}`);
  const lvl       = Math.min(_mg.levels[idx], 100);
  if (fillEl) fillEl.style.height = lvl + '%';
  if (overflowEl) overflowEl.style.opacity = _mg.levels[idx] > 100 ? '1' : '0';
}

function cnFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  // Score: average fill, penalize overflow
  let total = 0;
  for (let i = 0; i < CN_SECTIONS; i++) {
    const lvl = _mg.levels[i];
    const s   = lvl > 100 ? Math.max(0, 100 - (lvl - 100) * 3) : lvl;
    total += s;
  }
  const score = Math.min(100, Math.round(total / CN_SECTIONS));
  const msg   = score >= 90 ? '🌟 Perfectly poured!' : score >= 70 ? '✅ Solid slab!' : score >= 40 ? '👍 Getting the hang of it!' : '🏗️ Uneven pour...';
  const overlay = document.getElementById('cn-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'cn-result-overlay';
    res.innerHTML = `<div class="cn-result-card"><div class="cn-result-score">${score}%</div><div class="cn-result-label">evenly filled</div><div class="cn-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Power Washing ───────────────────────────────────────────────────
// Drag to blast grime off a house facade — roof angle clips top tiles,
// door and windows are non-cleanable structure.
const WS_COLS = 10, WS_ROWS = 16, WS_DURATION = 9;

function launchWashGame(upgradeKey) {
  closeModal();

  // Classify every tile
  const types = [];
  let totalDirty = 0;
  for (let r = 0; r < WS_ROWS; r++) {
    for (let c = 0; c < WS_COLS; c++) {
      const xf    = (c + 0.5) / WS_COLS;
      const yRoof = Math.abs(xf - 0.5) * 0.40; // eaves at 20% of height, peak at top-center
      if (r / WS_ROWS < yRoof)                                         { types.push('roof');      continue; }
      if (c >= 4 && c <= 5 && r >= 12)                                 { types.push('door-tile'); continue; }
      if (((c >= 1 && c <= 2) || (c >= 7 && c <= 8)) && r >= 5 && r <= 7) { types.push('winpane');   continue; }
      types.push('wall');
      totalDirty++;
    }
  }

  _mg = { locked: true, upgradeKey, running: false, timerId: null, cleaned: 0, totalDirty };

  const old = document.getElementById('ws-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'ws-overlay';
  overlay.innerHTML = `
    <div class="ws-hud">
      <div class="ws-hud-top">
        <span class="ws-title">${pxIcon('💧',20)} Power Washing</span>
        <span class="ws-time-box"><span id="ws-time">${WS_DURATION}</span>s</span>
      </div>
      <div class="ws-timer-track"><div class="ws-timer-fill" id="ws-timer-fill"></div></div>
      <div class="ws-score" id="ws-score">0% cleaned</div>
    </div>
    <div class="ws-scene">
      <div class="ws-house-wrap">
        <div class="ws-grid" id="ws-grid"></div>
        <div class="ws-door-frame"></div>
        <div class="ws-win-frame ws-win-left"></div>
        <div class="ws-win-frame ws-win-right"></div>
      </div>
    </div>
    <div id="ws-start-screen" class="ws-start-screen">
      <div class="ws-start-card">
        <div class="ws-start-icon">${pxIcon('💧',48)}</div>
        <div class="ws-start-title">Power Washing</div>
        <div class="ws-start-desc">Drag your finger to blast the grime off the house!</div>
        <button class="ws-start-btn" id="ws-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const grid = document.getElementById('ws-grid');
  for (let i = 0; i < types.length; i++) {
    const cell = document.createElement('div');
    cell.className = `ws-cell ws-${types[i]}`;
    grid.appendChild(cell);
  }

  let pressing = false;
  const scene = overlay.querySelector('.ws-scene');
  scene.addEventListener('pointerdown', e => { pressing = true; wsClean(e); });
  scene.addEventListener('pointermove', e => { if (pressing) wsClean(e); });
  scene.addEventListener('pointerup',   () => { pressing = false; });
  scene.addEventListener('touchstart',  e => { e.preventDefault(); pressing = true; wsCleanTouch(e); }, { passive: false });
  scene.addEventListener('touchmove',   e => { e.preventDefault(); if (pressing) wsCleanTouch(e); }, { passive: false });
  scene.addEventListener('touchend',    () => { pressing = false; });

  document.getElementById('ws-start-btn').addEventListener('click', wsStart);
}

function wsClean(e) {
  if (!_mg.running) return;
  wsCleanCell(document.elementFromPoint(e.clientX, e.clientY));
}
function wsCleanTouch(e) {
  if (!_mg.running) return;
  for (const t of e.touches) wsCleanCell(document.elementFromPoint(t.clientX, t.clientY));
}
function wsCleanCell(el) {
  if (!el || !el.classList.contains('ws-wall')) return;
  el.classList.remove('ws-wall');
  el.classList.add('ws-clean');
  _mg.cleaned++;
  const pct = Math.round((_mg.cleaned / _mg.totalDirty) * 100);
  const scoreEl = document.getElementById('ws-score');
  if (scoreEl) scoreEl.textContent = `${pct}% cleaned`;
  if (_mg.cleaned >= _mg.totalDirty) { clearInterval(_mg.timerId); _mg.running = false; wsFinish(); }
}

function wsStart() {
  document.getElementById('ws-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + WS_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (WS_DURATION * 1000);
    const fill = document.getElementById('ws-timer-fill');
    const timeEl = document.getElementById('ws-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#29B6F6' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; wsFinish(); }
  }, 50);
}

function wsFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  const score = Math.min(100, Math.round((_mg.cleaned / _mg.totalDirty) * 100));
  const msg   = score >= 100 ? '🌟 Spotless!' : score >= 80 ? '✅ Nice and clean!' : score >= 50 ? '👍 Mostly clean!' : '💧 Still pretty grimy...';
  const overlay = document.getElementById('ws-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'ws-result-overlay';
    res.innerHTML = `<div class="ws-result-card"><div class="ws-result-score">${score}%</div><div class="ws-result-label">cleaned</div><div class="ws-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Install Cabinets ────────────────────────────────────────────────
// Cabinet drops from top — slide it left/right to align with the bracket, then tap to lock.
const CB_DURATION = 16, CB_COUNT = 6;

function launchCabinetGame(upgradeKey) {
  closeModal();
  _mg = { locked: true, upgradeKey, running: false, timerId: null, installed: 0, cabinetActive: false };

  const old = document.getElementById('cb-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'cb-overlay';
  overlay.innerHTML = `
    <div class="cb-hud">
      <div class="cb-hud-top">
        <span class="cb-title">${pxIcon('🍳',20)} Install Cabinets</span>
        <span class="cb-time-box"><span id="cb-time">${CB_DURATION}</span>s</span>
      </div>
      <div class="cb-timer-track"><div class="cb-timer-fill" id="cb-timer-fill"></div></div>
      <div class="cb-score" id="cb-score">0 / ${CB_COUNT} installed</div>
    </div>
    <div class="cb-arena" id="cb-arena">
      <div class="cb-wall">
        <div class="cb-bracket" id="cb-bracket"></div>
      </div>
      <div class="cb-cabinet" id="cb-cabinet">
        <div class="cb-cabinet-body">
          <div class="cb-cabinet-handle"></div>
        </div>
        <div class="cb-align-indicator" id="cb-align"></div>
      </div>
      <div class="cb-slider-wrap">
        <input type="range" id="cb-slider" class="cb-slider" min="5" max="95" value="50">
        <div class="cb-slider-label">← Slide to align →</div>
      </div>
      <div class="cb-instruction" id="cb-instruction">Align the cabinet with the bracket, then tap!</div>
    </div>
    <div id="cb-start-screen" class="cb-start-screen">
      <div class="cb-start-card">
        <div class="cb-start-icon">${pxIcon('🍳',48)}</div>
        <div class="cb-start-title">Install Cabinets</div>
        <div class="cb-start-desc">Slide to align the cabinet with the bracket, then tap to lock it in!</div>
        <button class="cb-start-btn" id="cb-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const slider = document.getElementById('cb-slider');
  slider.addEventListener('input', () => { _mg.cabinetPos = parseFloat(slider.value); cbUpdateCabinet(); });

  const arena = document.getElementById('cb-arena');
  arena.addEventListener('click',      e => { if (e.target !== slider) cbTap(); });
  arena.addEventListener('touchstart', e => { if (e.target !== slider) { e.preventDefault(); cbTap(); } }, { passive: false });

  document.getElementById('cb-start-btn').addEventListener('click', cbStart);
}

function cbStart() {
  document.getElementById('cb-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + CB_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (CB_DURATION * 1000);
    const fill = document.getElementById('cb-timer-fill');
    const timeEl = document.getElementById('cb-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#A1887F' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; cbFinish(); }
  }, 50);
  cbNextCabinet();
}

function cbNextCabinet() {
  if (!_mg.running || _mg.installed >= CB_COUNT) { cbFinish(); return; }
  // Random bracket position
  _mg.bracketPos  = 20 + Math.random() * 60;
  _mg.cabinetPos  = 50;
  _mg.cabinetActive = true;

  const bracket = document.getElementById('cb-bracket');
  const slider  = document.getElementById('cb-slider');
  const cabinet = document.getElementById('cb-cabinet');
  if (bracket) bracket.style.left = _mg.bracketPos + '%';
  if (slider)  { slider.value = '50'; }
  if (cabinet) { cabinet.style.opacity = '1'; cabinet.classList.remove('cb-locked', 'cb-fail'); }
  cbUpdateCabinet();
  const inst = document.getElementById('cb-instruction');
  if (inst) inst.textContent = 'Align the cabinet with the bracket, then tap!';
}

function cbUpdateCabinet() {
  const cabinet = document.getElementById('cb-cabinet');
  const align   = document.getElementById('cb-align');
  if (cabinet) cabinet.style.left = _mg.cabinetPos + '%';
  const diff = Math.abs((_mg.cabinetPos || 50) - (_mg.bracketPos || 50));
  if (align) {
    align.style.background = diff <= 5 ? '#4CAF50' : diff <= 12 ? '#FF9800' : '#F44336';
    align.textContent = diff <= 5 ? '✓' : diff <= 12 ? '~' : '✗';
  }
}

function cbTap() {
  if (!_mg.running || !_mg.cabinetActive) return;
  const diff = Math.abs((_mg.cabinetPos || 50) - (_mg.bracketPos || 50));
  const cabinet = document.getElementById('cb-cabinet');
  const inst    = document.getElementById('cb-instruction');
  _mg.cabinetActive = false;

  if (diff <= 8) {
    cabinet?.classList.add('cb-locked');
    if (inst) inst.textContent = '✅ Locked in!';
    _mg.installed++;
    const score = document.getElementById('cb-score');
    if (score) score.textContent = `${_mg.installed} / ${CB_COUNT} installed`;
    setTimeout(() => { if (cabinet) cabinet.style.opacity = '0'; setTimeout(cbNextCabinet, 250); }, 500);
  } else {
    cabinet?.classList.add('cb-fail');
    if (inst) inst.textContent = '❌ Misaligned! Try again.';
    setTimeout(() => { cabinet?.classList.remove('cb-fail'); _mg.cabinetActive = true; }, 500);
  }
}

function cbFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  const score = Math.min(100, Math.round((_mg.installed / CB_COUNT) * 100));
  const msg   = score >= 100 ? '🌟 Kitchen looks great!' : score >= 75 ? '✅ Nice work!' : score >= 40 ? '👍 Getting there!' : '🍳 A few gaps in the kitchen...';
  const overlay = document.getElementById('cb-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'cb-result-overlay';
    res.innerHTML = `<div class="cb-result-card"><div class="cb-result-score">${score}%</div><div class="cb-result-label">installed</div><div class="cb-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Repair a Deck ───────────────────────────────────────────────────
// Tap rotted planks multiple times to pry them out before rot spreads.
const DK_COLS = 4, DK_ROWS = 7, DK_TOTAL = DK_COLS * DK_ROWS, DK_DURATION = 6, DK_TAPS = 3;

function launchDeckGame(upgradeKey) {
  closeModal();

  // Random seed: ~25% of planks start rotted
  const planks = Array(DK_TOTAL).fill(0).map(() => Math.random() < 0.25 ? 'rotted' : 'ok');
  // health = taps remaining per rotted plank
  const health = planks.map(p => p === 'rotted' ? DK_TAPS : 0);

  _mg = { locked: true, upgradeKey, running: false, timerId: null, planks, health, fixed: 0 };

  const old = document.getElementById('dk-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'dk-overlay';
  overlay.innerHTML = `
    <div class="dk-hud">
      <div class="dk-hud-top">
        <span class="dk-title">${pxIcon('🪜',20)} Repair a Deck</span>
        <span class="dk-time-box"><span id="dk-time">${DK_DURATION}</span>s</span>
      </div>
      <div class="dk-timer-track"><div class="dk-timer-fill" id="dk-timer-fill"></div></div>
      <div class="dk-score" id="dk-score">Tap rotted planks to pry them out!</div>
    </div>
    <div class="dk-arena">
      <div class="dk-grid" id="dk-grid"></div>
    </div>
    <div id="dk-start-screen" class="dk-start-screen">
      <div class="dk-start-card">
        <div class="dk-start-icon">${pxIcon('🪜',48)}</div>
        <div class="dk-start-title">Repair a Deck</div>
        <div class="dk-start-desc">Tap the rotted planks multiple times to pry them out — rot spreads if you wait!</div>
        <button class="dk-start-btn" id="dk-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const grid = document.getElementById('dk-grid');
  for (let i = 0; i < DK_TOTAL; i++) {
    const row = Math.floor(i / DK_COLS);
    const cell = document.createElement('div');
    // Stagger alternate rows like real deck boards
    cell.className = `dk-plank dk-${planks[i]} ${row % 2 === 1 ? 'dk-stagger' : ''}`;
    cell.dataset.idx = i;
    // Wood grain variation per plank
    const grain = Math.floor(Math.random() * 4);
    cell.dataset.grain = grain;
    cell.addEventListener('click',      () => dkTap(i));
    cell.addEventListener('touchstart', e => { e.preventDefault(); dkTap(i); }, { passive: false });
    if (planks[i] === 'rotted') dkSetHealth(cell, DK_TAPS);
    grid.appendChild(cell);
  }

  document.getElementById('dk-start-btn').addEventListener('click', dkStart);
}

function dkSetHealth(cell, hp) {
  // Show pip indicators for remaining taps
  let pips = cell.querySelector('.dk-pips');
  if (!pips) { pips = document.createElement('div'); pips.className = 'dk-pips'; cell.appendChild(pips); }
  pips.innerHTML = Array(DK_TAPS).fill(0).map((_, i) => `<span class="dk-pip ${i < hp ? 'dk-pip-full' : 'dk-pip-empty'}"></span>`).join('');
}

function dkStart() {
  document.getElementById('dk-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + DK_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (DK_DURATION * 1000);
    const fill = document.getElementById('dk-timer-fill');
    const timeEl = document.getElementById('dk-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#8D6E63' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; dkFinish(); }
  }, 50);

  const rotCount = _mg.planks.filter(p => p === 'rotted').length;
  const scoreEl = document.getElementById('dk-score');
  if (scoreEl) scoreEl.textContent = `${rotCount} rotted plank${rotCount !== 1 ? 's' : ''} remaining`;
}

function dkTap(idx) {
  if (!_mg.running || _mg.planks[idx] !== 'rotted') return;
  _mg.health[idx]--;
  const cell = document.querySelector(`#dk-grid .dk-plank[data-idx="${idx}"]`);
  if (_mg.health[idx] <= 0) {
    _mg.planks[idx] = 'fixed';
    _mg.fixed++;
    if (cell) { cell.className = cell.className.replace(/dk-rotted|dk-spreading/, 'dk-fixed'); const pips = cell.querySelector('.dk-pips'); if (pips) pips.remove(); }
  } else {
    if (cell) { cell.classList.add('dk-hit'); dkSetHealth(cell, _mg.health[idx]); setTimeout(() => cell.classList.remove('dk-hit'), 200); }
  }
  const rotCount = _mg.planks.filter(p => p === 'rotted').length;
  const scoreEl = document.getElementById('dk-score');
  if (scoreEl) scoreEl.textContent = `${rotCount} rotted plank${rotCount !== 1 ? 's' : ''} remaining`;
  if (rotCount === 0) { clearInterval(_mg.timerId); _mg.running = false; dkFinish(); }
}

function dkRenderPlanks() {
  for (let i = 0; i < DK_TOTAL; i++) {
    const cell = document.querySelector(`#dk-grid .dk-plank[data-idx="${i}"]`);
    if (!cell) continue;
    const row = Math.floor(i / DK_COLS);
    const stagger = row % 2 === 1 ? 'dk-stagger' : '';
    const grain = cell.dataset.grain || '0';
    cell.className = `dk-plank dk-${_mg.planks[i]} ${stagger} dk-grain-${grain}`;
    cell.dataset.grain = grain;
    if (_mg.planks[i] === 'rotted') {
      dkSetHealth(cell, _mg.health[i]);
    } else {
      const pips = cell.querySelector('.dk-pips');
      if (pips) pips.remove();
    }
  }
}

function dkFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false; _mg.locked = false;
  const rotLeft = _mg.planks.filter(p => p === 'rotted').length;
  const score   = Math.min(100, Math.round(((DK_TOTAL - rotLeft) / DK_TOTAL) * 100));
  const msg     = score >= 95 ? '🌟 Deck is solid!' : score >= 75 ? '✅ Good repair!' : score >= 50 ? '👍 Mostly fixed!' : '🪜 Rot got out of hand...';
  const overlay = document.getElementById('dk-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'dk-result-overlay';
    res.innerHTML = `<div class="dk-result-card"><div class="dk-result-score">${score}%</div><div class="dk-result-label">repaired</div><div class="dk-result-msg">${msg}</div></div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else { finishDIY(_mg.upgradeKey, score); }
}

// ── Mini-game: Tile the Bathroom ──────────────────────────────────────────────
const TL_COLS = 4, TL_ROWS = 6, TL_DURATION = 15, TL_TARGET = 20;
const TL_COLORS = ['#E8E0D0','#D4C9B8','#B8CDD4','#C8D4B8','#D4B8C8','#CCC8B8'];
const TL_FALL_START = 1400; // ms for tile to fall, decreases with score

function launchTileGame(upgradeKey) {
  closeModal();
  _mg = {
    locked: true, upgradeKey,
    running: false, timerId: null,
    placed: 0, missed: 0,
    cols: Array(TL_COLS).fill(0), // tiles placed per column
    fallingTile: null,  // { col, el, startTime, duration, color, raf }
    speed: TL_FALL_START,
  };

  const old = document.getElementById('tl-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'tl-overlay';
  overlay.innerHTML = `
    <div class="tl-hud">
      <div class="tl-hud-top">
        <span class="tl-title">${pxIcon('🚿',20)} Tile the Bathroom</span>
        <span class="tl-time-box"><span id="tl-time">${TL_DURATION}</span>s</span>
      </div>
      <div class="tl-timer-track"><div class="tl-timer-fill" id="tl-timer-fill"></div></div>
      <div class="tl-score" id="tl-score">0 tiles set</div>
    </div>
    <div class="tl-arena" id="tl-arena">
      <div class="tl-grid" id="tl-grid"></div>
    </div>
    <div id="tl-start-screen" class="tl-start-screen">
      <div class="tl-start-card">
        <div class="tl-start-icon">${pxIcon('🚿',48)}</div>
        <div class="tl-start-title">Tile the Bathroom</div>
        <div class="tl-start-desc">Tap the falling tile to set it before it hits the floor!</div>
        <button class="tl-start-btn" id="tl-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  // Build grid of already-placed tiles (bottom half pre-filled for aesthetics)
  const grid = document.getElementById('tl-grid');
  for (let r = 0; r < TL_ROWS; r++) {
    for (let c = 0; c < TL_COLS; c++) {
      const cell = document.createElement('div');
      cell.className = 'tl-cell';
      cell.dataset.row = r;
      cell.dataset.col = c;
      cell.id = `tl-cell-${r}-${c}`;
      grid.appendChild(cell);
    }
  }

  document.getElementById('tl-start-btn').addEventListener('click', tlStart);
}

function tlStart() {
  document.getElementById('tl-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + TL_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (TL_DURATION * 1000);
    const fill   = document.getElementById('tl-timer-fill');
    const timeEl = document.getElementById('tl-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#4CAF50' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; tlFinish(); }
  }, 50);
  tlDropNext();
}

function tlDropNext() {
  if (!_mg.running) return;

  // Pick a column that isn't full
  const openCols = [];
  for (let c = 0; c < TL_COLS; c++) {
    if (_mg.cols[c] < TL_ROWS) openCols.push(c);
  }
  if (openCols.length === 0) { tlFinish(); return; }

  const col   = openCols[Math.floor(Math.random() * openCols.length)];
  const color = TL_COLORS[Math.floor(Math.random() * TL_COLORS.length)];
  const arena = document.getElementById('tl-arena');
  const grid  = document.getElementById('tl-grid');
  if (!arena || !grid) return;

  const gridRect  = grid.getBoundingClientRect();
  const arenaRect = arena.getBoundingClientRect();
  const colW      = gridRect.width / TL_COLS;
  const tileSize  = colW - 6;
  const startX    = gridRect.left - arenaRect.left + col * colW + 3;

  const tile = document.createElement('div');
  tile.className = 'tl-falling';
  tile.style.cssText = `left:${startX}px; top:-${tileSize}px; width:${tileSize}px; height:${tileSize}px; background:${color};`;
  arena.appendChild(tile);

  // Target row = top of this column's stack
  const targetRow = TL_ROWS - 1 - _mg.cols[col];
  const targetY   = gridRect.top - arenaRect.top + targetRow * (gridRect.height / TL_ROWS) + 3;
  const floorY    = gridRect.bottom - arenaRect.top;

  const startTime = performance.now();
  const speed     = Math.max(500, _mg.speed - _mg.placed * 30);

  _mg.fallingTile = { col, color, el: tile, targetRow, targetY, floorY, startTime, speed, done: false };

  function animate(now) {
    if (!_mg.fallingTile || _mg.fallingTile.done) return;
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / speed, 1);
    const currentY = -tileSize + (floorY + tileSize) * progress;
    tile.style.top = currentY + 'px';

    if (progress >= 1) {
      // Missed — tile hits floor
      tlMiss();
    } else {
      _mg.fallingTile.raf = requestAnimationFrame(animate);
    }
  }
  _mg.fallingTile.raf = requestAnimationFrame(animate);

  // Tap handler
  function onTap(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!_mg.fallingTile || _mg.fallingTile.done) return;
    tlPlace();
  }
  tile.addEventListener('click', onTap);
  tile.addEventListener('touchstart', onTap, { passive: false });
}

function tlPlace() {
  const ft = _mg.fallingTile;
  if (!ft || ft.done) return;
  ft.done = true;
  cancelAnimationFrame(ft.raf);

  const tile = ft.el;
  const grid = document.getElementById('tl-grid');
  if (!grid) { tile.remove(); tlDropNext(); return; }

  // Snap tile into the grid cell
  const cell = document.getElementById(`tl-cell-${ft.targetRow}-${ft.col}`);
  if (cell) {
    cell.style.background = ft.color;
    cell.classList.add('tl-cell-placed');
  }
  tile.remove();
  _mg.cols[ft.col]++;
  _mg.placed++;
  _mg.fallingTile = null;

  const score = document.getElementById('tl-score');
  if (score) score.textContent = `${_mg.placed} tile${_mg.placed !== 1 ? 's' : ''} set`;

  if (_mg.placed >= TL_TARGET) { clearInterval(_mg.timerId); _mg.running = false; tlFinish(); return; }
  setTimeout(tlDropNext, 180);
}

function tlMiss() {
  const ft = _mg.fallingTile;
  if (!ft || ft.done) return;
  ft.done = true;
  cancelAnimationFrame(ft.raf);

  const tile = ft.el;
  tile.classList.add('tl-shatter');
  setTimeout(() => tile.remove(), 400);
  _mg.missed++;
  _mg.fallingTile = null;
  setTimeout(tlDropNext, 300);
}

function tlFinish() {
  if (_mg.fallingTile && !_mg.fallingTile.done) {
    _mg.fallingTile.done = true;
    cancelAnimationFrame(_mg.fallingTile.raf);
    _mg.fallingTile.el?.remove();
  }
  clearInterval(_mg.timerId);
  _mg.running = false;
  _mg.locked  = false;

  const score = Math.min(100, Math.round((_mg.placed / TL_TARGET) * 100));
  const msg   = score >= 100 ? '🌟 Perfect tiling!'       :
                score >= 75  ? '✅ Looks great!'            :
                score >= 40  ? '👍 Getting there!'          :
                               '🚿 A few gaps in the floor...';

  const overlay = document.getElementById('tl-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'tl-result-overlay';
    res.innerHTML = `
      <div class="tl-result-card">
        <div class="tl-result-score">${score}%</div>
        <div class="tl-result-label">tiles set</div>
        <div class="tl-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else {
    finishDIY(_mg.upgradeKey, score);
  }
}

// ── Mini-game: Wire the Circuit Panel ─────────────────────────────────────────
// Tap a wire on the left, then tap the matching terminal on the right.
// 5 color-coded wires shuffled against 5 terminals. Score = connections made.
const EL_DURATION = 3;
const EL_WIRES = [
  { id: 'red',    color: '#E53935', text: '#fff',     label: 'HOT  L1'  },
  { id: 'black',  color: '#37474F', text: '#fff',     label: 'HOT  L2'  },
  { id: 'white',  color: '#ECEFF1', text: '#263238',  label: 'NEUTRAL'  },
  { id: 'green',  color: '#2E7D32', text: '#fff',     label: 'GROUND'   },
  { id: 'yellow', color: '#F9A825', text: '#263238',  label: '3-WAY'    },
];

function launchElectricalGame(upgradeKey) {
  closeModal();
  const shuffled = [...EL_WIRES].sort(() => Math.random() - 0.5);
  _mg = {
    locked: true, upgradeKey,
    selected: null,
    connected: new Set(),
    total: EL_WIRES.length,
    running: false, timerId: null,
    shuffled,
  };

  const old = document.getElementById('el-overlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'el-overlay';
  overlay.innerHTML = `
    <div class="el-hud">
      <div class="el-hud-top">
        <span class="el-title">${pxIcon('⚡',20)} Wire the Panel</span>
        <span class="el-time-box"><span id="el-time">${EL_DURATION}</span>s</span>
      </div>
      <div class="el-timer-track"><div class="el-timer-fill" id="el-timer-fill"></div></div>
      <div class="el-progress" id="el-progress">0 / ${EL_WIRES.length} wires connected</div>
    </div>
    <div class="el-panel" id="el-panel">
      <svg id="el-svg" class="el-svg"></svg>

      <div class="el-row el-wires-row">
        <div class="el-row-label">WIRES</div>
        <div class="el-row-items">
        ${EL_WIRES.map(w => `
          <div class="el-wire" id="elw-${w.id}" data-id="${w.id}"
               style="--wc:${w.color};--wt:${w.text}">
            <div class="el-wire-body">${w.label}</div>
            <div class="el-wire-nub"></div>
          </div>`).join('')}
        </div>
      </div>

      <div class="el-divider">
        <span>⚡ MAIN PANEL ⚡</span>
      </div>

      <div class="el-row el-terminals-row">
        <div class="el-row-label">TERMINALS</div>
        <div class="el-row-items">
        ${shuffled.map(w => `
          <div class="el-terminal" id="elt-${w.id}" data-id="${w.id}"
               style="--wc:${w.color};--wt:${w.text}">
            <div class="el-terminal-screw"><div class="el-terminal-slot"></div></div>
            <div class="el-terminal-body">${w.label}</div>
          </div>`).join('')}
        </div>
      </div>
    </div>
    <div id="el-start-screen" class="el-start-screen">
      <div class="el-start-card">
        <div class="el-start-icon">${pxIcon('⚡',48)}</div>
        <div class="el-start-title">Wire the Panel</div>
        <div class="el-start-desc">Tap a wire on top, then tap the matching terminal on the bottom to connect it!</div>
        <button class="el-start-btn" id="el-start-btn">Start Job</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  overlay.querySelectorAll('.el-wire').forEach(el => {
    el.addEventListener('click', () => elTapWire(el.dataset.id));
    el.addEventListener('touchstart', e => { e.preventDefault(); elTapWire(el.dataset.id); }, { passive: false });
  });
  overlay.querySelectorAll('.el-terminal').forEach(el => {
    el.addEventListener('click', () => elTapTerminal(el.dataset.id));
    el.addEventListener('touchstart', e => { e.preventDefault(); elTapTerminal(el.dataset.id); }, { passive: false });
  });

  document.getElementById('el-start-btn').addEventListener('click', elStart);
}

function elClearSelection() {
  document.querySelectorAll('.el-wire.el-selected, .el-terminal.el-selected').forEach(el => el.classList.remove('el-selected'));
  _mg.selected = null;
}

function elTryConnect(wireId, termId) {
  const termEl = document.getElementById(`elt-${termId}`);
  const wireEl = document.getElementById(`elw-${wireId}`);
  if (wireId === termId) {
    // ✅ Correct match
    const wire = EL_WIRES.find(w => w.id === wireId);
    wireEl?.classList.remove('el-selected');
    wireEl?.classList.add('el-connected');
    termEl?.classList.remove('el-selected');
    termEl?.classList.add('el-connected');
    _mg.connected.add(wireId);
    elDrawLine(wireId, wire.color);
    _mg.selected = null;

    const prog = document.getElementById('el-progress');
    if (prog) prog.textContent = `${_mg.connected.size} / ${_mg.total} wires connected`;
    if (_mg.connected.size >= _mg.total) {
      clearInterval(_mg.timerId);
      _mg.running = false;
      elFinish();
    }
  } else {
    // ❌ Wrong match — flash both red, deselect
    wireEl?.classList.add('el-wrong');
    termEl?.classList.add('el-wrong');
    setTimeout(() => { wireEl?.classList.remove('el-wrong'); termEl?.classList.remove('el-wrong'); }, 450);
    elClearSelection();
  }
}

function elTapWire(wireId) {
  if (!_mg.running || _mg.connected.has(wireId)) return;
  if (_mg.selected?.type === 'terminal') {
    elTryConnect(wireId, _mg.selected.id);
  } else if (_mg.selected?.id === wireId) {
    elClearSelection();
  } else {
    elClearSelection();
    _mg.selected = { id: wireId, type: 'wire' };
    document.getElementById(`elw-${wireId}`)?.classList.add('el-selected');
  }
}

function elTapTerminal(termId) {
  if (!_mg.running || _mg.connected.has(termId)) return;
  if (_mg.selected?.type === 'wire') {
    elTryConnect(_mg.selected.id, termId);
  } else if (_mg.selected?.id === termId) {
    elClearSelection();
  } else {
    elClearSelection();
    _mg.selected = { id: termId, type: 'terminal' };
    document.getElementById(`elt-${termId}`)?.classList.add('el-selected');
  }
}

function elDrawLine(wireId, color) {
  const svg      = document.getElementById('el-svg');
  const panel    = document.getElementById('el-panel');
  const wireEl   = document.getElementById(`elw-${wireId}`);
  const termEl   = document.getElementById(`elt-${wireId}`);
  if (!svg || !panel || !wireEl || !termEl) return;

  const pr = panel.getBoundingClientRect();
  const wr = wireEl.getBoundingClientRect();
  const tr = termEl.getBoundingClientRect();

  const x1 = wr.left + wr.width / 2 - pr.left;
  const y1 = wr.bottom - pr.top;
  const x2 = tr.left + tr.width / 2 - pr.left;
  const y2 = tr.top - pr.top;
  const my = (y1 + y2) / 2;

  // Glow layer underneath
  const glow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  glow.setAttribute('d', `M ${x1} ${y1} C ${x1} ${my} ${x2} ${my} ${x2} ${y2}`);
  glow.setAttribute('stroke', color);
  glow.setAttribute('stroke-width', '12');
  glow.setAttribute('fill', 'none');
  glow.setAttribute('stroke-linecap', 'round');
  glow.setAttribute('opacity', '0.3');
  svg.appendChild(glow);

  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', `M ${x1} ${y1} C ${x1} ${my} ${x2} ${my} ${x2} ${y2}`);
  path.setAttribute('stroke', color);
  path.setAttribute('stroke-width', '6');
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke-linecap', 'round');
  path.setAttribute('opacity', '1');
  svg.appendChild(path);

  // Animate draw
  const len = path.getTotalLength();
  [path, glow].forEach(p => {
    p.style.strokeDasharray  = len;
    p.style.strokeDashoffset = len;
    p.style.transition       = 'stroke-dashoffset 0.35s ease-out';
  });
  requestAnimationFrame(() => {
    path.style.strokeDashoffset = '0';
    glow.style.strokeDashoffset = '0';
  });
}

function elStart() {
  document.getElementById('el-start-screen').style.display = 'none';
  _mg.running = true;
  const endTime = Date.now() + EL_DURATION * 1000;
  _mg.timerId = setInterval(() => {
    const left = Math.max(0, endTime - Date.now());
    const pct  = left / (EL_DURATION * 1000);
    const fill  = document.getElementById('el-timer-fill');
    const timeEl = document.getElementById('el-time');
    if (fill)   { fill.style.width = (pct * 100).toFixed(1) + '%'; fill.style.background = pct > 0.5 ? '#2196F3' : pct > 0.25 ? '#FF9800' : '#F44336'; }
    if (timeEl) timeEl.textContent = Math.ceil(left / 1000);
    if (left <= 0) { clearInterval(_mg.timerId); _mg.running = false; elFinish(); }
  }, 50);
}

function elFinish() {
  clearInterval(_mg.timerId);
  _mg.running = false;
  _mg.locked  = false;

  const score = Math.min(100, Math.round((_mg.connected.size / _mg.total) * 100));
  const msg = score >= 100 ? '🌟 Panel fully wired!'      :
              score >= 75  ? '✅ Almost there!'             :
              score >= 40  ? '👍 Getting the hang of it!'  :
                             '⚡ A few loose wires...';

  const overlay = document.getElementById('el-overlay');
  if (overlay) {
    const res = document.createElement('div');
    res.className = 'el-result-overlay';
    res.innerHTML = `
      <div class="el-result-card">
        <div class="el-result-score">${score}%</div>
        <div class="el-result-label">wired up</div>
        <div class="el-result-msg">${msg}</div>
      </div>`;
    overlay.appendChild(res);
    setTimeout(() => { overlay.remove(); finishDIY(_mg.upgradeKey, score); }, 2200);
  } else {
    finishDIY(_mg.upgradeKey, score);
  }
}

// ── Mini-game: Rapid Press ────────────────────────────────────────────────────
// Mash the button as fast as possible in 3 seconds. 30 presses = 100%.
function launchRapidPress(upgradeKey) {
  _mg = { ..._mg, presses: 0, target: 30, upgradeKey, running: false, timerId: null };
  openModal(`
    <div class="modal-handle"></div>
    <div class="mg-wrap" style="background:#FFF8E1">
      <div class="mg-title">${pxIcon('🎨',20)} Roll It Out!</div>
      <div class="mg-desc">Keep that roller moving — cover the whole surface in 3 seconds!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#E65100" id="rp-count">0</div><div style="font-size:11px">Strokes</div></div>
        <div><div class="mg-stat-val" style="color:#E65100" id="rp-time">3.0</div><div style="font-size:11px">Seconds</div></div>
      </div>
      <div style="height:22px;background:#E0E0E0;border-radius:4px;overflow:hidden;margin-bottom:14px">
        <div id="rp-bar" style="width:0%;height:100%;border-radius:4px;background:linear-gradient(90deg,#EF9A9A,#CE93D8,#90CAF9,#A5D6A7,#FFF176);transition:width 0.1s"></div>
      </div>
      <button class="mg-rapid-btn" id="rp-btn" onclick="rpPress()" style="display:none;background:#E65100;font-size:22px">${pxIcon('🖌️',16)} ROLL!</button>
    </div>
    <button class="btn btn-full" id="rp-start" onclick="rpStart()" style="background:#F57C00;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">${pxIcon('🎨',16)} Dip the Roller</button>`);
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
      <div class="mg-title">${pxIcon('🪵',20)} Match the Tile!</div>
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
    <button class="btn btn-primary btn-full" id="cm-start" onclick="cmStart()">${pxIcon('🪵',16)} Open the Tile Box</button>`);
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
      <div class="mg-title" style="color:#1565C0">${pxIcon('📐',20)} Level It Up!</div>
      <div class="mg-desc" style="color:#546E7A">Watch the bubble — tap the instant it centers in the tube!</div>
      <div class="mg-stats">
        <div><div class="mg-stat-val" style="color:#1565C0" id="rt-round">1</div><div style="color:#546E7A;font-size:11px">Round</div></div>
        <div><div class="mg-stat-val" style="color:#1565C0" id="rt-best">—</div><div style="color:#546E7A;font-size:11px">Best ms</div></div>
      </div>
      <div class="mg-reaction-light" id="rt-light" style="background:#1565C0;border-color:#0D47A1;box-shadow:none">↔️</div>
      <button class="mg-reaction-tap-btn" id="rt-tap" onclick="rtTap()" disabled style="background:#37474F;letter-spacing:1px">Hold steady…</button>
    </div>
    <button class="btn btn-full" id="rt-start" onclick="rtStart()" style="background:#1565C0;color:white;padding:14px;font-size:16px;font-weight:800;border-radius:var(--radius-sm);border:none;width:100%">${pxIcon('📐',16)} Get the Level</button>`);
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
  if (starterSquatterActive()) {
    toast("There's still a squatter in your house. That's not going away on its own.", 'warning');
    return;
  }
  const res = await api('/advance', 'POST', { days });
  const s   = getSeasonInfo(res.day);
  const rentPaid     = res.events.filter(e => e.category === 'rent' && e.type === 'positive');
  const rentProblems = res.events.filter(e => e.category === 'rent' && e.type !== 'positive');
  const otherEvents  = res.events.filter(e => e.category !== 'rent');

  const eventRow = e => `
    <div class="event-item">
      <div class="event-dot ${e.type}"></div>
      <div class="event-info">
        <div class="event-prop">${e.prop}</div>
        <div class="event-text ${e.type}">${e.text}</div>
      </div>
    </div>`;

  let rentPaidHtml = '';
  if (rentPaid.length > 4) {
    const total = rentPaid.reduce((sum, e) => sum + (e.amount || 0), 0);
    rentPaidHtml = `
    <div class="event-item">
      <div class="event-dot positive"></div>
      <div class="event-info">
        <div class="event-text positive">Collected ${fmt(total)} from ${rentPaid.length} tenants</div>
      </div>
    </div>`;
  } else {
    rentPaidHtml = rentPaid.map(eventRow).join('');
  }

  const allRows = rentPaidHtml + rentProblems.map(eventRow).join('') + otherEvents.map(eventRow).join('');
  const eventsHtml = res.events.length === 0
    ? '<p class="text-muted text-center" style="padding:16px 0">Nothing happened.</p>'
    : allRows;

  _pendingRepairs       = res.repairs        || [];
  _pendingMoraleEvents  = res.morale_events  || [];
  _pendingRenewalOffers = res.renewal_offers || [];
  _pendingSquatter      = (res.events || []).find(e => e.type === 'squatter') || null;
  _pendingTaxEvent      = (res.tax_event && res.tax_event.amount >= 0) ? res.tax_event : null;
  const totalPending    = _pendingRepairs.length + _pendingMoraleEvents.length + _pendingRenewalOffers.length;
  const repairNote = _pendingRepairs.length > 0
    ? `<div style="background:var(--warning-bg,#FFF8E1);border:2px solid var(--warning);border-radius:var(--radius-sm);padding:10px 12px;margin-top:12px;font-size:13px;font-weight:700">
        ${pxIcon('🔧',16)} ${_pendingRepairs.length} repair${_pendingRepairs.length > 1 ? 's' : ''} need${_pendingRepairs.length === 1 ? 's' : ''} attention!</div>`
    : '';
  const moraleNote = _pendingMoraleEvents.length > 0
    ? `<div style="background:#F3E5F5;border:2px solid #CE93D8;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('💬',16)} ${_pendingMoraleEvents.length} tenant request${_pendingMoraleEvents.length > 1 ? 's' : ''} waiting!</div>`
    : '';
  const renewalNote = _pendingRenewalOffers.length > 0
    ? `<div style="background:#E8F5E9;border:2px solid #66BB6A;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🔄',16)} ${_pendingRenewalOffers.length} lease renewal${_pendingRenewalOffers.length > 1 ? 's' : ''} to review!</div>`
    : '';
  const taxNote = _pendingTaxEvent
    ? `<div style="background:#FFEBEE;border:2px solid #C62828;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🧾',16)} Tax Day! ${fmt(_pendingTaxEvent.amount)} owed — you must respond before continuing.</div>`
    : '';

  const btnLabel = _pendingRepairs.length > 0
    ? `Fix Repairs (${_pendingRepairs.length})`
    : _pendingMoraleEvents.length > 0
      ? `Respond to Requests (${_pendingMoraleEvents.length})`
      : _pendingRenewalOffers.length > 0
        ? `Review Leases (${_pendingRenewalOffers.length})`
        : 'Continue';

  if (totalPending > 0 || _pendingTaxEvent) _modalLocked = true;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(s.icon)} ${s.name} · Day ${s.seasonDay}</div>
    <div class="modal-subtitle">Year ${s.year} · Overall Day ${res.day}</div>
    <div class="money-row"><span class="mr-label">Cash</span><span class="mr-value">${fmt(res.cash)}</span></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Net Worth</span><span class="mr-value green">${fmt(res.net_worth)}</span></div>
    <div class="section-title" style="margin-bottom:8px">Events</div>
    ${eventsHtml}
    ${repairNote}
    ${moraleNote}
    ${renewalNote}
    ${taxNote}
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
  } else if (_pendingTaxEvent) {
    const te = _pendingTaxEvent;
    _pendingTaxEvent = null;
    showTaxModal(te);
  } else if (_pendingLevelUp) {
    _modalLocked = false;
    const lvl   = _pendingLevelUp;
    _pendingLevelUp = null;
    showLevelUpModal(lvl);
  } else {
    _modalLocked = false;
    closeModal();
  }
}

function showSquatterModal(propId, bribe, propName) {
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🚨',20)} Squatters!</div>
    <div class="modal-subtitle">${propName}</div>
    <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px">
      Someone has moved into your vacant property without permission. They're refusing to leave and not paying a dime. What do you want to do?
    </p>
    <div class="card" style="margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        ${pxIcon('💸',30)}
        <div>
          <div style="font-size:15px;font-weight:800">Pay Them Off</div>
          <div style="font-size:12px;color:var(--text-muted)">They'll leave immediately — no questions asked.</div>
        </div>
      </div>
      <div class="money-row" style="margin-bottom:10px">
        <span class="mr-label">Their asking price</span>
        <span class="mr-value" style="color:#C62828">${fmt(bribe)}</span>
      </div>
      <button class="btn btn-danger btn-full" onclick="briberSquatter(${propId})">${pxIcon('💸',14)} Pay ${fmt(bribe)} to Remove Them</button>
    </div>
    <div class="card">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        ${pxIcon('⏳',30)}
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

// ── Tax Modal ─────────────────────────────────────────────────────────────────
function showTaxModal(taxEvent) {
  _modalLocked = true;   // prevent dismiss by tapping outside
  const amount = taxEvent.amount;
  const income = taxEvent.flip_income;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🧾',20)} Tax Day</div>
    <div class="modal-subtitle">Winter Day 28 — You must respond before continuing</div>
    <div class="card" style="margin-bottom:14px">
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏠',14)} Flip income this year</span>
        <span class="mr-value green">${fmt(income)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('📊',14)} Tax rate</span>
        <span class="mr-value">10%</span>
      </div>
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Taxes owed</span>
        <span class="mr-value" style="color:#C62828">${fmt(amount)}</span>
      </div>
    </div>
    <button class="btn btn-danger btn-full" style="margin-bottom:10px" onclick="payTaxes()">${pxIcon('💸',16)} Pay ${fmt(amount)} Now</button>
    <button class="btn btn-secondary btn-full" onclick="fileTaxExtension()">${pxIcon('📋',14)} File for Extension — pay on Spring Day 7</button>
    <p style="font-size:11px;color:var(--text-muted);text-align:center;margin-top:10px">Rent income is never taxed — only profits from selling properties.</p>
  `);
}

async function payTaxes() {
  const res = await api('/pay_taxes', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  _modalLocked = false;
  await refreshState();
  renderAll();
  closeModal();
  toast(`Taxes paid: ${fmt(res.tax_paid)}`, 'warning');
}

async function fileTaxExtension() {
  const res = await api('/file_tax_extension', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  _modalLocked = false;
  await refreshState();
  renderAll();
  closeModal();
  toast(`Extension filed — ${fmt(res.tax_owed)} due by Spring Day 7`, 'info');
}

// ── Morale Events ─────────────────────────────────────────────────────────────
function showNextMoraleEvent() {
  if (_pendingMoraleEvents.length === 0) { continueFromEvents(); return; }
  showMoraleEventModal(_pendingMoraleEvents.shift());
}

function showMoraleEventModal(ev) {
  const damPct = Math.round(ev.damage_chance * 100);
  const prop    = state?.properties?.find(p => p.id === ev.prop_id);
  const morale  = prop?.tenant?.morale ?? ev.morale ?? '?';
  const cond    = prop?.condition ?? '?';
  const condLabel = cond !== '?' ? condTier(cond) : '?';
  const condColor = cond !== '?' ? tierColor(condLabel) : 'var(--text)';
  const moraleColor = morale >= 70 ? 'var(--positive)' : morale >= 40 ? 'var(--warning)' : 'var(--negative)';
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon)} Tenant Request</div>
    <div class="modal-subtitle">${ev.prop_name}</div>
    <div style="display:flex;gap:8px;margin-bottom:12px">
      <div style="flex:1;background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius-sm);padding:8px 10px;text-align:center">
        <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Condition</div>
        <div style="font-size:15px;font-weight:800;color:${condColor}">${condLabel}</div>
      </div>
      <div style="flex:1;background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius-sm);padding:8px 10px;text-align:center">
        <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Tenant Morale</div>
        <div style="font-size:15px;font-weight:800;color:${moraleColor}">${morale}%</div>
      </div>
    </div>
    <p style="font-size:14px;color:var(--text-2);margin-bottom:16px">${ev.message}</p>

    <div class="card" style="margin-bottom:10px;border:2px solid var(--positive)">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        ${pxIcon('✅',24)}
        <div style="flex:1">
          <div style="font-size:14px;font-weight:800">Agree</div>
          <div style="font-size:12px;color:var(--text-muted)">
            ${ev.cond_gain
              ? `Morale +${ev.morale_gain} · Condition +${ev.cond_gain}`
              : ev.cash_bonus
                ? `Morale +${ev.morale_gain} · Cash bonus $150–$350`
                : `Morale +${ev.morale_gain} · ${damPct}% chance of −${ev.damage_pts} condition`
            }
          </div>
        </div>
      </div>
      <button class="btn btn-primary btn-full" onclick="respondMoraleEvent(${ev.prop_id},'${ev.key}',true)">
        ${ev.agree_label}
      </button>
    </div>

    <div class="card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        ${pxIcon('❌',24)}
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
    } else if (res.condition_change > 0) {
      toast(`Nice work! Condition +${res.condition_change} pts`, 'success');
    } else if (res.cash_awarded > 0) {
      toast(`They paid extra! +$${res.cash_awarded.toLocaleString()}`, 'success');
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
    <div class="modal-title">${pxIcon('🔄',20)} Lease Renewal</div>
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
        ${pxIcon('✅',24)}
        <div><div style="font-size:14px;font-weight:800">Renew Lease</div>
          <div style="font-size:12px;color:var(--text-muted)">They stay for another ${stayLabel} at the same rent</div>
        </div>
      </div>
      <button class="btn btn-primary btn-full" onclick="respondRenewal(${offer.prop_id}, true)">Renew Lease</button>
    </div>

    <div class="card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        ${pxIcon('👋',24)}
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
    <div class="modal-title">${pxIcon(rt.icon)} ${rt.name}</div>
    <div class="modal-subtitle">${repair.prop_name}</div>
    <p style="font-size:13px;color:var(--text-2);margin-bottom:12px">Your tenant reported a problem. Address it now or ignore and let the condition drop.</p>

    <div class="contractor-card" style="border-color:var(--primary);margin-bottom:8px" onclick="startRepairDIY()">
      <div class="contractor-header">
        <span class="contractor-icon">${pxIcon('🧰',28)}</span>
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
    <div class="modal-title">${pxIcon('🔧',20)} Repair Done!</div>
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
  if (tab === 'taxes')  renderTaxes();
}

function renderFinances() {
  switchFinTab(currentFinTab);
}

function renderTaxes() {
  const el = document.getElementById('fin-taxes');
  if (!el) return;
  if (!firstSaleDone()) {
    el.innerHTML = `
      <div style="padding:32px 20px;text-align:center">
        <div style="margin-bottom:12px">${pxIcon('🔒',44)}</div>
        <div style="font-size:15px;font-weight:800;margin-bottom:8px">Taxes Locked</div>
        <div style="font-size:13px;color:var(--text-muted);line-height:1.6;max-width:280px;margin:0 auto">You have to actually make money before Uncle Sam cares where it went. Go sell something.</div>
      </div>`;
    return;
  }
  const s          = getLocalState();
  if (!s) return;
  const flipIncome = s.tax_year_flip_income || 0;
  const rentIncome = s.tax_year_rent_income || 0;
  const totalIncome = flipIncome + rentIncome;
  const estimated  = Math.floor(flipIncome * 0.10);
  const extFiled   = s.tax_extension_filed  || false;
  const taxOwed    = s.tax_owed             || 0;
  el.innerHTML = `
    <div class="section-header"><span class="section-title">${pxIcon('🧾',18)} Taxes</span></div>
    <div class="card" style="margin-bottom:12px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:10px">Income This Year</div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏠',14)} Rent collected</span>
        <span class="mr-value green">${fmt(rentIncome)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('💰',14)} Flip profits (taxable)</span>
        <span class="mr-value green">${fmt(flipIncome)}</span>
      </div>
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Total income</span>
        <span class="mr-value green">${fmt(totalIncome)}</span>
      </div>
    </div>
    <div class="card" style="margin-bottom:12px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:10px">Tax Summary</div>
      <div class="money-row">
        <span class="mr-label">Taxable income (flip only)</span>
        <span class="mr-value">${fmt(flipIncome)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">Tax rate</span>
        <span class="mr-value">10%</span>
      </div>
      <div class="money-row" style="font-weight:800">
        <span class="mr-label">Est. taxes owed</span>
        <span class="mr-value" style="color:${estimated > 0 ? '#C62828' : 'var(--text-muted)'}">
          ${fmt(estimated)}
        </span>
      </div>
    </div>
    ${extFiled ? `
    <div class="card" style="background:#FFF8E1;border:2px solid var(--warning);margin-bottom:12px">
      <div style="font-size:14px;font-weight:800;margin-bottom:6px">${pxIcon('⏳',16)} Extension Filed</div>
      <div class="money-row">
        <span class="mr-label">Amount due Spring Day 7</span>
        <span class="mr-value" style="color:#C62828">${fmt(taxOwed)}</span>
      </div>
    </div>` : ''}
    <div class="card" style="font-size:12px;color:var(--text-muted)">
      💡 Rent income is <strong>never taxed</strong>. Only profits from selling properties are taxed at 10%.<br><br>
      ${pxIcon('📅',14)} Tax Day is <strong>Winter Day 28</strong>. You'll get a 7-day heads-up. Pay immediately or file a free extension (due Spring Day 7).
    </div>
  `;
}

async function renderBank() {
  if (!firstSaleDone()) {
    const note = starterSquatterActive()
      ? "I could deposit this... but then I'd have nothing left to bribe the squatter with. Savings account can wait."
      : "A savings account with nothing in it. Bold strategy. Sell the house first.";
    const lockHtml = `
      <div style="padding:32px 20px;text-align:center">
        <div style="margin-bottom:12px">${pxIcon('🔒',44)}</div>
        <div style="font-size:15px;font-weight:800;margin-bottom:8px">Bank Locked</div>
        <div style="font-size:13px;color:var(--text-muted);line-height:1.6;max-width:280px;margin:0 auto">${note}</div>
      </div>`;
    document.getElementById('bank-savings-section').innerHTML = lockHtml;
    document.getElementById('bank-loans-section').innerHTML = '';
    document.getElementById('bank-products-section').innerHTML = '';
    return;
  }
  const data = await api('/bank/products');
  const bank = state.bank || { savings: 0, loans: [] };
  const tier = state.savings_tier || data.savings_tiers[0];

  const nextTier  = data.savings_tiers.find(t => t.min > bank.savings);
  const toNextLbl = nextTier ? `${fmt(nextTier.min - bank.savings)} more to ${nextTier.label}` : 'Max tier reached!';
  const tierClass = tier.label === 'Basic' ? 'budget' : tier.label === 'Standard' ? 'mid' : 'premium';

  document.getElementById('bank-savings-section').innerHTML = `
    <div class="section-header"><span class="section-title">${pxIcon('💰',18)} Savings Account</span></div>
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
            <div class="card-icon">${pxIcon(l.icon)}</div>
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
          <button class="btn btn-ghost btn-sm" onclick="showExtraPaymentModal(${l.id}, ${Math.ceil(l.balance)})">${pxIcon('💸',14)} Extra Payment</button>
        </div>`;}).join('')
    : '';

  document.getElementById('bank-loans-section').innerHTML = bank.loans?.length > 0
    ? `<div class="section-header"><span class="section-title">${pxIcon('📄',18)} Active Loans</span></div>${loansHtml}`
    : '';

  document.getElementById('bank-products-section').innerHTML = `
    <div class="section-header"><span class="section-title">${pxIcon('🏦',18)} Take Out a Loan</span></div>
    ${data.products.map(p => `
      <div class="card" style="cursor:pointer" onclick="showLoanModal('${p.key}')">
        <div class="card-header">
          <div class="card-icon">${pxIcon(p.icon)}</div>
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
      <div class="modal-title">${pxIcon(p.icon)} ${p.name}</div>
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
    <div class="modal-title">${pxIcon('💸',20)} Extra Loan Payment</div>
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
    <div class="section-header"><span class="section-title">${pxIcon('⚙️',18)} Settings</span></div>

    <div class="card">
      <div style="font-size:14px;font-weight:800;margin-bottom:12px">Game Info</div>
      <div class="money-row"><span class="mr-label">Current Day</span><span class="mr-value">${state.day}</span></div>
      <div class="money-row"><span class="mr-label">Season</span><span class="mr-value">${pxIcon(s.icon)} ${s.name} — Year ${s.year}</span></div>
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
      <button class="btn btn-danger btn-full" onclick="confirmReset()">${pxIcon('🗑',16)} Start New Game</button>
    </div>

    <div class="section-header" style="margin-top:16px"><span class="section-title">${pxIcon('📋',18)} Activity Log</span></div>
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
      if (!state.intro_seen) {
        showIntroScreen();
      } else {
        await loadMarket();
        renderAll();
        navTo('dashboard');
      }
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
  el.innerHTML = `<div class="empty-state"><div class="empty-icon">${pxIcon('💹',48)}</div><div class="empty-text">Loading…</div></div>`;
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
      <div class="stocks-lock-icon">${pxIcon('🔒',44)}</div>
      <div class="stocks-lock-msg">Stocks unlock at <strong>Level 5</strong></div>
      <div class="stocks-lock-sub">Keep growing your property empire to gain access to the stock market.</div>
    </div>`;
    return;
  }

  let html = `<div class="stocks-section-header">
    <span class="stocks-section-icon">${pxIcon('📈',22)}</span>
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
      <span>${pxIcon('📦',14)} ${shares} share${shares !== 1 ? 's' : ''}</span>
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
    <div class="modal-title">${pxIcon(inst.icon)} Buy ${inst.name}</div>
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
    <div class="modal-title">${pxIcon(inst.icon)} Sell ${inst.name}</div>
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
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">${pxIcon('📋',48)}</div><div class="empty-text">No history yet</div></div>`;
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
  if (handle) handle.addEventListener('click', () => {
    if (_modalLocked || _mg.locked) return;
    if (_inPropSubModal) backToProperty(); else closeModal();
  }, { once: true });
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  _pendingConfirm = null;
  _propDetailId   = null;
  _inPropSubModal = false;
  if (_pendingLevelUp && !_modalLocked) {
    const lvl   = _pendingLevelUp;
    _pendingLevelUp = null;
    setTimeout(() => showLevelUpModal(lvl), 80);
  }
}

function backToProperty() {
  const id = _propDetailId;
  _inPropSubModal = false;
  // If a level-up is waiting, show it before going back to property
  if (_pendingLevelUp && !_modalLocked) {
    const lvl   = _pendingLevelUp;
    _pendingLevelUp = null;
    showLevelUpModal(lvl);
    return;
  }
  if (id != null) showPropertyDetail(id);
  else closeModal();
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
  if (_mg.locked || _modalLocked) return;
  if (e.target === this) {
    if (_inPropSubModal) backToProperty(); else closeModal();
  }
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = '') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  el.innerHTML = `${icons[type] ? `<span>${icons[type]}</span>` : ''}${msg}`;
  el.style.cssText += ';cursor:pointer;pointer-events:auto';
  const dismiss = () => el.remove();
  el.addEventListener('click', dismiss);
  el.addEventListener('touchstart', dismiss, { passive: true });
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
