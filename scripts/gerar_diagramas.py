#!/usr/bin/env python3
"""Gera o DER conceitual e o modelo lógico (Graphviz) em PNG e PDF."""
import subprocess, os
BASE = os.path.dirname(os.path.abspath(__file__))

# =====================================================================
# 1) DER CONCEITUAL: entidades (retângulos), relacionamentos (losangos), cardinalidades
# =====================================================================
ENT = {
 "CURSO":        ["<u>id_curso</u>", "nome", "sigla"],
 "TIPO_USUARIO": ["<u>id_tipo</u>", "nome", "limite_emprestimos", "prazo_dias", "max_renovacoes", "valor_multa_dia"],
 "USUARIO":      ["<u>id_usuario</u>", "matricula", "nome", "email", "ativo", "data_cadastro"],
 "CATEGORIA":    ["<u>id_categoria</u>", "nome"],
 "EDITORA":      ["<u>id_editora</u>", "nome"],
 "AUTOR":        ["<u>id_autor</u>", "nome"],
 "LIVRO":        ["<u>id_livro</u>", "isbn", "titulo", "ano_publicacao", "edicao"],
 "EXEMPLAR":     ["<u>id_exemplar</u>", "patrimonio", "status", "data_aquisicao"],
 "EMPRESTIMO":   ["<u>id_emprestimo</u>", "data_emprestimo", "data_prevista", "data_devolucao"],
 "RENOVACAO":    ["<u>id_renovacao</u>", "numero", "data_renovacao", "nova_data_prevista"],
 "RESERVA":      ["<u>id_reserva</u>", "data_reserva", "status"],
 "MULTA":        ["<u>id_multa</u>", "dias_atraso", "valor", "status", "data_geracao", "data_pagamento"],
}
# (entidade A, cardinalidade A, rótulo, cardinalidade B, entidade B)
REL = [
 ("USUARIO", "N", "pertence a", "1", "CURSO"),
 ("USUARIO", "N", "é do tipo", "1", "TIPO_USUARIO"),
 ("LIVRO", "N", "classificado em", "1", "CATEGORIA"),
 ("LIVRO", "N", "publicado por", "1", "EDITORA"),
 ("LIVRO", "N", "escrito por", "N", "AUTOR"),
 ("LIVRO", "1", "possui", "N", "EXEMPLAR"),
 ("USUARIO", "1", "realiza", "N", "EMPRESTIMO"),
 ("EXEMPLAR", "1", "é emprestado em", "N", "EMPRESTIMO"),
 ("EMPRESTIMO", "1", "pode sofrer", "N", "RENOVACAO"),
 ("EMPRESTIMO", "1", "pode gerar", "0..1", "MULTA"),
 ("USUARIO", "1", "faz", "N", "RESERVA"),
 ("LIVRO", "1", "é reservado em", "N", "RESERVA"),
]

def entidade_html(nome, attrs):
    linhas = "".join(f'<TR><TD ALIGN="LEFT" PORT="a{i}"><FONT POINT-SIZE="10">{a}</FONT></TD></TR>' for i, a in enumerate(attrs))
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" BGCOLOR="#FFFFFF">'
            f'<TR><TD BGCOLOR="#1F4E79"><FONT COLOR="white" POINT-SIZE="12"><B>{nome}</B></FONT></TD></TR>{linhas}</TABLE>>')

