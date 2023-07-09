import subprocess

message = input("Enter migration message: ")

target_directory = "../"

subprocess.run(
    ["poetry", "run", "alembic", "revision", "--autogenerate", "-m", message], cwd=target_directory
)
