from flask import Flask, render_template, request
import os
import sys
from dash import html
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from CarNetwork import CarNetwork
from graphiques import evolution_nbre_voiture_elec, graph_html_pol_par_activité, bornes_region,evol_accidents
import pyroutelib3


cwd=os.getcwd()
cwd_parent = (os.path.dirname(cwd))

car_network_directory = '/ElectricCar/Classe' 
#cwd_parent + '/Modules' 
sys.path.append(car_network_directory)


app = Flask(__name__)
@app.route('/calcul', methods=['POST'])
def calcul():
    """ 
    Permet de déterminer et retourner l'itinéraire.
    """
    destination = request.form['destination']
    depart = request.form['depart']
    autonomie = int(request.form['autonomie'])

    # Passons à la visualisation 
    reseau = CarNetwork(depart, destination, autonomie)  #On initialise un objet de la classe CarNetwork
    reseau.clean_data()  # On nettoie les données à l'aide de la méthode .clean_data()
    reseau.get_coordo()
    trajet = reseau.trajet_voiture()
    map1 = reseau.get_route_map()
    distance, stop_coord = reseau.distance_via_routes()
    reseau.plot_stop_points(map1)
    distance_max = autonomie
    nearest_stations = reseau.nearest_stations(stop_coord, distance_max)
    reseau.plot_nearest_stations(map1, nearest_stations)
    reseau.plot_stations(map1)
    carte_html = map1.get_root().render()

    # Renvoyer le contenu du fichier HTML via render_template
    return render_template('resultat.html', donnees=carte_html)

@app.route("/evolution_electrique")
def page_suivante1():
    def graph_intro():
        df = evolution_nbre_voiture_elec()
        plt.figure(figsize=(10, 6))
        plt.plot(df['Date'], df['Nombre'], label='Évolution du parc de véhicules électriques en France', color='blue', marker='o')
        plt.xlabel('Date')
        plt.ylabel('Nombre de véhicules électrique en France (x1e6)')
        plt.xticks(rotation=45)  # Rotation des étiquettes de l'axe des x pour rendre les dates plus lisibles
        plt.legend()
        plt.fill_between(df['Date'], df['Nombre'], color='lightgray', alpha=0.7)  # Fond gris clair
        plt.title('Évolution du parc de véhicules électriques en France', fontsize=16)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()  # Pour éviter que les étiquettes de l'axe des x ne se chevauchent
        img_data = BytesIO()  # Conversion du graphique en image base64
        plt.savefig(img_data, format='png')
        img_data.seek(0)
        img_base64 = base64.b64encode(img_data.read()).decode()
        graph_html = f'<img src="data:image/png;base64,{img_base64}" alt="Graphique d\'autonomie">'  # Code HTML pour afficher le graphique
        return graph_html
    get_graph = graph_intro()
    return render_template("evolution_electrique.html", graph = get_graph)

@app.route("/contextualisation")
def contextualisation():
  return render_template("contextualisation.html", graph = 'Static/IEA.jpeg')

@app.route("/bornes")
def page_suivante2():
  return render_template("map_bornes.html")

@app.route("/pol_par_activité")
def page_suivante3():
  get_graph = graph_html_pol_par_activité()
  return render_template("pol_par_activité.html", graph = get_graph)

@app.route("/bornes_region")
def page_suivante4():
  get_graph = bornes_region()
  return render_template("bornes_region.html", graph = get_graph)

@app.route("/evol_acc")
def page_suivante5():
  get_graph = evol_accidents()
  return render_template("evol_accidents.html", graph = get_graph)

@app.route('/EDA')
def EDA():
  return render_template("EDA_html.html")

@app.route('/')
def accueil():
  """
  Permet d'afficher la page d'accueil.
  """
  return render_template("index.html")

# Lancer l'application avec le terminal
"""
cd #chemin
python app.py
copier le chemin et le coller dans le navigateur
"""
if __name__ == '__main__':
    app.run(debug=True)
