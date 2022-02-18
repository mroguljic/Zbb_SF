import ROOT

import time, os
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Tools.Common import *
from TIMBER.Analyzer import *
import sys


def getNweighted(analyzer,isData):
    if not isData:
        nWeighted = a.DataFrame.Sum("genWeight").GetValue()
    else:
        nWeighted = a.DataFrame.Count().GetValue()
    return nWeighted

parser = OptionParser()

parser.add_option('-i', '--input', metavar='IFILE', type='string', action='store',
                default   =   '',
                dest      =   'input',
                help      =   'A root file or text file with multiple root file locations to analyze')
parser.add_option('-o', '--output', metavar='OFILE', type='string', action='store',
                default   =   'output.root',
                dest      =   'output',
                help      =   'Output file name.')
parser.add_option('-p', '--process', metavar='PROCESS', type='string', action='store',
                default   =   'ZJets400',
                dest      =   'process',
                help      =   'Process in the given MC file')
parser.add_option('-y', '--year', metavar='year', type='string', action='store',
                default   =   '2016',
                dest      =   'year',
                help      =   'Dataset year')
parser.add_option('--var', metavar='variation', type='string', action='store',
                default   =   "nom",
                dest      =   'variation',
                help      =   'jmrUp/Down, jmsUp/Down, jesUp/Down, jerUp/Down')

(options, args) = parser.parse_args()
start_time = time.time()
year = options.year

CompileCpp("TIMBER/Framework/common.cc") 
CompileCpp("TIMBER/Framework/deltaRMatching.cc") 
CompileCpp("TIMBER/Framework/helperFunctions.cc") 
CompileCpp("TIMBER/Framework/TTstitching.cc") 
CompileCpp("TIMBER/Framework/SemileptonicFunctions.cc") 
#CompileCpp("TIMBER/Framework/semiResolvedFunctions.cc") 
CompileCpp("TIMBER/Framework/ZbbSF/JMSUncShifter.cc") 
CompileCpp("TIMBER/Framework/ZbbSF/Zbb_Functions.cc") 
CompileCpp("JMSUncShifter jmsShifter = JMSUncShifter();") 
CompileCpp("TIMBER/Framework/src/JMRUncSmearer.cc") 
CompileCpp("JMRUncSmearer jmrSmearer = JMRUncSmearer();") 

varName = options.variation
if(varName=="nom"):
    ptVar  = "FatJet_pt_nom"
elif("jm" in varName):#jmr,jms
    ptVar  = "FatJet_pt_nom"
elif("je" in varName):#jes,jer
    ptVar  = "FatJet_pt_{0}".format(varName.replace("jes","jesTotal"))
else:
    print("Not recognizing shape uncertainty {0}, exiting".format(varName))        
    sys.exit()

a = analyzer(options.input)

# nToRun = 10000
# small_rdf = a.GetActiveNode().DataFrame.Range(nToRun) # makes an RDF with only the first nentries considered
# small_node = Node('small',small_rdf) # makes a node out of the dataframe
# a.SetActiveNode(small_node) # tell analyzer about the node by setting it as the active node


runNumber = a.DataFrame.Range(1).AsNumpy(["run"])#just checking the first run number to see if data or MC
if(runNumber["run"][0]>10000):
    isData=True
    print("Running on data")
else:
    isData=False
    print("Running on MC")
histos      = []

if isData:
    a.Define("genWeight","1")

nProc = a.genEventSumw

if not isData:
    CompileCpp('TIMBER/Framework/src/AK4Btag_SF.cc')
    print('AK4Btag_SF ak4SF = AK4Btag_SF({0}, "DeepJet", "reshaping");'.format(options.year[2:]))
    CompileCpp('AK4Btag_SF ak4SF = AK4Btag_SF({0}, "DeepJet", "reshaping");'.format(options.year[2:]))

if(options.year=="2016"):
    deepJetM = 0.3093
if(options.year=="2017"):
    deepJetM = 0.3040 
if(options.year=="2018"):
    deepJetM = 0.2783 

if(year=="2016"):
    eta_cut = 2.4
else:
    eta_cut = 2.5

