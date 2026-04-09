"""
rollstar_pricer.py — Rollstar (Fabritec) Pricer
Vendor: Rollstar by Fabritec LLC
Catalog: February 2026
Formula: dealer_cost = SRP × 0.50 (50% trade discount — Jeanette Cruz, Fabritec)

Usage:
    from rollstar_pricer import RollstarPricer
    p = RollstarPricer()
    result = p.quote(group='group_1', width_in=48, height_in=84)
"""

import json
import os
import bisect

_DATA_PATH = os.path.join(os.path.dirname(__file__), 'rollstar_pricing_complete.json')

DEALER_FACTOR = 0.50


def _find_break_index(value: float, breaks: list) -> int:
    """Ceiling lookup: return index of first break >= value."""
    idx = bisect.bisect_left(breaks, value)
    return min(idx, len(breaks) - 1)


class RollstarPricer:
    def __init__(self, data_path: str = _DATA_PATH):
        with open(data_path) as f:
            self._data = json.load(f)

        self._width_breaks  = self._data['width_breaks']
        self._height_breaks = self._data['height_breaks']
        self._groups        = self._data['price_groups']

        # Build fabric → group lookup
        self._fabric_group: dict[str, str] = {}
        for gkey, gdata in self._groups.items():
            for fabric in gdata.get('fabrics', []):
                self._fabric_group[fabric.lower()] = gkey

    # ── Core lookups ─────────────────────────────────────────────────────────

    def fabric_group(self, fabric: str) -> str | None:
        """Return the group key for a fabric name, or None."""
        return self._fabric_group.get(fabric.lower())

    def base_srp(self, group: str, width_in: float, height_in: float) -> float:
        """Return retail (SRP) price for a shade."""
        g = self._groups.get(group)
        if not g:
            raise ValueError(
                f"Group '{group}' not found. "
                f"Available: {list(self._groups.keys())}"
            )
        w_idx = _find_break_index(width_in,  self._width_breaks)
        h_idx = _find_break_index(height_in, self._height_breaks)
        return float(g['srp_grid'][h_idx][w_idx])

    def base_dealer_cost(self, group: str, width_in: float, height_in: float) -> float:
        """Return dealer cost (SRP × 0.50)."""
        return round(self.base_srp(group, width_in, height_in) * DEALER_FACTOR, 2)

    # ── Full quote ────────────────────────────────────────────────────────────

    def quote(
        self,
        group: str,
        width_in: float,
        height_in: float,
        fabric: str = None,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Compute a full quote for one Rollstar shade.

        Args:
            group:          Price group key (e.g. 'group_1')
            width_in:       Finished width in inches
            height_in:      Finished height in inches
            fabric:         Optional fabric name (used for description)
            target_margin:  Gross margin for sell price (default 40%)

        Returns:
            Dict with dealer_cost, sell_price, srp, line_items
        """
        if not group:
            raise ValueError("group is required")

        srp         = self.base_srp(group, width_in, height_in)
        dealer_cost = round(srp * DEALER_FACTOR, 2)
        sell_price  = round(dealer_cost / (1 - target_margin), 2)
        gross_margin = round((sell_price - dealer_cost) / sell_price * 100, 1)

        group_name = self._groups[group]['name'] if group in self._groups else group
        fabric_label = f", {fabric}" if fabric else ""
        description = f"Rollstar shade ({group_name}{fabric_label}, {width_in}\"W × {height_in}\"H)"

        return {
            'group':        group,
            'group_name':   group_name,
            'fabric':       fabric,
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

    def list_groups(self) -> dict[str, list[str]]:
        """Return all groups with their fabric lists."""
        return {
            k: v.get('fabrics', [])
            for k, v in self._groups.items()
        }

    def find_fabric(self, partial: str) -> list[str]:
        """Search for fabrics by partial name."""
        results = []
        for gkey, gdata in self._groups.items():
            for fab in gdata.get('fabrics', []):
                if partial.lower() in fab.lower():
                    results.append(f"{fab} [{gkey}]")
        return results

    def quote_by_fabric(
        self,
        fabric: str,
        width_in: float,
        height_in: float,
        target_margin: float = 0.40,
    ) -> dict:
        """Convenience: quote by fabric name (auto-looks up group)."""
        group = self.fabric_group(fabric)
        if not group:
            raise ValueError(
                f"Fabric '{fabric}' not found. "
                f"Use find_fabric() to search."
            )
        return self.quote(group=group, width_in=width_in, height_in=height_in,
                         fabric=fabric, target_margin=target_margin)


# ── CLI demo ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    p = RollstarPricer()

    print('=== Rollstar Pricer — Sample Quotes (50% discount) ===\n')

    test_cases = [
        {'group': 'group_1',  'width_in': 48,  'height_in': 84,  'fabric': 'Basic Blackout'},
        {'group': 'group_5',  'width_in': 72,  'height_in': 96,  'fabric': 'Basketweave Plus 3%'},
        {'group': 'group_10', 'width_in': 96,  'height_in': 120, 'fabric': 'M-Screen 3%'},
        {'group': 'group_14', 'width_in': 120, 'height_in': 144, 'fabric': 'Balmoral Blackout'},
    ]

    for tc in test_cases:
        try:
            result = p.quote(**tc, target_margin=0.40)
            print(f"{result.get('fabric', '')} [{result['group_name']}] "
                  f"{result['width_in']}\"W × {result['height_in']}\"H")
            print(f"  SRP=${result['srp']:.2f}  "
                  f"dealer=${result['dealer_cost']:.2f}  "
                  f"sell@40%=${result['sell_price']:.2f}")
            print()
        except ValueError as e:
            print(f"  ERROR: {e}\n")
