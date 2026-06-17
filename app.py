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
    "Midtown":            {"price_mult": 0.70, "rent_mult": 0.75, "desc": "Crumbling blocks, forgotten by time",       "tier": "budget"},
    "Northside":          {"price_mult": 0.85, "rent_mult": 0.90, "desc": "Gritty streets, high turnover",             "tier": "budget"},
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
    # ── More funny morale-choice events ───────────────────────────────────────
    {
        "key": "es_tarantula", "weight": 4, "type": "morale_choice",
        "name": "Emotional Support Tarantula", "icon": "🕷️",
        "agree_label": "...Fine.", "decline_label": "Absolutely not.",
        "morale_gain": 8, "damage_chance": 0.20, "damage_pts": 15,
        "message": "Your tenant has acquired an emotional support tarantula. She's very gentle. She's never bitten anyone. That they know of.",
    },
    {
        "key": "circus_skills", "weight": 4, "type": "morale_choice",
        "name": "Circus Skills Practice", "icon": "🎪",
        "agree_label": "Try not to break anything.", "decline_label": "Please take that somewhere else.",
        "morale_gain": 6, "damage_chance": 0.30, "damage_pts": 20,
        "message": "Your tenant has taken up juggling and unicycle riding. In the hallway.",
    },
    {
        "key": "telescope_hole", "weight": 3, "type": "morale_choice",
        "name": "Telescope Installation", "icon": "🔭",
        "agree_label": "That's... a very small hole.", "decline_label": "No modifications to the roof.",
        "morale_gain": 7, "damage_chance": 0.65, "damage_pts": 40,
        "message": "Your tenant wants to cut a small hole in the roof for a 'permanent telescope mount.' It's just a small hole.",
    },
    {
        "key": "home_science", "weight": 4, "type": "morale_choice",
        "name": "Home Science Lab", "icon": "🧪",
        "agree_label": "I probably don't want to know.", "decline_label": "I definitely don't want to know.",
        "morale_gain": 6, "damage_chance": 0.40, "damage_pts": 30,
        "message": "Your tenant is doing 'experiments.' Nothing illegal. They won't say more than that.",
    },
    {
        "key": "accordion", "weight": 4, "type": "morale_choice",
        "name": "Accordion Lessons", "icon": "🪗",
        "agree_label": "Sure, maybe they'll get good eventually.", "decline_label": "Not in my property.",
        "morale_gain": 7, "damage_chance": 0.10, "damage_pts": 10,
        "message": "Your tenant has started learning accordion. Lessons are every Tuesday and Thursday at 9pm.",
    },
    {
        "key": "tiny_house", "weight": 3, "type": "morale_choice",
        "name": "Backyard Tiny House", "icon": "🛖",
        "agree_label": "As long as it's not permanent.", "decline_label": "Please take that down.",
        "morale_gain": 10, "damage_chance": 0.50, "damage_pts": 35,
        "message": "Your tenant built a tiny structure in the backyard for their 'creative space.' It has electricity.",
    },
    {
        "key": "carousel_horse", "weight": 3, "type": "morale_choice",
        "name": "Vintage Carousel Horse", "icon": "🎠",
        "agree_label": "It's not hurting anyone.", "decline_label": "That has to go.",
        "morale_gain": 9, "damage_chance": 0.05, "damage_pts": 10,
        "message": "Your tenant bought a full-size vintage carousel horse from an estate sale. It lives in the living room now. They just want you to know.",
    },
    {
        "key": "outdoor_shower", "weight": 4, "type": "morale_choice",
        "name": "Outdoor Shower", "icon": "🚿",
        "agree_label": "Fine, just make sure it drains.", "decline_label": "This isn't a campsite.",
        "morale_gain": 8, "damage_chance": 0.35, "damage_pts": 25,
        "message": "Your tenant wants to install an outdoor shower on the back porch. 'For after gardening.'",
    },
    {
        "key": "arcade_cabinet", "weight": 4, "type": "morale_choice",
        "name": "Arcade Cabinet Project", "icon": "🕹️",
        "agree_label": "As long as the garage survives.", "decline_label": "Find somewhere else to build it.",
        "morale_gain": 9, "damage_chance": 0.20, "damage_pts": 15,
        "message": "Your tenant is building a full-size arcade cabinet. They need the garage for the next 'few weeks.'",
    },
    {
        "key": "cactus_garden", "weight": 4, "type": "morale_choice",
        "name": "Cactus Garden", "icon": "🌵",
        "agree_label": "Sure, very low maintenance.", "decline_label": "Let's keep the yard as-is.",
        "morale_gain": 6, "damage_chance": 0.15, "damage_pts": 10,
        "message": "Your tenant wants to convert the front yard to a cactus garden. 'Very low maintenance,' they promise.",
    },
    {
        "key": "large_statue", "weight": 3, "type": "morale_choice",
        "name": "Unsettling Garden Statue", "icon": "🗿",
        "agree_label": "I'll allow it.", "decline_label": "That needs to go.",
        "morale_gain": 8, "damage_chance": 0.05, "damage_pts": 5,
        "message": "Your tenant acquired a very large garden statue from an estate sale. It's a little unsettling but they absolutely love it.",
    },
    {
        "key": "power_washer", "weight": 4, "type": "morale_choice",
        "name": "Power Washer Purchase", "icon": "💦",
        "agree_label": "Go for it, but be careful with the siding.", "decline_label": "Please don't.",
        "morale_gain": 7, "damage_chance": 0.35, "damage_pts": 30,
        "message": "Your tenant bought a power washer and wants to 'clean everything.' You know how this ends.",
    },
    {
        "key": "es_goat", "weight": 3, "type": "morale_choice",
        "name": "Emotional Support Goat", "icon": "🐐",
        "agree_label": "It's basically a dog.", "decline_label": "Absolutely not.",
        "morale_gain": 10, "damage_chance": 0.55, "damage_pts": 35,
        "message": "Your tenant insists it's a miniature goat and miniature goats are basically dogs.",
    },
    {
        "key": "clothesline", "weight": 4, "type": "morale_choice",
        "name": "Permanent Clothesline", "icon": "🧺",
        "agree_label": "Sure, just keep it tidy.", "decline_label": "It'll just be in the way.",
        "morale_gain": 5, "damage_chance": 0.10, "damage_pts": 10,
        "message": "Your tenant wants to run a clothesline across the entire backyard. Permanently.",
    },
    {
        "key": "string_quartet", "weight": 4, "type": "morale_choice",
        "name": "String Quartet Practice", "icon": "🎻",
        "agree_label": "Sure, maybe they'll improve.", "decline_label": "Not in my property.",
        "morale_gain": 8, "damage_chance": 0.05, "damage_pts": 10,
        "message": "Your tenant joined a string quartet. They practice here now. They are not good yet.",
    },
    {
        "key": "rooster", "weight": 4, "type": "morale_choice",
        "name": "Surprise Rooster", "icon": "🐓",
        "agree_label": "It's already here, so...", "decline_label": "That has to go. Now.",
        "morale_gain": 9, "damage_chance": 0.30, "damage_pts": 20,
        "message": "Your tenant 'accidentally' got a rooster. Thought it was a hen. It is not a hen.",
    },
    {
        "key": "archery", "weight": 4, "type": "morale_choice",
        "name": "Backyard Archery Range", "icon": "🏹",
        "agree_label": "Just aim at the target, not the fence.", "decline_label": "Too much liability.",
        "morale_gain": 7, "damage_chance": 0.45, "damage_pts": 30,
        "message": "Your tenant has taken up archery. In the backyard.",
    },
    {
        "key": "open_mic", "weight": 4, "type": "morale_choice",
        "name": "Monthly Open Mic Night", "icon": "🎤",
        "agree_label": "Very small crowd though.", "decline_label": "Not at my property.",
        "morale_gain": 8, "damage_chance": 0.20, "damage_pts": 15,
        "message": "Your tenant wants to host a monthly open mic night in the living room. 'Very small crowd,' they say.",
    },
    {
        "key": "sublet_request", "weight": 4, "type": "morale_choice",
        "name": "Couch Sublet", "icon": "🛋️",
        "agree_label": "Just on weekends.", "decline_label": "Absolutely not.",
        "morale_gain": 10, "damage_chance": 0.35, "damage_pts": 25,
        "message": "Your tenant wants to rent out their couch on an app. 'Just on weekends.'",
    },
    {
        "key": "rain_barrels", "weight": 4, "type": "morale_choice",
        "name": "Rain Collection System", "icon": "🪣",
        "agree_label": "Sure, very eco-friendly.", "decline_label": "That's a lot of barrels.",
        "morale_gain": 5, "damage_chance": 0.10, "damage_pts": 10,
        "message": "Your tenant installed 12 rain barrels in the yard. They want to keep them.",
    },
    {
        "key": "storage_unit", "weight": 4, "type": "morale_choice",
        "name": "Unofficial Storage Unit", "icon": "📦",
        "agree_label": "Just temporarily, right?", "decline_label": "This isn't a storage unit.",
        "morale_gain": 7, "damage_chance": 0.25, "damage_pts": 20,
        "message": "Your tenant moved their storage unit contents into the property. 'Just temporarily.'",
    },
    {
        "key": "wall_mural", "weight": 4, "type": "morale_choice",
        "name": "Bedroom Mural", "icon": "🖼️",
        "agree_label": "Show me the design first.", "decline_label": "Not on my walls.",
        "morale_gain": 9, "damage_chance": 0.50, "damage_pts": 35,
        "message": "Your tenant wants to paint a mural on the bedroom wall. 'I'm a pretty good artist,' they say.",
    },
    {
        "key": "crystals", "weight": 4, "type": "morale_choice",
        "name": "EMF Protection Setup", "icon": "🔮",
        "agree_label": "Sure, whatever makes you feel safe.", "decline_label": "I'd rather not have copper mesh on all my windows.",
        "morale_gain": 6, "damage_chance": 0.25, "damage_pts": 20,
        "message": "Your tenant wants to install copper mesh on all the windows. For EMF protection.",
    },
    {
        "key": "bowling_garage", "weight": 3, "type": "morale_choice",
        "name": "Garage Bowling Lane", "icon": "🎳",
        "agree_label": "The garage is a bowling alley now.", "decline_label": "That needs to be undone.",
        "morale_gain": 8, "damage_chance": 0.40, "damage_pts": 30,
        "message": "Your tenant rearranged the garage into a 'mini bowling lane.' It's already done. They're asking if that's okay.",
    },

    # ── Special morale-choice events (cool mechanics) ──────────────────────────
    # cond_gain: if set and player agrees, restores condition by this amount.
    # cash_bonus: if True and player agrees, awards $150–$350 random cash.
    {
        "key": "tenant_repairs", "weight": 3, "type": "morale_choice",
        "name": "Tenant Fixed Something", "icon": "🔧",
        "agree_label": "Nice work, thank you!", "decline_label": "Run it by me first next time.",
        "morale_gain": 10, "damage_chance": 0, "damage_pts": 0, "cond_gain": 25,
        "message": "Your tenant fixed something on their own — properly, too. Better than you would have.",
    },
    {
        "key": "energy_audit", "weight": 3, "type": "morale_choice",
        "name": "DIY Energy Audit", "icon": "💡",
        "agree_label": "Put it into action!", "decline_label": "Appreciate the effort, but no thanks.",
        "morale_gain": 8, "damage_chance": 0, "damage_pts": 0, "cond_gain": 12,
        "message": "Your tenant did a DIY energy audit and left you a detailed report. With a spreadsheet. Color-coded.",
    },
    {
        "key": "rent_bump_offer", "weight": 3, "type": "morale_choice",
        "name": "Rent Bump Offer", "icon": "💸",
        "agree_label": "We appreciate it!", "decline_label": "No need, just pay what you owe.",
        "morale_gain": 5, "damage_chance": 0, "damage_pts": 0, "cash_bonus": True,
        "message": "Your tenant just got a raise and wants to pay a little extra this month as a thank you.",
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
    "coffee_maker":   {"name": "Coffee Maker",             "icon": "☕",  "cost":   499, "unlock_level": 1, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "A decent drip machine. +2 max energy."},
    "desk_fan":       {"name": "Desk Fan",                  "icon": "🌀",  "cost":   199, "unlock_level": 1, "max_energy_bonus": 1, "recharge_bonus": 0, "desc": "Not air conditioning. Close enough. +1 max energy."},
    "house_plant":    {"name": "House Plant",               "icon": "🪴",  "cost":    89, "unlock_level": 2, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Studies show it helps. You're not asking questions. 15% chance to block 1 morale loss/day."},
    "blackout_curtains": {"name": "Blackout Curtains",      "icon": "🪟",  "cost":   149, "unlock_level": 2, "max_energy_bonus": 0, "recharge_bonus": 1, "desc": "Sleep deeper. Wake up less angry. +1 recharge/day."},
    "new_bed":        {"name": "New Bed",                   "icon": "🛏️", "cost": 4_999, "unlock_level": 3, "max_energy_bonus": 0, "recharge_bonus": 1, "desc": "Memory foam. You wake up ready. +1 recharge/day."},
    "mini_fridge":    {"name": "Mini Fridge",               "icon": "🧊",  "cost":   349, "unlock_level": 3, "max_energy_bonus": 2, "recharge_bonus": 0, "desc": "Snacks within arm's reach. Peak efficiency. +2 max energy."},
    "whiteboard":     {"name": "Whiteboard",                "icon": "📋",  "cost":   249, "unlock_level": 4, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You mapped out the whole job. Bob charges less. 6% off all contractor renovation costs."},
    "filing_cabinet": {"name": "Filing Cabinet",            "icon": "🗂️", "cost":   449, "unlock_level": 5, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "Everything is documented. Problems get caught early. 15% lower repair event chance."},
    "headphones":     {"name": "Noise-Cancelling Headphones","icon": "🎧", "cost":   699, "unlock_level": 6, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You stop engaging. They interpret it as professionalism. -1 morale decay/day across all properties."},
    "negotiation_book":{"name": "Negotiation Book",         "icon": "📖",  "cost":   999, "unlock_level": 7, "max_energy_bonus": 0, "recharge_bonus": 0, "desc": "You read it twice. Vendors can tell. +4% on all property sale prices."},
}

# ── Vending Machine Business ───────────────────────────────────────────────────
VM_PRICES    = [1_200, 2_000, 3_000, 4_200, 5_800, 8_000]
VM_LOCATIONS = [
    "Midtown Grocery Entrance",
    "Riverside Park",
    "Northside Community Center",
    "Westwood Office Lobby",
    "Newbay Ferry Terminal",
    "Downtown Bus Station",
]
SNACK_REVENUE = {"cheap": 800, "mid": 2_400, "premium": 4_000}
VINNY_FEE     = 200

# effect types: income_mult (value = extra factor, so 1.0 = 2×),
#               income_zero, income_bonus (flat $), fine (flat $), drain_fast (extra days drained)
VM_LOCATION_EVENTS = {
    "Midtown Grocery Entrance": [
        {"text": "Weekend shopping rush at Midtown Grocery — Machine #{slot} doubled up!",        "type": "positive", "effect": "income_mult",  "value": 1.0},
        {"text": "Power outage hit Midtown — Machine #{slot} was offline all day.",               "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Health inspector surprise visit — Machine #{slot} hit with a fine.",            "type": "negative", "effect": "fine",          "value": 150},
        {"text": "Late-night grocery rush boosted Machine #{slot} sales.",                        "type": "positive", "effect": "income_bonus", "value": 80},
    ],
    "Riverside Park": [
        {"text": "Community 5K finished right by Machine #{slot} — runners cleaned it out early!", "type": "positive", "effect": "drain_fast",   "value": 2},
        {"text": "Park closed for maintenance — Machine #{slot} had no customers today.",         "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Heat wave brought big crowds to Riverside Park — Machine #{slot} earned extra!", "type": "positive", "effect": "income_mult",  "value": 0.5},
        {"text": "Vandals rocked Machine #{slot} overnight — repair fee.",                        "type": "negative", "effect": "fine",          "value": 100},
    ],
    "Northside Community Center": [
        {"text": "Youth basketball tournament — Machine #{slot} couldn't be restocked fast enough!", "type": "positive", "effect": "drain_fast",  "value": 2},
        {"text": "Center closed for deep cleaning — Machine #{slot} offline all day.",             "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Senior bingo night brought an unexpected crowd to Machine #{slot}.",             "type": "positive", "effect": "income_bonus", "value": 75},
        {"text": "Noise complaint from the building manager — Machine #{slot} fined.",            "type": "negative", "effect": "fine",          "value": 80},
    ],
    "Westwood Office Lobby": [
        {"text": "All-hands company meeting packed the lobby — Machine #{slot} had a great day!", "type": "positive", "effect": "income_mult",  "value": 0.5},
        {"text": "Office evacuation drill emptied the building — Machine #{slot} earned nothing.", "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Building management slapped Machine #{slot} with a placement fee.",             "type": "negative", "effect": "fine",          "value": 120},
        {"text": "Company happy hour spilled into the lobby — Machine #{slot} got a late rush.",  "type": "positive", "effect": "income_bonus", "value": 90},
    ],
    "Newbay Ferry Terminal": [
        {"text": "Ferry delays stranded passengers for hours — Machine #{slot} was emptied out!", "type": "positive", "effect": "drain_fast",   "value": 2},
        {"text": "Ferry service suspended today — empty terminal, Machine #{slot} earned nothing.", "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Tourist group rolled through Newbay — Machine #{slot} got an unexpected windfall!", "type": "positive", "effect": "income_mult",  "value": 1.0},
        {"text": "Port authority cited Machine #{slot} for an expired permit.",                   "type": "negative", "effect": "fine",          "value": 175},
    ],
    "Downtown Bus Station": [
        {"text": "Big game day — fans flooded the station, Machine #{slot} had a record day!",   "type": "positive", "effect": "income_mult",  "value": 1.0},
        {"text": "Transit shutdown left the station empty — Machine #{slot} earned nothing.",    "type": "negative", "effect": "income_zero",  "value": 0},
        {"text": "Homeless person sleeping by Machine #{slot} scared off customers — fine day cut short.", "type": "negative", "effect": "fine", "value": 50},
        {"text": "Concert let out nearby and fans rushed the station — Machine #{slot} cleaned out early!", "type": "positive", "effect": "drain_fast", "value": 2},
    ],
}

VM_UPGRADES = {
    "larger_capacity": {"name": "Larger Capacity", "icon": "📦", "cost": 500,   "desc": "+2 days per restock cycle."},
    "card_reader":     {"name": "Card Reader",     "icon": "💳", "cost": 800,   "desc": "+$50/day on top of snack income."},
    "premium_slot":    {"name": "Premium Slot",    "icon": "⭐", "cost": 1_200, "desc": "+25% revenue per cycle."},
}

def _vm_income(tier, upgrades):
    """Return (drain_days, daily_income) for a machine, applying any upgrades."""
    drain = random.randint(4, 8)
    if upgrades.get("larger_capacity"):
        drain += 2
    revenue = SNACK_REVENUE[tier]
    if upgrades.get("premium_slot"):
        revenue = round(revenue * 1.25)
    income = round(revenue / drain)
    if upgrades.get("card_reader"):
        income += 50
    return drain, income

# ── CostPro Wholesale — inventory items ───────────────────────────────────────
COSTPRO_ITEMS = {
    "snacks_cheap":   {"name": "Generic Brand Snacks",  "icon": "🍬", "price": 400,   "desc": "Budget snacks. They sell, barely.",             "category": "vending",     "revenue": 800},
    "snacks_mid":     {"name": "Name Brand Snacks",     "icon": "🍫", "price": 800,   "desc": "Popular brands. Solid margins.",                "category": "vending",     "revenue": 2_400},
    "snacks_premium": {"name": "Artisan Snack Pack",    "icon": "🧁", "price": 1_200, "desc": "Fancy stuff. Customers pay a premium for it.",  "category": "vending",     "revenue": 4_000},
    "soap":           {"name": "Laundry Soap",          "icon": "🧼", "price": 300,   "desc": "Required to operate. Each case lasts 7 days.",  "category": "laundromat"},
    "softener":       {"name": "Fabric Softener",       "icon": "🌸", "price": 500,   "desc": "+20% daily income. Lasts 10 days per case.",    "category": "laundromat"},
    "sheets":         {"name": "Dryer Sheets",          "icon": "🌬️", "price": 400,   "desc": "+15% daily income. Lasts 10 days per case.",   "category": "laundromat"},
    "grip_spray":     {"name": "Grip Spray",            "icon": "💦", "price": 400,   "desc": "Required to run classes. Lasts 7 days per case.", "category": "pole_studio"},
    "protein_shakes": {"name": "Health Drinks",         "icon": "🍹", "price": 600,   "desc": "+25% daily income. Lasts 10 days per case.",   "category": "pole_studio"},
    "branded_merch":  {"name": "Chicken Wings",         "icon": "🍗", "price": 500,   "desc": "+20% daily income. Lasts 10 days per case.",   "category": "pole_studio"},
    "cw_basic_soap":    {"name": "Basic Soap",           "icon": "🧼", "price": 350,   "desc": "Required to operate. 7 days per case.",               "category": "car_wash"},
    "cw_standard_soap": {"name": "Standard Soap",        "icon": "🫧", "price": 500,   "desc": "Required for Standard Wash+. 10 days per case.",      "category": "car_wash"},
    "cw_premium_wax":   {"name": "Premium Wax",          "icon": "✨", "price": 700,   "desc": "Required for Deluxe+. +30% income on Deluxe tier. 8 days per case.", "category": "car_wash"},
    "cw_tire_shine":    {"name": "Tire Shine",           "icon": "🖤", "price": 400,   "desc": "+15% income across all bays. 10 days per case.",      "category": "car_wash"},
    "cw_air_freshener": {"name": "Air Fresheners",       "icon": "🌲", "price": 300,   "desc": "+10% regulars growth rate. 12 days per case.",        "category": "car_wash"},
}

# ── Dirty Money Laundromat ─────────────────────────────────────────────────────
LAUNDROMAT_PRICE                   = 250_000
LAUNDROMAT_START_MACHINES          = 3     # machines included in the purchase
LAUNDROMAT_MAX_MACHINES            = 12
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
}

LAUNDROMAT_UPGRADES = {
    "heavy_duty":       {"name": "Heavy-Duty Motor",   "icon": "⚙️",  "cost": 2_000, "desc": "Breakdown chance 6% → 2%."},
    "card_reader":      {"name": "Card Reader",         "icon": "💳", "cost": 1_500, "desc": "+20% income from this machine."},
    "energy_efficient": {"name": "Energy Efficient",    "icon": "🌿", "cost": 1_000, "desc": "Soap lasts 10 days instead of 7."},
}

# ── Brass Pole Fitness Studio ──────────────────────────────────────────────────
POLE_STUDIO_PRICE            = 600_000
POLE_STUDIO_UNLOCK_LEVEL     = 8
POLE_STUDIO_START_POLES      = 0
POLE_STUDIO_MAX_POLES        = 6
POLE_STUDIO_POLE_PRICES      = [20_000, 25_000, 30_000, 35_000, 45_000, 55_000]
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
}

def _pole_studio_dancer_state(key):
    d = POLE_STUDIO_DANCERS[key]
    return {"hired": False, "mood": d["mood_start"], "demands_fulfilled": 0, "salary_delta": 0}

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
                "Restores +5 condition/day per bay. Broken bays fix themselves overnight. He hums while he works.",
        "effect": "auto_repair",
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
}

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
        "desc": "Four retail-facing storefronts. High traffic, high turnover.",
    },
    "office_building": {
        "name": "Office Building", "icon": "🏢",
        "unit_count": 3, "price": 1_400_000, "overhead": 3_500, "sqft": 12_000,
        "desc": "Professional tenants, longer leases, quieter events.",
    },
    "mixed_use": {
        "name": "Mixed-Use Building", "icon": "🏬",
        "unit_count": 5, "price": 1_800_000, "overhead": 4_000, "sqft": 18_000,
        "desc": "Three commercial floors and two upper-level office suites.",
    },
}

