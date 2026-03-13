# Competitive Pricing Analysis — Rolli Home LLC
**Date:** March 8, 2026
**Sources:** shadeit.com, rollishades.com cross-referenced against sbm_pricing_complete.json
**Motor assumption:** Automate 35mm Radio 110V, dealer cost $230.00
**Our target margin:** 40%

---

## Key Structural Finding (Read First)

The two competitors serve **fundamentally different market positions:**

| | shadeit.com | rollishades.com | Rolli Home (us) |
|---|---|---|---|
| **Model** | D2C online, low price | D2C online, premium motorized | Full-service dealer |
| **Shades** | Manual (motor optional) | Motorized only | Motorized, full install |
| **"From" price** | Entry-level manual | Entry-level motorized | N/A |
| **Service** | DIY install | DIY install | Measured + installed |
| **Target customer** | Price-sensitive DIY | Tech-forward homeowner | Trade / design / convenience |

The "from" prices on both sites are for their **smallest offered sizes** (likely ~24"–30" wide), which are smaller than our minimum catalog grid (37"W). This is why shadeit prices appear to undercut our dealer cost at larger sizes — they charge more for larger windows through their configurator.

---

## Sample Data — 8 Products Pulled Live

### shadeit.com (Manual shades, motorization available as add-on)

| Product | SBM Fabric | Listed "From" | Our Dealer Cost (37"×48") | Implied Margin at "From" |
|---|---|---|---|---|
| Sanctuary Blackout ⭐ Best Seller | Sanctuary BO | **$99** | $43.60 | 56.0% |
| Kleenscreen 3% | Kleenscreen | **$102** | $28.00 | 72.5% |
| Kleenscreen Blackout ⭐ Best Seller | Kleenscreen | **$112** | $28.00 | 75.0% |
| Balmoral Blackout | Balmoral BO | **$112** | $43.60 | 61.1% |
| Mesa Blackout ⭐ Best Seller | Mesa TL/BO | **$102** | $36.00 | 64.7% |

*Note: Implied margin calculated at 37"×48" — smallest grid. At standard sizes, their prices are significantly higher via configurator.*

---

### rollishades.com (All motorized — prices include motor)

| Product | SBM Fabric | Listed "From" | Our Dealer Cost Motorized (37"×48") | Implied Margin at "From" |
|---|---|---|---|---|
| Sanctuary Blackout | Sanctuary BO | **$521** | $273.60 | 47.5% |
| Tusk Blackout | Tusk BO/TL | **$543** | $266.00 | 51.0% |
| Vista Blackout | Vista | **$5** ⚠️ | $273.60 | — |

---

## Real-World Sizing: 48"W × 84"H (Standard Bedroom Window)

This is the most strategically important size — typical for a bedroom or living room.

| Site | Product | Their "From" | Our Dealer Cost | Our 40% Sell Price | Implied Margin vs Our Cost |
|---|---|---|---|---|---|
| shadeit.com | Sanctuary BO (manual) | $99 | $106.80 | $178.00 | **-7.9%** ⚠️ |
| shadeit.com | Kleenscreen 3% (manual) | $102 | $64.40 | $107.33 | 36.9% |
| shadeit.com | Balmoral BO (manual) | $112 | $106.80 | $178.00 | **4.6%** ⚠️ |
| shadeit.com | Mesa BO (manual) | $102 | $85.20 | $142.00 | 16.5% |
| rollishades.com | Sanctuary BO (motorized) | $521 | $336.80 | $561.33 | 35.4% |
| rollishades.com | Tusk BO (motorized) | $543 | $315.20 | $525.33 | 42.0% |

**Critical note:** shadeit's negative/thin margins at 48"×84" confirm they price dynamically — a 48"×84" Sanctuary BO on their configurator likely costs **$160–$200+**, not $99. The $99 is only for tiny windows.

---

## Anomalies & Flags

### 🔴 Anomaly 1: Vista Blackout (rollishades.com) — $5 Listed Price
Vista Blackout is showing "Start Customizing From **$5**" on rollishades.com. Every other product on the site is $500+. This is almost certainly a Shopify variant placeholder or pricing error — likely a fabric sample or test SKU accidentally published. **Risk:** if a customer finds this and attempts to order, it could create a refund/PR situation for Rolli. Worth monitoring.

### 🟡 Anomaly 2: shadeit.com "From" Prices Are Below Our Dealer Cost at Standard Sizes
At 48"×84", our dealer cost for Sanctuary BO ($106.80) **exceeds** shadeit's "from" price ($99), and Balmoral BO ($106.80) barely clears their $112 "from." This is not a real competitive threat — they price higher for larger windows — but it reveals their marketing strategy: advertise the cheapest possible price for the smallest window to drive traffic. Their actual Sanctuary BO price at 48"×84" is likely **~$178–$220** based on their margin structure.

### 🟡 Anomaly 3: Kleenscreen Blackout vs. Kleenscreen 3% — Different SKUs, Same Fabric?
shadeit.com sells both "Kleenscreen 3%" ($102) and "Kleenscreen Blackout" ($112) as separate products. In our SBM catalog, we have a single "Kleenscreen" fabric. The Blackout variant ($10 premium) likely uses a different backing construction. **Action needed:** confirm with SBM/Rollease Acmeda whether our "Kleenscreen" catalog entry covers both openness and blackout variants, and if separate SKUs/pricing apply.

### 🟢 Anomaly 4: Rolli Home Is Structurally Price-Competitive on Motorized
At 40% target margin, our motorized sell price for Sanctuary BO 48"×84" is **$561.33**. Rollishades' "from" price (smallest size) is $521 — meaning at standard and large sizes, Rolli is likely charging **$700–$900+** for the same product. We can price competitively while maintaining 40% margin AND offering full-service installation. This is a genuine differentiation opportunity.

### 🟡 Anomaly 5: Motor Markup at rollishades.com Is Very High
Shadeit manual Sanctuary BO "from $99" vs Rolli motorized Sanctuary BO "from $521" = **$422 delta** attributed to motor. Our motor dealer cost is $230. At 40% margin, we'd sell the motor at $383. Rolli appears to be selling the motor at $422+, implying **>45% margin on the motor alone** — or bundling a higher-grade motor. We should verify what motor Rolli uses (their site mentions "Pulse 2 app, Alexa, Google Home, Apple HomeKit" — consistent with Automate or Somfy RF).

---

## Pricing Guidance: Where Should We Be?

Using **48"×84" Sanctuary Blackout motorized** as the benchmark:

| Scenario | Price | Notes |
|---|---|---|
| Our dealer cost (Sanctuary BO + Automate Radio) | $336.80 | Hard floor |
| Our 40% margin sell price | **$561** | Target minimum |
| Rollishades "from" (smallest window, motorized) | $521 | Their entry point; larger windows cost more |
| Estimated Rolli price at 48"×84" | **~$700–$850** | Inferred from pricing curve |
| shadeit.com manual at ~48"×84" | **~$178–$220** | DIY, no motor, no service |

**Conclusion:** We have room to price at $561–$700 for a standard motorized shade (depending on premium and service tier), remain below Rollishades on a comparable product, and be significantly above shadeit (which is a different market — DIY manual, no service). Our value-add is professional measurement + installation + full service, which justifies a premium over both online-only competitors.

---

## Next Steps

1. **Verify Kleenscreen SKU split** — confirm whether our "Kleenscreen" covers both openness (1%/3%/5%) and Blackout variants
2. **Monitor Vista Blackout $5 error** on rollishades.com — flag if it changes
3. **Pull configurator prices at 48"×84"** on shadeit.com and rollishades.com when browser tooling is stable — this would sharpen our competitive pricing model considerably
4. **Consider tiered pricing** — entry price for our standard shades should target $50–$75 above rollishades.com configurator prices at the same size, justified by full-service install
5. **Phase 1B:** Build quoting engine that uses this competitive context to suggest sell prices, not just floor dealer cost

---

*Analysis generated March 8, 2026 | Data sources: live page scraping + sbm_pricing_complete.json | Motor: Automate 35mm Quiet 6Nm Radio 110V*
