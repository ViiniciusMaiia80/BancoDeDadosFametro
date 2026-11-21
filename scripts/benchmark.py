#!/usr/bin/env python3
"""Comparativo de desempenho ANTES x DEPOIS da indexação (Biblioteca Fametro).

Fluxo:
  1. cria o banco: 01_ddl + 02_triggers + 03_dml_carga + 08_carga_volume + 05_views
  2. mede cada experimento SEM os índices de performance
  3. aplica 04_indices.sql (cronometrando) e mede de novo
  4. grava resultados.json (consumido pelo gerador do relatório)

Uso:  python3 benchmark/benchmark.py [caminho_do_banco]
Obs.: SQLite com configuração padrão (inclui "automatic indexes", que deixam o
      cenário SEM índices melhor do que seria na maioria dos SGBDs).
"""
import sqlite3, os, sys, time, json, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
SQL = os.path.join(BASE, "..", "sql")
DB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/benchmark_fametro.db"
OUT = os.path.join(BASE, "resultados.json")

def ler(nome):
    return open(os.path.join(SQL, nome), encoding="utf-8").read()

# ------------------------------------------------------------------ banco
if os.path.exists(DB):
    os.remove(DB)
c = sqlite3.connect(DB)
c.execute("PRAGMA foreign_keys = ON")
t0 = time.perf_counter()
for f in ("01_ddl.sql", "02_triggers.sql", "03_dml_carga.sql", "08_carga_volume.sql", "05_views.sql"):
    c.executescript(ler(f))
tempo_carga = time.perf_counter() - t0
q1 = lambda s, p=(): c.execute(s, p).fetchone()[0]
volumes = {t: q1(f"SELECT count(*) FROM {t}")
           for t in ("livro", "autor", "exemplar", "usuario", "emprestimo", "multa")}
print("Volumes:", volumes, f"(carga {tempo_carga:.1f}s)")

# --------------------------------------------------------------- parâmetros
isbns   = [r[0] for r in c.execute("SELECT isbn FROM livro WHERE id_livro % 700 = 5 LIMIT 200")]
livros  = [r[0] for r in c.execute("SELECT id_livro FROM livro WHERE id_livro % 700 = 9 LIMIT 200")]
usuarios = [r[0] for r in c.execute("SELECT id_usuario FROM usuario WHERE id_usuario > 4000 AND id_usuario % 140 = 3 LIMIT 200")]
prefs = ["Fundamentos de", "Introdução à", "Manual de", "Tratado de", "Curso de", "Atlas de", "Gestão de", "Técnicas de"]
assuntos1 = ["Fisiologia", "Patologia", "Hidráulica", "Topografia", "Termodinâmica", "Estatística", "Marketing",
             "Logística", "Periodontia", "Endodontia", "Radiologia", "Histologia", "Bioquímica", "Imunologia",
             "Bioética", "Sociologia", "Pediatria", "Ginecologia", "Ortodontia", "Genética"]
compls = ["Aplicada", "Avançada", "Básica", "Clínica", "Moderna", "Essencial", "Geral", "Crítica"]
titulos_prefixo = [f"{prefs[i % len(prefs)]} {assuntos1[i % len(assuntos1)]}%" for i in range(40)]
pares_palavras = [(assuntos1[i % len(assuntos1)], compls[(i * 3) % len(compls)]) for i in range(40)]
# nomes de autores que EXISTEM na carga (primeiro nome + 1º sobrenome => ~25 autores por busca)
nomes_autor = [" ".join(r[0].split()[:2]) + "%" for r in
               c.execute("SELECT nome FROM autor WHERE id_autor > 1000 AND id_autor % 1000 = 7 LIMIT 20")]

