import csv
import json
from collections import Counter
from pathlib import Path

from src.models.schema import TABLES
from src.utils.core import checksum, json_text


class ChunkWriter:
    """Bounded-size files; no fact-table accumulation in Python."""
    def __init__(self, folder, name, fields=None, chunk_rows=100000, jsonl=False):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.name, self.fields, self.chunk_rows, self.jsonl = name, fields, chunk_rows, jsonl
        self.total = self.part_rows = self.part = 0
        self.handle = self.writer = None

    def _open(self):
        self.part += 1
        suffix = "" if self.part == 1 else f".part{self.part:05d}"
        extension = "jsonl" if self.jsonl else "csv"
        self.handle = (self.folder / f"{self.name}{suffix}.{extension}").open("w", encoding="utf-8", newline="")
        if not self.jsonl:
            self.writer = csv.DictWriter(self.handle, fieldnames=self.fields, lineterminator="\n", extrasaction="raise")
            self.writer.writeheader()
        self.part_rows = 0

    def write(self, row):
        if self.handle is None or self.part_rows >= self.chunk_rows:
            if self.handle:
                self.handle.close()
            self._open()
        if self.jsonl:
            self.handle.write(json_text(row) + "\n")
        else:
            self.writer.writerow({k: json_text(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
        self.total += 1
        self.part_rows += 1

    def close(self):
        # Empty tables still expose their schema/header (empty JSONL is zero bytes).
        if self.handle is None:
            self._open()
        self.handle.close()


class CanonicalSink:
    def __init__(self, root, chunk_rows):
        self.root = Path(root)
        self.writers = {name: ChunkWriter(self.root / "reference" / "canonical", name,
                        [c.name for c in table.columns], chunk_rows, name == "web_events")
                        for name, table in TABLES.items()}
        self.ids = Counter()

    def next_id(self, table):
        self.ids[table] += 1
        return self.ids[table]

    def emit(self, table, row):
        expected = {c.name for c in TABLES[table].columns}
        if set(row) != expected:
            raise ValueError(f"{table} field mismatch: {set(row) ^ expected}")
        self.writers[table].write(row)

    def close(self):
        for writer in self.writers.values():
            writer.close()

    @property
    def counts(self):
        return {name: writer.total for name, writer in self.writers.items()}


def table_files(folder, table):
    extension = "jsonl" if table == "web_events" else "csv"
    path = Path(folder)
    first = path / f"{table}.{extension}"
    return ([first] if first.exists() else []) + sorted(path.glob(f"{table}.part*.{extension}"))


def read_table(folder, name, typed=True):
    columns = TABLES[name].columns
    for path in table_files(folder, name):
        with path.open(encoding="utf-8", newline="") as handle:
            rows = (json.loads(line) for line in handle if line.strip()) if name == "web_events" else csv.DictReader(handle)
            for row in rows:
                if typed and name != "web_events":
                    for col in columns:
                        if row[col.name] == "":
                            row[col.name] = None
                        elif col.kind in {"id", "money", "int", "bool"}:
                            row[col.name] = int(row[col.name])
                        elif col.kind == "json":
                            row[col.name] = json.loads(row[col.name])
                yield row


def file_manifest(root):
    result = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and path.suffix in {".csv", ".jsonl"}:
            with path.open(encoding="utf-8", newline="") as handle:
                count = sum(1 for _ in handle) if path.suffix == ".jsonl" else sum(1 for _ in csv.reader(handle)) - 1
            result.append(dict(path=path.relative_to(root).as_posix(), rows=count,
                               bytes=path.stat().st_size, sha256=checksum(path)))
    return result
