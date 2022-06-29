import csv
import functools
import json
import logging
import re
import time
from json import JSONDecodeError
from pathlib import Path
from typing import cast

import requests
from lxml import etree
from playwright.sync_api import Browser, Error, TimeoutError, sync_playwright
from tqdm import tqdm

logger = logging.Logger("Spider")
logger.setLevel(logging.CRITICAL)
logger.addHandler(logging.FileHandler("spider.log", encoding="utf-8"))


class SpiderError(Exception):
    """
    This error represents all kind of error during the scraping process.
    """


def _func_wrapper(func):
    @functools.wraps(func)
    def _impl(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            raise SpiderError(e.name, e.message) from e
        except SpiderError as e:
            raise e
        except Exception as e:
            raise SpiderError(e) from e

    return _impl


class Spider:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
    }
    curdir = Path(globals().get("__file__", "") or "./placeholder").resolve().parent
    short_timeout = 500
    url_gen = "https://projectboard.world/isef/finalist-booth/{id}"

    @classmethod
    def escape_filename(cls, filename):
        for c in '\\/:*?"<>|':
            filename = filename.replace(c, "_")
        return filename.strip()

    def __init_subclass__(cls) -> None:
        for name, value in cls.__dict__.items():
            if callable(value):
                setattr(cls, name, _func_wrapper(value))
            if "__get__" in name:
                setattr(cls, name, _func_wrapper(value.__get__))
            if "__set__" in name:
                setattr(cls, name, _func_wrapper(value.__set__))

    def __init__(
        self,
        browser: Browser,
        url="https://projectboard.world/isef/viewAll?category=",
        type="ROBO",
        cont=0,
    ) -> None:
        self.browser = browser
        self.context = browser.new_context()
        self.page = self.context.new_page()
        self.url = url + type
        self.type = type
        self.dir = self.curdir / Spider.escape_filename(self.type)
        self.all_cards: list[dict[str, str]] = []
        self.projects: list[dict[str, str]] = []
        self.cont = cont

        try:
            self.dir.mkdir(parents=True, exist_ok=True)
        except IOError:
            logger.critical("Could not create directory")

        def cancel(route, request):
            if request.resource_type in {"image", "media", "font"}:
                # Just don't ask server. We don't want any media
                route.fulfill(status=200, content_type=request.resource_type, body=b"")
                return
            route.continue_()

        self.page.route("**/*", cancel)

        self.get_all_cards()

    def get_all_cards(self):
        json_path = self.dir / "index.json"
        csv_path = self.dir / "index.csv"

        if not (json_path.exists() and csv_path.exists()):
            logger.debug("Loading from web")
            self._load_from_web()
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(self.projects, f)
                with open(csv_path, "w", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=self.all_cards[0].keys())
                    for row in self.all_cards:
                        writer.writerow(row)
            except IOError as e:
                logger.critical(f"Could not write data to file {e!r}")
        else:
            logger.debug("Loading data from file")
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(
                        f,
                        fieldnames=[
                            "url",
                            "name",
                            "title",
                            "description",
                            "awards",
                            "created",
                            "updated",
                            "published",
                        ],
                    )
                    self.all_cards = [row for row in reader]
            except IOError as e:
                logger.critical(f"Could not read data from file {e!r}")

    def _load_from_web(self):
        def xhr(response):
            if (
                response.request.resource_type == "xhr"
                and response.url.find("memebers") == -1
            ):
                try:
                    json = response.json()
                    if isinstance(json, dict) and "projects" in json.get("result", {}):
                        self.projects.extend(json["result"]["projects"])
                except JSONDecodeError:
                    pass

        self.page.on("response", xhr)
        self.page.goto(self.url, wait_until="networkidle")

        prev_len = len(self.projects)
        for _ in range(40):
            self.infinite_scroll()
            self.page.locator(".loader").wait_for(state="hidden")
            self.page.wait_for_load_state("networkidle")

            if len(self.projects) == prev_len:
                break
            else:
                prev_len = len(self.projects)

        self.page.remove_listener("response", xhr)

        self.all_cards = [self.extract_one(project) for project in self.projects]

    def extract_one(self, project) -> dict[str, str]:
        url = Spider.url_gen.format(id=project["id"])
        created, updated, published = [
            project[k] for k in "created updated published".split(" ")
        ]
        name = (
            project["user"]["fullName"]
            or (project["user"]["firstName"] + project["user"]["lastName"])
            or project["user"]["userName"]
        )
        title = project["title"]
        description = project["description"]
        awards = ", ".join(award["name"] for award in project["awards"])
        return {
            "url": url,
            "name": name,
            "title": title,
            "description": description,
            "awards": awards,
            "created": created,
            "updated": updated,
            "published": published,
        }

    def infinite_scroll(self):
        self.page.evaluate(
            """
            var intervalID = setInterval(function () {
                var scrollingElement = (document.scrollingElement || document.body);
                scrollingElement.scrollTop = scrollingElement.scrollHeight;
            }, 200);

            """
        )
        prev_height = None
        while True:
            curr_height = self.page.evaluate("(window.innerHeight + window.scrollY)")
            if not prev_height:
                prev_height = curr_height
                time.sleep(1)
            elif prev_height == curr_height:
                self.page.evaluate("clearInterval(intervalID)")
                break
            else:
                prev_height = curr_height
                time.sleep(1)

    def close_feedback(self):
        card = self.page.locator(".modal-card:has(.feedback-container:visible)")
        if card.count():
            card.locator(".close").click()

    def main(self):
        idx = self.cont
        with tqdm(
            total=len(self.all_cards) - idx, leave=False, desc="Scraping"
        ) as pbar:
            first_time = True
            while idx < len(self.all_cards):
                card = self.all_cards[idx]
                try:
                    try:
                        self.page.goto(card["url"], wait_until="networkidle")
                    except TimeoutError:
                        if first_time:
                            logger.critical(
                                f"TimeoutError: {card['url']}. Retry with refresh."
                            )
                            self.retry()
                            first_time = False
                            continue
                        else:
                            first_time = True
                            logger.critical(f"Failed to scrape {card['url']}")
                            idx += 1
                            pbar.update()
                            continue

                    ModelWalker(
                        self.dir / "data", self.page, title=card["title"]
                    ).scrape_models()
                    idx += 1
                    pbar.update()
                except (SpiderError, Error) as e:
                    idx += 1
                    logger.critical(repr(e))
                    pbar.update()
                    continue

    def retry(self):
        self.context.close()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()


