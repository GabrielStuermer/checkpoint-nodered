import json

Z = "tab_semaforo"
BROKER = "mqtt_broker"
TAB = "ui_tab_sem"
G_SEM, G_CAT, G_SEN, G_EVT, G_HIS = "g_sem", "g_cat", "g_sen", "g_evt", "g_his"

nodes = []


def add(n):
    nodes.append(n)


add({"id": Z, "type": "tab", "label": "Semáforo Inteligente", "disabled": False,
     "info": "Dashboard do semáforo inteligente com catraca (FIAP Edge Computing)."})

add({"id": BROKER, "type": "mqtt-broker", "name": "Mosquitto local",
     "broker": "localhost", "port": "1883", "clientid": "nodered-dash-semaforo",
     "autoConnect": True, "usetls": False, "protocolVersion": "4", "keepalive": "60",
     "cleansession": True, "autoUnsubscribe": True,
     "birthTopic": "", "birthQos": "0", "birthPayload": "", "birthMsg": {},
     "closeTopic": "", "closeQos": "0", "closePayload": "", "closeMsg": {},
     "willTopic": "", "willQos": "0", "willPayload": "", "willMsg": {},
     "userProps": "", "sessionExpiry": ""})

add({"id": TAB, "type": "ui_tab", "name": "Semáforo Inteligente", "icon": "dashboard",
     "disabled": False, "hidden": False})


def group(gid, name, order, width="6"):
    add({"id": gid, "type": "ui_group", "name": name, "tab": TAB, "order": order,
         "disp": True, "width": width, "collapse": False, "className": ""})


group(G_SEM, "Semáforo de pedestres", 1)
group(G_CAT, "Catraca", 2)
group(G_SEN, "Sensor PIR e alertas", 3)
group(G_EVT, "Últimos eventos", 4)
group(G_HIS, "Histórico (últimos 10 min)", 5, "12")

add({"id": "c_info", "type": "comment", "z": Z, "name": "Tópicos MQTT: /TEF/semaforo001/attrs/{s,a,p}",
     "info": "s = fase (0 verde, 1 amarelo, 2 vermelho)\na = ângulo da catraca (graus)\np = presença PIR (0/1)",
     "x": 230, "y": 40, "wires": []})


def mqtt_in(nid, topic, y, wires):
    add({"id": nid, "type": "mqtt in", "z": Z, "name": topic.split("/")[-1],
         "topic": topic, "qos": "0", "datatype": "auto-detect", "broker": BROKER,
         "nl": False, "rap": True, "rh": 0, "inputs": 0, "x": 130, "y": y, "wires": [wires]})


def fn(nid, name, code, outputs, x, y, wires):
    add({"id": nid, "type": "function", "z": Z, "name": name, "func": code,
         "outputs": outputs, "timeout": 0, "noerr": 0, "initialize": "", "finalize": "",
         "libs": [], "x": x, "y": y, "wires": wires})


# ---------------- Fase do semáforo ----------------
mqtt_in("mq_s", "/TEF/semaforo001/attrs/s", 120, ["fn_estado", "tr_link"])
fn("fn_estado", "Interpretar fase", """const v = Number(msg.payload);
if (![0, 1, 2].includes(v)) {
    node.warn('Fase invalida: ' + msg.payload);
    return null;
}
const nomes = ['VERDE', 'AMARELO', 'VERMELHO'];
global.set('estado', v);
return [
    { payload: v, nome: nomes[v] },
    { payload: v, topic: 'Fase (0=verde, 1=amarelo, 2=vermelho)' },
    { payload: 'Semáforo: ' + nomes[v] }
];""", 3, 400, 120, [["ui_sem"], ["ch_fase"], ["fn_log"]])

