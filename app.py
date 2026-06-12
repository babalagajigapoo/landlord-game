from flask import Flask, render_template, jsonify, request, g
import json, os, random

app = Flask(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

STARTING_CASH = 4_367

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

PROPERTY_TYPES = ["Bungalow", "Ranch House", "Colonial", "Townhouse", "Condo", "Duplex", "Mansion"]
PROPERTY_ICONS = {
    "Bungalow": "🏚️", "Ranch House": "🏠", "Colonial": "🏛️",
    "Townhouse": "🏙️", "Condo": "🏢", "Duplex": "🏘️", "Mansion": "🏰"
}

# Street names per neighborhood for address generation
HOOD_STREETS = {
    "Midtown":   ["Oak St", "Pine Ave", "Elm St", "Main St", "1st Ave", "2nd St",
                  "Market St", "Union Ave", "Canal St", "Bridge Rd", "Iron Ave", "Mill Rd"],
    "Northside": ["Cedar Rd", "Birch Lane", "Spruce Dr", "North Ave", "Ridge Rd",
                  "Valley Rd", "Hollow Rd", "Quarry Rd", "Depot Ave", "Gravel Rd"],
    "Westwood":  ["Maple Ave", "Westwood Dr", "Oak Hill Rd", "Sunset Blvd", "Park Ave",
                  "Clover Dr", "Hillcrest Rd", "Garden Way", "Pinewood Dr", "Orchard Ln"],
    "Riverside": ["Riverside Dr", "Willow Lane", "Creekside Dr", "Waterway Blvd",
                  "Bay St", "Harbor Rd", "Bluff Rd", "Brook Lane", "Cove Dr", "Tide Rd"],
    "Newbay":    ["Grand Ave", "Harbor Blvd", "Bayview Dr", "Crest Rd", "Newport Way",
                  "Marina Blvd", "Summit Dr", "Lakeshore Blvd", "Glenview Ct", "Prestige Way"],
}

# Per-neighborhood property generation config
# cond_rolls: list of (low, high, weight) — condition ranges with relative weights
HOOD_PROP_CONFIG = {
    "Midtown": {
        "types":      ["Bungalow", "Ranch House", "Condo"],
        "beds":       (1, 2),
        "baths_max":  1,
        "sqft":       (380, 820),
        "cond_rolls": [(15, 74, 50), (75, 160, 50)],   # ~50% below C
    },
    "Northside": {
        "types":      ["Bungalow", "Ranch House", "Colonial", "Condo", "Duplex"],
        "beds":       (1, 3),
        "baths_max":  2,
        "sqft":       (650, 1250),
        "cond_rolls": [(20, 74, 50), (75, 175, 50)],   # ~50% below C
    },
    "Westwood": {
        "types":      ["Ranch House", "Colonial", "Townhouse", "Duplex"],
        "beds":       (2, 4),
        "baths_max":  3,
        "sqft":       (950, 1850),
        "cond_rolls": [(30, 74, 50), (75, 200, 50)],   # ~50% below C
    },
    "Riverside": {
        "types":      ["Colonial", "Townhouse", "Condo", "Duplex"],
        "beds":       (2, 5),
        "baths_max":  3,
        "sqft":       (1300, 2700),
        "cond_rolls": [(35, 74, 50), (75, 215, 50)],   # ~50% below C
    },
    "Newbay": {
        "types":      ["Colonial", "Townhouse", "Mansion"],
        "beds":       (3, 6),
        "baths_max":  4,
        "sqft":       (2000, 5500),
        "cond_rolls": [(10, 110, 91), (113, 147, 7), (150, 185, 2)],   # mostly F–C, B very rare, A near impossible, S/S+ never
    },
}

NEIGHBORHOODS = {
    "Midtown":   {"price_mult": 0.70, "rent_mult": 0.75, "desc": "Crumbling blocks, forgotten by time", "tier": "budget"},
    "Northside": {"price_mult": 0.85, "rent_mult": 0.90, "desc": "Gritty streets, high turnover",       "tier": "budget"},
    "Westwood":  {"price_mult": 1.00, "rent_mult": 1.00, "desc": "Solid middle-class area",               "tier": "mid"},
    "Riverside": {"price_mult": 1.40, "rent_mult": 1.35, "desc": "Desirable suburb, great schools",       "tier": "premium"},
    "Newbay":    {"price_mult": 1.60, "rent_mult": 1.55, "desc": "High-demand urban core",                "tier": "premium"},
}

# ── XP / Level System ──────────────────────────────────────────────────────────
# XP_THRESHOLDS[level] = cumulative XP required to reach that level.
# Level 0 → 1 is a special trigger (guaranteed on first property sale).
# Levels 1 → 7 are earned through gameplay.
XP_THRESHOLDS         = [0, 0, 150, 450, 1050, 2250, 4750, 9750, 17250, 27250, 42250, 62250, 92250, 132250, 187250]
MAX_LEVEL             = 14

# Neighborhood unlocked at each level (index 0 → level 1, index 1 → level 2, …)
NEIGHBORHOOD_UNLOCK_ORDER = ["Midtown", "Northside", "Westwood", "Riverside", "Newbay"]

# Personal home key unlocked at each level (index 0 → level 1, index 1 → level 2, …)
HOME_UNLOCK_ORDER  = ["small_apt", "condo", "small_home", "suburban_home", "luxury_villa", "mansion"]
HOME_UNLOCK_LEVELS = [1, 3, 5, 7, 9, 12]   # level required to unlock each entry above

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
    "landscaping": {"name": "Landscaping",       "icon": "🌿", "base_cost":  1500, "value_add":  3000, "cond_boost":  8, "energy_cost": 1},
    "paint":       {"name": "Interior Paint",    "icon": "🎨", "base_cost":  2000, "value_add":  4500, "cond_boost": 12, "energy_cost": 1},
    "flooring":    {"name": "New Flooring",      "icon": "🪵", "base_cost":  4000, "value_add":  8000, "cond_boost": 21, "energy_cost": 2},
    "windows":     {"name": "New Windows",       "icon": "🪟", "base_cost":  6000, "value_add": 10000, "cond_boost": 26, "energy_cost": 2},
    "bathrooms":   {"name": "Bathroom Remodel",  "icon": "🚿", "base_cost":  7000, "value_add": 11000, "cond_boost": 30, "energy_cost": 3},
    "kitchen":     {"name": "Kitchen Remodel",   "icon": "🍳", "base_cost":  8000, "value_add": 14000, "cond_boost": 38, "energy_cost": 3},
    "hvac":        {"name": "HVAC System",       "icon": "❄️", "base_cost": 10000, "value_add": 15000, "cond_boost": 40, "energy_cost": 4},
    "roof":        {"name": "Roof Replacement",  "icon": "🏠", "base_cost": 12000, "value_add": 22000, "cond_boost": 60, "energy_cost": 4},
}

