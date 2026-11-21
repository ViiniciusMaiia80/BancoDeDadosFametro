-- =====================================================================
-- 04b_remover_indices.sql  -  volta ao estado "SEM índices de performance"
-- (usado apenas para o comparativo antes/depois do relatório).
-- Mantém todas as constraints e índices de integridade do DDL.
-- =====================================================================
DROP TRIGGER IF EXISTS trg_livro_fts_ai;  DROP TRIGGER IF EXISTS trg_livro_fts_ad;
DROP TRIGGER IF EXISTS trg_livro_fts_au;  DROP TRIGGER IF EXISTS trg_autor_fts_ai;
DROP TRIGGER IF EXISTS trg_autor_fts_ad;  DROP TRIGGER IF EXISTS trg_autor_fts_au;
DROP TABLE IF EXISTS livro_fts;
DROP TABLE IF EXISTS autor_fts;
DROP INDEX IF EXISTS ux_livro_isbn;
DROP INDEX IF EXISTS idx_livro_titulo;
DROP INDEX IF EXISTS idx_autor_nome;
DROP INDEX IF EXISTS idx_livro_autor_autor;
DROP INDEX IF EXISTS idx_livro_categoria;
DROP INDEX IF EXISTS idx_livro_editora;
DROP INDEX IF EXISTS idx_exemplar_livro_status;
DROP INDEX IF EXISTS idx_usuario_curso;
DROP INDEX IF EXISTS idx_usuario_nome;
DROP INDEX IF EXISTS idx_emprestimo_exemplar;
DROP INDEX IF EXISTS idx_emprestimo_usuario;
DROP INDEX IF EXISTS idx_emprestimo_data;
DROP INDEX IF EXISTS idx_reserva_livro_status;
DROP INDEX IF EXISTS idx_reserva_usuario;
DROP INDEX IF EXISTS idx_multa_pendente;
DROP TABLE IF EXISTS sqlite_stat1;
