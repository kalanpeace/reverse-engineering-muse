# Complete client export and bounded runtime tracing

Later local inspection: [static dispatch review](STATIC-DISPATCH-2026-09-27.md) closes several static gaps recorded below. The historical runtime limits still apply.

Prepared by **Astra (gpt-6-astra)**, with independent local static reviews by **Luna (gpt-6-luna, max)**, 2026-09-27 UTC.

## Human version

Both proposed routes produced new evidence. We obtained the complete compiled catalog client and traced two ordinary invocations. The traced process delegates through a local worker socket, so tracing that process alone does not reveal the worker's scoring calculation. We still have no ranking formula or demonstrated first ordering transformation.

## Facts

Kalan explicitly approved export of `/opt/hatch/bin/meta-catalog-search` for local static analysis. The former exact-file approval boundary is resolved. The executable remains local and was never executed here. The approval does not extend to worker attachment, credential access, security changes or direct service probing.

The executable is an 11,684,112-byte ELF64 x86-64 PIE. Its SHA-256 is `fe3bc08c928c9177eb2e685dc3db4c15bdc972ffe782b3a50282d88499388753`. Its archive hash, CRC and all 16 manifest rows verified. All four earlier binary slices match the corresponding executable bytes: 2,188 bytes in total. This materially improves our ability to follow previously missing calls. It establishes byte consistency, not independent authentication of the remote machine or original Rust source.

There is a build-identity caveat. Earlier `stdout-search/COMMANDS.md` reports SHA-256 `db8bcb0c16143c71d1d0d320ad2a16404efa723ed2db582f39e9340e59465702` and Build ID `e9c8beff451ffdb7c933c3f5e4a318e8bd0089f9`; the new ELF's Build ID is `dcc174575349c13ff33728c294e09cc4998a1ac5`. The matching slices establish consistency only for those spans. They do not establish whole-file identity across historical tests, and the reason for the differing identifiers is unknown. The runtime collectors logged the executable path but did not hash its bytes at each invocation.

Muse supplied receipts reporting installed strace 6.8 and a successful `/bin/true` tracing preflight; ltrace and gdb were not found. We then supplied two exact Python collectors, each permitting one normal catalog invocation, no retries, and separate stdout/stderr capture. Both downloaded collectors match the locally authored bytes. Both runs returned exit 0. Their ZIP hashes, CRCs and all six manifest rows per ZIP verified.

These are **two separate sampled requests**, not stages of the same response. Each contains 43 returned products. Each has a score increase at position 41:

| Capture | Position 40 score | Quince at position 41 |
|---|---:|---:|
| Receive trace | 0.546875 | 0.761719 |
| Descriptor trace | 0.546875 | 0.765625 |

The new traces confirm that the ordering mismatch still occurs under this instrumentation. They do not explain its cause or reproduce the earlier Quince score of 0.773438.

The first trace records a connection to `/run/hatch/privsep/meta-catalog-search.sock` and a 50-byte socket reply:

```json
{"response_bytes":"e30=","exit_status":{"Code":0}}
```

The encoded response is `{}`. Separately captured stdout contains 172,837 bytes of catalog results. The small socket reply is therefore not the product-list body. The second trace records a `sendmsg` with `SCM_RIGHTS` after connecting to the worker socket. That is evidence of file-descriptor transfer, but its descriptor values are abbreviated in this capture.

Neither trace includes a `write` or `writev` to file descriptor 1 among its captured calls. This does **not** prove absence of every possible stdout-writing mechanism: the collectors did not trace every syscall. Large later reads from descriptor 9 in the first trace must not be mistaken for incoming products; the second trace identifies the analogous reads as loading a CA bundle for later telemetry.

## Static inference and hypotheses

The complete binary resolves three previously unavailable indirect-call targets. The ELF relocation and stored-pointer values agree:

| GOT slot | Target | Bounded interpretation |
|---|---|---|
| `0xb1cd18` | `0x556fa0`, then slot `0xb1cd20` | A short forwarding function |
| `0xb1cd20` | `0x566a00` | Builds auxiliary tagged identifier structures from projected IDs/URLs; exact final consumer remains unresolved |
| `0xb1cd38` | `0x560070` | A different caller branch, reached before the parser/projection path; its tag meaning remains unresolved |

In the inspected `0x566a00` path, IDs are read in forward index order and tagged with `fbid`; the URL path uses `url`. The inspected call receives projected ID and URL arrays rather than the original product-record array. This advances the earlier missing-helper analysis, but does not expose a product-score comparison or a product-order transformation. The ultimate helper at `0xb1cd10` remains semantically unresolved.

Another compiled routine, starting at `0x45f550`, contains serialization-shaped calls associating internal argument fields with `queries`, `num_results`, `brands` and `prefer_brands`. Astra rechecked the field-pointer and key-reference instructions. This is a bounded, explanatory rendering of those calls, **not recovered Rust source or an observed network request**:

```text
serialize_field("queries", argument_object + 0x30)
serialize_field("num_results", argument_object + 0x200)
serialize_field("brands", argument_object + 0x90)
serialize_field("prefer_brands", argument_object + 0x138)
```

The field names do not reveal boost weights or the receiving worker's interpretation. The complete CLI parsing-to-transmission path has not been reconstructed.

The runtime evidence supports a delegation boundary between the launched CLI process and a separate local worker. A descriptor handoff explains how output could arrive separately from the small status reply, but the trace alone does not identify every descriptor or establish the worker's implementation.

Previously decoded parser and serializer routines remain actual bytes in this executable. Their presence does not establish that the observed unprivileged process executes those routines for the traced request. Any reconstructed client path must be tied to the relevant dispatch branch before it is treated as the live catalog path.

## What remains unobserved

The worker's response receipt, any remote catalog service processing, score calculation, score components and the first operation choosing returned order remain unobserved. There is no same-request comparison of an incoming HTTP body against CLI stdout. No worker was attached to, no alternate endpoint was called and no security setting was changed.

This did not reveal the scoring formula: collecting a complete executable and locating a handoff are substantial new evidence, but neither recovers the scoring function or ordering operation. We have reached a concrete runtime visibility limit for the two tested tracing methods; this is not proof that every possible research method is exhausted.

## Summary

After explicit approval, we acquired the complete compiled client and verified consistency with earlier code slices. Two bounded traces of ordinary catalog invocations showed communication with a local worker over a Unix socket; one trace exposed a status-only response and another exposed descriptor-transfer metadata. The catalog output continued to show nonmonotone score order. These observations locate an additional execution boundary but do not identify the ranking formula, authenticate the remote execution independently, or establish that CLI raw output equals an untouched upstream HTTP body.

## Reproduction and artifacts

The trace captures, screenshots and the full executable are not published. The derived result is [runtime-trace-audit.json](../data/runtime-trace-audit.json). The prompts are in the chat transcript.

The trace options were checked against the [strace manual](https://man7.org/linux/man-pages/man1/strace.1.html), linked by the [strace project](https://strace.io/). Payload suppression and a limited syscall set intentionally constrain what these captures can establish. They are not general process or network captures.
