import matplotlib
matplotlib.use('Agg')

import ROOT as r
from optparse import OptionParser
from time import sleep
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplhep as hep
from root_numpy import hist2array
import ctypes

matplotlib.use('Agg')
r.gROOT.SetBatch(True)
r.gStyle.SetOptFit(111)

def plotTriggerEff(hPass,hTotal,year,luminosity,outFile):
    TEff   = r.TEfficiency(hPass,hTotal)
    effs   = []
    errsUp = []
    errsDn = []
    binsX  = []
    for i in range(1,hPass.GetNbinsX()+1):
        binX  = hPass.GetBinCenter(i)
        eff   = TEff.GetEfficiency(i)
        errUp = TEff.GetEfficiencyErrorUp(i)
        errDn = TEff.GetEfficiencyErrorLow(i)

        binsX.append(binX)
        effs.append(eff)
        errsDn.append(errDn)
        errsUp.append(errUp)


    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()
    plt.errorbar(binsX, effs, yerr=[errsDn,errsUp], fmt='o',color="black",label="{0} Data trigger efficiency".format(year))

    plt.xlabel("$p_{T}$ [GeV]", horizontalalignment='right', x=1.0)
    plt.ylabel("Trigger efficiency / 10 GeV",horizontalalignment='right', y=1.0)

    lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
    hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    ax.set_ylim([0.92,1.02])
    plt.legend(loc="best")#loc = 'best'
    plt.tight_layout()

    print("Saving {0}".format(outFile))
    plt.savefig(outFile)
    plt.clf()

def plotVarStack(data,var,outFile,xTitle="",yTitle="",yRange=[],xRange=[],log=True,rebinX=1,luminosity="35.9",proj="X"):
    histos = []
    labels  = []
    edges   = []
    colors  = []
    histosData = []#we're assuming only one data_obs dataset
    edgesData  = []#it's still kept in array (with one element) to be similar to other processes
    labelsData = []
    data = sorted(data.items(), key=lambda x: x[1]["order"])#VERY HANDY, reads samples in order
    for sample, sample_cfg in data:
        print(sample)
        tempFile = r.TFile.Open(sample_cfg["file"])
        if(proj=="X"):
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionX()
        else:
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionY()
        h.RebinX(rebinX)
        hist, edges = hist2array(h,return_edges=True)
        if("jetht" in sample.lower() or "data" in sample.lower()):
            histosData.append(hist)
            edgesData.append(edges[0])
            labelsData.append(sample_cfg["label"])
            continue  
        else:
            histos.append(hist)
            edges.append(edges[0])
            labels.append(sample_cfg["label"])
            colors.append(sample_cfg["color"])
            if(sample_cfg["label"]=="ttbar"):
                labels[-1]=r"t$\bar{t}$"#json restrictions workaround


    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()
    centresData = (edgesData[0][:-1] + edgesData[0][1:])/2.
    errorsData  = np.sqrt(histosData[0])

    #----QCD scaling to data----#
    hDataMinusBkgs = histosData[0]
    QCDposition    = -1
    for i,hBkg in enumerate(histos):
        if("Multijet" in labels[i]):
            QCDposition = i
            continue
        else:
            hDataMinusBkgs = np.subtract(hDataMinusBkgs,hBkg)
    if(QCDposition==-1):
        print("No QCD in bkg, skipping reweighting")
    else:
        scale = np.sum(hDataMinusBkgs)/np.sum(histos[QCDposition])
        print("QCD scale {0}".format(scale))
        histos[QCDposition] = histos[QCDposition]*scale
    #--------------------------#

    hep.histplot(histos,edges[0],stack=True,ax=ax,label=labels,linewidth=1,histtype="fill",facecolor=colors,edgecolor='black')
    plt.errorbar(centresData,histosData[0], yerr=errorsData, fmt='o',color="k",label = labelsData[0])    
    if(log):
        ax.set_yscale("log")
    ax.legend()
    ax.set_ylabel(yTitle)
    ax.set_xlabel(xTitle)
    plt.xlabel(xTitle, horizontalalignment='right', x=1.0)
    plt.ylabel(yTitle,horizontalalignment='right', y=1.0)
    if(yRange):
        ax.set_ylim(yRange)
    if(xRange):
        ax.set_xlim(xRange)
    lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
    hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    plt.tight_layout()
    plt.legend(loc="best",ncol=2)#loc = 'best'

    print("Saving {0}".format(outFile))

    plt.savefig(outFile)

    plt.clf()

