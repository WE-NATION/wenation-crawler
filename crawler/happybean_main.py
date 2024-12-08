import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from happybean_crawler import get_posts_by_category  
from selenium.webdriver.common.by import By
import time

# campaign_id_counter를 전역 변수로 선언하여 모든 게시글에 대해 고유한 ID 부여
global_campaign_id_counter = 200000

def save_posts_to_json(posts, filename):
    # "posts" 데이터를 filename에 저장
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({"posts": posts}, f, ensure_ascii=False, indent=4)

def get_unique_campaign_id():
    global global_campaign_id_counter
    campaign_id = global_campaign_id_counter
    global_campaign_id_counter += 1
    return campaign_id

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get("https://happybean.naver.com/donation/DonateHomeMain")

    category_buttons = driver.find_elements(By.CSS_SELECTOR, ".category_theme_item a")[1:]
    categories = ["아동·청소년", "어르신", "장애인", "다문화", "지구촌", "가족·여성", "시민사회", "동물", "환경"] 

    all_posts = []  # 모든 카테고리의 게시글들을 여기에 저장
    
    for category_name, category_button in zip(categories, category_buttons):
        print(f"{category_name} 카테고리 크롤링 중...")
        posts = get_posts_by_category(driver, category_name, category_button)
        
        # 각 카테고리에서 반환된 게시글들에 대해 "post" 키 아래에 저장
        for post in posts:
            post["category_name"] = category_name  # 각 게시글에 카테고리 이름을 포함
            post["campaign_id"] = get_unique_campaign_id()  # 고유한 campaign_id 부여
        all_posts.extend(posts)  # 모든 게시글을 하나의 리스트로 합침

        time.sleep(2)  # 카테고리별 대기시간

    # 한 번만 "data/happybean.json"에 모든 게시글을 저장
    save_posts_to_json(all_posts, 'data/happybean.json')  # 전체 게시글을 "posts" 키 아래에 저장
    print("크롤링 완료: data/happybean.json 파일에 저장되었습니다.")

    driver.quit()

if __name__ == '__main__':
    main()
