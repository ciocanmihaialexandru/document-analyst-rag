"""Schema Pydantic pentru extracția structurată din documentul CEC.

Documentul conține MAI MULTE pachete, fiecare cu lista lui de comisioane.
"""

from pydantic import BaseModel, Field


class Comision(BaseModel):
    serviciu: str = Field(
        description="Numele serviciului, ex: 'Retragere numerar de la ATM altă bancă'"
    )
    categorie: str | None = Field(
        default=None,
        description="Categoria, ex: 'Carduri și numerar', 'Plăți'",
    )
    valoare: str = Field(
        description="Comisionul ca text, ex: '5 lei/operațiune', '0 Lei'"
    )


class Pachet(BaseModel):
    """Un pachet de cont cu lista lui de comisioane."""

    nume: str = Field(description="Numele pachetului, ex: 'GRIJA COMPLETA', 'PREMIUM'")
    comisioane: list[Comision] = Field(
        default_factory=list,
        description="Toate comisioanele pachetului",
    )


class DocumentComisioane(BaseModel):
    """Documentul complet: banca + toate pachetele."""

    banca: str = Field(description="Numele băncii, ex: 'CEC Bank S.A.'")
    data: str | None = Field(default=None, description="Data documentului")
    pachete: list[Pachet] = Field(
        default_factory=list,
        description="Toate pachetele din document",
    )