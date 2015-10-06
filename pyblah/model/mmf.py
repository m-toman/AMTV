# written by Jakob Hollenstein, February 2013, some rights reserved.

#from profilehooks import profile

import re
import logging
import numpy
import collections

##------------------------------------------------------------------
####### Created by tomer filiba on Fri, 26 May 2006 (PSF-License) 
## {{{ http://code.activestate.com/recipes/496741/ (r1)
class Proxy(object):
    __slots__ = ["_obj", "__weakref__"]
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)
    
    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name)
    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_obj"), name)
    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_obj"), name, value)
    
    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_obj"))
    def __str__(self):
        return str(object.__getattribute__(self, "_obj"))
    def __repr__(self):
        return repr(object.__getattribute__(self, "_obj"))
    
    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__', 
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', 
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', 
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__', 
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__', 
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', 
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__', 
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', 
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', 
        '__truediv__', '__xor__', 'next',
    ]
    
    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""
        
        def make_method(name):
            def method(self, *args, **kw):
                return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
            return method
        
        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
        return type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
    
    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an 
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins
## end of http://code.activestate.com/recipes/496741/ }}}
##----------------------------------------------------------------------------------------


#Import Psyco if available
# try:
#     import psyco
#     psyco.full()
# except ImportError:
#     print "psyco not available"
#     pass


class GlobalOption(object):
    __slots__ =  'streaminfo vecsize msdinfo covkind durkind parmkind'.split()
    def __init__(self,streaminfo=None, vecsize=None, msdinfo=None, covkind=None, durkind=None, parmkind=None):
        self.streaminfo = streaminfo
        self.vecsize = vecsize
        self.msdinfo = msdinfo
        self.covkind = covkind
        self.durkind = durkind
        self.parmkind= parmkind

    def __eq__(self, other):
        if id(self) != id(other):
            # below is a magical backslash, do not remove it 
            # because "return " is a short way for writing "return None"...
            return \
            (self.streaminfo == other.streaminfo) and \
            (self.vecsize    == other.vecsize) and \
            (self.msdinfo == other.msdinfo) and \
            (self.covkind == other.covkind) and \
            (self.durkind == other.durkind) and \
            (self.parmkind == other.parmkind)
        else:
            return True
    def __repr__(self):
        return "%s(streaminfo=%r, vecsize=%r, msdinfo=%r, covkind=%r, durkind=%r, parmkind=%r)" % \
               (self.__class__.__name__,
                self.streaminfo,
                self.vecsize,
                self.msdinfo,
                self.covkind,
                self.durkind,
                self.parmkind)
        

GlobalOption.covkinds = set("DIAGC INVDIAGC FULLC LLTC XFORMC".split(" "))
GlobalOption.durkinds = set("NULLD POISSOND GAMMAD GEND".split(" "))
GlobalOption.parmkinds= set("DISCRETE LPC LPCEPSTRA MFCC FBANK MELSPEC LPREFC LPDELCEP USER".split(" "))

#-------------------------------------------
# Macro
#-------------------------------------------
def isMacro(value):
    return getattr(value, 'macroType', None) and getattr(value, 'macroId', None)
def macroName(value):
    return getattr(value, 'macroId', None)
def macroType(value):
    return getattr(value, 'macroType', None)
def isDanglingMacro(value):
    return not bool( getattr(value, 'target', False))