if("TTbar" in options.process):
    a.Define("topIdx","getPartIdx(nGenPart,GenPart_pdgId,GenPart_statusFlags,6)")
    a.Define("antitopIdx","getPartIdx(nGenPart,GenPart_pdgId,GenPart_statusFlags,-6)")
    a.Cut("twoTops","topIdx>-1 && antitopIdx>-1") #perhaps unnecessary
    a.Define("topVector","analyzer::TLvector(GenPart_pt[topIdx],GenPart_eta[topIdx],GenPart_phi[topIdx],GenPart_mass[topIdx])")
    a.Define("antitopVector","analyzer::TLvector(GenPart_pt[antitopIdx],GenPart_eta[antitopIdx],GenPart_phi[antitopIdx],GenPart_mass[antitopIdx])")
    a.Define("MTT",'analyzer::invariantMass(topVector,antitopVector)')
    a.Define("topPt",'GenPart_pt[topIdx]')
    a.Define("antitopPt",'GenPart_pt[antitopIdx]')
    if(year=="2016"):
        a.Define("ttHTFlag","highHTFlag(nGenPart,GenPart_pdgId,GenPart_pt,GenPart_phi,GenPart_eta,GenPart_mass,nGenJetAK8,GenJetAK8_pt,GenJetAK8_phi,GenJetAK8_eta,GenJetAK8_mass)")
        if("HT" in options.process):
            a.Cut("ttHTCut","ttHTFlag==1")
        else:
           a.Cut("ttHTCut","ttHTFlag==0")
    else:
        if(options.process=="TTbar" or options.process=="TTbarSemi"):
            a.Cut("MTTcut","MTT<700")


nSkimmed = getNweighted(a,isData)

MetFilters = ["Flag_BadPFMuonFilter","Flag_EcalDeadCellTriggerPrimitiveFilter","Flag_HBHENoiseIsoFilter","Flag_HBHENoiseFilter","Flag_globalSuperTightHalo2016Filter","Flag_goodVertices"]
if(isData):
    MetFilters.append("Flag_eeBadScFilter")
if(year!="2016"):
    MetFilters.append("Flag_ecalBadCalibFilter")
    MetFilters.append("Flag_eeBadScFilter")
MetFiltersString = a.GetFlagString(MetFilters)

if(year=="2016"):
    if("JetHT2016B" in options.process):
        #2016B does not have the AK8PFJet450 in all files and this causes problems so it's removed from the list
        triggerList = ["HLT_AK8DiPFJet280_200_TrimMass30","HLT_PFHT650_WideJetMJJ900DEtaJJ1p5","HLT_AK8PFHT650_TrimR0p1PT0p03Mass50",
        "HLT_AK8PFHT700_TrimR0p1PT0p03Mass50","HLT_PFHT800","HLT_PFHT900","HLT_AK8PFJet360_TrimMass30","HLT_AK8DiPFJet280_200_TrimMass30_BTagCSV_p20"]
    else:
        triggerList = ["HLT_AK8DiPFJet280_200_TrimMass30","HLT_PFHT650_WideJetMJJ900DEtaJJ1p5","HLT_AK8PFHT650_TrimR0p1PT0p03Mass50",
        "HLT_AK8PFHT700_TrimR0p1PT0p03Mass50","HLT_PFHT800","HLT_PFHT900","HLT_AK8PFJet360_TrimMass30","HLT_AK8DiPFJet280_200_TrimMass30_BTagCSV_p20","HLT_AK8PFJet450"]
elif(year=="2017"):
    triggerList=["HLT_PFHT1050","HLT_AK8PFJet400_TrimMass30","HLT_AK8PFJet420_TrimMass30","HLT_AK8PFHT800_TrimMass50",
"HLT_PFJet500","HLT_AK8PFJet500"]
elif(year=="2018"):
   triggerList=["HLT_PFHT1050","HLT_AK8PFJet400_TrimMass30","HLT_AK8PFJet420_TrimMass30","HLT_AK8PFHT800_TrimMass50",
"HLT_PFJet500","HLT_AK8PFJet500"]


