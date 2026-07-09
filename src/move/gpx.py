from gpx import read_gpx
from geopy.distance import geodesic
from move.utils import coordinate_url
import logging

logger = logging.getLogger(__name__)


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
        point = Point(self.index, waypoint.lat, waypoint.lon, waypoint.time)
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


class Point(Coordinate):
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
