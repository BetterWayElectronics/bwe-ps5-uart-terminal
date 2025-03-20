import serial
import serial.tools.list_ports
from colorama import init, Fore, Style, Back
import threading
import sys
import os
import re
import time

version = "1.0.2"

def print_banner():
    print(Fore.BLACK + Back.CYAN + "*-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-*")
    print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + "            __________          __________               " + Fore.BLACK + Back.CYAN + "|")
    print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + "            \\______   \\ __  _  _\\_   ____/               " + Fore.BLACK + Back.CYAN + "|")
    print(Fore.BLACK + Back.CYAN + ":" + Fore.WHITE + Back.BLACK + "             |    |  _//  \\/ \\/  /|  __)_                " + Fore.BLACK + Back.CYAN + ":")
    print(Fore.BLACK + Back.CYAN + "." + Fore.WHITE + Back.BLACK + "             |    |   \\\\        //       \\               " + Fore.BLACK + Back.CYAN + ".")
    print(Fore.BLACK + Back.CYAN + ":" + Fore.WHITE + Back.BLACK + "  /\\_/\\      |______  / \\__/\\__//______  /               " + Fore.BLACK + Back.CYAN + ":")
    print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + " ( O.O )            \\/" + Fore.CYAN + "PS5 UART Terminal" + Fore.WHITE + "\\/" + version + "           " + Fore.BLACK + Back.CYAN + "|")
    print(Fore.BLACK + Back.CYAN + "|" + Fore.WHITE + Back.BLACK + " (>   <)                                                 " + Fore.BLACK + Back.CYAN + "|")
    print(Fore.BLACK + Back.CYAN + "*-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-*" + Back.BLACK + Style.RESET_ALL + "\n")

# Global flag to control listener thread
keep_listening = True

# Function to calculate checksum
def calculate_command(command):
    checksum = sum(ord(c) for c in command)
    checksum_with_extra = checksum + 0x100
    return checksum_with_extra % 0x100

# Function to send command with checksum
def send_command(command, ser):
    checksum = calculate_command(command)
    full_command_with_crlf = "{}:{:02X}\r\n".format(command, checksum)
    full_command_bytes = full_command_with_crlf.encode('ascii')
    ser.write(full_command_bytes)

# Function to handle clearing and reprinting input
def print_response(response):
    # Move the cursor up, print the response, and restore input line
    sys.stdout.write("\r" + " " * 80 + "\r")  # Clear current line
    print(Fore.MAGENTA + "> " + Style.RESET_ALL + response)
    sys.stdout.write(Fore.CYAN + "--> " + Style.RESET_ALL)
    sys.stdout.flush()

# Function to listen for data from the serial port
def listen_for_data(ser):
    global keep_listening
    while keep_listening:
        try:
            response = ser.readline()
            if response:
                decoded_response = response.decode('utf-8', errors='replace').strip()
                print_response(decoded_response)
        except serial.SerialException as e:
            print_response(Fore.RED + f"Serial Error: {e}" + Style.RESET_ALL)
            break

# Function to auto-select the COM port
def auto_select_port():
    com_ini_file = 'com.ini'
    
    if os.path.exists(com_ini_file):
        with open(com_ini_file, 'r') as f:
            first_line = f.readline().strip()
            if re.match(r'^COM[1-9][0-9]?$', first_line, re.IGNORECASE):
                selected_port = first_line
                print(Fore.GREEN + f"Using Port From Settings File: {selected_port}\n" + Style.RESET_ALL)
                time.sleep(1)
                return selected_port

    # Filter ports whose description suggests a USB Serial device.
    pattern = re.compile(r"^(USB-?Serial|USB Serial)\b", re.IGNORECASE)
    ports = list(serial.tools.list_ports.comports())
    filtered_ports = [port for port in ports if pattern.search(port.description)]
    
    if filtered_ports:
        # Sort ports by the numeric part of the COM port (e.g., COM3, COM4, etc.)
        def com_number(port):
            match = re.search(r'COM(\d+)', port.device, re.IGNORECASE)
            return int(match.group(1)) if match else float('inf')
        
        sorted_ports = sorted(filtered_ports, key=com_number)
        
        if len(sorted_ports) > 1:
            print("Multiple UART Devices Found:")
            for port in sorted_ports:
                num = com_number(port)
                print(f"  {num}: {port.device} - {port.description}")
            while True:
                choice = input("\nSelect A Port By Entering Its COM Number: ").strip()
                if choice.isdigit():
                    chosen = int(choice)
                    matching = [port for port in sorted_ports if com_number(port) == chosen]
                    if matching:
                        selected_port = matching[0].device
                        print(f"\nSelected Port: {selected_port}\n")
                        time.sleep(1)
                        break
                    else:
                        print(Fore.RED + "\nInvalid COM Number. Please Choose A Valid Com Port Number From The List." + Style.RESET_ALL)
                else:
                    print(Fore.RED + "\nPlease Enter A Valid Number." + Style.RESET_ALL)
        else:
            selected_port = sorted_ports[0].device
            print(Fore.GREEN + f"UART Reader Found. Auto-selecting {selected_port} - {sorted_ports[0].description}\n" + Style.RESET_ALL)
            time.sleep(1)
    else:
        selected_port = input("Enter COM Port (Example COM4): ").strip()
        # Ensure that if user inputs just a number, we prepend "COM"
        digits = ''.join(filter(str.isdigit, selected_port))
        selected_port = 'COM' + digits if digits else selected_port

    if not selected_port:
        print(Fore.RED + "\nError: No Port Specified. Exiting program." + Style.RESET_ALL)
        input("\nPress Enter to exit...")
        sys.exit(1)

    return selected_port

