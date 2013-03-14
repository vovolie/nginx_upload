#coding=utf-8
#!/usr/bin/python
#Author:zhonglie
#Email:13558871@qq.com

import os
import atexit
import time
from wsgiServer import *
from signal import SIGTERM

class Daemon():
	"""服务器守护进程。"""

	def __init__(self, pidfile,stdin="/dev/null",stdout="/dev/null",\
			stderr="/dev/null"):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile

	def _daemonize(self):

        #脱离父进程
		try:
			pid = os.fork()
			if pid >0:
				sys.exit(0)
		except OSError, e:
			sys.stderr.write("fork #1 failed.%d (%s)\n" % (e.errno,\
					e.strerr))
			sys.exit(1)

		#脱离终端
		os.setsid()
		#修改当前工作目录 
		os.chdir('/')
		#重设文件创建权限
		os.umask(0)

		#第二次fork，禁止进程重新打开控制终端
		try:
			pid = os.fork()
			if pid >0:
				sys.exit()
		except OSError, e:
			sys.stderr.write("fork #1 failed. %d (%s)\n" % (e.errno,\
				e.strerr))
			sys.exit(1)			
		

		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin,'r')
		so = file(self.stdout,'a+')
		se = file(self.stderr,'a+',0)

		#重定向标准输入/输出/错误
		os.dup2(si.fileno(),sys.stdin.fileno())
		os.dup2(so.fileno(),sys.stdout.fileno())
		os.dup2(se.fileno(),sys.stderr.fileno())

		#注册程序退出时的函数，即删掉pid文件
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write('%s\n' % pid )

	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		'''
		开始守护进程。
		'''
		#检查pid文件是否存在
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if pid:
			message = "pidfile %s already exist.Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)

		#Start the Daemon
		self._daemonize()
		self._run()

	def stop(self):
		#获取pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
		
		if not pid:
			message = "pidfile %s does not exist.Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return

		# try killing the daemon Pro
		try:
			while 1:
				os.kill(pid,SIGTERM)
				time.sleep(1)
		except OSError, e:
			e = str(e)
			if e.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
				else:
					print err
					sys.exit(1)

	def restart(self):
		self.stop()
		self.start()

	def _run(self):
		pass

class UploadServerDaemon(Daemon):
	
	def __init__(self,stdin = "/dev/null", stdout = "/dev/null", stderr = "/dev/null"):
		pidfile = CUR_PATH + "../.uploadServer_service.pid"
		Daemon.__init__(self,pidfile,stdin,stdout,stderr)


	def _run(self):
		runServer()

if __name__ == '__main__':
	daemon = UploadServerDaemon()
	if len(sys.argv) == 2:
		if "start" == sys.argv[1]:
			log.info("uploadServer Service start.")
			print "uploadServer Service start."
			daemon.start()
		elif "stop" == sys.argv[1]:
			log.info("uploadServer Service stop.")
			print "uploadServer Service stop."
			daemon.stop()
		elif "restart" == sys.argv[1]:
			log.info("uploadServer Service restart.")
			print "uploadServer Service restart."
			daemon.restart()
		else:
			print "Unknown command, valid param: start/stop/restart"
			sys.exit(2)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)



