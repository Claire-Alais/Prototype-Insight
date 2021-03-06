# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 10:46:53 2021

@author: clair

Floyd-Warshall alternative: Dijkstra from city center to city center

/!\ not yet very robust to change in names of columns etc,
/!\ adaptations needed for other cities

Missing cities in dt_idf_loc.csv, to add to have a complete Grand Paris dataset
df2 = pandas.DataFrame([[93073,48.95,2.57222],
                    [92026,48.8972,2.2522],
                    [92004,48.91075,2.288933],
                    [75101,48.86263, 2.336298 ],
                    [75102,48.867903, 2.344111],
                    [75103,48.863053, 2.359368],
                    [75104,48.854229, 2.357364],
                    [75105,48.844509, 2.349863],
                    [75106,48.848968, 2.332671],
                    [75107,48.856083, 2.312439],
                    [75108,48.872527, 2.312586],
                    [75109,48.876897, 2.337464],
                    [75110,48.876029, 2.361113],
                    [75111,48.859415, 2.378731],
                    [75112,48.835154, 2.419818],
                    [75113,48.82872, 2.362471],
                    [75114,48.828994, 2.327104],
                    [75115,48.840155, 2.293563],
                    [75116,48.860397, 2.262102],
                    [75117,48.887337, 2.307486],
                    [75118,48.892735, 2.348712],
                    [75119,48.886869, 2.384696],
                    [75120,48.86318, 2.400816]], columns=['code_insee','latitude','longitude'])

