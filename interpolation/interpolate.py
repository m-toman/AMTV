# encoding: utf-8
'''
interpolate -- interpolates a single utterance between two models

interpolates a single utterance between two models

@author:     mtoman

@contact:    toman@ftw.at
'''


import sys
import os
import numpy
import logging

# add path to pyblah
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

# import pyblah.model.labelold as label
from pyblah.model import label
from pyblah.model import mmf
from pyblah.model import model
from pyblah.util import dtw
from pyblah.util import kld

logger = logging.getLogger("interpolate")


#==============================================================================
# InterpolationPoint
#==============================================================================
class InterpolationPoint(object):

    """Between these points, interpolation will occur.

    A single interpolation point is a complete utterance.
    """

    def __init__(self, modelfolder, labelfile, expand=False):

        """Loads models, labels and sets up necessary data structures."""

        self.expanded = expand
        self.labels = []
        self.macros_to_phones = {}
        self.pdfs_to_phones = {}
        self.macro_ids_to_region = {}
        self.regions_to_pdf_ids = {}

        # load models and labels
        self.model = model.HTSVoiceModel()
        self.model.loadModel(modelfolder)
        logger.info("Loading label file " + labelfile)
        self.utterance = label.UtteranceLabel(labelfile)

        # classify the labels and get spectral macros
        self.mcep_macros = self.classify_labels(self.model.getMetaTree("mcep")
                                              , self.model.cmpMMF, store_regions=True)
        self.log_f0_macros = self.classify_labels(self.model.getMetaTree("logF0")
                                                , self.model.cmpMMF)
        self.bndap_macros = self.classify_labels(self.model.getMetaTree("bndap")
                                               , self.model.cmpMMF)

        # classify labels to get duration macros
        self.dur_macros = self.classify_labels(self.model.getMetaTree("dur")
                                             , self.model.durMMF)
        self.dur_pdfs = self.get_pdfs_for_dur_macros(self.model.durMMF
                                                   , self.dur_macros)

        # expand the states if necessary
        if expand:
            self._expand_states()

        # now get pdfs for the expanded or not expanded macros
        self.mcep_pdfs = self.get_pdfs_for_macros(self.model.cmpMMF
                                       , self.mcep_macros, store_regions=True)
        self.log_f0_mixtures = {}
        for i in range(2, 5):
            self.log_f0_mixtures[i] = self.get_mixtures_for_macros(
                              self.model.cmpMMF,
                              [(x + "-" + str(i)) for x in self.log_f0_macros])
        self.bndap_pdfs = self.get_pdfs_for_macros(self.model.cmpMMF
                                                 , self.bndap_macros)

    def _expand_states(self):

        ''' Expands all states with duration > 1 to duration states with duration 1 '''

        new_mcep = []
        new_log_f0 = []
        new_bndap = []
        new_dur_pdfs = []
        new_labels = []
        new_macro_ids_to_region = {}
        diff = 0
        totaldur = 0
        j = 0

        for i in range(0, len(self.mcep_macros)):
            mean = (self.dur_pdfs[i].means[0])
            rounded = int(mean + diff + 0.5)
            totaldur += rounded
            diff += mean - rounded

            # Duration of each expanded state is now 1.
            self.dur_pdfs[i].means[0] = 1.0

            # Insert the same model duration times.
            for _ in range(rounded):
                new_mcep.append(self.mcep_macros[i])
                new_log_f0.append(self.log_f0_macros[i])
                new_bndap.append(self.bndap_macros[i])
                new_dur_pdfs.append(self.dur_pdfs[i])
                new_labels.append(self.labels[i])
                new_macro_ids_to_region[j] = self.macro_ids_to_region[i]
                j += 1

        # Make the newly generated macro lists the lists to be used.
        self.mcep_macros = new_mcep
        self.log_f0_macros = new_log_f0
        self.bndap_macros = new_bndap
        self.dur_pdfs = new_dur_pdfs
        self.labels = new_labels
        self.macro_ids_to_region = new_macro_ids_to_region

    def classify_labels(self, mtree, mmf, store_regions=False):
        """Classify labels using a MetaTree.

        For every label in utterance, classify it
        using the MetaTree with the given tree.
        Returns resulting macros. 
        """
        ret = []
        for l in self.utterance.labels:
            # Classify each level using all trees.
            for tree in mtree.treeList:
                macro = tree.classifyLabelString(l.context)
                self.labels.append(l.phon)
                self.macros_to_phones[macro] = l.phon
                if store_regions:
                    self.macro_ids_to_region[len(ret)] = l.regionnum
                ret.append(macro)
                try:
                    self.pdfs_to_phones[
                       id(mmf.getMacro('~p', macro).mixture.pdfs[1])] = l.phon
                except:
                    pass
        return ret

    def get_mixtures_for_macros(self, mmf, macronames):
        """Returns the PDF objects for a number of macronames."""
        return [mmf.getMacro('~p', m).mixture for m in macronames]

    def get_pdfs_for_macros(self, mmf, macronames, store_regions=False):
        """Returns the PDF objects for a number of macronames."""
        ret = []
        i = 0

        for m in macronames:
            pdf = mmf.getMacro('~p', m).mixture.pdfs[1]
            if store_regions:
                region = self.macro_ids_to_region[i]
                if region not in self.regions_to_pdf_ids:
                    self.regions_to_pdf_ids[region] = []
                self.regions_to_pdf_ids[region].append(len(ret))
                i += 1
            ret.append(pdf)

        return ret

    def get_pdfs_for_dur_macros(self, mmf, macronames):
        """Returns the PDF objects for a number of macronames."""
        ret = []
        for m in macronames:
            for i in range(1, 6):
                # print "Trying macro " + m + " for stream " + str(i)
                ret.append(mmf.getMacro('~s', m)[i].mixture.pdfs[1])
        return ret