def getPoissonErrors(hist):
    hist.SetBinErrorOption(1)

    #This is needed due to some nasty float precision inaccuracy causing some data content to be 0.9999998
    #The kPoisson error does not get calculated correctly in that case for some reason
    tempHist   = hist.Clone("tempHist_forErrs")
    tempHist.Reset()
    tempHist.SetBinErrorOption(1)

    errors_low = []
    errors_hi  = []
    for i in range(1,hist.GetNbinsX()+1):
        tempHist.SetBinContent(i,int(round(hist.GetBinContent(i))))
        #print(int(hist.GetBinContent(i)),tempHist.GetBinErrorLow(i),tempHist.GetBinErrorUp(i))
        errors_low.append(tempHist.GetBinErrorLow(i))
        errors_hi.append(tempHist.GetBinErrorUp(i))

    return [errors_low,errors_hi]

def rebinHisto(hModel,hToRebin,name,scale=1.0):
    hRes = hModel.Clone(name)
    hRes.Reset()
    xaxis = hToRebin.GetXaxis()
    yaxis = hToRebin.GetYaxis()
    xaxis_re = hRes.GetXaxis()
    yaxis_re = hRes.GetYaxis()
    for i in range(1,hToRebin.GetNbinsX()+1):
        for j in range(1,hToRebin.GetNbinsY()+1):
            x = xaxis.GetBinCenter(i)
            y = yaxis.GetBinCenter(j)
            i_re = xaxis_re.FindBin(x)
            j_re = yaxis_re.FindBin(y)
            value = hToRebin.GetBinContent(i,j)
            if(value<0.):
                value = 0.
            err = hToRebin.GetBinError(i,j)
            err_re = np.sqrt(hRes.GetBinError(i_re,j_re)*hRes.GetBinError(i_re,j_re)+err*err)
            hRes.Fill(x,y,value)
            hRes.SetBinError(i_re,j_re,err_re)
    hRes.Scale(scale)
    hRes.SetDirectory(0)
    return hRes

def get_binning_x(hLow,hSig,hHigh):
    bins = []
    for i in range(1,hLow.GetNbinsX()+1):
        bins.append(hLow.GetXaxis().GetBinLowEdge(i))
    for i in range(1,hSig.GetNbinsX()+1):
        bins.append(hSig.GetXaxis().GetBinLowEdge(i))
    for i in range(1,hHigh.GetNbinsX()+2):#low edge of overflow is high edge of last bin
        bins.append(hHigh.GetXaxis().GetBinLowEdge(i))
    bins = np.array(bins,dtype='float64')
    return bins

def get_binning_y(hLow,hSig,hHigh):
    #histos should have same binning in Y
    bins = []
    for i in range(1,hLow.GetNbinsY()+2):
        bins.append(hLow.GetYaxis().GetBinLowEdge(i))
    bins = np.array(bins,dtype='float64')
    return bins

