"""Reviewable, retry-safe contract-renewal batches.

The existing single-fighter negotiation window remains the authoritative
negotiation UI and resolver.  This mixin adds the planning layer requested by
J3: a player explicitly selects fighters, receives a pure quote for every row,
then confirms a stable, identity-deduplicated batch.  Each row gets its own
Foundation receipt so a partial result is visible and a repeated click never
rerolls a completed or failed offer.
"""

from copy import deepcopy
import math


class ContractBatchWorkbenchMixin:
    CONTRACT_BATCH_SCHEMA_VERSION = 1

    @staticmethod
    def _default_contract_batch_state():
        return {
            "schema_version": 1,
            "sequence": 0,
            "batches": [],
        }

    def ensure_contract_batch_state(self):
        state = getattr(self, "contract_batch_workbench", None)
        if not isinstance(state, dict):
            state = self._default_contract_batch_state()
        defaults = self._default_contract_batch_state()
        for key, value in defaults.items():
            if key not in state:
                state[key] = deepcopy(value)
        try:
            state["sequence"] = max(0, int(state.get("sequence", 0) or 0))
        except (TypeError, ValueError):
            state["sequence"] = 0
        batches = []
        for batch in state.get("batches", []) if isinstance(state.get("batches"), list) else []:
            if not isinstance(batch, dict) or not str(batch.get("batch_id", "") or ""):
                continue
            row_list = batch.get("rows", []) if isinstance(batch.get("rows"), list) else []
            batch["rows"] = [dict(row) for row in row_list if isinstance(row, dict)]
            batch["results"] = [dict(row) for row in (batch.get("results", []) if isinstance(batch.get("results"), list) else []) if isinstance(row, dict)]
            batch.setdefault("status", "Draft")
            batch.setdefault("created_month", int(getattr(self, "month", 1) or 1))
            batch.setdefault("created_week", int(getattr(self, "week", 1) or 1))
            batches.append(batch)
        state["batches"] = batches[-40:]
        self.contract_batch_workbench = state
        return state

    def _contract_batch_identity(self, fighter):
        key_fn = getattr(self, "fighter_identity_key", None)
        if callable(key_fn):
            try:
                value = key_fn(fighter)
                if value:
                    return str(value)
            except Exception:
                pass
        return str(getattr(fighter, "fighter_id", "") or f"legacy-{getattr(fighter, 'name', '')}")

    def _contract_batch_resolve(self, reference):
        resolver = getattr(self, "resolve_fighter", None)
        if callable(resolver):
            try:
                fighter = resolver(reference)
                if fighter is not None:
                    return fighter
            except Exception:
                pass
        reference = str(reference or "")
        roster = list(getattr(self, "roster", []) or [])
        matches = [fighter for fighter in roster if self._contract_batch_identity(fighter) == reference]
        if len(matches) == 1:
            return matches[0]
        name_matches = [fighter for fighter in roster if str(getattr(fighter, "name", "")) == reference]
        return name_matches[0] if len(name_matches) == 1 else None

    @staticmethod
    def _contract_batch_round(value, step=500):
        try:
            value = float(value or 0)
            if not math.isfinite(value):
                value = 0.0
        except (TypeError, ValueError, OverflowError):
            value = 0.0
        try:
            step = max(1, int(step or 1))
        except (TypeError, ValueError, OverflowError):
            step = 1
        return int(round(max(0.0, value) / step) * step)

    @staticmethod
    def _contract_batch_int(value, fallback=0):
        """Project malformed retained contract facts to bounded display values."""
        if isinstance(value, bool) or value is None or value == "":
            return int(fallback)
        try:
            parsed = int(value)
        except (TypeError, ValueError, OverflowError):
            return int(fallback)
        if isinstance(value, float) and not math.isfinite(value):
            return int(fallback)
        return parsed

    @staticmethod
    def _contract_batch_float(value, fallback=0.0):
        try:
            parsed = float(value or 0)
        except (TypeError, ValueError, OverflowError):
            return float(fallback)
        return parsed if math.isfinite(parsed) else float(fallback)

    def _contract_batch_quote_row(self, fighter, *, order=0):
        """Build a deterministic renewal quote from current public contract facts."""
        identity = self._contract_batch_identity(fighter)
        name = str(getattr(fighter, "name", "Unknown") or "Unknown")
        base_purse = max(0, self._contract_batch_int(getattr(fighter, "purse", 0)))
        popularity = max(0, self._contract_batch_int(getattr(fighter, "popularity", 0)))
        momentum = self._contract_batch_float(getattr(fighter, "momentum", 0))
        champion = bool(getattr(fighter, "champion", False))
        # This mirrors the established ask curve, but deliberately omits its
        # negotiation RNG.  The quote is a planning estimate, not a promise.
        leverage = 1 + popularity / 140 + (0.35 if champion else 0) + max(0, momentum) * 0.05
        loyalty = 0.82
        ask = max(4000, self._contract_batch_round(base_purse * leverage * loyalty))
        purse = max(4000, ask)
        age = self._contract_batch_int(getattr(fighter, "age", 30), 30)
        term = 18 if age <= 32 else 14
        term = max(8, min(30, term))
        guaranteed_fights = 5
        signing_bonus = self._contract_batch_round(purse * 0.5, step=1000)
        exclusive = bool(getattr(fighter, "exclusive", True))
        upfront = purse * (2 if exclusive else 1) + signing_bonus
        exposure = purse * guaranteed_fights + signing_bonus
        clauses = []
        for label, field in (
            ("champion's clause", "champions_clause"),
            ("title-shot clause", "title_shot_clause"),
            ("main-event promise", "main_event_promise"),
            ("top-opponent promise", "top_opponent_promise"),
        ):
            if bool(getattr(fighter, field, False)):
                clauses.append(label)
        months_left = max(0, self._contract_batch_int(getattr(fighter, "contract_months", 0)))
        if getattr(fighter, "retired", False) or getattr(fighter, "retirement_pending", False):
            current_status = "Blocked"
            reasons = ["Retiring or already retired"]
        elif months_left <= 0:
            current_status = "Expired"
            reasons = ["Contract is already expired; use the normal signing/comeback route"]
        elif months_left <= 1:
            current_status = "Final month"
            reasons = []
        elif months_left <= 3:
            current_status = "Expiring soon"
            reasons = []
        else:
            current_status = "Active"
            reasons = []
        cash = self._contract_batch_int(getattr(self, "cash", 0))
        reserve_fn = getattr(self, "player_monthly_office_cost", None)
        upkeep_fn = getattr(self, "strategic_investment_upkeep", None)
        reserve = 0
        try:
            reserve = (self._contract_batch_int(reserve_fn()) if callable(reserve_fn) else 0) * 3
            reserve += (self._contract_batch_int(upkeep_fn()) if callable(upkeep_fn) else 0) * 3
        except (TypeError, ValueError, OverflowError):
            reserve = 0
        cautions = []
        if cash - upfront < reserve:
            cautions.append(f"Up-front ${upfront:,} would breach the current ${reserve:,} operating reserve")
        if months_left > 3:
            cautions.append("Renewal is optional while the current term is secure")
        company_rank, world_rank = "-", "-"
        rank_map_fn = getattr(self, "player_division_rank_map", None)
        if callable(rank_map_fn):
            try:
                rank_map = rank_map_fn() or {}
                rank_value = rank_map.get(self._contract_batch_identity(fighter))
                if rank_value is None:
                    rank_value = rank_map.get(identity)
                company_rank = "C" if champion else (f"#{rank_value}" if rank_value else "-")
            except Exception:
                company_rank = "C" if champion else "-"
        return {
            "fighter_id": identity,
            "fighter_name": name,
            "order": int(order),
            "quoted_month": int(getattr(self, "month", 1) or 1),
            "quoted_week": int(getattr(self, "week", 1) or 1),
            "quoted_status": current_status,
            "current_months": months_left,
            "quoted_terms": {
                "purse": purse,
                "months": term,
                "guaranteed_fights": guaranteed_fights,
                "signing_bonus": signing_bonus,
                "exclusive": exclusive,
                "clauses": clauses,
            },
            "required_cash": upfront,
            "guaranteed_exposure": exposure,
            "company_rank": company_rank,
            "world_rank": world_rank,
            "hard_reasons": reasons,
            "cautions": cautions,
            "status": "Blocked" if reasons else "Ready",
        }

    def _contract_batch_order_key(self, row):
        return (
            0 if str(row.get("quoted_status", "")) == "Final month" else 1,
            int(row.get("current_months", 0) or 0),
            str(row.get("fighter_name", "")).casefold(),
            str(row.get("fighter_id", "")),
        )

    def create_contract_batch(self, fighters_or_refs):
        """Create and persist one pure quote batch from explicit selections."""
        state = self.ensure_contract_batch_state()
        selected = list(fighters_or_refs or [])
        seen = set()
        rows = []
        for reference in selected:
            fighter = reference if hasattr(reference, "name") else self._contract_batch_resolve(reference)
            if fighter is None:
                continue
            identity = self._contract_batch_identity(fighter)
            if not identity or identity in seen:
                continue
            seen.add(identity)
            rows.append(self._contract_batch_quote_row(fighter, order=len(rows)))
        if not rows:
            return False, "Select at least one active roster fighter for a renewal review.", None
        state["sequence"] = int(state.get("sequence", 0) or 0) + 1
        batch_id = f"contract-batch-{state['sequence']:06d}"
        rows.sort(key=self._contract_batch_order_key)
        for index, row in enumerate(rows, 1):
            row["order"] = index
        batch = {
            "batch_id": batch_id,
            "schema_version": self.CONTRACT_BATCH_SCHEMA_VERSION,
            "created_month": int(getattr(self, "month", 1) or 1),
            "created_week": int(getattr(self, "week", 1) or 1),
            "quote_revision": 1,
            "status": "Draft",
            "rows": rows,
            "results": [],
            "total_required_cash": sum(int(row.get("required_cash", 0) or 0) for row in rows),
            "total_guaranteed_exposure": sum(int(row.get("guaranteed_exposure", 0) or 0) for row in rows),
            "partial_success_policy": "Rows are processed in the displayed order; each success or failure is sealed independently.",
        }
        state["batches"].append(batch)
        state["batches"] = state["batches"][-40:]
        return True, f"Renewal review {batch_id} prepared for {len(rows)} fighter(s).", deepcopy(batch)

    def contract_batch_snapshot(self, batch_id):
        state = self.ensure_contract_batch_state()
        batch = next((row for row in state.get("batches", []) if str(row.get("batch_id", "")) == str(batch_id)), None)
        return deepcopy(batch) if isinstance(batch, dict) else None

    def review_contract_batch(self, batch_id):
        """Re-read current identities without rewriting the saved quote."""
        batch = self.contract_batch_snapshot(batch_id)
        if not batch:
            return None
        results_by_id = {str(row.get("fighter_id", "")): row for row in batch.get("results", []) if isinstance(row, dict)}
        reviewed = []
        for row in batch.get("rows", []):
            row = deepcopy(row)
            fighter = self._contract_batch_resolve(row.get("fighter_id", ""))
            if fighter is None:
                row.update({"current_status": "Unavailable", "current_reason": "The fighter is no longer on the player roster."})
            elif getattr(fighter, "retired", False) or getattr(fighter, "retirement_pending", False):
                row.update({"current_status": "Blocked", "current_reason": "The fighter is retiring or already retired."})
            elif str(row.get("fighter_id", "")) in results_by_id:
                row.update({"current_status": "Sealed", "current_reason": "This row already has a recorded result; it will not be rerun."})
            else:
                current_months = max(0, self._contract_batch_int(getattr(fighter, "contract_months", 0)))
                row.update({"current_status": "Eligible", "current_reason": "Ready for the existing negotiation handler."})
                if current_months != int(row.get("current_months", 0) or 0):
                    row["current_reason"] = f"Current term changed to {current_months} month(s); the saved quote remains historical evidence."
            reviewed.append(row)
        batch["review_rows"] = reviewed
        batch["reviewed_month"] = int(getattr(self, "month", 1) or 1)
        batch["reviewed_week"] = int(getattr(self, "week", 1) or 1)
        return batch

    def _contract_batch_executor(self, fighter, row):
        """Use an injectable test executor or the established batch negotiator."""
        injected = getattr(self, "contract_batch_executor", None)
        if callable(injected):
            return injected(fighter, deepcopy(row))
        negotiator = getattr(self, "auto_negotiate_player_contracts", None)
        if not callable(negotiator):
            return {"renewed": 0, "failed": 1, "results": [{"name": getattr(fighter, "name", "Unknown"), "status": "failed", "reason": "No renewal handler is available."}]}
        return negotiator([fighter])

    def _contract_batch_row_validation(self, fighter):
        if fighter is None:
            return False, "The fighter is no longer on the player roster."
        if fighter not in (getattr(self, "roster", []) or []):
            return False, "The fighter is no longer on the player roster."
        if getattr(fighter, "retired", False) or getattr(fighter, "retirement_pending", False):
            return False, "The fighter is retiring or already retired."
        return True, ""

    def commit_contract_batch(self, batch_id):
        """Commit each reviewed row once, preserving partial outcomes."""
        state = self.ensure_contract_batch_state()
        batch = next((row for row in state.get("batches", []) if str(row.get("batch_id", "")) == str(batch_id)), None)
        if not isinstance(batch, dict):
            return False, "That renewal batch no longer exists.", None
        if batch.get("status") in ("Completed", "Partial", "Blocked") and len(batch.get("results", []) or []) >= len(batch.get("rows", []) or []):
            return True, "This renewal batch is already sealed; no offers were rerun.", deepcopy(batch)
        reviewed = self.review_contract_batch(batch_id) or {}
        rows = reviewed.get("review_rows", [])
        existing = {str(row.get("fighter_id", "")) for row in batch.get("results", []) if isinstance(row, dict)}
        for row in rows:
            identity = str(row.get("fighter_id", "") or "")
            if not identity or identity in existing:
                continue
            fighter = self._contract_batch_resolve(identity)
            valid, reason = self._contract_batch_row_validation(fighter)
            quote = {"batch_id": batch_id, "row": deepcopy(row), "partial_success_policy": batch.get("partial_success_policy", "")}
            operation_key = f"contract-batch:{batch_id}:row:{identity}"
            if not valid:
                receipt = self.foundation_record_work(operation_key, domain="contracts", action="renewal_batch_row", target_id=identity, status="rejected", error=reason, quote=quote) if hasattr(self, "foundation_record_work") else {"status": "rejected", "error": reason}
            else:
                def validate(fighter=fighter):
                    return self._contract_batch_row_validation(fighter)

                def apply(fighter=fighter, row=row):
                    return self._contract_batch_executor(fighter, row)

                if hasattr(self, "foundation_commit"):
                    receipt = self.foundation_commit(
                        operation_key, domain="contracts", action="renewal_batch_row", target_id=identity,
                        quote=quote, validate=validate, apply=apply,
                    )
                else:
                    try:
                        receipt = {"status": "committed", "result": apply()}
                    except Exception as exc:
                        receipt = {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}
            result_payload = receipt.get("result") if isinstance(receipt, dict) and isinstance(receipt.get("result"), dict) else {}
            result_rows = result_payload.get("results", []) if isinstance(result_payload.get("results", []), list) else []
            result_row = result_rows[0] if result_rows and isinstance(result_rows[0], dict) else {}
            row_status = str(result_row.get("status", "") or "")
            if not row_status:
                row_status = "renewed" if int(result_payload.get("renewed", 0) or 0) else "failed"
            sealed_status = "Renewed" if row_status == "renewed" else "Failed"
            receipt_error = str(receipt.get("error", "") or "") if isinstance(receipt, dict) else ""
            row_reason = str(result_row.get("reason", "") or "") or receipt_error
            # Carry the domain-reported cash through the durable row result so
            # callers such as Staff Full Auto can reconcile the actual spend
            # against their preflight ceiling without guessing from a quote.
            row_cost = self._contract_batch_int(
                result_row.get("cost", result_payload.get("cost", 0)), 0,
            )
            row_cost = max(0, row_cost)
            batch.setdefault("results", []).append({
                "fighter_id": identity,
                "fighter_name": row.get("fighter_name", "Unknown"),
                "status": sealed_status,
                "reason": row_reason,
                "cost": row_cost,
                "receipt_id": str(receipt.get("operation_id", "") if isinstance(receipt, dict) else ""),
                "operation_key": operation_key,
                "detail": deepcopy(result_row or result_payload),
            })
            existing.add(identity)
        total = len(batch.get("rows", []) or [])
        renewed = sum(1 for row in batch.get("results", []) if row.get("status") == "Renewed")
        failed = len(batch.get("results", [])) - renewed
        if total and len(batch.get("results", [])) >= total:
            batch["status"] = "Completed" if failed == 0 else ("Partial" if renewed else "Blocked")
        else:
            batch["status"] = "Partial" if renewed else "Blocked"
        batch["renewed"] = renewed
        batch["failed"] = failed
        batch["sealed_month"] = int(getattr(self, "month", 1) or 1)
        batch["sealed_week"] = int(getattr(self, "week", 1) or 1)
        state["batches"] = [row if row.get("batch_id") != batch_id else batch for row in state.get("batches", [])]
        return True, f"Batch sealed: {renewed} renewed, {failed} not renewed. Each row is recorded separately.", deepcopy(batch)
