# written by Jakob Hollenstein, February 2013, some rights reserved.

import mmf
import numpy
import StringIO
import datetime
import itertools

import sys
if sys.version_info < (2, 6, 0):
    import unittest2 as unittest
else:
    import unittest



def SLexer( sval ):
    return mmf.Lexer(StringIO.StringIO(sval))


def assertEqualAttrs(test, a, b, attrs):
    for attr in attrs:
        test.assertEqual(getattr(a,attr),getattr(b,attr),
                         msg="testing attr %s" % attr)

def assertEqualStripedLines(test, a, b):    
    lines_a = [x.strip() for x in a.strip().split('\n')]
    lines_b = [x.strip() for x in b.strip().split('\n')]
    if len(lines_a) != len (lines_b):    
        test.fail("comparing strings regarding contained lines, but line count differs! %d vs %d" %
                  (len(lines_a),len(lines_b)))
    for x,y in itertools.izip(lines_a,lines_b):
        test.assertEqual(x,y)

class MyTest(unittest.TestCase):
    def setUp(self):
        self.dtype = numpy.float32
        unittest.TestCase.setUp(self)
        self.data_str = "data/m.mmf"

    def testMMF(self):
        """ this tests the reading of macros in general """
        lexer = SLexer(
        '~o\n'
        '<STREAMINFO> 5 123 180 1 1 1\n'
        '<MSDINFO> 5 0 0 1 1 1\n'
        '<VECSIZE> 306<NULLD><USER><DIAGC>\n'
        '~t "trP_1"\n'            
        '<TRANSP> 3\n'
        ' 1.000000e+00 2.000000e+00 3.000000e+00\n'
        ' 4.000000e+00 5.000000e+00 6.000000e+00\n'
        ' 7.000000e+00 8.000000e+00 9.000000e+00\n'
        '~v "varFloor3"\n'
        '<VARIANCE> 1\n'
        ' 5.329445e-05\n'
        '~s "dur_s2_25"\n'
        '<MEAN> 5\n'
        ' 2.380282e+00 6.014084e+00 3.225352e+00 5.549296e+00 3.478873e+00\n'
        '<VARIANCE> 5\n'
        ' 1.094989e+01 2.353197e+02 1.083246e+01 2.172435e+02 4.882293e+01\n'
        '<GCONST> 2.869543e+01\n'
        '~u "globalMean1"\n'
        '<MEAN> 4\n'
        ' 4.896214e-02 8.493645e-02 1.502419e-01 2.209209e-01\n'
        '~e "dep_34"\n'
        '<DEPCLASS> 3 4\n'
        ' 1.000000e+00  2.000000e+00  3.000000e+00  4.000000e+00 \n'
        ' 5.000000e+00  6.000000e+00  7.000000e+00  8.000000e+00 \n'
        ' 9.000000e+00 10.000000e+00 11.000000e+00 12.000000e+00\n'
        ' \n'
        '~p "cep_s6_65-1"\n'
        '<STREAM> 1\n'
        '~e "dep_34"\n'
        '<MEAN> 4\n'
        ' 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n'
        '<VARIANCE> 4\n'
        ' 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n'
        '<GCONST> -8.066434e+02\n'
        '~h "C"\n'
        '<BEGINHMM>\n'
        '<NUMSTATES> 3\n'
        '<STATE> 2\n'
        '~s "dur_s2_25"\n'
        '~t "trP_1"\n'
        '<ENDHMM>\n'
        )
        mfile = mmf.ParseMMF(lexer)
        gopt = mfile.getMacro("~o","")
        self.assertEqual(len(gopt.streaminfo),5)
        self.assertEqual(len(mfile.getMacros("~t")),1)

        self.assertEqual(len(mfile.getMacros("~v")),1)
        self.assertEqual(len(mfile.getMacros("~s")),1)
        self.assertEqual(len(mfile.getMacros("~u")),1)
        self.assertEqual(len(mfile.getMacros("~p")),1)
        self.assertEqual(len(mfile.getMacros("~h")),1)
        self.assertEqual( len(mfile.getMacro("~s","dur_s2_25")[1].pdfs[1].means), 5)
        hmm = mfile.getMacro("~h",'C')
        self.assertEqual( hmm.state[2].stream[1].pdfs[1].means[0], self.dtype("2.380282e+00"))
        

    def testDepTrans(self):
        lexer = SLexer(            
            '<DEPCLASS> 3 4\n'
            ' 1.000000e+00  2.000000e+00  3.000000e+00  4.000000e+00 \n'
            ' 5.000000e+00  6.000000e+00  7.000000e+00  8.000000e+00 \n'
            ' 9.000000e+00 10.000000e+00 11.000000e+00 12.000000e+00 \n'
            )
        deptrans = mmf.ParseDepTrans(lexer)
        numpy.testing.assert_array_almost_equal(deptrans,
                numpy.array([
                        [ 1, 2, 3, 4],
                        [ 5, 6, 7, 8],
                        [ 9,10,11,12]
                    ],dtype=self.dtype))
        

    def testGlobalOptions(self):
        lexer = SLexer(
            '~o\n'
            '<STREAMINFO> 5 123 180 1 1 1\n'
            '<MSDINFO> 5 0 0 1 1 1\n'
            '<VECSIZE> 306<NULLD><USER><DIAGC>\n'
            )
        gopt = mmf.GlobalOption()
        gopt.streaminfo = {1: 123, 2: 180, 3: 1, 4: 1, 5: 1}
        gopt.vecsize = 306
        gopt.msdinfo = {1: 0, 2: 0, 3: 1, 4: 1, 5: 1}
        gopt.covkind = 'DIAGC'
        gopt.durkind = 'NULLD'
        gopt.parmkind= 'USER'      
        
        context = mmf.MMF()
        pgopt = mmf.ParseGlobalOpts( lexer)
        assertEqualAttrs(self,gopt,pgopt, ['streaminfo','vecsize','msdinfo',
                                      'covkind','durkind','parmkind'])

        lexer = SLexer(
            '~o <VecSize> 4 <MFCC>\n'
            '<StreamInfo> 2 3 1\n'
            '~o <DISCRETE> <StreamInfo> 2 1 1\n'
            '~o\n'
            '<STREAMINFO> 1 5\n'
            '<VECSIZE> 5<GEND><USER><DIAGC>\n'
            '~t "trP_1"\n'            
            )
        pgopt = mmf.ParseGlobalOpts(lexer)
        self.assertEqual(pgopt.vecsize, 4)
        self.assertEqual(pgopt.parmkind, 'MFCC')
        self.assertEqual(pgopt.covkind, None)
        self.assertEqual(pgopt.streaminfo, {1:3, 2:1})

        pgopt = mmf.ParseGlobalOpts(lexer)
        self.assertEqual(pgopt.streaminfo, {1:1, 2:1})
        self.assertEqual(pgopt.parmkind, 'DISCRETE')

        pgopt = mmf.ParseGlobalOpts(lexer)
        self.assertEqual(pgopt.streaminfo, {1:5})
        self.assertEqual(pgopt.vecsize, 5)
        self.assertEqual(pgopt.durkind, 'GEND')
        self.assertEqual(pgopt.parmkind, 'USER')
        self.assertEqual(pgopt.covkind, 'DIAGC')

    def testTransp(self):
        lexer = SLexer(
            '<TRANSP> 3\n'
            ' 1.000000e+00 2.000000e+00 3.000000e+00\n'
            ' 4.000000e+00 5.000000e+00 6.000000e+00\n'
            ' 7.000000e+00 8.000000e+00 9.000000e+00\n'
            )
        transp = mmf.ParseTransp(lexer)
        numpy.testing.assert_array_almost_equal( transp,
            numpy.array( [[1,2,3],[4,5,6],[7,8,9]], dtype=self.dtype))
        self.assertEqual(transp.shape, (3,3))

    def testHMM(self):
        lexer = SLexer(
            '<BEGINHMM>\n'
            '<NUMSTATES> 3\n'
            '<STATE> 2\n'
            '~s "dur_s2_25"\n'
            '~t "trP_1"\n'
            '<ENDHMM>\n'
#
            
            )
        context = mmf.MMF()
        hmm = mmf.ParseHMM(lexer,context)
        self.assertEqual(hmm.numstates, 3)
        self.assertTrue(mmf.isMacro   ( hmm.state[2].stream))
        self.assertEqual(mmf.macroName( hmm.state[2].stream),"dur_s2_25")
        self.assertEqual(mmf.macroName( hmm.transp), "trP_1")
        self.assertEqual(lexer.get(), None)
        
    def testMultiStream(self):
        lexer = SLexer(
            '~s "dur_s2_100"\n'
            '<STREAM> 1\n'
            '<MEAN> 1\n'
            ' 2.015551e+00\n'
            '<VARIANCE> 1\n'
            ' 2.348032e+00\n'
            '<GCONST> 2.691455e+00\n'
            '<STREAM> 2\n'
            '<MEAN> 1\n'
            ' 2.936162e+00\n'
            '<VARIANCE> 1\n'
            ' 7.378427e+00\n'
            '<GCONST> 3.836437e+00\n'
            '<STREAM> 3\n'
            '<MEAN> 1\n'
            ' 2.488250e+00\n'
            '<VARIANCE> 1\n'
            ' 3.780098e+00\n'
            '<GCONST> 3.167627e+00\n'
            '<STREAM> 4\n'
            '<MEAN> 1\n'
            ' 1.925306e+00\n'
            '<VARIANCE> 1\n'
            ' 6.589187e-01\n'
            '<GCONST> 1.420722e+00\n'
            '<STREAM> 5\n'
            '<MEAN> 1\n'
            ' 1.399122e+00\n'
            '<VARIANCE> 1\n'
            ' 6.598312e-01\n'
            '<GCONST> 1.422106e+00\n')

        mfile = mmf.ParseMMF(lexer)
        smacro = mfile.getMacro('~s','dur_s2_100')
        self.assertEqual(len(smacro), 5)
        self.assertEqual(smacro[1].pdfs[1].means[0] ,self.dtype('2.015551e+00'))
        


    def testState(self):
        lexer = SLexer(
            '<STATE> 2\n'
            '<MEAN> 5\n'
            ' 1e+00 2e+00 3e+00 4e+00 5e+00 \n'
            '<VARIANCE> 5\n'
            ' 1e+00 2e+00 3e+00 4e+00 5e+00 \n'
            '<GCONST> 2e+00\n'
#
            '<STATE> 2\n'
            '~s "dur_s2_25"\n'
#            
            '<STATE> 2\n'
            '~w "SWeightall"\n'
            '<STREAM> 1\n'
            '~p "mcep_s2_213"\n'
            '<STREAM> 2\n'
            '~p "logF0_s2_41-2"\n'
            '<STREAM> 3\n'
            '~p "logF0_s2_41-3"\n'
            '<STREAM> 4\n'
            '~p "logF0_s2_41-4"\n'
            '<STREAM> 5\n'
            '~p "bndap_s2_123"\n'
#            
            '<STATE> 2\n'
            '<SWEIGHTS> 5\n'
            ' 1.000000e+00 1.000000e+00 1.000000e+00 1.000000e+00 0.000000e+00\n'
            '<STREAM> 1\n'
            '~p "mcep_s2_213"\n'
            '<STREAM> 2\n'
            '~p "logF0_s2_41-2"\n'
            '<STREAM> 3\n'
            '~p "logF0_s2_41-3"\n'
            '<STREAM> 4\n'
            '~p "logF0_s2_41-4"\n'
            '<STREAM> 5\n'
            '~p "bndap_s2_123"\n'
            )
        context = mmf.MMF()
        # gopts = mmf.GlobalOption()
        # gopts.streaminfo = {1:5, 2:1}
        # context.findOrDeclareMacro('~o','').setTarget(gopts) # register streaminfo

        #case one
        state = mmf.ParseState(lexer,context)
        self.assertTrue( state.stream[1].pseudo )
        numpy.testing.assert_array_almost_equal( state.stream[1].pdfs[1].means,
                     numpy.array('1e+00 2e+00 3e+00 4e+00 5e+00'.split(' '),
                                 dtype=self.dtype))
        numpy.testing.assert_array_almost_equal( state.stream[1].pdfs[1].variances,
                     numpy.array('1e+00 2e+00 3e+00 4e+00 5e+00'.split(' '),
                                 dtype=self.dtype))
        # case two
        state = mmf.ParseState(lexer,context)
        self.assertTrue( mmf.isMacro(state.stream) )
        self.assertEqual( mmf.macroName(state.stream), "dur_s2_25")

        #case three
        state = mmf.ParseState(lexer,context)
        for i in xrange(1,5):
            self.assertEqual( state.stream[i].streamNumber, i )
            self.assertFalse( state.stream[i].pseudo )
            self.assertTrue ( mmf.isMacro(state.stream[i].mixture) )
        self.assertEqual(mmf.macroName(state.weight), 'SWeightall')
        self.assertEqual(mmf.macroName(state.stream[1].mixture), "mcep_s2_213")
        self.assertEqual(mmf.macroName(state.stream[2].mixture), "logF0_s2_41-2")

        #case four
        state = mmf.ParseState(lexer,context)