DIY_CLASSES = {
    "flooring_class": {"name": "Flooring Installation Class", "icon": "🪵", "energy_cost": 10, "unlock_level": 2, "unlocks": ["flooring"],             "desc": "Learn to lay hardwood and tile yourself."},
    "windows_class":  {"name": "Window Installation Class",   "icon": "🪟", "energy_cost": 10, "unlock_level": 2, "unlocks": ["windows"],              "desc": "Master framing, sealing, and fitting new windows."},
    "remodel_class":  {"name": "Remodeling Class",            "icon": "🛠️", "energy_cost": 12, "unlock_level": 3, "unlocks": ["bathrooms", "kitchen"], "desc": "Full course covering bathroom and kitchen remodels."},
    "hvac_class":     {"name": "HVAC System Course",          "icon": "❄️", "energy_cost": 14, "unlock_level": 4, "unlocks": ["hvac"],                 "desc": "Certification-level HVAC installation and maintenance."},
    "roof_class":     {"name": "Roof Replacement Course",     "icon": "🏠", "energy_cost": 14, "unlock_level": 4, "unlocks": ["roof"],                 "desc": "Safety and technique for full residential roof replacement."},
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

# Grade multipliers applied to each upgrade's cond_boost.
# Designed so: starting at 0, A-grade on all 8 renovations → ~200 condition (S tier, not S+).
GRADE_MULT = {
    "F":  -0.40,   # actively damages — bad contractor makes things worse
    "D":   0.00,   # wasted money, zero gain
    "C":   0.28,
    "B":   0.58,
    "A":   0.85,   # all 8 at A = 200 condition from 0 (S tier)
    "S":   1.00,   # all 8 at S = 235 (S+ territory — earns it)
    "S+":  1.20,   # all 8 at S+ = 250 (capped max)
}

def tier_cond_change(tier, cond_boost):
    """Return condition point change for a renovation given the grade tier and the
    upgrade's base cond_boost.  Positive upgrades help; F grade actively hurts."""
    return round(GRADE_MULT.get(tier["key"], 0) * cond_boost)

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
    "cheatercheater":  {"desc": "Here you go cheater, here's 10 mill. Now leave me alone 💰", "cash": 10_000_000},
    "pumpkineater":    {"desc": "Max level? Sweet! Now you ruined all the progression of the game... ⭐", "level": MAX_LEVEL, "xp": XP_THRESHOLDS[MAX_LEVEL]},
    "69 bitches":      {"desc": "Real mature Alex... Real mature... 🙄"},
    "redmo":           {"desc": "Hey dummy, you spelt that wrong... it's Dremo"},
    "dremo":           {"desc": "Wait... I thought it was spelt Redmo?"},
    "toro":            {"desc": "Ask for the Big Dog... Cilda..."},
    "david":           {"desc": "Did you mean Edgar?"},
    "edgar":           {"desc": "Did you mean David?"},
    "hannah":          {"desc": "My Love 🥰"},
    "kelly":           {"desc": "Which one? There's three"},
    "edwin":           {"desc": '"We have a little issue..."'},
    "hallie":          {"desc": "MEAN"},
    "alex":            {"desc": "Measures everyday, but doesn't know what 3 inches is"},
    "kenney":          {"desc": "OMG... YOU KILLED KENNEY"},
    "express":         {"desc": "ew"},
    "express flooring":{"desc": "ew"},
    "paul":            {"desc": "PABLO BLANCO"},
    "nibbler":         {"desc": "KITTY KITTY"},
    "cilda":           {"desc": "Yup, that's the big dog"},
    "big dog":         {"desc": "Silly Cilda"},
    "slumlord":        {"desc": "Sly dog, that's a code. Here is $50 on the house 🏠", "cash": 50},
    "slumlord special":{"desc": "Wow, that's a code! Here's some extra cash! 💵", "cash": 10_000},
    "cash":            {"desc": "good try..."},
    "cheat":           {"desc": "You really think there's a cheat named cheat?", "cash": 1},
    "money":           {"desc": "Money? What's that?"},
    "guess":           {"desc": "Hey, good guess. I wouldn't have thought of that", "cash": 1_000},
    "guess one":       {"desc": "Funny, you and I both thought of this", "cash": 1_000},
    "one":             {"desc": "Oh, awesome, you guessed one. Here is One Dollar", "cash": 1},
    "rachael":         {"desc": "Rachet"},
    "help":            {"desc": "Need help with what?"},
    "creator":         {"desc": "Yes, I am the Creator of this crappy game"},
    "creator code":    {"desc": "Hmmm, you couldn't think of anything better?"},
    "poop":            {"desc": "Real mature dude..."},
    "hey":             {"desc": "what?"},
    "what":            {"desc": "WHAT... do you want"},
    "game":            {"desc": "Yup, that's what this is"},
    "lulu":            {"desc": "She doesn't like tickles..."},
    "white":           {"desc": "Like the color, race or Paul?"},
    "life":            {"desc": "If ____ gives you lemons"},
    "lemons":          {"desc": "If life gives you ______"},
    "give":            {"desc": "I ain't giving you nothin' homie..."},
    "weed":            {"desc": "Skunk"},
    "flooring":        {"desc": "IT'S EVERYWHERE"},
    "windows":         {"desc": "If you look out of one, you'll see outside..."},
    "secret":          {"desc": "No secrets here friend..."},
    "secrets":         {"desc": "What secrets? Are you keeping secrets?!?!"},
    "whisper":         {"desc": "LIKE THIS!!!"},
    "yell":            {"desc": "no thank you, try whisper"},
    "chair":           {"desc": "Are you sitting in one?"},
    "desk":            {"desc": "Yup, desk... how interesting."},
    "computer":        {"desc": "Cool, that's what I used to make this game"},
    "keyboard":        {"desc": "I type on those... Cool"},
    "random":          {"desc": "It's random that you put this here"},
    "tv":              {"desc": "Ya, I have one of those"},
    "vape":            {"desc": "I should quit"},
    "geek bar":        {"desc": "my favorite"},
    "geek":            {"desc": "that's what I am! Wait, that's rude"},
    "venus":           {"desc": "Peni... nevermind"},
    "nevermind":       {"desc": "okay..."},
    "buy":             {"desc": "what do you want to buy?"},
    "sell":            {"desc": "what do you want to sell?"},
    "late":            {"desc": "Pretty much everyday to work..."},
    "if":              {"desc": "if what?"},
    "chino":           {"desc": "Smelly booty dog"},
    "caro":            {"desc": "He wants you... BAD"},
    "cats":            {"desc": "Love and hate relationship"},
    "dog":             {"desc": "What's up dog?"},
    "look":            {"desc": "Look where?"},
    "under there":     {"desc": "Underwear? Wait... I see what you did there"},
    "joke":            {"desc": "I ain't got one... sorry"},
    "tell me a joke":  {"desc": "Your face..."},
    "face":            {"desc": "we all have one. Well, should have one."},
    "lie":             {"desc": "You're beautiful"},
    "beautiful":       {"desc": "Well thank you!"},
    "ugly":            {"desc": "Yes you are"},
    "radish":          {"desc": "We miss you little buddy"},
    "meat":            {"desc": "Stop beating it and just play the game"},
    "playstation":     {"desc": "Ya, this is never coming to Playstation"},
    "xbox":            {"desc": "I'm a Playstation guy"},
    "steam":           {"desc": "I like that platform"},
    "battery":         {"desc": "What's yours at? Mine is 22%"},
    "time":            {"desc": "Time for what?"},
    "what time is it": {"desc": "Aren't you playing on a phone?"},
    "phone":           {"desc": "Yes, that is what you are holding"},
    "holding":         {"desc": "Holding what? Drugs?!?!"},
    "drugs":           {"desc": "Say no to drugs, but only on weekdays"},
    "week":            {"desc": "Usually 7 days long, I think..."},
    "weekend":         {"desc": "PARTY TIME"},
    "party":           {"desc": "Alrighty, we can party together"},
    "weekday":         {"desc": "I hate those"},
    "monday":          {"desc": "I hate Monday"},
    "tuesday":         {"desc": "Second worse day of the week"},
    "wednesday":       {"desc": "Isn't it called humpday?"},
    "thursday":        {"desc": "Almost there"},
    "friday":          {"desc": "TGIF"},
    "saturday":        {"desc": "Time to put my feet up"},
    "sunday":          {"desc": "The Lord's day"},
    "work":            {"desc": "I hate that stuff"},
    "enter":           {"desc": "So you typed that out, and clicked it, cool..."},
    ".":               {"desc": "That is a period"},
    "..":              {"desc": "That's two periods"},
    "...":             {"desc": "..."},
    "school":          {"desc": "I hated it. I bet you did too"},
    "me":              {"desc": "Me or you? I'm confused"},
    # ── My additions ──────────────────────────────────────────────────────────
    "yes":             {"desc": "No."},
    "no":              {"desc": "Yes."},
    "okay":            {"desc": "Okay what?"},
    "hello":           {"desc": "Hi. This is a code box, not a chat."},
    "hi":              {"desc": "Hey. Still not how codes work."},
    "bye":             {"desc": "Don't go, we're having fun"},
    "please":          {"desc": "Well since you asked nicely... still nothing."},
    "why":             {"desc": "Why not?"},
    "how":             {"desc": "Very carefully"},
    "password":        {"desc": "If I told you, it wouldn't be a password"},
    "1234":            {"desc": "Real secure... that's your ATM pin isn't it"},
    "test":            {"desc": "Test successful. Nothing happened."},
    "404":             {"desc": "Error: code not found. Wait..."},
    "420":             {"desc": "Ah yes, the magic number"},
    "123":             {"desc": "...456"},
    "abc":             {"desc": "...easy as 123"},
    "qwerty":          {"desc": "Just slam the keyboard why don't ya"},
    "asdf":            {"desc": "Hello keyboard face"},
    "landlord":        {"desc": "That's you, buddy"},
    "tenant":          {"desc": "Treat them well... or don't"},
    "rent":            {"desc": "Pay yours on time"},
    "pizza":           {"desc": "Now I'm hungry"},
    "burger":          {"desc": "I could go for one"},
    "taco":            {"desc": "Taco Tuesday baby"},
    "coffee":          {"desc": "I run on this stuff"},
    "beer":            {"desc": "I'll have one too"},
    "cake":            {"desc": "The cake is a lie"},
    "bread":           {"desc": "The best thing since... itself"},
    "cheese":          {"desc": "Say it!"},
    "snake":           {"desc": "SNAAAAKE"},
    "spider":          {"desc": "NOPE"},
    "bird":            {"desc": "Free bird"},
    "fish":            {"desc": "...something smells fishy"},
    "fire":            {"desc": "WHERE"},
    "space":           {"desc": "The final frontier"},
    "sun":             {"desc": "Don't look directly at it"},
    "star":            {"desc": "You are one 🌟"},
    "moon":            {"desc": "It's right there, just look up"},
    "sleep":           {"desc": "Go to bed"},
    "tired":           {"desc": "Same. All the time."},
    "bored":           {"desc": "You're playing my game, so that tracks"},
    "love":            {"desc": "Awww"},
    "hate":            {"desc": "Strong word, but okay"},
    "sad":             {"desc": "Come here, big hug"},
    "angry":           {"desc": "Breathe"},
    "idk":             {"desc": "same tbh"},
    "bruh":            {"desc": "bruh"},
    "sus":             {"desc": "Very sus that you typed that"},
    "lmao":            {"desc": "I'm glad"},
    "netflix":         {"desc": "You should be watching something instead"},
    "youtube":         {"desc": "How'd you end up here?"},
    "tiktok":          {"desc": "Your attention span is exactly why I made this short"},
    "twitter":         {"desc": "It's called X now apparently"},
    "facebook":        {"desc": "You probably have a parent on there"},
    "google":          {"desc": "You could've just googled the codes"},
    "math":            {"desc": "2 + 2 = fish"},
    "science":         {"desc": "It's real, by the way"},
    "art":             {"desc": "This game is art. I said what I said."},
    "music":           {"desc": "The language of the soul"},
    "stop":            {"desc": "Hammer time"},
    "go":              {"desc": "And where exactly?"},
    "up":              {"desc": "Down"},
    "down":            {"desc": "Up"},
    "left":            {"desc": "Right"},
    "right":           {"desc": "Left"},
    "hot":             {"desc": "You? Or the weather?"},
    "cold":            {"desc": "Put a jacket on"},
    "fast":            {"desc": "And furious?"},
    "slow":            {"desc": "And steady wins the race"},
    "lost":            {"desc": "And found?"},
    "open":            {"desc": "It's open"},
    "wait":            {"desc": "...okay I'm done waiting"},
    "never":           {"desc": "Never say never"},
    "always":          {"desc": "Always? Bold claim"},
    "again":           {"desc": "And again, and again..."},
    "back":            {"desc": "Welcome back"},
    "outside":         {"desc": "It's nice out there, or so I hear"},
    "love you":        {"desc": "Love you too, weirdo"},
    "i love this game":{"desc": "I love you for saying that 🥹"},
    "this sucks":      {"desc": "Yeah... maybe a little 😅"},
    "mario":           {"desc": "Wrong game bro"},
    "minecraft":       {"desc": "This ain't that"},
    "fortnite":        {"desc": "L"},
    "roblox":          {"desc": "How old are you?"},
    "star wars":       {"desc": "I am your developer"},
    "gym":             {"desc": "Said everyone on January 1st"},
    "diet":            {"desc": "Starting Monday, always"},
    "hungry":          {"desc": "Go eat, the game will wait"},
    "perfect":         {"desc": "Nobody is, but keep trying"},
    "wrong":           {"desc": "Try again"},
    "normal":          {"desc": "Doesn't exist"},
    "crazy":           {"desc": "A little, yeah"},
    "smile":           {"desc": "There you go 😊"},
    "run":             {"desc": "Forrest... RUN"},
    "short":           {"desc": "Don't call people that"},
    "old":             {"desc": "Respect your elders"},
    "young":           {"desc": "Enjoy it"},
    "interesting":     {"desc": "I thought so too"},
    "amazing":         {"desc": "Why thank you!"},
    "terrible":        {"desc": "Rude."},
    "begin":           {"desc": "It has begun"},
    "end":             {"desc": "This is not the end"},
    "finish":          {"desc": "Are we there yet?"},
    "later":           {"desc": "See you then"},
    "now":             {"desc": "Right now?"},
    # ── Round 3 ───────────────────────────────────────────────────────────────
    # Food
    "banana":          {"desc": "🍌 Nice."},
    "avocado":         {"desc": "That'll be $18 extra on your toast"},
    "sushi":           {"desc": "Fancy"},
    "bacon":           {"desc": "Now THAT'S a reward"},
    "donut":           {"desc": "Homer Simpson has entered the chat"},
    "cereal":          {"desc": "Dinner of champions"},
    "hot dog":         {"desc": "Is it a sandwich? We need to talk."},
    "ice cream":       {"desc": "You deserve it honestly"},
    "potato":          {"desc": "Versatile. Respected. Underrated."},
    "tomato":          {"desc": "Fruit. Fight me."},
    "pineapple":       {"desc": "Goes on pizza. I said what I said."},
    "sandwich":        {"desc": "The GOAT of meals"},
    "soup":            {"desc": "Not a meal. Fight me on that too."},
    # Animals
    "horse":           {"desc": "Of course"},
    "cow":             {"desc": "Moo"},
    "duck":            {"desc": "If it walks like one..."},
    "penguin":         {"desc": "Formally dressed, always"},
    "elephant":        {"desc": "Never forgets. Unlike you with your password."},
    "bear":            {"desc": "Bear with me here..."},
    "shark":           {"desc": "DUHHHH duh... duh duh duh duh"},
    "whale":           {"desc": "Big mood"},
    "dinosaur":        {"desc": "Extinct, like my motivation"},
    "rabbit":          {"desc": "How'd you get so fast?"},
    "turtle":          {"desc": "Slow and steady. Just like this game loads sometimes."},
    "hamster":         {"desc": "Running on a wheel. Relatable."},
    # Colors
    "red":             {"desc": "Among us color. Very sus."},
    "blue":            {"desc": "Feeling it?"},
    "green":           {"desc": "Like the money you're making in this game"},
    "yellow":          {"desc": "Coward's color? No. Best color? Yes."},
    "purple":          {"desc": "Royal. Distinguished. You."},
    "black":           {"desc": "Classic"},
    "pink":            {"desc": "The superior color and I will not be taking questions"},
    "orange":          {"desc": "The fruit came first. Then the color. Look it up."},
    # Weather
    "rain":            {"desc": "Great, now I'm sad"},
    "snow":            {"desc": "Beautiful until you have to drive in it"},
    "thunder":         {"desc": "BOOM"},
    "lightning":       {"desc": "Don't stand under a tree"},
    "storm":           {"desc": "Batten down the hatches"},
    "wind":            {"desc": "Blows"},
    "fog":             {"desc": "Can't see a thing... like my future"},
    # Holidays
    "christmas":       {"desc": "Ho ho ho, still no code"},
    "halloween":       {"desc": "Spooky szn"},
    "easter":          {"desc": "Hiding eggs like I hide the real cheat codes"},
    "thanksgiving":    {"desc": "Grateful for your gameplay 🦃"},
    "new year":        {"desc": "New year, same game"},
    # Nature
    "beach":           {"desc": "I wish I was there right now"},
    "mountain":        {"desc": "Must be nice up there"},
    "ocean":           {"desc": "Deep. Like this game's lore. (there is none)"},
    "forest":          {"desc": "Very peaceful. Unlike my inbox."},
    "grass":           {"desc": "Touch it. Please. Go outside."},
    "tree":            {"desc": "Huggers welcome"},
    "flower":          {"desc": "Aww, how sweet"},
    "desert":          {"desc": "Dry. Like this game's humor. Wait no."},
    # Space
    "alien":           {"desc": "They're here. They just don't talk much."},
    "rocket":          {"desc": "To the moon? Nah, we're staying here."},
    "planet":          {"desc": "Which one? We've got 8. Or 9. Still heated about Pluto."},
    "pluto":           {"desc": "Still a planet in my heart"},
    "galaxy":          {"desc": "Far far away"},
    "universe":        {"desc": "Existential crisis loading..."},
    # Sports
    "football":        {"desc": "The American or real kind? Matters a lot."},
    "soccer":          {"desc": "The rest of the world is right about the name"},
    "basketball":      {"desc": "Nothing but net"},
    "baseball":        {"desc": "America's pastime, apparently"},
    "golf":            {"desc": "A walk ruined by a little white ball"},
    "tennis":          {"desc": "Anyone? Anyone?"},
    "swimming":        {"desc": "Don't forget to breathe"},
    # Pop culture
    "beyonce":         {"desc": "Queen. No notes."},
    "drake":          {"desc": "Started from the bottom"},
    "taylor swift":    {"desc": "She's going to write a song about this"},
    "eminem":          {"desc": "His palms are sweaty, knees weak, arms are heavy"},
    "harry potter":    {"desc": "You're a landlord, Harry"},
    "batman":          {"desc": "Why so serious?"},
    "spiderman":       {"desc": "With great power comes great rent increases"},
    "avengers":        {"desc": "Endgame was when I started making this instead"},
    "frozen":          {"desc": "Let it go... let it gooo"},
    # Misc
    "wifi":            {"desc": "The 5th basic human need"},
    "internet":        {"desc": "Where would we be without it. Probably outside."},
    "email":           {"desc": "Checking yours right now, aren't you"},
    "homework":        {"desc": "Did you finish it first?"},
    "nap":             {"desc": "Genuinely jealous if you're about to"},
    "dream":           {"desc": "Big ones only"},
    "nightmare":       {"desc": "Is this game one?"},
    "money bag":       {"desc": "💰 noted"},
    "rich":            {"desc": "Not from playing this game, I can tell you that"},
    "broke":           {"desc": "Same honestly"},
    "zero":            {"desc": "That's what you've got after the bad word trick"},
    "nothing":         {"desc": "Exactly what you get"},
    "something":       {"desc": "Vague. I respect it."},
    "everything":      {"desc": "Slow down there"},
    "anyone":          {"desc": "Anyone? Bueller?"},
    "someone":         {"desc": "That someone is you. Figure it out."},
    "nobody":          {"desc": "Nobody puts Baby in a corner"},
    "zxcv":            {"desc": "The other keyboard face"},
    "hjkl":            {"desc": "Vim user spotted"},
    "easter egg":      {"desc": "There is a lot here, find them all"},
    "egg":             {"desc": "Like an easter egg? There is a ton here, find them"},
}

