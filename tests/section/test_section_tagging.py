import pytest
from femora.components.section.section_base import Section

class DummySection(Section):
    def __init__(self, section_type, section_name, user_name):
        super().__init__(section_type, section_name, user_name)
    @classmethod
    def get_parameters(cls):
        return []
    @classmethod
    def get_description(cls):
        return []
    @classmethod
    def get_help_text(cls):
        return ""
    @classmethod
    def validate_section_parameters(cls, **kwargs):
        return {}
    def get_values(self, keys):
        return {}
    def update_values(self, values):
        pass
    def to_tcl(self):
        return ""

@pytest.fixture(autouse=True)
def clear_sections():
    Section.clear_all_sections()
    yield
    Section.clear_all_sections()

def test_section_sequential_tagging():
    s1 = DummySection('Elastic', 'ElasticSection', 'sec1')
    s2 = DummySection('Elastic', 'ElasticSection', 'sec2')
    s3 = DummySection('Elastic', 'ElasticSection', 'sec3')
    assert s1.tag == 1
    assert s2.tag == 2
    assert s3.tag == 3

def test_section_custom_start_tag():
    Section.set_tag_start(100)
    s1 = DummySection('Elastic', 'ElasticSection', 'secA')
    s2 = DummySection('Elastic', 'ElasticSection', 'secB')
    assert s1.tag == 100
    assert s2.tag == 101

def test_section_tag_reset():
    s1 = DummySection('Elastic', 'ElasticSection', 'secX')
    Section.clear_all_sections()
    Section.set_tag_start(50)
    s2 = DummySection('Elastic', 'ElasticSection', 'secY')
    assert s2.tag == 50

def test_section_set_tag_start_after_some_created():
    Section.set_tag_start(1)
    s1 = DummySection('Elastic', 'ElasticSection', 'sec1')
    s2 = DummySection('Elastic', 'ElasticSection', 'sec2')
    Section.set_tag_start(200)
    s3 = DummySection('Elastic', 'ElasticSection', 'sec3')
    assert s1.tag == 200
    assert s2.tag == 201
    assert s3.tag == 202
    Section.set_tag_start(10)
    s4 = DummySection('Elastic', 'ElasticSection', 'sec4')
    assert s4.tag == 13

def test_section_tagging_with_deletions_and_start_tag_change():
    Section.set_tag_start(10)
    s1 = DummySection('Elastic', 'ElasticSection', 'sec1')  # tag 10
    s2 = DummySection('Elastic', 'ElasticSection', 'sec2')  # tag 11
    s3 = DummySection('Elastic', 'ElasticSection', 'sec3')  # tag 12
    assert s1.tag == 10
    assert s2.tag == 11
    assert s3.tag == 12
    Section.delete_section(s2.tag)
    Section.set_tag_start(102)
    s4 = DummySection('Elastic', 'ElasticSection', 'sec4')  # should get tag 102
    assert s4.tag == 104
    Section.delete_section(s1.tag)
    Section.delete_section(s3.tag)
    Section.set_tag_start(201)
    s5 = DummySection('Elastic', 'ElasticSection', 'sec5')  # should get tag 201
    assert s5.tag == 202 