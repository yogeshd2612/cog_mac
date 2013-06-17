import numpy
import gras
import time
from PMC import *
from math import pi
import Queue
import time
import thread

# cntrl commands
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


MAX_INPUT_QSIZE= 1000



class simple_arq(gras.Block):
	"""
	three input port : port 0 for phy ; port 1 for application ; port 2 for ctrl
	two output port : port 0 for phy , port 1 for application , port 2 for ctrl
	Stop and wait arq implementation with new message framework of gras motivated from pre-cog
	"""
	def __init__(self,dest_addr,source_addr,max_attempts,time_out):
		gras.Block.__init__(self,name="simple_arq",
			in_sig = [numpy.uint8,numpy.uint8,numpy.uint8],
            out_sig = [numpy.uint8,numpy.uint8,numpy.uint8])
		self.input_config(0).reserve_items = 0
		self.input_config(1).reserve_items = 0
		self.input_config(2).reserve_items = 0
		#self.input_config(1).reserve_items = 4096
		#self.output_config(0).reserve_items = 4096
		

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
		self.failed_arq=0
		#measurement variable
		self.arq_sequence_err_cnt=0
		self.total_pkt_txed=0
		self.total_tx=0
		self.i=0
		#Queue for app packets
		self.q=Queue.Queue()
		self.msg_from_app=0
		self.a=0
		
	def param(self):
		print "Destination addr : ",self.dest_addr
		print "Source addr : ",self.source_addr
		print "TimeOut : ",self.time_out
		print "Max Attempts : ",self.max_attempts

	def work(self,ins,outs):
		#print "mac at work"
		#Taking packet out of App port and puting them on queue
		msg=self.pop_input_msg(APP_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			#print "msg from app ",  pkt_msg.buff.get().tostring()
			self.msg_from_app+=1
			self.q.put(pkt_msg.buff.get().tostring())


		if(self.arq_state==ARQ_CHANNEL_IDLE):
			#print "In idle state "
			if not self.q.empty():
				self.outgoing_msg=self.q.get()
				#print self.outgoing_msg
				self.send_pkt_phy(self.outgoing_msg,self.arq_expected_sequence_no,DATA_PKT)
				self.no_attempts=1
				self.total_tx+=1
				self.tx_time=time.time()
				self.arq_state=ARQ_CHANNEL_BUSY
		
		# Taking packet out of control port
		msg=self.pop_input_msg(CTRL_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg):
			#wake up time to check time_out for ack
			#print "its time ..."
			a=0


		msg=self.pop_input_msg(PHY_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			msg_str=pkt_msg.buff.get().tostring()
			if(len(msg_str) >3 and ord(msg_str[PKT_INDEX_DEST])==self.source_addr):
				# if packet is ack
				#print "i am ",self.source_addr," and rx packet from ",ord(msg_str[PKT_INDEX_DEST])," pkt type : ",ord(msg_str[PKT_INDEX_CNTRL_ID])," seq no. ",ord(msg_str[PKT_INDEX_SEQ])
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==ACK_PKT):
					if(ord(msg_str[PKT_INDEX_SEQ])==self.arq_expected_sequence_no):
						print "pack tx successfully ",self.arq_expected_sequence_no
						self.arq_expected_sequence_no=(self.arq_expected_sequence_no+1)%255
						self.total_pkt_txed+=1
						self.arq_state=ARQ_CHANNEL_IDLE

				# For data pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==DATA_PKT):
					#send ack
					self.send_pkt_phy("####",ord(msg_str[PKT_INDEX_SEQ]),ACK_PKT)
					#send pkt to app
					self.send_pkt_app(msg_str[4:])
		else:
			#fishy
			a=0

			
		if self.arq_state==ARQ_CHANNEL_BUSY:
			#print "channel_busy",time.time()-self.tx_time
			if(time.time()-self.tx_time>self.time_out):
				if(self.no_attempts>self.max_attempts):
					print "pkt failed arq "
					self.failed_arq+=1
					# trying next packet
					self.arq_state=ARQ_CHANNEL_IDLE
					self.arq_expected_sequence_no=(self.arq_expected_sequence_no+1)%255 
				else:
					#retransmit
					print "Retransmitting : ",self.no_attempts," ",time.time()-self.tx_time," ",self.time_out
					self.send_pkt_phy(self.outgoing_msg,self.arq_expected_sequence_no,
						DATA_PKT)
					self.no_attempts+=1
					self.tx_time=time.time()
					self.total_tx+=1

		#print "msg queued up ",self.msg_from_app

	#post msg data to phy port- msg is string
	def send_pkt_phy(self,msg,pkt_cnt,protocol_id):
		#Framing MAC Info
		if(protocol_id==ACK_PKT):
			print "Transmitting ACK no. ",pkt_cnt
		else:
			print "Transmitting PKT no. ",pkt_cnt
		pkt_str=chr(self.dest_addr)+chr(self.source_addr)+chr(protocol_id)+chr(pkt_cnt)+msg

		#get a reference counted buffer to pass downstream
		buff = self.get_output_buffer(PHY_PORT)
		buff.offset = 0
		buff.length = len(pkt_str)
		buff.get()[:] = numpy.fromstring(pkt_str, numpy.uint8)
		self.post_output_msg(PHY_PORT,gras.PacketMsg(buff))
	
	#post msg data to app port - msg is string
	def send_pkt_app(self,msg):
		#print "Recieved data packet."
 		#get a reference counted buffer to pass downstream
		buff = self.get_output_buffer(APP_PORT)
		buff.offset = 0
		buff.length = len(msg)
		buff.get()[:] = numpy.fromstring(msg, numpy.uint8)
		self.post_output_msg(APP_PORT,gras.PacketMsg(buff))
