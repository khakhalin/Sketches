import numpy as np

class Graph:
    """Minimalistic graph toolbox."""
    def __init__(self,nv=1,directed=False):
        '''Create an empty graph.'''
        self.adj = {}
        self.nv = nv
        self.directed = directed # Plug for the future
        for i in range(self.nv):
            self.adj[i] = []
            
    def n(self): 
        """Number of vertices + updates nv property."""
        self.nv = len(self.adj)
        return self.nv
            
    def __str__(self):
        return f'Graph of {len(self.adj)} edges:\n'+'\n'.join([str(key)+':'+str(self.adj[key]) for key in self.adj])
    
    def add_edge(self,i,j):
        """Adds one edge from i to j (and j to i if the graph isn't directed)."""
        if i not in self.adj: 
            self.adj[i] = [j]
        else:                 
            if j not in self.adj[i]: # Say no to double-edges
                self.adj[i].append(j)
        if j not in self.adj:
            self.adj[j] = []
        if not self.directed:
            self.directed = True # A roundabout way to add the opposite edge recursively
            self.add_edge(j,i)   # .. without triggering an infinite loop.
            self.directed = False        
                
    def del_edge(self,i,j):
        """Deletes edge from i to j (and if undirected, also from j to i)."""
        if i not in self.adj: return
        if j not in self.adj: return
        if j in self.adj[i]:          # Remove gives an error if you try to remove non-existent element
            self.adj[i].remove(j)
        if not self.directed:
            if i in self.adj[j]:
                self.adj[j].remove(i)
                
    def add_edges(self,ts):
        """Builds a graph from a list of tuples"""
        for (i,j) in ts:
            self.add_edge(i,j)
                
    def a(self):
        """Returns adjacency matrix."""
        out = np.zeros((len(self.adj),len(self.adj)),dtype=int)
        for i in self.adj:
            for j in self.adj[i]:
                out[i,j] = 1
        return out
    
    def dfs(self,v=None,visited=None,path=None,topord=None,verbose=False):
        """Depth-first search from a given, or random, node. Returns topological sorting from this node."""
        if v is None: v=next(iter(self.adj.keys()))     # If needed, pick some random vertex as a root
        if visited is None: visited = []                # If needed, set all v as unvisited
        if path is None:    path = []
        if topord is None:  topord = []                 # Topological ordering, will be returned
        visited.append(v)                               # Mark current v as visited
        path += [v]
        if verbose: print(path)
        for i in self.adj[v]:                           # For all connections from the current vertex
            if i not in visited:                        # If they weren't yet visited, visit them
                topord = self.dfs(i,visited,path,topord=topord,verbose=verbose)
        return [v]+topord       
                
    def bfs(self,v=None,target=None,verbose=False):
        """Breadth-first exploration, looking for a distance from one vertex to another."""
        if v is None: v = next(iter(self.adj.keys()))   # If needed, pick some random vertex as a root
        q = [(v,0)]                                     # Queue of vertices to be visited, with their distances from the root
        visited = [0]*len(self.adj)                     # Not recursive, so mark all as unvisited
        while len(q)>0:                                 # While queue isn't empty
            (v,d) = q.pop(-1)                           # Pop the last element of the queue
            if v==target:
                return d
            if verbose: print(v,':',q)
            visited[v] =  1
            for i in self.adj[v]:
                if visited[i]==0 and ((i,d+1) not in q):
                    q.append((i,d+1))
                    
    def reverse(self):
        """Reverse the graph."""
        g = Graph(self.n(), self.directed) # Strictly speaking, there's no need to reverse undirected.
        for (k,vals) in self.adj.items():  # If I had a copy() method, I could have just used it here.
            for v in vals:
                g.add_edge(v,k)
        return g
    
    def randomize(self,nedges=None):
        """Add random edges to the graph (by default, E = V)."""
        if nedges is None: nedges = self.nv
        for _ in range(nedges):
            i = np.random.randint(self.nv)
            j = np.random.randint(self.nv)
            self.add_edge(j,i)
            
    def erase(self):
        """Remove all edges from a graph."""
        for k,v in self.adj.items():
            self.adj[k] = []
            
    def urchin(self,n=20):
        """Generate a directed graph with high modularity."""
        self.erase()
        nclusters = np.floor(np.sqrt(n)).astype(int)
        orphans = list(range(n))                       # List of nodes without links
        for iclust in range(nclusters):
            lo = iclust*nclusters
            if iclust==nclusters-1:
                hi = n
            else:
                hi = (iclust+1)*nclusters        
            for i in range(hi-lo):
                node1 = np.random.randint(low=lo,high=hi)
                node2 = np.random.randint(low=lo,high=hi)
                self.add_edge(node1 , node2)
                if node1 in orphans: orphans.remove(node1)
                if node2 in orphans: orphans.remove(node2)
        for i in orphans:
            if np.random.uniform(1)<0.5:
                self.add_edge(i, np.random.randint(n))
            else:
                self.add_edge(np.random.randint(n),i)
    
    def rpo(self):
        """Reversed Post-Order (DFS-based). Returns a toporder on a DAG, just an RPO on others."""
        queue = list(self.adj.keys()) # By itself keys() return dict keys object, and not a list
        topo = []
        while len(queue)>0:
            i = queue.pop()
            temp = self.dfs(i)
            queue = [q for q in queue if q not in temp] # Remove newly visited nodes from the queue
            temp =  [q for q in temp  if q not in topo] # Remove previously visited nodes from new batch
            topo += temp
        return topo
    
    def trim_loops(self):
        """Removes loops from a graph"""
        for k,v in self.adj.items():
            if k in v:
                v.remove(k)
    
    def _dfs_cycler(self,v,root=None,visited=None):
        """Helper function: checks if you can cycle from a node to itself."""
        if root is None: root=v
        if visited is None: visited = []
        if root in self.adj[v]: return False
        if self.adj[v]==[]: return True
        for i in self.adj[v]:
            if i not in visited:
                visited.append(i)
                if not self._dfs_cycler(i,root,visited):
                    return False
        return True
    
    def isdag(self):
        """Checks if there are any cycles in a graph."""
        if not self.directed: return False # Undirected graphs can't be DAGs
        queue = list(self.adj.keys())
        for v in queue:
            if not self._dfs_cycler(v):
                return False
        return True