# Implementacao do CasoDeUsoService (US IA-03).
# Parser deterministico: regex para user stories + lista de palavras vagas para ambiguidades.

import io
import re
from typing import List, Tuple

from app.application.ports.driving.caso_de_uso_service import CasoDeUsoService
from app.domain.entidades.caso_de_uso import (
    Ambiguidade,
    Ator,
    CasoDeUso,
    DiagramaCasoDeUso,
)
from app.domain.excecoes import (
    FormatoNaoSuportadoError,
    PDFInvalidoError,
    RequisitosVaziosError,
)


# Captura: "Como [um/uma/o/a]? <ator>, [eu]? quero <acao> [para <beneficio>]?"
_REGEX_USER_STORY = re.compile(
    r"""^[\s\-\*\d\.\)]*               # bullet/numero opcional no inicio
        Como\s+(?:um\s+|uma\s+|o\s+|a\s+|os\s+|as\s+)?
        (?P<ator>[A-Za-zÀ-ÿ][\w\sÀ-ÿ\-]*?)
        \s*,\s*
        (?:eu\s+)?quero\s+
        (?P<acao>.+?)
        (?:\s*,\s*para\s+(?P<beneficio>.+?))?
        \s*[.;]?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


_PALAVRAS_VAGAS = {
    "etc": "uso de 'etc' deixa o escopo aberto",
    "etc.": "uso de 'etc' deixa o escopo aberto",
    "diversos": "termo vago — quantos exatamente?",
    "varios": "termo vago — quantos exatamente?",
    "varias": "termo vago — quantos exatamente?",
    "alguns": "termo vago — quantos exatamente?",
    "algumas": "termo vago — quantos exatamente?",
    "muitos": "termo vago — quantificar",
    "muitas": "termo vago — quantificar",
    "talvez": "incerteza no requisito",
    "possivelmente": "incerteza no requisito",
    "provavelmente": "incerteza no requisito",
    "geralmente": "comportamento condicional vago",
    "as vezes": "comportamento condicional vago",
    "rapido": "metrica subjetiva — definir tempo",
    "rapida": "metrica subjetiva — definir tempo",
    "lento": "metrica subjetiva — definir tempo",
    "facil": "metrica subjetiva — definir criterio",
    "deveria": "modal subjuntivo — preferir 'deve' (obrigatorio) ou 'pode' (opcional)",
}

_REGEX_RETICENCIAS = re.compile(r"\.{3,}|…")


class CasoDeUsoServiceImpl(CasoDeUsoService):

    def extrair_de_texto(self, texto: str, formato: str = "markdown") -> DiagramaCasoDeUso:
        if not texto or not texto.strip():
            raise RequisitosVaziosError("texto de requisitos esta vazio.")
        formato_n = (formato or "markdown").lower()
        if formato_n not in ("markdown", "md", "txt", "plain"):
            raise FormatoNaoSuportadoError(
                f"formato '{formato}' nao suportado. Use markdown, md, txt ou plain."
            )

        linhas = texto.splitlines()
        casos = self._extrair_user_stories(linhas)
        ambiguidades = self._detectar_ambiguidades(linhas)
        atores = self._consolidar_atores(casos)

        avisos: List[str] = []
        if not casos:
            avisos.append(
                "Nenhuma user story no formato 'Como X, eu quero Y' foi reconhecida. "
                "Ambiguidades podem ainda assim ter sido detectadas."
            )

        diagrama = DiagramaCasoDeUso(
            atores=atores, casos_uso=casos, ambiguidades=ambiguidades, avisos=avisos,
        )
        diagrama.mermaid = self._gerar_mermaid(diagrama)
        return diagrama

    def extrair_de_pdf(self, conteudo_bytes: bytes) -> DiagramaCasoDeUso:
        if not conteudo_bytes:
            raise PDFInvalidoError("conteudo PDF vazio.")
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise PDFInvalidoError(f"pypdf nao instalado: {e}") from e
        try:
            reader = PdfReader(io.BytesIO(conteudo_bytes))
            paginas = []
            for page in reader.pages:
                paginas.append(page.extract_text() or "")
        except Exception as e:
            raise PDFInvalidoError(f"falha ao parsear PDF: {e}") from e
        texto = "\n".join(paginas)
        return self.extrair_de_texto(texto, formato="markdown")

    @staticmethod
    def _extrair_user_stories(linhas: List[str]) -> List[CasoDeUso]:
        agregado: dict = {}
        for i, linha in enumerate(linhas, start=1):
            match = _REGEX_USER_STORY.match(linha)
            if not match:
                continue
            ator = match.group("ator").strip()
            acao = match.group("acao").strip()
            beneficio = (match.group("beneficio") or "").strip()
            if not ator or not acao:
                continue
            chave = (acao.lower(), beneficio.lower())
            if chave in agregado:
                atores_existentes, linha_origem = agregado[chave]
                if ator not in atores_existentes:
                    atores_existentes.append(ator)
            else:
                agregado[chave] = ([ator], i)

        casos: List[CasoDeUso] = []
        for (acao_lower, _), (atores, linha_origem) in agregado.items():
            linha_original = linhas[linha_origem - 1]
            match = _REGEX_USER_STORY.match(linha_original)
            descricao = match.group("acao").strip() if match else acao_lower
            beneficio = (match.group("beneficio") or "").strip() if match else ""
            # Fallback: "X para Y" sem virgula tambem deve separar acao e beneficio.
            # Pegamos o ULTIMO " para " — assumindo que o beneficio vem por ultimo.
            if not beneficio and " para " in descricao:
                idx = descricao.rfind(" para ")
                beneficio = descricao[idx + len(" para "):].strip().rstrip(".;,")
                descricao = descricao[:idx].strip()
            casos.append(CasoDeUso(
                descricao=descricao,
                atores=tuple(sorted(atores)),
                beneficio=beneficio,
                linha_origem=linha_origem,
            ))
        casos.sort(key=lambda c: c.linha_origem)
        return casos

    @staticmethod
    def _consolidar_atores(casos: List[CasoDeUso]) -> List[Ator]:
        nomes = set()
        for c in casos:
            for a in c.atores:
                nomes.add(a)
        return [Ator(nome=n) for n in sorted(nomes)]

    @staticmethod
    def _detectar_ambiguidades(linhas: List[str]) -> List[Ambiguidade]:
        ambiguidades: List[Ambiguidade] = []
        for i, linha in enumerate(linhas, start=1):
            linha_lower = linha.lower()
            for palavra, motivo in _PALAVRAS_VAGAS.items():
                padrao = r"\b" + re.escape(palavra) + r"\b"
                if re.search(padrao, linha_lower):
                    ambiguidades.append(Ambiguidade(
                        linha=i,
                        trecho=linha.strip()[:120],
                        motivo=motivo,
                        palavra=palavra,
                    ))
                    break
            if _REGEX_RETICENCIAS.search(linha):
                ambiguidades.append(Ambiguidade(
                    linha=i,
                    trecho=linha.strip()[:120],
                    motivo="reticencias indicam continuacao implicita",
                    palavra="...",
                ))
        return ambiguidades

    @staticmethod
    def _gerar_mermaid(diagrama: DiagramaCasoDeUso) -> str:
        if not diagrama.atores and not diagrama.casos_uso:
            return "flowchart LR\n    vazio[Sem casos de uso reconhecidos]\n"

        linhas = ["flowchart LR"]
        ator_id = {}
        for i, ator in enumerate(diagrama.atores):
            aid = f"a{i}"
            ator_id[ator.nome] = aid
            linhas.append(f'    {aid}(("{_escapar(ator.nome)}"))')

        for j, caso in enumerate(diagrama.casos_uso):
            cid = f"u{j}"
            descricao_curta = caso.descricao[:60]
            linhas.append(f'    {cid}(["{_escapar(descricao_curta)}"])')
            for ator_nome in caso.atores:
                aid = ator_id.get(ator_nome)
                if aid:
                    linhas.append(f"    {aid} --> {cid}")

        linhas.append("    classDef ator fill:#e3f2fd,stroke:#1565c0,stroke-width:2px")
        linhas.append("    classDef uc fill:#fff3e0,stroke:#ef6c00")
        for aid in ator_id.values():
            linhas.append(f"    class {aid} ator")
        for j in range(len(diagrama.casos_uso)):
            linhas.append(f"    class u{j} uc")

        return "\n".join(linhas) + "\n"


def _escapar(s: str) -> str:
    """Escapa caracteres que quebrariam o Mermaid em strings entre aspas."""
    return s.replace('"', "'").replace("\n", " ")
