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
import aloha_mac
import heart_beat
import sys
import probe
import csma

class top_block(grc_wxgui.top_block_gui):

	def __init__(self,options):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))
		#CHANGE ME
		self.cog_phy_0=phy.cog_phy(options.args)
		# dest_addt,source_addr,max_attempts,time_out
		self.probe_0=probe.probe(0,1)
		self.mac_0=csma.csma_mac(options.dest_addr,options.source_addr,options.max_attempts,options.time_out,0.05,0.00001,10000,self.probe_0,1e-6)
		self.wake_up=heart_beat.heart_beat("check","wake_up",0.001)
		
		#CHANGE ME
		self.gr_file_source_0 = gr.file_source(gr.sizeof_char*1, options.input_file, True)
		
		#CHANGE ME
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_char*1, options.output_file)
		self.gr_file_sink_0.set_unbuffered(True)
		self.extras_stream_to_datagram_0 = grextras.Stream2Datagram(1, options.pkt_size)
		self.extras_datagram_to_stream_0 = grextras.Datagram2Stream(1)

		self.wxgui_fftsink2_0 = fftsink2.fft_sink_c(
			self.GetWin(),
			baseband_freq=990e6,
			y_per_div=10,
			y_divs=10,
			ref_level=0,
			ref_scale=2.0,
			sample_rate=1e6,
			fft_size=1024,
			fft_rate=15,
			average=False,
			avg_alpha=None,
			title="FFT Plot of source usrp",
			peak_hold=True,
		)
		#self.Add(self.wxgui_fftsink2_0.win)

		#self.tags_d_0=tags_demo.tags_demo()
		#self.extras_stream_to_datagram_1 = grextras.Stream2Datagram(1, 256)
		#self.extras_datagram_to_stream_1 = grextras.Datagram2Stream(1)
		
		
		##################################################
		# Connections
		##################################################
		self.connect((self.gr_file_source_0, 0), (self.extras_stream_to_datagram_0, 0))
		self.connect((self.extras_stream_to_datagram_0,0),(self.mac_0,1))
		self.connect((self.cog_phy_0,0),(self.mac_0,0))
		self.connect((self.mac_0,0),(self.cog_phy_0,0))
		self.connect((self.mac_0,1),(self.extras_datagram_to_stream_0,0))
		self.connect((self.extras_datagram_to_stream_0,0),(self.gr_file_sink_0,0))
		#self.connect((self.cog_phy_0,1),(self.wxgui_fftsink2_0,0))
		self.connect((self.wake_up,0),(self.mac_0,2))
		self.connect((self.cog_phy_0,1),(self.probe_0,0))
		#self.connect((self.cog_phy_0,1),(self.mac_0,3))
		#self.connect((self.cog_phy_0,1),(self.tags_d_0,0))

		"""self.connect((self.gr_file_source_1, 0), (self.extras_stream_to_datagram_1, 0))
		self.connect((self.extras_stream_to_datagram_1,0),(self.mac_1,1))
		self.connect((self.cog_phy_1,0),(self.mac_1,0))
		self.connect((self.mac_1,0),(self.cog_phy_1,0))
		self.connect((self.mac_1,1),(self.extras_datagram_to_stream_1,0))
		self.connect((self.extras_datagram_to_stream_1,0),(self.gr_file_sink_1,0))"""


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

	
	
	(options, args) = parser.parse_args ()
	# build the graph
	if(options.input_file==None):
		print "give path of input file to transmit"
		parser.print_help()
		sys.exit(1)

	tb=top_block(options)
	tb.Run(True)
	
	#tb.cog_phy_1.print_param()
	#tb.cog_phy_0.print_param()
if __name__=="__main__":
	main()
