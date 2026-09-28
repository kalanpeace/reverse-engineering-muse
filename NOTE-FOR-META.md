# A note for Meta

While researching how Muse shops, I found that the raw catalog responses Muse handed back include internal debug links, like this one:

```text
https://www.internalfb.com/unicorn/query?tier=unicorn.aggregator.alacorn-genai-synapse-products.211.denmark.s00.r01-prod&baseRequestHandle=REDACTED
```

There are 474 of these links in the archives in this repository. They all point to Meta's internal network, behind Meta's employee sign-in. The one link that was opened (from a later follow-up search, not in this repository) showed only Meta's "Internal Login" page. I have no Meta login, so all I have are the addresses themselves.

In this repository, the domain, path and tier name are kept, and every request handle is replaced with `REDACTED`. [`evidence/REDACTIONS.json`](evidence/REDACTIONS.json) lists every change. The unredacted originals are kept privately.

The chat transcript here also contains Muse's own description of its safety checker, including that it "*fails open* when the classifier backend errors" (transcript line 3627). I have not tested this. The file-share links Muse posted in the chat have their account id and access token blanked.

If anyone on Meta's team would like to take a look, you can contact me at [kalanpeace@gmail.com](mailto:kalanpeace@gmail.com).

Kalan
