import six
from hamcrest.core.base_matcher import BaseMatcher
from math import fabs


class IsWithinDelta(BaseMatcher):

    def __init__(self, value, delta):
        self.value = value
        self.delta = delta

    def _matches(self, item):
        return item > self.value - self.delta and item < self.value + self.delta

    def describe_mismatch(self, item, mismatch_description):
        actual_delta = item - self.value
        mismatch_description.append_description_of(item)            \
                            .append_text(' differed by ')           \
                            .append_description_of(actual_delta)

    def describe_to(self, description):
        description.append_text('a numeric value within ')  \
                   .append_description_of(self.delta)       \
                   .append_text(' of ')                     \
                   .append_description_of(self.value)


def within_delta(value, delta):
    """Matches if object is a object within value + delta and value - detla

    :param value: The value to compare against as the expected value.
    :param delta: The maximum delta between the values for which the numbers
        are considered close.

    This matcher check the the evaluated object is between ``value`` + and - ``delta``.

    Example::

        within(3.0, 0.25)

    """
    return IsWithinDelta(value, delta)
