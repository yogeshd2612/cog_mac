#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Mon Jun 24 14:17:55 2013
##################################################

from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import grextras
import wx
import time
import spectrum_sense
import fft_probe

class top_block(grc_wxgui.top_block_gui):

	def __init__(self,options):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

				
		##################################################
		# Blocks
		##################################################
		self.uhd_usrp_source = uhd.usrp_source(
			device_addr=self.device_addr,
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
		self.uhd_usrp_source.set_samp_rate(options.sample_rate)
		self.uhd_usrp_source.set_center_freq(980e6, 0)
		self.uhd_usrp_source.set_gain(10, 0)
		self.uhd_usrp_source.set_antenna("RX2", 0)

		self.cs_0=spectrum_sense.pwrfft_c(options.sample_rate,options.fft_size,
								options.sample_rate/(options.fft_size*8),1,False)
		self.probe_0=fft_probe.probe(options.fft_size,options.sample_rate,options.ch_band,"977e6,978.5e6,980e6,981.5e6,983e6",options.freq)

		##################################################
		# Connections
		##################################################
		self.connect((self.uhd_usrp_source,0),(self.cs_0,0))
		self.connect((self.cs_0,0),(self.probe_0,0))

	
if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	parser.add_option("", "--args",default="",
	                  help="set the address of usrp_device [default='']")
	parser.add_option("","--sample_rate", type=int, default=int(8e6),
	                  help="set the sample_rate [default=8e6]")
	parser.add_option("","--freq", type=int, default=980e6,
	                  help="set the center_freq [default=980e6]")
	parser.add_option("","--fft_size", type=int, default=1024,
	                  help="set the fft_size size [default=1024]")
	parser.add_option("","--ch_band", type=int, default=1e6,
	                  help="set the channel bandwidth [default=1e6]")
	(options, args) = parser.parse_args()
	tb = top_block(options)
	#tb.Run(True)
	tb.start()
	while(1):
		tb.probe_0.print_cs_info()
		time.sleep(2)

