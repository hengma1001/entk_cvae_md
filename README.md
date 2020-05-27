# entk_cvae_md
A script that runs Molecular Dynamics simulations under supervision of Machine 
Learning model on Summit@ORNL through Radical toolkit. 

```bash
module load python/2.7.15-anaconda2-5.3.0 
source activate /ccs/home/hm0/.conda/envs/entk

export RMQ_HOSTNAME=two.radical-project.org 
export RMQ_PORT=33235 
export RADICAL_PILOT_DBURL=mongodb://hyperrct:h1p3rrc7@two.radical-project.org:27017/hyperrct 
export RADICAL_PROFILE=True
export RADICAL_PILOT_PROFILE=True
export RADICAL_ENTK_PROFILE=True

```

The code is running as a preliminary fashion and will be cleaned up soon. 
