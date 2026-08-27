# ============================================================
# INDOOR BEEHIVE HUB / DASHBOARD
# ============================================================
#
# PURPOSE:
# This is the INDOOR receiver/dashboard code.
#
# At the moment, the Kookaberry can run by itself.
# No sensors or HC-12 need to be connected yet.
#
# FUTURE SYSTEM:
#
# OUTDOOR BEEHIVE SYSTEM
#     |
#     | Sensors
#     |
# Outdoor Pico
#     |
#     | HC-12 radio
#     v
# Indoor HC-12
#     |
#     v
# Indoor Kookaberry
#     |
#     v
# Local Wi-Fi Dashboard

# IMPORTANT:
# The Kookaberry creates its OWN Wi-Fi network, INTERNET IS NOT REQUIRED.

# The indoor hub does NOT directly read the sensors, it will eventually extract the sensor values from the data packet received through the HC-12.

# ============================================================
# IMPORT NECESSARY MODULES
# ============================================================

# network -> creates the Kookaberry Wi-Fi network
# socket  -> creates the webpage server
# time    -> timing functions
# kooka   -> Kookaberry hardware/display
# fonts   -> Kookaberry display fonts

# ============================================================

import network
import socket
import time

from machine import Pin, UART, RTC

import kooka
import fonts

# ============================================================
# WI-FI SETTINGS
# ============================================================

# The Kookaberry creates its own Wi-Fi network.

# Connect your laptop/phone to this network and enter the IP address shown on the Kookaberry into a web browser.
# ============================================================

ssid = 'Beehive monitoring system'
password = '12345678'

disp = kooka.display


# ============================================================
# FUTURE HC-12 RECEIVER
# ============================================================
#
# The HC-12 will receive the data packet sent by the outdoor
# Pico.
#
# The exact UART and pin numbers depend on the final wiring.
#
# CHANGE ACCORDING TO PIN ALLOCATION
#
# ============================================================

# ============================================================
# HC-12 UART
# ============================================================
#
# CHANGE THESE PINS TO MATCH THE FINAL KOOKABERRY WIRING.
#
# The HC-12 receiver receives sensor values and GPS date/time
# from the outdoor Pico.
# ============================================================

# HC12_TX_PIN = 4
# HC12_RX_PIN = 5

# hc12 = UART(
#    1,
#    baudrate=9600,
#    tx=Pin(HC12_TX_PIN),
#    rx=Pin(HC12_RX_PIN)
# )

# ============================================================
# HC-12 UART SETUP
# ============================================================

HC12_TX_PIN = 12   # Pico GP12 / physical pin 16 -> HC-12 RXD
HC12_RX_PIN = 13   # Pico GP13 / physical pin 17 -> HC-12 TXD
HC12_SET_PIN = 28  # Pico GP28 / physical pin 34 -> HC-12 SET

# SET is active-low.
# HIGH = normal transparent transmission mode
# LOW  = configuration mode
hc12_set = Pin(HC12_SET_PIN, Pin.OUT)
hc12_set.value(1)

# GP12 and GP13 use UART0
hc12 = UART(
    0,
    baudrate=9600,
    tx=Pin(HC12_TX_PIN),
    rx=Pin(HC12_RX_PIN),
    bits=8,
    parity=None,
    stop=1
)

# ============================================================
# REAL TIME CLOCK
# ============================================================
#
# The RTC is initially set from the GPS date/time received
# through the HC-12.
#
# After that, the Kookaberry RTC keeps the time running
# locally, so the dashboard does not stay stuck at the last
# GPS timestamp received.
# ============================================================

rtc = RTC()
rtc_set = False


# ============================================================
# SENSOR DATA
# ============================================================
#
# IMPORTANT
# These readings are  eventually be extracted from the packet received through the HC-12 (beehive)

#They are currently set to 0 so the dashboard can run without any hardware connected.