add({"id": "ui_sem", "type": "ui_template", "z": Z, "group": G_SEM, "name": "Semáforo visual",
     "order": 1, "width": "6", "height": "6", "format":
     "<style>\n"
     ".sem{display:flex;flex-direction:column;align-items:center;gap:10px;padding:14px;"
     "background:#222;border-radius:18px;width:110px;margin:4px auto}\n"
     ".luz{width:70px;height:70px;border-radius:50%;background:#555;opacity:.3;transition:all .3s}\n"
     ".luz.on.vermelho{background:#e74c3c;opacity:1;box-shadow:0 0 28px #e74c3c}\n"
     ".luz.on.amarelo{background:#f1c40f;opacity:1;box-shadow:0 0 28px #f1c40f}\n"
     ".luz.on.verde{background:#2ecc71;opacity:1;box-shadow:0 0 28px #2ecc71}\n"
     ".nome{text-align:center;font-weight:bold;font-size:18px;margin-top:4px}\n"
     "</style>\n"
     "<div class='sem'>\n"
     "  <div class='luz vermelho' ng-class='{on: msg.payload===2}'></div>\n"
     "  <div class='luz amarelo' ng-class='{on: msg.payload===1}'></div>\n"
     "  <div class='luz verde' ng-class='{on: msg.payload===0}'></div>\n"
     "</div>\n"
     "<div class='nome'>{{msg.nome || 'Aguardando dados...'}}</div>",
     "storeOutMessages": True, "fwdInMessages": False, "resendOnRefresh": True,
     "templateScope": "local", "className": "", "x": 650, "y": 80, "wires": [[]]})

add({"id": "ch_fase", "type": "ui_chart", "z": Z, "group": G_HIS, "name": "Gráfico da fase",
     "label": "Fase do semáforo (0=verde, 1=amarelo, 2=vermelho)", "order": 1, "width": "12",
     "height": "4", "chartType": "line", "legend": "false", "xformat": "HH:mm:ss",
     "interpolate": "step", "nodata": "Aguardando dados...", "dot": False, "ymin": "0",
     "ymax": "2", "removeOlder": "10", "removeOlderPoints": "", "removeOlderUnit": "60",
     "cutout": 0, "useOneColor": False, "useUTC": False,
     "colors": ["#1f77b4", "#aec7e8", "#ff7f0e", "#2ca02c", "#98df8a", "#d62728",
                "#ff9896", "#9467bd", "#c5b0d5"],
     "outputs": 1, "useDifferentColor": False, "className": "",
     "x": 650, "y": 120, "wires": [[]]})

# ---------------- Ângulo da catraca ----------------
mqtt_in("mq_a", "/TEF/semaforo001/attrs/a", 260, ["fn_angulo", "tr_link"])
fn("fn_angulo", "Interpretar ângulo", """const v = Number(msg.payload);
if (isNaN(v) || v < 0 || v > 180) {
    node.warn('Angulo invalido: ' + msg.payload);
    return null;
}
let situacao = 'EM MOVIMENTO';
if (v <= 5) situacao = 'FECHADA';
else if (v >= 85) situacao = 'ABERTA';
// so registra no log quando a situacao muda, para nao poluir a lista
const anterior = flow.get('situacaoCatraca');
flow.set('situacaoCatraca', situacao);
const log = situacao !== anterior ? { payload: 'Catraca: ' + situacao + ' (' + v + '°)' } : null;
return [
    { payload: v },
    { payload: v, topic: 'Ângulo da catraca (graus)' },
    { payload: situacao },
    log
];""", 4, 400, 260, [["ga_ang"], ["ch_ang"], ["tx_cat"], ["fn_log"]])

add({"id": "ga_ang", "type": "ui_gauge", "z": Z, "name": "Ângulo", "group": G_CAT, "order": 1,
     "width": "6", "height": "4", "gtype": "gage", "title": "Ângulo da catraca",
     "label": "graus", "format": "{{value}}", "min": 0, "max": "90",
     "colors": ["#ca3838", "#e6e600", "#00b500"], "seg1": "", "seg2": "",
     "diff": False, "className": "", "x": 650, "y": 220, "wires": []})

