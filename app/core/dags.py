from pathlib import Path
import json
import os
import logging

logger = logging.getLogger(__name__)

def _cast_value(value, type_str):
    """Cast value to its proper type based on type annotation string"""
    if value is None:
        return None
    
    # Handle string type annotations
    type_str = str(type_str).lower()
    
    # Remove 'typing.' prefix if present
    type_str = type_str.replace('typing.', '')
    
    try:
        if 'int' in type_str:
            return int(value)
        elif 'float' in type_str:
            return float(value)
        elif 'bool' in type_str:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif 'list' in type_str or 'sequence' in type_str:
            if isinstance(value, list):
                return value
            return [value] if value else []
        elif 'dict' in type_str:
            if isinstance(value, dict):
                return value
            return {}
        else:
            # Default to string
            return str(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to cast '{value}' to {type_str}: {e}")
        return value
    
def normalize_dag_config(payload: dict) -> dict:
    """Normalize the payload structure to standard DAG format"""
    dag_config = payload.get('dagConfig', {})
    tasks = payload.get('tasks', [])
    connections = payload.get('connections', [])
    
    return {
        'dag_id': dag_config.get('dag_id', 'unknown_dag'),
        'description': dag_config.get('description', ''),
        'schedule': dag_config.get('schedule', '@daily'),
        'start_date': dag_config.get('start_date', '2025-12-25'),
        'catchup': dag_config.get('catchup', False),
        'tags': dag_config.get('tags', ['airdraw']),
        'max_active_runs': dag_config.get('max_active_runs', 1),
        'default_view': dag_config.get('default_view', 'grid'),
        'tasks': normalize_new_format_tasks(tasks, connections),
    }

def normalize_new_format_tasks(tasks, connections):
    """Convert new format tasks to standard format."""
    normalized_tasks = []
    connection_map = {}
    
    # Build connection map
    for conn in connections:
        from_node = conn.get('from')
        to_node = conn.get('to')
        if from_node and to_node:
            connection_map.setdefault(from_node, []).append(to_node)

    id_to_task_name = {task.get('id'): task.get('taskName', task.get('id')) for task in tasks}
    
    for task in tasks:
        task_id = task.get('taskName', task.get('id'))
        task_type = task.get('type')
        
        normalized_task = {
            'task_id': task_id,
            'library': task.get('providerTypes'),
            'type': task_type,
        }
        
        # Extract operator params
        op_params = task.get('operatorParams', {})
        params_without_defaults = op_params.get('params_without_defaults', {})
        params_with_defaults = op_params.get('params_with_defaults', {})

        all_params = {**params_with_defaults, **params_without_defaults}
        
        for param_name, param_info in all_params.items():
            value = param_info.get('value')
            param_type = param_info.get('type', 'str')
            
            # Only add if value exists
            if value is not None:
                casted_value = _cast_value(value, param_type)
                normalized_task[param_name] = casted_value
        
        
        # Add downstream if this node has connections
        node_id = task.get('id')
        if node_id in connection_map:
            downstream_ids = [
                id_to_task_name[to_node_id]
                for to_node_id in connection_map[node_id]
                if to_node_id in id_to_task_name
            ]
            if downstream_ids:
                normalized_task['downstream'] = downstream_ids
        
        normalized_tasks.append(normalized_task)
    
    return normalized_tasks

def store_dag(dag_data: dict) -> tuple[dict, list]:
    """Store the DAG configuration after normalizing it."""

    AIRDRAW_DAGS_PATH = Path(os.getenv("AIRFLOW_HOME")) / ".airdraw" / "dags"
    logger.info(f"Looking for DAGs in: {AIRDRAW_DAGS_PATH}")

    normalized_config = normalize_dag_config(dag_data)
    logger.info(f"Normalized DAG config: {normalized_config}")
    # Here you would add logic to store the normalized_config, e.g., save to a database or file system.
    with open(AIRDRAW_DAGS_PATH / f"{normalized_config['dag_id']}.json", 'w', encoding='utf-8') as f:
        json.dump(normalized_config, f, indent=4)
    # For this example, we'll just return the normalized config and an empty error list.
    return normalized_config, []