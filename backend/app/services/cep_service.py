import httpx


class CepNaoEncontradoError(Exception):
    pass


class ViaCepIndisponivelError(Exception):
    pass


class BrasilApiIndisponivelError(Exception):
    pass


class ViaCepService:
    URL = "https://viacep.com.br/ws/{cep}/json/"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def verificar_cep(self, cep: str) -> None:
        try:
            if self._client is not None:
                resposta = await self._client.get(self.URL.format(cep=cep))
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resposta = await client.get(self.URL.format(cep=cep))
            resposta.raise_for_status()
            dados = resposta.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ViaCepIndisponivelError from exc

        if not isinstance(dados, dict):
            raise ViaCepIndisponivelError("Resposta invalida do ViaCEP")
        if dados.get("erro") in (True, "true"):
            raise CepNaoEncontradoError(cep)


class BrasilApiCepService:
    """Consulta endereco e coordenada aproximada do CEP pela BrasilAPI."""

    URL = "https://brasilapi.com.br/api/cep/v2/{cep}"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def consultar(self, cep: str) -> dict:
        try:
            if self._client is not None:
                resposta = await self._client.get(self.URL.format(cep=cep))
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resposta = await client.get(self.URL.format(cep=cep))
            if resposta.status_code == 404:
                raise CepNaoEncontradoError(cep)
            resposta.raise_for_status()
            dados = resposta.json()
        except CepNaoEncontradoError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise BrasilApiIndisponivelError from exc

        try:
            return {
                "cep": dados["cep"],
                "rua": dados.get("street") or "",
                "bairro": dados.get("neighborhood") or "",
                "cidade": dados["city"],
                "estado": dados["state"],
            }
        except (KeyError, TypeError) as exc:
            raise BrasilApiIndisponivelError("Resposta invalida da BrasilAPI") from exc
