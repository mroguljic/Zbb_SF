import ROOT as r
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array

matplotlib.use('Agg')

def getRatio(ptLOkFac,ptNLO,rName):
    ratio = ptNLO.Clone(rName)
    ratio.Divide(ptLOkFac)
    f = r.TFile.Open("test.root","UPDATE")
    ratio.Write()
    f.Close()

def plotPts(LO,LOcorr,NLO,outputFile,legendTitle=2016):
    plt.style.use([hep.style.CMS])
    LO, edges   = hist2array(LO,return_edges=True)
    LOcorr      = hist2array(LOcorr,return_edges=False)
    NLO         = hist2array(NLO,return_edges=False)

    f, axs      = plt.subplots(2,1, sharex=True, sharey=False,gridspec_kw={'height_ratios': [4, 1],'hspace': 0.15})
    axs         = axs.flatten()
    plt.sca(axs[0])
    histos      = [LO,LOcorr,NLO]
    labels      = ["LO","LO x kFactor","NLO"]

    hep.histplot(histos,edges[0],stack=False,label=labels,linewidth=2,histtype="step")

    hep.cms.lumitext(text="1 $fb^{-1}$ (13 TeV)")
    hep.cms.text("WiP",loc=0)
    plt.tight_layout()
    plt.legend(loc="best",title=legendTitle)
    axs[0].set_yscale("log")
    axs[0].set_xlim([200,1000])
    axs[0].set_ylim([1,None])
    axs[0].set_ylabel("Events/10 GeV",horizontalalignment='right', y=1.0)

    axs[1].set_ylabel("Ratio to NLO")
    #axs[1].set_ylim([-2.5,2.5])
    axs[1].set_xlabel("Generator V pT",horizontalalignment='right', x=1.0)


    plt.sca(axs[1])#switch to lower pad
    axs[1].set_ylim([0.5,1.5])
    axs[1].axhline(y=1.0, color="black")

    ratiosBefore = LO/NLO
    ratiosAfter  = LOcorr/NLO
    hep.histplot([ratiosBefore,ratiosAfter],edges[0],histtype="step",linewidth=2)
    print("Saving ", outputFile)
    plt.savefig(outputFile)

    plt.clf()


corrFile    = r.TFile.Open("NLO_corrections_new.root")
shapesFile  = r.TFile.Open("NLOcheck.root")

#Z+Jets corrections
ptNLO       = shapesFile.Get("DYJetsToLL_2017_gen_V_pT")
ptNLO.Scale(6.93)#BR(Z->qq)/BR(Z->ll)


for year in ["2016","2017","2018"]:
    ptLO        = shapesFile.Get("ZJets_{0}_gen_V_pT".format(year))
    ptLOkFac    = ptLO.Clone("ZJets_{0}_gen_V_pT_corr".format(year))

    if(year=="2016"):
        corr        = corrFile.Get("QCD_Z_16")
    else:
        corr        = corrFile.Get("QCD_Z_17")

    for i in range(1,ptLO.GetNbinsX()+1):
        pt          = ptLO.GetBinCenter(i)
        kFac        = corr.GetBinContent(corr.FindBin(pt))

        ptLOkFac.SetBinContent(i,ptLOkFac.GetBinContent(i)*kFac)

    #plotPts(ptLO,ptLOkFac,ptNLO,"{0}_Z.png".format(year),legendTitle=year)
    getRatio(ptLOkFac,ptNLO,"residual_{0}".format(year))



#W+Jets corrections
# ptNLO       = shapesFile.Get("WJetsToLNu_2017_gen_V_pT")
# ptNLO.Scale(2.09)#BR(W->qq)/BR(W->lnu)


# for year in ["2016","2017","2018"]:
#     ptLO        = shapesFile.Get("WJets_{0}_gen_V_pT".format(year))
#     ptLOkFac    = ptLO.Clone("WJets_{0}_gen_V_pT_corr".format(year))

#     if(year=="2016"):
#         corr        = corrFile.Get("QCD_W_16")
#     else:
#         corr        = corrFile.Get("QCD_W_17")

#     for i in range(1,ptLO.GetNbinsX()+1):
#         pt          = ptLO.GetBinCenter(i)
#         kFac        = corr.GetBinContent(corr.FindBin(pt))

#         ptLOkFac.SetBinContent(i,ptLOkFac.GetBinContent(i)*kFac)

#     plotPts(ptLO,ptLOkFac,ptNLO,"{0}_W.png".format(year),legendTitle=year)
