import os

wp   = 0.98
args = ""
for year in ["2016","2017","2018"]:
	evtSelDir = "/afs/cern.ch/user/m/mrogulji/UL_X_YH/Zbb_SF/results/eventSelection/{0}/".format(year)
	tplDir    = "/afs/cern.ch/user/m/mrogulji/UL_X_YH/Zbb_SF/results/templates/{0}/{1}/".format(wp,year)
	samples   = [d for d in os.listdir(evtSelDir) if os.path.isdir(os.path.join(evtSelDir,d))]
	for sample in samples:
		argLine = "{0} {1} {2} {3}\n".format(evtSelDir,sample,tplDir,wp)
		args+=argLine
f = open("args.txt","w")
f.write(args)
f.close()