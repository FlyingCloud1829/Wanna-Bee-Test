import machine
import time
import fonts

from machine import SoftI2C, Pin
from sh1106 import SH1106_I2C


# ============================================================
# SELECT SENSOR TO TEST
# ============================================================

# Change this one line depending on the sensor being tested

TEST_SENSOR = "AHT21"

# Options:
# "BME1"
# "BME2"
# "VEML"
# "DHT22"
# "AHT21"
# "ENS160"
# "MIC"


# ============================================================
# HC-12 COMMUNICATION TEST MODE (ADDED)
# ============================================================
#
# True  = send a test packet every 2 seconds without requiring
#         any sensor to be connected.
# False = run the original single-sensor test selected above.
#
# ============================================================

HC12_TEST_MODE = True


# ============================================================
# I2C SETUP
# ============================================================

i2c = SoftI2C(
    scl=Pin("P3A"),
    sda=Pin("P3B")
)


# ============================================================
# EXTERNAL SH1106 DISPLAY SETUP
# ============================================================

beehivedisp = SH1106_I2C(
    128,
    64,
    i2c,
    addr=60
)



# Define global objects.
i2c = SoftI2C(scl="P3A", sda="P3B")
display_kbhjb = SH1106_I2C(128, 64, i2c, addr=60)

beehivedisp.setfont(fonts.mono5x5)


# ============================================================
# HC-12 UART TRANSMITTER SETUP (ADDED)
# ============================================================
#
# Pico physical pin 16 = GP12 = UART0 TX -> HC-12 RXD
# Pico physical pin 17 = GP13 = UART0 RX <- HC-12 TXD
# Pico physical pin 34 = GP28             -> HC-12 SET
#
# SET is active-low:
# HIGH = normal transparent transmission mode
# LOW  = AT-command configuration mode
#
# Both HC-12 modules must use the same baud rate, channel,
# and operating mode. This test uses UART 9600 baud, 8N1.
# ============================================================

HC12_TX_PIN = 12
HC12_RX_PIN = 13
HC12_SET_PIN = 28

hc12_set = Pin(HC12_SET_PIN, Pin.OUT)
hc12_set.value(1)

hc12 = machine.UART(
    0,
    baudrate=9600,
    tx=Pin(HC12_TX_PIN),
    rx=Pin(HC12_RX_PIN),
    bits=8,
    parity=None,
    stop=1
)


# ============================================================
# DATA PACKING, CRC, SEQUENCE NUMBER, AND SENDING (ADDED)
# ============================================================

packet_sequence = 0


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


def build_test_payload(sequence):
    """Create one realistic test payload for the receiver."""

    # Change these values later when real sensor readings are ready.
    # The receiver already recognises all of these field names.
    test_second = sequence % 60

    return (
        "TYPE=TEST,"
        "SEQ=%05d,"
        "TEMP_OUT=23.6,"
        "TEMP_HIVE=34.8,"
        "HUM=58.2,"
        "PRESS=1013.2,"
        "LIGHT=420.0,"
        "WEIGHT=27.4,"
        "LAT=-34.4278,"
        "LON=150.8931,"
        "ALT=30.0,"
        "SOLAR_V=5.15,"
        "SOLAR_I=182.0,"
        "SOUND_DB=63.5,"
        "SOUND_HZ=245.0,"
        "DATE=27/08/2026,"
        "TIME=12:00:%02d"
    ) % (sequence, test_second)


def build_test_packet(sequence):
    """Add a CRC field and newline frame terminator to a payload."""

    payload = build_test_payload(sequence)
    checksum = crc16_ccitt(payload.encode("ascii"))

    # CRC is calculated over everything before ",CRC=".
    # Newline marks the end of one complete HC-12 packet.
    packet = "%s,CRC=%04X\n" % (payload, checksum)

    return packet, checksum


def send_test_packet():
    """Send one packet and advance the 16-bit sequence number."""

    global packet_sequence

    packet, checksum = build_test_packet(packet_sequence)
    bytes_written = hc12.write(packet.encode("ascii"))

    print("HC-12 TX:", packet.strip())
    print(
        "Sequence:",
        packet_sequence,
        "CRC: %04X" % checksum,
        "Bytes:",
        bytes_written
    )

    sent_sequence = packet_sequence
    packet_sequence = (packet_sequence + 1) & 0xFFFF

    return sent_sequence, checksum, bytes_written


# ============================================================
# STANDALONE HC-12 COMMUNICATION TEST (ADDED)
# ============================================================
#
# This block runs before the original sensor-selection code.
# Set HC12_TEST_MODE to False to return to the original sensor
# testing behaviour without removing any sensor code.
# ============================================================

