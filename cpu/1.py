from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import random
import pandas as pd
from fake_useragent import UserAgent
from datetime import date

# ================== 配置区 ==================
COOKIES_PATH = "cookies.json"
CPUS = ["i7-920", "i7-930", "i7-950", "i7-960", "i7-980X", "i5-750", "i5-760", 
"i3-530", "i3-540", "i3-2100", "i3-2120", "i3-2100T", "i5-2300", "i5-2400", "i5-2500K", 
"i5-2550K", "i7-2600", "i7-2600K", "i7-2700K", "i3-3220", "i3-3240T", "i5-3470", 
"i5-3570K", "i5-3550", "i7-3770", "i7-3770K", "i7-3820", "i3-4130", "i3-4330", "i5-4440", 
"i5-4690K", "i7-4770", "i7-4790K", "i5-4590", "i3-4360", "i7-5775C", "i5-5675C", 
"i7-6700K", "i7-6700", "i5-6600K", "i5-6600", "i5-6500", "i5-6400", "i3-6100", 
"i7-7700K", "i7-7700", "i5-7600K", "i5-7600", "i5-7500", "i5-7400", "i3-7350K", 
"i3-7300", "i3-7100", "i7-7700T", "i5-7600T", "i5-7500T", "i7-8700K", "i7-8700", 
"i7-8700T", "i5-8600K", "i5-8600", "i5-8500", "i5-8400", "i5-8400T", "i3-8350K", 
"i3-8300", "i3-8100"]       # 要搜索的CPU型号列表
PRICE_CSS_SELECTOR = "span[class^='number--']"  # 类名前缀匹配
SCROLL_TIMES = 3                                # 滚动次数
HEADLESS_MODE = False                           # 调试时关闭无头模式

# ================== 工具函数 ==================
def save_cookies(driver):
    """保存Cookies到文件"""
    driver.get("https://www.goofish.com")
    with open(COOKIES_PATH, 'w') as f:
        json.dump(driver.get_cookies(), f)
    print(f"[Cookies] 已保存至 {COOKIES_PATH}")

def load_cookies(driver):
    """加载Cookies并适配域名"""
    if not os.path.exists(COOKIES_PATH):
        return False
    
    driver.get("https://www.goofish.com")
    time.sleep(2)
    
    with open(COOKIES_PATH, 'r') as f:
        cookies = json.load(f)
    
    # 修正Cookie格式
    for cookie in cookies:
        if 'domain' in cookie and cookie['domain'].startswith('.'):
            cookie['domain'] = cookie['domain'][1:]
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"跳过无效Cookie: {cookie.get('name')}, 原因: {str(e)}")
    print("[Cookies] 加载完成")
    return True

def init_browser():
    """初始化浏览器（绕过检测）"""
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    
    # 反爬配置
    options.add_argument(f"user-agent={ua.random}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--ignore-certificate-errors")
    
    if HEADLESS_MODE:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    
    # 隐藏自动化特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
    })
    return driver

# ================== 核心逻辑 ==================
def scroll_to_bottom(driver):
    """模拟人类滚动行为"""
    current_height = 0
    for _ in range(SCROLL_TIMES):
        # 随机滚动距离（800-1200像素）
        scroll_pixels = random.randint(800, 1200)
        new_height = current_height + scroll_pixels
        driver.execute_script(f"window.scrollTo(0, {new_height});")
        current_height = new_height
        
        # 随机等待（1.5-3.5秒）
        time.sleep(random.uniform(1.5, 3.5))
        
        # 动态加载检测（可选）
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.body.scrollHeight") > current_height
            )
        except:
            pass

def get_prices(driver):
    """获取价格数据（带重试机制）"""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PRICE_CSS_SELECTOR))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, PRICE_CSS_SELECTOR)
        return [e.text for e in elements if e.text.strip()]
    except Exception as e:
        print(f"[错误] 价格获取失败: {str(e)}")
        return []

# ================== 主流程 ==================
def main():
    driver = init_browser()
    try:
        # 1. 登录与Cookies处理
        if not os.path.exists(COOKIES_PATH):
            driver.get("https://www.goofish.com")
            input("请手动登录后按回车保存Cookies...")
            save_cookies(driver)
        else:
            driver.get("https://www.goofish.com")
            load_cookies(driver)
        
        # 2. 遍历所有CPU型号
        result = {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "time": pd.Timestamp.now().strftime("%H:%M:%S")
        }
        
        for cpu in CPUS:
            # 构造目标URL
            target_url = f"https://www.goofish.com/search?q={cpu}"
            driver.get(target_url)
            print(f"当前页面标题（{cpu}）:", driver.title)
            
            # 3. 滚动加载数据
            all_prices = []
            for attempt in range(2):  # 最多重试2次
                scroll_to_bottom(driver)
                prices = get_prices(driver)
                if prices:
                    all_prices.extend(prices)
                    break
                elif attempt == 0:
                    print(f"[重试] {cpu} 首次获取失败，尝试重新加载...")
                    driver.refresh()
                    time.sleep(3)
            
            # 4. 数据处理（取最低价）
            if all_prices:
                try:
                    # 清洗价格（移除¥符号并转为数字）
                    clean_prices = [float(p.replace("¥", "").strip()) for p in all_prices]
                    result[cpu] = clean_prices
                except ValueError:
                    print(f"[错误] {cpu} 价格格式异常: {all_prices}")
                    result[cpu] = None
            else:
                result[cpu] = None
                print(f"[警告] {cpu} 未获取到价格")
        
        # 5. 保存结果（确保列顺序）
        save_dir = "./data"
        os.makedirs(save_dir, exist_ok=True)
        today = date.today().strftime("%Y-%m-%d")
        filename = os.path.join(save_dir, f"{today}_input.csv")
        df = pd.DataFrame([result]).reindex(columns=["date", "time"] + CPUS)
        df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
        print("数据保存完成，最新记录：")
        print(df)
            
    except Exception as e:
        print(f"[主流程异常] {str(e)}")
    finally:
        driver.quit()
        print("浏览器已关闭")

if __name__ == "__main__":
    main()