from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.config.composition_root import CompositionRoot

# 1. Definimos o prefixo e a tag para o Swagger
router = APIRouter(prefix="/qualidade", tags=["Qualidade"])

# 2. Modelo de dados para a requisição
class AnaliseRequest(BaseModel):
    codigo: str

# 3. Função de ajuda para obter o serviço via CompositionRoot
def get_qualidade_service():
    return CompositionRoot().get_qualidade_service()

# 4. O Endpoint que atende à US IA-04
@router.post("/analisar")
async def analisar_codigo(
    request: AnaliseRequest,
    service = Depends(get_qualidade_service)
):
    """
    Endpoint para análise de qualidade:
    - Mapeia acoplamento (imports).
    - Identifica possíveis ciclos.
    - Sugere ações por severidade.
    """
    try:
        # Chama o serviço que ligamos na Composition Root
        diagnostico = service.obter_diagnostico_completo(request.codigo)
        return diagnostico
    except Exception as e:
        # Se algo falhar na análise técnica, retornamos erro 400
        raise HTTPException(status_code=400, detail=f"Erro na análise de qualidade: {str(e)}")