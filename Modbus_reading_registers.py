"""
---------------------------------------------------------------------------------
Microcontroller Program for Modbus RTU Communication
---------------------------------------------------------------------------------

Description:
    This program is designed to operate on a microcontroller, such as the Raspberry Pi Pico,
    utilizing the UART interface for communication with a Modbus RTU device. It retrieves
    the battery voltage register from a Modbus slave device, such as the Renogy Wanderer,
    and outputs the corresponding battery voltage to the console.

---------------------------------------------------------------------------------
"""

from machine import UART
import time

# Define Constants
BAUDRATE = 9600
DATA_BITS = 8
STOP_BITS = 1
PARITY = None
TX_PIN = 4  # GP4 for TX
RX_PIN = 5  # GP5 for RX
SLAVE_ADDRESS = 1  # Slave device address (Renogy Wanderer) 

# Define Modbus request parameters
FUNCTION_CODE = 0x03  # Read Holding Registers
REGISTER_ADDRESS = 0x0101  # Battery Voltage register
REGISTER_COUNT = 1  # Number of registers to read

def calculate_crc(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF

def read_battery_voltage(uart, slave_addr):
    try:
        # Construct the Modbus RTU request PDU
        request_pdu = bytearray([
            slave_addr,         # Slave Address
            FUNCTION_CODE,      # Function Code (Read Holding Registers)
            (REGISTER_ADDRESS >> 8) & 0xFF,  # High byte of register address
            REGISTER_ADDRESS & 0xFF,         # Low byte of register address
            (REGISTER_COUNT >> 8) & 0xFF,    # High byte of register count
            REGISTER_COUNT & 0xFF            # Low byte of register count
        ])

        # Calculate CRC for error checking
        crc = calculate_crc(request_pdu)
        request_pdu.append(crc & 0xFF)        # Low byte of CRC
        request_pdu.append((crc >> 8) & 0xFF) # High byte of CRC

        # Send the request to the slave
        uart.write(request_pdu)

        # Wait for a response
        time.sleep(0.1)  # Wait for the response to be received

        # Read the response from the slave
        response = uart.read(7)  # Expect 7 bytes for 1 register (2 data bytes + overhead)
        
        if response and len(response) >= 5:
            # Extract register data (assuming valid response)
            high_byte = response[3]
            low_byte = response[4]
            raw_value = (high_byte << 8) | low_byte

            # Apply scaling factor (0.1 for battery voltage)
            voltage = raw_value * 0.1
            return voltage
        else:
            return None

    except Exception as e:
        return f"Error: {e}"

def main():
    # Initialize UART with the correct TX and RX pins
    uart = UART(1, baudrate=BAUDRATE, bits=DATA_BITS, parity=None, stop=STOP_BITS, tx=TX_PIN, rx=RX_PIN)

    # Call the function for the specific slave address
    voltage = read_battery_voltage(uart, SLAVE_ADDRESS)

    if voltage is not None:
        print(f"Battery Voltage from slave {SLAVE_ADDRESS}: {voltage} V")
    else:
        print(f"Failed to read battery voltage from slave {SLAVE_ADDRESS}")

if __name__ == "__main__":
    main()
