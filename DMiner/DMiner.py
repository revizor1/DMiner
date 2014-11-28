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


def MainSearch(keyword, base="http://seeker.dice.com", tail="/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=4&FREE_TEXT="):
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


def Main():
    G = nx.MultiDiGraph()
    Postings = ExtractPostings(MainSearch("vmware"))
#    G.add_node("VMWare", name="VMware")
    url2desc = {}
    for key in Postings.keys():
        url2desc[key] = ExtractText(GetSoup(key))
#        G.add_node(Postings[key], name=url2desc[key])
#        G.add_edge("VMware", Postings[key], name=url2desc[key])
    G.add_nodes_from(Postings.values())
    print(url2desc)

    H = nx.Graph(G)
    plt.rcParams['text.usetex'] = False
    plt.figure(figsize=(8, 8))

    try:
        pos = nx.graphviz_layout(H)
    except:
        pos = nx.spring_layout(H, iterations=20)
    nx.draw_networkx_labels(H, pos, fontsize=12)

    plt.axis('off')
    plt.text(0.5, 0.97, "VMware",
             horizontalalignment='center', transform=plt.gca().transAxes)

    font = {'fontname': 'Arial',
            'color': 'k',
            'fontweight': 'bold',
            'fontsize': 14}

    plt.title("PZ", font)
    nx.draw(G)
    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()
    return G


if __name__ == '__main__':
    Main()
    print(" ")
