from flask import Flask

cwd=os.getcwd()
cwd_parent = (os.path.dirname(cwd))

car_network_directory = '/ElectricCar/Classe' 
#cwd_parent + '/Modules' 
sys.path.append(car_network_directory)


app = Flask(__name__)
