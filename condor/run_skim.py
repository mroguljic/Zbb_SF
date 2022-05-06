#!/usr/bin/env python

import os, sys, re
from templates import *
import subprocess


def createDirIfNotExist(path):
    if not os.path.exists(path):
        #print("CREATING DIR: ", path)
        os.makedirs(path)

def removeProcessedFiles(inputFiles,outputDir):
    filesToProcess = []

    for iFile in inputFiles:
        fileName = iFile.split("/")[-1]
        outputPath = os.path.join(outputDir,fileName)
        if not os.path.exists(outputPath):
            filesToProcess.append(iFile)

    return filesToProcess



def create_jobs(config,year="2016",jobs_dir="",out_dir=""):
    submissionCmds     = []
    for sample, sample_cfg in config.items():
        
        sampleJobs_dir = os.path.join(jobs_dir,sample)
        sampleOut_dir  = os.path.join(out_dir, sample)
        #Create dir to store jobs and dir to store output
        createDirIfNotExist(os.path.join(sampleJobs_dir, 'input'))
        createDirIfNotExist(os.path.join(sampleJobs_dir, 'output'))
        createDirIfNotExist(sampleOut_dir)

        exeScript     = skim_template.replace("JOB_DIR",sampleJobs_dir)
        open(os.path.join(sampleJobs_dir, 'input', 'run_{}.sh'.format(sample)), 'w').write(exeScript)

        condor_script = re.sub('EXEC',os.path.join(sampleJobs_dir, 'input', 'run_{}.sh'.format(sample)), selection_condor)
        condor_script = re.sub('ARGFILE',os.path.join(sampleJobs_dir, 'input', 'args_{}.txt'.format(sample)), condor_script)
        condor_script = re.sub('OUTPUT',os.path.join(sampleJobs_dir, 'output'), condor_script)
        open(os.path.join(sampleJobs_dir, 'input', 'condor_{}.condor'.format(sample)), 'w').write(condor_script)

        #Get input files
        dataset     = sample_cfg["dataset"]
        das_query   =[]
        for singleDataset in dataset.split(','):
            query   = "dasgoclient -query='file dataset={singleDataset}'".format(**locals())
            das_query.append(query)
        allFiles    = []
        for query in das_query:
            files   = subprocess.check_output(das_query, shell=True).split()
            for file in files:
              allFiles.append(file.decode("utf-8"))


        #Check if files already processed
        nDASFiles   = len(allFiles)
        allFiles    = removeProcessedFiles(allFiles,sampleOut_dir)
        print("{0}:\t{1}/{2} files processed".format(sample,nDASFiles-len(allFiles),nDASFiles))

        if(len(allFiles)==0):
            continue

        #Create file with arguments to the python script
        argsFile       = open(os.path.join(sampleJobs_dir, 'input', 'args_{}.txt'.format(sample)), 'w')
        for iFile in allFiles:
            fName      = iFile.split("/")[-1]
            outputPath = os.path.join(sampleOut_dir,fName)
            argsFile.write("-i {0} -o {1} -p {2} -y {3}\n".format(iFile,outputPath,sample,year))

        #Submit
        os.system("chmod +x {0}".format(os.path.join(sampleJobs_dir, 'input', 'run_{}.sh'.format(sample))))
        submissionCmds.append("condor_submit {0}".format(os.path.join(sampleJobs_dir, 'input', 'condor_{}.condor'.format(sample))))
    
    for cmd in submissionCmds:
        print(cmd)

def main():

    import json
    
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Do -h to see usage")

    parser.add_argument('-c', '--config', help='Job config file in JSON format')
    parser.add_argument('-y', '--year', help='Dataset year',default="2016")
    parser.add_argument('-o', '--outdir',help='Output directory')
    parser.add_argument('-j', '--jobdir',help='Jobs directory')
 
    args = parser.parse_args()

    print(args)

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)
        create_jobs(config,year=args.year,out_dir=args.outdir,jobs_dir=args.jobdir)
                    

            

if __name__ == "__main__":
    main()

