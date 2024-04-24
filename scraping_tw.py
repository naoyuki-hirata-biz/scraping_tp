"""Script to export CSV.

usage: scraping_tw.py [-h] --keyword KEYWORD [--records RECORDS] [--timeout TIMEOUT] [--retry RETRY]

Usage

optional arguments:
  -h, --help         show this help message and exit
  --keyword KEYWORD  keyword (single word)
  --records RECORDS  Maximum number of records
  --timeout TIMEOUT  Timeout time to find the element (seconds) (default: 90)
  --retry RETRY      Number of retries (default: 3)
"""

import argparse

from config import settings
from scraping_tp.csv_creator import CsvCreator


def get_args():
    """Return arguments."""
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('--keyword', help='keyword (single word)', required=True, type=str)
    parser.add_argument('--records', help='Maximum number of records', type=int)
    parser.add_argument('--timeout', help='Timeout time to find the element (seconds) (default: 90)', type=int, default=90)
    parser.add_argument('--retry', help='Number of retries (default: 3)', type=int, default=3)

    args = parser.parse_args()
    variables = vars(args)
    variables['filename'] = settings.filename
    variables['encoding'] = settings.csv_file_encoding
    variables['uri'] = settings.uri
    variables['areas'] = sum(settings.areas.values(), [])
    return variables


def main():
    """Main processing."""
    arguments = get_args()
    CsvCreator(**arguments).create()


if __name__ == '__main__':
    main()