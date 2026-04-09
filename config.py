"""
config.py — Rolli Home Quote Engine Configuration
Phase 1B

Centralised vendor metadata, defaults, and file paths.
Add new vendors here as pricers are built.
"""

from __future__ import annotations
import os

# ── Root path ─────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(__file__)

def data_path(filename: str) -> str:
    return os.path.join(_ROOT, filename)


# ── Vendor Registry ────────────────────────────────────────────────────────────
#
# Each entry:
#   name:          Display name
#   pricer_class:  Python class (imported lazily in quote_engine)
#   data_file:     JSON pricing database (relative to this dir)
#   dealer_factor: Dealer cost = SRP × dealer_factor
#   pic_account:   PIC Business Systems subdomain (for order submission)
#   phases:        Which quote/order phases are supported
#   products:      High-level product categories available

VENDOR_REGISTRY = {
    "sbm": {
        "name":          "Shades by Matiss",
        "pricer_module": "sbm_pricer",
        "pricer_class":  "SBMPricer",
        "data_file":     "sbm_pricing_complete.json",
        "dealer_factor": 0.36,
        "pic_account":   "100320.picbusiness.com",
        "phases":        ["quote", "order"],
        "products":      ["roller_shade"],
        "notes":         "64% off MSRP — verified from live PIC orders",
    },
    "wsc": {
        "name":          "Window Shade Crafters",
        "pricer_module": "wsc_pricer",
        "pricer_class":  "WSCPricer",
        "data_file":     "wsc_pricing_complete.json",
        "dealer_factor": 0.50,
        "pic_account":   None,
        "phases":        ["quote"],
        "products":      ["roman_shade", "roller_shade"],
        "notes":         "50% off SRP",
    },
    "rollstar": {
        "name":          "Rollstar (Fabritec)",
        "pricer_module": "rollstar_pricer",
        "pricer_class":  "RollstarPricer",
        "data_file":     "rollstar_pricing_complete.json",
        "dealer_factor": 0.50,
        "pic_account":   None,
        "phases":        ["quote"],
        "products":      ["roller_shade"],
        "notes":         "50% trade discount — Jeanette Cruz, Fabritec",
    },
    "sts": {
        "name":          "Style Studio (Fabritec)",
        "pricer_module": "sts_pricer",
        "pricer_class":  "STSPricer",
        "data_file":     "sts_pricing_complete.json",
        "dealer_factor": 0.50,
        "pic_account":   None,
        "phases":        ["quote"],
        "products":      ["roman_shade"],
        "notes":         "50% trade discount — Fabritec brand",
    },
    "ucs": {
        "name":          "US Custom Shades",
        "pricer_module": "ucs_pricer",
        "pricer_class":  "UCSPricer",
        "data_file":     "ucs_pricing_complete.json",
        "dealer_factor": 0.55,
        "pic_account":   "7653.picbusiness.com",
        "phases":        ["quote", "order"],
        "products":      ["roller_shade"],
        "notes":         "45% off — awaiting price catalog PDF from Liam/Brian",
    },
}


# ── PIC Business Systems Credentials ─────────────────────────────────────────
# NOTE: Do NOT commit real credentials. Load from environment in production.
PIC_ACCOUNTS = {
    "sbm": {
        "url":      "https://100320.picbusiness.com",
        "username": "1576",       # TODO: Move to env var
        "password": None,         # Load from PIC_SBM_PASSWORD env var
    },
    "ucs": {
        "url":      "https://7653.picbusiness.com",
        "username": "1576",
        "password": None,         # Load from PIC_UCS_PASSWORD env var
    },
}


# ── Quote Number Counter ───────────────────────────────────────────────────────
# Simple file-based counter. In production, replace with DB or shared file.
QUOTE_COUNTER_FILE = data_path("quote_counter.txt")
QUOTE_STORAGE_DIR  = data_path("quotes")          # quotes/Q-2026-NNNN.json


def next_quote_number() -> str:
    """
    Return the next sequential quote number: Q-YYYY-NNNN.
    Atomically increments the counter file.
    """
    import datetime
    year = datetime.date.today().year

    os.makedirs(QUOTE_STORAGE_DIR, exist_ok=True)

    counter = 1
    if os.path.exists(QUOTE_COUNTER_FILE):
        with open(QUOTE_COUNTER_FILE) as f:
            try:
                counter = int(f.read().strip()) + 1
            except ValueError:
                counter = 1

    with open(QUOTE_COUNTER_FILE, "w") as f:
        f.write(str(counter))

    return f"Q-{year}-{counter:04d}"


# ── Default Quoting Parameters ─────────────────────────────────────────────────
DEFAULTS = {
    "target_margin":   0.40,    # 40% gross margin
    "mount":           "Inside",
    "roll_direction":  "Regular",
    "control_side":    "Right",
    "hembar":          "Standard",
}


# ── Tube / Motor Auto-Selection Thresholds ────────────────────────────────────
# (From shade_selection_rules.md — Rollease Acmeda eBOM v1.26)
# Used by tube_motor_selector.py

TUBE_SELECTION = [
    # (max_width_in, tube_label)  — ordered smallest first
    (48,  '1-1/8"'),
    (72,  '1-1/2"'),
    (96,  '2"'),
    (120, '2-1/2"'),
    (144, '2-1/2" or 3-1/4"'),
    (192, '3-1/4"'),
]

MOTOR_SELECTION = [
    # (max_width_in, fabric_class, torque_nm, motor_key)
    # fabric_class: "light" | "standard" | "heavy"
    (48,  "light",    0.7,  "0.7nm_battery"),
    (48,  "standard", 1.1,  "1.1nm_battery"),
    (48,  "heavy",    2.0,  "2nm_radio"),
    (72,  "light",    1.1,  "1.1nm_battery"),
    (72,  "standard", 2.0,  "2nm_radio"),
    (72,  "heavy",    3.0,  "3nm_radio"),
    (96,  "light",    3.0,  "3nm_radio"),
    (96,  "standard", 6.0,  "6nm_radio"),
    (96,  "heavy",    6.0,  "6nm_radio"),
    (144, "light",    6.0,  "6nm_radio"),
    (144, "standard", 10.0, "10nm_radio"),
    (144, "heavy",    15.0, "15nm_radio"),
    (192, "light",    10.0, "10nm_radio"),
    (192, "standard", 15.0, "15nm_radio"),
    (192, "heavy",    30.0, "30nm_radio"),
]

FABRIC_WEIGHT_CLASS = {
    # SBM fabrics
    "kleenscreen":    "light",
    "serene":         "light",
    "sanctuary bo":   "standard",
    "tusk bo":        "standard",
    "mesa bo":        "standard",
    "balmoral bo":    "heavy",
    "jersey bo":      "heavy",
    "linen bo":       "heavy",
    "silverscreen":   "heavy",
    # Rollstar fabrics
    "sheerweave 2360": "light",
    "sheerweave 2390": "light",
    "sheerweave 2410": "standard",
    "sheerweave 4400": "standard",
    "sheerweave 4800": "heavy",
    "sheerweave 7001": "standard",
    "sheerweave 7400": "standard",
    "sheerweave 7800": "standard",
    "balmoral blackout": "standard",
    "basic blackout":    "standard",
    "darwin blackout":   "standard",
    # Default
    "_default":       "standard",
}

def fabric_weight_class(fabric_name: str) -> str:
    return FABRIC_WEIGHT_CLASS.get(fabric_name.lower(), FABRIC_WEIGHT_CLASS["_default"])