BAD_WORDS = {"fuck", "shit", "cunt", "asshole"}

# ── Stocks & Crypto ────────────────────────────────────────────────────────────
STOCKS = {
    "AMZ":  {"name": "Amazoom",          "icon": "📦", "ticker": "AMZ",
              "desc": "We ship everything. Eventually.",
              "base_price": 142.00, "volatility": 0.022, "tier": "stock"},
    "GOG":  {"name": "Goog-L",           "icon": "🔍", "ticker": "GOG",
              "desc": "Searching for new ways to monetize you.",
              "base_price": 95.00,  "volatility": 0.018, "tier": "stock"},
    "FCP":  {"name": "Faceplant Inc.",   "icon": "📘", "ticker": "FCP",
              "desc": "Connecting the world, one data breach at a time.",
              "base_price": 26.00,  "volatility": 0.035, "tier": "stock"},
    "MSS":  {"name": "MicroSoft-Serve", "icon": "💻", "ticker": "MSS",
              "desc": "Your OS now requires a monthly subscription.",
              "base_price": 68.00,  "volatility": 0.020, "tier": "stock"},
    "APC":  {"name": "AppleCorp",        "icon": "🍎", "ticker": "APC",
              "desc": "Same phone. New port. $200 more.",
              "base_price": 185.00, "volatility": 0.024, "tier": "stock"},
    "TLM":  {"name": "TesLame",          "icon": "🚗", "ticker": "TLM",
              "desc": "Electric cars. Unhinged tweets.",
              "base_price": 38.00,  "volatility": 0.055, "tier": "stock"},
}
ALL_INSTRUMENTS = STOCKS

def _init_stock_state():
    return {
        "portfolio": {},
        "prices":    {t: i["base_price"] for t, i in ALL_INSTRUMENTS.items()},
        "history":   {t: [i["base_price"]] for t, i in ALL_INSTRUMENTS.items()},
    }

def _update_stock_prices(s, days):
    """Advance all prices by `days` using GBM + mean reversion."""
    ss       = s.setdefault("stocks", _init_stock_state())
    prices   = ss.setdefault("prices",  {t: i["base_price"] for t, i in ALL_INSTRUMENTS.items()})
    histories = ss.setdefault("history", {t: [i["base_price"]] for t, i in ALL_INSTRUMENTS.items()})
    for ticker, info in ALL_INSTRUMENTS.items():
        base  = info["base_price"]
        vol   = info["volatility"]
        price = prices.get(ticker, base)
        hist  = list(histories.get(ticker, [base]))
        for _ in range(days):
            reversion = (base - price) / base * 0.08   # gentle pull toward base
            chg       = random.gauss(reversion, vol)
            chg       = max(-0.18, min(0.18, chg))     # cap ±18%/day
            price     = max(price * (1 + chg), base * 0.05)  # floor at 5% of base
        price = round(price, 4 if price < 1 else 2)
        prices[ticker] = price
        hist.append(price)
        histories[ticker] = hist[-50:]
    ss["prices"]  = prices
    ss["history"] = histories

# Player homes — unlock levels defined in HOME_UNLOCK_LEVELS above
# Mansion recharge (60) exceeds its base max_energy (58) intentionally — it fully recharges every day.
# With the Coffee Maker (+2 max_energy) the cap becomes 60 and still recharges fully.
PLAYER_HOMES = [
    {"key": "grandmas_basement", "name": "Grandma's Basement", "icon": "🛋️", "cost":         0, "max_energy":  8, "recharge":  1, "unlock_level":  0, "desc": "Grandma's got a cot, a leaky fridge, and opinions about your life choices. Free rent — if you can survive the casserole."},
    {"key": "small_apt",         "name": "Small Apartment",    "icon": "🏠", "cost":    80_000, "max_energy": 10, "recharge":  3, "unlock_level":  1, "desc": "Thin walls, no dishwasher, and a neighbor who practices drums at midnight. Still yours."},
    {"key": "condo",             "name": "Condo",              "icon": "🏢", "cost":   150_000, "max_energy": 12, "recharge":  5, "unlock_level":  3, "desc": "An HOA fee and a parking sticker — welcome to adulthood."},
    {"key": "small_home",        "name": "Small Home",         "icon": "🏡", "cost":   250_000, "max_energy": 15, "recharge":  7, "unlock_level":  5, "desc": "A real yard. A real mortgage. A real lawn to mow at 7am on a Saturday."},
    {"key": "suburban_home",     "name": "Suburban Home",      "icon": "🏘️", "cost":   400_000, "max_energy": 18, "recharge": 11, "unlock_level":  7, "desc": "Cul-de-sac living with a two-car garage and a wave-hello relationship with the neighbors."},
    {"key": "luxury_villa",      "name": "Luxury Villa",       "icon": "🏛️", "cost":   750_000, "max_energy": 24, "recharge": 19, "unlock_level":  9, "desc": "Heated floors, a wine cellar, and someone else mows the lawn."},
    {"key": "mansion",           "name": "Mansion",            "icon": "🏰", "cost": 1_500_000, "max_energy": 58, "recharge": 60, "unlock_level": 12, "desc": "You have a butler named Gerald and a room you've never entered. Peak existence."},
]

STORE_ITEMS = {
    "coffee_maker": {"name": "Coffee Maker", "icon": "☕",  "cost":   499, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "A decent drip machine. +2 max energy."},
    "new_bed":      {"name": "New Bed",       "icon": "🛏️", "cost": 4_999, "max_energy_bonus": 0, "recharge_bonus": 1, "desc": "Memory foam. You wake up ready. +1 recharge/day."},
}

def generate_jobs():
    """TEST MODE: all job types available, zero energy cost."""
    jobs = []
    lo, hi = JOB_PAY_RANGES[2]
    for i, t in enumerate(JOB_TEMPLATES):
        jobs.append({**t, "id": i, "energy_cost": 0, "base_pay": random.randint(lo, hi)})
    return jobs

CONTRACTORS = {
    "budget":   {"name": "Budget Bob",     "icon": "🔨", "desc": "Cheap but inconsistent — may cut corners", "cost_mult": 0.70, "q_min": 0,  "q_max": 59, "tier_range": "F – B"},
    "standard": {"name": "Standard Steve", "icon": "🛠️", "desc": "Reliable work at fair prices",              "cost_mult": 1.00, "q_min": 30, "q_max": 74, "tier_range": "C – A"},
    "premium":  {"name": "Premier Pete",   "icon": "⭐", "desc": "Top-tier quality, fully guaranteed",         "cost_mult": 1.50, "q_min": 45, "q_max": 100, "tier_range": "B – S+"},
}

# ── Special contractors ────────────────────────────────────────────────────────
# 8% chance to replace the premium slot for a given upgrade type.
# Always guarantee S+ (quality = 100). Same cost/duration as premium.
SPECIAL_CONTRACTORS = {
    "paint":       {"name": "Dremo Construction", "icon": "🐒", "desc": "They might bring a monkey to help paint"},
    "landscaping": {"name": "Green Thumb Gang",   "icon": "🌱", "desc": "They don't stop until the grass literally sings"},
    "flooring":    {"name": "Toro Flooring",       "icon": "🐂", "desc": "Top dogs with Top Work"},
    "windows":     {"name": "Toro Windows",        "icon": "🪟", "desc": "New to windows, but still the best"},
    "hvac":        {"name": "Arctic Pros",          "icon": "❄️", "desc": "Former NASA engineers. Allegedly."},
    "bathrooms":   {"name": "Dremo Construction", "icon": "🐒", "desc": "Hope the monkey won't need to use it after..."},
    "roof":        {"name": "Sky High Co.",         "icon": "🦅", "desc": "If it touches the sky, they've already touched it first"},
    "kitchen":     {"name": "The Sous Crew",        "icon": "👨‍🍳", "desc": "Michelin-starred kitchens, rental-grade prices"},
}
SPECIAL_CONTRACTOR_CHANCE = 0.10

def _roll_special_contractors(s):
    """Re-roll which special contractors are available across all owned properties."""
    for prop in s.get("properties", []):
        rolled = {}
        for key in SPECIAL_CONTRACTORS:
            if random.random() < SPECIAL_CONTRACTOR_CHANCE:
                prem_cost = int(UPGRADES[key]["base_cost"] * CONTRACTORS["premium"]["cost_mult"])
                rolled[key] = {**SPECIAL_CONTRACTORS[key], "cost": prem_cost}
        prop["special_contractors"] = rolled

# ── Special tenant: The Phil ──────────────────────────────────────────────────
# Only one Phil can rent at a time. After he leaves a 4-season (112-day)
# cooldown prevents him from reappearing in any applicant pool.
# He never damages property, always pays, and actively improves the place.
THE_PHIL = {
    "name":          "The Phil",
    "icon":          "🔱",
    "pay_chance":    1.00,
    "damage_chance": 0.00,
    "stay_min":      56,
    "stay_max":      112,
    "is_phil":       True,
    "damage_label":  "None ✨",
    "desc":          "Mysterious. Immaculate. He just… fixes things.",
}

THE_BAILEYS = {
    "name":          "The Baileys",
    "icon":          "👨‍👩‍👧‍👦",
    "pay_chance":    1.00,
    "damage_chance": 0.00,
    "stay_min":      84,    # 3 seasons
    "stay_max":      224,   # ~2 years
    "is_baileys":    True,
    "damage_label":  "None ✨",
    "desc":          "A tight-knit family who treat every home like their own. Never a complaint, never a late payment, never a scuff on the wall.",
}

