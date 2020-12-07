# -*- coding: utf-8 -*-
"""
Created on Mon Dec 7 09:45:49 2020

@author: Sancho, Martin, Edwin
"""

import networkx as nx
import ndlib.models.ModelConfig as mc
from emojiset_app.epidemiology.MultipleMajority import MultipleMajority
from bokeh.io import show, output_file, save
from ndlib.viz.bokeh.DiffusionTrend import DiffusionTrend
#rom bs4 import BeautifulSoup
from emojiset_app.utils import debug
from bs4 import BeautifulSoup
import codecs

#Network Topology
#graph = nx.erdos_renyi_graph(1000, .8)
#graph = nx.dense_gnm_random_graph(1000, 5000)
graph = nx.watts_strogatz_graph(1000, 5, .2)
#graph = nx.random_regular_graph(5, 1000)
#graph = nx.barabasi_albert_graph(1000, 5)
#graph = nx.powerlaw_cluster_graph(1000, 5, 0.2)
#graph = nx.duplication_divergence_graph(1000, 0.2)
#model selection

def MMR(bias ,fraction_Adopter, fraction_Rejector, Q):
    denom = bias;
    model = MultipleMajority(graph, denom)
    
    config = mc.Configuration()
    config.add_model_parameter('fraction_Adopter', fraction_Adopter)
    config.add_model_parameter('fraction_Rejector', fraction_Rejector)
    config.add_model_parameter("q", Q)
    model.set_initial_status(config)
    
    #Simulation execution
    iterations = model.iteration_bunch(1000)
    trends = model.build_trends(iterations)
    
    viz = DiffusionTrend(model, trends)
    p = viz.plot(width=500, height=500)
    output_file("mmr.html")
    save(p)

    f = open("mmr.html", "r")
    document = f.read()
    soup = BeautifulSoup(document, 'html.parser')
    plot = str(soup.find('body')).replace('<body>', "").replace("</body>", "")
    return plot
