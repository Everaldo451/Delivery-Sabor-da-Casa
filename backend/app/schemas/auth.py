from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("senha")
    @classmethod
    def validar_tamanho_senha_bcrypt(cls, senha: str) -> str:
        if len(senha.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no maximo 72 bytes")
        return senha


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
