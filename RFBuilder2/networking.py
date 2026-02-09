import requests

def send_http_data(data: dict, ip: str, port: int) -> dict:
    """
    Send data via HTTP POST and receive response
    
    Args:
        data: Dictionary to send as JSON
        ip: Target IP address
        port: Target port
        
    Returns:
        dict: Response data from server
    """
    url = f"http://{ip}:{port}"
    
    # Create a simple session with extended timeout
    session = requests.Session()
    
    # Set longer timeouts to handle slow responses
    timeout = (10, 30)  # (connect timeout, read timeout)
    
    try:
        options_response = session.options(url, timeout=timeout)
    
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': 'RFSoC-Python-Interface/1.0'
        }
        
        response = session.post(url, json=data, headers=headers, timeout=timeout, stream=True)

    except requests.Timeout:
        print("Request timed out")
        return {"error": "Request timed out"}
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    # Process the response
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return {"error": response.status_code}