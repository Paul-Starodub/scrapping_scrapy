import scrapy
from scrapy import Selector
from scrapy.http import Response
from selenium import webdriver
from selenium.webdriver.common.by import By


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["webscraper.io"]
    start_urls = [
        "https://webscraper.io/test-sites/e-commerce/static/computers/laptops"
    ]

    def __init__(self):
        super().__init__()
        self.driver = webdriver.Chrome()

    def close(self, reason):
        self.driver.close()

    def parse(self, response: Response, **kwargs):
        for product in response.css(".thumbnail"):
            yield {
                "title": product.css(".title::attr(title)").get(),
                "description": product.css(".description::text").get(),
                "price": float(
                    product.css(".price::text").get().replace("$", "")
                ),
                "rating": int(
                    product.css("p[data-rating]::attr(data-rating)").get()
                ),
                "num_of_reviews": int(
                    product.css(".ratings > p.pull-right::text")
                    .get()
                    .split()[0]
                ),
                "additional_info": {
                    "hdd_prices": self._parse_hdd_block_prices(
                        response, product
                    )
                },
            }
        next_page = (
            response.css(".pagination > li")[-1].css("a::attr(href)").get()
        )

        if next_page is not None:
            # next_page_url = response.urljoin(next_page)  # alternative
            # yield scrapy.Request(next_page_url, callback=self.parse)
            yield response.follow(
                next_page,
                callback=self.parse,
            )

    def _parse_hdd_block_prices(
        self, response: Response, product: Selector
    ) -> dict[str, float]:
        detailed_url = response.urljoin(
            product.css(".title::attr(href)").get()
        )
        self.driver.get(detailed_url)
        swatches = self.driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        prices = {}

        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    self.driver.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                )

        return prices
