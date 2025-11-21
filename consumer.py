from colorama import Fore, Style
import time, random, requests, sys

BROKER_URL = "http://127.0.0.1:8000"

COLORS = [Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.WHITE]

def main():
    consumer_id = sys.argv[1] if len(sys.argv) > 1 else "Anon"
    color = COLORS[hash(consumer_id) % len(COLORS)]

    print(color + f"[CONSUMER {consumer_id}] Iniciado..." + Style.RESET_ALL)

    try:
        while True:
            resp = requests.post(f"{BROKER_URL}/consume")
            json_data = resp.json()

            if json_data:
                print(color + f"[CONSUMER {consumer_id}] Tomó mensaje {json_data['id']}: {json_data['payload']}" + Style.RESET_ALL)

                # tiempo de servicio
                time.sleep(random.uniform(1, 4))

                print(color + f"[CONSUMER {consumer_id}] Procesado mensaje {json_data['id']}" + Style.RESET_ALL)
            else:
                print(color + f"[CONSUMER {consumer_id}] No hay mensajes, esperando..." + Style.RESET_ALL)
                time.sleep(1)

    except KeyboardInterrupt:
        print(color + f"[CONSUMER {consumer_id}] Detenido." + Style.RESET_ALL)


if __name__ == "__main__":
    main()
