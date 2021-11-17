import ROOT as r

processes = ["QCD","TTbar","ZJets","WJets","ST"]

for proc in processes:
	f = r.TFile.Open("results/templates/2016/scaled/{0}16.root".format(proc))
	T = f.Get("{0}_m_pT_T_nom".format(proc)).Integral()
	L = f.Get("{0}_m_pT_L_nom".format(proc)).Integral()
	F = f.Get("{0}_m_pT_F_nom".format(proc)).Integral()
	print("{0} {1:.1f} {2:.1f} {3:.1f}".format(proc,T,L,F))