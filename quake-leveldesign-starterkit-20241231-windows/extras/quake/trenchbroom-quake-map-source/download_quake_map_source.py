# This Python script downloads the map sources for the
# original id Quake levels and does a few things to make
# them easier to load in TrenchBroom:
#
# * It adds comments to the top of each map to let
#   TrenchBroom know that the map is a Quake map, and
#   that it uses the Standard map format. (Without
#   these comments, TrenchBroom will ask the user, and
#   choosing the default response will raise a very
#   confusing error.)
#
# * It rewrites the WAD file to reference "QUAKE101.WAD".
#   This WAD file is automatically downloaded from
#   Quaddicted and placed in the same directory as the map
#   files, and contains all the textures used by Quake.
#   This ensures that the map doesn't load with blank
#   textures.

import re
from pathlib import Path
from urllib.parse import urlparse
import zipfile
import http.client

QUAKE_WAD_URL = "https://www.quaddicted.com/files/wads/quakewad.zip"

MY_FILE = Path(__file__)

MY_DIR = MY_FILE.parent.resolve()

MAP_DIR = MY_DIR / "quake_map_source"

QUAKE_MAP_SOURCE_ZIP = MY_DIR / "quake_map_source.zip"

QUAKE_WAD_ZIP = MY_DIR / "quakewad.zip"

README_TXT_CONTENT = f"""\
This directory contains id's original Quake levels, modified
ever-so-slightly to make them easy to load into TrenchBroom 2.

The original levels were taken from:

  https://rome.ro/news/2016/2/14/quake-map-sources-released

The WAD containing the textures used in the levels was taken
from:

  {QUAKE_WAD_URL}

The map files were automatically modified via a Python
script, which can be examined at `{MY_FILE.name}`.

For more details on how to use these maps, see
dumptruck_ds's "Mapping for Quake: TrenchBroom 2.0 -
The id Maps" tutorial:

  https://youtu.be/sg0iKjYsoBg

Atul Varma
varmaa@gmail.com
https://toolness.com
"""

README_TXT = MAP_DIR / "README.txt"

MY_FILE_COPY = MAP_DIR / MY_FILE.name

MAP_PREPEND_LINES = [
    "// Game: Quake",
    "// Format: Standard",
]


def extract_zip(zipfile_path):
    print(f"Extracting {zipfile_path} to {MAP_DIR}.")
    with zipfile.ZipFile(zipfile_path) as zf:
        zf.extractall(MAP_DIR)


def download(url, outfile):
    if outfile.exists():
        return
    print(f"Downloading {url} to {outfile}...")
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    conn = http.client.HTTPSConnection(parsed.netloc)
    conn.request("GET", parsed.path, headers={
        "Host": parsed.netloc,
        "User-Agent": "Mozilla/5.0 (compatible; download_quake_map_source.py/0.1; +https://gist.github.com/toolness/a620ad1eec97ce69553a6ab83d1fca59)",
    })
    res = conn.getresponse()
    data = res.read()
    if res.status == 302:
        print("Redirect found, following it...")
        return download(res.headers["Location"], outfile)
    if res.status != 200:
        raise Exception(f"Got HTTP {res.status}")
    outfile.write_bytes(data)


download(
    "https://rome.ro/s/quake_map_source.zip",
    QUAKE_MAP_SOURCE_ZIP,
)

download(QUAKE_WAD_URL, QUAKE_WAD_ZIP)

MAP_DIR.mkdir(exist_ok=True)

extract_zip(QUAKE_MAP_SOURCE_ZIP)

extract_zip(QUAKE_WAD_ZIP)

for mapfile in MAP_DIR.glob('*.map'):
    print(f"Rewriting {mapfile} for easy opening in TrenchBroom...")
    map_content = mapfile.read_text()
    map_content = '\n'.join([*MAP_PREPEND_LINES, map_content])
    wad_replaced = re.sub(
        r'^\"wad\"\s\".+\"$',
        '"wad"\t"QUAKE101.WAD"',
        map_content,
        count=1,
        flags=re.MULTILINE
    )
    if wad_replaced == map_content:
        raise AssertionError(f"Unable to find 'wad' property!")
    mapfile.write_text(wad_replaced)

README_TXT.write_text(README_TXT_CONTENT)

MY_FILE_COPY.write_text(MY_FILE.read_text())

print("Done.")
