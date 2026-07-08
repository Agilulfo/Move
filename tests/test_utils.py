from move.utils import format_coordinates, clickable_url, osm_url
from decimal import Decimal

COLOSSEUM_COORDS = (Decimal("41.890246"), Decimal("12.492332"))
TITICACA_LAKE_COORDS = (Decimal("-15.6991"), Decimal("-69.4432"))


def test_format_coordinates():
    lat, lon = COLOSSEUM_COORDS
    assert format_coordinates(lat, lon) == "41.890246, 12.492332"


def test_format_coordinates_with_precision():
    lat, lon = COLOSSEUM_COORDS
    assert format_coordinates(lat, lon, 2) == "41.89, 12.49"


def test_format_negative_coordinates():
    lat, lon = TITICACA_LAKE_COORDS
    assert format_coordinates(lat, lon) == "-15.699100, -69.443200"


def test_clickable_url():
    url = "example.com"
    display_text = "hello"
    assert (
        clickable_url(display_text, url)
        == "\x1b]8;;example.com\x1b\\hello\x1b]8;;\x1b\\"
    )


def test_OSM_url():
    lat, lon = TITICACA_LAKE_COORDS
    assert (
        osm_url(lat, lon)
        == "https://www.openstreetmap.org/?mlat=-15.699100&mlon=-69.443200#map=16/-15.699100/-69.443200"
    )
    assert (
        osm_url(lat, lon, False)
        == "https://www.openstreetmap.org/?#map=16/-15.699100/-69.443200"
    )