if("ZJets" in options.process or "WJets" in options.process):
    a.Define("genVpt","genVpt(nGenPart,GenPart_pdgId,GenPart_pt,GenPart_statusFlags)")
    a.Define("nAK4_30","nAK4(nJet,Jet_eta,Jet_pt,30,{0})".format(eta_cut))
    a.Define("nAK4_50","nAK4(nJet,Jet_eta,Jet_pt,50,{0})".format(eta_cut))
    a.Define("nAK8_100","nAK4(nFatJet,FatJet_eta,FatJet_pt,100,{0})".format(eta_cut))#nAK4 works with AK8 collection as well
    a.Define("nAK8_200","nAK4(nFatJet,FatJet_eta,FatJet_pt,200,{0})".format(eta_cut))#nAK4 works with AK8 collection as well
    a.Define("nGenHardPart","nPartHardProcess(nGenPart,GenPart_pdgId,GenPart_statusFlags)")
    a.Define("nLHEOutgoingPart","nLHEPartOutgoing(nLHEPart,LHEPart_pdgId,LHEPart_status)")
    a.Define("nAK4_30_extra","nAK4Extra(nJet,Jet_eta,Jet_phi,Jet_pt,30,{0},FatJet_eta,FatJet_phi)".format(eta_cut))
    hvPt = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_gen_V_pT'.format(options.process),';Gen V pT [GeV]; Events/10 GeV;',200,0,2000),"genVpt","genWeight")
    h_HT = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_HT'.format(options.process),';HT [GeV]; Events/10 GeV;',200,0,2000),"LHE_HT","genWeight")
    h_LHEnJets = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_LHEnJets'.format(options.process),';LHE_Njets; Events/1;',11,-0.5,10.5),"LHE_Njets","genWeight")
    h_LHEnPart = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_LHEnPart'.format(options.process),';LHE_nPartons; Events/1;',11,-0.5,10.5),"nLHEOutgoingPart","genWeight")
    h_GennPart = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_GennPart'.format(options.process),';Gen_nPartons; Events/1;',11,-0.5,10.5),"nGenHardPart","genWeight")
    h_nAK4_30  = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_n_AK4_30'.format(options.process),';nAK4; Events/1;',11,-0.5,10.5),"nAK4_30","genWeight")
    h_nAK4_50  = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_n_AK4_50'.format(options.process),';nAK4; Events/1;',11,-0.5,10.5),"nAK4_50","genWeight")
    h_nAK8_100 = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_n_AK8_100'.format(options.process),';nAK8; Events/1;',11,-0.5,10.5),"nAK8_100","genWeight")
    h_nAK8_200 = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_n_AK8_200'.format(options.process),';nAK8; Events/1;',11,-0.5,10.5),"nAK8_200","genWeight")

    histos.append(hvPt)
    histos.append(h_HT)
    histos.append(h_LHEnJets)
    histos.append(h_LHEnPart)
    histos.append(h_GennPart)
    histos.append(h_nAK4_30)
    histos.append(h_nAK4_50)
    histos.append(h_nAK8_100)
    histos.append(h_nAK8_200)


a.Cut("MET_Filters",MetFiltersString)
beforeTrigCheckpoint = a.GetActiveNode()
if(isData):
    triggersStringAll = a.GetTriggerString(triggerList)    
    a.Cut("Triggers",triggersStringAll)
    #Only applying trigger to data, will apply trigger turn-on to MC
nTrig = getNweighted(a,isData)


#Jet(s) definition
a.Cut("nFatJet","nFatJet>1")
a.Cut("ID","FatJet_jetId[0]>1 && FatJet_jetId[1]>1")#bit 1 is loose, bit 2 is tight, bit3 is tightlepVeto, we select tight
nJetID = getNweighted(a,isData)


a.Cut("Eta","abs(FatJet_eta[0])<{0} && abs(FatJet_eta[1])<{0}".format(eta_cut))
nEta = getNweighted(a,isData)


if(varName=="jmsUp" or varName=="jmsPtUp"):
    msdShift = 2
elif(varName=="jmsDown" or varName=="jmsPtDown"):
    msdShift = 1
else:
    msdShift = 0

