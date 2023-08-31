from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup

class Scraper(ABC):
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def _get_soup(self):
        response = requests.get(self.url)
        return BeautifulSoup(response.content, "html.parser")

    def add_offers(self, scrap_dict):
        self._fill_dict(scrap_dict, self._get_soup())

    @abstractmethod
    def _fill_dict(self, dict, soup):
        """
        Must put key-value such as :
        - key :  URL
        - value : [Source, Offer_Name]
        """
        pass

class CityaScraper(Scraper):
    def _fill_dict(self, scrap_dict, soup):
        temp = soup.find("ul", class_="list-biens")
        for info in temp.find_all("div", class_="infos"):
            info = info.find("a")
            link = "https://www.citya.com" + info.get("href")
            h3_tag = info.find("h3")
            ville_tag = info.find("p", class_="ville")
            offer_name = f"{h3_tag.get_text(separator=' ', strip=True)} {ville_tag.get_text(strip=True)}"

            scrap_dict[link] = [self.name, offer_name]

class Century21Scraper(Scraper):
    def _fill_dict(self, scrap_dict, soup):
        for info in soup.find_all("div", class_="js-the-list-of-properties-list-property"):
            offer_name = info.find("div", class_="c-text-theme-heading-4 tw-text-c21-grey-darker tw-font-semibold").get_text().split()
            offer_name = ' '.join(offer_name)
            link = "https://www.century21.fr" + info.find('a', title="Voir le détail du bien").get("href")
            scrap_dict[link] = [self.name, offer_name]