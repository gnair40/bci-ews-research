#!/usr/bin/env python3
"""
02_inspect_dataset.py
=====================
Take an inventory of whatever is inside data/raw/ -- without changing anything.

WHAT THIS SCRIPT IS FOR
-----------------------
Before analysing data you must know what the data *are*. Not what a paper says
they are, and not what a filename implies -- what is literally on disk. This
script opens every file it can and reports:

    * the folder/file structure and how deep it nests
    * file types and sizes
    * for each MATLAB .mat file: every variable, its shape, and its data type
    * for each table (.csv/.tsv): rows, columns, dtypes, missing values
    * numeric summaries (min/max/mean) so obviously-wrong values stand out
    * how many participants / sessions / blocks the folder names imply

It writes a machine-readable inventory to  reports/inventory.json  and prints a
human-readable summary. It NEVER writes into data/raw/.

WHY "SHAPE" AND "DTYPE" MATTER
------------------------------
  shape   The dimensions of an array, written (rows, columns). A neural
          recording of shape (180000, 192) means 180,000 time points measured
          on 192 channels. Reading that one number tells you the sampling
          resolution and the array size immediately.
  dtype   "Data type" -- how each number is stored. float64 = a decimal number
          using 8 bytes; int16 = a whole number using 2 bytes; bool = true/false.
          It matters because e.g. integer-typed "spike counts" and float-typed
          "spike band power" are different measurements.

A NOTE ON .mat FILES
--------------------
MATLAB has two incompatible save formats and you cannot tell which one you have
from the filename:
  * v7 and earlier  -> read with scipy.io.loadmat
  * v7.3 and later  -> actually HDF5 files; scipy cannot read them, h5py can
This script tries scipy first and automatically falls back to h5py, so you do
not have to care which one Dryad used.

HOW TO RUN
----------
    python3 scripts/02_inspect_dataset.py
    python3 scripts/02_inspect_dataset.py --extract     # unzip archives first
    python3 scripts/02_inspect_dataset.py --max-files 20

REQUIREMENTS
------------
    pip install numpy pandas scipy h5py
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import scipy.io as sio
except ImportError:
    sio = None
try:
    import h5py
except ImportError:
    h5py = None


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
REPORT_DIR = REPO_ROOT / "reports"

# Files that are bookkeeping, not data.
IGNORE_NAMES = {".gitkeep", "download_manifest.json", ".DS_Store"}


# ---------------------------------------------------------------------------
# GENERIC HELPERS
# ---------------------------------------------------------------------------

def human_size(n: int | None) -> str:
    if n is None:
        return "?"
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} TB"


def describe_array(arr) -> dict:
    """
    Summarise a numeric array: shape, dtype, missing values, range.

    'NaN' means "Not a Number" -- the standard marker for a missing value in
    floating-point data. Counting NaNs is how you find missing data in arrays
    that have no explicit "null" concept.
    """
    out: dict = {}
    try:
        a = np.asarray(arr)
    except Exception:                       # noqa: BLE001
        return {"note": "could not convert to array"}

    out["shape"] = list(a.shape)
    out["dtype"] = str(a.dtype)
    out["n_elements"] = int(a.size)

    if a.size == 0:
        out["note"] = "empty"
        return out

    if np.issubdtype(a.dtype, np.number):
        finite = a[np.isfinite(a)] if np.issubdtype(a.dtype, np.floating) else a
        n_nan = int(np.count_nonzero(~np.isfinite(a))) if np.issubdtype(a.dtype, np.floating) else 0
        out["n_nan_or_inf"] = n_nan
        out["pct_nan_or_inf"] = round(100 * n_nan / a.size, 4)
        if finite.size:
            out["min"] = float(np.min(finite))
            out["max"] = float(np.max(finite))
            out["mean"] = float(np.mean(finite))
            out["std"] = float(np.std(finite))
        # A small number of distinct values usually means a label/category,
        # not a continuous measurement. Worth flagging.
        if finite.size and finite.size <= 5_000_000:
            uniq = np.unique(finite)
            if uniq.size <= 12:
                out["unique_values"] = [float(u) for u in uniq]
                out["looks_categorical"] = True
    elif a.dtype == bool:
        out["n_true"] = int(np.count_nonzero(a))
        out["n_false"] = int(a.size - np.count_nonzero(a))
    else:
        out["note"] = "non-numeric array"
        flat = a.ravel()[:5]
        out["sample_values"] = [str(v)[:80] for v in flat]
    return out


# ---------------------------------------------------------------------------
# .mat READERS
# ---------------------------------------------------------------------------

def inspect_mat_scipy(path: Path) -> dict | None:
    """Read a pre-v7.3 .mat file. Returns None if this is the wrong format."""
    if sio is None:
        return None
    try:
        # squeeze_me/struct_as_record make MATLAB structs come back as objects
        # that are easier to walk than raw record arrays.
        md = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
    except NotImplementedError:
        return None                 # this is the "it's v7.3" signal
    except Exception as exc:        # noqa: BLE001
        return {"error": f"scipy.io.loadmat failed: {exc}"}

    variables = {}
    for key, val in md.items():
        if key.startswith("__"):    # __header__, __version__, __globals__
            continue
        variables[key] = summarise_matlab_value(val)
    return {"mat_format": "v7 or earlier (scipy.io)", "variables": variables}


def summarise_matlab_value(val, depth: int = 0) -> dict:
    """Recursively describe a value loaded from a .mat file."""
    if depth > 3:
        return {"note": "nesting deeper than 3 levels; not expanded"}

    # A MATLAB struct comes back from scipy as an object with _fieldnames.
    if hasattr(val, "_fieldnames"):
        return {
            "kind": "struct",
            "fields": {
                f: summarise_matlab_value(getattr(val, f), depth + 1)
                for f in val._fieldnames
            },
        }
    if isinstance(val, np.ndarray) and val.dtype == object:
        entry = {"kind": "cell/object array", "shape": list(val.shape)}
        if val.size:
            entry["first_element"] = summarise_matlab_value(val.ravel()[0], depth + 1)
        return entry
    if isinstance(val, (str, bytes)):
        return {"kind": "string", "value": str(val)[:200]}
    if isinstance(val, (int, float, np.number)):
        return {"kind": "scalar", "value": float(val)}
    entry = {"kind": "array"}
    entry.update(describe_array(val))
    return entry


def inspect_mat_h5py(path: Path) -> dict:
    """Read a v7.3 .mat file, which is really an HDF5 file."""
    if h5py is None:
        return {"error": "h5py not installed; cannot read v7.3 .mat files"}
    try:
        variables: dict = {}
        with h5py.File(path, "r") as f:
            def walk(name, obj):
                if name.startswith("#"):    # MATLAB internal refs
                    return
                if isinstance(obj, h5py.Dataset):
                    d = {"kind": "dataset", "shape": list(obj.shape),
                         "dtype": str(obj.dtype)}
                    # Only load small datasets fully; big ones we sample.
                    try:
                        if obj.size and obj.size <= 5_000_000:
                            d.update(describe_array(obj[()]))
                        elif obj.size:
                            d["note"] = "large; summarised from first 100k values"
                            d.update(describe_array(np.asarray(obj).ravel()[:100_000]))
                    except Exception as exc:          # noqa: BLE001
                        d["read_error"] = str(exc)[:200]
                    variables[name] = d
                elif isinstance(obj, h5py.Group):
                    variables[name] = {"kind": "group",
                                       "members": list(obj.keys())[:50]}
            f.visititems(walk)
        return {"mat_format": "v7.3 (HDF5, read with h5py)", "variables": variables}
    except Exception as exc:                          # noqa: BLE001
        return {"error": f"h5py failed: {exc}"}


def is_hdf5(path: Path) -> bool:
    """
    Detect a v7.3 .mat file by its 'magic bytes'.

    Nearly every binary format starts with a fixed signature so programs can
    identify it without trusting the filename. HDF5 files always begin with
    the 8 bytes  \x89 H D F \r \n \x1a \n.  Checking this is far more
    reliable than guessing from which error scipy happens to raise.
    """
    try:
        with path.open("rb") as fh:
            return fh.read(8) == b"\x89HDF\r\n\x1a\n"
    except OSError:
        return False


def inspect_mat(path: Path) -> dict:
    """
    Read a .mat file in whichever of the two MATLAB formats it actually is.

    Order of operations:
      1. If the magic bytes say HDF5, it is v7.3 -> go straight to h5py.
      2. Otherwise try scipy (v7 and earlier).
      3. If scipy fails for ANY reason, try h5py anyway before giving up, and
         if that also fails report BOTH errors so the cause is diagnosable.
    """
    if is_hdf5(path):
        return inspect_mat_h5py(path)

    result = inspect_mat_scipy(path)
    if result is not None and "error" not in result:
        return result

    fallback = inspect_mat_h5py(path)
    if "error" not in fallback:
        return fallback

    return {
        "error": "could not read as either MATLAB format",
        "scipy_error": (result or {}).get("error", "returned no result"),
        "h5py_error": fallback.get("error"),
    }


# ---------------------------------------------------------------------------
# TABLE READER
# ---------------------------------------------------------------------------

def inspect_table(path: Path, sep: str) -> dict:
    """
    Describe a CSV/TSV: shape, column names, dtypes, missingness, uniqueness.

    'Missingness' is the fraction of blank cells per column. It matters because
    a column that is 95% empty cannot support an analysis no matter how
    promising its name sounds.
    """
    if pd is None:
        return {"error": "pandas not installed"}
    try:
        df = pd.read_csv(path, sep=sep, low_memory=False)
    except Exception as exc:                          # noqa: BLE001
        return {"error": f"pandas failed to read: {exc}"}

    cols = {}
    for c in df.columns:
        s = df[c]
        info = {
            "dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(100 * float(s.isna().mean()), 3),
            "n_unique": int(s.nunique(dropna=True)),
        }
        # A column whose every value is distinct is probably an identifier.
        if info["n_unique"] == len(df) and len(df) > 1:
            info["candidate_unique_identifier"] = True
        if pd.api.types.is_numeric_dtype(s):
            info.update({
                "min": None if s.dropna().empty else float(s.min()),
                "max": None if s.dropna().empty else float(s.max()),
                "mean": None if s.dropna().empty else float(s.mean()),
            })
        else:
            info["example_values"] = [str(v)[:60] for v in
                                      s.dropna().unique()[:5]]
        cols[str(c)] = info

    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": cols,
        "head": df.head(3).to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# ARCHIVES
# ---------------------------------------------------------------------------

def inspect_zip(path: Path) -> dict:
    """List a zip's contents WITHOUT unpacking it."""
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            return {
                "n_entries": len(names),
                "uncompressed_bytes": sum(i.file_size for i in z.infolist()),
                "extension_counts": dict(Counter(
                    Path(n).suffix.lower() or "(no extension)"
                    for n in names if not n.endswith("/")
                )),
                "first_entries": names[:40],
            }
    except Exception as exc:                          # noqa: BLE001
        return {"error": f"could not read zip: {exc}"}


