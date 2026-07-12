import pandas as pd
import requests
import xml.etree.ElementTree as ET

def query_sda(query):
    url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"
    payload = {"query": query}
    response = requests.post(url, data=payload)

    root = ET.fromstring(response.text)
    data = []
    for table in root.findall(".//Table"):
        row = {child.tag: child.text for child in table}
        data.append(row)

    return pd.DataFrame(data)