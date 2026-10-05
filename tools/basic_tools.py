
from tools.params_models import CalculatorParams, DateTimeParams, WeatherParams, WebSearchParams
from tools.registry import register_tool
from datetime import datetime
from db.database import transaction
from rag.service import RAGService
from .params_models import SearchDocumentsParams

@register_tool
def calculator(params: CalculatorParams) -> str:
    """Evaluează o expresie matematică (adunare, scădere, înmulțire,
    împărțire, putere). Folosește pentru calcule precise, nu estima. """
    
    result = eval(params.expression)
    return str(result)

@register_tool
def get_datetime(params: DateTimeParams) -> str:
    """Întoarce data și ora curentă a sistemului, în formatul YYYY-MM-DD HH:MM:SS."""
    
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@register_tool
def get_weather(params: WeatherParams) -> str:
    """Întoarce prognoza meteo pentru un oraș și o dată specifică (sau azi, dacă nu se specifică)."""
    
    # Implementare fictivă; în realitate, ar trebui să folosească un API meteo.
    if params.date:
        return f"Prognoza meteo pentru {params.location} la data {params.date}: Soare, 25°C."
    else:
        return f"Prognoza meteo pentru {params.location} azi: Noros, 20°C."

@register_tool
def web_search(params: WebSearchParams) -> str:
    """Caută pe web termenii specificați și întoarce primele rezultate (maxim 20)."""
    
    # Implementare fictivă; în realitate, ar trebui să folosească un motor de căutare.
    results = [f"Rezultat {i+1} pentru '{params.query}'" for i in range(params.max_results)]
    return "\n".join(results)

@register_tool
def search_documents(params: SearchDocumentsParams) -> str:
    """Caută informații în documentul CEC cu comisioane bancare. Folosește
    pentru întrebări despre comisioane, servicii sau pachete. Dacă întrebarea
    e despre un pachet anume, pune package cu numele lui exact."""
    with transaction() as db:
        rag = RAGService(db)
        results = rag.search(params.query, top_k=5, package=params.package)
        if not results:
            return "Nu am găsit informații relevante în documente."
        # formatăm AICI, cât sesiunea e încă deschisă
        return "\n\n".join(
            f"[{c.package} | {s:.2f}] {c.content}" for c, s in results
        )
    