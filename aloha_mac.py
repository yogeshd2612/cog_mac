import numpy
import gras
import time
from PMC import *
from math import pi
import Queue
import time
import thread

# cntl commands
ACK_PKT = 90
DATA_PKT = 91


BROADCAST_ADDR = 255

#block port definition
PHY_PORT=0
APP_PORT=1
CTRL_PORT=2

#Packet index definitions
PKT_INDEX_DEST = 0
PKT_INDEX_SRC = 1
PKT_INDEX_CNTRL_ID = 2     
PKT_INDEX_SEQ = 3

#ARQ Channel States
ARQ_CHANNEL_BUSY = 1
ARQ_CHANNEL_IDLE = 0

#
MAX_INPUT_QSIZE= 1000


class aloha_mac(gras.Block):
	"""
	three inputs : from_phy ,from_app , ctrl_in
	three outputs : to_phy , to_app, ctrl_out
	"""
	def __init__(self,dest_addr,source_addr,max_attempts,time_out):
		gras.Block.__init__(self,name="sniffer",
			in_sig = [numpy.uint8,numpy.uint8],
            out_sig = [numpy.uint8,numpy.uint8])
		self.output_config(0).reserve_items = 4096
		self.dest_addr=dest_addr
		self.source_addr=source_addr
		self.max_attempts=max_attempts
		self.time_out=time_out
		#state variable
		self.arq_expected_sequence_no=0
		self.pkt_retxed=0
		self.tx_time=0
		self.arq_state=ARQ_CHANNEL_IDLE
		self.no_attempts=0
		#measurement variable
		self.arq_sequence_err_cnt=0
		self.total_pkt_txed=0
		self.total_tx=0

		
		#For storing app packets while ARQ is BUSY
		#self.queue = Queue.Queue()

	#post msg data to phy port- msg is string
	def send_pkt_phy(self,msg,pkt_cnt,protocol_id):
		#Framing MAC Info
		pkt_str=chr(self.dest_addr)+chr(self.source_addr)+chr(protocol_id)+chr(pkt_cnt)+msg
		self.post_output_msg(PHY_PORT,pkt_str)

	#post msg data to app port - msg is string
	def send_pkt_app(self,msg):
		self.post(APP_PORT,msg)

	
	def work(self,ins,outs):
		while(1):
			print "working..."
			if(self.arq_state==ARQ_CHANNEL_IDLE):
				msg=self.pop_input_msg(APP_PORT)
				pkt_msg=msg()
				if not isinstance(pkt_msg, gras.PacketMsg): return	
				self.outgoing_msg=pkt_msg.buff.get().tostring()
				send_pkt_phy(msg,self.arq_expected_sequence_no,DATA_PKT)
				self.no_attempts=1
				self.total_tx+=1
				self.tx_time=time.time()
				self.arq_state=ARQ_CHANNEL_BUSY

			else:
				
				msg=self.pop_input_msg(PHY_PORT)
				pkt_msg=msg()
				if not isinstance(pkt_msg, gras.PacketMsg): return	
				msg_str=pkt_msg.buff.get().tostring()
				if(len(msg_str) >3 and msg_str[PKT_INDEX_DEST]==self.dest_addr):
					# if packet is ack
					if(msg_str[PKT_INDEX_CNTRL_ID]==ACK_PKT):
						if(msg_str[PKT_INDEX_SEQ]==self.arq_expected_sequence_no):
							print "pack tx successfully ",self.arq_expected_sequence_no
							self.arq_expected_sequence_no=(self.arq_expected_sequence_no+1)%256
							self.total_pkt_txed+=1
							self.arq_state=ARQ_CHANNEL_IDLE

						else:
							if(time.time()-self.tx_time>self.time_out):
								if(self.no_attempts>self.max_attempts):
									print "Channel is broken"
									return
								#retransmit
								print "Retransmitting : ",no_attempts
								send_pkt_pht(self.outgoing_msg,self.arq_expected_sequence_no,
									DATA_PKT)
								self.no_attempts+=1
								self.tx_time=time.time()
								self.total_tx+=1

					# For data pkts
					if(msg_str[PKT_INDEX_CNTRL_ID]==DATA_PKT):
						#send ack
						self.send_pkt_phy("",msg_str[PKT_INDEX_SEQ],ACK_PKT)
						#send pkt to app
						self.send_pkt_app(msg_str)



	
