import os
import subprocess
import dotenv
import sys
import time
from pathlib import Path

# Set recursion depth for searching parent directories
MAX_RECURSION_DEPTH = 16

def find_closest_env_file(start_path, max_depth):
    """
    Search for the closest .env file up to a specified depth.

    :param start_path: The starting directory for the search.
    :param max_depth: The maximum recursion depth.
    :return: The path to the closest .env file, or None if not found within the depth.
    """
    current_path = Path(start_path).resolve()

    for _ in range(max_depth):
        env_path = current_path / '.env'
        if env_path.is_file():
            return str(env_path)

        # Move to the parent directory
        if current_path.parent == current_path:
            break  # We've reached the root directory
        
        current_path = current_path.parent
    
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
    return os.getenv('BACKEND_PORT', '8000')

def migrate_database():
    """
    Run database migrations.
    """
    try:
        # Get the directory of the script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the manage.py file
        manage_py_path = os.path.join(script_dir, 'manage.py')
        
        #try:
        command = ["python", manage_py_path, "makemigrations"]
        subprocess.run(command, check=True)

        # wait 2 seconds
        time.sleep(2)

        command = ["python", manage_py_path, "migrate"]
        subprocess.run(command, check=True)
        time.sleep(2)

    except Exception as e:
        print(f"Error migrating database: {e}")
        # ask the user if he wants to exit or continue with y/n
        if input("Do you want to exit? (y/n): ") == "y":
            sys.exit(1)
        else:
            print("WARNING: Continuing without the database migration.")





def start_django_server(hosting_ip, port):
    """
    Start the Django development server with the specified port.

    :param hosting_ip: IP address to bind the server to.
    :param port: Port number to listen on.
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
    """
    Main function to set up and start the Django server.

    This function performs the following steps:
    1. Gets the directory of the script.
    2. Finds the closest .env file.
    3. Loads environment variables from the .env file.
    4. Retrieves the hosting IP and port from environment variables.
    5. Starts the Django server with the specified IP and port.
    """
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Find the closest .env file
    env_file = find_closest_env_file(script_dir, MAX_RECURSION_DEPTH)

    # Load environment variables
    load_env_file(env_file)

    # Get the IP and port for the Django server
    hosting_ip = os.getenv('HOSTING_IP', '127.0.0.1')
    port = os.getenv('BACKEND_PORT', '8000')

    # # Migrate the database
    # migrate_database()

    # Start the Django server
    start_django_server(hosting_ip, port)

if __name__ == "__main__":
    main()