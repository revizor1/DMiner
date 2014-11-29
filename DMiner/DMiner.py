'''
Created on Nov 27, 2014

@author: PZ
'''

from bs4 import BeautifulSoup as bs4
import urllib.request
import re
import networkx as nx
import matplotlib.pyplot as plt


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


def kw2Jd(searchterm):
    exclusions = [line.upper().strip() for line in open(fExclusions)]
    sresume = " ".join([line.lower().strip() for line in open(fResume)])
    G = nx.MultiDiGraph()
    tail = "/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=" + \
        str(results) + "&FREE_TEXT="

    Postings = ExtractPostings(MainSearch(searchterm, tail=tail))
    freqs[searchterm] = freqs.get(searchterm, 0) + 1
    url2desc = {}
    data = []
    for key in Postings.keys():
        url2desc[key] = ExtractText(GetSoup(key))
        data.append((searchterm, Postings[key]))
        G.add_edge(searchterm, Postings[key], alpha=0)
        freqs[Postings[key]] = freqs.get(Postings[key], 0) + 1

        for line in url2desc[key]:
            for word in re.split('[ :,.!?\)\(/]', line.lower()):
                if len(word) < 18 and len(word) > 2:
                    if re.match('\D', word):  # Weed out numerics
                        # Weed out non-alphanumerics
                        if not re.match('\W', word):
                            if word.upper() not in exclusions:
                                if word.lower() not in sresume:
                                    # fetch and increment OR initialize
                                    freqs[word] = freqs.get(word, 0) + 1
    for word in freqs.keys():
        print(word, freqs[word])
        if freqs[word] > results * .2 and freqs[word] < 4 * results:
            for key in Postings.keys():
                if word in " ".join(url2desc[key]):
                    data.append((Postings[key], word))
                    G.add_edge(Postings[key], word)

    return G


def Main():
    searchterm = "vmware"
    G = kw2Jd(searchterm)
    H = nx.Graph(G)
    font = {'fontname': 'Arial',
            'color': 'k',
            'fontweight': 'bold',
            'fontsize': 14}
    plt.rcParams['text.usetex'] = False
    plt.figure(figsize=(8, 8))
    plt.title("PZ", font)
    plt.axis('off')
    plt.text(0.5, .95, searchterm,
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
        sampleFreq[u] += .0
        sampleFreq[v] += 4.0
    nodesize = [sampleFreq[v] * 50 for v in H]

    alphas = [freqs.get(v, 0) for v in H]

    print(nodesize)
    print(alphas)
    nodes = H.nodes()

    nx.draw_networkx_nodes(H, pos, nodelist=nodes, node_size=nodesize,
                           cmap=plt.get_cmap('jet'), vmin=0, vmax=max(alphas), node_color=alphas)

# nx.draw(H)  # Messes up everything
    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()


if __name__ == '__main__':
    results = 50
    fExclusions = "C:\\Workdir\\pZuikov\\r\\exclusions.txt"
    fResume = "C:\\Workdir\\pZuikov\\r\\pz.txt"

    freqs = {}
    Main()
    print(" ")
