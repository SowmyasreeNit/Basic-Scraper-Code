import asyncio
import json
import re

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

results = []


async def main():

    crawler = PlaywrightCrawler(
        max_requests_per_crawl=5,
        headless=False
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext):

        page = context.page

        await page.wait_for_load_state("networkidle")

        # Get page title
        title = await page.title()

        # Get all text on page
        body_text = await page.locator("body").inner_text()

        # -------------------------
        # EMAIL EXTRACTION
        # -------------------------

        emails = re.findall(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            body_text
        )

        # -------------------------
        # PHONE EXTRACTION
        # -------------------------

        phones = re.findall(
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            body_text
        )

        # -------------------------
        # SOCIAL LINKS
        # -------------------------

        links = await page.locator("a").evaluate_all(
            """
            elements => elements.map(el => el.href)
            """
        )

        social_links = []

        for link in links:

            if any(site in link for site in [
                "instagram.com",
                "facebook.com",
                "tiktok.com",
                "twitter.com",
                "linkedin.com"
            ]):
                social_links.append(link)

        # -------------------------
        # HERO TEXT
        # -------------------------

        hero_text = ""

        h1s = await page.locator("h1").all_inner_texts()

        if h1s:
            hero_text = h1s[0]

        data = {
            "url": context.request.url,
            "business_name": title,
            "phone": list(set(phones)),
            "email": list(set(emails)),
            "social_links": list(set(social_links)),
            "hero_text": hero_text
        }

        results.append(data)

        print(json.dumps(data, indent=4))

    await crawler.run([
        "https://thriftshopofboston.org"
    ])

    with open("business_data.json", "w") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
