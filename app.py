from flask import Flask, render_template, jsonify, request, g
import json, os, random, copy
from dark_events import CREW_EVENTS, DEALER_EVENTS, LAUNDER_EVENTS

app = Flask(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

STARTING_CASH = 4_367

# `apr` is the BASE (good-credit) rate and `max` the BASE ceiling; both are scaled
# by the player's credit score at borrow time. `min_score` gates qualification.
LOAN_PRODUCTS = [
    {"key": "quick",    "name": "Quick Cash",    "icon": "💵", "min": 500,   "max": 5_000,   "apr": 0.24, "term_seasons": 2,  "min_score": 300, "desc": "Fast money, high interest. Anyone qualifies."},
    {"key": "personal", "name": "Personal Loan", "icon": "🤝", "min": 3_000, "max": 25_000,  "apr": 0.15, "term_seasons": 4,  "min_score": 560, "desc": "Reasonable rates for mid-range needs."},
    {"key": "property", "name": "Property Loan", "icon": "🏦", "min": 15000, "max": 75_000,  "apr": 0.09, "term_seasons": 8,  "min_score": 640, "desc": "Low rates for real estate investment."},
    {"key": "business", "name": "Business Loan", "icon": "💼", "min": 50000, "max": 150_000, "apr": 0.07, "term_seasons": 12, "min_score": 720, "desc": "Best rates — for borrowers with strong credit."},
]

# ── Credit score ────────────────────────────────────────────────────────────────
# 300–850 (FICO-style). On-time payments build it; missed payments + late fees wreck
# it. Score sets your effective APR (good credit = cheaper), your borrowing ceiling,
# and which loan products you qualify for. Refinance once your credit improves.
CREDIT_MIN, CREDIT_MAX, CREDIT_START = 300, 850, 600  # start qualifies for Quick Cash + Personal only
CREDIT_ONTIME_BONUS    = 2     # per on-time weekly payment
CREDIT_PAYOFF_BONUS    = 25    # for fully clearing a loan
CREDIT_MISSED_PENALTY  = 25    # per missed weekly payment (subtracted)
CREDIT_DRIFT           = 1     # weekly drift toward fair-credit baseline when debt-free
LOAN_LATE_FEE_PCT      = 0.05  # of the missed payment, added to the balance
LOAN_LATE_FEE_MIN      = 25
CREDIT_REFINANCE_FEE_PCT = 0.02  # of remaining balance, to refinance to a better rate

# ── Certificates of Deposit (term deposits) ─────────────────────────────────────
# Lock cash for a fixed term at a guaranteed total yield that beats savings — but
# it's illiquid, and cashing out early forfeits the interest plus a principal hit.
CD_MIN_DEPOSIT = 1_000
CD_EARLY_PENALTY_PCT = 0.03   # of principal, on early withdrawal (interest also forfeited)
CD_TERMS = [
    {"key": "s1", "name": "1-Season CD",       "term_seasons": 1, "yield": 0.05, "desc": "Locked for 1 season (28 days)."},
    {"key": "s2", "name": "2-Season CD",       "term_seasons": 2, "yield": 0.12, "desc": "Locked for 2 seasons (56 days)."},
    {"key": "s4", "name": "1-Year CD",         "term_seasons": 4, "yield": 0.28, "desc": "Locked for a full year (4 seasons)."},
]

SAVINGS_TIERS = [
    {"min": 0,      "label": "Basic",    "monthly_rate": 0.001, "apr": 1.2},
    {"min": 1_000,  "label": "Standard", "monthly_rate": 0.003, "apr": 3.6},
    {"min": 10_000, "label": "Premium",  "monthly_rate": 0.005, "apr": 6.0},
    {"min": 50_000, "label": "Elite",    "monthly_rate": 0.008, "apr": 9.6},
]

# ── Taxes ───────────────────────────────────────────────────────────────────────
# Rent is taxed gently (landlording is the core game). Business + flip profit ride
# a progressive bracket schedule — small operators pay little, empires pay real
# money (a much-needed late-game money sink). Operating expenses (wages, supplies,
# maintenance/repairs) are deductible from the business+flip side; capital
# renovations are NOT (they raise property value instead).
RENT_TAX_RATE = 0.05
TAX_BRACKETS = [   # (upper bound of the slice, marginal rate)
    (25_000,        0.08),
    (100_000,       0.15),
    (300_000,       0.22),
    (float("inf"),  0.30),
]
ACCOUNTANT_DEDUCTION_BONUS = 0.15  # Accountant assistant finds 15% more deductions you'd have missed

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
    "Midtown":            {"price_mult": 0.70, "rent_mult": 0.85, "desc": "Crumbling blocks, forgotten by time",       "tier": "budget"},
    "Northside":          {"price_mult": 0.85, "rent_mult": 0.97, "desc": "Gritty streets, high turnover",             "tier": "budget"},
    "Westwood":           {"price_mult": 1.00, "rent_mult": 1.00, "desc": "Solid middle-class area",                   "tier": "mid"},
    "Riverside":          {"price_mult": 1.40, "rent_mult": 1.35, "desc": "Desirable suburb, great schools",           "tier": "premium"},
    "Newbay":             {"price_mult": 1.60, "rent_mult": 1.55, "desc": "High-demand urban core",                    "tier": "premium"},
    "Cedarvale Estates":  {"price_mult": 1.80, "rent_mult": 1.70, "desc": "Exclusive custom-built community",          "tier": "premium"},
    "Commerce Row":       {"price_mult": 1.00, "rent_mult": 1.00, "desc": "The city's commercial and business core",    "tier": "commercial"},
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

# ── Repair Scenarios (choice-based; replaces the old fix-it/contractor/ignore flow) ──
# Each repair is a "how do you want to handle it?" card. Choices have:
#   label, cost (cash), cond (condition delta), morale (tenant morale delta), result text.
#   optional "risk": {"chance": 0-1, "cond": delta, "morale": delta, "result_bad": text}
#       — a baked-in gamble applied server-side (cheap/DIY fixes that might backfire).
#   optional "loyalty": tenant loyalty delta.
# A standard "Ignore it" choice is appended automatically based on "sev" (severity).
REPAIR_IGNORE_SEV = {"minor": (6, 10), "moderate": (11, 15), "major": (17, 22)}

REPAIR_SCENARIOS = [
    # ── Plumbing ────────────────────────────────────────────────────────────────
    {"key": "sink_leak", "title": "Leak Under the Sink", "icon": "🚰", "sev": "minor",
     "text": "{name} reports water pooling in the cabinet under the kitchen sink.", "choices": [
        {"label": "Call a plumber", "cost": 300, "cond": 12, "morale": 6, "result": "A pro swaps the corroded trap. Dry as a bone, tenant pleased."},
        {"label": "Patch it with a repair kit", "cost": 45, "cond": 5, "result": "The kit holds and the cabinet dries out.",
         "risk": {"chance": 0.30, "cond": -7, "result_bad": "The patch let go a week later and warped the cabinet floor."}},
        {"label": "Tighten the fitting yourself", "cost": 0, "cond": 3, "morale": -2, "result": "A wrench and ten minutes. Good enough for now."}]},
    {"key": "running_toilet", "title": "The Running Toilet", "icon": "🚽", "sev": "minor",
     "text": "{name}'s toilet won't stop running — and the water bill shows it.", "choices": [
        {"label": "Plumber replaces the guts", "cost": 140, "cond": 8, "morale": 4, "result": "New fill and flush valve. Blissful silence."},
        {"label": "Drop in a flapper kit", "cost": 20, "cond": 4, "result": "A two-dollar flapper does the trick."},
        {"label": "Jiggle-the-handle note to tenant", "cost": 0, "cond": 1, "morale": -3, "result": "You tell them to jiggle it. They are not thrilled."}]},
    {"key": "low_pressure", "title": "Weak Water Pressure", "icon": "🚿", "sev": "moderate",
     "text": "The whole unit's water pressure has dropped to a sad trickle, {name} says.", "choices": [
        {"label": "Repipe the corroded section", "cost": 650, "cond": 16, "morale": 6, "result": "Old galvanized pipe replaced. Showers feel brand new."},
        {"label": "Descale the fixtures", "cost": 120, "cond": 7, "result": "Cleaning the aerators and valves buys real improvement.",
         "risk": {"chance": 0.30, "cond": -6, "result_bad": "It helped for a day — the real problem is deeper in the pipes."}},
        {"label": "Tell them it's the city's mains", "cost": 0, "cond": 0, "morale": -6, "result": "You blame the city. They don't buy it."}]},
    {"key": "water_heater_leak", "title": "Leaking Water Heater", "icon": "🔥", "sev": "major",
     "text": "The water heater is weeping rust-colored water across the basement floor.", "choices": [
        {"label": "Replace the tank", "cost": 850, "cond": 20, "morale": 10, "result": "A new high-efficiency unit. Endless hot water, happy tenant."},
        {"label": "Patch it and add a drip pan", "cost": 180, "cond": 6, "result": "Bought some time and contained the mess.",
         "risk": {"chance": 0.40, "cond": -12, "morale": -6, "result_bad": "The tank failed completely days later — and flooded the basement."}},
        {"label": "It'll last a while longer", "cost": 0, "cond": -3, "morale": -5, "result": "You leave it. The drip becomes a puddle."}]},
    {"key": "sewer_smell", "title": "A Foul Smell", "icon": "🤢", "sev": "moderate",
     "text": "{name} keeps catching a sewer-gas smell from the bathroom drain.", "choices": [
        {"label": "Snake the line, fix the vent", "cost": 280, "cond": 12, "morale": 6, "result": "A clogged vent stack was the culprit. Air's fresh again."},
        {"label": "Pour in enzyme cleaner", "cost": 30, "cond": 4, "result": "The enzymes clear the gunk and the smell fades.",
         "risk": {"chance": 0.35, "cond": -8, "result_bad": "The smell came roaring back — it was a cracked drain line all along."}},
        {"label": "Suggest an air freshener", "cost": 0, "cond": -1, "morale": -5, "result": "A plug-in masks it. Barely."}]},
    {"key": "burst_pipe", "title": "Burst Pipe in the Wall", "icon": "💥", "sev": "major",
     "text": "A pipe let go inside the wall and water is coming through the drywall fast.", "choices": [
        {"label": "Emergency plumber, now", "cost": 700, "cond": 22, "morale": 8, "result": "Shut off, repaired, drywall patched. Disaster averted."},
        {"label": "Kill the water, clamp it yourself", "cost": 150, "cond": 8, "result": "A pipe clamp and a fan. Crisis managed for now.",
         "risk": {"chance": 0.45, "cond": -14, "morale": -8, "result_bad": "The clamp slipped overnight — extensive water damage and mold risk."}},
        {"label": "Mop it and hope", "cost": 0, "cond": -6, "morale": -10, "result": "You mop up. The wall behind stays soaked."}]},
    # ── Electrical ──────────────────────────────────────────────────────────────
    {"key": "flickering_lights", "title": "Flickering Lights", "icon": "💡", "sev": "moderate",
     "text": "Lights across the unit flicker whenever the fridge kicks on. {name} is uneasy.", "choices": [
        {"label": "Electrician traces the wiring", "cost": 520, "cond": 15, "morale": 6, "result": "A loose neutral, found and fixed. Rock-steady lights."},
        {"label": "Swap the worst fixtures", "cost": 90, "cond": 6, "result": "New fixtures calm most of the flicker.",
         "risk": {"chance": 0.30, "cond": -8, "result_bad": "It wasn't the fixtures — the flickering hid a real wiring fault."}},
        {"label": "Probably just the bulbs", "cost": 0, "cond": 0, "morale": -5, "result": "You blame the bulbs. The flicker continues, ominously."}]},
    {"key": "tripping_breaker", "title": "The Tripping Breaker", "icon": "⚡", "sev": "moderate",
     "text": "The kitchen breaker trips constantly and {name} is tired of resetting it.", "choices": [
        {"label": "Upgrade the panel circuit", "cost": 900, "cond": 18, "morale": 8, "result": "A dedicated circuit ends the tripping for good."},
        {"label": "Rebalance the loads", "cost": 60, "cond": 5, "result": "An electrician redistributes the circuits. Better.",
         "risk": {"chance": 0.30, "cond": -7, "result_bad": "Still trips under load — the panel itself is undersized."}},
        {"label": "Tell them to unplug things", "cost": 0, "cond": 0, "morale": -6, "result": "Your advice: run fewer appliances. They're unimpressed."}]},
    {"key": "dead_outlets", "title": "Dead Outlets", "icon": "🔌", "sev": "minor",
     "text": "Half the outlets in the living room have gone dead, {name} reports.", "choices": [
        {"label": "Electrician rewires them", "cost": 240, "cond": 10, "morale": 4, "result": "A failed outlet upstream was the cause. All live again."},
        {"label": "Replace the outlets yourself", "cost": 35, "cond": 5, "result": "New outlets, carefully wired. Power restored.",
         "risk": {"chance": 0.25, "cond": -6, "result_bad": "A miswire popped the GFCI and you had to call a pro anyway."}},
        {"label": "Point them to a power strip", "cost": 0, "cond": 0, "morale": -4, "result": "An extension cord 'solution.' Not ideal."}]},
    {"key": "smoke_detector", "title": "Chirping Smoke Alarms", "icon": "🚨", "sev": "minor",
     "text": "The smoke detectors are chirping and at least one is fully dead — a real safety issue.", "choices": [
        {"label": "Replace all detectors", "cost": 90, "cond": 5, "morale": 8, "loyalty": 4, "result": "Fresh hardwired detectors throughout. {name} feels safe."},
        {"label": "Fresh batteries all around", "cost": 15, "cond": 2, "morale": 3, "result": "New batteries hush the chirping."},
        {"label": "Tell them to pull the battery", "cost": 0, "cond": -2, "morale": -8, "result": "Disabling a smoke alarm. They know it's wrong, and so do you."}]},
    # ── HVAC ──────────────────────────────────────────────────────────────────
    {"key": "ac_dead", "title": "The AC Died", "icon": "🥵", "sev": "major",
     "text": "The air conditioning quit and {name} is sweltering through a heat wave.", "choices": [
        {"label": "Install a new AC unit", "cost": 1100, "cond": 20, "morale": 12, "result": "Cool, quiet, efficient. Tenant practically weeps with relief."},
        {"label": "Recharge and repair the old one", "cost": 260, "cond": 8, "result": "A recharge and a new capacitor bring it back to life.",
         "risk": {"chance": 0.35, "cond": -6, "morale": -6, "result_bad": "The compressor was shot — the repair money was wasted."}},
        {"label": "Drop off window units", "cost": 150, "cond": 3, "morale": 4, "result": "Two window units take the edge off the heat."},
        {"label": "It'll cool down at night", "cost": 0, "cond": -4, "morale": -12, "result": "You wait it out. They do not forgive easily."}]},
    {"key": "furnace_out", "title": "No Heat", "icon": "❄️", "sev": "major",
     "text": "The furnace won't fire and the unit is getting cold fast, {name} warns.", "choices": [
        {"label": "Replace the furnace", "cost": 1000, "cond": 20, "morale": 12, "result": "A new furnace roars to life. Toasty and reliable."},
        {"label": "Repair the igniter", "cost": 220, "cond": 8, "result": "A new igniter and it lights right up.",
         "risk": {"chance": 0.30, "cond": -8, "morale": -6, "result_bad": "The heat exchanger was cracked — it needs full replacement after all."}},
        {"label": "Lend them space heaters", "cost": 80, "cond": 2, "morale": 3, "result": "Space heaters keep the chill off, for now."},
        {"label": "Tell them to bundle up", "cost": 0, "cond": -4, "morale": -12, "result": "Sweaters as a heating plan. They start apartment-hunting."}]},
    {"key": "clogged_filter", "title": "Weak Airflow", "icon": "🌬️", "sev": "minor",
     "text": "{name} says barely any air comes from the vents lately.", "choices": [
        {"label": "Full HVAC service + new filters", "cost": 90, "cond": 6, "morale": 3, "result": "Cleaned coils and fresh filters. Airflow restored."},
        {"label": "Swap the filter yourself", "cost": 0, "cond": 3, "result": "A $5 filter and the vents breathe again."},
        {"label": "Tell them it's fine", "cost": 0, "cond": -1, "morale": -4, "result": "You wave it off. The system keeps straining."}]},
    {"key": "thermostat_dead", "title": "Dead Thermostat", "icon": "🌡️", "sev": "minor",
     "text": "The thermostat's screen is black and the system won't respond.", "choices": [
        {"label": "Install a smart thermostat", "cost": 180, "cond": 8, "morale": 4, "result": "A sleek smart stat — lower bills and a delighted tenant."},
        {"label": "Basic replacement", "cost": 40, "cond": 4, "result": "A simple new thermostat. Back in business."},
        {"label": "Reset the breaker and pray", "cost": 0, "cond": 1, "morale": -3, "result": "A reset gets a flicker of life. Temporary at best."}]},
    {"key": "duct_leak", "title": "Leaky Ductwork", "icon": "♨️", "sev": "moderate",
     "text": "Heating bills are sky-high and {name} suspects the ducts are leaking.", "choices": [
        {"label": "Seal and insulate the ducts", "cost": 300, "cond": 12, "morale": 6, "result": "Sealed ducts, even temperatures, lower bills all around."},
        {"label": "Foil-tape the obvious gaps", "cost": 40, "cond": 5, "result": "Taping the accessible joints helps noticeably.",
         "risk": {"chance": 0.30, "cond": -6, "result_bad": "The worst leaks were buried in the walls — bills stayed high."}},
        {"label": "Ignore the bills", "cost": 0, "cond": -2, "morale": -4, "result": "The drafts and the bills both linger."}]},
    # ── Roof & Exterior ──────────────────────────────────────────────────────
    {"key": "roof_leak", "title": "The Roof Leaks", "icon": "🏚️", "sev": "major",
     "text": "A brown stain blooms across {name}'s ceiling every time it rains.", "choices": [
        {"label": "Re-roof the failing section", "cost": 850, "cond": 20, "morale": 8, "result": "New shingles and flashing. Bone dry through the next storm."},
        {"label": "Tar-patch the leak", "cost": 160, "cond": 8, "result": "A roofing patch stops the drip for now.",
         "risk": {"chance": 0.40, "cond": -12, "result_bad": "The patch failed in the next downpour — the deck is rotting."}},
        {"label": "Put a bucket under it", "cost": 0, "cond": -6, "morale": -8, "result": "A bucket and a prayer. The stain keeps spreading."}]},
    {"key": "gutter_fail", "title": "Overflowing Gutters", "icon": "🍂", "sev": "moderate",
     "text": "The gutters are sheeting water down the siding and pooling at the foundation.", "choices": [
        {"label": "Replace gutters, add guards", "cost": 380, "cond": 14, "morale": 4, "result": "New seamless gutters with guards. Low-maintenance and dry."},
        {"label": "Clean them out", "cost": 60, "cond": 5, "result": "A good clearing gets them flowing again."},
        {"label": "Wait for a dry spell", "cost": 0, "cond": -3, "result": "You leave it. The siding starts to stain and swell."}]},
    {"key": "siding_rot", "title": "Rotting Siding", "icon": "🪵", "sev": "moderate",
     "text": "A patch of exterior siding has gone soft and spongy with rot.", "choices": [
        {"label": "Replace the rotted boards", "cost": 420, "cond": 14, "morale": 4, "result": "New boards, primed and painted. Solid and sharp."},
        {"label": "Paint over the soft spots", "cost": 80, "cond": 5, "result": "Filler and paint hide it for the season.",
         "risk": {"chance": 0.35, "cond": -8, "result_bad": "The rot spread underneath the paint — now it's a bigger job."}},
        {"label": "Leave it", "cost": 0, "cond": -2, "result": "The rot quietly creeps along the wall."}]},
    {"key": "chimney_crack", "title": "Cracked Chimney", "icon": "🧱", "sev": "moderate",
     "text": "The chimney's mortar is crumbling and a few bricks have shifted.", "choices": [
        {"label": "Repoint the brickwork", "cost": 340, "cond": 12, "morale": 4, "result": "Fresh mortar and a cap. Sound for decades."},
        {"label": "Seal the worst cracks", "cost": 70, "cond": 5, "result": "A masonry sealant buys time.",
         "risk": {"chance": 0.30, "cond": -7, "result_bad": "Water got behind the seal and a freeze popped more bricks loose."}},
        {"label": "It's just cosmetic", "cost": 0, "cond": -2, "result": "You decide it can wait. The crack widens."}]},
    {"key": "foundation_crack", "title": "Foundation Cracks", "icon": "🏗️", "sev": "major",
     "text": "Cracks are spidering up a foundation wall — could be settling, could be worse.", "choices": [
        {"label": "Assess and stabilize", "cost": 750, "cond": 18, "morale": 6, "result": "Caught early and braced. The structure is secure."},
        {"label": "Epoxy-fill the cracks", "cost": 130, "cond": 6, "result": "Injected epoxy seals them up cosmetically.",
         "risk": {"chance": 0.40, "cond": -12, "result_bad": "The settling continued — the cracks reopened, wider than before."}},
        {"label": "Houses settle, right?", "cost": 0, "cond": -5, "morale": -4, "result": "You hope it's nothing. The cracks say otherwise."}]},
    {"key": "broken_window", "title": "Shattered Window", "icon": "🪟", "sev": "minor",
     "text": "A window pane shattered and {name} has it taped up with cardboard.", "choices": [
        {"label": "Glazier installs new glass", "cost": 180, "cond": 8, "morale": 4, "result": "A clean new pane. Light and security restored."},
        {"label": "DIY glass kit", "cost": 40, "cond": 4, "result": "You fit a replacement pane yourself. Tidy enough.",
         "risk": {"chance": 0.25, "cond": -5, "result_bad": "The pane cracked during install and you had to redo it."}},
        {"label": "Leave the cardboard", "cost": 0, "cond": -3, "morale": -6, "result": "Cardboard and tape. Not a great look for the block."}]},
    # ── Appliances ────────────────────────────────────────────────────────────
    {"key": "fridge_dying", "title": "Fridge on the Fritz", "icon": "🧊", "sev": "moderate",
     "text": "The refrigerator is humming loudly, leaking, and barely keeping cold.", "choices": [
        {"label": "Buy a new fridge", "cost": 640, "cond": 10, "morale": 8, "result": "A shiny efficient fridge. {name} is thrilled."},
        {"label": "Repair the compressor", "cost": 180, "cond": 5, "result": "A compressor relay swap brings it back.",
         "risk": {"chance": 0.40, "cond": -4, "morale": -5, "result_bad": "It died for good a week later — money down the drain."}},
        {"label": "Grab a used replacement", "cost": 220, "cond": 6, "morale": 3, "result": "A decent secondhand unit does the job."},
        {"label": "Tell them to defrost it", "cost": 0, "cond": -2, "morale": -6, "result": "Your fix: defrost it more. The groceries disagree."}]},
    {"key": "dishwasher_leak", "title": "Leaking Dishwasher", "icon": "🍽️", "sev": "minor",
     "text": "The dishwasher is leaving a puddle across the kitchen floor each cycle.", "choices": [
        {"label": "Replace the dishwasher", "cost": 480, "cond": 8, "morale": 5, "result": "A quiet new unit, properly plumbed. No more puddles."},
        {"label": "Reseal the door gasket", "cost": 40, "cond": 4, "result": "A fresh gasket stops the leak.",
         "risk": {"chance": 0.30, "cond": -5, "result_bad": "The leak was from the pump, not the door — it's back."}},
        {"label": "They can hand-wash", "cost": 0, "cond": -1, "morale": -5, "result": "Hand-washing as a 'feature.' They're not amused."}]},
    {"key": "oven_out", "title": "The Oven Won't Heat", "icon": "🔥", "sev": "moderate",
     "text": "{name}'s oven won't come up to temperature anymore.", "choices": [
        {"label": "Install a new range", "cost": 560, "cond": 9, "morale": 6, "result": "A gleaming new range. Baking season is saved."},
        {"label": "Replace the heating element", "cost": 70, "cond": 5, "result": "A new bake element and it's good as new."},
        {"label": "Suggest the microwave", "cost": 0, "cond": -1, "morale": -5, "result": "Microwave dinners indefinitely. A hard sell."}]},
    {"key": "washer_broke", "title": "The Washer Died", "icon": "🧺", "sev": "minor",
     "text": "The washing machine stopped mid-cycle and won't drain, {name} says.", "choices": [
        {"label": "Replace the washer", "cost": 520, "cond": 8, "morale": 5, "result": "A new washer, properly leveled. Laundry day restored."},
        {"label": "Repair the belt and pump", "cost": 90, "cond": 4, "result": "A belt and pump fix gets it spinning.",
         "risk": {"chance": 0.30, "cond": -4, "result_bad": "The motor was failing too — it quit again within days."}},
        {"label": "Point them to a laundromat", "cost": 0, "cond": -1, "morale": -5, "result": "Hauling laundry across town. They're not happy."}]},
    {"key": "garbage_disposal", "title": "Jammed Disposal", "icon": "🌀", "sev": "minor",
     "text": "The garbage disposal is jammed and humming ominously.", "choices": [
        {"label": "Plumber clears and resets it", "cost": 130, "cond": 5, "morale": 3, "result": "Unjammed and tested. Grinding happily again."},
        {"label": "Reset and free it yourself", "cost": 0, "cond": 3, "result": "The reset button and a hex key do the trick.",
         "risk": {"chance": 0.20, "cond": -3, "result_bad": "Something metal had wrecked the blades — it needs replacing."}},
        {"label": "Tell them to stop using it", "cost": 0, "cond": -1, "morale": -3, "result": "A disposal they can't use. Minor, but annoying."}]},
    # ── Pests & Bio ────────────────────────────────────────────────────────────
    {"key": "roaches", "title": "Roach Problem", "icon": "🪳", "sev": "moderate",
     "text": "{name} has spotted roaches in the kitchen — and where there's one...", "choices": [
        {"label": "Hire an exterminator", "cost": 320, "cond": 12, "morale": 8, "result": "A full treatment and follow-up. Pest-free and grateful."},
        {"label": "Store-bought baits and spray", "cost": 35, "cond": 4, "morale": -2, "result": "The baits knock the population down a lot.",
         "risk": {"chance": 0.50, "cond": -8, "morale": -6, "result_bad": "They came right back — an infestation needs the pros."}},
        {"label": "Tell them to clean more", "cost": 0, "cond": -3, "morale": -10, "result": "Blaming the tenant. The roaches multiply regardless."}]},
    {"key": "mice", "title": "Mice in the Walls", "icon": "🐭", "sev": "moderate",
     "text": "Scratching in the walls at night — {name} is sure it's mice.", "choices": [
        {"label": "Pro pest control + seal entry", "cost": 280, "cond": 12, "morale": 8, "result": "Trapped, removed, and sealed out. Quiet nights again."},
        {"label": "Set traps yourself", "cost": 30, "cond": 5, "result": "A line of traps thins them out.",
         "risk": {"chance": 0.40, "cond": -6, "morale": -4, "result_bad": "Without sealing the gaps, the mice just kept coming."}},
        {"label": "Get them a cat? (decline)", "cost": 0, "cond": -3, "morale": -8, "result": "You shrug it off. The scratching gets louder."}]},
    {"key": "termites", "title": "Termite Damage", "icon": "🐜", "sev": "major",
     "text": "An inspection turned up active termites in a structural beam.", "choices": [
        {"label": "Full treatment + repair", "cost": 900, "cond": 18, "morale": 6, "result": "Colony eradicated, beam reinforced. Structure saved."},
        {"label": "Spot-treat the visible damage", "cost": 200, "cond": 6, "result": "A targeted treatment hits the active area.",
         "risk": {"chance": 0.50, "cond": -14, "result_bad": "The colony was far larger — they kept eating through the framing."}},
        {"label": "Hope they move on", "cost": 0, "cond": -8, "morale": -4, "result": "Termites do not move on. They feast."}]},
    {"key": "wasp_nest", "title": "Wasp Nest by the Door", "icon": "🐝", "sev": "minor",
     "text": "A wasp nest has appeared right beside the front door. {name} is dodging it daily.", "choices": [
        {"label": "Pro removal", "cost": 110, "cond": 4, "morale": 6, "result": "Gone safely, no stings. Easy in and out again."},
        {"label": "Knock it down at dusk yourself", "cost": 0, "cond": 2, "morale": -3, "result": "A can of spray and quick aim. Handled.",
         "risk": {"chance": 0.40, "cond": -4, "morale": -5, "result_bad": "You got swarmed and the tenant got stung. Bad scene."}},
        {"label": "Just avoid that door", "cost": 0, "cond": -1, "morale": -6, "result": "Telling them to use the back door. Not a fix."}]},
    {"key": "mold", "title": "Mold Patch", "icon": "🦠", "sev": "moderate",
     "text": "Black mold is creeping up the bathroom wall and {name} is worried about the air.", "choices": [
        {"label": "Professional remediation", "cost": 400, "cond": 15, "morale": 8, "result": "Source found, sealed, and the mold's gone for good."},
        {"label": "Bleach it and add a fan", "cost": 50, "cond": 5, "result": "Scrubbed and ventilated — looks clean now.",
         "risk": {"chance": 0.45, "cond": -10, "morale": -6, "result_bad": "It bloomed right back — the moisture source was never fixed."}},
        {"label": "Tell them to wipe it down", "cost": 0, "cond": -4, "morale": -8, "result": "A rag won't stop mold. It spreads behind the tile."}]},
    # ── Structural, Safety & Misc ────────────────────────────────────────────
    {"key": "stair_rot", "title": "Rotting Porch Steps", "icon": "🪜", "sev": "moderate",
     "text": "The porch steps are soft and one cracked under {name}'s foot — a real hazard.", "choices": [
        {"label": "Rebuild the steps", "cost": 360, "cond": 12, "morale": 6, "loyalty": 4, "result": "Solid new treads and stringers. Safe and sturdy."},
        {"label": "Reinforce the worst tread", "cost": 80, "cond": 5, "result": "A sister board shores up the bad step.",
         "risk": {"chance": 0.30, "cond": -7, "morale": -6, "result_bad": "Another step gave way — the whole stringer was rotten."}},
        {"label": "Add a 'watch your step' note", "cost": 0, "cond": -3, "morale": -8, "result": "A sign instead of a repair. Someone could get hurt."}]},
    {"key": "floor_squeak", "title": "Soft, Squeaky Floor", "icon": "🪵", "sev": "minor",
     "text": "A spot in the hallway floor squeaks loudly and feels a little spongy underfoot.", "choices": [
        {"label": "Repair the subfloor", "cost": 300, "cond": 10, "morale": 4, "result": "The subfloor's re-secured and refinished. Silent and solid."},
        {"label": "Screw it down yourself", "cost": 30, "cond": 4, "result": "A few deck screws into the joist quiet it down."},
        {"label": "It adds character", "cost": 0, "cond": -1, "morale": -3, "result": "You call the squeak 'charm.' They call it annoying."}]},
    {"key": "door_wont_lock", "title": "Front Door Won't Lock", "icon": "🔒", "sev": "minor",
     "text": "The front door deadbolt is sticking and won't reliably lock — a security worry for {name}.", "choices": [
        {"label": "Install a new deadbolt", "cost": 90, "cond": 5, "morale": 8, "loyalty": 4, "result": "A smooth new lock. They sleep easier tonight."},
        {"label": "Lubricate and realign it", "cost": 0, "cond": 3, "morale": 2, "result": "Some graphite and a strike-plate tweak. Working again."},
        {"label": "Tell them to use the chain", "cost": 0, "cond": -2, "morale": -8, "result": "A door chain isn't a deadbolt. They feel unsafe."}]},
    {"key": "ceiling_stain", "title": "Spreading Ceiling Stain", "icon": "🟤", "sev": "moderate",
     "text": "A brown stain on the ceiling is slowly growing — something's leaking above.", "choices": [
        {"label": "Find the leak and repair", "cost": 420, "cond": 14, "morale": 6, "result": "Traced to a loose supply line, fixed and repainted. Done right."},
        {"label": "Paint over the stain", "cost": 50, "cond": 4, "result": "A stain-blocking coat hides it nicely.",
         "risk": {"chance": 0.50, "cond": -9, "result_bad": "The leak kept going — the stain bled right back through the paint."}},
        {"label": "It's barely noticeable", "cost": 0, "cond": -4, "result": "You ignore it. The stain — and the leak — keep growing."}]},
    {"key": "driveway_crack", "title": "Cracked Driveway", "icon": "🛣️", "sev": "minor",
     "text": "The driveway has cracked badly and a lip is becoming a trip hazard.", "choices": [
        {"label": "Repave it", "cost": 500, "cond": 10, "morale": 4, "result": "Smooth fresh asphalt. Curb appeal way up."},
        {"label": "Fill the cracks", "cost": 60, "cond": 4, "result": "Crack filler levels the worst of it."},
        {"label": "Leave it", "cost": 0, "cond": -2, "result": "The cracks widen with every freeze."}]},
    {"key": "fence_down", "title": "Fence Section Down", "icon": "🚧", "sev": "minor",
     "text": "A storm knocked down a section of the backyard fence.", "choices": [
        {"label": "Replace the section", "cost": 300, "cond": 8, "morale": 4, "result": "New posts and panels. Yard's secure again."},
        {"label": "Prop and patch it", "cost": 60, "cond": 4, "result": "Braced and re-screwed. Standing for now.",
         "risk": {"chance": 0.30, "cond": -5, "result_bad": "The next gust took it down again, worse this time."}},
        {"label": "Leave it leaning", "cost": 0, "cond": -2, "morale": -3, "result": "The gap stays. The neighbor's dog visits often."}]},
    {"key": "garage_door", "title": "Garage Door Stuck", "icon": "🚙", "sev": "minor",
     "text": "The garage door opener gave out — with {name}'s car trapped inside.", "choices": [
        {"label": "New opener + tune-up", "cost": 240, "cond": 8, "morale": 5, "result": "A quiet new opener and balanced springs. Smooth as silk."},
        {"label": "Repair the motor", "cost": 90, "cond": 5, "result": "A gear kit gets it moving again.",
         "risk": {"chance": 0.30, "cond": -4, "result_bad": "A spring snapped soon after — the whole unit needs replacing."}},
        {"label": "They can lift it by hand", "cost": 0, "cond": -1, "morale": -4, "result": "Manual operation as the plan. A daily hassle."}]},
    # ── Weather / Emergency ──────────────────────────────────────────────────
    {"key": "frozen_pipe", "title": "A Frozen Pipe", "icon": "🧊", "sev": "major",
     "text": "A pipe froze overnight and cracked — water's seeping out as it thaws.", "choices": [
        {"label": "Emergency repair + insulate", "cost": 650, "cond": 18, "morale": 8, "result": "Replaced and insulated against the next freeze. Solid."},
        {"label": "Thaw it and clamp the crack", "cost": 120, "cond": 6, "result": "A clamp holds the split for now.",
         "risk": {"chance": 0.50, "cond": -12, "morale": -6, "result_bad": "The clamp failed and the line burst fully — major water damage."}},
        {"label": "Let it thaw naturally", "cost": 0, "cond": -6, "morale": -8, "result": "You wait. The crack widens as it thaws and floods the floor."}]},
    {"key": "storm_damage", "title": "Storm Knocked Shingles Loose", "icon": "🌬️", "sev": "moderate",
     "text": "Last night's storm tore several shingles loose and exposed the roof deck.", "choices": [
        {"label": "Roofer replaces the shingles", "cost": 420, "cond": 14, "morale": 5, "result": "New shingles and flashing. Watertight before the next storm."},
        {"label": "Tarp it temporarily", "cost": 70, "cond": 5, "result": "A secured tarp keeps the rain out for now.",
         "risk": {"chance": 0.40, "cond": -8, "result_bad": "Wind ripped the tarp off and the deck soaked through."}},
        {"label": "It'll probably be fine", "cost": 0, "cond": -5, "morale": -4, "result": "You leave the deck exposed. The next rain finds it."}]},
    {"key": "ice_dam", "title": "Ice Dam on the Roof", "icon": "🏔️", "sev": "moderate",
     "text": "An ice dam has formed at the eaves and meltwater is backing up under the shingles.", "choices": [
        {"label": "Steam removal + insulate attic", "cost": 380, "cond": 13, "morale": 5, "result": "Dam cleared and the attic insulated to prevent the next one."},
        {"label": "Chip the ice off yourself", "cost": 0, "cond": 3, "result": "Hours of careful chipping clears the worst of it.",
         "risk": {"chance": 0.40, "cond": -9, "result_bad": "You gouged the shingles and the meltwater got into the ceiling."}},
        {"label": "Wait for the thaw", "cost": 0, "cond": -4, "morale": -3, "result": "You wait it out. The water finds its way inside."}]},
    {"key": "gas_smell", "title": "A Faint Gas Smell", "icon": "🟡", "sev": "major",
     "text": "{name} reports a faint smell of gas near the furnace — this needs a careful response.", "choices": [
        {"label": "Shut off gas & call the utility (free)", "cost": 0, "cond": 6, "morale": 10, "loyalty": 4, "result": "You do it right: gas off, utility out same day. A loose fitting, tightened. Safe."},
        {"label": "Hire a private tech to inspect", "cost": 280, "cond": 14, "morale": 8, "result": "A thorough inspection finds and fixes a small leak. Peace of mind."},
        {"label": "Crack a window and wait", "cost": 0, "cond": -8, "morale": -14, "result": "Ignoring a gas smell. Reckless — and the tenant is rightly furious."}]},
]

def _repair_choices(sc):
    """Full ordered choice list for a repair scenario, with a standard Ignore appended."""
    choices = [dict(c) for c in sc["choices"]]
    cond, mor = REPAIR_IGNORE_SEV.get(sc.get("sev", "moderate"), (11, 15))
    choices.append({
        "label": "Ignore it for now", "cost": 0, "cond": -cond, "morale": -mor, "ignore": True,
        "result": sc.get("ignore_result",
                         "You let it slide. The problem festers — the property's condition drops and your tenant's patience wears thin."),
    })
    return choices

# ── Tenant Event System ────────────────────────────────────────────────────────
# One event can fire per day when the global roll succeeds.
# Chance = 15% base + 1% per tenant (capped at 75%).
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
    # ── Special auto events: cash ──────────────────────────────────────────────
    # Fires silently; adds cash_min–cash_max to player's cash.
    {
        "key": "tenant_gift", "weight": 3, "type": "cash_auto",
        "name": "Tenant Gift", "icon": "💝",
        "cash_min": 150, "cash_max": 400,
        "message": "left you a cash gift — a thank-you for being a great landlord",
    },
    {
        "key": "scratch_ticket", "weight": 3, "type": "cash_auto",
        "name": "Lucky Scratch Ticket", "icon": "🎰",
        "cash_min": 50, "cash_max": 200,
        "message": "found a scratch ticket in the couch cushions and split their winnings with you",
    },
    {
        "key": "holiday_gift", "weight": 3, "type": "cash_auto",
        "name": "Holiday Gift", "icon": "🎁",
        "cash_min": 75, "cash_max": 150,
        "message": "left a holiday gift and a card — it was a thoughtful gesture",
    },
    {
        "key": "found_in_walls", "weight": 2, "type": "cash_auto",
        "name": "Found in the Walls", "icon": "💎",
        "cash_min": 300, "cash_max": 800,
        "message": "found something valuable inside the walls during a minor repair and split it with you",
    },

    # ── Special auto events: condition restore ─────────────────────────────────
    # Fires silently; restores cond_gain pts to condition, capped at MAX_CONDITION.
    # Optional filters: max_condition (fires only if condition <= this),
    #                   min_morale (fires only if tenant morale >= this).
    {
        "key": "property_of_year", "weight": 2, "type": "cond_auto",
        "name": "Property of the Year", "icon": "🏆",
        "cond_gain": 10,
        "message": "A local neighborhood blog named your property 'Hidden Gem of the Block'",
    },
    {
        "key": "deep_clean", "weight": 3, "type": "cond_auto",
        "name": "Tenant Deep Clean", "icon": "🧹",
        "cond_gain": 15, "min_morale": 80,
        "message": "deep cleaned the entire place before you could schedule it",
    },
    {
        "key": "self_fix_window", "weight": 4, "type": "cond_auto",
        "name": "Self-Fixed Window", "icon": "🪟",
        "cond_gain": 5,
        "message": "broke a window and quietly fixed it themselves, out of pocket. You noticed when it looked better than before",
    },
    {
        "key": "planted_tree", "weight": 3, "type": "cond_auto",
        "name": "Planted a Tree", "icon": "🌳",
        "cond_gain": 8,
        "message": "planted a nice tree in the yard without asking. It's genuinely a nice tree",
    },
    {
        "key": "green_thumb", "weight": 3, "type": "cond_auto",
        "name": "Green Thumb Tenant", "icon": "🌿",
        "cond_gain": 25, "max_condition": 175,
        "message": "has been maintaining the landscaping entirely on their own, without being asked",
    },
    {
        "key": "handy_tenant", "weight": 3, "type": "cond_auto",
        "name": "Handy Tenant", "icon": "🏗️",
        "cond_gain": 20,
        "message": "patched the drywall on their own — properly, with compound and everything",
    },
    {
        "key": "energy_savings", "weight": 4, "type": "cond_auto",
        "name": "Energy Upgrades", "icon": "🔋",
        "cond_gain": 5,
        "message": "installed smart power strips and LED bulbs out of their own pocket. Left a note: 'You're welcome.'",
    },

    # ── Special morale-auto events (larger deltas) ─────────────────────────────
    {
        "key": "word_of_mouth", "weight": 3, "type": "morale_auto",
        "name": "Word of Mouth", "icon": "⭐",
        "morale_delta": 15,
        "message": "told everyone they know how great the place is",
    },
    {
        "key": "turnaround", "weight": 3, "type": "morale_auto",
        "name": "The Turnaround", "icon": "🌟",
        "morale_delta": 25, "max_morale": 30,
        "message": "had something go really right in their life and their whole mood shifted",
    },

    # ── Funny morale-auto events ───────────────────────────────────────────────
    {
        "key": "squirrel_roof", "weight": 5, "type": "morale_auto",
        "name": "Squirrel on the Roof", "icon": "🐿️",
        "morale_delta": -4,
        "message": "heard something on the roof and sent you eleven voice memos about it",
    },
    {
        "key": "wrong_mail", "weight": 5, "type": "morale_auto",
        "name": "Wrong Mail Again", "icon": "📬",
        "morale_delta": 3,
        "message": "has been getting someone else's mail for six months and is now very invested in that person's life",
    },
    {
        "key": "spider_situation", "weight": 5, "type": "morale_auto",
        "name": "Spider Situation", "icon": "🕸️",
        "morale_delta": -6,
        "message": "encountered a very large spider. They have not fully recovered",
    },
    {
        "key": "great_rain_nap", "weight": 5, "type": "morale_auto",
        "name": "Great Rain Nap", "icon": "☔",
        "morale_delta": 8,
        "message": "did absolutely nothing all weekend because it rained and loved every second of it",
    },
    {
        "key": "perfect_couch", "weight": 5, "type": "morale_auto",
        "name": "Perfect Couch Position", "icon": "🛋️",
        "morale_delta": 6,
        "message": "rearranged the furniture and it is now somehow perfect. Texted you about it at 11pm",
    },
    {
        "key": "seasonal_allergies", "weight": 5, "type": "morale_auto",
        "name": "Seasonal Allergies", "icon": "🤧",
        "morale_delta": -5,
        "message": "is suffering through seasonal allergies. Not your fault, but they're miserable",
    },
    {
        "key": "bus_route_changed", "weight": 4, "type": "morale_auto",
        "name": "Bus Route Changed", "icon": "🚌",
        "morale_delta": -7,
        "message": "just found out the city changed their bus route. They are devastated",
    },
    {
        "key": "found_their_song", "weight": 5, "type": "morale_auto",
        "name": "Found Their Song", "icon": "🎶",
        "morale_delta": 7,
        "message": "discovered a song that perfectly describes their life right now and is absolutely thriving",
    },
    {
        "key": "overslept", "weight": 5, "type": "morale_auto",
        "name": "Overslept", "icon": "😴",
        "morale_delta": -4,
        "message": "overslept and missed something important. They're embarrassed and grumpy",
    },
    {
        "key": "double_rainbow", "weight": 3, "type": "morale_auto",
        "name": "Double Rainbow", "icon": "🌈",
        "morale_delta": 9,
        "message": "saw a double rainbow from the backyard and texted you about it immediately. They're inexplicably emotional",
    },
    {
        "key": "thinks_haunted", "weight": 4, "type": "morale_auto",
        "name": "Possibly Haunted", "icon": "👻",
        "morale_delta": -5,
        "message": "heard a noise and is now 40% convinced the property is haunted. Still not moving though",
    },
    {
        "key": "made_waffles", "weight": 5, "type": "morale_auto",
        "name": "Made Waffles", "icon": "🧇",
        "morale_delta": 7,
        "message": "made waffles from scratch for the first time and is very proud of themselves",
    },
    {
        "key": "phone_died", "weight": 5, "type": "morale_auto",
        "name": "Phone Died", "icon": "📵",
        "morale_delta": -5,
        "message": "had their phone die with no charger for an entire day",
    },
    {
        "key": "bad_burrito", "weight": 5, "type": "morale_auto",
        "name": "Bad Burrito", "icon": "😬",
        "morale_delta": -4,
        "message": "had a terrible experience at a new restaurant they were excited about. They're shaken",
    },
    {
        "key": "bird_window", "weight": 5, "type": "morale_auto",
        "name": "Bird at the Window", "icon": "🐦",
        "morale_delta": 5,
        "message": "has a bird that taps on the window every morning and believes it means something",
    },
    {
        "key": "ran_into_you", "weight": 5, "type": "morale_auto",
        "name": "Ran Into Landlord", "icon": "😶",
        "morale_delta": 3,
        "message": "ran into you at the grocery store. It was a little awkward but the place is still great",
    },
    {
        "key": "adopted_plant", "weight": 5, "type": "morale_auto",
        "name": "Adopted a Plant", "icon": "🪴",
        "morale_delta": 5,
        "message": "adopted a large plant named Gerald and is very happy about it",
    },
    {
        "key": "parking_incident", "weight": 5, "type": "morale_auto",
        "name": "Parking Incident", "icon": "🚗",
        "morale_delta": -6,
        "message": "had someone park in their spot again. They are furious",
    },
    {
        "key": "neighborhood_drama", "weight": 5, "type": "morale_auto",
        "name": "Neighborhood Drama", "icon": "🍿",
        "morale_delta": -4,
        "message": "is deeply invested in a neighborhood dispute that has nothing to do with them",
    },
    {
        "key": "bad_week", "weight": 5, "type": "morale_auto",
        "name": "Just One of Those Weeks", "icon": "😩",
        "morale_delta": -7,
        "message": "is just having one of those weeks. They didn't elaborate",
    },
    {
        "key": "great_new_neighbor", "weight": 5, "type": "morale_auto",
        "name": "Great New Neighbor", "icon": "🏡",
        "morale_delta": 6,
        "message": "says a really nice person just moved in next door",
    },
    {
        "key": "true_crime_phase", "weight": 5, "type": "morale_auto",
        "name": "True Crime Phase", "icon": "📺",
        "morale_delta": 4,
        "message": "is deep in a true crime podcast phase and keeps leaving suspiciously specific voicemails",
    },
    {
        "key": "good_taco", "weight": 5, "type": "morale_auto",
        "name": "Found a Great Taco Place", "icon": "🌮",
        "morale_delta": 8,
        "message": "texted you about a taco place. You didn't ask. Morale is up though",
    },
    {
        "key": "package_stolen", "weight": 5, "type": "morale_auto",
        "name": "Package Stolen", "icon": "😤",
        "morale_delta": -8,
        "message": "had a package stolen off the porch. They don't blame you. But they're upset",
    },
    {
        "key": "mosquito_season", "weight": 5, "type": "morale_auto",
        "name": "Mosquito Season", "icon": "🦟",
        "morale_delta": -5,
        "message": "is suffering through mosquito season. It's bad this year",
    },
    {
        "key": "cant_sleep", "weight": 5, "type": "morale_auto",
        "name": "Can't Sleep", "icon": "🌙",
        "morale_delta": -6,
        "message": "has been sleeping terribly. They did not elaborate",
    },
    {
        "key": "dog_sitting", "weight": 5, "type": "morale_auto",
        "name": "Dog Sitting", "icon": "🐕",
        "morale_delta": 7,
        "message": "is dog sitting for a friend this week and is extremely happy about it",
    },
    {
        "key": "great_pizza", "weight": 5, "type": "morale_auto",
        "name": "Found a Great Pizza Place", "icon": "🍕",
        "morale_delta": 6,
        "message": "texted you about a pizza place. You also didn't ask about this one",
    },
    {
        "key": "hoa_nonsense", "weight": 4, "type": "morale_auto",
        "name": "HOA Nonsense", "icon": "📋",
        "morale_delta": -7,
        "message": "received an HOA letter about something extremely minor. They are furious",
    },
    {
        "key": "perfect_weather", "weight": 5, "type": "morale_auto",
        "name": "Perfect Weather Week", "icon": "☀️",
        "morale_delta": 5,
        "message": "had a genuinely perfect weather week and is in a great mood",
    },
    {
        "key": "drafty_window_auto", "weight": 5, "type": "morale_auto",
        "name": "Drafty Window", "icon": "🥶",
        "morale_delta": -5,
        "message": "noticed a draft from a window they hadn't noticed before",
    },
    {
        "key": "mystery_package", "weight": 4, "type": "morale_auto",
        "name": "Mystery Package", "icon": "🎀",
        "morale_delta": 3,
        "message": "received a giant mysterious package and won't say what it is. Morale is up somehow",
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
    "level11":         {"desc": "Jumped you to Level 11. The crossroads. 🌙", "level": 11, "xp": XP_THRESHOLDS[11]},
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
# `dividend` = annual yield, paid quarterly (every season) on held shares.
STOCKS = {
    "AMZ":  {"name": "Amazoom",          "icon": "📦", "ticker": "AMZ",
              "desc": "We ship everything. Eventually.",
              "base_price": 142.00, "volatility": 0.022, "tier": "stock", "dividend": 0.02},
    "GOG":  {"name": "Goog-L",           "icon": "🔍", "ticker": "GOG",
              "desc": "Searching for new ways to monetize you.",
              "base_price": 95.00,  "volatility": 0.018, "tier": "stock", "dividend": 0.025},
    "FCP":  {"name": "Faceplant Inc.",   "icon": "📘", "ticker": "FCP",
              "desc": "Connecting the world, one data breach at a time.",
              "base_price": 26.00,  "volatility": 0.035, "tier": "stock", "dividend": 0.03},
    "MSS":  {"name": "MicroSoft-Serve", "icon": "💻", "ticker": "MSS",
              "desc": "Your OS now requires a monthly subscription.",
              "base_price": 68.00,  "volatility": 0.020, "tier": "stock", "dividend": 0.035},
    "APC":  {"name": "AppleCorp",        "icon": "🍎", "ticker": "APC",
              "desc": "Same phone. New port. $200 more.",
              "base_price": 185.00, "volatility": 0.024, "tier": "stock", "dividend": 0.02},
    "TLM":  {"name": "TesLame",          "icon": "🚗", "ticker": "TLM",
              "desc": "Electric cars. Unhinged tweets.",
              "base_price": 38.00,  "volatility": 0.055, "tier": "stock", "dividend": 0.0},
}
# Low-volatility, dividend-paying index funds — safe parking for idle cash.
INDEX_FUNDS = {
    "BRDX": {"name": "BroadMarket 500",  "icon": "🧺", "ticker": "BRDX",
              "desc": "The whole market in one ticker. Boring on purpose.",
              "base_price": 300.00, "volatility": 0.007, "tier": "index", "dividend": 0.04},
    "DVND": {"name": "DiviShield ETF",   "icon": "🛡️", "ticker": "DVND",
              "desc": "Stodgy blue-chips that just keep paying.",
              "base_price": 110.00, "volatility": 0.009, "tier": "index", "dividend": 0.055},
    "TECQ": {"name": "TechTen Index",    "icon": "💾", "ticker": "TECQ",
              "desc": "All the tech, none of the stock-picking. Swings a touch more.",
              "base_price": 220.00, "volatility": 0.013, "tier": "index", "dividend": 0.015},
    "BOND": {"name": "Treasury Bond Fund","icon": "🏛️", "ticker": "BOND",
              "desc": "Boring government IOUs. Sleeps like a baby.",
              "base_price": 100.00, "volatility": 0.004, "tier": "index", "dividend": 0.045},
    "REIT": {"name": "Landlord's REIT",  "icon": "🏘️", "ticker": "REIT",
              "desc": "Real estate, but someone else mows the lawn.",
              "base_price": 90.00,  "volatility": 0.010, "tier": "index", "dividend": 0.06},
    "GBLX": {"name": "Global Markets Index","icon": "🌐", "ticker": "GBLX",
              "desc": "The whole planet's economy in one ticker.",
              "base_price": 160.00, "volatility": 0.011, "tier": "index", "dividend": 0.035},
}
# Crypto — no dividends, weak mean reversion, gut-churning swings. Moon or dust.
CRYPTO = {
    "BTK":  {"name": "Bitcrown",         "icon": "🪙", "ticker": "BTK",
              "desc": "Digital gold, allegedly. Mostly vibes.",
              "base_price": 1200.00, "volatility": 0.085, "tier": "crypto", "dividend": 0.0},
    "SHBR": {"name": "ShibRocket",       "icon": "🚀", "ticker": "SHBR",
              "desc": "A meme coin with a dog mascot. What could go wrong?",
              "base_price": 0.45, "volatility": 0.14, "tier": "crypto", "dividend": 0.0},
    "AETH": {"name": "Aetherium",        "icon": "⛓️", "ticker": "AETH",
              "desc": "Smart contracts, dumb gas fees.",
              "base_price": 290.00, "volatility": 0.10, "tier": "crypto", "dividend": 0.0},
    "LTCN": {"name": "Litecorn",         "icon": "🌽", "ticker": "LTCN",
              "desc": "Like Bitcrown, but faster and lonelier.",
              "base_price": 85.00, "volatility": 0.11, "tier": "crypto", "dividend": 0.0},
    "DOGM": {"name": "DogeMoon",         "icon": "🌙", "ticker": "DOGM",
              "desc": "A joke that refuses to die. To the moon, allegedly.",
              "base_price": 0.12, "volatility": 0.16, "tier": "crypto", "dividend": 0.0},
    "SOLR": {"name": "Solaire",          "icon": "☀️", "ticker": "SOLR",
              "desc": "Blazing fast. Occasionally on fire.",
              "base_price": 42.00, "volatility": 0.13, "tier": "crypto", "dividend": 0.0},
}
ALL_INSTRUMENTS = {**STOCKS, **INDEX_FUNDS, **CRYPTO}

# Per-tier price dynamics: (mean-reversion strength, daily move cap).
TIER_DYNAMICS = {
    "stock":  {"reversion": 0.08, "cap": 0.18},
    "index":  {"reversion": 0.06, "cap": 0.05},   # hugs its base, barely moves
    "crypto": {"reversion": 0.015, "cap": 0.40},  # drifts & spikes wildly
}

# Market news — a headline can shock one instrument's price on a given advance.
STOCK_NEWS_CHANCE = 0.20   # per advance, at most one headline
STOCK_NEWS = [
    {"text": "📈 {name} ({ticker}) smashed earnings — shares surge!",      "min": 0.10, "max": 0.25, "good": True},
    {"text": "📈 Analysts upgrade {name} to 'strong buy'.",                "min": 0.06, "max": 0.15, "good": True},
    {"text": "📈 {name} unveils a blockbuster new product.",               "min": 0.08, "max": 0.20, "good": True},
    {"text": "📈 Buyout rumors send {name} soaring.",                      "min": 0.10, "max": 0.22, "good": True},
    {"text": "📈 {name} lands a massive government contract.",             "min": 0.07, "max": 0.18, "good": True},
    {"text": "📉 {name} ({ticker}) misses earnings — sell-off!",           "min": -0.22, "max": -0.10, "good": False},
    {"text": "📉 Data-breach scandal rocks {name}.",                       "min": -0.20, "max": -0.08, "good": False},
    {"text": "📉 Regulators open a probe into {name}.",                    "min": -0.18, "max": -0.08, "good": False},
    {"text": "📉 {name} guidance disappoints Wall Street.",                "min": -0.15, "max": -0.06, "good": False},
    {"text": "📉 A short-seller report torches {name}.",                   "min": -0.20, "max": -0.09, "good": False},
]

def _init_stock_state():
    return {
        "portfolio": {},
        "prices":    {t: i["base_price"] for t, i in ALL_INSTRUMENTS.items()},
        "history":   {t: [i["base_price"]] for t, i in ALL_INSTRUMENTS.items()},
    }

def _update_stock_prices(s, days):
    """Advance all prices by `days` using GBM + mean reversion, tuned per tier
    (stocks moderate, index funds barely move, crypto swings wildly)."""
    ss       = s.setdefault("stocks", _init_stock_state())
    prices   = ss.setdefault("prices",  {t: i["base_price"] for t, i in ALL_INSTRUMENTS.items()})
    histories = ss.setdefault("history", {t: [i["base_price"]] for t, i in ALL_INSTRUMENTS.items()})
    for ticker, info in ALL_INSTRUMENTS.items():
        base  = info["base_price"]
        vol   = info["volatility"]
        dyn   = TIER_DYNAMICS.get(info.get("tier", "stock"), TIER_DYNAMICS["stock"])
        rev, cap = dyn["reversion"], dyn["cap"]
        price = prices.get(ticker, base)
        hist  = list(histories.get(ticker, [base]))
        for _ in range(days):
            reversion = (base - price) / base * rev
            chg       = random.gauss(reversion, vol)
            chg       = max(-cap, min(cap, chg))
            price     = max(price * (1 + chg), base * 0.05)  # floor at 5% of base
        price = round(price, 4 if price < 1 else 2)
        prices[ticker] = price
        hist.append(price)
        histories[ticker] = hist[-50:]
    ss["prices"]  = prices
    ss["history"] = histories

def _maybe_stock_news(s):
    """At most one market-news headline per advance; shocks one instrument's price.
    Returns an event dict (or None)."""
    if random.random() >= STOCK_NEWS_CHANCE:
        return None
    ss     = s.setdefault("stocks", _init_stock_state())
    ticker = random.choice(list(ALL_INSTRUMENTS.keys()))
    info   = ALL_INSTRUMENTS[ticker]
    news   = random.choice(STOCK_NEWS)
    mag    = random.uniform(news["min"], news["max"])
    if info.get("tier") == "crypto":
        mag *= 1.5   # crypto headlines hit harder
    price     = ss["prices"].get(ticker, info["base_price"])
    new_price = max(info["base_price"] * 0.05, price * (1 + mag))
    new_price = round(new_price, 4 if new_price < 1 else 2)
    ss["prices"][ticker] = new_price
    hist = ss["history"].get(ticker, [info["base_price"]])
    hist.append(new_price)
    ss["history"][ticker] = hist[-50:]
    return {"prop": "Market News",
            "text": news["text"].format(name=info["name"], ticker=ticker) + f" ({mag*100:+.0f}%)",
            "type": "positive" if news["good"] else "negative"}

def _pay_dividends(s, current_day):
    """Quarterly (every 28 days) dividend on held shares. Returns event dict or None."""
    ss   = s.setdefault("stocks", _init_stock_state())
    last = ss.setdefault("last_dividend_day", current_day)
    if current_day - last < 28:
        return None
    ss["last_dividend_day"] = current_day
    total = 0.0
    for ticker, held in ss.get("portfolio", {}).items():
        info = ALL_INSTRUMENTS.get(ticker)
        shares = held.get("shares", 0)
        if not info or shares <= 0 or info.get("dividend", 0) <= 0:
            continue
        price = ss["prices"].get(ticker, info["base_price"])
        total += shares * price * info["dividend"] / 4   # quarterly slice of annual yield
    total = round(total, 2)
    if total <= 0:
        return None
    s["cash"] += total
    return {"prop": "Dividends", "text": f"Quarterly dividends paid out: +${total:,.2f}", "type": "positive"}

# Player homes — all base stats are 4 max_energy / 1 recharge. All energy/recharge gains come from furniture items.
PLAYER_HOMES = [
    {"key": "grandmas_basement", "name": "Grandma's Basement", "icon": "🛋️", "cost":         0, "max_energy": 4, "recharge": 1, "unlock_level":  0, "desc": "Grandma's got a cot, a leaky fridge, and opinions about your life choices. Free rent — if you can survive the casserole."},
    {"key": "small_apt",         "name": "Small Apartment",    "icon": "🏠",  "cost":    80_000, "max_energy": 4, "recharge": 1, "unlock_level":  2, "desc": "Thin walls, no dishwasher, and a neighbor who practices drums at midnight. Still yours."},
    {"key": "condo",             "name": "Condo",              "icon": "🏢",  "cost":   150_000, "max_energy": 4, "recharge": 1, "unlock_level":  4, "desc": "An HOA fee and a parking sticker — welcome to adulthood."},
    {"key": "small_home",        "name": "Small Home",         "icon": "🏡",  "cost":   250_000, "max_energy": 4, "recharge": 1, "unlock_level":  7, "desc": "A real yard. A real mortgage. A real lawn to mow at 7am on a Saturday."},
    {"key": "suburban_home",     "name": "Suburban Home",      "icon": "🏘️",  "cost":   400_000, "max_energy": 4, "recharge": 1, "unlock_level":  9, "desc": "Cul-de-sac living with a two-car garage and a wave-hello relationship with the neighbors."},
    {"key": "luxury_villa",      "name": "Luxury Villa",       "icon": "🏛️",  "cost":   750_000, "max_energy": 4, "recharge": 1, "unlock_level": 11, "desc": "Heated floors, a wine cellar, and someone else mows the lawn."},
    {"key": "mansion",           "name": "Mansion",            "icon": "🏰",  "cost": 1_500_000, "max_energy": 4, "recharge": 1, "unlock_level": 13, "desc": "You have a butler named Gerald and a room you've never entered. Peak existence."},
]

STORE_ITEMS = {
    "coffee_maker":   {"name": "Coffee Maker",             "icon": "☕",  "cost":   499, "unlock_level": 1, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "A decent drip machine. +2 max energy."},
    "desk_fan":       {"name": "Desk Fan",                  "icon": "🌀",  "cost":   199, "unlock_level": 1, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Not air conditioning. Close enough. +2 max energy."},
    "house_plant":    {"name": "House Plant",               "icon": "🪴",  "cost":    89, "unlock_level": 2, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Studies show it helps. You're not asking questions. 15% chance to block 1 morale loss/day."},
    "blackout_curtains": {"name": "Blackout Curtains",      "icon": "🪟",  "cost":   149, "unlock_level": 2, "max_energy_bonus": 0, "recharge_bonus": 1, "desc": "Sleep deeper. Wake up less angry. +1 recharge/day."},
    "new_bed":        {"name": "New Bed",                   "icon": "🛏️", "cost": 4_999, "unlock_level": 3, "max_energy_bonus": 0, "recharge_bonus": 1, "desc": "Memory foam. You wake up ready. +1 recharge/day."},
    "mini_fridge":    {"name": "Mini Fridge",               "icon": "🧊",  "cost":   349, "unlock_level": 3, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Snacks within arm's reach. Peak efficiency. +2 max energy."},
    "whiteboard":     {"name": "Whiteboard",                "icon": "📋",  "cost":   249, "unlock_level": 4, "unlock_home": "small_apt", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You mapped out the whole job. Bob charges less. 6% off all contractor renovation costs."},
    "filing_cabinet": {"name": "Filing Cabinet",            "icon": "🗂️", "cost":   449, "unlock_level": 5, "unlock_home": "small_apt", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Everything is documented. Problems get caught early. 15% lower repair event chance."},
    "headphones":     {"name": "Noise-Cancelling Headphones","icon": "🎧", "cost":   699, "unlock_level": 6, "unlock_home": "small_apt", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You stop engaging. They interpret it as professionalism. -1 morale decay/day across all properties."},
    "negotiation_book":{"name": "Negotiation Book",         "icon": "📖",  "cost":   999, "unlock_level": 7, "unlock_home": "small_apt", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You read it twice. Vendors can tell. +4% on all property sale prices."},
    # ── New home furnishings ──────────────────────────────────────────────────
    "couch":           {"name": "Couch",                    "icon": "🛋️", "cost":   600, "unlock_level": 1, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Somewhere to actually sit. +2 max energy."},
    "flat_screen_tv":  {"name": "Flat Screen TV",           "icon": "📺",  "cost": 1_200, "unlock_level": 1, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Something to unwind to. +2 max energy."},
    "espresso_machine":{"name": "Espresso Machine",         "icon": "☕",  "cost":   899, "unlock_level": 3, "max_energy_bonus": 2, "recharge_bonus": 1, "desc": "Real caffeine. Finally. +2 max energy, +1 recharge."},
    "wine_rack":       {"name": "Wine Rack",                "icon": "🍷",  "cost": 1_500, "unlock_level": 5, "unlock_home": "condo", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "The landlord aesthetic. +$100/day passive income."},
    "gaming_setup":    {"name": "Gaming Setup",             "icon": "🎮",  "cost": 2_500, "unlock_level": 5, "max_energy_bonus": 3, "recharge_bonus": 0, "desc": "For decompressing. Professionally. +3 max energy."},
    "workbench_tools": {"name": "Workbench & Tools",        "icon": "🔧",  "cost":   800, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You've got the tools. Bob is a little threatened. 8% off contractor labor."},
    "bbq_grill":       {"name": "BBQ Grill",                "icon": "🍖",  "cost":   600, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Grilling on your own property hits different. No gameplay effect — just good vibes."},
    "patio_set":       {"name": "Patio Furniture",          "icon": "🪑",  "cost": 1_200, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Morning coffee outside. Cosmetic upgrade."},
    "hot_tub":         {"name": "Hot Tub",                  "icon": "🛁",  "cost": 8_000, "unlock_level": 7, "max_energy_bonus": 0, "recharge_bonus": 3, "desc": "Hydrotherapy. Tax deductible? Maybe. +3 recharge/day."},
    "home_gym":        {"name": "Home Gym",                 "icon": "🏋️", "cost": 5_000, "unlock_level": 7, "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "No more excuses. No gym commute. +4 max energy."},
    "swimming_pool":   {"name": "Swimming Pool",            "icon": "🏊",  "cost":25_000, "unlock_level": 9, "max_energy_bonus": 0, "recharge_bonus": 5, "desc": "Proving a point at this stage. +5 recharge/day."},
    "home_theater":    {"name": "Home Theater",             "icon": "🎬",  "cost": 8_000, "unlock_level": 9, "max_energy_bonus": 5, "recharge_bonus": 0, "desc": "The screen. The surround sound. The popcorn machine. +5 max energy."},
    # ── Living room furnishings ───────────────────────────────────────────────
    "bookshelf":       {"name": "Bookshelf",                "icon": "📚",  "cost":   350, "unlock_level": 1, "unlock_home": "condo", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Tax strategy, biographies, one novel you never finished. +5% property sale price."},
    "aquarium":        {"name": "Aquarium",                 "icon": "🐠",  "cost":   650, "unlock_level": 2, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Fish don't care about your problems. 20% chance to block 1 morale loss/day."},
    "fireplace":       {"name": "Fireplace",                "icon": "🪵",  "cost": 2_000, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 2, "desc": "Mood. Warmth. Crackling sounds. +2 recharge/day."},
    "pool_table":      {"name": "Pool Table",               "icon": "🎱",  "cost": 3_500, "unlock_level": 7, "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "You hustle your contractors. They respect it. +4 max energy."},
    "grand_piano":     {"name": "Grand Piano",              "icon": "🎹",  "cost":12_000, "unlock_level":11, "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "You don't play. Gerald does. +4 max energy."},
    # ── Bedroom ───────────────────────────────────────────────────────────────
    "meditation_corner":{"name": "Meditation Corner",       "icon": "🧘",  "cost":   900, "unlock_level": 3, "max_energy_bonus": 0, "recharge_bonus": 2, "desc": "Five minutes of silence. Life-changing. +2 recharge/day."},
    "sauna":           {"name": "Sauna",                    "icon": "🧖",  "cost": 6_000, "unlock_level": 9, "max_energy_bonus": 0, "recharge_bonus": 5, "desc": "You sweat out bad decisions daily. +5 recharge/day."},
    # ── Kitchen ──────────────────────────────────────────────────────────────
    "instant_pot":     {"name": "Instant Pot",              "icon": "🥘",  "cost":   150, "unlock_level": 1, "max_energy_bonus": 1, "recharge_bonus": 0, "desc": "Set it, forget it, eat well. +1 max energy."},
    "kitchen_island":  {"name": "Kitchen Island",           "icon": "🍳",  "cost": 2_200, "unlock_level": 5, "max_energy_bonus": 3, "recharge_bonus": 0, "desc": "More counter space. More life. +3 max energy."},
    "smart_fridge":    {"name": "Smart Fridge",             "icon": "🗄️", "cost": 1_800, "unlock_level": 7, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "It texts you when you're low on eggs. Cosmetic upgrade."},
    # ── Home office ──────────────────────────────────────────────────────────
    "ergonomic_chair": {"name": "Ergonomic Chair",          "icon": "💺",  "cost":   600, "unlock_level": 4, "unlock_home": "small_apt", "max_energy_bonus": 0, "recharge_bonus": 2, "desc": "Your back stops screaming. Your productivity speaks. +2 recharge/day."},
    "second_monitor":  {"name": "Second Monitor",           "icon": "🖥️", "cost":   400, "unlock_level": 5, "unlock_home": "condo", "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Left screen: spreadsheets. Right screen: also spreadsheets. +2 max energy."},
    "printer":         {"name": "Laser Printer",            "icon": "🖨️", "cost":   250, "unlock_level": 3, "unlock_home": "condo", "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Print the listing yourself. Save on fees. 5% off all property purchase prices."},
    # ── Garage ───────────────────────────────────────────────────────────────
    "motorcycle":      {"name": "Motorcycle",               "icon": "🏍️", "cost": 8_000, "unlock_level": 7, "unlock_home": "suburban_home", "max_energy_bonus": 0, "recharge_bonus": 3, "desc": "Wind in your face on the way to collect rent. +3 recharge/day."},
    "sports_car":      {"name": "Sports Car",               "icon": "🚗",  "cost":45_000, "unlock_level": 9, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Landlord tax write-off, obviously. +$200/day passive income."},
    # ── Outdoor ──────────────────────────────────────────────────────────────
    "garden":          {"name": "Garden",                   "icon": "🌻",  "cost":   500, "unlock_level": 3, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Something living that actually needs you. 20% chance to block 1 morale loss/day."},
    "fire_pit":        {"name": "Fire Pit",                 "icon": "🔥",  "cost":   700, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 2, "desc": "Evening decompression. You've earned it. +2 recharge/day."},
    "basketball_hoop": {"name": "Basketball Hoop",          "icon": "🏀",  "cost":   400, "unlock_level": 4, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Shoot your frustration into a net. Cosmetic upgrade."},
    # ── New high-tier items ───────────────────────────────────────────────────
    "smart_home_system": {"name": "Smart Home System",  "icon": "🏠", "cost": 12_000, "unlock_level": 9,  "unlock_home": "luxury_villa", "max_energy_bonus": 5, "recharge_bonus": 0, "desc": "Whole-home automation that optimizes your routines. +5 max energy."},
    "home_bar":          {"name": "Home Bar",           "icon": "🍸", "cost":  8_000, "unlock_level": 12, "unlock_home": "mansion", "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "Top-shelf everything. No excuses needed. +4 max energy."},
    "art_gallery":       {"name": "Art Gallery",        "icon": "🖼️", "cost": 15_000, "unlock_level": 12, "unlock_home": "mansion", "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "Three rooms of originals. One is a forgery. +4 max energy."},
    "professional_gym":  {"name": "Professional Gym",  "icon": "💪", "cost": 20_000, "unlock_level": 12, "unlock_home": "mansion", "max_energy_bonus": 4, "recharge_bonus": 0, "desc": "Olympic weights. No waiting for machines. +4 max energy."},
    "spa_suite":         {"name": "Spa Suite",          "icon": "💆", "cost": 25_000, "unlock_level": 13, "unlock_home": "mansion", "max_energy_bonus": 0, "recharge_bonus": 6, "desc": "Hot stone massages at 6am on a Tuesday. +6 recharge/day."},
    "luxury_sleep_system": {"name": "Luxury Sleep System","icon": "🛌","cost": 10_000, "unlock_level": 12, "unlock_home": "mansion", "max_energy_bonus": 0, "recharge_bonus": 4, "desc": "Temperature-regulated, zero-gravity mattress. +4 recharge/day."},
    "indoor_pool":       {"name": "Indoor Pool",        "icon": "🌊", "cost": 40_000, "unlock_level": 13, "unlock_home": "mansion", "max_energy_bonus": 0, "recharge_bonus": 6, "desc": "Climate-controlled. Gerald maintains it. +6 recharge/day."},
    "grand_fireplace":   {"name": "Grand Fireplace",    "icon": "🕯️", "cost":  5_000, "unlock_level": 12, "unlock_home": "mansion", "max_energy_bonus": 0, "recharge_bonus": 3, "desc": "Floor-to-ceiling stone. You read by firelight. +3 recharge/day."},
    "music_studio":      {"name": "Music Studio",       "icon": "🎸", "cost": 18_000, "unlock_level": 13, "unlock_home": "mansion", "max_energy_bonus": 0, "recharge_bonus": 3, "desc": "Soundproofed. Pro-grade gear. You play once a month. +3 recharge/day."},
}

# ── Vending Machine Business (Phase 1 overhaul) ─────────────────────────────────
# Locations have demand PROFILES (what each spot wants); machines have SLOTS you
# assign product categories to and keep stocked. Daily income = demand matching,
# split per category across slots, capped by stock, with perishable spoilage.
# (Reputation, dynamic pricing, competition, seasons come in later phases.)
VM_PRICES        = [1_200, 2_000, 3_000, 4_200, 5_800, 8_000]   # machine #1–6 purchase price
VM_SLOTS         = 6                                            # slots per machine
VM_SLOT_CAPACITY = 60                                           # base units a filled slot holds (90 with Bigger Capacity)
VINNY_FEE        = 150                                          # per machine, per day Vinny restocks

# Phase 2 — dynamic pricing: per-machine price level → (price multiplier, demand multiplier).
VM_PRICE_LEVELS = {
    "value":   {"name": "Value",   "icon": "🏷️", "price_mult": 0.85, "demand_mult": 1.20},
    "normal":  {"name": "Normal",  "icon": "⚖️", "price_mult": 1.00, "demand_mult": 1.00},
    "premium": {"name": "Premium", "icon": "💎", "price_mult": 1.30, "demand_mult": 0.72},
}

# Phase 2 — per-machine upgrades (one-time purchase, stored in vm["upgrades"]).
VM_UPGRADES = {
    "capacity":    {"name": "Bigger Capacity",  "icon": "📦", "cost": 1_500, "desc": "Slot capacity 60 → 90. Slots last far longer between restocks."},
    "fridge":      {"name": "Refrigeration",    "icon": "❄️", "cost": 2_000, "desc": "Perishables last +2 days before spoiling (Fresh 3→5, Hot 6→8)."},
    "card_reader": {"name": "Card Reader",      "icon": "💳", "cost": 1_200, "desc": "+12% units sold — more customers can pay."},
    "branding":    {"name": "Branding Wrap",    "icon": "🎨", "cost": 1_000, "desc": "A sharp look. Reputation climbs faster."},
    "reinforced":  {"name": "Reinforced Build", "icon": "🛡️", "cost": 1_800, "desc": "Halves the odds of bad location events (vandalism, outages)."},
}

# Phase 2 — Grandma the buyer: weekly auto-purchase of product at a convenience markup.
GRANDMA_MARKUP    = 0.18   # she pays 18% over CostPro case price
GRANDMA_INTERVAL  = 7      # shops every 7 days
GRANDMA_BUFFER    = 1.5    # buys ~1.5× the coming week's demand

# Product categories. price = sale price per unit (pure income — wholesale was
# already paid at CostPro). Perishables spoil `shelf` days after a restock.
VM_PRODUCTS = {
    "snacks":    {"name": "Snacks",      "icon": "🍫",  "price": 2.25, "perishable": False, "shelf": None},
    "cold":      {"name": "Cold Drinks", "icon": "🥤",  "price": 2.75, "perishable": False, "shelf": None},
    "hot":       {"name": "Hot Drinks",  "icon": "☕",  "price": 3.00, "perishable": True,  "shelf": 6},
    "energy":    {"name": "Energy",      "icon": "⚡",  "price": 3.75, "perishable": False, "shelf": None},
    "fresh":     {"name": "Fresh Food",  "icon": "🥗",  "price": 6.50, "perishable": True,  "shelf": 3},
    "specialty": {"name": "Specialty",   "icon": "🎁",  "price": 4.75, "perishable": False, "shelf": None},
}

# Machine slot N (1-based purchase order) → location.
VM_LOCATION_ORDER = ["midtown_grocery", "downtown_bus", "westwood_office",
                     "northside_center", "newbay_ferry", "riverside_park"]
VM_LOCATIONS = {
    "midtown_grocery":  {"name": "Midtown Grocery Entrance",  "traffic": 200, "volatility": 0.10,
                         "profile": {"snacks": .25, "cold": .25, "fresh": .20, "specialty": .15, "energy": .10, "hot": .05}},
    "downtown_bus":     {"name": "Downtown Bus Station",       "traffic": 180, "volatility": 0.20,
                         "profile": {"snacks": .35, "cold": .30, "energy": .20, "hot": .10, "specialty": .05}},
    "westwood_office":  {"name": "Westwood Office Lobby",      "traffic": 160, "volatility": 0.15,
                         "profile": {"hot": .30, "energy": .25, "cold": .20, "snacks": .15, "specialty": .10}},
    "northside_center": {"name": "Northside Community Center", "traffic": 140, "volatility": 0.20,
                         "profile": {"energy": .30, "snacks": .30, "cold": .20, "hot": .10, "specialty": .10}},
    "newbay_ferry":     {"name": "Newbay Ferry Terminal",      "traffic": 130, "volatility": 0.35,
                         "profile": {"cold": .30, "snacks": .25, "specialty": .20, "fresh": .15, "hot": .10}},
    "riverside_park":   {"name": "Riverside Park",             "traffic": 120, "volatility": 0.30,
                         "profile": {"cold": .40, "snacks": .30, "energy": .15, "fresh": .10, "specialty": .05}},
    # Special: comes ONLY from the laundromat's In-House Vending add-on (not in
    # VM_LOCATION_ORDER, so it's never sold at the regular 6 market spots).
    "laundromat":       {"name": "Your Laundromat",            "traffic": 110, "volatility": 0.20,
                         "profile": {"snacks": .35, "cold": .30, "energy": .15, "hot": .10, "specialty": .10}},
    # Special: appears in the Back-Room Arcade (not in VM_LOCATION_ORDER). Gamers
    # run on energy drinks, soda & snacks.
    "arcade":           {"name": "The Arcade Floor",           "traffic": 115, "volatility": 0.25,
                         "profile": {"energy": .35, "cold": .25, "snacks": .25, "specialty": .10, "hot": .05}},
}

# Vending events are now CHOICE CARDS — the player decides how to handle each.
# At most one fires per advance, at a low chance (see VM_EVENT_CHANCE), so the
# player isn't buried in pop-ups across all their income sources.
# Choice effect keys: cost (cash out), cash (cash in), rep (machine reputation
# delta), spoil_pct (fraction of perishable stock dumped). Optional "risk":
# {chance, cost, rep, result_bad} — a gamble resolved server-side.
# "problem": True events are halved by the Reinforced Build upgrade.
VM_EVENT_CHANCE = 0.10   # per advance (one event max, on a random machine)

VM_EVENTS = [
    {"key": "vandalism", "title": "Vandalized Overnight", "icon": "🧱", "problem": True,
     "text": "Machine #{slot} at {loc} was tagged and pried at overnight.", "choices": [
        {"label": "Repair it properly", "cost": 180, "rep": 4, "result": "Good as new — and clearly cared-for."},
        {"label": "Cheap patch job", "cost": 50, "rep": -2, "result": "Functional, but it looks rough.",
         "risk": {"chance": 0.30, "cost": 150, "rep": -4, "result_bad": "The patch failed and they hit it again — extra repair."}},
        {"label": "Leave it for now", "cost": 0, "rep": -10, "result": "A battered machine. Customers notice."}]},
    {"key": "health_inspection", "title": "Surprise Inspection", "icon": "📋", "problem": True,
     "text": "A health inspector flagged Machine #{slot} at {loc}.", "choices": [
        {"label": "Pay the fine", "cost": 150, "rep": 0, "result": "Paid and done."},
        {"label": "Bring it up to code", "cost": 260, "rep": 5, "result": "Spotless and compliant — a reputation bump."},
        {"label": "Contest the citation", "cost": 0, "rep": 0, "result": "Dismissed — your paperwork held up.",
         "risk": {"chance": 0.45, "cost": 320, "rep": -3, "result_bad": "The city won — a steeper fine plus a reputation ding."}}]},
    {"key": "power_outage", "title": "Power Outage", "icon": "🔌", "problem": True,
     "text": "A power outage hit {loc} — Machine #{slot}'s fridge is warming up fast.", "choices": [
        {"label": "Rush a generator over", "cost": 120, "rep": 1, "result": "Power restored — the stock is saved."},
        {"label": "Let it ride", "cost": 0, "rep": -2, "spoil_pct": 0.6, "result": "Most of the perishables warmed past safe and had to be tossed."}]},
    {"key": "coin_theft", "title": "Coin Box Cracked", "icon": "🪙", "problem": True,
     "text": "Someone jimmied the coin box on Machine #{slot} at {loc}.", "choices": [
        {"label": "Upgrade to card-only", "cost": 200, "rep": 3, "result": "No more cash box to steal. Modern and tidy."},
        {"label": "Just repair the mech", "cost": 60, "rep": 0, "result": "Fixed — for now.",
         "risk": {"chance": 0.35, "cost": 60, "rep": -3, "result_bad": "They came back for the coins again."}},
        {"label": "Ignore it", "cost": 0, "rep": -6, "result": "Word gets around that it's an easy target."}]},
    {"key": "permit", "title": "Permit Renewal", "icon": "🏛️", "problem": True,
     "text": "The city says Machine #{slot} at {loc} needs its permit renewed.", "choices": [
        {"label": "Renew the permit", "cost": 130, "rep": 0, "result": "Squared away with the city."},
        {"label": "Operate without it", "cost": 0, "rep": 0, "result": "Nobody noticed... this time.",
         "risk": {"chance": 0.50, "cost": 400, "rep": -4, "result_bad": "Caught operating unpermitted — a hefty fine."}}]},
    {"key": "graffiti", "title": "Graffiti'd", "icon": "🎨", "problem": True,
     "text": "Someone tagged Machine #{slot} at {loc} with spray paint.", "choices": [
        {"label": "Pro cleaning", "cost": 90, "rep": 3, "result": "Looks brand new again."},
        {"label": "Scrub it yourself", "cost": 0, "rep": 1, "result": "Elbow grease and a weekend. Mostly gone."},
        {"label": "Leave it", "cost": 0, "rep": -5, "result": "The tag stays. So does the impression."}]},
    {"key": "jammed", "title": "Jammed Up", "icon": "🛠️", "problem": True,
     "text": "Machine #{slot} at {loc} is jammed and refusing dollars.", "choices": [
        {"label": "Call an emergency tech", "cost": 140, "rep": 2, "result": "Back in service within the hour."},
        {"label": "Try to unjam it yourself", "cost": 0, "rep": 0, "result": "A few whacks and it's working again.",
         "risk": {"chance": 0.30, "cost": 160, "rep": -5, "result_bad": "You made it worse — a real repair was needed."}},
        {"label": "Leave it shut down", "cost": 0, "rep": -8, "result": "Days of lost sales and an unhappy spot."}]},
    {"key": "captive_crowd", "title": "Captive Crowd!", "icon": "🌟", "problem": False,
     "text": "A delay has trapped a big crowd right by Machine #{slot} at {loc}. They're thirsty and impatient.", "choices": [
        {"label": "Crank prices — cash in", "cost": 0, "cash": 600, "rep": -6, "result": "You gouge the captive crowd. The register sings; the goodwill doesn't."},
        {"label": "Fair prices, move volume", "cost": 0, "cash": 280, "rep": 4, "result": "Steady fair sales — and grateful regulars."},
        {"label": "Do nothing special", "cost": 0, "cash": 120, "rep": 0, "result": "A modest bump from the crowd."}]},
    {"key": "co_promo", "title": "Co-Promotion Offer", "icon": "🤝", "problem": False,
     "text": "A local shop near Machine #{slot} ({loc}) offers to cross-promote your machine.", "choices": [
        {"label": "Split signage costs", "cost": 40, "rep": 8, "result": "Their customers become your customers. Great look."},
        {"label": "Politely decline", "cost": 0, "rep": 0, "result": "You pass. No harm done."}]},
    {"key": "influencer", "title": "Influencer Wants In", "icon": "📸", "problem": False,
     "text": "A local influencer wants to feature Machine #{slot} at {loc} — for some free product.", "choices": [
        {"label": "Comp them a haul", "cost": 0, "rep": 10, "spoil_pct": 0.15, "result": "The post blows up — your machine's the talk of the block."},
        {"label": "Offer a small sample", "cost": 0, "rep": 4, "result": "A modest shoutout. Every bit helps."},
        {"label": "Decline", "cost": 0, "rep": 0, "result": "Not interested in freebies-for-clout."}]},
]

def _vm_blank_slots():
    return [{"category": None, "stock": 0.0, "restock_day": 0} for _ in range(VM_SLOTS)]

def _vm_capacity(vm):
    """Per-slot capacity, raised by the Bigger Capacity upgrade."""
    return 90 if vm.get("upgrades", {}).get("capacity") else VM_SLOT_CAPACITY

def _vm_rep_mult(vm):
    """Reputation → demand multiplier (rep 0 → 0.7×, 70 → 1.05×, 100 → 1.2×)."""
    return 0.7 + (vm.get("reputation", 70) / 100) * 0.5

def _vm_restock_from_inventory(vm, inv, current_day):
    """Top every configured slot up to capacity from CostPro inventory.
    Returns total units moved (0 if nothing happened)."""
    cap   = _vm_capacity(vm)
    moved = 0.0
    for sl in vm.get("slots", []):
        cat = sl.get("category")
        if not cat:
            continue
        need = cap - sl.get("stock", 0)
        if need <= 0.5:
            continue
        avail = inv.get(cat, 0)
        take  = min(need, avail)
        if take > 0:
            sl["stock"] = sl.get("stock", 0) + take
            inv[cat]    = avail - take
            sl["restock_day"] = current_day
            moved += take
    return moved

def _vm_sell_day(vm, loc, current_day):
    """Run one day of sales for a machine. Mutates slot stock.
    Applies reputation, dynamic pricing, and upgrades.
    Returns (gross_profit, spoiled_units, stockout_count)."""
    ups          = vm.get("upgrades", {})
    shelf_bonus  = 2 if ups.get("fridge") else 0
    card_mult    = 1.12 if ups.get("card_reader") else 1.0
    plevel       = VM_PRICE_LEVELS.get(vm.get("price_level", "normal"), VM_PRICE_LEVELS["normal"])
    price_mult   = plevel["price_mult"]
    demand_mult  = plevel["demand_mult"] * card_mult * _vm_rep_mult(vm)

    # Spoilage first: perishables past (shelf + fridge bonus) are written off.
    spoiled = 0.0
    for sl in vm.get("slots", []):
        cat = sl.get("category")
        if not cat or sl.get("stock", 0) <= 0:
            continue
        prod = VM_PRODUCTS[cat]
        if prod["perishable"] and current_day - sl.get("restock_day", current_day) > prod["shelf"] + shelf_bonus:
            spoiled += sl["stock"]
            sl["stock"] = 0.0
    # Group ALL configured slots by category (incl. empty ones, so a drained slot
    # registers as a stockout). Category demand flows to the slots that have stock.
    configured = {}
    for sl in vm.get("slots", []):
        if sl.get("category"):
            configured.setdefault(sl["category"], []).append(sl)
    traffic = loc["traffic"] * (1 + random.uniform(-loc["volatility"], loc["volatility"])) * demand_mult
    profit, stockouts = 0.0, 0
    for cat, slot_list in configured.items():
        cat_demand = traffic * loc["profile"].get(cat, 0)
        if cat_demand <= 0:
            continue   # no demand for this here — dead weight, but not a "stockout"
        stocked = [sl for sl in slot_list if sl.get("stock", 0) > 0]
        if not stocked:
            stockouts += 1   # customers wanted it, the slot was empty
            continue
        per_slot = cat_demand / len(stocked)
        price    = VM_PRODUCTS[cat]["price"] * price_mult
        sold_cat = 0.0
        for sl in stocked:
            sold = min(per_slot, sl["stock"])
            profit      += sold * price
            sl["stock"] -= sold
            sold_cat    += sold
        if cat_demand - sold_cat > 0.5:   # couldn't fully meet demand
            stockouts += 1
    return profit, spoiled, stockouts

def _vm_update_reputation(vm, spoiled, stockouts):
    """Daily reputation drift from service quality + pricing + branding."""
    configured = [sl for sl in vm.get("slots", []) if sl.get("category")]
    if not configured:
        return   # idle machine — reputation holds
    delta = 0
    delta -= min(stockouts, 3)
    if spoiled >= 1:
        delta -= 2
    if stockouts == 0 and spoiled < 1:
        delta += 2
    plevel = vm.get("price_level", "normal")
    if plevel == "premium":
        delta -= 1
    elif plevel == "value":
        delta += 1
    if vm.get("upgrades", {}).get("branding"):
        delta += 1
    delta = max(-5, min(4, delta))
    vm["reputation"] = max(0, min(100, vm.get("reputation", 70) + delta))

def _vm_queue_event(vm, loc):
    """Build a pending vending-event choice card for the frontend (labels + costs only)."""
    ev = random.choice(VM_EVENTS)
    if ev.get("problem") and vm.get("upgrades", {}).get("reinforced") and random.random() < 0.5:
        return None   # Reinforced Build shrugged it off
    return {
        "machine_id":   vm["id"],
        "machine_slot": vm["slot"],
        "key":          ev["key"],
        "title":        ev["title"],
        "icon":         ev["icon"],
        "text":         ev["text"].format(slot=vm["slot"], loc=loc["name"]),
        "choices":      [{"label": c["label"], "cost": c.get("cost", 0), "gain": c.get("cash", 0)}
                         for c in ev["choices"]],
    }

def _vm_apply_event_choice(s, vm, choice):
    """Apply a vending event choice (cash/reputation/spoilage, with optional risk).
    Returns (result_text, was_bad_outcome)."""
    result, bad = choice.get("result", "Done."), False
    extra_cost = extra_rep = 0
    risk = choice.get("risk")
    if risk and random.random() < risk.get("chance", 0):
        bad        = True
        extra_cost = risk.get("cost", 0)
        extra_rep  = risk.get("rep", 0)
        result     = risk.get("result_bad", result)
    cost = choice.get("cost", 0) + extra_cost
    if cost:
        s["cash"] = max(0, s["cash"] - cost)
    if choice.get("cash"):
        s["cash"] += choice["cash"]
    rep_delta = choice.get("rep", 0) + extra_rep
    if rep_delta:
        vm["reputation"] = max(0, min(100, vm.get("reputation", 70) + rep_delta))
    spoil = choice.get("spoil_pct", 0)
    if spoil:
        for sl in vm.get("slots", []):
            cat = sl.get("category")
            if cat and VM_PRODUCTS.get(cat, {}).get("perishable") and sl.get("stock", 0) > 0:
                sl["stock"] = round(sl["stock"] * (1 - spoil), 1)
    return result, bad

def _grandma_shop(s, current_day, events):
    """Grandma's weekly run: buys cases (at a markup) to cover the coming week's
    demand for whatever categories your slots are configured to use."""
    vms = s.get("vending_machines", [])
    inv = s.setdefault("costpro_inventory", {})
    # Weekly demand per category across all machines that stock it.
    weekly = {}
    for vm in vms:
        loc = VM_LOCATIONS.get(vm.get("location_key"))
        if not loc:
            continue
        cats = {sl["category"] for sl in vm.get("slots", []) if sl.get("category")}
        for cat in cats:
            weekly[cat] = weekly.get(cat, 0) + loc["traffic"] * loc["profile"].get(cat, 0) * 7
    if not weekly:
        return
    budget   = s.get("grandma_budget", 0)   # 0 = uncapped
    spent, cases_bought = 0, 0
    bought_lines = []
    for cat, wk in sorted(weekly.items(), key=lambda kv: -kv[1]):
        item   = COSTPRO_ITEMS.get(cat)
        if not item:
            continue
        target = wk * GRANDMA_BUFFER
        need   = target - inv.get(cat, 0)
        if need <= 0:
            continue
        cases  = int(need // item["units"]) + (1 if need % item["units"] else 0)
        case_cost = int(round(item["price"] * (1 + GRANDMA_MARKUP)))
        for _ in range(cases):
            if s["cash"] < case_cost:
                break
            if budget and spent + case_cost > budget:
                break
            s["cash"]  -= case_cost
            inv[cat]    = inv.get(cat, 0) + item["units"]
            spent      += case_cost
            cases_bought += 1
            bought_lines.append(cat)
    # Quirky variance: occasional free sale find.
    if cases_bought and random.random() < 0.15:
        cat  = random.choice(bought_lines)
        item = COSTPRO_ITEMS[cat]
        inv[cat] = inv.get(cat, 0) + item["units"]
        events.append({"prop": "Grandma's Shop", "type": "positive", "category": "business",
                       "text": f"🧺 Grandma found {VM_PRODUCTS[cat]['name']} on sale — grabbed a free extra case!"})
    if cases_bought:
        s["log"].insert(0, {"day": current_day, "type": "info",
            "text": f"🧺 Grandma's weekly shop — {cases_bought} cases for ${spent:,} (incl. her markup)"})
        events.append({"prop": "Grandma's Shop", "type": "neutral", "category": "business",
                       "text": f"🧺 Grandma did the weekly shop — {cases_bought} cases, ${spent:,} (with her 18% markup)"})
    s["grandma_last_shop"] = current_day

# ── CostPro Wholesale — inventory items ───────────────────────────────────────
COSTPRO_ITEMS = {
    "snacks":    {"name": "Snacks (case)",      "icon": "🍫", "price":  45, "units": 40, "category": "vending", "desc": "Candy & chips. Steady sellers everywhere. 40 units/case."},
    "cold":      {"name": "Cold Drinks (case)", "icon": "🥤", "price":  58, "units": 40, "category": "vending", "desc": "Soda & water. Big at parks, stations, summer. 40 units/case."},
    "hot":       {"name": "Hot Drinks (case)",  "icon": "☕", "price":  48, "units": 30, "category": "vending", "desc": "Coffee & cocoa. Office gold. Perishable — sells fast or spoils. 30 units/case."},
    "energy":    {"name": "Energy (case)",      "icon": "⚡", "price":  62, "units": 30, "category": "vending", "desc": "Energy drinks & bars. High margin, gyms & offices love them. 30 units/case."},
    "fresh":     {"name": "Fresh Food (case)",  "icon": "🥗", "price":  72, "units": 20, "category": "vending", "desc": "Sandwiches & salads. Best margin, but spoils in 3 days. 20 units/case."},
    "specialty": {"name": "Specialty (case)",   "icon": "🎁", "price":  62, "units": 24, "category": "vending", "desc": "Novelty & local goods. Niche but lucrative at the right spot. 24 units/case."},
    "soap":           {"name": "Laundry Soap",          "icon": "🧼", "price": 300,   "desc": "Required to operate. Each case lasts 7 days.",  "category": "laundromat"},
    "softener":       {"name": "Fabric Softener",       "icon": "🌸", "price": 500,   "desc": "+20% daily income. Lasts 10 days per case.",    "category": "laundromat"},
    "sheets":         {"name": "Dryer Sheets",          "icon": "🌬️", "price": 400,   "desc": "+15% daily income. Lasts 10 days per case.",   "category": "laundromat"},
    "kb_ginger":   {"name": "Ginger 'Mule' Kombucha",  "icon": "🫚", "price": 380, "desc": "House pour. Zingy. Lasts 10 days per keg. (Kombucha Bar)", "category": "studio_bar", "kb_income": 0.6, "kb_sat": 2},
    "kb_hibiscus": {"name": "Hibiscus 'Cosmo' Kombucha","icon": "🌺", "price": 520, "desc": "Pink, fancy, photogenic. 10 days per keg. (Kombucha Bar)", "category": "studio_bar", "kb_income": 0.9, "kb_sat": 3},
    "kb_charcoal": {"name": "Charcoal 'Detox' Shots",  "icon": "🖤", "price": 460, "desc": "Tastes like punishment. People love it. 10 days/keg.", "category": "studio_bar", "kb_income": 0.8, "kb_sat": 2},
    "kb_cbd":      {"name": "CBD 'Sleepytime' Brew",   "icon": "😌", "price": 640, "desc": "The nightcap. Mellow vibes. 10 days per keg.", "category": "studio_bar", "kb_income": 1.0, "kb_sat": 4},
    "kb_sparkle":  {"name": "Sparkling Reserve",       "icon": "🥂", "price": 900, "desc": "The 'champagne.' Premium pour for VIPs. 10 days/keg.", "category": "studio_bar", "kb_income": 1.6, "kb_sat": 5},
    "cw_basic_soap":    {"name": "Basic Soap",           "icon": "🧼", "price": 350,   "desc": "Required to operate. 7 days per case.",               "category": "car_wash"},
    "cw_standard_soap": {"name": "Standard Soap",        "icon": "🫧", "price": 500,   "desc": "Required for Standard Wash+. 10 days per case.",      "category": "car_wash"},
    "cw_premium_wax":   {"name": "Premium Wax",          "icon": "✨", "price": 700,   "desc": "Required for Deluxe+. +30% income on Deluxe tier. 8 days per case.", "category": "car_wash"},
    "cw_tire_shine":    {"name": "Tire Shine",           "icon": "🖤", "price": 400,   "desc": "+15% income across all bays. 10 days per case.",      "category": "car_wash"},
    "cw_air_freshener": {"name": "Air Fresheners",       "icon": "🌲", "price": 300,   "desc": "+10% regulars growth rate. 12 days per case.",        "category": "car_wash"},
    "arcade_prizes":    {"name": "Prize Stock (case)",   "icon": "🧸", "price": 320, "units": 60, "category": "arcade", "desc": "Plush, tickets & trinkets for the prize counter. A stocked counter boosts cabinet income — but stock gets won daily. 60 units/case."},
}

# ── Dirty Money Laundromat ─────────────────────────────────────────────────────
LAUNDROMAT_PRICE                   = 250_000
LAUNDROMAT_START_MACHINES          = 4     # machines included in the purchase (2 washers + 2 dryers)
LAUNDROMAT_MAX_MACHINES            = 16
LAUNDROMAT_MACHINE_PRICES          = [15_000, 20_000, 25_000, 30_000, 35_000, 40_000, 45_000, 50_000, 55_000]  # machines 4–12
LAUNDROMAT_BASE_INCOME_PER_MACHINE = 280   # per day per working machine
LAUNDROMAT_CLEAN_DECAY             = 8     # cleanliness drops per day
LAUNDROMAT_BREAKDOWN_PCT           = 0.06  # 6% chance per machine per day
LAUNDROMAT_CLEAN_COST              = 75    # manual deep clean
LAUNDROMAT_REPAIR_COST             = 150   # manual repair (waived with insurance)
LAUNDROMAT_INSURANCE_WEEKLY        = 400

LAUNDROMAT_EVENTS = [
    # positive
    {"text": "Neighborhood moms group made your laundromat their weekly spot — regulars up!",   "type": "positive", "effect": "regulars",     "value":  5},
    {"text": "Nearby apartment complex lost their laundry room — residents flooding in!",        "type": "positive", "effect": "income_bonus",  "value": 400},
    {"text": "Social media influencer posted about your laundromat — unexpected rush today!",   "type": "positive", "effect": "income_mult",   "value":  0.5},
    {"text": "High school sports team after a muddy game — machines ran all day!",               "type": "positive", "effect": "income_bonus",  "value": 300},
    {"text": "Heat wave made everyone want fresh laundry — business is booming!",               "type": "positive", "effect": "income_mult",   "value":  0.4},
    {"text": "5-star Yelp review going viral — foot traffic jumped!",                           "type": "positive", "effect": "regulars",     "value":  8},
    {"text": "Corporate account from a nearby hotel — big load, big pay!",                      "type": "positive", "effect": "income_bonus",  "value": 500},
    {"text": "Festival nearby brought visitors who needed fresh clothes!",                       "type": "positive", "effect": "income_mult",   "value":  0.3},
    {"text": "The dog groomer next door sends overflow customers your way!",                    "type": "positive", "effect": "income_bonus",  "value": 250},
    {"text": "Your regulars started recommending the laundromat to friends!",                   "type": "positive", "effect": "regulars",     "value":  6},
    {"text": "Rain storm kept people indoors — they doubled up on laundry loads!",              "type": "positive", "effect": "income_mult",   "value":  0.3},
    {"text": "College move-in week — students piled in with mountains of laundry!",             "type": "positive", "effect": "income_bonus",  "value": 450},
    {"text": "Local daycare center sent their weekly load — easy money!",                       "type": "positive", "effect": "income_bonus",  "value": 200},
    # negative
    {"text": "Water main break shut you down for the day — no income!",                         "type": "negative", "effect": "income_zero",   "value":  0},
    {"text": "Pest inspection found a roach near one of your machines — health department fine!", "type": "negative", "effect": "fine",         "value": 300},
    {"text": "Pipe burst and flooded two of your machines — they need repairs!",                "type": "negative", "effect": "break_two",     "value":  2},
    {"text": "Power surge fried the payment systems — machines offline half the day.",          "type": "negative", "effect": "income_mult",   "value": -0.5},
    {"text": "Dryer vent overheated — machines shut down early for a safety inspection.",       "type": "negative", "effect": "income_mult",   "value": -0.4},
    {"text": "Customer left a scathing review about the smell — cleanliness reputation hit!",   "type": "negative", "effect": "cleanliness",   "value": -15},
    {"text": "Thieves broke in and stole quarters from your machines.",                         "type": "negative", "effect": "fine",          "value": 200},
    {"text": "Water heater went out — cold-water washes only. Income cut today.",               "type": "negative", "effect": "income_mult",   "value": -0.35},
    {"text": "New competitor laundromat opened nearby — some regulars drifted away.",           "type": "negative", "effect": "regulars",     "value": -8},
    {"text": "A washing machine overflowed, flooding the floor — cleanup fees!",                "type": "negative", "effect": "fine",          "value": 250},
    {"text": "City repaving the street — limited parking, traffic way down today.",             "type": "negative", "effect": "income_mult",   "value": -0.45},
    {"text": "Health inspector surprise visit — small fine for missing paperwork.",             "type": "negative", "effect": "fine",          "value": 175},
    {"text": "Vandals scratched up your machines overnight — repair costs.",                    "type": "negative", "effect": "fine",          "value": 150},
    {"text": "Plumbing leak in the back room — had to close early for repairs.",                "type": "negative", "effect": "income_mult",   "value": -0.3},
]

LAUNDROMAT_STAFF = {
    "janitor":   {"name": "Janitor",   "icon": "🧹", "cost": 175, "desc": "Auto-cleans when cleanliness drops below 75%."},
    "repairman": {"name": "Repairman", "icon": "🔧", "cost": 225, "desc": "Auto-fixes broken machines every day."},
    "manager":   {"name": "Supply Manager", "icon": "📦", "cost": 200, "desc": "Auto-orders soap, softener & dryer sheets — keeps you stocked, balanced to a buffer."},
}

LAUNDROMAT_UPGRADES = {
    "heavy_duty":       {"name": "Heavy-Duty Motor",   "icon": "⚙️",  "cost": 2_000, "desc": "Breakdown chance 6% → 2%."},
    "card_reader":      {"name": "Card Reader",         "icon": "💳", "cost": 1_500, "desc": "+20% throughput from this machine."},
    "energy_efficient": {"name": "Energy Efficient",    "icon": "🌿", "cost": 1_000, "desc": "Soap lasts 10 days instead of 7."},
}

# ── Laundromat overhaul: demand vs. capacity, machine types, loyalty, add-ons ──
# A load needs a WASH stage and a DRY stage. Washers add wash capacity, dryers add
# dry capacity, combos add both. Daily loads = min(wash_cap, dry_cap, demand);
# unmet demand = turn-aways (lost income + regulars erode). Income = loads × rate.
LAUNDROMAT_MACHINE_TYPES = {
    "washer": {"name": "Washer", "icon": "🌀", "wash": 12, "dry": 0,  "price": 15_000},
    "dryer":  {"name": "Dryer",  "icon": "💨", "wash": 0,  "dry": 12, "price": 15_000},
    "combo":  {"name": "Combo Unit", "icon": "🔄", "wash": 16, "dry": 16, "price": 40_000},
}
LAUNDROMAT_REV_PER_LOAD     = 22     # before cleanliness/supply multipliers
LAUNDROMAT_BASE_DEMAND      = 16     # loads/day floor
LAUNDROMAT_DEMAND_PER_REG   = 0.40   # + per regular
LAUNDROMAT_DEMAND_PER_MEMBER= 0.50   # + per member
LAUNDROMAT_DEMAND_VOLATILITY= 0.15
LAUNDROMAT_MEMBER_FEE       = 7      # recurring $/member/day
LAUNDROMAT_MACHINE_STEP     = 2_500  # price escalation per machine beyond the starters

LAUNDROMAT_ADDONS = {
    "vending":   {"name": "In-House Vending",   "icon": "🥤", "cost": 4_000, "income": 0,   "desc": "Adds a 7th machine to your Vending empire — stock & manage it from the Vending tab."},
    "arcade":    {"name": "Back-Room Arcade",   "icon": "🕹️", "cost": 20_000, "income": 0,  "desc": "Open the laundromat's back room to the public as a games arcade — unlocks a whole new business."},
    "atm":       {"name": "ATM",                "icon": "🏧", "cost": 3_500, "income": 55,  "desc": "Fee income that scales with foot traffic."},
    "detergent": {"name": "Detergent Vending",  "icon": "🧴", "cost": 3_000, "income": 50,  "desc": "Sell soap & supplies on-site. +$50/day."},
    "wash_fold": {"name": "Wash & Fold Service","icon": "🧺", "cost": 6_500, "income": 0,   "desc": "Turns spare machine capacity into high-margin service work."},
    "loyalty":   {"name": "Loyalty Program",    "icon": "💳", "cost": 4_500, "income": 0,   "desc": "Convert happy regulars into paying members — sticky recurring income."},
}

# ── The Back-Room Arcade (secret business — unlocked by the laundromat add-on) ──
# Cabinets have a GENRE; a varied floor out-earns duplicates (saturation). Cabinets
# wear & break (upkeep), and foot traffic rides the laundromat's regulars (synergy).
# (Playable mini-games + the hot-cabinet/high-score loop are the NEXT phase.)
ARCADE_CABINET_PRICE       = 15_000   # base; escalates per cabinet owned
ARCADE_INCOME_PER_CABINET  = 95       # base $/day per cabinet (before genre/condition/traffic)
ARCADE_INCOME_VOLATILITY   = 0.20
ARCADE_CABINET_DECAY       = 3        # condition lost per day
ARCADE_BREAKDOWN_PCT       = 0.04     # per working cabinet per day
ARCADE_SERVICE_COST        = 250      # manual service: fix + restore a cabinet
ARCADE_GENRES = {
    "fighting": {"name": "Fighting", "icon": "🥊"},
    "racing":   {"name": "Racing",   "icon": "🏎️"},
    "shooter":  {"name": "Shooter",  "icon": "👾"},
    "rhythm":   {"name": "Rhythm",   "icon": "🕺"},
    "pinball":  {"name": "Pinball",  "icon": "🎰"},
    "prize":    {"name": "Prize / Claw", "icon": "🎁"},
    "retro":    {"name": "Retro",    "icon": "🕹️"},
}
ARCADE_GAMES = [
    {"title": "Street Brawler",  "genre": "fighting"},
    {"title": "Kung-Fu Alley",   "genre": "fighting"},
    {"title": "Neon Drift",      "genre": "racing"},
    {"title": "Retro Racer",     "genre": "racing"},
    {"title": "Galaxy Siege",    "genre": "shooter"},
    {"title": "Pixel Blaster",   "genre": "shooter"},
    {"title": "Laser Tag Lords", "genre": "shooter"},
    {"title": "Dance Fever",     "genre": "rhythm"},
    {"title": "Beat Pulse",      "genre": "rhythm"},
    {"title": "Pinball Wizard",  "genre": "pinball"},
    {"title": "Crane Grab",      "genre": "prize"},
    {"title": "Ticket Tornado",  "genre": "prize"},
    {"title": "Zombie Dunk",     "genre": "prize"},
    {"title": "Quarter Muncher", "genre": "retro"},
]
def _arcade_genre_of(title):
    return next((g["genre"] for g in ARCADE_GAMES if g["title"] == title), "retro")
ARCADE_CLEAN_DECAY     = 4        # cleanliness lost per day (foot traffic)
ARCADE_CLEAN_COST      = 120      # manual deep clean
ARCADE_TILL_PER_CABINET= 1_200    # uncollected cash a machine holds before coins overflow
ARCADE_STAFF = {
    "tech":      {"name": "Repair Tech",   "icon": "🔧", "cost": 200, "desc": "Auto-fixes broken cabinets and keeps them maintained."},
    "collector": {"name": "Arcade Manager", "icon": "💰", "cost": 220, "desc": "Banks the machine cash daily AND keeps the prize counter stocked from CostPro."},
    "janitor":   {"name": "Janitor",       "icon": "🧹", "cost": 150, "desc": "Keeps the arcade floor clean automatically."},
}

# Only two of the same title may sit on the floor at once.
ARCADE_MAX_PER_TITLE = 2

# Playable mini-games: beating a cabinet's high score makes it run 🔥 HOT — an
# income boost for a few days. Each cabinet stores its own high_score + hot_until.
ARCADE_HOT_DAYS = 6      # how long a cabinet stays hot after a new high score
ARCADE_HOT_MULT = 1.6    # hot cabinets earn 60% more while the streak lasts
# One playable archetype per genre; cabinet titles are skins of their genre's game.
ARCADE_GENRE_GAME = {
    "fighting": "Counter Brawler", "racing": "Lane Dodge", "shooter": "Space Siege",
    "rhythm": "Beat Tap", "pinball": "Pinball", "prize": "Claw Grab", "retro": "Quarter Muncher",
}

# ── Prize counter ──────────────────────────────────────────────────────────────
# Prize stock (bought from CostPro) is an investment: a stocked prize counter
# boosts cabinet income up to +PRIZE_BOOST_MAX, but prizes get won/handed out
# daily, so you keep restocking.
ARCADE_PRIZE_BOOST_MAX   = 0.30   # full prize counter → +30% income
ARCADE_PRIZE_USE_PER_CAB = 1.6    # prize units consumed per working cabinet/day (×traffic)

# ── Cabinet market (refreshes only after you buy — no free re-rolling) ──────────
ARCADE_MARKET_SIZE       = 3
ARCADE_RARE_CHANCE       = 0.20   # chance a rare import shows up in the daily lineup
ARCADE_RARE_PRICE_MULT   = 2.4    # rares cost more...
ARCADE_RARE_INCOME_MULT  = 1.8    # ...but earn a lot more

# Rare import cabinets — coveted machines that only appear occasionally.
ARCADE_RARE_GAMES = [
    {"title": "Samurai Showdown DX", "genre": "fighting"},
    {"title": "Outrun Phantom",      "genre": "racing"},
    {"title": "Alien Onslaught EX",  "genre": "shooter"},
    {"title": "Taiko Legend",        "genre": "rhythm"},
    {"title": "Gold Fever Pinball",  "genre": "pinball"},
    {"title": "Mega Claw Deluxe",    "genre": "prize"},
    {"title": "Vector Classic '83",  "genre": "retro"},
]
ARCADE_RARE_TITLES = {g["title"] for g in ARCADE_RARE_GAMES}

# ── Decor / theming (one-time cosmetic upgrades with real effects) ─────────────
ARCADE_DECOR = {
    "neon":         {"name": "Neon Lights",   "icon": "🌈", "cost": 6_000,  "traffic": 0.08, "desc": "Glowing neon pulls passersby in. +8% foot traffic."},
    "sign":         {"name": "Marquee Sign",  "icon": "🪧", "cost": 5_500,  "traffic": 0.06, "desc": "A big lit sign out front. +6% foot traffic."},
    "themed_walls": {"name": "Themed Murals", "icon": "🎨", "cost": 7_500,  "traffic": 0.10, "desc": "Floor-to-ceiling art makes it a destination. +10% foot traffic."},
    "carpet":       {"name": "Arcade Carpet", "icon": "🟪", "cost": 4_500,  "clean": 1.5,    "desc": "Classic patterned carpet hides wear — the floor dirties slower."},
    "snack_nook":   {"name": "Snack Nook",    "icon": "🍿", "cost": 8_000,  "income": 0.08,  "desc": "Popcorn & soda corner. +8% to all cabinet income."},
}

# ── Arcade events (choice cards) ───────────────────────────────────────────────
# One may fire per advance at ARCADE_EVENT_CHANCE. Effect keys on a choice:
# cost (cash out), cash (cash in), clean (cleanliness delta), prizes (prize-stock
# delta), break_n (break N random working cabinets), steal_till_pct (skim the
# UNCOLLECTED machine cash — a Floor Manager who banks daily makes this harmless).
# Optional "risk": {chance, cost, result_bad} gamble resolved server-side.
ARCADE_EVENT_CHANCE = 0.12
ARCADE_EVENTS = [
    {"key": "break_in", "title": "Cabinets Jimmied", "icon": "🦹",
     "text": "Someone pried open your cabinets overnight, going for the uncollected coins.", "choices": [
        {"label": "Upgrade the cabinet locks", "cost": 320, "result": "Hardened locks installed — they left empty-handed."},
        {"label": "Just clean up the mess", "cost": 0, "steal_till_pct": 0.5, "result": "They made off with {lost} that was sitting in the machines."}]},
    {"key": "spill", "title": "Big Soda Spill", "icon": "🥤",
     "text": "A toppled tray of drinks left the floor sticky and gross.", "choices": [
        {"label": "Mop it immediately", "cost": 60, "clean": 5, "result": "Spotless again in minutes."},
        {"label": "Throw down a 'wet floor' sign", "cost": 0, "clean": -18, "result": "It'll dry... eventually. The floor's a mess in the meantime."}]},
    {"key": "rowdy", "title": "Rowdy Crowd", "icon": "😤", "problem": True,
     "text": "A pack of teens got too rough on the machines tonight.", "choices": [
        {"label": "Hire a door guy for the night", "cost": 200, "result": "Order restored — nothing got wrecked."},
        {"label": "Let it ride", "cost": 0, "break_n": 1, "result": "They cracked a cabinet before clearing out."}]},
    {"key": "power_bill", "title": "Surprise Power Bill", "icon": "🔌",
     "text": "All those cabinets and neon add up — the utility company sent a fat bill.", "choices": [
        {"label": "Pay it", "cost": 280, "result": "Paid. The lights stay on."},
        {"label": "Dispute the meter reading", "cost": 0, "result": "They knocked it down to nothing.",
         "risk": {"chance": 0.45, "cost": 420, "result_bad": "The meter was right — and now there's a late fee on top."}}]},
    {"key": "claw_jam", "title": "Claw Machine Jammed", "icon": "🎁", "problem": True,
     "text": "The prize claw seized up mid-grab and a crowd is grumbling.", "choices": [
        {"label": "Service it on the spot", "cost": 110, "result": "Back to grabbing in no time."},
        {"label": "Slap an 'out of order' note on it", "cost": 0, "prizes": -8, "result": "You lose a chunk of prize stock to a stuck door before it's noticed."}]},
    {"key": "high_score", "title": "Viral High Score", "icon": "🏆", "problem": False,
     "text": "A regular set a world-record run and the clip is blowing up online.", "choices": [
        {"label": "Lean in — host a watch night", "cost": 50, "cash": 520, "result": "The place is packed for the rematch. Register sings."},
        {"label": "Just enjoy the buzz", "cost": 0, "cash": 180, "result": "A nice little bump in walk-ins."}]},
    {"key": "birthday", "title": "Birthday Party Booking", "icon": "🎂", "problem": False,
     "text": "A parent wants to book out a corner for a kid's birthday bash.", "choices": [
        {"label": "Premium package — prizes included", "cost": 0, "cash": 600, "prizes": -10, "result": "A loud, happy afternoon — and a tidy fee."},
        {"label": "Floor rental only", "cost": 0, "cash": 300, "result": "They bring their own cake; you bank the rental."},
        {"label": "Too much hassle — pass", "cost": 0, "result": "You keep the floor open to walk-ins."}]},
    {"key": "supplier_deal", "title": "Prize Supplier Deal", "icon": "🧸", "problem": False,
     "text": "A wholesaler is dumping plush toys and wants them gone today.", "choices": [
        {"label": "Buy the pallet", "cost": 240, "prizes": 80, "result": "A mountain of prizes at a steal — the counter's stocked for ages."},
        {"label": "Grab a small lot", "cost": 90, "prizes": 25, "result": "A modest top-up at a fair price."},
        {"label": "Not today", "cost": 0, "result": "You let it pass."}]},
    {"key": "retro_craze", "title": "Retro Craze", "icon": "👾", "problem": False,
     "text": "A nostalgia wave has everyone hunting down old-school cabinets.", "choices": [
        {"label": "Ride the wave", "cost": 0, "cash": 260, "result": "Quarters rain in all weekend."}]},
    {"key": "inspection", "title": "Safety Inspection", "icon": "📋", "problem": True,
     "text": "The city's checking your cabinets for wiring and fire code.", "choices": [
        {"label": "Pay for full compliance", "cost": 260, "clean": 6, "result": "Passed clean — and the place looks sharp."},
        {"label": "Do the bare minimum", "cost": 80, "result": "Squeaked by.",
         "risk": {"chance": 0.40, "cost": 300, "result_bad": "A follow-up visit caught more issues — bigger fine."}}]},
]

def _arcade_roll_market(s):
    """Build the day's cabinet lineup (ARCADE_MARKET_SIZE offers, maybe one rare).
    Skips titles the player already owns two of. Stored on arc['market']."""
    arc = s.get("arcade")
    if not arc:
        return
    cabs       = arc.get("cabinets", [])
    # Base climbs $2,000 per cabinet already owned...
    base_price = ARCADE_CABINET_PRICE + len(cabs) * 2_000
    # ...and each offer gets a small ±9% wiggle so the three lineup prices look
    # distinct instead of identical (rounded to the nearest $50).
    def _jittered(base):
        return int(round(base * random.uniform(0.91, 1.09) / 50.0)) * 50
    title_ct   = {}
    for c in cabs:
        title_ct[c.get("title")] = title_ct.get(c.get("title"), 0) + 1
    offers, used = [], set()
    rare_idx = random.randrange(ARCADE_MARKET_SIZE) if (ARCADE_RARE_GAMES and random.random() < ARCADE_RARE_CHANCE) else -1
    for i in range(ARCADE_MARKET_SIZE):
        if i == rare_idx:
            g = random.choice(ARCADE_RARE_GAMES)
            offers.append({"id": i, "title": g["title"], "genre": g["genre"], "rare": True,
                           "price": _jittered(base_price * ARCADE_RARE_PRICE_MULT)})
        else:
            pool = [g for g in ARCADE_GAMES
                    if g["title"] not in used and title_ct.get(g["title"], 0) < ARCADE_MAX_PER_TITLE]
            if not pool:
                pool = [g for g in ARCADE_GAMES if g["title"] not in used] or ARCADE_GAMES
            g = random.choice(pool)
            used.add(g["title"])
            offers.append({"id": i, "title": g["title"], "genre": g["genre"], "rare": False,
                           "price": _jittered(base_price)})
    random.shuffle(offers)
    for n, o in enumerate(offers):
        o["id"] = n
    arc["market"]      = offers
    arc["market_day"]  = s.get("day", 0)
    arc["market_used"] = False

def _arcade_queue_event(s):
    """Build a pending arcade-event choice card (labels + costs only)."""
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return None
    ev = random.choice(ARCADE_EVENTS)
    return {
        "key":   ev["key"], "title": ev["title"], "icon": ev["icon"], "text": ev["text"],
        "choices": [{"label": c["label"], "cost": c.get("cost", 0), "gain": c.get("cash", 0)}
                    for c in ev["choices"]],
    }

def _arcade_apply_event_choice(s, choice):
    """Apply an arcade event choice. Returns (result_text, was_bad_outcome)."""
    arc = s.setdefault("arcade", {})
    result, bad = choice.get("result", "Done."), False
    extra_cost = 0
    risk = choice.get("risk")
    if risk and random.random() < risk.get("chance", 0):
        bad, extra_cost = True, risk.get("cost", 0)
        result = risk.get("result_bad", result)
    cost = choice.get("cost", 0) + extra_cost
    if cost:
        s["cash"] = max(0, s["cash"] - cost)
    if choice.get("cash"):
        s["cash"] += choice["cash"]
    if choice.get("clean"):
        arc["cleanliness"] = max(0, min(100, arc.get("cleanliness", 100) + choice["clean"]))
    if choice.get("prizes"):
        arc["prizes"] = max(0, arc.get("prizes", 0) + choice["prizes"])
    if choice.get("steal_till_pct"):
        lost = int(arc.get("uncollected", 0) * choice["steal_till_pct"])
        arc["uncollected"] = max(0, arc.get("uncollected", 0) - lost)
        result = result.replace("{lost}", f"${lost:,}")
    if choice.get("break_n"):
        working = [c for c in arc.get("cabinets", []) if c.get("status") == "working"]
        random.shuffle(working)
        for c in working[:choice["break_n"]]:
            c["status"] = "broken"
    return result, bad

# ── Brass Pole Fitness Studio ──────────────────────────────────────────────────
POLE_STUDIO_PRICE            = 600_000
POLE_STUDIO_UNLOCK_LEVEL     = 8
POLE_STUDIO_START_POLES      = 0
POLE_STUDIO_MAX_POLES        = 6
POLE_STUDIO_POLE_PRICES      = [20_000, 25_000, 30_000, 35_000, 45_000, 55_000]
# Class slots are the purchasable capacity now (poles retired). Start with 2; buy
# up to 8 (more than the 6 instructors, so you can double up popular classes).
STUDIO_START_SLOTS = 2
STUDIO_MAX_SLOTS   = 8
STUDIO_SLOT_PRICES = [16_000, 24_000, 33_000, 44_000, 57_000, 72_000]  # slots 3..8
POLE_STUDIO_ATM_DECAY        = 6
POLE_STUDIO_CLEAN_DECAY      = 7
POLE_STUDIO_BREAKDOWN_PCT    = 0.05
POLE_STUDIO_CLEAN_COST       = 100
POLE_STUDIO_CLEAN_ENERGY     = 4
POLE_STUDIO_REPAIR_COST      = 200
POLE_STUDIO_INSURANCE_WEEKLY = 500
POLE_STUDIO_PEP_ENERGY       = 3
POLE_STUDIO_PEP_MOOD         = 20
POLE_STUDIO_COFFEE_COST      = 300
POLE_STUDIO_COFFEE_MOOD      = 8

POLE_STUDIO_DANCERS = {
    "celestia": {"name": "Celestia",  "icon": "💫", "salary": 350, "base_income": 500,
                 "specialty": "Advanced Technique",
                 "desc": "The studio's founding instructor. Chose the name 'Celestia' in 2019 after a spiritual awakening. The awakening was a Pilates class. She's fully committed to it.",
                 "mood_decay": 4, "mood_start": 75},
    "raven":    {"name": "Raven",     "icon": "🖤", "salary": 400, "base_income": 620,
                 "specialty": "Competitive Performance",
                 "desc": "Former competitor on a circuit she describes as 'very prestigious and real.' The trophies are in her car.",
                 "mood_decay": 7, "mood_start": 80},
    "sunshine": {"name": "Sunshine",  "icon": "☀️", "salary": 250, "base_income": 370,
                 "specialty": "Beginner & Senior Wellness",
                 "desc": "Three separate Yelp reviews have called her 'aggressively wholesome.' She considers this a compliment.",
                 "mood_decay": 2, "mood_start": 90},
    "mercedes": {"name": "Mercedes",  "icon": "💼", "salary": 300, "base_income": 460,
                 "specialty": "Corporate & Private Sessions",
                 "desc": "Holds an MBA. Books all her own clients. Sends follow-up emails. The emails are extremely professional.",
                 "mood_decay": 4, "mood_start": 70},
    "diamond":  {"name": "Diamond",   "icon": "💎", "salary": 350, "base_income": 490,
                 "specialty": "Late Night & Special Events",
                 "desc": "Claims to have performed at three celebrity events. All three are unverifiable. The stories are incredible.",
                 "mood_decay": 6, "mood_start": 65},
    "gary":     {"name": "Gary",      "icon": "🤷", "salary": 200, "base_income": 340,
                 "specialty": "Tuesday Mornings",
                 "desc": "His qualifications are unclear. The Tuesday 9am slot has a 3-month waitlist. He just shrugs.",
                 "mood_decay": 0, "mood_start": 72},
}

# demand effect keys: cash_cost, salary_delta, income_bonus, mood_self, mood_all,
#                     members, reputation, atmosphere, cleanliness, quit
POLE_STUDIO_DEMANDS = [
    # ── CELESTIA ──────────────────────────────────────────────────────────────
    {"key":"cel_warmup",     "dancer":"celestia","deadline":5,"type":"financial",
     "text":"I'd like a warm-up area near my pole. A yoga mat and a foam roller.",
     "accept_note":"She sets it up herself. Immediately.",
     "reject_note":"She handles it professionally and does not forget.",
     "accept":{"cash_cost":150,"mood_self":15},"reject":{"mood_self":-10}},
    {"key":"cel_title",      "dancer":"celestia","deadline":6,"type":"ego",
     "text":"I'd like to be listed as Lead Instructor on all studio materials.",
     "accept_note":"Mood visibly improves. She says nothing.",
     "reject_note":"'It's not about the title.' (It is entirely about the title.)",
     "accept":{"mood_self":20,"members":3},"reject":{"mood_self":-20}},
    {"key":"cel_showcase",   "dancer":"celestia","deadline":7,"type":"values",
     "text":"I think we should host a quarterly showcase. I'll organize everything.",
     "accept_note":"She produces a 4-page planning document within the hour.",
     "reject_note":"She proposes it again next month. Slightly less warmly.",
     "accept":{"cash_cost":800,"reputation":20,"members":8,"mood_self":25},"reject":{"mood_self":-15}},
    {"key":"cel_locker",     "dancer":"celestia","deadline":4,"type":"financial",
     "text":"I'd like a private locker.",
     "accept_note":"Organized within the hour.",
     "reject_note":"A sticky note appears on a locker. It says 'Celestia.' Nobody moves it.",
     "accept":{"cash_cost":200,"mood_self":10},"reject":{"mood_self":-5}},
    {"key":"cel_salary",     "dancer":"celestia","deadline":5,"type":"financial",
     "text":"I've been here since the beginning. I think it's time we discussed a salary review.",
     "accept_note":"She nods once. That's it.",
     "reject_note":"She begins 'passively exploring options.'",
     "accept":{"salary_delta":75,"mood_self":25},"reject":{"mood_self":-20}},
    {"key":"cel_photo",      "dancer":"celestia","deadline":6,"type":"ego",
     "text":"The studio photo on the website is from 2019. I'm in it, but barely.",
     "accept_note":"New photo is stunning. She chose the angles.",
     "reject_note":"She updates her personal headshot and does not share it with the studio.",
     "accept":{"cash_cost":500,"mood_self":15,"reputation":5},"reject":{"mood_self":-10}},
    {"key":"cel_mentorship", "dancer":"celestia","deadline":7,"type":"values",
     "text":"I'd like to offer a mentorship program for the newer dancers.",
     "accept_note":"She starts immediately. The newer dancers appreciate it.",
     "reject_note":"She mentors them informally anyway. You get no credit.",
     "accept":{"mood_self":20,"mood_all":5},"reject":{"mood_self":-10}},
    {"key":"cel_coffee",     "dancer":"celestia","deadline":3,"type":"financial",
     "text":"The break room needs a proper coffee machine. Not instant.",
     "accept_note":"A French press and a bag of single-origin beans appear two days later.",
     "reject_note":"A French press appears from somewhere. Nobody asks.",
     "accept":{"cash_cost":300,"mood_self":10,"mood_all":5},"reject":{"mood_self":-5}},
    # ── RAVEN ─────────────────────────────────────────────────────────────────
    {"key":"rav_rechrome",   "dancer":"raven","deadline":2,"type":"financial",
     "text":"My pole needs re-chroming. This week.",
     "accept_note":"New pole. Raven approves without saying so.",
     "reject_note":"She meant it.",
     "accept":{"cash_cost":600,"mood_self":20},"reject":{"mood_self":-40,"quit":True}},
    {"key":"rav_slot",       "dancer":"raven","deadline":3,"type":"scheduling",
     "text":"I want the 7pm slot. That's my time.",
     "accept_note":"She takes the slot. Doesn't thank you.",
     "reject_note":"She takes it anyway on day 4.",
     "accept":{"mood_self":15,"mood_all":-5},"reject":{"mood_self":-25}},
    {"key":"rav_comp_off",   "dancer":"raven","deadline":4,"type":"scheduling",
     "text":"I entered a regional competition. I need Friday off.",
     "accept_note":"She returns with a trophy. She says it's 'very legitimate.'",
     "reject_note":"Personal day. She left a note.",
     "accept":{"mood_self":30,"reputation":10},"reject":{"mood_self":-20}},
    {"key":"rav_sound",      "dancer":"raven","deadline":5,"type":"financial",
     "text":"The sound system needs to be replaced.",
     "accept_note":"The whole studio sounds better.",
     "reject_note":"Mood in freefall. She's 'listening to offers.'",
     "accept":{"cash_cost":1500,"mood_self":20,"mood_all":5},"reject":{"mood_self":-30}},
    {"key":"rav_billing",    "dancer":"raven","deadline":3,"type":"ego",
     "text":"I want top billing on all promotional material. My name first.",
     "accept_note":"She sends you her preferred font.",
     "reject_note":"She prints her own schedule card and tapes it to the door.",
     "accept":{"mood_self":20,"mood_all":-5},"reject":{"mood_self":-20}},
    {"key":"rav_vegas",      "dancer":"raven","deadline":4,"type":"scheduling",
     "text":"There's a competition in Vegas. I need four days and $500 toward travel.",
     "accept_note":"She places. She sends one photo. No caption.",
     "reject_note":"She submits a leave notice. You're not sure if it's a demand or a resignation.",
     "accept":{"cash_cost":500,"mood_self":35,"reputation":15},"reject":{"mood_self":-25}},
    {"key":"rav_sponsor",    "dancer":"raven","deadline":5,"type":"financial",
     "text":"I've been offered a grip spray sponsorship. You get 20% of the deal.",
     "accept_note":"Checks arrive on schedule. Raven handles everything.",
     "reject_note":"She takes it personally. You get nothing.",
     "accept":{"mood_self":15,"income_bonus":150},"reject":{"mood_self":-10}},
    {"key":"rav_ultimatum",  "dancer":"raven","deadline":2,"type":"ultimatum",
     "text":"I've had an offer from Chromatic Fitness. Match what I'm worth or I go.",
     "accept_note":"She stays. One nod of acknowledgment.",
     "reject_note":"She goes. Very professionally. Same day.",
     "accept":{"salary_delta":150,"mood_self":25},"reject":{"mood_self":-50,"quit":True}},
    # ── SUNSHINE ──────────────────────────────────────────────────────────────
    {"key":"sun_shelter",    "dancer":"sunshine","deadline":6,"type":"values",
     "text":"Could we host a free class for the women's shelter? I hope that's okay to ask.",
     "accept_note":"She cries a little. Just a little.",
     "reject_note":"She does it on her own time. You feel genuinely bad.",
     "accept":{"reputation":15,"members":5,"mood_self":25},"reject":{"mood_self":-10}},
    {"key":"sun_microwave",  "dancer":"sunshine","deadline":4,"type":"financial",
     "text":"Could we get a microwave for the break room? The paper cups are a little sad.",
     "accept_note":"She stocks it with instant oatmeal for everyone.",
     "reject_note":"A microwave appears from her car two days later.",
     "accept":{"cash_cost":80,"mood_self":15,"mood_all":8},"reject":{"mood_self":-5}},
    {"key":"sun_bday",       "dancer":"sunshine","deadline":5,"type":"values",
     "text":"One of my seniors is turning 80. Could the studio host her party? Just the space.",
     "accept_note":"Sunshine decorates at 6am. The student cries happy tears.",
     "reject_note":"She finds another venue. The student tells everyone about Sunshine, not the studio.",
     "accept":{"members":4,"reputation":5,"mood_self":20},"reject":{"mood_self":-8}},
    {"key":"sun_cert",       "dancer":"sunshine","deadline":7,"type":"financial",
     "text":"Could the studio cover half of my certification? I'd pay the rest myself.",
     "accept_note":"She earns the cert. Mentions the studio in her thank-you post.",
     "reject_note":"She pays herself. 'It's totally fine.' Mood drops quietly.",
     "accept":{"cash_cost":300,"mood_self":20},"reject":{"mood_self":-10}},
    {"key":"sun_junior",     "dancer":"sunshine","deadline":7,"type":"values",
     "text":"Could we offer junior fitness classes? For kids? You can absolutely say no.",
     "accept_note":"Six families sign up before she finishes the flyer.",
     "reject_note":"She starts a private class in the park. Six families follow her there.",
     "accept":{"members":6,"reputation":8,"mood_self":25},"reject":{"mood_self":-10}},
    {"key":"sun_fundraiser", "dancer":"sunshine","deadline":5,"type":"values",
     "text":"There's a local fitness fundraiser. Could the studio sponsor a table?",
     "accept_note":"She brings a banner and three dancers. Reputation boost.",
     "reject_note":"She sponsors it herself. Lists the studio anyway.",
     "accept":{"cash_cost":400,"reputation":12,"members":4,"mood_self":20},"reject":{"mood_self":-10}},
    {"key":"sun_benefit",    "dancer":"sunshine","deadline":6,"type":"values",
     "text":"My student broke her wrist. She can't afford the bills. Could the studio do a benefit class?",
     "accept_note":"The community shows up. Studio is packed.",
     "reject_note":"Sunshine holds the class on her day off. You get no credit.",
     "accept":{"reputation":20,"members":6,"mood_self":30},"reject":{"mood_self":-15}},
    {"key":"sun_pizza",      "dancer":"sunshine","deadline":4,"type":"values",
     "text":"Could we do a staff appreciation thing? Just pizza and an hour together.",
     "accept_note":"Everyone shows up. Even Gary brings a dessert.",
     "reject_note":"She brings pizza anyway. It lands differently.",
     "accept":{"cash_cost":150,"mood_all":10,"mood_self":15},"reject":{"mood_self":-8}},
    # ── MERCEDES ──────────────────────────────────────────────────────────────
    {"key":"mer_commission", "dancer":"mercedes","deadline":6,"type":"financial",
     "text":"I've drafted a corporate expansion proposal. 10% commission on sessions I book.",
     "accept_note":"Corporate bookings triple within the week.",
     "reject_note":"She manages bookings less aggressively. You notice.",
     "accept":{"mood_self":20,"income_bonus":200},"reject":{"mood_self":-15}},
    {"key":"mer_raise",      "dancer":"mercedes","deadline":3,"type":"ultimatum",
     "text":"I've been approached with an outside contract. I'd like to discuss a counter-offer.",
     "accept_note":"She stays. One professional email of acknowledgment.",
     "reject_note":"She accepts the contract. 24-hour notice. Very professional email.",
     "accept":{"salary_delta":100,"mood_self":20},"reject":{"mood_self":-40,"quit":True}},
    {"key":"mer_lighting",   "dancer":"mercedes","deadline":5,"type":"financial",
     "text":"The changing room lighting needs upgrading for client-facing areas.",
     "accept_note":"Clients comment on it unprompted.",
     "reject_note":"A spreadsheet arrives projecting the cost of not doing it over 12 months.",
     "accept":{"cash_cost":400,"reputation":5,"cleanliness":10,"mood_self":10},"reject":{"mood_self":-10}},
    {"key":"mer_retainer",   "dancer":"mercedes","deadline":5,"type":"scheduling",
     "text":"Authorization to offer a corporate client a 15% retainer discount.",
     "accept_note":"Guaranteed weekly income. Mercedes is satisfied.",
     "reject_note":"She asks again next week with better data.",
     "accept":{"mood_self":12,"income_bonus":300},"reject":{"mood_self":-10}},
    {"key":"mer_booking_line","dancer":"mercedes","deadline":5,"type":"financial",
     "text":"I'd like a dedicated booking line for private and corporate inquiries.",
     "accept_note":"She immediately has three leads she couldn't close before.",
     "reject_note":"She forwards inquiries through her personal email. You see none of them.",
     "accept":{"cash_cost":150,"mood_self":12,"income_bonus":100},"reject":{"mood_self":-8}},
    {"key":"mer_lunchtime",  "dancer":"mercedes","deadline":7,"type":"scheduling",
     "text":"I've identified an underserved market: lunchtime express classes for office workers.",
     "accept_note":"Books solid every day within the first week.",
     "reject_note":"'Noted.' It goes in a document. The document has seventeen pages.",
     "accept":{"mood_self":20,"members":5,"income_bonus":200},"reject":{"mood_self":-12}},
    {"key":"mer_events_title","dancer":"mercedes","deadline":5,"type":"ego",
     "text":"I'd like the title 'Events Director' for private booking conversations. It helps close deals.",
     "accept_note":"She had business cards printed before you answered.",
     "reject_note":"She puts it on her business cards anyway. Her business cards. That she had printed.",
     "accept":{"mood_self":15,"income_bonus":150},"reject":{"mood_self":-10}},
    {"key":"mer_expense",    "dancer":"mercedes","deadline":5,"type":"financial",
     "text":"I've been paying for client entertainment out of pocket. I'd like expense reimbursement.",
     "accept_note":"Corporate income increases noticeably. ROI is immediate.",
     "reject_note":"She stops taking clients to lunch. Corporate bookings slow.",
     "accept":{"cash_cost":200,"mood_self":15,"income_bonus":180},"reject":{"mood_self":-10}},
    # ── DIAMOND ───────────────────────────────────────────────────────────────
    {"key":"dia_fog",        "dancer":"diamond","deadline":4,"type":"financial",
     "text":"I need the fog machine. You know why.",
     "accept_note":"She sets it up herself. Immediately. It looks incredible.",
     "reject_note":"'I can't perform without ambiance.' She performs. It's not the same.",
     "accept":{"cash_cost":800,"atmosphere":20,"mood_self":25},"reject":{"mood_self":-20}},
    {"key":"dia_event_night","dancer":"diamond","deadline":3,"type":"scheduling",
     "text":"I've been offered a private event Saturday night. I need the night.",
     "accept_note":"She returns with cash and a story she's still telling.",
     "reject_note":"She books it anyway through 'a connection.' You find out Monday.",
     "accept":{"income_bonus":3000,"mood_self":15},"reject":{"mood_self":-20}},
    {"key":"dia_journalist", "dancer":"diamond","deadline":5,"type":"ego",
     "text":"A journalist wants to interview me about my journey. The studio should be featured.",
     "accept_note":"The article is beautiful. Three of the quotes are about her.",
     "reject_note":"She does the interview. Mentions the studio 'briefly.'",
     "accept":{"reputation":12,"members":6,"mood_self":20},"reject":{"reputation":4,"mood_self":-10}},
    {"key":"dia_aesthetic",  "dancer":"diamond","deadline":5,"type":"financial",
     "text":"The late-night aesthetic needs a complete rethink. New lighting, new music, new everything.",
     "accept_note":"Late-night class has a waitlist for the first time.",
     "reject_note":"'I'll make do.' Reviews for the late class get slightly worse.",
     "accept":{"cash_cost":1200,"income_bonus":400,"mood_self":25},"reject":{"mood_self":-15}},
    {"key":"dia_drapes",     "dancer":"diamond","deadline":5,"type":"financial",
     "text":"The entrance needs to feel different. Not bad. Just... different. Drapes, maybe. Something velvet.",
     "accept_note":"Three new clients mention the entrance in their first session.",
     "reject_note":"She hangs a scarf near her pole. It's not nothing.",
     "accept":{"cash_cost":600,"atmosphere":15,"reputation":5,"mood_self":20},"reject":{"mood_self":-12}},
    {"key":"dia_miami",      "dancer":"diamond","deadline":3,"type":"scheduling",
     "text":"I've been offered a performance in Miami. I need a long weekend.",
     "accept_note":"She returns with $1,500 in cash and a story she tells very selectively.",
     "reject_note":"She goes anyway. 'Back Monday.'",
     "accept":{"income_bonus":1500,"mood_self":40},"reject":{"mood_self":-25}},
    {"key":"dia_rename",     "dancer":"diamond","deadline":6,"type":"ego",
     "text":"I want to rename my late-night class. 'Midnight Ascension.' I have other options.",
     "accept_note":"Bookings for that class increase 10% immediately.",
     "reject_note":"Everyone calls it that anyway within two weeks.",
     "accept":{"reputation":5,"income_bonus":150,"mood_self":15},"reject":{"mood_self":-8}},
    {"key":"dia_soundbath",  "dancer":"diamond","deadline":4,"type":"values",
     "text":"There's an energy in the studio this week. Not good. We need a deep clean and a sound bath.",
     "accept_note":"The whole studio feels different. Lighter. Everyone notices.",
     "reject_note":"She burns incense near her pole. It's not up to code. You don't say anything.",
     "accept":{"cash_cost":200,"cleanliness":30,"atmosphere":10,"mood_all":5,"mood_self":12},"reject":{"mood_self":-12}},
    # ── GARY ──────────────────────────────────────────────────────────────────
    {"key":"gary_mug",       "dancer":"gary","deadline":99,"type":"values",
     "text":"Hey, is it okay if I bring my own mug? The paper cups bother me.",
     "accept_note":"The mug was already there. Gary brought it last week.",
     "reject_note":"The mug was already there. Gary brought it last week.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
    {"key":"gary_start_time","dancer":"gary","deadline":99,"type":"scheduling",
     "text":"Any chance Tuesday could start 10 minutes later? No rush.",
     "accept_note":"Gary arrives at the same time.",
     "reject_note":"Gary arrives at the same time.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
    {"key":"gary_music",     "dancer":"gary","deadline":99,"type":"values",
     "text":"Could the playlist have a little classic rock sometimes? Just a thought.",
     "accept_note":"Gary doesn't check if you did it.",
     "reject_note":"Gary doesn't check if you did it.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
    {"key":"gary_plant",     "dancer":"gary","deadline":99,"type":"values",
     "text":"Is it alright if I put a small plant on the windowsill near my pole?",
     "accept_note":"It's already there. Gary brought it on day one. He named it.",
     "reject_note":"It's already there. Gary brought it on day one. He named it.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
    {"key":"gary_jacket",    "dancer":"gary","deadline":99,"type":"values",
     "text":"Someone left a jacket in Tuesday class three weeks ago. Should I donate it?",
     "accept_note":"Gary nods. Done.",
     "reject_note":"Gary nods. Done.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
    {"key":"gary_raven",     "dancer":"gary","deadline":99,"type":"values",
     "text":"This might not be my place — but Raven seems stressed lately. Is she okay?",
     "accept_note":"Gary nods. There's nothing you can do with this information.",
     "reject_note":"Gary nods. There's nothing you can do with this information.",
     "accept":{"mood_self":0},"reject":{"mood_self":0}},
]

POLE_STUDIO_EVENTS = [
    {"text":"A chiropractor started recommending aerial fitness for core strength. Walk-ins tripled.",          "type":"positive","effect":"members",   "value": 6},
    {"text":"Your studio was cited in a 'Surprising Wellness Trends' piece. New memberships surged.",          "type":"positive","effect":"reputation","value":12},
    {"text":"The senior center booked a morning class. Zero complaints. Twelve new members.",                  "type":"positive","effect":"members",   "value": 8},
    {"text":"A corporate team booked the studio for a team-building session. HR called it 'transformative.'", "type":"positive","effect":"income",    "value":3000},
    {"text":"Someone's first-class TikTok hit 200k views. You didn't ask questions.",                         "type":"positive","effect":"members",   "value":10},
    {"text":"Physical therapy clinic sent over three patients for 'core rehabilitation.' They loved it.",      "type":"positive","effect":"members",   "value": 4},
    {"text":"Bachelorette party booked the whole studio for Saturday night. A very good Saturday.",           "type":"positive","effect":"income",    "value":4500},
    {"text":"A fitness magazine asked to run a small feature. You said yes.",                                 "type":"positive","effect":"reputation","value": 8},
    {"text":"Gary went viral on a local Facebook group. Membership inquiries up.",                            "type":"positive","effect":"members",   "value":10},
    {"text":"A local school asked about a youth program. Sunshine has already said yes on your behalf.",      "type":"positive","effect":"members",   "value": 5},
    {"text":"A pole bent mid-advanced-class. The instructor called it 'interpretive movement.' The ceiling fan did not survive.", "type":"negative","effect":"break_pole","value":1},
    {"text":"A news van parked outside for three hours. They left. You got 14 new members from the foot traffic.", "type":"positive","effect":"members","value":5},
    {"text":"A 1-star Yelp review: 'Expected something different.' Your regulars buried it in 5-stars.",      "type":"negative","effect":"reputation","value":-5},
    {"text":"Grip spray ran out mid-session. Everyone agreed it was the most character-building class yet.",  "type":"negative","effect":"atmosphere","value":-15},
    {"text":"Health inspector arrived unannounced. Passed with flying colors. He asked about beginner class.", "type":"positive","effect":"reputation","value":8},
    {"text":"Someone tracked mud through the studio during the 6pm class.",                                   "type":"negative","effect":"cleanliness","value":-20},
    {"text":"Chromatic Fitness is running a promotion. A few members checked it out.",                        "type":"negative","effect":"members",   "value":-5},
    {"text":"A fire alarm test mid-class cleared the building. No income that hour.",                         "type":"negative","effect":"income",    "value":-500},
    {"text":"City repaving outside — limited parking, foot traffic way down today.",                          "type":"negative","effect":"income",    "value":-600},
    {"text":"Raven won a regional championship. The trophy is now in the lobby.",                             "type":"positive","effect":"reputation","value":10},
]

POLE_STUDIO_UPGRADES = {
    "chrome_polish": {"name": "Chrome Polish Kit",  "icon": "✨", "cost": 2_000, "desc": "Cuts bend chance in half."},
    "led_halo":      {"name": "LED Halo Lighting",  "icon": "💡", "cost": 2_500, "desc": "+20% income from this pole."},
    "grip_coating":  {"name": "Grip Coating",        "icon": "💪", "cost": 1_500, "desc": "+10% income, grip spray lasts 10 days."},
}

POLE_STUDIO_STAFF = {
    "vibe_manager":   {"name": "Vibe Manager",   "icon": "🎶", "cost": 200, "desc": "Auto-maintains atmosphere above 75%."},
    "studio_cleaner": {"name": "Studio Cleaner", "icon": "🧹", "cost": 175, "desc": "Auto-cleans when cleanliness drops below 70%. Shows up early. Asks no questions."},
    "manager":        {"name": "Studio Manager", "icon": "📋", "cost": 225, "desc": "Auto-handles dancer demands, fills empty class slots, keeps the Kombucha Bar stocked, AND resolves studio events (bookings, inspections, drama) for you."},
    "host":           {"name": "Front Desk Host", "icon": "🛎️", "cost": 160, "desc": "Greets & checks members in — lifts satisfaction and cuts churn."},
    "bartender":      {"name": "Bartender",        "icon": "🍸", "cost": 170, "desc": "Works the Kombucha Bar. Without one, the bar sits dark and earns nothing."},
}

# ── REVAMP: a membership-driven "totally legit aerial-fitness studio" ──────────
# (a wink-wink parody). Core loop: grow members → schedule classes to match their
# demand → keep members & instructors happy → expand. No consumable fuel gate.
STUDIO_DUES_PER_MEMBER    = 3.0    # recurring $/member/day
STUDIO_VIP_DUES           = 14.0   # recurring $/VIP member/day
STUDIO_AVG_VISITS         = 0.5    # member-visits demanded per member per day
STUDIO_BASE_SLOTS         = 4      # configurable class slots at start (+ from facilities)
STUDIO_INSTR_ENERGY_COST  = 22     # energy a class burns from its instructor per day
STUDIO_INSTR_ENERGY_REGEN = 30     # energy recovered each day (so 1 class/day nets +8; 2+ drains)
STUDIO_GRATUITY_RATE      = 0.14   # tips as fraction of class income at full satisfaction (if enabled)

# Class types: each fills from member demand (popularity), seats it can hold, $/head,
# and the equipment it needs. `private` is the VIP "private dance" parody.
POLE_STUDIO_CLASSES = {
    "intro":   {"name": "Intro Pole",          "icon": "🌱", "seats": 14, "popularity": 1.4, "rev": 7,  "equip": "pole"},
    "levels":  {"name": "Pole Levels",         "icon": "🔥", "seats": 10, "popularity": 1.0, "rev": 11, "equip": "pole"},
    "silks":   {"name": "Aerial Silks",        "icon": "🎀", "seats": 8,  "popularity": 0.7, "rev": 16, "equip": "silks"},
    "flex":    {"name": "Flexibility & Stretch","icon": "🧘", "seats": 16, "popularity": 1.1, "rev": 6,  "equip": "floor"},
    "private": {"name": "Private Session",      "icon": "🥂", "seats": 2,  "popularity": 0.5, "rev": 70, "equip": "vip"},
    "open":    {"name": "Open Practice",        "icon": "🕒", "seats": 12, "popularity": 0.6, "rev": 5,  "equip": "floor"},
}
# Each instructor is the natural star of exactly one class type.
POLE_STUDIO_SPECIALTY_CLASS = {
    "sunshine": "intro", "celestia": "levels", "raven": "silks",
    "mercedes": "private", "diamond": "flex", "gary": "open",
}
POLE_STUDIO_SPECIALTY_FIT = 1.4   # teaching her specialty
POLE_STUDIO_OFFSPEC_FIT   = 0.75  # teaching outside her lane

# Facilities — one-time upgrades that add capacity / unlock class types / amenities.
POLE_STUDIO_FACILITIES = {
    "silks_rig":  {"name": "Aerial Silks Rig",  "icon": "🎀", "cost": 30_000, "desc": "Unlocks Aerial Silks classes.",            "unlock": "silks"},
    "vip_suite":  {"name": "VIP Suite",          "icon": "🥂", "cost": 55_000, "desc": "The 'Champagne Room.' Unlocks Private Sessions + VIP memberships.", "unlock": "vip"},
    "stage":      {"name": "Performance Stage",  "icon": "🎤", "cost": 40_000, "desc": "Host Theme & Showcase Nights for big one-off payouts.",            "feature": "stage"},
    "lobby":      {"name": "Comfy Lobby Lounge", "icon": "🛋️", "cost": 22_000, "desc": "+satisfaction & retention. People linger.",  "feature": "lobby"},
    "dj_booth":   {"name": "Resident DJ Booth",  "icon": "🪩", "cost": 26_000, "desc": "Mood lighting + sound. Big atmosphere boost.", "feature": "dj"},
    "kombucha_bar":{"name": "Kombucha Bar",      "icon": "🥂", "cost": 24_000, "desc": "The 'bar.' Stock kombucha from CostPro for extra income + satisfaction.", "feature": "bar"},
}
# Marketing campaign (active member growth).
STUDIO_MARKETING_COST = 2_500
STUDIO_MARKETING_REP  = 12
# Theme night (needs the stage) — a big one-off, on a cooldown.
STUDIO_THEME_COST     = 1_200
STUDIO_THEME_COOLDOWN = 5

# ── Events as choice cards (one may fire per advance, low chance) ──────────────
# Choice effect keys: cost (cash out), cash (cash in), members/reputation/
# atmosphere/cleanliness (0–100 deltas), mood_all (all hired dancers), break_pole,
# plus optional risk {chance, cost, break_pole, result_bad}.
POLE_STUDIO_EVENT_CHANCE = 0.11
POLE_STUDIO_EVENT_CARDS = [
    {"key": "magazine", "title": "Magazine Feature", "icon": "📸",
     "text": "A wellness magazine wants to feature the studio — if you comp them a free private session.", "choices": [
        {"label": "Comp the shoot", "cost": 0, "reputation": 14, "members": 6, "result": "The spread looks incredible — inquiries all week."},
        {"label": "Charge full price", "cost": 0, "cash": 400, "reputation": -3, "result": "They paid, but the feature got... smaller."},
        {"label": "Decline", "cost": 0, "result": "You pass. No harm done."}]},
    {"key": "corporate", "title": "Corporate Booking", "icon": "💼",
     "text": "A tech company wants a team-building session — full budget, lots of demands.", "choices": [
        {"label": "Full custom package", "cost": 300, "cash": 3800, "members": 4, "result": "HR called it 'transformative.' Big check."},
        {"label": "Standard group class", "cost": 0, "cash": 1500, "result": "Tidy, low-effort money."}]},
    {"key": "inspector", "title": "Surprise Inspection", "icon": "📋",
     "text": "A health inspector arrives unannounced, mid-class.", "choices": [
        {"label": "Give the full tour", "cost": 120, "reputation": 8, "cleanliness": 10, "result": "Passed clean — he signed up for beginner class."},
        {"label": "Rush him through", "cost": 0, "result": "He left satisfied.", "risk": {"chance": 0.4, "cost": 500, "result_bad": "He cited two issues — fines plus a re-inspection fee."}}]},
    {"key": "bachelorette", "title": "Bachelorette Party", "icon": "🎉",
     "text": "A loud, fun bachelorette party wants to book the whole studio Saturday night.", "choices": [
        {"label": "Book it out", "cost": 0, "cash": 4500, "cleanliness": -15, "result": "A very good Saturday. The floor needs a mop."},
        {"label": "Politely decline", "cost": 0, "result": "Not tonight. The regulars appreciate the calm."}]},
    {"key": "pole_bend", "title": "Equipment Scare", "icon": "🛠️",
     "text": "A pole groaned ominously during an advanced class.", "choices": [
        {"label": "Pull it for inspection", "cost": 250, "result": "Tightened and certified safe. Nobody got hurt."},
        {"label": "'It's fine, keep going'", "cost": 0, "result": "Class continued.", "risk": {"chance": 0.5, "break_pole": 1, "result_bad": "It bent mid-spin. The instructor called it 'interpretive movement.'"}}]},
    {"key": "influencer", "title": "Influencer Class", "icon": "🤳",
     "text": "A local influencer wants a free class in exchange for a post.", "choices": [
        {"label": "Comp the class", "cost": 0, "members": 10, "mood_all": -4, "result": "Her post hit 200k views. The dancers found her exhausting."},
        {"label": "Offer a discount", "cost": 0, "members": 4, "result": "A modest shoutout. Every bit helps."},
        {"label": "Decline", "cost": 0, "result": "Not interested in freebies-for-clout."}]},
    {"key": "rival", "title": "Rival Promo", "icon": "🥊",
     "text": "Chromatic Fitness down the street launched an aggressive promo.", "choices": [
        {"label": "Counter with your own deal", "cost": 600, "members": 8, "result": "You held the line and poached a few of theirs."},
        {"label": "Ride it out", "cost": 0, "members": -6, "result": "A few members drifted off to try the new place."}]},
    {"key": "recital", "title": "Student Showcase", "icon": "🏆",
     "text": "Your students want to put on a showcase for friends and family.", "choices": [
        {"label": "Fund the full production", "cost": 700, "reputation": 18, "members": 7, "mood_all": 6, "result": "A packed house — everyone's glowing, dancers included."},
        {"label": "Keep it small & free", "cost": 0, "reputation": 6, "mood_all": 3, "result": "A sweet little show in the studio."}]},
    {"key": "heatwave", "title": "Heat Wave", "icon": "🥵",
     "text": "The AC is struggling in a brutal heat wave. Classes are sweaty.", "choices": [
        {"label": "Rent a portable AC", "cost": 350, "result": "Cool and comfortable — classes stayed full."},
        {"label": "Tough it out", "cost": 0, "atmosphere": -18, "result": "'Character-building,' someone said. Attendance dipped."}]},
]

def _pole_queue_event(s):
    ps = s.get("pole_studio")
    if not (ps and ps.get("owned")):
        return None
    ev = random.choice(POLE_STUDIO_EVENT_CARDS)
    return {"key": ev["key"], "title": ev["title"], "icon": ev["icon"], "text": ev["text"],
            "choices": [{"label": c["label"], "cost": c.get("cost", 0), "gain": c.get("cash", 0)} for c in ev["choices"]]}

def _pole_apply_event_choice(s, choice):
    ps = s.get("pole_studio") or {}
    result, bad, extra_cost = choice.get("result", "Done."), False, 0
    risk = choice.get("risk")
    if risk and random.random() < risk.get("chance", 0):
        bad, extra_cost = True, risk.get("cost", 0)
        result = risk.get("result_bad", result)
        if risk.get("break_pole"):
            wp = [p for p in ps.get("poles", []) if not p.get("broken")]
            if wp: random.choice(wp)["broken"] = True
    cost = choice.get("cost", 0) + extra_cost
    if cost: s["cash"] = max(0, s["cash"] - cost)
    if choice.get("cash"): s["cash"] += choice["cash"]
    for k in ("members", "reputation", "atmosphere", "cleanliness"):
        if choice.get(k): ps[k] = max(0, min(100, ps.get(k, 0) + choice[k]))
    if choice.get("mood_all"):
        for dk, dd in ps.get("dancers", {}).items():
            if dd.get("hired") and dk != "gary":
                dd["mood"] = max(0, min(100, dd.get("mood", 72) + choice["mood_all"]))
    if choice.get("break_pole"):
        wp = [p for p in ps.get("poles", []) if not p.get("broken")]
        if wp: random.choice(wp)["broken"] = True
    return result, bad

def _pole_studio_dancer_state(key):
    d = POLE_STUDIO_DANCERS[key]
    return {"hired": False, "mood": d["mood_start"], "demands_fulfilled": 0, "salary_delta": 0,
            "class": POLE_STUDIO_SPECIALTY_CLASS.get(key, "open")}

def _apply_demand_effects(s, ps, effects, dancer_key):
    """Apply a demand's effect dict to state."""
    if effects.get("cash_cost"):
        s["cash"] = max(0, s["cash"] - effects["cash_cost"])
    if effects.get("salary_delta"):
        ps["dancers"][dancer_key]["salary_delta"] = \
            ps["dancers"][dancer_key].get("salary_delta", 0) + effects["salary_delta"]
    if effects.get("income_bonus"):
        s["cash"] += effects["income_bonus"]
    if effects.get("mood_self"):
        d = ps["dancers"].get(dancer_key, {})
        if dancer_key != "gary":
            d["mood"] = max(0, min(100, d.get("mood", 72) + effects["mood_self"]))
        ps["dancers"][dancer_key] = d
    if effects.get("mood_all"):
        for dk, dd in ps["dancers"].items():
            if dd.get("hired") and dk != "gary":
                dd["mood"] = max(0, min(100, dd.get("mood", 72) + effects["mood_all"]))
    if effects.get("members"):
        ps["members"] = max(0, min(100, ps.get("members", 0) + effects["members"]))
    if effects.get("reputation"):
        ps["reputation"] = max(0, min(100, ps.get("reputation", 0) + effects["reputation"]))
    if effects.get("atmosphere"):
        ps["atmosphere"] = max(0, min(100, ps.get("atmosphere", 0) + effects["atmosphere"]))
    if effects.get("cleanliness"):
        ps["cleanliness"] = max(0, min(100, ps.get("cleanliness", 0) + effects["cleanliness"]))

def _pole_manager_sweep_demands(s, ps):
    """Studio Manager auto-resolves every active dancer demand (accepts if affordable, else rejects).
    Returns the number handled. Called both before and after demand spawning so nothing ever leaks
    to the player while a manager is on staff."""
    handled = 0
    for dem in list(ps.get("active_demands", [])):
        spec = next((d for d in POLE_STUDIO_DEMANDS if d["key"] == dem["key"]), None)
        if not spec:
            continue
        dk  = spec["dancer"]
        eff = spec["accept"] if s["cash"] >= spec["accept"].get("cash_cost", 0) else spec["reject"]
        _apply_demand_effects(s, ps, eff, dk)
        if eff.get("quit") and ps["dancers"].get(dk, {}).get("hired"):
            ps["dancers"][dk]["hired"] = False
        ps.setdefault("fulfilled_demands", []).append(dem["key"])
        handled += 1
    ps["active_demands"] = []
    return handled

# ── Slippery When Washed Car Wash ─────────────────────────────────────────────
CAR_WASH_PRICE            = 600_000
CAR_WASH_UNLOCK_LEVEL     = 10
CAR_WASH_START_BAYS       = 1
CAR_WASH_MAX_BAYS         = 5
CAR_WASH_BAY_PRICES       = [100_000, 175_000, 275_000, 400_000]  # 4 additional bays
CAR_WASH_BASE_INCOME      = 220   # per bay per day before multipliers
CAR_WASH_WATER_DECAY      = 8
CAR_WASH_EQUIP_DECAY      = 6
CAR_WASH_MORALE_DECAY     = 5
CAR_WASH_BREAKDOWN_PCT    = 0.04
CAR_WASH_REPRESSURIZE_COST = 400
CAR_WASH_REPAIR_COST      = 250
CAR_WASH_PEP_ENERGY       = 3
CAR_WASH_PEP_MORALE       = 20
CAR_WASH_LUNCH_COST       = 400
CAR_WASH_LUNCH_MORALE     = 12
CAR_WASH_LUNCH_COOLDOWN   = 7
CAR_WASH_INSURANCE_WEEKLY = 600

# Package multipliers — highest available tier auto-applies
CAR_WASH_PACKAGES = {
    "basic":    {"name": "Basic Rinse",          "icon": "💦", "mult": 1.0,
                 "desc": "Just water. Gets the job done. Mostly."},
    "standard": {"name": "Standard Wash",         "icon": "🫧", "mult": 1.75,
                 "req_supply": "cw_standard_soap",
                 "desc": "Soap + rinse. The classic. Requires Standard Soap."},
    "deluxe":   {"name": "Deluxe Wax & Shine",   "icon": "✨", "mult": 3.0,
                 "req_supply": "cw_premium_wax", "req_upgrade": "dryer_arch",
                 "desc": "Soap + wax + rinse + dry. Requires Premium Wax and Dryer Arch."},
    "premium":  {"name": "Premium Full Detail",   "icon": "💎", "mult": 5.0,
                 "req_staff": "rhonda",
                 "desc": "The full treatment. Requires Rhonda. Worth the wait. Rhonda is slow."},
}

CAR_WASH_STAFF = {
    "terry": {
        "name": "Terry", "icon": "💧", "cost": 180,
        "desc": "Head Wash Technician. 22 years in the business. He considers himself an artist. "
                "He has opinions about water temperature. He will share them.",
        "effect": "morale_decay_half",
    },
    "brianna": {
        "name": "Brianna", "icon": "📋", "cost": 220,
        "desc": "Shift Manager. Produced a 47-step laminated flow chart for 'optimal wash sequencing.' "
                "It works. +20% bay output. Reduces morale decay.",
        "effect": "output_boost",
    },
    "squeegee_kid": {
        "name": "The Squeegee Kid", "icon": "🪟", "cost": 80,
        "desc": "Name unknown. Shows up 65% of days. On the days he shows up, he is excellent. "
                "He has three other jobs. They are all similar.",
        "effect": "show_up_chance",
    },
    "dave": {
        "name": "Dave", "icon": "🌀", "cost": 120,
        "desc": "The Vacuum Guy. Only does vacuums. Refuses any other task. "
                "47 five-star Yelp reviews. Dave does not know what Yelp is.",
        "effect": "vacuum_bonus",
    },
    "rhonda": {
        "name": "Rhonda", "icon": "✨", "cost": 250,
        "desc": "Detailer. Takes 3 hours per car. They look incredible. Rhonda is very slow. "
                "She knows. She is unbothered. Unlocks Premium Full Detail.",
        "effect": "unlock_premium",
    },
    "manny": {
        "name": "Manny", "icon": "🔧", "cost": 160,
        "desc": "On-site Repairman. Always has the right tool, usually in his back pocket. "
                "Restores +5 condition/day per bay, fixes broken bays overnight, AND keeps the water "
                "pressure pegged near 100 — no more sad trickle. He hums while he works.",
        "effect": "auto_repair",
    },
    "carlos": {
        "name": "Carlos", "icon": "📦", "cost": 150,
        "desc": "Supply Manager. Knows a guy for everything. Auto-orders soap & wax from CostPro, "
                "balanced to a buffer — you'll never run dry. Keeps receipts. So many receipts.",
        "effect": "auto_supply",
    },
    "diane": {
        "name": "Diane", "icon": "🗂️", "cost": 240,
        "desc": "General Manager. Handles every dispute, contract offer, and curveball before it reaches "
                "you — always picks the sensible option. Keeps a binder. The binder has tabs.",
        "effect": "auto_events",
    },
}

CAR_WASH_BAY_UPGRADES = {
    "nozzles":   {"name": "High-Pressure Nozzles", "icon": "🔩", "cost": 15_000,
                  "desc": "+25% income from this bay. Cuts equipment decay in half."},
    "foam":      {"name": "Foam Cannon",            "icon": "🫧", "cost": 12_000,
                  "desc": "+20% income from this bay. +10 reputation on install."},
    "led_sign":  {"name": "LED Arch Sign",          "icon": "💡", "cost": 18_000,
                  "desc": "+15% income from this bay. Boosts regulars growth rate."},
    "conveyor":  {"name": "Conveyor Belt",          "icon": "⚙️", "cost": 35_000,
                  "desc": "+30% income from this bay. Eliminates Squeegee Kid no-show penalty."},
}

CAR_WASH_GLOBAL_UPGRADES = {
    "waiting_room_tv":  {"name": "Waiting Room TV",      "icon": "📺", "cost":  8_000,
                         "desc": "Reduces regulars drain from long-wait events."},
    "loyalty_machine":  {"name": "Loyalty Card Machine", "icon": "💳", "cost": 12_000,
                         "desc": "Doubles regulars build rate."},
    "water_tank":       {"name": "Industrial Water Tank","icon": "🛢️", "cost": 25_000,
                         "desc": "Water pressure decays 60% slower."},
    "dryer_arch":       {"name": "Automated Dryer Arch", "icon": "🌬️", "cost": 30_000,
                         "desc": "Required to offer Deluxe Wax & Shine package."},
    "membership_kiosk": {"name": "Wash Club Kiosk",      "icon": "🎟️", "cost": 28_000,
                         "desc": "Launch the Unlimited Wash Club — recurring monthly members who come rain or shine."},
    "upsell_menu":      {"name": "Digital Upsell Menu",  "icon": "🖥️", "cost": 16_000,
                         "desc": "Bright menu boards + suggestive selling push more cars into pricier washes."},
}

# ── Weather: the heartbeat of a car wash. Drives daily demand. Biased by season. ──
CAR_WASH_WEATHER = {
    "clear":    {"name": "Clear & Dusty",  "icon": "☀️", "demand": 1.15, "desc": "Dust settling on every car. Steady business."},
    "dusty":    {"name": "Dry Dusty Spell", "icon": "🌵", "demand": 1.45, "desc": "Everything's filthy. The line's out the door."},
    "pollen":   {"name": "Pollen Storm",   "icon": "🌼", "demand": 1.55, "desc": "Yellow film on every windshield. Mayhem (the good kind)."},
    "hot":      {"name": "Hot & Hazy",     "icon": "🥵", "demand": 1.2,  "desc": "Bugs on the grille. Decent walk-in traffic."},
    "overcast": {"name": "Overcast",       "icon": "☁️", "demand": 0.9,  "desc": "Meh weather, meh crowds."},
    "rain":     {"name": "Rainy",          "icon": "🌧️", "demand": 0.4,  "desc": "Why wash it now? Walk-ins dry up."},
    "storm":    {"name": "Storm",          "icon": "⛈️", "demand": 0.25, "desc": "Nobody's coming. The regulars maybe."},
    "road_salt":{"name": "Road-Salt Season","icon": "❄️", "demand": 1.75, "desc": "Salt eats cars. Everyone's panicking. Jackpot."},
}
# Seasonal weather weights (season index 0=Spring,1=Summer,2=Fall,3=Winter).
CAR_WASH_WEATHER_WEIGHTS = {
    0: {"clear": 3, "pollen": 4, "rain": 3, "overcast": 2, "dusty": 2, "storm": 1},
    1: {"clear": 4, "hot": 4, "dusty": 3, "overcast": 2, "rain": 2, "storm": 1},
    2: {"clear": 4, "dusty": 3, "overcast": 3, "rain": 3, "pollen": 1},
    3: {"road_salt": 5, "overcast": 3, "clear": 2, "storm": 2, "rain": 2},
}
def _roll_car_wash_weather(season_idx):
    w = CAR_WASH_WEATHER_WEIGHTS.get(season_idx, CAR_WASH_WEATHER_WEIGHTS[0])
    pool = [k for k, n in w.items() for _ in range(n)]
    return random.choice(pool)

CAR_WASH_BAY_CAPACITY  = 22     # cars/day a bay can handle (throughput)
CAR_WASH_BASE_PER_CAR  = 11     # $/car before package tier & multipliers
CAR_WASH_BASE_DEMAND   = 30     # baseline cars/day at neutral weather, no regulars/members
CAR_WASH_MEMBER_DUES   = 6.0    # recurring $/member/day
CAR_WASH_MEMBER_VISITS = 0.7    # guaranteed car-visits per member per day (come rain or shine)

# Choice-card events (one may fire per advance at a low rate; player decides).
CAR_WASH_EVENT_CHANCE = 0.12
CAR_WASH_EVENT_CARDS = [
    {"key": "fleet", "title": "Fleet Contract Offer", "icon": "🚐",
     "text": "A delivery company wants a standing contract to wash their van fleet weekly.", "choices": [
        {"label": "Sign the contract", "cost": 0, "cash": 3000, "regulars": 6, "result": "Steady fleet money — and the vans are always filthy."},
        {"label": "Stay walk-in only", "cost": 0, "result": "You keep the bays open for the public."}]},
    {"key": "scratch", "title": "Scratch Complaint", "icon": "😠",
     "text": "A customer insists your wash scratched their (already scratched) bumper.", "choices": [
        {"label": "Comp them a free detail", "cost": 200, "reputation": 5, "result": "They left happy and posted a glowing review."},
        {"label": "Stand your ground", "cost": 0, "result": "You pull the footage and they back off.",
         "risk": {"chance": 0.4, "reputation": -10, "result_bad": "They blasted you online before you found the footage."}}]},
    {"key": "influencer_detail", "title": "Influencer's Supercar", "icon": "🏎️",
     "text": "A car influencer wants the full premium treatment filmed for their channel.", "choices": [
        {"label": "Roll out the red carpet", "cost": 150, "cash": 1200, "reputation": 12, "result": "The clip hit 300k views. Phones ringing all week."},
        {"label": "Treat it like any car", "cost": 0, "cash": 600, "result": "A solid wash, a modest tip, no fuss."}]},
    {"key": "water_bill", "title": "Surprise Water Bill", "icon": "💧",
     "text": "The city sent a 'usage adjustment.' It is not in your favor.", "choices": [
        {"label": "Just pay it", "cost": 700, "result": "Paid. The taps keep running."},
        {"label": "Dispute it", "cost": 0, "result": "They waived it after a long phone call.",
         "risk": {"chance": 0.45, "cost": 1100, "result_bad": "The meter was right — bigger bill plus a late fee."}}]},
    {"key": "heat_wave_rush", "title": "Bug-Splatter Rush", "icon": "🦟",
     "text": "A massive bug hatch has coated every windshield in town.", "choices": [
        {"label": "Run an all-hands bug special", "cost": 100, "cash": 2200, "morale": -6, "result": "Crushing day. The crew is wiped but the till is full."},
        {"label": "Business as usual", "cost": 0, "cash": 900, "result": "A nice bump without burning out the crew."}]},
    {"key": "competitor", "title": "Competitor Promo", "icon": "🥊",
     "text": "The wash across town launched a $5 'Grand Reopening' special.", "choices": [
        {"label": "Match it with a loyalty deal", "cost": 500, "regulars": 8, "result": "You held your regulars and poached a few of theirs."},
        {"label": "Compete on quality", "cost": 0, "reputation": 6, "regulars": -4, "result": "You lost a few price-shoppers but kept your name clean."}]},
    {"key": "charity", "title": "Charity Wash Day", "icon": "🎗️",
     "text": "The high school booster club wants to run a fundraiser car wash in your lot.", "choices": [
        {"label": "Host it for free", "cost": 0, "reputation": 14, "regulars": 5, "result": "Great publicity — the neighborhood loves you."},
        {"label": "Rent them the space", "cost": 0, "cash": 500, "result": "A tidy rental fee; the kids still had fun."},
        {"label": "Decline", "cost": 0, "result": "You keep the bays running for paying customers."}]},
    {"key": "equipment_recall", "title": "Equipment Recall", "icon": "🛠️",
     "text": "The maker of your wash arches issued a safety recall.", "choices": [
        {"label": "Schedule the fix", "cost": 400, "result": "All bays serviced and certified safe."},
        {"label": "Ignore it for now", "cost": 0, "result": "You keep washing.",
         "risk": {"chance": 0.5, "break_bay": 1, "result_bad": "An arch seized mid-wash — a bay's down."}}]},
]
def _car_wash_queue_event(s):
    cw = s.get("car_wash")
    if not (cw and cw.get("owned")):
        return None
    ev = random.choice(CAR_WASH_EVENT_CARDS)
    return {"key": ev["key"], "title": ev["title"], "icon": ev["icon"], "text": ev["text"],
            "choices": [{"label": c["label"], "cost": c.get("cost", 0), "gain": c.get("cash", 0)} for c in ev["choices"]]}

def _car_wash_apply_event_choice(s, choice):
    cw = s.get("car_wash") or {}
    result, bad, extra_cost = choice.get("result", "Done."), False, 0
    risk = choice.get("risk")
    if risk and random.random() < risk.get("chance", 0):
        bad, extra_cost = True, risk.get("cost", 0)
        result = risk.get("result_bad", result)
        if risk.get("reputation"): cw["reputation"] = max(0, min(100, cw.get("reputation", 0) + risk["reputation"]))
        if risk.get("break_bay"):
            wb = [b for b in cw.get("bays", []) if not b.get("broken")]
            if wb: random.choice(wb)["broken"] = True
    cost = choice.get("cost", 0) + extra_cost
    if cost: s["cash"] = max(0, s["cash"] - cost)
    if choice.get("cash"): s["cash"] += choice["cash"]
    for k in ("reputation", "regulars", "morale"):
        if choice.get(k): cw[k] = max(0, min(100, cw.get(k, 0) + choice[k]))
    if choice.get("break_bay"):
        wb = [b for b in cw.get("bays", []) if not b.get("broken")]
        if wb: random.choice(wb)["broken"] = True
    return result, bad

CAR_WASH_EVENTS = [
    {"text": "Bird migration season. Every car in town is a crime scene. Business is booming.",                       "type": "positive",  "effect": "income",     "value":  2000},
    {"text": "It rained last night. Walk-ins down. The regulars still showed.",                                       "type": "positive",  "effect": "regulars",   "value":     4},
    {"text": "The Squeegee Kid posted a video from your wash. 8,000 views. He didn't ask.",                           "type": "positive",  "effect": "reputation", "value":    12},
    {"text": "Dave won a local vacuum award. He accepted it with a nod. There was no speech.",                        "type": "positive",  "effect": "reputation", "value":     8},
    {"text": "Brianna's laminated flow chart was featured in an operations newsletter. Morale is up.",                "type": "positive",  "effect": "morale",     "value":    15},
    {"text": "A customer complained about a scratch that was already there. It was not.",                             "type": "negative",  "effect": "reputation", "value":    -8},
    {"text": "Local competitor opened nearby with a 'Grand Opening' discount.",                                       "type": "negative",  "effect": "regulars",   "value":    -5},
    {"text": "A luxury car came through. Rhonda handled it personally.",                                              "type": "positive",  "effect": "income",     "value":  3500},
    {"text": "Health inspector arrived unannounced. Passed with flying colors. She asked about the wax.",             "type": "positive",  "effect": "reputation", "value":     6},
    {"text": "Water main pressure drop city-wide. Extra maintenance needed.",                                         "type": "negative",  "effect": "water",      "value":   -20},
    {"text": "Equipment overheated during peak summer hours.",                                                        "type": "negative",  "effect": "equip",      "value":   -20},
    {"text": "The Squeegee Kid didn't show up.",                                                                      "type": "negative",  "effect": "income",     "value":  -400},
    {"text": "Someone tipped Terry $40. He used it to buy a thermometer for the rinse water.",                        "type": "positive",  "effect": "morale",     "value":    10},
    {"text": "A local school booked a field trip to see the operation. Eight new memberships followed.",              "type": "positive",  "effect": "regulars",   "value":     6},
    {"text": "City repaving outside — foot traffic down today.",                                                      "type": "negative",  "effect": "income",     "value":  -600},
    {"text": "Detailing package review went viral on a local Facebook group.",                                        "type": "positive",  "effect": "reputation", "value":    10},
    {"text": "A car came in that needed more than a wash. Rhonda did not comment. The car left spotless.",            "type": "positive",  "effect": "income",     "value":  2000},
    {"text": "Terry gave a 20-minute speech about the importance of rinse temperature. Morale dipped slightly.",      "type": "negative",  "effect": "morale",     "value":    -8},
    {"text": "Pump broke mid-shift.",                                                                                 "type": "negative",  "effect": "break_bay",  "value":     1},
    {"text": "Free car wash promotion at a dealership nearby. Walk-ins slowed.",                                      "type": "negative",  "effect": "regulars",   "value":    -4},
    {"text": "Dave's Yelp page got cited in a 'Hidden Gems' article. Regulars up.",                                   "type": "positive",  "effect": "regulars",   "value":     5},
    {"text": "Sudden hailstorm. Every car needs a wash afterwards.",                                                  "type": "positive",  "effect": "income",     "value":  4000},
    {"text": "A returning regular left a $100 tip. Brianna documented it in the flow chart.",                         "type": "positive",  "effect": "income",     "value":   100},
    {"text": "Power surge damaged equipment across all bays.",                                                        "type": "negative",  "effect": "equip_all",  "value":   -15},
]

# ── New Builds System ─────────────────────────────────────────────────────────
NEW_BUILDS_UNLOCK_LEVEL = 9
BUILDING_PERMIT_COST    = 100_000

HOOD_STREETS["Commerce Row"] = [
    "Commerce Blvd", "Trade St", "Market Row", "Industry Ave",
    "Enterprise Dr", "Capital Way", "Merchant Ln", "Exchange St",
    "Business Pkwy", "Commerce Park Dr",
]

HOOD_STREETS["Cedarvale Estates"] = [
    "Cedarvale Blvd", "Hearthstone Dr", "Millbrook Ln", "Stonegate Rd",
    "Ashford Way", "Cresthollow Ct", "Elmcroft Ave", "Fairlawn Dr",
    "Glenbrook Pl", "Harborview Cir",
]

# ── Commercial Properties ──────────────────────────────────────────────────────
COMMERCE_ROW_UNLOCK_LEVEL = 11

COMMERCIAL_TYPES = {
    "strip_mall": {
        "name": "Strip Mall", "icon": "🏪",
        "unit_count": 4, "price": 950_000, "overhead": 2_500, "sqft": 8_000,
        "superintendent_monthly": 3_500, "maintenance_monthly": 2_500, "emergency_repair_cost": 12_000,
        "desc": "Four retail-facing storefronts. High traffic, high turnover.",
    },
    "office_building": {
        "name": "Office Building", "icon": "🏢",
        "unit_count": 3, "price": 1_400_000, "overhead": 3_500, "sqft": 12_000,
        "superintendent_monthly": 4_500, "maintenance_monthly": 3_200, "emergency_repair_cost": 15_000,
        "desc": "Professional tenants, longer leases, quieter events.",
    },
    "mixed_use": {
        "name": "Mixed-Use Building", "icon": "🏬",
        "unit_count": 5, "price": 1_800_000, "overhead": 4_000, "sqft": 18_000,
        "superintendent_monthly": 5_500, "maintenance_monthly": 3_800, "emergency_repair_cost": 20_000,
        "desc": "Three commercial floors and two upper-level office suites.",
    },
}

COMMERCIAL_UPGRADES = {
    "security_system": {
        "name": "Security System", "icon": "🔒", "cost": 12_000,
        "desc": "Cuts inspection failures and sudden closures by 60%.",
    },
    "commercial_hvac": {
        "name": "Commercial HVAC", "icon": "❄️", "cost": 18_000,
        "desc": "35% less daily condition loss from tenant wear.",
    },
    "renovated_common": {
        "name": "Renovated Common Areas", "icon": "✨", "cost": 25_000,
        "desc": "All unit rents permanently +8%.",
    },
    "fiber_internet": {
        "name": "Fiber Internet", "icon": "📡", "cost": 9_000,
        "desc": "Law offices and accounting firms pay +$500/mo.",
    },
    "parking_expansion": {
        "name": "Parking Expansion", "icon": "🅿️", "cost": 20_000,
        "desc": "Reduces event rates for high-traffic tenants by 40%.",
    },
    "exterior_facelift": {
        "name": "Exterior Facelift", "icon": "🎨", "cost": 30_000,
        "desc": "+40 condition immediately. All units +$300/mo.",
    },
}

BUSINESS_TENANT_TYPES = {
    "restaurant": {
        "name": "Restaurant", "icon": "🍽️",
        "monthly_rent": 8_500, "lease_days": 112, "event_chance": 0.15,
        "desc": "High traffic. Great rent but inspection events are common.",
        "names": ["Brick & Smoke BBQ", "The Hungry Fork", "Mambo Kitchen", "Noodle House",
                  "Golden Spoon Diner", "Harbor Grill", "Casa Verde", "The Rustic Table"],
    },
    "retail": {
        "name": "Retail Shop", "icon": "🛍️",
        "monthly_rent": 5_500, "lease_days": 84, "event_chance": 0.08,
        "desc": "Short leases, decent income. Moderate turnover.",
        "names": ["QuickMart", "Corner Finds", "Daily Goods", "Bloom Boutique",
                  "The Gear Stop", "Sunrise Goods", "Main St Market", "Fifth Ave Finds"],
    },
    "law_office": {
        "name": "Law Office", "icon": "⚖️",
        "monthly_rent": 9_000, "lease_days": 224, "event_chance": 0.03,
        "desc": "Quiet, long-term, pays well. The dream tenant.",
        "names": ["Fletcher & Associates", "Caldwell Law Group", "Stone Legal",
                  "Harmon & Pierce LLC", "Vance Law", "Burke & Rowe Legal"],
    },
    "salon": {
        "name": "Salon", "icon": "💈",
        "monthly_rent": 6_000, "lease_days": 112, "event_chance": 0.08,
        "desc": "Steady income, reasonable events. Popular anchor tenant.",
        "names": ["Shear Bliss", "The Cut Above", "Platinum Cuts",
                  "Studio 9 Salon", "The Style Bar", "Velvet Scissors"],
    },
    "gym": {
        "name": "Gym", "icon": "🏋️",
        "monthly_rent": 11_000, "lease_days": 168, "event_chance": 0.12,
        "desc": "Highest rent, but equipment wear is no joke.",
        "names": ["Iron District", "Peak Fitness", "Grind Athletics",
                  "FitCore Gym", "Steel & Sweat", "Apex Performance"],
    },
    "coffee_shop": {
        "name": "Coffee Shop", "icon": "☕",
        "monthly_rent": 4_200, "lease_days": 84, "event_chance": 0.08,
        "desc": "Popular morning anchor. Steady foot traffic, low drama.",
        "names": ["Brew & Co.", "Morning Ritual", "The Daily Grind", "Roasted Roots",
                  "Copper Cup Cafe", "Sunrise Brew", "Vault Coffee", "Mellow Grounds"],
    },
    "barber_shop": {
        "name": "Barber Shop", "icon": "🪒",
        "monthly_rent": 3_500, "lease_days": 84, "event_chance": 0.07,
        "desc": "Low rent, low drama. Community staple.",
        "names": ["The Sharp Cut", "Clipper's Den", "Classic Cuts", "Fade Factory",
                  "Razor's Edge", "The Trim Shop", "Main St. Barber", "Old School Cuts"],
    },
    "nail_salon": {
        "name": "Nail Salon", "icon": "💅",
        "monthly_rent": 3_800, "lease_days": 84, "event_chance": 0.07,
        "desc": "Steady clientele. Reliable rent, minimal issues.",
        "names": ["Polished Nails", "Pink Tips Studio", "Luxe Nails", "Crystal Nails",
                  "The Nail Bar", "Pure Polish", "Gloss Studio", "Flawless Nails"],
    },
    "pawn_shop": {
        "name": "Pawn Shop", "icon": "🏷️",
        "monthly_rent": 4_800, "lease_days": 56, "event_chance": 0.14,
        "desc": "High-traffic, high-risk. Short leases, frequent events.",
        "names": ["Gold & Silver Exchange", "Quick Cash Co.", "ValueTown Pawn",
                  "City Pawn & Trade", "Relics & Goods", "The Trading Post"],
    },
    "tattoo_studio": {
        "name": "Tattoo Studio", "icon": "🎨",
        "monthly_rent": 5_200, "lease_days": 56, "event_chance": 0.16,
        "desc": "Creative energy. Shorter leases, busier than expected.",
        "names": ["Ink District", "Black & Grey Studio", "Sacred Skin Tattoo",
                  "The Parlor", "Iron Needle Ink", "Canvas & Needle"],
    },
    "auto_parts": {
        "name": "Auto Parts Store", "icon": "🔧",
        "monthly_rent": 6_800, "lease_days": 84, "event_chance": 0.10,
        "desc": "Industrial foot traffic. Decent rent, moderate wear.",
        "names": ["FastLane Parts", "Gear Up Auto", "City Auto Supply",
                  "ProDrive Parts", "The Parts Depot", "GridLock Auto"],
    },
    "daycare": {
        "name": "Daycare Center", "icon": "🧒",
        "monthly_rent": 6_200, "lease_days": 168, "event_chance": 0.10,
        "desc": "Long leases, community anchor. Inspections are standard.",
        "names": ["Bright Futures Daycare", "Little Sprouts", "Sunshine Kids Center",
                  "Tiny Steps Academy", "Rainbow Nest", "Growing Minds"],
    },
    "accounting_firm": {
        "name": "Accounting Firm", "icon": "📊",
        "monthly_rent": 8_000, "lease_days": 168, "event_chance": 0.03,
        "desc": "Professional and quiet. Long-term, low hassle.",
        "names": ["Ledger & Co.", "Summit Accounting", "Clear Books LLC",
                  "Apex Financial Group", "Harmon CPA", "Prestige Accounting"],
    },
    "pharmacy": {
        "name": "Pharmacy", "icon": "💊",
        "monthly_rent": 10_000, "lease_days": 112, "event_chance": 0.05,
        "desc": "High-demand essential business. Solid rent, very low drama.",
        "names": ["CityMed Pharmacy", "QuickRx", "Wellness Depot",
                  "TruCare Rx", "Neighborhood Pharmacy", "MedFast"],
    },
    "tech_startup": {
        "name": "Tech Startup", "icon": "💻",
        "monthly_rent": 9_500, "lease_days": 56, "event_chance": 0.18,
        "desc": "High rent but they pivot fast. Short leases, frequent events.",
        "names": ["Launchpad Labs", "Node & Co.", "Axle Tech",
                  "Pivot House", "ByteStarter", "Circuit Ventures"],
    },
    "medical_clinic": {
        "name": "Medical Clinic", "icon": "🏥",
        "monthly_rent": 12_500, "lease_days": 224, "event_chance": 0.04,
        "desc": "Top-tier rent, longest leases. Nearly zero trouble.",
        "names": ["CityHealth Clinic", "Meridian Medical", "Pinnacle Care",
                  "Lakeside Health", "ProMed Clinic", "Summit Healthcare"],
    },
    "dental_office": {
        "name": "Dental Office", "icon": "🦷",
        "monthly_rent": 11_000, "lease_days": 224, "event_chance": 0.02,
        "desc": "Ultra-reliable. Great rent, iron-clad leases.",
        "names": ["Bright Smiles Dental", "Apex Dental Group", "ClearBite Dentistry",
                  "Prestige Dental", "Summit Smiles", "ProDent Clinic"],
    },
    "flooring_express": {
        "name": "Flooring Express", "icon": "🏪",
        "monthly_rent": 20_000, "lease_days": 224, "event_chance": 0.0,
        "special": True,
        "desc": "⭐ SPECIAL — Pays double. Minimum 2-year lease. Never any issues.",
        "names": ["Flooring Express"],
    },
}

# ── Commercial overhaul: tenant mix, foot traffic, % rent, satisfaction, leasing agent ──
BUSINESS_TENANT_CAT = {
    "restaurant": "food", "coffee_shop": "food",
    "retail": "retail", "pawn_shop": "retail", "auto_parts": "retail", "flooring_express": "retail",
    "salon": "service", "barber_shop": "service", "nail_salon": "service", "tattoo_studio": "service",
    "law_office": "professional", "accounting_firm": "professional", "tech_startup": "professional",
    "gym": "health", "daycare": "health", "medical_clinic": "health",
    "dental_office": "health", "pharmacy": "health",
}
CAT_LABEL = {"food": "Food", "retail": "Retail", "service": "Service",
             "professional": "Professional", "health": "Health"}
# Anchor tenants pull in shared foot traffic that lifts every neighbor in the building.
BUSINESS_ANCHORS = {"restaurant", "coffee_shop", "gym", "pharmacy", "medical_clinic"}
# Monthly $ upside from percentage (sales) rent at 100 foot traffic. 0 = fixed-rent tenant.
BUSINESS_PCT_MAX = {
    "restaurant": 4_000, "coffee_shop": 2_200,
    "retail": 2_600, "pawn_shop": 1_800, "auto_parts": 1_600,
    "salon": 1_500, "barber_shop": 900, "nail_salon": 1_000, "tattoo_studio": 1_400,
    "gym": 2_500,
}
COMMERCIAL_LEASING_AGENT_FEE = 7_000  # monthly; auto-fills vacancies + handles routine events

def _commercial_foot_traffic(prop):
    """Building foot-traffic 0-100 from occupancy, anchors, tenant-mix diversity, condition, upgrades."""
    units = prop.get("units", [])
    total = len(units) or 1
    occ   = [u for u in units if u.get("business_type")]
    occ_rate = len(occ) / total
    cats, anchors = {}, 0
    for u in occ:
        bt = u["business_type"]
        c  = BUSINESS_TENANT_CAT.get(bt, "retail")
        cats[c] = cats.get(c, 0) + 1
        if bt in BUSINESS_ANCHORS:
            anchors += 1
    diversity = len(cats)
    dup_pen   = sum(max(0, n - 1) for n in cats.values())   # same-category cannibalization
    ft  = 30 + occ_rate * 28 + min(anchors, 3) * 7 + diversity * 4 - dup_pen * 5
    ft += (prop.get("condition", 80) / 100 - 0.7) * 12       # a well-kept building draws crowds
    up  = prop.get("upgrades", {})
    if up.get("exterior_facelift"):  ft += 6
    if up.get("renovated_common"):   ft += 5
    if up.get("parking_expansion"):  ft += 4
    return max(0, min(100, round(ft)))

def _agent_pick_tenant(prop):
    """Leasing Agent's pick: favor high rent, fresh categories, low-drama tenants. Returns biz key or None."""
    cat_counts = {}
    for u in prop.get("units", []):
        if u.get("business_type"):
            c = BUSINESS_TENANT_CAT.get(u["business_type"], "retail")
            cat_counts[c] = cat_counts.get(c, 0) + 1
    best, best_score = None, -1e9
    for bt, btd in BUSINESS_TENANT_TYPES.items():
        if btd.get("special"):
            continue
        c     = BUSINESS_TENANT_CAT.get(bt, "retail")
        score = btd["monthly_rent"] / 1000.0
        score -= cat_counts.get(c, 0) * 4               # avoid piling up one category
        if bt in BUSINESS_ANCHORS and cat_counts.get(c, 0) == 0:
            score += 5                                  # a fresh anchor is valuable
        score -= btd["event_chance"] * 10               # prefers reliable, low-drama tenants
        score += random.uniform(0, 3)                   # a little variety
        if score > best_score:
            best, best_score = bt, score
    return best

# ─────────────────────────────────────────────────────────────────────────────
# Commercial event engine — data-driven. Each event is "auto" (applies instantly)
# or "choice" (queued as a card the player resolves; the building's Superintendent
# auto-resolves it via the option flagged "default").
#
# effect dict keys (values are int or [lo,hi] ranges, rolled at fire time):
#   gain      cash in           cost      cash out (deductible if "deduct": True)
#   cond      condition delta   sat       satisfaction delta
#   rent_add  monthly_rent +=   rent_mult monthly_rent *= (float, not rolled)
#   vacate    True → tenant leaves
# Text templates may use {tenant}, {biz}, {cost}, {gain}, {cond}.
# ─────────────────────────────────────────────────────────────────────────────
from collections import defaultdict as _defaultdict

def _roll_eff_val(v):
    return random.randint(v[0], v[1]) if isinstance(v, (list, tuple)) else v

def _concrete_effect(eff):
    out = {}
    for k, v in (eff or {}).items():
        out[k] = v if k in ("deduct", "vacate", "rent_mult") else _roll_eff_val(v)
    return out

def _fmt_comm(tmpl, ctx):
    return (tmpl or "").format_map(_defaultdict(str, ctx))

def _eff_ctx(base, eff):
    ctx = dict(base)
    if eff.get("cost"): ctx["cost"] = f"${eff['cost']:,}"
    if eff.get("gain"): ctx["gain"] = f"${eff['gain']:,}"
    if "cond" in eff:   ctx["cond"] = str(abs(eff["cond"]))
    return ctx

def _apply_commercial_effect(s, prop, unit, eff):
    """Mutates state for one (already-rolled) effect dict."""
    if not eff:
        return
    if eff.get("gain"):
        s["cash"] += eff["gain"]
    if eff.get("cost"):
        s["cash"] = max(0, s["cash"] - eff["cost"])
        if eff.get("deduct"):
            _tax_deduct(s, eff["cost"])
    if eff.get("cond"):
        prop["condition"] = max(0, min(MAX_CONDITION, prop.get("condition", 0) + eff["cond"]))
    if unit:
        if eff.get("sat"):
            unit["satisfaction"] = max(0, min(100, unit.get("satisfaction", 70) + eff["sat"]))
        if eff.get("rent_add"):
            unit["monthly_rent"] = unit.get("monthly_rent", 0) + eff["rent_add"]
        if eff.get("rent_mult"):
            unit["monthly_rent"] = int(unit.get("monthly_rent", 0) * eff["rent_mult"])
        if eff.get("vacate"):
            unit["business_type"] = None; unit["tenant_name"] = None
            unit["lease_days_remaining"] = 0; unit["monthly_rent"] = 0
            unit["renewal_pending"] = False; unit["satisfaction"] = 70
            unit["pct_rent_monthly"] = 0

def _build_commercial_event(defn, prop, unit, btype, prop_label):
    """Roll a definition into a concrete event instance for this tenant."""
    base = {"tenant": unit.get("tenant_name", "The tenant"), "biz": btype["name"]}
    inst = {
        "id": defn["id"], "kind": defn.get("kind", "choice"),
        "icon": defn.get("icon", "🏢"), "etype": defn.get("etype", "info"),
        "prop_id": prop["id"], "unit_idx": unit["idx"],
        "biz_type": unit.get("business_type"), "biz_icon": btype["icon"],
        "tenant_name": base["tenant"], "prop_label": prop_label,
        "title": _fmt_comm(defn.get("title", ""), base),
        "desc":  _fmt_comm(defn.get("desc", ""), base),
    }
    if inst["kind"] == "auto":
        eff = _concrete_effect(defn.get("effect"))
        inst["auto_effect"] = eff
        inst["result"] = _fmt_comm(defn.get("result", defn.get("desc", "")), _eff_ctx(base, eff))
    else:
        inst["options"] = []
        for o in defn["options"]:
            eff = _concrete_effect(o.get("effect"))
            ctx = _eff_ctx(base, eff)
            inst["options"].append({
                "label":  _fmt_comm(o["label"], ctx),
                "result": _fmt_comm(o.get("result", ""), ctx),
                "effect": eff, "etype": o.get("etype", "info"),
                "default": o.get("default", False),
            })
    return inst

def _superintendent_resolve(s, prop, unit, inst, events, current_day):
    """Building's superintendent auto-picks the responsible (default) option."""
    opt = next((o for o in inst["options"] if o.get("default")), inst["options"][0])
    _apply_commercial_effect(s, prop, unit, opt["effect"])
    events.append({"prop": inst["prop_label"], "type": "info", "category": "commercial",
        "text": f"👷 Superintendent handled it — {opt['result']}"})
    s["log"].insert(0, {"day": current_day, "type": "info",
        "text": f"Superintendent resolved “{inst['title']}” at {inst['prop_label']}"})

# Events available to every commercial tenant
_GENERIC_COMM_EVENTS = [
    {"id": "boom_season", "kind": "auto", "icon": "💰", "etype": "positive", "weight": 3,
     "result": "{tenant} had a banner month — bonus {gain}!", "effect": {"gain": [2_000, 5_000], "sat": 3}},
    {"id": "community_award", "kind": "auto", "icon": "🏆", "etype": "positive", "weight": 2,
     "result": "{tenant} won a community award — {gain} in extra foot traffic!", "effect": {"gain": [1_500, 3_500], "sat": 2}},
    {"id": "great_review", "kind": "auto", "icon": "⭐", "etype": "positive", "weight": 2,
     "result": "{tenant} got a glowing local review — happier tenant, {gain} bump.", "effect": {"gain": [500, 1_800], "sat": 5}},
    {"id": "utility_spike", "kind": "auto", "icon": "⚡", "etype": "warning", "weight": 3,
     "result": "Utility spike hit {tenant}'s unit — emergency cost {cost}.", "effect": {"cost": [1_500, 4_000], "deduct": True}},
    {"id": "inspection_fail", "kind": "choice", "icon": "🚨", "etype": "warning", "weight": 3,
     "title": "Inspection Failed", "desc": "{biz} {tenant} flunked a surprise health & safety inspection. Cover the repairs or they shut down.",
     "options": [
        {"label": "Pay {cost} for repairs", "result": "Violations fixed — {tenant} passed re-inspection and stays.",
         "effect": {"cost": [3_000, 8_000], "deduct": True}, "default": True},
        {"label": "Refuse — let them deal with it", "result": "{tenant} couldn't reopen and walked out.",
         "effect": {"vacate": True}, "etype": "warning"},
     ]},
    {"id": "sublet_request", "kind": "choice", "icon": "🤝", "etype": "info", "weight": 2,
     "title": "Sublet Request", "desc": "{tenant} wants to sublet part of their space to a partner business.",
     "options": [
        {"label": "Approve — rent +{gain}/mo", "result": "Sublet approved — rent up {gain}/mo.",
         "effect": {"rent_add": [300, 800]}, "default": True},
        {"label": "Deny the sublet", "result": "Sublet denied — {tenant} grumbles a bit.",
         "effect": {"sat": -3}},
     ]},
    {"id": "rent_negotiation", "kind": "choice", "icon": "💬", "etype": "info", "weight": 2,
     "title": "Rent Negotiation", "desc": "{tenant} says business is slow and asks for a 15% rent cut.",
     "options": [
        {"label": "Accept the lower rent", "result": "Rent reduced to keep {tenant} happy.",
         "effect": {"rent_mult": 0.85, "sat": 6}, "default": True},
        {"label": "Hold firm on rent", "result": "You held firm — {tenant} stays but isn't thrilled.",
         "effect": {"sat": -8}},
     ]},
    {"id": "early_exit", "kind": "choice", "icon": "🚪", "etype": "warning", "weight": 1,
     "title": "Early Exit Request", "desc": "{tenant} wants to break their lease early. Either way they're leaving.",
     "options": [
        {"label": "Charge the {gain} exit fee", "result": "Collected a {gain} exit fee; the unit is now vacant.",
         "effect": {"gain": [4_000, 8_000], "vacate": True}, "default": True},
        {"label": "Waive the fee", "result": "Let {tenant} go without a fee — unit vacant.",
         "effect": {"vacate": True}},
     ]},
    {"id": "equipment_damage", "kind": "choice", "icon": "🔨", "etype": "warning", "weight": 2,
     "title": "Equipment Damage", "desc": "{tenant} reported damage to shared building equipment.",
     "options": [
        {"label": "Pay {cost} to repair", "result": "Equipment repaired — {cost} spent.",
         "effect": {"cost": [2_500, 6_000], "deduct": True}, "default": True},
        {"label": "Leave it for now", "result": "Left unrepaired — building condition took a hit.",
         "effect": {"cond": -20, "sat": -5}},
     ]},
    {"id": "pipe_burst", "kind": "choice", "icon": "🚿", "etype": "warning", "weight": 2,
     "title": "Burst Pipe", "desc": "A pipe burst overnight near {tenant}'s unit.",
     "options": [
        {"label": "Call an emergency plumber ({cost})", "result": "Plumber patched it fast — {cost} spent.",
         "effect": {"cost": [2_000, 5_000], "deduct": True}, "default": True},
        {"label": "Patch it cheaply yourself", "result": "Your DIY patch held… mostly. Condition slipped.",
         "effect": {"cond": -12, "sat": -4}},
     ]},
    {"id": "noise_complaint", "kind": "choice", "icon": "📢", "etype": "info", "weight": 2,
     "title": "Noise Complaint", "desc": "Neighboring tenants are complaining about noise from {tenant}.",
     "options": [
        {"label": "Mediate & soundproof ({cost})", "result": "You mediated and added soundproofing — peace restored.",
         "effect": {"cost": [800, 2_500], "deduct": True, "sat": 4}, "default": True},
        {"label": "Ignore it", "result": "You ignored it — tensions simmer.",
         "effect": {"sat": -6}},
     ]},
    {"id": "vandalism", "kind": "choice", "icon": "🪟", "etype": "warning", "weight": 2,
     "title": "Vandalism", "desc": "Vandals hit the storefront overnight.",
     "options": [
        {"label": "Repair & add cameras ({cost})", "result": "Repaired the damage and added cameras.",
         "effect": {"cost": [1_500, 4_500], "deduct": True}, "default": True},
        {"label": "Just board it up", "result": "Boarded it up cheap — condition dropped.",
         "effect": {"cond": -10, "sat": -3}},
     ]},
]

# Business-type-specific events (layered on top of the generic pool)
BUSINESS_EVENTS = {
    "restaurant": [
        {"id": "grease_fire", "kind": "choice", "icon": "🔥", "etype": "warning", "weight": 3,
         "title": "Kitchen Grease Fire", "desc": "A grease fire scorched {tenant}'s kitchen line.",
         "options": [
            {"label": "Fund the cleanup ({cost})", "result": "Kitchen restored — {tenant} reopens.",
             "effect": {"cost": [3_000, 7_000], "deduct": True}, "default": True},
            {"label": "Make them handle it", "result": "{tenant} closed for repairs and lost faith.",
             "effect": {"cond": -10, "sat": -10}}]},
        {"id": "food_critic", "kind": "auto", "icon": "🍽️", "etype": "positive", "weight": 2,
         "result": "A food critic raved about {tenant} — packed house, {gain} in the till!",
         "effect": {"gain": [2_000, 4_500], "sat": 6}},
    ],
    "coffee_shop": [
        {"id": "espresso_down", "kind": "choice", "icon": "☕", "etype": "warning", "weight": 3,
         "title": "Espresso Machine Down", "desc": "{tenant}'s espresso machine died mid-rush.",
         "options": [
            {"label": "Comp a new machine ({cost})", "result": "New machine humming — lattes flowing again.",
             "effect": {"cost": [1_800, 4_000], "deduct": True, "sat": 4}, "default": True},
            {"label": "Tell them it's their problem", "result": "{tenant} fumed through a drip-coffee week.",
             "effect": {"sat": -7}}]},
        {"id": "latte_viral", "kind": "auto", "icon": "📸", "etype": "positive", "weight": 2,
         "result": "{tenant}'s latte art went viral — lines out the door, {gain}!",
         "effect": {"gain": [1_200, 3_000], "sat": 5}},
    ],
    "retail": [
        {"id": "shoplift_ring", "kind": "choice", "icon": "🕵️", "etype": "warning", "weight": 3,
         "title": "Shoplifting Ring", "desc": "An organized shoplifting ring is hitting {tenant} hard.",
         "options": [
            {"label": "Install loss-prevention ({cost})", "result": "Security tightened — losses stopped.",
             "effect": {"cost": [2_000, 5_000], "deduct": True}, "default": True},
            {"label": "Let them eat the losses", "result": "{tenant} ate the losses and isn't happy.",
             "effect": {"sat": -8}}]},
        {"id": "sale_day", "kind": "auto", "icon": "🛍️", "etype": "positive", "weight": 2,
         "result": "{tenant}'s clearance event packed the store — {gain}!",
         "effect": {"gain": [1_000, 2_800], "sat": 3}},
    ],
    "gym": [
        {"id": "injury_claim", "kind": "choice", "icon": "🩹", "etype": "warning", "weight": 3,
         "title": "Equipment Injury Claim", "desc": "A member hurt themselves on {tenant}'s aging equipment and is threatening to sue.",
         "options": [
            {"label": "Settle & re-pad the gear ({cost})", "result": "Settled quietly and upgraded the equipment.",
             "effect": {"cost": [3_000, 8_000], "deduct": True}, "default": True},
            {"label": "Fight the claim", "result": "Legal drama dragged on — reputation dinged.",
             "effect": {"sat": -9, "cond": -5}}]},
        {"id": "new_year_rush", "kind": "auto", "icon": "🏋️", "etype": "positive", "weight": 2,
         "result": "New-Year resolution rush packed {tenant} — memberships surged, {gain}!",
         "effect": {"gain": [2_500, 5_500], "sat": 5}},
    ],
    "law_office": [
        {"id": "big_case", "kind": "auto", "icon": "⚖️", "etype": "positive", "weight": 2,
         "result": "{tenant} won a high-profile case — prestige and a {gain} referral bonus to the building.",
         "effect": {"gain": [3_000, 7_000], "sat": 4}},
        {"id": "data_leak", "kind": "choice", "icon": "🔐", "etype": "warning", "weight": 2,
         "title": "Confidential Leak", "desc": "{tenant} fears a client-file leak from the building's network.",
         "options": [
            {"label": "Upgrade building security ({cost})", "result": "Security hardened — crisis averted.",
             "effect": {"cost": [2_500, 6_000], "deduct": True, "sat": 3}, "default": True},
            {"label": "Downplay it", "result": "{tenant} lost trust in the building.",
             "effect": {"sat": -10}}]},
    ],
    "salon": [
        {"id": "celeb_client", "kind": "auto", "icon": "💃", "etype": "positive", "weight": 2,
         "result": "A celebrity got styled at {tenant} — buzz and {gain}!", "effect": {"gain": [1_500, 3_500], "sat": 6}},
        {"id": "dye_spill", "kind": "choice", "icon": "🎨", "etype": "warning", "weight": 2,
         "title": "Hair Dye Disaster", "desc": "{tenant} spilled industrial hair dye across the floor.",
         "options": [
            {"label": "Refinish the floor ({cost})", "result": "Floor refinished — good as new.",
             "effect": {"cost": [1_200, 3_000], "deduct": True}, "default": True},
            {"label": "Leave the stain", "result": "A purple floor stain remains. Classy.",
             "effect": {"cond": -8, "sat": -3}}]},
    ],
    "barber_shop": [
        {"id": "barber_legend", "kind": "auto", "icon": "💈", "etype": "positive", "weight": 2,
         "result": "{tenant} became the neighborhood's go-to fade — steady crowd, {gain}.",
         "effect": {"gain": [600, 1_800], "sat": 4}},
    ],
    "nail_salon": [
        {"id": "fume_complaint", "kind": "choice", "icon": "💅", "etype": "warning", "weight": 2,
         "title": "Ventilation Complaint", "desc": "Neighbors complain about acetone fumes from {tenant}.",
         "options": [
            {"label": "Install ventilation ({cost})", "result": "New venting cleared the air.",
             "effect": {"cost": [1_500, 3_500], "deduct": True, "sat": 4}, "default": True},
            {"label": "Crack a window and hope", "result": "The smell lingers; neighbors are annoyed.",
             "effect": {"sat": -6}}]},
    ],
    "pawn_shop": [
        {"id": "stolen_goods", "kind": "choice", "icon": "🚓", "etype": "warning", "weight": 3,
         "title": "Police Inquiry", "desc": "Police believe stolen goods passed through {tenant}.",
         "options": [
            {"label": "Cooperate & audit inventory ({cost})", "result": "Full cooperation cleared {tenant}'s name.",
             "effect": {"cost": [1_000, 3_000], "deduct": True}, "default": True},
            {"label": "Stonewall the police", "result": "The standoff scared off customers.",
             "effect": {"sat": -8}}]},
        {"id": "rare_find", "kind": "auto", "icon": "💎", "etype": "positive", "weight": 2,
         "result": "{tenant} flipped a rare find for a fortune — {gain} windfall!",
         "effect": {"gain": [1_500, 4_000], "sat": 4}},
    ],
    "tattoo_studio": [
        {"id": "viral_tattoo", "kind": "auto", "icon": "🎨", "etype": "positive", "weight": 2,
         "result": "A {tenant} piece went viral — booked solid for months, {gain}!",
         "effect": {"gain": [1_200, 3_200], "sat": 6}},
        {"id": "ink_spill", "kind": "choice", "icon": "🖤", "etype": "warning", "weight": 2,
         "title": "Ink Catastrophe", "desc": "A gallon of black ink soaked {tenant}'s floor.",
         "options": [
            {"label": "Replace the flooring ({cost})", "result": "New floor down — spotless again.",
             "effect": {"cost": [1_500, 3_500], "deduct": True}, "default": True},
            {"label": "Embrace the 'art'", "result": "The permanent ink stain stays. Edgy.",
             "effect": {"cond": -9}}]},
    ],
    "auto_parts": [
        {"id": "forklift_oops", "kind": "choice", "icon": "🚜", "etype": "warning", "weight": 2,
         "title": "Forklift Mishap", "desc": "{tenant}'s forklift punched a hole in the loading-dock wall.",
         "options": [
            {"label": "Repair the dock ({cost})", "result": "Dock wall rebuilt — operations resume.",
             "effect": {"cost": [2_000, 4_500], "deduct": True}, "default": True},
            {"label": "Tape it off for now", "result": "A taped-off hole isn't a great look.",
             "effect": {"cond": -10}}]},
        {"id": "fleet_order", "kind": "auto", "icon": "🔧", "etype": "positive", "weight": 2,
         "result": "{tenant} landed a big fleet contract — {gain} bonus!", "effect": {"gain": [1_500, 3_500], "sat": 4}},
    ],
    "daycare": [
        {"id": "licensing", "kind": "choice", "icon": "🧸", "etype": "warning", "weight": 2,
         "title": "Licensing Inspection", "desc": "{tenant} needs safety upgrades to pass state childcare licensing.",
         "options": [
            {"label": "Fund safety upgrades ({cost})", "result": "Upgrades done — license renewed.",
             "effect": {"cost": [2_000, 5_000], "deduct": True, "sat": 4}, "default": True},
            {"label": "Skip it", "result": "{tenant} barely scraped by and is stressed.",
             "effect": {"sat": -9}}]},
        {"id": "cute_viral", "kind": "auto", "icon": "🧒", "etype": "positive", "weight": 2,
         "result": "An adorable {tenant} moment went viral — waitlist full, {gain}!",
         "effect": {"gain": [800, 2_200], "sat": 5}},
    ],
    "accounting_firm": [
        {"id": "tax_surge", "kind": "auto", "icon": "📊", "etype": "positive", "weight": 2,
         "result": "Tax season swamped {tenant} (in a good way) — {gain} in overflow business.",
         "effect": {"gain": [2_000, 4_500], "sat": 3}},
        {"id": "audit_scare", "kind": "choice", "icon": "📋", "etype": "info", "weight": 1,
         "title": "Building Records Audit", "desc": "{tenant} asks you to produce building compliance records for an audit.",
         "options": [
            {"label": "Hire a clerk to compile them ({cost})", "result": "Records produced — audit passed clean.",
             "effect": {"cost": [800, 2_000], "deduct": True}, "default": True},
            {"label": "Hand over a shoebox of receipts", "result": "{tenant} was not amused.",
             "effect": {"sat": -5}}]},
    ],
    "pharmacy": [
        {"id": "flu_rush", "kind": "auto", "icon": "💊", "etype": "positive", "weight": 2,
         "result": "Flu season drove a vaccine rush at {tenant} — {gain}!", "effect": {"gain": [1_800, 4_000], "sat": 4}},
        {"id": "controlled_audit", "kind": "choice", "icon": "🔏", "etype": "warning", "weight": 2,
         "title": "Controlled-Substance Audit", "desc": "{tenant} needs a secure storage upgrade to pass a DEA audit.",
         "options": [
            {"label": "Install a secure vault ({cost})", "result": "Vault installed — audit passed.",
             "effect": {"cost": [3_000, 6_500], "deduct": True, "sat": 3}, "default": True},
            {"label": "Let them improvise", "result": "{tenant} sweated through the audit.",
             "effect": {"sat": -8}}]},
    ],
    "tech_startup": [
        {"id": "funding_round", "kind": "auto", "icon": "🚀", "etype": "positive", "weight": 3,
         "result": "{tenant} closed a funding round — they prepaid rent, {gain} to you!",
         "effect": {"gain": [3_000, 8_000], "sat": 6}},
        {"id": "server_meltdown", "kind": "choice", "icon": "💻", "etype": "warning", "weight": 2,
         "title": "Server Room Meltdown", "desc": "{tenant}'s server room overheated and tripped the building power.",
         "options": [
            {"label": "Upgrade cooling & wiring ({cost})", "result": "Cooling upgraded — servers stable.",
             "effect": {"cost": [3_500, 7_000], "deduct": True}, "default": True},
            {"label": "Run an extension cord", "result": "A jury-rigged fix strained the building.",
             "effect": {"cond": -12, "sat": -6}}]},
        {"id": "pivot", "kind": "choice", "icon": "🔄", "etype": "warning", "weight": 1,
         "title": "Sudden Pivot", "desc": "{tenant} is pivoting business models and may relocate.",
         "options": [
            {"label": "Offer a flexible lease tweak", "result": "A flexible deal kept {tenant} in the building.",
             "effect": {"rent_mult": 0.92, "sat": 8}, "default": True},
            {"label": "Hold them to the lease", "result": "{tenant} stayed, but resentfully.",
             "effect": {"sat": -10}}]},
    ],
    "medical_clinic": [
        {"id": "insurance_windfall", "kind": "auto", "icon": "🏥", "etype": "positive", "weight": 2,
         "result": "{tenant} cleared a big insurance backlog — {gain} referral to the building.",
         "effect": {"gain": [2_500, 6_000], "sat": 3}},
        {"id": "biohazard", "kind": "choice", "icon": "☣️", "etype": "warning", "weight": 2,
         "title": "Biohazard Incident", "desc": "A medical-waste mishap at {tenant} needs professional remediation.",
         "options": [
            {"label": "Hire certified cleanup ({cost})", "result": "Hazmat handled it — all clear.",
             "effect": {"cost": [3_000, 7_000], "deduct": True}, "default": True},
            {"label": "Mop it up yourself", "result": "Cutting corners on biohazard? Condition and trust dropped.",
             "effect": {"cond": -15, "sat": -8}}]},
    ],
    "dental_office": [
        {"id": "smile_feature", "kind": "auto", "icon": "🦷", "etype": "positive", "weight": 2,
         "result": "{tenant} was featured in a 'best smiles' roundup — new patients, {gain}!",
         "effect": {"gain": [1_500, 3_500], "sat": 4}},
        {"id": "water_line", "kind": "choice", "icon": "🚰", "etype": "warning", "weight": 2,
         "title": "Water Line Contamination", "desc": "{tenant}'s dental water lines failed a safety test.",
         "options": [
            {"label": "Replace the lines ({cost})", "result": "New lines installed — {tenant} reopened safely.",
             "effect": {"cost": [2_000, 4_500], "deduct": True}, "default": True},
            {"label": "Flush and hope", "result": "A risky shortcut left {tenant} uneasy.",
             "effect": {"sat": -7}}]},
    ],
    # ⭐ Flooring Express — the special tenant. A flooring company that installs flooring.
    # Their events are funny and lean positive (they keep "fixing" your floors).
    "flooring_express": [
        {"id": "fe_lobby_glowup", "kind": "auto", "icon": "✨", "etype": "positive", "weight": 3,
         "result": "Flooring Express re-tiled the whole lobby overnight 'as a sample.' The building looks incredible. (+{cond} condition)",
         "effect": {"cond": [10, 18]}},
        {"id": "fe_moonwalk", "kind": "auto", "icon": "🕺", "etype": "info", "weight": 2,
         "result": "Their new floor was so glossy a customer moonwalked straight into a wall. No injuries, huge laughs, slight scuff.",
         "effect": {"cond": -2}},
        {"id": "fe_floortok", "kind": "auto", "icon": "📱", "etype": "positive", "weight": 2,
         "result": "Flooring Express's showroom blew up on FloorTok (#satisfyinggrout). Foot traffic everywhere — {gain}!",
         "effect": {"gain": [2_000, 4_500], "sat": 5}},
        {"id": "fe_plaque", "kind": "choice", "icon": "🏅", "etype": "info", "weight": 2,
         "title": "A Heartfelt Request", "desc": "Flooring Express surprise-installed premium hardwood in your hallway for free — and would just love a small commemorative plaque honoring 'the day the floors got good.'",
         "options": [
            {"label": "Buy them the plaque ({cost})", "result": "They wept. The plaque is bronze. The floors are immaculate.",
             "effect": {"cost": [400, 900], "deduct": True, "cond": 6, "sat": 6}, "default": True},
            {"label": "Politely decline the plaque", "result": "They understood… but you caught the head installer sighing at the floor.",
             "effect": {"sat": -5}}]},
        {"id": "fe_floor_feud", "kind": "choice", "icon": "🥚", "etype": "warning", "weight": 2,
         "title": "Flooring Feud", "desc": "A rival flooring outfit egged Flooring Express's windows after a heated 'best underlayment' debate.",
         "options": [
            {"label": "Pay for cleanup & repaint ({cost})", "result": "Windows sparkling again. Flooring Express vows revenge (via superior grout).",
             "effect": {"cost": [500, 1_500], "deduct": True}, "default": True},
            {"label": "Let them settle it themselves", "result": "They counter-egged. It escalated. The sidewalk is a mess.",
             "effect": {"cond": -6}}]},
        {"id": "fe_overzealous", "kind": "auto", "icon": "🧰", "etype": "positive", "weight": 1,
         "result": "Flooring Express got bored and 'upgraded' the floors in two of your other units too. You didn't ask. You're not mad. (+{cond} condition)",
         "effect": {"cond": [6, 12]}},
    ],
}

COMMERCIAL_EVENT_RATE = 10.0  # global multiplier — events should be a regular, visible part of play

def _commercial_event_chance(btype_key, btype):
    """Per-tenant seasonal event chance. Flooring Express has no base chance of its own."""
    base = 0.16 if btype_key == "flooring_express" else btype.get("event_chance", 0.0)
    return base * COMMERCIAL_EVENT_RATE

def _gen_commercial_market(start_id):
    listings, nid = [], start_id
    types = list(COMMERCIAL_TYPES.keys())
    for t_key in random.sample(types, min(len(types), random.randint(2, 3))):
        ctype  = COMMERCIAL_TYPES[t_key]
        street = random.choice(HOOD_STREETS["Commerce Row"])
        addr   = f"{random.randint(10, 99) * 100 + random.randint(1, 99)} {street}"
        units  = [{"idx": i, "business_type": None, "tenant_name": None,
                   "lease_days_remaining": 0, "monthly_rent": 0, "renewal_pending": False,
                   "satisfaction": 70, "pct_rent_monthly": 0}
                  for i in range(ctype["unit_count"])]
        listings.append({
            "id":               nid,
            "commercial":       True,
            "type":             t_key,
            "neighborhood":     "Commerce Row",
            "address":          addr,
            "condition":        random.randint(80, 100),
            "purchase_price":   ctype["price"],
            "overhead_monthly": ctype["overhead"],
            "sqft":             ctype["sqft"],
            "units":            units,
            "upgrades":         {},
            "superintendent":   False,
            "maintenance":      False,
            "pending_reno":     None,
            "purchase_day":     None,
        })
        nid += 1
    return listings, nid

BUILD_CREWS = {
    "handys":   {"name": "Handy's Crew",      "icon": "🔨", "buy_cost":  15_000, "daily_rate":  400, "speed_mult": 1.00, "desc": "Small local crew. Reliable, affordable. Best value on small builds."},
    "summit":   {"name": "Summit Builders",   "icon": "🏗️", "buy_cost":  35_000, "daily_rate":  700, "speed_mult": 0.85, "desc": "Mid-size team with solid references. 15% faster than Handy's."},
    "apex":     {"name": "Apex Construction", "icon": "⚙️", "buy_cost":  75_000, "daily_rate": 1200, "speed_mult": 0.70, "desc": "Professional outfit. 30% faster. Worth it on larger projects."},
    "pinnacle": {"name": "Pinnacle Group",    "icon": "🏆", "buy_cost": 150_000, "daily_rate": 2000, "speed_mult": 0.55, "desc": "Elite construction firm. Nearly twice the speed. Premium price."},
}

NEW_BUILD_SIZES = {
    "studio":    {"name": "Studio Cottage",   "icon": "🏠", "base_days":  84, "build_cost":  80_000, "finished_value":  300_000,
                  "prop_type": "Bungalow",    "beds": 1, "baths": 1, "sqft":  680,
                  "desc": "Compact single-story cottage. Quick build, solid return on a budget."},
    "townhouse": {"name": "Townhouse",        "icon": "🏘️", "base_days": 140, "build_cost": 160_000, "finished_value":  450_000,
                  "prop_type": "Townhouse",   "beds": 2, "baths": 2, "sqft": 1250,
                  "desc": "Two-story townhouse with modern finishes. Good rental or flip."},
    "sfh":       {"name": "Single Family",    "icon": "🏡", "base_days": 168, "build_cost": 280_000, "finished_value":  700_000,
                  "prop_type": "Colonial",    "beds": 3, "baths": 2, "sqft": 1900,
                  "desc": "Classic single-family home. Strong value, broad appeal."},
    "executive": {"name": "Executive Home",   "icon": "🏰", "base_days": 196, "build_cost": 450_000, "finished_value": 1_100_000,
                  "prop_type": "Colonial",    "beds": 4, "baths": 3, "sqft": 3200,
                  "desc": "Spacious executive residence. Premium lot, premium returns."},
    "estate":    {"name": "Estate",           "icon": "🏯", "base_days": 224, "build_cost": 700_000, "finished_value": 1_750_000,
                  "prop_type": "Mansion",     "beds": 6, "baths": 5, "sqft": 7500,
                  "desc": "The flagship build. Two full years in construction. Worth every day."},
}

def _complete_new_build(s, build):
    """Convert a finished build into a real property on state.properties."""
    size   = NEW_BUILD_SIZES[build["size"]]
    nid    = s.get("next_id", 1000)
    s["next_id"] = nid + 1
    address = _make_address("Cedarvale Estates")
    prop = {
        "id": nid,
        "type": size["prop_type"],
        "neighborhood": "Cedarvale Estates",
        "address": address,
        "bedrooms":  size["beds"],
        "bathrooms": size["baths"],
        "sqft":      size["sqft"],
        "condition": 250,
        "upgrades": {},
        "premium_upgrades": list(build.get("premium_upgrades", [])),
        "squatter": None,
        "vacant_since": s["day"],
        "pending_reno": None, "pending_premium": None,
        "scheduled_reno": None, "scheduled_premium": None,
        "tenant": None, "days_rented": 0,
        "total_rent_collected": 0, "total_repair_costs": 0,
        "purchase_price": 0,
        "new_build": True,
        "fixed_market_value": size["finished_value"] + sum(
            PREMIUM_UPGRADES[k]["value_bonus"] for k in build.get("premium_upgrades", []) if k in PREMIUM_UPGRADES
        ),
    }
    s["properties"].append(prop)
    return prop

def _get_car_wash_package(cw):
    """Return the highest package tier currently available."""
    staff   = cw.get("staff",   {})
    inv     = cw.get("supplies", {})
    g_upgs  = cw.get("global_upgrades", {})
    if staff.get("rhonda") and inv.get("cw_standard_soap", 0) > 0 and inv.get("cw_premium_wax", 0) > 0 and g_upgs.get("dryer_arch"):
        return "premium"
    if inv.get("cw_premium_wax", 0) > 0 and g_upgs.get("dryer_arch"):
        return "deluxe"
    if inv.get("cw_standard_soap", 0) > 0:
        return "standard"
    return "basic"

def _car_wash_offered_packages(cw):
    """Which wash tiers you can currently offer (basic always, others gated by supply/upgrade/staff)."""
    staff = cw.get("staff", {}); inv = cw.get("supplies", {}); g = cw.get("global_upgrades", {})
    tiers = ["basic"]
    if inv.get("cw_standard_soap", 0) > 0:
        tiers.append("standard")
    if inv.get("cw_premium_wax", 0) > 0 and g.get("dryer_arch"):
        tiers.append("deluxe")
    if staff.get("rhonda") and inv.get("cw_standard_soap", 0) > 0 and inv.get("cw_premium_wax", 0) > 0 and g.get("dryer_arch"):
        tiers.append("premium")
    return tiers

def _car_wash_avg_price(cw):
    """Average $/car from the customer package mix. The Upsell Menu shifts the mix toward pricier washes."""
    tiers   = _car_wash_offered_packages(cw)
    upsell  = bool(cw.get("global_upgrades", {}).get("upsell_menu"))
    base_w  = {"basic": 5, "standard": 4, "deluxe": 2, "premium": 1}
    up_w    = {"basic": 2, "standard": 4, "deluxe": 4, "premium": 3}
    weights = up_w if upsell else base_w
    tw = sum(weights[t] for t in tiers) or 1
    return sum(weights[t] * CAR_WASH_BASE_PER_CAR * CAR_WASH_PACKAGES[t]["mult"] for t in tiers) / tw

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

ASSISTANTS = {
    "manager": {
        "name": "Property Manager", "icon": "🤝",
        "unlock_level": 11, "monthly_fee": 20_000,
        "desc": "Full hands-off management. Automatically handles every tenant issue, repair, story event, and lease renewal across all your rentals — true passive income.",
    },
    "accountant": {
        "name": "Accountant", "icon": "🧮",
        "unlock_level": 3, "monthly_fee": 2_800,
        "desc": "Auto-files your taxes on time every year and finds 15% more deductible write-offs. The retainer itself is a deductible expense.",
    },
    "leasing_agent": {
        "name": "Commercial Leasing Agent", "icon": "🤝",
        "unlock_level": COMMERCE_ROW_UNLOCK_LEVEL, "monthly_fee": COMMERCIAL_LEASING_AGENT_FEE,
        "desc": "Keeps Commerce Row leased — automatically fills vacant units with strong, complementary tenants so you never have to court applicants. (Building events are handled per-building by Superintendents.)",
    },
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

# ── Renovation cost scaling ────────────────────────────────────────────────────
# Base cost (from UPGRADES) applies to the smallest Midtown properties.
# Larger homes and better neighborhoods cost proportionally more.
_RENO_SQFT_MULT = [
    (600,  1.00),   # < 600 sqft  — tiny bungalows/condos
    (1000, 1.20),   # 600–999
    (1500, 1.45),   # 1000–1499
    (2000, 1.70),   # 1500–1999
    (3000, 2.10),   # 2000–2999
]
_RENO_HOOD_MULT = {
    "Midtown":   1.00,
    "Northside": 1.10,
    "Westwood":  1.25,
    "Riverside": 1.50,
    "Newbay":    1.80,
}

# DIY energy bonus per neighborhood tier (each step up costs +1 energy)
_RENO_HOOD_ENERGY_BONUS = {
    "Midtown":   0,
    "Northside": 1,
    "Westwood":  2,
    "Riverside": 3,
    "Newbay":    4,
}

def diy_energy_cost(prop, base_energy):
    """Return scaled DIY energy cost based on the property's neighborhood."""
    bonus = _RENO_HOOD_ENERGY_BONUS.get(prop.get("neighborhood", "Midtown"), 0)
    return base_energy + bonus

def reno_cost_mult(prop):
    """Return total cost multiplier for renovations at this property."""
    sqft = prop.get("sqft", 500)
    sqft_mult = 2.60  # 3000+ sqft
    for threshold, mult in _RENO_SQFT_MULT:
        if sqft < threshold:
            sqft_mult = mult
            break
    return sqft_mult * _RENO_HOOD_MULT.get(prop.get("neighborhood", "Midtown"), 1.0)

def _reno_cost(prop, base_cost, contractor_mult):
    return int(base_cost * contractor_mult * reno_cost_mult(prop))

def _roll_special_contractors(s):
    """Re-roll which special contractors are available across all owned properties."""
    for prop in s.get("properties", []):
        rolled = {}
        for key in SPECIAL_CONTRACTORS:
            if random.random() < SPECIAL_CONTRACTOR_CHANCE:
                prem_cost = _reno_cost(prop, UPGRADES[key]["base_cost"], CONTRACTORS["premium"]["cost_mult"])
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

    # ── Friends & family (cameos) ──────────────────────────────────────────────
    {"name": "Alexis Kennedy",      "icon": "🗨️",  "pay_chance": 0.91, "damage_chance": 0.05, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Could talk to a brick wall and leave the wall feeling heard. Somehow never annoying. You now know everything about competitive hot dog eating."},
    {"name": "Hannah Bailey",       "icon": "💡",  "pay_chance": 0.98, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Reads the whole lease twice and finds the typo you missed. Sharp, funny, three steps ahead. Quietly the best tenant on your books."},
    {"name": "Dez Castro",          "icon": "🤍",  "pay_chance": 0.95, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Knows every neighbor and their kids by name. The porch has never had more flowers. Leaves soup on your step when you look tired."},
    {"name": "Pablo Blanco",        "icon": "🧽",  "pay_chance": 0.96, "damage_chance": 0.01, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"], "unique": True,
     "desc": "The unit is cleaner than the day he moved in. Fixed the disposal, the gutter, and a problem you hadn't noticed. Owns a label maker. Uses it daily."},

    # ── Quirky originals — budget ──────────────────────────────────────────────
    {"name": "Tonya Brick",         "icon": "🧱",  "pay_chance": 0.85, "damage_chance": 0.10, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"], "unique": True,
     "desc": "Competitive powerlifter. Drops the bar like it owes her money. Apologizes through the floor to the unit below. Every single time."},
    {"name": "Gil Pruitt",          "icon": "🪀",  "pay_chance": 0.86, "damage_chance": 0.09, "stay_min": 30,  "stay_max": 120, "tiers": ["budget"], "unique": True,
     "desc": "Backyard inventor. The smoke alarm now goes off on a schedule. He calls these 'controlled tests.' You call the fire department."},
    {"name": "Marisol Vega",        "icon": "🌶️",  "pay_chance": 0.88, "damage_chance": 0.07, "stay_min": 45,  "stay_max": 150, "tiers": ["budget"], "unique": True,
     "desc": "Grows peppers on every windowsill. Handed you a jar of her hot sauce and watched you try it. You wept. She was delighted."},
    {"name": "Dewey Pratt",         "icon": "🦝",  "pay_chance": 0.83, "damage_chance": 0.11, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"], "unique": True,
     "desc": "Insists the raccoon is now a pet. It is not a pet. It does, however, come when he calls it."},
    {"name": "Bex Holloway",        "icon": "🛹",  "pay_chance": 0.84, "damage_chance": 0.10, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"], "unique": True,
     "desc": "Builds skate ramps in the driveway. A genuinely skilled carpenter. A genuinely terrible asker-of-permission."},
    {"name": "Otis Crumb",          "icon": "🥪",  "pay_chance": 0.87, "damage_chance": 0.06, "stay_min": 45,  "stay_max": 150, "tiers": ["budget"], "unique": True,
     "desc": "Films a sandwich-review channel from your kitchen. Forty thousand subscribers. Will offer you a bite — take it, it's incredible."},
    {"name": "Sandy Pell",          "icon": "🐚",  "pay_chance": 0.86, "damage_chance": 0.07, "stay_min": 45,  "stay_max": 120, "tiers": ["budget"], "unique": True,
     "desc": "Collects seashells. The whole place whispers like the ocean when the vents kick on. Mostly soothing. Occasionally haunting."},
    {"name": "Reg Tubbs",           "icon": "📺",  "pay_chance": 0.85, "damage_chance": 0.08, "stay_min": 60,  "stay_max": 180, "tiers": ["budget"], "unique": True,
     "desc": "Has a strong opinion about every show ever aired and the time to share it. Pays rent promptly during the commercial breaks."},
    {"name": "Wally Ng",            "icon": "🐠",  "pay_chance": 0.87, "damage_chance": 0.09, "stay_min": 30,  "stay_max": 120, "tiers": ["budget"], "unique": True,
     "desc": "Aquascaping obsessive. Six tanks and counting. The power bill is a felony. The fish have never been happier."},
    {"name": "Cricket Doyle",       "icon": "🎻",  "pay_chance": 0.84, "damage_chance": 0.08, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"], "unique": True,
     "desc": "Practicing violin, and honestly improving. The cat in the next unit remains his harshest critic."},
    {"name": "Trixie Vaughn",       "icon": "🪩",  "pay_chance": 0.85, "damage_chance": 0.11, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"], "unique": True,
     "desc": "Hosts a weekly disco night in the living room. The neighbors have stopped complaining and started attending."},

    # ── Quirky originals — budget + mid ────────────────────────────────────────
    {"name": "Lupe Ramos",          "icon": "🔧",  "pay_chance": 0.89, "damage_chance": 0.03, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Fixes the neighbors' cars in the lot. Yours runs smoother now and you never asked. Faint smell of motor oil. Completely worth it."},
    {"name": "Hank Mosby",          "icon": "🪣",  "pay_chance": 0.88, "damage_chance": 0.05, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Retired plumber, physically unable to walk past a drip. Every faucet you own has been silent since the day he arrived."},
    {"name": "Penny Lautner",       "icon": "💸",  "pay_chance": 0.90, "damage_chance": 0.05, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Negotiates everything to the cent — once got the power company to apologize. Always pays on time. Just argues first, on principle."},
    {"name": "Mateo Ferreira",      "icon": "⚽",  "pay_chance": 0.91, "damage_chance": 0.08, "stay_min": 60,  "stay_max": 150, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Coaches a kids' rec team that practices in the yard. The grass never fully recovers. The kids absolutely worship him."},
    {"name": "Glenda Pope",         "icon": "🧶",  "pay_chance": 0.92, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Knits without pause. You own three scarves and it is July. Possibly the sweetest human being currently alive."},
    {"name": "Foster Klein",        "icon": "🔬",  "pay_chance": 0.89, "damage_chance": 0.09, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Self-described 'independent researcher.' The garage hums faintly at night. He assures you it is legal. It is, you think, probably legal."},
    {"name": "Roni Salazar",        "icon": "📦",  "pay_chance": 0.91, "damage_chance": 0.04, "stay_min": 60,  "stay_max": 180, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Runs a small online shop. Boxes stacked by the door, never blocking the hall, rent in your account a day early every week."},
    {"name": "Faye Okonkwo",        "icon": "📷",  "pay_chance": 0.91, "damage_chance": 0.04, "stay_min": 90,  "stay_max": 240, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Photographer who develops film in the bathroom. The hallway smells faintly of chemistry. The prints taped up in the window are stunning."},
    {"name": "Norbert Stamp",       "icon": "📮",  "pay_chance": 0.92, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["budget", "mid"], "unique": True,
     "desc": "Philatelist. Has shown you his stamp collection three times. You now know more about 19th-century postage than any person should."},

    # ── Quirky originals — mid ─────────────────────────────────────────────────
    {"name": "Vivian Stathakis",    "icon": "📐",  "pay_chance": 0.96, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"], "unique": True,
     "desc": "Architect. Returned your lease with the formatting redlined. Pays ten days early. Has Opinions about the doorframes she will share unprompted."},
    {"name": "Doc Ferraro",         "icon": "🩻",  "pay_chance": 0.95, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid"], "unique": True,
     "desc": "Retired radiologist. Sees straight through everyone and says nothing about it. Somehow always knows the week you're stressed and stays out of your way."},
    {"name": "The Okafor Twins",    "icon": "👯",  "pay_chance": 0.93, "damage_chance": 0.07, "stay_min": 90,  "stay_max": 240, "tiers": ["mid"], "unique": True,
     "desc": "Identical. You genuinely cannot tell which one signed the lease. Based on a recent conversation, neither can they."},
    {"name": "Beatrice Lund",       "icon": "🕯️",  "pay_chance": 0.96, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid"], "unique": True,
     "desc": "Runs a candle business from the spare bedroom. The entire house now smells like 'Autumn Reverie.' You have stopped fighting it."},
    {"name": "Quentin Ash",         "icon": "♟️",  "pay_chance": 0.95, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"], "unique": True,
     "desc": "Plays chess by mail against seventeen opponents. The mailbox is a daily avalanche of postcards. He is winning twelve of them."},
    {"name": "The Mwangi Family",   "icon": "👨‍👩‍👧‍👦","pay_chance": 0.96, "damage_chance": 0.07, "stay_min": 150, "stay_max": 365, "tiers": ["mid"], "unique": True,
     "desc": "Three kids, one trampoline, infinite energy. The walls have a few new stories. Loud, warm, and worth every single scuff."},
    {"name": "Lorne Pickett",       "icon": "🪕",  "pay_chance": 0.94, "damage_chance": 0.05, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"], "unique": True,
     "desc": "Builds banjos by hand. The garage is full of half-finished banjos. Every so often a complete one escapes into the world."},
    {"name": "Yusuf Demir",         "icon": "♨️",  "pay_chance": 0.95, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 270, "tiers": ["mid"], "unique": True,
     "desc": "Mechanical engineer. Rebalanced your water pressure 'for fun.' Every shower in the building has been a religious experience since."},

    # ── Quirky originals — mid + premium ───────────────────────────────────────
    {"name": "Cordelia Vance",      "icon": "🎭",  "pay_chance": 0.97, "damage_chance": 0.03, "stay_min": 90,  "stay_max": 240, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Theater director. The living room is a permanent rehearsal space. You have already been handed a script 'just to read, no pressure.'"},
    {"name": "The Abernathys",      "icon": "🐕",  "pay_chance": 0.96, "damage_chance": 0.06, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Two humans, four dogs, one deeply exhausted mail carrier. Spotless inside, against all odds. Among the finest people you'll ever rent to."},
    {"name": "Sunny Adeyemi",       "icon": "☀️",  "pay_chance": 0.98, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Botanist who turned the side yard into an unofficial garden tour. Neighbors stop to photograph it. The property has never looked better."},
    {"name": "Roman Petrov",        "icon": "🧊",  "pay_chance": 0.97, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Speaks maybe forty words a month. Pays in crisp, flat bills. You're certain he has a fascinating life. You will never learn a thing about it."},
    {"name": "Delphine Marchetti",  "icon": "🥂",  "pay_chance": 0.98, "damage_chance": 0.02, "stay_min": 120, "stay_max": 365, "tiers": ["mid", "premium"], "unique": True,
     "desc": "Sommelier. Paid a full year ahead 'to simplify things.' Left a bottle on your desk that was older than you are."},

    # ── Quirky originals — premium ─────────────────────────────────────────────
    {"name": "Judge Edwin Cho",     "icon": "⚖️",  "pay_chance": 0.99, "damage_chance": 0.01, "stay_min": 120, "stay_max": 365, "tiers": ["premium"], "unique": True,
     "desc": "Retired judge. Reads the lease like he's about to rule on it. Has not been late to a single thing in his entire life."},
    {"name": "Saoirse Byrne",       "icon": "✒️",  "pay_chance": 0.98, "damage_chance": 0.02, "stay_min": 90,  "stay_max": 270, "tiers": ["premium"], "unique": True,
     "desc": "Bestselling novelist who writes from 4am to noon. You have definitely appeared in a book — you're pretty sure you're the suspicious landlord."},
    {"name": "Magnus Holt",         "icon": "🏔️",  "pay_chance": 0.97, "damage_chance": 0.03, "stay_min": 60,  "stay_max": 180, "tiers": ["premium"], "unique": True,
     "desc": "Mountaineer between expeditions. Vanishes for months at a time. Returns sun-scorched and silent, pays the whole balance, says almost nothing."},

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
    # ── Risky tier (genuinely flaky — low reliability, real screening stakes) ────
    {"name": "Chase Dillard",       "icon": "🎲",  "pay_chance": 0.62, "damage_chance": 0.13, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "Always 'between gigs.' Rent shows up eventually. Sometimes. The stories are genuinely great, though."},
    {"name": "Brandi Cole",         "icon": "💅",  "pay_chance": 0.68, "damage_chance": 0.10, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Lovely, scattered, perpetually 'so sorry, payday moved.' She means it every single time."},
    {"name": "Tevin Marsh",         "icon": "🃏",  "pay_chance": 0.58, "damage_chance": 0.09, "stay_min": 30,  "stay_max": 75,  "tiers": ["budget"],         "unique": True,
     "desc": "Swears he's good for it. Has sworn this four times now. Weirdly, impossibly likable."},
    {"name": "The Rourke Boys",     "icon": "🍻",  "pay_chance": 0.60, "damage_chance": 0.16, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "Three roommates, one lease, zero communication. The recycling bin tells a harrowing story."},
    {"name": "Dot Kessler",         "icon": "🪙",  "pay_chance": 0.66, "damage_chance": 0.05, "stay_min": 45,  "stay_max": 120, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Counts rent out in exact change and disputes every cent. Eventually pays. Eventually."},
    {"name": "Sly Benedetto",       "icon": "🎰",  "pay_chance": 0.55, "damage_chance": 0.12, "stay_min": 30,  "stay_max": 60,  "tiers": ["budget"],         "unique": True,
     "desc": "Cash business, vague hours, pays big or not at all. A coin-flip in tenant form."},
    {"name": "Margie Flint",        "icon": "🐈",  "pay_chance": 0.70, "damage_chance": 0.11, "stay_min": 45,  "stay_max": 120, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Wonderful woman. Six cats she 'doesn't have.' Rent is more of an afterthought to her."},
    {"name": "Deke Valentine",      "icon": "🎸",  "pay_chance": 0.64, "damage_chance": 0.15, "stay_min": 30,  "stay_max": 90,  "tiers": ["budget"],         "unique": True,
     "desc": "Touring musician. Home unpredictably, pays equally unpredictably. The amp is staying, apparently."},
    {"name": "Pru Hatcher",         "icon": "📺",  "pay_chance": 0.72, "damage_chance": 0.07, "stay_min": 45,  "stay_max": 120, "tiers": ["budget", "mid"],  "unique": True,
     "desc": "Means well, forgets everything — rent, trash day, your name. Pays double to apologize, then forgets again."},
]

# ── Tenant traits ──────────────────────────────────────────────────────────────
# One signature trait per tenant — surfaced at screening so picking matters, and
# it drives behavior. Some traits are mechanical now; others are flavor + hooks
# for the upcoming renewal/storylet systems.
TENANT_TRAITS = {
    "reliable":    {"name": "Reliable",      "icon": "🎯",   "desc": "Pays like clockwork — basically never misses rent."},
    "handy":       {"name": "Handy",         "icon": "🔧",   "desc": "Fixes things up — condition slowly improves while they live here."},
    "green_thumb": {"name": "Green Thumb",   "icon": "🌱",   "desc": "Tends the place — condition gently improves over time."},
    "quiet":       {"name": "Quiet",         "icon": "🤫",   "desc": "Low-key and easy to keep happy. Little wear."},
    "rowdy":       {"name": "Rowdy",         "icon": "🔊",   "desc": "Lively — noticeably harder on the property."},
    "big_family":  {"name": "Big Family",    "icon": "👨‍👩‍👧‍👦", "desc": "Full house — more wear, but they stay for the long haul."},
    "creative":    {"name": "Creative",      "icon": "🎨",   "desc": "Big projects at home — a little harder on the place."},
    "homebody":    {"name": "Homebody",      "icon": "🏠",   "desc": "Always home. Notices — and reports — everything."},
    "penny":       {"name": "Penny Pincher", "icon": "💰",   "desc": "Haggles on rent, but won't walk over a few dollars."},
    "subletter":   {"name": "Subletter",     "icon": "🕵️",   "desc": "Might quietly rent your place out to someone else…"},
}

# Mechanical effects applied this pass. Traits not listed are flavor + future hooks.
TRAIT_EFFECTS = {
    "reliable":    {"pay_floor": 0.97},
    "handy":       {"cond_per_week":  3},
    "green_thumb": {"cond_per_week":  2},
    "rowdy":       {"cond_per_week": -2},
    "big_family":  {"cond_per_week": -1},
    "creative":    {"cond_per_week": -1},
}

# Signature trait per named profile (matched to their bio).
PROFILE_TRAITS = {
    "Todd Burman": "homebody", "Stevie Reinholt": "creative", "Darnell Okafor": "rowdy",
    "Wanda Greer": "homebody", "Priya Nair": "green_thumb", "Ziggy": "rowdy",
    "Kevin Marsh": "reliable", "Miles Garner": "reliable", "Dennis Falk": "creative",
    "Orlando Cruz": "creative", "Fran Dubois": "creative", "Clint Hooper": "reliable",
    "Margot Voss": "handy", "Carol Fitch": "quiet", "Juno Park": "homebody",
    "Cynthia Bloom": "rowdy", "Russ Tirado": "creative", "Janet Osei": "rowdy",
    "Marcus Webb": "reliable", "Nora Finch": "homebody", "Sam & Deb Hollis": "creative",
    "Theo Blackwell": "handy", "Donna Kephart": "homebody", "Bev Stanton": "homebody",
    '"Coach" Ernie Walls': "quiet", "Gerald": "reliable", "Nina Alcott": "creative",
    "The Watkins Brothers": "rowdy", "Simone Adeyemi": "subletter", "Arthur Pham": "reliable",
    "Gracie Monroe": "quiet", "Hector Vidal": "creative", "Patrice Owens": "quiet",
    "Ben Kowalczyk": "handy", "Pete": "subletter", "The Nguyens": "reliable",
    "The Delgados": "big_family", '"Big" Lou Santino': "quiet", "Diane Cho": "homebody",
    "Dr. Yemi Adebayo": "homebody", "Cassandra Lyle": "reliable", "Maureen Tully": "homebody",
    "Old Man Pietrzak": "reliable", "Ray Kowalski": "quiet", "Carl & Judy Prescott": "reliable",
    "College Student": "rowdy", "The Musician": "rowdy", "Night Owl": "quiet",
    "The Artist": "creative", "The Freelancer": "homebody", "Young Couple": "creative",
    "Section 8": "reliable", "The Teacher": "quiet", "Single Parent": "reliable",
    "The Handyman": "handy", "Remote Worker": "homebody", "Young Professional": "quiet",
    "The Couple": "quiet", "The Executive": "reliable", "Empty Nesters": "homebody",
    # Cameos
    "Alexis Kennedy": "homebody", "Hannah Bailey": "reliable", "Dez Castro": "green_thumb", "Pablo Blanco": "handy",
    # Quirky originals
    "Tonya Brick": "rowdy", "Gil Pruitt": "creative", "Marisol Vega": "green_thumb", "Dewey Pratt": "rowdy",
    "Bex Holloway": "creative", "Otis Crumb": "homebody", "Sandy Pell": "quiet", "Reg Tubbs": "homebody",
    "Wally Ng": "creative", "Cricket Doyle": "rowdy", "Trixie Vaughn": "rowdy", "Lupe Ramos": "handy",
    "Hank Mosby": "handy", "Penny Lautner": "penny", "Mateo Ferreira": "rowdy", "Glenda Pope": "quiet",
    "Foster Klein": "creative", "Roni Salazar": "reliable", "Faye Okonkwo": "homebody", "Norbert Stamp": "homebody",
    "Vivian Stathakis": "reliable", "Doc Ferraro": "quiet", "The Okafor Twins": "rowdy", "Beatrice Lund": "homebody",
    "Quentin Ash": "quiet", "The Mwangi Family": "big_family", "Lorne Pickett": "creative", "Yusuf Demir": "handy",
    "Cordelia Vance": "creative", "The Abernathys": "big_family", "Sunny Adeyemi": "green_thumb", "Roman Petrov": "quiet",
    "Delphine Marchetti": "reliable", "Judge Edwin Cho": "reliable", "Saoirse Byrne": "homebody", "Magnus Holt": "quiet",
    # Risky tier
    "Chase Dillard": "rowdy", "Brandi Cole": "creative", "Tevin Marsh": "subletter", "The Rourke Boys": "rowdy",
    "Dot Kessler": "penny", "Sly Benedetto": "subletter", "Margie Flint": "homebody", "Deke Valentine": "rowdy",
    "Pru Hatcher": "creative",
}

def trait_for(profile):
    """A tenant's signature trait — mapped by name, else inferred from stats."""
    name = profile.get("name", "")
    if name in PROFILE_TRAITS:
        return PROFILE_TRAITS[name]
    if profile.get("damage_chance", 0) >= 0.10:
        return "rowdy"
    if profile.get("pay_chance", 0) >= 0.96:
        return "reliable"
    return "quiet"

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
    """Return (max_energy, recharge). Base is 4/1; all bonuses come from owned items."""
    max_e = 4
    rch   = 1
    items = s.get("owned_items", {})
    for key, item in STORE_ITEMS.items():
        if items.get(key):
            max_e += item.get("max_energy_bonus", 0)
            rch   += item.get("recharge_bonus", 0)
    return max_e, rch

def upgrade_cooldown_remaining(upg_val, current_day):
    """Days left before this upgrade can be done again. 0 = available now."""
    if not isinstance(upg_val, dict):
        return 0   # old format = no cooldown
    return max(0, RENO_COOLDOWN - (current_day - upg_val.get("day", 0)))

def calc_market_value(prop):
    # Commercial properties use purchase price as their market value baseline
    if prop.get("commercial"):
        ctype = COMMERCIAL_TYPES.get(prop.get("type", ""), {})
        return prop.get("purchase_price", ctype.get("price", 0))
    if prop.get("fixed_market_value"):
        val = prop["fixed_market_value"]
        for key, upg_val in prop.get("upgrades", {}).items():
            quality = get_upgrade_quality(upg_val)
            val    += int(UPGRADES[key]["value_add"] * (quality / 100))
        val += get_premium_bonuses(prop)["value"]
        return val
    n         = NEIGHBORHOODS[prop["neighborhood"]]
    base      = prop["sqft"] * 120 + prop["bedrooms"] * 15000 + prop["bathrooms"] * 8000
    cond_mult = 0.70 + (prop["condition"] / MAX_CONDITION) * 0.30
    val       = int(base * n["price_mult"] * cond_mult)
    for key, upg_val in prop.get("upgrades", {}).items():
        quality = get_upgrade_quality(upg_val)
        val    += int(UPGRADES[key]["value_add"] * (quality / 100))
    val += get_premium_bonuses(prop)["value"]
    return val

def calc_monthly_rent(prop):
    if prop.get("commercial"):
        return sum(u.get("monthly_rent", 0) for u in prop.get("units", []))
    n         = NEIGHBORHOODS[prop["neighborhood"]]
    base      = int((prop["sqft"] * 1.3 + prop["bedrooms"] * 475 + prop["bathrooms"] * 185) * n["rent_mult"])
    cond_mult = 0.65 + (prop["condition"] / MAX_CONDITION) * 0.55
    bonus     = sum(int(UPGRADES[k]["value_add"] * 0.003 * (get_upgrade_quality(v) / 100))
                    for k, v in prop.get("upgrades", {}).items())
    # premium_weekly is per-week; monthly_rent is used as 4-week equivalent
    premium_weekly = get_premium_bonuses(prop)["rent"]
    total = int(base * cond_mult) + bonus + (premium_weekly * 4)
    if prop.get("new_build"):
        total = int(total * 1.25)
    return total

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

# ── Credit score helpers ─────────────────────────────────────────────────────
def _bank(s):
    return s.setdefault("bank", {"savings": 0, "loans": [], "next_loan_id": 1})

def credit_score(s):
    return _bank(s).get("credit_score", CREDIT_START)

def _credit_set(s, score):
    _bank(s)["credit_score"] = max(CREDIT_MIN, min(CREDIT_MAX, int(round(score))))

def _credit_adjust(s, delta):
    _credit_set(s, credit_score(s) + delta)

def credit_label(score):
    if score >= 760: return "Excellent"
    if score >= 700: return "Good"
    if score >= 640: return "Fair"
    if score >= 580: return "Poor"
    return "Bad"

def _credit_apr_mult(score):
    """Effective-APR multiplier: 300 → 1.5×, 850 → 0.6× (linear)."""
    t = (max(CREDIT_MIN, min(CREDIT_MAX, score)) - CREDIT_MIN) / (CREDIT_MAX - CREDIT_MIN)
    return 1.5 - t * 0.9

def _credit_size_factor(score):
    """Borrowing-ceiling factor: 300 → 0.3, 760+ → 1.0 of a product's base max."""
    t = max(0.0, min(1.0, (score - CREDIT_MIN) / (760 - CREDIT_MIN)))
    return 0.3 + t * 0.7

def effective_apr(product, score):
    return round(product["apr"] * _credit_apr_mult(score), 4)

def effective_max(product, score):
    # round down to a clean $500 step, never below the product minimum
    raw = product["max"] * _credit_size_factor(score)
    return max(product["min"], int(raw // 500) * 500)

def loan_offer(product, score):
    """Score-adjusted offer for a product: qualifies?, effective APR & ceiling."""
    return {
        **product,
        "qualifies":     score >= product["min_score"],
        "effective_apr": effective_apr(product, score),
        "effective_max": effective_max(product, score),
        "sample_payment": calc_weekly_payment(product["min"], effective_apr(product, score), product["term_seasons"]),
    }

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
    prop["purchase_price"] = int(calc_market_value(prop) * random.uniform(0.97, 1.10))
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
        "properties": [starter], "market": [], "commercial_market": [], "log": [],
        "applicants_cache": {},
        "last_bank_day": 1,
        "energy": 4,
        "player_home": "grandmas_basement",
        "owned_items": {},
        "diy_classes": {},
        "jobs": generate_jobs(),
        "redeemed_codes": [],
        "intro_seen": False,
        "squatter_count": 0,
        "bank": {"savings": 0, "loans": [], "next_loan_id": 1, "credit_score": CREDIT_START, "cds": [], "next_cd_id": 1},
        "level": 0, "xp": 0,
        "stocks": _init_stock_state(),
        "assistants": {},
    }
    state["log"].append({"day": 1, "type": "warning",
        "text": "You inherited a run-down Bungalow in Midtown — but there's a squatter inside demanding $4,367 to leave. Bribe them out, or sell the property as-is and pocket $80,000 to start fresh."})
    state["market"], state["next_id"] = _gen_market(state["next_id"])
    return state

# Foreclosures: rare, dirt-cheap, always F-tier fixer-uppers — a beginner on-ramp.
# Per-neighborhood spawn chance, highest in the cheap areas, ~1% in the best (Newbay).
FORECLOSURE_CHANCE = {"Midtown": 0.15, "Northside": 0.12, "Westwood": 0.07, "Riverside": 0.03, "Newbay": 0.01}

def _make_foreclosure(nid, hood):
    p = generate_property(nid, hoods=[hood])
    p["condition"]      = random.randint(15, 37)     # always F-tier
    p["foreclosure"]    = True
    p["purchase_price"] = max(2_000, int(calc_market_value(p) * random.uniform(0.30, 0.40)))
    return p

def _gen_market(start_id, hoods=None):
    listings, nid = [], start_id
    target_hoods = list(hoods) if hoods else list(NEIGHBORHOODS.keys())
    for hood in target_hoods:
        count = random.randint(2, 5)
        for _ in range(count):
            listings.append(generate_property(nid, hoods=[hood]))
            nid += 1
        # Rare bonus foreclosure listing for this neighborhood (extra opportunity, not a replacement)
        if random.random() < FORECLOSURE_CHANCE.get(hood, 0):
            listings.append(_make_foreclosure(nid, hood))
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
    s.setdefault("vending_machines", [])
    s.setdefault("vinny_hired", False)
    s.setdefault("costpro_inventory", {})
    # ── Commercial overhaul migration: leasing agent + per-unit satisfaction/% rent ──
    # Leasing Agent moved into the unified assistants system; migrate the old standalone flag.
    if s.pop("leasing_agent", None):
        s.setdefault("assistants", {})["leasing_agent"] = True
    for _p in s.get("properties", []):
        if _p.get("commercial"):
            _p.setdefault("foot_traffic", 50)
            for _u in _p.get("units", []):
                _u.setdefault("satisfaction", 70)
                _u.setdefault("pct_rent_monthly", 0)
    # ── Vending Phase-1 migration: old single-tier machines → slot model ──────
    _vm_name_to_key = {v["name"]: k for k, v in VM_LOCATIONS.items()}
    for vm in s.get("vending_machines", []):
        if "slots" in vm:
            continue   # already new-model
        loc_key = vm.get("location_key") or _vm_name_to_key.get(vm.get("location", "")) \
                  or VM_LOCATION_ORDER[(vm.get("slot", 1) - 1) % len(VM_LOCATION_ORDER)]
        vm["location_key"] = loc_key
        slots = _vm_blank_slots()
        # Grandfather their old stock into slot 0 as Snacks, filled.
        slots[0].update({"category": "snacks", "stock": float(VM_SLOT_CAPACITY), "restock_day": s.get("day", 0)})
        vm["slots"] = slots
        for k in ("snack_tier", "drain_days", "days_remaining", "daily_income", "status", "location", "upgrades"):
            vm.pop(k, None)
    # Old per-tier snack inventory → unified "snacks" units (1 old case ≈ 30 units).
    _inv = s.get("costpro_inventory", {})
    _old_snacks = sum(_inv.pop(f"snacks_{t}", 0) for t in ("cheap", "mid", "premium"))
    if _old_snacks:
        _inv["snacks"] = _inv.get("snacks", 0) + _old_snacks * 30
    # ── Vending Phase-2 fields: reputation, pricing, upgrades + Grandma ───────
    for vm in s.get("vending_machines", []):
        vm.setdefault("reputation", 70)
        vm.setdefault("price_level", "normal")
        vm.setdefault("upgrades", {})
    s.setdefault("grandma_hired", False)
    s.setdefault("grandma_last_shop", 0)
    s.setdefault("grandma_budget", 0)   # 0 = uncapped
    s.setdefault("laundromat", None)
    # Laundromat overhaul migration: old type-less machines become Combo units
    # (they did wash+dry), plus new loyalty/add-on fields.
    _lm = s.get("laundromat")
    if _lm:
        for _m in _lm.get("machines", []):
            _m.setdefault("type", "combo")
        _lm.setdefault("members", 0)
        _lm.setdefault("addons", {})
        # If they already own the vending add-on but have no laundromat machine
        # (pre-7th-machine saves), spawn it now.
        if _lm["addons"].get("vending"):
            _vms = s.setdefault("vending_machines", [])
            if not any(v.get("location_key") == "laundromat" for v in _vms):
                _vms.append(_vm_new_machine(s, 7, "laundromat"))
    s.setdefault("arcade", None)
    # Existing saves that bought the arcade add-on but predate the Arcade business.
    if _lm and _lm.get("addons", {}).get("arcade") and not (s.get("arcade") and s["arcade"].get("unlocked")):
        _g = random.choice(ARCADE_GAMES)
        s["arcade"] = {"unlocked": True, "total_earned": 0, "staff": {},
                       "cabinets": [{"id": 0, "title": _g["title"], "genre": _g["genre"],
                                     "condition": 100, "status": "working"}]}
    # Bring older arcade cabinets up to the genre/upkeep model.
    _arc = s.get("arcade")
    if _arc and _arc.get("unlocked"):
        _arc.setdefault("staff", {})
        _arc.setdefault("uncollected", 0)
        _arc.setdefault("cleanliness", 100)
        _arc.setdefault("prizes", 0)
        _arc.setdefault("decor", {})
        for _cab in _arc.get("cabinets", []):
            if "title" not in _cab:
                _cab["title"] = _cab.pop("game", "Quarter Muncher")
            _cab.setdefault("genre", _arcade_genre_of(_cab["title"]))
            _cab.setdefault("condition", 100)
            _cab.setdefault("status", "working")
            _cab.setdefault("rare", _cab["title"] in ARCADE_RARE_TITLES)
            _cab.setdefault("high_score", 0)
            _cab.setdefault("hot_until", 0)
        if not _arc.get("market"):
            _arcade_roll_market(s)
        # Retroactively give existing arcades their on-floor vending machine.
        _vms = s.setdefault("vending_machines", [])
        if not any(v.get("location_key") == "arcade" for v in _vms):
            _vms.append(_vm_new_machine(s, 8, "arcade"))
    s.setdefault("pole_studio", None)
    s.setdefault("car_wash", None)
    s.setdefault("commercial_market", [])
    s.setdefault("assistants", {})
    # The three old assistants (repair / tenant / estate) were merged into one
    # all-in-one "manager". Grandfather anyone who hired any of them into the bundle.
    _asst = s["assistants"]
    if any(_asst.get(k) for k in ("repair", "tenant", "estate")) and not _asst.get("manager"):
        _asst["manager"] = True
    for k in ("repair", "tenant", "estate"):
        _asst.pop(k, None)
    # ── Milestones / Mogul Rank: baseline existing saves silently (no reward flood) ──
    if "milestones_done" not in s:
        s["milestones_done"] = [m["key"] for m in MILESTONES if _milestone_ok(m, s)]
    s.setdefault("mogul_rank", _mogul_rank_index(_empire_score(s)))
    for prop in s.get("properties", []):
        if prop.get("commercial"):
            prop.setdefault("superintendent", False)
            prop.setdefault("maintenance", False)
            # Bugfix cleanup: squatters used to be able to spawn on commercial buildings.
            # They only belong in residential homes — evict any that slipped in.
            if prop.get("squatter"):
                prop["squatter"] = None
    _bank(s).setdefault("credit_score", CREDIT_START)
    _bank(s).setdefault("cds", [])
    _bank(s).setdefault("next_cd_id", 1)
    s.setdefault("tax_year_flip_income", 0)
    s.setdefault("tax_year_rent_income", 0)
    s.setdefault("tax_year_biz_income", {})
    s.setdefault("tax_year_deductions", 0)
    s.setdefault("tax_extension_filed", False)
    s.setdefault("tax_owed", 0)
    # Accountant is now an assistant (was a standalone flag); migrate it over.
    if s.pop("accountant_hired", False):
        s.setdefault("assistants", {})["accountant"] = True
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
                    prem_cost = _reno_cost(prop, UPGRADES[key]["base_cost"], CONTRACTORS["premium"]["cost_mult"])
                    rolled[key] = {**SPECIAL_CONTRACTORS[key], "cost": prem_cost}
            prop["special_contractors"] = rolled
    # ── Dark Mode ("Off the Books"): its own self-contained game, namespaced. ──
    s.setdefault("mode", "legit")        # 'legit' | 'dark'
    s.setdefault("dark", None)           # all crime-empire data lives here in dark mode
    s.setdefault("dark_snapshot", None)  # the Level-11 legit save to "wake" back to
    # Backfill dark saves made before newer fields existed (so old in-progress runs work).
    dk = s.get("dark")
    if dk:
        dk.setdefault("cred", 1); dk.setdefault("cred_xp", 0)
        dk.setdefault("dirty_money", 0); dk.setdefault("heat", 0)
        dk.setdefault("crews", []); dk.setdefault("next_crew_id", 1)
        dk.setdefault("roster", []); dk.setdefault("recruits", []); dk.setdefault("next_recruit_id", 1)
        dk.setdefault("recruits_refresh_day", None); dk.setdefault("supplies", {})
        dk.setdefault("pending_event", None)
        dk.setdefault("raid_in", None); dk.setdefault("bribes", 0)
        dk.setdefault("lawyered", False); dk.setdefault("moved", False); dk.setdefault("lying_low", False)
        dk.setdefault("watch", None); dk.setdefault("watch_known", False)
        dk.setdefault("watch_quiet", 0); dk.setdefault("watch_since", 0); dk.setdefault("vip", False)
        dk.setdefault("raid_cooldown", 0); dk.setdefault("raid_pace", 0); dk.setdefault("raid_days", 0)
        for _ln in (dk.get("launder") or {}).values(): _ln.setdefault("bank", 0)
        # The Hunt was reworked (heat = a per-op watch trigger + raid countdown). Any tail from
        # the old model is reset to a clean slate so its stale heat isn't read as a countdown.
        if dk.get("watch") and not dk["watch"].get("clues"):
            dk["watch"] = None; dk["heat"] = 0; dk["raid_pace"] = 0; dk["raid_days"] = 0
        dk.setdefault("hunt_introduced", False); dk.setdefault("cook_day", None); dk.setdefault("cooks_today", 0)
        dk.setdefault("sling_day", None); dk.setdefault("slings_today", 0)
        dk.setdefault("fixer_washed_day", None); dk.setdefault("fixer_washed", 0)
        dk.setdefault("debt_active", False); dk.setdefault("debt_balance", 0); dk.setdefault("year_take", 0)
        dk.setdefault("debt_bill", 0); dk.setdefault("debt_paid", 0); dk.setdefault("debt_bill_year", None)
        dk.setdefault("debt_first_year", None); dk.setdefault("fixer_event", None)
        dk.setdefault("stash", {}); dk.setdefault("dealers", []); dk.setdefault("next_dealer_id", 1)
        dk.setdefault("home_market", []); dk.setdefault("homes_bought", 0)
        if "biz" not in dk:
            dk["biz"] = {"laundromat": bool((s.get("laundromat") or {}).get("owned")),
                         "car_wash":   bool((s.get("car_wash") or {}).get("owned")),
                         "strip_club": bool((s.get("pole_studio") or {}).get("owned")),
                         "casino":     False,
                         "arcade_had": bool((s.get("arcade") or {}).get("unlocked")),
                         "vending":    len(s.get("vending_machines") or []) > 0}
        dk.setdefault("corners_unlocked", not dk["biz"].get("vending"))
        dk.setdefault("heists_done", []); dk.setdefault("heist_crew", []); dk.setdefault("heist", None)
        dk.setdefault("next_heist_member", 1); dk.setdefault("heist_takes", {})
        dk.setdefault("heist_lockout", 0); dk.setdefault("heist_lockout_cred", 0)
        dk.setdefault("phil", None); dk.setdefault("phil_notified", False)
        if dk.get("heist_crew"): _dark_heist_ensure_pool(dk)   # repair old duplicated/partial pools
        if dk.get("club"): _dark_club_migrate(dk["club"])
    return s

def load():
    """Read game state from the request body (_state field) or start a new game."""
    data  = request.get_json(silent=True) or {}
    state = data.get('_state')
    return _migrate_state(state) if state else new_game()

def save(state):
    """Store state on Flask's per-request g — injected into the response automatically."""
    state["log"] = state.get("log", [])[-300:]   # cap log so state doesn't grow unbounded
    g.game_state = state

def _biz_income(s, key, amt):
    """Tally a business's operating income for the current tax year (display only)."""
    if amt:
        b = s.setdefault("tax_year_biz_income", {})
        b[key] = b.get(key, 0) + int(round(amt))

def _tax_deduct(s, amt):
    """Tally a deductible operating expense (wages, supplies, maintenance) for the
    current tax year — lowers taxable business+flip income."""
    if amt and amt > 0:
        s["tax_year_deductions"] = s.get("tax_year_deductions", 0) + int(round(amt))

def _bracket_tax(amount):
    """Progressive tax on a positive amount across TAX_BRACKETS."""
    if amount <= 0:
        return 0.0
    tax, last = 0.0, 0
    for cap, rate in TAX_BRACKETS:
        if amount <= last:
            break
        tax += (min(amount, cap) - last) * rate
        last = cap
    return tax

def _compute_taxes(s):
    """Break down taxes owed for the current tax year.
    Rent → flat low rate. Business + flip profit → progressive brackets, minus
    deductible operating expenses (boosted if an Accountant is on staff)."""
    rent = int(s.get("tax_year_rent_income", 0))
    flip = int(s.get("tax_year_flip_income", 0))
    biz  = int(sum(s.get("tax_year_biz_income", {}).values()))
    ded  = int(s.get("tax_year_deductions", 0))
    has_accountant = bool(s.get("assistants", {}).get("accountant"))
    if has_accountant:
        ded = int(ded * (1 + ACCOUNTANT_DEDUCTION_BONUS))
    taxable_active = max(0, flip + biz - ded)
    rent_tax   = int(round(rent * RENT_TAX_RATE))
    active_tax = int(round(_bracket_tax(taxable_active)))
    return {
        "rent_income": rent, "flip_income": flip, "biz_income": biz,
        "deductions": ded, "taxable_active": taxable_active,
        "rent_tax": rent_tax, "active_tax": active_tax,
        "total": rent_tax + active_tax,
        "accountant": has_accountant,
    }

def _reset_tax_year(s):
    s["tax_year_flip_income"] = 0
    s["tax_year_rent_income"] = 0
    s["tax_year_biz_income"]  = {}
    s["tax_year_deductions"]  = 0
    s["tax_owed"]             = 0
    s["tax_extension_filed"]  = False

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
    # Cache-busting version from asset mtimes, so browsers always load fresh
    # game.js / style.css after an update (no more stale-cache "missing feature" bugs).
    try:
        base = os.path.join(os.path.dirname(__file__), "static")
        ver  = int(max(os.path.getmtime(os.path.join(base, f)) for f in ("game.js", "style.css")))
    except OSError:
        ver = 1
    return render_template('index.html', asset_v=ver)

@app.route('/api/state', methods=['GET', 'POST'])
def api_state():
    s = load()
    max_e, rch = _get_home_stats(s)
    weekly_income = sum(p["tenant"]["rent"] for p in s["properties"] if p.get("tenant"))
    lvl = s.get("level", 0)
    # Milestones can be earned by any action (sell, buy, hire…), not just advancing —
    # so reconcile them on every state read and report freshly-unlocked ones for a toast.
    _ms_newly = _sync_milestones(s)
    if _ms_newly:
        save(s)   # persist so the unlock isn't re-detected next refresh
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
        "assistants":             s.get("assistants", {}),
        "tax_breakdown":          _compute_taxes(s),
        "level":                  lvl,
        "xp_pct":                 calc_xp_pct(s),
        "unlocked_neighborhoods": get_unlocked_neighborhoods(lvl),
        "unlocked_homes":         get_unlocked_home_keys(lvl),
        "intro_seen":             s.get("intro_seen", True),
        "vending_machines":       s.get("vending_machines", []),
        "vinny_hired":            s.get("vinny_hired", False),
        "grandma_hired":          s.get("grandma_hired", False),
        "grandma_last_shop":      s.get("grandma_last_shop", 0),
        "grandma_budget":         s.get("grandma_budget", 0),
        "costpro_inventory":      s.get("costpro_inventory", {}),
        "laundromat":             s.get("laundromat"),
        "arcade":                 s.get("arcade"),
        "pole_studio":            s.get("pole_studio"),
        "car_wash":               s.get("car_wash"),
        "building_permit":        s.get("building_permit", False),
        "owned_crews":            s.get("owned_crews", []),
        "active_builds":          s.get("active_builds", []),
        "empire":                 {**_empire_payload(s), "just_unlocked": [{"name": m["name"], "reward": MILESTONE_REWARD.get(m["key"], 0)} for m in _ms_newly]},
        "mode":                   s.get("mode", "legit"),
        "dark":                   s.get("dark"),
        "dark_defs":              ({"drugs": DARK_DRUGS, "supplies": DARK_SUPPLIES, "traits": DARK_TRAITS, "swat_heat": DARK_SWAT_HEAT}
                                   if s.get("mode") == "dark" else None),
    })

def _empire_payload(s):
    score   = _empire_score(s)
    idx     = _mogul_rank_index(score)
    cur     = MOGUL_RANKS[idx]
    nxt     = MOGUL_RANKS[idx + 1] if idx + 1 < len(MOGUL_RANKS) else None
    span_lo = cur["score"]
    span_hi = nxt["score"] if nxt else cur["score"]
    pct     = 100 if not nxt else max(0, min(100, round((score - span_lo) / max(1, span_hi - span_lo) * 100)))
    done    = set(s.get("milestones_done", []))
    return {
        "score":            score,
        "total_wealth":     _total_wealth(s),
        "businesses_owned": _businesses_owned(s),
        "rank_index":       idx,
        "rank_name":        cur["name"],
        "rank_icon":        cur["icon"],
        "next_rank_name":   nxt["name"] if nxt else None,
        "next_rank_score":  nxt["score"] if nxt else None,
        "progress_pct":     pct,
        "business_bonus":   EMPIRE_BUSINESS_BONUS,
        "milestone_bonus":  EMPIRE_MILESTONE_BONUS,
        "milestones_total": len(MILESTONES),
        "milestones_done":  len(done),
        "milestones": [{"key": m["key"], "name": m["name"], "icon": m["icon"],
                        "desc": m["desc"], "reward": MILESTONE_REWARD.get(m["key"], 0),
                        "done": m["key"] in done}
                       for m in MILESTONES],
    }

# ── Dark Mode: enter ("Off the Books") and wake ("it was all a dream") ──────────
@app.route('/api/dark/enter', methods=['POST'])
def api_dark_enter():
    s = load()
    if s.get("mode") == "dark":
        return jsonify({"error": "You're already on the dark side."}), 400
    # Snapshot the whole legit save so "it was all a dream" restores it exactly.
    s["dark_snapshot"] = copy.deepcopy({k: v for k, v in s.items() if k not in ("dark", "dark_snapshot")})
    s["mode"] = "dark"
    # The Fixer takes EVERYTHING. You start from scratch: $10k seed + one rundown starter
    # house (Midtown — "crumbling blocks, forgotten by time"). Nothing else carries over.
    starter = generate_property(s["next_id"], hoods=["Midtown"]); s["next_id"] += 1
    starter["purchase_price"] = 0; starter["foreclosure"] = False
    starter["rented"] = False; starter["tenant"] = None; starter["lab"] = None; starter["starter"] = True
    s["properties"] = [starter]
    s["cash"] = 10_000
    s["dark"] = {"cred": 1, "cred_xp": 0, "dirty_money": 0, "heat": 0, "entered_day": s.get("day", 1),
                 "crews": [], "next_crew_id": 1,
                 "recruits": [], "next_recruit_id": 1, "roster": [], "recruits_refresh_day": None,
                 "stash": {}, "supplies": {}, "dealers": [], "next_dealer_id": 1, "home_market": [],
                 "biz": {}, "corners_unlocked": True, "homes_bought": 0,
                 "raid_in": None, "bribes": 0, "lawyered": False, "moved": False, "lying_low": False,
                 "watch": None, "watch_known": False, "watch_quiet": 0, "watch_since": 0, "vip": False,
                 "raid_cooldown": 0, "raid_pace": 0, "raid_days": 0,
                 "hunt_introduced": False, "pending_event": None}
    s["dark"]["recruits"] = _dark_gen_recruits(s["dark"], 10)   # faces on the street to hire
    _dark_gen_home_market(s)                                    # more homes you can buy later
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/wake', methods=['POST'])
def api_dark_wake():
    s = load()
    snap = s.get("dark_snapshot")
    if not snap:
        return jsonify({"error": "Nothing to wake from."}), 400
    restored = copy.deepcopy(snap)
    restored["mode"] = "legit"
    restored["dark"] = None
    restored["dark_snapshot"] = None
    save(restored)
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════════════════════════════
#  DARK MODE BACKEND — "Off the Books" crime systems (only active when mode=='dark')
# ══════════════════════════════════════════════════════════════════════════════

# Drug ladder — street nicknames only. Higher tier = more money, more heat, higher
# Street Cred to unlock (gated gradually). base_yield = product units/day at production
# level 1; base_heat = heat added to that home/day at level 1; unit_value = $ (dirty)/unit.
DARK_DRUGS = {
    "reggie": {"name": "Weed",   "icon": "🌿", "tier": 1, "cred_req": 1,  "base_yield": 3, "base_heat": 3,  "unit_value": 110},
    "beans":  {"name": "Pills",  "icon": "💊", "tier": 2, "cred_req": 3,  "base_yield": 3, "base_heat": 5,  "unit_value": 220},
    "soft":   {"name": "Powder", "icon": "❄️", "tier": 3, "cred_req": 5,  "base_yield": 3, "base_heat": 8,  "unit_value": 370},
    "hard":   {"name": "Rock",   "icon": "🪨", "tier": 4, "cred_req": 7,  "base_yield": 3, "base_heat": 12, "unit_value": 590},
    "glass":  {"name": "Glass",  "icon": "🧊", "tier": 5, "cred_req": 9,  "base_yield": 4, "base_heat": 17, "unit_value": 910},
    "tar":    {"name": "Tar",    "icon": "🛢️", "tier": 6, "cred_req": 10, "base_yield": 4, "base_heat": 24, "unit_value": 1450},
}

# Drug-making EQUIPMENT — one bundled set per drug (no individual ingredients). Bought
# from the Fence with clean cash; a lab needs the matching set installed to operate.
# Drug-making SUPPLIES — consumable, one set per drug, bought from the Fence. You hand a
# set to a crew at a lab to start a batch (one batch = one supply set).
DARK_SUPPLIES = {
    "reggie": {"name": "Weed Supplies",   "icon": "🌱", "cost": 1_000},
    "beans":  {"name": "Pill Supplies",   "icon": "⚗️", "cost": 2_500},
    "soft":   {"name": "Powder Supplies", "icon": "🔪", "cost": 5_000},
    "hard":   {"name": "Rock Supplies",   "icon": "🍳", "cost": 9_000},
    "glass":  {"name": "Glass Supplies",  "icon": "🧪", "cost": 14_000},
    "tar":    {"name": "Tar Supplies",    "icon": "🛢️", "cost": 22_000},
}
DARK_BATCH_DAYS  = {1: 5, 2: 3, 3: 2}          # cook speed 1=slow,2=med,3=fast → days to finish
DARK_BATCH_HEAT  = {1: 0.8, 2: 1.3, 3: 2.2}    # heat/day multiplier by speed (faster = hotter)
DARK_BATCH_YIELD = 15                          # batch units = base_yield × this × crew factor
DARK_CREW_FEE_PCT = 0.10                        # crew's cut: 10% of a finished batch's street value
DARK_CREW_GRACE   = 3                           # days they'll wait for their cut before tempers flare
DARK_CREW_TEMPER_RATE = 25                      # temper gained per day once the grace period's up

# Cooking it yourself (the hands-on minigame): max units from a PERFECT hand-cook, scaled
# by your minigame score. Smaller than a crew batch — but instant, no crew, no cut.
DARK_SELFCOOK = {"reggie": 12, "beans": 12, "soft": 14, "hard": 15, "glass": 16, "tar": 18}
# A hand-cook costs a little CLEAN cash for ingredients (~30% of a perfect batch's street
# value) — NOT a Fence supply (those are for crew batches). Limited to once per day.
DARK_SELFCOOK_COST = {"reggie": 150, "beans": 325, "soft": 675, "hard": 1250, "glass": 2300, "tar": 4300}
DARK_SELFCOOK_PER_DAY = 3   # hand-cooks allowed per day
DARK_SLING_PER_DAY = 8      # hand-to-hand deals the player can work themselves per day
DARK_FIXER_WASH_CAP = 15000  # most the Fixer will quick-wash per day (until you get your own front)
DARK_FIXER_CUT = 0.15       # the Fixer's cut on a quick wash
# The Fixer's debt — triggered at Pusher (cred 3). A looming $1B you can never clear;
# each year he takes a cut of your GROSS take, locked on Winter 1, due Winter 28.
DARK_DEBT_TOTAL = 1_000_000_000
DARK_DEBT_RATE  = 0.15      # yearly bill = this × your gross take that year
DARK_DEBT_MISS_MULT = 1.10  # miss the deadline → total debt grows by this

def _dark_season(day):
    yd = (day - 1) % 112
    return yd // 28, (yd % 28) + 1, (day - 1) // 112 + 1   # (seasonIdx 0-3 Spring..Winter, seasonDay 1-28, year)

# ── Street Cred — the Kingpin rank ladder. `cred` (1–10) is your reputation level,
# earned by moving product + washing money (cred_xp). Each rank is a perk; the drug
# tree unlocks at the cred levels in DARK_DRUGS[*]["cred_req"] (1/3/5/7/9/10). ──
DARK_RANKS = [
    {"level": 1,  "name": "Corner Boy",  "xp": 0,     "perk": "Cooking Weed and working corners."},
    {"level": 2,  "name": "Slinger",     "xp": 280,   "perk": "Dealers move more product per day."},
    {"level": 3,  "name": "Pusher",      "xp": 850,   "perk": "💊 Pills unlocked."},
    {"level": 4,  "name": "Lieutenant",  "xp": 2250,  "perk": "Your name pulls weight — supplies cost less."},
    {"level": 5,  "name": "Supplier",    "xp": 4500,  "perk": "❄️ Powder unlocked."},
    {"level": 6,  "name": "Distributor", "xp": 7800,  "perk": "A cop on the payroll bleeds your heat down."},
    {"level": 7,  "name": "Boss",        "xp": 12000, "perk": "🪨 Rock unlocked."},
    {"level": 8,  "name": "Underboss",   "xp": 17500, "perk": "Dealers move even more; supplies cheaper still."},
    {"level": 9,  "name": "Shot Caller", "xp": 24500, "perk": "🧊 Glass unlocked."},
    {"level": 10, "name": "Kingpin",     "xp": 34000, "perk": "🛢️ Tar unlocked. You run this town."},
]

# Dark-only creator codes (redeemed through the same box, but ONLY work while mode=='dark').
DARK_CREATOR_CODES = {
    "dirtymoneyplease": {"desc": "Here's $10,000,000 in grimy, unmarked bills. 🧺", "dirty": 10_000_000},
    "cleanmoneyplease": {"desc": "Here's $10,000,000, squeaky clean. 💵", "cash": 10_000_000},
    "replayheists":     {"desc": "Every score's back on the board — pull 'em again. 🎬", "reset": "heists"},
}
for _r in DARK_RANKS:
    if _r["level"] >= 2:
        DARK_CREATOR_CODES[f"streetcred{_r['level']}"] = {
            "cred": _r["level"], "xp": _r["xp"],
            "desc": f"Fast-tracked to Street Cred {_r['level']} — {_r['name']}. 📈"}

def _dark_rank(level):
    return next((r for r in DARK_RANKS if r["level"] == level), DARK_RANKS[0])

def _dark_level_for_xp(xp):
    lvl = 1
    for r in DARK_RANKS:
        if xp >= r["xp"]: lvl = r["level"]
    return lvl

def _dark_dealer_cap(d):
    # Base 12/day, +4 at Slinger (2), +5 more at Underboss (8) → product moves fast as you rise.
    cred = d.get("cred", 1)
    return 12 + (4 if cred >= 2 else 0) + (5 if cred >= 8 else 0)

def _dark_supply_price(drug, d):
    base = (DARK_SUPPLIES.get(drug) or {}).get("cost", 0)
    cred = d.get("cred", 1)
    disc = (0.10 if cred >= 4 else 0.0) + (0.10 if cred >= 8 else 0.0)   # Lieutenant 10%, Underboss +10%
    return int(round(base * (1 - disc)))

def _dark_heat_bleed(d):
    # Distributor (6)+ keeps a cop on the payroll who quietly bleeds global heat each day.
    return 3 if d.get("cred", 1) >= 6 else 0

def _dark_award_cred(s, events):
    """Bump cred_xp → cred, firing a Fixer rank-up message for each level gained."""
    d = s["dark"]; before = d.get("cred", 1)
    after = _dark_level_for_xp(d.get("cred_xp", 0))
    if after > before:
        d["cred"] = after
        if d.get("heist_lockout", 0) > s.get("day", 1):   # ranking up shakes a post-bust score lockout
            d["heist_lockout"] = 0
            events.append({"type": "info", "text": "🎬 Word of your promotion travels — the heat off that botched score fades. The board's open again."})
        for lvl in range(before + 1, after + 1):
            r = _dark_rank(lvl)
            events.append({"type": "info", "text": f"📈 The Fixer: \"They're calling you a {r['name']} now.\" — {r['perk']}"})

def _dark_activate_debt(s):
    """The Fixer calls in his marker — triggered the day you open your own laundering front
    (you no longer need his quick-wash, so now he wants what he's owed)."""
    d = s["dark"]
    if d.get("debt_active"): return
    d["debt_active"] = True
    d["debt_balance"] = DARK_DEBT_TOTAL
    d["year_take"] = 0
    seasonIdx, _, year = _dark_season(s.get("day", 1))
    d["debt_first_year"] = year + 1 if seasonIdx == 3 else year   # open a front in Winter → first bill is next year
    d["fixer_event"] = {"kind": "intro"}

def _dark_debt_tick(s, events):
    """Per advanced day: settle last year's bill when the year rolls, lock the new one on Winter 1."""
    d = s["dark"]
    if not d.get("debt_active"): return
    seasonIdx, seasonDay, year = _dark_season(s.get("day", 1))
    by = d.get("debt_bill_year")
    if by is not None and year > by:                    # crossed past that bill's Winter 28 → settle
        if d.get("debt_paid", 0) < d.get("debt_bill", 0):
            d["debt_balance"] = round(d.get("debt_balance", 0) * DARK_DEBT_MISS_MULT)
            lost_dirty = d.get("dirty_money", 0); lost_units = sum((d.get("stash") or {}).values())
            d["dirty_money"] = 0; d["stash"] = {}
            d["fixer_event"] = {"kind": "goons", "dirty": lost_dirty, "units": lost_units, "balance": d["debt_balance"]}
            events.append({"type": "negative", "text": "💢 You came up short — the Fixer's goons cleaned you out (all dirty money + stash gone)."})
        d["debt_bill"] = 0; d["debt_paid"] = 0; d["debt_bill_year"] = None
    if seasonIdx == 3 and seasonDay == 1 and d.get("debt_bill_year") is None and year >= (d.get("debt_first_year") or year):
        bill = round(DARK_DEBT_RATE * d.get("year_take", 0))      # lock 15% of this year's gross take
        d["debt_bill"] = bill; d["debt_paid"] = 0; d["debt_bill_year"] = year; d["year_take"] = 0
        d["fixer_event"] = {"kind": "warn", "bill": bill}
        events.append({"type": "warning", "text": f"🕴️ The Fixer wants his cut: ${bill:,} by Winter 28. Don't be short."})

def _dark_watch_candidates(s):
    """Every operation Marsh could lock onto, paired with its current local heat. The strip
    club is a legit business — it's not on the list. Heat = how much each op is exposing itself."""
    d = s["dark"]; biz = d.get("biz") or {}; launder = d.get("launder") or {}; out = []
    for p in s["properties"]:
        if p.get("lab"):
            out.append((p["lab"].get("heat", 0), {"kind": "lab", "ref": p["id"],
                        "name": f"the {p.get('type', 'house')} in {p.get('neighborhood', 'town')}"}))
    for dl in d.get("dealers", []):
        out.append((dl.get("heat", 0), {"kind": "dealer", "ref": dl["id"], "name": f"your dealer {dl.get('name', '?')}"}))
    for key in DARK_LAUNDER:
        if biz.get(key):
            out.append((launder.get(key, {}).get("heat", 0), {"kind": "front", "ref": key, "name": f"the {DARK_LAUNDER[key]['name']}"}))
    return out

def _dark_watch_entity(s, w):
    """Resolve a watch descriptor to ('kind', the live object) — or None if it no longer exists."""
    if not w: return None
    d = s["dark"]; kind = w.get("kind"); ref = w.get("ref")
    if kind == "lab":
        p = next((x for x in s["properties"] if x.get("id") == ref and x.get("lab")), None)
        return ("lab", p) if p else None
    if kind == "dealer":
        dl = next((x for x in d.get("dealers", []) if x["id"] == ref), None)
        return ("dealer", dl) if dl else None
    if kind == "front":
        return ("front", (d.get("launder") or {}).get(ref)) if (d.get("biz") or {}).get(ref) else None
    return None

def _dark_watch_chance(heat):
    """Daily chance an op draws Marsh's eye: 25%+ heat → 10%, +10% per extra 25% tier (100% → 40%)."""
    h = min(int(heat or 0), 100)
    return (h // 25) * 0.10 if h >= DARK_WATCH_MIN_HEAT else 0.0

def _dark_op_dirty(s, w):
    """Is the watched op actively running something illegal right now? Shutting it down (lab: no
    crew/no batch · dealer: paused · front: washing off) makes it clean, so a raid finds nothing."""
    ent = _dark_watch_entity(s, w)
    if not ent or ent[1] is None: return False
    kind, obj = ent
    if kind == "lab":   return bool(obj["lab"].get("crew_id")) or bool(obj["lab"].get("batch"))
    if kind == "dealer": return not obj.get("paused") and sum((obj.get("inventory") or {}).values()) > 0
    if kind == "front": return bool(obj.get("manager")) and obj.get("rate", 0) > 0
    return False

def _dark_first_name(name):
    """Just the first name off a full name for an early clue: \"Tony 'Bull' Russo\" → 'Tony'."""
    parts = (name or "").strip().split()
    return parts[0] if parts else "someone"

def _dark_build_clues(s, w):
    """Ordered clue pool for the watched op, vague → specific. Later clues actually pin down
    which one it is, so with multiple ops of a kind the details (size, product, name) triangulate."""
    d = s["dark"]; ent = _dark_watch_entity(s, w); kind = (w or {}).get("kind")
    if not ent or ent[1] is None: return []
    _, obj = ent
    if kind == "lab":
        lab = obj["lab"]; crew = _dark_crew_by_id(d, lab.get("crew_id"))
        members = _dark_crew_members(d, crew) if crew else []
        size = len(members); drug = (DARK_DRUGS.get(lab.get("drug")) or {}).get("name", "something")
        hood = obj.get("neighborhood", "town"); ptype = obj.get("type", "house")
        cook = members[0].get("name") if members else None
        crew_desc = "a one-man operation" if size == 1 else (f"a crew of about {size}" if size else "a small crew")
        cl = ["He's working a house, not a corner — somebody's cooking for you.",
              f"Word is it's {crew_desc} running it.",
              f"Whatever they're making in there, it's {drug}."]
        if cook:
            cl.append(f"Marsh got a first name off an informant — the cook goes by {_dark_first_name(cook)}. No last name yet.")
            cl.append(f"He's got the cook's full name now: {cook}.")
        cl.append(f"He's got the address — it's the {ptype} over in {hood}.")
        return cl
    if kind == "dealer":
        inv = obj.get("inventory") or {}
        main = max(inv, key=inv.get) if inv else None
        drug = (DARK_DRUGS.get(main) or {}).get("name", "product"); name = obj.get("name", "your guy")
        return ["He's watching a corner — a street dealer of yours, not a house.",
                f"The guy's mostly moving {drug}.",
                f"Marsh has a first name for him — {_dark_first_name(name)}.",
                f"It's {name}. Marsh has his whole routine down."]
    if kind == "front":
        key = w.get("ref"); meta = DARK_LAUNDER.get(key, {})
        fname = meta.get("name", "a front"); ftype = meta.get("kind_label", fname)
        return ["He pulled financial records on one of your cash businesses.",
                "An accountant's flagged it — the numbers at one of your fronts don't add up.",
                f"It's a {ftype} — a cash-heavy spot.",
                f"He's subpoenaed the books on {fname}."]
    return []

def _dark_clue_reveal(d, n=1):
    """Surface the next n clues from the watched op's pool. Returns the newly revealed lines."""
    w = d.get("watch")
    if not w: return []
    pool = w.get("clues") or []; found = w.get("found", 0)
    new = pool[found:found + n]
    w["found"] = min(len(pool), found + n)
    return new

def _dark_clues_done(d):
    w = d.get("watch") or {}
    return bool(w.get("clues")) and w.get("found", 0) >= len(w["clues"])

def _dark_lock_watch(s, w, events=None):
    """Marsh commits to one op: build its clue pool, roll a hidden 5–10 day raid pace, start the
    countdown (the top-right Heat) at zero."""
    d = s["dark"]
    w = dict(w); w["clues"] = _dark_build_clues(s, w); w["found"] = 0
    d["watch"] = w; d["watch_known"] = False
    days = random.randint(DARK_RAID_MIN_DAYS, DARK_RAID_MAX_DAYS)
    d["raid_days"] = days; d["raid_pace"] = 100.0 / days; d["heat"] = 0
    d["lawyered"] = False; d["moved"] = False
    if events is not None:
        events.append({"type": "warning", "text": f"🕵️ The Fixer: \"{random.choice(DARK_MARSH_LOCK_LINES)}\""})

def _dark_trigger_hunt(s, bump=40):
    """Story-beat shortcut: drag Marsh's attention onto your hottest op (or shove the countdown
    forward if he's already locked on). Used by sting/betrayal events."""
    d = s["dark"]
    if d.get("cred", 1) < 2: return
    if not d.get("watch"):
        cands = [(h, w) for (h, w) in _dark_watch_candidates(s) if h > 5]
        if not cands: return
        cands.sort(key=lambda x: x[0], reverse=True)
        _dark_lock_watch(s, cands[0][1], None)
    d["heat"] = min(99, d.get("heat", 0) + bump)   # jump the clock, but never auto-raid the same day

def _dark_apply_local_heat(s, n):
    """Lay `n` heat on a RANDOM operation you actually run (lab / dealer / front). This is how
    events 'draw heat' under the new model — it makes that op likelier to be Marsh's next target,
    rather than touching the global raid countdown. No ops → the heat has nowhere to land."""
    if not n: return
    d = s["dark"]; biz = d.get("biz") or {}; ops = []
    ops += [p["lab"] for p in s["properties"] if p.get("lab")]
    ops += list(d.get("dealers", []))
    ops += [v for k, v in (d.get("launder") or {}).items() if biz.get(k)]
    if not ops: return
    o = random.choice(ops); o["heat"] = max(0, min(100, o.get("heat", 0) + n))

def _dark_do_raid(s, events):
    """The countdown hit 100 — Marsh raids the op he's been building a case on. If you shut it
    down in time it's clean and you walk; if it's still running it gets drained. A lawyer beats
    the charge (op survives), and moving product saves loose cash/stash."""
    d = s["dark"]; lawyered = d.get("lawyered"); moved = d.get("moved"); hit = []
    w = d.get("watch"); ent = _dark_watch_entity(s, w); dirty = _dark_op_dirty(s, w); op_saved = False
    if ent and ent[1] is not None and dirty:
        kind, obj = ent
        if lawyered:
            op_saved = True   # the charge that would've taken the operation gets beaten
        elif kind == "lab":
            cid = obj["lab"].get("crew_id")
            d["roster"] = [m for m in d.get("roster", []) if m.get("crew_id") != cid]
            d["crews"]  = [c for c in d.get("crews", []) if c["id"] != cid]
            s["properties"] = [x for x in s["properties"] if x["id"] != obj["id"]]
            hit.append("the lab, its crew, and all the product")
        elif kind == "dealer":
            d["dealers"] = [x for x in d.get("dealers", []) if x["id"] != obj["id"]]
            hit.append(f"your dealer {obj.get('name', '?')} (and what he was holding)")
        elif kind == "front":
            key = w["ref"]; bank = obj.get("bank", 0)
            (d.get("biz") or {})[key] = False; (d.get("launder") or {}).pop(key, None)
            if d.get("phil") and d["phil"].get("front") == key: d["phil"]["front"] = None
            hit.append(f"the {DARK_LAUNDER.get(key, {}).get('name', 'front')}" + (f" + ${bank:,} uncollected" if bank else ""))
    if not moved:
        grab = d.get("dirty_money", 0) // (2 if lawyered else 1)
        if grab: d["dirty_money"] -= grab; hit.append(f"${grab:,} loose dirty cash")
        if d.get("stash"): d["stash"] = {}; hit.append("your stash")
    where = (w or {}).get("name", "your operation")
    if not dirty and ent and ent[1] is not None:
        events.append({"type": "info", "text": f"🚨 RAID — {DARK_DETECTIVE} hit {where}… and found a clean, legit operation. You'd shut it down in time. He leaves empty-handed."})
    elif hit:
        extra = " Your lawyer beat the main charge — the operation survives." if op_saved else ""
        events.append({"type": "negative", "text": f"🚨 RAID — {DARK_DETECTIVE} hit {where}. Lost: {', '.join(hit)}.{extra}"})
    else:
        events.append({"type": "info", "text": f"🚨 The raid came up empty — {DARK_DETECTIVE} leaves with nothing."})
    # Case closes; Marsh backs off for a cooldown before he can lock onto anything new.
    d["watch"] = None; d["watch_known"] = False; d["heat"] = 0
    d["lawyered"] = False; d["moved"] = False; d["raid_pace"] = 0; d["raid_days"] = 0
    d["raid_cooldown"] = s["day"] + DARK_RAID_COOLDOWN

def _dark_hunt_tick(s, events):
    """End-of-day Hunt: pick a target (heat-tier roll), run the raid countdown, drip clues."""
    d = s["dark"]
    if d.get("cred", 1) < 2:        # still small-time — no case builds
        if d.get("watch"): d["watch"] = None
        d["heat"] = 0; return
    # Post-raid cooldown: he's looking the other way for a few days.
    if s["day"] < d.get("raid_cooldown", 0):
        d["heat"] = 0; return
    w = d.get("watch")
    if w and not _dark_watch_entity(s, w):   # the watched thing is fully gone (dismantled/sold)
        d["watch"] = None; d["heat"] = 0; w = None
    if not w:
        # Each Watched rolls to draw his eye; the hottest one that triggers becomes the target.
        triggered = [(h, c) for (h, c) in _dark_watch_candidates(s) if random.random() < _dark_watch_chance(h)]
        if triggered:
            triggered.sort(key=lambda x: x[0], reverse=True)
            _dark_lock_watch(s, triggered[0][1], events)
        else:
            d["heat"] = 0
        return
    # ── He's locked on: the countdown climbs (lie-low buys a day), clues sharpen, then the raid. ──
    if d.get("lying_low"):
        events.append({"type": "info", "text": f"🛌 You lay low — the case sat still today. {DARK_DETECTIVE} made no progress."})
    else:
        step = d.get("raid_pace", 12) * random.uniform(0.85, 1.15)
        d["heat"] = min(100, d.get("heat", 0) + step)
    h = d.get("heat", 0)
    # Clues sharpen with the countdown: a guaranteed clue roughly every 20%.
    target = min(len(w.get("clues", [])), int(h // 20))
    if w.get("found", 0) < target:
        new = _dark_clue_reveal(d, target - w.get("found", 0))
        if new: events.append({"type": "info", "text": "🗂️ New lead in the case file: " + new[-1]})
    # Connected crew whisper a clue.
    if not _dark_clues_done(d) and any(m.get("trait") == "connected" for m in d.get("roster", [])) \
            and random.random() < DARK_CLUE_CREW_CHANCE:
        new = _dark_clue_reveal(d, 1)
        if new: events.append({"type": "info", "text": "👂 One of your connected people heard something: " + new[-1]})
    # A dealer flags a weird buyer — only when the target actually is a dealer.
    if not _dark_clues_done(d) and w.get("kind") == "dealer" and random.random() < DARK_CLUE_DEAL_CHANCE:
        new = _dark_clue_reveal(d, 1)
        if new: events.append({"type": "warning", "text": "🧢 One of your dealers flagged a buyer who smelled like a cop: " + new[-1]})
    # Free ambient news headline.
    if not _dark_clues_done(d) and random.random() < DARK_CLUE_NEWS_CHANCE:
        new = _dark_clue_reveal(d, 1)
        if new: events.append({"type": "info", "text": random.choice(DARK_NEWS_HEADLINES) + " " + new[-1]})
    if d.get("heat", 0) >= 100:
        _dark_do_raid(s, events)

# ══════════════════════════════════════════════════════════════════════════════
#  THE STRIP CLUB — a LEGIT business you actively run. Dancers + the bar pull in
#  modest CLEAN income (you pay the staff out of it); bouncers keep heat and trouble
#  down; nightly incidents freeze the club until handled; and the VIP room is a
#  read-the-patron minigame that buys you intel on the Hunt.
# ══════════════════════════════════════════════════════════════════════════════
DARK_CLUB_DANCER_CAP  = 6
DARK_CLUB_BOUNCER_CAP = 4
DARK_CLUB_COMPROMISE  = {"cop": 8_000, "da": 18_000}
DARK_CLUB_NAMES = ["Roxy", "Cherry", "Lola", "Diamond", "Jade", "Bambi", "Crystal", "Star",
                   "Ginger", "Mercedes", "Candy", "Vixen", "Destiny", "Angel", "Porsha", "Sapphire"]
DARK_CLUB_PATRONS = {"cop": ["a precinct sergeant", "a vice detective", "a beat captain"],
                     "da":  ["an assistant DA", "a city councilman", "a sitting judge"]}
DARK_CLUB_WHY = ["putting herself through nursing school", "saving to open her own salon",
                 "a single mom with two kids at home", "new in town and dead broke",
                 "paying off her brother's debts", "dancing her way out of a bad scene",
                 "in it for the money and the attention", "an art student who needs the rent"]
DARK_CLUB_QUIRKS = {
    "viral":     {"name": "Goes Viral",      "icon": "📱", "desc": "Huge online following — packs the room, but the attention runs hot."},
    "student":   {"name": "Law Student",     "icon": "📚", "desc": "Sharp and discreet — reads people well in the VIP room."},
    "heatmag":   {"name": "Trouble Follows", "icon": "🌶️", "desc": "Pulls big tips — and the wrong kind of attention."},
    "denmother": {"name": "Den Mother",      "icon": "🧁", "desc": "Keeps the other girls happy — lifts the whole floor's mood."},
    "showpony":  {"name": "Showstopper",     "icon": "🎀", "desc": "A signature act that owns the main stage."},
}
DARK_CLUB_SPECS = {"stage": "Stage", "floor": "Floor", "vip": "VIP"}
# Star ladder: (min level, title, icon). A dancer's draw climbs with her level (to cap 7),
# and titles carry perks in the tick — Headliners cool the room, Stars+ build the name faster.
DARK_CLUB_TITLES = [(1, "Rookie", "🌱"), (2, "Regular", "💃"), (4, "Headliner", "✨"),
                    (6, "Star", "🌟"), (8, "Legend", "👑")]
def _dark_club_title(level):
    t = DARK_CLUB_TITLES[0]
    for entry in DARK_CLUB_TITLES:
        if level >= entry[0]: t = entry
    return t   # (min_level, name, icon)
# Personal goals — each dancer is working toward something; she fills a goal bar as she
# works, and hitting it triggers a milestone choice (send-off / House Mom / re-sign).
DARK_CLUB_GOALS = ["open her own salon", "pay off her student loans", "buy her mom a house",
                   "save a real nest egg", "get her kid into a good school", "fund her own business",
                   "get out of the life clean", "put a down payment on a place of her own",
                   "bankroll her music career", "finish her degree"]
DARK_BOUNCER_NAMES = ["Tank", "Diesel", "Bruno", "Moose", "Vince", "Knuckles", "Tiny", "Hammer",
                      "Rocco", "Sal", "Big Mike", "Curtis", "Ox", "Dutch"]
DARK_BOUNCER_ARCH = {
    "excon":  {"name": "Ex-Con",        "icon": "⛓️", "desc": "All muscle — but the badge knows his face (a little extra heat)."},
    "expat":  {"name": "Ex-Cop",        "icon": "👮", "desc": "Spots an undercover from across the room. Costs more."},
    "gentle": {"name": "Gentle Giant",  "icon": "🧸", "desc": "Calms trouble without a scene — keeps heat down."},
    "pro":    {"name": "Pro",           "icon": "🕶️", "desc": "Solid, reliable all-rounder."},
}
# Each upgrade is tiered: (label, cost) per tier. All bought with CLEAN cash.
DARK_CLUB_UPGRADES = {
    "stage":    {"name": "Main Stage",       "icon": "🎤", "desc": "Lifts how much your dancers pull each night.",
                 "tiers": [("LED stage & new poles", 60_000), ("Mirrored multi-pole stage", 140_000)]},
    "bar":      {"name": "The Bar",          "icon": "🍸", "desc": "Opens a drink-sales income stream you tune yourself.",
                 "tiers": [("Build a full bar", 45_000), ("Top-shelf cocktail lounge", 120_000)]},
    "vip":      {"name": "VIP / Champagne Room", "icon": "🥂", "desc": "Where you read connected patrons for intel on the Hunt.",
                 "tiers": [("Private champagne room", 80_000), ("VIP balcony", 180_000)]},
    "sound":    {"name": "Sound & Lighting", "icon": "🔊", "desc": "Boosts reputation and kills dead nights.",
                 "tiers": [("Pro rig + resident DJ", 50_000)]},
    "security": {"name": "Security Suite",   "icon": "📹", "desc": "Backs your bouncers, cools heat, prevents some incidents.",
                 "tiers": [("Cameras & an office", 40_000), ("Full surveillance", 95_000)]},
    "license":  {"name": "Liquor License",   "icon": "📜", "desc": "A clean legal face — lowers the club's baseline heat.",
                 "tiers": [("Get it on the books", 55_000)]},
    "back":     {"name": "Back Entrance",    "icon": "🚪", "desc": "Discreet in-and-out for VIPs — less heat from the back rooms.",
                 "tiers": [("Private parking & door", 35_000)]},
}
DARK_BAR_PRICE = {
    "water": {"name": "Watered down", "mult": 1.55, "rep": -1, "desc": "Fat margins — but a sharp customer might notice."},
    "std":   {"name": "Standard pour", "mult": 1.0,  "rep": 0,  "desc": "Honest drinks, honest money."},
    "top":   {"name": "Top-shelf",    "mult": 0.7,  "rep": +1, "desc": "Thin margins, but the room loves it."},
}
DARK_BARTENDER_NAMES = ["Tony", "Gina", "Rick", "Manny", "Lou", "Dom"]
# VIP minigame patron archetypes. `topics` = the angle that gets them talking;
# `reward` = what extracting their intel does. `risk` rises the deeper/wronger you push.
DARK_VIP_TYPES = {
    "beat":      {"name": "an off-duty beat cop", "tell": "keeps glancing at the door like he's still on shift",
                  "topic": "the neighborhood", "reward": "cool", "susp": 3},
    "vice":      {"name": "a vice detective",     "tell": "nurses one drink and watches the room more than the stage",
                  "topic": "open cases",    "reward": "watch", "susp": 7},
    "da":        {"name": "an assistant DA",      "tell": "name-drops the courthouse and flashes an expensive watch",
                  "topic": "the courthouse", "reward": "leverage_da", "susp": 5},
    "snitch":    {"name": "a nervous informant",  "tell": "sits with his back to the wall and won't give his name",
                  "topic": "street talk",    "reward": "sell", "susp": 4},
    "undercover":{"name": "a friendly regular",   "tell": "asks a few too many friendly questions about the owner",
                  "topic": "the business",   "reward": "trap", "susp": 9},
}
DARK_VIP_TOPICS = {"the neighborhood": "beat", "open cases": "vice", "the courthouse": "da",
                   "street talk": "snitch", "the business": "undercover"}

# ── THE CAST: six fixed, hand-written dancers. You bring them on one at a time;
#    once all six are in, the roster's closed (no more hiring, no firing). Each has a
#    3-beat scripted story arc with moral choices. A beat fires on a nightly roll and
#    PAUSES that dancer (she stops earning) until you handle it — separate from the
#    whole-club incidents (those live on c["event"] and freeze everything). ──────────
DARK_DANCERS = {
    "roxy": {"name": "Roxy", "draw": 4, "charm": 3, "quirk": "denmother", "cost": 24000,
        "blurb": "Pushing 40, fifteen years on the pole. Breaks in the new girls and keeps the peace. Saving to buy her own bar and get out with her dignity.",
        "arc": [
            {"icon": "🦵", "text": "Roxy's knee blew out mid-set — she's backstage on the floor, gritting through it.",
             "choices": ["Pay for the surgery", "Hand her painkillers, keep her working", "Move her to training the new girls"]},
            {"icon": "👯", "text": "A newer girl is openly gunning for Roxy's spot, running her mouth backstage.",
             "choices": ["Back Roxy", "Side with the young blood", "Make them work it out"]},
            {"icon": "🍸", "text": "Roxy found a little bar for sale. She's asking you to cosign the loan — her way out of the life.",
             "choices": ["Invest in her dream", "Talk her out of it", "Keep her on as House Mom"]},
        ]},
    "jade": {"name": "Jade", "draw": 3, "charm": 4, "quirk": "student", "cost": 18000,
        "blurb": "Twenty-two, pre-law, dancing nights to cover tuition — and terrified of being recognized. Sharp, guarded, always watching.",
        "arc": [
            {"icon": "🎓", "text": "A regular at the rail just locked eyes with Jade — it's her law professor.",
             "choices": ["Help her slip out the back", "Do nothing", "Lean on the professor"]},
            {"icon": "📸", "text": "Someone snapped a photo of Jade and is threatening to send it to her school unless they're paid.",
             "choices": ["Pay the blackmail", "Send a bouncer to handle it", "Call their bluff"]},
            {"icon": "⚖️", "text": "Jade's days from passing the bar and leaving the life for good. She's come to say goodbye.",
             "choices": ["Throw her a real sendoff", "Guilt her into staying"]},
        ]},
    "bambi": {"name": "Brittany “Bambi”", "draw": 5, "charm": 3, "quirk": "heatmag", "cost": 30000,
        "blurb": "Early twenties, your biggest draw when she's on — and a liability when she's not. She's fighting a pill habit.",
        "arc": [
            {"icon": "💊", "text": "Bambi showed up wrecked — pinned pupils, can barely stand. The crowd's already filling in.",
             "choices": ["Send her home to sober up", "Push her on stage anyway", "Cut her off the party crowd"]},
            {"icon": "🚬", "text": "You clocked it — Bambi's dealer has been working your club, keeping her hooked.",
             "choices": ["86 the dealer for good", "Look the other way", "Quietly buy out her debt"]},
            {"icon": "🏥", "text": "Bambi OD'd in the dressing room. She pulled through, scared straight, and is begging for help.",
             "choices": ["Pay for proper rehab", "Get her into outpatient help", "You can't keep carrying her"]},
        ]},
    "mercedes": {"name": "Mercedes", "draw": 5, "charm": 3, "quirk": "showpony", "cost": 28000,
        "blurb": "Late twenties, the top earner, always running an angle. Cunning, charming, loyal to cash first.",
        "arc": [
            {"icon": "💸", "text": "You caught Mercedes skimming from the bar take — bold as you like.",
             "choices": ["Dock her pay & warn her", "Take a cut and say nothing", "Make her your collections muscle"]},
            {"icon": "💋", "text": "A rival club is dangling double the money to poach Mercedes.",
             "choices": ["Match the offer", "Let her walk", "Try to earn her loyalty"]},
            {"icon": "🐳", "text": "Mercedes says she's been grooming a whale for a massive private party — the score of the year. She needs you to trust her play.",
             "choices": ["Let her run it", "Keep her on a short leash"]},
        ]},
    "lola": {"name": "Lola", "draw": 3, "charm": 3, "quirk": None, "cost": 18000,
        "blurb": "Mid-twenties, sweet and a little reckless, always tangled up with the wrong man. Warm, big-hearted, in over her head.",
        "arc": [
            {"icon": "💢", "text": "Lola's violent ex is at the door, drunk and raging, demanding to see her.",
             "choices": ["Have the bouncers walk him out", "Quietly ban him", "Let her handle it herself"]},
            {"icon": "🩸", "text": "Lola's new man is leaning on her — and now on you — for a cut of the club's money.",
             "choices": ["Shut it down hard", "Pay him off", "Let him hang around"]},
            {"icon": "🥀", "text": "Lola's planning to run off with him — and you both know how that story ends.",
             "choices": ["Stage an intervention", "Give her cash to get away clean", "Let her go"]},
        ]},
    "destiny": {"name": "Destiny", "draw": 3, "charm": 2, "quirk": "viral", "cost": 16000,
        "blurb": "Twenty, phone always out, wants to be famous more than anything. Bubbly, attention-hungry, a little naive. Her chihuahua keeps turning up backstage.",
        "arc": [
            {"icon": "📱", "text": "A clip of Destiny's set blew up overnight — there's a line forming around the block.",
             "choices": ["Lean in — promote the club", "Keep it low-key", "Monetize it properly"]},
            {"icon": "🤳", "text": "A promoter wants Destiny for a string of out-of-town appearances.",
             "choices": ["Let her go do it", "Hold her to her shifts", "Negotiate a cut"]},
            {"icon": "🌟", "text": "A manager wants to take Destiny solo and make her famous.",
             "choices": ["Bless her exit", "Make her your headline face", "Warn her it's a scam"]},
        ]},
}
DARK_DANCER_ORDER = ["destiny", "jade", "lola", "roxy", "mercedes", "bambi"]

def _dark_make_dancer(c, key):
    spec = DARK_DANCERS[key]
    c["next_id"] = c.get("next_id", 1) + 1
    return {"id": c["next_id"] - 1, "key": key, "name": spec["name"], "draw": spec["draw"],
            "charm": spec["charm"], "quirk": spec.get("quirk"), "loyalty": 60,
            "level": 1, "xp": 0, "wage": spec["draw"] * 65, "manager": False,
            "beat": 0, "event": None, "away_until": None, "done": False}

def _dark_bouncer(c):
    c["next_id"] = c.get("next_id", 1) + 1
    arch = random.choice(list(DARK_BOUNCER_ARCH))
    muscle = random.randint(2, 4); eye = random.randint(1, 3)
    if arch == "excon":  muscle = min(5, muscle + 1)
    if arch == "expat":  eye = min(5, eye + 2)
    if arch == "gentle": eye = min(5, eye + 1)
    return {"id": c["next_id"] - 1, "name": random.choice(DARK_BOUNCER_NAMES), "arch": arch,
            "muscle": muscle, "eye": eye, "loyalty": random.randint(50, 75),
            "level": 1, "assign": "off", "wage": 130 + muscle * 35}

def _dark_club_refresh(c):
    # Recruits = the cast members you haven't brought on yet (and who haven't left).
    hired = set(c.get("roster_keys", []))
    c["recruits"] = [k for k in DARK_DANCER_ORDER if k not in hired]
    while len(c.get("bouncer_recruits", [])) < 2:
        c["bouncer_recruits"].append(_dark_bouncer(c))

def _dark_club_migrate(c):
    """Backfill the richer club schema onto saves made before the operations overhaul."""
    c.setdefault("rep", 45); c.setdefault("heat", 0); c.setdefault("next_id", 1)
    c.setdefault("dancers", []); c.setdefault("recruits", []); c.setdefault("leverage", [])
    c.setdefault("bouncers", []); c.setdefault("bouncer_recruits", []); c.setdefault("roster_keys", [])
    c.setdefault("upgrades", {k: 0 for k in DARK_CLUB_UPGRADES})
    for k in DARK_CLUB_UPGRADES: c["upgrades"].setdefault(k, 0)
    if c.get("security"): c["upgrades"]["security"] = max(c["upgrades"]["security"], min(2, c.pop("security")))
    c.setdefault("bar", {"price": "std", "bartender": None, "signature": None})
    c.setdefault("door", "balanced")
    c.setdefault("event", None); c.setdefault("vip_patron", False); c.setdefault("vip_game", None)
    c.setdefault("vip_day", 0); c.setdefault("last_gross", 0); c.setdefault("last_wages", 0); c.setdefault("last_net", 0)
    c.pop("lounge_offer", None); c.pop("lounge_day", None)
    # Saves made before the named-cast overhaul had randomly-generated dancers — reset to the
    # fresh cast (a clean slate for the scripted arcs).
    if any("key" not in x for x in c.get("dancers", [])):
        c["dancers"] = []; c["roster_keys"] = []
    for x in c.get("dancers", []):
        x.setdefault("charm", 2); x.setdefault("loyalty", 60); x.setdefault("level", 1); x.setdefault("xp", 0)
        x.setdefault("wage", x.get("draw", 1) * 65); x.setdefault("manager", False)
        x.setdefault("beat", 0); x.setdefault("event", None); x.setdefault("away_until", None); x.setdefault("done", False)
        for dead in ("spec", "assign", "why", "goal", "goal_prog", "stamina", "mood"): x.pop(dead, None)
    _dark_club_refresh(c)

def _dark_club_init(d):
    c = {"rep": 45, "heat": 0, "next_id": 1, "dancers": [], "recruits": [], "roster_keys": [], "leverage": [],
         "bouncers": [], "bouncer_recruits": [], "upgrades": {k: 0 for k in DARK_CLUB_UPGRADES},
         "bar": {"price": "std", "bartender": None, "signature": None}, "door": "balanced",
         "event": None, "vip_patron": False, "vip_game": None, "vip_day": 0,
         "last_gross": 0, "last_wages": 0, "last_net": 0}
    _dark_club_refresh(c)
    d["club"] = c

def _dark_club_secrating(c):
    """Effective security: bouncers on the door/floor + the camera suite."""
    r = sum(b.get("muscle", 1) for b in c.get("bouncers", []) if b.get("assign") in ("door", "floor"))
    r += 2 * c.get("upgrades", {}).get("security", 0)
    if c.get("door") == "strict": r += 2
    if c.get("door") == "loose":  r -= 2
    return max(0, r)

def _dark_club_workers(c, day=None):
    """Dancers actually on the floor earning tonight — excludes the House Mom, anyone
    paused by her own story event, and anyone away for a few days."""
    out = []
    for x in c.get("dancers", []):
        if x.get("manager") or x.get("event"): continue
        if day is not None and x.get("away_until") and day < x["away_until"]: continue
        out.append(x)
    return out

def _dark_club_tick(s, events):
    """Each advanced day: clean income (net of wages), reputation, heat/raid, dancer wear,
    the weekly VIP patron, and a chance of a club incident that freezes the floor."""
    d = s["dark"]
    if not (d.get("biz") or {}).get("strip_club"): return
    c = d.get("club")
    if not c: _dark_club_init(d); c = d["club"]
    _dark_club_migrate(c)
    if c.get("event"):                 # an unhandled incident: the club is shut until you deal with it
        return
    up = c["upgrades"]; rep = c.get("rep", 0); day = s["day"]
    # ── Dancers come back from being sidelined a few days. ──
    for x in c.get("dancers", []):
        if x.get("away_until") and day >= x["away_until"]:
            x["away_until"] = None
            events.append({"type": "info", "text": f"💃 {x['name']} is back on the floor."})
    workers = _dark_club_workers(c, day)
    managers = [x for x in c.get("dancers", []) if x.get("manager")]
    # ── Gross take: dancers on the floor (× reputation) + bar sales + a House Mom lift. ──
    stage_mult = 1 + 0.18 * up.get("stage", 0)
    gross = 0.0
    for x in workers:
        gross += x.get("draw", 1) * 175 * (0.45 + rep / 200.0) * stage_mult
    if managers: gross *= 1.15                       # a House Mom keeps the floor tight
    if up.get("bar", 0) > 0:
        pr = DARK_BAR_PRICE.get(c["bar"].get("price", "std"), DARK_BAR_PRICE["std"])
        bar_inc = up["bar"] * 220 * pr["mult"] * (0.5 + rep / 150.0)
        if c["bar"].get("bartender"): bar_inc *= 1.15
        gross += bar_inc
    gross = round(gross)
    # ── Wages: you pay the dancers, the House Mom, and the door out of the take. ──
    wages = sum(x.get("wage", x.get("draw", 1) * 65) for x in workers)
    wages += sum(x.get("wage", 250) for x in managers)
    wages += sum(b.get("wage", 150) for b in c.get("bouncers", []) if b.get("assign") != "off")
    if up.get("bar", 0) > 0 and c["bar"].get("bartender"): wages += 200
    net = gross - wages
    s["cash"] = s.get("cash", 0) + net          # CLEAN money — a legit business
    c["last_gross"], c["last_wages"], c["last_net"] = gross, wages, net
    # ── Dancer progression: loyalty + XP → levels (draw grows, title climbs). ──
    denmother = any(x.get("quirk") == "denmother" for x in workers)
    for x in workers:
        x["loyalty"] = min(100, x.get("loyalty", 60) + (2 if denmother else 1))
        x["xp"] = x.get("xp", 0) + 1
        if x["xp"] >= x.get("level", 1) * 4:
            x["xp"] = 0; x["level"] = x.get("level", 1) + 1
            if x.get("draw", 1) < 7: x["draw"] += 1
            x["wage"] = x.get("wage", x["draw"] * 65) + 25
            ttl = _dark_club_title(x["level"])
            events.append({"type": "info", "text": f"{ttl[2]} {x['name']} leveled up to {ttl[1]} — she's pulling bigger crowds now."})
    # ── Reputation (Stars+ build the name faster). ──
    pr_rep = DARK_BAR_PRICE.get(c["bar"].get("price", "std"), {}).get("rep", 0) if up.get("bar", 0) > 0 else 0
    star_rep = sum(1 for x in workers if x.get("level", 1) >= 6)
    if workers:
        c["rep"] = min(100, rep + 2 + up.get("sound", 0) + pr_rep + star_rep)
    else:
        c["rep"] = max(0, rep - 1)
    # ── Heat (Headliners+ pull a classier crowd that cools the room). ──
    secr = _dark_club_secrating(c)
    classy = sum(1 for x in workers if x.get("level", 1) >= 4)
    base = 6 + sum(1 for x in workers if x.get("quirk") in ("heatmag", "viral")) - classy
    base -= 1 if up.get("back", 0) else 0
    base -= 2 if up.get("license", 0) else 0
    # Club heat = how much it's drawing the vice squad's eye (feeds Marsh's watch — a vice raid
    # now only comes if he picks the club and you don't cool it). Capped at 100.
    c["heat"] = min(100, max(0, c.get("heat", 0) + max(0, base - min(secr, 7))))
    bent = sum(1 for L in c.get("leverage", []) if L.get("kind") == "bent_cop")
    if bent: d["heat"] = max(0, d.get("heat", 0) - 3 * bent)
    # ── A connected patron drifts into the VIP room (the intel minigame). ──
    if up.get("vip", 0) > 0 and not c.get("vip_patron") and not c.get("vip_game") and (s["day"] - c.get("vip_day", 0)) >= 5:
        c["vip_patron"] = True; c["vip_day"] = s["day"]
        events.append({"type": "info", "text": "🥂 Someone connected just slipped into the VIP room — go read them (Biz → Strip Club)."})
    # ── ONE drama per night: either a dancer's story beat (pauses just her) OR a
    #    whole-club operational incident (freezes everything). Never both — so the two
    #    systems can't collide. The whole-club incident only fires if no dancer beat does. ──
    arc_of = lambda x: DARK_DANCERS.get(x.get("key", ""), {}).get("arc", [])
    story_pool = [x for x in c.get("dancers", [])
                  if not x.get("manager") and not x.get("done") and not x.get("event")
                  and not (x.get("away_until") and day < x["away_until"])
                  and x.get("beat", 0) < len(arc_of(x))]
    # Operational incidents come first and scale HARD with how weak your door is:
    # no security ⇒ ~28%/night; a well-staffed, trained door ⇒ ~5%.
    inc_chance = max(0.05, 0.28 - 0.03 * secr)
    story_chance = 0.18 if story_pool else 0.0
    roll = random.random()
    if roll < inc_chance:                          # a whole-club operational incident
        _dark_club_spawn_event(s, c, events)
    elif roll < inc_chance + story_chance:         # else a dancer's story advances tonight
        x = random.choice(story_pool)
        beat = arc_of(x)[x.get("beat", 0)]
        x["event"] = {"icon": beat["icon"], "text": beat["text"], "choices": list(beat["choices"])}
        events.append({"type": "warning", "text": f"{beat['icon']} {x['name']} has pulled you aside — she's off the floor until you hear her out (Biz → Strip Club)."})

# ── Club incidents: each freezes the floor until you tap "Handle it". Outcomes scale
#    with your bouncers (security rating) and what you've built. ────────────────────
DARK_CLUB_EVENTS = {
    "fight":     {"icon": "🥊", "tag": "bad",    "text": "A brawl just kicked off by the main stage — drinks flying, a girl screaming.",
                  "choices": ["Send the bouncers in", "Let it burn out", "86 the whole table"]},
    "vice":      {"icon": "🕵️", "tag": "bad",    "text": "A man at the bar keeps flashing a badge and asking your dancers about the back rooms.",
                  "choices": ["Comp him and smooth it over", "Throw him out", "Make a call (leverage)"]},
    "underage":  {"icon": "🪪", "tag": "bad",    "text": "A regular pulls you aside — that girl you just waved in looked way underage.",
                  "choices": ["Quietly walk her out and pay him off", "Call his bluff"]},
    "marshal":   {"icon": "🚒", "tag": "bad",    "text": "Fire marshal at the door doing a count — you're well over capacity tonight.",
                  "choices": ["Slip him some cash", "Clear the floor for the night"]},
    "whale":     {"icon": "🧾", "tag": "bad",    "text": "A big spender is trying to walk out on a ${amt:,} tab.",
                  "choices": ["Have a bouncer collect", "Comp it and keep him sweet"]},
    "poach":     {"icon": "💋", "tag": "bad",    "text": "A rival club sent muscle to poach {who} right off your floor.",
                  "choices": ["Match their offer", "Stand firm with your bouncers", "Let her walk"]},
    "barcaught": {"icon": "🍸", "tag": "bad",    "text": "A whale just realized his top-shelf is watered down and he's making a scene.",
                  "choices": ["Comp the table and apologize", "Brush it off"]},
    "celeb":     {"icon": "🌟", "tag": "good",   "text": "A local celebrity just rolled in with an entourage and a camera crew.",
                  "choices": ["Comp the VIP and let them flex", "Charge them full freight"]},
    "bachelor":  {"icon": "🎉", "tag": "good",   "text": "A huge bachelor party wants to book out the whole place.",
                  "choices": ["Go all-in — pull the girls to the party", "Run standard service"]},
    "talent":    {"icon": "🌹", "tag": "good",   "text": "A stunning dancer walked in looking for a spot — she wants a ${amt:,} signing bonus.",
                  "choices": ["Pay the bonus and sign her", "Pass on her"]},
    "briefcase": {"icon": "💼", "tag": "quirky", "text": "Housekeeping found a briefcase stuffed with ${amt:,} in the VIP room.",
                  "choices": ["Keep it", "Track down whoever left it"]},
    "viral":     {"icon": "📱", "tag": "quirky", "text": "{who} blew up online overnight — there's a line forming around the block.",
                  "choices": ["Lean all the way into the hype", "Keep it low-key"]},
    "raise":     {"icon": "💰", "tag": "dancer", "text": "{who} pulls you aside — she wants a bigger cut, says she's earned it.",
                  "choices": ["Give her the raise", "Talk her down", "Flat-out refuse"]},
    "burnout":   {"icon": "😮‍💨", "tag": "dancer", "text": "{who} is feeling burnt out and unappreciated — she's hinting she might walk.",
                  "choices": ["Give her a night and some respect", "Tell her to suck it up"]},
    "trouble":   {"icon": "🆘", "tag": "dancer", "text": "{who} is in a jam outside the club and quietly asks you for help.",
                  "choices": ["Help her out (${amt:,})", "Stay out of it"]},
}

def _dark_club_pick_dancer(c):
    ds = [x for x in c.get("dancers", []) if not x.get("manager")]
    return random.choice(ds) if ds else None

def _dark_club_spawn_milestone(s, c, dancer, events):
    """A dancer hit her personal goal — freeze the floor for the player's call."""
    ttl = _dark_club_title(dancer.get("level", 1))
    c["event"] = {"key": "milestone", "icon": "🎯", "dancer_id": dancer["id"], "amt": 0,
                  "choices": ["Throw her a sendoff — let her leave on top",
                              "Talk her into staying as your House Mom",
                              "Re-sign her with a raise"],
                  "text": f"{dancer['name']} ({ttl[1]}) just hit her goal — she's finally saved enough to {dancer.get('goal', 'move on')}. She's wondering what comes next."}
    events.append({"type": "info", "text": f"🎯 {dancer['name']} reached her life goal — there's a decision waiting at the club."})

def _dark_club_spawn_event(s, c, events):
    # Whole-club OPERATIONAL incidents only — these never target the named cast (the cast
    # has its own scripted per-dancer stories), so the two systems can't collide.
    up = c.get("upgrades", {})
    door_eye = max([b.get("eye", 0) for b in c.get("bouncers", []) if b.get("assign") == "door"] or [0])
    pool = ["fight", "vice", "marshal", "whale", "celeb", "bachelor", "briefcase"]
    if door_eye < 3: pool.append("underage")              # a sharp door bouncer keeps minors out entirely
    if up.get("bar", 0) > 0 and c.get("bar", {}).get("price") == "water": pool.append("barcaught")
    key = random.choice(pool)
    meta = DARK_CLUB_EVENTS[key]
    ev = {"key": key, "icon": meta["icon"], "choices": list(meta["choices"])}
    amt = {"whale": random.randint(2_000, 6_000),
           "briefcase": random.randint(3_000, 9_000)}.get(key, 0)
    ev["amt"] = amt
    ev["text"] = meta["text"].format(amt=amt, who="one of your girls")
    c["event"] = ev
    events.append({"type": "warning", "text": f"{meta['icon']} Something's gone down at the club — it's shut until you handle it (Biz tab)."})

def _dark_story_resolve(s, c, x, choice):
    """Resolve one beat of a dancer's scripted arc. Returns a result line."""
    d = s["dark"]; k = x.get("key"); b = x.get("beat", 0); nm = x["name"]
    def cash(n): s["cash"] = s.get("cash", 0) + n
    def rep(n):  c["rep"]  = min(100, max(0, c.get("rep", 0) + n))
    def heat(n): c["heat"] = min(120, max(0, c.get("heat", 0) + n))
    def loy(n):  x["loyalty"] = min(100, max(0, x.get("loyalty", 60) + n))
    def away(days): x["away_until"] = s["day"] + days
    secr = _dark_club_secrating(c)
    x["event"] = None
    left = ended = False
    msg = "Handled."
    if k == "roxy":
        if b == 0:
            if choice == 0: cash(-12000); away(6); loy(20); msg = "You covered Roxy's surgery. She's out about a week — and she'll never forget it."
            elif choice == 1: loy(-12); heat(4); msg = "Roxy gutted it out on painkillers. That knee's a time bomb now."
            else: loy(8); msg = "You moved Roxy to breaking in the new girls — easier on the body, and the floor's better for it."
        elif b == 1:
            if choice == 0: loy(12); msg = "You backed Roxy. The young one fell back in line."
            elif choice == 1: loy(-18); rep(2); msg = "You sided with youth. Roxy took it like a slap."
            else: loy(6); rep(4); msg = "You made them work it out — Roxy took the kid under her wing."
        else:
            if choice == 0: cash(-20000); rep(12); left = True; msg = "You cosigned Roxy's bar. She left to run it — and still sends her regulars your way. 🥂"
            elif choice == 1: loy(-10); ended = True; msg = "You talked Roxy out of it. She stayed — but something in her dimmed."
            else: x["manager"] = True; loy(100); ended = True; msg = "Roxy hung up her heels to run your floor as House Mom. 🧁"
    elif k == "jade":
        if b == 0:
            if choice == 0: loy(12); msg = "You slipped Jade out the back before he clocked her. She's shaken but grateful."
            elif choice == 1: away(3); loy(-6); msg = "You did nothing. Jade panicked and didn't show for a few nights."
            else: heat(-10); loy(-15); msg = "You leaned on the professor — he'll stay quiet. Jade's disgusted you used her like that."
        elif b == 1:
            if choice == 0: cash(-6000); loy(8); msg = "You paid the blackmail. It's handled — for now."
            elif choice == 1:
                if secr >= 3: loy(15); heat(6); msg = "Your bouncer had a quiet word. The photo's gone and Jade's loyal for life."
                else: heat(14); loy(5); msg = "Short-handed, it got ugly — the photo's gone but you drew heat doing it."
            else:
                if random.random() < 0.5: loy(6); msg = "You called the bluff — it blew over. Jade dodged a bullet."
                else: away(4); loy(-10); rep(-3); msg = "The bluff backfired — the photo got out. Jade went to ground for days."
        else:
            if choice == 0:
                c.setdefault("leverage", []).append({"kind": "da", "who": "Jade, now a defense attorney"})
                rep(6); left = True; msg = "You sent Jade off in style. She passed the bar — and a lawyer who owes you is worth more than any dancer. ⚖️"
            else: loy(-20); ended = True; msg = "You guilted Jade into staying. She dances with dead eyes now."
    elif k == "bambi":
        if b == 0:
            if choice == 0: away(3); loy(8); msg = "You sent Bambi home to sober up. Lost the night, but it was the right call."
            elif choice == 1: cash(4000); heat(10); loy(-10); msg = "You pushed her on stage anyway. Huge night — and you just made it all worse."
            else: loy(-6); heat(-4); msg = "You cut Bambi off the party crowd. She's furious, but it helps."
        elif b == 1:
            if choice == 0: heat(4); loy(12); msg = "You 86'd the dealer for good. Bambi's got a real shot now."
            elif choice == 1: cash(3000); heat(14); loy(-8); msg = "You looked away. She stays lit and packs the house — and your heat climbs."
            else: cash(-5000); loy(15); msg = "You quietly bought out her debt and cut the dealer loose. She's stunned anyone cared."
        else:
            if choice == 0: cash(-15000); away(14); loy(100); x["draw"] = min(7, x.get("draw", 5) + 1); ended = True; msg = "You paid for real rehab. Two weeks later she's back — clean, glowing, your most loyal girl. A genuine comeback. ✨"
            elif choice == 1: cash(-6000); loy(20); ended = True; msg = "You got Bambi into outpatient help. It's fragile, but she's fighting — and she's still yours."
            else: rep(-8); left = True; msg = "You couldn't keep carrying her. Bambi spiraled out and disappeared. That one's going to sit with you."
    elif k == "mercedes":
        if b == 0:
            if choice == 0: loy(-8); cash(1000); msg = "You docked her and warned her. Mercedes respects strength — but she's sore about it."
            elif choice == 1: loy(10); heat(2); msg = "You took a cut and said nothing. She's loyal now — and theft is the house culture."
            else: cash(2500); heat(6); loy(6); msg = "You made Mercedes your collections muscle. Deadbeats pay up now — and the room knows it."
        elif b == 1:
            if choice == 0: cash(-8000); loy(12); msg = "You matched the offer. Mercedes is staying — money talks."
            elif choice == 1: left = True; heat(5); msg = "You let Mercedes walk. She knows too much about your operation to feel good about it."
            else:
                if x.get("loyalty", 60) >= 70: loy(10); msg = "You appealed to loyalty — and you'd earned it. Mercedes turned the rival down flat."
                else: loy(-5); msg = "You asked for loyalty you hadn't earned. Mercedes just smiled and said she'd think about it."
        else:
            if choice == 0:
                if x.get("loyalty", 60) >= 60: cash(25000); rep(6); ended = True; msg = "Mercedes delivered — a whale party that printed money. She's earned her keep. 🐳"
                else:
                    left = True; _dark_trigger_hunt(s, bump=40)   # the sting puts Marsh onto your hottest op
                    msg = "The 'whale' was a sting. Mercedes set you up and vanished — Marsh is moving on one of your operations now."
            else: cash(2000); ended = True; msg = "You kept Mercedes on a short leash. No windfall, but no knife in your back either."
    elif k == "lola":
        if b == 0:
            if choice == 0:
                if secr >= 3: loy(15); msg = "Your bouncers walked the ex out hard. Lola's safe, and she knows who kept her that way."
                else: heat(10); loy(6); msg = "You tried to walk him out short-handed — it got loud. He's gone, but it drew eyes."
            elif choice == 1: loy(8); msg = "You quietly put him on the do-not-admit list. Lola breathes easier."
            else: away(4); loy(-8); msg = "You let her handle it. She was terrified and didn't surface for days."
        elif b == 1:
            if choice == 0: heat(12); loy(14); msg = "You shut his little shakedown down hard. He's furious — but Lola's not his to sell."
            elif choice == 1: cash(-5000); loy(4); msg = "You paid him off to go away. For now."
            else: heat(16); loy(-10); cash(2000); msg = "You let him hang around. He runs her and brings trouble through your doors."
        else:
            if choice == 0:
                if x.get("loyalty", 60) >= 60: loy(10); ended = True; msg = "Your intervention got through. Lola saw him for what he is and stayed."
                else: left = True; msg = "She didn't want to hear it. Lola ran off with him anyway."
            elif choice == 1: cash(-8000); rep(5); left = True; msg = "You gave Lola the money to get away clean — from him, and from you. She'll make it. 🕊️"
            else: left = True; msg = "You let Lola go. You both knew how it would end."
    elif k == "destiny":
        if b == 0:
            if choice == 0: rep(14); heat(10); msg = "You leaned all the way in. The club's the hottest ticket in town — and a lot more eyes are on it."
            elif choice == 1: loy(-6); msg = "You kept it low-key. Destiny's crushed you didn't run with her moment."
            else: cash(5000); rep(5); loy(6); msg = "You monetized it right — merch, cover, the works. Everybody won."
        elif b == 1:
            if choice == 0: away(5); rep(8); msg = "You let Destiny go do the appearances. She's away a few days — and comes back with serious buzz."
            elif choice == 1: loy(-12); msg = "You held Destiny to her shifts. She did them, resenting every one."
            else: cash(4000); loy(5); msg = "You negotiated a cut of the appearances. Good money, happy girl."
        else:
            if choice == 0: rep(15); left = True; msg = "You blessed Destiny's exit. She went solo and famous — and the club's the place that made her. 🌟"
            elif choice == 1: rep(5); loy(10); x["draw"] = min(7, x.get("draw", 3) + 1); ended = True; msg = "You made Destiny your headline face. She's a star, and she's yours."
            else:
                if x.get("loyalty", 60) >= 50: loy(15); ended = True; msg = "You warned Destiny it was a scam — and she listened. She owes you one."
                else: left = True; rep(-3); msg = "You warned her, but she didn't listen. The 'manager' fleeced her and she's gone."
    # advance her arc
    if left:
        c["dancers"] = [dd for dd in c.get("dancers", []) if dd["id"] != x["id"]]
    elif ended:
        x["done"] = True
    else:
        x["beat"] = b + 1
        if x["beat"] >= len(DARK_DANCERS.get(k, {}).get("arc", [])): x["done"] = True
    return msg

def _dark_club_resolve_event(s, c, choice):
    """Apply the outcome of the player's choice. Returns a result line for the toast."""
    ev = c.get("event")
    if not ev: return "Nothing to handle."
    key = ev.get("key"); amt = ev.get("amt", 0); secr = _dark_club_secrating(c)
    did = ev.get("dancer_id"); dancer = next((x for x in c.get("dancers", []) if x["id"] == did), None) if did else None
    nm = dancer["name"] if dancer else "she"
    def heat(n): c["heat"] = min(120, max(0, c.get("heat", 0) + n))
    def rep(n):  c["rep"]  = min(100, max(0, c.get("rep", 0) + n))
    def cash(n): s["cash"] = s.get("cash", 0) + n
    msg = "Handled."
    if key == "fight":
        if choice == 0:
            if secr >= 4: rep(5); msg = "Your bouncers had it broken up before the next song. Clean."
            else: hurt = random.randint(2_000, 6_000); cash(-hurt); heat(10); msg = f"Short-handed at the door — someone got hurt and it cost you ${hurt:,} to keep quiet."
        elif choice == 1:
            rep(-6)
            if dancer: dancer["loyalty"] = max(0, dancer.get("loyalty", 60) - 8)
            msg = "You let it run its course. The place got trashed and the girls were rattled."
        else:
            rep(4); msg = "You 86'd the whole table. Lost their tab, but the room respects a tight house."
    elif key == "vice":
        if choice == 0: cash(-2_000); heat(-15); msg = "A comped bottle and a charming girl, and he forgot why he came. Heat cooled."
        elif choice == 1: heat(18); msg = "You threw him out. He'll remember the place — heat's up."
        else:
            lev = next((L for L in c.get("leverage", []) if L.get("kind") in ("da", "bent_cop")), None)
            if lev: c["leverage"] = [L for L in c["leverage"] if L is not lev]; heat(-25); msg = f"One call to {lev['who']} and the badge suddenly had somewhere else to be."
            else: heat(20); msg = "You've got nobody in your pocket to call — he left unhappy and the heat climbed."
    elif key == "underage":
        if choice == 0: cash(-random.randint(1_000, 3_000)); heat(4); msg = "Walked her out a side door and slipped the regular a few bills. Contained."
        else: heat(25); rep(-5); msg = "You called his bluff. He wasn't bluffing — that's a serious problem now."
    elif key == "marshal":
        if choice == 0: b = random.randint(3_000, 7_000); cash(-b); msg = f"${b:,} in his back pocket and the count came out fine."
        else: rep(-2); heat(-6); msg = "You cleared the floor and ate the lost night. Safe, at least."
    elif key == "whale":
        if choice == 0:
            if secr >= 3: cash(amt); rep(2); msg = f"Your bouncer had a quiet word. He paid the ${amt:,} — with a tip."
            else: cash(amt // 2); heat(12); msg = f"It turned into a shoving match. You got half (${amt//2:,}) and some heat."
        else: rep(3); msg = "You comped the tab with a smile. He left a loyal big spender."
    elif key == "poach":
        if choice == 0:
            if dancer: dancer["wage"] = dancer.get("wage", 200) + 60; dancer["loyalty"] = min(100, dancer.get("loyalty", 60) + 20)
            msg = f"You matched the offer. {nm} is staying — for now."
        elif choice == 1:
            if secr >= 4: rep(4); msg = f"Your muscle walked the rival's guy out. {nm} stayed and the street noticed."
            else:
                if dancer: c["dancers"] = [x for x in c["dancers"] if x["id"] != did]
                heat(8); msg = f"Without the muscle to back it up, {nm} took the better offer and walked."
        else:
            if dancer: c["dancers"] = [x for x in c["dancers"] if x["id"] != did]
            msg = f"You let {nm} go. No hard feelings."
    elif key == "barcaught":
        if choice == 0: cash(-random.randint(1_500, 3_500)); rep(-2); msg = "You comped the table and apologized. Damage controlled."
        else: rep(-10); msg = "You brushed him off. Word gets around — the club's name took a hit."
    elif key == "celeb":
        if choice == 0: cash(-random.randint(1_000, 3_000)); rep(12); msg = "You comped the VIP and let them put on a show. The exposure's worth a fortune."
        else: cash(random.randint(4_000, 8_000)); msg = "You charged full freight. Good money — but they won't be back."
    elif key == "bachelor":
        if choice == 0: cash(random.randint(7_000, 13_000)); rep(-3); msg = "You went all-in on the party. Huge night — the stage suffered for it."
        else: cash(random.randint(3_000, 6_000)); rep(1); msg = "Solid, steady service. Everyone left happy."
    elif key == "talent":
        if choice == 0:
            if s.get("cash", 0) >= amt and len(c.get("dancers", [])) < DARK_CLUB_DANCER_CAP:
                cash(-amt); nd = _dark_club_dancer(c, draw=random.randint(4, 5)); nd["assign"] = "stage"
                c["dancers"].append(nd); msg = f"You paid the bonus. {nd['name']} (⭐{nd['draw']}) starts tonight on the main stage."
            elif len(c.get("dancers", [])) >= DARK_CLUB_DANCER_CAP: msg = "No room on the roster — you had to pass."
            else: msg = f"You couldn't cover the ${amt:,} bonus. She moved on."
        else: msg = "You passed. She'll find a stage somewhere."
    elif key == "briefcase":
        if choice == 0: cash(amt); heat(15); msg = f"You kept the ${amt:,}. Could've been a setup — the heat says someone's watching."
        else: rep(6); msg = "You returned it to the right people. That kind of goodwill is worth more than cash."
    elif key == "viral":
        if choice == 0: rep(12); heat(10); msg = f"You leaned into {nm}'s viral moment. Packed house — and a lot more eyes on the place."
        else: rep(3); msg = "You kept it low-key. A nice little bump, no drama."
    elif key == "raise":
        if choice == 0:
            if dancer: dancer["wage"] = dancer.get("wage", 200) + 50; dancer["loyalty"] = min(100, dancer.get("loyalty", 60) + 15)
            msg = f"You gave {nm} the raise. She's loyal and lit up about it."
        elif choice == 1:
            if dancer: dancer["loyalty"] = max(0, dancer.get("loyalty", 60) + random.choice([-5, 5]))
            msg = f"You talked {nm} down. We'll see if it holds."
        else:
            if dancer: dancer["loyalty"] = max(0, dancer.get("loyalty", 60) - 20)
            msg = f"You refused flat-out. {nm} is not happy."
    elif key == "burnout":
        if choice == 0:
            if dancer: dancer["loyalty"] = min(100, dancer.get("loyalty", 60) + 14)
            msg = f"You gave {nm} a night and made her feel valued. She won't forget it."
        else:
            if dancer: dancer["loyalty"] = max(0, dancer.get("loyalty", 60) - 18)
            rep(-2); msg = f"You told {nm} to suck it up. The set was flat and she resents it."
    elif key == "milestone":
        if not dancer:
            msg = "She'd already moved on."
        elif choice == 0:                       # sendoff — she leaves on top
            c["dancers"] = [x for x in c.get("dancers", []) if x["id"] != did]
            rep(10); msg = f"You threw {nm} a proper sendoff and let her go out on top. The whole club loved it. (+rep)"
        elif choice == 1:                       # promote to House Mom
            dancer["manager"] = True; dancer["assign"] = "manager"; dancer["loyalty"] = 100
            dancer["goal_prog"] = 0
            msg = f"{nm} hung up her heels to run the floor as your House Mom — she lifts the whole room now."
        else:                                   # re-sign with a raise + a fresh goal
            dancer["loyalty"] = min(100, dancer.get("loyalty", 60) + 25)
            dancer["wage"] = dancer.get("wage", 200) + 40
            dancer["goal"] = random.choice(DARK_CLUB_GOALS); dancer["goal_prog"] = 0
            if dancer.get("draw", 1) < 7: dancer["draw"] += 1
            msg = f"You re-signed {nm} with a raise. New goal, bigger draw — she's not going anywhere."
    elif key == "trouble":
        if choice == 0:
            cash(-amt)
            if dancer: dancer["loyalty"] = min(100, dancer.get("loyalty", 60) + 25)
            msg = f"You helped {nm} out of the ${amt:,} jam. She's loyal to you for life now."
        else:
            if dancer: dancer["loyalty"] = max(0, dancer.get("loyalty", 60) - 15)
            msg = f"You stayed out of it. {nm} understands — but she remembers, too."
    c["event"] = None
    return msg

# ── VIP room minigame: read the patron, loosen their tongue, extract Hunt intel. ──
def _dark_vip_start(c):
    weights = ["beat", "beat", "vice", "vice", "da", "snitch", "undercover"]
    t = random.choice(weights)
    c["vip_patron"] = False
    c["vip_game"] = {"type": t, "comfort": 15, "susp": DARK_VIP_TYPES[t]["susp"], "intel": 0,
                     "round": 0, "revealed": False, "done": False}

# Criminal traits — each recruit has exactly ONE. "knows" traits gate which drug a crew
# can cook (a crew needs a member who knows the target drug). The rest are skill/personality
# traits whose mechanical effects kick in once crews work labs.
DARK_TRAITS = {
    "green_thumb": {"name": "Green Thumb",   "icon": "🌿", "knows": "reggie", "cost": 2500,  "desc": "Knows how to grow Weed."},
    "pill_cook":   {"name": "Pill Cook",     "icon": "💊", "knows": "beans",  "cost": 5000,  "desc": "Knows how to press Pills."},
    "cutter":      {"name": "Cutter",        "icon": "❄️", "knows": "soft",   "cost": 8000,  "desc": "Knows how to cut Powder."},
    "rock_cook":   {"name": "Rock Cook",     "icon": "🪨", "knows": "hard",   "cost": 11000, "desc": "Knows how to cook Rock."},
    "chemist":     {"name": "Chemist",       "icon": "🧪", "knows": "glass",  "cost": 15000, "desc": "Knows how to cook Glass."},
    "tar_boiler":  {"name": "Tar Boiler",    "icon": "🛢️", "knows": "tar",    "cost": 20000, "desc": "Knows how to boil Tar."},
    "workhorse":   {"name": "Workhorse",     "icon": "🐂", "cost": 3500, "desc": "Cranks out product faster."},
    "ghost":       {"name": "Ghost",         "icon": "👻", "cost": 4000, "desc": "Draws less heat — barely leaves a trace."},
    "loyal":       {"name": "Loyal",         "icon": "🤝", "cost": 3500, "desc": "Won't snitch, even unpaid. Fewer bad events."},
    "hothead":     {"name": "Hothead",       "icon": "🔥", "cost": 1800, "desc": "More conflict events — but wins turf."},
    "connected":   {"name": "Connected",     "icon": "📇", "cost": 4500, "desc": "Brings cheap-gear & opportunity events."},
    "sloppy":      {"name": "Sloppy",        "icon": "🧤", "cost": 900,  "desc": "Cheap, but causes more accidents."},
    "lookout":     {"name": "Lookout",       "icon": "👀", "cost": 3000, "desc": "Gives early warning before a raid."},
    "lucky":       {"name": "Lucky",         "icon": "🍀", "cost": 4500, "desc": "Better luck on event rolls."},
    "junkie":      {"name": "Junkie",        "icon": "💉", "cost": 700,  "desc": "Skims product for himself. Dirt cheap."},
    "smooth":      {"name": "Smooth Talker", "icon": "🎩", "cost": 3500, "desc": "Talks down cops — softens busts."},
}
# Weighted recruit pool: weed-cooks + skills common, high-tier cooks rare.
_DARK_TRAIT_WEIGHTS = {"green_thumb": 6, "pill_cook": 3, "cutter": 2, "rock_cook": 1, "chemist": 1, "tar_boiler": 1,
                       "workhorse": 3, "ghost": 3, "loyal": 3, "hothead": 3, "connected": 3, "sloppy": 3,
                       "lookout": 3, "lucky": 2, "junkie": 3, "smooth": 3}
# ── Crew/dealer names are generated FIRST × LAST (+ an occasional mob nickname), then
#    deduped against everyone you already know — so you'll basically never see a repeat. ──
_DARK_FIRST_NAMES = [
    "Tony", "Vince", "Marco", "Sal", "Rico", "Benny", "Dom", "Carlo", "Joey", "Nico", "Frankie", "Lou", "Gus",
    "Paulie", "Mickey", "Manny", "Vito", "Sonny", "Angelo", "Gino", "Bruno", "Aldo", "Enzo", "Luca", "Matteo",
    "Rocco", "Sergio", "Dario", "Carmine", "Salvatore", "Lorenzo", "Giovanni", "Cosmo", "Silvio", "Renzo", "Fredo",
    "Augie", "Vinnie", "Sammy", "Mario", "Gianni", "Tito", "Eddie", "Charlie", "Johnny", "Ray", "Pete", "Stevie",
    "Gabe", "Marty", "Dean", "Moe", "Hank", "Bobby", "Donnie", "Tommy", "Jimmy", "Georgie", "Richie", "Nicky",
    "Petey", "Jerry", "Frank", "Mike", "Joe", "Chris", "Danny", "Marcus", "Jamal", "Omar", "Hector", "Diego",
    "Reggie", "Trey", "Cyrus", "Bishop", "Andre", "Darnell", "Tyrese", "Malik", "Deshawn", "Terrence", "Maurice",
    "Leon", "Curtis", "Jerome", "Devon", "Rashad", "Kareem", "Otis", "Clyde", "Roscoe", "Theo", "Ramon", "Carlos",
    "Javier", "Miguel", "Luis", "Tomas", "Rafael", "Emilio", "Cesar", "Pablo", "Sergei", "Dmitri", "Yuri", "Viktor",
    "Ivan", "Nikolai", "Boris", "Anton", "Mikhail", "Stavros", "Niko", "Dimitri"]
_DARK_LAST_NAMES = [
    "Russo", "Gambino", "Marino", "Romano", "Bianchi", "Esposito", "Ricci", "Greco", "Costa", "Conti", "Marchetti",
    "De Luca", "Moretti", "Barbieri", "Fontana", "Caruso", "Ferrari", "Galli", "Lombardi", "Mancini", "Rizzo",
    "Santoro", "Vitale", "Colombo", "Gallo", "Leone", "Longo", "Martini", "Palumbo", "Parisi", "Serra", "Villa",
    "Fiore", "Sorrentino", "Gentile", "Pellegrino", "Carbone", "Valentino", "Castellano", "Genovese", "Bonanno",
    "Lucchese", "Profaci", "Maranzano", "Scarpa", "Persico", "Falcone", "Borsellino", "Provenzano", "Cutolo", "Spada",
    "Williams", "Johnson", "Brown", "Davis", "Jackson", "Carter", "Robinson", "Mitchell", "Coleman", "Hayes",
    "Brooks", "Reed", "Bell", "Ward", "Cooper", "Foster", "Greene", "Powell", "Bryant", "Watkins", "Holloway",
    "Sanders", "Garcia", "Hernandez", "Lopez", "Gonzalez", "Ramirez", "Torres", "Flores", "Rivera", "Morales",
    "Ortiz", "Castillo", "Vega", "Reyes", "Delgado", "Mendez", "Petrov", "Volkov", "Sokolov", "Ivanov", "Kozlov",
    "Novak", "Kowalski", "Nowak", "Papadopoulos", "O'Brien", "Sullivan", "Kelly", "Murphy", "Walsh", "Doyle",
    "Burke", "Quinn", "McKenna", "Donovan", "Flynn", "Brennan"]
_DARK_NICKNAMES = ["Knuckles", "Slim", "Ace", "Doc", "Tank", "Razor", "Smiley", "Lefty", "Spider", "Fingers",
                   "Bugsy", "Lucky", "Tiny", "Bull", "Ghost", "Bones", "Snake", "The Chin", "Three-Fingers",
                   "Whitey", "Cadillac", "Pretty Boy", "The Hammer", "Icepick", "Mad Dog", "Curly", "Fish",
                   "Tubby", "Junior", "Sticks", "Goldie", "Nails", "Two-Times", "Sneaks", "Bishop", "Gigs"]

def _dark_used_names(d):
    used = set()
    for coll in ((d or {}).get("roster", []), (d or {}).get("recruits", []), (d or {}).get("dealers", [])):
        for x in coll:
            if x.get("name"): used.add(x["name"])
    return used

def _dark_make_name(used):
    """One fresh FIRST LAST (sometimes FIRST 'Nick' LAST), avoiding anything already in `used`."""
    nm = None
    for _ in range(60):
        first = random.choice(_DARK_FIRST_NAMES); last = random.choice(_DARK_LAST_NAMES)
        nm = f"{first} '{random.choice(_DARK_NICKNAMES)}' {last}" if random.random() < 0.16 else f"{first} {last}"
        if nm not in used: break
    used.add(nm)
    return nm

def _dark_gen_recruits(d, n=10):
    cred = d.get("cred", 1)
    # Guarantee EXACTLY ONE cook for each drug you've unlocked — no more, no fewer.
    cooks = [t for t, m in DARK_TRAITS.items()
             if m.get("knows") and DARK_DRUGS.get(m["knows"], {}).get("cred_req", 99) <= cred]
    # The rest of the list is personality/skill traits only — never a second cook of any kind.
    fillers = [t for t, w in _DARK_TRAIT_WEIGHTS.items() if not DARK_TRAITS.get(t, {}).get("knows") for _ in range(w)]
    out = []; used = _dark_used_names(d)
    def add(trait):
        rid = d.get("next_recruit_id", 1); d["next_recruit_id"] = rid + 1
        out.append({"id": rid, "name": _dark_make_name(used), "trait": trait})
    for t in cooks: add(t)
    while len(out) < n and fillers: add(random.choice(fillers))
    random.shuffle(out)
    return out

# Crew roles. hire = one-time clean-cash cost; wage = clean cash/day while employed.
DARK_SWAT_HEAT = 100   # per-home heat that triggers a raid

# ── THE HUNT ──────────────────────────────────────────────────────────────────
# Each Watched operation (lab / dealer / front) builds LOCAL heat as it runs — harder
# and faster you push it, the hotter. That heat is the daily chance Marsh locks onto it
# as his single target: 25%+ heat → 10%, and +10% more for every extra 25% (100% → 40%).
# He watches ONE op at a time. Once he's locked on, the top-right Heat becomes a 5–10 day
# RAID COUNTDOWN that climbs each day; at 100% he raids that op. You piece together which
# op it is from CLUES (they sharpen as the countdown climbs), then shut it down before the
# raid — lab: no crew/no batch · dealer: paused · front: washing off. The raid still comes,
# but if there's nothing illegal running there, you walk untouched. If it's still dirty,
# it gets drained: lab → crew + product + house; dealer → busted; front → uncollected
# cash + the business itself (rebuy + rehire). The strip club is legit — it's NOT Watched.
DARK_DETECTIVE       = "Det. Marsh"
DARK_WATCH_MIN_HEAT  = 25      # an op must be at least this hot to draw his eye at all
DARK_RAID_MIN_DAYS   = 5       # fastest the countdown fills once he's locked on
DARK_RAID_MAX_DAYS   = 10      # slowest
DARK_RAID_COOLDOWN   = 6       # days after a raid before he can lock onto a new target
DARK_INTEL_COST      = 25_000  # the mole's tip — a sharp clue, but it costs real money now
DARK_VIP_COST        = 60_000  # build the strip-club VIP lounge (intel engine)
DARK_VIP_WORK_COST   = 6_000   # work the VIP room for a guaranteed clue
DARK_VIP_INTEL_CHANCE = 0.35   # passive daily chance the lounge turns up a clue
DARK_STRIPCLUB_EARN  = 1_500   # dirty money/day the club pulls in on its own
DARK_CLUE_CREW_CHANCE = 0.18   # daily: a Connected crew member whispers a clue
DARK_CLUE_NEWS_CHANCE = 0.12   # daily: a local news headline drops a vague category clue
DARK_CLUE_DEAL_CHANCE = 0.22   # daily (only if the target is a dealer): a dealer flags a buyer

DARK_MARSH_LOCK_LINES = [   # the Fixer's word when Marsh picks a fresh target (vague)
    "Marsh pulled a file today — he's locked onto one of your spots. Start working the case.",
    "Word is Marsh opened a surveillance log on one of your operations. The clock's running now.",
    "A detective started building a case on one of your spots. Marsh. Figure out which one — fast.",
]
DARK_NEWS_HEADLINES = [   # free ambient clue delivery — vague, sets the mood
    "📰 Local news: \"POLICE ANNOUNCE CRACKDOWN ON ORGANIZED CRIME.\"",
    "📰 Local news: \"TASK FORCE TARGETS ILLEGAL OPERATIONS DOWNTOWN.\"",
    "📰 Local news: \"DETECTIVE VOWS ARRESTS BY MONTH'S END.\"",
]

def _dark_heat_tier(h):
    if h >= DARK_SWAT_HEAT: return "swat"
    if h >= 75: return "imminent"
    if h >= 50: return "hot"
    if h >= 25: return "watched"
    return "quiet"

def _dark_crew_by_id(d, cid):
    return next((c for c in d.get("crews", []) if c["id"] == cid), None)

def _dark_crew_members(d, crew):
    return [m for m in d.get("roster", []) if crew and m.get("crew_id") == crew["id"]]

def _dark_crew_knows(d, crew):
    # the set of drug keys this crew can cook (from members' knowledge traits)
    out = set()
    for m in _dark_crew_members(d, crew):
        kn = (DARK_TRAITS.get(m.get("trait")) or {}).get("knows")
        if kn: out.add(kn)
    return out

def _dark_stash_add(d, drug, units):
    st = d.setdefault("stash", {})
    st[drug] = st.get(drug, 0) + units

DARK_DEALER_CAP = 12   # units a dealer moves per day (see _dark_dealer_cap for cred scaling)
DARK_BIZ_PRICE  = {"laundromat": 50_000, "car_wash": 300_000, "strip_club": 200_000, "pizzeria": 130_000,
                   "autolot": 600_000, "construction": 1_200_000}
DARK_CASINO_COST = 75_000   # convert a carried-over arcade into a casino

# Laundering fronts — wash dirty money into clean. cap = dirty $/day cleaned per rate level;
# hire = one-time dirty-manager fee; wage = daily upkeep while washing; heat_rate scales business heat.
# A clean ladder: cheaper fronts wash less and run hotter; the premium front washes the
# most and is the safest per push. (cap = dirty $/day per rate level; rate is 0-3.)
DARK_LAUNDER = {
    "laundromat":   {"name": "Laundromat",          "kind_label": "laundromat",       "icon": "🧼", "cap": 2000,  "hire": 4_000,  "wage": 200,  "heat_rate": 9},
    "pizzeria":     {"name": "Famiglia's Pizzeria", "kind_label": "pizzeria",         "icon": "🍕", "cap": 4500,  "hire": 8_000,  "wage": 500,  "heat_rate": 7},
    "car_wash":     {"name": "Car Wash",            "kind_label": "car wash",         "icon": "🚗", "cap": 8000,  "hire": 12_000, "wage": 850,  "heat_rate": 5},
    "autolot":      {"name": "Big Al's Used Autos", "kind_label": "used-car lot",     "icon": "🚙", "cap": 13000, "hire": 18_000, "wage": 1300, "heat_rate": 4},
    "construction": {"name": "Apex Contracting",    "kind_label": "contracting firm", "icon": "🏗️", "cap": 20000, "hire": 30_000, "wage": 2000, "heat_rate": 3},
}
DARK_VENDING_PAYOUT = 80_000   # cousin Vinny buys the vending business

# ── Phil, the front Enforcer. Old contractor from your house-flipping days; now he
#    parks himself at one front, eats any event, slows the heat, and never lets it
#    boil over to a raid — all for a token $100/day. Offered at Street Cred 3. ──
DARK_PHIL_WAGE = 100
DARK_PHIL_LINES = [
    "🧰 Phil had a quiet word with the health inspector at the {front}. Handled.",
    "🧰 Phil walked a nosy detective back to his car — the {front}'s fine.",
    "🧰 Somebody came around the {front} asking questions. Phil saw them off.",
    "🧰 Phil smoothed over a problem at the {front} before it was a problem.",
    "🧰 A situation at the {front} just… sorted itself out. That's Phil.",
]

# ══════════════════════════════════════════════════════════════════════════════
#  SCORES — one-time heists. Bigger targets unlock by Street Cred. Assemble a crew
#  of specialists (cut for life, +1 skill every job they run), case the joint to
#  raise your odds, then pull a branching job: build the pot to the estimate, then
#  cash out OR push your luck for way more. A specialist buffs the choice that
#  matches their role. Loot is dirty money. A bust costs the take + a heat spike
#  (crew walks clean, and the job stays available to try again).
# ══════════════════════════════════════════════════════════════════════════════
DARK_HEIST_ROLES = {"driver": {"name": "Driver", "icon": "🚗"}, "hacker": {"name": "Hacker", "icon": "💻"},
                    "boxman": {"name": "Boxman", "icon": "🧨"}, "muscle": {"name": "Muscle", "icon": "🔫"},
                    "face":   {"name": "Face",   "icon": "🎭"}}
DARK_HEIST_TIERS = [{"tier": "street", "name": "Street", "cut": 6, "skill": 1},
                    {"tier": "seasoned", "name": "Seasoned", "cut": 10, "skill": 3},
                    {"tier": "pro", "name": "Pro", "cut": 15, "skill": 5}]
DARK_HEIST_NAMES = {
    "driver": ["Treadz", "Gears", "Lefty", "Wheels", "Ramps"],
    "hacker": ["Bitwise", "Glitch", "Cipher", "Modem", "Root"],
    "boxman": ["Tumbler", "Click", "Nitro", "Fingers", "Dial"],
    "muscle": ["Bull", "Crusher", "Tiny", "Rebar", "Mack"],
    "face":   ["Silk", "Cardsharp", "Mirage", "Velvet", "Slick"],
}
DARK_HEIST_SKILL_BUFF = 8   # +% to a matching choice per skill point
DARK_HEIST_FUMBLE_MULT = 1.8  # a blown clutch costs this much more than just taking the loss

# Each beat: choices = [{label, role?, base%, good (pot $ on success), bad (pot $ lost on fail), crit?}].
# Getaway choices keep the pot on success; a crit fail anywhere = bust.
DARK_HEISTS = {
    "checkcash": {
        "name": "The Check-Cashing Spot", "icon": "🏪", "cred": 2, "est": 25_000, "roles": ["driver", "muscle"],
        "blurb": "A cash-heavy check-cashing joint off the boulevard. Thin security, fat drawers. A clean first score.",
        "case": [
            {"id": "watch", "label": "Watch the place for a day", "cost": 1_500, "bonus": 6,  "note": "You clock the guard's smoke breaks and the camera blind spot."},
            {"id": "sched", "label": "Buy the schedule off the clerk's cousin", "cost": 3_500, "bonus": 9, "note": "Now you know exactly when the drawer's fattest."},
        ],
        "beats": [
            {"icon": "🚪", "text": "Two minutes to opening. Through the glass: one clerk counting her till, a rent-a-guard half-asleep on a stool. Your muscle's knuckles are white on the door handle. How do you go in?",
             "choices": [{"label": "Walk in calm — flash the piece", "role": "muscle", "base": 42, "good": 9_000, "bad": 3_000,
                          "win": "The piece does the talking. The guard's hands are up before he's even awake.", "fail": "The guard's quicker than he looks — he lunges for the panic button.",
                          "clutch": "His hand's slamming toward the alarm — you have to reach him first."},
                         {"label": "Kick the door — all noise", "role": "muscle", "base": 34, "good": 11_000, "bad": 4_000,
                          "win": "You come in like a thunderclap. Nobody so much as breathes.", "fail": "Too loud — someone on the sidewalk already has a phone out.",
                          "clutch": "A bystander's filming — shut it down before that clip goes anywhere."}]},
            {"icon": "💵", "text": "The clerk's frozen, hand trembling an inch above the cash drawer. Every second you stand here is a second closer to a silent alarm she hasn't hit yet.",
             "choices": [{"label": "Let your muscle lean on her — now", "role": "muscle", "base": 47, "good": 8_000, "bad": 2_500,
                          "win": "One look from your guy and the drawer slides open.", "fail": "She panics and her knee finds the alarm under the counter.",
                          "clutch": "Her hand's diving for the alarm — beat her to it."},
                         {"label": "Keep it cool, talk her through it", "base": 43, "good": 9_000, "bad": 2_000,
                          "win": "Soft voice, steady hands. She does exactly what you say.", "fail": "She reads calm as weakness and starts stalling for time.",
                          "clutch": "She's running out the clock on purpose — close the gap fast."}]},
            {"icon": "🧷", "text": "Drawer's open. Banded stacks staring back at you. The clock in your head is screaming to move.",
             "choices": [{"label": "Sweep it into the bag and move", "base": 60, "good": 8_000, "bad": 3_000,
                          "win": "Bag's full in eight seconds flat.", "fail": "You fumble a stack and bills go fluttering across the floor.",
                          "clutch": "Cash all over the tile — scoop it before it scatters."}]},
        ],
        "greed": [
            {"icon": "🗄️", "text": "On the way out you clock it — a back-office safe, door cracked, nobody watching. Could be nothing. Could be the real money.",
             "choices": [{"label": "Have your guy force it", "role": "muscle", "base": 38, "good": 13_000, "bad": 5_000,
                          "win": "He peels it like a tin can. Jackpot.", "fail": "The hinge shrieks — and so does somebody out front.",
                          "clutch": "That screech carried — move before it brings company."},
                         {"label": "Pop it quiet, driver on the street", "role": "driver", "base": 42, "good": 11_000, "bad": 4_000,
                          "win": "Quiet, clean, and your driver never blinked.", "fail": "Your driver hisses a warning — headlights swinging in.",
                          "clutch": "Headlights coming — finish it or bolt, right now."}]},
            {"icon": "🏧", "text": "Out back, the night-deposit ATM sits there fat and dumb. But you can hear a patrol car a few blocks off, and it's getting closer.",
             "choices": [{"label": "Rip it open and gun it", "role": "muscle", "base": 30, "good": 18_000, "bad": 9_000, "crit": True,
                          "win": "You tear it open and the cash is yours — go, go, go.", "fail": "The cruiser rounds the corner just as it gives. They've got you.",
                          "clutch": "Cruiser's right on top of you — one perfect move or it's over."},
                         {"label": "Crack it careful, eyes on the road", "role": "driver", "base": 35, "good": 15_000, "bad": 7_000, "crit": True,
                          "win": "Surgical. You're a ghost before the taillights fade.", "fail": "A beat too slow — a spotlight pins you to the wall.",
                          "clutch": "Spotlight swinging your way — NOW or never."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Bag's heavy, sirens somewhere behind you, your driver's got the engine screaming. Which way out of here?",
                    "choices": [{"label": "Main road — floor it", "role": "driver", "base": 46, "crit": True,
                                 "win": "He threads moving traffic like it's parked. Gone.", "fail": "Roadblock. Lights everywhere, nowhere to go.",
                                 "clutch": "Roadblock dead ahead — thread the gap or get boxed in."},
                                {"label": "Back streets — stay cool", "role": "driver", "base": 56, "crit": True,
                                 "win": "Quiet streets, easy speed. You melt into the city.", "fail": "Dead end — and a cruiser fills the mirror.",
                                 "clutch": "Dead end coming up — find the out before he blocks it."}]},
    },
    # ── The rest of the ladder: visible on the board, authored later. ──
    "jewelry": {
        "name": "The Jewelry Store", "icon": "💍", "cred": 4, "est": 80_000, "roles": ["driver", "muscle", "hacker"],
        "blurb": "Display cases of ice and a back-room safe — wired to the teeth. Bring someone who can talk to alarms.",
        "case": [
            {"id": "buyer", "label": "Pose as a buyer, scope the floor", "cost": 3_000, "bonus": 7, "note": "You map the cases and every camera arc."},
            {"id": "mall",  "label": "Bribe the mall's night guard", "cost": 6_000, "bonus": 11, "note": "He'll be on a very long bathroom break at showtime."},
        ],
        "beats": [
            {"icon": "💻", "text": "The whole shop's tied to a central monitoring station — motion sensors, glass-break mics, the works. Nothing happens until that system goes blind.",
             "choices": [{"label": "Loop the camera feed", "role": "hacker", "base": 44, "good": 26_000, "bad": 9_000,
                          "win": "The cameras play yesterday on a loop. You're invisible.", "fail": "The loop stutters and the station pings for a status check.",
                          "clutch": "The system wants a handshake — answer it before it locks the place down."},
                         {"label": "Cut the line, brute-force the panel", "role": "muscle", "base": 36, "good": 30_000, "bad": 12_000,
                          "win": "Lines dead, panel in pieces. Crude — but it's dark.", "fail": "A backup cell uplink kicks in — the alarm's awake.",
                          "clutch": "The backup radio's powering up — kill it NOW."}]},
            {"icon": "🔨", "text": "Rows of glass cases full of ice stand between you and the back safe. The night guard's halfway through his round.",
             "choices": [{"label": "Lay the guard down quiet", "role": "muscle", "base": 46, "good": 27_000, "bad": 9_000,
                          "win": "Zip-tied and calm before he knew you were in the room.", "fail": "He twists loose and lunges for his radio.",
                          "clutch": "He's keying the radio — shut him up first."},
                         {"label": "Ignore him, hammer the cases", "base": 40, "good": 24_000, "bad": 8_000,
                          "win": "Hammers swing, velvet trays empty into the bag.", "fail": "He rounds the corner mid-smash and bolts for the door.",
                          "clutch": "He's sprinting for the exit — cut him off."}]},
            {"icon": "💎", "text": "The floor ice is bagged. The real money's the certified stones locked in the back safe.",
             "choices": [{"label": "Crack the back safe", "role": "hacker", "base": 48, "good": 27_000, "bad": 10_000,
                          "win": "The little safe gives up its velvet boxes. Gorgeous.", "fail": "Three wrong codes — it locks itself for an hour.",
                          "clutch": "One attempt left before lockout — read the dial right."}]},
        ],
        "greed": [
            {"icon": "⌚", "text": "There's a sealed case of collector watches up front — Pateks, the works. Right under the street window, though.",
             "choices": [{"label": "Smash it and grab", "role": "muscle", "base": 38, "good": 35_000, "bad": 14_000,
                          "win": "A fortune in wrists, straight into the bag.", "fail": "The smash trips a separate window sensor.",
                          "clutch": "Window alarm arming — clear the case before it screams."},
                         {"label": "Pick it clean and quiet", "role": "hacker", "base": 42, "good": 28_000, "bad": 11_000,
                          "win": "Lock pops without a sound. Tidy.", "fail": "A passerby on the sidewalk stops to stare.",
                          "clutch": "Someone's watching through the glass — look casual, move fast."}]},
            {"icon": "🏦", "text": "The owner's personal safe is upstairs — rumored to hold loose diamonds worth more than the whole floor. You're way past your window now.",
             "choices": [{"label": "Go for the owner's safe", "role": "muscle", "base": 30, "good": 55_000, "bad": 22_000, "crit": True,
                          "win": "Loose stones by the fistful. The score of a lifetime.", "fail": "A silent alarm you missed — blue lights fill the street.",
                          "clutch": "Sirens already wailing — grab it and vanish in five seconds."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Bags of ice, and somewhere a silent alarm's tripped. Your driver's idling out back.",
                    "choices": [{"label": "Hit the freeway", "role": "driver", "base": 48, "crit": True,
                                 "win": "Onto the on-ramp and gone before the first cruiser shows.", "fail": "A traffic cam tags you — units converging.",
                                 "clutch": "They're funneling you toward a checkpoint — find the off-ramp."},
                                {"label": "Ditch the car, vanish through the mall", "role": "driver", "base": 56, "crit": True,
                                 "win": "You melt into the late crowd and out a service door.", "fail": "Mall security locks the exits — you're penned in.",
                                 "clutch": "They're sealing the doors — make the service exit first."}]},
    },
    "armored": {
        "name": "The Armored Truck", "icon": "🚚", "cred": 5, "est": 160_000, "roles": ["driver", "muscle", "hacker"],
        "blurb": "Hit it on its route. All timing and nerve — stop it cold, crack it fast, and have a wheelman who can vanish.",
        "case": [
            {"id": "tail",   "label": "Tail the route for a week", "cost": 6_000, "bonus": 8, "note": "You know the exact corner where it slows for the light."},
            {"id": "freq",   "label": "Buy the dispatch frequency", "cost": 12_000, "bonus": 12, "note": "You'll hear them call it in — and you'll already be moving."},
        ],
        "beats": [
            {"icon": "🚧", "text": "The truck runs its route like clockwork. You've got one intersection to stop ten tons of steel cold.",
             "choices": [{"label": "Box it in with two cars", "role": "driver", "base": 42, "good": 38_000, "bad": 16_000,
                          "win": "Pinned at the light, nowhere to go.", "fail": "The driver guns it onto the curb and around you.",
                          "clutch": "He's mounting the curb to escape — cut the angle off."},
                         {"label": "Lay a spike strip", "role": "hacker", "base": 40, "good": 42_000, "bad": 18_000,
                          "win": "Tires blow and the truck slews to a dead stop.", "fail": "Only one tire catches — it limps forward.",
                          "clutch": "Still rolling on the rim — stop it before it clears the block."}]},
            {"icon": "📡", "text": "The guards inside are already keying the radio to dispatch. Cut them off, or the cavalry's coming in minutes.",
             "choices": [{"label": "Jam their comms", "role": "hacker", "base": 44, "good": 40_000, "bad": 16_000,
                          "win": "Static. They're screaming into a dead mic.", "fail": "The jam's spotty — a partial call slips out.",
                          "clutch": "Half a distress call got through — smother the rest."},
                         {"label": "Smoke them out the back", "role": "muscle", "base": 38, "good": 38_000, "bad": 17_000,
                          "win": "Doors pop, hands up, no shots fired.", "fail": "They button up tight and call it in anyway.",
                          "clutch": "They're radioing from inside — breach before they finish the sentence."}]},
            {"icon": "💰", "text": "Back doors open. Canvas bags of banded cash, more than you can carry. The clock's screaming.",
             "choices": [{"label": "Form a chain, load fast", "role": "muscle", "base": 50, "good": 42_000, "bad": 14_000,
                          "win": "Bag after bag into the trunk. Heavy and beautiful.", "fail": "You drop a bag and bills wash toward a storm drain.",
                          "clutch": "A bag's tipping into the gutter — save it."}]},
            {"icon": "🔥", "text": "You've got the cash, but dash cams have your faces and dispatch knows something's wrong.",
             "choices": [{"label": "Torch the truck to kill the evidence", "role": "hacker", "base": 46, "good": 38_000, "bad": 12_000,
                          "win": "Flames eat the cameras and the prints. Clean.", "fail": "The fire draws every eye on the block.",
                          "clutch": "The blaze is a beacon — get clear before it pins you."}]},
        ],
        "greed": [
            {"icon": "🔒", "text": "There's a second strongbox bolted to the floor — the high-value run. Bearer bonds, maybe. The good stuff.",
             "choices": [{"label": "Pry it loose", "role": "muscle", "base": 34, "good": 60_000, "bad": 24_000,
                          "win": "The bolts shear and the box is yours. Jackpot.", "fail": "It won't budge and you've burned a minute you don't have.",
                          "clutch": "Last heave before the units arrive — rip it free."}]},
            {"icon": "🚁", "text": "Dispatch scrambled a chopper. One more grab from the cab's lockbox — the payroll run — or you run now.",
             "choices": [{"label": "One more grab", "role": "hacker", "base": 28, "good": 90_000, "bad": 40_000, "crit": True,
                          "win": "The cab box held the whole payroll. Unreal.", "fail": "A searchlight from above lights up the entire scene.",
                          "clutch": "Spotlight sweeping in — clear the cab in three seconds."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Loaded down, sirens closing, a chopper somewhere overhead.",
                    "choices": [{"label": "Highway sprint", "role": "driver", "base": 46, "crit": True,
                                 "win": "He outruns the cruisers and loses the chopper under an overpass.", "fail": "They PIT you into the median.",
                                 "clutch": "Cruiser's lining up the PIT — break away before contact."},
                                {"label": "Lose them in the industrial maze", "role": "driver", "base": 54, "crit": True,
                                 "win": "Alleys, loading docks, a switch to a clean car. Gone.", "fail": "Dead-end loading bay — boxed in.",
                                 "clutch": "That bay's a dead end — reverse out before they block it."}]},
    },
    "bank": {
        "name": "The Bank", "icon": "🏦", "cred": 7, "est": 375_000, "roles": ["driver", "muscle", "hacker", "boxman"],
        "blurb": "The real thing. A hardened vault, a full specialist crew, and a take that changes everything.",
        "case": [
            {"id": "acct", "label": "Open an account, walk the lobby", "cost": 12_000, "bonus": 7, "note": "You've clocked the vault door and the camera blind spots."},
            {"id": "tell", "label": "Turn a teller", "cost": 30_000, "bonus": 12, "note": "She'll leave the day-gate unlocked and look the other way."},
        ],
        "beats": [
            {"icon": "🚪", "text": "Doors at open. A floor of customers, two guards, and a manager carrying the only override card.",
             "choices": [{"label": "Lock it down loud — everyone on the floor", "role": "muscle", "base": 40, "good": 90_000, "bad": 35_000,
                          "win": "One shout and the whole floor's flat. You own the room.", "fail": "A guard's hand drops to his sidearm.",
                          "clutch": "Guard's drawing — put him down before he clears leather."},
                         {"label": "Quiet — pull the manager aside first", "role": "muscle", "base": 44, "good": 85_000, "bad": 30_000,
                          "win": "Manager's cooperating, customers none the wiser.", "fail": "A customer clocks what's happening and screams.",
                          "clutch": "The room's about to panic — calm it instantly."}]},
            {"icon": "📷", "text": "Cameras and silent alarms run off the security room. While it's live, every second is recorded and counted.",
             "choices": [{"label": "Hijack the security room", "role": "hacker", "base": 42, "good": 95_000, "bad": 38_000,
                          "win": "Feeds frozen, alarms suppressed. The clock's yours now.", "fail": "A failsafe pings the monitoring company.",
                          "clutch": "Monitoring's calling to verify — answer as the guard."}]},
            {"icon": "🔐", "text": "The vault door. A foot of hardened steel on a time-lock — the real obstacle. This is what you brought the boxman for.",
             "choices": [{"label": "Drill the lock", "role": "boxman", "base": 40, "good": 100_000, "bad": 40_000,
                          "win": "He finds the sweet spot. The door sighs open.", "fail": "The bit snaps off in the housing.",
                          "clutch": "Bit's about to seize — ease off at the exact right second."},
                         {"label": "Burn it with thermite", "role": "boxman", "base": 36, "good": 105_000, "bad": 45_000,
                          "win": "White-hot and fast — the door gives.", "fail": "The burn warps the frame and jams it half-open.",
                          "clutch": "It's jamming — wedge it before it seizes shut."}]},
            {"icon": "💵", "text": "Vault's open. Pallets of banded cash and a wall of safe-deposit boxes. Load what you came for.",
             "choices": [{"label": "Sweep the cash drawers", "role": "muscle", "base": 54, "good": 90_000, "bad": 28_000,
                          "win": "Duffels full of clean stacks. This is the number you came for.", "fail": "A dye pack you missed bursts in the bag.",
                          "clutch": "Dye pack arming — ditch that bundle before it blows."}]},
        ],
        "greed": [
            {"icon": "🗃️", "text": "The safe-deposit boxes. Drill a row and you can't know what you'll get — but rich people hide rich things.",
             "choices": [{"label": "Drill the VIP row", "role": "boxman", "base": 36, "good": 200_000, "bad": 80_000,
                          "win": "Cash, bonds, a velvet bag of stones. Pure profit.", "fail": "Half come up empty and you've burned precious minutes.",
                          "clutch": "Time's bleeding — get the high-number boxes open NOW."}]},
            {"icon": "👔", "text": "There's a second vault — the manager's private hold for the high-net clients. Nobody hits that and walks away. You could be nobody.",
             "choices": [{"label": "Take the private vault", "role": "boxman", "base": 28, "good": 400_000, "bad": 160_000, "crit": True,
                          "win": "Gold, cash, and paper worth more than the building. Legends are made of this.", "fail": "The hold's on its own loop — every cop in the city just woke up.",
                          "clutch": "That loop's screaming — clear the hold in five or you're done."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Duffels stacked, the lobby alarm finally howling, your driver flooring it to the curb.",
                    "choices": [{"label": "Straight shot down the avenue", "role": "driver", "base": 46, "crit": True,
                                 "win": "He splits the traffic and the city swallows you whole.", "fail": "They've strung a roadblock clean across the avenue.",
                                 "clutch": "Roadblock ahead — find the gap or get caught with all of it."},
                                {"label": "Through the parking structure to the swap car", "role": "driver", "base": 56, "crit": True,
                                 "win": "Up, around, into a clean car two levels down. Vanished.", "fail": "They seal the structure's exits behind you.",
                                 "clutch": "Gates dropping on the exits — beat the last one down."}]},
    },
    "casino": {
        "name": "The Casino Count Room", "icon": "🎰", "cred": 8, "est": 750_000, "roles": ["driver", "muscle", "hacker", "boxman", "face"],
        "blurb": "Where the house keeps its cash. You don't get in without a man on the inside and a face that can lie to a pit boss.",
        "case": [
            {"id": "comp", "label": "Comp a weekend, learn the floor", "cost": 25_000, "bonus": 7, "note": "You know the pit bosses' rotations and the cage shifts."},
            {"id": "deal", "label": "Flip a dealer for the count-room schedule", "cost": 60_000, "bonus": 12, "note": "You'll hit it during the drop — when the cash is all in one place."},
        ],
        "beats": [
            {"icon": "🎭", "text": "Getting back-of-house means a keycard door and a very alert pit boss. This is the face's moment.",
             "choices": [{"label": "Walk in as a gaming inspector", "role": "face", "base": 42, "good": 180_000, "bad": 70_000,
                          "win": "Clipboard, confidence, a flashed badge — they hold the door.", "fail": "The boss asks for a credential you don't have.",
                          "clutch": "He's calling to verify your badge — sell it, hard."},
                         {"label": "Inside man buzzes you through", "role": "face", "base": 46, "good": 170_000, "bad": 65_000,
                          "win": "A nod from your guy and the lock clicks green.", "fail": "His relief came in early — wrong man at the desk.",
                          "clutch": "Stranger at the desk — improvise before he calls it in."}]},
            {"icon": "📹", "text": "The surveillance room — the 'eye in the sky' — watches everything. Blind it or the whole floor's against you.",
             "choices": [{"label": "Loop the eye", "role": "hacker", "base": 40, "good": 185_000, "bad": 72_000,
                          "win": "Every monitor plays a quiet night on repeat.", "fail": "An operator notices the timestamp's frozen.",
                          "clutch": "He's reaching for the floor phone — cut the line first."}]},
            {"icon": "🔐", "text": "The count-room vault, where the day's drop sits being tallied. Your boxman's whole reason for coming.",
             "choices": [{"label": "Crack the count-room vault", "role": "boxman", "base": 38, "good": 195_000, "bad": 78_000,
                          "win": "The door swings on a room knee-deep in banded cash.", "fail": "The seismic sensor in the door trips.",
                          "clutch": "Sensor's arming — still the door before it locks the room down."}]},
            {"icon": "🧰", "text": "Inside: more cash than you've seen in one place in your life. Load it before the drop team's break ends.",
             "choices": [{"label": "Bag the cage and the drop", "role": "muscle", "base": 50, "good": 190_000, "bad": 60_000,
                          "win": "Carts of cash straight into the laundry bins. Genius.", "fail": "A drop-team guard wanders back early.",
                          "clutch": "Guard's keying in — be ready at the door."}]},
        ],
        "greed": [
            {"icon": "🃏", "text": "The high-limit cage holds the whales' markers and a vault of chips you can wash dirty. Greedy. Beautiful.",
             "choices": [{"label": "Hit the high-limit cage", "role": "boxman", "base": 34, "good": 300_000, "bad": 120_000,
                          "win": "Plaques and markers worth a fortune. The whales will weep.", "fail": "The cage has a time-delay you didn't budget for.",
                          "clutch": "Delay timer ticking — pop it before it freezes."}]},
            {"icon": "💎", "text": "The owner's private vault behind the count room — the skim, untaxed, off every book. Touch it and there's no going back, ever.",
             "choices": [{"label": "Take the owner's skim", "role": "boxman", "base": 26, "good": 700_000, "bad": 280_000, "crit": True,
                          "win": "Stacks the taxman never knew existed. You just robbed a robber blind.", "fail": "His private alarm goes straight to people far worse than cops.",
                          "clutch": "That alarm reaches very bad men — clear it in five seconds flat."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Laundry bins of cash, the floor finally catching on, your driver waiting at the loading dock.",
                    "choices": [{"label": "Out through the service tunnels", "role": "driver", "base": 48, "crit": True,
                                 "win": "Down through the kitchens and out a delivery ramp. Ghosts.", "fail": "Security floods the tunnels behind you.",
                                 "clutch": "They're sealing the tunnel — make the ramp first."},
                                {"label": "Blend into the valet chaos", "role": "driver", "base": 54, "crit": True,
                                 "win": "You roll out in the valet line like any other high roller.", "fail": "They lock the garage — you're trapped in the line.",
                                 "clutch": "Garage gates dropping — slip out before they seal it."}]},
    },
    "bigone": {
        "name": "The Big One", "icon": "🏛️", "cred": 9, "est": 1_600_000, "roles": ["driver", "muscle", "hacker", "boxman", "face"],
        "blurb": "A private depository — where institutions that can't use real banks stash untraceable cash. Three rings of security, a four-minute response clock, and a legend waiting on the other side. One night. No second chances.",
        "case": [
            {"id": "months", "label": "Months of surveillance", "cost": 60_000, "bonus": 7, "note": "You know the guard rotations down to the minute."},
            {"id": "inside", "label": "Buy a man on the inside", "cost": 150_000, "bonus": 12, "note": "He'll kill the inner door's failsafe at the exact moment."},
        ],
        "beats": [
            {"icon": "🚁", "text": "The roof, midnight. Armed patrols, a grid of motion lasers, and a four-minute armed-response clock the instant you trip anything.",
             "choices": [{"label": "Rappel in through the skylight", "role": "muscle", "base": 38, "good": 320_000, "bad": 130_000,
                          "win": "Silent descent, boots down between the beams. You're in.", "fail": "A boot clips a laser — the clock starts ticking.",
                          "clutch": "You broke a beam — kill the relay before it makes the call."}]},
            {"icon": "💻", "text": "First ring: a lattice of motion sensors feeding the master alarm spine. Blind all of it or die trying.",
             "choices": [{"label": "Splice the alarm spine", "role": "hacker", "base": 36, "good": 330_000, "bad": 140_000,
                          "win": "The whole building goes dumb. Every sensor sleeps.", "fail": "A redundant node screams to the response center.",
                          "clutch": "Backup node waking — sever it before the call connects."}]},
            {"icon": "🎭", "text": "The inner door needs two things: a biometric you have to talk a guard into giving, and a code only the night manager carries.",
             "choices": [{"label": "Run the con on the night manager", "role": "face", "base": 38, "good": 340_000, "bad": 145_000,
                          "win": "You walk him right up and his own thumb opens the door.", "fail": "He sees through it and reaches for the panic stud.",
                          "clutch": "His thumb's drifting to the panic button — stop him cold."}]},
            {"icon": "🔐", "text": "The main vault. A door built to survive a bomb. Your boxman's whole career has led to this single moment.",
             "choices": [{"label": "Defeat the vault", "role": "boxman", "base": 34, "good": 350_000, "bad": 150_000,
                          "win": "Forty minutes of genius compressed into eight. The door yawns open.", "fail": "The relockers fire — the door's a tomb.",
                          "clutch": "Relockers tripping — hit the override this instant."}]},
            {"icon": "💵", "text": "Beyond the door: pallets. Shrink-wrapped bricks of cash stacked to the ceiling. More money than you can comprehend.",
             "choices": [{"label": "Load the cart — every second counts", "role": "muscle", "base": 48, "good": 320_000, "bad": 110_000,
                          "win": "Bricks by the armful. The response clock be damned.", "fail": "You overload the cart and a wheel buckles.",
                          "clutch": "Cart's tipping — steady it and keep moving."}]},
        ],
        "greed": [
            {"icon": "🏷️", "text": "A sealed room off the vault — bearer bonds and cartel paper. Untraceable, weightless, worth a fortune.",
             "choices": [{"label": "Take the paper room", "role": "boxman", "base": 30, "good": 800_000, "bad": 320_000,
                          "win": "Folders of bonds worth more than the cash on your back.", "fail": "It's on a separate trigger — your response clock just halved.",
                          "clutch": "You cut the timeline in half — clear the room NOW."}]},
            {"icon": "☠️", "text": "And the last door. Whatever's behind it, the people who own this place will hunt you to the ends of the earth for it. Point of no return.",
             "choices": [{"label": "Open the last door", "role": "boxman", "base": 24, "good": 1_600_000, "bad": 700_000, "crit": True,
                          "win": "Gold bars and a number with too many zeros. You just became a myth — and a marked man for life.", "fail": "It was bait. The trap closes and the real guns arrive.",
                          "clutch": "The trap's springing — beat it shut in five seconds or it's over."}]},
        ],
        "getaway": {"icon": "🚗", "text": "Everything you can carry, the four-minute clock long expired, the whole city's law bearing down. Your driver's been counting every second.",
                    "choices": [{"label": "The planned route — full commitment", "role": "driver", "base": 44, "crit": True,
                                 "win": "Every turn rehearsed a hundred times. You disappear like you were never there.", "fail": "They predicted the route — it's a gauntlet of cruisers.",
                                 "clutch": "They're waiting on the route — break off it before they close the net."},
                                {"label": "Go dark — switch cars, walk away clean", "role": "driver", "base": 52, "crit": True,
                                 "win": "Three cars, a tunnel, and a quiet walk into a brand new life.", "fail": "The switch point's already crawling with units.",
                                 "clutch": "Units at the swap — make the change before they lock it down."}]},
    },
}
DARK_HEIST_ORDER = ["checkcash", "jewelry", "armored", "bank", "casino", "bigone"]

DARK_HEIST_LOCKOUT = 28   # days all scores go cold after a bust (one season-month); a level-up lifts it

def _dark_heist_playable(key):
    return bool(DARK_HEISTS.get(key, {}).get("beats"))

def _dark_scores_locked(s):
    """After a busted score everything's too hot to touch for a month — unless you've ranked up
    since (a level-up clears it, so the score you just unlocked AND the busted one are back)."""
    d = s["dark"]
    if d.get("heist_lockout", 0) <= s.get("day", 1): return False
    if d.get("cred", 1) > d.get("heist_lockout_cred", 0): return False   # leveled up → lockout lifted
    return True

def _heist_member(d, mid):
    return next((m for m in d.get("heist_crew", []) if m["id"] == mid), None)

def _dark_heist_ensure_pool(d):
    """The crew are permanent people: exactly 3 named specialists per role (one per tier).
    Idempotent + self-repairing — keeps existing (leveled) members, dedupes extras, fills any
    gaps. Safe to run on every load, so old duplicated/partial pools get fixed automatically."""
    crew = d.get("heist_crew", [])
    valid_tiers = [t["tier"] for t in DARK_HEIST_TIERS]
    rebuilt = []
    for role in DARK_HEIST_ROLES:
        members = [m for m in crew if m.get("role") == role]
        by_tier = {}
        for m in members:                       # keep the best (most-leveled) member per tier
            t = m.get("tier")
            if t in valid_tiers and (t not in by_tier or m.get("skill", 0) > by_tier[t].get("skill", 0)):
                by_tier[t] = m
        names = DARK_HEIST_NAMES.get(role, ["Smith", "Jones", "Doe"]); used = set()
        for td in DARK_HEIST_TIERS:
            keep = by_tier.get(td["tier"])
            if keep:
                keep["cut"] = td["cut"]; rebuilt.append(keep); used.add(keep.get("name"))
            else:
                avail = [n for n in names if n not in used] or names
                nm = random.choice(avail); used.add(nm)
                mid = d.get("next_heist_member", 1); d["next_heist_member"] = mid + 1
                rebuilt.append({"id": mid, "role": role, "tier": td["tier"], "name": nm,
                                "cut": td["cut"], "skill": td["skill"]})
    d["heist_crew"] = rebuilt
    h = d.get("heist")                            # drop any now-dangling crew assignments
    if h and isinstance(h.get("crew"), dict):
        valid = {m["id"] for m in rebuilt}
        h["crew"] = {r: mid for r, mid in h["crew"].items() if mid in valid}

def _dark_heist_chance(h, d, opt):
    base = opt.get("base", 50) + h.get("case_bonus", 0)
    role = opt.get("role")
    if role and h.get("crew", {}).get(role):
        m = _heist_member(d, h["crew"][role])
        if m: base += m.get("skill", 1) * DARK_HEIST_SKILL_BUFF
    return max(5, min(95, base))

def _dark_heist_curbeat(h, defn):
    ph = h.get("phase"); idx = h.get("idx", 0)
    if ph == "getaway": return defn.get("getaway")
    if ph == "greed":
        g = defn.get("greed", []); return g[idx] if idx < len(g) else None
    if ph == "core":
        b = defn.get("beats", []); return b[idx] if idx < len(b) else None
    return None

def _dark_heist_set_beat(h, d):
    """Stash a client-facing view of the current beat (with crew/casing-adjusted odds)."""
    defn = DARK_HEISTS.get(h["key"], {})
    beat = _dark_heist_curbeat(h, defn)
    if not beat:
        h["beat"] = None; return
    h["beat"] = {"icon": beat["icon"], "text": beat["text"], "getaway": h.get("phase") == "getaway",
                 "choices": [{"label": c["label"], "role": c.get("role"), "crit": bool(c.get("crit")),
                              "chance": _dark_heist_chance(h, d, c)} for c in beat["choices"]]}

def _dark_heist_finish(s, d, busted):
    h = d.get("heist");  defn = DARK_HEISTS.get(h["key"], {})
    if busted:
        _dark_trigger_hunt(s, bump=40)        # getting caught mid-score puts Marsh onto your ops
        # All scores go cold for a month (28 days) — unless you level up, which lifts it early
        # (the score your new rank unlocks AND the one you busted both come back).
        d["heist_lockout"] = s.get("day", 1) + DARK_HEIST_LOCKOUT
        d["heist_lockout_cred"] = d.get("cred", 1)
        h["stage"] = "done"; h["outcome"] = "bust"
        h["final"] = {"your": 0, "cut": 0, "pot": 0}
        return
    pot = h.get("pot", 0)
    members = [_heist_member(d, mid) for mid in h.get("crew", {}).values()]
    cut_pct = sum(m["cut"] for m in members if m)
    cut_amt = round(pot * cut_pct / 100.0)
    your = max(0, pot - cut_amt)
    d["dirty_money"] = d.get("dirty_money", 0) + your   # a clean getaway leaves no heat behind
    d["cred_xp"] = d.get("cred_xp", 0) + round(your / 500)
    for m in members:
        if m: m["skill"] = min(6, m.get("skill", 1) + 1)
    d.setdefault("heists_done", []).append(h["key"])
    d.setdefault("heist_takes", {})[h["key"]] = your   # remember what this score banked
    h["stage"] = "done"; h["outcome"] = "win"
    h["final"] = {"your": your, "cut": cut_amt, "pot": pot, "cut_pct": cut_pct}

# ── Events — fire on Advance, each a choice with good/bad/quirky outcomes. ──
# req gates eligibility: always | crew | lab | dealer | business.
# effects apply cash / dirty_money / heat (global). "special" runs a coded handler.
DARK_EVENTS = [
    {"key": "cop_take", "icon": "👮", "req": "always",
     "text": "A patrol cop catches your eye and taps his badge. \"Be a shame if I had to start writing things down.\"",
     "choices": [{"label": "Slip him an envelope", "result": "He pockets it and forgets your face.", "effects": {"cash": -4000, "heat": -18}},
                 {"label": "Play dumb", "result": "He writes something down. Great.", "effects": {"heat": 10}}]},
    {"key": "snitch", "icon": "🐀", "req": "crew",
     "text": "Word is one of your guys has been chatting with someone who reeks of 'undercover.'",
     "choices": [{"label": "Pay him to stay quiet", "result": "Money talks. He stays loyal.", "effects": {"cash": -3000, "heat": -5}},
                 {"label": "Cut him loose", "result": "You show him the door before he shows the cops yours.", "effects": {"heat": -8}, "special": "lose_crew_member"}]},
    {"key": "lab_fire", "icon": "🔥", "req": "lab",
     "text": "A hot plate left on overnight nearly took a whole lab — and the block — up in flames.",
     "choices": [{"label": "Pay for quiet repairs", "result": "Patched up before anyone asks questions.", "effects": {"cash": -2500}},
                 {"label": "Air it out and hope", "result": "The neighbors definitely noticed.", "effects": {"heat": 12}}]},
    {"key": "dealer_jumped", "icon": "🥊", "req": "dealer",
     "text": "One of your dealers got jumped on his corner. He wants to know if you'll cover what they took.",
     "choices": [{"label": "Make him whole", "result": "He's grateful. Loyalty bought cheap.", "effects": {"cash": -2500}},
                 {"label": "\"That's the job\"", "result": "He eats the loss — and the grudge.", "effects": {"heat": 4}, "special": "dealer_lose_held"}]},
    {"key": "bulk_buyer", "icon": "🤝", "req": "lab",
     "text": "A club promoter wants a bulk order — cash up front, no questions.",
     "choices": [{"label": "Make the deal", "result": "Easiest money you've made all week.", "effects": {"dirty_money": 4000}},
                 {"label": "Smells like a setup — pass", "result": "Maybe paranoid. Maybe alive.", "effects": {"heat": -3}}]},
    {"key": "wall_cash", "icon": "💵", "req": "always",
     "text": "Renovating one of your places, you found a roll of cash a previous tenant stashed in the wall.",
     "choices": [{"label": "Pocket it", "result": "Finders keepers — straight into your pocket.", "effects": {"cash": 1800}}]},
    {"key": "junkie", "icon": "💉", "req": "crew",
     "text": "One of your guys 'quality tested' a little too much of the product. Again.",
     "choices": [{"label": "Dock his cut", "result": "He grumbles, but gets the message.", "effects": {"cash": 300}},
                 {"label": "Let it slide", "result": "Morale stays up; inventory does not.", "effects": {"heat": 2}}]},
    {"key": "livestream", "icon": "📱", "req": "lab",
     "text": "A crew member livestreamed the lab 'as a joke.' It got 4,000 views before he deleted it.",
     "choices": [{"label": "Pay a guy to scrub it", "result": "Gone. Probably.", "effects": {"cash": -1200}},
                 {"label": "Pray nobody important saw", "result": "Bold strategy.", "effects": {"heat": 14}}]},
    {"key": "abuela", "icon": "🫔", "req": "crew",
     "text": "The cook's abuela showed up and fed the whole crew. Morale's through the roof.",
     "choices": [{"label": "Let them enjoy it", "result": "A happy crew is a careful crew.", "effects": {"heat": -7}}]},
    {"key": "inspector", "icon": "📋", "req": "business",
     "text": "A surprise inspector is poking around one of your fronts, clipboard in hand.",
     "choices": [{"label": "Grease the clipboard", "result": "He finds everything 'in order.'", "effects": {"cash": -2000}},
                 {"label": "Let him look", "result": "He left frowning.", "effects": {"heat": 9}}]},
    {"key": "rival_push", "icon": "🔪", "req": "crew",
     "text": "A rival crew is muscling onto one of your corners.",
     "choices": [{"label": "Push back hard", "result": "You hold the block — loudly.", "effects": {"heat": 8, "cash": 1200}},
                 {"label": "Give them the corner", "result": "Not worth the bodies. This time.", "effects": {"dirty_money": -1500}}]},
    {"key": "cartel_tip", "icon": "📦", "req": "lab",
     "text": "Your supplier slips you a tip: a pallet of supplies 'fell off a truck.' Cheap.",
     "choices": [{"label": "Buy the load", "result": "Free supplies hit your stash.", "effects": {"cash": -1500}, "special": "free_supplies"},
                 {"label": "Pass", "result": "Too good to be true, usually is.", "effects": {}}]},
    {"key": "quiet_week", "icon": "😌", "req": "always",
     "text": "Quiet week on the block. The heat's died down on its own.",
     "choices": [{"label": "Enjoy the calm", "result": "Things cool off.", "effects": {"heat": -12}}]},
    {"key": "old_debt", "icon": "💰", "req": "always",
     "text": "An old debt finally got paid back — in grimy, unmarked bills.",
     "choices": [{"label": "Take the dirty cash", "result": "Straight onto the pile that needs washing.", "effects": {"dirty_money": 3000}}]},
]

def _dark_eligible_events(s):
    d = s["dark"]
    has = {
        "always":   True,
        "crew":     any(_dark_crew_members(d, c) for c in d.get("crews", [])),
        "lab":      any(p.get("lab") for p in s["properties"]),
        "dealer":   bool(d.get("dealers")),
        "business": any((d.get("biz") or {}).get(k) for k in ("laundromat", "car_wash", "strip_club", "casino", "pizzeria")),
    }
    return [e for e in DARK_EVENTS if has.get(e["req"])]

def _dark_gen_home_market(s):
    # 3 buyable homes/day, refreshed each advance. Homes are just lab/rent locations now
    # (no flipping), so prices sit in a flat, moderate band rather than legit market values.
    hoods = get_unlocked_neighborhoods(s.get("level", 0)) or list(NEIGHBORHOODS.keys())
    # Prices creep up as you buy more (gentle +8%/purchase, capped) — homes get pricier
    # the bigger your operation gets, but never runaway.
    mult = min(4.0, 1 + 0.08 * s["dark"].get("homes_bought", 0))
    nid = s["next_id"]; homes = []
    for _ in range(3):
        p = generate_property(nid, hoods=[random.choice(hoods)]); nid += 1
        base = random.randint(20, 80) * 1000   # ~$20k–$80k before scaling
        p["purchase_price"] = int(round(base * mult / 1000)) * 1000
        p["foreclosure"] = False
        homes.append(p)
    s["next_id"] = nid
    s["dark"]["home_market"] = homes

def _dark_rent_options(prop):
    # 3 tenant choices (from the real tenant pool) — all pay ~the same, no downsides.
    base = max(50, int(calc_fair_weekly_rent(prop)))
    tier = NEIGHBORHOODS.get(prop.get("neighborhood", ""), {}).get("tier", "mid")
    pool = [t for t in TENANT_PROFILES if t.get("unique") and tier in t.get("tiers", ["budget", "mid", "premium"])]
    if len(pool) < 3:
        pool += [t for t in TENANT_PROFILES if tier in t.get("tiers", ["budget", "mid", "premium"])]
    if len(pool) < 3:
        pool = list(TENANT_PROFILES)
    picks = random.sample(pool, min(3, len(pool)))
    return [{"name": t["name"], "icon": t.get("icon", "🧑"), "desc": t.get("desc", ""),
             "rent": int(round(base * random.uniform(0.95, 1.05)))} for t in picks]

@app.route('/api/dark/buy_supplies', methods=['POST'])
def api_dark_buy_supplies():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; drug = (request.json or {}).get("drug")
    sup = DARK_SUPPLIES.get(drug); dm = DARK_DRUGS.get(drug)
    if not sup or not dm: return jsonify({"error": "No such supplies."}), 400
    if dm["cred_req"] > d.get("cred", 1):
        return jsonify({"error": f"{dm['name']} supplies unlock at Street Cred {dm['cred_req']}."}), 400
    price = _dark_supply_price(drug, d)
    if s["cash"] < price:
        return jsonify({"error": f"Need ${price:,} for {sup['name']}."}), 400
    s["cash"] -= price
    d.setdefault("supplies", {})[drug] = d.get("supplies", {}).get(drug, 0) + 1
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/put_word_out', methods=['POST'])
def api_dark_put_word_out():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; FEE = 2_000
    if d.get("recruits_refresh_day") and d["recruits_refresh_day"] > s["day"]:
        return jsonify({"error": "Word's already out — new faces show up tomorrow."}), 400
    if s["cash"] < FEE: return jsonify({"error": f"Need ${FEE:,} to put the word out."}), 400
    s["cash"] -= FEE
    d["recruits_refresh_day"] = s["day"] + 1
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/hire_recruit', methods=['POST'])
def api_dark_hire_recruit():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; rid = (request.json or {}).get("recruit_id")
    rec = next((r for r in d.get("recruits", []) if r["id"] == rid), None)
    if not rec: return jsonify({"error": "They've already moved on."}), 400
    trait = DARK_TRAITS.get(rec["trait"]); cost = (trait or {}).get("cost", 2000)
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to bring {rec['name']} on."}), 400
    s["cash"] -= cost
    d["recruits"] = [r for r in d["recruits"] if r["id"] != rid]
    d.setdefault("roster", []).append({"id": rec["id"], "name": rec["name"], "trait": rec["trait"], "crew_id": None})
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/dismiss_roster', methods=['POST'])
def api_dark_dismiss_roster():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; mid = (request.json or {}).get("member_id")
    d["roster"] = [m for m in d.get("roster", []) if m["id"] != mid]
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/form_crew', methods=['POST'])
def api_dark_form_crew():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    mids = data.get("member_ids") or []
    members = [m for m in d.get("roster", []) if m["id"] in mids]
    if not (3 <= len(members) <= 5):
        return jsonify({"error": "A crew needs 3 to 5 people."}), 400
    if any(m.get("crew_id") is not None for m in members):
        return jsonify({"error": "Someone in that group is already in a crew."}), 400
    cid = d.get("next_crew_id", 1); d["next_crew_id"] = cid + 1
    name = (data.get("name") or "").strip() or f"Crew #{cid}"
    d.setdefault("crews", []).append({"id": cid, "name": name, "home_id": None})
    for m in members: m["crew_id"] = cid
    save(s)
    return jsonify({"ok": True, "crew_id": cid})

@app.route('/api/dark/disband_crew', methods=['POST'])
def api_dark_disband_crew():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; cid = (request.json or {}).get("crew_id")
    crew = _dark_crew_by_id(d, cid)
    if not crew: return jsonify({"error": "No such crew."}), 400
    if crew.get("home_id") is not None:   # pull them off the lab (any in-progress batch is lost)
        p = next((x for x in s["properties"] if x.get("id") == crew["home_id"]), None)
        if p and p.get("lab"): p["lab"] = None
    for m in d.get("roster", []):
        if m.get("crew_id") == cid: m["crew_id"] = None
    d["crews"] = [c for c in d.get("crews", []) if c["id"] != cid]
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/rename_crew', methods=['POST'])
def api_dark_rename_crew():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    crew = _dark_crew_by_id(d, data.get("crew_id"))
    if not crew: return jsonify({"error": "No such crew."}), 400
    name = (data.get("name") or "").strip()
    if not name: return jsonify({"error": "Give the crew a name."}), 400
    crew["name"] = name[:24]   # keep it tidy on the cards
    save(s)
    return jsonify({"ok": True, "name": crew["name"]})

@app.route('/api/dark/assign_lab', methods=['POST'])
def api_dark_assign_lab():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    crew = _dark_crew_by_id(d, data.get("crew_id"))
    p = next((x for x in s["properties"] if x.get("id") == data.get("prop_id")), None)
    drug = data.get("drug"); dm = DARK_DRUGS.get(drug)
    if not crew or not p or not dm: return jsonify({"error": "Bad crew, home, or product."}), 400
    if crew.get("home_id") is not None: return jsonify({"error": "That crew's already working a lab."}), 400
    if p.get("lab"): return jsonify({"error": "That home's already a lab."}), 400
    if dm["cred_req"] > d.get("cred", 1):
        return jsonify({"error": f"{dm['name']} needs Street Cred {dm['cred_req']}."}), 400
    if drug not in _dark_crew_knows(d, crew):
        return jsonify({"error": f"Nobody in this crew knows how to cook {dm['name']}."}), 400
    p["rented"] = False; p["tenant"] = None            # lab OR rental — never both
    p["lab"] = {"drug": drug, "speed": 2, "heat": 0, "product": 0, "batch": None, "crew_id": crew["id"],
                "owed": 0, "owed_since": None, "temper": 0}
    crew["home_id"] = p["id"]
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/set_lab_speed', methods=['POST'])
def api_dark_set_lab_speed():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    data = request.json or {}
    p = next((x for x in s["properties"] if x.get("id") == data.get("prop_id")), None)
    if not p or not p.get("lab"): return jsonify({"error": "Not a lab."}), 400
    p["lab"]["speed"] = max(1, min(3, int(data.get("speed", 2))))
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/start_batch', methods=['POST'])
def api_dark_start_batch():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    p = next((x for x in s["properties"] if x.get("id") == data.get("prop_id")), None)
    if not p or not p.get("lab"): return jsonify({"error": "Not a lab."}), 400
    lab = p["lab"]
    if lab.get("batch"): return jsonify({"error": "A batch is already cooking here."}), 400
    if lab.get("owed", 0) > 0: return jsonify({"error": "Pay your crew their cut before they'll start another batch."}), 400
    crew = _dark_crew_by_id(d, lab.get("crew_id")); members = _dark_crew_members(d, crew) if crew else []
    if not crew or not members: return jsonify({"error": "This lab has no working crew."}), 400
    drug = lab["drug"]
    if d.get("supplies", {}).get(drug, 0) < 1:
        sup = DARK_SUPPLIES.get(drug) or {}
        return jsonify({"error": f"No {sup.get('name', 'supplies')} — buy some at the Fence first."}), 400
    speed = max(1, min(3, int(data.get("speed", lab.get("speed", 2))))); lab["speed"] = speed
    d["supplies"][drug] -= 1
    n = len(members); wh = sum(1 for m in members if m.get("trait") == "workhorse")
    yld = max(1, round(DARK_DRUGS[drug]["base_yield"] * DARK_BATCH_YIELD * (0.7 + 0.15 * n) * (1 + 0.25 * wh)))
    lab["batch"] = {"speed": speed, "days_left": DARK_BATCH_DAYS[speed], "yield": yld}
    save(s)
    return jsonify({"ok": True, "yield": yld, "days": DARK_BATCH_DAYS[speed]})

@app.route('/api/dark/pay_crew', methods=['POST'])
def api_dark_pay_crew():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    p = next((x for x in s["properties"] if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p or not p.get("lab"): return jsonify({"error": "Not a lab."}), 400
    lab = p["lab"]; owed = lab.get("owed", 0)
    if owed <= 0: return jsonify({"error": "Your crew isn't owed anything right now."}), 400
    if s["cash"] < owed: return jsonify({"error": f"Need ${owed:,} clean to settle up with the crew."}), 400
    s["cash"] -= owed
    lab["owed"] = 0; lab["owed_since"] = None; lab["temper"] = 0
    save(s)
    return jsonify({"ok": True, "paid": owed})

@app.route('/api/dark/dismantle_lab', methods=['POST'])
def api_dark_dismantle_lab():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; p = next((x for x in s["properties"] if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p or not p.get("lab"): return jsonify({"error": "Not a lab."}), 400
    cid = p["lab"].get("crew_id")
    crew = _dark_crew_by_id(d, cid) if cid is not None else None
    if crew: crew["home_id"] = None
    p["lab"] = None
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/toggle_rent', methods=['POST'])
def api_dark_toggle_rent():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    p = next((x for x in s["properties"] if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p: return jsonify({"error": "No such property."}), 400
    if p.get("lab"): return jsonify({"error": "It's a lab — dismantle it first."}), 400
    p["rented"] = not p.get("rented")
    if not p["rented"]:
        p["tenant"] = None; p.pop("rent_options", None)   # evicted
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/rent_options', methods=['POST'])
def api_dark_rent_options():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    p = next((x for x in s["properties"] if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p: return jsonify({"error": "No such property."}), 400
    if p.get("lab"): return jsonify({"error": "It's a lab — dismantle it first."}), 400
    if p.get("rented"): return jsonify({"error": "Already rented."}), 400
    p["rent_options"] = _dark_rent_options(p)
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/rent_pick', methods=['POST'])
def api_dark_rent_pick():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    data = request.json or {}
    p = next((x for x in s["properties"] if x.get("id") == data.get("prop_id")), None)
    if not p: return jsonify({"error": "No such property."}), 400
    opts = p.get("rent_options") or []
    idx = data.get("idx")
    if not isinstance(idx, int) or idx < 0 or idx >= len(opts):
        return jsonify({"error": "Pick a tenant."}), 400
    o = opts[idx]
    p["rented"] = True
    p["tenant"] = {"name": o["name"], "icon": o.get("icon", "🧑"), "rent": o["rent"], "next_pay": s["day"] + 7}
    p.pop("rent_options", None)
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/buy_home', methods=['POST'])
def api_dark_buy_home():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; mkt = d.get("home_market", [])
    p = next((x for x in mkt if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p: return jsonify({"error": "That listing's already gone."}), 400
    price = p.get("purchase_price", 0)
    if s["cash"] < price: return jsonify({"error": f"Need ${price:,} for that place."}), 400
    s["cash"] -= price
    p["rented"] = False; p["lab"] = None; p["tenant"] = None
    s["properties"].append(p)
    d["home_market"] = [x for x in mkt if x.get("id") != p["id"]]
    d["homes_bought"] = d.get("homes_bought", 0) + 1   # nudges future market prices up
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/sell_vending', methods=['POST'])
def api_dark_sell_vending():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; biz = d.setdefault("biz", {})
    if not biz.get("vending"): return jsonify({"error": "No vending business to sell."}), 400
    s["cash"] += DARK_VENDING_PAYOUT
    biz["vending"] = False
    d["corners_unlocked"] = True
    save(s)
    return jsonify({"ok": True, "payout": DARK_VENDING_PAYOUT})

@app.route('/api/dark/buy_business', methods=['POST'])
def api_dark_buy_business():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; biz = d.setdefault("biz", {}); key = (request.json or {}).get("key")
    price = DARK_BIZ_PRICE.get(key)
    if price is None: return jsonify({"error": "Can't buy that."}), 400
    if biz.get(key): return jsonify({"error": "You already run that."}), 400
    if s["cash"] < price: return jsonify({"error": f"Need ${price:,}."}), 400
    s["cash"] -= price; biz[key] = True
    if key == "strip_club" and not d.get("club"): _dark_club_init(d)
    if key in DARK_LAUNDER and not d.get("debt_active"):   # first laundering front → the Fixer calls in his marker
        _dark_activate_debt(s)
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/convert_casino', methods=['POST'])
def api_dark_convert_casino():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; biz = d.setdefault("biz", {})
    if biz.get("casino"): return jsonify({"error": "It's already a casino."}), 400
    if not biz.get("arcade_had"): return jsonify({"error": "You've got no arcade to convert."}), 400
    if s["cash"] < DARK_CASINO_COST: return jsonify({"error": f"Need ${DARK_CASINO_COST:,} to convert it."}), 400
    s["cash"] -= DARK_CASINO_COST; biz["casino"] = True
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/hire_manager', methods=['POST'])
def api_dark_hire_manager():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; key = (request.json or {}).get("front"); meta = DARK_LAUNDER.get(key)
    if not meta or not (d.get("biz") or {}).get(key): return jsonify({"error": "You don't run that front."}), 400
    ln = d.setdefault("launder", {}).setdefault(key, {"manager": False, "heat": 0, "rate": 0})
    if ln.get("manager"): return jsonify({"error": "Already got a manager there."}), 400
    if s["cash"] < meta["hire"]: return jsonify({"error": f"Need ${meta['hire']:,} to bring one on."}), 400
    s["cash"] -= meta["hire"]; ln["manager"] = True
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/fire_manager', methods=['POST'])
def api_dark_fire_manager():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    ln = ((s["dark"].get("launder") or {}).get((request.json or {}).get("front")))
    if ln: ln["manager"] = False; ln["rate"] = 0
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/set_launder_rate', methods=['POST'])
def api_dark_set_launder_rate():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}; key = data.get("front")
    if key not in DARK_LAUNDER or not (d.get("biz") or {}).get(key): return jsonify({"error": "You don't run that front."}), 400
    ln = d.setdefault("launder", {}).setdefault(key, {"manager": False, "heat": 0, "rate": 0})
    ln["rate"] = max(0, min(3, int(data.get("rate", 0))))
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/collect_lab', methods=['POST'])
def api_dark_collect_lab():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    p = next((x for x in s["properties"] if x.get("id") == (request.json or {}).get("prop_id")), None)
    if not p or not p.get("lab"): return jsonify({"error": "Not a lab."}), 400
    units = p["lab"].get("product", 0)
    if units <= 0: return jsonify({"error": "Nothing to collect yet."}), 400
    _dark_stash_add(s["dark"], p["lab"]["drug"], units)
    p["lab"]["product"] = 0
    save(s)
    return jsonify({"ok": True, "collected": units})

@app.route('/api/dark/self_cook', methods=['POST'])
def api_dark_self_cook():
    # Player cooks a batch by hand (the minigame): consumes 1 supply, product → stash,
    # yield scaled by their score. No crew, no cut. Adds a little heat to the operation.
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    drug = data.get("drug"); dm = DARK_DRUGS.get(drug)
    p = next((x for x in s["properties"] if x.get("id") == data.get("prop_id")), None)
    if not p or not dm: return jsonify({"error": "Bad cook."}), 400
    if p.get("lab") or p.get("rented"): return jsonify({"error": "You can only hand-cook in a vacant house."}), 400
    if dm["cred_req"] > d.get("cred", 1): return jsonify({"error": f"{dm['name']} unlocks at Street Cred {dm['cred_req']}."}), 400
    today = s.get("day")
    if d.get("cook_day") != today: d["cook_day"] = today; d["cooks_today"] = 0   # new day → reset the counter
    if d.get("cooks_today", 0) >= DARK_SELFCOOK_PER_DAY:
        return jsonify({"error": f"You've cooked all {DARK_SELFCOOK_PER_DAY} of today's hand-batches — come back tomorrow."}), 400
    cost = DARK_SELFCOOK_COST.get(drug, 200)
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} for ingredients."}), 400
    try: score = float(data.get("score", 0))
    except (TypeError, ValueError): score = 0.0
    score = max(0.0, min(1.0, score)); botched = bool(data.get("botched"))
    s["cash"] -= cost                          # pay for ingredients (clean cash)
    d["cooks_today"] = d.get("cooks_today", 0) + 1
    units = 0 if botched else max(1, round(DARK_SELFCOOK.get(drug, 10) * score))
    if units > 0:
        _dark_stash_add(d, drug, units)
        d["cred_xp"] = d.get("cred_xp", 0) + units            # cooking builds your rep
    # (a hand-cook in a vacant house leaves no standing operation for Marsh to watch — no heat)
    save(s)
    return jsonify({"ok": True, "yield": units, "botched": botched, "drug": drug, "cost": cost,
                    "cash": s["cash"], "cook_day": d["cook_day"], "cooks_today": d["cooks_today"],
                    "left": max(0, DARK_SELFCOOK_PER_DAY - d["cooks_today"]), "stash": d.get("stash", {})})

@app.route('/api/dark/fixer_wash', methods=['POST'])
def api_dark_fixer_wash():
    # The Fixer's quick-wash: instant dirty→clean, no front needed, but he takes a cut and
    # caps how much he'll handle per day. (His "help" early is the hook for the debt later.)
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; today = s.get("day")
    if d.get("debt_active"): return jsonify({"error": "The Fixer's done washing for you — you've got your own front now (and a marker to pay)."}), 400
    if d.get("fixer_washed_day") != today: d["fixer_washed_day"] = today; d["fixer_washed"] = 0
    remaining = max(0, DARK_FIXER_WASH_CAP - d.get("fixer_washed", 0))
    amount = min(d.get("dirty_money", 0), remaining)
    if amount <= 0:
        if d.get("dirty_money", 0) <= 0: return jsonify({"error": "No dirty money to wash."}), 400
        return jsonify({"error": "The Fixer's washed all he will for you today — come back tomorrow."}), 400
    clean = int(round(amount * (1 - DARK_FIXER_CUT)))
    d["dirty_money"] -= amount; s["cash"] += clean; d["fixer_washed"] = d.get("fixer_washed", 0) + amount
    save(s)
    return jsonify({"ok": True, "washed": amount, "clean": clean, "cut": amount - clean,
                    "cap_left": max(0, DARK_FIXER_WASH_CAP - d["fixer_washed"]),
                    "cash": s["cash"], "dirty_money": d["dirty_money"]})

@app.route('/api/dark/pay_fixer', methods=['POST'])
def api_dark_pay_fixer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; owed = d.get("debt_bill", 0) - d.get("debt_paid", 0)
    if not d.get("debt_active") or d.get("debt_bill_year") is None or owed <= 0:
        return jsonify({"error": "Nothing's due to the Fixer right now."}), 400
    pay = min(s["cash"], owed)
    if pay <= 0: return jsonify({"error": "You're tapped out — no clean cash to pay him."}), 400
    s["cash"] -= pay
    d["debt_paid"] = d.get("debt_paid", 0) + pay
    d["debt_balance"] = max(0, d.get("debt_balance", 0) - pay)
    save(s)
    return jsonify({"ok": True, "paid": pay, "settled": d["debt_paid"] >= d.get("debt_bill", 0),
                    "cash": s["cash"], "debt_paid": d["debt_paid"], "debt_bill": d.get("debt_bill", 0),
                    "debt_balance": d["debt_balance"]})

@app.route('/api/dark/ack_fixer', methods=['POST'])
def api_dark_ack_fixer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    s["dark"]["fixer_event"] = None   # dismiss the story-beat modal
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/hire_dealer', methods=['POST'])
def api_dark_hire_dealer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; cost = 5_000 + 3_000 * len(d.get("dealers", []))
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to bring a dealer on."}), 400
    s["cash"] -= cost
    did = d.get("next_dealer_id", 1); d["next_dealer_id"] = did + 1
    d.setdefault("dealers", []).append({"id": did, "name": _dark_make_name(_dark_used_names(d)),
                                        "inventory": {}, "held": 0, "heat": 0})
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/fire_dealer', methods=['POST'])
def api_dark_fire_dealer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; dl = next((x for x in d.get("dealers", []) if x["id"] == (request.json or {}).get("dealer_id")), None)
    if not dl: return jsonify({"error": "No such dealer."}), 400
    d["dirty_money"] = d.get("dirty_money", 0) + dl.get("held", 0)   # cash off them before they walk
    d["dealers"] = [x for x in d.get("dealers", []) if x["id"] != dl["id"]]
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/stock_dealer', methods=['POST'])
def api_dark_stock_dealer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    dl = next((x for x in d.get("dealers", []) if x["id"] == data.get("dealer_id")), None)
    drug = data.get("drug"); avail = d.get("stash", {}).get(drug, 0)
    if not dl: return jsonify({"error": "No such dealer."}), 400
    if avail <= 0: return jsonify({"error": "No product of that kind in your stash."}), 400
    amt = data.get("amount")
    units = avail if amt in (None, "all", 0) else min(avail, max(1, int(amt)))
    inv = dl.setdefault("inventory", {})
    inv[drug] = inv.get(drug, 0) + units
    d["stash"][drug] = avail - units
    if d["stash"][drug] <= 0: d["stash"].pop(drug, None)
    save(s)
    return jsonify({"ok": True, "stocked": units})

@app.route('/api/dark/pause_dealer', methods=['POST'])
def api_dark_pause_dealer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    dl = next((x for x in s["dark"].get("dealers", []) if x["id"] == (request.json or {}).get("dealer_id")), None)
    if not dl: return jsonify({"error": "No such dealer."}), 400
    dl["paused"] = not dl.get("paused")
    save(s)
    return jsonify({"ok": True, "paused": dl["paused"]})

@app.route('/api/dark/sling', methods=['POST'])
def api_dark_sling():
    # Player works a corner themselves (the "Sling Yourself" minigame): hand-to-hand
    # sale straight from the stash → dirty money + street-cred XP. No heat (it's the safe play).
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    drug = data.get("drug"); dm = DARK_DRUGS.get(drug)
    try: qty = int(data.get("qty", 0)); price = int(data.get("price", 0))
    except (TypeError, ValueError): return jsonify({"error": "Bad deal."}), 400
    if not dm or qty <= 0: return jsonify({"error": "Bad deal."}), 400
    have = d.get("stash", {}).get(drug, 0)
    if have < qty: return jsonify({"error": "You're out of that."}), 400
    today = s.get("day")
    if d.get("sling_day") != today: d["sling_day"] = today; d["slings_today"] = 0   # new day → reset the counter
    if d.get("slings_today", 0) >= DARK_SLING_PER_DAY:
        return jsonify({"error": f"You've worked all {DARK_SLING_PER_DAY} of today's corners yourself — let your dealers handle the rest, or come back tomorrow."}), 400
    price = max(0, min(price, int(dm["unit_value"] * qty * 2)))   # sanity cap (anti-cheat)
    d["slings_today"] = d.get("slings_today", 0) + 1
    d["stash"][drug] = have - qty
    if d["stash"][drug] <= 0: d["stash"].pop(drug, None)
    d["dirty_money"] = d.get("dirty_money", 0) + price
    d["cred_xp"] = d.get("cred_xp", 0) + round(price / 80)   # active selling pays a bit more rep/$
    d["year_take"] = d.get("year_take", 0) + price           # gross take → the Fixer's cut
    msgs = []
    _dark_award_cred(s, msgs)
    save(s)
    return jsonify({"ok": True, "dirty_money": d["dirty_money"], "cred": d.get("cred", 1),
                    "cred_xp": d.get("cred_xp", 0), "stash": d.get("stash", {}),
                    "slings_today": d["slings_today"], "sling_left": max(0, DARK_SLING_PER_DAY - d["slings_today"]),
                    "rank_msgs": [m["text"] for m in msgs]})

DARK_BRIBE_BASE = 4_000   # paying off the detective; climbs each time he's paid
DARK_LAWYER_COST = 8_000
DARK_MOVE_COST   = 3_000

@app.route('/api/dark/hunt_action', methods=['POST'])
def api_dark_hunt_action():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; act = (request.json or {}).get("action"); raid = bool(d.get("watch"))
    if act == "lie_low":
        if d.get("lying_low"): return jsonify({"error": "You're already set to lie low."}), 400
        d["lying_low"] = True
        save(s); return jsonify({"ok": True, "msg": "You'll keep everything quiet — advance to stall the case a day."})
    if act == "bribe":
        if not raid: return jsonify({"error": f"{DARK_DETECTIVE} hasn't got an open case to bury right now."}), 400
        cost = DARK_BRIBE_BASE + 1500 * d.get("bribes", 0)
        if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to pay {DARK_DETECTIVE} off."}), 400
        s["cash"] -= cost; d["bribes"] = d.get("bribes", 0) + 1
        d["heat"] = max(0, d.get("heat", 0) - 35)   # knocks the raid countdown back a few days
        save(s); return jsonify({"ok": True, "msg": f"Paid off {DARK_DETECTIVE} — bought yourself some days."})
    if act == "lawyer":
        if not raid: return jsonify({"error": "Nothing to lawyer up for right now."}), 400
        if d.get("lawyered"): return jsonify({"error": "Your lawyer's already on retainer."}), 400
        if s["cash"] < DARK_LAWYER_COST: return jsonify({"error": f"Need ${DARK_LAWYER_COST:,} for a lawyer."}), 400
        s["cash"] -= DARK_LAWYER_COST; d["lawyered"] = True
        save(s); return jsonify({"ok": True, "msg": "Lawyer's on retainer — if they raid, he'll beat the charge."})
    if act == "move":
        if not raid: return jsonify({"error": "No case open — nothing to move yet."}), 400
        if d.get("moved"): return jsonify({"error": "Product's already stashed safe."}), 400
        if s["cash"] < DARK_MOVE_COST: return jsonify({"error": f"Need ${DARK_MOVE_COST:,} for a mover."}), 400
        s["cash"] -= DARK_MOVE_COST; d["moved"] = True
        save(s); return jsonify({"ok": True, "msg": "Stash and dirty money moved somewhere safe."})
    return jsonify({"error": "Unknown move."}), 400

@app.route('/api/dark/buy_intel', methods=['POST'])
def api_dark_buy_intel():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]
    if not d.get("watch"): return jsonify({"error": "Marsh isn't building a case on anything right now."}), 400
    if _dark_clues_done(d): return jsonify({"error": "Your mole's got nothing new — you already know exactly what he's after."}), 400
    if s["cash"] < DARK_INTEL_COST: return jsonify({"error": f"Need ${DARK_INTEL_COST:,} for the mole's tip."}), 400
    s["cash"] -= DARK_INTEL_COST; new = _dark_clue_reveal(d, 1)
    save(s)
    return jsonify({"ok": True, "msg": "Mole's tip — " + (new[-1] if new else "nothing new, sorry.")})

@app.route('/api/dark/collect_front', methods=['POST'])
def api_dark_collect_front():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; key = (request.json or {}).get("key")
    ln = (d.get("launder") or {}).get(key)
    if not ln: return jsonify({"error": "No such front."}), 400
    got = ln.get("bank", 0)
    if got <= 0: return jsonify({"error": "Nothing clean to collect here yet."}), 400
    s["cash"] += got; ln["bank"] = 0
    save(s)
    return jsonify({"ok": True, "collected": got})

@app.route('/api/dark/build_vip', methods=['POST'])
def api_dark_build_vip():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]
    if not (d.get("biz") or {}).get("strip_club"): return jsonify({"error": "You don't run a strip club."}), 400
    if d.get("vip"): return jsonify({"error": "The VIP lounge is already open."}), 400
    if s["cash"] < DARK_VIP_COST: return jsonify({"error": f"Need ${DARK_VIP_COST:,} to build the VIP lounge."}), 400
    s["cash"] -= DARK_VIP_COST; d["vip"] = True
    if not d.get("club"): _dark_club_init(d)
    save(s)
    return jsonify({"ok": True})

@app.route('/api/dark/club_hire', methods=['POST'])
def api_dark_club_hire():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    key = (request.json or {}).get("key")
    if key not in DARK_DANCERS: return jsonify({"error": "No such dancer."}), 400
    if key in c.get("roster_keys", []): return jsonify({"error": "She's already part of the story."}), 400
    cost = DARK_DANCERS[key]["cost"]
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to bring her on."}), 400
    s["cash"] -= cost
    c.setdefault("roster_keys", []).append(key)
    c["dancers"].append(_dark_make_dancer(c, key)); _dark_club_refresh(c)
    save(s)
    return jsonify({"ok": True, "msg": f"{DARK_DANCERS[key]['name']} starts tonight. 💃"})

@app.route('/api/dark/club_fire', methods=['POST'])
def api_dark_club_fire():
    # The cast is fixed — you don't fire your girls; their stories play out instead.
    return jsonify({"error": "These six are family — you don't fire them. Their stories play out on their own."}), 400

@app.route('/api/dark/dancer_story', methods=['POST'])
def api_dark_dancer_story():
    s, c, err = _club_or_err()
    if err: return err
    j = request.json or {}
    x = next((dd for dd in c.get("dancers", []) if dd["id"] == j.get("id")), None)
    if not x or not x.get("event"): return jsonify({"error": "Nothing to handle for her right now."}), 400
    msg = _dark_story_resolve(s, c, x, int(j.get("choice", 0)))
    save(s)
    return jsonify({"ok": True, "msg": msg})


@app.route('/api/dark/club_lounge', methods=['POST'])
def api_dark_club_lounge():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; c = d.get("club")
    if not c or not c.get("lounge_offer"): return jsonify({"error": "Nobody worth working in the lounge right now."}), 400
    offer = c["lounge_offer"]; choice = (request.json or {}).get("choice")
    msg = ""
    if choice == "listen":
        if d.get("watch") and not _dark_clues_done(d):
            new = _dark_clue_reveal(d, 1)
            msg = "Lounge chatter paid off — " + (new[-1] if new else "but nothing new tonight.")
        else:
            c["rep"] = min(100, c.get("rep", 0) + 6)
            msg = "No case talk tonight — but you worked the room. The club's name is the better for it."
    elif choice == "compromise":
        cost = DARK_CLUB_COMPROMISE.get(offer["kind"], 10_000)
        if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to set the trap (drinks, a room, a camera)."}), 400
        s["cash"] -= cost
        kind = "bent_cop" if offer["kind"] == "cop" else "da"
        c.setdefault("leverage", []).append({"kind": kind, "who": offer["who"]})
        msg = f"You've got {offer['who']} in your pocket now."
    else:
        msg = "You let them drink in peace. For now."
    c["lounge_offer"] = None
    save(s)
    return jsonify({"ok": True, "msg": msg})

@app.route('/api/dark/club_leverage', methods=['POST'])
def api_dark_club_leverage():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; c = d.get("club")
    if not c: return jsonify({"error": "You don't run a club."}), 400
    lev = next((L for L in c.get("leverage", []) if L.get("kind") == "da"), None)
    if not lev: return jsonify({"error": "You've got no DA or judge in your pocket to make a call."}), 400
    who = lev["who"]; Who = who[:1].upper() + who[1:]
    if d.get("watch"):
        d["watch"] = None; d["watch_known"] = False; d["heat"] = 0
        d["raid_pace"] = 0; d["raid_days"] = 0; d["lawyered"] = False; d["moved"] = False
        d["raid_cooldown"] = s["day"] + DARK_RAID_COOLDOWN
        msg = f"{Who} made the whole case disappear. {DARK_DETECTIVE} is fuming — and back to square one."
    else:
        msg = f"{Who} owes you one — but there's no case open to bury right now."
    c["leverage"] = [L for L in c["leverage"] if L is not lev]   # one-time use
    save(s)
    return jsonify({"ok": True, "msg": msg})

@app.route('/api/dark/work_vip', methods=['POST'])
def api_dark_work_vip():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]
    if not ((d.get("biz") or {}).get("strip_club") and d.get("vip")): return jsonify({"error": "Build the VIP lounge first."}), 400
    if s["cash"] < DARK_VIP_WORK_COST: return jsonify({"error": f"Need ${DARK_VIP_WORK_COST:,} to work the room."}), 400
    s["cash"] -= DARK_VIP_WORK_COST
    if d.get("watch") and not _dark_clues_done(d):
        new = _dark_clue_reveal(d, 1)
        save(s); return jsonify({"ok": True, "msg": "You worked the VIP room — " + (new[-1] if new else "but nothing new tonight.")})
    save(s); return jsonify({"ok": True, "msg": "You greased a badge in the lounge — but there's no open case to dig on."})

# ── Strip-club operations: upgrades, staff, the bar, incidents, and the VIP minigame ──
def _club_or_err():
    s = load()
    if s.get("mode") != "dark": return None, None, (jsonify({"error": "Not on the dark side."}), 400)
    c = s["dark"].get("club")
    if not c: return None, None, (jsonify({"error": "You don't run a club."}), 400)
    _dark_club_migrate(c)
    return s, c, None

def _club_frozen(c):
    return jsonify({"error": "There's a situation at the club — handle it first."}), 400

@app.route('/api/dark/club_upgrade', methods=['POST'])
def api_dark_club_upgrade():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    key = (request.json or {}).get("key"); meta = DARK_CLUB_UPGRADES.get(key)
    if not meta: return jsonify({"error": "No such upgrade."}), 400
    cur = c["upgrades"].get(key, 0)
    if cur >= len(meta["tiers"]): return jsonify({"error": "That's already maxed out."}), 400
    label, cost = meta["tiers"][cur]
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} for that."}), 400
    s["cash"] -= cost; c["upgrades"][key] = cur + 1
    if key == "vip": s["dark"]["vip"] = True       # keep the Hunt-tab quick-action in sync
    save(s); return jsonify({"ok": True, "msg": f"{meta['icon']} {label} — done."})

@app.route('/api/dark/dancer_assign', methods=['POST'])
def api_dark_dancer_assign():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    j = request.json or {}; did = j.get("id"); slot = j.get("slot")
    if slot not in ("stage", "floor", "vip", "off"): return jsonify({"error": "Bad slot."}), 400
    if slot == "vip" and c["upgrades"].get("vip", 0) <= 0: return jsonify({"error": "Build the VIP room first."}), 400
    x = next((d for d in c.get("dancers", []) if d["id"] == did), None)
    if not x: return jsonify({"error": "No such dancer."}), 400
    x["assign"] = slot
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/club_door', methods=['POST'])
def api_dark_club_door():
    s, c, err = _club_or_err()
    if err: return err
    pol = (request.json or {}).get("policy")
    if pol not in ("strict", "balanced", "loose"): return jsonify({"error": "Bad policy."}), 400
    c["door"] = pol
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bouncer_hire', methods=['POST'])
def api_dark_bouncer_hire():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    if len(c.get("bouncers", [])) >= DARK_CLUB_BOUNCER_CAP: return jsonify({"error": "Your security team's full."}), 400
    bid = (request.json or {}).get("id")
    b = next((x for x in c.get("bouncer_recruits", []) if x["id"] == bid), None)
    if not b: return jsonify({"error": "He's already taken another job."}), 400
    cost = b["muscle"] * 7_000 + b["eye"] * 4_000
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to bring him on."}), 400
    s["cash"] -= cost
    c["bouncer_recruits"] = [x for x in c["bouncer_recruits"] if x["id"] != bid]
    b["assign"] = "door"; c["bouncers"].append(b); _dark_club_refresh(c)
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bouncer_fire', methods=['POST'])
def api_dark_bouncer_fire():
    s, c, err = _club_or_err()
    if err: return err
    bid = (request.json or {}).get("id")
    c["bouncers"] = [x for x in c.get("bouncers", []) if x["id"] != bid]
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bouncer_assign', methods=['POST'])
def api_dark_bouncer_assign():
    s, c, err = _club_or_err()
    if err: return err
    j = request.json or {}; bid = j.get("id"); slot = j.get("slot")
    if slot not in ("door", "floor", "vip", "off"): return jsonify({"error": "Bad slot."}), 400
    b = next((x for x in c.get("bouncers", []) if x["id"] == bid), None)
    if not b: return jsonify({"error": "No such bouncer."}), 400
    b["assign"] = slot
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bouncer_train', methods=['POST'])
def api_dark_bouncer_train():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    j = request.json or {}; bid = j.get("id"); stat = j.get("stat")
    if stat not in ("muscle", "eye"): return jsonify({"error": "Train what?"}), 400
    b = next((x for x in c.get("bouncers", []) if x["id"] == bid), None)
    if not b: return jsonify({"error": "No such bouncer."}), 400
    if b.get(stat, 1) >= 5: return jsonify({"error": "He's maxed there."}), 400
    cost = b.get("level", 1) * 12_000
    if s["cash"] < cost: return jsonify({"error": f"Need ${cost:,} to train him up."}), 400
    s["cash"] -= cost; b[stat] = b.get(stat, 1) + 1; b["level"] = b.get("level", 1) + 1; b["wage"] = b.get("wage", 150) + 30
    save(s); return jsonify({"ok": True, "msg": f"{b['name']} put in the work — {stat} up."})

@app.route('/api/dark/bar_set', methods=['POST'])
def api_dark_bar_set():
    s, c, err = _club_or_err()
    if err: return err
    pr = (request.json or {}).get("price")
    if pr not in DARK_BAR_PRICE: return jsonify({"error": "Bad price."}), 400
    if c["upgrades"].get("bar", 0) <= 0: return jsonify({"error": "Build the bar first."}), 400
    c["bar"]["price"] = pr
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bar_hire', methods=['POST'])
def api_dark_bar_hire():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    if c["upgrades"].get("bar", 0) <= 0: return jsonify({"error": "Build the bar first."}), 400
    if c["bar"].get("bartender"): return jsonify({"error": "You've already got a bartender."}), 400
    if s["cash"] < 12_000: return jsonify({"error": "Need $12,000 to hire a bartender."}), 400
    s["cash"] -= 12_000
    c["bar"]["bartender"] = {"name": random.choice(DARK_BARTENDER_NAMES), "upsell": random.randint(2, 4)}
    save(s); return jsonify({"ok": True, "msg": "Hired a bartender — drink sales just got a lift."})

@app.route('/api/dark/bar_fire', methods=['POST'])
def api_dark_bar_fire():
    s, c, err = _club_or_err()
    if err: return err
    c["bar"]["bartender"] = None
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/bar_signature', methods=['POST'])
def api_dark_bar_signature():
    s, c, err = _club_or_err()
    if err: return err
    if c["upgrades"].get("bar", 0) <= 0: return jsonify({"error": "Build the bar first."}), 400
    name = (str((request.json or {}).get("name") or "")).strip()[:28]
    if not name: return jsonify({"error": "Give the drink a name."}), 400
    first = not c["bar"].get("signature")
    c["bar"]["signature"] = name
    if first: c["rep"] = min(100, c.get("rep", 0) + 5)
    save(s); return jsonify({"ok": True, "msg": f'"{name}" is on the menu.' + (" The room's buzzing." if first else "")})

@app.route('/api/dark/club_event', methods=['POST'])
def api_dark_club_event():
    s, c, err = _club_or_err()
    if err: return err
    if not c.get("event"): return jsonify({"error": "Nothing to handle right now."}), 400
    choice = (request.json or {}).get("choice", 0)
    msg = _dark_club_resolve_event(s, c, int(choice))
    save(s); return jsonify({"ok": True, "msg": msg})

@app.route('/api/dark/vip_start', methods=['POST'])
def api_dark_vip_start():
    s, c, err = _club_or_err()
    if err: return err
    if c.get("event"): return _club_frozen(c)
    if c["upgrades"].get("vip", 0) <= 0: return jsonify({"error": "Build the VIP room first."}), 400
    if not c.get("vip_patron"): return jsonify({"error": "Nobody worth working in the VIP room right now."}), 400
    if c.get("vip_game"): return jsonify({"error": "You're already in there with someone."}), 400
    _dark_vip_start(c)
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/vip_action', methods=['POST'])
def api_dark_vip_action():
    s, c, err = _club_or_err()
    if err: return err
    g = c.get("vip_game")
    if not g: return jsonify({"error": "There's nobody in the VIP room."}), 400
    j = request.json or {}; action = j.get("action")
    d = s["dark"]; t = g["type"]; meta = DARK_VIP_TYPES[t]
    if action == "close":
        c["vip_game"] = None; save(s); return jsonify({"ok": True})
    if g.get("done"): return jsonify({"ok": True, "game": g})
    if action == "leave":
        c["vip_game"] = None
        save(s); return jsonify({"ok": True, "left": True, "msg": "You read the room and stepped back out. Sometimes that's the smart play."})
    if action == "dancer":
        x = next((dd for dd in c.get("dancers", []) if dd["id"] == j.get("id")), None)
        if not x: return jsonify({"error": "Send which girl?"}), 400
        ch = x.get("charm", 2)
        g["comfort"] = min(100, g["comfort"] + ch * 9)
        g["susp"] = max(0, g["susp"] - ch * 2)
        if t == "undercover": g["susp"] += 4          # he keeps probing no matter how charming she is
        g["round"] += 1
    elif action == "bottle":
        if s["cash"] < 1_500: return jsonify({"error": "Need $1,500 for a bottle."}), 400
        s["cash"] -= 1_500
        g["comfort"] = min(100, g["comfort"] + 22); g["susp"] = max(0, g["susp"] - 4); g["round"] += 1
    elif action == "steer":
        topic = j.get("topic")
        if topic not in DARK_VIP_TOPICS: return jsonify({"error": "Steer toward what?"}), 400
        if DARK_VIP_TOPICS[topic] == t:
            g["intel"] = min(100, g["intel"] + round(35 * g["comfort"] / 100.0) + 10); g["susp"] += meta["susp"]
        else:
            g["susp"] += 18; g["intel"] = min(100, g["intel"] + 2)
        g["round"] += 1
    else:
        return jsonify({"error": "Bad action."}), 400
    if g["comfort"] >= 40: g["revealed"] = True       # enough rapport to clock his tell
    # ── Resolve outcome. ──
    outcome = None
    if g["susp"] >= 100:
        g["done"] = True; g["win"] = False
        if t == "undercover":
            _dark_trigger_hunt(s, bump=40)   # he made a call — Marsh swings onto your hottest op
            outcome = "🚨 He was undercover — and you tipped your hand. He made a call on the way out. Marsh is moving on one of your spots."
        else:
            outcome = "He clammed up and left rattled. Whatever he knew, it's locked up tight now."
    elif g["intel"] >= 100:
        g["done"] = True; g["win"] = True
        rw = meta["reward"]
        if rw == "trap":
            _dark_trigger_hunt(s, bump=30)   # that was no regular — you walked into it
            outcome = "🎣 You pushed him for everything — and walked right into it. That was no regular. Marsh just moved on one of your spots."
        elif rw == "watch":
            if d.get("watch") and not _dark_clues_done(d):
                new = _dark_clue_reveal(d, 1)
                outcome = "🔎 You got it out of him — " + (new[-1] if new else "but nothing new tonight.")
            else:
                outcome = "🔎 He let slip the detective's got nothing solid right now. Nothing to act on."
        elif rw == "leverage_da":
            c.setdefault("leverage", []).append({"kind": "da", "who": meta["name"]})
            outcome = f"⚖️ {meta['name'].capitalize()} said too much over too many drinks. You've got leverage on him now."
        elif rw == "sell":
            pay = random.randint(2_000, 5_000)
            s["cash"] = max(0, s.get("cash", 0) - pay)
            if random.random() < 0.25:
                outcome = f"🐀 He took your ${pay:,} and fed you a line — that intel was garbage. Wasted money."
            elif d.get("watch") and not _dark_clues_done(d):
                new = _dark_clue_reveal(d, 1)
                outcome = f"🐀 ${pay:,} loosened his tongue — " + (new[-1] if new else "but he had nothing new.")
            else:
                outcome = f"🐀 ${pay:,} loosened his tongue, but there's no open case for him to talk about right now."
        else:  # beat cop
            if d.get("watch") and not _dark_clues_done(d):
                new = _dark_clue_reveal(d, 1)
                outcome = "🍺 A friendly badge, a few beers — " + (new[-1] if new else "nothing new tonight, though.")
            else:
                outcome = "🍺 Just street gossip, but a friendly badge is always worth having."
    elif g["round"] >= 6:
        g["done"] = True; g["win"] = False
        outcome = "Last call — he's done talking for the night. You didn't get what you came for."
    if g.get("done"): g["outcome"] = outcome
    save(s); return jsonify({"ok": True, "game": g})

def _dark_heist_curchoice(h, defn, ci):
    if h.get("phase") == "getaway": beat = defn["getaway"]
    elif h.get("phase") == "greed": beat = defn.get("greed", [])[h["idx"]]
    else: beat = defn["beats"][h["idx"]]
    return beat["choices"][ci]

def _dark_heist_resolve_beat(s, d, h, defn, ci, kind):
    """kind: 'win' (rolled it / clutched it), 'loss' (took the loss), 'fumble' (blew the clutch)."""
    opt = _dark_heist_curchoice(h, defn, ci)
    if kind == "win":
        h["heat"] = h.get("heat", 0) + 2
        h["pot"] = h.get("pot", 0) + opt.get("good", 0)
        h["last"] = {"ok": True, "gain": opt.get("good", 0), "text": opt.get("win", "")}
        _heist_advance(h, defn, True)
        if h.get("phase") == "payout": _dark_heist_finish(s, d, busted=False)
        else: _dark_heist_set_beat(h, d)
        return
    h["heat"] = h.get("heat", 0) + 5
    if opt.get("crit"):                       # a failed critical beat = caught, no matter how it failed
        h["last"] = {"ok": False, "text": opt.get("fail", "")}
        _dark_heist_finish(s, d, busted=True)
        return
    mult = DARK_HEIST_FUMBLE_MULT if kind == "fumble" else 1.0
    loss = min(h.get("pot", 0), round(opt.get("bad", 0) * mult))
    h["pot"] = h.get("pot", 0) - loss
    txt = opt.get("fail", "")
    if kind == "fumble": txt += " You blew the clutch — it cost you extra."
    h["last"] = {"ok": False, "loss": loss, "text": txt}
    _heist_advance(h, defn, False)
    _dark_heist_set_beat(h, d)

def _heist_advance(h, defn, success):
    """Move to the next beat / phase after a beat resolves."""
    phase = h["phase"]
    if phase == "getaway":
        h["phase"] = "payout"   # getaway done → payout (success keeps the pot)
        return
    h["idx"] = h.get("idx", 0) + 1
    if phase == "core":
        if h["idx"] >= len(defn["beats"]):
            h["secured"] = True
            if defn.get("greed"): h["phase"] = "greed"; h["idx"] = 0
            else: h["phase"] = "getaway"; h["idx"] = 0
    elif phase == "greed":
        if h["idx"] >= len(defn.get("greed", [])):
            h["phase"] = "getaway"; h["idx"] = 0

@app.route('/api/dark/heist_start', methods=['POST'])
def api_dark_heist_start():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; key = (request.json or {}).get("key"); defn = DARK_HEISTS.get(key)
    if not defn: return jsonify({"error": "No such score."}), 400
    if d.get("heist"): return jsonify({"error": "You're already lining up a job."}), 400
    if key in d.get("heists_done", []): return jsonify({"error": "That score's already been pulled."}), 400
    if _dark_scores_locked(s):
        days = d.get("heist_lockout", 0) - s.get("day", 1)
        return jsonify({"error": f"That last bust burned you — every score's cold for ~{max(1, days)} more day(s). Lay low, or rank up to shake it."}), 400
    if not _dark_heist_playable(key): return jsonify({"error": "That one's still in the works."}), 400
    if d.get("cred", 1) < defn["cred"]: return jsonify({"error": f"Unlocks at Street Cred {defn['cred']}."}), 400
    _dark_heist_ensure_pool(d)
    d["heist"] = {"key": key, "stage": "plan", "crew": {},
                  "case_bonus": 0, "cased": [], "pot": 0, "heat": 0, "phase": "core", "idx": 0,
                  "secured": False, "last": None, "outcome": None, "final": None}
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_crew', methods=['POST'])
def api_dark_heist_crew():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "plan": return jsonify({"error": "No job to crew up."}), 400
    j = request.json or {}; role = j.get("role")
    if role not in DARK_HEISTS[h["key"]]["roles"]: return jsonify({"error": "That role isn't on this job."}), 400
    m = _heist_member(d, j.get("id"))
    if not m or m["role"] != role: return jsonify({"error": "No such specialist for that role."}), 400
    h["crew"][role] = m["id"]   # just select — the crew are permanent, no duplicating
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_case', methods=['POST'])
def api_dark_heist_case():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "plan": return jsonify({"error": "No job to case."}), 400
    aid = (request.json or {}).get("action")
    act = next((a for a in DARK_HEISTS[h["key"]].get("case", []) if a["id"] == aid), None)
    if not act: return jsonify({"error": "Nothing to do there."}), 400
    if aid in h.get("cased", []): return jsonify({"error": "You've already cased that angle."}), 400
    if s["cash"] < act["cost"]: return jsonify({"error": f"Need ${act['cost']:,} to case it."}), 400
    s["cash"] -= act["cost"]; h["case_bonus"] = h.get("case_bonus", 0) + act["bonus"]
    h.setdefault("cased", []).append(aid); h["heat"] = min(100, h.get("heat", 0) + 2)   # casing risk rides on the job, not your global heat
    save(s); return jsonify({"ok": True, "note": act["note"]})

@app.route('/api/dark/heist_go', methods=['POST'])
def api_dark_heist_go():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "plan": return jsonify({"error": "No job to pull."}), 400
    missing = [r for r in DARK_HEISTS[h["key"]]["roles"] if r not in h.get("crew", {})]
    if missing: return jsonify({"error": f"Still need a {DARK_HEIST_ROLES[missing[0]]['name']}."}), 400
    h["stage"] = "run"; h["phase"] = "core"; h["idx"] = 0; h["pot"] = 0; h["secured"] = False; h["last"] = None
    _dark_heist_set_beat(h, d)
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_choice', methods=['POST'])
def api_dark_heist_choice():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "run": return jsonify({"error": "No job running."}), 400
    if h.get("clutch"): return jsonify({"error": "Handle the clutch first."}), 400
    defn = DARK_HEISTS[h["key"]]; phase = h["phase"]; idx = h["idx"]
    if phase == "getaway": beat = defn["getaway"]
    elif phase == "greed": beat = defn.get("greed", [])[idx]
    else: beat = defn["beats"][idx]
    ci = int((request.json or {}).get("choice", 0))
    if ci < 0 or ci >= len(beat["choices"]): return jsonify({"error": "Pick a move."}), 400
    opt = beat["choices"][ci]
    if (random.random() * 100) < _dark_heist_chance(h, d, opt):
        _dark_heist_resolve_beat(s, d, h, defn, ci, "win")
    else:
        # The roll failed — let the player decide: take the loss, or go for a clutch.
        h["clutch"] = {"ci": ci, "crit": bool(opt.get("crit")), "bad": opt.get("bad", 0),
                       "label": opt.get("label", ""), "text": opt.get("clutch") or "It's going sideways — one shot to pull it back."}
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_clutch', methods=['POST'])
def api_dark_heist_clutch():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "run" or not h.get("clutch"): return jsonify({"error": "Nothing to clutch."}), 400
    defn = DARK_HEISTS[h["key"]]; ci = h["clutch"]["ci"]
    j = request.json or {}; go = bool(j.get("go"))
    h["clutch"] = None
    if not go:
        _dark_heist_resolve_beat(s, d, h, defn, ci, "loss")          # take the smaller loss
    elif j.get("result") == "hit":
        _dark_heist_resolve_beat(s, d, h, defn, ci, "win")           # nailed it
    else:
        _dark_heist_resolve_beat(s, d, h, defn, ci, "fumble")        # blew it — bigger loss
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_cashout', methods=['POST'])
def api_dark_heist_cashout():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; h = d.get("heist")
    if not h or h.get("stage") != "run" or not h.get("secured"): return jsonify({"error": "Nothing secured to cash out yet."}), 400
    if h["phase"] == "getaway": return jsonify({"error": "You're already on your way out."}), 400
    h["phase"] = "getaway"; h["idx"] = 0
    _dark_heist_set_beat(h, d)
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_close', methods=['POST'])
def api_dark_heist_close():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    s["dark"]["heist"] = None
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/heist_abort', methods=['POST'])
def api_dark_heist_abort():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    h = s["dark"].get("heist")
    if h and h.get("stage") == "plan": s["dark"]["heist"] = None
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/hire_phil', methods=['POST'])
def api_dark_hire_phil():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; biz = d.get("biz") or {}
    if d.get("phil"): return jsonify({"error": "Phil's already on the payroll."}), 400
    if sum(1 for k in DARK_LAUNDER if biz.get(k)) < 2:
        return jsonify({"error": "Phil hasn't come around yet."}), 400
    front = next((k for k in DARK_LAUNDER if biz.get(k)), None)   # park him on a front right away
    d["phil"] = {"front": front}
    save(s); return jsonify({"ok": True, "msg": "Phil's on the crew. Good to have him back. 🧰"})

@app.route('/api/dark/phil_assign', methods=['POST'])
def api_dark_phil_assign():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; biz = d.get("biz") or {}
    if not d.get("phil"): return jsonify({"error": "You haven't brought Phil on."}), 400
    front = (request.json or {}).get("front")
    if front in (None, "", "off"): d["phil"]["front"] = None
    elif front in DARK_LAUNDER and biz.get(front): d["phil"]["front"] = front
    else: return jsonify({"error": "You don't run that front."}), 400
    save(s); return jsonify({"ok": True})

@app.route('/api/dark/collect_dealer', methods=['POST'])
def api_dark_collect_dealer():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; dl = next((x for x in d.get("dealers", []) if x["id"] == (request.json or {}).get("dealer_id")), None)
    if not dl: return jsonify({"error": "No such dealer."}), 400
    got = dl.get("held", 0)
    if got <= 0: return jsonify({"error": "They've got nothing to hand over yet."}), 400
    d["dirty_money"] = d.get("dirty_money", 0) + got
    dl["held"] = 0
    save(s)
    return jsonify({"ok": True, "collected": got})

@app.route('/api/dark/advance', methods=['POST'])
def api_dark_advance():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; events = []
    seized_ids = []; rented = 0
    lying = d.get("lying_low")     # "lie low" day — everything goes quiet and cools (set by a Hunt scramble)
    for p in s["properties"]:
        lab = p.get("lab")
        if lab:
            if lab.get("event"):     # trouble at the lab — production frozen until you handle it
                continue
            if lying:                # laying low: no cooking today, lab cools fast
                lab["heat"] = max(0, lab.get("heat", 0) - 14); continue
            drug  = DARK_DRUGS.get(lab.get("drug")) or DARK_DRUGS["reggie"]
            batch = lab.get("batch")
            crew  = _dark_crew_by_id(d, lab.get("crew_id"))
            members = _dark_crew_members(d, crew) if crew else []
            # ── Unpaid crew: after a grace period their temper climbs, then they may walk. ──
            if lab.get("owed", 0) > 0 and crew and members:
                days_owed = s["day"] - (lab.get("owed_since") or s["day"])
                loyal = any(m.get("trait") == "loyal" for m in members)
                if days_owed > DARK_CREW_GRACE and not loyal:
                    lab["temper"] = min(100, lab.get("temper", 0) + DARK_CREW_TEMPER_RATE)
                    if random.random() < lab["temper"] / 200:     # walk chance scales with temper
                        d["roster"] = [m for m in d.get("roster", []) if m.get("crew_id") != crew["id"]]
                        d["crews"]  = [c for c in d.get("crews", []) if c["id"] != crew["id"]]
                        lab["crew_id"] = None; lab["owed"] = 0; lab["owed_since"] = None; lab["temper"] = 0
                        events.append({"type": "negative", "text": f"💢 Fed up with not getting paid, the crew walked off the {p.get('type','lab')} — and took the keys."})
                        continue
            if not batch or not crew or not members:
                lab["heat"] = max(0, lab.get("heat", 0) - 8)     # no batch / no crew: cools off
                continue
            speed = batch.get("speed", 2)
            gh = sum(1 for m in members if m.get("trait") == "ghost")
            sl = sum(1 for m in members if m.get("trait") == "sloppy")
            # heat accrues by cook speed (faster = hotter); ghosts cool it, sloppy stokes it
            hmult = max(0.4, 1 - 0.25 * gh + 0.2 * sl)
            # Local heat = how much this lab is drawing Marsh's eye (his watch target is weighted by it).
            lab["heat"] = min(100, lab.get("heat", 0) + drug["base_heat"] * DARK_BATCH_HEAT.get(speed, 1.3) * hmult)
            batch["days_left"] = batch.get("days_left", 1) - 1
            if batch["days_left"] <= 0:                          # batch done — big drop of product
                lab["product"] = lab.get("product", 0) + batch.get("yield", 0)
                fee = round(DARK_CREW_FEE_PCT * batch.get("yield", 0) * drug.get("unit_value", 0))
                lab["owed"] = fee; lab["owed_since"] = s["day"]; lab["temper"] = 0
                d["cred_xp"] = d.get("cred_xp", 0) + batch.get("yield", 0)   # cooking builds rep too
                events.append({"type": "info", "text": f"✅ Batch ready at the {p.get('type','lab')} — {batch.get('yield',0)} units of {drug['name']}. The crew wants their cut: ${fee:,}."})
                lab["batch"] = None
        elif p.get("rented"):
            rented += 1
    if seized_ids:
        s["properties"] = [p for p in s["properties"] if p["id"] not in seized_ids]
    # ── Dealers work product into dirty money — and rack up their own heat ──
    for dl in d.get("dealers", []):
        inv = dl.setdefault("inventory", {})
        if dl.get("event"):          # dealer's got a problem — frozen until you handle it
            continue
        if lying:                    # laying low: corners go quiet, dealer cools
            dl["heat"] = max(0, dl.get("heat", 0) - 14); continue
        if dl.get("paused") or sum(inv.values()) <= 0:
            dl["heat"] = max(0, dl.get("heat", 0) - 10)   # paused / idle: cools off
            continue
        to_sell = _dark_dealer_cap(d); sold_val = 0.0; sold_units = 0
        for dk in list(inv.keys()):
            if to_sell <= 0: break
            take = min(inv[dk], to_sell)
            if take <= 0: continue
            uv = (DARK_DRUGS.get(dk) or {}).get("unit_value", 40)
            sold_val += take * uv
            inv[dk] -= take; sold_units += take; to_sell -= take
            if inv[dk] <= 0: del inv[dk]
        dl["held"] = dl.get("held", 0) + round(sold_val)
        dl["heat"] = min(100, dl.get("heat", 0) + sold_units * 1.8)   # heat = how much this corner draws Marsh
        d["cred_xp"] = d.get("cred_xp", 0) + round(sold_val / 150)   # street rep grows as you move weight
        d["year_take"] = d.get("year_take", 0) + round(sold_val)    # gross take → counts toward the Fixer's cut
    # ── Laundering — fronts wash dirty money into clean (needs a manager + a rate). ──
    laundered = 0; biz = d.get("biz") or {}; launder = d.setdefault("launder", {})
    for key, meta in DARK_LAUNDER.items():
        if not biz.get(key): continue
        ln = launder.setdefault(key, {"manager": False, "heat": 0, "rate": 0})
        philhere = bool(d.get("phil") and d["phil"].get("front") == key)
        if philhere:
            if s.get("cash", 0) >= DARK_PHIL_WAGE: s["cash"] -= DARK_PHIL_WAGE   # Phil's token wage
            if ln.get("bank", 0) > 0:                  # Phil collects the front's takings for you
                s["cash"] += ln["bank"]; ln["bank"] = 0
            if ln.get("event"):                       # Phil quietly handles whatever came up
                ln["event"] = None
                events.append({"type": "info", "text": random.choice(DARK_PHIL_LINES).format(front=meta["name"])})
        if ln.get("event"):          # front's got a situation — washing frozen until handled
            continue
        if lying:                    # laying low: front sits quiet, cools
            ln["heat"] = max(0, ln.get("heat", 0) - 10); continue
        if not ln.get("manager") or ln.get("rate", 0) <= 0:
            ln["heat"] = max(0, ln.get("heat", 0) - 8)   # idle: cools off
            continue
        if philhere and ln.get("heat", 0) >= 70:     # Phil eases off a day to keep it from boiling over
            ln["heat"] = max(0, ln.get("heat", 0) - 14); continue
        if s["cash"] < meta["wage"]:
            ln["manager"] = False
            events.append({"type": "warning", "text": f"💸 Couldn't make payroll — the {meta['name']} manager walked."})
            continue
        s["cash"] -= meta["wage"]   # daily upkeep
        amount = min(d.get("dirty_money", 0), meta["cap"] * ln["rate"])
        if amount > 0:
            d["dirty_money"] -= amount; ln["bank"] = ln.get("bank", 0) + amount; laundered += amount
            hr = meta["heat_rate"] * (0.4 if philhere else 1.0)   # Phil keeps the heat way down
            ln["heat"] = min(100, ln.get("heat", 0) + (amount / meta["cap"]) * hr)   # heat = Marsh's interest in this front
            d["cred_xp"] = d.get("cred_xp", 0) + round(amount / 800)   # clean money builds your standing
    if laundered:
        # Phil-run fronts sweep straight to cash; the rest pile up clean money you go collect.
        unswept = sum((d.get("launder") or {}).get(k, {}).get("bank", 0) for k in DARK_LAUNDER)
        tail = f" — ${unswept:,} waiting at your fronts to collect." if unswept else "."
        events.append({"type": "info", "text": f"🧼 Washed ${laundered:,} clean{tail}"})
    bleed = _dark_heat_bleed(d)   # bent-cop perk (Distributor+) quietly drags the raid countdown
    if bleed: d["heat"] = max(0, d.get("heat", 0) - bleed)
    _dark_club_tick(s, events)    # strip-club income, reputation, heat, VIP lounge
    # ── THE HUNT — local heat draws Marsh onto ONE op; the top-right Heat is the raid
    # countdown that follows. Only live once you've made a name (Street Cred 2+). ──
    _dark_hunt_tick(s, events)    # reads lying_low to stall the countdown, so clear it AFTER
    if lying: d["lying_low"] = False
    s["day"] += 1
    # Put-the-word-out refresh lands the next day with a fresh ~10 recruits.
    if d.get("recruits_refresh_day") and s["day"] >= d["recruits_refresh_day"]:
        d["recruits"] = _dark_gen_recruits(d, 10); d["recruits_refresh_day"] = None
        events.append({"type": "info", "text": "📞 Word got around — fresh faces are looking for work (check the Crew tab)."})
    # Rented homes pay clean rent weekly (cover income — no late pay, no trouble).
    rent_got = 0
    for p in s["properties"]:
        t = p.get("tenant")
        if p.get("rented") and t and t.get("rent") and t.get("next_pay", 0) <= s["day"]:
            s["cash"] += t["rent"]; rent_got += t["rent"]; t["next_pay"] = s["day"] + 7
    if rent_got:
        d["year_take"] = d.get("year_take", 0) + rent_got   # rent counts toward the Fixer's cut too
        events.append({"type": "info", "text": f"🏠 Rent day — collected ${rent_got:,} from your tenants."})
    _dark_gen_home_market(s)   # fresh listings on the home market each day
    # ── Roll a situation onto ONE active operation — it pauses until handled. ──
    ent_pool = []
    for p in s["properties"]:
        lab = p.get("lab")
        if lab and lab.get("crew_id") and not lab.get("event"):
            ent_pool.append(("lab", lab, CREW_EVENTS))
    for dl in d.get("dealers", []):
        if not dl.get("event"):
            ent_pool.append(("dealer", dl, DEALER_EVENTS))
    phil_front = (d.get("phil") or {}).get("front")
    for key in DARK_LAUNDER:
        if biz.get(key) and key != phil_front:   # Phil's front is off the table — he handles it
            ln = launder.setdefault(key, {"manager": False, "heat": 0, "rate": 0})
            if not ln.get("event") and LAUNDER_EVENTS.get(key):
                ent_pool.append(("front", ln, LAUNDER_EVENTS[key]))
    if ent_pool and random.random() < 0.45:
        _, ent, pool = random.choice(ent_pool)
        e = random.choice(pool)
        ent["event"] = {"icon": e["i"], "text": e["t"], "choices": e["c"]}
        events.append({"type": "warning", "text": f"{e['i']} Something's come up — one of your operations is paused until you handle it."})
    # A general street situation that needs your call (global choice modal).
    if not d.get("pending_event") and random.random() < 0.3:
        pool = _dark_eligible_events(s)
        if pool:
            ev = random.choice(pool)
            d["pending_event"] = {"key": ev["key"], "icon": ev["icon"], "text": ev["text"], "choices": ev["choices"]}
    _dark_award_cred(s, events)   # rank up if the day's hustle pushed cred_xp over a threshold
    # Phil comes looking for you once you're running enough fronts to need a man on them (2+).
    if not d.get("phil") and not d.get("phil_notified") and sum(1 for k in DARK_LAUNDER if biz.get(k)) >= 2:
        d["phil_notified"] = True
        events.append({"type": "info", "text": "📞 There's a big fella waiting outside one of your fronts — says he used to work for you. (Cash tab)"})
    _dark_debt_tick(s, events)    # the Fixer's yearly cut: lock on Winter 1, settle on the year-roll
    # The Hunt switches on the first time you hit Street Cred 2 — one-time heads-up.
    hunt_intro = False
    if d.get("cred", 1) >= 2 and not d.get("hunt_introduced"):
        d["hunt_introduced"] = True
        hunt_intro = True
    save(s)
    return jsonify({"ok": True, "events": events, "hunt_intro": hunt_intro})

@app.route('/api/dark/resolve_entity_event', methods=['POST'])
def api_dark_resolve_entity_event():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; data = request.json or {}
    kind = data.get("kind"); ref = data.get("ref"); idx = data.get("choice", 0)
    ent = None
    if kind == "lab":
        p = next((x for x in s["properties"] if x.get("id") == ref), None)
        ent = p.get("lab") if p else None
    elif kind == "dealer":
        ent = next((x for x in d.get("dealers", []) if x["id"] == ref), None)
    elif kind == "front":
        ent = (d.get("launder") or {}).get(ref)
    if not ent or not ent.get("event"): return jsonify({"error": "Nothing to handle."}), 400
    choices = ent["event"].get("choices", []); icon = ent["event"].get("icon", "❗")
    if not isinstance(idx, int) or idx < 0 or idx >= len(choices): return jsonify({"error": "Pick an option."}), 400
    label, result, eff = choices[idx][0], choices[idx][1], (choices[idx][2] or {})
    s["cash"] = max(0, s["cash"] + eff.get("cash", 0))
    d["dirty_money"] = max(0, d.get("dirty_money", 0) + eff.get("dirty", 0))
    # The event is ON this op — its heat lands on THIS op's local heat (raising its watch odds),
    # never the global raid countdown. "heat" and "eheat" both mean the same thing now.
    hadd = eff.get("heat", 0) + eff.get("eheat", 0)
    if hadd: ent["heat"] = max(0, min(100, ent.get("heat", 0) + hadd))
    sp = eff.get("s"); removed = False; note = ""
    if sp == "lose_crew" and kind == "lab":
        crew = _dark_crew_by_id(d, ent.get("crew_id")); members = _dark_crew_members(d, crew) if crew else []
        if members:
            gone = random.choice(members); d["roster"] = [m for m in d.get("roster", []) if m["id"] != gone["id"]]
            note = f"{gone.get('name', 'A crew member')} is gone."
    elif sp == "lose_product" and kind == "lab":
        before = ent.get("product", 0); ent["product"] = before // 2; note = f"Lost {before - ent['product']} units of product."
    elif sp == "bonus_product" and kind == "lab":
        ent["product"] = ent.get("product", 0) + 15; note = "Gained 15 units of product."
    elif sp == "lose_held" and kind == "dealer":
        ent["held"] = 0; note = "The dealer's cash is gone."
    elif sp == "free_supplies":
        pool = [k for k, dm in DARK_DRUGS.items() if dm["cred_req"] <= d.get("cred", 1)]
        if pool:
            k = random.choice(pool); d.setdefault("supplies", {})[k] = d.get("supplies", {}).get(k, 0) + 1
            note = f"Free {DARK_DRUGS[k]['name']} supplies added."
    elif sp == "bust" and kind == "dealer":
        d["dealers"] = [x for x in d.get("dealers", []) if x["id"] != ref]; removed = True; note = "The dealer got busted — he's gone."
    if not removed:
        ent["event"] = None
    save(s)
    return jsonify({"ok": True, "result": result, "icon": icon, "note": note,
                    "delta": {"cash": eff.get("cash", 0), "dirty": eff.get("dirty", 0), "heat": hadd}})

@app.route('/api/dark/resolve_event', methods=['POST'])
def api_dark_resolve_event():
    s = load()
    if s.get("mode") != "dark": return jsonify({"error": "Not on the dark side."}), 400
    d = s["dark"]; ev = d.get("pending_event")
    if not ev: return jsonify({"error": "Nothing to resolve."}), 400
    idx = (request.json or {}).get("choice", 0)
    choices = ev.get("choices", [])
    if not isinstance(idx, int) or idx < 0 or idx >= len(choices): return jsonify({"error": "Pick an option."}), 400
    ch = choices[idx]; eff = ch.get("effects", {}); icon = ev.get("icon", "❗")
    s["cash"] = max(0, s["cash"] + eff.get("cash", 0))
    d["dirty_money"] = max(0, d.get("dirty_money", 0) + eff.get("dirty_money", 0))
    _dark_apply_local_heat(s, eff.get("heat", 0))   # street event heat lands on a random op, not the global countdown
    sp = ch.get("special"); note = ""
    if sp == "lose_crew_member":
        roster = d.get("roster", [])
        if roster:
            gone = random.choice(roster)
            d["roster"] = [x for x in roster if x["id"] != gone["id"]]
            note = f"{gone.get('name', 'A crew member')} is gone."
    elif sp == "dealer_lose_held":
        holders = [x for x in d.get("dealers", []) if x.get("held", 0) > 0]
        if holders: random.choice(holders)["held"] = 0; note = "A dealer lost the cash he was holding."
    elif sp == "free_supplies":
        pool = [k for k, dm in DARK_DRUGS.items() if dm["cred_req"] <= d.get("cred", 1)]
        if pool:
            k = random.choice(pool); d.setdefault("supplies", {})[k] = d.get("supplies", {}).get(k, 0) + 1
            note = f"Picked up a free batch of {DARK_DRUGS[k]['name']} supplies."
    d["pending_event"] = None
    save(s)
    return jsonify({"ok": True, "result": ch.get("result", ""), "icon": icon, "note": note,
                    "delta": {"cash": eff.get("cash", 0), "dirty": eff.get("dirty_money", 0), "heat": eff.get("heat", 0)}})

@app.route('/api/market', methods=['GET', 'POST'])
def api_market():
    s = load()
    unlocked = get_unlocked_neighborhoods(s.get("level", 0))
    if not unlocked:
        return jsonify({"listings": [], "commercial_listings": [], "level_locked": True})
    generated_for  = set(s.get("market_unlocked_hoods", []))
    newly_unlocked = set(unlocked) - generated_for
    if newly_unlocked or not s.get("market"):
        s["market"], s["next_id"] = _gen_market(s["next_id"], hoods=unlocked)
        s["market_unlocked_hoods"] = list(unlocked)
        save(s)
    # Generate commercial market if level unlocked and not yet generated
    if s.get("level", 0) >= COMMERCE_ROW_UNLOCK_LEVEL and not s.get("commercial_market"):
        s["commercial_market"], s["next_id"] = _gen_commercial_market(s["next_id"])
        save(s)
    commercial = s.get("commercial_market", [])
    return jsonify({
        "listings":            [enrich(p, s["day"]) for p in s["market"]],
        "commercial_listings": commercial,
    })

@app.route('/api/market/refresh', methods=['POST'])
def api_market_refresh():
    s = load()
    unlocked = get_unlocked_neighborhoods(s.get("level", 0))
    if not unlocked:
        return jsonify({"listings": [], "commercial_listings": [], "level_locked": True})
    s["market"], s["next_id"] = _gen_market(s["next_id"], hoods=unlocked)
    if s.get("level", 0) >= COMMERCE_ROW_UNLOCK_LEVEL:
        s["commercial_market"], s["next_id"] = _gen_commercial_market(s["next_id"])
    save(s)
    return jsonify({
        "listings":            [enrich(p, s["day"]) for p in s["market"]],
        "commercial_listings": s.get("commercial_market", []),
    })

@app.route('/api/buy', methods=['POST'])
def api_buy():
    data = request.json
    s    = load()
    if s.get("level", 0) == 0:
        return jsonify({"error": "Reach Level 1 first — sell your starter property!"}), 400
    prop = next((p for p in s["market"] if p["id"] == data["listing_id"]), None)
    if not prop:
        return jsonify({"error": "Listing not found"}), 404
    buy_cost = prop["purchase_price"]
    if s.get("owned_items", {}).get("printer"):
        buy_cost = int(buy_cost * 0.95)
    if buy_cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= buy_cost
    prop["vacant_since"] = s["day"]
    prop["purchase_day"] = s["day"]
    # Roll special contractors immediately so they're available before the next day advance
    rolled = {}
    for key in SPECIAL_CONTRACTORS:
        if random.random() < SPECIAL_CONTRACTOR_CHANCE:
            prem_cost = _reno_cost(prop, UPGRADES[key]["base_cost"], CONTRACTORS["premium"]["cost_mult"])
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
                costs = {ck: _reno_cost(prop, upg["base_cost"], c["cost_mult"]) for ck, c in CONTRACTORS.items()}
                entry = {**upg, "key": key, "costs": costs, "prev_quality_tier": tier_key,
                         "energy_cost": diy_energy_cost(prop, upg["energy_cost"])}
                sc = prop.get("special_contractors", {}).get(key)
                if sc:
                    entry["special_contractor"] = sc
                available.append(entry)
        else:
            costs = {ck: _reno_cost(prop, upg["base_cost"], c["cost_mult"]) for ck, c in CONTRACTORS.items()}
            entry = {**upg, "key": key, "costs": costs,
                     "energy_cost": diy_energy_cost(prop, upg["energy_cost"])}
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
        cost    = _reno_cost(prop, upg["base_cost"], premium["cost_mult"])
        quality = 100   # guaranteed S+
        cont_name = sc["name"]
    else:
        if contractor_key not in CONTRACTORS:
            return jsonify({"error": "Unknown contractor"}), 400
        cont      = CONTRACTORS[contractor_key]
        cost      = _reno_cost(prop, upg["base_cost"], cont["cost_mult"])
        if s.get("owned_items", {}).get("whiteboard"):
            cost = int(cost * 0.94)
        if s.get("owned_items", {}).get("workbench_tools"):
            cost = int(cost * 0.92)
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
    purchase_day = prop.get("purchase_day")
    if purchase_day is not None and (s["day"] - purchase_day) < 3:
        days_left = 3 - (s["day"] - purchase_day)
        return jsonify({"error": f"Couldn't find a buyer — word hasn't gotten out yet. Try again in {days_left} day{'s' if days_left != 1 else ''}."}), 400
    # Fixed-value properties (e.g. starter home) sell at exact price until upgraded
    if prop.get("fixed_market_value") and not prop.get("upgrades") and not prop.get("premium_upgrades"):
        sale = prop["fixed_market_value"]
    else:
        sale = int(calc_market_value(prop) * random.uniform(0.90, 1.00))
    if s.get("owned_items", {}).get("negotiation_book"):
        sale = int(sale * 1.04)
    if s.get("owned_items", {}).get("bookshelf"):
        sale = int(sale * 1.05)
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
        def _in_tier(t):
            return hood_tier in t.get("tiers", ["budget", "mid", "premium"])
        # Prefer unique named tenants not already renting somewhere.
        uniq_pool = [t for t in TENANT_PROFILES
                     if _in_tier(t) and t.get("unique") and t["name"] not in active_names]
        picks = random.sample(uniq_pool, min(3, len(uniq_pool)))
        # Generic fallbacks ONLY fill the remaining slots when the unique pool for
        # this tier is exhausted — never when named tenants are still available.
        if len(picks) < 3:
            generic_pool = [t for t in TENANT_PROFILES if _in_tier(t) and not t.get("unique")]
            picks += random.sample(generic_pool, min(3 - len(picks), len(generic_pool)))
        applicants = []
        for i, t in enumerate(picks):
            tk = trait_for(t)
            applicants.append({**t, "idx": i, "trait": tk,
                "trait_info": {**TENANT_TRAITS[tk], "key": tk},
                "damage_label": "Low" if t["damage_chance"] < 0.05 else ("Medium" if t["damage_chance"] < 0.10 else "High")})
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
    # Trait: reliable tenants have a pay-chance floor regardless of rent tier
    _trait_eff  = TRAIT_EFFECTS.get(t.get("trait"), {})
    if "pay_floor" in _trait_eff:
        pay_chance = max(pay_chance, _trait_eff["pay_floor"])

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
        "loyalty":          10,   # 0-100; grows with renewals & tenure, drives negotiation
        "renewals":         0,
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


# ── Tenant storylets ────────────────────────────────────────────────────────
# Multi-stage tenant situations. One active storylet per tenant at a time.
# Choice stages pause for the player (queued like tenant requests); auto stages
# resolve during a time-advance by weighted roll. Choice transitions use delay>=1
# (land in a future advance); auto transitions may use delay 0 to chain instantly.
# Outcome keys: morale, loyalty, condition, cash(+income/-cost), pay_chance,
#   damage_chance_add, flag{}, goto+delay, resolve, leave, result(player text).
STORYLETS = {
    "hard_times": {
        "title": "Hard Times", "icon": "💼",
        "trigger": {"weight": 5, "cooldown_days": 84, "min_days_resident": 21},
        "stages": {
            "start": {
                "text": "{name} just lost their job and is short on rent this week. They're asking for a little flexibility.",
                "choices": [
                    {"label": "Offer a payment plan",
                     "outcome": {"morale": 8, "loyalty": 8, "goto": "recovery", "delay": 14,
                                 "result": "You set up a payment plan. They're grateful."}},
                    {"label": "Forgive this week's rent", "cost": {"cash_weeks": 1},
                     "outcome": {"morale": 16, "loyalty": 14, "resolve": True,
                                 "result": "You forgave the week. They won't forget it."}},
                    {"label": "Hold firm — rent's due",
                     "outcome": {"morale": -12, "goto": "ultimatum", "delay": 18,
                                 "result": "You held firm. The air is tense."}},
                ],
            },
            "recovery": {"auto": True, "roll": [
                {"weight": 60, "text": "{name} landed a new job and is back on track.",
                 "outcome": {"loyalty": 10, "resolve": True}},
                {"weight": 40, "text": "{name} is still out of work and falling behind.",
                 "outcome": {"goto": "ultimatum", "delay": 14}},
            ]},
            "ultimatum": {
                "text": "{name} is now weeks behind on rent. Time to make a call.",
                "choices": [
                    {"label": "Start eviction ($1,500)", "cost": {"cash": 1500},
                     "outcome": {"leave": True, "result": "You started eviction. They're gone."}},
                    {"label": "Cash-for-keys ($800, clean exit)", "cost": {"cash": 800},
                     "outcome": {"leave": True, "result": "They took the deal and left without a fuss."}},
                    {"label": "One more extension",
                     "outcome": {"morale": 5, "goto": "recovery", "delay": 14,
                                 "result": "You gave them one more shot."}},
                ],
            },
        },
    },
    "dog": {
        "title": "The Dog Question", "icon": "🐕",
        "trigger": {"weight": 6, "cooldown_days": 84, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "{name} wants to adopt a dog and is asking your permission.",
                "choices": [
                    {"label": "Allow it",
                     "outcome": {"morale": 10, "flag": {"has_pet": True}, "damage_chance_add": 0.08,
                                 "resolve": True, "result": "They're thrilled. Hope the floors hold up."}},
                    {"label": "Allow it — with a $400 pet deposit",
                     "outcome": {"morale": 4, "cash": 400, "flag": {"has_pet": True}, "damage_chance_add": 0.05,
                                 "resolve": True, "result": "Deposit collected. Everybody wins."}},
                    {"label": "Say no",
                     "outcome": {"morale": -8, "resolve": True,
                                 "result": "They're disappointed but accept it."}},
                ],
            },
        },
    },
    "small_leak": {
        "title": "The Small Leak", "icon": "💧",
        "trigger": {"weight": 6, "cooldown_days": 56, "min_days_resident": 7, "min_condition": 40},
        "stages": {
            "start": {
                "text": "{name} reports a small leak under the kitchen sink.",
                "choices": [
                    {"label": "Fix it now ($300)", "cost": {"cash": 300},
                     "outcome": {"morale": 6, "condition": 4, "resolve": True,
                                 "result": "Fixed fast. They appreciate a responsive landlord."}},
                    {"label": "Credit them $150 to handle it", "cost": {"cash": 150},
                     "outcome": {"morale": 4, "resolve": True,
                                 "result": "They sorted it out and pocketed the credit."}},
                    {"label": "It can wait",
                     "outcome": {"morale": -4, "goto": "escalate", "delay": 12,
                                 "result": "You'll deal with it later. Probably."}},
                ],
            },
            "escalate": {"auto": True, "roll": [
                {"weight": 55, "text": "That little leak became real water damage at {prop}.",
                 "outcome": {"condition": -30, "morale": -12, "resolve": True}},
                {"weight": 45, "text": "{name} got fed up waiting and fixed the leak themselves.",
                 "outcome": {"morale": -6, "loyalty": -5, "resolve": True}},
            ]},
        },
    },
    "sublet": {
        "title": "The Sublet", "icon": "🕵️",
        "trigger": {"weight": 8, "cooldown_days": 84, "min_days_resident": 21, "traits": ["subletter"]},
        "stages": {
            "start": {
                "text": "Word is {name} might be quietly subletting the place on a vacation-rental site.",
                "choices": [
                    {"label": "Investigate quietly",
                     "outcome": {"goto": "confirmed", "delay": 2, "result": "You start digging…"}},
                    {"label": "Confront them directly",
                     "outcome": {"morale": -10, "goto": "confront", "delay": 1, "result": "You call them out."}},
                    {"label": "Let it slide",
                     "outcome": {"damage_chance_add": 0.05, "resolve": True,
                                 "result": "You look the other way. The extra foot traffic adds wear."}},
                ],
            },
            "confirmed": {"auto": True, "roll": [
                {"weight": 65, "text": "Confirmed — {name} has been subletting your unit.",
                 "outcome": {"goto": "confront", "delay": 0}},
                {"weight": 35, "text": "False alarm — {name} was just hosting out-of-town family.",
                 "outcome": {"morale": 4, "resolve": True}},
            ]},
            "confront": {
                "text": "{name} is busted subletting. How do you handle it?",
                "choices": [
                    {"label": "Fine them ($1,000 penalty to you)... collect it", "cost": {},
                     "outcome": {"cash": 1000, "morale": -8, "loyalty": -10, "resolve": True,
                                 "result": "You levied a $1,000 fine. They paid, grumbling."}},
                    {"label": "Evict ($1,500)", "cost": {"cash": 1500},
                     "outcome": {"leave": True, "result": "You evicted them on the spot."}},
                    {"label": "Cut a deal — take a cut (+$600)", "cost": {},
                     "outcome": {"cash": 600, "morale": 6, "flag": {"sublet_deal": True}, "resolve": True,
                                 "result": "You take a cut of the action. Unorthodox, but profitable."}},
                ],
            },
        },
    },

    # ── Special-tenant signature storylets ─────────────────────────────────────
    "phil_gift": {
        "title": "A Note from Phil", "icon": "🔱",
        "trigger": {"special": "is_phil", "weight": 10, "cooldown_days": 56, "min_days_resident": 10},
        "stages": {
            "start": {
                "text": "You find a handwritten note from The Phil. He'd like to spend the weekend 'setting a few things right,' if you'll allow it. He asks for nothing in return.",
                "choices": [
                    {"label": "Give him free rein",
                     "outcome": {"condition": 30, "morale": 6, "resolve": True,
                                 "result": "By Monday the place gleams. You can't find a single flaw. You never will."}},
                    {"label": "Cover materials ($200)", "cost": {"cash": 200},
                     "outcome": {"condition": 42, "loyalty": 10, "resolve": True,
                                 "result": "He accepts with a small nod. The work is somewhere beyond professional."}},
                    {"label": "Politely decline",
                     "outcome": {"resolve": True,
                                 "result": "He folds the note away. 'Another time, then.' The faucet you'd been meaning to fix is fixed by morning anyway."}},
                ],
            },
        },
    },
    "baileys_dinner": {
        "title": "Sunday Dinner", "icon": "👨‍👩‍👧‍👦",
        "trigger": {"special": "is_baileys", "weight": 10, "cooldown_days": 56, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "The Baileys leave an invitation: they'd love to have you over for Sunday dinner, just to say thank you for being a good landlord.",
                "choices": [
                    {"label": "Happily accept",
                     "outcome": {"loyalty": 20, "morale": 8, "resolve": True,
                                 "result": "Best roast you've had in years. They ask to renew on the spot — you're basically family now."}},
                    {"label": "Send a gift instead ($150)", "cost": {"cash": 150},
                     "outcome": {"loyalty": 12, "morale": 6, "resolve": True,
                                 "result": "They're touched. The kids drew you a card. It's on your fridge now."}},
                    {"label": "Too busy — maybe next time",
                     "outcome": {"morale": -4, "resolve": True,
                                 "result": "They understand completely. They always do."}},
                ],
            },
        },
    },
    "goldbergs_soiree": {
        "title": "The Soirée", "icon": "🎩",
        "trigger": {"special": "is_goldbergs", "weight": 12, "cooldown_days": 30, "min_days_resident": 7},
        "stages": {
            "start": {
                "text": "The Goldbergs wish to host an extravagant soirée at the property this weekend. Enclosed is a generous 'inconvenience fee,' should you agree.",
                "choices": [
                    {"label": "By all means (+$3,000 fee)",
                     "outcome": {"cash": 3000, "damage_chance_add": 0.05, "resolve": True,
                                 "result": "Valets, a string quartet, an ice sculpture of — apparently — you. $3,000 richer, minor wear."}},
                    {"label": "A smaller gathering (+$1,200)",
                     "outcome": {"cash": 1200, "resolve": True,
                                 "result": "Tastefully restrained, by Goldberg standards. The check clears before they leave."}},
                    {"label": "Decline — too much liability",
                     "outcome": {"morale": -6, "resolve": True,
                                 "result": "They're mildly affronted, but pay their (enormous) rent regardless."}},
                ],
            },
        },
    },
    "mystery_visit": {
        "title": "Something Odd", "icon": "👤",
        "trigger": {"special": "is_mystery", "weight": 12, "cooldown_days": 42, "min_days_resident": 7},
        "stages": {
            "start": {
                "text": "Neighbors report strange lights and a faint humming from ???'s unit at 3am. ???, as always, has said nothing.",
                "choices": [
                    {"label": "Knock and ask",
                     "outcome": {"goto": "knock", "delay": 1, "result": "You decide to head over and ask…"}},
                    {"label": "Let it be",
                     "outcome": {"resolve": True,
                                 "result": "Whatever it is, the rent's always paid in full and early. You let it be."}},
                ],
            },
            "knock": {"auto": True, "roll": [
                {"weight": 50, "text": "???'s unit is immaculate, ordinary, silent. They press an envelope of cash into your hand and gently close the door.",
                 "outcome": {"cash": 1500, "resolve": True}},
                {"weight": 50, "text": "No one answers. By morning every fixture in the building works better than new, and a note reads only: 'Thank you.'",
                 "outcome": {"condition": 25, "resolve": True}},
            ]},
        },
    },

    # ── Special-tenant events (expansion) ──────────────────────────────────────
    # THE PHIL — mysterious, immaculate, just… fixes things.
    "phil_storm": {
        "title": "After the Storm", "icon": "🔱",
        "trigger": {"special": "is_phil", "weight": 8, "cooldown_days": 60, "min_days_resident": 14},
        "stages": {"start": {
            "text": "A nasty storm battered the block. By dawn, every home on the street is somehow already repaired — and The Phil is wiping his hands clean on the sidewalk, saying nothing.",
            "choices": [
                {"label": "Thank him and insist on paying ($200)", "cost": {"cash": 200},
                 "outcome": {"condition": 30, "loyalty": 10, "resolve": True, "result": "He waves the money off twice before accepting. The property has never looked sturdier."}},
                {"label": "Just thank him warmly",
                 "outcome": {"condition": 22, "morale": 6, "resolve": True, "result": "A single nod. 'It needed doing.' The roof will outlast you both."}},
                {"label": "Ask how he does it",
                 "outcome": {"goto": "phil_secret", "delay": 1, "result": "He pauses, considering whether to answer…"}}]},
            "phil_secret": {"auto": True, "roll": [
                {"weight": 100, "text": "He smiles faintly. 'Right tools. Right time.' That's all you'll ever get. The repairs are flawless.",
                 "outcome": {"condition": 28, "loyalty": 8, "resolve": True}}]}}},
    "phil_apprentice": {
        "title": "The Toolbox", "icon": "🧰",
        "trigger": {"special": "is_phil", "weight": 7, "cooldown_days": 70, "min_days_resident": 28},
        "stages": {"start": {
            "text": "The Phil leaves a beautifully kept antique toolbox outside your door with a note: 'For the next thing that breaks. You'll know what to do.'",
            "choices": [
                {"label": "Accept it gratefully",
                 "outcome": {"condition": 10, "loyalty": 12, "morale": 8, "resolve": True, "result": "Oddly, the next three repairs around the property go perfectly. Beginner's luck, surely."}},
                {"label": "Try to return it",
                 "outcome": {"morale": 4, "resolve": True, "result": "It's back on your doorstep the next morning. You keep it."}},
                {"label": "Offer to pay for such fine tools ($150)", "cost": {"cash": 150},
                 "outcome": {"condition": 12, "loyalty": 14, "resolve": True, "result": "He accepts, just this once. The tools feel weightless and perfectly balanced."}}]}}},
    "phil_neighbor": {
        "title": "A Favor for the Block", "icon": "🏘️",
        "trigger": {"special": "is_phil", "weight": 7, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "An elderly neighbor's porch is collapsing and they can't afford repairs. The Phil quietly asks your blessing to fix it on his own time.",
            "choices": [
                {"label": "Bless it — and chip in for materials ($175)", "cost": {"cash": 175},
                 "outcome": {"condition": 8, "loyalty": 16, "morale": 12, "resolve": True, "result": "The whole street notices. Your reputation as a landlord quietly soars."}},
                {"label": "Of course — go ahead",
                 "outcome": {"loyalty": 12, "morale": 10, "resolve": True, "result": "The porch is rebuilt by Sunday. The neighbor leaves you a pie."}},
                {"label": "Better not get involved",
                 "outcome": {"morale": -4, "resolve": True, "result": "He respects it. The porch gets fixed anyway, somehow, a week later."}}]}}},
    "phil_farewell": {
        "title": "Phil's Farewell", "icon": "🕯️",
        "trigger": {"special": "is_phil", "weight": 6, "cooldown_days": 90, "min_days_resident": 70},
        "stages": {"start": {
            "text": "The Phil mentions, almost in passing, that he'll be moving on soon. Before he goes, he'd like to leave the place 'truly finished.'",
            "choices": [
                {"label": "Let him do his final work",
                 "outcome": {"condition": 45, "loyalty": 10, "resolve": True, "result": "When he's done, the home is, by any measure, perfect. You almost don't want to rent it to anyone else."}},
                {"label": "Insist on a parting gift for him ($250)", "cost": {"cash": 250},
                 "outcome": {"condition": 40, "loyalty": 18, "morale": 10, "resolve": True, "result": "He's quietly moved. 'Nobody's ever done that.' The work is his masterpiece."}},
                {"label": "Thank him and let him rest",
                 "outcome": {"condition": 20, "morale": 8, "resolve": True, "result": "He smiles. 'Maybe just the gutters, then.' Even his 'rest' is excellent work."}}]}}},
    # THE BAILEYS — wholesome, devoted family. Never a complaint.
    "baileys_lemonade": {
        "title": "The Lemonade Stand", "icon": "🍋",
        "trigger": {"special": "is_baileys", "weight": 8, "cooldown_days": 60, "min_days_resident": 14},
        "stages": {"start": {
            "text": "The Bailey kids have set up a lemonade stand out front and shyly ask if it's allowed.",
            "choices": [
                {"label": "Grant them an official 'permit' (and buy a cup)",
                 "outcome": {"loyalty": 16, "morale": 12, "resolve": True, "result": "Best fifty-cent lemonade you've ever had. The kids beam. The parents melt."}},
                {"label": "Of course — have fun",
                 "outcome": {"loyalty": 10, "morale": 8, "resolve": True, "result": "A summer staple is born. The block adores them."}},
                {"label": "Keep it off the sidewalk, please",
                 "outcome": {"morale": -2, "resolve": True, "result": "They move it to the porch, only slightly deflated."}}]}}},
    "baileys_holiday": {
        "title": "Decking the Block", "icon": "🎁",
        "trigger": {"special": "is_baileys", "weight": 7, "cooldown_days": 80, "min_days_resident": 21, "season": 3},
        "stages": {"start": {
            "text": "The Baileys want to go all-out with holiday decorations — lights, inflatables, the whole display — and ask if you mind.",
            "choices": [
                {"label": "Mind? Help fund it! ($75)", "cost": {"cash": 75},
                 "outcome": {"loyalty": 16, "morale": 14, "resolve": True, "result": "The house wins the neighborhood lights contest. Photos of YOUR property are all over local social media."}},
                {"label": "Absolutely, go for it",
                 "outcome": {"loyalty": 10, "morale": 10, "resolve": True, "result": "A magical display. Cars slow down just to look."}},
                {"label": "Keep it tasteful, watch the wiring",
                 "outcome": {"morale": 4, "resolve": True, "result": "They keep it classy. Still lovely."}}]}}},
    "baileys_reference": {
        "title": "Friends of the Family", "icon": "👪",
        "trigger": {"special": "is_baileys", "weight": 7, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "The Baileys know another family — 'just like us' — looking for a good landlord, and would love to vouch for them.",
            "choices": [
                {"label": "Gratefully take the referral ($50 thank-you)", "cost": {"cash": 50},
                 "outcome": {"loyalty": 14, "morale": 10, "resolve": True, "result": "A pre-vetted dream tenant for one of your other units. Gold."}},
                {"label": "Happily take their word",
                 "outcome": {"loyalty": 10, "morale": 8, "resolve": True, "result": "If the Baileys vouch, that's all you need to know."}},
                {"label": "Not looking right now",
                 "outcome": {"resolve": True, "result": "They understand completely. They always do."}}]}}},
    "baileys_milestone": {
        "title": "A Family Milestone", "icon": "🎓",
        "trigger": {"special": "is_baileys", "weight": 7, "cooldown_days": 80, "min_days_resident": 28},
        "stages": {"start": {
            "text": "The eldest Bailey is graduating, and the family invites you to the small backyard celebration.",
            "choices": [
                {"label": "Attend with a gift ($100)", "cost": {"cash": 100},
                 "outcome": {"loyalty": 20, "morale": 14, "resolve": True, "result": "You're seated with the family. They introduce you as 'the best landlord in the world.' You believe them."}},
                {"label": "Stop by to congratulate them",
                 "outcome": {"loyalty": 12, "morale": 10, "resolve": True, "result": "A warm afternoon. The grad thanks you for keeping their home steady."}},
                {"label": "Send your best wishes",
                 "outcome": {"loyalty": 4, "morale": 4, "resolve": True, "result": "They appreciate the thought."}}]}}},
    # THE GOLDBERGS — old money, extravagant, brief stays.
    "goldbergs_art": {
        "title": "A Lasting Impression", "icon": "🖼️",
        "trigger": {"special": "is_goldbergs", "weight": 10, "cooldown_days": 35, "min_days_resident": 7},
        "stages": {"start": {
            "text": "The Goldbergs wish to install a rather expensive chandelier and built-in shelving — and, naturally, they'll leave it all behind when they go.",
            "choices": [
                {"label": "By all means (keep the fixtures)",
                 "outcome": {"condition": 25, "cash": 500, "resolve": True, "result": "The crystal chandelier alone adds real value. They even cover the electrician."}},
                {"label": "Delighted — split the install ($300)", "cost": {"cash": 300},
                 "outcome": {"condition": 35, "loyalty": 6, "resolve": True, "result": "A tasteful, permanent upgrade. The next tenant will swoon."}},
                {"label": "Nothing structural, please",
                 "outcome": {"morale": -4, "resolve": True, "result": "They sigh dramatically and hang their art on existing hooks. Philistine."}}]}}},
    "goldbergs_gala": {
        "title": "The Charity Gala", "icon": "🥂",
        "trigger": {"special": "is_goldbergs", "weight": 10, "cooldown_days": 35, "min_days_resident": 7},
        "stages": {"start": {
            "text": "The Goldbergs propose hosting a charity gala at the property. There will be valets. There will be swans. There will be a 'venue honorarium' for you.",
            "choices": [
                {"label": "Host it (+$2,500 honorarium)",
                 "outcome": {"cash": 2500, "damage_chance_add": 0.04, "resolve": True, "result": "A dazzling, slightly chaotic evening. The check is, of course, immaculate. Minor wear from the swans."}},
                {"label": "A refined, smaller affair (+$1,000)",
                 "outcome": {"cash": 1000, "resolve": True, "result": "Restrained elegance. No swans this time. Sadly."}},
                {"label": "Decline — far too much",
                 "outcome": {"morale": -6, "resolve": True, "result": "'How very… practical of you.' They pay their staggering rent regardless."}}]}}},
    "goldbergs_complaint": {
        "title": "A Trifling Matter", "icon": "🎩",
        "trigger": {"special": "is_goldbergs", "weight": 9, "cooldown_days": 35, "min_days_resident": 7},
        "stages": {"start": {
            "text": "The Goldbergs are displeased: the water pressure is 'merely adequate.' They have, however, enclosed an apology gift for troubling you with it.",
            "choices": [
                {"label": "Upgrade the fixtures at once ($250)", "cost": {"cash": 250},
                 "outcome": {"condition": 12, "cash": 400, "loyalty": 8, "resolve": True, "result": "Spa-grade pressure restored. Their 'thank-you' more than covers it."}},
                {"label": "Accept the gift, look into it",
                 "outcome": {"cash": 400, "morale": 2, "resolve": True, "result": "You pocket a startlingly generous gift for doing very little."}},
                {"label": "The pressure is perfectly fine",
                 "outcome": {"morale": -4, "resolve": True, "result": "They are scandalized. The gift, regrettably, is rescinded."}}]}}},
    "goldbergs_extend": {
        "title": "An Unusual Extension", "icon": "💎",
        "trigger": {"special": "is_goldbergs", "weight": 8, "cooldown_days": 40, "min_days_resident": 21},
        "stages": {"start": {
            "text": "Against all their usual habits, the Goldbergs are enjoying it here and float staying longer — at a generous premium, of course.",
            "choices": [
                {"label": "Welcome them to stay (+8% rent)",
                 "outcome": {"rent_mult": 1.08, "loyalty": 10, "morale": 8, "resolve": True, "result": "A rare long stay from old money. Your bank account approves."}},
                {"label": "A toast to it — same terms",
                 "outcome": {"loyalty": 12, "morale": 10, "resolve": True, "result": "They're charmed you didn't gouge them. Refreshing, they say."}},
                {"label": "Their suite awaits elsewhere",
                 "outcome": {"resolve": True, "result": "'Quite right. We do get restless.' They begin packing the silver."}}]}}},
    # ??? — THE MYSTERY. Pays early, in full. Says nothing.
    "mystery_package": {
        "title": "The Package", "icon": "📦",
        "trigger": {"special": "is_mystery", "weight": 10, "cooldown_days": 45, "min_days_resident": 7},
        "stages": {"start": {
            "text": "A plain box arrives at your door, addressed to you in elegant handwriting. No return address. It is, unmistakably, from ???.",
            "choices": [
                {"label": "Open it",
                 "outcome": {"goto": "open_box", "delay": 1, "result": "You carefully lift the lid…"}},
                {"label": "Leave it sealed on the shelf",
                 "outcome": {"morale": 4, "resolve": True, "result": "Some things are better left unopened. The humming from their unit stops that night."}}]},
            "open_box": {"auto": True, "roll": [
                {"weight": 60, "text": "Inside: a neat stack of cash and a card reading 'For your trouble. There will be none.'",
                 "outcome": {"cash": 1200, "resolve": True}},
                {"weight": 40, "text": "Inside: an antique brass key that fits no lock you own — and the next morning, the property's every flaw has quietly mended itself.",
                 "outcome": {"condition": 30, "resolve": True}}]}}},
    "mystery_request": {
        "title": "One Small Request", "icon": "🔑",
        "trigger": {"special": "is_mystery", "weight": 9, "cooldown_days": 45, "min_days_resident": 7},
        "stages": {"start": {
            "text": "A single typed line slides under your door: 'Do not enter the basement on the night of the full moon. This is the only thing I will ever ask.'",
            "choices": [
                {"label": "Honor the request without question",
                 "outcome": {"loyalty": 20, "condition": 15, "resolve": True, "result": "You never go down there that night. In return, the unit is impossibly well-kept, and the rent is always early."}},
                {"label": "Agree, but leave a camera",
                 "outcome": {"goto": "mystery_cam", "delay": 1, "result": "Curiosity gets the better of you…"}},
                {"label": "Refuse — it's your property",
                 "outcome": {"morale": -6, "resolve": True, "result": "The reply is a single word, slid back under the door: 'Pity.' The humming grows louder for a week."}}]},
            "mystery_cam": {"auto": True, "roll": [
                {"weight": 50, "text": "The footage is nothing but static from dusk to dawn. The camera is, afterward, mysteriously polished.",
                 "outcome": {"condition": 10, "resolve": True}},
                {"weight": 50, "text": "The camera simply won't record that night. You decide not to try again.",
                 "outcome": {"morale": 2, "resolve": True}}]}}},
    "mystery_offer": {
        "title": "The Standing Offer", "icon": "🌑",
        "trigger": {"special": "is_mystery", "weight": 8, "cooldown_days": 50, "min_days_resident": 21},
        "stages": {"start": {
            "text": "An envelope appears, heavier than it should be. Inside: a great deal of cash and a note offering to extend the lease 'indefinitely, on the current terms.' No signature.",
            "choices": [
                {"label": "Accept the indefinite lease (+$1,500)",
                 "outcome": {"cash": 1500, "loyalty": 20, "resolve": True, "result": "You shake a hand you never quite see. The arrangement is, in every way, ideal."}},
                {"label": "Accept the cash, keep it lease-to-lease",
                 "outcome": {"cash": 1500, "morale": 4, "resolve": True, "result": "They seem to expect this. The note vanishes from your hand."}},
                {"label": "Return the envelope unopened",
                 "outcome": {"morale": -2, "resolve": True, "result": "It's gone by morning, along with any memory of strange humming. The rent still arrives, early as ever."}}]}}},

    # ── Converted requests (now branching) ─────────────────────────────────────
    "duck": {
        "title": "The Duck", "icon": "🦆",
        "trigger": {"weight": 4, "cooldown_days": 84, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "{name} would like to keep a duck. Just one duck, they promise. A single, solitary duck.",
                "choices": [
                    {"label": "…Fine. One duck.",
                     "outcome": {"morale": 12, "flag": {"has_duck": True}, "goto": "more_ducks", "delay": 21,
                                 "result": "The duck has a name. The duck has a little ramp. The duck seems content."}},
                    {"label": "Allow it — cleaning deposit ($250)",
                     "outcome": {"cash": 250, "morale": 8, "flag": {"has_duck": True}, "resolve": True,
                                 "result": "Deposit in hand. The duck is, against all odds, impeccably behaved."}},
                    {"label": "Absolutely not",
                     "outcome": {"morale": -8, "resolve": True,
                                 "result": "They're crushed. The duck, you imagine, is also crushed."}},
                ],
            },
            "more_ducks": {"auto": True, "roll": [
                {"weight": 55, "text": "It was never one duck. There are now several ducks at {prop}. There is a kiddie pool.",
                 "outcome": {"condition": -18, "morale": 4, "resolve": True}},
                {"weight": 45, "text": "{name} kept their word — it really was just the one duck, and it's basically a mascot now.",
                 "outcome": {"morale": 6, "loyalty": 5, "resolve": True}},
            ]},
        },
    },
    "chickens": {
        "title": "Backyard Chickens", "icon": "🐔",
        "trigger": {"weight": 4, "cooldown_days": 84, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "{name} wants to keep backyard chickens. 'Fresh eggs!' they say, eyes shining.",
                "choices": [
                    {"label": "Sure — keep them in the yard",
                     "outcome": {"morale": 10, "damage_chance_add": 0.06, "goto": "egg_returns", "delay": 18,
                                 "result": "A modest coop appears. The neighborhood roosters now have competition."}},
                    {"label": "No livestock, sorry",
                     "outcome": {"morale": -7, "resolve": True,
                                 "result": "No eggs for you, then. Or for them."}},
                ],
            },
            "egg_returns": {"auto": True, "roll": [
                {"weight": 50, "text": "{name} keeps leaving fresh eggs at your door — lovely — but the coop's done a number on the yard.",
                 "outcome": {"condition": -22, "morale": 5, "loyalty": 6, "resolve": True}},
                {"weight": 50, "text": "The chickens are a tidy little operation, and {name} sends the occasional dozen eggs your way.",
                 "outcome": {"morale": 6, "resolve": True}},
            ]},
        },
    },

    # ── Batch 1: trait-driven situations ───────────────────────────────────────
    "noise_war": {
        "title": "Noise War", "icon": "🔊",
        "trigger": {"traits": ["rowdy"], "weight": 6, "cooldown_days": 60, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "The neighbors are filing complaints about late-night noise from {prop}.",
                "choices": [
                    {"label": "Have a friendly word with them",
                     "outcome": {"morale": -2, "goto": "talk", "delay": 3, "result": "You stop by to talk it out."}},
                    {"label": "Hire a mediator ($200)", "cost": {"cash": 200},
                     "outcome": {"morale": 2, "resolve": True, "result": "A neutral third party smooths it over. Peace restored."}},
                    {"label": "Stay out of it",
                     "outcome": {"goto": "escalate", "delay": 10, "result": "Not your circus. Probably fine."}},
                ],
            },
            "talk": {"auto": True, "roll": [
                {"weight": 60, "text": "{name} took the hint and dialed it back.", "outcome": {"morale": 3, "loyalty": 4, "resolve": True}},
                {"weight": 40, "text": "{name} promised to behave… and didn't.", "outcome": {"goto": "escalate", "delay": 7}},
            ]},
            "escalate": {"auto": True, "roll": [
                {"weight": 55, "text": "The city slapped a noise citation on {prop}.", "outcome": {"cash": -400, "morale": -8, "resolve": True}},
                {"weight": 45, "text": "A neighbor moved out and blamed your tenant. Awkward.", "outcome": {"morale": -5, "resolve": True}},
            ]},
        },
    },
    "handy_helper": {
        "title": "The Handy Tenant", "icon": "🔧",
        "trigger": {"traits": ["handy"], "weight": 6, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "{name} offers to renovate the place themselves over a weekend — for a small rent break.",
            "choices": [
                {"label": "Deal — comp a week's rent", "cost": {"cash_weeks": 1},
                 "outcome": {"condition": 25, "loyalty": 10, "resolve": True, "result": "Pro-grade work for a week's rent. Steal of a deal."}},
                {"label": "Just buy the materials ($250)", "cost": {"cash": 250},
                 "outcome": {"condition": 30, "morale": 6, "resolve": True, "result": "They do the labor; the place looks fantastic."}},
                {"label": "Thanks, but no",
                 "outcome": {"morale": -3, "resolve": True, "result": "They shrug and fix the squeaky door anyway."}},
            ]}},
    },
    "garden_takeover": {
        "title": "Garden Takeover", "icon": "🌱",
        "trigger": {"traits": ["green_thumb"], "weight": 6, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "{name} wants to transform the tired yard into a proper garden.",
            "choices": [
                {"label": "Go for it",
                 "outcome": {"condition": 12, "morale": 8, "resolve": True, "result": "The curb appeal is unreal. Neighbors keep stopping to look."}},
                {"label": "Chip in for supplies ($150)", "cost": {"cash": 150},
                 "outcome": {"condition": 20, "loyalty": 8, "resolve": True, "result": "A showpiece garden. Worth every dollar."}},
                {"label": "Keep the yard as-is",
                 "outcome": {"morale": -5, "resolve": True, "result": "They settle for a few pots on the porch."}},
            ]}},
    },
    "the_haggle": {
        "title": "The Haggle", "icon": "💰",
        "trigger": {"traits": ["penny"], "weight": 6, "cooldown_days": 56, "min_days_resident": 14},
        "stages": {"start": {
            "text": "{name} is making a case for a rent reduction — and they've brought a spreadsheet.",
            "choices": [
                {"label": "Hold firm",
                 "outcome": {"morale": -4, "resolve": True, "result": "They grumble, but they're not going anywhere over it."}},
                {"label": "Small cut to keep the peace (-3%)",
                 "outcome": {"rent_mult": 0.97, "morale": 8, "loyalty": 10, "resolve": True, "result": "A tiny discount buys a lot of goodwill."}},
                {"label": "Trade a chore for a break",
                 "outcome": {"condition": 8, "morale": 6, "resolve": True, "result": "They take on some upkeep in exchange. Win-win."}},
            ]}},
    },
    "the_report": {
        "title": "The Detailed Report", "icon": "🏠",
        "trigger": {"traits": ["homebody"], "weight": 6, "cooldown_days": 56, "min_days_resident": 14},
        "stages": {
            "start": {
                "text": "{name} hands you a meticulous list of three things 'starting to go' around the property.",
                "choices": [
                    {"label": "Fix all of it now ($350)", "cost": {"cash": 350},
                     "outcome": {"condition": 15, "morale": 8, "loyalty": 6, "resolve": True, "result": "Caught early, all minor. They feel heard."}},
                    {"label": "Handle the urgent one yourself",
                     "outcome": {"condition": 5, "morale": 3, "resolve": True, "result": "You take care of the worst of it."}},
                    {"label": "Tell them it's fine",
                     "outcome": {"morale": -4, "goto": "ignored", "delay": 14, "result": "You wave it off."}},
                ],
            },
            "ignored": {"auto": True, "roll": [
                {"weight": 60, "text": "One of those little issues at {prop} became a real repair.", "outcome": {"condition": -20, "resolve": True}},
                {"weight": 40, "text": "{name} quietly fixed it themselves and said nothing. The look says everything.", "outcome": {"morale": -6, "loyalty": -6, "resolve": True}},
            ]},
        },
    },
    "the_studio": {
        "title": "The Home Studio", "icon": "🎨",
        "trigger": {"traits": ["creative"], "weight": 6, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "{name} wants to turn the spare room into a studio — soundproofing, easels, the works.",
            "choices": [
                {"label": "Sure, get creative",
                 "outcome": {"morale": 10, "damage_chance_add": 0.06, "resolve": True, "result": "Paint everywhere, but they're inspired and happy."}},
                {"label": "Allow it — $300 deposit",
                 "outcome": {"cash": 300, "morale": 6, "damage_chance_add": 0.04, "resolve": True, "result": "Deposit covers the inevitable. They get to work."}},
                {"label": "Not in this unit",
                 "outcome": {"morale": -7, "resolve": True, "result": "They set up a corner easel instead, deflated."}},
            ]}},
    },
    "growing_family": {
        "title": "Growing Family", "icon": "👶",
        "trigger": {"traits": ["big_family"], "weight": 6, "cooldown_days": 84, "min_days_resident": 21},
        "stages": {
            "start": {
                "text": "The family is growing — {name} asks if a grandparent can move in to help out.",
                "choices": [
                    {"label": "Of course — family first",
                     "outcome": {"loyalty": 18, "morale": 8, "damage_chance_add": 0.03, "goto": "settled", "delay": 21, "result": "Three generations under one roof now."}},
                    {"label": "Adjust the lease (+10% rent)",
                     "outcome": {"rent_mult": 1.10, "morale": 2, "resolve": True, "result": "More people, fair bump. They agree it's reasonable."}},
                    {"label": "Sorry — occupancy limits",
                     "outcome": {"morale": -9, "loyalty": -6, "resolve": True, "result": "They're hurt. Grandma stays across town."}},
                ],
            },
            "settled": {"auto": True, "roll": [
                {"weight": 60, "text": "Grandma fixed the porch and bakes for the whole street. Best tenants ever.", "outcome": {"condition": 10, "loyalty": 8, "resolve": True}},
                {"weight": 40, "text": "A full house means more wear at {prop}.", "outcome": {"condition": -12, "resolve": True}},
            ]},
        },
    },
    "commit_offer": {
        "title": "Pay Ahead", "icon": "🎯",
        "trigger": {"traits": ["reliable"], "weight": 5, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "{name}, ever reliable, offers to commit to a longer stay if you'll trim the rent a touch.",
            "choices": [
                {"label": "Deal — small discount (-2%)",
                 "outcome": {"rent_mult": 0.98, "loyalty": 12, "morale": 6, "resolve": True, "result": "Locked-in income and a thrilled tenant."}},
                {"label": "Appreciate it, but no discount",
                 "outcome": {"morale": -2, "resolve": True, "result": "They pay on time regardless, as always."}},
            ]}},
    },
    "new_roommate": {
        "title": "The Roommate", "icon": "🛋️",
        "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 21},
        "stages": {"start": {
            "text": "{name} wants to bring on a roommate to split costs.",
            "choices": [
                {"label": "Fine — bump the rent (+8%)",
                 "outcome": {"rent_mult": 1.08, "damage_chance_add": 0.03, "morale": 2, "resolve": True, "result": "Two tenants, more rent, a bit more wear."}},
                {"label": "Allow it, no change",
                 "outcome": {"morale": 8, "loyalty": 6, "damage_chance_add": 0.04, "resolve": True, "result": "They're grateful you kept it simple."}},
                {"label": "One name on the lease only",
                 "outcome": {"morale": -6, "resolve": True, "result": "They drop it, a little put out."}},
            ]}},
    },
    "the_promotion": {
        "title": "The Promotion", "icon": "📈",
        "trigger": {"weight": 5, "cooldown_days": 84, "min_days_resident": 28, "min_morale": 40},
        "stages": {
            "start": {
                "text": "{name} just landed a big promotion and is in a celebrating mood.",
                "choices": [
                    {"label": "Congratulate them warmly",
                     "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "A little kindness goes a long way."}},
                    {"label": "Gently float a small raise (+5%)",
                     "outcome": {"goto": "raise_ask", "delay": 1, "result": "You bring up the rent…"}},
                    {"label": "Send a bottle of champagne ($60)", "cost": {"cash": 60},
                     "outcome": {"morale": 12, "loyalty": 12, "resolve": True, "result": "They're genuinely touched."}},
                ],
            },
            "raise_ask": {"auto": True, "roll": [
                {"weight": 60, "text": "Flush with the new salary, {name} accepts the bump.", "outcome": {"rent_mult": 1.05, "morale": -3, "resolve": True}},
                {"weight": 40, "text": "{name} politely declines — 'bad timing.'", "outcome": {"morale": -4, "resolve": True}},
            ]},
        },
    },
    # ── Batch 2: life events ───────────────────────────────────────────────────
    "new_baby": {"title": "A New Arrival", "icon": "👶", "trigger": {"weight": 5, "cooldown_days": 120, "min_days_resident": 28}, "stages": {"start": {"text": "{name} is expecting a baby and is over the moon about it.", "choices": [
        {"label": "Send a gift basket ($80)", "cost": {"cash": 80}, "outcome": {"morale": 10, "loyalty": 14, "resolve": True, "result": "They're touched you remembered."}},
        {"label": "Offer to repaint a nursery", "cost": {"cash": 250}, "outcome": {"condition": 6, "morale": 12, "loyalty": 10, "resolve": True, "result": "A fresh little nursery. They'll stay for years."}},
        {"label": "Congratulate them and move on", "outcome": {"morale": 4, "resolve": True, "result": "Warm wishes, nothing more."}}]}}},
    "breakup": {"title": "The Breakup", "icon": "💔", "trigger": {"weight": 5, "cooldown_days": 120, "min_days_resident": 21}, "stages": {"start": {"text": "{name} is going through a rough breakup — one of the couple is moving out.", "choices": [
        {"label": "Keep the lease as-is", "outcome": {"morale": -3, "resolve": True, "result": "They'll manage the rent alone, somehow."}},
        {"label": "Check in and be kind", "outcome": {"morale": 8, "loyalty": 10, "resolve": True, "result": "A little compassion goes a long way."}},
        {"label": "Trim the rent while they regroup (-4%)", "outcome": {"rent_mult": 0.96, "morale": 12, "loyalty": 12, "resolve": True, "result": "They won't forget the kindness."}}]}}},
    "retirement": {"title": "Retirement", "icon": "🌅", "trigger": {"weight": 5, "cooldown_days": 120, "min_days_resident": 60}, "stages": {"start": {"text": "{name} is retiring and would love to settle in here for the long haul.", "choices": [
        {"label": "Offer a long-stay discount (-2%)", "outcome": {"rent_mult": 0.98, "loyalty": 18, "morale": 10, "resolve": True, "result": "A loyal, low-maintenance tenant for years to come."}},
        {"label": "Keep terms the same", "outcome": {"loyalty": 6, "resolve": True, "result": "They're staying regardless."}},
        {"label": "Send a retirement gift ($100)", "cost": {"cash": 100}, "outcome": {"loyalty": 14, "morale": 10, "resolve": True, "result": "They're delighted."}}]}}},
    "job_relocation": {"title": "The Job Offer", "icon": "✈️", "trigger": {"weight": 5, "cooldown_days": 120, "min_days_resident": 28}, "stages": {
        "start": {"text": "{name} got a job offer in another city and is genuinely torn about leaving.", "choices": [
            {"label": "Offer an incentive to stay (-5%)", "outcome": {"rent_mult": 0.95, "morale": 8, "goto": "decide", "delay": 7, "result": "You make a case for staying…"}},
            {"label": "Wish them well", "outcome": {"goto": "decide_low", "delay": 7, "result": "You tell them to do what's best."}},
            {"label": "Help with a glowing reference", "outcome": {"loyalty": 10, "goto": "decide", "delay": 7, "result": "You write them a great reference either way."}}]},
        "decide": {"auto": True, "roll": [
            {"weight": 60, "text": "{name} decided to stay after all.", "outcome": {"loyalty": 8, "resolve": True}},
            {"weight": 40, "text": "{name} took the job and gave proper notice.", "outcome": {"leave": True}}]},
        "decide_low": {"auto": True, "roll": [
            {"weight": 65, "text": "{name} took the new job and moved on.", "outcome": {"leave": True}},
            {"weight": 35, "text": "It fell through — {name} is staying put.", "outcome": {"morale": 4, "resolve": True}}]}}},
    "lottery": {"title": "Lucky Numbers", "icon": "🍀", "trigger": {"weight": 4, "cooldown_days": 150, "min_days_resident": 21}, "stages": {
        "start": {"text": "{name} won a modest lottery prize and is feeling generous.", "choices": [
            {"label": "Accept a thank-you tip", "outcome": {"cash": 500, "morale": 6, "resolve": True, "result": "They slip you $500 'for being a decent landlord.'"}},
            {"label": "Suggest they invest it", "outcome": {"goto": "invest", "delay": 21, "result": "You give some sage advice…"}},
            {"label": "Congratulate them", "outcome": {"morale": 6, "resolve": True, "result": "Good for them."}}]},
        "invest": {"auto": True, "roll": [
            {"weight": 50, "text": "{name} used the winnings as a down payment — and gave notice.", "outcome": {"leave": True}},
            {"weight": 50, "text": "{name} blew it on a hot tub for the patio. Surprisingly, you don't mind.", "outcome": {"morale": 6, "condition": 4, "resolve": True}}]}}},
    "health_scare": {"title": "Health Scare", "icon": "🩺", "trigger": {"weight": 5, "cooldown_days": 120, "min_days_resident": 21}, "stages": {"start": {"text": "{name} had a health scare and needs a few accessibility fixes — a grab bar, better lighting.", "choices": [
        {"label": "Install everything ($300)", "cost": {"cash": 300}, "outcome": {"condition": 8, "morale": 14, "loyalty": 16, "resolve": True, "result": "They're moved that you cared. A tenant for life."}},
        {"label": "Offer a credit to DIY ($120)", "cost": {"cash": 120}, "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "They handle it with the credit."}},
        {"label": "Say it's not your responsibility", "outcome": {"morale": -14, "loyalty": -10, "resolve": True, "result": "Cold. They won't forget it."}}]}}},
    "back_to_school": {"title": "Back to School", "icon": "🎓", "trigger": {"weight": 4, "cooldown_days": 120, "min_days_resident": 21}, "stages": {"start": {"text": "{name} enrolled in night school and money's a little tighter now.", "choices": [
        {"label": "Temporary discount (-4%)", "outcome": {"rent_mult": 0.96, "morale": 10, "loyalty": 10, "resolve": True, "result": "They'll repay the faith."}},
        {"label": "Offer flexible due dates", "outcome": {"morale": 6, "pay_chance": -0.02, "resolve": True, "result": "A little breathing room helps."}},
        {"label": "Hold firm on terms", "outcome": {"morale": -5, "resolve": True, "result": "They tighten the budget and manage."}}]}}},
    "home_business": {"title": "The Side Hustle", "icon": "💻", "trigger": {"weight": 5, "cooldown_days": 100, "min_days_resident": 28}, "stages": {"start": {"text": "{name} quit their job to run a small business out of the unit.", "choices": [
        {"label": "Support the dream", "outcome": {"morale": 10, "damage_chance_add": 0.04, "resolve": True, "result": "Boxes and ring lights everywhere, but they're thriving."}},
        {"label": "Allow it — light commercial bump (+6%)", "outcome": {"rent_mult": 1.06, "morale": 2, "resolve": True, "result": "Fair, given the extra use. They agree."}},
        {"label": "No businesses in a residential unit", "outcome": {"morale": -8, "resolve": True, "result": "They rent a co-working desk instead, grumbling."}}]}}},
    "moving_in_partner": {"title": "Moving In Together", "icon": "💕", "trigger": {"weight": 5, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} wants their partner to move in.", "choices": [
        {"label": "Add them to the lease (+8%)", "outcome": {"rent_mult": 1.08, "damage_chance_add": 0.02, "morale": 4, "resolve": True, "result": "Two on the lease, fair bump."}},
        {"label": "Welcome them, no change", "outcome": {"morale": 10, "loyalty": 8, "damage_chance_add": 0.03, "resolve": True, "result": "They're thrilled you made it easy."}},
        {"label": "One leaseholder only", "outcome": {"morale": -7, "resolve": True, "result": "A frosty 'understood.'"}}]}}},
    "rescue_animals": {"title": "Foster Fails", "icon": "🐾", "trigger": {"weight": 4, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name} fosters rescue animals and asks to keep a few at the unit for a while.", "choices": [
        {"label": "Allow it", "outcome": {"morale": 10, "damage_chance_add": 0.07, "resolve": True, "result": "The place is a menagerie, but a happy one."}},
        {"label": "Allow it with a deposit ($300)", "outcome": {"cash": 300, "morale": 6, "damage_chance_add": 0.04, "resolve": True, "result": "Deposit covers the chaos."}},
        {"label": "Just one or two", "outcome": {"morale": 2, "damage_chance_add": 0.02, "resolve": True, "result": "A reasonable compromise."}}]}}},
    "tenant_anniversary": {"title": "One Year In", "icon": "🎂", "trigger": {"weight": 5, "cooldown_days": 200, "min_days_resident": 60}, "stages": {"start": {"text": "{name} leaves a kind note marking a year (or more) of renting from you.", "choices": [
        {"label": "Reciprocate with a small gift ($60)", "cost": {"cash": 60}, "outcome": {"loyalty": 16, "morale": 10, "resolve": True, "result": "A lovely little tradition begins."}},
        {"label": "Write a heartfelt note back", "outcome": {"loyalty": 10, "morale": 8, "resolve": True, "result": "Sometimes words are enough."}},
        {"label": "Let it pass", "outcome": {"morale": -2, "resolve": True, "result": "A missed moment, but no harm done."}}]}}},
    "family_visit": {"title": "Relatives in Town", "icon": "🧳", "trigger": {"weight": 5, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "{name}'s relatives are visiting and staying at the unit for a month.", "choices": [
        {"label": "No problem at all", "outcome": {"morale": 8, "resolve": True, "result": "A full, happy house for a few weeks."}},
        {"label": "Ask for a small occupancy fee ($150)", "outcome": {"cash": 150, "morale": -2, "resolve": True, "result": "They pay it, a touch surprised."}},
        {"label": "Remind them of guest limits", "outcome": {"morale": -6, "resolve": True, "result": "The relatives get a hotel. Tension lingers."}}]}}},
    "new_job_upgrade": {"title": "Moving Up", "icon": "📈", "trigger": {"weight": 4, "cooldown_days": 120, "min_days_resident": 28, "min_morale": 45}, "stages": {"start": {"text": "{name} landed a great job and is eyeing nicer places — but loves it here.", "choices": [
        {"label": "Make the case to stay", "outcome": {"loyalty": 10, "morale": 6, "resolve": True, "result": "Loyalty wins out — they re-commit."}},
        {"label": "Propose a modest raise (+4%)", "outcome": {"rent_mult": 1.04, "morale": -2, "resolve": True, "result": "They can afford it now and agree."}},
        {"label": "Wish them well if they go", "outcome": {"morale": 2, "resolve": True, "result": "No pressure. They appreciate it."}}]}}},
    "midlife_motorcycle": {"title": "The Motorcycle", "icon": "🏍️", "trigger": {"weight": 4, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name} bought a motorcycle and wants to store it inside over winter.", "choices": [
        {"label": "Sure, in the garage", "outcome": {"morale": 8, "damage_chance_add": 0.03, "resolve": True, "result": "Oil stains, but a happy tenant."}},
        {"label": "Charge a storage fee ($200)", "outcome": {"cash": 200, "morale": 2, "resolve": True, "result": "Fair's fair. They pay up."}},
        {"label": "Outdoor parking only", "outcome": {"morale": -4, "resolve": True, "result": "It gets a tarp and a sad corner of the lot."}}]}}},
    "newlyweds": {"title": "The Engagement", "icon": "💍", "trigger": {"weight": 4, "cooldown_days": 150, "min_days_resident": 21}, "stages": {"start": {"text": "{name} just got engaged and wants to host a small engagement party at the place.", "choices": [
        {"label": "Of course — congrats!", "outcome": {"morale": 10, "damage_chance_add": 0.04, "resolve": True, "result": "A joyful night. Minor wear, major goodwill."}},
        {"label": "Fine, with a cleaning deposit ($150)", "outcome": {"cash": 150, "morale": 6, "resolve": True, "result": "Deposit secured, party approved."}},
        {"label": "Keep it small, please", "outcome": {"morale": -3, "resolve": True, "result": "A quiet toast instead."}}]}}},
    "remote_upgrade": {"title": "Work-From-Home Woes", "icon": "🖥️", "trigger": {"weight": 5, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} works from home now and the unit's wiring and AC aren't keeping up.", "choices": [
        {"label": "Upgrade it properly ($400)", "cost": {"cash": 400}, "outcome": {"condition": 12, "morale": 10, "loyalty": 8, "resolve": True, "result": "A pro setup. They'll renew without blinking."}},
        {"label": "Split the cost with them ($150)", "cost": {"cash": 150}, "outcome": {"condition": 6, "morale": 6, "resolve": True, "result": "A fair compromise."}},
        {"label": "Suggest a co-working space", "outcome": {"morale": -6, "resolve": True, "result": "They're not impressed."}}]}}},
    "empty_nest": {"title": "Empty Nest", "icon": "🪺", "trigger": {"weight": 4, "cooldown_days": 150, "min_days_resident": 60}, "stages": {"start": {"text": "{name}'s kids have moved out and the place suddenly feels too big and too quiet.", "choices": [
        {"label": "Check in warmly", "outcome": {"morale": 8, "loyalty": 8, "resolve": True, "result": "They appreciate being seen."}},
        {"label": "Suggest taking in a boarder", "outcome": {"goto": "boarder", "delay": 14, "result": "You float the idea of renting a room out."}},
        {"label": "Leave them to it", "outcome": {"resolve": True, "result": "They'll adjust in time."}}]},
        "boarder": {"auto": True, "roll": [
            {"weight": 55, "text": "{name} took in a lovely boarder and feels alive again.", "outcome": {"morale": 8, "loyalty": 6, "resolve": True}},
            {"weight": 45, "text": "The boarder didn't work out and left a mess.", "outcome": {"condition": -10, "morale": -4, "resolve": True}}]}}},
    # ── Batch 3: property & neighbor drama ─────────────────────────────────────
    "parking_dispute": {"title": "Parking Wars", "icon": "🅿️", "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 14}, "stages": {
        "start": {"text": "A neighbor keeps parking in {name}'s assigned spot, and tempers are flaring.", "choices": [
            {"label": "Paint the spot number clearly ($60)", "cost": {"cash": 60}, "outcome": {"morale": 6, "resolve": True, "result": "A little paint settles it."}},
            {"label": "Talk to the neighbor", "outcome": {"goto": "talk", "delay": 4, "result": "You go have a word."}},
            {"label": "Tell them to sort it out", "outcome": {"morale": -6, "resolve": True, "result": "They're annoyed you won't help."}}]},
        "talk": {"auto": True, "roll": [{"weight": 65, "text": "The neighbor apologized and stopped.", "outcome": {"morale": 5, "loyalty": 4, "resolve": True}}, {"weight": 35, "text": "It turned into a shouting match in the lot.", "outcome": {"morale": -6, "resolve": True}}]}}},
    "package_thief": {"title": "Porch Pirate", "icon": "📦", "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 14}, "stages": {"start": {"text": "{name}'s packages keep vanishing off the porch.", "choices": [
        {"label": "Install a doorbell camera ($120)", "cost": {"cash": 120}, "outcome": {"condition": 3, "morale": 8, "resolve": True, "result": "Thefts stop overnight. They feel safe."}},
        {"label": "Suggest a parcel locker", "outcome": {"morale": 3, "resolve": True, "result": "A decent workaround."}},
        {"label": "Not your problem", "outcome": {"morale": -7, "resolve": True, "result": "They start having things shipped to work."}}]}}},
    "pest_problem": {"title": "Uninvited Guests", "icon": "🪳", "trigger": {"weight": 5, "cooldown_days": 60, "min_days_resident": 14}, "stages": {
        "start": {"text": "{name} reports a pest problem creeping in.", "choices": [
            {"label": "Call an exterminator ($300)", "cost": {"cash": 300}, "outcome": {"condition": 6, "morale": 8, "resolve": True, "result": "Handled professionally. Crisis averted."}},
            {"label": "Drop off traps and spray ($40)", "cost": {"cash": 40}, "outcome": {"morale": 2, "goto": "linger", "delay": 14, "result": "A cheap first attempt."}},
            {"label": "Tell them to keep it cleaner", "outcome": {"morale": -8, "goto": "linger", "delay": 14, "result": "You imply it's their fault."}}]},
        "linger": {"auto": True, "roll": [{"weight": 55, "text": "The infestation spread before it was dealt with.", "outcome": {"condition": -18, "morale": -8, "resolve": True}}, {"weight": 45, "text": "The traps did the trick after all.", "outcome": {"morale": 2, "resolve": True}}]}}},
    "ac_breakdown": {"title": "Heat Wave", "icon": "🥵", "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 7, "season": 1}, "stages": {"start": {"text": "The AC died during a brutal heat wave and {name} is miserable.", "choices": [
        {"label": "Emergency repair, today ($500)", "cost": {"cash": 500}, "outcome": {"condition": 8, "morale": 12, "loyalty": 8, "resolve": True, "result": "Cool air by evening. They're grateful."}},
        {"label": "Drop off window units ($150)", "cost": {"cash": 150}, "outcome": {"morale": 4, "resolve": True, "result": "Not elegant, but it works."}},
        {"label": "It'll get scheduled eventually", "outcome": {"morale": -16, "resolve": True, "result": "Three sweltering days. They are furious."}}]}}},
    "storm_branch": {"title": "Storm Damage", "icon": "🌬️", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 7}, "stages": {"start": {"text": "A storm dropped a heavy branch on the property.", "choices": [
        {"label": "Full removal + cleanup ($350)", "cost": {"cash": 350}, "outcome": {"condition": 6, "morale": 6, "resolve": True, "result": "Cleared and tidy by the weekend."}},
        {"label": "Quick clear, deal with the rest later ($100)", "cost": {"cash": 100}, "outcome": {"morale": 2, "resolve": True, "result": "Good enough for now."}},
        {"label": "Leave it", "outcome": {"condition": -10, "morale": -5, "resolve": True, "result": "The yard's a mess and the tenant's embarrassed."}}]}}},
    "basement_flood": {"title": "Basement Flood", "icon": "🌊", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 14, "min_condition": 30}, "stages": {
        "start": {"text": "Heavy rain flooded the basement at {prop}.", "choices": [
            {"label": "Pump, dry, and restore ($600)", "cost": {"cash": 600}, "outcome": {"condition": 10, "morale": 8, "resolve": True, "result": "Fully restored, no lasting damage."}},
            {"label": "Pump it and hope ($150)", "cost": {"cash": 150}, "outcome": {"goto": "mold_risk", "delay": 18, "result": "Water's gone, dampness remains."}},
            {"label": "Let it dry on its own", "outcome": {"condition": -12, "morale": -8, "goto": "mold_risk", "delay": 14, "result": "You leave it to nature."}}]},
        "mold_risk": {"auto": True, "roll": [{"weight": 55, "text": "Mold took hold in the damp basement.", "outcome": {"condition": -22, "morale": -10, "resolve": True}}, {"weight": 45, "text": "It dried out fine in the end.", "outcome": {"resolve": True}}]}}},
    "roof_leak": {"title": "Ceiling Stain", "icon": "🏠", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "A brown stain is spreading across {name}'s ceiling — the roof's leaking.", "choices": [
        {"label": "Reroof the section ($800)", "cost": {"cash": 800}, "outcome": {"condition": 18, "morale": 8, "resolve": True, "result": "Done right. No more leaks."}},
        {"label": "Patch it for now ($150)", "cost": {"cash": 150}, "outcome": {"condition": 4, "morale": 3, "resolve": True, "result": "Holds for this season, at least."}},
        {"label": "Put a bucket under it", "outcome": {"condition": -16, "morale": -10, "resolve": True, "result": "The stain — and the smell — only grow."}}]}}},
    "neighbor_feud": {"title": "Neighbor Feud", "icon": "😠", "trigger": {"weight": 4, "cooldown_days": 70, "min_days_resident": 21}, "stages": {"start": {"text": "{name} is locked in a petty, escalating feud with the next-door neighbor.", "choices": [
        {"label": "Mediate between them", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "You broker an uneasy peace."}},
        {"label": "Stay strictly neutral", "outcome": {"resolve": True, "result": "Not your fight. It eventually fizzles."}},
        {"label": "Take your tenant's side loudly", "outcome": {"morale": 10, "goto": "fallout", "delay": 10, "result": "You back them to the hilt."}}]},
        "fallout": {"auto": True, "roll": [{"weight": 50, "text": "Your tenant adores you for it; the neighbor complains to the city.", "outcome": {"loyalty": 8, "cash": -200, "resolve": True}}, {"weight": 50, "text": "It blew over and everyone moved on.", "outcome": {"resolve": True}}]}}},
    "graffiti": {"title": "Tagged", "icon": "🎨", "trigger": {"weight": 4, "cooldown_days": 70, "min_days_resident": 7}, "stages": {"start": {"text": "Someone tagged the exterior wall with graffiti overnight.", "choices": [
        {"label": "Repaint the wall ($200)", "cost": {"cash": 200}, "outcome": {"condition": 6, "morale": 4, "resolve": True, "result": "Gone by morning. Curb appeal restored."}},
        {"label": "Pressure-wash it ($50)", "cost": {"cash": 50}, "outcome": {"condition": 2, "resolve": True, "result": "Mostly gone — a faint shadow remains."}},
        {"label": "Leave it as 'urban character'", "outcome": {"condition": -6, "morale": -5, "resolve": True, "result": "The tag invites more tags."}}]}}},
    "car_breakin": {"title": "Break-In in the Lot", "icon": "🚗", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "{name}'s car was broken into in the parking lot.", "choices": [
        {"label": "Add lighting and a camera ($250)", "cost": {"cash": 250}, "outcome": {"condition": 4, "morale": 8, "loyalty": 6, "resolve": True, "result": "They feel looked-after. No repeat incidents."}},
        {"label": "Be supportive, file a report together", "outcome": {"morale": 6, "resolve": True, "result": "It helps to feel heard."}},
        {"label": "Shrug it off", "outcome": {"morale": -8, "goto": "repeat", "delay": 14, "result": "You don't do much."}}]},
        "repeat": {"auto": True, "roll": [{"weight": 50, "text": "There was a second break-in. {name} is rattled.", "outcome": {"morale": -8, "resolve": True}}, {"weight": 50, "text": "Thankfully, no repeat.", "outcome": {"resolve": True}}]}}},
    "power_outage": {"title": "The Long Outage", "icon": "🔌", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 7}, "stages": {"start": {"text": "An extended power outage spoiled everything in {name}'s fridge.", "choices": [
        {"label": "Reimburse the groceries ($100)", "cost": {"cash": 100}, "outcome": {"morale": 10, "loyalty": 10, "resolve": True, "result": "A small gesture, big goodwill."}},
        {"label": "Sympathize, but it's the utility's fault", "outcome": {"morale": 2, "resolve": True, "result": "Fair point, mostly accepted."}},
        {"label": "Not your problem", "outcome": {"morale": -7, "resolve": True, "result": "They disagree, pointedly."}}]}}},
    "hoa_fine": {"title": "HOA Trouble", "icon": "📋", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21}, "stages": {"start": {"text": "The HOA fined you over {name}'s overgrown lawn and 'unapproved' decor.", "choices": [
        {"label": "Pay it and ask them to tidy up ($250)", "cost": {"cash": 250}, "outcome": {"morale": 2, "condition": 4, "resolve": True, "result": "Smoothed over; they trim the hedges."}},
        {"label": "Pass the fine to the tenant", "outcome": {"morale": -10, "resolve": True, "result": "Technically fair. They're not happy."}},
        {"label": "Fight the HOA", "outcome": {"goto": "hoa_fight", "delay": 14, "result": "You take it to the next meeting."}}]},
        "hoa_fight": {"auto": True, "roll": [{"weight": 50, "text": "You won the appeal — fine waived.", "outcome": {"morale": 4, "resolve": True}}, {"weight": 50, "text": "You lost, and now they're watching you.", "outcome": {"cash": -250, "resolve": True}}]}}},
    "water_heater": {"title": "Cold Showers", "icon": "🚿", "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 7}, "stages": {"start": {"text": "The water heater quit — {name} has been taking cold showers for two days.", "choices": [
        {"label": "Replace it ($700)", "cost": {"cash": 700}, "outcome": {"condition": 14, "morale": 10, "resolve": True, "result": "Endless hot water again. Relief all around."}},
        {"label": "Repair the old one ($200)", "cost": {"cash": 200}, "outcome": {"condition": 4, "morale": 5, "resolve": True, "result": "Patched up — should last a while."}},
        {"label": "Tell them you'll get to it", "outcome": {"morale": -12, "resolve": True, "result": "Day three of cold showers. They are not amused."}}]}}},
    "driveway_crack": {"title": "Trip Hazard", "icon": "🧱", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "The cracked walkway is becoming a genuine trip hazard.", "choices": [
        {"label": "Repave it properly ($500)", "cost": {"cash": 500}, "outcome": {"condition": 12, "morale": 4, "resolve": True, "result": "Smooth and safe. One less worry."}},
        {"label": "Patch the worst cracks ($120)", "cost": {"cash": 120}, "outcome": {"condition": 4, "resolve": True, "result": "Good enough to stop the stumbling."}},
        {"label": "Put up a 'watch your step' sign", "outcome": {"morale": -4, "goto": "trip", "delay": 21, "result": "A sign'll do, surely."}}]},
        "trip": {"auto": True, "roll": [{"weight": 40, "text": "A guest tripped and there was talk of liability.", "outcome": {"cash": -400, "morale": -6, "resolve": True}}, {"weight": 60, "text": "Nobody got hurt, thankfully.", "outcome": {"resolve": True}}]}}},
    "appliance_choice": {"title": "Fridge on the Fritz", "icon": "🧊", "trigger": {"weight": 5, "cooldown_days": 70, "min_days_resident": 14}, "stages": {"start": {"text": "The refrigerator is dying — humming, leaking, barely cold.", "choices": [
        {"label": "Buy a nice new one ($600)", "cost": {"cash": 600}, "outcome": {"condition": 10, "morale": 8, "resolve": True, "result": "Shiny, quiet, ice-cold. A clear upgrade."}},
        {"label": "Grab a used replacement ($200)", "cost": {"cash": 200}, "outcome": {"condition": 4, "morale": 3, "resolve": True, "result": "It works. That's what matters."}},
        {"label": "Tell them to defrost it more", "outcome": {"morale": -8, "resolve": True, "result": "That is not how refrigerators work, and they know it."}}]}}},
    "noisy_construction": {"title": "Construction Next Door", "icon": "🚧", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "A months-long construction project next door is driving {name} up the wall.", "choices": [
        {"label": "Offer a small rent credit ($100)", "cost": {"cash": 100}, "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "A fair gesture for the disruption."}},
        {"label": "Drop off some earplugs and sympathy", "outcome": {"morale": 4, "resolve": True, "result": "It's the thought that counts."}},
        {"label": "Nothing you can do about it", "outcome": {"morale": -6, "resolve": True, "result": "True, but cold comfort."}}]}}},
    # ── Batch 4: money & lease situations ──────────────────────────────────────
    "wants_to_buy": {"title": "An Offer to Buy", "icon": "🏷️", "trigger": {"weight": 3, "cooldown_days": 150, "min_days_resident": 60, "min_morale": 55}, "stages": {"start": {"text": "{name} loves the place so much they ask if you'd ever consider selling it to them.", "choices": [
        {"label": "Not for sale — but I'm flattered", "outcome": {"loyalty": 10, "morale": 6, "resolve": True, "result": "They take it as the compliment it is."}},
        {"label": "Everything's for sale at a price", "outcome": {"goto": "haggle_buy", "delay": 7, "result": "You name a (high) number."}},
        {"label": "Offer rent-to-own talk later", "outcome": {"loyalty": 8, "resolve": True, "result": "A maybe is enough to keep them happy."}}]},
        "haggle_buy": {"auto": True, "roll": [{"weight": 75, "text": "{name} couldn't swing your asking price, but appreciated the honesty.", "outcome": {"morale": 4, "resolve": True}}, {"weight": 25, "text": "{name} got serious about financing — one to revisit.", "outcome": {"loyalty": 6, "resolve": True}}]}}},
    "late_excuse": {"title": "The Excuse", "icon": "🐕", "trigger": {"weight": 5, "cooldown_days": 50, "min_days_resident": 14}, "stages": {"start": {"text": "Rent's late, and {name} has a truly spectacular excuse involving a dog and a printer.", "choices": [
        {"label": "Give them grace this once", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "They pay two days later, mortified and grateful."}},
        {"label": "Charge the late fee ($50)", "outcome": {"cash": 50, "morale": -5, "resolve": True, "result": "Rules are rules. They pay it."}},
        {"label": "Firm reminder, no fee", "outcome": {"pay_chance": 0.01, "resolve": True, "result": "Message received. It won't happen again."}}]}}},
    "early_break": {"title": "Breaking the Lease", "icon": "🚪", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} needs to break the lease early and is asking how to handle it.", "choices": [
        {"label": "Let them go, keep the deposit", "outcome": {"cash": 400, "leave": True, "result": "Clean break. You keep the deposit and re-list."}},
        {"label": "Negotiate a buyout (+$900)", "outcome": {"cash": 900, "leave": True, "result": "They pay to walk away amicably."}},
        {"label": "Hold them to the lease", "outcome": {"morale": -10, "resolve": True, "result": "They stay, resentful, counting the days."}}]}}},
    "deposit_talk": {"title": "Deposit Dispute", "icon": "💵", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21}, "stages": {"start": {"text": "{name} is anxious about getting their full deposit back someday and wants reassurance now.", "choices": [
        {"label": "Promise a fair walkthrough", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Transparency buys trust."}},
        {"label": "Offer a small move-in credit ($75)", "cost": {"cash": 75}, "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "A goodwill gesture lands well."}},
        {"label": "Brush off the worry", "outcome": {"morale": -6, "resolve": True, "result": "They start photographing every scratch."}}]}}},
    "rent_strike": {"title": "Withholding Rent", "icon": "✊", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21, "max_morale": 55}, "stages": {
        "start": {"text": "{name} is threatening to withhold rent until a lingering issue gets fixed.", "choices": [
            {"label": "Fix the issue properly ($300)", "cost": {"cash": 300}, "outcome": {"condition": 8, "morale": 12, "resolve": True, "result": "Addressed. Rent resumes, relationship repaired."}},
            {"label": "Compromise — partial fix + credit ($120)", "cost": {"cash": 120}, "outcome": {"morale": 5, "resolve": True, "result": "Not perfect, but it defuses things."}},
            {"label": "Call their bluff", "outcome": {"goto": "bluff", "delay": 10, "result": "You hold your ground."}}]},
        "bluff": {"auto": True, "roll": [{"weight": 50, "text": "{name} backed down and paid up.", "outcome": {"morale": -4, "resolve": True}}, {"weight": 50, "text": "{name} actually withheld — and started looking for legal advice.", "outcome": {"morale": -10, "pay_chance": -0.05, "resolve": True}}]}}},
    "upgrade_ultimatum": {"title": "Upgrade or I Walk", "icon": "🔧", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 28}, "stages": {"start": {"text": "{name} will happily re-sign — if you upgrade the kitchen first.", "choices": [
        {"label": "Do the upgrade ($900)", "cost": {"cash": 900}, "outcome": {"condition": 20, "loyalty": 14, "morale": 10, "resolve": True, "result": "A lovely kitchen and a locked-in tenant."}},
        {"label": "Meet halfway — new appliances ($350)", "cost": {"cash": 350}, "outcome": {"condition": 8, "morale": 6, "resolve": True, "result": "A fair compromise they accept."}},
        {"label": "No upgrades", "outcome": {"morale": -8, "resolve": True, "result": "They mark it down as a strike against renewing."}}]}}},
    "bounced_payment": {"title": "Bounced Payment", "icon": "📉", "trigger": {"weight": 4, "cooldown_days": 60, "min_days_resident": 14}, "stages": {"start": {"text": "{name}'s rent payment bounced — they swear it's a bank glitch.", "choices": [
        {"label": "Waive it, no big deal", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Grace appreciated; they fix it same day."}},
        {"label": "Charge the NSF fee ($35)", "outcome": {"cash": 35, "morale": -3, "resolve": True, "result": "Standard fee, paid without much fuss."}},
        {"label": "Set them up on autopay", "outcome": {"pay_chance": 0.03, "morale": 3, "resolve": True, "result": "Future payments now run like clockwork."}}]}}},
    "prepay_deal": {"title": "Cash Up Front", "icon": "💸", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} offers a chunk of cash up front in exchange for a small ongoing discount.", "choices": [
        {"label": "Take the deal (+$1,000, -3% rent)", "outcome": {"cash": 1000, "rent_mult": 0.97, "loyalty": 10, "resolve": True, "result": "Cash in hand, a happy long-term tenant."}},
        {"label": "Cash yes, no discount (+$600)", "outcome": {"cash": 600, "morale": 4, "resolve": True, "result": "They go for it anyway."}},
        {"label": "Prefer steady monthly", "outcome": {"resolve": True, "result": "No harm in keeping it simple."}}]}}},
    "long_lease": {"title": "The Long Lease", "icon": "📜", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 28, "min_morale": 55}, "stages": {"start": {"text": "{name} asks for a two-year lease — they want to put down roots.", "choices": [
        {"label": "Grant it with a small discount (-2%)", "outcome": {"rent_mult": 0.98, "loyalty": 20, "morale": 8, "resolve": True, "result": "Two years of guaranteed, happy income."}},
        {"label": "Grant it at the current rate", "outcome": {"loyalty": 12, "morale": 5, "resolve": True, "result": "Stability for you both."}},
        {"label": "Prefer to keep it year-to-year", "outcome": {"morale": -4, "resolve": True, "result": "They're a little disappointed."}}]}}},
    "utility_dispute": {"title": "Whose Bill Is It?", "icon": "🧾", "trigger": {"weight": 4, "cooldown_days": 70, "min_days_resident": 14}, "stages": {"start": {"text": "{name} is disputing who's responsible for a surprise utility bill.", "choices": [
        {"label": "Eat the cost to keep peace ($120)", "cost": {"cash": 120}, "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Cheaper than a sour tenant."}},
        {"label": "Split it down the middle", "outcome": {"cash": -60, "morale": 3, "resolve": True, "result": "Fair is fair. They agree."}},
        {"label": "Point to the lease", "outcome": {"morale": -5, "resolve": True, "result": "Correct, but it stings."}}]}}},
    "referral": {"title": "A Good Word", "icon": "🤝", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 28, "min_morale": 55}, "stages": {"start": {"text": "{name} has a friend looking to rent and offers to vouch for them.", "choices": [
        {"label": "Thank them with a credit ($75)", "cost": {"cash": 75}, "outcome": {"loyalty": 12, "morale": 8, "resolve": True, "result": "A referral bonus — and a pre-screened lead."}},
        {"label": "Gladly take the lead", "outcome": {"loyalty": 8, "morale": 4, "resolve": True, "result": "Word-of-mouth is the best kind."}},
        {"label": "Not taking applications", "outcome": {"resolve": True, "result": "No harm done."}}]}}},
    "tax_passthrough": {"title": "Taxes Went Up", "icon": "🏛️", "trigger": {"weight": 4, "cooldown_days": 120, "min_days_resident": 28}, "stages": {"start": {"text": "Property taxes jumped this year. Do you pass any of it along to {name}?", "choices": [
        {"label": "Modest raise to cover it (+5%)", "outcome": {"rent_mult": 1.05, "morale": -6, "resolve": True, "result": "They grumble but understand."}},
        {"label": "Absorb it yourself", "outcome": {"morale": 8, "loyalty": 10, "resolve": True, "result": "They notice you didn't gouge them."}},
        {"label": "Explain it and split the difference (+2%)", "outcome": {"rent_mult": 1.02, "morale": -1, "resolve": True, "result": "A reasonable middle ground."}}]}}},
    "rent_relief": {"title": "A Tough Month", "icon": "🙏", "trigger": {"weight": 5, "cooldown_days": 60, "min_days_resident": 14}, "stages": {"start": {"text": "{name} hit a rough patch and asks to defer part of this month's rent.", "choices": [
        {"label": "Defer it, no fee", "outcome": {"morale": 10, "loyalty": 10, "resolve": True, "result": "They pay it back in full next month, grateful."}},
        {"label": "Take partial now, rest later", "outcome": {"morale": 5, "resolve": True, "result": "A workable plan."}},
        {"label": "Rent's due on time", "outcome": {"morale": -8, "resolve": True, "result": "They scrape it together, resentful."}}]}}},
    "insurance_question": {"title": "Renters Insurance", "icon": "📄", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 14}, "stages": {"start": {"text": "After a minor mishap, {name} isn't sure what's covered by whom.", "choices": [
        {"label": "Walk them through it patiently", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "A confused tenant becomes a confident one."}},
        {"label": "Cover a small out-of-pocket cost ($100)", "cost": {"cash": 100}, "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "Above and beyond — they notice."}},
        {"label": "That's on their policy", "outcome": {"resolve": True, "result": "Accurate, if a little curt."}}]}}},
    # ── Batch 5: quirky & comedic ───────────────────────────────────────────────
    "garage_band": {"title": "The Garage Band", "icon": "🎸", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21}, "stages": {"start": {"text": "{name} has started a garage band. The good news: they're not bad. The bad news: it's 11pm.", "choices": [
        {"label": "Set practice hours, all good", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "A compromise everyone can live with."}},
        {"label": "Soundproof the garage ($250)", "cost": {"cash": 250}, "outcome": {"condition": 5, "morale": 12, "loyalty": 8, "resolve": True, "result": "Now they're your biggest fans."}},
        {"label": "Absolutely not", "outcome": {"morale": -8, "resolve": True, "result": "The band breaks up. So does some goodwill."}}]}}},
    "influencer_shoot": {"title": "Content Creator", "icon": "📸", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "{name} wants to film a home tour for their channel and tag the listing.", "choices": [
        {"label": "Sure — free marketing", "outcome": {"morale": 8, "loyalty": 4, "resolve": True, "result": "The video pulls 40k views. Your DMs are flooded with would-be renters."}},
        {"label": "Ask for a cut ($60)", "outcome": {"cash": 60, "morale": -2, "resolve": True, "result": "They pay, but find it a little gauche."}},
        {"label": "No filming, please", "outcome": {"morale": -4, "resolve": True, "result": "They respect it, reluctantly."}}]}}},
    "the_hoard": {"title": "Just a Little Clutter", "icon": "📦", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 45, "max_morale": 65}, "stages": {
        "start": {"text": "You notice {name}'s place is getting... full. Like, narrow-pathways full.", "choices": [
            {"label": "Gentle check-in", "outcome": {"goto": "hoard_check", "delay": 8, "result": "You offer help, no judgment."}},
            {"label": "Cite the lease's clutter clause", "outcome": {"morale": -6, "resolve": True, "result": "They clear a path, embarrassed."}},
            {"label": "Hire a cleanup ($200)", "cost": {"cash": 200}, "outcome": {"condition": 6, "morale": 8, "loyalty": 6, "resolve": True, "result": "A fresh start. They're quietly grateful."}}]},
        "hoard_check": {"auto": True, "roll": [{"weight": 60, "text": "{name} opened up — it was a rough year. They start decluttering.", "outcome": {"morale": 10, "loyalty": 8, "resolve": True}}, {"weight": 40, "text": "{name} got defensive and the clutter stayed.", "outcome": {"condition": -5, "morale": -4, "resolve": True}}]}}},
    "the_prepper": {"title": "Just In Case", "icon": "🥫", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30}, "stages": {"start": {"text": "{name} has converted the spare room into a survival pantry. They'd like to install a water tank.", "choices": [
        {"label": "Approve the tank", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "They feel safe. You feel oddly reassured too."}},
        {"label": "Pantry's fine, no plumbing changes", "outcome": {"morale": 2, "resolve": True, "result": "A fair line to draw."}},
        {"label": "This is a lot", "outcome": {"morale": -5, "resolve": True, "result": "They quietly judge your lack of preparedness."}}]}}},
    "the_aquarium": {"title": "The Giant Aquarium", "icon": "🐠", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30}, "stages": {"start": {"text": "{name} wants to install a 200-gallon saltwater aquarium. That's... a lot of water on a floor.", "choices": [
        {"label": "Approve, with a reinforced stand", "outcome": {"morale": 10, "loyalty": 6, "resolve": True, "result": "It's genuinely stunning. And it holds."}},
        {"label": "Smaller tank only", "outcome": {"morale": 2, "resolve": True, "result": "They settle for 40 gallons."}},
        {"label": "Picture the leak. No.", "outcome": {"morale": -4, "resolve": True, "result": "Your floors thank you."}}]}}},
    "the_telescope": {"title": "Rooftop Observatory", "icon": "🔭", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 30}, "stages": {"start": {"text": "{name}, an amateur astronomer, asks to mount a telescope platform on the roof.", "choices": [
        {"label": "Approve it properly ($150)", "cost": {"cash": 150}, "outcome": {"condition": 4, "morale": 10, "loyalty": 8, "resolve": True, "result": "They name a (very small) star after the house."}},
        {"label": "Balcony setup instead", "outcome": {"morale": 4, "resolve": True, "result": "Less ideal, but they make it work."}},
        {"label": "No roof access", "outcome": {"morale": -3, "resolve": True, "result": "They stargaze from the yard, wistfully."}}]}}},
    "the_beekeeper": {"title": "Backyard Bees", "icon": "🐝", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["green_thumb"]}, "stages": {"start": {"text": "{name} wants to keep two beehives in the yard. They promise jars of honey.", "choices": [
        {"label": "Approve the hives", "outcome": {"goto": "bee_result", "delay": 10, "result": "Welcome to beekeeping."}},
        {"label": "One hive, on probation", "outcome": {"morale": 4, "resolve": True, "result": "A cautious yes."}},
        {"label": "Too risky with neighbors", "outcome": {"morale": -4, "resolve": True, "result": "The bees find another home."}}]},
        "bee_result": {"auto": True, "roll": [{"weight": 80, "text": "The hives thrive — you get honey, the garden booms.", "outcome": {"condition": 6, "morale": 10, "loyalty": 8, "resolve": True}}, {"weight": 20, "text": "A neighbor got stung and complained loudly.", "outcome": {"morale": -4, "resolve": True}}]}}},
    "escape_room": {"title": "The Home Escape Room", "icon": "🗝️", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["creative"]}, "stages": {"start": {"text": "{name} has turned the basement into a homemade escape room and wants to charge friends admission.", "choices": [
        {"label": "Love it — just keep it safe", "outcome": {"morale": 10, "loyalty": 6, "resolve": True, "result": "It becomes a neighborhood legend."}},
        {"label": "No paid guests on the property", "outcome": {"morale": -2, "resolve": True, "result": "They keep it for friends only."}},
        {"label": "Ask for a small cut ($40)", "outcome": {"cash": 40, "morale": -1, "resolve": True, "result": "A modest house cut."}}]}}},
    "the_quail": {"title": "Quail This Time", "icon": "🐤", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "exclude_traits": ["rowdy"]}, "stages": {"start": {"text": "{name} read that quail are 'easier than chickens' and would like to keep a dozen.", "choices": [
        {"label": "Sure, with a proper coop", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Tiny eggs arrive at your door weekly."}},
        {"label": "We've been down this road", "outcome": {"morale": -2, "resolve": True, "result": "They take the gentle ribbing well."}},
        {"label": "No more livestock", "outcome": {"morale": -4, "resolve": True, "result": "The quail dream dies."}}]}}},
    "metal_detector": {"title": "X Marks the Yard", "icon": "🪙", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 30}, "stages": {
        "start": {"text": "{name} swears there's buried treasure in the backyard and wants to dig.", "choices": [
            {"label": "Let them dig (fill it back in!)", "outcome": {"goto": "dig_result", "delay": 6, "result": "Happy hunting."}},
            {"label": "No holes in my yard", "outcome": {"morale": -3, "resolve": True, "result": "They sulk with their detector."}}]},
        "dig_result": {"auto": True, "roll": [{"weight": 70, "text": "They found old bottle caps and a 1987 quarter. Thrilled anyway.", "outcome": {"morale": 6, "resolve": True}}, {"weight": 30, "text": "They actually found an old coin cache and split it with you!", "outcome": {"cash": 220, "morale": 8, "loyalty": 6, "resolve": True}}]}}},
    "karaoke_machine": {"title": "Karaoke Night", "icon": "🎤", "trigger": {"weight": 4, "cooldown_days": 70, "min_days_resident": 21, "traits": ["rowdy"]}, "stages": {"start": {"text": "{name} hosts weekly karaoke. The neighbors have... opinions about the 2am power ballads.", "choices": [
        {"label": "Mediate a reasonable curfew", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "Songs stop by 11. Mostly."}},
        {"label": "Shut it down", "outcome": {"morale": -8, "resolve": True, "result": "The mic goes quiet, and so does their warmth toward you."}},
        {"label": "Join one night", "outcome": {"morale": 12, "loyalty": 10, "resolve": True, "result": "Your duet was, by all accounts, a triumph."}}]}}},
    "the_statue": {"title": "Yard Art", "icon": "🗿", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["creative"]}, "stages": {"start": {"text": "{name} installed a large, abstract metal sculpture in the front yard. It's... bold.", "choices": [
        {"label": "Honestly? Kind of love it", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "It becomes the most photographed spot on the block."}},
        {"label": "Backyard only", "outcome": {"morale": 2, "resolve": True, "result": "A reasonable relocation."}},
        {"label": "It has to go", "outcome": {"morale": -6, "resolve": True, "result": "Art is subjective. They are hurt."}}]}}},
    "indoor_jungle": {"title": "The Indoor Jungle", "icon": "🪴", "trigger": {"weight": 3, "cooldown_days": 80, "min_days_resident": 30, "traits": ["green_thumb"]}, "stages": {"start": {"text": "{name} now has 200 houseplants and wants to install grow lights and a misting system.", "choices": [
        {"label": "Approve it (watch the humidity)", "outcome": {"condition": 4, "morale": 10, "loyalty": 8, "resolve": True, "result": "The place looks incredible. Air quality: elite."}},
        {"label": "Grow lights yes, no misters", "outcome": {"morale": 4, "resolve": True, "result": "A sensible middle path."}},
        {"label": "Worried about moisture damage", "outcome": {"morale": -3, "resolve": True, "result": "They scale back, a little crushed."}}]}}},
    "the_ghost": {"title": "Something in the Walls", "icon": "👻", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 30}, "stages": {
        "start": {"text": "{name} is convinced the place is haunted — knocking pipes, cold spots, the works.", "choices": [
            {"label": "Send someone to investigate ($120)", "cost": {"cash": 120}, "outcome": {"goto": "ghost_result", "delay": 5, "result": "A pro takes a look."}},
            {"label": "Reassure them it's an old house", "outcome": {"morale": 3, "resolve": True, "result": "They remain... unconvinced."}},
            {"label": "Play along, suggest a sage cleanse", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "They feel heard, which is half the battle."}}]},
        "ghost_result": {"auto": True, "roll": [{"weight": 85, "text": "It was a loose pipe and a drafty vent. Fixed — and the 'ghost' is gone.", "outcome": {"condition": 6, "morale": 8, "loyalty": 6, "resolve": True}}, {"weight": 15, "text": "The contractor found nothing and left looking a little pale.", "outcome": {"morale": 2, "resolve": True}}]}}},
    # ── Batch 6: trait depth (round 2) & seasonal ───────────────────────────────
    "rooftop_party": {"title": "Rooftop Rager", "icon": "🎉", "trigger": {"weight": 4, "cooldown_days": 70, "min_days_resident": 21, "traits": ["rowdy"]}, "stages": {
        "start": {"text": "{name} threw a rooftop party that, per three neighbors, 'shook the whole street.'", "choices": [
            {"label": "Stern warning, no fee", "outcome": {"morale": -4, "pay_chance": 0.0, "resolve": True, "result": "They dial it back. Mostly."}},
            {"label": "Charge for a noise complaint ($75)", "outcome": {"cash": 75, "morale": -7, "resolve": True, "result": "An expensive lesson."}},
            {"label": "Ask to be invited next time", "outcome": {"goto": "party_invite", "delay": 8, "result": "You disarm them with charm."}}]},
        "party_invite": {"auto": True, "roll": [{"weight": 70, "text": "They actually invited you — and kept it tamer out of respect.", "outcome": {"morale": 8, "loyalty": 10, "resolve": True}}, {"weight": 30, "text": "The next party was just as loud. Charm has limits.", "outcome": {"morale": -6, "condition": -3, "resolve": True}}]}}},
    "unauthorized_addition": {"title": "They Built... a Deck?", "icon": "🪚", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 45, "traits": ["handy"]}, "stages": {"start": {"text": "{name} built a (genuinely nice) deck out back — without asking first.", "choices": [
        {"label": "It's great — keep it, thank them", "outcome": {"condition": 12, "morale": 10, "loyalty": 8, "resolve": True, "result": "Free home improvement. You'll allow it."}},
        {"label": "Reimburse the materials ($150)", "cost": {"cash": 150}, "outcome": {"condition": 12, "morale": 14, "loyalty": 14, "resolve": True, "result": "A class move. They're a tenant for life now."}},
        {"label": "Lecture them on asking first", "outcome": {"condition": 6, "morale": -6, "resolve": True, "result": "Correct, but the deck stays and so does the chill between you."}}]}}},
    "mysterious_absence": {"title": "Gone, But Paid", "icon": "🌑", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 45, "traits": ["quiet"]}, "stages": {
        "start": {"text": "You haven't seen {name} in weeks — but rent keeps arriving, right on time.", "choices": [
            {"label": "Do a welfare check", "outcome": {"goto": "absence_check", "delay": 4, "result": "You knock, just in case."}},
            {"label": "Rent's paid — respect the privacy", "outcome": {"loyalty": 8, "morale": 4, "resolve": True, "result": "They appreciate not being hovered over."}}]},
        "absence_check": {"auto": True, "roll": [{"weight": 70, "text": "They were traveling for work. Touched you checked.", "outcome": {"loyalty": 6, "morale": 4, "resolve": True}}, {"weight": 30, "text": "They found it a bit intrusive, honestly.", "outcome": {"morale": -4, "resolve": True}}]}}},
    "camera_privacy": {"title": "Too Many Cameras", "icon": "📹", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["homebody"]}, "stages": {"start": {"text": "{name} feels uneasy about the exterior cameras and asks about privacy.", "choices": [
        {"label": "Walk them through what's recorded", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Transparency settles their nerves."}},
        {"label": "Remove the cameras facing their space ($60)", "cost": {"cash": 60}, "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "They feel respected at home."}},
        {"label": "Cameras stay, full stop", "outcome": {"morale": -6, "resolve": True, "result": "They feel watched in their own home."}}]}}},
    "the_mural": {"title": "The Mural", "icon": "🎨", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["creative"]}, "stages": {"start": {"text": "{name} painted a stunning mural across the living room wall and hopes you won't mind.", "choices": [
        {"label": "It's beautiful — leave it", "outcome": {"condition": 6, "morale": 12, "loyalty": 10, "resolve": True, "result": "Future renters will fight over this place."}},
        {"label": "Love it, but neutral it before move-out", "outcome": {"morale": 4, "resolve": True, "result": "A fair condition they accept."}},
        {"label": "Walls stay white ($40 to repaint)", "outcome": {"cash": -40, "morale": -8, "resolve": True, "result": "You repaint. The artist within them weeps."}}]}}},
    "kids_olympics": {"title": "Backyard Olympics", "icon": "🥇", "trigger": {"weight": 3, "cooldown_days": 80, "min_days_resident": 30, "traits": ["big_family"]}, "stages": {"start": {"text": "{name}'s kids have turned the yard into an athletic arena. The lawn is... a casualty.", "choices": [
        {"label": "Kids will be kids — reseed it ($90)", "cost": {"cash": 90}, "outcome": {"condition": 5, "morale": 10, "loyalty": 8, "resolve": True, "result": "The yard recovers; the family adores you."}},
        {"label": "Ask them to protect the lawn", "outcome": {"morale": 2, "resolve": True, "result": "They set up a 'track' on the patio instead."}},
        {"label": "Charge for yard damage ($60)", "outcome": {"cash": 60, "morale": -7, "resolve": True, "result": "Technically fair. Emotionally? Cold."}}]}}},
    "coupon_loophole": {"title": "The Fine Print", "icon": "🔎", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["penny"]}, "stages": {"start": {"text": "{name} found a clause in the lease they're convinced entitles them to a discount.", "choices": [
        {"label": "They're right — honor it (-3%)", "outcome": {"rent_mult": 0.97, "loyalty": 10, "morale": 8, "resolve": True, "result": "Fair's fair. They respect that you owned it."}},
        {"label": "Nice try — clarify the wording", "outcome": {"morale": -2, "resolve": True, "result": "They concede, grudgingly impressed you read it too."}},
        {"label": "Split the difference (-1%)", "outcome": {"rent_mult": 0.99, "morale": 4, "resolve": True, "result": "A negotiated peace."}}]}}},
    "reliable_vip": {"title": "The Golden Reference", "icon": "⭐", "trigger": {"weight": 3, "cooldown_days": 120, "min_days_resident": 60, "traits": ["reliable"], "min_morale": 60}, "stages": {"start": {"text": "{name} has been a model tenant for ages and offers to mentor a struggling neighbor of yours.", "choices": [
        {"label": "Gratefully accept their help", "outcome": {"loyalty": 12, "morale": 10, "resolve": True, "result": "The whole building runs smoother. Reputation up."}},
        {"label": "Reward them with a loyalty credit ($100)", "cost": {"cash": 100}, "outcome": {"loyalty": 16, "morale": 12, "resolve": True, "result": "They're floored. A tenant for life."}},
        {"label": "Politely keep things separate", "outcome": {"resolve": True, "result": "No harm; they understand."}}]}}},
    "sublet_office": {"title": "Working From... Whose Home?", "icon": "💼", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 30, "traits": ["subletter"]}, "stages": {
        "start": {"text": "You hear {name} has been quietly running a small business out of the unit — clients coming and going.", "choices": [
            {"label": "Allow it for a small bump (+4%)", "outcome": {"rent_mult": 1.04, "morale": 4, "resolve": True, "result": "Above board now, and you're compensated."}},
            {"label": "Residential only — shut it down", "outcome": {"morale": -8, "resolve": True, "result": "They comply, but the warmth cools."}},
            {"label": "Look the other way", "outcome": {"goto": "office_result", "delay": 12, "result": "You decide not to make a thing of it."}}]},
        "office_result": {"auto": True, "roll": [{"weight": 65, "text": "It stayed small and tidy. No harm done.", "outcome": {"loyalty": 6, "resolve": True}}, {"weight": 35, "text": "The foot traffic annoyed neighbors and wore on the place.", "outcome": {"condition": -6, "morale": -4, "resolve": True}}]}}},
    "holiday_goodwill": {"title": "Season's Greetings", "icon": "🎄", "trigger": {"weight": 4, "cooldown_days": 300, "min_days_resident": 30, "season": 3}, "stages": {"start": {"text": "It's the holidays. {name} has been a good tenant this year — do you mark the occasion?", "choices": [
        {"label": "Send a small gift ($50)", "cost": {"cash": 50}, "outcome": {"loyalty": 14, "morale": 14, "resolve": True, "result": "A card and a gift basket. They're genuinely touched."}},
        {"label": "Knock $25 off this month", "outcome": {"cash": -25, "loyalty": 10, "morale": 12, "resolve": True, "result": "A little holiday relief goes a long way."}},
        {"label": "A heartfelt thank-you note", "outcome": {"loyalty": 6, "morale": 6, "resolve": True, "result": "Free, sincere, and surprisingly effective."}}]}}},
    "summer_pool": {"title": "Pool Party Season", "icon": "🏊", "trigger": {"weight": 4, "cooldown_days": 300, "min_days_resident": 21, "season": 1}, "stages": {"start": {"text": "Summer's here and {name} asks about putting in an above-ground pool for the season.", "choices": [
        {"label": "Approve it (liability waiver signed)", "outcome": {"morale": 12, "loyalty": 8, "resolve": True, "result": "Best summer ever, per {name}."}},
        {"label": "A kiddie pool, maybe", "outcome": {"morale": 4, "resolve": True, "result": "A modest splash."}},
        {"label": "Too much liability", "outcome": {"morale": -4, "resolve": True, "result": "They settle for the sprinkler."}}]}}},
    "fall_yardwork": {"title": "Leaf It to Me", "icon": "🍂", "trigger": {"weight": 4, "cooldown_days": 300, "min_days_resident": 21, "season": 2}, "stages": {"start": {"text": "Autumn leaves are burying the yard. {name} asks who's handling cleanup.", "choices": [
        {"label": "Hire a service ($80)", "cost": {"cash": 80}, "outcome": {"condition": 5, "morale": 8, "resolve": True, "result": "Spotless yard, happy tenant."}},
        {"label": "Offer a rent credit if they do it ($40)", "outcome": {"cash": -40, "morale": 6, "loyalty": 6, "resolve": True, "result": "They like the deal and the autonomy."}},
        {"label": "It's in their lease to maintain", "outcome": {"morale": -3, "resolve": True, "result": "True, if a little brisk."}}]}}},
    "spring_cleaning": {"title": "Spring Refresh", "icon": "🌷", "trigger": {"weight": 4, "cooldown_days": 300, "min_days_resident": 21, "season": 0}, "stages": {"start": {"text": "Spring's arrived and {name} is in a refresh mood — they'd love some small updates.", "choices": [
        {"label": "Fund a refresh ($120)", "cost": {"cash": 120}, "outcome": {"condition": 8, "morale": 10, "loyalty": 6, "resolve": True, "result": "New paint, new energy. The place sparkles."}},
        {"label": "Provide supplies, they do the work", "outcome": {"cash": -40, "condition": 4, "morale": 6, "resolve": True, "result": "A team effort that brightens the unit."}},
        {"label": "Maybe next year", "outcome": {"morale": -2, "resolve": True, "result": "They tidy up on their own anyway."}}]}}},
    # ── Batch 7A: life events (round 2) ─────────────────────────────────────────
    "college_kid": {"title": "Off to College", "icon": "🎓", "trigger": {"weight": 4, "cooldown_days": 120, "min_days_resident": 30}, "stages": {"start": {"text": "{name}'s eldest is leaving for college and the house feels suddenly emptier.", "choices": [
        {"label": "Send a care package ($50)", "cost": {"cash": 50}, "outcome": {"loyalty": 10, "morale": 10, "resolve": True, "result": "A thoughtful touch they won't forget."}},
        {"label": "Warm congratulations", "outcome": {"morale": 6, "resolve": True, "result": "They appreciate you noticing."}},
        {"label": "Float downsizing to a smaller unit", "outcome": {"morale": -3, "resolve": True, "result": "Too soon — they're not ready to move."}}]}}},
    "military_deploy": {"title": "Deployment", "icon": "🎖️", "trigger": {"weight": 3, "cooldown_days": 150, "min_days_resident": 21}, "stages": {"start": {"text": "{name} is being deployed for several months and asks you to hold the unit.", "choices": [
        {"label": "Hold it, no questions", "outcome": {"loyalty": 18, "morale": 12, "resolve": True, "result": "They leave with one less worry. A tenant for life."}},
        {"label": "Hold it at a reduced holding rate (-20%)", "outcome": {"rent_mult": 0.80, "loyalty": 14, "morale": 10, "resolve": True, "result": "A generous arrangement they deeply value."}},
        {"label": "Can't hold it unpaid", "outcome": {"morale": -8, "resolve": True, "result": "They understand, but it stings."}}]}}},
    "inheritance": {"title": "An Inheritance", "icon": "📜", "trigger": {"weight": 3, "cooldown_days": 150, "min_days_resident": 30}, "stages": {"start": {"text": "{name} came into a modest inheritance and is weighing what to do with it.", "choices": [
        {"label": "Suggest prepaying their lease", "outcome": {"cash": 800, "loyalty": 8, "resolve": True, "result": "They prepay several months on the spot."}},
        {"label": "Just be happy for them", "outcome": {"morale": 6, "resolve": True, "result": "No strings, and they notice."}},
        {"label": "Mention you'd consider selling", "outcome": {"goto": "inherit_buy", "delay": 7, "result": "They mull it over."}}]},
        "inherit_buy": {"auto": True, "roll": [{"weight": 80, "text": "Not quite enough to buy — but they re-signed gladly.", "outcome": {"loyalty": 8, "resolve": True}}, {"weight": 20, "text": "They decided to keep renting and travel instead.", "outcome": {"morale": 4, "resolve": True}}]}}},
    "divorce_final": {"title": "A Fresh Start", "icon": "🕊️", "trigger": {"weight": 3, "cooldown_days": 120, "min_days_resident": 30}, "stages": {"start": {"text": "{name}'s divorce just finalized. They're rebuilding and want to stay put for stability.", "choices": [
        {"label": "Lock in their rate for a year", "outcome": {"loyalty": 14, "morale": 10, "resolve": True, "result": "Stability is exactly what they needed."}},
        {"label": "Check in and be supportive", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "A little kindness goes a long way."}},
        {"label": "Keep it strictly professional", "outcome": {"resolve": True, "result": "Fair enough. They carry on."}}]}}},
    "adoption": {"title": "Welcoming a Child", "icon": "🧸", "trigger": {"weight": 3, "cooldown_days": 130, "min_days_resident": 30}, "stages": {"start": {"text": "{name} is adopting a child and asks about adding a small safety upgrade or two.", "choices": [
        {"label": "Install childproofing ($150)", "cost": {"cash": 150}, "outcome": {"condition": 4, "loyalty": 14, "morale": 12, "resolve": True, "result": "They're moved that you cared."}},
        {"label": "Approve any changes they make", "outcome": {"loyalty": 8, "morale": 8, "resolve": True, "result": "Flexibility they're grateful for."}},
        {"label": "They can DIY at their cost", "outcome": {"morale": 2, "resolve": True, "result": "They handle it themselves."}}]}}},
    "eldercare": {"title": "Caring for a Parent", "icon": "👵", "trigger": {"weight": 3, "cooldown_days": 120, "min_days_resident": 30, "exclude_traits": ["big_family"]}, "stages": {"start": {"text": "{name}'s aging parent needs to move in, and they ask about accessibility tweaks.", "choices": [
        {"label": "Add a ramp and grab bars ($250)", "cost": {"cash": 250}, "outcome": {"condition": 5, "loyalty": 14, "morale": 12, "resolve": True, "result": "A real kindness during a hard time."}},
        {"label": "Approve the parent on the lease", "outcome": {"loyalty": 8, "morale": 6, "resolve": True, "result": "Family comes first."}},
        {"label": "Occupancy limits, sorry", "outcome": {"morale": -8, "resolve": True, "result": "A painful no for them."}}]}}},
    "career_change": {"title": "A New Path", "icon": "🧭", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 30}, "stages": {"start": {"text": "{name} is retraining for a whole new career, and income is bumpy for a few months.", "choices": [
        {"label": "Offer flexible due dates", "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "Breathing room they'll repay in loyalty."}},
        {"label": "Small temporary discount (-4%)", "outcome": {"rent_mult": 0.96, "morale": 8, "resolve": True, "result": "A bridge through the lean stretch."}},
        {"label": "Rent stays the same", "outcome": {"morale": -4, "resolve": True, "result": "They tighten the belt and manage."}}]}}},
    "podcast_start": {"title": "The Podcast", "icon": "🎙️", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name} started a podcast and wants to build a small recording booth in the closet.", "choices": [
        {"label": "Go for it, sounds fun", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "Episode one features a glowing landlord shoutout."}},
        {"label": "Closet only, easily removable", "outcome": {"morale": 4, "resolve": True, "result": "A reasonable boundary."}},
        {"label": "No structural changes", "outcome": {"morale": -3, "resolve": True, "result": "They record under a blanket fort instead."}}]}}},
    "wedding_host": {"title": "The Backyard Wedding", "icon": "💒", "trigger": {"weight": 3, "cooldown_days": 130, "min_days_resident": 30}, "stages": {"start": {"text": "{name} wants to host their small backyard wedding at the property.", "choices": [
        {"label": "What an honor — yes!", "outcome": {"loyalty": 16, "morale": 14, "resolve": True, "result": "A beautiful day. You're in the photos."}},
        {"label": "Yes, with a cleanup deposit ($200)", "outcome": {"cash": 200, "morale": 8, "resolve": True, "result": "They happily agree."}},
        {"label": "Too much liability", "outcome": {"morale": -6, "resolve": True, "result": "They book a venue, a little hurt."}}]}}},
    "puppy_training": {"title": "Puppy Problems", "icon": "🐶", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21}, "stages": {
        "start": {"text": "{name}'s new puppy has discovered the joy of chewing baseboards.", "choices": [
            {"label": "Offer to split a trainer ($90)", "cost": {"cash": 90}, "outcome": {"condition": 3, "morale": 10, "loyalty": 8, "resolve": True, "result": "A well-behaved pup and a grateful tenant."}},
            {"label": "Ask them to handle repairs", "outcome": {"goto": "puppy_later", "delay": 12, "result": "You trust them to sort it."}},
            {"label": "Add a pet damage deposit ($200)", "outcome": {"cash": 200, "morale": -3, "resolve": True, "result": "Fair, if a little cold."}}]},
        "puppy_later": {"auto": True, "roll": [{"weight": 70, "text": "The puppy grew out of it; they patched the baseboards themselves.", "outcome": {"condition": 2, "loyalty": 6, "resolve": True}}, {"weight": 30, "text": "The chewing spread to the door frames before it stopped.", "outcome": {"condition": -6, "resolve": True}}]}}},
    "outgrowing_space": {"title": "Bursting at the Seams", "icon": "📐", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 45, "traits": ["big_family"]}, "stages": {"start": {"text": "{name}'s family has simply outgrown the place and they're eyeing a move.", "choices": [
        {"label": "Offer them a bigger unit if you have one", "outcome": {"loyalty": 14, "morale": 10, "resolve": True, "result": "They'd love to stay in your portfolio."}},
        {"label": "Help them find space-saving fixes", "outcome": {"morale": 6, "resolve": True, "result": "It buys some time."}},
        {"label": "Wish them well", "outcome": {"morale": 2, "resolve": True, "result": "An amicable parting, eventually."}}]}}},
    "gap_year": {"title": "The Gap Year", "icon": "🌍", "trigger": {"weight": 3, "cooldown_days": 130, "min_days_resident": 30}, "stages": {"start": {"text": "{name} is taking a year to travel the world and asks whether they can hold the unit.", "choices": [
        {"label": "Allow a sublet while they're away", "outcome": {"goto": "gap_result", "delay": 14, "result": "You okay a vetted subletter."}},
        {"label": "Hold it if they keep paying", "outcome": {"loyalty": 10, "morale": 6, "resolve": True, "result": "They pay from afar and send postcards."}},
        {"label": "Can't hold it that long", "outcome": {"morale": -5, "resolve": True, "result": "They give notice, sadly."}}]},
        "gap_result": {"auto": True, "roll": [{"weight": 65, "text": "The subletter was lovely; the place stayed pristine.", "outcome": {"loyalty": 8, "resolve": True}}, {"weight": 35, "text": "The subletter left it a bit rough around the edges.", "outcome": {"condition": -6, "resolve": True}}]}}},
    # ── Batch 7B: maintenance & property (round 2) ──────────────────────────────
    "mold_spot": {"title": "The Mold Spot", "icon": "🦠", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14, "max_condition": 70}, "stages": {"start": {"text": "{name} found a patch of mold creeping up the bathroom wall.", "choices": [
        {"label": "Remediate it properly ($350)", "cost": {"cash": 350}, "outcome": {"condition": 10, "morale": 10, "resolve": True, "result": "Source found and sealed. No more mold."}},
        {"label": "Clean and ventilate ($80)", "cost": {"cash": 80}, "outcome": {"condition": 3, "morale": 3, "resolve": True, "result": "Better for now — keep an eye on it."}},
        {"label": "Tell them to wipe it down", "outcome": {"condition": -5, "morale": -8, "resolve": True, "result": "It comes right back, bigger."}}]}}},
    "gutter_clog": {"title": "Overflowing Gutters", "icon": "🍂", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "The gutters are clogged and rainwater is sheeting down the siding.", "choices": [
        {"label": "Clean and add guards ($180)", "cost": {"cash": 180}, "outcome": {"condition": 8, "morale": 5, "resolve": True, "result": "Done right, and low-maintenance going forward."}},
        {"label": "Quick clear-out ($50)", "cost": {"cash": 50}, "outcome": {"condition": 3, "resolve": True, "result": "Flowing again, for now."}},
        {"label": "It can wait for dry weather", "outcome": {"condition": -4, "resolve": True, "result": "A little siding damage sets in."}}]}}},
    "fence_repair": {"title": "The Leaning Fence", "icon": "🪵", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "A section of the backyard fence is leaning badly after the last storm.", "choices": [
        {"label": "Replace the section ($300)", "cost": {"cash": 300}, "outcome": {"condition": 8, "morale": 6, "resolve": True, "result": "Sturdy and straight again."}},
        {"label": "Prop and patch it ($70)", "cost": {"cash": 70}, "outcome": {"condition": 3, "resolve": True, "result": "Holds — for now."}},
        {"label": "Leave it leaning", "outcome": {"condition": -3, "morale": -3, "resolve": True, "result": "It topples by month's end."}}]}}},
    "mailbox_smashed": {"title": "Smashed Mailbox", "icon": "📪", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 14}, "stages": {"start": {"text": "Someone knocked over the mailbox overnight — again.", "choices": [
        {"label": "Install a sturdy new one ($90)", "cost": {"cash": 90}, "outcome": {"condition": 3, "morale": 5, "resolve": True, "result": "Reinforced and standing tall."}},
        {"label": "Cheap replacement ($25)", "cost": {"cash": 25}, "outcome": {"condition": 1, "resolve": True, "result": "Functional, if flimsy."}},
        {"label": "Tell them to prop it back up", "outcome": {"morale": -3, "resolve": True, "result": "The mail piles up at the curb."}}]}}},
    "smart_lock": {"title": "Smart Lock Request", "icon": "🔐", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} asks if they can swap the deadbolt for a keypad smart lock.", "choices": [
        {"label": "Install one yourself ($120)", "cost": {"cash": 120}, "outcome": {"condition": 4, "loyalty": 8, "morale": 8, "resolve": True, "result": "A nice upgrade that adds value too."}},
        {"label": "They can, if you keep a code", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "Convenient and secure for you both."}},
        {"label": "Keep the original lock", "outcome": {"morale": -3, "resolve": True, "result": "They fumble for keys, mildly annoyed."}}]}}},
    "ev_charger": {"title": "EV Charger", "icon": "🔋", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 28}, "stages": {"start": {"text": "{name} bought an electric car and wants a charger installed in the driveway.", "choices": [
        {"label": "Install it ($500) and bump rent (+3%)", "cost": {"cash": 500}, "outcome": {"condition": 6, "rent_mult": 1.03, "loyalty": 10, "resolve": True, "result": "A modern amenity that pays for itself."}},
        {"label": "Split the cost with them ($200)", "cost": {"cash": 200}, "outcome": {"condition": 5, "loyalty": 8, "morale": 8, "resolve": True, "result": "A fair partnership."}},
        {"label": "They use a public charger", "outcome": {"morale": -3, "resolve": True, "result": "Inconvenient, but they cope."}}]}}},
    "solar_panels": {"title": "Going Solar", "icon": "☀️", "trigger": {"weight": 3, "cooldown_days": 130, "min_days_resident": 30}, "stages": {"start": {"text": "{name} suggests adding solar panels — they'd love lower bills and so would the planet.", "choices": [
        {"label": "Invest in panels ($900), raise rent (+4%)", "cost": {"cash": 900}, "outcome": {"condition": 10, "rent_mult": 1.04, "loyalty": 10, "resolve": True, "result": "Greener, cheaper to run, and worth more."}},
        {"label": "Look into a lease-to-own program", "outcome": {"morale": 6, "resolve": True, "result": "A maybe that keeps the door open."}},
        {"label": "Not in the budget", "outcome": {"morale": -2, "resolve": True, "result": "They understand."}}]}}},
    "chimney_sweep": {"title": "The Chimney", "icon": "🧹", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name} wants to use the fireplace, but it hasn't been swept in years.", "choices": [
        {"label": "Hire a sweep and inspect ($160)", "cost": {"cash": 160}, "outcome": {"condition": 5, "morale": 8, "resolve": True, "result": "Safe, clean, and cozy for winter."}},
        {"label": "Cap it off, no fires", "outcome": {"morale": -2, "resolve": True, "result": "Safe, if less charming."}},
        {"label": "Let them light it up", "outcome": {"goto": "chimney_risk", "delay": 8, "result": "You take their word it's fine."}}]},
        "chimney_risk": {"auto": True, "roll": [{"weight": 70, "text": "All was well — cozy fires all season.", "outcome": {"morale": 6, "resolve": True}}, {"weight": 30, "text": "A small chimney fire scorched the flue. Lesson learned.", "outcome": {"condition": -10, "morale": -5, "resolve": True}}]}}},
    "foundation_settle": {"title": "Settling Cracks", "icon": "🧱", "trigger": {"weight": 3, "cooldown_days": 120, "min_days_resident": 30, "max_condition": 65}, "stages": {"start": {"text": "Hairline cracks are spidering up a wall — could be settling, could be more.", "choices": [
        {"label": "Get it assessed and stabilized ($700)", "cost": {"cash": 700}, "outcome": {"condition": 14, "morale": 8, "resolve": True, "result": "Caught early. Stabilized and patched."}},
        {"label": "Patch the cracks cosmetically ($100)", "cost": {"cash": 100}, "outcome": {"condition": 3, "resolve": True, "result": "Looks better; the cause remains."}},
        {"label": "Probably nothing", "outcome": {"condition": -6, "resolve": True, "result": "The cracks widen over time."}}]}}},
    "window_crack": {"title": "Cracked Window", "icon": "🪟", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 14}, "stages": {"start": {"text": "A window cracked across the pane and lets in a draft.", "choices": [
        {"label": "Replace with double-pane ($220)", "cost": {"cash": 220}, "outcome": {"condition": 7, "morale": 6, "resolve": True, "result": "Quieter, warmer, better."}},
        {"label": "Patch and tape for now ($20)", "cost": {"cash": 20}, "outcome": {"condition": 1, "morale": -1, "resolve": True, "result": "Holds the draft back, barely."}},
        {"label": "It's just cosmetic", "outcome": {"condition": -3, "morale": -4, "resolve": True, "result": "The draft drives up their heating bill."}}]}}},
    "garage_door": {"title": "Stuck Garage Door", "icon": "🚙", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "The garage door opener gave out with the car trapped inside.", "choices": [
        {"label": "New opener + tune-up ($240)", "cost": {"cash": 240}, "outcome": {"condition": 6, "morale": 8, "resolve": True, "result": "Smooth and quiet again."}},
        {"label": "Repair the old motor ($90)", "cost": {"cash": 90}, "outcome": {"condition": 2, "resolve": True, "result": "Working, for now."}},
        {"label": "They can lift it manually", "outcome": {"morale": -4, "resolve": True, "result": "A daily workout they didn't ask for."}}]}}},
    "sump_pump": {"title": "The Sump Pump", "icon": "💧", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "With the rainy season coming, {name} worries the basement sump pump is on its last legs.", "choices": [
        {"label": "Replace it now ($300)", "cost": {"cash": 300}, "outcome": {"condition": 8, "morale": 8, "resolve": True, "result": "Peace of mind before the rains."}},
        {"label": "Service the existing one ($80)", "cost": {"cash": 80}, "outcome": {"condition": 3, "resolve": True, "result": "Should hold the season."}},
        {"label": "Wait and see", "outcome": {"goto": "sump_risk", "delay": 14, "result": "You roll the dice on the weather."}}]},
        "sump_risk": {"auto": True, "roll": [{"weight": 55, "text": "Dry season — the old pump held.", "outcome": {"morale": 2, "resolve": True}}, {"weight": 45, "text": "It failed during a downpour and the basement flooded.", "outcome": {"condition": -12, "morale": -8, "resolve": True}}]}}},
    # ── Batch 7C: money & lease (round 2) ───────────────────────────────────────
    "rent_comparison": {"title": "The Neighbor Pays Less", "icon": "⚖️", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 28}, "stages": {"start": {"text": "{name} found out a neighbor pays less and feels a little cheated.", "choices": [
        {"label": "Explain the difference fairly", "outcome": {"morale": 4, "resolve": True, "result": "Context they can accept."}},
        {"label": "Match it to keep them happy (-3%)", "outcome": {"rent_mult": 0.97, "loyalty": 8, "morale": 8, "resolve": True, "result": "Goodwill bought cheaply."}},
        {"label": "Rates are rates", "outcome": {"morale": -5, "resolve": True, "result": "They grumble about it for weeks."}}]}}},
    "cosigner_request": {"title": "A Co-Signer", "icon": "✍️", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name} wants to add a co-signer to strengthen the lease and lower their deposit.", "choices": [
        {"label": "Approve and reduce the deposit", "outcome": {"loyalty": 8, "morale": 6, "resolve": True, "result": "A fair, lower-risk arrangement."}},
        {"label": "Approve, deposit unchanged", "outcome": {"morale": 3, "resolve": True, "result": "They're satisfied enough."}},
        {"label": "No co-signers on your leases", "outcome": {"morale": -3, "resolve": True, "result": "A rigid no."}}]}}},
    "pet_rent": {"title": "Pet Rent Talk", "icon": "🐾", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "You're considering adding a small monthly pet fee for {name}'s well-behaved cat.", "choices": [
        {"label": "Add modest pet rent (+3%)", "outcome": {"rent_mult": 1.03, "morale": -4, "resolve": True, "result": "Standard practice; they accept it."}},
        {"label": "One-time pet fee instead ($120)", "outcome": {"cash": 120, "morale": -1, "resolve": True, "result": "A cleaner deal they prefer."}},
        {"label": "Waive it — the cat's an angel", "outcome": {"loyalty": 8, "morale": 8, "resolve": True, "result": "They love you for it."}}]}}},
    "parking_fee": {"title": "The Second Spot", "icon": "🅿️", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} wants a second parking space for their other vehicle.", "choices": [
        {"label": "Rent them the extra spot (+$60/mo)", "outcome": {"cash": 60, "rent_mult": 1.02, "resolve": True, "result": "Found money from unused space."}},
        {"label": "Include it as a perk", "outcome": {"loyalty": 8, "morale": 6, "resolve": True, "result": "A generous freebie."}},
        {"label": "Only one spot per unit", "outcome": {"morale": -3, "resolve": True, "result": "They park the second car on the street."}}]}}},
    "storage_request": {"title": "Storage Space", "icon": "📦", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} asks to use part of the garage or basement for extra storage.", "choices": [
        {"label": "Rent the space (+$40/mo)", "outcome": {"cash": 40, "rent_mult": 1.015, "resolve": True, "result": "A little extra income."}},
        {"label": "Let them use it, no charge", "outcome": {"loyalty": 6, "morale": 6, "resolve": True, "result": "A small kindness."}},
        {"label": "Keep those areas clear", "outcome": {"morale": -2, "resolve": True, "result": "They rent a unit across town."}}]}}},
    "lease_transfer": {"title": "Lease Transfer", "icon": "🔁", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 28}, "stages": {
        "start": {"text": "{name} has to move and wants to transfer the lease to a friend instead of breaking it.", "choices": [
            {"label": "Approve, pending screening", "outcome": {"goto": "transfer_screen", "delay": 6, "result": "You vet the replacement."}},
            {"label": "Charge a transfer fee ($150)", "outcome": {"cash": 150, "resolve": True, "result": "Standard processing; they pay it."}},
            {"label": "They must break the lease normally", "outcome": {"morale": -5, "resolve": True, "result": "A costlier path for them."}}]},
        "transfer_screen": {"auto": True, "roll": [{"weight": 75, "text": "The friend checked out great. Smooth handoff.", "outcome": {"loyalty": 6, "resolve": True, "leave": True}}, {"weight": 25, "text": "The friend didn't qualify; {name} broke the lease after all.", "outcome": {"cash": 300, "resolve": True, "leave": True}}]}}},
    "app_glitch": {"title": "Payment App Glitch", "icon": "📱", "trigger": {"weight": 3, "cooldown_days": 70, "min_days_resident": 14}, "stages": {"start": {"text": "The rent app double-charged {name} and they're (rightly) frustrated.", "choices": [
        {"label": "Refund immediately, apologize", "outcome": {"cash": -0, "morale": 8, "loyalty": 6, "resolve": True, "result": "Handled fast; trust intact."}},
        {"label": "Credit it to next month", "outcome": {"morale": 4, "resolve": True, "result": "Resolved, if a little slowly."}},
        {"label": "Tell them to dispute it with the app", "outcome": {"morale": -6, "resolve": True, "result": "They feel brushed off."}}]}}},
    "voucher_program": {"title": "The Housing Voucher", "icon": "🎫", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 21}, "stages": {"start": {"text": "{name} qualifies for a housing assistance voucher and asks if you'll accept it.", "choices": [
        {"label": "Accept it — guaranteed portion", "outcome": {"pay_chance": 0.05, "loyalty": 10, "morale": 10, "resolve": True, "result": "Steadier payments and a grateful tenant."}},
        {"label": "Accept, with the paperwork", "outcome": {"pay_chance": 0.03, "morale": 6, "resolve": True, "result": "A bit of admin, but worth it."}},
        {"label": "Decline the program", "outcome": {"morale": -8, "resolve": True, "result": "A hard blow for them."}}]}}},
    "guarantor_issue": {"title": "The Guarantor Falls Through", "icon": "📋", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 21}, "stages": {"start": {"text": "{name}'s guarantor backed out and they're scrambling to reassure you.", "choices": [
        {"label": "Accept a larger deposit instead ($300)", "outcome": {"cash": 300, "morale": 4, "resolve": True, "result": "Risk covered; everyone's comfortable."}},
        {"label": "Trust their track record", "outcome": {"loyalty": 10, "morale": 8, "resolve": True, "result": "A vote of confidence they'll honor."}},
        {"label": "No guarantor, no lease renewal", "outcome": {"morale": -8, "resolve": True, "result": "A tense standoff."}}]}}},
    "rate_lock": {"title": "Lock My Rate", "icon": "🔒", "trigger": {"weight": 4, "cooldown_days": 100, "min_days_resident": 28, "min_morale": 55}, "stages": {"start": {"text": "{name} asks you to lock their rent for two years, worried about rising rates.", "choices": [
        {"label": "Lock it — slight bump now (+2%)", "outcome": {"rent_mult": 1.02, "loyalty": 14, "morale": 8, "resolve": True, "result": "Predictability for you both."}},
        {"label": "Lock it at the current rate", "outcome": {"loyalty": 12, "morale": 10, "resolve": True, "result": "They breathe a sigh of relief."}},
        {"label": "Keep it year-to-year", "outcome": {"morale": -3, "resolve": True, "result": "They worry, but stay."}}]}}},
    # ── Batch 7D: quirky (round 2) ──────────────────────────────────────────────
    "the_drone": {"title": "Drone Pilot", "icon": "🛸", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} has taken up drone racing and is launching from the backyard at all hours.", "choices": [
        {"label": "Set sensible flight hours", "outcome": {"morale": 4, "resolve": True, "result": "A fair compromise with the neighbors."}},
        {"label": "Ask them to use the park", "outcome": {"morale": 2, "resolve": True, "result": "They relocate the hobby."}},
        {"label": "No drones over the property", "outcome": {"morale": -4, "resolve": True, "result": "Grounded, and grumpy about it."}}]}}},
    "model_trains": {"title": "The Train Room", "icon": "🚂", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 30}, "stages": {"start": {"text": "{name} has built an elaborate model railroad that now occupies the entire spare room.", "choices": [
        {"label": "Marvel at it — totally fine", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "A masterpiece. They give you a guided tour."}},
        {"label": "No permanent fixtures to the walls", "outcome": {"morale": 2, "resolve": True, "result": "They keep it freestanding."}},
        {"label": "That's a lot of room for trains", "outcome": {"morale": -2, "resolve": True, "result": "They take the comment in stride."}}]}}},
    "reptile_room": {"title": "The Reptile Collection", "icon": "🦎", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 30}, "stages": {"start": {"text": "{name} keeps a growing collection of reptiles — heat lamps, terrariums, the works.", "choices": [
        {"label": "Fine, with safe wiring", "outcome": {"morale": 6, "loyalty": 4, "resolve": True, "result": "The geckos are, admittedly, charming."}},
        {"label": "Cap the number of tanks", "outcome": {"morale": 2, "resolve": True, "result": "A reasonable limit."}},
        {"label": "Worried about the wiring load", "outcome": {"morale": -3, "resolve": True, "result": "They scale back the heat lamps."}}]}}},
    "ham_radio": {"title": "The Radio Tower", "icon": "📡", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 30}, "stages": {"start": {"text": "{name}, a ham radio enthusiast, wants to erect an antenna tower in the yard.", "choices": [
        {"label": "Approve a modest mast", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "They talk to Japan from the backyard. Delighted."}},
        {"label": "Roof-mounted antenna only", "outcome": {"morale": 4, "resolve": True, "result": "A tidy compromise."}},
        {"label": "No towers, sorry", "outcome": {"morale": -4, "resolve": True, "result": "They settle for a smaller setup."}}]}}},
    "indoor_trampoline": {"title": "Indoor Trampoline", "icon": "🤸", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} installed a full-size trampoline. Indoors. In the living room.", "choices": [
        {"label": "Honestly, why not", "outcome": {"morale": 8, "loyalty": 4, "resolve": True, "result": "The downstairs neighbor has thoughts, but okay."}},
        {"label": "Backyard only", "outcome": {"morale": 2, "resolve": True, "result": "A safer arrangement."}},
        {"label": "Picture the ceiling below. No.", "outcome": {"morale": -3, "resolve": True, "result": "Deflated, literally."}}]}}},
    "sourdough_empire": {"title": "The Sourdough Empire", "icon": "🍞", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21}, "stages": {"start": {"text": "{name} runs a small sourdough business from the kitchen. The whole block smells amazing.", "choices": [
        {"label": "Allow it — and accept a loaf", "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "Best bread you've ever had. Worth it."}},
        {"label": "Light home-business bump (+4%)", "outcome": {"rent_mult": 1.04, "morale": 2, "resolve": True, "result": "Above board, and you still get bread."}},
        {"label": "No commercial baking", "outcome": {"morale": -6, "resolve": True, "result": "The ovens cool. The block mourns."}}]}}},
    "mannequin_collection": {"title": "The Mannequins", "icon": "🧍", "trigger": {"weight": 3, "cooldown_days": 100, "min_days_resident": 30}, "stages": {"start": {"text": "During a visit you notice {name} collects vintage mannequins. Dozens of them. Watching.", "choices": [
        {"label": "To each their own", "outcome": {"morale": 6, "resolve": True, "result": "Unsettling, but harmless."}},
        {"label": "Maybe fewer by the window?", "outcome": {"morale": 2, "resolve": True, "result": "The neighbors will sleep easier."}},
        {"label": "Politely note it's a bit much", "outcome": {"morale": -3, "resolve": True, "result": "They're a little hurt on the mannequins' behalf."}}]}}},
    "vintage_arcade": {"title": "The Home Arcade", "icon": "🕹️", "trigger": {"weight": 3, "cooldown_days": 90, "min_days_resident": 21, "traits": ["rowdy"]}, "stages": {"start": {"text": "{name} filled the basement with vintage arcade cabinets and hosts game nights.", "choices": [
        {"label": "Amazing — keep it down past 11", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "You're invited to the next tournament."}},
        {"label": "Mind the electrical load", "outcome": {"morale": 4, "resolve": True, "result": "They add a dedicated circuit."}},
        {"label": "Game nights are getting loud", "outcome": {"morale": -4, "resolve": True, "result": "They dial it back, reluctantly."}}]}}},
    "the_llama": {"title": "The Llama", "icon": "🦙", "trigger": {"weight": 2, "cooldown_days": 120, "min_days_resident": 45}, "stages": {"start": {"text": "{name} would like to keep a llama in the backyard. As a pet. Named Gerald.", "choices": [
        {"label": "...Okay. One llama.", "outcome": {"morale": 10, "loyalty": 6, "resolve": True, "result": "Gerald becomes the neighborhood mascot."}},
        {"label": "Check the zoning first", "outcome": {"goto": "llama_zone", "delay": 6, "result": "You make a call to the city."}},
        {"label": "Absolutely not a llama", "outcome": {"morale": -5, "resolve": True, "result": "Gerald goes to a farm. A real one."}}]},
        "llama_zone": {"auto": True, "roll": [{"weight": 50, "text": "Zoning allows it! Gerald moves in.", "outcome": {"morale": 8, "loyalty": 6, "resolve": True}}, {"weight": 50, "text": "Zoning says no livestock. Gerald is heartbroken.", "outcome": {"morale": -3, "resolve": True}}]}}},
    "snake_escape": {"title": "The Escaped Snake", "icon": "🐍", "trigger": {"weight": 2, "cooldown_days": 110, "min_days_resident": 30}, "stages": {
        "start": {"text": "{name} sheepishly admits their pet snake has... gotten loose. Somewhere in the unit.", "choices": [
            {"label": "Hire a pro to find it ($150)", "cost": {"cash": 150}, "outcome": {"morale": 8, "loyalty": 8, "resolve": True, "result": "Found behind the water heater. Crisis averted."}},
            {"label": "Give them 48 hours to find it", "outcome": {"goto": "snake_hunt", "delay": 3, "result": "You wait, nervously."}},
            {"label": "No more snakes after this", "outcome": {"morale": -2, "resolve": True, "result": "They agree, still searching."}}]},
        "snake_hunt": {"auto": True, "roll": [{"weight": 75, "text": "They found it curled up in a boot. All's well.", "outcome": {"morale": 4, "resolve": True}}, {"weight": 25, "text": "Still missing. The downstairs neighbor is NOT pleased.", "outcome": {"morale": -8, "resolve": True}}]}}},
    "giant_pumpkin": {"title": "The Giant Pumpkin", "icon": "🎃", "trigger": {"weight": 2, "cooldown_days": 300, "min_days_resident": 30, "season": 2}, "stages": {"start": {"text": "{name} is growing a county-fair giant pumpkin that's slowly eating the entire backyard.", "choices": [
        {"label": "Root for it!", "outcome": {"morale": 8, "loyalty": 6, "resolve": True, "result": "It takes second place. A backyard legend."}},
        {"label": "Just keep it off the fence", "outcome": {"morale": 4, "resolve": True, "result": "Contained, mostly."}},
        {"label": "That's a lot of lawn gone", "outcome": {"morale": -2, "resolve": True, "result": "They promise to reseed after harvest."}}]}}},
    "taxidermy_hobby": {"title": "The Taxidermy Hobby", "icon": "🦌", "trigger": {"weight": 2, "cooldown_days": 110, "min_days_resident": 30}, "stages": {"start": {"text": "{name} has picked up taxidermy and the living room is becoming a small natural history museum.", "choices": [
        {"label": "Fascinating, carry on", "outcome": {"morale": 6, "resolve": True, "result": "Surprisingly tasteful, actually."}},
        {"label": "Ask about ventilation and chemicals", "outcome": {"morale": 3, "resolve": True, "result": "Good call — they set up a proper workspace."}},
        {"label": "Keep it to one room", "outcome": {"morale": -2, "resolve": True, "result": "The owl stays in the den."}}]}}},
    "pipe_organ": {"title": "The Pipe Organ", "icon": "🎹", "trigger": {"weight": 2, "cooldown_days": 120, "min_days_resident": 30, "traits": ["creative"]}, "stages": {"start": {"text": "{name} acquired a secondhand pipe organ and wants to install it in the living room.", "choices": [
        {"label": "Approve it (it's magnificent)", "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "Sunday recitals become a neighborhood event."}},
        {"label": "Soundproof first ($200)", "cost": {"cash": 200}, "outcome": {"condition": 4, "morale": 8, "resolve": True, "result": "Glorious, and the neighbors can still sleep."}},
        {"label": "Too big, too loud", "outcome": {"morale": -5, "resolve": True, "result": "They get a keyboard instead, deflated."}}]}}},
    "backyard_zipline": {"title": "The Zipline", "icon": "🪢", "trigger": {"weight": 2, "cooldown_days": 110, "min_days_resident": 30}, "stages": {"start": {"text": "{name} wants to string a zipline between two backyard trees for the kids.", "choices": [
        {"label": "Approve with a safety inspection ($80)", "cost": {"cash": 80}, "outcome": {"morale": 10, "loyalty": 6, "resolve": True, "result": "The most popular backyard on the block."}},
        {"label": "Low and short only", "outcome": {"morale": 4, "resolve": True, "result": "Safe thrills for the little ones."}},
        {"label": "Too much liability", "outcome": {"morale": -4, "resolve": True, "result": "The trees remain zipline-free."}}]}}},
    # ── Batch 7E: trait depth (round 3) ─────────────────────────────────────────
    "early_bird": {"title": "Months Ahead", "icon": "🐦", "trigger": {"weight": 4, "cooldown_days": 100, "min_days_resident": 30, "traits": ["reliable"]}, "stages": {"start": {"text": "{name} offers to pay several months of rent in advance, just because they can.", "choices": [
        {"label": "Gladly accept (+$1,200)", "outcome": {"cash": 1200, "loyalty": 10, "resolve": True, "result": "Cash flow and a rock-solid tenant."}},
        {"label": "Accept, knock off a little (-2%)", "outcome": {"cash": 1100, "rent_mult": 0.98, "loyalty": 14, "resolve": True, "result": "A small thank-you they appreciate."}},
        {"label": "Monthly's fine, thanks", "outcome": {"morale": 4, "resolve": True, "result": "No pressure either way."}}]}}},
    "workshop_request": {"title": "The Workshop", "icon": "🛠️", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["handy"]}, "stages": {"start": {"text": "{name} wants to set up a proper workshop in the garage — and offers to fix things around the place in exchange.", "choices": [
        {"label": "Deal — they maintain, you supply ($100)", "cost": {"cash": 100}, "outcome": {"condition": 12, "loyalty": 14, "morale": 10, "resolve": True, "result": "Your handiest tenant becomes your unofficial super."}},
        {"label": "Sure, just keep it safe", "outcome": {"condition": 6, "loyalty": 8, "morale": 8, "resolve": True, "result": "Half the small repairs vanish from your list."}},
        {"label": "Garage stays for cars", "outcome": {"morale": -4, "resolve": True, "result": "A missed opportunity, honestly."}}]}}},
    "veggie_stand": {"title": "The Veggie Stand", "icon": "🥕", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["green_thumb"]}, "stages": {"start": {"text": "{name}'s garden is so productive they want to sell the surplus from a little front-yard stand.", "choices": [
        {"label": "Charming — go for it", "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "The block loves it. So do the property photos."}},
        {"label": "Fine, keep it tidy and weekends-only", "outcome": {"morale": 6, "resolve": True, "result": "A reasonable arrangement."}},
        {"label": "No commerce out front", "outcome": {"morale": -4, "resolve": True, "result": "They give the veggies away instead."}}]}}},
    "quiet_bothered": {"title": "The Quiet One Speaks Up", "icon": "🤫", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["quiet"]}, "stages": {"start": {"text": "Your most low-key tenant rarely complains — so when {name} mentions the upstairs noise, you know it's real.", "choices": [
        {"label": "Address it with the neighbor", "outcome": {"morale": 10, "loyalty": 12, "resolve": True, "result": "They're relieved you took them seriously."}},
        {"label": "Offer them earplugs and sympathy", "outcome": {"morale": 2, "resolve": True, "result": "A weak response they quietly note."}},
        {"label": "Tell them it's just apartment living", "outcome": {"morale": -8, "loyalty": -6, "resolve": True, "result": "A rare tenant, taken for granted."}}]}}},
    "game_day": {"title": "The Big Game", "icon": "🏈", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21, "traits": ["rowdy"]}, "stages": {"start": {"text": "{name} is hosting a huge game-day party and the guest list keeps growing.", "choices": [
        {"label": "Have fun — just no fireworks", "outcome": {"morale": 8, "loyalty": 4, "resolve": True, "result": "A blowout, but it stays in bounds."}},
        {"label": "Cap the guest count", "outcome": {"morale": 2, "resolve": True, "result": "A sensible limit they accept."}},
        {"label": "Not this time", "outcome": {"morale": -6, "resolve": True, "result": "They watch the game elsewhere, sulking."}}]}}},
    "carpool_lot": {"title": "The Family Fleet", "icon": "🚐", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["big_family"]}, "stages": {"start": {"text": "Between teen drivers and a minivan, {name}'s family has more cars than parking.", "choices": [
        {"label": "Add a gravel parking pad ($300)", "cost": {"cash": 300}, "outcome": {"condition": 4, "loyalty": 12, "morale": 10, "resolve": True, "result": "Problem solved, and the property gains a spot."}},
        {"label": "Assign street-permit parking", "outcome": {"morale": 4, "resolve": True, "result": "A workable fix."}},
        {"label": "They'll have to figure it out", "outcome": {"morale": -4, "resolve": True, "result": "The driveway becomes a daily puzzle."}}]}}},
    "gallery_night": {"title": "Gallery Night", "icon": "🖼️", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["creative"]}, "stages": {"start": {"text": "{name} wants to host a one-night art show at the unit to sell their work.", "choices": [
        {"label": "Wonderful — happy to host", "outcome": {"morale": 10, "loyalty": 8, "resolve": True, "result": "A lovely evening. The place looks gorgeous in the listing photos after."}},
        {"label": "Yes, with a cleanup deposit ($100)", "outcome": {"cash": 100, "morale": 6, "resolve": True, "result": "A fair safeguard they accept."}},
        {"label": "No public events", "outcome": {"morale": -5, "resolve": True, "result": "They host it at a friend's instead."}}]}}},
    "delivery_overload": {"title": "Package Mountain", "icon": "📬", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21, "traits": ["homebody"]}, "stages": {"start": {"text": "{name} rarely leaves home, so deliveries pile up daily at the entrance.", "choices": [
        {"label": "Install a parcel drop box ($110)", "cost": {"cash": 110}, "outcome": {"condition": 3, "morale": 8, "loyalty": 6, "resolve": True, "result": "Tidy entryway, happy homebody."}},
        {"label": "Ask them to clear it daily", "outcome": {"morale": 2, "resolve": True, "result": "They're better about it now."}},
        {"label": "It's becoming a hazard", "outcome": {"morale": -4, "resolve": True, "result": "They take it personally."}}]}}},
    "thermostat_war": {"title": "The Thermostat War", "icon": "🌡️", "trigger": {"weight": 4, "cooldown_days": 90, "min_days_resident": 30, "traits": ["penny"]}, "stages": {
        "start": {"text": "To save money, {name} keeps the heat off entirely — even as pipes get dangerously cold.", "choices": [
            {"label": "Explain the frozen-pipe risk kindly", "outcome": {"morale": 4, "resolve": True, "result": "They set a sensible minimum. Crisis avoided."}},
            {"label": "Include a heat minimum in the lease", "outcome": {"morale": -3, "resolve": True, "result": "Enforced, if grudgingly accepted."}},
            {"label": "Let them save their pennies", "outcome": {"goto": "pipe_freeze", "delay": 10, "result": "You leave it to them."}}]},
        "pipe_freeze": {"auto": True, "roll": [{"weight": 55, "text": "Mild winter — the pipes held.", "outcome": {"morale": 2, "resolve": True}}, {"weight": 45, "text": "A pipe froze and burst. Expensive lesson.", "outcome": {"condition": -12, "cash": -200, "morale": -6, "resolve": True}}]}}},
    "listed_again": {"title": "Listed Again", "icon": "🛏️", "trigger": {"weight": 4, "cooldown_days": 80, "min_days_resident": 21, "traits": ["subletter"]}, "stages": {
        "start": {"text": "You spot the unit back up on a short-term rental site, despite the last conversation.", "choices": [
            {"label": "Final warning, in writing", "outcome": {"morale": -4, "pay_chance": 0.0, "resolve": True, "result": "They take it down. This time you mean it."}},
            {"label": "Charge a penalty ($250)", "outcome": {"cash": 250, "morale": -8, "resolve": True, "result": "An expensive habit to break."}},
            {"label": "Strike a revenue-share deal", "outcome": {"goto": "share_result", "delay": 10, "result": "If you can't beat them..."}}]},
        "share_result": {"auto": True, "roll": [{"weight": 60, "text": "The arrangement worked — steady extra income, kept clean.", "outcome": {"cash": 300, "loyalty": 6, "resolve": True}}, {"weight": 40, "text": "Guests trashed the place one weekend. Deal's off.", "outcome": {"condition": -10, "morale": -4, "resolve": True}}]}}},
    "the_fixer_pitch": {"title": "Let Me Renovate", "icon": "🔨", "trigger": {"weight": 3, "cooldown_days": 110, "min_days_resident": 45, "traits": ["handy"]}, "stages": {"start": {"text": "{name} pitches a full bathroom remodel they'd do themselves, for materials plus a rent break.", "choices": [
        {"label": "Fund materials ($400), comp two weeks", "cost": {"cash": 400}, "outcome": {"condition": 22, "loyalty": 16, "morale": 12, "resolve": True, "result": "A stunning remodel at a fraction of contractor cost."}},
        {"label": "Materials only, no rent break ($400)", "cost": {"cash": 400}, "outcome": {"condition": 18, "loyalty": 8, "resolve": True, "result": "Great work; they'd have liked the discount."}},
        {"label": "Leave renovations to the pros", "outcome": {"morale": -3, "resolve": True, "result": "They respect the call, mostly."}}]}}},
    "memory_lane": {"title": "Down Memory Lane", "icon": "📷", "trigger": {"weight": 3, "cooldown_days": 150, "min_days_resident": 90, "traits": ["reliable"], "min_morale": 55}, "stages": {"start": {"text": "{name} reflects on how many years they've been here and how much the place means to them.", "choices": [
        {"label": "Frame a thank-you for the wall ($40)", "cost": {"cash": 40}, "outcome": {"loyalty": 16, "morale": 14, "resolve": True, "result": "A small gesture that means the world to them."}},
        {"label": "Reminisce together warmly", "outcome": {"loyalty": 10, "morale": 10, "resolve": True, "result": "A genuine moment between landlord and tenant."}},
        {"label": "Nice — anyway, about renewal", "outcome": {"morale": -3, "resolve": True, "result": "The moment passes, a little awkwardly."}}]}}},
}

def _fmt_sl(txt, t, prop):
    return (txt or "").replace("{name}", t.get("name", "Your tenant")) \
                      .replace("{prop}", f"{prop['type']} — {prop['neighborhood']}")

def _storylet_eligible(sl, t, prop, season_idx, current_day):
    tr = sl["trigger"]
    # Special-tenant gating: storylets with a "special" key fire ONLY for that
    # special tenant; storylets without one never fire for special tenants.
    sp = tr.get("special")
    if sp:
        if not t.get(sp):
            return False
    elif _is_special_tenant(t):
        return False
    if t.get("days_resident", 0) < tr.get("min_days_resident", 0):
        return False
    m = t.get("morale", 50)
    if m < tr.get("min_morale", 0) or m > tr.get("max_morale", 100):
        return False
    c = prop.get("condition", 0)
    if c < tr.get("min_condition", 0) or c > tr.get("max_condition", MAX_CONDITION):
        return False
    if "traits" in tr and t.get("trait") not in tr["traits"]:
        return False
    if t.get("trait") in tr.get("exclude_traits", []):
        return False
    if "season" in tr and season_idx != tr["season"]:
        return False
    return True

def _storylet_leave(s, prop, t, current_day):
    for flag, ckey, mult in (("is_phil", "phil_cooldown_until", 4), ("is_baileys", "baileys_cooldown_until", 2),
                              ("is_goldbergs", "goldbergs_cooldown_until", 2), ("is_mystery", "mystery_cooldown_until", 2)):
        if t.get(flag): s[ckey] = current_day + DAYS_PER_SEASON * mult
    prop["tenant"]       = None
    prop["vacant_since"] = current_day

def _apply_storylet_outcome(s, prop, t, outcome, current_day):
    """Apply an outcome. Returns True only if the storylet should keep processing now."""
    if outcome.get("morale"):
        t["morale"] = max(0, min(100, t.get("morale", 50) + outcome["morale"]))
    if outcome.get("loyalty"):
        t["loyalty"] = max(0, min(100, t.get("loyalty", 10) + outcome["loyalty"]))
    if outcome.get("condition"):
        prop["condition"] = max(0, min(MAX_CONDITION, prop.get("condition", 0) + outcome["condition"]))
    if outcome.get("cash"):
        s["cash"] += outcome["cash"]
    if outcome.get("rent_mult"):
        t["rent"] = max(1, int(round(t.get("rent", 0) * outcome["rent_mult"])))
    if outcome.get("pay_chance"):
        t["pay_chance"] = max(0.50, min(0.99, t.get("pay_chance", 0.9) + outcome["pay_chance"]))
    if outcome.get("damage_chance_add"):
        t["damage_chance"] = min(0.60, t.get("damage_chance", 0.10) + outcome["damage_chance_add"])
    for k, v in (outcome.get("flag") or {}).items():
        t[k] = v
    if outcome.get("leave"):
        _storylet_leave(s, prop, t, current_day)
        t.pop("storylet", None)
        return False
    if outcome.get("resolve"):
        t.pop("storylet", None)
        return False
    if "goto" in outcome:
        t["storylet"]["stage"]   = outcome["goto"]
        t["storylet"]["due_day"] = current_day + outcome.get("delay", 0)
        return outcome.get("delay", 0) == 0
    t.pop("storylet", None)
    return False

def _run_until_player(s, prop, t, current_day, recap):
    """Resolve auto stages until a choice stage (return its queued dict) or the storylet ends."""
    for _ in range(8):
        st = t.get("storylet")
        if not st or not prop.get("tenant"):
            return None
        if st.get("due_day", 9_999_999) > current_day:
            return None
        sl = STORYLETS.get(st["id"])
        if not sl:
            t.pop("storylet", None); return None
        stage = sl["stages"].get(st["stage"])
        if not stage:
            t.pop("storylet", None); return None
        if stage.get("auto"):
            rolls = stage["roll"]
            pick  = random.choices(rolls, weights=[r.get("weight", 1) for r in rolls], k=1)[0]
            recap.append({"prop": f"{prop['type']} — {prop['neighborhood']}",
                          "text": f"{sl['icon']} {_fmt_sl(pick['text'], t, prop)}", "type": "info"})
            if not _apply_storylet_outcome(s, prop, t, pick["outcome"], current_day):
                return None
        else:
            st["due_day"] = 9_999_999   # pause until the player responds
            return {
                "prop_id": prop["id"], "prop_name": f"{prop['type']} — {prop['neighborhood']}",
                "storylet_id": st["id"], "stage": st["stage"],
                "title": sl["title"], "icon": sl["icon"],
                "text": _fmt_sl(stage["text"], t, prop),
                "choices": [{"label": c["label"]} for c in stage["choices"]],
            }
    return None

def _storylet_tick(s, prop, t, current_day, events):
    """Progress this tenant's active storylet, or maybe start a new one. Returns a queued choice event or None."""
    st = t.get("storylet")
    if st:
        if st.get("due_day", 9_999_999) <= current_day:
            return _run_until_player(s, prop, t, current_day, events)
        return None
    if random.random() >= 0.015:   # ~1.5%/day to kick off a new storylet
        return None
    season_idx = _season_info(current_day)[0]
    cands = []
    for key, sl in STORYLETS.items():
        if not _storylet_eligible(sl, t, prop, season_idx, current_day):
            continue
        cd = sl["trigger"].get("cooldown_days", 56)
        if any(r["id"] == key and current_day - r["day"] < cd for r in t.get("recent_storylets", [])):
            continue
        cands.append((key, sl["trigger"].get("weight", 5)))
    if not cands:
        return None
    key = random.choices([k for k, _ in cands], weights=[w for _, w in cands], k=1)[0]
    t["storylet"] = {"id": key, "stage": "start", "due_day": current_day}
    t.setdefault("recent_storylets", []).append({"id": key, "day": current_day})
    t["recent_storylets"] = [r for r in t["recent_storylets"] if current_day - r["day"] < DAYS_PER_SEASON * 4]
    return _run_until_player(s, prop, t, current_day, events)

# ─────────────────────────────────────────────────────────────────────────────
# Milestones, Empire Score & Mogul Rank — endgame progression.
# Empire Score = total wealth + bonus per business owned + bonus per milestone done.
# Mogul Rank is a status ladder driven by Empire Score (never gates content).
# ─────────────────────────────────────────────────────────────────────────────
EMPIRE_BUSINESS_BONUS  = 2_000_000
EMPIRE_MILESTONE_BONUS =   500_000
CORE_RENO_KEYS = ["landscaping", "paint", "flooring", "windows", "bathrooms", "kitchen", "hvac", "roof"]

MOGUL_RANKS = [
    {"name": "Broke Nobody",             "icon": "🪣", "score": 0},
    {"name": "Squatter Wrangler",        "icon": "🔑", "score": 100_000},
    {"name": "Slumlord",                 "icon": "🏚️", "score": 500_000},
    {"name": "Landlord",                 "icon": "🏠", "score": 1_500_000},
    {"name": "Property Baron",           "icon": "🏢", "score": 5_000_000},
    {"name": "Business Mogul",           "icon": "💼", "score": 15_000_000},
    {"name": "Real Estate Tycoon",       "icon": "🏙️", "score": 40_000_000},
    {"name": "City Magnate",             "icon": "👑", "score": 100_000_000},
    {"name": "Empire Kingpin",           "icon": "🌆", "score": 250_000_000},
    {"name": "Owns the Whole Damn City", "icon": "🏆", "score": 500_000_000},
]

def _businesses_owned(s):
    n = 0
    if any(v.get("location_key") in VM_LOCATION_ORDER for v in s.get("vending_machines", [])): n += 1
    if (s.get("laundromat") or {}).get("owned"):  n += 1
    if (s.get("arcade") or {}).get("unlocked"):   n += 1
    if (s.get("pole_studio") or {}).get("owned"): n += 1
    if (s.get("car_wash") or {}).get("owned"):    n += 1
    if any(p.get("commercial") for p in s.get("properties", [])): n += 1
    return n

def _total_wealth(s):
    cash = s.get("cash", 0)
    res  = sum(calc_market_value(p) for p in s.get("properties", []) if not p.get("commercial"))
    comm = sum(p.get("purchase_price", 0) for p in s.get("properties", []) if p.get("commercial"))
    bank = _bank(s)
    sav  = bank.get("savings", 0)
    cds  = sum(c.get("principal", 0) for c in bank.get("cds", []))
    ss   = s.get("stocks") or {}
    prices = ss.get("prices", {})
    stk  = sum((h.get("shares", 0) if isinstance(h, dict) else h) * prices.get(tk, 0)
               for tk, h in (ss.get("portfolio") or {}).items())
    return int(cash + res + comm + sav + cds + stk)

def _empire_score(s):
    return (_total_wealth(s)
            + _businesses_owned(s) * EMPIRE_BUSINESS_BONUS
            + len(s.get("milestones_done", [])) * EMPIRE_MILESTONE_BONUS)

def _mogul_rank_index(score):
    idx = 0
    for i, r in enumerate(MOGUL_RANKS):
        if score >= r["score"]:
            idx = i
    return idx

def _vending_market_count(s):
    return len([v for v in s.get("vending_machines", []) if v.get("location_key") in VM_LOCATION_ORDER])
def _commercial_props(s):
    return [p for p in s.get("properties", []) if p.get("commercial")]
def _has_flooring_express(s):
    return any(u.get("business_type") == "flooring_express"
               for p in _commercial_props(s) for u in (p.get("units") or []))
def _empire_perfected(s):
    lm = s.get("laundromat") or {}; arc = s.get("arcade") or {}; ps = s.get("pole_studio") or {}; cw = s.get("car_wash") or {}
    return (_vending_market_count(s) >= 6
            and len(lm.get("machines") or []) >= LAUNDROMAT_MAX_MACHINES
            and len(arc.get("cabinets") or []) >= 8
            and (ps.get("slot_count") or 0) >= STUDIO_MAX_SLOTS
            and all((ps.get("staff") or {}).get(k) for k in POLE_STUDIO_STAFF)
            and (cw.get("bay_count") or 0) >= CAR_WASH_MAX_BAYS
            and all((cw.get("staff") or {}).get(k) for k in CAR_WASH_STAFF)
            and any(p.get("units") and all(u.get("business_type") for u in p["units"]) for p in _commercial_props(s)))

# Milestones are pure achievements — no cash reward; each adds to your Empire Score (and thus Mogul Rank).
MILESTONES = [
    # ── Getting started ──
    {"key": "sold_first",   "name": "Off the Streets",     "icon": "🔑", "desc": "Sell your starter property.",
     "check": lambda s: s.get("level", 0) >= 1},
    {"key": "first_tenant", "name": "Got a Tenant",        "icon": "🧑", "desc": "Place your first tenant.",
     "check": lambda s: any(p.get("tenant") for p in s.get("properties", []) if not p.get("commercial"))},
    {"key": "squatter",     "name": "Squatter Buster",     "icon": "🚪", "desc": "Deal with a squatter.",
     "check": lambda s: s.get("squatter_count", 0) >= 1},
    {"key": "full_reno",    "name": "The Flipper",         "icon": "🛠️", "desc": "Fully renovate a property (all 8 upgrades).",
     "check": lambda s: any(all((p.get("upgrades") or {}).get(k) for k in CORE_RENO_KEYS) for p in s.get("properties", []) if not p.get("commercial"))},
    {"key": "premium_up",   "name": "A Touch of Luxury",   "icon": "✨", "desc": "Add a premium upgrade to a property.",
     "check": lambda s: any(p.get("premium_upgrades") for p in s.get("properties", []) if not p.get("commercial"))},
    # ── Real estate empire ──
    {"key": "props_3",      "name": "Portfolio Builder",   "icon": "🏘️", "desc": "Own 3 properties at once.",
     "check": lambda s: len([p for p in s.get("properties", []) if not p.get("commercial")]) >= 3},
    {"key": "props_10",     "name": "Real Estate Machine", "icon": "🏙️", "desc": "Own 10 properties at once.",
     "check": lambda s: len([p for p in s.get("properties", []) if not p.get("commercial")]) >= 10},
    {"key": "props_25",     "name": "Property Tycoon",     "icon": "🌆", "desc": "Own 25 properties at once.",
     "check": lambda s: len([p for p in s.get("properties", []) if not p.get("commercial")]) >= 25},
    {"key": "mansion",      "name": "Living Large",        "icon": "🏰", "desc": "Move into the Mansion.",
     "check": lambda s: s.get("player_home") == "mansion"},
    # ── Businesses ──
    {"key": "first_biz",    "name": "Side Hustle",         "icon": "🥤", "desc": "Own your first business.",
     "check": lambda s: _businesses_owned(s) >= 1},
    {"key": "grandma",      "name": "Grandma's Got It",    "icon": "👵", "desc": "Hire Grandma to stock your vending machines.",
     "check": lambda s: bool(s.get("grandma_hired"))},
    {"key": "vending_6",    "name": "Vending Empire",      "icon": "🥫", "desc": "Own all 6 street vending machines.",
     "check": lambda s: _vending_market_count(s) >= 6},
    {"key": "three_biz",    "name": "Diversified",         "icon": "📊", "desc": "Own three different businesses.",
     "check": lambda s: _businesses_owned(s) >= 3},
    {"key": "laundro_max",  "name": "Spin to Win",         "icon": "🌀", "desc": "Run a fully-built laundromat (16 machines).",
     "check": lambda s: len((s.get("laundromat") or {}).get("machines") or []) >= LAUNDROMAT_MAX_MACHINES},
    {"key": "laundro_full", "name": "Full-Service Wash",   "icon": "🧺", "desc": "Install every laundromat add-on.",
     "check": lambda s: all(((s.get("laundromat") or {}).get("addons") or {}).get(k) for k in LAUNDROMAT_ADDONS)},
    {"key": "arcade_baron", "name": "Arcade Baron",        "icon": "🕹️", "desc": "Run 10 arcade cabinets.",
     "check": lambda s: len((s.get("arcade") or {}).get("cabinets") or []) >= 10},
    {"key": "pole_slots",   "name": "Full Schedule",       "icon": "🗓️", "desc": "Build all 8 studio class slots.",
     "check": lambda s: ((s.get("pole_studio") or {}).get("slot_count") or 0) >= STUDIO_MAX_SLOTS},
    {"key": "pole_dancers", "name": "Star-Studded Lineup", "icon": "💃", "desc": "Hire 5 studio instructors.",
     "check": lambda s: sum(1 for d in ((s.get("pole_studio") or {}).get("dancers") or {}).values() if (d or {}).get("hired")) >= 5},
    {"key": "pole_staff",   "name": "Fully Staffed Studio","icon": "📋", "desc": "Hire every studio employee.",
     "check": lambda s: all(((s.get("pole_studio") or {}).get("staff") or {}).get(k) for k in POLE_STUDIO_STAFF)},
    {"key": "cw_bays",      "name": "Five-Bay Operation",  "icon": "🚿", "desc": "Build all 5 car wash bays.",
     "check": lambda s: ((s.get("car_wash") or {}).get("bay_count") or 0) >= CAR_WASH_MAX_BAYS},
    {"key": "cw_staff",     "name": "The Whole Crew",      "icon": "🧽", "desc": "Hire every car wash employee.",
     "check": lambda s: all(((s.get("car_wash") or {}).get("staff") or {}).get(k) for k in CAR_WASH_STAFF)},
    {"key": "all_biz",      "name": "Business Tycoon",     "icon": "🏭", "desc": "Own all six businesses at once.",
     "check": lambda s: _businesses_owned(s) >= 6},
    # ── Commercial ──
    {"key": "commerce",     "name": "Commerce King",       "icon": "🏢", "desc": "Fully lease a commercial building.",
     "check": lambda s: any(p.get("units") and all(u.get("business_type") for u in p["units"]) for p in _commercial_props(s))},
    {"key": "flooring_exp", "name": "VIP Tenant",          "icon": "⭐", "desc": "Land Flooring Express as a tenant.",
     "check": _has_flooring_express},
    {"key": "comm_3",       "name": "Commercial Baron",    "icon": "🏬", "desc": "Own 3 commercial buildings.",
     "check": lambda s: len(_commercial_props(s)) >= 3},
    # ── Finance & delegation ──
    {"key": "investor",     "name": "Wall Street",         "icon": "📈", "desc": "Own shares of a stock.",
     "check": lambda s: any((h.get("shares", 0) if isinstance(h, dict) else h) > 0 for h in ((s.get("stocks") or {}).get("portfolio") or {}).values())},
    {"key": "banker",       "name": "Compound Interest",   "icon": "🏦", "desc": "Open a savings account or CD.",
     "check": lambda s: _bank(s).get("savings", 0) > 0 or len(_bank(s).get("cds", [])) > 0},
    {"key": "developer",    "name": "Developer",           "icon": "🏗️", "desc": "Buy a building permit.",
     "check": lambda s: bool(s.get("building_permit"))},
    {"key": "crew",         "name": "Got a Crew",          "icon": "👷", "desc": "Hire a construction crew.",
     "check": lambda s: len(s.get("owned_crews") or []) >= 1},
    {"key": "delegator",    "name": "Delegator",           "icon": "👔", "desc": "Hire an assistant.",
     "check": lambda s: any((s.get("assistants") or {}).values())},
    {"key": "all_assts",    "name": "Hands-Off Mogul",     "icon": "🤝", "desc": "Hire all three personal assistants.",
     "check": lambda s: all((s.get("assistants") or {}).get(k) for k in ("manager", "accountant", "leasing_agent"))},
    # ── Prestige ──
    {"key": "max_level",    "name": "Seasoned Pro",        "icon": "🎓", "desc": "Reach the maximum Level.",
     "check": lambda s: s.get("level", 0) >= MAX_LEVEL},
    {"key": "millionaire",  "name": "Millionaire",         "icon": "💰", "desc": "Reach $1,000,000 total wealth.",
     "check": lambda s: _total_wealth(s) >= 1_000_000},
    {"key": "eight_fig",    "name": "Eight Figures",       "icon": "💎", "desc": "Reach $10,000,000 total wealth.",
     "check": lambda s: _total_wealth(s) >= 10_000_000},
    {"key": "heavy_hitter", "name": "Heavy Hitter",        "icon": "🤑", "desc": "Reach $50,000,000 total wealth.",
     "check": lambda s: _total_wealth(s) >= 50_000_000},
    {"key": "nine_fig",     "name": "Nine Figures",        "icon": "🏆", "desc": "Reach $100,000,000 total wealth.",
     "check": lambda s: _total_wealth(s) >= 100_000_000},
    {"key": "empire_perf",  "name": "Empire Perfected",    "icon": "👑", "desc": "Max out every single business at once.",
     "check": _empire_perfected},
]

# One-time cash reward per milestone (small early, bigger for the hard ones).
MILESTONE_REWARD = {
    "sold_first": 2_000, "first_tenant": 3_000, "squatter": 5_000, "full_reno": 10_000, "premium_up": 8_000,
    "props_3": 5_000, "props_10": 25_000, "props_25": 75_000, "mansion": 50_000,
    "first_biz": 10_000, "grandma": 5_000, "vending_6": 20_000, "three_biz": 50_000,
    "laundro_max": 40_000, "laundro_full": 30_000, "arcade_baron": 40_000,
    "pole_slots": 30_000, "pole_dancers": 25_000, "pole_staff": 30_000,
    "cw_bays": 30_000, "cw_staff": 30_000, "all_biz": 250_000,
    "commerce": 100_000, "flooring_exp": 50_000, "comm_3": 150_000,
    "investor": 5_000, "banker": 5_000, "developer": 10_000, "crew": 10_000, "delegator": 5_000, "all_assts": 50_000,
    "max_level": 50_000, "millionaire": 25_000, "eight_fig": 100_000, "heavy_hitter": 500_000,
    "nine_fig": 1_000_000, "empire_perf": 1_000_000,
}

def _milestone_ok(m, s):
    try: return bool(m["check"](s))
    except Exception: return False

def _sync_milestones(s):
    """Mark any newly-completed milestones; return the list of newly-completed defs."""
    done  = s.setdefault("milestones_done", [])
    newly = []
    for m in MILESTONES:
        if m["key"] in done:
            continue
        if _milestone_ok(m, s):
            done.append(m["key"])
            newly.append(m)
            r = MILESTONE_REWARD.get(m["key"], 0)
            if r:
                s["cash"] += r
            s["log"].insert(0, {"day": s["day"], "type": "positive",
                "text": f"Milestone unlocked: {m['name']}" + (f" (+${r:,})" if r else "")})
    return newly

def _update_mogul_rank(s, events):
    new_idx = _mogul_rank_index(_empire_score(s))
    old_idx = s.get("mogul_rank", 0)
    if new_idx > old_idx:
        for i in range(old_idx + 1, new_idx + 1):
            r = MOGUL_RANKS[i]
            bonus = int(r["score"] * 0.02)
            s["cash"] += bonus
            events.append({"type": "positive", "category": "mogul",
                "text": f"{r['icon']} RANK UP — you're now a {r['name']}!" + (f" (+${bonus:,})" if bonus else "")})
            s["log"].insert(0, {"day": s["day"], "type": "positive",
                "text": f"Mogul Rank up: {r['name']}" + (f" (+${bonus:,})" if bonus else "")})
        s["mogul_rank"] = new_idx

@app.route('/api/advance', methods=['POST'])
def api_advance():
    data     = request.json
    days     = max(1, min(int(data.get("days", 1)), 30))
    s           = load()
    if any(isinstance(p.get("squatter"), dict) and p["squatter"].get("starter") for p in s["properties"]):
        return jsonify({"error": "There's a squatter in your house. Time isn't going anywhere until you deal with that."}), 400
    events             = []
    new_repairs            = []
    new_renewal_offers     = []
    new_commercial_events  = []
    new_storylet_events    = []
    new_vending_events     = []
    new_arcade_events      = []
    new_pole_events        = []
    new_car_wash_events    = []
    rent_log               = {}   # prop_id -> summary dict
    squatter_spawned       = False

    tax_event = None

    for d in range(days):
        current_day       = s["day"] + d + 1
        early_exit_happened = False   # only one tenant leaves early per day

        # Assistant daily fee deductions
        for asst_key, asst in ASSISTANTS.items():
            if s.get("assistants", {}).get(asst_key):
                _fee = int(asst["monthly_fee"] / 28)
                s["cash"] = max(0, s["cash"] - _fee)
                if asst_key in ("accountant", "leasing_agent"):
                    _tax_deduct(s, _fee)   # these retainers are deductible business expenses

        for prop in s["properties"]:
            if not prop.get("tenant"):
                continue
            t   = prop["tenant"]
            pid = prop["id"]

            # Waiting on player's renewal response — skip all processing
            if t.get("renewal_pending"):
                continue

            # Storylets — progress an active one (or maybe start one)
            _sev = _storylet_tick(s, prop, t, current_day, events)
            if _sev:
                new_storylet_events.append(_sev)
            if not prop.get("tenant"):
                continue   # tenant left via a storylet outcome
            t = prop["tenant"]

            # Lease end — willingness to renew scales with morale, loyalty, rent tier
            if current_day >= t.get("lease_end_day", 999999):
                _tier_pen = {"Very High": 0.40, "High": 0.20}.get(t.get("rent_tier", "Average"), 0.0)
                renew_chance = 0.40 + 0.40 * (t.get("morale", 50) / 100) + 0.20 * (t.get("loyalty", 10) / 100) - _tier_pen
                renew_chance = max(0.05, min(0.97, renew_chance))
                if random.random() < renew_chance:
                    new_stay = random.randint(t.get("stay_min", 60), t.get("stay_max", 180))
                    t["renewal_pending"]   = True
                    t["renewal_stay_days"] = new_stay
                    t["renewal_odds"]      = _renewal_odds(t)
                    new_renewal_offers.append({
                        "prop_id":        prop["id"],
                        "prop_name":      f"{prop['type']} — {prop['neighborhood']}",
                        "tenant_name":    t["name"],
                        "tenant_icon":    t.get("icon", "👤"),
                        "rent":           t["rent"],
                        "fair_rent":      calc_fair_weekly_rent(prop),
                        "rent_tier":      t.get("rent_tier", "Average"),
                        "new_stay_days":  new_stay,
                        "missed_payments": t.get("missed_payments", 0),
                        "morale":         t.get("morale", 50),
                        "loyalty":        t.get("loyalty", 10),
                        "renewals":       t.get("renewals", 0),
                        "trait_info":     t.get("trait_info"),
                        "renewal_odds":   t["renewal_odds"],
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
                # Trait: weekly condition effect (handy/green_thumb improve, rowdy/family wear)
                _cpw = TRAIT_EFFECTS.get(t.get("trait"), {}).get("cond_per_week", 0)
                if _cpw:
                    prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + _cpw))
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

            prop["days_rented"]  = prop.get("days_rented", 0) + 1
            t["days_resident"]   = t.get("days_resident", 0) + 1

        # ── Global tenant event roll ───────────────────────────────────────────
        # 15% base chance + 1% per tenant (capped at 75%) that one event fires.
        # Each event type has a weight; same event can't repeat for a tenant within a season.
        # The Phil is excluded — he handles his own improvements separately.
        # To add a new event: add to TENANT_EVENTS and add an elif handler below.
        tenant_props = [p for p in s["properties"] if p.get("tenant") and not _is_special_tenant(p["tenant"])]
        tenant_count = len(tenant_props)
        if tenant_count > 0:
            owned_items  = s.get("owned_items", {})
            event_chance = min(0.15 + 0.01 * tenant_count, 0.75)
            if owned_items.get("filing_cabinet"):
                event_chance *= 0.85
            if random.random() < event_chance:
                target_prop = random.choice(tenant_props)
                t           = target_prop["tenant"]

                # Filter out events used by this tenant within the last season
                recent_keys  = {e["key"] for e in t.get("recent_events", [])
                                if current_day - e["day"] < DAYS_PER_SEASON}
                tenant_morale = t.get("morale", 50)
                prop_cond     = target_prop.get("condition", 0)
                valid_events  = [
                    e for e in TENANT_EVENTS
                    if e["key"] not in recent_keys
                    and tenant_morale >= e.get("min_morale", 0)
                    and tenant_morale <= e.get("max_morale", 100)
                    and prop_cond     <= e.get("max_condition", MAX_CONDITION)
                ]

                if valid_events:
                    chosen_event = _pick_weighted_event(valid_events)

                    # Record event on tenant; trim entries older than 2 seasons
                    t.setdefault("recent_events", []).append(
                        {"key": chosen_event["key"], "day": current_day})
                    t["recent_events"] = [e for e in t["recent_events"]
                                          if current_day - e["day"] < DAYS_PER_SEASON * 2]

                    if chosen_event["type"] == "repair":
                        sc = random.choice(REPAIR_SCENARIOS)
                        target_prop["condition"] = max(0, target_prop["condition"] - 2)
                        new_repairs.append({
                            "id":        f"r{current_day}_{target_prop['id']}",
                            "prop_id":   target_prop["id"],
                            "prop_name": f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "key":       sc["key"],
                            "title":     sc["title"],
                            "icon":      sc["icon"],
                            "text":      _fmt_sl(sc["text"], t, target_prop),
                            "choices":   [{"label": c["label"], "cost": c["cost"]}
                                          for c in _repair_choices(sc)],
                        })

                    elif chosen_event["type"] == "morale_auto":
                        # Auto events: apply morale silently, show in advance events list
                        delta = chosen_event.get("morale_delta", 0)
                        # House plant: 15% chance to block 1 point of morale loss
                        if delta < 0 and owned_items.get("house_plant") and random.random() < 0.15:
                            delta = min(0, delta + 1)
                        # Aquarium: additional 20% morale block
                        if delta < 0 and owned_items.get("aquarium") and random.random() < 0.20:
                            delta = min(0, delta + 1)
                        # Garden: 20% morale block (independent roll)
                        if delta < 0 and owned_items.get("garden") and random.random() < 0.20:
                            delta = min(0, delta + 1)
                        # Headphones: negative morale events reduced by 1 point
                        if delta < 0 and owned_items.get("headphones"):
                            delta = min(0, delta + 1)
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

                    elif chosen_event["type"] == "cash_auto":
                        bonus       = random.randint(chosen_event["cash_min"], chosen_event["cash_max"])
                        s["cash"]  += bonus
                        icon        = chosen_event.get("icon", "💰")
                        tenant_name = t.get("name", "Your tenant")
                        msg         = chosen_event.get("message", "sent you some cash")
                        events.append({
                            "prop": f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "text": f"{icon} {tenant_name} {msg}. (+${bonus:,})",
                            "type": "success",
                        })
                        s["log"].insert(0, {"day": current_day, "type": "info",
                            "text": f"{tenant_name} {msg} — you received ${bonus:,}"})

                    elif chosen_event["type"] == "cond_auto":
                        gain        = chosen_event.get("cond_gain", 0)
                        old_cond    = target_prop.get("condition", 0)
                        target_prop["condition"] = min(MAX_CONDITION, old_cond + gain)
                        actual_gain = target_prop["condition"] - old_cond
                        icon        = chosen_event.get("icon", "🔧")
                        tenant_name = t.get("name", "Your tenant")
                        msg         = chosen_event.get("message", "improved the property")
                        events.append({
                            "prop": f"{target_prop['type']} — {target_prop['neighborhood']}",
                            "text": f"{icon} {tenant_name} {msg}. (Condition +{actual_gain})",
                            "type": "success",
                        })
                        s["log"].insert(0, {"day": current_day, "type": "info",
                            "text": f"{tenant_name} {msg} at {target_prop['type']} in {target_prop['neighborhood']} (condition +{actual_gain})"})
                    # ── Add handlers for future event types here ──────────────

        # ── Commercial properties tick ────────────────────────────────────────
        for prop in s["properties"]:
            if not prop.get("commercial"):
                continue
            ctype = COMMERCIAL_TYPES.get(prop["type"])
            if not ctype:
                continue
            prop_label = f"{ctype['name']} — Commerce Row"

            # Daily overhead
            s["cash"] = max(0, s["cash"] - int(ctype["overhead"] / 28))

            # Foot traffic recomputed daily from the current tenant mix
            ft = _commercial_foot_traffic(prop)
            prop["foot_traffic"] = ft

            for unit in prop.get("units", []):
                btype_key = unit.get("business_type")
                if not btype_key:
                    continue
                btype = BUSINESS_TENANT_TYPES.get(btype_key)
                if not btype:
                    continue
                # Daily base rent + percentage (sales) rent scaled by foot traffic
                daily_rent = int(unit["monthly_rent"] / 28)
                pct_max    = BUSINESS_PCT_MAX.get(btype_key, 0)
                pct_month  = int(pct_max * (ft / 100)) if pct_max else 0
                unit["pct_rent_monthly"] = pct_month                # for UI display
                gross = daily_rent + int(pct_month / 28)
                s["cash"] += gross
                s["tax_year_rent_income"] = s.get("tax_year_rent_income", 0) + gross

                # Tenant satisfaction drifts toward a target set by traffic, condition, upgrades, sales
                sat_target = 35 + ft * 0.45 + (prop.get("condition", 80) - 70) * 0.30
                _up = prop.get("upgrades", {})
                if _up.get("renovated_common"): sat_target += 4
                if _up.get("security_system"):  sat_target += 3
                if pct_month > 0:               sat_target += 4     # they're making good money here
                sat_target = max(0, min(100, sat_target))
                _cur = unit.get("satisfaction", 70)
                unit["satisfaction"] = round(_cur + (sat_target - _cur) * 0.10, 1)

                # Lease countdown
                unit["lease_days_remaining"] = max(0, unit.get("lease_days_remaining", 0) - 1)

                if unit["lease_days_remaining"] <= 0:
                    sat = unit.get("satisfaction", 70)
                    # Satisfaction drives renewal odds: ~45% at rock bottom, ~95% when thrilled
                    renew_chance = 0.45 + (sat / 100) * 0.50
                    if btype_key == "flooring_express" or random.random() < renew_chance:
                        unit["lease_days_remaining"] = btype["lease_days"]
                        unit["renewal_pending"]      = False
                        # Happy tenants accept a rent bump on renewal (up to +7%)
                        old = unit["monthly_rent"]
                        if sat >= 70 and btype_key != "flooring_express":
                            unit["monthly_rent"] = int(old * (1.0 + min(0.07, (sat - 70) / 100 * 0.20)))
                        if unit["monthly_rent"] > old:
                            events.append({"prop": prop_label, "type": "positive", "category": "commercial",
                                "text": f"✅ {unit['tenant_name']} renewed — rent raised to ${unit['monthly_rent']:,}/mo."})
                        else:
                            events.append({"prop": prop_label, "type": "info", "category": "commercial",
                                "text": f"✅ {unit['tenant_name']} renewed their lease."})
                        s["log"].insert(0, {"day": current_day, "type": "info",
                            "text": f"{unit['tenant_name']} renewed at {prop_label}"})
                    else:
                        name = unit["tenant_name"]
                        unit["business_type"]        = None
                        unit["tenant_name"]          = None
                        unit["lease_days_remaining"] = 0
                        unit["monthly_rent"]         = 0
                        unit["renewal_pending"]      = False
                        unit["satisfaction"]         = 70
                        unit["pct_rent_monthly"]     = 0
                        msg = "didn't renew (unhappy tenant)" if sat < 55 else "didn't renew their lease"
                        events.append({"prop": prop_label, "type": "warning", "category": "commercial",
                            "text": f"🚪 {name} {msg} — unit now vacant."})
                        s["log"].insert(0, {"day": current_day, "type": "warning",
                            "text": f"{name} vacated after lease expired at {prop_label}"})
                    continue

                # Random event roll (upgrades can reduce event chance)
                evt_chance = _commercial_event_chance(btype_key, btype) / 28
                upgrades   = prop.get("upgrades", {})
                if upgrades.get("security_system"):
                    evt_chance *= 0.40
                if upgrades.get("parking_expansion") and btype_key in ("restaurant", "gym", "pawn_shop", "tattoo_studio", "auto_parts"):
                    evt_chance *= 0.60
                if random.random() < evt_chance:
                    # Pool = shared events + this business's signature events
                    pool = list(_GENERIC_COMM_EVENTS) + BUSINESS_EVENTS.get(btype_key, [])
                    # Flooring Express is the special tenant — only its own funny events fire.
                    if btype_key == "flooring_express":
                        pool = BUSINESS_EVENTS["flooring_express"]
                    defn = random.choices(pool, weights=[e.get("weight", 2) for e in pool])[0]
                    inst = _build_commercial_event(defn, prop, unit, btype, prop_label)
                    if inst["kind"] == "auto":
                        _apply_commercial_effect(s, prop, unit, inst["auto_effect"])
                        log_type = inst["etype"] if inst["etype"] in ("positive", "warning", "info", "negative") else "info"
                        events.append({"prop": prop_label, "type": inst["etype"], "category": "commercial",
                            "text": f"{inst['icon']} {inst['result']}"})
                        s["log"].insert(0, {"day": current_day, "type": log_type,
                            "text": f"{inst['result']} ({prop_label})"})
                    elif prop.get("superintendent"):
                        # The building's superintendent handles its own choice-card events
                        _superintendent_resolve(s, prop, unit, inst, events, current_day)
                    else:
                        new_commercial_events.append(inst)

            # Condition degradation (per occupied unit type)
            upgrades_      = prop.get("upgrades", {})
            restaurant_ct  = sum(1 for u in prop["units"] if u.get("business_type") == "restaurant")
            gym_ct         = sum(1 for u in prop["units"] if u.get("business_type") == "gym")
            heavy_wear_ct  = sum(1 for u in prop["units"] if u.get("business_type") in ("tattoo_studio", "auto_parts", "pawn_shop", "tech_startup"))
            cond_loss      = 0.05 + 0.10 * restaurant_ct + 0.08 * gym_ct + 0.06 * heavy_wear_ct
            if upgrades_.get("commercial_hvac"):
                cond_loss *= 0.65  # HVAC reduces wear by 35%

            # Maintenance Man: per-building employee who keeps the building in good shape.
            # Cuts wear sharply and steadily repairs the building toward a well-kept 92.
            if prop.get("maintenance"):
                maint_daily = int(ctype.get("maintenance_monthly", 0) / 28)
                s["cash"]   = max(0, s["cash"] - maint_daily)
                _tax_deduct(s, maint_daily)
                cond_loss  *= 0.40
                if prop.get("condition", 100) < 92:
                    prop["condition"] = min(92, prop.get("condition", 0) + 0.8)

            # Superintendent: per-building employee — daily fee; handles this building's
            # choice-card events (resolved at event time above). No condition role.
            if prop.get("superintendent"):
                sup_daily = int(ctype.get("superintendent_monthly", 0) / 28)
                s["cash"] = max(0, s["cash"] - sup_daily)
                _tax_deduct(s, sup_daily)

            prop["condition"] = max(0, prop.get("condition", 100) - cond_loss)

            # Leasing Agent: gradually fills vacant units with a complementary tenant
            if s.get("assistants", {}).get("leasing_agent"):
                for unit in prop.get("units", []):
                    if unit.get("business_type") or random.random() > 0.22:
                        continue
                    bt = _agent_pick_tenant(prop)
                    if not bt:
                        continue
                    btd       = BUSINESS_TENANT_TYPES[bt]
                    base_rent = btd["monthly_rent"]
                    _ug = prop.get("upgrades", {})
                    if _ug.get("renovated_common"):  base_rent = int(base_rent * 1.08)
                    if _ug.get("exterior_facelift"): base_rent += 300
                    if _ug.get("fiber_internet") and bt in ("law_office", "accounting_firm"): base_rent += 500
                    unit["business_type"]        = bt
                    unit["tenant_name"]          = random.choice(btd["names"])
                    unit["lease_days_remaining"] = btd["lease_days"]
                    unit["monthly_rent"]         = base_rent
                    unit["renewal_pending"]      = False
                    unit["satisfaction"]         = 72
                    unit["pct_rent_monthly"]     = 0
                    unit["applicants"]           = []
                    events.append({"prop": prop_label, "type": "positive", "category": "commercial",
                        "text": f"🤝 Leasing Agent signed {unit['tenant_name']} ({btd['name']}) — ${base_rent:,}/mo."})
                    s["log"].insert(0, {"day": current_day, "type": "positive",
                        "text": f"Leasing Agent filled a unit at {prop_label} with {unit['tenant_name']}"})

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
                        if not p.get("commercial")          # squatters only target residential homes
                        and not p.get("tenant") and not p.get("squatter")
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
                if s["cash"] >= payment:
                    # On-time payment — pay it, chip the balance, build credit.
                    int_part = round(loan["balance"] * wr, 2)
                    pri_part = round(payment - int_part, 2)
                    s["cash"] -= payment
                    loan["balance"]    = round(max(0, loan["balance"] - pri_part), 2)
                    loan["weeks_paid"] = loan.get("weeks_paid", loan.get("months_paid", 0)) + 1
                    loan["missed"]     = 0
                    _credit_adjust(s, CREDIT_ONTIME_BONUS)
                    events.append({"prop": loan["product"],
                                    "text": f"Weekly loan payment: -${payment:,.2f} (${loan['balance']:,.0f} left)",
                                    "type": "warning"})
                    if loan["balance"] <= 0:
                        paid_off.append(loan["id"])
                        _credit_adjust(s, CREDIT_PAYOFF_BONUS)
                        events.append({"prop": loan["product"],
                                        "text": f"Loan fully paid off! 🎉 Credit score +{CREDIT_PAYOFF_BONUS}.",
                                        "type": "positive"})
                else:
                    # Missed payment — late fee onto the balance, interest accrues, credit drops.
                    late_fee = max(LOAN_LATE_FEE_MIN, round(payment * LOAN_LATE_FEE_PCT, 2))
                    loan["balance"] = round(loan["balance"] + late_fee, 2)
                    loan["missed"]  = loan.get("missed", 0) + 1
                    _credit_adjust(s, -CREDIT_MISSED_PENALTY)
                    events.append({"prop": loan["product"],
                                    "text": f"⚠ MISSED loan payment! +${late_fee:,.0f} late fee, credit score −{CREDIT_MISSED_PENALTY}. Balance ${loan['balance']:,.0f}.",
                                    "type": "negative"})
            bank["loans"] = [l for l in bank["loans"] if l["id"] not in paid_off]
            # Debt-free weeks let credit slowly recover toward fair.
            if not bank.get("loans") and credit_score(s) < CREDIT_START:
                _credit_adjust(s, CREDIT_DRIFT)
            s["bank"] = bank

        # CD maturity — checked daily so payout lands on the exact maturity day.
        _cb = _bank(s)
        _matured = [cd for cd in _cb.get("cds", []) if current_day >= cd.get("mature_day", 0)]
        if _matured:
            for cd in _matured:
                s["cash"] += cd["payout"]
                _interest = cd["payout"] - cd["principal"]
                events.append({"prop": "Certificate of Deposit",
                                "text": f"{cd['name']} matured: +${cd['payout']:,} (${cd['principal']:,} principal + ${_interest:,} interest)",
                                "type": "positive"})
                s["log"].insert(0, {"day": current_day, "type": "positive",
                    "text": f"{cd['name']} matured — ${cd['payout']:,} returned to cash."})
            _cb["cds"] = [cd for cd in _cb.get("cds", []) if current_day < cd.get("mature_day", 0)]
            s["bank"] = _cb

        # ── Tax system ────────────────────────────────────────────────────────
        _si, _di = _season_info(current_day)

        # Winter day 21: 7-day heads-up
        if _si == 3 and _di == 21:
            _tx = _compute_taxes(s)
            events.append({
                "prop": "Tax Notice",
                "text": f"📋 Tax Day is 7 days away (Winter Day 28)! Estimated tax owed: ${_tx['total']:,} "
                        f"(rent ${_tx['rent_tax']:,} + business/flips ${_tx['active_tax']:,}).",
                "type": "warning",
            })
            s["log"].insert(0, {"day": current_day, "type": "warning",
                "text": f"Tax reminder: ~${_tx['total']:,} due on Winter Day 28"})

        # Winter day 28: tax due. With an Accountant on staff it's auto-filed &
        # paid on time; otherwise the player gets the pay-now / extension modal.
        if _si == 3 and _di == 28 and not s.get("tax_extension_filed", False):
            _tx = _compute_taxes(s)
            if s.get("assistants", {}).get("accountant"):
                s["cash"] -= _tx["total"]
                events.append({
                    "prop": "Accountant",
                    "text": f"🧾 Your accountant filed and paid your taxes: -${_tx['total']:,} "
                            f"(rent ${_tx['rent_tax']:,} + business/flips ${_tx['active_tax']:,}).",
                    "type": "warning",
                })
                s["log"].insert(0, {"day": current_day, "type": "warning",
                    "text": f"Accountant auto-filed taxes: -${_tx['total']:,} paid."})
                _reset_tax_year(s)
            else:
                tax_event = _tx
                events.append({
                    "prop": "IRS",
                    "text": f"🧾 Tax Day! ${_tx['total']:,} owed — pay now or file for extension.",
                    "type": "warning",
                })

        # Spring day 7: collect deferred extension tax
        if _si == 0 and _di == 7 and s.get("tax_extension_filed", False):
            _owed = s.get("tax_owed", 0)
            s["cash"] -= _owed
            _reset_tax_year(s)
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


    # ── Vending: demand-matched sales, reputation, pricing, upgrades, Vinny ────
    vms      = s.get("vending_machines", [])
    vinny_on = s.get("vinny_hired", False)
    inv      = s.setdefault("costpro_inventory", {})
    for vm in vms:
        loc = VM_LOCATIONS.get(vm.get("location_key"))
        if not loc:
            continue
        for d2 in range(days):
            cur = s["day"] + d2 + 1
            # Grandma's weekly shop (runs once across the portfolio, not per machine).
            if s.get("grandma_hired") and cur - s.get("grandma_last_shop", -GRANDMA_INTERVAL) >= GRANDMA_INTERVAL:
                _grandma_shop(s, cur, events)
            # Vinny tops the route up each morning, for a fee if he moved anything.
            if vinny_on and _vm_restock_from_inventory(vm, inv, cur) > 0:
                s["cash"] = max(0, s["cash"] - VINNY_FEE)
                _tax_deduct(s, VINNY_FEE)

            day_profit, spoiled, stockouts = _vm_sell_day(vm, loc, cur)
            _vm_update_reputation(vm, spoiled, stockouts)
            s["cash"] += round(day_profit)
            _biz_income(s, "vending", round(day_profit))

            if spoiled >= 1:
                events.append({
                    "prop":     f"Machine #{vm['slot']} — {loc['name']}",
                    "text":     f"{int(round(spoiled))} units of perishable stock spoiled before selling.",
                    "type":     "negative", "category": "business",
                })

    # At most ONE vending event per advance (choice card), at a low chance, on a
    # random machine — so the player isn't buried in pop-ups.
    if vms and random.random() < VM_EVENT_CHANCE:
        _evm = random.choice(vms)
        _eloc = VM_LOCATIONS.get(_evm.get("location_key"))
        if _eloc:
            _qe = _vm_queue_event(_evm, _eloc)
            if _qe:
                new_vending_events.append(_qe)

    s["vending_machines"]  = vms
    s["costpro_inventory"] = inv

    # ── Personal item passive income ─────────────────────────────────────────
    if s.get("owned_items", {}).get("wine_rack"):
        s["cash"] += 100 * days
    if s.get("owned_items", {}).get("sports_car"):
        s["cash"] += 200 * days

    # ── Laundromat income + events ─────────────────────────────────────────────
    lm = s.get("laundromat")
    if lm and lm.get("owned"):
        staff    = lm.setdefault("staff",    {"janitor": False, "repairman": False})
        machines = lm.setdefault("machines", [
            {"id": i, "status": "working", "upgrades": {}} for i in range(LAUNDROMAT_START_MACHINES)
        ])
        for _day in range(days):
            # Insurance weekly charge
            if lm.get("insurance"):
                lm["insurance_days"] = lm.get("insurance_days", 7) - 1
                if lm["insurance_days"] <= 0:
                    lm["insurance_days"] = 7
                    s["cash"] = max(0, s["cash"] - LAUNDROMAT_INSURANCE_WEEKLY)

            # Cleanliness decay
            lm["cleanliness"] = max(0, lm.get("cleanliness", 100) - LAUNDROMAT_CLEAN_DECAY)

            # Machine breakdowns
            for machine in machines:
                if machine["status"] == "working":
                    bd = 0.02 if machine.get("upgrades", {}).get("heavy_duty") else LAUNDROMAT_BREAKDOWN_PCT
                    if random.random() < bd:
                        machine["status"] = "broken"

            # Janitor daily cost + auto-clean
            if staff.get("janitor"):
                s["cash"] = max(0, s["cash"] - LAUNDROMAT_STAFF["janitor"]["cost"])
                _tax_deduct(s, LAUNDROMAT_STAFF["janitor"]["cost"])
                if lm["cleanliness"] < 75:
                    lm["cleanliness"] = min(100, lm["cleanliness"] + 30)

            # Repairman daily cost + auto-fix
            if staff.get("repairman"):
                s["cash"] = max(0, s["cash"] - LAUNDROMAT_STAFF["repairman"]["cost"])
                _tax_deduct(s, LAUNDROMAT_STAFF["repairman"]["cost"])
                repair_fee = 0 if lm.get("insurance") else LAUNDROMAT_REPAIR_COST
                for machine in machines:
                    if machine["status"] == "broken":
                        s["cash"] = max(0, s["cash"] - repair_fee)
                        machine["status"] = "working"

            # Supply Manager: daily salary + auto-orders supplies to a buffer (like Grandma).
            if staff.get("manager"):
                s["cash"] = max(0, s["cash"] - LAUNDROMAT_STAFF["manager"]["cost"])
                _tax_deduct(s, LAUNDROMAT_STAFF["manager"]["cost"])
                has_ee   = any(m.get("upgrades", {}).get("energy_efficient") for m in machines)
                soap_per = 10 if has_ee else 7
                while lm.get("soap_days", 0) < 10 and s["cash"] >= 300:       # required — keep ~10–17 days
                    s["cash"] -= 300; lm["soap_days"] = lm.get("soap_days", 0) + soap_per
                while lm.get("softener_days", 0) < 8 and s["cash"] >= 500:    # income booster
                    s["cash"] -= 500; lm["softener_days"] = lm.get("softener_days", 0) + 10
                while lm.get("sheets_days", 0) < 8 and s["cash"] >= 400:
                    s["cash"] -= 400; lm["sheets_days"] = lm.get("sheets_days", 0) + 10

            # No soap = no income
            if lm.get("soap_days", 0) <= 0:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 2)
                continue
            lm["soap_days"] -= 1

            working = [m for m in machines if m["status"] == "working"]
            if not working:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 3)
                continue
            broken_count = len(machines) - len(working)

            # ── Capacity by stage (a load needs a wash AND a dry) ──
            def _cap(stage):
                return sum(LAUNDROMAT_MACHINE_TYPES.get(m.get("type", "combo"), {}).get(stage, 0)
                           * (1.20 if m.get("upgrades", {}).get("card_reader") else 1.0)
                           for m in working)
            wash_cap, dry_cap = _cap("wash"), _cap("dry")
            throughput = min(wash_cap, dry_cap)

            # ── Demand (regulars + members drive it; daily volatility) ──
            members = lm.get("members", 0)
            demand  = (LAUNDROMAT_BASE_DEMAND
                       + lm.get("regulars", 0) * LAUNDROMAT_DEMAND_PER_REG
                       + members * LAUNDROMAT_DEMAND_PER_MEMBER)
            demand  = max(0, demand * (1 + random.uniform(-LAUNDROMAT_DEMAND_VOLATILITY, LAUNDROMAT_DEMAND_VOLATILITY)))

            loads      = min(throughput, demand)
            turn_aways = max(0, demand - throughput)

            income = loads * LAUNDROMAT_REV_PER_LOAD
            income = income * (0.4 + lm.get("cleanliness", 100) / 100 * 1.4)   # cleanliness mult
            if lm.get("softener_days", 0) > 0:
                income *= 1.25; lm["softener_days"] = max(0, lm["softener_days"] - 1)
            if lm.get("sheets_days", 0) > 0:
                income *= 1.20; lm["sheets_days"] = max(0, lm["sheets_days"] - 1)
            income = round(income)

            # ── Membership recurring income + add-on income ──
            addons = lm.setdefault("addons", {})
            income += round(members * LAUNDROMAT_MEMBER_FEE)
            for akey, a in LAUNDROMAT_ADDONS.items():
                if not addons.get(akey):
                    continue
                if akey == "vending":
                    continue   # a real vending machine now — earns via the vending system
                if akey == "atm":
                    income += a["income"] + round(loads * 0.5)
                elif akey == "wash_fold":
                    # A wash-&-fold service bonus on loads actually run — NOT a reward for
                    # over-building idle machines (which it used to be).
                    income += round(loads * 2)
                else:
                    income += a.get("income", 0)
                if akey == "arcade" and random.random() < 0.5:
                    lm["regulars"] = min(100, lm.get("regulars", 0) + 1)

            # ── Reputation / regulars dynamics ──
            if turn_aways > 0.5:
                lm["regulars"] = max(0, lm.get("regulars", 0) - min(5, 1 + int(turn_aways // 4)))
            elif lm.get("cleanliness", 100) > 55 and broken_count == 0:
                lm["regulars"] = min(100, lm.get("regulars", 0) + 2)
            if broken_count > len(machines) // 2:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 1)
            if lm.get("cleanliness", 100) < 25:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 2)

            # ── Members drift toward a share of regulars (only with Loyalty Program) ──
            if addons.get("loyalty"):
                target = lm.get("regulars", 0) * 0.6
                if members < target:
                    lm["members"] = min(target, members + 1.5)
                elif members > target:
                    lm["members"] = max(target, members - 1)
            lm["members"] = round(lm.get("members", 0), 1)

            # ── Random flavor event (~12%/day while operating) ──
            if random.random() < 0.12:
                evt    = random.choice(LAUNDROMAT_EVENTS)
                effect = evt["effect"]; val = evt["value"]
                if effect == "income_zero":
                    income = 0
                elif effect == "income_mult":
                    income = max(0, round(income * (1 + val)))
                elif effect == "income_bonus":
                    income += int(val)
                elif effect == "fine":
                    s["cash"] = max(0, s["cash"] - int(val))
                elif effect == "cleanliness":
                    lm["cleanliness"] = max(0, min(100, lm.get("cleanliness", 100) + int(val)))
                elif effect == "regulars":
                    lm["regulars"] = max(0, min(100, lm.get("regulars", 0) + int(val)))
                elif effect == "break_two":
                    for m in random.sample(working, min(2, len(working))):
                        m["status"] = "broken"
                events.append({"prop": "Dirty Money Laundromat", "text": evt["text"],
                               "type": evt["type"], "category": "business"})

            # Surface turn-aways so the player feels the capacity squeeze.
            if turn_aways >= 4:
                events.append({"prop": "Dirty Money Laundromat",
                    "text": f"Turned away ~{int(turn_aways)} loads of demand — not enough {'dryers' if dry_cap < wash_cap else 'washers' if wash_cap < dry_cap else 'machines'} to keep up.",
                    "type": "negative", "category": "business"})

            s["cash"]         += income
            lm["total_earned"] = lm.get("total_earned", 0) + income
            _biz_income(s, "laundromat", income)

        s["laundromat"] = lm

    # ── The Back-Room Arcade advance ──────────────────────────────────────────
    arc = s.get("arcade")
    if arc and arc.get("unlocked"):
        import math
        cabs   = arc.get("cabinets", [])
        astaff = arc.setdefault("staff", {})
        lm_arc = s.get("laundromat") or {}
        arc.setdefault("uncollected", 0)
        arc.setdefault("cleanliness", 100)
        arc.setdefault("prizes", 0)
        decor = arc.get("decor", {})
        decor_traffic = sum(ARCADE_DECOR[k].get("traffic", 0) for k in decor if decor.get(k) and k in ARCADE_DECOR)
        decor_clean   = sum(ARCADE_DECOR[k].get("clean", 0)   for k in decor if decor.get(k) and k in ARCADE_DECOR)
        decor_income  = sum(ARCADE_DECOR[k].get("income", 0)  for k in decor if decor.get(k) and k in ARCADE_DECOR)
        clean_decay   = max(1, ARCADE_CLEAN_DECAY - decor_clean)
        for _day in range(days):
            _cur_day = s["day"] + _day + 1   # simulated calendar day for hot-streak decay
            # Foot traffic dirties the floor; the Janitor keeps it clean. Carpet slows it.
            arc["cleanliness"] = max(0, arc.get("cleanliness", 100) - clean_decay)
            if astaff.get("janitor"):
                s["cash"] = max(0, s["cash"] - ARCADE_STAFF["janitor"]["cost"])
                _tax_deduct(s, ARCADE_STAFF["janitor"]["cost"])
                if arc["cleanliness"] < 70:
                    arc["cleanliness"] = min(100, arc["cleanliness"] + 35)

            # Wear, breakdowns, and the Repair Tech (auto-fix + maintain).
            for cab in cabs:
                if cab.get("status") == "working":
                    cab["condition"] = max(0, cab.get("condition", 100) - ARCADE_CABINET_DECAY)
                    if random.random() < ARCADE_BREAKDOWN_PCT:
                        cab["status"] = "broken"
            if astaff.get("tech"):
                s["cash"] = max(0, s["cash"] - ARCADE_STAFF["tech"]["cost"])
                _tax_deduct(s, ARCADE_STAFF["tech"]["cost"])
                for cab in cabs:
                    if cab.get("status") == "broken":
                        cab["status"] = "working"
                    cab["condition"] = max(cab.get("condition", 100), 80)

            working = [c for c in cabs if c.get("status") == "working"]
            if working:
                traffic_f = (0.6 + min(1.0, (lm_arc.get("regulars", 0) + lm_arc.get("members", 0)) / 100) * 0.8) * (1 + decor_traffic)
                clean_f   = 0.6 + arc.get("cleanliness", 100) / 100 * 0.4   # dirty floor earns less
                # Prize counter: a stocked counter boosts income, but prizes get won daily.
                prize_use = round(len(working) * traffic_f * ARCADE_PRIZE_USE_PER_CAB)
                coverage  = min(1.0, arc.get("prizes", 0) / prize_use) if prize_use > 0 else 0.0
                prize_f   = 1 + ARCADE_PRIZE_BOOST_MAX * coverage
                arc["prizes"] = max(0, arc.get("prizes", 0) - prize_use)
                gcounts   = {}
                for c in working:
                    gcounts[c.get("genre", "retro")] = gcounts.get(c.get("genre", "retro"), 0) + 1
                income = 0
                for c in working:
                    cond_f  = 0.5 + c.get("condition", 100) / 100 * 0.5
                    sat_f   = 1.0 / math.sqrt(gcounts[c.get("genre", "retro")])
                    rare_f  = ARCADE_RARE_INCOME_MULT if c.get("rare") else 1.0
                    hot_f   = ARCADE_HOT_MULT if c.get("hot_until", 0) > _cur_day else 1.0   # 🔥 high-score streak
                    vol     = 1 + random.uniform(-ARCADE_INCOME_VOLATILITY, ARCADE_INCOME_VOLATILITY)
                    income += round(ARCADE_INCOME_PER_CABINET * cond_f * traffic_f * clean_f
                                    * sat_f * rare_f * hot_f * prize_f * (1 + decor_income) * vol)
                # Money piles up in the machines until you (or the Floor Manager) collect it.
                cap = max(1000, len(cabs) * ARCADE_TILL_PER_CABINET)
                arc["uncollected"] = min(cap, arc.get("uncollected", 0) + income)

            # Arcade Manager: banks the machine cash daily AND restocks the prize
            # counter (balanced to a ~7-day buffer, bought from CostPro out of cash).
            if astaff.get("collector"):
                s["cash"] = max(0, s["cash"] - ARCADE_STAFF["collector"]["cost"])
                _tax_deduct(s, ARCADE_STAFF["collector"]["cost"])
                take = arc.get("uncollected", 0)
                if take > 0:
                    s["cash"]          += take
                    arc["total_earned"] = arc.get("total_earned", 0) + take
                    _biz_income(s, "arcade", take)
                    arc["uncollected"]  = 0
                n_working = sum(1 for c in cabs if c.get("status") == "working")
                if n_working:
                    est_traffic = (0.6 + min(1.0, (lm_arc.get("regulars", 0) + lm_arc.get("members", 0)) / 100) * 0.8) * (1 + decor_traffic)
                    daily_use   = max(1, round(n_working * est_traffic * ARCADE_PRIZE_USE_PER_CAB))
                    target      = daily_use * 7
                    if arc.get("prizes", 0) < target:
                        _pitem    = COSTPRO_ITEMS["arcade_prizes"]
                        per_case  = _pitem.get("units", 60)
                        case_cost = _pitem["price"]
                        need      = math.ceil((target - arc.get("prizes", 0)) / per_case)
                        cases     = min(need, int(s["cash"] // case_cost))
                        if cases > 0:
                            s["cash"]    -= cases * case_cost
                            arc["prizes"] = arc.get("prizes", 0) + cases * per_case
        # The cabinet market refreshes for a new day — but ONLY if you bought from
        # it (or there isn't one yet). Sit on the same lineup and it won't re-roll.
        if arc.get("market_used") or not arc.get("market"):
            _arcade_roll_market(s)
        s["arcade"] = arc

        # One arcade choice-card event may fire per advance, at a low chance.
        if random.random() < ARCADE_EVENT_CHANCE:
            _qae = _arcade_queue_event(s)
            if _qae:
                new_arcade_events.append(_qae)

    # ── Brass Pole Fitness Studio advance ─────────────────────────────────────
    ps = s.get("pole_studio")
    if ps and ps.get("owned"):
        staff   = ps.setdefault("staff", {})
        facs    = ps.setdefault("facilities", {})
        ps.setdefault("dancers", {k: _pole_studio_dancer_state(k) for k in POLE_STUDIO_DANCERS})
        for _dk, _dd in ps["dancers"].items():
            _dd.setdefault("class", POLE_STUDIO_SPECIALTY_CLASS.get(_dk, "open"))
            _dd.setdefault("energy", 100)
        ps.setdefault("active_demands", [])
        ps.setdefault("slots", [])
        ps.setdefault("slot_count", ps.get("pole_count", STUDIO_START_SLOTS) or STUDIO_START_SLOTS)
        ps.setdefault("members", 0); ps.setdefault("vip_members", 0); ps.setdefault("satisfaction", 70)
        ps.setdefault("kombucha", {})
        dancers = ps["dancers"]
        slot_cap = ps.get("slot_count", STUDIO_START_SLOTS)
        while len(ps["slots"]) < slot_cap:   # ensure a slot object exists for every available class slot
            ps["slots"].append({"type": "intro", "instructor": None})
        def _equip_ok(eq):
            if eq == "silks": return bool(facs.get("silks_rig"))
            if eq == "vip":   return bool(facs.get("vip_suite"))
            return True

        for _day in range(days):
            # ── Insurance weekly charge ──
            if ps.get("insurance"):
                ps["insurance_days"] = ps.get("insurance_days", 7) - 1
                if ps["insurance_days"] <= 0:
                    ps["insurance_days"] = 7
                    s["cash"] = max(0, s["cash"] - POLE_STUDIO_INSURANCE_WEEKLY)

            # ── Ambiance & cleanliness decay; staff upkeep ──
            ps["atmosphere"]  = max(0, ps.get("atmosphere", 100)  - POLE_STUDIO_ATM_DECAY)
            ps["cleanliness"] = max(0, ps.get("cleanliness", 100) - POLE_STUDIO_CLEAN_DECAY)
            if facs.get("dj_booth"):
                ps["atmosphere"] = min(100, ps["atmosphere"] + 14)   # resident DJ keeps the vibe up
            if staff.get("vibe_manager"):
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["vibe_manager"]["cost"]); _tax_deduct(s, POLE_STUDIO_STAFF["vibe_manager"]["cost"])
                if ps["atmosphere"] < 75: ps["atmosphere"] = min(100, ps["atmosphere"] + 20)
            if staff.get("studio_cleaner"):
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["studio_cleaner"]["cost"]); _tax_deduct(s, POLE_STUDIO_STAFF["studio_cleaner"]["cost"])
                if ps["cleanliness"] < 70: ps["cleanliness"] = min(100, ps["cleanliness"] + 25)
            host_on = bool(staff.get("host"))
            if host_on:
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["host"]["cost"]); _tax_deduct(s, POLE_STUDIO_STAFF["host"]["cost"])
            bartender_on = bool(staff.get("bartender"))
            if bartender_on:
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["bartender"]["cost"]); _tax_deduct(s, POLE_STUDIO_STAFF["bartender"]["cost"])

            # ── Studio Manager: salary + auto-handle demands + auto-fill empty slots ──
            if staff.get("manager"):
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["manager"]["cost"]); _tax_deduct(s, POLE_STUDIO_STAFF["manager"]["cost"])
                # Clear any demands carried in before they can count down / expire.
                _carry = _pole_manager_sweep_demands(s, ps)
                if _carry:
                    events.append({"prop": "Brass Pole Fitness Studio", "type": "info", "category": "business",
                        "text": f"📋 Studio Manager handled {_carry} dancer demand{'s' if _carry > 1 else ''}."})
                _assigned = {sl.get("instructor") for sl in ps["slots"][:slot_cap] if sl.get("instructor")}
                for sl in ps["slots"][:slot_cap]:
                    if not sl.get("instructor"):
                        cand = next((k for k, dd in dancers.items() if dd.get("hired") and k not in _assigned), None)
                        if cand:
                            sl["instructor"] = cand; sl["type"] = POLE_STUDIO_SPECIALTY_CLASS.get(cand, sl.get("type", "open")); _assigned.add(cand)
                # Keep the Kombucha Bar stocked (only worthwhile with a bartender on).
                if facs.get("kombucha_bar") and staff.get("bartender"):
                    kb = ps.setdefault("kombucha", {})
                    _types = [k for k in COSTPRO_ITEMS if COSTPRO_ITEMS[k].get("category") == "studio_bar" and kb.get(k, 0) > 0] or ["kb_ginger"]
                    for _kk in _types:
                        if kb.get(_kk, 0) < 7:   # ~7-day buffer per stocked drink
                            _kitem = COSTPRO_ITEMS.get(_kk)
                            if _kitem and s["cash"] >= _kitem["price"]:
                                s["cash"] -= _kitem["price"]; _tax_deduct(s, _kitem["price"])
                                kb[_kk] = kb.get(_kk, 0) + 10

            # ── Dancer demands: countdown/expiry + spawn ──
            new_demands = []
            for dem in ps.get("active_demands", []):
                dem["days_left"] = dem.get("days_left", 5) - 1
                if dem["days_left"] > 0:
                    new_demands.append(dem)
                else:
                    spec = next((d for d in POLE_STUDIO_DEMANDS if d["key"] == dem["key"]), None)
                    if spec:
                        dk = spec["dancer"]; _apply_demand_effects(s, ps, spec["reject"], dk)
                        if spec["reject"].get("quit") and ps["dancers"].get(dk, {}).get("hired"):
                            ps["dancers"][dk]["hired"] = False
                            events.append({"prop": "Brass Pole Fitness Studio", "text": f"{POLE_STUDIO_DANCERS[dk]['name']} quit. The demand expired.", "type": "negative", "category": "business"})
                    events.append({"prop": "Brass Pole Fitness Studio", "text": "A dancer demand expired unresolved.", "type": "warning", "category": "business"})
            ps["active_demands"] = new_demands
            if len(ps["active_demands"]) < 2 and random.random() < 0.06:
                hired_keys = [k for k, dd in dancers.items() if dd.get("hired")]
                if hired_keys:
                    dk = random.choice(hired_keys)
                    eligible = [d for d in POLE_STUDIO_DEMANDS if d["dancer"] == dk and d["key"] not in [ad["key"] for ad in ps["active_demands"]] and d["key"] not in ps.get("fulfilled_demands", [])]
                    if eligible:
                        spec = random.choice(eligible)
                        ps["active_demands"].append({"key": spec["key"], "dancer": dk, "days_left": spec["deadline"]})
                        if not staff.get("manager"):   # with a manager it's handled instantly below — no alert
                            events.append({"prop": "Brass Pole Fitness Studio", "text": f"{POLE_STUDIO_DANCERS[dk]['name']} has a new demand.", "type": "warning", "category": "business"})

            # Studio Manager resolves demands the same day they appear — including any just spawned.
            if staff.get("manager"):
                _swept = _pole_manager_sweep_demands(s, ps)
                if _swept:
                    events.append({"prop": "Brass Pole Fitness Studio", "type": "info", "category": "business",
                        "text": f"📋 Studio Manager handled {_swept} dancer demand{'s' if _swept > 1 else ''}."})

            # ── Members + class schedule ──
            members = ps.get("members", 0); vip = ps.get("vip_members", 0)
            daily_demand = (members + vip) * STUDIO_AVG_VISITS * (1 + random.uniform(-0.12, 0.12))
            active_slots = ps["slots"][:slot_cap]
            for sl in active_slots:
                ik = sl.get("instructor"); dd = dancers.get(ik) if ik else None
                ct = POLE_STUDIO_CLASSES.get(sl.get("type"))
                ok = bool(ct) and dd and dd.get("hired") and _equip_ok(ct["equip"]) and dd.get("energy", 100) >= 12
                sl["_valid"] = bool(ok)
            valid = [sl for sl in active_slots if sl.get("_valid")]
            pop_total = sum(POLE_STUDIO_CLASSES[sl["type"]]["popularity"] for sl in valid) or 1
            teaching = set()
            capacity = 0.0; attendance = 0.0; class_income = 0.0; cancelled = 0
            for sl in active_slots:
                if not sl.get("_valid"):
                    if sl.get("instructor"): cancelled += 1
                    continue
                ct = POLE_STUDIO_CLASSES[sl["type"]]; ik = sl["instructor"]; dd = dancers[ik]
                seats = ct["seats"]
                capacity += seats
                if sl["type"] == "private":
                    want = vip * 0.7 * (1 + random.uniform(-0.1, 0.1))
                else:
                    want = daily_demand * (ct["popularity"] / pop_total)
                fill = max(0.0, min(seats, want))
                attendance += fill
                fit_m    = POLE_STUDIO_SPECIALTY_FIT if POLE_STUDIO_SPECIALTY_CLASS.get(ik) == sl["type"] else POLE_STUDIO_OFFSPEC_FIT
                energy_f = 0.6 + dd.get("energy", 100) / 100 * 0.4
                mood_f   = 1.0 if ik == "gary" else (0.6 + dd.get("mood", 72) / 100 * 0.5)
                class_income += fill * ct["rev"] * fit_m * energy_f * mood_f
                teaching.add(ik)
                dd["energy"] = max(0, dd.get("energy", 100) - STUDIO_INSTR_ENERGY_COST)
                if ik != "gary": dd["mood"] = max(0, dd.get("mood", 72) - POLE_STUDIO_DANCERS[ik]["mood_decay"])
            for ik, dd in dancers.items():   # everyone rests overnight; one class/day is sustainable
                if dd.get("hired"):
                    dd["energy"] = min(100, dd.get("energy", 100) + STUDIO_INSTR_ENERGY_REGEN)

            # ── Multipliers ──
            cln_m = 0.6 + ps.get("cleanliness", 100) / 100 * 0.5
            atm_m = 0.7 + ps.get("atmosphere", 100) / 100 * 0.5
            rep_m = 0.7 + ps.get("reputation", 0) / 100 * 0.6
            sat_m = 0.7 + ps.get("satisfaction", 70) / 100 * 0.5
            class_income *= cln_m * atm_m * rep_m * sat_m

            # ── Kombucha bar (needs the facility, a bartender, and stock) ──
            bar_income = 0.0
            if facs.get("kombucha_bar") and bartender_on:
                kb = ps.setdefault("kombucha", {})
                stocked = [k for k in list(kb) if kb.get(k, 0) > 0]
                if stocked:
                    avg_inc = sum(COSTPRO_ITEMS[k].get("kb_income", 0.6) for k in stocked if k in COSTPRO_ITEMS) / len(stocked)
                    bar_income = attendance * avg_inc
                    for k in stocked: kb[k] -= 1
                    ps["satisfaction"] = min(100, ps.get("satisfaction", 70) + min(4, len(stocked)))

            # ── Gratuities (tips), recurring dues, total ──
            tips = class_income * STUDIO_GRATUITY_RATE * (ps.get("satisfaction", 70) / 100)
            dues = members * STUDIO_DUES_PER_MEMBER + vip * STUDIO_VIP_DUES
            income = round(dues + class_income + bar_income + tips)

            # ── Member dynamics: satisfaction, signups, churn, VIP, reputation ──
            overbook = daily_demand - capacity
            ds = 0
            if capacity <= 0: ds -= 3
            elif overbook > capacity * 0.15: ds -= 4
            if ps.get("cleanliness", 100) < 50: ds -= 3
            if ps.get("atmosphere", 100) < 45:  ds -= 1
            if facs.get("lobby"): ds += 1
            if host_on: ds += 2
            ds -= cancelled
            if cancelled == 0 and overbook <= 0 and ps.get("cleanliness", 100) >= 55 and ps.get("atmosphere", 100) >= 50:
                ds += 2   # a clean, well-run, roomy studio earns goodwill
            ps["satisfaction"] = max(0, min(100, ps.get("satisfaction", 70) + ds))
            spare   = max(0.0, capacity - daily_demand)
            signups = (0.6 + ps.get("reputation", 0) / 100 * 2.5) * (0.5 + min(1.0, spare / 8) * 0.7)
            signups += ps.pop("marketing_boost", 0)
            churn_rate = 0.008
            if ps.get("satisfaction", 70) < 40: churn_rate += 0.03
            if overbook > capacity * 0.15:       churn_rate += 0.025
            if ps.get("cleanliness", 100) < 40:  churn_rate += 0.015
            if host_on: churn_rate *= 0.6
            members = max(0.0, members + signups - members * churn_rate)
            ps["members"] = members
            if facs.get("vip_suite") and any(sl.get("type") == "private" and sl.get("_valid") for sl in active_slots):
                ps["vip_members"] = vip + max(0.0, (members * 0.03 - vip) * 0.1) + 0.2
            else:
                ps["vip_members"] = max(0.0, vip * 0.97)
            tgt = ps.get("satisfaction", 70)
            if ps.get("reputation", 0) < tgt and random.random() < 0.5:   ps["reputation"] = min(100, ps.get("reputation", 0) + 1)
            elif ps.get("reputation", 0) > tgt and random.random() < 0.3: ps["reputation"] = max(0, ps.get("reputation", 0) - 1)

            s["cash"]          += income
            ps["total_earned"]  = ps.get("total_earned", 0) + income
            _biz_income(s, "pole_studio", income)

        if random.random() < POLE_STUDIO_EVENT_CHANCE:
            if staff.get("manager"):
                # Studio Manager handles it — picks the sensible (first) option.
                _pcard   = random.choice(POLE_STUDIO_EVENT_CARDS)
                _pchoice = _pcard["choices"][0]
                _pres, _pbad = _pole_apply_event_choice(s, _pchoice)
                events.append({"prop": "The Studio", "type": "warning" if _pbad else "info",
                    "category": "pole_studio", "text": f"📋 Studio Manager handled “{_pcard['title']}” — {_pres}"})
                s["log"].insert(0, {"day": s["day"], "type": "info",
                    "text": f"Studio Manager resolved: {_pcard['title']}"})
            else:
                _qpe = _pole_queue_event(s)
                if _qpe: new_pole_events.append(_qpe)
        s["pole_studio"] = ps

    # ── Slippery When Washed advance ──────────────────────────────────────────
    cw = s.get("car_wash")
    if cw and cw.get("owned"):
        bays      = cw.setdefault("bays", [{"id": i, "upgrades": {}, "broken": False}
                                            for i in range(cw.get("bay_count", CAR_WASH_START_BAYS))])
        staff     = cw.setdefault("staff", {k: False for k in CAR_WASH_STAFF})
        g_upgs    = cw.setdefault("global_upgrades", {})
        sup       = cw.setdefault("supplies", {})
        cw.setdefault("members", 0)

        for _day in range(days):
            _cur = s["day"] + _day + 1
            # Weather drives the day's demand; carry a 1-day forecast for the UI.
            cw["weather"]  = cw.get("forecast") or _roll_car_wash_weather(_season_info(_cur)[0])
            cw["forecast"] = _roll_car_wash_weather(_season_info(_cur + 1)[0])
            wx = CAR_WASH_WEATHER[cw["weather"]]

            # Supply Manager (Carlos) auto-orders soap & wax to a buffer.
            if staff.get("carlos"):
                for _key, _buf, _price, _days, _needarch in [
                        ("cw_basic_soap", 12, 350, 7, False), ("cw_standard_soap", 10, 500, 10, False),
                        ("cw_premium_wax", 8, 700, 8, True)]:
                    if _needarch and not g_upgs.get("dryer_arch"):
                        continue
                    if sup.get(_key, 0) < _buf and s["cash"] >= _price:
                        s["cash"] -= _price; _tax_deduct(s, _price); sup[_key] = sup.get(_key, 0) + _days

            # Insurance weekly charge
            if cw.get("insurance"):
                cw["insurance_days"] = cw.get("insurance_days", 7) - 1
                if cw["insurance_days"] <= 0:
                    cw["insurance_days"] = 7
                    s["cash"] = max(0, s["cash"] - CAR_WASH_INSURANCE_WEEKLY)

            # Water pressure decay (slower with industrial tank)
            water_decay = CAR_WASH_WATER_DECAY * (0.4 if g_upgs.get("water_tank") else 1.0)
            cw["water_pressure"] = max(0, cw.get("water_pressure", 100) - water_decay)
            # Manny keeps the pumps primed — water pressure stays pegged near 100.
            if staff.get("manny"):
                cw["water_pressure"] = min(100, cw.get("water_pressure", 100) + 25)

            # Equipment decay per bay
            for bay in bays:
                if bay.get("broken"):
                    if staff.get("manny"):
                        bay["broken"] = False
                        bay["condition"] = min(100, bay.get("condition", 0) + 10)
                else:
                    bd = CAR_WASH_BREAKDOWN_PCT * (0.5 if bay.get("upgrades", {}).get("nozzles") else 1.0)
                    if random.random() < bd:
                        bay["broken"] = True
                    decay = CAR_WASH_EQUIP_DECAY * (0.5 if bay.get("upgrades", {}).get("nozzles") else 1.0)
                    bay["condition"] = max(0, bay.get("condition", 100) - decay)
                    if staff.get("manny"):
                        bay["condition"] = min(100, bay.get("condition", 100) + 5)

            # Morale decay
            morale_decay = CAR_WASH_MORALE_DECAY
            if staff.get("brianna"): morale_decay = max(1, morale_decay - 2)
            if staff.get("terry"):   morale_decay = max(1, morale_decay - 1)
            cw["morale"] = max(0, cw.get("morale", 80) - morale_decay)

            # Staff daily costs
            for role, hired in staff.items():
                if hired:
                    s["cash"] = max(0, s["cash"] - CAR_WASH_STAFF[role]["cost"])
                    _tax_deduct(s, CAR_WASH_STAFF[role]["cost"])

            # No basic soap = closed (regulars drift off)
            if sup.get("cw_basic_soap", 0) <= 0:
                cw["regulars"] = max(0, cw.get("regulars", 0) - 3)
                continue
            sup["cw_basic_soap"] -= 1

            members  = cw.get("members", 0)
            regulars = cw.get("regulars", 0)
            has_kiosk = bool(g_upgs.get("membership_kiosk"))

            # ── Demand (weather-driven walk-ins + members) vs. throughput (bays) ──
            walk_in = (CAR_WASH_BASE_DEMAND + regulars * 0.6) * wx["demand"] * (1 + random.uniform(-0.1, 0.1))
            member_visits = (members * CAR_WASH_MEMBER_VISITS) if has_kiosk else 0
            demand = walk_in + member_visits

            working_bays = [b for b in bays if not b.get("broken")]
            cap = 0.0
            for bay in working_bays:
                u = bay.get("upgrades", {})
                speed = 1.0 + (0.5 if u.get("conveyor") else 0) + (0.15 if u.get("nozzles") else 0)
                cap += CAR_WASH_BAY_CAPACITY * speed
            if staff.get("brianna"): cap *= 1.2          # flow optimization
            if staff.get("squeegee_kid") and random.random() >= 0.65 \
               and not any(b.get("upgrades", {}).get("conveyor") for b in working_bays):
                cap *= 0.85                              # the Kid no-showed
            cap *= 0.5 + cw.get("water_pressure", 100) / 100 * 0.5   # low water = slower

            cars       = min(demand, cap)
            turn_aways = max(0, demand - cap)

            # ── Revenue: cars × avg price from the package mix, then quality mults ──
            avg_price = _car_wash_avg_price(cw)
            income = cars * avg_price
            # consume one unit of each offered upper-tier supply per operating day
            if sup.get("cw_standard_soap", 0) > 0: sup["cw_standard_soap"] -= 1
            if sup.get("cw_premium_wax", 0) > 0 and g_upgs.get("dryer_arch"): sup["cw_premium_wax"] -= 1
            avg_cond = (sum(b.get("condition", 100) for b in working_bays) / len(working_bays)) if working_bays else 0
            income *= 0.6 + avg_cond / 100 * 0.4                       # equipment condition
            income *= 0.6 + cw.get("morale", 80) / 100 * 0.5          # crew morale
            if staff.get("dave"): income *= 1.12                      # Dave's vacuums
            if sup.get("cw_tire_shine", 0) > 0:
                income *= 1.15; sup["cw_tire_shine"] = max(0, sup["cw_tire_shine"] - 1)
            if sup.get("cw_air_freshener", 0) > 0:
                cw["regulars"] = min(100, cw.get("regulars", 0) + 0.1)
            income *= 0.7 + cw.get("reputation", 0) / 100 * 0.8       # reputation
            income = round(income)
            if has_kiosk:
                income += round(members * CAR_WASH_MEMBER_DUES)       # recurring dues

            # ── Turn-aways hurt: long lines bleed regulars & reputation ──
            if cap > 0 and turn_aways > cap * 0.15:
                cw["regulars"] = max(0, cw.get("regulars", 0) - 1)
                if random.random() < 0.3:
                    cw["reputation"] = max(0, cw.get("reputation", 0) - 1)

            # ── Membership growth/churn (Wash Club) ──
            if has_kiosk:
                grow  = (cw.get("reputation", 0) / 100) * 1.6 * (1.0 if turn_aways < cap * 0.15 else 0.3)
                churn = members * (0.01 + (0.03 if (cap > 0 and turn_aways > cap * 0.15) else 0))
                cw["members"] = max(0, members + grow - churn)

            # ── Regulars slow build + reputation drift ──
            if turn_aways < cap * 0.1 and random.random() < 0.35:
                cw["regulars"] = min(100, cw.get("regulars", 0) + 2)
            if random.random() < 0.25 and g_upgs.get("loyalty_machine"):
                cw["regulars"] = min(100, cw.get("regulars", 0) + 2)
            if cw.get("reputation", 0) > 60 and random.random() < 0.15:
                cw["reputation"] = max(0, cw["reputation"] - 1)

            cw["last_cars"] = round(cars); cw["last_turnaways"] = round(turn_aways)   # for the UI
            s["cash"]         += income
            cw["total_earned"] = cw.get("total_earned", 0) + income
            _biz_income(s, "car_wash", income)

        # One car-wash choice-card event may fire per advance, at a low chance.
        if random.random() < CAR_WASH_EVENT_CHANCE:
            if staff.get("diane"):
                # General Manager handles it — picks the sensible (first) option.
                _card   = random.choice(CAR_WASH_EVENT_CARDS)
                _choice = _card["choices"][0]
                _res, _bad = _car_wash_apply_event_choice(s, _choice)
                events.append({"prop": "Slippery When Washed", "type": "warning" if _bad else "info",
                    "category": "car_wash", "text": f"🗂️ Diane handled “{_card['title']}” — {_res}"})
                s["log"].insert(0, {"day": s["day"], "type": "info",
                    "text": f"Car wash GM resolved: {_card['title']}"})
            else:
                _qcw = _car_wash_queue_event(s)
                if _qcw:
                    new_car_wash_events.append(_qcw)
        s["car_wash"] = cw

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
            events.append({"prop": rs["prop"], "text": txt, "type": etype,
                           "category": "rent", "amount": rs["collected"]})

    # ── New Builds tick ──────────────────────────────────────────────
    active_builds     = s.get("active_builds", [])
    completed_ids     = []
    for build in active_builds:
        if build.get("paused"):
            continue
        crew_key  = build.get("crew")
        crew      = BUILD_CREWS.get(crew_key, BUILD_CREWS["handys"])
        daily_pay = crew["daily_rate"] * days
        s["cash"] = max(0, s["cash"] - daily_pay)
        build["days_remaining"] = max(0, build.get("days_remaining", 1) - days)
        build["total_crew_paid"] = build.get("total_crew_paid", 0) + daily_pay
        if build["days_remaining"] <= 0:
            completed_ids.append(build["id"])
            prop = _complete_new_build(s, build)
            events.append({"prop": "Cedarvale Estates",
                           "text": f"Build complete! Your {NEW_BUILD_SIZES[build['size']]['name']} at {prop['address']} is ready.",
                           "type": "positive", "category": "build"})
    s["active_builds"] = [b for b in active_builds if b["id"] not in completed_ids]

    # ── Assistant auto-resolution ─────────────────────────────────────────────
    hired = s.get("assistants", {})

    if hired.get("manager"):
        auto_handled = []
        for repair in new_repairs:
            prop = next((p for p in s["properties"] if p["id"] == repair["prop_id"]), None)
            if not prop:
                auto_handled.append(repair)
                continue
            sc = next((r for r in REPAIR_SCENARIOS if r["key"] == repair.get("key")), None)
            if not sc:
                auto_handled.append(repair)
                continue
            # Pick the best (highest-cost) proactive fix the budget allows; skip "ignore".
            affordable = [c for c in sc["choices"] if c.get("cost", 0) <= s["cash"]]
            if affordable:
                choice    = max(affordable, key=lambda c: c.get("cost", 0))
                cost      = choice.get("cost", 0)
                cond_gain = choice.get("cond", 0)
                s["cash"] -= cost
                prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_gain))
                if prop.get("tenant"):
                    mdelta = max(0, choice.get("morale", 0)) + 3
                    prop["tenant"]["morale"] = min(100, prop["tenant"].get("morale", 50) + mdelta)
                if cost > 0:
                    prop["total_repair_costs"] = prop.get("total_repair_costs", 0) + cost
                s["log"].insert(0, {"day": s["day"] + days, "type": "renovate",
                    "text": f"🔧 Assistant handled '{sc['title']}' at {prop['type']} in {prop['neighborhood']} — {choice['label']} (cost ${cost:,})"})
                events.append({"prop": f"{prop['type']} — {prop['neighborhood']}", "type": "info",
                    "text": f"🔧 Assistant: {sc['title']} — {choice['label']} (cost ${cost:,})"})
                auto_handled.append(repair)
        new_repairs = [r for r in new_repairs if r not in auto_handled]

    # Property Manager auto-resolves tenant storylets (the story system).
    if hired.get("manager"):
        resolve_day = s["day"] + days
        def _sl_cash_cost(c, t):
            cc = c.get("cost", {})
            return cc.get("cash", 0) + int(t.get("rent", 0)) * cc.get("cash_weeks", 0)
        def _sl_score(c, t):
            o = c.get("outcome", {})
            return (o.get("morale", 0) + o.get("loyalty", 0) + o.get("condition", 0)
                    + o.get("cash", 0) / 200.0 - _sl_cash_cost(c, t) / 200.0)
        auto_handled_s = []
        for sev in new_storylet_events:
            prop = next((p for p in s["properties"] if p["id"] == sev["prop_id"]), None)
            if not prop or not prop.get("tenant"):
                auto_handled_s.append(sev); continue
            t     = prop["tenant"]
            st    = t.get("storylet")
            sl    = STORYLETS.get(sev["storylet_id"])
            stage = sl["stages"].get(sev["stage"]) if sl else None
            if not st or not sl or not stage or stage.get("auto"):
                auto_handled_s.append(sev); continue
            affordable = [c for c in stage["choices"] if _sl_cash_cost(c, t) <= s["cash"]]
            # Prefer choices that don't make the tenant leave; fall back if those are all we can afford.
            pool = [c for c in affordable if not c.get("outcome", {}).get("leave")] or affordable
            if not pool:
                continue   # can't afford any option — leave it for the player to decide
            choice = max(pool, key=lambda c: _sl_score(c, t))
            s["cash"] -= _sl_cash_cost(choice, t)
            st["due_day"] = resolve_day
            _apply_storylet_outcome(s, prop, t, choice["outcome"], resolve_day)
            result = choice["outcome"].get("result", "Handled.")
            s["log"].insert(0, {"day": resolve_day, "type": "info",
                "text": f"📖 Assistant handled '{sl['title']}' at {prop['type']} in {prop['neighborhood']} — {choice['label']}"})
            events.append({"prop": f"{prop['type']} — {prop['neighborhood']}", "type": "info",
                "text": f"📖 Assistant: {sl['title']} — {result}"})
            auto_handled_s.append(sev)
        new_storylet_events = [e for e in new_storylet_events if e not in auto_handled_s]

    # Property Manager auto-renews lease offers at the current rent (keeps the tenant).
    if hired.get("manager"):
        renew_day = s["day"] + days
        auto_handled_rn = []
        for offer in new_renewal_offers:
            prop = next((p for p in s["properties"] if p["id"] == offer["prop_id"]), None)
            if not prop or not prop.get("tenant"):
                auto_handled_rn.append(offer); continue
            t = prop["tenant"]
            new_stay = t.get("renewal_stay_days", offer.get("new_stay_days", 120))
            t["lease_end_day"]   = renew_day + new_stay
            t["renewal_pending"] = False
            t.pop("renewal_stay_days", None)
            t.pop("renewal_odds", None)
            t["renewals"]   = t.get("renewals", 0) + 1
            t["loyalty"]    = min(100, t.get("loyalty", 10) + 15)
            t["pay_chance"] = min(0.99, t.get("pay_chance", 0.9) + 0.01)
            s["log"].insert(0, {"day": renew_day, "type": "rent",
                "text": f"🤝 Assistant renewed {t['name']} at {prop['type']} in {prop['neighborhood']} — ${t['rent']:,}/wk, {new_stay} more days"})
            events.append({"prop": f"{prop['type']} — {prop['neighborhood']}", "type": "info",
                "text": f"🤝 Assistant renewed {t['name']}'s lease — ${t['rent']:,}/wk"})
            auto_handled_rn.append(offer)
        new_renewal_offers = [o for o in new_renewal_offers if o not in auto_handled_rn]

    _update_stock_prices(s, days)
    _final_day = s["day"] + days
    _div_ev = _pay_dividends(s, _final_day)
    if _div_ev:
        events.append(_div_ev)
    _news_ev = _maybe_stock_news(s)
    if _news_ev:
        events.append(_news_ev)
    _roll_special_contractors(s)
    s["applicants_cache"] = {}   # fresh tenant pool each advance
    s["day"] += days
    for _m in _sync_milestones(s):   # award newly-completed milestones (recap)
        _mr = MILESTONE_REWARD.get(_m["key"], 0)
        events.append({"type": "positive", "category": "milestone",
            "text": f"🏅 Milestone: {_m['name']} — {_m['desc']}" + (f" (+${_mr:,})" if _mr else "")})
    _update_mogul_rank(s, events)    # celebrate any rank-ups
    save(s)
    return jsonify({
        "success":   True,
        "day":       s["day"],
        "cash":      s["cash"],
        "net_worth": s["cash"] + sum(calc_market_value(p) for p in s["properties"]),
        "events":             events,
        "repairs":            new_repairs,
        "storylet_events":    new_storylet_events,
        "vending_events":     new_vending_events,
        "arcade_events":      new_arcade_events,
        "pole_events":        new_pole_events,
        "car_wash_events":    new_car_wash_events,
        "renewal_offers":     new_renewal_offers,
        "commercial_events":  new_commercial_events,
        "tax_event":          tax_event,
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
    s  = load()
    tx = _compute_taxes(s)
    s["cash"] -= tx["total"]
    s["log"].insert(0, {"day": s["day"], "type": "warning",
        "text": f"Paid ${tx['total']:,} in taxes (rent ${tx['rent_tax']:,} + business/flips ${tx['active_tax']:,})"})
    _reset_tax_year(s)
    save(s)
    return jsonify({"success": True, "tax_paid": tx["total"], "cash": s["cash"]})


@app.route('/api/file_tax_extension', methods=['POST'])
def api_file_tax_extension():
    s  = load()
    tx = _compute_taxes(s)
    s["tax_extension_filed"] = True
    s["tax_owed"]            = tx["total"]
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Filed tax extension — ${tx['total']:,} due on Spring Day 7"})
    save(s)
    return jsonify({"success": True, "tax_owed": tx["total"], "cash": s["cash"]})


def _renewal_odds(t):
    """Acceptance probability for a rent increase at renewal, per raise % tier."""
    morale   = t.get("morale", 50)
    loyalty  = t.get("loyalty", 10)
    tier_pen = {"Very High": 0.40, "High": 0.20}.get(t.get("rent_tier", "Average"), 0.0)
    penny    = t.get("trait") == "penny"
    base = {5: 0.85, 10: 0.65, 15: 0.45}
    odds = {}
    for pct, b in base.items():
        p = b + (morale - 50) / 250 + loyalty / 350 - tier_pen - (0.30 if penny else 0.0)
        odds[str(pct)] = round(max(0.05, min(0.97, p)), 2)
    return odds

@app.route('/api/property/<int:pid>/renewal_respond', methods=['POST'])
def api_renewal_respond(pid):
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == pid), None)
    if not prop or not prop.get("tenant") or not prop["tenant"].get("renewal_pending"):
        return jsonify({"error": "No pending renewal for this property"}), 400

    t        = prop["tenant"]
    action   = data.get("action") or ("renew" if data.get("agree") else "decline")  # back-compat
    new_stay = t.get("renewal_stay_days", random.randint(t.get("stay_min", 60), t.get("stay_max", 180)))

    def _leave(reason):
        name = t["name"]
        for flag, ckey, mult in (("is_phil", "phil_cooldown_until", 4), ("is_baileys", "baileys_cooldown_until", 2),
                                  ("is_goldbergs", "goldbergs_cooldown_until", 2), ("is_mystery", "mystery_cooldown_until", 2)):
            if t.get(flag): s[ckey] = s["day"] + DAYS_PER_SEASON * mult
        prop["tenant"]       = None
        prop["vacant_since"] = s["day"]
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"{name} moved out of {prop['type']} in {prop['neighborhood']} — {reason}"})

    def _renew(label, extra_days=0):
        t["lease_end_day"]   = s["day"] + new_stay + extra_days
        t["renewal_pending"] = False
        t.pop("renewal_stay_days", None)
        t.pop("renewal_odds", None)
        t["renewals"]   = t.get("renewals", 0) + 1
        t["pay_chance"] = min(0.99, t.get("pay_chance", 0.9) + 0.01)  # tenure → reliability
        s["log"].append({"day": s["day"], "type": "rent",
            "text": f"{t['name']} renewed at {prop['type']} in {prop['neighborhood']} — {label}, {new_stay + extra_days} more days"})

    if action == "renew":
        t["loyalty"] = min(100, t.get("loyalty", 10) + 15)
        _renew(f"${t['rent']:,}/wk")
        outcome = "renewed"
    elif action == "discount":
        t["rent"]    = max(1, int(round(t["rent"] * 0.95)))
        t["morale"]  = min(100, t.get("morale", 50) + 8)
        t["loyalty"] = min(100, t.get("loyalty", 10) + 25)
        t["rent_tier"] = rent_tier(t["rent"], calc_fair_weekly_rent(prop))["tier"]
        _renew(f"${t['rent']:,}/wk (-5% retention)", extra_days=int(new_stay * 0.4))
        outcome = "discounted"
    elif action == "raise":
        pct  = int(data.get("pct", 5))
        odds = (t.get("renewal_odds") or _renewal_odds(t)).get(str(pct), 0.5)
        if random.random() < odds:
            t["rent"]      = int(round(t["rent"] * (1 + pct / 100)))
            t["rent_tier"] = rent_tier(t["rent"], calc_fair_weekly_rent(prop))["tier"]
            t["morale"]    = max(0, t.get("morale", 50) - 8)
            t["loyalty"]   = min(100, t.get("loyalty", 10) + 5)
            _renew(f"+{pct}% to ${t['rent']:,}/wk")
            outcome = "raise_accepted"
        elif t.get("trait") == "penny":
            # Penny pinchers grumble but won't actually walk over rent
            t["morale"]  = max(0, t.get("morale", 50) - 5)
            t["loyalty"] = min(100, t.get("loyalty", 10) + 5)
            _renew(f"held at ${t['rent']:,}/wk (rejected the raise)")
            outcome = "raise_rejected_stayed"
        else:
            t["renewal_pending"] = False
            _leave(f"rejected the +{pct}% increase")
            outcome = "raise_rejected_left"
    else:  # decline
        t["renewal_pending"] = False
        _leave("you chose not to renew")
        outcome = "declined"

    save(s)
    return jsonify({"success": True, "outcome": outcome,
                    "rent": (prop.get("tenant") or {}).get("rent"),
                    "tenant_name": t.get("name")})


@app.route('/api/storylet/respond', methods=['POST'])
def api_storylet_respond():
    s    = load()
    data = request.json or {}
    prop = next((p for p in s["properties"] if p["id"] == data.get("prop_id")), None)
    if not prop or not prop.get("tenant"):
        return jsonify({"error": "No tenant here"}), 404
    t  = prop["tenant"]
    st = t.get("storylet")
    if not st:
        return jsonify({"error": "No active storylet"}), 400
    sl    = STORYLETS.get(st["id"])
    stage = sl["stages"].get(st["stage"]) if sl else None
    if not stage or stage.get("auto"):
        return jsonify({"error": "Not awaiting a choice"}), 400
    idx = int(data.get("choice_idx", -1))
    if idx < 0 or idx >= len(stage["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    choice = stage["choices"][idx]

    # Validate + charge any cost
    cost      = choice.get("cost", {})
    cash_cost = cost.get("cash", 0) + int(t.get("rent", 0)) * cost.get("cash_weeks", 0)
    if cash_cost > s["cash"]:
        return jsonify({"error": f"Need ${cash_cost:,} for that"}), 400
    s["cash"] -= cash_cost

    st["due_day"] = s["day"]
    outcome = choice["outcome"]
    _apply_storylet_outcome(s, prop, t, outcome, s["day"])
    result = outcome.get("result", "Done.")
    s["log"].append({"day": s["day"], "type": "info", "text": f"{sl['title']} — {result}"})

    # XP for engaging with a tenant storylet (ported from the old request system).
    # Scales with the positive impact of the choice; always at least 1 for responding.
    pos      = max(0, outcome.get("morale", 0)) + max(0, outcome.get("loyalty", 0)) + max(0, outcome.get("condition", 0))
    xp_gain  = max(1, pos // 5)
    level_up = add_xp(s, xp_gain)

    save(s)
    return jsonify({"success": True, "result": result, "left": prop.get("tenant") is None,
                    "xp_gain": xp_gain, "level_up": level_up, "new_level": s.get("level", 0)})


# ── Bank Routes ────────────────────────────────────────────────────────────────

@app.route('/api/bank/products', methods=['GET', 'POST'])
def api_bank_products():
    s     = load()
    score = credit_score(s)
    products = [loan_offer(p, score) for p in LOAN_PRODUCTS]
    return jsonify({"products": products, "savings_tiers": SAVINGS_TIERS,
                    "credit_score": score, "credit_label": credit_label(score),
                    "cd_terms": CD_TERMS, "cd_min": CD_MIN_DEPOSIT,
                    "cd_penalty_pct": CD_EARLY_PENALTY_PCT})

@app.route('/api/bank/loan/preview', methods=['POST'])
def api_loan_preview():
    data    = request.json
    s       = load()
    product = next((p for p in LOAN_PRODUCTS if p["key"] == data["product_key"]), None)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    score   = credit_score(s)
    eapr    = effective_apr(product, score)
    emax    = effective_max(product, score)
    amount  = int(data["amount"])
    if amount < product["min"] or amount > emax:
        return jsonify({"error": f"Amount must be between ${product['min']:,} and ${emax:,}"}), 400
    payment     = calc_weekly_payment(amount, eapr, product["term_seasons"])
    term_weeks  = product["term_seasons"] * 4
    total       = round(payment * term_weeks, 2)
    return jsonify({"weekly_payment": payment, "total_repaid": total,
                    "total_interest": round(total - amount, 2), "term_seasons": product["term_seasons"],
                    "term_weeks": term_weeks, "effective_apr": eapr, "effective_max": emax})

@app.route('/api/bank/loan/take', methods=['POST'])
def api_loan_take():
    data    = request.json
    s       = load()
    product = next((p for p in LOAN_PRODUCTS if p["key"] == data["product_key"]), None)
    if not product:
        return jsonify({"error": "Invalid product"}), 400
    score = credit_score(s)
    if score < product["min_score"]:
        return jsonify({"error": f"Your credit score ({score}) is too low — need {product['min_score']} for this loan."}), 400
    eapr   = effective_apr(product, score)
    emax   = effective_max(product, score)
    amount = int(data["amount"])
    if amount < product["min"] or amount > emax:
        return jsonify({"error": f"Amount must be between ${product['min']:,} and ${emax:,} at your credit score."}), 400
    _bank(s)
    payment      = calc_weekly_payment(amount, eapr, product["term_seasons"])
    term_weeks   = product["term_seasons"] * 4
    term_seasons = product["term_seasons"]
    loan = {"id": s["bank"]["next_loan_id"], "product": product["name"], "product_key": product["key"],
            "icon": product["icon"], "balance": amount, "original_amount": amount,
            "weekly_payment": payment, "weekly_rate": eapr / 52, "apr": eapr,
            "term_seasons": term_seasons, "term_weeks": term_weeks, "weeks_paid": 0, "missed": 0}
    s["bank"]["next_loan_id"] += 1
    s["bank"]["loans"].append(loan)
    s["cash"] += amount
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Took out a {product['name']} for ${amount:,} @ {eapr*100:.1f}% APR — ${payment:,.2f}/wk for {term_seasons} seasons"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "loan": loan})

@app.route('/api/bank/loan/refinance', methods=['POST'])
def api_loan_refinance():
    data    = request.json or {}
    s       = load()
    loan    = next((l for l in _bank(s)["loans"] if l["id"] == data.get("loan_id")), None)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404
    product = next((p for p in LOAN_PRODUCTS if p["key"] == loan.get("product_key")), None) \
              or next((p for p in LOAN_PRODUCTS if p["name"] == loan.get("product")), None)
    if not product:
        return jsonify({"error": "This loan can't be refinanced."}), 400
    score    = credit_score(s)
    new_apr  = effective_apr(product, score)
    cur_apr  = loan.get("apr", round(loan.get("weekly_rate", 0) * 52, 4))
    if new_apr >= cur_apr - 0.0001:
        return jsonify({"error": f"Your credit doesn't earn a better rate yet (current {cur_apr*100:.1f}% APR). Build your score first."}), 400
    fee = max(50, int(round(loan["balance"] * CREDIT_REFINANCE_FEE_PCT)))
    if s["cash"] < fee:
        return jsonify({"error": f"Need ${fee:,} for the refinance fee."}), 400
    remaining_weeks   = max(4, loan.get("term_weeks", 8) - loan.get("weeks_paid", 0))
    remaining_seasons = remaining_weeks / 4
    new_payment = calc_weekly_payment(loan["balance"], new_apr, remaining_seasons)
    s["cash"]            -= fee
    loan["apr"]           = new_apr
    loan["weekly_rate"]   = new_apr / 52
    loan["weekly_payment"] = new_payment
    loan["term_weeks"]    = remaining_weeks
    loan["term_seasons"]  = round(remaining_seasons, 2)
    loan["weeks_paid"]    = 0
    loan["refinanced"]    = True
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Refinanced your {loan['product']} to {new_apr*100:.1f}% APR (fee ${fee:,}) — now ${new_payment:,.2f}/wk."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "new_apr": new_apr, "fee": fee, "loan": loan})

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
    paid_off = loan["balance"] <= 0
    if paid_off:
        s["bank"]["loans"] = [l for l in s["bank"]["loans"] if l["id"] != loan["id"]]
        _credit_adjust(s, CREDIT_PAYOFF_BONUS)
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"Fully paid off your {loan['product']}! Credit score +{CREDIT_PAYOFF_BONUS}."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "remaining": max(0, loan.get("balance", 0)),
                    "paid_off": paid_off, "credit_score": credit_score(s)})

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

@app.route('/api/bank/cd/open', methods=['POST'])
def api_cd_open():
    data = request.json or {}
    s    = load()
    term = next((t for t in CD_TERMS if t["key"] == data.get("term_key")), None)
    if not term:
        return jsonify({"error": "Invalid CD term"}), 400
    amount = int(data.get("amount", 0))
    if amount < CD_MIN_DEPOSIT:
        return jsonify({"error": f"Minimum deposit is ${CD_MIN_DEPOSIT:,}"}), 400
    if amount > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    bank = _bank(s)
    bank.setdefault("cds", []); bank.setdefault("next_cd_id", 1)
    s["cash"]  -= amount
    mature_day  = s["day"] + term["term_seasons"] * 28
    payout      = int(round(amount * (1 + term["yield"])))
    cd = {"id": bank["next_cd_id"], "name": term["name"], "principal": amount,
          "term_seasons": term["term_seasons"], "yield": term["yield"],
          "open_day": s["day"], "mature_day": mature_day, "payout": payout}
    bank["next_cd_id"] += 1
    bank["cds"].append(cd)
    s["log"].append({"day": s["day"], "type": "info",
        "text": f"Opened a {term['name']}: ${amount:,} locked, matures to ${payout:,} in {term['term_seasons']} season(s)."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "cd": cd})

@app.route('/api/bank/cd/withdraw', methods=['POST'])
def api_cd_withdraw():
    data = request.json or {}
    s    = load()
    bank = _bank(s)
    cd   = next((c for c in bank.get("cds", []) if c["id"] == data.get("cd_id")), None)
    if not cd:
        return jsonify({"error": "CD not found"}), 404
    if s["day"] >= cd.get("mature_day", 0):
        payout, penalty, early = cd["payout"], 0, False   # matured — full payout
    else:
        penalty = int(round(cd["principal"] * CD_EARLY_PENALTY_PCT))
        payout  = cd["principal"] - penalty               # forfeit interest + penalty
        early   = True
    s["cash"] += payout
    bank["cds"] = [c for c in bank["cds"] if c["id"] != cd["id"]]
    s["log"].append({"day": s["day"], "type": "warning" if early else "info",
        "text": (f"Cashed out {cd['name']} early — ${payout:,} (forfeited interest + ${penalty:,} penalty)."
                 if early else f"{cd['name']} cashed out at maturity — ${payout:,}.")})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "payout": payout, "penalty": penalty, "early": early})

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
    energy_cost = diy_energy_cost(prop, upg.get("energy_cost", 1))
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

@app.route('/api/repair/resolve', methods=['POST'])
def api_repair_resolve():
    """Resolve a repair scenario by the player's chosen handling option."""
    data = request.json
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == data["prop_id"]), None)
    if not prop:
        return jsonify({"error": "Not found"}), 404
    sc = next((r for r in REPAIR_SCENARIOS if r["key"] == data["repair_key"]), None)
    if not sc:
        return jsonify({"error": "Invalid repair"}), 400

    choices = _repair_choices(sc)
    try:
        idx = int(data["choice_idx"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid choice"}), 400
    if idx < 0 or idx >= len(choices):
        return jsonify({"error": "Invalid choice"}), 400
    choice = choices[idx]

    cost = int(choice.get("cost", 0))
    if cost > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400

    cond_delta   = choice.get("cond", 0)
    morale_delta = choice.get("morale", 0)
    loyalty_delta = choice.get("loyalty", 0)
    result = choice.get("result", "")
    bad    = False
    risk   = choice.get("risk")
    if risk and random.random() < risk.get("chance", 0):
        cond_delta   += risk.get("cond", 0)
        morale_delta += risk.get("morale", 0)
        result        = risk.get("result_bad", result)
        bad           = True

    if cost:
        s["cash"] -= cost
        prop["total_repair_costs"] = prop.get("total_repair_costs", 0) + cost
    prop["condition"] = max(0, min(MAX_CONDITION, prop["condition"] + cond_delta))
    morale_after = None
    if prop.get("tenant"):
        morale_after = max(0, min(100, prop["tenant"].get("morale", 50) + morale_delta))
        prop["tenant"]["morale"] = morale_after
        if loyalty_delta:
            prop["tenant"]["loyalty"] = max(0, min(100, prop["tenant"].get("loyalty", 10) + loyalty_delta))

    result = _fmt_sl(result, prop.get("tenant") or {}, prop)
    log_type = "warning" if choice.get("ignore") else "renovate"
    s["log"].append({"day": s["day"], "type": log_type,
        "text": f"{sc['title']} at {prop['type']} in {prop['neighborhood']} — {choice['label']}"
                + (f" (${cost:,})" if cost else "")})
    save(s)
    return jsonify({"success": True, "result": result, "bad": bad,
                    "condition": prop["condition"], "cost": cost, "cash": s["cash"],
                    "morale": morale_after})


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
    # ── Dark-only codes — only redeemable while you're off the books ────────────
    if code in DARK_CREATOR_CODES:
        if s.get("mode") != "dark":
            return jsonify({"error": "Invalid code — try again!"}), 400   # stays secret in the legit game
        rw = DARK_CREATOR_CODES[code]; d = s.setdefault("dark", {})
        if rw.get("reset"):   # reusable dev resets — skip the one-time-use guard
            if rw["reset"] == "heists":
                d["heists_done"] = []; d["heist"] = None; d["heist_crew"] = []; d["next_heist_member"] = 1
            s["log"].insert(0, {"day": s["day"], "type": "info", "text": f"Dark code — {rw['desc']}"})
            save(s)
            return jsonify({"success": True, "reward_desc": rw["desc"]})
        if code in s.get("redeemed_codes", []):
            return jsonify({"error": "Code already used!"}), 400
        if "cred" in rw:
            d["cred"] = rw["cred"]; d["cred_xp"] = rw.get("xp", d.get("cred_xp", 0))
        if "dirty" in rw:
            d["dirty_money"] = d.get("dirty_money", 0) + rw["dirty"]
        if "cash" in rw:
            s["cash"] = s.get("cash", 0) + rw["cash"]
        s.setdefault("redeemed_codes", []).append(code)
        s["log"].insert(0, {"day": s["day"], "type": "info", "text": f"Dark code — {rw['desc']}"})
        save(s)
        return jsonify({"success": True, "reward_desc": rw["desc"]})
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
    unlock_level = item.get("unlock_level", 0)
    if unlock_level > 0 and s.get("level", 0) < unlock_level:
        return jsonify({"error": f"Unlocks at Level {unlock_level}"}), 400
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
            "tier":     info.get("tier", "stock"),
            "dividend": info.get("dividend", 0),
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

def _vm_new_machine(s, slot, loc_key):
    return {
        "id":           int(s["day"] * 1000 + slot),
        "slot":         slot,
        "location_key": loc_key,
        "slots":        _vm_blank_slots(),
        "reputation":   70,
        "price_level":  "normal",
        "upgrades":     {},
    }

@app.route('/api/vending/buy', methods=['POST'])
def api_vending_buy():
    s    = load()
    vms  = s.setdefault("vending_machines", [])
    # Only the 6 market locations are buyable here; the laundromat & arcade machines are extra.
    market = [v for v in vms if v.get("location_key") in VM_LOCATION_ORDER]
    if len(market) >= 6:
        return jsonify({"error": "You already own the maximum of 6 market machines"}), 400
    slot     = len(market) + 1
    price    = VM_PRICES[slot - 1]
    loc_key  = VM_LOCATION_ORDER[slot - 1]
    if s["cash"] < price:
        return jsonify({"error": f"Not enough cash — need ${price:,}"}), 400
    s["cash"] -= price
    vms.append(_vm_new_machine(s, slot, loc_key))
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bought Vending Machine #{slot} at {VM_LOCATIONS[loc_key]['name']} for ${price:,}!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/configure', methods=['POST'])
def api_vending_configure():
    """Assign a product category to a slot (or clear it), then fill from inventory."""
    s    = load()
    data = request.json or {}
    vm   = next((v for v in s.get("vending_machines", []) if v["id"] == data.get("vm_id")), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    idx = int(data.get("slot_idx", -1))
    if idx < 0 or idx >= len(vm.get("slots", [])):
        return jsonify({"error": "Invalid slot"}), 400
    cat = data.get("category")
    sl  = vm["slots"][idx]
    if cat in (None, "", "none"):
        sl.update({"category": None, "stock": 0.0, "restock_day": 0})
        save(s); return jsonify({"success": True})
    if cat not in VM_PRODUCTS:
        return jsonify({"error": "Unknown product"}), 400
    cur = sl.get("category")
    # Can't swap product while stock remains — must clear it first (avoids accidental loss).
    if cur and cur != cat and sl.get("stock", 0) > 0.5:
        return jsonify({"error": "Clear the slot first — switching would dump the current product."}), 400
    if cur != cat:
        sl.update({"category": cat, "stock": 0.0})
    inv  = s.setdefault("costpro_inventory", {})
    need = _vm_capacity(vm) - sl.get("stock", 0)
    take = min(need, inv.get(cat, 0))
    if take > 0:
        sl["stock"] = sl.get("stock", 0) + take
        inv[cat]    = inv.get(cat, 0) - take
        sl["restock_day"] = s["day"]
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/restock', methods=['POST'])
def api_vending_restock():
    """Top every configured slot on a machine up to capacity from your inventory (free — your own labor)."""
    s    = load()
    data = request.json or {}
    vm   = next((v for v in s.get("vending_machines", []) if v["id"] == data.get("vm_id")), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    inv   = s.setdefault("costpro_inventory", {})
    moved = _vm_restock_from_inventory(vm, inv, s["day"])
    if moved <= 0:
        return jsonify({"error": "Nothing to restock — slots are full, unassigned, or you're out of stock."}), 400
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Restocked Machine #{vm['slot']} — {int(round(moved))} units topped up."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/toggle_vinny', methods=['POST'])
def api_vending_toggle_vinny():
    s = load()
    s["vinny_hired"] = not s.get("vinny_hired", False)
    save(s)
    return jsonify({"success": True, "vinny_hired": s["vinny_hired"]})

@app.route('/api/vending/set_price', methods=['POST'])
def api_vending_set_price():
    s    = load()
    data = request.json or {}
    vm   = next((v for v in s.get("vending_machines", []) if v["id"] == data.get("vm_id")), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    level = data.get("level")
    if level not in VM_PRICE_LEVELS:
        return jsonify({"error": "Invalid price level"}), 400
    vm["price_level"] = level
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/upgrade', methods=['POST'])
def api_vending_upgrade():
    s    = load()
    data = request.json or {}
    vm   = next((v for v in s.get("vending_machines", []) if v["id"] == data.get("vm_id")), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    key = data.get("upgrade_key")
    up  = VM_UPGRADES.get(key)
    if not up:
        return jsonify({"error": "Unknown upgrade"}), 400
    ups = vm.setdefault("upgrades", {})
    if ups.get(key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < up["cost"]:
        return jsonify({"error": f"Not enough cash — need ${up['cost']:,}"}), 400
    s["cash"] -= up["cost"]
    ups[key]   = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {up['name']} on Vending Machine #{vm['slot']} for ${up['cost']:,}."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/event_resolve', methods=['POST'])
def api_vending_event_resolve():
    s    = load()
    data = request.json or {}
    vm   = next((v for v in s.get("vending_machines", []) if v["id"] == data.get("machine_id")), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    ev = next((e for e in VM_EVENTS if e["key"] == data.get("event_key")), None)
    if not ev:
        return jsonify({"error": "Unknown event"}), 400
    idx = int(data.get("choice_idx", -1))
    if idx < 0 or idx >= len(ev["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    choice = ev["choices"][idx]
    if choice.get("cost", 0) > s["cash"]:
        return jsonify({"error": "Not enough cash for that"}), 400
    result, bad = _vm_apply_event_choice(s, vm, choice)
    s["log"].insert(0, {"day": s["day"], "type": "warning" if bad else "info",
        "text": f"{ev['title']} (Machine #{vm['slot']}) — {choice['label']}"})
    save(s)
    return jsonify({"success": True, "result": result, "bad": bad, "cash": s["cash"]})

@app.route('/api/vending/toggle_grandma', methods=['POST'])
def api_vending_toggle_grandma():
    s = load()
    s["grandma_hired"] = not s.get("grandma_hired", False)
    if s["grandma_hired"]:
        # First shop happens on the next advance (last_shop far enough back).
        s["grandma_last_shop"] = s["day"] - GRANDMA_INTERVAL
    save(s)
    return jsonify({"success": True, "grandma_hired": s["grandma_hired"]})

@app.route('/api/vending/set_grandma_budget', methods=['POST'])
def api_vending_set_grandma_budget():
    s    = load()
    data = request.json or {}
    s["grandma_budget"] = max(0, int(data.get("budget", 0)))
    save(s)
    return jsonify({"success": True, "grandma_budget": s["grandma_budget"]})

@app.route('/api/costpro/buy', methods=['POST'])
def api_costpro_buy():
    s    = load()
    data = request.json or {}
    key  = data.get("item_key", "")
    qty  = int(data.get("qty", 1))
    item = COSTPRO_ITEMS.get(key)
    if not item:
        return jsonify({"error": "Unknown item"}), 400
    if qty not in (1, 3, 5):
        return jsonify({"error": "Invalid quantity — choose 1, 3, or 5"}), 400
    total = item["price"] * qty
    if s["cash"] < total:
        return jsonify({"error": f"Not enough cash — need ${total:,}"}), 400
    s["cash"] -= total
    _tax_deduct(s, total)   # supplies are a deductible business expense
    if item.get("category") == "laundromat":
        lm = s.get("laundromat")
        if not lm:
            s["cash"] += total   # refund
            return jsonify({"error": "You don't own the Dirty Money Laundromat yet!"}), 400
        if key == "soap":
            has_ee        = any(m.get("upgrades", {}).get("energy_efficient") for m in lm.get("machines", []))
            days_per_case = 10 if has_ee else 7
            lm["soap_days"] = lm.get("soap_days", 0) + days_per_case * qty
        elif key == "softener":
            lm["softener_days"] = lm.get("softener_days", 0) + 10 * qty
        elif key == "sheets":
            lm["sheets_days"] = lm.get("sheets_days", 0) + 10 * qty
        s["laundromat"] = lm
    elif item.get("category") == "studio_bar":
        ps = s.get("pole_studio")
        if not ps:
            s["cash"] += total
            return jsonify({"error": "You don't own the studio yet!"}), 400
        if not ps.get("facilities", {}).get("kombucha_bar"):
            s["cash"] += total
            return jsonify({"error": "Install the Kombucha Bar first (Facilities)."}), 400
        kb = ps.setdefault("kombucha", {})
        kb[key] = kb.get(key, 0) + 10 * qty   # 10 days per keg
        s["pole_studio"] = ps
    elif item.get("category") == "car_wash":
        cw = s.get("car_wash")
        if not cw:
            s["cash"] += total
            return jsonify({"error": "You don't own Slippery When Washed yet!"}), 400
        sup = cw.setdefault("supplies", {})
        days_map = {"cw_basic_soap": 7, "cw_standard_soap": 10,
                    "cw_premium_wax": 8, "cw_tire_shine": 10, "cw_air_freshener": 12}
        sup[key] = sup.get(key, 0) + days_map.get(key, 7) * qty
        s["car_wash"] = cw
    elif item.get("category") == "arcade":
        arc = s.get("arcade")
        if not (arc and arc.get("unlocked")):
            s["cash"] += total   # refund
            return jsonify({"error": "You haven't opened the Back-Room Arcade yet!"}), 400
        arc["prizes"] = arc.get("prizes", 0) + item.get("units", 1) * qty
        s["arcade"] = arc
    else:
        # Vending supplies: each "case" adds `units` to the category's inventory.
        inv      = s.setdefault("costpro_inventory", {})
        inv[key] = inv.get(key, 0) + item.get("units", 1) * qty
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bought ×{qty} {item['name']} from CostPro for ${total:,}."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/buy', methods=['POST'])
def api_laundromat_buy():
    s = load()
    if s.get("laundromat"):
        return jsonify({"error": "Already owned"}), 400
    if s.get("level", 0) < 5:
        return jsonify({"error": "Unlocks at Level 5"}), 400
    if s["cash"] < LAUNDROMAT_PRICE:
        return jsonify({"error": f"Need ${LAUNDROMAT_PRICE:,}"}), 400
    s["cash"] -= LAUNDROMAT_PRICE
    # Starter: 2 washers + 2 dryers — balanced wash/dry to start.
    _starter_types = ["washer", "washer", "dryer", "dryer"]
    s["laundromat"] = {
        "owned":          True,
        "cleanliness":    20,
        "machines":       [{"id": i, "type": _starter_types[i], "status": "working", "upgrades": {}}
                           for i in range(LAUNDROMAT_START_MACHINES)],
        "soap_days":      0,
        "softener_days":  0,
        "sheets_days":    0,
        "staff":          {"janitor": False, "repairman": False},
        "regulars":       0,
        "members":        0,
        "addons":         {},
        "insurance":      False,
        "insurance_days": 0,
        "total_earned":   0,
    }
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Purchased Dirty Money Laundromat for ${LAUNDROMAT_PRICE:,}!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/buy_machine', methods=['POST'])
def api_laundromat_buy_machine():
    s  = load()
    lm = s.get("laundromat")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    machines = lm.get("machines", [])
    if len(machines) >= LAUNDROMAT_MAX_MACHINES:
        return jsonify({"error": f"Already at max {LAUNDROMAT_MAX_MACHINES} machines"}), 400
    mtype = (request.json or {}).get("machine_type", "washer")
    if mtype not in LAUNDROMAT_MACHINE_TYPES:
        return jsonify({"error": "Unknown machine type"}), 400
    step  = max(0, len(machines) - LAUNDROMAT_START_MACHINES) * LAUNDROMAT_MACHINE_STEP
    price = LAUNDROMAT_MACHINE_TYPES[mtype]["price"] + step
    if s["cash"] < price:
        return jsonify({"error": f"Need ${price:,}"}), 400
    s["cash"] -= price
    new_id = (max((m["id"] for m in machines), default=-1)) + 1
    machines.append({"id": new_id, "type": mtype, "status": "working", "upgrades": {}})
    lm["machines"] = machines
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Added a {LAUNDROMAT_MACHINE_TYPES[mtype]['name']} to the Dirty Money Laundromat for ${price:,}!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/arcade/buy_cabinet', methods=['POST'])
def api_arcade_buy_cabinet():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    cabs = arc.get("cabinets", [])
    # No hard floor cap — the 2-per-title limit (below) bounds the collection.
    if not arc.get("market"):
        _arcade_roll_market(s)
    offer_id = (request.json or {}).get("offer_id")
    offer    = next((o for o in arc.get("market", []) if o.get("id") == offer_id), None)
    if not offer:
        return jsonify({"error": "That cabinet's gone — check the lineup."}), 400
    title_ct = sum(1 for c in cabs if c.get("title") == offer["title"])
    if title_ct >= ARCADE_MAX_PER_TITLE:
        return jsonify({"error": f"You already run two '{offer['title']}' cabinets — that's the limit."}), 400
    price = offer["price"]
    if s["cash"] < price:
        return jsonify({"error": f"Need ${price:,}"}), 400
    s["cash"] -= price
    new_id = (max((c["id"] for c in cabs), default=-1)) + 1
    cabs.append({"id": new_id, "title": offer["title"], "genre": offer["genre"],
                 "rare": bool(offer.get("rare")), "condition": 100, "status": "working",
                 "high_score": 0, "hot_until": 0})
    arc["cabinets"] = cabs
    # Pull the bought unit off the lineup; mark the market so it re-rolls next day.
    arc["market"]      = [o for o in arc.get("market", []) if o.get("id") != offer_id]
    arc["market_used"] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{'🌟 Landed a RARE ' if offer.get('rare') else 'Added a '}'{offer['title']}' cabinet for ${price:,}."})
    save(s)
    return jsonify({"success": True, "rare": bool(offer.get("rare"))})

@app.route('/api/arcade/buy_decor', methods=['POST'])
def api_arcade_buy_decor():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    key = (request.json or {}).get("key")
    d   = ARCADE_DECOR.get(key)
    if not d:
        return jsonify({"error": "Unknown decor"}), 400
    decor = arc.setdefault("decor", {})
    if decor.get(key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < d["cost"]:
        return jsonify({"error": f"Need ${d['cost']:,}"}), 400
    s["cash"]  -= d["cost"]
    decor[key]  = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {d['name']} in the arcade (${d['cost']:,})."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/arcade/event_resolve', methods=['POST'])
def api_arcade_event_resolve():
    s    = load()
    data = request.json or {}
    ev = next((e for e in ARCADE_EVENTS if e["key"] == data.get("event_key")), None)
    if not ev:
        return jsonify({"error": "Unknown event"}), 400
    idx = int(data.get("choice_idx", -1))
    if idx < 0 or idx >= len(ev["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    choice = ev["choices"][idx]
    if choice.get("cost", 0) > s["cash"]:
        return jsonify({"error": "Not enough cash for that"}), 400
    result, bad = _arcade_apply_event_choice(s, choice)
    s["log"].insert(0, {"day": s["day"], "type": "warning" if bad else "info",
        "text": f"Arcade · {ev['title']} — {choice['label']}"})
    save(s)
    return jsonify({"success": True, "result": result, "bad": bad, "cash": s["cash"]})

@app.route('/api/arcade/service_cabinet', methods=['POST'])
def api_arcade_service_cabinet():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    cab = next((c for c in arc.get("cabinets", []) if c["id"] == (request.json or {}).get("cabinet_id")), None)
    if not cab:
        return jsonify({"error": "Cabinet not found"}), 400
    if cab.get("status") == "working" and cab.get("condition", 100) >= 99:
        return jsonify({"error": "This cabinet is already in top shape."}), 400
    if s["cash"] < ARCADE_SERVICE_COST:
        return jsonify({"error": f"Need ${ARCADE_SERVICE_COST:,}"}), 400
    s["cash"] -= ARCADE_SERVICE_COST
    _tax_deduct(s, ARCADE_SERVICE_COST)
    cab["status"] = "working"; cab["condition"] = 100
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Serviced the '{cab['title']}' cabinet (${ARCADE_SERVICE_COST})."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/arcade/remove_cabinet', methods=['POST'])
def api_arcade_remove_cabinet():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    cid  = (request.json or {}).get("cabinet_id")
    cabs = arc.get("cabinets", [])
    cab  = next((c for c in cabs if c["id"] == cid), None)
    if not cab:
        return jsonify({"error": "Cabinet not found"}), 400
    arc["cabinets"] = [c for c in cabs if c["id"] != cid]
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Hauled off the '{cab['title']}' cabinet (no refund)."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/arcade/hire_tech', methods=['POST'])
def api_arcade_hire_tech():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    st = arc.setdefault("staff", {})
    st["tech"] = not st.get("tech", False)
    save(s)
    return jsonify({"success": True, "hired": st["tech"]})

@app.route('/api/arcade/hire_staff', methods=['POST'])
def api_arcade_hire_staff():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    role = (request.json or {}).get("role")
    if role not in ARCADE_STAFF:
        return jsonify({"error": "Unknown role"}), 400
    st = arc.setdefault("staff", {})
    st[role] = not st.get(role, False)
    meta = ARCADE_STAFF[role]
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": (f"Hired a {meta['name']} (${meta['cost']}/day)." if st[role]
                 else f"Let the {meta['name']} go.")})
    save(s)
    return jsonify({"success": True, "hired": st[role]})

@app.route('/api/arcade/collect', methods=['POST'])
def api_arcade_collect():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    take = arc.get("uncollected", 0)
    if take <= 0:
        return jsonify({"error": "The machines are empty — nothing to collect."}), 400
    if s.get("energy", 0) < 4:
        return jsonify({"error": "Not enough energy — need 4 ⚡ (or let the Arcade Manager do it)"}), 400
    s["energy"]        -= 4
    s["cash"]          += take
    arc["total_earned"] = arc.get("total_earned", 0) + take
    _biz_income(s, "arcade", take)
    arc["uncollected"]  = 0
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Emptied the arcade machines: ${take:,} collected."})
    save(s)
    return jsonify({"success": True, "collected": take})

@app.route('/api/arcade/clean', methods=['POST'])
def api_arcade_clean():
    s   = load()
    arc = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    if arc.get("cleanliness", 100) >= 99:
        return jsonify({"error": "The arcade is already spotless."}), 400
    if s.get("energy", 0) < 6:
        return jsonify({"error": "Not enough energy — need 6 ⚡ (or hire a Janitor)"}), 400
    if s["cash"] < ARCADE_CLEAN_COST:
        return jsonify({"error": f"Need ${ARCADE_CLEAN_COST:,}"}), 400
    s["energy"]       -= 6
    s["cash"]         -= ARCADE_CLEAN_COST
    _tax_deduct(s, ARCADE_CLEAN_COST)
    arc["cleanliness"] = 100
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Deep-cleaned the arcade floor (${ARCADE_CLEAN_COST})."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/arcade/play_result', methods=['POST'])
def api_arcade_play_result():
    """Record a mini-game score. A new cabinet high score lights it 🔥 hot."""
    s    = load()
    arc  = s.get("arcade")
    if not (arc and arc.get("unlocked")):
        return jsonify({"error": "No arcade"}), 400
    data  = request.json or {}
    cab   = next((c for c in arc.get("cabinets", []) if c["id"] == data.get("cabinet_id")), None)
    if not cab:
        return jsonify({"error": "Cabinet not found"}), 400
    score = max(0, int(data.get("score", 0)))
    prev  = int(cab.get("high_score", 0))
    new_high = score > prev
    if new_high:
        cab["high_score"] = score
        cab["hot_until"]  = s["day"] + ARCADE_HOT_DAYS
        s["log"].insert(0, {"day": s["day"], "type": "positive",
            "text": f"🔥 New high score on '{cab['title']}' ({score:,})! It's running hot — +{int((ARCADE_HOT_MULT-1)*100)}% income for {ARCADE_HOT_DAYS} days."})
    save(s)
    return jsonify({"success": True, "new_high": new_high, "high_score": cab["high_score"],
                    "hot_days": ARCADE_HOT_DAYS if new_high else 0, "previous": prev})

@app.route('/api/laundromat/remove_machine', methods=['POST'])
def api_laundromat_remove_machine():
    s  = load()
    lm = s.get("laundromat")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    mid      = (request.json or {}).get("machine_id")
    machines = lm.get("machines", [])
    m        = next((x for x in machines if x["id"] == mid), None)
    if not m:
        return jsonify({"error": "Machine not found"}), 400
    lm["machines"] = [x for x in machines if x["id"] != mid]
    tname = LAUNDROMAT_MACHINE_TYPES.get(m.get("type", "combo"), {}).get("name", "machine")
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"Removed a {tname} from the laundromat (no refund)."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/buy_addon', methods=['POST'])
def api_laundromat_buy_addon():
    s  = load()
    lm = s.get("laundromat")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    key = (request.json or {}).get("addon_key")
    a   = LAUNDROMAT_ADDONS.get(key)
    if not a:
        return jsonify({"error": "Unknown add-on"}), 400
    addons = lm.setdefault("addons", {})
    if addons.get(key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < a["cost"]:
        return jsonify({"error": f"Need ${a['cost']:,}"}), 400
    s["cash"] -= a["cost"]
    addons[key] = True
    extra = ""
    # In-House Vending spawns a REAL 7th vending machine in the empire.
    if key == "vending":
        vms = s.setdefault("vending_machines", [])
        if not any(v.get("location_key") == "laundromat" for v in vms):
            vms.append(_vm_new_machine(s, 7, "laundromat"))
            extra = " A new vending machine appeared in your Vending tab — stock it!"
    # Back-Room Arcade unlocks a whole new (secret) business, starting with this cabinet.
    if key == "arcade":
        arc = s.get("arcade")
        if not (arc and arc.get("unlocked")):
            g = random.choice(ARCADE_GAMES)
            s["arcade"] = {"unlocked": True, "total_earned": 0, "uncollected": 0,
                           "cleanliness": 100, "prizes": 0, "decor": {}, "staff": {},
                           "cabinets": [{"id": 0, "title": g["title"], "genre": g["genre"],
                                         "rare": False, "condition": 100, "status": "working",
                                         "high_score": 0, "hot_until": 0}]}
            _arcade_roll_market(s)   # seed the first day's cabinet lineup
            # ...and a vending machine right there on the arcade floor (shows up in Vending).
            vms = s.setdefault("vending_machines", [])
            if not any(v.get("location_key") == "arcade" for v in vms):
                vms.append(_vm_new_machine(s, 8, "arcade"))
            extra = " You opened a secret Arcade business — and a new vending machine appeared on the arcade floor (check the Vending tab)!"
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {a['name']} at the laundromat for ${a['cost']:,}.{extra}"})
    save(s)
    return jsonify({"success": True, "spawned_vending": key == "vending", "unlocked_arcade": key == "arcade"})

@app.route('/api/laundromat/clean', methods=['POST'])
def api_laundromat_clean():
    s  = load()
    lm = s.get("laundromat")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    if s.get("energy", 0) < 6:
        return jsonify({"error": "Not enough energy — need 6 ⚡"}), 400
    if s["cash"] < LAUNDROMAT_CLEAN_COST:
        return jsonify({"error": f"Need ${LAUNDROMAT_CLEAN_COST}"}), 400
    s["energy"] -= 6
    s["cash"] -= LAUNDROMAT_CLEAN_COST
    _tax_deduct(s, LAUNDROMAT_CLEAN_COST)
    lm["cleanliness"] = min(100, lm.get("cleanliness", 0) + 30)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Cleaned the laundromat — cleanliness now {lm['cleanliness']}%."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/repair_machine', methods=['POST'])
def api_laundromat_repair_machine():
    s    = load()
    lm   = s.get("laundromat")
    data = request.json or {}
    mid  = data.get("machine_id")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    machines = lm.get("machines", [])
    machine  = next((m for m in machines if m["id"] == mid), None)
    if not machine:
        return jsonify({"error": "Machine not found"}), 400
    if machine["status"] != "broken":
        return jsonify({"error": "Machine is not broken"}), 400
    if s.get("energy", 0) < 3:
        return jsonify({"error": "Not enough energy — need 3 ⚡"}), 400
    repair_cost = 0 if lm.get("insurance") else LAUNDROMAT_REPAIR_COST
    if s["cash"] < repair_cost:
        return jsonify({"error": f"Need ${repair_cost}"}), 400
    s["energy"] -= 3
    s["cash"] -= repair_cost
    machine["status"] = "working"
    cost_str = "free (insurance)" if lm.get("insurance") else f"${repair_cost}"
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Repaired Laundromat Machine #{mid + 1} — {cost_str}."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/hire_staff', methods=['POST'])
def api_laundromat_hire_staff():
    s    = load()
    lm   = s.get("laundromat")
    data = request.json or {}
    role = data.get("role")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    if role not in LAUNDROMAT_STAFF:
        return jsonify({"error": "Unknown staff role"}), 400
    staff      = lm.setdefault("staff", {})
    staff[role] = not staff.get(role, False)
    action     = "hired" if staff[role] else "fired"
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"{LAUNDROMAT_STAFF[role]['name']} {action} at the laundromat."})
    save(s)
    return jsonify({"success": True, "hired": staff[role]})

@app.route('/api/laundromat/upgrade_machine', methods=['POST'])
def api_laundromat_upgrade_machine():
    s    = load()
    lm   = s.get("laundromat")
    data = request.json or {}
    mid  = data.get("machine_id")
    key  = data.get("upgrade_key")
    upg  = LAUNDROMAT_UPGRADES.get(key)
    if not lm or not upg:
        return jsonify({"error": "Not found"}), 400
    machines = lm.get("machines", [])
    machine  = next((m for m in machines if m["id"] == mid), None)
    if not machine:
        return jsonify({"error": "Machine not found"}), 400
    upgrades = machine.setdefault("upgrades", {})
    if upgrades.get(key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < upg["cost"]:
        return jsonify({"error": f"Need ${upg['cost']:,}"}), 400
    s["cash"] -= upg["cost"]
    upgrades[key] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {upg['name']} on Laundromat Machine #{mid + 1} for ${upg['cost']:,}!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/laundromat/insurance', methods=['POST'])
def api_laundromat_insurance():
    s  = load()
    lm = s.get("laundromat")
    if not lm:
        return jsonify({"error": "No laundromat"}), 400
    lm["insurance"] = not lm.get("insurance", False)
    if lm["insurance"]:
        lm["insurance_days"] = 7
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"Laundromat insurance {'activated ($400/week)' if lm['insurance'] else 'cancelled'}."})
    save(s)
    return jsonify({"success": True, "insurance": lm["insurance"]})

@app.route('/api/pole_studio/buy', methods=['POST'])
def api_pole_studio_buy():
    s = load()
    if s.get("pole_studio") and s["pole_studio"].get("owned"):
        return jsonify({"error": "Already owned"}), 400
    if s.get("level", 0) < POLE_STUDIO_UNLOCK_LEVEL:
        return jsonify({"error": f"Requires Level {POLE_STUDIO_UNLOCK_LEVEL}"}), 400
    if s["cash"] < POLE_STUDIO_PRICE:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= POLE_STUDIO_PRICE
    # Starts with a small member base and 2 class slots; buy more slots & hire instructors.
    s["pole_studio"] = {
        "owned": True, "slot_count": STUDIO_START_SLOTS,
        "dancers": {k: _pole_studio_dancer_state(k) for k in POLE_STUDIO_DANCERS},
        "staff": {}, "facilities": {}, "kombucha": {},
        "atmosphere": 80, "cleanliness": 90, "reputation": 15,
        "members": 18, "vip_members": 0, "satisfaction": 72,
        "slots": [{"type": "intro", "instructor": None}, {"type": "levels", "instructor": None}],
        "insurance": False, "insurance_days": 7,
        "active_demands": [], "fulfilled_demands": [], "total_earned": 0,
    }
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Brass Pole Fitness Studio acquired. Totally a legit fitness studio. The vibe is immaculate."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/set_slot', methods=['POST'])
def api_pole_studio_set_slot():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    idx  = int(data.get("slot_idx", -1))
    ct   = data.get("class_type")
    ik   = data.get("instructor")   # may be None to clear
    slots = ps.setdefault("slots", [])
    if idx < 0 or idx >= len(slots):
        return jsonify({"error": "Invalid slot"}), 400
    if ct is not None:
        if ct not in POLE_STUDIO_CLASSES:
            return jsonify({"error": "Unknown class type"}), 400
        slots[idx]["type"] = ct
    if "instructor" in data:
        if ik and ik not in ps.get("dancers", {}):
            return jsonify({"error": "Unknown instructor"}), 400
        slots[idx]["instructor"] = ik or None
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/buy_facility', methods=['POST'])
def api_pole_studio_buy_facility():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    key = data.get("key")
    f   = POLE_STUDIO_FACILITIES.get(key)
    if not f:
        return jsonify({"error": "Unknown facility"}), 400
    facs = ps.setdefault("facilities", {})
    if facs.get(key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < f["cost"]:
        return jsonify({"error": f"Need ${f['cost']:,}"}), 400
    s["cash"] -= f["cost"]
    _tax_deduct(s, f["cost"])
    facs[key] = True
    if f.get("slots"):   # a pole rack also adds a configurable slot
        ps.setdefault("slots", []).append({"type": "intro", "instructor": None})
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {f['name']} at the studio (${f['cost']:,})."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/hype', methods=['POST'])
def api_pole_studio_hype():
    s  = load()
    ps = s.get("pole_studio")
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    if ps.get("atmosphere", 0) >= 99:
        return jsonify({"error": "The vibe is already immaculate."}), 400
    if s.get("energy", 0) < 3:
        return jsonify({"error": "Not enough energy — need 3 ⚡ (or hire a Vibe Manager)"}), 400
    if s["cash"] < 120:
        return jsonify({"error": "Need $120"}), 400
    s["energy"] -= 3
    s["cash"]   -= 120
    _tax_deduct(s, 120)
    ps["atmosphere"] = min(100, ps.get("atmosphere", 0) + 30)
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": "Freshened the vibe — new playlist, dimmed the lights. Atmosphere up."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/marketing', methods=['POST'])
def api_pole_studio_marketing():
    s  = load()
    ps = s.get("pole_studio")
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    if s["cash"] < STUDIO_MARKETING_COST:
        return jsonify({"error": f"Need ${STUDIO_MARKETING_COST:,}"}), 400
    s["cash"] -= STUDIO_MARKETING_COST
    _tax_deduct(s, STUDIO_MARKETING_COST)
    ps["reputation"]      = min(100, ps.get("reputation", 0) + STUDIO_MARKETING_REP)
    ps["members"]         = ps.get("members", 0) + 5                       # immediate signups
    ps["marketing_boost"] = ps.get("marketing_boost", 0) + 5              # lingering buzz next advance
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Ran a marketing push (${STUDIO_MARKETING_COST:,}) — reputation +{STUDIO_MARKETING_REP}, new faces in the door."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/theme_night', methods=['POST'])
def api_pole_studio_theme_night():
    s  = load()
    ps = s.get("pole_studio")
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    if not ps.get("facilities", {}).get("stage"):
        return jsonify({"error": "Build the Performance Stage first."}), 400
    if s["day"] < ps.get("theme_until", 0):
        return jsonify({"error": f"The stage needs {ps['theme_until'] - s['day']} more day(s) to reset."}), 400
    if s["cash"] < STUDIO_THEME_COST:
        return jsonify({"error": f"Need ${STUDIO_THEME_COST:,}"}), 400
    if s.get("energy", 0) < 4:
        return jsonify({"error": "Not enough energy — need 4 ⚡"}), 400
    s["energy"] -= 4
    s["cash"]   -= STUDIO_THEME_COST
    _tax_deduct(s, STUDIO_THEME_COST)
    payout = int(round(1500 + ps.get("members", 0) * 22 * (0.6 + ps.get("reputation", 0) / 100 * 0.8)))
    s["cash"] += payout
    ps["total_earned"]  = ps.get("total_earned", 0) + payout
    _biz_income(s, "pole_studio", payout)
    ps["reputation"]    = min(100, ps.get("reputation", 0) + 6)
    ps["members"]       = ps.get("members", 0) + 4
    ps["satisfaction"]  = min(100, ps.get("satisfaction", 70) + 5)
    ps["theme_until"]   = s["day"] + STUDIO_THEME_COOLDOWN
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Hosted a Theme Night! Packed house — +${payout:,}, reputation up, new members."})
    save(s)
    return jsonify({"success": True, "payout": payout})

@app.route('/api/pole_studio/buy_slot', methods=['POST'])
def api_pole_studio_buy_slot():
    s  = load()
    ps = s.get("pole_studio")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    sc = ps.get("slot_count", STUDIO_START_SLOTS)
    if sc >= STUDIO_MAX_SLOTS:
        return jsonify({"error": f"Already at the max of {STUDIO_MAX_SLOTS} class slots."}), 400
    price = STUDIO_SLOT_PRICES[sc - STUDIO_START_SLOTS] if (sc - STUDIO_START_SLOTS) < len(STUDIO_SLOT_PRICES) else STUDIO_SLOT_PRICES[-1]
    if s["cash"] < price:
        return jsonify({"error": f"Need ${price:,}"}), 400
    s["cash"] -= price
    _tax_deduct(s, price)
    ps["slot_count"] = sc + 1
    ps.setdefault("slots", []).append({"type": "intro", "instructor": None})
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Added a class slot (now {sc + 1}). Schedule another class!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/hire_dancer', methods=['POST'])
def api_pole_studio_hire_dancer():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    dk   = data.get("dancer")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    if dk not in POLE_STUDIO_DANCERS:
        return jsonify({"error": "Unknown dancer"}), 400
    dancers = ps.setdefault("dancers", {k: _pole_studio_dancer_state(k) for k in POLE_STUDIO_DANCERS})
    if dancers[dk].get("hired"):
        return jsonify({"error": "Already hired"}), 400
    dancers[dk]["hired"] = True
    dancers[dk]["mood"]  = POLE_STUDIO_DANCERS[dk]["mood_start"]
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{POLE_STUDIO_DANCERS[dk]['name']} {POLE_STUDIO_DANCERS[dk]['icon']} joins the studio."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/fire_dancer', methods=['POST'])
def api_pole_studio_fire_dancer():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    dk   = data.get("dancer")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    dancers = ps.setdefault("dancers", {})
    if not dancers.get(dk, {}).get("hired"):
        return jsonify({"error": "Not hired"}), 400
    dancers[dk]["hired"] = False
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"{POLE_STUDIO_DANCERS[dk]['name']} has left the studio."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/clean', methods=['POST'])
def api_pole_studio_clean():
    s  = load()
    ps = s.get("pole_studio")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    energy = s.get("energy", 0)
    if energy < POLE_STUDIO_CLEAN_ENERGY:
        return jsonify({"error": "Not enough energy"}), 400
    if s["cash"] < POLE_STUDIO_CLEAN_COST:
        return jsonify({"error": "Not enough cash"}), 400
    s["energy"] = energy - POLE_STUDIO_CLEAN_ENERGY
    s["cash"]   = s["cash"] - POLE_STUDIO_CLEAN_COST
    ps["cleanliness"] = min(100, ps.get("cleanliness", 0) + 40)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Studio cleaned. The floors shine. Gary notices."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/pep_talk', methods=['POST'])
def api_pole_studio_pep_talk():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    dk   = data.get("dancer")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    energy = s.get("energy", 0)
    if energy < POLE_STUDIO_PEP_ENERGY:
        return jsonify({"error": "Not enough energy"}), 400
    dancers = ps.setdefault("dancers", {})
    if dk and dk != "gary" and dancers.get(dk, {}).get("hired"):
        last_pep = dancers[dk].get("pep_day", -1)
        if last_pep == s["day"]:
            return jsonify({"error": f"Already gave {POLE_STUDIO_DANCERS[dk]['name']} a pep talk today."}), 400
        s["energy"] = energy - POLE_STUDIO_PEP_ENERGY
        dancers[dk]["mood"]    = min(100, dancers[dk].get("mood", 50) + POLE_STUDIO_PEP_MOOD)
        dancers[dk]["pep_day"] = s["day"]
        name = POLE_STUDIO_DANCERS[dk]["name"]
        s["log"].insert(0, {"day": s["day"], "type": "positive",
            "text": f"Pep talk with {name}. Mood improved."})
        save(s)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid dancer"}), 400

@app.route('/api/pole_studio/team_coffee', methods=['POST'])
def api_pole_studio_team_coffee():
    s  = load()
    ps = s.get("pole_studio")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    last_coffee = ps.get("last_coffee_day", -999)
    if s["day"] - last_coffee < 7:
        days_left = 7 - (s["day"] - last_coffee)
        return jsonify({"error": f"Team coffee is on cooldown — {days_left} day(s) left."}), 400
    if s["cash"] < POLE_STUDIO_COFFEE_COST:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= POLE_STUDIO_COFFEE_COST
    ps["last_coffee_day"] = s["day"]
    dancers   = ps.setdefault("dancers", {})
    boosted   = 0
    for dk, dd in dancers.items():
        if dd.get("hired") and dk != "gary":
            dd["mood"] = min(100, dd.get("mood", 50) + POLE_STUDIO_COFFEE_MOOD)
            boosted += 1
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Team coffee! {boosted} dancer(s) felt the appreciation."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/set_class', methods=['POST'])
def api_pole_studio_set_class():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    dk = data.get("dancer_key"); ck = data.get("class_key")
    if dk not in ps.get("dancers", {}) or ck not in POLE_STUDIO_CLASSES:
        return jsonify({"error": "Invalid class assignment"}), 400
    ps["dancers"][dk]["class"] = ck
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/event_resolve', methods=['POST'])
def api_pole_studio_event_resolve():
    s    = load()
    ps   = s.get("pole_studio")
    if not (ps and ps.get("owned")):
        return jsonify({"error": "No studio"}), 400
    data = request.json or {}
    ev = next((e for e in POLE_STUDIO_EVENT_CARDS if e["key"] == data.get("event_key")), None)
    if not ev:
        return jsonify({"error": "Unknown event"}), 400
    idx = int(data.get("choice_idx", -1))
    if idx < 0 or idx >= len(ev["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    choice = ev["choices"][idx]
    if choice.get("cost", 0) > s["cash"]:
        return jsonify({"error": "Not enough cash for that"}), 400
    result, bad = _pole_apply_event_choice(s, choice)
    s["log"].insert(0, {"day": s["day"], "type": "warning" if bad else "info",
        "text": f"Studio · {ev['title']} — {choice['label']}"})
    save(s)
    return jsonify({"success": True, "result": result, "bad": bad, "cash": s["cash"]})

@app.route('/api/pole_studio/resolve_demand', methods=['POST'])
def api_pole_studio_resolve_demand():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    key  = data.get("key")
    action = data.get("action", "accept")  # "accept" or "reject"
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    spec = next((d for d in POLE_STUDIO_DEMANDS if d["key"] == key), None)
    if not spec:
        return jsonify({"error": "Unknown demand"}), 400
    effects = spec["accept"] if action == "accept" else spec["reject"]
    dk = spec["dancer"]
    _apply_demand_effects(s, ps, effects, dk)
    if effects.get("quit") and ps["dancers"].get(dk, {}).get("hired"):
        ps["dancers"][dk]["hired"] = False
        events_msg = f"{POLE_STUDIO_DANCERS[dk]['name']} has left the studio."
    else:
        events_msg = spec["accept_note"] if action == "accept" else spec["reject_note"]
    # Remove from active demands
    ps["active_demands"] = [d for d in ps.get("active_demands", []) if d["key"] != key]
    ps.setdefault("fulfilled_demands", []).append(key)
    s["log"].insert(0, {"day": s["day"], "type": "positive" if action == "accept" else "neutral",
        "text": events_msg})
    save(s)
    return jsonify({"success": True, "msg": events_msg})

@app.route('/api/pole_studio/upgrade_pole', methods=['POST'])
def api_pole_studio_upgrade_pole():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    pole_idx = data.get("pole_idx", 0)
    upg      = data.get("upgrade")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    if upg not in POLE_STUDIO_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    poles = ps.setdefault("poles", [])
    if pole_idx >= len(poles):
        return jsonify({"error": "Invalid pole"}), 400
    cost = POLE_STUDIO_UPGRADES[upg]["cost"]
    if s["cash"] < cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= cost
    poles[pole_idx].setdefault("upgrades", {})[upg] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Pole #{pole_idx + 1} upgraded: {POLE_STUDIO_UPGRADES[upg]['name']}."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/repair_pole', methods=['POST'])
def api_pole_studio_repair_pole():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    pole_idx = data.get("pole_idx", 0)
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    poles = ps.setdefault("poles", [])
    if pole_idx >= len(poles) or not poles[pole_idx].get("broken"):
        return jsonify({"error": "Pole not broken"}), 400
    repair_cost = 0 if ps.get("insurance") else POLE_STUDIO_REPAIR_COST
    if s["cash"] < repair_cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= repair_cost
    poles[pole_idx]["broken"] = False
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Pole #{pole_idx + 1} repaired and ready."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/hire_staff', methods=['POST'])
def api_pole_studio_hire_staff():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    if role not in POLE_STUDIO_STAFF:
        return jsonify({"error": "Unknown role"}), 400
    staff = ps.setdefault("staff", {})
    if staff.get(role):
        return jsonify({"error": "Already hired"}), 400
    staff[role] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{POLE_STUDIO_STAFF[role]['name']} hired."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/fire_staff', methods=['POST'])
def api_pole_studio_fire_staff():
    s    = load()
    ps   = s.get("pole_studio")
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    staff = ps.setdefault("staff", {})
    staff[role] = False
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"{POLE_STUDIO_STAFF[role]['name']} let go."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/insurance', methods=['POST'])
def api_pole_studio_insurance():
    s  = load()
    ps = s.get("pole_studio")
    if not ps:
        return jsonify({"error": "No studio"}), 400
    ps["insurance"] = not ps.get("insurance", False)
    if ps["insurance"]:
        ps["insurance_days"] = 7
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"Studio insurance {'activated ($500/week)' if ps['insurance'] else 'cancelled'}."})
    save(s)
    return jsonify({"success": True, "insurance": ps["insurance"]})

def _cw_check(s):
    cw = s.get("car_wash")
    if not cw or not cw.get("owned"):
        return None, jsonify({"error": "No car wash"}), 400
    return cw, None, None

@app.route('/api/car_wash/buy', methods=['POST'])
def api_car_wash_buy():
    s = load()
    if s.get("car_wash") and s["car_wash"].get("owned"):
        return jsonify({"error": "Already owned"}), 400
    if s.get("level", 0) < CAR_WASH_UNLOCK_LEVEL:
        return jsonify({"error": f"Requires Level {CAR_WASH_UNLOCK_LEVEL}"}), 400
    if s["cash"] < CAR_WASH_PRICE:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= CAR_WASH_PRICE
    s["car_wash"] = {
        "owned": True, "bay_count": CAR_WASH_START_BAYS,
        "bays": [{"id": 0, "upgrades": {}, "broken": False, "condition": 100}],
        "staff": {k: False for k in CAR_WASH_STAFF},
        "global_upgrades": {},
        "supplies": {},
        "water_pressure": 100, "morale": 80,
        "reputation": 5, "regulars": 0, "members": 0,
        "weather": "clear", "forecast": _roll_car_wash_weather(_season_info(s["day"] + 1)[0]),
        "insurance": False, "insurance_days": 7,
        "total_earned": 0,
    }
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Slippery When Washed is open. The sign is crooked. It adds character."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/build_bay', methods=['POST'])
def api_car_wash_build_bay():
    s  = load()
    cw = s.get("car_wash")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    bc = cw.get("bay_count", CAR_WASH_START_BAYS)
    if bc >= CAR_WASH_MAX_BAYS:
        return jsonify({"error": "Maximum 5 bays reached"}), 400
    price = CAR_WASH_BAY_PRICES[bc - CAR_WASH_START_BAYS]
    if s["cash"] < price:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= price
    cw["bay_count"] = bc + 1
    cw.setdefault("bays", []).append({"id": bc, "upgrades": {}, "broken": False, "condition": 100})
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bay #{bc + 1} constructed. The sign is still crooked."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/hire_staff', methods=['POST'])
def api_car_wash_hire_staff():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    if role not in CAR_WASH_STAFF:
        return jsonify({"error": "Unknown role"}), 400
    staff = cw.setdefault("staff", {})
    if staff.get(role):
        return jsonify({"error": "Already hired"}), 400
    staff[role] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{CAR_WASH_STAFF[role]['name']} is on the team."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/fire_staff', methods=['POST'])
def api_car_wash_fire_staff():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    cw.setdefault("staff", {})[role] = False
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"{CAR_WASH_STAFF[role]['name']} let go."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/upgrade_bay', methods=['POST'])
def api_car_wash_upgrade_bay():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    bay_idx = data.get("bay_idx", 0)
    upg     = data.get("upgrade")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    if upg not in CAR_WASH_BAY_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    bays = cw.setdefault("bays", [])
    if bay_idx >= len(bays):
        return jsonify({"error": "Invalid bay"}), 400
    cost = CAR_WASH_BAY_UPGRADES[upg]["cost"]
    if s["cash"] < cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= cost
    bays[bay_idx].setdefault("upgrades", {})[upg] = True
    if upg == "foam":
        cw["reputation"] = min(100, cw.get("reputation", 0) + 10)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bay #{bay_idx + 1}: {CAR_WASH_BAY_UPGRADES[upg]['name']} installed."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/global_upgrade', methods=['POST'])
def api_car_wash_global_upgrade():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    upg  = data.get("upgrade")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    if upg not in CAR_WASH_GLOBAL_UPGRADES:
        return jsonify({"error": "Unknown upgrade"}), 400
    g = cw.setdefault("global_upgrades", {})
    if g.get(upg):
        return jsonify({"error": "Already installed"}), 400
    cost = CAR_WASH_GLOBAL_UPGRADES[upg]["cost"]
    if s["cash"] < cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= cost
    g[upg] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Slippery When Washed: {CAR_WASH_GLOBAL_UPGRADES[upg]['name']} installed."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/repair_bay', methods=['POST'])
def api_car_wash_repair_bay():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    bay_idx = data.get("bay_idx", 0)
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    bays = cw.setdefault("bays", [])
    if bay_idx >= len(bays):
        return jsonify({"error": "Invalid bay"}), 400
    repair_cost = 0 if cw.get("insurance") else CAR_WASH_REPAIR_COST
    if s["cash"] < repair_cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= repair_cost
    bays[bay_idx]["broken"]    = False
    bays[bay_idx]["condition"] = 80
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bay #{bay_idx + 1} repaired and back in service."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/repressurize', methods=['POST'])
def api_car_wash_repressurize():
    s  = load()
    cw = s.get("car_wash")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    if s["cash"] < CAR_WASH_REPRESSURIZE_COST:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= CAR_WASH_REPRESSURIZE_COST
    cw["water_pressure"] = min(100, cw.get("water_pressure", 0) + 50)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Water pressure restored."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/pep_talk', methods=['POST'])
def api_car_wash_pep_talk():
    s    = load()
    cw   = s.get("car_wash")
    data = request.get_json(silent=True) or {}
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    energy = s.get("energy", 0)
    if energy < CAR_WASH_PEP_ENERGY:
        return jsonify({"error": "Not enough energy"}), 400
    if cw.get("pep_day") == s["day"]:
        return jsonify({"error": "Already gave the team a pep talk today."}), 400
    s["energy"]    = energy - CAR_WASH_PEP_ENERGY
    cw["morale"]   = min(100, cw.get("morale", 80) + CAR_WASH_PEP_MORALE)
    cw["pep_day"]  = s["day"]
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Pep talk delivered. Terry made a counterpoint about water temperature."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/team_lunch', methods=['POST'])
def api_car_wash_team_lunch():
    s  = load()
    cw = s.get("car_wash")
    if not cw or not cw.get("owned"):
        return jsonify({"error": "No car wash"}), 400
    last = cw.get("last_lunch_day", -999)
    if s["day"] - last < CAR_WASH_LUNCH_COOLDOWN:
        days_left = CAR_WASH_LUNCH_COOLDOWN - (s["day"] - last)
        return jsonify({"error": f"Team lunch on cooldown — {days_left} day(s) left."}), 400
    if s["cash"] < CAR_WASH_LUNCH_COST:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= CAR_WASH_LUNCH_COST
    cw["morale"]        = min(100, cw.get("morale", 80) + CAR_WASH_LUNCH_MORALE)
    cw["last_lunch_day"] = s["day"]
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Team lunch. Dave ordered a vacuum-shaped sandwich. Nobody commented."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/car_wash/insurance', methods=['POST'])
def api_car_wash_insurance():
    s  = load()
    cw = s.get("car_wash")
    if not cw:
        return jsonify({"error": "No car wash"}), 400
    cw["insurance"] = not cw.get("insurance", False)
    if cw["insurance"]:
        cw["insurance_days"] = 7
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"Car wash insurance {'activated ($600/week)' if cw['insurance'] else 'cancelled'}."})
    save(s)
    return jsonify({"success": True, "insurance": cw["insurance"]})

@app.route('/api/car_wash/event_resolve', methods=['POST'])
def api_car_wash_event_resolve():
    s  = load()
    cw = s.get("car_wash")
    if not (cw and cw.get("owned")):
        return jsonify({"error": "No car wash"}), 400
    data = request.json or {}
    ev = next((e for e in CAR_WASH_EVENT_CARDS if e["key"] == data.get("event_key")), None)
    if not ev:
        return jsonify({"error": "Unknown event"}), 400
    idx = int(data.get("choice_idx", -1))
    if idx < 0 or idx >= len(ev["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    choice = ev["choices"][idx]
    if choice.get("cost", 0) > s["cash"]:
        return jsonify({"error": "Not enough cash for that"}), 400
    result, bad = _car_wash_apply_event_choice(s, choice)
    s["log"].insert(0, {"day": s["day"], "type": "warning" if bad else "info",
        "text": f"Car Wash · {ev['title']} — {choice['label']}"})
    save(s)
    return jsonify({"success": True, "result": result, "bad": bad, "cash": s["cash"]})

# ── New Builds routes ─────────────────────────────────────────────────────────

@app.route('/api/new_builds/buy_permit', methods=['POST'])
def api_buy_permit():
    s = load()
    if s.get("level", 0) < NEW_BUILDS_UNLOCK_LEVEL:
        return jsonify({"error": f"Reach Level {NEW_BUILDS_UNLOCK_LEVEL} to unlock New Builds"}), 400
    if s.get("building_permit"):
        return jsonify({"error": "You already own a building permit"}), 400
    if s["cash"] < BUILDING_PERMIT_COST:
        return jsonify({"error": f"Need ${BUILDING_PERMIT_COST:,}"}), 400
    s["cash"] -= BUILDING_PERMIT_COST
    s["building_permit"] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Building permit purchased. You can now build homes in Cedarvale Estates."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/new_builds/buy_crew', methods=['POST'])
def api_buy_crew():
    s    = load()
    data = request.get_json(silent=True) or {}
    crew_key = data.get("crew")
    if crew_key not in BUILD_CREWS:
        return jsonify({"error": "Unknown crew"}), 400
    if not s.get("building_permit"):
        return jsonify({"error": "Purchase a building permit first"}), 400
    owned = s.get("owned_crews", [])
    if crew_key in owned:
        return jsonify({"error": "You already own this crew"}), 400
    cost = BUILD_CREWS[crew_key]["buy_cost"]
    if s["cash"] < cost:
        return jsonify({"error": f"Need ${cost:,}"}), 400
    s["cash"] -= cost
    owned.append(crew_key)
    s["owned_crews"] = owned
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{BUILD_CREWS[crew_key]['name']} is now on your roster."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/new_builds/start', methods=['POST'])
def api_start_build():
    s    = load()
    data = request.get_json(silent=True) or {}
    size_key  = data.get("size")
    crew_key  = data.get("crew")
    premiums  = data.get("premium_upgrades", [])

    if not s.get("building_permit"):
        return jsonify({"error": "No building permit"}), 400
    if size_key not in NEW_BUILD_SIZES:
        return jsonify({"error": "Invalid size"}), 400
    if crew_key not in BUILD_CREWS:
        return jsonify({"error": "Invalid crew"}), 400
    if crew_key not in s.get("owned_crews", []):
        return jsonify({"error": "You don't own that crew"}), 400

    # Check crew not already on another build
    for b in s.get("active_builds", []):
        if b.get("crew") == crew_key and not b.get("paused"):
            return jsonify({"error": f"{BUILD_CREWS[crew_key]['name']} is already assigned to another build"}), 400

    # Validate premium upgrades
    for pk in premiums:
        if pk not in PREMIUM_UPGRADES:
            return jsonify({"error": f"Unknown upgrade: {pk}"}), 400

    size = NEW_BUILD_SIZES[size_key]
    crew = BUILD_CREWS[crew_key]
    premium_cost = sum(PREMIUM_UPGRADES[pk]["cost"] for pk in premiums)
    total_upfront = size["build_cost"] + premium_cost

    if s["cash"] < total_upfront:
        return jsonify({"error": f"Need ${total_upfront:,} upfront (build + upgrades)"}), 400

    s["cash"] -= total_upfront

    days = max(1, round(size["base_days"] * crew["speed_mult"]))
    build_id = s.get("next_build_id", 1)
    s["next_build_id"] = build_id + 1

    build = {
        "id": build_id,
        "size": size_key,
        "crew": crew_key,
        "premium_upgrades": premiums,
        "days_remaining": days,
        "total_days": days,
        "paused": False,
        "started_day": s["day"],
        "build_cost": size["build_cost"],
        "premium_cost": premium_cost,
        "total_crew_paid": 0,
    }
    s.setdefault("active_builds", []).append(build)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Construction started on a {size['name']} in Cedarvale Estates. ETA: {days} days."})
    save(s)
    return jsonify({"success": True, "cash": s["cash"], "build": build})

@app.route('/api/new_builds/toggle_pause', methods=['POST'])
def api_toggle_build_pause():
    s    = load()
    data = request.get_json(silent=True) or {}
    bid  = data.get("build_id")
    build = next((b for b in s.get("active_builds", []) if b["id"] == bid), None)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    build["paused"] = not build.get("paused", False)
    state_str = "paused" if build["paused"] else "resumed"
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"{NEW_BUILD_SIZES[build['size']]['name']} construction {state_str}."})
    save(s)
    return jsonify({"success": True, "paused": build["paused"]})

@app.route('/api/new_builds/cancel', methods=['POST'])
def api_cancel_build():
    s    = load()
    data = request.get_json(silent=True) or {}
    bid  = data.get("build_id")
    build = next((b for b in s.get("active_builds", []) if b["id"] == bid), None)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    # Refund 40% of upfront costs
    refund = round((build["build_cost"] + build.get("premium_cost", 0)) * 0.40)
    s["cash"] += refund
    s["active_builds"] = [b for b in s["active_builds"] if b["id"] != bid]
    s["log"].insert(0, {"day": s["day"], "type": "warning",
        "text": f"{NEW_BUILD_SIZES[build['size']]['name']} build cancelled. ${refund:,} refunded (40%)."})
    save(s)
    return jsonify({"success": True, "refund": refund, "cash": s["cash"]})

@app.route('/api/commercial/buy', methods=['POST'])
def api_commercial_buy():
    s    = load()
    data = request.get_json(silent=True) or {}
    cid  = data.get("listing_id")
    if s.get("level", 0) < COMMERCE_ROW_UNLOCK_LEVEL:
        return jsonify({"error": f"Reach Level {COMMERCE_ROW_UNLOCK_LEVEL} to unlock Commerce Row"}), 400
    prop = next((p for p in s.get("commercial_market", []) if p["id"] == cid), None)
    if not prop:
        return jsonify({"error": "Listing not found"}), 404
    if prop["purchase_price"] > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= prop["purchase_price"]
    prop["purchase_day"] = s["day"]
    s["properties"].append(prop)
    s["commercial_market"] = [p for p in s["commercial_market"] if p["id"] != cid]
    ctype = COMMERCIAL_TYPES[prop["type"]]
    s["log"].insert(0, {"day": s["day"], "type": "buy",
        "text": f"Bought {ctype['name']} on {prop['address']} for ${prop['purchase_price']:,}"})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/commercial/<int:pid>/get_applicants', methods=['POST'])
def api_commercial_get_applicants(pid):
    s    = load()
    data = request.get_json(silent=True) or {}
    uidx = data.get("unit_idx")
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    unit = next((u for u in prop["units"] if u["idx"] == uidx), None)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    if unit.get("business_type"):
        return jsonify({"error": "Unit already occupied"}), 400
    # Generate 3 random business applicants (rare chance for Flooring Express)
    regular_types = [k for k, v in BUSINESS_TENANT_TYPES.items() if not v.get("special")]
    chosen        = random.sample(regular_types, min(3, len(regular_types)))
    if random.random() < 0.125:  # 1-in-8 chance to replace one slot with Flooring Express
        chosen[random.randint(0, len(chosen) - 1)] = "flooring_express"
    applicants = []
    for bt in chosen:
        btype = BUSINESS_TENANT_TYPES[bt]
        applicants.append({
            "biz_type":     bt,
            "name":         random.choice(btype["names"]),
            "icon":         btype["icon"],
            "display_name": btype["name"],
            "monthly_rent": btype["monthly_rent"],
            "lease_days":   btype["lease_days"],
            "desc":         btype["desc"],
            "special":      btype.get("special", False),
        })
    unit["applicants"] = applicants
    save(s)
    return jsonify({"success": True, "applicants": applicants})

@app.route('/api/commercial/<int:pid>/accept_tenant', methods=['POST'])
def api_commercial_accept_tenant(pid):
    s    = load()
    data = request.get_json(silent=True) or {}
    uidx     = data.get("unit_idx")
    biz_type = data.get("biz_type")
    biz_name = data.get("biz_name")
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    unit = next((u for u in prop["units"] if u["idx"] == uidx), None)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    btype = BUSINESS_TENANT_TYPES.get(biz_type)
    if not btype:
        return jsonify({"error": "Invalid business type"}), 400
    unit["business_type"]        = biz_type
    unit["tenant_name"]          = biz_name or random.choice(btype["names"])
    unit["lease_days_remaining"] = btype["lease_days"]
    unit["renewal_pending"]      = False
    unit["satisfaction"]         = 72
    unit["pct_rent_monthly"]     = 0
    unit["applicants"]           = []
    # Apply active upgrade rent bonuses to incoming tenant
    base_rent = btype["monthly_rent"]
    upgrades  = prop.get("upgrades", {})
    if upgrades.get("renovated_common"):
        base_rent = int(base_rent * 1.08)
    if upgrades.get("exterior_facelift"):
        base_rent += 300
    if upgrades.get("fiber_internet") and biz_type in ("law_office", "accounting_firm"):
        base_rent += 500
    unit["monthly_rent"] = base_rent
    ctype = COMMERCIAL_TYPES[prop["type"]]
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{unit['tenant_name']} ({btype['name']}) moved into {ctype['name']} on {prop['address']}"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/commercial/event_respond', methods=['POST'])
def api_commercial_event_respond():
    """Generic resolver — applies the chosen option's (already-rolled) effect."""
    s    = load()
    data = request.get_json(silent=True) or {}
    pid    = data.get("prop_id")
    uidx   = data.get("unit_idx")
    effect = data.get("effect") or {}
    result = data.get("result") or "Handled."
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    unit = next((u for u in prop["units"] if u["idx"] == uidx), None)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    # Only honor known effect keys (the client owns state, but stay defensive)
    safe = {k: effect[k] for k in ("cost", "gain", "cond", "sat", "rent_add", "rent_mult", "vacate", "deduct")
            if k in effect}
    _apply_commercial_effect(s, prop, unit, safe)
    s["log"].insert(0, {"day": s["day"], "type": "info", "text": result})
    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/commercial/<int:pid>/superintendent', methods=['POST'])
def api_commercial_superintendent(pid):
    s      = load()
    data   = request.get_json(silent=True) or {}
    action = data.get("action", "hire")
    prop   = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    ctype = COMMERCIAL_TYPES.get(prop["type"], {})
    if action == "hire":
        if prop.get("superintendent"):
            return jsonify({"error": "Superintendent already hired"}), 400
        prop["superintendent"] = True
        s["log"].insert(0, {"day": s["day"], "type": "positive",
            "text": f"Building superintendent hired for {ctype['name']} on {prop['address']}"})
    else:
        prop["superintendent"] = False
        s["log"].insert(0, {"day": s["day"], "type": "info",
            "text": f"Building superintendent dismissed from {ctype['name']} on {prop['address']}"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/commercial/<int:pid>/maintenance', methods=['POST'])
def api_commercial_maintenance(pid):
    s      = load()
    data   = request.get_json(silent=True) or {}
    action = data.get("action", "hire")
    prop   = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    ctype = COMMERCIAL_TYPES.get(prop["type"], {})
    if action == "hire":
        if prop.get("maintenance"):
            return jsonify({"error": "Maintenance man already hired"}), 400
        prop["maintenance"] = True
        s["log"].insert(0, {"day": s["day"], "type": "positive",
            "text": f"Maintenance man hired for {ctype['name']} on {prop['address']} — building upkeep now handled"})
    else:
        prop["maintenance"] = False
        s["log"].insert(0, {"day": s["day"], "type": "info",
            "text": f"Maintenance man let go from {ctype['name']} on {prop['address']}"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/commercial/<int:pid>/upgrade', methods=['POST'])
def api_commercial_upgrade(pid):
    s           = load()
    data        = request.get_json(silent=True) or {}
    upgrade_key = data.get("upgrade")
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    upg = COMMERCIAL_UPGRADES.get(upgrade_key)
    if not upg:
        return jsonify({"error": "Unknown upgrade"}), 400
    if prop.get("upgrades", {}).get(upgrade_key):
        return jsonify({"error": "Already installed"}), 400
    if s["cash"] < upg["cost"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= upg["cost"]
    prop.setdefault("upgrades", {})[upgrade_key] = True
    ctype = COMMERCIAL_TYPES.get(prop["type"], {})
    # One-time effects at install time
    if upgrade_key == "exterior_facelift":
        prop["condition"] = min(prop.get("condition", 0) + 40, 250)
        for u in prop.get("units", []):
            if u.get("business_type"):
                u["monthly_rent"] = u.get("monthly_rent", 0) + 300
    elif upgrade_key == "renovated_common":
        for u in prop.get("units", []):
            if u.get("business_type"):
                u["monthly_rent"] = int(u.get("monthly_rent", 0) * 1.08)
    elif upgrade_key == "fiber_internet":
        for u in prop.get("units", []):
            if u.get("business_type") in ("law_office", "accounting_firm"):
                u["monthly_rent"] = u.get("monthly_rent", 0) + 500
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{upg['name']} installed at {ctype.get('name','building')} on {prop['address']}"})
    save(s)
    return jsonify({"success": True, "condition": prop["condition"]})

@app.route('/api/commercial/<int:pid>/emergency_repair', methods=['POST'])
def api_commercial_emergency_repair(pid):
    s    = load()
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    ctype = COMMERCIAL_TYPES.get(prop["type"], {})
    cost  = ctype.get("emergency_repair_cost", 15_000)
    if s["cash"] < cost:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"]          -= cost
    prop["condition"]   = max(prop.get("condition", 0), 120)  # restore to low-B tier
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Emergency repair completed at {ctype.get('name','building')} on {prop['address']} — condition restored"})
    save(s)
    return jsonify({"success": True, "condition": prop["condition"]})

@app.route('/api/hire_assistant', methods=['POST'])
def api_hire_assistant():
    s    = load()
    data = request.get_json(silent=True) or {}
    key  = data.get("key")
    asst = ASSISTANTS.get(key)
    if not asst:
        return jsonify({"error": "Unknown assistant"}), 400
    if (s.get("level", 0) < asst["unlock_level"]):
        return jsonify({"error": f"Unlocks at Level {asst['unlock_level']}"}), 400
    if s.get("assistants", {}).get(key):
        return jsonify({"error": "Already hired"}), 400
    s.setdefault("assistants", {})[key] = True
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{asst['name']} hired — ${asst['monthly_fee']:,}/mo"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/fire_assistant', methods=['POST'])
def api_fire_assistant():
    s    = load()
    data = request.get_json(silent=True) or {}
    key  = data.get("key")
    asst = ASSISTANTS.get(key)
    if not asst:
        return jsonify({"error": "Unknown assistant"}), 400
    s.setdefault("assistants", {})[key] = False
    s["log"].insert(0, {"day": s["day"], "type": "info",
        "text": f"{asst['name']} dismissed"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
