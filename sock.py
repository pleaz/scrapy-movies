import pymysql.cursors
from bs4 import BeautifulSoup
from selenium import webdriver
from multiprocessing import Pool


connection = pymysql.connect(host='localhost',
                             user='',
                             password='',
                             db='movies',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


def get_frame(source):
    soup = BeautifulSoup(source, 'html.parser')
    div = soup.find('div', id='player')
    try:
        frame = div.find('iframe').attrs['src']
    except AttributeError:
        frame = False
    return frame


def ch_func(item):
    # options = webdriver.ChromeOptions()
    # preferences = {'profile.managed_default_content_settings.images': 2}
    # options.add_argument('window-size=640x480')
    # options.add_experimental_option('prefs', preferences)
    # driver = webdriver.Chrome(chrome_options=options)
    service_args = ['--load-images=no']
    driver = webdriver.PhantomJS(executable_path='/usr/local/lib/node_modules/phantomjs-prebuilt/lib/phantom/bin/phantomjs',service_args=service_args)
    driver.get(item['tmp_url'])
    elem = driver.page_source
    driver.close()
    frames = get_frame(elem)
    if frames is not False:
        with connection.cursor() as cursor_q:
            sql_q = 'UPDATE `sock` SET `one_url`=%s WHERE `id`=%s'
            cursor_q.execute(sql_q, (frames, item['id']))
    print(item['id'], 'is done')


def ff_func(item):
    driver = webdriver.Firefox()
    driver.get(item['tmp_url'])
    elem = driver.page_source
    driver.close()
    frames = get_frame(elem)
    if frames is not False:
        with connection.cursor() as cursor_q:
            sql_q = 'UPDATE `sock` SET `one_url`=%s WHERE `id`=%s'
            cursor_q.execute(sql_q, (frames, item['id']))
    else:
        with connection.cursor() as cursor_q:
            sql_q = 'UPDATE `sock` SET `one_url`=\'temp not found\' WHERE `id`=%s'
            cursor_q.execute(sql_q, (item['id']))
    print(item['id'], 'is done')


try:
    with connection.cursor() as cursor:
        sql = 'SELECT `id`, `tmp_url` FROM `sock` WHERE `one_url` = \'ready\''
        cursor.execute(sql)
        result = cursor.fetchall()

    # pool = Pool(16)
    pool = Pool(4)

    params = []
    for i in range(0, len(result)):
        params.append(result[i])

    for param in params:
        # pool.apply_async(ff_func, [param])
        pool.apply_async(ch_func, [param])

    pool.close()
    pool.join()


finally:
    connection.close()


