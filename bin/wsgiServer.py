#encoding:utf-8
#!/usr/bin/python

import sys
import os
import time
import datetime
import logging
import logging.config
import threading
import shutil
import re
import json
import web
import random
from gevent import wsgi,pool,monkey; monkey.patch_all()
from pgmagick import Image,Blob,Geometry,FilterTypes
import ConfigParser


#定义全局变量
CUR_PATH = sys.path[0] + os.sep
CONFIG_FILE = CUR_PATH + "../conf/uploadServer.cfg"
LOG_CONFIG = CUR_PATH + "../conf/logger.cfg"

#获取日志
logging.config.fileConfig(LOG_CONFIG)
log = logging.getLogger('uploadServer')

#定义urls
urls = (
	'/','Index',
	'/PicUpload','PicUpload',
	'/VoiceUpload','VoiceUpload'
	)

#app = web.application(urls,globals())
web.config.debug = False

#定义配置文件
class Config(object):
	"""读取配置文件项"""
	def __init__(self):
		self.__parser = ConfigParser.ConfigParser()
		self.__configFile = CONFIG_FILE
		self.__info = "info"

	def __getValue(self,sec,key):
		if not sec or not key:
			log.error("无效配置参数。[sec]:%s,[key]:%s" % (sec,key))
			return False

		try:
			fp = open(self.__configFile)
			self.__parser.readfp(fp)
			value = self.__parser.get(sec,key)
			fp.close()
		except Exception, e:
			log.critical("读取配置意外,[Exception]: %s" % e)
			return False
		else:
			return value

	def get(self,key):
		return self.__getValue(self.__info,key)


#定义全局配置
config = Config()

#索引首页
class Index:
	"""class of Index"""
	def GET(self):
		web.header("Content-Type","text/html;charset=utf-8")
		return """<html><head></head><body>上传服务器！</body></html>"""


class PicUpload():
	'''POST接收上传图片请求'''
	def POST(self):
		client = web.ctx.environ['REMOTE_ADDR']
		x = web.input(_unicode=False)
		print x
		web.header("Content-Type","application/json;charset=utf-8")
		timestamp = time.strftime('%Y%m%d%H%M%S') + random.choice('abcdefghijklmnopqrstuvwxyz') 

		#处理图片
		try:
			upName = x['img.name']
			upPath = x['img.path']
			upMd5 = x['img.md5']
			upSize = x['img.size']
			upThumbnail = x['thumb']
			upContent_type = x['img.content_type']
			upUid = x ['uid']
		except Exception, e:
			log.error("无效form的传值。[input]: %s" % x )
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return '''{"img":"","thumb":"","status":"5"}'''

		#检查参数
		if not upUid or not upPath:
			log.error("无效上传内容，或缺少uid。[uid]:%s,[path]:%s" % (upUid,upPath))
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return '''{"img":"","thumb":"","status":"6"}'''

		#检查缩略图分辨率参数
		if not upThumbnail == '':
			try:
				getThumb = upThumbnail.split('x')
				getW = int(getThumb[0])
				getH = int(getThumb[1])
			except Exception, e:
				log.error("缩略图分辨率参数不正确。[thumb]:%s，原因：%s" % (upThumbnail,e))
				return '''{"img":"","thumb":"","status":"9"}'''
		

		#检查文件类型
		if upContent_type not in ["image/jpeg", "image/gif", "image/png"]:
			log.error("上传不是图片。[uid]:%s,[Content_type]:%s" % (upUid,upContent_type))
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return '''{"img":"","thumb":"","status":"7"}'''

		#获取扩展名
		ext = upName.split('.')[-1]
		imgFilename = "%s_%s_%s.%s" % (upUid,upMd5,timestamp,ext)
		img_dir = config.get('imgDir')
		thumbDir = config.get('thumbDir')
		newFilename = img_dir + '/' + imgFilename
		realAdd = 'http://' + config.get('openHost') + '/'

		if os.path.isfile(upPath):
			shutil.copyfile(upPath,newFilename)
			log.info("%s上传了图片文件%s." % (upUid,newFilename))
			os.remove(upPath)
			if not os.path.isfile(upPath):
				log.info("成功删除原图片文件%s." % upPath)

			
			realPath = newFilename.split('/')
			realAddImg = realAdd + realPath[-2] + '/' + realPath[-1]

			if os.path.isfile(newFilename):
				fp = open(newFilename,'r')
				orig_blob = Blob(fp.read())
				orig_args = self.__getAttributes(Image(orig_blob))

				print orig_args['width'],orig_args['high']

				if getW>orig_args['width'] or getH>orig_args['high']:
					log.error("[uid]:%s请求的缩略图大过于原图了。[origImg]:%sx%s,[requestImg]:%sx%s" % (upUid,getW,getH,orig_args['width'],orig_args['high']))
					#原图返回
					return '''{"img":"%s","thumb":"%s","status":"1"}''' % (realAddImg,realAddImg)
				else:
					thumb = Blob()
					im = Image(orig_blob)
					im.quality(100)
					im.filterType(FilterTypes.SincFilter)
					im.scale(upThumbnail)
					im.sharpen(1.0)
					thumbName = "%s_%s_%s_%s.%s" % (upUid,upMd5,timestamp,upThumbnail,ext)
					thumbFile = thumbDir  + '/' + thumbName
					im.write(thumbFile)
					log.info("%s [uid]:%s成功生成缩略图%s." % (client,upUid,thumbFile))
					realThumbPath = thumbFile.split('/')
					realAddThumb = realAdd + realThumbPath[-2] + '/' + realThumbPath[-1]

				fp.close()

			return """{"img":"%s","thumb":"%s","status":"1"}""" % (realAddImg,realAddThumb)
		else:
			log.error("%s写图片文件出错。[upPath]: %s ，原文件不存在。" % (upUid,upPath))
			return '''{"img":"","thumb":"","status":"8"}'''


	def __getAttributes(self,im):
		args = {}
		args["size"] = "%dx%d" % (im.columns(), im.rows())
		args["width"] = int(im.columns())
		args["high"] = int(im.rows())
		args["content_type"] = "image/" + im.magick().lower()
		return args		

