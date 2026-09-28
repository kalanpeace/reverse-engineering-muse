# What we can reconstruct from the saved client code

**2026-09-27 static continuation — Astra:** [Worker dispatch and raw output](STATIC-DISPATCH-2026-09-27.md) resolves the raw flag and writer input, connects a worker-associated static call chain, and corrects an earlier parsing-helper description. It does not establish runtime body identity or recover the ranking rule.

**2026-09-27 continuation:** the complete compiled client is now saved locally
after exact-file approval. The [two-route review](TWO-ROUTES-2026-09-27.md)
resolves the formerly unknown GOT targets and adds bounded argument-map
inferences. Its runtime traces also expose a separate local-worker boundary.
The older unresolved-address descriptions below remain the historical state
of this earlier analysis; the ranking formula and full response lineage remain
unresolved.

Prepared by **Astra (gpt-6-astra)**, with bounded local reviews by **Luna (gpt-6-luna, max)**, 26 September 2026.

**We have not exhausted useful pseudocode work.** This audit translates more of the material already saved. It recovers parts of the client’s parsing and output behavior, not original Rust source or the remote scoring formula.

## Human version

We can read parts of the program that turns product text into records, attaches position numbers, collects IDs and URLs, and writes ordinary JSON. None of those inspected loops explains why one product has a particular numerical score or why a higher-scoring product sometimes appears later.

If “two upstream black boxes” means **how scores are calculated** and **how returned order is chosen**, that captures two open questions. We have not established that they are two separate programs. Muse’s choice of final recommendations is another, downstream decision. We also lack a complete trace connecting the incoming response, raw output and parsed output.

## Facts and scope

**OBSERVED:** Four additional *already held text dumps* contain 7,370 byte-column bytes and 1,642 instructions. A local LLVM decode agrees on every address, byte and instruction boundary. These are not four new remote acquisitions. The previous four separately supplied binary slices contain 2,188 bytes and 540 locally decoded instructions.

The additional check reconstructs bytes from text, builds local ELF containers, and disassembles them. It never executes the supplied code. Agreement checks consistency, not remote origin, real execution, or every semantic interpretation. See the [verification record](../evidence/program/decoded-pieces/additional-text-verification.json) and [earlier binary-slice evidence](../evidence/program/decoded-pieces/README.md).

**STATIC INFERENCE:** The pseudocode below is ours. Names such as `ordinal`, `records`, and `unknown_helper` are explanatory names, not recovered source identifiers. Snippets describe separate functions or partial paths; they must not be read as one proven end-to-end runtime trace. Error handling, allocations and cleanup are abbreviated where stated.

### 1. Product parsing and position numbers

Successful-record path in `0x4a98f0`; field extraction and malformed-input branches remain partly abstracted:

```text
ordinal = 1
for block in accepted_PRODUCT_blocks(input_bytes):
    record = extract_product_fields(block)
    record.ordinal = ordinal
    append(records, record)
    ordinal = ordinal + 1
```

The counter starts at one at `0x4a9941–0x4a9946`, is copied into a record at `0x4aa4ed–0x4aa4f5`, and increments at `0x4aa752`. Records have a 376-byte (`0x178`) stride. This explains ordinal `rank` on this path; it is not a second numerical relevance score.

Extractor calls request product ID, URL, name, brand, price, sale price, description, image URL, color, material, pattern, size, gender, category, rating, and checkout-related fields. A `citation_id` extraction call also exists; its eventual destination is not established. Requesting a field does not prove it is populated, retained, merchant-controlled, or actually inspected by Muse.

### 2. Ordinary output

Single-record writer `0x48e5c0` and vector writer `0x4bc7f0`:

```text
begin_array()
for record in supplied_record_span_in_forward_order:
    write_object(
        rank = record.ordinal,
        product_id = record.product_id,
        url = record.url,
        name = record.name,
        brand = record.brand,
        price = record.price,
        sale_price = record.sale_price,
        description = record.description,
        image_url = record.image_url,
        color = record.color,
        material = record.material,
        pattern = record.pattern,
        size = record.size,
        gender = record.gender,
        category = record.category,
        rating = record.rating,
        is_agentic_checkout_creation_enabled = record.checkout_creation,
        is_agentic_checkout_completion_enabled = record.checkout_completion
    )
end_array()
```

The actual writers propagate serialization failures; this sketch abbreviates those paths and separators. The `rank` value is read from record offset `+0x168`, not calculated from `ranking_score`. These inspected ordinary-output fields exclude `ranking_score`. The array loop advances by `0x178`; it does not visibly sort its input. How that input became ordered remains a separate question. Neither function has been established as the raw-output sink.

### 3. Numeric product-ID collection

Function `0x4a2ea0`, using integer parser `0x4bb670`:

```text
ids = []
for record in record_span_in_forward_order:
    if record.id_storage_marker == -1:
        continue
    success, value = parse_signed_decimal(record.id_bytes)
    if success:
        append(ids, value)
return ids
```

The integer routine checks decimal characters and signed-overflow conditions. This filters an auxiliary ID list. It does not demonstrate removal or reordering of product records and is not scoring code.

### 4. URL collection

Function `0x4a2cc0`:

