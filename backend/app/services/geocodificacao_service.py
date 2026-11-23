import httpx


class GeocodificacaoIndisponivelError(Exception):
    pass


class PhotonService:
    URL = "https://photon.komoot.io/api/"
    LIMITE_SUGESTOES = 5

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def sugerir_enderecos(self, consulta: str) -> list[dict]:
        parametros = {
            "q": consulta,
            "limit": self.LIMITE_SUGESTOES,
            "lang": "pt",
            "countrycode": "BR",
        }
        try:
            if self._client is not None:
                resposta = await self._client.get(
                    self.URL,
                    params=parametros,
                    headers={"User-Agent": "SaborDaCasaBackend/1.0"},
                )
            else:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resposta = await client.get(
                        self.URL,
                        params=parametros,
                        headers={"User-Agent": "SaborDaCasaBackend/1.0"},
                    )
            resposta.raise_for_status()
            dados = resposta.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GeocodificacaoIndisponivelError from exc

        if not isinstance(dados, dict):
            raise GeocodificacaoIndisponivelError("Resposta invalida do Photon")

        sugestoes = []
        for feature in dados.get("features", []):
            try:
                propriedades = feature["properties"]
                longitude, latitude = feature["geometry"]["coordinates"]
                latitude = float(latitude)
                longitude = float(longitude)
                rua = propriedades.get("street") or propriedades.get("name") or ""
                numero = propriedades.get("housenumber")
                bairro = propriedades.get("district") or propriedades.get("locality") or ""
                cidade = propriedades.get("city") or propriedades.get("county") or ""
                estado = propriedades.get("state") or ""
                cep = propriedades.get("postcode") or ""
                endereco = " ".join(parte for parte in (rua, numero) if parte)
                contexto = " - ".join(parte for parte in (bairro, cidade, estado, cep) if parte)
                sugestoes.append(
                    {
                        "descricao": " · ".join(parte for parte in (endereco, contexto) if parte),
                        "rua": rua,
                        "numero": numero,
                        "bairro": bairro,
                        "cidade": cidade,
                        "estado": estado,
                        "cep": cep,
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue

        return sugestoes
