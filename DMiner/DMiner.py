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


def MainSearch(keyword, base="http://seeker.dice.com", tail="/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=3&FREE_TEXT="):
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
    Postings = ExtractPostings(MainSearch("vmware"))
#     G.add_node("VMWare", weight=8, color="b")
    url2desc = {}
    data = []
    for key in Postings.keys():
        url2desc[key] = ExtractText(GetSoup(key))
        data.append(("VMware", Postings[key]))
        G.add_edge("VMware", Postings[key], alpha=0)
        for line in url2desc[key]:
            for word in line.split():
                # fetch and increment OR initialize
                freqs[word] = freqs.get(word, 0) + 1
            if len(line) < 8 and len(line) > 2:
                if re.match('\D', line):  # Weed out numerics
                    if not re.match('\W', line):  # Weed out non-alphanumerics
                        if line.upper() not in exclusions:
                            print(line)
                            data.append((Postings[key], line))
                            G.add_edge(Postings[key], line)
    print(url2desc)
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
    plt.text(0.5, 1, "VMware",
             horizontalalignment='center', transform=plt.gca().transAxes)

    try:
        pos = nx.graphviz_layout(H)
    except:
        pos = nx.spring_layout(H, iterations=20)
    print(pos)
    nx.draw_networkx_edges(
        H, pos, alpha=0.2, node_size=0, width=2, edge_color='k')
    nx.draw_networkx_nodes(
        H, pos, node_color='w', alpha=0.4)

    nx.draw_networkx_labels(H, pos, fontsize=12)

# nx.draw(H)  # Messes up
    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()


if __name__ == '__main__':

    freqs = {}
    Main()
    print(" ")
