"""
SBM Pricer — Phase 1A Lookup Engine
Vendor: Shades by Matiss (SBM)
Catalog: 2023 (effective July 1, 2023)
Formula: dealer_cost = MSRP × 0.36  (64% off MSRP — verified from live PIC orders)

Usage:
    from sbm_pricer import SBMPricer
    p = SBMPricer()
    result = p.quote(fabric='Serene', width=48, height=84, motor='automate')
"""

import json
import os
import bisect

# Resolve path relative to this file
_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sbm_pricing_complete.json')

# ── Width breaks: 17 columns (37"–192") ─────────────────────────────────────
WIDTH_BREAKS  = [37, 46, 55, 64, 72, 78, 83, 96, 103, 109, 120, 132, 144, 156, 168, 180, 192]
# ── Height breaks: 15 rows (48"–216") ───────────────────────────────────────
HEIGHT_BREAKS = [48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168, 180, 192, 204, 216]

# ── Discount factor (64% off MSRP, verified from live PIC orders) ────────────
DEALER_FACTOR = 0.36


def _find_break_index(value, breaks):
    """
    Return the index of the break that covers `value`.
    Rules (matching SBM catalog):
      - Use the first break >= value  (ceiling lookup)
      - Values above the largest break use the largest break
    """
    idx = bisect.bisect_left(breaks, value)
    return min(idx, len(breaks) - 1)


