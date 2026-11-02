"""Workspace-local scratch space, including Windows sandboxes with restricted ACLs."""
from contextlib import contextmanager
from pathlib import Path
import shutil
import uuid


@contextmanager
def scratch_directory(parent, prefix=".scratch-"):
    parent = Path(parent).resolve()
    target = parent / (prefix + uuid.uuid4().hex)
    target.mkdir()
    try:
        yield target
    finally:
        resolved = target.resolve()
        if resolved.parent != parent or not resolved.name.startswith(prefix):
            raise ValueError("Refusing cleanup outside the scratch parent")
        shutil.rmtree(resolved)
