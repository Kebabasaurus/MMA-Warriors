import json
import hashlib
import math
import random
import tkinter as tk
from copy import deepcopy
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion


class MediaMixin:
    """Shared media market, campaign, contract, audience, and AI logic.

    All state is kept in ordinary dictionaries so universe databases remain
    editable and old saves can be repaired without a one-off migration tool.
    ``finance['media_rights']`` remains the primary-contract alias used by the
    existing event finance code.
    """

    MEDIA_STRATEGIES = (
        "Balanced", "Sporting Credibility", "Star Builder", "Viral Growth",
        "Regional Expansion", "Sponsor Friendly", "Crisis Management",
    )
    MEDIA_PRODUCTION_QUALITY = {"Lean": 20, "Standard": 45, "Premium": 65, "Spectacle": 85}

    def default_media_companies(self):
        defaults = [
            {"id": "local_fight_stream", "name": "Local Fight Stream", "type": "Regional Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 16, "prestige": 24, "budget": 24, "selectivity": 18, "min_popularity": 8, "min_card_quality": 36, "min_production": 20, "base_fee": 9_000, "editorial_style": "Local access", "audience": "Regional", "active": True, "volatility": 12},
            {"id": "regional_combat_network", "name": "Regional Combat Network", "type": "Syndicated TV", "home_region": "USA", "markets": ["USA", "Canada", "Mexico"], "reach": 30, "prestige": 38, "budget": 38, "selectivity": 32, "min_popularity": 22, "min_card_quality": 44, "min_production": 30, "base_fee": 24_000, "editorial_style": "Regional rivalries", "audience": "Core fight fans", "active": True, "volatility": 15},
            {"id": "combat_cable", "name": "Combat Cable", "type": "Cable", "home_region": "USA", "markets": ["USA", "Canada", "UK"], "reach": 44, "prestige": 52, "budget": 55, "selectivity": 48, "min_popularity": 36, "min_card_quality": 52, "min_production": 42, "base_fee": 58_000, "editorial_style": "Sporting analysis", "audience": "Hardcore", "active": True, "volatility": 13},
            {"id": "euro_fight_tv", "name": "Euro Fight TV", "type": "Television / Streaming", "home_region": "Europe", "markets": ["Europe", "UK"], "reach": 48, "prestige": 57, "budget": 58, "selectivity": 50, "min_popularity": 38, "min_card_quality": 52, "min_production": 44, "base_fee": 72_000, "editorial_style": "European stars", "audience": "International", "active": True, "volatility": 17},
            {"id": "pacific_combat_plus", "name": "Pacific Combat Plus", "type": "Streaming", "home_region": "Japan", "markets": ["Japan", "Asia", "Australia"], "reach": 52, "prestige": 61, "budget": 64, "selectivity": 54, "min_popularity": 40, "min_card_quality": 54, "min_production": 46, "base_fee": 86_000, "editorial_style": "International spectacle", "audience": "Crossover", "active": True, "volatility": 19},
            {"id": "world_fight_pass", "name": "World Fight Pass", "type": "Global Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 66, "prestige": 70, "budget": 72, "selectivity": 62, "min_popularity": 52, "min_card_quality": 60, "min_production": 54, "base_fee": 145_000, "editorial_style": "Deep fight library", "audience": "Global fight fans", "active": True, "volatility": 14},
            {"id": "prime_sports_network", "name": "Prime Sports Network", "type": "Premium Television", "home_region": "USA", "markets": list(REGIONS), "reach": 80, "prestige": 84, "budget": 88, "selectivity": 78, "min_popularity": 67, "min_card_quality": 70, "min_production": 68, "base_fee": 330_000, "editorial_style": "Champions and stars", "audience": "Mainstream", "active": True, "volatility": 11},
            {"id": "global_sports_plus", "name": "Global Sports Plus", "type": "Global Premium Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 92, "prestige": 94, "budget": 96, "selectivity": 91, "min_popularity": 82, "min_card_quality": 78, "min_production": 80, "base_fee": 760_000, "editorial_style": "Global super fights", "audience": "Mass market", "active": True, "volatility": 9},
        ]
        section = self.universe_section("media", {}) if hasattr(self, "universe_section") else {}
        custom = section.get("rights_packages", []) if isinstance(section, dict) else []
        if not isinstance(custom, (list, tuple)):
            custom = []

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback

        def safe_markets(value):
            if isinstance(value, str):
                return [value] if value.strip() else []
            if isinstance(value, (list, tuple, set)):
                return [str(item) for item in value if item is not None and str(item).strip()]
            return []

        converted = []
        for index, row in enumerate(custom):
            if not isinstance(row, dict) or not row.get("name"):
                continue
            name = str(row["name"])
            slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
            reach = max(1, min(99, safe_int(row.get("reach", 25), 25)))
            markets = safe_markets(row.get("markets", REGIONS))
            converted.append({
                "id": row.get("id", slug or f"custom_media_{index}"), "name": name,
                "type": row.get("type", "Streaming"), "home_region": row.get("home_region", "Worldwide"),
                "markets": markets, "reach": reach,
                "prestige": safe_int(row.get("prestige", reach), reach), "budget": safe_int(row.get("budget", reach), reach),
                "selectivity": safe_int(row.get("selectivity", max(12, reach - 8)), max(12, reach - 8)),
                "min_popularity": safe_int(row.get("min_popularity", max(8, reach - 24)), max(8, reach - 24)),
                "min_card_quality": safe_int(row.get("min_card_quality", max(35, reach - 12)), max(35, reach - 12)),
                "min_production": safe_int(row.get("min_production", max(20, reach - 18)), max(20, reach - 18)),
                "base_fee": max(0, safe_int(row.get("base_fee", row.get("fee", 10_000)), 10_000)),
                "editorial_style": row.get("editorial_style", "General fight coverage"),
                "audience": row.get("audience", "Fight fans"), "active": bool(row.get("active", True)),
                "volatility": max(0, min(100, safe_int(row.get("volatility", 15), 15))),
            })
        # Custom universe entries override same-name defaults but the wider
        # market remains populated for old three-package databases.
        by_name = {row["name"].lower(): row for row in defaults}
        for row in converted:
            by_name[row["name"].lower()] = row
        return list(by_name.values())

    def ensure_media_system(self):
        raw_existing = getattr(self, "media_companies", [])
        if isinstance(raw_existing, (list, tuple)):
            existing = list(raw_existing)
        else:
            existing = []
            if raw_existing not in (None, ""):
                self.media_companies_legacy_raw = raw_existing
        # Reading a universe pack is intentionally avoided after initialisation;
        # monthly AI reviews call this method many times in long simulations.
        seeded = self.default_media_companies() if not existing else []
        by_id = {str(row.get("id", row.get("name", ""))): row for row in existing if isinstance(row, dict)}
        for base in seeded:
            row = by_id.get(base["id"])
            if row is None:
                by_id[base["id"]] = dict(base)
            else:
                for key, value in base.items():
                    row.setdefault(key, list(value) if isinstance(value, list) else value)
        self.media_companies = list(by_id.values())
        self.media_market_history = list(getattr(self, "media_market_history", []) or [])[:120]
        raw_last_month = getattr(self, "media_market_last_month", 0)
        try:
            self.media_market_last_month = int(raw_last_month or 0)
        except (TypeError, ValueError):
            self.media_market_last_month = 0
            self.media_market_review_required = True
            self.media_market_review_reason = "Saved media market month is malformed; market history needs review."
        self.ensure_player_media_state()
        for promo in getattr(self, "promotions", []):
            self.ensure_ai_media_state(promo)
        return self.media_companies

    def _media_finance(self, promotion=None):
        if promotion is None:
            if not isinstance(getattr(self, "finance", None), dict):
                self.finance = self.seed_finance()
            return self.finance
        if not isinstance(getattr(promotion, "finance", None), dict):
            promotion.finance = {}
        return promotion.finance

    def _media_finance_readonly(self, promotion=None):
        """Return the existing media envelope without filling or repairing it.

        Desk refreshes are presentation reads.  The normal ``_media_finance``
        helper is intentionally allowed to create a missing envelope for
        gameplay owners, but that behaviour would make merely opening Media
        Rights mutate an old save.  Readers use this accessor and tolerate
        absent legacy keys with their display defaults instead.
        """
        raw = getattr(self, "finance", {}) if promotion is None else getattr(promotion, "finance", {})
        return raw if isinstance(raw, dict) else {}

    def _media_company_values(self, promotion=None):
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
        if promotion is None:
            roster = getattr(self, "roster", [])
            if not isinstance(roster, (list, tuple)):
                roster = []
            return (getattr(self, "player_company_name", "Player Company"), getattr(self, "player_region", "Worldwide"),
                    safe_int(getattr(self, "company_pop", 0), 0), safe_int(getattr(self, "company_stability", 0), 0),
                    safe_int(getattr(self, "cash", 0), 0), roster)
        roster = getattr(promotion, "roster", [])
        if not isinstance(roster, (list, tuple)):
            roster = []
        return (getattr(promotion, "name", "Promotion"), getattr(promotion, "region", "Worldwide"),
                safe_int(getattr(promotion, "reputation_score", 0), 0), safe_int(getattr(promotion, "stability", 0), 0),
                safe_int(getattr(promotion, "cash", 0), 0), roster)

    def _empty_media_rights(self):
        return {"id": "", "outlet_id": "", "name": "No rights package", "months": 0, "fee": 0, "guarantee_per_event": 0, "reach": 0, "events_remaining": 0, "events_total": 0, "status": "Inactive"}

    def _ensure_media_state(self, promotion=None):
        if promotion is None and hasattr(self, "ensure_finance_defaults"):
            self.ensure_finance_defaults()
        finance = self._media_finance(promotion)
        finance.setdefault("media_contracts", [])
        finance.setdefault("media_offers", [])
        finance.setdefault("media_offer_history", [])
        finance.setdefault("media_campaign_history", [])
        finance.setdefault("media_campaign_cooldowns", {})
        finance.setdefault("media_audience_history", [])
        finance.setdefault("media_commercial_receipts", [])
        finance.setdefault("media_relationships", {})
        finance.setdefault("media_strategy", "Balanced")
        finance.setdefault("media_last_offer_month", 0)
        finance.setdefault("media_action_week", -1)
        finance.setdefault("media_actions_used", 0)
        finance.setdefault("media_public_trust", 55)
        finance.setdefault("media_company_buzz", 20)
        finance.setdefault("media_popularity_month", {})
        # M1 campaign planning is a deliberately small organisational layer
        # over the existing media action resolver.  The plan itself is saved,
        # quoted and retargetable; it adds no hidden audience lift or bonus.
        finance.setdefault("media_primary_plan", None)
        finance.setdefault("media_plan_history", [])
        finance.setdefault("media_plan_sequence", 0)
        finance.setdefault("media_successor_offer", None)
        finance.setdefault("media_successor_contract", None)
        finance.setdefault("sponsor_deals", [])
        finance.setdefault("sponsor_offers", [])
        finance.setdefault("sponsor_offer_history", [])
        finance.setdefault("sponsor_duty_history", [])
        finance.setdefault("sponsor_last_pitch_month", -1)
        finance.setdefault("sponsor_pitch_brief", "Balanced Portfolio")
        for collection_key in (
            "media_contracts", "media_offers", "media_offer_history",
            "media_campaign_history", "media_audience_history",
            "media_commercial_receipts", "media_plan_history",
            "sponsor_deals", "sponsor_offers", "sponsor_offer_history", "sponsor_duty_history",
        ):
            if not isinstance(finance.get(collection_key), list):
                if collection_key in finance and finance.get(collection_key) is not None:
                    finance.setdefault(f"{collection_key}_legacy_raw", finance.get(collection_key))
                finance[collection_key] = []
        for mapping_key in ("media_campaign_cooldowns", "media_relationships", "media_popularity_month"):
            if not isinstance(finance.get(mapping_key), dict):
                if mapping_key in finance and finance.get(mapping_key) is not None:
                    finance.setdefault(f"{mapping_key}_legacy_raw", finance.get(mapping_key))
                finance[mapping_key] = {}
        def positive_int(value):
            if isinstance(value, bool):
                return 0
            try:
                return int(value or 0)
            except (TypeError, ValueError, OverflowError):
                return 0
        legacy = finance.get("media_rights")
        if not isinstance(legacy, dict):
            legacy = self._empty_media_rights()
            finance["media_rights"] = legacy
        legacy.setdefault("months", 0)
        legacy.setdefault("fee", legacy.get("guarantee_per_event", 0))
        legacy.setdefault("guarantee_per_event", legacy.get("fee", 0))
        legacy.setdefault("reach", 0)
        legacy_months = positive_int(legacy.get("months", 0))
        # Old active contracts shipped without an event quota.  They should
        # continue paying rather than becoming silently inactive on load.
        if "events_remaining" not in legacy:
            legacy["events_remaining"] = max(1, min(24, legacy_months)) if legacy_months > 0 else 0
        legacy.setdefault("events_total", legacy.get("events_remaining", 0))
        active_contracts = [item for item in finance["media_contracts"] if isinstance(item, dict) and item.get("status", "Active") == "Active" and positive_int(item.get("months", 0)) > 0 and positive_int(item.get("events_remaining", 0)) > 0]
        if (legacy_months > 0 and positive_int(legacy.get("events_remaining", 0)) > 0 and
                legacy.get("name") not in ("", "No rights package") and
                legacy.get("status", "Active") == "Active" and not active_contracts):
            migrated = dict(legacy)
            migrated.setdefault("id", f"legacy_{abs(hash((migrated.get('name'), migrated.get('months')))) % 10_000_000}")
            migrated.setdefault("outlet_id", "")
            migrated.setdefault("type", "Legacy package")
            migrated.setdefault("relationship", 50)
            migrated.setdefault("minimum_rating", 35)
            migrated.setdefault("min_card_quality", 35)
            migrated.setdefault("min_production", 20)
            migrated.setdefault("breach_strikes", 0)
            migrated.setdefault("exclusivity", "Non-exclusive")
            migrated["status"] = "Active"
            finance["media_contracts"].insert(0, migrated)
        finance["media_contracts"] = finance["media_contracts"][:12]
        finance["media_offers"] = finance["media_offers"][:12]
        finance["media_offer_history"] = finance["media_offer_history"][:40]
        finance["media_campaign_history"] = finance["media_campaign_history"][:60]
        finance["media_audience_history"] = finance["media_audience_history"][:60]
        finance["media_commercial_receipts"] = finance.get("media_commercial_receipts", [])[:120]
        finance["media_plan_history"] = finance.get("media_plan_history", [])[:60]
        finance["sponsor_duty_history"] = finance.get("sponsor_duty_history", [])[:120]
        if not isinstance(finance.get("media_successor_offer"), dict):
            finance["media_successor_offer"] = None
        if not isinstance(finance.get("media_successor_contract"), dict):
            finance["media_successor_contract"] = None
        self.sync_legacy_media_rights(promotion)
        return finance

    def ensure_player_media_state(self):
        return self._ensure_media_state(None)

    def ensure_ai_media_state(self, promo):
        return self._ensure_media_state(promo)

    def active_media_contract(self, promotion=None):
        # Contract lookup is used heavily by dashboard/account readers. Keep
        # it observational: a missing legacy finance envelope must not be
        # seeded merely because a screen asked whether a deal is active.
        # Mutation owners call ``_ensure_media_state`` before this lookup.
        finance = self._media_finance_readonly(promotion)
        rows = finance.get("media_contracts", []) if isinstance(finance, dict) else []
        if not isinstance(rows, (list, tuple)):
            return None
        def positive_int(value):
            if isinstance(value, bool):
                return 0
            try:
                return int(value or 0)
            except (TypeError, ValueError, OverflowError):
                return 0
        return next((item for item in rows if isinstance(item, dict)
                     and item.get("status", "Active") == "Active"
                     and positive_int(item.get("months", 0)) > 0
                     and positive_int(item.get("events_remaining", 0)) > 0), None)

    @staticmethod
    def media_contract_delivery_history(active, history):
        """Project delivery rows attributable to one contract without repair."""
        if not isinstance(active, dict) or not isinstance(history, (list, tuple)):
            return [], 0
        contract_id = str(active.get("contract_id", "") or active.get("id", "") or "").strip()
        outlet_id = str(active.get("outlet_id", "") or "").strip()
        outlet_name = str(active.get("name", "") or "").strip()
        matched = []
        unscoped = 0
        for row in history:
            if not isinstance(row, dict):
                continue
            row_contract_id = str(row.get("contract_id", "") or "").strip()
            row_outlet_id = str(row.get("outlet_id", "") or "").strip()
            row_outlet_name = str(row.get("outlet", "") or "").strip()
            if contract_id:
                if row_contract_id == contract_id:
                    matched.append(row)
                elif not row_contract_id and ((outlet_id and row_outlet_id == outlet_id)
                                               or (not outlet_id and outlet_name and row_outlet_name == outlet_name)):
                    unscoped += 1
                continue
            if row_contract_id:
                continue
            if outlet_id and row_outlet_id == outlet_id:
                matched.append(row)
            elif not outlet_id and outlet_name and not row_outlet_id and row_outlet_name == outlet_name:
                matched.append(row)
        return matched, unscoped

    @staticmethod
    def media_renewal_due(contract):
        """Whether the saved contract is inside the renewal review window."""
        if not isinstance(contract, dict) or contract.get("status", "Active") != "Active":
            return False
        try:
            months = int(contract.get("months", 0) or 0)
            events = int(contract.get("events_remaining", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            return False
        return months <= 2 or events <= 2

    @staticmethod
    def media_contract_terminal_status(contract):
        """Return the truthful terminal label for a rights contract."""
        if not isinstance(contract, dict):
            return "Needs review"
        saved_status = str(contract.get("status", "Active") or "Active")
        if saved_status in ("Terminated", "Terminated for delivery failures"):
            return "Terminated"
        if saved_status == "Fulfilled":
            return "Fulfilled"
        if saved_status == "Expired with shortfall":
            return "Expired with shortfall"
        if saved_status in ("Bought out", "Terminated by player"):
            return "Terminated"
        def parsed(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return None
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return None

        remaining = parsed(contract.get("events_remaining", 0))
        months = parsed(contract.get("months", 0))
        breaches = parsed(contract.get("breach_strikes", 0))
        if remaining is None or months is None or breaches is None:
            # A terminal label must not turn unknown legacy evidence into a
            # false clean delivery. Keep the row visible for an explicit
            # review/migration boundary instead.
            return "Needs review"
        if remaining <= 0:
            # A delivery failure is still a shortfall even when it consumed
            # the final entitlement. A clean quota is Fulfilled.
            return "Fulfilled" if breaches <= 0 else "Expired with shortfall"
        if months <= 0:
            return "Expired with shortfall"
        return "Active"

    def media_contract_history_readonly(self, promotion=None, limit=12):
        """Return saved rights contracts for account-review display only."""
        finance = self._media_finance_readonly(promotion)
        rows = finance.get("media_contracts", []) if isinstance(finance, dict) else []
        if not isinstance(rows, list):
            return []
        try:
            size = max(1, min(100, int(limit or 12)))
        except (TypeError, ValueError, OverflowError):
            size = 12
        def number(value, fallback=0):
            try:
                return int(value or fallback)
            except (TypeError, ValueError, OverflowError):
                return int(fallback)
        result = []
        for row in rows[:size]:
            if not isinstance(row, dict):
                continue
            result.append({
                "contract_id": str(row.get("id", "") or ""),
                "outlet_id": str(row.get("outlet_id", "") or ""),
                "name": str(row.get("name", "Rights partner") or "Rights partner"),
                "status": str(row.get("status", "Active") or "Active"),
                "lifecycle_status": self.media_contract_terminal_status(row),
                "months": number(row.get("months", 0)),
                "events_remaining": number(row.get("events_remaining", 0)),
                "events_total": number(row.get("events_total", row.get("events_remaining", 0))),
                "breach_strikes": number(row.get("breach_strikes", 0)),
                "fee": number(row.get("fee", row.get("guarantee_per_event", 0))),
            })
        return deepcopy(result)

    def media_contract_terms(self, contract):
        """Return one truthful rights-terms view while retaining legacy aliases.

        Existing saves occasionally disagree on ``fee`` versus
        ``guarantee_per_event``.  The compatibility payment path has always
        preferred ``fee`` when present, so this read model reports that basis
        and a warning instead of silently rewriting history.
        """
        contract = contract if isinstance(contract, dict) else {}
        def number(value, fallback=0):
            if isinstance(value, bool):
                return int(fallback)
            try:
                return int(value or fallback)
            except (TypeError, ValueError, OverflowError):
                return int(fallback)
        has_fee = "fee" in contract and contract.get("fee") is not None
        has_guarantee = "guarantee_per_event" in contract and contract.get("guarantee_per_event") is not None
        try:
            fee = int(contract.get("fee")) if has_fee else int(contract.get("guarantee_per_event", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            fee = 0
        try:
            guarantee = int(contract.get("guarantee_per_event")) if has_guarantee else fee
        except (TypeError, ValueError, OverflowError):
            guarantee = fee
        conflict = bool(has_fee and has_guarantee and fee != guarantee)
        tier = str(contract.get("production_tier", "") or "")
        if not tier:
            try:
                threshold = int(contract.get("min_production", 45) or 45)
            except (TypeError, ValueError, OverflowError):
                threshold = 45
            tier = "Spectacle" if threshold >= 85 else "Premium" if threshold >= 65 else "Standard" if threshold >= 45 else "Lean"
        if tier not in ("Lean", "Standard", "Premium", "Spectacle"):
            tier = "Standard"
        try:
            minimum_production = int(contract.get("min_production", 45) or 45)
        except (TypeError, ValueError, OverflowError):
            minimum_production = 45
        return {
            "canonical_fee": fee, "fee": fee, "guarantee_per_event": guarantee,
            "payment_basis": "fee" if has_fee else "guarantee_per_event",
            "alias_conflict": conflict,
            "warning": "Legacy fee aliases disagree; existing payment basis is retained." if conflict else "",
            "production_tier": tier, "minimum_production": minimum_production,
            "months": max(0, number(contract.get("months", 0))), "events_remaining": max(0, number(contract.get("events_remaining", 0))),
        }

    def media_event_production_quality(self, event):
        """Resolve the disclosed MMA production tier to its contractual scale."""
        event = event if isinstance(event, dict) else {}
        tier = str(event.get("production_tier", "Standard") or "Standard")
        return tier, int(self.MEDIA_PRODUCTION_QUALITY.get(tier, self.MEDIA_PRODUCTION_QUALITY["Standard"]))

    def sync_legacy_media_rights(self, promotion=None):
        finance = self._media_finance(promotion)
        active = self.active_media_contract(promotion)
        finance["media_rights"] = active if active else self._empty_media_rights()
        return finance["media_rights"]

    def media_action_capacity(self, promotion=None):
        if promotion is not None:
            strategy = getattr(promotion, "strategy", {}) or {}
            if not isinstance(strategy, dict):
                strategy = {}
            try:
                size = int(getattr(promotion, "size", 0) or 0)
            except (TypeError, ValueError):
                size = 0
            try:
                commercial = int(strategy.get("commercial_strength", size) or size)
            except (TypeError, ValueError):
                commercial = size
            return 2 + (1 if commercial >= 70 else 0)
        marketing = self.staff_skill("Marketing") if hasattr(self, "staff_skill") else 45
        return 2 + (1 if marketing >= 68 else 0) + (1 if marketing >= 88 else 0)

    def media_actions_remaining(self, promotion=None):
        finance = self._ensure_media_state(promotion)
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
        marker = (safe_int(getattr(self, "month", 1), 1) - 1) * 4 + safe_int(getattr(self, "week", 1), 1)
        if finance.get("media_action_week") != marker:
            finance["media_action_week"] = marker
            finance["media_actions_used"] = 0
        return max(0, self.media_action_capacity(promotion) - safe_int(finance.get("media_actions_used", 0), 0))

    def media_actions_remaining_readonly(self, promotion=None):
        """Return the current weekly capacity without rolling the action marker."""
        # Do not use ``_media_finance`` here: that gameplay accessor creates a
        # missing/non-mapping envelope. A desk repaint must remain a pure read,
        # even when an old save has malformed media state.
        finance = self._media_finance_readonly(promotion)
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
        marker = (safe_int(getattr(self, "month", 1), 1) - 1) * 4 + safe_int(getattr(self, "week", 1), 1)
        used = max(0, safe_int(finance.get("media_actions_used", 0))) if finance.get("media_action_week") == marker else 0
        return max(0, self.media_action_capacity(promotion) - used)

    def _outlet_for(self, outlet_id):
        return next((item for item in self.media_companies if item.get("id") == outlet_id), None)

    def _media_offer_score(self, outlet, promotion=None):
        _name, region, popularity, stability, _cash, roster = self._media_company_values(promotion)
        stars = sorted((fighter.popularity + fighter.star_quality + fighter.media_presence for fighter in roster if not fighter.retired), reverse=True)[:8]
        star_score = sum(stars) / max(1, len(stars))
        region_fit = 12 if region in outlet.get("markets", []) or "Worldwide" in outlet.get("markets", []) else -18
        relationship = self._media_finance(promotion).get("media_relationships", {}).get(outlet["id"], 50)
        return popularity * 1.35 + stability * 0.48 + star_score * 0.28 + relationship * 0.22 + region_fit - outlet.get("selectivity", 40) + random.randint(-12, 12)

    def generate_media_offers(self, promotion=None, force=False, count=None):
        self.ensure_media_system()
        finance = self._ensure_media_state(promotion)
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))
        if (not force and isinstance(finance.get("media_offers"), list) and
                finance.get("media_offers") and
                safe_int(finance.get("media_last_offer_month", 0), 0) >= safe_int(self.month, 0) - 1):
            return finance["media_offers"]
        self.expire_media_offers(promotion)
        _name, region, popularity, stability, _cash, _roster = self._media_company_values(promotion)
        candidates = []
        for outlet in self.media_companies:
            if not outlet.get("active", True) or popularity + 10 < outlet.get("min_popularity", 0):
                continue
            score = self._media_offer_score(outlet, promotion)
            if score < 20 and outlet.get("reach", 0) > 25:
                continue
            candidates.append((score, outlet))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        desired = max(2, min(5, count or 4))
        chosen = candidates[:desired]
        if len(chosen) < 2:
            chosen = sorted(((self._media_offer_score(o, promotion), o) for o in self.media_companies if o.get("active", True)), key=lambda pair: pair[0], reverse=True)[:2]
        offers = []
        for index, (score, outlet) in enumerate(chosen):
            relationship = finance["media_relationships"].get(outlet["id"], 50)
            leverage = max(0.58, min(1.65, 0.68 + popularity / 115 + stability / 280 + relationship / 500))
            fee = round(outlet["base_fee"] * leverage / 1000) * 1000
            months = random.choice([8, 10, 12, 16, 18, 24])
            events = max(4, min(18, round(months * random.uniform(0.55, 0.9))))
            offer_id = f"{outlet['id']}_{self.month}_{random.randint(1000, 9999)}"
            offers.append({
                "id": offer_id, "outlet_id": outlet["id"], "name": outlet["name"], "type": outlet["type"],
                "reach": outlet["reach"], "fee": max(4_000, fee), "guarantee_per_event": max(4_000, fee),
                "months": months, "events_total": events, "events_remaining": events,
                "minimum_rating": max(32, outlet.get("min_card_quality", 45) - 4),
                "min_card_quality": outlet.get("min_card_quality", 45), "min_production": outlet.get("min_production", 30),
                "exclusivity": "Exclusive" if outlet["reach"] >= 42 else "Regional non-exclusive",
                "relationship": relationship, "breach_strikes": 0, "performance_bonus": round(max(0, fee) * 0.18),
                "termination_fee": round(max(4_000, fee) * max(2, events) * 0.18),
                "region": region, "created_month": self.month, "expires_month": self.month + 2,
                "status": "Offer", "market_score": round(score),
            })
        finance["media_offers"] = offers
        finance["media_last_offer_month"] = self.month
        return offers

    def expire_media_offers(self, promotion=None):
        finance = self._ensure_media_state(promotion)
        kept = []
        for offer in finance.get("media_offers", []):
            if not isinstance(offer, dict):
                # Retain non-dictionary legacy evidence for the explicit
                # migration boundary; a monthly refresh must not drop it.
                kept.append(offer)
                finance.setdefault("media_offer_review_required", True)
                finance.setdefault("media_offer_review_reason", "One or more saved media offers are malformed.")
                continue
            expiry = offer.get("expires_month", self.month + 1)
            try:
                expiry = int(expiry if expiry is not None else self.month + 1)
            except (TypeError, ValueError):
                kept.append(offer)
                finance.setdefault("media_offer_review_required", True)
                finance.setdefault("media_offer_review_reason", "One or more saved media offers have malformed expiry terms.")
                continue
            if expiry < self.month:
                expired = dict(offer); expired["status"] = "Expired"
                finance["media_offer_history"].insert(0, expired)
            else:
                kept.append(offer)
        finance["media_offers"] = kept[:12]
        finance["media_offer_history"] = finance["media_offer_history"][:40]
        return kept

    def _accept_media_offer(self, offer_id, promotion=None, counter=None):
        finance = self._ensure_media_state(promotion)
        offer = next((item for item in finance["media_offers"] if isinstance(item, dict) and item.get("id") == offer_id), None)
        if not offer:
            return False, "That offer is no longer available."
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback
        required = {
            "fee": safe_int(offer.get("fee", offer.get("guarantee_per_event", 0)), None),
            "reach": safe_int(offer.get("reach", 0), None),
            "months": safe_int(offer.get("months", 0), None),
            "events": safe_int(offer.get("events_total", offer.get("events_remaining", 0)), None),
        }
        if (any(value is None for value in required.values()) or required["months"] <= 0 or
                required["events"] <= 0 or not str(offer.get("outlet_id", "") or "")):
            finance.setdefault("media_offer_review_required", True)
            finance.setdefault("media_offer_review_reason", "The selected media offer has malformed terms and cannot be signed.")
            return False, "That media offer has malformed terms and needs review before it can be signed."
        active = self.active_media_contract(promotion)
        buyout = active.get("termination_fee", 0) if active else 0
        if promotion is None:
            if buyout and self.cash < buyout:
                return False, f"Replacing the active deal requires a ${buyout:,} buyout."
            self.cash -= buyout
            if buyout:
                self.record_finance_transaction(
                    f"Media contract buyout: {active.get('name', 'current deal')}", costs=buyout,
                    category="Media", source="Media rights replacement", counterparty=active.get("name", ""),
                    reference=f"media-buyout:{active.get('id', active.get('name', 'current'))}:{self.month}:{self.week}",
                )
        elif buyout:
            if promotion.cash < buyout:
                return False, "The company cannot afford to replace its current deal."
            promotion.cash -= buyout
            if hasattr(self, "record_promotion_finance_transaction"):
                self.record_promotion_finance_transaction(
                    promotion, f"Media contract buyout: {active.get('name', 'current deal')}", costs=buyout,
                    category="Media", source="Media rights replacement", counterparty=active.get("name", ""),
                    reference=f"media-buyout:{active.get('id', active.get('name', 'current'))}:{self.month}:{self.week}",
                )
        if active:
            active["status"] = "Bought out"
        contract = dict(offer)
        if counter:
            contract.update(counter)
        # New accepted/countered terms keep both compatibility aliases in
        # sync.  Legacy conflicting records are only normalised at acceptance;
        # their existing receipt/payment path is never rewritten by a refresh.
        try:
            canonical_fee = int(contract.get("fee", contract.get("guarantee_per_event", 0)) or 0)
        except (TypeError, ValueError):
            canonical_fee = 0
        contract["fee"] = canonical_fee
        contract["guarantee_per_event"] = canonical_fee
        contract.setdefault("terms_version", 1)
        contract.setdefault("production_tier", self.media_contract_terms(contract).get("production_tier", "Standard"))
        contract["status"] = "Active"
        contract["signed_month"] = self.month
        contract["events_remaining"] = contract.get("events_total", contract.get("events_remaining", 1))
        finance["media_contracts"].insert(0, contract)
        finance["media_offers"] = [item for item in finance["media_offers"] if not (isinstance(item, dict) and item.get("id") == offer_id)]
        accepted = dict(offer); accepted["status"] = "Accepted"
        finance["media_offer_history"].insert(0, accepted)
        finance["media_relationships"][contract["outlet_id"]] = min(100, finance["media_relationships"].get(contract["outlet_id"], 50) + 4)
        self.sync_legacy_media_rights(promotion)
        return True, f"Signed {contract['name']}: ${contract['fee']:,}/event, reach {contract['reach']}, {contract['events_remaining']} events over {contract['months']} months."

    def accept_player_media_offer(self, offer_id, counter=None):
        return self._accept_media_offer(offer_id, None, counter)

    def reject_player_media_offer(self, offer_id):
        finance = self.ensure_player_media_state()
        offer = next((item for item in finance["media_offers"] if isinstance(item, dict) and item.get("id") == offer_id), None)
        if not offer:
            return False, "That offer is no longer available."
        finance["media_offers"].remove(offer)
        rejected = dict(offer); rejected["status"] = "Rejected"
        finance["media_offer_history"].insert(0, rejected)
        finance["media_relationships"][offer["outlet_id"]] = max(0, finance["media_relationships"].get(offer["outlet_id"], 50) - 1)
        return True, f"Rejected {offer['name']}."

    def terminate_player_media_contract(self, contract_id=""):
        finance = self.ensure_player_media_state()
        active = next((item for item in finance["media_contracts"] if (not contract_id or item.get("id") == contract_id) and item.get("status") == "Active"), None)
        if not active:
            return False, "There is no active contract to end."
        cost = int(active.get("termination_fee", 0))
        if self.cash < cost:
            return False, f"Ending this deal costs ${cost:,}."
        self.cash -= cost
        if cost:
            self.record_finance_transaction(
                f"Media contract termination: {active.get('name', 'current deal')}", costs=cost,
                category="Media", source="Media rights termination", counterparty=active.get("name", ""),
                reference=f"media-termination:{active.get('id', active.get('name', 'current'))}:{self.month}:{self.week}",
            )
        active["status"] = "Terminated"
        finance["media_relationships"][active.get("outlet_id", "")] = max(0, finance["media_relationships"].get(active.get("outlet_id", ""), 50) - 14)
        self.sync_legacy_media_rights()
        return True, f"Ended {active['name']} for ${cost:,}. The outlet relationship was damaged."

    def prepare_media_renewal_offer(self, promotion=None):
        """Prepare a no-cost successor quote tied to the current contract."""
        finance = self._ensure_media_state(promotion)
        active = self.active_media_contract(promotion)
        if not active:
            return False, "There is no active rights contract to renew.", None
        existing = finance.get("media_successor_offer")
        try:
            existing_expiry = int(existing.get("expires_month", self.month) or self.month) if isinstance(existing, dict) else self.month - 1
        except (TypeError, ValueError):
            existing_expiry = self.month - 1
        if (isinstance(existing, dict) and existing.get("status") == "Offer" and
                existing_expiry >= int(self.month) and
                existing.get("predecessor_id") == active.get("id")):
            return True, f"Renewal offer from {existing.get('name', 'the outlet')} is already ready for review.", dict(existing)
        if isinstance(existing, dict) and existing.get("status") == "Offer":
            existing["status"] = "Expired"
            finance.setdefault("media_offer_history", []).insert(0, {
                **dict(existing), "decision": "Renewal offer superseded", "month": int(self.month),
            })
        terms = self.media_contract_terms(active)
        offer = dict(active)
        offer.update({
            "id": f"renewal:{active.get('id', active.get('name', 'rights'))}:{self.month}",
            "predecessor_id": active.get("id", active.get("name", "rights")),
            "status": "Offer", "renewal": True, "created_month": int(self.month),
            "expires_month": int(self.month) + 2, "start_trigger": "After predecessor completes",
            "fee": terms["canonical_fee"], "guarantee_per_event": terms["canonical_fee"],
            "terms_version": int(active.get("terms_version", 1) or 1),
        })
        finance["media_successor_offer"] = offer
        return True, f"Prepared a successor offer from {offer.get('name', 'the outlet')}. It starts only after the current deal completes.", dict(offer)

    def accept_media_renewal_offer(self, promotion=None):
        """Queue one accepted successor; no overlapping guarantee is paid."""
        finance = self._ensure_media_state(promotion)
        offer = finance.get("media_successor_offer")
        active = self.active_media_contract(promotion)
        pending = finance.get("media_successor_contract")
        if isinstance(pending, dict) and pending.get("status") == "Pending" and hasattr(self, "foundation_get_receipt"):
            prior_key = f"media-renewal:{pending.get('predecessor_id', '')}:{pending.get('id', '')}"
            prior = self.foundation_get_receipt(prior_key)
            if prior and prior.get("status") != "failed":
                result = prior.get("result") or {"name": pending.get("name", "the outlet")}
                return prior.get("status") == "committed", f"Renewal is already queued with {result.get('name', 'the outlet')}.", result
        if not isinstance(offer, dict) or offer.get("status") != "Offer":
            return False, "Prepare a renewal offer before accepting one.", None
        if not active or str(offer.get("predecessor_id")) != str(active.get("id", active.get("name", "rights"))):
            return False, "The current rights deal changed; refresh the renewal offer first.", None
        if int(offer.get("expires_month", self.month) or self.month) < int(self.month):
            offer["status"] = "Expired"
            return False, "That renewal offer has expired.", None
        operation_key = f"media-renewal:{offer.get('predecessor_id', '')}:{offer.get('id', '')}"
        quote = self.foundation_quote("media", "renewal", str(offer.get("id", "")), amount=int(offer.get("fee", 0) or 0), details={
            "predecessor_id": offer.get("predecessor_id", ""), "start_trigger": "After predecessor completes",
            "overlap": False,
        }) if hasattr(self, "foundation_quote") else None

        def validate():
            return bool(self.active_media_contract(promotion))

        def apply():
            successor = dict(offer)
            successor["status"] = "Pending"
            successor["accepted_month"] = int(self.month)
            successor["start_trigger"] = "After predecessor completes"
            finance["media_successor_contract"] = successor
            finance["media_successor_offer"] = None
            return {"name": successor.get("name", "Rights partner"), "predecessor_id": successor.get("predecessor_id", "")}

        if hasattr(self, "foundation_commit"):
            receipt = self.foundation_commit(operation_key, domain="media", action="accept_renewal", target_id=str(offer.get("id", "")), quote=quote, validate=validate, apply=apply)
            result = receipt.get("result") if isinstance(receipt, dict) else None
            return receipt.get("status") == "committed", (f"Queued renewal with {result.get('name', 'the outlet')}; it starts after the current deal completes." if result else receipt.get("error", "Renewal was not accepted.")), result
        result = apply()
        return True, f"Queued renewal with {result['name']}; it starts after the current deal completes.", result

    def reject_media_renewal_offer(self, promotion=None):
        finance = self._ensure_media_state(promotion)
        offer = finance.get("media_successor_offer")
        if not isinstance(offer, dict) or offer.get("status") != "Offer":
            return False, "There is no live renewal offer to reject.", None
        offer["status"] = "Rejected"
        finance["media_successor_offer"] = None
        finance.setdefault("media_offer_history", []).insert(0, {
            **dict(offer), "decision": "Renewal rejected", "month": int(self.month),
        })
        finance["media_offer_history"] = finance["media_offer_history"][:40]
        return True, f"Rejected the renewal offer from {offer.get('name', 'the outlet')}.", dict(offer)

    def counter_media_renewal_offer(self, promotion=None, stance="Higher Guarantee", roll=None):
        """Allow exactly one injected/testable counter on a queued renewal."""
        finance = self._ensure_media_state(promotion)
        offer = finance.get("media_successor_offer")
        if not isinstance(offer, dict) or offer.get("status") != "Offer":
            return False, "Prepare a live renewal offer before countering it.", None
        valid_stances = ("Higher Guarantee", "Wider Reach", "Lower Standards", "Shorter Commitment")
        stance = stance if stance in valid_stances else "Higher Guarantee"
        operation_key = f"media-renewal-counter:{offer.get('id', '')}"
        quote = self.foundation_quote("media", "renewal_counter", str(offer.get("id", "")), amount=int(offer.get("fee", 0) or 0), details={"stance": stance, "one_counter": True}) if hasattr(self, "foundation_quote") else None
        if hasattr(self, "foundation_get_receipt"):
            prior = self.foundation_get_receipt(operation_key)
            if prior and prior.get("status") != "failed":
                result = prior.get("result") or {}
                return result.get("status") == "Accepted", result.get("message", "Renewal counter already resolved."), result
        if offer.get("negotiated"):
            return False, "This renewal offer has already answered one counteroffer.", None

        def apply():
            chance = max(18, min(88, round(28 + offer.get("relationship", 50) * .35 + self._media_company_values(promotion)[2] * .18 + self._media_company_values(promotion)[3] * .12 + offer.get("market_score", 0) * .12)))
            offer["negotiated"] = True
            actual_roll = random.randint(1, 100) if roll is None else int(roll)
            if actual_roll <= chance:
                if stance == "Higher Guarantee":
                    offer["fee"] = round(int(offer.get("fee", 0)) * 1.12 / 1000) * 1000
                elif stance == "Wider Reach":
                    offer["reach"] = min(99, int(offer.get("reach", 0)) + 5)
                elif stance == "Lower Standards":
                    offer["minimum_rating"] = max(20, int(offer.get("minimum_rating", 0)) - 5)
                    offer["min_card_quality"] = max(20, int(offer.get("min_card_quality", 0)) - 4)
                else:
                    offer["months"] = max(6, int(offer.get("months", 0)) - 4)
                    offer["events_total"] = max(4, int(offer.get("events_total", 0)) - 2)
                    offer["events_remaining"] = offer["events_total"]
                offer["guarantee_per_event"] = offer.get("fee", offer.get("guarantee_per_event", 0))
                offer.setdefault("terms_version", 1)
                offer.setdefault("production_tier", self.media_contract_terms(offer).get("production_tier", "Standard"))
                return {"status": "Accepted", "message": f"{offer.get('name', 'The outlet')} accepted your {stance.lower()} renewal counteroffer.", "roll": actual_roll, "chance": chance}
            offer["status"] = "Withdrawn"
            finance.setdefault("media_offer_history", []).insert(0, {**offer, "decision": "Renewal counter declined", "month": self.month})
            finance["media_successor_offer"] = None
            return {"status": "Withdrawn", "message": f"{offer.get('name', 'The outlet')} rejected the renewal counter and withdrew the offer.", "roll": actual_roll, "chance": chance}

        if hasattr(self, "foundation_commit"):
            receipt = self.foundation_commit(operation_key, domain="media", action="renewal_counter", target_id=str(offer.get("id", "")), quote=quote, validate=lambda: bool(finance.get("media_successor_offer")), apply=apply)
            result = receipt.get("result") or {}
            return result.get("status") == "Accepted", result.get("message", receipt.get("error", "Renewal counter was not resolved.")), result
        result = apply()
        return result["status"] == "Accepted", result["message"], result

    def media_contract_eligibility(self, contract, event, promotion=None):
        """Return whether a saved rights package can cover ``event``.

        This helper sits on the settlement boundary, so malformed legacy
        numbers must fail closed instead of bubbling a ``TypeError`` through
        card execution.  The original valid-value semantics are unchanged;
        only the malformed path gains an explicit, reviewable reason.
        """
        if not isinstance(contract, dict):
            return False, "Contract inactive or fully delivered"
        event = event if isinstance(event, dict) else {}

        def positive_int(value):
            if isinstance(value, bool) or value is None or value == "":
                return 0
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return 0

        if contract.get("status") != "Active" or positive_int(contract.get("months", 0)) <= 0 or positive_int(contract.get("events_remaining", 0)) <= 0:
            return False, "Contract inactive or fully delivered"
        if str(event.get("broadcaster", "No Coverage")) == "No Coverage":
            return False, "No event production provider selected"
        outlet = self._outlet_for(contract.get("outlet_id"))
        region = event.get("region", self._media_company_values(promotion)[1])
        if outlet and region not in outlet.get("markets", []) and "Worldwide" not in outlet.get("markets", []):
            return False, f"Outside {outlet['name']}'s territories"
        return True, "Eligible for contracted coverage"

    def eligible_media_contracts(self, event, promotion=None):
        finance = self._ensure_media_state(promotion)
        return [item for item in finance["media_contracts"] if self.media_contract_eligibility(item, event, promotion)[0]]

    def _media_action_spec(self, action, fighter=None, *, promotion=None):
        specs = {
            "Interview": (1, 0, 7, 8), "Call Out": (1, 0, 11, 22),
            "Press Tour": (2, 12_000 + max(0, getattr(fighter, "popularity", 40) - 40) * 200, 18, 12),
            "Open Workout": (1, 4_000, 9, 7), "Highlight Package": (1, 7_500, 12, 5),
            "Press Conference": (1, 6_000, 13, 16), "Regional Tour": (2, 14_000, 16, 8),
            "Crisis Response": (1, 9_000, 2, 4),
        }
        points, cost, heat, risk = specs.get(action, specs["Interview"])
        # Quote and settlement both flow through this pure spec, so the
        # Campaign Coordinator effect cannot make the preview disagree with
        # the eventual charge.  Free appearances remain free.
        base_cost = cost
        reduction = 0
        # ``promotion`` identifies an AI/child promotion resolver.  Its staff
        # roster is not the player's staff, so never leak a player specialty
        # saving into another company's campaign quote.
        reduction_fn = getattr(self, "staff_specialty_cost_reduction", None) if promotion is None else None
        if cost > 0 and callable(reduction_fn):
            reduction = reduction_fn("Marketing", cost, cost_type="media_campaign")
            cost = max(0, cost - reduction)
        return {
            "points": points, "cost": cost, "heat": heat, "risk": risk,
            "base_cost": base_cost, "staff_cost_saving": reduction,
        }

    def media_action_preview(self, action, fighter=None):
        spec = self._media_action_spec(action, fighter)
        target_note = " Same-division target required." if action == "Call Out" else ""
        # ``risk`` is an authored exposure score, not a calibrated probability.
        exposure = "Low" if spec["risk"] <= 6 else "Moderate" if spec["risk"] <= 12 else "High"
        saving_note = f" Campaign Coordinator saving ${spec['staff_cost_saving']:,}." if spec.get("staff_cost_saving") else ""
        return f"{spec['points']} action point(s) | Cost ${spec['cost']:,} | Base heat {spec['heat']} | Exposure {exposure}.{saving_note}{target_note}"

    # ----- M1: optional, target-aware campaign plan -----------------------
    # A plan is an organisational record around the existing campaign
    # resolver.  It intentionally does not change the resolver's economics.
    MEDIA_PLAN_OBJECTIVES = (
        "Event Promotion", "Prospect Exposure", "Sponsor Duty",
        "Regional Work", "Trust Repair",
    )

    def _media_plan_event_rows(self):
        """Return scheduled event dictionaries without changing simulation state."""
        getter = getattr(self, "sorted_scheduled_events", None)
        rows = getter() if callable(getter) else list(getattr(self, "scheduled_events", []) or [])
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _media_plan_disambiguate_options(options):
        """Add deterministic selector labels without changing source labels/IDs."""
        rows = [dict(row) for row in options if isinstance(row, dict)]
        label_counts = {}
        id_counts = {}
        for row in rows:
            label = str(row.get("label", row.get("id", "")) or "")
            source_id = str(row.get("id", "") or "")
            label_counts[label] = label_counts.get(label, 0) + 1
            id_counts[source_id] = id_counts.get(source_id, 0) + 1
        for row in rows:
            label = str(row.get("label", row.get("id", "")) or "")
            source_id = str(row.get("id", "") or "")
            duplicate_id = not source_id or id_counts.get(source_id, 0) != 1
            row["selectable"] = not duplicate_id
            if duplicate_id:
                suffix = "identity unavailable" if not source_id else "duplicate identity"
                row["display_label"] = f"{label} [{suffix}]"
            elif label_counts.get(label, 0) > 1:
                snapshot = row.get("snapshot", {}) if isinstance(row.get("snapshot", {}), dict) else {}
                context = str(snapshot.get("date", "") or snapshot.get("weight", "") or snapshot.get("category", "") or "").strip()
                short_id = source_id if len(source_id) <= 18 else source_id[-12:]
                qualifier = f"{context}; {short_id}" if context else short_id
                row["display_label"] = f"{label} [{qualifier}]"
            else:
                row["display_label"] = label
        return rows

    @staticmethod
    def _media_plan_target_by_id(options, target_id):
        """Resolve exactly one selectable plan target by its durable source ID."""
        target_id = str(target_id or "")
        matches = [row for row in options if str(row.get("id", "") or "") == target_id and row.get("selectable", True)]
        return matches[0] if target_id and len(matches) == 1 else None

    def media_plan_target_options(self, objective, *, migrate=True):
        """Build display options for the plan editor from current identities."""
        if migrate and hasattr(self, "ensure_foundation_ids"):
            # Event targets must use the same durable IDs as settlement and
            # receipts.  This migration is deterministic and RNG-free.
            self.ensure_foundation_ids()
        objective = str(objective or "")
        if objective == "Event Promotion":
            options = [
                {"id": str(row.get("event_id", "") or row.get("id", "") or row.get("name", "")),
                 "label": str(row.get("name", row.get("event_name", "Event"))),
                 "kind": "event", "snapshot": {"name": row.get("name", row.get("event_name", "Event")),
                                                   "date": row.get("date", "") or f"M{row.get('month', '?')} W{row.get('week', '?')}"}}
                for row in self._media_plan_event_rows()
            ]
        elif objective == "Prospect Exposure":
            options = [{"id": str(getattr(fighter, "fighter_id", "") or fighter.name), "label": fighter.name,
                        "kind": "fighter", "snapshot": {"name": fighter.name, "weight": fighter.weight}}
                       for fighter in getattr(self, "roster", []) if not getattr(fighter, "retired", False)]
        elif objective == "Regional Work":
            options = [{"id": str(region), "label": str(region), "kind": "region", "snapshot": {"region": str(region)}}
                       for region in REGIONS]
        elif objective == "Sponsor Duty":
            if migrate:
                deals = self._ensure_media_state().get("sponsor_deals", [])
            else:
                raw_finance = getattr(self, "finance", {})
                deals = raw_finance.get("sponsor_deals", []) if isinstance(raw_finance, dict) else []
            options = [{"id": str(deal.get("id", "") or deal.get("name", "Sponsor")), "label": str(deal.get("name", "Sponsor")),
                        "kind": "sponsor", "snapshot": {"name": deal.get("name", "Sponsor"), "category": deal.get("category", "")}}
                       for deal in deals if isinstance(deal, dict)]
        else:
            # Trust repair is linked to the company rather than an invented
            # person or event.  The existing resolver remains authoritative.
            options = [{"id": "company-trust", "label": str(getattr(self, "player_company_name", "Company")),
                        "kind": "company", "snapshot": {"name": getattr(self, "player_company_name", "Company")}}]
        return self._media_plan_disambiguate_options(options)

    def media_plan_quote(self, objective, target_id="", action="Interview", fighter=None, *, region=""):
        """Pure quote for the plan editor; no offer, RNG or cooldown mutation."""
        objective = str(objective or "")
        action = str(action or "Interview")
        target_id = str(target_id or "")
        current = self.media_plan_target_choice.get() if hasattr(self, "media_plan_target_choice") else ""
        selected_source_id = str(getattr(self, "_media_plan_target_map", {}).get(current, "") or "")
        options = self.media_plan_target_options(objective, migrate=False)
        target = self._media_plan_target_by_id(options, target_id)
        spec = self._media_action_spec(action, fighter)
        allowed = {
            "Event Promotion": ("Press Tour", "Press Conference", "Interview", "Highlight Package"),
            "Prospect Exposure": ("Interview", "Open Workout", "Highlight Package", "Press Tour"),
            "Sponsor Duty": ("Interview", "Press Tour", "Highlight Package", "Open Workout"),
            "Regional Work": ("Regional Tour", "Open Workout", "Interview"),
            "Trust Repair": ("Crisis Response", "Press Conference", "Interview"),
        }.get(objective, (action,))
        return self.foundation_quote("media", "campaign_plan_quote", target_id, amount=spec["cost"], details={
            "objective": objective, "action": action, "allowed_actions": list(allowed),
            "target_found": bool(target), "target_label": target.get("label", "") if target else "",
            "action_points": spec["points"], "remaining_points": self.media_actions_remaining_readonly(),
            "region": str(region or getattr(self, "player_region", "")),
            "uncertainty": "Existing campaign outcome roll; no plan bonus is applied.",
        }) if hasattr(self, "foundation_quote") else {
            "domain": "media", "action": "campaign_plan_quote", "target_id": target_id,
            "amount": spec["cost"], "details": {"objective": objective, "action": action, "allowed_actions": list(allowed)},
        }

    def create_media_campaign_plan(self, objective, target_id="", *, action_ids=None, spend_ceiling=0, deadline=None, staff_id=""):
        """Create/replace the one optional primary plan. Creation has no gameplay effect."""
        finance = self.ensure_player_media_state()
        objective = str(objective or "")
        if objective not in self.MEDIA_PLAN_OBJECTIVES:
            return False, "Choose a recognised campaign objective.", None
        options = self.media_plan_target_options(objective)
        target = self._media_plan_target_by_id(options, target_id)
        if target is None:
            return False, "Choose a current target before saving the plan.", None
        previous = finance.get("media_primary_plan")
        sequence = int(finance.get("media_plan_sequence", 0) or 0) + 1
        finance["media_plan_sequence"] = sequence
        allowed_by_objective = {
            "Event Promotion": ("Press Tour", "Press Conference", "Interview", "Highlight Package"),
            "Prospect Exposure": ("Interview", "Open Workout", "Highlight Package", "Press Tour"),
            "Sponsor Duty": ("Interview", "Press Tour", "Highlight Package", "Open Workout"),
            "Regional Work": ("Regional Tour", "Open Workout", "Interview"),
            "Trust Repair": ("Crisis Response", "Press Conference", "Interview"),
        }.get(objective, ("Interview",))
        allowed = [str(value) for value in (action_ids or ("Interview",)) if str(value) in allowed_by_objective]
        if not allowed:
            allowed = [allowed_by_objective[0]]
        plan = {
            "schema_version": 1, "plan_id": f"media-plan-{self.month}-{self.week}-{sequence}",
            "objective": objective, "target_id": target["id"], "target_kind": target.get("kind", ""),
            "target_snapshot": dict(target.get("snapshot", {})), "target_label": target.get("label", ""),
            "responsible_staff_id": str(staff_id or ""), "spend_ceiling": max(0, int(spend_ceiling or 0)),
            "allowed_action_ids": allowed, "deadline": dict(deadline or {}), "status": "Draft",
            "revision": 1, "action_receipts": [], "created_month": int(self.month),
            "created_week": int(self.week), "updated_month": int(self.month), "updated_week": int(self.week),
        }
        if previous:
            finance.setdefault("media_plan_history", []).insert(0, dict(previous, status="Replaced"))
        finance["media_primary_plan"] = plan
        finance["media_plan_history"] = finance.get("media_plan_history", [])[:60]
        return True, f"Saved {objective.lower()} plan for {plan['target_label']}. It organises existing actions; no bonus is active.", dict(plan)

    def retarget_media_campaign_plan(self, target_id):
        finance = self.ensure_player_media_state()
        plan = finance.get("media_primary_plan")
        if not isinstance(plan, dict) or plan.get("status") in ("Cancelled", "Completed", "Replaced"):
            return False, "There is no active campaign plan to retarget.", None
        target = self._media_plan_target_by_id(self.media_plan_target_options(plan.get("objective", "")), target_id)
        if target is None:
            return False, "That target is no longer available. Review the plan before committing work.", None
        plan.update({"target_id": target["id"], "target_kind": target.get("kind", ""), "target_snapshot": dict(target.get("snapshot", {})),
                     "target_label": target.get("label", ""), "revision": int(plan.get("revision", 0) or 0) + 1,
                     "updated_month": int(self.month), "updated_week": int(self.week)})
        return True, f"Retargeted the plan to {plan['target_label']}. Existing completed work remains unchanged.", dict(plan)

    def cancel_media_campaign_plan(self):
        finance = self.ensure_player_media_state()
        plan = finance.get("media_primary_plan")
        if not isinstance(plan, dict) or plan.get("status") in ("Cancelled", "Completed", "Replaced"):
            return False, "There is no active campaign plan to cancel.", None
        plan["status"] = "Cancelled"
        plan["revision"] = int(plan.get("revision", 0) or 0) + 1
        plan["updated_month"], plan["updated_week"] = int(self.month), int(self.week)
        finance.setdefault("media_plan_history", []).insert(0, dict(plan))
        finance["media_plan_history"] = finance["media_plan_history"][:60]
        return True, f"Cancelled the {plan.get('objective', 'campaign').lower()} plan. No action was run.", dict(plan)

    @staticmethod
    def media_plan_recorded_spend(plan):
        """Return (known spend, issue) from immutable plan action evidence."""
        if not isinstance(plan, dict):
            return None, "campaign plan is unavailable"
        receipts = plan.get("action_receipts", [])
        if not isinstance(receipts, (list, tuple)):
            return None, "recorded campaign spend is malformed"
        total = 0
        for receipt in receipts:
            if not isinstance(receipt, dict):
                return None, "recorded campaign spend contains an invalid receipt"
            outcome = receipt.get("outcome")
            if not isinstance(outcome, dict) or "cost" not in outcome:
                return None, "recorded campaign spend is incomplete"
            value = outcome.get("cost")
            if isinstance(value, bool) or value is None or isinstance(value, float) and not math.isfinite(value):
                return None, "recorded campaign spend contains an invalid amount"
            try:
                amount = int(value)
            except (TypeError, ValueError, OverflowError):
                return None, "recorded campaign spend contains an invalid amount"
            if amount < 0:
                return None, "recorded campaign spend contains an invalid amount"
            total += amount
        return total, ""

    def execute_media_campaign_plan(self, action, fighter, target=None, *, region=""):
        """Commit one allowed existing action and attach immutable plan evidence."""
        finance = self.ensure_player_media_state()
        plan = finance.get("media_primary_plan")
        if not isinstance(plan, dict) or plan.get("status") in ("Cancelled", "Completed", "Replaced"):
            return False, "Create an active campaign plan before committing managed work.", None
        action = str(action or "Interview")
        if action not in set(plan.get("allowed_action_ids", [])):
            return False, f"{action} is not enabled for this plan. Edit the allowed actions first.", None
        options = self.media_plan_target_options(plan.get("objective", ""))
        if self._media_plan_target_by_id(options, plan.get("target_id")) is None:
            return False, "The plan target changed or left the game. Retarget it before committing work.", None
        fighter_id = str(getattr(fighter, "fighter_id", "") or getattr(fighter, "name", ""))
        target_id = str(getattr(target, "fighter_id", "") or getattr(target, "name", "") if target else "")
        marker = f"{self.month}:{self.week}:{action}:{fighter_id}:{target_id}"
        operation_key = f"media-plan:{plan.get('plan_id', 'unassigned')}:{marker}"
        quote = self.media_plan_quote(plan.get("objective", ""), plan.get("target_id", ""), action, fighter, region=region)
        if hasattr(self, "foundation_get_receipt"):
            prior = self.foundation_get_receipt(operation_key)
            if prior and prior.get("status") != "failed":
                return prior.get("status") == "committed", str((prior.get("result") or {}).get("text", prior.get("error", "Work already reviewed."))), prior.get("result")

        def validate():
            try:
                ceiling = int(plan.get("spend_ceiling", 0) or 0)
                quoted = int(quote.get("amount", 0) or 0)
            except (TypeError, ValueError, OverflowError):
                return False, "The plan spending limit or quoted cost is unavailable. Review the plan before committing work."
            if ceiling < 0 or quoted < 0:
                return False, "The plan spending limit or quoted cost is unavailable. Review the plan before committing work."
            if not ceiling:
                return True
            spent, issue = self.media_plan_recorded_spend(plan)
            if spent is None:
                return False, f"{issue.capitalize()}. Review the plan before committing paid work."
            if spent + quoted > ceiling:
                return False, "This action would exceed the plan's spend ceiling."
            return True

        def apply():
            ok, text, row = self.resolve_media_campaign(action, fighter, target, region=region)
            if not ok:
                raise ValueError(text)
            evidence_key = f"campaign-evidence:{plan['plan_id']}:{len(plan.get('action_receipts', [])) + 1}"
            row["plan_id"], row["evidence_key"], row["plan_objective"] = plan["plan_id"], evidence_key, plan.get("objective", "")
            plan.setdefault("action_receipts", []).append({"evidence_key": evidence_key, "action": action, "target_id": plan.get("target_id", ""), "outcome": dict(row)})
            plan["status"] = "Active"
            plan["revision"] = int(plan.get("revision", 0) or 0) + 1
            plan["updated_month"], plan["updated_week"] = int(self.month), int(self.week)
            return {"text": text, "evidence_key": evidence_key, "row": dict(row)}

        if hasattr(self, "foundation_commit"):
            receipt = self.foundation_commit(operation_key, domain="media", action="campaign_plan_commit", target_id=plan.get("target_id", ""), quote=quote, validate=validate, apply=apply)
            result = receipt.get("result") if isinstance(receipt, dict) else None
            return receipt.get("status") == "committed", str((result or {}).get("text", receipt.get("error", "Campaign work was not committed."))), result
        try:
            if validate() is not True:
                return False, "This action would exceed the plan's spend ceiling.", None
            result = apply()
            return True, result["text"], result
        except Exception as exc:
            return False, str(exc), None

    def resolve_media_campaign(self, action, fighter, target=None, region=None, promotion=None):
        if not fighter:
            return False, "Choose a spokesperson first.", None
        finance = self._ensure_media_state(promotion)
        spec = self._media_action_spec(action, fighter, promotion=promotion)
        remaining = self.media_actions_remaining(promotion)
        if remaining < spec["points"]:
            return False, f"Only {remaining} media action point(s) remain this week.", None
        if action == "Call Out" and (not target or target is fighter or target.gender != fighter.gender or target.weight != fighter.weight):
            return False, "Callouts require a different fighter in the same division.", None
        rivalry_target = None
        if action in ("Press Conference", "Press Tour") and getattr(fighter, "rival", ""):
            resolver = getattr(self, "resolve_rivalry_target", None)
            rivalry_target = resolver(fighter) if resolver else None
            if rivalry_target is None:
                return False, "That rivalry reference is missing or ambiguous. Repair it before promoting the feud.", None
        company_name, company_region, _pop, _stability, cash, _roster = self._media_company_values(promotion)
        if cash < spec["cost"]:
            return False, f"This campaign costs ${spec['cost']:,}.", None
        marker = (self.month - 1) * 4 + self.week
        fighter_identity = getattr(fighter, "fighter_id", "") or fighter.name
        target_identity = getattr(target, "fighter_id", "") or getattr(target, "name", "")
        fighter_key = f"fighter:{fighter_identity}"
        pair_key = f"callout:{fighter_identity}:{target_identity}"
        cooldowns = finance["media_campaign_cooldowns"]
        if cooldowns.get(fighter_key, -99) >= marker:
            return False, f"{fighter.name} has already completed a media appearance this week.", None
        if action == "Call Out" and cooldowns.get(pair_key, -99) > marker:
            return False, "That rivalry callout is still on a four-week cooldown.", None
        if promotion is None:
            self.cash -= spec["cost"]
            if spec["cost"]:
                self.record_finance_transaction(
                    f"Media campaign: {action}", costs=spec["cost"], category="Media",
                    source="Media desk", counterparty=getattr(fighter, "name", ""),
                    reference=f"media-campaign:{self.month}:{self.week}:{action}:{fighter_identity}",
                )
            marketing = self.staff_skill("Marketing") if hasattr(self, "staff_skill") else 45
        else:
            promotion.cash -= spec["cost"]
            if spec["cost"] and hasattr(self, "record_promotion_finance_transaction"):
                self.record_promotion_finance_transaction(
                    promotion, f"Media campaign: {action}", costs=spec["cost"], category="Media",
                    source="Media desk", counterparty=getattr(fighter, "name", ""),
                    reference=f"media-campaign:{promotion.name}:{self.month}:{self.week}:{action}:{fighter_identity}",
                )
            marketing = int((promotion.strategy or {}).get("commercial_strength", promotion.size))
        strategy = finance.get("media_strategy", "Balanced")
        strategy_bonus = {
            "Sporting Credibility": 7 if action in ("Interview", "Open Workout", "Highlight Package") else -2,
            "Star Builder": 7 if fighter.popularity >= 55 else 1,
            "Viral Growth": 9 if action in ("Call Out", "Press Conference") else -1,
            "Regional Expansion": 8 if action in ("Regional Tour", "Open Workout") else 0,
            "Sponsor Friendly": 7 if action in ("Interview", "Highlight Package") else -4 if action == "Call Out" else 0,
            "Crisis Management": 12 if action == "Crisis Response" else -1,
        }.get(strategy, 3)
        score = fighter.media_presence * 0.32 + fighter.charisma * 0.25 + fighter.popularity * 0.17 + fighter.professionalism * 0.13 + marketing * 0.13 + strategy_bonus + random.randint(-22, 22)
        if action == "Crisis Response":
            score += fighter.professionalism * 0.12
        if score >= 86:
            band, multiplier, trust_delta = "Viral", 1.55, 3
        elif score >= 70:
            band, multiplier, trust_delta = "Strong", 1.22, 2
        elif score >= 52:
            band, multiplier, trust_delta = "Routine", 0.9, 1
        elif score >= 38:
            band, multiplier, trust_delta = "Flat", 0.35, -1
        else:
            band, multiplier, trust_delta = "Backlash", -0.45, -4
        heat_delta = round(spec["heat"] * multiplier)
        if action == "Crisis Response":
            heat_delta = max(-4, min(4, heat_delta))
            trust_delta += 4 if band in ("Viral", "Strong") else 1
        fighter.media_heat = max(0, min(100, fighter.media_heat + heat_delta))
        pop_key = f"{self.month}:{fighter.name}"
        gained = int(finance["media_popularity_month"].get(pop_key, 0))
        pop_delta = 1 if band in ("Viral", "Strong") and gained < 3 else (-1 if band == "Backlash" and fighter.popularity > 10 else 0)
        fighter.popularity = max(1, min(100, fighter.popularity + pop_delta))
        finance["media_popularity_month"][pop_key] = max(0, gained + max(0, pop_delta))
        finance["media_public_trust"] = max(0, min(100, finance.get("media_public_trust", 55) + trust_delta))
        finance["media_company_buzz"] = max(0, min(100, finance.get("media_company_buzz", 20) + round(heat_delta / 2)))
        finance["media_actions_used"] += spec["points"]
        cooldowns[fighter_key] = marker
        if action == "Call Out":
            cooldowns[pair_key] = marker + 4
            existing_heat = self.rivalry_heat_between(fighter, target) if hasattr(self, "rivalry_heat_between") else 0
            if existing_heat and hasattr(self, "build_rivalry_heat"):
                # Calling out an existing rival escalates the feud rather than
                # resetting it, so a grudge can be built over several weeks.
                self.build_rivalry_heat(
                    fighter, target, max(4, 8 + heat_delta // 2),
                    note=f"{fighter.name} escalated the feud with {target.name} in the media.",
                )
            elif hasattr(self, "establish_rivalry"):
                try:
                    self.establish_rivalry(fighter, target, origin="Media callout", heat=max(35, 45 + heat_delta))
                except TypeError:
                    fighter.rival, target.rival = target.name, fighter.name
                    fighter.rival_fighter_id = getattr(target, "fighter_id", "")
                    target.rival_fighter_id = getattr(fighter, "fighter_id", "")
            else:
                fighter.rival, target.rival = target.name, fighter.name
                fighter.rival_fighter_id = getattr(target, "fighter_id", "")
                target.rival_fighter_id = getattr(fighter, "fighter_id", "")
            target.media_heat = max(0, min(100, target.media_heat + max(2, heat_delta // 2)))
        elif action in ("Press Conference", "Press Tour") and hasattr(self, "build_rivalry_heat"):
            # Promoting a fighter who is already in a feud builds that feud too.
            if rivalry_target is not None and self.rivalry_heat_between(fighter, rivalry_target):
                self.build_rivalry_heat(
                    fighter, rivalry_target, max(2, 4 + heat_delta // 3),
                    note=f"{fighter.name}'s {action.lower()} kept the feud with {rivalry_target.name} in the headlines.",
                )
        subject = fighter.name
        target_name = target.name if target else (region or company_region if action == "Regional Tour" else "")
        from narrative_presentation import media_voice
        outcome_text = media_voice(fighter, action, band, target_name)
        if action == "Call Out" and target:
            outcome_text += (" The callout adds personal tension, but publicity does not establish a sporting case for a rematch."
                             if band == "Backlash" else
                             " The challenge adds rivalry tension; a return fight still needs a credible sporting case.")
        elif action in ("Press Conference", "Press Tour") and rivalry_target is not None:
            outcome_text += " Keeping the feud in public view can increase tension even when the campaign fails to impress."
        outcome_text += f"\n\nCampaign effects: {band}; {heat_delta:+} media heat, {pop_delta:+} popularity, {trust_delta:+} public trust."
        row = {"date": f"M{self.month} W{self.week}", "month": self.month, "week": self.week, "strategy": strategy, "action": action, "subject": subject, "target": target_name, "outcome": outcome_text, "band": band, "heat": heat_delta, "popularity": pop_delta, "trust": trust_delta, "cost": spec["cost"]}
        finance["media_campaign_history"].insert(0, row)
        finance["media_campaign_history"] = finance["media_campaign_history"][:60]
        if promotion is None:
            response = {"Viral": "breaks into wider attention", "Strong": "connects with the audience",
                        "Routine": "keeps their name in circulation", "Flat": "struggles for attention",
                        "Backlash": "draws backlash"}.get(band, "reaches its audience")
            headline = f"{fighter.name}'s {action.lower()} {response}."
            self.news.insert(0, headline)
            if hasattr(self, "record_world_story"):
                self.record_world_story("Media", headline, outcome_text, [company_name], [fighter.name] + ([target.name] if target else []), 3 if band in ("Viral", "Backlash") else 2)
            if spec["cost"]:
                finance.setdefault("ledger", []).insert(0, f"Month {self.month}: {action} campaign for {fighter.name} cost ${spec['cost']:,}.")
        return True, outcome_text, row

    def update_media_market(self):
        self.ensure_media_system()
        if self.media_market_last_month == self.month:
            return
        self.media_market_last_month = self.month
        changes = []
        for outlet in self.media_companies:
            if not isinstance(outlet, dict) or not outlet.get("active", True):
                continue
            def safe_int(value, fallback=None):
                if isinstance(value, bool) or value is None or value == "":
                    return fallback
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return fallback

            raw_volatility = outlet.get("volatility", 15)
            raw_budget = outlet.get("budget", 50)
            raw_base_fee = outlet.get("base_fee", 10_000)
            volatility_value = safe_int(raw_volatility, None)
            budget_value = safe_int(raw_budget, None)
            base_fee_value = safe_int(raw_base_fee, None)
            malformed = []
            if volatility_value is None:
                malformed.append("volatility")
                volatility_value = 15
            if budget_value is None:
                malformed.append("budget")
                budget_value = 50
            if base_fee_value is None:
                malformed.append("base_fee")
                base_fee_value = 10_000
            if malformed:
                # Market refresh is a gameplay mutation, but it must not
                # overwrite an untrusted legacy outlet field with a guessed
                # value. Keep the raw evidence and make the row reviewable.
                outlet.setdefault("market_review_required", True)
                outlet.setdefault(
                    "market_review_reason",
                    "Malformed saved market fields: " + ", ".join(malformed),
                )
            volatility = max(3, min(100, volatility_value))
            budget_change = random.choice([-1, 0, 0, 0, 1]) if random.randint(1, 100) > volatility else random.choice([-3, -2, 2, 3])
            if "budget" not in malformed:
                outlet["budget"] = max(10, min(99, budget_value + budget_change))
            if "base_fee" not in malformed:
                outlet["base_fee"] = max(4_000, round(base_fee_value * (1 + budget_change / 250)))
            if abs(budget_change) >= 3:
                changes.append(f"{outlet.get('name', 'Unnamed outlet')} budget {'rose' if budget_change > 0 else 'fell'}")
        active_outlets = [o for o in self.media_companies if isinstance(o, dict) and o.get("active", True)]
        budgets = [safe_int(o.get("budget"), 0) or 0 for o in active_outlets]
        snapshot = {"month": self.month, "active_outlets": len(active_outlets), "average_budget": round(sum(budgets) / max(1, len(budgets))), "changes": changes[:4]}
        self.media_market_history.insert(0, snapshot)
        self.media_market_history = self.media_market_history[:120]

    def review_ai_media_deals(self, promo):
        finance = self.ensure_ai_media_state(promo)
        active = self.active_media_contract(promo)
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback

        if (active and safe_int(active.get("months", 0), 0) > 0 and
                safe_int(active.get("events_remaining", 0), 0) > 0):
            return active
        offers = self.generate_media_offers(promo, force=not finance.get("media_offers"), count=4)
        if not offers:
            return active
        valid_offers = []
        malformed_offer_ids = []
        for offer in offers if isinstance(offers, list) else []:
            if not isinstance(offer, dict) or not str(offer.get("id", "") or ""):
                malformed_offer_ids.append(str(offer.get("id", "") or "legacy") if isinstance(offer, dict) else "legacy")
                continue
            numeric = {
                field: safe_int(offer.get(field), None)
                for field in ("fee", "reach", "min_card_quality", "months", "events_total")
            }
            if any(value is None for value in numeric.values()) or numeric["months"] <= 0 or numeric["events_total"] <= 0:
                malformed_offer_ids.append(str(offer.get("id")))
                continue
            valid_offers.append(offer)
        if malformed_offer_ids:
            # Preserve malformed offers for an explicit migration/review
            # boundary; AI must not silently discard them or treat raw strings
            # as spendable contract terms.
            finance.setdefault("media_offer_review_required", True)
            finance.setdefault("media_offer_review_ids", list(malformed_offer_ids))
            finance.setdefault("media_offer_review_reason", "One or more saved media offers have malformed terms.")
        if not valid_offers:
            return active
        strategy = getattr(promo, "strategy", {})
        mode = strategy.get("current_mode", "Balanced") if isinstance(strategy, dict) else "Balanced"
        promo_size = max(1, safe_int(getattr(promo, "size", 1), 1))
        reputation_score = safe_int(getattr(promo, "reputation_score", 0), 0)
        def value(offer):
            fee = safe_int(offer.get("fee"), 0)
            reach = safe_int(offer.get("reach"), 0)
            minimum_quality = safe_int(offer.get("min_card_quality"), 0)
            affordability = fee / max(1, promo_size * 1500)
            reach_weight = 1.5 if mode in ("Star Chasing", "Title Push") else 0.9
            security = 1.3 if mode == "Financial Recovery" else 1.0
            standards_risk = max(0, minimum_quality - reputation_score) * 3
            return reach * reach_weight + fee / 6000 * security - standards_risk - affordability
        choice = max(valid_offers, key=value)
        ok, _message = self._accept_media_offer(choice["id"], promo)
        return self.active_media_contract(promo) if ok else active

    def process_media_month(self):
        self.ensure_media_system()
        self.update_media_market()
        self.review_sponsor_duties()
        if not getattr(self, "spectator_mode", False):
            finance = self.ensure_player_media_state()
            self.expire_media_offers()
            if not finance["media_offers"] or self.month - finance.get("media_last_offer_month", 0) >= 3:
                self.generate_media_offers(force=True)
        for promo in self.promotions:
            finance = self.ensure_ai_media_state(promo)
            self.expire_media_offers(promo)
            self.review_ai_media_deals(promo)
            if promo.roster and random.random() < 0.42:
                candidates = [f for f in promo.roster if not f.retired and not f.injured]
                if candidates:
                    voice = (promo.strategy or {}).get("media_voice", "Reliable fights").lower()
                    action = "Call Out" if "spectacle" in voice and random.random() < 0.35 else ("Highlight Package" if "future" in voice or "prospect" in voice else "Interview")
                    fighter = max(random.sample(candidates, k=min(6, len(candidates))), key=lambda f: f.media_presence + f.popularity)
                    target = next((f for f in candidates if f is not fighter and f.gender == fighter.gender and f.weight == fighter.weight), None) if action == "Call Out" else None
                    if action != "Call Out" or target:
                        self.resolve_media_campaign(action, fighter, target, promotion=promo)
        # Contract terms count down once here. The old business tick skips the
        # legacy alias when media_contracts exists, preventing double expiry.
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback

        for promotion in [None] + list(self.promotions):
            finance = self._ensure_media_state(promotion)
            contracts = finance.get("media_contracts", [])
            if not isinstance(contracts, list):
                contracts = []
            for contract in contracts:
                if not isinstance(contract, dict):
                    continue
                if contract.get("status") != "Active":
                    continue
                months = safe_int(contract.get("months", 0), None)
                if months is None:
                    # Hold malformed legacy terms for explicit review rather
                    # than guessing an expiry boundary or aborting the whole
                    # calendar month.  The raw value remains intact.
                    contract.setdefault("contract_review_required", True)
                    contract.setdefault("contract_review_reason", "Contract months are malformed; media expiry was held.")
                    continue
                contract["months"] = max(0, months - 1)
                terminal = self.media_contract_terminal_status(contract)
                if terminal != "Active":
                    contract["status"] = terminal
                    if promotion is None:
                        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Media contract {contract['status'].lower()}: {contract['name']}.")
            # A successor is activated only after the predecessor has ended;
            # this prevents overlapping guarantees and keeps the boundary
            # deterministic across save/reload.
            pending = finance.get("media_successor_contract")
            predecessor = None
            if isinstance(pending, dict):
                predecessor_id = str(pending.get("predecessor_id", "") or "")
                predecessor = next((row for row in contracts if isinstance(row, dict) and str(row.get("id", row.get("name", "rights"))) == predecessor_id), None)
                if (pending.get("status") == "Pending" and predecessor and
                        predecessor.get("status") in ("Terminated", "Expired with shortfall", "Terminated for delivery failures")):
                    pending["status"] = "Needs review"
                    pending["needs_review_reason"] = "Predecessor ended with a shortfall; obtain a new valid commitment."
            if (isinstance(pending, dict) and pending.get("status") == "Pending" and predecessor and
                    predecessor.get("status") == "Fulfilled" and not self.active_media_contract(promotion)):
                successor = dict(pending)
                successor["status"] = "Active"
                successor["signed_month"] = safe_int(self.month, 0) or 0
                successor_events = safe_int(successor.get("events_total", successor.get("events_remaining", 1)), None)
                if successor_events is None or successor_events <= 0:
                    pending["status"] = "Needs review"
                    pending["needs_review_reason"] = "Successor entitlement count is malformed; obtain a new valid commitment."
                else:
                    successor["events_remaining"] = successor_events
                    contracts.insert(0, successor)
                    finance["media_successor_contract"] = None
                    if promotion is None:
                        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Media renewal activated with {successor.get('name', 'the outlet')}.")
            # Renewal becomes an available player decision at the declared
            # two-month/two-entitlement boundary. Preparing the offer is a
            # deterministic calendar action; it spends no cash or RNG.
            if promotion is None:
                current = self.active_media_contract()
                if (current and self.media_renewal_due(current) and
                        not isinstance(finance.get("media_successor_offer"), dict) and
                        not isinstance(finance.get("media_successor_contract"), dict)):
                    self.prepare_media_renewal_offer()
            self.sync_legacy_media_rights(promotion)

    def calculate_event_media_outcome(self, event, package=None, promotion=None, contract=None, apply=False):
        finance = self._ensure_media_state(promotion)
        event = event if isinstance(event, dict) else {}
        contract = contract or self.active_media_contract(promotion)
        eligible, reason = self.media_contract_eligibility(contract, event, promotion) if contract else (False, "No active rights deal")
        package = package if isinstance(package, dict) else {}
        financial = package.get("finance", package) if isinstance(package, dict) else {}
        financial = financial if isinstance(financial, dict) else {}

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback

        def safe_float(value, fallback=0.0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                result = float(value)
                return result if math.isfinite(result) else fallback
            except (TypeError, ValueError, OverflowError):
                return fallback

        fights = event.get("fights", [])
        if not isinstance(fights, (list, tuple)):
            fights = []
        fight_count = max(0, safe_int(package.get("fight_count", len(fights)), len(fights)))
        excitement = max(0.0, min(100.0, safe_float(package.get("average_excitement", financial.get("excitement_score", 50)), 50.0)))
        build = max(0.0, min(100.0, safe_float(financial.get("build_score", package.get("average_build", 50)), 50.0)))
        roster = self._media_company_values(promotion)[5]
        if not isinstance(roster, (list, tuple)):
            roster = []
        names = [name for fight in fights if isinstance(fight, dict) for name in (fight.get("fighters", []) or []) if isinstance(name, str)]
        featured = [fighter for fighter in roster if getattr(fighter, "name", "") in names]
        def fighter_metric(fighter, field):
            return safe_float(getattr(fighter, field, 0), 0.0)
        star_power = sum(
            fighter_metric(f, "popularity") + fighter_metric(f, "star_quality") + fighter_metric(f, "media_heat")
            for f in featured
        ) / max(1, len(featured)) if featured else 45
        campaign_history = finance.get("media_campaign_history", [])
        if not isinstance(campaign_history, list):
            campaign_history = []
        current_month = safe_int(getattr(self, "month", 0), 0)
        recent_campaigns = [row for row in campaign_history if isinstance(row, dict) and safe_int(row.get("month"), 0) in (current_month, current_month - 1)]
        campaign_lift = max(-8, min(14, sum(safe_float(row.get("heat", 0), 0.0) for row in recent_campaigns[:8]) / 8))
        reach = max(0, safe_int(contract.get("reach", 0), 0)) if eligible else (4 if event.get("broadcaster") != "No Coverage" else 0)
        rating = max(5, min(99, round(build * 0.30 + excitement * 0.28 + star_power * 0.22 + reach * 0.14 + campaign_lift + random.uniform(-5, 5))))
        viewers = round((8_000 + reach * 15_000) * (0.55 + rating / 100) * max(0.75, min(1.35, fight_count / 8))) if reach else round(1_500 * max(1, fight_count))
        minimum = max(0, safe_int(contract.get("minimum_rating", 0), 0)) if contract else 0
        production_tier, production_quality = self.media_event_production_quality(event)
        required_production = max(0, safe_int(contract.get("min_production", 0), 0)) if contract else 0
        production_ok = bool(not contract or production_quality >= required_production)
        delivery_reason = reason
        if eligible and not production_ok:
            delivery_reason = f"Production tier {production_tier} ({production_quality}) is below the contracted {required_production} standard"
        min_card_quality = max(0, safe_int(contract.get("min_card_quality", 0), 0)) if contract else 0
        delivered = bool(eligible and production_ok and rating >= minimum and build >= max(0, min_card_quality - 10))
        relationship_delta = (4 if delivered and rating >= minimum + 12 else 2 if delivered else -5 if eligible else -2)
        performance_bonus = max(0, safe_int(contract.get("performance_bonus", 0), 0)) if delivered and rating >= minimum + 10 else 0
        guarantee = max(0, safe_int(contract.get("fee", contract.get("guarantee_per_event", 0)), 0)) if eligible else 0
        exposure_delta = 2 if rating >= 78 else 1 if rating >= 58 else (-1 if not eligible else 0)
        result = {"outlet": contract.get("name", "No rights partner") if contract else "No rights partner", "eligible": eligible, "reason": delivery_reason, "reach": reach, "rating": rating, "viewers": viewers, "delivered": delivered, "minimum_rating": minimum, "required_production": required_production, "production_tier": production_tier, "production_quality": production_quality, "production_ok": production_ok, "relationship_delta": relationship_delta, "performance_bonus": performance_bonus, "rights_income": guarantee + performance_bonus, "exposure_delta": exposure_delta, "campaign_lift": round(campaign_lift, 1)}
        if contract:
            # Stable IDs keep account reviews truthful when two outlets share
            # a display name. Legacy outcome rows simply omit these fields.
            result["outlet_id"] = str(contract.get("outlet_id", "") or "")
            result["contract_id"] = str(contract.get("id", "") or "")
        if apply:
            self.record_media_event_outcome(event, result, promotion=promotion, featured_fighters=featured)
        return result

    def _media_event_entitlement_id(self, event):
        event = event or {}
        return str(event.get("event_id", "") or event.get("id", "") or
                   f"{event.get('name', event.get('event_name', 'event'))}:{event.get('month', self.month)}:{event.get('week', self.week)}")

    def record_commercial_receipt(self, event, media_outcome, promotion=None):
        """Create one idempotent, read-only-after-settlement commercial receipt."""
        finance = self._ensure_media_state(promotion)
        if hasattr(self, "ensure_foundation_ids"):
            self.ensure_foundation_ids()
        event_id = self._media_event_entitlement_id(event)
        receipt_id = f"commercial-receipt:{event_id}"
        existing = next((row for row in finance.get("media_commercial_receipts", []) if row.get("receipt_id") == receipt_id), None)
        if existing:
            return existing
        deals = finance.get("sponsor_deals", [])
        if not isinstance(deals, list):
            # A malformed retained sponsor envelope must not prevent the
            # rights receipt for an otherwise settled event from being saved.
            deals = []
        sponsor_rows = []
        for deal in deals:
            if not isinstance(deal, dict):
                continue
            ready, reason = self.sponsor_activation_status(deal, event=event) if promotion is None else (True, "promotion contract uses existing settlement")
            amount = int(self.sponsor_event_fee(deal, event=event) if promotion is None else deal.get("fee", 0) or 0)
            duty = self._sponsor_duty_for_deal(deal, create=False)
            evidence_key = ""
            if isinstance(deal.get("duty"), dict) and duty.get("status") == "Pending":
                evidence_key = f"{duty.get('duty_id', 'duty')}:{event_id}"
                evidence = duty.setdefault("evidence", [])
                if not any(item.get("evidence_key") == evidence_key for item in evidence if isinstance(item, dict)):
                    evidence.append({"evidence_key": evidence_key, "event_id": event_id, "met": bool(ready), "reason": reason})
            sponsor_rows.append({"deal_id": str(deal.get("id", "") or deal.get("name", "Sponsor")), "name": deal.get("name", "Sponsor"),
                                 "amount": amount, "status": "Met" if ready else "Shortfall", "reason": reason,
                                 "evidence_key": evidence_key, "duty_status": duty.get("status", "Legacy") if isinstance(duty, dict) else "Legacy"})
        rights_amount = int((media_outcome or {}).get("rights_income", 0) or 0)
        receipt = {
            "schema_version": 1, "receipt_id": receipt_id, "event_id": event_id,
            "date": f"M{self.month} W{self.week}", "event": (event or {}).get("name", (event or {}).get("event_name", "Event")),
            "rights": {"outlet": (media_outcome or {}).get("outlet", "No rights partner"),
                       "outlet_id": (media_outcome or {}).get("outlet_id", ""),
                       "contract_id": (media_outcome or {}).get("contract_id", ""),
                       "amount": rights_amount,
                       "delivered": bool((media_outcome or {}).get("delivered", False)), "reason": (media_outcome or {}).get("reason", ""),
                       "production_tier": (media_outcome or {}).get("production_tier", "Standard"),
                       "production_quality": (media_outcome or {}).get("production_quality", 45),
                       "required_production": (media_outcome or {}).get("required_production", 0)},
            "sponsors": sponsor_rows, "sponsor_total": sum(row["amount"] for row in sponsor_rows),
            "relationship_delta": int((media_outcome or {}).get("relationship_delta", 0) or 0),
        }
        finance["media_commercial_receipts"].insert(0, receipt)
        finance["media_commercial_receipts"] = finance["media_commercial_receipts"][:120]
        if hasattr(self, "foundation_append_historical"):
            self.foundation_append_historical("commercial_receipts", receipt, max_items=120)
        return receipt

    def record_media_event_outcome(self, event, outcome, promotion=None, featured_fighters=None):
        finance = self._ensure_media_state(promotion)
        # Settlement callers may supply a legacy/manual outcome rather than
        # the calculated result. Copy it before enriching so the saved receipt
        # still carries the active contract identity when that fact is known.
        event = event if isinstance(event, dict) else {}
        outcome = dict(outcome) if isinstance(outcome, dict) else {}

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))

        event_id = self._media_event_entitlement_id(event)
        receipt_id = f"commercial-receipt:{event_id}"
        existing_receipt = next((row for row in finance.get("media_commercial_receipts", []) if row.get("receipt_id") == receipt_id), None)
        if existing_receipt:
            return next((row for row in finance.get("media_audience_history", []) if row.get("event_id") == event_id), existing_receipt)
        contract = self.active_media_contract(promotion)
        if contract:
            outcome.setdefault("outlet_id", str(contract.get("outlet_id", "") or ""))
            outcome.setdefault("contract_id", str(contract.get("id", "") or ""))
        if contract and outcome.get("eligible"):
            # Legacy contracts can retain malformed relationship/strike
            # evidence even when their entitlement count is still usable. Do
            # not let that evidence abort settlement or overwrite it with a
            # guessed value; valid fields continue to receive their ordinary
            # transition and the saved audience row carries the review note.
            quality_notes = []
            raw_remaining = contract.get("events_remaining", 0)
            remaining = safe_int(raw_remaining, None)
            if remaining is None:
                quality_notes.append("events_remaining is malformed")
            else:
                contract["events_remaining"] = max(0, remaining - 1)
            raw_relationship = contract.get("relationship", 50)
            relationship = safe_int(raw_relationship, None)
            delta = safe_int(outcome.get("relationship_delta", 0), 0)
            if relationship is None:
                quality_notes.append("relationship is malformed")
            else:
                contract["relationship"] = max(0, min(100, relationship + delta))
            if not outcome.get("delivered"):
                raw_breaches = contract.get("breach_strikes", 0)
                breaches = safe_int(raw_breaches, None)
                if breaches is None:
                    quality_notes.append("breach_strikes is malformed")
                else:
                    contract["breach_strikes"] = breaches + 1
            breaches = safe_int(contract.get("breach_strikes", 0), None)
            if relationship is not None:
                finance["media_relationships"][contract.get("outlet_id", "")] = contract["relationship"]
            if quality_notes:
                outcome["settlement_review"] = "; ".join(quality_notes)
                outcome["settlement_status"] = "Needs review"
            if breaches is not None and breaches >= 3:
                contract["status"] = "Terminated"
                pending = finance.get("media_successor_contract")
                if (isinstance(pending, dict) and pending.get("status") == "Pending" and
                        str(pending.get("predecessor_id", "")) == str(contract.get("id", contract.get("name", "rights")))):
                    pending["status"] = "Needs review"
                    pending["needs_review_reason"] = "Predecessor terminated for delivery failures; obtain a new valid commitment."
            else:
                terminal = self.media_contract_terminal_status(contract)
                if terminal != "Active":
                    contract["status"] = terminal
        row = {"date": f"M{self.month} W{self.week}", "month": self.month, "week": self.week, "event_id": event_id, "event": event.get("name", event.get("event_name", "Event")), **dict(outcome)}
        finance["media_audience_history"].insert(0, row)
        finance["media_audience_history"] = finance["media_audience_history"][:60]
        self.record_commercial_receipt(event, outcome, promotion=promotion)
        if promotion is None:
            self.company_pop = max(1, min(100, self.company_pop + outcome.get("exposure_delta", 0)))
            self.fanbase["casual_reach"] = max(5, min(100, self.fanbase.get("casual_reach", 30) + outcome.get("exposure_delta", 0)))
            for fighter in list(featured_fighters or [])[:6]:
                if outcome.get("rating", 0) >= 66:
                    fighter.popularity = min(100, fighter.popularity + 1)
                    fighter.sponsor_appeal = min(100, fighter.sponsor_appeal + 1)
            headline = f"{row['event']} drew an audience rating of {outcome.get('rating', 0)} for {outcome.get('outlet', 'its media partner')}."
            self.news.insert(0, headline)
            if hasattr(self, "record_world_story"):
                detail = f"Estimated viewers: {outcome.get('viewers', 0):,}. Contract delivery: {'met' if outcome.get('delivered') else 'missed'}. Relationship {outcome.get('relationship_delta', 0):+}."
                self.record_world_story("Media", headline, detail, [self.player_company_name], [f.name for f in list(featured_fighters or [])[:6]], 3)
        else:
            promotion.reputation_score = max(1, min(100, promotion.reputation_score + (1 if outcome.get("rating", 0) >= 78 else 0)))
        self.sync_legacy_media_rights(promotion)
        return row

    # ----- Media Desk UI callbacks / compatibility wrappers -----
    def _media_surface_notice(self, attr, message, *, warning=False, title="Media Desk"):
        """Keep routine media feedback in the active desk when available.

        Campaign and rights actions are often reached from a finance shortcut,
        so the desk may not be built in headless/regression callers.  Preserve
        the compatibility dialog for those callers while the live game keeps
        the result beside the controls instead of losing it behind a popup.
        """
        widget = getattr(self, attr, None)
        if widget is not None:
            semantic = self.semantic_status_palette(self.colors) if hasattr(self, "semantic_status_palette") else {}
            colour = semantic.get("negative" if warning else "info", self.colors.get("gold", "#e0b85c"))
            try:
                widget.config(text=str(message), foreground=colour)
                return
            except (tk.TclError, AttributeError):
                pass
        (messagebox.showwarning if warning else messagebox.showinfo)(title, str(message))

    def _media_campaign_notice(self, message, *, warning=False):
        self._media_surface_notice("media_action_notice", message, warning=warning, title="Media Campaign")

    def _media_plan_notice(self, message, *, warning=False):
        self._media_surface_notice("media_plan_notice", message, warning=warning, title="Campaign Plan")

    def _media_rights_notice(self, message, *, warning=False):
        self._media_surface_notice("media_rights_notice", message, warning=warning, title="Media Rights")

    def _media_receipt_notice(self, message, *, warning=False):
        """Keep receipt-reader guidance beside the retained receipt list.

        A receipt is an observational record, so selecting or opening it should
        never interrupt the player with a transient dialog.  The label is also
        used by headless/legacy callers through the shared compatibility helper.
        """
        self._media_surface_notice("media_receipt_detail", message, warning=warning, title="Settlement receipt")

    def media_apply_strategy(self):
        finance = self.ensure_player_media_state()
        strategy = self.media_strategy_choice.get() if hasattr(self, "media_strategy_choice") else "Balanced"
        if strategy not in self.MEDIA_STRATEGIES:
            strategy = "Balanced"
        finance["media_strategy"] = strategy
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Media strategy changed to {strategy}.")
        self._media_campaign_notice(f"Strategy set to {strategy}. Future campaign previews now use this operating brief.")
        self.refresh_all()

    def media_run_selected_campaign(self):
        fighter = self.media_desk_fighter() if hasattr(self, "media_desk_fighter") else None
        action = self.media_action_choice.get() if hasattr(self, "media_action_choice") else "Interview"
        target_label = self.media_target_choice.get() if hasattr(self, "media_target_choice") else ""
        target = getattr(self, "_media_target_rows", {}).get(target_label)
        if target is None and action == "Call Out" and target_label:
            try:
                target = self.get_fighter(target_label)
            except LookupError:
                target = None
        plan = self.ensure_player_media_state().get("media_primary_plan")
        if isinstance(plan, dict) and plan.get("status") not in ("Cancelled", "Completed", "Replaced"):
            ok, text, _row = self.execute_media_campaign_plan(action, fighter, target, region=getattr(self, "player_region", ""))
        else:
            ok, text, _row = self.resolve_media_campaign(action, fighter, target, region=getattr(self, "player_region", ""))
        self._media_campaign_notice(text, warning=not ok)
        self.refresh_all()

    def refresh_media_plan_targets(self, _event=None):
        """Refresh plan targets without creating offers or touching RNG."""
        if not hasattr(self, "media_plan_target_combo"):
            return
        objective = self.media_plan_objective_choice.get() if hasattr(self, "media_plan_objective_choice") else "Event Promotion"
        # Migration/ID repair belongs to plan creation or calendar ownership,
        # not a combobox repaint.  Legacy targets remain visible through their
        # existing name fallback until the player explicitly saves a plan.
        current = self.media_plan_target_choice.get() if hasattr(self, "media_plan_target_choice") else ""
        selected_source_id = str(getattr(self, "_media_plan_target_map", {}).get(current, "") or "")
        options = self.media_plan_target_options(objective, migrate=False)
        self._media_plan_target_rows = options
        labels = [str(row.get("display_label", row.get("label", row.get("id", "")))) for row in options]
        self._media_plan_target_map = {
            str(row.get("display_label", row.get("label", row.get("id", "")))): str(row.get("id", "") or "")
            for row in options if row.get("selectable", True)
        }
        self.media_plan_target_combo.configure(values=labels)
        retained = next((label for label, source_id in self._media_plan_target_map.items() if source_id == selected_source_id), "")
        if retained:
            self.media_plan_target_choice.set(retained)
        elif current not in labels:
            self.media_plan_target_choice.set("")
        action_options = {
            "Event Promotion": ("Press Tour", "Press Conference", "Interview", "Highlight Package"),
            "Prospect Exposure": ("Interview", "Open Workout", "Highlight Package", "Press Tour"),
            "Sponsor Duty": ("Interview", "Press Tour", "Highlight Package", "Open Workout"),
            "Regional Work": ("Regional Tour", "Open Workout", "Interview"),
            "Trust Repair": ("Crisis Response", "Press Conference", "Interview"),
        }.get(objective, ("Interview",))
        if hasattr(self, "media_plan_action_combo"):
            self.media_plan_action_combo.configure(values=action_options)
        if hasattr(self, "media_plan_action_choice") and self.media_plan_action_choice.get() not in action_options:
            self.media_plan_action_choice.set(action_options[0])
        self.refresh_media_plan_summary()

    def _selected_media_plan_target_id(self):
        label = self.media_plan_target_choice.get() if hasattr(self, "media_plan_target_choice") else ""
        return str(getattr(self, "_media_plan_target_map", {}).get(label, "") or "")

    def refresh_media_plan_summary(self):
        if not hasattr(self, "media_plan_summary"):
            return
        finance = self._media_finance_readonly()
        plan = finance.get("media_primary_plan")
        if not isinstance(plan, dict) or plan.get("status") in ("Cancelled", "Completed", "Replaced"):
            self.media_plan_summary.config(text="No active plan. Save an optional target and action to create a reviewable campaign brief; this does not grant a hidden bonus.")
            return
        action = self.media_plan_action_choice.get() if hasattr(self, "media_plan_action_choice") else "Interview"
        quote = self.media_plan_quote(plan.get("objective", ""), plan.get("target_id", ""), action, self.media_desk_fighter() if hasattr(self, "media_desk_fighter") else None)
        # This is a presentation-only projection.  Legacy or externally
        # edited quote/plan fields must not reach Tk formatting operators (or
        # turn a malformed string into a list of fake completed actions).
        quote = quote if isinstance(quote, dict) else {}
        details = quote.get("details", {})
        details = details if isinstance(details, dict) else {}

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))

        receipts = plan.get("action_receipts", [])
        completed = len(receipts) if isinstance(receipts, (list, tuple)) else 0
        amount = safe_int(quote.get("amount", 0))
        action_points = safe_int(details.get("action_points", 0))
        revision = safe_int(plan.get("revision", 1), 1)
        self.media_plan_summary.config(text=(
            f"{plan.get('status', 'Draft').upper()}  |  {plan.get('objective', 'Campaign')} → {plan.get('target_label', 'Target')}  |  "
            f"Action {action} (${max(0, amount):,}, {action_points} AP)  |  Completed {completed}  |  Revision {max(0, revision)}. "
            "Quotes are current-state only; retarget before committing if the event or fighter changes."
        ))

    def media_save_plan_from_ui(self):
        objective = self.media_plan_objective_choice.get() if hasattr(self, "media_plan_objective_choice") else ""
        target_id = self._selected_media_plan_target_id()
        action = self.media_plan_action_choice.get() if hasattr(self, "media_plan_action_choice") else "Interview"
        try:
            spend = max(0, int((self.media_plan_spend_entry.get() if hasattr(self, "media_plan_spend_entry") else "0") or 0))
        except (TypeError, ValueError):
            self._media_plan_notice("Spend ceiling must be a whole number (0 means no extra ceiling).", warning=True)
            return
        ok, text, _plan = self.create_media_campaign_plan(objective, target_id, action_ids=[action], spend_ceiling=spend)
        self._media_plan_notice(text, warning=not ok)
        self.refresh_media_plan_summary()

    def media_retarget_plan_from_ui(self):
        target_id = self._selected_media_plan_target_id()
        ok, text, _plan = self.retarget_media_campaign_plan(target_id)
        self._media_plan_notice(text, warning=not ok)
        self.refresh_media_plan_summary()

    def media_cancel_plan_from_ui(self):
        ok, text, _plan = self.cancel_media_campaign_plan()
        self._media_plan_notice(text, warning=not ok)
        self.refresh_media_plan_summary()

    def _selected_media_offer_id(self):
        selected = self.media_offers_tree.selection() if hasattr(self, "media_offers_tree") else ()
        if not selected:
            return ""
        # Treeview IDs are presentation keys. Resolve the saved offer through
        # the row map so a refresh or duplicate legacy row cannot route an
        # accept/counter/reject action to a different offer.
        row = getattr(self, "_media_offer_rows", {}).get(selected[0])
        if isinstance(row, dict):
            return str(row.get("id", "") or "").strip()
        return ""

    @staticmethod
    def _media_offer_identity_key(offer, index=None):
        """Return a stable market-offer identity without using row position."""
        if not isinstance(offer, dict):
            return ""
        offer_id = str(offer.get("id", "") or "").strip()
        if offer_id:
            return f"media-offer:{offer_id}"
        payload = {
            "name": offer.get("name", ""), "type": offer.get("type", ""),
            "fee": offer.get("fee", ""), "months": offer.get("months", ""),
            "events_total": offer.get("events_total", ""),
            "expires_month": offer.get("expires_month", ""),
            "reach": offer.get("reach", ""),
        }
        payload["raw_type"] = type(offer).__name__
        digest = hashlib.sha1(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]
        return f"legacy-media-offer:{digest}"

    @classmethod
    def _media_offer_view_id(cls, offer, fallback_index=0):
        """Build the Treeview key used by the read-only offer table."""
        identity = cls._media_offer_identity_key(offer, index=fallback_index)
        if identity:
            return identity
        raw = f"{type(offer).__name__}:{offer!s}"
        digest = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:20]
        return f"legacy-media-offer:{digest}"

    def media_accept_selected_offer(self):
        offer_id = self._selected_media_offer_id()
        if not offer_id:
            self._media_rights_notice("Select a media-rights offer first.", warning=True)
            return
        active = self.active_media_contract()
        if active and not messagebox.askyesno("Replace Media Deal", f"Accepting this offer will end {active['name']} and may charge its ${active.get('termination_fee', 0):,} buyout. Continue?"):
            return
        ok, text = self.accept_player_media_offer(offer_id)
        self._media_rights_notice(text, warning=not ok)
        if ok:
            self.news.insert(0, text)
            self.record_world_story("Business", f"{self.player_company_name} signs with {self.active_media_contract()['name']}.", text, [self.player_company_name], [], 3)
        self.refresh_all()

    def media_reject_selected_offer(self):
        offer_id = self._selected_media_offer_id()
        if not offer_id:
            self._media_rights_notice("Select a media-rights offer first.", warning=True)
            return
        _ok, text = self.reject_player_media_offer(offer_id)
        self._media_rights_notice(text)
        self.finance.setdefault("ledger", []).insert(0, f"Month {self.month}: {text}")
        self.refresh_all()

    def media_refresh_offers(self):
        finance = self.ensure_player_media_state()
        cost = 3_500
        if self.cash < cost:
            self._media_rights_notice(f"A market review costs ${cost:,}; cash is short, so no review was commissioned.", warning=True)
            return
        current = len(finance.get("media_offers", []) or [])
        if not messagebox.askyesno(
            "Commission Media Market Review",
            f"Commission a fresh media-rights market review for ${cost:,}?\n\n"
            f"This replaces {current} uncommitted offer(s); active contracts are not changed.",
        ):
            return
        self.cash -= cost
        self.record_finance_transaction(
            "Media-rights market review", costs=cost, category="Media",
            source="Media market research", reference=f"media-market-review:{self.month}:{self.week}",
        )
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Commissioned media-rights market review for ${cost:,}.")
        self.generate_media_offers(force=True)
        self._media_rights_notice(f"Market review complete: {len(finance.get('media_offers', []) or [])} fresh offer(s) are ready to compare.")
        self.refresh_all()

    def media_terminate_contract(self):
        active = self.active_media_contract()
        if not active:
            self._media_rights_notice("There is no active media deal to end.", warning=True)
            return
        if not messagebox.askyesno("End Media Deal", f"End {active['name']} for ${active.get('termination_fee', 0):,}?"):
            return
        ok, text = self.terminate_player_media_contract(active.get("id", ""))
        self._media_rights_notice(text, warning=not ok)
        self.refresh_all()

    def media_prepare_renewal(self):
        ok, text, _offer = self.prepare_media_renewal_offer()
        self._media_rights_notice(text, warning=not ok)
        self.refresh_all()

    def media_accept_renewal(self):
        ok, text, _result = self.accept_media_renewal_offer()
        self._media_rights_notice(text, warning=not ok)
        self.refresh_all()

    def media_counter_renewal(self):
        stance = self.media_negotiation_stance.get() if hasattr(self, "media_negotiation_stance") else "Higher Guarantee"
        ok, text, _result = self.counter_media_renewal_offer(stance=stance)
        self._media_rights_notice(text, warning=not ok)
        self.refresh_all()

    def negotiate_media_rights(self):
        """Finance-screen shortcut into the actual offer market."""
        finance = self.ensure_player_media_state()
        generated = not bool(finance.get("media_offers"))
        self.generate_media_offers(force=generated)
        if hasattr(self, "select_tab"):
            self.select_tab("website")
        else:
            self.refresh_all()
        if generated:
            self._media_rights_notice("Media market opened with a fresh set of offers. Compare delivery standards before committing.")

    def pitch_sponsors(self):
        """Ask the market for competing, fit-aware offers instead of auto-signing one."""
        finance = self.ensure_player_media_state()
        brief = self.sponsor_pitch_brief.get() if hasattr(self, "sponsor_pitch_brief") else finance.get("sponsor_pitch_brief", "Balanced Portfolio")
        if brief not in ("Balanced Portfolio", "Highest Fee", "Best Brand Fit", "Long Partnership", "Accessible Brands"):
            brief = "Balanced Portfolio"
        finance["sponsor_pitch_brief"] = brief
        if finance.get("sponsor_last_pitch_month") == self.month:
            finance["sponsor_market_note"] = "The commercial team has already pitched this month. Review the live offers below."
            if hasattr(self, "refresh_finance"):
                self.refresh_finance()
            return
        finance["sponsor_last_pitch_month"] = self.month
        brands = [
            ("Apex Hydration", "Hydration", 28), ("Ironclad Fight Gear", "Equipment", 22),
            ("Volt Energy", "Energy Drink", 38), ("Northstar Sportsbook", "Betting", 44),
            ("Forge Nutrition", "Nutrition", 30), ("Atlas Automotive", "Automotive", 64),
            ("Guardline Insurance", "Insurance", 55), ("Victory Mobile", "Technology", 48),
            ("Skyline Sports", "Broadcast Partner", 72), ("Pioneer Fitness", "Training", 20),
            ("Crown Hotels", "Travel", 58), ("Vertex Gaming", "Gaming", 46),
        ]
        existing = {str(deal.get("name", "")).lower() for deal in finance.get("sponsor_deals", []) if isinstance(deal, dict)}
        available = [row for row in brands if row[0].lower() not in existing]
        if not available:
            finance["sponsor_market_note"] = "No fresh brands are available while the current portfolio remains active."
            self.refresh_all()
            return
        top_appeal = sum(sorted((f.sponsor_appeal for f in self.roster), reverse=True)[:8]) / max(1, min(8, len(self.roster)))
        trust = finance.get("media_public_trust", 55)
        base_score = self.company_pop * 0.55 + self.company_stability * 0.18 + top_appeal * 0.18 + trust * 0.09
        access_bonus = 12 if brief == "Accessible Brands" else 0
        suitable = [row for row in available if base_score + access_bonus + random.randint(-18, 18) >= row[2]]
        if not suitable:
            text = "Brands passed after reviewing company reach, stability, public trust, and roster sponsor appeal."
            finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Sponsor pitch failed.")
            self.inbox.append({"subject": "Sponsor Pitch Failed", "body": text, "type": "Business", "resolved": False})
            finance["sponsor_market_note"] = text
            self.refresh_all()
            return
        offers = []
        random.shuffle(suitable)
        for index, (name, category, threshold) in enumerate(suitable[:min(4, max(2, len(suitable)))]):
            fit = max(1, min(99, round(base_score - threshold + 58 + random.randint(-7, 7)
                                       + (8 if brief == "Best Brand Fit" else 0))))
            fee = max(4_000, round((self.company_pop * 190 + top_appeal * 85 + fit * 110)
                                   * random.uniform(0.75, 1.35) * (1.16 if brief == "Highest Fee" else 1) / 100) * 100)
            months = random.randint(12, 24) if brief == "Long Partnership" else random.randint(6, 18)
            offers.append({
                "id": f"sponsor-{self.month}-{index}-{name.lower().replace(' ', '-')}", "name": name,
                "category": category, "fee": fee, "months": months, "fit": fit, "pitch_brief": brief,
                "relationship": 50, "activation_requirement": random.choice((
                    "Brand placement on every promoted event", "Feature a ranked fighter in campaign media",
                    "Maintain company stability above 45", "Deliver at least one event each month",
                )), "conduct_threshold": max(20, 78 - trust), "expires_month": self.month + 1,
            })
        finance["sponsor_offers"] = offers
        finance["sponsor_market_note"] = f"{len(offers)} offer(s) returned for the {brief} brief. Select one to compare, negotiate or sign."
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Sponsor market returned {len(offers)} offer(s).")
        self.refresh_all()

    def selected_sponsor_offer(self):
        if not hasattr(self, "sponsor_market_tree"):
            return None
        selected = self.sponsor_market_tree.selection()
        if not selected:
            return None
        row = getattr(self, "_sponsor_market_rows", {}).get(selected[0])
        if isinstance(row, dict):
            item = row.get("item") if row.get("kind") == "offer" else None
            return item if isinstance(item, dict) else None
        # Compatibility with callers/tests that select an offer by its saved
        # ID before the finance table has built its identity map.
        offer_id = selected[0]
        offers = self.finance.get("sponsor_offers", []) if isinstance(getattr(self, "finance", None), dict) else []
        return next((offer for offer in offers if isinstance(offer, dict) and offer.get("id") == offer_id), None)

    def selected_sponsor_deal(self):
        """Return the selected active agreement, if the portfolio row is selected."""
        if not hasattr(self, "sponsor_market_tree"):
            return None
        selected = self.sponsor_market_tree.selection()
        row = getattr(self, "_sponsor_market_rows", {}).get(selected[0]) if selected else None
        item = row.get("item") if isinstance(row, dict) and row.get("kind") == "deal" else None
        return item if isinstance(item, dict) else None

    def show_selected_sponsor_offer(self):
        if not hasattr(self, "sponsor_offer_verdict"):
            return
        offer = self.selected_sponsor_offer()
        deal = self.selected_sponsor_deal()
        if deal:
            ready, reason = self.sponsor_activation_preview(deal)
            duty = deal.get("duty") if isinstance(deal.get("duty"), dict) else {}
            duty_status = duty.get("status", "Legacy")
            try:
                fee = max(0, int(deal.get("fee", 0) or 0))
            except (TypeError, ValueError):
                fee = 0
            estimated = fee if ready else round(fee * 0.5)
            basis = "FULL FEE" if ready else "HALF FEE"
            try:
                term_months = max(0, int(deal.get("months", 0) or 0))
            except (TypeError, ValueError):
                term_months = 0
            self.sponsor_offer_verdict.config(text=f"ACTIVE PARTNER  •  {'READY' if ready else 'AT RISK'}")
            self.sponsor_offer_numbers.config(
                text=(f"FIT {deal.get('fit', '-')}/100  •  MAX ${fee:,}/ELIGIBLE EVENT  •  "
                      f"EST. NOW ${estimated:,} ({basis})  •  TERM {term_months} MO  •  "
                      f"DUTY {duty_status}  •  AGREEMENT {deal.get('agreement_id', 'Legacy')}")
            )
            if hasattr(self, "sponsor_offer_reason"):
                self.sponsor_offer_reason.config(
                    text=f"Active agreement. Current preview: {reason}. {basis.title()} applies at settlement; stored duty evidence remains read-only until event settlement."
                )
            for attr in ("sponsor_accept_button", "sponsor_negotiate_button", "sponsor_reject_button"):
                button = getattr(self, attr, None)
                if button is not None:
                    button.configure(state="disabled")
            return
        for attr in ("sponsor_accept_button", "sponsor_negotiate_button", "sponsor_reject_button"):
            button = getattr(self, attr, None)
            if button is not None:
                button.configure(state="normal" if offer else "disabled")
        assessment = self.sponsor_offer_assessment(offer)
        self.sponsor_offer_verdict.config(text=assessment["verdict"])
        if offer:
            conflict = f"  •  BLOCKED BY {assessment['conflict']}" if assessment["conflict"] else ""
            counter = "  •  COUNTER COMPLETE" if offer.get("negotiated") else "  •  COUNTER AVAILABLE"
            readiness = "READY NOW" if assessment["activation_ready"] else "AT RISK NOW"
            self.sponsor_offer_numbers.config(
                text=(f"FIT {assessment['score']}/100  •  MAX ${assessment['max_per_event']:,}/ELIGIBLE EVENT  •  "
                      f"EST. NOW ${assessment['estimated_per_event']:,}/EVENT  •  TERM {assessment['term_months']} MO  •  "
                      f"{readiness}{counter}{conflict}")
            )
            if hasattr(self, "sponsor_offer_reason"):
                self.sponsor_offer_reason.config(
                    text=f"Activation check: {assessment['activation_reason']}. Maximum is the contracted fee; estimate uses the current full/half-fee rule."
                )
        else:
            self.sponsor_offer_numbers.config(text="Compare fee, fit, term and activation duty")
            if hasattr(self, "sponsor_offer_reason"):
                self.sponsor_offer_reason.config(text="Activation requirements and fee basis appear here when an offer is selected.")

    def sponsor_activation_preview(self, deal, event=None):
        """Return a pure current-state activation estimate for an offer card.

        This intentionally does not call ``ensure_player_media_state`` or any
        settlement helper: opening/refreshing the sponsor market must remain a
        read-only preview.  Settlement still uses ``sponsor_activation_status``
        as its canonical owner.
        """
        finance = getattr(self, "finance", {}) or {}

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback

        trust = safe_int(finance.get("media_public_trust", 55), 55) if isinstance(finance, dict) else 55
        threshold = safe_int(deal.get("conduct_threshold", 0), 0) if isinstance(deal, dict) else 0
        if trust < threshold:
            return False, f"public trust {trust} is below {threshold}"
        if not isinstance(deal, dict):
            return False, "the saved sponsor agreement is unavailable"
        requirement = str(deal.get("activation_requirement", "Event brand placement"))
        stability = safe_int(getattr(self, "company_stability", 0), 0)
        if requirement == "Maintain company stability above 45" and stability <= 45:
            return False, f"company stability is {stability}"
        if requirement == "Feature a ranked fighter in campaign media":
            campaign_history = finance.get("media_campaign_history", []) if isinstance(finance, dict) else []
            if not isinstance(campaign_history, list):
                campaign_history = []
            subjects = {
                row.get("subject") for row in campaign_history
                if isinstance(row, dict) and safe_int(row.get("month", 0), 0) == safe_int(getattr(self, "month", 0), 0)
            }
            roster = getattr(self, "roster", [])
            if not isinstance(roster, (list, tuple)):
                roster = []
            featured = [fighter for fighter in roster if getattr(fighter, "name", "") in subjects]
            if not any(getattr(fighter, "champion", False) or 0 < safe_int(getattr(fighter, "ranking_position", 0), 0) <= 10 for fighter in featured):
                return False, "run media this month with a champion or top-10 fighter"
        if requirement == "Deliver at least one event each month":
            # A committed event is the future evidence this duty is waiting
            # for.  Keep the offer card (which has no event argument) at-risk,
            # while a runway row may show the event-specific expectation
            # without pretending that settlement has already happened.
            if isinstance(event, dict) and (event.get("event_id") or event.get("id") or event.get("name")):
                return True, "scheduled event satisfies the delivery duty when settled"
            return False, "requires a delivered event this month"
        return True, "activation ready"

    def sponsor_offer_assessment(self, offer):
        if not isinstance(offer, dict):
            return {
                "score": 0, "verdict": "Select an offer", "annual": 0, "max_per_event": 0,
                "estimated_per_event": 0, "term_months": 0, "activation_ready": False,
                "activation_reason": "Select an offer", "conflict": "",
            }
        finance = getattr(self, "finance", {}) if isinstance(getattr(self, "finance", {}), dict) else {}
        deals = finance.get("sponsor_deals", [])
        if not isinstance(deals, list):
            deals = []
        conflict = next((deal.get("name", "Active partner") for deal in deals
                         if isinstance(deal, dict) and deal.get("category") == offer.get("category")), "")
        try:
            raw_months = int(offer.get("months", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            raw_months = 0
        months = min(12, max(1, raw_months))
        # The old label implied guaranteed annual income. Retain the legacy
        # ``annual`` value for save/test compatibility, but make the display
        # explicit that it assumes one qualifying event per month.
        try:
            fee = max(0, int(offer.get("fee", 0) or 0))
        except (TypeError, ValueError, OverflowError):
            fee = 0
        try:
            fit = max(0, int(offer.get("fit", 0) or 0))
        except (TypeError, ValueError, OverflowError):
            fit = 0
        annual = fee * months
        score = round(fit * .52 + min(100, fee / 700) * .30
                      + min(100, raw_months * 5) * .18)
        verdict = "BLOCKED — CATEGORY CONFLICT" if conflict else "STRONG FIT" if score >= 72 else "WORKABLE" if score >= 54 else "LOW VALUE"
        activation_ready, activation_reason = self.sponsor_activation_preview(offer)
        return {
            "score": score, "verdict": verdict, "annual": annual, "months_assumed": months,
            "term_months": max(0, raw_months),
            "max_per_event": fee, "estimated_per_event": fee if activation_ready else round(fee * .5),
            "activation_ready": activation_ready, "activation_reason": activation_reason,
            "conflict": conflict,
        }

    def sponsor_activation_status(self, deal, event=None):
        """Return whether today's portfolio work earns this deal's full event fee."""
        if not isinstance(deal, dict):
            return False, "the saved sponsor agreement is unavailable"
        finance = self.ensure_player_media_state()
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
        trust = safe_int(finance.get("media_public_trust", 55), 55)
        threshold = safe_int(deal.get("conduct_threshold", 0))
        if trust < threshold:
            return False, f"public trust {trust} is below {threshold}"
        requirement = str(deal.get("activation_requirement", "Event brand placement"))
        stability = safe_int(getattr(self, "company_stability", 0))
        if requirement == "Maintain company stability above 45" and stability <= 45:
            return False, f"company stability is {stability}"
        if requirement == "Feature a ranked fighter in campaign media":
            campaign_history = finance.get("media_campaign_history", [])
            if not isinstance(campaign_history, list):
                campaign_history = []
            current_month = safe_int(getattr(self, "month", 0))
            subjects = {row.get("subject") for row in campaign_history
                        if isinstance(row, dict) and safe_int(row.get("month", 0)) == current_month}
            roster = getattr(self, "roster", [])
            if not isinstance(roster, (list, tuple)):
                roster = []
            featured = [fighter for fighter in roster if getattr(fighter, "name", "") in subjects]
            if not any(getattr(fighter, "champion", False) or 0 < safe_int(getattr(fighter, "ranking_position", 0)) <= 10 for fighter in featured):
                return False, "run media this month with a champion or top-10 fighter"
        if requirement == "Deliver at least one event each month":
            current_month = safe_int(getattr(self, "month", 1), 1)
            event_month = safe_int((event or {}).get("month", current_month), current_month) if isinstance(event, dict) else current_month
            audience_history = finance.get("media_audience_history", [])
            if not isinstance(audience_history, list):
                audience_history = []
            delivered_this_month = any(
                isinstance(row, dict) and safe_int(row.get("month", 0)) == event_month
                for row in audience_history
            )
            if isinstance(event, dict) and safe_int(event.get("month", current_month), current_month) == event_month:
                delivered_this_month = True
            if not delivered_this_month:
                return False, "deliver at least one event this month"
        return True, "activation ready"

    def _sponsor_duty_for_deal(self, deal, *, create=False):
        """Return the saved duty envelope for a newly versioned agreement.

        Legacy sponsor dictionaries remain untouched unless the player signs a
        new offer.  Their existing fee/activation path therefore stays exactly
        as before while the UI can still describe them as legacy terms.
        """
        if not isinstance(deal, dict):
            return None
        duty = deal.get("duty")
        if isinstance(duty, dict):
            duty.setdefault("status", "Pending")
            duty.setdefault("evidence", [])
            return duty
        if not create:
            return {"duty_id": f"legacy-duty:{deal.get('name', 'sponsor')}", "status": "Legacy", "evidence": [], "legacy": True}
        agreement_id = str(deal.get("agreement_id", "") or deal.get("id", "") or deal.get("name", "Sponsor"))
        try:
            months = max(1, int(deal.get("months", 1) or 1))
        except (TypeError, ValueError):
            months = 1
        duty = {
            "duty_id": f"duty:{agreement_id}", "type": str(deal.get("activation_requirement", "Event brand placement")),
            "period_start": int(deal.get("signed_month", self.month) or self.month),
            "period_end": int(deal.get("signed_month", self.month) or self.month) + months - 1,
            "status": "Pending", "evidence": [], "reviewed_month": None,
        }
        deal["duty"] = duty
        return duty

    def review_sponsor_duties(self, promotion=None):
        """Close versioned duties at period end without adding a new penalty."""
        finance = self._ensure_media_state(promotion)
        if promotion is not None:
            return []
        closed = []
        for deal in list(finance.get("sponsor_deals", []) or []):
            duty = self._sponsor_duty_for_deal(deal, create=False)
            if not isinstance(duty, dict) or duty.get("legacy") or duty.get("status") != "Pending":
                continue
            try:
                period_end = int(duty.get("period_end", self.month) or self.month)
            except (TypeError, ValueError):
                period_end = self.month
            if int(self.month) <= period_end:
                continue
            evidence = list(duty.get("evidence", []) or [])
            duty["status"] = "Met" if any(isinstance(item, dict) and item.get("met") for item in evidence) else "Missed"
            duty["reviewed_month"] = int(self.month)
            snapshot = {"agreement_id": deal.get("agreement_id", deal.get("name", "Sponsor")), "duty": dict(duty), "name": deal.get("name", "Sponsor")}
            finance.setdefault("sponsor_duty_history", []).insert(0, snapshot)
            finance["sponsor_duty_history"] = finance["sponsor_duty_history"][:120]
            closed.append(snapshot)
        return closed

    def sponsor_event_fee(self, deal, event=None):
        ready, _reason = self.sponsor_activation_status(deal, event=event)
        if not isinstance(deal, dict):
            return 0
        try:
            fee = max(0, int(deal.get("fee", 0) or 0))
        except (TypeError, ValueError, OverflowError):
            fee = 0
        return fee if ready else round(fee * .5)

    def negotiate_sponsor_offer(self):
        finance = self.ensure_player_media_state()
        offer = self.selected_sponsor_offer()
        if not offer:
            finance["sponsor_market_note"] = "Select a live sponsor offer before negotiating."
            self.refresh_finance(); return
        _ok, message = self.counter_sponsor_offer(offer.get("id", ""))
        finance["sponsor_market_note"] = message
        self.refresh_finance()

    def counter_sponsor_offer(self, offer_id, roll=None):
        """Resolve one sponsor counter; ``roll`` keeps regression tests deterministic."""
        finance = self.ensure_player_media_state()
        offers = finance.get("sponsor_offers", [])
        if not isinstance(offers, list):
            offers = []
        offer = next((row for row in offers if isinstance(row, dict) and row.get("id") == offer_id), None)
        if not offer:
            return False, "That sponsor offer is no longer available."
        if offer.get("negotiated"):
            return False, f"{offer.get('name', 'Sponsor')} has already answered your counter."
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback
        fee = safe_int(offer.get("fee"), None)
        fit = safe_int(offer.get("fit"), None)
        stability = safe_int(getattr(self, "company_stability", 0), None)
        marketing = safe_int(self.staff_skill("Marketing") if hasattr(self, "staff_skill") else 45, None)
        if fee is None or fit is None or stability is None or marketing is None:
            offer.setdefault("offer_review_required", True)
            offer.setdefault("offer_review_reason", "Sponsor fee, fit or company evidence is malformed.")
            return False, "That sponsor offer has malformed terms and needs review before negotiation."
        chance = max(20, min(88, round(24 + fit * .32 + stability * .18
                                      + marketing * .18 - fee / 5000)))
        offer["negotiated"] = True
        if (random.randint(1, 100) if roll is None else roll) <= chance:
            old_fee = fee
            offer["fee"] = round(old_fee * 1.12 / 100) * 100
            relationship = safe_int(offer.get("relationship", 50), 50)
            offer["relationship"] = min(100, relationship + 3)
            message = f"{offer.get('name', 'Sponsor')} accepted the counter: ${old_fee:,} → ${offer['fee']:,} per event."
            accepted = True
        else:
            finance["sponsor_offers"] = [row for row in finance.get("sponsor_offers", []) if row is not offer]
            finance.setdefault("sponsor_offer_history", []).insert(0, {**offer, "decision": "Counter declined", "month": self.month})
            message = f"{offer.get('name', 'Sponsor')} declined the counter and withdrew its offer."
            accepted = False
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: {message}")
        return accepted, message

    def media_offer_assessment(self, offer):
        if not isinstance(offer, dict):
            return {"score": 0, "verdict": "Select an offer", "gross": 0, "risk": 0}
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback
        fee = max(0, safe_int(offer.get("fee", 0)))
        events_total = max(0, safe_int(offer.get("events_total", 0)))
        gross = fee * events_total
        standards_gap = max(0, safe_int(offer.get("minimum_rating", 0)) - safe_int(getattr(self, "company_pop", 0)))
        risk = min(100, standards_gap * 3 + max(0, safe_int(offer.get("min_production", 0)) - safe_int(getattr(self, "company_stability", 0))) * 2)
        score = round(safe_int(offer.get("reach", 0)) * .35 + min(100, gross / 25_000) * .35
                      + safe_int(offer.get("relationship", 50), 50) * .20 + (100-risk) * .10)
        verdict = "PREMIUM OPPORTUNITY" if score >= 75 else "BALANCED DEAL" if score >= 58 else "DEMANDING TERMS" if risk >= 40 else "LIMITED UPSIDE"
        return {"score": score, "verdict": verdict, "gross": gross, "risk": risk}

    def show_selected_media_offer(self):
        if not hasattr(self, "media_offer_verdict"):
            return
        selected = self.media_offers_tree.selection() if hasattr(self, "media_offers_tree") else ()
        offer = getattr(self, "_media_offer_rows", {}).get(selected[0]) if selected else None
        # This is a presentation reader. State repair belongs to the monthly
        # media boundary or an explicit player action, not selecting a row.
        finance = getattr(self, "finance", {})
        if not isinstance(finance, dict):
            finance = {}
        offers = finance.get("media_offers", [])
        if not isinstance(offers, list):
            offers = []
        if not isinstance(offer, dict):
            offer_id = self._selected_media_offer_id()
            offer = next((row for row in offers if isinstance(row, dict) and str(row.get("id", "") or "") == str(offer_id or "")), None)
        assessment = self.media_offer_assessment(offer)
        self.media_offer_verdict.config(text=assessment["verdict"])
        if offer:
            counter = "COUNTER COMPLETE" if offer.get("negotiated") else "COUNTER AVAILABLE"
            self.media_offer_numbers.config(text=f"VALUE {assessment['score']}/100  •  GROSS ${assessment['gross']:,}  •  DELIVERY RISK {assessment['risk']}/100  •  {counter}")
        else:
            self.media_offer_numbers.config(text="Compare reach, guarantee and delivery standards")

    def media_counter_selected_offer(self):
        offer_id = self._selected_media_offer_id()
        finance = self.ensure_player_media_state()
        offer = next((row for row in finance.get("media_offers", []) if row.get("id") == offer_id), None)
        if not offer:
            self._media_rights_notice("Select a live rights offer before negotiating.", warning=True)
            return
        stance = self.media_negotiation_stance.get() if hasattr(self, "media_negotiation_stance") else "Higher Guarantee"
        ok, message = self.counter_player_media_offer(offer_id, stance)
        self._media_rights_notice(message, warning=not ok)
        self.refresh_all()

    def counter_player_media_offer(self, offer_id, stance, roll=None):
        """Resolve one rights counter while preserving the legacy offer fields."""
        finance = self.ensure_player_media_state()
        offers = finance.get("media_offers", [])
        if not isinstance(offers, list):
            offers = []
        offer = next((row for row in offers if isinstance(row, dict) and row.get("id") == offer_id), None)
        if not offer:
            return False, "That media-rights offer is no longer available."
        if offer.get("negotiated"):
            return False, f"{offer.get('name', 'Media outlet')} has already answered one counteroffer."
        valid_stances = ("Higher Guarantee", "Wider Reach", "Lower Standards", "Shorter Commitment")
        if stance not in valid_stances:
            stance = "Higher Guarantee"
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback
        required = {
            "fee": safe_int(offer.get("fee"), None), "reach": safe_int(offer.get("reach"), None),
            "minimum_rating": safe_int(offer.get("minimum_rating"), None),
            "min_card_quality": safe_int(offer.get("min_card_quality"), None),
            "months": safe_int(offer.get("months"), None),
            "events_total": safe_int(offer.get("events_total"), None),
            "relationship": safe_int(offer.get("relationship", 50), None),
            "market_score": safe_int(offer.get("market_score", 0), None),
            "company_pop": safe_int(getattr(self, "company_pop", 0), None),
            "company_stability": safe_int(getattr(self, "company_stability", 0), None),
        }
        if (any(value is None for value in required.values()) or required["months"] <= 0 or
                required["events_total"] <= 0):
            offer.setdefault("offer_review_required", True)
            offer.setdefault("offer_review_reason", "Media fee, standards or commitment evidence is malformed.")
            return False, "That media-rights offer has malformed terms and needs review before negotiation."
        chance = max(18, min(88, round(28 + required["relationship"] * .35 + required["company_pop"] * .18
                                      + required["company_stability"] * .12 + required["market_score"] * .12)))
        offer["negotiated"] = True
        if (random.randint(1, 100) if roll is None else roll) <= chance:
            if stance == "Higher Guarantee": offer["fee"] = round(required["fee"] * 1.12 / 1000) * 1000
            elif stance == "Wider Reach": offer["reach"] = min(99, required["reach"] + 5)
            elif stance == "Lower Standards":
                offer["minimum_rating"] = max(20, required["minimum_rating"] - 5); offer["min_card_quality"] = max(20, required["min_card_quality"] - 4)
            elif stance == "Shorter Commitment":
                offer["months"] = max(6, required["months"] - 4); offer["events_total"] = max(4, required["events_total"] - 2); offer["events_remaining"] = offer["events_total"]
            offer["guarantee_per_event"] = offer.get("fee", offer.get("guarantee_per_event", 0))
            offer.setdefault("production_tier", self.media_contract_terms(offer).get("production_tier", "Standard"))
            offer.setdefault("terms_version", 1)
            offer["relationship"] = min(100, required["relationship"] + 2)
            message = f"{offer.get('name', 'Media outlet')} accepted your {stance.lower()} counteroffer."
            accepted = True
        else:
            finance["media_offers"] = [row for row in finance.get("media_offers", []) if row is not offer]
            finance.setdefault("media_offer_history", []).insert(0, {**offer, "status": "Counter declined"})
            outlet_id = offer.get("outlet_id", "")
            finance["media_relationships"][outlet_id] = max(0, safe_int(finance["media_relationships"].get(outlet_id, 50), 50) - 3)
            message = f"{offer.get('name', 'Media outlet')} rejected the counter and withdrew its offer."
            accepted = False
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: {message}")
        return accepted, message

    def accept_sponsor_offer(self):
        finance = self.ensure_player_media_state()
        offer = self.selected_sponsor_offer()
        if not offer:
            finance["sponsor_market_note"] = "Select a live sponsor offer first."
            self.refresh_finance()
            return
        deals = finance.get("sponsor_deals", [])
        if not isinstance(deals, list):
            deals = []
        malformed_deals = [deal for deal in deals if not isinstance(deal, dict)]
        if malformed_deals:
            finance.setdefault("sponsor_deal_review_required", True)
            finance.setdefault("sponsor_deal_review_reason", "One or more saved sponsor agreements are malformed.")
        if len(deals) >= 8:
            finance["sponsor_market_note"] = (
                "Sponsor portfolio is at its eight-deal capacity. End an existing agreement before signing this offer; "
                "no active deal will be removed automatically."
            )
            finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Sponsor offer blocked at eight-deal capacity.")
            self.refresh_finance()
            return False, finance["sponsor_market_note"]
        if any(isinstance(deal, dict) and deal.get("category") == offer.get("category") for deal in deals):
            finance["sponsor_market_note"] = f"An active {offer['category']} partner blocks this category."
            self.refresh_finance()
            return
        def safe_int(value, fallback=None):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            try:
                return int(value)
            except (TypeError, ValueError):
                return fallback
        fee = safe_int(offer.get("fee"), None)
        months = safe_int(offer.get("months"), None)
        if (not str(offer.get("name", "") or "").strip() or
                not str(offer.get("category", "") or "").strip() or fee is None or fee < 0 or
                months is None or months <= 0):
            offer.setdefault("offer_review_required", True)
            offer.setdefault("offer_review_reason", "Sponsor name, category, fee or term is malformed.")
            finance["sponsor_market_note"] = "That sponsor offer has malformed terms and needs review before signing."
            self.refresh_finance()
            return False, finance["sponsor_market_note"]
        deal = {key: value for key, value in offer.items() if key not in ("id", "expires_month")}
        deal["agreement_id"] = str(offer.get("id", "") or offer.get("name", "Sponsor"))
        deal["signed_month"] = int(self.month)
        self._sponsor_duty_for_deal(deal, create=True)
        finance.setdefault("sponsor_deals", []).insert(0, deal)
        finance["sponsor_deals"] = finance["sponsor_deals"][:8]
        finance["sponsor_offers"] = [row for row in finance.get("sponsor_offers", []) if not (isinstance(row, dict) and row.get("id") == offer.get("id"))]
        finance.setdefault("sponsor_offer_history", []).insert(0, {**offer, "decision": "Accepted", "month": self.month})
        finance["sponsor_offer_history"] = finance["sponsor_offer_history"][:60]
        finance["sponsor_market_note"] = f"Signed {deal['name']} for ${deal['fee']:,} per event over {deal['months']} months."
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Signed {deal['name']} ({deal['category']}) for ${deal['fee']:,}/event.")
        self.inbox.append({"subject": "Sponsor Signed", "body": finance["sponsor_market_note"], "type": "Business", "resolved": False})
        self.news.insert(0, f"{self.player_company_name} signs {deal['name']} as its {deal['category'].lower()} partner.")
        self.refresh_all()
        return True, finance["sponsor_market_note"]

    def reject_sponsor_offer(self):
        finance = self.ensure_player_media_state()
        offer = self.selected_sponsor_offer()
        if not offer:
            finance["sponsor_market_note"] = "Select a live sponsor offer first."
            self.refresh_finance()
            return
        finance["sponsor_offers"] = [row for row in finance.get("sponsor_offers", []) if not (isinstance(row, dict) and row.get("id") == offer.get("id"))]
        finance.setdefault("sponsor_offer_history", []).insert(0, {**offer, "decision": "Rejected", "month": self.month})
        finance["sponsor_market_note"] = f"Rejected {offer['name']}."
        self.refresh_finance()

    def refresh_media_dashboard(self):
        if not hasattr(self, "media_kpi_summary"):
            return
        # This path is a reader: no defaults, offer expiry, IDs or weekly
        # markers are repaired just because the player opened the desk.
        finance = self._media_finance_readonly()
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))
        audience_history = finance.get("media_audience_history", [])
        if not isinstance(audience_history, list):
            audience_history = []
        offers = finance.get("media_offers", [])
        if not isinstance(offers, list):
            offers = []
        campaigns = finance.get("media_campaign_history", [])
        if not isinstance(campaigns, list):
            campaigns = []
        if hasattr(self, "refresh_media_plan_targets"):
            self.refresh_media_plan_targets()
        # Offers are created by the monthly media cycle and by the negotiate
        # action, never by drawing this dashboard. Generating them here made a
        # screen redraw consume simulation RNG and change later outcomes.
        # Do not roll the weekly action marker merely because the player opened
        # or refreshed the Media Desk. The action owner advances that marker
        # when a campaign is committed; this read model only reports it.
        remaining = self.media_actions_remaining_readonly()
        active = self.active_media_contract()
        recent = next((row for row in audience_history if isinstance(row, dict)), None)
        rating = f" | Last rating {safe_int(recent.get('rating', 0))} ({safe_int(recent.get('viewers', 0)):,} viewers)" if recent else ""
        rights_reach = safe_int(active.get("reach", 0)) if isinstance(active, dict) else 0
        strategy = str(finance.get("media_strategy", "Balanced") or "Balanced")
        company_buzz = safe_int(finance.get("media_company_buzz", 20), 20)
        public_trust = safe_int(finance.get("media_public_trust", 55), 55)
        self.media_kpi_summary.config(text=f"Actions {remaining}/{self.media_action_capacity()} | Strategy {strategy} | Company buzz {company_buzz} | Public trust {public_trust} | Rights reach {rights_reach}{rating}")
        if hasattr(self, "media_strategy_choice"):
            self.media_strategy_choice.set(strategy)
        action = self.media_action_choice.get() if hasattr(self, "media_action_choice") else "Interview"
        fighter = self.media_desk_fighter() if hasattr(self, "media_desk_fighter") else None
        self.media_action_summary.config(text=self.media_action_preview(action, fighter))
        if active:
            terms = self.media_contract_terms(active)
            requirements = f"rating {safe_int(active.get('minimum_rating', 0))}+, card {safe_int(active.get('min_card_quality', 0))}+, production {terms['minimum_production']}+"
            warning = f" | {terms['warning']}" if terms.get("warning") else ""
            rights_text = (f"ACTIVE: {str(active.get('name', 'Rights partner') or 'Rights partner')} | ${terms['canonical_fee']:,}/event ({terms['payment_basis']}) | reach {safe_int(active.get('reach', 0))} | "
                           f"{terms['events_remaining']}/{safe_int(active.get('events_total', 0))} events | {terms['months']} months | relationship {safe_int(active.get('relationship', 50), 50)} | "
                           f"strikes {safe_int(active.get('breach_strikes', 0))}/3 | Contract standard {terms['production_tier']} | Requires {requirements}{warning}")
        else:
            rights_text = "No active rights package. Events receive only the reach of their paid production provider; future offers depend on stability, stars, ratings, and outlet relationships."
            history_rows = self.media_contract_history_readonly(limit=4)
            terminal = next((row for row in history_rows if row.get("lifecycle_status") != "Active"), None)
            if terminal:
                rights_text += (f" Last deal: {terminal.get('name', 'Rights partner')} — "
                                f"{terminal.get('lifecycle_status', terminal.get('status', 'Unknown'))}.")
        if hasattr(self, "media_account_review"):
            history = [row for row in audience_history if isinstance(row, dict)]
            if active:
                active_name = str(active.get("name", "") or "")
                relevant, unscoped = self.media_contract_delivery_history(active, history)
                delivered = sum(1 for row in relevant if row.get("delivered"))
                shortfalls = [row for row in relevant if not row.get("delivered")]
                strikes = safe_int(active.get("breach_strikes", 0))
                active_months = safe_int(active.get("months", 0))
                active_events = safe_int(active.get("events_remaining", 0))
                deadline = "Renewal review due now" if active_months <= 2 or active_events <= 2 else f"{active_months} contract month(s) remaining"
                shortfall_text = "No recorded shortfall" if not shortfalls else "; ".join(
                    f"{row.get('event', 'Event')}: {row.get('reason', 'delivery missed')}"
                    for row in shortfalls[:2]
                )
                successor = finance.get("media_successor_contract")
                successor_offer = finance.get("media_successor_offer")
                successor_text = (
                    f"Successor queued ({successor.get('name', 'outlet')})" if isinstance(successor, dict) and successor.get("status") == "Pending" else
                    f"Successor needs review: {successor.get('needs_review_reason', 'predecessor shortfall')}" if isinstance(successor, dict) and successor.get("status") == "Needs review" else
                    f"Successor offer ready ({successor_offer.get('name', 'outlet')})" if isinstance(successor_offer, dict) and successor_offer.get("status") == "Offer" else
                    "No successor queued"
                )
                evidence_text = f" | {unscoped} legacy unscoped row(s) excluded" if unscoped else ""
                self.media_account_review.config(text=(
                    f"ACCOUNT REVIEW  |  {active_name}: {delivered} delivered / {len(relevant)} recorded | "
                    f"{active_events} event(s) still owed | strikes {strikes}/3 | {deadline}{evidence_text}\n"
                    f"Shortfalls: {shortfall_text} | {successor_text}. Evidence is historical/read-only; refresh does not settle or repair the contract."
                ))
            else:
                history_rows = self.media_contract_history_readonly(limit=4)
                terminal = next((row for row in history_rows if row.get("lifecycle_status") != "Active"), None)
                if terminal:
                    self.media_account_review.config(text=(
                        f"ACCOUNT REVIEW  |  No active rights contract. Last deal: {terminal.get('name', 'Rights partner')} — "
                        f"{terminal.get('lifecycle_status', terminal.get('status', 'Unknown'))}; "
                        f"{terminal.get('events_remaining', 0)} event(s) remained owed, {terminal.get('breach_strikes', 0)} delivery strike(s)."
                    ))
                else:
                    self.media_account_review.config(text="ACCOUNT REVIEW  |  No active rights contract. Sign or renew a package to begin tracking delivery evidence.")
        receipts = finance.get("media_commercial_receipts", [])
        if not isinstance(receipts, list):
            receipts = []
        latest_receipt = next((row for row in receipts if isinstance(row, dict)), None)
        if latest_receipt:
            receipt_rights = latest_receipt.get("rights", {}) if isinstance(latest_receipt.get("rights", {}), dict) else {}
            rights_text += (f" | Latest receipt: {latest_receipt.get('event', 'Event')} — rights ${safe_int(receipt_rights.get('amount', 0)):,}, "
                            f"sponsors ${safe_int(latest_receipt.get('sponsor_total', 0)):,}; settled receipts are read-only.")
        renewal_offer = finance.get("media_successor_offer")
        renewal_pending = finance.get("media_successor_contract")
        if isinstance(renewal_pending, dict) and renewal_pending.get("status") == "Pending":
            rights_text += f" Renewal queued with {renewal_pending.get('name', 'the outlet')} and starts after this deal completes."
        elif isinstance(renewal_pending, dict) and renewal_pending.get("status") == "Needs review":
            rights_text += f" Renewal needs review: {renewal_pending.get('needs_review_reason', 'predecessor ended with a shortfall')}."
        elif isinstance(renewal_offer, dict) and renewal_offer.get("status") == "Offer":
            rights_text += f" Renewal offer ready from {renewal_offer.get('name', 'the outlet')}; accept it to queue a non-overlapping successor."
        self.media_rights_summary.config(text=rights_text)
        selected = self.media_offers_tree.selection()
        prior_offer_key = ""
        if selected:
            prior_offer = getattr(self, "_media_offer_rows", {}).get(selected[0])
            if isinstance(prior_offer, dict):
                prior_offer_key = self._media_offer_identity_key(prior_offer)
        self.media_offers_tree.delete(*self.media_offers_tree.get_children())
        self._media_offer_rows = {}
        used_offer_ids = set()
        retained_offer_id = ""
        for index, offer in enumerate(offers):
            if not isinstance(offer, dict):
                row_id = self._media_offer_view_id(offer, fallback_index=index)
                duplicate = 2
                while row_id in used_offer_ids:
                    row_id = f"{self._media_offer_view_id(offer, fallback_index=index)}#{duplicate}"
                    duplicate += 1
                used_offer_ids.add(row_id)
                self._media_offer_rows[row_id] = offer
                self.media_offers_tree.insert("", "end", iid=row_id, tags=("risk",), values=("Unavailable offer", "—", "Unknown", "Unknown", "Unknown", "Unknown", "Malformed retained offer"))
                continue
            base_id = self._media_offer_view_id(offer, fallback_index=index)
            row_id = base_id
            duplicate = 2
            while row_id in used_offer_ids:
                row_id = f"{base_id}#{duplicate}"
                duplicate += 1
            used_offer_ids.add(row_id)
            self._media_offer_rows[row_id] = offer
            if prior_offer_key and self._media_offer_identity_key(offer, index=index) == prior_offer_key and not retained_offer_id:
                retained_offer_id = row_id
            expiry_month = safe_int(offer.get("expires_month", getattr(self, "month", 1)), getattr(self, "month", 1))
            expiry = self.format_game_date(expiry_month, 1, include_week=False)
            req = f"Rating {safe_int(offer.get('minimum_rating', 0))} / card {safe_int(offer.get('min_card_quality', 0))} / production {safe_int(offer.get('min_production', 0))} | {str(offer.get('exclusivity', 'Unknown') or 'Unknown')} | expires {expiry}"
            self.media_offers_tree.insert("", "end", iid=row_id, values=(str(offer.get("name", "Media offer") or "Media offer"), str(offer.get("type", "Rights") or "Rights"), safe_int(offer.get("reach", 0)), f"${max(0, safe_int(offer.get('fee', 0))):,}", f"{max(0, safe_int(offer.get('months', 0)))} mo", safe_int(offer.get("events_total", 0)), req))
        if retained_offer_id:
            self.media_offers_tree.selection_set(retained_offer_id)
        elif self.media_offers_tree.get_children():
            self.media_offers_tree.selection_set(self.media_offers_tree.get_children()[0])
        self.show_selected_media_offer()
        previous_campaign_key = ""
        selected_campaign = self.media_campaign_history_tree.selection()
        if selected_campaign:
            previous_row = getattr(self, "_media_campaign_rows", {}).get(selected_campaign[0])
            previous_campaign_key = self._media_campaign_identity_key(previous_row)
        self.media_campaign_history_tree.delete(*self.media_campaign_history_tree.get_children())
        self._media_campaign_rows = {}
        used_campaign_ids = set()
        retained_campaign_id = ""
        for index, row in enumerate(campaigns[:60]):
            if not isinstance(row, dict):
                row_id = self._media_campaign_view_id(row, fallback_index=index)
                duplicate = 2
                while row_id in used_campaign_ids:
                    row_id = f"{self._media_campaign_view_id(row, fallback_index=index)}#{duplicate}"
                    duplicate += 1
                used_campaign_ids.add(row_id)
                self._media_campaign_rows[row_id] = row
                self.media_campaign_history_tree.insert("", "end", iid=row_id, tags=("risk",), values=("Unavailable", "—", "—", "—", "—", "Malformed retained campaign", "—", "Unknown"))
                continue
            base_id = self._media_campaign_view_id(row, fallback_index=index)
            row_id = base_id
            duplicate = 2
            while row_id in used_campaign_ids:
                row_id = f"{base_id}#{duplicate}"
                duplicate += 1
            used_campaign_ids.add(row_id)
            self._media_campaign_rows[row_id] = row
            if previous_campaign_key and self._media_campaign_identity_key(row) == previous_campaign_key and not retained_campaign_id:
                retained_campaign_id = row_id
            self.media_campaign_history_tree.insert("", "end", iid=row_id, values=(self.format_game_date_text(row.get("date", "")), row.get("strategy", ""), row.get("action", ""), row.get("subject", ""), row.get("target", ""), row.get("outcome", ""), f"{safe_int(row.get('heat', 0)):+}", f"${max(0, safe_int(row.get('cost', 0))):,}"))
        if retained_campaign_id:
            self.media_campaign_history_tree.selection_set(retained_campaign_id)
        elif self.media_campaign_history_tree.get_children():
            self.media_campaign_history_tree.selection_set(self.media_campaign_history_tree.get_children()[0])
        self.show_selected_media_campaign()
        self.refresh_media_receipts()
        self.refresh_media_plan_summary()

    @staticmethod
    def _media_campaign_identity_key(row):
        """Return an at-the-time campaign identity without using its row position.

        Campaign history predates durable IDs, so an authored identifier wins
        when present and a content-bound digest is used for legacy mappings.
        Empty/malformed rows remain explicitly non-durable rather than being
        silently reassociated after sorting or a refresh.
        """
        if not isinstance(row, dict):
            return ""
        for field in ("campaign_id", "operation_id", "evidence_key"):
            value = str(row.get(field, "") or "").strip()
            if value:
                return f"media-campaign:{field}:{value}"
        payload = {
            key: row.get(key, "") for key in (
                "date", "month", "week", "strategy", "action", "subject", "target",
                "outcome", "band", "heat", "popularity", "trust", "cost",
            )
        }
        payload["raw_type"] = type(row).__name__
        digest = hashlib.sha1(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]
        return f"legacy-media-campaign:{digest}"

    @classmethod
    def _media_campaign_view_id(cls, row, fallback_index=0):
        """Build a stable presentation key for campaign history rows."""
        identity = cls._media_campaign_identity_key(row)
        if identity:
            return identity
        raw = f"{type(row).__name__}:{row!s}"
        digest = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:20]
        return f"legacy-media-campaign:{digest}"

    def show_selected_media_campaign(self, _event=None):
        """Project the selected campaign into a readable, immutable brief."""
        detail = getattr(self, "media_campaign_detail", None)
        if detail is None:
            return
        tree = getattr(self, "media_campaign_history_tree", None)
        selected = tree.selection() if tree is not None else ()
        row = getattr(self, "_media_campaign_rows", {}).get(selected[0]) if selected else None
        if not isinstance(row, dict):
            detail.config(text="Select a campaign to inspect its retained outcome. Malformed legacy rows remain visible but have no detail projection.")
            return
        identity = self._media_campaign_identity_key(row)
        identity_text = identity or "Legacy history — no durable campaign identity was stored"
        try:
            raw_cost = row.get("cost", 0) or 0
            cost = int(raw_cost)
            if isinstance(raw_cost, float) and not math.isfinite(raw_cost):
                raise ValueError("non-finite cost")
            cost = max(-1_000_000_000, min(1_000_000_000, cost))
        except (TypeError, ValueError, OverflowError):
            cost = 0
        try:
            raw_heat = row.get("heat", 0) or 0
            heat = int(raw_heat)
            if isinstance(raw_heat, float) and not math.isfinite(raw_heat):
                raise ValueError("non-finite heat")
            heat = max(-100, min(100, heat))
        except (TypeError, ValueError, OverflowError):
            heat = 0
        detail.config(text=(
            f"{row.get('date', 'Date')} · {row.get('action', 'Campaign')} · {row.get('subject', 'Spokesperson')} → {row.get('target', '—')} | "
            f"{row.get('band', 'Outcome')} | Heat {heat:+} | Cost ${max(0, cost):,}\n"
            f"{row.get('outcome', 'No retained outcome text.')} | {identity_text}. This campaign record is read-only."
        ))

    def refresh_media_receipts(self):
        if not hasattr(self, "media_receipts_tree"):
            return
        # This is a read-model refresh.  Do not normalise finance or rebuild
        # offers while the player is only inspecting settled evidence.
        finance = getattr(self, "finance", {})
        if not isinstance(finance, dict):
            finance = {}
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))
        selected = self.media_receipts_tree.selection()
        prior_key = ""
        if selected:
            prior_row = getattr(self, "_media_receipt_rows", {}).get(selected[0], {})
            if isinstance(prior_row, dict):
                prior_key = self._media_receipt_identity_key(prior_row)
        self.media_receipts_tree.delete(*self.media_receipts_tree.get_children())
        rows = finance.get("media_commercial_receipts", []) or []
        if not isinstance(rows, list):
            rows = []
        self._media_receipt_rows = {}
        used_ids = set()
        for index, receipt in enumerate(rows[:120]):
            if not isinstance(receipt, dict):
                row_id = self._media_receipt_view_id(receipt, fallback_index=index)
                duplicate = 2
                while row_id in used_ids:
                    row_id = f"{self._media_receipt_view_id(receipt, fallback_index=index)}#{duplicate}"
                    duplicate += 1
                used_ids.add(row_id)
                self._media_receipt_rows[row_id] = receipt
                self.media_receipts_tree.insert("", "end", iid=row_id, tags=("shortfall",), values=("Unavailable", "Malformed retained receipt", "Unknown", "Unknown", "REVIEW"))
                continue
            rights = receipt.get("rights", {}) if isinstance(receipt.get("rights", {}), dict) else {}
            review_required = bool(receipt.get("settlement_status") == "Needs review" or receipt.get("settlement_review"))
            delivery = "REVIEW" if review_required else "DELIVERED" if rights.get("delivered") else "SHORTFALL"
            base_id = self._media_receipt_view_id(receipt, index)
            row_id = base_id
            duplicate = 2
            while row_id in used_ids:
                row_id = f"{base_id}#{duplicate}"
                duplicate += 1
            used_ids.add(row_id)
            self._media_receipt_rows[row_id] = receipt
            tag = "review" if review_required else "delivered" if rights.get("delivered") else "shortfall"
            self.media_receipts_tree.insert("", "end", iid=row_id, tags=(tag,), values=(
                self.format_game_date_text(receipt.get("date", "")), receipt.get("event", "Event"),
                f"${safe_int(rights.get('amount', 0)):,}", f"${safe_int(receipt.get('sponsor_total', 0)):,}", delivery,
            ))
        retained = next(
            (row_id for row_id, row in self._media_receipt_rows.items()
             if prior_key and self._media_receipt_identity_key(row) == prior_key),
            "",
        )
        if retained:
            self.media_receipts_tree.selection_set(retained)
        elif self.media_receipts_tree.get_children():
            self.media_receipts_tree.selection_set(self.media_receipts_tree.get_children()[0])
        self.show_selected_media_receipt()

    @staticmethod
    def _media_receipt_identity_key(receipt):
        """Return the saved identity used to retain a receipt selection.

        A receipt ID is authoritative; event ID is the compatible secondary
        key.  Legacy rows without either identity use a deterministic
        retained-fact fingerprint so refreshes can preserve the same evidence
        without pretending that the key is a durable saved receipt ID.
        """
        if not isinstance(receipt, dict):
            return ""
        receipt_id = str(receipt.get("receipt_id", "") or "").strip()
        if receipt_id:
            return f"receipt:{receipt_id}"
        event_id = str(receipt.get("event_id", "") or "").strip()
        if event_id:
            return f"event:{event_id}"
        payload = {
            "date": receipt.get("date", ""),
            "month": receipt.get("month", ""),
            "week": receipt.get("week", ""),
            "event": receipt.get("event", ""),
            "company": receipt.get("company", ""),
            "rights": receipt.get("rights", {}),
            "sponsor_total": receipt.get("sponsor_total", ""),
            "settlement_status": receipt.get("settlement_status", ""),
        }
        if not any(value not in ("", None, [], {}) for value in payload.values()):
            return "legacy-receipt:empty"
        digest = hashlib.sha1(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]
        return f"legacy-receipt:{digest}"

    @classmethod
    def _media_receipt_view_id(cls, receipt, fallback_index=0):
        """Build a stable Treeview iid without inventing saved history IDs."""
        identity = cls._media_receipt_identity_key(receipt)
        if identity:
            return identity
        # Opaque non-mapping rows remain UI-only and are never resolved back
        # through a visible list position.
        raw = f"{type(receipt).__name__}:{receipt!s}"
        digest = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:20]
        return f"legacy-receipt:{digest}"

    def _selected_media_receipt(self):
        tree = getattr(self, "media_receipts_tree", None)
        if tree is None:
            return None
        selected = tree.selection()
        if not selected:
            return None
        row = getattr(self, "_media_receipt_rows", {}).get(selected[0])
        if row is not None:
            return row
        # A stale/pre-upgrade Treeview ID is not a safe source reference.  Do
        # not resolve it through the current visible list position.
        return None

    def media_commercial_receipt_details(self, *, receipt_id="", event_id=""):
        """Return one immutable commercial receipt package for UI inspection.

        Settlement receipts are already the authoritative historical record.
        This read model follows the receipt to its audience outcome and any
        sponsor-duty history without calling ``ensure_player_media_state`` or
        rebuilding offers.  It is therefore safe for refreshes and detail
        windows, including when a legacy save has no linked history row.
        """
        finance = getattr(self, "finance", {})
        if not isinstance(finance, dict):
            return None
        rows = finance.get("media_commercial_receipts", [])
        if not isinstance(rows, list):
            return None
        wanted_receipt = str(receipt_id or "")
        wanted_event = str(event_id or "")
        receipt = next(
            (row for row in rows if isinstance(row, dict) and (
                (wanted_receipt and str(row.get("receipt_id", "") or "") == wanted_receipt)
                or (wanted_event and str(row.get("event_id", "") or "") == wanted_event)
            )),
            None,
        )
        if receipt is None:
            return None
        resolved_event = str(receipt.get("event_id", "") or "")
        rights = receipt.get("rights", {}) if isinstance(receipt.get("rights", {}), dict) else {}
        receipt_contract_id = str(rights.get("contract_id", "") or "").strip()
        receipt_outlet_id = str(rights.get("outlet_id", "") or "").strip()
        audience_rows = finance.get("media_audience_history", [])
        if not isinstance(audience_rows, list):
            audience_rows = []
        event_rows = [
            row for row in audience_rows
            if isinstance(row, dict) and (
                not resolved_event or str(row.get("event_id", "") or "") == resolved_event
            )
        ]

        # Identity-bearing evidence wins over event/name matching.  This keeps
        # two contracts sharing an outlet label from cross-linking in the
        # account reader.  Only rows with no saved identity participate in the
        # explicit legacy fallback.
        audience = None
        if receipt_contract_id:
            audience = next(
                (row for row in event_rows
                 if isinstance(row, dict)
                 and str(row.get("contract_id", "") or "").strip() == receipt_contract_id),
                None,
            )
        if audience is None and receipt_outlet_id:
            audience = next(
                (row for row in event_rows
                 if isinstance(row, dict)
                 and str(row.get("outlet_id", "") or "").strip() == receipt_outlet_id
                 and (not receipt_contract_id or not str(row.get("contract_id", "") or "").strip())),
                None,
            )
        if audience is None:
            if receipt_contract_id or receipt_outlet_id:
                audience = next(
                    (row for row in event_rows
                     if not str(row.get("contract_id", "") or "").strip()
                     and not str(row.get("outlet_id", "") or "").strip()),
                    None,
                )
            else:
                audience = event_rows[0] if event_rows else None
        duty_history = [
            row for row in (finance.get("sponsor_duty_history", []) if isinstance(finance.get("sponsor_duty_history", []), list) else [])
            if isinstance(row, dict) and (
                str(row.get("event_id", "") or "") == resolved_event
                or str(row.get("receipt_id", "") or "") == str(receipt.get("receipt_id", "") or "")
            )
        ]
        return {
            "receipt": deepcopy(receipt),
            "audience": deepcopy(audience) if isinstance(audience, dict) else None,
            "duty_history": deepcopy(duty_history),
        }

    def show_selected_media_receipt(self):
        if not hasattr(self, "media_receipt_detail"):
            return
        receipt = self._selected_media_receipt()
        if not isinstance(receipt, dict):
            self.media_receipt_detail.config(text="No settled receipts yet. A receipt is created once at event settlement and cannot be edited by reopening it.")
            return
        rights = receipt.get("rights", {}) if isinstance(receipt.get("rights", {}), dict) else {}
        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))
        sponsor_lines = []
        sponsors = receipt.get("sponsors", [])
        if not isinstance(sponsors, list):
            sponsors = []
        for row in sponsors:
            if not isinstance(row, dict):
                sponsor_lines.append("Unavailable retained sponsor duty")
                continue
            amount = safe_int(row.get("amount", 0) or 0)
            sponsor_lines.append(f"{row.get('name', 'Sponsor')}: ${amount:,} {row.get('status', 'Unknown')} ({row.get('reason', '')})")
        rights_amount = safe_int(rights.get("amount", 0) or 0)
        sponsor_total = safe_int(receipt.get("sponsor_total", 0) or 0)
        relationship_delta = safe_int(receipt.get("relationship_delta", 0) or 0)
        sponsor_text = "; ".join(sponsor_lines) if sponsor_lines else "No sponsor entitlements"
        review_note = str(receipt.get("settlement_review", "") or "").strip()
        review_text = f" Data quality review: {review_note}." if review_note else ""
        self.media_receipt_detail.config(text=(
            f"{receipt.get('event', 'Event')} | Rights: {rights.get('outlet', 'No rights partner')} ${rights_amount:,} — "
            f"{rights.get('reason', 'No additional delivery note.')} | Production {rights.get('production_tier', 'Standard')} ({rights.get('production_quality', 45)}/100). "
            f"Sponsors: {sponsor_text}. Sponsor total ${sponsor_total:,}. Relationship change {relationship_delta:+}.{review_text} This record is immutable after settlement."
        ))

    def media_open_selected_receipt(self):
        """Open the selected settlement receipt as a structured read-only brief."""
        receipt = self._selected_media_receipt()
        if not isinstance(receipt, dict):
            self._media_receipt_notice("Select a settled receipt first.")
            return None
        detail_fn = getattr(self, "media_commercial_receipt_details", None)
        detail = None
        if callable(detail_fn):
            detail = detail_fn(receipt_id=receipt.get("receipt_id", ""), event_id=receipt.get("event_id", ""))
        if not detail and not self._media_receipt_identity_key(receipt):
            # Preserve the complete legacy row in the reader while making its
            # missing durable identity explicit instead of guessing one.
            detail = {"receipt": deepcopy(receipt), "audience": None, "duty_history": []}
        if not detail:
            self._media_receipt_notice("The selected receipt is no longer available in the current save.", warning=True)
            return None

        window = self.create_managed_window(key="media-commercial-receipt", parent=getattr(self, "root", None))
        window.title("MMA Warriors - Settlement Receipt")
        window.geometry("900x660")
        window.minsize(720, 500)
        window.configure(bg=self.colors["chrome"])
        receipt = detail.get("receipt", {})
        rights = receipt.get("rights", {}) if isinstance(receipt.get("rights"), dict) else {}
        delivery = "DELIVERED" if rights.get("delivered") else "SHORTFALL"
        ttk.Label(window, text=f"{receipt.get('event', 'Event')}  ·  {delivery}", style="Title.TLabel", anchor="w").pack(fill="x", padx=14, pady=(12, 1))
        receipt_id = str(receipt.get("receipt_id", "") or "").strip()
        event_id = str(receipt.get("event_id", "") or "").strip()
        if receipt_id or event_id:
            identity_text = f"Receipt: {receipt_id or '—'}    Event: {event_id or '—'}"
        else:
            identity_text = "Legacy history — no durable receipt/event ID was stored; full payload retained, re-association unavailable"
        ttk.Label(window, text=f"{receipt.get('date', 'Date')}    {identity_text}", style="Inset.TLabel", anchor="w", justify="left").pack(fill="x", padx=14, pady=(0, 8))
        body = ttk.Frame(window, style="Inset.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        scrollbar = ttk.Scrollbar(body, orient="vertical")
        text = tk.Text(body, wrap="word", yscrollcommand=scrollbar.set, font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=10)
        scrollbar.configure(command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        def safe_int(value, fallback=0):
            if isinstance(value, bool) or value is None or value == "":
                return fallback
            if isinstance(value, float) and not math.isfinite(value):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(-1_000_000_000, min(1_000_000_000, parsed))

        lines = [
            "SETTLEMENT SUMMARY",
            "=" * 68,
            f"Delivery: {delivery}",
            f"Rights partner: {rights.get('outlet', 'No rights partner')}",
            f"Rights income: ${safe_int(rights.get('amount', 0)):,}",
            f"Delivery note: {rights.get('reason', 'No additional delivery note.') or 'No additional delivery note.'}",
            f"Production: {rights.get('production_tier', 'Standard')} — quality {rights.get('production_quality', 0)}/100; required {rights.get('required_production', 0)}/100",
            f"Sponsor total: ${safe_int(receipt.get('sponsor_total', 0)):,}",
            f"Relationship change: {safe_int(receipt.get('relationship_delta', 0)):+}",
        ]
        audience = detail.get("audience") if isinstance(detail.get("audience"), dict) else None
        if audience:
            lines.extend(("", "AUDIENCE OUTCOME", "-" * 68))
            for key in ("rating", "viewers", "exposure_delta", "campaign_lift", "eligible", "delivered"):
                if key in audience:
                    label = key.replace("_", " ").title()
                    value = f"{audience[key]:,}" if key == "viewers" and isinstance(audience[key], int) else audience[key]
                    lines.append(f"{label}: {value}")
        sponsors = receipt.get("sponsors", []) if isinstance(receipt.get("sponsors"), list) else []
        lines.extend(("", "SPONSOR DUTIES", "-" * 68))
        if sponsors:
            for sponsor in sponsors:
                if not isinstance(sponsor, dict):
                    lines.append(f"- {sponsor}")
                    continue
                lines.append(f"- {sponsor.get('name', 'Sponsor')} | ${safe_int(sponsor.get('amount', 0)):,} | {sponsor.get('status', 'Unknown')} | {sponsor.get('reason', 'No reason recorded')}")
                lines.append(f"  Duty status: {sponsor.get('duty_status', 'Legacy')} | Evidence: {sponsor.get('evidence_key', 'None') or 'None'}")
        else:
            lines.append("- No sponsor entitlements recorded.")
        history = detail.get("duty_history", []) if isinstance(detail.get("duty_history"), list) else []
        if history:
            lines.append("Duty-period history:")
            for row in history:
                if isinstance(row, dict):
                    lines.append(f"- {row.get('duty_id', 'Duty')} | {row.get('status', 'Unknown')} | {row.get('reason', 'No reason recorded')}")
        lines.extend(("", "FULL STORED PAYLOAD", "-" * 68, json.dumps(detail, indent=2, ensure_ascii=False, default=str)))
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")
        ttk.Button(window, text="Close", command=window.destroy).pack(anchor="e", padx=14, pady=(0, 12))
        return window

    def media_desk_callout(self):
        if hasattr(self, "media_action_choice"):
            self.media_action_choice.set("Call Out")
        self.media_run_selected_campaign()

    def media_desk_interview(self):
        if hasattr(self, "media_action_choice"):
            self.media_action_choice.set("Interview")
        self.media_run_selected_campaign()

    def media_desk_press_tour(self):
        if hasattr(self, "media_action_choice"):
            self.media_action_choice.set("Press Tour")
        self.media_run_selected_campaign()
