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

def separateVHistos(analyzer,process,region,nomTreeFlag,massVar):
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
            tplHist   = r.TH2F('{0}_{1}_m_pT_{2}'.format(process,cat,region),';{0} [GeV];pT [GeV];'.format(massVar),32,40,200,31,450,2000)
            templates = analyzer.MakeTemplateHistos(tplHist,[massVar,"FatJet_pt0"])
            separatedGroups.append(templates)
        else:
            #For jms/jmr/jes/jer trees, we don't need to calculate uncertainties on nominal trees
            hist = analyzer.DataFrame.Histo2D(('{0}_{1}_m_pT_{2}'.format(process,cat,region),';{0} [GeV];pT [GeV];'.format(massVar),32,40,200,31,450,2000),massVar,"FatJet_pt0","weight__nominal")
            separatedHistos.append(hist)

        hVpt = analyzer.DataFrame.Histo1D(('{0}_{1}_VpT_{2}'.format(process,cat,region),';V pT [GeV];;',200,0,2000),"genVpt","weight__nominal")
        separatedHistos.append(hVpt)

    analyzer.SetActiveNode(beforeNode)
    return separatedHistos,separatedGroups


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
                help      =   'nom; jer, jes, jmr, jms + Up/Down')
parser.add_option('-m', metavar='mode', type='string', action='store',
                default   =   "RECREATE",
                dest      =   'mode',
                help      =   'RECREATE or UPDATE outputfile')
parser.add_option('-w', '--wp', metavar='working point', action="append", type=float,
                default   =   [],
                dest      =   'wps',
                help      =   'Working point')


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


if "nom" in iFile:
    #Nominal tree processing will run all variations which do not require separate selection
    nomTreeFlag = True
else:
    nomTreeFlag = False


a = analyzer(iFile)
print(options.wps)
pnetWpUp   = options.wps[0]
pnetWpLo   = options.wps[1]
year    = options.year
histos=[]
histGroups=[]

massVar = "JetPnetMass"
#massVar = "JetSDMass"

if("data" in options.process.lower() or "jetht" in options.process.lower()):
    print("Running on data")
    isData=True
else:
    print("Running on MC")
    isData=False


if isData:
    a.Define("genWeight","1")
#Workaround to include genWeight into template maker
genWCorr    = Correction('genW',"TIMBER/Framework/Zbb_modules/BranchCorrection.cc",corrtype='corr',mainFunc='evalCorrection')

a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})



