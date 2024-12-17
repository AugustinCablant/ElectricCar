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