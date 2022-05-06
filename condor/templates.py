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
cd /users/mrogul/Work/CMSSW_11_1_4/
eval `scramv1 runtime -sh`
cd /users/mrogul/Work/
source timber-env/bin/activate

export WORK_DIR=/users/mrogul/Work/Zbb_SF/
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
'''

selection_template_data='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /users/mrogul/Work/CMSSW_11_1_4/
eval `scramv1 runtime -sh`
cd /users/mrogul/Work/
source timber-env/bin/activate

export WORK_DIR=/users/mrogul/Work/Zbb_SF/
cd JOB_DIR

echo eventSelection.py $*
python $WORK_DIR/eventSelection.py $* --var nom
'''

skim_template='''#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /users/mrogul/Work/CMSSW_11_1_4/
eval `scramv1 runtime -sh`
cd /users/mrogul/Work/
source timber-env/bin/activate

export WORK_DIR=/users/mrogul/Work/Zbb_SF/
cd JOB_DIR

echo $WORK_DIR/snapshot.py $*
python $WORK_DIR/snapshot.py $*
'''