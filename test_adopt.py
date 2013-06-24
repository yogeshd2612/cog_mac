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
import adopt_demo

class top_block(grc_wxgui.top_block_gui):

	def __init__(self,options):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

		##################################################
		# Variables
		##################################################
		self.samp_rate = samp_rate = 500000

		##################################################
		# Blocks
		##################################################
		self.uhd_usrp_sink_0 = uhd.usrp_sink(
			device_addr=options.args,
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
		self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
		self.uhd_usrp_sink_0.set_center_freq(990e6, 0)
		self.uhd_usrp_sink_0.set_gain(10, 0)
		self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
		self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 1000, 1, 0)
		self.extras_uhd_control_port_0 = grextras.UHDControlPort(options.args)
		self.sniff_0=adopt_demo.sniff(options.args,self.extras_uhd_control_port_0,self.uhd_usrp_sink_0)
		
		self.sniff_0.adopt_element("uhd_control",self.extras_uhd_control_port_0.to_element())

		##################################################
		# Connections
		##################################################
		self.connect((self.analog_sig_source_x_0, 0), (self.sniff_0, 0))
		self.connect((self.sniff_0,0),(self.uhd_usrp_sink_0,0))


	def get_samp_rate(self):
		return self.samp_rate

	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate
		self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
		self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	parser.add_option("", "--args",default="",
	                  help="set the address of usrp_device [default='']")
	(options, args) = parser.parse_args()
	tb = top_block(options)
	#tb.Run(True)
	tb.start()
	while(1):
		print "freq : ",tb.uhd_usrp_sink_0.get_center_freq()
		time.sleep(2)

