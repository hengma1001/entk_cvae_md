import os, glob 
import sys 
import shutil
import time

if len(sys.argv) > 1: 
    status = sys.argv[1] 
else: 
    status = 'fail'

print status 
omm_dirs = glob.glob('MD_exps/fs-pep/omm_runs*') 
pca_dirs = glob.glob('PCA_exps/pca_runs_*') 
jsons = glob.glob('Outlier_search/*json') 

result_save = os.path.join('./results', 'result_%d_%s' % (int(time.time()), status)) 
os.makedirs(result_save) 

omm_save = os.path.join(result_save, 'omm_results') 
os.makedirs(omm_save) 
for omm_dir in omm_dirs: 
    shutil.move(omm_dir, omm_save) 

pca_save = os.path.join(result_save, 'pca_results') 
os.makedirs(pca_save) 
for pca_dir in pca_dirs: 
    shutil.move(pca_dir, pca_save) 

outlier_save = os.path.join(result_save, 'outlier_save/') 
os.makedirs(outlier_save) 
for json in jsons:  
    shutil.move(json, outlier_save) 

if os.path.isdir('Outlier_search/outlier_pdbs'): 
    shutil.move('Outlier_search/outlier_pdbs', outlier_save) 

sandbox_path = '/gpfs/alpine/bip179/scratch/hm0/radical.pilot.sandbox' 
local_entk_path = sorted(glob.glob('re.session.*'))[-1] 
shutil.move(local_entk_path, result_save) 
sandbox_src = os.path.join(sandbox_path, local_entk_path) 
sandbox_dst = os.path.join(result_save, local_entk_path + '_sandbox') 
shutil.copytree(sandbox_src, sandbox_dst) 


