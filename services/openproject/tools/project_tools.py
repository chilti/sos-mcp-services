from typing import Dict, Any, List, Optional
from services.openproject.tools.client import OpenProjectClient

def openproject_list_projects() -> List[Dict[str, Any]]:
    """
    Lista todos los proyectos disponibles en OpenProject.
    Retorna el ID, nombre, identificador, descripción y estado de cada proyecto.
    """
    client = OpenProjectClient()
    res = client.get("/api/v3/projects")
    elements = res.get("_embedded", {}).get("elements", [])
    projects = []
    for el in elements:
        desc = el.get("description", {})
        raw_desc = desc.get("raw", "") if isinstance(desc, dict) else str(desc)
        status_info = el.get("_embedded", {}).get("status", {}).get("name", "N/A")
        projects.append({
            "id": el.get("id"),
            "name": el.get("name"),
            "identifier": el.get("identifier"),
            "active": el.get("active", True),
            "public": el.get("public", False),
            "status": status_info,
            "description": raw_desc
        })
    return projects

def openproject_get_project(project_id_or_identifier: str) -> Dict[str, Any]:
    """
    Obtiene los detalles de un proyecto por su ID numérico o identificador (slug).
    """
    client = OpenProjectClient()
    res = client.get(f"/api/v3/projects/{project_id_or_identifier}")
    desc = res.get("description", {})
    raw_desc = desc.get("raw", "") if isinstance(desc, dict) else str(desc)
    return {
        "id": res.get("id"),
        "name": res.get("name"),
        "identifier": res.get("identifier"),
        "active": res.get("active"),
        "public": res.get("public"),
        "created_at": res.get("createdAt"),
        "updated_at": res.get("updatedAt"),
        "description": raw_desc
    }

def openproject_create_project(
    name: str,
    identifier: Optional[str] = None,
    description: Optional[str] = None,
    public: bool = False
) -> Dict[str, Any]:
    """
    Crea un nuevo proyecto en OpenProject.
    
    Args:
        name: Nombre legible del proyecto.
        identifier: Identificador slug único (letras minúsculas, números, guiones). Si no se provee, se deriva del nombre.
        description: Descripción general o alcance del proyecto en markdown.
        public: Si el proyecto debe ser público o privado (default: False).
    """
    client = OpenProjectClient()
    payload: Dict[str, Any] = {
        "name": name,
        "public": public
    }
    if identifier:
        payload["identifier"] = identifier
    if description:
        payload["description"] = {
            "format": "markdown",
            "raw": description
        }
    res = client.post("/api/v3/projects", payload)
    return {
        "id": res.get("id"),
        "name": res.get("name"),
        "identifier": res.get("identifier"),
        "message": f"Proyecto '{name}' creado exitosamente con ID {res.get('id')}."
    }

