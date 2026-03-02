import colorsys


def _clamp_u8(value: float) -> int:
    """Convert float 0–1 to safe 0–255 integer."""
    return max(0, min(255, int(round(value * 255))))


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert an HSL color to a 6-digit hexadecimal RGB string.

    Args:
        h: Hue angle in degrees (0–360). Values outside this range are wrapped
            modulo 360.
        s: Saturation percentage (0–100). Clamped to the valid range.
        l: Lightness percentage (0–100). Clamped to the valid range.

    Returns:
        Uppercase 6-digit hex RGB string without a leading `'#'` (e.g. `'RRGGBB'`).

    Notes:
        Conversion delegates to Python's `colorsys.hls_to_rgb`.
    """
    h_f: float = (h % 360) / 360
    s_f: float = max(0.0, min(1.0, s / 100))
    l_f: float = max(0.0, min(1.0, l / 100))

    r_f, g_f, b_f = colorsys.hls_to_rgb(h_f, l_f, s_f)

    r = _clamp_u8(r_f)
    g = _clamp_u8(g_f)
    b = _clamp_u8(b_f)

    return f"{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to an RGB tuple.

    Accepts `'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`.
    Returns integer channel values in the range 0–255.

    Args:
        hex_color: Hex color string.

    Returns:
        (r, g, b) tuple with values 0–255.

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(
            f"hex color must be 3 or 6 digits, got {len(hex_color.lstrip('#'))}"
        )
    if not all(c in "0123456789ABCDEFabcdef" for c in h):
        raise ValueError(f"hex color contains invalid characters: {hex_color!r}")

    return int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB channels to HSL.

    Note: Python's `colorsys` module uses HLS ordering internally, so this
    function maps it back to the conventional HSL output.

    Args:
        r: Red channel 0–255.
        g: Green channel 0–255.
        b: Blue channel 0–255.

    Returns:
        (h, s, l) where:
            h: Hue in degrees 0–360.
            s: Saturation percentage 0–100.
            l: Lightness percentage 0–100.
    """
    r_f: float = r / 255
    g_f: float = g / 255
    b_f: float = b / 255

    h, l, s = colorsys.rgb_to_hls(r_f, g_f, b_f)
    return h * 360, s * 100, l * 100


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex color string to an HSL tuple.

    Accepts `'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`.

    Args:
        hex_color: Hex color string.

    Returns:
        (h, s, l) where:
            h: Hue in degrees 0–360.
            s: Saturation percentage 0–100.
            l: Lightness percentage 0–100.

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hsl(r, g, b)


def hex_to_rgb_css(hex_color: str) -> str:
    """Convert a hex color string to a CSS rgb() color string.

    Output uses CSS Color Level 4 space-separated syntax: `rgb(R G B)`.

    Args:
        hex_color: Hex color string (`'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`).

    Returns:
        CSS rgb() string.

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    r, g, b = hex_to_rgb(hex_color)
    return f"rgb({r} {g} {b})"


def hex_to_hsl_css(hex_color: str) -> str:
    """Convert a hex color string to a CSS hsl() color string.

    Output uses CSS Color Level 4 space-separated syntax: `hsl(H S% L%)`.
    Values are rounded to whole numbers.

    Args:
        hex_color: Hex color string (`'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`).

    Returns:
        CSS hsl() string.

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    h, s, l = hex_to_hsl(hex_color)
    return f"hsl({round(h)} {round(s)}% {round(l)}%)"


def analogous_palette(hex_color: str, step_degrees: float = 30) -> list[str]:
    """Return a 5-color analogous palette for a given hex color.

    Uses the input color's saturation and lightness, rotating hue by
    -2*step, -step, 0, +step, and +2*step degrees.

    Args:
        hex_color: Hex color string (`'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`).
        step_degrees: Hue step in degrees between neighbors (commonly 15–30).

    Returns:
        List of 5 hex strings in `'RRGGBB'` format (no leading `'#'`).

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    h, s, l = hex_to_hsl(hex_color)
    offsets = (-2 * step_degrees, -step_degrees, 0.0, step_degrees, 2 * step_degrees)
    return [hsl_to_hex(h + off, s, l) for off in offsets]


def complementary_palette(hex_color: str) -> list[str]:
    """Return a 5-color palette built around the complement of a given hex color.

    The complement is the hue opposite on the color wheel (hue + 180°). The
    returned palette spreads ±30° and ±60° around that complement, preserving
    the input color's saturation and lightness.

    Args:
        hex_color: Hex color string (`'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`).

    Returns:
        List of 5 hex strings in `'RRGGBB'` format (no leading `'#'`), ordered
        from complement − 60° to complement + 60°.

    Raises:
        ValueError: If the input is not a valid 3- or 6-digit hex color.
    """
    h, s, l = hex_to_hsl(hex_color)

    complement = (h + 180) % 360
    offsets = (-60, -30, 0, 30, 60)

    return [hsl_to_hex(complement + off, s, l) for off in offsets]


def color_shades_palette(
    hex_color: str, count: int = 5, lightness_range: tuple[float, float] = (20, 80)
) -> list[str]:
    """Generate a palette of shades for a given hex color by varying lightness.

    Hue and saturation are kept constant while lightness is interpolated
    across a specified range.

    Args:
        hex_color: Hex color string (`'#RRGGBB'`, `'RRGGBB'`, `'#RGB'`, or `'RGB'`).
        count: Number of shades to generate. Must be >= 1.
        lightness_range: (min_L, max_L) lightness percentages to span (0–100).

    Returns:
        List of hex strings in `'RRGGBB'` format (no leading `'#'`), ordered
        from darkest to lightest.

    Raises:
        ValueError: If `count` is less than 1.
        ValueError: If `lightness_range` values are outside 0–100 or min > max.
        ValueError: If `hex_color` is not a valid 3- or 6-digit hex color.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    min_l, max_l = lightness_range
    if not (0 <= min_l <= 100 and 0 <= max_l <= 100 and min_l <= max_l):
        raise ValueError("lightness_range must be within 0–100 and min<=max")

    h, s, _ = hex_to_hsl(hex_color)

    if count == 1:
        return [hsl_to_hex(h, s, (min_l + max_l) / 2)]

    step = (max_l - min_l) / (count - 1)
    lightness_values = [min_l + i * step for i in range(count)]

    return [hsl_to_hex(h, s, lv) for lv in lightness_values]
