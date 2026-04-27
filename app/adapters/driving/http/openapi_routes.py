from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.config.composition_root import CompositionRoot

# Criamos o roteador do FastAPI
router = APIRouter(prefix="/openapi", tags=["OpenAPI"])

# Modelo de dados para receber o código via JSON
class CodigoFonteRequest(BaseModel):
    codigo: str

# Função auxiliar para obter o serviço a partir da Composition Root
def get_openapi_service():
    root = CompositionRoot()
    return root.get_openapi_service()

@router.post("/extrair")
async def extrair_openapi(
    request: CodigoFonteRequest,
    service = Depends(get_openapi_service)
):
    """
    Endpoint que recebe código Python e retorna a especificação OAS 3.0.
    Atende à US IA-02.
    """
    try:
        # Chama o serviço (que por sua vez usa o adaptador AST que criamos)
        especificacao_json = service.gerar_especificacao_do_codigo(request.codigo)
        return especificacao_json
    except Exception as e:
        # Se algo falhar na análise, retornamos erro 400 (Bad Request)
        raise HTTPException(status_code=400, detail=str(e))