import pytest
from femora.components.TimeSeries.timeSeriesBase import TimeSeries

class DummyTimeSeries(TimeSeries):
    def __init__(self, series_type):
        super().__init__(series_type)
    def to_tcl(self):
        return ""
    @staticmethod
    def get_Parameters():
        return []
    def get_values(self):
        return {}
    def update_values(self, **kwargs):
        pass
    @staticmethod
    def validate(**kwargs):
        return {}

@pytest.fixture(autouse=True)
def clear_time_series():
    TimeSeries.reset()
    yield
    TimeSeries.reset()

def test_time_series_sequential_tagging():
    ts1 = DummyTimeSeries('Constant')
    ts2 = DummyTimeSeries('Constant')
    ts3 = DummyTimeSeries('Constant')
    assert ts1.tag == 1
    assert ts2.tag == 2
    assert ts3.tag == 3

def test_time_series_custom_start_tag():
    TimeSeries.set_tag_start(100)
    ts1 = DummyTimeSeries('Constant')
    ts2 = DummyTimeSeries('Constant')
    assert ts1.tag == 100
    assert ts2.tag == 101

def test_time_series_tag_reset():
    ts1 = DummyTimeSeries('Constant')
    TimeSeries.reset()
    TimeSeries.set_tag_start(50)
    ts2 = DummyTimeSeries('Constant')
    assert ts2.tag == 50

def test_time_series_set_tag_start_after_some_created():
    TimeSeries.set_tag_start(1)
    ts1 = DummyTimeSeries('Constant')
    ts2 = DummyTimeSeries('Constant')
    TimeSeries.set_tag_start(200)
    # After retag, ts1 and ts2 should be 200, 201
    assert ts1.tag == 200
    assert ts2.tag == 201
    ts3 = DummyTimeSeries('Constant')
    assert ts3.tag == 202
    TimeSeries.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert ts1.tag == 10
    assert ts2.tag == 11
    assert ts3.tag == 12
    ts4 = DummyTimeSeries('Constant')
    assert ts4.tag == 13

def test_time_series_tagging_with_deletions_and_start_tag_change():
    TimeSeries.set_tag_start(10)
    ts1 = DummyTimeSeries('Constant')  # tag 10
    ts2 = DummyTimeSeries('Constant')  # tag 11
    ts3 = DummyTimeSeries('Constant')  # tag 12
    assert ts1.tag == 10
    assert ts2.tag == 11
    assert ts3.tag == 12
    TimeSeries.remove_time_series(ts2.tag)
    # After removal, tags are reassigned: ts1=10, ts3=11
    assert ts1.tag == 10
    assert ts3.tag == 11
    TimeSeries.set_tag_start(104)
    # After retag, ts1=104, ts3=105
    assert ts1.tag == 104
    assert ts3.tag == 105
    ts4 = DummyTimeSeries('Constant')  # should get tag 106
    assert ts4.tag == 106
    TimeSeries.remove_time_series(ts1.tag)
    TimeSeries.remove_time_series(ts3.tag)
    TimeSeries.set_tag_start(202)
    # No time series left, next should be 202
    ts5 = DummyTimeSeries('Constant')  # should get tag 202 