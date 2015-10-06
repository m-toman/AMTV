'''
Created on 25.01.2013

@author: mtoman

Classes to read label files.

2013-03-06 JHO
                * unit testing
                * moved parsing from UtteranceLabel to Label
                * 

'''

import sys
import re

def quinphone(key):
    left = 0
    right = key.find('@')
    if right == -1:
        right = len(key)
    return key[left:right]

def centerphone(key):
    left = key.find('-') + 1
    right = key.find('+')
    if right == -1:
        right = len(key)
    return key[left:right]

def leftrightphone(key):
    leftphone = key[key.find('^') + 1:key.find('-')]
    rightleft = key.find('+') + 1
    rightright = key.find('=')
    if rightright == -1 : rightright = len(key)
    rightphone = key[rightleft: rightright]
    return (leftphone, rightphone)

def triphone(key):
    left = key.find('^') + 1
    right = key.find('=')
    if right == -1:
        right = len(key)
    return key[ left:right ]



class UtteranceLabel(object):
    
    '''Represents a single utterance, consisting of multiple labels.'''
    
    def __init__(self, file_or_name):
        ''' 
        Reads the utterance from a full or mono context label file.
        Access the internal label objects (of type Label) using .labels
        '''
        
        self.labels = []
        
        # read label file
        if isinstance(file_or_name, str):
            uttfile = open(file_or_name, 'rt')
        else:
            uttfile = file_or_name
            
        lines = uttfile.readlines()
        uttfile.close()
                
        for line in lines:
            fields = line.split()            
            if len(fields) < 3:
                print 'Error reading label: ' + line
                continue            
            lab = Label(line)
            self.labels.append(lab)            
    

class Label(object):
    
    ''' Represents a single label. '''

    #    __slots__ = 'phon start end context wordnum state quinphon'.split()
    def __init__(self, labline=None):
        '''
        Constructor
        '''
        self.phon = ""

        self.context = ""
        self.wordnum = -1
        self.state = -1
        self.quinphon = ""
        self.regionnum = None

        self._end = 0
        self._start = 0
        self._begintime = 0
        self._endtime = 0

        if labline:
            split = labline.split()
            if split[0].isdigit():  #  aligned label
                self.begintime = int(split.pop(0))
                self.endtime = int(split.pop(0))
            rest = split[0]  # ignore anything else            
            # * is it a ALIGNED, FULLCONTEXT, or MONOPHONE
            match = re.search(r'([^\s\[\]]+)(\[(\d+)\])?$|([a-zA-Z][\w\d]*)', rest)
            if not match:
                raise ValueError("Tried to create a Label from '%s' parse error" % labline)
            if match.group(1):
                self.context = match.group(1)
                self.phon = re.search('-(.+?)\+', self.context).group(1)
                self.quinphon = self.context[:self.context.find('@')]
                # get state
                if match.group(3):
                    self.state = int(match.group(3))                
                # get wordnum
                m = re.search('\/E\:[a-zA-Z]+\+[0-9]+@([0-9]+)', self.context)
                if m:
                    self.wordnum = int(m.group(1))
                # get region number
                m = re.search('\/REG\:([0-9]+)', self.context)
                if m:
                    self.regionnum = int(m.group(1))                
                


            else:
                self.phon = match.group(4)

    def get_end(self):
        return self._end
    def get_start(self):
        return self._start
    def get_btime(self):
        return self._begintime
    def get_etime(self):
        return self._endtime

    def set_end(self, value):
        self._end = value
        self._endtime = int(round(self._end * 1.0e7))
    def set_start(self, value):
        self._start = value
        self._begintime = int(round(self._start * 1.0e7))
    def set_etime(self, value):
        self._endtime = value
        self._end = float(value) * 1.0E-7
    def set_btime(self, value):
        self._begintime = value
        self._start = float(value) * 1.0E-7


    end = property(get_end, set_end)
    """ end time of label as a python-float in seconds """
    start = property(get_start, set_start)
    """ start time of label as a python-float in seconds """
    begintime = property(get_btime, set_btime)
    """ start time of label as an int in 100ns """
    endtime = property(get_etime, set_etime)
    """ end time of label as an int in 100ns """

    @staticmethod
    def Full2Mono(full):
        return full[ full.find('-') + 1 : full.find('+')]
         
         
