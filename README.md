# HC-12 Code Modification and Reversion Guide

## 1. Purpose

This document explains the changes I made to my teammates’ sender and receiver programs to test wireless communication between the outdoor Raspberry Pi Pico 2 and the indoor Raspberry Pi Pico W using two HC-12 radio modules.

The wireless communication test was successful. The sender transmitted test data every two seconds, and the receiver successfully received, validated, and displayed the data.

This document also explains how each modification can be disabled or completely removed when the team returns to the original sensor-testing programs.

---

## 2. Communication Configuration

Both Pico boards were configured to use UART0 with the following settings:

* Baud rate: 9600 baud
* Data bits: 8
* Parity: None
* Stop bits: 1
* HC-12 operating mode: Normal transparent transmission mode

The HC-12 connections used on both Pico boards were:

| Pico physical pin | GPIO            | Connection            |
| ----------------- | --------------- | --------------------- |
| Pin 16            | GP12 / UART0 TX | Connects to HC-12 RXD |
| Pin 17            | GP13 / UART0 RX | Connects to HC-12 TXD |
| Pin 34            | GP28            | Connects to HC-12 SET |
| GND               | GND             | Connects to HC-12 GND |

The SET pin is held HIGH so that the HC-12 operates in normal transparent transmission mode.

Both HC-12 modules must use the same baud rate, radio channel, and operating mode.

---

# 3. Changes Made to the Sender Program

## 3.1 Added an HC-12 test mode

I added the following configuration variable:

```python
HC12_TEST_MODE = True
```

When this variable is `True`, the program performs the HC-12 wireless communication test without requiring any sensors to be connected.

The program sends a test packet every two seconds before entering any of the original sensor-testing branches.

The original sensor code for the following devices was retained:

* BME280 sensor 1
* BME280 sensor 2
* VEML7700
* DHT22
* AHT21
* ENS160
* Microphone

Therefore, the original sensor-testing functionality was not removed.

---

## 3.2 Added HC-12 UART configuration

I added the following HC-12 pin definitions:

```python
HC12_TX_PIN = 12
HC12_RX_PIN = 13
HC12_SET_PIN = 28
```

I also configured GP28 as the SET control pin:

```python
hc12_set = Pin(HC12_SET_PIN, Pin.OUT)
hc12_set.value(1)
```

A HIGH signal places the HC-12 in normal transparent transmission mode.

UART0 was configured as follows:

```python
hc12 = machine.UART(
    0,
    baudrate=9600,
    tx=Pin(HC12_TX_PIN),
    rx=Pin(HC12_RX_PIN),
    bits=8,
    parity=None,
    stop=1
)
```

This allows the Pico 2 to send data to the HC-12 through GP12.

---

## 3.3 Added a test data packet

I created a test packet containing realistic values for every sensor field already recognised by the receiver program.

The packet contains:

* Outdoor temperature
* Beehive temperature
* Humidity
* Air pressure
* Light level
* Hive weight
* GPS latitude
* GPS longitude
* GPS altitude
* Solar voltage
* Solar current
* Hive sound level
* Dominant hive sound frequency
* GPS date
* GPS time

An example packet is:

```text
TYPE=TEST,SEQ=00007,TEMP_OUT=23.6,TEMP_HIVE=34.8,HUM=58.2,
PRESS=1013.2,LIGHT=420.0,WEIGHT=27.4,LAT=-34.4278,
LON=150.8931,ALT=30.0,SOLAR_V=5.15,SOLAR_I=182.0,
SOUND_DB=63.5,SOUND_HZ=245.0,DATE=27/08/2026,
TIME=12:00:07,CRC=D7B0
```

The packet ends with a newline character:

```python
"\n"
```

The newline marks the end of one complete packet and allows the receiver to separate consecutive packets correctly.

---

## 3.4 Added CRC error detection

I added a CRC-16/CCITT-FALSE checksum function.

The CRC configuration is:

* Initial value: `0xFFFF`
* Polynomial: `0x1021`
* CRC length: 16 bits

The sender calculates the CRC over the complete payload before adding the final `CRC` field.

The packet is constructed using:

```python
packet = "%s,CRC=%04X\n" % (payload, checksum)
```

The receiver independently calculates the CRC again. If the calculated CRC does not match the received CRC, the receiver rejects the packet.

This allows the system to detect data corruption during wireless transmission.

---

## 3.5 Added a sequence number

I added a sequence number to every packet:

```text
SEQ=00000
SEQ=00001
SEQ=00002
```

