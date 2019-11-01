from abc import ABCMeta, abstractmethod
import cPickle as pickle

class TaskMan(metaclass=ABCMeta):
	def __init__(self, task_name, cpu_reqs, gpu_reqs):
		"""
		Parameters
		----------
		task_name : str
			name of particular task

		cpu_reqs : dict
			contains cpu hardware requirments for task

		gpu_reqs : dict
			contains gpu hardware requirments for task

		"""
		self.task_name = task_name
		self.outfile = str()
		self.subscriptions = dict()
		self.input = dict()

		# For minimizing the amount of disk IO.
		# Only needs to write output data once.
		# Reads input data once, and stores dictionary in self.input
		self.has_read = False
		self.has_written = False

	@abstractmethod
	def output(self):
		"""
		Effects
		-------
		Defines a dictionary of output to be passed to the next 
		stages TaskMan's. Calls self.write_output().

		"""
		raise NotImplementedError('Should implement output()')


	@abstractmethod
	def tasks(self):
		"""
		Returns
		-------
		Set of tasks to be added to the stage.

		"""
		raise NotImplementedError('Should implement tasks()')


	def subscribe(self, taskmans):
		"""
		Parameters
		----------
		taskmans : list
			list of DeepDriveMD.tasks.TaskMan objects 
			which manage different types of tasks within the pipeline
				
		Effects
		-------
		Sets infile to the outfile of the previous MD stages.

		"""
		self.subscriptions = {t.task_name : t.outfile for t in taskmans}


	def read_input(self):
		"""
		Parameters
		----------

		Effects
		-------
		Reads data from all subscriptions. 
		Only reads once and then stores data in self.input.

		Return
		----------
		result : dict
			stores user defined set of metadata to coordinate data 
			transfer between stages.

		"""

		if not self.has_read:
			for key, val in self.subscriptions.items():
				with open(val, 'rb') as f:
					self.input[key] = pickle.load(f)

			self.has_read = True

		# TODO: consider functools.lru_cache
		# TODO: currently not using return

		return self.input


	def write_output(self, data):
		"""
		Parameters
		----------
		data : dict
			stores user defined set of metadata to coordinate data 
			transfer between stages.

		Effects
		-------
		Writes data to outfile for subscribers to read.
		Only writes once.

		"""
		if not self.has_written:
			with open(self.outfile, 'wb') as f:
				pickle.dump(data, f)

			self.has_written = True


	def force_read(self):
		"""
		Effects
		-------
		Reads from subscriptions even if already read before.

		"""
		self.has_read = False
		self.read_input()