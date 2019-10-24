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
from PIL import Image
from math import sin, cos, tan, floor


class Decoder(object):
    def __init__(self, seed, id):
        self.view_cnt = seed
        self.__seed = seed/10
        self.id = id
        self.cx=5
        self.cy=5

        if self.__seed>30000:
            self.cx = 1
            self.cy = 6
        elif self.__seed>20000:
            self.cx = 1
        elif self.__seed>10000:
            self.cy = 1

        self.order = []
        for i in range(self.cx*self.cy):
            #print i
            tmp = []
            tmp.append(i)
            if self.id < 554714:
                tmp.append(self._random(i))
            else:
                tmp.append(self.newRandom(i))
            self.order.append(tmp)

        self.order.sort(key=lambda x:x[1])


    def decode(self, input):
        if self.view_cnt==0:
            return input
        output = Image.new("RGBA", (input.width, input.height))
        row_w = input.width / self.cx
        row_h = input.height / self.cy
        #logger.debug('input.width : %s', input.width)
        #logger.debug('input.height : %s', input.height)
        #logger.debug('row_w : %s', row_w)
        #logger.debug('row_h : %s', row_h)
        for i in range(self.cx*self.cy):
            o = self.order[i]
            ox = i % self.cx
            oy = i / self.cx
            tx = o[0] % self.cx
            ty = o[0] / self.cx
            ox * row_w, oy * row_h
            tmp = input.crop( (ox * row_w, oy * row_h, ox * row_w+row_w, oy * row_h+row_h ))
            output.paste(tmp, (tx * row_w, ty * row_h) )
        output = output.convert("RGB")
        return output

   
    def _random(self, index):
        x = sin(self.__seed+index) * 10000
        return int(floor((x - floor(x)) * 100000))
    
    def newRandom(self, index):
        index += 1
        t = 100 * sin(10 * (self.__seed+index))
        n = 1000 * cos(13 * (self.__seed+index))
        a = 10000 * tan(14 * (self.__seed+index))
        t = floor(100 * (t - floor(t)))
        n = floor(1000 * (n - floor(n)))
        a = floor(10000 * (a - floor(a)))
        return int((t + n + a))
    





if __name__ == "__main__":
    try:
        #https://manamoa15.net/bbs/board.php?bo_table=manga&wr_id=694872
        #var view_cnt = 397340;
        
        print os.path.dirname(__file__)
        test_dir =os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test')
        tmp = os.listdir(test_dir)
        decoder = Decoder(397340, 694872)
        for idx, t in enumerate(tmp):
            im = Image.open(os.path.join(test_dir, t))
            print im.width
            output = decoder.decode(im)
            output.save('%s.jpg' % idx)
            #break
        
    except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())

