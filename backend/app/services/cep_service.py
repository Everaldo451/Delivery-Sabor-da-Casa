import httpx


class CepNaoEncontradoError(Exception):
    pass


class ViaCepIndisponivelError(Exception):
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
