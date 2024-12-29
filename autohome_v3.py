import requests
from bs4 import BeautifulSoup
import json
import math
import traceback
import pandas as pd


def prepare_car_list(oem_names):
    def check_brand_name(brand_name_key):
        for oem_name in oem_names:
            if oem_name.lower() in brand_name_key.lower():
                return True
        return False

    car_list = []
    response = requests.get('https://caropen.api.autohome.com.cn/v1/carprice/tree_menu')
    if response.status_code != 200:
        raise Exception(f"Failed to fetch car list: {response.status_code}")
    data = response.json()
    results = data.get("result", [])
    for result in results:
        brand_items = result.get("branditems", [])
        for brand_item in brand_items:
            brand_id = brand_item.get("id")
            brand_name = brand_item.get("name")
            for fct_item in brand_item.get("fctitems", []):
                sub_brand_id = fct_item.get("id")
                sub_brand_name = fct_item.get("name")
                for series_item in fct_item.get("seriesitems", []):
                    car_id = series_item.get("id")
                    car_name = series_item.get("name")
                    if not check_brand_name(brand_name):
                        continue
                    car_list.append([brand_id, brand_name, sub_brand_id, sub_brand_name, car_id, car_name])
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
            'Accept': 'application/json',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Authorization': 'Basic Y2FyLXBjLW5leHRqc3lJNndab292Om5HM2RsNU5uUHZZRA==',
            'Connection': 'keep-alive',
            'Origin': 'https://www.autohome.com.cn',
            'Referer': 'https://www.autohome.com.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        params = {
            '_entryid': '7',
            'specEntryId': '6',
            'isNeedUnSale': '1',
            '_appid': 'pc',
            'seriesid': f'{car_id}',
            'cityid': '110100',
        }
        try:
            response = requests.get(
                'https://autoapi.autohome.com.cn/jxsjs/ics/yhz/dealerlq/v1/statistics/seriesprice/getSeriesMinpriceWithSpecs',
                params=params,
                headers=headers,
            )
            maxPrice = -math.inf
            minPrice = +math.inf
            for d in response.json()['result']:
                for i in d['specs']:
                    if i['newsPrice'] > maxPrice:
                        maxPrice = i['newsPrice']
                    if i['newsPrice'] < minPrice:
                        minPrice = i['newsPrice']
                    print(i['newsPrice'])
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
        # 'cookie': '_ac=9ebc6ad721abf951.1735423428; sessionip=103.248.174.139; sessionid=2C1D6A0B-7266-4649-B8AE-7FDE1D990C6F%7C%7C2024-12-29+06%3A03%3A48.175%7C%7C0; autoid=7cb72aa30e0385fdb05f11da5475240f; area=999999; cookieCityId=110100; __ah_uuid_ng=c_2C1D6A0B-7266-4649-B8AE-7FDE1D990C6F; tfstk=gvbjhJs1FBvrlRkli-FydENolNL_LOaFMfOOt13q6ELvBVC1TilV6o096TBv3nPc6d61UL72bEdN5T6D9q8aDtSW51CtQO1giCpOBO9N0uzFisYMWJW_8y5DWu7lFZTtQ_LD_BtAY9zFisc-GAFF2yk166QfXdB9DbdJgLnxDOpv27O9_xp9HOC8NLAnBId9H_LJOLp9WFBOw7Ois3cB1o9cGSguS-1qIy6JFV3OPIFDps9WZQbWGn9p2LgOGaOXcpCAu53QUBsCPHSYModB5LfcznaqoFfPAOsOp8o2HMOCh3szCxpGP_QAX_Dbwe154M-fV-36UZJkYZLQoqT1aatFfFaoZKIh4tQJSXokuM5FSHQYlvvyxC6WYiwIl9IrM2JCLonsNH09NpP7NcmgrMnbH3KCS8KvZItzN7MAjndkNeP7NcmMDQAXa7NSHGf..; series_ask_price_popup=2024-12-29; sessionvid=585127B1-D2CA-479D-A2ED-EA4A7DA07AB2; historyseries=4212%2C3825%2C2097%2C3895; ahpvno=16; v_no=3; visit_info_ad=2C1D6A0B-7266-4649-B8AE-7FDE1D990C6F||585127B1-D2CA-479D-A2ED-EA4A7DA07AB2||-1||-1||3; ref=0%7C0%7C0%7C0%7C2024-12-29+07%3A43%3A00.229%7C2024-12-29+06%3A03%3A48.175; ahrlid=1735429377241yzyAOE0KXP-1735429399811',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    car_info = {'OEM Name': 'N/A', 'Car Name': 'N/A', 'Tag Price': 'N/A', 'Transaction Price': 'N/A'}
    try:
        url = f'https://www.autohome.com.cn/{car_id}/'
        print(f"Fetching car details for {url}")
        response = requests.get(f'https://www.autohome.com.cn/{car_id}/', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        json_data = json.loads(script_tag.string)
        series_basic_info = json_data.get('props', {}).get('pageProps', {}).get('seriesBaseInfo', {})
        car_info['p__minPrice'] = series_basic_info.get('minPrice', 'N/A')
        car_info['p__maxPrice'] = series_basic_info.get('maxPrice', 'N/A')
        car_info['p__fctId'] = series_basic_info.get('fctId', 'N/A')
        car_info['p__fctName'] = series_basic_info.get('fctName', 'N/A')
        car_info['p__hotSpecName'] = series_basic_info.get('hotSpecName', 'N/A')
        car_info['Transaction Price'] = get_transaction_price()
        car_info['Tag Price'] = f"{series_basic_info.get('minPrice', 'N/A')} - {series_basic_info.get('maxPrice', 'N/A')}"
        return car_info
    except Exception as e:
        print(traceback.format_exc())
        print(f"Failed to fetch car details: {e}")
        return car_info


def process_car_list(car_list):
    car_details = car_list[:]
    car_details[0].extend(['Tag Price', 'p__fctId', 'p__fctName', 'p__hotSpecName',  'Transaction Price'])
    for car in car_details[1:]:
        car_id = car[4]
        car_info = fetch_car_details(car_id)
        print(f"Car details: {car_info}")
        car.extend([car_info['Tag Price'], car_info['p__fctId'], car_info['p__fctName'], car_info['p__hotSpecName'], car_info['Transaction Price']])
        print(f"Car details: {car}")
    return car_details


if __name__ == '__main__':
    oem_names = input("Enter OEM names (comma separated): ").split(",")
    oem_names = [oem_name.strip() for oem_name in oem_names]
    print("OEM names: ", oem_names)
    car_list = prepare_car_list(oem_names)
    car_details = process_car_list(car_list)
    df = pd.DataFrame(car_details[1:], columns=car_details[0])
    df.to_csv('car_details.csv', index=False, columns=car_details[0])
