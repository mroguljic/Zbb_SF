import ROOT as r
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array

matplotlib.use('Agg')

def multiplyCorrs(h1,h2):
    #multiplies h1 with values of h2 evaluated at h1 bin center
    for i in range(1,h1.GetNbinsX()+1):
        binCoord = h1.GetXaxis().GetBinCenter(i)
        h2Val    = h2.GetBinContent(h2.FindBin(binCoord))
        newVal   = h1.GetBinContent(i)*h2Val
        h1.SetBinContent(i,newVal)
    return h1

def plotPts(LO,LOcorr,NLO,outputFile,legendTitle=""):
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

    hep.cms.lumitext(text="1 $fb^{-1}$ (13 TeV)",fontsize=25)
    hep.cms.text("Simulation Work in progress",loc=0,fontsize=25)
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
    plt.savefig(outputFile.replace(".png",".pdf"))

    plt.clf()

def plotQCDCorr(corr,d1KUp,d2KUp,d1KDn,d2KDn,outputFile):
    plt.style.use([hep.style.CMS])
    corr, edgesCorr = hist2array(corr,return_edges=True)
    d1KUp,edgesUnc  = hist2array(d1KUp,return_edges=True)
    d2KUp           = hist2array(d2KUp,return_edges=False)
    d1KDn           = hist2array(d1KDn,return_edges=False)
    d2KDn           = hist2array(d2KDn,return_edges=False)

    f, ax      = plt.subplots()
    histos     = [d1KUp,d2KUp,d1KDn,d2KDn]
    labels     = ["d1K Unc","d2K Unc","_nolegend_","_nolegend_"]
    linestyles = ["--",":","--",":"]
    colors     = ["red","green","red","green"]
    hep.histplot(corr,edgesCorr[0],stack=False,label=["NLO QCD correction"],linewidth=2,histtype="step",linestyle=["-"],color=["black"])
    hep.histplot(histos,edgesUnc[0],stack=False,label=labels,linewidth=2,histtype="step",linestyle=linestyles,color=colors)

    hep.cms.lumitext(text="(13 TeV)")
    hep.cms.text("Simulation Work in progress",loc=0)
    plt.legend(loc="best")
    ax.set_yscale("linear")
    ax.set_xlim([200,2000])
    ax.set_ylim([0,None])
    ax.set_ylabel("Correction value",horizontalalignment='right', y=1.0)
    ax.set_xlabel("Generator V pT [GeV]",horizontalalignment='right', x=1.0)

    print("Saving ", outputFile)
    plt.tight_layout()
    plt.savefig(outputFile)
    plt.savefig(outputFile.replace(".png",".pdf"))
    plt.clf()

def plotEWKCorr(corr,d1KUp,d2KUp,d3KUp,d1KDn,d2KDn,d3KDn,outputFile):
    plt.style.use([hep.style.CMS])
    corr, edges     = hist2array(corr,return_edges=True)
    d1KUp           = hist2array(d1KUp,return_edges=False)
    d2KUp           = hist2array(d2KUp,return_edges=False)
    d3KUp           = hist2array(d3KUp,return_edges=False)
    d1KDn           = hist2array(d1KDn,return_edges=False)
    d2KDn           = hist2array(d2KDn,return_edges=False)
    d3KDn           = hist2array(d3KDn,return_edges=False)

    f, ax      = plt.subplots()
    histos     = [corr,d1KUp,d2KUp,d3KUp,d1KDn,d2KDn,d3KDn]
    labels     = ["NLO EWK correction","d1kappa Unc","d2kappa Unc","d3kappa Unc","_nolegend_","_nolegend_","_nolegend_"]
    linestyles = ["-","--",":","-.","--",":","-."]
    colors     = ["black","red","green","blue","red","green","blue"]
    hep.histplot(histos,edges[0],stack=False,label=labels,linewidth=2,histtype="step",linestyle=linestyles,color=colors)

    hep.cms.lumitext(text="(13 TeV)")
    hep.cms.text("Simulation Work in progress",loc=0)
    plt.legend(loc="best")
    ax.set_yscale("linear")
    ax.set_xlim([200,2000])
    ax.set_ylim([0,None])
    ax.set_ylabel("Correction value",horizontalalignment='right', y=1.0)
    ax.set_xlabel("Generator V pT [GeV]",horizontalalignment='right', x=1.0)

    print("Saving ", outputFile)
    plt.tight_layout()
    plt.savefig(outputFile)
    plt.savefig(outputFile.replace(".png",".pdf"))
    plt.clf()

