# Raw-tags collection, 27 September 2026

The Part 5 experiment ("I tested it: the raw-tags experiment"). Planned in advance and collection only: Muse ran one collector script on its own computer and handed back the ZIP in this folder. The only change is that the request handle in each of the 48 internal debug links is blanked; see [`../REDACTIONS.json`](../REDACTIONS.json).

| | |
|---|---|
| Archive | `raw-tags-20260927T234719067674Z.zip` |
| Original, as Muse supplied it | 2,956,811 bytes, SHA-256 `d0fec8cf6ad6c668b3c0f7e988281158e20dfe5da5aef0aa0ef36f95e1a521aa` (held privately) |
| This copy, handles blanked | SHA-256 `05d0b3ae9748541d4d8af5c734e3758e82160450256129612937aba8db630a51` |
| Files | 149: 48 calls × (`execution.json`, `stdout.bin`, `stderr.bin`), plus `MANIFEST.csv`, `schedule.json`, `run-summary.json`, `tool-identity.json` and the collector script (`collector.py`). `MANIFEST.csv` lists the other 148 with size and SHA-256 |
| Run time | 2026-09-27 23:47:19 to 23:50:16 UTC |
| Catalog program | `/opt/hatch/bin/meta-catalog-search`, 11,532,776 bytes, SHA-256 `eb99783b88312a7aa75b843d2323a491f1bde24af5f06e39595f69b86afd240d`, identical before the first call and after the last |

## What was run

Every call used the same command, with only the query changing:

```text
/opt/hatch/bin/meta-catalog-search --query "<query>" -n 50 --conversation-id raw-tags-20260927-fixed --retries 0 --timeout-secs 30 --raw --no-save
```

No `--user-id`, `--brand`, `--domain` or other filters were sent. Each arm ran three times, interleaved (all queries once, then again, then a third time).

**Arm A, 12 product categories (36 calls):** stainless steel frying pan · 32 oz insulated water bottle · everyday backpack · office desk chair · bath towel set · men's running shoes · women's dresses · air purifier for a bedroom · burr coffee grinder · cotton bed sheets queen · moisturizer for dry skin · dog bed

**Arm B, 4 products many stores sell (12 calls):** All-Clad D3 10 inch fry pan · Hydro Flask 32 oz wide mouth · Vitamix E310 · Levoit Core 300 air purifier

Run IDs follow `<arm>-R<repeat>-Q<query number>`, for example `A-R1-Q09` is the first burr coffee grinder search.

## Checks

- The original archive's SHA-256 matches the value Muse reported in the chat.
- ZIP CRC check passes. The 100 unchanged entries in `MANIFEST.csv` match their size and SHA-256. For the 48 `stdout.bin` entries with a blanked handle, the original hash in the redaction log equals the one in `MANIFEST.csv`, and the file matches the log's redacted hash.
- All 48 calls exited with code 0, and every response's own `success` field is `true`.

## Reproduce the analysis

```sh
python3 code/analyze_raw_tags.py
```

The script reads the archive in place (nothing is extracted or executed), repeats the checks above, recomputes every Part 5 number and writes [`data/raw-tags-analysis.json`](../../data/raw-tags-analysis.json). It stops if any number differs from the report. Standard library only.

Per-category comparisons (seller rating, native checkout, the tail after a score jump) use the first of the three repeats; that is the pass the report's figures are computed from.
