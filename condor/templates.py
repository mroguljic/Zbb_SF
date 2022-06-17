from paths import CMSSW_DIR, TIMBERENV_DIR, ZBB_DIR


selection_condor = """universe              = vanilla
executable            = EXEC
output                = OUTPUT/output_$(Process).out
error                 = OUTPUT/output_$(Process).err
log                   = OUTPUT/output_$(Process).log
Arguments = "$(args)"
use_x509userproxy = true
Queue args from ARGFILE
queue
"""

selection_template='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {0}
eval `scramv1 runtime -sh`
cd {1}
source timber-env/bin/activate

export WORK_DIR={2}
cd JOB_DIR

echo eventSelection.py $*
python $WORK_DIR/eventSelection.py $* --var nom
python $WORK_DIR/eventSelection.py $* --var jesDown
python $WORK_DIR/eventSelection.py $* --var jesUp
python $WORK_DIR/eventSelection.py $* --var jerDown
python $WORK_DIR/eventSelection.py $* --var jerUp
python $WORK_DIR/eventSelection.py $* --var jmsUp
python $WORK_DIR/eventSelection.py $* --var jmsDown
python $WORK_DIR/eventSelection.py $* --var jmrUp
python $WORK_DIR/eventSelection.py $* --var jmrDown
'''.format(CMSSW_DIR,TIMBERENV_DIR,ZBB_DIR)

selection_template_data='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {0}
eval `scramv1 runtime -sh`
cd {1}
source timber-env/bin/activate

export WORK_DIR={2}
cd JOB_DIR

echo eventSelection.py $*
python $WORK_DIR/eventSelection.py $* --var nom
'''.format(CMSSW_DIR,TIMBERENV_DIR,ZBB_DIR)

skim_template='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {0}
eval `scramv1 runtime -sh`
cd {1}
source timber-env/bin/activate

export WORK_DIR={2}
cd JOB_DIR

echo $WORK_DIR/snapshot.py $*
python $WORK_DIR/snapshot.py $*
'''.format(CMSSW_DIR,TIMBERENV_DIR,ZBB_DIR)

#Condor exe template for running jobs which create histogram templates :)
templates_template='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {0}
eval `scramv1 runtime -sh`
cd {1}
source timber-env/bin/activate

export WORK_DIR={2}
cd $WORK_DIR

echo $WORK_DIR/templateCreation.py $*
python $WORK_DIR/templateCreation.py $*
'''.format(CMSSW_DIR,TIMBERENV_DIR,ZBB_DIR)