corrFile    = r.TFile.Open("NLO_corrections.root")
shapesFile  = r.TFile.Open("NLOcheck.root")

#Z+Jets corrections
for year in ["2017"]:
    ptNLO       = shapesFile.Get("DYJetsToLL_{0}_gen_V_pT".format(year))
    ptNLO.Scale(6.93)#BR(Z->qq)/BR(Z->ll)

    ptLO        = shapesFile.Get("ZJets_{0}_gen_V_pT".format(year))
    ptLOkFac    = ptLO.Clone("ZJets_{0}_gen_V_pT_corr".format(year))

    corr        = corrFile.Get("QCD_Z")

    for i in range(1,ptLO.GetNbinsX()+1):
        pt          = ptLO.GetBinCenter(i)
        kFac        = corr.GetBinContent(corr.FindBin(pt))

        ptLOkFac.SetBinContent(i,ptLOkFac.GetBinContent(i)*kFac)

    plotPts(ptLO,ptLOkFac,ptNLO,"plots/QCD_Z.png")



# #W+Jets corrections
for year in ["2017"]:
    ptNLO       = shapesFile.Get("WJetsToLNu_{0}_gen_V_pT".format(year))
    ptNLO.Scale(2.09)#BR(W->qq)/BR(W->lnu)
    ptLO        = shapesFile.Get("WJets_{0}_gen_V_pT".format(year))
    ptLOkFac    = ptLO.Clone("WJets_{0}_gen_V_pT_corr".format(year))

    corr        = corrFile.Get("QCD_W")

    for i in range(1,ptLO.GetNbinsX()+1):
        pt          = ptLO.GetBinCenter(i)
        kFac        = corr.GetBinContent(corr.FindBin(pt))

        ptLOkFac.SetBinContent(i,ptLOkFac.GetBinContent(i)*kFac)

    plotPts(ptLO,ptLOkFac,ptNLO,"plots/QCD_W.png")


#NLO QCD corr with unc
for year in ["2017"]:
    corrFile    = r.TFile.Open("NLO_corrections.root")
    for V in ["Z","W"]:
        corr        = corrFile.Get("QCD_{0}".format(V))

        ewkNom = corrFile.Get("EWK_{0}_nominal".format(V))
        d1KUp  = corrFile.Get("EWK_{0}_d1K_NLO_up".format(V))
        d2KUp  = corrFile.Get("EWK_{0}_d2K_NLO_up".format(V))
        d1KDn  = corrFile.Get("EWK_{0}_d1K_NLO_down".format(V))
        d2KDn  = corrFile.Get("EWK_{0}_d2K_NLO_down".format(V))

        d1KUp.Divide(ewkNom)
        d2KUp.Divide(ewkNom)
        d1KDn.Divide(ewkNom)
        d2KDn.Divide(ewkNom)

        d1KUp = multiplyCorrs(d1KUp,corr)
        d2KUp = multiplyCorrs(d2KUp,corr)
        d1KDn = multiplyCorrs(d1KDn,corr)
        d2KDn = multiplyCorrs(d2KDn,corr)

        plotQCDCorr(corr,d1KUp,d2KUp,d1KDn,d2KDn,"plots/{0}_QCDcorrection.png".format(V))
    corrFile.Close()

#NLO EWK corr with unc
corrFile    = r.TFile.Open("NLO_corrections.root")
for V in ["Z","W"]:
    corr   = corrFile.Get("EWK_{0}_nominal".format(V))
    d1KUp  = corrFile.Get("EWK_{0}_d1kappa_EW_up".format(V))
    d2KUp  = corrFile.Get("EWK_{0}_{0}_d2kappa_EW_up".format(V))
    d3KUp  = corrFile.Get("EWK_{0}_{0}_d3kappa_EW_up".format(V))
    d1KDn  = corrFile.Get("EWK_{0}_d1kappa_EW_down".format(V))
    d2KDn  = corrFile.Get("EWK_{0}_{0}_d2kappa_EW_down".format(V))
    d3KDn  = corrFile.Get("EWK_{0}_{0}_d3kappa_EW_down".format(V))

    plotEWKCorr(corr,d1KUp,d2KUp,d3KUp,d1KDn,d2KDn,d3KDn,"plots/{0}_EWKcorrection.png".format(V))