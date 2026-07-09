from gpx import read_gpx
from geopy.distance import geodesic
from move.utils import coordinate_url
import logging
import json

logger = logging.getLogger(__name__)


class GpxTreeElementAddress:
    """
    GpxTreeElementAddress provide utils to
    refer to specific XML tags in a GPX file.

    The intention is to allow to consistently
    retrieve specific datapoints from a gpx document.
    """

    def __init__(self, path, indexes):
        self.path = path
        self.indexes = indexes

    @classmethod
    def deserialize(cls, data):
        data = json.loads(data)
        return cls(data["path"], data["indexes"])

    def serialize(self):
        data = {"path": self.path, "indexes": self.indexes}
        return json.dumps(data)

    def __eq__(self, other):
        return self.path == other.path and self.indexes == other.indexes


# WARNING: StopIteration not handled
def get_datapoint_at(address):
    point_streamer = PointStreamer(address.path)
    point = next(point_streamer)
    while point.address != address:
        point = next(point_streamer)
    return point


# WARNING: Assumptions here:
# from_location and to_location are siblings of the same father
# and from comes before to
# StopIteration not handled
def get_datapoint_sequence(from_location, to_location):
    point_streamer = PointStreamer(from_location.path)
    point = next(point_streamer)

    while point.address != from_location:
        point = next(point_streamer)

    sequence = []

    while point.address != to_location:
        sequence.append(point)
        point = next(point_streamer)

    sequence.append(point)

    return sequence


class PointStreamer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.cursor = None
        # WARNING: this loads the whole file at once
        # for larger file this cause a larg amount of memory
        # and quite some time to load the whole file
        self.gpx = read_gpx(file_path)
        logger.info("gpx loaded")

    def __iter__(self):
        return self

    def __next__(self):
        self._advance_cursor()
        trk_index, seg_index, point_index = self.cursor
        waypoint = self.gpx.trk[trk_index].trkseg[seg_index].trkpt[point_index]
        address = GpxTreeElementAddress(self.file_path, self.cursor)
        return DataPoint(address, waypoint.lat, waypoint.lon, waypoint.time)

    def _advance_cursor(self):
        # WARNING: this makes several assumptions on how a file is structured
        # that might not be true with many files
        if self.cursor:
            trk_index, seg_index, point_index = self.cursor
            if point_index == len(self.gpx.trk[trk_index].trkseg[seg_index].trkpt) - 1:
                if seg_index == len(self.gpx.trk[trk_index].trkseg) - 1:
                    if trk_index == len(self.gpx.trk) - 1:
                        raise StopIteration()
                    else:
                        # move to next trk
                        trk_index += 1
                        seg_index = 0
                        point_index = 0
                else:
                    # move to next seg
                    seg_index += 1
                    point_index = 0
            else:
                # move to next point
                point_index += 1

            self.cursor = [trk_index, seg_index, point_index]
        else:
            self.cursor = [0, 0, 0]


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

    def __init__(self, address, lat, lon, timestamp):
        self.address = address
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp

    def __str__(self):
        return (
            f"Datapoint - "
            f"pos = {super().__str__()}, "
            f"t = {self.timestamp}, "
            f"address = {self.address}"
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