if __name__ == '__main__':
    def TESTS():
        import sys
        cmpreader = sys.modules[__name__]

        import unittest2 as unittest
        import numpy
        import datetime
        import tempfile
        import StringIO

        def assertEqualAttrs(test, a, b, attrs):
            for attr in attrs:
                test.assertEqual(getattr(a, attr), getattr(b, attr),
                                 msg="testing attr %s" % attr)

        def tmpstr(string):
            tmp = tempfile.TemporaryFile()
            tmp.write(string)
            tmp.seek(0, 0)
            return tmp
        class MyTest(unittest.TestCase):

            def setUp(self):
                self.dtype = numpy.float32
#                 self.normal_lines = \
# """         0    1500000 x^x-sil+sil=v@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:5+4-1
#    1500000    3780000 x^sil-sil+v=Eh6@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_1/G:0_0/H:x=x@1=1|0/I:5=4/J:5+4-1
# """
#                 self.mono_lines = \
# """         0    1500000 sil
#    1500000    3840000 sil
#    3840000    4100000 GS
# """
                self.align_full_line = "         0    1500000 x^x-sil+sil=v@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:5+4-1"
                self.noalign_full_line = "x^x-sil+sil=v@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:5+4-1"
                self.align_hvite_line = "3550000 3950000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[3]"
                self.align_hvite_context = "sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1"


                unittest.TestCase.setUp(self)
            def test_phone_helpers(self):
                fullcontext = ('f^schwa-GS+a=n@1_3/A:0_0_2/B:1-1-3@1-3&9-3#5-1$2'
                              '-2!2-0;4-2|0/C:0+0+4/D:content_2/E:content+3@6+1'
                              '&5+0#1+0/F:0_0/G:0_0/H:11=6@1=1|L-L%/I:0=0/J:11+6-1')
                self.assertEqual(centerphone(fullcontext), 'GS')
                self.assertEqual(centerphone(centerphone(fullcontext)), 'GS')
                self.assertEqual(triphone(fullcontext), 'schwa-GS+a')
                self.assertEqual(triphone(triphone(fullcontext)), 'schwa-GS+a')
                self.assertEqual(centerphone(triphone(fullcontext)), 'GS')
                self.assertEqual(quinphone(quinphone(fullcontext)), 'f^schwa-GS+a=n')
                self.assertEqual(centerphone(quinphone(fullcontext)), 'GS')

                self.assertEqual(leftrightphone(fullcontext), ('schwa', 'a'))
                self.assertEqual(leftrightphone(quinphone(fullcontext)), ('schwa', 'a'))
                self.assertEqual(leftrightphone(triphone(quinphone(fullcontext))),
                                  ('schwa', 'a'))
                
                pass
                    

            def test_label_properties(self):
                label = Label()
                label.begintime = 0.1 * 1e7
                label.endtime = 1.0 * 1e7
                numpy.testing.assert_almost_equal(label.start, 0.1)
                numpy.testing.assert_almost_equal(label.end, 1.0)
                numpy.testing.assert_almost_equal(label.begintime, 0.1 * 1e7)
                numpy.testing.assert_almost_equal(label.endtime  , 1.0 * 1e7)

                label.start = 0.2 
                label.end = 3.0 
                numpy.testing.assert_almost_equal(label.start, 0.2)
                numpy.testing.assert_almost_equal(label.end, 3.0)
                numpy.testing.assert_almost_equal(label.begintime, 0.2 * 1e7)
                numpy.testing.assert_almost_equal(label.endtime  , 3.0 * 1e7)
                
            def test_label(self):
                lab1 = Label(labline=self.align_full_line)
                self.assertEqual(lab1.phon, 'sil')
                self.assertEqual(lab1.quinphon, 'x^x-sil+sil=v')
                self.assertEqual(lab1.context, self.noalign_full_line)
                numpy.testing.assert_almost_equal(lab1.start, 0.0)
                numpy.testing.assert_almost_equal(lab1.end, 0.150000000)

                lab2 = Label(labline=self.noalign_full_line)
                self.assertEqual(lab2.phon, 'sil')
                self.assertEqual(lab2.quinphon, 'x^x-sil+sil=v')
                self.assertEqual(lab2.context, self.noalign_full_line)
                self.assertEqual(lab2.state, -1)

                lab3 = Label(labline=self.align_hvite_line)
                self.assertEqual(lab3.phon, 'GS')
                self.assertEqual(lab3.quinphon, 'sil^sil-GS+ah=d')
                self.assertEqual(lab3.context, self.align_hvite_context)
                numpy.testing.assert_almost_equal(lab3.start, 0.355000000)
                numpy.testing.assert_almost_equal(lab3.end, 0.3950000)
                self.assertEqual(lab3.wordnum, 1)
                self.assertEqual(lab3.state, 3)


                self.assertEqual(Label.Full2Mono("sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1"),
                                  "GS")
                pass

            def test_reader(self):
                readerfile = StringIO.StringIO(
"""0 100000 x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1[2] x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1
100000 600000 x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1[3]
600000 1800000 x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1[4]
1800000 1850000 x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1[5]
1850000 1900000 x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1[6]
1900000 2350000 x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1[2] x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1
2350000 2400000 x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1[3]
2400000 3150000 x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1[4]
3150000 3200000 x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1[5]
3200000 3500000 x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1[6]
3500000 3550000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[2] sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1
3550000 3950000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[3]
3950000 4000000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[4]
4000000 4050000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[5]
4050000 4200000 sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1[6]
""")

                ul = UtteranceLabel(readerfile)
                allContexts = [
                "x^x-sil+sil=GS@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:0+0+0/D:0_0/E:x+x@x+x&x+x#x+x/F:0_0/G:0_0/H:x=x@1=1|0/I:0=0/J:9+5-1",
                "x^sil-sil+GS=ah@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=5/J:9+5-1",
                "sil^sil-GS+ah=d@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-5$1-4!0-2;0-2|0/C:0+0+4/D:0_0/E:content+2@1+5&1+4#0+1/F:content_2/G:0_0/H:9=5@1=1|L-L%/I:0=0/J:9+5-1"
                ]
                
                self.assertItemsEqual(allContexts,
                set([ lab.context for lab in ul.labels])
                )

                


        testresult = unittest.TextTestRunner().run(
          unittest.TestLoader().loadTestsFromTestCase(MyTest))
        # print testresult.errors
        # print testresult.failures
        # print testresult.failures[0][0]
        
                
        # unittest.main(exit=False) # this calls sys.exit()
        # print "Test done"
        # print datetime.datetime.time(datetime.datetime.now())
        pass


    if len(sys.argv) == 1 or ((
        len(sys.argv) == 2 and
        sys.argv[1] == '--test')):
        print "no commandline arguments given, executing unittests"
        TESTS()
        # print "Usage: python LabelReader.py <labelfile>"

    else:
        print len(sys.argv)
        if len(sys.argv) < 2:
            sys.exit("Usage: python LabelReader.py <labelfile>")

        ulab = UtteranceLabel(sys.argv[1])

        for lab in ulab.labels:
            print "Begin-Time: " + str(lab.begintime) + ", End-Time: " + str(lab.endtime) + ", Phon: " + lab.phon + ", Wordnum: " + str(lab.wordnum) + ", Context: " + lab.context

