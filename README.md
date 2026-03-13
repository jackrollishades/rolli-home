# Rolli Home LLC — Quoting Engine
**Rolli Home / Shades by Matiss Technology Stack**
Last updated: March 2026

---

## What This Is

A programmatic pricing engine for window shade products sold through Rolli Home LLC. The system reads raw vendor pricing from structured JSON files and produces dealer costs and suggested retail prices on demand — without requiring access to the PIC portal for every quote.

Two vendors are currently implemented:

| Vendor | File Prefix | Discount |
|---|---|---|
| Shades by Matiss (SBM) | `sbm_*` | 64% off MSRP (factor = 0.36) |
| Fabritec / Woven Shades Collection (WSC) | `wsc_*` | 50% off SRP (factor = 0.50) |

---

## File Reference

| File | Purpose |
|---|---|
| `sbm_pricing_complete.json` | SBM pricing database — 8 price charts, 2,040 MSRP cells + dealer cost cells, motorization (Automate/Somfy/Gaposa), surcharges |
| `sbm_pricer.py` | SBM pricing engine — call `quote()`, `base_dealer_cost()`, `motorization_dealer_cost()` |
| `wsc_pricing_complete.json` | WSC pricing database — 10 Roman shade groups (2,550 cells), 10 Roller shade groups (666 cells), lining grids, motorization |
| `wsc_pricer.py` | WSC pricing engine — call `quote_roman()`, `quote_roller()`, motor/lining add-ons |
| `test_quote.py` | Interactive test harness for SBM pricer — edit the REQUEST block and run |
| `pic_quote_schema.json` | Field map of the e-PIC One portal quote form (100320.picbusiness.com) |
| `shade_selection_rules.md` | Motor and tube selection logic extracted from the Rollease Acmeda eBOM Calculator v1.26 |
| `competitive_pricing_analysis.md` | Competitive pricing analysis vs shadeit.com and rollishades.com |

---

## Quick Start

### Requirements

- Python 3.8+
- No external dependencies for the pricers (`json`, `bisect`, `os` — all stdlib)
- `pdfplumber`, `pandas` only needed if re-running the PDF extraction scripts

### Run a test quote (SBM)

Open `test_quote.py`, edit the REQUEST block at the top, then run:

```bash
python test_quote.py
```

### Run a test quote (WSC)

Open `wsc_pricer.py`, edit the REQUEST block at the bottom, then run:

```bash
python wsc_pricer.py
```

### Use as a module (SBM)

```python
from sbm_pricer import SBMPricer

p = SBMPricer()

# Simple base shade quote
result = p.quote(
    fabric="Sanctuary TL",
    width_in=48,
    height_in=84,
    target_margin=0.40
)
print(f"Dealer cost: ${result['dealer_cost']}")
print(f"Sell price:  ${result['sell_price']}")

# Motorized quote
result = p.quote(
    fabric="Sanctuary BO",
    width_in=48,
    height_in=84,
    motor_brand="automate",
    motor_category="battery_integrated",
    motor_key="25mm_1_1nm",
    target_margin=0.40
)
```

### Use as a module (WSC)

```python
from wsc_pricer import WSCPricer

p = WSCPricer()

# Roman shade — manual, no lining
result = p.quote_roman(group=1, width_in=48, height_in=72)

# Roman shade — with blackout lining, top-down feature, motorized
result = p.quote_roman(
    group=9,
    width_in=36,
    height_in=60,
    lining="blackout",
    top_down=True,
    valance_height_in=6,
    motor_brand="rollease",
    motor_key="1_1nm_battery",
    remote_brand="rollease",
    remote_key="five_channel_remote",
    target_margin=0.40
)

# Roller shade
result = p.quote_roller(group=5, width_in=60, height_in=72)

# List all groups
p.list_groups("roman")
p.list_groups("roller")
```

### Return value structure

Both pricers return the same shape:

```python
{
    "product_type": "roman_shade",  # or "roller_shade", etc.
    "group": 1,
    "width_in": 48,
    "height_in": 72,
    "line_items": [
        {
            "item": "Roman Shade — Group 1 (101-Pacifica), 48\"W × 72\"H",
            "msrp": 694,
            "dealer_cost": 347.0
        },
        # ... additional line items (lining, motor, remote, etc.)
    ],
    "dealer_cost": 347.0,       # total we pay vendor
    "sell_price": 578.33,       # suggested retail at target_margin
    "msrp": 694.0,              # vendor's list price
    "gross_margin": 0.4,
    "target_margin": 0.40
}
```

---

## Pricing Architecture

### SBM — How It Works

- Pricing stored in `sbm_pricing_complete.json` under `price_charts`
- Each chart has `msrp_grid[height_idx][width_idx]` and `dealer_cost_grid[height_idx][width_idx]`
- `DEALER_FACTOR = 0.36` (64% off MSRP — verified from live PIC invoices, orders 80912, 95256, 98500)
- Width/height lookup uses **ceiling bins** — 36" bins to the 37" minimum column
- Margins calculated as: `sell_price = dealer_cost / (1 - target_margin)`

### WSC — How It Works

- Pricing stored in `wsc_pricing_complete.json` under `roman_shades.price_groups` and `roller_shades.price_groups`
- Roman shades: 10 groups × 15 heights (36"–120") × 17 widths (24"–120") = 2,550 cells
- Roller shades: 10 groups with variable grid sizes (widths up to 80", heights up to 80")
- `DEALER_FACTOR = 0.50` (50% off SRP — Fabritec trade pricing)
- Lining is an add-on for roman shades (not built into roller shade prices)
- Valance surcharges (cords-forward, top-down) stored separately per group

### Discount Factor — Important Note

- **SBM**: The SBM catalog originally showed 60% off (factor 0.40). Live PIC invoices for Roller Skyline series confirmed 64% off (factor 0.36). All grids have been updated to 0.36. When the first Premium Roller Series invoice arrives, verify the discount column and update `DEALER_FACTOR` in `sbm_pricer.py` if different.
- **WSC**: 50% confirmed as standard Fabritec trade pricing. No PIC verification yet.

---

## PIC Portal Integration

The file `pic_quote_schema.json` maps the field structure of the e-PIC One portal at `https://100320.picbusiness.com/main.pic`.

This schema is the foundation for Phase 1B: automating order entry into PIC directly from a priced quote, eliminating manual data re-entry.

---

## Roadmap

**Phase 1A** ✅ Complete
SBM pricing JSON + pricer engine + discount factor verification

**Phase 1B** — In Progress
Quoting engine that maps priced output → PIC-compatible order fields using `pic_quote_schema.json`

**Phase 1C** — Planned
WSC ordering integration (Fabritec has its own order portal — field mapping TBD)

**Phase 2** — Planned
Shopify / e-commerce storefront integration — customer-facing configurator feeds into this engine

---

## Key Contacts & Credentials

| System | Detail |
|---|---|
| SBM / PIC Portal | `https://100320.picbusiness.com` — account 100320 |
| Fabritec Sales | 800-828-2500 |
| Fabritec Tech Support | 800-828-2500 (same line, request technical) |

---

## Contributing

1. Pull the latest from the shared repo before making changes
2. Never edit `*_pricing_complete.json` by hand — re-run the extraction script or use a targeted `Edit` patch with verification
3. When adding a new vendor, follow the same JSON structure: `meta`, `price_groups` with `msrp_grid` + `dealer_cost_grid`, `motorization_*`, and a matching `*_pricer.py`
4. Update this README when you add files or change the discount factor
