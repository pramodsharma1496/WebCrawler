import subprocess
import os

# Function to execute a shell command
def execute_command(command):
    subprocess.call(command, shell=True)

# Function to access sensitive information
def access_sensitive_data():
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        print("Accessing sensitive data with secret key:", secret_key)
        print("test")
    else:
        print("Error: Secret key not found.")

# Main function
def main():
    user_input = input("Enter a command to execute: ")
    execute_command(user_input)
    access_sensitive_data()

if __name__ == "__main__":
    main()
