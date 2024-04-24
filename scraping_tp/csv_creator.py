"""Module providing a CsvCreator."""

from __future__ import annotations

import csv
import json
import os
import shutil
import time
import traceback
import urllib.parse
from abc import abstractmethod
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests_file import FileAdapter


class CsvCreator:
    """Class for outputting Csv."""

    TIMEZONE = timezone(timedelta(hours=+9), 'JST')
    CSV_HEADER = ['社名', '番号', '住所', 'URL', '検索キーワード', '検索地域', '日時']

    def __init__(self, **kwargs):
        self.areas = kwargs['areas']
        self.keyword = kwargs['keyword']
        self.filename = kwargs['filename']
        self.encoding = kwargs['encoding']
        self.uri = kwargs['uri']
        self.timeout = kwargs['timeout']
        self.retry = kwargs['retry']

    def create(self) -> CsvCreator:
        """Output CSV file."""
        try:
            self._setUp()
            self._write_csv()
            self._tearDown()
        except Exception:  # pylint: disable=broad-exception-caught
            traceback.print_exc()
            self._on_error()

    def _now(self) -> datetime:
        """Returns the current time."""
        return datetime.now(self.TIMEZONE)

    def _now_str(self) -> str:
        """Returns the current time as a string."""
        return self._now().strftime('%Y年%m月%d日 %H:%M:%S')

    @abstractmethod
    def _setUp(self):
        """setUp."""

    @abstractmethod
    def _tearDown(self):
        """tearDown."""

    def _on_error(self):
        """Cleaning up after an error."""
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    @abstractmethod
    def _write_csv(self):
        """Write to CSV file"""


class CsvCreatorFactory:
    """Factory class for CsvCreator."""

    @staticmethod
    def create_csv_creator(**kwargs) -> CsvCreator:
        """Returns an instance of CsvCreator."""

        lib = kwargs['lib']
        if lib == 'requests':
            return RequestsCsvCreator(**kwargs)
        if lib == 'selenium':
            # return SeleniumCsvCreator(**kwargs)
            pass
        raise ValueError(f'Unknown type: {lib}')


class RequestsCsvCreator(CsvCreator):
    """CsvCreator for requests."""

    # Override
    def _setUp(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        if self.uri.startswith('file:///opt/python/static/html/'):
            shutil.unpack_archive('static/html.zip', 'static/html')

    # Override
    def _tearDown(self):
        if os.path.isdir('static/html'):
            shutil.rmtree('static/html')

    def __beautiful_soup_instance(self, url, from_param):
        session = requests.Session()
        user_agent = UserAgent().chrome

        if url.startswith('http'):
            target_url = f'{url}&from={from_param}'
            res = session.get(target_url, headers={'User-Agent': user_agent, 'Content-Type': 'text/html'})
            return BeautifulSoup(res.content.decode('utf-8'), 'html.parser')

        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        filename, file_extension = os.path.splitext(original_filename)
        if from_param:
            filename = filename.split('_')[0] + '_' + filename.split('_')[1] + '_' + str(from_param).zfill(2) + file_extension
            target_url = url.replace(original_filename, filename)
        else:
            target_url = url

        session.mount('file://', FileAdapter())
        res = session.get(target_url, headers={'User-Agent': user_agent})
        with open(target_url.replace('file://', ''), mode='r', encoding='utf-8') as file:
            return BeautifulSoup(file, 'html.parser')

    # Override
    def _write_csv(self):
        print('INFO ', self._now(), f'{self.keyword}のCSVを出力します')
        keyword_param = urllib.parse.quote(self.keyword)
        page = 1
        company_count = 0
        PER_PAGE = 20

        with open(self.filename, 'w', encoding=self.encoding, newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.CSV_HEADER)

        for area in self.areas:
            area_param = urllib.parse.quote(area)

            while True:
                from_param = (page - 1) * PER_PAGE
                search_url = f'{self.uri}/keyword?areaword={area_param}&keyword={keyword_param}&sort=01'
                soup = self.__beautiful_soup_instance(search_url, from_param=from_param)
                json_element = soup.find('script', type='application/ld+json')
                if not json_element:
                    print('INFO ', self._now(), f'{self.keyword}({area})を{company_count}件出力しました')
                    break

                json_ld = json.loads(json_element.text)
                for element in json_ld['itemListElement']:
                    row = []
                    item = element.get('item', {})
                    row.append(item['name'])  # 社名
                    row.append(item['telephone'])  # 番号
                    address = item.get('address', {})
                    row.append(f"{address['addressLocality']}{address.get('streetAddress', '')}")  # 住所
                    row.append(item['url'])
                    row.append(self.keyword)
                    row.append(area)
                    row.append(self._now_str())
                    company_count += 1
                    with open(self.filename, 'a', encoding=self.encoding, newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row)

                if len(json_ld['itemListElement']) < PER_PAGE:
                    print('INFO ', self._now(), f'{self.keyword}({area})を{company_count}件出力しました')
                    page = 1
                    company_count = 0
                    time.sleep(3)
                    break

                page += 1
                time.sleep(3)

        print('INFO ', self._now(), f'{self.keyword}のCSVを出力しました')
