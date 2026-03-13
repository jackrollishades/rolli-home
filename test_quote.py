"""
SBM Quote Tester
────────────────
Edit the REQUEST block below, then run:
    python test_quote.py

Both files must be in the same folder:
    sbm_pricer.py
    sbm_pricing_complete.json
"""

from sbm_pricer import SBMPricer

# ═══════════════════════════════════════════════════════════════════════════════
#  REQUEST — edit these values, then run the script
# ═══════════════════════════════════════════════════════════════════════════════

fabric      = "Serene"       # Fabric name — run SEARCH MODE below if unsure
width_in    = 48             # Finished width in inches
height_in   = 84             # Finished height in inches

# Top treatment — set to None if not needed
# Options: '3in_fascia_skyline', '4in_fascia_skyline', '5in_fascia_skyline',
#          '3in_4in_fabric_wrapped_fascia', 'skyline_cassette_80_100_120',
#          '3in_pocket_bottom_closure', '4in_pocket_bottom_closure',
#          '5in_pocket_bottom_closure', '6in_pocket_bottom_closure',
#          'dust_cover_valance_fabric_insert', 'l_i_clip_recess_closure',
#          'scalloped_bottom', 'open_bottom', 'fabric_insert'
top_treatment = None

# Motorization — set all three or leave all as None
# motor_brand:    'automate', 'somfy', or 'gaposa'
# motor_category: e.g. 'hardwired_110v', 'radio_110v', 'battery_integrated'
# motor_key:      e.g. '35mm_quiet_6nm', 'sonesse_40_rts'  (run LIST MOTORS below)
motor_brand    = None
motor_category = None
motor_key      = None

# Target gross margin for sell price calculation (0.40 = 40%)
target_margin = 0.40

# ═══════════════════════════════════════════════════════════════════════════════
#  SEARCH MODE — flip to True to find fabric names instead of running a quote
# ═══════════════════════════════════════════════════════════════════════════════

search_fabrics = False       # Set True + edit search_term to find fabrics
search_term    = "linen"     # Partial match, case-insensitive

list_motors    = False       # Set True to list all motors for a brand
list_brand     = "automate"  # 'automate', 'somfy', or 'gaposa'

# ═══════════════════════════════════════════════════════════════════════════════
#  ENGINE — don't edit below this line
# ═══════════════════════════════════════════════════════════════════════════════

p = SBMPricer()

if search_fabrics:
    print(f'\n── Fabrics matching "{search_term}" ──────────────────────────────')
    results = p.find_fabric(search_term)
    if results:
        for r in results:
            print(f'  {r}')
    else:
        print('  No matches found.')
    print()

elif list_motors:
    print(f'\n── Motors: {list_brand} ──────────────────────────────────────────')
    motors = p.list_motors(list_brand)
    for category, keys in motors.items():
        print(f'\n  {category}:')
        for k in keys:
            print(f'    {k}')
    print()

else:
    try:
        result = p.quote(
            fabric=fabric,
            width_in=width_in,
            height_in=height_in,
            top_treatment=top_treatment,
            motor_brand=motor_brand,
            motor_category=motor_category,
            motor_key=motor_key,
            target_margin=target_margin,
        )

        margin_pct = int(target_margin * 100)

        print()
        print('╔══════════════════════════════════════════════════════════════╗')
        print(f'  SBM QUOTE — {result["fabric"]}  {result["width_in"]}"W × {result["height_in"]}"H')
        print(f'  Chart: {result["chart"]}')
        print('╠══════════════════════════════════════════════════════════════╣')
        for li in result['line_items']:
            print(f'  {li["description"]}')
            print(f'    Dealer cost:  ${li["dealer_cost"]:>8.2f}    MSRP: ${li["msrp"]:>8.2f}')
        print('╠══════════════════════════════════════════════════════════════╣')
        print(f'  TOTAL DEALER COST:    ${result["dealer_cost"]:>8.2f}')
        print(f'  SELL PRICE @{margin_pct}% margin: ${result["sell_price"]:>8.2f}')
        print(f'  MSRP (retail):        ${result["msrp"]:>8.2f}')
        print(f'  GROSS MARGIN:          {result["gross_margin"]}')
        print('╚══════════════════════════════════════════════════════════════╝')
        print()

    except ValueError as e:
        print(f'\n  ERROR: {e}\n')
        print('  Tip: set search_fabrics = True to find the correct fabric name.\n')
