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