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
ACK_WAIT =7


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
	def __init__(self,dest_addr,source_addr,sifs,nav):
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
		self.nav=nav
		

		#state variable

		
		self.arq_expected_sequence_no=0
		self.sifs=sifs
				
		#Queue for app packets
		self.q=Queue.Queue()
		self.msg_from_app=0
		
		

		self.sifs_in=False
		self.sifs_start=0.0
		self.ack_no=0
		self.ack_dest=0
		self.ack_pending=False
		

	def param(self):
		print "Destination addr : ",self.dest_addr
		print "Source addr : ",self.source_addr
		
	
	def work(self,ins,outs):
		#print "mac at work"
		

		#Taking packet out of App port and puting them on queue
		msg=self.pop_input_msg(APP_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			#print "msg from app ",  pkt_msg.buff.get().tostring()
			self.msg_from_app+=1
			#ITS RX
			#self.q.put(pkt_msg.buff.get().tostring())

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
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==RTS_PKT and ord(msg_str[PKT_INDEX_DEST])==self.source_addr ):
					self.nav= struct.unpack(">d",msg_str[NAV_START:NAV_END+1])[0]
					print "Sending CTS Request ..."
					pkt_str=chr(self.dest_addr)+chr(self.source_addr)+chr(CTS_PKT)+struct.pack('>d',self.nav)+"####"
					self.send_pkt(pkt_str,PHY_PORT)		

			 
				#For ACk_PKT
				if(ord(msg_str[PKT_INDEX_DEST])==self.source_addr and ord(msg_str[PKT_INDEX_CNTRL_ID])==ACK_PKT):
					#This is Rx 
					pass

				# For data pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==DATA_PKT):
					
					self.ack_pending=True
					self.ack_no=msg_str[PKT_INDEX_SEQ]
					self.ack_dest=msg_str[PKT_INDEX_SRC]
					#Sending packet to APP
					print "Data Pkt Received"
					send_pkt(msg_str[4:],APP_PORT)

				#For CTS pkts
				if(ord(msg_str[PKT_INDEX_CNTRL_ID])==CTS_PKT ):
					#Discard Its Rx
					pass
		else:
			#fishy
			pass

		if(self.ack_pending):
			self.sifs_start=time.time()
			while(time.time()<self.sifs_start+self.sifs):
				a=0
			print "sending ACK"
			pkt_str=chr(self.ack_dest)+chr(self.source_addr)+chr(ACK_PKT)+chr(self.ack_no)+"####"	
			send_pkt(pkt_str,PHY_PORT)

		
		
	#post msg data to phy/app port 
	def send_pkt(self,msg,port):
		
		#get a reference counted buffer to pass downstream
		buff = self.get_output_buffer(port)
		buff.offset = 0
		buff.length = len(msg)
		buff.get()[:] = numpy.fromstring(msg, numpy.uint8)
		self.post_output_msg(PHY_PORT,gras.PacketMsg(buff))
		
	#sense channel
	def cs_busy(self):
		return self.probe.level()>self.threshold
	
			