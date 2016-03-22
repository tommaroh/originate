# originate
Collects country of origin for all visitors and displays results on a world map.
Implemented in pure python.

* [Falcon](http://falconframework.org/) for routing.
* [gunicorn](http://gunicorn.org/) for running the server.
* [Vincent](https://github.com/wrobstory/vincent) (+Vega) for rendering the map and cloropleth overlay.
* [python-geoip](http://pythonhosted.org/python-geoip/) for turning an incoming IP into a country code.
* [pycountry](https://pypi.python.org/pypi/pycountry) for handling country codes.
* [SQLite](https://docs.python.org/2/library/sqlite3.html) for database to store vistor IPs.

![alt tag](https://raw.github.com/keypusher/originate/master/data/world_example.png)
