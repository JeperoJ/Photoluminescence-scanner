import serial
from serial.tools import list_ports
ports = list_ports.comports()
print(ports)