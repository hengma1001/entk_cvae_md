import os
from radical.entk import Pipeline, Stage, Task, AppManager


class DeepDriveMD:
    """
    Implements an interface for the DeepDriveMD computational 
    motif presented in: https://arxiv.org/abs/1909.07817
    """
    def __init__(self, md_sims, preprocs, ml_algs, outlier_algs, 
    			 max_iter=1, pipeline_name='MD_ML', md_stage_name='MD',
                 pre_stage_name='Preprocess', ml_stage_name='ML',
                 outlier_stage_name='Outlier'):

        """
        Parameters
        ----------
		md_sims : list
			list of DeepDriveMD.taskman.TaskMan objects 
            which manage simulations

		preprocs : list
			list of DeepDriveMD.taskman.TaskMan objects 
            which manage data preprocessing

		ml_algs : list
			list of DeepDriveMD.taskman.TaskMan objects 
            which manage representation learning
		
		outlier_algs : list
			list of DeepDriveMD.taskman.TaskMan objects 
            which manage outlier detection

        max_iter : int
            Max number of iterations through the pipeline
	
        pipeline_name : str
            Name of computational pipeline

        md_stage_name : str
            Name of MD stage

        pre_stage_name : str
            Name of preprocessing stage

        ml_stage_name : str
            Name of ML stage

        outlier_stage_name : str
            Name of outlier detection stage

        """

        # Number of iterations through the pipeline
        self.current_iter = 0
        self.max_iter = max_iter

        # TODO: Move outside of class? Maybe put in __init__.py
        # Set default verbosity
        if os.environ.get('RADICAL_ENTK_VERBOSE') is None:
            os.environ['RADICAL_ENTK_REPORT'] = 'True'

        # Initialize pipeline
        self.__pipeline = Pipeline()
        self.__pipeline.name = pipeline_name
        self.md_stage_name = md_stage_name
        self.pre_stage_name = pre_stage_name
        self.ml_stage_name = ml_stage_name
        self.outlier_stage_name = outlier_stage_name

        # Set stage task managers
        self.md_sims = md_sims
        self.preprocs = preprocs
        self.ml_algs = ml_algs
        self.outlier_algs = outlier_algs

        # Initialize each incomming list of TaskMan's with output files.
        self.__init_log_dir()

        # Sets pipeline stages
        self.pipeline()

        # Create Application Manager
        self.appman = AppManager(hostname=os.environ.get('RMQ_HOSTNAME'), 
                                 port=int(os.environ.get('RMQ_PORT')))
        self.appman.resource_desc = resources

        # Assign the workflow as a list of Pipelines to the Application Manager. In
        # this way, all the pipelines in the list will execute concurrently.
        self.appman.workflow = [self.__pipeline]

    def __init_log_dir(self):
        """
        Effects
        -------
        Creates {cwd}/deepdrive_logs directory for logging.
        Raises error if log directory already exists.

        Initialize each incomming list of TaskMan's with output files.
        Then writes output (file metadata) for inter-TaskMan communications
        to respective output files.
        
        """
        # Create log directory
        log_dir = '{}/deepdrive_logs'.format(os.getcwd())
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        else:
            raise FileExistsError('Log directory already exits. Please remove: {}'.format(log_dir))


        # Define each outfile and then write output data to each respective file
        for i, md_sim in enumerate(self.md_sims):
            md_sim.outfile = '{}/md_sim_{}_{}.pickle'.format(log_dir, md_sim.task_name, i)
            md_sim.output()

        for i, preproc in enumerate(self.preprocs):
            preproc.outfile = '{}/preproc_{}_{}.pickle'.format(log_dir, preproc.task_name, i)
            preproc.output()

        for i, ml_alg in enumerate(self.ml_algs):
            ml_alg.outfile = '{}/ml_alg_{}_{}.pickle'.format(log_dir, ml_alg.task_name, i)
            ml_alg.output()

        for i, outlier_alg in enumerate(self.outlier_algs):
            outlier_alg.outfile = '{}/outlier_alg_{}_{}.pickle'.format(log_dir, outlier_alg.task_name, i)
            outlier_alg.output()


	def run(self):
		"""
		Effects
		-------
		Reads data from subscriptions and runs the Application Manager. 
		
		"""

        # Read input data from subscriptions
        for md_sim in self.md_sim:
            md_sim.read_input()

        for preproc in self.preprocs:
            preproc.read_input()

        for ml_alg in self.ml_algs:
            ml_alg.read_input()

        for outlier_alg in self.outlier_algs:
            outlier_alg.read_input()

        self.appman.run()


    def generate_MD_stage(self):
		stage = Stage()
		stage.name = self.md_stage_name
		for sim in self.md_sims:
    		stage.add_tasks(set(sim.tasks()))
       	return stage


	def generate_preprocess_stage(self):
		stage = Stage()
		stage.name = self.pre_stage_name
		for preproc in self.preprocs:
			stage.add_tasks(set(preproc.tasks()))
		return stage


	def generate_ml_stage(self):
		stage = Stage()
		stage.name = self.ml_stage_name
		for alg in self.ml_algs:
			stage.add_tasks(set(alg.tasks()))
		return stage


	def generate_outlier_stage(self):
		stage = Stage()
		stage.name = self.outlier_stage_name
		for alg in self.outlier_algs:
			stage.add_tasks(set(alg.tasks()))

		stage.post_exec = {
			'condition': lambda: self.current_iter < self.max_iter,
			'on_true': self.pipeline,
			'on_false': lambda: print('Done')
		}

		return stage


    def pipeline(self):
        """
        Effects
        -------
        Adds stages to pipeline.

        """
        if self.current_iter:
            print('Finishing pipeline iteration {} of {}'.format(self.current_iter, 
                                                				 self.max_iter)) 
        # MD stage
        s1 = self.generate_md_stage()
        self.__pipeline.add_stages(s1)

        # Preprocess stage
        s2 = self.generate_preprocess_stage() 
        self.__pipeline.add_stages(s2)  

        # Learning stage
        s3 = self.generate_ml_stage() 
        self.__pipeline.add_stages(s3)

        # Outlier identification stage
        s4 = self.generate_outlier_stage(settings) 
        self.__pipeline.add_stages(s4) 

        self.current_iter += 1