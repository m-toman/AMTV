'''
Created on 16.05.2013

Dynamic timewarping implementation
http://en.wikipedia.org/wiki/Dynamic_time_warping

@author: mtoman
'''

 
import sys
 
class Dtw(object):
    
    def __init__(self, seq1, seq2, distance_func=None):
        '''
        seq1, seq2 are two lists,
        distance_func is a function for calculating
        the local distance between two elements.
        '''
        self._seq1 = seq1
        self._seq2 = seq2
        self._distance_func = distance_func if distance_func else lambda: 0
        self._map = {(-1, -1): 0.0}
        self._distance_matrix = {}
        self._path = []
        self.distance_map = {} 
     
    def get_distance(self, i1, i2):
        ret = self._distance_matrix.get((i1, i2))
        if not ret:
            ret = self._distance_func(self._seq1[i1], self._seq2[i2])
            self._distance_matrix[(i1, i2)] = ret
        return ret
     
    def calculate(self):
        # nice but crashes due to recursion depth:
        # return self.calculate_backward(len(self._seq1) - 1,
        #                                len(self._seq2) - 1)
        # so instead we use an iterative approach.
        
        for i in range( 0, len(self._seq1) ):
            #DTW[i, 0] := infinity
            self._map[(i,-1)] = float('inf')
            
        for i in range( 0, len(self._seq2) ):
            #DTW[0, i] := infinity
            self._map[(-1,i)] = float('inf')
            
        self._map[(-1,-1)] = 0

        #for i := 1 to n
        #    for j := 1 to m
        #        cost:= d(s[i], t[j])
        #        DTW[i, j] := cost + minimum(DTW[i-1, j  ],    // insertion
        #                                    DTW[i  , j-1],    // deletion
        #                                    DTW[i-1, j-1])    // match        

        for i in range( 0, len(self._seq1) ):
            for j in range( 0, len(self._seq2) ):
                cost = self.get_distance(i, j)
                self.distance_map[(i,j)] = cost
                self._map[(i,j)] = cost + min( self._map[ i-1 , j    ],      # insertion
                                               self._map[ i   ,  j-1 ],      # deletion
                                               self._map[ i-1 ,  j-1 ]       # match
                                            )
        return self._map
                                        

    def calculate_constrained(self, r):

        for i in range(-1, len(self._seq1)):
            for j in range(-1, len(self._seq2)):

                if i == -1 and j == -1:
                    self._map[(i,j)] = 0.0
                    continue
                elif i == -1 or j == -1:
                    self._map[(i,j)] = float('inf')
                    continue
                elif abs(i - j) > r:
                    continue
                elif abs(i - j) == r:
                    self._map[(i,j)] = float('inf')
                    continue

                cost = self.get_distance(i, j)
                self.distance_map[(i,j)] = cost
                self._map[(i,j)] = cost + min(self._map[ i-1 , j    ],      # insertion
                                              self._map[ i   ,  j-1 ],      # deletion
                                              self._map[ i-1 ,  j-1 ]       # match
                                             )
        return self._map

#    def calculate_backward(self, i1, i2):
#        '''
#        Calculate the dtw distance between
#        seq1[:i1 + 1] and seq2[:i2 + 1]
#        '''
#        if self._map.get((i1, i2)) is not None:
#            return self._map[(i1, i2)]
#         
#        if i1 == -1 or i2 == -1:
#            self._map[(i1, i2)] = float('inf')
#            return float('inf')
#         
#        min_i1, min_i2 = min((i1 - 1, i2), (i1, i2 - 1), (i1 - 1, i2 - 1),
#                                key=lambda x: self.calculate_backward(*x) )
#         
#        self._map[(i1, i2)] = self.get_distance(i1, i2) + self.calculate_backward(min_i1, min_i2)
#         
#        return self._map[(i1, i2)]
     
    def get_path(self):
        '''
        Calculate the path mapping.
        Must be called after calculate()
        '''
        i1, i2 = (len(self._seq1) - 1, len(self._seq2) - 1)
        while (i1, i2) != (-1, -1):
            self._path.insert(0,(i1, i2))
            min_i1, min_i2 = min((i1 - 1, i2), (i1, i2 - 1), (i1 - 1, i2 - 1),
                                    key=lambda x: self._map[x[0], x[1]])
            i1, i2 = min_i1, min_i2
        return self._path
     
