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
import csma_macaw_rx



class top_block(grc_wxgui.top_block_gui):

	def __init__(self,options):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))
		#CHANGE ME
		self.cog_phy_0=phy.cog_phy(options.args)
		self.mac_0=csma_macaw_rx.csma_mac(options.dest_addr,options.source_addr,0.001,1)
		self.wake_up=heart_beat.heart_beat("check","wake_up",0.001)
		
				
		#CHANGE ME
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_char*1, options.output_file)
		self.gr_file_sink_0.set_unbuffered(True)
		self.extras_datagram_to_stream_0 = grextras.Datagram2Stream(1)

				
		##################################################
		# Connections
		##################################################
		self.connect((self.cog_phy_0,0),(self.mac_0,0))
		self.connect((self.mac_0,0),(self.cog_phy_0,0))
		self.connect((self.mac_0,1),(self.extras_datagram_to_stream_0,0))
		self.connect((self.extras_datagram_to_stream_0,0),(self.gr_file_sink_0,0))
		
		self.connect((self.wake_up,0),(self.mac_0,2))
		
		
		
		

def main():

	parser = OptionParser(option_class=eng_option, conflict_handler="resolve")
	parser.add_option("", "--args",default="",
	                  help="set the address of usrp_device [default='']")
	                        

	parser.add_option("", "--source_addr", type=int,default=100,
	                  help="set your radio(mac) address [default=100]")
	parser.add_option("", "--dest_addr", type=int, default=100,
	                  help="set dest radio(mac) address[default =100]")
	parser.add_option("","--output_file", default="Output",
	                  help="path of output file to store")
	

	
	
	(options, args) = parser.parse_args ()
	# build the graph
	tb=top_block(options)
	tb.Run(True)
	
	#tb.cog_phy_1.print_param()
	#tb.cog_phy_0.print_param()
if __name__=="__main__":
	main()
