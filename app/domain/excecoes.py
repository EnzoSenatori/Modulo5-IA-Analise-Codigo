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
