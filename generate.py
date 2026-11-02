"""CLI: never replaces existing user files or connects to external systems."""
import argparse
import sys
import time
from pathlib import Path

from src.config.settings import Settings, load_config
from src.generators.project import generate


def main():
    parser = argparse.ArgumentParser(description="Generate VietCommerce synthetic enterprise source data")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--profile", choices=["clean", "realistic", "challenging"], default="realistic")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--chunk-rows", type=int)
    parser.add_argument("--keep-ground-truth", action="store_true")
    parser.add_argument("--omit-reference", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        values = load_config(args.config)
        if args.chunk_rows is not None:
            values["chunk_rows"] = args.chunk_rows
        settings = Settings(size=args.size, seed=args.seed, output=args.output, profile=args.profile,
                            keep_ground_truth=args.keep_ground_truth, omit_reference=args.omit_reference, **values)
        manifest = generate(settings)
    except (ValueError, OSError) as error:
        print(f"Generation failed: {error}", file=sys.stderr)
        return 1
    print(f"Generated {len(manifest['canonical_rows'])} datasets; {manifest['total_data_bytes'] / 1e6:.1f} MB; {time.perf_counter()-started:.1f}s")
    print(f"Validate with: python validate.py --input \"{args.output}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
