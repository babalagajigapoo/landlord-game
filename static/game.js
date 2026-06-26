// Apply saved dark mode before first render to prevent flash
if (localStorage.getItem('darkMode') === '1') document.body.classList.add('dark');

// ── Pixel Art Icons (cleared — all icons use raw emoji) ──────────────────────
const PIXEL_ICONS = {};


function pxIcon(emoji, size) {
  return emoji || '';
}

// Custom house art (baked-in SVG so it's identical on every device).
// Rental types pick a good or run-down model by condition (>=75 / C-tier = good).
const PROP_MODEL_SLUG = { 'Bungalow':'bungalow', 'Ranch House':'ranch', 'Colonial':'colonial',
  'Townhouse':'townhouse', 'Condo':'condo', 'Duplex':'duplex', 'Mansion':'mansion' };
function propModelImg(p, size) {
  const slug  = PROP_MODEL_SLUG[p.type] || 'ranch';
  const cond  = (p.condition >= 75) ? 'good' : 'bad';
  const px    = size || 48;   // inline style overrides the shared .card-icon/.prop-icon-circle img rule
  return `<img src="/static/icons/prop-${slug}-${cond}.svg" alt="${p.type}" style="width:${px}px;height:${px}px;display:block">`;
}
function homeModelImg(key, size) {
  const px = size || 48;
  return `<img src="/static/icons/myhome-${key}.svg" alt="" style="width:${px}px;height:${px}px;display:block">`;
}

// ── State ─────────────────────────────────────────────────────────────────────
let state           = null;

function starterSquatterActive() {
  return !!(state?.properties?.find(p => p.squatter?.starter));
}
function firstSaleDone() {
  return (state?.level || 0) >= 1;
}
let marketListings      = [];
let commercialListings  = [];
let marketHoodOpen     = {};   // tracks which hood sections are expanded; undefined = open
let _currentMarketTab  = 'residential';
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
  'Cedarvale Estates': 'premium',
};

const NEW_BUILDS_UNLOCK_LEVEL    = 9;
const COMMERCE_ROW_UNLOCK_LEVEL  = 11;

const COMMERCIAL_TYPES_DATA = {
  strip_mall:      { name: 'Strip Mall',          icon: '🏪', unit_count: 4, price: 950000,   overhead: 2500, sqft: 8000,  superintendent_monthly: 3500, maintenance_monthly: 2500, emergency_repair_cost: 12000, desc: 'Four retail-facing storefronts. High traffic, high turnover.' },
  office_building: { name: 'Office Building',     icon: '🏢', unit_count: 3, price: 1400000,  overhead: 3500, sqft: 12000, superintendent_monthly: 4500, maintenance_monthly: 3200, emergency_repair_cost: 15000, desc: 'Professional tenants, longer leases, quieter events.' },
  mixed_use:       { name: 'Mixed-Use Building',  icon: '🏬', unit_count: 5, price: 1800000,  overhead: 4000, sqft: 18000, superintendent_monthly: 5500, maintenance_monthly: 3800, emergency_repair_cost: 20000, desc: 'Three commercial floors and two upper-level office suites.' },
};

const ASSISTANTS_DATA = {
  manager:    { name: 'Property Manager', icon: '🤝', unlock_level: 11, monthly_fee: 20000, desc: 'Full hands-off management. Automatically handles every tenant issue, repair, story event, and lease renewal across all your rentals — true passive income.' },
  accountant: { name: 'Accountant',       icon: '🧮', unlock_level: 3,  monthly_fee: 2800,  desc: 'Auto-files your taxes on time every year and finds 15% more deductible write-offs. The retainer itself is a deductible expense.' },
  leasing_agent: { name: 'Commercial Leasing Agent', icon: '🤝', unlock_level: 11, monthly_fee: 7000, desc: 'Keeps Commerce Row leased — automatically fills vacant units with strong, complementary tenants so you never have to court applicants. (Building events are handled per-building by Superintendents.)' },
};

const COMMERCIAL_UPGRADES_DATA = {
  security_system:  { name: 'Security System',         icon: '🔒', cost: 12000, desc: 'Cuts inspection failures and sudden closures by 60%.' },
  commercial_hvac:  { name: 'Commercial HVAC',          icon: '❄️', cost: 18000, desc: '35% less daily condition loss from tenant wear.' },
  renovated_common: { name: 'Renovated Common Areas',   icon: '✨', cost: 25000, desc: 'All unit rents permanently +8%.' },
  fiber_internet:   { name: 'Fiber Internet',           icon: '📡', cost: 9000,  desc: 'Law offices & accounting firms +$500/mo.' },
  parking_expansion:{ name: 'Parking Expansion',        icon: '🅿️', cost: 20000, desc: 'Reduces events for high-traffic tenants by 40%.' },
  exterior_facelift:{ name: 'Exterior Facelift',        icon: '🎨', cost: 30000, desc: '+40 condition immediately. All units +$300/mo.' },
};

const BUSINESS_TENANT_DATA = {
  restaurant:       { name: 'Restaurant',       icon: '🍽️', monthly_rent: 8500,  lease_days: 112, desc: 'High traffic. Great rent but inspections are common.' },
  retail:           { name: 'Retail Shop',      icon: '🛍️', monthly_rent: 5500,  lease_days: 84,  desc: 'Short leases, decent income. Moderate turnover.' },
  law_office:       { name: 'Law Office',       icon: '⚖️', monthly_rent: 9000,  lease_days: 224, desc: 'Quiet, long-term, pays well.' },
  salon:            { name: 'Salon',            icon: '💈', monthly_rent: 6000,  lease_days: 112, desc: 'Steady income, reasonable events.' },
  gym:              { name: 'Gym',              icon: '🏋️', monthly_rent: 11000, lease_days: 168, desc: 'Highest rent, but heavy wear.' },
  coffee_shop:      { name: 'Coffee Shop',      icon: '☕', monthly_rent: 4200,  lease_days: 84,  desc: 'Popular morning anchor. Steady traffic, low drama.' },
  barber_shop:      { name: 'Barber Shop',      icon: '🪒', monthly_rent: 3500,  lease_days: 84,  desc: 'Low rent, low drama. Community staple.' },
  nail_salon:       { name: 'Nail Salon',       icon: '💅', monthly_rent: 3800,  lease_days: 84,  desc: 'Steady clientele. Reliable rent, minimal issues.' },
  pawn_shop:        { name: 'Pawn Shop',        icon: '🏷️', monthly_rent: 4800,  lease_days: 56,  desc: 'High-traffic, high-risk. Short leases, frequent events.' },
  tattoo_studio:    { name: 'Tattoo Studio',    icon: '🎨', monthly_rent: 5200,  lease_days: 56,  desc: 'Creative energy. Shorter leases, busier than expected.' },
  auto_parts:       { name: 'Auto Parts Store', icon: '🔧', monthly_rent: 6800,  lease_days: 84,  desc: 'Industrial foot traffic. Decent rent, moderate wear.' },
  daycare:          { name: 'Daycare Center',   icon: '🧒', monthly_rent: 6200,  lease_days: 168, desc: 'Long leases, community anchor. Inspections are standard.' },
  accounting_firm:  { name: 'Accounting Firm',  icon: '📊', monthly_rent: 8000,  lease_days: 168, desc: 'Professional and quiet. Long-term, low hassle.' },
  pharmacy:         { name: 'Pharmacy',         icon: '💊', monthly_rent: 10000, lease_days: 112, desc: 'High-demand essential business. Very low drama.' },
  tech_startup:     { name: 'Tech Startup',     icon: '💻', monthly_rent: 9500,  lease_days: 56,  desc: 'High rent but they pivot fast. Short leases, frequent events.' },
  medical_clinic:   { name: 'Medical Clinic',   icon: '🏥', monthly_rent: 12500, lease_days: 224, desc: 'Top-tier rent, longest leases. Nearly zero trouble.' },
  dental_office:    { name: 'Dental Office',    icon: '🦷', monthly_rent: 11000, lease_days: 224, desc: 'Ultra-reliable. Great rent, iron-clad leases.' },
  flooring_express: { name: 'Flooring Express', icon: '🏪', monthly_rent: 20000, lease_days: 224, desc: '⭐ SPECIAL — Pays double. Never any issues.', special: true },
};

// ── Commercial overhaul mirrors (match app.py) ──────────────────────────────
const BUSINESS_TENANT_CAT = {
  restaurant:'food', coffee_shop:'food',
  retail:'retail', pawn_shop:'retail', auto_parts:'retail', flooring_express:'retail',
  salon:'service', barber_shop:'service', nail_salon:'service', tattoo_studio:'service',
  law_office:'professional', accounting_firm:'professional', tech_startup:'professional',
  gym:'health', daycare:'health', medical_clinic:'health', dental_office:'health', pharmacy:'health',
};
const CAT_LABEL = { food:'Food', retail:'Retail', service:'Service', professional:'Professional', health:'Health' };
const CAT_ICON  = { food:'🍴', retail:'🛍️', service:'✂️', professional:'💼', health:'➕' };
const BUSINESS_ANCHORS = new Set(['restaurant','coffee_shop','gym','pharmacy','medical_clinic']);
const BUSINESS_PCT_MAX = {
  restaurant:4000, coffee_shop:2200, retail:2600, pawn_shop:1800, auto_parts:1600,
  salon:1500, barber_shop:900, nail_salon:1000, tattoo_studio:1400, gym:2500,
};

const BUILD_CREWS_DATA = {
  handys:   { name: "Handy's Crew",      icon: '🔨', buy_cost:  15000, daily_rate:  400, speed_mult: 1.00, desc: "Small local crew. Reliable, affordable. Best value on small builds." },
  summit:   { name: 'Summit Builders',   icon: '🏗️', buy_cost:  35000, daily_rate:  700, speed_mult: 0.85, desc: "Mid-size team with solid references. 15% faster than Handy's." },
  apex:     { name: 'Apex Construction', icon: '⚙️', buy_cost:  75000, daily_rate: 1200, speed_mult: 0.70, desc: "Professional outfit. 30% faster. Worth it on larger projects." },
  pinnacle: { name: 'Pinnacle Group',    icon: '🏆', buy_cost: 150000, daily_rate: 2000, speed_mult: 0.55, desc: "Elite construction firm. Nearly twice the speed. Premium price." },
};

const NEW_BUILD_SIZES_DATA = {
  studio:    { name: 'Studio Cottage',  icon: '🏠', base_days:  84, build_cost:  80000, finished_value:  300000, desc: "Compact single-story cottage. Quick build, solid return on a budget." },
  townhouse: { name: 'Townhouse',       icon: '🏘️', base_days: 140, build_cost: 160000, finished_value:  450000, desc: "Two-story townhouse with modern finishes. Good rental or flip." },
  sfh:       { name: 'Single Family',   icon: '🏡', base_days: 168, build_cost: 280000, finished_value:  700000, desc: "Classic single-family home. Strong value, broad appeal." },
  executive: { name: 'Executive Home',  icon: '🏰', base_days: 196, build_cost: 450000, finished_value: 1100000, desc: "Spacious executive residence. Premium lot, premium returns." },
  estate:    { name: 'Estate',          icon: '🏯', base_days: 224, build_cost: 700000, finished_value: 1750000, desc: "The flagship build. Two full years in construction. Worth every day." },
};

const PREMIUM_UPGRADES_DATA = {
  ev_charger: { name: 'EV Charging Station', icon: '⚡', cost:  4000, rent_bonus:  20, value_bonus:  5000 },
  smarthome:  { name: 'Smart Home Package',  icon: '📱', cost:  5500, rent_bonus:  32, value_bonus:  7000 },
  deck:       { name: 'Deck & Patio',        icon: '🪵', cost:  9000, rent_bonus:  45, value_bonus: 11000 },
  hot_tub:    { name: 'Hot Tub / Spa',       icon: '🛁', cost: 12000, rent_bonus:  60, value_bonus: 13000 },
  garage:     { name: '2-Car Garage',        icon: '🚗', cost: 16000, rent_bonus:  85, value_bonus: 20000 },
  solar:      { name: 'Solar Panel Array',   icon: '☀️', cost: 19000, rent_bonus:  65, value_bonus: 22000 },
  basement:   { name: 'Finished Basement',   icon: '🏗️', cost: 22000, rent_bonus: 130, value_bonus: 27000 },
  pool:       { name: 'Swimming Pool',       icon: '🏊', cost: 28000, rent_bonus: 175, value_bonus: 32000 },
  adu:        { name: 'Guest House / ADU',   icon: '🏡', cost: 48000, rent_bonus: 325, value_bonus: 55000 },
};

let _prevCash = null;   // tracks last known cash for float animation

// ── Mini-game state ───────────────────────────────────────────────────────────
let _mg             = {};   // active mini-game state
let _modalLocked          = false; // true while event flow is in progress (repairs/morale/tax/etc.)
let _propDetailId         = null;  // id of the property currently open in detail modal
let _inPropSubModal       = false; // true when a sub-modal inside a property detail is open
let _propHoodOpen         = {};    // { 'Maplewood Heights': false } — collapsed neighborhoods
let _commercialExpanded   = {};    // { propId: true } — expanded commercial cards
let _propHoodTab          = {};    // { 'Maplewood Heights': 'vacant' } — active sub-tab per hood
let _pendingLevelUp       = null;  // new level number waiting to be shown after all other modals
let _pendingRepairs       = [];   // repair events queued after advancing
let _currentRepair        = null; // repair being handled right now
let _pendingJob           = null; // side job being played
let _pendingSquatter         = null; // squatter event queued after repairs
let _pendingCommercialEvents = [];   // commercial events (lease renewals, inspections, subletting)
let _currentCommercialEvent  = null; // the commercial event currently shown in the modal
let _pendingRenewalOffers = [];   // lease renewal offers queued after advancing
let _pendingStorylets     = [];   // multi-stage tenant situations queued after advancing
let _pendingVendingEvents = [];   // vending machine choice-card events queued after advancing
let _currentVendingEvent  = null; // vending event being decided right now
let _pendingArcadeEvents  = [];   // arcade choice-card events queued after advancing
let _currentArcadeEvent   = null; // arcade event being decided right now
let _pendingPoleEvents    = [];   // pole-studio choice-card events queued after advancing
let _currentPoleEvent     = null; // pole-studio event being decided right now
let _pendingCarWashEvents = [];   // car-wash choice-card events queued after advancing
let _currentCarWashEvent  = null; // car-wash event being decided right now
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
  { key: 'grandmas_basement', name: "Grandma's Basement", icon: '🛋️', cost:       0, unlock_level:  0, desc: "Grandma's got a cot, a leaky fridge, and opinions about your life choices. Free rent — if you can survive the casserole." },
  { key: 'small_apt',         name: 'Small Apartment',    icon: '🏠',  cost:   80000, unlock_level:  2, desc: 'Thin walls, no dishwasher, and a neighbor who practices drums at midnight. Still yours.' },
  { key: 'condo',             name: 'Condo',              icon: '🏢',  cost:  150000, unlock_level:  4, desc: 'An HOA fee and a parking sticker — welcome to adulthood.' },
  { key: 'small_home',        name: 'Small Home',         icon: '🏡',  cost:  250000, unlock_level:  7, desc: 'A real yard. A real mortgage. A real lawn to mow at 7am on a Saturday.' },
  { key: 'suburban_home',     name: 'Suburban Home',      icon: '🏘️',  cost:  400000, unlock_level:  9, desc: 'Cul-de-sac living with a two-car garage and a wave-hello relationship with the neighbors.' },
  { key: 'luxury_villa',      name: 'Luxury Villa',       icon: '🏛️',  cost:  750000, unlock_level: 11, desc: 'Heated floors, a wine cellar, and someone else mows the lawn.' },
  { key: 'mansion',           name: 'Mansion',            icon: '🏰',  cost: 1500000, unlock_level: 13, desc: "You have a butler named Gerald and a room you've never entered. Peak existence." },
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

// ── One-time forced wipe ──────────────────────────────────────────────────────
// Resets every player's save exactly ONCE — the first time they open this build.
// A localStorage flag makes it self-disabling: after the wipe the flag is set and
// the reset never runs again. DO NOT change ONE_TIME_RESET_KEY — bumping it would
// wipe everyone's progress all over again. Only ever introduce a NEW key (and a
// new reason) if a future forced reset is genuinely intended.
const ONE_TIME_RESET_KEY = 'landlord_forced_reset_2026_06_22';
function runOneTimeReset() {
  try {
    if (localStorage.getItem(ONE_TIME_RESET_KEY)) return;   // already done — never again
    clearLocalState();                                       // wipe the save (if any)
    localStorage.setItem(ONE_TIME_RESET_KEY, '1');           // mark it consumed forever
  } catch {}
}

// Keep --hdr-h in sync with the real header height so bottom-sheet modals stop
// below the header (the cash/level/energy bar stays visible while a menu is open).
function syncHeaderHeight() {
  const h = document.querySelector('header');
  if (h && h.offsetHeight) document.documentElement.style.setProperty('--hdr-h', h.offsetHeight + 'px');
}
window.addEventListener('resize', syncHeaderHeight);
window.addEventListener('load', syncHeaderHeight);

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  runOneTimeReset();   // must run BEFORE refreshState loads the old save
  setupNav();
  await refreshState();
  syncHeaderHeight();
  if (!state.intro_seen) {
    // New game: tell grandma's story — but only after the opening splash finishes.
    whenSplashDone(showIntroScreen);
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
  // Milestones can unlock from any action — toast any that just completed.
  const _ms = (state.empire && state.empire.just_unlocked) || [];
  _ms.forEach(m => toast(`🏅 Milestone: ${m.name}${m.reward ? ' · +' + fmt(m.reward) : ''}`, 'success'));
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
  if (typeof applyGameMode === 'function') applyGameMode();   // dark-mode router (separate module)
  if (typeof DARK !== 'undefined' && DARK.maybeOffer) DARK.maybeOffer();   // Level-11 dark-side dilemma
  if (typeof DARK !== 'undefined' && DARK.checkFixer) DARK.checkFixer();   // Fixer debt story beats
}

async function loadMarket() {
  const data      = await api('/market');
  marketListings  = data.listings || [];
  commercialListings = data.commercial_listings || [];
}

// ── Header ────────────────────────────────────────────────────────────────────
function updateHeader() {
  const cashEl  = document.getElementById('hdr-cash');
  const newCash = state.cash;
  if (_prevCash !== null && _prevCash !== newCash) {
    animateCashChange(newCash - _prevCash);
    animateCounter(cashEl, _prevCash, newCash);
    if (newCash > _prevCash) sfx.cash();
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
  updateMusicMode();
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
        unlocks: ["📈 Keep scaling — the premium districts are yours to dominate", "💃 Brass Pole Fitness Studio unlocked in Business tab ($600,000) — 6 poles, 6 dancers, one very confused Gary"] },
  9:  { joke: "Heated floors. A wine cellar. Someone else mows the lawn. You made it.",
        unlocks: ["🏛️ Luxury Villa available in Personal → Homes ($750,000)", "🏗️ New Builds unlocked — build homes from scratch in Cedarvale Estates (buy a permit in Personal → New Builds)"] },
  10: { joke: "Double digits. Gerald can already smell the ambition from here.",
        unlocks: ["📈 Endgame territory — maximize every income stream", "🚗 Speedy Suds Car Wash unlocked in Business tab"] },
  11: { joke: "Strip malls, office buildings, and gyms. Your empire just went corporate.",
        unlocks: ["🏙️ Commerce Row unlocked — buy commercial properties in the Market (Strip Malls, Office Buildings, Mixed-Use Buildings)", "📈 Commercial tenants pay monthly: Restaurants $8,500, Law Offices $9,000, Gyms $11,000"] },
  12: { joke: "There's a room in the Mansion you've never entered. Gerald has been living there.",
        unlocks: ["🏰 Mansion available in Personal → Homes ($1,500,000)"] },
  13: { joke: "Thirteen. The city is basically yours at this point. Don't tell the tenants.",
        unlocks: ["📈 The empire is yours — squeeze every dollar from it"] },
  14: { joke: "Maximum level. You built an empire from a basement casserole. Grandma is complicated about it.",
        unlocks: ["🏆 Max level reached — the empire is complete"] },
};

function showLevelUpModal(newLevel) {
  sfx.levelUp();
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
  sfx.infoOpen();
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
    btn.addEventListener('click', () => { sfx.tap(); navTo(btn.dataset.page); });
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
  if (page === 'finances')   renderFinances();
  if (page === 'settings')   renderSettings();
  if (page === 'personal')   renderPersonal();
  if (page === 'business')   renderBusiness();
  if (page === 'store')      { _costproOpen = {}; renderStore(); }
  if (page === 'properties') { renderProperties(); if (_currentPropTab === 'newbuilds') renderNewBuilds(); if (_currentPropTab === 'commercial') renderCommercial(); }
}

// ── Render All ────────────────────────────────────────────────────────────────
function renderAll() {
  setupMusicAutoStart();
  setupSfxAutoStart();
  renderDashboard();
  renderMarket();
  if (_currentMarketTab === 'commercial') renderCommercialMarket();
  renderProperties();
  if (_currentPropTab === 'newbuilds')  renderNewBuilds();
  if (_currentPropTab === 'commercial') renderCommercial();
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

  // Mogul Rank + Milestones
  renderMogul();
  renderMilestones();

  // Side jobs
  renderJobs();
}

let _milestonesOpen = false;
function toggleMilestones() {
  _milestonesOpen = !_milestonesOpen;
  const t = document.getElementById('dash-milestones-toggle');
  if (t) t.textContent = _milestonesOpen ? '▴' : '▾';
  renderMilestones();
}

function renderMogul() {
  const el = document.getElementById('dash-mogul');
  const e  = state && state.empire;
  if (!el || !e) return;
  const next = e.next_rank_name
    ? `<span style="font-size:11px;color:var(--text-muted)">Next: <strong>${e.next_rank_name}</strong> at ${fmt(e.next_rank_score)}</span>`
    : `<span style="font-size:11px;color:var(--positive);font-weight:800">👑 Maximum rank — you own the whole damn city.</span>`;
  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:12px">
      <span style="font-size:40px;line-height:1">${pxIcon(e.rank_icon, 40)}</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:17px;font-weight:900">${e.rank_name}</div>
        <div style="font-size:12px;color:var(--text-muted)">Empire Score <strong style="color:var(--text-1)">${fmt(e.score)}</strong></div>
      </div>
    </div>
    <div class="condition-bar" style="margin-top:10px"><div class="condition-fill cond-great" style="width:${e.progress_pct}%"></div></div>
    <div style="display:flex;justify-content:space-between;margin-top:5px">${next}<span style="font-size:11px;color:var(--text-muted)">${e.progress_pct}%</span></div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;font-size:10px;color:var(--text-muted)">
      <span style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:2px 8px">💵 Wealth ${fmt(e.total_wealth)}</span>
      <span style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:2px 8px">🏢 ${e.businesses_owned}/6 businesses +${fmt(e.businesses_owned * e.business_bonus)}</span>
      <span style="background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:2px 8px">🏅 ${e.milestones_done}/${e.milestones_total} milestones +${fmt(e.milestones_done * e.milestone_bonus)}</span>
    </div>`;
}

function renderMilestones() {
  const el = document.getElementById('dash-milestones');
  const e  = state && state.empire;
  if (!el || !e) return;
  const t = document.getElementById('dash-milestones-toggle');
  if (t) t.textContent = _milestonesOpen ? '▴' : '▾';
  if (!_milestonesOpen) {
    el.innerHTML = `<div class="card" style="text-align:center;font-size:12px;color:var(--text-muted);padding:10px;cursor:pointer" onclick="toggleMilestones()">
      ${e.milestones_done} of ${e.milestones_total} completed — tap to view</div>`;
    return;
  }
  const rows = e.milestones.map(m => `
    <div style="display:flex;align-items:center;gap:10px;padding:8px 10px;border-bottom:1px solid var(--border);opacity:${m.done ? 1 : 0.55}">
      <span style="font-size:20px;line-height:1">${m.done ? '✅' : pxIcon(m.icon, 18)}</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:13px;font-weight:700">${m.name}</div>
        <div style="font-size:11px;color:var(--text-muted)">${m.desc}</div>
      </div>
      <span style="text-align:right;white-space:nowrap;flex-shrink:0">
        <span style="font-size:12px;font-weight:800;color:${m.done ? 'var(--positive)' : 'var(--text-muted)'}">+${fmt(m.reward)}</span>
        ${m.done ? '<div style="font-size:9px;font-weight:800;color:var(--positive);letter-spacing:0.5px">DONE</div>' : ''}
      </span>
    </div>`).join('');
  el.innerHTML = `<div class="card" style="padding:0;overflow:hidden">${rows}</div>`;
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

function switchMarketTab(tab) {
  sfx.tab();
  _currentMarketTab = tab;
  ['residential', 'commercial'].forEach(t => {
    const el  = document.getElementById('mkt-' + t);
    const btn = document.querySelector(`.fin-tab[data-mkt-tab="${t}"]`);
    if (el)  el.style.display = t === tab ? '' : 'none';
    if (btn) btn.classList.toggle('active', t === tab);
  });
  if (tab === 'commercial') renderCommercialMarket();
}

function renderCommercialMarket() {
  const el = document.getElementById('commercial-market-list');
  if (!el || !state) return;
  const level = state.level || 0;
  if (level < COMMERCE_ROW_UNLOCK_LEVEL) {
    el.innerHTML = `<div class="empty-state" style="padding:32px 16px;text-align:center">
      <div style="font-size:48px;margin-bottom:12px">${pxIcon('🔒', 48)}</div>
      <div style="font-size:15px;font-weight:800;margin-bottom:6px">Unlocks at Level ${COMMERCE_ROW_UNLOCK_LEVEL}</div>
      <div style="font-size:12px;color:var(--text-muted)">Reach Level ${COMMERCE_ROW_UNLOCK_LEVEL} to unlock Strip Malls, Office Buildings, and Mixed-Use properties.</div>
    </div>`;
    return;
  }
  if (commercialListings.length === 0) {
    el.innerHTML = `<div class="empty-state" style="padding:32px 16px;text-align:center">
      <div style="font-size:48px;margin-bottom:12px">${pxIcon('🏙️', 48)}</div>
      <div style="font-size:15px;font-weight:800;margin-bottom:6px">No commercial listings</div>
      <div style="font-size:12px;color:var(--text-muted)">All buildings have been purchased. Advance time to refresh the market.</div>
    </div>`;
    return;
  }
  el.innerHTML = commercialListings.map(p => commercialMarketCardHtml(p)).join('');
}

function toggleMarketHood(hood) {
  // undefined = open by default; toggling for the first time closes it
  marketHoodOpen[hood] = marketHoodOpen[hood] === false ? true : false;
  sfx.accordion();
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
  <div class="card" style="${p.foreclosure ? 'border:2px solid #C0392B' : ''}">
    ${p.foreclosure ? `<div style="display:inline-block;background:#C0392B;color:#fff;font-size:11px;font-weight:800;letter-spacing:0.5px;padding:3px 10px;border-radius:6px;margin-bottom:8px">🏷️ FORECLOSURE · sold as-is</div>` : ''}
    <div class="card-header">
      <div class="card-icon">${propModelImg(p)}</div>
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
  sfx.buyOpen();
  showConfirmModal(
    `Buy ${listing.bedrooms}bd ${listing.type}?`,
    `${listing.neighborhood} · ${fmt(listing.purchase_price)}`,
    async () => {
      const res = await api('/buy', 'POST', { listing_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      sfx.buy();
      closeModal();
      toast(`Purchased ${listing.type} in ${listing.neighborhood}!`, 'success');
      // Remove the bought listing locally — market only refills on day advance
      marketListings = marketListings.filter(p => p.id !== id);
      await refreshState();
      renderAll();
    }
  );
}

function commercialMarketCardHtml(p) {
  const ct         = COMMERCIAL_TYPES_DATA[p.type] || {};
  const canAfford  = p.purchase_price <= (state ? state.cash : 0);
  const maxRent    = p.units.reduce((sum, _) => sum + Math.max(...Object.values(BUSINESS_TENANT_DATA).map(b => b.monthly_rent)), 0);
  const minOverhead = ct.overhead || 0;
  const condPct_   = Math.min(100, Math.round((p.condition / 250) * 100));
  return `
  <div class="card">
    <div class="card-header">
      <div class="card-icon">${pxIcon(ct.icon || '🏢')}</div>
      <div style="flex:1">
        <div class="card-title">${p.address}</div>
        <div class="card-subtitle">${ct.name} · ${(p.sqft || 0).toLocaleString()} sqft · ${ct.unit_count} units</div>
      </div>
    </div>
    <div class="condition-wrap">
      <div class="condition-top">
        <span class="condition-lbl">Condition</span>
        <span class="condition-val" style="color:${tierColor(condTier(p.condition))};font-weight:900">${condTier(p.condition)} Tier</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${condPct_}%"></div></div>
    </div>
    <div class="money-row"><span class="mr-label">Asking Price</span><span class="mr-value">${fmt(p.purchase_price)}</span></div>
    <div class="money-row"><span class="mr-label">Monthly Overhead</span><span class="mr-value" style="color:var(--negative)">−${fmt(minOverhead)}/mo</span></div>
    <div class="money-row"><span class="mr-label">Max Monthly Income</span><span class="mr-value green">up to ${fmt(maxRent)}/mo (fully leased)</span></div>
    <div style="display:flex;justify-content:flex-end;margin-top:12px">
      <button class="btn btn-primary btn-sm" onclick="buyCommercial(${p.id})" ${!canAfford ? 'disabled style="opacity:0.4"' : ''}>
        Buy ${fmt(p.purchase_price)}
      </button>
    </div>
  </div>`;
}

async function buyCommercial(id) {
  const listing = commercialListings.find(p => p.id === id);
  if (!listing) return;
  if (listing.purchase_price > state.cash) { toast('Not enough cash!', 'error'); return; }
  const ct = COMMERCIAL_TYPES_DATA[listing.type] || {};
  showConfirmModal(
    `Buy ${ct.name}?`,
    `${listing.address} · ${fmt(listing.purchase_price)}`,
    async () => {
      const res = await api('/commercial/buy', 'POST', { listing_id: id });
      if (res.error) { toast(res.error, 'error'); return; }
      closeModal();
      toast(`Purchased ${ct.name} on ${listing.address}!`, 'success');
      commercialListings = commercialListings.filter(p => p.id !== id);
      await refreshState();
      renderAll();
    }
  );
}

async function refreshMarketListings() {
  const data = await api('/market/refresh', 'POST');
  marketListings     = data.listings || [];
  commercialListings = data.commercial_listings || [];
  renderMarket();
  renderCommercialMarket();
}

// ── Properties ────────────────────────────────────────────────────────────────
function renderProperties() {
  const el = document.getElementById('property-list');
  if (!el) return;

  const residential = (state.properties || []).filter(p => !p.commercial);

  if (residential.length === 0) {
    el.innerHTML = `<div class="empty-state">
      <div class="empty-icon">${pxIcon('🏗️', 48)}</div>
      <div class="empty-text">No rental properties yet</div>
      <div class="empty-sub">Head to the Market tab to buy your first property</div>
    </div>`;
    return;
  }

  // Group by neighborhood
  const byHood = {};
  residential.forEach(p => {
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

function toggleCommercialCard(pid) {
  const wasOpen = !!_commercialExpanded[pid];
  _commercialExpanded = {};
  _commercialExpanded[pid] = !wasOpen;
  renderCommercial();
}

// ── Commercial overhaul UI helpers ──────────────────────────────────────────
function ftColor(ft) { return ft >= 70 ? '#2E7D32' : ft >= 45 ? '#F9A825' : '#C62828'; }
function ftLabel(ft) { return ft >= 80 ? 'Bustling' : ft >= 60 ? 'Busy' : ft >= 40 ? 'Steady' : ft >= 20 ? 'Quiet' : 'Dead Zone'; }
function satEmoji(s) { return s >= 75 ? '😀' : s >= 55 ? '🙂' : s >= 35 ? '😐' : '😟'; }
function satColor(s) { return s >= 70 ? '#2E7D32' : s >= 45 ? '#F9A825' : '#C62828'; }

function tenantMixHtml(p) {
  const ft       = p.foot_traffic == null ? 50 : p.foot_traffic;
  const occUnits = p.units.filter(u => u.business_type);
  const catCounts = {}; let anchorCt = 0;
  occUnits.forEach(u => {
    const c = BUSINESS_TENANT_CAT[u.business_type] || 'retail';
    catCounts[c] = (catCounts[c] || 0) + 1;
    if (BUSINESS_ANCHORS.has(u.business_type)) anchorCt++;
  });
  const dupPen = Object.values(catCounts).reduce((s, n) => s + Math.max(0, n - 1), 0);
  const chips = Object.entries(catCounts).map(([c, n]) =>
    `<span style="font-size:10px;font-weight:700;background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:2px 8px">${CAT_ICON[c] || ''} ${CAT_LABEL[c] || c}${n > 1 ? ` ×${n}` : ''}</span>`
  ).join('');
  let hint = '';
  if (occUnits.length === 0)      hint = 'Empty building — no foot traffic. Sign an anchor tenant to get going.';
  else if (dupPen > 0)            hint = '⚠ Duplicate categories cannibalize each other — diversify the mix for more traffic.';
  else if (anchorCt === 0)        hint = 'No anchor tenant yet — a restaurant, café, gym, pharmacy, or clinic draws crowds.';
  else                           hint = `Healthy mix${anchorCt > 1 ? ` with ${anchorCt} anchors` : ' with an anchor'} — traffic lifts every tenant\'s sales rent.`;
  return `<div style="margin:4px 0 12px;padding:10px;border-radius:8px;background:rgba(0,0,0,0.03);border:1px solid var(--border)">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
      <span style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted)">Foot Traffic</span>
      <span style="font-size:12px;font-weight:900;color:${ftColor(ft)}">${ftLabel(ft)} · ${ft}/100</span>
    </div>
    <div class="condition-bar" style="margin-bottom:8px"><div class="condition-fill" style="width:${ft}%;background:${ftColor(ft)}"></div></div>
    <div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:6px">${chips || '<span style="font-size:10px;color:var(--text-muted);font-style:italic">No tenants yet</span>'}</div>
    <div style="font-size:10px;color:var(--text-muted);line-height:1.35">${hint}</div>
  </div>`;
}

function commercialPortfolioCardHtml(p) {
  const ct       = COMMERCIAL_TYPES_DATA[p.type] || {};
  const condPct_ = Math.min(100, Math.round((p.condition / 250) * 100));
  const totalRent  = p.units.reduce((s, u) => s + (u.monthly_rent || 0), 0);
  const pctMonthly = p.units.reduce((s, u) => s + (u.pct_rent_monthly || 0), 0);
  const occupied   = p.units.filter(u => u.business_type).length;
  const isOpen     = !!_commercialExpanded[p.id];
  const ft_        = p.foot_traffic == null ? 50 : p.foot_traffic;

  // Compact unit pills shown in collapsed view
  const unitPills = p.units.map(u => {
    const bt = u.business_type ? (BUSINESS_TENANT_DATA[u.business_type] || {}) : null;
    return bt
      ? `<span style="font-size:13px" title="${u.tenant_name}">${bt.icon}</span>`
      : `<span style="font-size:13px;opacity:0.35">⬜</span>`;
  }).join('');

  // Full unit rows (expanded only)
  const unitRows = p.units.map(u => {
    const bt = u.business_type ? (BUSINESS_TENANT_DATA[u.business_type] || {}) : null;
    if (!bt) {
      return `<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);gap:8px">
        <div style="display:flex;align-items:center;gap:6px;flex:1">
          <span style="font-size:16px">⬜</span>
          <span style="font-size:12px;color:var(--text-muted);font-style:italic">Vacant unit</span>
        </div>
        <button class="btn btn-sm btn-primary" style="font-size:10px;padding:3px 8px" onclick="findCommercialTenant(${p.id},${u.idx})">Find Tenant</button>
      </div>`;
    }
    const leaseLabel = u.lease_days_remaining <= 7
      ? `<span style="color:var(--warning);font-size:10px">⚠ ${u.lease_days_remaining}d left</span>`
      : `<span style="font-size:10px;color:var(--text-muted)">${u.lease_days_remaining}d left</span>`;
    const sat   = u.satisfaction == null ? 70 : u.satisfaction;
    const pct   = u.pct_rent_monthly || 0;
    const total = (u.monthly_rent || 0) + pct;
    return `<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);gap:8px">
      <div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0">
        <span style="font-size:16px">${bt.icon}</span>
        <div style="min-width:0">
          <div style="font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${u.tenant_name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${bt.name} · ${leaseLabel} · <span style="color:${satColor(sat)};font-weight:700" title="Tenant satisfaction">${satEmoji(sat)} ${Math.round(sat)}%</span></div>
        </div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:11px;font-weight:700;color:var(--positive);white-space:nowrap">${fmt(total)}/mo</div>
        ${pct > 0 ? `<div style="font-size:9px;color:var(--text-muted);white-space:nowrap">${fmt(u.monthly_rent)} + ${fmt(pct)} sales</div>` : ''}
      </div>
    </div>`;
  }).join('');

  const expandedHtml = `
    <div style="margin-top:10px;border-top:1px solid var(--border);padding-top:10px">
      ${tenantMixHtml(p)}
      <div class="money-row"><span class="mr-label">Base Rent</span><span class="mr-value green">${fmt(totalRent)}/mo</span></div>
      ${pctMonthly > 0 ? `<div class="money-row"><span class="mr-label">Sales Rent (foot traffic)</span><span class="mr-value green">+${fmt(pctMonthly)}/mo</span></div>` : ''}
      <div class="money-row"><span class="mr-label">Monthly Overhead</span><span class="mr-value" style="color:var(--negative)">−${fmt(ct.overhead || 0)}/mo</span></div>

      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);margin:10px 0 6px">Building Staff <span style="font-weight:600;text-transform:none;letter-spacing:0">· one of each per building</span></div>

      ${p.maintenance
        ? `<div class="money-row">
             <span class="mr-label">🔧 Maintenance Man</span>
             <span style="display:flex;align-items:center;gap:6px">
               <span class="mr-value" style="color:var(--negative)">−${fmt(ct.maintenance_monthly || 0)}/mo</span>
               <button class="btn btn-ghost" style="font-size:9px;padding:2px 7px;line-height:1.4" onclick="manageMaintenance(${p.id},'fire')">Fire</button>
             </span>
           </div>
           <div style="font-size:10px;color:var(--text-muted);line-height:1.4;margin:2px 0 10px;padding:7px 9px;background:rgba(46,125,50,0.06);border:1px solid var(--positive);border-radius:7px">
             🛠️ On duty — cuts daily wear by 60% and steadily repairs the building back up toward top condition. Keeps you out of the danger zone.
           </div>`
        : `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:2px">
             <span style="font-size:11px;color:var(--text-muted)">🔧 No Maintenance Man</span>
             <button class="btn btn-secondary btn-sm" style="font-size:10px;padding:3px 9px" onclick="manageMaintenance(${p.id},'hire')">Hire (${fmt(ct.maintenance_monthly || 0)}/mo)</button>
           </div>
           <div style="font-size:10px;color:var(--text-muted);line-height:1.4;margin:2px 0 10px;padding:7px 9px;background:rgba(0,0,0,0.03);border:1px solid var(--border);border-radius:7px">
             Hire him to keep this building's <strong>condition</strong> healthy — he cuts wear and steadily repairs it. Without him, condition only drops over time.
           </div>`
      }

      ${p.superintendent
        ? `<div class="money-row">
             <span class="mr-label">👷 Superintendent</span>
             <span style="display:flex;align-items:center;gap:6px">
               <span class="mr-value" style="color:var(--negative)">−${fmt(ct.superintendent_monthly || 0)}/mo</span>
               <button class="btn btn-ghost" style="font-size:9px;padding:2px 7px;line-height:1.4" onclick="manageSuperintendent(${p.id},'fire')">Fire</button>
             </span>
           </div>
           <div style="font-size:10px;color:var(--text-muted);line-height:1.4;margin:2px 0 10px;padding:7px 9px;background:rgba(46,125,50,0.06);border:1px solid var(--positive);border-radius:7px">
             📋 On duty — <strong>auto-handles this building's choice-card events</strong> (inspections, repairs, disputes, negotiations) so you're never prompted for this building.
           </div>`
        : `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:2px">
             <span style="font-size:11px;color:var(--text-muted)">👷 No Superintendent</span>
             <button class="btn btn-secondary btn-sm" style="font-size:10px;padding:3px 9px" onclick="manageSuperintendent(${p.id},'hire')">Hire (${fmt(ct.superintendent_monthly || 0)}/mo)</button>
           </div>
           <div style="font-size:10px;color:var(--text-muted);line-height:1.4;margin:2px 0 10px;padding:7px 9px;background:rgba(0,0,0,0.03);border:1px solid var(--border);border-radius:7px">
             Handles this building's <strong>choice-card events</strong> automatically. Without one, this building's events come to you to resolve by hand.
           </div>`
      }
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:6px">Units</div>
      ${unitRows}
      ${p.condition < 75 ? `
      <div style="margin-top:12px;padding:10px;background:rgba(183,28,28,0.08);border:1px solid #B71C1C;border-radius:8px;display:flex;align-items:center;justify-content:space-between;gap:8px">
        <div>
          <div style="font-size:12px;font-weight:800;color:#B71C1C">🚨 Building in D Condition</div>
          <div style="font-size:11px;color:var(--text-muted)">Tenants may leave without repairs</div>
        </div>
        <button class="btn btn-sm" style="background:#B71C1C;color:#fff;font-size:11px;white-space:nowrap" onclick="commercialEmergencyRepair(${p.id})">Emergency Repair ${fmt(ct.emergency_repair_cost || 15000)}</button>
      </div>` : ''}
      <div style="margin-top:12px">
        <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);margin-bottom:8px">Building Upgrades</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
          ${Object.entries(COMMERCIAL_UPGRADES_DATA).map(([key, upg]) => {
            const owned = (p.upgrades || {})[key];
            return `<div style="padding:8px;border-radius:6px;border:1px solid ${owned ? 'var(--positive)' : 'var(--border)'};background:${owned ? 'rgba(46,125,50,0.07)' : 'var(--card-bg)'}">
              <div style="font-size:16px">${upg.icon}</div>
              <div style="font-size:11px;font-weight:700;margin-top:2px">${upg.name}</div>
              <div style="font-size:10px;color:var(--text-muted);margin-top:2px;line-height:1.3">${upg.desc}</div>
              ${owned
                ? `<div style="font-size:10px;color:var(--positive);font-weight:800;margin-top:4px">✓ Installed</div>`
                : `<button class="btn btn-secondary btn-sm" style="font-size:10px;padding:2px 7px;margin-top:4px;width:100%" onclick="buyCommercialUpgrade(${p.id},'${key}')">Buy ${fmt(upg.cost)}</button>`
              }
            </div>`;
          }).join('')}
        </div>
      </div>
    </div>`;

  return `<div class="card">
    <div class="card-header" style="cursor:pointer" onclick="toggleCommercialCard(${p.id})">
      <div class="card-icon">${pxIcon(ct.icon || '🏢')}</div>
      <div style="flex:1;min-width:0">
        <div class="card-title">${p.address}</div>
        <div class="card-subtitle">${ct.name} · ${occupied}/${ct.unit_count || 0} occupied</div>
      </div>
      <span style="font-size:18px;color:var(--text-muted);flex-shrink:0;transition:transform 0.2s;${isOpen ? 'transform:rotate(180deg)' : ''}">▾</span>
    </div>
    <div class="condition-wrap" style="margin-bottom:${isOpen ? '0' : '4px'}">
      <div class="condition-top">
        <span class="condition-lbl">Building Condition ${p.maintenance ? '<span style="color:var(--positive);font-weight:800;font-size:10px">🔧 Maintained</span>' : '<span style="color:var(--text-muted);font-weight:700;font-size:10px">⚠ no upkeep</span>'}</span>
        <span class="condition-val" style="color:${tierColor(condTier(p.condition))};font-weight:900">${condTier(p.condition)} Tier</span>
      </div>
      <div class="condition-bar"><div class="condition-fill ${condClass(p.condition)}" style="width:${condPct_}%"></div></div>
    </div>
    ${!isOpen ? `<div style="display:flex;align-items:center;gap:8px;margin-top:8px;flex-wrap:wrap">
        <span style="font-size:10px;font-weight:800;color:${ftColor(ft_)};background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:2px 8px" title="Foot traffic">🚶 ${ft_}</span>
        <div style="display:flex;gap:4px;flex-wrap:wrap">${unitPills}</div>
      </div>` : ''}
    ${isOpen ? expandedHtml : ''}
  </div>`;
}

async function findCommercialTenant(pid, unitIdx) {
  const res = await api(`/commercial/${pid}/get_applicants`, 'POST', { unit_idx: unitIdx });
  if (res.error) { toast(res.error, 'error'); return; }
  const apps = res.applicants || [];
  const rows = apps.map(a => {
    const specialStyle = a.special
      ? 'border:2px solid #DAA520;border-radius:8px;background:rgba(255,215,0,0.06);padding:10px;margin-bottom:6px;'
      : 'border-bottom:1px solid var(--border);padding:10px 0;';
    const specialBadge = a.special
      ? ' <span style="font-size:10px;color:#DAA520;font-weight:900">⭐ SPECIAL</span>'
      : '';
    return `
    <div style="display:flex;align-items:center;justify-content:space-between;${specialStyle}gap:10px">
      <div style="display:flex;align-items:center;gap:10px;flex:1;min-width:0">
        <span style="font-size:24px">${a.icon}</span>
        <div style="min-width:0">
          <div style="font-size:13px;font-weight:800">${a.name}${specialBadge}</div>
          <div style="font-size:11px;color:var(--text-muted)">${a.display_name} · ${Math.round(a.lease_days / 28)} season lease</div>
          <div style="font-size:11px;color:var(--text-muted)">${a.desc}</div>
        </div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:13px;font-weight:800;color:var(--positive)">${fmt(a.monthly_rent)}/mo</div>
        <button class="btn btn-primary btn-sm" style="margin-top:4px;font-size:11px" onclick="acceptCommercialTenant(${pid},${unitIdx},'${a.biz_type}','${a.name.replace(/'/g,"\\'")}')"
        >Accept</button>
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🏢',18)} Business Applicants</div>
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">Select a tenant for this unit</div>
    ${rows}
    <button class="btn btn-ghost btn-sm" style="width:100%;margin-top:14px" onclick="closeModal()">Close</button>
  `);
}

async function acceptCommercialTenant(pid, unitIdx, bizType, bizName) {
  const res = await api(`/commercial/${pid}/accept_tenant`, 'POST', { unit_idx: unitIdx, biz_type: bizType, biz_name: bizName });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal();
  toast(`${bizName} moved in!`, 'success');
  await refreshState();
  renderCommercial();
}

async function manageSuperintendent(pid, action) {
  const res = await api(`/commercial/${pid}/superintendent`, 'POST', { action });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderCommercial();
  toast(action === 'hire' ? '👷 Superintendent hired!' : 'Superintendent dismissed.', action === 'hire' ? 'success' : 'info');
}

async function manageMaintenance(pid, action) {
  const res = await api(`/commercial/${pid}/maintenance`, 'POST', { action });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderCommercial();
  toast(action === 'hire' ? '🔧 Maintenance man hired!' : 'Maintenance man let go.', action === 'hire' ? 'success' : 'info');
}

async function buyCommercialUpgrade(pid, upgradeKey) {
  const upg = COMMERCIAL_UPGRADES_DATA[upgradeKey];
  if (!upg) return;
  const res = await api(`/commercial/${pid}/upgrade`, 'POST', { upgrade: upgradeKey });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderCommercial();
  toast(`${upg.icon} ${upg.name} installed!`, 'success');
}

async function commercialEmergencyRepair(pid) {
  const ct = COMMERCIAL_TYPES_DATA[gameState.properties?.find(p => p.id === pid)?.type] || {};
  const cost = ct.emergency_repair_cost || 15000;
  const res = await api(`/commercial/${pid}/emergency_repair`, 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderCommercial();
  toast(`🔧 Emergency repairs done! Building restored.`, 'success');
}

async function commercialEventRespond(pid, unitIdx, optIdx) {
  const ev  = _currentCommercialEvent;
  const opt = ev && ev.options ? ev.options[optIdx] : null;
  if (!opt) { drainCommercialEvents(); return; }
  const res = await api('/commercial/event_respond', 'POST',
    { prop_id: pid, unit_idx: unitIdx, effect: opt.effect, result: opt.result });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal();
  if (opt.result) toast(opt.result, opt.etype === 'warning' || opt.etype === 'negative' ? 'warning' : 'success');
  await refreshState();
  renderProperties();
  drainCommercialEvents();
}

function toggleHoodSection(hood) {
  _propHoodOpen[hood] = _propHoodOpen[hood] === false ? true : false;
  sfx.accordion();
  renderProperties();
}

function switchHoodTab(hood, tab) {
  sfx.tab();
  _propHoodTab[hood] = tab;
  renderProperties();
}

let _currentPropTab = 'portfolio';

function switchPropTab(tab) {
  sfx.tab();
  _currentPropTab = tab;
  ['portfolio', 'commercial', 'newbuilds'].forEach(t => {
    const el  = document.getElementById('prop-' + t);
    const btn = document.querySelector(`.fin-tab[data-prop-tab="${t}"]`);
    if (el)  el.style.display = t === tab ? '' : 'none';
    if (btn) btn.classList.toggle('active', t === tab);
  });
  if (tab === 'newbuilds')  renderNewBuilds();
  if (tab === 'portfolio')  renderProperties();
  if (tab === 'commercial') renderCommercial();
}

function renderCommercial() {
  const el = document.getElementById('commercial-list');
  if (!el || !state) return;
  const buildings = (state.properties || []).filter(p => p.commercial);
  if (buildings.length === 0) {
    const level = state.level || 0;
    if (level < COMMERCE_ROW_UNLOCK_LEVEL) {
      el.innerHTML = `<div class="empty-state" style="padding:32px 16px;text-align:center">
        <div style="font-size:48px;margin-bottom:12px">${pxIcon('🔒', 48)}</div>
        <div style="font-size:15px;font-weight:800;margin-bottom:6px">Unlocks at Level ${COMMERCE_ROW_UNLOCK_LEVEL}</div>
        <div style="font-size:12px;color:var(--text-muted)">Buy Strip Malls, Office Buildings, and Mixed-Use properties in Commerce Row.</div>
      </div>`;
    } else {
      el.innerHTML = `<div class="empty-state" style="padding:32px 16px;text-align:center">
        <div style="font-size:48px;margin-bottom:12px">${pxIcon('🏙️', 48)}</div>
        <div style="font-size:15px;font-weight:800;margin-bottom:6px">No commercial properties yet</div>
        <div style="font-size:12px;color:var(--text-muted)">Head to the Market tab to buy a Strip Mall, Office Building, or Mixed-Use Building.</div>
      </div>`;
    }
    return;
  }
  el.innerHTML = buildings.map(p => commercialPortfolioCardHtml(p)).join('');
}

function renderNewBuilds() {
  const el = document.getElementById('new-builds-list');
  if (!el || !state) return;

  const level      = state.level || 0;
  const hasPermit  = !!state.building_permit;
  const ownedCrews = state.owned_crews || [];
  const builds     = state.active_builds || [];

  if (level < NEW_BUILDS_UNLOCK_LEVEL) {
    el.innerHTML = `<div class="empty-state" style="padding:32px 16px;text-align:center">
      <div style="font-size:48px;margin-bottom:12px">${pxIcon('🔒', 48)}</div>
      <div style="font-size:15px;font-weight:800;margin-bottom:6px">Unlocks at Level ${NEW_BUILDS_UNLOCK_LEVEL}</div>
      <div style="font-size:12px;color:var(--text-muted)">Build brand-new homes from the ground up in Cedarvale Estates.</div>
    </div>`;
    return;
  }

  if (!hasPermit) {
    el.innerHTML = `<div style="padding:16px;text-align:center">
      <div style="font-size:40px;margin-bottom:10px">📋</div>
      <div style="font-size:14px;font-weight:800;margin-bottom:6px">Building Permit Required</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px">Purchase a building permit in Personal → New Builds to unlock construction.</div>
      <button class="btn btn-primary" onclick="navTo('personal')" style="font-size:13px">Go to Personal Tab</button>
    </div>`;
    return;
  }

  if (ownedCrews.length === 0) {
    el.innerHTML = `<div style="padding:16px;text-align:center">
      <div style="font-size:40px;margin-bottom:10px">🔨</div>
      <div style="font-size:14px;font-weight:800;margin-bottom:6px">No Crews Hired</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px">Hire at least one building crew in Personal → New Builds to start a project.</div>
      <button class="btn btn-primary" onclick="navTo('personal')" style="font-size:13px">Hire a Crew</button>
    </div>`;
    return;
  }

  // Build cards for active builds
  const buildCards = builds.length === 0
    ? `<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px">No active builds. Start a project below.</div>`
    : builds.map(b => {
        const size   = NEW_BUILD_SIZES_DATA[b.size];
        const crew   = BUILD_CREWS_DATA[b.crew];
        const pct    = Math.round(((b.total_days - b.days_remaining) / b.total_days) * 100);
        const daysLeft = b.days_remaining;
        const seasons = (daysLeft / 28).toFixed(1);
        const paused = b.paused;
        const premiums = (b.premium_upgrades || []).map(k => PREMIUM_UPGRADES_DATA[k]?.name).filter(Boolean);
        return `
        <div style="background:var(--card-bg);border:2px solid ${paused ? '#555' : 'var(--primary)'};border-radius:8px;padding:12px;margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <div style="font-size:28px;line-height:1">${pxIcon(size.icon, 28)}</div>
            <div style="flex:1">
              <div style="font-size:14px;font-weight:800">${size.name}</div>
              <div style="font-size:11px;color:var(--text-muted)">${crew.name} · ${paused ? '<span style="color:#FFA726">Paused</span>' : `${fmt(crew.daily_rate)}/day`}</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:11px;color:var(--text-muted)">${daysLeft}d left</div>
              <div style="font-size:10px;color:var(--text-muted)">(~${seasons} seasons)</div>
            </div>
          </div>
          <div style="background:var(--surface-2);border-radius:4px;height:8px;margin-bottom:8px;overflow:hidden">
            <div style="height:100%;width:${pct}%;background:${paused ? '#FFA726' : 'var(--primary)'};transition:width 0.3s"></div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
            <div style="font-size:10px;color:var(--text-muted)">${pct}% complete</div>
            <div style="font-size:10px;color:var(--text-muted)">Est. Finished Value:~${fmt(size.finished_value + (b.premium_upgrades||[]).reduce((s,k) => s+(PREMIUM_UPGRADES_DATA[k]?.value_bonus||0), 0))}</div>
          </div>
          ${premiums.length > 0 ? `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px">${premiums.map(n => `<span style="background:var(--surface-2);color:var(--text-muted);padding:2px 6px;font-size:9px;border-radius:3px">${n}</span>`).join('')}</div>` : ''}
          <div style="display:flex;gap:6px">
            <button onclick="toggleBuildPause(${b.id})" style="flex:1;padding:6px;background:${paused ? 'var(--primary)' : '#37474F'};border:none;color:white;border-radius:4px;font-size:11px;font-weight:700;cursor:pointer">${paused ? '▶ Resume' : '⏸ Pause'}</button>
            <button onclick="cancelBuild(${b.id},'${size.name}')" style="padding:6px 10px;background:none;border:1px solid var(--negative);color:var(--negative);border-radius:4px;font-size:11px;cursor:pointer">Cancel</button>
          </div>
        </div>`;
      }).join('');

  el.innerHTML = `
    <div style="padding:12px;max-width:480px;margin:0 auto">
      <div style="margin-bottom:12px">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:8px">Active Projects</div>
        ${buildCards}
      </div>
      <button onclick="showStartBuildModal()" style="width:100%;padding:12px;background:var(--primary);border:none;color:white;border-radius:6px;font-size:14px;font-weight:700;cursor:pointer">+ Start New Project</button>
    </div>`;
}

function showStartBuildModal() {
  const ownedCrews = state.owned_crews || [];
  const activeBuildCrews = (state.active_builds || []).filter(b => !b.paused).map(b => b.crew);

  const sizeOptions = Object.entries(NEW_BUILD_SIZES_DATA).map(([key, s]) => `
    <label style="display:flex;align-items:flex-start;gap:10px;padding:10px;border:2px solid var(--border);border-radius:6px;cursor:pointer;margin-bottom:6px;transition:border-color 0.15s" onclick="nbSelectSize('${key}',this)">
      <input type="radio" name="nb-size" value="${key}" style="margin-top:3px;flex-shrink:0">
      <div style="flex:1">
        <div style="font-size:13px;font-weight:800">${pxIcon(s.icon, 16)} ${s.name}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${s.desc}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:3px;font-weight:700">Build cost: ${fmt(s.build_cost)} · Est. Finished Value:${fmt(s.finished_value)}</div>
      </div>
    </label>`).join('');

  const crewOptions = ownedCrews.map(key => {
    const c = BUILD_CREWS_DATA[key];
    const busy = activeBuildCrews.includes(key);
    return `
    <label style="display:flex;align-items:flex-start;gap:10px;padding:10px;border:2px solid var(--border);border-radius:6px;cursor:${busy?'not-allowed':'pointer'};margin-bottom:6px;opacity:${busy?0.5:1}" ${busy ? '' : `onclick="nbSelectCrew('${key}',this)"`}>
      <input type="radio" name="nb-crew" value="${key}" ${busy ? 'disabled' : ''} style="margin-top:3px;flex-shrink:0">
      <div style="flex:1">
        <div style="font-size:13px;font-weight:800">${pxIcon(c.icon, 16)} ${c.name}${busy ? ' <span style="font-size:10px;color:#FFA726">(busy)</span>' : ''}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${fmt(c.daily_rate)}/day · ${Math.round((1 - c.speed_mult) * 100)}% faster</div>
      </div>
    </label>`;
  }).join('');

  const upgradeOptions = Object.entries(PREMIUM_UPGRADES_DATA).map(([key, u]) => `
    <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;margin-bottom:4px">
      <input type="checkbox" name="nb-upgrade" value="${key}" onchange="nbUpdateCostSummary()" style="flex-shrink:0">
      <div style="flex:1">
        <span style="font-size:12px;font-weight:700">${pxIcon(u.icon,14)} ${u.name}</span>
        <span style="font-size:11px;color:var(--text-muted);margin-left:6px">+${fmt(u.cost)} · +${fmt(u.value_bonus)} value</span>
      </div>
    </label>`).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">Start New Build</div>
    <div style="max-height:60vh;overflow-y:auto;padding-bottom:8px">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);margin-bottom:8px">Choose Size</div>
      ${sizeOptions}
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);margin:12px 0 8px">Assign Crew</div>
      ${crewOptions}
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);margin:12px 0 8px">Premium Upgrades <span style="font-weight:400">(optional — paid upfront)</span></div>
      ${upgradeOptions}
      <div id="nb-cost-summary" style="margin-top:12px;padding:10px;background:var(--surface-2);border-radius:6px;font-size:12px;color:var(--text-muted);text-align:center">Select a size and crew to see cost</div>
    </div>
    <button onclick="submitStartBuild()" style="width:100%;margin-top:12px;padding:12px;background:var(--primary);border:none;color:white;border-radius:6px;font-size:14px;font-weight:700;cursor:pointer">Start Build</button>
  `);
}

function nbSelectSize(key, el) {
  document.querySelectorAll('label[onclick^="nbSelectSize"]').forEach(l => l.style.borderColor = 'var(--border)');
  el.style.borderColor = 'var(--primary)';
  nbUpdateCostSummary();
}

function nbSelectCrew(key, el) {
  document.querySelectorAll('label[onclick^="nbSelectCrew"]').forEach(l => l.style.borderColor = 'var(--border)');
  el.style.borderColor = 'var(--primary)';
  nbUpdateCostSummary();
}

function nbUpdateCostSummary() {
  const sizeEl  = document.querySelector('input[name="nb-size"]:checked');
  const crewEl  = document.querySelector('input[name="nb-crew"]:checked');
  const summary = document.getElementById('nb-cost-summary');
  if (!summary) return;
  if (!sizeEl || !crewEl) { summary.textContent = 'Select a size and crew to see cost'; return; }
  const size  = NEW_BUILD_SIZES_DATA[sizeEl.value];
  const crew  = BUILD_CREWS_DATA[crewEl.value];
  const upgrades = Array.from(document.querySelectorAll('input[name="nb-upgrade"]:checked')).map(i => i.value);
  const upgCost  = upgrades.reduce((t, k) => t + (PREMIUM_UPGRADES_DATA[k]?.cost || 0), 0);
  const days     = Math.round(size.base_days * crew.speed_mult);
  const crewTotal = days * crew.daily_rate;
  const upfront  = size.build_cost + upgCost;
  const total    = upfront + crewTotal;
  const value    = size.finished_value + upgrades.reduce((t, k) => t + (PREMIUM_UPGRADES_DATA[k]?.value_bonus || 0), 0);
  const seasons     = (days / 28).toFixed(1);
  const years       = (days / 112).toFixed(1);
  const timeLabel   = days >= 112 ? `${years} years` : `${seasons} seasons`;
  summary.innerHTML = `
    <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span>Build time</span><span style="font-weight:700">${days} days (~${timeLabel})</span></div>
    <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span>Build cost</span><span style="font-weight:700">${fmt(size.build_cost)}</span></div>
    ${upgCost > 0 ? `<div style="display:flex;justify-content:space-between;margin-bottom:4px"><span>Upgrades</span><span style="font-weight:700">${fmt(upgCost)}</span></div>` : ''}
    <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span>Crew pay (${days} days)</span><span style="font-weight:700">${fmt(crewTotal)}</span></div>
    <div style="border-top:1px solid var(--border);padding-top:4px;margin-top:4px;display:flex;justify-content:space-between"><span style="font-weight:700">Total invested</span><span style="font-weight:800;color:var(--negative)">${fmt(total)}</span></div>
    <div style="display:flex;justify-content:space-between;margin-top:4px"><span style="font-weight:700">Est. Finished Value</span><span style="font-weight:800;color:var(--positive)">${fmt(value)}</span></div>
    <div style="display:flex;justify-content:space-between"><span>Profit</span><span style="font-weight:800;color:${value - total >= 0 ? 'var(--positive)' : 'var(--negative)'}">${fmt(value - total)}</span></div>`;
}

async function submitStartBuild() {
  const sizeEl  = document.querySelector('input[name="nb-size"]:checked');
  const crewEl  = document.querySelector('input[name="nb-crew"]:checked');
  if (!sizeEl) { toast('Select a build size', 'warning'); return; }
  if (!crewEl) { toast('Select a crew', 'warning'); return; }
  const upgrades = Array.from(document.querySelectorAll('input[name="nb-upgrade"]:checked')).map(i => i.value);
  const res = await api('/new_builds/start', 'POST', { size: sizeEl.value, crew: crewEl.value, premium_upgrades: upgrades });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.construct();
  closeModal();
  await refreshState();
  renderNewBuilds();
  toast(`Construction started! ${NEW_BUILD_SIZES_DATA[sizeEl.value].name} underway in Cedarvale Estates.`, 'success');
}

async function toggleBuildPause(buildId) {
  const res = await api('/new_builds/toggle_pause', 'POST', { build_id: buildId });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderNewBuilds();
  toast(res.paused ? 'Construction paused.' : 'Construction resumed.', 'info');
}

function cancelBuild(buildId, sizeName) {
  openModal(`
    <div style="text-align:center;padding:8px 0">
      <div style="font-size:32px;margin-bottom:8px">🚧</div>
      <div style="font-size:16px;font-weight:700;margin-bottom:6px">Cancel ${sizeName}?</div>
      <div style="font-size:13px;color:var(--text-muted);margin-bottom:6px">You'll receive a <strong>40% refund</strong> on build and upgrade costs.</div>
      <div style="font-size:12px;color:var(--negative);margin-bottom:16px">Crew pay already spent is not refunded.</div>
      <div style="display:flex;gap:8px;justify-content:center">
        <button onclick="closeModal()" style="padding:8px 18px;background:var(--card-bg);border:1px solid var(--border);color:var(--text-1);border-radius:4px;cursor:pointer;font-size:13px">Keep Building</button>
        <button onclick="cancelBuildConfirmed(${buildId})" style="padding:8px 18px;background:#c0392b;border:none;color:white;border-radius:4px;cursor:pointer;font-size:13px;font-weight:700">Cancel Build</button>
      </div>
    </div>`);
}

async function cancelBuildConfirmed(buildId) {
  closeModal();
  const res = await api('/new_builds/cancel', 'POST', { build_id: buildId });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderNewBuilds();
  toast(`Build cancelled. ${fmt(res.refund)} refunded.`, 'info');
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
      <div class="card-icon">${homeModelImg(home.key)}</div>
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
        <div style="line-height:1">${homeModelImg(current.key, 56)}</div>
        <div style="flex:1">
          <div style="font-size:16px;font-weight:800">${current.name}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${current.desc}</div>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:12px">
        <div style="flex:1;text-align:center;padding:8px;background:var(--surface);border-radius:8px">
          <div style="font-size:20px;font-weight:900;color:var(--positive)">⚡ ${state.max_energy || 4}</div>
          <div style="font-size:11px;color:var(--text-muted)">Max Energy</div>
        </div>
        <div style="flex:1;text-align:center;padding:8px;background:var(--surface);border-radius:8px">
          <div style="font-size:20px;font-weight:900;color:var(--primary)">+${state.recharge || 1}/day</div>
          <div style="font-size:11px;color:var(--text-muted)">Daily Recharge</div>
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
           const newItemCount = STORE_ITEM_DATA.filter(i => i.unlock_home === h.key).length;
           return `
           <div class="card" style="margin-bottom:10px;opacity:${isLocked ? '0.45' : (!canAfford ? '0.6' : '1')}">
             <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
               <div style="font-size:28px;line-height:1">${isLocked ? pxIcon('🔒') : homeModelImg(h.key, 44)}</div>
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
                 <div style="font-size:15px;font-weight:800;color:var(--positive)">${newItemCount > 0 ? `+${newItemCount}` : '—'} items</div>
                 <div style="font-size:10px;color:var(--text-muted)">New Furniture</div>
               </div>
               <div style="flex:1;text-align:center;padding:6px;background:var(--surface-2);border-radius:6px">
                 <div style="font-size:15px;font-weight:800;color:var(--text-muted)">${h.cost === 0 ? 'Free' : fmt(h.cost)}</div>
                 <div style="font-size:10px;color:var(--text-muted)">Purchase Price</div>
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
  sfx.moveIn();
  closeModal();
  await refreshState();
  renderAll();
  renderPersonal();
  const home = PLAYER_HOME_DATA.find(h => h.key === homeKey);
  toast(`🏠 Moved into ${home ? home.name : 'new home'}! New items now available in your home store.`);
}

// ── Personal Tab ──────────────────────────────────────────────────────────────

const STORE_ITEM_DATA = [
  // room: living | bedroom | kitchen | office | garage | outdoor
  // unlock_home: null = all homes; otherwise minimum home key required
  { key: 'house_plant',      name: 'House Plant',                 icon: '🪴', room: 'living',   unlock_home: null,            cost:   89, unlock_level: 2, bonus: '15% chance to block 1 morale loss/day',  desc: 'Studies show it helps.' },
  { key: 'couch',            name: 'Couch',                       icon: '🛋️',room: 'living',   unlock_home: 'small_apt',     cost:  600, unlock_level: 1, bonus: '+2 ⚡ max energy',                      desc: 'Somewhere to actually sit.' },
  { key: 'flat_screen_tv',   name: 'Flat Screen TV',              icon: '📺', room: 'living',   unlock_home: 'small_apt',     cost: 1200, unlock_level: 1, bonus: '+2 ⚡ max energy',                      desc: 'Something to unwind to.' },
  { key: 'home_theater',     name: 'Home Theater',                icon: '🎬', room: 'living',   unlock_home: 'luxury_villa',  cost: 8000, unlock_level: 9, bonus: '+5 ⚡ max energy',                      desc: 'The screen. The surround sound. The popcorn machine.' },
  { key: 'new_bed',          name: 'New Bed',                     icon: '🛏️',room: 'bedroom',  unlock_home: null,            cost: 4999, unlock_level: 3, bonus: '+1 ⚡/day recharge',                    desc: 'Memory foam. You wake up ready.' },
  { key: 'blackout_curtains',name: 'Blackout Curtains',           icon: '🪟', room: 'bedroom',  unlock_home: null,            cost:  149, unlock_level: 2, bonus: '+1 ⚡/day recharge',                    desc: 'Sleep deeper. Wake up less angry.' },
  { key: 'hot_tub',          name: 'Hot Tub',                     icon: '🛁', room: 'bedroom',  unlock_home: 'suburban_home', cost: 8000, unlock_level: 7, bonus: '+3 ⚡/day recharge',                    desc: 'Hydrotherapy. Tax deductible? Maybe.' },
  { key: 'coffee_maker',     name: 'Coffee Maker',                icon: '☕', room: 'kitchen',  unlock_home: null,            cost:  499, unlock_level: 1, bonus: '+2 ⚡ max energy',                      desc: 'A decent drip machine. Never run on empty again.' },
  { key: 'mini_fridge',      name: 'Mini Fridge',                 icon: '🧊', room: 'kitchen',  unlock_home: null,            cost:  349, unlock_level: 3, bonus: '+2 ⚡ max energy',                      desc: 'Snacks within arm\'s reach.' },
  { key: 'espresso_machine', name: 'Espresso Machine',            icon: '☕', room: 'kitchen',  unlock_home: 'condo',         cost:  899, unlock_level: 3, bonus: '+2 ⚡ max energy, +1 recharge',         desc: 'Real caffeine. Finally.' },
  { key: 'wine_rack',        name: 'Wine Rack',                   icon: '🍷', room: 'kitchen',  unlock_home: 'condo',         cost: 1500, unlock_level: 5, bonus: '+$100/day passive income',               desc: 'The landlord aesthetic.' },
  { key: 'desk_fan',         name: 'Desk Fan',                    icon: '🌀', room: 'office',   unlock_home: null,            cost:  199, unlock_level: 1, bonus: '+2 ⚡ max energy',                      desc: 'Not air conditioning. Close enough.' },
  { key: 'whiteboard',       name: 'Whiteboard',                  icon: '📋', room: 'office',   unlock_home: 'small_apt',     cost:  249, unlock_level: 4, bonus: '6% off all contractor renovation costs', desc: 'You mapped out the whole job.' },
  { key: 'filing_cabinet',   name: 'Filing Cabinet',              icon: '🗂️',room: 'office',   unlock_home: 'small_apt',     cost:  449, unlock_level: 5, bonus: '15% lower repair event chance',          desc: 'Everything is documented.' },
  { key: 'headphones',       name: 'Noise-Cancelling Headphones', icon: '🎧', room: 'office',   unlock_home: 'small_apt',     cost:  699, unlock_level: 6, bonus: 'Reduces morale events by 1 point',       desc: 'You stop engaging.' },
  { key: 'negotiation_book', name: 'Negotiation Book',            icon: '📖', room: 'office',   unlock_home: 'small_apt',     cost:  999, unlock_level: 7, bonus: '+4% on property sale prices',            desc: 'You read it twice. Vendors can tell.' },
  { key: 'gaming_setup',     name: 'Gaming Setup',                icon: '🎮', room: 'office',   unlock_home: 'small_home',    cost: 2500, unlock_level: 5, bonus: '+3 ⚡ max energy',                      desc: 'For decompressing. Professionally.' },
  { key: 'workbench_tools',  name: 'Workbench & Tools',           icon: '🔧', room: 'garage',   unlock_home: 'small_home',    cost:  800, unlock_level: 5, bonus: '8% off contractor labor costs',          desc: 'You\'ve got the tools. Bob is a little threatened.' },
  { key: 'home_gym',         name: 'Home Gym',                    icon: '🏋️',room: 'garage',   unlock_home: 'suburban_home', cost: 5000, unlock_level: 7, bonus: '+4 ⚡ max energy',                      desc: 'No more excuses. No gym commute.' },
  { key: 'bbq_grill',        name: 'BBQ Grill',                   icon: '🍖', room: 'outdoor',  unlock_home: 'small_home',    cost:  600, unlock_level: 5, bonus: 'Good vibes only',                        desc: 'Grilling on your own property hits different.' },
  { key: 'patio_set',        name: 'Patio Furniture',             icon: '🪑', room: 'outdoor',  unlock_home: 'small_home',    cost: 1200, unlock_level: 5, bonus: 'Cosmetic upgrade',                       desc: 'Morning coffee outside.' },
  { key: 'swimming_pool',    name: 'Swimming Pool',               icon: '🏊', room: 'outdoor',  unlock_home: 'luxury_villa',  cost:25000, unlock_level: 9, bonus: '+5 ⚡/day recharge',                    desc: 'Proving a point at this stage.' },
  // ── More living room ──────────────────────────────────────────────────────
  { key: 'bookshelf',        name: 'Bookshelf',                   icon: '📚', room: 'living',   unlock_home: 'condo',         cost:  350, unlock_level: 1, bonus: '+5% property sale price',                desc: 'Tax strategy, biographies, one novel you never finished.' },
  { key: 'aquarium',         name: 'Aquarium',                    icon: '🐠', room: 'living',   unlock_home: 'small_apt',     cost:  650, unlock_level: 2, bonus: '20% chance to block 1 morale loss/day',  desc: 'Fish don\'t care about your problems.' },
  { key: 'fireplace',        name: 'Fireplace',                   icon: '🪵', room: 'living',   unlock_home: 'small_home',    cost: 2000, unlock_level: 5, bonus: '+2 ⚡/day recharge',                    desc: 'Mood. Warmth. Crackling sounds.' },
  { key: 'pool_table',       name: 'Pool Table',                  icon: '🎱', room: 'living',   unlock_home: 'suburban_home', cost: 3500, unlock_level: 7, bonus: '+4 ⚡ max energy',                      desc: 'You hustle your contractors. They respect it.' },
  { key: 'grand_piano',      name: 'Grand Piano',                 icon: '🎹', room: 'living',   unlock_home: 'mansion',       cost:12000, unlock_level:11, bonus: '+4 ⚡ max energy',                      desc: 'You don\'t play. Gerald does.' },
  // ── More bedroom ─────────────────────────────────────────────────────────
  { key: 'meditation_corner',name: 'Meditation Corner',           icon: '🧘', room: 'bedroom',  unlock_home: 'condo',         cost:  900, unlock_level: 3, bonus: '+2 ⚡/day recharge',                    desc: 'Five minutes of silence. Life-changing.' },
  { key: 'sauna',            name: 'Sauna',                       icon: '🧖', room: 'bedroom',  unlock_home: 'luxury_villa',  cost: 6000, unlock_level: 9, bonus: '+5 ⚡/day recharge',                    desc: 'You sweat out bad decisions daily.' },
  // ── More kitchen ─────────────────────────────────────────────────────────
  { key: 'instant_pot',      name: 'Instant Pot',                 icon: '🥘', room: 'kitchen',  unlock_home: null,            cost:  150, unlock_level: 1, bonus: '+1 ⚡ max energy',                      desc: 'Set it, forget it, eat well.' },
  { key: 'kitchen_island',   name: 'Kitchen Island',              icon: '🍳', room: 'kitchen',  unlock_home: 'small_home',    cost: 2200, unlock_level: 5, bonus: '+3 ⚡ max energy',                      desc: 'More counter space. More life.' },
  { key: 'smart_fridge',     name: 'Smart Fridge',                icon: '🗄️',room: 'kitchen',  unlock_home: 'suburban_home', cost: 1800, unlock_level: 7, bonus: 'Cosmetic upgrade',                       desc: 'It texts you when you\'re low on eggs.' },
  // ── More office ──────────────────────────────────────────────────────────
  { key: 'ergonomic_chair',  name: 'Ergonomic Chair',             icon: '💺', room: 'office',   unlock_home: 'small_apt',     cost:  600, unlock_level: 4, bonus: '+2 ⚡/day recharge',                    desc: 'Your back stops screaming.' },
  { key: 'second_monitor',   name: 'Second Monitor',              icon: '🖥️',room: 'office',   unlock_home: 'condo',         cost:  400, unlock_level: 5, bonus: '+2 ⚡ max energy',                      desc: 'Left screen: spreadsheets. Right screen: also spreadsheets.' },
  { key: 'printer',          name: 'Laser Printer',               icon: '🖨️',room: 'office',   unlock_home: 'condo',         cost:  250, unlock_level: 3, bonus: '5% off all property purchase prices',   desc: 'Print the listing yourself. Save on fees.' },
  // ── More garage ──────────────────────────────────────────────────────────
  { key: 'motorcycle',       name: 'Motorcycle',                  icon: '🏍️',room: 'garage',   unlock_home: 'suburban_home', cost: 8000, unlock_level: 7, bonus: '+3 ⚡/day recharge',                    desc: 'Wind in your face on the way to collect rent.' },
  { key: 'sports_car',       name: 'Sports Car',                  icon: '🚗', room: 'garage',   unlock_home: 'suburban_home', cost:45000, unlock_level: 9, bonus: '+$200/day passive income',               desc: 'Landlord tax write-off, obviously.' },
  // ── More outdoor ─────────────────────────────────────────────────────────
  { key: 'garden',           name: 'Garden',                      icon: '🌻', room: 'outdoor',  unlock_home: 'small_home',    cost:  500, unlock_level: 3, bonus: '20% chance to block 1 morale loss/day',  desc: 'Something living that actually needs you.' },
  { key: 'fire_pit',         name: 'Fire Pit',                    icon: '🔥', room: 'outdoor',  unlock_home: 'small_home',    cost:  700, unlock_level: 5, bonus: '+2 ⚡/day recharge',                    desc: 'Evening decompression. You\'ve earned it.' },
  { key: 'basketball_hoop',  name: 'Basketball Hoop',             icon: '🏀', room: 'outdoor',  unlock_home: 'small_home',    cost:  400, unlock_level: 4, bonus: 'Cosmetic upgrade',                       desc: 'Shoot your frustration into a net.' },
  // ── High-tier items ───────────────────────────────────────────────────────
  { key: 'smart_home_system',name: 'Smart Home System',           icon: '🏠', room: 'living',   unlock_home: 'luxury_villa',  cost:12000, unlock_level: 9, bonus: '+5 ⚡ max energy',                      desc: 'Whole-home automation that optimizes your routines.' },
  { key: 'home_bar',         name: 'Home Bar',                    icon: '🍸', room: 'living',   unlock_home: 'mansion',       cost: 8000, unlock_level:12, bonus: '+4 ⚡ max energy',                      desc: 'Top-shelf everything. No excuses needed.' },
  { key: 'art_gallery',      name: 'Art Gallery',                 icon: '🖼️',room: 'living',   unlock_home: 'mansion',       cost:15000, unlock_level:12, bonus: '+4 ⚡ max energy',                      desc: 'Three rooms of originals. One is a forgery.' },
  { key: 'professional_gym', name: 'Professional Gym',            icon: '💪', room: 'garage',   unlock_home: 'mansion',       cost:20000, unlock_level:12, bonus: '+4 ⚡ max energy',                      desc: 'Olympic weights. No waiting for machines.' },
  { key: 'spa_suite',        name: 'Spa Suite',                   icon: '💆', room: 'bedroom',  unlock_home: 'mansion',       cost:25000, unlock_level:13, bonus: '+6 ⚡/day recharge',                    desc: 'Hot stone massages at 6am on a Tuesday.' },
  { key: 'luxury_sleep_system',name: 'Luxury Sleep System',       icon: '🛌', room: 'bedroom',  unlock_home: 'mansion',       cost:10000, unlock_level:12, bonus: '+4 ⚡/day recharge',                    desc: 'Temperature-regulated, zero-gravity mattress.' },
  { key: 'indoor_pool',      name: 'Indoor Pool',                 icon: '🌊', room: 'outdoor',  unlock_home: 'mansion',       cost:40000, unlock_level:13, bonus: '+6 ⚡/day recharge',                    desc: 'Climate-controlled. Gerald maintains it.' },
  { key: 'grand_fireplace',  name: 'Grand Fireplace',             icon: '🕯️',room: 'living',   unlock_home: 'mansion',       cost: 5000, unlock_level:12, bonus: '+3 ⚡/day recharge',                    desc: 'Floor-to-ceiling stone. You read by firelight.' },
  { key: 'music_studio',     name: 'Music Studio',                icon: '🎸', room: 'office',   unlock_home: 'mansion',       cost:18000, unlock_level:13, bonus: '+3 ⚡/day recharge',                    desc: 'Soundproofed. Pro-grade gear. You play once a month.' },
];

// ── Home tier order (for unlock_home checks) ──────────────────────────────
const HOME_TIER_ORDER = ['grandmas_basement','small_apt','condo','small_home','suburban_home','luxury_villa','mansion'];

function homeTierUnlocked(unlock_home) {
  if (!unlock_home) return true;
  const cur = HOME_TIER_ORDER.indexOf(state.player_home || 'grandmas_basement');
  return cur >= HOME_TIER_ORDER.indexOf(unlock_home);
}

// ── Sprite pixel-art data (top-down view, 16x16) ──────────────────────────
const _ROOM_LABELS = { living:'Living Room', bedroom:'Bedroom', kitchen:'Kitchen', office:'Home Office', garage:'Garage', outdoor:'Outdoor' };
const _ROOM_ORDER  = ['living','bedroom','kitchen','office','garage','outdoor'];

// ── Floor plan system ─────────────────────────────────────────────────────
// Top-down furniture sprites, drawn centered at local (0,0). w/h = footprint
// used for placement. One shared scale across all homes (consistent sizing).
const FP_FLOOR = { living:'#B89469', kitchen:'#9FB3B8', bedroom:'#B59A78', office:'#9E8E72', garage:'#8E969E', outdoor:'#7FB05F', bath:'#AEC4CC' };

const FP_SPRITES = {
  // ── Living ──
  house_plant:   { w:28, h:30, art:`<rect x="-8" y="2" width="16" height="13" rx="3" fill="#C66B3D" stroke="#8A4527" stroke-width="1.5"/><circle cx="-5" cy="-5" r="8" fill="#4CAF50"/><circle cx="5" cy="-8" r="8" fill="#66BB6A"/><circle cx="6" cy="0" r="6" fill="#4CAF50"/>` },
  couch:         { w:46, h:18, art:`<rect x="-21" y="-8" width="42" height="8" rx="4" fill="#5FC4BA" stroke="#2E8B83" stroke-width="1.5"/><rect x="-21" y="-5" width="42" height="13" rx="4" fill="#4DB6AC" stroke="#2E8B83" stroke-width="1.5"/><rect x="-24" y="-4" width="6" height="12" rx="2" fill="#3FA89E"/><rect x="18" y="-4" width="6" height="12" rx="2" fill="#3FA89E"/>` },
  flat_screen_tv:{ w:40, h:14, art:`<rect x="-20" y="-7" width="40" height="6" rx="2" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><rect x="-12" y="-1" width="24" height="5" rx="2" fill="#A9744F"/>` },
  home_theater:  { w:46, h:26, art:`<rect x="-22" y="-12" width="44" height="6" rx="2" fill="#2B2B33"/><rect x="-18" y="0" width="10" height="10" rx="3" fill="#5C6BC0"/><rect x="-4" y="0" width="10" height="10" rx="3" fill="#5C6BC0"/><rect x="10" y="0" width="10" height="10" rx="3" fill="#5C6BC0"/>` },
  bookshelf:     { w:34, h:20, art:`<rect x="-17" y="-10" width="34" height="20" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.5"/><rect x="-13" y="-7" width="4" height="14" fill="#E0533F"/><rect x="-8" y="-7" width="4" height="14" fill="#4D8FE0"/><rect x="-3" y="-7" width="4" height="14" fill="#5FB85F"/><rect x="2" y="-7" width="4" height="14" fill="#F2C744"/><rect x="7" y="-7" width="4" height="14" fill="#E0533F"/>` },
  aquarium:      { w:36, h:22, art:`<rect x="-18" y="-11" width="36" height="22" rx="4" fill="#5AB6E0" stroke="#2E7FA8" stroke-width="1.5"/><rect x="-15" y="-8" width="30" height="16" rx="3" fill="#8AD4F0"/><path d="M-8 0 l7 -4 l0 8 z" fill="#F2A65A"/><path d="M5 3 l6 -3 l0 6 z" fill="#E0533F"/>` },
  fireplace:     { w:34, h:20, art:`<rect x="-17" y="-4" width="34" height="14" rx="3" fill="#8A8A92" stroke="#5A5A62" stroke-width="1.5"/><rect x="-17" y="-10" width="34" height="8" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.5"/><path d="M-7 9 q-3 -10 3 -11 q-1 7 4 8 q4 -3 2 -8 q5 5 0 11 z" fill="#FF9A3D"/>` },
  pool_table:    { w:42, h:26, art:`<rect x="-21" y="-13" width="42" height="26" rx="4" fill="#2E8B57" stroke="#1E5E3A" stroke-width="2"/><rect x="-17" y="-9" width="34" height="18" rx="2" fill="#3CA86A"/><circle cx="-17" cy="-11" r="2.5" fill="#143A24"/><circle cx="17" cy="-11" r="2.5" fill="#143A24"/><circle cx="-17" cy="11" r="2.5" fill="#143A24"/><circle cx="17" cy="11" r="2.5" fill="#143A24"/><circle cx="-4" cy="0" r="2.5" fill="#fff"/><circle cx="4" cy="-2" r="2.5" fill="#F2C744"/>` },
  grand_piano:   { w:38, h:30, art:`<path d="M-16 -14 h12 q18 0 18 15 q0 11 -14 11 h-16 z" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><rect x="-16" y="-14" width="8" height="26" rx="1" fill="#F4F0E6"/><line x1="-14" y1="-14" x2="-14" y2="12" stroke="#111"/><line x1="-11" y1="-14" x2="-11" y2="12" stroke="#111"/>` },
  smart_home_system:{ w:24, h:24, art:`<rect x="-11" y="-11" width="22" height="22" rx="6" fill="#ECEFF1" stroke="#90A4AE" stroke-width="1.5"/><circle cx="0" cy="0" r="7" fill="#CFE8F5" stroke="#7FB5D8" stroke-width="1.5"/><circle cx="0" cy="0" r="3" fill="#4D8FE0"/>` },
  home_bar:      { w:40, h:22, art:`<rect x="-20" y="-6" width="40" height="14" rx="3" fill="#7A4F2F" stroke="#4A2F1A" stroke-width="1.5"/><rect x="-20" y="-9" width="40" height="5" rx="2" fill="#9A6A3F"/><circle cx="-12" cy="11" r="4" fill="#C98A4E"/><circle cx="12" cy="11" r="4" fill="#C98A4E"/><rect x="10" y="-7" width="3" height="6" fill="#5FB85F"/>` },
  art_gallery:   { w:40, h:16, art:`<rect x="-20" y="-7" width="40" height="6" rx="1" fill="#8A6A4A"/><rect x="-18" y="-1" width="11" height="13" rx="1" fill="#F2C744" stroke="#7A4F2F" stroke-width="1.5"/><rect x="-5" y="-1" width="11" height="13" rx="1" fill="#5FB85F" stroke="#7A4F2F" stroke-width="1.5"/><rect x="8" y="-1" width="11" height="13" rx="1" fill="#E08AB0" stroke="#7A4F2F" stroke-width="1.5"/>` },
  grand_fireplace:{ w:40, h:22, art:`<rect x="-20" y="-3" width="40" height="14" rx="3" fill="#7A6A5A" stroke="#4A3F33" stroke-width="1.5"/><rect x="-20" y="-10" width="40" height="9" rx="2" fill="#9A8A7A" stroke="#4A3F33" stroke-width="1.5"/><path d="M-8 10 q-4 -12 3 -13 q-2 8 5 9 q5 -3 3 -9 q6 6 0 13 z" fill="#FF9A3D"/>` },
  // ── Kitchen ──
  coffee_maker:  { w:18, h:22, art:`<rect x="-9" y="-10" width="18" height="22" rx="3" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><rect x="-6" y="-7" width="12" height="6" rx="1" fill="#5A5A66"/><circle cx="0" cy="6" r="4" fill="#6B3F2A"/>` },
  mini_fridge:   { w:22, h:26, art:`<rect x="-11" y="-13" width="22" height="26" rx="4" fill="#ECEFF1" stroke="#90A4AE" stroke-width="1.5"/><line x1="-11" y1="0" x2="11" y2="0" stroke="#90A4AE"/><rect x="5" y="-9" width="2.5" height="7" rx="1" fill="#B0BEC5"/>` },
  espresso_machine:{ w:26, h:22, art:`<rect x="-13" y="-10" width="26" height="20" rx="3" fill="#D7DBE0" stroke="#9AA3AB" stroke-width="1.5"/><rect x="-10" y="-7" width="9" height="14" rx="2" fill="#4A4A52"/><circle cx="-6" cy="9" r="2.5" fill="#F2C744"/>` },
  wine_rack:     { w:28, h:26, art:`<rect x="-14" y="-13" width="28" height="26" rx="3" fill="#9A6A3F" stroke="#5A3A1F" stroke-width="1.5"/><line x1="-14" y1="0" x2="14" y2="0" stroke="#5A3A1F"/><line x1="0" y1="-13" x2="0" y2="13" stroke="#5A3A1F"/><circle cx="-7" cy="-6" r="2.5" fill="#7B2D3A"/><circle cx="7" cy="-6" r="2.5" fill="#3A6B3A"/><circle cx="-7" cy="6" r="2.5" fill="#7B2D3A"/><circle cx="7" cy="6" r="2.5" fill="#C9A227"/>` },
  instant_pot:   { w:24, h:24, art:`<circle cx="0" cy="2" r="11" fill="#C0392B" stroke="#7E2218" stroke-width="1.5"/><circle cx="0" cy="2" r="7" fill="#D85A4A"/><rect x="-12" y="-10" width="24" height="6" rx="3" fill="#B0BEC5" stroke="#7D868E" stroke-width="1"/>` },
  kitchen_island:{ w:34, h:20, art:`<rect x="-17" y="-10" width="34" height="20" rx="3" fill="#CFD4DA" stroke="#9AA3AB" stroke-width="1.5"/><rect x="-17" y="-12" width="34" height="6" rx="2" fill="#C98A4E"/><rect x="-4" y="-6" width="9" height="6" rx="1" fill="#8A8A92"/>` },
  smart_fridge:  { w:24, h:28, art:`<rect x="-12" y="-14" width="24" height="28" rx="4" fill="#ECEFF1" stroke="#90A4AE" stroke-width="1.5"/><rect x="-7" y="-9" width="14" height="11" rx="2" fill="#2B6CB0"/><line x1="-12" y1="2" x2="12" y2="2" stroke="#90A4AE"/>` },
  // ── Bedroom ──
  new_bed:       { w:34, h:36, art:`<rect x="-17" y="-18" width="34" height="36" rx="5" fill="#FBF3E6" stroke="#CBB89A" stroke-width="1.5"/><rect x="-16" y="-2" width="32" height="18" rx="4" fill="#7E9CE0"/><rect x="-13" y="-14" width="11" height="9" rx="2" fill="#fff"/><rect x="2" y="-14" width="11" height="9" rx="2" fill="#fff"/>` },
  blackout_curtains:{ w:26, h:16, art:`<rect x="-13" y="-8" width="26" height="14" rx="2" fill="#CFE8F5" stroke="#7FB5D8" stroke-width="1.5"/><rect x="-13" y="-8" width="6" height="14" rx="2" fill="#2B6CB0"/><rect x="7" y="-8" width="6" height="14" rx="2" fill="#2B6CB0"/>` },
  hot_tub:       { w:30, h:28, art:`<circle cx="0" cy="0" r="14" fill="#3FA0A8" stroke="#256066" stroke-width="2"/><circle cx="0" cy="0" r="9" fill="#6FD0D6"/><circle cx="-4" cy="-2" r="2" fill="#fff"/><circle cx="4" cy="2" r="2" fill="#fff"/>` },
  meditation_corner:{ w:24, h:16, art:`<rect x="-12" y="-6" width="24" height="12" rx="5" fill="#F4EAD8" stroke="#CBB89A" stroke-width="1.5"/><circle cx="9" cy="-4" r="2.5" fill="#A9C8C0"/>` },
  sauna:         { w:30, h:26, art:`<rect x="-15" y="-13" width="30" height="26" rx="3" fill="#B5763A" stroke="#7A4F2F" stroke-width="1.5"/><line x1="-15" y1="-4" x2="15" y2="-4" stroke="#7A4F2F"/><line x1="-15" y1="4" x2="15" y2="4" stroke="#7A4F2F"/><circle cx="0" cy="0" r="3" fill="#E0533F"/>` },
  spa_suite:     { w:34, h:20, art:`<rect x="-17" y="-9" width="34" height="18" rx="5" fill="#F4EAD8" stroke="#CBB89A" stroke-width="1.5"/><rect x="-17" y="-9" width="9" height="18" rx="5" fill="#E8DCC4"/><circle cx="11" cy="-3" r="2.5" fill="#A9C8C0"/><circle cx="11" cy="4" r="2.5" fill="#A9C8C0"/>` },
  luxury_sleep_system:{ w:36, h:34, art:`<rect x="-18" y="-17" width="36" height="34" rx="6" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><rect x="-16" y="-2" width="32" height="17" rx="5" fill="#5C6BC0"/><rect x="-16" y="-13" width="32" height="5" rx="2" fill="#7FE0FF"/><rect x="-13" y="-11" width="12" height="8" rx="2" fill="#fff"/><rect x="2" y="-11" width="12" height="8" rx="2" fill="#fff"/>` },
  // ── Office ──
  desk_fan:      { w:20, h:20, art:`<circle cx="0" cy="0" r="9" fill="#5AB6E0" stroke="#2E7FA8" stroke-width="1.5"/><line x1="0" y1="0" x2="-6" y2="-4" stroke="#fff" stroke-width="2"/><line x1="0" y1="0" x2="6" y2="-4" stroke="#fff" stroke-width="2"/><line x1="0" y1="0" x2="0" y2="6" stroke="#fff" stroke-width="2"/><circle cx="0" cy="0" r="2.5" fill="#2B2B33"/>` },
  whiteboard:    { w:34, h:18, art:`<rect x="-17" y="-9" width="34" height="14" rx="2" fill="#F4F0E6" stroke="#9AA3AB" stroke-width="1.5"/><line x1="-12" y1="-4" x2="8" y2="-4" stroke="#E0533F" stroke-width="1.5"/><line x1="-12" y1="0" x2="11" y2="0" stroke="#4D8FE0" stroke-width="1.5"/><line x1="-12" y1="4" x2="2" y2="4" stroke="#5FB85F" stroke-width="1.5"/>` },
  filing_cabinet:{ w:22, h:24, art:`<rect x="-11" y="-12" width="22" height="24" rx="2" fill="#8A8A92" stroke="#5A5A62" stroke-width="1.5"/><rect x="-8" y="-9" width="16" height="6" rx="1" fill="#B8BEC4"/><rect x="-8" y="-1" width="16" height="6" rx="1" fill="#B8BEC4"/><rect x="-8" y="7" width="16" height="4" rx="1" fill="#B8BEC4"/>` },
  headphones:    { w:26, h:24, art:`<path d="M-11 -8 a11 11 0 0 1 22 0" fill="none" stroke="#2B2B33" stroke-width="2.5"/><rect x="-15" y="-6" width="8" height="14" rx="3" fill="#3A3A42"/><rect x="7" y="-6" width="8" height="14" rx="3" fill="#3A3A42"/>` },
  negotiation_book:{ w:20, h:22, art:`<rect x="-10" y="-11" width="20" height="22" rx="2" fill="#A9744F" stroke="#5A3A1F" stroke-width="1.5"/><rect x="-10" y="-11" width="5" height="22" rx="1" fill="#7A4F2F"/><rect x="-3" y="-7" width="11" height="14" rx="1" fill="#F4F0E6"/><rect x="6" y="-11" width="3" height="8" fill="#E0533F"/>` },
  gaming_setup:  { w:34, h:22, art:`<rect x="-17" y="-3" width="34" height="13" rx="3" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.5"/><rect x="-14" y="-11" width="22" height="8" rx="1" fill="#2B2B33"/><rect x="11" y="-2" width="9" height="8" rx="2" fill="#5C6BC0"/>` },
  ergonomic_chair:{ w:26, h:26, art:`<ellipse cx="0" cy="2" rx="11" ry="9" fill="#5C6BC0" stroke="#3F4AA0" stroke-width="1.5"/><rect x="-9" y="-12" width="18" height="8" rx="4" fill="#6E7BD0" stroke="#3F4AA0" stroke-width="1.5"/>` },
  second_monitor:{ w:30, h:18, art:`<rect x="-15" y="-8" width="13" height="11" rx="1" fill="#2B2B33" stroke="#111" stroke-width="1"/><rect x="2" y="-8" width="13" height="11" rx="1" fill="#2B2B33" stroke="#111" stroke-width="1"/><rect x="-12" y="-6" width="9" height="7" fill="#5C6BC0"/><rect x="5" y="-6" width="9" height="7" fill="#5C6BC0"/>` },
  printer:       { w:26, h:18, art:`<rect x="-13" y="-6" width="26" height="13" rx="2" fill="#D7DBE0" stroke="#9AA3AB" stroke-width="1.5"/><rect x="-13" y="-9" width="26" height="5" rx="2" fill="#B8BEC4"/><rect x="-7" y="5" width="14" height="6" rx="1" fill="#fff" stroke="#9AA3AB" stroke-width="1"/>` },
  music_studio:  { w:34, h:18, art:`<rect x="-17" y="-3" width="26" height="8" rx="1" fill="#2B2B33"/><rect x="-15" y="-1" width="2.5" height="5" fill="#fff"/><rect x="-11" y="-1" width="2.5" height="5" fill="#fff"/><rect x="-7" y="-1" width="2.5" height="5" fill="#fff"/><rect x="-3" y="-1" width="2.5" height="5" fill="#fff"/><rect x="1" y="-1" width="2.5" height="5" fill="#fff"/><rect x="11" y="-7" width="7" height="7" rx="1" fill="#5A5A62"/>` },
  // ── Garage ──
  workbench_tools:{ w:34, h:22, art:`<rect x="-17" y="-4" width="34" height="13" rx="2" fill="#A9744F" stroke="#5A3A1F" stroke-width="1.5"/><rect x="-17" y="-11" width="34" height="6" rx="1" fill="#8A8A92"/><line x1="-11" y1="-10" x2="-11" y2="-6" stroke="#3A3A42" stroke-width="1.5"/><rect x="-3" y="-10" width="5" height="4" fill="#E0533F"/>` },
  home_gym:      { w:30, h:22, art:`<rect x="-15" y="-7" width="30" height="16" rx="3" fill="#3A3A42" stroke="#111" stroke-width="1.5"/><line x1="-15" y1="-11" x2="15" y2="-11" stroke="#8A8A92" stroke-width="2"/><circle cx="-14" cy="-11" r="3" fill="#2B2B33"/><circle cx="14" cy="-11" r="3" fill="#2B2B33"/>` },
  motorcycle:    { w:20, h:36, art:`<rect x="-5" y="-16" width="10" height="32" rx="5" fill="#C0392B" stroke="#7E2218" stroke-width="1.5"/><circle cx="0" cy="-15" r="6" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><circle cx="0" cy="15" r="7" fill="#2B2B33" stroke="#111" stroke-width="1.5"/><line x1="-8" y1="-10" x2="8" y2="-10" stroke="#4A4A52" stroke-width="2"/>` },
  sports_car:    { w:30, h:40, art:`<rect x="-13" y="-18" width="26" height="36" rx="9" fill="#E0533F" stroke="#992F22" stroke-width="1.5"/><rect x="-10" y="-6" width="20" height="13" rx="3" fill="#8AD4F0" stroke="#2E7FA8" stroke-width="1"/><rect x="-10" y="-15" width="20" height="7" rx="2" fill="#F4A8A0"/><rect x="-17" y="-13" width="5" height="10" rx="2" fill="#2B2B33"/><rect x="12" y="-13" width="5" height="10" rx="2" fill="#2B2B33"/><rect x="-17" y="5" width="5" height="10" rx="2" fill="#2B2B33"/><rect x="12" y="5" width="5" height="10" rx="2" fill="#2B2B33"/>` },
  professional_gym:{ w:30, h:26, art:`<rect x="-7" y="-13" width="14" height="26" rx="3" fill="#3A3A42" stroke="#111" stroke-width="1.5"/><line x1="-14" y1="0" x2="14" y2="0" stroke="#8A8A92" stroke-width="2"/><circle cx="-13" cy="0" r="4" fill="#2B2B33"/><circle cx="13" cy="0" r="4" fill="#2B2B33"/>` },
  // ── Outdoor ──
  bbq_grill:     { w:26, h:22, art:`<rect x="-13" y="-7" width="26" height="15" rx="3" fill="#3A3A42" stroke="#111" stroke-width="1.5"/><rect x="-13" y="-10" width="26" height="5" rx="2" fill="#5A5A62"/><circle cx="-6" cy="-1" r="3" fill="#FF9A3D"/><circle cx="1" cy="-1" r="3" fill="#FF9A3D"/><circle cx="8" cy="-1" r="3" fill="#FF9A3D"/>` },
  patio_set:     { w:34, h:32, art:`<circle cx="0" cy="0" r="9" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.5"/><circle cx="-13" cy="0" r="5" fill="#B5763A" stroke="#7A4F2F" stroke-width="1"/><circle cx="13" cy="0" r="5" fill="#B5763A" stroke="#7A4F2F" stroke-width="1"/><circle cx="0" cy="-13" r="5" fill="#B5763A" stroke="#7A4F2F" stroke-width="1"/>` },
  swimming_pool: { w:50, h:30, art:`<ellipse cx="0" cy="0" rx="24" ry="14" fill="#5AB6E0" stroke="#2E7FA8" stroke-width="2"/><ellipse cx="0" cy="0" rx="18" ry="9" fill="#8AD4F0"/>` },
  garden:        { w:34, h:24, art:`<rect x="-17" y="-10" width="34" height="20" rx="3" fill="#8A5A2F" stroke="#5A3A1F" stroke-width="1.5"/><circle cx="-10" cy="-4" r="2.5" fill="#E0533F"/><circle cx="0" cy="-4" r="2.5" fill="#F2C744"/><circle cx="10" cy="-4" r="2.5" fill="#E08AB0"/><circle cx="-5" cy="4" r="2.5" fill="#5FB85F"/><circle cx="6" cy="4" r="2.5" fill="#E0533F"/>` },
  fire_pit:      { w:28, h:28, art:`<circle cx="0" cy="0" r="13" fill="#9AA3AB" stroke="#5A5A62" stroke-width="2"/><circle cx="0" cy="0" r="8" fill="#5A4A3A"/><path d="M-6 2 q-3 -11 4 -12 q-2 8 4 8 q4 -3 3 -9 q6 6 0 13 z" fill="#FF9A3D"/>` },
  basketball_hoop:{ w:26, h:22, art:`<rect x="-11" y="-11" width="22" height="6" rx="1" fill="#F4F0E6" stroke="#9AA3AB" stroke-width="1.5"/><rect x="-5" y="-5" width="10" height="7" rx="1" fill="none" stroke="#E0533F" stroke-width="2"/><circle cx="0" cy="8" r="6" fill="#E8862E" stroke="#A85A18" stroke-width="1.5"/>` },
  indoor_pool:   { w:50, h:30, art:`<rect x="-25" y="-14" width="50" height="28" rx="3" fill="#DCE6E8" stroke="#9AA3AB" stroke-width="1.5"/><rect x="-20" y="-9" width="40" height="18" rx="2" fill="#5AB6E0"/><line x1="-20" y1="-2" x2="20" y2="-2" stroke="#fff" stroke-width="1.5" stroke-dasharray="4 3"/><line x1="-20" y1="4" x2="20" y2="4" stroke="#fff" stroke-width="1.5" stroke-dasharray="4 3"/>` },
  // ── Cosmetic decor (fixtures, not buyable — always present in the room) ──
  decor_toilet:        { w:16, h:22, art:`<rect x="-7" y="-11" width="14" height="7" rx="2" fill="#EDEFF2" stroke="#9AA6AE" stroke-width="1.2"/><ellipse cx="0" cy="3" rx="7" ry="8" fill="#F4F6F8" stroke="#9AA6AE" stroke-width="1.2"/><ellipse cx="0" cy="3" rx="4" ry="5" fill="#D9E2E8"/>` },
  decor_pedestal_sink: { w:16, h:16, art:`<rect x="-3" y="0" width="6" height="7" fill="#D7DEE3"/><ellipse cx="0" cy="-1" rx="8" ry="6" fill="#F4F6F8" stroke="#9AA6AE" stroke-width="1.2"/><ellipse cx="0" cy="-1" rx="4.5" ry="3" fill="#D9E2E8"/><circle cx="0" cy="-4" r="1.2" fill="#9AA6AE"/>` },
  decor_bathtub:       { w:34, h:18, art:`<rect x="-17" y="-9" width="34" height="18" rx="8" fill="#F4F6F8" stroke="#9AA6AE" stroke-width="1.4"/><rect x="-13" y="-6" width="26" height="12" rx="6" fill="#DCEAF1"/><circle cx="-10" cy="0" r="1.3" fill="#9AA6AE"/>` },
  decor_shower:        { w:20, h:20, art:`<rect x="-10" y="-10" width="20" height="20" rx="3" fill="#E4EBF0" stroke="#9AA6AE" stroke-width="1.2"/><circle cx="0" cy="0" r="2.5" fill="#9AA6AE"/><circle cx="6" cy="-6" r="2" fill="#CBD6DD"/>` },
  decor_kitchen_sink:  { w:26, h:14, art:`<rect x="-13" y="-7" width="26" height="14" rx="2" fill="#CFD4DA" stroke="#9AA3AB" stroke-width="1.2"/><rect x="-10" y="-4" width="8" height="8" rx="1.5" fill="#AEB8C0"/><rect x="2" y="-4" width="8" height="8" rx="1.5" fill="#AEB8C0"/><circle cx="0" cy="-5" r="1.2" fill="#7D868E"/>` },
  decor_counter:       { w:40, h:12, art:`<rect x="-20" y="-6" width="40" height="12" rx="2" fill="#CFD4DA" stroke="#9AA3AB" stroke-width="1.2"/><rect x="-20" y="-6" width="40" height="4" rx="2" fill="#C98A4E"/>` },
  decor_counter_corner:{ w:24, h:24, art:`<path d="M-12 -12 h24 v10 h-14 v14 h-10 z" fill="#CFD4DA" stroke="#9AA3AB" stroke-width="1.2"/><path d="M-12 -12 h24 v4 h-20 v20 h-4 z" fill="#C98A4E"/>` },
  decor_stove:         { w:20, h:20, art:`<rect x="-10" y="-10" width="20" height="20" rx="2" fill="#3A3A42" stroke="#111" stroke-width="1.2"/><circle cx="-5" cy="-5" r="3" fill="#5A5A66"/><circle cx="5" cy="-5" r="3" fill="#5A5A66"/><circle cx="-5" cy="5" r="3" fill="#5A5A66"/><circle cx="5" cy="5" r="3" fill="#5A5A66"/>` },
  decor_dining_table:  { w:40, h:30, art:`<rect x="-13" y="-13" width="26" height="26" rx="4" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.4"/><rect x="-18" y="-5" width="4" height="10" rx="1" fill="#A9744F"/><rect x="14" y="-5" width="4" height="10" rx="1" fill="#A9744F"/><rect x="-5" y="-18" width="10" height="4" rx="1" fill="#A9744F"/><rect x="-5" y="14" width="10" height="4" rx="1" fill="#A9744F"/>` },
  decor_dining_chair:  { w:12, h:12, art:`<rect x="-5" y="-5" width="10" height="10" rx="2" fill="#B5763A" stroke="#7A4F2F" stroke-width="1.2"/><rect x="-5" y="-6" width="10" height="3" rx="1" fill="#9A6432"/>` },
  decor_armchair:      { w:18, h:18, art:`<rect x="-9" y="-6" width="18" height="14" rx="4" fill="#A9C0E0" stroke="#5E7BA8" stroke-width="1.3"/><rect x="-9" y="-8" width="18" height="6" rx="3" fill="#8FAAD6"/><rect x="-11" y="-4" width="4" height="10" rx="2" fill="#8FAAD6"/><rect x="7" y="-4" width="4" height="10" rx="2" fill="#8FAAD6"/>` },
  decor_side_table:    { w:14, h:14, art:`<circle cx="0" cy="0" r="7" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.3"/><circle cx="0" cy="0" r="3" fill="#B5763A"/>` },
  decor_nightstand:    { w:12, h:12, art:`<rect x="-6" y="-6" width="12" height="12" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.2"/><circle cx="0" cy="0" r="1.4" fill="#5A3A1F"/>` },
  decor_dresser:       { w:30, h:14, art:`<rect x="-15" y="-7" width="30" height="14" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.3"/><line x1="0" y1="-7" x2="0" y2="7" stroke="#7A4F2F"/><circle cx="-7" cy="0" r="1.3" fill="#5A3A1F"/><circle cx="7" cy="0" r="1.3" fill="#5A3A1F"/>` },
  decor_floor_lamp:    { w:12, h:12, art:`<circle cx="0" cy="0" r="6" fill="#F7E7A6" stroke="#D9B85A" stroke-width="1.2"/><circle cx="0" cy="0" r="2.5" fill="#FFF6D6"/>` },
  decor_table_lamp:    { w:10, h:10, art:`<circle cx="0" cy="0" r="5" fill="#F7E7A6" stroke="#D9B85A" stroke-width="1"/><circle cx="0" cy="0" r="2" fill="#FFF6D6"/>` },
  decor_rug:           { w:52, h:36, art:`<rect x="-26" y="-18" width="52" height="36" rx="4" fill="#D98C8C" stroke="#A85E5E" stroke-width="1.5"/><rect x="-21" y="-13" width="42" height="26" rx="3" fill="none" stroke="#EFC9C9" stroke-width="1.5"/><rect x="-15" y="-8" width="30" height="16" rx="2" fill="#C97676"/>` },
  decor_rug_round:     { w:34, h:34, art:`<circle cx="0" cy="0" r="16" fill="#8FB0C9" stroke="#5E7E96" stroke-width="1.5"/><circle cx="0" cy="0" r="11" fill="none" stroke="#C5DCEA" stroke-width="1.5"/><circle cx="0" cy="0" r="6" fill="#7299B5"/>` },
  decor_doorway:       { w:20, h:18, art:`<path d="M-9 -8 A16 16 0 0 1 7 8" fill="none" stroke="#9AA3AB" stroke-width="1" stroke-dasharray="2 2"/><rect x="-10" y="-9" width="3" height="17" rx="1" fill="#A9744F"/>` },
  decor_window:        { w:22, h:6,  art:`<rect x="-11" y="-3" width="22" height="6" rx="1" fill="#CFE8F5" stroke="#7FB5D8" stroke-width="1.2"/><line x1="0" y1="-3" x2="0" y2="3" stroke="#7FB5D8"/>` },
  decor_ceiling_fan:   { w:20, h:20, art:`<ellipse cx="0" cy="-7" rx="3" ry="7" fill="#C7B299" stroke="#9A8568" stroke-width="0.8"/><ellipse cx="0" cy="7" rx="3" ry="7" fill="#C7B299" stroke="#9A8568" stroke-width="0.8"/><ellipse cx="-7" cy="0" rx="7" ry="3" fill="#C7B299" stroke="#9A8568" stroke-width="0.8"/><ellipse cx="7" cy="0" rx="7" ry="3" fill="#C7B299" stroke="#9A8568" stroke-width="0.8"/><circle cx="0" cy="0" r="3" fill="#8A8A92"/>` },
  decor_stairs:        { w:20, h:30, art:`<rect x="-10" y="-15" width="20" height="30" rx="1" fill="#C7B299" stroke="#9A8568" stroke-width="1"/><line x1="-10" y1="-9" x2="10" y2="-9" stroke="#9A8568"/><line x1="-10" y1="-3" x2="10" y2="-3" stroke="#9A8568"/><line x1="-10" y1="3" x2="10" y2="3" stroke="#9A8568"/><line x1="-10" y1="9" x2="10" y2="9" stroke="#9A8568"/>` },
  decor_bar_stool:     { w:10, h:10, art:`<circle cx="0" cy="0" r="5" fill="#5A5A66" stroke="#3A3A42" stroke-width="1"/><circle cx="0" cy="0" r="2" fill="#7A7A86"/>` },
  decor_plant_small:   { w:14, h:16, art:`<rect x="-4" y="2" width="8" height="6" rx="1.5" fill="#C66B3D" stroke="#8A4527" stroke-width="1"/><circle cx="-2" cy="-3" r="4" fill="#5FB85F"/><circle cx="3" cy="-4" r="4" fill="#4CAF50"/>` },
  decor_coffee_table:  { w:28, h:16, art:`<rect x="-14" y="-8" width="28" height="16" rx="3" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.3"/><rect x="-10" y="-5" width="20" height="10" rx="2" fill="#B5763A"/>` },
  decor_tv_console:    { w:34, h:12, art:`<rect x="-17" y="-6" width="34" height="12" rx="2" fill="#7A4F2F" stroke="#4A2F1A" stroke-width="1.3"/><rect x="-13" y="-3" width="9" height="6" rx="1" fill="#5A3A1F"/><rect x="-2" y="-3" width="9" height="6" rx="1" fill="#5A3A1F"/><rect x="9" y="-3" width="6" height="6" rx="1" fill="#5A3A1F"/>` },
  decor_ottoman:       { w:16, h:16, art:`<rect x="-8" y="-8" width="16" height="16" rx="4" fill="#D4A05A" stroke="#9A6A3F" stroke-width="1.3"/><line x1="-8" y1="0" x2="8" y2="0" stroke="#B5763A" stroke-width="0.8"/><line x1="0" y1="-8" x2="0" y2="8" stroke="#B5763A" stroke-width="0.8"/>` },
  decor_wall_shelf:    { w:26, h:8,  art:`<rect x="-13" y="-4" width="26" height="6" rx="1" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.2"/><rect x="-10" y="-7" width="4" height="3" fill="#E0533F"/><rect x="-4" y="-8" width="3" height="4" fill="#4D8FE0"/><rect x="2" y="-7" width="4" height="3" fill="#5FB85F"/><rect x="8" y="-8" width="3" height="4" fill="#F2C744"/>` },
  decor_record_player: { w:16, h:14, art:`<rect x="-8" y="-7" width="16" height="14" rx="2" fill="#3A3A42" stroke="#111" stroke-width="1.2"/><circle cx="-1" cy="0" r="5" fill="#5A5A66"/><circle cx="-1" cy="0" r="1.5" fill="#C98A4E"/><rect x="4" y="-5" width="3" height="6" rx="1" fill="#8A8A92"/>` },
  decor_plant_tall:    { w:16, h:18, art:`<rect x="-5" y="4" width="10" height="8" rx="2" fill="#C66B3D" stroke="#8A4527" stroke-width="1.2"/><circle cx="-3" cy="-4" r="5" fill="#4CAF50"/><circle cx="3" cy="-6" r="5" fill="#66BB6A"/><circle cx="2" cy="0" r="4" fill="#4CAF50"/><circle cx="-2" cy="-9" r="4" fill="#7CCB7E"/>` },
  decor_mirror:        { w:8,  h:18, art:`<rect x="-4" y="-9" width="8" height="18" rx="3" fill="#CFE8F5" stroke="#9AA6AE" stroke-width="1.3"/><rect x="-2" y="-7" width="3" height="14" rx="1" fill="#EAF4FA" opacity="0.7"/>` },
  decor_clock:         { w:12, h:12, art:`<circle cx="0" cy="0" r="6" fill="#F4F0E6" stroke="#5A5A62" stroke-width="1.3"/><line x1="0" y1="0" x2="0" y2="-4" stroke="#2B2B33" stroke-width="1"/><line x1="0" y1="0" x2="3" y2="1" stroke="#2B2B33" stroke-width="1"/>` },
  decor_runner_rug:    { w:14, h:44, art:`<rect x="-7" y="-22" width="14" height="44" rx="3" fill="#C97676" stroke="#A85E5E" stroke-width="1.3"/><rect x="-5" y="-19" width="10" height="38" rx="2" fill="none" stroke="#EFC9C9" stroke-width="1.2"/>` },
  decor_wall_divider:  { w:30, h:5,  art:`<rect x="-15" y="-2.5" width="30" height="5" rx="1" fill="#4A3A2C"/>` },
  decor_column:        { w:12, h:12, art:`<circle cx="0" cy="0" r="6" fill="#D7DBE0" stroke="#9AA3AB" stroke-width="1.3"/><circle cx="0" cy="0" r="3" fill="#ECEFF1"/>` },
  decor_wardrobe:      { w:26, h:14, art:`<rect x="-13" y="-7" width="26" height="14" rx="2" fill="#9A6A3F" stroke="#5A3A1F" stroke-width="1.3"/><line x1="0" y1="-7" x2="0" y2="7" stroke="#5A3A1F"/><circle cx="-2" cy="0" r="1.2" fill="#3A2410"/><circle cx="2" cy="0" r="1.2" fill="#3A2410"/>` },
  decor_vanity:        { w:22, h:12, art:`<rect x="-11" y="-2" width="22" height="10" rx="2" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.3"/><rect x="-8" y="-7" width="16" height="6" rx="2" fill="#CFE8F5" stroke="#9AA6AE" stroke-width="1"/>` },
  decor_crib:          { w:22, h:28, art:`<rect x="-11" y="-14" width="22" height="28" rx="3" fill="#FBF3E6" stroke="#CBB89A" stroke-width="1.3"/><rect x="-8" y="-3" width="16" height="14" rx="3" fill="#F4C0D1"/><line x1="-11" y1="-7" x2="11" y2="-7" stroke="#CBB89A" stroke-width="0.7"/>` },
  decor_microwave:     { w:16, h:12, art:`<rect x="-8" y="-6" width="16" height="12" rx="2" fill="#D7DBE0" stroke="#9AA3AB" stroke-width="1.2"/><rect x="-6" y="-4" width="8" height="8" rx="1" fill="#4A4A52"/><circle cx="5" cy="-2" r="1" fill="#5A5A66"/><circle cx="5" cy="2" r="1" fill="#5A5A66"/>` },
  decor_dishwasher:    { w:20, h:18, art:`<rect x="-10" y="-9" width="20" height="18" rx="2" fill="#ECEFF1" stroke="#90A4AE" stroke-width="1.3"/><rect x="-7" y="-6" width="14" height="3" rx="1" fill="#B0BEC5"/><rect x="-6" y="6" width="12" height="1.5" rx="0.7" fill="#90A4AE"/>` },
  decor_trash_can:     { w:10, h:12, art:`<rect x="-5" y="-6" width="10" height="12" rx="2" fill="#8A8A92" stroke="#5A5A62" stroke-width="1.2"/><rect x="-6" y="-7" width="12" height="2.5" rx="1" fill="#6A6A72"/>` },
  decor_pantry:        { w:16, h:14, art:`<rect x="-8" y="-7" width="16" height="14" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.3"/><line x1="0" y1="-7" x2="0" y2="7" stroke="#7A4F2F"/><circle cx="-2" cy="0" r="1" fill="#5A3A1F"/><circle cx="2" cy="0" r="1" fill="#5A3A1F"/>` },
  decor_washer:        { w:18, h:18, art:`<rect x="-9" y="-9" width="18" height="18" rx="2" fill="#ECEFF1" stroke="#90A4AE" stroke-width="1.3"/><circle cx="0" cy="1" r="5.5" fill="#CFE8F5" stroke="#7FB5D8" stroke-width="1.2"/><circle cx="0" cy="1" r="2.5" fill="#AED4EA"/><rect x="-6" y="-7" width="12" height="2" rx="1" fill="#B0BEC5"/>` },
  decor_dryer:         { w:18, h:18, art:`<rect x="-9" y="-9" width="18" height="18" rx="2" fill="#E4EBF0" stroke="#90A4AE" stroke-width="1.3"/><circle cx="0" cy="1" r="5.5" fill="#F4EAD8" stroke="#C7B299" stroke-width="1.2"/><circle cx="0" cy="1" r="2.5" fill="#E8DCC4"/><rect x="-6" y="-7" width="12" height="2" rx="1" fill="#B0BEC5"/>` },
  decor_towel_rack:    { w:14, h:6,  art:`<rect x="-7" y="-3" width="14" height="6" rx="1" fill="#A9C8C0" stroke="#6A9A90" stroke-width="1.2"/><rect x="-5" y="-3" width="4" height="6" rx="1" fill="#CFE8E2"/><rect x="1" y="-3" width="4" height="6" rx="1" fill="#E8DCC4"/>` },
  decor_desk:          { w:28, h:14, art:`<rect x="-14" y="-7" width="28" height="14" rx="2" fill="#A9744F" stroke="#7A4F2F" stroke-width="1.3"/><rect x="-12" y="-2" width="8" height="7" rx="1" fill="#8A5A28"/>` },
  decor_office_chair:  { w:12, h:12, art:`<ellipse cx="0" cy="1" rx="6" ry="5" fill="#5A5A66" stroke="#3A3A42" stroke-width="1.2"/><rect x="-5" y="-6" width="10" height="4" rx="2" fill="#6A6A72"/>` },
  decor_car_sedan:     { w:26, h:36, art:`<rect x="-11" y="-16" width="22" height="32" rx="7" fill="#5E7BA8" stroke="#3F567A" stroke-width="1.3"/><rect x="-8" y="-5" width="16" height="11" rx="3" fill="#AED4EA" stroke="#7FB5D8" stroke-width="1"/><rect x="-8" y="-13" width="16" height="6" rx="2" fill="#8FAAD6"/><rect x="-14" y="-11" width="4" height="8" rx="2" fill="#2B2B33"/><rect x="10" y="-11" width="4" height="8" rx="2" fill="#2B2B33"/><rect x="-14" y="4" width="4" height="8" rx="2" fill="#2B2B33"/><rect x="10" y="4" width="4" height="8" rx="2" fill="#2B2B33"/>` },
  decor_tool_chest:    { w:20, h:12, art:`<rect x="-10" y="-6" width="20" height="12" rx="2" fill="#C0392B" stroke="#7E2218" stroke-width="1.3"/><rect x="-8" y="-3.5" width="16" height="2.5" rx="1" fill="#E0533F"/><rect x="-8" y="0.5" width="16" height="2.5" rx="1" fill="#E0533F"/>` },
  decor_storage_rack:  { w:28, h:12, art:`<rect x="-14" y="-6" width="28" height="12" rx="1" fill="#8A8A92" stroke="#5A5A62" stroke-width="1.2"/><rect x="-12" y="-4" width="7" height="8" fill="#C98A4E"/><rect x="-3" y="-4" width="7" height="8" fill="#A9744F"/><rect x="6" y="-4" width="6" height="8" fill="#C98A4E"/>` },
  decor_bicycle:       { w:12, h:26, art:`<circle cx="0" cy="-9" r="6" fill="none" stroke="#3A3A42" stroke-width="2"/><circle cx="0" cy="9" r="6" fill="none" stroke="#3A3A42" stroke-width="2"/><line x1="0" y1="-9" x2="0" y2="9" stroke="#E0533F" stroke-width="2"/><line x1="-3" y1="0" x2="3" y2="0" stroke="#E0533F" stroke-width="2"/>` },
  decor_tree:          { w:28, h:28, art:`<circle cx="0" cy="0" r="13" fill="#5FB85F" stroke="#3E8E3E" stroke-width="1.5"/><circle cx="-5" cy="-4" r="6" fill="#7CCB7E"/><circle cx="5" cy="3" r="6" fill="#4CAF50"/><circle cx="0" cy="0" r="3" fill="#8A5A2F"/>` },
  decor_bush:          { w:18, h:16, art:`<ellipse cx="0" cy="0" rx="9" ry="8" fill="#5FB85F" stroke="#3E8E3E" stroke-width="1.3"/><circle cx="-3" cy="-2" r="4" fill="#7CCB7E"/><circle cx="3" cy="2" r="4" fill="#4CAF50"/>` },
  decor_bench:         { w:22, h:8,  art:`<rect x="-11" y="-4" width="22" height="6" rx="1" fill="#B5763A" stroke="#7A4F2F" stroke-width="1.2"/><rect x="-11" y="-4" width="22" height="2.5" rx="1" fill="#9A6432"/>` },
  decor_patio_umbrella:{ w:30, h:30, art:`<circle cx="0" cy="0" r="14" fill="#E0533F" stroke="#992F22" stroke-width="1.4"/><line x1="0" y1="-14" x2="0" y2="14" stroke="#fff" stroke-width="0.8" opacity="0.6"/><line x1="-14" y1="0" x2="14" y2="0" stroke="#fff" stroke-width="0.8" opacity="0.6"/><circle cx="0" cy="0" r="2.5" fill="#7A4F2F"/>` },
  decor_lounge_chair:  { w:14, h:26, art:`<rect x="-6" y="-13" width="12" height="26" rx="4" fill="#A9C8C0" stroke="#6A9A90" stroke-width="1.3"/><rect x="-5" y="-12" width="10" height="8" rx="3" fill="#CFE8E2"/><line x1="-5" y1="-2" x2="5" y2="-2" stroke="#6A9A90" stroke-width="0.7"/><line x1="-5" y1="3" x2="5" y2="3" stroke="#6A9A90" stroke-width="0.7"/>` },
  decor_fence:         { w:30, h:6,  art:`<rect x="-15" y="-3" width="30" height="4" rx="1" fill="#C7B299" stroke="#9A8568" stroke-width="1"/><rect x="-13" y="-3" width="2" height="6" fill="#B5A082"/><rect x="-5" y="-3" width="2" height="6" fill="#B5A082"/><rect x="3" y="-3" width="2" height="6" fill="#B5A082"/><rect x="11" y="-3" width="2" height="6" fill="#B5A082"/>` },
  decor_flower_bed:    { w:24, h:12, art:`<rect x="-12" y="-6" width="24" height="12" rx="3" fill="#8A5A2F" stroke="#5A3A1F" stroke-width="1.2"/><circle cx="-7" cy="0" r="2.5" fill="#E08AB0"/><circle cx="-1" cy="-1" r="2.5" fill="#F2C744"/><circle cx="5" cy="0" r="2.5" fill="#E0533F"/><circle cx="9" cy="1" r="2" fill="#7CCB7E"/>` },
  decor_pond:          { w:34, h:22, art:`<ellipse cx="0" cy="0" rx="16" ry="10" fill="#5AB6E0" stroke="#2E7FA8" stroke-width="1.5"/><ellipse cx="0" cy="0" rx="11" ry="6" fill="#8AD4F0"/><ellipse cx="-4" cy="-1" rx="2.5" ry="1.5" fill="#5FB85F"/>` },
  decor_mailbox:       { w:8,  h:10, art:`<rect x="-4" y="-3" width="8" height="6" rx="2" fill="#C0392B" stroke="#7E2218" stroke-width="1.2"/><rect x="-1" y="3" width="2" height="4" fill="#7A4F2F"/><rect x="3" y="-3" width="2" height="3" fill="#F2C744"/>` },
  decor_pet_dog:       { w:14, h:12, art:`<ellipse cx="0" cy="1" rx="6" ry="5" fill="#C98A4E" stroke="#8A5A28" stroke-width="1.2"/><circle cx="0" cy="-5" r="3.5" fill="#B5763A"/><circle cx="-2" cy="-6" r="1.2" fill="#5A3A1F"/><circle cx="2" cy="-6" r="1.2" fill="#5A3A1F"/>` },
  decor_pet_cat:       { w:12, h:12, art:`<ellipse cx="0" cy="1" rx="5" ry="5" fill="#8A8A92" stroke="#5A5A62" stroke-width="1.2"/><circle cx="0" cy="-4" r="3" fill="#9AA0A8"/><path d="M-3 -6 l1 -2 l1.5 1.5 z" fill="#9AA0A8"/><path d="M3 -6 l-1 -2 l-1.5 1.5 z" fill="#9AA0A8"/>` },
};

// Baked floor-plan layouts authored in the editor. Per home: room shapes and
// explicit furniture placement (center x,y in viewBox units, scale, rotation).
// cosmetic:true pieces always render; buyable pieces render only when owned.
// Source of truth backed up at landlord_web/floor_plan_layout.json.
const FP_LAYOUT = JSON.parse('{"grandmas_basement":{"rooms":[{"key":"living","label":"Living","x":4,"y":4,"w":150,"h":96}],"furniture":[{"key":"house_plant","cosmetic":false,"x":117,"y":90,"scale":0.5,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":144,"y":15,"scale":0.75,"rot":0},{"key":"new_bed","cosmetic":false,"x":22,"y":23,"scale":1,"rot":0},{"key":"blackout_curtains","cosmetic":false,"x":77,"y":99,"scale":1,"rot":0},{"key":"decor_stairs","cosmetic":true,"x":141,"y":82,"scale":1.2,"rot":180},{"key":"decor_doorway","cosmetic":true,"x":142,"y":92,"scale":1,"rot":270},{"key":"decor_floor_lamp","cosmetic":true,"x":19,"y":89,"scale":1,"rot":0},{"key":"decor_rug","cosmetic":true,"x":82,"y":58,"scale":1,"rot":15},{"key":"decor_nightstand","cosmetic":true,"x":120,"y":13,"scale":1.15,"rot":0},{"key":"instant_pot","cosmetic":false,"x":120,"y":12,"scale":0.5,"rot":0},{"key":"decor_bar_stool","cosmetic":true,"x":13,"y":59,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":55,"y":12,"scale":0.55,"rot":0},{"key":"decor_nightstand","cosmetic":true,"x":105,"y":13,"scale":1.1,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":105,"y":12,"scale":0.6,"rot":0}]},"small_apt":{"rooms":[{"key":"living","label":"Living","x":4,"y":4,"w":174,"h":112},{"key":"kitchen","label":"Kitchen","x":103,"y":4,"w":75,"h":53},{"key":"bedroom","label":"Bedroom","x":4,"y":108,"w":104,"h":78},{"key":"bath","label":"Bath","x":110,"y":118,"w":58,"h":58}],"furniture":[{"key":"decor_rug","cosmetic":true,"x":130,"y":140,"scale":0.5,"rot":105},{"key":"decor_rug_round","cosmetic":true,"x":40,"y":40,"scale":1.8,"rot":0},{"key":"house_plant","cosmetic":false,"x":93,"y":53,"scale":0.6,"rot":0},{"key":"couch","cosmetic":false,"x":50,"y":29,"scale":1,"rot":90},{"key":"flat_screen_tv","cosmetic":false,"x":8,"y":28,"scale":1,"rot":90},{"key":"aquarium","cosmetic":false,"x":14,"y":91,"scale":0.8,"rot":90},{"key":"mini_fridge","cosmetic":false,"x":166,"y":17,"scale":0.95,"rot":0},{"key":"new_bed","cosmetic":false,"x":24,"y":151,"scale":1,"rot":270},{"key":"blackout_curtains","cosmetic":false,"x":84,"y":8,"scale":1,"rot":0},{"key":"whiteboard","cosmetic":false,"x":100,"y":147,"scale":1,"rot":90},{"key":"filing_cabinet","cosmetic":false,"x":97,"y":176,"scale":0.8,"rot":90},{"key":"ergonomic_chair","cosmetic":false,"x":41,"y":69,"scale":0.75,"rot":135},{"key":"decor_doorway","cosmetic":true,"x":170,"y":87,"scale":1,"rot":180},{"key":"decor_doorway","cosmetic":true,"x":122,"y":126,"scale":1,"rot":90},{"key":"decor_counter","cosmetic":true,"x":128,"y":55,"scale":1.25,"rot":180},{"key":"headphones","cosmetic":false,"x":110,"y":56,"scale":0.4,"rot":15},{"key":"decor_nightstand","cosmetic":true,"x":13,"y":125,"scale":1,"rot":0},{"key":"decor_nightstand","cosmetic":true,"x":14,"y":178,"scale":1,"rot":0},{"key":"decor_table_lamp","cosmetic":true,"x":14,"y":178,"scale":0.85,"rot":0},{"key":"decor_counter","cosmetic":true,"x":152,"y":55,"scale":1.25,"rot":180},{"key":"decor_kitchen_sink","cosmetic":true,"x":130,"y":55,"scale":1,"rot":180},{"key":"decor_counter","cosmetic":true,"x":129,"y":13,"scale":1.25,"rot":0},{"key":"decor_stove","cosmetic":true,"x":144,"y":13,"scale":0.75,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":111,"y":12,"scale":0.5,"rot":0},{"key":"instant_pot","cosmetic":false,"x":126,"y":13,"scale":0.5,"rot":0},{"key":"decor_toilet","cosmetic":true,"x":156,"y":130,"scale":1,"rot":90},{"key":"decor_pedestal_sink","cosmetic":true,"x":159,"y":150,"scale":1,"rot":270},{"key":"decor_bathtub","cosmetic":true,"x":129,"y":166,"scale":1,"rot":0},{"key":"negotiation_book","cosmetic":false,"x":157,"y":55,"scale":0.4,"rot":15},{"key":"decor_floor_lamp","cosmetic":true,"x":56,"y":60,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":12,"y":124,"scale":0.45,"rot":0}]},"condo":{"rooms":[{"key":"living","label":"Living","x":4,"y":6,"w":150,"h":96},{"key":"kitchen","label":"Kitchen","x":150,"y":6,"w":68,"h":96},{"key":"bedroom","label":"Bedroom","x":115,"y":104,"w":104,"h":78},{"key":"office","label":"Office","x":4,"y":104,"w":48,"h":87},{"key":"bath","label":"Bath","x":54,"y":104,"w":58,"h":58}],"furniture":[{"key":"decor_rug_round","cosmetic":true,"x":157,"y":139,"scale":1.6,"rot":0},{"key":"decor_rug","cosmetic":true,"x":49,"y":48,"scale":1,"rot":0},{"key":"decor_counter","cosmetic":true,"x":178,"y":16,"scale":1.35,"rot":0},{"key":"house_plant","cosmetic":false,"x":104,"y":15,"scale":0.5,"rot":0},{"key":"couch","cosmetic":false,"x":49,"y":53,"scale":1,"rot":180},{"key":"flat_screen_tv","cosmetic":false,"x":50,"y":9,"scale":1,"rot":180},{"key":"bookshelf","cosmetic":false,"x":11,"y":35,"scale":0.65,"rot":90},{"key":"aquarium","cosmetic":false,"x":51,"y":94,"scale":0.7,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":206,"y":20,"scale":1,"rot":0},{"key":"instant_pot","cosmetic":false,"x":159,"y":15,"scale":0.5,"rot":0},{"key":"new_bed","cosmetic":false,"x":165,"y":163,"scale":1,"rot":180},{"key":"blackout_curtains","cosmetic":false,"x":215,"y":139,"scale":1,"rot":90},{"key":"meditation_corner","cosmetic":false,"x":108,"y":95,"scale":1,"rot":0},{"key":"whiteboard","cosmetic":false,"x":12,"y":160,"scale":1,"rot":270},{"key":"filing_cabinet","cosmetic":false,"x":42,"y":182,"scale":0.75,"rot":90},{"key":"ergonomic_chair","cosmetic":false,"x":34,"y":133,"scale":0.9,"rot":255},{"key":"decor_doorway","cosmetic":true,"x":122,"y":151,"scale":1,"rot":0},{"key":"decor_doorway","cosmetic":true,"x":132,"y":112,"scale":1,"rot":90},{"key":"decor_doorway","cosmetic":true,"x":126,"y":14,"scale":1,"rot":90},{"key":"decor_doorway","cosmetic":true,"x":83,"y":112,"scale":1,"rot":90},{"key":"decor_doorway","cosmetic":true,"x":15,"y":112,"scale":1,"rot":90},{"key":"decor_counter","cosmetic":true,"x":44,"y":134,"scale":1.25,"rot":90},{"key":"second_monitor","cosmetic":false,"x":43,"y":127,"scale":1,"rot":90},{"key":"printer","cosmetic":false,"x":43,"y":160,"scale":0.75,"rot":90},{"key":"decor_counter","cosmetic":true,"x":190,"y":93,"scale":1.35,"rot":180},{"key":"decor_counter_corner","cosmetic":true,"x":167,"y":82,"scale":1.55,"rot":270},{"key":"decor_kitchen_sink","cosmetic":true,"x":185,"y":93,"scale":1,"rot":180},{"key":"decor_stove","cosmetic":true,"x":176,"y":16,"scale":0.75,"rot":0},{"key":"wine_rack","cosmetic":false,"x":207,"y":93,"scale":0.55,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":20,"y":183,"scale":0.5,"rot":240},{"key":"espresso_machine","cosmetic":false,"x":156,"y":73,"scale":0.6,"rot":270},{"key":"decor_dining_table","cosmetic":true,"x":110,"y":52,"scale":1,"rot":30},{"key":"negotiation_book","cosmetic":false,"x":116,"y":51,"scale":0.45,"rot":345},{"key":"headphones","cosmetic":false,"x":157,"y":94,"scale":0.4,"rot":15},{"key":"decor_nightstand","cosmetic":true,"x":190,"y":173,"scale":1,"rot":0},{"key":"decor_nightstand","cosmetic":true,"x":138,"y":173,"scale":1,"rot":0},{"key":"decor_dresser","cosmetic":true,"x":165,"y":112,"scale":1,"rot":0},{"key":"decor_armchair","cosmetic":true,"x":201,"y":114,"scale":1,"rot":30},{"key":"decor_table_lamp","cosmetic":true,"x":138,"y":173,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":191,"y":174,"scale":0.5,"rot":0},{"key":"decor_rug","cosmetic":true,"x":186,"y":60,"scale":0.7,"rot":90},{"key":"decor_toilet","cosmetic":true,"x":63,"y":155,"scale":0.75,"rot":270},{"key":"decor_counter","cosmetic":true,"x":61,"y":126,"scale":1.05,"rot":270},{"key":"decor_pedestal_sink","cosmetic":true,"x":61,"y":119,"scale":1,"rot":90},{"key":"decor_bathtub","cosmetic":true,"x":101,"y":122,"scale":1,"rot":90}]},"small_home":{"rooms":[{"key":"living","label":"Living","x":2,"y":77,"w":187,"h":100},{"key":"kitchen","label":"Kitchen","x":92,"y":2,"w":97,"h":75},{"key":"bedroom","label":"Bedroom","x":64,"y":179,"w":125,"h":75},{"key":"office","label":"Office","x":2,"y":2,"w":87,"h":73},{"key":"garage","label":"Garage","x":192,"y":3,"w":123,"h":99},{"key":"outdoor","label":"Patio","x":191,"y":104,"w":81,"h":150},{"key":"bath","label":"Bath","x":2,"y":179,"w":60,"h":75}],"furniture":[{"key":"decor_rug","cosmetic":true,"x":129,"y":41,"scale":0.6,"rot":300},{"key":"decor_rug_round","cosmetic":true,"x":43,"y":45,"scale":1.2,"rot":15},{"key":"decor_rug","cosmetic":true,"x":118,"y":217,"scale":1,"rot":345},{"key":"decor_rug","cosmetic":true,"x":29,"y":118,"scale":0.9,"rot":0},{"key":"ergonomic_chair","cosmetic":false,"x":29,"y":34,"scale":0.8,"rot":45},{"key":"decor_counter","cosmetic":true,"x":101,"y":50,"scale":1.35,"rot":270},{"key":"house_plant","cosmetic":false,"x":12,"y":165,"scale":0.6,"rot":0},{"key":"couch","cosmetic":false,"x":28,"y":124,"scale":1,"rot":180},{"key":"flat_screen_tv","cosmetic":false,"x":29,"y":81,"scale":1,"rot":180},{"key":"bookshelf","cosmetic":false,"x":179,"y":107,"scale":0.85,"rot":270},{"key":"aquarium","cosmetic":false,"x":63,"y":170,"scale":0.6,"rot":0},{"key":"espresso_machine","cosmetic":false,"x":100,"y":64,"scale":0.65,"rot":270},{"key":"kitchen_island","cosmetic":false,"x":150,"y":64,"scale":1,"rot":180},{"key":"new_bed","cosmetic":false,"x":114,"y":235,"scale":1,"rot":180},{"key":"blackout_curtains","cosmetic":false,"x":165,"y":253,"scale":1,"rot":0},{"key":"meditation_corner","cosmetic":false,"x":280,"y":83,"scale":1,"rot":345},{"key":"whiteboard","cosmetic":false,"x":81,"y":40,"scale":1,"rot":90},{"key":"filing_cabinet","cosmetic":false,"x":11,"y":67,"scale":0.7,"rot":270},{"key":"negotiation_book","cosmetic":false,"x":139,"y":64,"scale":0.4,"rot":15},{"key":"bbq_grill","cosmetic":false,"x":253,"y":116,"scale":1,"rot":0},{"key":"patio_set","cosmetic":false,"x":210,"y":193,"scale":1,"rot":75},{"key":"garden","cosmetic":false,"x":244,"y":237,"scale":1.35,"rot":0},{"key":"fire_pit","cosmetic":false,"x":256,"y":170,"scale":0.65,"rot":0},{"key":"basketball_hoop","cosmetic":false,"x":214,"y":115,"scale":1,"rot":0},{"key":"decor_doorway","cosmetic":true,"x":67,"y":67,"scale":1,"rot":270},{"key":"decor_doorway","cosmetic":true,"x":34,"y":187,"scale":1,"rot":90},{"key":"decor_doorway","cosmetic":true,"x":72,"y":199,"scale":1,"rot":0},{"key":"decor_doorway","cosmetic":true,"x":87,"y":187,"scale":1,"rot":90},{"key":"decor_doorway","cosmetic":true,"x":199,"y":78,"scale":1,"rot":0},{"key":"decor_doorway","cosmetic":true,"x":181,"y":139,"scale":1,"rot":180},{"key":"decor_bathtub","cosmetic":true,"x":52,"y":236,"scale":1,"rot":270},{"key":"decor_toilet","cosmetic":true,"x":14,"y":246,"scale":1,"rot":270},{"key":"decor_counter","cosmetic":true,"x":11,"y":207,"scale":1.35,"rot":270},{"key":"decor_pedestal_sink","cosmetic":true,"x":11,"y":192,"scale":1,"rot":90},{"key":"decor_pedestal_sink","cosmetic":true,"x":11,"y":220,"scale":1,"rot":90},{"key":"fireplace","cosmetic":false,"x":131,"y":167,"scale":1,"rot":180},{"key":"decor_nightstand","cosmetic":true,"x":141,"y":245,"scale":1,"rot":0},{"key":"decor_nightstand","cosmetic":true,"x":87,"y":245,"scale":1,"rot":0},{"key":"decor_counter_corner","cosmetic":true,"x":112,"y":23,"scale":1.55,"rot":0},{"key":"decor_counter","cosmetic":true,"x":148,"y":12,"scale":1.35,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":176,"y":16,"scale":1,"rot":0},{"key":"decor_stove","cosmetic":true,"x":101,"y":40,"scale":0.85,"rot":0},{"key":"decor_kitchen_sink","cosmetic":true,"x":122,"y":12,"scale":1,"rot":0},{"key":"decor_dining_table","cosmetic":true,"x":125,"y":109,"scale":1,"rot":15},{"key":"decor_armchair","cosmetic":true,"x":175,"y":191,"scale":1,"rot":45},{"key":"wine_rack","cosmetic":false,"x":155,"y":12,"scale":0.5,"rot":0},{"key":"decor_window","cosmetic":true,"x":316,"y":21,"scale":1,"rot":270},{"key":"decor_window","cosmetic":true,"x":316,"y":87,"scale":1,"rot":90},{"key":"decor_window","cosmetic":true,"x":316,"y":65,"scale":1,"rot":90},{"key":"decor_window","cosmetic":true,"x":316,"y":43,"scale":1,"rot":90},{"key":"decor_side_table","cosmetic":true,"x":63,"y":121,"scale":1,"rot":0},{"key":"decor_dresser","cosmetic":true,"x":122,"y":187,"scale":1,"rot":0},{"key":"decor_table_lamp","cosmetic":true,"x":87,"y":245,"scale":1,"rot":0},{"key":"decor_floor_lamp","cosmetic":true,"x":72,"y":12,"scale":1,"rot":0},{"key":"decor_counter_corner","cosmetic":true,"x":17,"y":18,"scale":1.2,"rot":0},{"key":"gaming_setup","cosmetic":false,"x":12,"y":39,"scale":1,"rot":90},{"key":"second_monitor","cosmetic":false,"x":7,"y":37,"scale":1,"rot":270},{"key":"decor_counter","cosmetic":true,"x":42,"y":10,"scale":1,"rot":0},{"key":"printer","cosmetic":false,"x":23,"y":10,"scale":0.7,"rot":0},{"key":"headphones","cosmetic":false,"x":50,"y":13,"scale":0.4,"rot":15},{"key":"desk_fan","cosmetic":false,"x":130,"y":187,"scale":0.6,"rot":0},{"key":"decor_counter","cosmetic":true,"x":226,"y":14,"scale":1.6,"rot":0},{"key":"decor_counter","cosmetic":true,"x":264,"y":14,"scale":1.6,"rot":0},{"key":"workbench_tools","cosmetic":false,"x":235,"y":15,"scale":1,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":278,"y":14,"scale":0.6,"rot":15},{"key":"instant_pot","cosmetic":false,"x":101,"y":13,"scale":0.45,"rot":315}]},"suburban_home":{"rooms":[{"key":"living","label":"Living","x":4,"y":4,"w":150,"h":96},{"key":"kitchen","label":"Kitchen","x":162,"y":4,"w":100,"h":66},{"key":"bedroom","label":"Bedroom","x":4,"y":108,"w":104,"h":78},{"key":"office","label":"Office","x":116,"y":108,"w":120,"h":76},{"key":"garage","label":"Garage","x":4,"y":194,"w":104,"h":86},{"key":"outdoor","label":"Patio","x":116,"y":194,"w":150,"h":78},{"key":"bath","label":"Bath","x":274,"y":194,"w":58,"h":58}],"furniture":[{"key":"house_plant","cosmetic":false,"x":22,"y":23,"scale":1,"rot":0},{"key":"couch","cosmetic":false,"x":63,"y":17,"scale":1,"rot":0},{"key":"flat_screen_tv","cosmetic":false,"x":110,"y":15,"scale":1,"rot":0},{"key":"bookshelf","cosmetic":false,"x":25,"y":52,"scale":1,"rot":0},{"key":"aquarium","cosmetic":false,"x":64,"y":53,"scale":1,"rot":0},{"key":"fireplace","cosmetic":false,"x":103,"y":52,"scale":1,"rot":0},{"key":"pool_table","cosmetic":false,"x":29,"y":81,"scale":1,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":175,"y":19,"scale":1,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":199,"y":21,"scale":1,"rot":0},{"key":"espresso_machine","cosmetic":false,"x":227,"y":19,"scale":1,"rot":0},{"key":"wine_rack","cosmetic":false,"x":180,"y":51,"scale":1,"rot":0},{"key":"instant_pot","cosmetic":false,"x":210,"y":50,"scale":1,"rot":0},{"key":"kitchen_island","cosmetic":false,"x":183,"y":78,"scale":1,"rot":0},{"key":"smart_fridge","cosmetic":false,"x":216,"y":82,"scale":1,"rot":0},{"key":"new_bed","cosmetic":false,"x":25,"y":130,"scale":1,"rot":0},{"key":"blackout_curtains","cosmetic":false,"x":59,"y":120,"scale":1,"rot":0},{"key":"hot_tub","cosmetic":false,"x":23,"y":166,"scale":1,"rot":0},{"key":"meditation_corner","cosmetic":false,"x":54,"y":160,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":130,"y":122,"scale":1,"rot":0},{"key":"whiteboard","cosmetic":false,"x":161,"y":121,"scale":1,"rot":0},{"key":"filing_cabinet","cosmetic":false,"x":193,"y":124,"scale":1,"rot":0},{"key":"headphones","cosmetic":false,"x":133,"y":152,"scale":1,"rot":0},{"key":"negotiation_book","cosmetic":false,"x":160,"y":151,"scale":1,"rot":0},{"key":"gaming_setup","cosmetic":false,"x":191,"y":151,"scale":1,"rot":0},{"key":"ergonomic_chair","cosmetic":false,"x":133,"y":181,"scale":1,"rot":0},{"key":"second_monitor","cosmetic":false,"x":165,"y":177,"scale":1,"rot":0},{"key":"printer","cosmetic":false,"x":197,"y":177,"scale":1,"rot":0},{"key":"workbench_tools","cosmetic":false,"x":25,"y":209,"scale":1,"rot":0},{"key":"home_gym","cosmetic":false,"x":61,"y":209,"scale":1,"rot":0},{"key":"motorcycle","cosmetic":false,"x":90,"y":216,"scale":1,"rot":0},{"key":"sports_car","cosmetic":false,"x":23,"y":258,"scale":1,"rot":0},{"key":"bbq_grill","cosmetic":false,"x":133,"y":209,"scale":1,"rot":0},{"key":"patio_set","cosmetic":false,"x":167,"y":214,"scale":1,"rot":0},{"key":"garden","cosmetic":false,"x":205,"y":210,"scale":1,"rot":0},{"key":"fire_pit","cosmetic":false,"x":240,"y":212,"scale":1,"rot":0},{"key":"basketball_hoop","cosmetic":false,"x":133,"y":245,"scale":1,"rot":0}]},"luxury_villa":{"rooms":[{"key":"living","label":"Living","x":4,"y":4,"w":150,"h":96},{"key":"kitchen","label":"Kitchen","x":162,"y":4,"w":100,"h":66},{"key":"bedroom","label":"Bedroom","x":4,"y":108,"w":104,"h":78},{"key":"office","label":"Office","x":116,"y":108,"w":120,"h":76},{"key":"garage","label":"Garage","x":4,"y":194,"w":104,"h":86},{"key":"outdoor","label":"Patio","x":116,"y":194,"w":150,"h":78},{"key":"bath","label":"Bath","x":274,"y":194,"w":58,"h":58}],"furniture":[{"key":"house_plant","cosmetic":false,"x":22,"y":23,"scale":1,"rot":0},{"key":"couch","cosmetic":false,"x":63,"y":17,"scale":1,"rot":0},{"key":"flat_screen_tv","cosmetic":false,"x":110,"y":15,"scale":1,"rot":0},{"key":"home_theater","cosmetic":false,"x":31,"y":55,"scale":1,"rot":0},{"key":"bookshelf","cosmetic":false,"x":75,"y":52,"scale":1,"rot":0},{"key":"aquarium","cosmetic":false,"x":114,"y":53,"scale":1,"rot":0},{"key":"fireplace","cosmetic":false,"x":25,"y":82,"scale":1,"rot":0},{"key":"pool_table","cosmetic":false,"x":67,"y":85,"scale":1,"rot":0},{"key":"smart_home_system","cosmetic":false,"x":104,"y":84,"scale":1,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":175,"y":19,"scale":1,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":199,"y":21,"scale":1,"rot":0},{"key":"espresso_machine","cosmetic":false,"x":227,"y":19,"scale":1,"rot":0},{"key":"wine_rack","cosmetic":false,"x":180,"y":51,"scale":1,"rot":0},{"key":"instant_pot","cosmetic":false,"x":210,"y":50,"scale":1,"rot":0},{"key":"kitchen_island","cosmetic":false,"x":183,"y":78,"scale":1,"rot":0},{"key":"smart_fridge","cosmetic":false,"x":216,"y":82,"scale":1,"rot":0},{"key":"new_bed","cosmetic":false,"x":25,"y":130,"scale":1,"rot":0},{"key":"blackout_curtains","cosmetic":false,"x":59,"y":120,"scale":1,"rot":0},{"key":"hot_tub","cosmetic":false,"x":23,"y":166,"scale":1,"rot":0},{"key":"meditation_corner","cosmetic":false,"x":54,"y":160,"scale":1,"rot":0},{"key":"sauna","cosmetic":false,"x":85,"y":165,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":130,"y":122,"scale":1,"rot":0},{"key":"whiteboard","cosmetic":false,"x":161,"y":121,"scale":1,"rot":0},{"key":"filing_cabinet","cosmetic":false,"x":193,"y":124,"scale":1,"rot":0},{"key":"headphones","cosmetic":false,"x":133,"y":152,"scale":1,"rot":0},{"key":"negotiation_book","cosmetic":false,"x":160,"y":151,"scale":1,"rot":0},{"key":"gaming_setup","cosmetic":false,"x":191,"y":151,"scale":1,"rot":0},{"key":"ergonomic_chair","cosmetic":false,"x":133,"y":181,"scale":1,"rot":0},{"key":"second_monitor","cosmetic":false,"x":165,"y":177,"scale":1,"rot":0},{"key":"printer","cosmetic":false,"x":197,"y":177,"scale":1,"rot":0},{"key":"workbench_tools","cosmetic":false,"x":25,"y":209,"scale":1,"rot":0},{"key":"home_gym","cosmetic":false,"x":61,"y":209,"scale":1,"rot":0},{"key":"motorcycle","cosmetic":false,"x":90,"y":216,"scale":1,"rot":0},{"key":"sports_car","cosmetic":false,"x":23,"y":258,"scale":1,"rot":0},{"key":"bbq_grill","cosmetic":false,"x":133,"y":209,"scale":1,"rot":0},{"key":"patio_set","cosmetic":false,"x":167,"y":214,"scale":1,"rot":0},{"key":"swimming_pool","cosmetic":false,"x":213,"y":213,"scale":1,"rot":0},{"key":"garden","cosmetic":false,"x":137,"y":246,"scale":1,"rot":0},{"key":"fire_pit","cosmetic":false,"x":172,"y":248,"scale":1,"rot":0},{"key":"basketball_hoop","cosmetic":false,"x":203,"y":245,"scale":1,"rot":0}]},"mansion":{"rooms":[{"key":"living","label":"Living","x":4,"y":4,"w":150,"h":96},{"key":"kitchen","label":"Kitchen","x":162,"y":4,"w":100,"h":66},{"key":"bedroom","label":"Bedroom","x":4,"y":108,"w":104,"h":78},{"key":"office","label":"Office","x":116,"y":108,"w":120,"h":76},{"key":"garage","label":"Garage","x":4,"y":194,"w":104,"h":86},{"key":"outdoor","label":"Patio","x":116,"y":194,"w":150,"h":78},{"key":"bath","label":"Bath","x":274,"y":194,"w":58,"h":58}],"furniture":[{"key":"house_plant","cosmetic":false,"x":22,"y":23,"scale":1,"rot":0},{"key":"couch","cosmetic":false,"x":63,"y":17,"scale":1,"rot":0},{"key":"flat_screen_tv","cosmetic":false,"x":110,"y":15,"scale":1,"rot":0},{"key":"home_theater","cosmetic":false,"x":31,"y":55,"scale":1,"rot":0},{"key":"bookshelf","cosmetic":false,"x":75,"y":52,"scale":1,"rot":0},{"key":"aquarium","cosmetic":false,"x":114,"y":53,"scale":1,"rot":0},{"key":"fireplace","cosmetic":false,"x":25,"y":82,"scale":1,"rot":0},{"key":"pool_table","cosmetic":false,"x":67,"y":85,"scale":1,"rot":0},{"key":"grand_piano","cosmetic":false,"x":111,"y":87,"scale":1,"rot":0},{"key":"smart_home_system","cosmetic":false,"x":20,"y":118,"scale":1,"rot":0},{"key":"home_bar","cosmetic":false,"x":56,"y":117,"scale":1,"rot":0},{"key":"art_gallery","cosmetic":false,"x":100,"y":114,"scale":1,"rot":0},{"key":"grand_fireplace","cosmetic":false,"x":28,"y":145,"scale":1,"rot":0},{"key":"coffee_maker","cosmetic":false,"x":175,"y":19,"scale":1,"rot":0},{"key":"mini_fridge","cosmetic":false,"x":199,"y":21,"scale":1,"rot":0},{"key":"espresso_machine","cosmetic":false,"x":227,"y":19,"scale":1,"rot":0},{"key":"wine_rack","cosmetic":false,"x":180,"y":51,"scale":1,"rot":0},{"key":"instant_pot","cosmetic":false,"x":210,"y":50,"scale":1,"rot":0},{"key":"kitchen_island","cosmetic":false,"x":183,"y":78,"scale":1,"rot":0},{"key":"smart_fridge","cosmetic":false,"x":216,"y":82,"scale":1,"rot":0},{"key":"new_bed","cosmetic":false,"x":25,"y":130,"scale":1,"rot":0},{"key":"blackout_curtains","cosmetic":false,"x":59,"y":120,"scale":1,"rot":0},{"key":"hot_tub","cosmetic":false,"x":23,"y":166,"scale":1,"rot":0},{"key":"meditation_corner","cosmetic":false,"x":54,"y":160,"scale":1,"rot":0},{"key":"sauna","cosmetic":false,"x":85,"y":165,"scale":1,"rot":0},{"key":"spa_suite","cosmetic":false,"x":25,"y":194,"scale":1,"rot":0},{"key":"luxury_sleep_system","cosmetic":false,"x":64,"y":201,"scale":1,"rot":0},{"key":"desk_fan","cosmetic":false,"x":130,"y":122,"scale":1,"rot":0},{"key":"whiteboard","cosmetic":false,"x":161,"y":121,"scale":1,"rot":0},{"key":"filing_cabinet","cosmetic":false,"x":193,"y":124,"scale":1,"rot":0},{"key":"headphones","cosmetic":false,"x":133,"y":152,"scale":1,"rot":0},{"key":"negotiation_book","cosmetic":false,"x":160,"y":151,"scale":1,"rot":0},{"key":"gaming_setup","cosmetic":false,"x":191,"y":151,"scale":1,"rot":0},{"key":"ergonomic_chair","cosmetic":false,"x":133,"y":181,"scale":1,"rot":0},{"key":"second_monitor","cosmetic":false,"x":165,"y":177,"scale":1,"rot":0},{"key":"printer","cosmetic":false,"x":197,"y":177,"scale":1,"rot":0},{"key":"music_studio","cosmetic":false,"x":137,"y":207,"scale":1,"rot":0},{"key":"workbench_tools","cosmetic":false,"x":25,"y":209,"scale":1,"rot":0},{"key":"home_gym","cosmetic":false,"x":61,"y":209,"scale":1,"rot":0},{"key":"motorcycle","cosmetic":false,"x":90,"y":216,"scale":1,"rot":0},{"key":"sports_car","cosmetic":false,"x":23,"y":258,"scale":1,"rot":0},{"key":"professional_gym","cosmetic":false,"x":57,"y":251,"scale":1,"rot":0},{"key":"bbq_grill","cosmetic":false,"x":133,"y":209,"scale":1,"rot":0},{"key":"patio_set","cosmetic":false,"x":167,"y":214,"scale":1,"rot":0},{"key":"swimming_pool","cosmetic":false,"x":213,"y":213,"scale":1,"rot":0},{"key":"garden","cosmetic":false,"x":137,"y":246,"scale":1,"rot":0},{"key":"fire_pit","cosmetic":false,"x":172,"y":248,"scale":1,"rot":0},{"key":"basketball_hoop","cosmetic":false,"x":203,"y":245,"scale":1,"rot":0},{"key":"indoor_pool","cosmetic":false,"x":145,"y":281,"scale":1,"rot":0}]}}');

function buildFloorPlanHtml() {
  const homeKey = state.player_home || 'grandmas_basement';
  const L = FP_LAYOUT[homeKey] || FP_LAYOUT.grandmas_basement;
  const owned = state.owned_items || {};

  // viewBox bounds = furthest room edge / sprite extent (+ small margin)
  let W = 0, Hh = 0;
  for (const r of L.rooms) { if (r.x + r.w > W) W = r.x + r.w; if (r.y + r.h > Hh) Hh = r.y + r.h; }
  for (const f of L.furniture) { const sp = FP_SPRITES[f.key]; if (!sp) continue; if (f.x + sp.w / 2 > W) W = f.x + sp.w / 2; if (f.y + sp.h / 2 > Hh) Hh = f.y + sp.h / 2; }
  W += 4; Hh += 4;

  let frames = '', floors = '', labels = '', furn = '';
  for (const r of L.rooms) {
    frames += `<rect x="${r.x - 2}" y="${r.y - 2}" width="${r.w + 4}" height="${r.h + 4}" rx="5" fill="#4A3A2C"/>`;
    floors += `<rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" fill="${FP_FLOOR[r.key] || '#B89469'}"/>`;
    labels += `<text x="${r.x + 4}" y="${r.y + 9}" font-size="6.5" fill="#241B12" opacity="0.5" style="font-family:system-ui,sans-serif;font-weight:600">${r.label || r.key}</text>`;
  }
  for (const f of L.furniture) {
    const sp = FP_SPRITES[f.key];
    if (!sp) continue;
    if (!f.cosmetic && !owned[f.key]) continue; // buyable item only shows once owned
    const t = `translate(${f.x},${f.y}) scale(${f.scale}) rotate(${f.rot || 0})`;
    furn += f.cosmetic
      ? `<g transform="${t}">${sp.art}</g>`
      : `<g transform="${t}" onclick="showOwnedItemDetail('${f.key}')" style="cursor:pointer">${sp.art}</g>`;
  }
  const K = 1.9, wpx = Math.round(W * K);
  return `<svg viewBox="0 0 ${W} ${Hh}" style="width:${wpx}px;max-width:100%;height:auto;display:block;margin:0 auto" xmlns="http://www.w3.org/2000/svg">`
       + `${frames}${floors}${furn}${labels}</svg>`;
}

function buildFloorPlanCard() {
  const ownedCount = STORE_ITEM_DATA.filter(i => (state.owned_items || {})[i.key]).length;
  const hint = ownedCount === 0
    ? `Buy furniture below and it appears here — tap any piece for details.`
    : `Tap any piece for details.`;
  return `
    <div class="hood-section" style="margin-bottom:10px;padding:14px">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:8px">Floor Plan</div>
      <div style="background:var(--surface-2);border-radius:10px;padding:12px 10px">${buildFloorPlanHtml()}</div>
      <div style="font-size:10px;color:var(--text-muted);margin-top:8px;text-align:center">${hint}</div>
    </div>`;
}

function buildMyHomeContent() {
  const homeKey     = state.player_home || 'grandmas_basement';
  const homeIdx     = HOME_TIER_ORDER.indexOf(homeKey);
  const ownedItems  = state.owned_items || {};
  const squatterBlocked = starterSquatterActive();

  // Floor plan canvas hidden for now — code intact, re-enable by restoring the svgHtml line in the return
  // const svgHtml = buildFloorPlanHtml();

  const byRoom = {};
  for (const item of STORE_ITEM_DATA) {
    const reqIdx = item.unlock_home ? HOME_TIER_ORDER.indexOf(item.unlock_home) : 0;
    if (homeIdx < reqIdx) continue;
    if (!byRoom[item.room]) byRoom[item.room] = [];
    byRoom[item.room].push(item);
  }

  const storeHtml = _ROOM_ORDER.filter(r => byRoom[r]).map(roomKey => {
    const rows = byRoom[roomKey].filter(item => !ownedItems[item.key]).map(item => {
      const owned       = false; // owned items are hidden from store — they appear on the home card
      const levelLocked = (state.level || 0) < (item.unlock_level || 0);
      const canAfford   = !owned && !levelLocked && !squatterBlocked && state.cash >= item.cost;

      let badge = '';
      if (owned)        badge = `<span style="background:var(--positive);color:#fff;border-radius:3px;font-size:10px;padding:1px 6px;font-weight:700">✓</span>`;
      else if (levelLocked) badge = `<span style="background:#555;color:#fff;border-radius:3px;font-size:10px;padding:1px 6px;font-weight:700">LVL ${item.unlock_level}</span>`;

      let btn = '';
      if (owned)             btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;opacity:0.4">Owned</button>`;
      else if (levelLocked)  btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Lvl ${item.unlock_level}</button>`;
      else if (squatterBlocked) btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">🚨 Later</button>`;
      else if (canAfford)    btn = `<button class="btn btn-primary btn-sm" onclick="buyStoreItem('${item.key}')" style="font-size:11px">Buy ${fmt(item.cost)}</button>`;
      else                   btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Need ${fmt(item.cost)}</button>`;

      return `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--border);${levelLocked?'opacity:0.55':''}">
          <div style="font-size:20px;line-height:1;flex-shrink:0">${item.icon}</div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
              <span style="font-size:12px;font-weight:800;font-family:'DotGothic16',monospace">${item.name}</span>${badge}
            </div>
            <div style="font-size:10px;color:var(--text-muted);margin-top:1px">${levelLocked ? `Unlocks at Level ${item.unlock_level}` : item.desc}</div>
            ${!levelLocked ? `<div style="font-size:10px;font-weight:700;color:var(--primary);margin-top:1px">${item.bonus}</div>` : ''}
          </div>
          <div style="flex-shrink:0">${btn}</div>
        </div>`;
    }).join('');

    if (!rows) return ''; // room fully furnished — skip the section header
    return `
      <div style="padding:6px 14px 3px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.10em;color:var(--text-muted);font-family:'DotGothic16',monospace;background:var(--surface-2)">
        ${_ROOM_LABELS[roomKey]}
      </div>
      ${rows}`;
  }).join('');

  const allFurnished = !storeHtml.trim();
  return allFurnished
    ? `<div style="padding:24px 16px;text-align:center;color:var(--text-muted);font-size:13px">${pxIcon('🏆',28)}<div style="margin-top:8px;font-weight:700">Fully Furnished</div><div style="font-size:11px;margin-top:4px">Your home is complete. Gerald is impressed.</div></div>`
    : storeHtml; // floor plan canvas re-enable: `<div style="padding:10px 14px 6px">${svgHtml}</div>${storeHtml}`
}

function buildOwnedItemsRow(ownedItems) {
  const items = STORE_ITEM_DATA.filter(i => ownedItems[i.key]);
  if (!items.length) return `
    <div style="margin-top:12px;padding:10px 12px;background:var(--surface-2);border-radius:8px;text-align:center;font-size:11px;color:var(--text-muted)">
      Nothing yet — open Furnishings below to get started.
    </div>`;
  return `
    <div style="margin-top:12px">
      <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted);margin-bottom:7px">What's In Your Place</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        ${items.map(item => `
          <button onclick="showOwnedItemDetail('${item.key}')"
            style="width:42px;height:42px;border-radius:10px;background:var(--surface-2);border:1.5px solid var(--border);font-size:21px;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;transition:transform 0.1s"
            onpointerdown="this.style.transform='scale(0.92)'" onpointerup="this.style.transform=''" onpointerleave="this.style.transform=''">
            ${item.icon}
          </button>`).join('')}
      </div>
    </div>`;
}

function showOwnedItemDetail(key) {
  const item = STORE_ITEM_DATA.find(i => i.key === key);
  if (!item) return;
  openModal(`
    <div class="modal-handle"></div>
    <div style="text-align:center;padding:24px 20px 8px">
      <div style="font-size:52px;margin-bottom:10px;line-height:1">${item.icon}</div>
      <div style="font-size:18px;font-weight:900;margin-bottom:8px">${item.name}</div>
      <div style="font-size:13px;color:var(--text-muted);line-height:1.6;margin-bottom:${item.bonus ? '10px' : '0'}">${item.desc}</div>
      ${item.bonus ? `<div style="display:inline-block;padding:5px 14px;background:var(--surface-2);border-radius:8px;font-size:12px;font-weight:700;color:var(--primary)">${item.bonus}</div>` : ''}
    </div>
    <div style="padding:16px">
      <button class="btn btn-ghost btn-full" onclick="closeModal()">Close</button>
    </div>`);
}

function buildMyHomeMeta() {
  const homeKey = state.player_home || 'grandmas_basement';
  const homeIdx = HOME_TIER_ORDER.indexOf(homeKey);
  const owned   = STORE_ITEM_DATA.filter(i => !!(state.owned_items || {})[i.key]).length;
  const avail   = STORE_ITEM_DATA.filter(i => {
    const ri = i.unlock_home ? HOME_TIER_ORDER.indexOf(i.unlock_home) : 0;
    return homeIdx >= ri;
  }).length;
  return `${owned}/${avail} furnished`;
}

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

let _personalOpen    = { my_home: false, homes: false, classes: false, store: false, newbuilds: false, assistants: false };
let _personalMainTab = 'home';

function switchPersonalTab(tab) {
  sfx.tab();
  _personalMainTab = tab;
  ['home', 'career'].forEach(t => {
    const el  = document.getElementById('personal-' + t);
    const btn = document.querySelector(`.fin-tab[data-personal="${t}"]`);
    if (el)  el.style.display = t === tab ? '' : 'none';
    if (btn) btn.classList.toggle('active', t === tab);
  });
  renderPersonal();
}

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

    const newItems = STORE_ITEM_DATA.filter(i => i.unlock_home === h.key).length;
    const statLine = idx === 0
      ? `Unlocks ${STORE_ITEM_DATA.filter(i => !i.unlock_home).length} starter items`
      : newItems > 0 ? `Unlocks ${newItems} new item${newItems !== 1 ? 's' : ''}` : 'Larger home';

    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);opacity:${opacity}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${(isUnlocked || isCurrent) ? homeModelImg(h.key, 40) : pxIcon('🔒')}</div>
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

  // ── New Builds rows (permit + crews) ──────────────────────────────
  const nbLevel     = NEW_BUILDS_UNLOCK_LEVEL;
  const nbUnlocked  = (state.level || 0) >= nbLevel;
  const hasPermit   = !!state.building_permit;
  const ownedCrews  = state.owned_crews || [];

  const permitRow = (() => {
    const locked   = !nbUnlocked;
    const canAfford = nbUnlocked && !hasPermit && state.cash >= 100000;
    let badge = '';
    if (hasPermit)      badge = `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">✓ Owned</span>`;
    else if (locked)    badge = `<span style="background:#555;color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">${pxIcon('🔒',12)} LVL ${nbLevel}</span>`;
    let btn = '';
    if (hasPermit)      btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;opacity:0.5">Owned</button>`;
    else if (locked)    btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Lvl ${nbLevel}</button>`;
    else if (canAfford) btn = `<button class="btn btn-primary btn-sm" onclick="buyBuildingPermit()" style="font-size:11px">Buy ${fmt(100000)}</button>`;
    else                btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Need ${fmt(100000)}</button>`;
    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);${hasPermit?'opacity:0.6':''}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(locked ? '🔒' : '📋')}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">Building Permit</span>${badge}
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${locked ? `Unlocks at Level ${nbLevel}` : 'One-time purchase. Required to start any new build in Cedarvale Estates.'}</div>
      </div>
      <div style="flex-shrink:0">${btn}</div>
    </div>`;
  })();

  const crewRows = Object.entries(BUILD_CREWS_DATA).map(([key, crew]) => {
    const locked    = !nbUnlocked || !hasPermit;
    const owned     = ownedCrews.includes(key);
    const canAfford = !locked && !owned && state.cash >= crew.buy_cost;
    let badge = '';
    if (owned)  badge = `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">✓ Hired</span>`;
    let btn = '';
    if (owned)          btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px;opacity:0.5">Hired</button>`;
    else if (locked)    btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">${hasPermit ? `Lvl ${nbLevel}` : 'Need Permit'}</button>`;
    else if (canAfford) btn = `<button class="btn btn-primary btn-sm" onclick="buyBuildCrew('${key}')" style="font-size:11px">Buy ${fmt(crew.buy_cost)}</button>`;
    else                btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Need ${fmt(crew.buy_cost)}</button>`;
    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);${owned?'opacity:0.6':''}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(locked && !owned ? '🔒' : crew.icon)}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">${crew.name}</span>${badge}
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${crew.desc}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;font-weight:700">${fmt(crew.daily_rate)}/day · ${Math.round((1 - crew.speed_mult) * 100)}% faster than baseline</div>
      </div>
      <div style="flex-shrink:0">${btn}</div>
    </div>`;
  }).join('');

  const nbContent   = permitRow + crewRows;
  const nbMeta      = !nbUnlocked ? `Unlocks at Lvl ${nbLevel}` : `${ownedCrews.length + (hasPermit ? 1 : 0)} / ${Object.keys(BUILD_CREWS_DATA).length + 1} owned`;

  const homesUnlocked = unlockedKeys.length;
  const classesCount  = Object.keys(diyClasses).length;

  // ── My Home tab ───────────────────────────────────────────────
  const homeTabEl = document.getElementById('personal-home');
  if (homeTabEl) {
    homeTabEl.innerHTML = `
      <div style="padding:12px;max-width:480px;margin:0 auto">

        <div class="hood-section" style="margin-bottom:10px">
          <div style="padding:14px">
            <div style="display:flex;align-items:center;gap:14px">
              <div style="flex-shrink:0">${homeModelImg(homeKey, 54)}</div>
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
            ${buildOwnedItemsRow(ownedItems)}
          </div>
        </div>

        ${buildFloorPlanCard()}

        ${personalSection('my_home', `${pxIcon('🛋️',16)} Furnishings`,   buildMyHomeContent(), buildMyHomeMeta())}
        ${personalSection('homes',   `${pxIcon('🏠',16)} Home Upgrades`, homeRows, `${homesUnlocked}/${PLAYER_HOME_DATA.length} unlocked`)}

      </div>`;
  }

  // ── Career tab ────────────────────────────────────────────────
  const careerTabEl = document.getElementById('personal-career');
  if (careerTabEl) {
    careerTabEl.innerHTML = `
      <div style="padding:12px;max-width:480px;margin:0 auto">
        ${personalSection('classes',    `${pxIcon('📚',16)} Skill Classes`, classRows,            `${classesCount}/${DIY_CLASS_DATA.length} done`)}
        ${personalSection('newbuilds',  `${pxIcon('🏗️',16)} New Builds`,    nbContent,            nbMeta)}
        ${personalSection('assistants', `${pxIcon('👔',16)} Assistants`,    buildAssistantRows(), buildAssistantMeta())}
      </div>`;
  }

  // requestAnimationFrame(_drawFloorPlan); // re-enable with floor plan canvas
}

function buildAssistantMeta() {
  const hired = Object.keys(ASSISTANTS_DATA).filter(k => (state.assistants || {})[k]).length;
  return `${hired}/${Object.keys(ASSISTANTS_DATA).length} hired`;
}

function buildAssistantRows() {
  const level     = state.level || 0;
  const assistants = state.assistants || {};
  return Object.entries(ASSISTANTS_DATA).map(([key, asst]) => {
    const hired      = !!assistants[key];
    const locked     = level < asst.unlock_level;
    const opacity    = hired ? '0.7' : locked ? '0.4' : '1';
    let badge = '';
    if (hired)       badge = `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">✓ Hired</span>`;
    else if (locked) badge = `<span style="background:#555;color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700">${pxIcon('🔒',12)} LVL ${asst.unlock_level}</span>`;
    let btn = '';
    if (hired) {
      btn = `<button class="btn btn-ghost btn-sm" style="font-size:11px;color:var(--negative)" onclick="fireAssistant('${key}')">Fire</button>`;
    } else if (locked) {
      btn = `<button class="btn btn-ghost btn-sm" disabled style="font-size:11px">Lvl ${asst.unlock_level}</button>`;
    } else {
      btn = `<button class="btn btn-primary btn-sm" style="font-size:11px" onclick="hireAssistant('${key}')">Hire</button>`;
    }
    return `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);opacity:${opacity}">
      <div style="font-size:22px;line-height:1;flex-shrink:0">${pxIcon(locked ? '🔒' : asst.icon)}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span style="font-size:13px;font-weight:800">${asst.name}</span>${badge}
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.4">${locked ? `Unlocks at Level ${asst.unlock_level}` : asst.desc}</div>
        <div style="font-size:10px;font-weight:700;color:var(--negative);margin-top:3px">${fmt(asst.monthly_fee)}/mo</div>
      </div>
      <div style="flex-shrink:0">${btn}</div>
    </div>`;
  }).join('');
}

async function hireAssistant(key) {
  const res = await api('/hire_assistant', 'POST', { key });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.hire();
  await refreshState();
  renderPersonal();
  toast(`${ASSISTANTS_DATA[key].icon} ${ASSISTANTS_DATA[key].name} hired!`, 'success');
}

async function fireAssistant(key) {
  const res = await api('/fire_assistant', 'POST', { key });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderPersonal();
  toast(`${ASSISTANTS_DATA[key].name} dismissed.`, 'info');
}

function togglePersonalSection(id) {
  sfx.accordion();
  _personalOpen[id] = !_personalOpen[id];
  renderPersonal();
}

async function buyStoreItem(itemKey) {
  const res = await api('/store/buy_item', 'POST', { item_key: itemKey });
  if (res.error) { toast(res.error, 'warning'); return; }
  sfx.purchase();
  await refreshState();
  renderPersonal();
  toast(`${res.item} purchased!`);
}

async function buyDiyClass(classKey) {
  const res = await api('/education/buy_class', 'POST', { class_key: classKey });
  if (res.error) { toast(res.error, 'warning'); return; }
  sfx.purchase();
  await refreshState();
  renderPersonal();
  toast(`${res.class_name} completed! New DIY skills unlocked.`);
}

async function buyBuildingPermit() {
  const res = await api('/new_builds/buy_permit', 'POST');
  if (res.error) { toast(res.error, 'warning'); return; }
  sfx.purchase();
  await refreshState();
  renderPersonal();
  toast('Building permit purchased! Head to My Properties → New Builds to start.', 'success');
}

async function buyBuildCrew(crewKey) {
  const res = await api('/new_builds/buy_crew', 'POST', { crew: crewKey });
  if (res.error) { toast(res.error, 'warning'); return; }
  sfx.hire();
  await refreshState();
  renderPersonal();
  toast(`${BUILD_CREWS_DATA[crewKey].name} hired!`, 'success');
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
      <div class="prop-icon-circle prop-icon-${tier}">${propModelImg(p)}</div>
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
  sfx.propOpen();
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
      <span style="flex-shrink:0">${propModelImg(prop, 60)}</span>
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
  sfx.specialReno();
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
  sfx.specialReno();
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
      sfx.evict();
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
  sfx.findTenant();
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
      </div>` : regularTenantCard(t, id, _fairRent)).join('')}
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
  sfx.signLease();
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
  sfx.propOpen();
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
  sfx.construct();
  _mg = { isRepair: false };
  launchMgByType(selectMgType(upgradeKey), upgradeKey);
}

async function finishDIY(upgradeKey, score) {
  sfx.complete();
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
  if (contractorKey === 'special') sfx.specialReno(); else sfx.construct();
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
const VM_PRICES        = [1200, 2000, 3000, 4200, 5800, 8000];
const VM_SLOT_CAPACITY = 60;
const VM_PRODUCTS = {
  snacks:    { name: 'Snacks',      icon: '🍫', price: 2.25 },
  cold:      { name: 'Cold Drinks', icon: '🥤', price: 2.75 },
  hot:       { name: 'Hot Drinks',  icon: '☕', price: 3.00, perishable: true },
  energy:    { name: 'Energy',      icon: '⚡', price: 3.75 },
  fresh:     { name: 'Fresh Food',  icon: '🥗', price: 6.50, perishable: true },
  specialty: { name: 'Specialty',   icon: '🎁', price: 4.75 },
};
const VM_LOCATION_ORDER = ['midtown_grocery', 'downtown_bus', 'westwood_office',
                           'northside_center', 'newbay_ferry', 'riverside_park'];
const VM_LOCATIONS = {
  midtown_grocery:  { name: 'Midtown Grocery Entrance',  profile: { snacks:.25, cold:.25, fresh:.20, specialty:.15, energy:.10, hot:.05 } },
  downtown_bus:     { name: 'Downtown Bus Station',       profile: { snacks:.35, cold:.30, energy:.20, hot:.10, specialty:.05 } },
  westwood_office:  { name: 'Westwood Office Lobby',      profile: { hot:.30, energy:.25, cold:.20, snacks:.15, specialty:.10 } },
  northside_center: { name: 'Northside Community Center', profile: { energy:.30, snacks:.30, cold:.20, hot:.10, specialty:.10 } },
  newbay_ferry:     { name: 'Newbay Ferry Terminal',      profile: { cold:.30, snacks:.25, specialty:.20, fresh:.15, hot:.10 } },
  riverside_park:   { name: 'Riverside Park',             profile: { cold:.40, snacks:.30, energy:.15, fresh:.10, specialty:.05 } },
  laundromat:       { name: 'Your Laundromat',            profile: { snacks:.35, cold:.30, energy:.15, hot:.10, specialty:.10 } },
  arcade:           { name: 'The Arcade Floor',           profile: { energy:.35, cold:.25, snacks:.25, specialty:.10, hot:.05 } },
};
const VM_CAT_COLOR = {
  snacks: '#D98E3C', cold: '#3FA7D6', hot: '#B5651D',
  energy: '#E8B92E', fresh: '#4CAF50', specialty: '#9C5BD6',
};
const VM_PRICE_LEVELS = [
  { key: 'value',   name: 'Value',   icon: '🏷️' },
  { key: 'normal',  name: 'Normal',  icon: '⚖️' },
  { key: 'premium', name: 'Premium', icon: '💎' },
];
const VM_UPGRADES_META = [
  { key: 'capacity',    name: 'Bigger Capacity',  icon: '📦', cost: 1500, desc: 'Slot capacity 60 → 90. Slots last far longer.' },
  { key: 'fridge',      name: 'Refrigeration',    icon: '❄️', cost: 2000, desc: 'Perishables last +2 days before spoiling.' },
  { key: 'card_reader', name: 'Card Reader',      icon: '💳', cost: 1200, desc: '+12% units sold.' },
  { key: 'branding',    name: 'Branding Wrap',    icon: '🎨', cost: 1000, desc: 'Reputation climbs faster.' },
  { key: 'reinforced',  name: 'Reinforced Build', icon: '🛡️', cost: 1800, desc: 'Halves bad location events.' },
];
function vmCapacity(vm) { return (vm.upgrades && vm.upgrades.capacity) ? 90 : 60; }
function repColor(r) { return r >= 75 ? 'var(--positive)' : r >= 45 ? 'var(--warning)' : 'var(--negative)'; }

let _bizOpen = {};   // all business windows start closed

function toggleBiz(id) {
  sfx.accordion();
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
    { id: 'vending',      name: 'Vending Machine Entrepreneur', unlockLevel: 3,  icon: 'svg:business-vending', content: renderVendingContent     },
    { id: 'laundromat',   name: 'Dirty Money Laundromat',       unlockLevel: 5,  icon: 'svg:business-laundromat', content: renderLaundromContent    },
    { id: 'arcade',       name: 'The Back-Room Arcade',         secret: true,    icon: '🕹️',              content: renderArcadeContent, tagline: 'Behind the laundromat' },
    { id: 'pole_studio',  name: 'Brass Pole Fitness Studio',    unlockLevel: 8,  icon: '💃',              content: renderPoleStudioContent  },
    { id: 'car_wash',     name: 'Slippery When Washed',         unlockLevel: 10, icon: '🚗',              content: renderCarWashContent     },
  ];

  const cards = bizDefs.map(biz => {
    // Secret businesses stay completely hidden until unlocked (no locked placeholder).
    if (biz.secret) {
      if (!(state.arcade && state.arcade.unlocked)) return '';
    } else {
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
    }
    const isOpen  = !!_bizOpen[biz.id];
    const iconImg = biz.icon
      ? (biz.icon.startsWith('svg:')
          ? `<img src="/static/icons/${biz.icon.slice(4)}.svg" width="28" height="28" style="vertical-align:middle;image-rendering:pixelated">`
          : `<span style="font-size:22px;line-height:1">${biz.icon}</span>`)
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
            <div style="font-size:11px;color:${mutedColor}">${biz.tagline || `Level ${biz.unlockLevel} Business`}</div>
          </div>
          <div style="font-size:11px;color:${mutedColor}">${isOpen ? '▲' : '▼'}</div>
        </div>
        ${isOpen ? `<div style="padding:0 14px 14px;border-top:2px solid var(--primary)">${inner}</div>` : ''}
      </div>`;
  }).join('');

  el.innerHTML = `<div class="section-header"><span class="section-title">💼 My Businesses</span></div>${cards}`;
}

function vinnyIcon() {
  return `<svg viewBox='0 0 44 56' xmlns='http://www.w3.org/2000/svg' width='48' height='61' style='flex-shrink:0;display:block'>
    <path d='M5 26 Q6 7 22 5 Q38 7 39 26' fill='#1A0800'/>
    <path d='M18 14 Q22 19 26 14 Q24 10 22 9 Q20 10 18 14 Z' fill='#1A0800'/>
    <circle cx='5' cy='28' r='3.5' fill='#C8955A'/>
    <circle cx='39' cy='28' r='3.5' fill='#C8955A'/>
    <circle cx='22' cy='27' r='17' fill='#C8955A'/>
    <ellipse cx='15' cy='25' rx='4.2' ry='2.8' fill='white'/>
    <ellipse cx='29' cy='25' rx='4.2' ry='2.8' fill='white'/>
    <circle cx='16' cy='25.5' r='2.3' fill='#2A1400'/>
    <circle cx='30' cy='25.5' r='2.3' fill='#2A1400'/>
    <circle cx='16.5' cy='25.2' r='1.1' fill='#0A0400'/>
    <circle cx='30.5' cy='25.2' r='1.1' fill='#0A0400'/>
    <circle cx='17' cy='24.8' r='0.5' fill='white'/>
    <circle cx='31' cy='24.8' r='0.5' fill='white'/>
    <path d='M11 20.5 Q15.5 17.5 19.5 20' stroke='#1A0800' stroke-width='2.8' fill='none' stroke-linecap='round'/>
    <path d='M24.5 20 Q28.5 17.5 33 20.5' stroke='#1A0800' stroke-width='2.8' fill='none' stroke-linecap='round'/>
    <path d='M10.5 23 Q15 21.5 19.5 23' stroke='#9A6840' stroke-width='1.2' fill='none'/>
    <path d='M24.5 23 Q29 21.5 33.5 23' stroke='#9A6840' stroke-width='1.2' fill='none'/>
    <path d='M19 28 Q21 26 20 30 Q21.5 33 22 33 Q22.5 33 24 30 Q23 26 25 28' fill='#B07840'/>
    <ellipse cx='20.5' cy='32.5' rx='1.8' ry='1' fill='#9A5828'/>
    <ellipse cx='23.5' cy='32.5' rx='1.8' ry='1' fill='#9A5828'/>
    <path d='M16 37 Q22 35.5 28 37' stroke='#7A3A18' stroke-width='1.8' fill='none' stroke-linecap='round'/>
    <circle cx='17' cy='38.5' r='0.5' fill='#6A3010' opacity='0.8'/>
    <circle cx='19' cy='39.2' r='0.5' fill='#6A3010' opacity='0.8'/>
    <circle cx='22' cy='39.5' r='0.5' fill='#6A3010' opacity='0.8'/>
    <circle cx='25' cy='39.2' r='0.5' fill='#6A3010' opacity='0.8'/>
    <circle cx='27' cy='38.5' r='0.5' fill='#6A3010' opacity='0.8'/>
    <rect x='18' y='44' width='8' height='7' rx='2' fill='#C8955A'/>
    <path d='M2 56 Q3 47 10 45 Q17 43 22 43 Q27 43 34 45 Q41 47 42 56 Z' fill='#8B0000'/>
    <path d='M10 45 Q17 43 22 53 Q27 43 34 45 L33 47 Q27 45 22 55 Q17 45 11 47 Z' fill='#C62828'/>
    <path d='M17 43 Q22 53 27 43' fill='#C8955A'/>
    <line x1='20' y1='50' x2='21.5' y2='53.5' stroke='#8A4820' stroke-width='0.8' opacity='0.7'/>
    <line x1='22' y1='49.5' x2='23' y2='53.5' stroke='#8A4820' stroke-width='0.8' opacity='0.7'/>
    <line x1='24' y1='50' x2='22.5' y2='54' stroke='#8A4820' stroke-width='0.8' opacity='0.7'/>
    <path d='M17 43 Q22 51 27 43' stroke='#D4A017' stroke-width='2' fill='none' stroke-linecap='round'/>
    <circle cx='22' cy='51' r='1.2' fill='#D4A017'/>
  </svg>`;
}

function renderVendingContent() {
  const vms   = state.vending_machines || [];
  const inv   = state.costpro_inventory || {};
  const vinny = state.vinny_hired || false;

  const totalUnits = Object.keys(VM_PRODUCTS).reduce((a, c) => a + (inv[c] || 0), 0);
  const invBadges  = Object.keys(VM_PRODUCTS).filter(c => (inv[c] || 0) > 0)
    .map(c => `<span style="background:var(--surface,var(--card-bg));border:1px solid var(--border);padding:2px 7px;font-size:10px;white-space:nowrap">${VM_PRODUCTS[c].icon} ${Math.round(inv[c])}</span>`)
    .join('');
  const invBar = `
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:10px 0;font-size:12px">
      ${pxIcon('🎒', 16)}
      ${totalUnits > 0 ? invBadges : `<span style="color:var(--warning);font-size:11px">No stock — <span style="text-decoration:underline;cursor:pointer" onclick="navTo('store')">visit CostPro</span></span>`}
    </div>`;

  const vmCards = vms.map(vm => {
    const loc   = VM_LOCATIONS[vm.location_key] || { name: '?', profile: {} };
    const chips = Object.entries(loc.profile).sort((a, b) => b[1] - a[1])
      .map(([c, w]) => {
        const col = VM_CAT_COLOR[c] || 'var(--text-muted)';
        return `<span style="font-size:10px;background:var(--surface,var(--card-bg));border:1px solid var(--border);border-radius:11px;padding:2px 9px;white-space:nowrap;display:inline-flex;align-items:center;gap:3px"><span style="color:${col}">${VM_PRODUCTS[c].icon}</span>${Math.round(w * 100)}%</span>`;
      }).join('');
    const cap = vmCapacity(vm);
    const slotCells = (vm.slots || []).map((sl, i) => {
      if (!sl.category) {
        return `<div onclick="showConfigureSlot(${vm.id},${i})" style="border:1.5px dashed var(--border);border-radius:9px;cursor:pointer;color:var(--text-muted);min-height:74px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px">
          <div style="font-size:18px;opacity:0.45">➕</div>
          <div style="font-size:10px">Assign</div>
        </div>`;
      }
      const p      = VM_PRODUCTS[sl.category];
      const pct    = Math.max(0, Math.min(100, Math.round((sl.stock / cap) * 100)));
      const col    = pct > 50 ? 'var(--positive)' : pct > 20 ? 'var(--warning)' : 'var(--negative)';
      const accent = VM_CAT_COLOR[sl.category] || 'var(--border)';
      const matched = loc.profile[sl.category] > 0;
      return `<div onclick="showConfigureSlot(${vm.id},${i})" style="border:1.5px solid ${matched ? accent : 'var(--negative)'};border-radius:9px;padding:8px 8px 6px;cursor:pointer;min-height:74px;background:linear-gradient(160deg, ${accent}1f, transparent 70%)">
        <div style="display:flex;align-items:center;gap:4px;font-size:11px;font-weight:800;line-height:1.1">
          <span style="font-size:15px">${p.icon}</span>
          <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.name}</span>
          ${matched ? '' : '<span title="No demand at this location" style="margin-left:auto">⚠️</span>'}
        </div>
        <div style="background:var(--border);height:6px;width:100%;border-radius:3px;margin:8px 0 4px">
          <div style="background:${col};height:6px;border-radius:3px;width:${pct}%"></div>
        </div>
        <div style="font-size:10px;color:var(--text-muted);text-align:right">${Math.round(sl.stock)}/${cap}</div>
      </div>`;
    }).join('');
    const stockedCount = (vm.slots || []).filter(sl => sl.category).length;
    const rep   = Math.round(vm.reputation != null ? vm.reputation : 70);
    const plvl  = vm.price_level || 'normal';
    const priceToggle = VM_PRICE_LEVELS.map(pl => {
      const active = pl.key === plvl;
      return `<button onclick="setVmPrice(${vm.id},'${pl.key}')" style="flex:1;font-size:10px;font-weight:700;padding:5px 2px;border:1px solid ${active ? 'var(--primary)' : 'var(--border)'};border-radius:7px;cursor:pointer;background:${active ? 'var(--primary)' : 'transparent'};color:${active ? '#fff' : 'var(--text-muted)'}">${pl.icon} ${pl.name}</button>`;
    }).join('');
    const upCount = VM_UPGRADES_META.filter(u => (vm.upgrades || {})[u.key]).length;
    const upIcons = VM_UPGRADES_META.filter(u => (vm.upgrades || {})[u.key]).map(u => u.icon).join(' ');
    return `
      <div style="border:1px solid var(--border);border-radius:12px;margin-top:10px;padding:12px;overflow:hidden">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px">
          <img src="/static/icons/business-vending.svg" width="32" height="32" style="flex-shrink:0;image-rendering:pixelated">
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">${loc.name}${upIcons ? ` <span style="font-size:11px">${upIcons}</span>` : ''}</div>
            <div style="font-size:11px;color:var(--text-muted)">📍 Machine #${vm.slot}</div>
          </div>
          <span style="font-size:10px;font-weight:700;color:var(--text-muted);background:var(--surface,var(--card-bg));border:1px solid var(--border);border-radius:10px;padding:2px 9px;white-space:nowrap">${stockedCount}/6 slots</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:10px">
          <span style="font-size:10px;color:var(--text-muted);white-space:nowrap">⭐ Reputation</span>
          <div style="flex:1;background:var(--border);height:7px;border-radius:4px"><div style="background:${repColor(rep)};height:7px;border-radius:4px;width:${rep}%"></div></div>
          <span style="font-size:11px;font-weight:800;color:${repColor(rep)}">${rep}</span>
        </div>
        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:5px">This spot wants</div>
        <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:11px">${chips}</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px">${slotCells}</div>
        <div style="display:flex;gap:6px;margin-top:10px">
          <span style="font-size:10px;color:var(--text-muted);align-self:center;white-space:nowrap">Pricing:</span>
          ${priceToggle}
        </div>
        <div style="display:flex;gap:6px;margin-top:9px">
          <button class="btn btn-primary btn-sm" style="flex:2" onclick="restockVending(${vm.id})">${pxIcon('📦',14)} Restock All</button>
          <button class="btn btn-ghost btn-sm" style="flex:1" onclick="showVmUpgrades(${vm.id})">🔧 ${upCount}/5</button>
        </div>
      </div>`;
  }).join('');

  const marketCount = vms.filter(v => VM_LOCATION_ORDER.includes(v.location_key)).length;
  const nextSlot  = marketCount + 1;
  const buyBtn    = nextSlot <= 6
    ? `<button class="btn btn-primary btn-full" style="margin-top:14px" onclick="showBuyVendingModal()">
         Buy Vending Machine #${nextSlot} — ${fmt(VM_PRICES[nextSlot - 1])}
       </button>`
    : `<div style="text-align:center;font-size:12px;color:var(--text-muted);margin-top:12px;opacity:0.6">All 6 market machines owned!</div>`;

  const vinnyCard = vms.length > 0 ? `
    <div style="display:flex;align-items:flex-start;gap:12px;padding:12px;border:1px solid var(--border);margin-top:14px">
      ${vinnyIcon()}
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

  const grandma   = state.grandma_hired || false;
  const budget    = state.grandma_budget || 0;
  const grandmaCard = vms.length > 0 ? `
    <div style="display:flex;align-items:flex-start;gap:12px;padding:12px;border:1px solid var(--border);border-radius:10px;margin-top:10px">
      <div style="font-size:30px;flex-shrink:0">🧺</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800">Grandma's Weekly Shop</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.5">Buys product for your configured slots once a week — at an 18% markup ("she doesn't haggle"). Pair with Vinny for hands-off income. Buying it yourself is still cheaper.</div>
        <div style="font-size:11px;margin-top:5px;color:${grandma ? 'var(--positive)' : 'var(--text-muted)'}">${grandma ? '🟢 Doing the shopping' : '⚫ Not hired'}</div>
        ${grandma ? `<div style="font-size:11px;color:var(--text-muted);margin-top:6px">Weekly budget cap: <strong>${budget > 0 ? fmt(budget) : 'none'}</strong>
          <span style="display:inline-flex;gap:4px;margin-left:6px">
            <button class="btn btn-ghost btn-sm" style="font-size:10px;padding:2px 7px" onclick="setGrandmaBudget(0)">None</button>
            <button class="btn btn-ghost btn-sm" style="font-size:10px;padding:2px 7px" onclick="setGrandmaBudget(1000)">$1k</button>
            <button class="btn btn-ghost btn-sm" style="font-size:10px;padding:2px 7px" onclick="setGrandmaBudget(3000)">$3k</button>
          </span></div>` : ''}
        <button class="btn btn-sm ${grandma ? 'btn-ghost' : 'btn-primary'}" style="margin-top:8px;width:100%" onclick="toggleGrandma()">
          ${grandma ? 'Thank Grandma (stop)' : 'Send Grandma shopping'}
        </button>
      </div>
    </div>` : '';

  const empty = vms.length === 0
    ? `<div style="text-align:center;color:var(--text-muted);font-size:12px;padding:14px 0">No machines yet. Buy your first one below!</div>` : '';

  return `${invBar}${vmCards}${empty}${buyBtn}${vinnyCard}${grandmaCard}`;
}

// ── Dirty Money Laundromat ────────────────────────────────────────────────────
const LAUNDROMAT_MAX_MACHINES    = 16;
const LAUNDROMAT_MACHINE_STEP    = 2500;   // price escalation per machine past the starters
const LAUNDROMAT_MACHINE_TYPES = {
  washer: { name: 'Washer', icon: '🌀', wash: 12, dry: 0,  price: 15000 },
  dryer:  { name: 'Dryer',  icon: '💨', wash: 0,  dry: 12, price: 15000 },
  combo:  { name: 'Combo Unit', icon: '🔄', wash: 16, dry: 16, price: 40000 },
};
const LM_BASE_DEMAND = 16, LM_DEM_REG = 0.40, LM_DEM_MEM = 0.50;
const LAUNDROMAT_ADDONS_META = [
  { key: 'vending',   name: 'In-House Vending',    icon: '🥤', cost: 4000, desc: 'Adds a 7th vending machine you stock from the Vending tab.' },
  { key: 'arcade',    name: 'Back-Room Arcade',    icon: '🕹️', cost: 20000, desc: 'Open the back room to the public — unlocks a whole new Arcade business.' },
  { key: 'atm',       name: 'ATM',                 icon: '🏧', cost: 3500, desc: 'Fee income that scales with traffic.' },
  { key: 'detergent', name: 'Detergent Vending',   icon: '🧴', cost: 3000, desc: '+$50/day selling supplies on-site.' },
  { key: 'wash_fold', name: 'Wash & Fold Service', icon: '🧺', cost: 6500, desc: 'Monetizes spare machine capacity.' },
  { key: 'loyalty',   name: 'Loyalty Program',     icon: '💳', cost: 4500, desc: 'Turns regulars into paying members.' },
];
function lmCapacity(machines, stage) {
  return (machines || []).filter(m => m.status === 'working').reduce((a, m) =>
    a + (LAUNDROMAT_MACHINE_TYPES[m.type || 'combo']?.[stage] || 0) * (m.upgrades?.card_reader ? 1.2 : 1), 0);
}

const LAUNDROMAT_UPGRADES_META = [
  { key: 'heavy_duty',       name: 'Heavy-Duty Motor',  icon: '⚙️',  cost: 2000, desc: 'Breakdown chance 6% → 2%.' },
  { key: 'card_reader',      name: 'Card Reader',        icon: '💳', cost: 1500, desc: '+20% income from this machine.' },
  { key: 'energy_efficient', name: 'Energy Efficient',   icon: '🌿', cost: 1000, desc: 'Soap lasts 10 days instead of 7.' },
];

const LAUNDROMAT_STAFF_META = {
  janitor:   { name: 'Janitor',   icon: '🧹', cost: 175, desc: 'Auto-cleans when cleanliness drops below 75%.' },
  repairman: { name: 'Repairman', icon: '🔧', cost: 225, desc: 'Auto-fixes broken machines every day.' },
  manager:   { name: 'Supply Manager', icon: '📦', cost: 200, desc: 'Auto-orders soap, softener & dryer sheets — keeps you stocked to a buffer.' },
};
const LAUNDROMAT_START_MACHINES = 4;

function laundryMachineIcon(type, isBroken, isRunning, id) {
  type = type || 'combo';
  const led = isBroken ? '#F44336' : isRunning ? '#4CAF50' : '#607D8B';
  const run = isRunning && !isBroken;
  const panel = `
    <rect x="0" y="0" width="20" height="5" fill="#607D8B"/>
    <circle cx="2.5" cy="2.5" r="1.2" fill="${led}"/>
    <rect x="5" y="1.5" width="1.5" height="2" fill="#455A64"/>
    <rect x="7.5" y="1.5" width="1.5" height="2" fill="#455A64"/>
    <rect x="10" y="1.5" width="1.5" height="2" fill="#455A64"/>
    <circle cx="15" cy="2.5" r="1.8" fill="#455A64"/>
    <rect x="14.6" y="0.8" width="0.8" height="1" fill="#B0BEC5"/>`;
  const body = `
    <rect x="0" y="5" width="20" height="16" fill="#FAFAFA"/>
    <rect x="0" y="5" width="1" height="16" fill="#CFD8DC"/>
    <rect x="19" y="5" width="1" height="16" fill="#CFD8DC"/>`;
  const feet = `
    <rect x="0" y="21" width="20" height="3" fill="#607D8B"/>
    <rect x="3" y="22" width="2" height="1" fill="#455A64"/>
    <rect x="8" y="22" width="2" height="1" fill="#455A64"/>`;
  const wrap = inner => `<svg viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" width="38" height="46" style="display:block;margin:0 auto">${panel}${body}${inner}${feet}</svg>`;

  if (type === 'dryer') {
    // Warm brass door, heat coil, tumbling, lint vent grille at the bottom.
    const glass = isBroken ? '#1A1A1A' : run ? '#FFB74D' : '#ECEFF1';
    const tumble = run
      ? `<defs><clipPath id="lm-d-${id}"><circle cx="10" cy="11" r="4.4"/></clipPath></defs>
         <g clip-path="url(#lm-d-${id})"><animateTransform attributeName="transform" type="rotate" from="0 10 11" to="360 10 11" dur="2.4s" repeatCount="indefinite"/>
           <rect x="7.6" y="9" width="2.5" height="2" rx="0.4" fill="#EF5350"/><rect x="10.2" y="10.8" width="2.3" height="1.7" rx="0.4" fill="#42A5F5"/><rect x="8" y="12.4" width="1.9" height="1.9" rx="0.4" fill="#FFEE58"/></g>`
      : `<circle cx="10" cy="11" r="2.2" fill="#CFD8DC" opacity="0.6"/>`;
    return wrap(`
      <circle cx="10" cy="11" r="6" fill="#8D6E63"/>
      <circle cx="10" cy="11" r="5.2" fill="#4E342E"/>
      <circle cx="10" cy="11" r="4.4" fill="${glass}"/>
      ${tumble}
      <path d="M5.8 11 A4.2 4.2 0 0 1 14.2 11" fill="none" stroke="#FF8A65" stroke-width="0.6" opacity="${run ? '0.85' : '0'}"/>
      <circle cx="7.8" cy="9.2" r="1" fill="white" opacity="0.3"/>
      <rect x="3" y="17.3" width="14" height="2.7" rx="0.5" fill="#ECEFF1"/>
      <rect x="4" y="18" width="12" height="0.6" fill="#B0BEC5"/><rect x="4" y="19" width="12" height="0.6" fill="#B0BEC5"/>`);
  }
  if (type === 'combo') {
    // Stacked unit: small warm dryer on top, blue washer below.
    const top = isBroken ? '#1A1A1A' : run ? '#FFB74D' : '#ECEFF1';
    const bot = isBroken ? '#1A1A1A' : run ? '#81D4FA' : '#ECEFF1';
    const spin = run
      ? `<defs><clipPath id="lm-c-${id}"><circle cx="10" cy="16" r="2.6"/></clipPath></defs>
         <g clip-path="url(#lm-c-${id})"><animateTransform attributeName="transform" type="rotate" from="0 10 16" to="360 10 16" dur="1.8s" repeatCount="indefinite"/>
           <rect x="8.2" y="14.6" width="1.8" height="1.5" rx="0.3" fill="#FF7043"/><rect x="10" y="16" width="1.7" height="1.3" rx="0.3" fill="#26A69A"/></g>`
      : '';
    return wrap(`
      <rect x="2.5" y="6.4" width="15" height="0.5" fill="#CFD8DC"/>
      <circle cx="10" cy="9.6" r="3.3" fill="#8D6E63"/><circle cx="10" cy="9.6" r="2.6" fill="#4E342E"/><circle cx="10" cy="9.6" r="2.1" fill="${top}"/>
      <rect x="3" y="12.7" width="14" height="0.5" fill="#CFD8DC"/>
      <circle cx="10" cy="16" r="3.5" fill="#546E7A"/><circle cx="10" cy="16" r="2.8" fill="#37474F"/><circle cx="10" cy="16" r="2.3" fill="${bot}"/>
      ${spin}
      <circle cx="8.8" cy="8.7" r="0.6" fill="white" opacity="0.3"/>`);
  }
  // washer (default): round steel door, blue glass, spinning clothes.
  const glass = isBroken ? '#1A1A1A' : run ? '#81D4FA' : '#ECEFF1';
  const spin = run
    ? `<defs><clipPath id="lm-w-${id}"><circle cx="10" cy="12" r="5"/></clipPath></defs>
       <g clip-path="url(#lm-w-${id})"><animateTransform attributeName="transform" type="rotate" from="0 10 12" to="360 10 12" dur="1.8s" repeatCount="indefinite"/>
         <rect x="7" y="9.5" width="2.8" height="2.2" rx="0.4" fill="#FF7043"/><rect x="10.5" y="11.5" width="2.8" height="2" rx="0.4" fill="#26A69A"/><rect x="7.5" y="13.5" width="2.2" height="2.2" rx="0.4" fill="#FFF176"/></g>`
    : `<circle cx="10" cy="12" r="2.5" fill="#CFD8DC" opacity="0.6"/>`;
  return wrap(`
    <circle cx="10" cy="12" r="6.5" fill="#546E7A"/>
    <circle cx="10" cy="12" r="5.8" fill="#37474F"/>
    <circle cx="10" cy="12" r="5" fill="${glass}"/>
    ${spin}
    <circle cx="8" cy="10" r="1.3" fill="white" opacity="0.35"/>
    <rect x="15.5" y="11.5" width="1" height="1" fill="#B0BEC5"/><rect x="15.5" y="13" width="1" height="1" fill="#B0BEC5"/>`);
}

function renderLaundromContent() {
  const lm = state.laundromat;

  if (!lm) {
    const canAfford = state.cash >= 250000;
    return `
      <div style="text-align:center;padding:16px 0">
        <div style="font-size:52px;line-height:1;margin-bottom:10px">🌀</div>
        <div style="font-weight:800;font-size:14px;margin-bottom:6px">Dirty Money Laundromat</div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:14px;line-height:1.6">
          Balance washers & dryers against demand · grow loyal regulars<br>
          Loyalty program, add-ons (vending, ATM, wash & fold), staff & insurance
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

  // Regulars bar (regulars now drive DEMAND, not a flat income bonus)
  const members  = Math.round(lm.members || 0);
  const regColor = lm.regulars > 60 ? 'var(--positive)' : lm.regulars > 20 ? 'var(--warning)' : 'var(--text-muted)';
  const regBar   = `
    <div style="margin:6px 0 10px">
      <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);margin-bottom:3px">
        <span>Regulars (drive demand)</span><span style="color:${regColor}">${lm.regulars}/100${(lm.addons||{}).loyalty ? ` · 💳 ${members} members` : ''}</span>
      </div>
      <div style="background:var(--border);height:6px">
        <div style="background:${regColor};height:6px;width:${lm.regulars}%"></div>
      </div>
    </div>`;

  // Capacity vs. demand — the heart of the new model
  const wcap = Math.round(lmCapacity(lm.machines, 'wash'));
  const dcap = Math.round(lmCapacity(lm.machines, 'dry'));
  const thru = Math.min(wcap, dcap);
  const demand = Math.round(LM_BASE_DEMAND + (lm.regulars || 0) * LM_DEM_REG + (lm.members || 0) * LM_DEM_MEM);
  const shortBy = Math.max(0, demand - thru);
  const bottleneck = wcap < dcap ? 'washers' : dcap < wcap ? 'dryers' : 'machines';
  const capColor = shortBy > 0 ? 'var(--negative)' : 'var(--positive)';
  const capPanel = `
    <div style="border:1px solid ${shortBy > 0 ? 'var(--negative)' : 'var(--border)'};border-radius:10px;padding:10px 12px;margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <span style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted)">Demand vs. Capacity</span>
        <span style="font-size:13px;font-weight:800;color:${capColor}">${demand} / ${thru} loads/day</span>
      </div>
      <div style="display:flex;gap:8px;font-size:11px;color:var(--text-muted)">
        <span>🌀 Wash cap <strong style="color:var(--text-1)">${wcap}</strong></span>
        <span>💨 Dry cap <strong style="color:var(--text-1)">${dcap}</strong></span>
      </div>
      ${shortBy > 0
        ? `<div style="font-size:11px;color:var(--negative);margin-top:6px;font-weight:700">⚠️ Turning away ~${shortBy} loads/day — add ${bottleneck} to capture it.</div>`
        : `<div style="font-size:11px;color:var(--text-muted);margin-top:6px">Capacity covers demand. Grow regulars to fill it.</div>`}
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
      <span style="color:${soapColor}">${pxIcon('🧼', 14)} ${soapLabel}</span>
    </div>`;

  // Supplies row
  const supRow = `
    <div style="display:flex;flex-wrap:wrap;gap:8px;font-size:11px;margin-bottom:12px">
      <span>${pxIcon('🌸', 14)} ${lm.softener_days > 0 ? lm.softener_days + 'd' : '—'}</span>
      <span style="color:var(--text-muted)">|</span>
      <span>${pxIcon('🌬️', 14)} ${lm.sheets_days > 0 ? lm.sheets_days + 'd' : '—'}</span>
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
    const tmeta = LAUNDROMAT_MACHINE_TYPES[m.type || 'combo'];
    return `<div onclick="${onclick}" style="border:1px solid ${border};padding:7px 4px;text-align:center;cursor:pointer;background:${bgColor}">
      <div class="${animClass}">${laundryMachineIcon(m.type || 'combo', isBroken, isRunning, m.id)}</div>
      <div style="font-size:9px;color:var(--text-muted);margin-top:2px">${tmeta.name}</div>
      ${isBroken
        ? `<div style="font-size:9px;color:var(--negative);font-weight:800">⚡3</div>`
        : upgCount > 0
          ? `<div style="font-size:9px;color:var(--positive)">⭐${upgCount}</div>`
          : '<div style="font-size:9px"> </div>'}
    </div>`;
  });
  if (canBuyMore) {
    const step = Math.max(0, machineCount - LAUNDROMAT_START_MACHINES) * LAUNDROMAT_MACHINE_STEP;
    machineCells.push(`
      <div onclick="showBuyLaundroMachine()"
        style="border:1px dashed var(--border);padding:7px 4px;text-align:center;cursor:pointer">
        <div style="font-size:20px;line-height:1;margin-bottom:2px">＋</div>
        <div style="font-size:8px;color:var(--text-muted)">Add machine</div>
        <div style="font-size:8px;color:var(--text-muted)">from ${fmt(15000 + step)}</div>
      </div>`);
  }
  const machineGrid = `
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:12px">
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
        ${pxIcon(meta.icon, 20)}
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

  // Add-ons
  const addons    = lm.addons || {};
  const addonCards = LAUNDROMAT_ADDONS_META.map(a => {
    const owned     = !!addons[a.key];
    const canAfford = state.cash >= a.cost;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:9px;border:1px solid var(--border);border-radius:9px;margin-bottom:6px${owned ? ';opacity:0.7' : ''}">
        <div style="font-size:20px">${a.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:12px">${a.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${a.desc}</div>
        </div>
        ${owned
          ? `<span style="font-size:11px;color:var(--positive);flex-shrink:0">✓ Installed</span>`
          : `<button class="btn btn-sm btn-primary" style="flex-shrink:0" ${canAfford ? `onclick="buyLaundroAddon('${a.key}')"` : 'disabled'}>${canAfford ? fmt(a.cost) : 'Need cash'}</button>`}
      </div>`;
  }).join('');

  // ── Polished layout: header band + section cards ──
  const card = (title, body) => `
    <div style="border:1px solid var(--border);border-radius:12px;padding:12px;margin-bottom:10px">
      <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:8px">${title}</div>
      ${body}
    </div>`;
  const headerBand = `
    <div style="display:flex;align-items:center;gap:11px;padding:12px;border-radius:12px;margin-bottom:10px;background:linear-gradient(135deg,rgba(21,101,192,0.16),transparent 70%);border:1px solid var(--border)">
      <div style="font-size:30px;flex-shrink:0">🌀</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800;font-size:14px">Dirty Money Laundromat</div>
        <div style="font-size:14px;color:${starColor}">${starStr}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:10px;color:var(--text-muted)">Total earned</div>
        <div style="font-weight:800;color:var(--positive)">${fmt(lm.total_earned || 0)}</div>
      </div>
    </div>`;

  return `${headerBand}
    ${capPanel}
    ${card('Health & Loyalty', `${cleanBar}${regBar}<div style="font-size:11px;margin-bottom:4px"><span style="color:${soapColor};font-weight:700">${pxIcon('🧼',13)} ${soapLabel}</span></div>${supRow}`)}
    ${card(`Machines · ${working}/${machineCount} running${broken > 0 ? ` · <span style="color:var(--negative)">${broken} broken</span>` : ''}`, machineGrid + actionRow)}
    ${card('🛍️ Add-Ons', addonCards)}
    ${card('👷 Staff', staffCards)}`;
}

async function buyLaundromat() {
  const res = await api('/laundromat/buy', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
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
  sfx.clean();
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
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px;color:var(--negative)" onclick="showLaundroRemoveConfirm(${machineId})">🗑️ Scrap it instead (no refund)</button>
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
  const tmeta = LAUNDROMAT_MACHINE_TYPES[machine.type || 'combo'];
  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
      <div style="font-size:28px">${tmeta.icon}</div>
      <div>
        <div style="font-weight:800;font-size:15px">${tmeta.name} · Upgrades</div>
        <div style="font-size:11px;color:var(--text-muted)">Dirty Money Laundromat</div>
      </div>
    </div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:8px;color:var(--negative)" onclick="showLaundroRemoveConfirm(${machineId})">🗑️ Remove this machine</button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Close</button>`);
}

function showLaundroRemoveConfirm(machineId) {
  const lm = state.laundromat;
  const m  = lm && lm.machines.find(x => x.id === machineId);
  if (!m) return;
  const tmeta = LAUNDROMAT_MACHINE_TYPES[m.type || 'combo'];
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;color:var(--negative)">⚠️ Remove this ${tmeta.name}?</div>
    <p style="font-size:13px;color:var(--text-2);margin:10px 2px 16px;line-height:1.55">It'll be hauled away for good — <strong>no refund</strong>. Your wash/dry capacity drops by what this machine provided, so watch your demand-vs-capacity balance.</p>
    <button class="btn btn-danger btn-full" onclick="removeLaundroMachine(${machineId})">Remove it — no refund</button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="showLaundroMachineUpgradesModal(${machineId})">Keep it</button>`);
}

async function removeLaundroMachine(machineId) {
  const res = await api('/laundromat/remove_machine', 'POST', { machine_id: machineId });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  closeModal();
  await refreshState();
  renderBusiness();
  toast('Machine removed.', 'info');
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
  sfx.toggle();
  await refreshState();
  renderBusiness();
  const on = state.laundromat?.insurance;
  toast(on ? 'Insurance activated — $400/week, free repairs!' : 'Insurance cancelled.', 'info');
}

async function toggleLaundroStaff(role) {
  const res = await api('/laundromat/hire_staff', 'POST', { role });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.hire();
  await refreshState();
  renderBusiness();
  const hired = state.laundromat?.staff?.[role];
  const name  = LAUNDROMAT_STAFF_META[role]?.name || role;
  toast(hired ? `${name} is on the job!` : `${name} let go.`, 'info');
}

// ── The Back-Room Arcade (secret business, unlocked via the laundromat) ───────
const ARCADE_SERVICE_COST = 250;
const ARCADE_CLEAN_COST   = 120;
const ARCADE_STAFF_META = {
  tech:      { name: 'Repair Tech',   icon: '🔧', cost: 200, desc: 'Auto-fixes & maintains cabinets.' },
  collector: { name: 'Arcade Manager', icon: '💰', cost: 220, desc: 'Banks the cash daily & keeps the prize counter stocked.' },
  janitor:   { name: 'Janitor',       icon: '🧹', cost: 150, desc: 'Keeps the floor clean automatically.' },
};
const ARCADE_DECOR_META = {
  neon:         { name: 'Neon Lights',   icon: '🌈', cost: 6000, effect: '+8% foot traffic' },
  sign:         { name: 'Marquee Sign',  icon: '🪧', cost: 5500, effect: '+6% foot traffic' },
  themed_walls: { name: 'Themed Murals', icon: '🎨', cost: 7500, effect: '+10% foot traffic' },
  carpet:       { name: 'Arcade Carpet', icon: '🟪', cost: 4500, effect: 'Floor dirties slower' },
  snack_nook:   { name: 'Snack Nook',    icon: '🍿', cost: 8000, effect: '+8% cabinet income' },
};
const ARCADE_PRIZES_PER_CASE = 60;
const ARCADE_PRIZE_CASE_COST = 320;
const ARCADE_GENRES = {
  fighting: { name: 'Fighting', icon: '🥊' }, racing: { name: 'Racing', icon: '🏎️' },
  shooter:  { name: 'Shooter',  icon: '👾' }, rhythm: { name: 'Rhythm', icon: '🕺' },
  pinball:  { name: 'Pinball',  icon: '🎰' }, prize:  { name: 'Prize / Claw', icon: '🎁' },
  retro:    { name: 'Retro',    icon: '🕹️' },
};
const ARCADE_GENRE_GAME = {
  fighting: 'Counter Brawler', racing: 'Lane Dodge', shooter: 'Space Siege', rhythm: 'Beat Tap',
  pinball: 'Pinball', prize: 'Claw Grab', retro: 'Quarter Muncher',
};
const ARCADE_GAMES = [
  { title: 'Street Brawler', genre: 'fighting' }, { title: 'Kung-Fu Alley', genre: 'fighting' },
  { title: 'Neon Drift', genre: 'racing' },       { title: 'Retro Racer', genre: 'racing' },
  { title: 'Galaxy Siege', genre: 'shooter' },    { title: 'Pixel Blaster', genre: 'shooter' },
  { title: 'Laser Tag Lords', genre: 'shooter' }, { title: 'Dance Fever', genre: 'rhythm' },
  { title: 'Beat Pulse', genre: 'rhythm' },       { title: 'Pinball Wizard', genre: 'pinball' },
  { title: 'Crane Grab', genre: 'prize' },        { title: 'Ticket Tornado', genre: 'prize' },
  { title: 'Zombie Dunk', genre: 'prize' },       { title: 'Quarter Muncher', genre: 'retro' },
];
function arcadeCabinetIcon(genre, rare) {
  genre = genre || 'retro';
  // Per-genre cabinet: distinct marquee/body colors + unique screen art (same pixel style).
  const C = rare
    ? { dark: '#B8860B', body: '#FFC107', btn: '#FFF59D' }   // rare imports wear gold
    : {
    fighting: { dark: '#7F0000', body: '#C62828', btn: '#FF5252' },
    racing:   { dark: '#1B5E20', body: '#2E7D32', btn: '#66BB6A' },
    shooter:  { dark: '#311B92', body: '#5E35B1', btn: '#B388FF' },
    rhythm:   { dark: '#880E4F', body: '#C2185B', btn: '#FF80AB' },
    pinball:  { dark: '#BF360C', body: '#E65100', btn: '#FFB74D' },
    prize:    { dark: '#006064', body: '#00838F', btn: '#4DD0E1' },
    retro:    { dark: '#1A237E', body: '#3949AB', btn: '#FFD740' },
  }[genre] || { dark: '#1A237E', body: '#3949AB', btn: '#FFD740' };
  // Screen contents (region ~x4.5–15.5, y9–16 on the black screen).
  const SCREEN = {
    fighting: `<rect x="5.5" y="11" width="2.4" height="4" rx="0.4" fill="#FF5252"/><circle cx="6.7" cy="10.3" r="1" fill="#FF5252"/>
               <rect x="12" y="11" width="2.4" height="4" rx="0.4" fill="#42A5F5"/><circle cx="13.2" cy="10.3" r="1" fill="#42A5F5"/>
               <path d="M9.4 11.8 l1 -1 l0.3 1.4 l1 -0.4 l-1 1.5 l-0.3 -1.2 z" fill="#FFEB3B"/>`,
    racing:   `<path d="M6.2 16 L8.6 9.6 L11.4 9.6 L13.8 16 Z" fill="#455A64"/>
               <rect x="9.7" y="10.2" width="0.6" height="1.1" fill="#FFF59D"/><rect x="9.7" y="12.4" width="0.6" height="1.1" fill="#FFF59D"/>
               <rect x="8.8" y="13.8" width="2.4" height="1.8" rx="0.4" fill="#FF5252"/><rect x="9" y="13.4" width="2" height="0.7" fill="#B0BEC5"/>`,
    shooter:  `<rect x="5" y="9.8" width="1.8" height="1.3" fill="#69F0AE"/><rect x="9.1" y="9.8" width="1.8" height="1.3" fill="#69F0AE"/><rect x="13.2" y="9.8" width="1.8" height="1.3" fill="#69F0AE"/>
               <rect x="5.4" y="11.1" width="0.6" height="0.6" fill="#69F0AE"/><rect x="6" y="11.1" width="0.6" height="0.6" fill="#69F0AE"/>
               <rect x="9.6" y="12.6" width="0.6" height="1.1" fill="#FFEB3B"/>
               <path d="M8.7 15.6 l1.3 -1.1 l1.3 1.1 z" fill="#FFFFFF"/>`,
    rhythm:   `<path d="M6.4 13 l1.3 -1.6 l1.3 1.6 z" fill="#E040FB"/>
               <path d="M9.4 11.4 l1.6 1.3 l-1.6 1.3 z" fill="#18FFFF"/>
               <path d="M14 11.4 l-1.6 1.3 l1.6 1.3 z" fill="#FFEB3B"/>
               <rect x="6.5" y="14.4" width="7" height="0.7" fill="#76FF03"/>`,
    pinball:  `<circle cx="10" cy="9.9" r="0.9" fill="#FFFFFF"/>
               <circle cx="6.6" cy="11.6" r="1.1" fill="#FF4081"/><circle cx="13.4" cy="11.6" r="1.1" fill="#18FFFF"/><circle cx="10" cy="13" r="0.9" fill="#FFD740"/>
               <path d="M6.8 15.4 L9.4 14.2" stroke="#ECEFF1" stroke-width="1" stroke-linecap="round"/><path d="M13.2 15.4 L10.6 14.2" stroke="#ECEFF1" stroke-width="1" stroke-linecap="round"/>`,
    prize:    `<rect x="9.4" y="9" width="1.2" height="1.8" fill="#90A4AE"/><path d="M9 10.6 l1 1.2 l1 -1.2" fill="none" stroke="#CFD8DC" stroke-width="0.8"/>
               <circle cx="6.5" cy="14.5" r="1.2" fill="#FF5252"/><circle cx="9.2" cy="15" r="1.3" fill="#FFD740"/><circle cx="12" cy="14.4" r="1.1" fill="#69F0AE"/><circle cx="14" cy="15" r="1" fill="#40C4FF"/>`,
    retro:    `<circle cx="7.3" cy="12.6" r="2.3" fill="#FFEB3B"/><path d="M7.3 12.6 L9.8 11 L9.8 14.2 Z" fill="#0B0B1A"/>
               <rect x="11" y="12.1" width="0.9" height="0.9" fill="#FFFFFF"/><rect x="12.8" y="12.1" width="0.9" height="0.9" fill="#FFFFFF"/><rect x="14.6" y="12.1" width="0.9" height="0.9" fill="#FFFFFF"/>`,
  }[genre] || '';
  return `<svg viewBox="0 0 20 26" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" width="40" height="52" style="display:block;margin:0 auto">
    ${rare ? `<rect x="1.2" y="0.4" width="17.6" height="25.2" rx="1.4" fill="none" stroke="#FFD700" stroke-width="0.8"/>` : ''}
    <rect x="3" y="1" width="14" height="6" rx="1" fill="${C.dark}"/>
    <rect x="4" y="2" width="12" height="4" fill="${C.body}"/>
    ${rare ? `<path d="M10 1.6 l0.5 1.1 l1.2 0.1 l-0.9 0.8 l0.3 1.2 l-1.1 -0.7 l-1.1 0.7 l0.3 -1.2 l-0.9 -0.8 l1.2 -0.1 z" fill="#FFF8E1"/>` : ''}
    <rect x="2" y="7" width="16" height="13" fill="${C.body}"/>
    <rect x="3.5" y="8.5" width="13" height="8" fill="#0B0B1A"/>
    ${SCREEN}
    <rect x="4" y="17" width="12" height="3" fill="${C.dark}"/>
    <circle cx="7" cy="18.5" r="0.9" fill="${C.btn}"/><circle cx="10" cy="18.5" r="0.9" fill="#FFD740"/><rect x="12.3" y="18" width="1.6" height="1.2" fill="#40C4FF"/>
    <rect x="2" y="20" width="16" height="6" fill="${C.body}"/>
    <rect x="5" y="21.5" width="10" height="2" fill="${C.dark}"/>
  </svg>`;
}

function renderArcadeContent() {
  const arc = state.arcade;
  if (!arc || !arc.unlocked) return `<div style="font-size:12px;color:var(--text-muted);padding:10px 0">Locked.</div>`;
  const cabs    = arc.cabinets || [];
  const working = cabs.filter(c => c.status !== 'broken');
  const lm      = state.laundromat || {};
  const traffic = Math.round((0.6 + Math.min(1, ((lm.regulars || 0) + (lm.members || 0)) / 100) * 0.8) * 100);
  // genre counts (working) for the saturation hint
  const gc = {};
  working.forEach(c => { gc[c.genre] = (gc[c.genre] || 0) + 1; });
  const distinct = Object.keys(gc).length;
  const header = `
    <div style="display:flex;align-items:center;gap:11px;padding:12px;border-radius:12px;margin:4px 0 10px;background:linear-gradient(135deg,rgba(57,73,171,0.22),transparent 70%);border:1px solid var(--border)">
      <div style="font-size:30px">🕹️</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800;font-size:14px">The Back-Room Arcade</div>
        <div style="font-size:11px;color:var(--text-muted)">${cabs.length} cabinet${cabs.length === 1 ? '' : 's'} · ${distinct} genre${distinct === 1 ? '' : 's'} on the floor</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:10px;color:var(--text-muted)">Total earned</div>
        <div style="font-weight:800;color:var(--positive)">${fmt(arc.total_earned || 0)}</div>
      </div>
    </div>`;
  // The till: coins pile up in the machines until collected.
  const till      = Math.round(arc.uncollected || 0);
  const tillCap   = Math.max(1000, cabs.length * 1200);
  const tillPct   = Math.min(100, Math.round(till / tillCap * 100));
  const hasCollector = !!(arc.staff && arc.staff.collector);
  const tillNearFull = tillPct >= 85 && !hasCollector;
  const tillCard = `
    <div style="border:1.5px solid ${tillNearFull ? 'var(--warning)' : 'var(--border)'};border-radius:10px;padding:11px 12px;margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:22px">🪙</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:10px;color:var(--text-muted)">In the machines</div>
          <div style="font-weight:800;font-size:17px;color:${till > 0 ? 'var(--positive)' : 'var(--text-muted)'}">${fmt(till)}</div>
        </div>
        ${hasCollector
          ? `<div style="font-size:10px;color:var(--positive);text-align:right;flex-shrink:0">Arcade Manager<br>banks it daily 🟢</div>`
          : `<button class="btn btn-sm btn-primary" style="flex-shrink:0" ${till > 0 && (state.energy || 0) >= 4 ? 'onclick="collectArcade()"' : 'disabled'}>Collect · 4⚡</button>`}
      </div>
      <div style="background:var(--border);height:5px;border-radius:3px;margin-top:8px"><div style="background:${tillNearFull ? 'var(--warning)' : 'var(--positive)'};height:5px;border-radius:3px;width:${tillPct}%"></div></div>
      ${tillNearFull ? `<div style="font-size:10px;color:var(--warning);margin-top:5px">⚠️ Machines almost full — coins past the limit are lost. Collect, or hire an Arcade Manager.</div>` : ''}
    </div>`;
  // Cleanliness: foot traffic dirties the floor; a janitor or a deep clean fixes it.
  const clean     = Math.round(arc.cleanliness != null ? arc.cleanliness : 100);
  const hasJanitor = !!(arc.staff && arc.staff.janitor);
  const cleanCol  = clean > 60 ? 'var(--positive)' : clean > 30 ? 'var(--warning)' : 'var(--negative)';
  const cleanCard = `
    <div style="border:1px solid var(--border);border-radius:10px;padding:11px 12px;margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:20px">${clean > 60 ? '✨' : clean > 30 ? '🧽' : '🤢'}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:10px;color:var(--text-muted)">Cleanliness</div>
          <div style="font-weight:800;font-size:13px;color:${cleanCol}">${clean}%${clean <= 60 ? ' — grimy floors scare off players' : ''}</div>
          <div style="background:var(--border);height:5px;border-radius:3px;margin-top:5px"><div style="background:${cleanCol};height:5px;border-radius:3px;width:${clean}%"></div></div>
        </div>
        ${hasJanitor
          ? `<div style="font-size:10px;color:var(--positive);text-align:right;flex-shrink:0">Janitor<br>on duty 🟢</div>`
          : `<button class="btn btn-sm ${clean < 99 ? 'btn-primary' : 'btn-ghost'}" style="flex-shrink:0" ${clean < 99 && state.cash >= ARCADE_CLEAN_COST && (state.energy || 0) >= 6 ? 'onclick="cleanArcade()"' : 'disabled'}>Clean ${fmt(ARCADE_CLEAN_COST)} · 6⚡</button>`}
      </div>
    </div>`;
  // Prize counter: stock from CostPro to boost income; prizes get won daily.
  const prizes    = Math.round(arc.prizes || 0);
  const prizeUse  = Math.max(1, Math.round(working.length * (traffic / 100) * 1.6));
  const coverage  = Math.min(1, prizes / prizeUse);
  const boostPct  = Math.round(30 * coverage);
  const prizeCard = `
    <div style="border:1px solid var(--border);border-radius:10px;padding:11px 12px;margin-bottom:10px">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:20px">🧸</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:10px;color:var(--text-muted)">Prize counter</div>
          <div style="font-weight:800;font-size:13px">${prizes} prizes in stock
            <span style="font-size:11px;color:${boostPct >= 20 ? 'var(--positive)' : boostPct > 0 ? 'var(--warning)' : 'var(--text-muted)'}">· +${boostPct}% income</span></div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:1px">~${prizeUse} won/day · a full counter = +30%</div>
        </div>
        ${hasCollector
          ? `<div style="font-size:10px;color:var(--positive);text-align:right;flex-shrink:0">Arcade Manager<br>restocks these 🟢</div>`
          : `<button class="btn btn-sm btn-primary" style="flex-shrink:0" onclick="navTo('store')">🛒 CostPro</button>`}
      </div>
      ${prizes === 0 && !hasCollector ? `<div style="font-size:10px;color:var(--text-muted);margin-top:5px">Empty — buy Prize Stock at the CostPro store to boost every cabinet's take. An investment that pays for itself.</div>` : ''}
    </div>`;
  // Floor info: traffic from laundromat + variety tip
  const dupGenres = Object.entries(gc).filter(([, n]) => n >= 3).map(([g]) => ARCADE_GENRES[g].name);
  const floorInfo = `
    <div style="border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin-bottom:10px;font-size:11px;color:var(--text-muted);line-height:1.6">
      🚶 Foot traffic from the laundromat: <strong style="color:${traffic >= 110 ? 'var(--positive)' : traffic >= 80 ? 'var(--warning)' : 'var(--negative)'}">${traffic}%</strong> — busier laundromat, busier arcade.<br>
      🎮 ${distinct >= 4 ? 'Nice variety — a mixed floor pulls bigger crowds.' : 'Mix up your genres — a varied floor out-earns duplicates.'}${dupGenres.length ? ` <span style="color:var(--warning)">Saturated: ${dupGenres.join(', ')}.</span>` : ''}
    </div>`;
  // Stack cabinets by title (×N), surfacing how many of a stack are broken. You
  // can own at most two of any title, so a tile shows ×1 or ×2. Rares get their
  // own gold row beneath the standard floor.
  const stacks = {};
  cabs.forEach(c => {
    if (!stacks[c.title]) stacks[c.title] = { title: c.title, genre: c.genre, rare: !!c.rare, cabs: [] };
    stacks[c.title].cabs.push(c);
  });
  const today  = state.day || 0;
  const stackTile = (stk) => {
    const n      = stk.cabs.length;
    const broken = stk.cabs.filter(c => c.status === 'broken').length;
    const worst  = Math.min(...stk.cabs.map(c => c.status === 'broken' ? 0 : Math.round(c.condition != null ? c.condition : 100)));
    const col    = broken ? 'var(--negative)' : worst > 50 ? 'var(--positive)' : worst > 25 ? 'var(--warning)' : 'var(--negative)';
    const gmeta  = ARCADE_GENRES[stk.genre] || ARCADE_GENRES.retro;
    const hot    = stk.cabs.some(c => (c.hot_until || 0) > today);
    const border = hot ? '#ff7a18' : stk.rare ? '#FFD700' : broken ? 'var(--negative)' : 'var(--border)';
    const status = broken ? `${broken}/${n} 🔧` : worst + '%';
    return `<div onclick="showArcadeStack(${stk.cabs[0].id})" style="position:relative;border:1.5px solid ${border};border-radius:9px;padding:7px 4px 6px;text-align:center;cursor:pointer${stk.rare ? ';background:linear-gradient(160deg,rgba(255,215,0,0.12),transparent 70%)' : ''}">
      ${hot ? `<div style="position:absolute;top:3px;left:3px;font-size:11px">🔥</div>` : ''}
      ${n > 1 ? `<div style="position:absolute;top:3px;right:3px;background:var(--primary);color:#fff;font-size:9px;font-weight:800;border-radius:8px;padding:0 5px;line-height:15px">×${n}</div>` : ''}
      ${arcadeCabinetIcon(stk.genre, stk.rare)}
      <div style="font-size:9px;font-weight:700;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${stk.rare ? '🌟' : gmeta.icon} ${stk.title}</div>
      <div style="background:var(--border);height:4px;border-radius:2px;margin:4px 2px 0"><div style="background:${col};height:4px;border-radius:2px;width:${broken ? 100 : worst}%"></div></div>
      <div style="font-size:8px;color:${col};margin-top:1px">${status}</div>
    </div>`;
  };
  const allStacks  = Object.values(stacks);
  const normStacks = allStacks.filter(x => !x.rare).sort((a, b) => a.genre.localeCompare(b.genre) || a.title.localeCompare(b.title));
  const rareStacks = allStacks.filter(x => x.rare).sort((a, b) => a.title.localeCompare(b.title));
  const gridStyle  = 'display:grid;grid-template-columns:repeat(4,1fr);gap:6px';
  const normalGrid = normStacks.length
    ? `<div style="${gridStyle}">${normStacks.map(stackTile).join('')}</div>`
    : `<div style="text-align:center;font-size:12px;color:var(--text-muted);padding:14px 0">No cabinets yet — hit the market below.</div>`;
  const rareGrid   = rareStacks.length
    ? `<div style="font-size:11px;font-weight:800;color:#C99700;margin:13px 0 6px;letter-spacing:0.5px">🌟 RARE IMPORTS</div><div style="${gridStyle}">${rareStacks.map(stackTile).join('')}</div>`
    : '';
  const floorHtml  = `${normalGrid}${rareGrid}`;
  const buyBtn = `<button class="btn btn-primary btn-full" style="margin-top:10px" onclick="showBuyArcadeCabinet()">🛒 Today's Cabinet Market</button>`;
  // Decor / theming — one-time cosmetic upgrades with real effects.
  const decor = arc.decor || {};
  const decorCards = Object.entries(ARCADE_DECOR_META).map(([key, m]) => {
    const owned = !!decor[key];
    return `
    <div style="display:flex;align-items:center;gap:10px;padding:9px 10px;border:1px solid ${owned ? 'var(--positive)' : 'var(--border)'};border-radius:9px;margin-top:8px${owned ? ';opacity:0.75' : ''}">
      <div style="font-size:20px">${m.icon}</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800;font-size:12px">${m.name}</div>
        <div style="font-size:10px;color:var(--text-muted)">${m.effect}</div>
      </div>
      ${owned
        ? `<span style="font-size:11px;color:var(--positive);font-weight:700;flex-shrink:0">✓ Installed</span>`
        : `<button class="btn btn-sm btn-primary" style="flex-shrink:0" ${state.cash >= m.cost ? `onclick="buyArcadeDecor('${key}')"` : 'disabled'}>${fmt(m.cost)}</button>`}
    </div>`;
  }).join('');
  const decorSection = `<div style="font-size:11px;font-weight:700;color:var(--text-muted);margin-top:14px">DECOR & THEMING</div>${decorCards}`;
  // Staff — tech, floor manager, janitor.
  const staffCards = ['tech', 'collector', 'janitor'].map(role => {
    const m   = ARCADE_STAFF_META[role];
    const on  = !!(arc.staff && arc.staff[role]);
    return `
    <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);border-radius:9px;margin-top:8px">
      <div style="font-size:20px">${m.icon}</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800;font-size:12px">${m.name}</div>
        <div style="font-size:10px;color:var(--text-muted)">${m.desc}</div>
        <div style="font-size:10px;margin-top:2px;color:${on ? 'var(--positive)' : 'var(--text-muted)'}">${on ? `🟢 On the job — $${m.cost}/day` : '⚫ Not hired'}</div>
      </div>
      <button class="btn btn-sm ${on ? 'btn-ghost' : 'btn-primary'}" onclick="toggleArcadeStaff('${role}')">${on ? 'Fire' : `Hire — $${m.cost}/day`}</button>
    </div>`;
  }).join('');
  const staffSection = `<div style="font-size:11px;font-weight:700;color:var(--text-muted);margin-top:14px">STAFF</div>${staffCards}`;
  return `${header}${tillCard}${cleanCard}${prizeCard}${floorInfo}
    ${floorHtml}
    ${buyBtn}${decorSection}${staffSection}
    <div style="font-size:11px;color:var(--text-muted);margin-top:12px;line-height:1.5">🕹️ Coming next: <strong>play your cabinets yourself</strong> — set the high score and make a machine go 🔥 hot. (Plus tournaments.)</div>`;
}

function showBuyArcadeCabinet() {
  const arc = state.arcade; if (!arc) return;
  const market = arc.market || [];
  const owned  = arc.cabinets || [];
  const rows = market.length === 0
    ? `<div style="text-align:center;font-size:12px;color:var(--text-muted);padding:18px 0">Sold out for today.<br>Advance a day for a fresh lineup.</div>`
    : market.map(o => {
        const gm     = ARCADE_GENRES[o.genre] || ARCADE_GENRES.retro;
        const atCap  = owned.filter(c => c.title === o.title).length >= 2;
        const tooPoor = state.cash < o.price;
        const dis    = atCap || tooPoor;
        return `
      <div style="display:flex;align-items:center;gap:10px;padding:9px 10px;border:1.5px solid ${o.rare ? '#FFD700' : 'var(--border)'};border-radius:10px;margin-bottom:8px${o.rare ? ';background:linear-gradient(150deg,rgba(255,215,0,0.14),transparent 75%)' : ''}">
        <div style="flex-shrink:0">${arcadeCabinetIcon(o.genre, o.rare)}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:13px">${o.rare ? '🌟 ' : ''}${o.title}</div>
          <div style="font-size:10px;color:var(--text-muted)">${gm.name}${o.rare ? ' · RARE IMPORT — earns ~80% more' : ''}</div>
          <div style="font-weight:800;font-size:13px;color:${o.rare ? '#C99700' : 'var(--text-1)'};margin-top:2px">${fmt(o.price)}</div>
          ${atCap ? `<div style="font-size:10px;color:var(--warning)">You already run two of these</div>` : ''}
        </div>
        <button class="btn btn-sm ${o.rare ? 'btn-primary' : 'btn-primary'}" style="flex-shrink:0" ${dis ? 'disabled' : `onclick="buyArcadeCabinet(${o.id})"`}>${atCap ? 'Max' : tooPoor ? 'Need $' : 'Buy'}</button>
      </div>`;
      }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px">🛒 Today's Cabinet Market</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">Three machines on offer today. The lineup only refreshes once you buy one — and there's always a chance a 🌟 rare import shows up.</div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Close</button>`);
}

async function buyArcadeCabinet(offerId) {
  const res = await api('/arcade/buy_cabinet', 'POST', { offer_id: offerId });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  closeModal();
  await refreshState();
  renderBusiness();
  toast(res.rare ? '🌟 Rare import on the floor!' : 'New cabinet on the floor!', 'success');
}

async function buyArcadeDecor(key) {
  const res = await api('/arcade/buy_decor', 'POST', { key });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('Looking sharp!', 'success');
}

function showArcadeStack(anchorId) {
  const arc = state.arcade; if (!arc) return;
  const anchor = (arc.cabinets || []).find(x => x.id === anchorId); if (!anchor) return;
  const copies = (arc.cabinets || []).filter(x => x.title === anchor.title);
  const gm = ARCADE_GENRES[anchor.genre] || ARCADE_GENRES.retro;
  const today = state.day || 0;
  const gameName = ARCADE_GENRE_GAME[anchor.genre] || 'Arcade Game';
  const rows = copies.map((c, i) => {
    const broken = c.status === 'broken';
    const cond   = Math.round(c.condition != null ? c.condition : 100);
    const needs  = broken || cond < 99;
    const stCol  = broken ? 'var(--negative)' : cond > 50 ? 'var(--positive)' : 'var(--warning)';
    const hot    = (c.hot_until || 0) > today;
    const hi     = c.high_score || 0;
    return `
      <div style="border:1px solid ${hot ? '#ff7a18' : 'var(--border)'};border-radius:9px;padding:10px;margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <div style="flex:1;font-weight:700;font-size:12px">${copies.length > 1 ? `Cabinet #${i + 1}` : 'Cabinet'} ${hot ? '<span style="color:#ff7a18">🔥 HOT</span>' : ''}</div>
          <div style="font-size:11px;color:var(--text-muted)">HI ${hi.toLocaleString()}</div>
          <div style="font-size:11px;font-weight:700;color:${stCol}">${broken ? '🔧 Broken' : `${cond}%`}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" style="flex:1" ${broken ? 'disabled title="Repair it first"' : `onclick="playArcadeCabinet(${c.id})"`}>${broken ? '🔧 Broken' : '▶ Play'}</button>
          ${needs ? `<button class="btn btn-sm btn-ghost" style="flex-shrink:0" ${state.cash >= ARCADE_SERVICE_COST ? `onclick="serviceArcadeCabinet(${c.id})"` : 'disabled'}>${broken ? 'Repair' : 'Service'} ${fmt(ARCADE_SERVICE_COST)}</button>` : ''}
          <button class="btn btn-sm btn-ghost" style="flex-shrink:0;color:var(--negative)" onclick="removeArcadeCabinet(${c.id})">🗑️</button>
        </div>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px">${anchor.rare ? '🌟 ' : gm.icon + ' '}${anchor.title}</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">${gameName} · ${gm.name}${anchor.rare ? ' · rare import' : ''} · beat the high score to go 🔥 hot</div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Close</button>`);
}

async function serviceArcadeCabinet(cid) {
  const res = await api('/arcade/service_cabinet', 'POST', { cabinet_id: cid });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  closeModal(); await refreshState(); renderBusiness();
  toast('Cabinet serviced.', 'success');
}

async function removeArcadeCabinet(cid) {
  const res = await api('/arcade/remove_cabinet', 'POST', { cabinet_id: cid });
  if (res.error) { toast(res.error, 'error'); return; }
  closeModal(); await refreshState(); renderBusiness();
  toast('Cabinet removed.', 'info');
}

async function toggleArcadeStaff(role) {
  const res = await api('/arcade/hire_staff', 'POST', { role });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  await refreshState(); renderBusiness();
}

async function collectArcade() {
  const res = await api('/arcade/collect', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase?.();
  await refreshState(); renderBusiness();
  toast(`Collected ${fmt(res.collected)} from the machines!`, 'success');
}

async function cleanArcade() {
  const res = await api('/arcade/clean', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  await refreshState(); renderBusiness();
  toast('Floor sparkling again.', 'success');
}

// ── Playable arcade mini-games (one archetype per genre) ──────────────────────
(function(){
  var W=400,H=440,cv=null,X=null,G=null,RAF=null,last=0,curCab=null;
  var keys={},AC=null;
  function ac(){if(typeof _sfxEnabled!=='undefined'&&!_sfxEnabled)return null;if(!AC){try{AC=new (window.AudioContext||window.webkitAudioContext)();}catch(e){}}if(AC&&AC.state==='suspended')AC.resume();return AC;}
  function beep(f,dur,type,vol,slide){var c=ac();if(!c)return;var o=c.createOscillator(),g=c.createGain();o.type=type||'square';o.frequency.setValueAtTime(f,c.currentTime);if(slide)o.frequency.exponentialRampToValueAtTime(slide,c.currentTime+dur);g.gain.setValueAtTime(vol||0.18,c.currentTime);g.gain.exponentialRampToValueAtTime(0.0001,c.currentTime+dur);o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+dur);}
  function noise(dur,vol){var c=ac();if(!c)return;var n=Math.floor(c.sampleRate*dur),buf=c.createBuffer(1,n,c.sampleRate),d=buf.getChannelData(0);for(var i=0;i<n;i++)d[i]=Math.random()*2-1;var src=c.createBufferSource();src.buffer=buf;var g=c.createGain();g.gain.setValueAtTime(vol||0.15,c.currentTime);g.gain.exponentialRampToValueAtTime(0.0001,c.currentTime+dur);var fl=c.createBiquadFilter();fl.type='highpass';fl.frequency.value=700;src.connect(fl);fl.connect(g);g.connect(c.destination);src.start();src.stop(c.currentTime+dur);}
  var SFX={shoot:function(){beep(880,0.07,'square',0.08,300);},zap:function(){beep(520,0.09,'square',0.12,1300);},hit:function(){beep(180,0.12,'sawtooth',0.18,80);},blip:function(){beep(620,0.05,'square',0.1);},hi:function(){beep(1046,0.08,'square',0.13);},mid:function(){beep(740,0.08,'square',0.11);},low:function(){beep(150,0.2,'sawtooth',0.18,70);},coin:function(){beep(880,0.05,'square',0.11);setTimeout(function(){beep(1318,0.08,'square',0.11);},45);},punch:function(){noise(0.07,0.2);beep(110,0.1,'sawtooth',0.16,55);},whoosh:function(){beep(420,0.12,'sine',0.12,950);},boing:function(){beep(300,0.12,'triangle',0.15,720);},flip:function(){beep(210,0.04,'square',0.09);},drop:function(){beep(700,0.22,'sine',0.11,200);},chime:function(){beep(784,0.08,'sine',0.13);setTimeout(function(){beep(1046,0.1,'sine',0.13);},65);setTimeout(function(){beep(1318,0.12,'sine',0.13);},135);},ko:function(){beep(523,0.1,'square',0.15);setTimeout(function(){beep(659,0.1,'square',0.15);},85);setTimeout(function(){beep(784,0.2,'square',0.15);},175);},over:function(){beep(380,0.15,'sawtooth',0.16,200);setTimeout(function(){beep(190,0.32,'sawtooth',0.16,75);},130);},crash:function(){noise(0.25,0.22);beep(140,0.25,'sawtooth',0.18,60);}};
  function rc(x,y,w,h,c){X.fillStyle=c;X.fillRect(x,y,w,h);}
  function rr(x,y,w,h,r,c){X.fillStyle=c;X.beginPath();X.moveTo(x+r,y);X.arcTo(x+w,y,x+w,y+h,r);X.arcTo(x+w,y+h,x,y+h,r);X.arcTo(x,y+h,x,y,r);X.arcTo(x,y,x+w,y,r);X.fill();}
  function ci(x,y,r,c){X.fillStyle=c;X.beginPath();X.arc(x,y,r,0,7);X.fill();}
  function tx(s,x,y,sz,c,a){X.fillStyle=c;X.font='bold '+sz+'px monospace';X.textAlign=a||'center';X.textBaseline='alphabetic';X.fillText(s,x,y);}
  function logical(e){var r=cv.getBoundingClientRect();return {x:(e.clientX-r.left)/r.width*W,y:(e.clientY-r.top)/r.height*H};}
  var HINTS={fighting:'Read the telegraph: tap the side it shows to dodge, then tap to counter-punch.',racing:'Tap the left or right side to switch lanes. Dodge the cars.',shooter:'Drag to move your ship — it auto-fires. Don’t let invaders land.',rhythm:'Tap each column as its note crosses the line.',pinball:'Tap the left or right side to flip. Only the center gap drains.',prize:'Tap to drop the claw when it lines up with a prize.',retro:'Tap a direction to steer. Eat coins, don’t bite yourself.'};

  function makeFighting(){return{score:0,php:100,ohp:100,omax:100,round:1,state:'idle',t:0.6,need:0,dodged:0,combo:0,msg:'',mt:0,ph:0,osh:0,winT:0.95,
   update:function(dt){if(this.mt>0)this.mt-=dt;if(this.ph>0)this.ph-=dt;if(this.osh>0)this.osh-=dt;this.t-=dt;
    if(this.state==='idle'){if(this.t<=0){this.need=Math.random()<0.5?-1:1;this.dodged=0;this.t=this.winT;this.state='windup';}}
    else if(this.state==='windup'){if(this.t<=0){if(this.dodged===this.need){this.state='open';this.t=0.95;this.msg='COUNTER!';this.mt=0.5;SFX.whoosh();}else{this.php-=14+this.round*2;this.combo=0;this.ph=0.4;this.msg='HIT!';this.mt=0.5;this.state='recover';this.t=0.5;SFX.hit();if(this.php<=0)this.over=true;}}}
    else if(this.state==='open'){if(this.t<=0){this.state='recover';this.t=0.35;}}
    else if(this.state==='recover'){if(this.t<=0){this.t=0.3+Math.random()*0.5;this.state='idle';}}},
   dodge:function(d){if(this.state==='windup')this.dodged=d;},
   punch:function(){if(this.state==='open'){this.ohp-=10;this.combo++;this.score+=12*(1+this.combo*0.1);this.osh=0.12;SFX.punch();if(this.ohp<=0){this.round++;this.omax+=20;this.ohp=this.omax;this.winT=Math.max(0.42,this.winT-0.07);this.score+=80;this.state='recover';this.t=0.7;this.msg='K.O.!';this.mt=0.9;SFX.ko();}}},
   key:function(k){if(k==='ArrowLeft'||k==='a')this.dodge(-1);else if(k==='ArrowRight'||k==='d')this.dodge(1);else if(k===' ')this.punch();},
   tap:function(x){if(this.state==='open')this.punch();else if(this.state==='windup')this.dodge(x<W/2?-1:1);},
   draw:function(){rc(0,0,W,H,'#2a1018');var sh=this.ph>0?(Math.random()*10-5):0;
    if(this.state==='windup'){var a=0.2+0.3*Math.abs(Math.sin(performance.now()/70));X.fillStyle='rgba(255,210,74,'+a+')';X.fillRect(this.need<0?0:W-54,0,54,H);}
    var ox=W/2+sh+(this.osh>0?(Math.random()*12-6):0);var op=this.state==='open';
    rc(ox-36,206,72,96,op?'#caa23a':'#a83a54');ci(ox,168,46,op?'#ffd24a':'#c0506e');
    if(this.state==='windup'){var aw=this.need<0?1:-1;ci(ox+aw*52,210,20,'#a83a54');}else{ci(ox-50,250,18,op?'#caa23a':'#a83a54');ci(ox+50,250,18,op?'#caa23a':'#a83a54');}
    if(op){tx('!',ox-16,150,22,'#fff');tx('!',ox+16,150,22,'#fff');}
    rc(30,300,150,14,'#3a2030');rc(30,300,150*Math.max(0,this.ohp/this.omax),14,'#ff5a6e');tx('ENEMY',30,296,11,'#9aa3c0','left');
    rc(W-180,300,150,14,'#1a2c38');rc(W-180,300,150*Math.max(0,this.php/100),14,'#4ad6ff');tx('YOU',W-30,296,11,'#9aa3c0','right');
    if(this.state==='windup')tx(this.need<0?'◀ DODGE':'DODGE ▶',W/2,135,22,'#ffd24a');else if(op)tx('TAP TO COUNTER!',W/2,135,18,'#7cff6b');
    if(this.mt>0)tx(this.msg,W/2,350,24,(this.msg==='HIT!')?'#ff5a6e':'#7cff6b');
    var pgx=sh+(this.dodged?this.dodged*34:0);ci(W/2-58+pgx,432,18,'#4ad6ff');ci(W/2+58+pgx,432,18,'#4ad6ff');
    tx('ROUND '+this.round,W/2,52,14,'#c08bff');}};}

  function makeRacing(){var L=[80,200,320];return{score:0,lane:1,obs:[],spawn:0.6,v:175,road:0,
   update:function(dt){this.v+=dt*7;this.road=(this.road+this.v*dt)%48;this.score+=this.v*dt*0.12;this.spawn-=dt;if(this.spawn<=0){this.spawn=Math.max(0.42,1.15-this.v/520);this.obs.push({l:Math.floor(Math.random()*3),y:-44});}for(var k=0;k<this.obs.length;k++)this.obs[k].y+=this.v*dt;this.obs=this.obs.filter(function(o){return o.y<H+50;});for(var j=0;j<this.obs.length;j++)if(this.obs[j].l===this.lane&&Math.abs(this.obs[j].y-360)<48){SFX.crash();this.over=true;}},
   tap:function(x){this.lane=x<W/2?Math.max(0,this.lane-1):Math.min(2,this.lane+1);SFX.blip();},
   key:function(k){if(k==='ArrowLeft'||k==='a'){this.lane=Math.max(0,this.lane-1);SFX.blip();}if(k==='ArrowRight'||k==='d'){this.lane=Math.min(2,this.lane+1);SFX.blip();}},
   draw:function(){rc(0,0,W,H,'#20242e');rc(30,0,W-60,H,'#2c313d');for(var i=-1;i<12;i++)rc(W/2-3,i*48+this.road,6,26,'#6a7081');rc(135,0,4,H,'#444b59');rc(261,0,4,H,'#444b59');
    for(var k=0;k<this.obs.length;k++){var o=this.obs[k];rr(L[o.l]-17,o.y-22,34,44,5,'#ffd24a');rc(L[o.l]-12,o.y-14,24,10,'#0d1020');}
    rr(L[this.lane]-17,338,34,46,5,'#4ad6ff');rc(L[this.lane]-12,346,24,10,'#0d1020');}};}

  function makeShooter(){return{score:0,lives:3,px:W/2,bul:[],en:[],spawn:0.5,fire:0,
   update:function(dt){if(keys['ArrowLeft']||keys['a'])this.px-=250*dt;if(keys['ArrowRight']||keys['d'])this.px+=250*dt;this.px=Math.max(18,Math.min(W-18,this.px));
    this.fire-=dt;if(this.fire<=0){this.fire=0.26;this.bul.push({x:this.px,y:372});SFX.shoot();}for(var k=0;k<this.bul.length;k++)this.bul[k].y-=440*dt;this.bul=this.bul.filter(function(b){return b.y>-8;});
    this.spawn-=dt;if(this.spawn<=0){this.spawn=Math.max(0.24,0.95-this.score/650);var cnt=this.score>800?2:1;for(var q=0;q<cnt;q++)this.en.push({x:28+Math.random()*(W-56),y:-18,vy:60+Math.min(150,this.score/20)+Math.random()*45,t:Math.random()*6,a:0});}
    for(var e=0;e<this.en.length;e++){this.en[e].t+=dt;this.en[e].a=this.en[e].x+Math.sin(this.en[e].t*2.3)*24;this.en[e].y+=this.en[e].vy*dt;}
    for(var m=0;m<this.en.length;m++){var en=this.en[m];for(var n=0;n<this.bul.length;n++){var b=this.bul[n];if(Math.abs(b.x-en.a)<16&&Math.abs(b.y-en.y)<15){en.d=1;b.d=1;this.score+=10;SFX.zap();}}if(en.y>388){en.d=1;this.lives--;SFX.hit();if(this.lives<=0)this.over=true;}}
    this.en=this.en.filter(function(e){return !e.d;});this.bul=this.bul.filter(function(b){return !b.d;});},
   move:function(x){this.px=Math.max(18,Math.min(W-18,x));},
   draw:function(){rc(0,0,W,H,'#070b1c');for(var i=0;i<24;i++){var sy=(i*53+performance.now()*0.02)%H;rc((i*137)%W,sy,2,2,'#2a3050');}
    for(var k=0;k<this.bul.length;k++)rc(this.bul[k].x-1.5,this.bul[k].y,3,10,'#7cff6b');
    for(var m=0;m<this.en.length;m++){var e=this.en[m];rr(e.a-13,e.y-10,26,20,4,'#ff5a6e');rc(e.a-7,e.y-2,4,4,'#0d1020');rc(e.a+3,e.y-2,4,4,'#0d1020');}
    X.fillStyle='#4ad6ff';X.beginPath();X.moveTo(this.px,372);X.lineTo(this.px-15,396);X.lineTo(this.px+15,396);X.fill();}};}

  function makeRhythm(){var C=[64,154,246,336],KM={d:0,f:1,j:2,k:3},hy=378;return{score:0,timeLeft:30,combo:0,notes:[],spawn:0,fl:[0,0,0,0],judge:'',jt:0,
   update:function(dt){this.timeLeft-=dt;if(this.timeLeft<=0)this.over=true;this.spawn-=dt;if(this.spawn<=0){this.spawn=0.4+Math.random()*0.28;this.notes.push({c:Math.floor(Math.random()*4),y:-18});}for(var k=0;k<this.notes.length;k++){var nn=this.notes[k];nn.y+=300*dt;if(nn.y>hy+34&&!nn.hit){nn.hit=1;this.combo=0;this.judge='MISS';this.jt=0.35;}}this.notes=this.notes.filter(function(n){return n.y<H+20;});for(var i=0;i<4;i++)if(this.fl[i]>0)this.fl[i]-=dt;if(this.jt>0)this.jt-=dt;},
   hit:function(c){this.fl[c]=0.12;var best=null,bd=999;for(var k=0;k<this.notes.length;k++){var n=this.notes[k];if(n.c===c&&!n.hit){var d=Math.abs(n.y-hy);if(d<bd){bd=d;best=n;}}}if(best&&bd<42){best.hit=1;if(bd<14){this.score+=30*(1+this.combo*0.05);this.judge='PERFECT';SFX.hi();}else{this.score+=15*(1+this.combo*0.05);this.judge='GOOD';SFX.mid();}this.combo++;this.jt=0.4;}else{this.combo=0;this.judge='MISS';this.jt=0.35;SFX.low();}},
   key:function(k){if(k in KM)this.hit(KM[k]);},tap:function(x){var c=0;for(var i=1;i<4;i++)if(Math.abs(x-C[i])<Math.abs(x-C[c]))c=i;this.hit(c);},
   draw:function(){rc(0,0,W,H,'#150d24');for(var i=0;i<4;i++){rc(C[i]-40,30,80,H-30,i%2?'#1c1330':'#1f1636');if(this.fl[i]>0){X.fillStyle='rgba(192,139,255,'+(this.fl[i]/0.12*0.5)+')';X.fillRect(C[i]-40,30,80,H-30);}}
    rc(20,hy,W-40,4,'#c08bff');for(var j=0;j<4;j++){rr(C[j]-30,hy+8,60,32,5,'#2a1c40');ci(C[j],hy+24,6,'#c08bff');}
    for(var k=0;k<this.notes.length;k++){var n=this.notes[k];if(!n.hit)rr(C[n.c]-28,n.y-10,56,20,5,'#c08bff');}
    if(this.jt>0)tx(this.judge,W/2,200,22,this.judge==='PERFECT'?'#7cff6b':this.judge==='GOOD'?'#ffd24a':'#ff5a6e');}};}

  function makePinball(){var B=[{x:120,y:150,r:22},{x:280,y:160,r:22},{x:200,y:240,r:24}];
   var WALLS=[[22,22,22,300],[378,22,378,300],[22,22,378,22],[22,300,130,404],[378,300,270,404]];
   function rA(s){return s>0?0.30:Math.PI-0.30;}function uA(s){return s>0?-0.52:Math.PI+0.52;}
   return{score:0,lives:3,bx:200,by:70,vx:30,vy:0,la:rA(1),ra:rA(-1),lp:0,rp:0,lt:null,rt:null,
    reset:function(){this.bx=200;this.by=64;this.vx=Math.random()*50-25;this.vy=0;},
    seg:function(ax,ay,bx2,by2,r,flip,act){var dx=bx2-ax,dy=by2-ay,L=dx*dx+dy*dy||1;var t=Math.max(0,Math.min(1,((this.bx-ax)*dx+(this.by-ay)*dy)/L));var qx=ax+dx*t,qy=ay+dy*t;var nx=this.bx-qx,ny=this.by-qy,d=Math.hypot(nx,ny);if(d<r){nx/=(d||1);ny/=(d||1);this.bx=qx+nx*r;this.by=qy+ny*r;var dot=this.vx*nx+this.vy*ny;if(dot<0){this.vx-=2*dot*nx;this.vy-=2*dot*ny;}this.vx*=0.95;this.vy*=0.95;if(flip&&act){this.vx+=nx*165;this.vy+=ny*165;SFX.flip();}}},
    update:function(dt){if(this.lp>0)this.lp-=dt;if(this.rp>0)this.rp-=dt;var lAct=keys['ArrowLeft']||keys['a']||this.lp>0,rAct=keys['ArrowRight']||keys['d']||this.rp>0;
     this.la+=((lAct?uA(1):rA(1))-this.la)*Math.min(1,dt*24);this.ra+=((rAct?uA(-1):rA(-1))-this.ra)*Math.min(1,dt*24);
     this.lt={x:130+Math.cos(this.la)*54,y:404+Math.sin(this.la)*54};this.rt={x:270+Math.cos(this.ra)*54,y:404+Math.sin(this.ra)*54};
     for(var s=0;s<5;s++){var h=dt/5;this.vy+=430*h;this.bx+=this.vx*h;this.by+=this.vy*h;
      for(var w=0;w<WALLS.length;w++)this.seg(WALLS[w][0],WALLS[w][1],WALLS[w][2],WALLS[w][3],8,false,false);
      for(var bi=0;bi<B.length;bi++){var b=B[bi];var dx=this.bx-b.x,dy=this.by-b.y,d=Math.hypot(dx,dy);if(d<b.r+8){var nx=dx/(d||1),ny=dy/(d||1);this.bx=b.x+nx*(b.r+8);this.by=b.y+ny*(b.r+8);var dot=this.vx*nx+this.vy*ny;this.vx-=2*dot*nx;this.vy-=2*dot*ny;this.vx*=1.03;this.vy*=1.03;this.score+=100;SFX.boing();}}
      this.seg(130,404,this.lt.x,this.lt.y,9,true,lAct);this.seg(270,404,this.rt.x,this.rt.y,9,true,rAct);}
     var sp=Math.hypot(this.vx,this.vy);if(sp>520){this.vx*=520/sp;this.vy*=520/sp;}
     if(this.by>H+16){this.lives--;SFX.low();if(this.lives<=0)this.over=true;else this.reset();}},
    tap:function(x){if(x<W/2)this.lp=0.16;else this.rp=0.16;},
    draw:function(){rc(0,0,W,H,'#0d1424');X.strokeStyle='#33476e';X.lineWidth=5;X.lineCap='round';for(var w=0;w<WALLS.length;w++){X.beginPath();X.moveTo(WALLS[w][0],WALLS[w][1]);X.lineTo(WALLS[w][2],WALLS[w][3]);X.stroke();}
     for(var bi=0;bi<B.length;bi++){ci(B[bi].x,B[bi].y,B[bi].r,'#ffd24a');ci(B[bi].x,B[bi].y,B[bi].r-7,'#1a2742');}
     X.strokeStyle='#4ad6ff';X.lineWidth=11;X.beginPath();X.moveTo(130,404);X.lineTo(this.lt.x,this.lt.y);X.stroke();X.beginPath();X.moveTo(270,404);X.lineTo(this.rt.x,this.rt.y);X.stroke();
     ci(this.bx,this.by,8,'#fff');}};}

  function makeClaw(){var P=[];for(var i=0;i<6;i++)P.push({x:50+i*60,gold:Math.random()<0.2,oy:Math.random()*18-6});return{score:0,timeLeft:30,cx:200,dir:1,sp:155,drop:0,dy:30,msg:'',mt:0,prizes:P,
   update:function(dt){this.timeLeft-=dt;if(this.timeLeft<=0)this.over=true;if(this.mt>0)this.mt-=dt;if(!this.drop){this.cx+=this.dir*this.sp*dt;if(this.cx>360){this.cx=360;this.dir=-1;}if(this.cx<40){this.cx=40;this.dir=1;}}else{this.dy+=300*dt;if(this.dy>=392){var got=null;for(var k=0;k<this.prizes.length;k++){var p=this.prizes[k];if(!p.taken&&Math.abs(p.x-this.cx)<22){got=p;break;}}if(got){got.taken=1;this.score+=got.gold?50:20;this.msg=got.gold?'GOLD! +50':'+20';this.mt=0.7;SFX.chime();got.x=40+Math.random()*320;got.gold=Math.random()<0.2;got.oy=Math.random()*18-6;got.taken=0;}else{this.msg='miss';this.mt=0.5;SFX.blip();}this.drop=0;this.dy=30;}}},
   tap:function(){if(!this.drop){this.drop=1;SFX.drop();}},key:function(k){if(k===' '&&!this.drop){this.drop=1;SFX.drop();}},
   draw:function(){rc(0,0,W,H,'#241526');rc(20,40,W-40,8,'#3a2440');for(var k=0;k<this.prizes.length;k++){var p=this.prizes[k];if(!p.taken)rr(p.x-15,402+p.oy,30,28,4,p.gold?'#ffd24a':'#ff9ecb');}
    rc(this.cx-3,48,6,this.dy-48,'#9aa3c0');X.strokeStyle='#cfd6ee';X.lineWidth=4;X.beginPath();X.moveTo(this.cx-12,this.dy);X.lineTo(this.cx,this.dy+14);X.lineTo(this.cx+12,this.dy);X.stroke();
    if(this.mt>0)tx(this.msg,W/2,200,22,this.msg==='miss'?'#9aa3c0':'#ffd24a');
    if(!this.drop)tx('tap to drop',W/2,H-16,12,'#9aa3c0');}};}

  function makeSnake(){var cell=20,cols=20,rows=22;return{score:0,snake:[{x:10,y:11},{x:9,y:11},{x:8,y:11}],dir:{x:1,y:0},nd:{x:1,y:0},coin:{x:14,y:11},acc:0,step:0.14,
   update:function(dt){this.acc+=dt;if(this.acc<this.step)return;this.acc=0;if(this.nd.x!==-this.dir.x||this.nd.y!==-this.dir.y)this.dir=this.nd;var hd={x:this.snake[0].x+this.dir.x,y:this.snake[0].y+this.dir.y};if(hd.x<0||hd.y<0||hd.x>=cols||hd.y>=rows){SFX.crash();this.over=true;return;}for(var k=0;k<this.snake.length;k++)if(this.snake[k].x===hd.x&&this.snake[k].y===hd.y){SFX.crash();this.over=true;return;}this.snake.unshift(hd);if(hd.x===this.coin.x&&hd.y===this.coin.y){this.score+=10;SFX.coin();this.step=Math.max(0.07,this.step-0.004);var ok;do{ok=true;this.coin={x:Math.floor(Math.random()*cols),y:Math.floor(Math.random()*rows)};for(var j=0;j<this.snake.length;j++)if(this.snake[j].x===this.coin.x&&this.snake[j].y===this.coin.y)ok=false;}while(!ok);}else this.snake.pop();},
   set:function(x,y){this.nd={x:x,y:y};},key:function(k){if(k==='ArrowUp'||k==='w')this.set(0,-1);if(k==='ArrowDown'||k==='s')this.set(0,1);if(k==='ArrowLeft'||k==='a')this.set(-1,0);if(k==='ArrowRight'||k==='d')this.set(1,0);},
   tap:function(x,y){var hx=this.snake[0].x*cell+cell/2,hy=this.snake[0].y*cell+cell/2;if(Math.abs(x-hx)>Math.abs(y-hy))this.set(x>hx?1:-1,0);else this.set(0,y>hy?1:-1);},
   draw:function(){rc(0,0,W,H,'#0d1020');ci(this.coin.x*cell+cell/2,this.coin.y*cell+cell/2,7,'#ffd24a');tx('$',this.coin.x*cell+cell/2,this.coin.y*cell+cell/2+4,11,'#0d1020');for(var i=0;i<this.snake.length;i++){var s=this.snake[i];rr(s.x*cell+1,s.y*cell+1,cell-2,cell-2,4,i===0?'#7cff6b':'#3b9e4a');}}};}

  var FACTORY={fighting:makeFighting,racing:makeRacing,shooter:makeShooter,rhythm:makeRhythm,pinball:makePinball,prize:makeClaw,retro:makeSnake};
  function drawHud(){tx('SCORE '+Math.round(G.score),12,22,15,'#e8ecff','left');if(G.timeLeft!=null)tx(Math.ceil(Math.max(0,G.timeLeft))+'s',W-12,22,15,'#e8ecff','right');else if(G.lives!=null)tx('LIVES '+G.lives,W-12,22,15,'#e8ecff','right');if(G.combo)tx('x'+G.combo,W/2,22,15,'#ffd24a');}
  function drawOver(){X.fillStyle='rgba(5,8,20,0.82)';X.fillRect(0,0,W,H);tx('GAME OVER',W/2,H/2-36,26,'#ffd24a');tx('Score '+Math.round(G.score),W/2,H/2,20,'#fff');if(G.result)tx(G.result,W/2,H/2+30,15,G.result.indexOf('NEW')>=0?'#ff7a18':'#9aa3c0');tx('tap to retry',W/2,H/2+62,12,'#9aa3c0');}
  async function postResult(score){var res=await api('/arcade/play_result','POST',{cabinet_id:curCab.id,score:Math.round(score)});if(res&&!res.error){G.result=res.new_high?('NEW HIGH! 🔥 hot '+res.hot_days+'d'):('High score: '+(res.high_score||0).toLocaleString());if(res.new_high){SFX.ko();curCab.high_score=res.high_score;}await refreshState();renderBusiness();}}
  function loop(t){if(!cv)return;if(!cv.isConnected){quit();return;}var dt=Math.min(0.05,(t-last)/1000);last=t;X.clearRect(0,0,W,H);if(G){if(!G.over)G.update(dt);G.draw();drawHud();if(G.over){if(!G._ann){G._ann=1;SFX.over();postResult(G.score);}drawOver();}}RAF=requestAnimationFrame(loop);}
  function begin(genre){G=(FACTORY[genre]||makeSnake)();G.over=false;G._ann=0;G.result='';}
  function onDown(e){e.preventDefault();ac();cv.focus();var p=logical(e);if(G&&G.over){begin(curCab.genre);return;}if(G&&G.tap)G.tap(p.x,p.y);}
  function onMove(e){if(G&&G.move){var p=logical(e);G.move(p.x,p.y);}}
  function keydown(e){if(!G)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' '].indexOf(e.key)>=0)e.preventDefault();if(keys[e.key])return;keys[e.key]=true;if(G.over&&(e.key===' '||e.key==='Enter')){begin(curCab.genre);return;}if(G.key)G.key(e.key);}
  function keyup(e){keys[e.key]=false;}
  function quit(){if(RAF)cancelAnimationFrame(RAF);RAF=null;if(cv){cv.removeEventListener('pointerdown',onDown);cv.removeEventListener('pointermove',onMove);}window.removeEventListener('keydown',keydown);window.removeEventListener('keyup',keyup);keys={};G=null;cv=null;if(_mg)_mg.locked=false;}

  window.playArcadeCabinet=function(cid){var arc=state.arcade;if(!arc)return;var cab=(arc.cabinets||[]).find(function(c){return c.id===cid;});if(!cab||cab.status==='broken')return;curCab=cab;var gn=ARCADE_GENRE_GAME[cab.genre]||'Arcade Game';
    _mg={locked:true,arcadeGame:true};
    openModal('<div class="modal-handle"></div>'
     +'<div style="font-weight:800;font-size:15px">'+gn+'</div>'
     +'<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px">'+cab.title+' · HI '+(cab.high_score||0).toLocaleString()+' · beat it to go 🔥 hot</div>'
     +'<div style="background:#0d1020;border-radius:10px;overflow:hidden;border:0.5px solid var(--border)"><canvas id="arc-mg" width="400" height="440" tabindex="0" style="display:block;width:100%;height:auto;touch-action:none;outline:none"></canvas></div>'
     +'<div style="font-size:11px;color:var(--text-muted);text-align:center;margin-top:7px;min-height:15px">'+(HINTS[cab.genre]||'')+'</div>'
     +'<button class="btn btn-ghost btn-sm btn-full" style="margin-top:8px" onclick="quitArcadeGame()">Done</button>');
    cv=document.getElementById('arc-mg');X=cv.getContext('2d');
    cv.addEventListener('pointerdown',onDown);cv.addEventListener('pointermove',onMove);
    window.addEventListener('keydown',keydown);window.addEventListener('keyup',keyup);
    begin(cab.genre);cv.focus();ac();last=performance.now();RAF=requestAnimationFrame(loop);};
  window.quitArcadeGame=function(){quit();closeModal();};
})();

function showBuyLaundroMachine() {
  const lm    = state.laundromat;
  if (!lm) return;
  const step  = Math.max(0, lm.machines.length - LAUNDROMAT_START_MACHINES) * LAUNDROMAT_MACHINE_STEP;
  const wcap  = Math.round(lmCapacity(lm.machines, 'wash'));
  const dcap  = Math.round(lmCapacity(lm.machines, 'dry'));
  const rows = Object.entries(LAUNDROMAT_MACHINE_TYPES).map(([key, t]) => {
    const price = t.price + step;
    const canAfford = state.cash >= price;
    const adds = key === 'combo' ? '+16 wash & +16 dry' : key === 'washer' ? '+12 wash capacity' : '+12 dry capacity';
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);border-radius:9px;margin-bottom:8px">
        <div style="font-size:24px">${t.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:13px">${t.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${adds}</div>
        </div>
        <button class="btn btn-sm btn-primary" style="flex-shrink:0" ${canAfford ? `onclick="buyLaundroMachine('${key}')"` : 'disabled'}>${canAfford ? fmt(price) : 'Need cash'}</button>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px">Add a Machine</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">Current capacity — 🌀 ${wcap} wash · 💨 ${dcap} dry. A load needs both; balance them.</div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Cancel</button>`);
}

async function buyLaundroMachine(machineType) {
  const res = await api('/laundromat/buy_machine', 'POST', { machine_type: machineType });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  closeModal();
  await refreshState();
  renderBusiness();
  toast(`${LAUNDROMAT_MACHINE_TYPES[machineType]?.name || 'Machine'} added!`, 'success');
}

async function buyLaundroAddon(key) {
  const res = await api('/laundromat/buy_addon', 'POST', { addon_key: key });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('Add-on installed!', 'success');
}

function showBuyVendingModal() {
  const vms     = state.vending_machines || [];
  const slot    = vms.filter(v => VM_LOCATION_ORDER.includes(v.location_key)).length + 1;
  if (slot > 6) return;
  const price   = VM_PRICES[slot - 1];
  const locKey  = VM_LOCATION_ORDER[slot - 1];
  const loc     = VM_LOCATIONS[locKey];
  const chips   = Object.entries(loc.profile).sort((a, b) => b[1] - a[1])
    .map(([c, w]) => `<span style="font-size:11px;background:var(--surface,var(--card-bg));border:1px solid var(--border);padding:2px 7px">${VM_PRODUCTS[c].icon} ${VM_PRODUCTS[c].name} ${Math.round(w * 100)}%</span>`).join(' ');
  openModal(`
    <div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <img src="/static/icons/business-vending.svg" width="52" height="52" style="flex-shrink:0;image-rendering:pixelated">
      <div>
        <div style="font-weight:800;font-size:15px">Buy Vending Machine #${slot}</div>
        <div style="font-size:11px;color:var(--text-muted)">📍 ${loc.name}</div>
      </div>
    </div>
    <div class="money-row"><span class="mr-label">Purchase Price</span><span class="mr-value" style="color:var(--negative)">${fmt(price)}</span></div>
    <div class="money-row" style="margin-bottom:12px"><span class="mr-label">Your Cash</span><span class="mr-value">${fmt(state.cash)}</span></div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px">This location's demand profile — stock its slots to match:</div>
    <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:14px">${chips}</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">Comes with 6 empty slots. You'll assign products and stock them from CostPro.</div>
    <button class="btn btn-primary btn-full" ${state.cash < price ? 'disabled' : 'onclick="buyVendingMachine()"'}>${state.cash < price ? 'Not Enough Cash' : `Buy — ${fmt(price)}`}</button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Cancel</button>`);
}

function showConfigureSlot(vmId, idx) {
  const vm  = (state.vending_machines || []).find(v => v.id === vmId);
  if (!vm) return;
  const loc    = VM_LOCATIONS[vm.location_key] || { name: '?', profile: {} };
  const inv    = state.costpro_inventory || {};
  const sl     = vm.slots[idx];
  const locked = sl.category && sl.stock > 0.5;   // holding product → must clear to switch
  const rows = Object.entries(VM_PRODUCTS).map(([c, p]) => {
    const have      = Math.round(inv[c] || 0);
    const w         = Math.round((loc.profile[c] || 0) * 100);
    const isCurrent = sl.category === c;
    const accent    = VM_CAT_COLOR[c] || 'var(--border)';
    const match     = w > 0
      ? `<span style="color:var(--positive)">${w}% demand here</span>`
      : `<span style="color:var(--negative)">no demand here</span>`;
    let btn;
    if (isCurrent) {
      btn = have > 0
        ? `<button class="btn btn-sm btn-primary" onclick="configureSlot(${vmId},${idx},'${c}')">Top Up</button>`
        : `<button class="btn btn-sm btn-ghost" onclick="closeModal();navTo('store')">Buy More</button>`;
    } else if (locked) {
      btn = `<button class="btn btn-sm btn-ghost" disabled style="opacity:0.4">🔒</button>`;
    } else if (have === 0) {
      btn = `<button class="btn btn-sm btn-ghost" onclick="closeModal();navTo('store')">Buy</button>`;
    } else {
      btn = `<button class="btn btn-sm btn-primary" onclick="configureSlot(${vmId},${idx},'${c}')">Stock</button>`;
    }
    const dim = (!isCurrent && (locked || have === 0)) ? 'opacity:0.5;' : '';
    return `
      <div style="${dim}display:flex;align-items:center;gap:10px;padding:9px;border:1.5px solid ${isCurrent ? accent : 'var(--border)'};border-radius:9px;margin-bottom:7px">
        ${pxIcon(p.icon, 22)}
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:12px">${p.name}${isCurrent ? ` <span style="font-size:9px;font-weight:700;color:${accent}">● IN SLOT</span>` : ''}<span style="font-weight:400;color:var(--text-muted)"> · $${p.price.toFixed(2)}${p.perishable ? ' · perishable' : ''}</span></div>
          <div style="font-size:10px;margin-top:1px">${match} · <strong>${have}</strong> units in bag</div>
        </div>
        ${btn}
      </div>`;
  }).join('');
  const lockNote = locked
    ? `<div style="font-size:11px;color:var(--text-2);background:var(--surface,var(--card-bg));border:1px solid var(--border);border-radius:8px;padding:8px 10px;margin-bottom:10px">🔒 Holding <strong>${Math.round(sl.stock)} ${VM_PRODUCTS[sl.category].name}</strong>. Top it up, or clear the slot to switch products.</div>`
    : '';
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px">Slot ${idx + 1} · Machine #${vm.slot}</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">📍 ${loc.name}</div>
    ${lockNote}
    ${rows}
    ${sl.category ? `<button class="btn btn-ghost btn-sm btn-full" style="margin-top:2px;color:var(--negative)" onclick="showClearSlotConfirm(${vmId},${idx})">Clear slot</button>` : ''}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Cancel</button>`);
}

function showClearSlotConfirm(vmId, idx) {
  const vm = (state.vending_machines || []).find(v => v.id === vmId);
  if (!vm) return;
  const sl = vm.slots[idx];
  if (!sl.category) return;
  const units = Math.round(sl.stock);
  if (units <= 0) { configureSlot(vmId, idx, 'none'); return; }   // empty — nothing to warn about
  const p = VM_PRODUCTS[sl.category];
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;color:var(--negative)">⚠️ Clear this slot?</div>
    <p style="font-size:13px;color:var(--text-2);margin:10px 2px 16px;line-height:1.55">This dumps the <strong>${units} units of ${p.icon} ${p.name}</strong> still loaded in the slot. That stock is <strong>gone for good</strong> — no refund. You only need to clear it if you want to switch this slot to a different product.</p>
    <button class="btn btn-danger btn-full" onclick="configureSlot(${vmId},${idx},'none')">Clear & lose ${units} units</button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="showConfigureSlot(${vmId},${idx})">Keep it — go back</button>`);
}

async function buyVendingMachine() {
  closeModal();
  const res = await api('/vending/buy', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('Vending machine purchased! Assign products to its slots.', 'success');
}

async function configureSlot(vmId, idx, category) {
  const res = await api('/vending/configure', 'POST', { vm_id: vmId, slot_idx: idx, category });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.restock();
  closeModal();
  await refreshState();
  renderBusiness();
}

async function restockVending(vmId) {
  const res = await api('/vending/restock', 'POST', { vm_id: vmId });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.restock();
  await refreshState();
  renderBusiness();
  toast('Machine topped up from your inventory.', 'success');
}

function showNextVendingEvent() {
  if (_pendingVendingEvents.length === 0) { continueFromEvents(); return; }
  _currentVendingEvent = _pendingVendingEvents.shift();
  showVendingEventModal(_currentVendingEvent);
}

function showVendingEventModal(ev) {
  const cards = ev.choices.map((c, i) => {
    const tag = c.gain > 0 ? `<span class="contractor-cost" style="color:var(--positive)">+${fmt(c.gain)}</span>`
              : c.cost > 0 ? `<span class="contractor-cost">${fmt(c.cost)}</span>`
              : `<span class="contractor-cost" style="color:var(--text-muted)">free</span>`;
    const tooPoor = c.cost > (state.cash || 0);
    return `<div class="contractor-card" style="margin-bottom:8px${tooPoor ? ';opacity:0.45' : ''}" ${tooPoor ? '' : `onclick="resolveVendingEvent(${i})"`}>
      <div class="contractor-header">
        <span class="contractor-name">${c.label}</span>
        ${tooPoor ? `<span class="contractor-cost" style="color:var(--negative)">Need ${fmt(c.cost)}</span>` : tag}
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon)} ${ev.title}</div>
    <div class="modal-subtitle">Machine #${ev.machine_slot}</div>
    <p style="font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.5">${ev.text}</p>
    ${cards}
    ${_pendingVendingEvents.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingVendingEvents.length} more after this</div>` : ''}`);
}

async function resolveVendingEvent(choiceIdx) {
  const ev  = _currentVendingEvent;
  if (!ev) return;
  const res = await api('/vending/event_resolve', 'POST', { machine_id: ev.machine_id, event_key: ev.key, choice_idx: choiceIdx });
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon, 20)} ${ev.title}</div>
    <p style="font-size:14px;color:var(--text-1);margin:10px 4px 16px;line-height:1.55">${res.result}</p>
    <button class="btn btn-primary btn-full" onclick="afterVendingEvent()">
      ${_pendingVendingEvents.length > 0 ? `Next (${_pendingVendingEvents.length})` : 'Done'}
    </button>`);
  await refreshState();
  renderAll();
}

function afterVendingEvent() { showNextVendingEvent(); }

function showNextArcadeEvent() {
  if (_pendingArcadeEvents.length === 0) { continueFromEvents(); return; }
  _currentArcadeEvent = _pendingArcadeEvents.shift();
  showArcadeEventModal(_currentArcadeEvent);
}

function showArcadeEventModal(ev) {
  const cards = ev.choices.map((c, i) => {
    const tag = c.gain > 0 ? `<span class="contractor-cost" style="color:var(--positive)">+${fmt(c.gain)}</span>`
              : c.cost > 0 ? `<span class="contractor-cost">${fmt(c.cost)}</span>`
              : `<span class="contractor-cost" style="color:var(--text-muted)">free</span>`;
    const tooPoor = c.cost > (state.cash || 0);
    return `<div class="contractor-card" style="margin-bottom:8px${tooPoor ? ';opacity:0.45' : ''}" ${tooPoor ? '' : `onclick="resolveArcadeEvent(${i})"`}>
      <div class="contractor-header">
        <span class="contractor-name">${c.label}</span>
        ${tooPoor ? `<span class="contractor-cost" style="color:var(--negative)">Need ${fmt(c.cost)}</span>` : tag}
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon)} ${ev.title}</div>
    <div class="modal-subtitle">The Back-Room Arcade</div>
    <p style="font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.5">${ev.text}</p>
    ${cards}
    ${_pendingArcadeEvents.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingArcadeEvents.length} more after this</div>` : ''}`);
}

async function resolveArcadeEvent(choiceIdx) {
  const ev = _currentArcadeEvent;
  if (!ev) return;
  const res = await api('/arcade/event_resolve', 'POST', { event_key: ev.key, choice_idx: choiceIdx });
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon, 20)} ${ev.title}</div>
    <p style="font-size:14px;color:var(--text-1);margin:10px 4px 16px;line-height:1.55">${res.result}</p>
    <button class="btn btn-primary btn-full" onclick="afterArcadeEvent()">
      ${_pendingArcadeEvents.length > 0 ? `Next (${_pendingArcadeEvents.length})` : 'Done'}
    </button>`);
  await refreshState();
  renderAll();
}

function afterArcadeEvent() { showNextArcadeEvent(); }

function showNextPoleEvent() {
  if (_pendingPoleEvents.length === 0) { continueFromEvents(); return; }
  _currentPoleEvent = _pendingPoleEvents.shift();
  showPoleEventModal(_currentPoleEvent);
}

function showPoleEventModal(ev) {
  const cards = ev.choices.map((c, i) => {
    const tag = c.gain > 0 ? `<span class="contractor-cost" style="color:var(--positive)">+${fmt(c.gain)}</span>`
              : c.cost > 0 ? `<span class="contractor-cost">${fmt(c.cost)}</span>`
              : `<span class="contractor-cost" style="color:var(--text-muted)">free</span>`;
    const tooPoor = c.cost > (state.cash || 0);
    return `<div class="contractor-card" style="margin-bottom:8px${tooPoor ? ';opacity:0.45' : ''}" ${tooPoor ? '' : `onclick="resolvePoleEvent(${i})"`}>
      <div class="contractor-header">
        <span class="contractor-name">${c.label}</span>
        ${tooPoor ? `<span class="contractor-cost" style="color:var(--negative)">Need ${fmt(c.cost)}</span>` : tag}
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon)} ${ev.title}</div>
    <div class="modal-subtitle">Brass Pole Fitness Studio</div>
    <p style="font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.5">${ev.text}</p>
    ${cards}
    ${_pendingPoleEvents.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingPoleEvents.length} more after this</div>` : ''}`);
}

async function resolvePoleEvent(choiceIdx) {
  const ev = _currentPoleEvent;
  if (!ev) return;
  const res = await api('/pole_studio/event_resolve', 'POST', { event_key: ev.key, choice_idx: choiceIdx });
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon, 20)} ${ev.title}</div>
    <p style="font-size:14px;color:var(--text-1);margin:10px 4px 16px;line-height:1.55">${res.result}</p>
    <button class="btn btn-primary btn-full" onclick="afterPoleEvent()">
      ${_pendingPoleEvents.length > 0 ? `Next (${_pendingPoleEvents.length})` : 'Done'}
    </button>`);
  await refreshState();
  renderAll();
}

function afterPoleEvent() { showNextPoleEvent(); }

function showNextCarWashEvent() {
  if (_pendingCarWashEvents.length === 0) { continueFromEvents(); return; }
  _currentCarWashEvent = _pendingCarWashEvents.shift();
  showCarWashEventModal(_currentCarWashEvent);
}

function showCarWashEventModal(ev) {
  const cards = ev.choices.map((c, i) => {
    const tag = c.gain > 0 ? `<span class="contractor-cost" style="color:var(--positive)">+${fmt(c.gain)}</span>`
              : c.cost > 0 ? `<span class="contractor-cost">${fmt(c.cost)}</span>`
              : `<span class="contractor-cost" style="color:var(--text-muted)">free</span>`;
    const tooPoor = c.cost > (state.cash || 0);
    return `<div class="contractor-card" style="margin-bottom:8px${tooPoor ? ';opacity:0.45' : ''}" ${tooPoor ? '' : `onclick="resolveCarWashEvent(${i})"`}>
      <div class="contractor-header">
        <span class="contractor-name">${c.label}</span>
        ${tooPoor ? `<span class="contractor-cost" style="color:var(--negative)">Need ${fmt(c.cost)}</span>` : tag}
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon)} ${ev.title}</div>
    <div class="modal-subtitle">Slippery When Washed</div>
    <p style="font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.5">${ev.text}</p>
    ${cards}
    ${_pendingCarWashEvents.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingCarWashEvents.length} more after this</div>` : ''}`);
}

async function resolveCarWashEvent(choiceIdx) {
  const ev = _currentCarWashEvent;
  if (!ev) return;
  const res = await api('/car_wash/event_resolve', 'POST', { event_key: ev.key, choice_idx: choiceIdx });
  if (res.error) { toast(res.error, 'error'); return; }
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon, 20)} ${ev.title}</div>
    <p style="font-size:14px;color:var(--text-1);margin:10px 4px 16px;line-height:1.55">${res.result}</p>
    <button class="btn btn-primary btn-full" onclick="afterCarWashEvent()">
      ${_pendingCarWashEvents.length > 0 ? `Next (${_pendingCarWashEvents.length})` : 'Done'}
    </button>`);
  await refreshState();
  renderAll();
}

function afterCarWashEvent() { showNextCarWashEvent(); }

async function setVmPrice(vmId, level) {
  const res = await api('/vending/set_price', 'POST', { vm_id: vmId, level });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle();
  await refreshState();
  renderBusiness();
}

function showVmUpgrades(vmId) {
  const vm = (state.vending_machines || []).find(v => v.id === vmId);
  if (!vm) return;
  const ups = vm.upgrades || {};
  const rows = VM_UPGRADES_META.map(u => {
    const owned     = !!ups[u.key];
    const canAfford = state.cash >= u.cost;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--border);border-radius:9px;margin-bottom:8px${owned ? ';opacity:0.6' : ''}">
        <div style="font-size:22px">${u.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:12px">${u.name}</div>
          <div style="font-size:10px;color:var(--text-muted)">${u.desc}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          ${owned
            ? `<span style="font-size:11px;color:var(--positive)">✓ Installed</span>`
            : `<div style="font-size:12px;font-weight:800">${fmt(u.cost)}</div>
               <button class="btn btn-sm btn-primary" style="margin-top:2px" ${canAfford ? `onclick="buyVmUpgrade(${vmId},'${u.key}')"` : 'disabled'}>${canAfford ? 'Install' : 'Need Cash'}</button>`}
        </div>
      </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px">Machine #${vm.slot} · Upgrades</div>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:12px">One-time per machine. Permanent.</div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Close</button>`);
}

async function buyVmUpgrade(vmId, key) {
  const res = await api('/vending/upgrade', 'POST', { vm_id: vmId, upgrade_key: key });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
  closeModal();
  await refreshState();
  renderBusiness();
  toast('Upgrade installed!', 'success');
}

async function toggleGrandma() {
  const res = await api('/vending/toggle_grandma', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle();
  await refreshState();
  renderBusiness();
  toast(state.grandma_hired ? 'Grandma is on the case! 🧺' : 'Grandma hangs up her shopping bags.', 'info');
}

async function setGrandmaBudget(budget) {
  const res = await api('/vending/set_grandma_budget', 'POST', { budget });
  if (res.error) { toast(res.error, 'error'); return; }
  await refreshState();
  renderBusiness();
}

async function toggleVinny() {
  const res = await api('/vending/toggle_vinny', 'POST', {});
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle();
  await refreshState();
  renderBusiness();
  toast(state.vinny_hired ? 'Cousin Vinny is on the job!' : 'Vinny has been let go.', 'info');
}

// ── Brass Pole Fitness Studio ─────────────────────────────────────────────────
const POLE_STUDIO_PRICE = 600000;

const PS_DANCERS = {
  celestia: { name: 'Celestia', icon: '💫', specialty: 'Advanced Technique',
    desc: "The studio's founding instructor. Chose the name 'Celestia' in 2019 after a spiritual awakening. The awakening was a Pilates class." },
  raven:    { name: 'Raven',    icon: '🖤', specialty: 'Competitive Performance',
    desc: "Former competitor on a circuit she describes as 'very prestigious and real.' The trophies are in her car." },
  sunshine: { name: 'Sunshine', icon: '☀️', specialty: 'Beginner & Senior Wellness',
    desc: "Three separate Yelp reviews have called her 'aggressively wholesome.' She considers this a compliment." },
  mercedes: { name: 'Mercedes', icon: '💼', specialty: 'Corporate & Private Sessions',
    desc: "Holds an MBA. Books all her own clients. Sends follow-up emails. The emails are extremely professional." },
  diamond:  { name: 'Diamond',  icon: '💎', specialty: 'Late Night & Special Events',
    desc: "Claims to have performed at three celebrity events. All three are unverifiable. The stories are incredible." },
  gary:     { name: 'Gary',     icon: '🤷', specialty: 'Tuesday Mornings',
    desc: "His qualifications are unclear. The Tuesday 9am slot has a 3-month waitlist. He just shrugs." },
};

const PS_UPGRADES = {
  chrome_polish: { name: 'Chrome Polish Kit', icon: '✨', cost: 2000, desc: 'Cuts bend chance in half.' },
  led_halo:      { name: 'LED Halo Lighting', icon: '💡', cost: 2500, desc: '+20% income from this pole.' },
  grip_coating:  { name: 'Grip Coating',      icon: '💪', cost: 1500, desc: '+10% income, grip spray lasts 10 days.' },
};

const PS_STAFF = {
  vibe_manager:   { name: 'Vibe Manager',   icon: '🎶', cost: 200, desc: 'Keeps the music & lighting going so Atmosphere never tanks (atmosphere boosts class income + satisfaction).' },
  studio_cleaner: { name: 'Studio Cleaner', icon: '🧹', cost: 175, desc: 'Auto-cleans the studio so Cleanliness stays high.' },
  manager:        { name: 'Studio Manager', icon: '📋', cost: 225, desc: 'Auto-handles demands, fills empty class slots, restocks the Kombucha Bar, AND resolves studio events (bookings, inspections, drama) — fully hands-off.' },
  host:           { name: 'Front Desk Host', icon: '🛎️', cost: 160, desc: 'Greets & checks members in — lifts satisfaction and cuts member churn.' },
  bartender:      { name: 'Bartender',       icon: '🍸', cost: 170, desc: 'Works the Kombucha Bar. No bartender = the bar earns nothing.' },
};
// Class types: seats (capacity), pop (demand pull), rev ($/head), equip needed, and the parody flavor.
const PS_CLASSES = {
  intro:   { name: 'Intro Pole',           icon: '🌱', seats: 14, pop: 1.4, rev: 7,  equip: 'pole',  desc: 'Packed beginner classes. High volume, low $/head.' },
  levels:  { name: 'Pole Levels',          icon: '🔥', seats: 10, pop: 1.0, rev: 11, equip: 'pole',  desc: 'The bread & butter. Steady, solid earners.' },
  silks:   { name: 'Aerial Silks',         icon: '🎀', seats: 8,  pop: 0.7, rev: 16, equip: 'silks', desc: 'Niche but premium. Needs the Aerial Silks Rig.' },
  flex:    { name: 'Flexibility & Stretch',icon: '🧘', seats: 16, pop: 1.1, rev: 6,  equip: 'floor', desc: 'Popular, low equipment. Fills easily.' },
  private: { name: 'Private Session',       icon: '🥂', seats: 2,  pop: 0.5, rev: 70, equip: 'vip',   desc: 'The "private dance." Tiny class, huge $/head. Needs the VIP Suite & VIP members.' },
  open:    { name: 'Open Practice',         icon: '🕒', seats: 12, pop: 0.6, rev: 5,  equip: 'floor', desc: 'Low-key open floor. Modest, easy income.' },
};
const PS_SPECIALTY_CLASS = { sunshine: 'intro', celestia: 'levels', raven: 'silks', mercedes: 'private', diamond: 'flex', gary: 'open' };
const PS_FACILITIES = {
  silks_rig:    { name: 'Aerial Silks Rig',  icon: '🎀', cost: 30000, desc: 'Unlocks Aerial Silks classes.' },
  vip_suite:    { name: 'VIP Suite',          icon: '🥂', cost: 55000, desc: 'The "Champagne Room." Unlocks Private Sessions + VIP memberships.' },
  stage:        { name: 'Performance Stage',  icon: '🎤', cost: 40000, desc: 'Host Theme Nights for big one-off payouts.' },
  lobby:        { name: 'Comfy Lobby Lounge', icon: '🛋️', cost: 22000, desc: '+satisfaction & retention.' },
  dj_booth:     { name: 'Resident DJ Booth',  icon: '🪩', cost: 26000, desc: 'Mood lighting + sound — keeps Atmosphere high automatically.' },
  kombucha_bar: { name: 'Kombucha Bar',       icon: '🥂', cost: 24000, desc: 'The "bar." Hire a bartender & stock kombucha from CostPro for extra income.' },
};
const PS_KOMBUCHA = ['kb_ginger', 'kb_hibiscus', 'kb_charcoal', 'kb_cbd', 'kb_sparkle'];
const COSTPRO_KOMBUCHA_ICON = { kb_ginger: '🫚', kb_hibiscus: '🌺', kb_charcoal: '🖤', kb_cbd: '😌', kb_sparkle: '🥂' };

const PS_DEMAND_TEXT = {
  cel_warmup:     "I'd like a warm-up area near my pole. A yoga mat and a foam roller.",
  cel_title:      "I'd like to be listed as Lead Instructor on all studio materials.",
  cel_showcase:   "I think we should host a quarterly showcase. I'll organize everything.",
  cel_locker:     "I'd like a private locker.",
  cel_salary:     "I've been here since the beginning. I think it's time we discussed a salary review.",
  cel_photo:      "The studio photo on the website is from 2019. I'm in it, but barely.",
  cel_mentorship: "I'd like to offer a mentorship program for the newer dancers.",
  cel_coffee:     "The break room needs a proper coffee machine. Not instant.",
  rav_rechrome:   "My pole needs re-chroming. This week.",
  rav_slot:       "I want the 7pm slot. That's my time.",
  rav_comp_off:   "I entered a regional competition. I need Friday off.",
  rav_sound:      "The sound system needs to be replaced.",
  rav_billing:    "I want top billing on all promotional material. My name first.",
  rav_vegas:      "There's a competition in Vegas. I need four days and $500 toward travel.",
  rav_sponsor:    "I've been offered a grip spray sponsorship. You get 20% of the deal.",
  rav_ultimatum:  "I've had an offer from Chromatic Fitness. Match what I'm worth or I go.",
  sun_shelter:    "Could we host a free class for the women's shelter? I hope that's okay to ask.",
  sun_microwave:  "Could we get a microwave for the break room? The paper cups are a little sad.",
  sun_bday:       "One of my seniors is turning 80. Could the studio host her party? Just the space.",
  sun_cert:       "Could the studio cover half of my certification? I'd pay the rest myself.",
  sun_junior:     "Could we offer junior fitness classes? For kids? You can absolutely say no.",
  sun_fundraiser: "There's a local fitness fundraiser. Could the studio sponsor a table?",
  sun_benefit:    "My student broke her wrist. She can't afford the bills. Could the studio do a benefit class?",
  sun_pizza:      "Could we do a staff appreciation thing? Just pizza and an hour together.",
  mer_commission: "I've drafted a corporate expansion proposal. 10% commission on sessions I book.",
  mer_raise:      "I've been approached with an outside contract. I'd like to discuss a counter-offer.",
  mer_lighting:   "The changing room lighting needs upgrading for client-facing areas.",
  mer_retainer:   "Authorization to offer a corporate client a 15% retainer discount.",
  mer_booking_line:"I'd like a dedicated booking line for private and corporate inquiries.",
  mer_lunchtime:  "I've identified an underserved market: lunchtime express classes for office workers.",
  mer_events_title:"I'd like the title 'Events Director' for private booking conversations. It helps close deals.",
  mer_expense:    "I've been paying for client entertainment out of pocket. I'd like expense reimbursement.",
  dia_fog:        "I need the fog machine. You know why.",
  dia_event_night:"I've been offered a private event Saturday night. I need the night.",
  dia_journalist: "A journalist wants to interview me about my journey. The studio should be featured.",
  dia_aesthetic:  "The late-night aesthetic needs a complete rethink. New lighting, new music, new everything.",
  dia_drapes:     "The entrance needs to feel different. Not bad. Just... different. Drapes, maybe. Something velvet.",
  dia_miami:      "I've been offered a performance in Miami. I need a long weekend.",
  dia_rename:     "I want to rename my late-night class. 'Midnight Ascension.' I have other options.",
  dia_soundbath:  "There's an energy in the studio this week. Not good. We need a deep clean and a sound bath.",
  gary_mug:       "Hey, is it okay if I bring my own mug? The paper cups bother me.",
  gary_start_time:"Any chance Tuesday could start 10 minutes later? No rush.",
  gary_music:     "Could the playlist have a little classic rock sometimes? Just a thought.",
  gary_plant:     "Is it alright if I put a small plant on the windowsill near my pole?",
  gary_jacket:    "Someone left a jacket in Tuesday class three weeks ago. Should I donate it?",
  gary_raven:     "This might not be my place — but Raven seems stressed lately. Is she okay?",
};

const PS_REP_TIERS = [
  { min: 0,  label: 'Unknown',      color: '#888' },
  { min: 20, label: 'Local Gem',    color: '#4CAF50' },
  { min: 40, label: 'Trending',     color: '#2196F3' },
  { min: 60, label: 'Established',  color: '#9C27B0' },
  { min: 80, label: 'Iconic',       color: '#FF9800' },
];

function _psRepTier(rep) {
  let t = PS_REP_TIERS[0];
  for (const tier of PS_REP_TIERS) { if (rep >= tier.min) t = tier; }
  return t;
}

function dancerPixelArt(key, hired) {
  const isGary = key === 'gary';
  if (!hired) {
    return `<svg viewBox="0 0 40 70" xmlns="http://www.w3.org/2000/svg" width="30" height="52" style="flex-shrink:0;opacity:0.3">
      <rect x="18" y="0" width="4" height="70" fill="#546E7A"/>
      <rect x="19.2" y="0" width="1.2" height="70" fill="white" opacity="0.2"/>
    </svg>`;
  }
  if (isGary) {
    return `<svg viewBox="0 0 40 70" xmlns="http://www.w3.org/2000/svg" width="30" height="52" style="flex-shrink:0">
      <rect x="18" y="0" width="4" height="70" fill="#90A4AE"/>
      <rect x="19.2" y="0" width="1.2" height="70" fill="white" opacity="0.35"/>
      <text x="7" y="55" font-size="12" class="ps-rise-1">✨</text>
      <text x="23" y="44" font-size="10" class="ps-rise-2">⭐</text>
      <text x="5" y="38" font-size="8" class="ps-rise-3">✦</text>
      <text x="27" y="50" font-size="9" class="ps-rise-2">✨</text>
    </svg>`;
  }
  return `<svg viewBox="0 0 40 70" xmlns="http://www.w3.org/2000/svg" width="30" height="52" style="flex-shrink:0">
    <rect x="18" y="0" width="4" height="64" fill="#CFD8DC"/>
    <rect x="19.2" y="0" width="1.2" height="64" fill="white" opacity="0.4"/>
    <polygon points="10,2 30,2 38,60 2,60" fill="#FFD700" opacity="0.06"/>
    <line x1="8" y1="5" x2="3" y2="60" stroke="#FFD700" stroke-width="0.7" opacity="0.2"/>
    <line x1="16" y1="3" x2="15" y2="60" stroke="#FFD700" stroke-width="0.6" opacity="0.13"/>
    <line x1="24" y1="3" x2="25" y2="60" stroke="#FFD700" stroke-width="0.6" opacity="0.13"/>
    <line x1="32" y1="5" x2="37" y2="60" stroke="#FFD700" stroke-width="0.7" opacity="0.2"/>
    <ellipse cx="20" cy="60" rx="17" ry="4.5" fill="#FFD700" class="ps-spot-a"/>
    <ellipse cx="20" cy="60" rx="10" ry="3" fill="#FFD700" class="ps-spot-b"/>
    <ellipse cx="20" cy="60" rx="4" ry="1.5" fill="#FFD700" class="ps-spot-c"/>
  </svg>`;
}

function renderPoleStudioContent() {
  const ps = state.pole_studio;
  const inv = state.costpro_inventory || {};

  if (!ps || !ps.owned) {
    return `
      <div style="padding:16px 0;text-align:center">
        <div style="font-size:64px;line-height:1;margin:0 auto 10px">💃</div>
        <div style="font-size:15px;font-weight:700;color:#E8D5F5;margin-bottom:4px">Brass Pole Fitness Studio</div>
        <div style="font-size:12px;color:#C4A8E0;margin-bottom:16px">6 poles. 6 dancers. One very confused Gary.</div>
        <button class="btn-primary" onclick="psBuy()" style="background:#7B2D8B;border:none;color:#E8D5F5;padding:10px 24px;font-size:14px;cursor:pointer">
          Purchase Studio — $${POLE_STUDIO_PRICE.toLocaleString()}
        </button>
      </div>`;
  }

  const dancers = ps.dancers || {};
  const poles   = ps.poles || [];
  const staff   = ps.staff || {};
  const facs    = ps.facilities || {};
  const kb      = ps.kombucha || {};
  const demands = ps.active_demands || [];
  const repTier = _psRepTier(ps.reputation || 0);
  const currentDay = state.day || 0;
  const members = Math.round(ps.members || 0);
  const vip     = Math.round(ps.vip_members || 0);
  const sat     = Math.round(ps.satisfaction || 0);
  const PURP = '#BB86FC', GREEN = '#4CAF50', AMBER = '#FF9800', RED = '#FF5252';

  function meter(label, val, color, warn) {
    const pct = Math.round(val);
    const barColor = pct < (warn || 0) ? '#e74c3c' : color;
    return `<div style="margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;font-size:11px;color:#C4A8E0;margin-bottom:2px"><span>${label}</span><span>${pct}%</span></div>
      <div style="background:#3A1A4A;height:8px;border-radius:4px;overflow:hidden"><div style="width:${pct}%;height:100%;background:${barColor};border-radius:4px"></div></div></div>`;
  }
  function hdr(t) { return `<div style="font-size:11px;font-weight:700;color:${PURP};text-transform:uppercase;letter-spacing:1px;margin:14px 0 8px">${t}</div>`; }
  function equipOk(eq) { return eq === 'silks' ? !!facs.silks_rig : eq === 'vip' ? !!facs.vip_suite : true; }

  // ── Dancer requests are answered by tapping the flagged instructor below ──
  const demandByDancer = {};
  demands.forEach(d => { demandByDancer[d.dancer] = d; });
  const demandNote = demands.length
    ? `<div style="background:#3A1A4A;border:1px solid ${AMBER};border-radius:6px;padding:9px;margin-bottom:10px;font-size:11px;color:#E8D5F5">💬 ${demands.length} instructor${demands.length > 1 ? 's have' : ' has'} a request — tap the flagged instructor below to answer.</div>`
    : '';

  // ── Class schedule (live, explained) ──
  const slotCap = ps.slot_count || 2;
  const slots   = (ps.slots || []);
  slots.forEach(sl => {
    const ct = PS_CLASSES[sl.type], dd = dancers[sl.instructor];
    sl._ok = !!ct && dd && dd.hired && equipOk(ct.equip) && (dd.energy == null || dd.energy >= 12);
  });
  const dailyDemand = (members + vip) * 0.5;
  const popTotal = slots.filter(s => s._ok && s.type !== 'private').reduce((a, s) => a + PS_CLASSES[s.type].pop, 0) || 1;
  const slotCards = slots.slice(0, slotCap).map((sl, i) => {
    const ct = PS_CLASSES[sl.type] || PS_CLASSES.open;
    const dm = sl.instructor ? PS_DANCERS[sl.instructor] : null;
    const seats = ct.seats;
    let status, scol, sub = '';
    if (!sl.instructor) { status = 'Empty — tap to assign an instructor'; scol = '#9B7BB8'; }
    else if (!sl._ok) {
      if (ct.equip === 'silks' && !facs.silks_rig) { status = '⚠ Needs Aerial Silks Rig'; scol = RED; }
      else if (ct.equip === 'vip' && !facs.vip_suite) { status = '⚠ Needs VIP Suite'; scol = RED; }
      else if (dancers[sl.instructor] && (dancers[sl.instructor].energy || 0) < 12) { status = '😴 Instructor exhausted — class cancelled'; scol = RED; }
      else { status = '⚠ Not running'; scol = RED; }
    } else {
      const onSpec = PS_SPECIALTY_CLASS[sl.instructor] === sl.type;
      const want = sl.type === 'private' ? vip * 0.7 : dailyDemand * (ct.pop / popTotal);
      const fill = Math.min(seats, want);
      const est  = Math.round(fill * ct.rev * (onSpec ? 1.4 : 0.75));
      status = onSpec ? `★ ${dm.name}'s specialty — +40% income` : `${dm.name} is off her lane — −25% income`;
      scol = onSpec ? GREEN : AMBER;
      sub = `~${Math.round(fill)}/${seats} attending${want > seats ? ' · waitlist!' : ''} · ~$${est}/day`;
    }
    return `<div onclick="showPsSlotConfig(${i})" style="background:#2A1035;border:1px solid #7B2D8B;border-radius:6px;padding:9px 10px;margin-bottom:6px;cursor:pointer">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:18px">${ct.icon}</span>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:12px">${ct.name}${dm ? ` · ${dm.icon} ${dm.name}` : ''}</div>
          <div style="font-size:10px;color:${scol};margin-top:1px">${status}</div>
          ${sub ? `<div style="font-size:10px;color:#C4A8E0">${sub}</div>` : ''}
        </div>
        <span style="color:#9B7BB8;font-size:13px">›</span>
      </div></div>`;
  }).join('');

  // ── Instructors roster ──
  const dancerKeys = Object.keys(PS_DANCERS);
  const hiredCount = dancerKeys.filter(k => (dancers[k] || {}).hired).length;
  const assignedTo = {};
  slots.slice(0, slotCap).forEach(sl => { if (sl.instructor) assignedTo[sl.instructor] = PS_CLASSES[sl.type]; });
  const dancerCards = dancerKeys.filter(dk => (dancers[dk] || {}).hired).map(dk => {
    const dd = dancers[dk] || {}, dm = PS_DANCERS[dk], isGary = dk === 'gary';
    const starOf = PS_CLASSES[PS_SPECIALTY_CLASS[dk]];
    const energy = Math.round(dd.energy != null ? dd.energy : 100);
    const eCol = energy < 25 ? RED : energy < 55 ? AMBER : GREEN;
    const moodPct = isGary ? 72 : Math.round(dd.mood || 0);
    const mCol = moodPct < 30 ? RED : moodPct < 60 ? AMBER : GREEN;
    const teaching = assignedTo[dk];
    const pepUsed = dd.pep_day === currentDay;
    const dem = demandByDancer[dk];
    const demColor = dem ? (dem.days_left <= 2 ? RED : AMBER) : '#7B2D8B';
    return `<div style="background:#2A1035;border:1px solid ${demColor};padding:9px;margin-bottom:6px;border-radius:6px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        ${dancerPixelArt(dk, true)}
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:12px">${dm.name}</div>
          <div style="font-size:10px;color:#9B7BB8">★ ${starOf.icon} ${starOf.name}${teaching ? ` · now: ${teaching.icon} ${teaching.name}` : ' · unassigned'}</div>
        </div>
        ${!isGary && !pepUsed ? `<button onclick="psPepTalk('${dk}')" style="background:#5A2D7A;border:none;color:#E8D5F5;padding:4px 8px;font-size:10px;cursor:pointer;border-radius:3px">💬 Pep ⚡3</button>` : ''}
        <button onclick="psFireDancer('${dk}')" style="background:none;border:1px solid #5A2D7A;color:#9B7BB8;padding:4px 8px;font-size:10px;cursor:pointer;border-radius:3px">✕</button>
      </div>
      ${dem ? `<button onclick="showPsDemand('${dk}')" style="width:100%;background:${demColor};border:none;color:#1A0826;font-weight:700;padding:7px;font-size:11px;cursor:pointer;border-radius:4px;margin-bottom:6px">💬 ${dm.name} has a request — tap to answer (${dem.days_left}d left)</button>` : ''}
      <div style="display:flex;gap:10px">
        <div style="flex:1"><div style="display:flex;justify-content:space-between;font-size:9px;color:#C4A8E0"><span>Energy</span><span style="color:${eCol}">${energy}%</span></div>
          <div style="background:#3A1A4A;height:5px;border-radius:3px;overflow:hidden"><div style="width:${energy}%;height:100%;background:${eCol}"></div></div></div>
        <div style="flex:1"><div style="display:flex;justify-content:space-between;font-size:9px;color:#C4A8E0"><span>Mood</span><span style="color:${mCol}">${moodPct}%</span></div>
          <div style="background:#3A1A4A;height:5px;border-radius:3px;overflow:hidden"><div style="width:${moodPct}%;height:100%;background:${mCol}"></div></div></div>
      </div></div>`;
  }).join('') || `<div style="font-size:11px;color:#9B7BB8;text-align:center;padding:8px 0">No instructors hired yet — tap "Hire Instructors" below.</div>`;

  // ── Kombucha bar ──
  let barHtml = '';
  if (facs.kombucha_bar) {
    const hasBartender = !!staff.bartender;
    const stocked = PS_KOMBUCHA.filter(k => (kb[k] || 0) > 0);
    barHtml = hdr('🥂 Kombucha Bar') + `<div style="background:#2A1035;border:1px solid #7B2D8B;border-radius:6px;padding:10px;margin-bottom:6px">
      <div style="font-size:11px;color:${hasBartender ? GREEN : RED};margin-bottom:6px">${hasBartender ? '🍸 Bartender on duty — bar is open.' : '⚠ Hire a Bartender (Staff) — the bar is closed without one.'}</div>
      <div style="font-size:11px;color:#C4A8E0;margin-bottom:8px">Stocked: ${stocked.length ? stocked.map(k => COSTPRO_KOMBUCHA_ICON[k] + ' ' + (kb[k]) + 'd').join('  ') : '<span style="color:'+AMBER+'">nothing — bar earns $0</span>'}</div>
      <button onclick="navTo('store')" style="background:#7B2D8B;border:none;color:#E8D5F5;padding:6px 12px;font-size:11px;cursor:pointer;border-radius:3px">🛒 Stock kombucha at CostPro</button>
    </div>`;
  }

  // ── Upgrades / facilities ──
  const facHtml = Object.entries(PS_FACILITIES).map(([key, f]) => {
    const owned = !!facs[key];
    return `<div style="display:flex;align-items:center;gap:8px;padding:8px;background:#2A1035;border:1px solid ${owned ? GREEN : '#5A2D7A'};margin-bottom:6px;border-radius:6px${owned ? ';opacity:0.7' : ''}">
      <span style="font-size:18px">${f.icon}</span>
      <div style="flex:1;font-size:11px"><div style="font-weight:700">${f.name}</div><div style="color:#9B7BB8">${f.desc}</div></div>
      ${owned ? `<span style="font-size:10px;color:${GREEN};font-weight:700">✓ Installed</span>`
              : `<button onclick="psBuyFacility('${key}')" style="background:#7B2D8B;border:none;color:#E8D5F5;padding:5px 9px;font-size:11px;cursor:pointer;border-radius:3px;white-space:nowrap">$${f.cost.toLocaleString()}</button>`}
    </div>`;
  }).join('');

  // ── Staff ──
  const staffHtml = Object.entries(PS_STAFF).map(([role, meta]) => {
    const hired = staff[role];
    return `<div style="display:flex;align-items:center;gap:8px;padding:8px;background:#2A1035;border:1px solid #5A2D7A;margin-bottom:6px;border-radius:6px">
      <span style="font-size:18px">${meta.icon}</span>
      <div style="flex:1;font-size:11px"><div style="font-weight:700">${meta.name}${hired ? ' <span style="color:'+GREEN+'">🟢</span>' : ''}</div><div style="color:#9B7BB8">${meta.desc}</div></div>
      ${hired ? `<button onclick="psFireStaff('${role}')" style="background:none;border:1px solid #5A2D7A;color:#9B7BB8;padding:4px 8px;font-size:10px;cursor:pointer;border-radius:3px">Let Go</button>`
              : `<button onclick="psHireStaff('${role}')" style="background:#7B2D8B;border:none;color:#E8D5F5;padding:4px 8px;font-size:11px;cursor:pointer;border-radius:3px;white-space:nowrap">$${meta.cost}/day</button>`}
    </div>`;
  }).join('');

  const SLOT_PRICES = [16000, 24000, 33000, 44000, 57000, 72000];
  const themeReady = (ps.theme_until || 0) <= currentDay;
  const buySlotBtn = slotCap < 8
    ? `<button onclick="psBuySlot()" style="width:100%;background:#3A1A4A;border:2px dashed #7B2D8B;color:${PURP};padding:9px;font-size:12px;cursor:pointer;margin:2px 0 6px;border-radius:6px">➕ Build New Pole — $${(SLOT_PRICES[slotCap - 2] || SLOT_PRICES[SLOT_PRICES.length - 1]).toLocaleString()}</button>`
    : `<div style="font-size:11px;color:#9B7BB8;text-align:center;margin-bottom:6px">Max 8 poles reached.</div>`;

  return `<div style="background:#1A0826;color:#E8D5F5;padding:12px;margin:-14px -14px 0;border-bottom:2px solid #5A2D7A">
    ${demandNote}

    <div style="display:flex;gap:8px;margin-bottom:10px">
      <div style="flex:1;background:#2A1035;border:1px solid #5A2D7A;border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:#2196F3">${members}</div><div style="font-size:10px;color:#9B7BB8">Members</div></div>
      ${facs.vip_suite ? `<div style="flex:1;background:#2A1035;border:1px solid #5A2D7A;border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:#FFD24A">${vip}</div><div style="font-size:10px;color:#9B7BB8">VIP</div></div>` : ''}
      <div style="flex:1;background:#2A1035;border:1px solid #5A2D7A;border-radius:6px;padding:8px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:${sat < 40 ? RED : GREEN}">${sat}%</div><div style="font-size:10px;color:#9B7BB8">Satisfaction</div></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 12px;margin-bottom:8px">
      <div>${meter('Atmosphere', ps.atmosphere || 0, PURP, 45)}${meter('Cleanliness', ps.cleanliness || 0, GREEN, 50)}</div>
      <div>${meter('Reputation', ps.reputation || 0, AMBER, 0)}
        <div style="font-size:10px;color:#C4A8E0;margin-top:6px">🎭 <span style="color:${repTier.color};font-weight:700">${repTier.label}</span> · 💰 $${(ps.total_earned || 0).toLocaleString()} earned</div></div>
    </div>

    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px">
      <button onclick="psClean()" style="background:#5A2D7A;border:none;color:#E8D5F5;padding:6px 11px;font-size:11px;cursor:pointer;border-radius:3px">🧹 Clean ($100·⚡4)</button>
      <button onclick="psHype()" style="background:#5A2D7A;border:none;color:#E8D5F5;padding:6px 11px;font-size:11px;cursor:pointer;border-radius:3px">🪩 Hype Vibe ($120·⚡3)</button>
      <button onclick="psMarketing()" style="background:#5A2D7A;border:none;color:#E8D5F5;padding:6px 11px;font-size:11px;cursor:pointer;border-radius:3px">📣 Marketing ($2.5k)</button>
      ${facs.stage ? (themeReady
        ? `<button onclick="psThemeNight()" style="background:#A855F7;border:none;color:#fff;padding:6px 11px;font-size:11px;cursor:pointer;border-radius:3px">🎤 Theme Night ($1.2k·⚡4)</button>`
        : `<span style="padding:6px 11px;font-size:11px;color:#9B7BB8;background:#2A1035;border:1px solid #5A2D7A;border-radius:3px">🎤 Stage resets in ${(ps.theme_until||0)-currentDay}d</span>`) : ''}
      <button onclick="psToggleInsurance()" style="background:${ps.insurance ? '#5A2D7A' : '#2A1035'};border:1px solid #5A2D7A;color:${ps.insurance ? '#E8D5F5' : '#9B7BB8'};padding:6px 11px;font-size:11px;cursor:pointer;border-radius:3px">🛡️ Insurance ${ps.insurance ? 'On' : 'Off'}</button>
    </div>

    ${hdr(`📅 Class Schedule (${slots.slice(0, slotCap).filter(s => s._ok).length}/${slotCap} running)`)}
    <div style="font-size:10px;color:#9B7BB8;margin-bottom:8px">Tap a slot to set its class & instructor. Matching an instructor to her specialty (★) earns the most; demand fills the seats.</div>
    ${slotCards}${buySlotBtn}

    ${hdr(`🧍 Instructors (${hiredCount} hired)`)}
    ${dancerCards}
    <button onclick="showHireInstructors()" style="width:100%;background:#A855F7;border:none;color:#fff;padding:10px;font-size:13px;font-weight:700;cursor:pointer;margin:4px 0 6px;border-radius:6px">➕ Hire Instructors</button>

    ${barHtml}
    ${hdr('🏗️ Upgrades')}${facHtml}
    ${hdr('👔 Staff')}${staffHtml}
  </div>`;
}

async function psBuy() {
  const r = await api('/pole_studio/buy', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('Brass Pole Fitness Studio acquired! 🎪', 'success');
}

async function psBuySlot() {
  const r = await api('/pole_studio/buy_slot', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('New class slot added — schedule a class!', 'success');
}

function showHireInstructors() {
  const ps = state.pole_studio; if (!ps) return;
  const dancers = ps.dancers || {};
  const rows = Object.keys(PS_DANCERS).map(dk => {
    const dm = PS_DANCERS[dk], hired = (dancers[dk] || {}).hired;
    const starOf = PS_CLASSES[PS_SPECIALTY_CLASS[dk]];
    return `<div style="background:${hired ? '#241036' : '#2A1035'};border:1px solid ${hired ? '#4CAF50' : '#5A2D7A'};border-radius:6px;padding:9px;margin-bottom:6px;display:flex;align-items:center;gap:8px${hired ? ';opacity:0.75' : ''}">
      ${dancerPixelArt(dk, hired)}
      <div style="flex:1;min-width:0">
        <div style="font-weight:700;font-size:12px;color:#E8D5F5">${dm.name} <span style="font-size:10px;color:#C4A8E0">★ ${starOf.icon} ${starOf.name}</span></div>
        <div style="font-size:10px;color:#9B7BB8;font-style:italic">${dm.desc}</div>
      </div>
      ${hired ? `<span style="font-size:11px;color:#4CAF50;font-weight:700;white-space:nowrap">✓ On staff</span>`
              : `<button onclick="psHireDancer('${dk}')" style="background:#A855F7;border:none;color:#fff;padding:7px 14px;font-size:12px;font-weight:700;cursor:pointer;border-radius:3px">Hire</button>`}
    </div>`;
  }).join('');
  openModal(`<div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;color:#E8D5F5">Hire Instructors</div>
    <div style="font-size:11px;color:#C4A8E0;margin-bottom:10px">Hire as many as you like — they only earn once you schedule them into a class. Each is the ★ star of one class type.</div>
    ${rows}
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:4px" onclick="closeModal()">Done</button>`);
}

async function psHireDancer(dk) {
  const r = await api('/pole_studio/hire_dancer', 'POST', { dancer: dk });
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.hire();
  await refreshState();
  renderBusiness();
  showHireInstructors();   // refresh the hire list in place
  toast(`${PS_DANCERS[dk].name} ${PS_DANCERS[dk].icon} joins the studio!`, 'success');
}

function psFireDancer(dk) {
  const d = PS_DANCERS[dk];
  openModal(`
    <div class="modal-handle"></div>
    <div style="background:#1A0826;padding:16px">
      <div style="font-size:22px;text-align:center;margin-bottom:8px">${d.icon}</div>
      <div style="font-size:14px;font-weight:700;color:#E8D5F5;text-align:center;margin-bottom:6px">Let ${d.name} go?</div>
      <div style="font-size:12px;color:#C4A8E0;text-align:center;margin-bottom:16px">Any class they teach will be left unassigned.</div>
      <div style="display:flex;gap:8px">
        <button onclick="closeModal()" style="flex:1;background:#3A1A4A;border:1px solid #5A2D7A;color:#9B7BB8;padding:10px;font-size:13px;cursor:pointer;border-radius:3px">Keep</button>
        <button onclick="_psFireDancerConfirmed('${dk}')" style="flex:1;background:#e74c3c;border:none;color:white;padding:10px;font-size:13px;font-weight:700;cursor:pointer;border-radius:3px">Let Go</button>
      </div>
    </div>`);
}

async function _psFireDancerConfirmed(dk) {
  closeModal();
  const r = await api('/pole_studio/fire_dancer', 'POST', { dancer: dk });
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(`${PS_DANCERS[dk].name} has left.`, 'info');
}

async function psClean() {
  const r = await api('/pole_studio/clean', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.clean();
  await refreshState();
  renderBusiness();
  toast('Studio deep cleaned! ✨', 'success');
}

async function psPepTalk(dk) {
  const r = await api('/pole_studio/pep_talk', 'POST', { dancer: dk });
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(`Pep talk with ${PS_DANCERS[dk].name}. Mood improved!`, 'success');
}

async function psTeamCoffee() {
  const r = await api('/pole_studio/team_coffee', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Team coffee! Everyone feels appreciated. ☕', 'success');
}

function showPsDemand(dk) {
  const ps = state.pole_studio; if (!ps) return;
  const dem = (ps.active_demands || []).find(d => d.dancer === dk);
  const dm = PS_DANCERS[dk] || {};
  if (!dem) { renderBusiness(); return; }
  openModal(`<div class="modal-handle"></div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <span style="font-size:22px">${dm.icon || '👤'}</span>
      <div><div style="font-weight:800;font-size:15px;color:#E8D5F5">${dm.name}</div>
        <div style="font-size:11px;color:#FF9800">⏰ ${dem.days_left} day(s) to answer — ignore it and she gets upset</div></div>
    </div>
    <p style="font-size:14px;color:#C4A8E0;line-height:1.55;font-style:italic;margin:8px 4px 16px">"${PS_DEMAND_TEXT[dem.key] || '...'}"</p>
    <div style="display:flex;gap:8px">
      <button class="btn btn-primary" style="flex:1" onclick="psResolveDemand('${dem.key}','accept')">✅ Grant it</button>
      <button class="btn btn-ghost" style="flex:1" onclick="psResolveDemand('${dem.key}','reject')">❌ Turn it down</button>
    </div>`);
}

async function psResolveDemand(key, action) {
  const r = await api('/pole_studio/resolve_demand', 'POST', { key, action });
  if (r.error) { toast(r.error, 'error'); return; }
  closeModal();
  await refreshState();
  renderBusiness();
  toast(r.msg || (action === 'accept' ? 'Request granted.' : 'Request turned down.'), action === 'accept' ? 'success' : 'info');
}

function psPoleUpgradeMenu(poleIdx) {
  const ps    = state.pole_studio;
  const pole  = ps && ps.poles && ps.poles[poleIdx];
  if (!pole) return;
  const upgrades = pole.upgrades || {};

  const rows = ['chrome_polish','led_halo','grip_coating'].map(u => {
    const meta = PS_UPGRADES[u];
    const has  = !!upgrades[u];
    return `
      <div style="background:#2A1035;border:1px solid ${has ? '#7B2D8B' : '#3A1A4A'};padding:12px;margin-bottom:8px;border-radius:4px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          ${pxIcon(meta.icon, 20)}
          <div style="flex:1">
            <div style="font-weight:700;color:#E8D5F5;font-size:13px">${meta.name}</div>
            <div style="font-size:11px;color:#C4A8E0;margin-top:2px">${meta.desc}</div>
          </div>
          <div style="font-size:13px;font-weight:700;color:#BB86FC;white-space:nowrap">$${meta.cost.toLocaleString()}</div>
        </div>
        ${has
          ? `<div style="font-size:11px;color:#4CAF50;margin-top:4px">✅ Installed</div>`
          : `<button onclick="psUpgradePole(${poleIdx},'${u}');closeModal()" style="width:100%;margin-top:6px;background:#7B2D8B;border:none;color:#E8D5F5;padding:8px;font-size:12px;font-weight:700;cursor:pointer;border-radius:3px">Install — $${meta.cost.toLocaleString()}</button>`}
      </div>`;
  }).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div style="background:#1A0826;padding:16px;min-height:100px">
      <div style="font-size:14px;font-weight:700;color:#E8D5F5;margin-bottom:4px">✨ Pole #${poleIdx + 1} Upgrades</div>
      <div style="font-size:11px;color:#9B7BB8;margin-bottom:14px">Each upgrade is permanent and applies to this pole only.</div>
      ${rows}
      <button onclick="closeModal()" style="width:100%;background:#3A1A4A;border:1px solid #5A2D7A;color:#9B7BB8;padding:8px;font-size:12px;cursor:pointer;border-radius:3px;margin-top:4px">Close</button>
    </div>`);
}

async function psUpgradePole(poleIdx, upgrade) {
  const r = await api('/pole_studio/upgrade_pole', 'POST', { pole_idx: poleIdx, upgrade });
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(`Pole upgraded: ${PS_UPGRADES[upgrade].name}!`, 'success');
}

async function psRepairPole(poleIdx) {
  const r = await api('/pole_studio/repair_pole', 'POST', { pole_idx: poleIdx });
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast('Pole repaired!', 'success');
}

function showPsSlotConfig(idx) {
  const ps = state.pole_studio; if (!ps) return;
  const slot = (ps.slots || [])[idx]; if (!slot) return;
  const dancers = ps.dancers || {}, facs = ps.facilities || {};
  const equipOk = eq => eq === 'silks' ? !!facs.silks_rig : eq === 'vip' ? !!facs.vip_suite : true;
  // class type options with info + lock state
  const classRows = Object.entries(PS_CLASSES).map(([ck, ct]) => {
    const locked = !equipOk(ct.equip);
    const sel = slot.type === ck;
    const star = Object.keys(PS_SPECIALTY_CLASS).find(k => PS_SPECIALTY_CLASS[k] === ck);
    const starName = star ? PS_DANCERS[star].name : '';
    return `<div onclick="${locked ? '' : `psSetSlot(${idx},'${ck}',undefined)`}" style="background:${sel ? '#5A2D7A' : '#2A1035'};border:1px solid ${sel ? '#BB86FC' : '#5A2D7A'};border-radius:6px;padding:8px;margin-bottom:5px;${locked ? 'opacity:0.5' : 'cursor:pointer'}">
      <div style="display:flex;align-items:center;gap:7px"><span style="font-size:16px">${ct.icon}</span>
        <div style="flex:1;min-width:0"><div style="font-weight:700;font-size:12px;color:#E8D5F5">${ct.name} <span style="font-size:9px;color:#9B7BB8">${ct.seats} seats · $${ct.rev}/head</span></div>
          <div style="font-size:10px;color:#C4A8E0">${ct.desc}${starName ? ` <span style="color:#4CAF50">★ ${starName}</span>` : ''}</div></div>
        ${locked ? `<span style="font-size:9px;color:#FF5252">🔒</span>` : sel ? `<span style="color:#BB86FC">✓</span>` : ''}</div></div>`;
  }).join('');
  // instructor options
  const instrRows = Object.keys(PS_DANCERS).filter(k => (dancers[k] || {}).hired).map(k => {
    const dm = PS_DANCERS[k], dd = dancers[k];
    const onSpec = PS_SPECIALTY_CLASS[k] === slot.type;
    const sel = slot.instructor === k;
    const energy = Math.round(dd.energy != null ? dd.energy : 100);
    return `<div onclick="psSetSlot(${idx},undefined,'${k}')" style="background:${sel ? '#5A2D7A' : '#2A1035'};border:1px solid ${sel ? '#BB86FC' : '#5A2D7A'};border-radius:6px;padding:8px;margin-bottom:5px;cursor:pointer;display:flex;align-items:center;gap:7px">
      <span style="font-size:16px">${dm.icon}</span>
      <div style="flex:1;min-width:0"><div style="font-weight:700;font-size:12px;color:#E8D5F5">${dm.name} <span style="font-size:9px;color:${onSpec ? '#4CAF50' : '#FF9800'}">${onSpec ? '★ specialty (+40%)' : 'off-lane (−25%)'}</span></div>
        <div style="font-size:10px;color:#9B7BB8">energy ${energy}%</div></div>
      ${sel ? `<span style="color:#BB86FC">✓</span>` : ''}</div>`;
  }).join('') || `<div style="font-size:11px;color:#9B7BB8;padding:6px">No instructors hired yet.</div>`;
  openModal(`<div class="modal-handle"></div>
    <div style="font-weight:800;font-size:15px;color:#E8D5F5">Class Slot ${idx + 1}</div>
    <div style="font-size:11px;color:#C4A8E0;margin-bottom:10px">Pick what to teach, then who teaches it. Match an instructor to her ★ specialty for the biggest payout.</div>
    <div style="font-size:11px;font-weight:700;color:#BB86FC;margin-bottom:6px">CLASS TYPE</div>${classRows}
    <div style="font-size:11px;font-weight:700;color:#BB86FC;margin:10px 0 6px">INSTRUCTOR</div>${instrRows}
    <button onclick="psSetSlot(${idx},undefined,null)" style="width:100%;margin-top:6px;background:#3A1A4A;border:1px solid #5A2D7A;color:#9B7BB8;padding:7px;font-size:11px;cursor:pointer;border-radius:4px">Clear instructor (close this class)</button>
    <button class="btn btn-ghost btn-sm btn-full" style="margin-top:6px" onclick="closeModal()">Done</button>`);
}

async function psSetSlot(idx, classType, instructor) {
  const body = { slot_idx: idx };
  if (classType !== undefined) body.class_type = classType;
  if (instructor !== undefined) body.instructor = instructor;   // null clears
  const r = await api('/pole_studio/set_slot', 'POST', body);
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.toggle?.();
  await refreshState();
  renderBusiness();
  showPsSlotConfig(idx);   // re-open with updated state
}

async function psBuyFacility(key) {
  const r = await api('/pole_studio/buy_facility', 'POST', { key });
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast(`${PS_FACILITIES[key].name} installed!`, 'success');
}

async function psMarketing() {
  const r = await api('/pole_studio/marketing', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast('Marketing push live — new members incoming!', 'success');
}

async function psThemeNight() {
  const r = await api('/pole_studio/theme_night', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.purchase();
  await refreshState();
  renderBusiness();
  toast(`Theme Night was a hit! +${fmt(r.payout)}`, 'success');
}

async function psHype() {
  const r = await api('/pole_studio/hype', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.toggle?.();
  await refreshState();
  renderBusiness();
  toast('Vibe freshened — atmosphere up.', 'success');
}

async function psHireStaff(role) {
  const r = await api('/pole_studio/hire_staff', 'POST', { role });
  if (r.error) { toast(r.error, 'error'); return; }
  sfx.hire();
  await refreshState();
  renderBusiness();
  toast(`${PS_STAFF[role].name} hired!`, 'success');
}

async function psFireStaff(role) {
  const r = await api('/pole_studio/fire_staff', 'POST', { role });
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(`${PS_STAFF[role].name} let go.`, 'info');
}

async function psToggleInsurance() {
  const r = await api('/pole_studio/insurance', 'POST');
  if (r.error) { toast(r.error, 'error'); return; }
  await refreshState();
  renderBusiness();
  toast(r.insurance ? 'Studio insurance activated.' : 'Insurance cancelled.', 'info');
}

// ── Slippery When Washed ─────────────────────────────────────────────────────
const CW_STAFF = {
  terry:         { name: 'Terry',             icon: '💧', cost: 180, desc: 'Head Wash Technician. 22 years in the business. He considers himself an artist. He has opinions about water temperature. He will share them.' },
  brianna:       { name: 'Brianna',           icon: '📋', cost: 220, desc: 'Shift Manager. Produced a 47-step laminated flow chart for optimal wash sequencing. It works. +20% bay output. Reduces morale decay.' },
  squeegee_kid:  { name: 'The Squeegee Kid', icon: '🪟', cost:  80, desc: 'Name unknown. Shows up 65% of days. On the days he shows up, he is excellent. He has three other jobs. They are all similar.' },
  dave:          { name: 'Dave',              icon: '🌀', cost: 120, desc: 'The Vacuum Guy. Only does vacuums. Refuses any other task. 47 five-star Yelp reviews. Dave does not know what Yelp is.' },
  rhonda:        { name: 'Rhonda',            icon: '✨', cost: 250, desc: 'Detailer. Takes 3 hours per car. They look incredible. Rhonda is very slow. She knows. She is unbothered. Unlocks Premium Full Detail.' },
  manny:         { name: 'Manny',             icon: '🔧', cost: 160, desc: 'On-site Repairman. Always has the right tool, usually in his back pocket. Restores +5 condition/day per bay, fixes broken bays overnight, AND keeps water pressure pegged near 100. He hums while he works.' },
  carlos:        { name: 'Carlos',            icon: '📦', cost: 150, desc: 'Supply Manager. Knows a guy for everything. Auto-orders soap & wax from CostPro to a buffer — you never run dry.' },
  diane:         { name: 'Diane',             icon: '🗂️', cost: 240, desc: 'General Manager. Handles every dispute, contract offer, and curveball before it reaches you — always picks the sensible option. Keeps a binder. The binder has tabs.' },
};

const CW_BAY_UPGRADES = {
  nozzles:  { name: 'High-Pressure Nozzles', icon: '🔩', cost: 15000, desc: '+25% income from this bay. Cuts equipment decay in half.' },
  foam:     { name: 'Foam Cannon',           icon: '🫧', cost: 12000, desc: '+20% income from this bay. +10 reputation on install.' },
  led_sign: { name: 'LED Arch Sign',         icon: '💡', cost: 18000, desc: '+15% income from this bay. Boosts regulars growth.' },
  conveyor: { name: 'Conveyor Belt',         icon: '⚙️', cost: 35000, desc: '+30% income. Eliminates Squeegee Kid no-show penalty.' },
};

const CW_GLOBAL_UPGRADES = {
  waiting_room_tv:  { name: 'Waiting Room TV',       icon: '📺', cost:  8000, desc: 'Reduces regulars drain from wait events.' },
  loyalty_machine:  { name: 'Loyalty Card Machine',  icon: '💳', cost: 12000, desc: 'Doubles regulars build rate.' },
  water_tank:       { name: 'Industrial Water Tank',  icon: '🛢️', cost: 25000, desc: 'Water pressure decays 60% slower.' },
  dryer_arch:       { name: 'Automated Dryer Arch',   icon: '🌬️', cost: 30000, desc: 'Required for Deluxe Wax & Shine package.' },
  membership_kiosk: { name: 'Wash Club Kiosk',       icon: '🎟️', cost: 28000, desc: 'Launch the Unlimited Wash Club — recurring members who come rain or shine.' },
  upsell_menu:      { name: 'Digital Upsell Menu',   icon: '🖥️', cost: 16000, desc: 'Pushes more cars into pricier washes (higher $/car).' },
};

const CW_PACKAGES = {
  basic:    { name: 'Basic Rinse',        icon: '💦' },
  standard: { name: 'Standard Wash',      icon: '🫧' },
  deluxe:   { name: 'Deluxe Wax & Shine', icon: '✨' },
  premium:  { name: 'Premium Detail',     icon: '💎' },
};
const CW_PKG_MULT = { basic: 1.0, standard: 1.75, deluxe: 3.0, premium: 5.0 };
const CW_BASE_PER_CAR = 11;
const CW_WEATHER = {
  clear:    { name: 'Clear & Dusty',    icon: '☀️', good: true  },
  dusty:    { name: 'Dry Dusty Spell',  icon: '🌵', good: true  },
  pollen:   { name: 'Pollen Storm',     icon: '🌼', good: true  },
  hot:      { name: 'Hot & Hazy',       icon: '🥵', good: true  },
  overcast: { name: 'Overcast',         icon: '☁️', good: false },
  rain:     { name: 'Rainy',            icon: '🌧️', good: false },
  storm:    { name: 'Storm',            icon: '⛈️', good: false },
  road_salt:{ name: 'Road-Salt Season', icon: '❄️', good: true  },
};

const CW_BAY_PRICES   = [100000, 175000, 275000, 400000];
const CW_MAX_BAYS     = 5;
const CW_WASH_PRICE   = 600000;
const CW_UNLOCK_LEVEL = 10;

function cwCarSvg(broken) {
  // Clean side-profile car (vector, scales crisply — no emoji).
  return `<svg viewBox="0 0 96 48" width="88" height="44" style="display:block;margin:0 auto;filter:${broken ? 'grayscale(1) brightness(0.6)' : 'drop-shadow(0 2px 2px rgba(0,0,0,0.3))'}">
    <ellipse cx="48" cy="43.5" rx="37" ry="3.2" fill="rgba(0,0,0,0.28)"/>
    <path d="M7 33 Q7 26 14 25 L25 24 Q31 15 41 14 L59 14 Q70 15 76 24 L85 26 Q91 27.5 91 33 L91 36 Q91 38 89 38 L9 38 Q7 38 7 36 Z" fill="#E53935"/>
    <path d="M29 24 Q34 16 42 15 L57 15 Q65 16 70 24 Z" fill="#C62828"/>
    <path d="M33 23 Q37 17.5 43 17 L49 17 L49 23 Z" fill="#BBDEFB"/>
    <path d="M51 17 L56 17 Q62 17.5 66 23 L51 23 Z" fill="#BBDEFB"/>
    <path d="M14 30.5 Q48 27.5 86 30.5" stroke="rgba(255,255,255,0.55)" stroke-width="1.6" fill="none" stroke-linecap="round"/>
    <circle cx="88" cy="31" r="2.3" fill="#FFF59D"/>
    <circle cx="27" cy="38" r="7.6" fill="#1c1c1c"/><circle cx="27" cy="38" r="3.2" fill="#B0BEC5"/>
    <circle cx="70" cy="38" r="7.6" fill="#1c1c1c"/><circle cx="70" cy="38" r="3.2" fill="#B0BEC5"/>
  </svg>`;
}

function cwAnimatedCar(bayIdx, broken) {
  const bubbles = Array.from({ length: 9 }, (_, i) => {
    const left  = 6 + (i * 11) % 84;
    const size  = 7 + (i * 7 % 9);             // 7–15px, varied
    const dur   = 2.4 + (i % 4) * 0.7;
    const delay = (-(dur * (i / 9))).toFixed(2);   // negative: each starts already mid-rise (no bottom row)
    const bottom = 3 + (i * 5 % 16);               // varied start heights
    return `<div style="position:absolute;left:${left}%;bottom:${bottom}%;width:${size}px;height:${size}px;border-radius:50%;
      background:radial-gradient(circle at 34% 30%, rgba(255,255,255,0.95) 0%, rgba(214,240,255,0.5) 38%, rgba(150,205,250,0.22) 72%, rgba(150,205,250,0.05) 100%);
      box-shadow:inset 0 0 3px rgba(255,255,255,0.55), 0 0 3px rgba(200,235,255,0.35);
      animation:cwBubble ${dur.toFixed(1)}s ${delay}s ease-in infinite;pointer-events:none"></div>`;
  }).join('');

  return `
    <div style="position:relative;width:96px;height:56px;margin:4px auto;text-align:center">
      <div style="animation:cwCarBob 2.4s ease-in-out infinite;position:relative;display:inline-block">
        ${cwCarSvg(broken)}
        ${broken ? '<div style="position:absolute;top:-4px;right:2px;font-size:15px">💨</div>' : ''}
      </div>
      ${broken ? '' : bubbles}
    </div>`;
}

function renderCarWashContent() {
  const cw = state.car_wash;
  if (!cw || !cw.owned) {
    const lvl = state.level || 0;
    const canAfford = (state.cash || 0) >= CW_WASH_PRICE;
    const canLevel  = lvl >= CW_UNLOCK_LEVEL;
    return `
      <div style="text-align:center;padding:20px 10px">
        <div style="font-size:64px;line-height:1;margin:0 auto 8px">🚗</div>
        <div style="font-size:14px;font-weight:700;color:#1E88E5;margin-bottom:4px">Slippery When Washed</div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:16px">The sign is already crooked. It adds character.</div>
        <button onclick="cwBuy()" ${(!canAfford||!canLevel)?'disabled':''} style="background:${canAfford&&canLevel?'#1E88E5':'#555'};border:none;color:white;padding:10px 24px;font-size:13px;font-weight:700;cursor:${canAfford&&canLevel?'pointer':'not-allowed'};border-radius:4px;width:100%">
          ${!canLevel ? `🔒 Requires Level ${CW_UNLOCK_LEVEL}` : !canAfford ? `💸 $${CW_WASH_PRICE.toLocaleString()} required` : `🚿 Open for $${CW_WASH_PRICE.toLocaleString()}`}
        </button>
      </div>`;
  }

  const bays     = cw.bays     || [];
  const staff    = cw.staff    || {};
  const gUpgs    = cw.global_upgrades || {};
  const sup      = cw.supplies || {};
  const currentDay = state.day || 0;

  // Offered package tiers + average $/car (the customer mix; upsell shifts it up)
  const hasSoap   = (sup.cw_basic_soap    || 0) > 0;
  const hasStdSoap= (sup.cw_standard_soap || 0) > 0;
  const hasWax    = (sup.cw_premium_wax   || 0) > 0;
  const hasRhonda = staff.rhonda;
  const hasDryer  = gUpgs.dryer_arch;
  const offered = ['basic'];
  if (hasStdSoap) offered.push('standard');
  if (hasWax && hasDryer) offered.push('deluxe');
  if (hasRhonda && hasStdSoap && hasWax && hasDryer) offered.push('premium');
  const upsellOn = !!gUpgs.upsell_menu;
  const _W = upsellOn ? { basic: 2, standard: 4, deluxe: 4, premium: 3 } : { basic: 5, standard: 4, deluxe: 2, premium: 1 };
  const _tw = offered.reduce((a, t) => a + _W[t], 0) || 1;
  const avgPrice = offered.reduce((a, t) => a + _W[t] * CW_BASE_PER_CAR * CW_PKG_MULT[t], 0) / _tw;

  // Weather, demand readout, members
  const wx = CW_WEATHER[cw.weather] || CW_WEATHER.clear;
  const fx = cw.forecast ? CW_WEATHER[cw.forecast] : null;
  const lastCars = Math.round(cw.last_cars || 0), lastTA = Math.round(cw.last_turnaways || 0);
  const members  = Math.round(cw.members || 0);
  const hasKiosk = !!gUpgs.membership_kiosk;

  // Meters
  const waterPct  = Math.round(cw.water_pressure || 0);
  const moralePct = Math.round(cw.morale || 0);
  const repPct    = Math.round(cw.reputation || 0);
  const regPct    = Math.round(cw.regulars || 0);
  const wColor    = waterPct < 30 ? '#e74c3c' : waterPct < 60 ? '#FF9800' : '#2196F3';
  const mColor    = moralePct < 30 ? '#e74c3c' : moralePct < 60 ? '#FF9800' : '#4CAF50';

  function meter(label, pct, color, extra='') {
    return `<div style="margin-bottom:6px">
      <div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;margin-bottom:2px">
        <span>${label}</span><span style="color:${color}">${pct}%${extra}</span>
      </div>
      <div style="background:#1a2a3a;height:7px;border-radius:4px;overflow:hidden">
        <div style="width:${pct}%;height:100%;background:${color};border-radius:4px;transition:width 0.3s"></div>
      </div>
    </div>`;
  }

  const lunchCooldown = Math.max(0, 7 - (currentDay - (cw.last_lunch_day || -999)));
  const pepUsed = cw.pep_day === currentDay;

  // Bay cards
  const bayCards = bays.map((bay, i) => {
    const broken   = bay.broken;
    const cond     = Math.round(bay.condition || 0);
    const condColor= cond < 30 ? '#e74c3c' : cond < 60 ? '#FF9800' : '#4CAF50';
    const upgs     = bay.upgrades || {};
    const allUpgs  = Object.keys(CW_BAY_UPGRADES).every(u => upgs[u]);
    return `
      <div style="background:#0D1E2E;border:2px solid ${broken?'#e74c3c':'#1565C0'};border-radius:6px;padding:10px;margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <div style="font-size:12px;font-weight:700;color:#90CAF9">Bay #${i+1}</div>
          <div style="flex:1;font-size:10px;color:#64B5F6">Condition: <span style="color:${condColor}">${cond}%</span></div>
          ${broken
            ? `<button onclick="cwRepairBay(${i})" style="background:#e74c3c;border:none;color:white;padding:3px 8px;font-size:10px;cursor:pointer;border-radius:3px">🔧 Repair $250</button>`
            : (!allUpgs ? `<button onclick="cwBayUpgradeMenu(${i})" style="background:#0D47A1;border:1px solid #1E88E5;color:#90CAF9;padding:3px 8px;font-size:10px;cursor:pointer;border-radius:3px">🔧 Upgrades</button>` : '')}
        </div>
        ${cwAnimatedCar(i, broken)}
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
          ${Object.entries(CW_BAY_UPGRADES).filter(([u]) => upgs[u]).map(([u,m]) =>
            `<span style="background:#0D47A1;color:#90CAF9;padding:2px 6px;font-size:9px;border-radius:2px">${m.icon} ${m.name}</span>`
          ).join('')}
        </div>
      </div>`;
  }).join('');

  const nextBayPrice = CW_BAY_PRICES[bays.length - 1] || null;
  const canBuildBay  = bays.length < CW_MAX_BAYS;

  // Staff cards
  const staffCards = Object.entries(CW_STAFF).map(([role, meta]) => {
    const hired = staff[role];
    return `
      <div style="display:flex;align-items:center;gap:8px;padding:8px;background:#0D1E2E;border:1px solid ${hired?'#1E88E5':'#1a2a3a'};border-radius:4px;margin-bottom:6px">
        ${pxIcon(meta.icon, 20)}
        <div style="flex:1">
          <div style="font-weight:700;color:#90CAF9;font-size:12px">${meta.name} <span style="color:#64B5F6;font-weight:400;font-size:10px">$${meta.cost}/day</span></div>
          <div style="font-size:10px;color:#546E7A">${meta.desc}</div>
        </div>
        ${hired
          ? `<button onclick="cwFireStaff('${role}')" style="background:none;border:1px solid #1a3a4a;color:#546E7A;padding:3px 8px;font-size:10px;cursor:pointer;border-radius:3px">✕</button>`
          : `<button onclick="cwHireStaff('${role}')" style="background:#1E88E5;border:none;color:white;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;border-radius:3px;white-space:nowrap">Hire</button>`}
      </div>`;
  }).join('');

  // Global upgrades
  const globalUpgHtml = Object.entries(CW_GLOBAL_UPGRADES).map(([key, meta]) => {
    const has = gUpgs[key];
    return `
      <div style="display:flex;align-items:center;gap:8px;padding:8px;background:#0D1E2E;border:1px solid ${has?'#1E88E5':'#1a2a3a'};border-radius:4px;margin-bottom:6px">
        ${pxIcon(meta.icon, 20)}
        <div style="flex:1">
          <div style="font-weight:700;color:#90CAF9;font-size:12px">${meta.name}</div>
          <div style="font-size:10px;color:#546E7A">${meta.desc}</div>
        </div>
        ${has
          ? `<span style="font-size:11px;color:#4CAF50">✅ Installed</span>`
          : `<button onclick="cwGlobalUpgrade('${key}')" style="background:#1E88E5;border:none;color:white;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;border-radius:3px;white-space:nowrap">$${meta.cost.toLocaleString()}</button>`}
      </div>`;
  }).join('');

  // Supply status badges
  const supplyBadges = [
    ['cw_basic_soap','🧼','Basic Soap'],['cw_standard_soap','🫧','Std Soap'],
    ['cw_premium_wax','✨','Premium Wax'],['cw_tire_shine','🖤','Tire Shine'],
    ['cw_air_freshener','🌲','Air Fresh'],
  ].map(([k,icon,label]) => {
    const days = sup[k] || 0;
    return days > 0
      ? `<span style="background:#0D47A1;border:1px solid #1E88E5;color:#90CAF9;padding:3px 7px;font-size:10px;border-radius:3px">${pxIcon(icon, 14)} ${label}: ${days}d</span>`
      : '';
  }).filter(Boolean).join('');

  return `
    <div style="background:#071525;padding:12px;border-radius:4px">

      <div style="display:flex;align-items:center;gap:10px;background:#0D1E2E;border:1px solid ${wx.good ? '#2E7D32' : '#FF9800'};border-radius:6px;padding:9px 11px;margin-bottom:10px">
        <div style="font-size:26px">${wx.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:13px;font-weight:700;color:#E3F2FD">${wx.name} <span style="font-size:10px;color:${wx.good ? '#81C784' : '#FFB74D'}">${wx.good ? 'busy day' : 'slow day'}</span></div>
          <div style="font-size:10px;color:#64B5F6">🚗 ${lastCars} cars washed/day${lastTA > 0 ? ` · <span style="color:#FF9800">⚠ ${lastTA} turned away — build more bays!</span>` : ''}</div>
        </div>
        ${fx ? `<div style="text-align:right;flex-shrink:0"><div style="font-size:9px;color:#546E7A">tomorrow</div><div style="font-size:13px">${fx.icon}</div></div>` : ''}
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
        ${meter('💧 Water Pressure', waterPct, wColor, waterPct < 40 ? ' ⚠️':'')}
        ${meter('😊 Staff Morale',   moralePct, mColor)}
        ${meter('⭐ Reputation',     repPct, '#FFD700')}
        ${meter('👥 Regulars',       regPct, '#4CAF50')}
      </div>

      ${hasKiosk ? `<div style="display:flex;align-items:center;gap:8px;background:#0D1E2E;border:1px solid #1E88E5;border-radius:6px;padding:8px 11px;margin-bottom:10px">
        <span style="font-size:18px">🎟️</span><div style="flex:1"><div style="font-size:12px;font-weight:700;color:#90CAF9">Wash Club</div><div style="font-size:10px;color:#64B5F6">comes rain or shine</div></div>
        <div style="text-align:right"><div style="font-size:17px;font-weight:800;color:#FFD24A">${members}</div><div style="font-size:9px;color:#546E7A">members · $${members * 6}/day</div></div></div>` : ''}

      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:6px">
        <div style="font-size:11px;color:#546E7A">Offering: ${offered.map(t => CW_PACKAGES[t].icon).join('')} · <span style="color:#90CAF9;font-weight:700">~$${avgPrice.toFixed(1)}/car</span>${upsellOn ? ' <span style="color:#81C784;font-size:9px">▲ upsell</span>' : ''}</div>
        <div style="font-size:11px;color:#546E7A">Earned: <span style="color:#4CAF50">$${(cw.total_earned||0).toLocaleString()}</span></div>
      </div>

      ${!hasSoap ? `<div style="background:#4A0000;border:1px solid #e74c3c;color:#FF5252;padding:6px;font-size:11px;margin-bottom:8px;border-radius:3px">⚠️ Out of Basic Soap — closed! (Buy at CostPro or hire Carlos.)</div>` : ''}
      ${waterPct < 30 ? `<div style="background:#1a2000;border:1px solid #FF9800;color:#FF9800;padding:6px;font-size:11px;margin-bottom:8px;border-radius:3px">⚠️ Water pressure critical — <button onclick="cwRepressurize()" style="background:#FF9800;border:none;color:#000;padding:2px 8px;font-size:10px;font-weight:700;cursor:pointer;border-radius:2px">Repressurize $400</button></div>` : ''}

      ${supplyBadges ? `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px">${supplyBadges}</div>` : ''}

      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
        ${pepUsed
          ? `<span style="padding:6px 12px;font-size:11px;color:#546E7A;background:#0D1E2E;border:1px solid #1a2a3a;border-radius:3px">💬 Pep talk done today</span>`
          : `<button onclick="cwPepTalk()" style="background:#1565C0;border:none;color:#90CAF9;padding:6px 12px;font-size:11px;cursor:pointer;border-radius:3px">💬 Pep Talk ⚡3</button>`}
        ${lunchCooldown > 0
          ? `<span style="padding:6px 12px;font-size:11px;color:#546E7A;background:#0D1E2E;border:1px solid #1a2a3a;border-radius:3px">🍔 Lunch in ${lunchCooldown}d</span>`
          : `<button onclick="cwTeamLunch()" style="background:#1565C0;border:none;color:#90CAF9;padding:6px 12px;font-size:11px;cursor:pointer;border-radius:3px">🍔 Team Lunch ($400)</button>`}
        <button onclick="cwToggleInsurance()" style="background:${cw.insurance?'#1B5E20':'#1565C0'};border:none;color:#90CAF9;padding:6px 12px;font-size:11px;cursor:pointer;border-radius:3px">
          🛡️ ${cw.insurance ? `Insurance ✓ ($600/wk)` : 'Get Insurance ($600/wk)'}
        </button>
        ${waterPct < 80 ? `<button onclick="cwRepressurize()" style="background:#1565C0;border:none;color:#90CAF9;padding:6px 12px;font-size:11px;cursor:pointer;border-radius:3px">💧 Repressurize ($400)</button>` : ''}
      </div>

      <div style="font-size:11px;font-weight:700;color:#1E88E5;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">🚗 Wash Bays (${bays.length}/${CW_MAX_BAYS})</div>
      ${bayCards}
      ${canBuildBay
        ? `<button onclick="cwBuildBay()" style="width:100%;background:#071525;border:2px dashed #1565C0;color:#1E88E5;padding:10px;font-size:12px;cursor:pointer;margin-bottom:12px;border-radius:4px">
            ➕ Build Bay #${bays.length+1} — $${nextBayPrice.toLocaleString()}
           </button>`
        : `<div style="font-size:11px;color:#546E7A;text-align:center;margin-bottom:12px">All 5 bays built.</div>`}

      <div style="font-size:11px;font-weight:700;color:#1E88E5;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">👔 Staff</div>
      ${staffCards}

      <div style="font-size:11px;font-weight:700;color:#1E88E5;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;margin-top:4px">🏗️ Facility Upgrades</div>
      ${globalUpgHtml}
    </div>`;
}

function cwBayUpgradeMenu(bayIdx) {
  const bays = (state.car_wash && state.car_wash.bays) || [];
  const bay  = bays[bayIdx];
  if (!bay) return;
  const upgs = bay.upgrades || {};

  const rows = Object.entries(CW_BAY_UPGRADES).map(([key, meta]) => {
    const has = !!upgs[key];
    return `
      <div style="background:#0D1E2E;border:1px solid ${has?'#1E88E5':'#1a2a3a'};padding:12px;margin-bottom:8px;border-radius:4px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          ${pxIcon(meta.icon, 20)}
          <div style="flex:1">
            <div style="font-weight:700;color:#90CAF9;font-size:13px">${meta.name}</div>
            <div style="font-size:11px;color:#546E7A;margin-top:2px">${meta.desc}</div>
          </div>
          <div style="font-size:13px;font-weight:700;color:#1E88E5;white-space:nowrap">$${meta.cost.toLocaleString()}</div>
        </div>
        ${has
          ? `<div style="font-size:11px;color:#4CAF50">✅ Installed</div>`
          : `<button onclick="cwUpgradeBay(${bayIdx},'${key}');closeModal()" style="width:100%;margin-top:6px;background:#1E88E5;border:none;color:white;padding:8px;font-size:12px;font-weight:700;cursor:pointer;border-radius:3px">Install — $${meta.cost.toLocaleString()}</button>`}
      </div>`;
  }).join('');

  openModal(`
    <div class="modal-handle"></div>
    <div style="background:#071525;padding:16px;min-height:100px">
      <div style="font-size:14px;font-weight:700;color:#90CAF9;margin-bottom:4px">🔧 Bay #${bayIdx+1} Upgrades</div>
      <div style="font-size:11px;color:#546E7A;margin-bottom:14px">Permanent upgrades for this bay only.</div>
      ${rows}
      <button onclick="closeModal()" style="width:100%;background:#0D1E2E;border:1px solid #1a2a3a;color:#546E7A;padding:8px;font-size:12px;cursor:pointer;border-radius:3px;margin-top:4px">Close</button>
    </div>`);
}

async function cwBuy()                       { const r = await api('/car_wash/buy','POST'); if(r.error){toast(r.error,'error');return;} sfx.purchase(); await refreshState(); renderBusiness(); toast('Slippery When Washed is open!','success'); }
async function cwBuildBay()                  { const r = await api('/car_wash/build_bay','POST'); if(r.error){toast(r.error,'error');return;} sfx.construct(); await refreshState(); renderBusiness(); toast('New bay built!','success'); }
async function cwHireStaff(role)             { const r = await api('/car_wash/hire_staff','POST',{role}); if(r.error){toast(r.error,'error');return;} sfx.hire(); await refreshState(); renderBusiness(); toast(`${CW_STAFF[role].name} hired.`,'success'); }
function cwFireStaff(role) {
  const meta = CW_STAFF[role];
  openModal(`
    <div style="text-align:center;padding:8px 0">
      <div style="font-size:32px;margin-bottom:8px">${pxIcon(meta.icon, 32)}</div>
      <div style="font-size:16px;font-weight:700;margin-bottom:6px">Fire ${meta.name}?</div>
      <div style="font-size:13px;color:var(--text-muted);margin-bottom:16px">This will remove them from your payroll immediately.</div>
      <div style="display:flex;gap:8px;justify-content:center">
        <button onclick="closeModal()" style="padding:8px 18px;background:var(--card-bg);border:1px solid var(--border);color:var(--text-1);border-radius:4px;cursor:pointer;font-size:13px">Cancel</button>
        <button onclick="cwFireStaffConfirmed('${role}')" style="padding:8px 18px;background:#c0392b;border:none;color:white;border-radius:4px;cursor:pointer;font-size:13px;font-weight:700">Fire</button>
      </div>
    </div>`);
}
async function cwFireStaffConfirmed(role) { closeModal(); const r = await api('/car_wash/fire_staff','POST',{role}); if(r.error){toast(r.error,'error');return;} await refreshState(); renderBusiness(); toast(`${CW_STAFF[role].name} let go.`,'info'); }
async function cwUpgradeBay(bayIdx,upgrade)  { const r = await api('/car_wash/upgrade_bay','POST',{bay_idx:bayIdx,upgrade}); if(r.error){toast(r.error,'error');return;} sfx.construct(); await refreshState(); renderBusiness(); toast(`${CW_BAY_UPGRADES[upgrade].name} installed.`,'success'); }
async function cwGlobalUpgrade(upgrade)      { const r = await api('/car_wash/global_upgrade','POST',{upgrade}); if(r.error){toast(r.error,'error');return;} sfx.construct(); await refreshState(); renderBusiness(); toast(`${CW_GLOBAL_UPGRADES[upgrade].name} installed.`,'success'); }
async function cwRepairBay(bayIdx)           { const r = await api('/car_wash/repair_bay','POST',{bay_idx:bayIdx}); if(r.error){toast(r.error,'error');return;} await refreshState(); renderBusiness(); toast('Bay repaired.','success'); }
async function cwRepressurize()              { const r = await api('/car_wash/repressurize','POST'); if(r.error){toast(r.error,'error');return;} await refreshState(); renderBusiness(); toast('Water pressure restored.','success'); }
async function cwPepTalk()                   { const r = await api('/car_wash/pep_talk','POST'); if(r.error){toast(r.error,'error');return;} await refreshState(); renderBusiness(); toast('Pep talk delivered. Terry commented on water temperature.','success'); }
async function cwTeamLunch()                 { const r = await api('/car_wash/team_lunch','POST'); if(r.error){toast(r.error,'error');return;} await refreshState(); renderBusiness(); toast('Team lunch done.','success'); }
async function cwToggleInsurance()           { const r = await api('/car_wash/insurance','POST'); if(r.error){toast(r.error,'error');return;} sfx.toggle(); await refreshState(); renderBusiness(); toast(r.insurance?'Insurance activated.':'Insurance cancelled.','info'); }

// ── CostPro Wholesale Store ───────────────────────────────────────────────────
const COSTPRO_SNACKS = [
  { key: 'snacks',    name: 'Snacks',      icon: '🍫', price:  45, units: 40, sale: 2.25, desc: 'Candy & chips. Steady sellers everywhere.' },
  { key: 'cold',      name: 'Cold Drinks', icon: '🥤', price:  58, units: 40, sale: 2.75, desc: 'Soda & water. Big at parks, stations, summer.' },
  { key: 'hot',       name: 'Hot Drinks',  icon: '☕', price:  48, units: 30, sale: 3.00, desc: 'Coffee & cocoa. Office gold. Perishable — 6 days.' },
  { key: 'energy',    name: 'Energy',      icon: '⚡', price:  62, units: 30, sale: 3.75, desc: 'Energy drinks & bars. High margin; gyms & offices.' },
  { key: 'fresh',     name: 'Fresh Food',  icon: '🥗', price:  72, units: 20, sale: 6.50, desc: 'Sandwiches & salads. Best margin, spoils in 3 days.' },
  { key: 'specialty', name: 'Specialty',   icon: '🎁', price:  62, units: 24, sale: 4.75, desc: 'Novelty & local goods. Niche but lucrative.' },
];

const COSTPRO_LAUNDRY = [
  { key: 'soap',     name: 'Laundry Soap',    icon: '🧼', price: 300, desc: 'Required to operate. Lasts 7 days per case (10 with Energy Efficient upgrade).' },
  { key: 'softener', name: 'Fabric Softener', icon: '🌸', price: 500, desc: '+20% daily income. Lasts 10 days per case.' },
  { key: 'sheets',   name: 'Dryer Sheets',    icon: '🌬️', price: 400, desc: '+15% daily income. Lasts 10 days per case.' },
];

const COSTPRO_KOMBUCHA = [
  { key: 'kb_ginger',   name: "Ginger 'Mule' Kombucha",   icon: '🫚', price: 380, desc: 'House pour. Zingy. 10 days per keg.' },
  { key: 'kb_hibiscus', name: "Hibiscus 'Cosmo' Kombucha", icon: '🌺', price: 520, desc: 'Pink, fancy, photogenic. 10 days per keg.' },
  { key: 'kb_charcoal', name: "Charcoal 'Detox' Shots",   icon: '🖤', price: 460, desc: 'Tastes like punishment. People love it. 10 days/keg.' },
  { key: 'kb_cbd',      name: "CBD 'Sleepytime' Brew",    icon: '😌', price: 640, desc: 'The nightcap. Mellow. 10 days per keg.' },
  { key: 'kb_sparkle',  name: 'Sparkling Reserve',        icon: '🥂', price: 900, desc: 'The "champagne." Premium VIP pour. 10 days/keg.' },
];

const STORE_UNLOCK_LEVEL = 3;

// Which CostPro group "windows" are expanded. Reset to all-closed each time the
// player opens the store (see navTo).
let _costproOpen = {};
function toggleCostproGroup(id) { _costproOpen[id] = !_costproOpen[id]; renderStore(); }
function costproGroup(id, icon, title, count, bodyHtml) {
  const open = !!_costproOpen[id];
  return `
    <div style="border:1px solid var(--border);border-radius:10px;margin-bottom:10px;overflow:hidden">
      <div onclick="toggleCostproGroup('${id}')" style="display:flex;align-items:center;gap:9px;padding:13px 14px;cursor:pointer;user-select:none">
        <span style="font-size:18px">${icon}</span>
        <span style="font-weight:800;font-size:14px;flex:1;min-width:0">${title}</span>
        <span style="font-size:11px;color:var(--text-muted)">${count} item${count === 1 ? '' : 's'}</span>
        <span style="font-size:12px;color:var(--text-muted);display:inline-block;transition:transform .15s;transform:rotate(${open ? 90 : 0}deg)">▶</span>
      </div>
      ${open ? `<div style="padding:2px 12px 6px;border-top:1px solid var(--border)">${bodyHtml}</div>` : ''}
    </div>`;
}

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

  const bestAt = (cat) => {
    const hits = Object.values(VM_LOCATIONS)
      .map(l => ({ name: l.name, w: l.profile[cat] || 0 }))
      .filter(x => x.w > 0).sort((a, b) => b.w - a.w).slice(0, 2)
      .map(x => x.name.replace(/ (Entrance|Lobby|Terminal|Station|Center)$/, ''));
    return hits.length ? hits.join(' · ') : 'niche spots';
  };
  const snackCards = COSTPRO_SNACKS.map(item => {
    const held    = Math.round(inv[item.key] || 0);
    const accent  = VM_CAT_COLOR[item.key] || 'var(--primary)';
    const perish  = (VM_PRODUCTS[item.key] || {}).perishable;
    const profitU = item.sale - item.price / item.units;
    return `
    <div class="card" style="margin-bottom:10px;padding:0;overflow:hidden;display:flex">
      <div style="width:5px;background:${accent};flex-shrink:0"></div>
      <div style="flex:1;min-width:0;padding:11px 12px">
        <div style="display:flex;align-items:flex-start;gap:10px">
          <div style="width:38px;height:38px;border-radius:9px;background:${accent}26;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:20px">${item.icon}</div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px;display:flex;align-items:center;gap:6px;flex-wrap:wrap">${item.name}${perish ? `<span style="font-size:9px;font-weight:700;color:var(--warning);border:1px solid var(--warning);border-radius:8px;padding:0 5px">PERISHABLE</span>` : ''}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:1px">${item.desc}</div>
          </div>
          <div style="text-align:right;flex-shrink:0"><div style="font-size:15px;font-weight:800;color:${accent}">${fmt(item.price)}</div><div style="font-size:9px;color:var(--text-muted)">/case</div></div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:10px;color:var(--text-muted);margin:9px 0 4px">
          <span>📦 ${item.units}/case</span>
          <span>🏷️ <span style="color:var(--positive)">$${item.sale.toFixed(2)}</span>/unit</span>
          <span>💰 ~$${profitU.toFixed(2)}/unit profit</span>
          <span>🎒 ${held} held</span>
        </div>
        <div style="font-size:10px;color:var(--text-muted);margin-bottom:9px">⭐ Best at: <span style="color:var(--text-2)">${bestAt(item.key)}</span></div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',1)">Buy 1</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',3)">×3 · ${fmt(item.price*3)}</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',5)">×5 · ${fmt(item.price*5)}</button>
        </div>
      </div>
    </div>`;
  }).join('');

  // Kombucha bar supplies — only shown when the studio's Kombucha Bar is installed
  let poleSection = '';
  const pst = state.pole_studio;
  if (pst && pst.owned && (pst.facilities || {}).kombucha_bar) {
    const kbStock = pst.kombucha || {};
    poleSection = COSTPRO_KOMBUCHA.map(item => {
      const days = kbStock[item.key] || 0;
      return `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
          ${pxIcon(item.icon, 28)}
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">${item.name}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:1px">${item.desc}</div>
            <div style="font-size:11px;margin-top:3px;color:${days > 0 ? 'var(--positive)' : 'var(--text-muted)'}">
              ${days > 0 ? `${days} days on tap` : 'Not stocked'}
            </div>
          </div>
          <div style="font-size:15px;font-weight:800;color:var(--primary);flex-shrink:0">${fmt(item.price)}<div style="font-size:10px;font-weight:400;color:var(--text-muted);text-align:right">keg</div></div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',1)">Buy 1</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',3)">×3 · ${fmt(item.price*3)}</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',5)">×5 · ${fmt(item.price*5)}</button>
        </div>
      </div>`;
    }).join('');
  }

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
          ${pxIcon(item.icon, 28)}
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
    laundrySection = laundryCards;
  }

  // Car wash supplies — only shown when car wash is owned
  let cwSection = '';
  const cwst = state.car_wash;
  if (cwst && cwst.owned) {
    const CW_STORE_ITEMS = [
      { key: 'cw_basic_soap',    icon: '🧼', name: 'Basic Soap',     price: 350, daysKey: 'cw_basic_soap',    warnText: '⚠️ OUT — no income!' },
      { key: 'cw_standard_soap', icon: '🫧', name: 'Standard Soap',  price: 500, daysKey: 'cw_standard_soap', warnText: 'None stocked' },
      { key: 'cw_premium_wax',   icon: '✨', name: 'Premium Wax',    price: 700, daysKey: 'cw_premium_wax',   warnText: 'None stocked' },
      { key: 'cw_tire_shine',    icon: '🖤', name: 'Tire Shine',     price: 400, daysKey: 'cw_tire_shine',    warnText: 'None stocked' },
      { key: 'cw_air_freshener', icon: '🌲', name: 'Air Fresheners', price: 300, daysKey: 'cw_air_freshener', warnText: 'None stocked' },
    ];
    const cwSupplies = cwst.supplies || {};
    const cwCards = CW_STORE_ITEMS.map(item => {
      const days = cwSupplies[item.daysKey] || 0;
      return `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
          ${pxIcon(item.icon, 28)}
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">${item.name}</div>
            <div style="font-size:11px;margin-top:3px;color:${days > 0 ? 'var(--positive)' : 'var(--warning)'}">
              ${days > 0 ? `${days} days remaining` : item.warnText}
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
    cwSection = cwCards;
  }

  // Arcade prize stock — only shown when the Back-Room Arcade is open.
  let arcadeSection = '';
  const arc = state.arcade;
  if (arc && arc.unlocked) {
    const held = Math.round(arc.prizes || 0);
    const item = { key: 'arcade_prizes', name: 'Prize Stock', icon: '🧸', price: 320 };
    arcadeSection = `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
          ${pxIcon(item.icon, 28)}
          <div style="flex:1;min-width:0">
            <div style="font-weight:800;font-size:13px">${item.name}</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:1px">Plush, tickets & trinkets. A stocked prize counter boosts every cabinet's income (up to +30%) — but stock gets won daily. 60/case.</div>
            <div style="font-size:11px;margin-top:3px;color:${held > 0 ? 'var(--positive)' : 'var(--warning)'}">${held > 0 ? `${held} prizes in stock` : 'Counter empty — no income boost'}</div>
          </div>
          <div style="font-size:15px;font-weight:800;color:var(--primary);flex-shrink:0">${fmt(item.price)}<div style="font-size:10px;font-weight:400;color:var(--text-muted);text-align:right">each</div></div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',1)">Buy 1</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',3)">Buy 3 · ${fmt(item.price*3)}</button>
          <button class="btn btn-sm btn-primary" style="flex:1" onclick="buySnacks('${item.key}',5)">Buy 5 · ${fmt(item.price*5)}</button>
        </div>
      </div>`;
  }

  const groups = [
    costproGroup('vending', '🍬', 'Vending Supplies', COSTPRO_SNACKS.length, snackCards),
    laundrySection ? costproGroup('laundry', '🧺', 'Laundromat Supplies', COSTPRO_LAUNDRY.length, laundrySection) : '',
    arcadeSection  ? costproGroup('arcade',  '🕹️', 'Arcade Prizes', 1, arcadeSection) : '',
    poleSection    ? costproGroup('pole',    '🥂', 'Kombucha Bar', COSTPRO_KOMBUCHA.length, poleSection) : '',
    cwSection      ? costproGroup('carwash', '🚗', 'Car Wash Supplies', 5, cwSection) : '',
  ].join('');

  el.innerHTML = `
    <div style="background:var(--primary);color:white;text-align:center;padding:14px 16px">
      <div style="font-family:'Rubik Dirt',cursive;font-size:22px;letter-spacing:2px">CostPro</div>
      <div style="font-size:10px;opacity:0.75;letter-spacing:3px;margin-top:2px">WHOLESALE · BULK · SAVINGS</div>
    </div>
    <div style="font-size:11px;color:var(--text-muted);padding:12px 2px 8px">Tap a category to open it.</div>
    ${groups}
    <div style="font-size:11px;color:var(--text-muted);text-align:center;padding:8px 0 16px">
      More products unlock with new businesses.
    </div>`;
}

async function buySnacks(itemKey, qty) {
  const res = await api('/costpro/buy', 'POST', { item_key: itemKey, qty });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase();
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
const PG_ROWS     = 20;
const PG_TOTAL    = PG_COLS * PG_ROWS;  // 160 tiles
const PG_DURATION = 5;                  // seconds

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
  _mgListen(document, 'mouseup', pgMouseUp);
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
  _mgListen(document, 'mouseup', () => { _mg.dragging = false; });

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
    if (!_mg.running || !_mg.fallingTile || _mg.fallingTile.done) return;
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
  sfx.advTime();
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

  _pendingRepairs          = res.repairs           || [];
  _pendingStorylets        = res.storylet_events   || [];
  _pendingVendingEvents    = res.vending_events     || [];
  _pendingArcadeEvents     = res.arcade_events      || [];
  _pendingPoleEvents       = res.pole_events        || [];
  _pendingCarWashEvents    = res.car_wash_events    || [];
  _pendingRenewalOffers    = res.renewal_offers    || [];
  _pendingCommercialEvents = res.commercial_events || [];
  _pendingSquatter      = (res.events || []).find(e => e.type === 'squatter') || null;
  _pendingTaxEvent      = (res.tax_event && res.tax_event.total >= 0) ? res.tax_event : null;
  const totalPending    = _pendingRepairs.length + _pendingStorylets.length + _pendingVendingEvents.length + _pendingArcadeEvents.length + _pendingPoleEvents.length + _pendingCarWashEvents.length + _pendingRenewalOffers.length + _pendingCommercialEvents.length;
  const repairNote = _pendingRepairs.length > 0
    ? `<div style="background:#FFF8E1;color:#7A4A00;border:2px solid var(--warning);border-radius:var(--radius-sm);padding:10px 12px;margin-top:12px;font-size:13px;font-weight:700">
        ${pxIcon('🔧',16)} ${_pendingRepairs.length} repair${_pendingRepairs.length > 1 ? 's' : ''} need${_pendingRepairs.length === 1 ? 's' : ''} attention!</div>`
    : '';
  const storyletNote = _pendingStorylets.length > 0
    ? `<div style="background:#E8EAF6;color:#283593;border:2px solid #9FA8DA;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('📖',16)} ${_pendingStorylets.length} tenant situation${_pendingStorylets.length > 1 ? 's' : ''} to handle!</div>`
    : '';
  const vendingNote = _pendingVendingEvents.length > 0
    ? `<div style="background:#FFF3E0;color:#A14B00;border:2px solid #FFB74D;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🥤',16)} ${_pendingVendingEvents.length} vending decision${_pendingVendingEvents.length > 1 ? 's' : ''} to make!</div>`
    : '';
  const arcadeNote = _pendingArcadeEvents.length > 0
    ? `<div style="background:#EDE7F6;color:#4527A0;border:2px solid #9575CD;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🕹️',16)} ${_pendingArcadeEvents.length} arcade decision${_pendingArcadeEvents.length > 1 ? 's' : ''} to make!</div>`
    : '';
  const poleNote = _pendingPoleEvents.length > 0
    ? `<div style="background:#F3E5F5;color:#6A1B9A;border:2px solid #BA68C8;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('💃',16)} ${_pendingPoleEvents.length} studio decision${_pendingPoleEvents.length > 1 ? 's' : ''} to make!</div>`
    : '';
  const carWashNote = _pendingCarWashEvents.length > 0
    ? `<div style="background:#E3F2FD;color:#0D47A1;border:2px solid #64B5F6;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🚗',16)} ${_pendingCarWashEvents.length} car wash decision${_pendingCarWashEvents.length > 1 ? 's' : ''} to make!</div>`
    : '';
  const renewalNote = _pendingRenewalOffers.length > 0
    ? `<div style="background:#E8F5E9;color:#1B5E20;border:2px solid #66BB6A;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🔄',16)} ${_pendingRenewalOffers.length} lease renewal${_pendingRenewalOffers.length > 1 ? 's' : ''} to review!</div>`
    : '';
  const taxNote = _pendingTaxEvent
    ? `<div style="background:#FFEBEE;color:#B71C1C;border:2px solid #C62828;border-radius:var(--radius-sm);padding:10px 12px;margin-top:8px;font-size:13px;font-weight:700">
        ${pxIcon('🧾',16)} Tax Day! ${fmt(_pendingTaxEvent.total)} owed — you must respond before continuing.</div>`
    : '';

  const btnLabel = _pendingRepairs.length > 0
    ? `Fix Repairs (${_pendingRepairs.length})`
    : _pendingStorylets.length > 0
      ? `Tenant Situations (${_pendingStorylets.length})`
      : _pendingVendingEvents.length > 0
        ? `Vending Decisions (${_pendingVendingEvents.length})`
      : _pendingArcadeEvents.length > 0
        ? `Arcade Decisions (${_pendingArcadeEvents.length})`
      : _pendingPoleEvents.length > 0
        ? `Studio Decisions (${_pendingPoleEvents.length})`
      : _pendingCarWashEvents.length > 0
        ? `Car Wash Decisions (${_pendingCarWashEvents.length})`
      : _pendingRenewalOffers.length > 0
        ? `Review Leases (${_pendingRenewalOffers.length})`
        : _pendingCommercialEvents.length > 0
          ? `Business Events (${_pendingCommercialEvents.length})`
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
    ${storyletNote}
    ${vendingNote}
    ${arcadeNote}
    ${poleNote}
    ${carWashNote}
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
  } else if (_pendingStorylets.length > 0) {
    showNextStorylet();
  } else if (_pendingVendingEvents.length > 0) {
    showNextVendingEvent();
  } else if (_pendingArcadeEvents.length > 0) {
    showNextArcadeEvent();
  } else if (_pendingPoleEvents.length > 0) {
    showNextPoleEvent();
  } else if (_pendingCarWashEvents.length > 0) {
    showNextCarWashEvent();
  } else if (_pendingRenewalOffers.length > 0) {
    showNextRenewalOffer();
  } else if (_pendingCommercialEvents.length > 0) {
    drainCommercialEvents();
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
  const amount = taxEvent.total || 0;
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🧾',20)} Tax Day</div>
    <div class="modal-subtitle">Winter Day 28 — You must respond before continuing</div>
    <div class="card" style="margin-bottom:14px">
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏠',14)} Rent tax (5% of ${fmt(taxEvent.rent_income || 0)})</span>
        <span class="mr-value">${fmt(taxEvent.rent_tax || 0)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('💼',14)} Business + flip income</span>
        <span class="mr-value">${fmt((taxEvent.flip_income || 0) + (taxEvent.biz_income || 0))}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">− Deductions</span>
        <span class="mr-value" style="color:var(--positive)">−${fmt(taxEvent.deductions || 0)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">Business + flip tax (brackets)</span>
        <span class="mr-value">${fmt(taxEvent.active_tax || 0)}</span>
      </div>
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Taxes owed</span>
        <span class="mr-value" style="color:#C62828">${fmt(amount)}</span>
      </div>
    </div>
    <button class="btn btn-danger btn-full" style="margin-bottom:10px" onclick="payTaxes()">${pxIcon('💸',16)} Pay ${fmt(amount)} Now</button>
    <button class="btn btn-secondary btn-full" onclick="fileTaxExtension()">${pxIcon('📋',14)} File for Extension — pay on Spring Day 7</button>
    <p style="font-size:11px;color:var(--text-muted);text-align:center;margin-top:10px">Rent is taxed lightly (5%); business & flip profits ride progressive brackets after deductions.</p>
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

  const morale      = offer.morale ?? 50;
  const moraleColor = morale >= 60 ? 'var(--positive)' : morale >= 30 ? 'var(--warning)' : 'var(--negative)';
  const odds        = offer.renewal_odds || {};
  const raiseBtns   = [5, 10, 15].map(p => {
    const nr = Math.round(offer.rent * (1 + p / 100));
    const od = Math.round((odds[String(p)] ?? 0.5) * 100);
    const odColor = od >= 70 ? 'var(--positive)' : od >= 40 ? 'var(--warning)' : 'var(--negative)';
    return `<button class="btn btn-ghost btn-sm btn-full" style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px" onclick="respondRenewal(${offer.prop_id},{action:'raise',pct:${p}})"><span style="font-weight:800;min-width:38px;text-align:left">+${p}%</span><span style="font-size:12px;color:var(--text-muted)">${fmt(nr)}/wk</span><span style="font-size:12px;color:${odColor};font-weight:700">${od}% accept</span></button>`;
  }).join('');
  const traitChip = offer.trait_info
    ? ` <span style="font-size:10px;font-weight:700;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:1px 7px">${offer.trait_info.icon} ${offer.trait_info.name}</span>`
    : '';

  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon('🔄',20)} Lease Renewal</div>
    <div class="modal-subtitle">${offer.prop_name}</div>

    <div class="card" style="margin-bottom:12px;text-align:center">
      <div style="font-size:32px;margin-bottom:2px">${offer.tenant_icon}</div>
      <div style="font-weight:800;font-size:15px">${offer.tenant_name}${traitChip}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Wants another <strong>${stayLabel}</strong> · current rent <strong>${fmt(offer.rent)}/wk</strong> (${offer.rent_tier || 'Average'})</div>
      <div style="display:flex;justify-content:center;gap:14px;margin-top:8px;font-size:12px;font-weight:700">
        <span style="color:${moraleColor}">😊 ${morale}%</span>
        <span style="color:var(--accent)">💛 Loyalty ${offer.loyalty ?? 0}%</span>
        ${offer.renewals ? `<span style="color:var(--text-muted)">🔁 ${offer.renewals}×</span>` : ''}
      </div>
      <div style="font-size:12px;margin-top:6px;color:${missedColor};font-weight:700">${missedLabel}</div>
    </div>

    <button class="btn btn-primary btn-full" style="margin-bottom:8px" onclick="respondRenewal(${offer.prop_id},{action:'renew'})">${pxIcon('✅',14)} Renew at same rent · ${fmt(offer.rent)}/wk</button>

    <div class="card" style="margin-bottom:8px">
      <div style="font-size:12px;font-weight:800;margin-bottom:8px">${pxIcon('📈',14)} Raise the rent <span style="font-weight:400;color:var(--text-muted)">— a reject risks them walking</span></div>
      ${raiseBtns}
    </div>

    <button class="btn btn-ghost btn-full btn-sm" style="margin-bottom:8px" onclick="respondRenewal(${offer.prop_id},{action:'discount'})">${pxIcon('🤝',14)} Offer -5% to lock them in longer (+loyalty)</button>

    <button class="btn btn-ghost btn-full btn-sm" onclick="respondRenewal(${offer.prop_id},{action:'decline'})">${pxIcon('👋',14)} Let them go</button>

    ${_pendingRenewalOffers.length > 0
      ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingRenewalOffers.length} more renewal(s) after this</div>`
      : ''}`);
}

async function respondRenewal(propId, payload) {
  if (payload === true)  payload = { action: 'renew' };
  if (payload === false) payload = { action: 'decline' };
  const res = await api(`/property/${propId}/renewal_respond`, 'POST', payload);
  if (res.error) { toast(res.error, 'error'); return; }
  const msgs = {
    renewed:               ['Lease renewed — tenant staying on.', 'success'],
    discounted:            ['Renewed at a 5% discount — they love you for it.', 'success'],
    raise_accepted:        [`They accepted! Rent is now ${fmt(res.rent)}/wk.`, 'success'],
    raise_rejected_stayed: ['They balked at the raise but stayed at the old rent.', 'info'],
    raise_rejected_left:   ['They refused to pay more and moved out.', 'warning'],
    declined:              ['Tenant moved out. Property is now vacant.', 'warning'],
  };
  const [msg, kind] = msgs[res.outcome] || ['Done.', 'info'];
  toast(msg, kind);
  await refreshState();
  renderAll();
  showNextRenewalOffer();
}

// ── Tenant Storylets ──────────────────────────────────────────────────────────
function showNextStorylet() {
  if (_pendingStorylets.length === 0) { continueFromEvents(); return; }
  showStoryletModal(_pendingStorylets.shift());
}

function showStoryletModal(ev) {
  const choices = (ev.choices || []).map((c, i) =>
    `<button class="btn btn-ghost btn-full" style="margin-bottom:8px;text-align:left;white-space:normal;line-height:1.35" onclick="respondStorylet(${ev.prop_id}, ${i})">${c.label}</button>`
  ).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(ev.icon || '📖',20)} ${ev.title}</div>
    <div class="modal-subtitle">${ev.prop_name}</div>
    <p style="font-size:14px;color:var(--text-2);margin:12px 0 16px;line-height:1.5">${ev.text}</p>
    ${choices}
    ${_pendingStorylets.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:6px">${_pendingStorylets.length} more situation(s) after this</div>` : ''}`);
}

async function respondStorylet(propId, idx) {
  const res = await api('/storylet/respond', 'POST', { prop_id: propId, choice_idx: idx });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(res.result || 'Done.', res.left ? 'warning' : 'success');
  if (res.xp_gain) toast(`+${res.xp_gain} XP`, 'success');
  if (res.level_up) _pendingLevelUp = res.new_level;
  await refreshState();
  renderAll();
  showNextStorylet();
}

function drainCommercialEvents() {
  if (_pendingCommercialEvents.length === 0) { continueFromEvents(); return; }
  showCommercialEventModal(_pendingCommercialEvents.shift());
}

function showCommercialEventModal(ev) {
  _currentCommercialEvent = ev;
  const icon = ev.icon || ev.biz_icon || '🏢';
  const opts = (ev.options || []).map((o, i) =>
    `<button class="btn ${i === 0 ? 'btn-primary' : 'btn-ghost'} btn-full" style="margin-bottom:8px;text-align:left;white-space:normal;line-height:1.35" onclick="commercialEventRespond(${ev.prop_id},${ev.unit_idx},${i})">${o.label}</button>`
  ).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(icon,18)} ${ev.title || 'Commercial Event'}</div>
    <div class="modal-subtitle">${ev.prop_label || ''}</div>
    <p style="font-size:13px;margin:12px 0 16px;color:var(--text-muted);line-height:1.5">${ev.desc || ''}</p>
    ${opts}
    ${_pendingCommercialEvents.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:8px">${_pendingCommercialEvents.length} more event(s) after this</div>` : ''}
  `);
}

function showNextRepair() {
  if (_pendingRepairs.length === 0) { continueFromEvents(); return; }
  _currentRepair = _pendingRepairs.shift();
  showRepairModal(_currentRepair);
}

function showRepairModal(repair) {
  sfx.repair();
  const lastIdx = repair.choices.length - 1;
  const choicesHtml = repair.choices.map((c, i) => {
    const isIgnore  = (i === lastIdx);
    const costLabel = c.cost > 0 ? fmt(c.cost) : (isIgnore ? '' : 'FREE');
    const costColor = c.cost > 0 ? 'var(--text-1)' : 'var(--positive)';
    const cardStyle = isIgnore
      ? 'border-color:var(--negative);margin-top:10px;margin-bottom:4px'
      : (i === 0 ? 'border-color:var(--primary);margin-bottom:8px' : 'margin-bottom:8px');
    const nameColor = isIgnore ? 'color:var(--negative)' : '';
    return `<div class="contractor-card" style="${cardStyle}" onclick="resolveRepair(${i})">
      <div class="contractor-header">
        <span class="contractor-name" style="${nameColor}">${c.label}</span>
        ${costLabel ? `<span class="contractor-cost" style="color:${costColor}">${costLabel}</span>` : ''}
      </div>
    </div>`;
  }).join('');
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(repair.icon)} ${repair.title}</div>
    <div class="modal-subtitle">${repair.prop_name}</div>
    <p style="font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.5">${repair.text}</p>
    ${choicesHtml}
    ${_pendingRepairs.length > 0 ? `<div style="text-align:center;font-size:11px;color:var(--text-muted);margin-top:10px">${_pendingRepairs.length} more repair(s) after this</div>` : ''}`);
}

async function resolveRepair(choiceIdx) {
  const repair = _currentRepair;
  const res = await api('/repair/resolve', 'POST', {
    prop_id: repair.prop_id, repair_key: repair.key, choice_idx: choiceIdx,
  });
  if (res.error) { toast(res.error, 'error'); return; }
  const tColor = tierColor(condTier(res.condition));
  openModal(`
    <div class="modal-handle"></div>
    <div class="modal-title">${pxIcon(repair.icon, 20)} ${repair.title}</div>
    <p style="font-size:14px;color:var(--text-1);margin:10px 4px 14px;line-height:1.55">${res.result}</p>
    <div style="text-align:center;margin:12px 0">
      <div style="font-size:52px;font-weight:900;color:${tColor}">${condTier(res.condition)}</div>
      <div style="font-size:13px;color:var(--text-muted)">condition${res.cost > 0 ? ` · −${fmt(res.cost)}` : ''}</div>
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

// ── Bank ──────────────────────────────────────────────────────────────────────
// ── Finances Tab ──────────────────────────────────────────────────────────────
function switchFinTab(tab) {
  sfx.tab();
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
  const biz        = s.tax_year_biz_income || {};
  const lvl        = state.level || 0;
  const BIZ_META   = [
    { key: 'vending',     name: 'Vending machines', icon: '🥤', unlock: 3,  owned: (state.vending_machines || []).length > 0 },
    { key: 'laundromat',  name: 'Laundromat',       icon: '🧺', unlock: 5,  owned: !!state.laundromat },
    { key: 'pole_studio', name: 'Pole studio',      icon: '💃', unlock: 8,  owned: !!(state.pole_studio && state.pole_studio.owned) },
    { key: 'car_wash',    name: 'Car wash',         icon: '🚗', unlock: 10, owned: !!(state.car_wash && state.car_wash.owned) },
    { key: 'arcade',      name: 'Arcade',           icon: '🕹️', unlock: 5,  owned: !!(state.arcade && state.arcade.unlocked), secret: true },
  ];
  const bizTotal   = BIZ_META.reduce((a, b) => a + (biz[b.key] || 0), 0);
  const bizRows    = BIZ_META.map(b => {
    if (b.secret && !b.owned) return '';   // stay hidden until discovered
    if (b.owned) {
      return `
      <div class="money-row">
        <span class="mr-label">${pxIcon(b.icon,14)} ${b.name}</span>
        <span class="mr-value green">${fmt(biz[b.key] || 0)}</span>
      </div>`;
    }
    const note = lvl < b.unlock ? `🔒 Locked · Lv ${b.unlock}` : 'Not bought yet';
    return `
      <div class="money-row" style="opacity:0.4">
        <span class="mr-label">${pxIcon(b.icon,14)} ${b.name}</span>
        <span class="mr-value" style="color:var(--text-muted);font-weight:600">${note}</span>
      </div>`;
  }).join('');
  const totalIncome = flipIncome + rentIncome + bizTotal;
  const tb = state.tax_breakdown || {
    rent_tax: Math.round(rentIncome * 0.05), deductions: s.tax_year_deductions || 0,
    taxable_active: Math.max(0, flipIncome + bizTotal - (s.tax_year_deductions || 0)),
    active_tax: 0, total: 0,
  };
  const extFiled   = s.tax_extension_filed  || false;
  const taxOwed    = s.tax_owed             || 0;
  const acct       = !!(state.assistants && state.assistants.accountant);
  const acctLocked = (state.level || 0) < (ASSISTANTS_DATA.accountant.unlock_level || 0);
  el.innerHTML = `
    <div class="section-header"><span class="section-title">${pxIcon('🧾',18)} Taxes</span></div>
    <div class="card" style="margin-bottom:12px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:10px">Income This Year</div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏠',14)} Rent collected</span>
        <span class="mr-value green">${fmt(rentIncome)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('💰',14)} Flip profits</span>
        <span class="mr-value green">${fmt(flipIncome)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏪',14)} Businesses</span>
        <span class="mr-value green">${fmt(bizTotal)}</span>
      </div>
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Total income</span>
        <span class="mr-value green">${fmt(totalIncome)}</span>
      </div>
    </div>
    <div class="card" style="margin-bottom:12px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:10px">${pxIcon('🏪',14)} Business Income This Year</div>
      ${bizRows}
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Total business income</span>
        <span class="mr-value green">${fmt(bizTotal)}</span>
      </div>
    </div>
    <div class="card" style="margin-bottom:12px">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text-muted);margin-bottom:10px">Tax Bill</div>
      <div class="money-row">
        <span class="mr-label">${pxIcon('🏠',14)} Rent tax (5%)</span>
        <span class="mr-value">${fmt(tb.rent_tax)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">Business + flip income</span>
        <span class="mr-value">${fmt(flipIncome + bizTotal)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">− Deductions${acct ? ' <span style="color:var(--positive)">(+15% acct.)</span>' : ''}</span>
        <span class="mr-value" style="color:var(--positive)">−${fmt(tb.deductions)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">Taxable (after deductions)</span>
        <span class="mr-value">${fmt(tb.taxable_active)}</span>
      </div>
      <div class="money-row">
        <span class="mr-label">Business + flip tax (brackets)</span>
        <span class="mr-value">${fmt(tb.active_tax)}</span>
      </div>
      <div class="money-row" style="border-top:1px solid var(--border);padding-top:10px;margin-top:6px;font-weight:800">
        <span class="mr-label">Est. total owed</span>
        <span class="mr-value" style="color:${tb.total > 0 ? '#C62828' : 'var(--text-muted)'}">${fmt(tb.total)}</span>
      </div>
      <div style="font-size:10px;color:var(--text-muted);margin-top:8px;line-height:1.5">Brackets on business+flip: 8% to $25k · 15% to $100k · 22% to $300k · 30% beyond.</div>
    </div>
    <div class="card" style="margin-bottom:12px;border:${acct ? '2px solid var(--positive)' : '1px solid var(--border)'}">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:22px">🧮</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:13px">Accountant</div>
          <div style="font-size:11px;color:var(--text-muted)">Auto-files on time & finds 15% more write-offs.</div>
          <div style="font-size:11px;margin-top:2px;color:${acct ? 'var(--positive)' : 'var(--text-muted)'}">${acct ? '🟢 On retainer — $2,800/mo' : acctLocked ? `🔒 Unlocks at Level ${ASSISTANTS_DATA.accountant.unlock_level}` : '⚫ Not hired'}</div>
        </div>
        ${acctLocked
          ? `<button class="btn btn-sm btn-ghost" style="flex-shrink:0" disabled>Lvl ${ASSISTANTS_DATA.accountant.unlock_level}</button>`
          : `<button class="btn btn-sm ${acct ? 'btn-ghost' : 'btn-primary'}" style="flex-shrink:0" onclick="toggleAccountant()">${acct ? 'Fire' : 'Hire — $2,800/mo'}</button>`}
      </div>
      <div style="font-size:10px;color:var(--text-muted);margin-top:8px">Also available in Personal → Career → Assistants, alongside the Property Manager.</div>
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
      💡 Rent is taxed gently at <strong>5%</strong>. Business + flip profits ride progressive brackets, minus deductible operating expenses — <strong>staff wages, CostPro supplies, and equipment upkeep</strong>. Reinvesting in your operations lowers your bill.<br><br>
      ${pxIcon('📅',14)} Tax Day is <strong>Winter Day 28</strong> (7-day heads-up first). Pay immediately or file a free extension (due Spring Day 7). ${acct ? 'Your <strong>accountant</strong> handles it automatically.' : ''}
    </div>
  `;
}

async function toggleAccountant() {
  const hired = !!(state.assistants && state.assistants.accountant);
  const res = await api(hired ? '/fire_assistant' : '/hire_assistant', 'POST', { key: 'accountant' });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  await refreshState();
  renderTaxes();
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

  // Credit score gauge
  const score  = data.credit_score || (bank.credit_score || 650);
  const clabel = data.credit_label || 'Fair';
  const cpct   = Math.round((score - 300) / 550 * 100);
  const ccol   = score >= 760 ? 'var(--positive)' : score >= 700 ? '#7CB342' : score >= 640 ? 'var(--warning)' : score >= 580 ? '#FB8C00' : 'var(--negative)';
  const creditHtml = `
    <div class="section-header"><span class="section-title">${pxIcon('📊',18)} Credit Score</span></div>
    <div class="card" style="margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px">
        <div><div style="font-size:30px;font-weight:800;color:${ccol};line-height:1">${score}</div><div style="font-size:11px;color:var(--text-muted)">of 850</div></div>
        <div class="card-badge" style="background:${ccol};color:#fff">${clabel}</div>
      </div>
      <div class="condition-bar"><div class="condition-fill" style="width:${cpct}%;background:${ccol}"></div></div>
      <div style="font-size:11px;color:var(--text-muted);margin-top:8px;line-height:1.5">Higher credit → lower APR, bigger loans, and access to better products. On-time payments build it; missed payments wreck it.</div>
    </div>`;

  // Certificates of Deposit
  const cds = bank.cds || [];
  const cdPenPct = Math.round((data.cd_penalty_pct || 0.03) * 100);
  const activeCdsHtml = cds.map(cd => {
    const daysLeft = Math.max(0, cd.mature_day - (state.day || 0));
    const interest = cd.payout - cd.principal;
    return `<div class="card" style="margin-bottom:8px">
      <div class="card-header">
        <div class="card-icon">${pxIcon('🔒')}</div>
        <div style="flex:1">
          <div class="card-title">${cd.name}</div>
          <div class="card-subtitle">${fmt(cd.principal)} locked → ${fmt(cd.payout)} (+${fmt(interest)})</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:15px;font-weight:800;color:${daysLeft === 0 ? 'var(--positive)' : 'var(--text-1)'}">${daysLeft === 0 ? 'Ready' : daysLeft + 'd'}</div>
          <div style="font-size:10px;color:var(--text-muted)">${daysLeft === 0 ? 'matures next advance' : 'to maturity'}</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" style="color:var(--negative)" onclick="withdrawCd(${cd.id})">Cash out early — forfeit interest + ${cdPenPct}% penalty</button>
    </div>`;
  }).join('');
  const cdOffersHtml = (data.cd_terms || []).map(t => `
    <div class="card" style="cursor:pointer;margin-bottom:8px" onclick="showCdModal('${t.key}')">
      <div class="card-header">
        <div class="card-icon">${pxIcon('📜')}</div>
        <div style="flex:1"><div class="card-title">${t.name}</div><div class="card-subtitle">${t.desc}</div></div>
        <div style="text-align:right"><div style="font-size:15px;font-weight:800;color:var(--positive)">+${Math.round(t.yield*100)}%</div><div style="font-size:10px;color:var(--text-muted)">guaranteed</div></div>
      </div>
    </div>`).join('');
  const cdHtml = `
    <div class="section-header"><span class="section-title">${pxIcon('📜',18)} Certificates of Deposit</span></div>
    ${activeCdsHtml}
    <div style="font-size:11px;color:var(--text-muted);margin:4px 0 8px">Lock cash for a fixed term at a guaranteed return that beats savings. Cashing out early forfeits the interest plus a ${cdPenPct}% penalty.</div>
    ${cdOffersHtml}`;

  document.getElementById('bank-savings-section').innerHTML = creditHtml + `
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
    </div>` + cdHtml;

  const loansHtml = bank.loans?.length > 0
    ? bank.loans.map(l => {
        const termWks  = l.term_weeks  || (l.term_seasons || 0) * 4 || (l.term || 0) * 4;
        const paidWks  = l.weeks_paid  || 0;
        const leftWks  = Math.max(0, termWks - paidWks);
        const leftSeas = Math.ceil(leftWks / 4);
        const pctLeft  = termWks > 0 ? Math.max(5, Math.min(95, (leftWks / termWks) * 100)) : 5;
        const orig     = l.original_amount || (l.weekly_payment || 0) * termWks;
        const paidOff  = orig > 0 ? Math.round(((orig - l.balance) / orig) * 100) : 0;
        const aprTxt  = l.apr != null ? ` · ${(l.apr*100).toFixed(1)}% APR` : '';
        const missed  = (l.missed || 0) > 0
          ? `<span style="background:var(--negative);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700;margin-left:6px">⚠ ${l.missed} missed</span>`
          : (l.refinanced ? `<span style="background:var(--positive);color:#fff;border-radius:5px;font-size:10px;padding:2px 7px;font-weight:700;margin-left:6px">refinanced</span>` : '');
        return `<div class="card">
          <div class="card-header">
            <div class="card-icon">${pxIcon(l.icon)}</div>
            <div style="flex:1">
              <div class="card-title">${l.product}${missed}</div>
              <div class="card-subtitle">${fmt(l.weekly_payment || 0)}/wk · ${leftSeas} season${leftSeas !== 1 ? 's' : ''} left${aprTxt}</div>
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
          <div class="btn-row">
            <button class="btn btn-ghost btn-sm" onclick="showExtraPaymentModal(${l.id}, ${Math.ceil(l.balance)})">${pxIcon('💸',14)} Extra Payment</button>
            <button class="btn btn-ghost btn-sm" onclick="refinanceLoan(${l.id})">${pxIcon('🔁',14)} Refinance</button>
          </div>
        </div>`;}).join('')
    : '';

  document.getElementById('bank-loans-section').innerHTML = bank.loans?.length > 0
    ? `<div class="section-header"><span class="section-title">${pxIcon('📄',18)} Active Loans</span></div>${loansHtml}`
    : '';

  document.getElementById('bank-products-section').innerHTML = `
    <div class="section-header"><span class="section-title">${pxIcon('🏦',18)} Take Out a Loan</span></div>
    ${data.products.map(p => {
      const locked = !p.qualifies;
      return `
      <div class="card" style="${locked ? 'opacity:0.55' : 'cursor:pointer'}" ${locked ? '' : `onclick="showLoanModal('${p.key}')"`}>
        <div class="card-header">
          <div class="card-icon">${pxIcon(locked ? '🔒' : p.icon)}</div>
          <div style="flex:1">
            <div class="card-title">${p.name}</div>
            <div class="card-subtitle">${p.desc}</div>
          </div>
          <div style="text-align:right;flex-shrink:0">
            <div style="font-size:13px;font-weight:700;color:var(--negative)">${(p.effective_apr*100).toFixed(1)}% APR</div>
            <div style="font-size:11px;color:var(--text-muted)">${p.term_seasons} season term</div>
          </div>
        </div>
        ${locked
          ? `<div style="font-size:12px;color:var(--warning);font-weight:700">${pxIcon('🔒',12)} Requires a credit score of ${p.min_score}+</div>`
          : `<div class="money-row"><span class="mr-label">Max at your credit</span><span class="mr-value">${fmt(p.min)} – ${fmt(p.effective_max)}</span></div>
             <div class="money-row"><span class="mr-label">Example Payment</span><span class="mr-value orange">${fmt(p.sample_payment)}/wk on ${fmt(p.min)}</span></div>`}
      </div>`;}).join('')}`;
}

function showLoanModal(productKey) {
  openModal(`<div class="modal-handle"></div><div class="modal-title">Loading…</div>`);
  api('/bank/products').then(data => {
    const p = data.products.find(x => x.key === productKey);
    openModal(`
      <div class="modal-handle"></div>
      <div class="modal-title">${pxIcon(p.icon)} ${p.name}</div>
      <div class="modal-subtitle">${(p.effective_apr*100).toFixed(1)}% APR at your credit · ${p.term_seasons}-season term</div>
      <div style="margin-bottom:12px">
        <label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">Amount (${fmt(p.min)}–${fmt(p.effective_max)})</label>
        <input id="loan-amount" type="number" min="${p.min}" max="${p.effective_max}" step="500" value="${p.min}"
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
  sfx.loan();
  toast(`Loan approved! ${fmt(res.loan.weekly_payment)}/wk`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

async function refinanceLoan(loanId) {
  const res = await api('/bank/loan/refinance', 'POST', { loan_id: loanId });
  if (res.error) { toast(res.error, 'info'); return; }
  sfx.loan?.();
  toast(`Refinanced to ${(res.new_apr*100).toFixed(1)}% APR (fee ${fmt(res.fee)})`, 'success');
  await refreshState();
  renderAll();
  renderBank();
}

function showCdModal(termKey) {
  openModal(`<div class="modal-handle"></div><div class="modal-title">Loading…</div>`);
  api('/bank/products').then(data => {
    const t = (data.cd_terms || []).find(x => x.key === termKey);
    if (!t) { closeModal(); return; }
    const minD = data.cd_min || 1000;
    const start = Math.max(minD, Math.min(Math.floor((state.cash || 0)), 10000));
    openModal(`
      <div class="modal-handle"></div>
      <div class="modal-title">${pxIcon('📜')} ${t.name}</div>
      <div class="modal-subtitle">${t.desc} · +${Math.round(t.yield*100)}% guaranteed at maturity</div>
      <div style="margin:8px 0 12px">
        <label style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">Deposit (min ${fmt(minD)})</label>
        <input id="cd-amount" type="number" min="${minD}" step="500" value="${start}"
          style="width:100%;padding:10px;border:2px solid var(--border);border-radius:var(--radius-sm);font-size:16px;font-weight:700"
          oninput="previewCd(${t.yield})">
      </div>
      <div id="cd-preview" class="card" style="background:var(--surface-2);margin-bottom:12px"></div>
      <div class="btn-row">
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="openCd('${termKey}')">Lock It In</button>
      </div>`);
    previewCd(t.yield);
  });
}

function previewCd(yld) {
  const amt = parseInt(document.getElementById('cd-amount')?.value || '0');
  const el  = document.getElementById('cd-preview');
  if (!el) return;
  const payout = Math.round(amt * (1 + yld));
  el.innerHTML = `
    <div class="money-row"><span class="mr-label">You lock</span><span class="mr-value">${fmt(amt)}</span></div>
    <div class="money-row"><span class="mr-label">Interest earned</span><span class="mr-value green">+${fmt(payout - amt)}</span></div>
    <div class="money-row" style="font-weight:800"><span class="mr-label">Payout at maturity</span><span class="mr-value green">${fmt(payout)}</span></div>`;
}

async function openCd(termKey) {
  const amount = parseInt(document.getElementById('cd-amount')?.value || '0');
  const res = await api('/bank/cd/open', 'POST', { term_key: termKey, amount });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.purchase?.();
  toast('CD locked in.', 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

async function withdrawCd(cdId) {
  const res = await api('/bank/cd/withdraw', 'POST', { cd_id: cdId });
  if (res.error) { toast(res.error, 'error'); return; }
  sfx.toggle?.();
  toast(res.early ? `Cashed out early: ${fmt(res.payout)} (−${fmt(res.penalty)} penalty)` : `Matured: ${fmt(res.payout)}`, res.early ? 'warning' : 'success');
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
  sfx.loanPay();
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
  sfx.deposit();
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
  sfx.withdraw();
  toast(`Withdrew ${fmt(parseInt(amount))}`, 'success');
  closeModal();
  await refreshState();
  renderAll();
  renderBank();
}

// ── Music System ──────────────────────────────────────────────────────────────
const MUSIC_VOLS        = [-4, -5, -1, -21, -11, -15];
const MUSIC_LAYER_NAMES = ['Xylophone','Drums','Bass','String Pads','Counter-Melody','Bell Shimmer'];

let _musicReady           = false;
let _musicStarted         = false;
let _musicVolNodes        = [];
let _musicEnabled         = localStorage.getItem('musicEnabled') !== '0';
let _musicAutoStartHandler = null;

function musicTargetLevel() {
  if (!_musicEnabled) return -1;
  const gameLevel = state ? Math.min(state.level ?? 0, 5) : 0;
  const manual    = localStorage.getItem('musicManualLevel');
  return manual !== null ? Math.min(parseInt(manual), gameLevel) : gameLevel;
}

function initMusicSynths() {
  if (_musicReady || typeof Tone === 'undefined') return;
  _musicReady = true;

  const mute = v => { v.volume.value = -Infinity; return v; };
  const xylV = mute(new Tone.Volume(0).toDestination());
  const drmV = mute(new Tone.Volume(0).toDestination());
  const basV = mute(new Tone.Volume(0).toDestination());
  const padV = mute(new Tone.Volume(0).toDestination());
  const cntV = mute(new Tone.Volume(0).toDestination());
  const belV = mute(new Tone.Volume(0).toDestination());
  _musicVolNodes = [xylV, drmV, basV, padV, cntV, belV];

  const xyl = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: 'triangle' },
    envelope: { attack: 0.001, decay: 0.2, sustain: 0, release: 0.1 }
  }).connect(xylV);
  const mel = [
    'E5',null,'C5','A4', null,'G5','E5',null, 'C5','E5','A4',null, 'D5',null,'E5',null,
    'D5',null,'B4','G4', null,'F5','D5',null, 'B4','D5','G4',null, 'C5','B4','A4','G4',
    'C5',null,'A4','F4', null,'E5','C5',null, 'A4','C5','F4',null, 'B4',null,'C5',null,
    'B4',null,'G4','E4', null,'D5','B4',null, 'G4','B4','E4',null, 'G4','A4','B4','C5'
  ];
  new Tone.Sequence((t,n) => { if(n) xyl.triggerAttackRelease(n,'8n',t); }, mel, '16n').start(0);

  const kick  = new Tone.MembraneSynth({ pitchDecay:0.08, octaves:6, envelope:{attack:0.001,decay:0.25,sustain:0,release:0.1} }).connect(drmV);
  const snare = new Tone.NoiseSynth({ noise:{type:'white'}, envelope:{attack:0.001,decay:0.1,sustain:0,release:0.05} }).connect(drmV);
  const hh    = new Tone.MetalSynth({ frequency:500, harmonicity:4, modulationIndex:20, resonance:4000, octaves:1.5, envelope:{attack:0.001,decay:0.03,release:0.01} }).connect(drmV);
  const kp    = [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0];
  new Tone.Sequence((t,v) => { if(v) kick.triggerAttackRelease('C1','8n',t); }, [...kp,...kp,...kp,...kp], '16n').start(0);
  new Tone.Sequence((t,v) => { if(v) snare.triggerAttackRelease('16n',t); }, [
    0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,
    0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,
    0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,
    0,0,0,0,1,0,0,0,0,0,0,0,1,1,1,1
  ], '16n').start(0);
  new Tone.Sequence((t,v) => { if(v) hh.triggerAttackRelease('32n',t); },
    [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], '16n').start(0);

  const bFilt = new Tone.Filter({ frequency:580, type:'lowpass', rolloff:-24 }).connect(basV);
  const bDist = new Tone.Distortion(0.1).connect(bFilt);
  const bass  = new Tone.Synth({
    oscillator: { type:'fatsawtooth', spread:18, count:2 },
    envelope: { attack:0.006, decay:0.12, sustain:0.9, release:2.2 }
  }).connect(bDist);
  const bn = [
    'A1',null,null,null,'C2',null,null,null,'E1',null,null,null,'A1',null,null,null,
    'G1',null,null,null,'B1',null,null,null,'D2',null,null,null,'G1',null,null,null,
    'F1',null,null,null,'A1',null,null,null,'C2',null,null,null,'F1',null,null,null,
    'E1',null,null,null,'G1',null,null,null,'B1',null,null,null,'E1',null,null,null
  ];
  new Tone.Sequence((t,n) => { if(n) bass.triggerAttackRelease(n,'2n',t); }, bn, '16n').start(0);

  const pFilt = new Tone.Filter({ frequency:1100, type:'lowpass' }).connect(padV);
  const pads  = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type:'sawtooth' },
    envelope: { attack:1.8, decay:0.3, sustain:0.88, release:4 }
  }).connect(pFilt);
  new Tone.Sequence((t,c) => { if(c) pads.triggerAttackRelease(c,'1m',t); }, [
    ['A2','E3','A3','C4','E4'],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,
    ['G2','D3','G3','B3','D4'],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,
    ['F2','C3','F3','A3','C4'],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,
    ['E2','B2','E3','G#3','B3'],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null
  ], '16n').start(0);

  const counter = new Tone.Synth({
    oscillator: { type:'sine' },
    envelope: { attack:0.08, decay:0.3, sustain:0.55, release:0.9 }
  }).connect(cntV);
  const cn = [
    'A3',null,null,null,'C4',null,null,null,'E4',null,null,null,'G4',null,null,null,
    'G3',null,null,null,'B3',null,null,null,'D4',null,null,null,'F4',null,null,null,
    'F3',null,null,null,'A3',null,null,null,'C4',null,null,null,'E4',null,null,null,
    'E3',null,null,null,'G#3',null,null,null,'B3',null,null,null,'D4',null,null,null
  ];
  new Tone.Sequence((t,n) => { if(n) counter.triggerAttackRelease(n,'4n',t); }, cn, '16n').start(0);

  const bell = new Tone.Synth({
    oscillator: { type:'triangle' },
    envelope: { attack:0.001, decay:0.45, sustain:0, release:0.35 }
  }).connect(belV);
  const blnotes = [
    'A5','C6','E5','A5','A5','C6','E5','A5','A5','C6','E5','A5','A5','C6','E5','A5',
    'G5','B5','D5','G5','G5','B5','D5','G5','G5','B5','D5','G5','G5','B5','D5','G5',
    'F5','A5','C5','F5','F5','A5','C5','F5','F5','A5','C5','F5','F5','A5','C5','F5',
    'E5','G#5','B4','E5','E5','G#5','B4','E5','E5','G#5','B4','E5','E5','G#5','B4','E5'
  ];
  new Tone.Sequence((t,n) => { if(n) bell.triggerAttackRelease(n,'16n',t); }, blnotes, '16n').start(0);

  Tone.getTransport().bpm.value = 92;
}

function syncMusicToLevel(targetLevel) {
  if (!_musicReady || !_musicStarted || _musicVolNodes.length === 0) return;
  for (let i = 0; i <= 5; i++) {
    const shouldPlay = _musicEnabled && i <= targetLevel;
    const vol        = _musicVolNodes[i].volume.value;
    if (shouldPlay && vol <= -50)  _musicVolNodes[i].volume.rampTo(MUSIC_VOLS[i], 2);
    if (!shouldPlay && vol > -50)  _musicVolNodes[i].volume.rampTo(-Infinity, 1.5);
  }
}

function _clearMusicAutoStart() {
  if (_musicAutoStartHandler) {
    document.removeEventListener('touchend', _musicAutoStartHandler, false);
    document.removeEventListener('click',    _musicAutoStartHandler, false);
    _musicAutoStartHandler = null;
  }
}

function setupMusicAutoStart() {
  if (!_musicEnabled || _musicStarted || _musicAutoStartHandler) return;
  // Use a plain function (not async) so iOS recognises the full call stack
  // as a user-gesture context. Synths are created here (not at page load)
  // so the AudioContext is born inside the gesture, never pre-suspended.
  _musicAutoStartHandler = function() {
    _clearMusicAutoStart();
    if (!_musicReady) initMusicSynths();
    Tone.start().then(function() {
      _sfxReady = true;
      if (!_musicStarted) {
        _musicStarted = true;
        Tone.getTransport().start();
      }
      DarkMusic.ensure();
      updateMusicMode();
    });
  };
  document.addEventListener('touchend', _musicAutoStartHandler, false);
  document.addEventListener('click',    _musicAutoStartHandler, false);
}

function toggleMusicEnabled(on) {
  _musicEnabled = on;
  localStorage.setItem('musicEnabled', on ? '1' : '0');
  if (on) {
    _clearMusicAutoStart();
    if (!_musicReady) initMusicSynths();
    Tone.start().then(function() {
      _sfxReady = true;
      if (!_musicStarted) {
        _musicStarted = true;
        Tone.getTransport().start();
      }
      DarkMusic.ensure();
      updateMusicMode();
    });
  } else {
    DarkMusic.stop();
    syncMusicToLevel(-1);
  }
  renderSettings();
}

function setMusicManualLevel(val) {
  if (val === '') localStorage.removeItem('musicManualLevel');
  else            localStorage.setItem('musicManualLevel', val);
  syncMusicToLevel(musicTargetLevel());
}

// ── Off the Books theme: "Cold Blooded" ────────────────────────────────────────
// A dedicated dark-mode track (raw Web Audio on Tone's context). 10 layers reveal by
// Street Cred rank, same idea as the normal song. Only one track is audible at a time —
// updateMusicMode() mutes the normal song and runs this when state.mode === 'dark'.
const DARK_MUSIC_LAYERS = ['Deep bell + crackle','Filthy bass','Heavy kick + clap','Drill hats',
  'Dark drone','Tritone stabs','Sub + groan','Dark strings','Whistle lead','Full mix + choir'];

const DarkMusic = (function() {
  var ctx=null, master, comp, conv, lg=[], noiseBuf, distCurve;
  var running=false, timer=null, level=0, built=false;
  var BPM=130, beat=60/BPM, barDur=beat*4, barTime=0, barIdx=0;
  var mix=[0.55,1.0,0.92,0.4,0.45,0.5,0.6,0.28,0.5,0.55];

  function f(n){var m={C:0,Db:1,'C#':1,D:2,Eb:3,'D#':3,E:4,F:5,Gb:6,'F#':6,G:7,Ab:8,'G#':8,A:9,Bb:10,'A#':10,B:11};
    var t=n.match(/^([A-G][b#]?)(\d)$/);return 440*Math.pow(2,(((+t[2]+1)*12+m[t[1]])-69)/12);}
  function curve(k){var n=1024,c=new Float32Array(n);for(var i=0;i<n;i++){var x=i*2/n-1;c[i]=(3+k)*x*20*Math.PI/180/(Math.PI+k*Math.abs(x));}return c;}

  function build() {
    if (built || typeof Tone === 'undefined') return;
    try { ctx = Tone.getContext().rawContext; } catch(e) { try { ctx = Tone.context.rawContext || Tone.context; } catch(e2) { return; } }
    if (!ctx) return;
    distCurve = curve(8);
    master = ctx.createGain(); master.gain.value = 0.5;
    comp = ctx.createDynamicsCompressor(); comp.threshold.value=-18; comp.ratio.value=6; comp.attack.value=0.003; comp.release.value=0.2;
    master.connect(comp); comp.connect(ctx.destination);
    var len=ctx.sampleRate*2.6; conv=ctx.createConvolver(); var ib=ctx.createBuffer(2,len,ctx.sampleRate);
    for(var c=0;c<2;c++){var d=ib.getChannelData(c);for(var i=0;i<len;i++)d[i]=(Math.random()*2-1)*Math.pow(1-i/len,2.0);}
    conv.buffer=ib; var rv=ctx.createGain(); rv.gain.value=0.42; conv.connect(rv); rv.connect(master);
    noiseBuf=ctx.createBuffer(1,ctx.sampleRate,ctx.sampleRate); var nd=noiseBuf.getChannelData(0);
    for(var k=0;k<nd.length;k++)nd[k]=Math.random()*2-1;
    lg=[]; for(var L=0;L<10;L++){var g=ctx.createGain(); g.gain.value=0; g.connect(master); if(L===0||L===7||L===8||L===9)g.connect(conv); lg.push(g);}
    built=true;
  }

  function tone(dest,o){var osc=ctx.createOscillator();osc.type=o.type||'sawtooth';osc.frequency.setValueAtTime(o.freq,o.t);
    if(o.glide)osc.frequency.exponentialRampToValueAtTime(o.glide,o.t+o.dur);if(o.detune)osc.detune.value=o.detune;var node=osc;
    if(o.filter){var fl=ctx.createBiquadFilter();fl.type=o.ft||'lowpass';fl.frequency.value=o.filter;if(o.q)fl.Q.value=o.q;node.connect(fl);node=fl;}
    var g=ctx.createGain();var a=o.atk==null?0.008:o.atk,rel=o.rel==null?0.09:o.rel;
    g.gain.setValueAtTime(0.0001,o.t);g.gain.linearRampToValueAtTime(o.peak,o.t+a);g.gain.setTargetAtTime(0.0001,o.t+o.dur,rel);
    node.connect(g);g.connect(dest);osc.start(o.t);osc.stop(o.t+o.dur+rel*7+0.05);}
  function noise(dest,t,dur,ft,fr,q,pk){var s=ctx.createBufferSource();s.buffer=noiseBuf;var fl=ctx.createBiquadFilter();fl.type=ft;fl.frequency.value=fr;if(q)fl.Q.value=q;
    var g=ctx.createGain();g.gain.setValueAtTime(pk,t);g.gain.exponentialRampToValueAtTime(0.0008,t+dur);s.connect(fl);fl.connect(g);g.connect(dest);s.start(t);s.stop(t+dur+0.03);}
  function kick(t){var o=ctx.createOscillator();o.type='sine';o.frequency.setValueAtTime(135,t);o.frequency.exponentialRampToValueAtTime(40,t+0.13);
    var ds=ctx.createWaveShaper();ds.curve=distCurve;var g=ctx.createGain();g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(1,t+0.006);g.gain.exponentialRampToValueAtTime(0.001,t+0.4);
    o.connect(ds);ds.connect(g);g.connect(lg[2]);o.start(t);o.stop(t+0.5);}
  function bass(t,freq,dur,glideFrom){var ds=ctx.createWaveShaper();ds.curve=distCurve;ds.oversample='2x';
    var lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.setValueAtTime(140,t);lp.frequency.linearRampToValueAtTime(1100,t+0.04);lp.frequency.setTargetAtTime(150,t+0.12,0.18);lp.Q.value=5;
    var g=ctx.createGain();g.gain.setValueAtTime(0.0001,t);g.gain.linearRampToValueAtTime(1,t+0.012);g.gain.setTargetAtTime(0.0001,t+dur,0.07);
    [[-9,0.5,'sawtooth',false],[10,0.5,'sawtooth',false],[0,1.0,'sine',true]].forEach(function(p){
      var o=ctx.createOscillator();o.type=p[2];var fr=p[3]?freq/2:freq;
      if(glideFrom){o.frequency.setValueAtTime(p[3]?glideFrom/2:glideFrom,t);o.frequency.exponentialRampToValueAtTime(fr,t+0.07);}else o.frequency.setValueAtTime(fr,t);
      o.detune.value=p[0];var og=ctx.createGain();og.gain.value=p[1];o.connect(og);og.connect(p[3]?g:ds);o.start(t);o.stop(t+dur+0.5);});
    ds.connect(lp);lp.connect(g);g.connect(lg[1]);}
  function whistle(t,freq,dur){var lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=3400;lp.Q.value=0.7;
    var g=ctx.createGain();g.gain.setValueAtTime(0.0001,t);g.gain.linearRampToValueAtTime(0.24,t+0.06);g.gain.setTargetAtTime(0.0001,t+dur,0.16);lp.connect(g);g.connect(lg[8]);
    var lfo=ctx.createOscillator();lfo.type='sine';lfo.frequency.value=5.1;var ld=ctx.createGain();ld.gain.value=11;lfo.connect(ld);lfo.start(t);lfo.stop(t+dur+0.4);
    [['triangle',0,1],['triangle',-7,0.55],['sine',5,0.4]].forEach(function(p){var o=ctx.createOscillator();o.type=p[0];o.frequency.value=freq;o.detune.value=p[1];ld.connect(o.detune);
      var og=ctx.createGain();og.gain.value=p[2];o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+0.4);});}

  var R=['D2','Eb2','D2','Eb2'];
  var BELL={0:[[0,'A3'],[2,'F3']],1:[[0,'Bb3'],[2,'G3']],2:[[0,'D4'],[2,'A3']],3:[[0,'Eb4'],[1.5,'Bb3'],[2.5,'G3']]};
  var TRI={0:['D3','F3','A3'],1:['Eb3','G3','Bb3'],2:['D3','F3','A3'],3:['Eb3','G3','Bb3']};
  var STAB={0:['D3','Ab3'],1:['Eb3','A3'],2:['D3','Ab3'],3:['Eb3','A3']};
  var STR={0:['D4','A4'],1:['Eb4','Bb4'],2:['D4','A4'],3:['Eb4','Bb4']};
  var LEAD={0:[[0,'A5',3.2]],1:[[0,'Bb5',1.7],[2,'A5',1.7]],2:[[0,'F5',3.2]],3:[[0,'Eb5',1.3],[1.5,'D5',1.2],[2.9,'A4',1.0]]};
  var CHOIR={0:['D5','F5','A5'],1:['Eb5','G5','Bb5'],2:['D5','F5','A5'],3:['Eb5','G5','Bb5']};

  function scheduleBar(t0,ci){var b=function(x){return t0+x*beat;};
    noise(lg[0],b(0),barDur,'lowpass',850,0,0.07);
    for(var p=0;p<7;p++)noise(lg[0],b(Math.random()*4),0.025,'bandpass',650+Math.random()*1600,2,0.06);
    BELL[ci].forEach(function(e){var fr=f(e[1]);
      tone(lg[0],{type:'triangle',freq:fr,t:b(e[0]),dur:beat*1.5,peak:0.4,atk:0.02,rel:0.45,filter:1150,detune:-9});
      tone(lg[0],{type:'triangle',freq:fr,t:b(e[0]),dur:beat*1.5,peak:0.4,atk:0.02,rel:0.45,filter:1150,detune:10});
      tone(lg[0],{type:'sine',freq:fr/2,t:b(e[0]),dur:beat*1.7,peak:0.5,atk:0.03,rel:0.5,filter:520});});
    var gf=f(R[(ci+3)%4]),rf=f(R[ci]); bass(b(0),rf,beat*1.2,gf); bass(b(1.5),rf,beat*0.45); bass(b(2.5),rf,beat*0.5); bass(b(3.25),rf,beat*0.4);
    [0,1.5,3.5].forEach(function(x){kick(b(x));});
    noise(lg[2],b(2),0.18,'bandpass',1500,1,0.6); noise(lg[2],b(2.03),0.13,'bandpass',2100,1.6,0.4); noise(lg[2],b(2.05),0.09,'highpass',3000,0,0.25);
    for(var h=0;h<8;h++)noise(lg[3],b(h*0.5),0.028,'highpass',8600,0,h%2?0.2:0.32);
    [3.33,3.66,3.999].forEach(function(x){noise(lg[3],b(x),0.02,'highpass',9000,0,0.26);});
    noise(lg[3],b(1),0.04,'bandpass',3600,8,0.18); noise(lg[3],b(3),0.04,'bandpass',4200,9,0.18);
    TRI[ci].forEach(function(nn){tone(lg[4],{type:'sawtooth',freq:f(nn),t:b(0),dur:beat*3.9,peak:0.16,atk:0.6,rel:0.5,filter:560,detune:-10});tone(lg[4],{type:'sawtooth',freq:f(nn),t:b(0),dur:beat*3.9,peak:0.16,atk:0.6,rel:0.5,filter:560,detune:11});});
    [0,2.5].forEach(function(x){STAB[ci].forEach(function(nn){var ds=ctx.createWaveShaper();ds.curve=distCurve;
      var o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=f(nn);o.detune.value=(Math.random()*16-8);
      var lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=1400;var g=ctx.createGain();var t=b(x);
      g.gain.setValueAtTime(0.0001,t);g.gain.linearRampToValueAtTime(0.34,t+0.01);g.gain.setTargetAtTime(0.0001,t+0.18,0.06);
      o.connect(ds);ds.connect(lp);lp.connect(g);g.connect(lg[5]);o.start(t);o.stop(t+0.5);});});
    var rf2=f(R[ci]);
    tone(lg[6],{type:'sawtooth',freq:rf2/2,t:b(0),dur:beat*3.8,peak:0.3,atk:0.25,rel:0.4,filter:140,glide:rf2/2*1.04});
    tone(lg[6],{type:'sine',freq:rf2/2,t:b(0),dur:beat*3.8,peak:0.45,atk:0.1,rel:0.4,filter:120});
    STR[ci].forEach(function(nn){tone(lg[7],{type:'sawtooth',freq:f(nn),t:b(0),dur:beat*3.9,peak:0.1,atk:0.9,rel:0.7,filter:1500,detune:-6});tone(lg[7],{type:'sawtooth',freq:f(nn),t:b(0),dur:beat*3.9,peak:0.1,atk:0.9,rel:0.7,filter:1500,detune:7});});
    LEAD[ci].forEach(function(e){whistle(b(e[0]),f(e[1]),beat*e[2]);});
    CHOIR[ci].forEach(function(nn){tone(lg[9],{type:'sawtooth',freq:f(nn),t:b(0),dur:beat*3.9,peak:0.06,atk:0.9,rel:0.7,filter:2600,detune:10});});
    if(ci===0){var o=ctx.createOscillator();o.type='sine';o.frequency.setValueAtTime(60,t0);o.frequency.exponentialRampToValueAtTime(28,t0+0.6);var ds=ctx.createWaveShaper();ds.curve=distCurve;var g=ctx.createGain();g.gain.setValueAtTime(1,t0);g.gain.exponentialRampToValueAtTime(0.001,t0+0.7);o.connect(ds);ds.connect(g);g.connect(lg[9]);o.start(t0);o.stop(t0+0.8);noise(lg[9],t0,0.6,'lowpass',300,0,0.55);}
    if(ci===3){var s=ctx.createBufferSource();s.buffer=noiseBuf;var fl=ctx.createBiquadFilter();fl.type='bandpass';fl.Q.value=1;fl.frequency.setValueAtTime(300,b(0));fl.frequency.exponentialRampToValueAtTime(6000,b(4));var g2=ctx.createGain();g2.gain.setValueAtTime(0.0008,b(0));g2.gain.exponentialRampToValueAtTime(0.3,b(4));s.connect(fl);fl.connect(g2);g2.connect(lg[9]);s.start(b(0));s.stop(b(4));}}

  function applyLevel(){ if(!built)return; var now=ctx.currentTime; for(var i=0;i<10;i++)lg[i].gain.setTargetAtTime(i<level?mix[i]:0.0001,now,0.6); }
  function tick(){ if(!running)return; while(barTime<ctx.currentTime+0.4){ scheduleBar(barTime,barIdx%4); barTime+=barDur; barIdx++; } }

  return {
    ensure: function(){ build(); },
    start: function(){ build(); if(!built||running)return; running=true; barTime=ctx.currentTime+0.12; barIdx=0; timer=setInterval(tick,60); },
    stop: function(){ if(!built){level=0;return;} level=0; applyLevel(); running=false; if(timer){clearInterval(timer);timer=null;} },
    setLevel: function(n){ level=Math.max(0,n|0); applyLevel(); },
    isBuilt: function(){ return built; }, isRunning: function(){ return running; }, getLevel: function(){ return level; }
  };
})();

function darkMusicTargetLevel() {
  if (!_musicEnabled || !state || state.mode !== 'dark' || !state.dark) return 0;
  const rank   = Math.max(1, Math.min(state.dark.cred || 1, 10));
  const manual = localStorage.getItem('darkMusicManualLevel');
  return manual !== null ? Math.min(parseInt(manual), rank) : rank;
}

function setDarkMusicLevel(val) {
  if (val === '') localStorage.removeItem('darkMusicManualLevel');
  else            localStorage.setItem('darkMusicManualLevel', val);
  DarkMusic.setLevel(darkMusicTargetLevel());
}

// Route audio to the right track for the current game mode. Only one plays at a time.
function updateMusicMode() {
  const dark = !!(state && state.mode === 'dark');
  if (dark && _musicEnabled) {
    syncMusicToLevel(-1);                 // silence the empire theme
    if (_musicStarted) { DarkMusic.start(); DarkMusic.setLevel(darkMusicTargetLevel()); }
  } else {
    DarkMusic.stop();                     // silence Cold Blooded
    syncMusicToLevel(musicTargetLevel());
  }
}

// ── Sound Effects ─────────────────────────────────────────────────────────────
let _sfxEnabled = localStorage.getItem('sfxEnabled') !== '0';
let _sfxReady   = false;

const sfx = {
  _ok: function() { return _sfxEnabled && _sfxReady && typeof Tone !== 'undefined'; },

  cash: function() {
    if (!sfx._ok()) return;
    const b = new Tone.Synth({ oscillator:{type:'triangle'}, envelope:{attack:0.001,decay:0.18,sustain:0,release:0.1} }).toDestination();
    b.volume.value = -10;
    b.triggerAttackRelease('G5','32n');
    b.triggerAttackRelease('B5','32n','+0.08');
    b.triggerAttackRelease('E6','16n','+0.16');
    setTimeout(() => b.dispose(), 1000);
  },

  buy: function() {
    if (!sfx._ok()) return;
    const kick = new Tone.MembraneSynth({ pitchDecay:0.05,octaves:5,envelope:{attack:0.001,decay:0.18,sustain:0,release:0.1} }).toDestination();
    const clk  = new Tone.Synth({ oscillator:{type:'triangle'}, envelope:{attack:0.001,decay:0.08,sustain:0,release:0.05} }).toDestination();
    kick.volume.value = -6; clk.volume.value = -14;
    kick.triggerAttackRelease('C2','8n');
    clk.triggerAttackRelease('C5','32n','+0.06');
    setTimeout(() => { kick.dispose(); clk.dispose(); }, 800);
  },

  levelUp: function() {
    if (!sfx._ok()) return;
    const bell  = new Tone.Synth({ oscillator:{type:'triangle'}, envelope:{attack:0.001,decay:0.5,sustain:0,release:0.3} }).toDestination();
    const metal = new Tone.MetalSynth({ frequency:600,harmonicity:3,modulationIndex:16,resonance:3000,octaves:1,envelope:{attack:0.001,decay:0.6,release:0.2} }).toDestination();
    bell.volume.value = -10; metal.volume.value = -16;
    ['C6','E6','G6','C7','E7'].forEach((n,i) => bell.triggerAttackRelease(n,'16n',`+${i*0.09}`));
    metal.triggerAttackRelease('16n','+0.36');
    setTimeout(() => { bell.dispose(); metal.dispose(); }, 2000);
  },

  tap: function() {
    if (!sfx._ok()) return;
    const r = () => Math.random();
    const clickFreq = 4400 + r() * 1200;          // 4400–5600 Hz
    const clickDecay = 0.006 + r() * 0.005;       // 6–11 ms
    const clickVol  = -6  + r() * 2;              // -6 to -4 dB
    const bodyPitch = ['F2','G2','G#2','A2'][Math.floor(r() * 4)];
    const bodyDecay = 0.055 + r() * 0.03;         // 55–85 ms
    const bodyVol   = -13  + r() * 3;             // -13 to -10 dB

    const noise = new Tone.NoiseSynth({ noise:{type:'white'}, envelope:{attack:0.0001,decay:clickDecay,sustain:0,release:0.004} }).toDestination();
    const filt  = new Tone.Filter({ frequency:clickFreq, type:'bandpass', Q:2.5 }).toDestination();
    noise.connect(filt); noise.volume.value = clickVol;
    const body  = new Tone.MembraneSynth({ pitchDecay:0.025,octaves:4,envelope:{attack:0.0001,decay:bodyDecay,sustain:0,release:0.03} }).toDestination();
    body.volume.value = bodyVol;
    noise.triggerAttackRelease('64n');
    body.triggerAttackRelease(bodyPitch,'32n','+0.008');
    setTimeout(() => { noise.dispose(); filt.dispose(); body.dispose(); }, 500);
  },

  error: function() {
    if (!sfx._ok()) return;
    const s = new Tone.Synth({ oscillator:{type:'sawtooth'}, envelope:{attack:0.005,decay:0.25,sustain:0,release:0.1} }).toDestination();
    const f = new Tone.Filter({ frequency:300, type:'lowpass' }).toDestination();
    s.connect(f); s.volume.value = -12;
    s.triggerAttackRelease('A2','8n');
    setTimeout(() => { s.dispose(); f.dispose(); }, 700);
  },

  repair: function() {
    if (!sfx._ok()) return;
    const k = new Tone.MembraneSynth({ pitchDecay:0.12,octaves:6,envelope:{attack:0.001,decay:0.3,sustain:0,release:0.15} }).toDestination();
    const n = new Tone.NoiseSynth({ noise:{type:'brown'}, envelope:{attack:0.001,decay:0.1,sustain:0,release:0.05} }).toDestination();
    k.volume.value = -10; n.volume.value = -16;
    k.triggerAttackRelease('G2','8n');
    n.triggerAttackRelease('32n','+0.02');
    setTimeout(() => { k.dispose(); n.dispose(); }, 800);
  },

  complete: function() {
    if (!sfx._ok()) return;
    const p = new Tone.PolySynth(Tone.Synth, { oscillator:{type:'triangle'}, envelope:{attack:0.01,decay:0.4,sustain:0.3,release:0.5} }).toDestination();
    p.volume.value = -10;
    p.triggerAttackRelease(['C4','E4','G4','C5'],'8n');
    setTimeout(() => p.dispose(), 1500);
  },
  advTime: function() {
    if (!sfx._ok()) return;
    const ch = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.6, sustain: 0.02, release: 0.8 } }).toDestination();
    ch.volume.value = -10;
    [[0, 'E5'], [180, 'G5'], [360, 'C6']].forEach(([ms2, note]) => {
      ch.triggerAttackRelease(note, '16n', Tone.now() + ms2 / 1000);
    });
    setTimeout(() => ch.dispose(), 2500);
    const swn = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.02, decay: 0.22, sustain: 0, release: 0.15 } }).toDestination();
    const swf = new Tone.Filter(2000, 'bandpass').toDestination();
    swn.disconnect(); swn.connect(swf);
    swn.volume.value = -18;
    swn.triggerAttackRelease('8n');
    setTimeout(() => { swn.dispose(); swf.dispose(); }, 700);
  },
  infoOpen: function() {
    if (!sfx._ok()) return;
    const mc = new Tone.MetalSynth({ frequency: 180, envelope: { attack: 0.001, decay: 0.07, release: 0.04 }, harmonicity: 3.1, modulationIndex: 10, resonance: 2500, octaves: 0.5 }).toDestination();
    mc.volume.value = -13;
    mc.triggerAttackRelease('32n');
    setTimeout(function() { mc.dispose(); }, 400);
    const ni = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.03, sustain: 0, release: 0.01 } }).toDestination();
    const fi = new Tone.Filter(3500, 'bandpass').toDestination();
    ni.disconnect(); ni.connect(fi);
    ni.volume.value = -18;
    ni.triggerAttackRelease('64n');
    setTimeout(function() { ni.dispose(); fi.dispose(); }, 300);
  },
  tab: function() {
    if (!sfx._ok()) return;
    const ot = new Tone.Oscillator({ type: 'sine', frequency: 520 }).toDestination();
    ot.volume.value = -20;
    ot.start();
    ot.frequency.exponentialRampToValueAtTime(260, Tone.now() + 0.1);
    ot.volume.rampTo(-80, 0.12);
    setTimeout(function() { ot.stop(); ot.dispose(); }, 200);
  },
  accordion: function() {
    if (!sfx._ok()) return;
    const sa = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.001, decay: 0.22, sustain: 0, release: 0.08 } }).toDestination();
    sa.volume.value = -13;
    sa.frequency.setValueAtTime(330, Tone.now());
    sa.frequency.exponentialRampToValueAtTime(590, Tone.now() + 0.1);
    sa.triggerAttackRelease('E4', '16n');
    setTimeout(function() { sa.dispose(); }, 500);
    const na = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.05, sustain: 0, release: 0.01 } }).toDestination();
    const fa = new Tone.Filter(1400, 'bandpass').toDestination();
    na.disconnect(); na.connect(fa);
    na.volume.value = -22;
    na.triggerAttackRelease('32n');
    setTimeout(function() { na.dispose(); fa.dispose(); }, 300);
  },
  propOpen: function() {
    if (!sfx._ok()) return;
    [0, 130].forEach(function(delay) {
      const mp = new Tone.MembraneSynth({ pitchDecay: 0.05, octaves: 2.5, envelope: { attack: 0.001, decay: 0.2, sustain: 0, release: 0.1 } }).toDestination();
      mp.volume.value = -9;
      mp.triggerAttackRelease('C2', '8n', Tone.now() + delay / 1000);
      setTimeout(function() { mp.dispose(); }, delay + 600);
      const np = new Tone.NoiseSynth({ noise: { type: 'brown' }, envelope: { attack: 0.001, decay: 0.08, sustain: 0, release: 0.02 } }).toDestination();
      const fp = new Tone.Filter(600, 'lowpass').toDestination();
      np.disconnect(); np.connect(fp);
      np.volume.value = -14;
      np.triggerAttackRelease('16n', Tone.now() + delay / 1000);
      setTimeout(function() { np.dispose(); fp.dispose(); }, delay + 600);
    });
  },
  buyOpen: function() {
    if (!sfx._ok()) return;
    const mb = new Tone.MembraneSynth({ pitchDecay: 0.07, octaves: 4, envelope: { attack: 0.001, decay: 0.28, sustain: 0, release: 0.12 } }).toDestination();
    mb.volume.value = -7;
    mb.triggerAttackRelease('G1', '8n');
    setTimeout(function() { mb.dispose(); }, 700);
    const nb = new Tone.NoiseSynth({ noise: { type: 'brown' }, envelope: { attack: 0.001, decay: 0.1, sustain: 0, release: 0.03 } }).toDestination();
    const fb = new Tone.Filter(900, 'lowpass').toDestination();
    nb.disconnect(); nb.connect(fb);
    nb.volume.value = -11;
    nb.triggerAttackRelease('16n');
    setTimeout(function() { nb.dispose(); fb.dispose(); }, 400);
  },
  findTenant: function() {
    if (!sfx._ok()) return;
    const st = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'triangle' }, envelope: { attack: 0.01, decay: 0.9, sustain: 0.08, release: 1.2 } }).toDestination();
    st.volume.value = -11;
    st.triggerAttackRelease('G5', '4n', Tone.now());
    st.triggerAttackRelease('D5', '4n', Tone.now() + 0.38);
    setTimeout(function() { st.dispose(); }, 3000);
  },
  signLease: function() {
    if (!sfx._ok()) return;
    const nl = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.015, decay: 0.12, sustain: 0.03, release: 0.18 } }).toDestination();
    const fl = new Tone.Filter(2800, 'bandpass').toDestination();
    nl.disconnect(); nl.connect(fl);
    nl.volume.value = -13;
    nl.triggerAttackRelease('8n');
    setTimeout(function() { nl.dispose(); fl.dispose(); }, 600);
    const cl = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.7, sustain: 0.04, release: 0.9 } }).toDestination();
    cl.volume.value = -12;
    cl.triggerAttackRelease('E5', '16n', Tone.now() + 0.12);
    cl.triggerAttackRelease('G5', '16n', Tone.now() + 0.28);
    cl.triggerAttackRelease('B5', '8n',  Tone.now() + 0.44);
    setTimeout(function() { cl.dispose(); }, 3000);
  },
  specialReno: function() {
    if (!sfx._ok()) return;
    const sr = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.45, sustain: 0, release: 0.6 } }).toDestination();
    sr.volume.value = -9;
    [[0, 'C6'], [80, 'E6'], [160, 'G6'], [260, 'C7']].forEach(([ms4, note]) => {
      sr.triggerAttackRelease(note, '16n', Tone.now() + ms4 / 1000);
    });
    setTimeout(() => sr.dispose(), 2200);
    const srm = new Tone.MembraneSynth({ pitchDecay: 0.08, octaves: 5, envelope: { attack: 0.001, decay: 0.4, sustain: 0, release: 0.15 } }).toDestination();
    srm.volume.value = -6;
    srm.triggerAttackRelease('C1', '8n');
    setTimeout(() => srm.dispose(), 800);
    const srmt = new Tone.MetalSynth({ frequency: 400, envelope: { attack: 0.001, decay: 0.5, release: 0.3 }, harmonicity: 5.1, modulationIndex: 24, resonance: 5000, octaves: 2 }).toDestination();
    srmt.volume.value = -12;
    srmt.triggerAttackRelease('8n', Tone.now() + 0.1);
    setTimeout(() => srmt.dispose(), 1500);
  },
  moveIn: function() {
    if (!sfx._ok()) return;
    const mi = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'triangle' }, envelope: { attack: 0.04, decay: 0.6, sustain: 0.2, release: 1.2 } }).toDestination();
    mi.volume.value = -9;
    mi.triggerAttackRelease(['C4','E4','G4','C5'], '4n');
    setTimeout(() => {
      mi.triggerAttackRelease(['E4','G4','B4','E5'], '4n');
      setTimeout(() => mi.dispose(), 3000);
    }, 350);
    const mk = new Tone.MetalSynth({ frequency: 600, envelope: { attack: 0.001, decay: 0.12, release: 0.1 }, harmonicity: 6.1, modulationIndex: 12, resonance: 3000, octaves: 0.5 }).toDestination();
    mk.volume.value = -18;
    mk.triggerAttackRelease('32n', Tone.now() + 0.05);
    setTimeout(() => mk.dispose(), 500);
  },
  cancel: function() {
    if (!sfx._ok()) return;
    const cv = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.001, decay: 0.18, sustain: 0, release: 0.1 } }).toDestination();
    cv.volume.value = -14;
    cv.frequency.setValueAtTime(400, Tone.now());
    cv.frequency.exponentialRampToValueAtTime(200, Tone.now() + 0.18);
    cv.triggerAttackRelease('G3', '16n');
    setTimeout(() => cv.dispose(), 400);
    const cn = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.04, sustain: 0, release: 0.01 } }).toDestination();
    const cf = new Tone.Filter(1500, 'lowpass').toDestination();
    cn.disconnect(); cn.connect(cf);
    cn.volume.value = -22;
    cn.triggerAttackRelease('32n');
    setTimeout(() => { cn.dispose(); cf.dispose(); }, 200);
  },
  evict: function() {
    if (!sfx._ok()) return;
    const ev = new Tone.MembraneSynth({ pitchDecay: 0.09, octaves: 5, envelope: { attack: 0.001, decay: 0.4, sustain: 0, release: 0.15 } }).toDestination();
    ev.volume.value = -5;
    ev.triggerAttackRelease('A0', '8n');
    setTimeout(() => ev.dispose(), 800);
    const en = new Tone.NoiseSynth({ noise: { type: 'brown' }, envelope: { attack: 0.001, decay: 0.25, sustain: 0, release: 0.05 } }).toDestination();
    const ef = new Tone.Filter(400, 'lowpass').toDestination();
    en.disconnect(); en.connect(ef);
    en.volume.value = -9;
    en.triggerAttackRelease('8n');
    setTimeout(() => { en.dispose(); ef.dispose(); }, 700);
  },
  purchase: function() {
    if (!sfx._ok()) return;
    const pu = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.35, sustain: 0, release: 0.2 } }).toDestination();
    pu.volume.value = -12;
    pu.triggerAttackRelease('C5', '16n');
    setTimeout(() => { pu.triggerAttackRelease('E5', '16n'); setTimeout(() => pu.dispose(), 600); }, 110);
  },
  hire: function() {
    if (!sfx._ok()) return;
    const hi = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'sine' }, envelope: { attack: 0.01, decay: 0.4, sustain: 0.05, release: 0.4 } }).toDestination();
    hi.volume.value = -13;
    hi.triggerAttackRelease('C4', '8n', Tone.now());
    hi.triggerAttackRelease('E4', '8n', Tone.now() + 0.12);
    hi.triggerAttackRelease('G4', '8n', Tone.now() + 0.24);
    setTimeout(() => hi.dispose(), 1200);
  },
  construct: function() {
    if (!sfx._ok()) return;
    const co = new Tone.MembraneSynth({ pitchDecay: 0.03, octaves: 3, envelope: { attack: 0.001, decay: 0.2, sustain: 0, release: 0.08 } }).toDestination();
    co.volume.value = -8;
    co.triggerAttackRelease('E2', '8n');
    setTimeout(() => co.dispose(), 500);
    const cm = new Tone.MetalSynth({ frequency: 250, envelope: { attack: 0.001, decay: 0.15, release: 0.1 }, harmonicity: 4.1, modulationIndex: 8, resonance: 1500, octaves: 0.8 }).toDestination();
    cm.volume.value = -16;
    cm.triggerAttackRelease('16n', Tone.now() + 0.05);
    setTimeout(() => cm.dispose(), 600);
  },
  restock: function() {
    if (!sfx._ok()) return;
    [0, 55, 110, 165].forEach((ms3, i) => {
      const rs = new Tone.Synth({ oscillator: { type: 'sine' }, envelope: { attack: 0.001, decay: 0.12, sustain: 0, release: 0.05 } }).toDestination();
      rs.volume.value = -19;
      rs.triggerAttackRelease(330 * Math.pow(1.18, i), '32n', Tone.now() + ms3 / 1000);
      setTimeout(() => rs.dispose(), ms3 + 300);
    });
  },
  clean: function() {
    if (!sfx._ok()) return;
    const cln = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.04, decay: 0.25, sustain: 0, release: 0.18 } }).toDestination();
    const clf = new Tone.Filter(4000, 'highpass').toDestination();
    cln.disconnect(); cln.connect(clf);
    cln.volume.value = -15;
    cln.triggerAttackRelease('4n');
    setTimeout(() => { cln.dispose(); clf.dispose(); }, 800);
    const cld = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.65, sustain: 0, release: 0.45 } }).toDestination();
    cld.volume.value = -13;
    cld.triggerAttackRelease('A5', '16n', Tone.now() + 0.2);
    setTimeout(() => cld.dispose(), 1500);
  },
  toggle: function() {
    if (!sfx._ok()) return;
    const tn = new Tone.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.025, sustain: 0, release: 0.01 } }).toDestination();
    const tf = new Tone.Filter(4000, 'bandpass').toDestination();
    tn.disconnect(); tn.connect(tf);
    tn.volume.value = -15;
    tn.triggerAttackRelease('64n');
    setTimeout(() => { tn.dispose(); tf.dispose(); }, 200);
    const tc = new Tone.Synth({ oscillator: { type: 'square' }, envelope: { attack: 0.001, decay: 0.04, sustain: 0, release: 0.02 } }).toDestination();
    tc.volume.value = -20;
    tc.triggerAttackRelease('C4', '64n');
    setTimeout(() => tc.dispose(), 200);
  },
  deposit: function() {
    if (!sfx._ok()) return;
    const dp = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.45, sustain: 0.05, release: 0.35 } }).toDestination();
    dp.volume.value = -12;
    dp.frequency.setValueAtTime(330, Tone.now());
    dp.frequency.exponentialRampToValueAtTime(528, Tone.now() + 0.09);
    dp.triggerAttackRelease('C5', '8n');
    setTimeout(() => dp.dispose(), 1000);
  },
  withdraw: function() {
    if (!sfx._ok()) return;
    const wd = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.45, sustain: 0.05, release: 0.35 } }).toDestination();
    wd.volume.value = -12;
    wd.frequency.setValueAtTime(528, Tone.now());
    wd.frequency.exponentialRampToValueAtTime(330, Tone.now() + 0.09);
    wd.triggerAttackRelease('E4', '8n');
    setTimeout(() => wd.dispose(), 1000);
  },
  loan: function() {
    if (!sfx._ok()) return;
    const ln = new Tone.Synth({ oscillator: { type: 'sawtooth' }, envelope: { attack: 0.02, decay: 0.5, sustain: 0.08, release: 0.4 } }).toDestination();
    ln.volume.value = -15;
    ln.triggerAttackRelease('A2', '4n');
    setTimeout(() => ln.dispose(), 1200);
    const lnm = new Tone.MembraneSynth({ pitchDecay: 0.05, octaves: 2, envelope: { attack: 0.001, decay: 0.25, sustain: 0, release: 0.1 } }).toDestination();
    lnm.volume.value = -11;
    lnm.triggerAttackRelease('F2', '8n', Tone.now() + 0.12);
    setTimeout(() => lnm.dispose(), 700);
  },
  loanPay: function() {
    if (!sfx._ok()) return;
    const lp = new Tone.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.001, decay: 0.28, sustain: 0, release: 0.18 } }).toDestination();
    lp.volume.value = -12;
    lp.triggerAttackRelease('C5', '16n');
    setTimeout(() => { lp.triggerAttackRelease('E5', '16n'); setTimeout(() => lp.dispose(), 600); }, 100);
  },
  stockBuy: function() {
    if (!sfx._ok()) return;
    const sb = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'sine' }, envelope: { attack: 0.001, decay: 0.25, sustain: 0, release: 0.15 } }).toDestination();
    sb.volume.value = -13;
    sb.triggerAttackRelease('D5', '16n', Tone.now());
    sb.triggerAttackRelease('F#5', '16n', Tone.now() + 0.09);
    sb.triggerAttackRelease('A5', '8n',  Tone.now() + 0.18);
    setTimeout(() => sb.dispose(), 800);
  },
  stockSell: function() {
    if (!sfx._ok()) return;
    const ss = new Tone.PolySynth(Tone.Synth, { oscillator: { type: 'sine' }, envelope: { attack: 0.001, decay: 0.25, sustain: 0, release: 0.15 } }).toDestination();
    ss.volume.value = -13;
    ss.triggerAttackRelease('A5', '16n', Tone.now());
    ss.triggerAttackRelease('F#5', '16n', Tone.now() + 0.09);
    ss.triggerAttackRelease('D5', '8n',  Tone.now() + 0.18);
    setTimeout(() => ss.dispose(), 800);
  },
};

function toggleSfxEnabled(on) {
  _sfxEnabled = on;
  localStorage.setItem('sfxEnabled', on ? '1' : '0');
  renderSettings();
}

function setupSfxAutoStart() {
  if (_sfxReady || _musicEnabled || !_sfxEnabled) return;
  let _h = function() {
    document.removeEventListener('touchend', _h, false);
    document.removeEventListener('click',    _h, false);
    if (typeof Tone !== 'undefined') Tone.start().then(function() { _sfxReady = true; });
  };
  document.addEventListener('touchend', _h, false);
  document.addEventListener('click',    _h, false);
}

// ── Settings ──────────────────────────────────────────────────────────────────
function toggleDarkMode(on) {
  document.body.classList.toggle('dark', on);
  localStorage.setItem('darkMode', on ? '1' : '0');
}

function renderSettings() {
  const el = document.getElementById('page-settings');
  if (!el || !state) return;
  const s         = getSeasonInfo(state.day);
  const darkOn    = localStorage.getItem('darkMode') === '1';
  const gameLevel = Math.min(state.level ?? 0, 5);
  const manualLvl = localStorage.getItem('musicManualLevel');
  const darkGame  = state.mode === 'dark';
  const dmRank    = darkGame ? Math.max(1, Math.min((state.dark && state.dark.cred) || 1, 10)) : 0;
  const dmManual  = localStorage.getItem('darkMusicManualLevel');
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
      <div style="font-size:14px;font-weight:800;margin-bottom:10px">🎨 Appearance</div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div style="font-size:13px;font-weight:600">🌙 Dark Mode</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Easy on the eyes</div>
        </div>
        <label class="dark-toggle">
          <input type="checkbox" ${darkOn ? 'checked' : ''} onchange="toggleDarkMode(this.checked)">
          <span class="dark-toggle-track"></span>
        </label>
      </div>
    </div>

    <div class="card" style="margin-top:12px">
      <div style="font-size:14px;font-weight:800;margin-bottom:10px">🎵 Music</div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <div style="font-size:13px;font-weight:600">Background Music</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${darkGame ? 'Off the Books — “Cold Blooded”' : 'Soundtrack for your empire'}</div>
        </div>
        <label class="dark-toggle">
          <input type="checkbox" ${_musicEnabled ? 'checked' : ''} onchange="toggleMusicEnabled(this.checked)">
          <span class="dark-toggle-track"></span>
        </label>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
        <div>
          <div style="font-size:13px;font-weight:600">🔊 Sound Effects</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Taps, cha-chings, alerts</div>
        </div>
        <label class="dark-toggle">
          <input type="checkbox" ${_sfxEnabled ? 'checked' : ''} onchange="toggleSfxEnabled(this.checked)">
          <span class="dark-toggle-track"></span>
        </label>
      </div>
      ${_musicEnabled ? (darkGame ? `
      <div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px">
        <div style="font-size:12px;font-weight:700;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px">Soundtrack Layer</div>
        <select onchange="setDarkMusicLevel(this.value)" style="width:100%;padding:9px 12px;font-size:13px;border:1.5px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text-primary);outline:none;appearance:auto">
          <option value="" ${dmManual === null ? 'selected' : ''}>Auto (follows your Street Cred)</option>
          ${[1,2,3,4,5,6,7,8,9,10].filter(i => i <= dmRank).map(i => {
            const names = ['Deep bell + crackle','+ Filthy bass','+ Heavy kick + clap','+ Drill hats','+ Dark drone','+ Tritone stabs','+ Sub + groan','+ Dark strings','+ Whistle lead','+ Full mix + choir'];
            return `<option value="${i}" ${dmManual === String(i) ? 'selected' : ''}>Layer ${i} — ${names[i-1]}</option>`;
          }).join('')}
        </select>
        <div style="font-size:11px;color:var(--text-muted);margin-top:6px">Rise in Street Cred to unlock all 10 layers</div>
      </div>` : (gameLevel >= 1 ? `
      <div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px">
        <div style="font-size:12px;font-weight:700;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px">Soundtrack Layer</div>
        <select onchange="setMusicManualLevel(this.value)" style="width:100%;padding:9px 12px;font-size:13px;border:1.5px solid var(--border);border-radius:10px;background:var(--bg-card);color:var(--text-primary);outline:none;appearance:auto">
          <option value="" ${manualLvl === null ? 'selected' : ''}>Auto (follows your level)</option>
          ${[0,1,2,3,4,5].filter(i => i <= gameLevel).map(i => {
            const names = ['Xylophone only','+ Drums','+ Bass','+ String Pads','+ Counter-Melody','+ Bell Shimmer'];
            return `<option value="${i}" ${manualLvl === String(i) ? 'selected' : ''}>Layer ${i} — ${names[i]}</option>`;
          }).join('')}
        </select>
        <div style="font-size:11px;color:var(--text-muted);margin-top:6px">Level up to unlock all 6 layers</div>
      </div>` : `<div style="margin-top:10px;font-size:12px;color:var(--text-muted);font-style:italic">🎚️ Level up to unlock more soundtrack layers</div>`)) : ''}
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

    <div class="card" id="settings-danger-zone" style="margin-top:12px">
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
let _stocksOpen = { stock: false, index: false, crypto: false };   // collapsible tiers — all closed on open
function toggleStockTier(key) {
  _stocksOpen[key] = !_stocksOpen[key];
  if (stocksData) _renderStocksInner(stocksData);
}

async function renderStocks() {
  const el = document.getElementById('stocks-list');
  if (!el) return;
  _stocksOpen = { stock: false, index: false, crypto: false };   // every time you open the menu, all tiers collapsed
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
      <div class="stocks-section-title">The Market</div>
      <div class="stocks-section-sub">${res.instruments.length} instruments · prices update each day · dividends paid quarterly</div>
    </div>
  </div>`;
  const tiers = [
    { key: 'stock',  label: 'Stocks',      icon: '📈', sub: 'Moderate risk · most pay dividends' },
    { key: 'index',  label: 'Index Funds', icon: '🧺', sub: 'Low risk · steady · best dividends' },
    { key: 'crypto', label: 'Crypto',      icon: '🪙', sub: 'Extreme risk · no dividends · moon or dust' },
  ];
  tiers.forEach(t => {
    const items = res.instruments.filter(i => (i.tier || 'stock') === t.key);
    if (!items.length) return;
    const open    = !!_stocksOpen[t.key];
    const heldArr = items.filter(i => i.shares > 0);
    const heldVal = heldArr.reduce((a, i) => a + i.shares * i.price, 0);
    const heldNote = heldArr.length ? ` · ${heldArr.length} held (${fmt(heldVal)})` : '';
    html += `
      <div onclick="toggleStockTier('${t.key}')" style="display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer;user-select:none;border:1px solid var(--border);border-radius:10px;margin:10px 0 ${open ? '8px' : '0'}">
        <span style="font-size:18px">${t.icon}</span>
        <div style="flex:1;min-width:0">
          <div style="font-weight:800;font-size:14px">${t.label} <span style="font-size:11px;color:var(--text-muted);font-weight:600">${items.length}</span></div>
          <div style="font-size:10px;color:var(--text-muted)">${t.sub}${heldNote}</div>
        </div>
        <span style="font-size:12px;color:var(--text-muted);display:inline-block;transition:transform .15s;transform:rotate(${open ? 90 : 0}deg)">▶</span>
      </div>`;
    if (open) html += items.map(i => stockCardHtml(i, res.cash)).join('');
  });
  el.innerHTML = html;
}

function stockCardHtml(inst, cash) {
  const { ticker, name, icon, desc, price, history, shares, avg_cost, gain, dividend } = inst;
  const divStr = dividend > 0 ? `<span style="font-size:10px;font-weight:700;color:var(--positive);border:1px solid var(--positive);border-radius:6px;padding:1px 5px;margin-left:4px">💵 ${(dividend*100).toFixed(1)}% div</span>` : '';
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
        <div class="stock-name">${name} <span class="stock-ticker">${ticker}</span>${divStr}</div>
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
  sfx.stockBuy();
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
  sfx.stockSell();
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
// Cancel any animation loops / timers a mini-game left running. Without this, a
// mini-game abandoned by closing the modal mid-play (or by launching another) leaks
// a 60fps RAF loop + intervals; these stack across a session and progressively chug
// the whole app — taps stop registering until a full restart clears the heap.
// document/window listeners owned by the active mini-game. Tracked at module scope
// (not on _mg, which gets reassigned per game) so teardown can always remove them.
let _mgListeners = [];
function _mgListen(target, type, fn, opts) {
  target.addEventListener(type, fn, opts);
  _mgListeners.push({ target, type, fn, opts });
}

function _teardownMinigame() {
  // remove any document/window listeners the mini-game attached
  _mgListeners.forEach(l => { try { l.target.removeEventListener(l.type, l.fn, l.opts); } catch (e) {} });
  _mgListeners = [];
  if (typeof _mg !== 'object' || !_mg) return;
  ['rafId', 'animId', 'markerRaf', 'wobbleRaf'].forEach(k => {
    if (_mg[k]) { cancelAnimationFrame(_mg[k]); _mg[k] = null; }
  });
  // The tiling game nests its falling-tile RAF off _mg.fallingTile, not a top-level
  // key — cancel it here too, or it keeps animating a detached tile after close.
  if (_mg.fallingTile) {
    if (_mg.fallingTile.raf) cancelAnimationFrame(_mg.fallingTile.raf);
    _mg.fallingTile.done = true;
    _mg.fallingTile = null;
  }
  ['timerId', 'autoCloseId', 'spawnId'].forEach(k => {
    if (_mg[k]) { clearTimeout(_mg[k]); clearInterval(_mg[k]); _mg[k] = null; }
  });
  _mg.running = false;
}

function openModal(html) {
  _teardownMinigame();   // kill any prior mini-game before showing a new modal
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
  _teardownMinigame();   // stop any mini-game loops/timers when the modal closes
  document.getElementById('modal-overlay').classList.remove('open');
  _pendingConfirm = null;
  _propDetailId   = null;
  _inPropSubModal = false;
  if (_pendingLevelUp && !_modalLocked) {
    const lvl   = _pendingLevelUp;
    _pendingLevelUp = null;
    setTimeout(() => showLevelUpModal(lvl), 80);
  } else if (typeof DARK !== 'undefined' && DARK.maybeOffer) {
    setTimeout(() => DARK.maybeOffer(), 90);   // once the last modal's closed, the Level-11 deal can knock
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
      <button class="btn btn-ghost btn-sm" onclick="sfx.cancel(); closeModal()">Cancel</button>
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
  if (type === 'error') sfx.error();
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

// Reliability rescaled to the band tenants actually occupy (~0.78–0.99) so the
// stars span 1–5 instead of clumping at 4–5. Pairs the stars with the real
// on-time % and a plain-language word.
function reliabilityInfo(pc) {
  const stars = Math.max(1, Math.min(5, Math.round((pc - 0.72) / 0.055)));
  let word, color;
  if (pc >= 0.96)      { word = 'Rock-solid'; color = 'var(--positive)'; }
  else if (pc >= 0.90) { word = 'Dependable'; color = 'var(--positive)'; }
  else if (pc >= 0.84) { word = 'Decent';     color = 'var(--warning)';  }
  else if (pc >= 0.78) { word = 'Spotty';     color = 'var(--warning)';  }
  else                 { word = 'Risky';      color = 'var(--negative)'; }
  return { stars, pct: Math.round(pc * 100), word, color,
           html: '★'.repeat(stars) + '☆'.repeat(5 - stars) };
}

function damageColor(label) {
  return label === 'Low' ? 'var(--positive)' : label === 'Medium' ? 'var(--warning)' : 'var(--negative)';
}

// One-line read on the tenant, combining reliability + damage risk.
function tenantVibe(t) {
  const payStrong = t.pay_chance >= 0.90, payWeak = t.pay_chance < 0.84;
  const dmgHigh = t.damage_label === 'High', dmgLow = t.damage_label === 'Low';
  if (payStrong && dmgLow)  return 'Model tenant — pays well, easy on the place.';
  if (payStrong && dmgHigh) return 'Pays reliably, but rough on the property.';
  if (payWeak && dmgLow)    return 'Gentle on the home, but payments can slip.';
  if (payWeak && dmgHigh)   return 'High-risk — shaky payments and hard on the home.';
  return 'A solid, dependable choice.';
}

// Expected income across a full lease at fair rent (rent × avg weeks × on-time %).
// A baseline for comparing applicants; actual depends on the rent tier chosen next.
function projectedLeaseIncome(t, fairRent) {
  const avgWeeks = ((t.stay_min + t.stay_max) / 2) / 7;
  return Math.round((fairRent * avgWeeks * t.pay_chance) / 100) * 100;
}

function regularTenantCard(t, id, fairRent) {
  const rel  = reliabilityInfo(t.pay_chance);
  const vibe = tenantVibe(t);
  const proj = projectedLeaseIncome(t, fairRent);
  const avgStay = Math.round((t.stay_min + t.stay_max) / 2);
  const traitChip = t.trait_info
    ? ` <span style="font-size:10px;font-weight:700;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:1px 7px;margin-left:4px;white-space:nowrap">${t.trait_info.icon} ${t.trait_info.name}</span>`
    : '';
  return `
      <div class="tenant-card" onclick="showRentSettingModal(${id}, ${t.idx})">
        <div class="tenant-header">
          <span class="tenant-icon">${pxIcon(t.icon || '👤', 28)}</span>
          <div style="flex:1">
            <div class="tenant-name">${t.name}${traitChip}</div>
            ${t.desc ? `<div style="font-size:11px;color:var(--text-muted);margin-top:3px;line-height:1.4">${t.desc}</div>` : ''}
            ${t.trait_info ? `<div style="font-size:11px;color:var(--accent);margin-top:3px;line-height:1.4">${t.trait_info.icon} ${t.trait_info.desc}</div>` : ''}
          </div>
        </div>
        <div class="tenant-meta">
          <div class="tenant-meta-item">
            <span class="tm-label">Reliability</span>
            <span class="tm-value"><span style="color:${rel.color}">${rel.html}</span> <span style="font-size:11px;color:var(--text-muted)">${rel.word} · ${rel.pct}%</span></span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Damage Risk</span>
            <span class="tm-value" style="color:${damageColor(t.damage_label)}">${t.damage_label}</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Typical Stay</span>
            <span class="tm-value">~${avgStay} days</span>
          </div>
          <div class="tenant-meta-item">
            <span class="tm-label">Est. Lease Income</span>
            <span class="tm-value" style="color:var(--positive)">${fmt(proj)}</span>
          </div>
          <div class="tenant-meta-item" style="grid-column:1/-1">
            <span class="tm-label">Summary</span>
            <span class="tm-value" style="font-weight:600;font-size:12px;line-height:1.4">${vibe}</span>
          </div>
        </div>
      </div>`;
}

// ── Opening splash ────────────────────────────────────────────────────────────
let _splashDone     = false;   // true once the splash is fully removed
let _splashDismissing = false;
let _afterSplash    = null;    // callback to run once the splash is gone (e.g. the intro)

function dismissSplash() {
  if (_splashDismissing) return;
  _splashDismissing = true;
  const s = document.getElementById('splash-screen');
  if (s) {
    s.classList.add('hide');
    setTimeout(_finishSplash, 600);
  } else {
    _finishSplash();
  }
}
function _finishSplash() {
  const s = document.getElementById('splash-screen');
  if (s && s.parentNode) s.remove();
  _splashDone = true;
  if (_afterSplash) { const cb = _afterSplash; _afterSplash = null; cb(); }
}
// Run cb once the splash has fully cleared (immediately if it's already gone).
function whenSplashDone(cb) {
  if (_splashDone) cb();
  else _afterSplash = cb;
}
setTimeout(dismissSplash, 5300);   // auto-dismiss after the studio bumper + title play

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
