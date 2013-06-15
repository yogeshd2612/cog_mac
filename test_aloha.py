from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import grextras
import wx
import gras
import phy
import aloha_mac
import my_block

class top_block(grc_wxgui.top_block_gui):

	def __init__(self):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

		self.cog_phy_0=phy.cog_phy("addr=10.32.19.156")
		self.mac_0=aloha_mac.aloha_mac(10,10,8,2)
		
		#self.cog_phy_1=phy.cog_phy("addr=10.32.19.164")
		#self.mac_1=aloha_mac.aloha_mac(11,10,25,16)

		self.gr_file_source_0 = gr.file_source(gr.sizeof_char*1, "/home/electron/project/cog-mac/testfile1", True)
		#self.gr_file_source_1 = gr.file_source(gr.sizeof_char*1, "/home/electron/project/cog-mac/testfile1", True)
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_char*1, "/home/electron/project/cog-mac/testOutput11")
		#self.gr_file_sink_1 = gr.file_sink(gr.sizeof_char*1, "/home/electron/project/cog-mac/testOutput10")
		self.gr_file_sink_0.set_unbuffered(True)
		#self.gr_file_sink_1.set_unbuffered(True)
		self.extras_stream_to_datagram_0 = grextras.Stream2Datagram(1, 1024)
		self.extras_datagram_to_stream_0 = grextras.Datagram2Stream(1)

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

		"""self.connect((self.gr_file_source_1, 0), (self.extras_stream_to_datagram_1, 0))
		self.connect((self.extras_stream_to_datagram_1,0),(self.mac_1,1))
		self.connect((self.cog_phy_1,0),(self.mac_1,0))
		self.connect((self.mac_1,0),(self.cog_phy_1,0))
		self.connect((self.mac_1,1),(self.extras_datagram_to_stream_1,0))
		self.connect((self.extras_datagram_to_stream_1,0),(self.gr_file_sink_1,0))"""


def main():
	tb=top_block()
	tb.Run(True)
	#tb.start()
	#tb.cog_phy_1.print_param()
	#tb.cog_phy_0.print_param()
if __name__=="__main__":
	main()