from move.utils import coordinate_url
from move.gpx import PointStreamer, MeanPoint
import logging

logger = logging.getLogger(__name__)

DISTANCE_TRESHOLD = 100  # meters
DURATION_TRESHOLD = 60 * 7  # seconds


class Stay:
    def __init__(self, path):
        self.path = path
        self.location = None
        self.over = False

    def extend(self, point):
        if not self.location:
            self.location = MeanPoint()
            self.location.add_point(point)
            return
        else:
            distance = point.distance(self.location)
            if distance > DISTANCE_TRESHOLD:
                logger.info("we are starting moving")
                self.next = Move(self.path)
                self.next.extend(point)
                self.over = True
            else:
                self.location.add_point(point)

    def get_next(self):
        assert self.over
        return self.next

    def force_end(self):
        self.over = True

    @property
    def lat(self):
        return self.location.lat

    @property
    def lon(self):
        return self.location.lon

    @property
    def duration(self):
        start = self.location.points[0].timestamp
        end = self.location.points[-1].timestamp
        return end - start

    @property
    def points(self):
        return self.location.points

    def is_over(self):
        return self.over

    def __str__(self):
        return (
            f"Stay - "
            f"at: {coordinate_url(self.lat, self.lon)}, "
            f"for: {self.duration} "
            f"({len(self.location.points)} points)"
        )


class Move:
    def __init__(self, path):
        self.path = path
        self.track = []
        self.pause = None
        self.over = False

    def extend(self, point):
        if self.track:
            if self.pause:
                self.pause.extend(point)
                if self.pause.over:
                    # it was a short break and now we continue to move
                    logging.info("this is not a stay.. we are keeping moving")
                    for p in self.pause.points:
                        self.track.append(p)
                    self.pause = None
                    self.track.append(point)
                    return
                if self.pause.duration.seconds >= DURATION_TRESHOLD:
                    logging.info("We have got a new stay")
                    # it's a long pause we can consider this movement completed
                    self.over = True
            else:
                distance = self.track[-1].distance(point)
                if distance <= DISTANCE_TRESHOLD:
                    logging.info("We might have a stay..")
                    # the movement was small we might have a stay.
                    self.pause = Stay(self.path)
                    self.pause.extend(self.track[-1])
                    self.pause.extend(point)
                    del self.track[-1]
                else:
                    # we are keeping moving
                    self.track.append(point)
        else:
            self.track.append(point)

    def is_over(self):
        return self.over

    def get_next(self):
        assert self.over
        return self.pause

    def force_end(self):
        self.over = True

    def __str__(self):
        start = self.track[0]
        end = self.track[-1]
        return (
            f"Move - "
            f"from: {coordinate_url(start.lat, start.lon)}, "
            f"to: {coordinate_url(end.lat, end.lon)}, "
            f"during: {abs(start.timestamp - end.timestamp)} "
            f"({len(self.track)} points)."
        )


def analize_gpx_file(path):
    timeline = []
    current_entity = Stay(path)
    for point in PointStreamer(path):
        current_entity.extend(point)
        if current_entity.is_over():
            timeline.append(current_entity)
            current_entity = current_entity.get_next()
    current_entity.force_end()
    timeline.append(current_entity)
    return timeline