def openproject_list_work_packages(
    project_id_or_identifier: Optional[str] = None,
    include_closed: bool = True,
    page_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Lista los paquetes de trabajo (tareas, hitos, funciones, épicos) en OpenProject, opcionalmente filtrados por proyecto.
    """
    import json
    client = OpenProjectClient()
    endpoint = f"/api/v3/projects/{project_id_or_identifier}/work_packages" if project_id_or_identifier else "/api/v3/work_packages"
    params: Dict[str, Any] = {"pageSize": page_size}
    if include_closed:
        params["filters"] = json.dumps([{"status": {"operator": "*", "values": []}}])
    res = client.get(endpoint, params=params)
    elements = res.get("_embedded", {}).get("elements", [])
    wps = []
    for el in elements:
        type_name = el.get("_links", {}).get("type", {}).get("title", "Task")
        status_name = el.get("_links", {}).get("status", {}).get("title", "New")
        priority_name = el.get("_links", {}).get("priority", {}).get("title", "Normal")
        project_name = el.get("_links", {}).get("project", {}).get("title", "")
        assignee_name = el.get("_links", {}).get("assignee", {}).get("title", "Unassigned")
        desc = el.get("description", {})
        raw_desc = desc.get("raw", "") if isinstance(desc, dict) else str(desc)

        wps.append({
            "id": el.get("id"),
            "subject": el.get("subject"),
            "type": type_name,
            "status": status_name,
            "priority": priority_name,
            "project": project_name,
            "assignee": assignee_name,
            "start_date": el.get("startDate"),
            "due_date": el.get("dueDate"),
            "percentage_done": el.get("percentageDone", 0),
            "estimated_time": el.get("estimatedTime"),
            "lock_version": el.get("lockVersion", 0),
            "description": raw_desc
        })
    return wps

def openproject_get_work_package(work_package_id: int) -> Dict[str, Any]:
    """
    Obtiene los detalles completos de una tarea o paquete de trabajo por su ID.
    """
    client = OpenProjectClient()
    el = client.get(f"/api/v3/work_packages/{work_package_id}")
    type_name = el.get("_links", {}).get("type", {}).get("title", "Task")
    status_name = el.get("_links", {}).get("status", {}).get("title", "New")
    priority_name = el.get("_links", {}).get("priority", {}).get("title", "Normal")
    project_name = el.get("_links", {}).get("project", {}).get("title", "")
    assignee_name = el.get("_links", {}).get("assignee", {}).get("title", "Unassigned")
    desc = el.get("description", {})
    raw_desc = desc.get("raw", "") if isinstance(desc, dict) else str(desc)

    return {
        "id": el.get("id"),
        "subject": el.get("subject"),
        "type": type_name,
        "status": status_name,
        "priority": priority_name,
        "project": project_name,
        "assignee": assignee_name,
        "start_date": el.get("startDate"),
        "due_date": el.get("dueDate"),
        "percentage_done": el.get("percentageDone", 0),
        "estimated_time": el.get("estimatedTime"),
        "lock_version": el.get("lockVersion", 0),
        "created_at": el.get("createdAt"),
        "updated_at": el.get("updatedAt"),
        "description": raw_desc
    }

def openproject_create_work_package(
    project_id: int,
    subject: str,
    description: Optional[str] = None,
    type_id: Optional[int] = None,
    status_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    estimated_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva tarea, paquete de trabajo o hito dentro de un proyecto.

    Args:
        project_id: ID numérico del proyecto donde se creará la tarea.
        subject: Título o asunto de la tarea.
        description: Descripción detallada de la tarea en markdown.
        type_id: ID numérico del tipo (1=Task, etc.). Si es None, se usa el tipo por defecto.
        status_id: ID numérico del estado inicial.
        priority_id: ID numérico de la prioridad.
        start_date: Fecha de inicio en formato 'YYYY-MM-DD'.
        due_date: Fecha límite en formato 'YYYY-MM-DD'.
        estimated_time: Estimación de tiempo en formato ISO 8601 (ej. 'PT4H' para 4 horas).
    """
    client = OpenProjectClient()
    payload: Dict[str, Any] = {
        "subject": subject,
        "_links": {
            "project": {"href": f"/api/v3/projects/{project_id}"}
        }
    }
    if description:
        payload["description"] = {"format": "markdown", "raw": description}
    if type_id:
        payload["_links"]["type"] = {"href": f"/api/v3/types/{type_id}"}
    if status_id:
        payload["_links"]["status"] = {"href": f"/api/v3/statuses/{status_id}"}
    if priority_id:
        payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
    if start_date:
        payload["startDate"] = start_date
    if due_date:
        payload["dueDate"] = due_date
    if estimated_time:
        payload["estimatedTime"] = estimated_time

    res = client.post("/api/v3/work_packages", payload)
    return {
        "id": res.get("id"),
        "subject": res.get("subject"),
        "lock_version": res.get("lockVersion", 0),
        "message": f"Tarea '{subject}' creada exitosamente con ID {res.get('id')}."
    }

def openproject_update_work_package(
    work_package_id: int,
    lock_version: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    status_id: Optional[int] = None,
    percentage_done: Optional[int] = None,
    due_date: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Actualiza una tarea existente (estado, avance %, descripción, fecha límite) y permite agregar una nota de bitácora.

    Args:
        work_package_id: ID de la tarea a actualizar.
        lock_version: Versión de bloqueo actual (requerido por OpenProject para control de concurrencia optimista).
        subject: Nuevo asunto (opcional).
        description: Nueva descripción en markdown (opcional).
        status_id: ID numérico del nuevo estado (opcional).
        percentage_done: Porcentaje de avance de 0 a 100 (opcional).
        due_date: Nueva fecha de vencimiento 'YYYY-MM-DD' (opcional).
        notes: Comentario o nota explicativa sobre la actualización (opcional).
    """
    client = OpenProjectClient()
    payload: Dict[str, Any] = {
        "lockVersion": lock_version
    }
    if subject:
        payload["subject"] = subject
    if description:
        payload["description"] = {"format": "markdown", "raw": description}
    if percentage_done is not None:
        payload["percentageDone"] = percentage_done
    if due_date:
        payload["dueDate"] = due_date
    if notes:
        payload["comment"] = {"format": "markdown", "raw": notes}
    if status_id:
        payload.setdefault("_links", {})["status"] = {"href": f"/api/v3/statuses/{status_id}"}

    res = client.patch(f"/api/v3/work_packages/{work_package_id}", payload)
    return {
        "id": res.get("id"),
        "subject": res.get("subject"),
        "lock_version": res.get("lockVersion"),
        "message": f"Tarea {work_package_id} actualizada correctamente."
    }

def openproject_add_comment(work_package_id: int, comment: str) -> Dict[str, Any]:
    """
    Agrega un comentario o actualización de bitácora a una tarea o paquete de trabajo.
    """
    client = OpenProjectClient()
    # Para agregar comentario en OpenProject v3 se puede obtener el lockVersion actual y hacer patch
    wp = client.get(f"/api/v3/work_packages/{work_package_id}")
    lock_version = wp.get("lockVersion", 0)
    payload = {
        "lockVersion": lock_version,
        "comment": {
            "format": "markdown",
            "raw": comment
        }
    }
    res = client.patch(f"/api/v3/work_packages/{work_package_id}", payload)
    return {
        "id": res.get("id"),
        "message": f"Comentario agregado exitosamente a la tarea {work_package_id}."
    }

def openproject_list_types() -> List[Dict[str, Any]]:
    """
    Lista los tipos de paquetes de trabajo disponibles en OpenProject (Task, Milestone, Phase, Bug, etc.).
    """
    client = OpenProjectClient()
    res = client.get("/api/v3/types")
    elements = res.get("_embedded", {}).get("elements", [])
    return [{"id": el.get("id"), "name": el.get("name"), "is_milestone": el.get("isMilestone", False)} for el in elements]

def openproject_list_statuses() -> List[Dict[str, Any]]:
    """
    Lista todos los estados disponibles de tareas (New, In progress, Developed, Closed, etc.).
    """
    client = OpenProjectClient()
    res = client.get("/api/v3/statuses")
    elements = res.get("_embedded", {}).get("elements", [])
    return [{"id": el.get("id"), "name": el.get("name"), "is_closed": el.get("isClosed", False)} for el in elements]

def openproject_list_users() -> List[Dict[str, Any]]:
    """
    Lista las cuentas de usuarios registradas en el sistema OpenProject.
    """
    client = OpenProjectClient()
    res = client.get("/api/v3/users")
    elements = res.get("_embedded", {}).get("elements", [])
    return [{"id": el.get("id"), "name": el.get("name"), "email": el.get("email"), "status": el.get("status")} for el in elements]
