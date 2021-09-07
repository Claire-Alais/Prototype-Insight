# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 14:10:45 2021

@author: clair

/!\ some lines tailored for Grand Paris (but explicit)


# La base de donnée habitudes de transports du Grand Paris croise 
#la durée de  déplacement et les modes de transports utilisés pour 
#les trajets domicile-travail, elle est obtenue comme suit :

statistiques_mode = np.array([2098 / sum([2098, 2628, 137, 228, 15, 570]),
                              2628 / sum([2098, 2628, 137, 228, 15, 570]),
                              137 / sum([2098, 2628, 137, 228, 15, 570]),
                              228 / sum([2098, 2628, 137, 228, 15, 570]),
                              15 / sum([2098, 2628, 137, 228, 15, 570]),
                              570 / sum([2098, 2628, 137, 228, 15, 570])])
#voiture, transports co, deux-roues motorisés, vélos, autres modes motorisés, marche
#TOTAL des déplacements en milliers : 5 313 pour domicile-travail, Ile-de-France

matrice_transport_duree = np.array([[0.56, 0.27, 0.13, 0.04],   #voiture
                                    [0.08, 0.31, 0.40, 0.21],   #transports collectifs
                                    [0.41, 0.37, 0.20, 0.02],   #deux-roues motorisés
                                    [0.63, 0.25, 0.10, 0.01],   #vélo
                                    [0.28, 0.38, 0.16, 0.18],   #autres modes motorisés
                                    [0.84, 0.12, 0.03, 0.01],   #marche
          ])  #classes de durées : <15, 16 à 30, 31 à 60, >=61 minutes
#source : Enquête globale transport, résultats provisoires 2018, 
#Flux de déplacements pour motif "Domicile-Travail" tous modes 
#Nombre de déplacements par jour et par personne de 6 ans et plus (en milliers) (p14)
#
#Durée des déplacements Répartition des durées selon le mode de transport (p23)
#classes de durées : <15, 16 à 30, 31 à 60, >=61 minutes

matrice_duree_transport =  matrice_transport_duree * statistiques_mode


