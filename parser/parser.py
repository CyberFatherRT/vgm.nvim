import aiohttp
import asyncio
import json
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
            "tracks": list(map(lambda x: x.__dict__, self.tracks)),
        }

        return json.dumps(d, indent=4)


class Parser:
    def __init__(self):
        self.url = "https://downloads.khinsider.com"
        self.albums: List[Album] = []

    async def fetch_content(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def query(self, request: str):
        if request is None:
            return

        request = parse.quote(request, safe="")
        content = await self.fetch_content(self.url + f"/search?search={request}")

        soup = BeautifulSoup(content, features="lxml")
        table = soup.find("table", {"class": "albumList"})

        if table is None:
            return

        tasks = []
        for row in table.find_all("tr")[1:]:
            td = row.find_all("td")
            album_link, _ = self.__parse_link(td[0])
            album = Album(
                album_link=f"{self.url}{album_link}",
                album_img=None,
                album_name=str(td[1].find("a").contents[0]),
                product_name=str(td[1].find("span").contents[0])
                if td[1].find("span")
                else None,
                platforms=[str(a.contents[0]) for a in td[2].find_all("a")],
                album_type=str(td[3].contents[0]) if td[3].contents else None,
                year=int(td[4].contents[0]) if td[4].contents else None,
                tracks=[],
            )
            tasks.append(self.__parse_album(album))

        await asyncio.gather(*tasks)

    async def __parse_album(self, album: Album):
        content = await self.fetch_content(album.album_link)

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
            mp3_link, flac_link = await self.__parse_download_links(
                self.url + download_link.find("a").get("href")
            )

            album.tracks.append(
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

        self.albums.append(album)

    async def __parse_download_links(self, download_link: str):
        content = await self.fetch_content(download_link)
        soup = BeautifulSoup(content, features="lxml")
        links = soup.select("a[href$='.mp3'], a[href$='.flac']")
        mp3 = links[0].get("href")
        flac = links[1].get("href")
        return mp3, flac

    def __parse_link(self, link: Tag):
        a = link.find("a")

        if a is None:
            return None, None

        img = a.find("img")
        if img is None:
            return a.get("href"), None

        return a.get("href"), img.get("src")
