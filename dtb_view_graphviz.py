#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DTB to graphviz

@author: Florent Tomasin <florenttomasn@orange.fr>
"""

import argparse
import json
import random
from graphviz import Graph
from nested_lookup import nested_lookup
from pyfdt.pyfdt import FdtBlobParse

####################################
#    Global Definitions
####################################
hidden_dict = ['aliases', 'chosen', 'uboot', 'prouct', 'platform', 'target', ]

####################################
#    Functions Definitions
####################################
def rand_color():
    """
    Generate random hex color
    """
    r = lambda : random.randint(35,220)
    return ('#%02X%02X%02X' % (r(),r(),r()))

"""
Check functions:
    - check_device_type(_json_data)
    - check_dict_child(_json_data)
    - check_status(_json_data, _graph)
"""
def check_device_type(_json_data):
    """
    Function to return the node device type
    """
    if 'device_type' in _json_data:
        return True
    
    return False

def check_dict_child(_json_data):
    """
    Determine if a dict as dict child
    """
    nb_child = 0
    for test_dict in _json_data:
        if type(_json_data[test_dict]) is dict:
            nb_child += 1
    return nb_child

def check_hidden(_dict_name):
    """
    Function to check if a node has to be hidden
    """
    if _dict_name in hidden_dict:
       return False
    return True

def check_status(_json_data, _graph):
    """
    Function to change block color if disabled
    """
    if 'status' in _json_data:
        if _json_data['status'][1] == 'disabled':
            return False
    return True

"""
Draw functions:
    - draw_clusters(_json_data, _graph)
    - draw_edges(_json_data, _device_type)

"""
def draw_clusters(_json_data, _graph):
    """
    Function to generate cluster in cluster graph based
    on DOT language.
    """
    sub_graph = None
    
    if type(_json_data) is dict:
        for dict_name in _json_data:
            if check_hidden(dict_name):
                if check_status(_json_data, _graph):
                    if type(_json_data[dict_name]) is dict:

                        # determine if a dict as dict child
                        # if the dict include other dict, it is a cluster        
                        if check_dict_child(_json_data[dict_name]):
                            sub_graph = Graph('cluster_' + dict_name)
                            sub_graph.attr(label     = '<<B>' + dict_name + '</B>>',
                                           color     = 'black',
                                           style     = 'filled',
                                           #~ ranktype  = 'min',
                                           #~ rankdir   = 'TB',
                                           fillcolor = rand_color())
                            
                            draw_clusters(_json_data = _json_data[dict_name],
                                          _graph     = sub_graph)

                            _graph.subgraph(sub_graph)

                        # if the dict as no child, it is a node
                        else:
                            _graph.attr('node', shape='record') # shape='box'
                            _graph.node(dict_name)
    return 0

def draw_edges(_json_data, _dict_name, _graph):
    """
    Function to find common node or cluster name graph based
    on DOT language.
    """
    find_common = nested_lookup(_dict_name,
                                _json_data,
                                wild      = True,
                                with_keys = True)
    for i in find_common:
        if check_hidden(find_common[i]):              # Continu only if the element has to be drawn
            if check_status(find_common[i], _graph):  # Continu only if the element is active
                if _dict_name in i:                   # Test link between element is true
                    if i != _dict_name:               # Prevent cycling
                        if (_dict_name + ' -- ' + i) not in str(_graph): # Prevent re-drawn
                            if ('@' not in _dict_name) and ('@'  in i):  # Prevent re-drawn
                                _graph.edge(_dict_name, i,
                                            overlap = 'false',
                                            color   = 'grey')
                                            #~ color   = 'grey',
                                            #~ style   = 'invis')
    return 0

def edge_connection_find(_json_data, _sub_json_data, _graph):
    """
    Function to connect cluster/node with edges, following their
    common proprieties.
    """
    for dict_name in _sub_json_data:
        if type(_sub_json_data[dict_name]) is dict:
            
            # determine if a dict as dict child
            # if the dict include other dict, it is a cluster        
            if check_dict_child(_sub_json_data[dict_name]):
                sub_json_data = _sub_json_data[dict_name]
                device_type = check_device_type(sub_json_data)
                if device_type:
                    draw_edges( _json_data, dict_name, _graph)
                    edge_connection_find(_json_data     = _json_data, 
                                         _sub_json_data = sub_json_data,
                                         _graph         = _graph)

            # else the dict as no child
            else:
                device_type = check_device_type(_sub_json_data)
                if device_type:
                    draw_edges( _json_data, dict_name, _graph)
    return 0

####################################
# Main script
####################################
if __name__ == '__main__':
    
    #~ parser = argparse.ArgumentParser(description='Device Tree Blob dump')
    #~ parser.add_argument('in_filename', help="input filename")
    #~ args = parser.parse_args()

    # Variables
    dtb_dir = "dtb/"
    out_dir = "out/"

    out_format = 'pdf' # pdf, png, svg ...

    # DTB file
    filename  = "sun50i-a64-pine64-pinebook"
    #~ filename  = "sample" 

    # Extract dtb content
    with open(dtb_dir + filename + ".dtb", "rb") as infile:
        dtb = FdtBlobParse(infile)

    fdt      = dtb.to_fdt()
    dts_str  = fdt.to_dts()
    json_str = fdt.to_json()

    # Write dts and json file from dtb content 
    with open(out_dir + filename + ".dts", 'w') as dts_file:
        dts_file.write(dts_str)
        
    with open(out_dir + filename + ".json", 'w') as json_file:
        json_file.write(json_str)
    
    # Parse json into a python dict
    json_data  = json.loads(json_str)
    
    # Create a Grapviz graph (based on DOT language)
    graph = Graph(filename + '_dtb',
                  filename = filename + '.gv',
                  format   = out_format)
                  
    graph.attr(label    = '<<B>' + 'dtb block design' + '</B>>', 
               compound = 'true',
               rankdir  = 'TB',
               splines  = 'ortho',
               nodesep  = '1',
               overlap  = 'false')

    # generate a tree block from json extrated dict
    draw_clusters(json_data, graph)
    
    # draw edge between clusters and nodes
    edge_connection_find(json_data, json_data, graph)
    
    # pdf output
    graph.render(out_dir + filename + '.gv', view=True) 

