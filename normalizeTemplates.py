import ROOT as r
import json
import sys
import re
import os


def normalizeProcess(process,year,inFile,outFile):
    h_dict = {}
    f = r.TFile.Open(inFile)
    print(process,inFile)
    json_file = open("xsecs.json")
    config = json.load(json_file)
    xsec    = config[year][process]["xsec"]
    luminosity  = config[year]["lumi"]
    sumGenW     = f.Get("{0}_cutflow_nom".format(process)).GetBinContent(1)
    nLumi       = xsec*luminosity
    scaling     = nLumi/sumGenW
    print("Scale: {0:.6f}".format(scaling))
    for key in f.GetListOfKeys():
        h = key.ReadObj()
        hName = h.GetName()
        h.Scale(scaling)
        h.SetDirectory(0)
        h_dict[hName] = h
    f.Close()

    f = r.TFile(outFile,"recreate")
    f.cd()
    for key in h_dict:
        histo = h_dict[key]
        histo.Write()
    f.Close()


def mergeSamples(inFiles,outFile,regexMatch,regexReplace):
    h_dict = {}
    print("Merging to {0}".format(outFile))
    for inFile in inFiles:
        print(inFile)
        f        = r.TFile.Open(inFile) 
        for key in f.GetListOfKeys():
            h = key.ReadObj()
            hName = h.GetName()
            h.SetDirectory(0)
            hKey = re.sub(regexMatch,regexReplace,hName,count=1)
            if not hKey in h_dict:
                h.SetName(hKey)
                h_dict[hKey] = h
            else:
                h_dict[hKey].Add(h)
        f.Close()
    f = r.TFile(outFile,"recreate")
    f.cd()
    for key in h_dict:
        histo = h_dict[key]
        histo.Write()
    f.Close()
    print("\n")

