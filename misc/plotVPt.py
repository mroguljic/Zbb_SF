import ROOT as r

r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(0000)

HTs = [400,600,800]
xsecs = [145.3,34.29,18.57]
lumi = 1000.

def plotHisto(histoname):
	for i,HT in enumerate(HTs):
		f = r.TFile.Open("../ZJets{0}_test_nom.root".format(HT,histoname))
		print("ZJets{0}_cutflow_nom".format(HT))
		hCutflow = f.Get("ZJets{0}_cutflow".format(HT))
		sumNGenW = hCutflow.GetBinContent(1)
		scale    = xsecs[i]*lumi/sumNGenW
		if(i==0):
			hNoCut = f.Get("ZJets{0}_no_cuts_{1}".format(HT,histoname))
			hCut = f.Get("ZJets{0}_jet_sel_{1}".format(HT,histoname))
			hNoCut.Scale(scale)
			hCut.Scale(scale)
			hNoCut.SetDirectory(0)
			hCut.SetDirectory(0)
		else:
			hNoCut_temp = f.Get("ZJets{0}_no_cuts_{1}".format(HT,histoname))
			hCut_temp = f.Get("ZJets{0}_jet_sel_{1}".format(HT,histoname))
			hNoCut_temp.Scale(scale)
			hCut_temp.Scale(scale)

			hNoCut.Add(hNoCut_temp)
			hCut.Add(hCut_temp)

	c = r.TCanvas("c","",1000,1000)
	c.cd()
	hNoCut.Draw("")
	c.SaveAs("nocut_{0}.png".format(histoname))
	hCut.Draw("")
	c.SaveAs("cut_{0}.png".format(histoname))

	c.SetLogy()
	c.cd()
	hNoCut.Draw("")
	c.SaveAs("log_nocut_{0}.png".format(histoname))
	hCut.Draw("")
	c.SaveAs("log_cut_{0}.png".format(histoname))


histonames = ["gen_V_pT","n_AK4_30","n_AK4_50","HT","LHEnJets","LHEnPart","GennPart","n_AK8_100","n_AK8_200"]
for histoname in histonames:
	plotHisto(histoname)