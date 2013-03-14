#test_client.py

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2


register_openers()

datagen,headers = multipart_encode({"img":open("1.jpg","rb"),"uid":"kk","submit":"Upload"})

request = urllib2.Request("http://127.0.0.1/PicUpload",datagen,headers)

print urllib2.urlopen(request).read()