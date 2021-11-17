import os
import sys
import os.path
from os import path
import ROOT as r
import time

def file_age(filepath):
    #last modification of file in days
    return (time.time() - os.path.getmtime(filepath))/(24*3600.)


def checkFile(fileName):
    if not path.exists(tempFileName):
        return False
    try:
        f = r.TFile.Open(tempFileName)
        tree = f.Get("Events")
        nEntries = tree.GetEntriesFast()
        if(nEntries<0):
            return False
        else:
            return True
    except:
        return False


targetDir = sys.argv[1]
samples         = os.listdir(targetDir)
verbose         = False
submit_cmds     = []
interactive_cmds= []
interactiveFlag = True #Whether to print commands to run interactively (true) or condor commands to rsb (false)
variations   = ["nom","jerUp","jerDown","jesUp","jesDown","jmsUp","jmsDown","jmrUp","jmrDown"]

for sample in samples:
    print(sample)

    toResubmit  = ""
    inputDir        = targetDir+"/"+sample+"/"+"input/"
    condorFile      = inputDir+"condor_{0}.condor".format(sample)
    argsFile        = inputDir+"args_{0}.txt".format(sample)
    argsFileBackup  = argsFile.replace(".txt","_ORIG.txt")

    if not(path.exists(argsFileBackup)):
        os.system("cp {0} {1}".format(argsFile,argsFileBackup))

    f = open(argsFileBackup,"r")
    args = f.readlines()
    for argSet in args:
        missingFileFlag = 0
        argArr  = argSet.split(" ")
        outputFile = argArr[3]
        for var in variations:
            if(var!="nom" and ("QCD" in sample or "JetHT" in sample)):
                continue
            tempFileName = outputFile.replace(".root","_{0}.root".format(var))
            if(checkFile(tempFileName) and file_age(tempFileName)<10.):
            #If files exists and younger than N days
                if(verbose):
                    print("Found ", tempFileName)
                continue
            else:
                if(verbose):
                    print("Missing: ", tempFileName)
                missingFileFlag = 1
                cmdToRun = "python eventSelection.py "+argSet.replace("\n","")+" --var {0}".format(var)
                interactive_cmds.append(cmdToRun)

        if missingFileFlag:
            toResubmit+=argSet

    f.close()
    if not interactiveFlag:
        f = open(argsFile,"w")
        f.write(toResubmit)
        if(toResubmit):
            submit_cmd = "condor_submit {0}".format(condorFile)
            submit_cmds.append(submit_cmd)

if(interactiveFlag):
    for cmd in interactive_cmds:
        print(cmd)
else:
    print("To resubmit: ")
    for submission in submit_cmds:
        print(submission)
