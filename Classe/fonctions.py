# Imports 
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from pyroutelib3 import Router

# Bornes 
URL = 'https://www.data.gouv.fr/fr/datasets/r/517258d5-aee7-4fa4-ac02-bd83ede23d25'
df_bornes = pd.read_csv(URL, sep = ';')


def clean_df(dataframe):
    """
    Fonction qui permet de nettoyer le dataframe des bornes de recharges électriques.
    On supprime les lignes où les coordonnées sont aberrantes et les lignes où les
    coordonnées sont manquantes.

    Liste de points extrêmes de la France Métropolitaine (Wikipedia : https://fr.wikipedia.org/wiki/Liste_de_points_extrêmes_de_la_France):
    - nord : Bray-Dunes, Nord (51.0891, 2.5729) ;
    - est : Lauterbourg, Bas-Rhin (48.9673, 8.2581) ;
    - sud : Puig de Coma Negra, Lamanère, Pyrénées-Orientales (42.3327, 2.5603) ;
    - ouest : pointe de Corsen, Plouarzel, Finistère (48.4129, -4.7681).
    
    Parameters:
    ----------- 
    dataframe : dataframe des bornes de recharges électriques
    """
    liste = []
    for row in dataframe.itertuples():
        if (row.Ylatitude < 40 or row.Ylatitude > 55) or (row.Xlongitude < -5 or row.Xlongitude > 10):
            liste.append(row.Index)
    df_bornes = dataframe.drop(liste)
    droping_liste = list(set(df_bornes[df_bornes['Xlongitude'].isna()].index.to_list() + df_bornes[df_bornes['Ylatitude'].isna()].index.to_list()))
    df = df_bornes.drop(droping_liste)
    return df


def coor_cp(df_code, code_postale):
    """
    Fonction qui permet de récupérer les coordonnées d'un code postal.
    
    Parameters:
    -----------
    df_code : dataframe des codes postaux
    code_postale : code postal dont on veut les coordonnées
    """
    for row in df_code.itertuples():
        cp = row.code_postal
        if code_postale == cp:
            lat = row.latitude
            lon = row.longitude
            return [lat, lon]
    return None


def recherche_station_proche(df, dist, lat, lon):
    """
    Recherche la station la plus proche dans un périmètre donné.

    Parameters:
    - df (DataFrame): DataFrame contenant les stations avec les colonnes 'xlongitude', 'ylatitude' et 'n_enseigne'.
    - dist (float): Distance maximale en kilomètres pour rechercher une station.
    - lat (float): Latitude du point de départ.
    - lon (float): Longitude du point de départ.

    Returns:
    - tuple: (lat, lon, nom) de la station la plus proche ou None si aucune station n'est trouvée.
    """
    # Conversion des coordonnées en float
    lat, lon = float(lat), float(lon)

    # Filtrer les lignes valides avec des coordonnées non manquantes
    df_valid = df.dropna(subset=['xlongitude', 'ylatitude'])

    # Calculer les distances pour chaque station
    df_valid['distance'] = df_valid.apply(lambda row: geodesic((lat, lon), (row['ylatitude'], row['xlongitude'])).km, axis=1)

    # Trouver la station avec la distance minimale
    station_proche = df_valid[df_valid['distance'] <= dist].nsmallest(1, 'distance')

    if station_proche.empty:
        return None

    # Extraire les informations de la station la plus proche
    lat_station = station_proche['ylatitude'].values[0]
    lon_station = station_proche['xlongitude'].values[0]
    nom_station = station_proche['n_enseigne'].values[0]

    return lat_station, lon_station, nom_station


