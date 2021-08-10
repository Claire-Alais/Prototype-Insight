# Prototype-Insight
prototype pour l'Ile de France<br/>
Claire et Mathis<br/>

## Partie géographique
La meilleure manière à ce jour est de faire un run de 
graphtoFW.py en lui donnant un fichier osm, parce que la 
sauvegarde du réseau (pour l'instant avec pickle, qui 
n'est déjà pas un bon choix) ne fonctionne pas bien.<br/>

Usage console python (Spyder par exemple): <br/>
run graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

Usage invite de commandes:<br/>
python graphtoFW.py -f map.osm -o -v 2 -t "hw"<br/>

## A faire
Le script de base ne gérait pas bien les trams apparemment,
il faut revoir ce qui se passe avec -t "all"<br/>
Pickle n'est pas une bonne solution: ça fonctionne mal et 
ça pose des problèmes de sécurité (save_module.py)

