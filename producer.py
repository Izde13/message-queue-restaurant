import time
import requests
from datetime import datetime

BROKER_URL = "http://127.0.0.1:8000"

def main():
    i = 1
    try:
        while True:
            payload = f"Pedido #{i} - Combo hamburguesa ({datetime.now().isoformat(timespec='seconds')})"
            resp = requests.post(f"{BROKER_URL}/produce", json={"payload": payload})
            if resp.status_code == 200:
                data = resp.json()
                print(f"[PRODUCER] Enviado: {data}")
            else:
                print(f"[PRODUCER] Error al producir: {resp.status_code} {resp.text}")

            i += 1
            time.sleep(2)  # cada 2 segundos llega un nuevo pedido
    except KeyboardInterrupt:
        print("\n[PRODUCER] Detenido por el usuario.")


if __name__ == "__main__":
    main()