add({"id": "tx_cat", "type": "ui_text", "z": Z, "group": G_CAT, "order": 2, "width": "6",
     "height": "1", "name": "Situação da catraca", "label": "Situação", "format": "{{msg.payload}}",
     "layout": "row-spread", "className": "", "style": True, "font": "", "fontSize": "20",
     "color": "#000000", "x": 660, "y": 260, "wires": []})

add({"id": "ch_ang", "type": "ui_chart", "z": Z, "group": G_HIS, "name": "Gráfico do ângulo",
     "label": "Ângulo da catraca (graus)", "order": 2, "width": "12", "height": "4",
     "chartType": "line", "legend": "false", "xformat": "HH:mm:ss", "interpolate": "linear",
     "nodata": "Aguardando dados...", "dot": False, "ymin": "0", "ymax": "90",
     "removeOlder": "10", "removeOlderPoints": "", "removeOlderUnit": "60", "cutout": 0,
     "useOneColor": False, "useUTC": False,
     "colors": ["#1f77b4", "#aec7e8", "#ff7f0e", "#2ca02c", "#98df8a", "#d62728",
                "#ff9896", "#9467bd", "#c5b0d5"],
     "outputs": 1, "useDifferentColor": False, "className": "",
     "x": 660, "y": 300, "wires": [[]]})

# ---------------- Presença (PIR) ----------------
mqtt_in("mq_p", "/TEF/semaforo001/attrs/p", 420, ["fn_presenca", "tr_link"])
fn("fn_presenca", "Interpretar presença", """const v = Number(msg.payload);
if (![0, 1].includes(v)) {
    node.warn('Presenca invalida: ' + msg.payload);
    return null;
}
const anterior = flow.get('presAnterior') || 0;
flow.set('presAnterior', v);
const estado = global.get('estado');

let total = flow.get('irregulares') || 0;
let alerta = null;
let log = null;

// Borda de subida (0 -> 1) com o sinal vermelho = travessia irregular
if (v === 1 && anterior === 0) {
    if (estado === 2) {
        total += 1;
        flow.set('irregulares', total);
        alerta = { topic: 'ALERTA', payload: 'Travessia irregular detectada no sinal vermelho!' };
        log = { payload: 'ALERTA: travessia irregular (total: ' + total + ')' };
    } else {
        log = { payload: 'Pedestre detectado (travessia regular)' };
    }
}
return [
    { payload: v === 1 ? 'DETECTADA' : 'Livre', topic: 'Presença' },
    alerta,
    { payload: total },
    log,
    { payload: v, topic: 'Presença (0/1)' }
];""", 5, 400, 420, [["tx_pres"], ["toast_alerta"], ["tx_cont"], ["fn_log"], ["ch_pres"]])

add({"id": "tx_pres", "type": "ui_text", "z": Z, "group": G_SEN, "order": 1, "width": "6",
     "height": "1", "name": "Presença", "label": "Presença (PIR)", "format": "{{msg.payload}}",
     "layout": "row-spread", "className": "", "style": True, "font": "", "fontSize": "20",
     "color": "#000000", "x": 660, "y": 400, "wires": []})

add({"id": "tx_cont", "type": "ui_text", "z": Z, "group": G_SEN, "order": 2, "width": "6",
     "height": "1", "name": "Contador de travessias irregulares",
     "label": "Travessias irregulares", "format": "{{msg.payload}}", "layout": "row-spread",
     "className": "", "style": True, "font": "", "fontSize": "20", "color": "#c0392b",
     "x": 700, "y": 440, "wires": []})

add({"id": "toast_alerta", "type": "ui_toast", "z": Z, "position": "top right",
     "displayTime": "5", "highlight": "#e74c3c", "sendall": True, "outputs": 0, "ok": "OK",
     "cancel": "", "raw": False, "className": "", "topic": "", "name": "Alerta na tela",
     "x": 650, "y": 480, "wires": []})

