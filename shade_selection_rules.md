# Shade Fabrication Selection Rules
**Source:** Rollease Acmeda eBOM Calculator v1.26 (shade-fabrication-calculator.xltm, Nov 2025)
**Region:** US (Global where noted)
**Purpose:** Logic for automated motor, tube, and hardware selection in the Rolli Home quoting engine

---

## How the Calculator Works (Core Logic)

The calculator determines correct components in this sequence:

1. **Inputs:** Width, Drop (height), Fabric type (density + thickness)
2. **Calculate torque required** — based on fabric weight × width × drop
3. **Select tube** — smallest tube that keeps deflection within limit (0.105% = 1.05 mm/m) at that width
4. **Select motor/control** — smallest motor with torque ≥ required that is compatible with the selected tube
5. **Validate** — confirm motor fits tube bore, bracket supports roll diameter

---

## Tube Selection (US Region)

Tubes are selected by **deflection limit**: the tube must not sag more than 0.105% of its span under load.
The calculator picks the **smallest adequate tube** (lightest = cheaper + easier to install).

### US Tube Reference Data

| Code | Description | OD (mm) | Mass (kg/m) | I_min (mm⁴) | EI (Nm²) | Max Length (m / in) |
|------|-------------|---------|-------------|-------------|----------|---------------------|
| RTEA1 | **1"** | 26.7 | 0.28 | 8,191 | 557 | 3.66m / 144" |
| RTEA2 | **1-1/8"** | 29.5 | 0.30 | 11,101 | 755 | 4.88m / 192" |
| RTEA3 | **1-1/4"** | 32.76 | 0.356 | 15,609 | 1,061 | 4.88m / 192" |
| RTEA4 | **1-1/2"** | 38.6 | 0.425 | 26,223 | 1,783 | 4.88m / 192" |
| RB93-23x5 | **1-1/2" Switch** | 45 | 0.678 | 49,362 | 3,357 | 4.88m / 192" |
| RTEA5 | **2"** | 50.8 | 0.736 | 74,381 | 5,058 | 4.88m / 192" |
| RTEA6 | **2-1/2"** | 65.2 | 1.31 | 224,028 | 15,234 | 4.88m / 192" |
| RTEA7 | **3-1/4"** | 83.1 | 3.08 | 798,623 | 54,306 | 4.88m / 192" |

**Key rule:** 1" tube max length is 144". For widths > 144", always use 1-1/8" or larger.

### Practical Tube Selection Guide (Standard Indoor Roller Fabrics)

The calculator solves deflection dynamically, but for standard SBM fabrics (avg density ~250–600 g/m²), these are reliable practical thresholds:

| Shade Width | Typical Tube | Notes |
|---|---|---|
| Up to 48" (1.22m) | **1-1/8"** | Fine for most standard fabrics up to medium weight |
| 49" – 72" (1.25–1.83m) | **1-1/2"** | Upgrade to 2" for heavy blackout fabrics (>500 g/m²) |
| 73" – 96" (1.85–2.44m) | **2"** | Standard choice; 2-1/2" for heavy/wide |
| 97" – 120" (2.46–3.05m) | **2-1/2"** | Consider 3-1/4" for heavy fabrics or long drops |
| 121" – 144" (3.07–3.66m) | **2-1/2" or 3-1/4"** | Always verify with calculator for heavy fabric |
| > 144" (3.66m+) | **3-1/4"** | Maximum width in SBM catalog |

*Note: Drop (height) also affects tube selection — longer drops = heavier fabric roll = more torque required.*

---

## Motor Selection (Automate / Rollease Acmeda — US)

Motors are selected by **required torque** to lift and hold the shade. The calculator computes exact torque; the table below gives practical rules.

### Automate Motor Reference — Torque Ratings

| Description | Torque (Nm) | RPM | Compatible Tubes |
|---|---|---|---|
| Automate 0.7 Nm | 0.7 | 20 | 1", 1-1/8", 1-1/4", 1-1/2", 1-1/2" Switch |
| Automate 1.1 Nm | 1.1 | 20 | 1-1/4", 1-1/2", 1-1/2" Switch |
| Automate 2 Nm | 2.0 | 20 | 1-1/2", 1-1/2" Switch, 2" |
| Automate 3 Nm | 3.0 | 28 | 2", 2-1/2" |
| **Automate 6 Nm** | **6.0** | **28** | **2", 2-1/2"** ← most common for standard residential |
| Automate 10 Nm | 10.0 | 9 | 2-1/2", 3-1/4" |
| Automate 15 Nm | 15.0 | 15 | 2-1/2", 3-1/4" |
| Automate 30 Nm | 30.0 | 15 | Large/commercial |
| Automate 50 Nm | 50.0 | 12 | Large/commercial |

### Practical Motor Selection Guide

Motor torque required ≈ `(fabric_density_kg_m2 × width_m × drop_m × 9.81) / tube_radius_m × 1.5 safety factor`

For standard SBM fabrics (Sanctuary BO ~305 g/m², Kleenscreen ~160 g/m², Balmoral BO ~410 g/m²):

| Shade Size | Light Fabric (<200 g/m²) | Standard Fabric (200–400 g/m²) | Heavy Fabric (>400 g/m²) |
|---|---|---|---|
| Up to 48"W × 84"H | 0.7 Nm | **1.1 Nm** | 2 Nm |
| 49"–72"W × 84"H | 1.1 Nm | **2 Nm** | 3 Nm |
| 49"–72"W × 96"–120"H | 2 Nm | **3 Nm** | 6 Nm |
| 73"–96"W × up to 120"H | 3 Nm | **6 Nm** | 6–10 Nm |
| 97"–144"W × any height | 6 Nm | **10 Nm** | 15 Nm |
| >144"W or very long drops | 10–15 Nm | **15–30 Nm** | 30–50 Nm |

