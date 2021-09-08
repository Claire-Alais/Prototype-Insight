# Prototype-Insight
prototype pour l'Ile de France<br/>
Claire et Mathis<br/>

## Partie population synthétique
Voir le notebook colab

## Partie géographique
graphtoFW.py ne fonctionnera que pour de très petites 
régions pour des questions de mémoire vive<br/>

Usage console python (Spyder par exemple): <br/>
run graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

Usage invite de commandes:<br/>
python graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

Pour une grande ville, on génère d'abord le réseau avec<br/>
python OSMtoGraph.py -f map.osm -v 2 -t "hw" -e "edges.csv" -n "nodes.csv"<br/>
On lui fournit : le fichier OSM découpé à la bonne région, <br/>
deux noms de fichiers pour y stocker le graphe (listes des noeuds et des arcs),<br/>
l'option -t "hw" indique qu'on ne prend en compte que les routes,<br/> 
pas les voies ferrées ni les lignes de transport en commun,<br/>
l'option -v 0 ne génère aucune sortie pendant le calcul, avec -v entre 1 et 3 <br/> 
des informations sur le déroulement du calcul s'affichent avec plus ou moins de détails.<br/> 


Puis on regarde les itinéraires qui relient les centre villes entre eux avec<br/>
python graphtoDijkstra.py -n nodes.csv -e edges.csv -c dt_idf_loc.csv -f "grandParis" -v3 -cn<br/>
On lui fournit : -n et -e les fichiers listes de noeuds et arcs issus du script précédent, <br/> 
-c les coordonnées des barycentres des zones d'intérêt (ici les communes du Grand Paris<br/> 
avec un découpage de Paris par arrondissements)<br/> 
-f le nom d'un filtre (si le fichier -c contient plus de coordonnées que ce qui nous intéresse),<br/> 
paris ou grandParis sont codés, pour autre il faut l'ajouter dans le script<br/> 
La première partie consiste à associer un noeud du graphe à chaque barycentre du fichier -c<br/> 
c'est une partie qui prend du temps car on vérifie que le noeud en question <br/> 
est bien relié au réseau par tous les moyens de transport (pas le bout d'une impasse piétonne ou une <br/> 
allée interne à un bâtiment. Elle est réalisée si l'option -cn est précisée, mais si elle a <br/> 
déjà été réalisée avec succès auparavant un fichier de correspondance entre les barycentres <br/> 
et les noueds a été généré, peut être donné en argument de -c, dans ce cas on ne laisse pas -cn<br/> 
et le calcul passe directement à l'étape suivante.<br/> 
Ce calcul est fini quand deux fichiers sont enregistrés : celui qui permet de court-circuiter<br/> 
la première étape et la base de données des trajets optimaux selon le point de départ, <br/> 
celui d'arrivée, la méthode d'optimisation et le mode de transport.<br/> 
Par défaut (voir dans le code) les deux fichiers s'appellent respectivement<br/> 
commune_node_codeINSEE.csv et distances_paths_cities.csv.<br/> 

## Partie simulations

Les individus de la population synthétique sont appariés à leurs trajets <br/> 
possibles sur la base de leur lieu de résidence et de ler lieu de travail.<br/> 
Des probabilités de choisir un mode de transport particulier pour chaque <br/> 
trajet et individu sont calculées à partir des données de l'enquête transport.<br/> 
Une série de tirages est effectuée.<br/> 
Usage :<br/> 
python multirun.py -f distances_paths_cities.csv -a dt_base_final.csv -s stat.csv -p1 -n5 -o output_test.csv -v3 <br/>
avec -f la sortie de graphtoDijkstra, -a la sortie de la partie population, <br/>
-s un fichier de statistiques d'habitudes de transport (croisement mode de transport et durée de déplacement)<br/>
-p la proportion de travailleurs qui vont vraiment se déplacer au travail (inutilisé pour l'instant)<br/>
L'INSEE indique qu'en moyenne un jour de semaine 80% des travailleurs se déplacent sur leur lieu de travail,<br/>
les autres étant en congés, malades, en télétravail, ne travaillant qu'à temps partiel...<br/>
-n le nombre de simulations (tirages) à faire<br/>
-o le nom du fichier de sortie finale