### this is more difficult to transform into a new style class, as
### proxying of special methods bypasses __getattr__ probably need to
### use the proxy class included above
class Macro:
#    __slots__ = 'macroType macroId target'.split()
    def __init__(self, macroType, macroId, target=None):
        self.macroType= macroType
        self.macroId = macroId
        self.target = target

    def setTarget(self, target):
        self.target=target
        # def __getattribute__(self,name):
        #     #        print "was asked for %s" % name
        #     if object.__getattribute__(self,'__dict__').has_key(
        #     if object.__getattribute__(self,'__dict__').has_key(name):
        #         x =object.__getattribute__(self,name)
        #         return x
        #     elif self.target:
        #         print "key %s not a self" % name
        #         return getattr(self.target,name)
    def __eq__(self, other):
        x=self.target
        if isMacro(other):
            y=other.target
        else:
            y=other
        if isinstance(x,numpy.ndarray):
            return (x==y).all()
        else:
            return x==y
            
    def __repr__(self):
        return "%s(%s,%s, target=%r)" % (self.__class__.__name__,
                                         self.macroType,
                                         self.macroId,
                                         self.target)
    def __getattr__(self, name):
        return getattr(self.target,name)

    def __dir__(self):
        macro_items = ['__init__','__doc__','__module__','macroType','macroId','target','setTarget','__getattr__','__dir__']
        if self.target:
            macro_items.extend( dir(self.target))
        return macro_items
        

#-------------------------------------------
# PDF
#-------------------------------------------

class PDF(object):
    __slots__ = 'means variances gconst'.split()
    def __init__(self, means=None, variances=None, gconst=None):
        self.means=means
        self.variances=variances
        self.gconst=gconst
    def __eq__(self,other):
        return ( numpy.array_equal(self.means,     other.means) and
                 numpy.array_equal(self.variances, other.variances) and
                 self.gconst == other.gconst )
    def __repr__(self):
        return "%s(means=%r, variances=%r, gconst=%r)" % \
               (self.__class__.__name__, self.means,self.variances,self.gconst)

#-------------------------------------------
# Mixture
#-------------------------------------------

class Mixture(object):
    __slots__ = 'pdfs weights pseudo'.split()
    """ a mixture contains PDFS and Weights.  it can be a *pseudo*
    mixture meaning that there is not really a mixture definition
    attached. The use of the pseudo mixture flag is to enable uniform
    access to the MMFs ressources. If no <NUMMIXES> field is present a
    pseudo mixture is assumed."""
    def __init__(self, pdfs=None, weights=None, pseudo=False):
        self.pdfs={} if pdfs==None else pdfs
        self.weights=weights if weights!=None else {}
        self.pseudo=pseudo
    def __eq__(self, other):
        return (
            self.pdfs   == other.pdfs    and
            self.weights== other.weights and
            self.pseudo == other.pseudo )
    def __repr__(self):
        return "%s(pdfs=%r, weights=%r, pseudo=%r)" % \
               (self.__class__.__name__,
                self.pdfs,
                self.weights,
                self.pseudo)
#-------------------------------------------
# Stream
#-------------------------------------------
class Stream(object):
    __slots__ = 'streamNumber mixture deptrans pseudo'.split()
    def __init__(self, streamNumber=None, mixture=None, deptrans=None, pseudo=False):
        self.streamNumber = streamNumber
        self.mixture = mixture
        self.deptrans = deptrans
        self.pseudo = pseudo
        
    def __getattr__(self, name):
        return getattr(self.mixture,name)
    def __eq__(self, other):
        return(
            self.streamNumber   == other.streamNumber    and
            self.mixture== other.mixture and
            numpy.array_equal(self.deptrans, other.deptrans) and
            self.pseudo == other.pseudo
            )
    def __repr__(self):
        return "%s(streamNumber=%r, mixture=%r, deptrans=%r, pseudo=%r)" % \
               (self.__class__.__name__,
                self.streamNumber,
                self.mixture,
                self.deptrans,
                self.pseudo)
    
        
#-------------------------------------------
# State
#-------------------------------------------
class State(object):
    __slots__ = 'number stream weight'.split()
    def __init__(self,number=None, stream=None, weight=None):
        buffer=dict()
        self.number = number if number!=None else {}
        self.stream = stream if stream!=None else {}
        self.weight = weight if weight!=None else {}
        
    def __eq__(self,other):
        return (
            self.number == other.number and
            self.stream == other.stream and
            self.weight == other.weight
            )
               
    def __repr__(self):
        return "%s(number=%r, stream=%r, weight=%r)" % \
               (self.__class__.__name__,
                self.number,
                self.stream,
                self.weight)
        
