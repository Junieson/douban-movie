# 需求：破解滑块验证码，完成登录
import json
import random

from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import time
# 导入动作链
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# 获取轨迹
def get_tracks(distance, rate=0.6, t=0.2, v=0):
    """
    将distance分割成小段的距离
    :param distance: 总距离
    :param rate: 加速减速的临界比例
    :param a1: 加速度
    :param a2: 减速度
    :param t: 单位时间
    :param t: 初始速度
    :return: 小段的距离集合
    """
    tracks = []
    # 加速减速的临界值
    mid = rate * distance
    # 当前位移
    s = 0
    # 循环
    while s < distance:
        # 初始速度
        v0 = v
        if s < mid:
            a = 20
        else:
            a = -3
        # 计算当前t时间段走的距离
        s0 = v0 * t + 0.5 * a * t * t
        # 计算当前速度
        v = v0 + a * t
        # 四舍五入距离，因为像素没有小数
        tracks.append(round(s0))
        # 计算当前距离
        s += s0

    return tracks


def slide(driver):
    """滑动验证码"""
    print("正在滑动验证码")
    # 切换iframe
    driver.switch_to.frame(1)
    #找到滑块
    try:
        block = driver.find_element_by_xpath('//*[@id="tcaptcha_drag_button"]')
    except:
        time.sleep(3)
        block = driver.find_element_by_xpath('//*[@id="tcaptcha_drag_button"]')
    #找到刷新
    reload = driver.find_element_by_xpath('//*[@id="reload"]')
    while True:
        # 摁下滑块
        ActionChains(driver).click_and_hold(block).perform()
        # 移动
        ActionChains(driver).move_by_offset(180, 0).perform()
        #获取位移
        tracks = get_tracks(30)
        #循环
        for track in tracks:
            #移动
            ActionChains(driver).move_by_offset(track, 0).perform()
        # 释放
        ActionChains(driver).release().perform()
        #停一下
        time.sleep(2)
        #判断
        if driver.title == "登录豆瓣":
            print("失败...再来一次...")
            #单击刷新按钮刷新
            reload.click()
            # 停一下
            time.sleep(2)
        else:
            break

def isElementExist(driver, element):
    flag = True
    browser = driver
    try:
        browser.find_element_by_id(element)
        return flag

    except:
        flag = False
        return flag



def load_web(href):
    """主程序"""
    url=href
    option = Options()
    #无头浏览器
    option.headless = False
    driver = webdriver.Chrome(options=option)
    # driver.set_window_size(900, 900)
    driver.get(url)
    print("打开浏览器")
    zh = ["junieson@163.com","sjj50179@163.com","1151453117@qq.com","1687680445@qq.com"]
    driver.find_element_by_xpath('//*[@id="account"]/div[2]/div[2]/div/div[1]/ul[1]/li[2]').click()
    id = random.choice(zh)
    print("输入账号%s"%id)
    driver.find_element_by_xpath('//*[@id="username"]').send_keys(id)
    driver.find_element_by_xpath('//*[@id="password"]').send_keys("song135790")
    driver.find_element_by_xpath('//*[@id="account"]/div[2]/div[2]/div/div[2]/div[1]/div[4]/a').click()
    # 停一下，等待出现
    print("登录...")
    # 有时候滑块没加载出来
    time.sleep(3)
    if isElementExist(driver,"t_mask"):
        slide(driver)


    print("登录成功")
    # href1="https://www.douban.com/doulist/1641439/?start=0"
    # driver.get(href1)
    time.sleep(2)
    cookies = driver.get_cookies()
    driver.quit()
    jsonCookies = json.dumps(cookies)  # 通过json将cookies写入文件
    with open('dbCookies.json', 'w') as f:
        f.write(jsonCookies)
    print(cookies)