# Main function for UART terminal
def uart_terminal():
    global keep_listening
    os.system("cls")
    print_banner()

    # Use auto_select_port() to get the port
    port = auto_select_port()
    
    # Clear Again
    os.system("cls")
    print_banner()

    # Ask user for baud rate from the available options
    baudrate_options = {
        '1': 115200,  # EMC
        '2': 460800,  # UART0/1
        '3': 230400   # UART1 APU
    }

    print("Select UART Type:")
    print("1. EMC (Southbridge (UART)) - Baudrate: 115200")
    print("2. Flash Controller (Bootrom (UART0/1)) - Baudrate: 460800")
    print("3. Flash Controller (APU/EAP FW (UART1)) - Baudrate: 230400")
    
    baudrate_choice = input("\nEnter Your Choice (1/2/3): ").strip()

    if baudrate_choice in baudrate_options:
        baudrate = baudrate_options[baudrate_choice]
    else:
        print(Fore.RED + "\nInvalid Choice. Defaulting To EMC (Southbridge) UART on Baudrate 115200." + Style.RESET_ALL)
        time.sleep(3)
        baudrate = 115200

    try:
        os.system("cls")
        print_banner()
        ser = serial.Serial(port, baudrate, timeout=1)

        # Start the listener thread
        listener_thread = threading.Thread(target=listen_for_data, args=(ser,))
        listener_thread.daemon = True
        listener_thread.start()

        try:
            while True:
                # Prompt for command input and send to serial port
                sys.stdout.write(Fore.CYAN + "--> " + Style.RESET_ALL)
                sys.stdout.flush()

                command = input().strip().lower()  # Get the user input
                
                if command == '!break':
                    print(Fore.YELLOW + "Sending Serial Break" + Style.RESET_ALL)
                    ser.send_break()
                    continue  # Skip further processing of the !break command

                elif command == '!dtr_on':
                    print(Fore.YELLOW + "DTR Enabled" + Style.RESET_ALL)
                    ser.setDTR(True)
                    continue

                elif command == '!dtr_off':
                    print(Fore.YELLOW + "DTR Disabled" + Style.RESET_ALL)
                    ser.setDTR(False)
                    continue

                elif command == '!rts_on':
                    print(Fore.YELLOW + "RTS Enabled" + Style.RESET_ALL)
                    ser.setRTS(True)
                    continue

                elif command == '!rts_off':
                    print(Fore.YELLOW + "RTS Disabled" + Style.RESET_ALL)
                    ser.setRTS(False)
                    continue              
                    
                elif command == '!flush':
                    print(Fore.YELLOW + "Serial Flush" + Style.RESET_ALL)
                    ser.setRTS(False)
                    continue   
                    
                elif command == '!resetin':
                    print(Fore.YELLOW + "Input Butter Cleared" + Style.RESET_ALL)
                    ser.setRTS(False)
                    continue                
                
                elif command == '!resetout':
                    print(Fore.YELLOW + "Output Butter Cleared" + Style.RESET_ALL)
                    ser.setRTS(False)
                    continue

                elif command == 'exit':
                    print(Fore.YELLOW + "Exiting UART Terminal." + Style.RESET_ALL)
                    keep_listening = False
                    ser.close()
                    break

                # Send the command to the serial port
                send_command(command, ser)
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nKeyboard Interrupt Detected. Exiting UART Terminal." + Style.RESET_ALL)
            keep_listening = False
            ser.close()

    except serial.SerialException as e:
        print(Fore.RED + f"Could Not Open Serial Port: {e}" + Style.RESET_ALL)
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    try:
        uart_terminal()
    except Exception as e:
        print(Fore.RED + f"Unhandled Exception: {e}" + Style.RESET_ALL)
        input("Press Enter to exit...")
        sys.exit(1)
