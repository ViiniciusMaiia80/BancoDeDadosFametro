#!/usr/bin/env python3
"""Testes das triggers/regras de negócio da biblioteca Fametro.

Cria um banco em memória a partir de 01_ddl.sql + 02_triggers.sql, insere uma
fixture mínima e verifica cada regra (cenário válido e cenários que DEVEM falhar).
Uso:  python3 testes/test_triggers.py
"""
import sqlite3, os, sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql")
resultados = []

def novo_banco():
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    for f in ("01_ddl.sql", "02_triggers.sql"):
        c.executescript(open(os.path.join(RAIZ, f), encoding="utf-8").read())
    c.executescript("""
    INSERT INTO curso VALUES (1,'Direito','DIR');
    INSERT INTO tipo_usuario VALUES (1,'ALUNO',3,7,2,1.00),(2,'DOCENTE',5,15,3,0.50);
    INSERT INTO categoria VALUES (1,'Direito');
    INSERT INTO editora VALUES (1,'Saraiva');
    INSERT INTO autor VALUES (1,'Autor Teste');
    INSERT INTO livro VALUES (1,'9788500000011','Livro A',2020,1,1,1),
                             (2,'9788500000028','Livro B',2020,1,1,1),
                             (3,'9788500000035','Livro C',2020,1,1,1),
                             (4,'9788500000042','Livro D',2020,1,1,1);
    INSERT INTO livro_autor VALUES (1,1,1),(2,1,1),(3,1,1),(4,1,1);
    -- livro 1: 1 exemplar | livro 2: 2 exemplares | livros 3 e 4: 1 exemplar
    INSERT INTO exemplar(id_exemplar,id_livro,patrimonio) VALUES (1,1,'P1'),(2,2,'P2'),(3,2,'P3'),(4,3,'P4'),(5,4,'P5');
    INSERT INTO usuario(id_usuario,matricula,nome,email,id_tipo,id_curso,ativo) VALUES
      (1,'A1','Aluno Um','a1@x.com',1,1,1),(2,'A2','Aluno Dois','a2@x.com',1,1,1),
      (3,'A3','Aluno Tres','a3@x.com',1,1,1),(4,'D1','Docente Um','d1@x.com',2,1,1),
      (5,'A5','Aluno Inativo','a5@x.com',1,1,0);
    """)
    return c

def ok(c, nome, sql, *p):
    """Espera que a instrução funcione."""
    try:
        c.execute(sql, p)
        resultados.append((nome, True, "executou"))
    except sqlite3.Error as e:
        resultados.append((nome, False, f"erro inesperado: {e}"))

def erro(c, nome, esperado, sql, *p):
    """Espera que a instrução seja REJEITADA com a mensagem esperada."""
    try:
        c.execute(sql, p)
        resultados.append((nome, False, "deveria ter sido rejeitada"))
    except sqlite3.Error as e:
        resultados.append((nome, esperado.lower() in str(e).lower(), str(e)))

def igual(nome, obtido, esperado):
    resultados.append((nome, obtido == esperado, f"obtido={obtido!r} esperado={esperado!r}"))

def val(c, sql, *p):
    r = c.execute(sql, p).fetchone()
    return r[0] if r else None

def emprestar(c, ex, us, dias_atras=0):
    c.execute("INSERT INTO emprestimo(id_exemplar,id_usuario,data_emprestimo) "
              "VALUES (?,?,date('now',?))", (ex, us, f"-{dias_atras} days"))
    return val(c, "SELECT max(id_emprestimo) FROM emprestimo")

