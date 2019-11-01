import os
from DeepDriveMD.taskman import TaskMan
from radical.entk import Task

class ContactMatrix(TaskMan):
	def __init__(self, task_name, cpu_reqs, gpu_reqs):
		super().__init__(task_name, cpu_reqs, gpu_reqs)

		self.conda_path = '/ccs/home/hm0/.conda/envs/omm'
		self.cwd = os.getcwd()

	def output(self):
		output_data = {'--h5': '/MD_to_CVAE/cvae_input.h5'}
		self.write_output(output_data)

	def tasks(self):
		# self.input stores sim_path: base/MD_exps/fs-pep
		

		task = Task()

		task.pre_exec = ['. /sw/summit/python/2.7/anaconda2/5.3.0/etc/profile.d/conda.sh',
						 'conda activate %s' % self.conda_path,
						 'cd %s/MD_to_CVAE' % self.cwd]
		task.executable = ['%s/bin/python' % self.conda_path]
		task.arguments = ['%s/MD_to_CVAE/MD_to_CVAE.py' % self.cwd, 
        				  '--sim_path', self.input['BasicMD']['--sim_path']]

        return set(task)
