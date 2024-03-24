import re
import os
import json
import requests
from bs4 import BeautifulSoup


class MTGDecksCLI:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:123.0) Gecko/20100101 Firefox/123.0"

    def scrape(self, max_n_decks: int, output_data_folder: str, format: str = "Modern"):
        n_collected_decks = 0
        page_index = 1
        while n_collected_decks < max_n_decks:
            print(f"Scrape page {page_index} (collected {n_collected_decks}/{max_n_decks})")
            url = f"https://mtgdecks.net/{format}/decklists/page:{page_index}"
            deck_json_dict_list = self.__collect_decks_on_page(url=url)
            if max_n_decks - n_collected_decks < len(deck_json_dict_list):
                deck_json_dict_list = deck_json_dict_list[:(max_n_decks - n_collected_decks)]
            self.__save_decks(deck_json_dict_list, output_data_folder)
            n_collected_decks += len(deck_json_dict_list)
            page_index += 1

    def __collect_decks_on_page(self, url: str):
        deck_urls = self.__get_deck_urls_on_page(url=url)
        deck_json_dict_list = self.__parse_decks_from_urls(deck_urls)
        return deck_json_dict_list

    def __get_deck_urls_on_page(self, url: str):
        deck_urls = []
        html_document = requests.get(
            url,
            headers={"User-Agent": self.user_agent}
        ).text
        soup = BeautifulSoup(html_document, features="html.parser")
        for element in soup.find_all("td", attrs={"nowrap": "nowrap"}):
            url = element.find("a")
            if url is not None:
                deck_urls.append(url["href"])
        return deck_urls

    def __parse_decks_from_urls(self, deck_urls):
        deck_json_dict_list = []
        for deck_url in deck_urls:
            deck_json_dict = self.__parse_deck_from_url(deck_url)
            deck_json_dict_list.append(deck_json_dict)
        return deck_json_dict_list

    def __parse_deck_from_url(self, deck_url):
        deck_json_dict = {
            "name": None,
            "cards": []
        }
        url = f"https://mtgdecks.net{deck_url}"
        html_document = requests.get(
            url,
            headers={"User-Agent": self.user_agent}
        ).text
        soup = BeautifulSoup(html_document, features="html.parser")

        deck_name = soup.find("h1").text.strip().replace(",", "")
        deck_json_dict["name"] = deck_name

        card_items = soup.find_all("tr", attrs={"class": "cardItem"})
        for card_item in card_items:
            card_name = card_item["data-card-id"]
            card_count = int(re.findall("\d", card_item.find("td", attrs={"class": "number"}).text)[0])
            deck_json_dict["cards"].append({
                "name": card_name,
                "count": card_count
            })

        return deck_json_dict

    def __save_decks(self, deck_json_dict_list, output_data_folder):
        for deck_json_dict in deck_json_dict_list:
            deck_name = deck_json_dict["name"]
            save_path = os.path.join(output_data_folder, f"{deck_name}.json")

            with open(save_path, "w") as f:
                json.dump(deck_json_dict, f, indent=4)
