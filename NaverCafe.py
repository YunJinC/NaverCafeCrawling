import re
import uuid
import requests
from bs4 import BeautifulSoup
import rsa
import lzstring
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import os
import pandas as pd
import json

class NaverCafe:
    
    def __init__(self):
        self.board_base_url = 'https://cafe.naver.com/ArticleList.nhn'
        self.article_base_url = 'https://cafe.naver.com/autowave21/ca-fe/ArticleRead.nhn'
        self.comment_base_url = 'http://cafe.naver.com/CommentView.nhn'
        self.base_path = 'D:\\00.프로젝트\\[20.04][제안] K-data 데이터 바우처\\01.수집\\해시넌스\\'
        self.headers = { 
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    
    def encrypt(self, key_str, uid, upw):
        def naver_style_join(l):
            return ''.join([chr(len(s)) + s for s in l])

        sessionkey, keyname, e_str, n_str = key_str.split(',')
        e, n = int(e_str, 16), int(n_str, 16)

        message = naver_style_join([sessionkey, uid, upw]).encode()

        pubkey = rsa.PublicKey(e, n)
        encrypted = rsa.encrypt(message, pubkey)

        return keyname, encrypted.hex()


    def encrypt_account(self, uid, upw):
        key_str = requests.get('https://nid.naver.com/login/ext/keys.nhn').content.decode("utf-8")
        return self.encrypt(key_str, uid, upw)


    def naver_session(self, nid, npw):
        encnm, encpw = self.encrypt_account(nid, npw)

        s = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        s.mount('https://', HTTPAdapter(max_retries=retries))
        request_headers = {
            'User-agent': 'Mozilla/5.0'
        }

        bvsd_uuid = uuid.uuid4()
        encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (bvsd_uuid, nid, nid, npw)
        bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))

        resp = s.post('https://nid.naver.com/nidlogin.login', data={
            'svctype': '0',
            'enctp': '1',
            'encnm': encnm,
            'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
            'url': 'www.naver.com',
            'smart_level': '1',
            'encpw': encpw,
            'bvsd': bvsd
        }, headers=request_headers)

        finalize_url = re.search(r'location\.replace\("([^"]+)"\)', resp.content.decode("utf-8")).group(1)
        s.get(finalize_url)

        self.s = s
    
    def makeDir(self, path):
        if not(os.path.isdir(path)):
            os.makedirs(os.path.join(path))
        
    def downloadImage(self, url, path):
        res = requests.get(url, headers=self.headers)
        with open(path, 'wb') as f:
            f.write(res.content)
            
    def getBoardName(self, board_id):
        if board_id == '655':
            return '정비인멤버 전용게시판'
        elif board_id == '334':
            return '노력멤버 전용게세판'

    def getArticleList(self, cafe_id, board_id, page):
        params = {
            'search.clubid' : cafe_id, # 카페 ID
            'search.menuid' : board_id, # 게시판 ID
            'search.boardtype' : 'L', # 보드타입 (반드시 필요로 하는 것은 아닌 것 같습니다.)
            'search.page' : page, # 불러올 페이지
            'userDisplay' : '50'
        }
        html = self.s.get(self.board_base_url, headers = self.headers, params = params)
        print(html.url)
        soup = BeautifulSoup(html.text, 'html.parser')
        board_name = self.getBoardName(board_id)
        values = []
        for tr in soup.select('tbody tr'):
            if len(tr.select('.inner_number')) > 0:
                values.append([ tr.select('.inner_number')[0].text.strip()
                              , tr.select('.article')[0].text.strip()
                              , board_name
                              , tr.select('.td_name a')[0].text.strip()
                              , tr.select('.td_date')[0].text.strip()
                              , 'https://cafe.naver.com/autowave21/'+tr.select('.inner_number')[0].text.strip() ])
        return pd.DataFrame(values, columns=['row_id', 'title_data', 'cat_data', 'user_data', 'create_date_data', 'link_data'])
    
    def getArticleHtml(self, cafe_id, board_id, article_id):
        params = {
            'clubid' : cafe_id, # 카페 ID
            'menuid' : board_id, # 게시판 ID
            'boardtype' : 'L', # 보드타입 (반드시 필요로 하는 것은 아닌 것 같습니다.)
            'articleid' : article_id  # 게시글 ID
        }        
        html = self.s.get(self.article_base_url, headers = self.headers, params = params)
        print(html.url)
        soup = BeautifulSoup(html.text, 'html.parser')
        board_name = self.getBoardName(board_id)
        download_path = self.base_path+board_name+'\\'+article_id
        content = soup.select('#tbody')[0].text.strip()
        real_html = soup.select('#tbody')[0].getText
        img_yn = 'n'
        i = 1
        for img in soup.select('#tbody')[0].select('img'):
            img_yn = 'y'
            self.makeDir(download_path)
            try:
                self.downloadImage(img.attrs['src'], download_path+'\\'+article_id+'_'+str(i)+'.jpg')
            except:
                pass
            i+=1
        return [article_id, content, img_yn, real_html]
    
    
    def getCommentHtml(self, cafe_id, board_id, article_id, page):
        params = {
            'search.clubid' : cafe_id, # 카페 ID
            'search.menuid' : board_id, # 게시판 ID
            'search.boardtype' : 'L', # 보드타입 (반드시 필요로 하는 것은 아닌 것 같습니다.)
            'search.articleid' : article_id, # 불러올 페이지
            'search.page' : page # 불러올 페이지
        }  
        html = self.s.get(self.comment_base_url, headers = self.headers, params = params)
        print(html.url)
        json_data  = html.json()
        return json_data
        
