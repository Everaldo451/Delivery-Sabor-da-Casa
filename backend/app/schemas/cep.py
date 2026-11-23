from pydantic import BaseModel

class CepEnderecoOut(BaseModel):
    cep: str
    rua: str
    bairro: str
    cidade: str
    estado: str