# par. de empréstimo/devolução: exemplares livres e usuários sem multa pendente/aberto
pares_op = [(r[0], r[1]) for r in c.execute("""
    SELECT x.id_exemplar, u.id_usuario
      FROM exemplar x JOIN usuario u ON u.id_usuario - 25000 = (x.id_exemplar - 200000) / 2
     WHERE x.id_exemplar BETWEEN 200000 AND 200600 AND x.status = 'disponivel'
       AND u.id_tipo = 1
       AND NOT EXISTS (SELECT 1 FROM multa m JOIN emprestimo e USING (id_emprestimo)
                        WHERE e.id_usuario = u.id_usuario AND m.status = 'pendente')
     LIMIT 250""")]

# -------------------------------------------------------------- experimentos
# (id, descrição, sql_antes, sql_depois, lista_de_parâmetros, repetições)
E = []
def exp(i, desc, antes, depois, params, reps=None):
    E.append(dict(id=i, desc=desc, antes=antes, depois=depois or antes, params=params, reps=reps or len(params)))

exp("E1", "Busca por ISBN (exato)",
    "SELECT id_livro, titulo FROM livro WHERE isbn = ?", None, [(x,) for x in isbns])
exp("E2", "Busca por título (começa com...)",
    "SELECT id_livro, titulo FROM livro WHERE titulo LIKE ? ORDER BY titulo", None, [(x,) for x in titulos_prefixo])
exp("E3", "Busca por 2 palavras em qualquer parte do título (LIKE '%a%' AND '%b%'  ->  FTS5)",
    "SELECT id_livro, titulo FROM livro WHERE titulo LIKE '%' || ? || '%' AND titulo LIKE '%' || ? || '%'",
    "SELECT l.id_livro, l.titulo FROM livro_fts f JOIN livro l ON l.id_livro = f.rowid WHERE livro_fts MATCH ? || ' ' || ?",
    pares_palavras)
exp("E4", "Obras de um autor (busca por nome)",
    "SELECT l.id_livro, l.titulo FROM autor a JOIN livro_autor la ON la.id_autor = a.id_autor "
    "JOIN livro l ON l.id_livro = la.id_livro WHERE a.nome LIKE ?", None, [(x,) for x in nomes_autor])
exp("E5", "Exemplares disponíveis de uma obra",
    "SELECT id_exemplar, patrimonio FROM exemplar WHERE id_livro = ? AND status = 'disponivel'", None,
    [(x,) for x in livros])
exp("E6", "Empréstimos em aberto do usuário (checagem de limite feita pela trigger)",
    "SELECT count(*) FROM emprestimo WHERE id_usuario = ? AND data_devolucao IS NULL", None, [(x,) for x in usuarios])
exp("E7", "Histórico recente de um usuário (JOIN com livro)",
    "SELECT e.data_emprestimo, l.titulo, e.data_devolucao FROM emprestimo e "
    "JOIN exemplar x ON x.id_exemplar = e.id_exemplar JOIN livro l ON l.id_livro = x.id_livro "
    "WHERE e.id_usuario = ? ORDER BY e.data_emprestimo DESC LIMIT 20", None, [(x,) for x in usuarios])
exp("E8", "Disponibilidade de uma obra (view vw_disponibilidade_acervo)",
    "SELECT * FROM vw_disponibilidade_acervo WHERE id_livro = ?", None, [(x,) for x in livros])
exp("E9", "Relatório: empréstimos atrasados (view vw_emprestimos_atrasados)",
    "SELECT * FROM vw_emprestimos_atrasados ORDER BY dias_atraso DESC LIMIT 50", None, [()], reps=5)
exp("E10", "Relatório: alunos com pendências (view vw_alunos_com_pendencias)",
    "SELECT * FROM vw_alunos_com_pendencias LIMIT 50", None, [()], reps=5)
exp("E11", "Relatório: livros mais emprestados por curso (view, agrega 505 mil empréstimos)",
    "SELECT * FROM vw_livros_mais_emprestados_por_curso", None, [()], reps=3)