BUSINESS_TENANT_TYPES = {
    "restaurant": {
        "name": "Restaurant", "icon": "🍽️",
        "monthly_rent": 8_500, "lease_days": 56, "event_chance": 0.15,
        "desc": "High traffic. Great rent but inspection events are common.",
        "names": ["Brick & Smoke BBQ", "The Hungry Fork", "Mambo Kitchen", "Noodle House",
                  "Golden Spoon Diner", "Harbor Grill", "Casa Verde", "The Rustic Table"],
    },
    "retail": {
        "name": "Retail Shop", "icon": "🛍️",
        "monthly_rent": 5_500, "lease_days": 28, "event_chance": 0.08,
        "desc": "Short leases, decent income. Moderate turnover.",
        "names": ["QuickMart", "Corner Finds", "Daily Goods", "Bloom Boutique",
                  "The Gear Stop", "Sunrise Goods", "Main St Market", "Fifth Ave Finds"],
    },
    "law_office": {
        "name": "Law Office", "icon": "⚖️",
        "monthly_rent": 9_000, "lease_days": 112, "event_chance": 0.03,
        "desc": "Quiet, long-term, pays well. The dream tenant.",
        "names": ["Fletcher & Associates", "Caldwell Law Group", "Stone Legal",
                  "Harmon & Pierce LLC", "Vance Law", "Burke & Rowe Legal"],
    },
    "salon": {
        "name": "Salon", "icon": "💈",
        "monthly_rent": 6_000, "lease_days": 56, "event_chance": 0.08,
        "desc": "Steady income, reasonable events. Popular anchor tenant.",
        "names": ["Shear Bliss", "The Cut Above", "Platinum Cuts",
                  "Studio 9 Salon", "The Style Bar", "Velvet Scissors"],
    },
    "gym": {
        "name": "Gym", "icon": "🏋️",
        "monthly_rent": 11_000, "lease_days": 84, "event_chance": 0.12,
        "desc": "Highest rent, but equipment wear is no joke.",
        "names": ["Iron District", "Peak Fitness", "Grind Athletics",
                  "FitCore Gym", "Steel & Sweat", "Apex Performance"],
    },
}

