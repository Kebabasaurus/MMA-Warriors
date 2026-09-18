## 10. Contracts, Weigh-ins, and Shared Rules

### Contract terms

Player-negotiated contract duration is normalized to 1-60 months. Duration is secondary to fair
compensation: fighters should not accept badly under-market base pay only because the company asks
for years of control. Security has diminishing value through 48 months and no additional scoring
benefit beyond that point. Keep `normalized_contract_months` and
`contract_duration_offer_score` aligned with the negotiation UI and smoke regressions.

All contract money and percentages are domain-validated, not merely widget-validated. Purse,
signing bonus, win bonus, finish-bonus percentage, PPV points, and guaranteed fights cannot be
negative, and invalid input must fail before cash or roster state changes. An agreed purse is paid at
its full contract value; company scale cannot silently discount it on fight night. Projection,
actual payout, the finance ledger, and the event report must consume the same clause calculation.
Every official player bout, including a draw, consumes one guaranteed fight. Ordinary guarantees
remain visible until fulfilled, and an expired deal never renews for free: use explicit negotiation
or the enabled paid auto-renew workflow.

### Weight cuts

Use `perform_weigh_in` for player events, AI cards, and sandbox fights. Do not add a second shortcut
calculation. Camp length, body fit, cut skill, scale weight, title-fight rules, and the resulting
performance penalty must stay consistent across every fight path.

