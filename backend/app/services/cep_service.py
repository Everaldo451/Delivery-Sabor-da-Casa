import httpx


class CepNaoEncontradoError(Exception):
    pass


class CepServiceIndisponivelError(Exception):
    pass


# Alias mantido para compatibilidade com chamadas existentes.
ViaCepIndisponivelError = CepServiceIndisponivelError


class ViaCepService:
    """Consulta o endereco e valida a existencia de um CEP via ViaCEP."""

    URL = "https://viacep.com.br/ws/{cep}/json/"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _consultar_dados(self, cep: str) -> dict:
        try:
            if self._client is not None:
                resposta = await self._client.get(self.URL.format(cep=cep))
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resposta = await client.get(self.URL.format(cep=cep))
            resposta.raise_for_status()
            dados = resposta.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CepServiceIndisponivelError from exc

        if not isinstance(dados, dict):
            raise CepServiceIndisponivelError("Resposta invalida do ViaCEP")
        if dados.get("erro") in (True, "true"):
            raise CepNaoEncontradoError(cep)
        return dados

    async def consultar(self, cep: str) -> dict[str, str]:
        dados = await self._consultar_dados(cep)

        try:
            return {
                "cep": str(dados["cep"]).replace("-", ""),
                "rua": dados.get("logradouro") or "",
                "bairro": dados.get("bairro") or "",
                "cidade": dados["localidade"],
                "estado": dados["uf"],
            }
        except (KeyError, TypeError) as exc:
            raise CepServiceIndisponivelError(
                "Resposta invalida do ViaCEP"
            ) from exc

    async def verificar_cep(self, cep: str) -> None:
        await self._consultar_dados(cep)
