import ROOT as r

r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(0000)

def plotHisto(histoname,sample):
	for i,HT in enumerate(HTs):
		f = r.TFile.Open("../results/templates/2016/scaled/{0}16.root".format(sample))
			h = f.Get("{0}_{1}".format(sample,histoname))
			h.SetDirectory(0)

	c = r.TCanvas("c","",1000,1000)
	c.cd()
	h.Draw("")
	c.SaveAs("plots/{0}_{1}.png".format(sample,histoname))

	c.SetLogy()
	c.cd()
	h.Draw("")
	c.SaveAs("plots/log_{0}_{1}.png".format(sample,histoname))


histonames_jetsel = ["gen_V_pT","HT","LHEnPart","n_AK4_30_away_nom"]
histonames_nocuts = ["gen_V_pT","HT","LHEnPart"]
for histoname in histonames_jetsel:
	hName = "jet_sel_"+histoname+"_nom"
	plotHisto(hName,"ZJets")
	plotHisto(hName,"WJets")

for histoname in histonames_nocuts:
	hName = "no_cuts_"+histoname+"_nom"
	plotHisto(hName,"ZJets")
	plotHisto(hName,"WJets")