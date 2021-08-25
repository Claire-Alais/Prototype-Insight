# Prototype-Insight
prototype pour l'Ile de France<br/>
Claire et Mathis<br/>

## Partie géographique
graphtoFW.py ne fonctionnera que pour de très petites 
régions pour des questions de mémoire vive<br/>

Usage console python (Spyder par exemple): <br/>
run graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

Usage invite de commandes:<br/>
python graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

Pour une grande ville, on génère d'abord le réseau avec<br/>
python OSMtoGraph.py -f map.osm -v 2 -t "hw" -e "edges.csv" -n "nodes.csv"<br/>

Puis on regarde les itinéraires qui relient les centre villes entre eux avec<br/>
python graphtoDijkstra.py -n nodes.csv -e edges.csv -c dt_idf_loc.csv -f "grandParis" -v 3<br/>



## A faire
Le script de base ne gérait pas bien les trams apparemment,
il faut revoir ce qui se passe avec -t "all"<br/>