#=======================================================================
# Interpolator
#=======================================================================
class Interpolator(object):

    """ Interpolations between two utterances stored in two interpolation points. """

    def __init__(self):
        self.region_info = {}  # holds interpolation information for each region

    def _calc_dtw(self):
        """ Applies dynamic time warping on current object state.

        self.path consists then of tuples (i1,i2) where i1 and i2 are indices
        of the pdf lists (e.g. mcep_pdfs).
        """
        logger.info("Calculating DTW")
        warper = dtw.Dtw(self.ipoint1.mcep_pdfs,
                         self.ipoint2.mcep_pdfs,
                         _pdf_kld_distance)
        self.dtw_map = warper.calculate()
        self.distance_map = warper.distance_map
        self.path = warper.get_path()
        logger.info("Calculating DTW done")

    def _calc_regional_dtw(self, ipoint1_ordering):
        """ Applies dynamic time warping on current object state.

        ipoint1_ordering -- True: use the order of ipoint1 to build the final path
                            False: use the order of ipoint2 to build the final path
        self.path consists then of tuples (i1,i2) where i1 and i2 are indices 
        of the pdf lists (e.g. mcep_pdfs).
        """

        logger.info("Calculating regional DTW")
        regions1 = set(self.ipoint1.regions_to_pdf_ids.keys())
        regions2 = set(self.ipoint2.regions_to_pdf_ids.keys())

        if regions1 != regions2:
            logger.error("Region information of label 1"
                         " and label 2 differ, stopping execution!")
            return
        if None in regions1 or None in regions2:
            logger.error("Not all PDFs contain a region "
                        "info, stopping execution!")
            return

        self.path = []
        self.distance_map = {}
        self.dtw_map = {}

        # Calculate DTW for each region
        for region in regions1:
            # get all mcep pdfs and their indices for the current region
            pdfs1idx = self.ipoint1.regions_to_pdf_ids[region]
            pdfs1 = [ self.ipoint1.mcep_pdfs[i] for i in pdfs1idx ]
            pdfs2idx = self.ipoint2.regions_to_pdf_ids[region]
            pdfs2 = [ self.ipoint2.mcep_pdfs[i] for i in pdfs2idx ]

            # just linearly map 1:1
            # number of mappings depends on ipoint1_ordering
            if region in self.region_info and self.region_info[region] == "switch":

                if ipoint1_ordering:
                    regpath = [ (x, None) for x in pdfs1idx ]
                else:
                    regpath = [ (None, x) for x in pdfs2idx ]

            # if region should be interpolated, DTW
            else:
                warper = dtw.Dtw(pdfs1
                                , pdfs2
                                , _pdf_kld_distance)
                tmp_dtw_map = warper.calculate()

                # build dtw_map and distance_map for plots
                for key in tmp_dtw_map.keys():
                    self.dtw_map[ (pdfs1idx[key[0]], pdfs2idx[key[1]]) ] = tmp_dtw_map[ key ]
                for key in warper.distance_map:
                    self.distance_map[(pdfs1idx[key[0]], pdfs2idx[key[1]]) ] = warper.distance_map[ key ]

                # map the regpath to actual indices
                regpath = warper.get_path()
                regpath = map(lambda pe: (pdfs1idx[pe[0]], pdfs2idx[pe[1]]), regpath)

            self.path.extend(regpath)

        print self.path
        self.path = sorted(self.path, key=lambda x: x[0 if ipoint1_ordering else 1])
        print self.path
        logger.info("Calculating regional DTW done")

    def _build_pseudo_transition_matrix(self, numstates):
        """Builds a transition matrix with 1 for every state transition probability."""
        ret = numpy.zeros((numstates, numstates))
        for i in range(0, numstates - 1):
                ret[i][i + 1] = 1.0
        return ret

    def _build_cmp_mmf(self, numstates, transmat):
        newMMF = mmf.MMF()
        oMacro = newMMF.findOrDeclareMacro('~o', '')
        oMacro.setTarget(self.ipoint1.model.cmpMMF.getMacro('~o', '').target)
        cmpHMM = mmf.HMM(numstates=numstates)
        hMacro = newMMF.findOrDeclareMacro('~h', 'everything')
        hMacro.setTarget(cmpHMM)
        tMacro = newMMF.findOrDeclareMacro('~t', 'dummy')
        tMacro.setTarget(transmat)
        cmpHMM.transp = tMacro
        return (newMMF, cmpHMM)

    def _build_dur_mmf(self, numstates, transmat):
        newDurMMF = mmf.MMF()
        oMacro = newDurMMF.findOrDeclareMacro('~o', '')
        oMacro.setTarget(self.ipoint1.model.durMMF.getMacro('~o', '').target)
        oMacro.target.vecsize = numstates - 2
        oMacro.target.streaminfo = { 1: (numstates - 2) }
        # for i in range(1, numstates - 1): oMacro.target.streaminfo[i] = 1
        durHMM = mmf.HMM(numstates=3)
        hMacro = newDurMMF.findOrDeclareMacro('~h', 'everything')
        hMacro.setTarget(durHMM)
        tMacro = newDurMMF.findOrDeclareMacro('~t', 'dummy')
        tMacro.setTarget(transmat)
        durHMM.transp = tMacro
        return (newDurMMF, durHMM)

    def _linear_interp(self, a, b, alpha):
        return  (1.0 - alpha) * a + (alpha) * b

    def _quad_interp(self, a, b, alpha):
        return  ((1.0 - alpha) * (1.0 - alpha)) * a + (alpha * alpha) * b

    def _interpolate_pdf(self, pdf1, pdf2, alpha):
        # TODO: pluggable interpolator
        return mmf.PDF(means=self._linear_interp(pdf1.means, pdf2.means, alpha)
                      , variances=self._quad_interp(pdf1.variances, pdf2.variances, alpha)
                      , gconst=self._linear_interp(pdf1.gconst, pdf2.gconst, alpha))

    def _interpolate_mcep(self, pdf1, pdf2, alpha):
        return self._interpolate_pdf(pdf1, pdf2, alpha)

    def _interpolate_bndap(self, pdf1, pdf2, alpha):
        return self._interpolate_pdf(pdf1, pdf2, alpha)

    def _interpolate_logf0(self, mix1, mix2, alpha):
        newMix = mmf.Mixture()
        # voiced component
        newMix.pdfs[1] = self._interpolate_pdf(mix1.pdfs[1], mix2.pdfs[1], alpha)
        newMix.weights[1] = self._linear_interp(mix1.weights[1], mix2.weights[1], alpha)

        # unvoiced component
        newMix.pdfs[2] = self._interpolate_pdf(mix1.pdfs[2], mix2.pdfs[2], alpha)
        newMix.weights[2] = self._linear_interp(mix1.weights[2], mix2.weights[2], alpha)

        return newMix

    def _build_ext_info(self, path, idx1, idx2, partnerIpoint):
        """ Builds extended information dictionary for a dtw path 

        path: the dtw path indices
        idx1: the index in the tuple (from which path is made up) for which ext_info should be generated
        idx2: the index in the tuple which is the partner to idx1 
        partnerIpoint: the InterpolationPoint object for the partner
        """
        ext_info = {}
        for pe in path:
            if None in pe:
                continue 
            if pe[idx1] not in ext_info:
                ext_info[pe[idx1]] = { "pd": 0.0, "pn": 0.0 }

            # every time the idx1 occurs, add 1 to the partner count
            # and add the duration of the partner to the duration count
            ext_info[pe[idx1]]["pn"] += 1.0
            ext_info[pe[idx1]]["pd"] += partnerIpoint.dur_pdfs[pe[idx2]].means[0]
        return ext_info

    def set_region_info(self, region_info):
        self.region_info = region_info

    def _interpolate_cmp(self, ipoint1, ipoint2, pe1, pe2, alpha):
        if pe1 is None:
            ipol_mcep = ipoint2.mcep_pdfs[ pe2 ]
            ipol_bndap = ipoint2.bndap_pdfs[ pe2 ]
            ipol_log_f0 = dict((i, ipoint2.log_f0_mixtures[i][ pe2 ]) for i in range(2, 5))
        elif pe2 is None:
            ipol_mcep = ipoint1.mcep_pdfs[ pe1 ]
            ipol_bndap = ipoint1.bndap_pdfs[ pe1 ]
            ipol_log_f0 = dict((i, ipoint1.log_f0_mixtures[i][ pe1 ]) for i in range(2, 5))
        else:                        
            ipol_mcep = self._interpolate_mcep(ipoint1.mcep_pdfs[ pe1 ]
                                           , ipoint2.mcep_pdfs[ pe2 ]
                                           , alpha)
            ipol_bndap = self._interpolate_bndap(ipoint1.bndap_pdfs[ pe1 ]
                                             , ipoint2.bndap_pdfs[ pe2 ]
                                             , alpha)
            ipol_log_f0 = {}
            # Interpolate the 3 log F0 streams.
            for i in range(2, 5):
                # every stream has 2 mixtures which will be interpolated here:
                ipol_log_f0[i] = self._interpolate_logf0(ipoint1.log_f0_mixtures[i][ pe1 ]
                                                     , ipoint2.log_f0_mixtures[i][ pe2 ]
                                                     , alpha)

        return (ipol_mcep, ipol_bndap, ipol_log_f0)

    def _interpolate_dur(self, ipoint1, ipoint2, pe1, pe2, ext_info1, ext_info2, alpha):
        
        if pe1 is None:
            dm = ipoint2.dur_pdfs[pe2].means[0]
            dv = ipoint2.dur_pdfs[pe2].variances[0]
        elif pe2 is None:
            dm = ipoint1.dur_pdfs[pe1].means[0]
            dv = ipoint1.dur_pdfs[pe1].variances[0]            
        else:
            # old method:
            # -----------
            # dm = self._linear_interp(ipoint1.dur_pdfs[pe[0]].means[0]
            #                       , ipoint2.dur_pdfs[pe[1]].means[0]
            #                      , alpha)
            #
            # new method:
            # -----------
            # TD = B.PD * alpha + A.PD * (1-alpha)
            # if A.PN > 1:
            #    PED = TD * ( B.D / A.PD )
            # elif B.PN > 1:
            #    PED = TD * ( A.D / B.PD )
            # else:
            #    PED = TD
            td = self._linear_interp(ext_info2[pe2]["pd"], ext_info1[pe1]["pd"], alpha)
            if ext_info1[pe1]["pn"] > 1:
                dm = td * (ipoint2.dur_pdfs[pe2].means[0] / ext_info1[pe1]["pd"])
            elif ext_info2[pe2]["pn"] > 1:
                dm = td * (ipoint1.dur_pdfs[pe1].means[0] / ext_info2[pe2]["pd"])
            else:
                dm = td
    
            # Calculate duration variance.
            dv = self._quad_interp(ipoint1.dur_pdfs[pe1].variances[0]
                                 , ipoint2.dur_pdfs[pe2].variances[0]
                                 , alpha)
        return (dm, dv)

    def _build_streams(self, ipol_cmp):
        stream_dict = {  }
        (ipolMcep, ipolBndap, ipolLogF0) = ipol_cmp

        # build MCEP stream data
        stream = mmf.Stream(streamNumber=1)
        pdfs = { 1 : ipolMcep  }
        stream.mixture = mmf.Mixture(pdfs=pdfs, pseudo=True)
        stream_dict[ 1 ] = stream

        # build logF0 stream data
        stream = mmf.Stream(streamNumber=2)
        stream.mixture = ipolLogF0[2]
        stream_dict[ 2 ] = stream

        stream = mmf.Stream(streamNumber=3)
        stream.mixture = ipolLogF0[3]
        stream_dict[ 3 ] = stream

        stream = mmf.Stream(streamNumber=4)
        stream.mixture = ipolLogF0[4]
        stream_dict[ 4 ] = stream

        # build BNDAP stream data
        stream = mmf.Stream(streamNumber=5)
        pdfs = { 1 : ipolBndap }
        stream.mixture = mmf.Mixture(pdfs=pdfs, pseudo=True)
        stream_dict[ 5 ] = stream

        return stream_dict

    def interpolate(self, ipoint1, ipoint2, alpha, use_regions=False):
        """ interpolates between two utterances and returns a combined MMF """
        self.ipoint1 = ipoint1
        self.ipoint2 = ipoint2

        logging.info("Starting interpolation using alpha %f" % alpha)

        # dynamic timewarping first to find interpolation partners
        if (None not in self.ipoint1.regions_to_pdf_ids.keys() and
             None not in self.ipoint2.regions_to_pdf_ids.keys()):
            # TODO: constant for threshold
            self._calc_regional_dtw(True if alpha <= 0.5 else False)
        else:
            self._calc_dtw()

        dur_means = []
        dur_variances = []
        cmp_states = []
        ext_info1 = self._build_ext_info(self.path, 0, 1, ipoint2)
        ext_info2 = self._build_ext_info(self.path, 1, 0, ipoint1)

        # loop path, interpolate and write into mmf
        state_num = 2
        counter = 0.0

        for pe in self.path:
            ipol_cmp = self._interpolate_cmp(ipoint1, ipoint2, pe[0], pe[1], alpha)
            (dm, dv) = self._interpolate_dur(ipoint1, ipoint2, pe[0], pe[1]
                                          , ext_info1, ext_info2, alpha)
            stream_dict = self._build_streams(ipol_cmp)

            # Only add states if we don't have to drop them.
            counter += dm
            if counter > 1.0:
                if dm > 1.0:
                    # we add an unrounded state
                    counter -= dm
                else:
                    # durations < 1 will be rounded to 1
                    counter -= 1.0
                    dm = 1.0

                # finally add the state
                dur_means.append(dm)
                dur_variances.append(dv)
                cmp_states.append(mmf.State(state_num, stream_dict, None))
                state_num += 1

        # building MMF headers
        # build pseudo transition matrices
        pseudo_cmp_transition = self._build_pseudo_transition_matrix(state_num)
        pseudo_dur_transition = self._build_pseudo_transition_matrix(3)

        # TODO: ~v macro?
        # build cmp and dur MMF
        logger.info("Building CMP and DUR MMFs using " + str(state_num) + " states.")
        (newMMF, cmpHMM) = self._build_cmp_mmf(state_num, pseudo_cmp_transition)
        (newDurMMF, durHMM) = self._build_dur_mmf(state_num, pseudo_dur_transition)

        # build the cmp states
        for c in cmp_states:
            cmpHMM.state[ c.number ] = c

        # build the single duration state with 1 stream
        durPDFs = { 1 : mmf.PDF(means=numpy.array(dur_means), variances=numpy.array(dur_variances))  }
        stream = mmf.Stream(streamNumber=1)
        stream.mixture = mmf.Mixture(pdfs=durPDFs, pseudo=True)
        durStreamDict = { 1:stream }
        durHMM.state[ 2 ] = mmf.State(2, durStreamDict, None)

        return (newMMF, newDurMMF)


