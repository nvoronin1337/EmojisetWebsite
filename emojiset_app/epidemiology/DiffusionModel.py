# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 09:06:30 2020

@author: mooreheadj
"""

import abc
import warnings
import numpy as np
import past.builtins
import future.utils
import six
import networkx as nx
import tqdm

__author__ = "Joshua Moorehead"
__email__ = "mooreheadj@wit.edu"

class ConfigurationException(Exception):
    """Configuration Exception"""

@six.add_metaclass(abc.ABCMeta)
class DiffusionModel(object):
    """
    Partial Abstract class that defines Diffusion Models
    """
    #__metaclass__ = abc.ABCMeta
    def __init__(self, graph, seed=None):
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
        np.random.seed(seed)
        self.discrete_state = True
        self.params = {
            'nodes': {},
            'edges': {},
            'model':{},
            'status':{}
        }
        
        self.available_statuses = {
            "Susceptible": 0,
            "Adopter": 1,
            "Rejector": 2
        }
        
        self.name = ""
        
        self.parameters = {
            "model": {},
            "nodes": {},
            "edges": {}
        }
        
        self.actual_iteration = 0
        self.graph = nx.Graph(graph)
        self.status = {n: 0 for n in self.graph.nodes}
        self.initial_status = {}
    
    def __validate_configuration(self, configuration):
        """
        Validate the consistancy of a configuration object for the specific model
        :param configuration: a Configuration object instance
        """
        if "Adopter" not in self.available_statuses:
            raise ConfigurationException("Adopter status not defined.")
        
        if "Rejector" not in self.available_statuses:
            raise ConfigurationException("Rejector status not defined.")
        
        #checking mandatory parameters
        omp = set([k for k in self.parameters['model'].keys() if self.parameters['model'][k]['optional']])
        onp = set([k for k in self.parameters['nodes'].keys() if self.parameters['nodes'][k]['optional']])
        oep = set([k for k in self.parameters['edges'].keys() if self.parameters['edges'][k]['optional']])
        
        mdp = set(configuration.get_model_parameters().keys())
        ndp = set(configuration.get_nodes_configuration().keys())
        edp = set(configuration.get_edges_configuration().keys())
        
        if len(omp) > 0:
            for param in omp:
                if param not in mdp:
                    configuration.add_model_parameter(param, self.parameters['model'][param]['default'])
        
        if len(onp) > 0:
            for param in onp:
                if param not in ndp:
                    for nid in self.graph.nodes:
                        configuration.add_model_parameter(param, nid, self.parameters['nodes'][param]['default'])
        
        if len(oep) > 0:
            for param in oep:
                if param not in edp:
                    for eid in self.graph.edges:
                        configuration.add_edge_configuration(param, eid, self.parameters['edges'][param]['default'])
        
        #checking initial simulation status
        sts = set(configuration.get_model_configuration().keys())
        if self.discrete_state and "Adopter" not in sts and "fraction_Adopter" not in mdp \
            and "percentage_Adopter" not in mdp:
                warnings.warn("Initial statuses missing: a random sample of 5% of graph nodes will be set as adopters")
                self.params['model']["fraction_Adopter"] = 0.05
        
        if self.discrete_state and "Rejector" not in sts and "fraction_Rejector" not in mdp \
            and "percentage_Rejector" not in mdp:
                warnings.warn("Initial statuses missing: a random sample of 5% of graph nodes will be set as rejectors")
                self.params['model']["fraction_Rejector"] = 0.05
    
    def set_initial_status(self, configuration):
        
        self.__validate_configuration(configuration)
        nodes_cfg = configuration.get_nodes_configuration()
        
        #set aditional node information
        
        for param, node_to_value in future.utils.iteritems(nodes_cfg):
            if len(node_to_value) < len(self.graph.nodes):
                raise ConfigurationException({"message": "Not all nodes have a configuration specified"})
            
            self.params['nodes'][param] = node_to_value
        
        edges_cfg = configuration.get_edges_configuration()
        #set aditional edges information
        for param, edge_to_values in future.utils.iteritems(edges_cfg):
            if len(edge_to_values) == len(self.graph.edges):
                self.params['edges'][param]={}
                for e in edge_to_values:
                    self.params['edges'][param][e] = edge_to_values[e]
        
        #set initial status
        model_status = configuration.get_model_configuration()
        
        for param, nodes in future.utils.iteritems(model_status):
            self.params['status'][param] = nodes
            for node in nodes:
                self.status[node] = self.available_statuses[param]
        
        #set aditional information
        model_params = configuration.get_model_parameters()
        for param, val in future.utils.iteritems(model_params):
            self.params['model'][param] = val
        
        #handle initial infection
        if'Adopter' not in self.params['status']:
            if 'percentage_Adopter' in self.params['model']:
                self.params['model']['fraction_Adopter'] == self.params['model']['percentage_Adopter']
            if 'fraction_Adopter' in self.params['model']:
                number_of_initial_Adopter = self.graph.number_of_nodes() * float(self.params['model']['fraction_Adopter'])
                if number_of_initial_Adopter < 1:
                    warnings.warn(
                        "The fraction_Adopter value is too low given the number of nodes of the selected graph: a "
                        "single node will be set as Adopter")
                    number_of_initial_Adopter = 1
                
                available_nodes = [n for n in self.status if self.status[n] == 0]
                sampled_nodes = np.random.choice(available_nodes, int(number_of_initial_Adopter), replace = False)
                for k in sampled_nodes:
                    self.status[k] = self.available_statuses['Adopter']
        
        if'Rejector' not in self.params['status']:
            if 'percentage_Rejector' in self.params['model']:
                self.params['model']['fraction_Rejector'] == self.params['model']['percentage_Rejector']
            if 'fraction_Rejector' in self.params['model']:
                number_of_initial_Rejector = self.graph.number_of_nodes() * float(self.params['model']['fraction_Rejector'])
                if number_of_initial_Rejector < 1:
                    warnings.warn(
                        "The fraction_Rejector value is too low given the number of nodes of the selected graph: a "
                        "single node will be set as Rejector")
                    number_of_initial_Adopter = 1
                
                available_nodes = [n for n in self.status if self.status[n] == 0]
                sampled_nodes = np.random.choice(available_nodes, int(number_of_initial_Rejector), replace = False)
                for k in sampled_nodes:
                    self.status[k] = self.available_statuses['Rejector']
        
        self.initial_status = self.status
    
    def clean_initial_status(self, valid_status = None):
        """
        Check the consistancy of initial status
        """
        for n, s in future.utils.iteritems(self.status):
            if s not in valid_status:
                self.status[n] = 0
    
    def iteration_bunch(self, bunch_size, node_status=True):
        """
        """
        system_status = []
        for it in tqdm.tqdm(past.builtins.xrange(0, bunch_size)):
            its = self.iteration(node_status)
            system_status.append(its)
        return system_status
    
    def get_info(self):
        """
        """
        info = {k: v for k, v in future.utils.iteritems(self.params) if k not in ['nodes', 'edges', 'status']}
        if 'Adopter_nodes' in self.params['status']:
            info['selected_initial_Adopter'] = True
        return info['model']
    
    def reset(self, Adopter_nodes=None, Rejector_nodes = None):
        """
        """
        self.actual_iteration = 0
        if Adopter_nodes is not None or Rejector_nodes is not None:
            for n in self.status:
                self.status[n] = 0
            for n in Adopter_nodes:
                self.status[n] = self.available_statuses['Adopter']
            for n in Rejector_nodes:
                self.status[n] = self.available_statuses['Rejector']
            self.initial_status = self.status
        
        else:
            if 'percentage_Adopter' in self.params['model']:
                self.params['model']['fraction_Adopter'] = self.params['model']['percentage_Adopter']
            if 'percentage_Rejector' in self.params['model']:
                self.params['model']['fraction_Rejector'] = self.params['model']['percentage_Rejector']
            if 'fraction_Adopter' in self.params['model']:
                for n in self.status:
                    self.status[n] = 0
                number_of_initial_Adopter = self.graph.number_of_nodes() * float(self.params['model']['fraction_Adopter'])
                number_of_initial_Rejector = self.graph.number_of_nodes() * float(self.params['model']['fraction_Rejector'])
                available_nodes = [n for n in self.status if self.status[n] == 0]
                sampled_nodesA = np.random.choice(available_nodes, int(number_of_initial_Adopter), replace = False)
                sampled_nodesR = np.random.choice(available_nodes, int(number_of_initial_Rejector), replace = False)
                
                for k in sampled_nodesA:
                    self.status[k] = self.available_statuses['Adopter']
                for k in sampled_nodesR:
                    self.status[k] = self.available_statuses['Rejector']
                self.initial_status = self.status
            else:
                self.status = self.initial_status
        return self
    
    def get_model_parameters(self):
        return self.parameters
    def get_name(self):
        return self.name
    
    def get_status_map(self):
        return self.available_statuses
    
    @abc.abstractmethod
    def iteration(self, node_status = True):
        pass
    
    @staticmethod
    def check_status_similarity(actual, previous):
        for n, v in future.utils.iteritems(actual):
            if n not in previous:
                return False
            if previous[n] != actual[n]:
                return False
        return True
    
    def status_delta(self, actual_status):
        """
        """
        actual_status_count = {}
        old_status_count = {}
        delta = {}
        for n, v in future.utils.iteritems(self.status):
            if v!= actual_status[n]:
                delta[n] = actual_status[n]
        
        for st in self.available_statuses.values():
            actual_status_count[st] = len([x for x in actual_status if actual_status[x] == st])
            old_status_count[st] = len([x for x in self.status if self.status[x] == st])
            
        status_delta = {st: actual_status_count[st] - old_status_count[st] for st in actual_status_count}
        
        return delta, actual_status_count, status_delta
    
    def build_trends(self, iterations):
        """
        """
        status_delta = {status: [] for status in self.available_statuses.values()}
        node_count = {status: [] for status in self.available_statuses.values()}
        
        for it in iterations:
            for st in self.available_statuses.values():
                try:
                    status_delta[st].append(it['status_delta'][st])
                    node_count[st].append(it['node_count'][st])
                except:
                    status_delta[st].append(it['status_delta'][str(st)])
                    node_count[st].append(it['node_count'][str(st)])
        
        return[{"trends": {"node_count": node_count, "status_delta": status_delta }}]