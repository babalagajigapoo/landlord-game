from flask import Flask, render_template, jsonify, request, g
import json, os, random

app = Flask(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

STARTING_CASH = 5_000

LOAN_PRODUCTS = [
    {"key": "quick",    "name": "Quick Cash",    "icon": "💵", "min": 500,   "max": 5_000,   "apr": 0.24, "term": 12, "desc": "Fast money, high interest."},
    {"key": "personal", "name": "Personal Loan", "icon": "🤝", "min": 3_000, "max": 25_000,  "apr": 0.15, "term": 24, "desc": "Reasonable rates for mid-range needs."},
    {"key": "property", "name": "Property Loan", "icon": "🏦", "min": 15000, "max": 75_000,  "apr": 0.09, "term": 36, "desc": "Low rates for real estate investment."},
    {"key": "business", "name": "Business Loan", "icon": "💼", "min": 50000, "max": 150_000, "apr": 0.07, "term": 48, "desc": "Best rates for serious investors."},
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
    {"key": "plumbing",   "name": "Plumbing Leak",       "icon": "🔧", "base_cost": 400,  "cond_loss": 3, "cond_fix": 4},
    {"key": "electrical", "name": "Electrical Issue",    "icon": "⚡", "base_cost": 700,  "cond_loss": 2, "cond_fix": 3},
    {"key": "appliance",  "name": "Appliance Breakdown", "icon": "📦", "base_cost": 350,  "cond_loss": 2, "cond_fix": 3},
    {"key": "roof_patch", "name": "Roof Patch Needed",   "icon": "🏚️", "base_cost": 900,  "cond_loss": 4, "cond_fix": 5},
    {"key": "pest",       "name": "Pest Problem",        "icon": "🐛", "base_cost": 300,  "cond_loss": 3, "cond_fix": 3},
    {"key": "hvac_fix",   "name": "HVAC Repair",         "icon": "🌡️", "base_cost": 600,  "cond_loss": 3, "cond_fix": 4},
]

UPGRADES = {
    "paint":       {"name": "Interior Paint",   "icon": "🎨", "base_cost": 1500,  "value_add": 3000,  "cond_boost": 15},
    "landscaping": {"name": "Landscaping",       "icon": "🌿", "base_cost": 2000,  "value_add": 4500,  "cond_boost": 10},
    "flooring":    {"name": "New Flooring",      "icon": "🪵", "base_cost": 4000,  "value_add": 8000,  "cond_boost": 20},
    "windows":     {"name": "New Windows",       "icon": "🪟", "base_cost": 6000,  "value_add": 10000, "cond_boost": 12},
    "hvac":        {"name": "HVAC System",       "icon": "❄️", "base_cost": 7000,  "value_add": 11000, "cond_boost": 15},
    "bathrooms":   {"name": "Bathroom Remodel",  "icon": "🚿", "base_cost": 8000,  "value_add": 14000, "cond_boost": 20},
    "roof":        {"name": "Roof Replacement",  "icon": "🏠", "base_cost": 10000, "value_add": 15000, "cond_boost": 18},
    "kitchen":     {"name": "Kitchen Remodel",   "icon": "🍳", "base_cost": 12000, "value_add": 22000, "cond_boost": 25},
}

CONTRACTORS = {
    "budget":   {"name": "Budget Bob",     "icon": "🔨", "desc": "Cheap but inconsistent — may cut corners", "cost_mult": 0.70, "q_min": 45, "q_max": 80},
    "standard": {"name": "Standard Steve", "icon": "🛠️", "desc": "Reliable work at fair prices",              "cost_mult": 1.00, "q_min": 75, "q_max": 95},
    "premium":  {"name": "Premier Pete",   "icon": "⭐", "desc": "Top-tier quality, fully guaranteed",         "cost_mult": 1.50, "q_min": 92, "q_max": 100},
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

def calc_market_value(prop):
    n    = NEIGHBORHOODS[prop["neighborhood"]]
    base = prop["sqft"] * 120 + prop["bedrooms"] * 15000 + prop["bathrooms"] * 8000
    cond_mult = 0.5 + (prop["condition"] / 100) * 0.7
    val  = int(base * n["price_mult"] * cond_mult)
    for key, quality in prop.get("upgrades", {}).items():
        val += int(UPGRADES[key]["value_add"] * (quality / 100))
    return val

def calc_monthly_rent(prop):
    n    = NEIGHBORHOODS[prop["neighborhood"]]
    base = int((prop["sqft"] * 1.1 + prop["bedrooms"] * 400 + prop["bathrooms"] * 150) * n["rent_mult"])
    cond_mult = 0.6 + (prop["condition"] / 100) * 0.5
    bonus = sum(int(UPGRADES[k]["value_add"] * 0.003 * (q / 100)) for k, q in prop.get("upgrades", {}).items())
    return int(base * cond_mult) + bonus

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

def condition_label(c):
    if c >= 90: return "Excellent"
    if c >= 75: return "Good"
    if c >= 55: return "Fair"
    if c >= 35: return "Poor"
    return "Dilapidated"

def calc_monthly_payment(principal, annual_rate, term_months):
    r = annual_rate / 12
    if r == 0:
        return round(principal / term_months, 2)
    return round(principal * r * (1 + r)**term_months / ((1 + r)**term_months - 1), 2)

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
    cond  = random.randint(10, 85)
    prop  = {"id": nid, "type": ptype, "neighborhood": hood, "bedrooms": beds,
             "bathrooms": baths, "sqft": sqft, "condition": cond, "upgrades": {},
             "tenant": None, "days_rented": 0,
             "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}
    prop["purchase_price"] = int(calc_market_value(prop) * random.uniform(0.88, 1.06))
    return prop

def make_starter_home():
    return {"id": 1, "type": "Bungalow", "neighborhood": "Eastside",
            "bedrooms": 2, "bathrooms": 1, "sqft": 820, "condition": 28,
            "upgrades": {}, "tenant": None, "days_rented": 0,
            "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}

def new_game():
    starter = make_starter_home()
    state = {
        "cash": STARTING_CASH, "day": 1, "next_id": 2,
        "properties": [starter], "market": [], "log": [],
        "applicants_cache": {},
        "last_bank_day": 1,
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
    available, done = [], []
    for key, upg in UPGRADES.items():
        if key in prop.get("upgrades", {}):
            done.append({**upg, "key": key, "quality": prop["upgrades"][key]})
        else:
            costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
            available.append({**upg, "key": key, "costs": costs})
    return jsonify({"available": available, "done": done, "contractors": CONTRACTORS, "cash": s["cash"]})

@app.route('/api/renovate', methods=['POST'])
def api_renovate():
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    if prop.get("tenant"):
        return jsonify({"error": "Tenant must vacate first"}), 400
    if data["upgrade_key"] in prop.get("upgrades", {}):
        return jsonify({"error": "Already upgraded"}), 400
    upg  = UPGRADES[data["upgrade_key"]]
    cont = CONTRACTORS[data["contractor_key"]]
    cost = int(upg["base_cost"] * cont["cost_mult"])
    if cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    quality   = random.randint(cont["q_min"], cont["q_max"])
    cond_gain = int(upg["cond_boost"] * (quality / 100))
    s["cash"] -= cost
    prop.setdefault("upgrades", {})[data["upgrade_key"]] = quality
    prop["condition"] = min(100, prop["condition"] + cond_gain)
    new_val = calc_market_value(prop)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"{upg['name']} done on {prop['type']} in {prop['neighborhood']} — quality {quality}/100, value now ${new_val:,}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "quality": quality,
                    "condition": prop["condition"], "market_value": new_val,
                    "weekly_rent": calc_fair_weekly_rent(prop)})

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
                prop["condition"] = max(0, prop["condition"] - 1)   # small drop just from problem occurring
                new_repairs.append({
                    "id":        f"r{current_day}_{pid}",
                    "prop_id":   pid,
                    "prop_name": f"{prop['type']} — {prop['neighborhood']}",
                    "repair_type": rt,
                    "costs":     {k: int(rt["base_cost"] * c["cost_mult"]) for k, c in CONTRACTORS.items()},
                })

            prop["days_rented"] = prop.get("days_rented", 0) + 1

        # Every 28 days: bank processing
        last_bank = s.get("last_bank_day", 1)
        if current_day - last_bank >= DAYS_PER_SEASON:
            s["last_bank_day"] = current_day
            bank = s.get("bank", {"savings": 0, "loans": [], "next_loan_id": 1})

            if bank.get("savings", 0) > 0:
                tier     = savings_tier(bank["savings"])
                interest = round(bank["savings"] * tier["monthly_rate"], 2)
                bank["savings"] = round(bank["savings"] + interest, 2)
                events.append({"prop": "Savings Account",
                                "text": f"Monthly interest earned: +${interest:,.2f}", "type": "positive"})

            paid_off = []
            for loan in bank.get("loans", []):
                payment  = round(min(loan["monthly_payment"], loan["balance"]), 2)
                int_part = round(loan["balance"] * loan["monthly_rate"], 2)
                pri_part = round(payment - int_part, 2)
                s["cash"] -= payment
                loan["balance"] = round(max(0, loan["balance"] - pri_part), 2)
                loan["months_paid"] += 1
                label = "⚠ You're in the red!" if s["cash"] < 0 else f"${loan['balance']:,.0f} left"
                events.append({"prop": loan["product"],
                                "text": f"Loan payment: -${payment:,.2f} ({label})",
                                "type": "negative" if s["cash"] < 0 else "warning"})
                if loan["balance"] <= 0:
                    paid_off.append(loan["id"])
                    events.append({"prop": loan["product"], "text": "Loan fully paid off! 🎉", "type": "positive"})
            bank["loans"] = [l for l in bank["loans"] if l["id"] not in paid_off]
            s["bank"] = bank


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
    products = [{**p, "sample_payment": calc_monthly_payment(p["min"], p["apr"], p["term"])}
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
    payment = calc_monthly_payment(amount, product["apr"], product["term"])
    total   = round(payment * product["term"], 2)
    return jsonify({"monthly_payment": payment, "total_repaid": total,
                    "total_interest": round(total - amount, 2), "term": product["term"]})

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
    payment = calc_monthly_payment(amount, product["apr"], product["term"])
    loan = {"id": s["bank"]["next_loan_id"], "product": product["name"], "icon": product["icon"],
            "balance": amount, "monthly_payment": payment, "monthly_rate": product["apr"] / 12,
            "term": product["term"], "months_paid": 0}
    s["bank"]["next_loan_id"] += 1
    s["bank"]["loans"].append(loan)
    s["cash"] += amount
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Took out a {product['name']} for ${amount:,} — ${payment:,.2f}/mo for {product['term']} months"})
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
    if upgrade_key in prop.get("upgrades", {}):
        return jsonify({"error": "Already upgraded"}), 400
    upg     = UPGRADES[upgrade_key]
    quality = max(5, min(100, int(data["quality"])))
    cond_gain = int(upg["cond_boost"] * (quality / 100))
    prop.setdefault("upgrades", {})[upgrade_key] = quality
    prop["condition"] = min(100, prop["condition"] + cond_gain)
    new_val = calc_market_value(prop)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"DIY {upg['name']} on {prop['type']} in {prop['neighborhood']} — quality {quality}/100, value now ${new_val:,}"})
    save(s)
    return jsonify({"success": True, "quality": quality, "condition": prop["condition"],
                    "market_value": new_val, "weekly_rent": calc_fair_weekly_rent(prop)})

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

    prop["condition"] = min(100, prop["condition"] + cond_gain)
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

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
