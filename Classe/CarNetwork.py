import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import requests, json
import urllib.parse
import folium 
import geopy.distance 
from geopy.distance import geodesic
from folium.plugins import MousePosition
from pyproj import Proj, transform
import folium
import os 


class CarNetwork():
    """
    Classe qui calcul le trajet optimal pour relier un point A à un point B avec une voiture électrique en France.

    Parameters:
    -----------
    A : adresse de départ  / format : numéro, rue, code postal ville (en minuscule)
    B : adresse d'arrivée / format : numéro, rue, code postal ville (en minuscule)
    Autonomie : Autonomie du véhicule utilisé
    --> on précise l'autonomie car si celle-ci est supérieure à la distance totale, 
    alors rien ne sert d'optimiser le trajet.

    Attributes:
    -----------
    x_A : (latitude, longitude) du point A
    x_B : (latitude, longitude) du point B
    df : base de données sur laquelle repose la classe. On la défini à partir d'un URL
    distance : distance between point A and point B that is computed afterwards
    Methods:
    --------
    get_coordo : permet de récupérer x_A et x_B
    calcul_distance_haversine : permet de calculer une distance à vol d'oiseau
    """
    def __init__(self, A = None, B = None, autonomie = None):
        self.A = A
        self.B = B
        self.autonomie = autonomie
        self.x_A = None
        self.x_B = None
        self.distance = None
        self.stations_data = pd.read_csv('https://www.data.gouv.fr/fr/datasets/r/517258d5-aee7-4fa4-ac02-bd83ede23d25', sep = ';')

    def clean_data(self):
        '''
        Les coordonnées de longitude > 90 ou de latitude > 90 sont inutiles car elles dépassent les limites 
        des valeurs possibles pour la longitude (de -180 à 180) et la latitude (de -90 à 90) sur la surface 
        de la Terre, et donc, elles sont généralement considérées comme des données incorrectes. 
        La routine supprime ces données du dataframe.
        '''

        liste = []
    
        for row in self.stations_data.itertuples():

            if row.Xlongitude > 90 or row.Ylatitude > 90:
                liste.append(row.Index)

        self.stations_data.drop(liste)

        # we clean the dataframe 

        droping_liste = list(set(self.stations_data[self.stations_data['Xlongitude'].isna()].index.to_list() + self.stations_data[self.stations_data['Ylatitude'].isna()].index.to_list()))
        self.stations_data.drop(droping_liste, inplace = True)

        # Supprimer les lignes où toutes les valeurs sont les mêmes
        self.stations_data.drop_duplicates()

        # we transform the acces row in the dataframe by defining 
        # a function that we will then apply to the "acces_recharge" row

        def transform_acces(row):
            if not pd.isna(row):  # On ne peut rien dire des nan
                row = row.lower()  # Mettre en lettre minuscule 
                mots = row.split(' ')
                if 'payant' in mots: row = 'payant'
                elif 'gratuit' in mots: row = 'gratuit'
                for mot in mots: 
                    if len(mot.split('€'))>1: row = 'payant'
                    if mot=='carte' or mot=='badge': row = 'carte ou badge'
                    if mot=='oui': row = 'information manquante'
                #else: row = 'accès spécial'
            else: row = 'information manquante'
            return row
        
        self.stations_data['acces_recharge'] = self.stations_data['acces_recharge'].apply(transform_acces)
        list(self.stations_data['acces_recharge'].unique())

    def get_coordo(self):
        """
        Permet de renvoyer (latitude,longitude)
        """
        dep_json_A = requests.get("https://api-adresse.data.gouv.fr/search/?q=" + urllib.parse.quote(self.A) + "&format=json").json()
        dep_json_B = requests.get("https://api-adresse.data.gouv.fr/search/?q=" + urllib.parse.quote(self.B) + "&format=json").json()
        self.x_A = list(dep_json_A['features'][0].get('geometry').get('coordinates'))
        self.x_B = list(dep_json_B['features'][0].get('geometry').get('coordinates'))

    def trajet_voiture(self):
    

        """
        ================================================================
        IDÉE : Fonction qui calcule l'itinéraire en voiture entre deux 
               adresses en utilisant l'API d'adresse gouvernementale et 
               la bibliothèque pyroutelib3.

        ================================================================

        ================================================================
        PARAMÈTRES : 

        ================================================================

        ================================================================
        SORTIE : Liste de coordonnées (latitude, longitude) représentant 
                 l'itinéraire en voiture.
        ================================================================

        
        
        Note: Il est recommandé d'inclure le code de la fonction get_cordo dans cette routine au cas où
        l'utilisateur utilise la méthode trajet_voiture avant celle get_cordo. Dans ce cas, les transformations
        sur self.x_A et self.x_B n'auraient pas été faites.

        """


        ## Il faut inclure le code de get_cordo dans le code de cette routine au cas où l'utilisateur 
        # utilise la méthode trajet_voiture avant celle get_cordo auquel cas les transformations sur 
        # self.x_A et self.x_B n'auraient pas été faites. 

        dep_json_A = requests.get("https://api-adresse.data.gouv.fr/search/?q=" + urllib.parse.quote(self.A) + "&format=json").json()
        dep_json_B = requests.get("https://api-adresse.data.gouv.fr/search/?q=" + urllib.parse.quote(self.B) + "&format=json").json()
        self.x_A = list(dep_json_A['features'][0].get('geometry').get('coordinates'))
        self.x_B = list(dep_json_B['features'][0].get('geometry').get('coordinates'))

        coord_dep = self.x_A 
        coord_arr = self.x_B
        router = pyroutelib3.Router('car')
        depart = router.findNode(coord_dep[1], coord_dep[0])
        #print(depart)
        arrivee = router.findNode(coord_arr[1], coord_arr[0])
        #print(arrivee)

        routeLatLons=[coord_dep,coord_arr]

        status, route = router.doRoute(depart, arrivee)

        if status == 'success':
            #print("Votre trajet existe")
            routeLatLons = list(map(router.nodeLatLon, route))
        #else:
            #print("Votre trajet n'existe pas")

        return routeLatLons
    

    def get_route_map(self):

        """

        ================================================================
        IDÉE : Fonction qui génère une carte représentant l'itinéraire 
               en voiture entre deux destinations, centrée sur Paris, 
               avec l'itinéraire tracé en rouge.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        ================================================================

        ================================================================
        SORTIE : Objet carte Folium représentant l'itinéraire.
        ================================================================

        """

        ## On récupère les coordonnées de Paris pour centrer la carte
        #  sur Paris
        trajet = self.trajet_voiture()
        paris_coord = [48.8566, 2.3522]

        # Crée une carte centrée sur Paris
        carte = folium.Map(location=paris_coord, zoom_start=13)


        # Représenter le point de départ et le point d'arrivée 
        # Pour le point de départ
        folium.Marker(
            location=trajet[0],
            popup=self.A,
            icon=folium.Icon(icon='home', prefix='fa', color='blue'),
            tooltip=self.A
        ).add_to(carte)


        # Pour le point d'arrivée 
        folium.Marker(
            location=trajet[-1],
            popup=self.B,
            icon=folium.Icon(icon='flag', prefix='fa', color='red'),
            tooltip=self.B
        ).add_to(carte)

        # Trace l'itinéraire
        """folium.PolyLine(locations=trajet, color='red').add_to(carte)"""

        folium.plugins.AntPath(
            locations=trajet, 
            reverse="True", 
            dash_array=[20, 30]
        ).add_to(carte)

        carte.fit_bounds(carte.get_bounds())

        # Paramétrer le plein écran sur la carte
        folium.plugins.Fullscreen(
            position="bottomleft",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True,
        ).add_to(carte)
        
        # Permet à l'utilisateur d'afficher la localisation du point sur 
        # lequel sa souris pointe
        MousePosition().add_to(carte)

        # Pour des raisons pratiques, on se restreint ici aux
        # localisations en île-de-France

        # On récupère les localisations des frontières de l'île-de-France 
        # sur le site https://france-geojson.gregoiredavid.fr/
        geojson_url = 'https://france-geojson.gregoiredavid.fr/repo/regions/ile-de-france/region-ile-de-france.geojson'
    

        # C'est une fonction définie par l'utilisateur qui prend 
        # en argument un élément géographique (ou une "feature") 
        # du GeoJSON et renvoie un dictionnaire spécifiant le style 
        # à appliquer à cet élément.
        def style_function(feature):
            return {
                'fillOpacity': 0,  # Ajuster la transparence ici (0 pour transparent, 1 pour opaque)
                'weight': 2, # contour bleu avec une épaisseur de 2
                'color': 'blue'
            }
        
        # Cette fonction de Folium est utilisée pour charger le 
        # fichier GeoJSON depuis l'URL spécifiée (geojson_url). 
        folium.GeoJson(
            geojson_url,
            name='Île-de-France', 
            style_function=style_function, 
            popup="Limites de l'île-de-France"
        ).add_to(carte)

        # Affiche la carte dans le notebook
        return carte
    
    def distance_via_routes(self):

        """

        ================================================================
        IDÉE : Fonction qui calcule la distance totale d'un trajet en 
               voiture entre deux destinations, tout en identifiant les 
               points d'arrêt potentiels où l'autonomie de la voiture ne 
               suffit plus.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        ================================================================

        ================================================================
        SORTIE : Tuple contenant la distance totale du trajet en voiture 
                 et une liste de coordonnées représentant les points 
                 d'arrêt potentiels où l'autonomie de la voiture ne suffit 
                 plus.
        ================================================================

        """

        ## On récupère le trajet en voiture entre les deux destinations 
        # A et B
        trajet = self.trajet_voiture()

        distance = 0
        distance_1 = 0 ## we use this double variable in the if
        # condition to remove the autonomy
        j = 0

        stop_coord = []

        for i in range(len(trajet)-1):
        
            ## on convertit l'élément i de la liste trajet, 
            # qui est un tuple, en une liste
            trajet_depart = list(trajet[i]) 
            trajet_arrivee = list(trajet[i+1])

            d = geopy.distance.distance(trajet_depart, trajet_arrivee).kilometers

            distance = distance + d
            distance_1 = distance 
            distance_1 = distance_1 - j*self.autonomie

            ## On fait d'une pierre deux coup dans ce code en calculant 
            #  une liste qui renvoie les premiers points à partir desquels 
            #  l'autonomie ne couvre plus la distance. 

            if self.autonomie < distance_1:
                stop_coord.append(list(trajet[i]))
                j = j + 1 # compte combien de fois l'autonomie a été saturée pour pénaliser 
                          # la distance_1 sur toutes les boucles à partir de là

        self.distance = distance 


        return distance, stop_coord
    
    def plot_stop_points(self, map):

        """

        ================================================================
        IDÉE : Fonction pour représenter graphiquement sur une carte les 
               points d'arrêt du réseau, en utilisant des marqueurs de 
               couleur violette.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        -map : Objet carte Folium sur laquelle les points d'arrêt seront 
               représentés.

        ================================================================

        ================================================================
        SORTIE : La carte Folium mise à jour avec des marqueurs violets 
                 représentant les points d'arrêts les plus proches.
        ================================================================

        """

        # Appel à la fonction distance_via_routes pour obtenir les distances et les coordonnées des points d'arrêt
        distance, stop_coord = self.distance_via_routes()

        # Itération sur chaque point d'arrêt
        for i in range(len(stop_coord)):
            lat = stop_coord[i][0]
            lon = stop_coord[i][1]


            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(icon=f'{i}', prefix='fa', color='purple'),
                popup=f"Arrêt numéro {i} : vous devez recharger votre batterie.",
                tooltip=f"Arrêt numéro {i} : vous devez recharger votre batterie."
                ).add_to(map)
            
        

    def nearest_stations(self, stop_coord, distance_max): 

        """

        ================================================================
        IDÉE : Fonction qui identifie et renvoie les stations les plus 
               proches pour chaque point d'arrêt donné,dans une plage de 
               distance spécifiée.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        -stop_coord : Liste des coordonnées (latitude, longitude) des 
                      points d'arrêt. Tel que rendu par distance_via_routes

        -distance_max : Distance maximale (en kilomètres) à partir de 
                        laquelle une station est considérée comme "proche".
        ================================================================

        ================================================================
        SORTIE : Liste de listes, où chaque sous-liste représente les 
                 coordonnées des stations les plus proches pour un point 
                 d'arrêt donné.
        ================================================================

        """

        # Extraction des coordonnées des stations du DataFrame self.stations_data
        stations = self.stations_data[['Xlongitude', 'Ylatitude']]
        stations = stations[(stations['Ylatitude'] >= -90) & (stations['Ylatitude'] <= 90) &
            (stations['Xlongitude'] >= -90) & (stations['Xlongitude'] <= 90)]

        ## On récupère uniquement les données qui nous intéressent sous forme 
        # de tuple de localisations (latitude, longitude)   
        loc_tuples = [(row.Ylatitude, row.Xlongitude) for row in stations.itertuples()]
    
        ## on définit une lambda fonction qui prend en argument une distance, 
        # un couple (latitude, longitude) [dans coord] et un float distance_max
        # et qui teste si la distance entre location et coord est inférieure (renvoie
        # alors True) à la distance_max
        is_in_range = lambda location, coord, distance: geodesic(location, coord).kilometers <= distance


        ## On instancie une liste vide qu'on remplira des stations les plus proches pour chaque 
        # point d'arrêt
        nearest_stations = []
        for i in range(len(stop_coord)):

            location = stop_coord[i]
                   
            # Filtrage des stations qui sont dans la plage de distance pour le point d'arrêt actuel
            location_tuples = [list(element) for element in loc_tuples if is_in_range(location, element, distance_max)]

            # Ajout des stations filtrées à la liste des stations les plus proches
            nearest_stations.append(location_tuples)

        return nearest_stations
    
    def plot_nearest_stations(self, map, nearest_stations):

        """ 
        ================================================================
        IDÉE : Fonction permettant de représenter graphiquement sur une 
               carte toutes les stations les plus proches associées à des 
               points d'arrêt donnés.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        -map : objet de type folium map, tel que renvoyé par get_route_map
               ou plot_stop_points

        -nearest_stations : liste de longueur égale au nombre d'arrêt 
                            sur le trajet. Chaque élément correspond 
                            lui-même à une liste de liste contenant les 
                            localisations des stations les plus proches
        ================================================================

        ================================================================
        SORTIE : La carte Folium mise à jour avec des marqueurs représentant 
                 les stations les plus proches.
        ================================================================

        """
         
        df = self.stations_data
        for i in range(len(nearest_stations)):
    
            ## On récupère les localisations de toutes les bornes les 
            # plus proches du i-ème point d'arrêt 
            nearest_stations_i = nearest_stations[i]

            ## On itère sur cette première liste pour représenter toutes les
            # stations les plus proches 
            for j in range(len(nearest_stations_i)):
                lat = nearest_stations_i[j][0] ## longitude
                lon = nearest_stations_i[j][1] ##  latitude

                ## On essaie de déterminer si cette borne est payante ou non, 
                #  et son type d'accès
                result =  df[(df['Xlongitude'] == lon) & (df['Ylatitude'] == lat)]

                acces_type = result['acces_recharge'].unique()[0]

                folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='yellow'),
                popup=f"Ceci est l'une des {len(nearest_stations_i)} bornes les plus proches de l'arrêt numéro {i}. Son type est {acces_type}",
                tooltip=f"Ceci est l'une des {len(nearest_stations_i)} bornes les plus proches de l'arrêt numéro {i}. Son type est {acces_type}"
                ).add_to(map)


        def plot_nearest_stations(self, map, nearest_stations):

        """ 
        ================================================================
        IDÉE : Fonction permettant de représenter graphiquement sur une 
               carte toutes les stations les plus proches associées à des 
               points d'arrêt donnés.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        -map : objet de type folium map, tel que renvoyé par get_route_map
               ou plot_stop_points

        -nearest_stations : liste de longueur égale au nombre d'arrêt 
                            sur le trajet. Chaque élément correspond 
                            lui-même à une liste de liste contenant les 
                            localisations des stations les plus proches
        ================================================================

        ================================================================
        SORTIE : La carte Folium mise à jour avec des marqueurs représentant 
                 les stations les plus proches.
        ================================================================

        """
         
        df = self.stations_data
        for i in range(len(nearest_stations)):
    
            ## On récupère les localisations de toutes les bornes les 
            # plus proches du i-ème point d'arrêt 
            nearest_stations_i = nearest_stations[i]

            ## On itère sur cette première liste pour représenter toutes les
            # stations les plus proches 
            for j in range(len(nearest_stations_i)):
                lat = nearest_stations_i[j][0] ## longitude
                lon = nearest_stations_i[j][1] ##  latitude

                ## On essaie de déterminer si cette borne est payante ou non, 
                #  et son type d'accès
                result =  df[(df['Xlongitude'] == lon) & (df['Ylatitude'] == lat)]

                acces_type = result['acces_recharge'].unique()[0]

                folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='yellow'),
                popup=f"Ceci est l'une des {len(nearest_stations_i)} bornes les plus proches de l'arrêt numéro {i}. Son type est {acces_type}",
                tooltip=f"Ceci est l'une des {len(nearest_stations_i)} bornes les plus proches de l'arrêt numéro {i}. Son type est {acces_type}"
                ).add_to(map)

    def plot_stations(self, map):

        """ 
        ================================================================
        IDÉE : Fonction permettant de représenter graphiquement sur une 
               carte folium toutes les stations dont on dispose dans notre 
               base de données en attribut.
        ================================================================

        ================================================================
        PARAMÈTRES : 

        -map : objet de type folium map, tel que renvoyé par get_route_map
               ou plot_stop_points
        
        -idf : vaut par défaut True, indique si l'on représente uniquement 
               les bornes en Île-de-France

        -distance : vaut par défaut True, indique si l'on indique la distance
               sur la carte

        ================================================================

        ================================================================
        SORTIE : La carte Folium mise à jour avec des marqueurs représentant 
                 toutes les stations de recharge de véhicules électrique en 
                 France.
        ================================================================

        """
        # On s'assure self.distance is défini avant de l'utiliser
        if self.distance is None:
            # If not set, calculate it
            self.distance, _ = self.distance_via_routes()

        # On récupère les données sur lesquelles on travaille, 
        # puisque l'on a restreint notre travail à l'Île-de-France, il 
        # faut restreindre le dataframe que l'on utilise aux bornes situées en 
        # Île-de-France. 

        #### Étape 1 : charger le dataframe contenant les localisations des limites de l'Île-de-France ####
        # URL du fichier GeoJSON
        geojson_url = 'https://france-geojson.gregoiredavid.fr/repo/regions/ile-de-france/region-ile-de-france.geojson'

        # Charger le GeoDataFrame à partir de l'URL
        gdf = gpd.read_file(geojson_url)

        # Extraire les coordonnées de tous les points du polygone dans une colonne 'Coordinates'
        gdf['Coordinates'] = gdf['geometry'].apply(lambda x: list(x.exterior.coords))

        # Créer une liste de toutes les coordonnées
        all_coords = [coord for sublist in gdf['Coordinates'] for coord in sublist]

        # Créer un DataFrame à partir de la liste de toutes les coordonnées
        df1 = pd.DataFrame(all_coords, columns=['Longitude', 'Latitude'])

        #### Étape 2 : récupérer les coordonnées de toutes les bornes en France
        df2 = self.stations_data[['Xlongitude', 'Ylatitude']]

        # On renomme les colonnes pour rendre les choses plus commodes
        df2.rename(columns={'Xlongitude': 'Longitude', 'Ylatitude': 'Latitude'}, inplace=True)
        
        # On inclut une qui vérifie si les bornes sont dans la région 
        # et renvoie un dataframe contenant toutes les localisations des
        # bornes en Île-de-France 

        def bornes_dans_region(df1, df2):
            def point_inside_polygon(x, y, poly):
                n = len(poly)
                inside = False
                p1x, p1y = poly[0]
                for i in range(1, n + 1):
                    p2x, p2y = poly[i % n]
                    if y > min(p1y, p2y):
                        if y <= max(p1y, p2y):
                            if x <= max(p1x, p2x):
                                if p1y != p2y:
                                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                    if p1x == p2x or x <= xinters:
                                        inside = not inside
                    p1x, p1y = p2x, p2y
                return inside
            
            # Convertir les frontières en une liste de tuples
            region_poly = list(zip(df1['Latitude'], df1['Longitude']))
            
            # Filtrer les bornes électriques qui sont à l'intérieur de la région
            df3 = df2[[point_inside_polygon(lat, lon, region_poly) for lat, lon in zip(df2['Latitude'], df2['Longitude'])]]
            
            return df3

        # On applique cette fonction pour récupérer les bornes qui nous intéressent
        df3 = bornes_dans_region(df1, df2) 

        # Finalement, on ne garde que les données de ces bornes 
        df = self.stations_data.loc[df3.index]
        distance = float(self.distance)

        legend_html = f"""
                <div style="position: fixed; 
                            top: 10px; 
                            right: 10px; 
                            width: 220px; 
                            background-color: rgba(255, 255, 255, 0.8); 
                            border: 2px solid #000; 
                            border-radius: 5px; 
                            box-shadow: 3px 3px 5px #888; 
                            z-index: 1000; padding: 10px; font-size: 14px; font-family: Arial, sans-serif;">
                    <p style="text-align: center; font-size: 18px;"><strong>Légende de la Carte</strong></p>
                    
                    <p><i class="fa fa-stop" style="color: red; font-size: 20px;"></i> <strong>Payant</strong></p>
                    
                    <p><i class="fa fa-stop" style="color: green; font-size: 20px;"></i> <strong>Gratuit</strong></p>
                    
                    <p><i class="fa fa-stop" style="color: grey; font-size: 20px;"></i> <strong>Informations manquantes</strong></p>
                    
                    <p><i class="fa fa-stop" style="color: cyan; font-size: 20px;"></i> <strong>Carte ou badge</strong></p>
                    
                    <p><i class="fa fa-stop" style="color: yellow; font-size: 20px;"></i> <strong>Gratuit de 12-14h et de 19h-21h</strong></p>
                    
                    <p><i class="fa fa-map-marker" style="color: purple; font-size: 20px;"></i> <strong>Points d'arrêt</strong></p>

                    Distance du trajet : <strong> {distance:.2f} km</strong> <br> 
                </div>
        """

        # Ajoutez la légende personnalisée à la carte
        map.get_root().html.add_child(folium.Element(legend_html))

        ## C.f. la documentation folium disponible ici pour justifier l'exemple 
        ## 'https://python-visualization.github.io/folium/latest/user_guide/plugins/tag_filter_button.html'

        for index, lat, lon, com, acces_recharge in df[['Ylatitude', 'Xlongitude', 'n_station', 'acces_recharge']].itertuples():
            # Créez un marqueur avec une couleur différente en fonction des valeurs
            if acces_recharge == 'payant' : fill_color = 'red'
            elif acces_recharge == 'gratuit' : fill_color = 'green'
            elif acces_recharge == 'information manquante' : fill_color = 'grey'
            elif acces_recharge == 'carte ou badge' : fill_color = 'cyan'
            elif acces_recharge == 'charges gratuites de 12 à 14h et de 19h à 21h' : fill_color = 'yellow'

            # Ajoutez le marqueur à la carte

            folium.RegularPolygonMarker(
                location=[lat, lon],
                popup = com,
                tooltip = com,
                fill_color = fill_color,
                color = fill_color,# Couleur des contours du polygone                    rotation=45,
                radius = 5  # Opacité du remplissage
            ).add_to(map)

    def plot_accidents(self, map, path):

        # Charge les données du fichier Excel dans un DataFrame nommé accidents_2022idf_carac

        accidents_2022idf_carac = pd.read_excel(path)

        # Remplace les virgules par des points et convertit la colonne "Latitude" en flottants
        accidents_2022idf_carac["Latitude"] = accidents_2022idf_carac["Latitude"].str.replace(',','.').astype(float)

        # Remplace les virgules par des points et convertit la colonne "Longitude" en flottants
        accidents_2022idf_carac["Longitude"] = accidents_2022idf_carac["Longitude"].str.replace(',','.').astype(float)

        # on trie les données d'accident en fonction de leur localisation
        dict_accidents_2022idf = accidents_2022idf_carac.groupby(["Commune", "Adresse"]).groups
        # on trie le dictionnaire obtenu
        dict_trie_accidents_2022idf = dict(sorted(dict_accidents_2022idf.items(), key=lambda item : len(item[1]), reverse=True))

        # on affiche les 25 localisations avec le plus d'accidents en Idf
        i = 0
        for key in dict_trie_accidents_2022idf.keys():
            list1 = []
            for elem in dict_trie_accidents_2022idf[key]:
                list1.append(accidents_2022idf_carac.iloc[elem]["Latitude"])
                m1, m2 = list1.index(min(list1)), list1.index(max(list1))
                # on affiche une ligne entre les points les plus éloignés
            coord_ligne1 = [accidents_2022idf_carac.iloc[dict_trie_accidents_2022idf[key][m1]]['Longitude'], accidents_2022idf_carac.iloc[dict_trie_accidents_2022idf[key][m1]]['Latitude']]
            coord_ligne2 = [accidents_2022idf_carac.iloc[dict_trie_accidents_2022idf[key][m2]]['Longitude'], accidents_2022idf_carac.iloc[dict_trie_accidents_2022idf[key][m2]]['Latitude']]
            folium.PolyLine([coord_ligne1, coord_ligne2],
                            popup=key,
                            weight = 0.7 * len(dict_trie_accidents_2022idf[key] / len(dict_trie_accidents_2022idf[('93066 - Saint-Denis','AUTOROUTE A1')]))
                            ).add_to(map)
            i = i+1
            if i > 25:
                break

    def cout_distance_thermique(self, prix_essence, essence = True):
        """ 
        Parameters:
        -----------
        dist : une distance (en kilomètres)
        prix_essence : prix de l'essence à une date t (exemple : 1.8€/l)
        essence : True par défaut (si False, signifie que c'est un véhicule Diesel)
        -----------
        N.B : 
        En 2021, une voiture particulière essence consommait en moyenne 7,54 litres pour parcourir 100 kilomètres 
        contre 6,11 pour les voitures diesel.
        -----------
        return : 
        -----------
        coût pour parcourir la distance 
        """

        prix_essence = 1.85

        distance, _ = self.distance_via_routes()

        if essence == True: 
            conso_100k = 7.54  #nombre de litre consommé par le véhicule à essence sur 100km  
            
        else: 
            conso_100k = 6.11  #nombre de litre consommé par le véhicule disesel sur 100km 
        
        nb_litre_trajet = (distance * conso_100k) / 100  #nombre de litre consommé par le véhicule sur la distance dist 
        cout_trajet = nb_litre_trajet * prix_essence  #coût du trajet 
        
        return cout_trajet 