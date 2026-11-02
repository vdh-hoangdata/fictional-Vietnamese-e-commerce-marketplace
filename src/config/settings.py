from dataclasses import dataclass, field
from pathlib import Path
import json

PRESETS = {
    "small": dict(orders=5000, customers=1400, products=240, sellers=18),
    "medium": dict(orders=100000, customers=20000, products=3000, sellers=100),
    "large": dict(orders=1000000, customers=200000, products=30000, sellers=1000),
}
DEFAULT_INCIDENTS = {
    "payment_outage": ["2024-08-12", "2024-08-16"],
    "carrier_disruption": ["2025-07-07", "2025-07-20"],
    "inventory_shortage": ["2025-03-01", "2025-03-14"],
    "margin_campaign": ["2025-11-01", "2025-11-15"],
    "quality_issue": ["2025-05-01", "2025-05-31"],
}


@dataclass
class Settings:
    size: str = "medium"
    seed: int = 42
    profile: str = "realistic"
    output: Path = Path("data")
    chunk_rows: int = 100000
    return_rate: float = 0.055
    cancellation_rate: float = 0.045
    payment_failure_rate: float = 0.085
    anonymous_sessions_per_order: float = 0.55
    incidents: dict = field(default_factory=lambda: dict(DEFAULT_INCIDENTS))
    keep_ground_truth: bool = False
    omit_reference: bool = False
    # Used by tests only; normal CLI volume is always the chosen preset.
    scale: dict | None = None

    @property
    def counts(self):
        return self.scale or PRESETS[self.size]

    def validate(self):
        if self.size not in PRESETS or self.profile not in {"clean", "realistic", "challenging"}:
            raise ValueError("Unknown size or anomaly profile")
        if self.chunk_rows < 1:
            raise ValueError("chunk_rows must be positive")
        for key in ("return_rate", "cancellation_rate", "payment_failure_rate"):
            if not 0 <= getattr(self, key) <= 1:
                raise ValueError(f"{key} must be in [0, 1]")
        if not 0 <= self.anonymous_sessions_per_order <= 10:
            raise ValueError("anonymous_sessions_per_order must be in [0, 10]")
        from datetime import date
        if set(self.incidents) != set(DEFAULT_INCIDENTS):
            raise ValueError("incidents must specify all five documented incident keys")
        for period in self.incidents.values():
            if len(period) != 2 or not date(2024, 1, 1) <= date.fromisoformat(period[0]) <= date.fromisoformat(period[1]) <= date(2025, 12, 31):
                raise ValueError("Incident windows must be ordered dates within 2024-2025")
        if min(self.counts.values()) < 1:
            raise ValueError("All volume counts must be positive")


def load_config(path):
    if not path:
        return {}
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {"return_rate", "cancellation_rate", "payment_failure_rate",
               "anonymous_sessions_per_order", "chunk_rows", "incidents"}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"Unsupported configuration keys: {sorted(unknown)}")
    return values
