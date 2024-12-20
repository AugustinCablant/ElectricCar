from flask import Flask, render_template, request
from CarNetwork import CarNetwork

cwd=os.getcwd()
cwd_parent = (os.path.dirname(cwd))

car_network_directory = '/ElectricCar/Classe' 
#cwd_parent + '/Modules' 
sys.path.append(car_network_directory)


app = Flask(__name__)

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
