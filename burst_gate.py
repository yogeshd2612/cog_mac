import numpy
import gras
import time
from PMC import *
from math import pi

SEARCH_EOB_IN = 0
FOUND_EOB_IN = 1

# /////////////////////////////////////////////////////////////////////////////
#                   Burst Gate - moves EOB to end of sample set
#                   Useful for DSP chains with propgation after eob insertion
# /////////////////////////////////////////////////////////////////////////////


class burst_gate(gras.Block):
	def __init__(self):
		gras.Block.__init__(self,name="burst_gate",
			in_sig=[numpy.complex64], out_sig=[numpy.complex64])
	def propagate_tags(self, which_input, iter):
		self.state = SEARCH_EOB_IN
		for tag in iter:
			if (tag.object().key)() == "tx_eob":
				self.state = FOUND_EOB_IN
			else:
				self.post_output_tag(0, tag)
		if self.state == FOUND_EOB_IN:
			tag = gras.StreamTag(PMC_M("tx_eob"), PMC_M(True))
			self.post_output_tag(which_input, gras.Tag(self.get_produced(0)-1, PMC_M(tag)))
	def work(self,ins,outs):
		n=min(len(ins[0]),len(outs[0]))
		outs[0][:n]=ins[0][:n]
		self.consume(0,n)
		self.produce(0,n)        

    	
