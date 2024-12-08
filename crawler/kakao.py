import time 
import random
from selenium.webdriver.common.by import By #HTML 요소를 찾기 위한 방법
from selenium.webdriver.support.ui import WebDriverWait #특정 요소가 로딩될 때까지 대기하는 조건
from selenium.webdriver.support import expected_conditions as EC# ^^^
from campaign import * #캠페인 데이터를 담는 클래스 파일
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager #Selenium으로 크롬 브라우저 관리
import json
from selenium.common.exceptions import StaleElementReferenceException
import pickle

URL = "https://together.kakao.com/fundraisings/now?"
DONATE_SITE = "kakao"

categories = {
    "아동·청소년": "categoryId=10",
    "동물": "categoryId=11",
    "환경": "categoryId=12",
    "장애인": "categoryId=13",
    "지구촌": "categoryId=14",
    "어르신": "categoryId=15",
    "사회": "categoryId=16"
}


# 크롬 드라이버 함수로 설정
def set_chrome_driver():
    options = webdriver.ChromeOptions()
    # 자동화 탐지 해결..
    #options.add_argument("--start-maximixed")
    #options.add_argument('headless')  # 웹 브라우저를 띄우지 않는 headless chrome 옵션 
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')     
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('incognito')
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install(), chrome_options=options))
    return driver


class KakaoCrawler:
    def __init__(self):
        self.driver = set_chrome_driver()   #시작할때 크롬 드라이버 열기
        self.seen_campaign_ids = set()  # 중복 체크용 집합

    def close_driver(self):
        self.driver.quit()
    
    def get_campaign_id(self, page_url):    #https://together.kakao.com/fundraisings/119996/story
        print("현재 url: " , page_url)
        return page_url.split("/")[4]   
    
    #텍스트 추출
    def get_element_text(self, by, value, timeout=10):  #지연, 예외 조건 안전하게 처리
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            print(f"추출된 텍스트({value}):", element.text)
            return element.text #내용 반환
        except:
            print(f"Failed to retrieve element by {by} with value {value}")
            return None


    def get_campaign_data(self, page_url, category_name):  #클래스로 못찾아서 css로 처리
        print("===get_campaign()===")
        print(f"캠페인 데이터 수집 중: {page_url}")

        campaign_id = self.get_campaign_id(page_url)

        # 중복 체크: 크롤링하는 과정에서 중복되는듯 함
        if campaign_id in self.seen_campaign_ids:
            print(f"Duplicate campaign_id {campaign_id} detected. Skipping.")
            return None

        self.seen_campaign_ids.add(campaign_id)  # 중복 체크에 추가

        url = page_url
        site_type = DONATE_SITE
        title = self.get_element_text(By.CSS_SELECTOR, "div[class^='sc-30093360'] h3[class^='sc-bad07a1e-0']")
        org_name = self.get_element_text(By.CSS_SELECTOR, "div[class^='sc-6cea5c55'] strong[class^='sc-bfd3080f-0']")
        thumbnail = self.driver.find_element(By.CSS_SELECTOR, "div[class^='sc-bad07a1e-0'] div[class^='sc-69ad430e-0']").get_attribute('src')
        money = self.driver.find_element(By.CSS_SELECTOR, "li.sc-7aaee6b6-2 span.sc-bfd3080f-0").text.strip() #'원' 포함
        percent = self.driver.find_element(By.CSS_SELECTOR, "div.sc-bad07a1e-0 span[aria-hidden='true']").text.strip().split()[1]
        print(f"가격: {money}")
        print(f"퍼센트: {percent}")
        print(f"썸네일 {thumbnail}")

        print(f"카테고리: {category_name}, ")
        return {
            "title": title,
            "organization": org_name,
            "percent": percent,                       
            "money": money,
            "link" : url,
            "campaign_id": campaign_id,
            "image_url": thumbnail,
            "category_name": category_name,  # 카테고리 추가
            "site_type" : site_type,
        }
    

    def get_dates(self):
        date_element = self.driver.find_element(By.CSS_SELECTOR, "ul.sc-7aaee6b6-1.lapLYi > li.sc-7aaee6b6-2.gqtpee.undefined:nth-of-type(2) span.sc-bfd3080f-0.cEa-dwF").text
        txt_date = date_element.strip().split("~")
        start_date = txt_date[0].strip().replace('.', '-').replace(' ', '') # 출력: 2024-10-10
        due_date = txt_date[1].strip().replace('.', '-').replace(' ', '')
        return start_date, due_date
    def get_prices(self):
        status_price = self.driver.find_element(By.CSS_SELECTOR, "li.sc-7aaee6b6-2.gqtpee.undefined > span.sc-bfd3080f-0.fSDYcU").text.split("원")[0].replace(',', '')
        target_price = self.driver.find_element(By.CSS_SELECTOR, "div.sc-2763473e-4.jnmCPM.ratio_count em").text.split()[2].strip("원").replace(',', '')
        return status_price, target_price


    def scroll_to_bottom(self):
        for _ in range(10000000000): # 최대 10000번 스크롤 실행
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);') #최하단까지 스크롤
            time.sleep(1)
            # 현재 페이지 높이와 스크롤 위치를 비교하여 더 이상 스크롤할 부분이 없는지 확인
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_height = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
            # 스크롤 끝에 도달했을 경우 루프 중단
            if current_height >= scroll_height:
                break


    def crawl_category_campaigns(self, category_name, category_param):
        category_url = URL + category_param  #아동·청소년 카테고리: "https://together.kakao.com/fundraisings/now?categoryId=10"
        self.driver.get(category_url)   #해당 카테고리 페이지로 이동

        time.sleep(5)
        self.scroll_to_bottom() 

        WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "sc-8c7fd3f-0"))
        )

        campaign_urls = []
        # 요소가 사라지거나 유효하지 않을 경우 재시도
        for _ in range(5):  # 최대 5번 시도
            try:
                campaign_urls = [card.get_attribute('href') for card in self.driver.find_elements(By.CLASS_NAME, "sc-8c7fd3f-0")
                                 if 'together.kakao.com/fundraisings/' in card.get_attribute('href')]
                print(f"추출된 캠페인 URL 리스트: {campaign_urls}")
                break  # 성공하면 루프 종료
            except StaleElementReferenceException:
                print("요소를 다시 찾습니다.")
                time.sleep(2)  # 대기 후 재시도

        campaign_data = []
        for page_url in campaign_urls:  #추출한 캠페인 URL을 하나씩 방문하여 데이터 수집
            print(f"캠페인 페이지 접근 중: {page_url}")
            self.driver.get(page_url)
            time.sleep(1)  # 페이지 로딩 대기

            #함수 호출
            campaign = self.get_campaign_data(page_url, category_name)
            if campaign:
                campaign_data.append(campaign)
        return campaign_data


    def crawl_all_categories(self): #카테고리별로 캠페인 크롤링
        all_campaigns = []
        for category_name, category_param in categories.items(): #"아동·청소년": "categoryId=10"
            print(f"카테고리 '{category_name}' 크롤링 중...")
            campaigns = self.crawl_category_campaigns(category_name, category_param)
            all_campaigns.extend(campaigns)
        return all_campaigns
    

if __name__ == '__main__':
    print("카카오같이가치 크롤링 시작")
    start_time = time.time()

    crawler = KakaoCrawler()
    data = crawler.crawl_all_categories()   
    crawler.close_driver()

    with open('./data/kakao.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    end_time = time.time()
    print(f"크롤링 완료: {end_time - start_time:.2f} 초")


