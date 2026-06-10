# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import pytest
from femora.core.model import Model
from femora.core.time_series_base import TimeSeries

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
def manager():
    mesh_maker = Model()
    mesh_maker.clear_model()
    yield mesh_maker.time_series
    mesh_maker.clear_model()

def test_time_series_sequential_tagging(manager):
    ts1 = manager.add(DummyTimeSeries('Constant'))
    ts2 = manager.add(DummyTimeSeries('Constant'))
    ts3 = manager.add(DummyTimeSeries('Constant'))
    assert ts1.tag == 1
    assert ts2.tag == 2
    assert ts3.tag == 3

def test_time_series_custom_start_tag(manager):
    manager.set_tag_start(100)
    ts1 = manager.add(DummyTimeSeries('Constant'))
    ts2 = manager.add(DummyTimeSeries('Constant'))
    assert ts1.tag == 100
    assert ts2.tag == 101

def test_time_series_tag_reset(manager):
    manager.add(DummyTimeSeries('Constant'))
    manager.clear()
    manager.set_tag_start(50)
    ts2 = manager.add(DummyTimeSeries('Constant'))
    assert ts2.tag == 50

def test_time_series_set_tag_start_after_some_created(manager):
    manager.set_tag_start(1)
    ts1 = manager.add(DummyTimeSeries('Constant'))
    ts2 = manager.add(DummyTimeSeries('Constant'))
    manager.set_tag_start(200)
    # After retag, ts1 and ts2 should be 200, 201
    assert ts1.tag == 200
    assert ts2.tag == 201
    ts3 = manager.add(DummyTimeSeries('Constant'))
    assert ts3.tag == 202
    manager.set_tag_start(10)
    # After retag, all tags are reassigned starting from 10
    assert ts1.tag == 10
    assert ts2.tag == 11
    assert ts3.tag == 12
    ts4 = manager.add(DummyTimeSeries('Constant'))
    assert ts4.tag == 13

def test_time_series_tagging_with_deletions_and_start_tag_change(manager):
    manager.set_tag_start(10)
    ts1 = manager.add(DummyTimeSeries('Constant'))  # tag 10
    ts2 = manager.add(DummyTimeSeries('Constant'))  # tag 11
    ts3 = manager.add(DummyTimeSeries('Constant'))  # tag 12
    assert ts1.tag == 10
    assert ts2.tag == 11
    assert ts3.tag == 12
    manager.remove(ts2.tag)
    # After removal, tags are reassigned: ts1=10, ts3=11
    assert ts1.tag == 10
    assert ts3.tag == 11
    manager.set_tag_start(104)
    # After retag, ts1=104, ts3=105
    assert ts1.tag == 104
    assert ts3.tag == 105
    ts4 = manager.add(DummyTimeSeries('Constant'))  # should get tag 106
    assert ts4.tag == 106
    manager.remove(ts1.tag)
    manager.remove(ts3.tag)
    manager.set_tag_start(202)
    # Existing ts4 is retagged to 202, so the next tag should be 203.
    ts5 = manager.add(DummyTimeSeries('Constant'))
    assert ts5.tag == 203