def _gen_commercial_market(start_id):
    listings, nid = [], start_id
    types = list(COMMERCIAL_TYPES.keys())
    for t_key in random.sample(types, min(len(types), random.randint(2, 3))):
        ctype  = COMMERCIAL_TYPES[t_key]
        street = random.choice(HOOD_STREETS["Commerce Row"])
        addr   = f"{random.randint(10, 99) * 100 + random.randint(1, 99)} {street}"
        units  = [{"idx": i, "business_type": None, "tenant_name": None,
                   "lease_days_remaining": 0, "monthly_rent": 0, "renewal_pending": False}
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
    """Return (max_energy, recharge) with store item bonuses applied.
    Takes the best stats from the current home and every home below it so
    skipping intermediate homes never silently reduces energy."""
    current     = get_player_home(s)
    current_idx = next(i for i, h in enumerate(PLAYER_HOMES) if h["key"] == current["key"])
    homes_owned = PLAYER_HOMES[:current_idx + 1]
    max_e = max(h["max_energy"] for h in homes_owned)
    rch   = max(h["recharge"]   for h in homes_owned)
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
    cond_mult = 0.5 + (prop["condition"] / MAX_CONDITION) * 0.7
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
    base      = int((prop["sqft"] * 1.1 + prop["bedrooms"] * 400 + prop["bathrooms"] * 150) * n["rent_mult"])
    cond_mult = 0.6 + (prop["condition"] / MAX_CONDITION) * 0.5
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
        "properties": [starter], "market": [], "commercial_market": [], "log": [],
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
    s.setdefault("vending_machines", [])
    s.setdefault("vinny_hired", False)
    s.setdefault("costpro_inventory", {})
    s.setdefault("laundromat", None)
    s.setdefault("pole_studio", None)
    s.setdefault("car_wash", None)
    s.setdefault("commercial_market", [])
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
                    prem_cost = _reno_cost(prop, UPGRADES[key]["base_cost"], CONTRACTORS["premium"]["cost_mult"])
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
        "vending_machines":       s.get("vending_machines", []),
        "vinny_hired":            s.get("vinny_hired", False),
        "costpro_inventory":      s.get("costpro_inventory", {}),
        "laundromat":             s.get("laundromat"),
        "pole_studio":            s.get("pole_studio"),
        "car_wash":               s.get("car_wash"),
        "building_permit":        s.get("building_permit", False),
        "owned_crews":            s.get("owned_crews", []),
        "active_builds":          s.get("active_builds", []),
    })

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
    if prop["purchase_price"] > s["cash"]:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= prop["purchase_price"]
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
        sale = int(calc_market_value(prop) * random.uniform(0.95, 1.05))
    if s.get("owned_items", {}).get("negotiation_book"):
        sale = int(sale * 1.04)
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
    new_repairs            = []
    new_morale_events      = []
    new_renewal_offers     = []
    new_commercial_events  = []
    rent_log               = {}   # prop_id -> summary dict
    squatter_spawned       = False

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
                            "cond_gain":    chosen_event.get("cond_gain", 0),
                            "cash_bonus":   bool(chosen_event.get("cash_bonus")),
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
                        elif chosen_event.get("message"):
                            ev_data["message"] = chosen_event["message"]
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
                        # House plant: 15% chance to block 1 point of morale loss
                        if delta < 0 and owned_items.get("house_plant") and random.random() < 0.15:
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

            for unit in prop.get("units", []):
                btype_key = unit.get("business_type")
                if not btype_key:
                    continue
                btype = BUSINESS_TENANT_TYPES.get(btype_key)
                if not btype:
                    continue
                if unit.get("renewal_pending"):
                    continue  # waiting on player response

                # Daily rent
                daily_rent = int(unit["monthly_rent"] / 28)
                s["cash"] += daily_rent
                s["tax_year_rent_income"] = s.get("tax_year_rent_income", 0) + daily_rent

                # Lease countdown
                unit["lease_days_remaining"] = max(0, unit.get("lease_days_remaining", 0) - 1)

                if unit["lease_days_remaining"] <= 0:
                    unit["renewal_pending"] = True
                    new_commercial_events.append({
                        "prop_id":      prop["id"],
                        "unit_idx":     unit["idx"],
                        "type":         "lease_renewal",
                        "biz_type":     btype_key,
                        "biz_icon":     btype["icon"],
                        "tenant_name":  unit["tenant_name"],
                        "prop_label":   prop_label,
                        "current_rent": unit["monthly_rent"],
                        "bumped_rent":  int(unit["monthly_rent"] * 1.10),
                    })
                    continue

                # Random event roll
                if random.random() < btype["event_chance"] / 28:
                    ev_type = random.choices(
                        ["inspection_fail", "boom_season", "business_closed", "sublet_request"],
                        weights=[3, 3, 2, 2]
                    )[0]
                    if ev_type == "boom_season":
                        bonus = random.randint(2_000, 5_000)
                        s["cash"] += bonus
                        events.append({"prop": prop_label, "type": "positive", "category": "commercial",
                            "text": f"💰 {unit['tenant_name']} had a great month — bonus ${bonus:,}!"})
                        s["log"].insert(0, {"day": current_day, "type": "positive",
                            "text": f"{unit['tenant_name']} boom season — +${bonus:,} at {prop_label}"})
                    elif ev_type == "business_closed":
                        name = unit["tenant_name"]
                        unit["business_type"] = None
                        unit["tenant_name"]   = None
                        unit["lease_days_remaining"] = 0
                        unit["monthly_rent"]  = 0
                        events.append({"prop": prop_label, "type": "warning", "category": "commercial",
                            "text": f"🚪 {name} closed overnight — unit now vacant."})
                        s["log"].insert(0, {"day": current_day, "type": "warning",
                            "text": f"{name} closed at {prop_label} — unit vacant"})
                    elif ev_type == "inspection_fail":
                        cost = random.randint(3_000, 8_000)
                        new_commercial_events.append({
                            "prop_id":     prop["id"],
                            "unit_idx":    unit["idx"],
                            "type":        "inspection_fail",
                            "biz_type":    btype_key,
                            "biz_icon":    btype["icon"],
                            "tenant_name": unit["tenant_name"],
                            "prop_label":  prop_label,
                            "repair_cost": cost,
                        })
                    elif ev_type == "sublet_request":
                        bonus_mo = random.randint(300, 800)
                        new_commercial_events.append({
                            "prop_id":      prop["id"],
                            "unit_idx":     unit["idx"],
                            "type":         "sublet_request",
                            "biz_type":     btype_key,
                            "biz_icon":     btype["icon"],
                            "tenant_name":  unit["tenant_name"],
                            "prop_label":   prop_label,
                            "bonus_monthly": bonus_mo,
                        })

            # Condition degradation (per occupied unit type)
            restaurant_ct = sum(1 for u in prop["units"] if u.get("business_type") == "restaurant")
            gym_ct        = sum(1 for u in prop["units"] if u.get("business_type") == "gym")
            cond_loss     = 0.05 + 0.10 * restaurant_ct + 0.08 * gym_ct
            prop["condition"] = max(0, prop.get("condition", 100) - cond_loss)

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


    # ── Vending machine income + location events + Vinny auto-restock ──────────
    vms      = s.get("vending_machines", [])
    vinny_on = s.get("vinny_hired", False)
    inv      = s.get("costpro_inventory", {})
    for vm in vms:
        had_loc_event = False   # max 1 location event per machine per advance
        for _ in range(days):
            upgrades = vm.setdefault("upgrades", {})
            if vm["status"] == "empty":
                if vinny_on:
                    chosen_tier = next(
                        (t for t in ("premium", "mid", "cheap") if inv.get(f"snacks_{t}", 0) > 0),
                        None
                    )
                    if chosen_tier:
                        inv[f"snacks_{chosen_tier}"] -= 1
                        s["cash"] = max(0, s["cash"] - VINNY_FEE)
                        drain, income = _vm_income(chosen_tier, upgrades)
                        vm["snack_tier"]      = chosen_tier
                        vm["drain_days"]      = drain
                        vm["days_remaining"]  = drain
                        vm["daily_income"]    = income
                        vm["status"]          = "running"
                        tier_names = {"premium": "Artisan", "mid": "Name Brand", "cheap": "Generic"}
                        events.append({
                            "prop": f"Machine #{vm['slot']} — {vm['location']}",
                            "text": f"Cousin Vinny restocked with {tier_names[chosen_tier]} snacks (−${VINNY_FEE} fee)",
                            "type": "neutral", "category": "business",
                        })
                continue

            day_income = vm.get("daily_income", 0)

            # 5% location event per machine per advance
            if not had_loc_event and random.random() < 0.05:
                had_loc_event = True
                loc_pool = VM_LOCATION_EVENTS.get(vm["location"], [])
                if loc_pool:
                    evt    = random.choice(loc_pool)
                    effect = evt["effect"]
                    val    = evt["value"]
                    txt    = evt["text"].format(slot=vm["slot"])
                    if effect == "income_zero":
                        day_income = 0
                    elif effect == "income_mult":
                        day_income = round(day_income * (1 + val))
                    elif effect == "income_bonus":
                        s["cash"] += val
                    elif effect == "fine":
                        s["cash"] = max(0, s["cash"] - val)
                    elif effect == "drain_fast":
                        extra = min(val, max(0, vm["days_remaining"] - 1))
                        s["cash"] += day_income * extra
                        vm["days_remaining"] = max(0, vm["days_remaining"] - extra)
                    events.append({
                        "prop":     f"Machine #{vm['slot']} — {vm['location']}",
                        "text":     txt,
                        "type":     evt["type"],
                        "category": "business",
                    })

            s["cash"] += day_income
            vm["days_remaining"] = max(0, vm["days_remaining"] - 1)
            if vm["days_remaining"] == 0:
                vm["status"] = "empty"
            elif vm["days_remaining"] <= 2:
                vm["status"] = "low"
            else:
                vm["status"] = "running"
    s["vending_machines"]  = vms
    s["costpro_inventory"] = inv

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
                if lm["cleanliness"] < 75:
                    lm["cleanliness"] = min(100, lm["cleanliness"] + 30)

            # Repairman daily cost + auto-fix
            if staff.get("repairman"):
                s["cash"] = max(0, s["cash"] - LAUNDROMAT_STAFF["repairman"]["cost"])
                repair_fee = 0 if lm.get("insurance") else LAUNDROMAT_REPAIR_COST
                for machine in machines:
                    if machine["status"] == "broken":
                        s["cash"] = max(0, s["cash"] - repair_fee)
                        machine["status"] = "working"

            # No soap = no income
            if lm.get("soap_days", 0) <= 0:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 2)
                continue
            lm["soap_days"] -= 1

            working = [m for m in machines if m["status"] == "working"]
            if not working:
                # All machines broken — regulars leave frustrated
                lm["regulars"] = max(0, lm.get("regulars", 0) - 3)
                continue

            # More than half machines broken — regulars getting annoyed
            broken_count = len(machines) - len(working)
            if broken_count > len(machines) // 2:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 1)

            # Filthy conditions drive regulars away
            if lm.get("cleanliness", 100) < 25:
                lm["regulars"] = max(0, lm.get("regulars", 0) - 2)

            # Base income (card reader upgrade: +20% per machine)
            income = sum(
                round(LAUNDROMAT_BASE_INCOME_PER_MACHINE * (1.20 if m.get("upgrades", {}).get("card_reader") else 1.0))
                for m in working
            )

            # Cleanliness multiplier: 0.4 at 0% → 1.8 at 100%
            income = round(income * (0.4 + lm.get("cleanliness", 100) / 100 * 1.4))

            # Optional supply bonuses
            if lm.get("softener_days", 0) > 0:
                income              = round(income * 1.25)
                lm["softener_days"] = max(0, lm["softener_days"] - 1)
            if lm.get("sheets_days", 0) > 0:
                income            = round(income * 1.20)
                lm["sheets_days"] = max(0, lm["sheets_days"] - 1)

            # Regulars bonus: up to +40%
            income = round(income * (1 + lm.get("regulars", 0) / 100 * 0.40))

            # Random event (5% per day)
            if random.random() < 0.05:
                evt    = random.choice(LAUNDROMAT_EVENTS)
                effect = evt["effect"]
                val    = evt["value"]
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
                    picks = random.sample(working, min(2, len(working)))
                    for m in picks:
                        m["status"] = "broken"
                events.append({
                    "prop":     "Dirty Money Laundromat",
                    "text":     evt["text"],
                    "type":     evt["type"],
                    "category": "business",
                })

            # Regulars build (40% chance of +3 per open day)
            if random.random() < 0.40:
                lm["regulars"] = min(100, lm.get("regulars", 0) + 3)

            s["cash"]         += income
            lm["total_earned"] = lm.get("total_earned", 0) + income

        s["laundromat"] = lm

    # ── Brass Pole Fitness Studio advance ─────────────────────────────────────
    ps = s.get("pole_studio")
    if ps and ps.get("owned"):
        staff         = ps.setdefault("staff",       {"vibe_manager": False, "studio_cleaner": False})
        ps.setdefault("dancers",     {k: _pole_studio_dancer_state(k) for k in POLE_STUDIO_DANCERS})
        ps.setdefault("poles",       [{"id": i, "upgrades": {}, "broken": False}
                                      for i in range(ps.get("pole_count", POLE_STUDIO_START_POLES))])
        ps.setdefault("active_demands", [])
        poles = ps["poles"]

        for _day in range(days):
            # Insurance weekly charge
            if ps.get("insurance"):
                ps["insurance_days"] = ps.get("insurance_days", 7) - 1
                if ps["insurance_days"] <= 0:
                    ps["insurance_days"] = 7
                    s["cash"] = max(0, s["cash"] - POLE_STUDIO_INSURANCE_WEEKLY)

            # Atmosphere + cleanliness natural decay
            ps["atmosphere"]  = max(0, ps.get("atmosphere", 100)  - POLE_STUDIO_ATM_DECAY)
            ps["cleanliness"] = max(0, ps.get("cleanliness", 100) - POLE_STUDIO_CLEAN_DECAY)

            # Vibe manager: auto-maintain atmosphere
            if staff.get("vibe_manager"):
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["vibe_manager"]["cost"])
                if ps["atmosphere"] < 75:
                    ps["atmosphere"] = min(100, ps["atmosphere"] + 20)

            # Studio cleaner: auto-clean
            if staff.get("studio_cleaner"):
                s["cash"] = max(0, s["cash"] - POLE_STUDIO_STAFF["studio_cleaner"]["cost"])
                if ps["cleanliness"] < 70:
                    ps["cleanliness"] = min(100, ps["cleanliness"] + 25)

            # Pole breakdowns (random unless chrome polish upgrade)
            for pole in poles:
                if not pole.get("broken"):
                    bd = 0.025 if not pole.get("upgrades", {}).get("chrome_polish") else 0.01
                    if random.random() < bd:
                        pole["broken"] = True

            # Demand countdown and auto-expiry
            new_demands = []
            for dem in ps.get("active_demands", []):
                dem["days_left"] = dem.get("days_left", 5) - 1
                if dem["days_left"] > 0:
                    new_demands.append(dem)
                else:
                    # Demand expired — apply reject effects and mark dancer unhappy
                    spec = next((d for d in POLE_STUDIO_DEMANDS if d["key"] == dem["key"]), None)
                    if spec:
                        dk = spec["dancer"]
                        _apply_demand_effects(s, ps, spec["reject"], dk)
                        if spec["reject"].get("quit") and ps["dancers"].get(dk, {}).get("hired"):
                            ps["dancers"][dk]["hired"] = False
                            events.append({"prop": "Brass Pole Fitness Studio",
                                           "text": f"{POLE_STUDIO_DANCERS[dk]['name']} quit. The demand expired.",
                                           "type": "negative", "category": "business"})
                    events.append({"prop": "Brass Pole Fitness Studio",
                                   "text": f"A dancer demand expired unresolved.",
                                   "type": "warning", "category": "business"})
            ps["active_demands"] = new_demands

            # Possibly spawn a new demand (6% chance per day, one at a time)
            if len(ps["active_demands"]) < 2 and random.random() < 0.06:
                hired_keys = [k for k, dd in ps["dancers"].items() if dd.get("hired")]
                if hired_keys:
                    dk = random.choice(hired_keys)
                    eligible = [d for d in POLE_STUDIO_DEMANDS
                                if d["dancer"] == dk
                                and d["key"] not in [ad["key"] for ad in ps["active_demands"]]
                                and d["key"] not in ps.get("fulfilled_demands", [])]
                    if eligible:
                        spec = random.choice(eligible)
                        ps["active_demands"].append({
                            "key": spec["key"],
                            "dancer": dk,
                            "days_left": spec["deadline"],
                        })
                        events.append({"prop": "Brass Pole Fitness Studio",
                                       "text": f"{POLE_STUDIO_DANCERS[dk]['name']} has a new demand.",
                                       "type": "warning", "category": "business"})

            # Grip spray required to run
            if ps.get("grip_spray_days", 0) <= 0:
                ps["atmosphere"] = max(0, ps.get("atmosphere", 50) - 10)
                continue
            ps["grip_spray_days"] -= 1

            # Mood decay per dancer
            for dk, dd in ps["dancers"].items():
                if dd.get("hired") and dk != "gary":
                    dd["mood"] = max(0, dd.get("mood", 72) - POLE_STUDIO_DANCERS[dk]["mood_decay"])

            # Count active working poles with hired dancers
            working_poles = [
                pole for i, pole in enumerate(poles)
                if not pole.get("broken")
                and list(ps["dancers"].values())[i if i < len(ps["dancers"]) else 0].get("hired", False)
            ]
            hired_dancers = [dd for dd in ps["dancers"].values() if dd.get("hired")]
            active_count  = min(len(working_poles), len(hired_dancers))
            if active_count == 0:
                continue

            # Base income per active dancer-pole pair
            income = 0
            for i, dd in enumerate([dd for dd in ps["dancers"].values() if dd.get("hired")]):
                dk_key = [k for k, v in ps["dancers"].items() if v is dd][0]
                base   = POLE_STUDIO_DANCERS[dk_key]["base_income"]
                # Mood multiplier: 0.5 at 0% → 1.3 at 100%
                mood_m = 0.5 + dd.get("mood", 50) / 100 * 0.8
                # LED halo upgrade on matched pole
                pole_i = list(ps["dancers"].keys()).index(dk_key)
                led_m  = 1.2 if (pole_i < len(poles) and poles[pole_i].get("upgrades", {}).get("led_halo")) else 1.0
                grip_m = 1.1 if (pole_i < len(poles) and poles[pole_i].get("upgrades", {}).get("grip_coating")) else 1.0
                income += round(base * mood_m * led_m * grip_m)

            # Atmosphere + cleanliness multipliers
            atm_m = 0.5 + ps.get("atmosphere", 100) / 100 * 0.7
            cln_m = 0.6 + ps.get("cleanliness", 100) / 100 * 0.5
            income = round(income * atm_m * cln_m)

            # Reputation multiplier (0-100 → 0.7x–1.5x)
            rep_m  = 0.7 + ps.get("reputation", 0) / 100 * 0.8
            income = round(income * rep_m)

            # Members multiplier
            mem_m  = 1.0 + ps.get("members", 0) / 100 * 0.5
            income = round(income * mem_m)

            # CostPro supply bonuses
            if ps.get("protein_shake_days", 0) > 0:
                income = round(income * 1.25)
                ps["protein_shake_days"] -= 1
            if ps.get("merch_days", 0) > 0:
                income = round(income * 1.20)
                ps["merch_days"] -= 1

            # Random event (5% per day)
            if random.random() < 0.05:
                evt    = random.choice(POLE_STUDIO_EVENTS)
                effect = evt["effect"]
                val    = evt["value"]
                if effect == "members":
                    ps["members"] = max(0, min(100, ps.get("members", 0) + int(val)))
                elif effect == "reputation":
                    ps["reputation"] = max(0, min(100, ps.get("reputation", 0) + int(val)))
                elif effect == "income":
                    income = max(0, income + int(val))
                elif effect == "income_mult":
                    income = max(0, round(income * (1 + val)))
                elif effect == "atmosphere":
                    ps["atmosphere"] = max(0, min(100, ps.get("atmosphere", 100) + int(val)))
                elif effect == "cleanliness":
                    ps["cleanliness"] = max(0, min(100, ps.get("cleanliness", 100) + int(val)))
                elif effect == "break_pole":
                    working_ps = [p for p in poles if not p.get("broken")]
                    if working_ps:
                        random.choice(working_ps)["broken"] = True
                events.append({
                    "prop":     "Brass Pole Fitness Studio",
                    "text":     evt["text"],
                    "type":     evt["type"],
                    "category": "business",
                })

            # Reputation and members slow drift
            if random.random() < 0.30:
                ps["reputation"] = min(100, ps.get("reputation", 0) + 1)
            if random.random() < 0.25:
                ps["members"] = min(100, ps.get("members", 0) + 1)
            # Small decay when reputation is high (harder to maintain)
            if ps.get("reputation", 0) > 70 and random.random() < 0.20:
                ps["reputation"] = max(0, ps["reputation"] - 1)

            s["cash"]          += income
            ps["total_earned"]  = ps.get("total_earned", 0) + income

        s["pole_studio"] = ps

    # ── Slippery When Washed advance ──────────────────────────────────────────
    cw = s.get("car_wash")
    if cw and cw.get("owned"):
        bays      = cw.setdefault("bays", [{"id": i, "upgrades": {}, "broken": False}
                                            for i in range(cw.get("bay_count", CAR_WASH_START_BAYS))])
        staff     = cw.setdefault("staff", {k: False for k in CAR_WASH_STAFF})
        g_upgs    = cw.setdefault("global_upgrades", {})
        sup       = cw.setdefault("supplies", {})

        for _day in range(days):
            # Insurance weekly charge
            if cw.get("insurance"):
                cw["insurance_days"] = cw.get("insurance_days", 7) - 1
                if cw["insurance_days"] <= 0:
                    cw["insurance_days"] = 7
                    s["cash"] = max(0, s["cash"] - CAR_WASH_INSURANCE_WEEKLY)

            # Water pressure decay (slower with industrial tank)
            water_decay = CAR_WASH_WATER_DECAY * (0.4 if g_upgs.get("water_tank") else 1.0)
            cw["water_pressure"] = max(0, cw.get("water_pressure", 100) - water_decay)

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

            # No basic soap = no income
            if sup.get("cw_basic_soap", 0) <= 0:
                cw["regulars"] = max(0, cw.get("regulars", 0) - 3)
                continue
            sup["cw_basic_soap"] -= 1

            # Determine active package
            pkg_key = _get_car_wash_package(cw)
            pkg_mult = CAR_WASH_PACKAGES[pkg_key]["mult"]

            # Consume package-specific supplies
            if pkg_key in ("standard", "deluxe", "premium") and sup.get("cw_standard_soap", 0) > 0:
                sup["cw_standard_soap"] = max(0, sup["cw_standard_soap"] - 1)
            if pkg_key in ("deluxe", "premium") and sup.get("cw_premium_wax", 0) > 0:
                sup["cw_premium_wax"] = max(0, sup["cw_premium_wax"] - 1)

            # Income per working bay
            working_bays = [b for b in bays if not b.get("broken")]
            income = 0
            for bay in working_bays:
                upgs    = bay.get("upgrades", {})
                base    = CAR_WASH_BASE_INCOME
                bay_m   = 1.0
                if upgs.get("nozzles"):  bay_m *= 1.25
                if upgs.get("foam"):     bay_m *= 1.20
                if upgs.get("led_sign"): bay_m *= 1.15
                if upgs.get("conveyor"): bay_m *= 1.30
                # Condition penalty: 0.6 at 0% → 1.0 at 100%
                cond_m  = 0.6 + bay.get("condition", 100) / 100 * 0.4
                income += round(base * bay_m * cond_m)

            # Global multipliers
            income = round(income * pkg_mult)

            # Brianna output boost
            if staff.get("brianna"): income = round(income * 1.20)

            # Squeegee Kid: 35% chance of not showing up when hired
            if staff.get("squeegee_kid"):
                showed_up = random.random() < 0.65
                if not showed_up:
                    # no-show penalty only if no conveyor belt on any bay
                    has_conveyor = any(b.get("upgrades", {}).get("conveyor") for b in working_bays)
                    if not has_conveyor:
                        income = round(income * 0.85)

            # Dave vacuum bonus
            if staff.get("dave"): income = round(income * 1.12)

            # Water pressure multiplier: 0.5 at 0% → 1.0 at 100%
            water_m = 0.5 + cw.get("water_pressure", 100) / 100 * 0.5
            income  = round(income * water_m)

            # Morale multiplier: 0.6 at 0% → 1.1 at 100%
            morale_m = 0.6 + cw.get("morale", 80) / 100 * 0.5
            income   = round(income * morale_m)

            # Supply bonuses
            if sup.get("cw_tire_shine", 0) > 0:
                income = round(income * 1.15)
                sup["cw_tire_shine"] = max(0, sup["cw_tire_shine"] - 1)
            if sup.get("cw_air_freshener", 0) > 0:
                cw["regulars"] = min(100, cw.get("regulars", 0) + 0.1)

            # Reputation + regulars multipliers
            rep_m = 0.7 + cw.get("reputation", 0) / 100 * 0.8
            reg_m = 1.0 + cw.get("regulars",   0) / 100 * 0.5
            income = round(income * rep_m * reg_m)

            # Random event 5% per day
            if random.random() < 0.05:
                evt    = random.choice(CAR_WASH_EVENTS)
                effect = evt["effect"]
                val    = evt["value"]
                if effect == "income":
                    income = max(0, income + int(val))
                elif effect == "reputation":
                    cw["reputation"] = max(0, min(100, cw.get("reputation", 0) + int(val)))
                elif effect == "regulars":
                    cw["regulars"] = max(0, min(100, cw.get("regulars", 0) + int(val)))
                elif effect == "morale":
                    cw["morale"] = max(0, min(100, cw.get("morale", 80) + int(val)))
                elif effect == "water":
                    cw["water_pressure"] = max(0, min(100, cw.get("water_pressure", 100) + int(val)))
                elif effect == "equip":
                    for b in bays:
                        b["condition"] = max(0, b.get("condition", 100) + int(val))
                elif effect == "equip_all":
                    for b in bays:
                        b["condition"] = max(0, b.get("condition", 100) + int(val))
                elif effect == "break_bay":
                    working = [b for b in bays if not b.get("broken")]
                    if working:
                        random.choice(working)["broken"] = True
                events.append({"prop": "Slippery When Washed", "text": evt["text"],
                                "type": evt["type"], "category": "business"})

            # Regulars slow build
            if random.random() < 0.35:
                cw["regulars"] = min(100, cw.get("regulars", 0) + 2)
            if random.random() < 0.25 and g_upgs.get("loyalty_machine"):
                cw["regulars"] = min(100, cw.get("regulars", 0) + 2)
            if cw.get("reputation", 0) > 60 and random.random() < 0.15:
                cw["reputation"] = max(0, cw["reputation"] - 1)

            s["cash"]         += income
            cw["total_earned"] = cw.get("total_earned", 0) + income

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
        "events":             events,
        "repairs":            new_repairs,
        "morale_events":      new_morale_events,
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
    cash_awarded     = 0
    morale_before    = t.get("morale", 50)

    if agree:
        morale_change = event_cfg["morale_gain"]
        t["morale"]   = min(100, t.get("morale", 50) + morale_change)

        if event_cfg.get("cond_gain"):
            # Special: agreement restores condition instead of risking damage
            condition_change   = event_cfg["cond_gain"]
            prop["condition"]  = min(MAX_CONDITION, prop["condition"] + condition_change)
        elif event_cfg.get("damage_chance") and random.random() < event_cfg["damage_chance"]:
            condition_change   = -event_cfg["damage_pts"]
            prop["condition"]  = max(0, prop["condition"] + condition_change)

        if event_cfg.get("cash_bonus"):
            cash_awarded = random.randint(150, 350)
            s["cash"]   += cash_awarded

        log_suffix = ""
        if condition_change > 0:
            log_suffix += f" — condition +{condition_change}"
        elif condition_change < 0:
            log_suffix += f" — caused {abs(condition_change)} pts condition damage"
        if cash_awarded:
            log_suffix += f" — received ${cash_awarded:,} bonus"
        s["log"].append({"day": s["day"], "type": "info",
            "text": f"Agreed to {t['name']}'s {event_cfg['name']} request at {prop['type']} in {prop['neighborhood']}{log_suffix}"})
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
        "cash_awarded":     cash_awarded,
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

