# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import threading
# third-party

# sjva 공용
from framework import db, scheduler, path_data
from framework.job import Job
from framework.util import Util
from framework.logger import get_logger

# 패키지
import system
from .model import ModelSetting

package_name = __name__.split('.')[0].split('_sjva')[0]
logger = get_logger(package_name)
#########################################################
import requests
import urllib
import time
import threading
from datetime import datetime

class Logic(object):
    db_default = {
        'auto_start' : 'False',
        'interval' : '30',
        'web_page_size' : '30',

        "sitecheck" : "https://manamoa15.net",
        "all_download" : "False",
        "zip" : "True",
        "cloudflare_bypass" : "True",
        "proxy" : "False",
        "proxy_url" : "",
        "downlist" : "",
        "discord_webhook" : "False",
        "discord_webhook_url" : "", 
        'dfolder' : os.path.join(path_data, 'MangaDownload'),
        "pagecount" : "1"
    }


    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_load():
        try:
            logger.debug('%s plugin_load', package_name)
            # DB 초기화 
            Logic.db_init()

            # 필요 패키지 설치
            try:
                from bs4 import BeautifulSoup
                import cfscrape
                from discord_webhook import DiscordWebhook
            except:
                try:
                    os.system('pip install -r %s' % os.path.join(os.path.dirname(__file__), 'requirements.txt'))
                except:
                    logger.error('pip install error!!')
                    pass
            
            # 다운로드 폴더 생성
            download_path = Logic.get_setting_value('download_path')
            if not os.path.exists(download_path):
                try:
                    os.mkdir(download_path)
                except:
                    logger.error('donwload_path make error!!')
            # 편의를 위해 json 파일 생성
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

            # 자동시작 옵션이 있으면 보통 여기서 
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_unload():
        try:
            logger.debug('%s plugin_unload', package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_start():
        try:
            logger.debug('%s scheduler_start', package_name)
            interval = Logic.get_setting_value('interval')
            job = Job(package_name, package_name, interval, Logic.scheduler_function, u"마나모아 다운로더", False)
            scheduler.add_job_instance(job)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_stop():
        try:
            logger.debug('%s scheduler_stop', package_name)
            scheduler.remove_job(package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def get_setting_value(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_function():
        try:
            from ManamoaDownloader import LogicMD
            setting_list = db.session.query(ModelSetting).all()
            arg = Util.db_list_to_dict(setting_list)
            arg['downlist'] = arg['downlist'].split('|')
            LogicMD.init(arg, Logic.listener)
            LogicMD.start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def one_execute():
        try:
            if scheduler.is_include(package_name):
                if scheduler.is_running(package_name):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(package_name)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function()
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret
    
    @staticmethod
    def reset_db():
        try:
            from ManamoaDownloader import LogicMD
            LogicMD.filedata.clear()
            return 'success'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret

    # 기본 구조 End
    ##################################################################

    @staticmethod
    def download_by_manga_id(req):
        try:
            from ManamoaDownloader import LogicMD
            logger.debug(req.form)
            LogicMD.current_manga_id = req.form['manga_id']
            return Logic.one_execute()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_zip_list():
        try:
            ret = []
            download_path = Logic.get_setting_value('dfolder')
            tmp = os.listdir(download_path)
            for t in tmp:
                title_path = os.path.join(download_path, t)
                if os.path.isdir(title_path):
                    zip_list = os.listdir(title_path)
                    for z in zip_list:
                        zip_path = os.path.join(title_path, z)
                        if os.path.isfile(zip_path) and zip_path.endswith('.zip'):
                            ret.append('dp/%s/%s' % (t, z))
            #return '|'.join(ret)
            return ret

        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        
    
    current_list = None
    current_epi = None
    @staticmethod
    def listener(*args, **kwargs):
        logger.debug(args)
        import plugin
        logger.debug(kwargs)
        if kwargs['type'] in ['recent_episode', 'all_download']:
            Logic.current_list = kwargs
            plugin.socketio_callback('on_connect', kwargs)
        elif kwargs['type'] == 'completed':
            plugin.socketio_callback('running_status', kwargs)
        elif kwargs['type'] == 'episode':
            if kwargs['status'] == 'ready':
                Logic.current_epi = None
                for entity in Logic.current_list['list']:
                    #logger.debug(entity['url'])
                    if entity['url'] == kwargs['url']:
                        Logic.current_epi = entity
                        break
            elif kwargs['status'] in ['episode_read_fail', 'downloaded']:
                Logic.current_epi['status'] = kwargs['status']
            elif kwargs['status'] == 'downloading':
                Logic.current_epi['epi_count'] = kwargs['epi_count']
                
                Logic.current_epi['epi_current'] = kwargs['epi_current']
                logger.debug('AAA %s %s', kwargs['epi_current'], Logic.current_epi['epi_current'])
                Logic.current_epi['percent'] = (kwargs['epi_current']*100/(kwargs['epi_count']-1))
            logger.debug('== %s', Logic.current_epi)
            plugin.socketio_callback('status', Logic.current_epi)
        try:
            pass
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def is_running():
        from ManamoaDownloader import LogicMD
        return LogicMD.is_running

    @staticmethod
    def stop():
        from ManamoaDownloader import LogicMD
        LogicMD.stop_flag = True
        return 'ok'

    