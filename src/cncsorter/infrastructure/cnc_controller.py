"""CNC Controller interface and implementations."""
from abc import ABC, abstractmethod
from typing import Optional
import serial
import time
import requests
from ..domain.entities import CNCCoordinate
from .motion_validator import MotionValidator, BoundaryViolationError


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
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200, 
                 motion_validator: Optional[MotionValidator] = None):
        """
        Initialize FluidNC serial controller.
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baudrate: Serial communication baudrate
            motion_validator: Optional MotionValidator for safety checks
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self._connected = False
        self.motion_validator = motion_validator
    
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
            response_bytes = self.serial_connection.readline()
            
            if not response_bytes:
                # Timeout or no data received
                print("No response received from FluidNC when requesting position")
                return None
                
            try:
                response = response_bytes.decode('utf-8').strip()
            except UnicodeDecodeError as e:
                print(f"Error decoding position response from FluidNC: {e}")
                return None
            
            if not response:
                print("Empty response received from FluidNC when requesting position")
                return None
            
            # Parse response like: <Idle|MPos:0.000,0.000,0.000|...>
            if 'MPos:' not in response:
                print(f"Unexpected position response format from FluidNC: {response}")
                return None

            pos_section = response.split('MPos:', 1)[1]
            # Only take up to the next '|' if present
            if '|' in pos_section:
                pos_str = pos_section.split('|', 1)[0]
            else:
                pos_str = pos_section

            coords = [c.strip() for c in pos_str.split(',') if c.strip() != ""]
            if len(coords) < 2:
                print(f"Incomplete coordinate data in FluidNC response: {response}")
                return None

            try:
                x = float(coords[0])
                y = float(coords[1])
                z = float(coords[2]) if len(coords) > 2 else 0.0
            except (ValueError, IndexError) as e:
                print(f"Error parsing coordinate values from FluidNC response '{response}': {e}")
                return None

            return CNCCoordinate(x=x, y=y, z=z)
        except Exception as e:
            print(f"Error getting position: {e}")
        
        return None
    
    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """Move to specified coordinate using G0 command.
        
        Validates coordinate against motion validator before sending command.
        
        Args:
            coordinate: Target CNC coordinate.
            
        Returns:
            True if move command sent successfully, False otherwise.
            
        Raises:
            BoundaryViolationError: If coordinate violates workspace boundaries.
        """
        if not self.is_connected():
            return False
        
        # Validate coordinate if validator is configured
        if self.motion_validator:
            self.motion_validator.validate_coordinate(coordinate)
        
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
    
    def __init__(self, host: str = '192.168.1.100', port: int = 80, 
                 motion_validator: Optional[MotionValidator] = None):
        """
        Initialize FluidNC HTTP controller.
        
        Args:
            host: IP address or hostname of FluidNC
            port: HTTP port (default 80)
            motion_validator: Optional MotionValidator for safety checks
        """
        self.base_url = f'http://{host}:{port}'
        self._connected = False
        self.motion_validator = motion_validator
    
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
            if response.status_code != 200:
                print(f"HTTP request failed with status code: {response.status_code}")
                return None
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if 'text' not in content_type.lower() and 'application' not in content_type.lower():
                print(f"Unexpected content type from FluidNC HTTP: {content_type}")
                return None
            
            data = response.text
            if not data:
                print("Empty response from FluidNC HTTP")
                return None
            
            # Parse response similar to serial version
            if 'MPos:' not in data:
                print(f"Unexpected HTTP response format from FluidNC: {data}")
                return None
            
            pos_section = data.split('MPos:', 1)[1]
            # Only take up to the next '|' if present
            if '|' in pos_section:
                pos_str = pos_section.split('|', 1)[0]
            else:
                pos_str = pos_section
            
            coords = [c.strip() for c in pos_str.split(',') if c.strip() != ""]
            if len(coords) < 2:
                print(f"Incomplete coordinate data in HTTP response: {data}")
                return None
            
            try:
                x = float(coords[0])
                y = float(coords[1])
                z = float(coords[2]) if len(coords) > 2 else 0.0
            except (ValueError, IndexError) as e:
                print(f"Error parsing coordinate values from HTTP response '{data}': {e}")
                return None
            
            return CNCCoordinate(x=x, y=y, z=z)
        except requests.RequestException as e:
            print(f"HTTP request error getting position: {e}")
        except Exception as e:
            print(f"Error getting position via HTTP: {e}")
        
        return None
    
    def move_to(self, coordinate: CNCCoordinate) -> bool:
        """Move to specified coordinate via HTTP API.
        
        Validates coordinate against motion validator before sending command.
        
        Args:
            coordinate: Target CNC coordinate.
            
        Returns:
            True if move command sent successfully, False otherwise.
            
        Raises:
            BoundaryViolationError: If coordinate violates workspace boundaries.
        """
        if not self.is_connected():
            return False
        
        # Validate coordinate if validator is configured
        if self.motion_validator:
            self.motion_validator.validate_coordinate(coordinate)
        
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
