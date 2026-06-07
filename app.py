from flask import Flask, render_template, jsonify, request, g
import json, os, random

app = Flask(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

STARTING_CASH = 5_000

LOAN_PRODUCTS = [
    {"key": "quick",    "name": "Quick Cash",    "icon": "💵", "min": 500,   "max": 5_000,   "apr": 0.24, "term_seasons": 2,  "desc": "Fast money, high interest."},
    {"key": "personal", "name": "Personal Loan", "icon": "🤝", "min": 3_000, "max": 25_000,  "apr": 0.15, "term_seasons": 4,  "desc": "Reasonable rates for mid-range needs."},
    {"key": "property", "name": "Property Loan", "icon": "🏦", "min": 15000, "max": 75_000,  "apr": 0.09, "term_seasons": 8,  "desc": "Low rates for real estate investment."},
    {"key": "business", "name": "Business Loan", "icon": "💼", "min": 50000, "max": 150_000, "apr": 0.07, "term_seasons": 12, "desc": "Best rates for serious investors."},
]

SAVINGS_TIERS = [
    {"min": 0,      "label": "Basic",    "monthly_rate": 0.001, "apr": 1.2},
    {"min": 1_000,  "label": "Standard", "monthly_rate": 0.003, "apr": 3.6},
    {"min": 10_000, "label": "Premium",  "monthly_rate": 0.005, "apr": 6.0},
    {"min": 50_000, "label": "Elite",    "monthly_rate": 0.008, "apr": 9.6},
]

PROPERTY_TYPES = ["Bungalow", "Ranch House", "Colonial", "Townhouse", "Condo", "Duplex"]
PROPERTY_ICONS = {
    "Bungalow": "🏡", "Ranch House": "🏘️", "Colonial": "🏛️",
    "Townhouse": "🏙️", "Condo": "🏢", "Duplex": "🏠"
}

NEIGHBORHOODS = {
    "Eastside":  {"price_mult": 0.70, "rent_mult": 0.75, "desc": "Up-and-coming, rough around the edges", "tier": "budget"},
    "Riverside": {"price_mult": 0.85, "rent_mult": 0.90, "desc": "Quiet and a bit isolated",              "tier": "budget"},
    "Midtown":   {"price_mult": 1.00, "rent_mult": 1.00, "desc": "Solid middle-class area",               "tier": "mid"},
    "Westwood":  {"price_mult": 1.40, "rent_mult": 1.35, "desc": "Desirable suburb, great schools",       "tier": "premium"},
    "Downtown":  {"price_mult": 1.60, "rent_mult": 1.55, "desc": "High-demand urban core",                "tier": "premium"},
}

DAYS_PER_SEASON = 28   # 4 seasons × 28 days = 112-day year

REPAIR_TYPES = [
    {"key": "plumbing",   "name": "Plumbing Leak",       "icon": "🔧", "base_cost": 400,  "cond_loss": 7,  "cond_fix": 9},
    {"key": "electrical", "name": "Electrical Issue",    "icon": "⚡", "base_cost": 700,  "cond_loss": 5,  "cond_fix": 7},
    {"key": "appliance",  "name": "Appliance Breakdown", "icon": "📦", "base_cost": 350,  "cond_loss": 5,  "cond_fix": 7},
    {"key": "roof_patch", "name": "Roof Patch Needed",   "icon": "🏚️", "base_cost": 900,  "cond_loss": 9,  "cond_fix": 11},
    {"key": "pest",       "name": "Pest Problem",        "icon": "🐛", "base_cost": 300,  "cond_loss": 7,  "cond_fix": 7},
    {"key": "hvac_fix",   "name": "HVAC Repair",         "icon": "🌡️", "base_cost": 600,  "cond_loss": 7,  "cond_fix": 9},
]

UPGRADES = {
    "paint":       {"name": "Interior Paint",   "icon": "🎨", "base_cost": 1500,  "value_add": 3000,  "cond_boost": 15, "energy_cost": 1},
    "landscaping": {"name": "Landscaping",       "icon": "🌿", "base_cost": 2000,  "value_add": 4500,  "cond_boost": 10, "energy_cost": 1},
    "flooring":    {"name": "New Flooring",      "icon": "🪵", "base_cost": 4000,  "value_add": 8000,  "cond_boost": 20, "energy_cost": 2},
    "windows":     {"name": "New Windows",       "icon": "🪟", "base_cost": 6000,  "value_add": 10000, "cond_boost": 12, "energy_cost": 2},
    "hvac":        {"name": "HVAC System",       "icon": "❄️", "base_cost": 7000,  "value_add": 11000, "cond_boost": 15, "energy_cost": 3},
    "bathrooms":   {"name": "Bathroom Remodel",  "icon": "🚿", "base_cost": 8000,  "value_add": 14000, "cond_boost": 20, "energy_cost": 3},
    "roof":        {"name": "Roof Replacement",  "icon": "🏠", "base_cost": 10000, "value_add": 15000, "cond_boost": 18, "energy_cost": 4},
    "kitchen":     {"name": "Kitchen Remodel",   "icon": "🍳", "base_cost": 12000, "value_add": 22000, "cond_boost": 25, "energy_cost": 4},
}

# Premium upgrades — permanent additions that raise market value & fair rent.
# Contractor-only (no DIY). Can only be installed once per property.
PREMIUM_UPGRADES = {
    "smarthome":    {"name": "Smart Home Package",   "icon": "📱", "cost":  5_500, "rent_bonus": 32,  "value_bonus":  7_000, "desc": "Security cameras, smart thermostat & lighting automation"},
    "ev_charger":   {"name": "EV Charging Station",  "icon": "⚡", "cost":  4_000, "rent_bonus": 20,  "value_bonus":  5_000, "desc": "Level 2 EV charger — big draw for modern renters"},
    "hot_tub":      {"name": "Hot Tub / Spa",        "icon": "🛁", "cost": 12_000, "rent_bonus": 60,  "value_bonus": 13_000, "desc": "Outdoor hot tub with privacy fencing"},
    "deck":         {"name": "Deck & Patio",         "icon": "🪵", "cost":  9_000, "rent_bonus": 45,  "value_bonus": 11_000, "desc": "Hardwood deck with built-in seating area"},
    "central_hvac": {"name": "Central A/C & Heat",   "icon": "🌡️", "cost": 13_000, "rent_bonus": 70,  "value_bonus": 15_000, "desc": "Full HVAC system — year-round climate control"},
    "garage":       {"name": "2-Car Garage",         "icon": "🚗", "cost": 16_000, "rent_bonus": 85,  "value_bonus": 20_000, "desc": "Attached 2-car garage with automatic door"},
    "solar":        {"name": "Solar Panel Array",    "icon": "☀️", "cost": 19_000, "rent_bonus": 65,  "value_bonus": 22_000, "desc": "Rooftop solar — lower bills, higher tenant appeal"},
    "basement":     {"name": "Finished Basement",    "icon": "🏗️", "cost": 22_000, "rent_bonus": 130, "value_bonus": 27_000, "desc": "Fully finished basement — extra living space"},
    "pool":         {"name": "Swimming Pool",        "icon": "🏊", "cost": 28_000, "rent_bonus": 175, "value_bonus": 32_000, "desc": "Inground pool with full landscaping package"},
    "adu":          {"name": "Guest House / ADU",    "icon": "🏡", "cost": 48_000, "rent_bonus": 325, "value_bonus": 55_000, "desc": "Detached accessory dwelling unit — major value add"},
}

def get_premium_bonuses(prop):
    """Return total weekly rent bonus and value bonus from installed premium upgrades."""
    installed = prop.get("premium_upgrades", [])
    rent_b  = sum(PREMIUM_UPGRADES[k]["rent_bonus"]  for k in installed if k in PREMIUM_UPGRADES)
    value_b = sum(PREMIUM_UPGRADES[k]["value_bonus"] for k in installed if k in PREMIUM_UPGRADES)
    return {"rent": rent_b, "value": value_b}

MAX_CONDITION    = 250   # condition is now out of 250 points
RENO_COOLDOWN    = 28    # days before a renovation can be done again
DAILY_ENERGY     = 10    # energy points restored each day; DIY renovations and side jobs consume energy

# Grade tiers: quality score 0-100 → letter grade → % change of MAX_CONDITION
TIER_GRADES = [
    {"key": "F",  "min_score": 0,  "max_score": 14,  "pct": -10},
    {"key": "D",  "min_score": 15, "max_score": 29,  "pct":   0},
    {"key": "C",  "min_score": 30, "max_score": 44,  "pct":   7},
    {"key": "B",  "min_score": 45, "max_score": 59,  "pct":  14},
    {"key": "A",  "min_score": 60, "max_score": 74,  "pct":  16},
    {"key": "S",  "min_score": 75, "max_score": 89,  "pct":  18},
    {"key": "S+", "min_score": 90, "max_score": 100, "pct":  25},
]

def tier_cond_change(tier):
    """Convert a tier's pct to actual condition points (out of MAX_CONDITION)."""
    return round(tier["pct"] / 100 * MAX_CONDITION)

JOB_TEMPLATES = [
    {"name": "Paint a Room",        "icon": "🎨", "desc": "Roll a fresh coat on interior walls"},
    {"name": "Lay Flooring",        "icon": "🪵", "desc": "Install hardwood planks in a living room"},
    {"name": "Patch the Roof",      "icon": "🏚️", "desc": "Seal up a leaking section of roofing"},
    {"name": "Fix a Plumbing Leak", "icon": "🔧", "desc": "Repair a leaky pipe under a kitchen sink"},
    {"name": "Install Windows",     "icon": "🪟", "desc": "Fit double-pane windows in a bedroom"},
    {"name": "Tile a Bathroom",     "icon": "🚿", "desc": "Lay ceramic tiles in a residential bathroom"},
    {"name": "Hang Drywall",        "icon": "🧱", "desc": "Install drywall sheets in a new build"},
    {"name": "Electrical Work",     "icon": "⚡", "desc": "Run wiring and fit outlets in a remodel"},
    {"name": "HVAC Maintenance",    "icon": "🌡️", "desc": "Service and tune a residential HVAC unit"},
    {"name": "Build a Fence",       "icon": "🪚", "desc": "Put up a new wooden privacy fence"},
    {"name": "Pour Concrete",       "icon": "🏗️", "desc": "Pour and level a new driveway section"},
    {"name": "Landscaping Work",    "icon": "🌿", "desc": "Clear, grade, and replant a front yard"},
    {"name": "Power Washing",       "icon": "💧", "desc": "Deep clean siding, decking, and walkways"},
    {"name": "Install Cabinets",    "icon": "🍳", "desc": "Mount and align kitchen cabinets and hardware"},
    {"name": "Repair a Deck",       "icon": "🪜", "desc": "Replace rotted planks on an outdoor deck"},
]

# Pay ranges per energy tier: {energy_cost: (min_base, max_base)}
JOB_PAY_RANGES = {1: (100, 350), 2: (350, 700), 3: (700, 1200), 4: (1200, 2000)}

# Creator / cheat codes — keys are lowercase for case-insensitive matching
CREATOR_CODES = {
    "cheatercheater": {"desc": "💰 $10,000,000 deposited!", "cash": 10_000_000},
}

def generate_jobs():
    """Pick 3 random jobs with guaranteed varied energy costs."""
    templates    = random.sample(JOB_TEMPLATES, 3)
    energy_costs = random.sample([1, 2, 3, 4], 3)   # always 3 different tiers
    jobs = []
    for i, (t, ec) in enumerate(zip(templates, energy_costs)):
        lo, hi = JOB_PAY_RANGES[ec]
        jobs.append({**t, "id": i, "energy_cost": ec, "base_pay": random.randint(lo, hi)})
    return jobs

CONTRACTORS = {
    "budget":   {"name": "Budget Bob",     "icon": "🔨", "desc": "Cheap but inconsistent — may cut corners", "cost_mult": 0.70, "q_min": 0,  "q_max": 59, "tier_range": "F – B"},
    "standard": {"name": "Standard Steve", "icon": "🛠️", "desc": "Reliable work at fair prices",              "cost_mult": 1.00, "q_min": 30, "q_max": 74, "tier_range": "C – A"},
    "premium":  {"name": "Premier Pete",   "icon": "⭐", "desc": "Top-tier quality, fully guaranteed",         "cost_mult": 1.50, "q_min": 45, "q_max": 100, "tier_range": "B – S+"},
}

# stay_min / stay_max are in DAYS
TENANT_PROFILES = [
    {"name": "Young Professional", "icon": "💼", "pay_chance": 0.97, "damage_chance": 0.03, "stay_min": 60,  "stay_max": 180},
    {"name": "College Student",    "icon": "🎓", "pay_chance": 0.82, "damage_chance": 0.12, "stay_min": 30,  "stay_max": 90},
    {"name": "Retired Couple",     "icon": "👴", "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365},
    {"name": "Young Family",       "icon": "👨‍👩‍👧", "pay_chance": 0.93, "damage_chance": 0.07, "stay_min": 90,  "stay_max": 270},
    {"name": "Freelancer",         "icon": "💻", "pay_chance": 0.85, "damage_chance": 0.05, "stay_min": 45,  "stay_max": 120},
    {"name": "Section 8",          "icon": "🏛️", "pay_chance": 0.95, "damage_chance": 0.08, "stay_min": 60,  "stay_max": 180},
]

# ── Game Logic ─────────────────────────────────────────────────────────────────

def get_upgrade_quality(upg_val):
    """Handle both old format (int) and new format (dict with quality+day)."""
    return upg_val["quality"] if isinstance(upg_val, dict) else upg_val

def upgrade_cooldown_remaining(upg_val, current_day):
    """Days left before this upgrade can be done again. 0 = available now."""
    if not isinstance(upg_val, dict):
        return 0   # old format = no cooldown
    return max(0, RENO_COOLDOWN - (current_day - upg_val.get("day", 0)))

def calc_market_value(prop):
    n         = NEIGHBORHOODS[prop["neighborhood"]]
    base      = prop["sqft"] * 120 + prop["bedrooms"] * 15000 + prop["bathrooms"] * 8000
    cond_mult = 0.5 + (prop["condition"] / MAX_CONDITION) * 0.7
    val       = int(base * n["price_mult"] * cond_mult)
    for key, upg_val in prop.get("upgrades", {}).items():
        quality = get_upgrade_quality(upg_val)
        val    += int(UPGRADES[key]["value_add"] * (quality / 100))
    val += get_premium_bonuses(prop)["value"]
    return val

def calc_monthly_rent(prop):
    n         = NEIGHBORHOODS[prop["neighborhood"]]
    base      = int((prop["sqft"] * 1.1 + prop["bedrooms"] * 400 + prop["bathrooms"] * 150) * n["rent_mult"])
    cond_mult = 0.6 + (prop["condition"] / MAX_CONDITION) * 0.5
    bonus     = sum(int(UPGRADES[k]["value_add"] * 0.003 * (get_upgrade_quality(v) / 100))
                    for k, v in prop.get("upgrades", {}).items())
    # premium_weekly is per-week; monthly_rent is used as 4-week equivalent
    premium_weekly = get_premium_bonuses(prop)["rent"]
    return int(base * cond_mult) + bonus + (premium_weekly * 4)

def calc_fair_weekly_rent(prop):
    return max(1, round(calc_monthly_rent(prop) / 4))

def rent_tier(weekly_rent, fair_rent):
    if fair_rent <= 0:
        return {"tier": "Average", "color": "blue", "stay_mult": 1.0, "damage_mult": 1.0, "pay_adj": 0.0}
    ratio = weekly_rent / fair_rent
    if ratio < 0.70:
        return {"tier": "Very Low",  "color": "green",  "stay_mult": 2.0, "damage_mult": 0.30, "pay_adj":  0.02}
    if ratio < 0.85:
        return {"tier": "Low",       "color": "green",  "stay_mult": 1.4, "damage_mult": 0.60, "pay_adj":  0.01}
    if ratio < 1.15:
        return {"tier": "Average",   "color": "blue",   "stay_mult": 1.0, "damage_mult": 1.00, "pay_adj":  0.00}
    if ratio < 1.35:
        return {"tier": "High",      "color": "orange", "stay_mult": 0.7, "damage_mult": 1.60, "pay_adj": -0.08}
    return     {"tier": "Very High", "color": "red",    "stay_mult": 0.4, "damage_mult": 2.50, "pay_adj": -0.18}

def score_to_tier(score):
    """Convert a 0-100 quality score to a letter grade tier."""
    for t in reversed(TIER_GRADES):
        if score >= t["min_score"]:
            return t
    return TIER_GRADES[0]

def condition_label(c):
    """Map a 0-250 condition value to a tier letter."""
    pct = (c / MAX_CONDITION) * 100
    return score_to_tier(pct)["key"]

def calc_weekly_payment(principal, annual_rate, term_seasons):
    term_weeks = term_seasons * 4   # 1 season = 28 days = 4 weeks exactly
    r = annual_rate / 52
    if r == 0:
        return round(principal / term_weeks, 2)
    return round(principal * r * (1 + r)**term_weeks / ((1 + r)**term_weeks - 1), 2)

def savings_tier(balance):
    tier = SAVINGS_TIERS[0]
    for t in SAVINGS_TIERS:
        if balance >= t["min"]:
            tier = t
    return tier

def enrich(prop, current_day=1):
    p = dict(prop)
    p["market_value"]    = calc_market_value(prop)
    p["monthly_rent"]    = calc_monthly_rent(prop)
    p["weekly_rent"]     = calc_fair_weekly_rent(prop)
    p["condition_label"] = condition_label(prop["condition"])
    p["icon"]            = PROPERTY_ICONS.get(prop["type"], "🏠")
    p["neighborhood_info"] = NEIGHBORHOODS[prop["neighborhood"]]
    p["deal"]            = p["market_value"] - prop["purchase_price"]
    if p.get("tenant"):
        lease_end = p["tenant"].get("lease_end_day", current_day)
        p["tenant_days_remaining"] = max(0, lease_end - current_day)
    return p

def generate_property(nid):
    ptype = random.choice(PROPERTY_TYPES)
    hood  = random.choice(list(NEIGHBORHOODS.keys()))
    beds  = random.randint(1, 5)
    baths = random.randint(1, min(beds, 3))
    sqft  = random.randint(600 + beds * 150, 900 + beds * 350)
    cond  = random.randint(25, 212)   # scaled to 250-point system
    prop  = {"id": nid, "type": ptype, "neighborhood": hood, "bedrooms": beds,
             "bathrooms": baths, "sqft": sqft, "condition": cond, "upgrades": {},
             "premium_upgrades": [],
             "tenant": None, "days_rented": 0,
             "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}
    prop["purchase_price"] = int(calc_market_value(prop) * random.uniform(0.88, 1.06))
    return prop

def make_starter_home():
    return {"id": 1, "type": "Bungalow", "neighborhood": "Eastside",
            "bedrooms": 2, "bathrooms": 1, "sqft": 820, "condition": 61,  # D tier on 250 scale
            "upgrades": {}, "premium_upgrades": [],
            "tenant": None, "days_rented": 0,
            "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}

def new_game():
    starter = make_starter_home()
    state = {
        "cash": STARTING_CASH, "day": 1, "next_id": 2,
        "properties": [starter], "market": [], "log": [],
        "applicants_cache": {},
        "last_bank_day": 1,
        "energy": DAILY_ENERGY,
        "jobs": generate_jobs(),
        "redeemed_codes": [],
        "bank": {"savings": 0, "loans": [], "next_loan_id": 1},
    }
    state["log"].append({"day": 1, "type": "info",
        "text": "You inherited a run-down Bungalow in Eastside. Fix it up and build your empire!"})
    state["market"], state["next_id"] = _gen_market(state["next_id"])
    return state

def _gen_market(start_id, count=5):
    listings, nid = [], start_id
    for _ in range(count):
        listings.append(generate_property(nid))
        nid += 1
    return listings, nid

def load():
    """Read game state from the request body (_state field) or start a new game."""
    data  = request.get_json(silent=True) or {}
    state = data.get('_state')
    return state if state else new_game()

def save(state):
    """Store state on Flask's per-request g — injected into the response automatically."""
    state["log"] = state["log"][-300:]   # cap log so state doesn't grow unbounded
    g.game_state = state

# ── Inject saved state into every JSON response ───────────────────────────────
@app.after_request
def inject_state(response):
    if response.content_type.startswith('application/json') and hasattr(g, 'game_state'):
        try:
            data = response.get_json()
            if isinstance(data, dict) and '_state' not in data:
                data['_state'] = g.game_state
                response.set_data(json.dumps(data))
        except Exception:
            pass
    return response

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state', methods=['GET', 'POST'])
def api_state():
    s = load()
    weekly_income = sum(p["tenant"]["rent"] for p in s["properties"] if p.get("tenant"))
    return jsonify({
        "cash":           s["cash"],
        "day":            s["day"],
        "energy":         s.get("energy", DAILY_ENERGY),
        "jobs":           s.get("jobs", []),
        "net_worth":      s["cash"] + sum(calc_market_value(p) for p in s["properties"]),
        "weekly_income":  weekly_income,
        "property_count": len(s["properties"]),
        "properties":     [enrich(p, s["day"]) for p in s["properties"]],
        "log":            s["log"][-40:],
        "bank":           s.get("bank", {"savings": 0, "loans": [], "next_loan_id": 1}),
        "savings_tier":   savings_tier(s.get("bank", {}).get("savings", 0)),
    })

@app.route('/api/market', methods=['GET', 'POST'])
def api_market():
    s = load()
    if not s["market"]:
        s["market"], s["next_id"] = _gen_market(s["next_id"])
        save(s)
    return jsonify({"listings": [enrich(p, s["day"]) for p in s["market"]]})

@app.route('/api/market/refresh', methods=['POST'])
def api_market_refresh():
    s = load()
    s["market"], s["next_id"] = _gen_market(s["next_id"])
    save(s)
    return jsonify({"listings": [enrich(p, s["day"]) for p in s["market"]]})

@app.route('/api/buy', methods=['POST'])
def api_buy():
    data = request.json
    s    = load()
    prop = next((p for p in s["market"] if p["id"] == data["listing_id"]), None)
    if not prop:
        return jsonify({"error": "Listing not found"}), 404
    if prop["purchase_price"] > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= prop["purchase_price"]
    s["properties"].append(prop)
    s["market"] = [p for p in s["market"] if p["id"] != prop["id"]]
    s["log"].append({"day": s["day"], "type": "buy",
        "text": f"Bought {prop['bedrooms']}bd {prop['type']} in {prop['neighborhood']} for ${prop['purchase_price']:,}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/property/<int:pid>/upgrades', methods=['GET', 'POST'])
def api_upgrades(pid):
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    available, on_cooldown = [], []
    current_day = s["day"]
    for key, upg in UPGRADES.items():
        upg_val = prop.get("upgrades", {}).get(key)
        if upg_val is not None:
            quality   = get_upgrade_quality(upg_val)
            remaining = upgrade_cooldown_remaining(upg_val, current_day)
            tier_key  = score_to_tier(quality)["key"]
            if remaining > 0:
                on_cooldown.append({**upg, "key": key, "quality": quality,
                                    "quality_tier": tier_key, "days_remaining": remaining})
            else:
                # Cooldown expired — available to renovate again
                costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
                available.append({**upg, "key": key, "costs": costs,
                                  "prev_quality_tier": tier_key})
        else:
            costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
            available.append({**upg, "key": key, "costs": costs})
    return jsonify({"available": available, "on_cooldown": on_cooldown,
                    "contractors": CONTRACTORS, "cash": s["cash"]})

@app.route('/api/renovate', methods=['POST'])
def api_renovate():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    if prop.get("tenant"):
        return jsonify({"error": "Tenant must vacate first"}), 400
    existing  = prop.get("upgrades", {}).get(data["upgrade_key"])
    remaining = upgrade_cooldown_remaining(existing, s["day"]) if existing is not None else 0
    if remaining > 0:
        return jsonify({"error": f"On cooldown — {remaining} days remaining"}), 400
    upg  = UPGRADES[data["upgrade_key"]]
    cont = CONTRACTORS[data["contractor_key"]]
    cost = int(upg["base_cost"] * cont["cost_mult"])
    if cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    quality     = random.randint(cont["q_min"], cont["q_max"])
    tier        = score_to_tier(quality)
    cond_change = tier_cond_change(tier)
    s["cash"] -= cost
    prop.setdefault("upgrades", {})[data["upgrade_key"]] = {"quality": quality, "day": s["day"]}
    prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_change))
    new_val = calc_market_value(prop)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"{upg['name']} on {prop['type']} in {prop['neighborhood']} — grade {tier['key']}, value now ${new_val:,}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "quality": quality,
                    "quality_tier": tier["key"], "cond_change": cond_change, "cond_pct": tier["pct"],
                    "condition": prop["condition"], "market_value": new_val,
                    "weekly_rent": calc_fair_weekly_rent(prop)})

@app.route('/api/property/<int:pid>/premium_upgrades', methods=['GET', 'POST'])
def api_premium_upgrades(pid):
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404

    # POST — return catalog if no upgrade_key (api() always POSTs), else install
    data        = request.json or {}
    upgrade_key = data.get("upgrade_key")
    if not upgrade_key:
        installed = prop.get("premium_upgrades", [])
        catalog = [
            {**v, "key": k, "installed": k in installed}
            for k, v in PREMIUM_UPGRADES.items()
        ]
        return jsonify({"catalog": catalog, "installed": installed})
    if upgrade_key not in PREMIUM_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400

    installed = prop.setdefault("premium_upgrades", [])
    if upgrade_key in installed:
        return jsonify({"error": "Already installed"}), 400

    upg  = PREMIUM_UPGRADES[upgrade_key]
    cost = upg["cost"]
    if s["cash"] < cost:
        return jsonify({"error": f"Need ${cost:,} — you have ${int(s['cash']):,}"}), 400

    s["cash"] -= cost
    installed.append(upgrade_key)
    new_val     = calc_market_value(prop)
    weekly_rent = calc_fair_weekly_rent(prop)
    s["log"].append({"day": s["day"], "type": "upgrade",
        "text": f"Installed {upg['name']} at {prop['type']} in {prop['neighborhood']} — value now ${new_val:,}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "market_value": new_val, "weekly_rent": weekly_rent,
                    "premium_upgrades": installed})

@app.route('/api/sell', methods=['POST'])
def api_sell():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    if prop.get("tenant"):
        return jsonify({"error": "Evict tenant first"}), 400
    sale   = int(calc_market_value(prop) * random.uniform(0.95, 1.05))
    profit = sale - prop["purchase_price"]
    s["cash"] += sale
    s["properties"] = [p for p in s["properties"] if p["id"] != prop["id"]]
    s["log"].append({"day": s["day"], "type": "sell" if profit >= 0 else "loss",
        "text": f"Sold {prop['type']} in {prop['neighborhood']} for ${sale:,} ({'profit' if profit >= 0 else 'loss'}: ${abs(profit):,})"})
    save(s)
    return jsonify({"success": True, "sale_price": sale, "profit": profit, "cash": s["cash"]})

@app.route('/api/property/<int:pid>/applicants', methods=['GET', 'POST'])
def api_applicants(pid):
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    key = str(pid)
    if key not in s.get("applicants_cache", {}):
        picks = random.sample(TENANT_PROFILES, min(3, len(TENANT_PROFILES)))
        applicants = [{**t, "idx": i,
                       "damage_label": "Low" if t["damage_chance"] < 0.05 else ("Medium" if t["damage_chance"] < 0.10 else "High")}
                      for i, t in enumerate(picks)]
        s.setdefault("applicants_cache", {})[key] = applicants
        save(s)
    fair_weekly = calc_fair_weekly_rent(prop)
    return jsonify({"applicants": s["applicants_cache"][key], "fair_weekly_rent": fair_weekly})

@app.route('/api/rent', methods=['POST'])
def api_rent():
    data        = request.json
    s           = load()
    prop        = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    if prop.get("tenant"):
        return jsonify({"error": "Already rented"}), 400
    key         = str(data["prop_id"])
    applicants  = s.get("applicants_cache", {}).get(key, [])
    if not applicants or data["applicant_idx"] >= len(applicants):
        return jsonify({"error": "Invalid applicant"}), 400

    weekly_rent = int(data["rent_amount"])
    fair_rent   = calc_fair_weekly_rent(prop)
    tier        = rent_tier(weekly_rent, fair_rent)
    t           = applicants[data["applicant_idx"]]

    base_stay   = random.randint(t["stay_min"], t["stay_max"])
    stay_days   = max(7, int(base_stay * tier["stay_mult"]))
    pay_chance  = min(0.99, max(0.50, t["pay_chance"] + tier["pay_adj"]))
    dmg_chance  = min(0.50, max(0.005, t["damage_chance"] * tier["damage_mult"]))

    prop["tenant"] = {
        **t,
        "rent":            weekly_rent,
        "fair_rent":       fair_rent,
        "rent_tier":       tier["tier"],
        "pay_chance":      pay_chance,
        "damage_chance":   dmg_chance,
        "next_rent_day":   s["day"] + 7,
        "lease_end_day":   s["day"] + stay_days,
    }
    s.get("applicants_cache", {}).pop(key, None)
    s["log"].append({"day": s["day"], "type": "rent",
        "text": f"{t['name']} moved into {prop['type']} in {prop['neighborhood']} — ${weekly_rent:,}/wk ({tier['tier']} rent) for ~{stay_days} days"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/evict', methods=['POST'])
def api_evict():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop or not prop.get("tenant"):
        return jsonify({"error": "No tenant to evict"}), 400
    fee  = 1500
    if s["cash"] < fee:
        return jsonify({"error": "Need $1,500 for legal fees"}), 400
    name = prop["tenant"]["name"]
    s["cash"] -= fee
    prop["tenant"] = None
    s["log"].append({"day": s["day"], "type": "evict",
        "text": f"Evicted {name} from {prop['type']} in {prop['neighborhood']} ($1,500 legal fees)"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/advance', methods=['POST'])
def api_advance():
    data     = request.json
    days     = max(1, min(int(data.get("days", 1)), 30))
    s           = load()
    events      = []
    new_repairs = []
    rent_log    = {}   # prop_id -> summary dict

    for d in range(days):
        current_day = s["day"] + d + 1

        for prop in s["properties"]:
            if not prop.get("tenant"):
                continue
            t   = prop["tenant"]
            pid = prop["id"]

            # Lease end
            if current_day >= t.get("lease_end_day", 999999):
                name = t["name"]
                prop["tenant"] = None
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"{name}'s lease ended — moved out", "type": "warning"})
                s["log"].append({"day": current_day, "type": "info",
                    "text": f"{name} moved out of {prop['type']} in {prop['neighborhood']}"})
                continue

            # Weekly rent due
            if current_day >= t.get("next_rent_day", 999999):
                t["next_rent_day"] += 7
                rent = t["rent"]
                if pid not in rent_log:
                    rent_log[pid] = {"name": t["name"],
                                     "prop": f"{prop['type']} — {prop['neighborhood']}",
                                     "collected": 0, "partial": 0, "missed": 0}
                roll = random.random()
                if roll < t["pay_chance"]:
                    s["cash"]                   += rent
                    prop["total_rent_collected"] += rent
                    rent_log[pid]["collected"]   += rent
                elif roll < t["pay_chance"] + 0.06:
                    partial = int(rent * 0.5)
                    s["cash"]                   += partial
                    prop["total_rent_collected"] += partial
                    rent_log[pid]["collected"]   += partial
                    rent_log[pid]["partial"]     += 1
                else:
                    rent_log[pid]["missed"] += 1

            # Daily damage chance — generates a repair event the player must handle
            if random.random() < t["damage_chance"] / 7:
                rt = random.choice(REPAIR_TYPES)
                prop["condition"] = max(0, prop["condition"] - 2)   # small drop just from problem occurring
                new_repairs.append({
                    "id":        f"r{current_day}_{pid}",
                    "prop_id":   pid,
                    "prop_name": f"{prop['type']} — {prop['neighborhood']}",
                    "repair_type": rt,
                    "costs":     {k: int(rt["base_cost"] * c["cost_mult"]) for k, c in CONTRACTORS.items()},
                })

            prop["days_rented"] = prop.get("days_rented", 0) + 1

        # Every 7 days: weekly bank processing (savings interest + loan payments)
        last_bank = s.get("last_bank_day", 1)
        if current_day - last_bank >= 7:
            s["last_bank_day"] = current_day
            bank = s.get("bank", {"savings": 0, "loans": [], "next_loan_id": 1})

            if bank.get("savings", 0) > 0:
                st       = savings_tier(bank["savings"])
                interest = round(bank["savings"] * st["monthly_rate"] / 4, 2)
                bank["savings"] = round(bank["savings"] + interest, 2)
                events.append({"prop": "Savings Account",
                                "text": f"Weekly interest: +${interest:,.2f}", "type": "positive"})

            paid_off = []
            for loan in bank.get("loans", []):
                # Support both old monthly_payment loans and new weekly_payment loans
                wp       = loan.get("weekly_payment") or round(loan.get("monthly_payment", 0) / 4, 2)
                wr       = loan.get("weekly_rate")    or loan.get("monthly_rate", 0) / 4
                payment  = round(min(wp, loan["balance"]), 2)
                int_part = round(loan["balance"] * wr, 2)
                pri_part = round(payment - int_part, 2)
                s["cash"] -= payment
                loan["balance"] = round(max(0, loan["balance"] - pri_part), 2)
                loan["weeks_paid"] = loan.get("weeks_paid", loan.get("months_paid", 0)) + 1
                label = "⚠ You're in the red!" if s["cash"] < 0 else f"${loan['balance']:,.0f} left"
                events.append({"prop": loan["product"],
                                "text": f"Weekly loan payment: -${payment:,.2f} ({label})",
                                "type": "negative" if s["cash"] < 0 else "warning"})
                if loan["balance"] <= 0:
                    paid_off.append(loan["id"])
                    events.append({"prop": loan["product"], "text": "Loan fully paid off! 🎉", "type": "positive"})
            bank["loans"] = [l for l in bank["loans"] if l["id"] not in paid_off]
            s["bank"] = bank

        # Refresh market each day advance
        s["market"], s["next_id"] = _gen_market(s["next_id"])

    # Restore energy and refresh jobs at the start of the new day
    s["energy"] = DAILY_ENERGY
    s["jobs"]   = generate_jobs()


    # Build rent summary events
    for pid, rs in rent_log.items():
        if rs["collected"] > 0 or rs["missed"] > 0:
            txt   = f"{rs['name']}: collected ${rs['collected']:,}/wk"
            if rs["partial"]:
                txt += f" ({rs['partial']} partial)"
            if rs["missed"]:
                txt += f", {rs['missed']} missed"
            etype = "positive" if rs["missed"] == 0 and rs["partial"] == 0 else (
                    "warning"  if rs["collected"] > 0 else "negative")
            events.append({"prop": rs["prop"], "text": txt, "type": etype})

    s["day"] += days
    save(s)
    return jsonify({
        "success":   True,
        "day":       s["day"],
        "cash":      s["cash"],
        "net_worth": s["cash"] + sum(calc_market_value(p) for p in s["properties"]),
        "events":    events,
        "repairs":   new_repairs,
    })

# ── Bank Routes ────────────────────────────────────────────────────────────────

@app.route('/api/bank/products', methods=['GET', 'POST'])
def api_bank_products():
    products = [{**p, "sample_payment": calc_weekly_payment(p["min"], p["apr"], p["term_seasons"])}
                for p in LOAN_PRODUCTS]
    return jsonify({"products": products, "savings_tiers": SAVINGS_TIERS})

@app.route('/api/bank/loan/preview', methods=['POST'])
def api_loan_preview():
    data    = request.json
    product = next((p for p in LOAN_PRODUCTS if p["key"] == data["product_key"]), None)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    amount  = int(data["amount"])
    if amount < product["min"] or amount > product["max"]:
        return jsonify({"error": f"Amount must be between ${product['min']:,} and ${product['max']:,}"}), 400
    payment     = calc_weekly_payment(amount, product["apr"], product["term_seasons"])
    term_weeks  = product["term_seasons"] * 4
    total       = round(payment * term_weeks, 2)
    return jsonify({"weekly_payment": payment, "total_repaid": total,
                    "total_interest": round(total - amount, 2), "term_seasons": product["term_seasons"],
                    "term_weeks": term_weeks})

@app.route('/api/bank/loan/take', methods=['POST'])
def api_loan_take():
    data    = request.json
    s       = load()
    product = next((p for p in LOAN_PRODUCTS if p["key"] == data["product_key"]), None)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    amount = int(data["amount"])
    if amount < product["min"] or amount > product["max"]:
        return jsonify({"error": "Amount out of range"}), 400
    if "bank" not in s:
        s["bank"] = {"savings": 0, "loans": [], "next_loan_id": 1}
    payment      = calc_weekly_payment(amount, product["apr"], product["term_seasons"])
    term_weeks   = product["term_seasons"] * 4
    term_seasons = product["term_seasons"]
    loan = {"id": s["bank"]["next_loan_id"], "product": product["name"], "icon": product["icon"],
            "balance": amount, "original_amount": amount,
            "weekly_payment": payment, "weekly_rate": product["apr"] / 52,
            "term_seasons": term_seasons, "term_weeks": term_weeks, "weeks_paid": 0}
    s["bank"]["next_loan_id"] += 1
    s["bank"]["loans"].append(loan)
    s["cash"] += amount
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Took out a {product['name']} for ${amount:,} — ${payment:,.2f}/wk for {term_seasons} seasons ({term_weeks} weeks)"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "loan": loan})

@app.route('/api/bank/loan/pay', methods=['POST'])
def api_loan_pay():
    data    = request.json
    s       = load()
    loan    = next((l for l in s["bank"]["loans"] if l["id"] == data["loan_id"]), None)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404
    amount  = min(float(data["amount"]), loan["balance"])
    if amount > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"]      -= amount
    loan["balance"] = round(loan["balance"] - amount, 2)
    if loan["balance"] <= 0:
        s["bank"]["loans"] = [l for l in s["bank"]["loans"] if l["id"] != loan["id"]]
        s["log"].append({"day": s["day"], "type": "info", "text": f"Fully paid off your {loan['product']}!"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "remaining": max(0, loan.get("balance", 0))})

@app.route('/api/bank/savings/deposit', methods=['POST'])
def api_savings_deposit():
    data   = request.json
    amount = int(data["amount"])
    s      = load()
    if amount <= 0 or amount > s["cash"]:
        return jsonify({"error": "Invalid amount"}), 400
    s["bank"].setdefault("savings", 0)
    s["cash"]            -= amount
    s["bank"]["savings"] += amount
    tier = savings_tier(s["bank"]["savings"])
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Deposited ${amount:,} into savings — ${s['bank']['savings']:,} total ({tier['label']} tier, {tier['apr']}% APR)"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "savings": s["bank"]["savings"], "tier": tier})

@app.route('/api/bank/savings/withdraw', methods=['POST'])
def api_savings_withdraw():
    data   = request.json
    amount = int(data["amount"])
    s      = load()
    if amount <= 0 or amount > s["bank"].get("savings", 0):
        return jsonify({"error": "Invalid amount"}), 400
    s["bank"]["savings"] -= amount
    s["cash"]            += amount
    s["log"].append({"day": s["day"], "type": "info", "text": f"Withdrew ${amount:,} from savings"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "savings": s["bank"]["savings"]})

@app.route('/api/diy_renovate', methods=['POST'])
def api_diy_renovate():
    data     = request.json
    s        = load()
    prop     = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    if prop.get("tenant"):
        return jsonify({"error": "Tenant must vacate first"}), 400
    upgrade_key = data["upgrade_key"]
    existing    = prop.get("upgrades", {}).get(upgrade_key)
    remaining   = upgrade_cooldown_remaining(existing, s["day"]) if existing is not None else 0
    if remaining > 0:
        return jsonify({"error": f"On cooldown — {remaining} days remaining"}), 400
    upg         = UPGRADES[upgrade_key]
    energy_cost = upg.get("energy_cost", 1)
    if s.get("energy", DAILY_ENERGY) < energy_cost:
        return jsonify({"error": f"Not enough energy — this renovation costs ⚡{energy_cost}"}), 400
    quality     = max(0, min(100, int(data["quality"])))
    tier        = score_to_tier(quality)
    cond_change = tier_cond_change(tier)
    s["energy"] = s.get("energy", DAILY_ENERGY) - energy_cost
    prop.setdefault("upgrades", {})[upgrade_key] = {"quality": quality, "day": s["day"]}
    prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_change))
    new_val = calc_market_value(prop)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"DIY {upg['name']} on {prop['type']} in {prop['neighborhood']} — grade {tier['key']}, value now ${new_val:,}"})
    save(s)
    return jsonify({"success": True, "quality": quality, "quality_tier": tier["key"],
                    "cond_change": cond_change, "cond_pct": tier["pct"], "condition": prop["condition"],
                    "market_value": new_val, "weekly_rent": calc_fair_weekly_rent(prop),
                    "energy": s["energy"]})

