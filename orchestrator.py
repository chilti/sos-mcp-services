#!/usr/bin/env python3
"""
SOS-MCP Services Orchestrator & Daemon Manager
Centralizes and manages the 7 FastMCP microservices in HTTP/SSE daemon mode.
Runs natively with Python /home/ambientesPy/revistaslatam for GPU CUDA, DuckDB and ClickHouse support.
"""

import os
import sys
import json
import time
import signal
import socket
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

BASE_DIR = Path(__file__).resolve().parent
PYTHON_BIN = Path("/home/ambientesPy/revistaslatam/bin/python")
LOGS_DIR = BASE_DIR / "logs"
PID_FILE = BASE_DIR / ".pids.json"

SERVICES: Dict[str, Dict[str, Any]] = {
    "knomap": {
        "port": 8010,
        "script": BASE_DIR / "services/knomap/mcp_server.py",
        "description": "KnoMap SOM (CUDA RTX 4090) & Louvain Communities Engine",
        "pythonpath": f"{BASE_DIR}:/home/labsom/knomap"
    },
    "sinapsisai": {
        "port": 8011,
        "script": BASE_DIR / "services/sinapsisai/mcp_server.py",
        "description": "SinapsisAI SNII Resolver & DuckDB Analytics (14 tables)",
        "pythonpath": f"{BASE_DIR}:/home/sinapsisai"
    },
    "plmetrix": {
        "port": 8012,
        "script": BASE_DIR / "services/plmetrix/mcp_server.py",
        "description": "PLMetrix Bibliometric Laws & Impact Indices Engine",
        "pythonpath": f"{BASE_DIR}"
    },
    "revistaslatam": {
        "port": 8013,
        "script": BASE_DIR / "services/revistaslatam/mcp_server.py",
        "description": "RevistasLatam Journals & Diamond Open Access Engine",
        "pythonpath": f"{BASE_DIR}:/mnt/ssd/revistaslatam"
    },
    "topics": {
        "port": 8014,
        "script": BASE_DIR / "services/topics/mcp_server.py",
        "description": "Topics & Research Fronts Multimodal Engine (Salton / AMI)",
        "pythonpath": f"{BASE_DIR}:/mnt/expansion/desplegados/Topics"
    },
    "openalex": {
        "port": 8015,
        "script": BASE_DIR / "services/openalex/mcp_server.py",
        "description": "OpenAlex Mexico Analytics & Nomic Semantics Gateway",
        "pythonpath": f"{BASE_DIR}"
    },
    "openproject": {
        "port": 8016,
        "script": BASE_DIR / "services/openproject/mcp_server.py",
        "description": "OpenProject PM Gateway",
        "pythonpath": f"{BASE_DIR}"
    }
}


def _load_pids() -> Dict[str, int]:
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_pids(pids: Dict[str, int]) -> None:
    with open(PID_FILE, "w", encoding="utf-8") as f:
        json.dump(pids, f, indent=2)