class SBMPricer:
    def __init__(self, data_path: str = _DATA_PATH):
        with open(data_path) as f:
            self._data = json.load(f)

        # Build fast fabric → chart lookup
        self._fabric_chart: dict[str, str] = {}
        for chart_name, chart in self._data['price_charts'].items():
            for fabric in chart['fabrics']:
                self._fabric_chart[fabric.lower()] = chart_name

    # ── Core lookup ──────────────────────────────────────────────────────────

    def fabric_chart(self, fabric: str) -> str | None:
        """Return the chart name for a fabric, or None if not found."""
        return self._fabric_chart.get(fabric.lower())

    def base_dealer_cost(self, fabric: str, width_in: float, height_in: float) -> float:
        """
        Return the dealer cost (MSRP × 0.36) for a shade.
        Width and height are looked up using ceiling rounding to the nearest break.

        Args:
            fabric:     Fabric name (case-insensitive). Must match catalog exactly.
            width_in:   Finished width in inches.
            height_in:  Finished height in inches.

        Returns:
            Dealer cost as float (USD).

        Raises:
            ValueError if fabric is not found in catalog.
        """
        chart_name = self.fabric_chart(fabric)
        if not chart_name:
            raise ValueError(
                f"Fabric '{fabric}' not found. "
                f"Call list_fabrics() to see all options."
            )

        chart = self._data['price_charts'][chart_name]
        w_idx = _find_break_index(width_in, WIDTH_BREAKS)
        h_idx = _find_break_index(height_in, HEIGHT_BREAKS)
        msrp = chart['msrp_grid'][h_idx][w_idx]
        return round(msrp * DEALER_FACTOR, 2)

    def base_msrp(self, fabric: str, width_in: float, height_in: float) -> float:
        """Return MSRP (retail list price) for a shade."""
        chart_name = self.fabric_chart(fabric)
        if not chart_name:
            raise ValueError(f"Fabric '{fabric}' not found.")
        chart = self._data['price_charts'][chart_name]
        w_idx = _find_break_index(width_in, WIDTH_BREAKS)
        h_idx = _find_break_index(height_in, HEIGHT_BREAKS)
        return float(chart['msrp_grid'][h_idx][w_idx])

    # ── Surcharges ────────────────────────────────────────────────────────────

    def top_treatment_dealer_cost(self, treatment_key: str, width_in: float) -> float:
        """
        Return dealer cost for a top treatment.

        treatment_key options:
            3in_fascia_skyline, 4in_fascia_skyline, 5in_fascia_skyline,
            3in_4in_fabric_wrapped_fascia, dust_cover_valance_fabric_insert,
            skyline_cassette_80_100_120, 3in_pocket_bottom_closure,
            4in_pocket_bottom_closure, 5in_pocket_bottom_closure,
            6in_pocket_bottom_closure, l_i_clip_recess_closure,
            scalloped_bottom, open_bottom, fabric_insert
        """
        tt = self._data.get('top_treatment_surcharges', {})
        items = tt.get('items', {})
        if treatment_key not in items:
            raise ValueError(f"Treatment '{treatment_key}' not found. Keys: {list(items.keys())}")
        tt_width_breaks = tt['width_breaks']
        msrp_list = items[treatment_key]['msrp']
        idx = _find_break_index(width_in, tt_width_breaks)
        return round(msrp_list[idx] * DEALER_FACTOR, 2)

    def unit_surcharge_dealer_cost(self, surcharge_key: str) -> float:
        """Return dealer cost for a flat unit surcharge."""
        us = self._data.get('unit_surcharges', {})
        if surcharge_key not in us:
            raise ValueError(f"Surcharge '{surcharge_key}' not found. Keys: {list(us.keys())}")
        val = us[surcharge_key]
        if isinstance(val, (int, float)):
            return round(float(val) * DEALER_FACTOR, 2)
        raise ValueError(f"Surcharge '{surcharge_key}' has unexpected format: {val}")

    def motorization_dealer_cost(self, brand: str, category: str, motor_key: str) -> float:
        """
        Return dealer cost for motorization.

        brand:    'automate', 'somfy', or 'gaposa'
        category: e.g. 'hardwired_110v', 'radio_110v', 'battery_integrated', 'low_voltage_12v'
        motor_key: e.g. '35mm_quiet_6nm', 'sonesse_40_rts', etc.

        Call list_motors(brand) to see all options.
        """
        brand_map = {
            'automate': 'motorization_automate_rollease',
            'automate_rollease': 'motorization_automate_rollease',
            'somfy': 'motorization_somfy',
            'gaposa': 'motorization_gaposa',
        }
        key = brand_map.get(brand.lower())
        if not key:
            raise ValueError(f"Brand '{brand}' not found. Options: automate, somfy, gaposa")
        motor_data = self._data.get(key, {})
        if category not in motor_data:
            raise ValueError(f"Category '{category}' not found in {brand}. Keys: {[k for k in motor_data if k != 'note']}")
        cat = motor_data[category]
        if motor_key not in cat:
            raise ValueError(f"Motor '{motor_key}' not found. Keys: {list(cat.keys())}")
        return round(float(cat[motor_key]) * DEALER_FACTOR, 2)

    def list_motors(self, brand: str) -> dict:
        """Return all motors for a brand, grouped by category."""
        brand_map = {
            'automate': 'motorization_automate_rollease',
            'somfy': 'motorization_somfy',
            'gaposa': 'motorization_gaposa',
        }
        key = brand_map.get(brand.lower())
        if not key:
            raise ValueError(f"Brand '{brand}' not found.")
        data = self._data.get(key, {})
        return {k: v for k, v in data.items() if k != 'note'}

    # ── Full quote ────────────────────────────────────────────────────────────

    def quote(
        self,
        fabric: str,
        width_in: float,
        height_in: float,
        top_treatment: str = None,
        motor_brand: str = None,
        motor_category: str = None,
        motor_key: str = None,
        extra_surcharges: list[str] = None,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Compute a full quote for one SBM shade.

        Args:
            fabric:           Fabric name (case-insensitive)
            width_in:         Finished width in inches
            height_in:        Finished height in inches
            top_treatment:    Optional top treatment key (see top_treatment_dealer_cost)
            motor_brand:      Optional: 'automate', 'somfy', or 'gaposa'
            motor_key:        Required if motor_brand is set
            extra_surcharges: List of unit surcharge keys to add
            target_margin:    Gross margin for sell price calc (default 40%)

        Returns:
            Dict with dealer_cost, sell_price, msrp, and line-item breakdown.
        """
        line_items = []

        # Base shade
        base_dealer = self.base_dealer_cost(fabric, width_in, height_in)
        base_msrp   = self.base_msrp(fabric, width_in, height_in)
        chart_name  = self.fabric_chart(fabric)
        line_items.append({
            'description': f'Base shade ({fabric}, {width_in}"W x {height_in}"H, {chart_name})',
            'dealer_cost': base_dealer,
            'msrp':        base_msrp,
        })

        # Top treatment
        if top_treatment:
            tt_cost = self.top_treatment_dealer_cost(top_treatment, width_in)
            line_items.append({
                'description': f'Top treatment: {top_treatment}',
                'dealer_cost': tt_cost,
                'msrp':        round(tt_cost / DEALER_FACTOR, 2),
            })

        # Motorization
        if motor_brand and motor_category and motor_key:
            m_cost = self.motorization_dealer_cost(motor_brand, motor_category, motor_key)
            line_items.append({
                'description': f'Motor: {motor_brand} {motor_key}',
                'dealer_cost': m_cost,
                'msrp':        round(m_cost / DEALER_FACTOR, 2),
            })

        # Extra unit surcharges
        for sk in (extra_surcharges or []):
            s_cost = self.unit_surcharge_dealer_cost(sk)
            line_items.append({
                'description': f'Surcharge: {sk}',
                'dealer_cost': s_cost,
                'msrp':        round(s_cost / DEALER_FACTOR, 2),
            })

        total_dealer = round(sum(li['dealer_cost'] for li in line_items), 2)
        total_msrp   = round(sum(li['msrp'] for li in line_items), 2)
        sell_price   = round(total_dealer / (1 - target_margin), 2)
        gross_margin = round((sell_price - total_dealer) / sell_price * 100, 1)

        return {
            'fabric':       fabric,
            'chart':        chart_name,
            'width_in':     width_in,
            'height_in':    height_in,
            'line_items':   line_items,
            'dealer_cost':  total_dealer,
            'sell_price':   sell_price,
            'msrp':         total_msrp,
            'gross_margin': f'{gross_margin}%',
        }

    # ── Utility ───────────────────────────────────────────────────────────────

    def list_fabrics(self) -> dict[str, list[str]]:
        """Return all fabrics grouped by chart."""
        return {
            name: chart['fabrics']
            for name, chart in self._data['price_charts'].items()
        }

    def find_fabric(self, partial: str) -> list[str]:
        """Search for fabrics by partial name (case-insensitive)."""
        results = []
        for chart_name, chart in self._data['price_charts'].items():
            for fabric in chart['fabrics']:
                if partial.lower() in fabric.lower():
                    results.append(f'{fabric} [{chart_name}]')
        return results


# ── CLI demo ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    p = SBMPricer()

    print('=== SBM Pricer — Sample Quotes (64% discount / 0.36 factor) ===\n')

    test_cases = [
        {'fabric': 'Serene',       'width_in': 48,  'height_in': 84},
        {'fabric': 'Silverscreen', 'width_in': 72,  'height_in': 96},
        {'fabric': 'Kleenscreen',  'width_in': 37,  'height_in': 48},
        {'fabric': 'Linen BO',     'width_in': 120, 'height_in': 144},
        {'fabric': 'Serene', 'width_in': 48, 'height_in': 84,
         'top_treatment': '3in_fascia_skyline'},
    ]

    for tc in test_cases:
        try:
            result = p.quote(**tc, target_margin=0.40)
            print(f"{result['fabric']} {result['width_in']}\"W x {result['height_in']}\"H [{result['chart']}]")
            for li in result['line_items']:
                print(f"  {li['description']}: dealer=${li['dealer_cost']:.2f}  MSRP=${li['msrp']:.2f}")
            print(f"  TOTAL dealer=${result['dealer_cost']:.2f} | sell@40%=${result['sell_price']:.2f} | MSRP=${result['msrp']:.2f}")
            print()
        except ValueError as e:
            print(f'  ERROR: {e}\n')
