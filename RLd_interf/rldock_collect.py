import os 
import glob 
import json 
import argparse 
from utils_rld import collect_rldock

run_path = os.path.abspath(".")
score_path = os.path.join(run_path, "scores")


if __name__ == "__main__": 
    parser = argparse.ArgumentParser() 
    parser.add_argument("-f", "--op", help="Input: Path of outlier pdbs") 
    parser.add_argument("-m", "--md", help="Input: MD simulation directory") 
    args = parser.parse_args() 

    outliers_pdb_path = os.path.abspath(args.op)

    ### Get the pdbs used once already
    used_pdbs = glob.glob(os.path.join(args.md, 'omm_runs_*/omm_runs_*.pdb'))
    used_pdbs_basenames = [os.path.basename(used_pdb) for used_pdb in used_pdbs ]
    
    ### Exclude the used pdbs
    outliers_list = glob.glob(os.path.join(outliers_pdb_path, 'omm_runs*.pdb')) 
    if outliers_list == []: 
        exit() 
    restart_pdbs = [outlier for outlier in outliers_list 
            if os.path.basename(outlier) not in used_pdbs_basenames]  
    
    ranked_pdb_list = collect_rldock(restart_pdbs, score_path) 
    # print used_pdbs_basenames, select_pdb_rank 
    
    pdb_list_save = os.path.abspath("./pdb_rldock.json") 
    json.dump(ranked_pdb_list, open(pdb_list_save, "w")) 
