"""Registry-ul de tool-uri + decoratorul de înregistrare automată.

- TOOL_REGISTRY: catalogul global (nume -> info despre tool)
- @register_tool: pus deasupra unei funcții, o validează și o
  înregistrează automat, la import.
"""

import inspect
from pydantic import BaseModel

TOOL_REGISTRY: dict[str, dict] = {}

def register_tool(func):
    """Validează funcția și o înregistrează în TOOL_REGISTRY.

    Convenții impuse:
      1. funcția are EXACT un parametru, de tip Pydantic BaseModel;
      2. funcția are docstring (devine descrierea trimisă la LLM).
    """

TOOL_REGISTRY: dict[str, dict] = {}

def register_tool(func):
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    if len(params) != 1:
        raise TypeError(f"{func.__name__} trebuie să aibă EXACT un parametru, de tip Pydantic BaseModel.")

    annotation = params[0].annotation
    if annotation is inspect.Parameter.empty or not issubclass(annotation, BaseModel):
        raise TypeError(f"Parametrul funcției {func.__name__} trebuie să fie de tip Pydantic BaseModel.")

    docstring = (func.__doc__ or "").strip()
    if len(docstring) < 15:
        raise ValueError(
            f"{func.__name__}: docstring obligatoriu, minim 15 caractere "
            f"(are {len(docstring)}) — devine descrierea pentru LLM"
        )
    
    TOOL_REGISTRY[func.__name__] = {
        "func": func,                  # funcția în sine
        "params_model": annotation,    # clasa Pydantic cu parametrii
        "description": docstring,      # ce citește LLM-ul
    }
    return func

    
    

