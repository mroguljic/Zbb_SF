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

def separateVHistos(analyzer,process,region,nomTreeFlag):
    cats = {
    "light" : "jetCat==1",
    "c"     : "jetCat==2",
    "b"     : "jetCat==3",
    "bc"     : "jetCat==3 || jetCat==2",
    "unm"   : "jetCat==0"}

    separatedHistos = []
    separatedGroups = []
    beforeNode = analyzer.GetActiveNode()
    for cat in cats:
        analyzer.SetActiveNode(beforeNode)
        analyzer.Cut("{0}_{1}_{2}_cut".format(process,cat,region),"{0}".format(cats[cat]))

        if nomTreeFlag:
            tplHist   = r.TH2F('{0}_{1}_m_pT_{2}'.format(process,cat,region),';mSD [GeV];pT [GeV];',160,40,200,155,450,2000)
            templates = analyzer.MakeTemplateHistos(tplHist,["mSD","FatJet_pt0"])
            separatedGroups.append(templates)
        else:
            #For jms/jmr/jes/jer trees, we don't need to calculate uncertainties on nominal trees
            hist = analyzer.DataFrame.Histo2D(('{0}_{1}_m_pT_{2}'.format(process,cat,region),';mSD [GeV];pT [GeV];',160,40,200,155,450,2000),"mSD","FatJet_pt0","weight__nominal")
            separatedHistos.append(hist)

        hVpt = analyzer.DataFrame.Histo1D(('{0}_{1}_VpT_{2}'.format(process,cat,region),';V pT [GeV];;',200,0,2000),"genVpt","weight__nominal")
        separatedHistos.append(hVpt)

    analyzer.SetActiveNode(beforeNode)
    return separatedHistos,separatedGroups

def getTaggingEfficiencies(analyzer,wpL,wpT,jetCat=3):
    beforeNode = analyzer.GetActiveNode()
    analyzer.Cut("jetCat_{0}_forEff".format(jetCat),"jetCat=={0}".format(jetCat))
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    analyzer.Cut("Eff_L_{0}_cut".format(jetCat),"pnet0>{0} && pnet0<{1} && jetCat=={2}".format(wpL,wpT,jetCat))
    nL   = analyzer.DataFrame.Sum("genWeight").GetValue()
    analyzer.SetActiveNode(beforeNode)
    analyzer.Cut("Eff_T_{0}_cut".format(jetCat),"pnet0>{0} && jetCat=={1}".format(wpT,jetCat))
    nT   = analyzer.DataFrame.Sum("genWeight").GetValue()
    effL = nL/(nTot+0.000001)#Avoid division by zero
    effT = nT/(nTot+0.000001)
    analyzer.SetActiveNode(beforeNode)
    return effL, effT


def getNCut(analyzer,cut,cutName):
    beforeNode = analyzer.GetActiveNode()
    analyzer.Cut(cutName,cut)
    nCut = analyzer.DataFrame.Sum("genWeight").GetValue()
    analyzer.SetActiveNode(beforeNode)
    return nCut

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


if "nom" in iFile and "pnet" not in variation:
    #Pnet variations have to be ran on nominal trees, but no need to calculate all unc. on nom trees
    nomTreeFlag = True
else:
    nomTreeFlag = False

a = analyzer(iFile)
pnetT   = options.wps[1]
pnetL   = options.wps[0]
year    = options.year
histos=[]
histGroups=[]

if("data" in options.process.lower() or "jetht" in options.process.lower()):
    isData=True
else:
    isData=False


if isData:
    a.Define("genWeight","1")
genWCorr    = Correction('genW',"TIMBER/Framework/ZbbSF/BranchCorrection.cc",corrtype='corr')
a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})

