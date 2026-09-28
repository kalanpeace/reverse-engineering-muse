# Upstream query combination: second evidence pass

Author: Astra (gpt-6-astra). Independent local analysis and design review: Luna (gpt-6-luna, max). Collection used the existing Muse main chat on 2026-09-27 UTC. Only Astra contacted Muse.

**The hidden scoring formula is still unknown. We did establish that combining two query arguments is not equivalent to concatenating their text or merely sorting their two visible result lists.** Those are scoped upstream observations, before recommendation selection; no resolver experiment is used to support them.

## Facts

The prespecified experiment made 21 calls: seven conditions, three interleaved blocks, one fixed CLI conversation ID, no user ID, requested count 50, retries zero. The downloaded collector matches our locally authored script byte-for-byte, and its 21 recorded argument arrays match the prespecified schedule. All execution receipts report exit zero with empty stderr; all 86 manifest rows and both archive integrity checks pass. These establish internal consistency of the supplied artifacts, not independently authenticated remote execution.

The calls contain **1,104 returned product-record occurrences**, not unique products or recommendations. A is `stainless steel frying pan`; B is `stainless steel skillet`. JOIN is one string containing both phrases. AB, BA, AAB and ABB use separate repeated `--query` arguments.

| Condition | Records in each of three calls | Common IDs across repeats | IDs with stable scores across repeats | Distinct returned-ID sequences |
|---|---:|---:|---:|---:|
| A | 43 | 43 | 43 | 1 |
| B | 53 | 53 | 53 | 1 |
| AB | 56 | 56 | 56 | 1 |
| BA | 56 | 56 | 47 | 3 |
| AAB | 56 | 55 | 50 | 2 |
| ABB | 56 | 55 | 49 | 2 |
| JOIN | 48 | 48 | 48 | 1 |

### The combined list reaches beyond the two visible solo lists

In every block, A and B's solo returned-ID sets are disjoint. AB contains 27 IDs from A, 26 from B, and three IDs absent from both solo outputs. **All 53 matched solo-to-AB score values are unchanged in every block.**

The three additional AB IDs are present in the solo query-debug metadata:

| Extra AB product ID | Solo debug list containing it |
|---|---|
| 26061255096884715 | B |
| 27703952109192589 | A |
| 7753718698060520 | B |

Each A/B metadata entry has 100 distinct IDs. The same ordered A list occurs in all 18 A entries across solo, combined and duplicate arms; B likewise has one ordered list across 18 entries. A and B's debug lists share 14 IDs. The query-entry sequence matches the recorded query arguments in all 21 calls. These are observations about metadata whose stage meaning remains undocumented. Debug membership does not supply a missing numeric score, establish eligibility or prove model inspection.

The simple expression `sort(union(visible_solo_A, visible_solo_B))` cannot reproduce these AB outputs: three returned IDs are missing from its inputs. This is a counterexample to that observable-list model, not proof of a particular hidden merge pipeline.

### Separate queries differ from one joined string

AB and JOIN share just five returned IDs in each block, and all five shared score values differ. AB has 51 IDs absent from JOIN; JOIN has 43 absent from AB. Both arms repeat exactly three times. For this phrase pair, a two-query request does not behave like one concatenated query. This says nothing universal about every synonym pair or the underlying text representation.

### Query order and duplication do not yield a clean weighting rule

AB and BA return the same 56-ID membership in all three blocks, but their ID order matches in only one block. Three shared scores differ in block one, none in block two, and seven in block three. BA itself varies across repeats. This prevents assigning all observed differences to query order.

AAB and ABB both reproduce AB's full IDs, order and scores in blocks one and three. In block two, each replaces one ID; AAB changes five shared scores and ABB changes six. These data do not establish a repeatable duplicate-query boost or universal duplicate invariance.

The literal max/mean/sum and duplicate-weighted-mean checks have **zero eligible products** because the solo A/B results have no shared IDs. The prespecified geometric surrogate also fails its minimum-overlap gate, so it was not fitted. No weights were estimated. The earlier one-item formula counterexample remains a separate experiment with a different B query; it is not pooled into this one.

Reproduce the facts with [the analyzer](../code/analyze_query_multiplicity.py), [derived records](../data/query-multiplicity-runs.jsonl), and [audit](../data/query-multiplicity-audit.json). The analyzer checks recorded arguments against the prespecified schedule and separately retains IDs, scores, positions and debug metadata.

## Hypotheses

**HYPOTHESIS:** combined-query processing may have access to candidates beyond the visible solo outputs and may preserve a query-specific score for some products. The stable debug lists and 53 unchanged scores are consistent with this. They do not reveal when selection, merging, deduplication, rescoring or truncation occurs, or whether any such operation is in the client or remote service.

**UNOBSERVED:** the score equation, feature definitions and contributions, candidate-stage semantics, normalization, ranker version, tie rules, intermediate scores, and the same-request path from response receipt to CLI stdout. No new original implementation source or binary slice was acquired.

## Direct contract search

Muse reported three additional ordinary skill-description searches: `catalog search ranking_score`; `MetaCatalogSearchToolData query_debug_info`; and `catalog score explanation ranker version`. Its downloaded, explicitly manual transcription reports eight unrelated hits, zero hits, and two unrelated hits, respectively. It read no new referenced document and invoked no explanation method. Four manifest rows, the displayed archive hash and ZIP CRC match locally.

This expands the recorded discovery attempts beyond the earlier shopping-only namespace and skill-doc search, but **it is not a native global tool inventory or proof that no scoring contract exists**. Muse's transcription labels the skill search as BM25; that label concerns skill discovery, not catalog ranking. It provides no evidence that the product scorer uses BM25.

At this point the complete executable request was still subject to the approval boundary. (Later on 27 September the full program was exported with explicit approval; see [TWO-ROUTES-2026-09-27.md](TWO-ROUTES-2026-09-27.md).) We neither resent it nor sought new slices as an indirect substitute. Even that executable, if later available, would be client evidence rather than guaranteed access to remote ranking source.

## Conclusion and remaining boundary

Through an AI agent, we collected repeated catalog outputs and compared returned records with nested query metadata. Separate-query and joined-text inputs produced distinct candidate sets and scores. For one pair, combined outputs included three IDs absent from both visible solo outputs while preserving all 53 shared scores. Query-order and multiplicity comparisons also exhibited within-condition variation. The observations constrain simple interface-level models but do not identify the production scoring function or the component that creates returned order.

The bounded investigation has delivered its reproducible experiments, artifact search and precise evidence boundary. **The stronger ambition—recovering the upstream formula—remains unmet.** We have not exhausted every black-box method. A decisive next advance would be a provenance-bearing score explanation or feature contract, or a same-response trace locating the score/order transformation. Another fitted equation over these incomplete observations would not supply that proof.

For a merchant, the practical finding is that inclusion, visible score, returned position and final recommendation are different outcomes. Neither these CLI interventions nor the earlier tests establish that editing a merchant description or title improves ranking. That needs a separately authorized field-change experiment with verified ingestion.

The downloaded ZIP (collectors and raw outputs, request handles blanked) is [evidence/combined-searches/](../evidence/combined-searches/). Prompts are in the chat transcript; screenshots are not published. No supplied script or binary was executed locally, no merchant listing was changed, and no new Muse conversation was created.
