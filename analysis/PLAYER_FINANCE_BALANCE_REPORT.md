# Player Finance Balance Review

## Decision summary

The player economy had opposite problems at each end of a career. At launch, the ten most expensive
curated contracts represented about **$988k** in base purses against **$275k** starting cash, so the
dominant early strategy was to bench recognizable talent and promote generated depth. In a mature
career, fixed **$12k** office costs and uncapped same-month commercial demand let extra events convert
large media deals into nearly linear cash growth.

The implemented balance package preserves the existing event model while addressing those causes:

- curated opening fighters receive 55% founder-era contracts; generated depth, market fighters,
  AI rosters, imported careers, and existing saves are unchanged;
- the office bill remains $12k at regional popularity, then rises to $73k in the representative
  mid game and $150k in the late game; and
- the first card each month retains full reach, while a second card receives a 0.7407 commercial
  demand factor. Purses and other event costs remain fully payable.

## Stage audit

The deterministic seed-90210 model uses an eight-bout Standard card, market-rate tickets,
stage-appropriate media and sponsors, and the shipped $27,500 staff payroll. Optional academies,
child promotions, signing bonuses, buyouts, injuries, and contract clauses are excluded.

| Stage | Popularity | Scaled office | First-card profit | Net after office + staff | Second-card profit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Early | 38 | $12,000 | $267,990 | $228,490 | $99,658 |
| Mid | 68 | $73,000 | $625,773 | $525,273 | $158,945 |
| Late | 88 | $150,000 | $1,762,046 | $1,584,546 | $759,040 |

These are controlled comparisons, not promises for individual saves. Actual results vary with card
composition, regional pull, production, ticket price, media eligibility, contract clauses, and
optional businesses. The late game remains strongly profitable because the $40m/$100m milestones
also require 60/100 completed events and sustained popularity, stability, and safety; the new cadence
rule prevents meeting the cash side simply by multiplying identical cards inside one month.

## KPIs and guardrails

- Primary: top-ten opening purse exposure, first-card net after fixed overhead, and second-card profit
  relative to the first.
- Drivers: company popularity, media reach, total card hype, contracted purse exposure, and event
  frequency.
- Guardrails: signed purses are never discounted at settlement; the first monthly event is untouched;
  old saves retain their contracts and base finance data; event settlement remains canonical.

## Evidence and reproducibility

Run `analysis/player_finance_balance_audit.py` from the repository root with the bundled Python
runtime. [`player_finance_balance_audit.ipynb`](player_finance_balance_audit.ipynb) is the notebook
companion. The audit copies the shipped universe database into a temporary data directory and never
touches player saves. A chart was intentionally omitted because three stage anchors are clearer as an
exact table than as an implied continuous trend.
