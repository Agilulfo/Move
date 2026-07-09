from move.utils import coordinate_url
from move.gpx import PointStreamer, AveragePoint
import logging

logger = logging.getLogger(__name__)

DISTANCE_TRESHOLD = 100  # meters
DURATION_TRESHOLD = 60 * 7  # seconds


class Stay:
    def __init__(self, point):
        self.start = point
        self.location = AveragePoint()
        self.location.add_point(point)
        logger.debug(f"New stay at: {point}")

    def extend(self, point):
        self.end = point
        self.location.add_point(point)

    def __str__(self):
        return (
            f"Stay - "
            f"at: {coordinate_url(self.location.lat, self.location.lon)}, "
            f"duration: {abs(self.start.timestamp - self.end.timestamp)}."
        )


    def duration(self):
        return (self.end.timestamp - self.start.timestamp).total_seconds()


class Move:
    def __init__(self, start_point):
        self.start = start_point
        logger.debug(f"New move at: {start_point}")

    def extend(self, point):
        self.end = point

    def __str__(self):
        return (
            f"Move - "
            f"from: {coordinate_url(self.start.lat, self.start.lon)}, "
            f"to: {coordinate_url(self.end.lat, self.end.lon)}, "
            f"duration: {abs(self.start.timestamp - self.end.timestamp)}."
        )



def analize_gpx_file(path):
    timeline = []

    last_datapoint = None

    current_move = None
    current_stay = None

    for current_datapoint in PointStreamer(path):
        if not last_datapoint:
            last_datapoint = current_datapoint
            continue

        distance = (
            current_stay.location.distance(current_datapoint)
            if current_stay
            else last_datapoint.distance(current_datapoint)
        )

        if distance > DISTANCE_TRESHOLD:
            # continue or start a move
            current_move = current_move or Move(last_datapoint)
            current_move.extend(current_datapoint)

            # terminate any stay
            if current_stay:
                if current_stay.duration() > DURATION_TRESHOLD:
                    logger.debug(f"completed {current_stay}")
                    timeline.append(current_stay)
                else:
                    logger.debug(f"killed {current_stay}")
                current_stay = None
        else:
            # continue or start a stay
            current_stay = current_stay or Stay(last_datapoint)
            current_stay.extend(current_datapoint)

            # if the stay is long enough, terminate any move.
            if current_move and current_stay.duration() > DURATION_TRESHOLD:
                timeline.append(current_move)
                logger.debug(f"compelted {current_move}")
                logger.debug(f"official {current_stay}")
                current_move = None

        last_datapoint = current_datapoint

    # TODO: check corner cases here
    if current_stay and current_stay.duration() > DURATION_TRESHOLD:
        timeline.append(current_stay)
        return timeline

    timeline.append(current_move)
    return timeline
