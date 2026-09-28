# What the numbers mean

Astra (gpt-6-astra), 27 September 2026. Descriptive analysis of supplied artifacts; no internal ranking weights estimated.

## The observable objects

For a requested query q on repeat r, let C(q,r) be the ordered PRODUCT records printed by the CLI, s(i,q,r) the printed `ranking_score`, and p(i,q,r) the record's one-based position. These are separate observations. The ordinary tool's `rank` is an ordinal; the model's selected order and the UI's order are later objects. A debug list is another surface whose semantics require evidence.

An abstract decomposition is useful:

$$
q=Q(x,c),\quad C=F(q,\theta,z),\quad A=G(C,W,c),\quad D=H(A).
$$

Here x is the shopper request, c the available context, W browser information, and z unobserved service state. Q is query formulation, F catalog retrieval/processing, G selection, and H resolution/display. This notation names unknown functions; it is not recovered source code or proof of a particular architecture. The raw CLI boundary may include client transformations.

## Membership and repetition

$$
J(C_a,C_b)=\frac{|\operatorname{IDs}(C_a)\cap\operatorname{IDs}(C_b)|}
{|\operatorname{IDs}(C_a)\cup\operatorname{IDs}(C_b)|}.
$$

We compare all three repeat pairs per original condition: 20 × 3 = 60 comparisons. We compare each of 18 non-baseline original conditions to its declared baseline in the same repeat: 18 × 3 = 54 comparisons. Means are 0.907626 and 0.030516 respectively. These are unweighted means across comparisons, not pooled record ratios. They share observations and are not independent trials. Both sets empty means undefined Jaccard. Separately, the extension's T21 has three empty sets; these are not assigned zero similarity and do not enter either original-phase denominator.

**Conclusion:** within this sample, query wording distinguishes returned sets much more than an immediate repeat of that wording. This is input sensitivity, not a measured aesthetic-quality improvement.

## Scores, positions and missing products

$$
\Delta s_i=s(i,q_b,r)-s(i,q_a,r),\qquad i\in C(q_a,r)\cap C(q_b,r).
$$

The original baseline contrasts contain 203 shared-ID comparisons; 194 have nonzero printed score differences. Products absent from either list are excluded, not assigned score zero. This conditions the result on survival in both lists and cannot explain why other products vanished. Scores may be query-normalized or otherwise noncomparable; differences describe printed numbers, not units of utility.

The 72 direct calls contain 3,827 scored record occurrences and 1,125 distinct product IDs. Their score range is 0.451172–0.824219. This verifies an observed range inside [0,1], not a universal bound, probability or confidence estimate.

Define a visible adjacent score rise as s(i+1) > s(i). It occurs in 33 of 69 nonempty responses; three empty responses are untestable. Thus global descending score is not a universal explanation of the returned record order in this sample. A rise does not identify where or why ordering occurred. Grouping, filtering, merged lists or another signal remain possible; they are not established causes.

## Merchant visibility denominators

A useful future benchmark reports separate quantities:

$$
\widehat{I}_b=\frac{\#\text{successful queries returning brand }b}
{\#\text{successful queries}},\qquad
\widehat{D}_b=\frac{\#\text{cases displaying brand }b}
{\#\text{completed shopping cases}}.
$$

Report failures and empty successes separately. Brand matching needs product IDs, manufacturer labels and verified domains; retailer host is not the manufacturer. Browser discovery may add a product outside C, so displayed inclusion is not always conditional on catalog inclusion. “Not selected” is only defensible where selection evidence exists; unobserved inspection remains unknown.

Three repeats in one research conversation do not estimate a population probability or independent-consumer recall. Six different ordinary cases are examples, not replicates of one request. Counts of returned records, unique IDs, variants, displayed cards and brands must remain separate.

## What would establish a useful merchant intervention?

Prespecify a real brand's customer intents and exact eligible variants. Obtain authorization for one concrete listing-field edit. Capture an unchanged control, verify the field's actual ingestion/indexing, then repeat the same queries before and after across time. Check price, availability, traffic/source changes and other simultaneous edits. A difference-in-differences estimate may describe an association; causal interpretation still needs credible parallel trends and stable measurement. A randomized intervention with sufficient independent units would be stronger.

Changing a shopper query is not changing a merchant description. Accurate product text, variant details, prices and working pages are sensible test targets, but this study does not quantify their ranking lift. A surrogate model fitted to the outputs would explain this dataset; its coefficients would not become Meta's weights.
