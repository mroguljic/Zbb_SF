import ROOT

import time, os
from optparse import OptionParser
from collections import OrderedDict

from TIMBER.Tools.Common import *
from TIMBER.Analyzer import *
import sys


def getNweighted(analyzer,isData):
    if not isData:
        nWeighted = analyzer.DataFrame.Sum("genWeight").GetValue()
    else:
        nWeighted = analyzer.DataFrame.Count().GetValue()
    return nWeighted

def ptCorrectorString(variation,isData):
    if isData:
        jetCorrector  = '{FatJet_JES_nom}'
    else:
        if(variation=="jesUp"):
            jetCorrector  = '{FatJet_JES_up,FatJet_JER_nom}'
        elif(variation=="jesDown"):
            jetCorrector  = '{FatJet_JES_down,FatJet_JER_nom}'
        elif(variation=="jerUp"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_up}'
        elif(variation=="jerDown"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_down}'
        else:
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom}'
    return jetCorrector

def massCorrectorString(variation,isData):
    if isData:
        jetCorrector  = '{FatJet_JES_nom}'
    else:
        if(variation=="jesUp"):
            jetCorrector  = '{FatJet_JES_up,FatJet_JER_nom,FatJet_JMS_nom,FatJet_JMR_nom}'
        elif(variation=="jesDown"):
            jetCorrector  = '{FatJet_JES_down,FatJet_JER_nom,FatJet_JMS_nom,FatJet_JMR_nom}'
        elif(variation=="jerUp"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_up,FatJet_JMS_nom,FatJet_JMR_nom}'
        elif(variation=="jerDown"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_down,FatJet_JMS_nom,FatJet_JMR_nom}'
        elif(variation=="jmsUp"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom,FatJet_JMS_up,FatJet_JMR_nom}'
        elif(variation=="jmsDown"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom,FatJet_JMS_down,FatJet_JMR_nom}'
        elif(variation=="jmrUp"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom,FatJet_JMS_nom,FatJet_JMR_up}'
        elif(variation=="jmrDown"):
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom,FatJet_JMS_nom,FatJet_JMR_down}'
        else:
            jetCorrector  = '{FatJet_JES_nom,FatJet_JER_nom,FatJet_JMS_nom,FatJet_JMR_nom}'

    return jetCorrector

