import copy
import math
from datetime import datetime
from datetime import timedelta
from functools import partial

from dateutil.tz import tzlocal

from util import BASE_CONFIG
from util import CONSTANTS
from util import MOCK_HOST
from util import ScreenshotTest

DIRECTION_TO_TREND = dict([
    ('DoubleUp', 1),
    ('SingleUp', 2),
    ('FortyFiveUp', 3),
    ('Flat', 4),
    ('FortyFiveDown', 5),
    ('SingleDown', 6),
    ('DoubleDown', 7),
])

def iso_date(dt):
    return dt.replace(tzinfo=tzlocal()).isoformat()

def default_sgv_series(count=50):
    return [
        max(30, int(200 - 3 * i + 10 * math.sin(2 * i / math.pi)))
        for i in range(count)
    ]

def default_dates(count=50, offset=0):
    now = datetime.now()
    return [
        int((now + timedelta(seconds=offset) - timedelta(minutes=5 * i)).strftime('%s')) * 1000
        for i in range(count)
    ]

def default_dates_as_iso(*args, **kwargs):
    return [
        iso_date(datetime.fromtimestamp(date / 1000))
        for date in default_dates(*args, **kwargs)
    ]

def default_entries(direction, count=50):
    return [
        {
            'type': 'sgv',
            'sgv': sgv,
            'date': date,
            'direction': direction,
            'trend': DIRECTION_TO_TREND[direction],
        }
        for sgv, date
        in zip(default_sgv_series(count), default_dates(count))
    ]

def some_real_life_entries(self=None, minutes_old=0):
    sgvs = [190, 188, 180, 184, 184, 177, 174, 163, 152, 141, 134, 127, 124, 121, 117, 109, 103, 97, 94, 88, 79, 79, 75, 79, 84, 87, 88, 91, 91, 91, 94, 99, 102, 107, 106, 108, 107, 108, 115, 111, 114, 113, 115, 118, 120, 119, 120, 122, 123, 126, 122, 125, 125, 126, 125, 122, 122, 122, 119, 118, 118, 118, 117, 116, 115, 114, 114, 115, 114, 113, 114, 115, 111, 114, 115, 114, 114, 116, 117, 117, 118, 119, 121, 124, 125, 128, 126, 128, 131, 133, 135, 136, 135, 134, 132, 130, 132, 130, 129, 131, 129, 128, 128, 127, 125, 124, 125, 126]
    return [
        {
            'type': 'sgv',
            'sgv': sgv,
            'date': date,
            'direction': 'Flat',
            'trend': 4,
        }
        for sgv, date
        in zip(sgvs, default_dates(len(sgvs), offset=-60 * minutes_old))
    ]

def sgvs_from_array(arr, offset=0):
    return [
        {'date': date, 'sgv': sgv, 'direction': 'Flat'}
        for date, sgv in zip(default_dates(len(arr), offset=offset), arr)
    ]

def some_fake_temp_basals(*args):
    rates = [2, 1, 0, 0.1, 0.4, 0, 0.5, 1.5, 0.8, 0]
    return [
        {'absolute': rate, 'created_at': date, 'duration': 30}
        # offset by 2.5 minutes so the basals are centered around the SGVs
        for rate, date in zip(rates, default_dates_as_iso(offset=-150))
    ]

def some_fake_boluses(*args):
    dates = default_dates_as_iso()
    return [
        {'created_at': dates[0], 'insulin': 1},
        {'created_at': dates[2], 'insulin': 1},
        {'created_at': dates[5], 'insulin': 1},
        {'created_at': dates[6], 'insulin': 1},
        {'created_at': dates[11], 'insulin': 1},
        {'created_at': dates[40], 'insulin': 1},
    ]

def boluses_from_array(arr, offset=0):
    return [
        {
            'created_at': iso_date(datetime.now() + timedelta(seconds=(-offset + b_offset - 5 * 60 * i))),
            'insulin': insulin,
        }
        for i, (b_offset, insulin)
        in enumerate(arr)
    ]

def basals_from_array(arr, offset=0):
    return [
        {
            'created_at': iso_date(datetime.now() + timedelta(seconds=(-offset + b_offset - 5 * 60 * i))),
            'duration': duration,
            'absolute': rate,
        }
        for i, (b_offset, duration, rate)
        in enumerate(arr)
    ]

def profile_with_one_basal(rate):
    return [{"basal": [{"time": "00:00", "value": rate}]}]

