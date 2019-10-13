# -*- coding: utf-8 -*-
import os
import sys
if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
    python = 'python'
else:
    python = 'python3'

logger = None
try:
    # SJVA
    from framework.logger import get_logger
    package_name = __name__.split('.')[0].split('_sjva')[0]
    logger = get_logger(package_name)
except:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("error.log")
    streamHandler = logging.StreamHandler()
    logger.addHandler(file_handler)
    logger.addHandler(streamHandler)

import traceback
import json
import re
from datetime import datetime
import shutil
import zipfile

try:
    import requests
    from bs4 import BeautifulSoup
    from sqlitedict import SqliteDict
    import cfscrape
    from discord_webhook import DiscordWebhook
    from google_drive_downloader import GoogleDriveDownloader as gdd
    from PIL import Image

except:
    requirements = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if os.system('%s -m pip install -r %s' % (python, requirements)) != 0:
        os.system('wget https://bootstrap.pypa.io/get-pip.py')
        os.system('%s get-pip.py' % python)
        os.system('%s -m pip install -r %s' % (python, requirements))
import requests
from bs4 import BeautifulSoup
from sqlitedict import SqliteDict
import cfscrape
from discord_webhook import DiscordWebhook
from google_drive_downloader import GoogleDriveDownloader as gdd
from PIL import Image
#############################################################################################


