from bs4 import BeautifulSoup
from requests import get

if __name__ == "__main__":
    # url = "https://downloads.khinsider.com/search?search=metal+gear+rising"
    # res = get(url).text

    res = open("index.html").read()

    soup = BeautifulSoup(res, features="lxml")
    a = soup.find_all("tr")[1:]

    print(a)
