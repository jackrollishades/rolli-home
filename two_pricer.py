"""
two_pricer.py — TWO USA / Colourvue Essentials Pricer
Vendor: TWO USA (Colourvue Essentials)
Catalog: V.02.10.26 (February 2026)
Formula: dealer_price = base + (W × H / 144 × fabric_rate) + width_surcharge + options
Note: two_pricing_complete.json contains DEALER prices (no additional discount factor).

Usage:
    from two_pricer import TWOPricer
    p = TWOPricer()
    result = p.quote(
        fabric='Jersey',
        fabric_style='Light Filtering',
        width_in=48,
        height_in=84,
        motorized=True,
    )
"""

import json
import os

_DATA_PATH  = os.path.join(os.path.dirname(__file__), 'two_pricing_complete.json')
_SPECS_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'mnt', 'Quote_Master', 'TWO', 'two_colourvue_specs.json'
)

DEALER_FACTOR = 1.0   # Prices in JSON are already dealer prices


class TWOPricer:
    """
    Prices TWO USA / Colourvue Essentials roller shades.

    Pricing formula (all values from two_pricing_complete.json):
        dealer_cost = base_price
                    + round(W * H / 144, 2) * fabric_rate_per_sqft
                    + width_surcharge(W)
                    + sum(option_surcharges)
    """

    def __init__(self, data_path: str = _DATA_PATH):
        with open(data_path) as f:
            self._data = json.load(f)

        self._base       = self._data['base_prices']
        self._fab_groups = self._data['fabric_groups']
        self._w_sur      = self._data['width_surcharges']
        self._options    = self._data['options']
        self._fab_detail = self._data.get('fabric_details', [])

        # Build fabric lookup: (fabric_lower, style_lower) → group int
        self._fab_lookup: dict[tuple, int] = {}
        for fd in self._fab_detail:
            key = (fd['fabric'].lower(), fd['style'].lower())
            self._fab_lookup[key] = fd['group']
        # Also by fabric name alone (falls back to first match)
        self._fab_name_lookup: dict[str, int] = {}
        for fd in self._fab_detail:
            name = fd['fabric'].lower()
            if name not in self._fab_name_lookup:
                self._fab_name_lookup[name] = fd['group']

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _fabric_group_num(self, fabric: str, fabric_style: str | None = None) -> int:
        """Return the pricing group number (1/2/3) for a fabric."""
        fab = fabric.lower()
        if fabric_style:
            key = (fab, fabric_style.lower())
            if key in self._fab_lookup:
                return self._fab_lookup[key]
        # Fall back to name-only lookup
        if fab in self._fab_name_lookup:
            return self._fab_name_lookup[fab]
        # Default group 2 (light filtering) if not found
        return 2

    def _fabric_rate(self, fabric: str, fabric_style: str | None = None) -> float:
        """Return $/sqft for the fabric group."""
        grp = self._fabric_group_num(fabric, fabric_style)
        group_key = f'group_{grp}_screens' if grp == 1 else (
            'group_2_light_filtering' if grp == 2 else 'group_3_blackout'
        )
        return self._fab_groups[group_key]['rate_per_sqft']

    def _width_surcharge(self, width_in: float) -> float:
        """Return width surcharge based on width bracket."""
        s = self._w_sur
        if width_in > 96:
            return s['over_96']
        elif width_in > 72:
            return s['72_to_96']
        elif width_in > 48:
            return s['48_to_72']
        elif width_in > 36:
            return s['36_to_48']
        return 0.0

    # ── Core pricing ──────────────────────────────────────────────────────────

    def base_dealer_cost(
        self,
        fabric: str,
        width_in: float,
        height_in: float,
        motorized: bool = False,
        fabric_style: str | None = None,
    ) -> float:
        """
        Return dealer cost for the shade body (no options).

        Args:
            fabric:        Fabric name (e.g. 'Jersey', 'Tusk')
            width_in:      Finished width in inches
            height_in:     Finished drop in inches
            motorized:     True for Whispertech/Automate base; False for manual
            fabric_style:  e.g. 'Light Filtering', 'Blackout', 'Screen'
        """
        base = self._base['motorized_automate_1way_rf'] if motorized else self._base['manual']
        rate = self._fabric_rate(fabric, fabric_style)
        sqft = round(width_in * height_in / 144, 4)
        fabric_cost = round(sqft * rate, 2)
        w_sur = self._width_surcharge(width_in)
        return round(base + fabric_cost + w_sur, 2)

    def option_cost(
        self,
        cover: str = 'cassette_neuvo',
        hem_bar: str = 'concealed',
        side_channels: str | None = None,
        door_hold_down: bool = False,
        remote_5ch: bool = False,
        wall_charger: bool = False,
        connect_pro_hub: bool = False,
        fabric_wrapped_cassette: bool = False,
    ) -> tuple[float, list[dict]]:
        """
        Return (total_option_cost, list_of_option_line_items).
        """
        items = []
        total = 0.0
        opt = self._options

        # Cover
        cover_map = {
            'roll_only':                    ('roll_only_open_roll',           'Roll Only'),
            'roll_only_open_roll':          ('roll_only_open_roll',           'Roll Only'),
            'cassette_neuvo':               ('cassette_neuvo',                'Cassette Neuvo'),
            'cassette_neuvo_fabric_wrapped':('cassette_neuvo_fabric_wrapped', 'Cassette Neuvo Fabric Wrapped'),
        }
        cover_key, cover_name = cover_map.get(cover.lower().replace(' ', '_'),
                                               ('cassette_neuvo', 'Cassette Neuvo'))
        if fabric_wrapped_cassette and cover_key == 'cassette_neuvo':
            cover_key  = 'cassette_neuvo_fabric_wrapped'
            cover_name = 'Cassette Neuvo Fabric Wrapped'
        cover_cost = opt['decorative_covers'][cover_key]
        if cover_cost != 0:
            items.append({'description': cover_name, 'dealer_cost': cover_cost})
            total += cover_cost

        # Hem bar
        hb_map = {
            'concealed': ('concealed', 'Concealed Hem Bar'),
            'fabric_wrapped': ('fabric_wrapped', 'Fabric Wrapped Hem Bar'),
            'designer': ('designer', 'Designer Hem Bar'),
        }
        hb_key, hb_name = hb_map.get(hem_bar.lower().replace(' ', '_'),
                                      ('concealed', 'Concealed Hem Bar'))
        hb_cost = opt['hem_bars'][hb_key]
        if hb_cost != 0:
            items.append({'description': hb_name, 'dealer_cost': hb_cost})
            total += hb_cost

        # Side channels
        if side_channels:
            sc_map = {
                'side_only':        ('side_only',        'Side Channels (side only)'),
                'bottom_only':      ('bottom_only',       'Side Channels (bottom only)'),
                'side_and_bottom':  ('side_and_bottom',   'Side Channels (side + bottom)'),
                'l_block_angles':   ('l_block_angles_each', 'L-Block Angles (each)'),
            }
            sc_key, sc_name = sc_map.get(side_channels.lower().replace(' ', '_'),
                                          (None, None))
            if sc_key:
                sc_cost = opt['side_channels'][sc_key]
                items.append({'description': sc_name, 'dealer_cost': sc_cost})
                total += sc_cost

        # Accessories
        if door_hold_down:
            c = opt['magnetic_door_hold_downs']
            items.append({'description': 'Magnetic Door Hold Down', 'dealer_cost': c})
            total += c
        if remote_5ch:
            c = opt['controls']['5_channel_remote']
            items.append({'description': '5-Channel Remote', 'dealer_cost': c})
            total += c
        if wall_charger:
            c = opt['controls']['magnetic_wall_charger']
            items.append({'description': 'Magnetic Wall Charger', 'dealer_cost': c})
            total += c
        if connect_pro_hub:
            c = opt['controls']['whispertech_connect_pro_hub']
            items.append({'description': 'Whispertech Connect Pro Hub', 'dealer_cost': c})
            total += c

        return round(total, 2), items

    # ── Full quote ────────────────────────────────────────────────────────────

    def quote(
        self,
        fabric: str,
        width_in: float,
        height_in: float,
        fabric_style: str | None = None,
        color: str | None = None,
        motorized: bool = False,
        cover: str = 'cassette_neuvo',
        hem_bar: str = 'concealed',
        side_channels: str | None = None,
        door_hold_down: bool = False,
        remote_5ch: bool = False,
        wall_charger: bool = False,
        connect_pro_hub: bool = False,
        fabric_wrapped_cassette: bool = False,
        target_margin: float = 0.40,
    ) -> dict:
        """
        Compute a full TWO USA dealer quote for one roller shade.

        Returns dict with dealer_cost, sell_price, line_items, etc.
        """
        # Body cost
        body_cost = self.base_dealer_cost(
            fabric=fabric,
            width_in=width_in,
            height_in=height_in,
            motorized=motorized,
            fabric_style=fabric_style,
        )

        style_label = f" {fabric_style}" if fabric_style else ""
        color_label = f" {color}"       if color        else ""
        motor_label = " Motorized"       if motorized    else " Manual"
        body_desc   = (
            f"TWO Colourvue{motor_label} Shade — {fabric}{style_label}{color_label}, "
            f"{width_in}\"W × {height_in}\"H"
        )
        line_items = [{'description': body_desc, 'dealer_cost': body_cost}]

        # Options
        opt_total, opt_items = self.option_cost(
            cover=cover,
            hem_bar=hem_bar,
            side_channels=side_channels,
            door_hold_down=door_hold_down,
            remote_5ch=remote_5ch,
            wall_charger=wall_charger,
            connect_pro_hub=connect_pro_hub,
            fabric_wrapped_cassette=fabric_wrapped_cassette,
        )
        line_items.extend(opt_items)

        dealer_cost  = round(body_cost + opt_total, 2)
        # SRP: not available from price guide (dealer IS the bottom price)
        # Use dealer_cost as SRP (no markup from factory; our markup = sell_price)
        srp          = dealer_cost
        sell_price   = round(dealer_cost / (1 - target_margin), 2)
        gross_margin = round((sell_price - dealer_cost) / sell_price * 100, 1)

        return {
            'fabric':         fabric,
            'fabric_style':   fabric_style,
            'color':          color,
            'width_in':       width_in,
            'height_in':      height_in,
            'motorized':      motorized,
            'cover':          cover,
            'hem_bar':        hem_bar,
            'line_items':     line_items,
            'dealer_cost':    dealer_cost,
            'sell_price':     sell_price,
            'srp':            srp,
            'gross_margin':   f'{gross_margin}%',
        }

    # ── Utilities ─────────────────────────────────────────────────────────────

    def list_fabrics(self) -> list[dict]:
        """Return all fabrics with style and group info."""
        return [
            {'fabric': fd['fabric'], 'style': fd['style'], 'group': fd['group']}
            for fd in self._fab_detail
        ]

    def fabric_group_num(self, fabric: str, style: str | None = None) -> int:
        return self._fabric_group_num(fabric, style)


