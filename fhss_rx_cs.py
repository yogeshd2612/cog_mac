import numpy
import gras
import time
from PMC import *
from math import pi
import Queue
import thread

from gnuradio import uhd
import grextras
# cntrl commands
ACK_PKT = 90
DATA_PKT = 91


BROADCAST_ADDR = 255

#block port definition
PHY_PORT=0
APP_PORT=1
CTRL_PORT=2
TAGS_PORT=3

#Packet index definitions
PKT_INDEX_DEST = 0
PKT_INDEX_SRC = 1
PKT_INDEX_CNTRL_ID = 2     
PKT_INDEX_SEQ = 3
PKT_INDEX_NHOP =4

#ARQ Channel States
ARQ_CHANNEL_BUSY = 1
ARQ_CHANNEL_IDLE = 0


MAX_INPUT_QSIZE= 1000

#Time state Variables
HAVE_TIME=0

#RX state machine
RX_INIT = 0 
RX_SEARCH = 1
RX_FOUND = 2

LOST_SYNC_THRESHOLD=0


class fhss_engine_rx(gras.Block):
	"""
	three input port : port 0 for phy ; port 1 for application ; port 2 for ctrl ; 
	two output port : port 0 for phy , port 1 for application , port 2 for ctrl
	"""
	def __init__(self,dest_addr,source_addr,freq_list,hop_interval,usrpSource,usrpSink):
		gras.Block.__init__(self,name="fhss_engine_tx",
			in_sig = [numpy.uint8,numpy.uint8,numpy.uint8],
            out_sig = [numpy.uint8,numpy.uint8,numpy.uint8])
		self.input_config(0).reserve_items = 0
		self.input_config(1).reserve_items = 0
		self.input_config(2).reserve_items = 0
		self.output_config(1).reserve_items = 4096
		self.output_config(0).reserve_items = 4096


		self.dest_addr=dest_addr
		self.source_addr=source_addr
		self.freq_list=freq_list	
		self.hop_interval = hop_interval
		self.freq_list = sorted(map(float,freq_list.split(',')))

		self.hop_index = 0 	
		self.start=False
		self.last_hop_time=0
		#Queue for app packets
		self.q=Queue.Queue()
		self.tx_queue = Queue.Queue()
		self.msg_from_app=0

		#usrp instances	
		self.usrp_source=usrpSource
		self.usrp_sink=usrpSink

		self.pkt_received = 0

	def param(self):
		print "Destination addr : ",self.dest_addr
		print "Source addr : ",self.source_addr
		
	
	def work(self,ins,outs):
		#print self.msg_from_app
		#Taking packet out of App port and puting them on queue
		msg=self.pop_input_msg(APP_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			#print "msg from app ",  pkt_msg.buff.get().tostring()
			self.msg_from_app+=1
			#self.q.put(pkt_msg.buff.get().tostring())
			#ITS RECEIVER NO NEED TO ACCUMULATE PACKET FROM APP

		#Taking packet msg out of CTRL port
		msg=self.pop_input_msg(CTRL_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			pass

		#Taking packet msg out of PHY port
		msg=self.pop_input_msg(PHY_PORT)
		pkt_msg=msg()

		if isinstance(pkt_msg, gras.PacketMsg) and len(pkt_msg.buff)>0: 
			#print "hello ",len(pkt_msg.buff)
			msg_str=pkt_msg.buff.get().tostring()
			if(len(msg_str) >5 and (ord(msg_str[PKT_INDEX_DEST])==self.source_addr or ord(msg_str[PKT_INDEX_DEST])==BROADCAST_ADDR)):
				if(not self.start):
					print "Starting sync operation ..."
					self.start=True
					self.last_hop_time=self.usrp_source.get_time_now().get_real_secs()
					#reterieving info about nhop from packet
					self.hop_index=ord(msg_str[PKT_INDEX_NHOP])
					self.pkt_received+=1

				# For data pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==DATA_PKT):
					print "Received data pkt at freq : ",self.freq_list[self.hop_index-1]
					#reterieving info about nhop from packet
					self.hop_index=ord(msg_str[PKT_INDEX_NHOP])
					self.pkt_received+=1					
					#send pkt to app
					self.send_pkt_app(msg_str[5:])
			else:
				print "len ",len(msg_str)
		else:
			#fishy
			a=0
			

		#HOP
		if(self.start and self.usrp_source.get_time_now().get_real_secs()>self.last_hop_time+self.hop_interval):
			if(self.pkt_received<=LOST_SYNC_THRESHOLD):
				print "Lost Sync ..."
				self.start=False
			else:
				print "hopping to : ",self.freq_list[self.hop_index]
				self.usrp_source.set_center_freq(self.freq_list[self.hop_index])
				self.last_hop_time=self.usrp_source.get_time_now().get_real_secs()
				self.pkt_received=0

	#post msg data to app port - msg is string
	def send_pkt_app(self,msg):
		#print "Recieved data packet."
 		#get a reference counted buffer to pass downstream
 		buff = self.get_output_buffer(APP_PORT)
		buff.offset = 0
		buff.length = len(msg)
		buff.get()[:] = numpy.fromstring(msg, numpy.uint8)
		self.post_output_msg(APP_PORT,gras.PacketMsg(buff))
		