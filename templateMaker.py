#To be used with trees from event selection
import ROOT as r
import time, os
import sys
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Tools.Common import *
from TIMBER.Analyzer import *

def getNweighted(analyzer,isData):
    if not isData:
        nWeighted = analyzer.DataFrame.Sum("genWeight").GetValue()
    else:
        nWeighted = analyzer.DataFrame.Count().GetValue()
    return nWeighted

parser = OptionParser()

parser.add_option('-i', '--input', metavar='IFILE', type='string', action='store',
                default   =   '',
                dest      =   'input',
                help      =   'A root file to analyze')
parser.add_option('-o', '--output', metavar='OFILE', type='string', action='store',
                default   =   'output.root',
                dest      =   'output',
                help      =   'Output file name.')
parser.add_option('-y', '--year', metavar='year', type='string', action='store',
                default   =   '2016',
                dest      =   'year',
                help      =   'Dataset year')
parser.add_option('-p', '--process', metavar='PROCESS', type='string', action='store',
                default   =   'X1600_Y100',
                dest      =   'process',
                help      =   'Process in the given file')
parser.add_option('-v','--var', metavar='variation', type='string', action='store',
                default   =   "nom",
                dest      =   'variation',
                help      =   'jer, jes, jmr, jms, trigger, etc + Up/Down')
parser.add_option('-m', metavar='mode', type='string', action='store',
                default   =   "RECREATE",
                dest      =   'mode',
                help      =   'RECREATE or UPDATE outputfile')
parser.add_option('-w', '--wp', metavar='working points',nargs=2, action="store", type=float,
                default   =   (0.94,0.98),
                dest      =   'wps',
                help      =   'Loose and tight working points')


(options, args) = parser.parse_args()
variation = options.variation
iFile = options.input
if not variation in iFile:
    if("je" in variation or "jm" in variation):
        iFile = iFile.replace(".root","_{0}.root".format(variation))
        print("{0} not in {1}, swapping input to {2}".format(variation,options.input,iFile))
    else:
        if not("nom" in iFile):
            iFile = iFile.replace(".root","_nom.root")

a = analyzer(iFile)
pnetT   = options.wps[1]
pnetL   = options.wps[0]
year    = options.year
histos=[]

if("data" in options.process.lower() or "jetht" in options.process.lower()):
    isData=True
else:
    isData=False

if not isData:
    # triggerCorr = Correction('triggerCorrection',"TIMBER/Framework/src/EffLoader.cc",constructor=['"../TIMBER/TIMBER/data/TriggerEffs/TriggerEffs.root"','"triggEff_{0}"'.format(year)],corrtype='weight')
    # a.AddCorrection(triggerCorr, evalArgs={'xval':'MJJ','yval':0,'zval':0})
    puCorr      = Correction('puReweighting',"TIMBER/Framework/src/puWeight.cc",constructor=['"../TIMBER/TIMBER/data/pileup/PUweights_{0}.root"'.format(year)],corrtype='weight')
    a.AddCorrection(puCorr, evalArgs={'puTrue':'Pileup_nTrueInt'})
    if("TTbar" in options.process):
        ptrwtCorr = Correction('topPtReweighting',"TIMBER/Framework/src/TopPt_reweighting.cc",corrtype='weight')
        a.AddCorrection(ptrwtCorr, evalArgs={'genTPt':'topPt','genTbarPt':'antitopPt'})

if isData:
    a.Define("genWeight","1")


a.MakeWeightCols()
weightString = "weight__nominal"
if("trig" in variation):
    if(variation=="trigUp"):
        weightString = "weight__triggerCorrection_up"
    if(variation=="trigDown"):
        weightString = "weight__triggerCorrection_down"
if("ptRwt" in variation):
    if(variation=="ptRwtUp"):
        weightString = "weight__topPtReweighting_up"
    if(variation=="ptRwtDown"):
        weightString = "weight__topPtReweighting_down"
if("puRwt" in variation):
    if(variation=="puRwtUp"):
        weightString = "weight__puReweighting_up"
    if(variation=="puRwtDown"):
        weightString = "weight__puReweighting_down"

if(year=="2018"):
    weightString+="*HEMweight"

a.Define("evtWeight","genWeight*{0}".format(weightString))

regionDefs = [("T","pnet0>{0}".format(pnetT)),("L","pnet0>{0} && pnet0<{1}".format(pnetL,pnetT)),("F","pnet0<{0}".format(pnetL))]
regionYields = {}

for region,cut in regionDefs:
    a.Define(region,cut)

checkpoint = a.GetActiveNode()

for region,cut in regionDefs:
    a.SetActiveNode(checkpoint)
    a.Cut("{0}_cut".format(region),cut)
    h2d = a.DataFrame.Histo2D(('{0}_m_pT_{1}'.format(options.process,region),';mSD [GeV];pT [GeV];',160,40,200,155,450,2000),"mSD","FatJet_pt0","evtWeight")
    histos.append(h2d)
    regionYields[region] = getNweighted(a,isData)

#include histos from evt sel in the template file for nominal template
if(options.variation=="nom"):
    in_f = ROOT.TFile(iFile)
    for key in in_f.GetListOfKeys():
        h = key.ReadObj()
        hName = h.GetName()
        if(hName=="Events"):
            continue
        h.SetDirectory(0)
        if("cutflow" in hName.lower()):
            h.SetBinContent(h.GetNbinsX(),regionYields["F"])
            h.SetBinContent(h.GetNbinsX()-1,regionYields["L"])
            h.SetBinContent(h.GetNbinsX()-2,regionYields["T"])
        histos.append(h)

out_f = ROOT.TFile(options.output,options.mode)
out_f.cd()
for h in histos:
    h.SetName(h.GetName()+"_"+options.variation)
    h.Write()
out_f.Close()

#a.PrintNodeTree('test.ps')
