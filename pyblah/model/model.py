'''
Created on 15.05.2013

@author: mtoman


'''

import sys
import os
import tempfile
import logging
import cPickle

import decisiontree
import mmf
import subprocess


logger = logging.getLogger("model")

class FileLoadException(Exception):
    '''
    Exception that occurs when a necessary file could not be loaded.
    '''
    def __init__(self, filename, msg=""):
        self.filename = filename
        
    def __str__(self):
        return repr(self.value)
    



class HTSVoiceModel(object):
    '''
    A HTS voice model consists of an MMF and different decision trees
    (might also add config, lists etc.)
    
    Currently available Tree types:
    mcep
    bndap
    logF0
    dur
    '''
    
    def __init__(self, path = None):
        '''
        Constructor
        '''
        
        self.defaultStateRange = range( 2, 7 )     # states [2-6]
        self.cmpMMF = None
        self.durMMF = None        
        self.modelPath = None
        self.trees = {}                             # contains treename -> MetaTree object           
               
        if path:
            self.loadModel( path )
            
    def loadModel(self, path):
        """ loads the model in path """
        
        self.modelPath = path
        
        # load mmfs      
        self.cmpMMF = self._loadMMF( "cmp" )
        self.durMMF = self._loadMMF( "dur" )
        
        # load trees
        self.addMetaTree( "mcep", self._loadMetaTree( os.path.join( self.modelPath, "tree.mcep.inf" ) ) )
        self.addMetaTree( "bndap", self._loadMetaTree( os.path.join( self.modelPath, "tree.bndap.inf" ) ) )
        self.addMetaTree( "logF0", self._loadMetaTree( os.path.join( self.modelPath, "tree.logF0.inf" ) ) )
        self.addMetaTree( "dur", self._loadMetaTree( os.path.join( self.modelPath, "tree.dur.inf" ) , [2] ) )

            
    def getMMF(self):
        """ Returns an HTSMMF object to the models MMF """
        return self.mmf

    def getMetaTree(self, treename ):
        """ Returns an MetaTree object for name treename (i.e. "mcep").
            This metatree then contains trees for the different states """
        return self.trees[ treename ]
    
    def addMetaTree(self, treename, tree ):
        """ Adds a tree with name treename (i.e. "mcep") and a MetaTree object """
        self.trees[ treename ] = tree
            
    def classifyLabelString( self, labelString ):
        ''' Classifies a label using all loaded trees '''
        ret = []
        for t in self.trees:
            ret.append( self.trees[t].classifyLabelString( labelString ) )
        return ret

    def getCmpPDF(self, modelName, mix=1 ):
        ''' Convenience method, returns the pdf with given macroname for the cmp mmf. '''
        return self.cmpMMF.getMacro( '~p', modelName ).mixture.pdfs[mix]                                 
                           
                           
    def _loadMetaTree(self, filename, staterange=None):
        """ Loads and returns a tree in a MetaTree object """                
        if staterange is None:
            staterange = self.defaultStateRange                    
        logger.info( "Loading trees: " + filename )
        mt = decisiontree.MetaTree()        
        mt.loadTrees( filename, staterange )
        return mt
        

    def _loadMMF(self, mmftype):
        """ Loads an MMF and returns it, also works for binary mmfs by using HHED to convert it. """        
        configAvailable = True
        modeldir = self.modelPath                
        ret = None         
        
        # is there a pickle file available? get that
        # TODO: check if its up to date       
        #mmffilepkl = os.path.join( modeldir, 'clustered.' + mmftype + '.mmf.pkl' )
        #if os.path.exists(mmffilepkl):
        #    logger.info( "Loading " + mmftype + " mmf (pickle): " + mmffilepkl )
        #    f = open(mmffilepkl, 'rb')
        #    ret = cPickle.load( f )
        #    f.close()            
            # in this case, do nothing else!
        #    return ret        
        
        # is there a file with .ascii suffix available? load that
        mmffileascii = os.path.join( modeldir, 'clustered.' + mmftype + '.mmf.ascii' )
        if os.path.exists(mmffileascii):
            logger.info( "Loading " + mmftype + " mmf (ascii): " + mmffileascii )
            ret = mmf.MMF(mmffileascii)
        
        # else use default filename and convert it
        else:                                        
            # check mmf file
            mmffile = os.path.join( modeldir, 'clustered.' + mmftype + '.mmf' ) 
            if not os.path.exists(mmffile):            
                raise FileLoadException( mmffile )
            
            # check if the mmf is actually ascii
            textchars = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
            is_binary_string = lambda ibytes: bool(ibytes.translate(None, textchars))

            if not is_binary_string( open(mmffile).read(1024) ):
                logger.info( "Loading " + mmftype + " mmf (ascii): " + mmffile )
                ret = mmf.MMF(mmffile)
            
            # file is binary, try to convert it using hhed
            else:            
                logger.info( "Converting " + mmftype + " mmf from binary to ascii: " + mmffile )
            
                # try to find config, first try one level higher, else two levels higher 
                # (there might be another subfolder in the "models" folder)
                conf = os.path.join(modeldir, '..', 'config', 'general.conf')
                if not os.path.exists(conf):
                    conf = os.path.join(modeldir, '..', '..', 'config', 'general.conf')
                    if not os.path.exists(conf):
                        #raise FileLoadException( "general.conf" )
                        configAvailable = False
                    
                    #TODO: generate config if not available
                                        
                # check list file 
                contextlist = os.path.join(modeldir, 'context.' + mmftype + '.list')
                if not os.path.exists(contextlist):
                    contextlist = os.path.join(modeldir, 'context.full.list')
                    if not os.path.exists(contextlist):
                        raise FileLoadException( contextlist )
                
                # find HHEd...
                # TODO: think about different solution here :(
                selfpath = os.path.dirname(os.path.realpath(__file__))
                HHEd = os.path.join( os.path.abspath(selfpath), '..', '..', 'hts', 'tool', 'bin', 'HHEd')
                print HHEd
                if not os.path.exists(HHEd):
                    raise FileLoadException( HHEd )
                    
                # HHEd -A -C ../config/general.conf -H 1/clustered.dur.mmf -w clustered.dur.mmf.txt /dev/null 1/context.dur.list   
                #(handle, asciifile) = tempfile.mkstemp()
                #os.close(handle)
                asciifile = mmffile + ".ascii"
                                              
                
                (handle, nullhed) = tempfile.mkstemp()
                os.close(handle)                
                
                # call HHEd to make ascii mmf file
                if configAvailable:
                    logger.info( "Config used for converting: " + conf)
                    cmndlist = [
                        HHEd,
                        #'-A',
                        '-C', conf,
                        '-H', mmffile,
                        '-w', asciifile,
                        nullhed,
                        contextlist
                    ]
                else:
                    logger.info( "No config available for converting.")
                    cmndlist = [
                        HHEd,
                        #'-A',
                        '-H', mmffile,
                        '-w', asciifile,
                        nullhed,
                        contextlist
                    ]
                
                logger.info( "Calling: " + " ".join( cmndlist ) )
                    
                subprocess.call(cmndlist)
                
                logger.info( "Loading " + mmftype + " mmf (ascii): " + asciifile )
                ret = mmf.MMF(asciifile)
                                
                logger.info( "Removing: " + asciifile )                        
                os.remove( nullhed )

       
        # store pickle file 
        #f = open( mmffilepkl, 'wb')
        #cPickle.dump( ret, f, cPickle.HIGHEST_PROTOCOL )
        #f.close()
                                                                  
        return ret
        
        
        

class ModelManager(object):
    def __init__(self):
        self.models = {}
        
    def getModel(self, path):        
        if path in self.models:
            return self.models[path]
        else:        
            md = HTSVoiceModel()        
            md.loadModel(path)
            self.models[path] = md
            return md
                
        
        

modelManager = ModelManager()        
        
def get_model_manager():        
    return modelManager
                
        

#------------------------------------------------------------------------------
# test main
#------------------------------------------------------------------------------        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit( "Usage: python " + __file__ + " <model directory>" )
        
    logging.basicConfig(level=logging.DEBUG)        
    model = HTSVoiceModel()
    try:
        model.loadModel( sys.argv[1] )
    except FileLoadException as fle:
        print "Could not load file " + fle.filename
        