The sequence number increases after every transmission:

```python
packet_sequence = (packet_sequence + 1) & 0xFFFF
```

It is a 16-bit sequence number, so it returns to zero after reaching 65535.

The sequence number allows the receiver to detect:

* Missing packets
* Duplicate packets
* Unexpected sequence gaps

---

## 3.6 Added automatic repeated transmission

The sender transmits one test packet every two seconds.

After sending a packet, the program prints information such as:

```text
Sequence: 7
CRC: D7B0
Bytes: 225
```

This output confirms that:

* A packet was created;
* A CRC value was calculated;
* The packet was written to UART;
* The sequence number is increasing.

---

## 3.7 Made the OLED optional

The original sender program attempted to initialise the SH1106 OLED before starting the HC-12 test.

When the OLED was not connected, the program stopped with:

```text
OSError: [Errno 19] ENODEV
```

This meant that a missing OLED prevented the HC-12 communication test from running.

I added a `NoDisplay` fallback class and placed OLED initialisation inside a `try/except` block.

If the OLED is available, the program uses it normally. If the OLED is not detected, the program prints:

```text
WARNING: SH1106 OLED not found
HC-12 transmission test will continue without the OLED.
```

The HC-12 test then continues without displaying information on the OLED.

---

## 3.8 Corrected an existing microphone syntax error

The original microphone code contained:

```python
sample_buf = array.array(
    "H",
    0 for _ in range(samples)
)
```

Because the generator expression is the second argument of `array.array()`, it must be placed inside parentheses.

I corrected it to:

```python
sample_buf = array.array(
    "H",
    (0 for _ in range(samples))
)
```

Without this correction, Python cannot parse the sender file, even when the microphone mode is not selected.

---

# 4. Changes Made to the Receiver Program

## 4.1 Retained the original receiver function

The original function was retained:

```python
process_hc12_data()
```

I did not remove the original:

* Wi-Fi access point;
* Web server;
* Dashboard webpage;
* RTC functions;
* Sensor variables;
* Kookaberry display code;
* Original HC-12 packet parser.

Instead, I added a separate checked receiver function.

---

## 4.2 Added a UART receive buffer

A transmitted packet is approximately 225 bytes long. UART may divide this packet into several smaller groups of bytes.

The original receiver used:

```python
hc12.readline()
```

after detecting available UART data. This could cause the program to process an incomplete packet.

I added:

```python
hc12_rx_buffer = b''
```

The enhanced receiver reads all currently available bytes and adds them to this buffer. It processes the data only after detecting a newline character.

This ensures that the receiver processes one complete packet instead of interpreting a partial UART transmission as a complete packet.

A 2048-byte safety limit was also added. If corrupted data continues arriving without a newline, the receiver clears the buffer to prevent unnecessary memory usage.

---

## 4.3 Added CRC validation

The receiver separates the received packet into:

1. The protected payload;
2. The received CRC value.

It then calculates the CRC again using the same CRC-16/CCITT-FALSE algorithm.

If the values are different, the receiver displays:

```text
HC-12 rejected: CRC mismatch
```

The corrupted packet is rejected, and the dashboard variables are not updated.

If the CRC is correct, the receiver accepts the packet.

---

## 4.4 Added sequence-number checking

The receiver records the sequence number of the last valid packet:

```python
last_hc12_sequence
```

It also maintains counters for:

```python
hc12_valid_packets
hc12_bad_crc_packets
hc12_missing_packets
hc12_duplicate_packets
```

If the same sequence number is received twice, the packet is treated as a duplicate and ignored.

If the sequence number jumps, for example:

```text
SEQ=00007
SEQ=00009
```

the receiver reports that one packet was missed.

---

## 4.5 Added safer sensor-value processing

The receiver first converts all received values into temporary variables.

Only after all included values have been converted successfully are the main dashboard variables updated.

This prevents a malformed packet from updating only some of the values while leaving the remaining values unchanged.

The receiver continues to support the existing fields:

```text
TEMP_OUT
TEMP_HIVE
HUM
PRESS
LIGHT
WEIGHT
LAT
LON
ALT
SOLAR_V
SOLAR_I
SOUND_DB
SOUND_HZ
DATE
TIME
```

The GPS date and time continue to initialise the receiver’s real-time clock.

---

## 4.6 Changed the function called by the main loop

The original receiver main loop called:

```python
process_hc12_data()
```

I changed it to:

```python
process_hc12_data_checked()
```

