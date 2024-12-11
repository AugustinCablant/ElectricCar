# Imports 
import pandas as pd
import math
from geopy.distance import geodesic
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
import datetime
import pyroutelib3
from pyroutelib3 import Router
import requests, json
import folium 
from CarNetwork import CarNetwork


# Bornes 
URL = 'https://www.data.gouv.fr/fr/datasets/r/517258d5-aee7-4fa4-ac02-bd83ede23d25'
df_bornes = pd.read_csv(URL, sep = ';')

def clean_df(dataframe):
    liste = []
    for row in dataframe.itertuples():
        if row.xlongitude > 90 or row.ylatitude > 90:
            liste.append(row.Index)
    df_bornes = dataframe.drop(liste)
    droping_liste = list(set(df_bornes[df_bornes['xlongitude'].isna()].index.to_list() + df_bornes[df_bornes['ylatitude'].isna()].index.to_list()))
    df = df_bornes.drop(liste)
    return df

def coor_cp(df_code, code_postale):
    for row in df_code.itertuples():
        cp = row.code_postal
        if code_postale == cp:
            lat = row.latitude
            lon = row.longitude
            return [lat, lon]
    return None