@app.route('/api/vending/buy', methods=['POST'])
def api_vending_buy():
    s    = load()
    data = request.json or {}
    tier = data.get("snack_tier", "cheap")
    if tier not in SNACK_REVENUE:
        return jsonify({"error": "Unknown snack tier"}), 400
    vms = s.setdefault("vending_machines", [])
    if len(vms) >= 6:
        return jsonify({"error": "You already own the maximum of 6 machines"}), 400
    slot  = len(vms) + 1
    price = VM_PRICES[slot - 1]
    if s["cash"] < price:
        return jsonify({"error": f"Not enough cash — need ${price:,}"}), 400
    inv     = s.setdefault("costpro_inventory", {})
    inv_key = f"snacks_{tier}"
    if inv.get(inv_key, 0) < 1:
        return jsonify({"error": f"No {tier} snacks in inventory — visit CostPro first"}), 400
    inv[inv_key] -= 1
    s["cash"] -= price
    drain, income = _vm_income(tier, {})
    vm = {
        "id":             int(s["day"] * 1000 + slot),
        "slot":           slot,
        "location":       VM_LOCATIONS[slot - 1],
        "snack_tier":     tier,
        "drain_days":     drain,
        "days_remaining": drain,
        "daily_income":   income,
        "status":         "running",
        "upgrades":       {},
    }
    vms.append(vm)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bought Vending Machine #{slot} at {vm['location']} for ${price:,}!"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/restock', methods=['POST'])