# ── CLI demo ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    p = TWOPricer()

    print('=== TWO USA / Colourvue Essentials Pricer ===\n')
    print('Available fabrics:')
    for f in p.list_fabrics():
        print(f"  {f['fabric']} {f['style']} [Group {f['group']}]")
    print()

    test_cases = [
        {'fabric': 'Jersey', 'fabric_style': 'Light Filtering', 'width_in': 36, 'height_in': 72,
         'motorized': False},
        {'fabric': 'Tusk',   'fabric_style': 'Blackout',        'width_in': 60, 'height_in': 84,
         'motorized': True,  'cover': 'cassette_neuvo'},
        {'fabric': 'Mesa',   'fabric_style': 'Blackout',        'width_in': 84, 'height_in': 96,
         'motorized': True,  'side_channels': 'side_and_bottom'},
    ]

    for tc in test_cases:
        result = p.quote(**tc, target_margin=0.40)
        print(f"{result['fabric']} {result.get('fabric_style','')} "
              f"{result['width_in']}\"W × {result['height_in']}\"H "
              f"{'(Motorized)' if result['motorized'] else '(Manual)'}")
        print(f"  dealer=${result['dealer_cost']:.2f}  "
              f"sell@40%=${result['sell_price']:.2f}")
        for li in result['line_items']:
            print(f"  • {li['description']}  ${li['dealer_cost']:.2f}")
        print()
