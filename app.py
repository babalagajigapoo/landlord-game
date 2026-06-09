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

# ── Tenant Event System ────────────────────────────────────────────────────────
# One event can fire per day when the global roll succeeds.
# Chance = 35% base + 1% per tenant (capped at 90%).
#
# To add a new event type:
#   1. Add an entry here with a unique "key", a "weight" (higher = more common),
#      a "type" string, and a display "name".
#   2. Add an `elif chosen_event["type"] == "your_type":` block in api_advance()
#      to handle the logic and append to new_repairs / events as needed.
TENANT_EVENTS = [
    # ── Repair ────────────────────────────────────────────────────────────────
    # weight 10 keeps repairs at ~8% of all events across the full list
    {"key": "repair", "weight": 10, "type": "repair", "name": "Repair Needed"},

    # ── Morale-choice events ───────────────────────────────────────────────────
    # Player sees a prompt and chooses Agree or Decline.
    # Agree: morale_gain applied; damage_chance to lose damage_pts condition.
    # Decline: morale drops 5-10 (handled in api_tenant_event_respond).
    # To add: give unique key, type="morale_choice", fill fields, add message
    #         logic in the advance loop's morale_choice elif block if needed.
    {
        "key": "paint_room", "weight": 6, "type": "morale_choice",
        "name": "Paint Request", "icon": "🎨",
        "agree_label": "Sure, go ahead!", "decline_label": "No thanks.",
        "morale_gain": 8, "damage_chance": 0.30, "damage_pts": 25,
        "rooms": ["bedroom", "kitchen", "living room", "bathroom", "dining room"],
    },
    {
        "key": "garage_sale", "weight": 6, "type": "morale_choice",
        "name": "Garage Sale", "icon": "🏷️",
        "agree_label": "Sure, go ahead!", "decline_label": "Not at my property.",
        "morale_gain": 8, "damage_chance": 0.15, "damage_pts": 25,
    },
    {
        "key": "party", "weight": 6, "type": "morale_choice",
        "name": "Party Request", "icon": "🎉",
        "agree_label": "Sure, have fun!", "decline_label": "No parties.",
        "morale_gain": 8, "damage_chance": 0.40, "damage_pts": 25,
        "reasons": ["birthday", "promotion", "holiday", "housewarming", "New Year's Eve"],
    },
    {
        "key": "dog", "weight": 6, "type": "morale_choice",
        "name": "Dog Request", "icon": "🐶",
        "agree_label": "Sure, one dog is fine!", "decline_label": "No pets allowed.",
        "morale_gain": 8, "damage_chance": 0.20, "damage_pts": 20,
    },
    {
        "key": "cat", "weight": 6, "type": "morale_choice",
        "name": "Cat Request", "icon": "🐱",
        "agree_label": "Sure, a cat is fine!", "decline_label": "No pets allowed.",
        "morale_gain": 6, "damage_chance": 0.10, "damage_pts": 15,
    },
    {
        "key": "garden", "weight": 6, "type": "morale_choice",
        "name": "Garden Request", "icon": "🌱",
        "agree_label": "Go for it!", "decline_label": "Let's keep the yard as-is.",
        "morale_gain": 10, "damage_chance": 0.10, "damage_pts": 10,
    },
    {
        "key": "satellite_dish", "weight": 5, "type": "morale_choice",
        "name": "Satellite Dish", "icon": "📡",
        "agree_label": "Sure, go ahead.", "decline_label": "No modifications to the roof.",
        "morale_gain": 7, "damage_chance": 0.25, "damage_pts": 20,
    },
    {
        "key": "band_practice", "weight": 5, "type": "morale_choice",
        "name": "Band Practice", "icon": "🎸",
        "agree_label": "As long as it's not too late!", "decline_label": "Not in my property.",
        "morale_gain": 8, "damage_chance": 0.35, "damage_pts": 20,
    },
    {
        "key": "home_gym", "weight": 5, "type": "morale_choice",
        "name": "Home Gym", "icon": "🏋️",
        "agree_label": "Sure, just don't damage the floors.", "decline_label": "No heavy equipment.",
        "morale_gain": 7, "damage_chance": 0.20, "damage_pts": 15,
    },
    {
        "key": "holiday_decorations", "weight": 5, "type": "morale_choice",
        "name": "Holiday Decorations", "icon": "🎃",
        "agree_label": "Sure, just take them down after.", "decline_label": "No exterior modifications.",
        "morale_gain": 6, "damage_chance": 0.10, "damage_pts": 10,
    },
    {
        "key": "fire_pit", "weight": 5, "type": "morale_choice",
        "name": "Fire Pit", "icon": "🔥",
        "agree_label": "Sure, be careful.", "decline_label": "Too much liability.",
        "morale_gain": 9, "damage_chance": 0.30, "damage_pts": 25,
    },
    {
        "key": "duck", "weight": 4, "type": "morale_choice",
        "name": "The Duck", "icon": "🦆",
        "agree_label": "...Fine. One duck.", "decline_label": "Absolutely not.",
        "morale_gain": 12, "damage_chance": 0.20, "damage_pts": 15,
    },
    {
        "key": "taco_tuesday", "weight": 5, "type": "morale_choice",
        "name": "Taco Tuesday", "icon": "🌮",
        "agree_label": "Sounds delicious, go ahead!", "decline_label": "Keep the gatherings small.",
        "morale_gain": 7, "damage_chance": 0.20, "damage_pts": 15,
    },
    {
        "key": "feng_shui", "weight": 4, "type": "morale_choice",
        "name": "Feng Shui Rearrangement", "icon": "🔮",
        "agree_label": "Sure, rearrange whatever you like.", "decline_label": "Please leave the fixtures alone.",
        "morale_gain": 6, "damage_chance": 0.40, "damage_pts": 20,
    },
    {
        "key": "backyard_chicken", "weight": 4, "type": "morale_choice",
        "name": "Backyard Chickens", "icon": "🦃",
        "agree_label": "Only if they stay in the yard.", "decline_label": "No livestock.",
        "morale_gain": 10, "damage_chance": 0.50, "damage_pts": 30,
    },
    {
        "key": "candles", "weight": 5, "type": "morale_choice",
        "name": "Candle Obsession", "icon": "🕯️",
        "agree_label": "Sure, just be careful!", "decline_label": "Too much of a fire risk.",
        "morale_gain": 5, "damage_chance": 0.35, "damage_pts": 20,
    },
    {
        "key": "bulletin_board", "weight": 4, "type": "morale_choice",
        "name": "Conspiracy Bulletin Board", "icon": "🛸",
        "agree_label": "...Sure.", "decline_label": "I'd rather not have holes in my walls.",
        "morale_gain": 4, "damage_chance": 0.15, "damage_pts": 10,
    },
    {
        "key": "dartboard", "weight": 5, "type": "morale_choice",
        "name": "Dart Board", "icon": "🎯",
        "agree_label": "Sure, sounds fun.", "decline_label": "Not on my walls.",
        "morale_gain": 5, "damage_chance": 0.45, "damage_pts": 15,
    },

    # ── Morale-auto events ─────────────────────────────────────────────────────
    # These fire silently — no modal. The morale change is applied automatically
    # and a note appears in the advance events list.
    # To add: give unique key, type="morale_auto", set morale_delta and message.
    {
        "key": "noise_complaint", "weight": 5, "type": "morale_auto",
        "name": "Noise Complaint", "icon": "😤",
        "morale_delta": -8,
        "message": "is being kept up by noisy neighbors",
    },
    {
        "key": "rainy_mood", "weight": 5, "type": "morale_auto",
        "name": "Rainy Day Mood", "icon": "🌧️",
        "morale_delta": -5,
        "message": "is having a rough week for no particular reason",
    },
    {
        "key": "great_month", "weight": 5, "type": "morale_auto",
        "name": "Great Month", "icon": "🎉",
        "morale_delta": 10,
        "message": "says they're really loving it here",
    },
    {
        "key": "new_job", "weight": 5, "type": "morale_auto",
        "name": "New Job", "icon": "📦",
        "morale_delta": 12,
        "message": "just got a new job and is thrilled",
    },
    {
        "key": "tight_month", "weight": 5, "type": "morale_auto",
        "name": "Tight Month", "icon": "💸",
        "morale_delta": -6,
        "message": "mentioned money is tight this month",
    },
    # ── Add future events below this line ─────────────────────────────────────
]

