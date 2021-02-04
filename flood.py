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

df2 = df[0:10]
df2['lat'] = ""
df2['long'] = ""
df2['coords'] =""
df2['description']=""
coords_list = []

for i in range(len(df2['latlon_url'])): 
    #if i % 10 == 0:
     #   print('{} of {} urls processed.\r'.format(i, len(df2)))
    r2 = requests.get(df['latlon_url'].iloc[i]).json()
    df2['long'].iloc[i] = r2['items']['long']
    df2['lat'].iloc[i] = r2['items']['lat']
    
    r3 = requests.get(df2['polygon_url'].iloc[i]).json()
    coords = r3['features'][0]['geometry']
    coords_list.append(coords)
    df2['description'].iloc[i] =r3['features'][0]['properties']['DESCRIP']

df2['coords'] = coords_list

df_360 = pd.read_csv('https://raw.githubusercontent.com/jenniferbufton/flood_app/main/360Giving_flood_20210204.csv')

@app.route('/')
def index():
    m = folium.Map(location=[51.509865,-0.118092], zoom_start='6')
    style_1 = {'fillColor': '#dd1c77',  'color': '#dd1c77', "fillOpacity": 0.5}
    
    for i in range(len(df_360)):
        folium.Circle(
          location=[df_360['Beneficiary Location:0:Latitude'][i],
                    df_360['Beneficiary Location:0:Longitude'][i]],
          popup=('Organisation: {} \n Amount: £{:,}' .format(df_360['Recipient Org:Name'].iloc[i], 
                                                          df_360['Amount Awarded'].iloc[i])),
          radius=df_360['Amount Awarded'].astype('float')[i]/2,
          color='navy',
          fill=True,
          fill_color='navy',
        opacity=0.2,
        fill_opacity=0.5,
        ).add_to(m)

    for i in range(len(coords_list)):
        geo_json = folium.GeoJson(coords_list[i], style_function = lambda x:style_1)
        geo_json.add_child(folium.Popup('Description: {} \n Severity: {}' .format(df2['description'][i], df2['severity_level'][i])))
        geo_json.add_to(m)
    
    return m._repr_html_()

if __name__ == '__main__':
    app.run()
