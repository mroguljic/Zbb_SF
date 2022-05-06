#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /users/mrogul/Work/CMSSW_11_1_4/
eval `scramv1 runtime -sh`
cd /users/mrogul/Work/
source timber-env/bin/activate

export WORK_DIR=/users/mrogul/Work/Zbb_SF/
cd $WORK_DIR

echo run_templates.py $*
python run_templates.py $*