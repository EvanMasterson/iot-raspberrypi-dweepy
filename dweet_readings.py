import fcntl, socket, struct, dweepy, time, math, json, sqlite3
from urllib2 import urlopen
from grovepi import *

dht_sensor_port = 7  # Connect the DHt sensor to port 7
buzzer_pin = 2		#Port for buzzer
button = 4		#Port for Button

pinMode(buzzer_pin, "OUTPUT")	# Assign mode for buzzer as output
pinMode(button, "INPUT")		# Assign mode for Button as input

sqlite_filename = 'sensor_readings.sqlite'
table_name = 'sensor_values'
temp_column = 'temp_value'
humidity_column = 'humidity_value'
button_column = 'button_value'
field_type = 'INTEGER'

conn = sqlite3.connect(sqlite_filename)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS {tn} ({cn1} {ft1}, {cn2} {ft2}, {cn3} {ft3})'.format(tn=table_name, cn1=temp_column, ft1=field_type, cn2=humidity_column, ft2=field_type, cn3=button_column, ft3=field_type))


def get_device_info(ifname):
    # ip info
    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    data = json.load(response)

    ip = data['ip']
    latlng = data['loc']
    org = data['org']

    # mac address of pi
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))

    return ip, ':'.join(['%02x' % ord(char) for char in info[18:24]]), org, latlng


def get_temp():
    try:
        [temp, hum] = dht(dht_sensor_port, 0)  # Get the Temperature from the DHT sensor
        if math.isnan(temp):
            temp = 0
        return float(temp)
    except (IOError, TypeError) as e:
        print(e, "Error")


def get_humidity():
    try:
        [temp, hum] = dht(dht_sensor_port, 1)  # Get the Humidity from the DHT sensor
        if math.isnan(hum):
            hum = 0
        return float(hum)
    except (IOError, TypeError) as e:
        print(e, "Error")


# If pressed returns 1 for true value, or if false returns 2
def get_button_pressed():
    while True:
        try:
            button_status = digitalRead(button)	#Read the Button status
            if button_status:	#If the Button is in HIGH position
                digitalWrite(buzzer_pin, 1)
                return 1
            else:		#If Button is in Off position
                digitalWrite(buzzer_pin, 0)
                return 2
        except KeyboardInterrupt:	# Stop the buzzer before stopping
            digitalWrite(buzzer_pin, 0)
            break
        except (IOError,TypeError) as e:
            print(e, "Error")


def post(dic):
    thing = 'get_your_own_thing'
    print dweepy.dweet_for(thing, dic)


def get_readings():
    values = {}
    values["button-pressed"] = get_button_pressed()
    values["temperature"] = get_temp()
    values["humidity"] = get_humidity()
    values["device-config"] = get_device_info('eth0')
    return values


while True:
    values = get_readings()
    cursor.execute('INSERT INTO sensor_values VALUES(?,?,?)', (values.get('temperature'), values.get('humidity'), values.get('button-pressed')))
    conn.commit()
    id = cursor.lastrowid
    cursor.execute('SELECT * FROM sensor_values WHERE rowid=?', (id,))
    print cursor.fetchone()
    post(values)
    time.sleep(3)
