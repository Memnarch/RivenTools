import subprocess
import sys
import vapoursynth as vs
from vapoursynth import core
from vsbasicvsrpp import BasicVSRPP

CFFMPEG = "E:\\CustomMyst\\ffmpeg\\bin\\ffmpeg.exe";

def extractAudio(videoFile, audioFile):
	subprocess.run([CFFMPEG, "-i", videoFile, "-vn", "-acodec", "copy", audioFile]);
	#subprocess.run([CFFMPEG, "-i", videoFile, "-vn", "-acodec", "pcm_s16le", "-f", "s16le", audioFile]);
	
def mergeAudio(videoIn, audioIn, videoOut):
	subprocess.run([CFFMPEG, "-i", videoIn, "-i", audioIn, "-c:v", "libx264", "-video_track_timescale", "30", "-c:a", "copy", videoOut])

def openVideo(fileName):
	return core.ffms2.Source(source=fileName, format=2000015) #pfRGBS
	
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
	return BasicVSRPP(clip=ret, model=1, interval=30, fp16=True)
	
def processVideo(inputFile, outputFile):
	ret = openVideo(original)
	ret = core.resize.Bicubic(ret, ret.width*2, ret.height*2)
	ret = deblock(ret);
	ret = core.resize.Bicubic(ret, ret.width/2, ret.height/2)
	ret = deblock(ret)
	ret = upscale(ret)
	ret = toYUV(ret)
	saveVideo(ret, "D:\\ScaledVideos\\Test7.mov")

original = "E:\\CustomMyst\\Sources\\t_data-1-mhk\\55_tmgtm2jg.mov"
#extractAudio(original, "Audio.aiff")
mergeAudio("D:\\ScaledVideos\\Test7.y4m", "Audio.aif", "Foo.mov")
