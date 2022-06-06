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
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os 

matplotlib.use('Agg')
r.gROOT.SetBatch(True)
r.gStyle.SetOptFit(111)


def plotRPF(postfitShapesFile,odir,polyOrder):
    hPass = get2DPostfitPlot(postfitShapesFile,"qcd_{0}".format(polyOrder),"pass")
    hFail = get2DPostfitPlot(postfitShapesFile,"qcd","fail")

    hRpf  = hPass.Clone("hRPF")
    hRpf.Divide(hFail)
    hRpf.Scale(1000)

    hRpf, edges = hist2array(hRpf,return_edges=True)
    edgesMass = edges[0]
    edgesPt   = edges[1]
    #print(hRpf, edgesMass,edgesPt)

    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()
    hep.hist2dplot(hRpf, xbins=edgesMass, ybins=edgesPt,cbar=True, cmin=None, cmax=None)

    clb = ax.collections[-1].colorbar

    hep.cms.text("Work in progress",loc=0)
    clb.set_label('$R_{P/F}$ x $10^{3}$')

    ax.set_xlim([50,150])
    ax.set_ylim([450,2000])


    plt.xlabel("$M_{SD}$ [GeV]",horizontalalignment='right', x=1.0)
    plt.ylabel("$p_{T}$ [GeV]",horizontalalignment='right', y=1.0)
    ax.yaxis.set_tick_params(which='minor', left=False)    
    ax.yaxis.set_tick_params(which='minor', right=False)    

    print("Saving "+odir+"/RPF.pdf")
    plt.savefig(odir+"/RPF.pdf", bbox_inches='tight')
    plt.cla()
    plt.clf()


def plotRPFSurf(postfitShapesFile,odir,polyOrder,zmax=20.):
    hPass = get2DPostfitPlot(postfitShapesFile,"qcd_{0}".format(polyOrder),"pass")
    hFail = get2DPostfitPlot(postfitShapesFile,"qcd","fail")

    hRpf  = hPass.Clone("hRPF")
    hRpf.Divide(hFail)
    hRpf.Scale(1000)

    hRpf, edges = hist2array(hRpf,return_edges=True)
    edgesMass = edges[0]
    edgesPt   = edges[1]
    #print(hRpf, edgesMass,edgesPt)

    #plt.style.use([hep.style.CMS])
    f, ax = plt.subplots(subplot_kw={"projection": "3d"},figsize=(15,12))
    plt.rcParams.update({'font.size': 22})

    #Surface
    centersY = (edgesMass[:-1] + edgesMass[1:]) / 2
    centersX = (edgesPt[:-1] + edgesPt[1:]) / 2
    X, Y = np.meshgrid(centersX,centersY)
    surf = ax.plot_surface(X, Y, hRpf,linewidth=0, antialiased=False,cmap=cm.coolwarm)

    # Customize the z axis.
    ax.set_zlim(0, zmax)
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # Add a color bar which maps values to colors.
    clb = f.colorbar(surf,shrink=0.7)
    clb.set_label('$R_{P/F}$ x $10^{3}$')

    plt.ylabel("$M_{SD}$ [GeV]",horizontalalignment='right', x=1.0,labelpad=15,fontsize=22)
    plt.xlabel("$p_{T}$ [GeV]",horizontalalignment='right', y=1.0,labelpad=15,fontsize=22)
    ax.tick_params(axis='x', labelsize=22)
    ax.tick_params(axis='y', labelsize=22)
    ax.tick_params(axis='z', labelsize=22)
    ax.yaxis.set_tick_params(which='minor', left=False)    
    ax.yaxis.set_tick_params(which='minor', right=False)    

    ax.zaxis.set_tick_params(pad=15)    

    plt.savefig(odir+"/RPFsurf.pdf", bbox_inches='tight')
    plt.cla()
    plt.clf()


