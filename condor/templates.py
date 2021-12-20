selection_condor = """universe              = vanilla
executable            = EXEC
output                = OUTPUT/output_$(Process).out
error                 = OUTPUT/output_$(Process).err
log                   = OUTPUT/output_$(Process).log
+JobFlavour           = "QUEUE"
Arguments = "$(args)"
use_x509userproxy = true
Queue args from ARGFILE
queue
"""

selection_template='''#!/bin/bash

cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/CMSSW_11_1_5/
eval `scramv1 runtime -sh`
cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/
source timber-env/bin/activate

export WORK_DIR=/afs/cern.ch/work/m/mrogulji/UL_X_YH/Zbb_SF/
cd JOB_DIR

echo eventSelection.py $*
python $WORK_DIR/eventSelection.py $* --var nom
python $WORK_DIR/eventSelection.py $* --var jesDown
python $WORK_DIR/eventSelection.py $* --var jesUp
python $WORK_DIR/eventSelection.py $* --var jerDown
python $WORK_DIR/eventSelection.py $* --var jerUp
python $WORK_DIR/eventSelection.py $* --var jmsDown
python $WORK_DIR/eventSelection.py $* --var jmsUp
python $WORK_DIR/eventSelection.py $* --var jmrDown
python $WORK_DIR/eventSelection.py $* --var jmrUp
python $WORK_DIR/eventSelection.py $* --var jmsPtDown
python $WORK_DIR/eventSelection.py $* --var jmsPtUp
'''

selection_template_data='''#!/bin/bash

cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/CMSSW_11_1_5/
eval `scramv1 runtime -sh`
cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/
source timber-env/bin/activate

export WORK_DIR=/afs/cern.ch/work/m/mrogulji/UL_X_YH/Zbb_SF/
cd JOB_DIR

echo eventSelection.py $*
python $WORK_DIR/eventSelection.py $* --var nom
'''