# ------------------------------------------------------------
# OUTDOOR TEMPERATURE
# ------------------------------------------------------------
#
# SENSOR: BME280
#
# This will eventually come from the OUTDOOR Pico through
# the HC-12.
#
# CHANGE SENSOR IF FINAL WIRING USES A DIFFERENT SENSOR.
#
# ------------------------------------------------------------

outdoor_temperature = 0


# ------------------------------------------------------------
# BEEHIVE TEMPERATURE
# ------------------------------------------------------------
#
# SENSOR: DHT22
#
# This is currently a placeholder mapping.
# Change according to final sensor placement.
#
# ------------------------------------------------------------

beehive_temperature = 0


# ------------------------------------------------------------
# HUMIDITY
# ------------------------------------------------------------
#
# SENSOR: DHT22
#
# Change according to final sensor placement.
#
# ------------------------------------------------------------

humidity = 0


# ------------------------------------------------------------
# AIR PRESSURE
# ------------------------------------------------------------
#
# SENSOR: BME280
#
# ------------------------------------------------------------

air_pressure = 0


# ------------------------------------------------------------
# LIGHT
# ------------------------------------------------------------
#
# SENSOR: VEML7700
#
# ------------------------------------------------------------

light_level = 0


# ------------------------------------------------------------
# WEIGHT
# ------------------------------------------------------------
#
# SENSOR: WEIGHT SENSOR
#
# Weight is measured in kilograms.
#
# ------------------------------------------------------------

weight = 0


# ------------------------------------------------------------
# GPS / LOCATION
# ------------------------------------------------------------
#
# SENSOR: NEO-6M GPS
#
# ------------------------------------------------------------

gps_latitude = 0
gps_longitude = 0
gps_altitude = 0


# ------------------------------------------------------------
# GPS DATE AND TIME
# ------------------------------------------------------------
#
# SENSOR: NEO-6M GPS
#
# The outdoor system will eventually send the GPS time
# together with the sensor readings.
#
# ------------------------------------------------------------

recorded_date = '--/--/----'
recorded_time = '--:--:--'


# ------------------------------------------------------------
# HIVE SOUND
# ------------------------------------------------------------
#
# SENSOR: MICROPHONE
#
# ------------------------------------------------------------

hive_sound_db = 0
hive_sound_hz = 0


# ------------------------------------------------------------
# POWER
# ------------------------------------------------------------
#
# SENSOR: SOLAR CELL MONITORING MODULE
#
# ------------------------------------------------------------

solar_voltage = 0
solar_current = 0


# ============================================================
# UPDATE DATE/TIME FROM RTC
# ============================================================

def update_recorded_datetime():
    global recorded_date
    global recorded_time

    dt = rtc.datetime()

    # MicroPython RTC format:
    # (year, month, day, weekday, hour, minute, second, subseconds)

    recorded_date = '%02d/%02d/%04d' % (
        dt[2],
        dt[1],
        dt[0]
    )

    recorded_time = '%02d:%02d:%02d' % (
        dt[4],
        dt[5],
        dt[6]
    )


# ============================================================
# SET RTC FROM GPS DATE/TIME
# ============================================================

def set_rtc_from_gps(date_string, time_string):
    global rtc_set

    try:
        # Expected:
        # date_string = DD/MM/YYYY
        # time_string = HH:MM:SS

        date_parts = date_string.split('/')
        time_parts = time_string.split(':')

        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])

        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])

        # weekday is not important for this application.
        # Use 0 as a placeholder.
        rtc.datetime((
            year,
            month,
            day,
            0,
            hour,
            minute,
            second,
            0
        ))

        rtc_set = True

        update_recorded_datetime()

        print(
            'RTC set from GPS:',
            recorded_date,
            recorded_time
        )

    except Exception as e:
        print('GPS date/time error:', e)


# ============================================================
# HC-12 DATA PROCESSING
# ============================================================

