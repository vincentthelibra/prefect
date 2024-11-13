import re
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd

# initial_url = "https://www.booli.se/sok/slutpriser?areaIds=20&page=3"


def check_response(url: str) -> bool:
    with requests.Session() as session:
        response = session.get(url)
        if response.status_code == 200:
            print("Request successful.")
            return True
        else:
            print(f"Request failed with status code {response.status_code}")
            return False


def get_token(soup: BeautifulSoup) -> str:
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if script_tag:
        content = script_tag.string
        data = json.loads(content)

        build_id = data.get('buildId')
        if build_id:
            print("Build ID:", build_id)
            return build_id


def get_total_page_number(soup: BeautifulSoup, token: str) -> int:
    api_url = f"https://www.booli.se/_next/data/{token}/sv/sok/slutpriser.json?searchType=slutpriser"
    with requests.Session() as session:
        response = session.get(api_url)
        data = response.json()

        root_query = data.get('pageProps', {}).get('__APOLLO_STATE__',
                                                   {}).get('ROOT_QUERY', {})

        search_key = next(
            (key for key in root_query if re.match(r'^searchSold\(', key)),
            None)

        if search_key:
            total_page_number = root_query.get(search_key, {}).get('pages')
            if total_page_number:
                print("Pages:", total_page_number)
                return total_page_number
            else:
                print("Pages not found in matched key.")
                return 0
        else:
            print("No matching key found for 'searchSold'.")
            return 0


def extract_data(soup: BeautifulSoup, token: str,
                 page_number: int) -> pd.DataFrame:
    properties = []
    api_url = f"https://www.booli.se/_next/data/{token}/sv/sok/slutpriser.json?page={page_number}&searchType=slutpriser"
    with requests.Session() as session:
        response = session.get(api_url)
        data = response.json()

        apollo_state = data.get('pageProps', {}).get('__APOLLO_STATE__', {})

        for key, value in apollo_state.items():
            if isinstance(value,
                          dict) and value.get("__typename") == "SoldProperty":
                # Extract relevant property details if they exist
                property_data = {
                    'id':
                    value.get('id'),
                    'list_price':
                    extract_digits((value.get('listPrice')
                                    or {}).get('formatted')),
                    # int
                    #     re.sub(r'[^\d]', '', (value.get('listPrice')
                    #                           or {}).get('formatted', 0))),
                    'sold_price':
                    value.get('soldPrice').get('raw'),
                    'address':
                    value.get('streetAddress'),
                    'number_of_floor': (value.get('floor')
                                        or {}).get('value', 0),
                    'object_type':
                    value.get('objectType'),
                    'sold_date':
                    value.get('soldDate'),
                    'latitude':
                    value.get('latitude'),
                    'longitude':
                    value.get('longitude'),
                    'municipality':
                    value.get('location').get('region').get(
                        'municipalityName'),
                }

                living_area_str = value.get('livingArea').get('formatted')
                living_area = int(
                    re.sub(r'[^\d]', '',
                           living_area_str)) if living_area_str else None
                property_data['living_area'] = living_area

                amenities_refs = value.get('amenities', [])
                for i, ref in enumerate(amenities_refs, start=1):
                    amenity_ref = ref.get("__ref")
                    if amenity_ref and amenity_ref in apollo_state:
                        amenity_key = apollo_state[amenity_ref].get("key")
                        property_data[f'amenity{i}'] = amenity_key

                properties.append(property_data)

        properties_df = pd.DataFrame(properties)
        print(properties_df)
        return properties_df


def extract_digits(text: str, default=0) -> int:
    if text is None:
        return default

    cleaned_text = re.sub(r'[^\d]', '', text)
    return int(cleaned_text) if cleaned_text else default


def main():
    initial_url = "https://www.booli.se/sok/slutpriser?"
    if check_response(initial_url):
        with requests.Session() as session:
            response = session.get(initial_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            my_token = get_token(soup)
            total_page_number = get_total_page_number(soup, my_token)
            all_properties = []

            for page in range(1, total_page_number + 1):
                page_properties = extract_data(my_token, page)
                all_properties.extend(page_properties)

            all_sold_properties_df = pd.DataFrame(all_properties)
            print(all_sold_properties_df)
            return all_sold_properties_df


if __name__ == "__main__":
    main()
