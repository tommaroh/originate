import sys
import sqlite3

db_file = "connections.sqlite"
table_name = "connections"

#columns
ip_col = "ip"
country_col = "country"
continent_col = "continent"
timezone_col = "timezone"
divisions_col = "divisions"

class RemoteConnection():

    def __init__(self, ip, country, continent, tz, divisions):
        self.ip = ip
        self.country = country
        self.continent = continent
        self.tz = tz
        self.divisions = divisions
    
    def __str__(self):
        return str(self.__dict__)

def create_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('CREATE TABLE {tn} ({ip} TEXT PRIMARY KEY, {country} TEXT, {continent} TEXT, {timezone} TEXT, {divisions} TEXT)'.format(
        tn=table_name, 
        ip=ip_col, 
        country=country_col, 
        continent=continent_col, 
        timezone=timezone_col, 
        divisions=divisions_col))


def upsert_connection(remote_connection):
    # Connecting to the database file

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    remote=remote_connection
    print("Adding: %s" % remote_connection)
    try:
        try:
            # insert a new row
            c.execute("INSERT INTO connections VALUES (?, ?, ?, ?, ?)", 
               [remote.ip, 
                remote.country, 
                remote.continent, 
                remote.tz, 
                remote.divisions])


        except sqlite3.IntegrityError:
            # update existing row
            c.execute('''UPDATE connections SET country = :country, continent = :continent, timezone = :timezone, divisions = :divisions
                      WHERE ip = :ip''', {
                        'ip': remote.ip,
                        'country': remote.country,
                        'continent': remote.continent,
                        'timezone': remote.tz,
                        'divisions': remote.divisions
                      }
            )
            print('IP already exists: {}, updating...'.format(remote.ip))
    
        conn.commit()
    finally:    
        conn.close()


def get_country_counts():
    '''
    Returns a dictionary of {country_code: count}
    '''

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
 
    counts = c.execute("SELECT country, COUNT(*) FROM connections GROUP BY country")
    result = {}
    for row in counts:
        result[row[0]] = row[1]
    print(result)
    return result

def get_all_connections():

    conn = sqlite3.connect(db_file)
    c = conn.cursor() 
    for row in c.execute('SELECT * FROM connections'):
        yield RemoteConnection(row[0], row[1], row[2], row[3], row[4])
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            create_db()
            sys.exit(0)
    print("No valid arguments")
    


