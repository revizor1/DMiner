from bs4 import BeautifulSoup as bs4
from threading import Thread
import urllib.request
import re
import networkx as nx
import matplotlib.pyplot as plt


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


def ExtractSalary(word):
    soup = GetSoup("http://www.indeed.com/salary?q1=" + word)
    try:
        t = soup.find('span', 'salary')
        s = int(t.text.replace('$', '').replace(',', '')) / 1000
    except:
        s = 0
    salary[word] = s
    return s


def ExtractSupply(word):
    soup = GetSoup("http://www.indeed.com/resumes?q=" + word)
    try:
        s = soup.find('div', {'id': 'result_count'})
        s = int(s.text.strip().split()[0].replace(',', ''))
    except:
        s = 10000
    supply[word] = s
    return s


def ExtractOpenings(word):
    soup = GetSoup(
        "http://seeker.dice.com/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=1&FREE_TEXT=" + word)
    try:
        s = int(
            soup.find('div', {'id': 'searchResHD'}).contents[1].text.split()[-1])
    except:
        s = 1
    openings[word] = s
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
    trends[word] = t
    return t


def ExtractPostings(soup, base="http://seeker.dice.com"):
    """
    Takes bs and returns dict{url:Title}
    """
    results = {}
    for link in soup.find_all('a', href=True):
        if "op=302&" in link['href']:
            results[base + link.get('href').split('@')[0]] = link.text

    return results


def SanitizeText(string):
    string = string.upper()
    string = re.sub('[^A-Za-z0-9\\s\\.]+', ' ', string)
    string = re.sub('\\b[\d]+\\b', ' ', string)
    string = re.sub('\\b.{1,2}\\b', ' ', string)
    string = clean_sentence(string)
    return string


def ExtractText(soup, base="http://seeker.dice.com"):
    """
    Get html and return visible text without all tags
    """
    texts = []
    # kill all script and style elements
    for script in soup(["script", "style", "input", "extjvbutton"]):
        script.extract()    # rip it out

    for string in soup.stripped_strings:
        string = SanitizeText(string)
        if string:
            texts.append(string)
    return texts


def clean_sentence(text):
    """
    Returns a list of all words from the sentence.
    """
    text = text.split()
    for word in text:
        #         if word in exclusions or word in sresume.upper():
        if word in exclusions:
            text.remove(word)
    x = " ".join(text)
    return x


def kw2Jd(searchterm):
    G = nx.MultiDiGraph()
    tail = "/jobsearch/servlet/JobSearch?op=100&NUM_PER_PAGE=" + \
        str(resultsMax) + "&FREE_TEXT="

    Postings = ExtractPostings(MainSearch(searchterm, tail=tail))
    freqs[searchterm] = freqs.get(searchterm, 0) + 1
    salary[searchterm] = ExtractSalary(searchterm)
    supply[searchterm] = ExtractSupply(searchterm)
    openings[searchterm] = ExtractOpenings(searchterm)
    trends[searchterm] = ExtractTrend(searchterm)
    url2desc = {}

    resultsCount = len(Postings)
    for key in Postings.keys():
        t = ExtractText(GetSoup(key))
        if t:
            url2desc[key] = t
            freqs[Postings[key]] = freqs.get(Postings[key], 0) + 1

            for line in url2desc[key]:
                for word in re.split('[\s :,.!?\)\(/@#%&*;"=\-\+\$''_]', line.upper()):
                    if len(word) < 18 and len(word) > 2:
                        freqs[word] = freqs.get(word, 0) + 1

# for word in re.split('[\s :,.!?\)\(/@#%&*;"=\-\+\$''_]', line.lower()):
#                     if len(word) < 18 and len(word) > 2:
# if re.match('\D', word):  # Weed out numerics
# Weed out non-alphanumerics
#                             if not re.match('\W', word):
#                                 if word.upper() not in exclusions:
#                                     if word.lower() not in sresume:
# fetch and increment OR initialize
#                                         freqs[word] = freqs.get(word, 0) + 1
    fulltext = ""
    for key in Postings.keys():
        fulltext += " ".join(url2desc[key])

    output = open('{}'.format(fTxtOut), 'w')
    output.write(fulltext)

    words = []
    j2w = []
    for word in freqs.keys():
        if freqs[word] > resultsCount * .2 + 1 and freqs[word] < 4 * resultsCount:
            threads = []
            t = Thread(target=ExtractSalary, args=(word,))
            t.start()
            threads.append(t)

            t = Thread(target=ExtractSupply, args=(word,))
            t.start()
            threads.append(t)

            t = Thread(target=ExtractOpenings, args=(word,))
            t.start()
            threads.append(t)

            t = Thread(target=ExtractTrend, args=(word,))
            t.start()
            threads.append(t)

            for t in threads:
                t.join()
#            print(word.upper())

            if salary[word] > 80:
                for key in Postings.keys():
                    if word in " ".join(url2desc[key]):
                        #                        G.add_edge(Postings[key], word, weight=10 * freqs[word])
                        words.append(word)
                        j2w.append((Postings[key], word))
    w = zip([searchterm for x in words], words)
    G.add_edges_from(j2w)
    return G


def Main():
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

    nx.draw_networkx_edges(
        H, pos, alpha=0.1, node_size=0, edge_color='w', width=3)
    nx.draw_networkx_labels(H, pos, fontsize=12)

    nodesize = [salary.get(v, 0) ** 2 for v in H]

    colorcoding = [supply.get(v, 10000) / (openings.get(v, 1) + 1) for v in H]
    linewidths = [
        (abs(trends.get(v, 0)) - trends.get(v, 10000)) / 10 for v in H]
    nodes = H.nodes()

    nx.draw_networkx_nodes(H, pos, nodelist=nodes, node_size=nodesize, linewidths=linewidths, cmap=plt.cm.Blues, vmin=min(
        colorcoding), vmax=100, node_color=colorcoding)
    plt.savefig("pz-networkx.png", dpi=75)
    plt.show()


if __name__ == '__main__':
    searchterm = "HYPERCONVERGED"
    resultsCount = resultsMax = 50
    fTxtOut = "C:\\temp\\tmp.txt"
    fExclusions = "C:\\Workdir\\pZuikov\\r\\exclusions.txt"
    fResume = "C:\\Workdir\\pZuikov\\r\\pz.txt"
    exclusions = [line.upper().strip() for line in open(fExclusions)]
#     sresume = " ".join([line.upper().strip() for line in open(fResume)])
#     sresume = " ".join([SanitizeText(line) for line in open(fResume)])
    sresume = (" ".join([SanitizeText(line)
                         for line in open(fResume)])).split()

    print(sresume)
    freqs = {}
    supply = {}
    openings = {}
    trends = {}
    salary = {}
    Main()