class ItemWalker(Spider):
    """
    A class that walks through the items in a carousel. Download the current item and
    classify them.
    """

    def __init__(self, page) -> None:
        self.page = page

    @property
    def idx(self):
        try:
            return len(
                etree.HTML(
                    self.page.locator(".carousel-dots").inner_html(
                        timeout=Spider.short_timeout
                    )
                ).xpath('//span[@class="selected"]/preceding-sibling::span')
            )
        except Error:
            # Not found, then there only 1.
            return 0

    @property
    def type(self):
        retry = 3
        while retry >= 0:
            try:
                if self.current.locator('.card-header-title:text("YouTube")').count():
                    return "youtube"
                elif self.current.locator("i.fa-file-pdf").count():
                    return "pdf"
                elif self.current.locator("img").count():
                    return "image"
                elif self.current.locator('div[role="document"]:text("media")').count():
                    return "media"
            except (Error, SpiderError):
                pass
            time.sleep(0.5)
            retry -= 1
        raise SpiderError("Unknown type")

    def next_item(self):
        try:
            self.page.locator(".carousel-nav-right").click(timeout=Spider.short_timeout)
        except Error as e:
            raise SpiderError("Next item not found") from e

    def prev_item(self):
        try:
            self.page.locator(".carousel-nav-left").click(timeout=Spider.short_timeout)
        except Error as e:
            raise SpiderError("Previous item not found") from e

    @property
    def size(self):
        try:
            self.page.locator(".carousel-dots").wait_for(
                state="attached", timeout=Spider.short_timeout
            )
            return self.page.locator(".carousel-dots > span").count()
        except TimeoutError:
            return 1

    @property
    def current(self):
        return self.page.locator(".carousel-container > div").nth(self.idx)

    def download(self, dir, num):
        try:
            dir.mkdir(parents=True, exist_ok=True)
        except IOError as e:
            logger.critical(f"Could not create directory {dir} {e!r}")

        match (self.type):
            case "youtube", "media":
                # NotImplemented
                pass
            case "pdf":
                with self.page.expect_popup() as popup_info:
                    btn = self.current.locator("button:has-text('Download')")
                    btn.click(modifiers=["Alt"])
                page = popup_info.value

                page.wait_for_load_state("networkidle")
                url = page.url
                page.close()

                self.page.wait_for_load_state("networkidle")
                file = (
                    Spider.escape_filename(
                        re.sub(
                            r"\s*(?=\.\w+$)",
                            "",
                            self.current.locator(".title").text_content(),
                        )
                    ).removesuffix(".pdf")
                    + ".pdf"
                )
                path: Path = dir / file
                if not path.exists():
                    try:
                        pdf = requests.get(url, headers=Spider.headers)
                        pdf.raise_for_status()
                        with open(path, "wb") as f:
                            f.write(pdf.content)
                    except (IOError, Error) as e:
                        raise SpiderError(
                            f"Failed to download {file} with has url {url}"
                        ) from e
                else:
                    logger.debug(f"{path} already exists. Skipped.")
            case "image":
                src = self.current.locator("img").get_attribute("src")
                img = requests.get(
                    cast(str, src),
                    headers=Spider.headers,
                )
                img.raise_for_status()
                path = dir / f"{num}.png"
                if not path.exists():
                    try:
                        with open(dir / f"{num}.png", "wb") as f:
                            f.write(img.content)
                    except (IOError, Error) as e:
                        raise SpiderError(
                            f"Failed to download image with has url {src}"
                        ) from e
                else:
                    logger.debug(f"{path} already exists. Skipped.")

    def download_all(self, dir):
        size = self.size
        with tqdm(desc="downloading", total=size, leave=False) as pbar:
            while True:
                self.download(dir, (idx := self.idx))
                pbar.update()
                if idx == size - 1:
                    break
                else:
                    self.next_item()