#-------------------------------------------
# HMM
#-------------------------------------------
class HMM(object):
    __slots__ = 'numstates state transp'.split()
    def __init__(self, numstates=None, state=None, transp=None):
        self.numstates = numstates
        self.state = state if state!=None else {}
        self.transp = transp
    def __eq__(self,other):
        return (
            self.numstates == other.numstates and
            self.state     == other.state and
            self.transp    == other.transp
            )
    def __repr__(self):
        return "%s(numstates=%r,state=%r,transp=%r)" % \
               ( self.__class__.__name__,
                 self.numstates,
                 self.state,
                 self.transp)

               
#-------------------------------------------
# HTSMMF
#-------------------------------------------
mmf_rex_macro = re.compile(r'\s+~(\w)\s+\"([A-Za-z_\-0-9]+)\"')
class MMF:
    def __init__(self, filename=None):
        self.macros = collections.defaultdict(dict)
        if filename:
            
            self.file = open( filename, 'rt')
            ParseMMF( Lexer( self.file ), self )
            self.file.close()

    def getMacros(self, mtype):
        if not self.macros.has_key(mtype):
            return None
        return self.macros[mtype]
    def hasMacro(self, mtype, mname):
        if not self.macros.has_key(mtype):
            return False
        return self.macros[mtype].has_key(mname)

        
    def getMacro(self, mtype, mname):
        if not self.macros.has_key(mtype):
            return None
        tmacros = self.macros[mtype]
        # if not tmacros.has_key(mname):
        #     return None
        return tmacros[mname]
    def findOrDeclareMacro(self, macro_type, macro_name):
        mtype = macro_type.strip()
        mname = macro_name.strip(' "\'')
        tmacros= self.macros[mtype]
        if not tmacros.has_key(mname):
            tmacros[mname] = Macro(mtype, mname)

        return tmacros[mname]
    def __repr__(self):
        return str([ (k,v.keys()) for k,v in self.macros.iteritems()])
    pass
#-------------------------------------------
# PARSE TOOLS - Lexer
#-------------------------------------------

class Lexer(object):
    __slots__ = "file stack _elements_ _ret_elements_ _line_no_".split()
    def __init__(self, filelike):
        self.file = filelike;
        self.stack = [self.file.tell()]
        self._elements_=[]
        self._ret_elements_=[]
        self._line_no_ = 0
        self._fill_buf_()
        
    # def tell(self):
    #     return (self.file.tell(),self.elements)
    # def seek(self,tuple):
    #     self.elements=tuple[1]
    #     return self.file.seek(tuple[0])

    #### GOALS
    
#    @profile
    # def _hasMore_(self):
    #     if( len(self._elements_) > 0):
    #         return True;
    #     line = self.file.readline()
    #     self._line_no_ = self._line_no_+1
    #     if not line:
    #         return False
    #     self._elements_ = [i.strip(' \t') for i in Lexer.split_rex.split(line) if i.strip(' \t')]
    #     return True
    #     #return self.hasMore()

    def getLineNo(self):
        return self._line_no_
    def getRetElements(self):
        return self._ret_elements_
#    @profile
    def _fill_buf_(self):
        #        while True:
        line = self.file.readline()
        if not line:
            return False
        self._line_no_ = self._line_no_+1
        # self._elements_ = [i.strip(' \t') for i in Lexer.split_rex.split(line) if i.strip(' \t')]
        self._elements_.extend( Lexer.find_rex.findall(line))
        return True
        pass

#    @profile
    def peek(self):
        if self._elements_:
            return self._elements_[0]
        return None

#    @profile
    def get(self):        
        #if self._hasMore_():
        if not self._elements_:
            return None        
        e = self._elements_.pop(0)
        self._ret_elements_.append(e) # TODO extend
        self._ret_elements_ = self._ret_elements_[-10:]
        if len(self._elements_) < 1:
            self._fill_buf_()
        return e

    def getN(self,num):
        result = []

        while len(result) < num:
            if not self._elements_:
                self._fill_buf_()
                if not self._elements_:
                    break;
            sres = len(result)
            left = num-sres
            maxEl = min( len(self._elements_), left )
            result = result + self._elements_[0:maxEl]
            self._elements_ = self._elements_[maxEl:]

        if not self._elements_:
            self._fill_buf_()
        self._ret_elements_+=result # TODO extend
        self._ret_elements_ = self._ret_elements_[-10:]
        return result

