# Dashboard Node-RED — Semáforo Inteligente com Catraca

Checkpoint de Edge Computing & Computer Systems (FIAP).

## Integrantes

- Luis Gabriel Pinheiro Stuermer
- Arthur Veiga Demétrio
- Carlos Adami

## Sobre o projeto

O projeto é um semáforo de pedestres com catraca automática, conectado à IoT:

- Um **LED RGB** representa o semáforo (verde → amarelo → vermelho).
- Um **micro servo SG90** é a catraca: abre no verde e fecha no vermelho.
- Um **sensor PIR HC-SR501** detecta travessia irregular quando o sinal está vermelho.
- O **Arduino UNO** lê os sensores e envia os dados por UART ao **ESP32** (simulador), que publica cada valor em um broker **MQTT**.

Neste checkpoint foi criado o **dashboard em Node-RED**, que assina os tópicos MQTT e mostra o estado do sistema em tempo real.

![Dashboard em funcionamento](prints/dashboard.png)

## Arquitetura

```
Arduino UNO ──UART──▶ ESP32 (simulador) ──MQTT──▶ Mosquitto ──MQTT──▶ Node-RED ──▶ Dashboard (navegador)
```

## Tópicos MQTT utilizados

Broker: `localhost:1883`. Device ID: `semaforo001`.

| Tópico | Payload | Significado |
|---|---|---|
| `/TEF/semaforo001/attrs/s` | `0`, `1` ou `2` | Fase do semáforo: 0 = verde, 1 = amarelo, 2 = vermelho |
| `/TEF/semaforo001/attrs/a` | `0` a `90` | Ângulo atual da catraca, em graus |
| `/TEF/semaforo001/attrs/p` | `0` ou `1` | Presença detectada pelo PIR |

## O que o dashboard mostra

A aba **Semáforo Inteligente** tem cinco grupos de widgets:

| Grupo | Widget | O que faz |
|---|---|---|
| Semáforo de pedestres | Semáforo visual (template HTML/CSS) | Acende a luz vermelha, amarela ou verde conforme a fase recebida |
| Catraca | Gauge de ângulo (0 a 90°) | Mostra o ângulo atual do servo |
| Catraca | Texto de situação | `ABERTA`, `FECHADA` ou `EM MOVIMENTO` |
| Sensor PIR e alertas | Texto de presença | `DETECTADA` ou `Livre` |
| Sensor PIR e alertas | Contador de travessias irregulares | Soma cada detecção que acontece com o sinal vermelho |
| Sensor PIR e alertas | Botão "Zerar contador" | Reinicia o contador |
| Sensor PIR e alertas | Alerta na tela (toast) | Aviso em destaque a cada travessia irregular |
| Sensor PIR e alertas | Status do dispositivo | `ONLINE` enquanto chegam dados; vira `OFFLINE` após 20 s sem mensagens |
| Últimos eventos | Lista de eventos com horário | Mudanças de fase, posição da catraca, presença e alertas |
| Histórico (últimos 10 min) | 3 gráficos | Fase, ângulo da catraca e presença ao longo do tempo |

### Regra da travessia irregular

Uma travessia irregular é registrada quando a presença muda de `0` para `1` **com o semáforo em vermelho**. Para isso o fluxo guarda a última fase recebida (variável global `estado`) e compara com a presença a cada mensagem. A detecção por borda evita contar várias vezes a mesma pessoa enquanto o PIR fica em `1`.

## Estrutura do repositório

```
dashboard-nodered/
├── flows.json            # fluxo do Node-RED (importar no editor)
├── simulador_mqtt.py     # publica dados de teste, sem precisar do hardware
├── gerar_flow.py         # script que gera o flows.json (opcional)
├── prints/               # capturas de tela do dashboard
└── README.md
```

## Como executar

### 1. Pré-requisitos

- [Node.js](https://nodejs.org) 18 ou superior
- [Node-RED](https://nodered.org/docs/getting-started/local): `npm install -g --unsafe-perm node-red`
- Broker [Mosquitto](https://mosquitto.org/download/) rodando na porta 1883. Com Docker, basta um comando:
  `docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf`
- Python 3 com `paho-mqtt` (só para o simulador): `pip install paho-mqtt`

### 2. Instalar o pacote do dashboard

```bash
cd ~/.node-red
npm install node-red-dashboard
```

Também dá para instalar pelo editor: **Menu → Manage palette → Install → `node-red-dashboard`**.

### 3. Subir o Node-RED e importar o fluxo

```bash
node-red
```

1. Abrir `http://localhost:1880`.
2. **Menu → Import → Select a file to import** e escolher `flows.json`.
3. Clicar em **Import** e depois em **Deploy**.
4. Se o broker estiver em outro endereço, dar duplo clique em qualquer nó `mqtt in`, editar o servidor "Mosquitto local" e ajustar host e porta.

### 4. Gerar dados

**Opção A: com o projeto completo** (Arduino + simulador ESP32 do professor):

1. Rodar o Mosquitto.
2. Conectar o Arduino e executar o `ESP32Mock`, como descrito no README do checkpoint 2.

**Opção B: só com o simulador Python** (para testar o dashboard):

```bash
python simulador_mqtt.py
```

Para conferir se as mensagens chegam ao broker:

```bash
mosquitto_sub -h localhost -t '/TEF/semaforo001/#' -v
```

### 5. Abrir o dashboard

`http://localhost:1880/ui`

## Como o fluxo está organizado

Cada tópico segue um caminho próprio no editor:

1. **`mqtt in`**: assina o tópico.
2. **Função "Interpretar ..."**: valida a faixa do valor (descarta fase fora de 0 a 2, ângulo fora de 0 a 180 e presença diferente de 0/1), transforma o dado em texto legível e envia para os widgets, para o gráfico e para o registro de eventos.
3. **Widgets** (`ui_template`, `ui_gauge`, `ui_text`, `ui_chart`, `ui_toast`).
4. **Nó `trigger`** ligado aos três tópicos: se nenhuma mensagem chegar por 20 s, o status do dispositivo muda para `OFFLINE`.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Os nós `mqtt in` mostram "connecting" | Broker fora do ar ou host/porta errados no nó de configuração |
| Nós `ui_*` aparecem em vermelho ou como "unknown" ao importar | `node-red-dashboard` não instalado |
| Dashboard fica em "Aguardando dados..." | Nada está publicando nos tópicos; testar com `mosquitto_sub` |
| Contador de travessias não aumenta | A presença só conta se a última fase recebida for vermelho (`2`) |
