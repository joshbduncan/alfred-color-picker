import os
import sys
import tempfile
from pathlib import Path

from alfred_results.result_item import Icon, Mod, ResultItem
from color_utils import (
    hex_to_hsl,
    hex_to_hsl_css,
    hex_to_rgb,
    hex_to_rgb_css,
)

# Maps Alfred modifier keys to user-configured copy actions via workflow
# environment variables. Each env var must be set to one of the valid
# copy action values:
#
#   COPY_AS_HEX      — copies the hex value (e.g. `#FF0080`)
#   COPY_AS_RGB      — copies comma-separated RGB values (e.g. `255, 0, 128`)
#   COPY_AS_RGB_CSS  — copies a CSS rgb() string (e.g. `rgb(255 0 128)`)
#   COPY_AS_HSL      — copies comma-separated HSL values (e.g. `214, 100, 50`)
#   COPY_AS_HSL_CSS  — copies a CSS hsl() string (e.g. `hsl(214 100% 50%)`)
#
# MOD_NONE controls the default action (no modifier key held).
# Unrecognized values are skipped with a warning to stderr.
USER_MODIFIERS: dict[str, dict[str, str]] = {
    "MOD_NONE": {"key": "return", "value": os.getenv("MOD_NONE", "COPY_AS_HEX")},
    "MOD_COMMAND": {"key": "cmd", "value": os.getenv("MOD_COMMAND", "COPY_AS_RGB")},
    "MOD_SHIFT": {"key": "shift", "value": os.getenv("MOD_SHIFT", "COPY_AS_RGB_CSS")},
    "MOD_ALT": {"key": "alt", "value": os.getenv("MOD_ALT", "COPY_AS_HSL")},
    "MOD_CONTROL": {
        "key": "ctrl",
        "value": os.getenv("MOD_CONTROL", "COPY_AS_HSL_CSS"),
    },
}


def create_color_icon_file(hex_color: str) -> Path:
    """Create an SVG icon for a given color and return its path.

    Renders a 96×96 rounded rectangle centered in a 128×128 viewbox, filled
    with the specified hex color. The SVG is written to a deterministic path in
    the system temporary directory keyed by hex value, so repeated calls for
    the same color are idempotent.

    The temp file is not deleted by this function. It persists until the OS
    removes it (on reboot or periodic tmp cleanup).

    Args:
        hex_color: Hex color string with or without a leading '#' (e.g. `'#FF0000'`
            or `'FF0000'`).

    Returns:
        `Path` to the generated SVG file in the system temporary directory.
    """
    hex_value = hex_color.removeprefix("#")
    svg: str = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="128" height="128" '
        f'viewBox="0 0 128 128">'
        f'<rect x="16" y="16" '
        f'width="96" height="96" '
        f'rx="8" ry="8" '
        f'fill="#{hex_value}"/>'
        f"</svg>"
    )
    output: Path = Path(tempfile.gettempdir()) / f"icon_{hex_value}.svg"
    output.write_text(svg, encoding="utf-8")
    return output


def make_color_result_item(hex_color: str, title: str | None = None) -> ResultItem:
    """Build an Alfred `ResultItem` for a given hex color.

    Computes all alternate color formats (RGB, CSS rgb(), HSL, CSS hsl()),
    generates an SVG icon, and applies the copy actions defined in
    `USER_MODIFIERS` to the item's arg, subtitle, and modifier keys.

    Args:
        hex_color: Hex color string with or without a leading '#' (e.g. `'#FF0000'`
            or `'FF0000'`).
        title: Display title for the result item. Defaults to the CSS hex
            string (e.g. `'#FF0000'`) when not provided.

    Returns:
        A `ResultItem` configured with the color icon, subtitle and arg driven
        by `USER_MODIFIERS["MOD_NONE"]`, and one `Mod` per non-empty modifier
        key in `USER_MODIFIERS`.
    """
    hex_value: str = hex_color.removeprefix("#")
    hex_value_css = f"#{hex_value}"
    title = title if title is not None else hex_value_css

    # calculate alternate color formats for result variables and modifiers
    r, g, b = hex_to_rgb(hex_value)
    rgb: str = f"{r}, {g}, {b}"
    rgb_css: str = hex_to_rgb_css(hex_value)
    h, s, l = hex_to_hsl(hex_value)
    hsl: str = f"{round(h)}, {round(s)}, {round(l)}"
    hsl_css: str = hex_to_hsl_css(hex_value)

    icon_file: str = create_color_icon_file(hex_value).resolve().as_posix()
    icon: Icon = Icon(icon_file)

    mod_values_lut = {
        "COPY_AS_HEX": {
            "arg": hex_value_css,
            "subtitle": f"Copy as HEX {hex_value_css}",
        },
        "COPY_AS_RGB": {
            "arg": rgb,
            "subtitle": f"Copy as RGB {rgb}",
        },
        "COPY_AS_RGB_CSS": {
            "arg": rgb_css,
            "subtitle": f"Copy as {rgb_css}",
        },
        "COPY_AS_HSL": {
            "arg": hsl,
            "subtitle": f"Copy as HSL {hsl}",
        },
        "COPY_AS_HSL_CSS": {
            "arg": hsl_css,
            "subtitle": f"Copy as {hsl_css}",
        },
    }

    mod_none_value = USER_MODIFIERS["MOD_NONE"]["value"]
    if mod_none_value not in mod_values_lut:
        print(
            f"color_result: unrecognized MOD_NONE value {mod_none_value!r}, "
            "falling back to COPY_AS_HEX",
            file=sys.stderr,
        )
        mod_none_value = "COPY_AS_HEX"
    subtitle = mod_values_lut[mod_none_value]["subtitle"]
    arg = mod_values_lut[mod_none_value]["arg"]

    mods: list[Mod] = []
    for k, v in USER_MODIFIERS.items():
        if k == "MOD_NONE":
            continue
        action = v["value"]
        if not action:
            continue
        if action not in mod_values_lut:
            print(
                f"color_result: unrecognized {k} value {action!r}, skipping modifier",
                file=sys.stderr,
            )
            continue
        mods.append(
            Mod(
                key=v["key"],
                arg=mod_values_lut[action]["arg"],
                subtitle=mod_values_lut[action]["subtitle"],
            )
        )

    return ResultItem(title=title, subtitle=subtitle, arg=arg, icon=icon, mods=mods)
