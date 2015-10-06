#!/usr/bin/python

import re
import logging

logger = logging.getLogger("mmf")

#-------------------------------------------
# PDFInfo
#-------------------------------------------
class PDFInfo:
    def __init__(self):
        self.means = []
        self.variances = []
        
    def setMeans(self, m):
        self.means = m
        
    def setVariances(self, v):
        self.variances = v

#-------------------------------------------
# MixtureInfo
#-------------------------------------------
class MixtureInfo:
    def __init__(self, owner, mixtureNumber):
        """ owner is the StateInfo, pdf is PDFInfo """
        self.mixtureNumber = mixtureNumber
        self.owner = owner
        self.weight = 0.0
        self.pdf = None
        
    def setPDF(self, pdf):        
        self.pdf = pdf
        
    def setWeight(self, weight):
        self.weight = weight

#-------------------------------------------
# StreamInfo
#-------------------------------------------
class StreamInfo:
    def __init__(self, owner, streamNumber):
        """ owner is the StateInfo """
        self.streamNumber = streamNumber
        self.mixtures = {}
        self.owner = owner
        
    def addMixtureInfo(self, mixtureInfo):
        self.mixtures[ mixtureInfo.mixtureNumber ] = mixtureInfo
        
    def getFullName(self):
        return self.owner.owner.name + ', state: ' + str(self.owner.stateNumber) + ', stream: ' + str(self.streamNumber)        

#-------------------------------------------
# StateInfo
#-------------------------------------------    
class StateInfo:
    def __init__(self, owner, stateNumber):
        """ owner is another macro """
        self.streamInfoDict = {}
        self.stateNumber = stateNumber
        self.owner = owner
        
    def addStreamInfo(self, streamInfo):
        self.streamInfoDict[ streamInfo.streamNumber ] = streamInfo  

#-------------------------------------------
# HMacro -> ~h macro in mono mmfs
# a macro that contains states
#-------------------------------------------
class HMacro:
    def __init__(self, name):
        self.name = name
        self.stateInfoDict = {}
        
    def addStateInfo(self, stateInfo):
        self.stateInfoDict[ stateInfo.stateNumber ] = stateInfo
        
#-------------------------------------------
# PMacro -> ~p macro in full mmfs
# i.e.: ~p "logF0_s3_145-3"
# so the macro directly contains mixtures
#-------------------------------------------
class PMacro:
    def __init__(self, name, stream):
        self.name = name
        self.stream = stream
        
        self.mixtures = {}
        
    def addMixtureInfo(self, mixtureInfo):
        self.mixtures[ mixtureInfo.mixtureNumber ] = mixtureInfo        

#------------------------------------------------
# SMacro -> ~s macro in full mmfs, shared state
#------------------------------------------------
class SMacro:
    def __init__(self, name):
        self.name = name
        self.state = None
        

#-------------------------------------------
# LabelEntry
# ~h "v^schwa-h+schwa=m@1_2/A:0_0_4/B:0-0-2@1-2&2-7#1-1$1-1!0-0;0-0|0/C:0+0+3/D:det_1/E:content+2@2+3&1+2#0+1/F:content_4/G:0_0/H:7=4@1=1|0/I:0=0/J:7+4-1"
#<BEGINHMM>
#<NUMSTATES> 7
#<STATE> 2
#~w "SWeightall"
#<STREAM> 1
#~p "mcep_s2_72"
#<STREAM> 2
#~p "logF0_s2_15-2"
#-------------------------------------------
class LabelEntry:                
    def __init__(self, name):
        self.name = name
        self.cphone = ""
        
        ret = re.match('([^ -]+)\-([^ \+]+)\+', self.name)
        if ret: self.cphone = ret.group(2)
        
        #print 'C-Phone for ' + self.name + " is " + self.cphone             
        
        self.associatedMacroNames = []
    
        