def merge_low_sig_high(hLow,hSig,hHigh,hName="temp"):
    n_x_low     = hLow.GetNbinsX()
    n_x_sig     = hSig.GetNbinsX()
    n_x_high    = hHigh.GetNbinsX()
    n_x         = n_x_low + n_x_sig + n_x_high
    n_y         = hLow.GetNbinsY()#assumes Y bins are the same
    bins_x      = get_binning_x(hLow,hSig,hHigh)
    bins_y      = get_binning_y(hLow,hSig,hHigh)
    h_res       = r.TH2F(hName,"",n_x,bins_x,n_y,bins_y)
    for i in range(1,n_x_low+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+0,j,hLow.GetBinContent(i,j))
            h_res.SetBinError(i+0,j,hLow.GetBinError(i,j))

    for i in range(1,n_x_sig+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+n_x_low,j,hSig.GetBinContent(i,j))
            h_res.SetBinError(i+n_x_low,j,hSig.GetBinError(i,j))

    for i in range(1,n_x_high+1):
        for j in range(1,n_y+1):
            h_res.SetBinContent(i+n_x_sig+n_x_low,j,hHigh.GetBinContent(i,j))
            h_res.SetBinError(i+n_x_sig+n_x_low,j,hHigh.GetBinError(i,j))
    return h_res

def get2DPostfitPlot(file,process,region,tagging):
    #regoin LL/TT, tagging fail/pass
    #process 16_TTbar_bqq, data_obs, qcd
    f       = r.TFile.Open(file)
    hLow    = f.Get("{0}_LOW_{1}_postfit/{2}".format(tagging,region,process))
    hSig    = f.Get("{0}_SIG_{1}_postfit/{2}".format(tagging,region,process))
    hHigh   = f.Get("{0}_HIGH_{1}_postfit/{2}".format(tagging,region,process))
    h2      = merge_low_sig_high(hLow,hSig,hHigh,hName="h2_{0}_{1}_{2}".format(process,region,tagging))
    h2.SetDirectory(0)
    return h2

def get2DPrefitPlot(file,process,region,tagging):
    #regoin LL/TT, tagging fail/pass
    #process 16_TTbar_bqq, data_obs, qcd
    f       = r.TFile.Open(file)
    hLow    = f.Get("{0}_LOW_{1}_prefit/{2}".format(tagging,region,process))
    hSig    = f.Get("{0}_SIG_{1}_prefit/{2}".format(tagging,region,process))
    hHigh   = f.Get("{0}_HIGH_{1}_prefit/{2}".format(tagging,region,process))
    h2      = merge_low_sig_high(hLow,hSig,hHigh,hName="h2_{0}_{1}_{2}".format(process,region,tagging))
    h2.SetDirectory(0)
    return h2

def getUncBand(totalHistos):
    yLo = []
    yUp = []
    for i in range(1,totalHistos.GetNbinsX()+1):
        errLo  = totalHistos.GetBinErrorLow(i)
        errUp  = totalHistos.GetBinErrorUp(i)
        mcPred = totalHistos.GetBinContent(i)
        yLo.append(mcPred-errLo)
        yUp.append(mcPred+errUp)
    return np.array(yLo), np.array(yUp)

def calculatePull(hData,dataErrors,hTotBkg,uncBand):
    pulls = []
    for i,dataYield in enumerate(hData):
        mcYield     = hTotBkg[i]
        diff        = dataYield-mcYield
        dataErr     = np.sqrt(dataYield)
        if(dataYield>=mcYield):
            dataErr = dataErrors[0][i]#ErrorLo
            mcErr   = uncBand[1][i]-mcYield#ErrorUp
        else:
            dataErr = dataErrors[1][i]#ErrorUp
            mcErr   = uncBand[0][i]-mcYield#ErrorLo

        sigma =  np.sqrt(dataErr*dataErr+mcErr*mcErr)
        pull        = diff/sigma
        pulls.append(pull)

    return np.array(pulls)

