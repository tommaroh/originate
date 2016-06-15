
import os
import falcon
import vincent
import json
import random
import pandas
import db
import jinja2
import pycountry
from geoip import geolite2
from vincent import values
from jinja2 import Environment, PackageLoader

TOPO_DATA = "world-countries.topo.json"
LIVE_DATA = "world.json"

class TopoDataResource(object):

    # backend REST call to get static country topo data
    def on_get(self, req, resp):

        resp.status = falcon.HTTP_200
        with open(os.path.join('data', TOPO_DATA)) as data:
            resp.body = data.read()

class LiveDataResource(object):

    # backend REST call that serves the rendered data as json
    def on_get(self, req, resp):

        with open(LIVE_DATA) as data:
            resp.body = data.read()

class CoreResource(object):

    """
    Implements application logic to visualize country of origin for all site visitors.
    User's IP is determined, used to lookup their country of origin, then db is updated.
    All visitor data is then used to populate a world map with appropriate coloring.
    """

    def __init__(self):
        
        self.html_file = 'index.html'

        # the source geo map
        self.geo_data = [{
             'name': 'countries',
             'url': "/topo",
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
            print("No match found for %s" % remote_ip)
 
    def get_local_topo(self):

        # grab the topo data
        with open(os.path.join('data', TOPO_DATA), 'r') as f:
            topo_data = json.load(f)
        return topo_data

    def get_country_counts(self):
        """
        Returns a tuple of ([country, county, ...], [vistor_count, visitor_count, ...])
        """

        # build a list of visit counts for all the countries ex. [1, 5, 0, 7, ...] 
        counts = db.get_country_counts()
        topo_data = self.get_local_topo()       
        countries = [country['id'] for country in topo_data['objects']['world-countries']['geometries']]

        # align the count of visits of visits from each country to the country order from the topo data
        aligned_counts = []
        for country in countries:
            if counts.get(country):
                print("Found: %s: %s" % (country, counts.get(country)))
                aligned_counts.append(counts.get(country))
            else:
               aligned_counts.append(0)

        return countries, aligned_counts
 
    def on_get(self, req, resp):

        # insert this user to the db
        remote_ip = req.env['REMOTE_ADDR']
        self.insert_user(remote_ip)
 
        # get a list of countries and a list of their visitor counts 
        countries, aligned_counts = self.get_country_counts()

        # join the list of countries with the list of counts in a pandas dataframe
        df = pandas.DataFrame({"COUNTRY": countries, "COUNT": aligned_counts})

        # render the visualization
        vis = vincent.Map(data=df, geo_data=self.geo_data, scale=150, projection='cylindricalStereographic',
            data_bind="COUNT", data_key="COUNTRY", map_key={'countries': "id"})

        # alter some map properties
        vis.scales['color'].domain = [0, 6]
        vis.marks[0].properties.enter.stroke_opacity = values.ValueRef(value=0.5)
        
        # export visualization as json
        # TODO a local temp file is used to store the user specific data, then later deleted (yuck)
        user_file = "%s.data" % remote_ip
        vis.to_json(user_file)
 
        # get some interesting stats from the db
        visits = db.count_connections()[0]
        countries = db.count_countries()[0]
 
        # set response
        resp.status = falcon.HTTP_200
        resp.content_type = "text/html; charset=utf-8"
        resp.body = env.get_template(self.html_file).render(total_visits=visits, unique_countries=countries)
        os.remove(user_file)


# setup jinja, for templating the html
env = Environment(loader=PackageLoader('origin', 'templates'))

# run the app
app = falcon.API()
topo = TopoDataResource()
live = LiveDataResource()
core = CoreResource()
app.add_route('/topo', topo)
app.add_route('/world.json', live)
app.add_route('/', core)

