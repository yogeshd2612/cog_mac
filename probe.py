import numpy
import gras
import time
from PMC import *
from math import pi

class probe(gras.Block):
	def __init__(self,threshold_db,alpha):
		gras.Block.__init__(self,name="sniffer",
			in_sig = [numpy.complex64],
            out_sig = None)
		self.register_getter("level", self.level)
		self.register_setter("set_threshold", self.set_threshold)
		self.register_setter("set_alpha", self.set_alpha)
		self.threshold_db=threshold_db
		self.alpha=alpha
		self.output=0.0
	def work(self,ins,outs):
		#print "probe working"
		n=len(ins[0])
		for i in range(n):
			mag_sqrd=ins[0][i].real*ins[0][i].real+ins[0][i].imag*ins[0][i].imag
			self.output=self.alpha*mag_sqrd+(1-self.alpha)*self.output
		#print self.output
		self.consume(0,n)
	def level(self):
		return self.output
	def set_threshold(self,threshold):
		self.threshold_db=threshold

	def set_alpha(self,alpha):
		self.alpha=alpha
