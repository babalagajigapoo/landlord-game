// ════════════════════════════════════════════════════════════════════════════
//  DARK MODE — "Off the Books"  (aka darkside / evil mode)
//  A self-contained crime-empire mode. It branches at the TOP (state.mode==='dark')
//  and owns its ENTIRE UI in this file, so the legit game's code is never touched
//  and can't break from anything in here.
//  Carry-over from legit: clean cash, owned businesses, owned homes + tenants.
// ════════════════════════════════════════════════════════════════════════════

const DARK = {
  _tab: 'home',

  // Bottom-nav tabs. Add / remove here — the nav bar and the page router are
  // both driven off this list, so changing the line-up is a one-line edit.
  TABS: [
    { key: 'home',       icon: '🏠',  label: 'Home' },
    { key: 'properties', icon: '🏚️',  label: 'Property' },
    { key: 'crew',       icon: '👥',  label: 'Crew' },
    { key: 'fence',      icon: '🧰',  label: 'Fence' },
    { key: 'dealers',    icon: '🧢',  label: 'Deal' },
    { key: 'cash',       icon: '💵',  label: 'Cash' },
    { key: 'businesses', icon: '🎰',  label: 'Biz' },
  ],

  // Trait display data (mirrors DARK_TRAITS in app.py). "knows" = the drug this person can cook.
  TRAITS: {
    green_thumb: { name: 'Green Thumb',   icon: '🌿', knows: 'Weed',   cooks: 'reggie', cost: 2500  },
    pill_cook:   { name: 'Pill Cook',     icon: '💊', knows: 'Pills',  cooks: 'beans',  cost: 5000  },
    cutter:      { name: 'Cutter',        icon: '❄️', knows: 'Powder', cooks: 'soft',   cost: 8000  },
    rock_cook:   { name: 'Rock Cook',     icon: '🪨', knows: 'Rock',   cooks: 'hard',   cost: 11000 },
    chemist:     { name: 'Chemist',       icon: '🧪', knows: 'Glass',  cooks: 'glass',  cost: 15000 },
    tar_boiler:  { name: 'Tar Boiler',    icon: '🛢️', knows: 'Tar',    cooks: 'tar',    cost: 20000 },
    workhorse:   { name: 'Workhorse',     icon: '🐂', cost: 3500, desc: 'Faster production' },
    ghost:       { name: 'Ghost',         icon: '👻', cost: 4000, desc: 'Less heat' },
    loyal:       { name: 'Loyal',         icon: '🤝', cost: 3500, desc: "Won't snitch" },
    hothead:     { name: 'Hothead',       icon: '🔥', cost: 1800, desc: 'Wins turf, more drama' },
    connected:   { name: 'Connected',     icon: '📇', cost: 4500, desc: 'Cheap-gear hookups' },
    sloppy:      { name: 'Sloppy',        icon: '🧤', cost: 900,  desc: 'Cheap, more accidents' },
    lookout:     { name: 'Lookout',       icon: '👀', cost: 3000, desc: 'Early raid warning' },
    lucky:       { name: 'Lucky',         icon: '🍀', cost: 4500, desc: 'Better event luck' },
    junkie:      { name: 'Junkie',        icon: '💉', cost: 700,  desc: 'Skims product, dirt cheap' },
    smooth:      { name: 'Smooth Talker', icon: '🎩', cost: 3500, desc: 'Softens busts' },
  },

  // Static design data (mirrors the backend defs in app.py). Drugs unlock by Street Cred.
  DRUGS: [
    { key: 'reggie', name: 'Weed',   icon: '🌿', cred: 1  },
    { key: 'beans',  name: 'Pills',  icon: '💊', cred: 3  },
    { key: 'soft',   name: 'Powder', icon: '❄️', cred: 5  },
    { key: 'hard',   name: 'Rock',   icon: '🪨', cred: 7  },
    { key: 'glass',  name: 'Glass',  icon: '🧊', cred: 9  },
    { key: 'tar',    name: 'Tar',    icon: '🛢️', cred: 10 },
  ],
  DRUG_VALUE: { reggie: 40, beans: 90, soft: 160, hard: 280, glass: 480, tar: 800 },  // street value/unit
  COOK_COST:  { reggie: 150, beans: 325, soft: 675, hard: 1250, glass: 2300, tar: 4300 },  // hand-cook ingredient cost (cash)
  SUPPLIES: {
    reggie: { name: 'Weed Supplies',   icon: '🌱', cost: 1000  },
    beans:  { name: 'Pill Supplies',   icon: '⚗️', cost: 2500  },
    soft:   { name: 'Powder Supplies', icon: '🔪', cost: 5000  },
    hard:   { name: 'Rock Supplies',   icon: '🍳', cost: 9000  },
    glass:  { name: 'Glass Supplies',  icon: '🧪', cost: 14000 },
    tar:    { name: 'Tar Supplies',    icon: '🛢️', cost: 22000 },
  },
  BATCH_DAYS: { 1: 5, 2: 3, 3: 2 },
  // Kingpin rank ladder (mirrors DARK_RANKS in app.py).
  RANKS: [
    { level: 1,  name: 'Corner Boy',  xp: 0,    perk: 'Cooking Weed and working corners.' },
    { level: 2,  name: 'Slinger',     xp: 150,  perk: 'Dealers move more product per day.' },
    { level: 3,  name: 'Pusher',      xp: 400,  perk: '💊 Pills unlocked.' },
    { level: 4,  name: 'Lieutenant',  xp: 800,  perk: 'Your name pulls weight — supplies cost less.' },
    { level: 5,  name: 'Supplier',    xp: 1400, perk: '❄️ Powder unlocked.' },
    { level: 6,  name: 'Distributor', xp: 2200, perk: 'A cop on the payroll bleeds your heat down.' },
    { level: 7,  name: 'Boss',        xp: 3200, perk: '🪨 Rock unlocked.' },
    { level: 8,  name: 'Underboss',   xp: 4500, perk: 'Dealers move even more; supplies cheaper still.' },
    { level: 9,  name: 'Shot Caller', xp: 6200, perk: '🧊 Glass unlocked.' },
    { level: 10, name: 'Kingpin',     xp: 8500, perk: '🛢️ Tar unlocked. You run this town.' },
  ],
  rank(lvl) { return this.RANKS.find(r => r.level === lvl) || this.RANKS[0]; },
  supplyPrice(drug) {
    const base = (this.SUPPLIES[drug] || {}).cost || 0;
    const cred = (state.dark && state.dark.cred) || 1;
    const disc = (cred >= 4 ? 0.10 : 0) + (cred >= 8 ? 0.10 : 0);
    return Math.round(base * (1 - disc));
  },
  dealerCap() {
    const cred = (state.dark && state.dark.cred) || 1;
    return 8 + (cred >= 2 ? 2 : 0) + (cred >= 8 ? 3 : 0);
  },
  LAUNDER: {
    laundromat: { name: 'Laundromat',          icon: '🧼', cap: 1500, hire: 5000,  wage: 250, price: 250000 },
    car_wash:   { name: 'Car Wash',            icon: '🚗', cap: 3000, hire: 8000,  wage: 450, price: 600000 },
    pizzeria:   { name: "Famiglia's Pizzeria", icon: '🍕', cap: 6000, hire: 12000, wage: 800, price: 200000 },
  },

  // ── Enter / exit ──────────────────────────────────────────────────────────
  // The descent: a deal-with-the-devil sequence — the Fixer's pitch, then a contract
  // you sign as "SlumLord". Only on signing do we actually flip to dark mode.
  DESCENT_BEATS: [
    { icon: '🕴️', btn: 'Who are you?', text: `"Rough year, wasn't it? You did everything right — the rents, the renovations, the little smiles at the bank. And here you still are. Scraping.<br><br>Don't get up. I'm not here to take anything. I'm here to offer you a <b>door</b>."` },
    { icon: '🚪', btn: "What's the catch?", text: `"There's a version of this city that doesn't keep receipts. No taxes. No inspectors. No levels to grind, no landlord's smile to fake. Down there you don't ask permission — you <b>take</b>.<br><br>I can put you down there. Tonight."` },
    { icon: '💼', btn: 'And if I say yes?', text: `"It isn't free. Nothing good is. The door opens one way — you can't be clutching the old world while you step through it.<br><br>Everything you've built up here — the cash, the keys, the deeds — stays with me. You walk in with <b>ten grand</b> and a clean slate. What you make of it is yours. What you <i>owe</i>… we'll get to that."` },
    { icon: '📜', btn: 'Read the contract', text: `He slides a single page across the desk. The ink still looks faintly wet.<br><br>"Most people can't let go. They cling to the scraps and die respectable. You're not most people. Read it — then sign."` },
  ],
  beginDescent() {
    this._ensureStyle();   // still in legit mode — make sure the dark CSS exists
    if (typeof sfx === 'object' && sfx.infoOpen) sfx.infoOpen();
    this._descentStep = 0;
    this.renderDescent();
  },
  renderDescent() {
    const b = this.DESCENT_BEATS[this._descentStep];
    let el = document.getElementById('dk-descent'); if (!el) { el = document.createElement('div'); el.id = 'dk-descent'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay'; el.style.zIndex = '9800';
    el.innerHTML = `<div class="dk-descent-card">
      <div class="dk-evt-icon">${b.icon}</div>
      <div class="dk-descent-fixer">The Fixer</div>
      <div class="dk-descent-text">${b.text}</div>
      <div class="dk-evt-choices"><button class="dk-evt-choice" onclick="DARK.nextDescent()">${b.btn}</button></div>
    </div>`;
    el.style.display = 'flex';
  },
  nextDescent() {
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    this._descentStep++;
    if (this._descentStep >= this.DESCENT_BEATS.length) this.showContract();
    else this.renderDescent();
  },
  showContract() {
    const el = document.getElementById('dk-descent');
    el.innerHTML = `<div class="dk-descent-card">
      <div class="dk-contract-title">⸻ OFF THE BOOKS · TERMS OF DESCENT ⸻</div>
      <div class="dk-contract-body">
        <p><i>Entered this night between the undersigned ("the Signatory") and the Party of the Lower Part ("the Fixer").</i></p>
        <p><b>I.</b> The Signatory surrenders, fully and forever, all lawful holdings — every dollar, every deed, every honest dime — the instant ink meets paper.</p>
        <p><b>II.</b> The Signatory's lawful name is struck from every record. From this night they sign, and answer, only as <b>the SlumLord</b>.</p>
        <p><b>III.</b> No taxes. No filings. No inspectors. No questions. And no road back but one — and you won't care for the toll.</p>
        <p><b>IV.</b> The Fixer advances <b>$10,000</b> in unmarked bills, a courtesy, to be spent however the dark allows.</p>
        <p><b>V.</b> The Fixer collects. Not tonight, not tomorrow — but always, and in full. The House does not forget.</p>
        <p><b>VI.</b> Signed in good faith and bad, of sound mind and worse intentions.</p>
      </div>
      <div class="dk-sig-line">
        <span class="dk-sig-x">✗</span>
        <div id="dk-sig-slot" class="dk-sig-slot"></div>
        <div id="dk-seal" class="dk-seal">OFF<br>THE<br>BOOKS</div>
      </div>
      <div class="dk-evt-choices">
        <button class="dk-evt-choice" id="dk-sign-btn" onclick="DARK.signContract()">🖊️ Sign it</button>
        <button class="dk-evt-choice" id="dk-decline-btn" style="background:#3a2024" onclick="DARK.declineContract()">Set the pen down — not tonight</button>
      </div>
    </div>`;
  },
  declineContract() {
    if (this._signing) return;   // can't back out once the ink's flowing
    const el = document.getElementById('dk-descent'); if (el) el.remove();
    if (typeof toast === 'function') toast('You slide the page back across the desk. "Another night, then." 🚪', 'info');
  },
  signContract() {
    if (this._signing) return; this._signing = true;
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    const btn = document.getElementById('dk-sign-btn'); if (btn) { btn.disabled = true; btn.textContent = '…'; }
    const dec = document.getElementById('dk-decline-btn'); if (dec) dec.style.display = 'none';
    const slot = document.getElementById('dk-sig-slot'); if (slot) slot.innerHTML = `<div class="dk-sig writing">SlumLord</div>`;
    setTimeout(() => { const seal = document.getElementById('dk-seal'); if (seal) seal.classList.add('show'); }, 1500);
    setTimeout(async () => {
      const el = document.getElementById('dk-descent'); if (el) el.remove();
      this._signing = false;
      await this.enter();
    }, 2700);
  },
  async enter() {
    const r = await api('/dark/enter', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    this._tab = 'home';
    await refreshState();
    toast("The ink dries. There's no map back here. 😈", 'warning');
  },
  _ensureStyle() {
    if (!document.getElementById('dk-style')) {
      const st = document.createElement('style'); st.id = 'dk-style'; st.textContent = DARK.css(); document.head.appendChild(st);
    }
  },
  // ── The Level-11 dilemma — the yes/no offer that opens the door to the dark side ──
  maybeOffer() {
    if (!state || state.mode === 'dark') return;
    if ((state.level ?? 0) < 11) return;                 // the crossroads is Level 11
    if (this._dilemmaOpen || this._offeredThisSession) return;
    const mo = document.getElementById('modal-overlay');
    if (mo && mo.classList.contains('open')) {           // a modal's up (e.g. the level-up popup) — wait it out, then knock
      if (this._offerWaiting) return;
      this._offerWaiting = true;
      const tick = () => {
        const m = document.getElementById('modal-overlay');
        if (m && m.classList.contains('open')) { setTimeout(tick, 500); return; }
        this._offerWaiting = false; this.maybeOffer();
      };
      setTimeout(tick, 500);
      return;
    }
    this._offeredThisSession = true;   // offer once per session; declining lets the Fixer knock again next time
    this.showDilemma();
  },
  showDilemma() {
    this._ensureStyle();
    this._dilemmaOpen = true;
    if (typeof sfx === 'object' && sfx.infoOpen) sfx.infoOpen();
    let el = document.getElementById('dk-dilemma'); if (!el) { el = document.createElement('div'); el.id = 'dk-dilemma'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay'; el.style.zIndex = '9750';
    el.innerHTML = `<div class="dk-descent-card">
      <div class="dk-evt-icon">🕴️</div>
      <div class="dk-descent-fixer">A knock at the door</div>
      <div class="dk-descent-text">Eleven levels of grind, and the city finally knows your name. So why does it still feel like <i>scraping</i>?<br><br>There's a man waiting in your office you never let in — sharp suit, no appointment. He says he can put you in a different kind of empire. One that doesn't answer to anyone. One <b>off the books</b>.</div>
      <div class="dk-evt-choices">
        <button class="dk-evt-choice" onclick="DARK.acceptDilemma()">🚬 Hear him out…</button>
        <button class="dk-evt-choice" style="background:#3a2024" onclick="DARK.declineDilemma()">Not tonight</button>
      </div>
    </div>`;
    el.style.display = 'flex';
  },
  acceptDilemma() {
    this._dilemmaOpen = false;
    const el = document.getElementById('dk-dilemma'); if (el) el.remove();
    this.beginDescent();
  },
  declineDilemma() {
    this._dilemmaOpen = false;
    const el = document.getElementById('dk-dilemma'); if (el) el.remove();
    if (typeof toast === 'function') toast("You show him the door. He'll be back. 🚪", 'info');
  },
  // "It was all a dream" — confirm first, since it wipes the whole dark side.
  confirmWake() {
    if (typeof sfx === 'object' && sfx.infoOpen) sfx.infoOpen();
    let el = document.getElementById('dk-wake-modal');
    if (!el) { el = document.createElement('div'); el.id = 'dk-wake-modal'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay';
    el.innerHTML = `<div class="dk-evt-card">
      <div class="dk-evt-icon">💤</div>
      <div class="dk-evt-text" style="text-align:left">
        <b style="font-size:15px">"It was all a dream"</b><br><br>
        This wipes the dark side <b>completely</b> — every lab, crew, dealer, front, plus all your dirty money and product — and drops you back into your <b>legit game</b> right where you left it, as if none of it happened.<br><br>
        Your clean game is untouched. But everything you built off the books is gone, and <b>there's no undo.</b>
      </div>
      <div class="dk-evt-choices">
        <button class="dk-evt-choice" onclick="DARK.wake()">💤 Yes — wake up</button>
        <button class="dk-evt-choice" style="background:#3a2024" onclick="DARK.closeWakeModal()">Stay in the game</button>
      </div>
    </div>`;
    el.style.display = 'flex';
  },
  closeWakeModal() {
    const el = document.getElementById('dk-wake-modal'); if (el) el.remove();
  },
  async wake() {
    const r = await api('/dark/wake', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    this.closeWakeModal();
    await refreshState();
    toast('You jolt awake at your desk. …Just a dream. 😮‍💨', 'success');
  },
  // Settings: hide the dark overlay, show the real settings page, offer a way back.
  _inSettings: false,
  openSettings() {
    if (typeof sfx === 'object' && sfx.infoOpen) sfx.infoOpen();
    this._inSettings = true;
    document.body.classList.add('dk-settings-open');   // hides legit nav/header/reset so there's no door back to the normal game
    const root = document.getElementById('dark-root'); if (root) root.style.display = 'none';
    if (typeof navTo === 'function') navTo('settings');
    let back = document.getElementById('dk-settings-back');
    if (!back) {
      back = document.createElement('button');
      back.id = 'dk-settings-back';
      back.textContent = '← Back to Off the Books';
      back.onclick = () => DARK.closeSettings();
      document.body.appendChild(back);
    }
    back.style.display = 'block';
  },
  closeSettings() {
    this._inSettings = false;
    document.body.classList.remove('dk-settings-open');
    const back = document.getElementById('dk-settings-back'); if (back) back.style.display = 'none';
    if (typeof applyGameMode === 'function') applyGameMode();   // re-show + re-render the dark overlay (fresh, with any code rewards)
  },

  // ── Tab routing ───────────────────────────────────────────────────────────
  go(tab) {
    this._tab = tab;
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    this.rerender();
  },
  rerender() {
    const root = document.getElementById('dark-root');
    if (root) root.innerHTML = this.render();
  },

  // What carried over — read straight from the shared state (no duplication).
  carryover() {
    const b = (state.dark && state.dark.biz) || {};
    let biz = 0;
    ['laundromat', 'car_wash', 'strip_club', 'casino', 'vending'].forEach(k => { if (b[k]) biz++; });
    const homes   = (state.properties || []).length;
    const tenants = (state.properties || []).filter(p => p.tenant).length;
    return { biz, homes, tenants };
  },

  // ── Shell ─────────────────────────────────────────────────────────────────
  render() {
    return `
    <div class="dk-app">
      ${this.header()}
      <div class="dk-content">${this.page()}</div>
      ${this.nav()}
    </div>
    ${this.eventModal()}`;
  },
  _evt: null,   // {kind, ref} of the entity event currently open in the modal
  // Find an entity's pending event (choices are [label, result, effects] arrays).
  entityEvent(kind, ref) {
    if (kind === 'lab')    { const p = (state.properties || []).find(x => x.id === ref); return p && p.lab && p.lab.event; }
    if (kind === 'dealer') { const dl = ((state.dark || {}).dealers || []).find(x => x.id === ref); return dl && dl.event; }
    if (kind === 'front')  { return (((state.dark || {}).launder || {})[ref] || {}).event; }
    return null;
  },
  openEvt(kind, ref) {
    this._evt = { kind, ref };
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    this.rerender();
  },
  eventModal() {
    // Entity event (a specific lab / dealer / front) takes priority — array-choice format.
    if (this._evt) {
      const ev = this.entityEvent(this._evt.kind, this._evt.ref);
      if (ev) {
        const choices = (ev.choices || []).map((c, i) => `<button class="dk-evt-choice" onclick="DARK.resolveEntityEvent(${i})">${c[0]}</button>`).join('');
        return `<div class="dk-evt-overlay"><div class="dk-evt-card">
          <div class="dk-evt-icon">${ev.icon || '❗'}</div>
          <div class="dk-evt-text">${ev.text}</div>
          <div class="dk-evt-choices">${choices}</div>
        </div></div>`;
      }
      this._evt = null;
    }
    const ev = state.dark && state.dark.pending_event;
    if (!ev) return '';
    const choices = (ev.choices || []).map((c, i) => `<button class="dk-evt-choice" onclick="DARK.resolveEvent(${i})">${c.label}</button>`).join('');
    return `<div class="dk-evt-overlay"><div class="dk-evt-card">
      <div class="dk-evt-icon">${ev.icon || '❗'}</div>
      <div class="dk-evt-text">${ev.text}</div>
      <div class="dk-evt-choices">${choices}</div>
    </div></div>`;
  },
  async resolveEvent(idx) {
    const r = await api('/dark/resolve_event', 'POST', { choice: idx });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
    if (r.result) toast(r.result, 'info');
  },
  async resolveEntityEvent(idx) {
    if (!this._evt) return;
    const { kind, ref } = this._evt;
    const r = await api('/dark/resolve_entity_event', 'POST', { kind, ref, choice: idx });
    if (r.error) { toast(r.error, 'error'); return; }
    this._evt = null;
    await refreshState(); this.rerender();
    if (r.result) toast(r.result, 'info');
  },
  // The "⚠ tap to handle" banner shown on a paused entity's card.
  evtHandle(kind, ref, ev, sub) {
    const t = ev.text.length > 64 ? ev.text.slice(0, 61) + '…' : ev.text;
    const r = typeof ref === 'string' ? `'${ref}'` : ref;
    return `<button class="dk-evt-handle" onclick="DARK.openEvt('${kind}',${r})">
      <span class="dk-evt-handle-t">${ev.icon || '⚠'} ${t}</span>
      <span class="dk-evt-handle-s">Tap to handle · ${sub}</span>
    </button>`;
  },

  header() {
    const d = state.dark || {};
    const cell = (lbl, val, col) =>
      `<div class="dk-res-cell"><div class="dk-res-lbl">${lbl}</div><div class="dk-res-val" style="color:${col}">${val}</div></div>`;
    const stash = d.stash || {};
    const keys = Object.keys(stash).filter(k => (stash[k] || 0) > 0);
    const total = keys.reduce((a, k) => a + (stash[k] || 0), 0);
    const open = this._stashOpen;
    const items = keys.length
      ? keys.map(k => {
          const drug = this.DRUGS.find(x => x.key === k) || { name: k, icon: '📦' };
          return `<div class="dk-stashrow"><span>${drug.icon} ${drug.name}</span><span>${stash[k]} units</span></div>`;
        }).join('')
      : `<div class="dk-stashrow" style="color:#caa">No product on hand — collect from a lab.</div>`;
    return `
    <div class="dk-header">
      <div class="dk-brandrow">
        <div class="dk-brand">🩸 Off the Books <span class="dk-rank">Street Cred ${d.cred || 1}</span></div>
        <div class="dk-hdr-btns">
          <button class="dk-hdr-btn" onclick="DARK.confirmWake()" title="It was all a dream">💤</button>
          <button class="dk-hdr-btn" onclick="DARK.openSettings()" title="Settings">⚙️</button>
        </div>
      </div>
      <div class="dk-res">
        ${cell('💵 Clean',  fmt(state.cash || 0),    '#4CAF50')}
        ${cell('🧼 Dirty',  fmt(d.dirty_money || 0), '#E0533D')}
        ${cell('🔥 Heat',   (d.heat || 0) + '%',     '#FF8A3D')}
      </div>
      <div class="dk-stashbar" onclick="DARK.toggleStash()">
        <span>📦 Inventory${total ? ` · ${total} units` : ''}</span>
        <span>${open ? '▾' : '▸'}</span>
      </div>
      ${open ? `<div class="dk-stashlist">${items}</div>` : ''}
    </div>`;
  },

  nav() {
    return `<div class="dk-nav">${this.TABS.map(t => `
      <button class="dk-nav-btn ${this._tab === t.key ? 'active' : ''}" onclick="DARK.go('${t.key}')">
        <span class="dk-nav-ic">${t.icon}</span><span>${t.label}</span>
      </button>`).join('')}</div>`;
  },

  page() {
    switch (this._tab) {
      case 'properties': return this.pageProperties();
      case 'crew':       return this.pageCrew();
      case 'fence':      return this.pageFence();
      case 'dealers':    return this.pageDealers();
      case 'cash':       return this.pageCash();
      case 'businesses': return this.pageBusinesses();
      default:           return this.pageHome();
    }
  },

  async buySupply(drug) {
    const r = await api('/dark/buy_supplies', 'POST', { drug });
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState();
    this.rerender();
    toast('Supplies bought. 🧰', 'success');
  },
  async hireRecruit(id) {
    const r = await api('/dark/hire_recruit', 'POST', { recruit_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('Brought them on. 🤝', 'success');
  },
  async putWordOut() {
    const r = await api('/dark/put_word_out', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast("Word's out. Fresh faces tomorrow. 📞", 'success');
  },
  async dismissRoster(id) {
    const r = await api('/dark/dismiss_roster', 'POST', { member_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async advance() {
    const r = await api('/dark/advance', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState();   // re-renders the dark UI (and surfaces any choice event under the modal)
    if (r.hunt_intro) this.showHuntIntro(r.events || []);
    else this.dayModal(r.events || []);
  },
  // One-time menu when the Hunt switches on at Street Cred 2.
  showHuntIntro(events) {
    this._pendingDay = events;
    let el = document.getElementById('dk-hunt-intro'); if (!el) { el = document.createElement('div'); el.id = 'dk-hunt-intro'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay'; el.style.zIndex = '9700';
    el.innerHTML = `<div class="dk-evt-card">
      <div class="dk-evt-icon">🕵️</div>
      <div class="dk-evt-text" style="text-align:left">
        <b style="font-size:15px">You've made a name for yourself.</b><br><br>
        Word just reached you: a detective — <b>${this.DETECTIVE}</b> — has opened a case on your operation. From now on, the more (and hotter) you run, the harder he digs.<br><br>
        Keep an eye on <b>The Hunt</b> on your home screen — pause what he's watching, lie low, or pay him off, or you'll get raided.
      </div>
      <div class="dk-evt-choices"><button class="dk-evt-choice" onclick="DARK.closeHuntIntro()">Let him try.</button></div>
    </div>`;
    el.style.display = 'flex';
  },
  closeHuntIntro() {
    const el = document.getElementById('dk-hunt-intro'); if (el) el.remove();
    this.dayModal(this._pendingDay || []); this._pendingDay = null;
  },
  // Daily recap menu, shown every time you advance a day.
  dayModal(events) {
    const d = state.dark || {};
    const col = t => t === 'negative' ? '#E0533D' : t === 'warning' ? '#FF8A3D' : '#9fd8a0';
    const rows = (events && events.length)
      ? events.map(e => `<div class="dk-day-row" style="border-left-color:${col(e.type)}">${e.text}</div>`).join('')
      : `<div class="dk-day-row" style="border-left-color:#3a2024;color:#9a8a8a">A quiet day on the streets. Nothing to report.</div>`;
    let el = document.getElementById('dk-day-modal'); if (!el) { el = document.createElement('div'); el.id = 'dk-day-modal'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay'; el.style.zIndex = '9600';
    el.innerHTML = `<div class="dk-evt-card" style="max-width:400px">
      <div class="dk-day-title">🌙 Day ${state.day} — off the books</div>
      <div class="dk-day-money">
        <div><div class="dk-day-mlbl">💵 Clean</div><div class="dk-day-mval" style="color:#4CAF50">${fmt(state.cash || 0)}</div></div>
        <div><div class="dk-day-mlbl">🧼 Dirty</div><div class="dk-day-mval" style="color:#E0533D">${fmt(d.dirty_money || 0)}</div></div>
      </div>
      <div class="dk-day-list">${rows}</div>
      <button class="dk-evt-choice" onclick="DARK.closeDayModal()">Continue</button>
    </div>`;
    el.style.display = 'flex';
  },
  closeDayModal() { const el = document.getElementById('dk-day-modal'); if (el) el.remove(); this.checkFixer(); },

  // ── The Fixer's debt ────────────────────────────────────────────────────────
  debtPanel() {
    const d = state.dark || {};
    if (!d.debt_active) return '';
    const cal = (typeof getSeasonInfo === 'function') ? getSeasonInfo(state.day || 1) : { name: '', seasonDay: 1, year: 1 };
    const bal = d.debt_balance || 0, bill = d.debt_bill || 0, paid = d.debt_paid || 0, owed = Math.max(0, bill - paid);
    const billActive = (d.debt_bill_year === cal.year) && bill > 0;
    let body;
    if (billActive && owed > 0) {
      const daysLeft = Math.max(0, 28 - cal.seasonDay), tooPoor = (state.cash || 0) <= 0;
      body = `<div class="dk-pline" style="color:#E0533D">Due by Winter 28: <b>${fmt(owed)}</b></div>
        <div class="dk-muted2" style="font-size:11px;margin-top:2px">${daysLeft} ${daysLeft === 1 ? 'day' : 'days'} left — come up short and the goons take it all.</div>
        <button class="dk-mini ${tooPoor ? 'dk-buy-off' : ''}" style="width:100%;margin-top:8px;background:#C0392B;border-color:#C0392B;color:#fff" ${tooPoor ? 'disabled' : 'onclick="DARK.payFixer()"'}>💵 Pay the Fixer ${fmt(Math.min(state.cash || 0, owed))}</button>`;
    } else if (billActive) {
      body = `<div class="dk-muted" style="color:#4CAF50;margin-top:4px">✅ Square with the Fixer this year.</div>`;
    } else {
      body = `<div class="dk-muted" style="margin-top:4px">He's tallying your take. His cut comes due on <b>Winter 1</b> — you won't know the number until then.</div>`;
    }
    const strike = (d.cred || 1) >= 10
      ? `<button class="dk-mini" style="width:100%;margin-top:9px;opacity:.8" disabled>⚔️ Strike Back at the Fixer <span class="dk-muted2">· coming soon</span></button>` : '';
    return `
      ${this.sectionTitle("The Fixer's Debt")}
      <div class="dk-card dk-pcard" style="border-color:#7A1A1E">
        <div class="dk-phead"><div class="dk-row-ic">🕴️</div>
          <div class="dk-row-main"><div class="dk-row-title">The House always collects</div><div class="dk-muted">You owe <b style="color:#E0533D">${fmt(bal)}</b></div></div></div>
        ${body}${strike}
      </div>`;
  },
  async payFixer() {
    const r = await api('/dark/pay_fixer', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.cash) sfx.cash();
    await refreshState(); this.rerender();
    toast(r.settled ? `Paid the Fixer ${fmt(r.paid)} — square for the year. 🤝` : `Paid ${fmt(r.paid)} — still owe ${fmt((r.debt_bill || 0) - (r.debt_paid || 0))}.`, r.settled ? 'success' : 'info');
  },
  checkFixer() {
    const d = state.dark; if (!d || !d.fixer_event || this._fixerOpen) return;
    if (document.getElementById('dk-day-modal') || document.getElementById('dk-hunt-intro')) return;   // let the recap finish first
    this.showFixerEvent(d.fixer_event);
  },
  showFixerEvent(ev) {
    this._fixerOpen = true;
    let icon = '🕴️', body = '';
    if (ev.kind === 'intro') {
      icon = '🕴️';
      body = `<b style="font-size:15px">Well, well. Look who made <span style="color:#C0392B">Pusher</span>.</b><br><br>"Knew you had it in you. Which means it's time we talked about what you owe me." He taps the contract — Article V, circled in red.<br><br>You owe the House <b>${fmt(1000000000)}</b>. You'll never clear it — that's rather the point. Every year, on <b>Winter 1</b>, I'll name my cut: <b>15% of everything you made</b>. Have it by <b>Winter 28</b>… or my boys come collect.`;
    } else if (ev.kind === 'warn') {
      body = `<b style="font-size:15px">"Time to settle up."</b><br><br>The Fixer wants <b style="color:#E0533D">${fmt(ev.bill || 0)}</b> by <b>Winter 28</b>. Pay him from the Cash tab — and don't come up short.`;
    } else if (ev.kind === 'goons') {
      icon = '💢';
      body = `<b style="font-size:15px">You came up short.</b><br><br>The Fixer doesn't do patience. His goons caught you in the open — took <b>${fmt(ev.dirty || 0)}</b> in dirty money and <b>${ev.units || 0} units</b> of product, and left you something to remember.<br><br>Your debt's grown to <b style="color:#E0533D">${fmt(ev.balance || 0)}</b>.`;
    }
    let el = document.getElementById('dk-fixer-modal'); if (!el) { el = document.createElement('div'); el.id = 'dk-fixer-modal'; document.body.appendChild(el); }
    el.className = 'dk-evt-overlay'; el.style.zIndex = '9750';
    el.innerHTML = `<div class="dk-evt-card"><div class="dk-evt-icon">${icon}</div>
      <div class="dk-evt-text" style="text-align:left">${body}</div>
      <div class="dk-evt-choices"><button class="dk-evt-choice" onclick="DARK.ackFixer()">${ev.kind === 'goons' ? 'Damn it.' : ev.kind === 'intro' ? 'I hear you.' : 'Got it.'}</button></div></div>`;
    el.style.display = 'flex';
  },
  ackFixer() {
    this._fixerOpen = false;
    const el = document.getElementById('dk-fixer-modal'); if (el) el.remove();
    if (state.dark) state.dark.fixer_event = null;
    api('/dark/ack_fixer', 'POST');
  },

  // ── Crew forming + lab management ──────────────────────────────────────────
  _sel: [],        // member ids selected while forming a crew
  _labFor: null,   // prop id whose lab-setup picker is open
  toggleSel(id) {
    const i = this._sel.indexOf(id);
    if (i >= 0) this._sel.splice(i, 1);
    else if (this._sel.length < 5) this._sel.push(id);
    else toast('A crew tops out at 5.', 'warning');
    this.rerender();
  },
  async formCrew() {
    if (this._sel.length < 3) { toast('A crew needs at least 3 people.', 'error'); return; }
    const pool = ['Vipers', 'Ghosts', 'Saints', 'Hyenas', 'Jokers', 'Wolves', 'Kings'];
    const name = (prompt('Name this crew:', 'The ' + pool[Math.floor(Math.random() * pool.length)]) || '').trim();
    if (name === null) return;
    const r = await api('/dark/form_crew', 'POST', { member_ids: this._sel.slice(), name });
    if (r.error) { toast(r.error, 'error'); return; }
    this._sel = [];
    await refreshState(); this.rerender(); toast('Crew formed. 👥', 'success');
  },
  async disbandCrew(id) {
    const r = await api('/dark/disband_crew', 'POST', { crew_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async assignLab(crewId, propId, drug) {
    const r = await api('/dark/assign_lab', 'POST', { crew_id: crewId, prop_id: propId, drug });
    if (r.error) { toast(r.error, 'error'); return; }
    this._labFor = null;
    await refreshState(); this.rerender(); toast('Lab is up — give the crew supplies to start a batch. 🧪', 'success');
  },
  async setLabSpeed(propId, speed) {
    const r = await api('/dark/set_lab_speed', 'POST', { prop_id: propId, speed });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async startBatch(propId, speed) {
    const r = await api('/dark/start_batch', 'POST', { prop_id: propId, speed });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast(`Batch cooking — ${r.yield} units in ${r.days} days. 🧪`, 'success');
  },
  async payCrew(propId) {
    const r = await api('/dark/pay_crew', 'POST', { prop_id: propId });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast(`Crew paid ${fmt(r.paid)} — they're ready to cook again. 🤝`, 'success');
  },
  async dismantleLab(propId) {
    const r = await api('/dark/dismantle_lab', 'POST', { prop_id: propId });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async toggleRent(propId) {
    const r = await api('/dark/toggle_rent', 'POST', { prop_id: propId });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  openLabPicker(propId) { this._labFor = (this._labFor === propId ? null : propId); this._rentFor = null; this.rerender(); },
  _rentFor: null,
  async openRentPicker(propId) {
    if (this._rentFor === propId) { this._rentFor = null; this.rerender(); return; }
    const r = await api('/dark/rent_options', 'POST', { prop_id: propId });
    if (r.error) { toast(r.error, 'error'); return; }
    this._rentFor = propId; this._labFor = null;
    await refreshState(); this.rerender();
  },
  async rentPick(propId, idx) {
    const r = await api('/dark/rent_pick', 'POST', { prop_id: propId, idx });
    if (r.error) { toast(r.error, 'error'); return; }
    this._rentFor = null;
    await refreshState(); this.rerender(); toast('Tenant moved in. 🛋️', 'success');
  },
  rentPicker(p) {
    const opts = p.rent_options || [];
    if (!opts.length) return `<div class="dk-muted" style="margin-top:9px">Putting the word out for tenants…</div>`;
    const rows = opts.map((o, i) => `
      <div class="dk-row" style="margin-top:7px">
        <div class="dk-row-ic">${o.icon || '🧑'}</div>
        <div class="dk-row-main"><div class="dk-row-title">${o.name} <span class="dk-muted">· ${fmt(o.rent)}/wk</span></div><div class="dk-muted">${o.desc || ''}</div></div>
        <button class="dk-buy" onclick="DARK.rentPick(${p.id},${i})">Pick</button>
      </div>`).join('');
    return `<div style="margin-top:9px;border-top:1px solid #3a2024;padding-top:9px"><div class="dk-muted">Pick a tenant — they pay weekly, no hassle:</div>${rows}</div>`;
  },

  heatTier(h) {
    h = h || 0;
    if (h >= 100) return { label: 'RAIDED', col: '#ff2d2d' };
    if (h >= 75)  return { label: 'Raid imminent', col: '#ff4d2d' };
    if (h >= 50)  return { label: 'Hot', col: '#FF8A3D' };
    if (h >= 25)  return { label: 'Watched', col: '#FFC83D' };
    return { label: 'Quiet', col: '#4CAF50' };
  },
  crewCooks(crewId) {   // Set of drug keys this crew can cook (from members' knowledge traits)
    const keys = new Set();
    (state.dark.roster || []).filter(m => m.crew_id === crewId).forEach(m => {
      const t = this.TRAITS[m.trait]; if (t && t.cooks) keys.add(t.cooks);
    });
    return keys;
  },
  async collectLab(propId) {
    const r = await api('/dark/collect_lab', 'POST', { prop_id: propId });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast(`Collected ${r.collected} units. 📦`, 'success');
  },
  async hireDealer() {
    const r = await api('/dark/hire_dealer', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('Dealer on the corner. 🧢', 'success');
  },
  async fireDealer(id) {
    const r = await api('/dark/fire_dealer', 'POST', { dealer_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async stockDealer(id, drug, amount) {
    const r = await api('/dark/stock_dealer', 'POST', { dealer_id: id, drug, amount });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast(`Stocked ${r.stocked} units.`, 'success');
  },
  async pauseDealer(id) {
    const r = await api('/dark/pause_dealer', 'POST', { dealer_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async collectDealer(id) {
    const r = await api('/dark/collect_dealer', 'POST', { dealer_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast(`Collected ${fmt(r.collected)} dirty. 💵`, 'success');
  },

  // ══════════════════════════════════════════════════════════════════════════
  //  SLING YOURSELF — an active, hand-to-hand selling minigame. Buyers fade in,
  //  you tap one, read their ask, then Take their offer or Haggle (timing bar)
  //  for more. Safe play: no heat. Pays DIRTY money + street-cred XP.
  // ══════════════════════════════════════════════════════════════════════════
  SLING_NAMES: ['Reggie', 'Tank', 'Lola', 'Smiley', 'Cinco', 'Marcus', 'Peaches', 'Slim', 'Vee', 'Dre',
    'Mookie', 'Nessa', 'Tito', 'Boomer', 'Kiki', 'Ghost', 'Rico', 'Dot', 'Pang', 'Trey', 'Mara', 'Cisco'],
  SLING_LINES: [
    'Ay, you holding? Need {q} of the {d}.',
    'Hook me up — {q} {d}, I\'m good for it.',
    'Yo. {q} {d}. Same as always.',
    'Psst. {d}? Gimme {q}, quick.',
    'My guy! {q} {d}, and keep it quiet.',
    'You straight? {q} {d}, cash in hand.',
    'C\'mon man, I been waiting. {q} {d}.',
    'Need {q} {d} for the weekend. You good?',
    'Heard you the one to see. {q} {d}.',
    'Just {q} {d}, then I\'m ghost.',
  ],
  SLING_BULK_LINES: [
    'I\'m buying for the whole block — {q} {d}. Real money.',
    'Out-of-town connect. I\'ll take {q} {d} right now.',
    'Stocking up. {q} {d}, and there\'s more where this came from.',
    'Big order: {q} {d}. Don\'t make me go elsewhere.',
  ],
  HAGGLE_WIN: [   // nailed the green zone — they cave
    'You drive a hard bargain, but I\'m in.',
    'Damn… alright, you got it.',
    'Pff. Fine. It\'s worth it.',
    'You\'re robbin\' me — but deal.',
    'Ha! Respect. Here you go.',
    'Smooth talker. Take my money.',
  ],
  HAGGLE_OK: [    // close to the green — modest bump
    'Eh, close enough. Deal.',
    'Alright, alright. Done.',
    'Fine, I\'ll meet you there.',
    'You got a little extra outta me. Cool.',
  ],
  HAGGLE_LOW: [   // missed — they counter low but still buy
    'That\'s all I got — take it or leave it.',
    'Nah, too steep. This is my price.',
    'You pushed too hard. Here\'s my offer.',
    'Don\'t get greedy. This much, no more.',
  ],
  _sling: null,
  openSling() {
    const stash = (state.dark && state.dark.stash) || {};
    if (!Object.keys(stash).some(k => stash[k] > 0)) {
      toast('Nothing to sling — cook some product first.', 'error'); return;
    }
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    this._sling = { custs: {}, nextId: 1, busy: false, earned: 0, xp: 0, deals: 0, spawnT: null, markerT: null };
    let el = document.getElementById('dk-sling');
    if (!el) { el = document.createElement('div'); el.id = 'dk-sling'; document.body.appendChild(el); }
    el.innerHTML = `
      <div class="dk-sl-top">
        <div class="dk-sl-inv" id="dk-sl-inv"></div>
        <div class="dk-sl-right">
          <div class="dk-sl-tally" id="dk-sl-tally"></div>
          <button class="dk-sl-done" onclick="DARK.closeSling()">Done</button>
        </div>
      </div>
      <div class="dk-sl-area" id="dk-sl-area"></div>
      <div class="dk-sl-hint" id="dk-sl-hint">Tap a buyer before they walk…</div>`;
    this.slingTopRender();
    this._sling.spawnT = setInterval(() => this.slingSpawn(), 1100);
    this.slingSpawn();
  },
  closeSling() {
    const sl = this._sling; if (!sl) return;
    clearInterval(sl.spawnT); clearInterval(sl.markerT);
    Object.values(sl.custs).forEach(c => clearTimeout(c.t));
    const el = document.getElementById('dk-sling'); if (el) el.remove();
    const earned = sl.earned, deals = sl.deals;
    this._sling = null;
    refreshState().then(() => this.rerender());
    if (deals) toast(`Worked the corner — ${deals} ${deals === 1 ? 'deal' : 'deals'}, ${fmt(earned)} dirty. 💪`, 'success');
  },
  slingTopRender() {
    const sl = this._sling; if (!sl) return;
    const stash = (state.dark && state.dark.stash) || {};
    const chips = this.DRUGS.filter(dr => (stash[dr.key] || 0) > 0)
      .map(dr => `<span class="dk-sl-chip">${dr.icon} ${stash[dr.key]}</span>`).join('') || '<span class="dk-muted">empty</span>';
    const inv = document.getElementById('dk-sl-inv'); if (inv) inv.innerHTML = chips;
    const t = document.getElementById('dk-sl-tally');
    if (t) t.innerHTML = `💵 ${fmt(sl.earned)} · ⭐ ${sl.xp} XP`;
  },
  slingSpawn() {
    const sl = this._sling; if (!sl || sl.busy) return;
    const area = document.getElementById('dk-sl-area'); if (!area) return;
    if (Object.keys(sl.custs).length >= 4) return;
    const stash = (state.dark && state.dark.stash) || {};
    const totalStock = Object.values(stash).reduce((a, b) => a + (b || 0), 0);
    const hint = document.getElementById('dk-sl-hint');
    if (totalStock <= 0) { if (hint) hint.textContent = "You're cleaned out — hit Done."; return; }
    if (hint) hint.textContent = 'Tap a buyer — but only deal what you can cover.';
    // Buyers ask for ANY unlocked drug at ANY quantity — independent of your stock.
    // You have to read each ask against what you're holding and decide who you can serve.
    const cred = (state.dark && state.dark.cred) || 1;
    const unlocked = this.DRUGS.filter(dr => cred >= dr.cred);
    const bulk = Math.random() < 0.14;
    const dr = unlocked[Math.floor(Math.random() * unlocked.length)];
    const qty = bulk ? (8 + Math.floor(Math.random() * 8)) : (1 + Math.floor(Math.random() * 6));
    const uv = this.DRUG_VALUE[dr.key] || 40;
    const offer = Math.round(uv * qty * (bulk ? (0.86 + Math.random() * 0.09) : (0.75 + Math.random() * 0.13)));
    const name = this.SLING_NAMES[Math.floor(Math.random() * this.SLING_NAMES.length)];
    const lines = bulk ? this.SLING_BULK_LINES : this.SLING_LINES;
    const line = lines[Math.floor(Math.random() * lines.length)].replace('{q}', qty).replace('{d}', dr.name);
    const id = sl.nextId++;
    const ttl = bulk ? 6200 : 4400;
    const x = 8 + Math.random() * 64, y = 10 + Math.random() * 66;
    const node = document.createElement('button');
    node.className = 'dk-sl-cust' + (bulk ? ' bulk' : '');
    node.id = 'dk-cust-' + id;
    node.style.cssText = `left:${x}%;top:${y}%;animation-duration:${ttl}ms`;
    node.onclick = () => this.slingTap(id);
    node.innerHTML = `<span class="dk-sl-cn">${bulk ? '💼 ' : ''}${name}</span><span class="dk-sl-ca">${dr.icon} ×${qty}</span>`;
    area.appendChild(node);
    const t = setTimeout(() => { const n = document.getElementById('dk-cust-' + id); if (n) n.remove(); delete sl.custs[id]; }, ttl);
    sl.custs[id] = { t, name, line, drug: dr.key, dname: dr.name, dicon: dr.icon, qty, offer, bulk };
  },
  slingTap(id) {
    const sl = this._sling; if (!sl) return;
    const c = sl.custs[id]; if (!c) return;
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    // Pause new spawns and pull THIS buyer off the street; the others keep waiting.
    sl.busy = true;
    clearTimeout(c.t); const cn = document.getElementById('dk-cust-' + id); if (cn) cn.remove();
    delete sl.custs[id];
    sl.deal = c;
    const have = ((state.dark && state.dark.stash) || {})[c.drug] || 0;
    const canFill = have >= c.qty;
    const shortfall = have <= 0
      ? `You're not holding any <b>${c.dname}</b>.`
      : `You've only got <b>${have}</b> ${c.dname} — they want <b>${c.qty}</b>.`;
    const el = document.getElementById('dk-sling');
    const panel = document.createElement('div'); panel.className = 'dk-sl-dealwrap'; panel.id = 'dk-sl-dealwrap';
    panel.innerHTML = `<div class="dk-sl-deal">
      <div class="dk-sl-deal-name">${c.bulk ? '💼 ' : ''}${c.name}</div>
      <div class="dk-sl-deal-line">"${c.line}"</div>
      <div class="dk-sl-deal-ask">Wants <b>${c.dicon} ${c.qty} × ${c.dname}</b> · offering <b style="color:#E0533D">${fmt(c.offer)}</b></div>
      <div class="dk-sl-deal-btns" id="dk-sl-dealbtns">
        ${canFill
          ? `<button class="dk-sl-take" onclick="DARK.slingTake()">💵 Take ${fmt(c.offer)}</button>
             <button class="dk-sl-hag" onclick="DARK.slingHaggle()">🤝 Haggle for more</button>`
          : `<div class="dk-muted" style="margin:4px 0 12px">${shortfall} Can't fill it.</div>
             <button class="dk-sl-take" onclick="DARK.slingDismiss()">Wave them off</button>`}
      </div>
    </div>`;
    el.appendChild(panel);
  },
  slingResume() {
    const sl = this._sling; if (!sl) return;
    const p = document.getElementById('dk-sl-dealwrap'); if (p) p.remove();
    clearInterval(sl.markerT); sl.markerT = null; sl.deal = null; sl.pending = null; sl.busy = false;
    this.slingTopRender();
  },
  slingDismiss() { if (typeof sfx === 'object' && sfx.tap) sfx.tap(); this.slingResume(); },
  slingTake() { const c = this._sling && this._sling.deal; if (c) this.slingCommit(c.drug, c.qty, c.offer, 'took'); },
  slingHaggle() {
    const sl = this._sling, c = sl && sl.deal; if (!c) return;
    const gw = c.bulk ? 12 : 18, gz = 50 - gw / 2;     // green band center ~50
    const btns = document.getElementById('dk-sl-dealbtns');
    btns.innerHTML = `<div class="dk-sl-bar">
        <div class="dk-sl-green" style="left:${gz}%;width:${gw}%"></div>
        <div class="dk-sl-marker" id="dk-sl-marker"></div>
      </div>
      <button class="dk-sl-stop" onclick="DARK.slingStop()">STOP</button>`;
    sl._gz = gz; sl._gw = gw; sl._pos = 0; sl._dir = 1;
    const m = document.getElementById('dk-sl-marker');
    sl.markerT = setInterval(() => {
      sl._pos += sl._dir * 3.2;
      if (sl._pos >= 100) { sl._pos = 100; sl._dir = -1; }
      if (sl._pos <= 0) { sl._pos = 0; sl._dir = 1; }
      if (m) m.style.left = sl._pos + '%';
    }, 40);
  },
  slingStop() {
    const sl = this._sling, c = sl && sl.deal; if (!c) return;
    clearInterval(sl.markerT); sl.markerT = null;
    const pos = sl._pos, gzL = sl._gz, gzR = sl._gz + sl._gw;
    let price, tone;
    if (pos >= gzL && pos <= gzR) { price = Math.round(c.offer * 1.4); tone = 'green'; }
    else if (pos >= gzL - 8 && pos <= gzR + 8) { price = Math.round(c.offer * 1.15); tone = 'near'; }
    else if (Math.random() < 0.5) {            // miss → 50/50 they walk
      if (typeof sfx === 'object' && sfx.error) sfx.error();
      toast(`${c.name} didn't like the price — walked off. 🚶`, 'error');
      this.slingResume(); return;
    } else { price = Math.round(c.offer * 0.8); tone = 'low'; }   // …or a worse counter
    // They respond to your haggle — confirm the new number before it's a deal.
    sl.pending = { price, tone };
    const pool = tone === 'low' ? this.HAGGLE_LOW : tone === 'green' ? this.HAGGLE_WIN : this.HAGGLE_OK;
    const line = pool[Math.floor(Math.random() * pool.length)];
    if (typeof sfx === 'object' && sfx.tap) sfx.tap();
    const btns = document.getElementById('dk-sl-dealbtns');
    btns.innerHTML = `<div class="dk-sl-react">"${line}"</div>
      <button class="dk-sl-take" onclick="DARK.slingSeal()">💰 Deal — ${fmt(price)}</button>
      <button class="dk-sl-hag" style="background:#3a2024" onclick="DARK.slingResume()">Walk away</button>`;
  },
  slingSeal() {
    const sl = this._sling, c = sl && sl.deal, p = sl && sl.pending;
    if (c && p) this.slingCommit(c.drug, c.qty, p.price, p.tone);
  },
  async slingCommit(drug, qty, price, tone) {
    const sl = this._sling; if (!sl) return;
    const r = await api('/dark/sling', 'POST', { drug, qty, price });
    if (r.error) { toast(r.error, 'error'); this.slingResume(); return; }
    // sync the fields the server changed (no full rerender — keeps the overlay alive)
    state.dark.stash = r.stash; state.dark.dirty_money = r.dirty_money;
    state.dark.cred = r.cred; state.dark.cred_xp = r.cred_xp;
    sl.earned += price; sl.xp += Math.round(price / 40); sl.deals += 1;
    if (typeof sfx === 'object' && sfx.cash) sfx.cash();
    const msg = tone === 'green' ? `Talked them up to ${fmt(price)}! 🤝` : tone === 'low' ? `Sold low — ${fmt(price)}.` : `Sold for ${fmt(price)}.`;
    toast(msg, tone === 'low' ? 'info' : 'success');
    (r.rank_msgs || []).forEach(m => toast(m, 'success'));
    this.slingResume();
  },
  async buyHome(id) {
    const r = await api('/dark/buy_home', 'POST', { prop_id: id });
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('New house on the books. 🏠', 'success');
  },
  async fixerWash() {
    const r = await api('/dark/fixer_wash', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.cash) sfx.cash();
    await refreshState(); this.rerender();
    toast(`The Fixer washed ${fmt(r.washed)} → ${fmt(r.clean)} clean (his cut: ${fmt(r.cut)}). 🧼`, 'success');
  },
  async hireManager(front) {
    const r = await api('/dark/hire_manager', 'POST', { front });
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('Dirty manager on the books. 🧑‍💼', 'success');
  },
  async fireManager(front) {
    const r = await api('/dark/fire_manager', 'POST', { front });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  async setLaunderRate(front, rate) {
    const r = await api('/dark/set_launder_rate', 'POST', { front, rate });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
  },
  _secOpen: { buy: false, owned: true },
  toggleSec(k) { this._secOpen[k] = !this._secOpen[k]; this.rerender(); },
  _homeTab: 'vacant',
  setHomeTab(k) { this._homeTab = k; this.rerender(); },
  _stashOpen: false,
  toggleStash() { this._stashOpen = !this._stashOpen; this.rerender(); },
  async sellVending() {
    const r = await api('/dark/sell_vending', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
    toast(`Vinny took it for ${fmt(r.payout)}. The corners are yours now. 🤝`, 'success');
  },
  async buyBusiness(key) {
    const r = await api('/dark/buy_business', 'POST', { key });
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('Bought. 💼', 'success');
  },
  async convertCasino() {
    const r = await api('/dark/convert_casino', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    if (typeof sfx === 'object' && sfx.purchase) sfx.purchase();
    await refreshState(); this.rerender(); toast('Arcade gutted — welcome to the casino. 🎰', 'success');
  },

  pageCrew() {
    const d = state.dark || {};
    const recruits = d.recruits || [];
    const roster   = d.roster || [];
    const crews    = d.crews || [];
    const wordOut  = d.recruits_refresh_day && d.recruits_refresh_day > (state.day || 0);
    const traitLine = (tk) => {
      const t = this.TRAITS[tk] || { name: tk, icon: '❓' };
      const extra = t.knows ? `<span class="dk-knows">🍳 cooks ${t.knows}</span>` : (t.desc ? `· ${t.desc}` : '');
      return `<b>${t.name}</b> ${extra}`;
    };
    const recruitRows = recruits.map(r => {
      const t = this.TRAITS[r.trait] || { cost: 2000, icon: '🧑' };
      const tooPoor = (state.cash || 0) < (t.cost || 0);
      return `<div class="dk-row">
        <div class="dk-row-ic">${t.icon || '🧑'}</div>
        <div class="dk-row-main"><div class="dk-row-title">${r.name}</div><div class="dk-muted">${traitLine(r.trait)}</div></div>
        <button class="dk-buy ${tooPoor ? 'dk-buy-off' : ''}" ${tooPoor ? 'disabled' : `onclick="DARK.hireRecruit(${r.id})"`}>${fmt(t.cost || 0)}</button>
      </div>`;
    }).join('') || `<div class="dk-muted" style="padding:8px 2px">Nobody around. Put the word out for fresh faces.</div>`;
    const crewRows = crews.map(c => {
      const members = roster.filter(m => m.crew_id === c.id);
      const cooks = [...this.crewCooks(c.id)].map(k => (this.DRUGS.find(x => x.key === k) || {}).name).filter(Boolean);
      const working = c.home_id != null;
      return `<div class="dk-card" style="margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:8px">
          <div style="flex:1"><b>${c.name}</b> <span class="dk-muted">· ${members.length} ppl · ${working ? '🧪 on a lab' : '😴 idle'}</span></div>
          ${working ? '' : `<button class="dk-x" onclick="DARK.disbandCrew(${c.id})">✕</button>`}
        </div>
        <div class="dk-muted" style="margin-top:4px">${members.map(m => `${(this.TRAITS[m.trait] || {}).icon || '🧑'} ${m.name}`).join('  ·  ')}</div>
        <div style="margin-top:6px">${cooks.length ? cooks.map(n => `<span class="dk-knows">🍳 ${n}</span>`).join(' ') : '<span class="dk-muted">⚠ no cook — this crew can\'t make anything yet</span>'}</div>
      </div>`;
    }).join('') || `<div class="dk-muted" style="padding:8px 2px">No crews yet — pick 3–5 from your payroll below.</div>`;
    const rosterRows = roster.map(m => {
      const inCrew = m.crew_id != null;
      const seld = this._sel.includes(m.id);
      return `<div class="dk-row ${seld ? 'dk-sel' : ''}" ${inCrew ? '' : `onclick="DARK.toggleSel(${m.id})"`} style="${inCrew ? 'opacity:0.5' : 'cursor:pointer'}">
        <div class="dk-row-ic">${(this.TRAITS[m.trait] || {}).icon || '🧑'}</div>
        <div class="dk-row-main">
          <div class="dk-row-title">${m.name}${inCrew ? ' <span class="dk-tag">in a crew</span>' : (seld ? ' <span class="dk-tag" style="background:#C0392B;color:#fff">picked</span>' : '')}</div>
          <div class="dk-muted">${traitLine(m.trait)}</div>
        </div>
        ${inCrew ? '' : `<button class="dk-x" onclick="event.stopPropagation();DARK.dismissRoster(${m.id})">✕</button>`}
      </div>`;
    }).join('') || `<div class="dk-muted" style="padding:8px 2px">No one on your payroll — hire from the street below.</div>`;
    const formBar = this._sel.length
      ? `<button class="dk-form ${this._sel.length < 3 ? 'dk-buy-off' : ''}" ${this._sel.length < 3 ? 'disabled' : 'onclick="DARK.formCrew()"'}>👥 Form crew from ${this._sel.length} ${this._sel.length < 3 ? '(need 3+)' : 'picked'}</button>`
      : '';
    return `
      ${this.sectionTitle('The Crew')}
      <div class="dk-card"><p class="dk-p">Recruit off the street, then group <b>3–5</b> into a crew. A crew can only cook a drug if a member <b>knows</b> it (the 🍳 tags). Put a crew on a home in the Property tab to start a lab.</p></div>
      ${this.sectionTitle(`Your Crews (${crews.length})`)}
      ${crewRows}
      ${this.sectionTitle(`Payroll (${roster.length}) — tap to pick`)}
      <div class="dk-list">${rosterRows}</div>
      ${formBar}
      <button class="dk-word ${wordOut ? 'dk-buy-off' : ''}" style="margin-top:14px" ${wordOut ? 'disabled' : 'onclick="DARK.putWordOut()"'}>
        ${wordOut ? '📞 Word is out — new faces tomorrow' : '📞 Put the word out — $2,000 (10 fresh faces)'}
      </button>
      ${this.sectionTitle(`On the Street (${recruits.length})`)}
      <div class="dk-list">${recruitRows}</div>
    `;
  },

  pageFence() {
    const d    = state.dark || {};
    const cred = d.cred || 1;
    const owned = d.supplies || {};
    const rows = this.DRUGS.map(drug => {
      const sup     = this.SUPPLIES[drug.key];
      const locked  = cred < drug.cred;
      const have    = owned[drug.key] || 0;
      const price   = this.supplyPrice(drug.key);
      const deal    = price < sup.cost;
      const tooPoor = (state.cash || 0) < price;
      const btn = locked
        ? `<div class="dk-row-soon">🔒 Cred ${drug.cred}</div>`
        : `<button class="dk-buy ${tooPoor ? 'dk-buy-off' : ''}" ${tooPoor ? 'disabled' : `onclick="DARK.buySupply('${drug.key}')"`}>${deal ? `<span style="text-decoration:line-through;opacity:0.6;font-size:9px">${fmt(sup.cost)}</span> ` : ''}${fmt(price)}</button>`;
      return `
      <div class="dk-row" style="${locked ? 'opacity:0.55' : ''}">
        <div class="dk-row-ic">${sup.icon}</div>
        <div class="dk-row-main">
          <div class="dk-row-title">${sup.name}${have ? ` <span class="dk-tag">×${have}</span>` : ''}</div>
          <div class="dk-muted">${drug.icon} one batch of ${drug.name}</div>
        </div>
        ${btn}
      </div>`;
    }).join('');
    return `
      ${this.sectionTitle('The Fence')}
      <div class="dk-card">
        <p class="dk-p">"You want to cook, you need supplies. No questions." Buy a set, then hand it to a crew at a lab to run a batch.</p>
      </div>
      ${this.sectionTitle('Supplies')}
      <div class="dk-list">${rows}</div>
      <div class="dk-muted" style="margin-top:10px">Higher-tier supplies unlock as your Street Cred grows. You're at <b style="color:#fff">Street Cred ${cred}</b>.</div>
    `;
  },

  pageDealers() {
    const d = state.dark || {};
    if (!d.corners_unlocked) {
      return `${this.sectionTitle('The Corners')}
        <div class="dk-card"><p class="dk-p">🔒 You're not working the corners yet. ${(d.biz || {}).vending
          ? 'Sell your vending business to cousin Vinny in the <b>Business</b> tab to free up the corners.'
          : 'Head to the <b>Business</b> tab to get started.'}</p></div>`;
    }
    const stash = d.stash || {};
    const dealers = d.dealers || [];
    const stashKeys = Object.keys(stash).filter(k => (stash[k] || 0) > 0);
    const hireCost = 5000 + 3000 * dealers.length;
    const stashRows = stashKeys.length ? stashKeys.map(k => {
      const drug = this.DRUGS.find(x => x.key === k) || { name: k, icon: '📦' };
      return `<div class="dk-row"><div class="dk-row-ic">${drug.icon}</div>
        <div class="dk-row-main"><div class="dk-row-title">${drug.name}</div><div class="dk-muted">${stash[k]} units</div></div></div>`;
    }).join('') : `<div class="dk-muted" style="padding:8px 2px">No product on hand — collect from a lab in the Property tab.</div>`;
    const dealerCards = dealers.map(dl => {
      const tier = this.heatTier(dl.heat); const hp = Math.min(100, Math.round(dl.heat || 0));
      const inv = dl.inventory || {}; const invKeys = Object.keys(inv).filter(k => (inv[k] || 0) > 0);
      const invStr = invKeys.length ? invKeys.map(k => `${(this.DRUGS.find(x => x.key === k) || {}).icon || '📦'} ${inv[k]}`).join('  ') : 'empty — stock them below';
      const stockRows = stashKeys.map(k => {
        const drug = this.DRUGS.find(x => x.key === k) || { name: k, icon: '📦' };
        const amt = n => `<button class="dk-rate" style="flex:0 0 auto;padding:6px 9px" onclick="DARK.stockDealer(${dl.id},'${k}',${n})">+${n}</button>`;
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:6px">
          <span style="flex:1;min-width:0;font-size:12px">${drug.icon} ${drug.name} <span class="dk-muted">(${stash[k]})</span></span>
          ${amt(5)}${amt(25)}${amt(100)}
        </div>`;
      }).join('');
      const ev = dl.event;
      return `<div class="dk-card" style="margin-bottom:8px;border-color:${ev ? '#E0533D' : dl.paused ? '#6a5a5a' : tier.col};${(ev || dl.paused) ? 'opacity:0.92' : ''}">
        <div style="display:flex;align-items:center;gap:8px">
          <div class="dk-row-ic">🧢</div>
          <div style="flex:1"><b>${dl.name}</b> <span class="dk-muted">· ${ev ? '<span style="color:#E0533D">⚠ paused</span>' : dl.paused ? '<span style="color:#FFC83D">paused</span>' : 'dealer'}</span><div class="dk-muted">carrying ${invStr}</div></div>
          <button class="dk-x" onclick="DARK.pauseDealer(${dl.id})" title="${dl.paused ? 'Resume' : 'Pause'}">${dl.paused ? '▶' : '⏸'}</button>
          <button class="dk-x" onclick="DARK.fireDealer(${dl.id})">✕</button>
        </div>
        ${ev ? this.evtHandle('dealer', dl.id, ev, 'Dealer paused') : ''}
        <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:9px"><span class="dk-muted">HEAT</span><span style="color:${tier.col};font-weight:800">${hp}% · ${tier.label}</span></div>
        <div class="dk-heat"><div class="dk-heat-fill" style="width:${hp}%;background:${tier.col}"></div></div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">
          <span style="font-size:12px">Holding <b style="color:#E0533D">${fmt(dl.held || 0)}</b> dirty</span>
          <button class="dk-buy ${(dl.held || 0) <= 0 ? 'dk-buy-off' : ''}" ${(dl.held || 0) <= 0 ? 'disabled' : `onclick="DARK.collectDealer(${dl.id})"`}>Collect</button>
        </div>
        ${stashKeys.length ? `<div class="dk-muted" style="font-size:10px;margin-top:10px">Stock from your stash (units):</div>${stockRows}` : ''}
      </div>`;
    }).join('') || `<div class="dk-muted" style="padding:8px 2px">No dealers yet — hire one to start moving product.</div>`;
    return `
      <button class="dk-sling-btn" onclick="DARK.openSling()">🎯 Sling Yourself <span>work the corner by hand · no heat</span></button>
      ${this.sectionTitle('Dealers')}
      <div class="dk-card"><p class="dk-p">Dealers move product into <b style="color:#E0533D">dirty money</b> on the street — up to <b>${this.dealerCap()}</b> units each per day. Keep them stocked, but pull their cash before the heat gets them. A bust takes everything they're holding.</p></div>
      <button class="dk-word" onclick="DARK.hireDealer()">🧢 Hire a dealer — ${fmt(hireCost)}</button>
      ${this.sectionTitle(`Your Dealers (${dealers.length})`)}
      ${dealerCards}
      ${this.sectionTitle('Your Stash')}
      <div class="dk-list">${stashRows}</div>
    `;
  },

  // ── Pages (placeholders showing real carried-over data; mechanics come later) ─
  pageHome() {
    const d  = state.dark || {};
    const cal = (typeof getSeasonInfo === 'function') ? getSeasonInfo(state.day || 1) : null;
    return `
      ${cal ? `<div class="dk-cal">
        <div><span style="font-size:17px">${cal.icon}</span> <b>${cal.name}</b> · Day ${cal.seasonDay} of 28 <span class="dk-muted2">· Year ${cal.year}</span></div>
        <div class="dk-cal-bar"><div style="width:${Math.round(cal.seasonDay / 28 * 100)}%"></div></div>
      </div>` : ''}
      <button class="dk-advance" onclick="DARK.advance()">⏭ Advance a Day</button>
      ${this.sectionTitle("The Empire You Don't Report")}
      <div class="dk-card">
        <p class="dk-p">You signed it all away. The Fixer left you a rundown house and ten grand in unmarked bills — nothing else. Build it back up from nothing, off the books this time. 😈</p>
      </div>
      <div class="dk-grid2" style="margin-top:10px">
        ${this.stat('💵 Clean Cash',  fmt(state.cash || 0),     '#4CAF50')}
        ${this.stat('🧼 Dirty Money', fmt(d.dirty_money || 0),  '#E0533D')}
        ${this.stat('🔥 Heat',        (d.heat || 0) + '%',      '#FF8A3D')}
        ${this.stat('🏆 Rank',        this.rank(d.cred || 1).name, '#C0392B')}
      </div>
      ${this.rankCard()}
      ${this.huntCard()}
    `;
  },
  rankCard() {
    const d = state.dark || {};
    const cred = d.cred || 1, xp = d.cred_xp || 0;
    const cur = this.rank(cred), next = this.rank(Math.min(10, cred + 1));
    const atMax = cred >= 10;
    const span = atMax ? 1 : (next.xp - cur.xp), into = atMax ? 1 : (xp - cur.xp);
    const pct = atMax ? 100 : Math.max(0, Math.min(100, Math.round(into / span * 100)));
    const ladder = this._ladderOpen ? `<div style="margin-top:10px">${this.RANKS.map(r => {
      const got = cred >= r.level;
      return `<div style="display:flex;gap:8px;padding:6px 0;border-top:1px solid #2a1518;${got ? '' : 'opacity:0.5'}">
        <span style="width:18px">${got ? '✅' : '🔒'}</span>
        <div style="flex:1"><b style="color:${got ? '#C0392B' : '#9a8a8a'}">${r.name}</b> <span class="dk-muted2">· Cred ${r.level}</span><div class="dk-muted" style="font-size:11px">${r.perk}</div></div>
      </div>`;
    }).join('')}</div>` : '';
    return `
      ${this.sectionTitle('Street Cred')}
      <div class="dk-card">
        <div style="display:flex;align-items:baseline;justify-content:space-between">
          <div><span class="dk-muted" style="font-size:10px">RANK ${cred}</span> <b style="font-size:16px;color:#C0392B">${cur.name}</b></div>
          ${atMax ? '<span class="dk-muted" style="font-size:11px">MAX</span>' : `<span class="dk-muted" style="font-size:11px">${fmt(into)} / ${fmt(span)} XP</span>`}
        </div>
        <div class="dk-heat" style="margin-top:8px"><div class="dk-heat-fill" style="width:${pct}%;background:#C0392B"></div></div>
        ${atMax ? `<div class="dk-muted" style="margin-top:8px">👑 ${cur.perk}</div>`
                : `<div class="dk-muted" style="margin-top:8px">Next — <b style="color:#FF8A3D">${next.name}</b>: ${next.perk}</div>`}
        <div class="dk-muted2" style="margin-top:7px;font-size:11px">Move product and wash money to build your rep.</div>
        <button class="dk-mini" style="width:100%;margin-top:9px" onclick="DARK.toggleLadder()">${this._ladderOpen ? 'Hide the ladder' : 'View the ladder'}</button>
        ${ladder}
      </div>`;
  },
  toggleLadder() { this._ladderOpen = !this._ladderOpen; if (typeof sfx === 'object' && sfx.tap) sfx.tap(); this.rerender(); },

  // ── The Hunt — the detective's case (global heat) + scramble actions ──
  DETECTIVE: 'Det. Marsh',
  RAID_SAFE: 65,
  huntTier(h) {
    if (h >= 85) return ['Closing In', '#E0533D'];
    if (h >= 65) return ['Building a Case', '#FF8A3D'];
    if (h >= 40) return ['Sniffing Around', '#FFC83D'];
    return ['Cold', '#4CAF50'];
  },
  huntCard() {
    const d = state.dark || {};
    if ((d.cred || 1) < 2) {   // Hunt not active yet — you're still small-time
      return `${this.sectionTitle('The Hunt')}
        <div class="dk-card"><div class="dk-muted" style="font-size:12px;line-height:1.5">🕵️ Nobody's watching you yet — you're too small to register. Make a name for yourself (<b>Street Cred 2</b>) and a detective will take an interest.</div></div>`;
    }
    const h = Math.round(d.heat || 0);
    const [label, col] = this.huntTier(h);
    const raid = d.raid_in;
    const bribeCost = 4000 + 1500 * (d.bribes || 0);
    const act = (a, label, sub, done) => `<button class="dk-hunt-act ${done ? 'done' : ''}" ${done ? 'disabled' : `onclick="DARK.huntAction('${a}')"`}><span>${label}</span><span class="dk-hunt-sub">${sub}</span></button>`;
    let body = `
      <div style="display:flex;align-items:baseline;justify-content:space-between">
        <div><span style="font-size:17px">🕵️</span> <b>${this.DETECTIVE}</b></div>
        <span style="color:${col};font-weight:800;font-size:12px">${label} · ${h}%</span>
      </div>
      <div class="dk-heat" style="margin-top:8px"><div class="dk-heat-fill" style="width:${h}%;background:${col}"></div></div>`;
    // ── The Watch: who/what Marsh is tailing (hidden until you have intel) ──
    const w = d.watch;
    if (w) {
      if (d.watch_known) {
        const lab = w.kind === 'crew' ? `tailing <b>${w.name}</b> — who works the <b>${w.house}</b>` : `watching the <b>${w.name}</b>`;
        body += `<div class="dk-hunt-watch known">👁️ Marsh is ${lab}. <b style="color:#E0533D">Pause that operation</b> and he'll lose the lead.</div>`;
      } else {
        const vip = (d.biz || {}).strip_club && d.vip;
        body += `<div class="dk-hunt-watch">🕵️ Marsh is tailing one of your operations — <b>you don't know which.</b>
          <div class="dk-hunt-acts" style="margin-top:8px">
            <button class="dk-hunt-act" onclick="DARK.buyIntel()"><span>🔎 Buy Intel</span><span class="dk-hunt-sub">${fmt(5000)} · mole</span></button>
            ${vip ? `<button class="dk-hunt-act" onclick="DARK.workVip()"><span>💋 Work VIP</span><span class="dk-hunt-sub">${fmt(6000)} · lounge</span></button>`
                  : `<button class="dk-hunt-act done" disabled><span>💋 VIP Lounge</span><span class="dk-hunt-sub">coming soon</span></button>`}
          </div></div>`;
      }
    }
    if (raid != null) {
      body += `<div class="dk-hunt-raid">
        <div class="dk-hunt-raid-t">🚨 RAID IN ${raid} DAY${raid === 1 ? '' : 'S'}</div>
        <div class="dk-muted" style="font-size:11px;margin-bottom:9px">Cool the case below ${this.RAID_SAFE}% to call it off — or soften the blow.</div>
        <div class="dk-hunt-acts">
          ${act('lie_low', '🛌 Lie Low', d.lying_low ? '✓ tomorrow' : 'quiet day', d.lying_low)}
          ${act('bribe', '💰 Pay Off', fmt(bribeCost))}
          ${act('lawyer', '⚖️ Lawyer Up', d.lawyered ? '✓ retained' : fmt(8000), d.lawyered)}
          ${act('move', '📦 Move Product', d.moved ? '✓ stashed' : fmt(3000), d.moved)}
        </div></div>`;
    } else {
      const note = h >= 65 ? "They're connecting your operations — cool it down."
                 : h >= 40 ? "Someone's been asking questions. Keep it low."
                 : "Nobody's looking your way. Stay sharp.";
      body += `<div class="dk-muted" style="margin-top:8px;font-size:12px">${note}</div>
        <div class="dk-hunt-acts" style="margin-top:9px">
          ${act('lie_low', '🛌 Lie Low', d.lying_low ? '✓ tomorrow' : 'quiet day · −heat', d.lying_low)}
          ${act('bribe', '💰 Pay Off', fmt(bribeCost))}
        </div>`;
    }
    return `${this.sectionTitle('The Hunt')}<div class="dk-card" style="border-color:${raid != null ? '#E0533D' : '#3a2024'}">${body}</div>`;
  },
  async huntAction(a) {
    const r = await api('/dark/hunt_action', 'POST', { action: a });
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender();
    if (r.msg) toast(r.msg, 'success');
  },
  async buyIntel() {
    const r = await api('/dark/buy_intel', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); if (r.msg) toast(r.msg, 'success');
  },
  async workVip() {
    const r = await api('/dark/work_vip', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); if (r.msg) toast(r.msg, 'success');
  },
  async buildVip() {
    const r = await api('/dark/build_vip', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState(); this.rerender(); toast('VIP lounge open — the chatter starts flowing. 💋', 'success');
  },

  pageProperties() {
    const d = state.dark || {};
    const props = state.properties || [];
    const idleCrews = (d.crews || []).filter(c => c.home_id == null);
    const market = (d.home_market || []).slice(0, 3);   // never show more than 3 (caps stale saves too)
    const vacant  = props.filter(p => !p.lab && !p.rented);
    const rented  = props.filter(p => !p.lab && p.rented);
    const cooking = props.filter(p => p.lab);
    const open = this._secOpen;
    const drop = (key, title, body) => `
      <div class="dk-drop" onclick="DARK.toggleSec('${key}')"><span>${title}</span><span>${open[key] ? '▾' : '▸'}</span></div>
      ${open[key] ? `<div style="margin-top:8px">${body}</div>` : ''}`;
    const buyRows = market.length ? market.map(p => {
      const tooPoor = (state.cash || 0) < (p.purchase_price || 0);
      return `<div class="dk-row">
        <div class="dk-row-ic">${p.foreclosure ? '🏷️' : '🏠'}</div>
        <div class="dk-row-main"><div class="dk-row-title">${p.type || 'Home'}</div><div class="dk-muted">${p.neighborhood || ''}</div></div>
        <button class="dk-buy ${tooPoor ? 'dk-buy-off' : ''}" ${tooPoor ? 'disabled' : `onclick="DARK.buyHome(${p.id})"`}>${fmt(p.purchase_price || 0)}</button>
      </div>`;
    }).join('') : `<div class="dk-muted" style="padding:8px 2px">No homes on the market today.</div>`;
    const tab = this._homeTab || 'vacant';
    const lists = { vacant, rented, cooking };
    const htab = (key, label, n) => `<button class="dk-htab ${tab === key ? 'active' : ''}" onclick="DARK.setHomeTab('${key}')">${label} <span class="dk-cnt">${n}</span></button>`;
    const sel = lists[tab] || [];
    const ownedBody = `
      <div class="dk-htabs">
        ${htab('vacant', '🏚️ Vacant', vacant.length)}
        ${htab('rented', '🏠 Rented', rented.length)}
        ${htab('cooking', '🧪 Cooking', cooking.length)}
      </div>
      ${sel.length ? sel.map(p => this.propCard(p, idleCrews)).join('') : '<div class="dk-muted" style="padding:8px 2px">No homes in this group.</div>'}`;
    return `
      ${this.sectionTitle('Property')}
      <div class="dk-card"><p class="dk-p">Buy homes to expand, then turn them into <b>labs</b> or <b>rent them out</b> for cover. Condition doesn't matter here — only heat does.</p></div>
      ${drop('buy', `🛒 Buy a Home (${market.length})`, buyRows)}
      ${drop('owned', `🏚️ Your Homes (${props.length})`, ownedBody)}
    `;
  },

  propCard(p, idleCrews) {
    const pill = (txt, col) => `<span class="dk-pill" style="color:${col};border-color:${col}66">${txt}</span>`;
    const head = (icon, st) => `<div class="dk-phead">
      <div class="dk-row-ic">${icon}</div>
      <div class="dk-row-main"><div class="dk-row-title">${p.type || 'Property'}</div><div class="dk-muted">${p.neighborhood || ''}</div></div>
      ${st}</div>`;
    if (p.lab) {
      const lab  = p.lab;
      const drug = this.DRUGS.find(x => x.key === lab.drug) || { name: lab.drug, icon: '🧪' };
      const crew = (state.dark.crews || []).find(c => c.id === lab.crew_id);
      const crewN = crew ? (state.dark.roster || []).filter(m => m.crew_id === crew.id).length : 0;
      const tier = this.heatTier(lab.heat);
      const hp   = Math.min(100, Math.round(lab.heat || 0));
      const batch = lab.batch;
      const supply = (state.dark.supplies || {})[lab.drug] || 0;
      const speed = lab.speed || 2;
      const sLabels = { 1: 'Slow', 2: 'Med', 3: 'Fast' };
      const ev = lab.event;
      const owed = lab.owed || 0;
      const pillTxt = ev ? '⚠ Paused' : (owed > 0 ? '💰 Payday' : (batch ? 'Cooking' : ((lab.product || 0) > 0 ? 'Ready' : 'Idle')));
      const pillCol = ev ? '#E0533D' : (owed > 0 ? '#FF8A3D' : (batch ? tier.col : ((lab.product || 0) > 0 ? '#4CAF50' : '#9a8a8a')));
      let mid;
      if (ev) {
        mid = this.evtHandle('lab', p.id, ev, 'Production paused');
      } else if (!crew || crewN === 0) {
        mid = '<div class="dk-muted" style="margin-top:9px;color:#ff6d4d">⚠ No working crew — dismantle and set it up again with a crew from the Crew tab.</div>';
      } else if (owed > 0) {
        const tooPoor = (state.cash || 0) < owed;
        const temperBar = (lab.temper || 0) > 0
          ? `<div class="dk-lbl" style="color:#E0533D">😤 Crew temper rising — pay up or they may walk off</div><div class="dk-heat"><div class="dk-heat-fill" style="width:${lab.temper}%;background:#E0533D"></div></div>`
          : `<div class="dk-lbl">They'll wait a few days — then tempers start to flare.</div>`;
        mid = `<div class="dk-pline">💰 Crew wants their cut: <b style="color:#FF8A3D">${fmt(owed)}</b> · no new batch until they're paid.</div>
          ${temperBar}
          <button class="dk-mini ${tooPoor ? 'dk-buy-off' : ''}" style="width:100%;margin-top:8px" ${tooPoor ? 'disabled' : `onclick="DARK.payCrew(${p.id})"`}>💵 ${tooPoor ? `Need ${fmt(owed)} clean to pay them` : `Pay the crew ${fmt(owed)}`}</button>`;
      } else if (batch) {
        const total = this.BATCH_DAYS[batch.speed] || 3;
        const done = total - (batch.days_left || 0);
        mid = `<div class="dk-pline">⏳ Cooking <b>${batch.yield} units</b> · ${batch.days_left} day${batch.days_left === 1 ? '' : 's'} left · ${sLabels[batch.speed]}</div>
          <div class="dk-heat"><div class="dk-heat-fill" style="width:${Math.round(done / total * 100)}%;background:#C0392B"></div></div>`;
      } else {
        const speedBtns = [1, 2, 3].map(sp => `<button class="dk-rate ${speed === sp ? 'active' : ''}" onclick="DARK.setLabSpeed(${p.id},${sp})">${sLabels[sp]}</button>`).join('');
        const canStart = supply > 0;
        mid = `<div class="dk-lbl">Cook speed — faster finishes sooner but runs hotter</div>
          <div class="dk-rates">${speedBtns}</div>
          <button class="dk-mini ${canStart ? '' : 'dk-buy-off'}" style="width:100%;margin-top:8px" ${canStart ? `onclick="DARK.startBatch(${p.id},${speed})"` : 'disabled'}>🧪 ${canStart ? `Start a batch · uses 1 ${drug.name} supply (have ${supply})` : 'No supplies — buy at the Fence'}</button>`;
      }
      return `<div class="dk-card dk-pcard" style="border-color:${pillCol}66">
        ${head('🧪', pill(pillTxt, pillCol))}
        <div class="dk-pline">${drug.icon} <b>${drug.name}</b> · ${crew && crewN ? `${crew.name} (${crewN})` : '<span style="color:#ff6d4d">⚠ no crew</span>'}</div>
        <div class="dk-chips">
          <div class="dk-chip">${lab.product || 0}<span>📦 units</span></div>
          <div class="dk-chip" style="color:${tier.col}">${hp}%<span>🔥 ${tier.label}</span></div>
        </div>
        ${mid}
        <button class="dk-mini ${(lab.product || 0) > 0 ? '' : 'dk-buy-off'}" style="width:100%;margin-top:8px" ${(lab.product || 0) > 0 ? `onclick="DARK.collectLab(${p.id})"` : 'disabled'}>📦 ${(lab.product || 0) > 0 ? `Collect ${lab.product} units` : 'Nothing to collect yet'}</button>
        <button class="dk-mini-x" onclick="DARK.dismantleLab(${p.id})">Dismantle lab</button>
      </div>`;
    }
    if (p.rented) {
      const t = p.tenant || {};
      return `<div class="dk-card dk-pcard">
        ${head(t.icon || '🏠', pill('Rented', '#4CAF50'))}
        ${t.name ? `<div class="dk-pline"><b>${t.name}</b> · ${fmt(t.rent || 0)}/wk</div>` : ''}
        <div class="dk-muted" style="margin-top:5px;color:#4CAF50">🛡️ Cover — bleeds your global heat down, pays weekly, no hassle.</div>
        <button class="dk-mini-x" onclick="DARK.toggleRent(${p.id})">Evict / stop renting</button>
      </div>`;
    }
    const picker = this._labFor === p.id ? this.labPicker(p, idleCrews)
                 : this._rentFor === p.id ? this.rentPicker(p)
                 : this._cookFor === p.id ? this.cookPicker(p) : '';
    return `<div class="dk-card dk-pcard">
      ${head(p.foreclosure ? '🏷️' : '🏚️', pill('Vacant', '#9a8a8a'))}
      <button class="dk-mini" style="width:100%" onclick="DARK.openCookPicker(${p.id})">👨‍🍳 Cook here yourself</button>
      <div class="dk-twocol" style="margin-top:7px">
        <button class="dk-mini" onclick="DARK.openLabPicker(${p.id})">🧪 Set up lab</button>
        <button class="dk-mini" onclick="DARK.openRentPicker(${p.id})">🏠 Rent out</button>
      </div>
      ${picker}
    </div>`;
  },
  openCookPicker(propId) { this._cookFor = (this._cookFor === propId ? null : propId); this._labFor = null; this._rentFor = null; this.rerender(); },
  cookPicker(p) {
    const d = state.dark || {}, cred = d.cred || 1, cash = state.cash || 0;
    const PER_DAY = 3;
    const left = (d.cook_day === state.day) ? Math.max(0, PER_DAY - (d.cooks_today || 0)) : PER_DAY;
    if (left <= 0) {
      return `<div style="margin-top:9px;border-top:1px solid #3a2024;padding-top:9px"><div class="dk-muted">👨‍🍳 You've cooked all 3 of today's hand-batches — advance a day to cook again.</div></div>`;
    }
    const rows = this.DRUGS.map(dr => {
      const cost = this.COOK_COST[dr.key] || 0, locked = cred < dr.cred, poor = cash < cost, can = !locked && !poor;
      return `<button class="dk-rate ${can ? '' : 'dk-buy-off'}" style="flex:0 0 auto;padding:7px 9px" ${can ? `onclick="DARK.startCook(${p.id},'${dr.key}')"` : 'disabled'}>${dr.icon} ${dr.name}${locked ? ` 🔒${dr.cred}` : ` <span class="dk-muted2">${fmt(cost)}</span>`}</button>`;
    }).join('');
    return `<div style="margin-top:9px;border-top:1px solid #3a2024;padding-top:9px">
      <div class="dk-muted" style="margin-bottom:6px">Cook by hand — <b>${left} ${left === 1 ? 'cook' : 'cooks'} left today</b> (3/day). Costs a little cash for ingredients; product goes straight to your stash. No crew, no cut.</div>
      <div class="dk-rates" style="flex-wrap:wrap;gap:6px">${rows}</div></div>`;
  },
  startCook(propId, drug) { this._cookFor = null; if (typeof sfx === 'object' && sfx.tap) sfx.tap(); COOK.open(propId, drug); },

  labPicker(p, idleCrews) {
    if (!idleCrews.length) return `<div class="dk-muted" style="margin-top:9px">No idle crews — form one in the Crew tab first.</div>`;
    const cred  = (state.dark.cred) || 1;
    const blocks = idleCrews.map(c => {
      const opts = [...this.crewCooks(c.id)].map(k => {
        const drug = this.DRUGS.find(x => x.key === k); if (!drug) return '';
        const locked = cred < drug.cred;
        return `<button class="dk-rate ${locked ? 'dk-buy-off' : ''}" ${locked ? 'disabled' : `onclick="DARK.assignLab(${c.id},${p.id},'${k}')"`}>${drug.icon} ${drug.name}${locked ? ` <span style="font-size:8px">🔒Cred ${drug.cred}</span>` : ''}</button>`;
      }).join('') || '<span class="dk-muted">⚠ this crew has no cook</span>';
      return `<div style="margin-top:8px"><div class="dk-muted" style="margin-bottom:4px">${c.name}:</div><div class="dk-rates" style="flex-wrap:wrap">${opts}</div></div>`;
    }).join('');
    return `<div style="margin-top:9px;border-top:1px solid #3a2024;padding-top:9px"><div class="dk-muted">Pick a crew + product to cook:</div>${blocks}</div>`;
  },

  pageCash() {
    const d = state.dark || {}; const biz = d.biz || {}; const launder = d.launder || {}; const cash = state.cash || 0;
    const frontCard = (key) => {
      const meta = this.LAUNDER[key];
      if (!biz[key]) {
        const poor = cash < meta.price;
        return `<div class="dk-card dk-pcard"><div class="dk-phead"><div class="dk-row-ic">${meta.icon}</div>
          <div class="dk-row-main"><div class="dk-row-title">${meta.name}</div><div class="dk-muted">A cash front for washing money. Buy it, hire a dirty manager, set a wash rate.</div></div></div>
          <button class="dk-mini ${poor ? 'dk-buy-off' : ''}" style="width:100%;margin-top:9px" ${poor ? 'disabled' : `onclick="DARK.buyBusiness('${key}')"`}>Buy — ${fmt(meta.price)}</button></div>`;
      }
      const ln = launder[key] || { manager: false, heat: 0, rate: 0 };
      const tier = this.heatTier(ln.heat); const hp = Math.min(100, Math.round(ln.heat || 0));
      const labels = ['Off', 'Low', 'Med', 'High'];
      if (!ln.manager) {
        const poor = cash < meta.hire;
        return `<div class="dk-card dk-pcard"><div class="dk-phead"><div class="dk-row-ic">${meta.icon}</div>
          <div class="dk-row-main"><div class="dk-row-title">${meta.name}</div><div class="dk-muted">Washes up to ${fmt(meta.cap)}/day per level. Needs a dirty manager.</div></div></div>
          <button class="dk-mini ${poor ? 'dk-buy-off' : ''}" style="width:100%;margin-top:9px" ${poor ? 'disabled' : `onclick="DARK.hireManager('${key}')"`}>🧑‍💼 Hire dirty manager — ${fmt(meta.hire)}</button></div>`;
      }
      const rates = [0, 1, 2, 3].map(rt => `<button class="dk-rate ${ln.rate === rt ? 'active' : ''}" onclick="DARK.setLaunderRate('${key}',${rt})">${labels[rt]}</button>`).join('');
      const ev = ln.event;
      return `<div class="dk-card dk-pcard" style="border-color:${ev ? '#E0533D' : tier.col + '66'}">
        <div class="dk-phead"><div class="dk-row-ic">${meta.icon}</div>
          <div class="dk-row-main"><div class="dk-row-title">${meta.name} ${ev ? '<span style="color:#E0533D;font-size:11px">⚠ paused</span>' : ''}</div><div class="dk-muted">Up to ${fmt(meta.cap * (ln.rate || 1))}/day at this rate</div></div></div>
        ${ev ? this.evtHandle('front', key, ev, 'Washing paused') : ''}
        <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:9px"><span class="dk-muted">BUSINESS HEAT</span><span style="color:${tier.col};font-weight:800">${hp}% · ${tier.label}</span></div>
        <div class="dk-heat"><div class="dk-heat-fill" style="width:${hp}%;background:${tier.col}"></div></div>
        <div class="dk-lbl">Wash rate — more = faster clean + more heat · $${meta.wage}/day upkeep</div>
        <div class="dk-rates">${rates}</div>
        <button class="dk-mini-x" onclick="DARK.fireManager('${key}')">Let the manager go</button>
      </div>`;
    };
    const fday = (d.fixer_washed_day === state.day) ? (d.fixer_washed || 0) : 0;
    const fLeft = Math.max(0, 8000 - fday);
    const fAmt = Math.min(d.dirty_money || 0, fLeft);
    const fNet = Math.round(fAmt * 0.85);
    const fOk = fAmt > 0;
    return `
      ${this.sectionTitle('Cash')}
      <div class="dk-grid2">
        ${this.stat('💵 Clean Cash',  fmt(cash),               '#4CAF50')}
        ${this.stat('🧼 Dirty Money', fmt(d.dirty_money || 0), '#E0533D')}
      </div>
      <div class="dk-card" style="margin-top:10px">
        <p class="dk-p">Dirty money's useless until it's washed. No front yet? The Fixer will wash it for you — for a cut.</p>
      </div>
      ${this.debtPanel()}
      ${this.sectionTitle("The Fixer's Quick-Wash")}
      <div class="dk-card dk-pcard">
        <div class="dk-phead"><div class="dk-row-ic">🕴️</div>
          <div class="dk-row-main"><div class="dk-row-title">The Fixer</div><div class="dk-muted">Instant, no front needed. He takes <b>15%</b> · up to <b>${fmt(8000)}/day</b>.</div></div></div>
        <div class="dk-muted2" style="margin-top:7px;font-size:11px">${fmt(fLeft)} left to wash with him today</div>
        <button class="dk-mini ${fOk ? '' : 'dk-buy-off'}" style="width:100%;margin-top:8px" ${fOk ? 'onclick="DARK.fixerWash()"' : 'disabled'}>${fOk ? `🧼 Wash ${fmt(fAmt)} → get ${fmt(fNet)}` : ((d.dirty_money || 0) <= 0 ? 'No dirty money to wash' : 'Maxed out with the Fixer today')}</button>
      </div>
      ${this.sectionTitle('Laundering Fronts')}
      ${frontCard('laundromat')}${frontCard('car_wash')}${frontCard('pizzeria')}
      ${this.soon('The Underworld Bank', 'Loan shark, offshore shells, street rep. Coming soon.')}
    `;
  },

  pageBusinesses() {
    const soon = (icon, title, body) => `<div class="dk-card" style="margin-bottom:8px;opacity:.92">
      <div style="display:flex;align-items:center;gap:10px">
        <div class="dk-row-ic">${icon}</div>
        <div class="dk-row-main"><div class="dk-row-title">${title} <span style="font-size:9px;font-weight:800;color:#FFC83D;border:1px solid #FFC83D66;border-radius:5px;padding:1px 5px;vertical-align:middle;text-transform:uppercase;letter-spacing:.5px">Soon</span></div><div class="dk-muted">${body}</div></div>
      </div></div>`;
    return `
      ${this.sectionTitle('Business')}
      <div class="dk-card"><p class="dk-p">Your <b>earners</b> — the muscle of the operation. They'll pull in money on their own (and the club becomes your ear on the cops) once they open up. Laundering fronts live over in the <b>Cash</b> tab.</p></div>
      ${soon('💋', 'Strip Club', 'A cash earner — and its VIP lounge becomes your ear on the cops in The Hunt.')}
      ${soon('🎰', 'Underground Casino', 'Rig the tables and rake the house — a pure money-maker.')}
      ${soon('🔧', 'Chop Shop', 'Strip stolen cars for parts — steady dirty cash off the street.')}
    `;
  },

  // ── Bits ────────────────────────────────────────────────────────────────--
  sectionTitle(t) { return `<div class="dk-sec">${t}</div>`; },
  stat(label, val, col) {
    return `<div class="dk-stat">
      <div class="dk-res-lbl">${label}</div>
      <div class="dk-stat-val" style="color:${col}">${val}</div></div>`;
  },
  soon(title, body) {
    return `<div class="dk-soon">
      <div class="dk-soon-tag">🚧 Coming soon</div>
      <div class="dk-soon-title">${title}</div>
      <div class="dk-muted" style="margin-top:3px">${body}</div></div>`;
  },

  css() {
    return `
    /* Mobile: stop taps/holds/drags from highlighting text or popping the iOS copy-paste bubble */
    body.dark-mode, body.dark-mode *, .dk-evt-overlay, .dk-evt-overlay *, .dkck-ov, .dkck-ov * {
      -webkit-user-select:none; -moz-user-select:none; -ms-user-select:none; user-select:none;
      -webkit-touch-callout:none;
    }
    #dkckS, #ckcS, #dk-sl-area, .dk-sl-cust, .dk-sl-bar, .dk-sl-deal{touch-action:none}
    .dk-app{max-width:480px;width:100%;height:100%;display:flex;flex-direction:column;background:#0c0608;color:#e8d9d9;font-family:'Inter',sans-serif}
    .dk-header{flex-shrink:0;padding:12px 14px 10px;background:linear-gradient(150deg,#3A0E10,#7A1A1E);border-bottom:2px solid #C0392B}
    .dk-brand{font-family:'Rubik Dirt',cursive;font-size:17px;color:#fff;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
    .dk-rank{font-family:'Inter',sans-serif;font-size:10px;font-weight:700;color:#f0c0c0;letter-spacing:0.5px;text-transform:uppercase}
    .dk-res{display:flex;gap:8px;margin-top:9px}
    .dk-res-cell{flex:1;background:rgba(0,0,0,0.28);border-radius:8px;padding:5px 8px}
    .dk-res-lbl{font-size:9px;color:#c9a9a9;text-transform:uppercase;letter-spacing:0.4px}
    .dk-res-val{font-size:15px;font-weight:800;line-height:1.2}
    .dk-stashbar{display:flex;justify-content:space-between;align-items:center;background:rgba(0,0,0,0.28);border-radius:8px;padding:7px 10px;margin-top:8px;font-size:12px;font-weight:800;color:#fff;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .dk-stashlist{background:rgba(0,0,0,0.28);border-radius:8px;padding:2px 10px;margin-top:6px}
    .dk-stashrow{display:flex;justify-content:space-between;align-items:center;font-size:12px;font-weight:700;padding:6px 0;color:#f0e0e0;border-bottom:1px solid rgba(255,255,255,0.08)}
    .dk-stashrow:last-child{border-bottom:none}
    .dk-q{color:#c9a9a9;font-size:10px;font-weight:700}
    .dk-content{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:14px 14px 22px}
    .dk-sec{font-size:11px;font-weight:800;color:#C0392B;text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px}
    .dk-sec:first-child{margin-top:2px}
    .dk-card{background:#140a0c;border:1px solid #3a2024;border-radius:10px;padding:12px 13px}
    .dk-p{font-size:13px;line-height:1.5;margin:0;color:#e0cfcf}
    .dk-muted{font-size:11px;color:#9a8a8a;line-height:1.45}
    .dk-muted2{font-size:10px;color:#7a6a6a}
    .dk-grid2{display:grid;grid-template-columns:1fr 1fr;gap:9px}
    .dk-stat{background:#140a0c;border:1px solid #3a2024;border-radius:10px;padding:10px 12px}
    .dk-stat-val{font-size:18px;font-weight:800;margin-top:2px}
    .dk-list{display:flex;flex-direction:column;gap:7px}
    .dk-row{display:flex;align-items:center;gap:10px;background:#140a0c;border:1px solid #3a2024;border-radius:10px;padding:9px 11px}
    .dk-row-ic{font-size:22px;flex-shrink:0}
    .dk-row-main{flex:1;min-width:0}
    .dk-row-title{font-size:13px;font-weight:700}
    .dk-row-soon{font-size:9px;font-weight:800;color:#7a6a6a;text-transform:uppercase;letter-spacing:0.5px;flex-shrink:0}
    .dk-buy{flex-shrink:0;background:#C0392B;border:none;color:#fff;font-weight:800;font-size:12px;padding:7px 12px;border-radius:8px;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .dk-buy-off{background:#2a1418;color:#6a5a5a;cursor:default}
    .dk-knows{display:inline-block;font-size:10px;font-weight:800;color:#1a2e10;background:#7ec850;border-radius:5px;padding:1px 6px;margin-left:4px}
    .dk-word{width:100%;background:linear-gradient(150deg,#3A0E10,#7A1A1E);border:1px solid #C0392B;color:#fff;font-weight:800;font-size:13px;padding:12px;border-radius:10px;cursor:pointer;margin-bottom:4px;-webkit-tap-highlight-color:transparent}
    .dk-x{flex-shrink:0;background:none;border:1px solid #3a2024;color:#9a8a8a;width:30px;height:30px;border-radius:7px;cursor:pointer;font-size:13px}
    .dk-sel{border-color:#C0392B!important;background:#1f0d10}
    .dk-form{width:100%;background:#C0392B;border:none;color:#fff;font-weight:800;font-size:14px;padding:13px;border-radius:10px;cursor:pointer;margin-top:8px;-webkit-tap-highlight-color:transparent}
    .dk-heat{height:7px;background:#2a1418;border-radius:4px;overflow:hidden;margin-top:4px}
    .dk-heat-fill{height:100%;border-radius:4px;transition:width 0.3s}
    .dk-rates{display:flex;gap:6px;margin-top:8px}
    .dk-rate{flex:1;background:#1a1012;border:1px solid #3a2024;color:#cbb6b6;font-weight:700;font-size:11px;padding:7px 4px;border-radius:7px;cursor:pointer}
    .dk-rate.active{background:#C0392B;border-color:#C0392B;color:#fff}
    .dk-mini{flex:1;background:#1a1012;border:1px solid #3a2024;color:#e8d9d9;font-weight:700;font-size:12px;padding:9px;border-radius:8px;cursor:pointer}
    .dk-mini-x{width:100%;margin-top:8px;background:none;border:1px solid #3a2024;color:#9a8a8a;font-size:11px;padding:8px;border-radius:8px;cursor:pointer}
    .dk-drop{display:flex;justify-content:space-between;align-items:center;background:#1a1012;border:1px solid #3a2024;border-radius:10px;padding:12px 13px;margin-top:10px;font-weight:800;font-size:13px;color:#e8d9d9;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .dk-htabs{display:flex;gap:6px;margin-bottom:10px}
    .dk-htab{flex:1;background:#1a1012;border:1px solid #3a2024;color:#cbb6b6;font-weight:700;font-size:11px;padding:9px 4px;border-radius:8px;cursor:pointer;text-align:center;white-space:nowrap;-webkit-tap-highlight-color:transparent}
    .dk-htab.active{background:#C0392B;border-color:#C0392B;color:#fff}
    .dk-cnt{display:inline-block;background:#3a2024;color:#cbb6b6;font-size:10px;font-weight:800;border-radius:999px;padding:0 6px;margin-left:2px}
    .dk-htab.active .dk-cnt{background:rgba(255,255,255,0.28);color:#fff}
    .dk-pcard{margin-bottom:8px}
    .dk-phead{display:flex;align-items:center;gap:10px}
    .dk-pill{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;padding:3px 9px;border-radius:999px;border:1px solid;flex-shrink:0}
    .dk-pline{font-size:12px;margin-top:9px}
    .dk-chips{display:flex;gap:6px;margin-top:10px}
    .dk-chip{flex:1;background:#1a1012;border:1px solid #3a2024;border-radius:8px;padding:7px 4px;text-align:center;font-size:15px;font-weight:800;line-height:1.15}
    .dk-chip span{display:block;font-size:8px;font-weight:700;color:#9a8a8a;text-transform:uppercase;letter-spacing:0.3px;margin-top:2px}
    .dk-lbl{font-size:9px;color:#9a8a8a;text-transform:uppercase;letter-spacing:0.5px;margin-top:11px;margin-bottom:2px}
    .dk-twocol{display:flex;gap:8px;margin-top:10px}
    .dk-advance{width:100%;background:linear-gradient(150deg,#C0392B,#7A1A1E);border:none;color:#fff;font-weight:800;font-size:15px;padding:14px;border-radius:12px;cursor:pointer;margin-bottom:6px;box-shadow:0 2px 10px rgba(192,57,43,0.35);-webkit-tap-highlight-color:transparent}
    .dk-cal{background:#140a0c;border:1px solid #3a2024;border-radius:10px;padding:10px 12px;margin-bottom:8px;font-size:13px}
    .dk-cal-bar{height:5px;background:#2a1418;border-radius:3px;margin-top:7px;overflow:hidden}
    .dk-cal-bar>div{height:100%;background:#C0392B;border-radius:3px}
    .dk-tag{font-size:9px;font-weight:800;color:#0c0608;background:#9a8a8a;border-radius:5px;padding:1px 5px;vertical-align:middle}
    .dk-soon{background:rgba(192,57,43,0.07);border:1px dashed #5a2024;border-radius:10px;padding:12px 13px;margin-top:10px}
    .dk-soon-tag{font-size:9px;font-weight:800;color:#C0392B;text-transform:uppercase;letter-spacing:0.5px}
    .dk-soon-title{font-size:13px;font-weight:800;margin-top:3px}
    .dk-wake{width:100%;margin-top:18px;background:none;border:1px solid #3a2024;color:#9a8a8a;padding:12px;border-radius:10px;font-size:13px;cursor:pointer;line-height:1.4}
    .dk-nav{flex-shrink:0;display:flex;background:#0a0506;border-top:1px solid #2a1418;padding-bottom:env(safe-area-inset-bottom,0px)}
    .dk-nav-btn{flex:1;background:none;border:none;color:#7a6a6a;padding:8px 2px 9px;font-size:10px;font-weight:700;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px;border-top:2px solid transparent;-webkit-tap-highlight-color:transparent}
    .dk-nav-ic{font-size:20px;line-height:1}
    .dk-nav-btn.active{color:#fff;border-top-color:#C0392B;background:linear-gradient(180deg,rgba(192,57,43,0.18),transparent)}
    .dk-evt-overlay{position:fixed;inset:0;z-index:9500;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;padding:24px}
    .dk-evt-card{max-width:380px;width:100%;background:#160a0c;border:1px solid #C0392B;border-radius:14px;padding:22px 18px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.6)}
    .dk-evt-icon{font-size:44px;line-height:1;margin-bottom:10px}
    .dk-evt-text{font-size:14px;line-height:1.55;color:#e8d9d9;margin-bottom:18px}
    .dk-evt-choices{display:flex;flex-direction:column;gap:8px}
    .dk-evt-choice{background:#C0392B;border:none;color:#fff;font-weight:800;font-size:13px;padding:13px;border-radius:10px;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .dk-evt-choice:active{opacity:0.85}
    .dk-evt-handle{display:flex;flex-direction:column;gap:2px;width:100%;margin-top:9px;padding:10px 12px;text-align:left;background:linear-gradient(180deg,rgba(224,83,61,0.22),rgba(224,83,61,0.08));border:1px solid #E0533D;border-radius:10px;cursor:pointer;-webkit-tap-highlight-color:transparent;animation:dkpulse 1.6s ease-in-out infinite}
    .dk-evt-handle:active{opacity:0.85}
    .dk-evt-handle-t{color:#ffd9d0;font-size:12px;font-weight:700;line-height:1.35}
    .dk-evt-handle-s{color:#E0533D;font-size:10px;font-weight:800;letter-spacing:0.3px;text-transform:uppercase}
    @keyframes dkpulse{0%,100%{border-color:#E0533D}50%{border-color:#ff8a73}}
    /* ── Sling Yourself minigame ── */
    .dk-sling-btn{width:100%;display:flex;flex-direction:column;align-items:center;gap:2px;background:linear-gradient(180deg,#C0392B,#8e2a20);border:none;color:#fff;font-weight:800;font-size:15px;padding:13px;border-radius:11px;cursor:pointer;margin-bottom:12px;-webkit-tap-highlight-color:transparent}
    .dk-sling-btn span{font-size:10px;font-weight:700;opacity:0.85;text-transform:uppercase;letter-spacing:0.4px}
    .dk-sling-btn:active{opacity:0.9}
    #dk-sling{position:fixed;inset:0;z-index:9400;background:#0c0608;display:flex;flex-direction:column;overflow:hidden}
    .dk-sl-top{display:flex;align-items:center;gap:8px;padding:12px 14px;border-bottom:1px solid #2a1518;background:#0c0608}
    .dk-sl-inv{flex:1;display:flex;flex-wrap:wrap;gap:5px}
    .dk-sl-chip{background:#1a1012;border:1px solid #3a2024;border-radius:7px;padding:4px 8px;font-size:13px;font-weight:800;color:#e8d9d9}
    .dk-sl-right{display:flex;flex-direction:column;align-items:flex-end;gap:5px}
    .dk-sl-tally{font-size:11px;font-weight:800;color:#4CAF50;white-space:nowrap}
    .dk-sl-done{background:#1a1012;border:1px solid #3a2024;color:#e8d9d9;font-weight:800;font-size:12px;padding:6px 14px;border-radius:8px;cursor:pointer}
    .dk-sl-area{position:relative;flex:1;overflow:hidden}
    .dk-sl-cust{position:absolute;display:flex;flex-direction:column;align-items:center;gap:1px;background:#160a0c;border:1px solid #C0392B;border-radius:10px;padding:8px 12px;cursor:pointer;-webkit-tap-highlight-color:transparent;opacity:0;animation-name:dkslfade;animation-timing-function:ease-in-out;animation-fill-mode:forwards}
    .dk-sl-cust.bulk{border-color:#FFC83D;background:#1a1206;box-shadow:0 0 14px rgba(255,200,61,0.25)}
    .dk-sl-cn{font-weight:800;font-size:13px;color:#fff}
    .dk-sl-ca{font-size:11px;color:#cbb6b6}
    @keyframes dkslfade{0%{opacity:0;transform:scale(0.9)}12%{opacity:1;transform:scale(1)}80%{opacity:1}100%{opacity:0;transform:scale(0.95)}}
    .dk-sl-hint{text-align:center;color:#9a8a8a;font-size:12px;padding:10px}
    .dk-sl-dealwrap{position:absolute;inset:0;z-index:5;background:rgba(0,0,0,0.55);display:flex;align-items:center;justify-content:center;padding:22px}
    .dk-sl-deal{max-width:360px;width:100%;background:#160a0c;border:1px solid #C0392B;border-radius:14px;padding:20px 18px;text-align:center}
    .dk-sl-deal-name{font-weight:800;font-size:17px;color:#fff;margin-bottom:8px}
    .dk-sl-deal-line{font-size:14px;font-style:italic;color:#d8c4c4;line-height:1.5;margin-bottom:14px}
    .dk-sl-deal-ask{font-size:13px;color:#e8d9d9;margin-bottom:16px}
    .dk-sl-deal-btns{display:flex;flex-direction:column;gap:8px}
    .dk-sl-take{background:#2e7d32;border:none;color:#fff;font-weight:800;font-size:14px;padding:13px;border-radius:10px;cursor:pointer}
    .dk-sl-hag{background:#C0392B;border:none;color:#fff;font-weight:800;font-size:14px;padding:13px;border-radius:10px;cursor:pointer}
    .dk-sl-bar{position:relative;height:26px;background:#1a1012;border:1px solid #3a2024;border-radius:8px;overflow:hidden;margin-bottom:10px}
    .dk-sl-green{position:absolute;top:0;bottom:0;background:rgba(76,175,80,0.55);border-left:2px solid #4CAF50;border-right:2px solid #4CAF50}
    .dk-sl-marker{position:absolute;top:-2px;bottom:-2px;left:0;width:4px;background:#FFC83D;box-shadow:0 0 8px #FFC83D}
    .dk-sl-stop{width:100%;background:#FFC83D;border:none;color:#1a1012;font-weight:900;font-size:15px;padding:13px;border-radius:10px;cursor:pointer;letter-spacing:1px}
    .dk-sl-react{font-size:14px;font-style:italic;color:#FFC83D;line-height:1.5;margin:2px 0 12px;font-weight:700}
    /* The Hunt */
    .dk-hunt-raid{margin-top:11px;padding:11px;border:1px solid #E0533D;border-radius:9px;background:rgba(224,83,61,0.09);animation:dkpulse 1.6s ease-in-out infinite}
    .dk-hunt-raid-t{color:#E0533D;font-weight:900;font-size:13px;letter-spacing:0.5px;margin-bottom:3px}
    .dk-hunt-acts{display:grid;grid-template-columns:1fr 1fr;gap:7px}
    .dk-hunt-act{display:flex;flex-direction:column;align-items:center;gap:2px;background:#1a1012;border:1px solid #3a2024;color:#e8d9d9;font-weight:800;font-size:12px;padding:9px 6px;border-radius:9px;cursor:pointer;-webkit-tap-highlight-color:transparent}
    .dk-hunt-act.done{opacity:0.5;border-color:#2e7d32;cursor:default}
    .dk-hunt-sub{font-size:9px;font-weight:700;color:#9a8a8a;text-transform:uppercase;letter-spacing:0.3px}
    .dk-hunt-watch{margin-top:10px;padding:10px;border:1px dashed #6a5a5a;border-radius:9px;background:rgba(255,255,255,0.02);font-size:12px;color:#cbb6b6;line-height:1.45}
    .dk-hunt-watch.known{border-style:solid;border-color:#E0533D;background:rgba(224,83,61,0.08);color:#e8d9d9}
    .dk-brandrow{display:flex;align-items:center;justify-content:space-between;gap:8px}
    .dk-hdr-btns{display:flex;gap:6px;flex:0 0 auto}
    .dk-hdr-btn{width:31px;height:31px;border-radius:8px;border:1px solid #3a2024;background:#1a1012;color:#e8d9d9;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;-webkit-tap-highlight-color:transparent}
    .dk-hdr-btn:active{opacity:0.8}
    #dk-settings-back{position:fixed;top:10px;left:10px;z-index:9999;background:#7A1A1E;color:#fff;border:none;border-radius:9px;padding:9px 14px;font-weight:800;font-size:13px;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,0.5)}
    /* In dark-mode settings: no door back to the normal game — only "Back to Off the Books". */
    body.dk-settings-open header, body.dk-settings-open nav.bottom-nav, body.dk-settings-open #settings-danger-zone{display:none !important}
    body.dk-settings-open main{padding-top:54px}
    .dk-day-title{font-size:16px;font-weight:800;color:#fff;text-align:center;margin-bottom:12px}
    .dk-day-money{display:flex;gap:10px;margin-bottom:13px}
    .dk-day-money>div{flex:1;background:#1a1012;border:1px solid #3a2024;border-radius:9px;padding:9px;text-align:center}
    .dk-day-mlbl{font-size:10px;color:#9a8a8a;font-weight:700;text-transform:uppercase;letter-spacing:0.3px}
    .dk-day-mval{font-size:16px;font-weight:800;margin-top:2px}
    .dk-day-list{display:flex;flex-direction:column;gap:6px;margin-bottom:14px;max-height:48vh;overflow-y:auto;text-align:left}
    .dk-day-row{font-size:12.5px;line-height:1.45;color:#e8d9d9;background:#160a0c;border:1px solid #2a1518;border-left:3px solid #3a2024;border-radius:7px;padding:8px 10px}
    /* The descent — Fixer's pitch + contract + signature */
    .dk-descent-card{max-width:400px;width:100%;background:#160a0c;border:1px solid #C0392B;border-radius:14px;padding:20px 18px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.6)}
    .dk-descent-fixer{font-size:11px;font-weight:800;color:#C0392B;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
    .dk-descent-text{font-size:14px;line-height:1.6;color:#e8d9d9;text-align:left;margin-bottom:18px}
    .dk-contract-title{font-size:12px;font-weight:800;color:#C0392B;text-align:center;letter-spacing:0.5px;margin-bottom:12px}
    .dk-contract-body{max-height:38vh;overflow-y:auto;font-size:12.5px;line-height:1.5;color:#d8c4c4;text-align:left;background:#120709;border:1px solid #2a1518;border-radius:8px;padding:12px 13px;margin-bottom:14px}
    .dk-contract-body p{margin:0 0 9px}.dk-contract-body p:last-child{margin:0}
    .dk-sig-line{display:flex;align-items:flex-end;gap:8px;position:relative;min-height:50px;margin-bottom:14px}
    .dk-sig-x{color:#9a8a8a;font-size:20px;line-height:44px}
    .dk-sig-slot{flex:1;border-bottom:1.5px solid #6a5a5a;min-height:46px;display:flex;align-items:flex-end;overflow:hidden}
    .dk-sig{font-family:'Great Vibes',cursive;font-size:42px;line-height:1.05;color:#E0533D;white-space:nowrap;padding:0 0 2px 6px}
    .dk-sig.writing{clip-path:inset(0 100% 0 0);animation:dkwrite 1.5s ease-out forwards}
    @keyframes dkwrite{to{clip-path:inset(0 0 0 0)}}
    .dk-seal{position:absolute;right:4px;bottom:2px;width:56px;height:56px;border-radius:50%;background:#7A1A1E;border:2px solid #C0392B;color:#ffd9d0;font-size:9px;font-weight:900;letter-spacing:0.5px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.1;opacity:0;transform:scale(2.4) rotate(-12deg)}
    .dk-seal.show{animation:dkstamp 0.5s ease-out forwards}
    @keyframes dkstamp{0%{transform:scale(2.4) rotate(-12deg);opacity:0}55%{transform:scale(0.82) rotate(-12deg);opacity:1}100%{transform:scale(1) rotate(-12deg);opacity:0.96}}
    /* Cook-it-yourself minigame */
    .dkck-ov{position:fixed;inset:0;z-index:9450;background:#0c0608;display:flex;flex-direction:column;color:#e8d9d9;-webkit-user-select:none;user-select:none}
    .dkck-top{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #2a1518;background:#160a0c;font-size:15px;font-weight:800}
    .dkck-prog{font-size:11px;color:#9a8a8a;letter-spacing:.5px;text-transform:uppercase}
    .dkck-stage{position:relative;flex:1;padding:14px;overflow:hidden}
    .dkck-foot{padding:12px 16px;border-top:1px solid #2a1518;background:#0c0608}
    .dkck-instr{font-size:12.5px;color:#cbb6b6;line-height:1.45;margin-bottom:9px;min-height:34px}
    .dkck-title{font-weight:800;font-size:15px;text-align:center;color:#fff;margin:0 0 10px}
    .dkck-bar{position:absolute;left:14px;right:14px;bottom:14px;height:9px;background:#1a1012;border-radius:5px;overflow:hidden}
    .dkck-bar>i{display:block;height:100%;width:0;background:#C0392B}
    .dkck-beaker{position:absolute;left:50%;transform:translateX(-50%);width:96px;border:3px solid #6a6a72;border-top:none;border-radius:0 0 18px 18px;overflow:hidden;background:#10141a}
    .dkck-bk-fill{position:absolute;left:0;right:0;bottom:0;height:0;transition:height .2s ease}
    .dkck-res-e{font-size:56px;text-align:center;line-height:1}
    .dkck-res-y{font-size:30px;font-weight:800;text-align:center;color:#4CAF50;margin-top:6px}
    .dkck-res-l{text-align:center;font-size:13px;margin-top:2px;text-transform:uppercase;letter-spacing:.5px}
    `;
  },
};

// ════════════════════════════════════════════════════════════════════════════
//  COOK — the hands-on "cook it yourself" minigame. A themed multi-step game per
//  drug; your score sets the yield. Launched from a vacant house. On finish it
//  commits to /dark/self_cook (consumes a supply → product to your stash).
// ════════════════════════════════════════════════════════════════════════════
const COOK = {
  GRACE: 2000, BLUE: '#5b8fd6',
  ACCENT: { reggie: '#5fae3a', beans: '#7da9e8', soft: '#8fd3e0', hard: '#d39a5a', glass: '#8fd3e0', tar: '#9c6b3f' },
  botchDrug: { hard: 1, glass: 1, tar: 1 },
  STEPS: {
    reggie: [ {t:'hold',label:'Tend the grow',sub:'Hold to water — keep the dial in the green. First 2s is a warm-up.',dur:7800,bandHW:.16,drift:.06},
              {t:'trim',label:'Trim the buds',sub:'Pick every bud off the plant.',count:6} ],
    beans:  [ {t:'pour',label:'Measure the binder',sub:'Hold to pour — release at the line.',style:'beaker',col:'#e8eef7',target:.62,tol:.26},
              {t:'mash',label:'Pack the press',sub:'Tap fast to pack the molds.',icon:'💊',col:'#cdd8ea',dur:4000},
              {t:'stopbar',label:'Stamp the pills',sub:'Tap STAMP in the green for each mold.',hits:3,zoneHW:.14,speed:1.5,verb:'STAMP'} ],
    soft:   [ {t:'stopbar',label:'Cut ratio',sub:'Stop the dial on the ideal cut.',hits:1,zoneHW:.13,speed:1.3,verb:'STOP'},
              {t:'chop',label:'Chop it fine',sub:'Drag the razor back and forth — chop it all down.',need:4400,dur:11000},
              {t:'pour',label:'Bag it',sub:'Pour powder into the baggie — stop at the line.',style:'bag',col:'#eef4f7',target:.7,tol:.22} ],
    hard:   [ {t:'seq',label:'Mix the wash',sub:'Watch, then repeat — each correct pour fills the beaker. One slip is OK.',len:3,col:'#cf9a5c',pads:[{e:'🧂',c:'#cfcfcf'},{e:'❄️',c:'#8fd3e0'},{e:'💧',c:'#7da9e8'}]},
              {t:'hold',label:'Boil it down',sub:'Tighter band — your dial is twitchy. 2s warm-up first.',dur:7400,bandHW:.115,drift:.13},
              {t:'mash',label:'Whip & crash',sub:'Mash until the wash crashes into rock.',icon:'🪨',col:'#c98a4e',dur:3800} ],
    glass:  [ {t:'seq',label:'Combine reagents',sub:'Longer order — each correct add fills the flask. One slip is OK.',len:5,col:'#8fd3e0',pads:[{e:'⚗️',c:'#8fd3e0'},{e:'🧪',c:'#7da9e8'},{e:'🧂',c:'#cfcfcf'},{e:'🔥',c:'#E0533D'}]},
              {t:'hold',label:'Hold the reaction',sub:'Twitchy dial, red zone = blows. 2s warm-up first.',dur:7600,bandHW:.11,drift:.16,danger:.9},
              {t:'stopbar',label:'Crystallize',sub:'Tap HARVEST at the peak — two tries, the best counts.',tries:2,zoneHW:.11,speed:1.7,verb:'HARVEST'},
              {t:'smash',label:'Break the tray',sub:'Smash the slab of glass into shards!',need:11,dur:7500} ],
    tar:    [ {t:'pour',label:'Dissolve',sub:'Exact solvent ratio — release at the line.',style:'beaker',col:'#7a5230',target:.5,tol:.18},
              {t:'chop',label:'Filter it',sub:'Drag to strain it through the filters — keep going.',need:3900,dur:10000,filter:true},
              {t:'hold',label:'Boil down',sub:'Longest, tightest band, twitchy dial. 2s warm-up first.',dur:9200,bandHW:.09,drift:.2},
              {t:'mash',label:'Pull the tar',sub:'Mash to fold and pull it to consistency.',icon:'🛢️',col:'#5e3d22',dur:4200} ] },
  loop: null, timers: [], winUp: null, prop: null, drug: null, sIdx: 0, scores: [], steps: [],
  clamp(v, a, b) { return Math.max(a, Math.min(b, v)); },
  stop() { if (this.loop) cancelAnimationFrame(this.loop); this.loop = null; this.timers.forEach(clearTimeout); this.timers = []; if (this.winUp) { window.removeEventListener('pointerup', this.winUp); this.winUp = null; } if (this.stage) { this.stage.onpointerdown = null; this.stage.onpointermove = null; this.stage.onpointerup = null; } },
  tlater(f, t) { var id = setTimeout(f, t); this.timers.push(id); return id; },
  btn(txt, fn, sec) { var b = document.createElement('button'); b.className = 'dk-evt-choice'; if (sec) b.style.background = '#3a2024'; b.textContent = txt; b.onpointerdown = function(e){e.preventDefault();}; b.onclick = fn; return b; },
  progbar(color) { var bar = document.createElement('div'); bar.className = 'dkck-bar'; bar.innerHTML = '<i></i>'; if (color) bar.firstChild.style.background = color; this.stage.appendChild(bar); return bar.firstChild; },
  acc() { return this.ACCENT[this.drug] || '#C0392B'; },
  open(propId, drug) {
    this.prop = propId; this.drug = drug; this.sIdx = 0; this.scores = []; this.steps = this.STEPS[drug] || [];
    var el = document.getElementById('dk-cook'); if (!el) { el = document.createElement('div'); el.id = 'dk-cook'; document.body.appendChild(el); }
    el.className = 'dkck-ov';
    var dd = DARK.DRUGS.find(function(x){return x.key===drug;}) || {name:drug,icon:'🧪'};
    el.innerHTML = '<div class="dkck-top"><span>'+dd.icon+' Cook '+dd.name+'</span><span class="dkck-prog" id="dkckP"></span></div><div class="dkck-stage" id="dkckS"></div><div class="dkck-foot"><div class="dkck-instr" id="dkckI"></div><div id="dkckC"></div></div>';
    this.stage = document.getElementById('dkckS'); this.instr = document.getElementById('dkckI'); this.ctrl = document.getElementById('dkckC'); this.prog = document.getElementById('dkckP');
    this.next();
  },
  syncMain() { try { refreshState().then(function(){ DARK.rerender(); }).catch(function(){}); } catch (e) {} },
  closeOverlay() { this.stop(); var el = document.getElementById('dk-cook'); if (el) el.remove(); this.syncMain(); },
  next() {
    this.stop();
    if (this.sIdx >= this.steps.length) return this.finish(false);
    var st = this.steps[this.sIdx];
    this.prog.textContent = 'Step ' + (this.sIdx + 1) + ' / ' + this.steps.length;
    this.instr.innerHTML = '<b style="color:#fff">' + st.label + '</b> — ' + st.sub;
    this.ctrl.innerHTML = '';
    this[st.t](st, function(score) {
      COOK.scores.push(score);
      if (COOK.botchDrug[COOK.drug] && score <= 0.02) return COOK.finish(true);
      COOK.sIdx++; COOK.tlater(function(){ COOK.next(); }, 360);
    });
  },
  async finish(botched) {
    this.stop();
    var avg = botched ? 0 : this.scores.reduce(function(a,b){return a+b;}, 0) / this.scores.length;
    this.stage.innerHTML = '<div class="dkck-title">Cooking…</div>'; this.ctrl.innerHTML = '';
    var r;
    try { r = await api('/dark/self_cook', 'POST', { prop_id: this.prop, drug: this.drug, score: avg, botched: botched }); }
    catch (e) { r = { error: 'Something went wrong — try again.' }; }
    if (!r || r.error) { toast((r && r.error) || 'Cook failed.', 'error'); this.closeOverlay(); return; }
    if (r.stash) state.dark.stash = r.stash;          // patch locally so the result + UI are right…
    if (typeof r.cash === 'number') state.cash = r.cash;   // …without depending on a full state refresh
    if (typeof r.cook_day !== 'undefined') state.dark.cook_day = r.cook_day;
    if (typeof r.cooks_today === 'number') state.dark.cooks_today = r.cooks_today;
    this.showResult(r, avg);
  },
  showResult(r, avg) {
    var dd = DARK.DRUGS.find(function(x){return x.key===COOK.drug;}) || {icon:'🧪',name:COOK.drug};
    if (r.botched || (r.yield || 0) <= 0) {
      this.stage.innerHTML = '<div class="dkck-title">It all went wrong</div><div class="dkck-res-e">🔥</div><div class="dkck-res-l" style="color:#E0533D">Batch botched — supply wasted</div>';
    } else {
      var lbl, col; if (avg>=.9){lbl='Perfect cook';col='#FFC83D';}else if(avg>=.72){lbl='Clean batch';col='#4CAF50';}else if(avg>=.5){lbl='Decent';col='#9fd8a0';}else if(avg>=.28){lbl='Sloppy';col='#FF8A3D';}else{lbl='Barely usable';col='#E0533D';}
      this.stage.innerHTML = '<div class="dkck-title">Batch done</div><div class="dkck-res-e">'+dd.icon+'</div><div class="dkck-res-y">+'+r.yield+' '+dd.name+'</div><div class="dkck-res-l" style="color:'+col+'">'+lbl+'</div>';
    }
    this.instr.textContent = "Straight to your stash — no crew, no cut. That's your hand-cook for today.";
    this.ctrl.innerHTML = '';
    this.ctrl.appendChild(this.btn('Done', function(){ COOK.closeOverlay(); }));
  },
  hold(st, done) {
    var C = this.clamp, A = this.acc();
    this.stage.innerHTML = '<div class="dkck-title" id="ckhT">Warming up…</div><div id="ckhTr" style="position:absolute;left:50%;top:60px;transform:translateX(-50%);width:80px;height:282px;background:#160a0c;border:1px solid #3a2024;border-radius:12px;overflow:hidden;cursor:pointer">'+(st.danger?'<div style="position:absolute;left:0;right:0;top:0;height:'+(100-st.danger*100)+'%;background:rgba(224,83,61,.16);border-bottom:1px dashed #E0533D"></div>':'')+'<div id="ckhB" style="position:absolute;left:0;right:0"></div><div id="ckhM" style="position:absolute;left:6px;right:6px;height:16px;border-radius:6px"></div></div>';
    var tr=document.getElementById('ckhTr'),band=document.getElementById('ckhB'),mark=document.getElementById('ckhM'),T=document.getElementById('ckhT');
    var H=282,pos=.12,vel=0,holding=false,t0=performance.now(),inb=0,last=t0,win=st.dur-this.GRACE,GR=this.GRACE,BL=this.BLUE;
    this.stage.onpointerdown=function(e){e.preventDefault();holding=true;}; this.winUp=function(){holding=false;}; window.addEventListener('pointerup',this.winUp);
    var fill=this.progbar();
    (function run(now){var dt=Math.min(40,now-last)/1000;last=now;var el=now-t0,grace=el<GR;
      vel+=(holding?5.2:-4.2)*dt;vel*=.97;vel=C(vel,-2.6,2.6);pos+=vel*dt;if(pos<0){pos=0;vel=-vel*.25;}if(pos>1){pos=1;vel=-vel*.25;}
      var bc=.5+Math.sin(el/950)*st.drift,lo=bc-st.bandHW,hi=bc+st.bandHW;band.style.bottom=(lo*H)+'px';band.style.height=((hi-lo)*H)+'px';mark.style.bottom=(pos*H-8)+'px';var ok=pos>=lo&&pos<=hi;
      if(grace){band.style.background='rgba(91,143,214,.30)';band.style.borderTop='2px solid '+BL;band.style.borderBottom='2px solid '+BL;mark.style.background=BL;}
      else{band.style.background='rgba(76,175,80,.32)';band.style.borderTop='2px solid #4CAF50';band.style.borderBottom='2px solid #4CAF50';mark.style.background=ok?'#4CAF50':A;if(ok)inb+=dt*1000;}
      T.textContent=grace?('Warm-up… '+Math.ceil((GR-el)/1000)):'Keep it steady';
      if(st.danger&&!grace&&pos>=st.danger){return done(0);}
      fill.style.width=Math.min(100,el/st.dur*100)+'%';fill.style.background=grace?BL:A;
      if(el>=st.dur){return done(C(inb/(win*.55),0,1));}COOK.loop=requestAnimationFrame(run);})(t0);
  },
  trim(st, done) {
    var A=this.acc();
    var leaf='M0,0 C -7,-22 -5,-46 0,-58 C 5,-46 7,-22 0,0 Z';
    function fan(cx,cy,s){var a=[-58,-30,0,30,58],o='';for(var i=0;i<a.length;i++){o+='<path d="'+leaf+'" transform="translate('+cx+','+cy+') rotate('+a[i]+') scale('+s+')" fill="#3f6b27" stroke="#2c4d1a" stroke-width="1.5"/>';}return o;}
    var buds=[[100,104],[78,150],[122,150],[80,206],[120,206],[100,168]].slice(0,st.count),bsvg='';
    for(var i=0;i<buds.length;i++){bsvg+='<g class="ckbud" style="cursor:pointer"><circle cx="'+buds[i][0]+'" cy="'+buds[i][1]+'" r="13" fill="#79a83f" stroke="#a6cf6c" stroke-width="2"/><circle cx="'+(buds[i][0]-4)+'" cy="'+(buds[i][1]-3)+'" r="2" fill="#e8f5d0"/><circle cx="'+(buds[i][0]+4)+'" cy="'+(buds[i][1]+2)+'" r="1.8" fill="#e8f5d0"/></g>';}
    this.stage.innerHTML='<div class="dkck-title" id="cktL">0 / '+st.count+' picked</div><svg viewBox="0 0 200 300" width="100%" height="320" style="display:block"><polygon points="72,300 128,300 120,256 80,256" fill="#6b4427"/><rect x="78" y="252" width="44" height="8" rx="3" fill="#7d5230"/><rect x="97" y="120" width="6" height="140" fill="#46662a"/>'+fan(100,236,1.5)+fan(82,150,1.2)+fan(118,150,1.2)+fan(100,118,1.0)+bsvg+'</svg>';
    var got=0,total=buds.length,t0=performance.now();
    this.stage.querySelectorAll('.ckbud').forEach(function(g){g.onpointerdown=function(e){e.preventDefault();if(g.dataset.done)return;g.dataset.done=1;g.style.transition='transform .18s,opacity .18s';g.style.transformOrigin='center';g.style.transform='scale(0)';g.style.opacity='0';got++;document.getElementById('cktL').textContent=got+' / '+total+' picked';if(got>=total){COOK.stop();COOK.tlater(function(){done(1);},250);}};});
    var fill=this.progbar(A);
    (function run(now){var el=now-t0;fill.style.width=Math.min(100,el/9000*100)+'%';if(el>=9000){COOK.stop();return done(got/total);}COOK.loop=requestAnimationFrame(run);})(t0);
  },
  pour(st, done) {
    var C=this.clamp,bag=st.style==='bag';
    this.stage.innerHTML='<div class="dkck-title">'+(bag?'Pour into the baggie':'Pour to the line')+'</div><div id="ckpC" style="position:absolute;left:50%;top:72px;transform:translateX(-50%);width:'+(bag?'120px':'108px')+';height:264px;background:#10141a;border:'+(bag?'2px solid #c9d2dc':'3px solid #6a6a72')+';border-top:'+(bag?'2px solid #c9d2dc':'none')+';border-radius:'+(bag?'4px 4px 14px 14px':'0 0 16px 16px')+';overflow:hidden;cursor:pointer">'+(bag?'<div style="position:absolute;top:0;left:0;right:0;height:10px;background:#c9d2dc"></div>':'')+'<div id="ckpF" style="position:absolute;left:0;right:0;bottom:0;height:0;background:'+st.col+'"></div><div style="position:absolute;left:0;right:0;height:3px;background:#FFC83D;bottom:'+(st.target*264)+'px"></div><div style="position:absolute;right:5px;font-size:9px;color:#FFC83D;bottom:'+(st.target*264+4)+'px">LINE</div></div><div style="position:absolute;left:0;right:0;bottom:46px;text-align:center;font-size:11px;color:#9a8a8a">hold to pour · release to stop</div>';
    var Cn=document.getElementById('ckpC'),fillEl=document.getElementById('ckpF'),lvl=0,holding=false,last=performance.now(),donev=false,started=false;
    this.stage.onpointerdown=function(e){e.preventDefault();holding=true;started=true;};
    this.winUp=function(){if(donev||!started)return;holding=false;donev=true;COOK.stop();var dd=Math.abs(lvl-st.target);done(C(1-dd/st.tol,0,1));};window.addEventListener('pointerup',this.winUp);
    (function run(now){var dt=(now-last)/1000;last=now;if(holding)lvl=C(lvl+.4*dt,0,1);fillEl.style.height=(lvl*264)+'px';if(!donev)COOK.loop=requestAnimationFrame(run);})(last);
  },
  mash(st, done) {
    var C=this.clamp,A=this.acc();
    this.stage.innerHTML='<div class="dkck-title" id="ckmL">Tap! '+(st.dur/1000).toFixed(0)+'s</div><div id="ckmP" style="position:absolute;left:50%;top:62px;transform:translateX(-50%);width:150px;height:230px;border:3px solid #6a6a72;border-top:none;border-radius:0 0 22px 22px;overflow:hidden;background:#10141a;cursor:pointer"><div id="ckmF" style="position:absolute;left:0;right:0;bottom:0;height:0;background:'+st.col+'"></div><div id="ckmI" style="position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font-size:60px;pointer-events:none">'+st.icon+'</div><div id="ckmR" style="position:absolute;left:50%;top:50%;width:10px;height:10px;border:3px solid #fff;border-radius:50%;transform:translate(-50%,-50%) scale(0);opacity:0;pointer-events:none"></div></div>';
    var pad=document.getElementById('ckmP'),fillEl=document.getElementById('ckmF'),ico=document.getElementById('ckmI'),ring=document.getElementById('ckmR'),L=document.getElementById('ckmL'),fillv=0,t0=performance.now(),last=t0,fb=this.progbar(A);
    this.stage.onpointerdown=function(e){e.preventDefault();fillv=C(fillv+.075,0,1);ico.style.transform='translateY(-50%) scale(1.18)';ring.style.transition='none';ring.style.transform='translate(-50%,-50%) scale(0)';ring.style.opacity='.9';COOK.tlater(function(){ring.style.transition='transform .3s,opacity .3s';ring.style.transform='translate(-50%,-50%) scale(7)';ring.style.opacity='0';},10);COOK.tlater(function(){ico.style.transform='translateY(-50%) scale(1)';},70);fb.style.width=(fillv*100)+'%';fillEl.style.height=(fillv*230)+'px';};
    (function run(now){var dt=(now-last)/1000;last=now;fillv=C(fillv-.17*dt,0,1);fb.style.width=(fillv*100)+'%';fillEl.style.height=(fillv*230)+'px';var rem=(st.dur-(now-t0))/1000;L.textContent='Tap! '+Math.max(0,rem).toFixed(1)+'s';if(now-t0>=st.dur){COOK.stop();return done(C(fillv,0,1));}COOK.loop=requestAnimationFrame(run);})(t0);
  },
  stopbar(st, done) {
    var C=this.clamp,isTries=!!st.tries,total=st.tries||st.hits||1,left=total,acc=[],verb=st.verb||'STOP';
    function head(){return isTries?('Try '+(total-left+1)+' of '+total):(st.hits>1?('Stamp '+st.hits):'Line it up');}
    this.stage.innerHTML='<div class="dkck-title" id="cksL">'+head()+'</div><div style="position:absolute;left:14px;right:14px;top:160px;height:36px;background:#160a0c;border:1px solid #3a2024;border-radius:9px;overflow:hidden"><div id="cksZ" style="position:absolute;top:0;bottom:0;background:rgba(76,175,80,.32);border-left:2px solid #4CAF50;border-right:2px solid #4CAF50"></div><div id="cksM" style="position:absolute;top:-3px;bottom:-3px;width:4px;background:#FFC83D"></div></div><div id="cksB" style="position:absolute;left:0;right:0;top:212px;text-align:center;font-size:11px;color:#9a8a8a"></div>';
    var W=332,zone=document.getElementById('cksZ'),mark=document.getElementById('cksM'),L=document.getElementById('cksL'),B=document.getElementById('cksB');
    var zc=.3+Math.random()*.4;zone.style.left=((zc-st.zoneHW)*W)+'px';zone.style.width=(st.zoneHW*2*W)+'px';var t0=performance.now();
    function doStop(){var p=parseFloat(mark.dataset.p||'0');var dd=Math.abs(p-zc);var s=C(1-dd/(st.zoneHW*1.8),0,1);acc.push(s);left--;if(left<=0){COOK.stop();return done(isTries?Math.max.apply(null,acc):acc.reduce(function(a,b){return a+b;},0)/acc.length);}if(isTries){B.textContent='Best so far: '+Math.round(Math.max.apply(null,acc)*100)+'%';L.textContent=head();}else{L.textContent='Stamp '+left+' to go';}zc=.18+Math.random()*.64;zone.style.left=((zc-st.zoneHW)*W)+'px';}
    this.ctrl.appendChild(this.btn(verb,doStop));
    this.stage.onpointerdown=function(e){e.preventDefault();doStop();};
    (function run(now){var el=(now-t0)/1000*st.speed;var p=(Math.sin(el*Math.PI)+1)/2;mark.dataset.p=p;mark.style.left=(p*W-2)+'px';COOK.loop=requestAnimationFrame(run);})(t0);
  },
  chop(st, done) {
    var C=this.clamp,A=this.acc();
    this.stage.innerHTML='<div class="dkck-title">'+(st.filter?'Strain it through':'Chop it fine')+'</div><div id="ckcS" style="position:absolute;left:14px;right:14px;top:54px;bottom:30px;background:'+(st.filter?'#140d0a':'#15171c')+';border:1px solid #3a2024;border-radius:12px;overflow:hidden;cursor:crosshair"><svg id="ckcSvg" width="100%" height="100%" style="position:absolute;inset:0"></svg><div id="ckcT" style="position:absolute;font-size:30px;transform:translate(-50%,-60%);pointer-events:none">'+(st.filter?'🧽':'🔪')+'</div></div>';
    var S=document.getElementById('ckcS'),svg=document.getElementById('ckcSvg'),tool=document.getElementById('ckcT'),col=st.filter?'#7a5230':'#dfeaf0';
    var dist=0,down=false,px=0,py=0,t0=performance.now(),lastDraw=0,fb=this.progbar(A);
    function R(){return S.getBoundingClientRect();}
    S.onpointerdown=function(e){e.preventDefault();down=true;var r=R();px=e.clientX-r.left;py=e.clientY-r.top;tool.style.left=px+'px';tool.style.top=py+'px';};
    S.onpointermove=function(e){var r=R();var x=e.clientX-r.left,y=e.clientY-r.top;tool.style.left=x+'px';tool.style.top=y+'px';if(!down)return;var dx=x-px,dy=y-py;dist+=Math.sqrt(dx*dx+dy*dy);if(dist-lastDraw>16){lastDraw=dist;var ln=document.createElementNS('http://www.w3.org/2000/svg','line');ln.setAttribute('x1',px);ln.setAttribute('y1',py);ln.setAttribute('x2',x);ln.setAttribute('y2',y);ln.setAttribute('stroke',col);ln.setAttribute('stroke-width',st.filter?'3':'2.5');ln.setAttribute('stroke-linecap','round');ln.setAttribute('opacity','.8');svg.appendChild(ln);}px=x;py=y;fb.style.width=Math.min(100,dist/st.need*100)+'%';if(dist>=st.need){down=false;COOK.stop();return done(1);}};
    this.winUp=function(){down=false;};window.addEventListener('pointerup',this.winUp);
    (function run(now){if(now-t0>=st.dur){COOK.stop();return done(C(dist/st.need,0,1));}COOK.loop=requestAnimationFrame(run);})(t0);
  },
  seq(st, done) {
    var order=[];for(var i=0;i<st.len;i++)order.push(Math.floor(Math.random()*st.pads.length));
    var n=st.pads.length,cols=Math.min(n,4);
    this.stage.innerHTML='<div class="dkck-title" id="ckqL">Watch the order…</div><div class="dkck-beaker" id="ckqBk" style="top:56px;height:150px"><div class="dkck-bk-fill" id="ckqF" style="background:'+st.col+'"></div></div><div id="ckqP" style="position:absolute;left:14px;right:14px;bottom:36px;display:grid;grid-template-columns:repeat('+cols+',1fr);gap:8px"></div>';
    var fillEl=document.getElementById('ckqF'),padWrap=document.getElementById('ckqP'),L=document.getElementById('ckqL'),pos=[];
    for(var j=0;j<n;j++){var p=document.createElement('div');p.style.cssText='height:62px;border-radius:12px;border:2px solid '+st.pads[j].c+';background:#160a0c;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer';p.dataset.i=j;p.textContent=st.pads[j].e;padWrap.appendChild(p);pos.push(p);}
    function flash(i,on,col){pos[i].style.background=on?(col||st.pads[i].c):'#160a0c';pos[i].style.transform=on?'scale(1.07)':'';}
    var k=0;function play(){if(k>=order.length){COOK.tlater(input,250);return;}flash(order[k],true);COOK.tlater(function(){flash(order[k],false);k++;COOK.tlater(play,210);},450);}
    var got=0,mistakes=0;function setFill(){fillEl.style.height=(got/order.length*100)+'%';}
    function input(){L.textContent='Repeat it';pos.forEach(function(p){p.onpointerdown=function(e){e.preventDefault();var i=+p.dataset.i;if(i===order[got]){flash(i,true);COOK.tlater(function(){flash(i,false);},150);got++;setFill();if(got>=order.length){COOK.stop();COOK.tlater(function(){done(mistakes>0?.7:1);},250);}}else{mistakes++;flash(i,true,'#E0533D');COOK.tlater(function(){flash(i,false);},220);if(mistakes>=2){COOK.stop();return done(0);}L.textContent='Slip! One more mistake fails it.';}};});}
    COOK.tlater(play,500);
  },
  smash(st, done) {
    var C=this.clamp;
    this.stage.innerHTML='<div class="dkck-title" id="ckxL">Smash it! 0 / '+st.need+'</div><div id="ckxW" style="position:absolute;left:50%;top:80px;transform:translateX(-50%);width:250px;height:188px;background:#23252b;border:5px solid #3a3d45;border-radius:8px;cursor:pointer"><div style="position:absolute;top:9px;left:9px;width:222px;height:160px"><svg id="ckxSvg" width="222" height="160" viewBox="0 0 222 160" style="display:block"><rect x="0" y="0" width="222" height="160" rx="4" fill="#bfe6f0"/><polygon points="0,0 92,0 46,62 0,78" fill="#d9f2f8"/><polygon points="222,0 222,72 150,36 120,0" fill="#a9d8e6"/><polygon points="0,160 72,160 30,104 0,112" fill="#a9d8e6"/><polygon points="222,160 222,92 156,128 128,160" fill="#d2eef5"/><polygon points="92,56 150,52 140,112 86,108" fill="#cfeaf2"/><g id="ckxC"></g></svg></div></div>';
    var wrap=document.getElementById('ckxW'),svg=document.getElementById('ckxSvg'),cracks=document.getElementById('ckxC'),L=document.getElementById('ckxL'),hits=0,t0=performance.now(),donev=false,fb=this.progbar('#8fd3e0');
    function spider(x,y){for(var a=0;a<5;a++){var ang=Math.random()*6.28,len=22+Math.random()*42;var ln=document.createElementNS('http://www.w3.org/2000/svg','line');ln.setAttribute('x1',x);ln.setAttribute('y1',y);ln.setAttribute('x2',x+Math.cos(ang)*len);ln.setAttribute('y2',y+Math.sin(ang)*len);ln.setAttribute('stroke','#ffffff');ln.setAttribute('stroke-width','1.5');ln.setAttribute('opacity','.85');cracks.appendChild(ln);}}
    this.stage.onpointerdown=function(e){e.preventDefault();if(donev)return;hits++;var r=svg.getBoundingClientRect();var x=C(e.clientX-r.left,8,214),y=C(e.clientY-r.top,8,152);spider(x,y);wrap.style.transform='translateX(-50%) translateY(2px)';COOK.tlater(function(){wrap.style.transform='translateX(-50%)';},60);L.textContent='Smash it! '+Math.min(hits,st.need)+' / '+st.need;fb.style.width=Math.min(100,hits/st.need*100)+'%';if(hits>=st.need){donev=true;COOK.stop();shatter();}};
    function shatter(){L.textContent='Shattered!';svg.querySelectorAll('polygon,rect').forEach(function(el){el.style.transition='transform .6s ease-in, opacity .6s';el.style.transform='translate('+((Math.random()-.5)*70)+'px,'+(80+Math.random()*70)+'px) rotate('+((Math.random()-.5)*70)+'deg)';el.style.opacity='0';});COOK.tlater(function(){done(1);},650);}
    (function run(now){if(now-t0>=st.dur){if(!donev){donev=true;COOK.stop();return done(C(hits/st.need,0,1));}return;}COOK.loop=requestAnimationFrame(run);})(t0);
  }
};

// ── Top-level mode router ───────────────────────────────────────────────────
// ONE switch decides the whole subsystem. Legit code is never entered in dark mode.
function applyGameMode() {
  const dark = !!(state && state.mode === 'dark');
  let root = document.getElementById('dark-root');
  if (!root) {   // self-create so we never depend on the template markup
    root = document.createElement('div');
    root.id = 'dark-root';
    root.style.display = 'none';
    document.body.appendChild(root);
  }
  document.body.classList.toggle('dark-mode', dark);
  const _legacyBtn = document.getElementById('dark-dev-btn'); if (_legacyBtn) _legacyBtn.remove();   // moon button retired — entry is the Level-11 dilemma only
  if (dark) {
    if (!document.getElementById('dk-style')) {
      const st = document.createElement('style');
      st.id = 'dk-style';
      st.textContent = DARK.css();
      document.head.appendChild(st);
    }
    if (DARK._inSettings) { root.style.display = 'none'; return; }   // viewing the real settings page — keep the overlay tucked away (survives refreshState)
    root.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;height:100vh;height:100dvh;z-index:9000;background:#0c0608;display:flex;justify-content:center';
    root.innerHTML = DARK.render();
  } else {
    root.style.display = 'none';
    root.innerHTML = '';
  }
}
