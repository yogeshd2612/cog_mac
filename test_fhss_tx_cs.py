from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import wxgui as grc_wxgui
from gnuradio.wxgui import fftsink2
from optparse import OptionParser
import grextras
import wx
import gras
import phy
import fhss_tx_cs
import heart_beat
import sys
import time
import spectrum_sense
import fft_probe

class top_block(grc_wxgui.top_block_gui):#grc_wxgui.top_block_gui

	def __init__(self,options):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))
		
		#sensing chain
		self.cs_0=spectrum_sense.pwrfft_c(options.sample_rate,options.fft_size,
								options.sample_rate/options.fft_size,1,False)
		
		self.probe_0=fft_probe.probe(options.fft_size,options.sense_band,options.sample_rate,"977e6,978.5e6,980e6,981.5e6,983e6",options.freq)
		#
		self.cog_phy_0=phy.cog_phy(options.args,options.sense_band,options.sample_rate,options.freq)
		# dest_addt,source_addr,max_attempts,time_out
		'''self.fhss_tx_0=fhss_tx.fhss_engine_tx(options.dest_addr,options.source_addr,"977e6,978.5e6,980e6,981.5e6,983e6"
			,7,0.05,1,0.05,2000,options.args,options.args)'''
		self.fhss_tx_0=fhss_tx_cs.fhss_engine_tx(options.dest_addr,options.source_addr,"977e6,978.5e6,980e6,981.5e6,983e6"
			,3,0.5,0.005,0.05,2000,self.cog_phy_0.uhd_usrp_source,self.cog_phy_0.uhd_usrp_sink,self.probe_0)
		self.wake_up=heart_beat.heart_beat("check","wake_up",0.01)
		
		self.gr_file_source_0 = gr.file_source(gr.sizeof_char*1, options.input_file, True)
		
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_char*1, options.output_file)
		
		self.gr_file_sink_0.set_unbuffered(True)
		
		self.extras_stream_to_datagram_0 = grextras.Stream2Datagram(1, options.pkt_size)
		self.extras_datagram_to_stream_0 = grextras.Datagram2Stream(1)

		
		##################################################
		# Connections
		##################################################
		self.connect((self.gr_file_source_0, 0), (self.extras_stream_to_datagram_0, 0))
		self.connect((self.extras_stream_to_datagram_0,0),(self.fhss_tx_0,1))
		self.connect((self.cog_phy_0,0),(self.fhss_tx_0,0))
		self.connect((self.fhss_tx_0,0),(self.cog_phy_0,0))
		self.connect((self.fhss_tx_0,1),(self.extras_datagram_to_stream_0,0))
		self.connect((self.extras_datagram_to_stream_0,0),(self.gr_file_sink_0,0))
		#self.connect((self.cog_phy_0,1),(self.wxgui_fftsink2_0,0))
		self.connect((self.wake_up,0),(self.fhss_tx_0,2))
		self.connect((self.cog_phy_0,1),(self.cs_0,0))
		self.connect((self.cs_0,0),(self.probe_0,0))
		#self.connect((self.cog_phy_0,1),(self.tags_d_0,0))

		

def main():

	parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
	parser.add_option("", "--args",default="",
	                  help="set the address of usrp_device [default='']")
	                        

	parser.add_option("", "--source_addr", type=int,default=100,
	                  help="set your radio(mac) address [default=100]")
	parser.add_option("", "--dest_addr", type=int, default=100,
	                  help="set dest radio(mac) address[default =100]")
	parser.add_option("","--max_attempts", type=int , default=8,
	                  help="max attempts at retransmission before moving to next packet [default=8]")
	parser.add_option("","--time_out", type=float , default=4,
	                  help="time_out for ack [default=3]")
	parser.add_option("","--input_file", 
	                  help="path of input file to transmit")
	parser.add_option("","--output_file", default="Output",
	                  help="path of output file to store")
	parser.add_option("","--pkt_size", type=int, default=128,
	                  help="set the packet size [default=128]")
	parser.add_option("","--sample_rate", type=int, default=int(1e6),
	                  help="set the packet size [default=1e6]")
	parser.add_option("","--freq", type=int, default=980e6,
	                  help="set the packet size [default=980e6]")
	parser.add_option("","--fft_size", type=int, default=1024,
	                  help="set the packet size [default=1024]")
	parser.add_option("","--sense_band", type=int, default=8e6,
	                  help="set the packet size [default=8e6]")
	
	
	(options, args) = parser.parse_args ()
	# build the graph
	if(options.input_file==None):
		print "give path of input file to transmit"
		parser.print_help()
		sys.exit(1)
	
	tb=top_block(options)
	#tb.adopt_element("uhd_control_sink",uhd_control_sink)
	#tb.adopt_element("uhd_control_source",uhd_control_source)

	
	#tb.Run(True)
	tb.start()
	while(1):
		#print "freq :",tb.cog_phy_0.uhd_usrp_sink.get_center_freq()
		time.sleep(2)

	#tb.cog_phy_1.print_param()
	#tb.cog_phy_0.print_param()
if __name__=="__main__":
	main()
