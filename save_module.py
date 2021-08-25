# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 14:29:16 2021

@author: clair

allows to save networkx graphs in csv files
"""

import pandas as pd  
import networkx  
    
def save_graph(graph, name):
    Gpanda = networkx.convert_matrix.to_pandas_edgelist(graph, edge_key='edgeKey')
    Gpanda.to_csv(name + '.csv')
    
def load_graph(name):
    Gpanda = pd.read_csv(name)
    return networkx.convert_matrix.from_pandas_edgelist(Gpanda, source='source', target='target', edge_attr=True)