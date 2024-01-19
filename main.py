import asyncio
import re
import requests
import os
import json
from pyppeteer import launch
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.request import urlretrieve
from datetime import datetime

async def main():
    browser = await launch()
    page = await browser.newPage()
    await page.goto('https://t.me/s/drop_opt_clothes0', { 'waitUntil': 'networkidle0', 'timeout': 30000 })

    # variables
    current_date = datetime.now().strftime("%B %d")
    date_chip_selector = '.tgme_widget_message_service_date'
    images_src_url_pattern = re.compile(r'url\((.+?)\)')

    # get posts from page
    while True:
        await page.evaluate('''() => {
            window.scrollTo(0, -400);
        }''')

        posts_date_chip_visible = await page.querySelector(date_chip_selector)
        if posts_date_chip_visible:
            break

        await asyncio.sleep(1)

    # loop founded posts
    posts = await page.querySelectorAll('.tgme_widget_message_wrap.js-widget_message_wrap')
    for post in posts:
        post_id_el = await post.querySelector('.tgme_widget_message')
        post_date_el = await post.querySelector('.tgme_widget_message_service_date')
        post_text_el = await post.querySelector('.tgme_widget_message_text')

        post_id = await page.evaluate('(el) => el.getAttribute("data-post").split("/")[1]', post_id_el)
        post_date = await page.evaluate('(el) => el.textContent', post_date_el)
        post_text = await page.evaluate('(el) => el.innerText', post_text_el)

        # only post with current date
        if post_date == current_date:
            continue
        
        # create post json file
        post_folder_path = "../post-data"
        post_file_path = f"{post_id}.json"
        post_full_path = os.path.join(post_folder_path, post_file_path)
        post_data = {
            'images': [],
            'videos': [],
            'price': None
        }

        if not os.path.exists(post_folder_path):
            os.makedirs(post_folder_path)

        if not os.path.exists(post_full_path):
            with open(post_full_path, 'w', encoding='utf-8') as json_file:
                json.dump({}, json_file, ensure_ascii=False, indent=4)
        
        # change post price
        post_prices = re.findall(r'(\d+)\s*грн', post_text)
        print(post_prices)
        prices = []
        for match in post_prices:
            number = int(match)
            increased_number = int(number + 0.3 * number)
            prices.append((number, increased_number))
        for original, increased in prices:
            post_text = re.sub(fr"{original}(\s*грн)", f"{increased}\\1", post_text)

        post_data['price'] = [post_prices]
        
        # change post text
        post_data['content'] = post_text

        # save images & videos   
        post_html = await page.evaluate('(el) => el.outerHTML', post)
        soup = BeautifulSoup(post_html, 'html.parser')

        images = soup.find_all('a', class_='tgme_widget_message_photo_wrap')
        videos = soup.find_all('video', class_='tgme_widget_message_video')

        for idx, image in enumerate(images):
            image_style_attr = image.get('style', '')
            match = images_src_url_pattern.search(image_style_attr)
            if match:
                image_url = match.group(1).strip('"')

                post_data['images'].append(image_url)

        for idx, video in enumerate(videos):
            video_url = video.get('src', '')
            
            post_data['videos'].append(video_url)

        # save post data in json
        with open(post_full_path, 'w', encoding='utf-8') as json_file:
            json.dump(post_data, json_file, ensure_ascii=False, indent=2)
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
