from hamcrest.core.base_matcher import BaseMatcher
from math import fabs


class CornersSameAsBounds(BaseMatcher):

    def __init__(self, bounds, delta):
        self.bounds = bounds
        self.delta = delta

    def _matches(self, item):
        """

        :param item: bounding corner, [bottom left, top left, top right, bottom right]
        :return: true if the same
        """
        bottom_left = item[0]
        bottom_right = item[3]
        top_left = item[1]
        top_right = item[2]

        return \
            self._check_corner(bottom_left, self.bounds.lon_min, self.bounds.lat_min) and \
            self._check_corner(bottom_right, self.bounds.lon_max, self.bounds.lat_min) and \
            self._check_corner(top_left, self.bounds.lon_min, self.bounds.lat_max) and \
            self._check_corner(top_right, self.bounds.lon_max, self.bounds.lat_max)

    def describe_mismatch(self, item, mismatch_description):
        bottom_left = item[0]
        bottom_right = item[3]
        top_left = item[1]
        top_right = item[2]

        mismatch_description.append_description_of(item)
        if self._check_corner(bottom_left, self.bounds.lon_min, self.bounds.lat_min):
            mismatch_description.append_text(' differed on bottom left ')
        if self._check_corner(bottom_right, self.bounds.lon_max, self.bounds.lat_min):
            mismatch_description.append_text(' differed on bottom right ')
        if self._check_corner(top_left, self.bounds.lon_min, self.bounds.lat_max):
            mismatch_description.append_text(' differed on top left ')
        if self._check_corner(top_right, self.bounds.lon_max, self.bounds.lat_max):
            mismatch_description.append_text(' differed on top right ')

    def describe_to(self, description):
        description.append_text('corners within ')  \
                   .append_description_of(self.delta)       \
                   .append_text(' lat:')                     \
                   .append_description_of(self.bounds.lat_min) \
                   .append_text(' - ')                     \
                   .append_description_of(self.bounds.lat_max) \
                   .append_text(' lon:')                     \
                   .append_description_of(self.bounds.lon_min) \
                   .append_text(' - ') \
                   .append_description_of(self.bounds.lon_max)

    def _check_corner(self, corner, lon, lat):
        return fabs(float(corner[0]) - float(lon)) < self.delta and fabs(float(corner[1]) - float(lat)) < self.delta


def corner_in_bounds_by_delta(bounds, delta):
    """
    Check that the corners are a the edges of the lat min max
    :param bounds: bounds object with attributes lat_min (minimum latitude), lat_max(maximum latitude),
        lon_min (minimum longitude), lon_max(maximum longitude)
    :param delta: The maximum delta between the values for which the numbers
        are considered close.
    :return: matcher
    """

    return CornersSameAsBounds(bounds, delta)
