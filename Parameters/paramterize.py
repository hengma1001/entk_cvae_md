import os 
import re
import glob 
# import json 
import shutil
from tqdm import tqdm
import MDAnalysis as mda 
import pandas as pd 

from comp_sim.utils import only_protein, align_to_template, clean_pdb
from comp_sim.param import ParameterizeAMBER_comp2 
from comp_sim.param import ParameterizeAMBER_prot 

host_dir = os.getcwd() 
pdb_files = sorted(glob.glob(host_dir + '/pdb/*.pdb') )
print(pdb_files)

# prot_files = [pdb for pdb in pdb_files if only_protein(pdb)] 
prot_files = [os.path.abspath('./pdb/adrp.pdb')]
print(prot_files) 

ref_pdb = prot_files[0]
info_list = []
for pdb in tqdm(pdb_files): 
    pdb_code = os.path.basename(pdb)[:-4] 

    if pdb_code.startswith('db'): 
        csv_file = './pdb/adrp_db_sorted_top100_rescore.csv'
    elif pdb_code.startswith('ena'): 
        csv_file = './pdb/adrp_ena+db_sorted_top100_rescore.csv' 
    else: 
        csv_file = '.'
    csv_file = os.path.abspath(csv_file) 
        
    work_dir = os.path.abspath(os.path.join(host_dir, 'input_' + pdb_code))
    os.makedirs(work_dir, exist_ok=True) 
    if glob.glob(work_dir + '/*prmtop') != []: 
        continue
    pdb_copy = os.path.join(work_dir, os.path.basename(pdb))
    
    # align all targets to template 
    # align_to_template(pdb, ref_pdb, pdb_copy)
    shutil.copy2(pdb, pdb_copy)
    clean_pdb(pdb_copy) 
    os.chdir(work_dir) 
    if only_protein(pdb): 
        info = ParameterizeAMBER_prot(pdb_copy, add_sol=True)
    else: 
        db_ind = int(re.findall("\d+", pdb_code)[0]) - 1 
        df = pd.read_csv(csv_file)  
        df = df.fillna(0)
        charge = df.iloc[db_ind]['JCHEM_FORMAL_CHARGE']
        print(pdb_code, charge)
        try: 
            info = ParameterizeAMBER_comp2(pdb_copy, lig_charge=charge, add_sol=True) 
        except: 
            if charge != 0: 
                print(f"{pdb_code} failed with provided charge {charge}, retrying with neutral charge...")
                info = ParameterizeAMBER_comp2(pdb_copy, add_sol=True) 
            else: 
                try:
                    print(f"{pdb_code} failed with provided charge {charge}, retrying with -1 e charge...")
                    info = ParameterizeAMBER_comp2(pdb_copy, lig_charge=-1, add_sol=True) 
                except: 
                    print(f"{pdb_code} failed with provided charge {charge}, retrying with +1 e charge...")
                    info = ParameterizeAMBER_comp2(pdb_copy, lig_charge=+1, add_sol=True)


    info_list.append(info)
    os.chdir(host_dir) 

# input_filepath = os.path.abspath('./input_conf.json') 
# with open(input_filepath, 'w') as input_file: 
#     json.dump(info_list, input_file)