def _pick_weighted_event(event_list):
    """Weighted-random pick from a list of events."""
    total = sum(e["weight"] for e in event_list)
    r, cumulative = random.uniform(0, total), 0
    for ev in event_list:
        cumulative += ev["weight"]
        if r <= cumulative:
            return ev
    return event_list[-1]

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
    "ev_charger": {"name": "EV Charging Station",  "icon": "⚡", "cost":  4_000, "rent_bonus": 20,  "value_bonus":  5_000, "days":  1, "desc": "Level 2 EV charger — big draw for modern renters"},
    "smarthome":  {"name": "Smart Home Package",   "icon": "📱", "cost":  5_500, "rent_bonus": 32,  "value_bonus":  7_000, "days":  1, "desc": "Security cameras, smart thermostat & lighting automation"},
    "deck":       {"name": "Deck & Patio",         "icon": "🪵", "cost":  9_000, "rent_bonus": 45,  "value_bonus": 11_000, "days":  2, "desc": "Hardwood deck with built-in seating area"},
    "hot_tub":    {"name": "Hot Tub / Spa",        "icon": "🛁", "cost": 12_000, "rent_bonus": 60,  "value_bonus": 13_000, "days":  3, "desc": "Outdoor hot tub with privacy fencing"},
    "garage":     {"name": "2-Car Garage",         "icon": "🚗", "cost": 16_000, "rent_bonus": 85,  "value_bonus": 20_000, "days":  5, "desc": "Attached 2-car garage with automatic door"},
    "solar":      {"name": "Solar Panel Array",    "icon": "☀️", "cost": 19_000, "rent_bonus": 65,  "value_bonus": 22_000, "days":  7, "desc": "Rooftop solar — lower bills, higher tenant appeal"},
    "basement":   {"name": "Finished Basement",    "icon": "🏗️", "cost": 22_000, "rent_bonus": 130, "value_bonus": 27_000, "days":  8, "desc": "Fully finished basement — extra living space"},
    "pool":       {"name": "Swimming Pool",        "icon": "🏊", "cost": 28_000, "rent_bonus": 175, "value_bonus": 32_000, "days": 10, "desc": "Inground pool with full landscaping package"},
    "adu":        {"name": "Guest House / ADU",    "icon": "🏡", "cost": 48_000, "rent_bonus": 325, "value_bonus": 55_000, "days": 14, "desc": "Detached accessory dwelling unit — major value add"},
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

# Player homes — each tier increases max energy and daily recharge by 2
PLAYER_HOMES = [
    {"key": "moms_basement", "name": "The Shed",         "icon": "🛖",  "cost":       0, "max_energy": 10, "recharge":  2, "desc": "Your in-laws' backyard shed. No rent, no dignity."},
    {"key": "studio_apt",    "name": "Studio Apartment","icon": "🏠",  "cost":   80_000, "max_energy": 12, "recharge":  4, "desc": "Your own place — finally."},
    {"key": "starter_house", "name": "Starter House",   "icon": "🏡",  "cost":  150_000, "max_energy": 14, "recharge":  6, "desc": "A real house with a yard. Moving up!"},
    {"key": "modern_condo",  "name": "Modern Condo",    "icon": "🏢",  "cost":  200_000, "max_energy": 16, "recharge":  8, "desc": "High-rise living with city views."},
    {"key": "suburban_home", "name": "Suburban Home",   "icon": "🏘️",  "cost":  500_000, "max_energy": 18, "recharge": 10, "desc": "Quiet neighborhood, big garage."},
    {"key": "luxury_villa",  "name": "Mansion",         "icon": "🏛️",  "cost":1_000_000, "max_energy": 20, "recharge": 12, "desc": "Sprawling estate. You've made it."},
    {"key": "mansion",       "name": "Castle",          "icon": "🏰",  "cost":10_000_000, "max_energy": 30, "recharge": 30, "desc": "Absolute excess. Full energy, every single day."},
]

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

# ── Special tenant: The Phil ──────────────────────────────────────────────────
# Only one Phil can rent at a time. After he leaves a 4-season (112-day)
# cooldown prevents him from reappearing in any applicant pool.
# He never damages property, always pays, and actively improves the place.
THE_PHIL = {
    "name":          "The Phil",
    "icon":          "🔱",
    "pay_chance":    1.00,
    "damage_chance": 0.00,
    "stay_min":      56,    # 2 seasons min
    "stay_max":      112,   # 1 year max
    "is_phil":       True,
    "damage_label":  "None ✨",
    "desc":          "Mysterious. Immaculate. He just… fixes things.",
}

