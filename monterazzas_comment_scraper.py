from base import BaseScraper
from playwright.async_api import Locator
import asyncio, traceback, csv
from pathlib import Path
import random
from bs4 import BeautifulSoup

class MonterazzasCommentScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            output_filename="monterazzas-comments",
            retry_filename="monterazzas-comments-retry",
            headless=False,
        )

        self.csv_file = Path("outputs/monterazzas-comments.csv")
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)

        self.total_scraped = 0
        self.saved_comments = set()  

        with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["id", "comment"])

    async def locate_comments(self):
        locator = self.page.locator(
            "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl"
        ).locator("div.xdj266r.x14z9mp.xat24cr.x1lziwak.x1vvkbs")
        return await locator.all()

    async def extract_comment(self, comment_el: Locator):
        try:
            html = await comment_el.inner_html()
            soup = BeautifulSoup(html, "html.parser")

            for img in soup.find_all("img", alt=True):
                img.replace_with(img["alt"])

            text = soup.get_text(separator=" ").strip()
            return text
        except Exception as e:
            print("⚠ Failed to extract comment:", e)
            return ""

    async def append_to_file(self, text: str):
        if text in self.saved_comments:
            return
        self.saved_comments.add(text)
        self.total_scraped += 1
        with open(self.csv_file, "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([self.total_scraped, text])

    async def scroll_and_extract(self):
        """Scroll slowly and extract comments after each step."""
        container = self.page.locator(
            "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl"
        ).first

        box = await container.bounding_box()
        if not box:
            return 0

        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        await self.page.mouse.move(x, y)

        new_comments = 0

        for _ in range(random.randint(12, 18)):
            await self.page.mouse.wheel(0, random.randint(150, 300))
            await asyncio.sleep(random.uniform(1.5, 2.5))

            comments = await self.locate_comments()
            for comment_el in comments:
                text = await self.extract_comment(comment_el)
                if text and text not in self.saved_comments:
                    await self.append_to_file(text)
                    new_comments += 1

        return new_comments

    async def process(self):
        await self.start()

        try:
            print("🔗 Opening Facebook post...")
            await self.navigate_with_retry(
                "https://www.facebook.com/story.php?story_fbid=1234796515363433&id=100064992870078&rdid=opX5gf0Oyv2JslNy#"
            )

            await asyncio.sleep(6)

            no_new_attempts = 0
            while True:
                new = await self.scroll_and_extract()
                print(f"📌 New comments after scroll: {new}")

                if new == 0:
                    no_new_attempts += 1
                    print(f"⚠ No new comments... retry {no_new_attempts}/3")
                else:
                    no_new_attempts = 0

                if no_new_attempts >= 3:
                    print("🚩 No more content detected. Extraction completed.")
                    break

            print(f"💾 Total saved: {self.total_scraped}")

        except Exception:
            print(traceback.format_exc())

        finally:
            print(f"✅ Finished scraping. Total: {self.total_scraped} comments")
            print(f"📄 Output file: {self.csv_file}")
            await self.quit()


async def main():
    scraper = MonterazzasCommentScraper()
    await scraper.process()


if __name__ == "__main__":
    asyncio.run(main())
