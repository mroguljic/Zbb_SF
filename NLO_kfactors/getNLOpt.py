import ROOT

import time, os
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Tools.Common import *
from TIMBER.Analyzer import *
import sys
import subprocess

def generateInput(dataset,inputFile,nFiles=-1):
    if dataset.split('/')[-1] == "USER":
        instance = 'prod/phys03'
    else:
        instance = 'prod/global'

    query = "dasgoclient -query='file dataset={dataset} instance={instance}'".format(**locals())    
    files = subprocess.check_output(query, shell=True).split()
    
    allFiles = []
    for file in files:
          allFiles.append(file.decode("utf-8"))

    open(inputFile, 'w').writelines("{}\n".format('root://cms-xrd-global.cern.ch//'+root_file) for root_file in allFiles[:nFiles])

def getXsec(process,year):
    json_file = open("../xsecs.json")
    config = json.load(json_file)
    xsec    = config[year][process]["xsec"]
    return xsec

def run(inputFile,outputFile,process,year,nToRun=-1):

    start_time = time.time()
    xsec = getXsec(process,year)
    lumi = 1000.0 #pb-1

    a = analyzer(inputFile)

    if(nToRun!=-1):
        small_rdf = a.GetActiveNode().DataFrame.Range(nToRun)
        small_node = Node('small',small_rdf)
        a.SetActiveNode(small_node)
    histos      = []

    nProc       = a.DataFrame.Count().GetValue()
    nGenWeight  = a.DataFrame.Sum("genWeight").GetValue()
    print(year, process)

    if(nProc!=nToRun and nToRun!=-1):
        print("nProc ({0}) !=nToRun ({1})".format(nProc,nToRun))
    else:
        print("nProc = {0}".format(nProc))

    lumiWeight = xsec*lumi/nGenWeight

    if("ZJets" in process):
        tag = "ZJets"
    elif("DY" in process):
        tag = "DYJetsToLL"
    elif("JetsToLNu" in process):
        tag = "WJetsToLNu"
    elif("WJets" in process):
        tag = "WJets" 
    else:
        print("UNKNOWN PROCESS, WILL CRASH")

    a.Define("evtWeight","{0}*genWeight".format(lumiWeight))
    a.Define("genVpt","genVpt(nGenPart,GenPart_pdgId,GenPart_pt,GenPart_statusFlags)")
    hvPt = a.GetActiveNode().DataFrame.Histo1D(('{0}_{1}_gen_V_pT'.format(tag,year),';Gen V pT [GeV]; Events/10 GeV;',180,200,2000),"genVpt","evtWeight")
    histos.append(hvPt)



    out_f = ROOT.TFile(outputFile,"RECREATE")
    out_f.cd()
    for h in histos:
        h.Write()
    out_f.Close()

    small_node.Close()
    a.Close()


    #a.PrintNodeTree('node_tree.dot',verbose=True)
    print("Total time: "+str((time.time()-start_time)/60.) + ' min')



runConfig = {
"2016":{
    "ZJets400":"/ZJetsToQQ_HT400to600_qc19_4j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v1-44377faedc969dcf531f5eb3e501054b/USER",
    "ZJets600":"/ZJetsToQQ_HT600to800_qc19_4j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v1-44377faedc969dcf531f5eb3e501054b/USER",
    "ZJets800":"/ZJetsToQQ_HT-800toInf_qc19_4j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v2-44377faedc969dcf531f5eb3e501054b/USER",
    "WJets400":"/WJetsToQQ_HT400to600_qc19_3j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v1-44377faedc969dcf531f5eb3e501054b/USER",
    "WJets600":"/WJetsToQQ_HT600to800_qc19_3j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v1-44377faedc969dcf531f5eb3e501054b/USER",
    "WJets800":"/WJetsToQQ_HT-800toInf_qc19_3j_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/bortigno-NanoTuples-30Apr2020_RunIISummer16MiniAODv3-PUMoriond17_94X_v3-v1-44377faedc969dcf531f5eb3e501054b/USER",
    "DY1JetsToLL150":"/DY1JetsToLL_M-50_LHEZpT_150-250_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DY1JetsToLL250":"/DY1JetsToLL_M-50_LHEZpT_250-400_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DY1JetsToLL400":"/DY1JetsToLL_M-50_LHEZpT_400-inf_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DY2JetsToLL150":"/DY2JetsToLL_M-50_LHEZpT_150-250_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DY2JetsToLL250":"/DY2JetsToLL_M-50_LHEZpT_250-400_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DY2JetsToLL400":"/DY2JetsToLL_M-50_LHEZpT_400-inf_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W1JetsToLNu150":"/W1JetsToLNu_LHEWpT_150-250_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W1JetsToLNu250":"/W1JetsToLNu_LHEWpT_250-400_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W1JetsToLNu400":"/W1JetsToLNu_LHEWpT_400-inf_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W2JetsToLNu150":"/W2JetsToLNu_LHEWpT_150-250_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W2JetsToLNu250":"/W2JetsToLNu_LHEWpT_250-400_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM",
    "W2JetsToLNu400":"/W2JetsToLNu_LHEWpT_400-inf_TuneCP5_13TeV-amcnloFXFX-pythia8/RunIIFall17NanoAODv7-PU2017_12Apr2018_Nano02Apr2020_102X_mc2017_realistic_v8-v1/NANOAODSIM"
    },
"2017":{
    "ZJets400":"/ZJetsToQQ_HT-400to600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "ZJets600":"/ZJetsToQQ_HT-600to800_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "ZJets800":"/ZJetsToQQ_HT-800toInf_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJets400":"/WJetsToQQ_HT-400to600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJets600":"/WJetsToQQ_HT-600to800_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJets800":"/WJetsToQQ_HT-800toInf_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DYJetsToLL100":"/DYJetsToLL_Pt-100To250_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DYJetsToLL250":"/DYJetsToLL_Pt-250To400_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DYJetsToLL400":"/DYJetsToLL_Pt-400To650_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "DYJetsToLL650":"/DYJetsToLL_Pt-650ToInf_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJetsToLNu100":"/WJetsToLNu_Pt-100To250_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJetsToLNu250":"/WJetsToLNu_Pt-250To400_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJetsToLNu400":"/WJetsToLNu_Pt-400To600_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    "WJetsToLNu600":"/WJetsToLNu_Pt-600ToInf_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM",
    }
}

    
CompileCpp("TIMBER/Framework/common.cc") 
CompileCpp("TIMBER/Framework/deltaRMatching.cc") 
CompileCpp("TIMBER/Framework/helperFunctions.cc") 
CompileCpp("TIMBER/Framework/ZbbSF/Zbb_Functions.cc") 


year = sys.argv[1]#Which year to run
procTag = sys.argv[2]#process string to match, e.g. ZJets will run all *ZJets* samples


if(year=="2016"):
    nFiles = 10#NanoTuples have less events / file
else:
    nFiles = 3
for proc in runConfig[year]:
    if not procTag in proc:
        continue
    inputFile   = "input/{0}_{1}.txt".format(year,proc)
    generateInput(runConfig[year][proc],inputFile,nFiles=nFiles)
    outputFile  = "{0}_{1}.root".format(proc,year)
    run(inputFile,outputFile,proc,year,nToRun=1000000)
    print("----------------------")


# haddCmd = "hadd -f NLOcheck.root *201*root"
# mvCmd   = "mv *201*root rootFiles"
# os.system(haddCmd)
# os.system(mvCmd)
