from . import logger, np
from ..utils import wrap_script_entry_point
from optparse import OptionParser
from rcl.library.event_text_log_reader import (aer_raw_sequence,
    AER_Filter, aer_raw_relative_timestamp, aer_raw_only_minus,
    aer_filtered_cutoff)
import os
from reprep.graphics.filter_scale import scale
from procgraph_pil.imwrite import imwrite
from reprep.graphics.zoom import rgb_zoom

class TrackerFixedFreq():
    def __init__(self, freq, sigma, shape=(128, 128)):
        self.freq = freq
        self.sigma = sigma
        self.p = np.zeros(shape, 'float')

        self.last_motion = None
        self.motion_interval = 0.001
        self.count = 0
        
    def integrate(self, aer_filtered_event):
        self.count += 1
        
        e = aer_filtered_event
        f = e['frequency']
        t = e['timestamp']
        
        w = np.exp(-((f - self.freq) / self.sigma) ** 2)
        
        self.p[e['x'], e['y']] += w

        self.handle_motion(t)
        
    def handle_motion(self, t):    
        if self.last_motion is None:
            self.last_motion = t
        else:
            if t - self.last_motion >= self.motion_interval:
                logger.info('Motion') 
                self.p *= 0.95
                self.last_motion = t

def rcl_filter_main(args):
    parser = OptionParser(usage="")
    parser.disable_interspersed_args()
    
    parser.add_option("--filename")
    parser.add_option("--frequency", type='float', default=1000.0)
    parser.add_option("--sigma", type='float', default=20.0)
    
    parser.add_option("--outdir", "-o", help="output directory [%default]")
    parser.add_option("--png_interval_ms", default=10.0, type='float')
    
    (options, args) = parser.parse_args()
    if args:
        raise Exception()

    freq = options.frequency
    sigma = options.sigma
    
    if options.outdir is None:
        options.outdir = os.path.splitext(options.filename)[0] + '_filter'
        if not os.path.exists(options.outdir):
            os.makedirs(options.outdir)
       
    line_stream = open(options.filename)
    raw_sequence = aer_raw_sequence(line_stream)
    raw_sequence = aer_raw_only_minus(raw_sequence)
    raw_sequence = aer_raw_relative_timestamp(raw_sequence)
    aer_filter = AER_Filter()
    filtered = aer_filter.filter(raw_sequence)
    # remove above frequency
    cutoff = aer_filtered_cutoff(filtered,
                                 min_frequency=freq - 4 * sigma,
                                 max_frequency=freq + 4 * sigma)
    
    tf = TrackerFixedFreq(freq=freq, sigma=sigma)
    
    
    def write_png(time):
        dirname = os.path.join(options.outdir, 'f%05d' % freq)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        time_us = time * 1000 * 1000
        filename = os.path.join(dirname, 'prob-ms%08d.png' % time_us)
        rgb = scale(tf.p)
        rgb = rgb_zoom(rgb, K=4)
        imwrite(rgb, filename)
        logger.debug('print to %r' % filename)
    
    last_write = None 
    
    
    for e in cutoff:
        tf.integrate(e)
    
        if last_write is None:
            last_write = e['timestamp']
      
        interval = options.png_interval_ms / 1000.0
        delay = e['timestamp'] - last_write
        if  delay >= interval:
            print ('Delay: %.8fs > %.8fs' % (delay, interval))
            write_png(e['timestamp'])
            last_write = e['timestamp']
    
   
def main():
    wrap_script_entry_point(rcl_filter_main, logger)
