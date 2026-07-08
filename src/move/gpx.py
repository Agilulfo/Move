from gpx import read_gpx
from geopy.distance import geodesic

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
        return point


class Coordinate:
    """
    Base class that provide utils for classes that contain coordinates.
    """

    def distance(self, other):
        return geodesic((self.lat, self.lon), (other.lat, other.lon)).meters


class Point(Coordinate):
    def __init__(self, id, lat, lon, timestamp):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp


class MeanPoint(Coordinate):
    def __init__(self):
        self.cumulative_lat = 0
        self.cumulative_lon = 0
        self.points = []

    def add_point(self, point):
        self.cumulative_lat += point.lat
        self.cumulative_lon += point.lon
        self.points.append(point)

    @property
    def lat(self):
        return self.cumulative_lat / len(self.points)

    @property
    def lon(self):
        return self.cumulative_lon / len(self.points)
