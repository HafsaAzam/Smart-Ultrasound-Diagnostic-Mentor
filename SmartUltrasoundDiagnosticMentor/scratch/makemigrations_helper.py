import subprocess
import sys

def run_makemigrations():
    # Provide a series of 'y' for renames and '1' then a default value for not-null changes.
    # Adjust the inputs based on the likely questions.
    inputs = "y\ny\ny\n1\n30\n1\n'male'\n1\n'Unknown'\n1\n'Unknown'\n1\n'No summary'\n1\n1\n1\n'no-reply@example.com'\n1\n'0000000000'\n"
    
    process = subprocess.Popen(
        [sys.executable, 'manage.py', 'makemigrations'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(input=inputs)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)

if __name__ == "__main__":
    run_makemigrations()
