from flask import Flask
import pandas as pd
import requests
import json
import folium

app = Flask(__name__)

url = 'http://environment.data.gov.uk/flood-monitoring/id/floods'
r = requests.get(url).json()

flood_area_id_list = []
county_list = []
severity_list = []
time_changed_list = []
flood_id_list = []
lat_list = []
long_list = []
polygon_url_list = []
riverorsea_list = []
severity_level_list = []

for i in range(len(r['items'])):
    flood_area_id = r['items'][i]['floodAreaID']
    county = r['items'][i]['floodArea']['county']
    severity = r['items'][i]['severity']
    severity_level = r['items'][i]['severityLevel']
    time_changed = r['items'][i]['timeSeverityChanged']
    flood_id = r['items'][i]['floodArea']['@id']
    polygon_url = r['items'][i]['floodArea']['polygon']
    riverorsea = r['items'][i]['floodArea']['riverOrSea']

    flood_area_id_list.append(flood_area_id)
    county_list.append(county)
    severity_list.append(severity)
    severity_level_list.append(severity_level)
    time_changed_list.append(time_changed)
    flood_id_list.append(flood_id)
    polygon_url_list.append(polygon_url)
    riverorsea_list.append(riverorsea)

df = pd.DataFrame(list(zip(flood_area_id_list, county_list, 
                severity_list, severity_level_list, time_changed_list, flood_id_list, polygon_url_list, riverorsea_list)),
columns = ["id", "county", "status", 'severity_level', "date changed", "latlon_url", "polygon_url", "riverorsea"])    

df = df[df['status']!='Warning no longer in force']
df.reset_index(inplace=True, drop=True)

df['lat'] = ""
df['long'] = ""
df['coords'] =""
df['description']=""
coords_list = []

for i in range(len(df['latlon_url'])): 
    r2 = requests.get(df['latlon_url'][i]).json()
    df['long'].iloc[i] = r2['items']['long']
    df['lat'].iloc[i] = r2['items']['lat']
    
    r3 = requests.get(df['polygon_url'][i]).json()
    coords = r3['features'][0]['geometry']
    coords_list.append(coords)
    df['description'].iloc[i] =r3['features'][0]['properties']['DESCRIP']

df['coords'] = coords_list

@app.route('/')
def index():
    m = folium.Map(location=[51.509865,-0.118092], zoom_start='6')
    style_1 = {'fillColor': '#dd1c77',  'color': '#dd1c77', "fillOpacity": 0.5}
    for i in range(len(coords_list)):
        geo_json = folium.GeoJson(coords_list[i], style_function = lambda x:style_1)
        geo_json.add_child(folium.Popup('Description: {} \n Severity: {}' .format(df['description'][i], df['severity_level'][i])))
        geo_json.add_to(m)
    return m._repr_html_()

if __name__ == '__main__':
    app.run() #host='0.0.0.0', port=PORT