class ModelWalker(Spider):
    def __init__(self, dir, page, title) -> None:
        self.dir = dir
        self.page = page
        self.title = title

    def get_id_title(self):
        self.page.wait_for_selector(".projectTitleContainer_title")
        return [
            title.strip()
            for title in self.page.locator(
                ".projectTitleContainer_title"
            ).all_text_contents()
        ]

    def next_model(self):
        """
        Walk to next section
        """
        self.page.locator(".modal-arrow:visible:has(i.fa-chevron-right)").click()

    def scrape_models(self):
        """
        Scrape all models of a page
        """
        with tqdm(total=5, leave=False, desc=f"{self.title}") as pbar:
            self.dir = self.dir / f"{Spider.escape_filename(self.title)}"

            if self.dir.exists():
                return

            try:
                self.dir.mkdir(parents=True, exist_ok=True)
            except IOError as e:
                raise SpiderError(f"Failed to create directory {self.dir}") from e

            self.page.locator(".content").first.click()

            pbar.set_description(f"{self.title} quadrant")
            pbar.update(1)

            self.walker = ItemWalker(self.page)
            try:
                self.walker.download_all(self.dir / "quadrant")
            except SpiderError as e:
                logger.critical(
                    f"Failed to download quadrant {self.title} because of {e!r}"
                )

            pbar.set_description(f"{self.title} model")
            pbar.update(1)

            self.next_model()
            try:
                self.walker.download_all(self.dir / "presentation")
            except SpiderError as e:
                logger.critical(
                    f"Failed to download presentation {self.title} because of {e!r}"
                )

            pbar.set_description("skip self picture")
            self.next_model()  # skip the self picture

            pbar.set_description(f"{self.title} extra stuff")
            self.next_model()
            try:
                self.walker.download_all(self.dir / "extra")
            except SpiderError as e:
                logger.critical(
                    f"Failed to download extra {self.title} because of {e!r}"
                )


if __name__ == "__main__":
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        spider = Spider(browser, type="SOFT", cont=0)
        spider.main()