def api_vending_restock():
    s    = load()
    data = request.json or {}
    vm_id = data.get("vm_id")
    tier  = data.get("snack_tier", "cheap")
    if tier not in SNACK_REVENUE:
        return jsonify({"error": "Unknown snack tier"}), 400
    vms = s.get("vending_machines", [])
    vm  = next((v for v in vms if v["id"] == vm_id), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    inv     = s.setdefault("costpro_inventory", {})
    inv_key = f"snacks_{tier}"
    if inv.get(inv_key, 0) < 1:
        return jsonify({"error": f"No {tier} snacks in inventory — visit CostPro first"}), 400
    inv[inv_key] -= 1
    drain, income = _vm_income(tier, vm.get("upgrades", {}))
    vm["snack_tier"]      = tier
    vm["drain_days"]      = drain
    vm["days_remaining"]  = drain
    vm["daily_income"]    = income
    vm["status"]          = "running"
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Restocked Machine #{vm['slot']} at {vm['location']} with {tier} snacks."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/toggle_vinny', methods=['POST'])
def api_vending_toggle_vinny():
    s = load()
    s["vinny_hired"] = not s.get("vinny_hired", False)
    save(s)
    return jsonify({"success": True, "vinny_hired": s["vinny_hired"]})

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
    elif item.get("category") == "pole_studio":
        ps = s.get("pole_studio")
        if not ps:
            s["cash"] += total
            return jsonify({"error": "You don't own the Brass Pole Fitness Studio yet!"}), 400
        has_grip_coat = any(p.get("upgrades", {}).get("grip_coating") for p in ps.get("poles", []))
        if key == "grip_spray":
            days_per_case = 10 if has_grip_coat else 7
            ps["grip_spray_days"] = ps.get("grip_spray_days", 0) + days_per_case * qty
        elif key == "protein_shakes":
            ps["protein_shake_days"] = ps.get("protein_shake_days", 0) + 10 * qty
        elif key == "branded_merch":
            ps["merch_days"] = ps.get("merch_days", 0) + 10 * qty
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
    else:
        inv     = s.setdefault("costpro_inventory", {})
        inv[key] = inv.get(key, 0) + qty
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Bought ×{qty} {item['name']} from CostPro for ${total:,}."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/vending/upgrade', methods=['POST'])
def api_vending_upgrade():
    s    = load()
    data = request.json or {}
    vm_id       = data.get("vm_id")
    upgrade_key = data.get("upgrade_key")
    upgrade     = VM_UPGRADES.get(upgrade_key)
    if not upgrade:
        return jsonify({"error": "Unknown upgrade"}), 400
    vms = s.get("vending_machines", [])
    vm  = next((v for v in vms if v["id"] == vm_id), None)
    if not vm:
        return jsonify({"error": "Machine not found"}), 400
    upgrades = vm.setdefault("upgrades", {})
    if upgrades.get(upgrade_key):
        return jsonify({"error": "Already installed on this machine"}), 400
    if s["cash"] < upgrade["cost"]:
        return jsonify({"error": f"Not enough cash — need ${upgrade['cost']:,}"}), 400
    s["cash"] -= upgrade["cost"]
    upgrades[upgrade_key] = True
    if upgrade_key == "larger_capacity":
        vm["days_remaining"] = vm.get("days_remaining", 0) + 2
        vm["drain_days"]     = vm.get("drain_days", 6) + 2
    elif upgrade_key == "card_reader":
        vm["daily_income"] = vm.get("daily_income", 0) + 25
    elif upgrade_key == "premium_slot":
        vm["daily_income"] = round(vm.get("daily_income", 0) * 1.25)
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Installed {upgrade['name']} on Machine #{vm['slot']} for ${upgrade['cost']:,}!"})
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
    s["laundromat"] = {
        "owned":          True,
        "cleanliness":    20,
        "machines":       [{"id": i, "status": "working", "upgrades": {}} for i in range(LAUNDROMAT_START_MACHINES)],
        "soap_days":      0,
        "softener_days":  0,
        "sheets_days":    0,
        "staff":          {"janitor": False, "repairman": False},
        "regulars":       0,
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
    price_idx = len(machines) - LAUNDROMAT_START_MACHINES
    price     = LAUNDROMAT_MACHINE_PRICES[price_idx]
    if s["cash"] < price:
        return jsonify({"error": f"Need ${price:,}"}), 400
    s["cash"] -= price
    new_id = len(machines)
    machines.append({"id": new_id, "status": "working", "upgrades": {}})
    lm["machines"] = machines
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"Added Machine #{new_id + 1} to the Dirty Money Laundromat for ${price:,}!"})
    save(s)
    return jsonify({"success": True})

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
    s["pole_studio"] = {
        "owned": True, "pole_count": POLE_STUDIO_START_POLES,
        "poles": [{"id": i, "upgrades": {}, "broken": False}
                  for i in range(POLE_STUDIO_START_POLES)],
        "dancers": {k: _pole_studio_dancer_state(k) for k in POLE_STUDIO_DANCERS},
        "staff": {"vibe_manager": False, "studio_cleaner": False},
        "atmosphere": 80, "cleanliness": 90, "reputation": 10, "members": 0,
        "grip_spray_days": 0, "protein_shake_days": 0, "merch_days": 0,
        "insurance": False, "insurance_days": 7,
        "active_demands": [], "fulfilled_demands": [], "total_earned": 0,
    }
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": "Brass Pole Fitness Studio acquired. The poles are chrome. The vibe is immaculate."})
    save(s)
    return jsonify({"success": True})