def loop_devicestatus(prediction_series, min_ago):
    start_iso = iso_date(datetime.now() - timedelta(minutes=min_ago))
    return [{
        'loop': {
            'predicted': {
            'values': prediction_series,
                'startDate': start_iso,
            },
        },
        'created_at': start_iso,
    }]

def mutate_element(layout, el_name, props):
    for el in layout['elements']:
        if CONSTANTS['ELEMENTS'][el['el']] == el_name:
            el.update(props)


class TestBasicIntegration(ScreenshotTest):
    """Test that the graph, delta, trend, etc. all work."""
    sgvs = partial(default_entries, 'FortyFiveDown')


class TestMmol(ScreenshotTest):
    """Test mmol."""
    config = {
        'mmol': True,
    }
    sgvs = partial(default_entries, 'Flat')


class TestGraphBoundsAndGridlines(ScreenshotTest):
    """Test adjusting the graph bounds and gridlines."""
    config = {
        'topOfGraph': 400,
        'topOfRange': 280,
        'bottomOfRange': 120,
        'bottomOfGraph': 20,
        'hGridlines': 20,
    }
    sgvs = partial(default_entries, 'DoubleUp')


class TestSGVsAtBoundsAndGridlines(ScreenshotTest):
    """Test that the placement of target range bounds and gridlines is consistent with the placement of SGV points."""
    def sgvs(self):
        sgvs = default_entries('Flat')
        for i, s in enumerate(sgvs):
            if i < 9:
                s['sgv'] = BASE_CONFIG['topOfRange']
            elif i < 18:
                s['sgv'] = BASE_CONFIG['topOfRange'] - BASE_CONFIG['hGridlines']
            elif i < 27:
                s['sgv'] = BASE_CONFIG['topOfRange'] - BASE_CONFIG['hGridlines'] * 2
            else:
                s['sgv'] = BASE_CONFIG['bottomOfRange']
        return sgvs


class TestStaleServerData(ScreenshotTest):
    """Test that when server data is stale, an icon appears, and no trend/delta is shown in the sidebar."""

    # TODO: make this test not flaky (sometimes icon position is off by one pixel)
    __test__ = False

    def sgvs(self):
        return default_entries('SingleDown')[7:]


class TestNotRecentButNotYetStaleBGRow(ScreenshotTest):
    """Test that trend and delta are not shown in the BG row when data is not recent."""
    config = {'layout': 'c'}
    def sgvs(self):
        return default_entries('SingleDown')[2:]


class TestErrorCodes(ScreenshotTest):
    """Test that error codes appear as ??? and are not graphed."""
    def sgvs(self):
        s = default_entries('SingleDown')
        for i in range(0, 19, 3):
            s[i]['sgv'] = s[i + 1]['sgv'] = 10
        del s[0]['direction']
        del s[0]['trend']
        return s


class TestPositiveDelta(ScreenshotTest):
    """Test that positive deltas have "+" prepended and are not treated as error codes."""
    def sgvs(self):
        s = default_entries('SingleUp')
        s[1]['sgv'] = s[0]['sgv'] - 10
        return s


class TestTrimmingValues(ScreenshotTest):
    """Test that values outside the graph bounds are trimmed."""
    config = {
        'topOfGraph': 250,
        'topOfRange': 200,
        'bottomOfRange': 80,
        'bottomOfGraph': 40,
        'hGridlines': 50,
    }
    def sgvs(self):
        s = default_entries('DoubleDown')
        for i in range(12):
            s[i]['sgv'] = 20 + 4 * i
        for i in range(12, 24):
            s[i]['sgv'] = 64 + 15 * (i - 12)
        for i in range(24, len(s)):
            s[i]['sgv'] = 229 + 9 * (i - 24)
        return s


class TestDegenerateEntries(ScreenshotTest):
    """Test that "bad" SGV entries don't cause the watchface to crash."""
    def sgvs(self):
        s = default_entries('DoubleDown')
        # A raw-only entry won't have sgv, shouldn't be graphed
        for i in range(6, 12):
            del s[i]['sgv']
        # Some uploaders sometimes give trend and direction as null
        s[0]['trend'] = s[0]['direction'] = None
        return s


class TestBlackBackground(ScreenshotTest):
    """Test that the time, status bar, sidebar, and graph elements can be set to a black background."""
    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['a'])
        elements_under_test = [CONSTANTS['ELEMENTS'][el['el']] for el in layout['elements']]
        assert all([
            el in elements_under_test
            for el
            in ('TIME_AREA_ELEMENT', 'STATUS_BAR_ELEMENT', 'SIDEBAR_ELEMENT', 'GRAPH_ELEMENT')
        ])

        for el in layout['elements']:
            el['black'] = True
        layout['recencyColorText'] = '0x00FFFF'

        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'black as coal',
            'bottomOfRange': 120,
            'topOfRange': 180,
            'pointColorDefault': '0x5555FF',
            'pointColorHigh': '0xFFAAAA',
            'pointColorLow': '0xAAFFFF',
        }

    sgvs = partial(default_entries, 'Flat')