def lumiNormalization(wp=0.98):

    processes16 = ["QCD500","QCD700","QCD1000","QCD1500","QCD2000","TTbar","TTbarSemi","TTbarHT","ST_top","ST_antitop","ST_tW_top"
    ,"ST_tW_antitop","ST_sChannel","WJets400","WJets600","WJets800","ZJets400","ZJets600","ZJets800"]
    processes17 = ["QCD500","QCD700","QCD1000","QCD1500","QCD2000","TTbar","TTbarSemi","TTbarMtt700","TTbarMtt1000",
    "WJets400","WJets600","WJets800","ZJets400","ZJets600","ZJets800"]
    processes18 = processes17
    for year in ['2016','2017','2018']:
        print(year)
        nonScaledDir = "results/templates/{0}/{1}/nonScaled/".format(wp,year)
        lumiScaledDir = "results/templates/{0}/{1}/scaled/".format(wp,year)
        if(year=='2016'):
            processes = processes16
        elif(year=='2017'):
            processes = processes17
        elif(year=='2018'):
            processes = processes18 
        for proc in processes:
            nonScaledFile = "{0}/{1}.root".format(nonScaledDir,proc)
            if(os.path.isfile(nonScaledFile)):
                try:                 
                    normalizeProcess(proc,year,"{0}/{1}.root".format(nonScaledDir,proc),"{0}/{1}.root".format(lumiScaledDir,proc))
                except:
                    print("Couldn't normalize {0}".format(proc))
            else:
                print("{0} does not exist, skipping!".format(nonScaledFile))
        
        QCDsamples = ["QCD500.root","QCD700.root","QCD1000.root","QCD1500.root","QCD2000.root"]
        QCDsamples = [lumiScaledDir+f for f in QCDsamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
        mergeSamples(QCDsamples,"{0}/QCD{1}.root".format(lumiScaledDir,year[-2:]),"QCD\d+_","QCD_")

        if(year=="2016"):
            ttSamples = ["TTbar.root","TTbarSemi.root","TTbarHT.root"]
            ttSamples = [lumiScaledDir+f for f in ttSamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
            mergeSamples(ttSamples,"{0}/TTbar{1}.root".format(lumiScaledDir,year[-2:]),"TTbarSemi|TTbarHT|TTbar","TTbar")
        else:
            ttSamples = ["TTbar.root","TTbarSemi.root","TTbarMtt700.root","TTbarMtt1000"]
            ttSamples = [lumiScaledDir+f for f in ttSamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
            mergeSamples(ttSamples,"{0}/TTbar{1}.root".format(lumiScaledDir,year[-2:]),"TTbarSemi|TTbarMtt700|TTbarMtt1000|TTbar","TTbar")

        STsamples = ["ST_top.root","ST_antitop.root","ST_tW_antitop.root","ST_tW_top.root","ST_sChannel.root"]
        STsamples = [lumiScaledDir+f for f in STsamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
        mergeSamples(STsamples,"{0}/ST{1}.root".format(lumiScaledDir,year[-2:]),"ST_sChannel_|.+top_","ST_")

        WJetsSamples = ["WJets400.root","WJets600.root","WJets800.root"]
        WJetsSamples = [lumiScaledDir+f for f in WJetsSamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
        mergeSamples(WJetsSamples,"{0}/WJets{1}.root".format(lumiScaledDir,year[-2:]),"[A-Z]Jets\d+_","WJets_")

        ZJetsSamples = ["ZJets400.root","ZJets600.root","ZJets800.root"]
        ZJetsSamples = [lumiScaledDir+f for f in ZJetsSamples if (os.path.isfile(os.path.join(lumiScaledDir, f)))]
        mergeSamples(ZJetsSamples,"{0}/ZJets{1}.root".format(lumiScaledDir,year[-2:]),"[A-Z]Jets\d+_","ZJets_")


        JetHTSamples = [nonScaledDir+f for f in os.listdir(nonScaledDir) if (os.path.isfile(os.path.join(nonScaledDir, f)) and "JetHT" in f)]
        mergeSamples(JetHTSamples,"{0}/JetHT{1}.root".format(lumiScaledDir,year[-2:]),"JetHT201[0-9][A-Z]_","data_obs_")

def getPtRwtScaling(inputFile):
    f           = r.TFile.Open(inputFile)
    hBeforePt   = f.Get("TTbar_m_pT_T__ptRwt_down")
    hBeforePt.Add(f.Get("TTbar_m_pT_L__ptRwt_down"))
    hBeforePt.Add(f.Get("TTbar_m_pT_F__ptRwt_down"))
    hAfterPt    = f.Get("TTbar_m_pT_T__nominal")
    hAfterPt.Add(f.Get("TTbar_m_pT_L__nominal"))
    hAfterPt.Add(f.Get("TTbar_m_pT_F__nominal"))
    scale       = hBeforePt.Integral()/hAfterPt.Integral()
    return scale

def getPtRwtUpScaling(inputFile):
    f           = r.TFile.Open(inputFile)
    hBeforePt   = f.Get("TTbar_m_pT_T__ptRwt_down")
    hBeforePt.Add(f.Get("TTbar_m_pT_L__ptRwt_down"))
    hBeforePt.Add(f.Get("TTbar_m_pT_F__ptRwt_down"))
    hAfterPt    = f.Get("TTbar_m_pT_T__ptRwt_up")
    hAfterPt.Add(f.Get("TTbar_m_pT_L__ptRwt_up"))
    hAfterPt.Add(f.Get("TTbar_m_pT_F__ptRwt_up"))
    scale       = hBeforePt.Integral()/hAfterPt.Integral()
    return scale


def renormalizePtRwt(inputFile):
    print("Adjusting for pT Rwt: {0}".format(inputFile.split("/")[-1]))
    f           = r.TFile.Open(inputFile)
    scalings    = {}
    newHistos   = []
    scale       = getPtRwtScaling(inputFile)
    rwtUpScale  = getPtRwtUpScaling(inputFile)
    print(scale, rwtUpScale)
    for key in f.GetListOfKeys():
        h       = key.ReadObj()
        hName   = h.GetName()
        h.SetDirectory(0)
        if(("_m_pT_" in hName) and not "ptRwt" in hName):
            normBefore = h.Integral()
            h.Scale(scale)
            normAfter  = h.Integral()
            #print("{0}: {1} -> {2}".format(hName,normBefore,normAfter))
            newHistos.append(h)
        elif("ptRwtUp" in hName):
            normBefore = h.Integral()
            h.Scale(rwtUpScale)
            normAfter  = h.Integral()
            #print("{0}: {1} -> {2}".format(hName,normBefore,normAfter))
            newHistos.append(h)
        else:
            newHistos.append(h)    
    f.Close()

    cpCmd = "cp {0} {1}".format(inputFile,inputFile.replace(".root","_backup.root"))
    os.system(cpCmd)

    f = r.TFile.Open(inputFile,"recreate")
    f.cd()
    for h in newHistos:
        h.Write()
    f.Close()


if __name__ == '__main__':

    #lumiNormalization(wp=0.94)
    lumiNormalization(wp=0.98)
    for year in ["16","17","18"]:
        ttbarTpl = "results/templates/20{0}/scaled/TTbar{0}.root".format(year)
        renormalizePtRwt(ttbarTpl)