#        print "stream keys: '%r'" % state.stream.keys()
        self.assertFalse(mmf.isMacro(state.weight))
        for i in xrange(1,5):
            self.assertNotEqual(state.stream[i], None)
            #self.assertEqual( state.stream[i].streamNumber, i )
            #self.assertFalse( state.stream[i].pseudo )
            #self.assertTrue ( mmf.isMacro(state.stream[i].mixture) )
        self.assertEqual(mmf.macroName(state.stream[1].mixture), "mcep_s2_213")
        self.assertEqual(mmf.macroName(state.stream[2].mixture), "logF0_s2_41-2")
        

    def testSWeights(self):
        lexer = SLexer(
                '<SWEIGHTS> 5\n'
                '1.000000e+00 1.000000e+00 1.000000e+00 1.000000e+00 0.000000e+00\n'
            )
        sweights = mmf.ParseSWeights(lexer)
        numpy.testing.assert_array_almost_equal(sweights,
                numpy.array([1,1,1,1,0],dtype=self.dtype))
        

    def testStream(self):
        
        lexer = mmf.Lexer(StringIO.StringIO(
        '<STREAM> 1\n'
        '~e "dep_20"\n'
        '~u "some_mean"\n'
        '~v "some_variance"\n'
        '<STREAM> 2\n'
        '~p "logF0_s2_41-2"\n'
        ))

        context = mmf.MMF()
        
        
        stream1 = mmf.ParseStream(lexer, context)
        stream2 = mmf.ParseStream(lexer, context)
        self.assertTrue( mmf.isMacro(stream1.deptrans))
        self.assertEqual(mmf.macroName(stream1.deptrans), "dep_20")
        self.assertTrue( mmf.macroName(stream1.pdfs[1].means), "some_mean")
        self.assertTrue( mmf.macroName(stream1.pdfs[1].variances), "some_variance")
        self.assertTrue( mmf.macroName(stream2.mixture), "logF0_s2_41-2")
        self.assertTrue( mmf.macroName(stream2.mixture), "logF0_s2_41-2")


    def testPseudoMixture(self):
        pdf = mmf.PDF(means=numpy.array(
                [5.227783e-02,9.354116e-02,1.573079e-01,2.662440e-01]),
                    variances=numpy.array(
                [3.093076e-04,5.616156e-04,1.446284e-03,2.297929e-03]),
                    gconst=self.dtype("-8.0664340e+02")
                    )
        lexer = mmf.Lexer(StringIO.StringIO(
            "<MEAN> 4\n"
            " 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n"
            "<VARIANCE> 4\n"
            " 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n"
            "<GCONST> -8.066434e+02\n"
            ))
        context = mmf.MMF()
        pmix = mmf.ParsePseudoMixture( lexer, context)
        numpy.testing.assert_array_almost_equal( pmix.pdfs[1].means, pdf.means )
        numpy.testing.assert_array_almost_equal( pmix.pdfs[1].variances, pdf.variances )
        numpy.testing.assert_array_almost_equal( pmix.pdfs[1].gconst, pdf.gconst )
        self.assertTrue(pmix.pseudo)
        
        
    def testMixture(self):
        mixture_f=StringIO.StringIO(
            "<NUMMIXES> 2 \n"
            "<MIXTURE> 1 9.999700e-01\n"
            "<MEAN> 1\n"
            " -5.783626e-03\n"
            "<VARIANCE> 1\n"
            " 2.020562e-04\n"
            "<GCONST> -6.669087e+00\n"
            "<MIXTURE> 2 4.429766e-01\n"
            "<MEAN> 0\n"
            "~v \"some_var\"\n"
            "<GCONST> 0.000000e+00\n"
            
            )
        mixture = mmf.Mixture(
            pdfs = {
                1: mmf.PDF(
                    means=numpy.array([" -5.783626e-03"],dtype=self.dtype),
                    variances=numpy.array(["2.020562e-04"],dtype=self.dtype),
                    gconst = self.dtype("-6.669087e+00")
                    ),
                2 : mmf.PDF(
                    means=numpy.array([],dtype=self.dtype),
                    gconst = self.dtype(0)
                    ),
                    
                    },
            weights= {
                1: self.dtype('9.999700e-01'),
                2: self.dtype('4.429766e-01'),
                }
            )
        
                    
        lexer = mmf.Lexer(mixture_f)
        context = mmf.MMF()
        result = mmf.ParseMixture(lexer,context)
        self.assertEqual(len(result.pdfs), 2)
        self.assertItemsEqual( result.weights, mixture.weights )
        
        numpy.testing.assert_array_almost_equal(result.pdfs[1].means,
                                                mixture.pdfs[1].means)
        numpy.testing.assert_array_almost_equal(result.pdfs[1].variances,
                                                mixture.pdfs[1].variances)
        numpy.testing.assert_array_almost_equal(\
            result.pdfs[2].means, numpy.array([],dtype=self.dtype))
        var = result.pdfs[2].variances
        self.assertTrue( mmf.isMacro(var) )
        self.assertEqual( mmf.macroName(var), "some_var")
        self.assertEqual( mmf.macroType(var), "~v")
        self.assertEqual(context.getMacro("~v","some_var"), var)
            
        

    def testPDF(self):
        pdf_str=(
            "<MEAN> 4\n"
            " 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n"
            "<VARIANCE> 4\n"
            " 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n"
            "<GCONST> -8.066434e+02\n"
            )
        pdf = mmf.PDF(means=numpy.array(
                [5.227783e-02,9.354116e-02,1.573079e-01,2.662440e-01]),
                    variances=numpy.array(
                [3.093076e-04,5.616156e-04,1.446284e-03,2.297929e-03]),
                    gconst=self.dtype("-8.0664340e+02")
                    )
            
        lexer = mmf.Lexer(StringIO.StringIO(pdf_str))
        context= mmf.MMF();
        result = mmf.ParsePDF(lexer,context)
        numpy.testing.assert_array_almost_equal( result.means, pdf.means )
        numpy.testing.assert_array_almost_equal( result.variances, pdf.variances )
        numpy.testing.assert_array_almost_equal( result.gconst, pdf.gconst )
        

        pdf2=(
            '~u "some_mean" \n'
            '~v "some_variance" \n')
        pdf3=(
            '~u "some_mean" \n'
            '<VARIANCE> 2\n'
            ' 3.0e+01 4.0e+01 \n')
        
        lexer = mmf.Lexer(StringIO.StringIO(pdf3))
        context= mmf.MMF();
        result = mmf.ParsePDF(lexer,context)
        
        self.assertTrue( mmf.isMacro(result.means) )
        self.assertEqual( mmf.macroName(result.means), "some_mean")
        self.assertEqual( mmf.macroType(result.means), "~u")
        numpy.testing.assert_almost_equal( result.variances, [3.0e+01, 4.0e+01])
        self.assertTrue( mmf.isDanglingMacro( context.getMacro("~u", "some_mean")))
        self.assertTrue( context.hasMacro('~u','some_mean'))
        self.assertFalse( context.hasMacro('~u', 'non-existant-macro'))

    def testGConst(self):
        gconst_str = " <GCONST> -8.066434e+02 \nhello"
        not_gconst = " <GCONST> :-) \n\n"
        not_gconst2= " some text."
        for val in [ (gconst_str, True), (not_gconst,False), (not_gconst2, False)]:
            lexer = mmf.Lexer( StringIO.StringIO( val[0] ))
            if not val[1]:
                self.assertRaises( RuntimeError, mmf.ParseGConst, lexer)
            else:                
                numpy.testing.assert_almost_equal( self.dtype("-8.066434e+02"), mmf.ParseGConst(lexer))
        pass
    def testVariance(self):
        variance = [
            ("<VARIANCE> 3 \n"
             " 5.080143e-02 6.878716e-02 1.023105e-01 \n"
             ),
            (" <VARIANCE> 2 \n"
             " 5.080143e-02 6.878716e-02 \n\n"
             ),
            " <VARIANCE> 0 \n"            
            ]
        variance_val =[
            numpy.array([5.080143e-02,6.878716e-02,1.023105e-01], dtype=self.dtype),
            numpy.array([5.080143e-02,6.878716e-02], dtype=self.dtype),
            numpy.array([],dtype=self.dtype)
            ]
        self.notvariance = [
            ("<VARIANCE> notvariance\n"),
            ("<VARIANCE> 1 \n"
             " 5.000000e+00  5.000000e+00 \n"),
            ("<VARIANCE> 2 \n"
             " 5.000000e+00  \n"),             
            ]

        for i in xrange(len(variance)):
            lexer = mmf.Lexer(StringIO.StringIO(variance[i]))
            numpy.testing.assert_array_almost_equal( mmf.ParseVariance( lexer ), variance_val[i])

        for i in xrange(len(self.notvariance)):
            lexer = mmf.Lexer(StringIO.StringIO(self.notvariance[i]))
            self.assertRaises(RuntimeError, mmf.ParseVariance, lexer )


    def testMean(self):
        mean = [
            ("<MEAN> 3 \n"
             " 5.080143e-02 6.878716e-02 1.023105e-01 \n"
             ),
            (" <MEAN> 2 \n"
             " 5.080143e-02 6.878716e-02 \n\n"
             ),
            (" <MEAN> 0 \n"
                ),
            ]
        mean_val =[
            numpy.array([5.080143e-02,6.878716e-02,1.023105e-01], dtype=self.dtype),
            numpy.array([5.080143e-02,6.878716e-02], dtype=self.dtype),
            numpy.array([], dtype=self.dtype),
            
            ]
        self.notmean = [
            ("<MEAN> notmean\n"),
            ("<MEAN> 1 \n"
             " 5.000000e+00  5.000000e+00 \n"),
            ("<MEAN> 2 \n"
             " 5.000000e+00  \n"),             
            ]

        for i in xrange(len(mean)):
            lexer = mmf.Lexer(StringIO.StringIO(mean[i]))
            numpy.testing.assert_array_almost_equal( mmf.ParseMean( lexer ), mean_val[i])

        for i in xrange(len(self.notmean)):
            lexer = mmf.Lexer(StringIO.StringIO(self.notmean[i]))
            self.assertRaises(RuntimeError, mmf.ParseMean, lexer )

        pass
                          

    def testLexer(self):
        file_like = StringIO.StringIO(
            "this is a 'test'. "
            "some\n"
            "more\n"
            "\"testing might be nice\"."
            )
        result=['this','is','a',"'test'",'.',
                'some','\n',
                'more','\n',
                '"testing might be nice"',
                '.',
                None]
          
        lexer = mmf.Lexer(file_like)
        while True:
            val = lexer.get()
            self.assertEqual(val, result.pop(0))
            if val == None:
                break
        pass

    def testLexerGetType(self):
        file_like = StringIO.StringIO(
            "1 two 3 4.5 5.6")
        lexer = mmf.Lexer(file_like)
        self.assertEqual(lexer.getType(int), 1)
        self.assertRaises(RuntimeError,lexer.getType,int)
        self.assertEqual(lexer.getType(float), 3)
        self.assertRaises(RuntimeError,lexer.getType,int)
        self.assertEqual(lexer.getType(float), 5.6)
        
        
    def testLexerSkip(self):
        file_like = StringIO.StringIO(
            "this is one line. \n\nnext line")
        lexer = mmf.Lexer(file_like)
        self.assertEqual(lexer.get(),'this')
        self.assertTrue(lexer.skipToNextLine())
        self.assertEqual(lexer.get(),'next')
    def testLexerGetN(self):
        file_like = StringIO.StringIO("one two three four\n")
        lexer = mmf.Lexer(file_like)
        self.assertEqual(lexer.getN(3),["one","two","three"])
        self.assertEqual(lexer.peek(), "four")
        self.assertEqual(lexer.getN(1),["four"])
        self.assertEqual(lexer.get(),"\n")
        
    def testMethod(self):
