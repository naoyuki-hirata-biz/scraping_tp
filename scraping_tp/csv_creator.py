"""Module providing a CsvCreator."""

from __future__ import annotations

import csv
import json
import os
import shutil
import time
import traceback
import urllib.parse
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests_file import FileAdapter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


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
        self.records = kwargs['records']
        self.timeout = kwargs['timeout']
        self.retry = kwargs['retry']
        self.driver = None
        self.wait = None

    def create(self) -> CsvCreator:
        """Output CSV file."""
        try:
            self._setUp()
            self._write_csv()
            self._tearDown()
        except Exception:  # pylint: disable=broad-exception-caught
            traceback.print_exc()
            self._on_error()

    def _setUp(self):
        """setUp."""
        service = Service(executable_path='/usr/bin/chromedriver')
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(driver=self.driver, timeout=self.timeout)

        if os.path.isfile(self.filename):
            os.remove(self.filename)
        if self.uri.startswith('file:///opt/python/static/html/'):
            shutil.unpack_archive('static/html.zip', 'static/html')

    def _tearDown(self):
        """tearDown."""
        if os.path.isdir('static/html'):
            shutil.rmtree('static/html')

        self.driver.close()
        self.driver.quit()

    def _on_error(self):
        """Cleaning up after an error."""
        if os.path.isfile(self.filename):
            os.remove(self.filename)

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
        """Write to CSV file"""
        print('INFO ', datetime.now(self.TIMEZONE), f'{self.keyword}のCSVを出力します')
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
                    print('INFO ', datetime.now(self.TIMEZONE), f'{self.keyword}({area})を{company_count}件出力しました')
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
                    now = datetime.now(self.TIMEZONE)
                    row.append(now.strftime('%Y年%m月%d日 %H:%M:%S'))
                    company_count += 1
                    with open(self.filename, 'a', encoding=self.encoding, newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(row)

                if len(json_ld['itemListElement']) < PER_PAGE:
                    print('INFO ', datetime.now(self.TIMEZONE), f'{self.keyword}({area})を{company_count}件出力しました')
                    page = 1
                    company_count = 0
                    time.sleep(3)
                    break

                page += 1
                time.sleep(3)

        print('INFO ', datetime.now(self.TIMEZONE), f'{self.keyword}のCSVを出力しました')
