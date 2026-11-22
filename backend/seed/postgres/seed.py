"""Importa dados locais de desenvolvimento para o PostgreSQL."""

import json
import mimetypes
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable

import bcrypt
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, select

from app.database.postgresql import create_session
from app.database.postgresql.models.cardapio import CategoriaModel, PratoModel
from app.database.postgresql.models.user import UserModel
from app.schemas.users import CadastroUsuario

PASTA_DADOS = Path(__file__).parent
PASTA_ASSETS = PASTA_DADOS / "assets"
IMAGEM_PADRAO = PASTA_ASSETS / "prato-padrao.png"


class UsuarioSeed(BaseModel):
    id: str
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    is_admin: bool
    senha_env: str


class CategoriaSeed(BaseModel):
    nome: str = Field(min_length=1, max_length=80)


class PratoSeed(BaseModel):
    id: str
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=2000)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    categoria: str
    disponivel: bool = True


@dataclass(frozen=True)
class DadosSeed:
    usuarios: list[UsuarioSeed]
    categorias: list[CategoriaSeed]
    pratos: list[PratoSeed]


def _ler_json(nome: str) -> list[dict]:
    dados = json.loads((PASTA_DADOS / nome).read_text(encoding="utf-8"))
    if not isinstance(dados, list):
        raise ValueError(f"{nome} deve conter uma lista JSON")
    return dados


def carregar_dados() -> DadosSeed:
    usuarios = [UsuarioSeed.model_validate(item) for item in _ler_json("usuarios.json")]
    categorias = [
        CategoriaSeed.model_validate(item) for item in _ler_json("categorias.json")
    ]
    pratos = [PratoSeed.model_validate(item) for item in _ler_json("pratos.json")]

    if len(usuarios) != 2 or sum(usuario.is_admin for usuario in usuarios) != 1:
        raise ValueError("O seed deve conter um usuario administrador e um usuario comum")
    nomes_categorias = {categoria.nome.casefold() for categoria in categorias}
    if len(nomes_categorias) != len(categorias):
        raise ValueError("O arquivo de categorias contem nomes duplicados")
    if len(pratos) != 40:
        raise ValueError("O arquivo pratos.json deve conter exatamente 40 pratos")
    ids = [prato.id for prato in pratos]
    if len(set(ids)) != len(ids):
        raise ValueError("O arquivo pratos.json contem identificadores duplicados")
    categorias_inexistentes = {
        prato.categoria
        for prato in pratos
        if prato.categoria.casefold() not in nomes_categorias
    }
    if categorias_inexistentes:
        raise ValueError(
            "Categorias ausentes no seed: " + ", ".join(sorted(categorias_inexistentes))
        )
    return DadosSeed(usuarios=usuarios, categorias=categorias, pratos=pratos)


def aplicar_seed(
    session: Session,
    dados: DadosSeed,
    senhas: dict[str, str],
) -> dict[str, int]:
    usuarios_validados: list[tuple[UsuarioSeed, CadastroUsuario]] = []
    for usuario in dados.usuarios:
        senha = senhas.get(usuario.senha_env)
        if not senha:
            raise ValueError(f"Defina a variavel de ambiente {usuario.senha_env}")
        cadastro = CadastroUsuario(nome=usuario.nome, email=usuario.email, senha=senha)
        usuarios_validados.append((usuario, cadastro))

    try:
        for usuario_config, cadastro in usuarios_validados:
            email = cadastro.email.strip().casefold()
            usuario_model = session.get(UserModel, usuario_config.id)
            if usuario_model is None:
                usuario_model = session.exec(
                    select(UserModel).where(func.lower(UserModel.email) == email)
                ).first()
            senha_hash = bcrypt.hashpw(
                cadastro.senha.encode("utf-8"), bcrypt.gensalt()
            ).decode("ascii")
            if usuario_model is None:
                usuario_model = UserModel(
                    id=usuario_config.id,
                    nome=cadastro.nome,
                    email=email,
                    senha_hash=senha_hash,
                    is_admin=usuario_config.is_admin,
                )
                session.add(usuario_model)
            else:
                usuario_model.nome = cadastro.nome
                usuario_model.email = email
                usuario_model.senha_hash = senha_hash
                usuario_model.is_admin = usuario_config.is_admin

        categorias_por_nome: dict[str, CategoriaModel] = {}
        for categoria_config in dados.categorias:
            nome_normalizado = categoria_config.nome.strip().casefold()
            categoria_model = session.exec(
                select(CategoriaModel).where(
                    func.lower(CategoriaModel.nome) == nome_normalizado
                )
            ).first()
            if categoria_model is None:
                categoria_model = CategoriaModel(nome=categoria_config.nome.strip())
                session.add(categoria_model)
            categorias_por_nome[nome_normalizado] = categoria_model

        session.flush()
        imagem_bytes = IMAGEM_PADRAO.read_bytes() if IMAGEM_PADRAO.is_file() else None
        tipo_imagem = (
            mimetypes.guess_type(IMAGEM_PADRAO.name)[0] if imagem_bytes else None
        )
        if imagem_bytes and tipo_imagem not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("A imagem padrao deve ser PNG, JPEG ou WebP")

        for prato_config in dados.pratos:
            categoria = categorias_por_nome[prato_config.categoria.casefold()]
            prato_model = session.get(PratoModel, prato_config.id)
            if prato_model is None:
                prato_model = PratoModel(
                    id=prato_config.id,
                    nome=prato_config.nome,
                    descricao=prato_config.descricao,
                    preco=prato_config.preco,
                    categoria_id=categoria.id,
                    imagem=imagem_bytes,
                    imagem_content_type=tipo_imagem,
                    disponivel=prato_config.disponivel,
                )
                session.add(prato_model)
            else:
                prato_model.nome = prato_config.nome
                prato_model.descricao = prato_config.descricao
                prato_model.preco = prato_config.preco
                prato_model.categoria_id = categoria.id
                prato_model.disponivel = prato_config.disponivel
                if imagem_bytes is not None and prato_model.imagem is None:
                    prato_model.imagem = imagem_bytes
                    prato_model.imagem_content_type = tipo_imagem

        session.commit()
    except Exception:
        session.rollback()
        raise

    return {
        "usuarios": len(usuarios_validados),
        "categorias": len(dados.categorias),
        "pratos": len(dados.pratos),
    }


def executar_seed(
    session_factory: Callable[[], Session] = create_session,
    variaveis_ambiente: dict[str, str] | None = None,
) -> dict[str, int]:
    dados = carregar_dados()
    ambiente = os.environ if variaveis_ambiente is None else variaveis_ambiente
    senhas = {
        usuario.senha_env: ambiente.get(usuario.senha_env, "")
        for usuario in dados.usuarios
    }
    with session_factory() as session:
        return aplicar_seed(session, dados, senhas)


def main() -> None:
    resultado = executar_seed()
    print(
        "Seed PostgreSQL aplicado: "
        f"{resultado['usuarios']} usuarios, "
        f"{resultado['categorias']} categorias e {resultado['pratos']} pratos."
    )


if __name__ == "__main__":
    main()