@app.route('/api/pole_studio/buy_pole', methods=['POST'])
def api_pole_studio_buy_pole():
    s  = load()
    ps = s.get("pole_studio")
    if not ps or not ps.get("owned"):
        return jsonify({"error": "No studio"}), 400
    pc = ps.get("pole_count", POLE_STUDIO_START_POLES)
    if pc >= POLE_STUDIO_MAX_POLES:
        return jsonify({"error": "Max poles reached"}), 400
    dancers     = ps.get("dancers", {})
    hired_count = sum(1 for dd in dancers.values() if dd.get("hired"))
    if hired_count < pc:
        return jsonify({"error": "Hire a dancer for the current pole before building another."}), 400
    price = POLE_STUDIO_POLE_PRICES[pc]
    if s["cash"] < price:
        return jsonify({"error": "Not enough cash"}), 400
    s["cash"] -= price
    ps["pole_count"] = pc + 1
    ps.setdefault("poles", []).append({"id": pc, "upgrades": {}, "broken": False})
    s["log"].insert(0, {"day": s["day"], "type": "neutral",
        "text": f"New pole installed (#{pc + 1}). Ready for a dancer."})
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
    hired_count = sum(1 for dd in dancers.values() if dd.get("hired"))
    if hired_count >= ps.get("pole_count", POLE_STUDIO_START_POLES):
        return jsonify({"error": "Build another pole first"}), 400
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
        "reputation": 5, "regulars": 0,
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
    # Generate 3 random business applicants
    biz_types = list(BUSINESS_TENANT_TYPES.keys())
    chosen    = random.sample(biz_types, min(3, len(biz_types)))
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
    unit["business_type"]      = biz_type
    unit["tenant_name"]        = biz_name or random.choice(btype["names"])
    unit["monthly_rent"]       = btype["monthly_rent"]
    unit["lease_days_remaining"] = btype["lease_days"]
    unit["renewal_pending"]    = False
    unit["applicants"]         = []
    ctype = COMMERCIAL_TYPES[prop["type"]]
    s["log"].insert(0, {"day": s["day"], "type": "positive",
        "text": f"{unit['tenant_name']} ({btype['name']}) moved into {ctype['name']} on {prop['address']}"})
    save(s)
    return jsonify({"success": True})