def process_hc12_data():
    global outdoor_temperature
    global beehive_temperature
    global humidity
    global air_pressure
    global light_level
    global weight
    global gps_latitude
    global gps_longitude
    global gps_altitude
    global solar_voltage
    global solar_current
    global hive_sound_db
    global hive_sound_hz

    if hc12.any():

        data = hc12.readline()

        if data:

            try:
                data = data.decode().strip()

                print('HC-12:', data)

                values = data.split(',')

                gps_date = None
                gps_time = None

                for value in values:

                    # ------------------------------------------
                    # OUTDOOR TEMPERATURE
                    # ------------------------------------------

                    if value.startswith('TEMP_OUT='):
                        outdoor_temperature = float(
                            value.replace('TEMP_OUT=', '')
                        )

                    # ------------------------------------------
                    # BEEHIVE TEMPERATURE
                    # ------------------------------------------

                    elif value.startswith('TEMP_HIVE='):
                        beehive_temperature = float(
                            value.replace('TEMP_HIVE=', '')
                        )

                    # ------------------------------------------
                    # HUMIDITY
                    # ------------------------------------------

                    elif value.startswith('HUM='):
                        humidity = float(
                            value.replace('HUM=', '')
                        )

                    # ------------------------------------------
                    # AIR PRESSURE
                    # ------------------------------------------

                    elif value.startswith('PRESS='):
                        air_pressure = float(
                            value.replace('PRESS=', '')
                        )

                    # ------------------------------------------
                    # LIGHT
                    # ------------------------------------------

                    elif value.startswith('LIGHT='):
                        light_level = float(
                            value.replace('LIGHT=', '')
                        )

                    # ------------------------------------------
                    # WEIGHT
                    # ------------------------------------------

                    elif value.startswith('WEIGHT='):
                        weight = float(
                            value.replace('WEIGHT=', '')
                        )

                    # ------------------------------------------
                    # GPS LATITUDE
                    # ------------------------------------------

                    elif value.startswith('LAT='):
                        gps_latitude = float(
                            value.replace('LAT=', '')
                        )

                    # ------------------------------------------
                    # GPS LONGITUDE
                    # ------------------------------------------

                    elif value.startswith('LON='):
                        gps_longitude = float(
                            value.replace('LON=', '')
                        )

                    # ------------------------------------------
                    # GPS ALTITUDE
                    # ------------------------------------------

                    elif value.startswith('ALT='):
                        gps_altitude = float(
                            value.replace('ALT=', '')
                        )

                    # ------------------------------------------
                    # SOLAR VOLTAGE
                    # ------------------------------------------

                    elif value.startswith('SOLAR_V='):
                        solar_voltage = float(
                            value.replace('SOLAR_V=', '')
                        )

                    # ------------------------------------------
                    # SOLAR CURRENT
                    # ------------------------------------------

                    elif value.startswith('SOLAR_I='):
                        solar_current = float(
                            value.replace('SOLAR_I=', '')
                        )

                    # ------------------------------------------
                    # HIVE SOUND DB
                    # ------------------------------------------

                    elif value.startswith('SOUND_DB='):
                        hive_sound_db = float(
                            value.replace('SOUND_DB=', '')
                        )

                    # ------------------------------------------
                    # HIVE SOUND HZ
                    # ------------------------------------------

                    elif value.startswith('SOUND_HZ='):
                        hive_sound_hz = float(
                            value.replace('SOUND_HZ=', '')
                        )

                    # Fallback for old single SOUND key
                    elif value.startswith('SOUND='):
                        hive_sound_db = float(
                            value.replace('SOUND=', '')
                        )

                    # ------------------------------------------
                    # GPS DATE
                    # ------------------------------------------

                    elif value.startswith('DATE='):
                        gps_date = value.replace('DATE=', '')

                    # ------------------------------------------
                    # GPS TIME
                    # ------------------------------------------

                    elif value.startswith('TIME='):
                        gps_time = value.replace('TIME=', '')

                # Set the RTC only after both date and time
                # have been received from the same packet.
                if gps_date is not None and gps_time is not None:
                    set_rtc_from_gps(gps_date, gps_time)

            except Exception as e:
                print('HC-12 data error:', e)


