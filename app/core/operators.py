from http.client import HTTPException
import os
import ast
import pkgutil
import importlib.util
import logging
import inspect

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
    
def _extract_docstring_from_ast(file_path: str, operator_name: str) -> str:
    """Extract docstring from operator class using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == operator_name:
                return ast.get_docstring(node) or ""
        return ""
    except Exception as e:
        logger.error(f"Failed to extract docstring for {operator_name}: {str(e)}")
        return ""
    
def _extract_params_from_ast(file_path: str, operator_name: str) -> dict:
    """Extract operator parameters using AST without importing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        params_without_defaults = {}
        params_with_defaults = {}
        
        # Find the class definition
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == operator_name:
                # Find __init__ method
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        # Extract parameters
                        for arg in item.args.args:
                            if arg.arg in ('self', 'args', 'kwargs'):
                                continue
                            
                            param_type = 'Any'
                            # Try to extract type annotation
                            if arg.annotation:
                                param_type = ast.unparse(arg.annotation)
                            
                            params_without_defaults[arg.arg] = {
                                'type': param_type,
                                'required': True
                            }
                        
                        # Extract defaults
                        num_defaults = len(item.args.defaults)
                        if num_defaults > 0:
                            # Arguments with defaults
                            args_with_defaults = item.args.args[-num_defaults:]
                            for i, arg in enumerate(args_with_defaults):
                                if arg.arg in ('self', 'args', 'kwargs'):
                                    continue
                                
                                param_type = 'Any'
                                if arg.annotation:
                                    param_type = ast.unparse(arg.annotation)
                                
                                default_value = ast.unparse(item.args.defaults[i])
                                
                                # Move from required to optional
                                if arg.arg in params_without_defaults:
                                    del params_without_defaults[arg.arg]
                                
                                params_with_defaults[arg.arg] = {
                                    'type': param_type,
                                    'default': default_value,
                                    'required': False
                                }
                        
                        break
                break
        
        return {
            'params_without_defaults': params_without_defaults,
            'params_with_defaults': params_with_defaults
        }
    except Exception as e:
        logger.error(f"Failed to extract params from AST for {operator_name}: {str(e)}")
        return {'params_without_defaults': {}, 'params_with_defaults': {}}

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

def get_module_path(module_name: str) -> str:
    """Get the file path of a module from its import name"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return spec.origin
        return None
    except (ImportError, AttributeError, ValueError) as e:
        logger.error(f"Could not find module path for {module_name}: {str(e)}")
        return None

def get_params_v1(module_name: str, operator_name: str) -> dict:
    """Get details of a specific operator"""
    try:
        # Get the file path without importing
        module_path = get_module_path(module_name)
        if not module_path or not os.path.exists(module_path):
            logger.error(f"Module file not found: {module_name}")
            return {}
        
        logger.info(f"Extracting params for {operator_name} from {module_name} at {module_path}")
        # Extract params using AST
        params = _extract_params_from_ast(module_path, operator_name)
        return {
            'class_name': operator_name,
            'module_path': module_name,
            **params
        }
    except Exception as e:
        logger.error(f"Failed to get params for {operator_name}: {str(e)}")
        return {}


def get_params(module_name: str, operator_name: str) -> dict:
    """Get details of a specific operator"""
    
    try:
        module = importlib.import_module(module_name)
        logger.info("Imported module: " + module_name)
        operator_class = getattr(module, operator_name)
        
        # Get signature from the class itself (handles inheritance)
        sig = inspect.signature(operator_class)
        
        logger.info("Extracted signature for: " + operator_name)
        params_with_defaults = {}
        params_without_defaults = {}
        
        for name, param in sig.parameters.items():
            if name in ('self', 'args', 'kwargs'):
                continue
            
            # Skip **kwargs and *args
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            
            if param.default == inspect.Parameter.empty:
                params_without_defaults[name] = {
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'required': True
                }
            else:
                params_with_defaults[name] = {
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': str(param.default) if param.default is not None else None,
                    'required': False
                }
        
        logger.info("Finished extracting params for: " + operator_name)
        return {
            'class_name': operator_name,
            'module_path': module_name,
            'params_without_defaults': params_without_defaults,
            'params_with_defaults': params_with_defaults
        }
    
    except (ImportError, AttributeError) as e:
        logger.error(f"Operator not found: {str(e)}")
        return {}
