import subprocess

message = input("Enter migration message: ")

subprocess.run(["poetry", "run", "alembic", "revision", "--autogenerate", "-m", message])