```text
urls = []
for record in record_span_in_forward_order:
    if record.url_storage_marker == -1:
        continue
    if record.url_pointer == null:
        break
    append(urls, (record.url_pointer, record.url_length))
return urls
```

The sentinel case skips; the non-sentinel null-pointer case stops. We have not established that the latter is reachable for a valid product record. The loop collects pointer/length pairs into an auxiliary vector without visibly changing product order.

### 5. The unresolved call after collection

Partial successful path in wrapper `0x4bb230`:

```text
records = parse_products(input_prepared_by_unresolved_branches)
intervening_helper_0x4b1ba0(...)
ids = collect_numeric_ids(records)
urls = collect_urls(records)
if ids.length != 0 or urls.length != 0:
    indirect_helper_at_GOT_0xb1cd18(ids, urls, ...)
return_wrapper_result(...)
```

The actual call occurs at `0x4bb3a0`; the GOT slot is known, its target and semantics are not. This schematic does not recover its full signature. We cannot certify the auxiliary ID list’s order after that helper. The visible argument setup does not demonstrate a product-record sort. This wrapper is not established as the ordinary product-output writer, so connecting the snippets into a single pipeline would overstate the evidence.

### 6. A guard on the response-processing branch

Text-only caller excerpt around `0x411a9f`, not part of the four additional local decodes:

```text
tested_value = low16(uint32(load32(state + 0x898) - 200))
if tested_value < 100:
    optional_argument = null
    if byte_at(state + 0xa38) != 0xff:
        optional_argument = state + 0xa38
    call_wrapper(result_at(state + 0xa08), optional_argument)
else:
    clear_vector_like_result(state + 0xa08)
```

There is an earlier unresolved predicate/flag branch, omitted here. The comparison uses the low 16 bits; calling the field an HTTP status is plausible context, not established semantics. The branch does not locate score calculation or prove that raw stdout is the untouched server response.

### 7. Tag finding

The parser calls `0x4a7600` with byte spans and literal PRODUCT delimiters. Its safe high-level abstraction at these call sites is:

```text
found, offset = find_literal_tag(input_bytes, delimiter)
```

This is matching delimiters in serialized text. It is not evidence that catalog retrieval uses lexical search, BM25, vectors, or any particular search algorithm.

## Hypotheses and what remains

| Question | Where we stand | Useful next evidence |
|---|---|---|
| What computes `ranking_score`? | No recovered formula, coefficients or implementation | A supported diagnostic explaining score components, or prespecified query tests with held-out predictions; fitted weights remain surrogate weights |
| What places products in returned order? | Score-only order is falsified; some grouping patterns repeat | Same-response intermediate orders through an exposed, supported diagnostic; controlled tests that distinguish concrete grouping rules |
| Does client processing alter the observed order? | Several loops preserve their own input order; an indirect helper and full lineage remain unresolved | Further static analysis of material already held and a supported same-request trace if available |
| How does Muse select final products? | One partially traced shopping journey, including browser discoveries | Repeated recorded journeys with exact candidates, actual observed inspections, selected IDs and displayed cards |
| Which merchant changes help? | Field availability and query associations do not establish intervention effects | A specifically authorized single-field edit, confirmed ingestion, controls and repetitions |

The new ordering review confirms 130 of 173 eligible scored responses are not descending in visible score. Of those, 99 have exactly one score increase and can be split into two nonincreasing sections. **That shape does not uniquely identify concatenation.** A priority-group sort can also produce it. The counts are in [ranking-math-2026-09-27.json](../data/ranking-math-2026-09-27.json).

## Practical next step and stopping rule

The next high-value target is **the earliest observable point where the same product sequence changes**. First use remaining held artifacts to resolve caller relationships and known indirect targets where possible. Then use only an exposed, supported same-request diagnostic if available. Compare product IDs, score literals and positions before/after; do not substitute separately sampled requests.

Stop claiming a trace at the first unavailable stage. More model-written pseudocode or repeated explanation cannot fill that gap. At the time of this audit (26 September) the full-program export had not been approved; it was exported with approval on 27 September. This audit made no Muse requests.

For ordering inference, write candidate rules before collecting more data, predict held-out brand/category/count cases, and retain counterexamples. Neither task is exhausted, and neither guarantees recovery of proprietary source or exact internal weights.

## Summary

We reconstructed bounded client-side parsing and serialization behavior from previously supplied machine-code slices and text disassembly. These paths assign ordinal positions and expose product fields, including descriptions. They do not reveal the catalog scoring function or establish an end-to-end response-order trace. Nonmonotone score order constrains possible ordering rules without uniquely identifying their implementation.

## Reproduce the added decoding check

The decoder is [code/decode_saved_windows.py](../code/decode_saved_windows.py). It ran on Apple LLVM `objdump` against text dumps in the researcher's working folder, which are not published. Its output is [additional-text-verification.json](../evidence/program/decoded-pieces/additional-text-verification.json), and the four byte pieces with their disassembly are in [evidence/program/decoded-pieces/](../evidence/program/decoded-pieces/).

## New accessible evidence, 2026-09-27 UTC

The [upstream continuation](UPSTREAM-2026-09-27.md) adds behavioral constraints and a bounded interface sketch. Accessible documentation examples are readable code, but no new original catalog implementation was recovered. Resolver deduplication/order observations are separately labelled downstream and do not fill the unknown scoring function.
