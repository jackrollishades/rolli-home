"""
pic_mapper.py — PIC Business Systems Field Mapper
Phase 1B

Translates a QuotedLineItem + LineItemSpec into the exact field
dictionary needed to populate the PIC ordering portal.

PIC field reference: pic_quote_schema.json
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import LineItemSpec, QuotedLineItem

from config import DEFAULTS

# ── SBM Model Code Lookup ─────────────────────────────────────────────────────
# Maps human-readable fabric/style to PIC "Pattern/Model" codes
# Expand this as more fabrics are confirmed from live orders

SBM_FABRIC_TO_MODEL = {
    # Blackout fabrics → Pattern code in PIC
    "sanctuary bo":   "SANCTBOxx",
    "tusk bo":        "TUSKBOxx",
    "balmoral bo":    "BALMBOxx",
    "mesa bo":        "MESABOxx",
    "jersey bo":      "JERSBOxx",
    "linen bo":       "LINENBOxx",
    # Solar / openness
    "kleenscreen":    "KLEENSCxx",
    "serene":         "SERENExx",
    "silverscreen":   "SILVSCxx",
    # Decorative
    "balmoral privacy": "BALMPRxx",
}

# Motor type mappings for PIC "MotorType" field (SBM)
SBM_MOTOR_TYPE_MAP = {
    "automate":  "Automate",
    "somfy":     "Somfy",
    "gaposa":    "Gaposa",
}

# Automate motor key → PIC RolleaseMotors field value
AUTOMATE_TO_ROLLEASE_FIELD = {
    "35mm_quiet_0.7nm":  "Automate 0.7 Nm",
    "35mm_quiet_1.1nm":  "Automate 1.1 Nm",
    "45mm_quiet_2nm":    "Automate 2 Nm",
    "45mm_quiet_3nm":    "Automate 3 Nm",
    "45mm_quiet_6nm":    "Automate 6 Nm",
    "45mm_quiet_10nm":   "Automate 10 Nm",
    "45mm_quiet_15nm":   "Automate 15 Nm",
    # Battery
    "5v_zero_li_ion_0.7nm":  "Automate 0.7 Nm Zero",
    "5v_zero_li_ion_2nm":    "Automate 2 Nm Zero",
}


class PICMapper:
    """
    Static mapper: LineItemSpec + QuotedLineItem → PIC field dict.
    """

    @staticmethod
    def map(spec: "LineItemSpec", qi: "QuotedLineItem") -> dict:
        """
        Return a dict of PIC field name → value for this line item.

        Keys match pic_quote_schema.json line-item fields.
        None values are excluded (PIC uses page defaults).
        """
        vendor = (spec.vendor or "").lower()

        # ── Dimensions ────────────────────────────────────────────────────
        fields = {
            "OverallWidth":  spec.width_in,
            "Height":        spec.height_in,
            "Qty":           spec.qty,
        }

        # ── Room location / sidemark ──────────────────────────────────────
        if spec.room_label:
            fields["RoomLocation"] = spec.room_label
        if spec.room_location:
            fields["RoomLocation"] = spec.room_location  # override if explicit

        # ── Mount, roll direction, control side ──────────────────────────
        fields["Mount"]           = spec.mount          or DEFAULTS["mount"]
        fields["RollDirection"]   = spec.roll_direction or DEFAULTS["roll_direction"]
        fields["ControlLocation"] = spec.control_side   or DEFAULTS["control_side"]

        # ── Hembar ────────────────────────────────────────────────────────
        fields["Hembar"] = spec.hembar or DEFAULTS["hembar"]

        # ── Tube size ─────────────────────────────────────────────────────
        if spec.tube_size:
            fields["TubeSize"] = spec.tube_size
        else:
            fields["TubeSize"] = PICMapper._auto_tube(spec)

        # ── Vendor-specific fields ────────────────────────────────────────
        if vendor == "sbm":
            PICMapper._sbm_fields(spec, qi, fields)
        elif vendor == "ucs":
            PICMapper._ucs_fields(spec, qi, fields)
        # WSC, Rollstar, STS don't use PIC for ordering (yet)

        # ── Notes ─────────────────────────────────────────────────────────
        if spec.notes:
            fields["Description"] = spec.notes

        # Remove None values
        return {k: v for k, v in fields.items() if v is not None}

    # ── SBM PIC fields ────────────────────────────────────────────────────────

    @staticmethod
    def _sbm_fields(spec: "LineItemSpec", qi: "QuotedLineItem", fields: dict):
        """Populate SBM-specific PIC fields."""

        # Pattern/Model: look up fabric code
        fabric_lower = spec.fabric.lower() if spec.fabric else ""
        model_code = SBM_FABRIC_TO_MODEL.get(fabric_lower)
        if model_code:
            fields["Pattern/Model"] = model_code
        else:
            # Fall back to fabric name; PIC operator will confirm
            fields["Pattern/Model"] = spec.fabric

        # Color
        if spec.color:
            fields["Color"] = spec.color

        # Style — SBM roller shades → "Standard"
        fields["Style"] = "Standard"

        # Control type + motor
        if spec.motor_brand:
            fields["ControlType"] = "Motor"
            motor_brand = spec.motor_brand.lower()
            fields["MotorType"] = SBM_MOTOR_TYPE_MAP.get(motor_brand, spec.motor_brand)

            if motor_brand == "automate":
                motor_label = AUTOMATE_TO_ROLLEASE_FIELD.get(
                    spec.motor_key, spec.motor_key
                )
                fields["RolleaseMotors"] = motor_label
            elif motor_brand == "somfy":
                fields["SomfyMotors"] = spec.motor_key
        else:
            fields["ControlType"] = "Continuous Chain"

        # Brackets — standard inside mount default
        if fields.get("Mount") == "Inside":
            fields["Brackets"] = "Inside Mount Standard"
        else:
            fields["Brackets"] = "Outside Mount Standard"

    # ── UCS PIC fields ────────────────────────────────────────────────────────

    @staticmethod
    def _ucs_fields(spec: "LineItemSpec", qi: "QuotedLineItem", fields: dict):
        """Populate US Custom Shades PIC fields."""
        if spec.fabric:
            fields["Pattern/Model"] = spec.fabric
        if spec.color:
            fields["Color"] = spec.color
        fields["Style"] = "Standard"

        if spec.motor_brand:
            fields["ControlType"] = "Motor"
            fields["MotorType"] = spec.motor_brand.title()
            if spec.motor_key:
                fields["RolleaseMotors"] = spec.motor_key
        else:
            fields["ControlType"] = "Continuous Chain"

    # ── Tube auto-selection ────────────────────────────────────────────────────

    @staticmethod
    def _auto_tube(spec: "LineItemSpec") -> str:
        """
        Return a recommended tube size based on width.
        Follows Rollease Acmeda eBOM practical guide (shade_selection_rules.md).
        """
        w = spec.width_in
        if w <= 48:
            return '1-1/8"'
        elif w <= 72:
            return '1-1/2"'
        elif w <= 96:
            return '2"'
        elif w <= 144:
            return '2-1/2"'
        else:
            return '3-1/4"'

    # ── Order-level fields (applied across all items) ────────────────────────

    @staticmethod
    def order_fields(request: "QuoteRequest") -> dict:
        """
        Return the order-level PIC fields (applied once per submission, not per line).
        """
        return {
            "Sidemark":   request.sidemark_or_customer(),
            "Client":     request.customer_name,
            "CustomerPO": request.project_name or request.customer_name,
        }
