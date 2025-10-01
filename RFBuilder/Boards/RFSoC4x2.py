from RFBuilder import RFBuilder

import requests

def transmit(packet: dict, ip: str, port: int) -> None:

    ## Send HTTP Post request to the system
    url = f"http://{ip}:{port}"

    # Send OPTIONS request
    response = requests.options(url)
    print(response)

    # Send POST request
    headers = {'Content-Type': 'application/json'}

    print("Transmitting Data: ", packet)

    try:
        response = requests.post(url, json=packet, headers=headers)
        if response.status_code == 200:
            print("Transmission successful:", response.json())
        else:
            print("Transmission failed:", response.status_code, response.text)
    except:
        pass
    
 
    