**For Rolli Home standard quote defaults (residential motorized):**
- Standard bedroom window (48"W × 84"H, Sanctuary/Balmoral BO): **Automate 6 Nm, 2" tube**
- Small window (<48"W × 72"H, light fabric): **Automate 1.1 Nm, 1-1/2" tube**
- Large window (>96"W, any height): **Automate 10 Nm, 2-1/2" tube**
- Always verify with the eBOM calculator for non-standard dimensions or very heavy fabrics.

---

## Manual Control Selection (Non-Motorized)

| Control | Max Holding Capacity | Tube Compatibility | Notes |
|---|---|---|---|
| G200 (Skyline clutch) | 2.04 Nm / ~0.46 kg | 1-1/2", 1-1/2" Switch, 2", 2-1/2" | Standard Skyline manual |
| G400 (Skyline clutch) | 4.5 Nm / ~1.02 kg | 1-1/2", 1-1/2" Switch, 2", 2-1/2", 3-1/4" | Heavy duty Skyline |
| SL10 | 0.71 Nm | 1", 1-1/8" | Small shades only |
| SL15 | 1.06 Nm | 1-1/8", 1-1/4", 1-1/2", 1-1/2" Switch | Light/medium |
| SL20 | 1.69 Nm | 1-1/2", 1-1/2" Switch, 2", 2-1/2" | Standard |
| SL30 | 2.54 Nm | 1-1/2", 1-1/2" Switch, 2", 2-1/2", 3-1/4" | Heavy duty |
| R16 | 1.36 Nm | 1-1/2", 1-1/2" Switch, 2", 2-1/2" | R-Series |
| R24 (has spring assist) | 2.04 Nm | 1-1/2", 1-1/2" Switch, 2", 2-1/2" | R-Series |

---

## Top Hardware / Bracket Selection

| Top Hardware | Notes |
|---|---|
| Skyline Bracket 32mm (SLxx650xx) | Standard 1-1/4" Skyline tube bracket |
| Skyline Bracket 38mm (SLxx660xx) | 1-1/2" tube |
| Skyline Bracket 50mm (SLxx680xx) | 2" tube |
| Skyline Bracket 73mm (SLxx690xx) | 2-1/2" tube |
| Cassette 80 / 100 / 120 | Enclosed cassette system; limits max roll diameter |
| 3" Fascia | Visible decorative fascia, standard |
| 4" Fascia | Wider decorative fascia |
| 5" Fascia - Single Roll | Single shade with 5" fascia |

Bracket selection must accommodate the **final roll diameter** (fabric + tube OD at full drop).
Larger drops = more fabric wraps = larger roll = may require larger bracket.

---

## Weight Bar / Bottom Rail Selection

| Bottom Rail | Mass/m | Notes |
|---|---|---|
| Internal Hem Bar | 186 g/m | Lightest; standard indoor shades |
| External Hem Bar | 250 g/m | Slightly heavier |
| Fabric Wrap Hem Bar | 235 g/m | Fabric-covered finish |
| D30 Medium Bottom Rail | 306 g/m | Standard upgraded rail |
| F4115 Heavy Duty | 540 g/m | Wide/heavy shades |
| F56 HD Weight Bar | 1,295 g/m | Extra heavy duty |
| F72 HD Weight Bar | 2,012 g/m | Maximum heavy duty |

**Rule:** For Easy Spring Air (manual spring assist), if weight bar is <500 g/m, the calculator automatically adds a ballast weight.

---

## Simplified Decision Tree for Rolli Home Quoting

```
INPUT: Width, Height, Fabric
  │
  ├─ Is it motorized?
  │    YES → Select motor by torque (see table above)
  │           → Motor determines compatible tube sizes
  │           → Select smallest compatible tube within deflection limit
  │    NO  → Select manual control (G200/SL20 for standard)
  │           → Select smallest adequate tube
  │
  ├─ Does width exceed 144"?
  │    YES → Must use 1-1/8" or larger tube (1" max = 144")
  │
  ├─ Is fabric heavy (>400 g/m²)? [Balmoral BO, Linen BO, F4115 class]
  │    YES → Upsize tube one grade; upsize motor one grade
  │
  └─ Select bracket/top hardware to fit tube OD + roll diameter
```

---

## SBM Fabric Weight Reference (for motor selection)

| Fabric Category | Approx Density | Weight Class |
|---|---|---|
| Solar / Openness fabrics (Kleenscreen, Serene) | ~160–250 g/m² | **Light** |
| Standard blackout (Sanctuary BO, Tusk BO, Mesa BO) | ~250–350 g/m² | **Standard** |
| Heavy blackout (Balmoral BO, Jersey BO) | ~350–450 g/m² | **Heavy** |
| Premium heavy (Linen BO, Silverscreen) | ~450–600 g/m² | **Heavy** |

*Source: Rollease Acmeda fabric list + manufacturer spec sheets. Exact densities vary by color.*

---

## What Still Requires the eBOM Calculator

The selection rules above cover the majority of standard residential installations. Use the full eBOM calculator for:
- Non-standard fabric densities (custom fabrics)
- Linked shade systems (multiple shades on one motor)
- Shades with unusually long drops (>120")
- Zipscreen / exterior roller systems
- Any installation where tube deflection is borderline per the table above

---

*Document generated March 8, 2026 | Source: shade-fabrication-calculator.xltm (Rollease Acmeda eBOM v1.26)*
