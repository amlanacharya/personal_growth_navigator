import os
import sys
import subprocess
import time

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def print_step(text):
    """Print a step with formatting."""
    print(f"\n>> {text}")

def run_command(command):
    """Run a command and print its output."""
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if stdout:
        print(stdout.decode())
    if stderr:
        print(stderr.decode())
    
    return process.returncode

def setup_environment():
    """Set up the environment for the Personal Growth Navigator."""
    print_header("Personal Growth Navigator Setup")
    print("This script will set up the Personal Growth Navigator application with gamification features.")
    
    # Check if Python is installed
    print_step("Checking Python installation")
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)
    print(f"Python {sys.version.split()[0]} detected.")
    
    # Check if pip is installed
    print_step("Checking pip installation")
    pip_check = run_command("pip --version")
    if pip_check != 0:
        print("Error: pip is not installed or not in PATH.")
        sys.exit(1)
    
    # Install dependencies
    print_step("Installing dependencies")
    dependencies = [
        "flask",
        "werkzeug",
        "python-dotenv"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        run_command(f"pip install {dep}")
    
    # Check if database exists
    print_step("Checking database")
    if not os.path.exists('growth_navigator.db'):
        print("Database not found. Creating initial database...")
        # Run the app briefly to create the database
        print("Starting the app to initialize the database...")
        process = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Wait a few seconds for the database to be created
        time.sleep(5)
        # Kill the process
        process.terminate()
        
        if not os.path.exists('growth_navigator.db'):
            print("Error: Failed to create database.")
            sys.exit(1)
        
        print("Database created successfully.")
    else:
        print("Database already exists.")
    
    # Set up gamification features
    print_step("Setting up gamification features")
    run_command("python setup_gamification.py")
    
    print_header("Setup Complete")
    print("The Personal Growth Navigator is now set up with gamification features!")
    print("\nTo start the application, run:")
    print("  python app.py")
    print("\nThen open your browser and go to:")
    print("  http://localhost:5000")
    
    print("\nEnjoy your gamified personal growth journey!")

if __name__ == "__main__":
    setup_environment()
