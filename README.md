# Módulo 5 — IA Análise de Código

Microsserviço de engenharia reversa e análise de qualidade de código Python.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # depois edite .env e cole sua chave
python -m uvicorn main:app --port 8001 --reload
```

Sem `GEMINI_API_KEY` configurada o serviço sobe em **modo fake** (LLM mockado),
útil pra dev/demo offline. As relações semânticas ficam vazias e um `warning`
aparece na resposta.

## Endpoints

### IA-01 — Gerar diagrama de arquitetura

```bash
curl -X POST http://localhost:8001/estrutura/diagrama \
  -H "Content-Type: application/json" \
  -d '{"codigo":"class A:\n    def x(self): pass\n"}'
```

Resposta:

```json
{
  "componentes": [{"nome": "A", "tipo": "classe", "metodos": ["x"], "atributos": [], "responsabilidade": "..."}],
  "relacoes": [],
  "mermaid": "classDiagram\n    class A {\n        +x()\n    }\n",
  "warnings": []
}
```

### IA-02 — Extrair OpenAPI

```bash
curl -X POST http://localhost:8001/openapi/extrair \
  -H "Content-Type: application/json" \
  -d '{"codigo":"@app.get(\"/x\")\ndef rota(): pass"}'
```

## Testes

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
```

Os testes não exigem `GEMINI_API_KEY` — usam `AdaptadorLLMFake`.

## Arquitetura

Hexagonal (Ports & Adapters):

- `app/domain/` — entidades de negócio
- `app/application/ports/` — interfaces (driving e driven)
- `app/application/services/` — implementação dos casos de uso
- `app/adapters/driven/` — integração com infra (AST, LLM, persistência)
- `app/adapters/driving/http/` — rotas FastAPI
- `app/config/composition_root.py` — injeção de dependências