if not isData:
    pdfCorr     = genWCorr.Clone("pdfUnc",newMainFunc="evalUncert",newType="uncert")
    puCorr      = genWCorr.Clone("puUnc",newMainFunc="evalWeight",newType="weight")
    a.AddCorrection(pdfCorr, evalArgs={'valUp':'Pdfweight__up','valDown':'Pdfweight__down'})
    a.AddCorrection(puCorr, evalArgs={'val':'Pileup__nom','valUp':'Pileup__up','valDown':'Pileup__down'})

    if(year=="2018"):
        hemCorr = genWCorr.Clone("hemCorrection")
        a.AddCorrection(hemCorr, evalArgs={'val':'HEM_drop__nom'})
    if(year!="2018"):
        prefireCorr = genWCorr.Clone("prefireUnc",newMainFunc="evalWeight",newType="weight")
        a.AddCorrection(prefireCorr, evalArgs={'val':'Prefire__nom','valUp':'Prefire__up','valDown':'Prefire__down'})

    trigFile   = "data/trig_eff_{0}.root".format(year)
    a.Define("pt_for_trig","TMath::Min(Double_t(FatJet_pt0),999.)")#Trigger eff, measured up to 1000 GeV (well withing 100% eff. regime)
    triggerCorr = Correction('trig',"TIMBER/Framework/Zbb_modules/TrigEff.cc",constructor=["{0}".format(trigFile),"trig_eff"],corrtype='weight')
    a.AddCorrection(triggerCorr, evalArgs={'xval':'pt_for_trig','yval':0,'zval':0})

    if("WJets" in options.process):
        qcdName = "QCD_W"
        ewkName     = "EWK_W_nominal"
        uncPrefix   = "unc_EWK_W"
        nloSyst     = ["d1K_NLO","d2K_NLO","d1kappa_EW","W_d2kappa_EW","W_d3kappa_EW"]
    if("ZJets" in options.process):
        qcdName = "QCD_Z"
        ewkName     = "EWK_Z_nominal"
        uncPrefix   = "unc_EWK_Z"
        nloSyst     = ["d1K_NLO","d2K_NLO","d3K_NLO","d1kappa_EW","Z_d2kappa_EW","Z_d3kappa_EW"]
    if("WJets" in options.process or "ZJets" in options.process):
        NLOfile     = "data/NLO_corrections.root"
        a.Define("genVpt_rescaled","TMath::Max(200.,TMath::Min(Double_t(genVpt),1999.))")#Weights applied in 200-2000 GeV gen V pt range
        NLOqcdCorr = Correction('qcd_nlo',"TIMBER/Framework/src/HistLoader.cc",constructor=[NLOfile,qcdName],corrtype='corr')
        NLOewkCorr = Correction('ewk_nlo',"TIMBER/Framework/src/HistLoader.cc",constructor=[NLOfile,ewkName],corrtype='corr',isClone=True,cloneFuncInfo=NLOqcdCorr._funcInfo,isNewConstr=True)
        a.AddCorrection(NLOqcdCorr, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})
        a.AddCorrection(NLOewkCorr, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})

        if nomTreeFlag:
            parsedFlag      = False#Is correction script parsed by C++ compiler
            parsedFunc      = None
            for syst in nloSyst:
                uncUp      = uncPrefix+"_"+syst+"_up"
                uncDown    = uncPrefix+"_"+syst+"_down"
                print(NLOfile,uncUp,uncDown)
                nloSystUnc = Correction(syst,"TIMBER/Framework/Zbb_modules/UncLoader.cc",constructor=[NLOfile,uncUp,uncDown],corrtype='uncert',isClone=parsedFlag,cloneFuncInfo=parsedFunc,isNewConstr=parsedFlag)
                parsedFunc = nloSystUnc._funcInfo
                a.AddCorrection(nloSystUnc, evalArgs={'xval':'genVpt_rescaled','yval':0,'zval':0})
                parsedFlag = True

a.MakeWeightCols()

regionDefs = [("pass","pnet0<{0} && pnet0>{1}".format(pnetWpUp, pnetWpLo)),("fail","pnet0<{0}".format(pnetWpLo))]
regionYields = {}

for region,cut in regionDefs:
    a.Define(region,cut)

checkpoint = a.GetActiveNode()

for region,cut in regionDefs:
    a.SetActiveNode(checkpoint)
    a.Cut("{0}_cut".format(region),cut)

    if("ZJets" in options.process or "WJets" in options.process):
        categorizedHistos, categorizedGroups = separateVHistos(a,options.process,region,nomTreeFlag,massVar)
        histos.extend(categorizedHistos)
        histGroups.extend(categorizedGroups)

    if("ZJets" in options.process or "WJets" in options.process):
        #For "inclusive flavour", still keep only jets matched to V
        a.Cut("{0}_matched_V_cut".format(region),"jetCat>0")

    if nomTreeFlag:
        tplHist   = r.TH2F('{0}_m_pT_{1}'.format(options.process,region),';{0} [GeV];pT [GeV];'.format(massVar),32,40,200,31,450,2000)
        templates = a.MakeTemplateHistos(tplHist,[massVar,"FatJet_pt0"])
        histGroups.append(templates)
    else:
        #For jms/jmr/jes/jer trees, we don't need to calculate uncertainties on nominal trees
        h2d = a.DataFrame.Histo2D(('{0}_m_pT_{1}'.format(options.process,region),';{0} [GeV];pT [GeV];'.format(massVar),32,40,200,31,450,2000),massVar,"FatJet_pt0","weight__nominal")
        histos.append(h2d)

    regionYields[region] = getNweighted(a,isData)

#include histos from evt sel in the template file for nominal template
regionDefs = [("pass","pnet0<{0} && pnet0>{1}".format(pnetWpUp, pnetWpLo)),("fail","pnet0<{0}".format(pnetWpLo))]



if(options.variation=="nom"):
    in_f = ROOT.TFile(iFile)
    for key in in_f.GetListOfKeys():
        h = key.ReadObj()
        hName = h.GetName()
        if(hName=="Events"):
            continue
        h.SetDirectory(0)
        if("cutflow" in hName.lower()):
            h.SetBinContent(h.GetNbinsX()-1,regionYields["pass"])
            h.SetBinContent(h.GetNbinsX(),regionYields["fail"])
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
