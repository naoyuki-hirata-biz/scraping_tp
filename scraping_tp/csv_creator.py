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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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
            return SeleniumCsvCreator(**kwargs)
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
            res = session.get(target_url, headers={'User-Agent': user_agent, 'Content-Type': 'text/html'}, timeout=30)
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
                company_elements = []
                row_count = 0
                if json_element:
                    json_ld = json.loads(json_element.text)
                    row_count = self._write_csv_by_json(area=area, json=json_ld)

                else:
                    company_elements = soup.select(
                        'div.dev-only-search-result-itemContainer[role="listitem"],div.dev-only-search-searchResultsBottom-itemContainer[role="listitem"]'
                    )
                    row_count = self._write_csv_by_html(area=area, elements=company_elements)

                company_count += row_count
                if row_count < PER_PAGE:
                    print('INFO ', self._now(), f'{self.keyword}({area})を{company_count}件出力しました')
                    page = 1
                    company_count = 0
                    time.sleep(10)
                    break

                page += 1
                time.sleep(10)

        print('INFO ', self._now(), f'{self.keyword}のCSVを出力しました')

    def _write_csv_by_json(self, area='', json=None) -> int:
        company_count = 0
        if not json:
            return company_count

        for element in json:
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

        return company_count

    def _write_csv_by_html(self, area='', elements=None) -> int:
        company_count = 0
        if not elements:
            return company_count

        for element in elements:
            row = []
            print(element.select_one('p.font_8 a'))
            row.append('')  # 社名
            row.append('')  # 番号
            row.append('')  # 住所
            row.append('')  # URL
            row.append(self.keyword)  # 検索キーワード
            row.append(area)  # 検索地域
            row.append(self._now_str())  # 日時
            company_count += 1
            with open(self.filename, 'a', encoding=self.encoding, newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)

        return company_count


class SeleniumCsvCreator(CsvCreator):
    """CsvCreator for selenium."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.browser = kwargs['browser']
        self.display = None
        self.driver = None
        self.wait = None

    # Override
    def _setUp(self):
        if self.browser == 'chrome':
            service = Service(executable_path='/usr/bin/chromedriver')
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--enable-javascript')
            options.add_argument('----user-agent={UserAgent().chrome}')
            self.driver = webdriver.Chrome(service=service, options=options)
        elif self.browser == 'firefox':
            service = Service(executable_path='/home/dev/.cargo/bin/geckodriver')
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('--enable-javascript')
            options.add_argument('----user-agent={UserAgent().firefox}')
            self.driver = webdriver.Firefox(service=service, options=options)
        else:
            raise ValueError(f'Unknown browser {self.browser}')

        self.wait = WebDriverWait(driver=self.driver, timeout=self.timeout)

        if os.path.isfile(self.filename):
            os.remove(self.filename)
        if self.uri.startswith('file:///opt/python/static/html/'):
            shutil.unpack_archive('static/html.zip', 'static/html')

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
                row = []
                from_param = (page - 1) * PER_PAGE
                search_url = f'{self.uri}/keyword?from={from_param}&areaword={area_param}&keyword={keyword_param}&sort=01'
                self.driver.get(search_url)
                self.wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.dev-only-search-result-itemContainer[role="listitem"]'))
                )
                time.sleep(10)  # 描画が完了するのにタイムラグが有る
                elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.dev-only-search-result-itemContainer[role="listitem"]')
                row_count = 0
                for element in elements:
                    company_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsTop-title > p.font_8 > a')
                    row.append(company_element.text)  # 社名
                    phone_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsTop-phone > p.font_3 > span')
                    row.append(phone_element.text)  # 番号
                    address_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsTop-address > p.font_8 > span')
                    row.append(address_element.text)  # 住所
                    row.append(company_element.get_attribute('href'))  # URL
                    row.append(self.keyword)  # 検索キーワード
                    row.append(area)  # 検索地域
                    row.append(self._now_str)  # 日時
                row_count += len(elements)

                elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 'div.dev-only-search-searchResultsBottom-itemContainer[role="listitem"]'
                )
                for element in elements:
                    company_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsBottom-title > p.font_8 > a')
                    row.append(company_element.text)  # 社名
                    phone_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsBottom-phone > p.font_3 > span')
                    row.append(phone_element.text)  # 番号
                    address_element = element.find_element(By.CSS_SELECTOR, 'div.dev-only-searchResultsBottom-address > p.font_8 > span')
                    row.append(address_element.text)  # 住所
                    row.append(company_element.get_attribute('href'))  # URL
                    row.append(self.keyword)  # 検索キーワード
                    row.append(area)  # 検索地域
                    row.append(self._now_str)  # 日時
                row_count += len(elements)

                company_count += row_count
                with open(self.filename, 'a', encoding=self.encoding, newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(row)

                if row_count < PER_PAGE:
                    print('INFO ', self._now(), f'{self.keyword}({area})を{company_count}件出力しました')
                    page = 1
                    company_count = 0
                    time.sleep(10)
                    break

                page += 1
                time.sleep(10)

        print('INFO ', self._now(), f'{self.keyword}のCSVを出力しました')

    # Override
    def _tearDown(self):
        if os.path.isdir('static/html'):
            shutil.rmtree('static/html')

        self.driver.close()
        self.driver.quit()
