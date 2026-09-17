# Getting the Track 2 data

Nothing in `data/` is committed except this README and `checksums.txt`. The source
data's licence (CC BY-NC-ND 4.0, see `ATTRIBUTION.md`) forbids redistributing anything
derived from it, so you download the source files and generate the rest on your own
machine. It takes about a minute.

## 1. Download the raw data

A 9.3 MB download, 88 MB unpacked. From `track-2/`:

```bash
curl -O https://mantisgrid-hackathon.s3.us-east-1.amazonaws.com/track-2-raw.zip
unzip track-2-raw.zip -d data/raw
```

(Or open the link in a browser and unzip the file into `track-2/data/raw/`.) You end up
with:

```
data/raw/scheduler_data.csv     the Slurm scheduler's record of every job
data/raw/dcgm.csv               per-GPU utilization for each job
data/raw/README.md              MIT's description of the data, and its terms of use
data/raw/LICENSE                CC BY-NC-ND 4.0
```

These are MIT SuperCloud's files, unchanged.

## 2. Prepare the tables

```bash
docker compose run --rm prep
```

This writes `data/prepped/jobs.parquet` and `data/prepped/gpus.parquet`. It runs in
the same pinned image as the API, so your tables are identical to everyone else's.
(`python scripts/prep_data.py` works too, from this directory, with the packages in
`requirements.lock.txt`.)

## 3. Generate the findings

```bash
make generate
```

This runs our generator in Docker, like step 2. It reads `data/prepped/` and writes
`data/synthetic/findings.json`, `resources.parquet` and `edges.parquet` in a few
seconds. The generator is in `bin/`, built for Linux on Intel and on ARM; Docker picks
the one for your machine. `bin/SHA256SUMS` lists their hashes.

Without `make` (Windows, usually): `docker compose run --rm generate`

## 4. Check it matches

```bash
make check-data
```

This compares your five files against `data/checksums.txt` and prints `ok` or
`MISMATCH` for each:

```
  ok        data/prepped/jobs.parquet
  ok        data/prepped/gpus.parquet
  ok        data/synthetic/resources.parquet
  ok        data/synthetic/edges.parquet
  ok        data/synthetic/findings.json

Your data matches.
```

If something doesn't match, it tells you which step to redo. When the tables from
step 2 differ, everything after them will too, so fix step 2 first.

**Why not just hash the files?** You can for `findings.json`: it comes out byte-for-byte
the same on every machine, so its SHA-256 (`shasum -a 256 data/synthetic/findings.json`,
or `certutil -hashfile data\synthetic\findings.json SHA256` on Windows) must equal the
last line of `data/checksums.txt`. The `.parquet` files are different: the same data is
compressed slightly differently on Intel and ARM machines, so their bytes, and a hash of
the bytes, differ even when every value is identical. For those, `make check-data` hashes
the values inside the file instead (`scripts/checksum_data.py`). It needs no Python
of your own: it runs in the same container as step 2.

If your data doesn't match, the API will still run, but your findings will differ from the
ones everyone else, and the judges, are looking at.

## 5. Start

```bash
docker compose up        # API on :8000, notebooks on :8888
```