def plotTriggerEff(hPass,hTotal,year,luminosity,outFile,xlabel="$p_{T}$ [GeV]",ylabel="Trigger efficiency / 10 GeV"):
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

    plt.xlabel(xlabel, horizontalalignment='right', x=1.0)
    plt.ylabel(ylabel,horizontalalignment='right', y=1.0)

    lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
    hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    ax.set_ylim([0.5,1.02])
    plt.legend(loc="best")#loc = 'best'
    plt.tight_layout()

    print("Saving {0}".format(outFile))
    plt.savefig(outFile)
    plt.clf()

def mergeLoMassBins(hist,edges):
    #Merges first 3 pairs of mass bins into 10 GeV bins to combat ParticleNet mass regression sculpting
    #Converts hist to Events / GeV

    binsToRemove    = [1,3,5]

    newEdges        = np.delete(edges,binsToRemove)
    newHist         = np.delete(hist,binsToRemove)

    for binIdx in binsToRemove:
        newBinIdx   = int((binIdx-1)/2)
        newHist[newBinIdx]+=hist[binIdx]

    for i in range(len(newHist)):
        binWidth    = newEdges[i+1]-newEdges[i]
        newHist[i]  = newHist[i]/binWidth

    return newHist, [newEdges]


def plotVarStack(data,var,outFile,xTitle="",yTitle="",yRange=[],xRange=[],log=True,rebinX=1,luminosity="36.3",proj="X",mergeMassBins=False):
    histos  = []
    labels  = []
    edges   = []
    colors  = []
    histosData = []#we're assuming only one data_obs dataset
    edgesData  = []#it's still kept in array (with one element) to be similar to other processes
    labelsData = []
    data = sorted(data.items(), key=lambda x: x[1]["order"])#VERY HANDY, reads samples in order
    for sample, sample_cfg in data:
        tempFile = r.TFile.Open(sample_cfg["file"])
        if(proj=="X"):
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionX()
        else:
            h = tempFile.Get("{0}_{1}".format(sample,var)).ProjectionY()
        h.RebinX(rebinX)
        hist, edges = hist2array(h,return_edges=True)
        if(mergeMassBins):
            hist, edges = mergeLoMassBins(hist,edges[0])
        if("jetht" in sample.lower() or "data" in sample.lower()):
            histosData.append(hist)
            dataMax = max(hist)
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
    f, ax       = plt.subplots()
    centresData = (edgesData[0][:-1] + edgesData[0][1:])/2.
    errorsData  = np.sqrt(histosData[0])
    xerrorsData = []
    if(mergeMassBins):
        for i in range(len(edges[0])-1):
            xerror = (edges[0][i+1]-edges[0][i])/2.
            xerrorsData.append(xerror)

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
    if mergeMassBins:
        plt.errorbar(centresData,histosData[0], yerr=errorsData, xerr=xerrorsData, fmt='o',color="k",label = labelsData[0])    
    else:
        plt.errorbar(centresData,histosData[0], yerr=errorsData, fmt='o',color="k",label = labelsData[0])    
    if(log):
        ax.set_yscale("log")
    ax.legend()
    ax.set_ylabel(yTitle)
    ax.set_xlabel(xTitle)
    plt.xlabel(xTitle, horizontalalignment='right', x=1.0)
    plt.ylabel(yTitle,horizontalalignment='right', y=1.0)
    
    if(yRange):
        if(yRange[1]==None):
            yRange[1] = dataMax*1.5
        ax.set_ylim(yRange)
    else:
        ax.set_ylim([0,dataMax*1.5])
    if(xRange):
        ax.set_xlim(xRange)
    lumiText = luminosity + " $fb^{-1}\ (13 TeV)$"
    hep.cms.lumitext(text=lumiText, ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    plt.legend(loc=1,ncol=3,handletextpad=0.3)#loc = 'best'
    plt.tight_layout()

    print("Saving {0}".format(outFile))

    plt.savefig(outFile)

    plt.cla()
    plt.clf()

def getPoissonErrors(hist,binWidthDivision=False):
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
        if(binWidthDivision):
            errors_low.append(tempHist.GetBinErrorLow(i)/tempHist.GetBinWidth(i))
            errors_hi.append(tempHist.GetBinErrorUp(i)/tempHist.GetBinWidth(i))
        else:
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

def get2DPostfitPlot(file,process,region):
    f       = r.TFile.Open(file)
    hLow    = f.Get("{0}_LOW_postfit/{1}".format(region,process))
    hSig    = f.Get("{0}_SIG_postfit/{1}".format(region,process))
    hHigh   = f.Get("{0}_HIGH_postfit/{1}".format(region,process))
    h2      = merge_low_sig_high(hLow,hSig,hHigh,hName="h2_{0}_{1}".format(process,region))
    h2.SetDirectory(0)
    return h2

def get2DPrefitPlot(file,process,region):
    f       = r.TFile.Open(file)
    hLow    = f.Get("{0}_LOW_prefit/{1}".format(region,process))
    hSig    = f.Get("{0}_SIG_prefit/{1}".format(region,process))
    hHigh   = f.Get("{0}_HIGH_prefit/{1}".format(region,process))
    h2      = merge_low_sig_high(hLow,hSig,hHigh,hName="h2_{0}_{1}".format(process,region))
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

def divideByBinWidth(h):
    hist, edges = hist2array(h,return_edges=True)
    newHist     = []
    for i in range(len(hist)):
        binWidth    = edges[0][i+1]-edges[0][i]
        newHist.append(hist[i]/binWidth)

    return newHist,edges



def plotShapes(hData,hMC,uncBand,labelsMC,colorsMC,xlabel,outputFile,xRange=[],yRange=[],projectionText=""):
    dataErrors      = getPoissonErrors(hData,binWidthDivision=True)
    hData, edges    = divideByBinWidth(hData)
    centresData     = (edges[0][:-1] + edges[0][1:])/2.#Bin centres
    xerrorsData     = []

    for i in range(len(edges[0])-1):
        xerror = (edges[0][i+1]-edges[0][i])/2.
        xerrorsData.append(xerror)

    histosMC        = []
    for h in hMC:
        histosMC.append(divideByBinWidth(h)[0])


    plt.style.use([hep.style.CMS])
    #matplotlib.rcParams.update({'font.size': 30})
    f, axs = plt.subplots(2,1, sharex=True, sharey=False,gridspec_kw={'height_ratios': [4, 1],'hspace': 0.05})
    axs = axs.flatten()
    plt.sca(axs[0])

    hep.histplot(histosMC[:-1],edges[0],stack=True,ax=axs[0],label = labelsMC, histtype="fill",facecolor=colorsMC,edgecolor='black')
    plt.errorbar(centresData,hData, yerr=dataErrors, xerr=xerrorsData, fmt='o',color="k",label = "Data")

    for i in range(len(uncBand[0])):
        binWidth            = edges[0][i+1]-edges[0][i]
        uncBand[0][i]       = uncBand[0][i]/binWidth
        uncBand[1][i]       = uncBand[1][i]/binWidth

    uncBandLow = np.append(uncBand[0],[0],axis=0)
    uncBandHi  = np.append(uncBand[1],[0],axis=0)#Hack to get the last bin uncertainty to plot, since we're using step="post"

    plt.fill_between(edges[0],uncBandLow,uncBandHi,facecolor="none", hatch="xxx", edgecolor="grey", linewidth=0.0,step="post")

    axs[0].legend()
    plt.ylabel("Events/GeV",horizontalalignment='right', y=1.0)
    axs[1].set_ylabel("Pulls")

    if(xRange):
        axs[0].set_xlim(xRange)
    if(yRange):
        axs[0].set_ylim(yRange)
    else:
        yMaximum = max(hData)*1.5+10.
        axs[0].set_ylim([0.,yMaximum])

    if("16APV" in outputFile):
        lumi = 19.5
    elif("16" in outputFile):
        lumi = 16.8
    elif("17" in outputFile):
        lumi = 41.5
    elif("18" in outputFile):
        lumi = 59.8
    else:
        lumi = "NaN"

    lumiText = str(lumi)+ "$ fb^{-1} (13 TeV)$"    
    hep.cms.lumitext(lumiText)
    hep.cms.text("WiP",loc=0)
    plt.legend(loc=1,ncol=2)

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
    plt.tight_layout()
    plt.savefig(outputFile,bbox_inches="tight")
    plt.savefig(outputFile.replace("png","pdf"))

    plt.clf()
    plt.cla()

def printYields(data_proj,hMC,procs):
    for i,proc in enumerate(procs):
        yieldErr  = ctypes.c_double(1.)#ROOT thing
        procYield = hMC[i].IntegralAndError(1,hMC[i].GetNbinsX(),yieldErr,"")
        print("{0} & {1:.0f} & {2:.0f}".format(proc,procYield,yieldErr.value))
    
    yieldErr  = ctypes.c_double(1.)#ROOT thing
    procYield = data_proj.IntegralAndError(1,data_proj.GetNbinsX(),yieldErr,"")
    print("Data & {0:.0f} & {1:.0f}".format(procYield,yieldErr.value))

def plotPostfit(postfitShapesFile,region,odir,prefitTag=False):

    # labels              = ["Data","Multijet",r"t$\bar{t}$","WJets","ZJets"]
    # tags                = ["data_obs","qcd","TTbar","WJets_c","ZJets_bc"]
    # colors              = ["black","khaki","lightcoral","palegreen","blueviolet"]

    labels              = ["Data","Multijet","WJets","ZJets"]
    tags                = ["data_obs","qcd","WJets_c","ZJets_bc"]
    colors              = ["black","khaki","palegreen","blueviolet"]
    plotSlices          = True

    if(prefitTag):
        outFile = "MSD_prefit"
    else:
        outFile = "MSD_postfit"


    twoDShapes          = []

    dirRegion  = region
    polyOrder  = odir.split("/")[-2]

    #Merge sliced histograms
    for tag in tags:
        if(tag=="qcd" and region=="pass"):
            tag = tag+"_"+polyOrder
        if(prefitTag):
            twoDShape = get2DPrefitPlot(postfitShapesFile,tag,dirRegion)
        else:
            twoDShape = get2DPostfitPlot(postfitShapesFile,tag,dirRegion)
        twoDShapes.append(twoDShape)

    if(prefitTag):
        totalProcs  = get2DPrefitPlot(postfitShapesFile,"TotalProcs".format(region),dirRegion)
    else:
        totalProcs  = get2DPostfitPlot(postfitShapesFile,"TotalProcs".format(region),dirRegion)
    
    if(plotSlices):
        #Plot mSD
        for i in range(1,totalProcs.GetNbinsY()+1):
            projections         = []
            for j,twoDShape in enumerate(twoDShapes):
                proj        = twoDShape.ProjectionX(tags[j]+"_projx_{0}".format(i),i,i)
                projections.append(proj)
            totalProcs_proj     = totalProcs.ProjectionX("totalprocs_projx_{0}".format(i),i,i)
            projections.append(totalProcs_proj)
            uncBand_proj        = getUncBand(totalProcs_proj)
            projLowEdge         = int(totalProcs.GetYaxis().GetBinLowEdge(i))
            projUpEdge          = int(totalProcs.GetYaxis().GetBinUpEdge(i))
            projectionText      = "{0}".format(projLowEdge)+"<$p_{T}$<"+"{0} GeV".format(projUpEdge)

            plotShapes(projections[0],projections[1:],uncBand_proj,labels[1:],colors[1:],"$M_{SD}$ [GeV]","{0}/{1}_{2}_{3}.png".format(odir,outFile,region,i),xRange=[50,150],projectionText=projectionText)

    projections         = []
    for j,twoDShape in enumerate(twoDShapes):
        proj            = twoDShape.ProjectionX(tags[j]+"_projx")
        projections.append(proj)
    totalProcs_proj     = totalProcs.ProjectionX("totalprocs_projx")
    projections.append(totalProcs_proj)
    uncBand_proj        = getUncBand(totalProcs_proj)

    plotShapes(projections[0],projections[1:],uncBand_proj,labels[1:],colors[1:],"$M_{SD}$ [GeV]","{0}/{1}_{2}.png".format(odir,outFile,region),xRange=[50,150])

    tags.append("Total")
    print("Yields in {0}".format(region))
    printYields(projections[0],projections[1:],tags[1:])

def plotVJets(data,var,outFile,xTitle="",yTitle="",yRange=[],xRange=[],log=True,rebinX=1,luminosity="36.3",proj=""):
    histos = []
    labels  = []
    edges   = []
    colors  = []
    histosData = []#we're assuming only one data_obs dataset
    edgesData  = []#it's still kept in array (with one element) to be similar to other processes
    labelsData = []
    data = sorted(data.items(), key=lambda x: x[1]["order"])#VERY HANDY, reads samples in order
    for sample, sample_cfg in data:
        if not(("ZJets" in sample) or ("WJets" in sample)):
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

    hep.histplot(histos,edges[0],stack=False,ax=ax,label=labels,linewidth=3,histtype="step",color=colors)
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
    hep.cms.text("Simulation WiP",loc=0)
    plt.legend(loc="best",ncol=2)#loc = 'best'
    plt.tight_layout()

    print("Saving {0}".format(outFile))

    plt.savefig(outFile)

    plt.clf()

def plotLines(hList,labels,colors,xlabel,linestyles,outputFile,xRange=[],yRange=[],projectionText=""):
    histos        = []
    for h in hList:
        histo,edges = hist2array(h,return_edges=True)
        histos.append(histo)




    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()

    hep.histplot(histos,edges[0],stack=False,ax=ax,label = labels, histtype="step",color=colors,linewidth=3,linestyle=linestyles)

    ax.legend()
    plt.ylabel("Events/bin",horizontalalignment='right', y=1.0)

    if(xRange):
        ax.set_xlim(xRange)
    if(yRange):
        ax.set_ylim(yRange)
    else:
        yMaximum = max(map(max, histos))*1.5
        ax.set_ylim([0.,yMaximum])

    lumiText = "36.3$ fb^{-1} (13 TeV)$"    
    hep.cms.lumitext(lumiText)
    hep.cms.text("Simulation WiP",loc=0)
    plt.legend(loc=1,ncol=2)

    if(projectionText):
        plt.text(0.80, 0.85, projectionText, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)

    print("Saving ", outputFile)
    plt.tight_layout()
    plt.savefig(outputFile,bbox_inches="tight")

    plt.clf()
    plt.cla()

def plotVJetsInFit(postfitShapesFile,region,odir):

    labels              = ["WJets prefit","WJets postfit","ZJets prefit","ZJets postfit"]
    tags                = ["WJets","ZJets"]
    colors              = ["red","red","blue","blue"]
    linestyles          = ["-","--","-","--"]
    yRanges             = [[0,300],[0,300],[0,200],[0,70]]
    plotSlices          = True

    twoDShapes          = []

    taggingCat = "pass"
    dirRegion  = region

    if(region=="F"):
        yRanges    = [[0,7000],[0,7000],[0,3500],[0,1000]]

        #Merge sliced histograms
    for tag in tags:
        twoDShape = get2DPrefitPlot(postfitShapesFile,tag,dirRegion)
        twoDShapes.append(twoDShape)
        twoDShape = get2DPostfitPlot(postfitShapesFile,tag,dirRegion)
        twoDShapes.append(twoDShape)
        
    if(plotSlices):
        #Plot mSD
        for i in range(1,twoDShapes[0].GetNbinsY()+1):
            projections         = []
            for j,twoDShape in enumerate(twoDShapes):
                proj        = twoDShape.ProjectionX(labels[j]+"_projx_{0}".format(i),i,i)
                projections.append(proj)
            projLowEdge         = int(twoDShapes[0].GetYaxis().GetBinLowEdge(i))
            projUpEdge          = int(twoDShapes[0].GetYaxis().GetBinUpEdge(i))
            projectionText      = "{0}".format(projLowEdge)+"<$p_{T}$<"+"{0} GeV".format(projUpEdge)

            plotLines(projections,labels,colors,"M_{SD} [GeV]",linestyles,"{0}/VJets_{1}_{2}.png".format(odir,region,i),xRange=[50,150],yRange=yRanges[i-1],projectionText=projectionText)

def SFcompTight():
    #SF comp 2016
    gsp = [[450,550,700,900],#pt bin centers
    [1.19,1.09,1.14,1.12],#sf val
    [50,50,100,100],#pt bin width
    [0.15,0.11,0.12,0.09]]#sf err
    z = [[725],[0.90],[275],[[0.12],[0.15]]] #[ptbin center, SF val, ptbin width, [- err, + err]]
    lumiText = "2016 (13 TeV)"
    outFile  =  "SF_2016.pdf"
    compSF(gsp,z,outFile,lumiText)


    #SF comp 2017
    gsp = [[450,550,800],#pt bin centers
    [1.09,1.08,1.05],#sf val
    [50,50,200],#pt bin width
    [0.051,0.072,0.052]]#sf err
    z = [[725],[1.04],[275],[[0.15],[0.17]]]
    lumiText = "2017 (13 TeV)"
    outFile  =  "SF_2017.pdf"
    compSF(gsp,z,outFile,lumiText)


    # #SF comp 2018
    gsp = [[450,550,800],#pt bin centers
    [1.00,1.03,1.04],#sf val
    [50,50,200],#pt bin width
    [0.046,0.036,0.050]]#sf err
    z = [[725],[0.94],[275],[[0.16],[0.19]]]
    lumiText = "2018 (13 TeV)"
    outFile  =  "SF_2018.pdf"
    compSF(gsp,z,outFile,lumiText)


def SFcompYears():
    #SF comp 2016
    SF_T     = [0.80,0.90,1.12,1.02]
    errsUp_T = [0.16,0.17,0.15,0.12]
    errsDn_T = [0.15,0.18,0.13,0.11]

    SF_L     = [0.89,1.06,1.12,1.18]
    errsUp_L = [0.17,0.10,0.17,0.11]
    errsDn_L = [0.20,0.28,0.15,0.17]

    plt.style.use([hep.style.CMS])
    f, ax = plt.subplots()

    plt.sca(ax)
    plt.errorbar([2014.9,2015.9,2016.9,2017.9], SF_T, yerr=[errsDn_T,errsUp_T],fmt='ro',label="Tight WP (0.98)")
    plt.errorbar([2015.1,2016.1,2017.1,2018.1], SF_L, yerr=[errsDn_L,errsUp_L],fmt='bo',label="Loose WP (0.94)")


    plt.ylabel("Scale factor",horizontalalignment='right', y=1.0)
    plt.xlabel("",horizontalalignment='right', x=1.0)
    xLabels=["2016APV","2016","2017","2018"]
    xTicks=[2015,2016,2017,2018]
    ax.set_xticks(xTicks)
    ax.set_xticklabels(xLabels)
    ax.set_xlim(2014,2019)
    ax.set_ylim(0.5,1.6)
    ax.xaxis.set_tick_params(which='minor', top=False,bottom=False)    
    plt.axhline(y=1.0, color='gray', linestyle='--')
    plt.legend(ncol=2)

    hep.cms.lumitext("(13 TeV)")
    hep.cms.text("Work in progress",loc=0)

    print("Saving SF.pdf")
    plt.tight_layout()
    plt.savefig("results/plots/SF.pdf",bbox_inches="tight")

    plt.clf()
    plt.cla()

def printMCYields(data,region,year):
    data = sorted(data.items(), key=lambda x: x[1]["order"])
    print("----------")
    print("Yields in {0} - {1}".format(year,region))
    for sample, sample_cfg in data:
        f       = r.TFile.Open(sample_cfg["file"])
        hist    = f.Get("{0}_m_pT_{1}__nominal".format(sample,region))
        print("{0:10}\t{1:.0f}".format(sample,hist.Integral()))


if __name__ == '__main__':


    for year in ["2016","2016APV","2017","2018"]:
        odir = "results/plots/0.98/{0}/".format(year)

        if(year=="2016APV"):
            luminosity="19.5"
        elif(year=="2016"):
            luminosity="16.8"
        elif(year=="2017"):
            luminosity="41.5"
        elif(year=="2018"):
            luminosity="59.8"

        with open("plotConfigs/hadronic{0}.json".format(year)) as json_file:
            data = json.load(json_file)

            printMCYields(data,"pass",year)
            printMCYields(data,"fail",year)

            plotVarStack(data,"m_pT_pass__nominal","{0}/m_lin_pass_data.png".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[0,None],log=False,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_pass__nominal","{0}/m_lin_pass_data.pdf".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[0,None],log=False,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_fail__nominal","{0}/m_lin_fail_data.png".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[0,10**6],log=False,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_pass__nominal","{0}/m_pass_data.png".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[1,10**6],log=True,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_fail__nominal","{0}/m_fail_data.png".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[100,10**8],log=True,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_fail__nominal","{0}/m_fail_data.pdf".format(odir),xTitle="$M_{PNet}$ [GeV]",yTitle="Events / GeV",yRange=[100,10**8],log=True,xRange=[40,200],rebinX=1,luminosity=luminosity,mergeMassBins=True)
            plotVarStack(data,"m_pT_pass__nominal","{0}/pT_pass_data.png".format(odir),xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[1,10**7],log=True,xRange=[450,2000],rebinX=1,luminosity=luminosity,proj="Y")
            plotVarStack(data,"m_pT_fail__nominal","{0}/pT_fail_data.png".format(odir),xTitle="$p_{T}$ [GeV]",yTitle="Events / 50 GeV",yRange=[100,10**9],log=True,xRange=[450,2000],rebinX=1,luminosity=luminosity,proj="Y")


            f = r.TFile.Open(data["data_obs"]["file"])#"JetHT16.root")
            print(data["data_obs"]["file"])
            hTotal = f.Get("data_obs_pT0noTriggers_nom")
            hPass  = f.Get("data_obs_pT0triggersAll_nom")
            eff = r.TEfficiency(hPass,hTotal)
            eff.SetName("trig_eff")
            #g   = r.TFile.Open("data/trig_eff_{0}.root".format(year),"RECREATE")
            # g   = r.TFile.Open("trig_eff_{0}.root".format(year),"RECREATE")
            # g.cd()
            # eff.Write()
            # g.Close()

            plotTriggerEff(hPass,hTotal,year,luminosity,"{0}/Trig_eff_{1}.pdf".format(odir,year))

            hTotal = f.Get("data_obs_noTriggers_nom").ProjectionX()
            hPass  = f.Get("data_obs_triggersAll_nom").ProjectionX()
            hPass.RebinX(5)
            hTotal.RebinX(5)
            plotTriggerEff(hPass,hTotal,year,luminosity,"{0}/Trig_eff_M_{1}.png".format(odir,year),xlabel="$M_{PNet}$ [GeV]",ylabel="Trigger efficiency")


        with open("plotConfigs/Vjets{0}.json".format(year)) as json_file:
            data = json.load(json_file)
            plotVJets(data,"VpT_fail_nom","{0}/vpT_fail_lin.png".format(odir),xTitle="$Gen V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=False,xRange=[0,1500],yRange=[1.,5500],rebinX=1,luminosity=luminosity)
            plotVJets(data,"VpT_pass_nom","{0}/vpT_pass_lin.png".format(odir),xTitle="$Gen V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=False,xRange=[0,1500],yRange=[1.,300],rebinX=1,luminosity=luminosity)
            plotVJets(data,"VpT_fail_nom","{0}/vpT_fail.png".format(odir),xTitle="$Gen V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=True,xRange=[0,1500],yRange=[1.,10**5],rebinX=1,luminosity=luminosity)
            plotVJets(data,"VpT_pass_nom","{0}/vpT_pass.png".format(odir),xTitle="$Gen V p_{T}$ [GeV]",yTitle="Events / 10 GeV",log=True,xRange=[0,1500],yRange=[1.,10**3],rebinX=1,luminosity=luminosity)


            plotVJets(data,"m_pT_fail__nominal","{0}/mVJets_fail_lin.png".format(odir),xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",log=False,xRange=[40,150],yRange=[0,5*10**4],rebinX=1,luminosity=luminosity,proj="X")
            plotVJets(data,"m_pT_pass__nominal","{0}/mVJets_pass_lin.png".format(odir),xTitle="$M_{SD}$ [GeV]",yTitle="Events / 5 GeV",log=False,xRange=[40,150],yRange=[0,1200],rebinX=1,luminosity=luminosity,proj="X")



    #Postfit T
    cmsswArea       = "CMSSW_10_6_14/src/"
    bestOrders      = {"SF16_T":"2","SF16APV_T":"3","SF17_T":"2","SF18_T":"2"}
    for workingArea in ["SF16_T","SF16APV_T","SF17_T","SF18_T"]:
        polyOrder       = bestOrders[workingArea]
        baseDir         = cmsswArea + workingArea + "/" + polyOrder + "_area/"
        fitFile         = baseDir+"postfitshapes_s.root"
        Path("results/plots/{0}/{1}/".format(workingArea,polyOrder)).mkdir(parents=True, exist_ok=True)

        try:
            plotPostfit(fitFile,"pass","results/plots/{0}/{1}/".format(workingArea,polyOrder))
            plotPostfit(fitFile,"fail","results/plots/{0}/{1}/".format(workingArea,polyOrder))
            plotRPF(fitFile,"results/plots/{0}/{1}/".format(workingArea,polyOrder),polyOrder)
            plotRPFSurf(fitFile,"results/plots/{0}/{1}/".format(workingArea,polyOrder),polyOrder,zmax=5.)
        except:
            print("Couldn't plot for {0} {1}".format(workingArea,polyOrder))

    #Postfit L
    cmsswArea       = "CMSSW_10_6_14/src/"
    bestOrders      = {"SF16_L":"2","SF16APV_L":"2","SF17_L":"2","SF18_L":"4"}
    for workingArea in ["SF16_L","SF16APV_L","SF17_L","SF18_L"]:
        polyOrder   = bestOrders[workingArea]
        baseDir         = cmsswArea + workingArea + "/" + polyOrder + "_area/"
        fitFile         = baseDir+"postfitshapes_s.root"
        Path("results/plots/{0}/{1}/".format(workingArea,polyOrder)).mkdir(parents=True, exist_ok=True)
        try:
            plotPostfit(fitFile,"pass","results/plots/{0}/{1}/".format(workingArea,polyOrder))
            plotPostfit(fitFile,"fail","results/plots/{0}/{1}/".format(workingArea,polyOrder))
            plotRPF(fitFile,"results/plots/{0}/{1}/".format(workingArea,polyOrder),polyOrder)
            plotRPFSurf(fitFile,"results/plots/{0}/{1}/".format(workingArea,polyOrder),polyOrder,zmax=5.)
        except:
            print("Couldn't plot for {0} {1}".format(workingArea,polyOrder))

    #plotVJetsInFit(fitFile,"T","results/plots/{0}/r_fit/")
    #plotVJetsInFit(fitFile,"F","results/plots/{0}/r_fit/")

    SFcompYears()
