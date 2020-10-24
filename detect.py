#!/usr/bin/python3

import jsbeautifier as jsb
import sys
import urllib3

from urllib.parse import urlparse
from bs4 import BeautifulSoup

def parse_url(url):
    parsed_url = urlparse(url)
    root_url = parsed_url.scheme + "://" + parsed_url.netloc
    path = parsed_url.path
    if path.endswith("/") == False:
        path = "".join(path.rpartition("/")[:2])
    return root_url, path
    
def get_urls(tags, given_url):
    # get values from src attributes
    src_values = [tag["src"] for tag in tags if tag.has_attr("src")]
    
    urls = []
    for src_value in src_values:
        if src_value.startswith("//") or src_value.startswith("http"):
            urls.append(src_value)
        else:
            root, path = parse_url(given_url)
            if src_value.startswith("/"):
                urls.append(root+"/"+src_value[1:])
            else:
                urls.append(root+path+src_value)
    return urls

def get_page(url):
    http = urllib3.PoolManager()
    try:
        page = http.request("GET", url)
    except Exception as e:
        print(e)
    return page

def loopy(lines):
    for index,line in enumerate(lines):
        if "postMessage" in line or "addEventListener(\"message\"" in line:
            try:
                snip = lines[index-1]+"\n"+line+"\n"+lines[index+1]
            except IndexError:
                snip = line
            yield [index+1, snip]

def search_web_messaging(js_data):
    if type(js_data) == type(b"test bytes"):
        js_data = js_data.decode("utf-8")
    js_lines = jsb.beautify(js_data).splitlines()
    snippets = [snip for snip in loopy(js_lines)]  
    return snippets            

def analyse_embedded_js(script_tags):
    js_embedded = []
    for tag in script_tags:
        em_snip = search_web_messaging(str(tag))
        if em_snip != []:
            js_embedded.append(em_snip)
    return js_embedded

if __name__ == "__main__":
    CODE = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'
    url_argv = sys.argv[1]

    page = get_page(url_argv)
    soup = BeautifulSoup(page.data, "html.parser")

    # Get script tags from first page
    script_tags = list(soup.find_all("script"))

    # Get all js files that are referenced in first page
    urls = get_urls(script_tags, url_argv)
    js_files = [get_page(url) for url in urls]
    js_in_html = analyse_embedded_js(script_tags)
    
    if js_in_html != []:
        print(OKBLUE+"\n### Location : "+page.geturl()+ENDC)
        for script in js_in_html:
            print("\n\t### ------ <Code snip> ------ ###\n")
            print(CODE+"\t"+script[0][1]+ENDC)
            print("\n\t### ------ </Code snip> ------ ###\n\n")
    
    for js_file in js_files:
        scripts = search_web_messaging(js_file.data)
        if scripts != []:
            print(OKBLUE+"\n### Location : "+js_file.geturl()+ENDC)
            for script in scripts:
                print(OKBLUE+"### From line : "+str(script[0])+ENDC)
                print("\n\t### ------ <Code snip> ------ ###\n")
                print(CODE+"\t"+script[1]+ENDC)
                print("\n\t### ------ </Code snip> ------ ###\n\n")

    
    
    