#    @profile
    def skipToNextLine(self):
        """skip to next newline + non newline item"""
        while True:
            i = 0
            found_n = False
            for element in self._elements_:
                if not found_n:
                    if element == '\n':
                        found_n = True
                else:
                    if element != '\n':
                        break
                i+=1            
            self._elements_ = self._elements_[i:]
            self._fill_buf_()
            if not self._elements_ or self._elements_[0]!='\n':
                break;
        return True
        # if self._elements_[0]!='\n'
        # while True:
        #     s = self.get()
        #     if not s:
        #         return False
        #     elif s == '\n':
        #         while True:
        #             s = self.peek()
        #             if s == '\n':
        #                 self.get()
        #             else:
        #                 return True
#            print "skipTonext: %r" % s




    def DebugState(self, string=""):
        return "%s; Line %d, Last elements: %r" % \
                           (string,self.getLineNo(),self.getRetElements())


    def Error(self,string):
        raise RuntimeError("%s; Line %d, Last elements: %r" %
                           (string,self.getLineNo(),self.getRetElements() ))

    def getRequireNextReg(self, rex, error_context="" ):
        val = self.get()
        if not rex.match(val):
            self.Error("lexer returned %r but %r compliance was expected - %s"%\
                       (val, rex.pattern, error_context) )
        return val
        
    def getRequireNext(self, string, context=""):
        val = self.get()
        if val != string:
            self.Error("lexer returned %r but %r was expected - %s" % (val, string, context) )
        return val

    def getType(self, usetype):        
        try:
            retval = usetype(self.get())
        except ValueError:
            self.Error("couldn't convert mixture num to %r" % usetype)
        return retval

        
        
    # def getRemaining(self):
    #     ("get the elements remaining in the internal buffer, usually that is until newline\n"
    #      "usually implies that this function probably is not a good idea")
    #     if self.hasMore():
    #         e = self.elements
    #         self.elements = []
    #         return e
    #     return []

    def skipIfNL(self):
        if(self.peek()=='\n'):
            self.skipToNextLine()
                

    
#    r'(\n|\s+|(?<!\\)".*?(?<!\\)"|(?<!\\)\'.*?(?<!\\)\')'
Lexer.split_rex = re.compile(r'(\n|\s+|\<[^\<\>]*\>|(?<!\\)".*?(?<!\\)"|(?<!\\)\'.*?(?<!\\)\')',re.MULTILINE)
Lexer.find_rex  = re.compile(r'[^\<\s\t\"\'\>]+|\<[^\>]+\>|\n|\"[^\"]+\"|\'[^\']+\'')
#r'[^\s\t\"\']+|\n|\"[^\"]+\"|\'[^\']+\'')
#http://stackoverflow.com/questions/79968/split-a-string-by-spaces-preserving-quoted-substrings-in-python

DTYPE_FLOAT = numpy.float32
#-------------------------------------------
# PARSE TOOLS - Mean
#-------------------------------------------
ParseUseMacro_rex = re.compile('~[ehopstuvw]')
ParseUseMacro_rexname=re.compile(r'"[^"]+"')#r'"[0-9a-zA-Z\-_%\^\:+@|#&\+/\!]+"')
def ParseUseMacro(lexer, context):
    mtype = lexer.getRequireNextReg(ParseUseMacro_rex)
    mname = lexer.getRequireNextReg(ParseUseMacro_rexname,
                                    ("macro name contains characters "
                                     "parser was not prepared for"))
    lexer.skipToNextLine()
    # trailing/leading '"' will be stripped by the macro functions
    return context.findOrDeclareMacro(mtype,mname)


