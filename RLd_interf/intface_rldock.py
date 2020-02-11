import os 
import sys 
import glob 
import json 
import errno
import numpy as np 

# echo "runner.py -i /gpfs/alpine/proj-shared/lrn005/RLDock/pdbs_traj/test_p0.pdb
# -o /gpfs/alpine/bip179/scratch/hm0/entk_MDs/experiments_folding/experiments_BBA/RLd_interf/test3.result" 
# >> /gpfs/alpine/proj-shared/lrn005/RLDock_watch/first-run


def make_dir_p(path_name):
    try:
        os.mkdir(path_name)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass


docker_watch = "/gpfs/alpine/proj-shared/lrn005/RLDock_watch/"
run_path = os.path.abspath(".")
scores_path = os.path.join(run_path, "scores")
make_dir_p(scores_path)


def rank_by_dock(pdb_list): 
    """
    A function that ranks pdb file according to their docking performance 
    with a list of ligands 

    Parameters 
    ==========
        pdb_list: list 
            List of protein pdb files to rank 

    Return 
    ======
        pdb_list : list 
            Ranked list of pdbs 
    """
    # Get all paths ready 
    for pdb in pdb_list: 
        score_filename = os.path.basename(pdb)[:-3] + 'result'
        score_output = os.path.join(scores_path, score_filename) 
        docker_command = "runner.py -i {} -o {}".format(pdb, score_output) 
        docker_filename = os.path.basename(pdb)[:-3] + 'run'
        docker_filepath = os.path.join(docker_watch, docker_filename)
        # only run docker if score file doesn't exist 
        if not os.path.exists(score_output): 
            with open(docker_filepath, 'w') as fp: 
                fp.write(docker_command) 

    # Wait for the RLdock run to finish 
    while True: 
        docker_runs = glob.glob(docker_watch + '/*run') 
        if docker_runs == []: 
            break 

    lowest_scores = np.empty(len(pdb_list)) 
    for i, pdb in enumerate(pdb_list): 
        score_filename = os.path.basename(pdb)[:-3] + 'result'
        score_output = os.path.join(scores_path, score_filename) 
        if os.path.exists(score_output): 
            score = np.loadtxt(score_output)
            lowest_scores[i] = min(score) 
        else: 
            warnings.warn(
                "File doesn't exists, skipping {}".format(score_filename))

    # Strategy here is to pick all candidates with energy lower than 
    # (median value - std / 2) 
    score_median, score_std = np.median(lowest_scores), np.std(lowest_scores) 
    score_cutoff = score_median - score_std / 2 
    select_pdb_list = []
    for score, pdb_file in sorted(zip(lowest_scores, pdb_list)): 
        if score < (score_cutoff): 
            select_pdb_list.append(pdb_file) 
        # No need to loop through the rest since scores are sorted 
        else: 
            break 

    return select_pdb_list 


if __name__ == "__main__": 
    outlier_path = "/gpfs/alpine/bip179/scratch/hm0/entk_MDs/"\
                   "experiments_folding/experiments_BBA/Outlier_search/" \
                   "outlier_pdbs/"
    pdb_list = glob.glob(outlier_path + "omm_run*pdb") 
    select_pdb_rank = rank_by_dock(pdb_list) 
    pdb_list_save = os.path.abspath("./pdb_rld.json") 
    json.dump(select_pdb_rank, open(pdb_list_save, "w")) 
