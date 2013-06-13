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
class top_block(grc_wxgui.top_block_gui):

	def __init__(self):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))
		self.cog_phy=phy.cog_phy("addr=10.32.19.156")

		self.gr_file_source_0 = gr.file_source(gr.sizeof_char*1, "/home/electron/project/exp/block_creation/testfile1", True)
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_char*1, "/home/electron/project/exp/block_creation/testOutput")
		self.gr_file_sink_0.set_unbuffered(True)
		self.extras_stream_to_datagram_0 = grextras.Stream2Datagram(1, 256)
		self.extras_datagram_to_stream_0 = grextras.Datagram2Stream(1)

		##################################################
		# Connections
		##################################################
		self.connect((self.gr_file_source_0, 0), (self.extras_stream_to_datagram_0, 0))
		self.connect((self.extras_stream_to_datagram_0,0),(self.cog_phy,0))
		self.connect((self.cog_phy,0),(self.extras_datagram_to_stream_0,0))
		self.connect((self.extras_datagram_to_stream_0,0),(self.gr_file_sink_0,0))
def main():
	tb=top_block()
	tb.Run(True)
if __name__=="__main__":
	main()