@app.route('/api/repair/fix', methods=['POST'])
def api_repair_fix():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    rt   = next((r for r in REPAIR_TYPES if r["key"] == data["repair_key"]), None)
    if not rt:
        return jsonify({"error": "Invalid repair type"}), 400

    method = data["method"]   # 'diy' or a contractor key
    if method == 'diy':
        quality   = max(5, min(100, int(data["quality"])))
        cond_gain = int(rt["cond_fix"] * (quality / 100))
        cost      = 0
    else:
        cont = CONTRACTORS.get(method)
        if not cont:
            return jsonify({"error": "Invalid contractor"}), 400
        cost = int(rt["base_cost"] * cont["cost_mult"])
        if cost > s["cash"]:
            return jsonify({"error": "Not enough cash"}), 400
        quality   = random.randint(cont["q_min"], cont["q_max"])
        cond_gain = int(rt["cond_fix"] * (quality / 100))
        s["cash"] -= cost
        prop["total_repair_costs"] += cost

    prop["condition"] = min(MAX_CONDITION, prop["condition"] + cond_gain)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"{rt['name']} fixed at {prop['type']} in {prop['neighborhood']} ({method}, quality {quality}/100)"})
    save(s)
    return jsonify({"success": True, "quality": quality, "condition": prop["condition"],
                    "cost": cost, "cash": s["cash"]})

