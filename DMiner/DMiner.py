'''
Created on Nov 27, 2014

@author: PZ
'''

from bs4 import BeautifulSoup as bs4
from threading import Thread
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
    try:
        resp = urllib.request.urlopen(url)
        soup = bs4(resp.read(), from_encoding=resp.info().get_param('charset'))
        return soup
    except:
        return


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


def ExtractSalary(word):
    soup = GetSoup("http://www.indeed.com/salary?q1=" + word)
    try:
        for sal in soup.find_all('span', 'salary'):
            s = int(sal.text.replace('$', '').replace(',', '')) / 1000
    except:
        s = 0
    return s


def ExtractSupply(word):
    soup = GetSoup("http://www.indeed.com/resumes?q=" + word)
    try:
        s = soup.find('div', {'id': 'result_count'})
        s = int(s.text.strip().split()[0].replace(',', ''))
    except:
        s = 10000
    return s


def ExtractOpenings(word):
    soup = GetSoup(
        "http://seeker.dice.com/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=1&FREE_TEXT=" + word)
    try:
        s = int(
            soup.find('div', {'id': 'searchResHD'}).contents[1].text.split()[-1])
    except:
        s = 0
    return s


def ExtractTrend(word):
    soup = GetSoup("http://www.simplyhired.com/a/jobtrends/trend/q-" + word)
    try:
        s = soup.find('li', 'trends_stats')
        t = int(s.contents[1].strip().split()[-1].replace('%', ''))
        if 'decreased' in s.contents[1].strip().split():
            t = -t
    except:
        t = 0
    return t


def kw2Jd(searchterm):
    exclusions = [line.upper().strip() for line in open(fExclusions)]
    sresume = " ".join([line.lower().strip() for line in open(fResume)])
    G = nx.MultiDiGraph()
    tail = "/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=" + \
        str(results) + "&FREE_TEXT="

    Postings = ExtractPostings(MainSearch(searchterm, tail=tail))
    freqs[searchterm] = freqs.get(searchterm, 0) + 1
    salary[searchterm] = ExtractSalary(searchterm)
    supply[searchterm] = ExtractSupply(searchterm)
    openings[searchterm] = ExtractOpenings(searchterm)
    trends[searchterm] = ExtractTrend(searchterm)
    url2desc = {}
    data = []
    for key in Postings.keys():
        url2desc[key] = ExtractText(GetSoup(key))
        data.append((searchterm, Postings[key]))
        G.add_edge(Postings[key], searchterm, alpha=0)
        freqs[Postings[key]] = freqs.get(Postings[key], 0) + 1

        for line in url2desc[key]:
            for word in re.split('[ :,.!?\)\(/@#%&*;"=\-\+\$]', line.lower()):
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
        if freqs[word] > results * .2 + 1 and freqs[word] < 4 * results:
            for key in Postings.keys():
                if word in " ".join(url2desc[key]):
                    data.append((Postings[key], word))
                    G.add_edge(Postings[key], word, weight=10 * freqs[word])
                    salary[word] = ExtractSalary(word)
                    supply[word] = ExtractSupply(word)
                    openings[word] = ExtractOpenings(word)
                    trends[word] = ExtractTrend(word)
    return G


def Main():
    searchterm = "VCLOUD"
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
#     ax = plt.axes([0, 0, 1, 1])
    try:
        pos = nx.graphviz_layout(H)
    except:
        pos = nx.spring_layout(H, iterations=20)

    nx.draw_networkx_edges(
        H, pos, alpha=0.1, node_size=0, edge_color='w', width=3)
    nx.draw_networkx_labels(H, pos, fontsize=12)

    sampleFreq = dict.fromkeys(G.nodes(), 0.0)
    for (u, v, d) in G.edges(data=True):
        sampleFreq[u] = .001
        sampleFreq[v] += 4.0
    nodesize = [salary.get(v, 0) ** 2 for v in H]

    colorcoding = [openings.get(v, 0) / supply.get(v, 10000) for v in H]
    linewidths = [
        (abs(trends.get(v, 0)) - trends.get(v, 10000)) / 10 for v in H]
    nodes = H.nodes()

    nx.draw_networkx_nodes(H, pos, nodelist=nodes, node_size=nodesize, linewidths=linewidths,
                           cmap=plt.get_cmap('jet'), vmin=0, vmax=2 * max(colorcoding), node_color=colorcoding)

    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()


if __name__ == '__main__':
    results = 20
    fExclusions = "C:\\Workdir\\pZuikov\\r\\exclusions.txt"
    fResume = "C:\\Workdir\\pZuikov\\r\\pz.txt"

    freqs = {}
    supply = {}
    openings = {}
    trends = {}
    salary = {}
    Main()
