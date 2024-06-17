import urllib
from scrapy.spiders import SitemapSpider


class Spider(SitemapSpider):
    name = 'example'
    allowed_domains = [ 'example.com' ]
    sitemap_urls = [ 'https://www.example.com/sitemap.xml' ]
    url_prefix = 'https://www.example.com'


    custom_settings = {
        'ACCEPT_LANGUAGE': 'en-US,en',
    }

    sitemap_rules = [('Article', 'parse_product')]

    def parse_product(self, response):
        self.logger.info('Visited %s', response.url)

        # check if we are on a product page
        if response.css(".page.articlepage"):
            
            url = None
            # get the first image that ends with .jpg
            for img in response.css("div.page.articlepage div.gallery img"):
                if img.attrib['src'].endswith('.jpg'):
                    url = img.attrib['src']
                    break
            
            if url is not None:
                
                # extract main label
                label = response.css("div.pageheader > h1::text").getall()[0]

                # extract data
                data = []
                data.extend(response.css("div.page.articlepage div.content.description p")[0].css("p::text").getall())

                # yield the data
                yield {
                    'url': urllib.parse.urljoin(self.url_prefix, url),
                    'web': {
                        'label': label,
                        'data': data
                    }
                }
            
