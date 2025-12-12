import os
import ast
import pkgutil
import importlib.util
import logging

logger = logging.getLogger(__name__)

_cached_operators = None
_cached_errors = None

def _extract_operators_from_file(file_path: str) -> list[str]:
    """Extract operator class names from Python file using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        operators = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Operator' in node.name and not node.name.startswith('Base'):
                    operators.append(node.name)
        return operators
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {str(e)}")
        return []

def load_operators() -> tuple[dict, list]:
    """Load all operators without importing"""
    global _cached_operators, _cached_errors
    operators_dict = {}
    errors = []
    
    try:
        import airflow.providers
        providers_path = airflow.providers.__path__
    except ImportError:
        logger.error("No providers installed")
        return {}, [{"error": "airflow.providers not installed"}]
    
    try:
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=providers_path,
            prefix='airflow.providers.',
        ):
            if 'operators' in modname and not ispkg:
                try:
                    spec = importlib.util.find_spec(modname)
                    if spec and spec.origin:
                        if not os.path.exists(spec.origin):
                            errors.append({"module": modname, "error": "File not found"})
                            continue
                        
                        operators = _extract_operators_from_file(spec.origin)
                        if operators:
                            operators_dict[modname] = operators
                        else:
                            errors.append({"module": modname, "error": "No operators defined"})
                    else:
                        errors.append({"module": modname, "error": "Module spec not found"})
                except Exception as e:
                    logger.error(f"Failed to process {modname}: {str(e)}")
                    errors.append({"module": modname, "error": str(e)})
    except Exception as e:
        logger.error(f"Failed to walk packages: {str(e)}")
    
    _cached_operators = operators_dict
    _cached_errors = errors
    return operators_dict, errors

def get_cached_operators() -> tuple[dict, list]:
    """Get cached operators"""
    return _cached_operators or {}, _cached_errors or []