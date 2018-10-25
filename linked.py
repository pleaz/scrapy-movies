import time
# from bs4 import BeautifulSoup
from selenium import webdriver


def ch_func(item):
    driver = webdriver.PhantomJS(
        executable_path='/usr/local/bin/phantomjs',
        # service_args=['--load-images=no']
    )
    # driver.set_window_size(640, 480)
    driver.get(item)
    # time.sleep(2)

    # elem = driver.page_source

    session_login = driver.find_element_by_xpath("//input [@id='session_key-login']")
    session_password = driver.find_element_by_xpath("//input [@id='session_password-login' and @class='password']")
    session_btn = driver.find_element_by_xpath("//input [@id='btn-primary' and  @class='btn-primary']")
    session_login.send_keys('')
    session_password.send_keys('')
    session_btn.click()

    time.sleep(5)
    driver.save_screenshot('after_submit.jpg')

    search = driver.find_element_by_xpath("//input [@placeholder='Search' and @class='ember-text-field ember-view']")
    search_btn = driver.find_element_by_xpath(
        "//button [@data-control-name='nav.search_button' and @class='nav-search-button']"
    )
    search.send_keys('Yahoo')
    search_btn.click()

    time.sleep(5)
    driver.save_screenshot('after_search.jpg')

    category_btn = driver.find_element_by_xpath(
        "//button [@data-control-name='vertical_nav_companies_toggle' and @data-vertical='COMPANIES']"
    )
    category_btn.click()

    time.sleep(5)
    driver.save_screenshot('after_category.jpg')

    company_btn = driver.find_element_by_xpath(
        "//a[1] [@data-control-name='search_srp_result' and @class='search-result__result-link ember-view']"
    )
    company_btn.click()

    time.sleep(30)
    driver.save_screenshot('after_company.jpg')

    driver.close()
    # return elem

print(ch_func('https://www.linkedin.com/uas/login'))
