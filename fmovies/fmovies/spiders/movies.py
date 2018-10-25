# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest


class MoviesSpider(scrapy.Spider):
    name = 'movies'
    # allowed_domains = ['fmovies.is']
    # start_urls = ['http://www.useragentstring.com/']
    start_urls = ['https://fmovies.is/film/from-the-ashes.7jn88/zqwr12']

    def parse(self, response):
        script = """
        function main(splash)
          splash:init_cookies(splash.args.cookies)
          splash.plugins_enabled = true
          local url = splash.args.url
          assert(splash:go{
            splash.args.url,
            headers=splash.args.headers,
            http_method=splash.args.http_method,
            body=splash.args.body,
          })
          assert(splash:wait(0.5))
          local play = splash:select('#player > div.cover')
          play:mouse_click()
          splash:set_viewport_full()
          assert(splash:wait(4))
          return {
            html = splash:html()
          }
        end
        """
        sc = """
        function main(splash)
          local url = splash.args.url
          assert(splash:go{
            splash.args.url,
            headers=splash.args.headers,
            http_method=splash.args.http_method,
            body=splash.args.body,
          })
          --assert(splash:go(url))
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
        yield {
            'text': response.body
        }