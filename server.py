import http.server
import subprocess
import json
import os

REPO_PATH = r"C:\Users\MS\Documents\Truenas"
TRUENAS_HOST = "192.168.1.222"
TRUENAS_USER = "root"
DOCKER_IMAGE = "ghcr.io/matejs783/muj-html-web:latest"
TRUENAS_PORT = 9000

SSH_COMMAND = (
    f"docker pull {DOCKER_IMAGE} && "
    f"docker stop $(docker ps -q --filter ancestor={DOCKER_IMAGE}) && "
    f"docker rm $(docker ps -aq --filter ancestor={DOCKER_IMAGE}) && "
    f"docker run -d -p {TRUENAS_PORT}:80 {DOCKER_IMAGE}"
)

class Handler(http.server.BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/publish":
            result = self.publish()
            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def publish(self):
        log = []
        try:
            # 1. git add
            r = subprocess.run(["git", "add", "."], cwd=REPO_PATH, capture_output=True, text=True)
            log.append(f"git add: {r.stdout or r.stderr}")

            # 2. git commit
            r = subprocess.run(["git", "commit", "-m", "Publikovano z weboveho rozhrani"],
                                cwd=REPO_PATH, capture_output=True, text=True)
            log.append(f"git commit: {r.stdout or r.stderr}")

            # 3. git push
            r = subprocess.run(["git", "push"], cwd=REPO_PATH, capture_output=True, text=True)
            log.append(f"git push: {r.stdout or r.stderr}")
            if r.returncode != 0:
                return {"ok": False, "log": log}

            # 4. SSH deploy na TrueNAS
            log.append("Cekam 120 sekund nez GitHub Actions sestavi novy image...")
            import time
            time.sleep(120)

            r = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no",
                 f"{TRUENAS_USER}@{TRUENAS_HOST}", SSH_COMMAND],
                capture_output=True, text=True
            )
            log.append(f"SSH deploy: {r.stdout or r.stderr}")

            # 5. Ověření že kontejner běží
            check = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no",
                 f"{TRUENAS_USER}@{TRUENAS_HOST}",
                 f"docker ps --filter ancestor={DOCKER_IMAGE} --format '{{{{.Status}}}}'"],
                capture_output=True, text=True
            )
            log.append(f"Stav kontejneru: {check.stdout.strip() or 'Neznamy'}")

            return {"ok": r.returncode == 0, "log": log}

        except Exception as e:
            log.append(f"Chyba: {str(e)}")
            return {"ok": False, "log": log}

    def log_message(self, format, *args):
        pass  # Tichy server

if __name__ == "__main__":
    PORT = 5555
    print(f"Server bezi na http://localhost:{PORT}")
    print("Stiskni Ctrl+C pro zastaveni.")
    http.server.HTTPServer(("localhost", PORT), Handler).serve_forever()
