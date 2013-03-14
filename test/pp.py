class PicProcess(object):
	def __init__(self):
		self.thumbnail_size = filter(None,config.get('thumbnail_size').split(','))
		self.orig_dir = config.get('imgDir')
		self.thumb_dir = config.get('thumbDir')

	def __getAttributes(self,im):
		if not im:
			log.error("无效参数。[im]: %s" % im)
			return False
		args = {}
		args["size"] = "%dx%d" % (im.columns(), im.rows())
		args["content_type"] = "image/" + im.magick().lower()
		return args

	# 保存原始图片与缩略图
	# 返回文件名
	def PP(self,fp,uid,filename,filemd5):
		
		result = {}
		#生成时间
		timestamp = time.strftime('%Y%m%d%H%M%S') 

		#另存原始图像
		op = open(fp)
		orig_blob = Blob(op.read())
		orig_args = self.__getAttributes(Image(orig_blob))
		ext = filename.split('.')[-1]
		orig_args["filename"] = "%s_%s_%s.%s" % (uid,filemd5,timestamp,ext)
		orig_args["newFilename"] = self.orig_dir + '/' + orig_args["filename"]

		if not os.path.isdir(self.orig_dir):
			log.error("%s写入大图文件出错。[orig_dir]: %s ，目标目录不存在。" % (uid,self.orig_dir))
			return False
		if os.path.isfile(fp):
			shutil.copyfile(fp,orig_args["newFilename"])
			log.info("%s上传了图片%s." % (uid,orig_args["newFilename"]))
			result['BigImage'] = orig_args["newFilename"]
		else:
			log.error("%s写入大图文件出错。[fp]: %s ，原文件不存在。" % (uid,fp))
			return False


		
		#另存缩略图
		for size in self.thumbnail_size:
			thumb = Blob()
			im = Image(orig_blob)
			im.quality(100)
			im.filterType(FilterTypes.SincFilter)
			im.scale(size)
			im.sharpen(1.0)
			#TODO 调整大小，太小的图时，会报错
			args = self.__getAttributes(im)
			args["uid"] = uid
			args["filename"] = "%s_%s_%s_%s.%s" % (uid,filemd5,timestamp,size,ext)
			args["newFilename"] = self.thumb_dir + '/' + args["filename"]
			im.write(args["newFilename"])
			result[size] = args["newFilename"]
			log.info("%s上传了图片成功生成缩略图%s." % (uid,args["newFilename"]))


		op.close()
		os.remove(fp)
		if not os.path.isfile(fp):
			log.info("成功删除原图%s." % fp)

		return result

