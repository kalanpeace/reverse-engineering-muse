# Distinct capability check: no new scoring access

Author: Astra (gpt-6-astra). Local evidence review: Luna (gpt-6-luna, max). Existing Muse main chat, 2026-09-27 UTC.

**This check produced no new scoring code, formula, component scores or runtime trace.** We stopped additional catalog batches and explicitly excluded another skill-description search.

The concrete gap was that earlier discovery repeatedly used `muse.skill_search`; loading the `shopping` namespace did not establish whether the tool registry exposed another catalog interface. We asked for the actual declared registry-discovery capability and permitted further discovery only through a genuinely exposed operation and observed names.

Muse supplied a 3,496-byte ZIP with three text files plus a manifest. The local SHA-256 matches the displayed `a8e5556675b6fd648984a96c293a78b51272c11621200e0c10e7a3d89938dd47`; all three manifest rows and ZIP CRC match. Screenshots are not published; the reply is in the chat transcript, and the ZIP is [evidence/tool-registry/](../evidence/tool-registry/).

The result is explicitly a **manual transcription** of session context. It says the registry offers only loading by an already-known namespace name, no list/search operation and no separately named catalog/scoring namespace. This is Muse's bounded capability report, not an independently authenticated registry inventory. The file does not contain a native JSON argument schema; its `paths` argument claim cites the prior invocation, and some instruction prose is labelled “verbatim in substance.” We cannot promote those assertions into a verified service contract. Namespace names alone do not establish all capabilities inside them.

No new service was invoked according to the reply. No new original implementation was supplied. The full-client export boundary remained unresolved at this point; no equivalent extraction was attempted. (Later on 27 September the full program was exported with explicit approval; see [TWO-ROUTES-2026-09-27.md](TWO-ROUTES-2026-09-27.md).)

The practical decision is to stop treating more repetitions of the same output surface as a route to exact source recovery. Further behavioral tests can answer specific new predictions, but a decisive formula investigation needs additional observability: an actual score-component diagnostic or implementation/configuration artifact. A same-response trace could locate ordering; even a complete client would not necessarily expose the remote scorer. A separately authorized merchant-field experiment could answer business questions without recovering that formula.

This is a recorded stopping point for this discovery path, not proof that every black-box method is exhausted or that no relevant interface exists anywhere.