# stay_min / stay_max are in DAYS
TENANT_PROFILES = [
    # ── Original profiles ──────────────────────────────────────────────────────
    {"name": "Young Professional", "icon": "💼", "pay_chance": 0.97, "damage_chance": 0.03, "stay_min": 60,  "stay_max": 180},
    {"name": "College Student",    "icon": "🎓", "pay_chance": 0.82, "damage_chance": 0.12, "stay_min": 30,  "stay_max": 90},
    {"name": "Retired Couple",     "icon": "👴", "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365},
    {"name": "Young Family",       "icon": "👨‍👩‍👧", "pay_chance": 0.93, "damage_chance": 0.07, "stay_min": 90,  "stay_max": 270},
    {"name": "Freelancer",         "icon": "💻", "pay_chance": 0.85, "damage_chance": 0.05, "stay_min": 45,  "stay_max": 120},
    {"name": "Section 8",          "icon": "🏛️", "pay_chance": 0.95, "damage_chance": 0.08, "stay_min": 60,  "stay_max": 180},
    # ── Expanded profiles ──────────────────────────────────────────────────────
    {"name": "Aspiring Chef",      "icon": "👨‍🍳", "pay_chance": 0.91, "damage_chance": 0.14, "stay_min": 60,  "stay_max": 180},
    {"name": "The Minimalist",     "icon": "🧘", "pay_chance": 0.98, "damage_chance": 0.01, "stay_min": 90,  "stay_max": 240},
    {"name": "Nurse (Night Shift)","icon": "🩺", "pay_chance": 0.96, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270},
    {"name": "Grad Student",       "icon": "📚", "pay_chance": 0.79, "damage_chance": 0.06, "stay_min": 60,  "stay_max": 120},
    {"name": "Single Parent",      "icon": "🧑‍👧", "pay_chance": 0.90, "damage_chance": 0.06, "stay_min": 90,  "stay_max": 300},
    {"name": "Social Butterfly",   "icon": "🦋", "pay_chance": 0.88, "damage_chance": 0.11, "stay_min": 45,  "stay_max": 120},
    {"name": "Veteran",            "icon": "🪖", "pay_chance": 0.99, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365},
    {"name": "Remote Worker",      "icon": "🖥️", "pay_chance": 0.94, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 270},
    {"name": "The Artist",         "icon": "🎨", "pay_chance": 0.80, "damage_chance": 0.15, "stay_min": 60,  "stay_max": 150},
    {"name": "Doomsday Prepper",   "icon": "🥫", "pay_chance": 0.92, "damage_chance": 0.09, "stay_min": 120, "stay_max": 365},
    {"name": "Trust Fund Kid",     "icon": "🛍️", "pay_chance": 0.99, "damage_chance": 0.13, "stay_min": 30,  "stay_max": 90},
    {"name": "Teacher",            "icon": "🍎", "pay_chance": 0.93, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270},
    {"name": "Outdoorsy Type",     "icon": "🏕️", "pay_chance": 0.95, "damage_chance": 0.02, "stay_min": 45,  "stay_max": 150},
    {"name": "Band Member",        "icon": "🎸", "pay_chance": 0.78, "damage_chance": 0.16, "stay_min": 30,  "stay_max": 90},
    {"name": "Influencer",         "icon": "📱", "pay_chance": 0.90, "damage_chance": 0.10, "stay_min": 30,  "stay_max": 90},
    {"name": "The Handyman",       "icon": "🔧", "pay_chance": 0.91, "damage_chance": 0.01, "stay_min": 90,  "stay_max": 240},
]

# ── Game Logic ─────────────────────────────────────────────────────────────────

def get_upgrade_quality(upg_val):
    """Handle both old format (int) and new format (dict with quality+day)."""
    return upg_val["quality"] if isinstance(upg_val, dict) else upg_val

def contractor_days(contractor_key, energy_cost):
    """How many days a contractor takes based on tier and job difficulty (energy_cost 1-4)."""
    if contractor_key == "budget":
        return 1
    if contractor_key == "standard":
        return 2 if energy_cost <= 2 else (3 if energy_cost == 3 else 4)
    # premium
    return 4 if energy_cost <= 2 else (5 if energy_cost == 3 else 6)

def calc_initial_morale(prop, weekly_rent):
    """Starting morale 0-100 based on rent vs fair and property condition at move-in."""
    fair  = max(1, calc_fair_weekly_rent(prop))
    ratio = weekly_rent / fair
    # rent component: 100 at 50%-of-fair, 50 at fair, 0 at 150%+ of fair
    rent_cmp = max(0.0, min(100.0, (1.5 - ratio) * 100))
    # condition component: 0-100 scaled from 0-MAX_CONDITION
    cond_cmp = (prop["condition"] / MAX_CONDITION) * 100
    return int(round(0.5 * rent_cmp + 0.5 * cond_cmp))

def clamp_morale(t):
    """Clamp tenant morale to 0-100 in-place."""
    t["morale"] = max(0, min(100, t.get("morale", 50)))

def get_player_home(s):
    """Return the PLAYER_HOMES dict for the player's current home."""
    key = s.get("player_home", "moms_basement")
    return next((h for h in PLAYER_HOMES if h["key"] == key), PLAYER_HOMES[0])

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
             "premium_upgrades": [], "squatter": None, "vacant_since": 1,
             "pending_reno": None, "pending_premium": None,
             "scheduled_reno": None, "scheduled_premium": None,
             "tenant": None, "days_rented": 0,
             "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}
    prop["purchase_price"] = int(calc_market_value(prop) * random.uniform(0.88, 1.06))
    return prop

def make_starter_home():
    return {"id": 1, "type": "Bungalow", "neighborhood": "Eastside",
            "bedrooms": 2, "bathrooms": 1, "sqft": 820, "condition": 61,
            "upgrades": {}, "premium_upgrades": [], "squatter": None, "vacant_since": 1,
            "pending_reno": None, "pending_premium": None,
            "scheduled_reno": None, "scheduled_premium": None,
            "tenant": None, "days_rented": 0,
            "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}

def new_game():
    starter = make_starter_home()
    state = {
        "cash": STARTING_CASH, "day": 1, "next_id": 2,
        "properties": [starter], "market": [], "log": [],
        "applicants_cache": {},
        "last_bank_day": 1,
        "energy": PLAYER_HOMES[0]["max_energy"],
        "player_home": "moms_basement",
        "jobs": generate_jobs(),
        "redeemed_codes": [],
        "squatter_count": 0,
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
    home = get_player_home(s)
    weekly_income = sum(p["tenant"]["rent"] for p in s["properties"] if p.get("tenant"))
    return jsonify({
        "cash":            s["cash"],
        "day":             s["day"],
        "energy":          s.get("energy", home["max_energy"]),
        "max_energy":      home["max_energy"],
        "energy_recharge": home["recharge"],
        "player_home":     s.get("player_home", "moms_basement"),
        "jobs":            s.get("jobs", []),
        "net_worth":       s["cash"] + sum(calc_market_value(p) for p in s["properties"]),
        "weekly_income":   weekly_income,
        "property_count":  len(s["properties"]),
        "properties":      [enrich(p, s["day"]) for p in s["properties"]],
        "log":             s["log"][-40:],
        "bank":            s.get("bank", {"savings": 0, "loans": [], "next_loan_id": 1}),
        "savings_tier":    savings_tier(s.get("bank", {}).get("savings", 0)),
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
    prop["vacant_since"] = s["day"]   # start tracking vacancy from purchase day
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
    pending_key = (prop.get("pending_reno") or {}).get("upgrade_key")
    for key, upg in UPGRADES.items():
        if key == pending_key:
            continue   # shown separately as in-progress
        upg_val = prop.get("upgrades", {}).get(key)
        if upg_val is not None:
            quality   = get_upgrade_quality(upg_val)
            remaining = upgrade_cooldown_remaining(upg_val, current_day)
            tier_key  = score_to_tier(quality)["key"]
            if remaining > 0:
                on_cooldown.append({**upg, "key": key, "quality": quality,
                                    "quality_tier": tier_key, "days_remaining": remaining})
            else:
                costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
                available.append({**upg, "key": key, "costs": costs,
                                  "prev_quality_tier": tier_key})
        else:
            costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
            available.append({**upg, "key": key, "costs": costs})
    return jsonify({"available": available, "on_cooldown": on_cooldown,
                    "pending_reno": prop.get("pending_reno"),
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
    if prop.get("squatter"):
        return jsonify({"error": "Remove squatters first"}), 400
    if prop.get("pending_reno"):
        return jsonify({"error": "A renovation is already in progress"}), 400
    upgrade_key = data["upgrade_key"]
    existing    = prop.get("upgrades", {}).get(upgrade_key)
    remaining   = upgrade_cooldown_remaining(existing, s["day"]) if existing is not None else 0
    if remaining > 0:
        return jsonify({"error": f"On cooldown — {remaining} days remaining"}), 400
    upg  = UPGRADES[upgrade_key]
    cont = CONTRACTORS[data["contractor_key"]]
    cost = int(upg["base_cost"] * cont["cost_mult"])
    if cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    quality      = random.randint(cont["q_min"], cont["q_max"])
    tier         = score_to_tier(quality)
    cond_change  = tier_cond_change(tier)
    duration     = contractor_days(data["contractor_key"], upg.get("energy_cost", 1))
    complete_day = s["day"] + duration
    s["cash"] -= cost
    prop["pending_reno"] = {
        "upgrade_key":  upgrade_key,
        "contractor":   data["contractor_key"],
        "quality":      quality,
        "tier_key":     tier["key"],
        "cond_change":  cond_change,
        "complete_day": complete_day,
        "duration":     duration,
        "name":         upg["name"],
        "icon":         upg["icon"],
    }
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"{upg['name']} started at {prop['type']} in {prop['neighborhood']} — done in {duration} day{'s' if duration > 1 else ''}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "duration": duration, "complete_day": complete_day,
                    "contractor_name": cont["name"]})

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
        installed    = prop.get("premium_upgrades", [])
        pending_key  = (prop.get("pending_premium") or {}).get("upgrade_key")
        catalog = [
            {**v, "key": k, "installed": k in installed}
            for k, v in PREMIUM_UPGRADES.items()
            if k != pending_key
        ]
        return jsonify({"catalog": catalog, "installed": installed,
                        "pending_premium":   prop.get("pending_premium"),
                        "scheduled_premium": prop.get("scheduled_premium")})
    if upgrade_key not in PREMIUM_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    if prop.get("squatter"):
        return jsonify({"error": "Remove squatters before installing upgrades"}), 400
    if prop.get("pending_reno"):
        return jsonify({"error": "Wait for the current renovation to finish first"}), 400
    if prop.get("pending_premium"):
        return jsonify({"error": "A premium upgrade is already in progress"}), 400

    installed = prop.get("premium_upgrades", [])
    if upgrade_key in installed:
        return jsonify({"error": "Already installed"}), 400

    upg  = PREMIUM_UPGRADES[upgrade_key]
    cost = upg["cost"]
    if s["cash"] < cost:
        return jsonify({"error": f"Need ${cost:,} — you have ${int(s['cash']):,}"}), 400

    s["cash"] -= cost
    complete_day = s["day"] + upg["days"]
    prop["pending_premium"] = {
        "upgrade_key":  upgrade_key,
        "complete_day": complete_day,
        "days":         upg["days"],
        "name":         upg["name"],
        "icon":         upg["icon"],
    }
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"{upg['name']} installation started at {prop['type']} in {prop['neighborhood']} — done in {upg['days']} day{'s' if upg['days'] > 1 else ''}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "duration": upg["days"], "complete_day": complete_day, "name": upg["name"]})

@app.route('/api/property/<int:pid>/schedule_reno', methods=['POST'])
def api_schedule_reno(pid):
    """Schedule a renovation to start when the tenant has a maintenance window."""
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    if not prop.get("tenant"):
        return jsonify({"error": "No tenant — just renovate normally"}), 400
    if prop.get("squatter"):
        return jsonify({"error": "Remove squatters first"}), 400
    if prop.get("pending_reno"):
        return jsonify({"error": "Renovation already in progress"}), 400
    if prop.get("scheduled_reno"):
        return jsonify({"error": "A renovation is already scheduled — wait for it to begin"}), 400

    upgrade_key    = data.get("upgrade_key")
    contractor_key = data.get("contractor_key")
    start_day      = data.get("start_day")

    if upgrade_key not in UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    if contractor_key not in CONTRACTORS:
        return jsonify({"error": "Unknown contractor"}), 400

    existing  = prop.get("upgrades", {}).get(upgrade_key)
    remaining = upgrade_cooldown_remaining(existing, s["day"]) if existing is not None else 0
    if remaining > 0:
        return jsonify({"error": f"On cooldown — {remaining} days remaining"}), 400

    upg  = UPGRADES[upgrade_key]
    cont = CONTRACTORS[contractor_key]
    cost = int(upg["base_cost"] * cont["cost_mult"])
    if cost > s["cash"]:
        return jsonify({"error": f"Need ${cost:,} — you have ${int(s['cash']):,}"}), 400

    # Validate/clamp start_day to 1-28 days out
    if not start_day or not (s["day"] + 1 <= start_day <= s["day"] + 28):
        start_day = s["day"] + random.randint(1, 28)

    quality     = random.randint(cont["q_min"], cont["q_max"])
    tier        = score_to_tier(quality)
    cond_change = tier_cond_change(tier)
    duration    = contractor_days(contractor_key, upg.get("energy_cost", 1))

    s["cash"] -= cost
    prop["scheduled_reno"] = {
        "upgrade_key":    upgrade_key,
        "contractor_key": contractor_key,
        "quality":        quality,
        "tier_key":       tier["key"],
        "cond_change":    cond_change,
        "start_day":      start_day,
        "duration":       duration,
        "name":           upg["name"],
        "icon":           upg["icon"],
        "cost":           cost,
    }
    days_out = start_day - s["day"]
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"{upg['name']} scheduled at {prop['type']} in {prop['neighborhood']} — contractors arrive in {days_out} day{'s' if days_out != 1 else ''}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "start_day": start_day, "duration": duration, "name": upg["name"]})


@app.route('/api/property/<int:pid>/schedule_premium', methods=['POST'])
def api_schedule_premium(pid):
    """Schedule a premium upgrade to start when the tenant has a maintenance window."""
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    if not prop.get("tenant"):
        return jsonify({"error": "No tenant — just install normally"}), 400
    if prop.get("squatter"):
        return jsonify({"error": "Remove squatters first"}), 400
    if prop.get("pending_premium"):
        return jsonify({"error": "Premium upgrade already in progress"}), 400
    if prop.get("scheduled_premium"):
        return jsonify({"error": "A premium upgrade is already scheduled"}), 400

    upgrade_key = data.get("upgrade_key")
    start_day   = data.get("start_day")

    if not upgrade_key or upgrade_key not in PREMIUM_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    if upgrade_key in prop.get("premium_upgrades", []):
        return jsonify({"error": "Already installed"}), 400

    upg  = PREMIUM_UPGRADES[upgrade_key]
    cost = upg["cost"]
    if cost > s["cash"]:
        return jsonify({"error": f"Need ${cost:,} — you have ${int(s['cash']):,}"}), 400

    # Validate/clamp start_day to 1-28 days out
    if not start_day or not (s["day"] + 1 <= start_day <= s["day"] + 28):
        start_day = s["day"] + random.randint(1, 28)

    s["cash"] -= cost
    prop["scheduled_premium"] = {
        "upgrade_key": upgrade_key,
        "start_day":   start_day,
        "days":        upg["days"],
        "name":        upg["name"],
        "icon":        upg["icon"],
        "cost":        cost,
    }
    days_out = start_day - s["day"]
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"{upg['name']} scheduled at {prop['type']} in {prop['neighborhood']} — workers arrive in {days_out} day{'s' if days_out != 1 else ''}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "start_day": start_day, "name": upg["name"]})


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
        # Possibly inject The Phil — only if nobody else has him and no cooldown
        phil_active   = any(p.get("tenant", {}).get("is_phil") for p in s["properties"])
        phil_cooldown = s.get("phil_cooldown_until", 0) > s["day"]
        if not phil_active and not phil_cooldown and random.random() < 0.20:
            applicants.append({**THE_PHIL, "idx": len(applicants)})
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

    initial_morale = calc_initial_morale(prop, weekly_rent)
    prop["tenant"] = {
        **t,
        "rent":            weekly_rent,
        "fair_rent":       fair_rent,
        "rent_tier":       tier["tier"],
        "pay_chance":      pay_chance,
        "damage_chance":   dmg_chance,
        "next_rent_day":   s["day"] + 7,
        "lease_end_day":   s["day"] + stay_days,
        "morale":          initial_morale,
        "recent_events":   [],   # {key, day} — prevents same event repeating within a season
    }
    # Phil-specific initialisation
    if t.get("is_phil"):
        prop["tenant"]["next_phil_work_day"] = s["day"] + 7
        prop["tenant"]["morale"] = 100
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
    if prop["tenant"].get("is_phil"):
        s["phil_cooldown_until"] = s["day"] + DAYS_PER_SEASON * 4
    s["cash"] -= fee
    prop["tenant"] = None
    prop["vacant_since"] = s["day"]
    s["log"].append({"day": s["day"], "type": "evict",
        "text": f"Evicted {name} from {prop['type']} in {prop['neighborhood']} ($1,500 legal fees)"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/advance', methods=['POST'])
def api_advance():
    data     = request.json
    days     = max(1, min(int(data.get("days", 1)), 30))
    s           = load()
    events             = []
    new_repairs        = []
    new_morale_events  = []
    new_renewal_offers = []
    rent_log           = {}   # prop_id -> summary dict
    squatter_spawned   = False

    for d in range(days):
        current_day       = s["day"] + d + 1
        early_exit_happened = False   # only one tenant leaves early per day

        for prop in s["properties"]:
            if not prop.get("tenant"):
                continue
            t   = prop["tenant"]
            pid = prop["id"]

            # Waiting on player's renewal response — skip all processing
            if t.get("renewal_pending"):
                continue

            # Lease end — 50% chance the tenant offers to renew
            if current_day >= t.get("lease_end_day", 999999):
                if random.random() < 0.50:
                    new_stay = random.randint(t.get("stay_min", 60), t.get("stay_max", 180))
                    t["renewal_pending"]   = True
                    t["renewal_stay_days"] = new_stay
                    new_renewal_offers.append({
                        "prop_id":        prop["id"],
                        "prop_name":      f"{prop['type']} — {prop['neighborhood']}",
                        "tenant_name":    t["name"],
                        "tenant_icon":    t.get("icon", "👤"),
                        "rent":           t["rent"],
                        "new_stay_days":  new_stay,
                        "missed_payments": t.get("missed_payments", 0),
                        "morale":         t.get("morale", 50),
                    })
                    events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                   "text": f"🔄 {t['name']}'s lease ended — they want to renew! (respond below)",
                                   "type": "info"})
                else:
                    name = t["name"]
                    if t.get("is_phil"):
                        s["phil_cooldown_until"] = current_day + DAYS_PER_SEASON * 4
                    prop["tenant"] = None
                    prop["vacant_since"] = current_day
                    events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"{name}'s lease ended — moved out", "type": "warning"})
                    s["log"].append({"day": current_day, "type": "info",
                        "text": f"{name} moved out of {prop['type']} in {prop['neighborhood']}"})
                continue

            # Morale-based early exit — kicks in below 20%, one tenant max per day
            morale = t.get("morale", 50)
            if morale < 20 and not early_exit_happened:
                if   morale <= 1:  exit_chance = 0.90
                elif morale <= 4:  exit_chance = 0.50
                elif morale <= 9:  exit_chance = 0.30
                elif morale <= 14: exit_chance = 0.20
                else:              exit_chance = 0.15   # 15-19
                if random.random() < exit_chance:
                    name = t["name"]
                    prop["tenant"]       = None
                    prop["vacant_since"] = current_day
                    early_exit_happened  = True
                    events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"😤 {name} broke their lease early — morale too low",
                                    "type": "negative"})
                    s["log"].insert(0, {"day": current_day, "type": "warning",
                        "text": f"{name} left {prop['type']} in {prop['neighborhood']} early — morale was {morale}%"})
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
                    t["missed_payments"] = t.get("missed_payments", 0) + 1

            # ── The Phil's special effects ─────────────────────────────────
            if t.get("is_phil"):
                # Passive: condition +1 every day Phil is here
                prop["condition"] = min(MAX_CONDITION, prop["condition"] + 1)

                # Weekly: 25% chance to do a renovation or premium upgrade
                if current_day >= t.get("next_phil_work_day", 999999):
                    t["next_phil_work_day"] = current_day + 7
                    if random.random() < 0.25:
                        avail_upgrades  = [k for k in UPGRADES         if k not in prop.get("upgrades", {})]
                        avail_premiums  = [k for k in PREMIUM_UPGRADES if k not in prop.get("premium_upgrades", [])]
                        all_work = [("u", k) for k in avail_upgrades] + [("p", k) for k in avail_premiums]
                        if all_work:
                            wtype, wkey = random.choice(all_work)
                            if wtype == "u":
                                quality     = random.randint(80, 100)
                                tier_grade  = next(tr for tr in TIER_GRADES if tr["min_score"] <= quality <= tr["max_score"])
                                cond_change = tier_cond_change(tier_grade)
                                prop.setdefault("upgrades", {})[wkey] = {"quality": quality, "day": current_day}
                                prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_change))
                                upg = UPGRADES[wkey]
                                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"🔱 The Phil did: {upg['icon']} {upg['name']} — Grade {tier_grade['key']}!", "type": "positive"})
                                s["log"].insert(0, {"day": current_day, "type": "renovate",
                                    "text": f"The Phil completed {upg['name']} at {prop['type']} in {prop['neighborhood']} — Grade {tier_grade['key']}"})
                            else:
                                prop.setdefault("premium_upgrades", []).append(wkey)
                                pu = PREMIUM_UPGRADES[wkey]
                                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"🔱 The Phil installed: {pu['icon']} {pu['name']}!", "type": "positive"})
                                s["log"].insert(0, {"day": current_day, "type": "upgrade",
                                    "text": f"The Phil installed {pu['name']} at {prop['type']} in {prop['neighborhood']}"})
                        else:
                            # Everything's already done — Phil does a deep clean
                            prop["condition"] = min(MAX_CONDITION, prop["condition"] + 10)
                            events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": "🔱 The Phil deep-cleaned everything — condition +10!", "type": "positive"})

            prop["days_rented"] = prop.get("days_rented", 0) + 1

        # ── Global tenant event roll ───────────────────────────────────────────
        # 35% base chance + 1% per tenant (capped at 90%) that one event fires.
        # Each event type has a weight; same event can't repeat for a tenant within a season.
        # The Phil is excluded — he handles his own improvements separately.
        # To add a new event: add to TENANT_EVENTS and add an elif handler below.
        tenant_props = [p for p in s["properties"] if p.get("tenant") and not p["tenant"].get("is_phil")]
        tenant_count = len(tenant_props)
        if tenant_count > 0:
            event_chance = min(0.35 + 0.01 * tenant_count, 0.90)
            if random.random() < event_chance:
                target_prop = random.choice(tenant_props)
                t           = target_prop["tenant"]

                # Filter out events used by this tenant within the last season
                recent_keys  = {e["key"] for e in t.get("recent_events", [])
                                if current_day - e["day"] < DAYS_PER_SEASON}
                valid_events = [e for e in TENANT_EVENTS if e["key"] not in recent_keys]

                if valid_events:
                    chosen_event = _pick_weighted_event(valid_events)

                    # Record event on tenant; trim entries older than 2 seasons
                    t.setdefault("recent_events", []).append(
                        {"key": chosen_event["key"], "day": current_day})
                    t["recent_events"] = [e for e in t["recent_events"]
                                          if current_day - e["day"] < DAYS_PER_SEASON * 2]

                    if chosen_event["type"] == "repair":
                        rt = random.choice(REPAIR_TYPES)
                        target_prop["condition"] = max(0, target_prop["condition"] - 2)
                        new_repairs.append({
                            "id":          f"r{current_day}_{target_prop['id']}",
                            "prop_id":     target_prop["id"],
                            "prop_name":   f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "repair_type": rt,
                            "costs":       {k: int(rt["base_cost"] * c["cost_mult"])
                                            for k, c in CONTRACTORS.items()},
                        })

                    elif chosen_event["type"] == "morale_choice":
                        ev_data = {
                            "key":          chosen_event["key"],
                            "name":         chosen_event["name"],
                            "icon":         chosen_event.get("icon", "💬"),
                            "prop_id":      target_prop["id"],
                            "prop_name":    f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "morale_gain":  chosen_event["morale_gain"],
                            "damage_chance":chosen_event["damage_chance"],
                            "damage_pts":   chosen_event["damage_pts"],
                            "agree_label":  chosen_event["agree_label"],
                            "decline_label":chosen_event["decline_label"],
                        }
                        if chosen_event["key"] == "paint_room":
                            room = random.choice(chosen_event["rooms"])
                            ev_data["message"] = f"Your tenant wants to paint the {room}."
                        elif chosen_event["key"] == "garage_sale":
                            ev_data["message"] = "Your tenant wants to host a garage sale."
                        elif chosen_event["key"] == "party":
                            reason = random.choice(chosen_event["reasons"])
                            ev_data["message"] = f"Your tenant wants to throw a party for their {reason}."
                        elif chosen_event["key"] == "dog":
                            ev_data["message"] = "Your tenant wants to get a dog."
                        elif chosen_event["key"] == "cat":
                            ev_data["message"] = "Your tenant wants to get a cat."
                        elif chosen_event["key"] == "garden":
                            ev_data["message"] = "Your tenant wants to start a garden in the backyard."
                        elif chosen_event["key"] == "satellite_dish":
                            ev_data["message"] = "Your tenant wants to install a satellite dish on the roof."
                        elif chosen_event["key"] == "band_practice":
                            ev_data["message"] = "Your tenant wants to host band practice at the property."
                        elif chosen_event["key"] == "home_gym":
                            ev_data["message"] = "Your tenant wants to set up a home gym with heavy equipment."
                        elif chosen_event["key"] == "holiday_decorations":
                            ev_data["message"] = "Your tenant wants to put up holiday decorations outside."
                        elif chosen_event["key"] == "fire_pit":
                            ev_data["message"] = "Your tenant wants to set up a fire pit in the backyard."
                        elif chosen_event["key"] == "duck":
                            ev_data["message"] = "Your tenant wants to keep a duck. Just one duck, they promise."
                        elif chosen_event["key"] == "taco_tuesday":
                            ev_data["message"] = "Your tenant wants to host a weekly Taco Tuesday with friends."
                        elif chosen_event["key"] == "feng_shui":
                            ev_data["message"] = "Your tenant wants to rearrange everything according to feng shui."
                        elif chosen_event["key"] == "backyard_chicken":
                            ev_data["message"] = "Your tenant wants to keep backyard chickens."
                        elif chosen_event["key"] == "candles":
                            ev_data["message"] = "Your tenant has developed a serious candle obsession."
                        elif chosen_event["key"] == "bulletin_board":
                            ev_data["message"] = "Your tenant wants to mount a large bulletin board on the wall."
                        elif chosen_event["key"] == "dartboard":
                            ev_data["message"] = "Your tenant wants to mount a dartboard on the wall."
                        else:
                            ev_data["message"] = f"Your tenant has a request: {chosen_event['name']}."
                        new_morale_events.append(ev_data)
                        # Also show a line in the advance events list so the player
                        # can see the request even before clicking "Respond"
                        events.append({
                            "prop": ev_data["prop_name"],
                            "text": f"{chosen_event.get('icon','💬')} {ev_data['message']} — tap below to respond",
                            "type": "request",
                        })

                    elif chosen_event["type"] == "morale_auto":
                        # Auto events: apply morale silently, show in advance events list
                        delta = chosen_event.get("morale_delta", 0)
                        icon  = chosen_event.get("icon", "💬")
                        tenant_name = t.get("name", "Your tenant")
                        msg   = chosen_event.get("message", "Something happened with your tenant.")
                        old_morale = t.get("morale", 50)
                        t["morale"] = max(0, min(100, old_morale + delta))
                        direction  = "▲" if delta > 0 else "▼"
                        events.append({
                            "prop": f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "text": f"{icon} {tenant_name} {msg}. (Morale {direction}{abs(delta)})",
                            "type": "info" if delta >= 0 else "warning",
                        })
                        s["log"].insert(0, {"day": current_day, "type": "info",
                            "text": f"{tenant_name} {msg} at {target_prop['type']} in {target_prop['neighborhood']} (morale {direction}{abs(delta)})"})
                    # ── Add handlers for future event types here ──────────────

        # Scheduled renovations — convert to pending when start_day arrives
        for prop in s["properties"]:
            sr = prop.get("scheduled_reno")
            if sr and current_day >= sr["start_day"] and not prop.get("pending_reno"):
                duration = sr["duration"]
                prop["pending_reno"] = {
                    "upgrade_key":  sr["upgrade_key"],
                    "contractor":   sr["contractor_key"],
                    "quality":      sr["quality"],
                    "tier_key":     sr["tier_key"],
                    "cond_change":  sr["cond_change"],
                    "complete_day": current_day + duration,
                    "duration":     duration,
                    "name":         sr["name"],
                    "icon":         sr["icon"],
                }
                prop["scheduled_reno"] = None
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"🔨 Contractors arrived for {sr['name']}!", "type": "info"})
                s["log"].insert(0, {"day": current_day, "type": "info",
                    "text": f"Contractors started {sr['name']} at {prop['type']} in {prop['neighborhood']}"})

        # Scheduled premium upgrades — convert to pending when start_day arrives
        for prop in s["properties"]:
            sp = prop.get("scheduled_premium")
            if sp and current_day >= sp["start_day"] and not prop.get("pending_premium"):
                prop["pending_premium"] = {
                    "upgrade_key":  sp["upgrade_key"],
                    "complete_day": current_day + sp["days"],
                    "days":         sp["days"],
                    "name":         sp["name"],
                    "icon":         sp["icon"],
                }
                prop["scheduled_premium"] = None
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"🔨 Workers arrived for {sp['name']}!", "type": "info"})
                s["log"].insert(0, {"day": current_day, "type": "info",
                    "text": f"Workers started {sp['name']} at {prop['type']} in {prop['neighborhood']}"})

        # Renovation completion
        for prop in s["properties"]:
            reno = prop.get("pending_reno")
            if reno and current_day >= reno["complete_day"]:
                prop.setdefault("upgrades", {})[reno["upgrade_key"]] = {
                    "quality": reno["quality"], "day": reno["complete_day"]}
                prop["condition"]   = max(0, min(MAX_CONDITION, prop["condition"] + reno["cond_change"]))
                prop["pending_reno"] = None
                new_val = calc_market_value(prop)
                # Tenant morale boost — they appreciate the improvement
                if prop.get("tenant"):
                    prop["tenant"]["morale"] = min(100, prop["tenant"].get("morale", 50) + 8)
                else:
                    # Vacant — protect against squatters for 3 days
                    prop["reno_protected_until"] = current_day + 3
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"✅ {reno['name']} finished! Grade {reno['tier_key']}",
                                "type": "positive"})
                s["log"].insert(0, {"day": current_day, "type": "renovate",
                    "text": f"{reno['name']} at {prop['type']} in {prop['neighborhood']} completed — grade {reno['tier_key']}, value now ${new_val:,}"})

        # Premium upgrade completion
        for prop in s["properties"]:
            pp = prop.get("pending_premium")
            if pp and current_day >= pp["complete_day"]:
                prop.setdefault("premium_upgrades", []).append(pp["upgrade_key"])
                prop["pending_premium"] = None
                new_val = calc_market_value(prop)
                # Tenant morale boost — premium upgrades impress tenants
                if prop.get("tenant"):
                    prop["tenant"]["morale"] = min(100, prop["tenant"].get("morale", 50) + 8)
                else:
                    # Vacant — protect against squatters for 3 days
                    prop["reno_protected_until"] = current_day + 3
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"✅ {pp['name']} installation complete!",
                                "type": "positive"})
                s["log"].insert(0, {"day": current_day, "type": "upgrade",
                    "text": f"{pp['name']} installed at {prop['type']} in {prop['neighborhood']} — value now ${new_val:,}"})

        # Squatter departure — natural end of stay
        for prop in s["properties"]:
            sq = prop.get("squatter")
            if sq and current_day >= sq["moved_in_day"] + sq["stay_days"]:
                prop["squatter"]     = None
                prop["vacant_since"] = current_day
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": "Squatters finally moved out on their own", "type": "positive"})
                s["log"].insert(0, {"day": current_day, "type": "info",
                    "text": f"Squatters left your {prop['type']} in {prop['neighborhood']} on their own"})

        # Squatter daily condition damage — 15% chance per squatter to drop condition 50 pts
        for prop in s["properties"]:
            if prop.get("squatter") and random.random() < 0.15:
                prop["condition"] = max(0, prop["condition"] - 50)
                s["log"].insert(0, {"day": current_day, "type": "warning",
                    "text": f"Squatters damaged your {prop['type']} in {prop['neighborhood']}!"})

        # Squatter spawning — rate drops with each past squatter event: 5% → 3% → 1%
        if not squatter_spawned:
            sq_count      = s.get("squatter_count", 0)
            spawn_chance  = 0.05 if sq_count == 0 else (0.03 if sq_count == 1 else 0.01)
            eligible = [p for p in s["properties"]
                        if not p.get("tenant") and not p.get("squatter")
                        and not p.get("pending_reno") and not p.get("pending_premium")
                        and (current_day - p.get("vacant_since", 1)) >= 3
                        and current_day > p.get("reno_protected_until", 0)]
            if eligible and random.random() < spawn_chance:
                target = random.choice(eligible)
                bribe  = int(calc_market_value(target) * 0.10)
                target["squatter"] = {
                    "moved_in_day": current_day,
                    "stay_days":    random.randint(28, 112),
                    "bribe":        bribe,
                }
                s["squatter_count"] = sq_count + 1
                events.append({
                    "type":      "squatter",
                    "prop":      f"{target['type']} — {target['neighborhood']}",
                    "text":      f"🚨 Squatters moved in! They want ${bribe:,} to leave.",
                    "prop_id":   target["id"],
                    "prop_name": f"{target['type']} — {target['neighborhood']}",
                    "bribe":     bribe,
                })
                s["log"].insert(0, {"day": current_day, "type": "warning",
                    "text": f"Squatters moved into your {target['type']} in {target['neighborhood']}!"})
                squatter_spawned = True

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

    # Restore energy (additive recharge capped at home max) and refresh jobs
    home = get_player_home(s)
    s["energy"] = min(home["max_energy"], s.get("energy", 0) + home["recharge"])
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
        "events":        events,
        "repairs":       new_repairs,
        "morale_events":  new_morale_events,
        "renewal_offers": new_renewal_offers,
    })


