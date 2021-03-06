import os

from aer.logs.chunks import aer_iterate_intervals
from aer.logs.load_aer_logs import aer_raw_events_from_file_all_faster
from procgraph import Block, BadConfig
from procgraph.block_utils import IteratorGenerator


class AERChunksStream(IteratorGenerator):
    ''' 
        Yields packets of AER events with the given interval.
    '''
    Block.alias('aer_chunk_stream')
    
    Block.config('filename', 'AEDAT Filename.')
    Block.config('interval', 'Interval')

    Block.output('events', 'Event stream')
    

    def init_iterator(self):
        filename = self.config.filename
        interval = self.config.interval
        
        if not os.path.exists(filename):
            msg = 'Not existent file %r.' % filename
            raise BadConfig(block=self, error=msg, config='filename')
        
        raw_events = aer_raw_events_from_file_all_faster(filename)
        chunks = aer_iterate_intervals(raw_events, interval)
        for timestamp, es in chunks:
            yield 0, timestamp, es

