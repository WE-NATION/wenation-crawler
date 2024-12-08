import pymysql
import json

# MySQL에 연결하는 함수
def connect_to_db():
    connection = pymysql.connect(
        host='localhost',         
        #port= 3306,
        user="root",         
        password="root1234",  
        database="wenation",  
        charset='utf8mb4'   # 한글 저장을 위한 인코딩
    )
    return connection


# JSON 데이터를 MySQL에 저장하는 함수
def save_campaign_data_to_db(data):
    connection = connect_to_db()
    cursor = connection.cursor()

    # 데이터 삽입 쿼리
    sql = """
    INSERT INTO Campaign (likes_count, campaign_id, category_name, image_url, link, money, organization, percent, site_type, title)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for campaign in data:
        try:
            # 데이터베이스에 데이터 삽입
            cursor.execute(sql,(
                campaign.get("likes_count", 0), 
                campaign["campaign_id"],                     
                campaign["category_name"],                  
                campaign["image_url"],                      
                campaign["link"],                           
                campaign["money"],                          
                campaign["organization"],                   
                campaign["percent"],                        
                campaign["site_type"],                      
                campaign["title"]                              
            ))
        except Exception as e:
            print(f"Error saving campaign {campaign['campaign_id']}: {e}")
    
    connection.commit()
    cursor.close()
    connection.close()
    print("db 저장 완료.")

# JSON 파일을 읽고 데이터 저장
with open('./data/kakao.json', 'r', encoding='utf-8') as kakao_file:
    kakao_data = json.load(kakao_file)
# Cherry 
with open('./data/cherry.json', 'r', encoding='utf-8') as cherry_file:
    cherry_data = json.load(cherry_file)
# happybean 
with open('./data/happybean.json', 'r', encoding='utf-8') as happybean_file:
    happybean_data_raw = json.load(happybean_file)

happybean_data = []
for post in happybean_data_raw["posts"]:
    happybean_data.append({
        "likes_count": 0,  
        "campaign_id": post["link"].split("/")[-1],  # link에서 ID 추출
        "category_name": post["category_name"],
        "image_url": post["image_url"],
        "link": post["link"],
        "money": post["money"],
        "organization": post["organization"],
        "percent": post["percent"],
        "site_type": post["site_type"],
        "title": post["title"]
    })
# 데이터 합치기
combined_data = kakao_data + cherry_data + happybean_data


# MySQL에 저장
save_campaign_data_to_db(combined_data)
