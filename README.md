# originate
Collects country of origin for all visitors and displays results on a world map.
Implemented in pure python.

Falcon for routing.
gunicorn for running the server.
Vincent (+Vega) for rendering the map and cloropleth overlay.
python-geoip for turning an incoming IP into a country code.
pycountry for handling country codes.
SQLite for database to store vistor IPs.

![alt tag](https://raw.github.com/keypusher/originate/master/data/world_example.png)
