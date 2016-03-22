
import os
import falcon
import vincent
import json
import random
import pandas
import db
import pycountry
from geoip import geolite2
from vincent import values
from db import RemoteConnection


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

    def get_matching_country(self, code):
        # takes an ISO-3666 alpha2 code and return corresponding alpha3 code
        country = pycountry.countries.get(alpha2=code)        
        return country.alpha3

    def on_get(self, req, resp):

        html_file = 'world.html'
        resp.status = falcon.HTTP_200
        remote_ip = req.env['REMOTE_ADDR']
        match = geolite2.lookup(remote_ip)

        # the geo map
        geo_data = [{
             'name': 'countries',
             'url': "http://45.33.70.211/core",
             'feature': 'world-countries'}]

        if match:
            # normalize the country code
            country = self.get_matching_country(match.country)
            # add to db
            connection_info = RemoteConnection(remote_ip, country, match.continent, match.timezone, str(list(match.subdivisions)))
            db.upsert_connection(connection_info)
            counts = db.get_country_counts()

        else:
            counts = {}
            print("No match found")

         
        # build some data
        with open(os.path.join('data', 'world-countries.topo.json'), 'r') as f:
            data = json.load(f)
        
        countries = [country['id'] for country in data['objects']['world-countries']['geometries']]
        aligned_counts = []
        for country in countries:
            if counts.get(country):
                print("Found: %s: %s" % (country, counts.get(country)))
                aligned_counts.append(counts.get(country))
            else:
                aligned_counts.append(random.randint(0, 10))

        # lets make a dataframe
        df = pandas.DataFrame({"COUNTRY": countries, "COUNT": aligned_counts})
        vis = vincent.Map(data=df, geo_data=geo_data, scale=200, projection='cylindricalStereographic',
            data_bind="COUNT", data_key="COUNTRY", map_key={'countries': "id"})
        #max_value = max(counts) if counts else 1
        #vis.scales['color'].domain = [0, max_value]
        vis.to_json("world.json", html_out=True, html_path=html_file)
        vis.marks[0].properties.enter.stroke_opacity = values.ValueRef(value=0.5)
        resp.content_type = "text/html; charset=utf-8"
        with open(html_file) as html:
            resp.body = html.read()


# run the app
app = falcon.API()
core = CoreDataResource()
live = LiveDataResource()
collect = CollectResource()
app.add_route('/core', core)
app.add_route('/world.json', live)
app.add_route('/world', collect)



