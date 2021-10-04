import Scaler
import os

CSourceDir = "G:\\Sources"
CTargetDir = "G:\\Targets"

counter = 0;
for dir in os.listdir(CSourceDir):
	if os.path.isdir(os.path.join(CSourceDir, dir)):
		SourceDir = os.path.join(CSourceDir, dir)
		TargetDir = os.path.join(CTargetDir, dir)
		if not os.path.exists(TargetDir):
			os.mkdir(TargetDir)
		for file in os.listdir(SourceDir):
			if os.path.isfile(os.path.join(SourceDir, file)) and file.endswith(".mov"):
				counter = counter + 1
				print(counter)
				sourceFile = os.path.join(SourceDir, file)
				targetFile = os.path.join(TargetDir, file)
				if not os.path.exists(targetFile):
					Scaler.processVideo(sourceFile, targetFile)
				else:
					print("skipped cause target exists " + sourceFile)