#        mmf_inst = mmf.MMF( self.data_str )       
#        self.assertEqual(1 + 2, 3, "1 + 2 not equal to 3")
        pass
    def testUseMacro(self):
        lexer = SLexer(
            '~h "about"\n'
            '~h "sil^sil-t+s=uh@1_3/A:0_0_0/B:0-0-3@1-2&1-8#1-6$1-5!0-1;0-1|uh/C:1+1+2/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:8=5@1=1|L-L%/I:0=0/J:8+5-1"\n'
            )
        context = mmf.MMF()

        self.assertEqual( mmf.macroName(mmf.ParseUseMacro(lexer,context)),
                          "about")
        self.assertEqual( mmf.macroName(mmf.ParseUseMacro(lexer,context)),
                ("sil^sil-t+s=uh@1_3/A:0_0_0/B:0-0-3@1-2&1-8#1-6$1-5!0-1;0-1|"
                 "uh/C:1+1+2/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/"
                 "G:0_0/H:8=5@1=1|L-L%/I:0=0/J:8+5-1"))
    def test_write_mmf(self):
        lexer = SLexer(
        '~o\n'
        '<STREAMINFO> 5 123 180 1 1 1\n'
        '<MSDINFO> 5 0 0 1 1 1\n'
        '<VECSIZE> 306<NULLD><USER><DIAGC>\n'
        '~t "trP_1"\n'            
        '<TRANSP> 3\n'
        ' 1.000000e+00 2.000000e+00 3.000000e+00\n'
        ' 4.000000e+00 5.000000e+00 6.000000e+00\n'
        ' 7.000000e+00 8.000000e+00 9.000000e+00\n'
        '~v "varFloor3"\n'
        '<VARIANCE> 1\n'
        ' 5.329445e-05\n'
        '~s "dur_s2_25"\n'
        '<MEAN> 5\n'
        ' 2.380282e+00 6.014084e+00 3.225352e+00 5.549296e+00 3.478873e+00\n'
        '<VARIANCE> 5\n'
        ' 1.094989e+01 2.353197e+02 1.083246e+01 2.172435e+02 4.882293e+01\n'
        '<GCONST> 2.869543e+01\n'
        '~u "globalMean1"\n'
        '<MEAN> 4\n'
        ' 4.896214e-02 8.493645e-02 1.502419e-01 2.209209e-01\n'
        '~e "dep_34"\n'
        '<DEPCLASS> 3 4\n'
        ' 1.000000e+00  2.000000e+00  3.000000e+00  4.000000e+00 \n'
        ' 5.000000e+00  6.000000e+00  7.000000e+00  8.000000e+00 \n'
        ' 9.000000e+00 10.000000e+00 11.000000e+00 12.000000e+00\n'
        ' \n'
        '~p "cep_s6_65-1"\n'
        '<STREAM> 1\n'
        '~e "dep_34"\n'
        '<MEAN> 4\n'
        ' 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n'
        '<VARIANCE> 4\n'
        ' 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n'
        '<GCONST> -8.066434e+02\n'
        '~h "C"\n'
        '<BEGINHMM>\n'
        '<NUMSTATES> 3\n'
        '<STATE> 2\n'
        '~s "dur_s2_25"\n'
        '~t "trP_1"\n'
        '<ENDHMM>\n'
        )
        mymmf = mmf.ParseMMF(lexer)
        fout = StringIO.StringIO()
        mmf.WriteMMF(fout,mymmf)
        #print fout.getvalue()
        fout.seek(0)
        newlex = mmf.Lexer(fout)
        newmmf= mmf.ParseMMF(newlex)
        self.assertItemsEqual(newmmf.macros, mymmf.macros)

    def test_write_hmm(self):
        lexer1 = mmf.Lexer(StringIO.StringIO(
            '<BEGINHMM>\n'
            '<NUMSTATES> 3\n'
            '<STATE> 2\n'
            '~s "dur_s2_25"\n'
            '~t "trP_1"\n'
            '<ENDHMM>\n\n\n<FOO>'))
        contextY = mmf.MMF()
        hmm = mmf.ParseHMM(lexer1,contextY)
        fout = StringIO.StringIO()
        mmf.WriteHMM(fout, hmm)
        fout.seek(0)
        context2 = mmf.MMF()
        hmm2 = mmf.ParseHMM(mmf.Lexer(fout), context2)
        self.assertEqual(repr(hmm),repr(hmm2))
        self.assertEqual(hmm,hmm2)
        
        pass
    def test_write_global_opts(self):
        gopt = mmf.GlobalOption()
        gopt.streaminfo = {1: 123, 2: 180, 3: 1, 4: 1, 5: 1}
        gopt.vecsize = 306
        gopt.msdinfo = {1: 0, 2: 0, 3: 1, 4: 1, 5: 1}
        gopt.covkind = 'DIAGC'
        gopt.durkind = 'NULLD'
        gopt.parmkind= 'USER'
        fout = StringIO.StringIO()
        mmf.WriteGlobalOpts(fout,gopt)
        fout.seek(0)
        context = mmf.MMF()
        gopt2 = mmf.ParseGlobalOpts(mmf.Lexer( fout))
        print gopt == gopt2
        self.assertEqual(gopt, gopt2)


    def test_write_state(self):
        val = StringIO.StringIO(
            '<STATE> 2\n'
            '<MEAN> 5\n'
            ' 1e+00 2e+00 3e+00 4e+00 5e+00 \n'
            '<VARIANCE> 5\n'
            ' 1e+00 2e+00 3e+00 4e+00 5e+00 \n'
            '<GCONST> 2e+00\n'
            '<STATE> 2\n'
            '~s "dur_s2_25"\n'
            '<STATE> 2\n'
            '~w "SWeightall"\n'
            '<STREAM> 1\n'
            '~p "mcep_s2_213"\n'
            '<STREAM> 2\n'
            '~p "logF0_s2_41-2"\n'
            '<STREAM> 3\n'
            '~p "logF0_s2_41-3"\n'
            '<STREAM> 4\n'
            '~p "logF0_s2_41-4"\n'
            '<STREAM> 5\n'
            '~p "bndap_s2_123"\n')
        lexer = mmf.Lexer(val)
        context = mmf.MMF()
        numcases =3
        states = [ mmf.ParseState(lexer,context) for i in range(numcases)]
        self.assertEqual(numcases, len(states))
        fout = StringIO.StringIO()
        for s in states:
            mmf.WriteState(fout, s)
        fout.seek(0)

        newlex = mmf.Lexer(fout)        
        newstates = [ mmf.ParseState(newlex,context) for i in range(numcases)]
        for i in range(numcases):
            self.assertEqual( newstates[i], states[i])

        pass
    def test_write_stream(self):
        lexer = mmf.Lexer(StringIO.StringIO(
        '<STREAM> 1\n'
        '~e "dep_20"\n'
        '~u "some_mean"\n'
        '~v "some_variance"\n'
        '<STREAM> 1\n'
        '<DEPCLASS> 3 4\n'
        ' 1.000000e+00  2.000000e+00  3.000000e+00  4.000000e+00 \n'
        ' 5.000000e+00  6.000000e+00  7.000000e+00  8.000000e+00 \n'
        ' 9.000000e+00 10.000000e+00 11.000000e+00 12.000000e+00\n'          
        '~u "some_mean"\n'
        '~v "some_variance"\n'
        '<STREAM> 2\n'
        '~p "logF0_s2_41-2"\n'
        ' \n'
        '<MEAN> 4\n'
        ' 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n'
        '<VARIANCE> 4\n'
        ' 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n'
        ))

        num_cases = 4

        context = mmf.MMF()
        streams = [ mmf.ParseStream(lexer,context) for i in xrange(num_cases )]
        fout = StringIO.StringIO()
        for s in streams:
            mmf.WriteStream( fout, s)
        fout.seek(0)
        newlex = mmf.Lexer(fout)
        nstreams = [mmf.ParseStream(newlex, context) for i in xrange(num_cases)]
        self.assertEqual(len(streams),num_cases)
        self.assertEqual(len(nstreams),num_cases)
        for x,y in itertools.izip(streams,nstreams):            
            self.assertEqual(x,y)
        
                         
        pass
    def test_write_mixture(self):
        # 
        fin = StringIO.StringIO( 
            "<NUMMIXES> 2 \n"
            "<MIXTURE> 1 9.999700e-01\n"
            "<MEAN> 1\n"
            " -5.783626e-03\n"
            "<VARIANCE> 1\n"
            " 2.020562e-04\n"
            "<GCONST> -6.669087e+00\n"
            "<MIXTURE> 2 4.429766e-01\n"
            "<MEAN> 0\n"
            "~v \"some_var\"\n"
            "<GCONST> 0.000000e+00\n"
            "<MEAN> 4\n"
            " 5.227783e-02 9.354116e-02 1.573079e-01 2.662440e-01 \n"
            "<VARIANCE> 4\n"
            " 3.093076e-04 5.616156e-04 1.446284e-03 2.297929e-03 \n"
            "<GCONST> -8.066434e+02\n")
        lexer = mmf.Lexer(fin)
        context= mmf.MMF()
        mixture0 = mmf.ParseMixture( lexer, context)
        pmixture0 = mmf.ParsePseudoMixture(lexer, context)
        fout = StringIO.StringIO()
        mmf.WriteMixture(fout, mixture0 )
        mmf.WriteMixture(fout, pmixture0 )
        fout.seek(0)
        lexer = mmf.Lexer(fout)
        mixture1 = mmf.ParseMixture(lexer, context)
        pmixture1 = mmf.ParsePseudoMixture(lexer, context)
        
        self.assertEqual( mixture0, mixture1)
        self.assertEqual( pmixture0, pmixture1)
        pass
    def test_write_pdf(self):        
        pdf0 = mmf.PDF( means=numpy.array("5.227783e-02 9.354116e-02"
                                          " 1.573079e-01 2.662440e-01".split()
                                          ,dtype=self.dtype),
                        
                        variances=numpy.array("3.093076e-04 5.616156e-04 "
                                              "1.446284e-03 2.297929e-03".split(),
                                              dtype=self.dtype),
                        gconst=self.dtype("-8.0664340e+02"))
        fo = StringIO.StringIO()
        mmf.WritePDF( fo, pdf0 )
        fo.seek(0)
        context = mmf.MMF()
        self.assertEqual( pdf0, mmf.ParsePDF(mmf.Lexer(fo),context))
        
        pdf0.gconst=None ## try again with gconst = None
        pdf0.means=numpy.array([],dtype=self.dtype)
        pdf0.variances = mmf.Macro("~v","foonic")
        fo = StringIO.StringIO()
        mmf.WritePDF( fo, pdf0 )
        fo.seek(0)
        context = mmf.MMF()
        self.assertEqual( pdf0, mmf.ParsePDF(mmf.Lexer(fo),context))
        pass

    def test_write_gconst(self):
        fo = StringIO.StringIO()
        value = self.dtype("-2.070931e+03")
        mmf.WriteGConst( fo, value )
        fo.seek(0)
        self.assertEqual(value, mmf.ParseGConst(mmf.Lexer(fo)))

    def test_write_vector_mean_var_sweight(self):
        vec0 = numpy.array([],dtype=self.dtype)
        vec3 = numpy.array([5.080143e-02,6.878716e-02,1.023105e-01],dtype=self.dtype)
        vec1 = numpy.array([0.0],dtype=self.dtype)
        pairs = [
            ( vec0, ("%s 0\n") ),
            ( vec3, ("%s 3\n"
         " 5.080143e-02 6.878716e-02 1.023105e-01 \n")),
            ( vec1, ("%s 1\n"
                      " 0.000000e+00 \n")),
            ]
        for funparse, tag in [
            (mmf.ParseMean,      "<MEAN>"),
            (mmf.ParseVariance, "<VARIANCE>"),
            (mmf.ParseSWeights, "<SWEIGHTS>"),     ]:
            for val,t in pairs:
                f = StringIO.StringIO()
                mmf.WriteVector( f, tag, val)
                assertEqualStripedLines(self, f.getvalue(), t % tag)
                f.seek(0)
                numpy.testing.assert_array_almost_equal( val, funparse(mmf.Lexer(f)))
        pass
    
    def test_write_transp_and_deptrans(self):
        values = numpy.array( [[1,2,3],[4,5,6],[7,8,9]], dtype=self.dtype)
        for funparse, tag, two_dims in [ (mmf.ParseTransp, "<TRANSP>", False),
                                         (mmf.ParseDepTrans, "<DEPCLASS>",True),
                               ]:
            f = StringIO.StringIO()
            mmf.WriteMatrix( f, tag, values, two_dims)
            f.seek(0)
            numpy.testing.assert_array_almost_equal( values, funparse(mmf.Lexer(f)))
        #self.fail()
        pass
    
    def testMacro(self):
        testlist = ['a','b']
        macro = mmf.Macro('x','hallo')
        macro.setTarget(testlist)
        self.assertEqual(macro[0],'a')
        self.assertEqual(macro[1],'b')
        self.assertTrue(mmf.isMacro(macro))
        self.assertFalse(mmf.isMacro(testlist))
    def testEqualities(self):
        pdf1 = mmf.PDF(means=[1,2,3], variances=[4,5,6], gconst=0)
        pdf2 = mmf.PDF(means=[1,2,3], variances=[4,5,6], gconst=0)
        pdf3 = mmf.PDF(means=[1,2,4], variances=[4,5,6], gconst=0)
        self.assertEqual(pdf1, pdf2)
        self.assertNotEqual(pdf1, pdf3)
        

if __name__ == '__main__':
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(MyTest))
    #unittest.main(exit=False) # this calls sys.exit()
    print "Test done"
    print datetime.datetime.time(datetime.datetime.now())