def ParseMMF(lexer, mmf=None):
    if None == mmf: mmf = MMF()
    while True:
        mtype = lexer.peek()
        if not mtype:
            break
        elif mtype=='\n':
            mytpe = lexer.skipToNextLine()
            continue
        
        if mtype == '~o':
            macro = mmf.findOrDeclareMacro("~o","")
            macro.setTarget( ParseGlobalOpts(lexer))
            continue
        
        macro = ParseUseMacro(lexer, mmf)
        if mtype == "~e":
            macro.setTarget( ParseDepTrans(lexer))
        elif mtype=="~h":
            macro.setTarget( ParseHMM(lexer,mmf))
        elif (mtype=="~s"):
            macro.setTarget( ParseMultiStream(lexer, mmf))
        elif (mtype=="~p"): # or mtype=="~s"):
            macro.setTarget( ParseStream(lexer, mmf))
        elif mtype=="~t":
            macro.setTarget( ParseTransp(lexer))
        elif mtype=="~u":
            macro.setTarget( ParseMean(lexer))
        elif mtype=="~v":
            macro.setTarget( ParseVariance(lexer))
        elif mtype=="~w":
            macro.setTarget( ParseSWeights(lexer))
        else:
            lexer.Error("at element %r " % mtype)
    #    ehopstuvw
    return mmf

    

def ParseHMM(lexer, context):
    hmm = HMM()
    lexer.getRequireNext("<BEGINHMM>")
    lexer.skipIfNL()
    lexer.getRequireNext("<NUMSTATES>")
    hmm.numstates = lexer.getType(int)
    lexer.skipIfNL()
    for i in xrange(2,hmm.numstates):
        state = hmm.state[i] = ParseState(lexer, context)
        if state.number != i :
            lexer.Error( (" parsing states but state number "
                          "not right: should be %r but is %r") %
                         ( i, state.number))
    if lexer.peek() == "~t":
        hmm.transp = ParseUseMacro(lexer, context)
    else:
        hmm.transp = ParseTransp(lexer)
    lexer.getRequireNext("<ENDHMM>")
    lexer.skipIfNL()
    return hmm

def ParseGlobalOpts(lexer):
    gopts = GlobalOption()
    lexer.getRequireNext("~o")
    while True:
        lexer.skipIfNL()
        val = lexer.peek()
        if not val:
            break
        if ParseUseMacro_rex.match(val): ## start of next macro            
            break;
        val = lexer.get().upper()
        #print "val: %s " % val
        val = val.strip("<>")
        if   val == "STREAMINFO":
            gopts.streaminfo = {}
            num = lexer.getType(int)
            for i in xrange(1,num+1):
                gopts.streaminfo[i] = lexer.getType(int)
            lexer.skipIfNL()
        elif val == "MSDINFO":
            gopts.msdinfo = {}
            num = lexer.getType(int)
            for i in xrange(1,num+1):
                gopts.msdinfo[i] = lexer.getType(int)
            lexer.skipIfNL()
        elif val == "VECSIZE":
            gopts.vecsize = lexer.getType(int)
            lexer.skipIfNL()
        elif val in GlobalOption.covkinds:
            gopts.covkind = val
        elif val in GlobalOption.durkinds:
            gopts.durkind = val
        elif val in GlobalOption.parmkinds:
            gopts.parmkind = val
        else:
            lexer.Error("encountered unknown token while parsing GlobalOption macro: %r" % val)
        # DO A SANITY CHECK HERE

    return gopts

def ParseMultiStream(lexer, context):
    streams = {}
    while True: ### we do not check for "<STREAM>" on the first
                ### occurrence because it might be a pseudo stream!
        stream_val = ParseStream(lexer, context)
        streams[stream_val.streamNumber] = stream_val
        #        print "lexer: %r" % lexer.peek()    
        if lexer.peek() != "<STREAM>":
            break
    return streams

