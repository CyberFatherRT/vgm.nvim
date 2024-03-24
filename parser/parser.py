import json
import requests
import urllib.parse as parse

from typing import List
from bs4 import BeautifulSoup
from bs4.element import Tag
from dataclasses import dataclass


@dataclass()
class Track:
    number: int
    name: str
    time: str
    mp3_size: str
    flac_size: str
    mp3_link: str
    flac_link: str


@dataclass()
class Album:
    album_link: str
    album_img: str | None
    album_name: str
    product_name: str | None
    platforms: List[str] | None
    album_type: str | None
    year: int | None
    tracks: List[Track]

    def __repr__(self):
        d = {
            "album_link": self.album_link,
            "album_img": self.album_img,
            "album_name": self.album_name,
            "product_name": self.product_name,
            "album_type": self.album_type,
            "year": self.year,
            "platforms": self.platforms,
            "tracks": [track.__dict__ for track in self.tracks],
        }

        return json.dumps(d, indent=4)


class Parser:
    def __init__(self, request: str | None = None):
        self.url = "https://downloads.khinsider.com"
        self.albums: List[Album] = []
        self.query(request)

    def query(self, request: str | None):
        if request is None:
            return

        request = parse.quote(request, safe="")
        content = requests.get(self.url + f"/search?search={request}").text

        soup = BeautifulSoup(content, features="lxml")
        table = soup.find("table", {"class": "albumList"})

        if table is None:
            return

        for row in table.find_all("tr")[1:]:
            td = row.find_all("td")
            self.__parse(td)
            self.__parse_albums(self.albums[-1])

    def __parse_albums(self, album: Album):
        content = requests.get(album.album_link).text

        soup = BeautifulSoup(content, features="lxml")
        songs_table = soup.find("table", id="songlist")
        songs = songs_table.find_all("tr")[1:-1]

        for song in songs:
            td = song.find_all("td")
            _, number, name, time, mp3_size, flac_size, download_link, _ = td

            number = str(number.contents[0]).strip(".")
            name = name.find("a").contents[0]
            time = time.find("a").contents[0]
            mp3_size = mp3_size.find("a").contents[0]
            flac_size = flac_size.find("a").contents[0]
            mp3_link, flac_link = self.__parse_download_links(
                self.url + download_link.find("a").get("href")
            )
            # mp3_link, flac_link = "", ""

            self.albums[-1].tracks.append(
                Track(
                    number=int(number),
                    name=str(name),
                    time=str(time),
                    mp3_size=str(mp3_size),
                    flac_size=str(flac_size),
                    mp3_link=str(mp3_link),
                    flac_link=str(flac_link),
                )
            )

    def __parse_download_links(self, download_link: str):
        content = requests.get(download_link).text
        soup = BeautifulSoup(content, features="lxml")
        links = soup.select("a[href$='.mp3'], a[href$='.flac']")
        mp3 = links[0].get("href")
        flac = links[1].get("href")
        return mp3, flac

    def __parse(self, data: List[Tag]):
        album_link, album_img = self.__parse_link(data[0])
        album_name, product_name = self.__parse_name(data[1])
        platforms = self.__parse_platforms(data[2])
        album_type = self.__parse_album_type(data[3])
        year = self.__parse_year(data[4])
        self.albums.append(
            Album(
                album_link=f"{self.url}{album_link}",
                album_img=str(album_img),
                album_name=str(album_name),
                product_name=str(product_name),
                platforms=platforms,
                album_type=album_type,
                year=year,
                tracks=[],
            )
        )

    def __parse_link(self, link: Tag):
        a = link.find("a")

        if a is None:
            return None, None

        img = a.find("img")

        if img is None:
            return a.get("href"), None

        return a.get("href"), img.get("src")

    def __parse_name(self, name: Tag) -> tuple[str, str]:
        album_name = name.find("a").contents[0]
        product_name = name.find("span")

        if product_name is not None:
            product_name = product_name.contents[0]

        return str(album_name), str(product_name)

    def __parse_platforms(self, platforms: Tag) -> List[str]:
        return list(map(lambda x: x.contents[0], platforms.find_all("a")))

    def __parse_album_type(self, album_type: Tag) -> str | None:
        contents = album_type.contents
        if contents:
            return str(contents[0])
        return None

    def __parse_year(self, year: Tag) -> int | None:
        contents = year.contents
        if contents:
            return int(f"{contents[0]}")
        return None
