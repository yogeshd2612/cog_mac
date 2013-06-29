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

#Packet index definitions
PKT_INDEX_DEST = 0
PKT_INDEX_SRC = 1
PKT_INDEX_CNTRL_ID = 2     
PKT_INDEX_SEQ = 3
PKT_INDEX_TIME =4

#ARQ Channel States
ARQ_CHANNEL_BUSY = 1
ARQ_CHANNEL_IDLE = 0


MAX_INPUT_QSIZE= 1000



class fhss_engine_tx(gras.Block):
	"""
	three input port : port 0 for phy ; port 1 for application ; port 2 for ctrl ; 
	two output port : port 0 for phy , port 1 for application , port 2 for ctrl
	"""
	def __init__(self,dest_addr,source_addr,freq_list,hop_interval,post_guard,pre_guard,lead_limit,link_bps,usrpSource,usrpSink,probe):
		gras.Block.__init__(self,name="fhss_engine_tx",
			in_sig = [numpy.uint8,numpy.uint8,numpy.uint8,numpy.uint8],
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
		self.post_guard = post_guard
		self.pre_guard = pre_guard
		self.lead_limit = lead_limit
		self.link_bps = link_bps
		self.freq_list = map(float,freq_list.split(','))
		self.hop_index = 0 	
		
		self.bytes_per_slot = int( ( self.hop_interval - self.post_guard - self.pre_guard ) * self.link_bps / 8 )

		self.has_old_msg = False
		self.overhead = 151

		self.pkt_count=0

		self.start=False
		#Queue for app packets
		self.q=Queue.Queue()
		self.tx_queue = Queue.Queue()
		self.msg_from_app=0
		# finding control blocks for source and sink usrps
		'''uhd_control_source=self.locate_block("/uhd_control_source")
		uhd_control_sink=self.locate_block("/uhd_control_sink")'''
		'''self.uhd_control_sink=grextras.UHDControlPort(usrpSink)
		self.uhd_control_source=grextras.UHDControlPort(usrpSource)'''
		self.usrp_source=usrpSource
		self.usrp_sink=usrpSink
		self.probe=probe
		self.threshold=1e6


	def param(self):
		print "Destination addr : ",self.dest_addr
		print "Source addr : ",self.source_addr
		
	def tx_frames(self):
		#print self.msg_from_app
		toatal_byte_count=0
		frame_count=0
		print "tx_frames"
		#control the uhd
		
		
		self.usrp_sink.set_center_freq(self.freq_list[self.hop_index])
		self.usrp_sink.clear_command_time()
		self.usrp_sink.set_command_time(uhd.time_spec_t(self.antenna_start))
		self.hop_index=(self.hop_index+1)%(len(self.freq_list))	
		print self.antenna_start,self.usrp_sink.get_time_now().get_real_secs()
		print self.usrp_sink.get_center_freq()

		#put residue from previous execution
		if self.has_old_msg:
			toatal_byte_count+=len(self.old_msg)+self.overhead
			self.tx_queue.put(self.old_msg)
			frame_count+=1
			self.has_old_msg=False
			#print 'old Msg'
		#fill outgoing queue until empty or maximum byter queued for slot
		while(not self.q.empty()):
			msg=self.q.get()
			toatal_byte_count+=len(msg)+self.overhead
			if(toatal_byte_count>=self.bytes_per_slot):
				self.has_old_msg=True
				self.old_msg=msg
				#print 'residue'
				break
			else:
				self.has_old_msg=False
				self.tx_queue.put(msg)
				frame_count+=1
		#print frame_count
		while frame_count:
			msg=self.tx_queue.get()
			#print "sending"
			self.send_pkt_phy(msg,self.pkt_count,DATA_PKT)
			self.pkt_count=(self.pkt_count+1)%256
			frame_count-=1
		
	
	def work(self,ins,outs):
		#print self.msg_from_app
		#Taking packet out of App port and puting them on queue
		#self.probe.print_cs_info()
		print "FFT avg :",self.probe.fft_avg()
		time.sleep(2)
		msg=self.pop_input_msg(APP_PORT)
		pkt_msg=msg()
		if isinstance(pkt_msg, gras.PacketMsg): 
			#print "msg from app ",  pkt_msg.buff.get().tostring()
			self.msg_from_app+=1
			#self.q.put(pkt_msg.buff.get().tostring())

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
			

		#determine first transmit slot
		if not self.start:
			self.start=True
			self.time_transmit_start=self.usrp_sink.get_time_now().get_real_secs()+10.0*self.lead_limit
			self.interval_start=self.usrp_sink.get_time_now().get_real_secs()+self.lead_limit
		else:
			if( self.usrp_sink.get_time_now().get_real_secs()>self.time_transmit_start):
				#print self.time_update,self.usrp_sink.get_time_now().get_real_secs(),self.time_transmit_start
				self.antenna_start = self.interval_start+self.post_guard
				#print self.usrp_sink.get_time_now().get_real_secs(),self.antenna_start,self.time_transmit_start
				#self.tx_frames()
				self.interval_start+=self.hop_interval
				self.time_transmit_start=self.interval_start-self.lead_limit

	
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
		