def plotShapes(hData,hMC,uncBand,labelsMC,colorsMC,xlabel,outputFile,xRange=[],yRange=[],projectionText=""):
    print(outputFile)
    dataErrors      = getPoissonErrors(hData)
    hData, edges    = hist2array(hData,return_edges=True)
    centresData     = (edges[0][:-1] + edges[0][1:])/2.#Bin centres
    xerrorsData     = []

    for i in range(len(edges[0])-1):
        xerror = (edges[0][i+1]-edges[0][i])/2.
        xerrorsData.append(xerror)

    histosMC        = []
    for h in hMC:
        histosMC.append(hist2array(h,return_edges=True)[0])




    plt.style.use([hep.style.CMS])
    #matplotlib.rcParams.update({'font.size': 30})
    f, axs = plt.subplots(2,1, sharex=True, sharey=False,gridspec_kw={'height_ratios': [4, 1],'hspace': 0.05})
    axs = axs.flatten()
    plt.sca(axs[0])

    hep.histplot(histosMC[:-1],edges[0],stack=True,ax=axs[0],label = labelsMC, histtype="fill",facecolor=colorsMC,edgecolor='black')
    plt.errorbar(centresData,hData, yerr=dataErrors, xerr=xerrorsData, fmt='o',color="k",label = "Data")

    uncBandLow = np.append(uncBand[0],[0],axis=0)
    uncBandHi = np.append(uncBand[1],[0],axis=0)#Hack to get the last bin uncertainty to plot, since we're using step="post"
    plt.fill_between(edges[0],uncBandLow,uncBandHi,facecolor="none", hatch="xxx", edgecolor="grey", linewidth=0.0,step="post")

    axs[0].legend()
    plt.ylabel("Events/bin",horizontalalignment='right', y=1.0)
    axs[1].set_ylabel("Pulls")

    if(xRange):
        axs[0].set_xlim(xRange)
    if(yRange):
        axs[0].set_ylim(yRange)
    else:
        yMaximum = max(hData)*1.5+10.
        axs[0].set_ylim([0.,yMaximum])

    lumiText = "138$fb^{-1} (13 TeV)$"    
    hep.cms.lumitext(lumiText)
    hep.cms.text("WiP",loc=0)
    plt.legend(loc='best',ncol=2)

    if(projectionText):
        plt.text(0.60, 0.15, projectionText, horizontalalignment='center',verticalalignment='center',transform=axs[0].transAxes)


    plt.sca(axs[1])#switch to lower pad
    #axs[1].axhline(y=0.0, xmin=0, xmax=1, color="r")
    axs[1].axhline(y=1.0, xmin=0, xmax=1, color="grey",linestyle="--",alpha=0.5)
    axs[1].axhline(y=-1.0, xmin=0, xmax=1, color="grey",linestyle="--",alpha=0.5)
    axs[1].axhline(y=2.0, xmin=0, xmax=1, color="grey",linestyle="-.",alpha=0.5)
    axs[1].axhline(y=-2.0, xmin=0, xmax=1, color="grey",linestyle="-.",alpha=0.5)
    axs[1].set_ylim([-2.5,2.5])
    plt.xlabel(xlabel,horizontalalignment='right', x=1.0)

    pulls = calculatePull(hData,dataErrors,histosMC[-1],uncBand)
    hep.histplot(pulls,edges[0],ax=axs[1],linewidth=1,histtype="fill",facecolor="grey",edgecolor='black')

    print("Saving ", outputFile)
    plt.savefig(outputFile,bbox_inches="tight")
    #plt.savefig(outputFile.replace("png","pdf"))

    plt.clf()

def printYields(data_proj,hMC,procs):
    for i,proc in enumerate(procs):
        yieldErr  = ctypes.c_double(1.)#ROOT thing
        procYield = hMC[i].IntegralAndError(1,hMC[i].GetNbinsX(),yieldErr,"")
        print("{0}\t{1:.0f} +/- {2:.0f}".format(proc,procYield,yieldErr.value))
    
    yieldErr  = ctypes.c_double(1.)#ROOT thing
    procYield = data_proj.IntegralAndError(1,data_proj.GetNbinsX(),yieldErr,"")
    print("Data\t{0:.0f} +/- {1:.0f}".format(procYield,yieldErr.value))


