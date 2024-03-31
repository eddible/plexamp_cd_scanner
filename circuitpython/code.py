import lib.scanner as scanner
import time
import sys
import os
import wifi
import socketpool
import adafruit_requests
import ssl

print("Connecting to WiFi")

#  connect to your SSID
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

#  prints IP address to REPL
print("My IP address is", wifi.radio.ipv4_address)


def fetch_data(barcode):
    url = f"http://192.168.1.81:5000/{barcode}"
    response = requests.get(url)
    print(response.text)
    return response.text

def run_example():

    print("\nConnecting to Scanner, please wait...")
    my_scanner = scanner.DE2120BarcodeScanner()

    if my_scanner.begin() == False:
        print("The Barcode Scanner module isn't connected correctly to the system. Please check wiring")
        return
    print("\nScanner ready!")
    time.sleep(1)

    scan_buffer = None
    
    while True:
        scan_buffer = my_scanner.read_barcode()
        if scan_buffer:
            print("\nCode found: " + str(scan_buffer))
            fetch_data(str(scan_buffer).strip())
            scan_buffer = None
        
        time.sleep(0.02)
    
if __name__ == '__main__':
    try:
        run_example()
    except(KeyboardInterrupt, SystemExit) as exErr:
        print("\nExiting, bye!")
        sys.exit(0)
