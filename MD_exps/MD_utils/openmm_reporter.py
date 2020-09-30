import simtk.openmm.app as app
import simtk.openmm as omm
import simtk.unit as u 

import numpy as np 
import h5py 

from MDAnalysis.analysis import distances

class ContactMapReporter(object):
    def __init__(self, file, reportInterval):
        self._file = h5py.File(file, 'w', libver='latest')
        self._file.swmr_mode = True
        self._out = self._file.create_dataset('contact_maps', shape=(2,0), maxshape=(None, None))
        self._reportInterval = reportInterval

    def __del__(self):
        self._file.close()

    def describeNextReport(self, simulation):
        steps = self._reportInterval - simulation.currentStep%self._reportInterval
        return (steps, True, False, False, False, None)

    def report(self, simulation, state):
        ca_indices = []
        for atom in simulation.topology.atoms():
            if atom.name == 'CA':
                ca_indices.append(atom.index)
        positions = np.array(state.getPositions().value_in_unit(u.angstrom))
        time = int(np.round(state.getTime().value_in_unit(u.picosecond)))
        positions_ca = positions[ca_indices].astype(np.float32)
        distance_matrix = distances.self_distance_array(positions_ca)
        contact_map = (distance_matrix < 8.0) * 1.0 
        new_shape = (len(contact_map), self._out.shape[1] + 1) 
        self._out.resize(new_shape)
        self._out[:, new_shape[1]-1] =contact_map
        self._file.flush()

import uuid
import subprocess

class CopySender:
    def __init__(self,, target, method='cp'):
        self.method = method
        self.target = target
        self.processes = []

    def send(self, path):
        p = subprocess.Popen(f'{self.method} {path} {self.target}', shell=True)
        self.processes.append(p)
        self.processes = [p for p in self.processes if p.poll() is None]

def write_contact_map_h5(file_name, rows, cols):

    # Helper function to create ragged array
    ragged = lambda data: np.array(data, dtype=object)

    # Specify variable length arrays
    dt = h5py.vlen_dtype(np.dtype('int16'))

    with open_h5(file_name, 'w', swmr=False) as h5_file:
        # list of np arrays of shape (2 * X) where X varies
        data = ragged([np.concatenate(row_col) for row_col in zip(rows, cols)])
        h5_file.create_dataset('contact_map',
                               data=data,
                               chunks=(1,) + data.shape[1:],
                               dtype=dt,
                               fletcher32=True)

class SparseContactMapReporter:

    def __init__(self, file, reportInterval, native_pdb,
                 selection='CA', threshold=8., batch_size=1024,
                 senders=[]):

        self._file_idx = 0
        self._base_name = file
        self._report_interval = reportInterval
        self._selection = selection
        self._threshold = threshold
        self._batch_size = batch_size
        self._senders = senders

        self._init_batch()

    def _init_batch(self):
        # Frame counter for writing batches to HDF5
        self._num_frames = 0
        # Row, Column indices for contact matrix in COO format
        self._rows, self._cols = [], []

    def __del__(self):
        self._file.close()

    def describeNextReport(self, simulation):
        steps = self._report_interval - simulation.currentStep % self._report_interval
        return (steps, True, False, False, False, None)

    def _report_contact_maps(self, positions):

        contact_map = distances.contact_matrix(positions, self._threshold,
                                               returntype='sparse')

        # Represent contact map in COO sparse format
        coo = contact_map.tocoo()
        self._rows.append(coo.row.astype('int16'))
        self._cols.append(coo.col.astype('int16'))

    def _report(self, simulation, state):
        atom_indices = [a.index for a in simulation.topology.atoms() if a.name == self._selection]
        all_positions = np.array(state.getPositions().value_in_unit(u.angstrom))
        positions = all_positions[atom_indices].astype(np.float32)

        self._report_contact_maps(positions)

        self._num_frames += 1

        if self._num_frames == batch_size:
            file_name = f'{self._base_name}_{self._file_idx:05d}_{uuid.uuid4()}.h5'
            write_contact_map_h5(file_name, self._rows, self._cols)
            self._init_batch()
            self._file_idx += 1

            for sender in self._senders:
                sender.send(file_name)
