from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


process = CrawlerProcess(get_project_settings())
process.crawl("ambient")
process.crawl("back-in-stock")
process.crawl("basic-channel")
process.crawl("chicago-oldschool")
process.crawl("collectors-items")
process.crawl("colundi-everyone")
process.crawl("detroit-house")
process.crawl("detroit")
process.crawl("digital")
process.crawl("disco")
process.crawl("drexciya")
process.crawl("drum-n-bass")
process.crawl("electro")
process.crawl("electronica")
process.crawl("electronic")
process.crawl("essentials")
process.crawl("exclusives")
process.crawl("grime")
process.crawl("honest-jons")
process.crawl("house")
process.crawl("irdial-discs")
process.crawl("labels")
process.crawl("last-week")
process.crawl("mego")
process.crawl("new-global-styles")
process.crawl("outernational")
process.crawl("reggae")
process.crawl("reissues")
process.crawl("surgeon")
process.crawl("techno")
process.crawl("this-week")
process.crawl("wave")
process.start()