if HC12_TEST_MODE:

    while True:

        sequence, checksum, bytes_written = send_test_packet()

        beehivedisp.clear()

        beehivedisp.print("HC-12 TX TEST", show=0)
        beehivedisp.print("SEQ: " + str(sequence), show=0)
        beehivedisp.print("CRC: %04X" % checksum, show=0)
        beehivedisp.print("BYTES: " + str(bytes_written), show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# BME280 SENSOR 1
# ============================================================

if TEST_SENSOR == "BME1":

    from bme280 import BME280

    sensor = BME280(
        i2c=i2c,
        address=0x77
    )

    while True:

        temperature = sensor.values[0]
        pressure = sensor.values[1]
        humidity = sensor.values[2]

        beehivedisp.clear()

        beehivedisp.print("BME280 #1", show=0)
        beehivedisp.print("Temp: " + str(temperature) + " C", show=0)
        beehivedisp.print("Press: " + str(pressure), show=0)
        beehivedisp.print("Hum: " + str(humidity) + " %", show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# BME280 SENSOR 2
# ============================================================

elif TEST_SENSOR == "BME2":

    from bme280 import BME280

    sensor = BME280(
        i2c=i2c,
        address=0x77
    )

    while True:

        temperature = sensor.values[0]
        pressure = sensor.values[1]
        humidity = sensor.values[2]

        beehivedisp.clear()

        beehivedisp.print("BME280 #2", show=0)
        beehivedisp.print("Temp: " + str(temperature) + " C", show=0)
        beehivedisp.print("Press: " + str(pressure), show=0)
        beehivedisp.print("Hum: " + str(humidity) + " %", show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# VEML7700 LIGHT SENSOR
# ============================================================

elif TEST_SENSOR == "VEML":
    
    import veml7700
   
    veml = veml7700.VEML7700(i2c=i2c)
    
    while True:

        light = veml.read_lux()

        beehivedisp.clear()

        beehivedisp.print("VEML7700", show=0)
        beehivedisp.print("Light:", show=0)
        beehivedisp.print(str(light) + " Lux", show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# DHT22
# ============================================================

elif TEST_SENSOR == "DHT22":

    import dht

    sensor = dht.DHT22(Pin("P4"))

    while True:

        sensor.measure()

        temperature = sensor.temperature()
        humidity = sensor.humidity()

        beehivedisp.clear()

        beehivedisp.print("DHT22", show=0)
        beehivedisp.print("Temp: " + str(temperature) + " C", show=0)
        beehivedisp.print("Hum: " + str(humidity) + " %", show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# AHT21
# ============================================================

elif TEST_SENSOR == "AHT21":

    from aht21 import AHT21

    sensor = AHT21(i2c=i2c)
    while True:

        humidity, temperature = sensor.read()

        beehivedisp.clear()

        beehivedisp.print("AHT21", show=0)
        beehivedisp.print("Temp: " + str(temperature) + " C", show=0)
        beehivedisp.print("Hum: " + str(humidity) + " %", show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# ENS160
# ============================================================

elif TEST_SENSOR == "ENS160":

    from ens160 import ENS160

    sensor = ENS160(
        bus=i2c,
        address=0x53
    )

    while True:

        aqi = sensor.aqi
        eco2 = sensor.eco2
        tvoc = sensor.tvoc

        beehivedisp.clear()

        beehivedisp.print("ENS160", show=0)
        beehivedisp.print("AQI: " + str(aqi), show=0)
        beehivedisp.print("eCO2: " + str(eco2), show=0)
        beehivedisp.print("TVOC: " + str(tvoc), show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# MICROPHONE FREQUENCY ANALYSIS
# ============================================================

elif TEST_SENSOR == "MIC":

    import math
    import array
    import kooka
    import goertzel

    audio_pin = "P1"

    freq_min = 40
    freq_max = 4000
    freq_res = 40

    freq_bins = int(
        math.ceil(
            (freq_max - freq_min) / freq_res
        )
    )

    sample_rate = int(freq_max * 2)

    samples = int(sample_rate / freq_res)

    sample_buf = array.array(
        "H",
        (0 for _ in range(samples))
    )

    adc = machine.ADC(audio_pin)

    spectrum = [0] * freq_bins

    while True:

        kooka.read_timed(
            adc,
            sample_buf,
            sample_rate
        )

        freqs, powers = goertzel.goertzel(
            sample_buf,
            sample_rate,
            (freq_min, freq_max)
        )

        for i in range(0, len(powers)):
            spectrum[i] = powers[i][2]

        dominant_frequency = freqs[
            spectrum.index(max(spectrum))
        ]

        dominant_power = max(spectrum)

        beehivedisp.clear()

        beehivedisp.print("MICROPHONE", show=0)
        beehivedisp.print("Peak Frequency:", show=0)
        beehivedisp.print(str(dominant_frequency) + " Hz", show=0)
        beehivedisp.print("Power:", show=0)
        beehivedisp.print(str(dominant_power), show=0)

        beehivedisp.show()

        time.sleep(2)


# ============================================================
# INVALID SENSOR SELECTION
# ============================================================

else:

    beehivedisp.clear()

    beehivedisp.print("INVALID SENSOR", show=0)
    beehivedisp.print(TEST_SENSOR, show=0)

    beehivedisp.show()
