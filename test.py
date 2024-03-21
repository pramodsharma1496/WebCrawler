import subprocess

# Function to execute a shell command
def execute_command(command):
    subprocess.call(command, shell=True)

# Main function
def main():
    user_input = input("Enter a command to execute: ")
    execute_command(user_input)

if __name__ == "__main__":
    main()
