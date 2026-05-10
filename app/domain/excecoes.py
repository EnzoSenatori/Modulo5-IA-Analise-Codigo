class AnaliseCodigoError(Exception):
    """Erro base para todas as exceções do módulo de IA"""
    pass

class ParserError(AnaliseCodigoError):
    """Lançado quando o código-fonte possui erros de sintaxe ou não pode ser lido"""
    pass

class EspecificacaoInvalidaError(AnaliseCodigoError):
    """Lançado quando os dados extraídos não formam uma especificação OpenAPI válida"""
    pass

class LLMError(AnaliseCodigoError):
    """Lançado quando a chamada ao provedor de LLM falha (timeout, JSON inválido, rede)"""
    pass


class AssinaturaWebhookInvalidaError(AnaliseCodigoError):
    """X-Hub-Signature-256 nao bate com HMAC do payload (US IA-11)."""
    pass


class WebhookIgnoradoError(AnaliseCodigoError):
    """Evento de webhook recebido mas nao alvo de processamento (ex: action='closed')."""
    pass


class GitHubAPIError(AnaliseCodigoError):
    """Falha de rede ou status HTTP inesperado ao falar com GitHub."""
    pass


class CoberturaInvalidaError(AnaliseCodigoError):
    """Inputs invalidos para analise de cobertura (codigo vazio, etc)."""
    pass


class IgnorarInvalidoError(AnaliseCodigoError):
    """Tentativa de marcar componente como ignorado com dados faltando."""
    pass
