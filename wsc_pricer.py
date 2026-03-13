"""
wsc_pricer.py — Fabritec / Woven Shades Collection (WSC) Pricing Engine
Vendor: Fabritec LLC | Catalog: February 2026 | Discount: 50% off SRP

Usage:
    from wsc_pricer import WSCPricer
    p = WSCPricer()
    result = p.quote_roman(group=1, width_in=36, height_in=72)
    result = p.quote_roller(group=1, width_in=36, height_in=72)

Or run directly:
    python wsc_pricer.py
"""

import json
import bisect
import os
import sys

# ── Constants ─────────────────────────────────────────────────────────────────
DEALER_FACTOR = 0.50   # 50% off SRP — verified trade pricing from Fabritec

JSON_PATH = os.path.join(os.path.dirname(__file__), "wsc_pricing_complete.json")


class WSCPricer:
    def __init__(self, json_path: str = JSON_PATH):
        with open(json_path) as f:
            self._data = json.load(f)
        self._roman = self._data["roman_shades"]
        self._roller = self._data["roller_shades"]
        self._lining = self._data["lining_pricing"]

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _ceil_index(self, value: float, breaks: list) -> int:
        """Return the index of the smallest break >= value (ceiling lookup)."""
        idx = bisect.bisect_left(breaks, value)
        if idx >= len(breaks):
            idx = len(breaks) - 1
        return idx

    def _roman_lookup(self, group: int, width_in: float, height_in: float) -> dict:
        """Return base price info for a roman shade."""
        grp = self._roman["price_groups"][f"group_{group}"]
        w_breaks = grp["width_breaks_in"]
        h_breaks = grp["height_breaks_in"]
        wi = self._ceil_index(width_in, w_breaks)
        hi = self._ceil_index(height_in, h_breaks)
        msrp = grp["msrp_grid"][hi][wi]
        dealer = grp["dealer_cost_grid"][hi][wi]
        return {
            "msrp": msrp,
            "dealer_cost": dealer,
            "billed_width": w_breaks[wi],
            "billed_height": h_breaks[hi],
        }

    def _roller_lookup(self, group: int, width_in: float, height_in: float) -> dict:
        """Return base price info for a roller shade."""
        grp = self._roller["price_groups"][f"group_{group}"]
        if not grp["width_breaks_in"]:
            raise ValueError(f"Roller group {group} has no fabrics currently.")
        w_breaks = grp["width_breaks_in"]
        h_breaks = grp["height_breaks_in"]

        max_w = max(w_breaks)
        max_h = max(h_breaks)
        if width_in > max_w:
            raise ValueError(f"Width {width_in}\" exceeds max {max_w}\" for roller group {group}.")
        if height_in > max_h:
            raise ValueError(f"Height {height_in}\" exceeds max {max_h}\" for roller group {group}.")

        wi = self._ceil_index(width_in, w_breaks)
        hi = self._ceil_index(height_in, h_breaks)
        msrp = grp["msrp_grid"][hi][wi]
        dealer = grp["dealer_cost_grid"][hi][wi]
        return {
            "msrp": msrp,
            "dealer_cost": dealer,
            "billed_width": w_breaks[wi],
            "billed_height": h_breaks[hi],
        }

    def _lining_lookup(self, lining_type: str, width_in: float, height_in: float) -> dict:
        """Return lining add-on price."""
        w_breaks = self._lining["width_breaks_in"]
        h_breaks = self._lining["height_breaks_in"]
        wi = self._ceil_index(width_in, w_breaks)
        hi = self._ceil_index(height_in, h_breaks)

        if lining_type == "privacy_satinsheen":
            msrp = self._lining["privacy_satinsheen"]["msrp_grid"][hi][wi]
            dealer = self._lining["privacy_satinsheen"]["dealer_cost_grid"][hi][wi]
        elif lining_type in ("blackout", "jute", "nightfall", "serenity", "apollo"):
            msrp = self._lining["blackout_and_regular_jute"]["msrp_grid"][hi][wi]
            dealer = self._lining["blackout_and_regular_jute"]["dealer_cost_grid"][hi][wi]
        else:
            raise ValueError(f"Unknown lining type: {lining_type!r}. "
                             f"Options: privacy_satinsheen, blackout, jute, nightfall, serenity, apollo")
        return {
            "msrp": msrp,
            "dealer_cost": dealer,
            "billed_width": w_breaks[wi],
            "billed_height": h_breaks[hi],
        }

    # ── Surcharge Lookups ──────────────────────────────────────────────────────

    def lifting_system_surcharge(self, system: str) -> dict:
        """Return SRP and dealer cost for a non-standard lifting system."""
        ls = self._data["lifting_system_surcharges"]
        key_map = {
            "cordless": "cordless",
            "cco": "continuous_chain_operator_cco",
            "continuous_chain": "continuous_chain_operator_cco",
            "slide_winder": "slide_winder_operator",
            "bottom_up": "bottom_up_roller",
        }
        key = key_map.get(system.lower().replace("-", "_").replace(" ", "_"))
        if not key or key not in ls:
            raise ValueError(f"Unknown lifting system: {system!r}. Options: {list(key_map.keys())}")
        entry = ls[key]
        return {"msrp": entry["price_usd"], "dealer_cost": entry["dealer_cost_usd"],
                "note": entry.get("note", "")}

    def motor_price(self, brand: str, motor_key: str, segment: str = "roman") -> dict:
        """
        Return SRP and dealer cost for a motor.
        brand: 'rollease' | 'somfy'
        segment: 'roman' | 'roller'
        motor_key examples: '1_1nm_battery', 'r28_battery_rts', 'sonesse400_rts'
        """
        brand = brand.lower()
        seg_key = f"{'roman_shades' if segment == 'roman' else 'roller_shades'}_pricing"
        if brand == "rollease":
            catalog = self._data["motorization_rollease"][seg_key]
        elif brand == "somfy":
            catalog = self._data["motorization_somfy"][seg_key]
        else:
            raise ValueError(f"Unknown motor brand: {brand!r}. Options: rollease, somfy")

        if motor_key not in catalog:
            available = list(catalog.keys())
            raise ValueError(f"Motor key {motor_key!r} not found. Available: {available}")

        entry = catalog[motor_key]
        return {
            "motor_key": motor_key,
            "brand": brand,
            "msrp": entry["price_usd"],
            "dealer_cost": entry["dealer_cost_usd"],
            "torque_nm": entry.get("torque_nm"),
            "note": entry.get("note", ""),
        }

    def remote_price(self, brand: str, remote_key: str) -> dict:
        """Return remote controller pricing."""
        brand = brand.lower()
        if brand == "rollease":
            catalog = self._data["motorization_rollease"]["accessories"]
        elif brand == "somfy":
            catalog = self._data["motorization_somfy"]["remote_controllers"]
        else:
            raise ValueError(f"Unknown brand: {brand!r}")
        if remote_key not in catalog:
            raise ValueError(f"Remote key {remote_key!r} not in catalog. Available: {list(catalog.keys())}")
        entry = catalog[remote_key]
        return {"msrp": entry["price_usd"], "dealer_cost": entry["dealer_cost_usd"]}

    # ── Quote Builders ─────────────────────────────────────────────────────────

    def quote_roman(
        self,
        group: int,
        width_in: float,
        height_in: float,
        style: str = "101-Pacifica",
        lining: str = None,          # None | 'privacy_satinsheen' | 'blackout' | 'jute'
        lifting_system: str = None,   # None | 'cordless' | 'cco' | 'slide_winder'
        top_down: bool = False,       # True = add TD valance surcharge
        cords_forward: bool = False,  # True = add CF valance surcharge
        valance_height_in: int = 6,   # 6 | 12 | 18 (for TD or CF)
        motor_brand: str = None,
        motor_key: str = None,
        remote_brand: str = None,
        remote_key: str = None,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Build a full roman shade quote.
        Returns dealer cost, suggested retail, and line item breakdown.
        """
        line_items = []
        total_dealer = 0.0
        total_msrp = 0.0

        # Base shade
        base = self._roman_lookup(group, width_in, height_in)
        line_items.append({
            "item": f"Roman Shade — Group {group} ({style}), "
                    f"{base['billed_width']}\"W × {base['billed_height']}\"H",
            "msrp": base["msrp"],
            "dealer_cost": base["dealer_cost"],
        })
        total_dealer += base["dealer_cost"]
        total_msrp += base["msrp"]

        # Lining
        if lining:
            lin = self._lining_lookup(lining, width_in, height_in)
            line_items.append({
                "item": f"Lining — {lining}",
                "msrp": lin["msrp"],
                "dealer_cost": lin["dealer_cost"],
            })
            total_dealer += lin["dealer_cost"]
            total_msrp += lin["msrp"]

        # Lifting system surcharge
        if lifting_system:
            ls = self.lifting_system_surcharge(lifting_system)
            line_items.append({
                "item": f"Lifting System — {lifting_system}",
                "msrp": ls["msrp"],
                "dealer_cost": ls["dealer_cost"],
            })
            total_dealer += ls["dealer_cost"]
            total_msrp += ls["msrp"]

        # Top-Down valance surcharge
        if top_down:
            grp_data = self._roman["price_groups"][f"group_{group}"]
            td = grp_data["top_down_valance_surcharge_msrp"]
            key = {6: "valance_6in", 12: "valance_12in", 18: "valance_18in"}.get(valance_height_in)
            if key and td.get(key):
                w_breaks = grp_data["width_breaks_in"]
                wi = self._ceil_index(width_in, w_breaks)
                surcharge_msrp = td[key][wi]
                surcharge_dealer = round(surcharge_msrp * DEALER_FACTOR, 2)
                line_items.append({
                    "item": f"Top-Down Valance ({valance_height_in}\"H) surcharge",
                    "msrp": surcharge_msrp,
                    "dealer_cost": surcharge_dealer,
                })
                total_dealer += surcharge_dealer
                total_msrp += surcharge_msrp

        # Cords-Forward valance surcharge
        if cords_forward:
            grp_data = self._roman["price_groups"][f"group_{group}"]
            cf = grp_data["cords_forward_valance_surcharge_msrp"]
            key = {6: "valance_6in", 12: "valance_12in", 18: "valance_18in"}.get(valance_height_in)
            if key and cf.get(key):
                w_breaks = grp_data["width_breaks_in"]
                wi = self._ceil_index(width_in, w_breaks)
                surcharge_msrp = cf[key][wi]
                surcharge_dealer = round(surcharge_msrp * DEALER_FACTOR, 2)
                line_items.append({
                    "item": f"Cords Forward Valance ({valance_height_in}\"H) surcharge",
                    "msrp": surcharge_msrp,
                    "dealer_cost": surcharge_dealer,
                })
                total_dealer += surcharge_dealer
                total_msrp += surcharge_msrp

        # Motor
        if motor_brand and motor_key:
            m = self.motor_price(motor_brand, motor_key, "roman")
            line_items.append({
                "item": f"Motor — {motor_brand} {motor_key}",
                "msrp": m["msrp"],
                "dealer_cost": m["dealer_cost"],
            })
            total_dealer += m["dealer_cost"]
            total_msrp += m["msrp"]

        # Remote
        if remote_brand and remote_key:
            r = self.remote_price(remote_brand, remote_key)
            line_items.append({
                "item": f"Remote — {remote_brand} {remote_key}",
                "msrp": r["msrp"],
                "dealer_cost": r["dealer_cost"],
            })
            total_dealer += r["dealer_cost"]
            total_msrp += r["msrp"]

        sell_price = round(total_dealer / (1 - target_margin), 2)
        gross_margin = round(1 - (total_dealer / sell_price), 4) if sell_price else 0

        return {
            "product_type": "roman_shade",
            "style": style,
            "group": group,
            "width_in": width_in,
            "height_in": height_in,
            "line_items": line_items,
            "dealer_cost": round(total_dealer, 2),
            "sell_price": sell_price,
            "msrp": round(total_msrp, 2),
            "gross_margin": gross_margin,
            "target_margin": target_margin,
        }

    def quote_roller(
        self,
        group: int,
        width_in: float,
        height_in: float,
        motor_brand: str = None,
        motor_key: str = None,
        remote_brand: str = None,
        remote_key: str = None,
        target_margin: float = 0.40,
    ) -> dict:
        """Build a full roller shade quote."""
        line_items = []
        total_dealer = 0.0
        total_msrp = 0.0

        base = self._roller_lookup(group, width_in, height_in)
        line_items.append({
            "item": f"Roller Shade — Group {group}, "
                    f"{base['billed_width']}\"W × {base['billed_height']}\"H (incl. SL Clutch)",
            "msrp": base["msrp"],
            "dealer_cost": base["dealer_cost"],
        })
        total_dealer += base["dealer_cost"]
        total_msrp += base["msrp"]

        if motor_brand and motor_key:
            m = self.motor_price(motor_brand, motor_key, "roller")
            line_items.append({
                "item": f"Motor — {motor_brand} {motor_key}",
                "msrp": m["msrp"],
                "dealer_cost": m["dealer_cost"],
            })
            total_dealer += m["dealer_cost"]
            total_msrp += m["msrp"]

        if remote_brand and remote_key:
            r = self.remote_price(remote_brand, remote_key)
            line_items.append({
                "item": f"Remote — {remote_brand} {remote_key}",
                "msrp": r["msrp"],
                "dealer_cost": r["dealer_cost"],
            })
            total_dealer += r["dealer_cost"]
            total_msrp += r["msrp"]

        sell_price = round(total_dealer / (1 - target_margin), 2)
        gross_margin = round(1 - (total_dealer / sell_price), 4) if sell_price else 0

        return {
            "product_type": "roller_shade",
            "group": group,
            "width_in": width_in,
            "height_in": height_in,
            "line_items": line_items,
            "dealer_cost": round(total_dealer, 2),
            "sell_price": sell_price,
            "msrp": round(total_msrp, 2),
            "gross_margin": gross_margin,
            "target_margin": target_margin,
        }

    # ── Utility ────────────────────────────────────────────────────────────────

    def list_groups(self, product: str = "roman") -> None:
        """Print all price groups and their fabric patterns."""
        src = self._roman if product == "roman" else self._roller
        print(f"\n{'ROMAN' if product == 'roman' else 'ROLLER'} SHADE PRICE GROUPS:")
        for key, grp in src["price_groups"].items():
            patterns = grp.get("patterns", [])
            note = grp.get("note", "")
            print(f"  {key}: {grp.get('fabric_width', '')} — {', '.join(patterns[:3])}"
                  f"{' ...' if len(patterns) > 3 else ''}"
                  f"{' [' + note + ']' if note else ''}")

    def list_motors(self, brand: str, segment: str = "roman") -> None:
        """Print all motor options for a brand."""
        seg_key = "roman_shades_pricing" if segment == "roman" else "roller_shades_pricing"
        brand = brand.lower()
        if brand == "rollease":
            catalog = self._data["motorization_rollease"][seg_key]
        elif brand == "somfy":
            catalog = self._data["motorization_somfy"][seg_key]
        else:
            raise ValueError(f"Unknown brand: {brand!r}")
        print(f"\n{brand.upper()} MOTORS ({segment}):")
        for k, v in catalog.items():
            print(f"  {k}: SRP=${v['price_usd']}, dealer=${v['dealer_cost_usd']}, "
                  f"torque={v.get('torque_nm')}Nm {v.get('note','')}")


# ── Quick demo ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = WSCPricer()

    # ── EDIT THIS BLOCK TO TEST ───────────────────────────────────────────────
    QUOTE_TYPE = "roman"          # "roman" or "roller"
    GROUP = 1                     # price group number (1–10)
    WIDTH = 48                    # width in inches
    HEIGHT = 72                   # height in inches
    STYLE = "101-Pacifica"        # "101-Pacifica" or "104-Laguna"
    LINING = None                 # None | "privacy_satinsheen" | "blackout"
    LIFTING = None                # None | "cordless" | "cco" | "slide_winder"
    TOP_DOWN = False              # True to add Top Down valance surcharge
    CORDS_FORWARD = False         # True to add Cords Forward valance surcharge
    VALANCE_HEIGHT = 6            # 6 | 12 | 18 (if TD or CF)
    MOTOR_BRAND = None            # None | "rollease" | "somfy"
    MOTOR_KEY = None              # e.g. "1_1nm_battery" | "r28_battery_rts"
    REMOTE_BRAND = None           # None | "rollease" | "somfy"
    REMOTE_KEY = None             # e.g. "single_channel_remote" | "five_channel_handheld"
    TARGET_MARGIN = 0.40          # gross margin target (40% default)
    # ─────────────────────────────────────────────────────────────────────────

    if QUOTE_TYPE == "roman":
        result = p.quote_roman(
            group=GROUP, width_in=WIDTH, height_in=HEIGHT,
            style=STYLE, lining=LINING, lifting_system=LIFTING,
            top_down=TOP_DOWN, cords_forward=CORDS_FORWARD,
            valance_height_in=VALANCE_HEIGHT,
            motor_brand=MOTOR_BRAND, motor_key=MOTOR_KEY,
            remote_brand=REMOTE_BRAND, remote_key=REMOTE_KEY,
            target_margin=TARGET_MARGIN,
        )
    else:
        result = p.quote_roller(
            group=GROUP, width_in=WIDTH, height_in=HEIGHT,
            motor_brand=MOTOR_BRAND, motor_key=MOTOR_KEY,
            remote_brand=REMOTE_BRAND, remote_key=REMOTE_KEY,
            target_margin=TARGET_MARGIN,
        )

    # Print results
    print(f"\n{'=' * 58}")
    print(f"  WSC QUOTE — {result['product_type'].upper().replace('_',' ')}")
    print(f"  Group {result['group']} | {WIDTH}\"W × {HEIGHT}\"H")
    print(f"{'=' * 58}")
    for item in result["line_items"]:
        print(f"  {item['item']}")
        print(f"    We pay Fabritec:  ${item['dealer_cost']:>8.2f}   "
              f"SRP: ${item['msrp']:>8.2f}")
    print(f"  {'─' * 54}")
    print(f"  TOTAL WE PAY FABRITEC:    ${result['dealer_cost']:>8.2f}")
    print(f"  SUGGESTED RETAIL @{int(TARGET_MARGIN*100)}%:    ${result['sell_price']:>8.2f}")
    print(f"  Fabritec SRP (list):      ${result['msrp']:>8.2f}")
    print(f"{'=' * 58}\n")
