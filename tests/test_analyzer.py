from move.analyzer import analize_gpx_file


def test_analize_file():
    file = "./examples/20260705.gpx"
    analize_gpx_file(file)
