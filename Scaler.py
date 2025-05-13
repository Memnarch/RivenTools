import subprocess
import sys
import warnings
from datetime import timedelta
import time
import math
import os
from vsrife import rife
from vsdpir import dpir
import vapoursynth as vs
from vapoursynth import core
from vsbasicvsrpp import basicvsrpp

CFFMPEG = "E:\\CustomMyst\\ffmpeg\\bin\\ffmpeg.exe";
CTimings = "Timings.txt";

CMaxGPUPixels = (608*2)*(392*2);
CMaxGPUPixelsForUpscale = (608*2)*(392*2);


#models
model_vsr_red = 0;
model_vsr_vimeoBI = 1;
model_vsr_vimeoBD = 2;
model_vsr_ntire = 3;
model_qec_ntire_t1 = 4;
model_qec_ntire_t2 = 5;
model_qec_ntire_t3 = 6;
model_deblur_dvd = 7;
model_deblur_gopro = 8;
model_denoise = 9;

def GetLogFile(suffix):
	return open(suffix + "-ffmpeg.log", "w")
	
def mergeAudio(videoIn, origVideo, videoOut):
	print("merging audio and compressing...")
	args = [CFFMPEG, "-y", "-i", videoIn, "-i", origVideo, "-map", "0:v", "-map", "1:a?", "-map", "-1:v", "-c:v", "libx264", "-crf", "17", "-video_track_timescale", "600", "-c:a", "copy", videoOut]
	subprocess.run(args, stderr = GetLogFile("merge"), check=True)

def openVideo(fileName):
	return core.ffms2.Source(source=fileName, format=2000015, timecodes=CTimings) #pfRGBS
	
def toYUV(clip):
	result = core.fmtc.bitdepth(clip=clip, bits=16, flt=0)
	result = core.fmtc.matrix(clip=result, mat="601", col_fam=vs.YUV, bits=16)
	result = core.fmtc.resample(clip=result, css="420")
	result = core.fmtc.bitdepth(clip=result, bits=8)
	return result
	
def toRGBS(clip):
	c = core.fmtc.resample (clip=clip, css="444")
	c = core.fmtc.matrix (clip=c, mat="601", col_fam=vs.RGB)
	return core.fmtc.bitdepth (clip=c, flt=1)

def printProgress(percent):
	print ("[%-20s] %d%%" % ('='*int(percent / 5), percent), end = '\r')


def reportProgress(currentFrame, totalFrames):
	printProgress(currentFrame/totalFrames*100)
	
def saveVideo(clip, fileName):
	f = open(fileName, "wb+")
	clip.set_output()
	clip.output(f, y4m=True, progress_update = reportProgress)
	f.close()
	print("")
	
def deblock(clip, batchSize = 30):
	cpumode = (clip.width*clip.height) > CMaxGPUPixels;
	print("Deblock with CPUCache: " + str(cpumode))
	return basicvsrpp(clip=clip, model=model_qec_ntire_t3, length=batchSize, cpu_cache=cpumode)
	
def upscale(clip):
	cpumode = (clip.width*clip.height) > CMaxGPUPixelsForUpscale;
	print("Upscale with CPUCache: " + str(cpumode))
	return basicvsrpp(clip=clip, model=model_vsr_vimeoBI, length=30, cpu_cache=cpumode)
	
def scaleVideo(inputFile, outputFile):
	ret = openVideo(inputFile)
	origWidth = ret.width;
	origHeight = ret.height;
	baseScale = 1;
	#if size is to small, we upscale but don't downscale before upscale and just do a final downscale at the end
	toLow = (ret.width < 256) or (ret.height < 256)
	if toLow:
		min = ret.width if ret.width < ret.height else ret.height 
		baseScale = math.ceil(256/min)
	print(origWidth)
	print(origHeight)
	ret = core.resize.Bicubic(ret, origWidth*baseScale*2, origHeight*baseScale*2)
	ret = deblock(ret, 60)
	ret = core.resize.Bicubic(ret, origWidth*baseScale, origHeight*baseScale)
	ret = deblock(ret, 60)
	if (origWidth >= 64) and (origHeight >= 64):
		ret = core.resize.Bicubic(ret, origWidth, origHeight)
		baseScale = 1
	ret = upscale(ret)
	if baseScale > 1:
		ret = core.resize.Bicubic(ret, origWidth*4, origHeight*4)
	if ret.fps.denominator > 1:
		targetFPS = ret.fps.numerator / ret.fps.denominator;
		print("VFR clip detected. Converting to " + str(targetFPS))
		ret = core.vfrtocfr.VFRToCFR(ret, CTimings, targetFPS, 1)
	#ret = RIFE(ret, fp16=True)
	ret = toYUV(ret)
	saveVideo(ret, outputFile)

def processVideo(inputFile, outputFile):
	print("processing " + inputFile)
	timer = time.time()
	tempFile = temp + os.path.basename(inputFile)
	scaleVideo(inputFile, tempFile)
	mergeAudio(tempFile, inputFile, outputFile)
	endTimer = time.time()
	neededTime = timedelta(seconds=endTimer-timer)
	print("time needed: " + str(neededTime))
	print("finished " + outputFile)


original = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\55_tmgtm2jg.mov"
intro = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\159_tintro.mov"
temp = "G:\\ScaledVideos\\"

warnings.filterwarnings("ignore", category=UserWarning)
