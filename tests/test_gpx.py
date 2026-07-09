from move.gpx import Gpx


def test_datapoint_at_location():
    path = "./examples/20260709.gpx"

    gpx = Gpx(path)
    iterator = iter(gpx)

    for _ in range(5):
        next(iterator)

    datapoint = next(iterator)

    retrieved_datapoint = gpx.get_datapoint_at(datapoint.id)

    assert datapoint.lat == retrieved_datapoint.lat
    assert datapoint.lon == retrieved_datapoint.lon
    assert datapoint.id == retrieved_datapoint.id


def test_get_datapoint_sequence():
    path = "./examples/20260709.gpx"
    gpx = Gpx(path)
    iterator = iter(gpx)

    for _ in range(5):
        next(iterator)

    sequence = [next(iterator) for _ in range(3)]

    retrieved_sequence = Gpx(path).get_datapoint_sequence(
        sequence[0].id, sequence[-1].id
    )

    for original, retrieved in zip(sequence, retrieved_sequence):
        assert original.id == retrieved.id
