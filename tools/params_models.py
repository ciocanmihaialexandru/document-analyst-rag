"""Modele Pydantic pentru paramterii fiecarui tool.

Un model = un singur loc care defineste tipuri, validare si valori implicite si descrieri. Descrierile ajung la LLM.
"""

from pydantic import BaseModel, Field
from typing import Optional

class CalculatorParams(BaseModel):
    expression: str = Field(
        ...,
        description="Expresia matematica care trebuie evaluata, de exemplu:'4500 + 150 * 0.19'",
        min_length=1,
    )

class DateTimeParams(BaseModel):
    # Fără parametri: tool-ul întoarce data/ora curentă a sistemului.
    pass

class WeatherParams(BaseModel):
    location: str = Field(..., description="Orașul, ex: 'București'", min_length=1)
    date: str | None = Field(
        default=None,
        description="Data YYYY-MM-DD; lasă gol pentru vremea de azi",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )

class WebSearchParams(BaseModel):
    query: str = Field(
        description="Termenii de căutat pe web",
        min_length=2,
    )
    max_results: int = Field(
        default=5,
        description="Numărul maxim de rezultate returnate",
        ge=1,
        le=20,
    )

class SearchDocumentsParams(BaseModel):
    query: str = Field(
        description="Întrebarea de căutat în documentul cu comisioane bancare"
    )
    package: Optional[str] = Field(
        default=None,
        description="Numele EXACT al pachetului dacă întrebarea e despre unul "
                    "(ex: 'PREMIUM', 'GRIJA COMPLETA', 'STUDENT FREE')",
    )