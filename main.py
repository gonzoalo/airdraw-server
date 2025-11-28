from typing import Union

from fastapi import FastAPI
import os
import pkgutil
import importlib
import airflow.providers

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/listFiles")
def list_files():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    return {"files_final": files}

@app.get("/path")
def show_path():
    return {"path": airflow.providers.__path__}

@app.get("/operators")
def list_operators():
    operators = {}
    try:
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=airflow.providers.__path__,
            prefix='airflow.providers.',
        ):
            if 'operators' in modname and not ispkg:
                try:
                    module = importlib.import_module(modname)
                    operator_group = {modname: []}
                    # print(f"\n{modname}:")
                    for item in dir(module):
                        if 'Operator' in item and not item.startswith('_'):
                            operator_group[modname].append(item)
                    operators.update(operator_group)
                except Exception as e:
                    pass
        return operators
    except ImportError:
        print("No providers installed")