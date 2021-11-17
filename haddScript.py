import os
import sys

targetDir = sys.argv[1]
os.chdir(targetDir)

directories=[d for d in os.listdir(os.getcwd()) if os.path.isdir(d)]

variations = ["nom","jesUp","jesDown","jerUp","jerDown","jmsUp","jmsDown","jmrUp","jmrDown"]

    
for d in directories:
    for variation in variations:
        if(variation!="nom" and ("JetHT" in d or "QCD" in d)):
            continue
        cmd = "hadd -f {0}_{1}.root {0}/*{1}*root".format(d,variation)
        print(cmd)
        os.system(cmd)
