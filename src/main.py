#!/usr/bin/env python3
import sys
from pathlib import Path

# Add alfred_results to the PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

import csv
import os
from collections.abc import Sequence
from io import StringIO

from alfred_results import ScriptFilterPayload
from alfred_results.result_item import Icon, Mod, ResultItem
from color_result import create_color_icon_file, make_color_result_item
from color_utils import (
    analogous_palette,
    color_shades_palette,
    complementary_palette,
    hex_to_hsl,
    hex_to_hsl_css,
    hex_to_rgb,
    hex_to_rgb_css,
)

# Back navigation item prepended to all result lists so the user can return
# to the previous Alfred view.
BACK_ICON: ResultItem = ResultItem(
    title="Back",
    arg="back",
    mods=[Mod(key="alt", subtitle=""), Mod(key="ctrl", subtitle="")],
    icon=Icon("./back.png"),
)


def extract_user_brand_colors(data: str) -> list[ResultItem]:
    """Parse a CSV string of brand colors into a list of result items.

    Each row must have at least two columns: a display name and a hex color
    value. Rows with fewer than two columns are silently skipped.

    The expected format of `data` matches the `BRAND_COLORS` workflow
    environment variable.

    Example:
        Brand Red,#FF0000
        Brand Blue,#0000FF

    Args:
        data: A CSV-formatted string where each row is `name,hex`.

    Returns:
        A list of `ResultItem` objects, one per valid row.
    """
    brand_colors: list[ResultItem] = []

    reader = csv.reader(StringIO(data))
    for row in reader:
        if not row:
            continue

        if len(row) < 2:
            continue

        name: str = row[0].strip()
        hex_value = row[1].strip().removeprefix("#").upper()

        if not name or not hex_value:
            print(f"invalid brand color info: {row}", file=sys.stderr)
            continue

        # validate hex color
        try:
            hex_to_rgb(hex_value)
        except ValueError:
            print(f"invalid brand hex color: {hex_value}", file=sys.stderr)
            continue

        color = make_color_result_item(hex_value, name)
        brand_colors.append(color)

    return brand_colors


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Alfred color picker script filter.

    Dispatches on the first argument to produce a `ScriptFilterPayload` and
    writes the JSON result to stdout. Supported subcommands:

    - `--brand`: Lists user-defined brand colors from the `BRAND_COLORS`
      environment variable.
    - `--analogous <hex>`: Generates an analogous color palette.
    - `--complementary <hex>`: Generates a complementary color palette.
    - `--shades <hex>`: Generates a shades palette.
    - `--convert <hex>`: Shows all format conversions for a single color.

    The `GO_BACK` environment variable controls whether a back-navigation item
    is prepended to result lists. Accepts `'true'` or `'false'` (case-insensitive);
    defaults to `'true'`.

    Args:
        argv: Argument list to parse. Defaults to `sys.argv[1:]` when `None`.

    Returns:
        Exit code. `0` on success, `1` when no arguments are provided.
    """
    args = list(argv) if argv is not None else sys.argv[1:]

    if not args:
        print("No argv provided.", file=sys.stderr)
        return 1

    flag = args[0]
    user_input = args[1] if len(args) >= 2 else None
    go_back = os.getenv("GO_BACK", "true").lower() == "true"

    match flag:
        case "--brand":
            items: list[ResultItem] = extract_user_brand_colors(
                os.getenv("BRAND_COLORS", "")
            )
            payload = ScriptFilterPayload(items=items)
        case "--analogous" | "--complementary" | "--shades":
            if user_input is None:
                payload = ScriptFilterPayload.info(
                    "Enter a HEX color code to continue..."
                )
            else:
                funcs = {
                    "--analogous": analogous_palette,
                    "--complementary": complementary_palette,
                    "--shades": color_shades_palette,
                }
                try:
                    func = funcs[flag]
                    hex_value = user_input.removeprefix("#")

                    items: list[ResultItem] = []
                    for c in func(hex_value):
                        items.append(make_color_result_item(hex_color=c))

                    payload = ScriptFilterPayload(items=items)
                except ValueError:
                    payload = ScriptFilterPayload.info(
                        title="Invalid HEX input",
                        subtitle="Use RRGGBB or RGB",
                    )
        case "--convert":
            if user_input is None:
                payload = ScriptFilterPayload.info(
                    "Enter a HEX color code to continue...",
                )
            else:
                try:
                    hex_value = user_input.removeprefix("#")
                    r, g, b = hex_to_rgb(hex_value)
                    rgb: str = f"{r}, {g}, {b}"
                    rgb_css: str = hex_to_rgb_css(hex_value)
                    h, s, l = hex_to_hsl(hex_value)
                    hsl: str = f"{round(h)}, {round(s)}, {round(l)}"
                    hsl_css: str = hex_to_hsl_css(hex_value)
                    icon_file: str = (
                        create_color_icon_file(hex_value).resolve().as_posix()
                    )
                    icon = Icon(icon_file)

                    items: list[ResultItem] = [
                        ResultItem(title=f"Copy as RGB {rgb}", arg=rgb, icon=icon),
                        ResultItem(title=f"Copy as {rgb_css}", arg=rgb_css, icon=icon),
                        ResultItem(title=f"Copy as HSL {hsl}", arg=hsl, icon=icon),
                        ResultItem(title=f"Copy as {hsl_css}", arg=hsl_css, icon=icon),
                    ]
                    payload = ScriptFilterPayload(items=items)

                except ValueError:
                    payload = ScriptFilterPayload.info(
                        title="Invalid HEX input",
                        subtitle="Use RRGGBB or RGB",
                    )
        case _:
            print(f"invalid argument: '{flag}'", file=sys.stderr)
            return 1

    if payload.items and go_back:
        payload.items.insert(0, BACK_ICON)
    sys.stdout.write(payload.to_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
