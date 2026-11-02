import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
VN = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")
START = datetime(2024, 1, 1, tzinfo=VN).astimezone(UTC)
END = datetime(2026, 1, 1, tzinfo=VN).astimezone(UTC)
CUTOFF = END - timedelta(seconds=1)


def rng(seed, name):
    digest = hashlib.sha256(f"vietcommerce:v1:{seed}:{name}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def stamp(value):
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


def parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def local_date(value):
    return value.astimezone(VN).date()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def checksum(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def incident(settings, name, when):
    start, end = settings.incidents[name]
    return start <= str(local_date(when)) <= end
