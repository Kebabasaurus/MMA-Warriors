import random
import tkinter as tk
from tkinter import messagebox

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
        converted = []
        for index, row in enumerate(custom):
            if not isinstance(row, dict) or not row.get("name"):
                continue
            name = str(row["name"])
            slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
            reach = max(1, min(99, int(row.get("reach", 25))))
            converted.append({
                "id": row.get("id", slug or f"custom_media_{index}"), "name": name,
                "type": row.get("type", "Streaming"), "home_region": row.get("home_region", "Worldwide"),
                "markets": list(row.get("markets", REGIONS)), "reach": reach,
                "prestige": int(row.get("prestige", reach)), "budget": int(row.get("budget", reach)),
                "selectivity": int(row.get("selectivity", max(12, reach - 8))),
                "min_popularity": int(row.get("min_popularity", max(8, reach - 24))),
                "min_card_quality": int(row.get("min_card_quality", max(35, reach - 12))),
                "min_production": int(row.get("min_production", max(20, reach - 18))),
                "base_fee": int(row.get("base_fee", row.get("fee", 10_000))),
                "editorial_style": row.get("editorial_style", "General fight coverage"),
                "audience": row.get("audience", "Fight fans"), "active": bool(row.get("active", True)),
                "volatility": int(row.get("volatility", 15)),
            })
        # Custom universe entries override same-name defaults but the wider
        # market remains populated for old three-package databases.
        by_name = {row["name"].lower(): row for row in defaults}
        for row in converted:
            by_name[row["name"].lower()] = row
        return list(by_name.values())

    def ensure_media_system(self):
        existing = list(getattr(self, "media_companies", []) or [])
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
        self.media_market_last_month = int(getattr(self, "media_market_last_month", 0) or 0)
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

    def _media_company_values(self, promotion=None):
        if promotion is None:
            roster = getattr(self, "roster", [])
            return self.player_company_name, self.player_region, self.company_pop, self.company_stability, self.cash, roster
        return promotion.name, promotion.region, promotion.reputation_score, promotion.stability, promotion.cash, promotion.roster

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
        finance.setdefault("media_relationships", {})
        finance.setdefault("media_strategy", "Balanced")
        finance.setdefault("media_last_offer_month", 0)
        finance.setdefault("media_action_week", -1)
        finance.setdefault("media_actions_used", 0)
        finance.setdefault("media_public_trust", 55)
        finance.setdefault("media_company_buzz", 20)
        finance.setdefault("media_popularity_month", {})
        finance.setdefault("sponsor_offers", [])
        finance.setdefault("sponsor_offer_history", [])
        finance.setdefault("sponsor_last_pitch_month", -1)
        legacy = finance.get("media_rights")
        if not isinstance(legacy, dict):
            legacy = self._empty_media_rights()
            finance["media_rights"] = legacy
        legacy.setdefault("months", 0)
        legacy.setdefault("fee", legacy.get("guarantee_per_event", 0))
        legacy.setdefault("guarantee_per_event", legacy.get("fee", 0))
        legacy.setdefault("reach", 0)
        # Old active contracts shipped without an event quota.  They should
        # continue paying rather than becoming silently inactive on load.
        if "events_remaining" not in legacy:
            legacy["events_remaining"] = max(1, min(24, int(legacy.get("months", 0)))) if legacy.get("months", 0) > 0 else 0
        legacy.setdefault("events_total", legacy.get("events_remaining", 0))
        active_contracts = [item for item in finance["media_contracts"] if item.get("status", "Active") == "Active" and item.get("months", 0) > 0 and item.get("events_remaining", 0) > 0]
        if legacy.get("months", 0) > 0 and legacy.get("events_remaining", 0) > 0 and legacy.get("name") not in ("", "No rights package") and not active_contracts:
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
        self.sync_legacy_media_rights(promotion)
        return finance

    def ensure_player_media_state(self):
        return self._ensure_media_state(None)

    def ensure_ai_media_state(self, promo):
        return self._ensure_media_state(promo)

    def active_media_contract(self, promotion=None):
        finance = self._media_finance(promotion)
        return next((item for item in finance.get("media_contracts", []) if item.get("status", "Active") == "Active" and item.get("months", 0) > 0 and item.get("events_remaining", 0) > 0), None)

    def sync_legacy_media_rights(self, promotion=None):
        finance = self._media_finance(promotion)
        active = self.active_media_contract(promotion)
        finance["media_rights"] = active if active else self._empty_media_rights()
        return finance["media_rights"]

    def media_action_capacity(self, promotion=None):
        if promotion is not None:
            strategy = getattr(promotion, "strategy", {}) or {}
            return 2 + (1 if strategy.get("commercial_strength", promotion.size) >= 70 else 0)
        marketing = self.staff_skill("Marketing") if hasattr(self, "staff_skill") else 45
        return 2 + (1 if marketing >= 68 else 0) + (1 if marketing >= 88 else 0)

    def media_actions_remaining(self, promotion=None):
        finance = self._ensure_media_state(promotion)
        marker = (int(self.month) - 1) * 4 + int(self.week)
        if finance.get("media_action_week") != marker:
            finance["media_action_week"] = marker
            finance["media_actions_used"] = 0
        return max(0, self.media_action_capacity(promotion) - int(finance.get("media_actions_used", 0)))

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
        if not force and finance.get("media_offers") and finance.get("media_last_offer_month", 0) >= self.month - 1:
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
            if offer.get("expires_month", self.month + 1) < self.month:
                expired = dict(offer); expired["status"] = "Expired"
                finance["media_offer_history"].insert(0, expired)
            else:
                kept.append(offer)
        finance["media_offers"] = kept[:12]
        finance["media_offer_history"] = finance["media_offer_history"][:40]
        return kept

    def _accept_media_offer(self, offer_id, promotion=None, counter=None):
        finance = self._ensure_media_state(promotion)
        offer = next((item for item in finance["media_offers"] if item.get("id") == offer_id), None)
        if not offer:
            return False, "That offer is no longer available."
        active = self.active_media_contract(promotion)
        buyout = active.get("termination_fee", 0) if active else 0
        if promotion is None:
            if buyout and self.cash < buyout:
                return False, f"Replacing the active deal requires a ${buyout:,} buyout."
            self.cash -= buyout
        elif buyout:
            if promotion.cash < buyout:
                return False, "The company cannot afford to replace its current deal."
            promotion.cash -= buyout
        if active:
            active["status"] = "Bought out"
        contract = dict(offer)
        if counter:
            contract.update(counter)
        contract["status"] = "Active"
        contract["signed_month"] = self.month
        contract["events_remaining"] = contract.get("events_total", contract.get("events_remaining", 1))
        finance["media_contracts"].insert(0, contract)
        finance["media_offers"] = [item for item in finance["media_offers"] if item.get("id") != offer_id]
        accepted = dict(offer); accepted["status"] = "Accepted"
        finance["media_offer_history"].insert(0, accepted)
        finance["media_relationships"][contract["outlet_id"]] = min(100, finance["media_relationships"].get(contract["outlet_id"], 50) + 4)
        self.sync_legacy_media_rights(promotion)
        return True, f"Signed {contract['name']}: ${contract['fee']:,}/event, reach {contract['reach']}, {contract['events_remaining']} events over {contract['months']} months."

    def accept_player_media_offer(self, offer_id, counter=None):
        return self._accept_media_offer(offer_id, None, counter)

    def reject_player_media_offer(self, offer_id):
        finance = self.ensure_player_media_state()
        offer = next((item for item in finance["media_offers"] if item.get("id") == offer_id), None)
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
        active["status"] = "Terminated"
        finance["media_relationships"][active.get("outlet_id", "")] = max(0, finance["media_relationships"].get(active.get("outlet_id", ""), 50) - 14)
        self.sync_legacy_media_rights()
        return True, f"Ended {active['name']} for ${cost:,}. The outlet relationship was damaged."

    def media_contract_eligibility(self, contract, event, promotion=None):
        if not contract or contract.get("status") != "Active" or contract.get("months", 0) <= 0 or contract.get("events_remaining", 0) <= 0:
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

    def _media_action_spec(self, action, fighter=None):
        specs = {
            "Interview": (1, 0, 7, 8), "Call Out": (1, 0, 11, 22),
            "Press Tour": (2, 12_000 + max(0, getattr(fighter, "popularity", 40) - 40) * 200, 18, 12),
            "Open Workout": (1, 4_000, 9, 7), "Highlight Package": (1, 7_500, 12, 5),
            "Press Conference": (1, 6_000, 13, 16), "Regional Tour": (2, 14_000, 16, 8),
            "Crisis Response": (1, 9_000, 2, 4),
        }
        points, cost, heat, risk = specs.get(action, specs["Interview"])
        return {"points": points, "cost": cost, "heat": heat, "risk": risk}

    def media_action_preview(self, action, fighter=None):
        spec = self._media_action_spec(action, fighter)
        target_note = " Same-division target required." if action == "Call Out" else ""
        return f"{spec['points']} action point(s) | Cost ${spec['cost']:,} | Base heat {spec['heat']} | Backfire risk {spec['risk']}%.{target_note}"

    def resolve_media_campaign(self, action, fighter, target=None, region=None, promotion=None):
        if not fighter:
            return False, "Choose a spokesperson first.", None
        finance = self._ensure_media_state(promotion)
        spec = self._media_action_spec(action, fighter)
        remaining = self.media_actions_remaining(promotion)
        if remaining < spec["points"]:
            return False, f"Only {remaining} media action point(s) remain this week.", None
        if action == "Call Out" and (not target or target is fighter or target.gender != fighter.gender or target.weight != fighter.weight):
            return False, "Callouts require a different fighter in the same division.", None
        company_name, company_region, _pop, _stability, cash, _roster = self._media_company_values(promotion)
        if cash < spec["cost"]:
            return False, f"This campaign costs ${spec['cost']:,}.", None
        marker = (self.month - 1) * 4 + self.week
        fighter_key = f"fighter:{fighter.name}"
        pair_key = f"callout:{fighter.name}:{getattr(target, 'name', '')}"
        cooldowns = finance["media_campaign_cooldowns"]
        if cooldowns.get(fighter_key, -99) >= marker:
            return False, f"{fighter.name} has already completed a media appearance this week.", None
        if action == "Call Out" and cooldowns.get(pair_key, -99) > marker:
            return False, "That rivalry callout is still on a four-week cooldown.", None
        if promotion is None:
            self.cash -= spec["cost"]
            marketing = self.staff_skill("Marketing") if hasattr(self, "staff_skill") else 45
        else:
            promotion.cash -= spec["cost"]
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
            if hasattr(self, "establish_rivalry"):
                try:
                    self.establish_rivalry(fighter, target, origin="Media callout", heat=max(35, 45 + heat_delta))
                except TypeError:
                    fighter.rival, target.rival = target.name, fighter.name
            else:
                fighter.rival, target.rival = target.name, fighter.name
            target.media_heat = max(0, min(100, target.media_heat + max(2, heat_delta // 2)))
        subject = fighter.name
        target_name = target.name if target else (region or company_region if action == "Regional Tour" else "")
        outcome_text = f"{band}: {fighter.name}'s {action.lower()} produced {heat_delta:+} heat and {pop_delta:+} popularity."
        row = {"date": f"M{self.month} W{self.week}", "month": self.month, "week": self.week, "strategy": strategy, "action": action, "subject": subject, "target": target_name, "outcome": outcome_text, "band": band, "heat": heat_delta, "popularity": pop_delta, "trust": trust_delta, "cost": spec["cost"]}
        finance["media_campaign_history"].insert(0, row)
        finance["media_campaign_history"] = finance["media_campaign_history"][:60]
        if promotion is None:
            headline = f"{fighter.name}'s {action.lower()} campaign lands as a {band.lower()} media moment."
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
            if not outlet.get("active", True):
                continue
            volatility = max(3, outlet.get("volatility", 15))
            budget_change = random.choice([-1, 0, 0, 0, 1]) if random.randint(1, 100) > volatility else random.choice([-3, -2, 2, 3])
            old = outlet.get("budget", 50)
            outlet["budget"] = max(10, min(99, old + budget_change))
            outlet["base_fee"] = max(4_000, round(outlet.get("base_fee", 10_000) * (1 + budget_change / 250)))
            if abs(budget_change) >= 3:
                changes.append(f"{outlet['name']} budget {'rose' if budget_change > 0 else 'fell'}")
        snapshot = {"month": self.month, "active_outlets": sum(1 for o in self.media_companies if o.get("active", True)), "average_budget": round(sum(o.get("budget", 0) for o in self.media_companies) / max(1, len(self.media_companies))), "changes": changes[:4]}
        self.media_market_history.insert(0, snapshot)
        self.media_market_history = self.media_market_history[:120]

    def review_ai_media_deals(self, promo):
        finance = self.ensure_ai_media_state(promo)
        active = self.active_media_contract(promo)
        if active and active.get("months", 0) > 0 and active.get("events_remaining", 0) > 0:
            return active
        offers = self.generate_media_offers(promo, force=not finance.get("media_offers"), count=4)
        if not offers:
            return active
        mode = (promo.strategy or {}).get("current_mode", "Balanced")
        def value(offer):
            affordability = offer["fee"] / max(1, promo.size * 1500)
            reach_weight = 1.5 if mode in ("Star Chasing", "Title Push") else 0.9
            security = 1.3 if mode == "Financial Recovery" else 1.0
            standards_risk = max(0, offer["min_card_quality"] - promo.reputation_score) * 3
            return offer["reach"] * reach_weight + offer["fee"] / 6000 * security - standards_risk - affordability
        choice = max(offers, key=value)
        ok, _message = self._accept_media_offer(choice["id"], promo)
        return self.active_media_contract(promo) if ok else active

    def process_media_month(self):
        self.ensure_media_system()
        self.update_media_market()
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
        for promotion in [None] + list(self.promotions):
            finance = self._ensure_media_state(promotion)
            for contract in finance["media_contracts"]:
                if contract.get("status") != "Active":
                    continue
                contract["months"] = max(0, contract.get("months", 0) - 1)
                if contract["months"] <= 0 or contract.get("events_remaining", 0) <= 0:
                    contract["status"] = "Completed"
                    if promotion is None:
                        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Media contract completed: {contract['name']}.")
            self.sync_legacy_media_rights(promotion)

    def calculate_event_media_outcome(self, event, package=None, promotion=None, contract=None, apply=False):
        finance = self._ensure_media_state(promotion)
        contract = contract or self.active_media_contract(promotion)
        eligible, reason = self.media_contract_eligibility(contract, event, promotion) if contract else (False, "No active rights deal")
        package = package or {}
        financial = package.get("finance", package) if isinstance(package, dict) else {}
        fight_count = int(package.get("fight_count", len(event.get("fights", []))) or len(event.get("fights", [])))
        excitement = float(package.get("average_excitement", financial.get("excitement_score", 50)) or 50)
        build = float(financial.get("build_score", package.get("average_build", 50)) or 50)
        roster = self._media_company_values(promotion)[5]
        names = [name for fight in event.get("fights", []) for name in fight.get("fighters", []) if isinstance(name, str)]
        featured = [fighter for fighter in roster if fighter.name in names]
        star_power = sum(f.popularity + f.star_quality + f.media_heat for f in featured) / max(1, len(featured)) if featured else 45
        recent_campaigns = [row for row in finance.get("media_campaign_history", []) if row.get("month") in (self.month, self.month - 1)]
        campaign_lift = max(-8, min(14, sum(row.get("heat", 0) for row in recent_campaigns[:8]) / 8))
        reach = int(contract.get("reach", 0)) if eligible else (4 if event.get("broadcaster") != "No Coverage" else 0)
        rating = max(5, min(99, round(build * 0.30 + excitement * 0.28 + star_power * 0.22 + reach * 0.14 + campaign_lift + random.uniform(-5, 5))))
        viewers = round((8_000 + reach * 15_000) * (0.55 + rating / 100) * max(0.75, min(1.35, fight_count / 8))) if reach else round(1_500 * max(1, fight_count))
        minimum = contract.get("minimum_rating", 0) if contract else 0
        delivered = bool(eligible and rating >= minimum and build >= max(0, contract.get("min_card_quality", 0) - 10))
        relationship_delta = (4 if rating >= minimum + 12 else 2 if delivered else -5 if eligible else -2)
        performance_bonus = contract.get("performance_bonus", 0) if delivered and rating >= minimum + 10 else 0
        guarantee = contract.get("fee", contract.get("guarantee_per_event", 0)) if eligible else 0
        exposure_delta = 2 if rating >= 78 else 1 if rating >= 58 else (-1 if not eligible else 0)
        result = {"outlet": contract.get("name", "No rights partner") if contract else "No rights partner", "eligible": eligible, "reason": reason, "reach": reach, "rating": rating, "viewers": viewers, "delivered": delivered, "minimum_rating": minimum, "relationship_delta": relationship_delta, "performance_bonus": performance_bonus, "rights_income": guarantee + performance_bonus, "exposure_delta": exposure_delta, "campaign_lift": round(campaign_lift, 1)}
        if apply:
            self.record_media_event_outcome(event, result, promotion=promotion, featured_fighters=featured)
        return result

    def record_media_event_outcome(self, event, outcome, promotion=None, featured_fighters=None):
        finance = self._ensure_media_state(promotion)
        contract = self.active_media_contract(promotion)
        if contract and outcome.get("eligible"):
            contract["events_remaining"] = max(0, contract.get("events_remaining", 0) - 1)
            contract["relationship"] = max(0, min(100, contract.get("relationship", 50) + outcome.get("relationship_delta", 0)))
            if not outcome.get("delivered"):
                contract["breach_strikes"] = contract.get("breach_strikes", 0) + 1
            finance["media_relationships"][contract.get("outlet_id", "")] = contract["relationship"]
            if contract.get("breach_strikes", 0) >= 3:
                contract["status"] = "Terminated for delivery failures"
        row = {"date": f"M{self.month} W{self.week}", "month": self.month, "week": self.week, "event": event.get("name", event.get("event_name", "Event")), **dict(outcome)}
        finance["media_audience_history"].insert(0, row)
        finance["media_audience_history"] = finance["media_audience_history"][:60]
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
    def media_apply_strategy(self):
        finance = self.ensure_player_media_state()
        strategy = self.media_strategy_choice.get() if hasattr(self, "media_strategy_choice") else "Balanced"
        if strategy not in self.MEDIA_STRATEGIES:
            strategy = "Balanced"
        finance["media_strategy"] = strategy
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Media strategy changed to {strategy}.")
        self.refresh_all()

    def media_run_selected_campaign(self):
        fighter = self.media_desk_fighter() if hasattr(self, "media_desk_fighter") else None
        action = self.media_action_choice.get() if hasattr(self, "media_action_choice") else "Interview"
        target = self.get_fighter(self.media_target_choice.get()) if action == "Call Out" and hasattr(self, "media_target_choice") and self.media_target_choice.get() else None
        ok, text, _row = self.resolve_media_campaign(action, fighter, target, region=getattr(self, "player_region", ""))
        if not ok:
            messagebox.showinfo("Media Campaign", text)
        self.refresh_all()

    def _selected_media_offer_id(self):
        selected = self.media_offers_tree.selection() if hasattr(self, "media_offers_tree") else ()
        return selected[0] if selected else ""

    def media_accept_selected_offer(self):
        offer_id = self._selected_media_offer_id()
        if not offer_id:
            messagebox.showinfo("Media Rights", "Select an offer first.")
            return
        active = self.active_media_contract()
        if active and not messagebox.askyesno("Replace Media Deal", f"Accepting this offer will end {active['name']} and may charge its ${active.get('termination_fee', 0):,} buyout. Continue?"):
            return
        ok, text = self.accept_player_media_offer(offer_id)
        (messagebox.showinfo if ok else messagebox.showwarning)("Media Rights", text)
        if ok:
            self.news.insert(0, text)
            self.record_world_story("Business", f"{self.player_company_name} signs with {self.active_media_contract()['name']}.", text, [self.player_company_name], [], 3)
        self.refresh_all()

    def media_reject_selected_offer(self):
        offer_id = self._selected_media_offer_id()
        if not offer_id:
            messagebox.showinfo("Media Rights", "Select an offer first.")
            return
        _ok, text = self.reject_player_media_offer(offer_id)
        self.finance.setdefault("ledger", []).insert(0, f"Month {self.month}: {text}")
        self.refresh_all()

    def media_refresh_offers(self):
        finance = self.ensure_player_media_state()
        cost = 3_500
        if self.cash < cost:
            messagebox.showwarning("Media Rights", f"A market review costs ${cost:,}.")
            return
        self.cash -= cost
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Commissioned media-rights market review for ${cost:,}.")
        self.generate_media_offers(force=True)
        self.refresh_all()

    def media_terminate_contract(self):
        active = self.active_media_contract()
        if not active:
            messagebox.showinfo("Media Rights", "There is no active deal to end.")
            return
        if not messagebox.askyesno("End Media Deal", f"End {active['name']} for ${active.get('termination_fee', 0):,}?"):
            return
        ok, text = self.terminate_player_media_contract(active.get("id", ""))
        (messagebox.showinfo if ok else messagebox.showwarning)("Media Rights", text)
        self.refresh_all()

    def negotiate_media_rights(self):
        """Finance-screen shortcut into the actual offer market."""
        finance = self.ensure_player_media_state()
        self.generate_media_offers(force=not bool(finance.get("media_offers")))
        if hasattr(self, "select_tab"):
            self.select_tab("website")
        else:
            self.refresh_all()

    def pitch_sponsors(self):
        """Ask the market for competing, fit-aware offers instead of auto-signing one."""
        finance = self.ensure_player_media_state()
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
        existing = {str(deal.get("name", "")).lower() for deal in finance.get("sponsor_deals", [])}
        available = [row for row in brands if row[0].lower() not in existing]
        if not available:
            finance["sponsor_market_note"] = "No fresh brands are available while the current portfolio remains active."
            self.refresh_all()
            return
        top_appeal = sum(sorted((f.sponsor_appeal for f in self.roster), reverse=True)[:8]) / max(1, min(8, len(self.roster)))
        trust = finance.get("media_public_trust", 55)
        base_score = self.company_pop * 0.55 + self.company_stability * 0.18 + top_appeal * 0.18 + trust * 0.09
        suitable = [row for row in available if base_score + random.randint(-18, 18) >= row[2]]
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
            fit = max(1, min(99, round(base_score - threshold + 58 + random.randint(-7, 7))))
            fee = max(4_000, round((self.company_pop * 190 + top_appeal * 85 + fit * 110) * random.uniform(0.75, 1.35) / 100) * 100)
            offers.append({
                "id": f"sponsor-{self.month}-{index}-{name.lower().replace(' ', '-')}", "name": name,
                "category": category, "fee": fee, "months": random.randint(6, 18), "fit": fit,
                "relationship": 50, "activation_requirement": random.choice((
                    "Brand placement on every promoted event", "Feature a ranked fighter in campaign media",
                    "Maintain company stability above 45", "Deliver at least one event each month",
                )), "conduct_threshold": max(20, 78 - trust), "expires_month": self.month + 1,
            })
        finance["sponsor_offers"] = offers
        finance["sponsor_market_note"] = f"{len(offers)} competing offer(s) received. Select one to review or accept."
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Sponsor market returned {len(offers)} offer(s).")
        self.refresh_all()

    def selected_sponsor_offer(self):
        if not hasattr(self, "sponsor_market_tree"):
            return None
        selected = self.sponsor_market_tree.selection()
        offer_id = selected[0] if selected else ""
        return next((offer for offer in self.finance.get("sponsor_offers", []) if offer.get("id") == offer_id), None)

    def accept_sponsor_offer(self):
        finance = self.ensure_player_media_state()
        offer = self.selected_sponsor_offer()
        if not offer:
            finance["sponsor_market_note"] = "Select a live sponsor offer first."
            self.refresh_finance()
            return
        if any(deal.get("category") == offer.get("category") for deal in finance.get("sponsor_deals", [])):
            finance["sponsor_market_note"] = f"An active {offer['category']} partner blocks this category."
            self.refresh_finance()
            return
        deal = {key: value for key, value in offer.items() if key not in ("id", "expires_month")}
        finance.setdefault("sponsor_deals", []).insert(0, deal)
        finance["sponsor_deals"] = finance["sponsor_deals"][:8]
        finance["sponsor_offers"] = [row for row in finance.get("sponsor_offers", []) if row.get("id") != offer.get("id")]
        finance.setdefault("sponsor_offer_history", []).insert(0, {**offer, "decision": "Accepted", "month": self.month})
        finance["sponsor_offer_history"] = finance["sponsor_offer_history"][:60]
        finance["sponsor_market_note"] = f"Signed {deal['name']} for ${deal['fee']:,} per event over {deal['months']} months."
        finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Signed {deal['name']} ({deal['category']}) for ${deal['fee']:,}/event.")
        self.inbox.append({"subject": "Sponsor Signed", "body": finance["sponsor_market_note"], "type": "Business", "resolved": False})
        self.news.insert(0, f"{self.player_company_name} signs {deal['name']} as its {deal['category'].lower()} partner.")
        self.refresh_all()

    def reject_sponsor_offer(self):
        finance = self.ensure_player_media_state()
        offer = self.selected_sponsor_offer()
        if not offer:
            finance["sponsor_market_note"] = "Select a live sponsor offer first."
            self.refresh_finance()
            return
        finance["sponsor_offers"] = [row for row in finance.get("sponsor_offers", []) if row.get("id") != offer.get("id")]
        finance.setdefault("sponsor_offer_history", []).insert(0, {**offer, "decision": "Rejected", "month": self.month})
        finance["sponsor_market_note"] = f"Rejected {offer['name']}."
        self.refresh_finance()

    def refresh_media_dashboard(self):
        if not hasattr(self, "media_kpi_summary"):
            return
        finance = self.ensure_player_media_state()
        if not finance["media_offers"]:
            self.generate_media_offers(force=True)
        remaining = self.media_actions_remaining()
        active = self.active_media_contract()
        recent = finance.get("media_audience_history", [])[:1]
        rating = f" | Last rating {recent[0].get('rating', 0)} ({recent[0].get('viewers', 0):,} viewers)" if recent else ""
        self.media_kpi_summary.config(text=f"Actions {remaining}/{self.media_action_capacity()} | Strategy {finance['media_strategy']} | Company buzz {finance.get('media_company_buzz', 20)} | Public trust {finance.get('media_public_trust', 55)} | Rights reach {active.get('reach', 0) if active else 0}{rating}")
        if hasattr(self, "media_strategy_choice"):
            self.media_strategy_choice.set(finance.get("media_strategy", "Balanced"))
        action = self.media_action_choice.get() if hasattr(self, "media_action_choice") else "Interview"
        fighter = self.media_desk_fighter() if hasattr(self, "media_desk_fighter") else None
        self.media_action_summary.config(text=self.media_action_preview(action, fighter))
        if active:
            requirements = f"rating {active.get('minimum_rating', 0)}+, card {active.get('min_card_quality', 0)}+, production {active.get('min_production', 0)}+"
            rights_text = f"ACTIVE: {active['name']} | ${active.get('fee', 0):,}/event | reach {active.get('reach', 0)} | {active.get('events_remaining', 0)}/{active.get('events_total', 0)} events | {active.get('months', 0)} months | relationship {active.get('relationship', 50)} | strikes {active.get('breach_strikes', 0)}/3 | Requires {requirements}"
        else:
            rights_text = "No active rights package. Events receive only the reach of their paid production provider; future offers depend on stability, stars, ratings, and outlet relationships."
        self.media_rights_summary.config(text=rights_text)
        selected = self.media_offers_tree.selection()
        self.media_offers_tree.delete(*self.media_offers_tree.get_children())
        for offer in finance["media_offers"]:
            expiry = self.format_game_date(offer["expires_month"], 1, include_week=False)
            req = f"Rating {offer['minimum_rating']} / card {offer['min_card_quality']} / production {offer['min_production']} | {offer['exclusivity']} | expires {expiry}"
            self.media_offers_tree.insert("", "end", iid=offer["id"], values=(offer["name"], offer["type"], offer["reach"], f"${offer['fee']:,}", f"{offer['months']} mo", offer["events_total"], req))
        if selected and selected[0] in self.media_offers_tree.get_children():
            self.media_offers_tree.selection_set(selected[0])
        elif self.media_offers_tree.get_children():
            self.media_offers_tree.selection_set(self.media_offers_tree.get_children()[0])
        self.media_campaign_history_tree.delete(*self.media_campaign_history_tree.get_children())
        for index, row in enumerate(finance.get("media_campaign_history", [])[:60]):
            self.media_campaign_history_tree.insert("", "end", iid=f"campaign:{index}", values=(self.format_game_date_text(row.get("date", "")), row.get("strategy", ""), row.get("action", ""), row.get("subject", ""), row.get("target", ""), row.get("outcome", ""), f"{row.get('heat', 0):+}", f"${row.get('cost', 0):,}"))

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