def conceitual():
    d = ['graph DER {', 'graph [layout=neato, overlap=false, splines=true, sep="+18", bgcolor="white", '
         'pad=0.4, outputorder=edgesfirst, label=<<B>DER Conceitual - Biblioteca Fametro</B><BR/>'
         '<FONT POINT-SIZE="10">Retângulo = entidade (atributo sublinhado = chave primária) | Losango = relacionamento | '
         'N / 1 / 0..1 = cardinalidade</FONT>>, labelloc=t, fontname="Helvetica", fontsize=18];',
         'node [fontname="Helvetica"]; edge [fontname="Helvetica", fontsize=11, color="#555555", penwidth=1.2];']
    for n, a in ENT.items():
        d.append(f'"{n}" [shape=plain, label={entidade_html(n, a)}];')
    for i, (a, ca, rot, cb, b) in enumerate(REL):
        r = f"r{i}"
        d.append(f'{r} [shape=diamond, style=filled, fillcolor="#FFF2CC", color="#BF9000", '
                 f'label="{rot}", fontsize=10, width=1.5, height=0.8];')
        d.append(f'"{a}" -- {r} [headlabel="{ca}", labeldistance=2.2, fontcolor="#C00000", len=1.9];')
        d.append(f'{r} -- "{b}" [taillabel="{cb}", labeldistance=2.2, fontcolor="#C00000", len=1.9];')
    d.append("}")
    return "\n".join(d)

# =====================================================================
# 2) MODELO LÓGICO: tabelas, PK/FK/UK, setas pé-de-galinha
# =====================================================================
# tabela -> lista de (coluna, tipo, marcadores)
TAB = {
 "curso": [("id_curso", "INTEGER", "PK"), ("nome", "TEXT", "UK"), ("sigla", "TEXT", "UK")],
 "tipo_usuario": [("id_tipo", "INTEGER", "PK"), ("nome", "TEXT", "UK"), ("limite_emprestimos", "INTEGER", ""),
                  ("prazo_dias", "INTEGER", ""), ("max_renovacoes", "INTEGER", ""), ("valor_multa_dia", "NUMERIC", "")],
 "usuario": [("id_usuario", "INTEGER", "PK"), ("matricula", "TEXT", "UK"), ("nome", "TEXT", ""), ("email", "TEXT", "UK"),
             ("id_tipo", "INTEGER", "FK"), ("id_curso", "INTEGER", "FK"), ("ativo", "INTEGER", ""), ("data_cadastro", "TEXT", "")],
 "categoria": [("id_categoria", "INTEGER", "PK"), ("nome", "TEXT", "UK")],
 "editora": [("id_editora", "INTEGER", "PK"), ("nome", "TEXT", "UK")],
 "autor": [("id_autor", "INTEGER", "PK"), ("nome", "TEXT", "")],
 "livro": [("id_livro", "INTEGER", "PK"), ("isbn", "TEXT", "UK"), ("titulo", "TEXT", ""), ("ano_publicacao", "INTEGER", ""),
           ("edicao", "INTEGER", ""), ("id_editora", "INTEGER", "FK"), ("id_categoria", "INTEGER", "FK")],
 "livro_autor": [("id_livro", "INTEGER", "PK,FK"), ("id_autor", "INTEGER", "PK,FK"), ("ordem", "INTEGER", "")],
 "exemplar": [("id_exemplar", "INTEGER", "PK"), ("id_livro", "INTEGER", "FK"), ("patrimonio", "TEXT", "UK"),
              ("status", "TEXT", ""), ("data_aquisicao", "TEXT", "")],
 "emprestimo": [("id_emprestimo", "INTEGER", "PK"), ("id_exemplar", "INTEGER", "FK"), ("id_usuario", "INTEGER", "FK"),
                ("data_emprestimo", "TEXT", ""), ("data_prevista", "TEXT", ""), ("data_devolucao", "TEXT", "")],
 "renovacao": [("id_renovacao", "INTEGER", "PK"), ("id_emprestimo", "INTEGER", "FK,UK"), ("numero", "INTEGER", "UK"),
               ("data_renovacao", "TEXT", ""), ("nova_data_prevista", "TEXT", "")],
 "reserva": [("id_reserva", "INTEGER", "PK"), ("id_livro", "INTEGER", "FK"), ("id_usuario", "INTEGER", "FK"),
             ("data_reserva", "TEXT", ""), ("status", "TEXT", "")],
 "multa": [("id_multa", "INTEGER", "PK"), ("id_emprestimo", "INTEGER", "FK,UK"), ("dias_atraso", "INTEGER", ""),
           ("valor", "NUMERIC", ""), ("status", "TEXT", ""), ("data_geracao", "TEXT", ""), ("data_pagamento", "TEXT", "")],
}
COR = {"curso": "#DEEAF6", "tipo_usuario": "#DEEAF6", "categoria": "#DEEAF6", "editora": "#DEEAF6", "autor": "#E2F0D9",
       "livro": "#E2F0D9", "livro_autor": "#E2F0D9", "exemplar": "#E2F0D9", "usuario": "#DEEAF6",
       "emprestimo": "#FFF2CC", "renovacao": "#FFF2CC", "reserva": "#FFF2CC", "multa": "#FBE5D6"}
