// ════════════════════════════════════════════════════════════════════════════
//  DARK MODE — "Off the Books"
//  A self-contained crime-empire mode. It branches at the TOP (state.mode === 'dark')
//  and owns its ENTIRE UI in this file, so the legit game's code is never touched
//  and can't break from anything in here.
//  Carry-over from legit: clean cash, owned businesses, owned homes + tenants.
// ════════════════════════════════════════════════════════════════════════════

const DARK = {
  async enter() {
    const r = await api('/dark/enter', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState();
    toast("You cross the line. There's no map back here. 😈", 'warning');
  },
  async wake() {
    const r = await api('/dark/wake', 'POST');
    if (r.error) { toast(r.error, 'error'); return; }
    await refreshState();
    toast('You jolt awake at your desk. …Just a dream. 😮‍💨', 'success');
  },

  // What carried over — read straight from the shared state (no duplication).
  carryover() {
    const biz = [];
    if (state.laundromat && state.laundromat.owned)   biz.push('Laundromat');
    if (state.arcade && state.arcade.unlocked)         biz.push('Arcade');
    if (state.pole_studio && state.pole_studio.owned)  biz.push('Studio');
    if (state.car_wash && state.car_wash.owned)        biz.push('Car Wash');
    const vm = (state.vending_machines || []).length;
    if (vm) biz.push(vm + ' Vending');
    const homes   = (state.properties || []).length;
    const tenants = (state.properties || []).filter(p => p.tenant).length;
    return { biz, homes, tenants };
  },

  stat(label, val, col) {
    return `<div style="background:#140a0c;border:1px solid #3a2024;border-radius:10px;padding:11px 12px">
      <div style="font-size:10px;color:#9a8a8a">${label}</div>
      <div style="font-weight:800;font-size:17px;color:${col}">${val}</div></div>`;
  },

  render() {
    const d  = state.dark || {};
    const co = this.carryover();
    return `
    <div style="min-height:100%;background:#0c0608;color:#e8d9d9;font-family:'Inter',sans-serif;padding:20px 16px 48px">
      <div style="text-align:center;margin-bottom:18px">
        <div style="font-family:'Rubik Dirt',cursive;font-size:27px;color:#C0392B;line-height:1.1">Off the Books</div>
        <div style="font-size:12px;color:#9a8a8a;margin-top:3px">Crime Rank ${d.rank || 1} · the empire you don't report</div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">
        ${this.stat('💵 Clean Cash',   fmt(state.cash || 0),          '#4CAF50')}
        ${this.stat('🧼 Dirty Money',  fmt(d.dirty_money || 0),       '#C0392B')}
        ${this.stat('🔥 Heat',         (d.heat || 0) + '%',           '#FF6D00')}
        ${this.stat('🏚️ Properties',   co.homes + (co.tenants ? ` · ${co.tenants} ten.` : ''), '#cbb6b6')}
      </div>

      <div style="border:1px solid #3a2024;border-radius:10px;padding:14px;margin-bottom:16px;background:#140a0c">
        <div style="font-size:11px;font-weight:700;color:#C0392B;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px">Carried Over</div>
        <div style="font-size:13px;color:#cbb6b6;line-height:1.5">Your money came back clean. You kept ${co.homes} ${co.homes === 1 ? 'property' : 'properties'}${co.tenants ? ` (and ${co.tenants} tenant${co.tenants === 1 ? '' : 's'})` : ''}${co.biz.length ? `, plus: ${co.biz.join(', ')}` : ''}.</div>
      </div>

      <div style="border:1px dashed #3a2024;border-radius:10px;padding:16px;margin-bottom:22px;text-align:center;color:#7a6a6a;font-size:13px;line-height:1.5">
        🚧 The empire gets built right here — the casino, the club, the labs, the corners. Coming next.
      </div>

      <button onclick="DARK.wake()" style="width:100%;background:none;border:1px solid #3a2024;color:#9a8a8a;padding:12px;border-radius:10px;font-size:13px;cursor:pointer">
        💤 "It was all a dream" — wake up at your desk <span style="opacity:0.7">(resets the dark side)</span>
      </button>
    </div>`;
  },
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
  if (dark) {
    root.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;width:100%;height:100vh;z-index:9000;overflow-y:auto;background:#0c0608';
    root.innerHTML = DARK.render();
    _darkDevBtn(false);
  } else {
    root.style.display = 'none';
    root.innerHTML = '';
    _darkDevBtn(true);   // temporary dev entry while the Level-11 dilemma is rebuilt
  }
}

// ── TEMP dev entry button ───────────────────────────────────────────────────
// The real entry will be the rebuilt Level-11 dilemma. This is dev-only for testing
// and must be removed before any push. (Nothing is pushed yet, so live players never
// see it.)
function _darkDevBtn(show) {
  let b = document.getElementById('dark-dev-btn');
  if (!show) { if (b) b.remove(); return; }
  if (b) return;
  b = document.createElement('button');
  b.id = 'dark-dev-btn';
  b.textContent = '🌙';
  b.title = 'Go Dark (dev only)';
  b.style.cssText = 'position:fixed;right:10px;bottom:84px;z-index:8000;width:42px;height:42px;border-radius:50%;border:none;background:#7A1A1E;color:#fff;font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.45)';
  b.onclick = () => DARK.enter();
  document.body.appendChild(b);
}
