# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 14:29:16 2021

@author: clair

/!\  /!\  /!\
allows to save networkx graphs but safety problems due to unpickling part
(unpickling a file that has been tampered with coul provoke running an unkown script)
I keep pickle for now as it is the simplest, but another solution is to be found.
networkx.readwrite.json_graph.node_link_data / networkx.readwrite.json_graph.node_link_graph seems promising for graphs
"""

import pickle


def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)