"""Script to export CSV.

usage: scraping_tp.py [-h] --keyword KEYWORD [--lib {requests,selenium}]
                      [--browser {chrome,firefox}] [--timeout TIMEOUT]
                      [--interval INTERVAL]

Usage

optional arguments:
  -h, --help            show this help message and exit
  --keyword KEYWORD     keyword (single word)
  --lib {requests,selenium}
                        use requests or selenium library (default: selenium)
  --browser {chrome,firefox}
                        Browser when using Selenium (default: chrome)
  --timeout TIMEOUT     Timeout time to find the element (seconds) (default: 90)
  --interval INTERVAL   Interval time (seconds) (default: 10)
"""

import argparse

from config import settings
from scraping_tp.csv_creator import CsvCreatorFactory


def get_args():
    """Return arguments."""
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('--keyword', help='keyword (single word)', required=True, type=str)
    parser.add_argument(
        '--lib', help='use requests or selenium library (default: selenium)', choices=['requests', 'selenium'], default='selenium'
    )
    parser.add_argument('--browser', help='Browser when using Selenium (default: chrome)', choices=['chrome', 'firefox'], default='chrome')
    parser.add_argument('--timeout', help='Timeout time to find the element (seconds) (default: 90)', type=int, default=90)
    parser.add_argument('--interval', help='Interval time (seconds) (default: 10)', type=int, default=10)

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
    creator = CsvCreatorFactory().create_csv_creator(**arguments)
    creator.create()


if __name__ == '__main__':
    main()
