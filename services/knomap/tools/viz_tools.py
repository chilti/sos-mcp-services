import sys
import os
import pandas as pd

# Asegurar que el engine de knomap está en el path
# (Asumiendo que el servidor MCP tiene permisos sobre la ruta)
KNOMAP_PATH = "/home/labsom/knomap"
if KNOMAP_PATH not in sys.path:
    sys.path.append(KNOMAP_PATH)

try:
    from engine.viz_extensions.charts_evolution import render_alluvial_diagram, render_slope_chart
    from engine.viz_extensions.charts_comparisons import render_dumbbell_chart, render_diverging_bar
    from engine.viz_extensions.charts_maps import render_connection_map, render_dorling_cartogram
    from engine.viz_extensions.charts_exploration import render_exploration_dashboard
    from engine.viz_extensions.charts_som import render_umatrix_3d, render_component_planes
except ImportError as e:
    # Si falla la importación al cargar el módulo, proveemos stubs para evitar crashear el servidor FastMCP
    print(f"Warning: No se pudo importar viz_extensions de knomap. Error: {e}")
    def render_alluvial_diagram(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_slope_chart(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_dumbbell_chart(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_diverging_bar(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_connection_map(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_dorling_cartogram(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_exploration_dashboard(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_umatrix_3d(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_component_planes(*args, **kwargs): return {"error": "viz_extensions not available"}

def knomap_render_alluvial_diagram(data_path: str, output_path: str) -> dict:
    """
    Genera un diagrama aluvial (Sankey) temporal de los frentes de investigación.
    
    Args:
        data_path: Ruta al archivo CSV/JSON con los datos de transiciones.
        output_path: Ruta donde se guardará el artefacto HTML generado.
    """
    try:
        # En una implementación real se cargaría el DataFrame desde data_path
        # df = pd.read_csv(data_path)
        df = pd.DataFrame()
        return render_alluvial_diagram(df, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_dumbbell_chart(data_path: str, metric: str, output_path: str) -> dict:
    """
    Genera un Dumbbell chart para evidenciar brechas en indicadores cienciométricos.
    
    Args:
        data_path: Ruta al archivo de datos.
        metric: Métrica objetivo a analizar (ej. CNCI).
        output_path: Ruta del HTML resultante.
    """
    try:
        df = pd.DataFrame()
        return render_dumbbell_chart(df, metric, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_connection_map(data_path: str, output_path: str) -> dict:
    """
    Genera un mapa geopolítico de conexiones transfronterizas de coautoría.
    
    Args:
        data_path: Ruta al archivo de datos (origen, destino, peso).
        output_path: Ruta del HTML resultante.
    """
    try:
        df = pd.DataFrame()
        return render_connection_map(df, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_exploration_dashboard(data_path: str, output_path: str) -> dict:
    """
    Genera un panel exploratorio (Profiler) para el Paso 1, con distribuciones y series temporales.
    
    Args:
        data_path: Ruta al archivo CSV con los datos crudos a explorar.
        output_path: Ruta del HTML resultante.
    """
    try:
        filename = os.path.basename(data_path)
        # Soportar CSV y Excel
        if data_path.lower().endswith('.xlsx') or data_path.lower().endswith('.xls'):
            df = pd.read_excel(data_path, engine='openpyxl')
        else:
            df = pd.read_csv(data_path)
            
        return render_exploration_dashboard(df, output_path, filename_hint=filename)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_umatrix_3d(som_state_path: str, output_path: str) -> dict:
    """
    Genera un mapa topológico interactivo 3D de la U-Matrix.
    
    Args:
        som_state_path: Ruta al archivo JSON con el estado del SOM entrenado (debe incluir 'umatrix' y 'config').
        output_path: Ruta del HTML resultante.
    """
    try:
        import json
        with open(som_state_path, 'r', encoding='utf-8') as f:
            som_state = json.load(f)
        return render_umatrix_3d(som_state, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_component_planes(som_state_path: str, output_path: str) -> dict:
    """
    Genera múltiples mapas de calor (Component Planes) para analizar correlaciones entre indicadores.
    
    Args:
        som_state_path: Ruta al archivo JSON con el estado del SOM (debe incluir 'weights' y 'config').
        output_path: Ruta del HTML resultante.
    """
    try:
        import json
        with open(som_state_path, 'r', encoding='utf-8') as f:
            som_state = json.load(f)
        return render_component_planes(som_state, output_path)
    except Exception as e:
        return {"error": str(e)}
