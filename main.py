import uvicorn
from fastapi import FastAPI

from app.adapters.driving.http.openapi_routes import router as openapi_router
from app.adapters.driving.http.estrutura_routes import router as estrutura_router

app = FastAPI(
    title="Módulo 5 - IA Análise de Código",
    description="Serviço de Engenharia Reversa e Análise de Qualidade",
    version="1.0.0",
)

app.include_router(openapi_router)
app.include_router(estrutura_router)


@app.get("/health", tags=["Saúde"])
async def health_check():
    return {"status": "healthy", "service": "ia-analise-codigo"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
