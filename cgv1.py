

from selenium import webdriver
from bs4 import BeautifulSoup
import time,re,csv


# 긍정 부정
POS={"재밌","재미","최고","감동","추천","만족","훌륭","몰입","소름","완성도","대박","굴잼","멋지"}
NEG={"별로","지루","실망","최악","아쉽","후회","노잼","망작","욕","어이없","엉망","짜증","불쾌"}

def datarabeling(text: str) -> str | None:
    t=text.strip()
    t=re.sub(r"\n+"," ",t)
    t = re.sub(r"[^0-9A-Za-zㄱ-ㅎ가-힣\s]", "", t)
    if len(t)<5:
        return None
    return t

def score(text: str) -> str:
   pos=sum(1 for w in POS if w in text)
   neg=sum(1 for w in NEG if w in text)

   if pos> neg:
       return "positive"
   if pos< neg:
       return "negative"
   else:
       return "normal"
# 최대 리뷰갯수 300개 까지 30번 도전해본다고 설정       
def load_more_reviews(driver,selector:str,target_count:int=300,max_rounds: int=30):
    prev_count=0 # 이전 루프에서 봤던 리뷰 개수
    same_count_rounds=0 # 스크롤 내린뒤 안늘어난게 몇번 연속인지
    for _ in range(max_rounds): # 30번까지 최대
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cur_count = len(soup.select(selector)) # 지금화면 보이는 리뷰 개수
        if cur_count==prev_count:
            same_count_rounds+=1
        else :
            same_count_rounds=0
        if same_count_rounds >= 3:
            break   # 종료  

        prev_count = cur_count
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)
# csv 파일생성
csv_file = open("cgv_reviews.csv", "w", newline="", encoding="utf-8-sig")
writer = csv.writer(csv_file)
writer.writerow(["movie_title", "review", "clean_review", "label"])

driver = webdriver.Chrome()
url="https://cgv.co.kr/cnm/cgvChart/movieChart?tabParam=123"
driver.get(url)
time.sleep(3)


driver.execute_script("window.scrollTo(0,2000)")
time.sleep(2)

#  1) 차트 HTML 파싱 
soup=BeautifulSoup(driver.page_source,"html.parser")
sect_movie_chart=soup.select_one(".cnms01010_chartSection__SjydY")
movie_chart=sect_movie_chart.select("li")

#  2) 일단 10개만 테스트
for i, movie in enumerate(movie_chart[:10]):
    title = movie.select_one(".bestChartList_name__sZyhY").text.strip()
    print("제목:", title)

  

    #  3) 이제 클릭은 Selenium이 해야 함 (BS는 클릭 불가)
    #    -> 같은 i번째 영화의 "상세보기" 버튼을 Selenium에서 찾아 클릭
    buttons = driver.find_elements("xpath", "//button[contains(., '상세보기')]")
    
    buttons[i].click()
    time.sleep(2)

    # 4) 이동된 URL이 상세페이지 URL
    detail_url = driver.current_url
    print("상세 URL:", detail_url)

    #  5) 상세페이지 HTML을 다시 BS로 파싱해서 리뷰 뽑기
    review_selector = ".reveiwCard_txt__RrTgu"
    load_more_reviews(driver, review_selector, target_count=300, max_rounds=40) 
    
    
    
    
    detail_soup = BeautifulSoup(driver.page_source, "html.parser")

    # 리뷰 페이지
    review_els = detail_soup.select(".reveiwCard_txt__RrTgu")
    pos_cnt=0
    neg_cnt=0
    nor_cnt=0

    for r in review_els[:300]:
        print("리뷰:", r.get_text(strip=True))
        review=r.get_text(strip=True)
        clean_review=datarabeling(review)
        if not clean_review:
            continue

        labeling=score(clean_review)
        if labeling == "positive":
            pos_cnt+=1
        elif labeling == "negative":
            neg_cnt+=1
        else:
            nor_cnt+=1


        writer.writerow([title, review, clean_review, labeling])    
    total=pos_cnt+neg_cnt+nor_cnt
    if total==0:
        print("리뷰없음")
    else:
        # 5+3+2   50.0 30.0 20.0 
        pos_cnt= round((pos_cnt/total)*100,1)
        neg_cnt= round((neg_cnt/total)*100,1)
        nor_cnt=round((nor_cnt/total)*100,1)

        print(f"총 리뷰수 : {total}")
        print(f"긍정 : {pos_cnt} ({pos_cnt}%)")
        print(f"부정:{neg_cnt} ({neg_cnt})%")
        print(f"중립:{nor_cnt} ({nor_cnt}%)")
    


    # print("-"*40)

    #  뒤로가기(다음 영화 처리 위해)
    driver.back()
    time.sleep(2)

driver.quit()
csv_file.close()
print("csv저장확인")