def extract_archives(raw_dir: Path) -> list[str]:
    """
    Unpack any .zip into data/raw/extracted/<zipname>/.

    The original .zip is left untouched -- extracting is additive, so the raw
    download stays pristine and re-runnable.
    """
    out = []
    dest_root = raw_dir / "extracted"
    for z in sorted(raw_dir.glob("*.zip")):
        dest = dest_root / z.stem
        if dest.exists():
            print(f"    already extracted: {z.name}")
            out.append(str(dest))
            continue
        dest.mkdir(parents=True, exist_ok=True)
        print(f"    extracting {z.name} -> {dest}")
        with zipfile.ZipFile(z) as zf:
            zf.extractall(dest)
        out.append(str(dest))
    return out


# ---------------------------------------------------------------------------
# STRUCTURE INFERENCE
# ---------------------------------------------------------------------------

def infer_structure(raw_dir: Path) -> dict:
    """
    Guess the organisational hierarchy from folder names.

    This is INFERENCE, not fact -- it reads folder names like 'T5', 'day_37',
    'block_2' and reports what they imply. Every conclusion here must be
    confirmed against the dataset's own documentation before you rely on it.
    """
    participants: set[str] = set()
    days: dict[str, set[int]] = defaultdict(set)
    blocks: dict[str, set[str]] = defaultdict(set)
    depths: Counter = Counter()

    for p in raw_dir.rglob("*"):
        rel = p.relative_to(raw_dir)
        if p.is_dir():
            depths[len(rel.parts)] += 1
            name = p.name
            # Participant identifiers in BrainGate data look like T5, T11.
            if len(name) <= 4 and name.startswith("T") and name[1:].isdigit():
                participants.add(name)
            if name.lower().startswith("day_"):
                parent_ps = [q for q in rel.parts if q in participants]
                key = parent_ps[0] if parent_ps else "(unknown)"
                try:
                    days[key].add(int(name.split("_", 1)[1]))
                except ValueError:
                    pass
            if name.lower().startswith("block"):
                parts = [q for q in rel.parts if q.lower().startswith("day_")]
                key = "/".join(rel.parts[:-1]) if parts else str(rel.parent)
                blocks[key].add(name)

    return {
        "participants_detected": sorted(participants),
        "days_per_participant": {k: sorted(v) for k, v in days.items()},
        "n_days_per_participant": {k: len(v) for k, v in days.items()},
        "n_block_folders_total": sum(len(v) for v in blocks.values()),
        "directory_depth_counts": dict(depths),
        "caveat": ("Derived from folder NAMES only. Confirm against the "
                   "dataset's official README before treating as fact."),
    }


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    ap.add_argument("--extract", action="store_true",
                    help="unpack .zip archives into data/raw/extracted/ first")
    ap.add_argument("--max-files", type=int, default=60,
                    help="how many data files to open in detail (default 60)")
    args = ap.parse_args()

    raw_dir: Path = args.raw_dir
    if not raw_dir.exists():
        print(f"ERROR: {raw_dir} does not exist.", file=sys.stderr)
        return 1

    all_paths = [p for p in sorted(raw_dir.rglob("*"))
                 if p.is_file() and p.name not in IGNORE_NAMES]
    if not all_paths:
        print("=" * 72)
        print(f"{raw_dir} contains no data files yet.")
        print("Run  python3 scripts/01_download_dataset.py  first.")
        print("=" * 72)
        return 1

    print("=" * 72)
    print(f"INVENTORY OF {raw_dir}")
    print("=" * 72)

    if args.extract:
        print("\nExtracting archives (originals are kept):")
        extract_archives(raw_dir)
        all_paths = [p for p in sorted(raw_dir.rglob("*"))
                     if p.is_file() and p.name not in IGNORE_NAMES]

    # ---- overview --------------------------------------------------------
    ext_counts = Counter(p.suffix.lower() or "(no extension)" for p in all_paths)
    total_bytes = sum(p.stat().st_size for p in all_paths)
    print(f"\nTotal files: {len(all_paths)}")
    print(f"Total size:  {human_size(total_bytes)}")
    print("\nFile types:")
    for ext, n in ext_counts.most_common():
        sz = sum(p.stat().st_size for p in all_paths if
                 (p.suffix.lower() or "(no extension)") == ext)
        print(f"  {ext:<20s} {n:>6d} file(s)   {human_size(sz)}")

    # ---- inferred hierarchy ---------------------------------------------
    structure = infer_structure(raw_dir)
    print("\nInferred organisation (from folder names -- MUST be confirmed):")
    print(f"  participants: {structure['participants_detected'] or '(none detected)'}")
    for k, v in structure["n_days_per_participant"].items():
        print(f"  {k}: {v} day/session folder(s)")
    print(f"  block folders: {structure['n_block_folders_total']}")

    # ---- per-file detail -------------------------------------------------
    # Prioritise formats that actually carry data.
    priority = {".mat": 0, ".csv": 1, ".tsv": 1, ".zip": 2,
                ".json": 3, ".txt": 4, ".md": 4, ".pdf": 5}
    to_open = sorted(all_paths,
                     key=lambda p: (priority.get(p.suffix.lower(), 9), str(p)))
    inspected = to_open[: args.max_files]

    print(f"\nOpening {len(inspected)} of {len(all_paths)} file(s) in detail "
          f"(raise with --max-files):")

    file_reports = {}
    for p in inspected:
        rel = str(p.relative_to(raw_dir))
        ext = p.suffix.lower()
        rec: dict = {"relative_path": rel, "bytes": p.stat().st_size,
                     "extension": ext}
        print(f"\n--- {rel}  ({human_size(p.stat().st_size)})")
        try:
            if ext == ".mat":
                rec["content"] = inspect_mat(p)
                content = rec["content"]
                if "variables" in content:
                    print(f"    format: {content.get('mat_format')}")
                    for vname, vinfo in content["variables"].items():
                        shape = vinfo.get("shape")
                        dtype = vinfo.get("dtype", vinfo.get("kind", "?"))
                        extra = ""
                        if vinfo.get("pct_nan_or_inf"):
                            extra = f"  NaN/Inf: {vinfo['pct_nan_or_inf']}%"
                        print(f"      {vname:<28s} shape={shape}  {dtype}{extra}")
                else:
                    print(f"    {content.get('error')}")
            elif ext in (".csv", ".tsv"):
                rec["content"] = inspect_table(p, "," if ext == ".csv" else "\t")
                c = rec["content"]
                if "n_rows" in c:
                    print(f"    {c['n_rows']:,} rows x {c['n_columns']} columns")
                    for cname, cinfo in list(c["columns"].items())[:25]:
                        flag = " [ID?]" if cinfo.get("candidate_unique_identifier") else ""
                        print(f"      {cname:<28s} {cinfo['dtype']:<10s} "
                              f"missing={cinfo['pct_missing']}%  "
                              f"unique={cinfo['n_unique']}{flag}")
                else:
                    print(f"    {c.get('error')}")
            elif ext == ".zip":
                rec["content"] = inspect_zip(p)
                c = rec["content"]
                print(f"    {c.get('n_entries')} entries, "
                      f"{human_size(c.get('uncompressed_bytes'))} uncompressed")
                print(f"    types inside: {c.get('extension_counts')}")
            elif ext in (".txt", ".md", ".json"):
                text = p.read_text(errors="replace")
                rec["content"] = {"n_chars": len(text),
                                  "first_2000_chars": text[:2000]}
                print(f"    text file, {len(text):,} characters. First lines:")
                for line in text.splitlines()[:8]:
                    print(f"      | {line[:100]}")
            else:
                rec["content"] = {"note": "not opened; unrecognised extension"}
                print("    (not opened -- unrecognised extension)")
        except Exception as exc:                       # noqa: BLE001
            rec["content"] = {"error": f"{exc.__class__.__name__}: {exc}"}
            print(f"    ERROR reading this file: {exc}")
        file_reports[rel] = rec

    # ---- write the machine-readable inventory ----------------------------
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/02_inspect_dataset.py",
        "raw_dir": str(raw_dir),
        "n_files_total": len(all_paths),
        "total_bytes": total_bytes,
        "extension_counts": dict(ext_counts),
        "inferred_structure": structure,
        "n_files_inspected": len(inspected),
        "files": file_reports,
    }
    out_path = REPORT_DIR / "inventory.json"
    out_path.write_text(json.dumps(inventory, indent=2, default=str))

    print("\n" + "=" * 72)
    print(f"Machine-readable inventory written to {out_path}")
    print("data/raw/ was NOT modified.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
