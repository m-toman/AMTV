'''
Created on 28.01.2013

@author: mtoman
'''

import sys
import os
import Tkinter
import tkSnack
from Tkinter import *
import time
from rat.io import label
        
#------------------------------------------------------------------------------
# FormantExtractor
#------------------------------------------------------------------------------
class FormantExtractor(object):
    '''
    Extracts formants from a given sound file and transcription.
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        root = Tk()
        tkSnack.initializeSnack(root)        
        
        print "FormantExtractor: Initialized"

    
    def extract(self, soundPath, transcriptPath, play=False ):
        """ extracts formants from soundfile given transcription """
        
        print "FormantExtractor: Loading " + soundPath
                      
        mysound = tkSnack.Sound()
        mysound.read( soundPath )
        
        #mysound.play(blocking=True)                
        #c = tkSnack.SnackCanvas(root, height=400)
        #c.pack()
        #c.create_waveform(0, 0, sound=mysound, height=100, zerolevel=1)
        #c.create_spectrogram(0, 150, sound=mysound, height=200)                    
        #root.mainloop()
        
        freq = mysound['frequency']
        print "File format: " + mysound[ 'fileformat' ]
        print "Encoding: " + mysound[ 'encoding' ]        
        print "Frequency: " + str(freq)
        print "Samples: " + str( mysound.length() )
        print "Length: " + str( float(mysound.length()) / float(mysound['frequency']) )  + "s"
        
        
        print "FormantExtractor: Loading " + transcriptPath
        
        lr = label.UtteranceLabel( transcriptPath )
        
        results = []
        
        for lab in lr.labels:
            
            #if lab.phon == "GS" or lab.phon == "P6": continue
            
            lab.begintime /= 10000.0      # to ms
            lab.endtime  /= 10000.0       # to ms
            print lab.phon + " " + str( lab.begintime ) + " " + str( lab.endtime )
            
            beginsample = int(lab.begintime * freq / 1000.0)
            endsample = int(lab.endtime * freq / 1000.0)
            print beginsample , endsample            
                                    
                                    #, framelength=(1.0/freq)
                                    #, windowlength=0.01 
            #formants = mysound.formant( start=beginsample, end=endsample, ds_freq=freq, framelength=0.001, windowlength=0.01 )
            formants = mysound.formant( start=beginsample, end=endsample)
            
            for f in formants:
                print f[0], f[1]
                                                
           
            
            middle = formants[len(formants)/2]
            results.append( ( lab.phon, middle[0], middle[1] ) )     
            
            print
            
            if play:
                tmpmysound = tkSnack.Sound()
                tmpmysound.read( soundPath )            
                tmpmysound.crop(beginsample, endsample)
                tmpmysound.play(blocking=True)
                time.sleep(0.5)
                                     
        
        #sFilter = tkSnack.Filter
        #mysound.filter(filter=sFilter)
        
        print "Done"
        return results
        



#------------------------------------------------------------------------------
# sample main
#------------------------------------------------------------------------------        
if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit("Usage: python FormantExtractor.py soundfile transcriptionfile\n")
        
    extractor = FormantExtractor()
    
    extractor.extract( sys.argv[1], sys.argv[2], play=True )