add({"id": "ch_pres", "type": "ui_chart", "z": Z, "group": G_HIS, "name": "Gráfico de presença",
     "label": "Presença detectada (0/1)", "order": 3, "width": "12", "height": "3",
     "chartType": "line", "legend": "false", "xformat": "HH:mm:ss", "interpolate": "step",
     "nodata": "Aguardando dados...", "dot": False, "ymin": "0", "ymax": "1",
     "removeOlder": "10", "removeOlderPoints": "", "removeOlderUnit": "60", "cutout": 0,
     "useOneColor": False, "useUTC": False,
     "colors": ["#d62728", "#aec7e8", "#ff7f0e", "#2ca02c", "#98df8a", "#d62728",
                "#ff9896", "#9467bd", "#c5b0d5"],
     "outputs": 1, "useDifferentColor": False, "className": "",
     "x": 670, "y": 520, "wires": [[]]})

# Botão para zerar o contador
add({"id": "bt_reset", "type": "ui_button", "z": Z, "name": "Zerar contador", "group": G_SEN,
     "order": 3, "width": "6", "height": "1", "passthru": False, "label": "Zerar contador",
     "tooltip": "", "color": "", "bgcolor": "", "className": "", "icon": "refresh",
     "payload": "reset", "payloadType": "str", "topic": "reset", "topicType": "str",
     "x": 140, "y": 560, "wires": [["fn_reset"]]})
fn("fn_reset", "Zerar contador", """flow.set('irregulares', 0);
return [
    { payload: 0 },
    { payload: 'Contador de travessias zerado' }
];""", 2, 400, 560, [["tx_cont"], ["fn_log"]])

# ---------------- Conexão do dispositivo (watchdog) ----------------
add({"id": "tr_link", "type": "trigger", "z": Z, "name": "Sem dados por 20 s?", "op1": "ONLINE",
     "op2": "OFFLINE", "op1type": "str", "op2type": "str", "duration": "20", "extend": True,
     "overrideDelay": False, "units": "s", "reset": "", "bytopic": "all", "topic": "topic",
     "outputs": 1, "x": 400, "y": 620, "wires": [["tx_link"]]})

add({"id": "tx_link", "type": "ui_text", "z": Z, "group": G_SEN, "order": 4, "width": "6",
     "height": "1", "name": "Conexão", "label": "Dispositivo", "format": "{{msg.payload}}",
     "layout": "row-spread", "className": "", "style": True, "font": "", "fontSize": "20",
     "color": "#000000", "x": 660, "y": 620, "wires": []})

# ---------------- Log de eventos ----------------
fn("fn_log", "Registrar evento", """const lista = flow.get('eventos') || [];
const hora = new Date().toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo' });
lista.unshift(hora + ' - ' + msg.payload);
if (lista.length > 12) lista.length = 12;
flow.set('eventos', lista);
return { payload: lista };""", 1, 880, 300, [["ui_log"]])

add({"id": "ui_log", "type": "ui_template", "z": Z, "group": G_EVT, "name": "Lista de eventos",
     "order": 1, "width": "6", "height": "7", "format":
     "<div style='font-family:monospace;font-size:13px;line-height:1.6'>\n"
     "  <div ng-repeat='e in msg.payload track by $index'>{{e}}</div>\n"
     "  <div ng-if='!msg.payload'>Aguardando eventos...</div>\n"
     "</div>",
     "storeOutMessages": True, "fwdInMessages": False, "resendOnRefresh": True,
     "templateScope": "local", "className": "", "x": 1100, "y": 300, "wires": [[]]})

with open("flows.json", "w", encoding="utf-8") as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)

# valida se todos os wires apontam para nós existentes
ids = {n["id"] for n in nodes}
for n in nodes:
    for out in n.get("wires", []):
        for target in out:
            assert target in ids, f"wire quebrado: {n['id']} -> {target}"
    if n["type"] == "function":
        assert len(n["wires"]) == n["outputs"], n["id"]
print("ok:", len(nodes), "nós")