def trajet(départ, fin):
    """
    Retourne une liste de longitude et 
    de latitude correspondant à la route à suivre pour rejoindre `fin` depuis `départ`.
    Les points de départ et d'arrivée sont définis par leurs coordonnées respectives (latitude, longitude).

    Arguments :
    - départ (tuple) : Coordonnées (latitude, longitude) du point de départ.
    - fin (tuple) : Coordonnées (latitude, longitude) du point d'arrivée.

    Retourne :
    - Trajet_lat (list) : Liste des latitudes des points du trajet.
    - Trajet_lon (list) : Liste des longitudes des points du trajet.
    - total (float) : Distance totale du trajet en kilomètres.
    """
    # Initialisation des listes de latitudes et longitudes
    Trajet_lat = []
    Trajet_lon = []
    total = 0
    
    # Initialisation du routeur pour un trajet en voiture
    router = Router('car')
    
    # Recherche des nœuds les plus proches des points de départ et d'arrivée
    start = router.findNode(départ[0], départ[1])
    end = router.findNode(fin[0], fin[1])
    
    # Calcul de l'itinéraire
    status, route = router.doRoute(start, end)
    
    if status == 'success':
        # Conversion des nœuds en coordonnées (latitude, longitude)
        routeLatLons = [router.nodeLatLon(node) for node in route]
        
        # Séparation des latitudes et longitudes
        Trajet_lat = [lat for lat, lon in routeLatLons]
        Trajet_lon = [lon for lat, lon in routeLatLons]
        
        # Calcul de la distance totale
        for i in range(len(routeLatLons) - 1):
            d = geodesic(routeLatLons[i], routeLatLons[i + 1]).km
            total += d
    else:
        print("Erreur : Itinéraire non trouvé.")
    
    return Trajet_lat, Trajet_lon, total


def trajet_electrique(trajet_thermique_lat, trajet_thermique_lon, autonomie):
    """
    Calcule le trajet pour un véhicule électrique en tenant compte de l'autonomie.
    
    Parameters:
    - trajet_thermique_lat (list): Liste des latitudes du trajet initial (thermique).
    - trajet_thermique_lon (list): Liste des longitudes du trajet initial (thermique).
    - autonomie (float): Autonomie du véhicule en kilomètres.

    Returns:
    - tuple: (trajet_lat, trajet_lon, total) où :
        - trajet_lat (list): Liste des latitudes du trajet adapté pour électrique.
        - trajet_lon (list): Liste des longitudes du trajet adapté pour électrique.
        - total (float): Distance totale parcourue.
    """
    trajet_lat = []
    trajet_lon = []
    distance_parcourue = 0
    total_distance = 0
    router = Router('car')

    def ajouter_segment(route_lat_lons):
        """Ajoute un segment de route au trajet et calcule la distance parcourue."""
        nonlocal distance_parcourue
        for i in range(len(route_lat_lons) - 1):
            dep_lat, dep_lon = route_lat_lons[i]
            fin_lat, fin_lon = route_lat_lons[i + 1]

            trajet_lat.extend([dep_lat, fin_lat])
            trajet_lon.extend([dep_lon, fin_lon])

            segment_distance = geodesic((dep_lat, dep_lon), (fin_lat, fin_lon)).km
            distance_parcourue += segment_distance

    for k in range(len(trajet_thermique_lat) - 1):
        if distance_parcourue <= autonomie * 0.7:
            start_lat, start_lon = trajet_thermique_lat[k], trajet_thermique_lon[k]
            end_lat, end_lon = trajet_thermique_lat[k + 1], trajet_thermique_lon[k + 1]

            start = router.findNode(start_lat, start_lon)
            end = router.findNode(end_lat, end_lon)
            status, route = router.doRoute(start, end)

            if status == 'success':
                route_lat_lons = list(map(router.nodeLatLon, route))
                ajouter_segment(route_lat_lons)
        else:
            station = recherche_station_proche(df_bornes, autonomie * 0.3, trajet_thermique_lat[k], trajet_thermique_lon[k])
            if station is None:
                return None
            
            station_lat, station_lon, _ = station

            # Aller jusqu'à la station de recharge
            start = router.findNode(trajet_thermique_lat[k], trajet_thermique_lon[k])
            end = router.findNode(station_lat, station_lon)
            status, route = router.doRoute(start, end)

            if status == 'success':
                route_lat_lons = list(map(router.nodeLatLon, route))
                ajouter_segment(route_lat_lons)

            # Revenir sur le trajet initial
            start = router.findNode(station_lat, station_lon)
            end = router.findNode(trajet_thermique_lat[k], trajet_thermique_lon[k])
            status, route = router.doRoute(start, end)

            if status == 'success':
                route_lat_lons = list(map(router.nodeLatLon, route))
                ajouter_segment(route_lat_lons)

            total_distance += distance_parcourue
            distance_parcourue = 0

    total_distance += distance_parcourue
    return trajet_lat, trajet_lon, total_distance