class TestStatusTextTooLong(ScreenshotTest):
    """Test that the watchface doesn't crash when the status text is too long."""
    config = {
        'statusContent': 'customtext',
        'statusText': '^_^ ' * 100,
    }
    sgvs = partial(default_entries, 'Flat')


def layout_test_config(config):
    return dict({
        'pointColorLow': '0xFF0000',
        'pointColorHigh': '0xFFAA00',
        'pointColorDefault': '0x0000FF',
        'topOfRange': 160,
        'bottomOfRange': 80,
    }, **config)

class TestLayoutA(ScreenshotTest):
    """Test layout A."""
    sgvs = partial(some_real_life_entries, minutes_old=3)
    config = layout_test_config({
        'layout': 'a',
        'statusContent': 'customtext',
        'statusText': '3.1 U 16 g',
    })


class TestLayoutB(ScreenshotTest):
    """Test layout B."""
    sgvs = partial(some_real_life_entries, minutes_old=3)
    config = layout_test_config({
        'layout': 'b',
        'statusContent': 'customtext',
        'statusText': 'Cln 179 186 187',
        'pointShape': 'rectangle',
        'pointColorLow': '0xFF00AA',
        'pointColorHigh': '0x0000AA',
        'pointColorDefault': '0x00AAAA',
    })


class TestLayoutC(ScreenshotTest):
    """Test layout C."""
    sgvs = partial(some_real_life_entries, minutes_old=3)
    config = layout_test_config({
        'layout': 'c',
        'statusContent': 'customtext',
        'statusText': 'Sat Nov 5',
        'batteryAsNumber': True,
    })


class TestLayoutD(ScreenshotTest):
    """Test layout D."""
    sgvs = partial(some_real_life_entries, minutes_old=3)
    config = layout_test_config({
        'layout': 'd',
        'pointShape': 'circle',
        'pointWidth': 5,
        'pointRightMargin': 2,
    })


class TestLayoutE(ScreenshotTest):
    """Test layout E."""
    sgvs = partial(some_real_life_entries, minutes_old=3)
    config = layout_test_config({
        'layout': 'e',
        'pointWidth': 2,
        'pointMargin': -1,
        'statusContent': 'customtext',
        'statusText': 'Extra long text. This example uses point width 2 and margin -1 to view 9 hrs.',
    })


class TestLayoutCustom(ScreenshotTest):
    """Test the default custom layout."""
    sgvs = some_real_life_entries
    config = layout_test_config({
        'layout': 'custom',
        'customLayout': BASE_CONFIG['customLayout'],
        'statusContent': 'customtext',
        'statusText': 'You are marvelous. The gods wait to delight in you.'
    })


class BaseBatteryLocInStatusTest(ScreenshotTest):
    status_props = None
    status_text = None

    @property
    def __test__(self):
        return not self.__class__ == BaseBatteryLocInStatusTest

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['e'])
        layout['batteryLoc'] = 'statusRight'
        layout['recencyLoc'] = 'none'
        mutate_element(layout, 'STATUS_BAR_ELEMENT', self.status_props)
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': self.status_text,
        }

    sgvs = partial(default_entries, 'FortyFiveDown')


class TestBatteryLocInStatusAlignedWithLastLineOfText(BaseBatteryLocInStatusTest):
    """Test that the battery is aligned to the bottom line of text in the status bar."""
    status_props = {'height': 28}
    status_text = 'Battery is level with last completely visible line of text'


class TestBatteryLocInStatusMinimumPadding(BaseBatteryLocInStatusTest):
    """Test that the battery has a minimum bottom padding."""
    status_props = {'height': 21, 'bottom': True}
    status_text = 'Should not be flush against the bottom'


class TestBatteryAsNumber(ScreenshotTest):
    sgvs = partial(default_entries, 'FortyFiveUp')
    config = {
        'layout': 'a',
        'statusContent': 'customtext',
        'statusText': 'battery ------>',
        'batteryAsNumber': True,
    }

