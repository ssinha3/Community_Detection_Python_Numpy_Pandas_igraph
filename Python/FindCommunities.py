# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>
import pdb
import sys
import igraph
from igraph import Graph
import random
import numpy as np
import pandas as pd


def read_graph(file_name):
    # Input edge list file name and output igraph representation
    df = pd.read_csv(file_name, sep=" ", names=["Edge1", "Edge2"])
    n_vertex, n_edge = df.irow(0)
    df = df.drop(0)
    graph = Graph(edges=[(x[1]["Edge1"], x[1]["Edge2"])
                  for x in df.iterrows()], directed=False)
    assert(graph.vcount() == n_vertex)
    assert(graph.ecount() == n_edge)
    return preprocess_graph(graph)


def density(subgraph):
    # Get density of graph (as defined in paper)
    if subgraph.vcount() == 0:
        return 0
    else:
        return subgraph.ecount() * 2.0 / subgraph.vcount()


def pagerank_order(graph, reverse=False):
    # Generator that returns indices of graph vertices in
    # page rank order. Default is smallest-to-largest.
    for (y, x) in sorted(zip(graph.pagerank(directed=False), range(0, graph.vcount())), reverse=reverse):
        yield x


def vertices_in_pagerank_order(graph, reverse=False):
    # Generator that returns graph vertices in page rank
    # order. Default is smallest-to-largest.
    for i in pagerank_order(graph, reverse=reverse):
        yield graph.vs.select([i])[0]


def update_graph(graph, subgraph, vertex, density_metric):
    # Add vertex to subgraph. If density is improved,
    # return this extended subgraph. Otherwise,
    # return original subgraph.
    new_subgraph = graph.subgraph(
        subgraph.vs["original_index"] + [vertex.index])
    if density_metric(new_subgraph) > density_metric(subgraph):
        return new_subgraph, True
    else:
        return subgraph, False


def preprocess_graph(graph):
    # Preprocess graph to ensure it doesn't have loops
    # or multiedges
    graph = graph.simplify()
    graph.vs["original_index"] = graph.vs.indices
    return graph


def LinkAggregateAlgorithm(graph, density_metric):
    # Run link Aggregate Algorithm as describedin paper
    C = set()

    vertex_count = graph.vcount()

    for i, v in enumerate(vertices_in_pagerank_order(graph, reverse=True)):
        if len(C) == 0:
            C.add(graph.subgraph([v.index]))
        C, added_array = zip(
            *map(lambda subgraph: update_graph(graph, subgraph, v, density_metric), C)
        )
        C = set(C)
        if not np.any(added_array):
            C.add(graph.subgraph([v.index]))

        if (i + 1) % 500 == 0:
            print >> sys.stderr, "\t...Processed vertex", i + \
                1, "of", vertex_count
    return C


def ImprovedIterativeScanAlgorithm(subgraph, graph, density_metric):
    # Run Improved Iterative Scan algorithm as described in paper

    C = subgraph
    w = density_metric(subgraph)
    increased = True

    while increased:
        N = C.as_undirected()
        for v in C.vs:
            v_neighbor_indices = [x["original_index"] for x in v.neighbors()]
            N = graph.subgraph(v_neighbor_indices + N.vs["original_index"])
        for v in N.vs:
            if v["original_index"] in C.vs["original_index"]:
                C_prime = graph.subgraph(
                    [x for x in C.vs["original_index"] if x != v["original_index"]])
            else:
                C_prime = graph.subgraph(
                    C.vs["original_index"] + [v["original_index"]])
            if density_metric(C_prime) > density_metric(C):
                C = C_prime
        if density_metric(C) == w:
            increased = False
        else:
            w = density_metric(C)
    return C


def process(file_name):

    graph = read_graph(file_name)
    print >> sys.stderr, "Running Link Aggregate Algorithm..."
    out = LinkAggregateAlgorithm(graph, density)
    print >> sys.stderr, "Running Improved Improved Iterative Scan Algorithm..."
    for i, subgraph in enumerate(out):
        for v in ImprovedIterativeScanAlgorithm(subgraph, graph,
                                                density).vs["original_index"]:
            print v,
        print


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print >> sys.stderr, "ERROR: Program requires single argument: path to graph file."
    else:
        try:
            with open(sys.argv[1]) as f:
                process(sys.argv[1])
        except IOError:
            print >> sys.stderr, 'ERROR: Input file does not exist.'
