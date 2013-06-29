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

class cog_phy(gras.HierBlock):
	def __init__(self,device_addr="",samp_rate_rx=int(1e6),samp_rate_tx=int(1e6),center_freq=int(990e6),
		tx_A="TX/RX",rx_A="RX2",tx_gain=15,rx_gain=0,sps=2,bps=1,access_code=""):
		gras.HierBlock.__init__(self,"cog_phy")
		#
		self.device_addr=device_addr
		self.tx_A=tx_A
		self.rx_A=rx_A
		self.tx_gain=tx_gain
		self.rx_gain=rx_gain
		self.center_freq=center_freq
		self.sps=sps
		self.bps=bps
		self.access_code=access_code
		# usrp source/sinks

		self.uhd_usrp_source = uhd.usrp_source(
			device_addr=self.device_addr,
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
		self.uhd_usrp_source.set_samp_rate(samp_rate_rx)
		self.uhd_usrp_source.set_center_freq(center_freq, 0)
		self.uhd_usrp_source.set_gain(rx_gain, 0)
		self.uhd_usrp_source.set_antenna(rx_A, 0)
		self.uhd_usrp_sink = uhd.usrp_sink(
			device_addr,
			stream_args=uhd.stream_args(
				cpu_format="fc32",
				channels=range(1),
			),
		)
		self.uhd_usrp_sink.set_samp_rate(samp_rate_tx)
		self.uhd_usrp_sink.set_center_freq(center_freq, 0)
		self.uhd_usrp_sink.set_gain(tx_gain, 0)
		self.uhd_usrp_sink.set_antenna(tx_A, 0)

		# packet framer/deframer

		self.extras_packet_framer = grextras.PacketFramer(
		    samples_per_symbol=1,
		    bits_per_symbol=1,
		    access_code=self.access_code,
		)
		self.extras_packet_deframer = grextras.PacketDeframer(
		    access_code=self.access_code,
		    threshold=-1,
		)

		# Modulator/Demodulator

		self.digital_gmsk_mod = digital.gmsk_mod(
			samples_per_symbol=self.sps,
			bt=0.35,
			verbose=False,
			log=False,
		)
		self.digital_gmsk_demod = digital.gmsk_demod(
			samples_per_symbol=self.sps,
			gain_mu=0.175,
			mu=0.5,
			omega_relative_limit=0.005,
			freq_error=0.0,
			verbose=False,
			log=False,
		)

		
		self.gr_multiply_const_vxx_0 = gr.multiply_const_vcc((0.3, ))
		self.extras_burst_tagger_0 = grextras.BurstTagger(self.sps)
		##################################################
		# Connections
		##################################################
		#RX chain
		self.connect((self.uhd_usrp_source, 0), (self.digital_gmsk_demod, 0))
		self.connect((self.digital_gmsk_demod, 0), (self.extras_packet_deframer, 0))
		self.connect((self.extras_packet_deframer, 0), (self,0))
		#TX chain		
		self.connect((self,0),((self.extras_packet_framer, 0)))
		self.connect((self.extras_packet_framer, 0), (self.digital_gmsk_mod, 0))
		self.connect((self.digital_gmsk_mod, 0), (self.gr_multiply_const_vxx_0,0))
		self.connect((self.gr_multiply_const_vxx_0,0),(self.extras_burst_tagger_0,0))
		self.connect((self.extras_burst_tagger_0,0),(self.uhd_usrp_sink, 0))
		#probe to demodulated values for tag collection
		self.connect((self.uhd_usrp_source,0),(self,1))
		

	

	def print_param(self):
		print "Parameters :"
		print "Device_addr : ",self.device_addr
		print " Transmitting Antenna : ",self.tx_A
		print "Receiving Antenna : ",self.rx_A
		print "Trasmitting Antenna gain : ",self.tx_gain
		print "Receiving Antenna gain : ",self.rx_gain
		print "Freq of operation : ",self.center_freq
		print "Sample per symbol : ",self.sps
		print "Bits per symbol : ",self.bps
		print "Access code (framer): ",self.access_code


