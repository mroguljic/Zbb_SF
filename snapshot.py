import ROOT, time
ROOT.gROOT.SetBatch(True)
from TIMBER.Tools.Common import CompileCpp
from optparse import OptionParser
import ROOT
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU, AutoPU, MakePU
import TIMBER.Tools.AutoJME as AutoJME
import os

AutoJME.AK8collection = "FatJet"

def twoDigitYear(year):
    if("16" in year):
        return 16
    elif("17" in year):
        return 17
    elif("18" in year):
        return 18
    else:
        print("WARNING: Year not supported")
        return -1

def ApplyKinematicsSnap(ana): # For snapshotting only
    ana.Cut('njets','nFatJet > 1')
    ana.Cut('pT', 'FatJet_pt[0] > 400 && FatJet_pt[1] > 150')
    return ana

def ApplyStandardCorrections(ana,year,process):
    yr = twoDigitYear(year)
    if ana.isData:
        lumiFilter = ModuleWorker("LumiFilter","TIMBER/Framework/include/LumiFilter.h",[yr])
        ana.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"run":"run","lumi":"luminosityBlock"}))
        if yr == 18:
            HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',["data"+process[-1],"{0}"])
            ana.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"FatJet_eta","FatJet_phi":"FatJet_phi"})))

    else:
        ana  = AutoPU(ana,year)
        ana.AddCorrection(Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[ana.lhaid],corrtype='uncert'))
        if yr == 16 or yr == 17:
            ana.AddCorrection(
                Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[yr],corrtype='weight')
            )
        elif yr == 18:
            ana.AddCorrection(
                Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[process,"{0}"],corrtype='corr')
            )

    ana = AutoJME.AutoJME(ana, "FatJet", year, dataEra=process[-1],ULflag=True)
    ana.MakeWeightCols(extraNominal='genWeight' if not ana.isData else '')

       
    return ana

def Snapshot(ana,year,output):
    yr = twoDigitYear(year)
    columns = [
        'n.*','FatJet*','HLT_PF*', 'HLT_AK8.*','Pileup_nTrueInt','Pileup_nPV',
        'event', 'eventWeight', 'luminosityBlock', 'run','Jet_pt', 'Jet_eta','Jet_phi', 'Jet_hadronFlavour','Jet_btagDeepB',
        'Electron_cutBased','Electron_pt','Electron_eta','Muon_looseId','Muon_pfIsoId','Muon_pt','Muon_eta', "Flag.*"
    ]

    if not ana.isData:
        columns.extend(['GenPart_.*','genWeight',"LHE*"])
        columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down'])
        if yr == 16 or yr == 17:
            columns.extend(['Prefire__nom','Prefire__up','Prefire__down'])
        elif yr == 18:
            columns.append('HEM_drop__nom')

    ana.Snapshot(columns,output,'Events',saveRunChain=True)

def localCopy(inputLFN):
    xrdcpCMD = "xrdcp root://cms-xrd-global.cern.ch//{0} .".format(inputLFN)
    print(xrdcpCMD)
    os.system(xrdcpCMD)

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
                default   =   'JetHT2016B',
                dest      =   'process',
                help      =   'Output file name.')
parser.add_option('-y', '--year', metavar='year', type="string", action='store',
                default   =   '2016',
                dest      =   'year',
                help      =   'Dataset year: 2016APV, 2016, 2017, 2018')

(options, args) = parser.parse_args()
start_time      = time.time()
year            = options.year
process         = options.process

if(".txt" in options.input):
    inputFiles  = open(options.input, 'r')
    lines       = inputFiles.readlines()
    for iFile in lines:
        localCopy(iFile)
        selection = analyzer(iFile.split("/")[-1])
        selection = ApplyKinematicsSnap(selection)
        selection = ApplyStandardCorrections(selection,year,process)

        odir = options.output.split("/")[:-1]
        if not os.path.exists(odir):
            print("CREATING DIR: ", odir)
            os.makedirs(odir)

        Snapshot(selection,year,options.output)
        os.system("rm {0}".format(iFile.split("/")[-1]))


else:
    localCopy(options.input)
    selection = analyzer(options.input.split("/")[-1])
    selection = ApplyKinematicsSnap(selection)
    selection = ApplyStandardCorrections(selection,year,process)

    odir = options.output.rsplit("/",1)[0]
    if not os.path.exists(odir):
        print("CREATING DIR: ", odir)
        os.makedirs(odir)

    Snapshot(selection,year,options.output)
    os.system("rm {0}".format(options.input.split("/")[-1]))
    
print ('%s sec'%(time.time()-start_time))
