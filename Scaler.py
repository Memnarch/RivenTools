import subprocess
import sys
import warnings
from datetime import timedelta
import time
import math
import os
from vsrife import RIFE
from vsdpir import DPIR
import mvsfunc as mvf
import vapoursynth as vs
from vapoursynth import core
from vsbasicvsrpp import BasicVSRPP

CFFMPEG = "E:\\CustomMyst\\ffmpeg\\bin\\ffmpeg.exe";
CTimings = "Timings.txt";
CAudio = "Audio.aiff";

def GetLogFile():
	return open("ffmpeg.log", "w")

def extractAudio(videoFile, audioFile):
	print("extracting audio...")
	if os.path.exists(audioFile):
		os.remove(audioFile)
	subprocess.run([CFFMPEG, "-y", "-i", videoFile, "-vn", "-acodec", "copy", audioFile], stderr = GetLogFile());
	
def mergeAudio(videoIn, audioIn, videoOut):
	print("merging audio and compressing...")
	subprocess.run([CFFMPEG, "-y", "-i", videoIn, "-i", audioIn, "-c:v", "libx264", "-crf", "17", "-c:a", "copy", videoOut], stderr = GetLogFile())

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
	return BasicVSRPP(clip=clip, model=5, interval=batchSize, fp16=True, cpu_cache=False)
	
def upscale(clip):
	return BasicVSRPP(clip=clip, model=1, interval=30, fp16=False, cpu_cache=True)
	
def denoise(clip):
	#float[] lSigma = [3,3,3]
	lRadius = 2;
	src = core.bm3d.RGB2OPP(clip)
	ref = core.bm3d.VBasic(src, profile="lc", matrix=100).bm3d.VAggregate(radius=lRadius)
	flt = core.bm3d.VFinal(src, ref, profile="lc", matrix=100).bm3d.VAggregate(radius=lRadius)
	flt = core.bm3d.OPP2RGB(flt)
	return core.fmtc.bitdepth (clip=flt, flt=1)


	
def scaleVideo(inputFile, outputFile):
	ret = openVideo(inputFile)
	origWidth = ret.width;
	origHeight = ret.height;
	baseScale = 1;
	ret = core.resize.Bicubic(ret, origWidth*2, origHeight*2)
	ret = DPIR(ret, task="deblock")
	ret = deblock(ret)
	ret = core.resize.Bicubic(ret, origWidth, origHeight)
	#if size is to small, we upscale but don't downscale before upscale and just do a final downscale at the 
	"""
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
	if (origWidth >= 64) and (origHeight >= 64) and (baseScale > 1):
		ret = core.resize.Bicubic(ret, ret.width / baseScale, ret.height / baseScale)
		baseScale = 1
	ret = upscale(ret)
	if baseScale > 1:
		ret = core.resize.Bicubic(ret, ret.width / baseScale, ret.height / baseScale)
	if ret.fps.denominator > 1:
		targetFPS = ret.fps.numerator / ret.fps.denominator;
		print("VFR clip detected. Converting to " + str(targetFPS))
		ret = core.vfrtocfr.VFRToCFR(ret, CTimings, targetFPS, 1)
	#ret = RIFE(ret, fp16=True)
	"""
	
	ret = upscale(ret)
	ret = toYUV(ret)
	ret = core.asharp.ASharp(ret)
	saveVideo(ret, outputFile)

def processVideo(inputFile, outputFile):
	print("processing " + inputFile)
	timer = time.time()
	scaleVideo(inputFile, temp)
	extractAudio(inputFile, CAudio)
	mergeAudio(temp, CAudio, outputFile)
	endTimer = time.time()
	neededTime = timedelta(seconds=endTimer-timer)
	print("time needed: " + str(neededTime))
	print("finished " + outputFile)


original = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\55_tmgtm2jg.mov"
intro = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\159_tintro.mov"
temp = "G:\\ScaledVideos\\temp5.y4m"

warnings.filterwarnings("ignore", category=UserWarning)
#processVideo(original, temp)
#extractAudio(original, CAudio)
#mergeAudio(temp, CAudio, "G:\\Maglev.mov")
