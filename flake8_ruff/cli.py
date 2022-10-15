from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence

import flake8
import toml
from flake8.main.options import register_default_options
from flake8.options.config import load_config
from flake8.options.config import OptionManager
from flake8.options.config import parse_config
from flake8.plugins.finder import Checkers
from flake8.plugins.finder import Plugins

from flake8_ruff.rules import SUPPORTED_RULES


def main() -> int:
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument("--exit-zero", action="store_true")
    parser.add_argument("--stdin-display-name", type=str)
    parser.add_argument("files", nargs="+")

    cmdline_options = vars(parser.parse_args())
    flake8_options = get_flake8_options()
    return run(cmdline_options, flake8_options)


def get_flake8_options() -> Mapping[str, Any]:
    plugins = Plugins(checkers=Checkers([], [], []), reporters={}, disabled=[])
    config_parser, config_dir = load_config(config=None, extra=[])
    option_manager = OptionManager(
        version=flake8.__version__,
        plugin_versions=plugins.versions_str(),
        parents=[],
    )
    register_default_options(option_manager)

    return parse_config(
        option_manager,
        config_parser,
        config_dir,
    )


def run(cli_options: Mapping[str, Any], file_options: Mapping[str, Any]) -> int:
    ruff_cli_args = map_cmdline_args(cli_options)
    ruff_options = map_file_options(file_options)

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml") as f:
        toml.dump(ruff_options, f)
        f.flush()

        process = subprocess.Popen([_find_ruff(), "--config", f.name, *ruff_cli_args])
        return process.wait()


def _find_ruff() -> str:
    executable = Path(sys.executable).absolute()
    return str(executable.parent / "ruff")


def map_cmdline_args(flake8_cmdline_options: Mapping[str, Any]) -> Sequence[str]:
    args = []
    if flake8_cmdline_options.get("exit_zero"):
        args.append("--exit-zero")

    if "stdin_display_name" in flake8_cmdline_options:
        args.append(f"--stdin-filename={flake8_cmdline_options['stdin_display_name']}")

    return [*args, *flake8_cmdline_options["files"]]


def map_file_options(
    file_options: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    known_options = {
        "exclude",
        "extend-exclude",
        "select",
        "extend-select",
        "ignore",
        "extend-ignore",
        "per-file-ignores",
    }
    option_map = {
        "max-line-length": "line-length",
    }
    filter_functions: Mapping[str, Callable[[Any], Any]] = {
        "per-file-ignores": filter_per_file_ignores,
    }

    options = {}

    for name, value in file_options.items():
        name = name.replace("_", "-")
        if name in known_options:
            name = option_map.get(name, name)

            if isinstance(value, list):
                value = [v for v in value if v in SUPPORTED_RULES]

            fn = filter_functions.get(name, lambda v: v)
            options[name] = fn(value)

    return {"tool": {"ruff": options}}


def filter_per_file_ignores(contents: Any) -> Any:
    assert isinstance(contents, str)

    items = (line.strip() for line in contents.splitlines(keepends=False))
    file_rules = (item.split(":", maxsplit=1) for item in items if item != "")
    return [
        ":".join(fr) for fr in file_rules if len(fr) == 2 and fr[1] in SUPPORTED_RULES
    ]


if __name__ == "__main__":
    sys.exit(main())