class LogicMD(object):
    nowdata = None
    filedata = {}
    json_data = {}
    scraper = None
    listener = None
    is_running = False
    stop_flag = False
    current_manga_id = None

    @staticmethod
    def init(data, listener=None):
        now = datetime.now()
        LogicMD.nowdata = u'{}월/{}일/{}:{}'.format(str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2))
        LogicMD.filedata = SqliteDict(os.path.join(os.path.dirname(__file__), 'newcheck.db'), tablename='cache', encode=json.dumps, decode=json.loads, autocommit=True)
        LogicMD.json_data = data
        if LogicMD.json_data['cloudflare_bypass'] == 'True':
            LogicMD.scraper = cfscrape.create_scraper()
        logger.debug(u'=========================================')
        logger.debug(u'sitecheck : {}\nall_download : {}\nzip : {}\ncloudflare_bypass : {}\nproxy : {}\nproxy_url : {}\ndownlist : {}'.format(LogicMD.json_data['sitecheck'],LogicMD.json_data['all_download'],LogicMD.json_data['zip'],LogicMD.json_data['cloudflare_bypass'],LogicMD.json_data['proxy'],LogicMD.json_data['proxy_url'],LogicMD.json_data['downlist']))
        logger.debug(u'=========================================')
        if listener is not None:
            from framework.event import MyEvent
            if LogicMD.listener is None:
                LogicMD.listener = MyEvent()
                LogicMD.listener += listener


    @staticmethod
    def titlereplace(title):
        return re.sub('[\\/:*?\"<>|]', '', title).strip()


    @staticmethod
    def senddiscord(sendcontent):
        try:
            if LogicMD.json_data['discord_webhook'] == 'True':
                Discord_Webhook_Url = LogicMD.json_data['discord_webhook_url']
                webhook = DiscordWebhook(url=Discord_Webhook_Url, content=sendcontent)
                webhook.execute()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def manadownload(url, image_filepath, decoder):
        try:
            headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
            image_data = requests.get(url,headers=headers,stream=True)
            if decoder is None:
                with open(image_filepath, 'wb') as handler:
                    handler.write(image_data.content)
            else:
                from PIL import Image
                im = Image.open(image_data.raw)
                output = decoder.decode(im)
                output.save(image_filepath)
            return image_data.status_code
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    # 압축할 폴더 경로를 인자로 받음. 폴더명.zip 생성
    @staticmethod
    def makezip(zip_path):
        try:
            if os.path.isdir(zip_path):
                zipfilename = os.path.join(os.path.dirname(zip_path), '%s.zip' % os.path.basename(zip_path))
                fantasy_zip = zipfile.ZipFile(zipfilename, 'w')
                for f in os.listdir(zip_path):
                    if f.endswith('.jpg'):
                        src = os.path.join(zip_path, f)
                        fantasy_zip.write(src, os.path.basename(src), compress_type = zipfile.ZIP_DEFLATED)
                fantasy_zip.close()
            shutil.rmtree(zip_path)
            LogicMD.senddiscord(u'{}  압축 완료'.format(os.path.basename(zip_path)))
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    # 다운여부 판단
    @staticmethod
    def is_exist_download_list(title):
        try:
            title = LogicMD.titlereplace(title).replace(' ', '')
            flag = False
            if len(LogicMD.json_data['downlist']) == 1:
                if LogicMD.json_data['downlist'][0] == '':
                    flag = True
                    return flag
            if len(LogicMD.json_data['downlist']) != 0:
                for downcheck in LogicMD.json_data['downlist']:
                    downcheck = downcheck.strip()
                    if downcheck == '':
                        pass
                    else:
                        if title.find(LogicMD.titlereplace(downcheck).replace(' ', '')) != -1:
                            flag = True
                            break
            else:
                flag = True
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return flag

    @staticmethod
    def pageparser(URL):
        try:
            from system import LogicSelenium
            return LogicSelenium.get_pagesoruce_by_selenium(URL, '//footer[@class="at-footer"]')
            headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
            if LogicMD.json_data['proxy'] == 'False' and LogicMD.json_data['cloudflare_bypass'] == 'False':
                page_source = requests.get(URL,headers=headers).text
            elif LogicMD.json_data['proxy'] == 'True' and LogicMD.json_data['cloudflare_bypass'] == 'False':
                page_source = requests.get(URL,headers=headers,proxies={"https": LogicMD.json_data['proxy_url']}).text
            elif LogicMD.json_data['proxy'] == 'False' and LogicMD.json_data['cloudflare_bypass'] == 'True':
                page_source = LogicMD.scraper.get(URL,headers=headers).text
            elif LogicMD.json_data['proxy'] == 'True' and LogicMD.json_data['cloudflare_bypass'] == 'True':
                page_source = LogicMD.scraper.get(URL,headers=headers,proxies={"https": LogicMD.json_data['proxy_url'] }).text
        except Exception as e:
            x = e.args
            for erro in x:
                if str(type(erro)) == "<class 'urllib3.exceptions.ProtocolError'>":
                    logger.error(u'======================[{}]================'.format(LogicMD.nowdata))
                    logger.error(e)
                    LogicMD.senddiscord(u'{}가 차단됐습니다.'.format(LogicMD.json_data['sitecheck']))
                elif str(type(erro)) == "<class 'urllib3.exceptions.MaxRetryError'>":
                    logger.error(u'======================[{}]================'.format(LogicMD.nowdata))
                    logger.error(e)
                    LogicMD.senddiscord(u'{} 재접속 시도 횟수 초과. 다음에 다시 시도해주세요.'.format(LogicMD.json_data['sitecheck']))
                else:
                    logger.error(u'======================[{}]================'.format(LogicMD.nowdata))
                    logger.error(e)
                    LogicMD.senddiscord(u'예상치 못한 접속 불가 오류')
            return
        return page_source


    # 에피소드 한편을 다운로드 한다.  wr_id= 포함된 url, 저장경로
    @staticmethod
    def episode_download(url, download_path):
        try:
            title = os.path.basename(download_path)
            LogicMD.senddiscord(u'{} 다운로드 시작'.format(title))
            event = {'type':'episode', 'status':'ready', 'title':title, 'url':url, 'epi_count':0, 'epi_current':0}
            LogicMD.send_to_listener(**event)
            page_source2 = LogicMD.pageparser(url)
            if page_source2 is None:
                logger.error('Source is None')
                event['status'] = 'episode_read_fail'
                LogicMD.send_to_listener(**event)
                return
            page_count = page_source2.find('var img_list = [')
            page_count2 = page_source2.find(']', page_count)
            mangajpglist = page_source2[page_count+16:page_count2].replace('\\','').replace('"','').split(',')
            page_count22 = page_source2.find('var img_list1 = [')
            page_count222 = page_source2.find(']', page_count22)
            mangajpglist2 = page_source2[page_count22+16:page_count222].replace('\\','').replace('"','').split(',')
            
            tmp1 = page_source2.find('var view_cnt =')
            tmp1 = page_source2.find('=', tmp1) + 1
            tmp2 = page_source2.find(';', tmp1)
            view_cnt = int(page_source2[tmp1:tmp2].strip())
            wr_id = int(url.split('wr_id=')[1].split('&')[0])
            logger.debug('view_cnt :%s, wr_id:%s', view_cnt, wr_id)
            if view_cnt == 0:
                decoder = None
            else:
                from .decoder import Decoder
                decoder = Decoder(view_cnt, wr_id)
            

            event['status'] = 'downloading'
            event['epi_count'] = len(mangajpglist)
            LogicMD.send_to_listener(**event)
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            tmp = os.path.join(download_path, str(1).zfill(5)+'.jpg')
            filesize = requests.get(mangajpglist[0]).status_code
            if filesize == 200:
                for idx, tt in enumerate(mangajpglist):
                    image_filepath = os.path.join(download_path, str(idx+1).zfill(5)+'.jpg')
                    LogicMD.manadownload(tt, image_filepath, decoder)
                    event['epi_current'] = idx
                    LogicMD.send_to_listener(**event)
            else:
                if mangajpglist[0].find('img.') != -1:
                    for idx, tt in enumerate(mangajpglist):
                        image_filepath = os.path.join(download_path, str(idx+1).zfill(5)+'.jpg')
                        downresult = LogicMD.manadownload(tt.replace('img.','s3.'), image_filepath, decoder)
                        if downresult != 200 and mangajpglist2[0].find('google') != -1:
                            for idx, tt in enumerate(mangajpglist2):
                                image_filepath = os.path.join(download_path, str(idx+1).zfill(5)+'.jpg')
                                gdd.download_file_from_google_drive(file_id=tt.replace('https://drive.google.com/uc?export=view&id=',''), dest_path=image_filepath)
                                event['epi_current'] = idx
                                LogicMD.send_to_listener(**event)
                            break
                        event['epi_current'] = idx
                        LogicMD.send_to_listener(**event)
                else:
                    for idx, tt in enumerate(mangajpglist):
                        image_filepath = os.path.join(download_path, str(idx+1).zfill(5)+'.jpg')
                        downresult = LogicMD.manadownload(tt.replace('s3.','img.'), image_filepath, decoder)
                        if downresult != 200 and mangajpglist2[0].find('google') != -1:
                            for idx, tt in enumerate(mangajpglist2):
                                image_filepath = os.path.join(download_path, str(idx+1).zfill(5)+'.jpg')
                                gdd.download_file_from_google_drive(file_id=tt.replace('https://drive.google.com/uc?export=view&id=',''), dest_path=image_filepath)
                                event['epi_current'] = idx
                                LogicMD.send_to_listener(**event)
                            break
                        event['epi_current'] = idx
                        LogicMD.send_to_listener(**event)
            LogicMD.senddiscord(u'{} 다운로드 완료'.format(title))
            event['status'] = 'downloaded'
            LogicMD.send_to_listener(**event)
            if LogicMD.json_data['zip'] == 'True':
                LogicMD.makezip(download_path)
                event['status'] = 'zip'
                LogicMD.send_to_listener(**event)
            LogicMD.filedata[url] = title
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def all_episode_download(url, check_download_list=True):
        try:
            event = {'type':'all_download'}
            event['list'] = []
            page_source = LogicMD.pageparser(url)
            soup = BeautifulSoup(page_source, 'html.parser')
            maintitle = LogicMD.titlereplace(soup.find('div', class_='red title').text)
            if LogicMD.is_exist_download_list(maintitle) or not check_download_list:
                logger.debug(u'타이틀 : {}'.format(maintitle))
                for idx, t in enumerate(list(reversed(soup.find_all('div', class_='slot')))):
                    title = t.find('div', class_='title').text.strip().split('\n')[0].strip()
                    title = re.sub(r'\s{2,}', ' ', title).strip()
                    title = LogicMD.titlereplace(title)
                    episode_url = LogicMD.json_data['sitecheck'] + t.find('a')['href']
                    event['list'].append({'idx':idx, 'title':title, 'url':episode_url, 'exist_download':LogicMD.is_exist_download_list(title), 'exist_filedata':episode_url in LogicMD.filedata, 'percent':0, 'epi_count':0, 'epi_current':0})
                LogicMD.send_to_listener(**event)
                for item in event['list']:
                    if LogicMD.stop_flag:
                        break
                    if not item['exist_filedata']:
                        LogicMD.episode_download(item['url'], os.path.join(LogicMD.json_data['dfolder'], maintitle, item['title']))
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def start():
        try:
            LogicMD.is_running = True
            LogicMD.stop_flag = False
            if LogicMD.current_manga_id is not None:
                if LogicMD.current_manga_id.find('wr') == -1:
                    url = LogicMD.json_data['sitecheck'] + '/bbs/page.php?hid=manga_detail&manga_id=' + LogicMD.current_manga_id
                    LogicMD.all_episode_download(url, check_download_list=False)
                else:
                    url = LogicMD.json_data['sitecheck'] + '/bbs/board.php?bo_table=manga&wr_id=' + LogicMD.current_manga_id.replace('wr','')
                    page_source = LogicMD.pageparser(url)
                    soup = BeautifulSoup(page_source, 'html.parser')
                    mangaid = soup.find('a','btn btn-color btn-sm')['href'].replace('/bbs/page.php?hid=manga_detail&manga_id=','')
                    mangascore = soup.find('span','count').text.replace('인기 : ','')
                    title = soup.title.text
                    title = LogicMD.titlereplace(title)
                    match = re.compile(ur'(?P<main>.*?)((단행본.*?)?|특별편)?(\s(?P<sub>(\d|\-|\.)*?(화|권)))?(\s\(완결\))?\s?$').match(title)
                    if match:
                        maintitle = match.group('main').strip()
                    else:
                        maintitle = title
                        logger.debug('not match')
                    maintitle = LogicMD.titlereplace(maintitle)
                    event = {'type':'recent_episode'}
                    event['list'] = []
                    event['list'].append({'idx':0, 'title':title, 'url':url, 'exist_download':LogicMD.is_exist_download_list(title), 'exist_filedata':url+'pass' in LogicMD.filedata, 'main':maintitle, 'manga_id':mangaid, 'score':mangascore, 'percent':0, 'epi_count':0, 'epi_current':0})
                    LogicMD.send_to_listener(**event)
                    LogicMD.episode_download(url, os.path.join(LogicMD.json_data['dfolder'], maintitle, title))

            else:
                if LogicMD.json_data['all_download'] == 'True':
                    for pagecheck in range(int(LogicMD.json_data['pagecount'])):
                        URL = '{}{}'.format(LogicMD.json_data['sitecheck'], '/bbs/board.php?bo_table=manga&page=' + str(pagecheck+1))
                        page_source = LogicMD.pageparser(URL)
                        soup = BeautifulSoup(page_source, 'html.parser')
                        for t in soup.find_all('div', 'pull-right post-info'):
                            url = '{}{}'.format(LogicMD.json_data['sitecheck'], t.find('a')['href'])
                            LogicMD.all_episode_download(url)
                            if LogicMD.stop_flag:
                                break
                else:
                    event = {'type':'recent_episode'}
                    event['list'] = []
                    for pagecheck in range(int(LogicMD.json_data['pagecount'])):
                        URL = '{}{}'.format(LogicMD.json_data['sitecheck'], '/bbs/board.php?bo_table=manga&page=' + str(pagecheck+1))
                        page_source = LogicMD.pageparser(URL)
                        soup = BeautifulSoup(page_source, 'html.parser')
                        for idx, t in enumerate(soup.find_all('div', class_='post-row')):
                            idx = pagecheck*80 + idx
                            item = LogicMD.get_info(t)
                            URL = '{}{}'.format(LogicMD.json_data['sitecheck'], t.find('a')['href'])
                            event['list'].append({'idx':idx, 'title':item['title'], 'url':item['url'], 'exist_download':LogicMD.is_exist_download_list(item['title']), 'exist_filedata':item['url'] in LogicMD.filedata, 'main':item['main'], 'manga_id':item['manga_id'], 'score':item['score'], 'percent':0, 'epi_count':0, 'epi_current':0})
                    LogicMD.send_to_listener(**event)
                    for item in event['list']:
                        if LogicMD.stop_flag:
                            break
                        if item['exist_download']:
                            if not item['exist_filedata']:
                                LogicMD.episode_download(item['url'], os.path.join(LogicMD.json_data['dfolder'], item['main'], item['title']))
            LogicMD.is_running = False
            event = {'type':'completed'}
            LogicMD.send_to_listener(**event)
            LogicMD.current_manga_id = None
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())



    @staticmethod
    def get_info(tag):
        try:
            item = {}
            a_tags = tag.find_all('a')
            item['manga_id'] = a_tags[1]['href'].split('manga_id=')[1]
            item['url'] = LogicMD.json_data['sitecheck'] + a_tags[2]['href']
            item['title'] = a_tags[2].text.replace(' NEW ','').strip()
            item['title'] = LogicMD.titlereplace(item['title'])
            #item['main'] = item['title'].replace(item['title'].split(' ')[-1],'').strip()
            match = re.compile(ur'(?P<main>.*?)((단행본.*?)?|특별편)?(\s(?P<sub>(\d|\-|\.)*?(화|권)))?(\s\(완결\))?\s?$').match(item['title'])
            if match:
                item['main'] = match.group('main').strip()
            else:
                item['main'] = item['title']
                logger.debug('not match')
            p_tags = tag.find_all('p')
            tmp = p_tags[1].text
            item['score'] = int(tmp.split(' ')[1])
            return item
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    # for sjva
    @staticmethod
    def send_to_listener(**kwargs):
        try:
            if LogicMD.listener is not None:
                args = []
                LogicMD.listener.fire(*args, **kwargs)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())



if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser(description = u'ManamoaDownloader')
        parser.add_argument('--manga_id', required=False, help=u"해당하는 작품의 전체 에피소드를 다운로드 합니다.", default=None)
        args = parser.parse_args()
        djson = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ManamoaDownloader.json')
        with open(djson) as json_file:
            json_data = json.load(json_file)
        json_data['dfolder'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MangaDownload')
        LogicMD.init(json_data)
        LogicMD.current_manga_id = args.manga_id
        LogicMD.start()
    except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
        logger.error(u'======================[{}]================'.format(LogicMD.nowdata))
        LogicMD.senddiscord(e)