class BaseDynamicTimeFontTest(ScreenshotTest):
    sgvs = partial(default_entries, 'Flat')
    time_height = None

    @property
    def __test__(self):
        return not self.__class__ == BaseDynamicTimeFontTest

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['e'])
        mutate_element(layout, 'TIME_AREA_ELEMENT', {
            'black': True,
            'height': self.time_height,
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'time height: %s%%' % self.time_height
        }

class TestDynamicTimeFont18(BaseDynamicTimeFontTest):
    time_height = 18

class TestDynamicTimeFont14(BaseDynamicTimeFontTest):
    time_height = 14

class TestDynamicTimeFont10(BaseDynamicTimeFontTest):
    time_height = 10

class TestDynamicTimeFont6(BaseDynamicTimeFontTest):
    time_height = 6

class TestBasalGraph(ScreenshotTest):
    config = {
        'layout': 'd',
        'basalGraph': True,
        'basalHeight': 20,
    }
    sgvs = some_real_life_entries
    profile = partial(profile_with_one_basal, 0.5)
    def treatments(self):
        dates = default_dates_as_iso(offset=-150)
        return [
            {'created_at': dates[0], 'duration': 30, 'absolute': 1},
            {'created_at': dates[9], 'duration': 30, 'absolute': 1},
            {'created_at': dates[16], 'duration': 30, 'absolute': 1},
            {'created_at': dates[18], 'duration': 30, 'absolute': 0.8},
            {'created_at': dates[25], 'duration': 30, 'absolute': 0},
            {'created_at': dates[35], 'duration': 30, 'absolute': 0.2},
            {'created_at': dates[48], 'duration': 30, 'absolute': 0.05},
        ]

class TestPointsCircleAlignment(ScreenshotTest):
    """Test the vertical alignment of circular points, including trimmed values."""
    config = {
        'layout': 'd',
        'topOfGraph': 250,
        'topOfRange': 180,
        'bottomOfRange': 80,
        'bottomOfGraph': 40,
        'hGridlines': 50,
        'pointShape': 'circle',
        'pointWidth': 11,
        'pointMargin': 4,
        'pointRightMargin': 5,
        'plotLine': True,
        'plotLineWidth': 3,
    }
    sgvs = partial(sgvs_from_array, [300, 250, 200, 180, 150, 100, 80, 50, 30])

class TestPointsMissingWithLine(ScreenshotTest):
    """Test that the line is drawn as expected when SGV values are missing."""
    config = {
        'layout': 'd',
        'pointShape': 'circle',
        'pointWidth': 9,
        'pointMargin': 3,
        'pointRightMargin': 0,
        'plotLine': True,
        'plotLineWidth': 1,
    }
    sgvs = partial(sgvs_from_array, [100, 150, 0, 0, 85, 0, 85, 0, 30, 85, 0, 230])

class TestPointsBarelyOnScreen(ScreenshotTest):
    config = {
        'layout': 'd',
        'pointShape': 'rectangle',
        'pointWidth': 9,
        'pointRectHeight': 9,
        'pointMargin': 6,
        'pointRightMargin': 0,
        'plotLine': True,
        'plotLineWidth': 1,
    }
    sgvs = partial(sgvs_from_array, [200 - 12 * i + (i ** 2) for i in range(10)])

class TestPointsBarelyOffScreen(TestPointsBarelyOnScreen):
    @property
    def config(self):
        config = super(TestPointsBarelyOffScreen, self).config.copy()
        config['pointRightMargin'] += 1
        return config

class TestPointsNegativeMargin(ScreenshotTest):
    config = {
        'layout': 'd',
        'pointShape': 'rectangle',
        'pointWidth': 19,
        'pointRectHeight': 19,
        'pointMargin': -9,
        'pointRightMargin': 0,
        'plotLine': False,
    }
    sgvs = partial(sgvs_from_array, range(230, 50, -15))

class TestPointsMarginsWithTreatments(ScreenshotTest):
    """Test that boluses and basals are left-shifted when there is a margin, and the leftmost point's basal extends to the left edge."""
    config = {
        'layout': 'd',
        'pointShape': 'rectangle',
        'pointWidth': 9,
        'pointRectHeight': 13,
        'pointMargin': 5,
        'pointRightMargin': 15,
        'plotLine': False,
        'bolusTicks': True,
        'basalGraph': True,
        'basalHeight': 20,
    }
    sgvs = partial(sgvs_from_array, range(200, 110, -10))
    profile = partial(profile_with_one_basal, 0.5)
    def treatments(self):
        return some_fake_temp_basals() + some_fake_boluses()

class TestPointsBolusesDefault(ScreenshotTest):
    """Test that bolus ticks are left-aligned with width 2 by default."""
    config = {
        'layout': 'd',
        'bolusTicks': True,
    }
    sgvs = some_real_life_entries
    treatments = some_fake_boluses

class TestPointsBolusesCenteredEven(ScreenshotTest):
    """Test that bolus ticks are center-aligned with width 2 for even-width points."""
    config = {
        'layout': 'd',
        'bolusTicks': True,
        'pointWidth': 6,
    }
    sgvs = some_real_life_entries
    treatments = some_fake_boluses


class TestPointsBolusesCenteredOdd(ScreenshotTest):
    """Test that bolus ticks are center-aligned with width 3 for odd-width points."""
    config = {
        'layout': 'a',
        'bolusTicks': True,
        'pointShape': 'circle',
        'pointWidth': 7,
        'pointRightMargin': 1,
    }
    sgvs = some_real_life_entries
    treatments = some_fake_boluses

def with_no_lines(config):
    return dict(config, **{
        'layout': 'd',
        'bottomOfRange': 20,
        'topOfRange': 400,
        'hGridlines': 0,
    })

class TestPointsPresetA(ScreenshotTest):
    config = with_no_lines(CONSTANTS['POINT_STYLES']['a'])
    sgvs = some_real_life_entries

class TestPointsPresetB(ScreenshotTest):
    config = with_no_lines(CONSTANTS['POINT_STYLES']['b'])
    sgvs = some_real_life_entries

class TestPointsPresetC(ScreenshotTest):
    config = with_no_lines(CONSTANTS['POINT_STYLES']['c'])
    sgvs = some_real_life_entries

class TestPointsPresetD(ScreenshotTest):
    config = with_no_lines(CONSTANTS['POINT_STYLES']['d'])
    sgvs = some_real_life_entries

class TestPointsColor(ScreenshotTest):
    config = {
        'topOfGraph': 200,
        'topOfRange': 150,
        'bottomOfRange': 100,
        'bottomOfGraph': 80,
        'layout': 'd',
        'pointShape': 'circle',
        'pointWidth': 7,
        'pointMargin': 4,
        'pointRightMargin': 0,
        'plotLine': True,
        'plotLineWidth': 3,
        'pointColorDefault': '0x00AA00',
        'pointColorHigh': '0xFFAA00',
        'pointColorLow': '0xFF0000',
        'plotLineIsCustomColor': False,
        'plotLineColor': '0x000000',
    }
    sgvs = partial(sgvs_from_array, [163, 162, 160, 155, 150, 145, 125, 110, 102, 100, 95, 90, 88])

class TestPointsColorLineWithMissingPoints(TestPointsColor):
    sgvs = partial(sgvs_from_array, [130, 160, 0, 140, 0, 0, 120, 0, 180, 0, 90, 0, 120])

class TestPointsColorCustomLine(TestPointsColor):
    config = dict(TestPointsColor.config, **{
        'plotLineIsCustomColor': True,
        'plotLineColor': '0x5555FF',
    })

STATUS_RECENCY_TEST_CONFIG = {
    'statusMinRecencyToShowMinutes': 10,
    'statusMaxAgeMinutes': 30,
    'statusContent': 'rigbattery',
}

def uploader_battery_devicestatus(min_ago):
    def devicestatus(self):
        return [{
            'uploaderBattery': 85,
            'created_at': iso_date(datetime.now() - timedelta(minutes=min_ago))
        }]
    return devicestatus

class TestStatusRecencyHiddenBeforeMinAge(ScreenshotTest):
    """Test that if the min status recency is set to 10 minutes, it's not reported until it says 11 minutes."""
    config = STATUS_RECENCY_TEST_CONFIG
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=10.2)