THE_GOLDBERGS = {
    "name":          "The Goldbergs",
    "icon":          "🎩",
    "pay_chance":    1.00,
    "damage_chance": 0.00,
    "stay_min":      14,
    "stay_max":      56,    # max 2 seasons
    "is_goldbergs":  True,
    "damage_label":  "None ✨",
    "desc":          "Old money. Very old money. They pay extravagantly, never haggle, and never miss a payment. They just don't stay long. Standards, you know.",
}

THE_MYSTERY = {
    "name":          "???",
    "icon":          "👤",
    "pay_chance":    1.00,
    "damage_chance": 0.00,
    "stay_min":      28,
    "stay_max":      168,
    "is_mystery":    True,
    "damage_label":  "None ✨",
    "desc":          "???",
}

def _is_special_tenant(t):
    return any(t.get(k) for k in ("is_phil", "is_baileys", "is_goldbergs", "is_mystery"))

# stay_min / stay_max are in DAYS
TENANT_PROFILES = [
    # ── Budget tier (Midtown / Northside) ──────────────────────────────────────
    {"name": "Todd Burman",         "icon": "🛋️",  "pay_chance": 0.87, "damage_chance": 0.07, "stay_min": 45,  "stay_max": 150, "tiers": ["budget"],         "unique": True,
     "desc": "Freelance 'consultant.' Unclear what he consults on. Always home. Always."},
    {"name": "Stevie Reinholt",     "icon": "🎬",  "pay_chance": 0.84, "damage_chance": 0.10, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "Film student. Has asked twice if they can build a 'small set' in the basement. They're starting to phrase it differently."},
    {"name": "Darnell Okafor",      "icon": "🎤",  "pay_chance": 0.85, "damage_chance": 0.07, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "Stand-up comedian. You've heard him practicing through the ceiling at 11pm. He's actually funny. Doesn't make up for the noise."},
    {"name": "Wanda Greer",         "icon": "👻",  "pay_chance": 0.84, "damage_chance": 0.09, "stay_min": 45,  "stay_max": 120, "tiers": ["budget"],         "unique": True,
     "desc": "Amateur ghost hunter. Asks a lot of questions about the house's history. Concerning."},
    {"name": "Priya Nair",          "icon": "🪴",  "pay_chance": 0.89, "damage_chance": 0.08, "stay_min": 45,  "stay_max": 150, "tiers": ["budget"],         "unique": True,
     "desc": "Has fourteen plants. Keeps asking if she can knock out a wall for 'natural light.' No."},
    {"name": "Ziggy",               "icon": "🎛️",  "pay_chance": 0.83, "damage_chance": 0.08, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "No last name given. Freelance 'sound designer.' Quiet during the day. You don't ask about the evenings."},
    # ── Budget + Mid ───────────────────────────────────────────────────────────
    {"name": "Kevin Marsh",         "icon": "📦",  "pay_chance": 0.88, "damage_chance": 0.04, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Moved in six months ago and still hasn't unpacked. Boxes everywhere. Pays on time though."},
    {"name": "Miles Garner",        "icon": "📲",  "pay_chance": 0.90, "damage_chance": 0.05, "stay_min": 60,  "stay_max": 150, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Pays rent in Venmo with a different emoji every month. Always on time. The emojis are getting weirder."},
    {"name": "Dennis Falk",         "icon": "🕹️",  "pay_chance": 0.89, "damage_chance": 0.12, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Collects vintage arcade machines. Claims they don't take up that much space. They do."},
    {"name": "Orlando Cruz",        "icon": "🏋️",  "pay_chance": 0.91, "damage_chance": 0.10, "stay_min": 60,  "stay_max": 150, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Personal trainer. Has turned the living room into a gym. Technically nothing in the lease says he can't."},
    {"name": "Fran Dubois",         "icon": "🍷",  "pay_chance": 0.88, "damage_chance": 0.11, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Amateur wine maker. The garage smells like a vineyard. She says that's a compliment."},
    {"name": "Clint Hooper",        "icon": "🎸",  "pay_chance": 0.93, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 300, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Says he's 'between gigs.' Has been between gigs for four years. Never missed rent. You've stopped asking."},
    {"name": "Margot Voss",         "icon": "🏺",  "pay_chance": 0.91, "damage_chance": 0.07, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Teaches ceramics online. The whole place smells like clay. She's made you a mug. It's actually very good."},
    {"name": "Carol Fitch",         "icon": "✉️",  "pay_chance": 0.93, "damage_chance": 0.02, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Does not own a phone. All communication is by note, slipped under the door. Surprisingly effective. Slightly unnerving."},
    {"name": "Juno Park",           "icon": "🗓️",  "pay_chance": 0.91, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 365, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Said she'd be here six months. That was two years ago. She doesn't bring it up. Neither do you."},
    {"name": "Cynthia Bloom",       "icon": "🎭",  "pay_chance": 0.90, "damage_chance": 0.07, "stay_min": 45,  "stay_max": 150, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Retired cruise ship entertainer. Will perform if asked. Rent always on time but neighbors have complained."},
    {"name": "Russ Tirado",         "icon": "🧊",  "pay_chance": 0.91, "damage_chance": 0.09, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Works in 'logistics.' Has asked twice if the garage can be climate controlled. You said no. He brought it up again."},
    {"name": "Janet Osei",          "icon": "📚",  "pay_chance": 0.90, "damage_chance": 0.09, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Lovely person. Hosts a book club every Thursday that has somehow become 22 people."},
    # ── Mid tier (Westwood / Riverside) ───────────────────────────────────────
    {"name": "Marcus Webb",         "icon": "🏥",  "pay_chance": 0.95, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "Works nights at the hospital, sleeps during the day. Never complains, always pays early."},
    {"name": "Nora Finch",          "icon": "📖",  "pay_chance": 0.97, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "Elementary school librarian. Will report every minor issue in writing, with timestamps."},
    {"name": "Sam & Deb Hollis",    "icon": "💍",  "pay_chance": 0.92, "damage_chance": 0.07, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "Newlyweds. Very excited about everything. Will ask if they can paint one wall an accent color."},
    {"name": "Theo Blackwell",      "icon": "🏃",  "pay_chance": 0.94, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "High school gym teacher. Quiet, respectful, occasionally does pull-ups in the doorframe."},
    {"name": "Donna Kephart",       "icon": "🗣️",  "pay_chance": 0.92, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 240, "tiers": ["mid"],             "unique": True,
     "desc": "Very nice. Has brought up five times that she used to own this neighborhood. Not this house. The neighborhood."},
    {"name": "Bev Stanton",         "icon": "🌡️",  "pay_chance": 0.94, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid"],             "unique": True,
     "desc": "Retired. Has strong opinions about your thermostat settings even though she controls her own."},
    {"name": '"Coach" Ernie Walls', "icon": "⚾",  "pay_chance": 0.94, "damage_chance": 0.03, "stay_min": 120, "stay_max": 365, "tiers": ["mid"],             "unique": True,
     "desc": "Coaches youth baseball but no one knows which team. There are trophies in the hall closet he refuses to acknowledge."},
    {"name": "Gerald",              "icon": "📮",  "pay_chance": 0.95, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid"],             "unique": True,
     "desc": "Retired postal worker. Been renting for 30 years. He knows things. Doesn't cause problems but definitely could."},
    {"name": "Nina Alcott",         "icon": "🔍",  "pay_chance": 0.94, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "Kindergarten teacher by day, true crime podcaster by night. The shelves of case files are a little much."},
    {"name": "The Watkins Brothers","icon": "🤼",  "pay_chance": 0.93, "damage_chance": 0.10, "stay_min": 90,  "stay_max": 240, "tiers": ["mid"],             "unique": True,
     "desc": "Two brothers, one apartment. Surprisingly clean. Shockingly loud. They arm-wrestle to decide who Venmos you."},
    {"name": "Simone Adeyemi",      "icon": "📝",  "pay_chance": 0.94, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],             "unique": True,
     "desc": "Graduate student, quiet, meticulous. Subletting is her whole personality."},
    # ── Mid + Premium ──────────────────────────────────────────────────────────
    {"name": "Arthur Pham",         "icon": "🧾",  "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Semi-retired accountant. Pays rent 10 days early, every time. Has never once made eye contact."},
    {"name": "Gracie Monroe",       "icon": "✈️",  "pay_chance": 0.97, "damage_chance": 0.01, "stay_min": 60,  "stay_max": 120, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Travel nurse, in town for 90 days at a time. You'll barely know she was there."},
    {"name": "Hector Vidal",        "icon": "👨‍🍳", "pay_chance": 0.95, "damage_chance": 0.06, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Chef. Works dinner service, home by 1am. The hallway always smells incredible. You want some."},
    {"name": "Patrice Owens",       "icon": "🩺",  "pay_chance": 0.97, "damage_chance": 0.01, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Nurse, night shift. Leaves a polite note asking that no one rings the doorbell before 3pm. Means it."},
    {"name": "Ben Kowalczyk",       "icon": "💻",  "pay_chance": 0.96, "damage_chance": 0.01, "stay_min": 60,  "stay_max": 180, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "IT contractor. Sets up his own router, patches the wi-fi dead spot you never told him about, and asks nothing in return."},
    {"name": "Pete",                "icon": "🤝",  "pay_chance": 0.97, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Just Pete. No last name on file. Handshake firm, eye contact strong, references spotless. Something is off but you can't prove it."},
    {"name": "The Nguyens",         "icon": "👨‍👩‍👧‍👦","pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Three generations. Grandmother barely speaks English but leaves food outside your door somehow. The best tenants you've ever had."},
    {"name": "The Delgados",        "icon": "🏡",  "pay_chance": 0.96, "damage_chance": 0.08, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Big family, loud on weekends, best rent-to-noise ratio you'll find. One grandmother fixed your porch without being asked."},
    {"name": '"Big" Lou Santino',   "icon": "🛁",  "pay_chance": 0.96, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Never seen without a bathrobe. Unclear if he owns pants. Pays cash, exact change, always in a sealed envelope."},
    {"name": "Diane Cho",           "icon": "🍎",  "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"],  "unique": True,
     "desc": "Retired teacher. Keeps the place immaculate. Will leave a note if a lightbulb is out."},
    # ── Premium tier (Newbay) ─────────────────────────────────────────────────
    {"name": "Dr. Yemi Adebayo",    "icon": "👶",  "pay_chance": 0.98, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["premium"],         "unique": True,
     "desc": "Pediatrician. Extremely quiet. Has a very specific parking spot preference. Mentions it at lease signing, move-in, and every renewal."},
    {"name": "Cassandra Lyle",      "icon": "⚖️",  "pay_chance": 0.99, "damage_chance": 0.02, "stay_min": 60,  "stay_max": 180, "tiers": ["premium"],         "unique": True,
     "desc": "Corporate lawyer. Never home. Pays 3 months upfront. You've seen her maybe twice."},
    {"name": "Maureen Tully",       "icon": "📋",  "pay_chance": 0.97, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["premium"],         "unique": True,
     "desc": "70s, sharp as a tack, rented this unit from three different landlords. Knows exactly what your responsibilities are. Will remind you."},
    {"name": "Old Man Pietrzak",    "icon": "🏚️",  "pay_chance": 0.98, "damage_chance": 0.02, "stay_min": 180, "stay_max": 365, "tiers": ["premium"],         "unique": True,
     "desc": "Has lived here 11 years through four ownership changes. Technically never signed a new lease. Just... stayed. Pays cash."},
    # ── All tiers ──────────────────────────────────────────────────────────────
    {"name": "Ray Kowalski",        "icon": "🚛",  "pay_chance": 0.96, "damage_chance": 0.01, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid", "premium"], "unique": True,
     "desc": "Truck driver, gone three weeks a month. Easiest tenant you'll ever have."},
    {"name": "Carl & Judy Prescott","icon": "👴",  "pay_chance": 0.98, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["budget", "mid", "premium"], "unique": True,
     "desc": "Older couple. Never miss rent. Will occasionally leave a casserole on the counter."},

    # ── Generic fallbacks (non-unique, always in pool) ─────────────────────────
    {"name": "College Student",     "icon": "🎓",  "pay_chance": 0.82, "damage_chance": 0.12, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],
     "desc": "Responsible enough. On time most months."},
    {"name": "The Musician",        "icon": "🎸",  "pay_chance": 0.78, "damage_chance": 0.14, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],
     "desc": "Between projects. The amp is non-negotiable."},
    {"name": "Night Owl",           "icon": "🌙",  "pay_chance": 0.85, "damage_chance": 0.06, "stay_min": 45,  "stay_max": 120, "tiers": ["budget"],
     "desc": "Never seen in daylight. The place is always clean though."},
    {"name": "The Artist",          "icon": "🎨",  "pay_chance": 0.80, "damage_chance": 0.15, "stay_min": 60,  "stay_max": 150, "tiers": ["budget", "mid"],
     "desc": "Big vision, flexible budget. Rent usually lands."},
    {"name": "The Freelancer",      "icon": "🖥️",  "pay_chance": 0.85, "damage_chance": 0.05, "stay_min": 45,  "stay_max": 150, "tiers": ["budget", "mid"],
     "desc": "Works from home. All day. Every day."},
    {"name": "Young Couple",        "icon": "👫",  "pay_chance": 0.91, "damage_chance": 0.07, "stay_min": 90,  "stay_max": 270, "tiers": ["budget", "mid"],
     "desc": "First place together. Excited about everything. Probably getting a dog."},
    {"name": "Section 8",           "icon": "🏛️",  "pay_chance": 0.95, "damage_chance": 0.08, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"],
     "desc": "Government-backed rent. You get paid regardless."},
    {"name": "The Teacher",         "icon": "🍎",  "pay_chance": 0.93, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"],
     "desc": "Steady, responsible, asks for nothing."},
    {"name": "Single Parent",       "icon": "🧑‍👧", "pay_chance": 0.90, "damage_chance": 0.06, "stay_min": 90,  "stay_max": 300, "tiers": ["mid"],
     "desc": "Responsible, organized, not here to cause problems."},
    {"name": "The Handyman",        "icon": "🔧",  "pay_chance": 0.91, "damage_chance": 0.01, "stay_min": 90,  "stay_max": 240, "tiers": ["mid"],
     "desc": "Will fix minor things himself. Actually helpful."},
    {"name": "Remote Worker",       "icon": "💼",  "pay_chance": 0.94, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"],
     "desc": "Home 24/7, somehow never noticed. Good tenant."},
    {"name": "Young Professional",  "icon": "👔",  "pay_chance": 0.97, "damage_chance": 0.03, "stay_min": 60,  "stay_max": 180, "tiers": ["mid", "premium"],
     "desc": "Early starts, late nights. Never around enough to cause trouble."},
    {"name": "The Couple",          "icon": "🏠",  "pay_chance": 0.96, "damage_chance": 0.04, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"],
     "desc": "Settled, quiet, pay early. Will ask about painting exactly once."},
    {"name": "The Executive",       "icon": "💰",  "pay_chance": 0.99, "damage_chance": 0.02, "stay_min": 60,  "stay_max": 180, "tiers": ["premium"],
     "desc": "Barely home. Pays 2 months upfront. You will never hear from them."},
    {"name": "Empty Nesters",       "icon": "🪑",  "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["premium"],
     "desc": "Kids are grown. They want peace, quiet, and the same parking spot every time."},
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
    # premium or special — same schedule
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

def get_unlocked_neighborhoods(level):
    """Return list of neighborhood names the player can access at this level."""
    if level == 0: return []
    return NEIGHBORHOOD_UNLOCK_ORDER[:min(level, len(NEIGHBORHOOD_UNLOCK_ORDER))]

def get_unlocked_home_keys(level):
    """Return list of personal home keys unlocked at this level."""
    base = ["grandmas_basement"]
    return base + [key for key, req in zip(HOME_UNLOCK_ORDER, HOME_UNLOCK_LEVELS) if level >= req]

def add_xp(s, amount):
    """Add XP to the player. Returns new level if a level-up occurred, else None.
    Level 0 is special — XP is ignored there (level 0→1 is triggered by first sale)."""
    lvl = s.get("level", 0)
    if lvl == 0 or lvl >= MAX_LEVEL:
        return None
    s["xp"] = s.get("xp", 0) + amount
    new_lvl = lvl
    for check in range(lvl + 1, MAX_LEVEL + 1):
        if s["xp"] >= XP_THRESHOLDS[check]:
            new_lvl = check
        else:
            break
    if new_lvl > lvl:
        s["level"] = new_lvl
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"Level Up! You are now Level {new_lvl}. New options unlocked!"})
        return new_lvl
    return None

def calc_xp_pct(s):
    """Return XP progress as integer percent (0-100) toward the next level."""
    lvl = s.get("level", 0)
    xp  = s.get("xp", 0)
    if lvl == 0: return 0
    if lvl >= MAX_LEVEL: return 100
    lo  = XP_THRESHOLDS[lvl]
    hi  = XP_THRESHOLDS[lvl + 1]
    if hi <= lo: return 100
    return min(100, max(0, int((xp - lo) / (hi - lo) * 100)))

def get_player_home(s):
    """Return the PLAYER_HOMES dict for the player's current home."""
    key = s.get("player_home", "grandmas_basement")
    return next((h for h in PLAYER_HOMES if h["key"] == key), PLAYER_HOMES[0])

def _get_home_stats(s):
    """Return (max_energy, recharge) with store item bonuses applied."""
    home  = get_player_home(s)
    items = s.get("owned_items", {})
    max_e = home["max_energy"] + (STORE_ITEMS["coffee_maker"]["max_energy_bonus"] if items.get("coffee_maker") else 0)
    rch   = home["recharge"]   + (STORE_ITEMS["new_bed"]["recharge_bonus"]        if items.get("new_bed") else 0)
    return max_e, rch

def upgrade_cooldown_remaining(upg_val, current_day):
    """Days left before this upgrade can be done again. 0 = available now."""
    if not isinstance(upg_val, dict):
        return 0   # old format = no cooldown
    return max(0, RENO_COOLDOWN - (current_day - upg_val.get("day", 0)))

def calc_market_value(prop):
    if prop.get("fixed_market_value"):
        val = prop["fixed_market_value"]
        for key, upg_val in prop.get("upgrades", {}).items():
            quality = get_upgrade_quality(upg_val)
            val    += int(UPGRADES[key]["value_add"] * (quality / 100))
        val += get_premium_bonuses(prop)["value"]
        return val
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
    p["address"]         = prop.get("address", f"{prop.get('type', 'Property')} — {prop.get('neighborhood', '')}")
    p["neighborhood_info"] = NEIGHBORHOODS[prop["neighborhood"]]
    p["deal"]            = p["market_value"] - prop["purchase_price"]
    if p.get("tenant"):
        lease_end = p["tenant"].get("lease_end_day", current_day)
        p["tenant_days_remaining"] = max(0, lease_end - current_day)
    return p

def _roll_condition(cond_rolls):
    """Pick a condition value using weighted ranges. cond_rolls = [(low, high, weight), ...]"""
    population = [r[:2] for r in cond_rolls]
    weights    = [r[2]  for r in cond_rolls]
    lo, hi     = random.choices(population, weights=weights)[0]
    return random.randint(lo, hi)

def _make_address(hood):
    """Generate a realistic street address for a neighborhood."""
    number = random.randint(1, 99) * 100 + random.choice([0, 5, 8, 12, 17, 24, 35, 43, 51, 62, 76, 88])
    number = max(100, min(9999, number))
    street = random.choice(HOOD_STREETS.get(hood, ["Main St"]))
    return f"{number} {street}"

def generate_property(nid, hoods=None):
    hood  = random.choice(hoods if hoods else list(NEIGHBORHOODS.keys()))
    cfg   = HOOD_PROP_CONFIG.get(hood, {})

    ptype = random.choice(cfg.get("types", PROPERTY_TYPES))

    # Mansions get their own generous stats to guarantee $1M+ asking price
    if ptype == "Mansion":
        beds  = random.randint(5, 7)
        baths = random.randint(3, min(beds, 5))
        sqft  = random.randint(6000, 9000)
        cond  = random.randint(185, 245)
    else:
        bed_min, bed_max = cfg.get("beds", (1, 5))
        beds  = random.randint(bed_min, bed_max)
        baths = random.randint(1, min(beds, cfg.get("baths_max", 3)))
        sq_lo, sq_hi = cfg.get("sqft", (600, 1800))
        sqft  = random.randint(sq_lo, sq_hi)
        cond  = _roll_condition(cfg.get("cond_rolls", [(25, 212, 1)]))

    address = _make_address(hood)
    prop = {"id": nid, "type": ptype, "neighborhood": hood, "address": address,
            "bedrooms": beds, "bathrooms": baths, "sqft": sqft, "condition": cond,
            "upgrades": {}, "premium_upgrades": [], "squatter": None, "vacant_since": 1,
            "pending_reno": None, "pending_premium": None,
            "scheduled_reno": None, "scheduled_premium": None,
            "tenant": None, "days_rented": 0,
            "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0}
    prop["purchase_price"] = int(calc_market_value(prop) * random.uniform(0.88, 1.06))
    return prop

def make_starter_home():
    return {"id": 1, "type": "Bungalow", "neighborhood": "Midtown", "address": "412 Elm St",
            "bedrooms": 2, "bathrooms": 1, "sqft": 820, "condition": 61,
            "upgrades": {}, "premium_upgrades": [],
            "squatter": {"moved_in_day": 1, "stay_days": 9999, "bribe": 4367, "starter": True},
            "vacant_since": 1,
            "pending_reno": None, "pending_premium": None,
            "scheduled_reno": None, "scheduled_premium": None,
            "tenant": None, "days_rented": 0,
            "total_rent_collected": 0, "total_repair_costs": 0, "purchase_price": 0,
            "fixed_market_value": 75633}

def new_game():
    starter = make_starter_home()
    state = {
        "cash": STARTING_CASH, "day": 1, "next_id": 2,
        "properties": [starter], "market": [], "log": [],
        "applicants_cache": {},
        "last_bank_day": 1,
        "energy": PLAYER_HOMES[0]["max_energy"],
        "player_home": "grandmas_basement",
        "owned_items": {},
        "diy_classes": {},
        "jobs": generate_jobs(),
        "redeemed_codes": [],
        "intro_seen": False,
        "squatter_count": 0,
        "bank": {"savings": 0, "loans": [], "next_loan_id": 1},
        "level": 0, "xp": 0,
        "stocks": _init_stock_state(),
    }
    state["log"].append({"day": 1, "type": "warning",
        "text": "You inherited a run-down Bungalow in Midtown — but there's a squatter inside demanding $4,367 to leave. Bribe them out, or sell the property as-is and pocket $80,000 to start fresh."})
    state["market"], state["next_id"] = _gen_market(state["next_id"])
    return state

def _gen_market(start_id, hoods=None):
    listings, nid = [], start_id
    target_hoods = list(hoods) if hoods else list(NEIGHBORHOODS.keys())
    for hood in target_hoods:
        count = random.randint(2, 5)
        for _ in range(count):
            listings.append(generate_property(nid, hoods=[hood]))
            nid += 1
    return listings, nid

_HOOD_MIGRATION = {
    "Eastside":  "Midtown",
    "Riverside": "Northside",
    "Midtown":   "Westwood",
    "Westwood":  "Riverside",
    "Downtown":  "Newbay",
}

def _migrate_state(s):
    """Migrate old saves to current schema."""
    # Neighbourhood rename: only remap on OLD saves (those without a "level" key).
    # New saves already use the correct hood names; remapping them would corrupt data
    # because several names overlap between old and new (Midtown, Westwood, Riverside).
    if "level" not in s:
        for prop in s.get("properties", []) + s.get("market", []):
            hood = prop.get("neighborhood", "")
            if hood in _HOOD_MIGRATION:
                prop["neighborhood"] = _HOOD_MIGRATION[hood]
    # Level/XP migration — give existing players a fair starting point.
    # Only applies when level is missing (first time loading after the XP update).
    if "level" not in s:
        props     = s.get("properties", [])
        has_props = len(props) > 0
        tenanted  = any(p.get("tenant") for p in props)
        cash      = s.get("cash", 0)
        # Anyone who already has property activity starts at level 1 so they
        # aren't locked out of everything they've already built.
        if has_props or cash > STARTING_CASH:
            s["level"] = 1
            s["xp"]    = 0
        else:
            s["level"] = 0
            s["xp"]    = 0
    s.setdefault("xp", 0)
    s.setdefault("owned_items", {})
    s.setdefault("diy_classes", {})
    # Rename old starting home key; other stale keys fall back gracefully in get_player_home
    if s.get("player_home") == "moms_basement":
        s["player_home"] = "grandmas_basement"
    s.setdefault("intro_seen", True)   # existing saves skip the intro
    s.setdefault("tax_year_flip_income", 0)
    s.setdefault("tax_year_rent_income", 0)
    s.setdefault("tax_extension_filed", False)
    s.setdefault("tax_owed", 0)
    if "stocks" not in s:
        s["stocks"] = _init_stock_state()
    # Ensure new per-property fields exist on old saves
    for prop in s.get("properties", []):
        prop.setdefault("reno_payment_owed", None)
    # One-time roll for any property that has never had special contractors set
    for prop in s.get("properties", []):
        if "special_contractors" not in prop:
            rolled = {}
            for key in SPECIAL_CONTRACTORS:
                if random.random() < SPECIAL_CONTRACTOR_CHANCE:
                    prem_cost = int(UPGRADES[key]["base_cost"] * CONTRACTORS["premium"]["cost_mult"])
                    rolled[key] = {**SPECIAL_CONTRACTORS[key], "cost": prem_cost}
            prop["special_contractors"] = rolled
    return s

def load():
    """Read game state from the request body (_state field) or start a new game."""
    data  = request.get_json(silent=True) or {}
    state = data.get('_state')
    return _migrate_state(state) if state else new_game()

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
    max_e, rch = _get_home_stats(s)
    weekly_income = sum(p["tenant"]["rent"] for p in s["properties"] if p.get("tenant"))
    lvl = s.get("level", 0)
    return jsonify({
        "cash":                   s["cash"],
        "day":                    s["day"],
        "energy":                 s.get("energy", max_e),
        "max_energy":             max_e,
        "energy_recharge":        rch,
        "player_home":            s.get("player_home", "grandmas_basement"),
        "owned_items":            s.get("owned_items", {}),
        "diy_classes":            s.get("diy_classes", {}),
        "jobs":                   s.get("jobs", []),
        "net_worth":              s["cash"] + sum(calc_market_value(p) for p in s["properties"]),
        "weekly_income":          weekly_income,
        "property_count":         len(s["properties"]),
        "properties":             [enrich(p, s["day"]) for p in s["properties"]],
        "log":                    s["log"][-40:],
        "bank":                   s.get("bank", {"savings": 0, "loans": [], "next_loan_id": 1}),
        "savings_tier":           savings_tier(s.get("bank", {}).get("savings", 0)),
        "level":                  lvl,
        "xp_pct":                 calc_xp_pct(s),
        "unlocked_neighborhoods": get_unlocked_neighborhoods(lvl),
        "unlocked_homes":         get_unlocked_home_keys(lvl),
        "intro_seen":             s.get("intro_seen", True),
    })

@app.route('/api/market', methods=['GET', 'POST'])
def api_market():
    s = load()
    unlocked = get_unlocked_neighborhoods(s.get("level", 0))
    if not unlocked:
        return jsonify({"listings": [], "level_locked": True})
    # Only regenerate when a brand-new neighborhood just unlocked (or first load).
    # Do NOT regenerate just because all listings in a hood were purchased —
    # the market only refills on day advance.
    generated_for  = set(s.get("market_unlocked_hoods", []))
    newly_unlocked = set(unlocked) - generated_for
    if newly_unlocked or not s.get("market"):
        s["market"], s["next_id"] = _gen_market(s["next_id"], hoods=unlocked)
        s["market_unlocked_hoods"] = list(unlocked)
        save(s)
    return jsonify({"listings": [enrich(p, s["day"]) for p in s["market"]]})

@app.route('/api/market/refresh', methods=['POST'])
def api_market_refresh():
    s = load()
    unlocked = get_unlocked_neighborhoods(s.get("level", 0))
    if not unlocked:
        return jsonify({"listings": [], "level_locked": True})
    s["market"], s["next_id"] = _gen_market(s["next_id"], hoods=unlocked)
    save(s)
    return jsonify({"listings": [enrich(p, s["day"]) for p in s["market"]]})

@app.route('/api/buy', methods=['POST'])
def api_buy():
    data = request.json
    s    = load()
    if s.get("level", 0) == 0:
        return jsonify({"error": "Reach Level 1 first — sell your starter property!"}), 400
    prop = next((p for p in s["market"] if p["id"] == data["listing_id"]), None)
    if not prop:
        return jsonify({"error": "Listing not found"}), 404
    if prop["purchase_price"] > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= prop["purchase_price"]
    prop["vacant_since"] = s["day"]   # start tracking vacancy from purchase day
    # Roll special contractors immediately so they're available before the next day advance
    rolled = {}
    for key in SPECIAL_CONTRACTORS:
        if random.random() < SPECIAL_CONTRACTOR_CHANCE:
            prem_cost = int(UPGRADES[key]["base_cost"] * CONTRACTORS["premium"]["cost_mult"])
            rolled[key] = {**SPECIAL_CONTRACTORS[key], "cost": prem_cost}
    prop["special_contractors"] = rolled
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
                entry = {**upg, "key": key, "costs": costs, "prev_quality_tier": tier_key}
                sc = prop.get("special_contractors", {}).get(key)
                if sc:
                    entry["special_contractor"] = sc
                available.append(entry)
        else:
            costs = {ck: int(upg["base_cost"] * c["cost_mult"]) for ck, c in CONTRACTORS.items()}
            entry = {**upg, "key": key, "costs": costs}
            sc = prop.get("special_contractors", {}).get(key)
            if sc:
                entry["special_contractor"] = sc
            available.append(entry)
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
    upg            = UPGRADES[upgrade_key]
    contractor_key = data["contractor_key"]
    is_special     = (contractor_key == "special")
    if is_special:
        if upgrade_key not in SPECIAL_CONTRACTORS:
            return jsonify({"error": "No special contractor available for this job"}), 400
        sc      = SPECIAL_CONTRACTORS[upgrade_key]
        premium = CONTRACTORS["premium"]
        cost    = int(upg["base_cost"] * premium["cost_mult"])
        quality = 100   # guaranteed S+
        cont_name = sc["name"]
    else:
        if contractor_key not in CONTRACTORS:
            return jsonify({"error": "Unknown contractor"}), 400
        cont      = CONTRACTORS[contractor_key]
        cost      = int(upg["base_cost"] * cont["cost_mult"])
        quality   = random.randint(cont["q_min"], cont["q_max"])
        cont_name = cont["name"]
    is_vacant    = not prop.get("tenant")
    # Vacant homes: pay contractor on completion, not upfront
    if not is_vacant and cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    tier         = score_to_tier(quality)
    cond_change  = tier_cond_change(tier, upg["cond_boost"])
    duration     = contractor_days("premium" if is_special else contractor_key, upg.get("energy_cost", 1))
    complete_day = s["day"] + duration
    if not is_vacant:
        s["cash"] -= cost
    prop["pending_reno"] = {
        "upgrade_key":      upgrade_key,
        "contractor":       contractor_key,
        "quality":          quality,
        "tier_key":         tier["key"],
        "cond_change":      cond_change,
        "complete_day":     complete_day,
        "duration":         duration,
        "name":             upg["name"],
        "icon":             upg["icon"],
        "deferred_payment": is_vacant,
        "cost":             cost,
    }
    # Consume the special contractor slot so it can't be reused before next advance
    if is_special:
        prop.setdefault("special_contractors", {}).pop(upgrade_key, None)
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"{upg['name']} started at {prop['type']} in {prop['neighborhood']} — {cont_name}, done in {duration} day{'s' if duration > 1 else ''}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"],
                    "duration": duration, "complete_day": complete_day,
                    "contractor_name": cont_name,
                    "deferred_payment": is_vacant})

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
    is_special = (contractor_key == "special")
    if not is_special and contractor_key not in CONTRACTORS:
        return jsonify({"error": "Unknown contractor"}), 400

    existing  = prop.get("upgrades", {}).get(upgrade_key)
    remaining = upgrade_cooldown_remaining(existing, s["day"]) if existing is not None else 0
    if remaining > 0:
        return jsonify({"error": f"On cooldown — {remaining} days remaining"}), 400

    upg = UPGRADES[upgrade_key]
    if is_special:
        if upgrade_key not in SPECIAL_CONTRACTORS:
            return jsonify({"error": "No special contractor available for this job"}), 400
        premium = CONTRACTORS["premium"]
        cost    = int(upg["base_cost"] * premium["cost_mult"])
        quality = 100
    else:
        cont    = CONTRACTORS[contractor_key]
        cost    = int(upg["base_cost"] * cont["cost_mult"])
        quality = random.randint(cont["q_min"], cont["q_max"])
    if cost > s["cash"]:
        return jsonify({"error": f"Need ${cost:,} — you have ${int(s['cash']):,}"}), 400

    # Validate/clamp start_day to 1-28 days out
    if not start_day or not (s["day"] + 1 <= start_day <= s["day"] + 28):
        start_day = s["day"] + random.randint(1, 28)

    tier        = score_to_tier(quality)
    cond_change = tier_cond_change(tier, upg["cond_boost"])
    duration    = contractor_days("premium" if is_special else contractor_key, upg.get("energy_cost", 1))

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
    if is_special:
        prop.setdefault("special_contractors", {}).pop(upgrade_key, None)
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
    if prop.get("squatter") and prop["squatter"].get("starter"):
        return jsonify({"error": "No buyer's touching that place with a squatter in it. Bribe them out first."}), 400
    # Fixed-value properties (e.g. starter home) sell at exact price until upgraded
    if prop.get("fixed_market_value") and not prop.get("upgrades") and not prop.get("premium_upgrades"):
        sale = prop["fixed_market_value"]
    else:
        sale = int(calc_market_value(prop) * random.uniform(0.95, 1.05))
    profit = sale - prop["purchase_price"]
    s["cash"] += sale
    if profit > 0:
        s["tax_year_flip_income"] = s.get("tax_year_flip_income", 0) + profit
    s["properties"] = [p for p in s["properties"] if p["id"] != prop["id"]]
    s["log"].append({"day": s["day"], "type": "sell" if profit >= 0 else "loss",
        "text": f"Sold {prop['type']} in {prop['neighborhood']} for ${sale:,} ({'profit' if profit >= 0 else 'loss'}: ${abs(profit):,})"})
    # ── XP / Level trigger ────────────────────────────────────────────────────
    level_up = None
    if s.get("level", 0) == 0:
        # First sale: guaranteed level 1
        s["level"] = 1
        s["xp"]    = 0
        s["log"].append({"day": s["day"], "type": "info",
            "text": "Level Up! You are now Level 1. Buy properties and find tenants in Midtown!"})
        level_up = 1
    elif profit > 0:
        xp_gain  = min(80, max(5, round(profit / 800)))
        level_up = add_xp(s, xp_gain)
    save(s)
    return jsonify({"success": True, "sale_price": sale, "profit": profit, "cash": s["cash"],
                    "level_up": level_up, "new_level": s.get("level", 0)})

@app.route('/api/property/<int:pid>/applicants', methods=['GET', 'POST'])
def api_applicants(pid):
    s    = load()
    if s.get("level", 0) == 0:
        return jsonify({"error": "Reach Level 1 first — sell your starter property!"}), 400
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    key = str(pid)
    if key not in s.get("applicants_cache", {}):
        # Filter tenant pool to profiles that match the property's neighborhood tier
        hood_tier = NEIGHBORHOODS.get(prop.get("neighborhood", ""), {}).get("tier", "mid")
        active_names = {
            p["tenant"]["name"] for p in s["properties"]
            if p.get("tenant") and not any(p["tenant"].get(k) for k in ("is_phil","is_baileys","is_goldbergs","is_mystery"))
        }
        eligible  = [
            t for t in TENANT_PROFILES
            if hood_tier in t.get("tiers", ["budget", "mid", "premium"])
            and (not t.get("unique") or t["name"] not in active_names)
        ]
        picks     = random.sample(eligible, min(3, len(eligible)))
        applicants = [{**t, "idx": i,
                       "damage_label": "Low" if t["damage_chance"] < 0.05 else ("Medium" if t["damage_chance"] < 0.10 else "High")}
                      for i, t in enumerate(picks)]
        # Possibly inject a special tenant — 5% chance per applicant list refresh.
        # Only one special tenant appears at a time, chosen randomly from eligible ones.
        special_pool = []
        def _eligible(flag, cooldown_key):
            active   = any((p.get("tenant") or {}).get(flag) for p in s["properties"])
            cooldown = s.get(cooldown_key, 0) > s["day"]
            return not active and not cooldown
        if _eligible("is_phil",      "phil_cooldown_until"):     special_pool.append(THE_PHIL)
        if _eligible("is_baileys",   "baileys_cooldown_until"):  special_pool.append(THE_BAILEYS)
        if _eligible("is_goldbergs", "goldbergs_cooldown_until"):special_pool.append(THE_GOLDBERGS)
        if _eligible("is_mystery",   "mystery_cooldown_until"):  special_pool.append(THE_MYSTERY)
        if special_pool and random.random() < 0.35:
            chosen = random.choice(special_pool)
            applicants.append({**chosen, "idx": len(applicants)})
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
    if prop.get("squatter"):
        return jsonify({"error": "Remove squatters first"}), 400
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
        "rent":             weekly_rent,
        "fair_rent":        fair_rent,
        "rent_tier":        tier["tier"],
        "pay_chance":       pay_chance,
        "damage_chance":    dmg_chance,
        "next_rent_day":    s["day"] + 7,
        "lease_end_day":    s["day"] + stay_days,
        "morale":           initial_morale,
        "recent_events":    [],   # {key, day} — prevents same event repeating within a season
        "missed_payments":  0,
    }
    # Special tenant overrides — pin pay/damage, lock morale at 100
    if _is_special_tenant(t):
        prop["tenant"]["pay_chance"]    = 1.00
        prop["tenant"]["damage_chance"] = 0.00
        prop["tenant"]["morale"]        = 100
    # Phil — passive renovation work
    if t.get("is_phil"):
        prop["tenant"]["next_phil_work_day"] = s["day"] + 7
    # Goldbergs — automatically pays 10× fair rent regardless of what player set
    if t.get("is_goldbergs"):
        goldbergs_rent = calc_fair_weekly_rent(prop) * 10
        prop["tenant"]["rent"] = goldbergs_rent
        s["log"][-1]["text"] = (s["log"][-1]["text"]
            .replace(f"${weekly_rent:,}/wk", f"${goldbergs_rent:,}/wk (10× rent!)"))
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
    if prop["tenant"].get("is_phil"):      s["phil_cooldown_until"]      = s["day"] + DAYS_PER_SEASON * 4
    if prop["tenant"].get("is_baileys"):   s["baileys_cooldown_until"]   = s["day"] + DAYS_PER_SEASON * 2
    if prop["tenant"].get("is_goldbergs"): s["goldbergs_cooldown_until"] = s["day"] + DAYS_PER_SEASON * 2
    if prop["tenant"].get("is_mystery"):   s["mystery_cooldown_until"]   = s["day"] + DAYS_PER_SEASON * 2
    s["cash"] -= fee
    prop["tenant"] = None
    prop["vacant_since"] = s["day"]
    s["log"].append({"day": s["day"], "type": "evict",
        "text": f"Evicted {name} from {prop['type']} in {prop['neighborhood']} ($1,500 legal fees)"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

def _season_info(game_day):
    """Returns (season_idx, day_in_season). 0=Spring, 1=Summer, 2=Fall, 3=Winter."""
    season_idx    = (game_day - 1) // DAYS_PER_SEASON % 4
    day_in_season = (game_day - 1) % DAYS_PER_SEASON + 1
    return season_idx, day_in_season


@app.route('/api/advance', methods=['POST'])
def api_advance():
    data     = request.json
    days     = max(1, min(int(data.get("days", 1)), 30))
    s           = load()
    if any(isinstance(p.get("squatter"), dict) and p["squatter"].get("starter") for p in s["properties"]):
        return jsonify({"error": "There's a squatter in your house. Time isn't going anywhere until you deal with that."}), 400
    events             = []
    new_repairs        = []
    new_morale_events  = []
    new_renewal_offers = []
    rent_log           = {}   # prop_id -> summary dict
    squatter_spawned   = False

    tax_event = None

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
                    if t.get("is_phil"):      s["phil_cooldown_until"]      = current_day + DAYS_PER_SEASON * 4
                    if t.get("is_baileys"):   s["baileys_cooldown_until"]   = current_day + DAYS_PER_SEASON * 2
                    if t.get("is_goldbergs"): s["goldbergs_cooldown_until"] = current_day + DAYS_PER_SEASON * 2
                    if t.get("is_mystery"):   s["mystery_cooldown_until"]   = current_day + DAYS_PER_SEASON * 2
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
                    s["cash"]                       += rent
                    prop["total_rent_collected"]    += rent
                    rent_log[pid]["collected"]      += rent
                    s["tax_year_rent_income"]        = s.get("tax_year_rent_income", 0) + rent
                elif roll < t["pay_chance"] + 0.06:
                    partial = int(rent * 0.5)
                    s["cash"]                       += partial
                    prop["total_rent_collected"]    += partial
                    rent_log[pid]["collected"]      += partial
                    rent_log[pid]["partial"]        += 1
                    s["tax_year_rent_income"]        = s.get("tax_year_rent_income", 0) + partial
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
                                upg         = UPGRADES[wkey]
                                cond_change = tier_cond_change(tier_grade, upg["cond_boost"])
                                prop.setdefault("upgrades", {})[wkey] = {"quality": quality, "day": current_day}
                                prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_change))
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
        tenant_props = [p for p in s["properties"] if p.get("tenant") and not _is_special_tenant(p["tenant"])]
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
                prop["condition"]    = max(0, min(MAX_CONDITION, prop["condition"] + reno["cond_change"]))
                prop["pending_reno"] = None
                new_val = calc_market_value(prop)
                if reno.get("deferred_payment"):
                    # Vacant hire: work is done but upgrade not recorded until contractor is paid
                    prop["reno_payment_owed"] = {
                        "amount":      reno["cost"],
                        "name":        reno["name"],
                        "icon":        reno["icon"],
                        "upgrade_key": reno["upgrade_key"],
                        "quality":     reno["quality"],
                        "tier_key":    reno["tier_key"],
                        "cond_change": reno["cond_change"],
                        "due_since_day": current_day,
                    }
                    prop["reno_protected_until"] = current_day + 3
                    events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"🔨 {reno['name']} is done — pay the contractor ${reno['cost']:,} to see the grade!",
                                    "type": "warning"})
                    s["log"].insert(0, {"day": current_day, "type": "renovate",
                        "text": f"{reno['name']} at {prop['type']} in {prop['neighborhood']} done — contractor payment of ${reno['cost']:,} due"})
                else:
                    # Paid upfront — record upgrade immediately
                    prop.setdefault("upgrades", {})[reno["upgrade_key"]] = {
                        "quality": reno["quality"], "day": reno["complete_day"]}
                    if prop.get("tenant"):
                        prop["tenant"]["morale"] = min(100, prop["tenant"].get("morale", 50) + 8)
                    else:
                        prop["reno_protected_until"] = current_day + 3
                    events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                    "text": f"✅ {reno['name']} finished! Grade {reno['tier_key']}",
                                    "type": "positive"})
                    s["log"].insert(0, {"day": current_day, "type": "renovate",
                        "text": f"{reno['name']} at {prop['type']} in {prop['neighborhood']} completed — grade {reno['tier_key']}, value now ${new_val:,}"})

        # Contractor payment: interest after 3 days, destruction after 28
        for prop in s["properties"]:
            owed = prop.get("reno_payment_owed")
            if not owed:
                continue
            days_overdue = current_day - owed["due_since_day"]
            if days_overdue >= 28:
                # Contractor destroys the home — set to F condition, debt forgiven
                prop["condition"]         = 0
                prop["reno_payment_owed"] = None
                # Remove the upgrade record if it somehow got added
                prop.get("upgrades", {}).pop(owed["upgrade_key"], None)
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"🔥 Contractor destroyed {prop['type']} — unpaid for 28 days! Condition reset to F, debt forgiven.",
                                "type": "negative"})
                s["log"].insert(0, {"day": current_day, "type": "warning",
                    "text": f"Contractor destroyed {prop['type']} in {prop['neighborhood']} after 28 days without payment — condition set to F"})
            elif days_overdue > 3:
                new_amount = int(owed["amount"] * 1.03)
                owed["amount"] = new_amount
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                                "text": f"📈 Contractor payment grew 3% — now ${new_amount:,} owed ({28 - days_overdue} days left)",
                                "type": "negative"})

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
                        and not p.get("reno_payment_owed")
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

        # ── Tax system ────────────────────────────────────────────────────────
        _si, _di = _season_info(current_day)

        # Winter day 21: 7-day heads-up
        if _si == 3 and _di == 21:
            _flip = s.get("tax_year_flip_income", 0)
            _est  = int(_flip * 0.10)
            events.append({
                "prop": "Tax Notice",
                "text": f"📋 Tax Day is 7 days away (Winter Day 28)! Flip income this year: ${_flip:,} · Est. taxes: ${_est:,}",
                "type": "warning",
            })
            s["log"].insert(0, {"day": current_day, "type": "warning",
                "text": f"Tax reminder: ~${_est:,} due on Winter Day 28 from ${_flip:,} in flip profits"})

        # Winter day 28: tax due (only if no extension already filed)
        if _si == 3 and _di == 28 and not s.get("tax_extension_filed", False):
            _flip = s.get("tax_year_flip_income", 0)
            _owed = int(_flip * 0.10)
            tax_event = {"amount": _owed, "flip_income": _flip}
            events.append({
                "prop": "IRS",
                "text": f"🧾 Tax Day! ${_owed:,} owed on ${_flip:,} in flip profits — pay now or file for extension.",
                "type": "warning",
            })

        # Spring day 7: collect deferred extension tax
        if _si == 0 and _di == 7 and s.get("tax_extension_filed", False):
            _owed = s.get("tax_owed", 0)
            s["cash"] -= _owed
            s["tax_extension_filed"]  = False
            s["tax_year_flip_income"] = 0
            s["tax_year_rent_income"] = 0
            s["tax_owed"]             = 0
            events.append({
                "prop": "IRS",
                "text": f"🧾 Tax extension due today: -${_owed:,} collected",
                "type": "negative",
            })
            s["log"].insert(0, {"day": current_day, "type": "warning",
                "text": f"Tax extension payment of ${_owed:,} collected (Spring Day 7)"})

        # Refresh market each day advance for all currently unlocked neighborhoods
        _adv_unlocked = get_unlocked_neighborhoods(s.get("level", 0))
        s["market"], s["next_id"] = _gen_market(s["next_id"], hoods=_adv_unlocked)
        s["market_unlocked_hoods"] = list(_adv_unlocked)

    # Restore energy (additive recharge capped at home max) and refresh jobs
    max_e, rch = _get_home_stats(s)
    s["energy"] = min(max_e, s.get("energy", 0) + rch)
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

    _update_stock_prices(s, days)
    _roll_special_contractors(s)
    s["applicants_cache"] = {}   # fresh tenant pool each advance
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
        "tax_event":      tax_event,
    })


