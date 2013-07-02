import numpy
import gras
import time
from PMC import *
from math import pi

class probe(gras.Block):
	def __init__(self,fft_size,sense_B,secondary_B,freq_list,center_freq):
		gras.Block.__init__(self,name="fft_probe",
			in_sig = [numpy.dtype((numpy.float32,fft_size))],
            out_sig = None)
		
		self.fft_size=fft_size
		self.output=0.0
		self.freq_list=sorted(map(float,freq_list.split(',')))
		self.fft_step=float(sense_B)/fft_size
		self.secondary_samples=int(secondary_B/self.fft_step)
		self.cs_info=[0.0 for i in range(len(self.freq_list))]
		self.min_freq=center_freq-sense_B/2.0
		self.fft_avg=0.0
	def work(self,ins,outs):
		n=len(ins[0])
		#print "len",len(ins[0][0])
		for i in range(n):
			#decimation taking every 8th vector
			if(i%8!=0):
				continue
			st=0.0
			x=numpy.concatenate([ins[0][i][self.fft_size/2:],ins[0][i][0:self.fft_size/2]])
			'''for j in range(len(x)):
				print x[j]
			print "Next" '''

			for j in range(len(self.freq_list)):
				sample_no=int((self.freq_list[j]-self.min_freq)/self.fft_step)
				s_left=sample_no-self.secondary_samples/2
				s_right=sample_no+self.secondary_samples/2
				#print s_left,s_right,self.freq_list[j],self.secondary_samples,self.fft_step,self.min_freq
				if(s_left<0 or s_right>=len(x)):
					raise ValueError, "secondary frequency allocation is out of sense band "
				s=0.0
				for k in range(s_left,s_right+1):
					s+=x[k]
				self.cs_info[j]=s/self.secondary_samples
				st+=s
				#print self.freq_list[j],self.cs_info[j],s_left,s_right
			self.fft_avg=st/self.fft_size
				
		#print self.output

		self.consume(0,n)
	def level(self):
		return self.output
	def best_band(self , nid=-1):
		min_I=1e6
		fid=0
		for i in range(len(self.cs_info)):
			if(self.cs_info[i]<min_I and nid!=i):
				min_I=self.cs_info[i]
				fid=i

		return (fid,self.cs_info[fid])
	def worst_band(self,nid=-1):
		max_I=1e-9
		fid=0
		for i in range(len(self.cs_info)):
			if(self.cs_info[i]>max_I and nid!=i):
				max_I=self.cs_info[i]
				fid=i
		return (fid,self.cs_info[fid])
	def print_cs_info(self):
		print "CS Info :"
		for i in range(len(self.cs_info)):
			print self.freq_list[i],self.cs_info[i]
	def print_fft_avg(self):
		print "FFT avg :", self.fft_avg
