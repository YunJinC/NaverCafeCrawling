# 네이버 카페 수집
---
## 주요 함수 설명
- def naver_session(self, nid, npw) : 네이버 로그인을 하는 함수
- def getArticleList(self, cafe_id, board_id, page) : 게시글 리스트를 얻는 함수
- def getArticleHtml(self, cafe_id, board_id, article_id) : 게시글을 수집
- def getCommentHtml(self, cafe_id, board_id, article_id, page) : 댓글을 수집
---
## 사용방법
- 객체 생성
```
n = NaverCafe()
```
- 로그인
```
n.naver_session('MYID', 'MYPW')
```
- 게시글 리스트 수집
```
#cafe_id, board_id, start_page_num, end_page_num 변수 셋팅
cafe_id = '10295448' # AUTOWAVE
board_id = '655'  #정비인멤버
start_page_num = 0
end_page_num = 10
df = []
for page in range(start_page_num, end_page_num):
    print(page)
    df.append(n.getArticleList(cafe_id, board_id, page))
```
- 게시글 내용 수집
```
c_df = []
for idx in range(len(df)):
    print(idx)
    values = []
    for article_idx in df[idx]['row_id']:
        values.append(n.getArticleHtml(cafe_id, board_id, article_idx))
    c_df.append(pd.DataFrame(values, columns=['row_id', 'content_data', 'img_yn', 'html_data']))
```
- 게시글 리스트와 게시글 내용 합치기
```
m_df = []
for idx in range(len(df)):
    m_df.append(pd.merge(df[idx], c_df[idx]))
m_df = pd.concat(m_df)
```