@app.route('/api/property/<int:pid>/pay_contractor', methods=['POST'])
def api_pay_contractor(pid):
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    owed = prop.get("reno_payment_owed")
    if not owed:
        return jsonify({"error": "No contractor payment owed"}), 400
    amount = owed["amount"]
    if s["cash"] < amount:
        return jsonify({"error": f"Not enough cash — you need ${amount:,}"}), 400
    s["cash"] -= amount
    # Now officially record the upgrade
    prop.setdefault("upgrades", {})[owed["upgrade_key"]] = {
        "quality": owed["quality"], "day": s["day"]}
    prop["reno_payment_owed"] = None
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Paid ${amount:,} for {owed['name']} at {prop['type']} in {prop['neighborhood']} — Grade {owed['tier_key']}"})
    save(s)
    return jsonify({"success": True, "amount_paid": amount, "cash": s["cash"],
                    "tier_key": owed["tier_key"], "upgrade_name": owed["name"]})


@app.route('/api/pay_taxes', methods=['POST'])
def api_pay_taxes():
    s = load()
    flip_income = s.get("tax_year_flip_income", 0)
    tax_owed    = int(flip_income * 0.10)
    s["cash"]  -= tax_owed
    s["tax_year_flip_income"] = 0
    s["tax_year_rent_income"] = 0
    s["tax_extension_filed"]  = False
    s["tax_owed"]             = 0
    s["log"].insert(0, {"day": s["day"], "type": "warning",
        "text": f"Paid ${tax_owed:,} in taxes (10% of ${flip_income:,} flip income)"})
    save(s)
    return jsonify({"success": True, "tax_paid": tax_owed, "cash": s["cash"]})


