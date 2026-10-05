"""ToolWrapper: punct unic de execuție și de expunere a tool-urilor.

  - call(name, args): Lookup -> Validare (Pydantic) -> Execuție -> Return
  - catalog(): generează schema JSON a fiecărui tool, pentru LLM
"""

from tools.registry import TOOL_REGISTRY

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