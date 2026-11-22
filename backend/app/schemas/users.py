from pydantic import BaseModel, Field, field_validator


class CadastroUsuario(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=8, max_length=128)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        nome = nome.strip()
        if not nome:
            raise ValueError("O nome nao pode ficar vazio")
        return nome

    @field_validator("senha")
    @classmethod
    def validar_tamanho_senha_bcrypt(cls, senha: str) -> str:
        if len(senha.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no maximo 72 bytes")
        return senha


class UsuarioOut(BaseModel):
    id: str
    nome: str
    email: str