def ParseState(lexer, context):
    state = State()
    lexer.getRequireNext("<STATE>")
    state.number = lexer.getType(int)
    lexer.skipIfNL()
    if lexer.peek() == "~w":
        state.weight = ParseUseMacro(lexer, context)
    elif lexer.peek() == "<SWEIGHTS>":
        state.weight = ParseSWeights(lexer)
    if lexer.peek() == "~s":
        state.stream = ParseUseMacro(lexer, context)
    elif lexer.peek() == "~p": # artificial case
        state.stream[1] = ParseUseMacro(lexer, context)
    elif lexer.peek()=="<STREAM>":
        state.stream = ParseMultiStream(lexer, context)
#        print lexer.DebugState()
    else:
        state.stream[1] = ParseStream(lexer, context)
#        lexer.Error("error parse state : %r " % lexer.peek())
    return state

    pass

def ParseStream(lexer, context):
    """ parse stream or pseudo stream """
    stream_val = Stream()
    if lexer.peek()=="<STREAM>":
        lexer.getRequireNext("<STREAM>")
        stream_val.streamNumber = lexer.getType(int)
        lexer.skipToNextLine()
        if(lexer.peek() == "~p"):
            stream_val.mixture = ParseUseMacro(lexer,context)
        else:
            if( lexer.peek() == "~e"):
                stream_val.deptrans = ParseUseMacro(lexer, context)
            elif( lexer.peek() == "<DEPCLASS>"):
                stream_val.deptrans = ParseDepTrans(lexer)
            if( lexer.peek() == "<NUMMIXES>"):
                stream_val.mixture = ParseMixture(lexer,context)
            else:
                stream_val.mixture = ParsePseudoMixture(lexer, context)
    else: # probably pseudo Stream
        stream_val.streamNumber = 1
        stream_val.pseudo = True
        if( lexer.peek() == "<NUMMIXES>"):
            stream_val.mixture = ParseMixture(lexer,context)
        else:
            stream_val.mixture = ParsePseudoMixture(lexer, context)
        
                
    return stream_val


def ParsePDF(lexer, context):
    result = PDF()
    if( lexer.peek() == "~u" ):
        result.means = ParseUseMacro(lexer, context)
    elif( lexer.peek() == "<MEAN>"):
        result.means = ParseMean(lexer)
    else:
        lexer.Error("expected '~u' or '<MEAN>'")

    if( lexer.peek() == "~v" ):
        result.variances = ParseUseMacro(lexer,context)
    elif( lexer.peek() == "<VARIANCE>"):
        result.variances = ParseVariance(lexer)
    elif( lexer.peek() == "<INVCOVAR>"):
        result.variances = ParseCoVariance(lexer)        
    else:
        lexer.Error("expected '~v' or '<VARIANCE>'")

    if( lexer.peek() == "<GCONST>"):
        result.gconst = ParseGConst(lexer)
    return result
    
    pass

def ParsePseudoMixture(lexer,context):
    pdf = ParsePDF(lexer, context)
    mixture = Mixture(pdfs={1:pdf},weights={1:1.0},pseudo=True)
    return mixture

def ParseMixture(lexer,context):
    lexer.getRequireNext("<NUMMIXES>")
    num = lexer.getType(int)
    lexer.skipToNextLine()
    mixture = Mixture()
    for i in xrange(1,num+1):
        lexer.getRequireNext("<MIXTURE>")
        mixNum = lexer.getType(int)
        if mixNum != i :
            lexer.Error("retrieved mixture number, but it was %d instead %d" %\
                        (mixNum, i))
        weight = lexer.getType(DTYPE_FLOAT)
        lexer.skipToNextLine()
        pdf = ParsePDF(lexer, context)
        mixture.weights[i] = weight
        mixture.pdfs[i] = pdf
    return mixture

def ParseGConst(lexer):
    lexer.getRequireNext("<GCONST>")
    try:
        val = DTYPE_FLOAT(lexer.get())
    except ValueError:
        lexer.Error("couldn't convert gconst value to float")
    lexer.skipToNextLine()
    return val

