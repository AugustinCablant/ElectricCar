# ElectricCar

## Project Overview
This project focuses on optimizing routes for electric vehicles (EVs) within France, with a special emphasis on the Île-de-France region. By integrating the availability of charging stations, the solution ensures that EV drivers can travel efficiently, with charging stops strategically planned. This project is developed as part of the *"Infrastructures and Software Systems"* course.

## Context
In the context of rapidly growing electric mobility, our route calculator goes beyond traditional solutions by incorporating the locations of EV charging stations across France. You can access the dataset of charging stations [here](https://www.data.gouv.fr/fr/datasets/bornes-de-recharge-pour-vehicules-electriques-3/). 

Our goal is to facilitate and optimize EV drivers' journeys by ensuring an efficient and stress-free driving experience. By embarking on this project, we aim to contribute to reducing carbon emissions by promoting clean transportation solutions. EVs, powered by renewable energy sources, reduce our reliance on fossil fuels and minimize the carbon footprint.

### Challenges Addressed
Currently, one of the major challenges for EV drivers is planning trips that take into account the availability of charging stations. Range anxiety, the fear of running out of battery during a trip, remains a key barrier to the adoption of electric mobility. 

Our project tackles this issue by offering an intelligent tool that integrates real-time data on charging station locations to provide optimal routes for EV drivers.

### Benefits of the Project
- **Reducing Range Anxiety:** By providing real-time information on charging stations, our route calculator reassures drivers about the availability of charging points, enhancing their confidence.
- **Encouraging EV Adoption:** By simplifying trip planning, our project promotes the adoption of EVs, making electric mobility a convenient and worry-free option.
- **Contributing to Sustainability:** By optimizing routes, we reduce the environmental impact, ensure efficient use of charging infrastructure, and decrease reliance on traditional fuel-powered vehicles.

## Features
- **Dynamic Route Optimization:** Calculates the most efficient route for EVs while considering the locations of charging stations.
- **Integration of Real-Time Data:** Uses up-to-date data from French charging stations to ensure route accuracy and relevance.
- **User-Centric Design:** Provides EV drivers with easy-to-understand and actionable route plans.

## Data Source
This project leverages the official dataset of EV charging stations in France, provided by [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/bornes-de-recharge-pour-vehicules-electriques-3/). 

## Installation and Usage
1. Clone the repository:
```bash
   git clone https://github.com/YourUsername/ElectricCar.git
```
2. Install dependencies: 
```bash
pip install -r requirements.txt
```
3. Run the project:
```bash
python App.py
```
While choosing the starting point and destination, specify the street adress as : number of the street, name of the street, area code.
Basically you should be able to copy it from a Google Maps result.

## Contributors
- Augustin CABLANT
- Romain DELHOMMAIS
- Guilhem GRIVAUX
- Quentin MARRET
- Nathan VAN ASSCHE


## License
This project is licensed under the MIT License. See the LICENSE file for more details.


**Together, let's make electric mobility more accessible and sustainable!** 
