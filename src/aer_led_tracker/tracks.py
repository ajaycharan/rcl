import numpy as np
from contracts import contract, new_contract
from aer_led_tracker.utils.vectors import vector_norm

aer_track_dtype = [
   ('timestamp', 'float'),
   ('id_track', 'S32'),
   ('npeaks', 'int'),
   ('peak', 'int'),
   ('i', 'float'),
   ('j', 'float'),
   ('quality', 'float')
]

@new_contract
def track_dtype(x):
    if not x.dtype == aer_track_dtype:
        msg = 'Invalid dtype: %r' % x.dtype
        raise ValueError(msg)

new_contract('tracks_array', 'array[>=1],track_dtype')

def create_track_observation(frequency, timestamp, peak, npeaks, coords, quality):
    id_track = '%d' % frequency
    val = (timestamp, id_track, npeaks, peak, coords[0], coords[1], quality)
    a = np.array(val, dtype=aer_track_dtype)
    return a

# @contract(tracks='tracks_array')
def enumerate_id_track(tracks):
    id_tracks = np.unique(tracks['id_track'])
    for id_track in id_tracks:
        sel = tracks['id_track'] == id_track
        yield id_track, tracks[sel]

@contract(tracks='tracks_array')
def assert_only_one_id(tracks):
    x = np.unique(tracks['id_track'])
    assert len(x) == 1
    
@contract(tracks='tracks_array,array[N]', returns='array[(N-1)x2]')
def track_velocities(tracks):
    assert_only_one_id(tracks)
    
    coords = track_coords(tracks)
    vel = np.diff(coords, axis=0)
    return vel

@contract(tracks='tracks_array,array[N]', returns='array[N-1]')
def track_velocities_norm(tracks):
    assert_only_one_id(tracks)
    velocities = track_velocities(tracks)
    vn = [vector_norm(x) for x in velocities]
    return np.array(vn)

@contract(tracks='tracks_array,array[N]', returns='array[Nx2]')
def track_coords(tracks):
    assert_only_one_id(tracks)
    i = tracks['i']
    j = tracks['j']
    coords = np.vstack((i, j)).T
    n = len(i)
    assert coords.shape == (n, 2)
    return coords