class TestStatusRecencyShownAfterMinAge(ScreenshotTest):
    config = STATUS_RECENCY_TEST_CONFIG
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=11)

class TestStatusHiddenAfterMaxAge(ScreenshotTest):
    config = STATUS_RECENCY_TEST_CONFIG
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=31)

class TestStatusRecencyOverOneHour(ScreenshotTest):
    config = dict(
        STATUS_RECENCY_TEST_CONFIG,
        statusMaxAgeMinutes=9999,
    )
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=129)

class TestStatusRecencyFormatColonLeft(ScreenshotTest):
    config = dict(
        STATUS_RECENCY_TEST_CONFIG,
        statusRecencyFormat='colonLeft',
    )
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=12)

class TestStatusRecencyFormatBracketRight(ScreenshotTest):
    config = dict(
        STATUS_RECENCY_TEST_CONFIG,
        statusRecencyFormat='bracketRight',
    )
    sgvs = some_real_life_entries
    devicestatus = uploader_battery_devicestatus(min_ago=12)

class TestRecencyLargePieGraphBottomLeft(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=2)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        layout.update({
          'recencyLoc': 'graphBottomLeft',
          'recencyStyle': 'largePie',
          'recencyColorCircle': '0x00FFFF',
          'recencyColorText': '0x5555FF',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
        }

class TestRecencyMediumRingTimeBottomRight(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=1)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        mutate_element(layout, 'TIME_AREA_ELEMENT', {'height': 30})
        layout.update({
          'recencyLoc': 'timeBottomRight',
          'recencyStyle': 'mediumRing',
          'recencyColorCircle': '0x000055',
          'recencyColorText': '0x005500',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'a b c d e f g h i j',
        }

class TestRecencyMediumPieStatusBottomRight(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=3)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['a'])
        mutate_element(layout, 'STATUS_BAR_ELEMENT', {'black': True, 'height': 27})
        layout.update({
          'batteryLoc': 'none',
          'recencyLoc': 'statusBottomRight',
          'recencyStyle': 'mediumPie',
          'recencyColorCircle': '0x5555FF',
          'recencyColorText': '0xFF0000',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'a b c d e f g h i j\nk l m n o p q r s'
        }

class TestRecencySmallNoCircleStatusTopRight(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=4)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['a'])
        mutate_element(layout, 'STATUS_BAR_ELEMENT', {'black': True, 'height': 27})
        layout.update({
          'batteryLoc': 'none',
          'recencyLoc': 'statusTopRight',
          'recencyStyle': 'smallNoCircle',
          'recencyColorText': '0xFFFFFF',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'a b c d e f g h i j\nk l m n o p q r s'
        }

class TestRecencyLongTextLeftAligned(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=87)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        mutate_element(layout, 'TIME_AREA_ELEMENT', {'height': 30})
        layout.update({
          'batteryLoc': 'timeTopLeft',
          'timeAlign': 'right',
          'recencyLoc': 'timeBottomLeft',
          'recencyStyle': 'mediumRing',
          'recencyColorCircle': '0x000055',
          'recencyColorText': '0x00AA00',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
        }

class TestRecencyLongTextRightAligned(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=87)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        mutate_element(layout, 'TIME_AREA_ELEMENT', {'height': 30})
        layout.update({
          'batteryLoc': 'timeBottomRight',
          'recencyLoc': 'timeTopRight',
          'recencyStyle': 'largeRing',
          'recencyColorText': '0xFF0000',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
        }

class TestRecencyStatusBarVerticallyCentered(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=1)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        mutate_element(layout, 'BG_ROW_ELEMENT', {'black': True})
        mutate_element(layout, 'STATUS_BAR_ELEMENT', {'enabled': True, 'height': 15})
        layout.update({
          'recencyLoc': 'statusTopRight',
          'recencyStyle': 'mediumPie',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'statusContent': 'customtext',
            'statusText': 'a b c d e f g h i'
        }

class TestRecencySuperOld(ScreenshotTest):
    # TODO: make this test not flaky (sometimes icon position is off by one pixel)
    __test__ = False

    def sgvs(self):
        return [some_real_life_entries(minutes_old=999)[0]]

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        layout.update({
          'connStatusLoc': 'graphBottomLeft',
          'recencyLoc': 'graphBottomLeft',
          'recencyStyle': 'largePie',
          'recencyColorCircle': '0x00FFFF',
          'recencyColorText': '0x5555FF',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
        }

class TestRecencyConnStatusBottomLeftWithBasal(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=9)

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        layout.update({
          'connStatusLoc': 'graphBottomLeft',
          'recencyLoc': 'graphBottomLeft',
          'recencyStyle': 'mediumNoCircle',
          'recencyColorText': '0x55AA00',
        })
        return {
            'layout': 'custom',
            'customLayout': layout,
            'basalGraph': True,
            'basalHeight': 20,
        }

class TestNiceLayout(ScreenshotTest):
    sgvs = partial(some_real_life_entries, minutes_old=3)

    @property
    def config(self):
        layout = {
            'elements': [
                {'el': 3, 'enabled': True, 'width': 100, 'height': 23, 'black': False, 'bottom': True, 'right': False},
                {'el': 0, 'enabled': True, 'width': 100, 'height': 0, 'black': False, 'bottom': True, 'right': False},
                {'el': 1, 'enabled': False, 'width': 100, 'height': 0, 'black': False, 'bottom': False, 'right': False},
                {'el': 2, 'enabled': True, 'width': 100, 'height': 16, 'black': True, 'bottom': False, 'right': False},
                {'el': 4, 'enabled': True, 'width': 100, 'height': 23, 'black': False, 'bottom': False, 'right': False}
            ],
            'batteryLoc': 'timeTopRight',
            'timeAlign': 'left',
            'connStatusLoc': 'graphBottomLeft',
            'recencyLoc': 'statusTopRight',
            'recencyStyle': 'mediumPie',
            'recencyColorCircle': '0xAA55FF',
            'recencyColorText': '0xFFFFFF',
        }
        return {
            'layout': 'custom',
            'customLayout': layout,
            'topOfGraph': 251,
            'topOfRange': 160,
            'bottomOfRange': 80,
            'bottomOfGraph': 51,
            'pointColorLow': '0xFF0000',
            'pointColorHigh': '0xFFAA00',
            'pointColorDefault': '0x0000FF',
            'statusContent': 'customtext',
            'statusText': '3.1 U 16 g',
        }

def predictions_config(config=None):
    return dict({
        'predictEnabled': True,
        'predictSource': 'loop',
        'predictMaxLength': 48,
        'layout': 'd',
        'pointWidth': 5,
        'pointRectHeight': 5,
    }, **(config or {}))

class BasePredictionsTest(ScreenshotTest):
    sgv_min_ago = None
    predictions_min_ago = None
    config = predictions_config()

    sgv_series = [150, 175, 150, 175, 150, 125]
    predictions = [150, 125, 100, 75, 100, 125]

    def sgvs(self):
        return sgvs_from_array(self.sgv_series, offset=(-60 * self.sgv_min_ago))

    def devicestatus(self):
        return loop_devicestatus(self.predictions, self.predictions_min_ago)

    @property
    def __test__(self):
        return not self.__class__ == BasePredictionsTest

class TestPredictionsDefault(BasePredictionsTest):
    sgv_min_ago = 3
    predictions_min_ago = 2

class TestPredictionsSGVNotQuiteStale(BasePredictionsTest):
    sgv_min_ago = 7
    predictions_min_ago = 7

class TestPredictionsSGVBarelyStale(BasePredictionsTest):
    sgv_min_ago = 9
    predictions_min_ago = 9

class TestPredictionsSGVStalePredictionFresh(BasePredictionsTest):
    sgv_min_ago = 18
    predictions_min_ago = 1

class TestPredictionsSGVFreshPredictionStale(BasePredictionsTest):
    sgv_min_ago = 2
    predictions_min_ago = 12

class TestPredictionsWithAGap(BasePredictionsTest):
    sgv_min_ago = 2
    predictions_min_ago = -10

class TestPredictionsNegativeMargin(BasePredictionsTest):
    sgv_min_ago = 2
    predictions_min_ago = 2
    config = predictions_config({
        'pointRectHeight': 5,
        'pointWidth': 5,
        'pointMargin': -2,
    })

class TestPredictionsColors(BasePredictionsTest):
    sgv_min_ago = 2
    predictions_min_ago = 2
    predictions = range(300, 25, -25)
    config = predictions_config({
        'predictColorDefault': '0x00AA00',
        'predictColorHigh': '0xFFAA00',
        'predictColorLow': '0xFF0055',
    })

def boluses_basals_config():
    layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
    layout.update({
        'recencyStyle': 'mediumRing',
        'recencyColorText': '0x000000',
        'recencyColorCircle': '0x005555',
    })
    mutate_element(layout, 'TIME_AREA_ELEMENT', {'enabled': True, 'height': 27})
    return {
        'layout': 'custom',
        'customLayout': layout,
        'basalGraph': True,
        'basalHeight': 20,
        'bolusTicks': True,
        'pointColorDefault': '0x0000FF',
        'predictEnabled': True,
        'predictMaxLength': 48,
        'pointWidth': 3,
        'pointMargin': -1,
    }

class TestPredictionsWithBolusesAndBasals(ScreenshotTest):
    def sgvs(self):
        return sgvs_from_array(
            [102, 97, 94, 93, 94, 96, 97, 96, 98, 101, 104, 106, 104, 105, 106, 108, 112, 113, 115, 116, 117, 119, 121, 122, 126, 129, 131, 133, 135, 136, 138, 141, 143, 145, 146, 148, 149, 152, 153, 152, 153, 153, 153, 152, 152, 150, 147, 148, 146, 148, 129, 137, 137, 129, 127, 126, 98, 104, 87, 85, 85, 83, 90, 108, 110, 117, 123, 129, 139, 130, 145, 142, 147, 148, 151, 150, 152, 156, 163, 167, 165, 182, 171, 185],
            offset=(-3 * 60)
        )

    def devicestatus(self):
        return loop_devicestatus(
            [102, 102, 106, 109, 111, 111, 111, 110, 108, 107, 106, 105, 105, 106, 107, 109, 110, 112, 114, 116, 118, 120, 123, 126, 128, 131, 132, 134, 135, 136, 137, 137, 137, 137, 137, 138, 139, 140, 140, 140, 141, 140, 141, 143, 144, 144, 144, 144],
            min_ago=1
        )

    def treatments(self):
        ts = []
        ts += boluses_from_array([
            (-1558, 5),
            (-3683, 3.5),
            (-21357, 1.5)
        ])
        ts += basals_from_array([
            (-190, 30, 3.575),
            (-462, 30, 2.85),
            (-1058, 0, 0),
            (-1987, 30, 0),
            (-3159, 30, 0),
            (-4060, 0, 0),
            (-4360, 30, 0),
            (-10726, 0, 0),
            (-11028, 30, 1.375),
            (-11602, 30, 1.45),
            (-11628, 0, 0),
            (-11928, 30, 1.4),
            (-12828, 0, 0),
            (-13125, 30, 1.55),
            (-13685, 30, 1.775),
            (-14286, 0, 0),
        ])
        return ts

    profile = partial(profile_with_one_basal, 0.65)

    config = boluses_basals_config()

class TestPredictionsMaxLength(TestPredictionsWithBolusesAndBasals):
    config = dict(boluses_basals_config(), predictMaxLength=18)

class TestPredictionsWithMultipleSeries(ScreenshotTest):
    def sgvs(self):
        return sgvs_from_array(
            [77, 77, 78, 79, 80, 82, 83, 84, 84, 84, 83, 85, 84, 84, 86, 87, 89, 91, 92],
            offset=(-3 * 60)
        )

    def devicestatus(self):
        return [
            {
                'created_at': iso_date(datetime.now()),
                'device': 'openaps://indy-e1',
                'openaps': {
                    'suggested': {
                        'predBGs': {
                            'COB': [77, 76, 75, 75, 76, 77, 79, 82, 85, 89, 92, 96, 99, 103, 107, 110, 114, 117, 120, 124, 126, 129, 132, 134, 136, 138, 139, 141, 142, 143, 144, 145, 146, 147, 147, 148, 148, 149, 149, 150, 150, 151],
                            'aCOB': [77, 83, 88, 93, 98, 102, 106, 110, 112, 114, 116, 119, 121, 124, 126, 128, 131, 133, 135, 137, 139, 140, 142, 143, 144, 145, 146, 147, 147, 148],
                            'IOB': [77, 75, 75, 74, 75, 76, 77, 79, 81, 84, 86, 89, 91, 93, 96, 98, 101, 103, 105, 107, 109, 110, 112, 113, 114, 115, 116, 117, 117, 118],
                        },
                    }
                },
            },
            {
                'created_at': iso_date(datetime.now() - timedelta(minutes=5)),
                'device': 'openaps://indy-e1',
                'openaps': {'suggested': {}}
            }
        ]

    @property
    def config(self):
        layout = copy.deepcopy(CONSTANTS['LAYOUTS']['d'])
        layout.update({
            'recencyColorText': '0x000000',
            'recencyColorCircle': '0xAAFFAA',
            'recencyLoc': 'timeTopLeft',
            'batteryLoc': 'timeBottomLeft',
            'timeAlign': 'right',
        })
        mutate_element(layout, 'TIME_AREA_ELEMENT', {'enabled': True, 'bottom': False})
        mutate_element(layout, 'BG_ROW_ELEMENT', {'bottom': True})
        layout['elements'] = [
            [e for e in layout['elements'] if CONSTANTS['ELEMENTS'][e['el']] == el][0]
            for el in
            ('BG_ROW_ELEMENT', 'GRAPH_ELEMENT', 'TIME_AREA_ELEMENT')
        ]
        return {
            'layout': 'custom',
            'customLayout': layout,
            'pointColorDefault': '0x0000FF',
            'pointColorLow': '0x0000FF',
            'predictEnabled': True,
            'predictSource': 'openaps',
            'predictMaxLength': 30,
            'hGridlines': 0,
            'bottomOfGraph': 50,
            'topOfGraph': 225,
            'bottomOfRange': 80,
            'topOfRange': 160,
        }
