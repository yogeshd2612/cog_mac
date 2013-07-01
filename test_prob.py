#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Sun Jun 23 21:45:37 2013
##################################################

from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio import window
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from gnuradio.wxgui import fftsink2
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import wx
import probe
import time

class top_block(grc_wxgui.top_block_gui):

	def __init__(self):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

		##################################################
		# Variables
		##################################################
		self.samp_rate = samp_rate = 100e3

		##################################################
		# Blocks
		##################################################
		self.wxgui_fftsink2_0 = fftsink2.fft_sink_c(
			self.GetWin(),
			baseband_freq=990e6,
			y_per_div=10,
			y_divs=10,
			ref_level=0,
			ref_scale=2.0,
			sample_rate=samp_rate,
			fft_size=1024,
			fft_rate=15,
			average=False,
			avg_alpha=None,
			title="FFT Plot",
			peak_hold=False,
		)
		self.Add(self.wxgui_fftsink2_0.win)
		self.uhd_usrp_source_0 = uhd.usrp_source(
			device_addr="addr=10.32.19.159",
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
		self.uhd_usrp_source_0.set_samp_rate(samp_rate)
		self.uhd_usrp_source_0.set_center_freq(990e6, 0)
		self.uhd_usrp_source_0.set_gain(10, 0)
		self.uhd_usrp_source_0.set_antenna("RX2", 0)
		#self.analog_probe_avg_mag_sqrd_x_1 = analog.probe_avg_mag_sqrd_c(0, 0.5)
		self.probe_0=probe.probe(0,0.9)
		##################################################
		# Connections
		##################################################
		#self.connect((self.uhd_usrp_source_0, 0), (self.wxgui_fftsink2_0, 0))
		self.connect((self.uhd_usrp_source_0, 0), (self.probe_0, 0))


	def get_samp_rate(self):
		return self.samp_rate

	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate
		self.wxgui_fftsink2_0.set_sample_rate(self.samp_rate)
		self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	(options, args) = parser.parse_args()
	tb = top_block()
	#tb.Run(True)
	tb.start()
	while(1):
		print tb.probe_0.get("level")
		time.sleep(1)

	

