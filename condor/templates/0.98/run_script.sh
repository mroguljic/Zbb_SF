#!/bin/bash
cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/CMSSW_11_1_5/
eval `scramv1 runtime -sh`
cd /afs/cern.ch/work/m/mrogulji/UL_X_YH/
source timber-env/bin/activate

export WORK_DIR=/afs/cern.ch/work/m/mrogulji/UL_X_YH/Zbb_SF/
cd $WORK_DIR

echo run_templates.py $*
python run_templates.py $*