@app.route('/api/file_tax_extension', methods=['POST'])
def api_file_tax_extension():
    s = load()
    flip_income = s.get("tax_year_flip_income", 0)
    tax_owed    = int(flip_income * 0.10)
    s["tax_extension_filed"] = True
    s["tax_owed"]            = tax_owed
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Filed tax extension — ${tax_owed:,} due on Spring Day 7"})
    save(s)
    return jsonify({"success": True, "tax_owed": tax_owed, "cash": s["cash"]})


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
        if t.get("is_phil"):      s["phil_cooldown_until"]      = s["day"] + DAYS_PER_SEASON * 4
        if t.get("is_baileys"):   s["baileys_cooldown_until"]   = s["day"] + DAYS_PER_SEASON * 2
        if t.get("is_goldbergs"): s["goldbergs_cooldown_until"] = s["day"] + DAYS_PER_SEASON * 2
        if t.get("is_mystery"):   s["mystery_cooldown_until"]   = s["day"] + DAYS_PER_SEASON * 2
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
    cond_change = tier_cond_change(tier, upg["cond_boost"])
    s["energy"] = s.get("energy", DAILY_ENERGY) - energy_cost
    prop.setdefault("upgrades", {})[upgrade_key] = {"quality": quality, "day": s["day"]}
    prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_change))
    new_val = calc_market_value(prop)
    s["log"].append({"day": s["day"], "type": "renovate",
        "text": f"DIY {upg['name']} on {prop['type']} in {prop['neighborhood']} — grade {tier['key']}, value now ${new_val:,}"})
    xp_gain  = round(quality * 0.35)
    level_up = add_xp(s, xp_gain) if xp_gain > 0 else None
    save(s)
    return jsonify({"success": True, "quality": quality, "quality_tier": tier["key"],
                    "cond_change": cond_change, "cond_pct": tier["pct"], "condition": prop["condition"],
                    "market_value": new_val, "weekly_rent": calc_fair_weekly_rent(prop),
                    "energy": s["energy"], "level_up": level_up, "new_level": s.get("level", 0)})

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

    level_up = None
    if agree and morale_change > 0:
        xp_gain  = max(1, morale_change // 5)
        level_up = add_xp(s, xp_gain)

    save(s)
    return jsonify({
        "success":          True,
        "agree":            agree,
        "condition":        prop["condition"],
        "morale":           t.get("morale"),
        "condition_change": condition_change,
        "morale_change":    morale_change,
        "cash":             s["cash"],
        "level_up":         level_up,
        "new_level":        s.get("level", 0),
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
    xp_gain  = round(quality * 0.4)
    level_up = add_xp(s, xp_gain) if xp_gain > 0 else None
    save(s)
    return jsonify({"success": True, "pay": pay, "cash": s["cash"],
                    "energy": s["energy"], "quality": quality,
                    "level_up": level_up, "new_level": s.get("level", 0)})

@app.route('/api/intro/seen', methods=['POST'])
def api_intro_seen():
    s = load()
    s["intro_seen"] = True
    save(s)
    return jsonify({"success": True})

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
    # ── Bad word check — steal all cash, fires every time ──────────────────────
    if code in BAD_WORDS:
        stolen = s["cash"]
        s["cash"] = 0
        msg = "Hey, naughty naughty... that's not allowed here"
        s["log"].insert(0, {"day": s["day"], "type": "negative",
            "text": f"Bad language in the code box — lost ${stolen:,}"})
        save(s)
        return jsonify({"success": True, "reward_desc": msg, "cash_after": 0})
    if code not in CREATOR_CODES:
        return jsonify({"error": "Invalid code — try again!"}), 400
    redeemed = s.get("redeemed_codes", [])
    if code in redeemed:
        return jsonify({"error": "Code already used!"}), 400
    reward = CREATOR_CODES[code]
    s["cash"] += reward.get("cash", 0)
    if "level" in reward:
        s["level"] = reward["level"]
        s["xp"]    = reward.get("xp", XP_THRESHOLDS[reward["level"]])
    s.setdefault("redeemed_codes", []).append(code)
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Creator code redeemed — {reward['desc']}"})
    save(s)
    return jsonify({"success": True, "reward_desc": reward["desc"],
                    "level_up": s.get("level") if "level" in reward else None,
                    "new_level": s.get("level", 0)})

@app.route('/api/move_in', methods=['POST'])
def api_move_in():
    s    = load()
    data = request.json or {}
    key  = data.get("home_key", "")
    new_home = next((h for h in PLAYER_HOMES if h["key"] == key), None)
    if not new_home:
        return jsonify({"error": "Invalid home"}), 400
    unlocked_homes = get_unlocked_home_keys(s.get("level", 0))
    if key not in unlocked_homes:
        return jsonify({"error": "This home is locked — level up to unlock it!"}), 400
    current     = get_player_home(s)
    current_idx = next(i for i, h in enumerate(PLAYER_HOMES) if h["key"] == current["key"])
    new_idx     = next(i for i, h in enumerate(PLAYER_HOMES) if h["key"] == key)
    if new_idx <= current_idx:
        return jsonify({"error": "You already live somewhere better!"}), 400
    if new_home["cost"] > 0 and s["cash"] < new_home["cost"]:
        return jsonify({"error": f"Not enough cash — need ${new_home['cost']:,}"}), 400
    s["cash"] -= new_home["cost"]
    s["player_home"] = key
    # Cap current energy at new (bonused) max
    max_e, rch = _get_home_stats(s)
    s["energy"] = min(s.get("energy", 0), max_e)
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Moved into {new_home['name']}! Max energy now ⚡{max_e}, recharge +{rch}/day."})
    save(s)
    return jsonify({"success": True, "home": new_home["name"]})

@app.route('/api/education/buy_class', methods=['POST'])
def api_buy_diy_class():
    s         = load()
    data      = request.json or {}
    class_key = data.get("class_key", "")
    cls       = DIY_CLASSES.get(class_key)
    if not cls:
        return jsonify({"error": "Unknown class"}), 400
    classes = s.setdefault("diy_classes", {})
    if classes.get(class_key):
        return jsonify({"error": "You already completed this course!"}), 400
    if s.get("level", 0) < cls["unlock_level"]:
        return jsonify({"error": f"Reach Level {cls['unlock_level']} to unlock this course"}), 400
    max_e, _ = _get_home_stats(s)
    cur_e = s.get("energy", max_e)
    if cur_e < cls["energy_cost"]:
        return jsonify({"error": f"Not enough energy — need ⚡{cls['energy_cost']} (you have ⚡{cur_e})"}), 400
    s["energy"] = max(0, cur_e - cls["energy_cost"])
    classes[class_key] = True
    unlocks_str = " & ".join(cls["unlocks"])
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Completed {cls['name']} {cls['icon']} — DIY {unlocks_str} unlocked!"})
    save(s)
    return jsonify({"success": True, "class_name": cls["name"]})

@app.route('/api/store/buy_item', methods=['POST'])
def api_store_buy_item():
    s        = load()
    data     = request.json or {}
    item_key = data.get("item_key", "")
    item     = STORE_ITEMS.get(item_key)
    if not item:
        return jsonify({"error": "Unknown item"}), 400
    if item_key in {"coffee_maker", "new_bed"}:
        if any(isinstance(p.get("squatter"), dict) and p["squatter"].get("starter") for p in s["properties"]):
            return jsonify({"error": "Treat yourself later. Right now you've got a squatter problem."}), 400
    items = s.setdefault("owned_items", {})
    if items.get(item_key):
        return jsonify({"error": "You already own this!"}), 400
    if s["cash"] < item["cost"]:
        return jsonify({"error": f"Not enough cash — need ${item['cost']:,}"}), 400
    s["cash"] -= item["cost"]
    items[item_key] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bought {item['name']} {item['icon']} for ${item['cost']:,}!"})
    save(s)
    return jsonify({"success": True, "item": item["name"]})

@app.route('/api/stocks', methods=['GET', 'POST'])
def api_stocks():
    s  = load()
    ss  = s.setdefault("stocks", _init_stock_state())
    lvl = s.get("level", 0)
    portfolio = ss.get("portfolio", {})
    result = []
    for ticker, info in ALL_INSTRUMENTS.items():
        price    = ss["prices"].get(ticker, info["base_price"])
        hist     = ss["history"].get(ticker, [info["base_price"]])
        held     = portfolio.get(ticker, {})
        shares   = held.get("shares", 0)
        avg_cost = held.get("avg_cost", 0)
        gain     = round((price - avg_cost) * shares, 2) if shares > 0 else 0
        result.append({
            "ticker":   ticker,
            "name":     info["name"],
            "icon":     info["icon"],
            "desc":     info["desc"],
            "price":    price,
            "history":  hist[-20:],
            "shares":   shares,
            "avg_cost": avg_cost,
            "gain":     gain,
        })
    return jsonify({"instruments": result, "cash": s["cash"], "level": lvl})

@app.route('/api/stocks/buy', methods=['POST'])
def api_stocks_buy():
    s    = load()
    data = request.json or {}
    ticker = data.get("ticker", "").upper()
    shares = int(data.get("shares", 0))
    if ticker not in ALL_INSTRUMENTS:
        return jsonify({"error": "Unknown ticker"}), 400
    info = ALL_INSTRUMENTS[ticker]
    if s.get("level", 0) < 5:
        return jsonify({"error": "Stocks unlock at Level 5"}), 400
    if shares < 1:
        return jsonify({"error": "Must buy at least 1 share"}), 400
    ss    = s.setdefault("stocks", _init_stock_state())
    price = ss["prices"].get(ticker, info["base_price"])
    cost  = round(price * shares, 2)
    if s["cash"] < cost:
        return jsonify({"error": f"Not enough cash — need ${cost:,.2f}"}), 400
    s["cash"] -= cost
    port = ss.setdefault("portfolio", {})
    held = port.get(ticker, {"shares": 0, "avg_cost": 0})
    total_shares = held["shares"] + shares
    held["avg_cost"] = round((held["avg_cost"] * held["shares"] + cost) / total_shares, 4)
    held["shares"]   = total_shares
    port[ticker]     = held
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Bought {shares}x {info['name']} ({ticker}) @ ${price:,.2f} — total ${cost:,.2f}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "shares": held["shares"],
                    "avg_cost": held["avg_cost"], "spent": cost})

@app.route('/api/stocks/sell', methods=['POST'])
def api_stocks_sell():
    s    = load()
    data = request.json or {}
    ticker = data.get("ticker", "").upper()
    shares = int(data.get("shares", 0))
    if ticker not in ALL_INSTRUMENTS:
        return jsonify({"error": "Unknown ticker"}), 400
    if shares < 1:
        return jsonify({"error": "Must sell at least 1 share"}), 400
    ss   = s.setdefault("stocks", _init_stock_state())
    port = ss.setdefault("portfolio", {})
    held = port.get(ticker, {"shares": 0, "avg_cost": 0})
    if held["shares"] < shares:
        return jsonify({"error": f"You only own {held['shares']} share{'s' if held['shares'] != 1 else ''}"}), 400
    info  = ALL_INSTRUMENTS[ticker]
    price = ss["prices"].get(ticker, info["base_price"])
    proceeds = round(price * shares, 2)
    profit   = round(proceeds - held["avg_cost"] * shares, 2)
    s["cash"] += proceeds
    held["shares"] -= shares
    if held["shares"] == 0:
        port.pop(ticker, None)
    else:
        port[ticker] = held
    ptype = "positive" if profit >= 0 else "negative"
    s["log"].insert(0, {"day": s["day"], "type": ptype,
        "text": f"Sold {shares}x {info['name']} ({ticker}) @ ${price:,.2f} — {'profit' if profit >= 0 else 'loss'} ${abs(profit):,.2f}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "proceeds": proceeds,
                    "profit": profit, "shares_remaining": held["shares"]})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
