"""Opt-in observation of prepared holds; never an outcome or frequency gate.

Mix ``PreparedSubmissionDiagnosticsMixin`` before a fight harness, or use
``PreparedFightAuditHarness``. Each simulate_fight call resets the observations.
Read ``prepared_submission_diagnostics()`` after the bout. Observation is active
only with experimental specialist entries enabled. No global patching is used.

Expected-use totals sum conditional action-probability * technique-ticket-share
along the observed bout paths. They are diagnostics, not an unconditional forecast
for a different mechanical policy. Missing weighted menus remain unknown (None),
not zero probability. Opponent interventions and emergency survival are separate.
"""
from copy import deepcopy

from fight_engine_audit import FightAuditHarness


SETUPS = (
    ("scarf", "scarf_hold_setup", "_valid_scarf_hold_setup", ("scarf-hold straight armbar", False)),
    ("von_flue", "von_flue_setup", "_valid_von_flue_setup", ("Von Flue choke", True)),
)


class PreparedSubmissionDiagnosticsMixin:
    def reset_prepared_submission_diagnostics(self):
        self._prepared_diagnostic_rows = []
        self._prepared_diagnostic_seen = set()
        self._prepared_diagnostic_active = None

    def simulate_fight(self, *args, **kwargs):
        self.reset_prepared_submission_diagnostics()
        return super().simulate_fight(*args, **kwargs)

    def _diagnostic_setup(self, actor, opponent, state, round_no, tick):
        if not getattr(self, "_experimental_specialist_entries", False):
            return None
        actor_key = self.fight_state_key(actor, state)
        opponent_key = self.fight_state_key(opponent, state)
        preview = dict(state, round=round_no, tick=tick)
        for kind, key, validator, ticket in SETUPS:
            setup = state.get(key)
            if not isinstance(setup, dict):
                continue
            top_fighter = actor if actor_key == setup.get("top") else opponent if opponent_key == setup.get("top") else None
            if top_fighter is None or not getattr(self, validator)(top_fighter, "submission", preview):
                continue
            identity = (kind, setup["round"], setup["created_tick"], setup["top"], setup["bottom"])
            return identity, {
                "kind": kind, "round": round_no, "created_tick": setup["created_tick"], "tick": tick,
                "top": setup["top"], "bottom": setup["bottom"], "actor": actor_key,
                "ticket": ticket, "action_probability": None, "prepared_ticket_share": None,
                "readiness": None, "expected_use_probability": None, "weight_observations": 0,
            }
        return None

    def choose_action(self, actor, opponent, state, round_no, tick):
        if not hasattr(self, "_prepared_diagnostic_rows"):
            self.reset_prepared_submission_diagnostics()
        found = self._diagnostic_setup(actor, opponent, state, round_no, tick)
        previous = self._prepared_diagnostic_active
        row = None
        if found and found[0] not in self._prepared_diagnostic_seen:
            identity, row = found
            self._prepared_diagnostic_seen.add(identity)
            self._prepared_diagnostic_rows.append(row)
        self._prepared_diagnostic_active = row
        try:
            action = super().choose_action(actor, opponent, state, round_no, tick)
            if row is not None:
                row["selected_action"] = action
                row["classification"] = (
                    "opponent_intervention" if row["actor"] != row["top"]
                    else "emergency_survival" if action == "survive" and not row["weight_observations"]
                    else "weighted" if row["weight_observations"] else "unobserved_menu"
                )
            return action
        except Exception:
            if row is not None:
                row["classification"] = "incomplete"
            raise
        finally:
            self._prepared_diagnostic_active = previous

    def _chain_action_weights(self, actor, opponent, state, weights, round_no, tick):
        adjusted = super()._chain_action_weights(actor, opponent, state, weights, round_no, tick)
        row = getattr(self, "_prepared_diagnostic_active", None)
        if row is not None and row["actor"] == row["top"]:
            # Observe the returned menu; do not call the apportioner twice.
            cleaned = {key: max(1, int(value)) for key, value in adjusted.items()}
            preview = dict(state, round=round_no, tick=tick)
            prepared = self._prepared_submission_opportunity(actor, "submission", preview)
            tickets = self.submission_technique_tickets(actor, "submission", preview)
            row.update(
                action_tickets=cleaned,
                action_probability=cleaned.get("submission", 0) / sum(cleaned.values()) if cleaned else None,
                prepared_ticket_share=tickets.count(row["ticket"]) / len(tickets) if tickets else None,
                readiness=prepared["readiness"] if prepared else None,
                weight_observations=row["weight_observations"] + 1,
            )
            row["expected_use_probability"] = (
                row["action_probability"] * row["prepared_ticket_share"]
                if row["action_probability"] is not None and row["prepared_ticket_share"] is not None else None
            )
        return adjusted

    def submission_technique(self, actor, action, state):
        row = None
        key = self.fight_state_key(actor, state)
        for candidate in reversed(getattr(self, "_prepared_diagnostic_rows", ())):
            if (candidate.get("selected_action") == action == "submission" and candidate["actor"] == key
                    and candidate["round"] == state.get("round") and candidate["tick"] == state.get("tick")
                    and "selected_technique" not in candidate):
                row = candidate
                break
        if row is not None:
            # Snapshot before the real draw consumes the setup. Pool building is
            # pure; the inherited method still performs the only real choice.
            tickets = self.submission_technique_tickets(actor, action, state)
            row["draw_prepared_tickets"] = tickets.count(row["ticket"])
            row["draw_total_tickets"] = len(tickets)
        result = super().submission_technique(actor, action, state)
        if row is not None:
            row["selected_technique"] = result["name"]
            row["prepared_selected"] = (result["name"], bool(result["choke"])) == row["ticket"]
        return result

    def prepared_submission_diagnostics(self):
        rows = deepcopy(getattr(self, "_prepared_diagnostic_rows", []))
        summary = {}
        for row in rows:
            counts = summary.setdefault(row["kind"], {
                "opportunities": 0, "weighted_menus": 0, "opponent_interventions": 0,
                "emergency_survival": 0, "unobserved_menus": 0, "incomplete": 0,
                "submission_choices": 0, "prepared_choices": 0,
                "invalid_observations": 0, "missing_draws": 0,
                "conditional_expected_submissions": 0.0, "conditional_expected_uses": 0.0,
            })
            counts["opportunities"] += 1
            classification = row.get("classification", "incomplete")
            counter = {"weighted": "weighted_menus", "opponent_intervention": "opponent_interventions",
                       "emergency_survival": "emergency_survival", "unobserved_menu": "unobserved_menus",
                       "incomplete": "incomplete"}[classification]
            counts[counter] += 1
            invalid = row["weight_observations"] > 1
            counts["invalid_observations"] += invalid
            top_submission = row["actor"] == row["top"] and row.get("selected_action") == "submission"
            counts["submission_choices"] += top_submission
            counts["missing_draws"] += top_submission and "selected_technique" not in row
            counts["prepared_choices"] += bool(row.get("prepared_selected"))
            # Multiple returned menus cannot identify the actual draw's menu
            # unambiguously. Retain rows for diagnosis, exclude ambiguous sums.
            if classification == "weighted" and not invalid:
                counts["conditional_expected_submissions"] += row["action_probability"] or 0
                counts["conditional_expected_uses"] += row["expected_use_probability"] or 0
        return {"by_setup": summary, "observations": rows}


class PreparedFightAuditHarness(PreparedSubmissionDiagnosticsMixin, FightAuditHarness):
    """Drop-in audit harness; capture diagnostics immediately after each bout."""
