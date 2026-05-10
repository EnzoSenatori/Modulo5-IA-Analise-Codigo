# Testes do CasoDeUsoServiceImpl (US IA-03).

import pytest

from app.application.services.caso_de_uso_service_impl import CasoDeUsoServiceImpl
from app.domain.excecoes import (
    FormatoNaoSuportadoError,
    PDFInvalidoError,
    RequisitosVaziosError,
)


@pytest.fixture
def service():
    return CasoDeUsoServiceImpl()


# ------------ Parser de user stories ------------

def test_extrai_user_story_simples(service):
    texto = "Como Cliente, eu quero realizar pedido para receber em casa."
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1
    caso = d.casos_uso[0]
    assert caso.atores == ("Cliente",)
    assert "realizar pedido" in caso.descricao.lower()
    assert "receber em casa" in caso.beneficio.lower()


def test_aceita_artigo_um_uma_o_a(service):
    texto = """
Como um Cliente, eu quero comprar produtos.
Como uma Atendente, quero consultar pedidos.
Como o Gerente, quero ver relatorios.
"""
    d = service.extrair_de_texto(texto)
    nomes = {a.nome for a in d.atores}
    assert "Cliente" in nomes and "Atendente" in nomes and "Gerente" in nomes


def test_eu_eh_opcional(service):
    """'Como X, quero Y' (sem 'eu') tambem deve casar."""
    texto = "Como Tech Lead, quero ver metricas para tomar decisoes."
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1


def test_aceita_bullet_inicial(service):
    texto = "- Como Cliente, eu quero pagar com pix."
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1


def test_aceita_numeracao(service):
    texto = "1. Como Cliente, eu quero ver historico."
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1


def test_aceita_acento_no_ator(service):
    texto = "Como Atendente Sênior, eu quero fechar caixa."
    d = service.extrair_de_texto(texto)
    assert d.casos_uso[0].atores[0] == "Atendente Sênior"


def test_acoes_iguais_de_atores_diferentes_consolidam(service):
    """Mesma acao, atores diferentes -> 1 caso de uso com varios atores."""
    texto = """
Como Cliente, eu quero consultar pedido.
Como Atendente, eu quero consultar pedido.
"""
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1
    assert d.casos_uso[0].atores == ("Atendente", "Cliente")


def test_atores_consolidados_e_ordenados(service):
    texto = """
Como Cliente, eu quero ver catalogo.
Como Atendente, eu quero atualizar catalogo.
Como Cliente, eu quero comprar.
"""
    d = service.extrair_de_texto(texto)
    assert [a.nome for a in d.atores] == ["Atendente", "Cliente"]


def test_acao_sem_beneficio(service):
    texto = "Como Cliente, eu quero apagar minha conta."
    d = service.extrair_de_texto(texto)
    assert d.casos_uso[0].beneficio == ""


def test_linhas_sem_user_story_sao_ignoradas(service):
    texto = """
# Requisitos do projeto

Esta secao descreve...

Como Cliente, eu quero pagar com cartao.

Outras notas aqui.
"""
    d = service.extrair_de_texto(texto)
    assert d.total_casos == 1


# ------------ Ambiguidades ------------

def test_detecta_etc(service):
    texto = "O sistema deve suportar Visa, Mastercard, etc."
    d = service.extrair_de_texto(texto)
    assert any(a.palavra == "etc." or a.palavra == "etc" for a in d.ambiguidades)


def test_detecta_palavras_vagas(service):
    texto = """
A resposta deve ser rapida.
O sistema deveria notificar o usuario.
Talvez precisemos de cache.
"""
    d = service.extrair_de_texto(texto)
    palavras_detectadas = {a.palavra for a in d.ambiguidades}
    assert "rapida" in palavras_detectadas
    assert "deveria" in palavras_detectadas
    assert "talvez" in palavras_detectadas


def test_detecta_reticencias(service):
    texto = "O sistema deve permitir login, logout, ..."
    d = service.extrair_de_texto(texto)
    assert any(a.palavra == "..." for a in d.ambiguidades)


def test_palavras_normais_nao_alertam(service):
    texto = "Como Cliente, eu quero realizar pedido para receber em casa."
    d = service.extrair_de_texto(texto)
    assert d.ambiguidades == []


# ------------ Mermaid ------------

def test_mermaid_tem_atores_e_casos(service):
    texto = """
Como Cliente, eu quero comprar.
Como Atendente, eu quero atender.
"""
    d = service.extrair_de_texto(texto)
    assert "flowchart LR" in d.mermaid
    assert "Cliente" in d.mermaid
    assert "Atendente" in d.mermaid
    assert "comprar" in d.mermaid


def test_mermaid_inclui_estilos(service):
    texto = "Como Cliente, eu quero comprar."
    d = service.extrair_de_texto(texto)
    assert "classDef ator" in d.mermaid
    assert "classDef uc" in d.mermaid


def test_mermaid_vazio_quando_sem_user_story(service):
    texto = "Apenas notas, sem nenhum 'Como X eu quero Y'."
    d = service.extrair_de_texto(texto)
    assert "vazio" in d.mermaid.lower() or "Sem casos de uso" in d.mermaid


def test_aviso_quando_sem_user_story(service):
    texto = "Apenas texto puro sem stories."
    d = service.extrair_de_texto(texto)
    assert any("Nenhuma user story" in a for a in d.avisos)


# ------------ Determinismo ------------

def test_mesma_entrada_mesma_saida(service):
    texto = """
Como Cliente, eu quero comprar.
Como Cliente, eu quero ver historico, etc.
Como Atendente, eu quero atualizar catalogo para manter atualizado.
"""
    a = service.extrair_de_texto(texto).to_dict()
    b = service.extrair_de_texto(texto).to_dict()
    c = service.extrair_de_texto(texto).to_dict()
    assert a == b == c


# ------------ Validacao ------------

def test_texto_vazio_400(service):
    with pytest.raises(RequisitosVaziosError):
        service.extrair_de_texto("")
    with pytest.raises(RequisitosVaziosError):
        service.extrair_de_texto("   \n\n")


def test_formato_invalido_400(service):
    with pytest.raises(FormatoNaoSuportadoError):
        service.extrair_de_texto("texto", formato="docx")


def test_pdf_vazio_falha(service):
    with pytest.raises(PDFInvalidoError):
        service.extrair_de_pdf(b"")


def test_pdf_invalido_falha(service):
    with pytest.raises(PDFInvalidoError):
        service.extrair_de_pdf(b"isso nao eh um pdf de verdade")


def test_pdf_real_processa(service, tmp_path):
    """Gera um PDF minusculo via reportlab... mas nao temos no IA repo.
    Vou usar um truque: escrever um PDF minimal valido e testar."""
    # PDF de uma pagina com texto "Como Cliente, eu quero comprar."
    # Construir manualmente eh complexo — vou usar pypdf pra gerar um PDF teste
    from pypdf import PdfWriter
    writer = PdfWriter()
    # PdfWriter nao gera texto facil; melhor abordagem eh testar o caminho
    # de erro com bytes invalidos (ja feito). Pulamos round-trip de PDF real
    # por ausencia de reportlab no IA-Analise.
    pytest.skip("Round-trip de PDF real exige reportlab — fora do escopo deste repo.")
