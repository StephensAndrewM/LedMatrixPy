import datetime
import unittest

from dateutil import tz

from timeutils import parse_utc_datetime


class TimeUtilsTest(unittest.TestCase):

    def testParseUtcDatetime_withNumericOffset(self) -> None:
        self.assertEqual(parse_utc_datetime("2000-01-02T03:04:05.006-07:00"),
                         datetime.datetime(2000, 1, 2, 3, 4,
                                           5, 0, tz.gettz("America/Denver"))
                         )

    def testParseUtcDatetime_withZOffset(self) -> None:
        self.assertEqual(parse_utc_datetime("2000-01-02T03:04:05.006Z"),
                         datetime.datetime(2000, 1, 2, 3, 4,
                                           5, 0, datetime.timezone.utc)
                         )

    def testParseUtcDatetime_withIrregularMillis(self) -> None:
        self.assertEqual(parse_utc_datetime("2000-01-02 03:04:05.6789-07:00"),
                         datetime.datetime(2000, 1, 2, 3, 4,
                                           5, 0, tz.gettz("America/Denver"))
                         )
