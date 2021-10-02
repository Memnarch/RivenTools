import subprocess
import sys
import warnings
from torch.serialization import UserWarning
import vapoursynth as vs
from vapoursynth import core
from vsbasicvsrpp import BasicVSRPP

CFFMPEG = "E:\\CustomMyst\\ffmpeg\\bin\\ffmpeg.exe";
CTimings = "Timings.txt";
CAudio = "Audio.aiff";

def extractAudio(videoFile, audioFile):
	subprocess.run([CFFMPEG, "-y", "-i", videoFile, "-vn", "-acodec", "copy", audioFile]);
	
def mergeAudio(videoIn, audioIn, videoOut):
#"-vsync", "2", "-r", "14.639",
	subprocess.run([CFFMPEG, "-y", "-i", videoIn, "-i", audioIn, "-c:v", "libx264", "-crf", "17", "-c:a", "copy", videoOut])

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
	
def deblock(clip, batchSize = 30):
	return BasicVSRPP(clip=clip, model=5, interval=batchSize, fp16=True)
	
def upscale(clip):
	return BasicVSRPP(clip=clip, model=1, interval=30, fp16=True)
	
def processVideo(inputFile, outputFile):
	ret = openVideo(inputFile)
	ret = deblock(ret, 90)
	ret = core.resize.Bicubic(ret, ret.width*2, ret.height*2)
	ret = deblock(ret);
	ret = core.resize.Bicubic(ret, ret.width/2, ret.height/2)
	ret = deblock(ret, 90)
	ret = upscale(ret)
	ret = toYUV(ret)
	if ret.fps.denominator > 1:
		targetFPS = ret.fps.numerator / ret.fps.denominator * 2;
		print("VFR clip detected. Converting to " + str(targetFPS))
		ret = core.vfrtocfr.VFRToCFR(ret, CTimings, 30, 1)
	saveVideo(ret, outputFile)

original = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\55_tmgtm2jg.mov"
intro = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\159_tintro.mov"
temp = "G:\\ScaledVideos\\temp2.y4m"

warnings.filterwarnings("ignore", category=UserWarning)
processVideo(intro, temp)
extractAudio(intro, CAudio)
mergeAudio(temp, CAudio, "G:\\Intro2.mov")
