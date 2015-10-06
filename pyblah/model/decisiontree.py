#!/usr/bin/python

import re
import sys

class MetaTree:
    """ Contains mutliple Decision Trees (for each state).
        So a MetaTree might represents the mcep-stream and hold 5 trees for each state. """
    
    def __init__(self):
        self.treeList = []
        self.treeDict = {}
        self.leavesList = []
        self.leavesDict = {}
        self.nodeList = []
        
    def loadTrees(self, filename, stateRange=range(2,7)):        
        for i in stateRange:
            dt = DecisionTree()
            dt.load( filename, i )
            self.addStateTree( dt )
        
    def printStats(self):
        for t in self.treeList:
            print "Tree state: ", t.state
            t.printStats()
        
    def addStateTree(self, tree):
        self.treeList.append( tree )
        self.treeDict[ tree.state ] = tree
        
        self.leavesList +=  tree.leavesList        
        self.nodeList += tree.nodeList 
        
        self.leavesDict = {}
        for l in self.leavesList:
            self.leavesDict[ l.macroName ] = l
            
            
    def classifyLabelString(self, labelString):
        ret = []
        for t in self.treeList:
            ret.append( t.classifyLabelString( labelString ) )
            
        return ret            
            
    def getStateTree(self, statenum ):
        return self.treeDict[ statenum ]