def is_process_running(pid: int) -> bool:
    """Verifica si un proceso con el PID dado está activo en el sistema operativo."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """Verifica si el puerto local está aceptando conexiones TCP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def start_service(name: str, pids: Dict[str, int], host: str = "0.0.0.0") -> bool:
    """Inicia un microservicio en segundo plano."""
    if name not in SERVICES:
        print(f"[!] Servicio desconocido: {name}")
        return False

    cfg = SERVICES[name]
    port = cfg["port"]
    script_path = cfg["script"]

    # Verificar si ya está corriendo
    current_pid = pids.get(name)
    if current_pid and is_process_running(current_pid):
        print(f"[*] {name:<14} ya está corriendo (PID {current_pid}, puerto {port}).")
        return True

    # Verificar si el puerto está ocupado por otro proceso
    if is_port_listening(port):
        print(f"[!] Puerto {port} para {name} ya está en uso por otro proceso.")
        return False

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{name}.log"
    out = open(log_file, "a", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = cfg["pythonpath"]
    env["MCP_TRANSPORT"] = "sse"
    env["PORT"] = str(port)
    env["HOST"] = host

    proc = subprocess.Popen(
        [str(PYTHON_BIN), str(script_path)],
        stdout=out,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(BASE_DIR),
        start_new_session=True
    )

    pids[name] = proc.pid
    _save_pids(pids)

    # Esperar hasta 3 segundos a que el puerto abra
    started = False
    for _ in range(6):
        time.sleep(0.5)
        if is_port_listening(port):
            started = True
            break

    if started:
        print(f"[✓] {name:<14} iniciado en http://{host}:{port}/sse (PID {proc.pid})")
        return True
    else:
        print(f"[?] {name:<14} lanzado con PID {proc.pid}, verificando inicio en log: {log_file}")
        return True


def stop_service(name: str, pids: Dict[str, int]) -> bool:
    """Detiene un microservicio en segundo plano."""
    current_pid = pids.get(name)
    if not current_pid:
        print(f"[-] {name:<14} no está registrado en ejecución.")
        return True

    if not is_process_running(current_pid):
        print(f"[-] {name:<14} no estaba activo (PID {current_pid} huérfano). Limpiando registro.")
        del pids[name]
        _save_pids(pids)
        return True

    try:
        os.kill(current_pid, signal.SIGTERM)
        for _ in range(10):
            time.sleep(0.3)
            if not is_process_running(current_pid):
                break
        if is_process_running(current_pid):
            os.kill(current_pid, signal.SIGKILL)
        print(f"[✓] {name:<14} detenido (PID {current_pid}).")
    except Exception as e:
        print(f"[!] Error deteniendo {name}: {e}")

    del pids[name]
    _save_pids(pids)
    return True


def get_service_status(name: str, pids: Dict[str, int]) -> Dict[str, Any]:
    cfg = SERVICES[name]
    port = cfg["port"]
    pid = pids.get(name)
    is_alive = bool(pid and is_process_running(pid))
    port_open = is_port_listening(port)

    status_str = "ONLINE" if (is_alive and port_open) else ("STARTING" if is_alive else "STOPPED")
    return {
        "name": name,
        "pid": pid if is_alive else None,
        "port": port,
        "status": status_str,
        "url": f"http://127.0.0.1:{port}/sse",
        "description": cfg["description"]
    }


def cmd_start(args):
    pids = _load_pids()
    target = args.service
    services = [target] if target != "all" else list(SERVICES.keys())

    print(f"\n🚀 Iniciando servicios MCP ({'todos' if target == 'all' else target})...\n")
    for s_name in services:
        start_service(s_name, pids, host=args.host)
    print("\n✅ Operación de inicio completada.\n")


def cmd_stop(args):
    pids = _load_pids()
    target = args.service
    services = [target] if target != "all" else list(SERVICES.keys())

    print(f"\n🛑 Deteniendo servicios MCP ({'todos' if target == 'all' else target})...\n")
    for s_name in services:
        stop_service(s_name, pids)
    print("\n✅ Operación de detención completada.\n")


def cmd_restart(args):
    cmd_stop(args)
    time.sleep(1)
    cmd_start(args)


def cmd_status(args):
    pids = _load_pids()
    print("\n" + "=" * 90)
    print(f"{'SERVICIO':<16} {'PUERTO':<8} {'PID':<8} {'ESTADO':<10} {'URL SSE':<28} {'DESCRIPCIÓN'}")
    print("=" * 90)

    for s_name in SERVICES:
        st = get_service_status(s_name, pids)
        st_color = st["status"]
        pid_str = str(st["pid"]) if st["pid"] else "-"
        print(f"{st['name']:<16} {st['port']:<8} {pid_str:<8} {st_color:<10} {st['url']:<28} {st['description']}")
    print("=" * 90 + "\n")


def cmd_logs(args):
    s_name = args.service
    if s_name not in SERVICES:
        print(f"[!] Servicio desconocido: {s_name}")
        return
    log_file = LOGS_DIR / f"{s_name}.log"
    if not log_file.exists():
        print(f"[-] No hay archivo de registro para {s_name} ({log_file})")
        return

    n_lines = args.lines
    print(f"\n--- Últimas {n_lines} líneas de {log_file} ---")
    try:
        res = subprocess.run(["tail", "-n", str(n_lines), str(log_file)], capture_output=True, text=True)
        print(res.stdout)
    except Exception as e:
        print(f"Error leyendo log: {e}")


def main():
    parser = argparse.ArgumentParser(description="Orchestrator para SOS-MCP Services (SSE/HTTP daemons)")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # Start
    p_start = subparsers.add_parser("start", help="Iniciar microservicio(s)")
    p_start.add_argument("service", nargs="?", default="all", choices=list(SERVICES.keys()) + ["all"], help="Servicio o 'all'")
    p_start.add_argument("--host", default="0.0.0.0", help="Host bind (0.0.0.0 o 127.0.0.1)")

    # Stop
    p_stop = subparsers.add_parser("stop", help="Detener microservicio(s)")
    p_stop.add_argument("service", nargs="?", default="all", choices=list(SERVICES.keys()) + ["all"], help="Servicio o 'all'")

    # Restart
    p_restart = subparsers.add_parser("restart", help="Reiniciar microservicio(s)")
    p_restart.add_argument("service", nargs="?", default="all", choices=list(SERVICES.keys()) + ["all"], help="Servicio o 'all'")
    p_restart.add_argument("--host", default="0.0.0.0", help="Host bind (0.0.0.0 o 127.0.0.1)")

    # Status
    subparsers.add_parser("status", help="Consultar estado de todos los microservicios")

    # Logs
    p_logs = subparsers.add_parser("logs", help="Ver registros de un microservicio")
    p_logs.add_argument("service", choices=list(SERVICES.keys()), help="Nombre del servicio")
    p_logs.add_argument("-n", "--lines", type=int, default=50, help="Número de líneas")

    args = parser.parse_args()

    if args.action == "start":
        cmd_start(args)
    elif args.action == "stop":
        cmd_stop(args)
    elif args.action == "restart":
        cmd_restart(args)
    elif args.action == "status":
        cmd_status(args)
    elif args.action == "logs":
        cmd_logs(args)


if __name__ == "__main__":
    main()
