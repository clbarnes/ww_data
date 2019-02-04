# WormWiring data tables

Plaintext datasets from [WormWiring](http://wormwiring.org/series/),
under git control for version-pinning purposes.

See `last_changed.txt` for when the dataset was last changed, in [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601).

## Populate

In an environment fulfilling the requirements (see [requirements.txt](./requirements.txt)), run

```bash
./populate.py
```

This will scrape the WormWiring website for CSV and TSV tables.
They will be standardised (given the same headers, strings stripped, lists sorted) and saved.

## Attribution

This repository is unreleased and therefore intentionally unlicensed.

All credit and attribution should go to the [Emmons lab](http://wormwiring.org/pages/contact.htm).