class DecisionTree:
    """ Represents a single decision tree (for a single state and stream) """

    ## Class Node
    class Node:
        question = ""
        macroName = ""
        code = None
        left = None             # false
        leftCode = None
        right = None            # true
        rightCode = None
        parent = None
        tree = None

                
        def printContent(self):
            """ Prints the node content to stdout """
                        
            if self.leftCode is not None and self.rightCode is not None:
                print 'Code: ' + self.code + ', Question: "' + self.question \
                    + '", Left: ' + self.leftCode + ", Right: " + self.rightCode
            else:
                print 'Code: ' + self.code + ', Question: ' + self.question
                
        def getPath(self):
            """ Get the path to this node """
                
            ret = self.question         
            if self.parent is not None:                               
                return self.parent.getPath() + ' - ' + ret
            else:
                return ret
            
        def _visitParentsR(self, visitor, lastNode, retlist):
            ret = visitor(self, lastNode)
            if ret is not None:
                retlist.append(ret)
            if self.parent is not None: 
                self.parent.visitParentsR(visitor, self, retlist)           
                        
                        
        def visitParents(self, visitor):
            """ visits itself and all parents and applies the function visitor(Node current, Node previousNode) """
            
            #TODO: would be simpler and safer without recursion
            
            retlist = []
                
            ret = visitor(self, None)         
            if ret is not None: retlist.append(ret)
            
            if self.parent is not None: 
                self.parent._visitParentsR(visitor, self, retlist)
            return retlist            
            
    ##-----------------------------------
                 
                 
    # init             
    def __init__(self):       
        self.leavesList = []       
        self.leavesDict = {}
        self.nodeList = []
        self.nodeDict = {}
        self.state = 0
        self.stream = 1
        self.questionsDict = {}
        self.root = None
 
 
    def printStats(self):
        """ Prints some stats of the tree. """
        print "  Number of nodes: ", len(self.nodeList)
        print "  Number of leaves: ", len(self.leavesList)
            
    # load
    def load(self, path, state):
        """ loads a tree from path for the given state and stream """
        
        self.state = state
        currentState = 0
        
        # load tree file
        treeFile = open(path)
        
        # loop tree file
        for line in treeFile:
            line = line.strip()            
            #print line , " compare with {*}[" + str(state) + "]"
            # Question definition
            # i.e.: QS Pos_C-Syl_in_C-Phrase(Bw)<=12 { "*-?#*","*-10#*","*-11#*","*-12#*" }
            m = re.match( r'QS\s+([^{]+){([^}]+).*', line )
            if m is not None:
                self.questionsDict[ m.group(1).strip() ] =  [ x.strip().strip("\"") for x in m.group(2).split(",") ]

            # begin of section - state and stream info
            elif line.startswith( '{*}[' + str(state) + ']' ):
                currentState = int(state)             
            # begin of tree structure info   
            elif line == '{':
                continue                  
            # end of tree structure info  
            elif line == '}' and currentState > 0:                
                self.buildStateTree(currentState)
                currentState = 0
            # tree structure line                
            elif currentState > 0:
                self._handleLine(currentState, line)
        
        treeFile.close()                                                    
        return True
        
    # handleLine
    def _handleLine(self, state, line):
        """ Handles a single tree line """

        # example line:
        #                   -29   L-sil    -51   "mcep_s2_1"        
        m = re.match(r'([0-9-]+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
        if m is None:
            print 'Invalid line: ' + line
        else:                        
            n = self.Node()
            n.code = m.group(1)
            n.question = m.group(2)
            n.leftCode = m.group(3)
            n.rightCode = m.group(4)
                        
            self.nodeList.append(n)
            self.nodeDict[ n.code ] = n
            
            #TODO: could be safer :)
            if self.root is None:
                self.root = n                                  
          
          
    # buildStateTree  
    def buildStateTree(self, state):
        """ builds the tree for state after all node data has been read """

        # loop all nodes
        for n in self.nodeList:
            # find real references for children codes if they exist
            if n.leftCode in self.nodeDict:
                n.left = self.nodeDict[ n.leftCode ]
                n.left.parent = n
            # else, the child it has to be a leaf with a model name                
            else:
                leaf = self.Node()
                leaf.code = n.leftCode
                leaf.macroName = n.leftCode.strip( '"' )
                leaf.parent = n
                leaf.tree = self
                self.leavesList.append(leaf)
                self.leavesDict[ leaf.macroName ] = leaf
                n.left = leaf
                #print 'Added leaf ' + leaf.code
            
            # find real references for children codes if they exist
            if n.rightCode in self.nodeDict:
                n.right = self.nodeDict[ n.rightCode ]            
                n.right.parent = n
            # else, the child it has to be a leaf with a model name                
            else:            
                leaf = self.Node()
                leaf.code = n.rightCode
                leaf.macroName = n.rightCode.strip( '"' )
                leaf.parent = n
                leaf.tree = self
                self.leavesList.append(leaf)
                self.leavesDict[ leaf.macroName ] = leaf
                n.right = leaf
                #print 'Added leaf ' + leaf.code
            


    def classifyLabelString(self, labelString):
        """ classifies a given labelstring and returns the name of the resulting model """
        
        if self.root is None: return ""
         
        currentNode = self.root
        
        while currentNode.macroName == "":
            # answer question            
            if currentNode.question not in self.questionsDict:
                print "ERROR: Question " + currentNode.question + " unknown!"
                return ""
            
            correctAnswerList = self.questionsDict[ currentNode.question ]

            # see if the label answers any of the questions correctly            
            found = False                                                    
            for ca in correctAnswerList:
                ca_mod = (re.escape( ca.strip("\"*") )).replace( "\?", "." )
                
                if re.search( ca_mod, labelString ) is not None:
                    found = True
                    break
                 
            #if True in [ x.strip("\"*") in labelString  for x in correctAnswerList ]:
            if found:
                currentNode = currentNode.right
            else:
                currentNode = currentNode.left
            
        if currentNode:                                
            return currentNode.macroName
        else: 
            return ""
        
        


        
if __name__ == '__main__':
    #label = r"         0    3460000 x^x-sil+h=OY@x_x/A:0_0_0/B:x-x-x@x-x&x-x#x-x$x-x!x-x;x-x|x/C:1+1+2/D:0_0/E:x+x@x+x&x+x#x+x/F:content_2/G:0_0/H:x=x@1=1|0/I:9=4/J:9+4-1/VAR:at"
    #label = r"   3460000    4080000 x^sil-h+OY=t@1_2/A:0_0_0/B:1-1-2@1-2&1-9#1-4$1-4!0-2;0-2|0/C:0+0+2/D:0_0/E:content+2@1+4&1+3#0+1/F:content_1/G:0_0/H:9=4@1=1|L-L%/I:0=0/J:9+4-1/VAR:at"
    label = r"  14020000   14380000 B^P6-s+f=P9e@3_1/A:0_0_1/B:0-0-3@2-1&7-2#3-2$3-2!2-1;2-1|0/C:1+1+3/D:content_1/E:content+2@5+2&5+1#1+1/F:content_1/G:0_0/H:8=6@1=1|L-L%/I:0=0/J:8+6-1/VAR:goi"
    
    if len(sys.argv) < 2:
        sys.exit( "Usage: python " + sys.argv[0] + " <treefile>" )
        
    t = DecisionTree()
    
    
    for i in range( 2, 7 ):
    
        #t.load(sys.argv[1] , i)
        t.load( "../../../../csc_to_goi/models_goi_1.0_mono2/tree.logF0.inf" , i)   
            
        # classify test
        print t.classifyLabelString( label )
    