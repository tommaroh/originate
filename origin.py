
import os
import falcon
import vincent
import json
import random
import pandas
from geoip import geolite2
from vincent import values

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

        html_file = 'world.html'
        resp.status = falcon.HTTP_200
        remote_ip = req.env['REMOTE_ADDR']
        match = geolite2.lookup(remote_ip)

        # the geo map
        geo_data = [{
             'name': 'countries',
             'url': "http://45.33.70.211/core",
             'feature': 'world-countries'}]
        
        # build some data
        with open(os.path.join('data', 'world-countries.topo.json'), 'r') as f:
            data = json.load(f)
        
        countries = [country['id'] for country in data['objects']['world-countries']['geometries']]
        counts = [random.randint(0, 10) for i in range(len(countries))]
            
        # sure, lets make a dataframe
        df = pandas.DataFrame({"COUNTRY": countries, "COUNT": counts})

        if match:
            print(match.country)
            print(match.continent)
            print(match.timezone)
            for sub in match.subdivisions:
                print(sub)

        else:
            print("No match found")

        vis = vincent.Map(data=df, geo_data=geo_data, scale=200, projection='cylindricalStereographic',
            data_bind="COUNT", data_key="COUNTRY", map_key={'countries': "id"})
        vis.scales['color'].domain = [0, max(counts)]
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



