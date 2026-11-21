-- =====================================================================
-- BIBLIOTECA FAMETRO - 06_consultas.sql   (DQL: consultas operacionais e analíticas)
-- Parâmetros de exemplo estão literais; troque pelos valores desejados.
-- =====================================================================

-- Q1. Busca por ISBN (exata)  -> usa ux_livro_isbn
SELECT l.id_livro, l.titulo, l.ano_publicacao, e.nome AS editora
  FROM livro l JOIN editora e ON e.id_editora = l.id_editora
 WHERE l.isbn = (SELECT isbn FROM livro WHERE id_livro = 10);

-- Q2. Busca por título - começa com...  -> usa idx_livro_titulo
SELECT id_livro, titulo, ano_publicacao
  FROM livro
 WHERE titulo LIKE 'Curso de Direito%'
 ORDER BY titulo;

-- Q3. Busca por palavra em qualquer parte do título (sem acento)  -> FTS5
SELECT l.id_livro, l.titulo
  FROM livro_fts f JOIN livro l ON l.id_livro = f.rowid
 WHERE livro_fts MATCH 'banco dados'
 ORDER BY rank;

-- Q4. Livros de um autor (busca por nome)  -> usa idx_autor_nome + idx_livro_autor_autor
SELECT a.nome AS autor, l.titulo, l.ano_publicacao
  FROM autor a
  JOIN livro_autor la ON la.id_autor = a.id_autor
  JOIN livro l        ON l.id_livro  = la.id_livro
 WHERE a.nome LIKE 'Idalberto%'
 ORDER BY l.ano_publicacao DESC;

-- Q5. Catálogo com disponibilidade (view)
SELECT titulo, total_exemplares, disponiveis, emprestados, reservados, fila_reservas
  FROM vw_disponibilidade_acervo
 WHERE titulo LIKE '%Banco de Dados%' OR titulo LIKE '%Engenharia de Software%';

-- Q6. Livros indisponíveis hoje com fila de reserva (demanda reprimida)
SELECT titulo, total_exemplares, emprestados, fila_reservas
  FROM vw_disponibilidade_acervo
 WHERE disponiveis = 0 AND fila_reservas > 0
 ORDER BY fila_reservas DESC, titulo;

-- Q7. Top 10 livros mais emprestados (geral)
SELECT l.titulo, COUNT(*) AS emprestimos
  FROM emprestimo e
  JOIN exemplar x ON x.id_exemplar = e.id_exemplar
  JOIN livro l    ON l.id_livro = x.id_livro
 GROUP BY l.id_livro
 ORDER BY emprestimos DESC
 LIMIT 10;

-- Q8. Livros mais emprestados por curso (view - top 3 de cada)
SELECT * FROM vw_livros_mais_emprestados_por_curso WHERE posicao <= 3;

-- Q9. Autores mais lidos
SELECT a.nome, COUNT(*) AS emprestimos
  FROM emprestimo e
  JOIN exemplar x     ON x.id_exemplar = e.id_exemplar
  JOIN livro_autor la ON la.id_livro = x.id_livro
  JOIN autor a        ON a.id_autor = la.id_autor
 GROUP BY a.id_autor
 ORDER BY emprestimos DESC
 LIMIT 10;

-- Q10. Alunos com pendências (view)
SELECT matricula, nome, curso, multas_pendentes, valor_multas_pendentes,
       emprestimos_atrasados, divida_total
  FROM vw_alunos_com_pendencias
 LIMIT 15;

-- Q11. Empréstimos atrasados hoje, do mais atrasado ao menos
SELECT usuario, curso, titulo, data_prevista, dias_atraso, multa_projetada
  FROM vw_emprestimos_atrasados
 ORDER BY dias_atraso DESC;

-- Q12. Empréstimos por mês (últimos 12 meses) e % devolvidos com atraso
SELECT strftime('%Y-%m', e.data_emprestimo) AS mes,
       COUNT(*) AS emprestimos,
       ROUND(100.0 * SUM(e.data_devolucao > e.data_prevista) / COUNT(e.data_devolucao), 1) AS pct_atraso
  FROM emprestimo e
 WHERE e.data_emprestimo >= date('now', 'start of month', '-11 months')
 GROUP BY mes
 ORDER BY mes;

-- Q13. Multas por curso (view)
SELECT * FROM vw_multas_por_curso;

-- Q14. Taxa de ocupação do acervo por categoria
SELECT c.nome AS categoria,
       COUNT(x.id_exemplar) AS exemplares,
       SUM(x.status IN ('emprestado','reservado')) AS em_uso,
       ROUND(100.0 * SUM(x.status IN ('emprestado','reservado')) / COUNT(x.id_exemplar), 1) AS pct_ocupacao
  FROM categoria c
  JOIN livro l    ON l.id_categoria = c.id_categoria
  JOIN exemplar x ON x.id_livro = l.id_livro
 GROUP BY c.id_categoria
 ORDER BY pct_ocupacao DESC;

-- Q15. Acervo ocioso: obras sem nenhum empréstimo nos últimos 12 meses
SELECT l.titulo, COUNT(x.id_exemplar) AS exemplares
  FROM livro l
  JOIN exemplar x ON x.id_livro = l.id_livro
 WHERE NOT EXISTS (SELECT 1 FROM emprestimo e
                    JOIN exemplar x2 ON x2.id_exemplar = e.id_exemplar
                   WHERE x2.id_livro = l.id_livro
                     AND e.data_emprestimo >= date('now', '-12 months'))
 GROUP BY l.id_livro
 ORDER BY exemplares DESC, l.titulo;

-- Q16. Usuários mais assíduos (top 10) com tipo e curso
SELECT u.nome, t.nome AS tipo, c.sigla AS curso, COUNT(*) AS emprestimos
  FROM emprestimo e
  JOIN usuario u      ON u.id_usuario = e.id_usuario
  JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
  JOIN curso c        ON c.id_curso = u.id_curso
 GROUP BY u.id_usuario
 ORDER BY emprestimos DESC
 LIMIT 10;

-- Q17. Renovações por tipo de usuário (uso do recurso)
SELECT t.nome AS tipo, COUNT(DISTINCT e.id_emprestimo) AS emprestimos_com_renovacao, COUNT(r.id_renovacao) AS renovacoes
  FROM renovacao r
  JOIN emprestimo e   ON e.id_emprestimo = r.id_emprestimo
  JOIN usuario u      ON u.id_usuario = e.id_usuario
  JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
 GROUP BY t.nome;

-- Q18. Operações do dia a dia (modelos de uso das triggers) - NÃO executar em lote:
--   INSERT INTO emprestimo(id_exemplar, id_usuario) VALUES (:exemplar, :usuario);
--   UPDATE emprestimo SET data_devolucao = date('now') WHERE id_emprestimo = :id;
--   INSERT INTO renovacao(id_emprestimo, numero)
--          SELECT :id, 1 + COUNT(*) FROM renovacao WHERE id_emprestimo = :id;
--   INSERT INTO reserva(id_livro, id_usuario) VALUES (:livro, :usuario);
--   UPDATE multa SET status = 'paga' WHERE id_multa = :id;