def plotPostfit():
    postfitShapesFile  = "/afs/cern.ch/user/m/mrogulji/UL_X_YH/Zbb_SF/CMSSW_10_6_14/src/2DAlphabet/Zbb_SF_22_16/postfitshapes_s.root"
    regionsToPlot      = ["T","F"]
    labelsMC           = ["Multijet",r"t$\bar{t}$","WJets","ZJets"]
    colorsMC           = ["khaki","lightcoral","palegreen","blueviolet"]
    plotSlices         = True


    for region in regionsToPlot:

        taggingCat = "pass"
        dirRegion  = region

        if(region=="F"):
            taggingCat = "fail"
            dirRegion  = "T"

        #Merge sliced histograms
        dataShape   = get2DPostfitPlot(postfitShapesFile,"data_obs",dirRegion,taggingCat)
        qcdShape    = get2DPostfitPlot(postfitShapesFile,"qcd",dirRegion,taggingCat)
        TTShape     = get2DPostfitPlot(postfitShapesFile,"TTbar",dirRegion,taggingCat)
        WJetsShape  = get2DPostfitPlot(postfitShapesFile,"WJets",dirRegion,taggingCat)
        ZJetsShape  = get2DPostfitPlot(postfitShapesFile,"ZJets",dirRegion,taggingCat)
        totalProcs  = get2DPostfitPlot(postfitShapesFile,"TotalProcs".format(region),dirRegion,taggingCat)

        #Get prefit for yields
        data_proj_pre   = get2DPrefitPlot(postfitShapesFile,"data_obs",dirRegion,taggingCat).ProjectionX()
        qcd_proj_pre    = get2DPrefitPlot(postfitShapesFile,"qcd",dirRegion,taggingCat).ProjectionX()
        TT_proj_pre     = get2DPrefitPlot(postfitShapesFile,"TTbar",dirRegion,taggingCat).ProjectionX()
        WJets_proj_pre  = get2DPrefitPlot(postfitShapesFile,"WJets",dirRegion,taggingCat).ProjectionX()
        ZJets_proj_pre  = get2DPrefitPlot(postfitShapesFile,"ZJets",dirRegion,taggingCat).ProjectionX()
        totalProcs_pre  = get2DPrefitPlot(postfitShapesFile,"TotalProcs".format(region),dirRegion,taggingCat).ProjectionX()
        hMC_pre         = [qcd_proj_pre,TT_proj_pre,WJets_proj_pre,ZJets_proj_pre,totalProcs_pre]
        uncBand_proj_pre= getUncBand(totalProcs_pre)
        
        if(plotSlices):
            #Plot mSD
            for i in range(1,dataShape.GetNbinsY()+1):
                data_proj           = dataShape.ProjectionX("data_projx_{0}".format(i),i,i)
                qcd_proj            = qcdShape.ProjectionX("qcd_projx_{0}".format(i),i,i)
                ttbar_proj          = TTShape.ProjectionX("ttbar_projx_{0}".format(i),i,i)
                wjets_proj          = WJetsShape.ProjectionX("wjets_projx_{0}".format(i),i,i)
                zjets_proj          = ZJetsShape.ProjectionX("zjets_projx_{0}".format(i),i,i)
                totalProcs_proj     = totalProcs.ProjectionX("totalprocs_projx_{0}".format(i),i,i)
                hMC                 = [qcd_proj,ttbar_proj,wjets_proj,zjets_proj,totalProcs_proj]
                uncBand_proj        = getUncBand(totalProcs_proj)
                projLowEdge         = int(dataShape.GetYaxis().GetBinLowEdge(i))
                projUpEdge          = int(dataShape.GetYaxis().GetBinUpEdge(i))
                projectionText      = "{0}".format(projLowEdge)+"<$p_{T}$<"+"{0} GeV".format(projUpEdge)

                plotShapes(data_proj,hMC,uncBand_proj,labelsMC,colorsMC,"$M_{SD}$ [GeV]","plots/2016/postfit/MSD_{0}_{1}.png".format(region,i),xRange=[50,150],projectionText=projectionText)
            #Plot pT TBD


        data_proj           = dataShape.ProjectionX("data_projx")
        qcd_proj            = qcdShape.ProjectionX("qcd_projx")
        ttbar_proj          = TTShape.ProjectionX("ttbar_projx")
        wjets_proj          = WJetsShape.ProjectionX("wjets_projx")
        zjets_proj          = ZJetsShape.ProjectionX("zjets_projx")
        totalProcs_proj     = totalProcs.ProjectionX("totalprocs_projx")
        hMC                 = [qcd_proj,ttbar_proj,wjets_proj,zjets_proj,totalProcs_proj]
        procs               = ["Multijet","TTbar","WJets","Zjets","Total"]
        uncBand_proj        = getUncBand(totalProcs_proj)

        print("Yields in {0}".format(region))
        printYields(data_proj,hMC,procs)
        printYields(data_proj,hMC_pre,procs)
        plotShapes(data_proj,hMC,uncBand_proj,labelsMC,colorsMC,"$M_{SD}$ [GeV]","plots/2016/postfit/MSD_{0}.png".format(region),xRange=[50,150])



            # data_proj    = dataShape.ProjectionY("data_projy")
            # qcd_proj     = qcdShape.ProjectionY("qcd_projy")
            # ttbar_proj   = TTshape.ProjectionY("ttbar_projy")
            # totalBkg_proj= totalBkg.ProjectionY("totalbkg_projy")
            # data_proj    = dataShape.ProjectionY("data_projy")
            # uncBand_proj = getUncBand(totalBkg_proj)


            # signalHistos     = getSignals(massPointsToPlot,dirRegion)
            # rebinnedSignal   = []
            # for i in range(len(massPointsToPlot)):
            #     rebinnedSignal.append(rebinHisto(dataShape,signalHistos[i],"{0}_{1}_rebinned".format(massPointsToPlot[i],region),scale=1.0).ProjectionY("{0}_{1}_projy".format(massPointsToPlot[i],region)))
            # if("NAL" in region):
            #     rebinnedSignal = []
            # plotShapes(data_proj,qcd_proj,ttbar_proj,totalBkg_proj,uncBand_proj,rebinnedSignal,labelsSignal,["darkred","blue","green"],"$M_{JJ}$ [GeV]","hadronicPostfitPlots/{0}_MJJ.png".format(region),xRange=[800.,4000.],yRange=[0.,ymax[region]])

