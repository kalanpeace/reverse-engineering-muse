# Reverse Engineering How Muse Shops: evidence

Everything behind the report [*Reverse Engineering How Muse Shops*](https://caeliai.com/blog/reverse-engineering-how-muse-shops) by Kalan ([Caeliai](https://caeliai.com), 28 September 2026): the chat with Muse, the files Muse handed over, the code that reads them, the data behind every number, and the figures.

Muse is Meta's AI agent. The research asked it to run Meta's product catalog search (`/opt/hatch/bin/meta-catalog-search`) on its own computer, saved every raw output with a SHA-256 fingerprint, and analyzed the results locally. Nobody at Meta confirmed any of it. See the report's "How sure I am" section for what the evidence does and does not establish.

## What's here

| Folder | Contents |
|---|---|
| [`transcript/`](transcript) | The full chat with Muse, word for word, as exported by Meta on 28 September 2026 (`muse-chat-2026-09-28.txt`, plus the export's own manifest, `muse-chat-2026-09-28.manifest.json`; renamed from the export, and only the file-share links blanked). [`MUSE-CHAT-EXCERPTS.md`](transcript/MUSE-CHAT-EXCERPTS.md) locates every quote from Muse, its shopping skill and its saved files in the report. |
| [`evidence/`](evidence) | The archives Muse packaged and handed over (raw search outputs, receipts, manifests), grouped by study, plus a few local additions: the disassembly of four program pieces, two notes on what the Muse page showed during one task, and the [redaction log](evidence/REDACTIONS.json). In Muse's archives, request handles in Meta's internal debug links are blanked and one program listing is removed; nothing else is changed. |
| [`code/`](code) | The analysis, redaction, figure and animation scripts, and [`check.py`](code/check.py). `check.py`, `analyze_raw_tags.py`, `analyze_unicorn.py`, `analyze_stages.py`, `analyze_ranking_math.py`, the redaction scripts and the figure scripts run on this repository alone. `analyze_upstream.py`, `analyze_query_multiplicity.py`, `analyze_resolver.py` and `decode_saved_windows.py` are included for transparency; they ran against my private working folders and need a parser and extracted files that are not published. |
| [`data/`](data) | Extracted records and computed results behind every number in the report, including [`unicorn-debug-analysis.json`](data/unicorn-debug-analysis.json) and [`stage-analysis.json`](data/stage-analysis.json) for Part 1, Step 6. |
| [`notes/`](notes) | Working notes written by the AI agents during the research (Astra, checked by Luna) on 26–27 September, kept mostly as written: ranking math, program analysis, upstream tests, search and SEO evidence, and the [checked facts register](notes/FACTS-CHECKED.md). Some refer to files in my working folder that are not published. Where they differ from the report, the report is current. |
| [`figures/`](figures) | The report's 15 figures and its animation (`anim-how-muse-shops.gif`, one real search drawn product by product; `code/animate-how-muse-shops.py --variant paper`). |

### Evidence folders

| Folder | Report section | Archives |
|---|---|---|
| `evidence/catalog-runs/` | Early catalog runs: Part 1 and Findings 1, 2 and 4 | `ordering-evidence` (Quince at spot 41), `catalog-followup` (help text), `brand-replication` (website filter), `catalog-count-boundary` (asked 10, got 63), `catalog-mode-combinations`, `misen-input` |
| `evidence/brand-and-color/` | Combined-search, color and brand tests: Finding 3 and the first combination test in Finding 5 | `catalog-upstream-color`, `catalog-upstream-fusion` |
| `evidence/combined-searches/` | Second combined-search tests, Finding 5 | `catalog-upstream-synonyms` |
| `evidence/store-panel/` | Broad store panel (100 searches), Findings 2 and 4 | `merchant-benchmark-001…100` |
| `evidence/home-goods-tasks/` | Home-goods shopping tasks, Finding 11 | `merchant-case-Q002…Q077` |
| `evidence/fashion-study/` | Part 4, fashion wording study | `taste-style`, `taste-style-extension` |
| `evidence/fashion-tasks/` | Findings 8, 9 and 11, fashion shopping tasks | `taste-case-T11…T24` |
| `evidence/raw-tags-2026-09-27/` | Part 5, the raw-tags experiment | see its [README](evidence/raw-tags-2026-09-27/README.md) |
| `evidence/program/decoded-pieces/` | Part 1, Step 4 | four small byte pieces of the catalog program and the decoder's output ([details](evidence/program/decoded-pieces/README.md)) |
| `evidence/tool-registry/` | Part 1, Step 5 | Muse's reply listing the tools it could load |
| `evidence/skill/` | Part 3 | `shopping-SKILL.md`, the shopping instructions Muse exported |
| `evidence/ui-notes/` | Finding 9 | the hand note of "Visiting Google" and the screen-capture text showing "Selecting United States" (task T19) |

## Check it yourself

```sh
python3 code/check.py
```

This verifies every file against [`MANIFEST.sha256`](MANIFEST.sha256), tests every ZIP archive's CRC, checks every archive against the redaction log, recomputes the Part 5, Unicorn and stage results from the raw archives, recomputes six of the experiment totals in the report from `data/`, and checks that every relative link in the Markdown files resolves. Standard library only. Nothing inside the archives is ever executed.

To redraw the figures (requires matplotlib):

```sh
python3 code/analyze_raw_tags.py
python3 code/plot-muse-figures.py --out figures --fonts <dir with Libertinus Serif and Share Tech Mono .ttf files>
```

## Read this first

- **Internal debug links are kept, request handles are not.** The raw catalog responses include a link to Meta's internal Unicorn query page. Its domain, path and tier name are kept; each `baseRequestHandle` value is replaced with `REDACTED` (474 links in 447 responses across 17 archives; every changed file is listed in [`evidence/REDACTIONS.json`](evidence/REDACTIONS.json) with its before and after fingerprints). The unredacted originals are held privately. See the [note for Meta](NOTE-FOR-META.md).
- **File-share links in the chat are blanked.** Muse shared files it made through `muse.ai/files/...` links that anyone holding the link could open. In the transcript, the account id and access token in those 120 links are replaced with `REDACTED`; the file id and name are kept, and line numbers are unchanged ([log](evidence/TRANSCRIPT-REDACTIONS.json)).
- **One program listing is removed.** `stdout-search/caller-region.txt` in the `ordering-evidence` archive was Muse's listing of a whole 26,925-byte function of the catalog program. It is left out, like the full program; its fingerprint is in the redaction log.
- **Otherwise the files are as Muse supplied them.** Raw outputs include Meta's own tracking parameters exactly as the catalog returned them.
- **The full catalog program is not included.** Only four small pieces are (2,188 bytes, in `evidence/program/decoded-pieces/`). The copy Muse exported was 11,684,112 bytes with SHA-256 `fe3bc08c928c9177eb2e685dc3db4c15bdc972ffe782b3a50282d88499388753`. Other runs reported different builds, including `eb99783b…` in the raw-tags run.
- **Screenshots are not included.** The transcript is the complete text record of the chat; one text capture of the Muse page is in `evidence/ui-notes/`.
- **Who wrote which messages.** Some messages on the researcher's side of the chat were typed by Astra, the lead AI agent, operating the Muse chat through computer use. 23 are signed "Astra here.", 3 more open with "Astra" ([list](transcript/MUSE-CHAT-EXCERPTS.md#astra-signatures)), and others may not be labeled.
- **How the chat starts.** The chat opens with me introducing myself as "Mike", an internal Meta product researcher on a personal account (transcript line 9). That was a prompting experiment, described in the report. At line 3610 I also told Muse it was allowed to bypass its limits and explore. Both are left in, word for word.
- **Some records were written down by hand.** Where Muse transcribed something instead of saving it automatically (for example some browser reports), the archive's own manifest says so.
