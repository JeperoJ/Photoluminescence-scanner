import serial.tools.list_ports

__all__ = ['get_ports']

def get_ports():
        """
        Get a list of available serial ports.
        Returns:
            ports: A list of available serial ports.
        """
        ports = serial.tools.list_ports.comports()
        # return [port.device for port in ports]
        return ports