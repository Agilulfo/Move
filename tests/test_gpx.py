from move.gpx import get_datapoint_at, get_datapoint_sequence, PointStreamer


def test_datapoint_at_location():
    path = "./examples/20260709.gpx"

    iterator = iter(PointStreamer(path))

    for _ in range(5):
        next(iterator)

    datapoint = next(iterator)

    retrieved_datapoint = get_datapoint_at(datapoint.address)

    assert datapoint.lat == retrieved_datapoint.lat
    assert datapoint.lon == retrieved_datapoint.lon
    assert datapoint.address == retrieved_datapoint.address


def test_get_datapoint_sequence():
    path = "./examples/20260709.gpx"

    iterator = iter(PointStreamer(path))

    for _ in range(5):
        next(iterator)

    sequence = [next(iterator) for _ in range(3)]

    retrieved_sequence = get_datapoint_sequence(
        sequence[0].address, sequence[-1].address
    )

    for original, retrieved in zip(sequence, retrieved_sequence):
        assert original.address == retrieved.address
