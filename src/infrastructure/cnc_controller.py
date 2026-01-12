"""CNC Controller interface and implementations."""
from abc import ABC, abstractmethod
from typing import Optional
import serial
import time
import requests
from ..domain.entities import CNCCoordinate


class CNCController(ABC):
    """Abstract base class for CNC controller communication."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the CNC controller."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the CNC controller."""
        pass
    
    @abstractmethod
    def get_position(self) -> Optional[CNCCoordinate]:
        """Get the current position of the CNC machine."""
        pass
    
    @abstractmethod
    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """Move the CNC machine to the specified coordinate."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the CNC controller."""
        pass


class FluidNCSerial(CNCController):
    """FluidNC controller implementation using serial communication."""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        """
        Initialize FluidNC serial controller.
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baudrate: Serial communication baudrate
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to FluidNC via serial."""
        try:
            self.serial_connection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=2
            )
            time.sleep(2)  # Wait for connection to stabilize
            self._connected = True
            print(f"Connected to FluidNC on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to FluidNC: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from FluidNC."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self._connected = False
            print("Disconnected from FluidNC")
    
    def get_position(self) -> Optional[CNCCoordinate]:
        """Get current position from FluidNC using ? command."""
        if not self.is_connected():
            return None
        
        try:
            self.serial_connection.write(b'?\n')
            response = self.serial_connection.readline().decode('utf-8').strip()
            
            # Parse response like: <Idle|MPos:0.000,0.000,0.000|...>
            if 'MPos:' in response:
                pos_str = response.split('MPos:')[1].split('|')[0]
                coords = pos_str.split(',')
                return CNCCoordinate(
                    x=float(coords[0]),
                    y=float(coords[1]),
                    z=float(coords[2]) if len(coords) > 2 else 0.0
                )
        except Exception as e:
            print(f"Error getting position: {e}")
        
        return None
    
    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """Move to specified coordinate using G0 command."""
        if not self.is_connected():
            return False
        
        try:
            command = f'G0 X{coordinate.x} Y{coordinate.y} Z{coordinate.z}\n'
            self.serial_connection.write(command.encode())
            return True
        except Exception as e:
            print(f"Error moving to position: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to FluidNC."""
        return self._connected and self.serial_connection and self.serial_connection.is_open


class FluidNCHTTP(CNCController):
    """FluidNC controller implementation using HTTP/WebSocket API."""
    
    def __init__(self, host: str = '192.168.1.100', port: int = 80):
        """
        Initialize FluidNC HTTP controller.
        
        Args:
            host: IP address or hostname of FluidNC
            port: HTTP port (default 80)
        """
        self.base_url = f'http://{host}:{port}'
        self._connected = False
    
    def connect(self) -> bool:
        """Test connection to FluidNC HTTP interface."""
        try:
            response = requests.get(f'{self.base_url}/', timeout=5)
            self._connected = response.status_code == 200
            if self._connected:
                print(f"Connected to FluidNC at {self.base_url}")
            return self._connected
        except requests.RequestException as e:
            print(f"Failed to connect to FluidNC HTTP: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from FluidNC HTTP."""
        self._connected = False
        print("Disconnected from FluidNC HTTP")
    
    def get_position(self) -> Optional[CNCCoordinate]:
        """Get current position via HTTP API."""
        if not self.is_connected():
            return None
        
        try:
            # FluidNC HTTP API endpoint for position status
            response = requests.get(f'{self.base_url}/command?commandText=?', timeout=2)
            if response.status_code == 200:
                data = response.text
                # Parse response similar to serial version
                if 'MPos:' in data:
                    pos_str = data.split('MPos:')[1].split('|')[0]
                    coords = pos_str.split(',')
                    return CNCCoordinate(
                        x=float(coords[0]),
                        y=float(coords[1]),
                        z=float(coords[2]) if len(coords) > 2 else 0.0
                    )
        except Exception as e:
            print(f"Error getting position via HTTP: {e}")
        
        return None
    
    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """Move to specified coordinate via HTTP API."""
        if not self.is_connected():
            return False
        
        try:
            command = f'G0 X{coordinate.x} Y{coordinate.y} Z{coordinate.z}'
            response = requests.get(
                f'{self.base_url}/command',
                params={'commandText': command},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error moving to position via HTTP: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to FluidNC HTTP."""
        return self._connected
