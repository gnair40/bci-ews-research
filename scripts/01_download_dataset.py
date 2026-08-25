#!/usr/bin/env python3
"""
01_download_dataset.py
======================
Download the Pun et al. (2024) MINDFUL dataset from Dryad, reproducibly.

WHAT THIS SCRIPT IS FOR
-----------------------
A core rule of research is that someone else must be able to repeat what you
did. If you download data by clicking a button in a web browser, nobody can
verify *which* version you got or whether the file arrived intact. This script
replaces the clicking. It:

  1. Asks Dryad's public API which files belong to DOI 10.5061/dryad.n2z34tn5s
  2. Downloads each one into  data/raw/
  3. Verifies each file's checksum (a fingerprint that proves the bytes are
     exactly what Dryad has -- catches corrupted or truncated downloads)
  4. Writes  data/raw/download_manifest.json  recording the DOI, the dataset
     version number, every filename, its size, its checksum, and the UTC time
     of download.

That manifest is the provenance record. It is what lets you write in a paper
"we analysed version N of DOI 10.5061/dryad.n2z34tn5s, downloaded on <date>".

VOCABULARY (nothing here is assumed knowledge)
----------------------------------------------
  API      "Application Programming Interface" -- a machine-readable version of
           a website. Instead of a page designed for human eyes, it returns
           structured text (JSON) designed for programs.
  JSON     A plain-text format for nested data. Looks like Python dictionaries.
  DOI      "Digital Object Identifier" -- a permanent ID for a dataset or paper.
           Unlike a normal web link, a DOI is guaranteed not to rot.
  checksum A short fingerprint computed from a file's contents (here, MD5).
           If even one byte changes, the fingerprint changes completely.
  stream   Downloading in small chunks instead of loading the whole file into
           memory. Necessary because these files may be gigabytes.

HOW TO RUN
----------
    python3 scripts/01_download_dataset.py

Options:
    --list-only     Show what files exist on Dryad without downloading them.
    --outdir PATH   Download somewhere other than data/raw.
    --force         Re-download files even if they already exist and verify.

REQUIREMENTS
------------
    pip install requests

NETWORK NOTE
------------
This script needs to reach https://datadryad.org. Some managed/cloud
environments block outbound traffic to sites that are not on an allowlist. If
you see "ProxyError" or "403 Forbidden" from a proxy, the network policy is the
problem, not this script -- see DATASET_README.md, section "Network access".

Author: prepared for the BCI early-warning-signals project (ISEF, Year 1).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("The 'requests' library is missing. Install it with:\n"
             "    pip install requests")


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# The dataset we want. The bare identifier "n2z34tn5s" that appears in the
# literature is only the last part; the full DOI is what actually resolves.
DATASET_DOI = "10.5061/dryad.n2z34tn5s"

# Dryad's public API. "v2" is the API version -- Dryad may add a v3 later, so
# pinning v2 here is deliberate: it keeps this script's behaviour stable.
DRYAD_API = "https://datadryad.org/api/v2"

# Where the untouched downloaded files go. NOTHING in this folder is ever
# edited by our analysis code. Anything we compute goes to data/processed/.
DEFAULT_OUTDIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Be polite to a free public server: identify ourselves and don't hammer it.
# Dryad's web application firewall rejects generic automated User-Agents
# (plain "python-requests/..." or "curl/..." get a 403 on the file-download
# route). The "Mozilla/5.0 (compatible; <name>; +<url>)" form is the long-
# standing convention for well-behaved automated clients -- the same shape
# search-engine crawlers use. It identifies this project honestly and gives a
# contact URL, rather than impersonating a real browser.
USER_AGENT = ("Mozilla/5.0 (compatible; bci-ews-research/1.0; "
              "+https://github.com/gnair40/bci-ews-research)")

HEADERS = {"Accept": "application/json", "User-Agent": USER_AGENT}
DOWNLOAD_HEADERS = {"User-Agent": USER_AGENT}
REQUEST_TIMEOUT = 120      # seconds to wait before giving up on a request
CHUNK_SIZE = 1024 * 1024   # download 1 MB at a time
MAX_RETRIES = 4            # network hiccups are normal; retry a few times


# ---------------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------------

def get_access_token(session: requests.Session) -> str | None:
    """
    Exchange Dryad API credentials for a short-lived access token.

    WHY THIS IS NEEDED
    ------------------
    Dryad protects its file-download route with an anti-bot challenge that only
    a JavaScript-executing browser can pass. Rather than trying to defeat that,
    we use the route Dryad provides *for programs*: an authenticated API call.

    HOW TO GET CREDENTIALS (one-time, free)
    ---------------------------------------
      1. Go to https://datadryad.org and sign in with ORCID
         (https://orcid.org -- free, and a researcher ID worth having anyway).
      2. Open "My account" -> create an API account.
      3. Dryad issues a client_id and a client_secret.
      4. Put them in your shell before running this script:

             export DRYAD_CLIENT_ID='...'
             export DRYAD_CLIENT_SECRET='...'

    NEVER commit these to Git. They are credentials. This script only ever
    reads them from the environment, and never writes them to any file --
    including the manifest.

    "OAuth client credentials grant" is the standard way a program (as opposed
    to a person) authenticates: you trade a long-lived id+secret for a
    short-lived token, so the token can leak with limited consequence. Dryad's
    tokens last about 10 hours.
    """
    client_id = os.environ.get("DRYAD_CLIENT_ID")
    client_secret = os.environ.get("DRYAD_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None

    print("      requesting an access token from Dryad ...")
    resp = session.post(
        "https://datadryad.org/oauth/token",
        data={"client_id": client_id,
              "client_secret": client_secret,
              "grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                 "User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Dryad rejected the API credentials (HTTP {resp.status_code}).\n"
            f"  {resp.text[:300]}\n"
            "Check DRYAD_CLIENT_ID and DRYAD_CLIENT_SECRET."
        )
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in Dryad's reply: {resp.text[:300]}")
    print("      token obtained (valid ~10 hours)")
    return token


def encode_doi(doi: str) -> str:
    """
    Turn '10.5061/dryad.n2z34tn5s' into 'doi%3A10.5061%2Fdryad.n2z34tn5s'.

    Why: the DOI has to be embedded *inside* a URL path. But ':' and '/' are
    structural characters in a URL -- a raw '/' would look like a new path
    segment. "Percent-encoding" replaces them with %3A and %2F so the server
    receives them as literal text.
    """
    return f"doi:{doi}".replace(":", "%3A").replace("/", "%2F")


def human_size(num_bytes: int | None) -> str:
    """Render a byte count as something a human can read (e.g. '1.4 GB')."""
    if num_bytes is None:
        return "unknown size"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} TB"


def get_json(url: str, session: requests.Session) -> dict:
    """
    Fetch a URL and parse the reply as JSON, retrying on transient failures.

    'Transient' means a problem likely to fix itself: a dropped connection, a
    server briefly overloaded (HTTP 5xx), or rate limiting (429). We do NOT
    retry 403/404 -- those mean "you are not allowed" or "does not exist", and
    retrying would just be noise.
    """
    delay = 2
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (403, 404, 410):
                raise RuntimeError(
                    f"Server refused or could not find this resource.\n"
                    f"  URL:    {url}\n"
                    f"  Status: {resp.status_code}\n"
                    f"  Body:   {resp.text[:400]}"
                )
            resp.raise_for_status()   # turns 5xx/4xx into a Python exception
            return resp.json()
        except RuntimeError:
            raise                      # permanent error -- do not retry
        except Exception as exc:       # noqa: BLE001 - deliberately broad
            last_error = exc
            if attempt == MAX_RETRIES:
                break
            print(f"    attempt {attempt}/{MAX_RETRIES} failed ({exc.__class__.__name__}); "
                  f"retrying in {delay}s ...")
            time.sleep(delay)
            delay *= 2                 # exponential backoff: 2s, 4s, 8s
    raise RuntimeError(f"Gave up fetching {url} after {MAX_RETRIES} attempts: {last_error}")


# Dryad reports which algorithm it used in the file record's "digestType".
# Map its spelling onto Python's hashlib names. Dryad currently uses sha-256
# for this deposit, but older deposits use md5, so support both.
DIGEST_ALGOS = {
    "md5": "md5",
    "sha-1": "sha1", "sha1": "sha1",
    "sha-256": "sha256", "sha256": "sha256",
    "sha-512": "sha512", "sha512": "sha512",
}


def hash_file(path: Path, algo: str) -> str:
    """
    Compute a file's fingerprint with the named algorithm, streaming it.

    "Streaming" means reading the file a megabyte at a time instead of loading
    all 400 MB into memory at once.
    """
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# TALKING TO DRYAD
# ---------------------------------------------------------------------------

def fetch_dataset_record(session: requests.Session) -> dict:
    """Get the top-level metadata record for our DOI (title, authors, etc.)."""
    url = f"{DRYAD_API}/datasets/{encode_doi(DATASET_DOI)}"
    print(f"[1/4] Looking up dataset record\n      {url}")
    return get_json(url, session)


def fetch_file_list(dataset: dict, session: requests.Session) -> tuple[list[dict], str]:
    """
    Get the list of files in the dataset's most recent published version.

    Dryad's data model has three layers:
        dataset  ->  version (v1, v2, ...)  ->  files
    A dataset can be revised, so we must record WHICH version we downloaded.
    The dataset record contains a link to its current version; that version
    has a '/files' endpoint listing its contents, one page at a time.
    """
    version_href = (
        dataset.get("_links", {})
        .get("stash:version", {})
        .get("href")
    )
    if not version_href:
        raise RuntimeError(
            "Dryad's reply did not contain a link to a dataset version. "
            "The API may have changed shape. Raw reply keys: "
            f"{sorted(dataset.keys())}"
        )

    version_url = f"https://datadryad.org{version_href}"
    print(f"[2/4] Reading version record\n      {version_url}")
    version = get_json(version_url, session)
    version_number = str(version.get("versionNumber", "unknown"))

    files: list[dict] = []
    page = 1
    while True:
        page_url = f"{version_url}/files?page={page}&per_page=100"
        payload = get_json(page_url, session)
        batch = payload.get("_embedded", {}).get("stash:files", [])
        if not batch:
            break
        files.extend(batch)
        # 'total' is how many files exist overall; stop once we have them all.
        total = payload.get("total")
        if total is not None and len(files) >= total:
            break
        page += 1
        if page > 200:      # safety valve against an infinite loop
            print("      warning: stopped paging at 200 pages")
            break

    print(f"      version {version_number}: {len(files)} file(s) listed")
    return files, version_number


def download_one(file_rec: dict, outdir: Path, session: requests.Session,
                 force: bool, token: str | None = None,
                 known_files: set[str] | None = None) -> dict:
    """
    Download a single file and verify it. Returns a manifest entry.

    Verification logic:
      - If Dryad tells us an MD5 checksum, we recompute it locally and compare.
        A match proves the file is byte-identical to Dryad's copy.
      - If Dryad gives no checksum, we fall back to comparing file size, and we
        say so honestly in the manifest rather than pretending we verified.
    """
    name = file_rec.get("path") or file_rec.get("filename") or "unnamed_file"
    expected_size = file_rec.get("size")
    digest = file_rec.get("digest")
    digest_type = (file_rec.get("digestType") or "").lower()

    # Dryad exposes two different download routes and only one is public:
    #   /api/v2/files/<id>/download   -> 401, needs a logged-in bearer token
    #   /downloads/file_stream/<id>   -> public, what the website itself uses
    # The API's link relations point at the first, so we take the numeric file
    # id from them and build the public URL ourselves.
    links = file_rec.get("_links", {})
    href = None
    for key in ("stash:download", "stash:file-download", "self"):
        href = links.get(key, {}).get("href")
        if href:
            break
    if not href:
        raise RuntimeError(
            f"No link of any known kind for '{name}'. "
            f"Link keys present: {sorted(links)}"
        )
    match = re.search(r"/files/(\d+)", href)
    file_id = match.group(1) if match else None
    if token and file_id:
        # Authenticated route -- not behind the anti-bot challenge.
        url = f"https://datadryad.org/api/v2/files/{file_id}/download"
    elif file_id:
        url = f"https://datadryad.org/downloads/file_stream/{file_id}"
    else:
        url = f"https://datadryad.org{href}"

    headers = dict(DOWNLOAD_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    dest = outdir / name
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Refuse to overwrite a file this script did not put here. Dryad's deposit
    # contains its own README.md, and blindly writing it would destroy an
    # unrelated file of the same name -- exactly the kind of silent data loss
    # data/raw is meant to be protected from.
    if dest.exists() and known_files is not None and name not in known_files:
        raise RuntimeError(
            f"'{name}' already exists in {outdir} but is not recorded in a "
            f"previous download manifest, so this script did not create it.\n"
            f"Refusing to overwrite it. Move or rename {dest} and re-run."
        )

    # Skip work we have already done, unless --force was passed.
    if dest.exists() and not force:
        if expected_size is None or dest.stat().st_size == expected_size:
            print(f"    already present, skipping: {name}")
            return _manifest_entry(name, dest, url, expected_size,
                                   digest, digest_type, skipped=True)

    print(f"    downloading {name}  ({human_size(expected_size)})")

    # Download to a temporary '.part' name first. If the transfer dies halfway,
    # we are left with an obviously-incomplete '.part' file rather than a
    # corrupt file that looks finished. Only on success do we rename it.
    tmp = dest.with_suffix(dest.suffix + ".part")
    delay = 2
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with session.get(url, headers=headers, stream=True,
                             timeout=REQUEST_TIMEOUT) as resp:
                resp.raise_for_status()
                written = 0
                with tmp.open("wb") as fh:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        written += len(chunk)
                        if expected_size:
                            pct = 100 * written / expected_size
                            print(f"\r      {pct:5.1f}%  "
                                  f"({human_size(written)})", end="", flush=True)
                print()
            break
        except Exception as exc:      # noqa: BLE001
            tmp.unlink(missing_ok=True)
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Failed to download {name}: {exc}") from exc
            print(f"\n      transfer failed ({exc.__class__.__name__}); "
                  f"retrying in {delay}s ...")
            time.sleep(delay)
            delay *= 2

    tmp.rename(dest)

    # ---- verification -----------------------------------------------------
    actual_size = dest.stat().st_size

    # A very common failure is receiving an HTML page (an anti-bot challenge or
    # an error page) instead of the file. Detect that and explain it, rather
    # than reporting a bare size mismatch the reader cannot act on.
    with dest.open("rb") as fh:
        head = fh.read(512).lstrip()[:64].lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        dest.unlink(missing_ok=True)
        raise RuntimeError(
            f"Dryad returned a web page instead of '{name}'.\n"
            "This is Dryad's anti-bot challenge: the public download route\n"
            "requires a browser that can run JavaScript, so a script cannot\n"
            "use it. Use Dryad's supported route for programs instead --\n"
            "an API account:\n"
            "  1. Sign in at https://datadryad.org with your ORCID iD\n"
            "  2. My account -> create an API account\n"
            "  3. export DRYAD_CLIENT_ID='...' DRYAD_CLIENT_SECRET='...'\n"
            "  4. re-run this script\n"
            "(The partial file has been deleted, so nothing invalid is left behind.)"
        )

    if expected_size is not None and actual_size != expected_size:
        raise RuntimeError(
            f"Size mismatch for {name}: Dryad said {expected_size:,} bytes, "
            f"we got {actual_size:,}. The download is incomplete."
        )

    verified = "size-only"
    algo = DIGEST_ALGOS.get(digest_type)
    if digest and algo:
        print(f"      verifying {algo} checksum ...")
        actual = hash_file(dest, algo)
        if actual.lower() != digest.lower():
            raise RuntimeError(
                f"CHECKSUM MISMATCH for {name}.\n"
                f"  Dryad expected ({algo}): {digest}\n"
                f"  We computed:             {actual}\n"
                "The file is corrupted. Delete it and re-run this script."
            )
        verified = algo
        print(f"      checksum OK ({algo} {actual[:16]}...)")
    elif digest:
        print(f"      note: unrecognised digest type '{digest_type}'; "
              f"verified by size only.")
    else:
        print("      note: Dryad supplied no checksum; verified by size only.")

    return _manifest_entry(name, dest, url, expected_size, digest,
                           digest_type, verified=verified)


def _manifest_entry(name, dest, url, expected_size, digest, digest_type,
                    skipped=False, verified="size-only") -> dict:
    """Build one row of the provenance manifest."""
    return {
        "filename": name,
        "local_path": str(dest.relative_to(dest.parent.parent.parent))
                      if dest.is_absolute() else str(dest),
        "bytes": dest.stat().st_size if dest.exists() else None,
        "dryad_reported_bytes": expected_size,
        "dryad_digest": digest,
        "dryad_digest_type": digest_type or None,
        "verification": "pre-existing" if skipped else verified,
        "source_url": url,
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list-only", action="store_true",
                        help="show the file list without downloading")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR,
                        help=f"destination folder (default: {DEFAULT_OUTDIR})")
    parser.add_argument("--force", action="store_true",
                        help="re-download files that already exist")
    args = parser.parse_args()

    print("=" * 72)
    print("Dryad dataset download")
    print(f"  DOI:         {DATASET_DOI}")
    print(f"  Landing page https://doi.org/{DATASET_DOI}")
    print(f"  Destination: {args.outdir}")
    print("=" * 72)

    session = requests.Session()

    token = get_access_token(session)
    if token is None:
        print("      no DRYAD_CLIENT_ID / DRYAD_CLIENT_SECRET set;\n"
              "      will try the public route (may hit Dryad's anti-bot check)")

    dataset = fetch_dataset_record(session)
    title = dataset.get("title", "(no title returned)")
    authors = ", ".join(
        f"{a.get('firstName','')} {a.get('lastName','')}".strip()
        for a in dataset.get("authors", [])
    ) or "(none listed)"
    print(f"      title:   {title}")
    print(f"      authors: {authors}")

    files, version_number = fetch_file_list(dataset, session)

    total_bytes = sum(f.get("size") or 0 for f in files)
    print(f"\n[3/4] Files in this version (total {human_size(total_bytes)}):")
    for f in files:
        print(f"      - {f.get('path'):<50s} {human_size(f.get('size'))}"
              f"   [{f.get('mimeType','?')}]")

    if args.list_only:
        print("\n--list-only given; nothing downloaded.")
        return 0

    args.outdir.mkdir(parents=True, exist_ok=True)
    print(f"\n[4/4] Downloading into {args.outdir}")
    # Filenames recorded by a previous run of this script -- safe to overwrite.
    manifest_path = args.outdir / "download_manifest.json"
    known_files: set[str] = set()
    if manifest_path.exists():
        try:
            prev = json.loads(manifest_path.read_text())
            known_files = {e["filename"] for e in prev.get("files", [])}
        except (ValueError, KeyError):
            pass

    entries = [download_one(f, args.outdir, session, args.force,
                            token=token, known_files=known_files)
               for f in files]

    manifest = {
        "dataset_doi": DATASET_DOI,
        "dataset_doi_url": f"https://doi.org/{DATASET_DOI}",
        "dryad_landing_page": f"https://datadryad.org/dataset/doi:{DATASET_DOI}",
        "dataset_title": title,
        "dataset_authors": authors,
        "dryad_version_number": version_number,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "downloaded_by_script": "scripts/01_download_dataset.py",
        "api_base": DRYAD_API,
        "n_files": len(entries),
        "total_bytes": sum(e["bytes"] or 0 for e in entries),
        "files": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print("\n" + "=" * 72)
    print(f"Done. {len(entries)} file(s) in {args.outdir}")
    print(f"Provenance record written to {manifest_path}")
    print("Do NOT edit anything in data/raw/. Treat it as read-only.")
    print("Next step:  python3 scripts/02_inspect_dataset.py")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as err:
        # A clean, readable failure beats a wall of traceback.
        print(f"\nERROR: {err}", file=sys.stderr)
        sys.exit(1)
