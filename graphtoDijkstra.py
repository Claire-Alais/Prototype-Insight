# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 10:46:53 2021

@author: clair

Floyd-Warshall alternative: Dijkstra from city center to city center

/!\ not yet very robust to change in names of columns etc,
/!\ adaptations needed for other cities
"""

import sys
import argparse
import pandas
import numpy
import save_module
import networkx

#filter functions______________________________________________________________

def grandParis(stri) :
  stri = str(stri)
  if (stri[0:2] in ['75', '92', '93', '94']) or stri in ['95018', '78645', '91479', '91027', '78326', '91589', '91687'] :
    return True
  else : 
    return False

#useful functions______________________________________________________________

verbose = 1
def vprint(stri,level):
    global verbose
    if verbose >= level:
        print(stri)

def find_min(lats, longs, latitude, longitude, dfNodes):
  distances = [(float(lats[i])-latitude)**2 + (float(longs[i])-longitude)**2 for i in range(len(lats))]
  return dfNodes['Id'].loc[numpy.argmin(distances)]

def city_nodes(dfNodes, dfCoord):
    A = dfNodes["Latitude"].values
    B = dfNodes["Longitude"].values
    npCoord = dfCoord.values
    liste_commune=[]
    for i in range(len(npCoord)):
        liste_commune.append(find_min(A,B, float(npCoord[i,1]), float(npCoord[i,2])))
    return liste_commune

#core__________________________________________________________________________
def main():
    """
    method to read the command line arguments and run the program
    """
    parser = argparse.ArgumentParser(\
             description='This script provides you paths from and to city centers',
             epilog="Have fun while usage; ")
    #input selection
    parser.add_argument("-n", "--graphNodes", help='path to node list file')
    parser.add_argument("-e", "--graphEdges", help='path to edge list file')
    parser.add_argument("-c", "--cityCoord", help='path to coordinates of city centers file')
    parser.add_argument("-f", "--filter", help="selects a subset of cities in the city-coord file",
                            dest='cityFilter', action='store_true')
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3],
                                help="increase output verbosity")
    args = parser.parse_args()

    global verbose
    verbose = args.verbosity
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    #get the input
    filecount = 0
    if args.graphNodes:
        filecount += 1
        nodes_file = args.graphNodes
    if args.graphEdges:
        filecount += 1
        edges_file = args.graphEdges    
    if args.cityCoord:
        filecount += 1
        coord_file = args.cityCoord   
    if filecount != 3:
        sys.exit("ERROR: not enough input given")
    
    main_function(nodes_file, edges_file, coord_file, args.cityFilter)

def main_function(nodes_file, edges_file, coord_file, cityFilter=False):
    vprint("Starting preprocessing...",2)
    
    # read files
    dfCoord = pandas.read_csv(coord_file)
    dfNodes = pandas.read_csv(nodes_file)
    dfEdges = pandas.read_csv(edges_file)                         
    
    # if there are too many useless nodes in the node list, a first filter
    dfNodes = pandas.DataFrame(dfEdges['source'].unique()).merge(dfNodes, 
                              'left', left_on=0, right_on='Id')
    #dfNodes.to_csv('nodesShort.csv')
    
    # filtering the coordinates files if it covers a bigger region
    if cityFilter:
        if cityFilter == 'grandParis':
            dfCoord['selectionGP'] = [grandParis(x) for x in dfCoord['code_insee'].to_list()]
            dfCoord = dfCoord[['code_insee','latitude','longitude']].loc[dfCoord['selectionGP'] == True].reset_index()
            #dfCoord.to_csv('grandParis_coord.csv')          
        else : 
            sys.exit("ERROR: this filter is not defined. Use 'grandParis' or define it beforehand")
    
    # compute closest to node of the graph to each city center
    list_cities = city_nodes(dfNodes, dfCoord)
    dfCoord['closest_node'] = list_cities
    
    # graph theory computations
    vprint("Starting path optimization...",2)
    G = save_module.load_graph(edges_file)
    dictionnary = {}
    count = 1
    vprint("There are "+ len(list_cities)+ " cities to look at",3)
    for source_commune in list_cities:
        if count % 10 == 0 :
            vprint("Done "+count,3)
            dict_provisoire_length, dict_provisoire_path  = networkx.algorithms.shortest_paths.weighted.single_source_dijkstra(G, source_commune, weight = 'length')
            for commune in set(list_cities).intersection(dict_provisoire_length.keys()):
                dictionnary[(source_commune, commune)] = dict_provisoire_length[commune], dict_provisoire_path[commune]
                count += 1
    vprint("Computations finished, saving to csv file",2)
    pandas.DataFrame(dictionnary).transpose().to_csv('distances_paths_cities.csv')
    

if __name__ == '__main__':
    main()