"""

import sys
import argparse
import pandas
import numpy
import save_module
import networkx
import math

#filter functions______________________________________________________________

def paris(stri):
    stri=str(stri)
    if stri[0:2] == '75':
        return True
    else :
        return False

def grandParis(stri) :
  stri = str(stri)
  if (stri[0:2] in ['75', '92', '93', '94']) or stri in ['95018', '91645', '91479', '91027', '91326', '91589', '91687'] :
    return True
  else : 
    return False

#useful functions______________________________________________________________

verbose = 3
def vprint(stri,level):
    global verbose
    if verbose >= level:
        print(stri)

def find_min(lats, longs, latitude, longitude, dfNodes):
  distances = [(float(lats[i])-latitude)**2 + (float(longs[i])-longitude)**2 for i in range(len(lats))]
  return dfNodes['Id'].loc[numpy.argmin(distances)]

def find_min_specialcase(dfNodes, latitude, longitude):
    A = dfNodes["Latitude"].values
    B = dfNodes["Longitude"].values
    distances = [(float(A[i])-latitude)**2 + (float(B[i])-longitude)**2 for i in range(len(A))]
    ind = numpy.argsort(distances)
    return ind

def city_nodes(dfNodes, dfCoord):
    A = dfNodes["Latitude"].values
    B = dfNodes["Longitude"].values
    npCoord = dfCoord.values
    liste_commune=[]
    for i in range(len(npCoord)):
        liste_commune.append(find_min(A,B, float(npCoord[i,2]), float(npCoord[i,3]),dfNodes))
    return liste_commune

def travel_time(DataFrame, transport):
    #distance is in km, time in min
    if transport == 'car' or transport =='':
        DataFrame['time_travel_by_car'] = DataFrame['length_car']/18*60 # ~18km/h en moyenne en ville#travel_time_car(DataFrame, 0, simplified=True)
    if transport == 'motorcycle' or transport =='':
        DataFrame['time_travel_by_motorcycle'] = DataFrame['length_car']/25*60 # ~25km/h en moyenne en ville#travel_time_car(DataFrame, 0, simplified=True)
    if transport == 'bike' or transport =='':
        DataFrame['time_travel_by_bike'] = DataFrame['length_bike']/22*60 # ~22km/h cycling
    if transport == 'walk' or transport =='':
        DataFrame['time_travel_by_walk'] = DataFrame['length_pedestrian']/6*60 # ~6km/h walking
    return DataFrame

def travel_time_car(DataFrame, edges, simplified=False):
    if simplified :
        return [DataFrame['Distance']/18*60] # ~18km/h en moyenne en ville
    #??a va ??tre hyper long...
    else :
        edgeList = pandas.read_csv(edges).set_index(['source','target'])
        times = []
        for row in DataFrame.itertuples():
            time = 0
            path = row.path
            for i in range(len(path)-1):
                source, target = path[i], path[i+1]
                edge = edgeList.iloc[source, target]
                try :
                    time += edge.length/edge.maxspeed/60
                except AttributeError :
                    time += edge.length/50/60
            times.append(time)
        return times

def weights_building_f(length, boolean):
    if boolean :
        return length
    else :
        return math.inf

def weights_building(dfEdges):
    modes = ['car', 'bike', 'pedestrian']
    for mode in modes :
        dfEdges['length_'+ mode] = [weights_building_f(row[0],row[1]) for row in zip(dfEdges['length'],dfEdges[mode])]
    dfEdges['maxspeed'] = dfEdges['maxspeed'].replace({'walk': 10, 'FR:urban' : 50, 'FR:rural' : 80, 'FR:zone30' : 30, 'FR:motorway' : 130}).astype(float)
    dfEdges['time_car'] = dfEdges['length_car'].to_numpy()/(dfEdges['maxspeed'].fillna(50))*60
    return dfEdges    
            

#core__________________________________________________________________________
def main():
    """
    method to read the command line arguments and run the program
    """
    parser = argparse.ArgumentParser(\
             description='This script provides you paths from and to city centers',
             epilog="Have fun while usage; graphtoDijkstra.py -n nodes.csv -e edges.csv -c dt_idf_loc.csv -f grandParis -v2 -cn")
    #input selection
    parser.add_argument("-n", "--graphNodes", help='path to node list file')
    parser.add_argument("-e", "--graphEdges", help='path to edge list file')
    parser.add_argument("-c", "--cityCoord", help='path to coordinates of city centers file')
    #parser.add_argument("-f", "--filter", help="selects a subset of cities in the city-coord file", dest='cityFilter', action='store_true')
    parser.add_argument("-f", "--cityFilter", nargs='?', const='grandParis',
            help="selects a subset of cities in the city-coord file")
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3],
                                help="increase output verbosity")
    parser.add_argument("-cn", "--correctNodes", help="takes nodes raw input",
                            dest="correctNodes", action="store_true")
    args = parser.parse_args()

    global verbose
    verbose = args.verbosity
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
     
    correctNodes = args.correctNodes
    
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
    
    main_function(nodes_file, edges_file, coord_file, verbose, args.cityFilter, correctNodes)

def main_function(nodes_file, edges_file, coord_file, verbosity, cityFilter=False, correctNodes = True):
    vprint("Starting preprocessing...",2)
    global verbose
    verbose = verbosity
    # read files
    dfCoord = pandas.read_csv(coord_file)
    dfNodes = pandas.read_csv(nodes_file)
    dfEdges = pandas.read_csv(edges_file)                         
    
    if correctNodes:  
        vprint("Preprocessing: correcting the nodes and coord databases",2)
        # if there are too many useless nodes in the node list, a first filter
        dfNodes = pandas.DataFrame(dfEdges['source'].unique()).merge(dfNodes, 
                                  'left', left_on=0, right_on='Id')
        #we do not want a city to be represented by a node not accessible to one type of transport
        dfNodescities = pandas.DataFrame(dfEdges.loc[dfEdges['car'] & dfEdges['bike'] & dfEdges['pedestrian']]['source'].unique()).merge(dfNodes, 
                                  'left', left_on=0, right_on='Id')
        #dfNodes.to_csv('nodesShort.csv')
        vprint("Preprocessing: applying filter",2)
        # filtering the coordinates files if it covers a bigger region
        if cityFilter:
            if cityFilter == 'grandParis':
                dfCoord['selectionGP'] = [grandParis(x) for x in dfCoord['code_insee'].to_list()]
                dfCoord = dfCoord[['code_insee','latitude','longitude']].loc[dfCoord['selectionGP'] == True].reset_index()
                #dfCoord.to_csv('grandParis_coord.csv')          
            elif cityFilter == 'paris' :
                dfCoord['selection'] = [paris(x) for x in dfCoord['code_insee'].to_list()]
                dfCoord = dfCoord[['code_insee','latitude','longitude']].loc[dfCoord['selection'] == True].reset_index()
            else : 
                sys.exit("ERROR: this filter is not defined. Use 'grandParis', 'paris' or define it beforehand")
            # compute closest to node of the graph to each city center
            list_cities = city_nodes(dfNodescities, dfCoord)
            dfCoord['closest_node'] = list_cities
            dfCoord.to_csv('commune_node_codeINSEE.csv')
        
        #test: is it well related to the rest of the graph ?
        count = 0
        G = save_module.load_graph(edges_file)
        vprint("There are "+str(len(list_cities))+" nodes to check",3)
        for i in range(len(list_cities)):
            source_commune = dfCoord.at[i, 'closest_node']
            if count % 10 == 0 :
                vprint("Scanned "+str(count),3)
            dict_provisoire_length, dict_provisoire_path = networkx.algorithms.shortest_paths.weighted.single_source_dijkstra(G, source_commune, weight='length')
            if len(set(list_cities).intersection(dict_provisoire_length.keys()))<len(list_cities)*0.8:   #we expect less than 20% of non connected nodes
                vprint(str(source_commune) + " is not connected to the rest of the graph, looking for another node",2)
                candidates = find_min_specialcase(dfNodes,float(dfCoord.at[i,"latitude"]), float(dfCoord.at[i,"longitude"]) )
                j=0
                while len(set(list_cities).intersection(dict_provisoire_length.keys())) < len(list_cities)*0.8 and j<100:
                    j += 1
                    candidate = dfNodes['Id'].loc[candidates[j]]
                    dict_provisoire_length = networkx.algorithms.shortest_paths.weighted.single_source_dijkstra(G, candidate, weight='length')[0]
                dfCoord.at[i,'closest_node'] = candidate
                source_commune = candidate
                vprint("New node found : "+ str( candidate),2)
            count += 1
        dfCoord.to_csv('commune_node_codeINSEE.csv')
        vprint("Preprocessing done, next time call commune_node_codeINSEE.csv as dfCoord and drop the -cn",2)
    
    list_cities = dfCoord['closest_node'].to_list()
    # graph theory computations
    vprint("Starting path optimization...",2)
    dfEdges = weights_building(dfEdges)
    G = networkx.convert_matrix.from_pandas_edgelist(dfEdges, source='source', target='target', edge_attr=True, create_using=networkx.DiGraph())
    weights = ['length_car', 'length_bike', 'length_pedestrian', 'time_car']
    dictionnary = {}
    count = 1
    vprint("There are "+str(len(list_cities))+" cities to look at",3)
    for i in range(len(list_cities)):
        source_commune = dfCoord.at[i, 'closest_node']
        if count % 10 == 0 :
            vprint("Done "+str(count),3)
        for weight in weights :
            dict_provisoire_length, dict_provisoire_path = networkx.algorithms.shortest_paths.weighted.single_source_dijkstra(G, source_commune, weight=weight)
            for commune in set(list_cities).intersection(dict_provisoire_length.keys()):
                dictionnary[(source_commune, commune, weight)] = dict_provisoire_length[commune], dict_provisoire_path[commune]
        count += 1
    
    #Minimal postprocessing
    vprint("Postprocessing: adding city tags in database...",2)
    df_result = pandas.DataFrame(dictionnary).transpose()
    df_result.to_csv('OUTPUT_distances_paths_cities.csv')
    df_result = pandas.read_csv('OUTPUT_distances_paths_cities.csv')
    df_result.columns=['source','target','weight','distance','path']
    result_complete = df_result.merge(dfCoord[['closest_node','code_insee']],'left', left_on='source', right_on='closest_node')
    result_complete.columns = ['source', 'target', 'weight', 'distance', 'path','argmin','code_insee_source']
    result_complete = result_complete[['source', 'target', 'weight', 'distance', 'path','code_insee_source']].merge(
            dfCoord[['closest_node','code_insee']],'left', left_on='target', right_on='closest_node')
    result_complete = result_complete[['source', 'target', 'weight', 'distance', 'path','code_insee_source','code_insee']]
    result_complete.columns = ['source', 'target', 'weight', 'distance', 'path','code_insee_source','code_insee_target']
    #the end
    vprint("Computations finished, saving to csv file",2)
    result_complete.to_csv('OUTPUT_distances_paths_cities.csv') 
    vprint("Work done, good bye !",2)

if __name__ == '__main__':
    main()
    