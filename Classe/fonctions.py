# Imports 
import pandas as pd
import numpy as np

# Bornes 
URL = 'https://www.data.gouv.fr/fr/datasets/r/517258d5-aee7-4fa4-ac02-bd83ede23d25'
df_bornes = pd.read_csv(URL, sep = ';')

def clean_df(dataframe):
    """
    Fonction qui permet de nettoyer le dataframe des bornes de recharges électriques.
    On supprime les lignes où les coordonnées sont aberrantes et les lignes où les
    coordonnées sont manquantes.
    
    Parameters:
    ----------- 
    dataframe : dataframe des bornes de recharges électriques
    """
    liste = []
    for row in dataframe.itertuples():
        if row.Xlongitude > 90 or row.Ylatitude > 90:
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