@app.route('/api/property/<int:pid>/renewal_respond', methods=['POST'])
def api_renewal_respond(pid):
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop or not prop.get("tenant") or not prop["tenant"].get("renewal_pending"):
        return jsonify({"error": "No pending renewal for this property"}), 400

    t = prop["tenant"]
    if data.get("agree"):
        new_stay = t.get("renewal_stay_days",
                         random.randint(t.get("stay_min", 60), t.get("stay_max", 180)))
        t["lease_end_day"]   = s["day"] + new_stay
        t["renewal_pending"] = False
        t.pop("renewal_stay_days", None)
        s["log"].append({"day": s["day"], "type": "rent",
            "text": f"{t['name']} renewed lease at {prop['type']} in {prop['neighborhood']} for {new_stay} more days"})
    else:
        name = t["name"]
        if t.get("is_phil"):
            s["phil_cooldown_until"] = s["day"] + DAYS_PER_SEASON * 4
        prop["tenant"]       = None
        prop["vacant_since"] = s["day"]
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"{name}'s renewal denied at {prop['type']} in {prop['neighborhood']} — moved out"})

    save(s)
    return jsonify({"success": True})


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
    # Tenant morale boost — they appreciate the quick fix
    if prop.get("tenant"):
        prop["tenant"]["morale"] = min(100, prop["tenant"].get("morale", 50) + 5)
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
    # Tenant morale hit — they're not happy about ignored issues
    morale_before = None
    if prop.get("tenant"):
        morale_before = prop["tenant"].get("morale", 50)
        prop["tenant"]["morale"] = max(0, morale_before - 15)
    s["log"].append({"day": s["day"], "type": "warning",
        "text": f"Ignored {rt['name'] if rt else 'repair'} at {prop['type']} in {prop['neighborhood']} — condition -{cond_loss}, tenant morale -{15 if morale_before is not None else 0}"})
    save(s)
    return jsonify({"success": True, "condition": prop["condition"], "cash": s["cash"],
                    "morale": prop["tenant"]["morale"] if prop.get("tenant") else None})

