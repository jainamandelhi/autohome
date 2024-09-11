import requests
from bs4 import BeautifulSoup
import json
import math
import traceback
import pandas as pd

def prepare_car_list(oem_names):
    def check_brand_name(brand_name):
        for oem_name in oem_names:
            if oem_name.lower() in brand_name.lower():
                return True
        return False
    car_list = []
    response = requests.get('https://car.autohome.com.cn/javascript/NewSpecCompare.js')
    data = response.text.split('var listCompare$100= ')[1]
    data = data.replace(';\r\n', '')
    data = json.loads(data)
    for d in data:
        brand_id = d['I']
        brand_name = d['N']
        for l in d['List']:
            sub_brand_id = l['I']
            sub_brand_name = l['N']
            for sub_l in l['List']:
                if not check_brand_name(brand_name):
                    continue
                car_list.append([brand_id, brand_name, sub_brand_id, sub_brand_name, sub_l['I'], sub_l['N']])
    car_list.insert(0, ['Brand Id', 'Brand', 'Sub-Brand ID', 'Sub-Brand', 'Car Model ID', 'Car Name Base Page'])
    print("Car list prepared", len(car_list), car_list[:5])
    return car_list


def fetch_car_details(car_id):
    def get_car_name():
        car_name = 'N/A'
        oem_name = 'N/A'
        car_name_elements = soup.find_all("div", {"class": "athm-sub-nav__car__name"})
        if len(car_name_elements) > 0:
            complete_name = car_name_elements[0].find('a').text
            car_name = car_name_elements[0].find('a').find('h1').text
            oem_name = complete_name.replace(car_name, '').strip()
            car_name = car_name.strip()
            oem_name = oem_name[:-1].strip()
        return oem_name, car_name
    
    def get_tag_price():
        tag_price = 'N/A'
        tag_price_elements = soup.find_all("a", {"class": "emphasis"})
        if len(tag_price_elements) > 0:
            tag_price = tag_price_elements[0].text
        return tag_price
    
    def get_transaction_price():

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Origin': 'https://www.autohome.com.cn',
            'Referer': 'https://www.autohome.com.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

        params = {
            '_appId': 'cms',
            'cityId': '110100',
            'seriesId': f'{car_id}',
        }
        try:
            response = requests.get(
                'https://autoapi.autohome.com.cn/autohome-www-api/inquirylayer/getSpecGroupedInfoListBySeriesId',
                params=params,
                headers=headers,
            )
            maxPrice = -math.inf
            minPrice = +math.inf
            for d in response.json()['result']:
                for i in d['specList']:
                    if i['newsId'] == 0:
                        continue
                    if i['newsPrice'] > maxPrice:
                        maxPrice = i['newsPrice']
                    if i['newsPrice'] < minPrice:
                        minPrice = i['newsPrice']
                    print(i['newsId'], i['newsPrice'])
            if minPrice == +math.inf:
                return 'N/A'
            if minPrice == -math.inf:
                return 'N/A'
            return f"{minPrice} - {maxPrice}"
        except Exception as e:
            print(traceback.format_exc())
            print(f"Failed to fetch transaction price: {e}")
            return 'N/A'


    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    car_info = {'OEM Name': 'N/A', 'Car Name': 'N/A', 'Tag Price': 'N/A', 'Transaction Price': 'N/A'}
    try:
        url = f'https://www.autohome.com.cn/{car_id}/'
        print(f"Fetching car details for {url}")
        response = requests.get(f'https://www.autohome.com.cn/{car_id}/', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info['OEM Name'], car_info['Car Name'] = get_car_name()
        car_info['Tag Price'] = get_tag_price()
        car_info['Transaction Price'] = get_transaction_price()
        return car_info
    except Exception as e:
        print(traceback.format_exc())
        print(f"Failed to fetch car details: {e}")
        return car_info

def process_car_list(car_list):
    car_details = car_list[:]
    car_details[0].extend(['OEM Name', 'Car Name', 'Tag Price', 'Transaction Price'])
    for car in car_details[1:]:
        car_id = car[4]
        car_info = fetch_car_details(car_id)
        print(f"Car details: {car_info}")
        car.extend([car_info['OEM Name'], car_info['Car Name'], car_info['Tag Price'], car_info['Transaction Price']])
    return car_details


if __name__ == '__main__':
    oem_names = input("Enter OEM names (comma separated): ").split(",")
    oem_names = [oem_name.strip() for oem_name in oem_names]
    print("OEM names: ", oem_names)
    car_list = prepare_car_list(oem_names)
    car_details = process_car_list(car_list)
    df = pd.DataFrame(car_details[1:], columns=car_details[0])
    df.to_csv('car_details.csv', index=False, columns=car_details[0])

