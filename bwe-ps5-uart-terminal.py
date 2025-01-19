import serial
from colorama import Fore, Style
import threading
import sys
import os
from colorama import init, Fore, Style, Back


version = "1.0.0"

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

# Main function for UART terminal
def uart_terminal():
    global keep_listening
    os.system("cls")
    print_banner()

    port = input("Enter COM port (e.g., COM3): ")
    print()

    # Ask user for baud rate from the available options
    baudrate_options = {
        '1': 115200,  # EMC
        '2': 460800,  # UART0/1
        '3': 230400   # UART1 APU
    }

    print("Select Baud Rate:")
    print("1. 115200 (EMC)")
    print("2. 460800 (UART0/1)")
    print("3. 230400 (UART1 APU)")
    
    baudrate_choice = input("\nEnter Your Choice (1/2/3): ").strip()

    if baudrate_choice in baudrate_options:
        baudrate = baudrate_options[baudrate_choice]
    else:
        print(Fore.RED + "Invalid Choice. Defaulting To 115200 (EMC)." + Style.RESET_ALL)
        baudrate = 115200

    try:
        os.system("cls")
        print_banner()
        ser = serial.Serial(port, baudrate, timeout=1)

        # Start the listener thread
        listener_thread = threading.Thread(target=listen_for_data, args=(ser,))
        listener_thread.daemon = True
        listener_thread.start()
        #print("\n")

        try:
            while True:
                # Prompt for command input and send to serial port
                sys.stdout.write(Fore.CYAN + "--> " + Style.RESET_ALL)
                sys.stdout.flush()

                command = input().strip()  # Get the user input

                if command.lower() == 'exit':
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


if __name__ == "__main__":
    uart_terminal()
