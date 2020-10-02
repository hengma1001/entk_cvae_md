import os 

def create_md_path(label, h5_dir=None): 
    """
    create MD simulation path based on its label (int), 
    and automatically update label if path exists. 
    """
    md_path = f'omm_runs_{label}'
    try:
        os.mkdir(md_path)

        if isinstance(h5_dir, str) and not h5_dir.endswith('.h5'):
            os.mkdir(os.path.join(md_path, h5_dir))

        return md_path
    except: 
        return create_md_path(label + 1, h5_dir)


def touch_file(file): 
    """
    create an empty file for bookkeeping sake
    """
    with open(file, 'w'): 
        pass
