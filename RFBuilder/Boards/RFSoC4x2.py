from RFBuilder import RFBuilder
import requests
import json
import time


class RFSoC4x2(Board):
    def __init__(self):
        super().__init__()


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
        


        # # print(f"Response: {response.text}")
        if response.status_code == 200:
            try:
                # IMPORTANT: Fully consume the response to drain buffers
                raw_content = response.content
                # # print(f"Raw response length: {len(raw_content)} bytes")
                
                # Ensure we've read everything by checking content-length
                expected_length = response.headers.get('content-length')
                if expected_length:
                    expected_length = int(expected_length)
                    # if len(raw_content) != expected_length:
                        # print(f"WARNING: Expected {expected_length} bytes, got {len(raw_content)} bytes")
                
                if raw_content:
                    
                    # Decode and parse response
                    text_content = raw_content.decode('utf-8', errors='ignore')
                    # # print(f"Raw response text (first 500 chars): {text_content[:500]}")
                    
                    # Parse JSON response
                    response_data = response.json()
                    # print(f"Parsed JSON Response: {response_data}")
                    
                    # CRITICAL: Check for continuation or flow control signals
                    # if isinstance(response_data, dict):
                    #     if 'continuation' in response_data:
                    #         # print(f"*** CONTINUATION RESPONSE ***: {response_data['continuation']}")
                    #     if 'ready_for_more' in response_data:
                    #         # print(f"Server ready for more data: {response_data['ready_for_more']}")
                    #     if 'buffer_status' in response_data:
                    #         # print(f"Server buffer status: {response_data['buffer_status']}")
                    #     if 'flow_control' in response_data:
                    #         # print(f"Flow control signal: {response_data['flow_control']}")
                    
                    return response_data
                else:
                    # print("Response body is empty")
                    return {"empty_response": True}
                    
            except ValueError as json_error:
                # # print(f"JSON parsing error: {json_error}")
                # Still consume the response to drain buffers
                response_text = response.text
                # # print(f"Response as text: {response_text}")
                return {"response_text": response._content, "json_error": str(json_error)}
            except Exception as parse_error:
                # print(f"Response parsing error: {parse_error}")
                # Ensure response is fully consumed
                try:
                    _ = response.content  # Force read all content
                except:
                    pass
                return {"parse_error": str(parse_error)}
        else:
            # print(f"Request failed: {response.status_code} - {response.text}")
            return {"error": f"{response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout as timeout_error:
        # print(f"Request timeout: {timeout_error}")
        return {"error": f"Timeout: {timeout_error}"}
    except requests.exceptions.ConnectionError as conn_error:
        # print(f"Connection error: {conn_error}")
        return {"error": f"Connection error: {conn_error}"}
    except Exception as e:
        # print(f"HTTP transmission error: {e}")
        return {"error": str(e)}
    finally:
        session.close()

def transmit(rf_builder: RFBuilder, ip: str, port: int) -> None:
    """
    Transmit RF builder configuration and data via HTTP with proper flow control
    """
    # print(f"Starting HTTP transmission to {ip}:{port}")
    
    # Send system architecture first
    architecture_packet = rf_builder.construct_packet()

    # print("Sending architecture packet...")
    arch_response = send_http_data(architecture_packet, ip, port)
    
    if "error" in arch_response:
        # print("Architecture transmission failed, aborting data transmission")
        return
    
    # Check if server wants us to wait or provides flow control
    wait_time = 0.1  # Default wait
    if isinstance(arch_response, dict):
        if 'wait_time' in arch_response:
            wait_time = float(arch_response['wait_time'])
        if 'ready_for_data' in arch_response and not arch_response['ready_for_data']:
            # print("Server not ready for data yet, waiting longer...")
            wait_time = 1.0
    
    # print(f"Waiting {wait_time} seconds before sending data...")
    time.sleep(wait_time)
    
    # Send data for each block that has data
    data_packet = None
    for rf_block in rf_builder.blocks:
        if rf_block.__class__.__name__ == "MemSource":
            data_packet = {
                "request-type": "memory-stream",
                "data": rf_block.data
            }
            break
    
    if data_packet:
        # print("Sending data packet...")
        
        # Check data size and warn if very large
        data_size = len(json.dumps(data_packet))
        # print(f"Data packet size: {data_size} bytes ({data_size/1024/1024:.2f} MB)")
        
        # if data_size > 10 * 1024 * 1024:  # > 10MB
            # print("WARNING: Large data packet detected. This may cause buffer issues.")
        
        data_response = send_http_data(data_packet, ip, port)
        
        if "error" not in data_response:
            pass
            # print("Data transmission completed successfully")
            
            # # Check for buffer status in response
            # if isinstance(data_response, dict):
            #     if 'buffer_drained' in data_response:
            #         # print(f"Server buffer drained: {data_response['buffer_drained']}")
            #     if 'processing_complete' in data_response:
            #         # print(f"Server processing complete: {data_response['processing_complete']}")
        else:
            pass
            # print("Data transmission failed")
    else:
        pass
        # print("No data packet to transmit")

def send_command(data: dict, ip: str, port: int) -> dict:
    """
    Send a simple command via HTTP and return response
    """
    # print(f"Sending command to {ip}:{port}")
    return send_http_data(data, ip, port)

def drain_server_buffers(ip: str, port: int) -> dict:
    """
    Send a drain command to help clear server buffers
    """
    drain_command = {
        "request-type": "drain-buffers",
        "action": "flush"
    }
    # print("Sending buffer drain command...")
    return send_command(drain_command, ip, port)

def check_server_status(ip: str, port: int) -> dict:
    """
    Check server buffer and processing status
    """
    status_command = {
        "request-type": "status",
        "query": ["buffer_status", "processing_status", "ready_for_data"]
    }
    # print("Checking server status...")
    return send_command(status_command, ip, port)