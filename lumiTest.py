import ROOT, time
ROOT.gROOT.SetBatch(True)
from TIMBER.Tools.Common import CompileCpp
import ROOT
from TIMBER.Analyzer import ModuleWorker, analyzer

inputFile   = "root://cms-xrd-global.cern.ch///store/data/Run2016F/JetHT/NANOAOD/UL2016_MiniAODv2_NanoAODv9-v1/70000/F77A6FC2-0D11-6445-880B-5B8509DC4AB2.root"
ana         = analyzer(inputFile)
print(ana.DataFrame.Count().GetValue())
lumiFilter  = ModuleWorker("LumiFilter","TIMBER/Framework/include/LumiFilter.h",[16])
ana.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"run":"run","lumi":"luminosityBlock"}))
print(ana.DataFrame.Count().GetValue())
