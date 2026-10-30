"""Simulador do semáforo inteligente para testar o dashboard sem o hardware.

Publica nos mesmos tópicos que o ESP32 (simulador do professor) usa:
  /TEF/semaforo001/attrs/s  -> fase (0 verde, 1 amarelo, 2 vermelho)
  /TEF/semaforo001/attrs/a  -> ângulo da catraca (0 a 90)
  /TEF/semaforo001/attrs/p  -> presença PIR (0 ou 1)

Uso:
  pip install paho-mqtt
  python simulador_mqtt.py [--host localhost] [--port 1883]
"""
import argparse
import random
import time

import paho.mqtt.client as mqtt

DEVICE = "semaforo001"
TOPICO = f"/TEF/{DEVICE}/attrs/"
FASES = [(0, 10), (1, 5), (2, 10)]  # (fase, duração em s): verde, amarelo, vermelho
ANGULO_ABERTO, ANGULO_FECHADO = 90, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    args = ap.parse_args()

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:  # paho-mqtt 1.x
        client = mqtt.Client()
    client.connect(args.host, args.port, 60)
    client.loop_start()

    angulo = ANGULO_FECHADO
    print(f"Publicando em {args.host}:{args.port} {TOPICO}* (Ctrl+C para parar)")
    try:
        while True:
            for fase, duracao in FASES:
                client.publish(TOPICO + "s", str(fase))
                destino = ANGULO_ABERTO if fase == 0 else ANGULO_FECHADO if fase == 2 else angulo
                for t in range(duracao):
                    # a catraca se move gradualmente, como o servo real
                    passo = 15 if destino > angulo else -15
                    if angulo != destino:
                        angulo = max(0, min(90, angulo + passo))
                        if abs(angulo - destino) < 15:
                            angulo = destino
                    client.publish(TOPICO + "a", str(angulo))
                    # PIR: mais chance de disparar no vermelho, para gerar alertas
                    chance = 0.25 if fase == 2 else 0.1
                    presenca = 1 if random.random() < chance else 0
                    client.publish(TOPICO + "p", str(presenca))
                    print(f"fase={fase} angulo={angulo:>2} presenca={presenca}")
                    time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
