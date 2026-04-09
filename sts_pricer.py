"""
sts_pricer.py — Style Studio (Fabritec) Pricer
Vendor: Style Studio by Fabritec LLC
Catalog: February 2026
Formula: dealer_cost = SRP × 0.50 (50% trade discount — Jeanette Cruz, Fabritec)

Usage:
    from sts_pricer import STSPricer
    p = STSPricer()
    result = p.quote(style='101-Pacifica', width_in=48, height_in=84)
"""

import json
import os
import bisect

_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sts_pricing_complete.json')

DEALER_FACTOR = 0.50


def _find_break_index(value: float, breaks: list) -> int:
    """Ceiling lookup: return index of first break >= value."""
    idx = bisect.bisect_left(breaks, value)
    return min(idx, len(breaks) - 1)


class STSPricer:
    def __init__(self, data_path: str = _DATA_PATH):
        with open(data_path) as f:
            self._data = json.load(f)

        # Support both 'price_groups' and 'styles' key names
        self._styles = (
            self._data.get('styles') or
            self._data.get('price_groups') or
            {}
        )

        self._width_breaks  = (
            self._data.get('width_breaks') or
            self._data.get('width_breaks_standard') or
            [24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114]
        )
        self._height_breaks = (
            self._data.get('height_breaks') or
            self._data.get('height_breaks_standard') or
            [36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144]
        )

        # Build style name → key lookup (case-insensitive)
        self._style_key: dict[str, str] = {}
        for skey, sdata in self._styles.items():
            name = sdata.get('style_name', skey)
            self._style_key[name.lower()] = skey
            # Also register by code (e.g. "101" from "101-Pacifica")
            code = name.split('-')[0].strip()
            self._style_key[code] = skey

    # ── Core lookups ─────────────────────────────────────────────────────────

    def style_key(self, style: str) -> str | None:
        """Return the style dict key for a style name or code."""
        return self._style_key.get(style.lower())

    def base_srp(self, style: str, width_in: float, height_in: float) -> float:
        """Return retail (SRP) price for a shade."""
        skey = self.style_key(style) or style
        s = self._styles.get(skey)
        if not s:
            raise ValueError(
                f"Style '{style}' not found. "
                f"Available: {[v.get('style_name', k) for k, v in self._styles.items()]}"
            )

        # Some styles have narrower width ranges
        grid = s.get('pricing_grid', s.get('srp_grid', []))
        if not grid:
            raise ValueError(f"No pricing grid for style '{style}'")

        n_cols = len(grid[0]) if grid else 0
        wb = self._width_breaks[:n_cols]

        w_idx = _find_break_index(width_in,  wb)
        h_idx = _find_break_index(height_in, self._height_breaks)

        # Clamp indices
        w_idx = min(w_idx, n_cols - 1)
        h_idx = min(h_idx, len(grid) - 1)

        return float(grid[h_idx][w_idx])

    def base_dealer_cost(self, style: str, width_in: float, height_in: float) -> float:
        """Return dealer cost (SRP × 0.50)."""
        return round(self.base_srp(style, width_in, height_in) * DEALER_FACTOR, 2)

    # ── Full quote ────────────────────────────────────────────────────────────

    def quote(
        self,
        style: str,
        width_in: float,
        height_in: float,
        fabric: str = None,
        color: str = None,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Compute a full quote for one STS roman shade.

        Args:
            style:          Style name or code (e.g. '101-Pacifica' or '101')
            width_in:       Finished width in inches
            height_in:      Finished height in inches
            fabric:         Optional fabric name
            color:          Optional color name
            target_margin:  Gross margin for sell price (default 40%)
        """
        skey = self.style_key(style)
        if not skey:
            raise ValueError(
                f"Style '{style}' not found. "
                f"Call list_styles() to see options."
            )

        sdata = self._styles[skey]
        style_name = sdata.get('style_name', skey)

        srp         = self.base_srp(style, width_in, height_in)
        dealer_cost = round(srp * DEALER_FACTOR, 2)
        sell_price  = round(dealer_cost / (1 - target_margin), 2)
        gross_margin = round((sell_price - dealer_cost) / sell_price * 100, 1)

        fabric_label = f", {fabric}" if fabric else ""
        color_label  = f" {color}"   if color  else ""
        description  = (f"STS Roman Shade ({style_name}{fabric_label}{color_label}, "
                        f"{width_in}\"W × {height_in}\"H)")

        return {
            'style':        style_name,
            'style_key':    skey,
            'fabric':       fabric,
            'color':        color,
            'width_in':     width_in,
            'height_in':    height_in,
            'line_items':   [{
                'description': description,
                'dealer_cost': dealer_cost,
                'srp':         srp,
            }],
            'dealer_cost':  dealer_cost,
            'sell_price':   sell_price,
            'srp':          srp,
            'gross_margin': f'{gross_margin}%',
        }

    # ── Utilities ─────────────────────────────────────────────────────────────

    def list_styles(self) -> list[str]:
        """Return all style names."""
        return [v.get('style_name', k) for k, v in self._styles.items()]

    def find_style(self, partial: str) -> list[str]:
        """Search styles by partial name."""
        return [name for name in self.list_styles()
                if partial.lower() in name.lower()]


# ── CLI demo ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    p = STSPricer()

    print('=== STS Pricer — Sample Quotes (50% discount) ===\n')
    print(f"Available styles: {p.list_styles()}\n")

    test_cases = [
        {'style': '101-Pacifica', 'width_in': 48, 'height_in': 84},
        {'style': '103-Balboa',   'width_in': 60, 'height_in': 96},
        {'style': '109-Malibu',   'width_in': 72, 'height_in': 108},
    ]

    for tc in test_cases:
        try:
            result = p.quote(**tc, target_margin=0.40)
            print(f"{result['style']} {result['width_in']}\"W × {result['height_in']}\"H")
            print(f"  SRP=${result['srp']:.2f}  "
                  f"dealer=${result['dealer_cost']:.2f}  "
                  f"sell@40%=${result['sell_price']:.2f}")
            print()
        except ValueError as e:
            print(f"  ERROR: {e}\n")