#-------------------------------------------
# HTSMMF
#-------------------------------------------
class HTSMMF:
    """ Holds data from an HTS/HTK MMF """
    
    # init
    def __init__(self):
        self.macroList = []             # for mono mmf, holds HMacro objects
        self.macroDict = {}
        self.streamList = []
        self.logFile = 'log_mmf.log'

        self.labelList = []              # for full mmf, contains LabelEntry
        self.labelDict = {}              # for full mmf, contains LabelEntry
        self.macroToLabels = {}          # for full mmf, contains nameof(~p) -> [ ~h ~h ~h ], ie. mcep_s2_234 -> [ x^x-sil.., x^sil-OY.., ... ]
        self.pmacroDict = {}             # for full mmf, contains PMacro objects
        self.smacroDict = {}             # for full mmf, contains SMacro objects
        
    # setVerbose
    def setVerbose(self, val):
        if val: logger.basicConfig(filename=self.logFile, level=logging.DEBUG)
        else: logger.basicConfig(filename=self.logFile, level=logging.WARNING)
        
        
        
    # S - Macro, shared state
    #-------------------------    
    # ~s "dur_s2_102"
    # <STREAM> 1
    # <MEAN> 1
    # 4.031463e+00
    # <VARIANCE> 1
    # 6.836528e+00
    # <GCONST> 3.760157e+00
    # <STREAM> 2
    # <MEAN> 1
    # 3.780972e+00
    # <VARIANCE> 1
    # 7.697128e+00
    # <GCONST> 3.878724e+00
    def readSMacro(self, macroname, mmfFile):
        smacro = SMacro( macroname )        
        smacro.state = StateInfo( smacro, None )
        
        stream = None
        mix = None
               
        #print "Adding smacro: " + macroname
        self.smacroDict[ macroname ] = smacro
               
        line = mmfFile.readline().strip()
        
        while line:
            
            if line.startswith( "~" ):                 
                return line
            
            # new STREAM section            
            elif line.startswith("<STREAM>"):                
                stream = StreamInfo( smacro.state, int(line.split()[1]) )
                smacro.state.addStreamInfo( stream )
                mix = MixtureInfo(stream, 1)            
                mix.setPDF( PDFInfo() )
                mix.setWeight(1.0)
                stream.addMixtureInfo( mix )                
                
            # read means for current stream/mix/pdf
            elif stream and line.startswith( "<MEAN>" ):
                line = mmfFile.readline().strip()
                mix.pdf.setMeans(map(float, line.split()))
                
            # read variances for current stream/mix/pdf                
            elif stream and line.startswith( "<VARIANCE>" ):                 
                line = mmfFile.readline().strip()
                mix.pdf.setVariances(map(float, line.split()))               
            
            line = mmfFile.readline().strip()                        
                  
        return None    
            

    # P- Macro, shared stream
    #-------------------------
    #~p "mcep_s2_97"
    #<STREAM> 1
    #<MEAN> 120
    # 4.529162e+00 5.270991e-02 -3.566374e-01 1.475486e+00 4.135128e-02 4.618275e-01 -2.068399e-02 3.665279e-01 2.591737e-01 2.853509e-01 7.972557e-02 3.055930e-01 1.052690e-01 1.880983e-01 2.416319e-02 2.795610e-02 -8.716719e-02 4.869177e-02 -2.237043e-02 6.059657e-02 -8.859082e-02 -2.925542e-02 -6.099129e-02 -1.704981e-04 -1.217862e-01 8.400177e-03 -3.748318e-02 8.393485e-03 -3.058818e-02 6.475165e-02 -5.597675e-02 -1.031008e-02 -4.275885e-02 6.848398e-02 -5.252855e-02 2.141088e-03 -2.706051e-02 -2.184314e-02 -7.740860e-02 6.625950e-02 1.235886e-01 -2.374133e-01 -1.103416e-01 -1.570142e-02 -4.393163e-02 -2.221312e-02 -1.288308e-02 -1.914864e-03 -1.030369e-02 4.572805e-04 -8.036544e-03 5.791422e-03 -1.402497e-03 9.536247e-03 1.170312e-02 1.750364e-02 1.664449e-02 1.909321e-02 6.464371e-03 5.484439e-03 -1.203959e-03 2.295552e-03 3.652232e-03 6.060214e-03 2.630744e-03 6.476380e-03 4.337474e-03 1.162881e-03 1.157596e-03 3.108819e-03 -1.239175e-03 8.459451e-04 -1.104668e-03 4.180601e-03 3.676374e-03 2.481273e-03 -5.096195e-04 -2.759750e-04 -1.630568e-03 4.781733e-03 -6.902804e-04 7.739620e-02 2.776514e-02 -3.262541e-02 -6.751866e-03 -1.078151e-02 -2.064562e-03 -1.067889e-02 -1.125452e-02 -1.250784e-02 -6.217085e-03 -2.959767e-03 1.897088e-03 -1.983848e-03 -1.366929e-03 -5.314090e-03 -3.097737e-03 -4.036894e-03 -2.809164e-03 -6.121532e-03 -3.404597e-03 -3.114668e-03 -1.935069e-03 -1.160055e-04 2.328403e-03 -9.855669e-04 2.229909e-04 -7.199371e-04 2.618338e-03 2.779936e-03 1.292643e-03 1.803393e-03 1.493117e-03 -2.174425e-03 -7.163017e-04 -4.367811e-04 -2.257627e-04 -3.894498e-04 -3.364580e-04 -1.679721e-03
    #<VARIANCE> 120
    # 5.772265e-01 2.482442e-01 1.778423e-01 5.969861e-02 5.989021e-02 3.016227e-02 4.126487e-02 2.676740e-02 2.495334e-02 1.487814e-02 1.652261e-02 1.627039e-02 1.305866e-02 1.148141e-02 1.218177e-02 1.920635e-02 1.084015e-02 1.474434e-02 1.396871e-02 1.016491e-02 7.401001e-03 1.293992e-02 1.091745e-02 1.643822e-02 9.129956e-03 8.044593e-03 6.006890e-03 1.012726e-02 6.148882e-03 5.926597e-03 1.050758e-02 5.852045e-03 7.975338e-03 6.574704e-03 5.656794e-03 5.664792e-03 5.550032e-03 4.822371e-03 6.623738e-03 5.681174e-03 1.893105e-02 1.776418e-02 5.280633e-03 4.623470e-03 2.059483e-03 1.490344e-03 1.381244e-03 1.577352e-03 1.259761e-03 1.155563e-03 8.369723e-04 8.792699e-04 9.560282e-04 9.036436e-04 8.215706e-04 7.549797e-04 6.772924e-04 7.704477e-04 8.414154e-04 8.720103e-04 6.377807e-04 6.385241e-04 6.055082e-04 6.562697e-04 6.158879e-04 6.198792e-04 5.730005e-04 6.143965e-04 5.983388e-04 6.370408e-04 6.029417e-04 5.225643e-04 5.075627e-04 5.390368e-04 5.442120e-04 4.730693e-04 5.032250e-04 4.528882e-04 3.815825e-04 4.749613e-04 2.474896e-02 6.109067e-03 2.708655e-03 2.495882e-03 1.441033e-03 1.035267e-03 1.088844e-03 1.108051e-03 1.028103e-03 9.954644e-04 7.374678e-04 8.683304e-04 9.479322e-04 8.959054e-04 8.689749e-04 7.744863e-04 7.178260e-04 7.383006e-04 7.036419e-04 7.530121e-04 7.234100e-04 7.391786e-04 6.435527e-04 7.339541e-04 6.772921e-04 7.887028e-04 7.285677e-04 6.659862e-04 7.069015e-04 7.356579e-04 6.773007e-04 6.649939e-04 6.926662e-04 6.916734e-04 6.717677e-04 5.961948e-04 5.801587e-04 6.105792e-04 4.983611e-04 6.068310e-04
    #<GCONST> -5.057032e+02        
    def readPMacro(self, macroname, mmfFile):
        stream = None       
        line = mmfFile.readline().strip()
        if line.startswith("<STREAM>"):
            stream = int(line.split()[1])
        else: 
            return line
        
        mac = PMacro(macroname, stream)                
                
        # mcep handling
        if macroname.startswith("mcep"):
            mix = MixtureInfo(mac, 1)            
            pdf = PDFInfo()
            
            mac.addMixtureInfo(mix)
            mix.setPDF(pdf)
            
            for j in [1, 2]:
                line = mmfFile.readline().strip()
                if line.startswith("<MEAN>"):
                    line = mmfFile.readline().strip()
                    pdf.setMeans(map(float, line.split()))
                elif line.startswith("<VARIANCE>"):
                    line = mmfFile.readline().strip()
                    pdf.setVariances(map(float, line.split()))                    
                else: 
                    return
            #TODO: logf0, bndap            
        else: 
            return None         
                  
        self.pmacroDict[ macroname ] = mac
        return None    
            
      
        
        
        
    # loadFullMMF
    def loadFullMMF(self, path):
        """ loads an mmf file containing full models """
        
        logger.info('Loading macro file %s', path)
            
        mmfFile = open(path)
        
        currentLabel = None
        hRegExp = re.compile("~h \"(.+)\"")
        pRegExp = re.compile("~p \"(.+)\"")
        sRegExp = re.compile("~s \"(.+)\"")             # ~s "dur_s2_102"
        
        # read file line by line
        line = mmfFile.readline()     
        while line:
            #print line
            
            # no ~h section till now, macro definitions?
            if currentLabel is None:
                
                # ~p macro? -> shared stream
                ret = pRegExp.match(line)
                if ret:
                    l = self.readPMacro(ret.group(1), mmfFile)
                    if l: 
                        line = l
                        continue
                    
                # ~s macro? -> shared state distribution
                ret = sRegExp.match(line)
                if ret:
                    l = self.readSMacro(ret.group(1), mmfFile)
                    if l: 
                        line = l
                        continue
                    
            
            # ~h section has begun? from now on only ~h definitions            
            # ~h "v^schwa-h+schwa=m@1_2/A:0_0_4/B:0-0-2@1-2&2-7#1-1$1-1!0-0;0-0|0/C:0+0+3/D:det_1/E:content+2@2+3&1+2#0+1/F:content_4/G:0_0/H:7=4@1=1|0/I:0=0/J:7+4-1"            
            ret = hRegExp.match(line)
            if ret:
                currentLabel = LabelEntry(ret.group(1))                
                self.labelList.append(currentLabel)
                self.labelDict[ ret.group(1) ] = currentLabel
                
                
            # we are already in the ~h section
            elif currentLabel:
                
                # link to a ~p macro which is then associated with the ~h macro            
                # <STATE> 2
                # ~w "SWeightall"
                # <STREAM> 1
                # ~p "mcep_s2_72"               
                ret = pRegExp.match(line)
                # or link to a ~s macro                
                if not ret:
                    ret = sRegExp.match(line)
                if ret:
                    currentLabel.associatedMacroNames.append(ret.group(1))
                    
                    # fill macroToLabels
                    if ret.group(1) in self.macroToLabels:
                        self.macroToLabels[ ret.group(1) ].append(currentLabel)
                    else:
                        self.macroToLabels[ ret.group(1) ] = [ currentLabel ]
                                        
            
            line = mmfFile.readline()
        mmfFile.close()
        #print 'done: ' + str(len( self.macroToLabels ))
        #print self.macroToLabels
                
        
    # loadMonoMMF    
    def loadMonoMMF(self, path):
        """ loads an mmf file containing monophon models """
        
        currentHMM = None
        currentState = None
        currentStream = None
        currentMixture = None
        
        # Example:
        # ~h "A"
        # <BEGINHMM>
        # <NUMSTATES> 7
        # <STATE> 2
        # <SWEIGHTS> 5
        # 1.000000e+00 1.000000e+00 1.000000e+00 1.000000e+00 0.000000e+00
        # <STREAM> 1
        # <MEAN> 120
        # 4.696125e+00 2.949968e+00 3.134574e-01 8.816458e-01 1.970429e-02 6.499365e-01 3.236455e-01 -2.100632e-01 -2.807565e-01 2.731812e-02 1.980597e-01 -3.675799e-02 -8.129626e-02 1.889552e-01 1.646941e-02 -1.289776e-01 -7.191063e-02 -8.503922e-02 -5.142944e-02 4.708945e-03 -1.301508e-01 -1.205762e-01 -2.791793e-02 -4.471184e-02 -3.310435e-02 4.167116e-02 -5.886093e-02 -1.739067e-02 2.174975e-02 2.013168e-03 1.526068e-02 2.820022e-02 -4.045233e-03 8.139343e-03 1.044561e-02 2.516671e-02 1.215572e-02 -1.503560e-02 -2.112125e-02 1.579380e-02 9.378761e-02 9.153476e-02 -3.943259e-03 3.806450e-03 -2.646687e-02 2.374074e-02 2.898503e-02 -4.656117e-02 -3.545107e-02 -2.300411e-02 2.819717e-02 -1.862090e-02 -3.309735e-02 1.990083e-02 1.583429e-03 -6.634455e-03 -3.381855e-03 -9.518028e-03 -4.426301e-03 -2.549598e-03 -3.076506e-03 -2.884187e-03 2.186387e-03 -2.975489e-03 4.832148e-03 1.308339e-02 -1.743729e-03 6.280211e-03 6.954642e-03 -6.576275e-04 4.461045e-03 1.880297e-03 4.778963e-03 -1.871376e-03 -3.224137e-03 1.496911e-03 -1.267739e-03 -1.200278e-03 -4.305848e-03 3.576194e-03 -7.372506e-02 -6.160514e-02 -2.629448e-03 7.157943e-03 7.199069e-03 -1.128740e-02 -1.195622e-02 1.683325e-02 1.154647e-02 3.931310e-03 -8.084111e-03 1.316739e-03 1.064620e-02 -7.454145e-03 2.635498e-04 4.661378e-03 1.686717e-03 5.327193e-03 2.250276e-03 -1.258986e-03 3.072441e-03 1.209965e-03 -7.417311e-04 6.167710e-05 -1.865989e-03 -2.905391e-03 3.621586e-04 3.377025e-04 -2.963853e-03 8.844314e-05 -3.321448e-03 -1.449478e-03 -1.439827e-03 -2.003317e-03 -2.297701e-03 6.066221e-04 -3.146972e-03 1.087785e-03 1.640665e-03 -1.389944e-03
        # <VARIANCE> 120
        # 2.749784e-01 9.513675e-02 9.151283e-02 7.004740e-02 6.639282e-02 5.846786e-02 4.681997e-02 4.555215e-02 3.252877e-02 3.858987e-02 4.224407e-02 4.190500e-02 2.866594e-02 2.525655e-02 2.227394e-02 2.177498e-02 1.459964e-02 1.985120e-02 1.503495e-02 1.568949e-02 1.634841e-02 1.390152e-02 1.478345e-02 1.550525e-02 1.553188e-02 1.173604e-02 9.394297e-03 1.201788e-02 9.938436e-03 8.747019e-03 8.849040e-03 9.817274e-03 6.372289e-03 7.423026e-03 5.927648e-03 5.913395e-03 5.848510e-03 5.512487e-03 5.220711e-03 7.363599e-03 2.489263e-02 1.073082e-02 3.360401e-03 2.513706e-03 1.973711e-03 1.693189e-03 2.335216e-03 1.915346e-03 1.364503e-03 1.332114e-03 1.159645e-03 9.800000e-04 1.099333e-03 1.042568e-03 7.632344e-04 7.993022e-04 5.957563e-04 7.604795e-04 6.706708e-04 6.345969e-04 6.288295e-04 5.336152e-04 6.252768e-04 6.391230e-04 5.661934e-04 6.331608e-04 5.145242e-04 4.738655e-04 5.501772e-04 4.354312e-04 4.913094e-04 4.626485e-04 3.851971e-04 4.831283e-04 3.829468e-04 3.732785e-04 3.603869e-04 3.458906e-04 3.119832e-04 5.431667e-04 2.544728e-02 5.996812e-03 1.494761e-03 1.115514e-03 1.235385e-03 1.107064e-03 1.210763e-03 8.309078e-04 7.964299e-04 6.786759e-04 6.709303e-04 5.907466e-04 6.343870e-04 6.149057e-04 4.585393e-04 4.753864e-04 4.183158e-04 4.501677e-04 3.928643e-04 4.064549e-04 4.214160e-04 4.000704e-04 3.696143e-04 4.195306e-04 3.726038e-04 3.557785e-04 3.535643e-04 3.656799e-04 3.461961e-04 3.616848e-04 3.172553e-04 2.983032e-04 2.908558e-04 3.325507e-04 2.619927e-04 2.673168e-04 2.908063e-04 2.554393e-04 2.491622e-04 4.217977e-04
        # <GCONST> -5.200827e+02
        
        logger.info('Loading monophon macro file %s', path)
            
        mmfFile = open(path)
        
        # read file line by line
        line = mmfFile.readline()
        while line != "":
            line = line.strip("\n").strip()
            
            # found a new ~h macro?
            ret = re.match("~h \"(\S+)\"", line)
            if ret is not None:
                currentHMM = HMacro(ret.group(1))
                self.macroList.append(currentHMM)
                self.macroDict[ currentHMM.name ] = currentHMM
                
                currentState = None
                currentStream = None
                currentMixture = None
                logger.info('Loading macro %s', currentHMM.name) 
                
            # state given?
            ret = re.match("<STATE>\s+([0-9]+)", line)
            if ret is not None:                
                currentState = StateInfo(currentHMM, int(ret.group(1)))
                currentHMM.addStateInfo(currentState)
                
                currentStream = None
                currentMixture = None                

            # stream given?            
            ret = re.match("<STREAM>\s+([0-9]+)", line)
            if ret is not None:
                currentStream = StreamInfo(currentState, int(ret.group(1)))
                currentState.addStreamInfo(currentStream)
                self.streamList.append(currentStream)
                
                currentMixture = None
                
            # mixture given?            
            ret = re.match("<MIXTURE>\s+([0-9]+)\s+(.+)", line)            
            if ret is not None:
                #print 'Found mixture with ' + ret.group(1) + ' ' + ret.group(2)
                currentMixture = MixtureInfo(currentStream, int(ret.group(1)))
                currentMixture.setWeight(float(ret.group(2)))
                currentStream.addMixtureInfo(currentMixture)
                                
                                
            # means given?
            ret = re.match("<MEAN>\s+([0-9]+)", line)
            if currentStream is not None and ret is not None:
                numMeans = int(ret.group(1))
                
                if currentMixture is None:
                    currentMixture = MixtureInfo(currentStream, 1)
                    currentMixture.setWeight(1.0)
                    currentStream.addMixtureInfo(currentMixture)
                            
                # not a multi space distribution with a mixture for unvoiced
                if numMeans > 0:   
                    line = mmfFile.readline()
                    means = map(float, line.split())
                    
                    pdf = currentMixture.pdf 
                    if pdf is None:
                        pdf = PDFInfo()
                        currentMixture.setPDF(pdf)
                       
                    pdf.setMeans(means)
                    
            # variances given?
            ret = re.match("<VARIANCE>\s+([0-9]+)", line)
            if currentStream is not None and ret is not None:
                numVars = int(ret.group(1))
                
                if currentMixture is None:
                    currentMixture = MixtureInfo(currentStream, 1)
                    currentMixture.setWeight(1.0)
                    currentStream.addMixtureInfo(currentMixture)
                            
                # not a multi space distribution with a mixture for unvoiced
                if numVars > 0:   
                    line = mmfFile.readline()
                    variances = map(float, line.split())
                    
                    pdf = currentMixture.pdf 
                    if pdf is None:
                        pdf = PDFInfo()
                        currentMixture.setPDF(pdf)
                       
                    pdf.setVariances(variances)                    
            
            
            # read next line and then finish loop
            line = mmfFile.readline()
                    
        # close the file and leave method                    
        mmfFile.close()
        



## example main program

#print 'Starting...'
#mmf1 = HTSMMF()
#mmf1.setVerbose( True )
#mmf1.loadMonoMMF( "../data/AT-mono.cmp.ascii.mmf")


#for s1 in mmf1.streamList:
    #print s1.owner.owner.name + ', state: ' + str( s1.owner.stateNumber ) + ', stream: ' +  str( s1.streamNumber )
    
#    for mix in s1.mixtures.itervalues():
        #if mix.pdf: 
            #print mix.pdf.means
            #print mix.pdf.variances

#    print '-'


#print 'Done.'