def eventSelection(options):

    #----Initialize RDataFrame-----#
    start_time = time.time()
    year = options.year
    a = analyzer(options.input)

    #For testing only, faster execution
    # nToRun = 10000
    # small_rdf = a.GetActiveNode().DataFrame.Range(nToRun) 
    # small_node = Node('small',small_rdf)
    # a.SetActiveNode(small_node)

    runNumber = a.DataFrame.Range(1).AsNumpy(["run"])#check run number to see if data
    if(runNumber["run"][0]>10000):
        isData=True
        a.Define("genWeight","1")
        print("Running on data")
    else:
        isData=False
        print("Running on MC")
    nProc = a.genEventSumw
    #------------------------------#


    #------------Setup env----------#
    CompileCpp("TIMBER/Framework/Zbb_modules/Zbb_Functions.cc") 
    CompileCpp("TIMBER/Framework/Zbb_modules/helperFunctions.cc") 

    ptCorrector     = ptCorrectorString(options.variation,isData) 
    massCorrector   = massCorrectorString(options.variation,isData) 

    histos          = []

    if(options.year=="2016APV"):
       deepCsvM    = 0.6001
    elif(options.year=="2016"):
       deepCsvM    = 0.5847
    elif(options.year=="2017"):
       deepCsvM    = 0.4506
    elif(options.year=="2018"):
       deepCsvM    = 0.4168 
    else:
        print("Year not supported")
        sys.exit()
    #------------------------------#


    #-------AK4 b-tag SF-----------#
    if not isData:
        CompileCpp('TIMBER/Framework/Zbb_modules/AK4Btag_SF.cc')
        print('AK4Btag_SF ak4SF = AK4Btag_SF("{0}", "DeepCSV", "reshaping");'.format(options.year))
        CompileCpp('AK4Btag_SF ak4SF = AK4Btag_SF("{0}", "DeepCSV", "reshaping");'.format(options.year))
    #------------------------------#


    #-------TTbar stitching--------#
    if(options.process=="TTbarHadronic" or options.process=="TTbarSemileptonic"):
        CompileCpp("TIMBER/Framework/Zbb_modules/TTstitching.cc") 
        a.Define("MTT",'getMTT(nGenPart,GenPart_pdgId,GenPart_pt,GenPart_phi,GenPart_eta,GenPart_mass)')
        a.Cut("MTTcut","MTT<700")
    #------------------------------#

    nSkimmed = getNweighted(a,isData)

    #-------MET filters------------#
    MetFilters = ["Flag_BadPFMuonFilter","Flag_EcalDeadCellTriggerPrimitiveFilter","Flag_HBHENoiseIsoFilter","Flag_HBHENoiseFilter",
    "Flag_globalSuperTightHalo2016Filter","Flag_goodVertices","Flag_BadPFMuonDzFilter","Flag_eeBadScFilter","Flag_ecalBadCalibFilter"]
    if(year=="2017" or year=="2018"):
        MetFilters.append("Flag_ecalBadCalibFilter")
    MetFiltersString = a.GetFlagString(MetFilters)
    if MetFiltersString:#RDF crashes if METstring is empty
        a.Cut("MET_Filters",MetFiltersString)
    #------------------------------#


    #----------Triggers------------#
    beforeTrigCheckpoint    = a.GetActiveNode()
    if(year=="2016" or year=="2016APV"):
        triggerList         = ["HLT_AK8DiPFJet280_200_TrimMass30","HLT_AK8PFHT650_TrimR0p1PT0p03Mass50",
            "HLT_AK8PFHT700_TrimR0p1PT0p03Mass50","HLT_PFHT800","HLT_PFHT900","HLT_AK8PFJet360_TrimMass30","HLT_AK8PFJet450"]
    elif(year=="2017"):
        triggerList         =["HLT_PFHT1050","HLT_AK8PFJet400_TrimMass30","HLT_AK8PFJet420_TrimMass30",
        "HLT_AK8PFHT800_TrimMass50","HLT_PFJet500","HLT_AK8PFJet500"]
    elif(year=="2018"):
       triggerList          =["HLT_PFHT1050","HLT_AK8PFJet400_TrimMass30","HLT_AK8PFJet420_TrimMass30"
       ,"HLT_AK8PFHT800_TrimMass50","HLT_PFJet500","HLT_AK8PFJet500"]
    triggersStringAll       = a.GetTriggerString(triggerList)    
    if(isData): #Only applying trigger to data, will apply trigger turn-on to MC
        a.Cut("Triggers",triggersStringAll)
    nTrig                   = getNweighted(a,isData)
    #------------------------------#



    #------V+Jets diagnostics-------#
    if("ZJets" in options.process or "WJets" in options.process):
        a.Define("genVpt","genVpt(nGenPart,GenPart_pdgId,GenPart_pt,GenPart_statusFlags)")
        hvPt = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_gen_V_pT'.format(options.process),';Gen V pT [GeV]; Events/10 GeV;',200,0,2000),"genVpt","genWeight")
        h_HT = a.GetActiveNode().DataFrame.Histo1D(('{0}_no_cuts_HT'.format(options.process),';HT [GeV]; Events/10 GeV;',200,0,2000),"LHE_HT","genWeight")

        histos.append(hvPt)
        histos.append(h_HT)
    #------------------------------#



    #----------Selection-----------#
    a.Cut("nFatJet","nFatJet>1")
    a.Cut("ID","FatJet_jetId[0]>1 && FatJet_jetId[1]>1")#bit 1 is loose, bit 2 is tight, bit3 is tightlepVeto, we select tight
    nJetID = getNweighted(a,isData)


    a.Cut("Eta","abs(FatJet_eta[0])<2.4 && abs(FatJet_eta[1])<2.4")
    nEta = getNweighted(a,isData)

    evtColumns = VarGroup("Event columns")
    evtColumns.Add('FatJet_pt_corr','hardware::MultiHadamardProduct(FatJet_pt,%s)'%ptCorrector)
    evtColumns.Add('FatJet_msoftdrop_corr','hardware::MultiHadamardProduct(FatJet_msoftdrop,%s)'%massCorrector)
    evtColumns.Add('FatJet_mpnet_corr','hardware::MultiHadamardProduct(FatJet_particleNet_mass,%s)'%massCorrector)
    evtColumns.Add("FatJet_pt0","FatJet_pt_corr[0]")
    evtColumns.Add("FatJet_pt1","FatJet_pt_corr[1]")
    evtColumns.Add("FatJet_eta0","FatJet_eta[0]")
    evtColumns.Add("FatJet_phi0","FatJet_phi[0]")
    evtColumns.Add("nEle","nElectrons(nElectron,Electron_cutBased,0,Electron_pt,20,Electron_eta)")
    #0:fail,1:veto,2:loose,3:medium,4:tight
    #condition is, cutBased>cut
    evtColumns.Add("nMu","nMuons(nMuon,Muon_looseId,Muon_pfIsoId,0,Muon_pt,20,Muon_eta)")
    #1=PFIsoVeryLoose, 2=PFIsoLoose, 3=PFIsoMedium, 4=PFIsoTight, 5=PFIsoVeryTight, 6=PFIsoVeryVeryTight
    #condition is, pfIsoId>cut
    evtColumns.Add("JetSDMass",'FatJet_msoftdrop_corr[0]')
    evtColumns.Add("JetPnetMass",'FatJet_mpnet_corr[0]')

    #b-tag reshaping
    if(options.variation == "sfDown"):
        sfVar = 1
    elif(options.variation=="sfUp"):
        sfVar = 2
    else:
        sfVar = 0 

    if(isData):
        evtColumns.Add("btagDisc",'Jet_btagDeepB') 
    else:
        evtColumns.Add("btagDisc",'ak4SF.evalCollection(nJet,Jet_pt, Jet_eta, Jet_hadronFlavour,Jet_btagDeepB,{0})'.format(sfVar)) 
    evtColumns.Add("topVetoFlag","topVeto(FatJet_eta0,FatJet_phi0,nJet,Jet_eta,{0},Jet_phi,Jet_pt,btagDisc,{1})".format(2.4,deepCsvM))

    a.Apply([evtColumns])

    a.Cut("pT","FatJet_pt0>450")
    a.Cut("pT_subl","FatJet_pt1>200")
    npT = getNweighted(a,isData)

    a.Cut("JetPnetMassCut","JetPnetMass>40")
    nJetMass = getNweighted(a,isData)

    if("ZJets" in options.process or "WJets" in options.process):
        hvPt = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_gen_V_pT'.format(options.process),';Gen V pT [GeV]; Events/10 GeV;',200,0,2000),"genVpt","genWeight")
        h_HT = a.GetActiveNode().DataFrame.Histo1D(('{0}_jet_sel_HT'.format(options.process),';HT [GeV]; Events/10 GeV;',200,0,2000),"LHE_HT","genWeight")
        histos.append(hvPt)
        histos.append(h_HT)


    a.Cut("LeptonVeto","nMu==0 && nEle==0")
    nLeptonVeto = getNweighted(a,isData)


    a.Cut("topVeto","topVetoFlag==0")
    nTopVeto = getNweighted(a,isData)

    a.Define("pnet0","FatJet_particleNetMD_Xbb[0]/(FatJet_particleNetMD_Xbb[0]+FatJet_particleNetMD_QCD[0])")
    #------------------------------#


    checkpoint  = a.GetActiveNode()
    #-----Trigger study part-------#
    if(options.variation=="nom"):
        baselineTrigger="HLT_PFJet260"
        a.SetActiveNode(beforeTrigCheckpoint)
        a.Cut("Baseline",baselineTrigger)
        if(MetFiltersString):
            a.Cut("MET For Trigger",MetFiltersString)
        #need to change names to create nodes with different names than already existing
        a.Cut("nFatJet_ForTrigger","nFatJet>1")
        a.Cut("Eta_ForTrigger","abs(FatJet_eta[0])<{0} && abs(FatJet_eta[1])<{0}".format(2.4))
        evtColumns.name = "Event Columns For Trigger"
        a.Apply([evtColumns])
        a.Cut("pT_ForTrigger","FatJet_pt0>450")
        a.Cut("pT_subl_ForTrigger","FatJet_pt1>200")
        a.Cut("JetMassCut_ForTrigger","JetPnetMass>40")
        a.Cut("LeptonVeto_ForTrigger","nMu==0 && nEle==0")
        a.Cut("topVeto_ForTrigger","topVetoFlag==0")

        triggersStringAll   = a.GetTriggerString(triggerList)  

        h_noTriggers        = a.GetActiveNode().DataFrame.Histo2D(('{0}_noTriggers'.format(options.process),';M_{SD} [GeV] / 1 GeV;p_{T} [GeV] / 10 GeV;',160,40,200,55,450,1000),'JetPnetMass','FatJet_pt0',"genWeight")
        h_pT0noTriggers     = a.GetActiveNode().DataFrame.Histo1D(('{0}_pT0noTriggers'.format(options.process),';Leading jet pT [GeV]; Events/10 GeV;',55,450,1000),"FatJet_pt0","genWeight")
        a.Cut("Triggers for trig measurement",triggersStringAll)
        h_triggersAll       = a.GetActiveNode().DataFrame.Histo2D(('{0}_triggersAll'.format(options.process),';M_{SD} [GeV] / 1 GeV;p_{T} [GeV] / 10 GeV;',160,40,200,55,450,1000),'JetPnetMass','FatJet_pt0',"genWeight")
        h_pT0triggersAll    = a.GetActiveNode().DataFrame.Histo1D(('{0}_pT0triggersAll'.format(options.process),';Leading jet pT [GeV]; Events/10 GeV;',55,450,1000),"FatJet_pt0","genWeight")

        histos.append(h_noTriggers)
        histos.append(h_pT0noTriggers)
        histos.append(h_triggersAll)
        histos.append(h_pT0triggersAll)
        a.SetActiveNode(checkpoint)
    #------------------------------#

    #-----Categorize V+Jets--------#
    if("ZJets" in options.process):
        a.Define("jetCat","classifyZJet(FatJet_phi0, FatJet_eta0, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags)")
        a.Define("VmatchedFatJetIdx","VmatchedFatJetIdx(nFatJet,FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_statusFlags)")
    if("WJets" in options.process):
        a.Define("jetCat","classifyWJet(FatJet_phi0, FatJet_eta0, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags)")
        a.Define("VmatchedFatJetIdx","VmatchedFatJetIdx(nFatJet,FatJet_phi,FatJet_eta,nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_statusFlags)")
    #------------------------------#


    #--------Store Output----------#

    snapshotColumns = ["pnet0","FatJet_pt0","JetPnetMass","JetSDMass","PV_npvsGood","nFatJet"]
    outputFile      = options.output.replace(".root","_{0}.root".format(options.variation))

    if not isData:
        snapshotColumns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__up','Pdfweight__down','Pileup_nTrueInt','genWeight'])
        
        if("TTbar" in options.process):
            snapshotColumns.append("MTT")
        
        if("ZJets" in options.process or "WJets" in options.process):
            snapshotColumns.append("jetCat")
            snapshotColumns.append("genVpt")
            snapshotColumns.append("LHE_HT")
            snapshotColumns.append("VmatchedFatJetIdx")

        if year=="2018":
            snapshotColumns.append("HEM_drop__nom")

        if "2016" in year or "2017" in year:
            snapshotColumns.extend(['Prefire__nom','Prefire__up','Prefire__down'])


    a.Snapshot(snapshotColumns,outputFile,'Events',saveRunChain=False)

    cutFlowVars         = [nProc,nSkimmed,nTrig,nJetID,nEta,npT,nJetMass,nLeptonVeto,nTopVeto]
    cutFlowLabels       = ["Processed","Skimmed","Trigger","JetID","Eta","pT","JetMass","Lepton Veto","Top veto","pass","fail"]#tagging bins will be filled out in template making
    nCutFlowlabels      = len(cutFlowLabels)
    hCutFlow            = ROOT.TH1F('{0}_cutflow'.format(options.process),"Number of events after each cut",nCutFlowlabels,0.5,nCutFlowlabels+0.5)
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
    #------------------------------#


    #a.PrintNodeTree('node_tree.dot',verbose=True)
    print("Total time: "+str((time.time()-start_time)/60.) + ' min')



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
eventSelection(options)
