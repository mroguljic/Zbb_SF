import os
import glob


wp   = 0.98
args = ""
#for year in ["2016","2017","2018"]:
for year in ["2018"]:
	evtSelDir = "/users/mrogul/Work/Zbb_SF/results/selection/{0}/".format(year)
	tplDir    = "/users/mrogul/Work/Zbb_SF/results/templates/{0}/{1}/".format(wp,year)
	nomFiles  = glob.glob('{0}/*nom.root'.format(evtSelDir))
	for nomFile in nomFiles:
		sample  = nomFile.split("/")[-1].replace("_nom.root","")
		argLine = "{0} {1} {2} {3}\n".format(evtSelDir,sample,tplDir,wp)
		args+=argLine
f = open("{0}/args.txt".format(wp),"w")
f.write(args)
f.close()