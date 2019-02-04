#!/usr/bin/env python
import csv
import hashlib
import os
from itertools import zip_longest
from pathlib import Path
import logging
from typing import Iterable, Tuple
from datetime import datetime

from requests import HTTPError
from requests_html import HTMLSession

logger = logging.getLogger(__name__)

here = Path(__file__).absolute().parent
data_dir = here / "data"

session = HTMLSession()
root_url = 'http://wormwiring.org/'
r = session.get(root_url + 'series/')

suffix = ' - Description'

parseable = ('.csv', '.tsv')


def noop(arg):
    """Do nothing, return arg"""
    return arg


def zip_fns(iterable, fns=None):
    """Pass items from the first iterable into the corresponding function in the second, yield the result"""
    if not fns:
        fns = []

    for item, fn in zip_longest(iterable, fns):
        if fn is None:
            fn = noop
        yield fn(item)


def to_int(s):
    """Strip and parse string"""
    return int(s.strip())


def strip(s):
    return s.strip()


def sort_strlist(s):
    """Deserialise, sort, and reserialise a list of strings in the format "potato,spade,elephant" """
    return ','.join(sorted(s.strip().split(',')))


def mangle_rows(source_rows, fns=None, key=None, reverse=False):
    """Given a list of row lists, a list of functions to apply to each item in every row, and some sorting arguments,
    transform and sort a table.
    """
    rows = []
    for row in source_rows:
        if not row:
            continue
        try:
            rows.append(list(zip_fns(row, fns)))
        except Exception as e:
            print(row)
            raise e
    rows.sort(key=key, reverse=reverse)
    return rows


class DataMangler:
    """Object which fetches a file from the URL, transform and sort it based on the file type, and save it"""

    def __init__(self, path: Path, url: str):
        self._logger = logging.getLogger(f"{__name__}.{type(self).__name__}")

        self.path = path
        self.url = url

        self.strategy = self._get_strategy()

    def _get_strategy(self):
        title = self.path.stem.lower()
        for key, strategy in [
            ("edge list", self._parse_edgelist),
            ("contact list", self._parse_contactlist),
            ("synapse list", self._parse_synapselist),
            ("adjacency", self._parse_adjacency)
        ]:
            if key in title:
                return strategy

        raise ValueError(f"Cannot parse file, unknown type: {self.url}")

    def _parse_edgelist(self, lines):
        """CSV, [pre, post, weight, type]; should sort"""
        next(lines)  # skip header
        rows = mangle_rows(csv.reader(lines), [strip, strip, to_int, strip])

        with open(self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["Source", "Target", "Weight", "Type"])
            writer.writerows(rows)

    def _parse_contactlist(self, lines):
        """TSV, [pre, post, preidx, postidx, em_section, contact_length_pixels, pre_obj, post_obj]; should sort"""
        reader = csv.reader(lines, delimiter='\t')
        headers = [s.strip() for s in next(reader)]
        fns = [strip, strip, to_int, to_int, strip, to_int, to_int, to_int]
        rows = mangle_rows(csv.reader(lines, delimiter='\t'), fns)

        with open(self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    def _parse_synapselist(self, lines):
        """CSV, [pre, post_list, # sections, synapse id, series]; should sort"""
        reader = csv.reader(lines)
        headers = [s.strip() for s in next(reader)]
        fns = [strip, sort_strlist, to_int, to_int, strip]
        rows = mangle_rows(csv.reader(lines), fns)

        with open(self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    def _parse_adjacency(self, lines):
        """CSV, save raw"""
        with open(self.path, 'w') as f:
            f.writelines(lines)

    def process(self):
        self._logger.debug("Processing %s", self.url)
        r = session.get(self.url)  # streaming is probably slower
        r.raise_for_status()
        self._logger.debug("Saving to %s", self.path)

        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.strategy(r.iter_lines(decode_unicode=True, delimiter='\n'))


def get_paths() -> Iterable[Tuple[Path, str]]:
    """Parse the WormWiring website to find tabular text datasets"""
    series_list = r.html.find('.series')
    logger.debug('Found %s series', len(series_list))

    for series in series_list:
        header = series.find('.series-header', first=True).text.strip(':')
        logger.debug('Processing series "%s"', header)
        series_dir = data_dir / header

        subs = series.find('.series-sub')
        datas = series.find('.series-data')

        assert len(subs) == len(datas), 'Mismatched number of subheadings and data lists'
        logger.debug('Found %s data subsets', len(subs))

        for sub, data in zip(subs, datas):
            subheader = sub.text
            if subheader.endswith(suffix):
                subheader = subheader[:-len(suffix)]

            logger.debug('Processing data subset "%s"', subheader)

            sub_dir = series_dir / subheader

            items = data.find('li')
            logger.debug('Found %s data items', len(items))

            for li in items:
                open_brack = li.text.find('(')
                if open_brack < 0:
                    open_brack = None
                li_title = li.text[:open_brack].strip()

                logger.debug('Processing data item "%s"', li_title)

                anchors = li.find('a')
                logger.debug('Found %s URLs', len(anchors))

                for anchor in anchors:
                    ext = anchor.text.strip(') ')
                    logger.debug('Processing anchor "%s"', ext)
                    if ext in parseable:
                        yield sub_dir / (li_title + ext), root_url + anchor.attrs['href'].lstrip('./')


def hash_file(rel_path: Path, md5=None, hash_path=False):
    """ Hash a file (and optionally, its path)

    Adapted from https://stackoverflow.com/a/22058673/2700168"""
    buf_size = 65536
    md5 = hashlib.md5() if md5 is None else md5.copy()

    if hash_path:
        for part in rel_path.parts:
            md5.update(part.encode())

    with open(rel_path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            md5.update(data)
    return md5


def hash_dirs(root: Path) -> hashlib.md5:
    """Hash all files in the directory, including their paths, in sort order"""
    root = root.absolute()
    md5 = hashlib.md5()

    for this_root, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fname in sorted(filenames):
            fpath = Path(this_root, fname)
            rel_fpath = fpath.relative_to(root)
            md5 = hash_file(rel_fpath, md5, True)

    return md5


def process(path, url):
    try:
        DataMangler(path, url).process()
    except (HTTPError, ValueError) as e:
        logger.warning(str(e))


class DirChecker:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.initial_digest = None
        self.final_digest = None

    @property
    def has_changed(self):
        if self.initial_digest is None:
            raise RuntimeError("Initial hash not completed, cannot compare states")
        final_digest = self.final_digest or self._get_digest()
        return final_digest != self.initial_digest

    def _get_digest(self):
        return hash_dirs(self.root_dir).hexdigest()

    def __enter__(self):
        self.initial_digest = self._get_digest()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.final_digest = self._get_digest()


def main():
    with DirChecker(data_dir) as d:
        for path, url in get_paths():
            process(path, url)

    if d.has_changed:
        with open(here / "last_changed.txt", "w") as f:
            f.write(datetime.utcnow().isoformat())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