def plotVJets(data,var,outFile,xTitle="",yTitle="",yRange=[],xRange=[],log=True,rebinX=1,luminosity="35.9",proj=""):
    histos = []
    labels  = []
    edges   = []
    colors  = []
    histosData = []#we're assuming only one data_obs dataset
    edgesData  = []#it's still kept in array (with one element) to be similar to other processes
    labelsData = []
    data = sorted(data.items(), key=lambda x: x[1]["order"])#VERY HANDY, reads samples in order
    for sample, sample_cfg in data:
        if not(("ZJets" in samples) or ("WJets" in sample)):
            continue

        tempFile = r.TFile.Open(sample_cfg["file"])
        if(proj=="X"):
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionX()
        elif(proj=="Y"):
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionY()
        else:
            h = tempFile.Get("{0}_{1}".format(sample,var))
        h.RebinX(rebinX)
        hist, edges = hist2array(h,return_edges=True)
        histos.append(hist)
        edges.append(edges[0])
        labels.append(sample_cfg["label"])
        colors.append(sample_cfg["color"])

    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()

    hep.histplot(histos,edges[0],stack=True,ax=ax,label=labels,linewidth=1,histtype="fill",facecolor=colors,edgecolor='black')
    if(log):
        ax.set_yscale("log")
    ax.legend()
    ax.set_ylabel(yTitle)
    ax.set_xlabel(xTitle)
    plt.xlabel(xTitle, horizontalalignment='right', x=1.0)
    plt.ylabel(yTitle,horizontalalignment='right', y=1.0)
    if(yRange):
        ax.set_ylim(yRange)
    if(xRange):
        ax.set_xlim(xRange)
    lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
    hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    plt.tight_layout()
    plt.legend(loc="best",ncol=2)#loc = 'best'

    print("Saving {0}".format(outFile))

    plt.savefig(outFile)

    plt.clf()


