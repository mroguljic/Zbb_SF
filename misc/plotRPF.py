import ROOT as r
import numpy as np
from root_numpy import hist2array

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import figaspect
import mplhep as hep
from itertools import cycle
import os
from root_numpy import hist2array
import matplotlib.ticker as ticker

def RPFEval(coeffs,x,y):
    xMin = 50.
    xMax = 150.
    yMin = 450.
    yMax = 2000.

    x_rel = (x-xMin)/(xMax-xMin)
    y_rel = (y-yMin)/(yMax-yMin)

    val = 2*coeffs[0]*(1+coeffs[1]*x_rel+coeffs[2]*x_rel**2)*(1+coeffs[3]*y_rel+coeffs[4]*y_rel**2)

    return val

def plotRPF(coeffs,outputFile):

    x = np.arange(50,151,1)
    y = np.arange(450,2000,1)


    X,Y = np.meshgrid(x, y) # grid of point
    Z = RPFEval(coeffs,X, Y) # evaluation of the function on the grid
    #print(Z)

    plt.style.use([hep.style.CMS])
    #matplotlib.rcParams.update({'font.size': 30})    
    f, ax = plt.subplots()

    hep.cms.lumitext("36.3 $fb^{-1}\ (13 TeV)$", ax=ax, fontname=None, fontsize=None)
    hep.cms.text("WiP",loc=0)
    
    levels = np.linspace(0.0, 6, 101)
    plt.contourf(X,Y,Z,levels=levels)
    clb = plt.colorbar()
    clb.set_label('$R_{P/F}$ x $10^{3}$')

    ax.set_xlim([50,150])
    ax.set_ylim([450,2000])

    plt.xlabel("$M_{SD}$ [GeV]",horizontalalignment='right', x=1.0)
    plt.ylabel("$p_{T}$ [GeV]",horizontalalignment='right', y=1.0)
    plt.tight_layout()
    plt.savefig(outputFile)


def fmt(x, pos):
    a = '{:.2f}'.format(x)
    return r'${}$'.format(a)




coeffs = [1.075,0.805,-0.008,-0.721,1.119]
plotRPF(coeffs,"RPF_kFactors.png")

coeffs = [1.070,0.940,-0.137,-0.777,1.067]
plotRPF(coeffs,"RPF_no_kFactors.png")
