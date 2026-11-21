from fastapi import HTTPException

from app.entities.usuario import Usuario


class UserService:
    def check_admin(self, usuario: Usuario) -> None:
        if not usuario.is_admin:
            raise HTTPException(403, "Usuario sem permissao de administrador")
