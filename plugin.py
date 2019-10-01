# -*- coding: utf-8 -*-
#########################################################
# 고정영역
#########################################################
# python
import os
import sys
import traceback
import json

# third-party
from flask import Blueprint, request, Response, render_template, redirect, jsonify, url_for, send_from_directory
from flask_login import login_required
from flask_socketio import SocketIO, emit, send

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, socketio, path_app_root
from framework.util import Util, AlchemyEncoder
from system.logic import SystemLogic
            
# 패키지
from logic import Logic
from model import ModelSetting

package_name = __name__.split('.')[0].split('_sjva')[0]
logger = get_logger(package_name)

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'kthoom'), static_url_path='kthoom')

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()

plugin_info = {
    'version' : '0.1.0.3',
    'name' : 'Manamoa 다운로더',
    'category_name' : 'service',
    'icon' : '',
    'developer' : 'noname',
    'description' : '마나모아 다운로드',
    'home' : '',
    'more' : '',
}
#########################################################

# 메뉴 구성.
menu = {
    'main' : [package_name, 'Manamoa 다운로더'],
    'sub' : [
        ['setting', '설정'], ['status', '상태 & 작품별 다운로드'], ['viewer', '뷰어'], ['log', '로그']
    ], 
    'category' : 'service',
}  

#########################################################
# WEB Menu
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)
    #return blueprint.send_static_file('index.html')

@blueprint.route('/<sub>')
@login_required
def detail(sub): 
    if sub == 'setting':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        arg['scheduler'] = str(scheduler.is_include(package_name))
        arg['is_running'] = str(scheduler.is_running(package_name))
        return render_template('%s_%s.html' % (package_name, sub), arg=arg)
    elif sub == 'status':
        arg = {}
        arg['is_running'] = str(scheduler.is_running(package_name))
        return render_template('%s_%s.html' % (package_name, sub), arg=arg)
    elif sub == 'command_list':
        arg = {}
        arg['list_type'] = "command_list"
        return render_template('%s_list.html' % (package_name), arg=arg)
    elif sub == 'kthoom':
        return blueprint.send_static_file('index.html')
    elif sub == 'viewer':
        site = "/manamoa/kthoom?bookUri=dp"
        return render_template('iframe.html', site=site)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI (보통 웹에서 요청하는 정보에 대한 결과를 리턴한다.)
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    if sub == 'setting_save':
        try:
            ret = Logic.setting_save(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'scheduler':
        try:
            go = request.form['scheduler']
            logger.debug('scheduler :%s', go)
            if go == 'true':
                Logic.scheduler_start()
            else:
                Logic.scheduler_stop()
            return jsonify(go)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    elif sub == 'one_execute':
        try:
            ret = Logic.one_execute()
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    # kthoom 에서 호출
    elif sub == 'zip_list':
        try:
            ret = Logic.get_zip_list()
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify('fail')   
    elif sub == 'stop':
        try:
            ret = Logic.stop()
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'reset_db':
        try:
            ret = Logic.reset_db()
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'download_by_manga_id':
        try:
            ret = Logic.download_by_manga_id(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
#########################################################
# API
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
def api(sub):
    logger.debug('api %s %s', package_name, sub)
    
#########################################################
# kthroom
#########################################################
@blueprint.route('/code/<path:path>', methods=['GET', 'POST'])
def kthroom(path):
    return blueprint.send_static_file('code/' + path)

@blueprint.route('/images/<path:path>', methods=['GET', 'POST'])
def kthroom_images(path):
    return blueprint.send_static_file('images/' + path)

@blueprint.route('/examples/<path:path>', methods=['GET', 'POST'])
def kthroom_examples(path):
    return blueprint.send_static_file('examples/' + path)

@blueprint.route('/dp/<path:path>', methods=['GET', 'POST'])
def kthroom_dp(path):
    tmp = path.split('/')
    real_path = os.path.join(Logic.get_setting_value('dfolder'), tmp[0], tmp[1])
    real_path = real_path.replace(path_app_root, '')[1:].replace('\\', '/')
    logger.debug('load:%s', real_path)
    return send_from_directory('', real_path)

#########################################################
# socketio
#########################################################
sid_list = []
@socketio.on('connect', namespace='/%s' % package_name)
def connect():
    try:
        logger.debug('socket_connect')
        sid_list.append(request.sid)
        running = "실행중" if Logic.is_running() else "실행중이 아닙니다."
        tmp = {'is_running':running, 'data':Logic.current_list}
        
        #if Logic.current_data is not None:
        #data = [_.__dict__ for _ in Logic.current_list]
        #dict_ = {'data':Logic.current_list, 'status':status}
        tmp = json.dumps(tmp, cls=AlchemyEncoder)
        tmp = json.loads(tmp)
        emit('on_connect', tmp, namespace='/%s' % package_name)
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())


@socketio.on('disconnect', namespace='/%s' % package_name)
def disconnect():
    try:
        sid_list.remove(request.sid)
        logger.debug('socket_disconnect')
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())

def socketio_callback(cmd, data):
    if sid_list:
        running = "실행중" if Logic.is_running() else "실행중이 아닙니다."
        tmp = {'is_running':running, 'data':data}
        tmp = json.dumps(tmp, cls=AlchemyEncoder)
        tmp = json.loads(tmp)
        socketio.emit(cmd, tmp, namespace='/%s' % package_name, broadcast=True)

