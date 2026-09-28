# Checked facts register (27 September 2026)

Astra (gpt-6-astra), 27 September 2026. This register consolidates an earlier facts list (not published), later studies and static-code corrections.

Scope: written on 27 September, before the raw-tags run and the Unicorn debug-list analysis. For those results (seller_quality values, flywheel_identifiers, Unicorn candidate lists) see the report (Part 1, Step 6 and Part 5), [raw-tags-analysis.json](../data/raw-tags-analysis.json), [unicorn-debug-analysis.json](../data/unicorn-debug-analysis.json) and [stage-analysis.json](../data/stage-analysis.json). “Checked” means the cited evidence or calculation was reviewed at the stated level; it does not certify Muse's remote execution or production implementation.

**Evidence classes:** OBSERVED = present in saved output/UI; STATIC INFERENCE = interpretation of supplied compiled code; EXPERIMENTAL ASSOCIATION = measured comparison without a merchant intervention; HYPOTHESIS = proposed explanation; UNOBSERVED = not established. Public documentation and personal recollection are explicitly attributed rather than treated as experimental findings.

## Opening facts

| ID  | Class and conclusion | Checked basis and boundary |
|---|---|---|
| P01 | DOCUMENTED: Muse is Meta's personal agent with a dedicated Linux cloud computer, browser, files, tools and subagents. | [Meta architecture](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse), published September 8, checked September 27, 2026. Platform description, not a shopping-test finding. |
| P02 | DOCUMENTED: runtime-container root differs from host root; built-in connectors use separate workers. | Same Meta source. This explains why reading a runtime file does not establish a sandbox escape or access to the remote catalog implementation. |
| P03 | OBSERVED: products returned by a catalog call, products selected, and products displayed are distinct outputs. | [Merchant study](MERCHANT-BENCHMARK-2026-09-27.md), [case audit](CASES-REVIEW.md). Browser work can add information/products and may precede catalog formulation. This is not one mandatory call sequence. |
| P04 | OBSERVED: returned order is not universally descending `ranking_score`. | [Reproducible math](RANKING-MATH-2026-09-27.md), [calculated records](../data/ranking-math-2026-09-27.json); named counterexample B01 below. |
| P05 | UNOBSERVED: the exact score formula and causal effects of merchant edits remain unknown. | No verified formula artifact or merchant listing intervention. Static client interpretation does not fill that gap. |
| P06 | DOCUMENTED: Shopify offers title, description and category source mappings; it documents Meta discovery through Shopify Catalog. | [Mapping](https://help.shopify.com/en/manual/shopify-catalog/mapping), [Meta channel](https://help.shopify.com/en/manual/online-sales-channels/agentic-storefronts/meta), checked September 27. A merchant route, not proof of lineage for each captured record or ranking lift. |

## Study populations: never silently add these together

| ID | Population | Verified total and unit | Source |
|---|---|---|---|
| D01 | Historical corpus | 185 subprocess invocations: 182 catalog calls and 3 metadata commands; 6,314 returned record occurrences. 179 raw-output calls and 3 parsed-output calls. | [Records](../data/catalog-runs.jsonl), [checkpoints](../data/checkpoints.json). Reconstructed from preserved originals by the local verifier. |
| D02 | Historical four-cohort subset | 163 invocations: 160 catalog plus 3 metadata, all reporting exit 0. | Same records, cohorts `brand63`, `followup60`, `boundary36`, `modes4`. This is the scope of an earlier facts list, not the latest total study. Exit status does not establish sidecar creation. |
| D03 | First upstream continuation | 27 scored catalog calls; 1,200 record occurrences; a separate hints call is not a scored run. | [Upstream report](UPSTREAM-2026-09-27.md), [runs](../data/upstream-runs.jsonl). |
| D04 | Query-combination continuation | 21 calls; 1,104 record occurrences. | [Second report](UPSTREAM-PHASE2-2026-09-27.md), [runs](../data/query-multiplicity-runs.jsonl). |
| D05 | Broad merchant panel | 100 direct catalog calls across 20 categories and 5 intents; 4,088 record occurrences; 3,827 distinct IDs. | [Panel analysis](MERCHANT-BENCHMARK-2026-09-27.md), [sanitized summary and receipts](../data/merchant-benchmark-2026-09-27.json). These are not 100 ordinary shopper conversations or 5,000 recommendations. |
| D06 | Separate ordinary merchant cases | 5 cases; 270 catalog records and 14 captured cards. Counts per case: 48/3, 40/3, 61/3, 63/3, 58/2. | Same panel report. Not the downstream funnel for D05. |
| D07 | Direct taste/style study | 72 calls = 60 original + 12 amendment; 3,827 scored occurrences; 1,125 distinct IDs. | [Taste records](../data/taste-study-runs.json), [summary](../data/taste-study-summary.json). The number 3,827 here counts occurrences; D05's 3,827 counts IDs. |
| D08 | Separate ordinary taste cases | 6 cases; 7 catalog calls; 375 record occurrences; 15 captured cards. | [Case audit](CASES-REVIEW.md), [crosswalk](../data/CASE-CROSSWALK.csv). Do not join their ordinals to scores from separately sampled direct calls. |

## Scores, order and interface behavior

| ID | Class and finding | Evidence and permitted conclusion |
|---|---|---|
| B01 | OBSERVED: Hestan's Brushed Clad Stainless Steel Skillets appears at position 40 / 0.558594; Quince's 5 Ply Stainless Steel Nonstick Cookware: 2 Piece Frying Pan Set: 8\" & 10\" appears at 41 / 0.773438. | D01 run `neutral_baseline/ncap-n50-run2`, 43 records. Exact arithmetic in [ranking math](RANKING-MATH-2026-09-27.md). Quince would be 20th under a local score-only sort; this is not an observed recommendation. |
| B02 | OBSERVED: 130 of 173 historical scored responses containing at least 3 records have an adjacent score increase. | 161 increases across 6,022 adjacent pairs. Of those 130 lists, 99 have one increase and 31 have two. [Math](RANKING-MATH-2026-09-27.md). This is an ordering property, not a ranking error rate. |
| B03 | OBSERVED: historical pairwise discordance is 14,202 / (131,973 − 3,836) ≈ 11.08%. | Denominator excludes tied pairs. Long lists and repeated records contribute dependent pairs; no shopper probability or significance claim. Same math source. |
| B04 | OBSERVED: all 18 strong-brand C2/C5 outputs in the three-brand replication have a contiguous matching-domain prefix and score increase at its boundary; 12/18 also violate descending order within a group. | All-Clad, Hydro Flask, Levoit; three repeats per condition. [Baseline data](../data/catalog-runs.jsonl). “Own-domain first, then score” is insufficient as a universal rule. Host match is an operational label, not verified legal ownership. |
| B05 | OBSERVED: domain flags do not always exclude other domains. | Hydro Flask C4: 27 matching-domain + 13 other; Levoit C4: 50 + 1 in each repeat. D01. |
| B06 | EXPERIMENTAL ASSOCIATION: requested count changes membership and order and is not a reliable output cap. | [Count tables and math](RANKING-MATH-2026-09-27.md). Misen `n10`: 21/21/22, `n11`: 5/5/5; Levoit behaves differently. Do not infer a universal threshold. |
| B07 | OBSERVED: 452 pair/argument-group combinations tied in at least two of 84 calls show zero relative-order flips among tied observations. | [Tie audit](../data/tie-audit.json). Dependent pairs, not 452 independent trials; no identified hidden tie-breaker. |
| B08 | EXPERIMENTAL ASSOCIATION: Hydro Flask's Palmer Green bottle moves 15→6 while score decreases 0.753906→0.750000 when a brand option is added, in all three repeats. | D03; [ranking math](RANKING-MATH-2026-09-27.md). Returned set changes 40→47; this is not reordering a fixed pool or a merchant edit. |
| B09 | EXPERIMENTAL ASSOCIATION: green and soft-brand options change membership while the 35 and 38 consistently matched IDs respectively retain scores and relative order. | D03. Missing products have unobserved scores, not zero scores. The named Palmer Green item is absent in both preference arms; do not infer its indexed color. |
| B10 | OBSERVED: a stable product has solo-query scores 0.781250 / 0.773438 and combined score 0.785156. | D03. Rejects literal max, mean, sum and convex averaging of those visible inputs for that case. It does not recover internal fusion rules. |
| B11 | OBSERVED: the separate combination study has disjoint solo return sets; combined AB includes 27 A IDs, 26 B IDs and 3 absent from either solo return; all 53 matched scores unchanged. | D04, all three blocks. Extra IDs occur in debug metadata with unknown stage semantics. AB vs joined-string query: 5 shared IDs / 99 union; no solo overlap eligible for the planned coefficient test. |
| B12 | OBSERVED: in D05, 94/100 calls are nonempty, 41 exceed requested 50; range 0–67, median 47. | Panel summary. 41 adjacent increases / 3,994 comparable pairs across 41 calls. Do not treat historical and later rates as a time trend or build comparison. |
| B13 | OBSERVED: 4,056/4,088 descriptions, 2,645 brands, 4,070 names and 1,854 categories are nonempty in D05. | Top-level fields in panel analysis. Presence, source ownership, ingestion, model exposure, actual inspection and selection effect are different questions. |
| B14 | OBSERVED: D05's 20 budget-text calls return 100 records; its 20 broad calls return 1,047. | Wording, task content and sequential collection time differ; budgets were literal text, not structured flags. Descriptive contrast, not isolated causality. |

## Client interpretation and the upstream boundary

| ID | Class and finding | Evidence and boundary |
|---|---|---|
| C01 | OBSERVED / STATIC INFERENCE: three ordinary parsed outputs have 107 records with descriptions and ordinal `rank`, without numeric `ranking_score`; bounded code interpretation agrees. | D01; [client pseudocode](CLIENT-PSEUDOCODE.md). Available text does not prove every description was read. |
| C02 | OBSERVED: seven historical `--out` attempts produced no requested parsed sidecar according to the saved receipts. | D02. No same-invocation raw/parsed comparison from those attempts. Later successful files do not retroactively repair them. |
| C03 | STATIC INFERENCE: four earlier binary slices comprise 2,188 bytes / 540 instructions; supplied disassembly agrees locally. | [Code evidence](../evidence/program/decoded-pieces/README.md). Four additional held text excerpts decode 7,370 byte-column bytes / 1,642 boundaries; do not sum as disjoint newly acquired source. |
| C04 | STATIC INFERENCE: supplied client code supports ordinal assignment, field extraction, ordinary formatting, auxiliary ID/URL projection and a retained-string raw writer. | [Pseudocode](CLIENT-PSEUDOCODE.md), [static dispatch](STATIC-DISPATCH-2026-09-27.md). Original Rust source, full path identity and the ranker's implementation remain unavailable. |
| C05 | STATIC INFERENCE: a worker-associated call chain and `raw` flag branch are located; `raw` writes a retained string rather than the parsed product vector. | Static dispatch addresses and source windows. The string may already be processed; this is not proof that CLI `--raw` equals the untouched HTTP body. Earlier whitespace-helper interpretation was corrected to structured parsing. |
| C06 | OBSERVED: bounded runtime traces show a local worker socket and file-descriptor transfer, without the upstream product body. | [Two-route review](TWO-ROUTES-2026-09-27.md), [runtime audit](../data/runtime-trace-audit.json). Not a trace of the later shopping cases or access to worker internals. |
| C07 | OBSERVED: the locally held binary and later reported executable have different hashes/sizes. | Held: 11,684,112 bytes, SHA-256 `fe3bc08c928c9177eb2e685dc3db4c15bdc972ffe782b3a50282d88499388753`. Later receipts: `cf7642f7…` (11,684,128 bytes, store panel), `e40c0a54…` (fashion study), `eb99783b…` (raw-tags run, 27 September, recorded after this register). Also reported: `db8bcb0c…` (COMMANDS.md in the ordering-evidence archive, 26 September) and `4b9c5185…` (chat only, 27 September). Do not assert analyzed code ran in a later request. |
| C08 | UNOBSERVED: score generation and the first operation determining catalog order have not been located in an authenticated live path. | [Capability boundary](CAPABILITY-BOUNDARY-2026-09-27.md). No server source code or exact formula was obtained. Compilation is not evidence of encryption. |

## Selection, taste and browser use

| ID | Class and finding | Evidence and boundary |
|---|---|---|
| T01 | OBSERVED: the earlier mattress journey has 55 catalog IDs, 6 browser IDs, 8 staged products and 5 initially visible cards. | Mattress task in the chat transcript, 26 September; the local files are not published. Manual selection notes; keep separate from D06/D08. Use as archival support, not the main public example. |
| T02 | OBSERVED: D06's selected browser records match pan catalog pages at positions 30, 2 and 10; a displayed chair corresponds to position 44. | [Case audit](CASES-REVIEW.md). Joins by normalized host/product-page path, not exact variant or catalog-ID selection. No same-run raw scores. |
| T03 | OBSERVED: five fixed-source resolver probes follow the first occurrence of each selected ID, removing repeats. | [Resolver audit](../data/resolver-audit.json), [upstream report](UPSTREAM-2026-09-27.md). A downstream behavior, not evidence of upstream ranking weights. |
| T04 | EXPERIMENTAL ASSOCIATION: original taste calls have mean same-query Jaccard 90.76%, versus 3.05% for changed-query/baseline contrasts; 194/203 shared-ID score comparisons change. | D07 original 60 calls; 60 within-query pairs and 54 baseline contrasts. [Definitions](TECHNICAL-APPENDIX.md). Related observations, one context; no significance or general shopper-frequency claim. |
| T05 | OBSERVED: 33/69 nonempty direct taste responses have score increases; 3 empty excluded. | D07. Same distinction between visible score and order. |
| T06 | OBSERVED: literal lesser-known-designer query returns 0/0/0 product blocks despite debug lists of 100 IDs; separate ordinary workflow rewrites its query, returns 2 then 64 records and displays 3 JNBY cards. | [Taste facts](taste-style-2026-09-27-FACTS.md), [case audit](CASES-REVIEW.md). Debug count is not returned, inspected or recommended count; no measured JNBY popularity/obscurity. |
| T07 | OBSERVED: a pre-owned Clover Canyon product is selected/displayed despite a new-only constraint; a Courrèges product has a disclosed logo caveat despite the no-visible-logo request. | D08 T20/T19. First is a documented constraint failure; second is a handoff/prose caveat, not independent visual proof of a visible logo. |
| T08 | OBSERVED / ATTRIBUTED: T24 manual records describe source search before catalog; two dated fashion articles were later checked independently. | [Source review](TREND-SOURCE-REVIEW.md). Native search trace absent; one author attribution differed. Two articles do not measure broad shopper discussion or trend prevalence. |
| T09 | OBSERVED: catalog/page prices, prose mentions and actual card order can differ; an unverified Lulus item was omitted after a page challenge. | [Case crosswalk](../data/CASE-CROSSWALK.csv). No checkout test; do not equate a selection payload with rendered UI. |
| T10 | UNOBSERVED: Google-provider use, SEO effects, pretraining/RL contributions, and a universal catalog-first or memory-only workflow. | Browser/source observations prevent a “never searches the web” conclusion. No ablation identifies the model's knowledge source. |

## Not established (hypotheses only)

Lexical/BM25, embeddings, hybrid retrieval, hidden priority groups and query-expansion mechanisms are hypotheses. No fitted production coefficients, ad-engagement factor, universal 0–1 bound, calibrated probability, universal 50/100 candidate count or “only titles matter” is established. Multiple analytical functions do not prove multiple services or numerical scoring systems.

Kalan's internal-tester prompting and phone reproduction are personal methodological recollections unless tied to exact paired captures.  Claude and DeepSeek reviews are contributions, not new independent empirical evidence. Their earlier claims must yield to checked raw-derived results and later corrections.

The absence of authenticated upstream implementation is an evidence boundary. It is not a proof that every possible black-box method is exhausted, and it does not make unsupported code explanations factual.
