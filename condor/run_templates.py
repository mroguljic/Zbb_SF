import os
import glob
import sys
from paths import SELECTION_DIR, TEMPLATE_JOB_DIR
from templates import templates_template, selection_condor
from pathlib import Path
import re
import stat
#python run_templates.py 0.94
#python run_templates.py 0.98

TEMPLATE_DIR = SELECTION_DIR.replace("selection","templates")

wp   = sys.argv[1]
args = ""
template_jobs_wp_dir = os.path.join(TEMPLATE_JOB_DIR,wp)
Path(template_jobs_wp_dir).mkdir(exist_ok=True, parents=True)

template_jobs_log_dir = os.path.join(template_jobs_wp_dir,"output")
Path(template_jobs_log_dir).mkdir(exist_ok=True, parents=True)

for year in ["2016","2016APV","2017","2018"]:
	evtSelDir = "{0}/{1}/".format(SELECTION_DIR,year)
	tplDir    = "{0}/{1}/{2}".format(TEMPLATE_DIR,wp,year)
	nomFiles  = glob.glob('{0}/*nom.root'.format(evtSelDir))
	for nomFile in nomFiles:
		sample  = nomFile.split("/")[-1].replace("_nom.root","")
		argLine = "{0} {1} {2} {3}\n".format(evtSelDir,sample,tplDir,wp)
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