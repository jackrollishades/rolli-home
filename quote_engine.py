"""
quote_engine.py — Rolli Home Quote Engine
Phase 1B

Routes LineItemSpec objects to the correct vendor pricer,
assembles QuotedLineItem results, and builds a complete Quote.

Usage:
    from quote_engine import QuoteEngine
    from models import QuoteRequest, LineItemSpec

    engine = QuoteEngine()
    request = QuoteRequest(
        customer_name="Smith Residence",
        project_name="Master Bedroom",
        items=[
            LineItemSpec(
                room_label="Master BR - Left Window",
                vendor="sbm",
                fabric="Sanctuary BO",
                width_in=48,
                height_in=84,
                motor_brand="automate",
                motor_category="radio_110v",
                motor_key="35mm_quiet_6nm",
            )
        ]
    )
    quote = engine.quote(request)
    print(quote.total_sell_price)
"""

from __future__ import annotations
import importlib
import json
import os
from typing import Optional

from models import LineItemSpec, QuoteRequest, QuotedLineItem, Quote
from config import (
    VENDOR_REGISTRY, DEFAULTS, next_quote_number, QUOTE_STORAGE_DIR,
    fabric_weight_class,
)


class QuoteEngine:
    """
    Routes pricing requests to the appropriate vendor pricer.
    Lazy-loads pricers on first use.
    """

    def __init__(self):
        self._pricers: dict = {}

    # ── Pricer loading ──────────────────────────────────────────────────────

    def _get_pricer(self, vendor_key: str):
        """Return (and cache) the pricer instance for a vendor."""
        vendor_key = vendor_key.lower()
        if vendor_key in self._pricers:
            return self._pricers[vendor_key]

        cfg = VENDOR_REGISTRY.get(vendor_key)
        if not cfg:
            raise ValueError(
                f"Unknown vendor '{vendor_key}'. "
                f"Available: {list(VENDOR_REGISTRY.keys())}"
            )

        module = importlib.import_module(cfg["pricer_module"])
        cls = getattr(module, cfg["pricer_class"])
        pricer = cls()
        self._pricers[vendor_key] = pricer
        return pricer

    # ── Core quoting ────────────────────────────────────────────────────────

    def quote(self, request: QuoteRequest) -> Quote:
        """
        Price all items in the request and return a complete Quote.
        Assigns a new quote number; does NOT persist to disk (call save_quote for that).
        """
        quote_number = next_quote_number()
        quoted_items = []

        for spec in request.items:
            qi = self._price_item(spec, request.target_margin)
            quoted_items.append(qi)

        return Quote(
            quote_number=quote_number,
            request=request,
            line_items=quoted_items,
        )

    def _price_item(self, spec: LineItemSpec, target_margin: float) -> QuotedLineItem:
        """Price a single LineItemSpec. Returns QuotedLineItem (never raises)."""
        qi = QuotedLineItem(spec=spec)

        try:
            vendor_key = (spec.vendor or "").lower()
            if not vendor_key:
                qi.errors.append("No vendor specified on line item.")
                return qi

            pricer = self._get_pricer(vendor_key)
            qi.pricer_used = type(pricer).__name__

            # ── Route to correct vendor method ──────────────────────────────
            if vendor_key == "sbm":
                result = pricer.quote(
                    fabric=spec.fabric,
                    width_in=spec.width_in,
                    height_in=spec.height_in,
                    top_treatment=spec.top_treatment,
                    motor_brand=spec.motor_brand,
                    motor_category=spec.motor_category,
                    motor_key=spec.motor_key,
                    extra_surcharges=spec.extra_surcharges,
                    target_margin=target_margin,
                )
                qi.line_items     = result["line_items"]
                qi.dealer_cost    = result["dealer_cost"]
                qi.sell_price     = result["sell_price"]
                qi.srp            = result["msrp"]
                qi.gross_margin_pct = float(result["gross_margin"].rstrip("%"))

            elif vendor_key == "wsc":
                # Determine roman vs roller
                if spec.wsc_style or spec.wsc_group and spec.wsc_group.startswith("G"):
                    result = pricer.quote_roman(
                        group=spec.wsc_group,
                        width_in=spec.width_in,
                        height_in=spec.height_in,
                        style=spec.wsc_style,
                        lining=spec.wsc_lining,
                        lifting_system=None,
                        motor_brand=spec.motor_brand,
                        motor_key=spec.motor_key,
                        target_margin=target_margin,
                    )
                else:
                    result = pricer.quote_roller(
                        group=spec.wsc_group,
                        width_in=spec.width_in,
                        height_in=spec.height_in,
                        motor_brand=spec.motor_brand,
                        motor_key=spec.motor_key,
                        target_margin=target_margin,
                    )
                qi.line_items     = result.get("line_items", [])
                qi.dealer_cost    = result.get("dealer_cost", 0)
                qi.sell_price     = result.get("sell_price", 0)
                qi.srp            = result.get("srp", result.get("msrp", 0))
                margin = result.get("gross_margin", "0%")
                qi.gross_margin_pct = float(str(margin).rstrip("%"))

            elif vendor_key == "rollstar":
                result = pricer.quote(
                    group=spec.rollstar_group,
                    width_in=spec.width_in,
                    height_in=spec.height_in,
                    fabric=spec.fabric,
                    target_margin=target_margin,
                )
                qi.line_items     = result.get("line_items", [])
                qi.dealer_cost    = result.get("dealer_cost", 0)
                qi.sell_price     = result.get("sell_price", 0)
                qi.srp            = result.get("srp", 0)
                margin = result.get("gross_margin", "0%")
                qi.gross_margin_pct = float(str(margin).rstrip("%"))

            elif vendor_key == "sts":
                result = pricer.quote(
                    style=spec.sts_style,
                    width_in=spec.width_in,
                    height_in=spec.height_in,
                    fabric=spec.fabric,
                    color=spec.color,
                    target_margin=target_margin,
                )
                qi.line_items     = result.get("line_items", [])
                qi.dealer_cost    = result.get("dealer_cost", 0)
                qi.sell_price     = result.get("sell_price", 0)
                qi.srp            = result.get("srp", 0)
                margin = result.get("gross_margin", "0%")
                qi.gross_margin_pct = float(str(margin).rstrip("%"))

            else:
                qi.errors.append(
                    f"Vendor '{vendor_key}' is registered but no routing logic exists yet. "
                    f"Add it to quote_engine.py _price_item()."
                )
                return qi

            # ── Attach PIC fields ──────────────────────────────────────────
            from pic_mapper import PICMapper
            qi.pic_fields = PICMapper.map(spec, qi)

        except ValueError as e:
            qi.errors.append(str(e))
        except Exception as e:
            qi.errors.append(f"Unexpected error pricing {spec.room_label}: {e}")

        return qi

    # ── Persistence ──────────────────────────────────────────────────────────

    def save_quote(self, quote: Quote) -> str:
        """
        Persist quote to JSON file.
        Returns the file path.
        """
        import dataclasses
        from datetime import date

        os.makedirs(QUOTE_STORAGE_DIR, exist_ok=True)
        path = os.path.join(QUOTE_STORAGE_DIR, f"{quote.quote_number}.json")

        def serialise(obj):
            if dataclasses.is_dataclass(obj):
                return dataclasses.asdict(obj)
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Cannot serialise {type(obj)}")

        with open(path, "w") as f:
            json.dump(dataclasses.asdict(quote), f, indent=2, default=serialise)

        return path

    # ── Convenience ──────────────────────────────────────────────────────────

    def quote_and_save(self, request: QuoteRequest) -> tuple[Quote, str]:
        """Price, persist, and return (Quote, file_path)."""
        q = self.quote(request)
        path = self.save_quote(q)
        return q, path

    def print_summary(self, quote: Quote):
        """Print a console summary of the quote."""
        r = quote.request
        print(f"\n{'='*60}")
        print(f"QUOTE {quote.quote_number}")
        print(f"Customer: {r.customer_name}  |  Project: {r.project_name}")
        print(f"{'='*60}")

        for li in quote.line_items:
            s = li.spec
            qty_label = f"  × {s.qty}" if s.qty > 1 else ""
            status = "✓" if li.ok else "✗"
            print(f"\n  {status} [{s.room_label}]  "
                  f"{s.vendor.upper()} | {s.fabric or s.wsc_group or s.rollstar_group or s.sts_style}")
            print(f"     {s.width_in}\"W × {s.height_in}\"H{qty_label}")
            for item in li.line_items:
                print(f"     • {item['description']:50s}  "
                      f"cost=${item['dealer_cost']:.2f}")
            if li.ok:
                print(f"     ─── Unit dealer=${li.dealer_cost:.2f}  "
                      f"sell@{li.gross_margin_pct:.0f}%=${li.sell_price:.2f}  "
                      f"SRP=${li.srp:.2f}")
                if s.qty > 1:
                    print(f"         Extended: dealer=${li.extended_dealer_cost:.2f}  "
                          f"sell=${li.extended_sell_price:.2f}")
            for err in li.errors:
                print(f"     ✗ ERROR: {err}")
            for w in li.warnings:
                print(f"     ⚠ {w}")

        print(f"\n{'─'*60}")
        print(f"  TOTAL  dealer=${quote.total_dealer_cost:.2f}  "
              f"sell=${quote.total_sell_price:.2f}  "
              f"SRP=${quote.total_srp:.2f}  "
              f"GM={quote.overall_gross_margin_pct:.1f}%")
        if quote.has_errors:
            print(f"\n  ERRORS:")
            for e in quote.error_summary():
                print(f"  ✗ {e}")
        print()
