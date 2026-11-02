from pathlib import Path
import sqlite3
import pytest

from src.config.settings import Settings
from src.generators.project import generate
from src.utils.scratch import scratch_directory
from src.validators.checks import load_database, validate_dataset


@pytest.fixture(scope="session")
def work_dir():
    # Ordinary mkdir inherits workspace ACLs; no outside-workspace temp writes.
    with scratch_directory(Path.cwd(), ".test-run-") as folder:
        yield folder


@pytest.fixture(scope="session")
def dataset(work_dir):
    destination = work_dir / "sample"
    generate(Settings(size="small", output=destination, seed=42, keep_ground_truth=True,
                      chunk_rows=400, scale=dict(orders=900, customers=180, products=72, sellers=12)), progress=lambda _: None)
    return destination


@pytest.fixture(scope="session")
def report(dataset):
    return validate_dataset(dataset)


@pytest.fixture(scope="session")
def database(dataset):
    db = sqlite3.connect(":memory:")
    errors = []
    load_database(db, dataset / "reference" / "canonical", errors)
    assert not errors
    yield db
    db.close()