@app.route('/api/commercial/event_respond', methods=['POST'])
def api_commercial_event_respond():
    s    = load()
    data = request.get_json(silent=True) or {}
    pid      = data.get("prop_id")
    uidx     = data.get("unit_idx")
    ev_type  = data.get("event_type")
    choice   = data.get("choice")   # "accept" / "decline" / "bump"
    prop = next((p for p in s["properties"] if p["id"] == pid and p.get("commercial")), None)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    unit = next((u for u in prop["units"] if u["idx"] == uidx), None)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    ctype = COMMERCIAL_TYPES[prop["type"]]
    btype = BUSINESS_TENANT_TYPES.get(unit.get("business_type", ""))
    prop_label = f"{ctype['name']} — Commerce Row"

    if ev_type == "lease_renewal":
        if choice == "accept":
            unit["lease_days_remaining"] = btype["lease_days"] if btype else 56
            unit["renewal_pending"]      = False
            s["log"].insert(0, {"day": s["day"], "type": "positive",
                "text": f"{unit['tenant_name']} renewed lease at {prop_label} — same rate"})
        elif choice == "bump":
            unit["monthly_rent"]         = int(unit["monthly_rent"] * 1.10)
            unit["lease_days_remaining"] = btype["lease_days"] if btype else 56
            unit["renewal_pending"]      = False
            s["log"].insert(0, {"day": s["day"], "type": "positive",
                "text": f"{unit['tenant_name']} renewed at +10% — now ${unit['monthly_rent']:,}/mo at {prop_label}"})
        elif choice == "decline":
            name = unit["tenant_name"]
            unit["business_type"]        = None
            unit["tenant_name"]          = None
            unit["lease_days_remaining"] = 0
            unit["monthly_rent"]         = 0
            unit["renewal_pending"]      = False
            s["log"].insert(0, {"day": s["day"], "type": "warning",
                "text": f"{name} vacated after lease expired at {prop_label}"})

    elif ev_type == "inspection_fail":
        cost = data.get("repair_cost", 0)
        if choice == "pay":
            if s["cash"] < cost:
                return jsonify({"error": f"Need ${cost:,}"}), 400
            s["cash"] -= cost
            s["log"].insert(0, {"day": s["day"], "type": "info",
                "text": f"Paid ${cost:,} inspection repair at {prop_label} — {unit['tenant_name']} stays"})
        elif choice == "ignore":
            name = unit["tenant_name"]
            unit["business_type"]        = None
            unit["tenant_name"]          = None
            unit["lease_days_remaining"] = 0
            unit["monthly_rent"]         = 0
            unit["renewal_pending"]      = False
            s["log"].insert(0, {"day": s["day"], "type": "warning",
                "text": f"{name} left after failed inspection at {prop_label}"})

    elif ev_type == "sublet_request":
        bonus_mo = data.get("bonus_monthly", 0)
        if choice == "approve":
            unit["monthly_rent"] = unit.get("monthly_rent", 0) + bonus_mo
            s["log"].insert(0, {"day": s["day"], "type": "positive",
                "text": f"Approved sublet at {prop_label} — rent +${bonus_mo:,}/mo"})
        else:
            s["log"].insert(0, {"day": s["day"], "type": "info",
                "text": f"Denied sublet request at {prop_label}"})

    save(s)
    return jsonify({"success": True, "cash": s["cash"]})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    s = new_game()
    save(s)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
