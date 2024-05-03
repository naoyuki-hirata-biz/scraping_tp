"""
Test for Requests.

Usage:

poetry run python -m pytest tests/test_create_csv_by_requests.py -s

"""

import os

import pytest

from config import settings
from scraping_tp.csv_creator import CsvCreatorFactory, RequestsCsvCreator


class TestCreateCsvByRequests:
    """Test for requests."""

    @pytest.fixture
    def args(self):
        """init arguments."""
        settings.configure(ENV_FOR_DYNACONF='test')
        args = {
            'keyword': '介護',
            'lib': 'requests',
            'timeout': 90,
            'interval': 3,
            'filename': settings.filename,
            'encoding': settings.csv_file_encoding,
            'uri': settings.uri,
            'areas': sum(settings.areas.values(), []),
        }

        if os.path.isfile(args['filename']):
            os.remove(args['filename'])

        return args

    def test_can_create_csv(self, args):
        """Test case to assert that a CSV file is output."""
        creator = CsvCreatorFactory().create_csv_creator(**args)
        assert isinstance(creator, RequestsCsvCreator)
        creator.create()
        assert os.path.isfile(args['filename'])
