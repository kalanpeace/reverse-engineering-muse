# Reviewed facts: taste and shopping behavior

Astra (gpt-6-astra), 27 September 2026. “Observed” below means present in preserved supplied artifacts or captured UI. It does not independently authenticate remote execution.

| Evidence class | Finding | Basis / scope |
|---|---|---|
| OBSERVED | 72 successful direct calls: original 60 plus separate 12-call amendment | Exact schedules, flags, receipts, stdout/stderr hashes and ZIP manifests checked |
| OBSERVED | 3,827 scored PRODUCT occurrences; 1,125 distinct IDs | Local raw parse; the unit is returned record occurrences, not recommendations |
| EXPERIMENTAL ASSOCIATION | 90.76% mean same-query overlap vs 3.05% mean changed-query/baseline overlap | Original 60 calls: 60 within pairs and 54 baseline contrasts; one shared context |
| EXPERIMENTAL ASSOCIATION | 194 of 203 shared-ID score comparisons changed | Conditional on appearing in both outputs; no missing score imputation |
| OBSERVED | 33 of 69 nonempty responses contain an adjacent score increase | Three empty responses excluded; global descending score is insufficient |
| OBSERVED | Literal lesser-known designer query returned 0/0/0 PRODUCT records while each debug list reported 100 IDs | Payload layers differ; not proof of no candidates or missing brands |
| OBSERVED | Ordinary designer case reworded its search; 2 then 64 records, three JNBY cards | Different queries and normal workflow; brand obscurity unmeasured |
| OBSERVED | Six ordinary cases, seven catalog calls, 375 record occurrences, 15 displayed cards | Illustrative cases, not representative shopper frequencies; some displayed choices had constraint caveats |
| OBSERVED | Pre-owned product appeared despite new-only requirement; logo-caveated product appeared despite no-visible-logos request | Own rationale and UI/crosswalk; not an independent visual logo determination |
| OBSERVED / ATTRIBUTED | T24 manual record describes broad web search before catalog; later public source check corroborates two dated articles | Native search/page traces absent; no Google-provider or SEO-effect inference |
| OBSERVED | T24 third product check blocked by human verification and omitted; catalog/page price differed for a shown Baltic Born dress | Saved handoff and UI; no checkout test |
| UNOBSERVED | Exact ranking formula, causal merchant-edit effects, pretraining/RL contribution, broad trend popularity | Not measured by this design |

See [quantitative readout](ANALYSIS-READOUT.md), [case audit](CASES-REVIEW.md), [trend-source review](TREND-SOURCE-REVIEW.md), and [math definitions](TECHNICAL-APPENDIX.md). The reader-facing account is Part 4 of the report.