This causes the receiver to use the enhanced buffering, CRC, and sequence-number functions.

The original function remains inside the file and can be restored easily.

---

# 5. Test Result

The HC-12 wireless communication test was successful.

During the test:

* The sender created a complete test packet every two seconds.
* The sender calculated a CRC for each packet.
* The sender transmitted the packet through UART0 and the HC-12.
* The receiver collected the complete packet.
* The receiver calculated the same CRC.
* The receiver accepted valid packets.
* The receiver detected the sequence number.
* The receiver updated its sensor variables.
* The test values appeared on the existing dashboard.

A simulated change to one protected value produced a different CRC, confirming that corrupted packets would be rejected.

Sequence gaps and duplicate sequence numbers were also detected correctly.

---

# 6. How to Revert the Changes

## 6.1 Recommended method: return to sensor testing without deleting code

The safest method is to keep the communication code but disable HC-12 test mode.

In the sender program, change:

```python
HC12_TEST_MODE = True
```

to:

```python
HC12_TEST_MODE = False
```

The program will then return to the original sensor-selection system:

```python
TEST_SENSOR = "AHT21"
```

For example, if `TEST_SENSOR` is set to `"AHT21"`, the original AHT21 testing loop will run.

The UART and packet functions remain in the file, but no test packets are transmitted.

---

## 6.2 Restore the receiver’s original parser

In the receiver main loop, change:

```python
process_hc12_data_checked()
```

back to:

```python
process_hc12_data()
```

This restores the original receiver function.

The added CRC, buffer, and sequence-number functions can remain in the file because they will no longer be called.

However, the original receiver function does not verify the CRC or detect missing and duplicate packets.

---

## 6.3 Completely remove the sender modifications

If the team wants to restore the sender file completely, the following additions can be removed:

1. Remove:

```python
HC12_TEST_MODE = True
```

2. Remove the HC-12 UART and SET configuration:

```python
HC12_TX_PIN = 12
HC12_RX_PIN = 13
HC12_SET_PIN = 28
```

3. Remove the following added variables and functions:

```python
packet_sequence
crc16_ccitt()
build_test_payload()
build_test_packet()
send_test_packet()
```

4. Remove the standalone HC-12 test loop:

```python
if HC12_TEST_MODE:
    while True:
        ...
```

5. Remove the `NoDisplay` class and OLED `try/except` block if the original direct OLED behaviour is required.

6. Restore the teammate’s original SH1106 initialisation.

This should only be done if an OLED is connected and responding at I2C address `0x3C`. Otherwise, the original `ENODEV` error will return.

7. Keep all original sensor-testing branches.

---

## 6.4 Completely remove the receiver modifications

First, restore the original main-loop call:

```python
process_hc12_data()
```

The following added receiver components can then be removed:

1. The receive buffer:

```python
hc12_rx_buffer
```

2. The status counters:

```python
last_hc12_sequence
hc12_valid_packets
hc12_bad_crc_packets
hc12_missing_packets
hc12_duplicate_packets
```

3. The added CRC function:

```python
crc16_ccitt()
```

4. The checked packet-processing function:

```python
process_checked_hc12_packet()
```

5. The buffered receiver function:

```python
process_hc12_data_checked()
```

The original Wi-Fi, webpage, RTC, sensor variables, display code, and `process_hc12_data()` function should remain unchanged.

---

## 6.5 Important syntax warning

The microphone syntax correction should not be reversed.

Keep:

```python
array.array(
    "H",
    (0 for _ in range(samples))
)
```

Do not restore:

```python
array.array(
    "H",
    0 for _ in range(samples)
)
```

The second form is syntactically invalid and prevents the entire sender program from starting.

---

## 6.6 Restoring the original OLED behaviour

The original sender program treated the OLED as a required device. If the OLED could not be detected, the entire program stopped.

To restore that behaviour:

* Remove the `NoDisplay` class;
* Remove the OLED `try/except` block;
* Restore direct `SH1106_I2C` initialisation.

This is not recommended during HC-12-only testing because a disconnected OLED would prevent the radio test from running.

---

# 7. Recommendation

I recommend keeping the enhanced sender and receiver files as separate communication-test versions and retaining the teammates’ original files as backups.

When returning to sensor testing:

```python
HC12_TEST_MODE = False
```

When returning to the original receiver parser:

```python
process_hc12_data()
```

This approach preserves the successful HC-12 communication work while providing a simple and safe way to return to the original program behaviour.

