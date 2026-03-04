import time
import requests

def send_http_data(data: dict | bytes, endpoint: str, ip: str, port: int) -> dict:
    """
    Send data via HTTP POST and receive response
    
    Args:
        data: Dictionary to send as JSON or bytes to send as raw data
        ip: Target IP address
        port: Target port
        endpoint: API endpoint to target
    Returns:
        dict: Response data from server
    """
    url = f"http://{ip}:{port}/{endpoint}"
    
    # Create a simple session with extended timeout
    session = requests.Session()
    
    # Set longer timeouts to handle slow responses
    timeout = (10, 30)  # (connect timeout, read timeout)
    
    try:
        options_response = session.options(url, timeout=timeout)
    
        # Data could be dict or bytes
        if isinstance(data, dict):
            headers = {
                'Content-Type': 'application/json',
                'Connection': 'keep-alive',
                'Accept': '*/*',
                'User-Agent': 'RFSoC-Python-Interface/1.0'
            }
            print(f"Sending JSON data to {url} with headers {headers}")
            response = session.post(url, json=data, headers=headers, timeout=timeout)
        else:
            headers = {
                'Content-Type': 'application/octet-stream',
                'Connection': 'keep-alive',
                'Accept': '*/*',
                'User-Agent': 'RFSoC-Python-Interface/1.0'
            }

            print(f"Sending {len(data)} bytes to {url} with headers {headers}")
            start_time = time.time()
            response = session.post(url, data=data, headers=headers, timeout=timeout)
            end_time = time.time()
            print(f"Link Speed : {len(data) / (end_time - start_time) / 1e6:.2f} MB/s")

    except requests.Timeout:
        print("Request timed out")
        return {"error": "Request timed out"}
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    # Process the response
    if response.status_code == 200:
        content = response.content
        exp_len = int(response.headers.get('Content-Length', len(content)))

        print(f"Expected response length: {exp_len}, Actual response length: {len(content)}")
        
        return content

        if isinstance(data, dict):
            try:
                return response.json()
            except ValueError:
                print("Response is not valid JSON")
                return {"error": "Invalid JSON response"}
    else:
        print(f"Error: {response.status_code}")
        
        return {"error": response.status_code}