# -*- coding: utf-8 -*-

import scrapy

# from linked.items import LinkedItem
from scrapy_splash import SplashRequest  # , SplashFormRequest
from datetime import datetime
import re


class LinkedinSpider(scrapy.Spider):

    name = "linkedin"
    allowed_domains = ['linkedin.com']
    start_urls = ['https://www.linkedin.com/']

    def __init__(self, query=None, *args, **kwargs):
        super(LinkedinSpider, self).__init__(*args, **kwargs)
        self.query = query.strip()

    def parse(self, response):
        script = """
        function main(splash)
            splash:init_cookies(splash.args.cookies)
            splash:set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5')
            splash:go(splash.args.url)
            local form = splash:select('#login')
            splash:wait(2)
            assert(form:fill({ session_key='', session_password='' }))
            assert(form:submit())
            splash:wait(3)
            splash:set_viewport_full()
            return {
                html = splash:html(),
                cookies = splash:get_cookies()
            }
        end
        """
        return SplashRequest(
            'https://www.linkedin.com/uas/login',
            self.check_login,
            endpoint='execute',
            args={
                'lua_source': script
            }
        )

    def check_login(self, response):
        check = response.xpath('//form[contains(@id, "login")]').extract_first()
        if check is None:
            self.logger.debug('Login success')
            # print(response.body)
            return self.find_company()
        else:
            self.logger.error('Login failed')

    def find_company(self):
        script = """
        function main(splash)
            splash:init_cookies(splash.args.cookies)
            splash:go(splash.args.url)
            splash:wait(3)
            splash:set_viewport_full()
            return {
                html = splash:html(),
                cookies = splash:get_cookies()
            }
        end
        """
        yield SplashRequest(
            'https://www.linkedin.com/search/results/companies/?keywords='+self.query,
            self.parse_result,
            endpoint='execute',
            args={
                'lua_source': script
            }

        )

    def parse_result(self, response):
        company_page = response.xpath(
            '//ul[contains(@class, "results-list")]/li[contains(@class, "search-result")][1]//a/@href'
        ).extract_first()
        if company_page:
            #local scroll_to = splash:jsfunc("window.scrollTo")
            #scroll_to(0, 600)
            #scroll_to(0, 1200)
            #scroll_to(0, 1800)
            script = """
            function main(splash)
                splash:init_cookies(splash.args.cookies)
                splash:go(splash.args.url)
                assert(splash:wait(4))
                splash.scroll_position = {y=600}
                assert(splash:wait(4))
                splash.scroll_position = {y=1200}
                assert(splash:wait(4))
                splash.scroll_position = {y=1800}
                assert(splash:wait(4))
                splash.scroll_position = {y=2400}
                assert(splash:wait(4))
                splash:set_viewport_full()
                return splash:html()
            end
            """
            yield SplashRequest(
                response.urljoin(company_page.strip()),
                self.page_parse,
                endpoint='execute',
                args={
                    'lua_source': script
                }
            )

    # @staticmethod
    def page_parse(self, response):
        item = {}

        headcount = response.xpath(
            '//div[@class="org-insights-module org-insights-headcount-module module ember-view"]')
        if headcount:
            item['employee_count'] = {}
            item['employee_count']['stats'] = {}
            for dates in headcount.xpath('.//tr[contains(., td[@headers="org-insight-headcount__a11y-date"])]'):
                date = dates.xpath('.//td[@headers="org-insight-headcount__a11y-date"]/text()').extract_first()
                num = dates.xpath('.//td[@headers="org-insight-headcount__a11y-num-employees"]/text()').extract_first()
                if date:
                    item['employee_count']['stats'][date] = num

            total_num = headcount.xpath(
                './/td[@headers="org-insights-module__a11y-summary-total"]//text()[normalize-space()]'
            ).extract_first()
            if total_num:
                item['employee_count']['total_employees'] = total_num.strip()

            avg_tenure = headcount.xpath('.//div[@class="org-insights-module__facts"]//strong/text()').extract_first()
            if avg_tenure:
                item['employee_count']['avg_tenure'] = avg_tenure

            item['employee_count']['growth'] = {}
            growth6 = headcount.xpath(
                    './/td[@headers="org-insights-module__a11y-summary-6"]//span[@class="visually-hidden"]/text()'
            ).extract_first()
            if growth6:
                item['employee_count']['growth']['6months'] = growth6
            growth12 = headcount.xpath(
                    './/td[@headers="org-insights-module__a11y-summary-12"]//span[@class="visually-hidden"]/text()'
            ).extract_first()
            if growth12:
                item['employee_count']['growth']['1year'] = growth12
            growth24 = headcount.xpath(
                    './/td[@headers="org-insights-module__a11y-summary-24"]//span[@class="visually-hidden"]/text()'
            ).extract_first()
            if growth24:
                item['employee_count']['growth']['2years'] = growth24

        distributions = response.xpath('//section[@class="org-insights-module org-insights-functions-growth insights-functions-module module ember-view"]')
        if distributions:
            item['employee_distribution'] = {}
            item['employee_distribution']['functions'] = {}
            for distribution in distributions.xpath(
                    './/div[@class="org-function-growth-table"]/table[@class="visually-hidden"]/tr[./td]'):
                function_name = distribution.xpath(
                    './/td[@headers="org-function-growth-table__a11y-functions-function"]/text()').extract_first()
                num_employees = distribution.xpath(
                    './/td[@headers="org-function-growth-table__a11y-functions-num-employees"]/text()').extract_first()
                percentage = distribution.xpath(
                    './/td[@headers="org-function-growth-table__a11y-functions-percentage"]/text()').extract_first()
                growth_6months = distribution.xpath(
                    './/td[@headers="org-function-growth-table__a11y-functions-6"]//span[@class="visually-hidden"]/text()').extract_first()
                growth_12months = distribution.xpath(
                    './/td[@headers="org-function-growth-table__a11y-functions-12"]//span[@class="visually-hidden"]/text()').extract_first()

                if function_name:
                    item['employee_distribution']['functions'][function_name] = {}
                    if num_employees:
                        item['employee_distribution']['functions'][function_name]['num_employees'] = num_employees.strip()
                    if percentage:
                        item['employee_distribution']['functions'][function_name]['percentage'] = percentage.strip()
                    if growth_6months:
                        item['employee_distribution']['functions'][function_name]['growth_6months'] = growth_6months.strip()
                    if growth_12months:
                        item['employee_distribution']['functions'][function_name]['growth_12months'] = growth_12months.strip()

            current_month = distributions.xpath(
                './/div[contains(@class, "org-insights-functions-growth__chart")]/h6/text()').extract_first()
            if current_month:
                item['employee_distribution']['current_month'] = current_month.strip()

        hires = response.xpath('//section[@class="org-insights-module org-insights-newhires-module module ember-view"]')
        if hires:
            item['hires'] = {}
            for hire in hires.xpath('.//div[@class="org-premium-container__content"]/table[@class="visually-hidden"]//tr[./td]'):
                hire_name = hire.xpath('.//td[@headers="org-insights-newhires-module__a11y-date"]/text()').extract_first()
                senior_hires = hire.xpath('.//td[@headers="org-insights-newhires-module__a11y-senior-hires"]/text()').extract_first()
                other_hires = hire.xpath('.//td[@headers="org-insights-newhires-module__a11y-other-hires"]/text()').extract_first()
                if hire_name:
                    item['hires'][hire_name] = {}
                    if senior_hires:
                        item['hires'][hire_name]['senior_hires'] = senior_hires.strip()
                    if other_hires:
                        item['hires'][hire_name]['other_hires'] = other_hires.strip()

        jobs = response.xpath('//section[@class="org-insights-module org-insights-functions-growth org-insights-jobs-module ember-view"]')
        if jobs:
            item['jobs'] = {}
            item['jobs']['functions'] = {}
            for job in jobs.xpath(
                    './/div[@class="org-function-growth-table"]/table[@class="visually-hidden"]/tr[./td]'):
                function_name = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-function"]/text()').extract_first()
                num_employees = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-num-employees"]/text()').extract_first()
                percentage = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-percentage"]/text()').extract_first()
                growth_3months = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-3"]//span[@class="visually-hidden"]/text()').extract_first()
                growth_6months = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-6"]//span[@class="visually-hidden"]/text()').extract_first()
                growth_12months = job.xpath(
                    './/td[@headers="org-function-growth-table__a11y-jobs-12"]//span[@class="visually-hidden"]/text()').extract_first()

                if function_name:
                    item['jobs']['functions'][function_name] = {}
                    if num_employees:
                        item['jobs']['functions'][function_name]['num_employees'] = num_employees.strip()
                    if percentage:
                        item['jobs']['functions'][function_name]['percentage'] = percentage.strip()
                    if growth_3months:
                        item['jobs']['functions'][function_name]['growth_3months'] = growth_3months.strip()
                    if growth_6months:
                        item['jobs']['functions'][function_name]['growth_6months'] = growth_6months.strip()
                    if growth_12months:
                        item['jobs']['functions'][function_name]['growth_12months'] = growth_12months.strip()

            current_date = jobs.xpath(
                './/div[contains(@class, "org-insights-functions-growth__chart")]/h6/text()').extract_first()
            if current_date:
                item['jobs']['current_date'] = current_date.strip()

        company_id = re.findall(r'/([0-9]+)/', response.url)
        if company_id:
            item['company_id'] = company_id[0]
        real_name = response.xpath('//h1/text()').extract_first()
        if real_name:
            item['real_name'] = real_name.strip()
        query_name = self.query
        if query_name:
            item['query_name'] = query_name
        followers = response.xpath(
            '//span[contains(@class, "org-top-card-module__followers-count")]/text()[normalize-space()]').extract_first()
        if followers:
            item['followers'] = followers.strip()

        i = datetime.now()
        item['datetime'] = i.strftime('%Y/%m/%d %H:%M:%S')

        yield item
