"""ToolWrapper: punct unic de execuție și de expunere a tool-urilor.

  - call(name, args): Lookup -> Validare (Pydantic) -> Execuție -> Return
  - catalog(): generează schema JSON a fiecărui tool, pentru LLM
"""

from tools.registry import TOOL_REGISTRY
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.tools import StructuredTool


class ToolWrapper:

    @staticmethod
    def call(name: str, args: dict) -> str:
        
        # 1. Lookup în registry
        if name not in TOOL_REGISTRY:
            return f"Eroare: tool '{name}' nu există."
        tool = TOOL_REGISTRY[name]

        # 2. Validare — Pydantic verifică tipuri și constrângeri
        try:
            params = tool["params_model"](**args)
        except Exception as e:
            return f"Eroare de validare pentru '{name}': {e}"

        # 3. Execuție + 4. Return (erori descriptive, nu stack traces)
        try:
            return str(tool["func"](params))
        except Exception as e:
            return f"Eroare la execuția '{name}': {e}"

    @staticmethod
    def catalog() -> list[dict]:
        # Un dict per tool: nume, descriere (docstring) și schema parametrilor
        return [
            {
                "name": name,
                "description": tool["description"],
                "input_schema": tool["params_model"].model_json_schema(),
            }
            for name, tool in TOOL_REGISTRY.items()
        ]
    
    @staticmethod
    def to_langchain_tools() -> list["StructuredTool"]:
        try:
            from langchain_core.tools import StructuredTool
        except ImportError:
            raise ImportError(
                "langchain-core nu este instalat. Rulează: pip install langchain-core"
            )

        lc_tools = []
        for name, tool in TOOL_REGISTRY.items():
            if not tool.get("enabled", True):   # registry-ul nostru n-are 'enabled' → default True
                continue

            params_model = tool["params_model"]
            func = tool["func"]

            def make_wrapper(f, pm):
                def wrapper(**kwargs) -> str:
                    params = pm(**kwargs)
                    return str(f(params))
                return wrapper

            lc_tool = StructuredTool.from_function(
                func=make_wrapper(func, params_model),
                name=name,
                description=tool["description"],
                args_schema=params_model,
            )
            lc_tools.append(lc_tool)
        return lc_tools