def ParseVector(lexer, tag):
    lexer.getRequireNext(tag)
    try:
        val = int(lexer.get())
    except ValueError:
        lexer.Error("couldn't convert  size of %s entry  to int" % tag)
    lexer.skipToNextLine()
    if(val>0):
        values = lexer.getN(val)
        try:
            vector = numpy.array( values, dtype= DTYPE_FLOAT)
        except ValueError:
            lexer.Error("couldn't convert %s data (n:%d) to floats" % (tag,val))
        lexer.getRequireNext("\n", context="%d values to be read, got: %r" % (val,values))
    else:
        vector= numpy.array([], dtype=DTYPE_FLOAT)
    return vector


### todo remove the need for the functions below, one would do just fine
def ParseMean(lexer):
    return ParseVector(lexer, "<MEAN>")
def ParseVariance(lexer):
    return ParseVector(lexer, "<VARIANCE>")
#TODO
def ParseCoVariance(lexer):
    return 1/ParseVector(lexer, "<INVCOVAR>")
def ParseSWeights(lexer):
    return ParseVector(lexer, "<SWEIGHTS>")

def ParseMatrix(lexer, tag, two_dims=False):
    lexer.getRequireNext(tag)
    rows    = lexer.getType(int)
    if two_dims:
        columns = lexer.getType(int)
    else:
        columns = rows
    lexer.skipIfNL()
    values = []
    for i in xrange(rows):
        values.append( lexer.getN(columns))
        lexer.getRequireNext('\n')
    try:
        result = numpy.array(values, dtype=DTYPE_FLOAT)
    except ValueError:
        lexer.Error("couldn't convert %s values to float: %r" % (tag,values))
    return result

def ParseTransp(lexer):
    return ParseMatrix(lexer, "<TRANSP>", two_dims=False)

def ParseDepTrans(lexer):
    return ParseMatrix(lexer, "<DEPCLASS>", two_dims=True)

# --------------------------------WRITING to file --------------------------------------------
def WriteUseMacro(fileobj, macro):
    fileobj.write('%s "%s"\n' % (macro.macroType, macro.macroId))
    pass

def WritePDF(fileobj, pdf):
    if isMacro(pdf.means):
        WriteUseMacro(fileobj, pdf.means)
    else:
        WriteVector(fileobj,"<MEAN>", pdf.means)
    if isMacro(pdf.variances):
        WriteUseMacro(fileobj, pdf.variances)
    else:
        WriteVector(fileobj,"<VARIANCE>", pdf.variances)
    if pdf.gconst!=None:
        WriteGConst(fileobj, pdf.gconst)
def WriteGConst(fileobj, gconst):
    fileobj.write("<GCONST> %10.6e \n" % gconst)

def WriteVector(filobj, name, vector):
    vecview = vector.reshape(1,-1)
    veclen  = vector.shape[-1]
    filobj.write("%s %d\n" % (name, veclen))
    if veclen > 0:        
        numpy.savetxt(filobj, vecview, delimiter='', fmt=' %10.6e')

def WriteMatrix(filobj, name, matrix, two_dims=False):
    if two_dims:
        filobj.write("%s %d %d\n" % (name, matrix.shape[0], matrix.shape[1]))
    else:
        filobj.write("%s %d\n" % (name, matrix.shape[0]))
    (rows, cols) = matrix.shape
    numpy.savetxt(filobj, matrix, delimiter='', fmt=' %10.6e')
    
def WriteMixture(fileobj, mixture):
    if not mixture.pseudo:
        fileobj.write("<NUMMIXES> %d\n" % len(mixture.pdfs))
    keys = sorted( mixture.pdfs.iterkeys())
    if mixture.pseudo:
        WritePDF( fileobj, mixture.pdfs[ keys[0]])
    else:
        for k in keys:
            fileobj.write("<MIXTURE> %d %10.6e\n" % (k, mixture.weights[k]) )
            WritePDF( fileobj, mixture.pdfs[ k ] )

#def WriteDepTrans(fileobj, deptrans):
#    pass

def WriteMultiStream(fileobj, multistream):
    for stream in multistream:
        WriteStream(fileobj, multistream[stream])


