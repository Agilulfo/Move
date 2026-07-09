from gpx import read_gpx
from geopy.distance import geodesic
from move.utils import coordinate_url
import logging

logger = logging.getLogger(__name__)


class Gpx:
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        return PointStreamer(self.path)

    def get_datapoint_at(self, location):
        point_streamer = PointStreamer(self.path)
        point = next(point_streamer)
        while point.id != location:
            point = next(point_streamer)
        return point

    def get_datapoint_sequence(self, from_location, to_location):
        point_streamer = PointStreamer(self.path)
        point = next(point_streamer)

        while point.id != from_location:
            point = next(point_streamer)

        sequence = []

        while point.id != to_location:
            sequence.append(point)
            point = next(point_streamer)

        sequence.append(point)

        return sequence


class PointStreamer:
    def __init__(self, file_path):
        self.index = 0
        gpx = read_gpx(file_path)
        logger.info("gpx loaded")
        self.waypoints = iter(gpx.trk[0].trkseg[0])

    def __iter__(self):
        return self

    def __next__(self):
        waypoint = next(self.waypoints)
        point = DataPoint(self.index, waypoint.lat, waypoint.lon, waypoint.time)
        self.index += 1
        return point


class Coordinate:
    """
    Base class that provide utils for classes that contain coordinates.
    """

    def distance(self, other):
        return geodesic((self.lat, self.lon), (other.lat, other.lon)).meters

    def __str__(self):
        return f"{coordinate_url(self.lat, self.lon)}"


class DataPoint(Coordinate):
    """
    DataPoint is the internal representation
    of a geographical location at a precise point in time

    roughtly it correspond to a gpx 'trkpt' 'wpt' or 'rtept' elements

    WARNING:
    currently it's expected for a datapoint to have a timestamp
    """

    def __init__(self, id, lat, lon, timestamp):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp

    def __str__(self):
        return (
            f"Datapoint - "
            f"pos = {super().__str__()}, "
            f"t = {self.timestamp}, "
            f"id = {self.id}"
        )


class AveragePoint(Coordinate):
    """
    AveragePoint allows to calculate
    a point that is somewhere in between other points,
    useful to filter noise on a sequnce of points.

    WARNING:
    this is mere approximation of an average point
    it might also produce completelly unacceptable
    results close to the antimeridian
    (lon == 180 or -180) or close to the poles.
    """

    def __init__(self):
        self.cumulative_lat = 0
        self.cumulative_lon = 0
        self.point_count = 0

    def add_point(self, point):
        self.cumulative_lat += point.lat
        self.cumulative_lon += point.lon
        self.point_count += 1

    @property
    def lat(self):
        return self.cumulative_lat / self.point_count

    @property
    def lon(self):
        return self.cumulative_lon / self.point_count

    def __str__(self):
        return f"Mean point - {super().__str__()}"
