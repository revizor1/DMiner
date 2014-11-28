'''
Created on Nov 27, 2014

@author: PZ
'''

from bs4 import BeautifulSoup as bs4
import urllib.request
import re
import networkx as nx
import matplotlib.pyplot as plt
from _ctypes import Array


def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True


def MainSearch(keyword, base="http://seeker.dice.com", tail="/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=5&FREE_TEXT="):
    """
    Get job listings from main keyword search and returns bs
    """
    url = base + tail + keyword
    resp = urllib.request.urlopen(url)
    soup = bs4(resp.read(), from_encoding=resp.info().get_param('charset'))
    return soup


def GetSoup(url):
    """
    Get job listings from main keyword search and returns bs
    """
    resp = urllib.request.urlopen(url)
    soup = bs4(resp.read(), from_encoding=resp.info().get_param('charset'))
    return soup


def ExtractPostings(soup, base="http://seeker.dice.com"):
    """
    Takes bs and returns dict{url:Title}
    """
    results = {}
    for link in soup.find_all('a', href=True):
        if "op=302&" in link['href']:
            results[base + link.get('href').split('@')[0]] = link.text

    return results


def ExtractText(soup, base="http://seeker.dice.com"):
    """
    Get html and return visible text without all tags
    """
    texts = []
    # kill all script and style elements
    for script in soup(["script", "style", "input", "extjvbutton"]):
        script.extract()    # rip it out

    for string in soup.stripped_strings:
        texts.append(string.replace(u'\xa0', u' ').replace('*', ''))
    return texts


def kw2Jd():
    fExclusions = "C:\\Workdir\\pZuikov\\r\\exclusions.txt"
    exclusions = [line.strip() for line in open(fExclusions)]
    G = nx.MultiDiGraph()
    tail = "/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=" + \
        str(results) + "&FREE_TEXT="
    Postings = ExtractPostings(MainSearch("vmware", tail=tail))
#     G.add_node("VMWare", weight=8, color="b")
    freqs["vmware"] = freqs.get("vmware", 0) + 1
    url2desc = {}
    data = []
    for key in Postings.keys():
        url2desc[key] = ExtractText(GetSoup(key))
        data.append(("vmware", Postings[key]))
        G.add_edge("vmware", Postings[key], alpha=0)
        freqs[Postings[key]] = freqs.get(Postings[key], 0) + 1

        for line in url2desc[key]:
            for word in re.split('[ :,.]', line.lower()):
                # fetch and increment OR initialize
                freqs[word] = freqs.get(word, 0) + 1

                if freqs[word] > results and freqs[word] < 2 * results:
                    if len(word) < 8 and len(word) > 2:
                        if re.match('\D', word):  # Weed out numerics
                            # Weed out non-alphanumerics
                            if not re.match('\W', word):
                                if word.upper() not in exclusions:
                                    data.append((Postings[key], word))
                                    G.add_edge(Postings[key], word)

    return G


def Main():
    G = kw2Jd()
    H = nx.Graph(G)
    font = {'fontname': 'Arial',
            'color': 'k',
            'fontweight': 'bold',
            'fontsize': 14}
    plt.rcParams['text.usetex'] = False
    plt.figure(figsize=(8, 8))
    plt.title("PZ", font)
    plt.axis('off')
    plt.text(0.5, .95, "VMware",
             horizontalalignment='center', transform=plt.gca().transAxes)
    try:
        pos = nx.graphviz_layout(H)
    except:
        pos = nx.spring_layout(H, iterations=20)

    print(pos)
    nx.draw_networkx_edges(
        H, pos, alpha=0.1, node_size=0, width=2, edge_color='w')
    nx.draw_networkx_labels(H, pos, fontsize=12)

    sampleFreq = dict.fromkeys(G.nodes(), 0.0)
    for (u, v, d) in G.edges(data=True):
        sampleFreq[u] += 1.0
        sampleFreq[v] += 4.0
#         r = d['freqs']
#         if r[0] == '1':
#             wins[u] += 1.0
#         elif r[0] == '1/2':
#             wins[u] += 0.5
#             wins[v] += 0.5
#         else:
#             wins[v] += 1.0
    nodesize = [sampleFreq[v] * 50 for v in H]

    nodes = H.nodes()
    blue = nodes.pop()

    nx.draw_networkx_nodes(H, pos, nodelist=[blue], node_color='b', alpha=.5)
    nx.draw_networkx_nodes(
        H, pos, nodelist=nodes, node_color='w', alpha=.2, node_size=nodesize)
#     for i in H.nodes_iter(data=True):
#         H.nodes[i]['freqs'] = freqs[i][0]
#         print(i)

#     nodesize = [freqs[v, 0] for v in H]
#     print(nodesize)
# nx.draw(H)  # Messes up everything
    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()


if __name__ == '__main__':
    results = 4
    freqs = {}
    Main()
    print(" ")
