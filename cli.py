#! /usr/bin/env python3

import argparse
import subprocess
import os
import shutil
import time
import threading


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8')

def run_npm_dev(directory):
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            print(line, end='')

        process.stdout.close()
        return_code = process.wait()

        if return_code:
            raise subprocess.CalledProcessError(return_code, "npm run dev")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Stopping...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def setup_react_project():
    # Run npm create vite with react template
    pass

def handle_run_command(file_path: str):
    if not file_path.endswith('.jsx'):
        print("Error: The file must have a .jsx extension.")
        return

def rm_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

def rm_dir_recursive(dir_path: str):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def run_uvicorn_server(port: int):
    try:
        process = subprocess.Popen(
            ["uvicorn", "server_snaptail:app", "--reload", "--host", "0.0.0.0", "--port", port],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            print(line, end='')

        process.stdout.close()
        return_code = process.wait()

        if return_code:
            raise subprocess.CalledProcessError(return_code, "uvicorn")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nUvicorn server interrupted by user. Stopping...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def run_servers_and_watch(snaptail_dir: str, port: int):
    # Start uvicorn server in a separate thread
    uvicorn_thread = threading.Thread(target=run_uvicorn_server, daemon=True, args=(port,))
    uvicorn_thread.start()

    # Run npm dev server (assuming this is for React)
    run_npm_dev(snaptail_dir)

    # The main thread will continue to run, keeping both servers active
    # You can add file watching logic here if needed


def watch_file_non_blocking(file_path: str, callback):
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    def run_watcher():
        class FileChangeHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path == file_path:
                    callback()

        observer = Observer()
        observer.schedule(FileChangeHandler(), path=os.path.dirname(file_path), recursive=False)
        observer.start()

        print(f"Watching {file_path}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    watcher_thread = threading.Thread(target=run_watcher, daemon=True)
    watcher_thread.start()
    return watcher_thread


def setup_and_run(file_to_run: str, host: str, port: int):
    snaptail_dir = os.path.join(os.getcwd(), '.snaptail')

    # Copy the file to the vite project
    def copy_file_to_vite_project(file_path: str):
        shutil.copy(file_path, os.path.join(snaptail_dir, "src", "App.jsx"))

    # Check if .snaptail directory already exists
    if os.path.exists(snaptail_dir):
        print(f".snaptail directory already exists at {snaptail_dir}")
        print("Using existing directory...")
        # copy_file_to_vite_project(file_to_run)()
    else:
        tmp_dir = f"snaptail_{time.time_ns()}"
        # Setup vite-react project
        # Remove all files except App.jsx and main.jsx

        run_command(f"npm create vite@latest {tmp_dir} -- --template react")

        # Clean up the vite project and keep essential files
        src_dir = os.path.join(tmp_dir, "src")
        files_to_remove = [
            os.path.join(tmp_dir, "eslint.config.js"),
            os.path.join(src_dir, "App.css"),
            os.path.join(src_dir, "main.css"),
            os.path.join(src_dir, "index.css"),
            os.path.join(src_dir, "main.jsx"),
            os.path.join(src_dir, "App.jsx"),
        ]
        for file in files_to_remove:
            rm_file(file)

        rm_dir_recursive(os.path.join(tmp_dir, "src", "assets"))

        os.rename(tmp_dir, snaptail_dir)

    # always update main.jsx
    main_jsx_content = [
        "import { StrictMode } from 'react'",
        "import { createRoot } from 'react-dom/client'",
        "import { App } from './App.jsx'", # <<< this is what we are interested in
        "createRoot(document.getElementById('root')).render(",
        "<StrictMode>",
        f"    <App apiUrl={{\"http://{host}:{port}\"}} />",
        "</StrictMode>",
        ")",
    ]

    with open(os.path.join(snaptail_dir, "src", "main.jsx"), "w") as f:
        f.write("\n".join(main_jsx_content))


    file_to_watch = os.path.join(os.getcwd(), file_to_run)
    copy_file_to_vite_project(file_to_watch)
    watch_file_non_blocking(file_to_watch, lambda: copy_file_to_vite_project(file_to_watch))

    # Run the vite project
    run_command(f"npm i --prefix {snaptail_dir}")
    # run_npm_dev(snaptail_dir)
    run_servers_and_watch(snaptail_dir, port)


def initialize_venv(project_dir):
    """
    Initialize a Python virtual environment in the project directory.
    """
    venv_path = os.path.join(project_dir, '.venv')
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        run_command(f"python -m venv {venv_path}")

        # Determine the correct activate script based on the OS
        if os.name == 'nt':  # Windows
            activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
        else:  # Unix-based systems (Linux, macOS)
            activate_script = os.path.join(venv_path, 'bin', 'activate')

        # Activate the virtual environment and install dependencies
        if os.name == 'nt':
            run_command(f"call {activate_script} && pip install -r requirements.txt")
        else:
            run_command(f"source {activate_script} && pip install -r requirements.txt")

        print("Virtual environment created and dependencies installed.")
    else:
        print("Virtual environment already exists.")


def main():
    parser = argparse.ArgumentParser(description="CLI program to manage and run JSX files")
    parser.add_argument('command', choices=['run', 'init'], help='Command to execute')
    parser.add_argument('file', nargs='?', help='Path to the JSX file (required for run command)')
    parser.add_argument('-p', '--port', type=int, default=9000, help='Port number for uvicorn server')
    args = parser.parse_args()

    if args.command == 'init':
        if args.file:
            print("Warning: 'file' argument is ignored for 'init' command")
        initialize_venv(os.getcwd())

    if args.command == 'run':
        # handle_run_command(args.file)
        setup_and_run(args.file, "0.0.0.0", args.port)
if __name__ == "__main__":
    main()
