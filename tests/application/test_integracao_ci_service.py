# Testes do IntegracaoCIServiceImpl (US IA-11) — usa fakes pra GitHub e notificador.

import pytest

from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.git.adaptador_github import AdaptadorGitHubFake
from app.adapters.driven.git.notificador_pr_github import NotificadorPRFake
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.adapters.driven.persistence.repositorio_webhooks_sqlite import (
    RepositorioWebhooksSQLite,
)
from app.application.services.comparacao_diagrama_service_impl import (
    ComparacaoDiagramaServiceImpl,
)
from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.application.services.integracao_ci_service_impl import (
    IntegracaoCIServiceImpl,
)
from app.domain.entidades.evento_ci import (
    EventoCI,
    TipoEventoGitHub,
    construir_evento_de_payload,
)


@pytest.fixture
def cenario(tmp_path):
    repo_webhooks = RepositorioWebhooksSQLite(str(tmp_path / "wh.db"))
    git = AdaptadorGitHubFake()
    notificador = NotificadorPRFake()
    estrutura = EstruturaServiceImpl(
        parser_codigo=AdaptadorParserPython(),
        provedor_llm=AdaptadorLLMFake(),
    )
    comparacao = ComparacaoDiagramaServiceImpl(estrutura_service=estrutura)
    service = IntegracaoCIServiceImpl(
        repositorio_webhooks=repo_webhooks,
        repositorio_git=git,
        notificador=notificador,
        comparacao=comparacao,
    )
    yield service, repo_webhooks, git, notificador
    repo_webhooks.fechar()


def _evento_pr_aberto(repo="o/r", pr=1, base="aaaaaaa", head="bbbbbbb") -> EventoCI:
    return construir_evento_de_payload("pull_request", {
        "action": "opened",
        "pull_request": {"number": pr, "head": {"sha": head}, "base": {"sha": base}},
        "repository": {"full_name": repo},
    })


def test_registrar_evento_persiste(cenario):
    service, repo_webhooks, _, _ = cenario
    evento = _evento_pr_aberto()
    service.registrar_evento(evento)
    assert repo_webhooks.obter(evento.id) is not None


def test_processar_evento_ignorado_marca_sucesso(cenario):
    service, _, _, notificador = cenario
    evento = construir_evento_de_payload("pull_request", {
        "action": "closed",
        "pull_request": {"number": 1, "head": {"sha": "a"}, "base": {"sha": "b"}},
        "repository": {"full_name": "o/r"},
    })
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is True
    assert "ignorado" in resultado.resultado
    assert notificador.chamadas == []  # nada foi postado


def test_processar_evento_sem_arquivos_python_posta_mensagem_curta(cenario):
    service, _, git, notificador = cenario
    evento = _evento_pr_aberto()
    git.configurar_arquivos_pr(evento.repositorio, evento.pr_numero, [])
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is True
    assert len(notificador.chamadas) == 1
    assert "Nenhum arquivo Python" in notificador.chamadas[0]["mensagem"]


def test_processar_pr_com_arquivo_modificado_posta_diff(cenario):
    service, _, git, notificador = cenario
    evento = _evento_pr_aberto()
    git.configurar_arquivos_pr(evento.repositorio, evento.pr_numero, ["app/x.py"])
    git.configurar_conteudo(evento.repositorio, evento.pr_base_sha, "app/x.py",
                            "class A:\n    def foo(self): pass\n")
    git.configurar_conteudo(evento.repositorio, evento.pr_head_sha, "app/x.py",
                            "class A:\n    def foo(self): pass\n    def bar(self): pass\nclass B:\n    pass\n")
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)

    assert resultado.sucesso is True
    assert len(notificador.chamadas) == 1
    msg = notificador.chamadas[0]["mensagem"]
    assert "Analise Arquitetural Automatica" in msg
    assert "Componentes adicionados: **1**" in msg
    assert "Componentes alterados: **1**" in msg
    assert "Nao bloqueia CI" in msg


def test_processar_arquivo_novo_no_head(cenario):
    service, _, git, notificador = cenario
    evento = _evento_pr_aberto()
    git.configurar_arquivos_pr(evento.repositorio, evento.pr_numero, ["app/novo.py"])
    git.configurar_conteudo(evento.repositorio, evento.pr_base_sha, "app/novo.py", None)
    git.configurar_conteudo(evento.repositorio, evento.pr_head_sha, "app/novo.py",
                            "class Novo:\n    pass\n")
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is True
    assert "Componentes adicionados: **1**" in notificador.chamadas[0]["mensagem"]


def test_falha_ao_listar_arquivos_marca_insucesso_e_nao_quebra(cenario):
    service, _, git, notificador = cenario
    evento = _evento_pr_aberto()
    git.fazer_falhar_listagem(RuntimeError("boom"))
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is False
    assert "erro ao listar arquivos" in resultado.resultado
    assert notificador.chamadas == []


def test_falha_no_notificador_marca_insucesso_mas_processa(cenario):
    service, _, git, notificador = cenario
    evento = _evento_pr_aberto()
    git.configurar_arquivos_pr(evento.repositorio, evento.pr_numero, ["app/x.py"])
    git.configurar_conteudo(evento.repositorio, evento.pr_base_sha, "app/x.py", "class A:\n    pass\n")
    git.configurar_conteudo(evento.repositorio, evento.pr_head_sha, "app/x.py", "class B:\n    pass\n")
    notificador.fazer_falhar()
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is False
    assert "falha ao postar comentario" in resultado.resultado


def test_evento_inexistente_devolve_outro_sem_quebrar(cenario):
    service, _, _, _ = cenario
    resultado = service.processar_evento("id-que-nao-existe")
    # nao quebra, devolve um EventoCI placeholder com tipo OUTRO
    assert resultado.tipo == TipoEventoGitHub.OUTRO


def test_payload_sem_pr_marca_insucesso(cenario):
    service, _, _, _ = cenario
    # Forcamos um evento "tipo PR mas sem dados" (pr_numero etc None)
    evento = EventoCI(
        tipo=TipoEventoGitHub.PULL_REQUEST_OPENED,
        repositorio="o/r",
        pr_numero=None,
        pr_head_sha=None,
        pr_base_sha=None,
    )
    service.registrar_evento(evento)
    resultado = service.processar_evento(evento.id)
    assert resultado.sucesso is False


def test_listar_eventos_devolve_persistidos(cenario):
    service, _, _, _ = cenario
    e1 = _evento_pr_aberto(pr=1)
    e2 = _evento_pr_aberto(pr=2)
    service.registrar_evento(e1)
    service.registrar_evento(e2)
    eventos = service.listar_eventos(repositorio="o/r")
    assert {e.pr_numero for e in eventos} == {1, 2}
