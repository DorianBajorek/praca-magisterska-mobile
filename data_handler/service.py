import requests
from lxml import html
import os
class Scraper:
    def __init__(self, isbn):
        self.isbn = isbn
        self.google_api_book_key = 'AIzaSyAzxO2vbiMbpv5F8P6V_Ff6EdUIiCap0sU'
    def find_key(self, data, key_to_find):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == key_to_find:
                    return value
                if isinstance(value, (dict, list)):
                    result = self.find_key(value, key_to_find)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self.find_key(item, key_to_find)
                if result is not None:
                    return result
        return None
    
    def create_url(self):
        return f"https://www.poczytaj.pl/index.php?akcja=pokaz_ksiazki&szukaj={self.isbn}&kategoria_szukaj=cala_oferta&id=best&limit=10"
    
    def get_from_openlibrary(self):
        url = f"http://openlibrary.org/api/volumes/brief/isbn/{self.isbn}.json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data != None:
                return None
            title = self.find_key(response, "title")
            author = self.find_key(data, "authors")
            authors = ', '.join([author[i]['name'] for i in range(len(author))])
            return title, authors
        else:
            return None
        
    def get_from_poczytaj_pl(self):
        try:
            url = f"https://www.poczytaj.pl/index.php?akcja=pokaz_ksiazki&szukaj={self.isbn}&kategoria_szukaj=cala_oferta&id=best&limit=10"
           
            response = requests.get(self.create_url())
            img_xpath = "/html/body/div/main/div[5]/div[1]/a/img"
            title_xpath = "/html/body/div/main/div[5]/div[2]/div[2]/h3/a"
            author_xpath = "/html/body/div/main/div[5]/div[2]/div[1]"
            tree = html.fromstring(response.text)
            title = tree.xpath(title_xpath)[0].text
            author = tree.xpath(author_xpath)[0].text
            return title, author
        except:
            return None
    
    def get_from_google(self):
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{self.isbn}&key={self.google_api_book_key}"
        print(url)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data)
            if data['totalItems'] > 0:
                book_info = data['items'][0]['volumeInfo']
                title = book_info.get('title', 'Nieznany tytuł')
                authors = ', '.join(book_info.get('authors', ['Nieznany autor']))
                if title != 'Nieznany tytuł' and authors != ['Nieznany autor'] :
                    return title, authors 
                return None
        return None

    def get_info(self):
        result = self.get_from_openlibrary()
        if result != None:
            return result
        result = self.get_from_poczytaj_pl()
        if result != None:
            return result
        result = self.get_from_google()
        if result != None:
            return result
        return None,None
    
