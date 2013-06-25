import numpy
import gras
import time
from PMC import *
from math import pi
import time
from gnuradio import uhd

class sniff(gras.Block):
	def __init__(self,addr,uhd_control,usrp_sink):
		gras.Block.__init__(self,name="sniffer",
			in_sig = [numpy.complex64],
            out_sig = [numpy.complex64])
		#locating block
		self.uhd_control=self.locate_block("../uhd_control")
		#self.uhd_control=uhd_control
		self.start=time.time()
		self.freq_ls=[980e6,990e6]
		self.hop_index=0
		self.usrp_sink=usrp_sink

	def work(self,ins,outs):
		n=min(len(ins[0]),len(outs[0]))
		outs[0][:n]=ins[0][:n]
		self.consume(0,n)
		self.produce(0,n)
		if(time.time()>self.start):
			print "hoping"
			#self.usrp_sink.set_center_freq(self.freq_ls[self.hop_index])
			self.uhd_control.set("rx_freq",uhd.tune_request_t(self.freq_ls[self.hop_index]))
			self.hop_index=(self.hop_index+1)%len(self.freq_ls)
			self.start=time.time()+5


		

