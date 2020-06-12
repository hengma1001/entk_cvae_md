import os 
import numpy as np
import h5py 
import errno 
import MDAnalysis as mda 
from tqdm import tqdm
from cvae.CVAE import CVAE
from keras import backend as K 
from sklearn.cluster import DBSCAN 
from sklearn.neighbors import LocalOutlierFactor 

def triu_to_full(cm0):
    num_res = int(np.ceil((len(cm0) * 2) ** 0.5))
    iu1 = np.triu_indices(num_res, 1)

    cm_full = np.zeros((num_res, num_res))
    cm_full[iu1] = cm0
    cm_full.T[iu1] = cm0
    np.fill_diagonal(cm_full, 1)
    return cm_full


def cm_to_cvae(cm_data, padding=2): 
    """
    A function converting the 2d upper triangle information of contact maps 
    read from hdf5 file to full contact map and reshape to the format ready 
    for cvae
    """
    # transfer upper triangle to full matrix 
    cm_data_full = np.array([triu_to_full(cm) for cm in cm_data.T])

    # padding if odd dimension occurs in image 
    pad_f = lambda x: (0,0) if x%padding == 0 else (0,padding-x%padding) 
    padding_buffer = [(0,0)] 
    for x in cm_data_full.shape[1:]: 
        padding_buffer.append(pad_f(x))
    cm_data_full = np.pad(cm_data_full, padding_buffer, mode='constant')

    # reshape matrix to 4d tensor 
    cvae_input = cm_data_full.reshape(cm_data_full.shape + (1,))   
    
    return cvae_input


def stamp_to_time(stamp): 
    import datetime
    return datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d %H:%M:%S') 
    

def find_frame(traj_dict, frame_number=0): 
    local_frame = frame_number
    for key in sorted(traj_dict.keys()): 
        if local_frame - int(traj_dict[key]) < 0: 
            dir_name = os.path.dirname(key) 
            traj_file = os.path.join(dir_name, 'output.dcd')             
            return traj_file, local_frame
        else: 
            local_frame -= int(traj_dict[key])
    raise Exception('frame %d should not exceed the total number of frames, %d' % (frame_number, sum(np.array(traj_dict.values()).astype(int))))
    
    
def write_pdb_frame(traj_file, pdb_file, frame_number, output_pdb): 
    mda_traj = mda.Universe(pdb_file, traj_file)
    mda_traj.trajectory[frame_number] 
    PDB = mda.Writer(output_pdb)
    PDB.write(mda_traj.atoms)     
    return output_pdb

def make_dir_p(path_name): 
    try:
        os.mkdir(path_name)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass


def outliers_from_cvae(model_weight, cvae_input, hyper_dim=3, eps=0.35): 
    os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"]=str(0)  
    cvae = CVAE(cvae_input.shape[1:], hyper_dim) 
    cvae.model.load_weights(model_weight)
    cm_predict = cvae.return_embeddings(cvae_input) 
    db = DBSCAN(eps=eps, min_samples=10).fit(cm_predict)
    db_label = db.labels_
    outlier_list = np.where(db_label == -1)
    K.clear_session()
    return outlier_list


def predict_from_cvae(model_weight, cm_files, hyper_dim=3): 
    os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"]=str(0)  
    # decoy run to identify cvae input shape 
    cm_h5 = h5py.File(cm_files[0], 'r', libver='latest', swmr=True)
    cm_data = cm_h5[u'contact_maps']
    cvae_input = cm_to_cvae(np.array(cm_data), padding=4)
    cvae = CVAE(cvae_input.shape[1:], hyper_dim) 
    cm_h5.close()
    # load weight 
    cvae.model.load_weights(model_weight)
    train_data_length = []
    cm_predict = [] 
    for i, cm_file in enumerate(cm_files[:]): 
        # Convert everything to cvae input
        cm_h5 = h5py.File(cm_file, 'r', libver='latest', swmr=True)
        cm_data = cm_h5[u'contact_maps']
        cvae_input = cm_to_cvae(np.array(cm_data), padding=4)
        cm_h5.close()

        # A record of every trajectory length
        train_data_length += [cvae_input.shape[0]]
        # Get the predicted embeddings 
        embeddings = cvae.return_embeddings(cvae_input) 
        cm_predict.append(embeddings) 
        print embeddings.shape, i

    cm_predict = np.vstack(cm_predict) 
    # clean up the keras session
    del cvae 
    K.clear_session()
    return cm_predict, train_data_length


def outliers_from_latent_loc(cm_predict, n_outliers=500, n_jobs=8): 
    clf = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=n_jobs).fit(cm_predict) 
    # label = clf.predict(cm_predict) 
    return np.argsort(clf.negative_outlier_factor_)[:n_outliers]

    
def outliers_from_latent_dbscan(cm_predict, eps=0.35): 
    db = DBSCAN(eps=eps, min_samples=10).fit(cm_predict)
    db_label = db.labels_
    outlier_list = np.array(np.where(db_label == -1)).flatten()
    return outlier_list


def outliers_from_latent_ranked(cm_predict, eps=.5):
    # run DBSCAN 
    db = DBSCAN(eps=eps, min_samples=10).fit(cm_predict)
    db_labels = db.labels_ 
#     print(1, sum(db_labels==-1))
    # get indices for each group, outliers and edgy 
    outlier_list = np.array(np.where(db_labels == -1)).flatten()
    core_indices = db.core_sample_indices_
    edgy_pnts = [i for i, label in enumerate(db_labels) if label != -1 and i not in core_indices]
#     print(2,len(edgy_pnts))
    # distance calculation 
    dist_list = np.empty(len(outlier_list))
    for i, outlier in enumerate(outlier_list):
        dist = [np.linalg.norm(cm_predict[outlier] - cm_predict[ind]) for ind in edgy_pnts]
        dist_list[i] = min(dist)
#     print(3)
    # rank outliers according to dist 
    rank_outlier_list = [outlier for _, outlier in sorted(zip(dist_list, outlier_list))]
    return rank_outlier_list	
