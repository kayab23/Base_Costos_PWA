import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

MONITORED_FOLDERS = ["app", "tests"]
TEST_SCRIPT = "test_login_usuarios.py"

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"\nArchivo modificado: {event.src_path}. Ejecutando pruebas de login...")
            try:
                result = subprocess.run([".venv\\Scripts\\python.exe", TEST_SCRIPT], capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print(f"Error al ejecutar pruebas: {e}")

if __name__ == "__main__":
    event_handler = ChangeHandler()
    observer = Observer()
    for folder in MONITORED_FOLDERS:
        observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    print("Monitoreando cambios en app/ y tests/. Presiona Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