@app.route('/api/repair/ignore', methods=['POST'])
def api_repair_ignore():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    rt        = next((r for r in REPAIR_TYPES if r["key"] == data["repair_key"]), None)
    cond_loss = rt["cond_loss"] if rt else 3
    prop["condition"] = max(0, prop["condition"] - cond_loss)
    s["log"].append({"day": s["day"], "type": "warning",
        "text": f"Ignored {rt['name'] if rt else 'repair'} at {prop['type']} in {prop['neighborhood']} — condition -{cond_loss}"})
    save(s)
    return jsonify({"success": True, "condition": prop["condition"], "cash": s["cash"]})

@app.route('/api/jobs/complete', methods=['POST'])
def api_jobs_complete():
    data = request.json
    s    = load()
    job  = next((j for j in s.get("jobs", []) if j["id"] == data["job_id"]), None)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if s.get("energy", DAILY_ENERGY) < job["energy_cost"]:
        return jsonify({"error": f"Not enough energy — this job needs ⚡{job['energy_cost']}"}), 400
    quality  = max(0, min(100, int(data["quality"])))
    # Pay scales from 50% (score 0) to 100% (score 100) of base_pay
    pay      = round(job["base_pay"] * (0.5 + 0.5 * quality / 100))
    s["energy"] = s.get("energy", DAILY_ENERGY) - job["energy_cost"]
    s["cash"]  += pay
    s["jobs"]   = [j for j in s["jobs"] if j["id"] != job["id"]]
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Side job '{job['name']}' — quality {quality}/100, earned ${pay:,}"})
    save(s)
    return jsonify({"success": True, "pay": pay, "cash": s["cash"],
                    "energy": s["energy"], "quality": quality})

@app.route('/api/redeem_code', methods=['POST'])
def api_redeem_code():
    s    = load()
    data = request.json or {}
    code = (data.get("code") or "").strip().lower()
    if code not in CREATOR_CODES:
        return jsonify({"error": "Invalid code — try again!"}), 400
    redeemed = s.get("redeemed_codes", [])
    if code in redeemed:
        return jsonify({"error": "Code already used!"}), 400
    reward = CREATOR_CODES[code]
    s["cash"] += reward.get("cash", 0)
    s.setdefault("redeemed_codes", []).append(code)
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Creator code redeemed — {reward['desc']}"})
    save(s)
    return jsonify({"success": True, "reward_desc": reward["desc"]})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