_cached_distances = {}
def _pdf_kld_distance(pdf1, pdf2):
    """ Calculates the distance between two pdfs. 
    """
    if (pdf1, pdf2) in _cached_distances:
        return _cached_distances[ (pdf1, pdf2) ]
    else:
        dst = kld.spectrumKLD(pdf1.means, pdf1.variances, pdf2.means, pdf2.variances)
        _cached_distances[ (pdf1, pdf2) ] = dst
        return dst


#===============================================================================
# main
#===============================================================================
def main():
    if len(sys.argv) < 6:
        sys.exit("Usage: python interpolate.py [-e] [-r regioninfo] <alpha> <model folder 1> <label file 1> <model folder 2> <label file 2> [<out cmp mmf> <out dur mmf> [<out map>]]")

    region_info_fn = None
    region_info = {}
    expand = False
    more = True

    # arguments
    while more:
        print "Checking command line param " + sys.argv[1].strip()
        if sys.argv[1].strip() == "-e":
            sys.argv = sys.argv[1:]
            expand = True
            print "Using expanded states"
        elif sys.argv[1].strip() == "-r":
            region_info_fn = sys.argv[2]
            print "Using region info from " + region_info_fn
            sys.argv = sys.argv[2:]
        else:
            more = False

    alpha = sys.argv[1]
    mf1 = sys.argv[2]
    lf1 = sys.argv[3]
    mf2 = sys.argv[4]
    lf2 = sys.argv[5]

    if(len(sys.argv) > 6): outcmp = sys.argv[6]
    else: outcmp = "clustered.cmp.mmf"
    if(len(sys.argv) > 7): outdur = sys.argv[7]
    else: outdur = "clustered.cmp.mmf"
    if(len(sys.argv) > 8): outmap = sys.argv[8]
    else: outmap = None

    # load stuff
    logging.basicConfig(level=logging.DEBUG
                        , format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                        , datefmt='%m-%d %H:%M:%S')
    try:
        ipoint1 = InterpolationPoint(mf1, lf1, expand)
        ipoint2 = InterpolationPoint(mf2, lf2, expand)
    except model.FileLoadException as fle:
        sys.exit("Could not load file " + fle.filename)

    if region_info_fn is not None:
        rif = open(region_info_fn, 'rt')
        for l in rif.readlines():
            [ reg, val ] = l.split()
            region_info[int(reg.strip())] = val.strip()
        rif.close()

    ipolator = Interpolator()
    ipolator.set_region_info(region_info)
    (newMMF, newDurMMF) = ipolator.interpolate(ipoint1, ipoint2, float(alpha))

    mmf.WriteMMF(open(outcmp, 'wt'), newMMF)
    mmf.WriteMMF(open(outdur, 'wt'), newDurMMF)

    # Visualize results
    try:
        from pyblah.vis import dtw_vis
        # testplot
        print ipoint1.labels
        print ipoint2.labels

        dtw_vis.plotDTW(ipolator.distance_map, ipolator.path, ipoint1.labels, ipoint2.labels)
        dtw_vis.plotDTW(ipolator.dtw_map, ipolator.path, ipoint1.labels, ipoint2.labels)
        dtw_vis.plotDTWHorizontal(ipolator.distance_map, ipolator.path, ipoint1.labels, ipoint2.labels)
    except ImportError:
        logging.info("Matplotlib not available, no plots rendered.")

    # print results
    x = []
    for pe in ipolator.path:
        if None not in pe:
            x.append((ipoint1.mcep_macros[ pe[0] ], ipoint2.mcep_macros[ pe[1] ]))

    if outmap is not None:
        outmapfile = open(outmap, 'wt')
        for m in x:
            outmapfile.write(m[0] + " " + m[1] + "\n")
        outmapfile.close()
    print x


if __name__ == '__main__':
    main()
