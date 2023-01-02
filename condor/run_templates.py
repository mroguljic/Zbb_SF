import os
import glob
import sys
from paths import SELECTION_DIR, TEMPLATE_JOB_DIR
from templates import templates_template, selection_condor
from pathlib import Path
import re
import stat
#python run_templates.py ceiling tight
#python run_templates.py tight medium -> if you want to run exclusive wp
#python run_templates.py ceiling medium -> if you want to run inclusive wp

TEMPLATE_DIR = SELECTION_DIR.replace("selection","templates")

wpUp   = sys.argv[1]
wpLo   = sys.argv[2]
args = ""
template_jobs_wp_dir = os.path.join(TEMPLATE_JOB_DIR,wpLo)
Path(template_jobs_wp_dir).mkdir(exist_ok=True, parents=True)

template_jobs_log_dir = os.path.join(template_jobs_wp_dir,"output")
Path(template_jobs_log_dir).mkdir(exist_ok=True, parents=True)

#ParticleNet pnet0
wp_ceiling	= {"2016APV":1.01,"2016":1.01,"2017":1.01,"2018":1.01}
wp_tight  	= {"2016APV":0.9883,"2016":0.9883,"2017":0.9870,"2018":0.9880}
wp_medium 	= {"2016APV":0.9737,"2016":0.9735,"2017":0.9714,"2018":0.9734}
wp_loose	= {"2016APV":0.9088,"2016":0.9137,"2017":0.9105,"2018":0.9172}

# #DeepDoubleX ddb0
# wp_ceiling	= {"2016APV":1.01,"2016":1.01,"2017":1.01,"2018":1.01}
# wp_tight  	= {"2016APV":0.2739,"2016":0.2786,"2017":0.3154,"2018":0.3140}
# wp_medium 	= {"2016APV":0.1180,"2016":0.1213,"2017":0.1566,"2018":0.1566}
# wp_loose	= {"2016APV":0.0256,"2016":0.0270,"2017":0.0404,"2018":0.0399}

# #DeepAK8 deepTag0
# wp_ceiling	= {"2016APV":1.01,"2016":1.01,"2017":1.01,"2018":1.01}
# wp_tight  	= {"2016APV":0.9521,"2016":0.9507,"2017":0.9546,"2018":0.9551}
# wp_medium 	= {"2016APV":0.8940,"2016":0.8877,"2017":0.9033,"2018":0.9058}
# wp_loose	= {"2016APV":0.7021,"2016":0.6890,"2017":0.7422,"2018":0.7432}

# #DoubleB hbb0
# wp_ceiling	= {"2016APV":1.01,"2016":1.01,"2017":1.01,"2018":1.01}
# wp_tight  	= {"2016APV":0.8926,"2016":0.8955,"2017":0.9175,"2018":0.9326}
# wp_medium 	= {"2016APV":0.7559,"2016":0.7646,"2017":0.8237,"2018":0.8193}
# wp_loose	= {"2016APV":0.3104,"2016":0.3279,"2017":0.5068,"2018":0.4939}



wp_vals   	= {"ceiling":wp_ceiling,"tight":wp_tight, "medium":wp_medium, "loose":wp_loose}
for year in ["2016","2016APV","2017","2018"]:
	evtSelDir = "{0}/{1}/".format(SELECTION_DIR,year)
	tplDir    = "{0}/{1}/{2}".format(TEMPLATE_DIR,wpLo,year)
	nomFiles  = glob.glob('{0}/*nom.root'.format(evtSelDir))
	for nomFile in nomFiles:
		sample  = nomFile.split("/")[-1].replace("_nom.root","")
		argLine = "{0} {1} {2} {3} {4}\n".format(evtSelDir,sample,tplDir,wp_vals[wpUp][year],wp_vals[wpLo][year])
		args+=argLine
f = open("{0}/args.txt".format(template_jobs_wp_dir),"w")
f.write(args)
f.close()


open(os.path.join(template_jobs_wp_dir, 'run_script.sh'), 'w').write(templates_template)
os.system("chmod +x {0}".format(os.path.join(template_jobs_wp_dir, 'run_script.sh')))

condor_script = re.sub('EXEC',os.path.join(template_jobs_wp_dir, 'run_script.sh'), selection_condor)
condor_script = re.sub('ARGFILE',os.path.join(template_jobs_wp_dir, 'args.txt'), condor_script)
condor_script = re.sub('OUTPUT',os.path.join(template_jobs_wp_dir, 'output'), condor_script)
open(os.path.join(template_jobs_wp_dir, 'condor_submit.condor'), 'w').write(condor_script)

cmd_to_run    = "condor_submit {0}/condor_submit.condor".format(template_jobs_wp_dir)
print(cmd_to_run)