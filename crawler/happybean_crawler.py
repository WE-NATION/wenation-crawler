import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def save_posts_to_json(posts, filename="data/happybean.json"):
    """게시글 데이터를 JSON 형식으로 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({"posts": posts}, f, ensure_ascii=False, indent=4)
    print(f"게시글 데이터를 {filename}에 저장했습니다.")

def get_posts_by_category(driver, category_name, category_button):
    """주어진 카테고리에 해당하는 게시글을 크롤링하여 JSON 파일로 저장"""
    
    campaign_id_counter = 200000

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_button)
    time.sleep(1)  

    try:
        category_button.click()
    except ElementClickInterceptedException:
        print(f"{category_name} 카테고리 버튼 클릭 재시도 중...")
        driver.execute_script("arguments[0].click();", category_button)  

    time.sleep(2) 

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "card"))
        )
        print(f"{category_name} 카테고리 페이지 로딩 완료")
    except TimeoutException:
        print(f"{category_name} 카테고리 페이지 로딩 대기 중 오류 발생")
        return []

    more_buttons = driver.find_elements(By.CLASS_NAME, "btn_horizontal_more")
    if more_buttons:  
        more_clicks = 0
        while more_clicks < 3:
            try:
                more_button = driver.find_element(By.CLASS_NAME, "btn_horizontal_more")
                driver.execute_script("arguments[0].click();", more_button)
                print(f"{category_name} 카테고리 - '더보기' 버튼 클릭 ({more_clicks + 1}번)")
                time.sleep(2)  
                more_clicks += 1
            except NoSuchElementException:
                print(f"{category_name} 카테고리 - 더 이상 '더보기' 버튼이 없습니다.")
                break
    else:
        print(f"{category_name} 카테고리에는 '더보기' 버튼이 없습니다.")

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    posts = []
    for item in soup.select('a.card'):
        title_tag = item.select_one('.card_title')
        organization_tag = item.select_one('.card_organization')
        percent_tag = item.select_one('.card_percent')
        money_tag = item.select_one('.card_money')
        link = item['href']
        image_tag = item.select_one('img.card_img') 

        campaign_id = campaign_id_counter
        campaign_id_counter += 1 

        if title_tag and organization_tag and percent_tag and money_tag:
            title = title_tag.get_text(strip=True)
            organization = organization_tag.get_text(strip=True)
            percent = percent_tag.get_text(strip=True)
            money = money_tag.get_text(strip=True)
            full_link = f'https://happybean.naver.com{link}'
            
            image_url = None
            if image_tag:
                image_url = image_tag['src'] 

            post_data = {
                'title': title,
                'organization': organization,
                'percent': percent,
                'money': money,
                'link': full_link,
                'campaign_id': campaign_id,
                'image_url': image_url,  
                'category_name': category_name, 
                'site_type': 'naver'  
            }

            posts.append(post_data)

    print(f"{category_name} 카테고리의 크롤링된 게시글 데이터:")
    print(posts) 

    save_posts_to_json(posts, filename="data/happybean.json")
    return posts