# ============================================================
# CHECKED HC-12 PACKET RECEIVER (ADDED)
# ============================================================
#
# Expected frame format:
#
# TYPE=TEST,SEQ=00001,...,TIME=12:00:01,CRC=ABCD\n
#
# The CRC covers every character before ",CRC=". A newline
# marks the end of one complete packet. The byte buffer allows
# the UART to deliver a packet in several smaller pieces.
#
# The original process_hc12_data() function above is retained.
# The main loop calls this checked version during the radio test.
# ============================================================

hc12_rx_buffer = b''
last_hc12_sequence = None
hc12_valid_packets = 0
hc12_bad_crc_packets = 0
hc12_missing_packets = 0
hc12_duplicate_packets = 0


def crc16_ccitt(data):
    """Calculate CRC-16/CCITT-FALSE over a bytes object."""

    crc = 0xFFFF

    for byte in data:
        crc ^= byte << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return crc


def process_checked_hc12_packet(packet_bytes):
    """Validate and apply one complete newline-delimited packet."""

    global outdoor_temperature
    global beehive_temperature
    global humidity
    global air_pressure
    global light_level
    global weight
    global gps_latitude
    global gps_longitude
    global gps_altitude
    global solar_voltage
    global solar_current
    global hive_sound_db
    global hive_sound_hz
    global last_hc12_sequence
    global hc12_valid_packets
    global hc12_bad_crc_packets
    global hc12_missing_packets
    global hc12_duplicate_packets

    try:
        packet_text = packet_bytes.decode('ascii').strip()

        if not packet_text:
            return

        print('HC-12 raw:', packet_text)

        if ',CRC=' not in packet_text:
            hc12_bad_crc_packets += 1
            print('HC-12 rejected: CRC field is missing')
            return

        payload, received_crc_text = packet_text.rsplit(',CRC=', 1)

        received_crc = int(received_crc_text, 16)
        calculated_crc = crc16_ccitt(payload.encode('ascii'))

        if received_crc != calculated_crc:
            hc12_bad_crc_packets += 1
            print(
                'HC-12 rejected: CRC mismatch, received=%04X calculated=%04X'
                % (received_crc, calculated_crc)
            )
            return

        fields = {}

        for item in payload.split(','):
            if '=' in item:
                key, value = item.split('=', 1)
                fields[key] = value

        if 'SEQ' not in fields:
            print('HC-12 rejected: sequence number is missing')
            return

        sequence = int(fields['SEQ']) & 0xFFFF

        # Detect duplicate packets and gaps after the first valid packet.
        if last_hc12_sequence is not None:
            sequence_step = (sequence - last_hc12_sequence) & 0xFFFF

            if sequence_step == 0:
                hc12_duplicate_packets += 1
                print('HC-12 duplicate packet: SEQ=%05d' % sequence)
                return

            if sequence_step > 1:
                missed_now = sequence_step - 1
                hc12_missing_packets += missed_now
                print('HC-12 warning: %d packet(s) missed' % missed_now)

        # Convert every received field before updating global readings.
        # If one value is malformed, no partially parsed data is applied.
        new_outdoor_temperature = float(
            fields.get('TEMP_OUT', outdoor_temperature)
        )
        new_beehive_temperature = float(
            fields.get('TEMP_HIVE', beehive_temperature)
        )
        new_humidity = float(fields.get('HUM', humidity))
        new_air_pressure = float(fields.get('PRESS', air_pressure))
        new_light_level = float(fields.get('LIGHT', light_level))
        new_weight = float(fields.get('WEIGHT', weight))
        new_gps_latitude = float(fields.get('LAT', gps_latitude))
        new_gps_longitude = float(fields.get('LON', gps_longitude))
        new_gps_altitude = float(fields.get('ALT', gps_altitude))
        new_solar_voltage = float(fields.get('SOLAR_V', solar_voltage))
        new_solar_current = float(fields.get('SOLAR_I', solar_current))
        new_hive_sound_db = float(
            fields.get('SOUND_DB', fields.get('SOUND', hive_sound_db))
        )
        new_hive_sound_hz = float(fields.get('SOUND_HZ', hive_sound_hz))

        outdoor_temperature = new_outdoor_temperature
        beehive_temperature = new_beehive_temperature
        humidity = new_humidity
        air_pressure = new_air_pressure
        light_level = new_light_level
        weight = new_weight
        gps_latitude = new_gps_latitude
        gps_longitude = new_gps_longitude
        gps_altitude = new_gps_altitude
        solar_voltage = new_solar_voltage
        solar_current = new_solar_current
        hive_sound_db = new_hive_sound_db
        hive_sound_hz = new_hive_sound_hz

        last_hc12_sequence = sequence
        hc12_valid_packets += 1

        if 'DATE' in fields and 'TIME' in fields:
            set_rtc_from_gps(fields['DATE'], fields['TIME'])

        print(
            'HC-12 valid: SEQ=%05d CRC=%04X valid=%d bad_crc=%d missed=%d'
            % (
                sequence,
                received_crc,
                hc12_valid_packets,
                hc12_bad_crc_packets,
                hc12_missing_packets
            )
        )

    except Exception as e:
        print('HC-12 checked packet error:', e)