def WriteStream(fileobj, stream):
    if not stream.pseudo:
        fileobj.write("<STREAM> %d\n" % stream.streamNumber)
    if stream.deptrans != None:
        if isMacro(stream.deptrans):
            WriteUseMacro(fileobj, stream.deptrans)
        else:
            WriteMatrix(fileobj,"<DEPCLASS>",stream.deptrans, two_dims=True)
    if isMacro(stream.mixture):
        WriteUseMacro(fileobj, stream.mixture)
    else:
        WriteMixture(fileobj,stream.mixture)

def WriteState(fileobj, state):
    fileobj.write("<STATE> %d\n" % state.number)
    if isMacro(state.weight):
        WriteUseMacro(fileobj, state.weight)
    elif len(state.weight)>0:
        WriteVector(fileobj, "<SWEIGHTS>", state.vector)
    if isMacro(state.stream) and macroType(state.stream)=='~s':
        WriteUseMacro(fileobj, state.stream)
    else:
        keys = sorted( state.stream.iterkeys())
        for k in keys:
            WriteStream(fileobj, state.stream[k])
def WriteGlobalOpts(fileobj, gopts):
    fileobj.write("~o \n")
    # stream info
    nums = [ str(gopts.streaminfo[k]) for k in sorted(gopts.streaminfo.iterkeys())]
    fileobj.write("<STREAMINFO> %d %s \n" % (len(nums), " ".join(nums)) )    
    # msdinfo
    if gopts.msdinfo != None:
        msd  = [ str(gopts.msdinfo[k]) for k in sorted(gopts.msdinfo.iterkeys())]
        fileobj.write("<MSDINFO> %d %s \n" % (len(msd), " ".join(msd)) )    
    # vecsize
    if gopts.vecsize != None:
        fileobj.write("<VECSIZE> %d" % gopts.vecsize)
    # durkind
    if gopts.durkind != None:
        fileobj.write("<%s>" % gopts.durkind)
    # covkind
    if gopts.covkind != None:
        fileobj.write("<%s>" % gopts.covkind)
    # parmkind
    if gopts.parmkind != None:
        fileobj.write("<%s>" % gopts.parmkind)
    fileobj.write('\n')
    pass
def WriteHMM(fileobj, hmm):
    fileobj.write("<BEGINHMM>\n")
    fileobj.write("<NUMSTATES> %d\n" % (hmm.numstates) )
    keys = sorted( hmm.state.iterkeys())
    for k in keys:
        WriteState(fileobj, hmm.state[k])
    if isMacro(hmm.transp):
        WriteUseMacro(fileobj, hmm.transp)
    else:
        WriteMatrix(fileobj, "<TRANSP>", hmm.transp)
        
    fileobj.write("<ENDHMM>\n")
    
def WriteMMF(fileobj, mmfile):
    WriteGlobalOpts(fileobj,mmfile.getMacro("~o","").target)
    for macro_type in WriteMMF.macro_order:
        if not mmfile.macros.has_key("~"+macro_type):
            continue
        macros = mmfile.getMacros("~"+macro_type)
        for macro in macros:
            target = macros[macro].target
            WriteUseMacro(fileobj, macros[macro])
            if macro_type in WriteMMF.macro_explicit:
                if macro_type=="u":
                    WriteVector(fileobj, "<MEAN>", target)
                elif macro_type=="v":
                    WriteVector(fileobj, "<VARIANCE>", target)
                elif macro_type=="t":
                    WriteMatrix(fileobj, "<TRANSP>", target, False)
                elif macro_type=="e":
                    WriteMatrix(fileobj, "<DEPCLASS>", target, True)
                elif macro_type=="s":
                    WriteMultiStream(fileobj, target)
            else:
                WriteMMF.writers[target.__class__.__name__]( fileobj, target)

    pass
WriteMMF.macro_order="eutvwpsh"
WriteMMF.macro_explicit=set("etvus")
WriteMMF.writers = {
    'State' : WriteState,
    'Stream': WriteStream,
    'HMM'   : WriteHMM,
    'PDF'   : WritePDF,
    'Mixture': WriteMixture,
    
    }
