import pandas as pd
from pyproj import Proj, transform
import folium
from CarNetwork import CarNetwork



class Autoroute(CarNetwork):
    """
    Classe Autoroute permettant de traiter et visualiser les gares de péage du réseau routier national.
    
    Attributs:
        - A, B : Paramètres hérités de CarNetwork.
        - autonomie : Autonomie héritée de CarNetwork.
        - stations_peages : DataFrame contenant les données des stations de péages.
    """

    def __init__(self, A, B, autonomie):
        super().__init__(A, B, autonomie)
        self.stations_peages = pd.read_csv(
            'https://static.data.gouv.fr/resources/gares-de-peage-du-reseau-routier-national-concede/20230728-163544/gares-peage-2023.csv',
            sep=';'
        )

    def clean_base(self):
        """
        Nettoie et transforme les données des stations de péages :
        - Conversion des coordonnées Lambert93 en coordonnées géographiques (latitude, longitude).
        - Filtre les données incorrectes (latitude > 90 ou longitude > 90).
        """
        
        # Conversion des colonnes 'x' et 'y' de string à float
        self.stations_peages['x'] = self.stations_peages['x'].str.replace(',', '.').astype(float)
        self.stations_peages['y'] = self.stations_peages['y'].str.replace(',', '.').astype(float)

        # Fonction interne pour convertir Lambert93 en lat/lon
        def lambert93_to_latlon(x, y):
            in_proj = Proj(init='epsg:2154')  # Lambert 93
            out_proj = Proj(init='epsg:4326')  # WGS84
            lon, lat = transform(in_proj, out_proj, x, y)
            return lat, lon

        # Application de la conversion sur les colonnes x et y
        self.stations_peages[['ylatitude', 'xlongitude']] = self.stations_peages.apply(
            lambda row: pd.Series(lambert93_to_latlon(row['x'], row['y'])), axis=1
        )

        # Renommage des colonnes
        self.stations_peages.rename(columns={'x': 'lambert93_x', 'y': 'lambert93_y'}, inplace=True)

        # Filtrage des coordonnées invalides
        invalid_coords = (self.stations_peages['xlongitude'] > 90) | (self.stations_peages['ylatitude'] > 90)
        self.stations_peages = self.stations_peages[~invalid_coords]

    def plot_peages_autoroutes(self, map):
        """
        Ajoute des marqueurs des stations de péages sur une carte Folium.
        
        Paramètres :
            - map : Carte Folium existante.
        """
        if 'xlongitude' not in self.stations_peages.columns or 'ylatitude' not in self.stations_peages.columns:
            raise ValueError("Assurez-vous d'avoir appelé la méthode clean_base() avant de visualiser les données.")
        
        # Filtre des stations associées aux autoroutes
        df_autoroutes = self.stations_peages[self.stations_peages['route'].str.startswith('A')]

        # Ajout des marqueurs sur la carte
        for _, row in df_autoroutes.iterrows():
            folium.RegularPolygonMarker(
                location=[row['xlongitude'], row['ylatitude']],
                color='blue',
                radius=5
            ).add_to(map)
