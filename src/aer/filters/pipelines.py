import os

from aer import logger
from aer.filters.transitions2 import aer_sign_transitions
from aer.types import aer_filtered_event_dtype
from compmake.utils import safe_pickle_dump, safe_pickle_load
import numpy as np

from . import aer_raw_relative_timestamp, aer_raw_only_middle
from ..logs import aer_raw_events_from_file_all


def aer_pipeline_transitions1(raw_sequence, name):
    """ Iterates over transitions events """
    raw_sequence = aer_raw_relative_timestamp(raw_sequence)
    raw_sequence = aer_raw_only_middle(raw_sequence,
                                       xmin=3, xmax=124, ymin=3, ymax=124)
    return aer_pipeline_choice(raw_sequence, name)


def aer_pipeline_transitions1_all(filename, name):
    """ Uses caches """
    cache_name = os.path.splitext(filename)[0] + '.events-%s.pickle' % name
    if os.path.exists(cache_name):
        logger.debug('Using cache %s ' % cache_name)
        return safe_pickle_load(cache_name)
    else:
        logger.debug('Cache not found %s' % cache_name)
        values = aer_pipeline_transitions1_all_slave(filename, name)
        safe_pickle_dump(values, cache_name)
        return values
    
    
def aer_pipeline_transitions1_all_slave(filename, name):
    """ Returns all events in a numpy array """
    logger.info('Opening file %s' % filename)
    limit = None
    raw_sequence = aer_raw_events_from_file_all(filename, limit=limit)
    filtered = aer_pipeline_transitions1(raw_sequence, name)
    
    # Upper bound on the number
    n = len(raw_sequence)
    logger.info('Allocating %d size' % n)
    out = np.zeros(dtype=aer_filtered_event_dtype, shape=n)
    nf = 0
    for i, f in enumerate(filtered):
        out[i] = f
        nf += 1
    logger.info('Read %d filtered events ' % nf)
    if nf == 0:
        raise ValueError('Not enough filtered events.')
    valid = out[:nf]
    return valid



def collect_all(sequence):
    logger.info('Reading all events...')
    l = list(sequence)
    logger.info('... read %d events.' % len(l))
    return np.array(l, dtype=l[0].dtype)


pipelines = {}
pipelines['p2n'] = lambda seq: aer_sign_transitions(seq, p2n=True, n2p=False) 
pipelines['n2p'] = lambda seq: aer_sign_transitions(seq, p2n=False, n2p=True)
pipelines['both'] = lambda seq: aer_sign_transitions(seq, p2n=True, n2p=True)

def aer_pipeline_choice(raw_sequence, name):
    if name not in pipelines:
        msg = "Could not find name %s" % name
        raise ValueError(msg)
    return pipelines[name](raw_sequence)
