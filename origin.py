
import os
import falcon
import vincent
import json
import pandas
import db
import socket
import pycountry
from geoip import geolite2
from vincent import values
from jinja2 import Environment, PackageLoader

#IP = "45.33.70.211"

def get_local_ip():
	return socket.gethostbyname(socket.gethostname())

class TopoResource(object):

    # backend REST call to get country base topo data
    def on_get(self, req, resp):

        resp.status = falcon.HTTP_200
        data_file = "world-countries.topo.json"
        with open(os.path.join('data', data_file)) as data:
            resp.body = data.read()

class PopulationResource(object):

    # backend REST call that serves the rendered data as json
    def on_get(self, req, resp):

        data_file = "world.json"
        with open(data_file) as data:
            resp.body = data.read()

class CoreResource(object):
    """
        Implements application logic to visualize country of origin for all site visitors.
		User's IP is determined, used to lookup their country of origin, then db is updated.
		All visitor data is then used to populate a world map with appropriate coloring.
    """

	def __init__(self):

        html_file = 'index.html'
        self.geo_data = [{
             'name': 'countries',
             'url': "http://%s/core" % get_local_ip,
             'feature': 'world-countries'}]

    def insert_user(self, remote_ip):
		
		match = geolite2.lookup(remote_ip)
        if match:
            # normalize theISO-3666 alpha2 country code -> alpha3
            country = pycountry.countries.get(alpha2=match.country).alpha3
            # add to db
            connection_info = db.RemoteConnection(remote_ip, country, match.continent, match.timezone, str(list(match.subdivisions)))
            db.upsert_connection(connection_info)
        else:
            print("No country match found for %s" % remote_ip)
	
    def on_get(self, req, resp):
         
		# lookup this client and put them in the db
		remote_ip = req.env['REMOTE_ADDR']
		client_location = insert_user(remote_ip)

	   # grab topo data
        with open(os.path.join('data', 'world-countries.topo.json'), 'r') as fi:
            topo_data = json.load(fi)
		
        # build a list of visit counts for all the countries ex. [1, 5, 0, 7, ...] 
		counts = db.get_country_counts()		
        countries = [country['id'] for country in topo_data['objects']['world-countries']['geometries']]
		
		# align the count of visits of visits from each country to the country order from the topo data
        aligned_counts = []
        for country in countries:
            if counts.get(country):
                aligned_counts.append(counts.get(country))
            else:
               aligned_counts.append(0)

        # join the list of countries with the list of counts in a dataframe
        df = pandas.DataFrame({"COUNTRY": countries, "COUNT": aligned_counts})

        # render the visualization
        vis = vincent.Map(data=df, geo_data=self.geo_data, scale=150, projection='cylindricalStereographic',
            data_bind="COUNT", data_key="COUNTRY", map_key={'countries': "id"})

        # alter some map properties
        max_value = max(counts.values()) if counts else 1
        vis.scales['color'].domain = [0, 6]
        vis.marks[0].properties.enter.stroke_opacity = values.ValueRef(value=0.5)
        
        # export visualization as json
        vis.to_json("world.json")

		# grab some interesting stats from the db
        visits = db.count_connections()[0]
        countries = db.count_countries()[0]
        
        # set response data
		resp.status = falcon.HTTP_200
        resp.content_type = "text/html; charset=utf-8"
        resp.body = env.get_template(self.html_file).render(total_visits=visits, unique_countries=countries)


# setup jinja for html template substitution
env = Environment(loader=PackageLoader('origin', 'templates'))

# run the app
app = falcon.API()
topo = TopoResource()
pop = PopulationResource()
core = CoreResource()
app.add_route('/core', topo)
app.add_route('/world.json', pop)
app.add_route('/world', core)