@app.route('/api/tenant_event/respond', methods=['POST'])
def api_tenant_event_respond():
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == data.get("prop_id")), None)
    if not prop or not prop.get("tenant"):
        return jsonify({"error": "Property or tenant not found"}), 404

    agree     = bool(data.get("agree"))
    event_key = data.get("event_key")
    event_cfg = next((e for e in TENANT_EVENTS if e["key"] == event_key), None)
    if not event_cfg:
        return jsonify({"error": "Unknown event"}), 400

    t                = prop["tenant"]
    condition_change = 0
    morale_change    = 0
    morale_before    = t.get("morale", 50)

    if agree:
        morale_change   = event_cfg["morale_gain"]
        t["morale"]     = min(100, t.get("morale", 50) + morale_change)
        if random.random() < event_cfg["damage_chance"]:
            condition_change    = -event_cfg["damage_pts"]
            prop["condition"]   = max(0, prop["condition"] + condition_change)
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"Agreed to {t['name']}'s {event_cfg['name']} request at {prop['type']} in {prop['neighborhood']}"
                   + (f" — caused {abs(condition_change)} pts condition damage" if condition_change else "")})
    else:
        morale_change = -random.randint(5, 10)
        t["morale"]   = max(0, morale_before + morale_change)
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"Declined {t['name']}'s {event_cfg['name']} request at {prop['type']} in {prop['neighborhood']} — morale {morale_change}"})

    save(s)
    return jsonify({
        "success":          True,
        "agree":            agree,
        "condition":        prop["condition"],
        "morale":           t.get("morale"),
        "condition_change": condition_change,
        "morale_change":    morale_change,
        "cash":             s["cash"],
    })


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

