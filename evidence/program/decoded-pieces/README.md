# Four pieces of the catalog program, and their disassembly

The four `.bin` files are byte-identical copies of `code-slices/` inside [`../../catalog-runs/ordering-evidence-2026-09-26.zip`](../../catalog-runs/ordering-evidence-2026-09-26.zip). Each was wrapped in an ELF section and disassembled on my computer with Apple LLVM `objdump`; the `.llvm.stdout.txt` files are that output.

| Slice | Bytes | Local decoded instructions |
|---|---:|---:|
| caller-0x4bb230 | 887 | 202 |
| pass-0x4a2cc0 | 466 | 116 |
| pass-0x4a2ea0 | 442 | 108 |
| pred-0x4bb670 | 393 | 114 |

Total: 2,188 bytes and 540 instructions. [`results.json`](results.json) compares that output with the disassembly Muse supplied (zero differences) and lists per-slice hashes; its output paths refer to my working folder. [`additional-text-verification.json`](additional-text-verification.json) is the output of [`code/decode_saved_windows.py`](../../../code/decode_saved_windows.py) for four further windows whose text dumps are not published. In the `.llvm.stdout.txt` files and `additional-text-verification.json`, the local folder path before each file name was removed; nothing else was changed.

This is disassembly, not original Rust source. Agreement verifies supplied byte decoding and instruction boundaries, not remote origin, all control flow, runtime behavior or the server-side ranking formula. These files have not been executed. Keep them as immutable data.
