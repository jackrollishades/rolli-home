"""
models.py — Rolli Home Quote Engine Data Models
Phase 1B

Core data classes for quote generation. Vendor-agnostic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import date


# ── Line Item Specification ──────────────────────────────────────────────────

@dataclass
class LineItemSpec:
    """
    All inputs needed to price and order a single shade.

    Vendor-agnostic: the quote engine routes to the correct pricer based on `vendor`.
    PIC fields (mount, roll_direction, etc.) are optional—defaulted in pic_mapper.
    """

    # ── Identity
    room_label: str                      # e.g. "Master Bedroom Left"
    qty: int = 1

    # ── Dimensions (finished width × drop, inches)
    width_in: float = 0.0
    height_in: float = 0.0

    # ── Vendor & product
    vendor: str = ""                     # "sbm" | "wsc" | "rollstar" | "sts" | ...
    fabric: str = ""                     # Fabric/pattern name (case-insensitive lookup)
    color: str = ""                      # Color name (free text for PIC)

    # ── WSC-specific
    wsc_group: Optional[str] = None      # e.g. "G1R", "G3SL"
    wsc_style: Optional[str] = None      # e.g. "Hobbled", "Flat"
    wsc_lining: Optional[str] = None     # e.g. "None", "Blackout", "Light Filter"

    # ── Rollstar-specific
    rollstar_group: Optional[str] = None  # e.g. "group_1" (from rollstar_pricing_complete.json)

    # ── STS-specific
    sts_style: Optional[str] = None      # e.g. "101-Pacifica"

    # ── UCS-specific
    ucs_chart: Optional[str] = None      # e.g. "light_filtering_chart_1"

    # ── TWO-specific
    two_fabric_style: Optional[str] = None          # e.g. "Light Filtering" | "Blackout" | "Screen"
    two_cover: Optional[str] = None                 # "cassette_neuvo" | "cassette_elite" | "roll_only"
    two_hem_bar: Optional[str] = None               # "concealed" | "fabric_wrapped" | "designer"
    two_side_channels: Optional[str] = None         # "side_only" | "bottom_only" | "side_and_bottom"
    two_door_hold_down: bool = False
    two_remote_5ch: bool = False
    two_wall_charger: bool = False
    two_connect_pro_hub: bool = False
    two_fabric_wrapped_cassette: bool = False

    # ── Motorization
    motor_brand: Optional[str] = None    # "automate" | "somfy" | "gaposa"
    motor_category: Optional[str] = None # "radio_110v" | "battery_integrated" | etc.
    motor_key: Optional[str] = None      # exact key in pricing JSON

    # ── Top treatment / surcharges
    top_treatment: Optional[str] = None  # key in top_treatment_surcharges
    extra_surcharges: list[str] = field(default_factory=list)

    # ── PIC order fields (optional — defaults applied in pic_mapper)
    mount: Optional[str] = None          # "Inside" | "Outside"
    roll_direction: Optional[str] = None # "Regular" | "Reverse"
    control_side: Optional[str] = None   # "Left" | "Right"
    hembar: Optional[str] = None         # e.g. "Standard" | "D30" | "Fabric Wrapped"
    tube_size: Optional[str] = None      # e.g. "1.5\"" | "2\"" — auto-selected if None
    room_location: Optional[str] = None  # Free text for PIC "Room Location" field

    # ── Misc
    notes: str = ""


# ── Quote Request ─────────────────────────────────────────────────────────────

@dataclass
class QuoteRequest:
    """
    Top-level input to the quote engine.
    One QuoteRequest → one Quote document.
    """
    customer_name: str
    project_name: str = ""
    sidemark: str = ""            # Used as PIC Sidemark (falls back to customer_name)
    items: list[LineItemSpec] = field(default_factory=list)
    target_margin: float = 0.40   # Default 40% gross margin
    notes: str = ""
    quote_date: date = field(default_factory=date.today)

    def sidemark_or_customer(self) -> str:
        return self.sidemark or self.customer_name


# ── Quoted Line Item ──────────────────────────────────────────────────────────

@dataclass
class QuotedLineItem:
    """
    Result of pricing one LineItemSpec.
    Includes dealer cost breakdown, sell price, and PIC-ready field map.
    """
    spec: LineItemSpec

    # ── Pricing
    line_items: list[dict] = field(default_factory=list)  # [{description, dealer_cost, srp}]
    dealer_cost: float = 0.0       # Total dealer cost (per unit)
    sell_price: float = 0.0        # Recommended sell price at target margin
    srp: float = 0.0               # MSRP / SRP
    gross_margin_pct: float = 0.0  # e.g. 40.0

    # ── PIC fields (ready to submit)
    pic_fields: dict = field(default_factory=dict)

    # ── Meta
    pricer_used: str = ""          # e.g. "SBMPricer", "WSCPricer"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def extended_dealer_cost(self) -> float:
        return round(self.dealer_cost * self.spec.qty, 2)

    @property
    def extended_sell_price(self) -> float:
        return round(self.sell_price * self.spec.qty, 2)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# ── Quote (final output) ──────────────────────────────────────────────────────

@dataclass
class Quote:
    """
    Final output of the quote engine.
    Contains all priced line items and totals.
    """
    quote_number: str               # e.g. "Q-2026-0042"
    request: QuoteRequest
    line_items: list[QuotedLineItem] = field(default_factory=list)

    @property
    def total_dealer_cost(self) -> float:
        return round(sum(li.extended_dealer_cost for li in self.line_items), 2)

    @property
    def total_sell_price(self) -> float:
        return round(sum(li.extended_sell_price for li in self.line_items), 2)

    @property
    def total_srp(self) -> float:
        return round(sum(li.srp * li.spec.qty for li in self.line_items), 2)

    @property
    def overall_gross_margin_pct(self) -> float:
        sp = self.total_sell_price
        if sp == 0:
            return 0.0
        return round((sp - self.total_dealer_cost) / sp * 100, 1)

    @property
    def has_errors(self) -> bool:
        return any(not li.ok for li in self.line_items)

    def error_summary(self) -> list[str]:
        errs = []
        for li in self.line_items:
            for e in li.errors:
                errs.append(f"[{li.spec.room_label}] {e}")
        return errs
