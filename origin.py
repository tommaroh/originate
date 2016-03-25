
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

class CoreDataResource(object):

    def on_get(self, req, resp):

        resp.status = falcon.HTTP_200
        data_file = "world-countries.topo.json"
        with open(os.path.join('data', data_file)) as data:
            resp.body = data.read()

class LiveDataResource(object):

    def on_get(self, req, resp):

        data_file = "world.json"
        with open(data_file) as data:
            resp.body = data.read()

class CollectResource(object):

    def on_get(self, req, resp):

        html_file = 'index.html'
        resp.status = falcon.HTTP_200
        remote_ip = req.env['REMOTE_ADDR']
        match = geolite2.lookup(remote_ip)

        if match:
            # normalize theISO-3666 alpha2 country code -> alpha3
            country = pycountry.countries.get(alpha2=match.country).alpha3
            # add to db
            connection_info = db.RemoteConnection(remote_ip, country, match.continent, match.timezone, str(list(match.subdivisions)))
            db.upsert_connection(connection_info)
            counts = db.get_country_counts()

        else:
            counts = {}
            print("No match found")
         
        # build some data
        with open(os.path.join('data', 'world-countries.topo.json'), 'r') as f:
            data = json.load(f)
        
        # build a list of visit counts for all the countries ex. [1, 5, 0, 7, ...] 
        countries = [country['id'] for country in data['objects']['world-countries']['geometries']]
        aligned_counts = []
        for country in countries:
            if counts.get(country):
                print("Found: %s: %s" % (country, counts.get(country)))
                aligned_counts.append(counts.get(country))
            else:
               aligned_counts.append(0)

        # join the list of countries with the list of counts in a dataframe
        df = pandas.DataFrame({"COUNTRY": countries, "COUNT": aligned_counts})

        # the source geo map
        geo_data = [{
             'name': 'countries',
             'url': "/core",
             'feature': 'world-countries'}]

        # make the live map
        vis = vincent.Map(data=df, geo_data=geo_data, scale=150, projection='cylindricalStereographic',
            data_bind="COUNT", data_key="COUNTRY", map_key={'countries': "id"})

        # alter map properties
        max_value = max(counts.values()) if counts else 1
        vis.scales['color'].domain = [0, 6]
        vis.marks[0].properties.enter.stroke_opacity = values.ValueRef(value=0.5)
        
        # export map
        vis_file = remote_ip
        vis.to_json("world.json")

        # return html
        resp.content_type = "text/html; charset=utf-8"
        #with open(html_file) as html:
        #    resp.body = html.read()
        visits = db.count_connections()[0]
        countries = db.count_countries()[0]
        
        resp.body = env.get_template(html_file).render(total_visits=visits, unique_countries=countries)


# setup
env = Environment(loader=PackageLoader('origin', 'templates'))

# run the app
app = falcon.API()
core = CoreDataResource()
live = LiveDataResource()
collect = CollectResource()
app.add_route('/core', core)
app.add_route('/world.json', live)
app.add_route('/', collect)



