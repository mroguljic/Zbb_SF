import os
import sys
from pathlib import Path


iDir = sys.argv[1]
sample = sys.argv[2]
outDir = sys.argv[3]
wp     = sys.argv[4]

if("2016" in iDir):
    year=2016
if("2017" in iDir):
    year=2017
if("2018" in iDir):
    year=2018


variations = ["nom","jesUp","jesDown","jerUp","jerDown","jmsUp","jmsDown","jmrUp","jmrDown"]
for variation in variations:
    if("ptRwt" in variation and "TTbar" not in sample):
        continue
    if("pnet" in variation and "ZJets" not in sample):
        continue
    if(variation!="nom" and ("QCD" in sample or "JetHT" in sample)):
        continue           

    inputTag = variation

    inputFile = "{0}/{1}_{2}.root".format(iDir,sample,inputTag)
    outputFile = os.path.join(outDir,"nonScaled/",sample)
    outputFile = outputFile+".root"
    Path(outDir+"/nonScaled").mkdir(parents=True, exist_ok=True)
    Path(outDir+"/scaled").mkdir(parents=True, exist_ok=True)
    if(variation=="nom"):
        mode="RECREATE"
    else:
        mode="UPDATE"
    cmd = "python templateMaker.py -i {0} -o {1} -y {2} -p {3} -v {4} -m {5} -w {6}".format(inputFile,outputFile,year,sample,variation,mode,wp)
    print(cmd)
    os.system(cmd)