# FK: filha.coluna -> pai (lado N na filha, lado 1 no pai)
FKS = [("usuario", "id_tipo", "tipo_usuario"), ("usuario", "id_curso", "curso"),
       ("livro", "id_editora", "editora"), ("livro", "id_categoria", "categoria"),
       ("livro_autor", "id_livro", "livro"), ("livro_autor", "id_autor", "autor"),
       ("exemplar", "id_livro", "livro"), ("emprestimo", "id_exemplar", "exemplar"),
       ("emprestimo", "id_usuario", "usuario"), ("renovacao", "id_emprestimo", "emprestimo"),
       ("reserva", "id_livro", "livro"), ("reserva", "id_usuario", "usuario"),
       ("multa", "id_emprestimo", "emprestimo")]

def tabela_html(nome, cols):
    linhas = ""
    for c, t, m in cols:
        nm = f"<B>{c}</B>" if "PK" in m else c
        linhas += (f'<TR><TD ALIGN="LEFT" PORT="{c}"><FONT POINT-SIZE="10">{nm}</FONT></TD>'
                   f'<TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#555555">{t}</FONT></TD>'
                   f'<TD ALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#C00000"><B>{m}</B></FONT></TD></TR>')
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" BGCOLOR="{COR[nome]}">'
            f'<TR><TD COLSPAN="3" BGCOLOR="#1F4E79"><FONT COLOR="white" POINT-SIZE="12"><B>{nome}</B></FONT></TD></TR>{linhas}</TABLE>>')

def logico():
    d = ['digraph L {', 'graph [rankdir=LR, splines=ortho, nodesep=0.35, ranksep=1.1, pad=0.4, bgcolor="white", '
         'label=<<B>Modelo Lógico (3FN) - Biblioteca Fametro</B><BR/><FONT POINT-SIZE="10">PK = chave primária | FK = chave estrangeira | '
         'UK = única | Pé-de-galinha = lado N; traço = lado 1</FONT>>, labelloc=t, fontname="Helvetica", fontsize=18];',
         'node [shape=plain, fontname="Helvetica"]; edge [color="#444444", arrowhead=tee, arrowtail=crow, dir=both, penwidth=1.1];']
    for n, cols in TAB.items():
        d.append(f'"{n}" [label={tabela_html(n, cols)}];')
    for filha, col, pai in FKS:
        # seta do pai (1) para a filha (N): pé-de-galinha junto à filha
        d.append(f'"{pai}" -> "{filha}":"{col}" [arrowtail=tee, arrowhead=crow];')
    d.append("}")
    return "\n".join(d)

def render(nome, dot, engine):
    path = os.path.join(BASE, nome + ".dot")
    open(path, "w", encoding="utf-8").write(dot)
    for fmt in ("png", "pdf"):
        extra = ["-Gdpi=130"] if fmt == "png" else []
        subprocess.run([engine, f"-T{fmt}", *extra, path, "-o", os.path.join(BASE, f"{nome}.{fmt}")], check=True)
    print("ok", nome)

if __name__ == "__main__":
    render("DER_conceitual", conceitual(), "neato")
    render("DER_modelo_logico", logico(), "dot")
