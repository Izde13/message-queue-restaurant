from fastapi import FastAPI
from pydantic import BaseModel
from collections import deque
from datetime import datetime
import threading
import time
import uvicorn

app = FastAPI(title="Simple Message Broker")

# ==== Modelos ====

class ProduceRequest(BaseModel):
    payload: str  # contenido del mensaje (ej: "Pedido hamburguesa X")


class ConsumeResponse(BaseModel):
    id: int
    payload: str
    enqueued_at: datetime
    dequeued_at: datetime
    wait_time_seconds: float


class Metrics(BaseModel):
    queue_length: int
    total_produced: int
    total_consumed: int
    avg_wait_time_seconds: float | None


# ==== Estructuras de datos en memoria ====

queue = deque()  # cola de mensajes
next_id = 1      # ID incremental para los mensajes

# estadísticas
total_produced = 0
total_consumed = 0
total_wait_time = 0.0  # en segundos

lock = threading.Lock()  # para evitar condiciones de carrera


# ==== Endpoints REST ====

@app.post("/produce")
def produce(req: ProduceRequest):
    """
    Productor envía un mensaje a la cola.
    """
    global next_id, total_produced

    with lock:
        message_id = next_id
        next_id += 1
        enqueued_at = datetime.utcnow()
        queue.append({
            "id": message_id,
            "payload": req.payload,
            "enqueued_at": enqueued_at,
        })
        total_produced += 1

        print(f"[BROKER] Mensaje {message_id} encolado: {req.payload}")
        print(f"[BROKER] Cola actual (FIFO): {[item['id'] for item in queue]}")

    return {"status": "ok", "id": message_id, "enqueued_at": enqueued_at}


@app.post("/consume", response_model=ConsumeResponse | None)
def consume():
    """
    Consumidor pide un mensaje. Si no hay, devolvemos None.
    """
    global total_consumed, total_wait_time

    with lock:
        if not queue:
            # No hay mensajes en cola
            return None

        msg = queue.popleft()
        dequeued_at = datetime.utcnow()
        wait_time = (dequeued_at - msg["enqueued_at"]).total_seconds()

        total_consumed += 1
        total_wait_time += wait_time

    print(
        f"[BROKER] Mensaje {msg['id']} desencolado. Esperó {wait_time:.3f} s. "
        f"Payload: {msg['payload']}"
    )
    print(f"[BROKER] Cola después de consumir: {[item['id'] for item in queue]}")

    return ConsumeResponse(
        id=msg["id"],
        payload=msg["payload"],
        enqueued_at=msg["enqueued_at"],
        dequeued_at=dequeued_at,
        wait_time_seconds=wait_time,
    )


@app.get("/metrics", response_model=Metrics)
def metrics():
    """
    Métricas básicas del sistema.
    """
    with lock:
        avg_wait = (
            total_wait_time / total_consumed
            if total_consumed > 0
            else None
        )

        return Metrics(
            queue_length=len(queue),
            total_produced=total_produced,
            total_consumed=total_consumed,
            avg_wait_time_seconds=avg_wait,
        )

@app.get("/queue")
def get_queue_state():
    with lock:
        return {
            "queue_ids": [msg["id"] for msg in queue],
            "length": len(queue),
            "messages": queue
        }


# ==== Hilo para imprimir métricas periódicamente ====

def log_metrics_periodically(interval_seconds: int = 2):
    while True:
        time.sleep(interval_seconds)
        with lock:
            queue_ids = [msg["id"] for msg in queue]
            avg_wait = (
                total_wait_time / total_consumed
                if total_consumed > 0 else 0.0
            )

            print("\n===== ESTADO DEL SISTEMA =====")
            print(f" Cola FIFO: {queue_ids}")
            print(f" Largo cola: {len(queue)}")
            print(f" Producidos: {total_produced}")
            print(f" Consumidos: {total_consumed}")
            print(f" Espera prom: {avg_wait:.2f} s")
            print("===============================\n")

if __name__ == "__main__":
    # Lanzamos hilo para log de métricas
    t = threading.Thread(target=log_metrics_periodically, daemon=True)
    t.start()

    # Levantamos la API
    uvicorn.run(app, host="0.0.0.0", port=8000)
