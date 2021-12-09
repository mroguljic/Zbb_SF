import ROOT as r

r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(0000)

def plotHisto(histoname,sample):
    f = r.TFile.Open("../results/templates/2016/scaled/{0}16.root".format(sample))
    h = f.Get("{0}_{1}".format(sample,histoname))
    print("{0}_{1}".format(sample,histoname))
    h.SetDirectory(0)

    c = r.TCanvas("c","",1000,1000)
    c.cd()
    h.Draw("")
    c.SaveAs("plots/{0}_{1}.png".format(sample,histoname))

    c.SetLogy()
    c.cd()
    h.Draw("")
    c.SaveAs("plots/log_{0}_{1}.png".format(sample,histoname))

def kFactorControlVars(histoname,sample):
    f       = r.TFile.Open("../results/templates/2016/scaled/{0}16.root".format(sample))
    hBefore = f.Get("{0}_{1}_noKFactors_nom".format(sample,histoname))
    hAfter  = f.Get("{0}_{1}_KFactors_nom".format(sample,histoname))
    #print("{0}_{1}".format(sample,histoname))

    hBefore.SetLineWidth(2)
    hAfter.SetLineWidth(2)
    hBefore.SetLineColor(r.kRed)
    hAfter.SetLineColor(r.kBlue)

    c = r.TCanvas("c","",1000,1000)
    c.cd()
    hBefore.Draw("hist")
    hAfter.Draw("hist same")
    hBefore.SetMaximum(hBefore.GetMaximum()*1.5)

    legend = r.TLegend(0.58,0.5,0.85,0.8)
    legend.SetFillStyle(0)
    legend.SetLineWidth(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(0.04)
    legend.AddEntry(hBefore,"No k-factors","L")
    legend.AddEntry(hAfter,"k-factors","L")
    legend.Draw()

    c.SaveAs("plots/kFactor_{0}_{1}.png".format(sample,histoname))

    c.SetLogy()
    c.cd()
    hBefore.Draw("hist")
    hAfter.Draw("hist same")

    legend = r.TLegend(0.58,0.5,0.85,0.8)
    legend.SetFillStyle(0)
    legend.SetLineWidth(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(0.04)
    legend.AddEntry(hBefore,"No k-factors","L")
    legend.AddEntry(hAfter,"k-factors","L")
    legend.Draw()

    c.SaveAs("plots/kFactor_log_{0}_{1}.png".format(sample,histoname))

def plotKFactors(histoname):
    f = r.TFile.Open("../data/NLO_corrections.root")
    h = f.Get(histoname)
    h.GetXaxis().SetTitle("Gen V pT [GeV]")
    h.GetYaxis().SetTitle("{0} k-Factor".format(histoname))

    c = r.TCanvas("c","",1000,1000)
    c.cd()
    c.SetMargin(0.15,0.15,0.15,0.15)
    h.Draw("hist")
    c.SaveAs("plots/corr_{0}.png".format(histoname))

# histonames_jetsel = ["gen_V_pT","HT","LHEnPart","n_AK4_30_away"]
# histonames_nocuts = ["gen_V_pT","HT","LHEnPart"]
# for histoname in histonames_jetsel:
#     hName = "jet_sel_"+histoname+"_nom"
#     plotHisto(hName,"ZJets")
#     plotHisto(hName,"WJets")

# for histoname in histonames_nocuts:
#     hName = "no_cuts_"+histoname+"_nom"
#     plotHisto(hName,"ZJets")
#     plotHisto(hName,"WJets")

# histonames_kFactors = ["HT","VpT","pT","mSD"]
# for histoname in histonames_kFactors:
#     kFactorControlVars(histoname,"WJets")    
#     kFactorControlVars(histoname,"ZJets")


plotKFactors("EWK_Z")
plotKFactors("EWK_W")
plotKFactors("QCD_Z_16")
plotKFactors("QCD_W_16")
plotKFactors("QCD_Z_17")
plotKFactors("QCD_W_17")