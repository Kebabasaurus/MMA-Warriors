"""Deterministic, reviewable booking proposals.

The booking workbench is deliberately a planning layer.  It reads the same
availability, ranking and matchup helpers used by the ordinary Matchmaking
screen, but it never books or reserves a fighter while a proposal is being
generated.  A player-confirmed fill is the only mutating operation and is
sealed through the shared Foundation receipt when that contract is available.
"""

from copy import deepcopy
import hashlib
import json


class BookingWorkbenchMixin:
    """Persisted J1 brief/proposal helpers shared by UI and headless tests."""

    BOOKING_WORKBENCH_SCHEMA_VERSION = 1
    BOOKING_WORKBENCH_EMPHASES = ("Balanced", "Sporting", "Development", "Commercial")

    @staticmethod
    def _default_booking_workbench_state():
        return {
            "schema_version": 1,
            "sequence": 0,
            "brief": None,
            "proposals": [],
            "locked_slot_proposals": [],
            "medical_plans": [],
        }

    def ensure_booking_workbench_state(self):
        """Repair only the workbench envelope, retaining unknown future fields."""
        state = getattr(self, "booking_workbench", None)
        if not isinstance(state, dict):
            state = self._default_booking_workbench_state()
        defaults = self._default_booking_workbench_state()
        for key, value in defaults.items():
            if key not in state:
                state[key] = deepcopy(value)
        try:
            state["schema_version"] = max(1, int(state.get("schema_version", 1) or 1))
            state["sequence"] = max(0, int(state.get("sequence", 0) or 0))
        except (TypeError, ValueError):
            state["schema_version"], state["sequence"] = 1, 0
        brief = state.get("brief")
        if isinstance(brief, dict):
            brief.setdefault("brief_id", "")
            brief.setdefault("fighter_id", "")
            brief.setdefault("fighter_name", "")
            brief.setdefault("preferred_window", {})
            brief.setdefault("emphasis", "Balanced")
            brief.setdefault("opposition_gap", 12)
            brief.setdefault("revision", 1)
            brief.setdefault("status", "Active")
            if not isinstance(brief.get("preferred_window"), dict):
                brief["preferred_window"] = {}
            if brief.get("emphasis") not in self.BOOKING_WORKBENCH_EMPHASES:
                brief["emphasis"] = "Balanced"
            try:
                brief["opposition_gap"] = max(0, min(30, int(brief.get("opposition_gap", 12) or 12)))
                brief["revision"] = max(1, int(brief.get("revision", 1) or 1))
            except (TypeError, ValueError):
                brief["opposition_gap"], brief["revision"] = 12, 1
        proposals = []
        for proposal in state.get("proposals", []) if isinstance(state.get("proposals"), list) else []:
            if not isinstance(proposal, dict):
                continue
            item = dict(proposal)
            item.setdefault("proposal_id", "")
            item.setdefault("brief_id", "")
            item.setdefault("anchor_id", "")
            item.setdefault("anchor_name", "")
            item.setdefault("target_month", 0)
            item.setdefault("target_week", 0)
            item.setdefault("status", "Draft")
            item.setdefault("selected_option", None)
            item.setdefault("options", [])
            item["options"] = [dict(row) for row in item["options"] if isinstance(row, dict)]
            proposals.append(item)
        state["proposals"] = proposals[-40:]
        locked_proposals = []
        for proposal in state.get("locked_slot_proposals", []) if isinstance(state.get("locked_slot_proposals"), list) else []:
            if not isinstance(proposal, dict):
                continue
            item = dict(proposal)
            item.setdefault("proposal_id", "")
            item.setdefault("proposal_kind", "locked_slot")
            item.setdefault("booking_id", "")
            item.setdefault("corner_index", 0)
            item.setdefault("original_fighter_ids", [])
            item.setdefault("original_participants", [])
            item.setdefault("original_fight_fingerprint", "")
            item.setdefault("target_month", 0)
            item.setdefault("target_week", 0)
            item.setdefault("status", "Draft")
            item.setdefault("selected_option", None)
            item.setdefault("options", [])
            item["options"] = [dict(row) for row in item["options"] if isinstance(row, dict)]
            locked_proposals.append(item)
        state["locked_slot_proposals"] = locked_proposals[-40:]
        medical_plans = []
        for plan in state.get("medical_plans", []) if isinstance(state.get("medical_plans"), list) else []:
            if not isinstance(plan, dict):
                continue
            item = dict(plan)
            item.setdefault("plan_id", "")
            item.setdefault("anchor_id", "")
            item.setdefault("candidate_id", "")
            item.setdefault("candidate_name", "")
            item.setdefault("target_month", 0)
            item.setdefault("target_week", 0)
            item.setdefault("created_month", 0)
            item.setdefault("created_week", 0)
            item.setdefault("status", "Tentative")
            item.setdefault("preview", {})
            if not isinstance(item.get("preview"), dict):
                item["preview"] = {}
            medical_plans.append(item)
        state["medical_plans"] = medical_plans[-40:]
        self.booking_workbench = state
        return state

    def _booking_workbench_raw_state(self):
        """Return the retained workbench envelope for observational readers.

        The normalizer above is deliberately a write-boundary helper used by
        explicit save/generate/commit actions. Page refreshes and review
        readers must not call it: malformed legacy drafts should remain
        available for diagnosis without being rewritten in the background.
        """
        state = getattr(self, "booking_workbench", {})
        return state if isinstance(state, dict) else {}

    def _booking_workbench_next_id(self, prefix="proposal"):
        state = self.ensure_booking_workbench_state()
        state["sequence"] = int(state.get("sequence", 0) or 0) + 1
        return f"booking-{prefix}-{state['sequence']:06d}"

    def _booking_resolve_fighter(self, reference):
        reference = str(reference or "")
        if not reference or reference == "TBA":
            return None
        resolver = getattr(self, "resolve_fighter", None)
        if callable(resolver):
            try:
                fighter = resolver(reference)
                if fighter is not None:
                    return fighter
            except Exception:
                pass
        for fighter in getattr(self, "roster", []) or []:
            if str(getattr(fighter, "fighter_id", "") or "") == reference:
                return fighter
        matches = [fighter for fighter in getattr(self, "roster", []) or [] if getattr(fighter, "name", "") == reference]
        return matches[0] if len(matches) == 1 else None

    def save_booking_workbench_brief(self, fighter_id="", *, preferred_window=None,
                                     emphasis="Balanced", opposition_gap=12):
        """Save/replace the player's planning brief without booking or RNG."""
        state = self.ensure_booking_workbench_state()
        fighter = self._booking_resolve_fighter(fighter_id) if fighter_id else None
        if fighter_id and fighter is None:
            return False, "The selected fighter is no longer on the player roster.", None
        emphasis = str(emphasis or "Balanced")
        if emphasis not in self.BOOKING_WORKBENCH_EMPHASES:
            return False, "Choose a supported booking emphasis.", None
        try:
            opposition_gap = max(0, min(30, int(opposition_gap)))
        except (TypeError, ValueError):
            return False, "Opposition range must be a whole number from 0 to 30.", None
        current = state.get("brief") if isinstance(state.get("brief"), dict) else None
        brief_id = str(current.get("brief_id", "") or "") if current else ""
        if not brief_id:
            brief_id = self._booking_workbench_next_id("brief")
        else:
            # Replacement is intentionally a new revision of the same brief;
            # existing proposals retain their original snapshot and evidence.
            state["sequence"] = max(int(state.get("sequence", 0) or 0), 1)
        revision = int(current.get("revision", 0) or 0) + 1 if current else 1
        target_window = deepcopy(preferred_window) if isinstance(preferred_window, dict) else {}
        cleaned_window = {}
        for key in ("start_month", "start_week", "end_month", "end_week"):
            if key in target_window:
                try:
                    cleaned_window[key] = max(1, int(target_window[key]))
                except (TypeError, ValueError):
                    continue
        brief = {
            "brief_id": brief_id,
            "fighter_id": str(getattr(fighter, "fighter_id", "") or fighter_id or ""),
            "fighter_name": str(getattr(fighter, "name", "") or ""),
            "preferred_window": cleaned_window,
            "emphasis": emphasis,
            "opposition_gap": opposition_gap,
            "created_month": int(getattr(self, "month", 1) or 1),
            "created_week": int(getattr(self, "week", 1) or 1),
            "revision": revision,
            "status": "Active",
        }
        state["brief"] = brief
        return True, f"Saved {brief_id} revision {revision}. It will only guide explicit proposals.", deepcopy(brief)

    def booking_workbench_brief_snapshot(self):
        state = self._booking_workbench_raw_state()
        brief = state.get("brief")
        return deepcopy(brief) if isinstance(brief, dict) else None

    def booking_workbench_draft_snapshot(self):
        """Describe the current draft card without taking control of it.

        Complete pairings are marked ``Preserved`` so a future proposal editor
        can never silently replace them. Foundation migration supplies a stable
        booking ID for legacy rows; hosts without that migration retain an
        explicitly labelled legacy slot reference rather than inventing one from
        a mutable position.
        """
        booked = getattr(self, "booked", [])
        if not isinstance(booked, list):
            booked = []
        rows = []
        locked_ids = []
        unresolved = []
        references_fn = getattr(self, "event_fight_participant_references", None)
        for index, fight in enumerate(booked):
            if not isinstance(fight, dict):
                continue
            participants = list(fight.get("fighters", []) or [])
            if callable(references_fn):
                try:
                    references = list(references_fn(fight) or [])
                except Exception:
                    references = list(fight.get("fighter_ids", []) or []) or participants
            else:
                references = list(fight.get("fighter_ids", []) or []) or participants
            references = [str(value or "") for value in references]
            open_slots = [position for position, value in enumerate(references) if not value or value == "TBA"]
            explicit_id = str(fight.get("booking_id", fight.get("fight_id", "")) or "").strip()
            if explicit_id:
                booking_id = explicit_id
            else:
                booking_id = f"legacy-slot:{self._booking_fight_fingerprint(fight)[:20]}"
            identity_status = "Stable" if explicit_id else "Legacy reference"
            status = "Needs opponent" if open_slots else "Preserved pairing"
            row = {
                "slot_index": index, "booking_id": booking_id,
                "identity_status": identity_status, "status": status,
                "participants": references, "open_slots": open_slots,
                "title": bool(fight.get("title", False)),
                "tier": str(fight.get("tier", "Main Card") or "Main Card"),
                "weight": str(fight.get("weight", fight.get("tournament_weight", "")) or ""),
                "reason": str(fight.get("booking_reason", "") or ""),
            }
            rows.append(row)
            if open_slots:
                unresolved.append(booking_id)
            else:
                locked_ids.append(booking_id)
        return {
            "schema_version": 1,
            "locked_existing_bout_ids": locked_ids,
            "unresolved_slots": unresolved,
            "rows": rows,
            "summary": f"{len(locked_ids)} preserved pairing(s), {len(unresolved)} unresolved slot(s)",
        }

    @staticmethod
    def _booking_fight_fingerprint(fight):
        """Return a stable digest for stale locked-slot detection."""
        if not isinstance(fight, dict):
            return ""
        try:
            payload = json.dumps(fight, sort_keys=True, default=str, separators=(",", ":"))
        except (TypeError, ValueError):
            payload = repr(sorted((str(key), repr(value)) for key, value in fight.items()))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _booking_locked_slot(self, booking_id, *, migrate=True):
        """Resolve one player draft fight by its migrated durable booking ID."""
        wanted = str(booking_id or "").strip()
        if not wanted:
            return None, None
        ensure_ids = getattr(self, "ensure_booking_ids", None)
        if migrate and callable(ensure_ids):
            ensure_ids()
        for index, fight in enumerate(getattr(self, "booked", []) or []):
            if isinstance(fight, dict) and str(fight.get("booking_id", "") or "").strip() == wanted:
                return index, fight
        return None, None

    def generate_locked_slot_proposal(self, booking_id, corner_index=0, target_month=None, target_week=None, *, limit=6):
        """Create alternatives for one complete draft-card corner.

        This is an explicit, non-mutating proposal.  It applies only to the
        player's unscheduled ``booked`` card; scheduled event fights remain
        observational until their domain owner is specified.
        """
        state = self.ensure_booking_workbench_state()
        index, fight = self._booking_locked_slot(booking_id)
        if fight is None:
            return False, "That draft slot no longer exists or has no stable booking ID.", None
        try:
            corner_index = int(corner_index)
        except (TypeError, ValueError):
            return False, "Choose corner 1 or corner 2.", None
        references_fn = getattr(self, "event_fight_participant_references", None)
        try:
            references = list(references_fn(fight) or []) if callable(references_fn) else list(fight.get("fighter_ids", []) or [])
        except Exception:
            references = list(fight.get("fighter_ids", []) or [])
        references = [str(value or "") for value in references]
        if len(references) < 2 or any(not value or value == "TBA" for value in references[:2]):
            return False, "Locked-slot proposals require a complete two-fighter pairing.", None
        if corner_index not in (0, 1):
            return False, "Choose corner 1 or corner 2.", None
        anchor = self._booking_resolve_fighter(references[corner_index])
        opponent = self._booking_resolve_fighter(references[1 - corner_index])
        if anchor is None or opponent is None:
            return False, "Both existing fighter identities must still be available.", None
        target_month = int(target_month if target_month is not None else getattr(self, "month", 1) or 1)
        target_week = int(target_week if target_week is not None else getattr(self, "week", 1) or 1)
        rows = self.booking_workbench_candidate_rows(
            getattr(anchor, "fighter_id", ""), target_month, target_week,
            include_blocked=True, limit=max(8, int(limit or 6) * 2),
        )
        options = []
        for row in rows:
            option = {key: deepcopy(value) for key, value in row.items() if key != "fighter"}
            option["replaces_fighter_id"] = str(getattr(opponent, "fighter_id", "") or references[1 - corner_index])
            options.append(option)
        proposal = {
            "proposal_id": self._booking_workbench_next_id("locked-slot"),
            "proposal_kind": "locked_slot",
            "booking_id": str(fight.get("booking_id", "") or ""),
            "slot_index": int(index),
            "corner_index": corner_index,
            "anchor_id": str(getattr(anchor, "fighter_id", "") or references[corner_index]),
            "anchor_name": str(getattr(anchor, "name", "Unknown")),
            "original_fighter_ids": deepcopy(references[:2]),
            "original_participants": list(fight.get("fighters", []) or [])[:2],
            "original_fight": deepcopy(fight),
            "original_fight_fingerprint": self._booking_fight_fingerprint(fight),
            "target_month": target_month,
            "target_week": target_week,
            "generated_month": int(getattr(self, "month", target_month) or target_month),
            "generated_week": int(getattr(self, "week", target_week) or target_week),
            "status": "Draft",
            "selected_option": None,
            "options": options[:max(1, min(12, int(limit or 6)))],
        }
        state["locked_slot_proposals"].append(proposal)
        state["locked_slot_proposals"] = state["locked_slot_proposals"][-40:]
        eligible = sum(1 for row in proposal["options"] if not row.get("hard_blocks"))
        return True, f"{proposal['proposal_id']} saved with {eligible} eligible alternative(s); the draft card is unchanged.", deepcopy(proposal)

    def review_locked_slot_proposal(self, proposal_id):
        """Re-read alternatives and report stale card state without rewriting evidence."""
        state = self._booking_workbench_raw_state()
        proposals = state.get("locked_slot_proposals", [])
        if not isinstance(proposals, list):
            return None
        proposal = next((row for row in proposals if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None)
        if not proposal:
            return None
        current = deepcopy(proposal)
        _index, fight = self._booking_locked_slot(proposal.get("booking_id", ""), migrate=False)
        if fight is None:
            current["current_status"] = "Unavailable"
            current["current_reason"] = "The draft slot no longer exists."
            return current
        if self._booking_fight_fingerprint(fight) != str(proposal.get("original_fight_fingerprint", "") or ""):
            current["current_status"] = "Stale"
            current["current_reason"] = "The draft slot changed after this proposal was generated; review it again before editing."
            return current
        snapshots = proposal.get("options", [])
        if not isinstance(snapshots, list):
            current["options"] = []
            current["current_status"] = "Unavailable"
            current["current_reason"] = "Saved alternative evidence is malformed; no replacement can be selected."
            return current
        current_rows = {row.get("fighter_id"): row for row in self.booking_workbench_candidate_rows(
            proposal.get("anchor_id", ""), proposal.get("target_month", getattr(self, "month", 1)),
            proposal.get("target_week", getattr(self, "week", 1)), include_blocked=True, limit=100,
        )}
        refreshed = []
        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                refreshed.append({
                    "raw_snapshot": deepcopy(snapshot),
                    "current_status": "Unavailable",
                    "current_blocks": ["saved alternative evidence is malformed"],
                })
                continue
            option = deepcopy(snapshot)
            live = current_rows.get(option.get("fighter_id"))
            if live is None:
                option["current_status"] = "Unavailable"
                option["current_blocks"] = ["fighter identity is no longer available"]
            else:
                option["current_status"] = "Eligible" if not live.get("hard_blocks") else "Blocked"
                option["current_blocks"] = list(live.get("hard_blocks", []))
                option["current_cautions"] = list(live.get("cautions", []))
                option["current_medical_preview"] = deepcopy(live.get("medical_preview", {}))
            refreshed.append(option)
        current["options"] = refreshed
        current["current_status"] = str(proposal.get("status", "Draft"))
        current["current_reason"] = "Stable draft slot; explicit commit is required to replace one corner."
        return current

    def commit_locked_slot_proposal(self, proposal_id, option_index):
        """Replace exactly one corner after stale/eligibility checks and one receipt."""
        # Preflight the retained row before invoking the explicit write-boundary
        # normaliser. A malformed option must fail closed without silently
        # dropping the raw evidence as a side effect of a rejected click.
        raw_state = self._booking_workbench_raw_state()
        raw_rows = raw_state.get("locked_slot_proposals", []) if isinstance(raw_state, dict) else []
        raw_proposal = next((row for row in raw_rows if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None) if isinstance(raw_rows, list) else None
        if raw_proposal is not None:
            try:
                raw_index = int(option_index)
            except (TypeError, ValueError):
                return False, "Choose one of the listed alternatives.", None
            raw_options = raw_proposal.get("options", [])
            if not isinstance(raw_options, list) or raw_index < 0 or raw_index >= len(raw_options):
                return False, "The saved alternative evidence is malformed; no replacement was applied.", None
            if not isinstance(raw_options[raw_index], dict):
                return False, "The saved alternative evidence is malformed; no replacement was applied.", None
        state = self.ensure_booking_workbench_state()
        proposal = next((row for row in state.get("locked_slot_proposals", []) if row.get("proposal_id") == str(proposal_id or "")), None)
        if not proposal:
            return False, "That locked-slot proposal no longer exists.", None
        try:
            option_index = int(option_index)
            if option_index < 0 or option_index >= len(proposal.get("options", [])):
                raise ValueError("Choose one of the listed alternatives.")
        except (TypeError, ValueError) as exc:
            return False, str(exc), None
        if not isinstance(proposal.get("options", [])[option_index], dict):
            return False, "The saved alternative evidence is malformed; no replacement was applied.", None
        if proposal.get("status") == "Committed":
            prior_key = f"booking-workbench:{proposal.get('proposal_id', '')}:option:{option_index}"
            prior_fn = getattr(self, "foundation_get_receipt", None)
            prior = prior_fn(prior_key) if callable(prior_fn) else None
            if prior is not None:
                return True, "This locked-slot proposal was already committed; the existing receipt was returned.", deepcopy(prior)
            return False, "This locked-slot proposal has already been committed.", deepcopy(proposal)
        option = proposal["options"][option_index]
        operation_key = f"booking-workbench:{proposal.get('proposal_id', '')}:option:{option_index}"
        quote_fn = getattr(self, "foundation_quote", None)
        details = {"proposal_id": proposal.get("proposal_id", ""), "booking_id": proposal.get("booking_id", ""), "corner_index": int(proposal.get("corner_index", 0) or 0)}
        quote = quote_fn("booking", "edit_locked_slot", proposal.get("booking_id", ""), amount=0, details=details) if callable(quote_fn) else None

        def validate():
            review = self.review_locked_slot_proposal(proposal.get("proposal_id", ""))
            if not review or review.get("current_status") in ("Stale", "Unavailable"):
                return False, (review or {}).get("current_reason", "The draft slot changed and must be reviewed again.")
            row = review.get("options", [])[option_index]
            if row.get("current_status") != "Eligible":
                return False, "; ".join(row.get("current_blocks", [])) or "The selected alternative is no longer eligible."
            return True

        def apply():
            _index, fight = self._booking_locked_slot(proposal.get("booking_id", ""))
            if fight is None or self._booking_fight_fingerprint(fight) != str(proposal.get("original_fight_fingerprint", "") or ""):
                raise ValueError("The draft slot changed after review; no replacement was applied.")
            new_fighter = self._booking_resolve_fighter(option.get("fighter_id", ""))
            if new_fighter is None:
                raise ValueError("The selected fighter is no longer available.")
            corner = int(proposal.get("corner_index", 0) or 0)
            ids = list(fight.get("fighter_ids", []) or [])
            names = list(fight.get("fighters", []) or [])
            while len(ids) < 2: ids.append("TBA")
            while len(names) < 2: names.append("TBA")
            ids[corner] = str(getattr(new_fighter, "fighter_id", "") or option.get("fighter_id", ""))
            names[corner] = str(getattr(new_fighter, "name", option.get("name", "Unknown")))
            fight["fighter_ids"], fight["fighters"] = ids, names
            history = fight.setdefault("replacement_history", [])
            if not isinstance(history, list): history = []; fight["replacement_history"] = history
            original_ids = list(proposal.get("original_fighter_ids", []) or [])
            original_names = list(proposal.get("original_participants", []) or [])
            history.append({
                "source": "Locked-slot proposal",
                "proposal_id": str(proposal.get("proposal_id", "")),
                "booking_id": str(proposal.get("booking_id", "")),
                "corner_index": corner,
                "removed_fighter_id": str(original_ids[corner] if corner < len(original_ids) else ""),
                "removed_name": str(original_names[corner] if corner < len(original_names) else ""),
                "replacement_fighter_id": ids[corner],
                "replacement_name": names[corner],
                "recorded_month": int(getattr(self, "month", 0) or 0),
                "recorded_week": int(getattr(self, "week", 0) or 0),
            })
            ensure_ids = getattr(self, "ensure_booking_ids", None)
            if callable(ensure_ids): ensure_ids()
            proposal["status"] = "Committed"
            proposal["selected_option"] = option_index
            proposal["committed_fighter_ids"] = ids[:2]
            return {"proposal_id": proposal.get("proposal_id", ""), "booking_id": proposal.get("booking_id", ""), "option_index": option_index, "fighter_ids": ids[:2]}

        def snapshot_domain():
            booked_ref = getattr(self, "booked", None)
            return (deepcopy(booked_ref) if isinstance(booked_ref, list) else None, deepcopy(state.get("locked_slot_proposals", [])))

        def restore_domain(snapshot):
            booked_snapshot, proposals_snapshot = snapshot if isinstance(snapshot, tuple) and len(snapshot) == 2 else (None, None)
            if isinstance(booked_snapshot, list) and isinstance(getattr(self, "booked", None), list):
                self.booked[:] = booked_snapshot
            if isinstance(proposals_snapshot, list):
                state["locked_slot_proposals"] = proposals_snapshot

        commit_fn = getattr(self, "foundation_commit", None)
        if callable(commit_fn):
            receipt = commit_fn(operation_key, domain="booking", action="edit_locked_slot", target_id=proposal.get("booking_id", ""), quote=quote, validate=validate, apply=apply, snapshot=snapshot_domain, restore=restore_domain)
            if receipt.get("status") != "committed":
                return False, receipt.get("error", "The locked-slot proposal was not committed."), deepcopy(receipt)
            return True, "Locked-slot proposal committed; one corner was replaced and the rest of the card was preserved.", deepcopy(receipt)
        verdict = validate()
        if verdict is False or (isinstance(verdict, tuple) and verdict and verdict[0] is False):
            return False, str(verdict[1] if isinstance(verdict, tuple) and len(verdict) > 1 else "The locked-slot proposal was rejected."), None
        return True, "Locked-slot proposal committed; one corner was replaced and the rest of the card was preserved.", deepcopy(apply())

    def commit_locked_slot_proposal_for_fighter(self, proposal_id, fighter_id):
        """Commit one locked-slot alternative by its saved fighter identity."""
        target_id = str(fighter_id or "").strip()
        if not target_id:
            return False, "That replacement has no stable fighter identity and cannot be committed safely.", None
        raw_state = self._booking_workbench_raw_state()
        raw_rows = raw_state.get("locked_slot_proposals", []) if isinstance(raw_state, dict) else []
        proposal = next((row for row in raw_rows if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None) if isinstance(raw_rows, list) else None
        options = proposal.get("options", []) if isinstance(proposal, dict) else []
        if not isinstance(options, list):
            return False, "The saved replacement evidence is malformed; no replacement was applied.", None
        matches = [
            index for index, row in enumerate(options)
            if isinstance(row, dict) and str(row.get("fighter_id", "") or "").strip() == target_id
        ]
        if len(matches) != 1:
            return False, (
                "That replacement identity is no longer available in this proposal."
                if not matches else
                "The saved proposal contains duplicate fighter identities; no replacement was applied."
            ), None
        return self.commit_locked_slot_proposal(proposal_id, matches[0])

    def booking_workbench_medical_preview(self, fighter_id, target_month=None, target_week=None):
        """Return factual return/camp information for a non-binding draft.

        This adapter intentionally does not reserve a fighter or promise a
        recovery date.  The ordinary medical check remains authoritative when
        the event week is reached.
        """
        fighter = self._booking_resolve_fighter(fighter_id)
        if fighter is None:
            return {
                "fighter_id": str(fighter_id or ""), "status": "Unavailable",
                "earliest_return": "Unknown", "camp": "No camp record",
                "medical_blocks": ["fighter identity is no longer available"],
                "binding": False,
            }
        target_month = int(target_month if target_month is not None else getattr(self, "month", 1) or 1)
        target_week = int(target_week if target_week is not None else getattr(self, "week", 1) or 1)
        calendar_fn = getattr(self, "calendar_week_index", None)
        target_index = int(calendar_fn(target_month, target_week) if callable(calendar_fn) else ((target_month - 1) * 4 + target_week))
        available_week = max(0, int(getattr(fighter, "available_week", 0) or 0))
        if not available_week or available_week <= target_index:
            earliest_return = "Now"
        else:
            parts_fn = getattr(self, "day_index_parts", None)
            date_fn = getattr(self, "format_game_date", None)
            if callable(parts_fn) and callable(date_fn):
                try:
                    return_month, return_week, _day = parts_fn(available_week * 7 - 6)
                    earliest_return = str(date_fn(return_month, return_week))
                except Exception:
                    earliest_return = f"Calendar week {available_week}"
            else:
                earliest_return = f"Calendar week {available_week}"
        medical_blocks = []
        if bool(getattr(fighter, "injured", False)):
            medical_blocks.append("injured")
        if available_week and available_week > target_index:
            medical_blocks.append("not medically available on the selected date")
        if not medical_blocks:
            status = "Ready to confirm"
        elif bool(getattr(fighter, "injured", False)):
            status = "Medical hold"
        else:
            status = "Return-date hold"
        camp_weeks = max(0, int(getattr(fighter, "camp_weeks", 0) or 0))
        camp_quality = max(0, int(getattr(fighter, "camp_quality", 0) or 0))
        camp = f"{camp_weeks} weeks recorded (quality {camp_quality}); no camp reserved by this draft"
        return {
            "fighter_id": str(getattr(fighter, "fighter_id", "") or fighter_id or ""),
            "fighter_name": str(getattr(fighter, "name", "Unknown")),
            "target_month": target_month, "target_week": target_week,
            "status": status, "earliest_return": earliest_return,
            "available_week": available_week, "camp": camp,
            "camp_weeks": camp_weeks, "camp_quality": camp_quality,
            "medical_blocks": list(dict.fromkeys(medical_blocks)),
            "binding": False,
            "confirmation_rule": "Re-run the normal medical and booking checks at the event-week boundary.",
        }

    def booking_workbench_medical_plans(self):
        state = self._booking_workbench_raw_state()
        plans = state.get("medical_plans", [])
        return deepcopy(plans) if isinstance(plans, list) else []

    def save_tentative_medical_slot(self, anchor_id, candidate_id, target_month=None, target_week=None):
        """Persist a non-binding medical planning note for one proposal option."""
        state = self.ensure_booking_workbench_state()
        anchor = self._booking_resolve_fighter(anchor_id)
        candidate = self._booking_resolve_fighter(candidate_id)
        if anchor is None or candidate is None:
            return False, "The anchor or medical candidate is no longer on the player roster.", None
        if anchor is candidate:
            return False, "Choose a different fighter for the medical planning slot.", None
        if getattr(anchor, "gender", "") != getattr(candidate, "gender", "") or getattr(anchor, "weight", "") != getattr(candidate, "weight", ""):
            return False, "Medical planning only supports the anchor's same division.", None
        target_month = int(target_month if target_month is not None else getattr(self, "month", 1) or 1)
        target_week = int(target_week if target_week is not None else getattr(self, "week", 1) or 1)
        preview = self.booking_workbench_medical_preview(candidate_id, target_month, target_week)
        if not preview.get("medical_blocks"):
            return False, "This fighter is ready to confirm; use Fill Selected Slot after the normal eligibility review.", None
        for plan in state.get("medical_plans", []):
            if (plan.get("anchor_id") == str(getattr(anchor, "fighter_id", "") or anchor_id)
                    and plan.get("candidate_id") == str(getattr(candidate, "fighter_id", "") or candidate_id)
                    and int(plan.get("target_month", 0) or 0) == target_month
                    and int(plan.get("target_week", 0) or 0) == target_week):
                return True, "That tentative medical slot already exists; the existing draft was returned.", deepcopy(plan)
        plan = {
            "plan_id": self._booking_workbench_next_id("medical"),
            "anchor_id": str(getattr(anchor, "fighter_id", "") or anchor_id),
            "anchor_name": str(getattr(anchor, "name", "Unknown")),
            "candidate_id": str(getattr(candidate, "fighter_id", "") or candidate_id),
            "candidate_name": str(getattr(candidate, "name", "Unknown")),
            "target_month": target_month, "target_week": target_week,
            "created_month": int(getattr(self, "month", target_month) or target_month),
            "created_week": int(getattr(self, "week", target_week) or target_week),
            "status": "Tentative", "binding": False,
            "preview": deepcopy(preview),
            "note": "No fighter, camp, cash or booking was reserved. Confirm through the normal medical checks at event week.",
        }
        state.setdefault("medical_plans", []).append(plan)
        state["medical_plans"] = state["medical_plans"][-40:]
        return True, f"Saved {plan['plan_id']} as a tentative medical slot; it is not a booking.", deepcopy(plan)

    def review_tentative_medical_slot(self, plan_id):
        """Return current status while keeping the stored draft immutable."""
        state = self._booking_workbench_raw_state()
        plans = state.get("medical_plans", [])
        if not isinstance(plans, list):
            return None
        plan = next((row for row in plans if isinstance(row, dict) and row.get("plan_id") == str(plan_id or "")), None)
        if not plan:
            return None
        current = deepcopy(plan)
        candidate = self._booking_resolve_fighter(plan.get("candidate_id", ""))
        if candidate is None:
            current["current_status"] = "Unavailable"
            current["current_reason"] = "The candidate identity is no longer available."
            return current
        preview = self.booking_workbench_medical_preview(plan.get("candidate_id", ""), plan.get("target_month"), plan.get("target_week"))
        calendar_fn = getattr(self, "calendar_week_index", None)
        now_index = int(calendar_fn() if callable(calendar_fn) else ((int(getattr(self, "month", 1) or 1) - 1) * 4 + int(getattr(self, "week", 1) or 1)))
        target_index = int(calendar_fn(plan.get("target_month"), plan.get("target_week")) if callable(calendar_fn) else ((int(plan.get("target_month", 1) or 1) - 1) * 4 + int(plan.get("target_week", 1) or 1)))
        if now_index > target_index:
            current["current_status"] = "Needs replacement"
            current["current_reason"] = "The target date has passed; this draft cannot execute retroactively."
        elif not preview.get("medical_blocks"):
            current["current_status"] = "Ready to confirm"
            current["current_reason"] = "The candidate is now clear, but ordinary booking checks still apply."
        else:
            current["current_status"] = "Tentative"
            current["current_reason"] = "; ".join(preview.get("medical_blocks", []))
        current["current_preview"] = preview
        return current

    def _booking_hard_reasons(self, fighter, target_month, target_week, *, anchor=None):
        reasons = []
        if fighter is None:
            return ["Fighter identity is not available"]
        try:
            target_month = int(target_month)
            target_week = int(target_week)
        except (TypeError, ValueError):
            return ["The selected booking date is unavailable"]
        calendar_index = getattr(self, "calendar_week_index", None)
        try:
            if callable(calendar_index):
                now_index = int(calendar_index())
                target_index = int(calendar_index(target_month, target_week))
            else:
                now_index = ((int(getattr(self, "month", 1) or 1) - 1) * 4
                             + int(getattr(self, "week", 1) or 1))
                target_index = ((target_month - 1) * 4) + target_week
            if target_index < now_index:
                reasons.append("the selected booking date has already passed")
        except (TypeError, ValueError, AttributeError):
            reasons.append("the selected booking date could not be verified")
        if anchor is not None and fighter is anchor:
            reasons.append("same fighter")
        if anchor is not None and getattr(fighter, "gender", "") != getattr(anchor, "gender", ""):
            reasons.append("different gender division")
        if anchor is not None and getattr(fighter, "weight", "") != getattr(anchor, "weight", ""):
            reasons.append("different weight class")
        if bool(getattr(fighter, "retired", False) or getattr(fighter, "retirement_pending", False)):
            reasons.append("retired or retirement pending")
        if bool(getattr(fighter, "injured", False)):
            reasons.append("injured")
        available = getattr(self, "fighter_available_for_date", None)
        if callable(available):
            try:
                if not available(fighter, target_month, target_week, getattr(self, "selected_booking_day", lambda: None)()):
                    reasons.append("not medically available on the selected date")
            except TypeError:
                try:
                    if not available(fighter, target_month, target_week):
                        reasons.append("not medically available on the selected date")
                except Exception:
                    reasons.append("medical availability could not be verified")
            except Exception:
                reasons.append("medical availability could not be verified")
        if int(getattr(fighter, "fatigue", 0) or 0) >= 65:
            reasons.append("fatigue is at the booking block threshold")
        closed = set(getattr(self, "closed_divisions", set()) or ())
        belt_key = getattr(self, "belt_key", None)
        if callable(belt_key):
            try:
                if belt_key(fighter.gender, fighter.weight) in closed:
                    reasons.append("division is closed")
            except Exception:
                pass
        busy = getattr(self, "fighter_has_scheduled_fight", None)
        if callable(busy):
            try:
                if busy(fighter, include_booked=True):
                    reasons.append("already has a future or draft booking")
            except TypeError:
                try:
                    if busy(fighter):
                        reasons.append("already has a future booking")
                except Exception:
                    pass
            except Exception:
                pass
        if anchor is not None:
            stale_fn = getattr(self, "ai_matchup_is_stale", None)
            if callable(stale_fn):
                try:
                    if stale_fn(anchor, fighter, title=False, target_month=target_month):
                        reasons.append("rematch cooldown or repeated-series limit")
                except TypeError:
                    try:
                        if stale_fn(anchor, fighter):
                            reasons.append("rematch cooldown or repeated-series limit")
                    except Exception:
                        reasons.append("rematch history could not be verified")
                except Exception:
                    reasons.append("rematch history could not be verified")
        return list(dict.fromkeys(reasons))

    def _booking_pair_hard_reasons(self, anchor, opponent, target_month, target_week,
                                   *, title=False, special_belt=""):
        """Apply pair-level sporting rules at the workbench commit boundary.

        Candidate generation is intentionally useful as a broad planning view,
        but a saved alternative must not become a bypass around the ordinary
        title, belt, or identity rules when the player confirms it.
        """
        reasons = []
        if anchor is None or opponent is None:
            return ["The anchor or selected opponent is no longer available"]
        if getattr(anchor, "gender", "") != getattr(opponent, "gender", ""):
            reasons.append("different gender division")
        if getattr(anchor, "weight", "") != getattr(opponent, "weight", ""):
            reasons.append("different weight class")

        if title:
            # A recognised holder must be present for a non-vacant divisional
            # belt.  Use the same retained belt projection as the booking UI;
            # if that reader is unavailable, the champion flags still protect
            # an explicitly held belt.
            belt_key_fn = getattr(self, "belt_key", None)
            normalize_belts = getattr(self, "normalize_belts", None)
            if callable(belt_key_fn) and callable(normalize_belts):
                try:
                    key = belt_key_fn(anchor.gender, anchor.weight)
                    holder = str(normalize_belts(getattr(self, "belts", {})).get(key, "") or "")
                    if holder and holder not in {getattr(anchor, "name", ""), getattr(opponent, "name", "")}:
                        reasons.append("the current divisional champion must be included")
                except Exception:
                    reasons.append("the current divisional champion could not be verified")
            holders = [fighter for fighter in (anchor, opponent)
                       if bool(getattr(fighter, "champion", False)
                               or getattr(fighter, "interim_champion", False))]
            if len(holders) > 1:
                reasons.append("both corners are marked as champions")
            eligibility_fn = getattr(self, "ai_title_challenger_is_eligible", None)
            if callable(eligibility_fn):
                contenders = [fighter for fighter in (anchor, opponent) if fighter not in holders]
                for contender in contenders:
                    try:
                        if not eligibility_fn(contender):
                            reasons.append(f"{getattr(contender, 'name', 'The challenger')} does not meet the title-challenger merit rule")
                    except Exception:
                        reasons.append("title-challenger merit could not be verified")
            else:
                title_advice = getattr(self, "assistant_title_recommendation", None)
                if holders and callable(title_advice):
                    try:
                        if not title_advice(anchor, opponent, rank_map=getattr(self, "player_division_rank_map", lambda: None)()):
                            reasons.append("the challenger does not meet the current title path")
                    except Exception:
                        reasons.append("title-challenger merit could not be verified")

        if special_belt:
            belt_error = getattr(self, "special_belt_booking_error", None)
            if callable(belt_error):
                try:
                    message = belt_error(special_belt, (anchor, opponent))
                except Exception:
                    message = "the selected special belt could not be verified"
                if message:
                    reasons.append(str(message))
        return list(dict.fromkeys(reasons))

    def _booking_rank_snapshot(self, fighter):
        identity = str(getattr(fighter, "fighter_id", "") or getattr(fighter, "name", ""))
        company_rank = None
        world_rank = "-"
        rank_map = getattr(self, "player_division_rank_map", None)
        if callable(rank_map):
            try:
                key = getattr(self, "fighter_identity_key", lambda value: str(getattr(value, "fighter_id", "") or value.name))(fighter)
                rank = rank_map().get(key)
                company_rank = "C" if rank == 0 else (f"#{rank}" if rank else "-")
            except Exception:
                pass
        world_maps = getattr(self, "division_rank_maps", None)
        rows_fn = getattr(self, "unfiltered_ranked_fighter_rows", None)
        if callable(world_maps) and callable(rows_fn):
            try:
                _company, world = world_maps(rows_fn())
                key = getattr(self, "fighter_identity_key", lambda value: str(getattr(value, "fighter_id", "") or value.name))(fighter)
                world_rank = world.get(key, "-")
            except Exception:
                pass
        if company_rank is None:
            rank = int(getattr(fighter, "ranking_position", 0) or 0)
            company_rank = "C" if getattr(fighter, "champion", False) else (f"#{rank}" if rank else "-")
        return identity, company_rank, world_rank

    def _booking_advisory(self, anchor, opponent, target_month):
        warnings = []
        warning_fn = getattr(self, "assistant_pair_booking_warning", None)
        if callable(warning_fn):
            try:
                warning = warning_fn(anchor, opponent, rank_map=self.player_division_rank_map(), target_month=target_month)
                if warning:
                    warnings.append(str(warning))
            except Exception:
                pass
        return list(dict.fromkeys(warnings))

    def booking_workbench_candidate_rows(self, anchor_id, target_month=None, target_week=None, *, include_blocked=True, limit=12):
        """Return deterministic alternatives with separate blockers/cautions."""
        anchor = self._booking_resolve_fighter(anchor_id)
        if target_month is None:
            target_month = int(getattr(self, "month", 1) or 1)
        if target_week is None:
            target_week = int(getattr(self, "week", 1) or 1)
        rows = []
        if anchor is None:
            return rows
        score_fn = getattr(self, "matchmaking_score", None)
        fit_fn = getattr(self, "matchmaking_fit_score", None)
        build_fn = getattr(self, "match_build_score", None)
        rank_map_fn = getattr(self, "player_division_rank_map", None)
        rank_map = rank_map_fn() if callable(rank_map_fn) else None
        for opponent in getattr(self, "roster", []) or []:
            hard = self._booking_hard_reasons(opponent, target_month, target_week, anchor=anchor)
            if hard and not include_blocked:
                continue
            cautions = []
            if not hard:
                cautions = self._booking_advisory(anchor, opponent, target_month)
                brief = self.booking_workbench_brief_snapshot()
                if brief and int(brief.get("opposition_gap", 12) or 12) < abs(int(getattr(anchor, "overall", 0) or 0) - int(getattr(opponent, "overall", 0) or 0)):
                    cautions.append(f"outside the brief's {brief['opposition_gap']}-point OVR range")
            score = -999.0
            build = 0
            reason = ""
            if not hard:
                try:
                    if callable(score_fn):
                        score, reason = score_fn(anchor, opponent, rank_map=rank_map)
                    if callable(fit_fn):
                        fit = fit_fn(anchor, opponent)
                    else:
                        fit = max(1, min(99, round(50 - abs(anchor.overall - opponent.overall) * 2)))
                    if callable(build_fn):
                        build = build_fn(anchor, opponent, {"title": False, "main": False}, rank_map=rank_map)
                    else:
                        build = max(1, min(99, round((anchor.popularity + opponent.popularity) / 2)))
                except Exception as exc:
                    fit = 0
                    cautions.append(f"matchup score unavailable: {exc}")
            else:
                fit = 0
            identity, company_rank, world_rank = self._booking_rank_snapshot(opponent)
            rows.append({
                "fighter_id": identity,
                "name": str(getattr(opponent, "name", "Unknown")),
                "gender": str(getattr(opponent, "gender", "")),
                "weight": str(getattr(opponent, "weight", "")),
                "company_rank": company_rank,
                "world_rank": world_rank,
                "record": str(getattr(opponent, "record", "")),
                "overall": int(getattr(opponent, "overall", 0) or 0),
                "popularity": int(getattr(opponent, "popularity", 0) or 0),
                "fit": int(fit or 0),
                "build": int(build or 0),
                "score": round(float(score), 3),
                "reason": str(reason or ""),
                "hard_blocks": hard,
                "cautions": cautions,
                "generation_status": "Eligible" if not hard else "Blocked",
                "medical_preview": self.booking_workbench_medical_preview(
                    getattr(opponent, "fighter_id", ""), target_month, target_week,
                ),
                "fighter": opponent,
            })
        eligible = [row for row in rows if not row["hard_blocks"]]
        blocked = [row for row in rows if row["hard_blocks"]]
        emphasis = (self.booking_workbench_brief_snapshot() or {}).get("emphasis", "Balanced")
        def sort_key(row):
            fighter = row.get("fighter")
            if emphasis == "Development":
                emphasis_score = -int(getattr(fighter, "age", 30) or 30) * 0.8 + (100 - row["overall"]) * 0.35
            elif emphasis == "Commercial":
                emphasis_score = row["build"] * 0.9 + row["popularity"] * 0.45
            elif emphasis == "Sporting":
                emphasis_score = row["fit"] * 0.9 + row["score"] * 0.25
            else:
                emphasis_score = row["score"] * 0.55 + row["build"] * 0.35 + row["fit"] * 0.25
            return (emphasis_score, row["fit"], row["build"], -row["overall"], str(row["fighter_id"]))
        eligible.sort(key=sort_key, reverse=True)
        # Keep blocked rows available as explicit explanations, but cap them
        # after eligible choices so a shallow division does not bury usable work.
        return deepcopy((eligible + blocked)[:max(1, min(100, int(limit or 12)))])

    def generate_booking_proposal(self, anchor_id, target_month=None, target_week=None, *, limit=6):
        """Explicitly generate and persist one deterministic proposal snapshot."""
        state = self.ensure_booking_workbench_state()
        anchor = self._booking_resolve_fighter(anchor_id)
        if anchor is None:
            return False, "The selected fighter is no longer available for a proposal.", None
        target_month = int(target_month if target_month is not None else getattr(self, "month", 1) or 1)
        target_week = int(target_week if target_week is not None else getattr(self, "week", 1) or 1)
        rows = self.booking_workbench_candidate_rows(anchor_id, target_month, target_week, include_blocked=True, limit=max(6, int(limit or 6) * 2))
        options = []
        for row in rows:
            option = {key: deepcopy(value) for key, value in row.items() if key != "fighter"}
            options.append(option)
        proposal = {
            "proposal_id": self._booking_workbench_next_id("proposal"),
            "brief_id": str((state.get("brief") or {}).get("brief_id", "") or ""),
            "brief_revision": int((state.get("brief") or {}).get("revision", 0) or 0),
            "anchor_id": str(getattr(anchor, "fighter_id", "") or anchor_id),
            "anchor_name": str(getattr(anchor, "name", "Unknown")),
            "target_month": target_month,
            "target_week": target_week,
            "generated_month": int(getattr(self, "month", target_month) or target_month),
            "generated_week": int(getattr(self, "week", target_week) or target_week),
            "emphasis": str((state.get("brief") or {}).get("emphasis", "Balanced")),
            "status": "Draft",
            "selected_option": None,
            "options": options[:max(1, min(12, int(limit or 6)))],
        }
        state["proposals"].append(proposal)
        state["proposals"] = state["proposals"][-40:]
        if not any(not row.get("hard_blocks") for row in proposal["options"]):
            return True, f"{proposal['proposal_id']} saved, but no eligible alternative is available on the selected date.", deepcopy(proposal)
        return True, f"{proposal['proposal_id']} saved with {sum(1 for row in proposal['options'] if not row.get('hard_blocks'))} eligible alternative(s).", deepcopy(proposal)

    def review_booking_proposal(self, proposal_id):
        """Return a current read model while preserving the generated snapshot."""
        state = self._booking_workbench_raw_state()
        proposals = state.get("proposals", [])
        if not isinstance(proposals, list):
            return None
        proposal = next((row for row in proposals if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None)
        if not proposal:
            return None
        current = deepcopy(proposal)
        anchor = self._booking_resolve_fighter(proposal.get("anchor_id", ""))
        snapshots = proposal.get("options", [])
        if not isinstance(snapshots, list):
            current["options"] = []
            current["current_status"] = "Unavailable"
            current["current_reason"] = "Saved alternative evidence is malformed; no opponent can be selected."
            return current
        current_rows = {row.get("fighter_id"): row for row in self.booking_workbench_candidate_rows(
            proposal.get("anchor_id", ""), proposal.get("target_month", getattr(self, "month", 1)),
            proposal.get("target_week", getattr(self, "week", 1)), include_blocked=True, limit=100,
        )} if anchor is not None else {}
        refreshed = []
        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                refreshed.append({
                    "raw_snapshot": deepcopy(snapshot),
                    "current_status": "Unavailable",
                    "current_blocks": ["saved alternative evidence is malformed"],
                })
                continue
            option = deepcopy(snapshot)
            live = current_rows.get(option.get("fighter_id"))
            if live is None:
                option["current_status"] = "Unavailable"
                option.setdefault("current_blocks", ["fighter identity is no longer available"])
            else:
                option["current_status"] = "Eligible" if not live.get("hard_blocks") else "Blocked"
                option["current_blocks"] = list(live.get("hard_blocks", []))
                option["current_cautions"] = list(live.get("cautions", []))
                option["current_medical_preview"] = deepcopy(live.get("medical_preview", {}))
            refreshed.append(option)
        current["options"] = refreshed
        current["current_status"] = "Review required" if anchor is None else str(proposal.get("status", "Draft"))
        return current

    def _booking_workbench_commit_apply(self, proposal, option_index, *, title=False,
                                        special_belt="", main=None, tier="Main Card"):
        option = proposal.get("options", [])[option_index]
        anchor = self._booking_resolve_fighter(proposal.get("anchor_id", ""))
        opponent = self._booking_resolve_fighter(option.get("fighter_id", ""))
        if anchor is None or opponent is None:
            raise ValueError("The anchor or selected opponent is no longer available.")
        hard = self._booking_hard_reasons(anchor, proposal.get("target_month"), proposal.get("target_week"))
        hard += self._booking_hard_reasons(opponent, proposal.get("target_month"), proposal.get("target_week"), anchor=anchor)
        hard += self._booking_pair_hard_reasons(
            anchor, opponent, proposal.get("target_month"), proposal.get("target_week"),
            title=bool(title), special_belt=special_belt,
        )
        if hard:
            raise ValueError("; ".join(dict.fromkeys(hard)))
        if getattr(anchor, "gender", "") != getattr(opponent, "gender", "") or getattr(anchor, "weight", "") != getattr(opponent, "weight", ""):
            raise ValueError("The selected opponents no longer share a bookable division.")
        booked = getattr(self, "booked", None)
        if not isinstance(booked, list):
            booked = []
            self.booked = booked
        make_main = bool(main) if main is not None else not booked
        append_pair = getattr(self, "_append_draft_matchup", None)
        if callable(append_pair):
            fight = append_pair(
                anchor, opponent, title=title, main=make_main, tier=tier,
                special_belt=special_belt,
                fight_plans={anchor.fighter_id: "Balanced", opponent.fighter_id: "Balanced"},
                booking_reason=f"Explicit booking-workbench proposal {proposal.get('proposal_id', '')}",
            )
        else:
            booked = getattr(self, "booked", None)
            if not isinstance(booked, list):
                booked = []
                self.booked = booked
            if make_main:
                for fight in booked:
                    if isinstance(fight, dict):
                        fight["main"] = False
            fight = {
                "fighters": [anchor.name, opponent.name],
                "fighter_ids": [anchor.fighter_id, opponent.fighter_id],
                "fight_plans": {anchor.fighter_id: "Balanced", opponent.fighter_id: "Balanced"},
                "title": bool(title or special_belt), "divisional_title": bool(title), "interim": False,
                "special_belt": str(special_belt or ""), "main": make_main, "tier": str(tier or "Main Card"),
                "booking_reason": f"Explicit booking-workbench proposal {proposal.get('proposal_id', '')}",
            }
            booked.append(fight)
            normalizer = getattr(self, "normalize_card_order", None)
            if callable(normalizer):
                normalizer()
        fight.setdefault("booking_workbench", {
            "proposal_id": str(proposal.get("proposal_id", "")),
            "option_index": int(option_index),
            "generated_target_month": int(proposal.get("target_month", 0) or 0),
            "generated_target_week": int(proposal.get("target_week", 0) or 0),
        })
        ensure_booking_ids = getattr(self, "ensure_booking_ids", None)
        if callable(ensure_booking_ids):
            ensure_booking_ids()
        proposal["status"] = "Committed"
        proposal["selected_option"] = int(option_index)
        proposal["committed_fighter_ids"] = [anchor.fighter_id, opponent.fighter_id]
        return {"proposal_id": proposal.get("proposal_id", ""), "option_index": int(option_index), "fighter_ids": [anchor.fighter_id, opponent.fighter_id]}

    def commit_booking_proposal(self, proposal_id, option_index, *, title=False,
                                special_belt="", main=None, tier="Main Card"):
        """Commit one reviewed option exactly once through Foundation."""
        # Validate the retained option before the explicit write-boundary
        # normaliser can filter malformed legacy rows. Rejected evidence must
        # remain available for review rather than being silently rewritten.
        raw_state = self._booking_workbench_raw_state()
        raw_rows = raw_state.get("proposals", []) if isinstance(raw_state, dict) else []
        raw_proposal = next((row for row in raw_rows if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None) if isinstance(raw_rows, list) else None
        if raw_proposal is not None:
            try:
                raw_index = int(option_index)
            except (TypeError, ValueError):
                return False, "Choose one of the listed alternatives.", None
            raw_options = raw_proposal.get("options", [])
            if not isinstance(raw_options, list) or raw_index < 0 or raw_index >= len(raw_options):
                return False, "The saved alternative evidence is malformed; no opponent was booked.", None
            if not isinstance(raw_options[raw_index], dict):
                return False, "The saved alternative evidence is malformed; no opponent was booked.", None
        state = self.ensure_booking_workbench_state()
        proposal = next((row for row in state.get("proposals", []) if row.get("proposal_id") == str(proposal_id or "")), None)
        if not proposal:
            return False, "That booking proposal no longer exists.", None
        try:
            option_index = int(option_index)
            if option_index < 0 or option_index >= len(proposal.get("options", [])):
                raise ValueError("Choose one of the listed alternatives.")
        except (TypeError, ValueError) as exc:
            return False, str(exc), None
        if not isinstance(proposal.get("options", [])[option_index], dict):
            return False, "The saved alternative evidence is malformed; no opponent was booked.", None
        if proposal.get("status") == "Committed":
            # A repeated click should resolve to the sealed Foundation result,
            # not create a second bout.  The proposal itself remains terminal.
            prior_index = proposal.get("selected_option")
            if prior_index is not None and int(prior_index) == option_index:
                prior_key = f"booking-workbench:{proposal.get('proposal_id', '')}:option:{option_index}"
                prior_receipt_fn = getattr(self, "foundation_get_receipt", None)
                prior_receipt = prior_receipt_fn(prior_key) if callable(prior_receipt_fn) else None
                if prior_receipt is not None:
                    return True, "This proposal was already committed; the existing receipt was returned.", prior_receipt
            return False, "This proposal has already filled a card slot.", deepcopy(proposal)
        option = proposal["options"][option_index]
        operation_key = f"booking-workbench:{proposal.get('proposal_id', '')}:option:{option_index}"
        quote_fn = getattr(self, "foundation_quote", None)
        commit_fn = getattr(self, "foundation_commit", None)
        details = {
            "proposal_id": proposal.get("proposal_id", ""), "option_index": option_index,
            "tier": str(tier or "Main Card"), "title": bool(title),
            "special_belt": str(special_belt or ""),
        }
        quote = quote_fn("booking", "fill_proposal", option.get("fighter_id", ""), amount=0, details=details) if callable(quote_fn) else None

        def validate():
            review = self.review_booking_proposal(proposal.get("proposal_id", ""))
            if not review:
                return False, "The proposal could not be re-read."
            row = review.get("options", [])[option_index]
            if row.get("current_status") != "Eligible":
                return False, "; ".join(row.get("current_blocks", [])) or "The selected alternative is no longer eligible."
            anchor = self._booking_resolve_fighter(proposal.get("anchor_id", ""))
            opponent = self._booking_resolve_fighter(row.get("fighter_id", ""))
            pair_blocks = self._booking_pair_hard_reasons(
                anchor, opponent, proposal.get("target_month"), proposal.get("target_week"),
                title=bool(title), special_belt=special_belt,
            )
            if pair_blocks:
                return False, "; ".join(pair_blocks)
            selected_date = getattr(self, "selected_booking_date", None)
            if callable(selected_date):
                try:
                    live_date = selected_date(reject_past=False)
                except TypeError:
                    try:
                        live_date = selected_date()
                    except Exception:
                        live_date = None
                except Exception:
                    live_date = None
                if live_date:
                    try:
                        live_pair = tuple(live_date[:2])
                    except (TypeError, ValueError):
                        live_pair = ()
                    if live_pair and live_pair != (
                        int(proposal.get("target_month", 0) or 0),
                        int(proposal.get("target_week", 0) or 0),
                    ):
                        return False, "The selected booking date changed; generate a fresh proposal for the new date."
            if proposal.get("brief_id") and proposal.get("brief_revision"):
                brief = self.booking_workbench_brief_snapshot()
                if brief and brief.get("brief_id") == proposal.get("brief_id") and int(brief.get("revision", 0) or 0) != int(proposal.get("brief_revision", 0) or 0):
                    return False, "The booking brief changed; generate a fresh proposal before filling it."
            return True

        def apply():
            # ``review_booking_proposal`` defensively normalises its read model.
            # Re-resolve the save-owned row after validation so the apply step
            # cannot mutate a stale pre-normalisation dictionary.
            live_state = self.ensure_booking_workbench_state()
            live_proposal = next((row for row in live_state.get("proposals", []) if row.get("proposal_id") == proposal.get("proposal_id")), None)
            if live_proposal is None:
                raise ValueError("The booking proposal disappeared during validation.")
            return self._booking_workbench_commit_apply(
                live_proposal, option_index, title=title, special_belt=special_belt,
                main=main, tier=tier,
            )

        if callable(commit_fn):
            receipt = commit_fn(operation_key, domain="booking", action="fill_proposal", target_id=option.get("fighter_id", ""), quote=quote, validate=validate, apply=apply)
            if receipt.get("status") != "committed":
                return False, receipt.get("error", "The booking proposal was not committed."), deepcopy(receipt)
            return True, "Booking proposal committed to the draft card.", deepcopy(receipt)
        verdict = validate()
        if verdict is not True and (not isinstance(verdict, tuple) or verdict[0] is False):
            return False, str(verdict[1] if isinstance(verdict, tuple) and len(verdict) > 1 else "The booking proposal was rejected."), None
        result = apply()
        return True, "Booking proposal committed to the draft card.", deepcopy(result)

    def commit_booking_proposal_for_fighter(self, proposal_id, fighter_id, *, title=False,
                                            special_belt="", main=None, tier="Main Card"):
        """Commit a workbench option by its saved fighter identity.

        The legacy index API remains available for compatibility and regression
        fixtures, but UI actions must not turn a visible row position into the
        option after a refresh. Resolve the durable candidate ID from the raw
        proposal, fail closed on missing/duplicate identities, then delegate to
        the existing exactly-once commit owner.
        """
        target_id = str(fighter_id or "").strip()
        if not target_id:
            return False, "That alternative has no stable fighter identity and cannot be committed safely.", None
        raw_state = self._booking_workbench_raw_state()
        raw_rows = raw_state.get("proposals", []) if isinstance(raw_state, dict) else []
        proposal = next((row for row in raw_rows if isinstance(row, dict) and row.get("proposal_id") == str(proposal_id or "")), None) if isinstance(raw_rows, list) else None
        options = proposal.get("options", []) if isinstance(proposal, dict) else []
        if not isinstance(options, list):
            return False, "The saved alternative evidence is malformed; no opponent was booked.", None
        matches = [
            index for index, row in enumerate(options)
            if isinstance(row, dict) and str(row.get("fighter_id", "") or "").strip() == target_id
        ]
        if len(matches) != 1:
            return False, (
                "That fighter identity is no longer available in this proposal."
                if not matches else
                "The saved proposal contains duplicate fighter identities; no opponent was booked."
            ), None
        return self.commit_booking_proposal(
            proposal_id, matches[0], title=title, special_belt=special_belt,
            main=main, tier=tier,
        )
