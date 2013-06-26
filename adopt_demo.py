import numpy
import gras
import time
from PMC import *
from math import pi
import time
from gnuradio import uhd

class sniff(gras.Block):
	def __init__(self):
		gras.Block.__init__(self,name="sniffer",
			in_sig = [numpy.complex64],
            out_sig = [numpy.complex64])
		#locating block
		self.freq_ls=[980e6,990e6]
		self.start=time.time()
		self.hop_index=0
		
	def notify_active(self):
		#locating block
		self.uhd_control=self.locate_block("../uhd_control")
	def work(self,ins,outs):
		n=min(len(ins[0]),len(outs[0]))
		outs[0][:n]=ins[0][:n]
		self.consume(0,n)
		self.produce(0,n)
		if(time.time()>self.start):
			print "hoping"
			self.uhd_control.set("tx_freq",uhd.tune_request_t(self.freq_ls[self.hop_index]))
			self.hop_index=(self.hop_index+1)%len(self.freq_ls)
			self.start=time.time()+5


		