if __name__ == '__main__':
    #Postfit
    # plotPostfit()

    #Control vars
    parser = OptionParser()
    parser.add_option('-j', '--json', metavar='IFILE', type='string', action='store',
                default   =   '',
                dest      =   'json',
                help      =   'Json file containing names, paths to histograms, xsecs etc.')
    parser.add_option('-y', '--year', metavar='IFILE', type='string', action='store',
            default   =   '',
            dest      =   'year',
            help      =   'Json file containing names, paths to histograms, xsecs etc.')
    (options, args) = parser.parse_args()
    odir = "results/plots/{0}/".format(options.year)

    year = options.year
    if(year=="2016"):
        luminosity="36.3"
    elif(year=="2017"):
        luminosity="41.5"
    elif(year=="2018"):
        luminosity="59.8"
    elif(year=="RunII"):
        luminosity="138"
    else:
        print("Year not specified")
        luminosity="0"

    with open(options.json) as json_file:
        data = json.load(json_file)

        plotVarStack(data,"m_pT_T_nom","plots/2016/T_lin_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[],log=False,xRange=[40,200],rebinX=5,luminosity="36.3")
        plotVarStack(data,"m_pT_L_nom","plots/2016/L_lin_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[],log=False,xRange=[40,200],rebinX=5,luminosity="36.3")
        plotVarStack(data,"m_pT_F_nom","plots/2016/F_lin_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[],log=False,xRange=[40,200],rebinX=5,luminosity="36.3")

        plotVarStack(data,"m_pT_T_nom","plots/2016/T_pT_lin_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 5 GeV",yRange=[],log=False,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")
        plotVarStack(data,"m_pT_L_nom","plots/2016/L_pT_lin_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[],log=False,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")
        plotVarStack(data,"m_pT_F_nom","plots/2016/F_pT_lin_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[],log=False,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")

        plotVarStack(data,"m_pT_T_nom","plots/2016/T_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[1,10**5],log=True,xRange=[40,200],rebinX=5,luminosity="36.3")
        plotVarStack(data,"m_pT_L_nom","plots/2016/L_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[10,10**5],log=True,xRange=[40,200],rebinX=5,luminosity="36.3")
        plotVarStack(data,"m_pT_F_nom","plots/2016/F_data.png",xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",yRange=[100,10**7],log=True,xRange=[40,200],rebinX=5,luminosity="36.3")


        plotVarStack(data,"m_pT_T_nom","plots/2016/T_pT_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[],log=True,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")
        plotVarStack(data,"m_pT_L_nom","plots/2016/L_pT_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[],log=True,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")
        plotVarStack(data,"m_pT_F_nom","plots/2016/F_pT_data.png",xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[],log=True,xRange=[450,2000],rebinX=5,luminosity="36.3",proj="Y")


        f = r.TFile.Open(data["data_obs"]["file"])#"JetHT16.root")
        hTotal = f.Get("data_obs_pT0noTriggers_nom")
        hPass  = f.Get("data_obs_pT0triggersAll_nom")
        eff = r.TEfficiency(hPass,hTotal)
        eff.SetName("trig_eff")
        print(eff.GetName())
        g   = r.TFile.Open("data/trig_eff_{0}.root".format(year),"RECREATE")
        g.cd()
        eff.Write()
        g.Close()

        plotTriggerEff(hPass,hTotal,year,luminosity,"plots/{0}/Trig_eff_{0}.png".format(year))



    plotVJets(data,"VpT_F_nom","plots/2016/F_vpT.png",xTitle="$V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=False,rebinX=1,luminosity="35.9")
    plotVJets(data,"VpT_L_nom","plots/2016/L_vpT.png",xTitle="$V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=False,rebinX=1,luminosity="35.9")
    plotVJets(data,"VpT_T_nom","plots/2016/T_vpT.png",xTitle="$V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=False,rebinX=1,luminosity="35.9")



