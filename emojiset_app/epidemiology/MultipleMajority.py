# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 09:02:03 2020

@author: mooreheadj
"""


from emojiset_app.epidemiology.DiffusionModel import DiffusionModel


__author__ = "Joshua Moorehead"
__email__ = "mooreheadj@wit.edu"

class MultipleMajority(DiffusionModel):
    """
    """
   
    
    

    def __init__(self, graph, denom, seed = None):
        """
        Parameters
        ----------
        graph : TYPE
            DESCRIPTION.
        seed : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        super(self.__class__, self).__init__(graph, seed)
        self.available_statuses = {
            "Undecided": 0,
            "Adopter": 1,
            "Rejector": 2,
            }
        self.parameters = {"model": {
            "q": {
                "descr": "Number of randomly chosen voters",
                "range": [0, len(self.graph.nodes)],
                "optional": False
            }
        },
            "nodes": {},
            "edges": {}
        }
        
        self.name = "Multiple Majority"
        self.opinion_Change = denom
        if denom >= 0.0:
            self.opinion_Change = denom
        else:
            self.opinion_Change = 0.5
    
    def iteration(self, node_status=True):
        """

        Parameters
        ----------
        node_status : TYPE, optional
            DESCRIPTION. The default is True.

        Returns
        -------
        None.

        """
        import numpy as np
        import random
        self.clean_initial_status(list(self.available_statuses.values()))
        
        if self.actual_iteration == 0:
            self.actual_iteration += 1
            delta, node_count, status_delta = self.status_delta(self.status)
            if node_status:
                return{"iteration":0, "status":self.status.copy(),
                       "node_count":node_count.copy(), "status_delta":status_delta.copy()}
            else:
                return{"iteration":0, "status":{},
                       "node_count":node_count.copy(), "status_delta":status_delta.copy()}
            
        
        #select q random nodes
        discussion_group = [list(self.graph.nodes)[i]
                            for i in np.random.randint(0, self.graph.number_of_nodes(), self.params['model']['q'])]
       
        #compute majority
        majority_vote = 1
        accept_sum = 0
        reject_sum = 0
        bias = round(random.uniform(0.0, 1.0),2)
        for node in discussion_group:
            if self.status[node] == 1:
                accept_sum += 1
            elif self.status[node] == 2:
                reject_sum += 1
        if(accept_sum == reject_sum):
            if(bias <= self.opinion_Change): 
                majority_vote = 1
            else:
                majority_vote = 2
        elif max(accept_sum, reject_sum) == accept_sum:
            majority_vote = 1
        elif max(accept_sum, reject_sum) == reject_sum:
            majority_vote = 2
        else:
            majority_vote = 0
		
		#update status of nodes in discussion group
        delta = {}
        status_delta = {st: 0 for st in self.available_statuses.values()}

        
        for listener in discussion_group:
            if majority_vote != self.status[listener]:
                delta[listener] = majority_vote

                status_delta[self.status[listener]] += 1
                for x in list(self.available_statuses.values()):
                    if x != self.status[listener]:
                        status_delta[x] -= 1

            self.status[listener] = majority_vote
            
        
        #fix
        node_count = {st: len([n for n in self.status if self.status[n] == st])
                      for st in self.available_statuses.values()}
        self.actual_iteration += 1
        
        if node_status:
            return{"iteration":self.actual_iteration - 1, "status":delta.copy(),
                   "node_count": node_count.copy(), "status_delta": status_delta.copy()}
        else:
            return{"iteration":self.actual_iteration - 1, "status":{},
                   "node_count":node_count.copy(), "status_delta":status_delta.copy()}
        