if(varName=="jmrUp"):
    msdSmear = 2
elif(varName=="jmrDown"):
    msdSmear = 0
else:
    msdSmear = 0

evtColumns = VarGroup("Event columns")


evtColumns.Add("FatJet_pt0","{0}[0]".format(ptVar))
evtColumns.Add("FatJet_pt1","{0}[1]".format(ptVar))
evtColumns.Add("FatJet_eta0","FatJet_eta[0]")
evtColumns.Add("FatJet_phi0","FatJet_phi[0]")
evtColumns.Add("nEle","nElectrons(nElectron,Electron_cutBased,0,Electron_pt,20,Electron_eta)")
#0:fail,1:veto,2:loose,3:medium,4:tight
#condition is, cutBased>cut
evtColumns.Add("nMu","nMuons(nMuon,Muon_looseId,Muon_pfIsoId,0,Muon_pt,20,Muon_eta)")
#1=PFIsoVeryLoose, 2=PFIsoLoose, 3=PFIsoMedium, 4=PFIsoTight, 5=PFIsoVeryTight, 6=PFIsoVeryVeryTight
#condition is, pfIsoId>cut


if isData:
    evtColumns.Add("mSD",'FatJet_msoftdrop[0]')
else:
    if("jmsPt" in varName):
        evtColumns.Add("scaledMSD",'jmsShifter.ptDependentJMS(FatJet_msoftdrop[0],FatJet_pt0,%i)' %(msdShift))
    else:
        evtColumns.Add("scaledMSD",'jmsShifter.shiftMsd(FatJet_msoftdrop[0],"%s",%i)' %(year, msdShift))

    smearString = "scaledMSD,1.1,nGenJetAK8,GenJetAK8_mass,FatJet_genJetAK8Idx[0],{0}".format(msdSmear)
    evtColumns.Add("mSD",'jmrSmearer.smearMsd(%s)'%(smearString))

#b-tag reshaping
if(varName == "sfDown"):
    sfVar = 1
elif(varName=="sfUp"):
    sfVar = 2
else:
    sfVar = 0 

if(isData):
    evtColumns.Add("btagDisc",'Jet_btagDeepB') 
else:
    evtColumns.Add("btagDisc",'ak4SF.evalCollection(nJet,Jet_pt, Jet_eta, Jet_hadronFlavour,Jet_btagDeepB,{0})'.format(sfVar)) 
evtColumns.Add("topVetoFlag","topVeto(FatJet_eta0,FatJet_phi0,nJet,Jet_eta,{0},Jet_phi,Jet_pt,btagDisc,{1})".format(eta_cut,deepJetM))

a.Apply([evtColumns])

a.Cut("pT","FatJet_pt0>450")
a.Cut("pT_subl","FatJet_pt1>200")
npT = getNweighted(a,isData)

a.Cut("mSDCut","mSD>40")
nmSD = getNweighted(a,isData)

if("ZJets" in options.process or "WJets" in options.process):
    hvPt = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_gen_V_pT'.format(options.process),';Gen V pT [GeV]; Events/10 GeV;',200,0,2000),"genVpt","genWeight")
    h_HT = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_HT'.format(options.process),';HT [GeV]; Events/10 GeV;',200,0,2000),"LHE_HT","genWeight")
    h_LHEnJets = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_LHEnJets'.format(options.process),';LHE_Njets; Events/1;',11,-0.5,10.5),"LHE_Njets","genWeight")
    h_LHEnPart = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_LHEnPart'.format(options.process),';LHE_nPartons; Events/1;',11,-0.5,10.5),"nLHEOutgoingPart","genWeight")
    h_GennPart = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_GennPart'.format(options.process),';Gen_nPartons; Events/1;',11,-0.5,10.5),"nGenHardPart","genWeight")
    h_nAK4_30 = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_n_AK4_30'.format(options.process),';nAK4; Events/1;',11,-0.5,10.5),"nAK4_30","genWeight")
    h_nAK4_30_extra = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_n_AK4_30_away'.format(options.process),';nAK4; Events/1;',11,-0.5,10.5),"nAK4_30_extra","genWeight")
    h_nAK4_50 = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_n_AK4_50'.format(options.process),';nAK4; Events/1;',11,-0.5,10.5),"nAK4_50","genWeight")
    h_nAK8_100 = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_n_AK8_100'.format(options.process),';nAK8; Events/1;',11,-0.5,10.5),"nAK8_100","genWeight")
    h_nAK8_200 = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_n_AK8_200'.format(options.process),';nAK8; Events/1;',11,-0.5,10.5),"nAK8_200","genWeight")

    histos.append(hvPt)
    histos.append(h_HT)
    histos.append(h_LHEnJets)
    histos.append(h_LHEnPart)
    histos.append(h_GennPart)
    histos.append(h_nAK4_30)
    histos.append(h_nAK4_30_extra)
    histos.append(h_nAK4_50)
    histos.append(h_nAK8_100)
    histos.append(h_nAK8_200)


