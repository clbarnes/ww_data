# WormWiring data tables

Plaintext datasets from [WormWiring](http://wormwiring.org/series/),
under git control for version-pinning purposes.

[last_changed.txt](./last_changed.txt) contains

- a 32-character hexadecimal md5 hashsum of the contents of [./data](./data),
- a line break
- a UTC timestamp of when the [./populate.py](./populate.py) script last changed the data, in [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601) format

## Populate

In a python 3.7+ environment fulfilling the requirements (see [requirements.txt](./requirements.txt)), run

```bash
./populate.py
```

This will scrape the WormWiring website for CSV and TSV tables.
They will be standardised (given the same headers, strings stripped, lists sorted) and saved.

If the dataset has changed, [last_changed.txt](./last_changed.txt) will be updated.

## Attribution

Data available on WormWiring; analysis published in Nature https://doi.org/10.1038/s41586-019-1352-7

```bibtex
@article{cook2019whole,
  title={Whole-animal connectomes of both Caenorhabditis elegans sexes},
  author={Cook, Steven J and Jarrell, Travis A and Brittin, Christopher A and Wang, Yi and Bloniarz, Adam E and Yakovlev, Maksim A and Nguyen, Ken CQ and Tang, Leo T-H and Bayer, Emily A and Duerr, Janet S and Bülow, Hannes E and Hobert, Oliver and Hall, David H and Emmons, Scott W},
  journal={Nature},
  volume={571},
  number={7763},
  pages={63},
  year={2019},
  doi={10.1038/s41586-019-1352-7},
  url={https://doi.org/10.1038/s41586-019-1352-7},
  publisher={Nature Publishing Group}
}
```

License is as relevant to those sources.

All credit and attribution should go to the [Emmons lab](http://wormwiring.org/pages/contact.htm).