if not isData:
    trigFile   = "data/trig_eff_2016.root"
    a.Define("pt_for_trig","TMath::Min(Double_t(FatJet_pt0),999.)")#Trigger eff, measured up to 1000 GeV (well withing 100% eff. regime)
    triggerCorr = Correction('trig',"TIMBER/Framework/src/EffLoader.cc",constructor=['"{0}"'.format(trigFile),'"trig_eff"'],corrtype='weight')
    a.AddCorrection(triggerCorr, evalArgs={'xval':'pt_for_trig','yval':0,'zval':0})
    puCorr      = Correction('puRwt',"TIMBER/Framework/src/puWeight.cc",constructor=['"../TIMBER/TIMBER/data/pileup/PUweights_{0}.root"'.format(year)],corrtype='weight')
    a.AddCorrection(puCorr, evalArgs={'puTrue':'Pileup_nTrueInt'})

    if("TTbar" in options.process):
        ptrwtCorr = Correction('ptRwt',"TIMBER/Framework/src/TopPt_reweighting.cc",corrtype='weight')
        a.AddCorrection(ptrwtCorr, evalArgs={'genTPt':'topPt','genTbarPt':'antitopPt'})
    if("WJets" in options.process):
        qcdName     = "QCD_W_16"
        ewkName     = "EWK_W_nominal"
        uncPrefix   = "unc_EWK_W"
        nloSyst     = ["d1K_NLO","d2K_NLO","d1kappa_EW","W_d2kappa_EW","W_d3kappa_EW"]
    if("ZJets" in options.process):
        qcdName     = "QCD_Z_16"
        ewkName     = "EWK_Z_nominal"
        uncPrefix   = "unc_EWK_Z"
        nloSyst     = ["d1K_NLO","d2K_NLO","d3K_NLO","d1kappa_EW","Z_d2kappa_EW","Z_d3kappa_EW"]
    if("WJets" in options.process or "ZJets" in options.process):
        NLOfile     = "data/NLO_corrections.root"
        a.Define("genVpt_rescaled","TMath::Max(300.,TMath::Min(Double_t(genVpt),3000.))")#Weights applied in 300-3000 GeV gen V pt range
        NLOqcdCorr = Correction('qcd_nlo',"TIMBER/Framework/src/HistLoader.cc",constructor=['"{0}","{1}"'.format(NLOfile,qcdName)],corrtype='corr')
        NLOewkCorr = Correction('ewk_nlo',"TIMBER/Framework/src/HistLoader.cc",constructor=['"{0}","{1}"'.format(NLOfile,ewkName)],corrtype='corr')
        a.AddCorrection(NLOqcdCorr, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})
        a.AddCorrection(NLOewkCorr, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})

        if nomTreeFlag:
            for syst in nloSyst:
                uncUp      = uncPrefix+"_"+syst+"_up"
                uncDown    = uncPrefix+"_"+syst+"_down"
                print(NLOfile,uncUp,uncDown)
                nloSystUnc = Correction(syst,"TIMBER/Framework/ZbbSF/UncLoader.cc",constructor=['"{0}","{1}","{2}"'.format(NLOfile,uncUp,uncDown)],corrtype='uncert')
                a.AddCorrection(nloSystUnc, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})

a.MakeWeightCols()


CompileCpp('TIMBER/Framework/ZbbSF/btagSFHandler.cc')
if(variation=="pnetUp"):
    pnetVar=2
elif(variation=="pnetDown"):
    pnetVar=1
else:
    pnetVar = 0

CompileCpp('btagSFHandler btagHandler = btagSFHandler({%f,%f},%s,%i);' %(pnetL,pnetT,year,pnetVar))#wps, year, var
a.Define("TaggerCat","btagHandler.createTaggingCategories(pnet0)")

if("ZJets" in options.process):
    #Only apply SF to Z jets (Z->bb and Z->cc)
    eff_bb_L, eff_bb_T = getTaggingEfficiencies(a,pnetL,pnetT,jetCat=3)#calculate efficiencies for Z->bb
    eff_cc_L, eff_cc_T = getTaggingEfficiencies(a,pnetL,pnetT,jetCat=2)#calculate efficiencies for Z->cc
    print("ParticleNet (L,T) bb-efficiencies: ({0:.2f},{1:.2f})".format(eff_bb_L,eff_bb_T))
    print("ParticleNet (L,T) cc-mistag: ({0:.2f},{1:.2f})".format(eff_cc_L,eff_cc_T))

    a.Define("eff_L","jetCat==3 ? {0} : {1}".format(eff_bb_L,eff_cc_L))
    a.Define("eff_T","jetCat==3 ? {0} : {1}".format(eff_bb_T,eff_cc_T))
    a.Define("jetFlav","jetCat+2")
    #a.Define("scaledPnet","btagHandler.updateTaggingCategories(TaggerCat,FatJet_pt0,jetFlav,{float(eff_L),float(eff_T)})") #Uncomment if we want to apply btag SF
    a.Define("scaledPnet","TaggerCat")#Don't apply btag sf
else:
    a.Define("scaledPnet","TaggerCat")

regionDefs = [("T","scaledPnet==2"),("L","scaledPnet==1"),("F","scaledPnet==0"),("I","pnet0>-1")]
regionYields = {}

for region,cut in regionDefs:
    a.Define(region,cut)

checkpoint = a.GetActiveNode()

for region,cut in regionDefs:
    a.SetActiveNode(checkpoint)
    a.Cut("{0}_cut".format(region),cut)

    if("ZJets" in options.process or "WJets" in options.process):
        categorizedHistos, categorizedGroups = separateVHistos(a,options.process,region,nomTreeFlag)
        histos.extend(categorizedHistos)
        histGroups.extend(categorizedGroups)

    if("ZJets" in options.process or "WJets" in options.process):
        #For "inclusive flavour", still keep only jets matched to V
        a.Cut("{0}_matched_V_cut".format(region),"jetCat>0")

    if nomTreeFlag:
        tplHist   = r.TH2F('{0}_m_pT_{1}'.format(options.process,region),';mSD [GeV];pT [GeV];',160,40,200,155,450,2000)
        templates = a.MakeTemplateHistos(tplHist,["mSD","FatJet_pt0"])
        histGroups.append(templates)
    else:
        #For jms/jmr/jes/jer trees, we don't need to calculate uncertainties on nominal trees
        h2d = a.DataFrame.Histo2D(('{0}_m_pT_{1}'.format(options.process,region),';mSD [GeV];pT [GeV];',160,40,200,155,450,2000),"mSD","FatJet_pt0","weight__nominal")
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

for hGroup in histGroups:
    hGroup.Do("Write")

out_f.Close()

#a.PrintNodeTree('test.ps')
