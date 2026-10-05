"""Agent QA cu tools + prompts, în buclă ReAct.

Rulare:
  python agent.py "Cât face 2+2?"
  python agent.py -m claude "Ce dată e azi?"
  python agent.py -m claude "Cât face 4500 + 150 * 0.19? Și ce dată e azi?"
  python agent.py -m claude "Pamantul este plat? cat fac 2+7? cum este vremea in Bucuresti?"
  python agent.py # mod interactiv
"""

import argparse
import json
import httpx
import os

from tools import ToolWrapper
from prompts.registry import get_prompt_registry

class QAAgent:
    
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:4000",
        max_iterations: int = 5,
        rol: str = "asistent QA",
        domeniu: str = "întrebări generale",
        max_cuvinte: int = 150,
    ):
        self.model = model
        self.base_url = base_url
        self.max_iterations = max_iterations

        self._tools_payload = self._build_tools_payload()
        self._system_prompt = get_prompt_registry().render(
            "qa_system",
            rol=rol,
            domeniu=domeniu,
            max_cuvinte=max_cuvinte,
        )

    def _build_tools_payload(self) -> list[dict]:
        """catalog() -> formatul de tools cerut de API-ul OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in ToolWrapper.catalog()
        ]

    def _call_llm(self, messages: list[dict], tools: list[dict]) -> dict:
        """Un apel către LLM prin LiteLLM."""
        try:
            payload = {"model": self.model, "messages": messages, "tools": tools}
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions", json=payload, timeout=120
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"Nu am putut contacta LLM-ul la {self.base_url}. "
                f"E pornit Docker (docker-compose up -d)? Detaliu: {e}"
            )

    def _execute_tool_calls(self, tool_calls: list[dict], messages: list[dict]) -> None:
        """Act + Observe: execută tool-urile cerute și adaugă rezultatele în messages."""
        for tc in tool_calls:
            name = tc["function"]["name"]
            raw_args = tc["function"]["arguments"]
            try:
                args = json.loads(raw_args or "{}")
            except json.JSONDecodeError:
                rezultat = f"Eroare: argumente JSON invalide pentru '{name}': {raw_args}"
            else:
                rezultat = ToolWrapper.call(name, args)

            print(f"  [tool] {name}({raw_args}) -> {rezultat}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": rezultat,
            })

    def run(self, intrebare: str) -> str:
        """Rulează bucla ReAct pentru o întrebare și întoarce răspunsul final."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": intrebare},
        ]

        for _ in range(self.max_iterations):
            mesaj = self._call_llm(messages, self._tools_payload)
            messages.append(mesaj)

            tool_calls = mesaj.get("tool_calls")
            if not tool_calls:
                return mesaj.get("content") or ""

            self._execute_tool_calls(tool_calls, messages)

        # Fallback: forțează un răspuns final fără tool-uri
        messages.append({
            "role": "user",
            "content": "Dă acum răspunsul final pentru întrebarea inițială, "
                       "folosind rezultatele de mai sus. Nu mai chema tool-uri.",
        })
        mesaj = self._call_llm(messages, tools=[])
        return mesaj.get("content") or "Nu am putut genera un răspuns final."

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent QA cu tools + prompts (ReAct).")
    parser.add_argument("question", nargs="?", help="Întrebarea. Lipsă -> mod interactiv.")
    parser.add_argument(
        "-m", "--model",
        default=os.environ.get("AGENT_MODEL", "qwen"),
        help="Modelul LLM (ex: qwen, mistral, gemini, claude).",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(os.environ.get("AGENT_MAX_ITER", "5")),
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    intrebare = args.question or input("Întrebarea ta: ").strip()
    if not intrebare:
        print("Nu ai dat nicio întrebare.")
        return

    agent = QAAgent(
        model=args.model,
        base_url=os.environ.get("LITELLM_BASE_URL", "http://localhost:4000"),
        max_iterations=args.max_iterations,
    )

    print(f"\nMODEL: {agent.model}")
    print(f"USER: {intrebare}\n")
    try:
        raspuns = agent.run(intrebare)
        print(f"\nAGENT: {raspuns}")
    except RuntimeError as e:
        print(f"\n[EROARE] {e}")

if __name__ == "__main__":
    main()
