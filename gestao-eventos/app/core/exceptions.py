import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

logger = logging.getLogger("gestao_eventos")


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    tipo = "erro_aplicacao"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    tipo = "requisicao_invalida"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    tipo = "recurso_nao_encontrado"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    tipo = "conflito"


class BusinessRuleError(AppError):
    status_code = status.HTTP_409_CONFLICT
    tipo = "regra_de_negocio"


def traduzir_integridade(exc: IntegrityError) -> str:
    """Converte a mensagem do SGBD em texto amigável (sem expor detalhes internos)."""
    msg = str(exc.orig).lower()
    if "unique" in msg or "duplicate" in msg:
        return "Já existe um registro com esses dados (valor único duplicado)."
    if "foreign key" in msg:
        return "Referência inválida: o registro relacionado não existe ou possui dependências."
    if "not null" in msg or "null value" in msg:
        return "Campo obrigatório não informado."
    if "check" in msg:
        return "Os dados violam uma restrição de integridade."
    return "A operação viola uma restrição de integridade."


def _resposta(status_code: int, tipo: str, detail: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"tipo": tipo, "detail": detail, **extra})


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _resposta(exc.status_code, exc.tipo, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError):
        erros = [
            {"campo": ".".join(str(p) for p in e["loc"]), "mensagem": e["msg"]}
            for e in exc.errors()
        ]
        if any(e["loc"] and e["loc"][0] == "path" for e in exc.errors()):
            return _resposta(400, "identificador_invalido", "Identificador inválido.", erros=erros)
        return _resposta(422, "dados_invalidos", "Dados inválidos.", erros=erros)

    @app.exception_handler(IntegrityError)
    async def _integridade(_: Request, exc: IntegrityError):
        return _resposta(409, "violacao_integridade", traduzir_integridade(exc))

    @app.exception_handler(OperationalError)
    async def _banco_indisponivel(_: Request, exc: OperationalError):
        logger.error("Erro de conexão com o banco: %s", exc)
        return _resposta(503, "banco_indisponivel", "Banco de dados indisponível. Tente novamente.")

    @app.exception_handler(SQLAlchemyError)
    async def _persistencia(_: Request, exc: SQLAlchemyError):
        logger.exception("Falha de persistência")
        return _resposta(500, "falha_persistencia", "Falha ao acessar os dados.")

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, exc: Exception):
        logger.exception("Erro inesperado")
        return _resposta(500, "erro_interno", "Erro interno inesperado.")