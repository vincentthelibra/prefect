from prefect import flow
import re
import json
import requests
from bs4 import BeautifulSoup

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
    api_url = f"https://www.booli.se/_next/data/{token}/sv/sok/slutpriser.json?areaIds=20&searchType=slutpriser"
    with requests.Session() as session:
        response = session.get(api_url)
        data = response.json()
        total_page_number = data.get('pageProps', {}).get(
            '__APOLLO_STATE__', {}
        ).get('ROOT_QUERY', {}).get(
            'searchSold({\"input\":{\"areaId\":\"20\",\"ascending\":false,\"filters\":[],\"page\":1,\"sort\":\"soldDate\"}})',
            {}).get('pages')

        if total_page_number:
            print("Pages:", total_page_number)
            return total_page_number
        else:
            print("Pages not found.")
            return 0

    def extract_data(soup: BeautifulSoup) -> None:
        pass


@flow
def main():
    initial_url = "https://www.booli.se/sok/slutpriser?areaIds=20"
    if check_response(initial_url):
        with requests.Session() as session:
            response = session.get(initial_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            my_token = get_token(soup)
            total_page_number = get_total_page_number(soup, my_token)
            for page_number in range(1, total_page_number + 1):
                # Process each page
                pass


if __name__ == "__main__":
    main()
