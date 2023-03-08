from selenium import webdriver
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_date():
    dates = []
    for i in range(2013, 2024):
        if i == 2013:
            dates.append(str(i) + '-12')
        else:
            for j in range(1, 13):
                if j < 10:
                    dates.append(str(i) + '-0' + str(j))
                else:
                    dates.append(str(i) + '-' + str(j))
    return dates


def spider(url):
    browser.get(url)
    time.sleep(2)
    text = browser.page_source

    # 通过text查找并记录所有样式
    soup = BeautifulSoup(text, 'html.parser')

    style = soup.find_all('style')
    # 获取style的文本
    style_text = style[0].text
    # 通过正则表达式获取所有的样式名
    style_name = re.findall('\.[a-zA-Z0-9]*', style_text)[7:]
    # 通过正则表达式获取所有大括号内的样式内容
    style_content = re.findall('\{([\s\S]*?)\}', style_text)[7:]
    # 将样式名和样式内容组合成字典
    style_dict = dict(zip(style_name, style_content))
    # 将字典中的样式内容的分号、空格和换行符去掉
    unvisible = []
    for key, value in style_dict.items():
        style_dict[key] = value.replace(';', '').replace(' ', '').replace('\n', '')
        if style_dict[key] == 'display:none':
            unvisible.append(key.replace('.', ''))

    # 获取所有table
    tables = soup.find_all('table')
    tables = [str(tables[0]), str(tables[1]), str(tables[2])]

    num = 0
    for i in range(3):
        # 如果tempstr中包含'-1500px'字符串，删除该表格
        if '-1500px' in tables[num] or 'opacity' in tables[num]:
            tables.pop(num)
            num -= 1
        num += 1
    table = tables[0]

    # 将table中'</td>'以及'</tr>'后添加换行符
    table = table.replace('</td>', '</td>\n')
    table = table.replace('</tr>', '</tr>\n')
    table = table.replace('<tr>', '<tr>\n')
    table = table.replace('</td>\n\n', '</td>\n')
    table = table.replace('</tr>\n\n', '</tr>\n')
    table = table.replace('<tr>\n\n', '<tr>\n')

    # 以换行符分割table
    table_s = table.split('\n')
    len = table_s.__len__()
    num = 0
    for i in range(3, len - 1):
        # 如果table_s中包含'-1500px'字符串，删除该行
        if (('hidden-lg' in table_s[num]) and ('hidden-md' in table_s[num]) and ('hidden-sm' in table_s[num])) \
                or ('display:none' in table_s[num]) \
                or ('class=\"hidden\"' in table_s[num]) \
                or ('-1500px' in table_s[num]):
            table_s.pop(num)
            num -= 1
        else:
            for j in unvisible:
                if j in table_s[num]:
                    table_s.pop(num)
                    num -= 1
                    break
        num += 1

    # 将table_s中的元素连接成字符串
    table = '\n'.join(table_s)

    df = pd.read_html(table)[0]

    return df


if __name__ == '__main__':
    dates = get_date()

    url = 'https://www.aqistudy.cn/historydata/monthdata.php?city=%E5%8C%97%E4%BA%AC'
    base_url = 'https://www.aqistudy.cn/historydata/daydata.php?city='
    # 声明浏览器对象
    option = webdriver.ChromeOptions()
    option.add_argument("start-maximized")
    option.add_argument("--disable-blink-features=AutomationControlled")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option("useAutomationExtension", False)
    browser = webdriver.Chrome(options=option)
    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''Object.defineProperty(navigator, 'webdriver', {
        get: () =>false'''
    })
    browser.get(url)
    # 点击'高级-继续访问'
    browser.find_element('id', 'details-button').click()
    browser.find_element('id', 'proceed-link').click()

    city = ['北京']
    list_data = []
    title_list = ['日期', 'AQI', '质量等级', 'PM2.5', 'PM10', 'SO2', 'CO', 'NO2', 'O3_8h']
    for ct in range(len(city)):
        for date in tqdm(dates):
            url = base_url + city[ct] + '&month=' + date
            df = spider(url)
            # 如果表格第一行第一个数据为'日期'，则表格包含表头,删除表头
            if df.values.tolist()[0][0] == '日期':
                df = df.drop(0, axis=0)
            list_data.extend(df.values.tolist()[:])
            time.sleep(1.5)

    browser.close()

    # 将数据写入csv文件
    all_data = pd.DataFrame(list_data)
    all_data.to_csv('data.csv', encoding='utf-8-sig', index=False, header=title_list)

