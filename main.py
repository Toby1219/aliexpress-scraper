import asyncio
import os
import csv
import json
import sqlite3
import time
import asyncio
from dataclasses import dataclass, asdict, astuple
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from functools import lru_cache, cache
from bs4 import BeautifulSoup

main_path = 'data'
if not os.path.exists(main_path):
    os.mkdir(main_path)
else:
    pass


@dataclass
class AliExpress:
    name: str | None
    price: float | None
    sold: float | None
    product_link: str | None
    shipping: float | None


async def get_browser(*link, p):
    urls = ' '.join(link)
    user_agents = UserAgent()
    header = user_agents.random
    browser = await p.chromium.launch()
    context = await browser.new_context(
        user_agent=header
    )
    page = await context.new_page()
    await page.goto(urls)
    for _ in range(7):
        await page.mouse.wheel(0, 1000)
        time.sleep(2)
    try:
        await page.wait_for_selector('//h1[@class="multi--titleText--nXeOvyr"]')
        html = await page.content()
        return html

    except Exception as e:
        print(f'Error {e}')


def extract_text(soup, tag, sel, value):
    try:
        elem = soup.find(tag, sel).text
        return clean_data(elem)
    except:
        return f'No {value} data'


def extract_list(soup, sel, value):
    try:
        elem = soup.select(sel)
        texts = [x.text for x in elem]
        text = ''.join(texts)
        return clean_data(text)
    except:
        return f'No {value} data'


def clean_data(text):
    chars = ['Phone<!-- --> ', '，tecno<!-- --> ', 'Cellphone<!-- -->', ', NFC<!-- -->', ', NFC']
    for char in chars:
        if char in text:
            value = text.replace(char, '').strip()
            return value
        else:
            return text


async def scraper(html):
    result = []
    result2 = []
    soup = BeautifulSoup(html, 'html5lib')
    div_box = soup.findAll('div', class_='search-item-card-wrapper-gallery')
    print(len(div_box))
    for item in div_box:
        name = extract_text(item, 'h1', {"class": "multi--titleText--nXeOvyr"}, 'Name')
        price = extract_list(item, 'div.multi--price-sale--U-S0jtj > span', 'Price')
        sales = extract_list(item, 'span.multi--trade--Ktbl2jB', 'Sales')
        prod_link = f"https:{item.find('a', {'class': 'search-card-item'})['href']}"
        ship = extract_list(item, 'div.multi--serviceContainer--3vRdzWN > span', 'Shipping')
        data = AliExpress(
            name=name,
            price=price,
            sold=sales,
            product_link=prod_link,
            shipping=ship
        )
        result.append(asdict(data))
        result2.append(astuple(data))
    return result, result2


def writer_to_json(data):
    path = 'data/aliexp'
    if os.path.isfile(path):
        for datas in data:
            with open(f'{path}.json', 'r') as file:
                char = json.load(file)
            char.append(datas)
            with open(f'{path}.json', 'w', encoding='utf-8') as file:
                json.dump(char, file, indent=2, ensure_ascii=False)
    else:
        with open(f'{path}.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)


def writer_to_csv(data):
    paths = 'data/aliexp'
    # file_exists = os.path.isfile(paths)
    field_name = list(data[0].keys())
    with open(f'{paths}.csv', 'a', newline='', encoding='utf-8') as csv_file:
        pen = csv.DictWriter(csv_file, fieldnames=field_name)
        csv_file.seek(0, 2)
        if csv_file.tell() == 0:
            pen.writeheader()
        # if not file_exists:
        #    pen.writeheader()
        pen.writerows(data)


def sql_writer(data):
    conn = sqlite3.connect('data/aliexp.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS scraped_data (name TXT, price REAL, sold REAL, product_link TXT, shipping REAL)")
    cur.executemany('INSERT INTO scraped_data VALUES (?, ?, ?, ?, ?)', data)
    cur.execute('SELECT * FROM scraped_data')
    dat = cur.fetchall()
    for row in dat:
        print(row)


@lru_cache(maxsize=None)
async def main(urls):
    async with async_playwright() as playwright:
        html = await get_browser(urls, p=playwright)
        result, result2 = await scraper(html)
        writer_to_json(result)
        writer_to_csv(result)
        sql_writer(result2)

    return 'All Done....'


if __name__ == '__main__':
    start = time.perf_counter()
    for pag in range(1, 11):
        url = f'https://www.aliexpress.com/w/wholesale-tecno.html?page={pag}&g=y&SearchText=tecno'
        txt = asyncio.run(main(url))
    print()
    print(txt)
    end = time.perf_counter()
    print()
    print(f'\nTime:{round(end - start, 2)} seconds')
