from flask import Flask
import pandas as pd
import requests
import json
import folium

app = Flask(__name__)

url = 'http://environment.data.gov.uk/flood-monitoring/id/floods'
r = requests.get(url).json()

severity_list = []
time_changed_list = []
flood_id_list = []
polygon_url_list = []
severity_level_list = []

for i in range(len(r['items'])):
    severity = r['items'][i]['severity']
    severity_level = r['items'][i]['severityLevel']
    time_changed = r['items'][i]['timeSeverityChanged']
    flood_id = r['items'][i]['floodArea']['@id']
    polygon_url = r['items'][i]['floodArea']['polygon']

    severity_list.append(severity)
    severity_level_list.append(severity_level)
    time_changed_list.append(time_changed)
    flood_id_list.append(flood_id)
    polygon_url_list.append(polygon_url)

df = pd.DataFrame(list(zip( 
                severity_list, severity_level_list, time_changed_list, flood_id_list, polygon_url_list)),
columns = ["id", "county", "status", 'severity_level', "date changed", "latlon_url", "polygon_url", "riverorsea"])    

df = df[df['status']== 'Flood alert']
df = df[df['severity_level']> 2]
df.reset_index(inplace=True, drop=True)

df2 = df
df2['coords'] =""
df2['description']=""
coords_list = []

for i in range(len(df2['latlon_url'])): 
    #if i % 10 == 0:
     #   print('{} of {} urls processed.\r'.format(i, len(df2)))
    r3 = requests.get(df2['polygon_url'][i]).json()
    coords = r3['features'][0]['geometry']
    coords_list.append(coords)
    df2['description'].iloc[i] =r3['features'][0]['properties']['DESCRIP']

@app.route('/')
def index():
    m = folium.Map(location=[51.509865,-0.118092], zoom_start='6')
    style_1 = {'fillColor': '#dd1c77',  'color': '#dd1c77', "fillOpacity": 0.5}
    for i in range(len(coords_list)):
        geo_json = folium.GeoJson(coords_list[i], style_function = lambda x:style_1)
        geo_json.add_child(folium.Popup('Description: {} \n Severity: {}' .format(df2['description'][i], df2['severity_level'][i])))
        geo_json.add_to(m)
    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True)
