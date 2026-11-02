from datetime import timedelta

from src.exporters.files import ChunkWriter
from src.models.schema import TABLES
from src.utils.core import CUTOFF, rng, stamp


class CDCWriter:
    """Full after-images, ordered per key by source_version, bounded arrival buffer."""
    def __init__(self, root, settings):
        self.random = rng(settings.seed, "cdc_transport")
        self.writer = ChunkWriter(root / "cdc", "changes", chunk_rows=settings.chunk_rows, jsonl=True)
        self.buffer = []

    def history(self, table, final, states):
        """states: [(business_time, changed_fields, reason), ...]. No invented updates."""
        business_key = final[TABLES[table].pk]
        states = sorted(states, key=lambda x: x[0])
        for version, (when, fields, reason) in enumerate(states, 1):
            if when > CUTOFF:
                continue
            payload = dict(final, **fields)
            change_id = f"{table}:{business_key}:{version}"
            event = dict(change_id=change_id, table=table, business_key=business_key,
                         operation="INSERT" if version == 1 else "UPDATE", source_version=version,
                         changed_at=stamp(when), ingested_at=stamp(when + timedelta(seconds=self.random.randint(5, 600))),
                         reason=reason, payload=payload)
            if self.random.random() < 0.025:
                event["ingested_at"] = stamp(when + timedelta(days=3, seconds=version))
            self.buffer.append(event)
            if self.random.random() < 0.012:
                self.buffer.append(dict(event, ingested_at=stamp(when + timedelta(days=5))))
            if len(self.buffer) >= 128:
                self.flush()

    def flush(self):
        # Export arrival order is intentionally unordered. Version is authoritative.
        self.random.shuffle(self.buffer)
        for event in self.buffer:
            self.writer.write(event)
        self.buffer.clear()

    def close(self):
        self.flush()
        self.writer.close()