a.Cut("LeptonVeto","nMu==0 && nEle==0")
nLeptonVeto = getNweighted(a,isData)


a.Cut("topVeto","topVetoFlag==0")
nTopVeto = getNweighted(a,isData)


if(year=="2016"):
    #Pnet_v0
    a.Define("pnet0","FatJet_ParticleNetMD_probXbb[0]/(FatJet_ParticleNetMD_probXbb[0]+FatJet_ParticleNetMD_probQCDb[0]+FatJet_ParticleNetMD_probQCDbb[0]+FatJet_ParticleNetMD_probQCDc[0]+FatJet_ParticleNetMD_probQCDcc[0]+FatJet_ParticleNetMD_probQCDothers[0])")
else:
    #Pnet_v1
    a.Define("pnet0","FatJet_particleNetMD_Xbb[0]/(FatJet_particleNetMD_Xbb[0]+FatJet_particleNetMD_QCD[0])")


checkpoint  = a.GetActiveNode()
#-----Trigger study part------
#Separated from the rest of the cut tree
if(varName=="nom"):
    baselineTrigger="HLT_PFJet260"
    a.SetActiveNode(beforeTrigCheckpoint)
    a.Cut("Baseline",baselineTrigger)
    if(isData):
        a.Cut("MET For Trigger",MetFiltersString)
    #need to change names to create nodes with different names than already existing
    a.Cut("nFatJet_ForTrigger","nFatJet>1")
    a.Cut("Eta_ForTrigger","abs(FatJet_eta[0])<{0} && abs(FatJet_eta[1])<{0}".format(eta_cut))
    evtColumns.name = "Event Columns For Trigger"
    a.Apply([evtColumns])
    a.Cut("pT_ForTrigger","FatJet_pt0>450")
    a.Cut("pT_subl_ForTrigger","FatJet_pt1>200")
    a.Cut("mSDCut_ForTrigger","mSD>40")
    a.Cut("LeptonVeto_ForTrigger","nMu==0 && nEle==0")
    a.Cut("topVeto_ForTrigger","topVetoFlag==0")

    triggersStringAll   = a.GetTriggerString(triggerList)  

    h_noTriggers        = a.GetActiveNode().DataFrame.Histo2D(('{0}_noTriggers'.format(options.process),';M_{SD} [GeV] / 1 GeV;p_{T} [GeV] / 10 GeV;',160,40,200,55,450,1000),'mSD','FatJet_pt0',"genWeight")
    h_pT0noTriggers     = a.GetActiveNode().DataFrame.Histo1D(('{0}_pT0noTriggers'.format(options.process),';Leading jet pT [GeV]; Events/10 GeV;',55,450,1000),"FatJet_pt0","genWeight")
    a.Cut("Triggers for trig measurement",triggersStringAll)
    h_triggersAll       = a.GetActiveNode().DataFrame.Histo2D(('{0}_triggersAll'.format(options.process),';M_{SD} [GeV] / 1 GeV;p_{T} [GeV] / 10 GeV;',160,40,200,55,450,1000),'mSD','FatJet_pt0',"genWeight")
    h_pT0triggersAll    = a.GetActiveNode().DataFrame.Histo1D(('{0}_pT0triggersAll'.format(options.process),';Leading jet pT [GeV]; Events/10 GeV;',55,450,1000),"FatJet_pt0","genWeight")

    histos.append(h_noTriggers)
    histos.append(h_pT0noTriggers)
    histos.append(h_triggersAll)
    histos.append(h_pT0triggersAll)
    #return to event selection
    a.SetActiveNode(checkpoint)