@app.route('/api/squatter/bribe', methods=['POST'])
def api_squatter_bribe():
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == data.get("prop_id")), None)
    if not prop or not prop.get("squatter"):
        return jsonify({"error": "No squatter found"}), 400
    bribe = prop["squatter"]["bribe"]
    if s["cash"] < bribe:
        return jsonify({"error": f"Not enough cash — they want ${bribe:,}"}), 400
    s["cash"] -= bribe
    prop["squatter"]     = None
    prop["vacant_since"] = s["day"]
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Paid ${bribe:,} bribe — squatters removed from {prop['type']} in {prop['neighborhood']}"})
    save(s)
    return jsonify({"success": True, "bribe_paid": bribe})

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

@app.route('/api/move_in', methods=['POST'])
def api_move_in():
    s    = load()
    data = request.json or {}
    key  = data.get("home_key", "")
    new_home = next((h for h in PLAYER_HOMES if h["key"] == key), None)
    if not new_home:
        return jsonify({"error": "Invalid home"}), 400
    current     = get_player_home(s)
    current_idx = next(i for i, h in enumerate(PLAYER_HOMES) if h["key"] == current["key"])
    new_idx     = next(i for i, h in enumerate(PLAYER_HOMES) if h["key"] == key)
    if new_idx <= current_idx:
        return jsonify({"error": "You already live somewhere better!"}), 400
    if new_home["cost"] > 0 and s["cash"] < new_home["cost"]:
        return jsonify({"error": f"Not enough cash — need ${new_home['cost']:,}"}), 400
    s["cash"] -= new_home["cost"]
    s["player_home"] = key
    # Cap current energy at new home's max (it might already be lower)
    s["energy"] = min(s.get("energy", 0), new_home["max_energy"])
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Moved into {new_home['name']}! Max energy now ⚡{new_home['max_energy']}, recharge +{new_home['recharge']}/day."})
    save(s)
    return jsonify({"success": True, "home": new_home["name"]})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
