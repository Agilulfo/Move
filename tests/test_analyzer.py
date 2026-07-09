from move.analyzer import analize_gpx_file, Stay, DURATION_TRESHOLD


def test_analize_produce_sequential_items():
    file = "./examples/20260705.gpx"
    items = analize_gpx_file(file)
    prev_item = items[0]

    for item in items[1:]:
        assert item.start.address == prev_item.end.address
        prev_item = item


def test_analize_dose_not_create_short_stays():
    file = "./examples/20260705.gpx"
    items = analize_gpx_file(file)

    for item in items:
        if type(item) is Stay:
            assert item.duration() > DURATION_TRESHOLD
