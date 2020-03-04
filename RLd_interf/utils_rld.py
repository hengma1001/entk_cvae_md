import os 
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


def submit_rldock(pdb_list, score_path): 
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
        score_output = os.path.join(score_path, score_filename) 
        docker_command = "runner.py -i {} -o {}".format(pdb, score_output) 
        docker_filename = os.path.basename(pdb)[:-3] + 'run'
        docker_filepath = os.path.join(docker_watch, docker_filename)
        # only run docker if score file doesn't exist 
        if not os.path.exists(score_output): 
            with open(docker_filepath, 'w') as fp: 
                fp.write(docker_command) 


def collect_rldock(pdb_list, score_path): 
    # Get score for each rldock result 
    lowest_scores = np.empty(len(pdb_list)) 
    for i, pdb in enumerate(pdb_list): 
        score_filename = os.path.basename(pdb)[:-3] + 'result'
        score_output = os.path.join(score_path, score_filename) 
        if os.path.exists(score_output): 
            score = np.loadtxt(score_output)
            lowest_scores[i] = min(score) 
        else: 
            warnings.warn(
                "File doesn't exists, skipping {}".format(score_filename))

    # sort pdbs according to rldock score 
    ranked_pdb_list = [pdb for _, pdb in sorted(zip(lowest_scores, pdb_list))]
    print pdb_list, lowest_scores 
    print ranked_pdb_list
    return ranked_pdb_list 

