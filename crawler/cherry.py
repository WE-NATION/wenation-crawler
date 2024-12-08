import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

URL = "https://cherry.charity/public/campaign/listPage?enterPage=cherryMain&searchType=A"
DONATE_SITE = "cherry"

# 카테고리 맵핑: 태그 기준으로 카테고리 분류
TAG_CATEGORY_MAP = {
    "아동·청소년": ["#아동", "#소아_청소년"],
    "동물": ["#유기동물", "#자연","#동물권", "#생명", "#유기견", "#환경_생태계"],
    "환경": ["#환경", "#환경_생태계", "#자연"],
    "장애인": ["#장애인"],
    "지구촌": ["#해외"],
    "어르신": ["#노인", "#취약계층_어르신"],
    "가족·여성": ["#여성", "#가정"]
}

# 크롬 드라이버 설정
def set_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--blink-settings=imagesEnabled=true')  # 이미지 로드 허용
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')     
    options.add_argument('incognito')
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option("useAutomationExtension", False)
    
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

class CherryCrawler:
    def __init__(self):
        self.driver = set_chrome_driver()

    def close_driver(self):
        self.driver.quit()

    
    # 텍스트 추출
    def get_element_text(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element.text
        except:
            return None

    # 캠페인 데이터 추출
    def get_campaign_data(self):
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, ".prflArea .tit").text.strip()
            org_name = self.get_element_text(By.CSS_SELECTOR, ".name")
            money = self.get_element_text(By.CSS_SELECTOR, ".sl_current")
            percent = self.get_element_text(By.CSS_SELECTOR, ".sl_percent")
            image_url = self.driver.find_element(By.CSS_SELECTOR, ".campaignVisual").get_attribute("data-imgurl")

            # 카테고리 결정
            tags = self.extract_tags()
            category_name = self.determine_category(tags)

            print(f"{title}, {percent}, {money} ,{org_name}, {category_name}")

            return {
                "title": title,
                "organization": org_name,
                "percent": percent,
                "money": money,
                "link": self.driver.current_url,
                "campaign_id": self.driver.current_url.split("/")[-1],
                "image_url": image_url,
                "category_name": category_name,
                "site_type": DONATE_SITE,
            }
        except Exception as e:
            print(f"Error while extracting campaign data: {e}")
            return None

    # 태그 텍스트 추출 함수
    def extract_tags(self):
        try:
            # 태그 리스트를 담고 있는 부모 요소 선택
            tag_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.sl_tagList > li.sl_tag > span")
            # 각 태그의 텍스트를 리스트로 추출
            tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
            print(f"추출된 태그: {tags}")  # 디버깅용 출력
            return tags
        except Exception as e:
            print(f"태그 추출 중 오류: {e}")
            return []    

    def determine_category(self, tags):
        for category, tag_list in TAG_CATEGORY_MAP.items():
            for tag in tags:
                if tag in tag_list:
                    return category
        return "기타"  # 매칭되지 않을 경우 기본값


    # 스크롤하여 페이지 로드
    def scroll_to_bottom(self):
        previous_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: self.driver.execute_script("return document.body.scrollHeight") > previous_height
                )
            except:
                print("더 이상 로드할 데이터가 없습니다.")
                break

            previous_height = self.driver.execute_script("return document.body.scrollHeight")


    # 캠페인 데이터 크롤링
    def crawl_campaigns(self):
        self.driver.get(URL)
        print("기본 페이지 접속 완료")
        time.sleep(5)
        self.scroll_to_bottom()
        print("스크롤 끝, 크롤링 시작")

        campaigns = self.driver.find_elements(By.CSS_SELECTOR, "li.campaign")   #게시물 리스트

            # 각 게시물에서 링크 추출
        campaign_links = []
        for campaign in campaigns:
            print("캠페인 추출 시작")
            try:
                onclick_value = campaign.get_attribute("onclick")
                campaign_id = onclick_value.split("(")[1].split(")")[0]  # 고유 ID 추출
                link = f"https://cherry.charity/public/campaign/cmpgnDtlPage/{campaign_id}"
                campaign_links.append(link)
                print(f"링크: {link}, 아이디: {campaign_id}")
            except Exception as e:
                print(f"링크 추출 중 오류: {e}")

        # 상세 데이터 크롤링
        campaign_data = []
        for link in campaign_links:
            try:
                self.driver.get(link)  # 링크로 이동
                time.sleep(2)  # 페이지 로드 대기
                data = self.get_campaign_data()  # 상세 데이터 수집
                if data:
                    campaign_data.append(data)
            except Exception as e:
                print(f"상세 데이터 크롤링 중 오류: {e}")

        return campaign_data


if __name__ == "__main__":
    print("Cherry 크롤링 시작")
    start_time = time.time()

    crawler = CherryCrawler()
    data = crawler.crawl_campaigns()
    crawler.close_driver()

    with open('./data/cherry.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    end_time = time.time()
    print(f"크롤링 완료: {end_time - start_time:.2f} 초")
