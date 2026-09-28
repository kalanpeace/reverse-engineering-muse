# Static worker dispatch and raw-output path

Author: Astra (gpt-6-astra). 2026-09-27 UTC. Local inspection only; no Muse contact, subagent delegation or downloaded code execution.

## Human version

The complete executable contains both ordinary CLI and worker execution paths. A static call chain connects a worker-labelled routine to the catalog response-processing routine. We also identified the raw flag and followed its output branch: it writes the retained response text, adding a newline if needed, instead of serializing the parsed product vector. This closes specific gaps in the earlier static review. It does not identify where the response's scores or product order originated, nor prove this path ran for the saved requests.

## Facts and static inferences

All findings refer to the full ELF with SHA-256 fe3bc08c928c9177eb2e685dc3db4c15bdc972ffe782b3a50282d88499388753. Direct instruction addresses and ELF RELATIVE relocations were inspected locally. `verified-dispatch.json` records nine checked relocation/stored-pointer agreements, six exact literals and 16 decoded windows with original bytes. The full disassembly, frame table and candidate call graph are preserved separately. The graph is an analysis aid: it omits unresolved indirect calls and may include cleanup/error paths, so reachability alone is not a semantic proof.

The worker-labelled routine has unwind range 0x3cb1b0–0x3cf98d and references `run_trusted: starting` and `run_trusted: fd mappings built, executing tool`. It is statically called from the dispatch routine at 0x3c701c. Within it, 0x3cb613 calls 0x3ca360; 0x3cacae calls 0x414400; and 0x41479f calls 0x40d100. The latter is the catalog response-processing routine already examined. These direct calls and labels establish a concrete static worker-associated route in the supplied executable. They do not establish the protected runtime worker's deployed build identity or which branches it took.

The internal argument serializer identifies these adjacent fields:

| Name | Argument offset | Key association address |
|---|---:|---:|
| allow_stub | 0x20b | 0x45f951 |
| raw | 0x20c | 0x45f971 |
| json | 0x20d | 0x45f991 |

At 0x40d14e–0x40d171, the response routine copies 0x210 bytes of arguments to state+0x338. Thus the raw field is at state+0x544 (0x338+0x20c). At 0x411add, that byte is tested. A nonzero value jumps to 0x412c04. This resolves the raw-flag location independently of its spelling in help text. The preceding state+0x543 test maps to `allow_stub`, not `raw`.

At 0x4119f0–0x4119fe, the routine saves a string-shaped triple: allocation/capacity-like word, pointer and length. The raw branch at 0x412c04 reloads the saved pointer and length from state+0x8a8/+0x8b0 and calls slot 0xb1caf0, resolved to 0x500b50. It does not pass the parsed product vector stored at state+0xa08. The product parser may already have run, but its vector is not the raw writer's input on this branch.

Function 0x500b50 forwards its input pointer and length through slot 0xb1cad8 to 0x5007f0. On success it checks the last byte; if empty or not newline, it calls the same writer with the literal byte 0x0a. Function 0x5007f0 obtains and locks a shared output object, then forwards that exact slice through slot 0xb217d0 to 0xa84e90. Its buffered-write path calls 0xa6d8b0, whose instruction 0xa6d8fe sets fd 1 and 0xa6d909 calls imported `write` through slot 0xb226e0. This supports a stdout-writing interpretation of the raw branch. The disassembly also has error paths; this is not a promise that every write succeeds.

A further static link resolves the formerly unconnected generic endpoint selector: 0x40e559 calls slot 0xb1c9f0 → 0x4a89d0, which calls slot 0xb1cc00 → 0x52e720. The selector is therefore reachable from the same catalog routine. The actual endpoint chosen for the saved requests remains unobserved. No endpoint was called during this analysis.

## Corrections to previous local interpretations

The previous response audit labelled 0x377970 a whitespace/error helper. Its first substantive action is a call at 0x3779bd to 0x378250, before the trailing-whitespace check. The latter recursively processes structured values, including array-shaped sequences and string/number branches. Therefore describing 0x377970 solely as whitespace checking omitted substantive parsing. This correction does not imply product ranking occurs there. The original review is preserved unchanged.

The old worker visibility limit applies to our runtime captures. It must not be read as evidence that all worker-associated code is absent from the downloaded executable. The new static chain gives us an additional local route to inspect.

## Explanatory pseudocode

This is Astra's bounded reconstruction, not original Rust source and not a demonstrated full request lifecycle:

```text
args_copy = copy_args_into_state(args)
response_text = previously_constructed_response_string
parsed_products = optional_product_parse(response_text)

if args_copy.raw:
    write_stdout(response_text)
    if response_text is empty or does not end with newline:
        write_stdout(newline)
```

The omitted code includes request/response acquisition, status handling, stub detection, validation, retry/error handling, side effects and cleanup. The representation labelled response_text may already have undergone decoding or processing. In particular, the helper at slot 0xb21bb0 resolves to 0xa923b0 and contains UTF-8-replacement-shaped logic; an exact original-byte passthrough claim would require tracing its full input and semantics.

## Remaining question and next discriminating step

The new evidence narrows one possibility: on this compiled raw branch, the writer uses the retained string rather than constructing raw output from reordered parsed products. It does not prove that the string's contents were not reordered before this point. Score computation and the first ordering transformation remain unlocated; the strict goal remains unmet.

The next local task is to trace where the retained response string is built, across the asynchronous body-receipt path into 0x411940, and follow the actual request construction. This can distinguish ordinary response decoding from a local product-list transformation. Only after that static path is understood would a same-build, same-request capture of body bytes versus stdout add decisive runtime evidence. The already-saved traces lack the worker body and an invocation-time executable hash; two separately sampled responses cannot fill that gap.

## Summary

Static inspection of the complete supplied client identified worker-associated dispatch code and a raw-output branch that forwards retained response text to stdout with optional newline completion. The parsed product vector is not the writer input on that branch. These findings locate a later output boundary but neither authenticate its execution for captured requests nor identify the upstream scoring or ordering operation.

## Reproduction

The analysis script and the full disassembly are not published, because they quote the full program, which this repository does not include. The four byte pieces are in [evidence/program/decoded-pieces/](../evidence/program/decoded-pieces/).
