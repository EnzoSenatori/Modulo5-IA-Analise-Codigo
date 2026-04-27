import uvicorn
from fastapi import FastAPI
from app.adapters.driving.http.openapi_routes import router as openapi_router

# 1. Instanciamos o FastAPI
app = FastAPI(
    title="Módulo 5 - IA Analise de Codigo",
    description="Serviço de Engenharia Reversa e Análise de Qualidade",
    version="1.0.0"
)

# 2. Incluímos as rotas que criamos no Passo 8
app.include_router(openapi_router)

# 3. Rota de saúde (Healthcheck) para verificar se o serviço está online
@app.get("/health", tags=["Saúde"])
async def health_check():
    return {"status": "healthy", "service": "ia-analise-codigo"}

# 4. Bloco para rodar localmente via PyCharm/Terminal
if __name__ == "__main__":
    # Rodando na porta 8001 para não conflitar com outros microsserviços
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)