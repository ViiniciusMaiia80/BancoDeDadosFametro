-- =====================================================================
-- BIBLIOTECA FAMETRO - 05_views.sql   (relatórios gerenciais)
-- =====================================================================
DROP VIEW IF EXISTS vw_livros_mais_emprestados_por_curso;
DROP VIEW IF EXISTS vw_usuarios_com_pendencias;
DROP VIEW IF EXISTS vw_alunos_com_pendencias;
DROP VIEW IF EXISTS vw_emprestimos_atrasados;
DROP VIEW IF EXISTS vw_disponibilidade_acervo;
DROP VIEW IF EXISTS vw_multas_por_curso;

-- Top 10 livros mais emprestados em cada curso (curso do usuário que emprestou).
-- Agrega por IDs inteiros (barato) e só depois busca os nomes das 10 linhas por curso.
CREATE VIEW vw_livros_mais_emprestados_por_curso AS
WITH base AS (
    SELECT u.id_curso, x.id_livro, COUNT(*) AS total_emprestimos
      FROM emprestimo e
      JOIN usuario  u ON u.id_usuario  = e.id_usuario
      JOIN exemplar x ON x.id_exemplar = e.id_exemplar
     GROUP BY u.id_curso, x.id_livro
), ranking AS (
    SELECT b.id_curso, b.id_livro, b.total_emprestimos,
           ROW_NUMBER() OVER (PARTITION BY b.id_curso
                              ORDER BY b.total_emprestimos DESC, b.id_livro) AS posicao
      FROM base b
)
SELECT c.nome AS curso, r.posicao, l.titulo, r.total_emprestimos
  FROM ranking r
  JOIN curso c ON c.id_curso = r.id_curso
  JOIN livro l ON l.id_livro = r.id_livro
 WHERE r.posicao <= 10
 ORDER BY c.nome, r.posicao;

-- Empréstimos em aberto e vencidos, com multa projetada até hoje
CREATE VIEW vw_emprestimos_atrasados AS
SELECT e.id_emprestimo, u.matricula, u.nome AS usuario, t.nome AS tipo, c.sigla AS curso,
       l.titulo, x.patrimonio, e.data_emprestimo, e.data_prevista,
       CAST(julianday('now') - julianday(e.data_prevista) AS INTEGER) AS dias_atraso,
       CAST(julianday('now') - julianday(e.data_prevista) AS INTEGER) * t.valor_multa_dia AS multa_projetada
  FROM emprestimo e
  JOIN usuario u       ON u.id_usuario  = e.id_usuario
  JOIN tipo_usuario t  ON t.id_tipo     = u.id_tipo
  JOIN curso c         ON c.id_curso    = u.id_curso
  JOIN exemplar x      ON x.id_exemplar = e.id_exemplar
  JOIN livro l         ON l.id_livro    = x.id_livro
 WHERE e.data_devolucao IS NULL
   AND e.data_prevista < date('now');

-- Usuários com pendências: multas a pagar e/ou empréstimos vencidos.
-- A consulta parte do conjunto (pequeno) de devedores e só então busca os dados
-- cadastrais - evita varrer todos os usuários.
CREATE VIEW vw_usuarios_com_pendencias AS
WITH multas AS (
    SELECT e.id_usuario, COUNT(*) AS qtd, SUM(mu.valor) AS valor
      FROM multa mu JOIN emprestimo e ON e.id_emprestimo = mu.id_emprestimo
     WHERE mu.status = 'pendente'
     GROUP BY e.id_usuario
), atrasos AS (
    SELECT e.id_usuario, COUNT(*) AS qtd,
           MAX(CAST(julianday('now') - julianday(e.data_prevista) AS INTEGER)) AS maior_atraso,
           SUM(CAST(julianday('now') - julianday(e.data_prevista) AS INTEGER) * t2.valor_multa_dia) AS projetada
      FROM emprestimo e
      JOIN usuario u2      ON u2.id_usuario = e.id_usuario
      JOIN tipo_usuario t2 ON t2.id_tipo    = u2.id_tipo
     WHERE e.data_devolucao IS NULL AND e.data_prevista < date('now')
     GROUP BY e.id_usuario
), devedores AS (
    SELECT id_usuario FROM multas UNION SELECT id_usuario FROM atrasos
)
SELECT u.id_usuario, u.matricula, u.nome, t.nome AS tipo, c.nome AS curso,
       COALESCE(m.qtd, 0)            AS multas_pendentes,
       COALESCE(m.valor, 0)          AS valor_multas_pendentes,
       COALESCE(a.qtd, 0)            AS emprestimos_atrasados,
       COALESCE(a.maior_atraso, 0)   AS maior_atraso_dias,
       COALESCE(a.projetada, 0)      AS multa_projetada,
       COALESCE(m.valor, 0) + COALESCE(a.projetada, 0) AS divida_total
  FROM devedores d
  JOIN usuario u      ON u.id_usuario = d.id_usuario
  JOIN tipo_usuario t ON t.id_tipo    = u.id_tipo
  JOIN curso c        ON c.id_curso   = u.id_curso
  LEFT JOIN multas  m ON m.id_usuario = u.id_usuario
  LEFT JOIN atrasos a ON a.id_usuario = u.id_usuario;

CREATE VIEW vw_alunos_com_pendencias AS
SELECT * FROM vw_usuarios_com_pendencias WHERE tipo = 'ALUNO' ORDER BY divida_total DESC;

-- Situação do acervo por obra
CREATE VIEW vw_disponibilidade_acervo AS
SELECT l.id_livro, l.isbn, l.titulo,
       COUNT(x.id_exemplar)                                    AS total_exemplares,
       SUM(x.status = 'disponivel')                            AS disponiveis,
       SUM(x.status = 'emprestado')                            AS emprestados,
       SUM(x.status = 'reservado')                             AS reservados,
       SUM(x.status IN ('manutencao','perdido'))               AS fora_de_circulacao,
       (SELECT COUNT(*) FROM reserva r
         WHERE r.id_livro = l.id_livro AND r.status = 'ativa') AS fila_reservas
  FROM livro l
  LEFT JOIN exemplar x ON x.id_livro = l.id_livro
 GROUP BY l.id_livro, l.isbn, l.titulo;

-- Multas por curso (arrecadação x inadimplência)
CREATE VIEW vw_multas_por_curso AS
SELECT c.nome AS curso,
       COUNT(*)                                                   AS qtd_multas,
       ROUND(SUM(m.valor), 2)                                     AS valor_total,
       ROUND(SUM(CASE WHEN m.status = 'paga'     THEN m.valor END), 2) AS valor_pago,
       ROUND(SUM(CASE WHEN m.status = 'pendente' THEN m.valor END), 2) AS valor_pendente,
       ROUND(AVG(m.dias_atraso), 1)                               AS media_dias_atraso
  FROM multa m
  JOIN emprestimo e ON e.id_emprestimo = m.id_emprestimo
  JOIN usuario u    ON u.id_usuario    = e.id_usuario
  JOIN curso c      ON c.id_curso      = u.id_curso
 GROUP BY c.nome
 ORDER BY valor_total DESC;