"""
import sys
import argparse
import pandas
import graphtoDijkstra
import numpy



#résultat pour les habitudes de transport Grand Paris :
habits_grandParis = numpy.array([[0.20699084, 0.09979915, 0.04805144, 0.01478506],   #voiture
                                 [0.03704017, 0.14353066, 0.18520085, 0.09723044],   #transports collectifs
                                 [0.00989605, 0.00893058, 0.00482734, 0.00048273],   #deux-roues motorisés
                                 [0.02530655, 0.01004228, 0.00401691, 0.00040169],   #vélo
                                 [0.00073996, 0.00100423, 0.00042283, 0.00047569],   #autres modes motorisés
                                 [0.08435518, 0.01205074, 0.00301268, 0.00100423]    #marche
                                 ]) 
 #                                  1 à 15      16 à 30     31 à 60   61+ minutes
 

verbose = 2
def vprint(stri,level):
    global verbose
    if verbose >= level:
        print(stri)

def grandParis(stri) :
    stri = str(stri)
    if (stri[0:2] in ['75', '92', '93', '94']) or stri in ['95018', '91645', '91479', '91027', '91326', '91589', '91687'] :
        return True
    else : 
        return False

def time_category (time_travel):
    if time_travel < 16:
        return 0
    if time_travel < 31:
        return 1
    if time_travel < 61:
        return 2
    return 3

def run_simulation(thresholds, categories, value):   #tower sampling
    for i in range(len(thresholds)-1) :
        if value <= thresholds[i] :
            return categories[i]
    return categories[-1]

def choice_of_a_mode_of_transport(row, habits, include_common_transport=False):  
    categories = ['car', 'motorcycle', 'bike', 'walk']
    probabilities = [ habits[0, time_category(row[0])], 
                      habits[2, time_category(row[1])],
                      habits[3, time_category(row[2])],
                      habits[4, time_category(row[3])] ]
    if include_common_transport:
        categories.append('public_transport')
        probabilities.append(habits[1, time_category(row[4])])   
    tot_chance = sum(probabilities)
    probabilities = numpy.array(probabilities)/tot_chance
    thresholds = numpy.array([sum(probabilities[0:i]) for i in range(len(probabilities))]) #for tower sampling
    return thresholds

def multi_run_simulation(DataFrame, habits, n=1000, include_common_transport = False):
    vprint("Multirun simulations...",1)
    column_selection = ['time_travel_by_car', 'time_travel_by_motorcycle',
                               'time_travel_by_bike','time_travel_by_walk']
    categories = ['car', 'motorcycle', 'bike', 'walk']
    if include_common_transport :
        column_selection.append('time_travel_by_public_transport')
        categories.append('public_transport')
    for i in range(n):
        DataFrame['thresholds'] = [choice_of_a_mode_of_transport(row, habits, include_common_transport) for row 
                 in DataFrame[column_selection].to_numpy()]     
        DataFrame["run_" + str(i + 1) + "_results"] = run_simulation(DataFrame["thresholds"].values, 
                  categories, numpy.random.uniform(0,1,len(DataFrame)))
    return(DataFrame)

def main():
    parser = argparse.ArgumentParser(\
             description='Multiruns from the paths and distance dataframe and probabilities',
             epilog="Have fun while usage; multirun.py -f path_dist_code_insee.csv -v 2 -a dt_base_final.csv -s stat.csv -p 0.8 -n 5 -o output_test.csv")
    #input selection
    parser.add_argument('-f','--filename','--file', help='the path to a file for paths in graph')
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3], help="increase output verbosity")
    parser.add_argument('-a', '--agent-population', help='the path to a file for synthetic population')
    parser.add_argument('-s', '--statistics', help='the path to a file for transport habits')
    parser.add_argument('-p', '--proportion-work', nargs='?', const=0.8, help='proportion of workers actually commuting on a given day')
    parser.add_argument('-n', '--nb_simulations', nargs='?', const=1000, help='number of run of simulations')
    parser.add_argument("-o", "--output", nargs='?', const='multisimulation_output.csv',
            help="name of the ouput file, with .csv")
    args = parser.parse_args()

    global verbose
    verbose = args.verbosity
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    paths = args.filename
    population = args.agent_population
    habits = args.statistics
    proportion = args.proportion_work
    n = args.nb_simulations
    output = args.output
    
    main_function(paths, population, habits, proportion, n, output, verbose)


#if we want to use the traditional way of calling functions
def main_function(paths, population, habits, proportion, n, output, verbose=verbose):
    # construction of the distribution to match
    vprint("Preprocessing...",1)
    # case by case preprocessing
    habits = habits_grandParis #habits[transport mode, time category] 
    # filtre Grand Paris
    vprint("Preprocessing: Filtering",2)
    df_synthPop = pandas.read_csv(population)
    df_synthPop['selectionGP'] = [grandParis(x[0]) and grandParis(x[1]) for x in df_synthPop[['codgeo', 'codgeo_travail']].to_numpy()]
    df_synthPop = df_synthPop.loc[df_synthPop['selectionGP'] == True].reset_index().drop(columns=['selectionGP'])
    # appariement base individuelle/ base déplacement -> distance, *liste vitesses
    vprint("Preprocessing: Database matching",2)
    df_trajectories = pandas.read_csv(paths)
    df_simul = df_synthPop.merge(df_trajectories[['distance','code_insee_source','code_insee_target']], 
                                'left', 
                                left_on = ['codgeo','codgeo_travail'], 
                                right_on = ['code_insee_source','code_insee_target'])
    vprint('Temporary output saved, will be replaced by the proper output at the end, for trouble shooting',1)
    df_simul.to_csv(output)
    vprint("Preprocessing: Travel time computation",2)
    df_simul = graphtoDijkstra.travel_time(df_simul, '') #syntax will change when travel_time is refined
    vprint("Preprocessing done !",1)
    # multirun transport choices
    df_simul_out = multi_run_simulation(df_simul, habits, n)
    vprint("Multirun simulations done! Saving output to csv file...",1)
    df_simul_out.to_csv(output)
    vprint("Work done, good bye !",1)
    
        


if __name__ == '__main__':
    main()