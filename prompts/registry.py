"""PromptRegistry: încarcă fișierele .yaml, le validează și le
randează cu Jinja2.

  - get(name)          -> template-ul brut (dict din YAML)
  - render(name, **v)  -> promptul final, cu variabilele aplicate
  - list_templates()   -> ce prompturi sunt disponibile
  - reload()           -> reîncarcă de pe disk (util în development)
"""

from functools import lru_cache
from pathlib import Path

import yaml
from jinja2 import Template


class PromptRegistry:
    def __init__(self, folder: str):
        self._folder = folder
        self._templates = self._load(folder)

    def _load(self, folder: str) -> dict[str, dict]:
        templates: dict[str, dict] = {}
        for path in Path(folder).rglob("*.yaml"):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            # validare minimă: câmpurile obligatorii
            for camp in ("name", "version", "prompt"):
                if camp not in data:
                    raise ValueError(f"{path.name}: lipsește câmpul '{camp}'")
            templates[data["name"]] = data
        return templates

    def get(self, name: str) -> dict:
        if name not in self._templates:
            raise KeyError(f"Promptul '{name}' nu există")
        return self._templates[name]

    def render(self, name: str, **variabile) -> str:
        template = self.get(name)
        return Template(template["prompt"]).render(**variabile)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())

    def reload(self) -> None:
        self._templates = self._load(self._folder)


# Acces global (Singleton) - o singură încărcare, reutilizată peste tot
@lru_cache(maxsize=1)
def get_prompt_registry() -> PromptRegistry:
    return PromptRegistry(folder="prompts")