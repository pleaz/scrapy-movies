# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest


class MoviesSpider(scrapy.Spider):
    name = 'freez'
    # allowed_domains = ['123moviesfreez.com']
    # start_urls = ['http://123moviesfreez.com/']
    start_urls = ['http://123moviesfreez.com/list/movies.html']

    def parse(self, response):
        pages = response.xpath('//div[@class="ml-item"]/a/@href').extract()
        for url in pages:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_page)

        next_page = response.xpath('//ul[@class="pagination"]/li/a[@title="Next"]/@href').extract_first()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse
            )

    def parse_page(self, response):
        script = """
        function main(splash)
          local url = splash.args.url
          assert(splash:go(url))
          assert(splash:wait(1))
          local server = splash:select('a[data-server="11"]')
          if server then
            server:mouse_click()
            assert(splash:wait(2))
          end
          return {
            html = splash:html()
          }
        end
        """
        return SplashRequest(
            response.url,
            self.save_all,
            endpoint='execute',
            args={
                'lua_source': script,
                'images': 0,
                'wait': 0.5,
                'timeout': 3600.0,
                'headers': {
                    'Accept': '*/*',
                    'Accept-Language': 'en-us',
                    'Connection': 'Keep-Alive',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
                }
            }
        )

    @staticmethod
    def save_all(response):
        link = response.xpath('//div[@id="mediaplayer"]//div[@class="me-cannotplay"]/a/@href').extract_first()
        name = response.xpath('//h3/a/@title').extract_first()
        imdb = response.xpath('//div[@class="mvici-right"]//a/@href').extract_first()
        year = response.xpath(
            '//div[@class="mvici-right"]/p/text()[preceding-sibling::strong[contains(text(),"Release:")]]'
        ).extract_first()
        item = {}
        if name:
            item['name'] = name.strip()
        if link:
            item['link'] = link.strip()
        if imdb:
            item['imdb'] = imdb.strip()
        if year:
            item['year'] = year.strip()
        item['page_url'] = response.url

        yield item
