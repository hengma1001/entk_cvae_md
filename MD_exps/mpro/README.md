# How to run the simulation 

```bash 
python run_openmm.py -f pdb/100-fs-peptide-400K.pdb
python run_openmm.py -f pdb/100-fs-peptide-400K.pdb -c checkpnt.chk
python run_openmm.py -f ../../Parameters/input_CoV/a_input.pdb -p ../../Parameters/input_CoV/a_input.prmtop -r ../../Parameters/input_CoV/a_input.json -l 10 -g 6 &> screen.log &
```
