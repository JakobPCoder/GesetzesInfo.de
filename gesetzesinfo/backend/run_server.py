import os
import subprocess
import dotenv
import sys

# Set recursion depth for searching parent directories
MAX_RECURSION_DEPTH = 16

def find_closest_env_file(start_path, max_depth):
    """
    Search for the closest .env file up to a specified depth.

    :param start_path: The starting directory for the search.
    :param max_depth: The maximum recursion depth.
    :return: The path to the closest .env file, or None if not found within the depth.
    """
    current_path = os.path.abspath(start_path)  # Ensure we start with an absolute path

    for _ in range(max_depth):
        env_path = os.path.join(current_path, '.env')
        if os.path.isfile(env_path):
            return env_path

        # Move to the parent directory
        parent_path = os.path.dirname(current_path)
        
        # If we have reached the root directory, stop searching
        if parent_path == current_path:
            break
        
        current_path = parent_path
    
    return None

def load_env_file(env_file_path):
    """
    Load environment variables from the specified .env file.

    :param env_file_path: Path to the .env file
    """
    if env_file_path:
        dotenv.load_dotenv(env_file_path)
        print(f"Loaded environment variables from '{env_file_path}'")
    else:
        print("No .env file found.")

def get_django_server_port():
    """
    Retrieve the port for the Django server from environment variables.

    :return: Port number (or '8000' if not found)
    """
    return os.getenv('PORT', '8000')

def start_django_server(hosting_ip, port):
    """
    Start the Django development server with the specified port.

    :param port: Port number to listen on
    """
    try:
        # Get the directory of the script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the manage.py file
        manage_py_path = os.path.join(script_dir, 'manage.py')

        # Construct the command to start the Django server
        command = ["python", manage_py_path, "runserver", f"{hosting_ip}:{port}"]

        print(f"Starting Django server with command: {' '.join(command)}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Django server: {e}")
        sys.exit(1)

def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the closest .env file
    env_file = find_closest_env_file(script_dir, MAX_RECURSION_DEPTH)

    # Load environment variables
    load_env_file(env_file)

    # Get the port for the Django server
    hosting_ip = os.getenv('HOSTING_IP', '127.0.0.1')
    port = os.getenv('PORT', '8000')


    # Start the Django server
    start_django_server(hosting_ip, port)

if __name__ == "__main__":
    main()
