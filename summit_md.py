import os, json, time 
from radical.entk import Pipeline, Stage, Task, AppManager

# ------------------------------------------------------------------------------
# Set default verbosity

if os.environ.get('RADICAL_ENTK_VERBOSE') is None:
    os.environ['RADICAL_ENTK_REPORT'] = 'True'

# Assumptions:
# - # of MD steps: 2
# - Each MD step runtime: 15 minutes
# - Summit's scheduling policy [1]
#
# Resource rquest:
# - 4 <= nodes with 2h walltime.
#
# Workflow [2]
#
# [1] https://www.olcf.ornl.gov/for-users/system-user-guides/summit/summit-user-guide/scheduling-policy
# [2] https://docs.google.com/document/d/1XFgg4rlh7Y2nckH0fkiZTxfauadZn_zSn3sh51kNyKE/
#
'''
export RADICAL_PILOT_DBURL=mongodb://hyperrct:v9gpU8gU5Wxz2C88@129.114.17.185:27017/hyperrct
export RMQ_HOSTNAME=129.114.17.185
export RMQ_PORT=5672
export RMQ_USERID=hyperrct
export RMQ_PASSWD=h1p3rrc7
export RADICAL_PROFILE=True
export RADICAL_PILOT_PROFILE=True
export RADICAL_ENTK_PROFILE=True
'''
#

base_path = os.path.abspath('.') # '/gpfs/alpine/proj-shared/bip179/entk/hyperspace/microscope/experiments/'
conda_path = ''' python env for entk ''' # '/ccs/home/hm0/.conda/envs/py3' 

md_path = os.path.join(base_path, 'MD_exps') 
agg_path = os.path.join(base_path, 'MD_to_CVAE') 
cvae_path = os.path.join(base_path, 'CVAE_exps') 
outlier_path = os.path.join(base_path, 'Outlier_search') 

pdb_file = ''' bba pdb file ''' # os.path.join(md_path, 'pdb/100-fs-peptide-400K.pdb') 
top_file = None 

N_jobs_MD = 120
N_jobs_ML = 0 #  11

hrs_wt = 12 
queue = 'batch'
proj_id = 'med110'


class DeepDriveMD:
    """
    DeepDriveMD class to carry out all the tasks in the pipeline 
    """

    def __init__(
            self, 
            num_MD=1, 
                    ): 
        """
        DeepDriveMD parameters 

        Parameters
        ----------
        num_MD : int 
            Numbers of MD simulations 
        """

        self.num_MD = num_MD 


    def generate_MD_tasks(self): 
        """
        Function to generate MD tasks. 
        """
        p = Pipeline() 
        p.name = "MD"
        s1 = Stage()
        s1.name = 'MD'

        # MD tasks
        for i in range(self.num_MD):
            t1 = Task()
            # https://github.com/radical-collaboration/hyperspace/blob/MD/microscope/experiments/MD_exps/fs-pep/run_openmm.py
            t1.pre_exec = ['. /sw/summit/python/2.7/anaconda2/5.3.0/etc/profile.d/conda.sh']
            t1.pre_exec += ['module load cuda/10.1.168']
            t1.pre_exec += ['conda activate %s' % conda_path] 
            t1.pre_exec += ['export PYTHONPATH=%s/MD_exps:$PYTHONPATH' % base_path] 
            t1.pre_exec += ['cd %s' % md_path] 
            # t1.pre_exec += [f"sleep {i}"]
            t1.executable = ['%s/bin/python' % conda_path]  # run_openmm.py
            t1.arguments = ['%s/run_openmm.py' % md_path] 
            t1.arguments += ['--pdb_file', pdb_file]
            if top_file: 
                t1.arguments += ['--topol', top_file]
            t1.arguments += ['--length', 1000000]

            # assign hardware the task 
            t1.cpu_reqs = {
                    'processes': 1,
                    'process_type': None,
                    'threads_per_process': 4,
                    'thread_type': 'OpenMP'
                    }
            t1.gpu_reqs = {
                    'processes': 1,
                    'process_type': None,
                    'threads_per_process': 1,
                    'thread_type': 'CUDA'
                    }
                              
            # Add the MD task to the simulating stage
            s1.add_tasks(t1)
            p.add_stages(s1)
        return p


    def generate_pipeline(self): 
#         p = Pipeline()
#         p.name = 'MD_ML'
#         
#         s = Stage() 
#         tasks = self.generate_MD_tasks() \
#                 + self.generate_aggregating_task() \
#                 # + self.generate_ML_tasks() \
#                 # + self.generate_interfacing_task() 
#         # print(tasks) 
#         for task in tasks: 
#             s.add_tasks(task) 
# 
#         p.add_stages(s)
        p = [\
                self.generate_MD_tasks(), \
                ]
        
        return p




if __name__ == '__main__':

    # Create a dictionary to describe four mandatory keys:
    # resource, walltime, cores and project
    # resource is 'local.localhost' to execute locally
    n_gpus = N_jobs_MD
    res_dict = {
            'resource': 'ornl.summit',
            'queue'   : queue,
            'schema'  : 'local',
            'walltime': 60 * hrs_wt,
            'cpus'    : n_gpus * 7,
            'gpus'    : n_gpus,#6*2 ,
            'project' : proj_id
    }

    DDmd = DeepDriveMD(
            num_MD=N_jobs_MD, 
            )
    p1 = DDmd.generate_pipeline()
    # Create Application Manager
    # appman = AppManager()
    appman = AppManager(
            hostname=os.environ.get('RMQ_HOSTNAME'), 
            port=int(os.environ.get('RMQ_PORT')), 
            username=os.environ.get('RMQ_USERID'), 
            password=os.environ.get('RMQ_PASSWD'))
    appman.resource_desc = res_dict


    pipelines = p1 #[]
    # pipelines.append(p1)
    # pipelines.append(p2)

    # Assign the workflow as a list of Pipelines to the Application Manager. In
    # this way, all the pipelines in the list will execute concurrently.
    appman.workflow = pipelines

    # Run the Application Manager
    appman.run()
