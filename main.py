from __future__ import annotations

import argparse
from pathlib import Path

from crawler.engine import CrawlerEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a config-driven crawler task.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a YAML crawler config, for example configs/example_static.yaml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    engine = CrawlerEngine.from_yaml(config_path)
    result = engine.run()
    print(
        f"Task finished: fetched={result.fetched}, parsed={result.parsed}, "
        f"saved={result.saved}, skipped={result.skipped}, failed={result.failed}"
    )


if __name__ == "__main__":
    main()