def process_hc12_data_checked():
    """Collect UART bytes and process every complete packet."""

    global hc12_rx_buffer

    if hc12.any():
        chunk = hc12.read()

        if chunk:
            hc12_rx_buffer += chunk

    # Protect memory if corrupted input never contains a newline.
    if len(hc12_rx_buffer) > 2048 and b'\n' not in hc12_rx_buffer:
        print('HC-12 receive buffer reset: no packet terminator')
        hc12_rx_buffer = b''
        return

    while b'\n' in hc12_rx_buffer:
        packet_bytes, hc12_rx_buffer = hc12_rx_buffer.split(b'\n', 1)

        if packet_bytes:
            process_checked_hc12_packet(packet_bytes)


# ============================================================
# WEBPAGE FUNCTION
# ============================================================
#
# This function creates the dashboard webpage.
#
# The browser receives this HTML from the Kookaberry.
#
# ============================================================

def webpage(
    outdoor_temperature,
    beehive_temperature,
    humidity,
    air_pressure,
    light_level,
    weight,
    gps_latitude,
    gps_longitude,
    gps_altitude,
    solar_voltage,
    solar_current,
    hive_sound_db,
    hive_sound_hz,
    recorded_date,
    recorded_time
):

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>BeeHive Monitoring System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            padding: 15px;
        }}

        /* Header Bar without logo */
        .header {{
            background-color: #ffc107;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 1.8rem;
            font-weight: bold;
            color: #222;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .section-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin: 20px 0 10px 0;
            color: #444;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}

        /* Responsive Grid Container */
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
        }}

        /* Metric Card Base */
        .card {{
            background: #ffffff;
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        /* Top Header of Card */
        .card-header {{
            padding: 8px 5px;
            font-size: 0.85rem;
            font-weight: bold;
            color: #ffffff;
            text-transform: uppercase;
        }}

        /* Content inside Card */
        .card-body {{
            padding: 15px 5px;
            background: #ffffff;
        }}

        .card-value {{
            font-size: 1.6rem;
            font-weight: bold;
            color: #111;
        }}

        .card-unit {{
            font-size: 0.9rem;
            color: #666;
            font-weight: normal;
        }}

        /* Full Width Card for Audio Graph */
        .card-full {{
            grid-column: 1 / -1;
        }}

        .chart-container {{
            position: relative;
            height: 220px;
            width: 100%;
            padding: 10px;
        }}

        /* Status Header Colors */
        .bg-green {{ background-color: #2e7d32; }}
        .bg-red {{ background-color: #c62828; }}
        .bg-blue {{ background-color: #1565c0; }}
        .bg-amber {{ background-color: #ef6c00; }}
        .bg-dark {{ background-color: #424242; }}
    </style>
</head>
<body>

    <div class="header">
        BeeHive Monitoring System
    </div>

    <!-- PROPERTIES SECTION -->
    <div class="section-title">Telemetry & Properties</div>
    <div class="grid-container">
        <div class="card">
            <div class="card-header bg-green">Internal Temp</div>
            <div class="card-body">
                <div class="card-value">{beehive_temperature}<span class="card-unit"> &deg;C</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-green">External Temp</div>
            <div class="card-body">
                <div class="card-value">{outdoor_temperature}<span class="card-unit"> &deg;C</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-green">Humidity</div>
            <div class="card-body">
                <div class="card-value">{humidity}<span class="card-unit"> %</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-red">Air Pressure</div>
            <div class="card-body">
                <div class="card-value">{air_pressure}<span class="card-unit"> hPa</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-red">Hive Weight</div>
            <div class="card-body">
                <div class="card-value">{weight}<span class="card-unit"> kg</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-red">Light Level</div>
            <div class="card-body">
                <div class="card-value">{light_level}<span class="card-unit"> lux</span></div>
            </div>
        </div>
    </div>

    <!-- HIVE SOUND SECTION -->
    <div class="section-title">Audio Metrics</div>
    <div class="grid-container">
        <div class="card">
            <div class="card-header bg-amber">Sound Level</div>
            <div class="card-body">
                <div class="card-value">{hive_sound_db}<span class="card-unit"> dB</span></div>
            </div>
        </div>

        <div class="card card-full">
            <div class="card-header bg-amber">Hive Frequency</div>
            <div class="chart-container">
                <canvas id="soundChart"></canvas>
            </div>
        </div>
    </div>

    <!-- POWER SECTION -->
    <div class="section-title">Power System</div>
    <div class="grid-container">
        <div class="card">
            <div class="card-header bg-blue">Solar Voltage</div>
            <div class="card-body">
                <div class="card-value">{solar_voltage}<span class="card-unit"> V</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-blue">Solar Current</div>
            <div class="card-body">
                <div class="card-value">{solar_current}<span class="card-unit"> mA</span></div>
            </div>
        </div>
    </div>

    <!-- LOCATION SECTION -->
    <div class="section-title">Location / GPS</div>
    <div class="grid-container">
        <div class="card">
            <div class="card-header bg-dark">Latitude</div>
            <div class="card-body">
                <div class="card-value">{gps_latitude}</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-dark">Longitude</div>
            <div class="card-body">
                <div class="card-value">{gps_longitude}</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-dark">Altitude</div>
            <div class="card-body">
                <div class="card-value">{gps_altitude}<span class="card-unit"> m</span></div>
            </div>
        </div>
    </div>

    <!-- SYSTEM STATUS SECTION -->
    <div class="section-title">System Status</div>
    <div class="grid-container">
        <div class="card">
            <div class="card-header bg-dark">Recorded Date</div>
            <div class="card-body">
                <div class="card-value" style="font-size: 1.2rem;">{recorded_date}</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-dark">Recorded Time</div>
            <div class="card-body">
                <div class="card-value" style="font-size: 1.2rem;">{recorded_time}</div>
            </div>
        </div>
    </div>

    <script>
        // Render Audio Frequency Graph
        const ctx = document.getElementById('soundChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['10s ago', '8s ago', '6s ago', '4s ago', '2s ago', 'Now'],
                datasets: [
                    {{
                        label: 'Frequency (Hz)',
                        data: [210, 215, 220, 218, 225, {hive_sound_hz}],
                        borderColor: '#1565c0',
                        backgroundColor: 'rgba(21, 101, 192, 0.1)',
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        type: 'linear',
                        position: 'left',
                        title: {{ display: true, text: 'Hz' }}
                    }}
                }}
            }}
        }});

        // Auto reload page every 10 seconds
        setInterval(function() {{
            location.reload(true);
        }}, 10000);
    </script>

</body>
</html>"""

    return str(html)
# ============================================================
# START WI-FI ACCESS POINT
# ============================================================
#
# Creates a local Wi-Fi network directly from the Kookaberry.
#
# INTERNET IS NOT REQUIRED.
#
# ============================================================

disp.print('BeeHive Dashboard')

disp.print('SSID %s' % ssid)


wlan = network.WLAN(
    network.AP_IF
)


wlan.config(
    essid=ssid,
    password=password
)


wlan.active(True)


# ============================================================
# WAIT FOR WI-FI TO ACTIVATE
# ============================================================

while wlan.active() == False:

    pass


print(
    'AP Mode Is Active, You can Now Connect'
)


# ============================================================
# GET IP ADDRESS
# ============================================================
#
# This is the IP address you enter into your browser.
#
# ============================================================

addr = wlan.ifconfig()[0]


print(
    'IP Address to connect to: ' + addr
)


disp.print('AP Active')

disp.print('Connect to:')

disp.print(addr)


# ============================================================
# CREATE WEB SERVER
# ============================================================
#
# The socket waits for a laptop/phone to request the
# dashboard webpage.
#
# ============================================================

s = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)


s.bind(
    ('', 80)
)


s.listen(1)

# Do not allow the web server to block HC-12 processing.
# The loop will continue if no browser is connected.
s.settimeout(0.1)


print(
    'Listening on',
    addr
)


disp.print('Listening')


# ============================================================
# MAIN LOOP
# ============================================================

while True:


    # ========================================================
    # HC-12 RECEIVE DATA
    # ========================================================
    #
    # The outdoor Pico sends sensor values and GPS date/time.
    # The Kookaberry receives and processes the packet here.
    # ========================================================

    process_hc12_data_checked()


    # If the RTC has already been synchronised by GPS,
    # keep the displayed time live.
    if rtc_set:
        update_recorded_datetime()


    # ========================================================
    # UPDATE KOOKABERRY DISPLAY
    # ========================================================
    #
    # Shows the main measurements and IP address on the
    # physical Kookaberry display.
    #
    # ========================================================

    disp.fill(0)


    disp.setfont(fonts.mono8x8)


    disp.text(
        'BeeHive Dashboard',
        0,
        6
    )


    disp.setfont(fonts.mono6x7)


    disp.text(
        'Out: %5.1f C' % outdoor_temperature,
        0,
        20
    )


    disp.text(
        'Hive: %4.1f C' % beehive_temperature,
        0,
        30
    )


    disp.text(
        'Hum: %5.1f %%' % humidity,
        0,
        40
    )


    disp.text(
        'Press:%5.1f' % air_pressure,
        0,
        50
    )


    disp.text(
        'IP: %s' % addr,
        0,
        60
    )


    disp.show()


    # ========================================================
    # PROCESS WEB CONNECTION
    # ========================================================
    #
    # Wait for a laptop/phone to request the dashboard.
    #
    # ========================================================

    try:

        conn, addrx = s.accept()


        print(
            'Got a connection from',
            addrx
        )


        # Receive browser request

        request = conn.recv(1024)


        request = str(request)


        print(
            'Request content = %s'
            % request
        )


        # ====================================================
        # CREATE WEBPAGE
        # ====================================================

        response = webpage(

            round(
                outdoor_temperature,
                1
            ),

            round(
                beehive_temperature,
                1
            ),

            round(
                humidity,
                1
            ),

            round(
                air_pressure,
                1
            ),

            round(
                light_level,
                1
            ),

            round(
                weight,
                1
            ),

            gps_latitude,

            gps_longitude,

            gps_altitude,

            round(
                solar_voltage,
                2
            ),

            round(
                solar_current,
                1
            ),

            round(
                hive_sound_db,
                1
            ),

            round(
                hive_sound_hz,
                1
            ),

            recorded_date,

            recorded_time

        )


        # ====================================================
        # SEND WEBPAGE
        # ====================================================

        conn.send(
            'HTTP/1.0 200 OK\r\n'
            'Content-type: text/html\r\n'
            '\r\n'
        )


        conn.send(response)


        # ====================================================
        # CLOSE CONNECTION
        # ====================================================

        conn.close()


    except OSError as e:

        try:

            conn.close()

        except:

            pass