#-----Trigger study part end------

#Categorize ZJets
if("ZJets" in options.process):
    a.Define("jetCat","classifyZJet(FatJet_phi0, FatJet_eta0, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags)")
    a.Define("VmatchedFatJetIdx","VmatchedFatJetIdx(nFatJet,FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_statusFlags)")
#Categorize WJets 
if("WJets" in options.process):
    a.Define("jetCat","classifyWJet(FatJet_phi0, FatJet_eta0, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags)")
    a.Define("VmatchedFatJetIdx","VmatchedFatJetIdx(nFatJet,FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_statusFlags)")

snapshotColumns = ["pnet0","FatJet_pt0","mSD","PV_npvsGood","nFatJet"]

#HEM drop
if(isData):
    if(year=="2018" and not "2018A" in options.process):
        a.Define("Jet0_HEM","FatJet_phi[0]>-1.57 && FatJet_phi[0]<-0.8 && FatJet_eta[0]<-1.3")
        a.Define("HEMflag","run>319076 && Jet0_HEM")
        a.Cut("HEMcut","HEMflag<1")
else:
    if(year=="2018"):
        a.Define("HEMflag","FatJet_phi[0]>-1.57 && FatJet_phi[0]<-0.8 && FatJet_eta[0]<-1.3")
        a.Define("HEMweight","HEMweightMC(HEMflag)")        

outputFile = options.output.replace(".root","_{0}.root".format(varName))

if not isData:
    snapshotColumns.append("Pileup_nTrueInt")
    snapshotColumns.append("genWeight")
    if("TTbar" in options.process):
        snapshotColumns.append("MTT")
        snapshotColumns.append("topPt")
        snapshotColumns.append("antitopPt")
    if("ZJets" in options.process or "WJets" in options.process):
        snapshotColumns.append("jetCat")
        snapshotColumns.append("genVpt")
        snapshotColumns.append("LHE_HT")
        snapshotColumns.append("VmatchedFatJetIdx")

        if(varName=="nom"):
            lhaid = a.lhaid
            CompileCpp("TIMBER/Framework/src/PDFweight_uncert.cc")
            CompileCpp("PDFweight_uncert pdfUncHandler = PDFweight_uncert({0});".format(lhaid))
            a.Define("pdfUnc","pdfUncHandler.eval(LHEPdfWeight)")
            snapshotColumns.append("pdfUnc")

if(year=="2018" and not isData):
    snapshotColumns.append("HEMweight")

opts = ROOT.RDF.RSnapshotOptions()
opts.fMode = "RECREATE"
opts.fLazy = False
a.GetActiveNode().DataFrame.Snapshot("Events",outputFile,snapshotColumns,opts)

cutFlowVars = [nProc,nSkimmed,nTrig,nJetID,nEta,npT,nmSD,nLeptonVeto,nTopVeto]
cutFlowLabels = ["Processed","Skimmed","Trigger","JetID","Eta","pT","mSD","Lepton Veto","Top veto","T","L","F"]#tagging bins will be filled out in template making
nCutFlowlabels = len(cutFlowLabels)
hCutFlow = ROOT.TH1F('{0}_cutflow'.format(options.process),"Number of events after each cut",nCutFlowlabels,0.5,nCutFlowlabels+0.5)
for i,label in enumerate(cutFlowLabels):
    hCutFlow.GetXaxis().SetBinLabel(i+1, label)

for i,var in enumerate(cutFlowVars):
    hCutFlow.AddBinContent(i+1,var)

histos.append(hCutFlow)


out_f = ROOT.TFile(outputFile,"UPDATE")
out_f.cd()
for h in histos:
    h.Write()
out_f.Close()

#a.PrintNodeTree('node_tree.dot',verbose=True)
print("Total time: "+str((time.time()-start_time)/60.) + ' min')