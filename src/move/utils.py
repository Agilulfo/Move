OSM_BASE = "https://www.openstreetmap.org/"


def coordinate_url(lat, lon):
    """
    Generate a String that can be used as a terminal output.
    the string shows coordinates that contain an url to a webpage
    that shows the actual location.
    """

    return clickable_url(format_coordinates(lat, lon, 2), osm_url(lat, lon))


def format_coordinates(lat, lon, precision=6):
    """
    Given coordinates this function return a string
    representing the coordinates, the optional precision
    parameter can be used to specify how many decimals to
    include (default to 6).

    It's recommended not to use more than 6 decimals.
    """
    return f"{lat:.{precision}f}, {lon:.{precision}f}"


def clickable_url(display_text, url):
    """
    Format a text and a url to be clickable in a terminal.
    Special escape characters are used to hide the url and
    get a clean output.
    """
    return f"\x1b]8;;{url}\x1b\\{display_text}\x1b]8;;\x1b\\"


def osm_url(lat, lon, marker=True, zoom=16):
    marker_option = f"mlat={lat:.6f}&mlon={lon:.6f}" if marker else ""
    return f"{OSM_BASE}?{marker_option}#map={zoom}/{lat:.6f}/{lon:.6f}"
