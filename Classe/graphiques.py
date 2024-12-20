import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime 
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def evolution_nbre_voiture_elec():
    df = pd.read_csv('Data/Voitures.csv', sep=';')
    List_date = []
    List_nombre = []

    for row in df.itertuples():
        date0 = row.date_arrete
        date = datetime.strptime(date0, "%d/%m/%Y").strftime("%Y-%m-%d")
        nbre = row.nb_vp_rechargeables_el
        if date in List_date:
            for i in range(len(List_date)):
                if List_date[i] == date:
                    List_nombre[i] += nbre
        else:
            List_date.append(date)
            List_nombre.append(nbre)

    dict = {'Date': List_date, 'Nombre': List_nombre}

    dataframe = pd.DataFrame(dict)
    return dataframe.sort_values('Date') 

def graph_html_pol_par_activité():
    URL = "https://www.insee.fr/fr/statistiques/fichier/2015759/deve-envir-emissions-co2.xlsx"
    df = pd.read_excel(URL)
    
    def transform(dataset):
        colonnes = ['Émissions de gaz à effet de serre par activité'] + [ f'{i}' for i in range(1990,2023)]
        dataset.set_axis(colonnes, axis=1, inplace=True)
        dataset = dataset[3:11].reset_index()
        dataset.drop('index', axis=1, inplace = True)
        return dataset
    df = transform(df)

    # Tracer l'évolution 
    plt.figure(figsize=(8,6))
    sns.set(style="whitegrid")
    palette = sns.color_palette("husl", n_colors=7)
    colonnes = df.columns.to_list()[1:]
    colonnes_int = [int(x) for x in colonnes]

    for i in df.index.to_list():
        if i<7:
            nom = df['Émissions de gaz à effet de serre par activité'][i]
            evol = [df[col][i] for col in colonnes]
            #evol = df[colonnes][i:i+1].values
            plt.plot(colonnes_int, evol, label = f'{nom}', color = palette[i])
        else:
            pass
    plt.xlabel('Année')
    plt.ylabel('en millions de tonnes d’équivalent CO₂')
    plt.title('Évolution des émissions de gaz à effet de serre par activité')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    img_data = BytesIO()  # Conversion du graphique en image base64
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode()
    graph_html = f'<img src="data:image/png;base64,{img_base64}" alt="Graphique d\'autonomie">'  # Code HTML pour afficher le graphique
    return graph_html


def bornes_region():
    URL = 'https://www.data.gouv.fr/fr/datasets/r/517258d5-aee7-4fa4-ac02-bd83ede23d25'
    df = pd.read_csv(URL, sep = ';')
    bornes_region = df['region'].value_counts().reset_index()  # On compte le nombre de bornes par région
    bornes_region.columns = ['region', 'nombre de bornes']
    bornes_region = bornes_region.sort_values(by='nombre de bornes', ascending=False)

    # On affiche cela dans un histogramme 
    plt.figure(figsize=(12, 6))
    plt.bar(bornes_region['region'], bornes_region['nombre de bornes'])
    plt.xlabel('Région')
    plt.ylabel('Nombre de bornes')
    plt.title('Nombre de bornes de recharge pour les véhicules électriques par région')
    plt.xticks(rotation=90)
    plt.tight_layout()
    img_data = BytesIO()  # Conversion du graphique en image base64
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode()
    graph_html = f'<img src="data:image/png;base64,{img_base64}" alt="Graphique d\'autonomie">'  # Code HTML pour afficher le graphique
    return graph_html

def evol_accidents():
    df_acc = pd.read_csv('Data/Evol_acc.csv').set_index('Année')
    df_acc = df_acc[1:]
    df_acc = df_acc.drop(['1981 et 1982'])
    df_acc['Accidents'] = df_acc['Accidents'].astype(int)
    plt.figure(figsize = (12, 8))
    df_sampled = df_acc[::4]
    plt.plot(df_acc.index, df_acc['Accidents'], marker='o', linestyle='-')
    plt.title('Évolution des accidents en France métropolitaine')
    plt.xlabel('Année')
    plt.xticks(df_sampled.index)
    plt.ylabel('Accidents')
    plt.legend(['Nombre d\'accidents'], loc='upper left')
    img_data = BytesIO()  # Conversion du graphique en image base64
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode()
    graph_html = f'<img src="data:image/png;base64,{img_base64}" alt="Graphique d\'autonomie">'
    return graph_html