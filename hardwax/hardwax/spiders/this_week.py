import scrapy


class This_weekSpider(scrapy.Spider):
    name = "this-week"
    allowed_domains = ["hardwax.com"]
    page_number = 1

    def __init__(self, *args, **kwargs):
        super(This_weekSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://hardwax.com/{self.name}/?page=1"]

    def parse(self, response):
        print("URL:", response.url)
        divs = response.css("div.qv")
        print("Number of divs found:", len(divs))
        if divs:
            data_found = False
            for li in response.css("li"):
                div = li.css("div.qv")
                a_elements = div.css("a")
                if len(a_elements) >= 2:
                    label = a_elements[0].attrib["title"]
                    artist_album = a_elements[1].attrib.get("title", "")
                    if (
                        artist_album.count(":") == 1
                    ):  # Only process the element if title contains exactly one colon
                        artist, album = artist_album.split(":")
                        label_issue = a_elements[1].css("::text").get()
                        for a in li.css("a.sa"):
                            title = a.attrib.get("title", "")
                            if (
                                title.count(":") == 1
                            ):  # Only process the element if title contains exactly one colon
                                track = title.split(":")[1]

                                yield {
                                    "artist": artist.strip(),
                                    "album": album.strip(),
                                    "label": label.strip(),
                                    "label_issue": label_issue.strip(),
                                    "track": track.strip(),
                                }
                                data_found = True
            if data_found:
                self.page_number += 1
                next_page = f"https://hardwax.com/{self.name}/?page={self.page_number}"
                yield scrapy.Request(next_page, self.parse)
