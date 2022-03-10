import json
import numpy as np
import ROOT as r

def ewkToRoot(correction,name,outputFile):
    print("Match check {0}: {1}".format(name,correction["name"]))
    nominal = correction["data"]["content"][0]
    binning = nominal["value"]["edges"]
    binning = np.array(binning,dtype='float64')
    hEWK    = r.TH1F(name,"",len(binning)-1,binning)
    
    for i,val in enumerate(nominal["value"]["content"]):
        hEWK.SetBinContent(i+1,val)

    hEWK.SetDirectory(0)
    f = r.TFile.Open(outputFile,"UPDATE")
    f.cd()
    hEWK.Write()
    f.Close()

def ewkToRootWithUncerts(correction,name,outputFile):
    print("Match check {0}: {1}".format(name,correction["name"]))


    variations  = correction["data"]["content"]
    nVars       = len(correction["data"]["content"])
    histos      = []

    for variation in variations:
        varName = variation["key"]
        binning = variation["value"]["edges"]
        binning = np.array(binning,dtype='float64')

        hEWK    = r.TH1F(name+"_{0}".format(varName),"",len(binning)-1,binning)
    
        for i,val in enumerate(variation["value"]["content"]):
            hEWK.SetBinContent(i+1,val)

        hEWK.SetDirectory(0)
        histos.append(hEWK)

    f = r.TFile.Open(outputFile,"UPDATE")
    f.cd()
    for h in histos:
        h.Write()
    f.Close()

def qcdToRoot(correction,name,outputFile):
    print("Match check {0}: {1}".format(name,correction["name"]))
    edges   = correction["data"]["edges"]
    edgeLo  = edges[0]
    edgeHi  = edges[-1]
    expr    = correction["data"]["content"][1]["expression"]
    tf      = r.TF1("tf_qcd",expr)
    binning = np.arange(edgeLo,edgeHi,1,dtype="float64")
    hQCD    = r.TH1F(name,"",len(binning)-1,binning)
    
    for i in range(1,hQCD.GetNbinsX()+1):
        vpt = hQCD.GetBinCenter(i)
        val = tf.Eval(vpt)
        hQCD.SetBinContent(i,val)

    hQCD.SetDirectory(0)
    f = r.TFile.Open(outputFile,"UPDATE")
    f.cd()
    hQCD.Write()
    f.Close()


def relativeUnc(outputFile):
    f = r.TFile.Open(outputFile,"UPDATE")

    systematics = ["d1K_NLO","d2K_NLO","d3K_NLO","d1kappa_EW"]
    systematics_Z = ["Z_d2kappa_EW","Z_d3kappa_EW"]
    systematics_W = ["W_d2kappa_EW","W_d3kappa_EW"]

    unc_histos = []

    for systematic in systematics:
        h_Z         = f.Get("EWK_Z_nominal")
        h_W         = f.Get("EWK_W_nominal")
        h_Z_up      = f.Get("EWK_Z_{0}_up".format(systematic))
        h_Z_down    = f.Get("EWK_Z_{0}_down".format(systematic))
        h_W_up      = f.Get("EWK_W_{0}_up".format(systematic))
        h_W_down    = f.Get("EWK_W_{0}_down".format(systematic))

        h_Z_up.Divide(h_Z)
        h_Z_down.Divide(h_Z)
        h_W_up.Divide(h_W)
        h_W_down.Divide(h_W)

        h_Z_up.SetName("unc_"+h_Z_up.GetName())
        h_Z_down.SetName("unc_"+h_Z_down.GetName())
        h_W_up.SetName("unc_"+h_W_up.GetName())
        h_W_down.SetName("unc_"+h_W_down.GetName())

        h_Z_up.SetDirectory(0)
        h_Z_down.SetDirectory(0)
        h_W_up.SetDirectory(0)
        h_W_down.SetDirectory(0)

        unc_histos.extend([h_Z_up,h_Z_down,h_W_up,h_W_down])

    for systematic in systematics_Z:
        h_Z         = f.Get("EWK_Z_nominal")
        h_Z_up      = f.Get("EWK_Z_{0}_up".format(systematic))
        h_Z_down    = f.Get("EWK_Z_{0}_down".format(systematic))

        h_Z_up.Divide(h_Z)
        h_Z_down.Divide(h_Z)

        h_Z_up.SetName("unc_"+h_Z_up.GetName())
        h_Z_down.SetName("unc_"+h_Z_down.GetName())

        h_Z_up.SetDirectory(0)
        h_Z_down.SetDirectory(0)

        unc_histos.extend([h_Z_up,h_Z_down])

    for systematic in systematics_W:
        h_W         = f.Get("EWK_W_nominal")
        h_W_up      = f.Get("EWK_W_{0}_up".format(systematic))
        h_W_down    = f.Get("EWK_W_{0}_down".format(systematic))

        h_W_up.Divide(h_W)
        h_W_down.Divide(h_W)

        h_W_up.SetName("unc_"+h_W_up.GetName())
        h_W_down.SetName("unc_"+h_W_down.GetName())

        h_W_up.SetDirectory(0)
        h_W_down.SetDirectory(0)

        unc_histos.extend([h_W_up,h_W_down])


    f.cd()
    for h in unc_histos:
        h.Write()
    f.Close()

with open("VJetsCorrections.json") as json_file:
    data        = json.load(json_file)
    corrections = data["corrections"]
    ewk_Z       = corrections[2]
    ewk_W       = corrections[5]
    qcd_Z_16    = corrections[1]
    qcd_Z_17    = corrections[0]
    qcd_W_16    = corrections[4]
    qcd_W_17    = corrections[3]

    outputFile = "NLO_corrections.root"

    qcdToRoot(qcd_Z_16,"QCD_Z_16",outputFile)
    qcdToRoot(qcd_Z_17,"QCD_Z_17",outputFile)

    qcdToRoot(qcd_W_16,"QCD_W_16",outputFile)
    qcdToRoot(qcd_W_17,"QCD_W_17",outputFile)

    ewkToRootWithUncerts(ewk_Z,"EWK_Z",outputFile)
    ewkToRootWithUncerts(ewk_W,"EWK_W",outputFile)


    relativeUnc(outputFile)