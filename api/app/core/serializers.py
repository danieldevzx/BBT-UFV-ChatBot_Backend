def categoria_dict(c) -> dict:
    return {"id": c.id, "nome": c.nome, "descricao": c.descricao}


def conteudo_dict(c) -> dict:
    return {
        "id": c.id,
        "categoria_id": c.categoria_id,
        "titulo": c.titulo,
        "texto": c.texto,
        "fonte": c.fonte,
        "ativo": c.ativo,
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def no_fluxo_dict(n) -> dict:
    return {
        "id": n.id,
        "parent_id": n.parent_id,
        "titulo": n.titulo,
        "tipo": n.tipo,
        "conteudo_id": n.conteudo_id,
        "ordem": n.ordem,
        "ativo": n.ativo,
    }


def config_bot_dict(c) -> dict:
    return {"chave": c.chave, "valor": c.valor}


def atendimento_dict(a) -> dict:
    return {
        "id": a.id,
        "telefone_solicitante": a.telefone_solicitante,
        "usuario_atendente_id": a.usuario_atendente_id,
        "status": a.status,
        "canal": a.canal,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "closed_at": a.closed_at.isoformat() if a.closed_at else None,
    }


def mensagem_dict(m) -> dict:
    return {
        "id": m.id,
        "atendimento_id": m.atendimento_id,
        "remetente": m.remetente,
        "texto": m.texto,
        "enviado_em": m.enviado_em.isoformat() if m.enviado_em else None,
    }


def feedback_dict(f) -> dict:
    return {
        "id": f.id,
        "no_fluxo_id": f.no_fluxo_id,
        "util": f.util,
        "comentario": f.comentario,
        "criado_em": f.criado_em.isoformat() if f.criado_em else None,
    }


def log_dict(l) -> dict:
    return {
        "id": l.id,
        "usuario_id": l.usuario_id,
        "acao": l.acao,
        "tabela_afetada": l.tabela_afetada,
        "registro_id": l.registro_id,
        "criado_em": l.criado_em.isoformat() if l.criado_em else None,
    }