# ======================================================================
# 1. EMPRÉSTIMO
c = novo_banco()
e1 = emprestar(c, 1, 1)
igual("1.1 empréstimo: exemplar passa a 'emprestado'", val(c, "SELECT status FROM exemplar WHERE id_exemplar=1"), "emprestado")
igual("1.2 prazo do ALUNO = 7 dias", val(c, "SELECT julianday(data_prevista)-julianday(data_emprestimo) FROM emprestimo WHERE id_emprestimo=?", e1), 7.0)
e_doc = emprestar(c, 2, 4)
igual("1.3 prazo do DOCENTE = 15 dias", val(c, "SELECT julianday(data_prevista)-julianday(data_emprestimo) FROM emprestimo WHERE id_emprestimo=?", e_doc), 15.0)
erro(c, "1.4 exemplar já emprestado é recusado", "indisponivel",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (1,2)")
erro(c, "1.5 usuário inativo é recusado", "inativo",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (4,5)")
# limite (aluno = 3)
c = novo_banco()
emprestar(c, 1, 1); emprestar(c, 2, 1); emprestar(c, 3, 1)
erro(c, "1.6 4º empréstimo simultâneo do aluno (limite 3) é recusado", "limite",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (4,1)")
erro(c, "1.7 manual: marcar exemplar emprestado 'disponivel' é recusado", "devolucao",
     "UPDATE exemplar SET status='disponivel' WHERE id_exemplar=1")
erro(c, "1.8 manual: marcar 'emprestado' sem empréstimo é recusado", "so pode ser definido",
     "UPDATE exemplar SET status='emprestado' WHERE id_exemplar=4")

# ======================================================================
# 2. DEVOLUÇÃO E MULTA AUTOMÁTICA
c = novo_banco()
e = emprestar(c, 1, 1, dias_atras=5)                      # vence em +2 dias
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
igual("2.1 devolução no prazo: não gera multa", val(c, "SELECT count(*) FROM multa"), 0)
igual("2.2 devolução: exemplar volta a 'disponivel'", val(c, "SELECT status FROM exemplar WHERE id_exemplar=1"), "disponivel")

e = emprestar(c, 1, 1, dias_atras=12)                     # vencia há 5 dias
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
igual("2.3 atraso de 5 dias (aluno): dias_atraso=5", val(c, "SELECT dias_atraso FROM multa WHERE id_emprestimo=?", e), 5)
igual("2.4 multa aluno R$1,00/dia = R$5,00", val(c, "SELECT valor FROM multa WHERE id_emprestimo=?", e), 5)
igual("2.5 multa nasce 'pendente'", val(c, "SELECT status FROM multa WHERE id_emprestimo=?", e), "pendente")

e = emprestar(c, 2, 4, dias_atras=25)                     # docente vencia há 10 dias
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
igual("2.6 multa docente R$0,50/dia x 10 dias = R$5,00", val(c, "SELECT valor FROM multa WHERE id_emprestimo=?", e), 5)
erro(c, "2.7 alterar devolução de empréstimo encerrado é recusado", "encerrado",
     "UPDATE emprestimo SET data_devolucao=date('now','-1 day') WHERE id_emprestimo=?", e)

# ======================================================================
# 3. MULTA PENDENTE / ATRASO BLOQUEIAM NOVOS EMPRÉSTIMOS
erro(c, "3.1 aluno com multa pendente não empresta", "multa pendente",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (4,1)")
id_multa_aluno = val(c, "SELECT m.id_multa FROM multa m JOIN emprestimo e USING(id_emprestimo) WHERE e.id_usuario=1")
c.execute("UPDATE multa SET status='paga' WHERE id_multa=?", (id_multa_aluno,))
igual("3.2 pagamento registra data_pagamento automaticamente",
      val(c, "SELECT data_pagamento FROM multa WHERE id_multa=?", id_multa_aluno), val(c, "SELECT date('now')"))
ok(c, "3.3 após pagar, aluno volta a emprestar", "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (4,1)")
c = novo_banco()
emprestar(c, 1, 2, dias_atras=10)                         # vencido e em aberto
erro(c, "3.4 aluno com livro em atraso não empresta outro", "atraso",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (4,2)")

# ======================================================================
# 4. RENOVAÇÃO
c = novo_banco()
e = emprestar(c, 1, 1, dias_atras=3)
prev0 = val(c, "SELECT data_prevista FROM emprestimo WHERE id_emprestimo=?", e)
ok(c, "4.1 renovação nº1 aceita", "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,1)", e)
igual("4.2 renovação estende data_prevista (hoje + 7d)",
      val(c, "SELECT data_prevista FROM emprestimo WHERE id_emprestimo=?", e), val(c, "SELECT date('now','+7 days')"))
igual("4.3 renovacao.nova_data_prevista preenchida",
      val(c, "SELECT nova_data_prevista FROM renovacao WHERE id_emprestimo=?", e), val(c, "SELECT date('now','+7 days')"))
erro(c, "4.4 renovação simultânea com mesmo número é recusada", "concorrente",
     "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,1)", e)
ok(c, "4.5 renovação nº2 aceita (limite do aluno = 2)", "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,2)", e)
erro(c, "4.6 renovação nº3 excede o limite", "limite de renovacoes",
     "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,3)", e)
c = novo_banco()
e = emprestar(c, 1, 1, dias_atras=10)
erro(c, "4.7 empréstimo em atraso não renova", "atraso",
     "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,1)", e)
c = novo_banco()
e = emprestar(c, 1, 1)
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
erro(c, "4.8 empréstimo devolvido não renova", "encerrado",
     "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,1)", e)
c = novo_banco()
e = emprestar(c, 1, 1)                                   # único exemplar do livro 1
ok(c, "4.9 reserva do livro 1 por outro usuário", "INSERT INTO reserva(id_livro,id_usuario) VALUES (1,2)")
erro(c, "4.10 livro com reserva de outro usuário não renova", "reservado",
     "INSERT INTO renovacao(id_emprestimo,numero) VALUES (?,1)", e)
c = novo_banco()
e = emprestar(c, 1, 1)
modelo = "INSERT INTO renovacao(id_emprestimo,numero) SELECT ?, 1 + COUNT(*) FROM renovacao WHERE id_emprestimo = ?"
ok(c, "4.11 modelo de uso (numero = 1 + COUNT) : 1ª renovação", modelo, e, e)
ok(c, "4.12 modelo de uso (numero = 1 + COUNT) : 2ª renovação", modelo, e, e)
erro(c, "4.13 modelo de uso: 3ª renovação excede o limite", "limite de renovacoes", modelo, e, e)

# ======================================================================
# 5. RESERVA
c = novo_banco()
erro(c, "5.1 reservar livro com exemplar disponível é recusado", "disponivel",
     "INSERT INTO reserva(id_livro,id_usuario) VALUES (1,2)")
e = emprestar(c, 1, 1)                                   # livro 1 sem exemplares livres
erro(c, "5.2 usuário não reserva livro que já está com ele", "ja esta com este livro",
     "INSERT INTO reserva(id_livro,id_usuario) VALUES (1,1)")
ok(c, "5.3 reserva do livro 1 (sem exemplar livre) aceita", "INSERT INTO reserva(id_livro,id_usuario) VALUES (1,2)")
erro(c, "5.4 reserva ativa duplicada é recusada (índice único parcial)", "unique",
     "INSERT INTO reserva(id_livro,id_usuario) VALUES (1,2)")
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
igual("5.5 devolução com fila: exemplar fica 'reservado'", val(c, "SELECT status FROM exemplar WHERE id_exemplar=1"), "reservado")
erro(c, "5.6 outro usuário não pega exemplar reservado", "reservado para outro",
     "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (1,3)")
ok(c, "5.7 quem reservou consegue emprestar", "INSERT INTO emprestimo(id_exemplar,id_usuario) VALUES (1,2)")
igual("5.8 reserva passa a 'atendida'", val(c, "SELECT status FROM reserva WHERE id_livro=1 AND id_usuario=2"), "atendida")
igual("5.9 exemplar passa a 'emprestado'", val(c, "SELECT status FROM exemplar WHERE id_exemplar=1"), "emprestado")
erro(c, "5.10 reserva finalizada não pode ser reaberta", "finalizada",
     "UPDATE reserva SET status='ativa' WHERE id_livro=1 AND id_usuario=2")
# cancelamento libera exemplar retido
c = novo_banco()
e = emprestar(c, 1, 1)
c.execute("INSERT INTO reserva(id_livro,id_usuario) VALUES (1,2)")
c.execute("UPDATE emprestimo SET data_devolucao=date('now') WHERE id_emprestimo=?", (e,))
c.execute("UPDATE reserva SET status='cancelada' WHERE id_livro=1 AND id_usuario=2")
igual("5.11 cancelar a reserva libera o exemplar retido", val(c, "SELECT status FROM exemplar WHERE id_exemplar=1"), "disponivel")

# ======================================================================
# 6. INTEGRIDADE REFERENCIAL / CONSTRAINTS
c = novo_banco()
erro(c, "6.1 FK: empréstimo de exemplar inexistente", "foreign key",
     "INSERT INTO emprestimo(id_exemplar,id_usuario,data_devolucao) VALUES (999,1,date('now'))")
erro(c, "6.2 CHECK: ISBN com letras", "check",
     "INSERT INTO livro(isbn,titulo,id_editora,id_categoria) VALUES ('97885000000AB','X',1,1)")
erro(c, "6.3 CHECK: status inválido de exemplar", "check",
     "UPDATE exemplar SET status='sumido' WHERE id_exemplar=1")
erro(c, "6.4 UNIQUE: patrimônio duplicado", "unique",
     "INSERT INTO exemplar(id_livro,patrimonio) VALUES (1,'P1')")
erro(c, "6.5 CHECK: devolução antes do empréstimo", "check",
     "INSERT INTO emprestimo(id_exemplar,id_usuario,data_emprestimo,data_devolucao) VALUES (1,1,date('now'),date('now','-1 day'))")
emprestar(c, 1, 1)
erro(c, "6.6 FK: não exclui usuário com empréstimos", "foreign key",
     "DELETE FROM usuario WHERE id_usuario=1")

# ======================================================================
largura = max(len(n) for n, _, _ in resultados)
falhas = 0
for n, passou, msg in resultados:
    print(f"[{'PASS' if passou else 'FAIL'}] {n:<{largura}}" + ("" if passou else f"  -> {msg}"))
    falhas += (not passou)
print(f"\n{len(resultados) - falhas}/{len(resultados)} testes passaram")
sys.exit(1 if falhas else 0)