class VoiceUpload:
	"""POST接收上传音频请求"""
	def POST(self):
		client = web.ctx.environ['REMOTE_ADDR']
		timestamp = time.strftime('%Y%m%d%H%M%S') + random.choice('abcdefghijklmnopqrstuvwxyz') 

		x = web.input(_unicode=False)
		print x
		web.header("Content-Type","application/json;charset=utf-8")

		#处理音频
		try:
			upName = x['Voice.name']
			upPath = x['Voice.path']
			upMd5 = x['Voice.md5']
			upSize = x['Voice.size']
			upContent_type = x['Voice.content_type']
			upUid = x ['uid']
		except Exception, e:
			log.error("无效form的传值。[input]: %s , 原因是：%s " % (x,e))
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return """{"Voice":"","status":"5"}"""


		#检查参数
		if not upUid or not upPath:
			log.error("无效上传内容，或缺少uid。[uid]:%s,[path]:%s" % (upUid,upPath))
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return """{"Voice":"","status":"6"}"""


		#检查文件类型
		if upContent_type not in ["application/octet-stream","audio/amr"]:
			log.error("上传不是音频文件。[uid]:%s,[Content_type]:%s" % (upUid,upContent_type))
			#start_response('400 Bad Request.',[('Content-Type','application/json;charset=utf-8')])
			return """{"Voice":"","status":"7"}"""

		#获取扩展名
		ext = upName.split('.')[-1]
		voiceFilename = "%s_%s_%s.%s" % (upUid,upMd5,timestamp,ext)
		voice_dir = config.get('voiceDir')
		newFilename = voice_dir + '/' + voiceFilename

		if os.path.isfile(upPath):
			shutil.copyfile(upPath,newFilename)
			log.info("%s上传了音频文件%s." % (upUid,newFilename))
			os.remove(upPath)
			if not os.path.isfile(upPath):
				log.info("成功删除原文件%s." % upPath)
			realAdd = 'http://' + config.get('openHost') + '/'
			realPath = newFilename.split('/')
			return """{"Voice":"%s","status":"1"}""" % (realAdd + realPath[-2] + '/' + realPath[-1])
		else:
			log.error("%s写音频文件出错。[fp]: %s ，原文件不存在。" % (upUid,upPath))
			return """{"Voice":"","status":"8"}"""




def runServer():
	host = config.get('host')
	port = int(config.get('port'))
	poolSize = int(config.get('poolSize'))
	p = pool.Pool(poolSize)
	log.info("Start server on %s:%s with pool szie %s" % (host,port,poolSize))
	application = web.application(urls,globals()).wsgifunc()
	wsgi.WSGIServer((host,port),application,spawn = p).serve_forever()

if  __name__ == '__main__':
	runServer()
