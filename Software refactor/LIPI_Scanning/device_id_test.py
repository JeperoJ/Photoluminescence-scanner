import serial
from serial.tools import list_ports
ports = list_ports.comports()
for port in ports:
    print(port.name, port.device, port.pid, port.vid, port.hwid, port.description, port.interface, port.location, port.manufacturer, port.product, port.serial_number)