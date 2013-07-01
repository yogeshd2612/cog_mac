import numpy
import gras
import time
from PMC import *
from math import pi
from gnuradio import analog
import Queue
import random
import time
import struct
import thread
 
# cntrl commands
ACK_PKT = 90
DATA_PKT = 91
RTS_PKT = 92
CTS_PKT = 93



BROADCAST_ADDR = 255

#block port definition

PHY_PORT=0
APP_PORT=1
CTRL_PORT=2
PROBE_PORT=3


#Packet index definitions

PKT_INDEX_DEST = 0
PKT_INDEX_SRC = 1
PKT_INDEX_CNTRL_ID = 2     
PKT_INDEX_SEQ = 3
NAV_START=3
NAV_END=10

#States
IDLE = 0
BUSY = 1
DIFS = 2
SIFS = 3
RTS = 4
CTS = 5
BACKOFF = 6
ACK = 7
CTS_RCVD = 8
ACK_WAIT =9


#CS States

CS_IDLE=0
CS_BUSY=1


MAX_INPUT_QSIZE= 1000



class csma_mac(gras.Block):
	"""
	four input port : port 0 for phy ; port 1 for application ; port 2 for ctrl ;
	three output port : port 0 for phy , port 1 for application , port 2 for ctrl
	Stop and wait arq implementation with new message framework of gras motivated from pre-cog
	"""
	def __init__(self,dest_addr,source_addr,max_attempts,time_out,difs,sifs,cts_timeout,backoff,probe,threshold,nav):
		gras.Block.__init__(self,name="csma_mac",
			in_sig = [numpy.uint8,numpy.uint8,numpy.uint8],
            out_sig = [numpy.uint8,numpy.uint8,numpy.uint8])
		self.input_config(0).reserve_items = 0
		self.input_config(1).reserve_items = 0
		self.input_config(2).reserve_items = 0
		
		self.output_config(1).reserve_items = 4096
		self.output_config(0).reserve_items = 4096
		

		self.dest_addr=dest_addr
		self.source_addr=source_addr
		self.max_attempts=max_attempts
		self.time_out=time_out
		self.nav=nav
		self.cts_timeout=cts_timeout

		#state variable

		self.state=IDLE
		self.cs_state=CS_BUSY

		self.arq_expected_sequence_no=0
		self.sifs=sifs
		self.difs=difs
		self.backoff_range=backoff
		#measurement variable
		self.arq_sequence_err_cnt=0
		self.total_pkt_txed=0
		self.total_tx=0
		self.pkt_retxed=0
		self.tx_time=0
		self.no_attempts=0
		self.failed_arq=0

		
		#Queue for app packets
		self.q=Queue.Queue()
		self.msg_from_app=0
		
		#probe
		self.probe=probe
		self.threshold=threshold

		self.difs_in=False
		self.sifs_in=False
		self.difs_start=0.0
		self.sifs_start=0.0
		self.backoff_counter=0
		self.ack_no=0
		self.ack_dest_addr=0
		self.nav_wait=0
		self.quiet=False
		self.cts_start=0
		self.nav_start=0
		self.cts_rcvd=False
		self.ack_rcvd=False

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

		#Taking packet msg out of CTRL port
		msg=self.pop_input_msg(CTRL_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			#print "Its time.."
			a=0 #control


		#Taking pkt out of phy_port
		msg=self.pop_input_msg(PHY_PORT)
		pkt_msg=msg()

		if isinstance(pkt_msg, gras.PacketMsg) and len(pkt_msg.buff)>0: 
			msg_str=pkt_msg.buff.get().tostring()
			#print "Received something"
			if(len(msg_str) >4):
				#For RTS pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==RTS_PKT ):
					self.nav_wait= struct.unpack(">d",msg_str[NAV_START:NAV_END+1])[0]
					self.quiet=True
					self.nav_start=time.time()
					self.state=BUSY

			 
				#For ACk_PKT
				if(ord(msg_str[PKT_INDEX_DEST])==self.source_addr and ord(msg_str[PKT_INDEX_CNTRL_ID])==ACK_PKT):
					if(ord(msg_str[PKT_INDEX_SEQ])==self.arq_expected_sequence_no):
						#print "pack tx successfully ",self.arq_expected_sequence_no
						self.nav=time.time()-self.tx_time()
						self.arq_expected_sequence_no=(self.arq_expected_sequence_no+1)%255
						self.total_pkt_txed+=1
						self.state=BUSY
						self.ack_rcvd=True

				# For data pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==DATA_PKT):
					#This is transmitter
					pass

				#For CTS pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==CTS_PKT ):
					if(ord(msg_str[PKT_INDEX_DEST])==self.source_addr):
						self.cts_rcvd=True
					else:
						self.nav_wait= struct.unpack(">d",msg_str[NAV_START:NAV_END+1])[0]
						self.quiet=True
						self.nav_start=time.time()
						self.state=BUSY
		else:
			#fishy
			pass


		#state machine
				
		if(self.state==IDLE):
			self.state=DIFS
		if(self.state==DIFS):
			if(not self.difs_in):
				self.difs_in=True
				self.difs_start=time.time()
			if(time.time()<self.difs_start+self.difs):
				if(self.cs_busy()):
					self.state=BACKOFF
					self.backoff_counter=random.randrange(self.backoff_range)
			else:
				self.state=RTS
		if(self.state=BACKOFF):
			while(not self.cs_busy() and self.backoff_counter>0):
				self.backoff_counter-=1
			if(self.backoff_counter==0):
				self.state=RTS

		if(self.state==RTS):
			#adding frame info
			print "Sending RTS Request ..."
			pkt_str=chr(self.dest_addr)+chr(self.source_addr)+chr(RTS_PKT)+struct.pack('>d',self.nav)+"####"
			self.send_pkt(pkt_str,PHY_PORT)
			self.cts_start=time.time()
			self.state=CTS

		if(self.state==CTS):
			#waiting for CTS
			if(self.cts_rcvd):
				if(not self.re_tx):
					self.outgoing_msg=self.q.get()
					self.no_attempts=1
				else:
					self.no_attempts+=1
				self.tx_time=time.time()		
				self.total_tx+=1
				print "Transmitting Pkt no. ",self.arq_expected_sequence_no
				pkt_str=chr(self.dest_addr)+chr(self.source_addr)+chr(RTS_PKT)+chr(self.arq_expected_sequence_no)+self.outgoing_msg
				self.send_pkt(pkt_str,PHY_PORT)
				self.ack_rcvd=False
				self.re_tx=False
				self.state=ACK_WAIT
			if(time.time()>self.cts_start+self.cts_timeout):
				self.state=IDLE

		if(self.state==BUSY):
			if(self.quiet):
				if(time.time()>self.nav_start+self.nav_wait):
					self.state=IDLE
					self.quiet=False

			if(self.ack_rcvd and not self.quiet):
				self.state=IDLE

			if(not self.ack_rcvd):
				if(time.time()-self.tx_time>self.time_out):
				if(self.no_attempts>self.max_attempts):
					print "pkt failed arq "
					self.failed_arq+=1
					# trying next packet
					self.state=IDLE
					self.arq_expected_sequence_no=(self.arq_expected_sequence_no+1)%255 
				else:
					#retransmit
					print "Retransmitting : ",self.no_attempts," ",time.time()-self.tx_time," ",self.time_out
					self.state=IDLE
					self.re_tx=True
			
	
		
	#post msg data to phy/app port 
	def send_pkt(self,msg,port):
		
		#get a reference counted buffer to pass downstream
		buff = self.get_output_buffer(port)
		buff.offset = 0
		buff.length = len(pkt_str)
		buff.get()[:] = numpy.fromstring(pkt_str, numpy.uint8)
		self.post_output_msg(PHY_PORT,gras.PacketMsg(buff))
		
	#sense channel
	def cs_busy(self):
		return self.probe.level()>self.threshold
	
			