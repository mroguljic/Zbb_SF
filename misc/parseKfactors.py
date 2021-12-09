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



with open("VJetsCorrections.json") as json_file:
    data        = json.load(json_file)
    corrections = data["corrections"]
    ewk_Z       = corrections[4]
    ewk_W       = corrections[9]
    qcd_Z_16    = corrections[1]
    qcd_Z_17    = corrections[0]
    qcd_W_16    = corrections[6]
    qcd_W_17    = corrections[5]

    outputFile = "kFactors.root"
    ewkToRoot(ewk_Z,"EWK_Z",outputFile)
    ewkToRoot(ewk_W,"EWK_W",outputFile)
    
    qcdToRoot(qcd_Z_16,"QCD_Z_16",outputFile)
    qcdToRoot(qcd_Z_17,"QCD_Z_17",outputFile)

    qcdToRoot(qcd_W_16,"QCD_W_16",outputFile)
    qcdToRoot(qcd_W_17,"QCD_W_17",outputFile)