def medir(sql, params, reps):
    """Retorna tempos em ms de cada execução (descarta 3 aquecimentos)."""
    for p in params[:3]:
        c.execute(sql, p).fetchall()
    ts, linhas = [], 0
    for i in range(reps):
        p = params[i % len(params)]
        t = time.perf_counter()
        r = c.execute(sql, p).fetchall()
        ts.append((time.perf_counter() - t) * 1000)
        linhas += len(r)
    return ts, linhas

def plano(sql, p):
    return " | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN " + sql, p).fetchall())

def resumo(ts):
    ts = sorted(ts)
    return dict(media=statistics.mean(ts), mediana=statistics.median(ts), p95=ts[min(len(ts) - 1, int(len(ts) * .95))])

def operacao_emprestimo():
    """Empréstimo + devolução completos (triggers), em transação revertida."""
    c.execute("BEGIN")
    t = time.perf_counter()
    for ex, us in pares_op:
        c.execute("INSERT INTO emprestimo(id_exemplar, id_usuario) VALUES (?, ?)", (ex, us))
        c.execute("UPDATE emprestimo SET data_devolucao = date('now') "
                  "WHERE id_exemplar = ? AND data_devolucao IS NULL", (ex,))
    dt = (time.perf_counter() - t) * 1000
    c.execute("ROLLBACK")
    return dt

INS_SQL = """
INSERT INTO emprestimo (id_exemplar, id_usuario, data_emprestimo, data_prevista, data_devolucao)
WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r WHERE n < 50000)
SELECT 1001 + (n * 2654435761 % 4294967296) % 255000, 1001 + (n * 2246822519 % 4294967296) % 30000,
       date('now','-100 days'), date('now','-93 days'), date('now','-95 days')
  FROM r"""
def custo_escrita():
    c.execute("BEGIN")
    t = time.perf_counter()
    c.execute(INS_SQL)
    dt = (time.perf_counter() - t) * 1000
    c.execute("ROLLBACK")
    return dt

# ------------------------------------------------------------------- rodada
def rodada(rotulo):
    print(f"\n=== {rotulo} ===")
    res = {}
    for e in E:
        sql = e["antes"] if rotulo == "ANTES" else e["depois"]
        ts, linhas = medir(sql, e["params"], e["reps"])
        r = resumo(ts)
        r.update(linhas=linhas / e["reps"], plano=plano(sql, e["params"][0]), reps=e["reps"])
        res[e["id"]] = r
        print(f"{e['id']:4s} média {r['media']:9.3f} ms  mediana {r['mediana']:9.3f} ms  linhas/exec {r['linhas']:.0f}")
    ops = [operacao_emprestimo() for _ in range(3)]
    res["OP"] = dict(ms_total=statistics.median(ops), n=len(pares_op))
    ws = [custo_escrita() for _ in range(3)]
    res["INS"] = dict(ms_total=statistics.median(ws), n=50000)
    print(f"OP   {len(pares_op)} empréstimos+devoluções via triggers: {res['OP']['ms_total']:.0f} ms")
    print(f"INS  50.000 empréstimos históricos: {res['INS']['ms_total']:.0f} ms")
    return res

tam_antes = os.path.getsize(DB) / 1e6
antes = rodada("ANTES")

t = time.perf_counter()
c.executescript(ler("04_indices.sql"))
tempo_indices = time.perf_counter() - t
c.commit()
tam_depois = os.path.getsize(DB) / 1e6
print(f"\nIndexação concluída em {tempo_indices:.1f}s | banco {tam_antes:.0f} MB -> {tam_depois:.0f} MB")

depois = rodada("DEPOIS")

out = dict(volumes=volumes, tempo_indices_s=tempo_indices, tam_antes_mb=tam_antes, tam_depois_mb=tam_depois,
           sqlite=sqlite3.sqlite_version, experimentos=[{k: e[k] for k in ("id", "desc")} for e in E],
           antes=antes, depois=depois, n_indices=q1("SELECT count(*) FROM sqlite_master WHERE type='index' AND name LIKE '%idx_%' OR name='ux_livro_isbn'"))
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
print("\nresultados em", OUT)
