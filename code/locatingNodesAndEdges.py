import pandas as pd
import folium
from folium import Map, Marker, PolyLine, features, RegularPolygonMarker, DivIcon
from folium.plugins import PolyLineTextPath
import math
import networkx as nx


# Inntak
nodes = pd.read_csv("data/nodes.tsv", sep="\t")
edges = pd.read_csv("data/edges.tsv", sep="\t")

# hleðslustöðvar valdar að handahófi
charging_station_nodes = {323346405, 87120378, 2374444198, 1345740157, 2351742223}


# Setjum upp hnit með folium
coords = {
    row['osmid']: (row['y'], row['x'])  # Folium notar (lat, lon)
    for _, row in nodes.iterrows()
}

# búum til graf með stefnu og þyngd fyrir edges
G = nx.DiGraph()
for _, row in edges.iterrows():
    G.add_edge(row['u'], row['v'], weight=row['length'])



# Finnum styðstu leið milli nodes og næstu hleðslustöðvar. 
def shortest_distance_to_charger(node_id, graph, charger_nodes):
    min_distance = float('inf')
    closest_station = None
    for charger_id in charger_nodes:
        try:
            dist = nx.dijkstra_path_length(graph, source=node_id, target=charger_id, weight='weight')
            if dist < min_distance:
                min_distance = dist
                closest_station = charger_id
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
    return min_distance, closest_station

# Búum til base map með miðju í average location. 
center_lat = nodes['y'].mean()
center_lon = nodes['x'].mean()
m = folium.Map(location = [center_lat, center_lon], zoom_start= 12)


# reiknum gráður fyrir örina sjálfa
def calculate_angle(start, end):
    dy = end[0] - start[0]
    dx = end[1] - start[1]
    angle = math.degrees(math.atan2(dy, dx))
    return angle


# setjum nodes á kortið - blátt=nonprimary rautt=primary og appelsínugult= hleðslustöð.
for _, row in nodes.iterrows():
    node_id = row['osmid']

    # Decide color and popup content
    if node_id in charging_station_nodes:
        color = "orange"
        popup_text = f"🔌 Hleðslustöð <br>Node ID: {node_id}"
    else:
        color = "red" if row['primary'] else "blue"
        distance, closest = shortest_distance_to_charger(node_id, G, charging_station_nodes)
        popup_text = f"🚗 Node ID: {node_id}<br>Primary: {row['primary']}<br>" \
                     f"Fjarlægð frá næstu hleðslustöð: {distance:.2f} meters<br>Næsta hleðslustöð: {closest}"
    
    folium.CircleMarker(
        location=[row['y'], row['x']],
        radius=4,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(popup_text, max_width=250)
    ).add_to(m)


# setjum edges með stefnu á kortið
for _, row in edges.iterrows():
    if row['u'] in coords and row['v'] in coords:
        start = coords[row['u']]
        end = coords[row['v']]

        # línan
        PolyLine(
            locations=[start, end],
            color='gray',
            weight=1,
            opacity=0.5,
            popup=row.get('name', '')
        ).add_to(m)

        # Reiknum gráðu á ör-iconinu og setjum svo á endann á línunni
        # vantar að laga betur, gerir kortið mjög hægt líka. 
        """angle = calculate_angle(start, end)
        folium.map.Marker(
            location=end,
            icon=DivIcon(
                icon_size=(150, 36),
                icon_anchor=(7, 20),
                html=f'<div style="transform: rotate({angle}deg); color: gray; font-size: 16px;">&#8594;</div>'
            )
        ).add_to(m)"""


output_file = "kort.html"
m.save(output_file)
print(f"Kort geymt i skra: {output_file}")