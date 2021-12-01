import ROOT as r

r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(0000)

HTs = [400,600,800]
xsecs = [145.3,34.29,18.57]
lumi = 1000.
for i,HT in enumerate(HTs):
	f = r.TFile.Open("../ZJets{0}_test_nom.root".format(HT))
	print("ZJets{0}_cutflow_nom".format(HT))
	hCutflow = f.Get("ZJets{0}_cutflow".format(HT))
	sumNGenW = hCutflow.GetBinContent(1)
	scale    = xsecs[i]*lumi/sumNGenW
	if(i==0):
		hNoCut = f.Get("ZJets{0}_no_cuts_gen_V_pT".format(HT))
		hCut = f.Get("ZJets{0}_jet_sel_gen_V_pT".format(HT))
		hNoCut.Scale(scale)
		hCut.Scale(scale)
		hNoCut.SetDirectory(0)
		hCut.SetDirectory(0)
	else:
		hNoCut_temp = f.Get("ZJets{0}_no_cuts_gen_V_pT".format(HT))
		hCut_temp = f.Get("ZJets{0}_jet_sel_gen_V_pT".format(HT))
		hNoCut_temp.Scale(scale)
		hCut_temp.Scale(scale)

		hNoCut.Add(hNoCut_temp)
		hCut.Add(hCut_temp)

c = r.TCanvas("c","",1000,1000)
c.cd()
hNoCut.Draw("")
c.SaveAs("nocut.png")
hCut.Draw("")
c.SaveAs("cut.png")