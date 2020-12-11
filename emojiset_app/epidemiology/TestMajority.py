# -*- coding: utf-8 -*-
"""
Created on Mon Dec 7 09:45:49 2020

@author: Sancho, Martin, Edwin
"""

def MMR(bias, fraction_Adopter, fraction_Rejector, Q):
    import networkx as nx
    import ndlib.models.ModelConfig as mc
    from emojiset_app.epidemiology.MultipleMajority import MultipleMajority
    from bokeh.io import show, output_file, save
    from ndlib.viz.bokeh.DiffusionTrend import DiffusionTrend
    from emojiset_app.utils import debug
    from bs4 import BeautifulSoup
    import codecs
    from bokeh.embed import file_html
    from bokeh.resources import CDN

    graph = nx.watts_strogatz_graph(1000, 5, .2)
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
    document = file_html(p, CDN)
    soup = BeautifulSoup(document, 'html.parser')
    plot = str(soup.find('body')).replace('<body>', '').replace("</body>", "")
    return plot
