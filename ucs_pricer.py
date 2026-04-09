"""
ucs_pricer.py — US Custom Shades (USCS) Pricer
Vendor: US Custom Shades (Coulisse fabricator)
Catalog: 2026 Retail Handbook
Formula: dealer_cost = retail_price × 0.55 (45% off retail — Liam Dobson / Brian)
PIC Account: 7653.picbusiness.com

Usage:
    from ucs_pricer import UCSPricer
    p = UCSPricer()
    result = p.quote(chart='light_filtering_chart_1', width_in=48, height_in=84)
    # or by fabric name:
    result = p.quote_by_fabric('Munich Light Filtering', width_in=48, height_in=84)
"""

import json
import os
import bisect

_DATA_PATH = os.path.join(os.path.dirname(__file__), 'uscs_pricing_complete.json')

DEALER_FACTOR = 0.55   # 45% off retail


def _find_break_index(value: float, breaks: list) -> int:
    """Ceiling lookup: return index of first break >= value."""
    idx = bisect.bisect_left(breaks, value)
    return min(idx, len(breaks) - 1)


class UCSPricer:
    """
    Prices US Custom Shades roller shades from 19 pricing charts.
    dealer_cost = retail × 0.55
    """

    def __init__(self, data_path: str = _DATA_PATH):
        with open(data_path) as f:
            self._data = json.load(f)

        self._width_breaks  = self._data['width_breaks']
        self._height_breaks = self._data['height_breaks']
        self._charts        = self._data['price_charts']

        # Build fabric → chart key lookup (case-insensitive)
        self._fabric_chart: dict[str, str] = {}
        for ckey, cdata in self._charts.items():
            for fabric in cdata.get('fabrics', []):
                self._fabric_chart[fabric.lower()] = ckey

    # ── Core lookups ─────────────────────────────────────────────────────────

    def chart_for_fabric(self, fabric: str) -> str | None:
        """Return the chart key for a fabric name, or None."""
        return self._fabric_chart.get(fabric.lower())

    def retail_price(self, chart: str, width_in: float, height_in: float) -> float:
        """Return retail (SRP) price for a shade."""
        c = self._charts.get(chart)
        if not c:
            raise ValueError(
                f"Chart '{chart}' not found. "
                f"Available: {list(self._charts.keys())}"
            )
        grid = c['retail_grid']
        w_idx = _find_break_index(width_in,  self._width_breaks)
        h_idx = _find_break_index(height_in, self._height_breaks)
        w_idx = min(w_idx, len(grid[0]) - 1)
        h_idx = min(h_idx, len(grid) - 1)
        return float(grid[h_idx][w_idx])

    def dealer_cost(self, chart: str, width_in: float, height_in: float) -> float:
        """Return dealer cost (retail × 0.55)."""
        return round(self.retail_price(chart, width_in, height_in) * DEALER_FACTOR, 2)

    # ── Full quote ────────────────────────────────────────────────────────────

    def quote(
        self,
        chart: str,
        width_in: float,
        height_in: float,
        fabric: str | None = None,
        color: str | None = None,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Compute a full quote for one USCS roller shade.

        Args:
            chart:          Chart key (e.g. 'light_filtering_chart_1')
            width_in:       Finished width in inches
            height_in:      Finished drop in inches
            fabric:         Optional fabric name (for description)
            color:          Optional color name
            target_margin:  Gross margin for sell price (default 40%)
        """
        srp          = self.retail_price(chart, width_in, height_in)
        dealer       = round(srp * DEALER_FACTOR, 2)
        sell_price   = round(dealer / (1 - target_margin), 2)
        gross_margin = round((sell_price - dealer) / sell_price * 100, 1)

        fabric_label = f" — {fabric}" if fabric else ""
        color_label  = f" {color}"   if color  else ""
        description  = (
            f"USCS Roller Shade{fabric_label}{color_label}, "
            f"{width_in}\"W × {height_in}\"H"
        )

        return {
            'chart':         chart,
            'fabric':        fabric,
            'color':         color,
            'width_in':      width_in,
            'height_in':     height_in,
            'line_items':    [{'description': description, 'dealer_cost': dealer, 'srp': srp}],
            'dealer_cost':   dealer,
            'sell_price':    sell_price,
            'srp':           srp,
            'gross_margin':  f'{gross_margin}%',
        }

    def quote_by_fabric(
        self,
        fabric: str,
        width_in: float,
        height_in: float,
        color: str | None = None,
        target_margin: float = 0.40,
    ) -> dict:
        """Convenience: look up chart automatically by fabric name."""
        chart = self.chart_for_fabric(fabric)
        if not chart:
            raise ValueError(
                f"Fabric '{fabric}' not found in pricing database. "
                f"Use list_fabrics() to see all options."
            )
        return self.quote(chart=chart, width_in=width_in, height_in=height_in,
                         fabric=fabric, color=color, target_margin=target_margin)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def list_charts(self) -> list[str]:
        """Return all chart keys."""
        return list(self._charts.keys())

    def list_fabrics(self) -> dict[str, list[str]]:
        """Return {chart_key: [fabric_names]} for all charts."""
        return {k: v.get('fabrics', []) for k, v in self._charts.items()}

    def find_fabric(self, partial: str) -> list[str]:
        """Search fabrics by partial name."""
        results = []
        for ckey, cdata in self._charts.items():
            for fab in cdata.get('fabrics', []):
                if partial.lower() in fab.lower():
                    results.append(f"{fab} [{ckey}]")
        return results


# ── CLI demo ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    p = UCSPricer()

    print('=== USCS Pricer — Sample Quotes (45% off retail) ===\n')
    print(f"Charts: {p.list_charts()}\n")

    test_cases = [
        {'chart': 'light_filtering_chart_1', 'width_in': 48, 'height_in': 84,
         'fabric': 'Munich Light Filtering'},
        {'chart': 'blackout_chart_1',         'width_in': 60, 'height_in': 96,
         'fabric': 'Blackout fabric'},
        {'chart': 'light_filtering_chart_3',  'width_in': 84, 'height_in': 108},
    ]

    for tc in test_cases:
        try:
            result = p.quote(**tc, target_margin=0.40)
            fab = result.get('fabric') or result['chart']
            print(f"{fab}  {result['width_in']}\"W × {result['height_in']}\"H")
            print(f"  retail=${result['srp']:.2f}  "
                  f"dealer=${result['dealer_cost']:.2f}  "
                  f"sell@40%=${result['sell_price']:.2f}")
            print()
        except ValueError as e:
            print(f"  ERROR: {e}\n")
