import numpy
import gras
import time
from PMC import *
from math import pi

class heart_beat(gras.Block):
	def __init__(self,key,value,period):
		gras.Block.__init__(self,name="heart_beat",
			in_sig = None,
            out_sig = [numpy.uint8])
		self.key=key
		self.value=value
		self.period=period
	def work(self,ins,outs):
		while(1):
			#print "heart_beat at work"
			buff = self.get_output_buffer(0)
			buff.offset = 0
			buff.length = len(self.value)
			buff.get()[:] = numpy.fromstring(self.value, numpy.uint8)
			self.post_output_msg(0,gras.PacketMsg(PMC_M(self.key),buff))
			time.sleep(self.period)

