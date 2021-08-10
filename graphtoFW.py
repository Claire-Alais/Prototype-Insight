# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 11:51:07 2021

@author: clair

Takes the graph from the OSMtoGraph or another, and returns the matrix of Floyd-Warshall routes
"""

import networkx
import sys
import argparse
import save_module



# main
#
# method to read the command line arguments and run the program
def vprint(stri,level):
    global verbose
    if verbose >= level:
        print(stri)

def reconstruct_path(source, target, predecessors):
    """(Copy-pasted directly from networkx because I had an error)
    Reconstruct a path from source to target using the predecessors
    dict as returned by floyd_warshall_predecessor_and_distance

    Parameters
    ----------
    source : node
       Starting node for path

    target : node
       Ending node for path

    predecessors: dictionary
       Dictionary, keyed by source and target, of predecessors in the
       shortest path, as returned by floyd_warshall_predecessor_and_distance

    Returns
    -------
    path : list
       A list of nodes containing the shortest path from source to target

       If source and target are the same, an empty list is returned

    Notes
    -----
    This function is meant to give more applicability to the
    floyd_warshall_predecessor_and_distance function

    See Also
    --------
    floyd_warshall_predecessor_and_distance
    """
    if source == target:
        return []
    prev = predecessors[source]
    curr = prev[target]
    path = [target, curr]
    while curr != source:
        curr = prev[curr]
        path.append(curr)
    return list(reversed(path))


def main():
    print('The beginning of a great adventure')
    parser = argparse.ArgumentParser(\
             description='This script computes optimal trajectories',
             epilog="Have fun while usage; graphtoFW.py -g graph_nx.pkl -v 2")
    #input selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f','--filename','--file', help='the path to a local file')
    group.add_argument("-b", "--bbox", help="an area to download highways in the format 'left,bottom,right,top'")
    group.add_argument("-g", "--graph", help="path to the graph file")
    parser.add_argument("-t", "--transport", choices=["all", "hw", "pt"], default="all",
            help="Experimental Option! Uses as well public transportation information")
            #type=argparse.FileType('w'),
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3],
                                help="increase output verbosity")
    parser.add_argument("-o", "--osm-file", nargs='?', const='export.osm',
            help="export the routeable graph as osm-xml to given file")
    
    args = parser.parse_args()
    
    global verbose
    verbose = args.verbosity
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    #get the input
    G = ""
    if args.filename or args.bbox:
        print("First, let's build the graph. Calling OSMtoGraph.")
        import OSMtoGraph
        if args.filename:
            fn = args.filename
        if args.bbox:
            [left,bottom,right,top] = [float(x) for x in args.bbox.split(",")]
            fn = OSMtoGraph.getNetwork(left,bottom,right,top,args.transport)
        G = OSMtoGraph.main_function(fn, transport=args.transport, osm_file=args.osm_file, graph=True, verbose=verbose, return_graph=True)
        #subprocess.call([sys.executable, 'OSMtoGraph.py', args])
        #sys.runfile('C:/Users/clair/Documents/Insight-Signals/OSMtoGraph.py', wdir='C:/Users/clair/Documents/Insight-Signals')
    if args.graph:
        G = save_module.load_obj(args.graph)
    if G==None:
        sys.exit("ERROR: no input given")

    #networkx magick
    save_module.save_obj(G, 'graph_nx')
    predecessors, distance = networkx.floyd_warshall_predecessor_and_distance(G)
    
    save_module.save_obj(predecessors, 'predecessors')

if __name__ == '__main__':
    main()