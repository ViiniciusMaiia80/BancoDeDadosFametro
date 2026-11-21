-- =====================================================================
-- BIBLIOTECA FAMETRO - 04_indices.sql
-- Índices de PERFORMANCE (busca por título, autor e ISBN + chaves
-- estrangeiras + consultas gerenciais). Execute após 01, 02 e 03.
-- Para reverter (comparação antes/depois): 04b_remover_indices.sql
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---- ISBN: busca exata + garantia de unicidade ------------------------
CREATE UNIQUE INDEX IF NOT EXISTS ux_livro_isbn ON livro(isbn);

-- ---- TÍTULO: busca por prefixo (LIKE 'texto%') sem diferenciar maiúsculas
CREATE INDEX IF NOT EXISTS idx_livro_titulo ON livro(titulo COLLATE NOCASE);

-- ---- AUTOR: busca por nome e navegação autor -> livros ----------------
CREATE INDEX IF NOT EXISTS idx_autor_nome        ON autor(nome COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_livro_autor_autor ON livro_autor(id_autor, id_livro);

-- ---- Chaves estrangeiras / filtros frequentes -------------------------
CREATE INDEX IF NOT EXISTS idx_livro_categoria      ON livro(id_categoria);
CREATE INDEX IF NOT EXISTS idx_livro_editora        ON livro(id_editora);
CREATE INDEX IF NOT EXISTS idx_exemplar_livro_status ON exemplar(id_livro, status);
CREATE INDEX IF NOT EXISTS idx_usuario_curso        ON usuario(id_curso);
CREATE INDEX IF NOT EXISTS idx_usuario_nome         ON usuario(nome COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_emprestimo_exemplar  ON emprestimo(id_exemplar);
-- índice de COBERTURA (id_exemplar incluído): relatórios por usuário/curso não precisam
-- voltar à tabela de 500 mil linhas (medido: relatório por curso 1,7 s -> 1,1 s)
CREATE INDEX IF NOT EXISTS idx_emprestimo_usuario   ON emprestimo(id_usuario, data_devolucao, id_exemplar);
CREATE INDEX IF NOT EXISTS idx_emprestimo_data      ON emprestimo(data_emprestimo);
CREATE INDEX IF NOT EXISTS idx_reserva_livro_status ON reserva(id_livro, status);
CREATE INDEX IF NOT EXISTS idx_reserva_usuario      ON reserva(id_usuario);

-- ---- Índice PARCIAL (pequeno: só as multas pendentes) -------------------
-- Obs.: para empréstimos "em aberto" não é preciso novo índice: o índice parcial
-- único ux_emprestimo_aberto_exemplar (01_ddl.sql) já cobre exatamente essas linhas.
CREATE INDEX IF NOT EXISTS idx_multa_pendente
    ON multa(id_emprestimo) WHERE status = 'pendente';

-- ---- BUSCA TEXTUAL (FTS5): palavra em qualquer posição do título/autor -
CREATE VIRTUAL TABLE IF NOT EXISTS livro_fts USING fts5(
    titulo, content='livro', content_rowid='id_livro',
    tokenize = 'unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS autor_fts USING fts5(
    nome, content='autor', content_rowid='id_autor',
    tokenize = 'unicode61 remove_diacritics 2');

CREATE TRIGGER IF NOT EXISTS trg_livro_fts_ai AFTER INSERT ON livro BEGIN
    INSERT INTO livro_fts(rowid, titulo) VALUES (NEW.id_livro, NEW.titulo);
END;
CREATE TRIGGER IF NOT EXISTS trg_livro_fts_ad AFTER DELETE ON livro BEGIN
    INSERT INTO livro_fts(livro_fts, rowid, titulo) VALUES ('delete', OLD.id_livro, OLD.titulo);
END;
CREATE TRIGGER IF NOT EXISTS trg_livro_fts_au AFTER UPDATE OF titulo ON livro BEGIN
    INSERT INTO livro_fts(livro_fts, rowid, titulo) VALUES ('delete', OLD.id_livro, OLD.titulo);
    INSERT INTO livro_fts(rowid, titulo) VALUES (NEW.id_livro, NEW.titulo);
END;
CREATE TRIGGER IF NOT EXISTS trg_autor_fts_ai AFTER INSERT ON autor BEGIN
    INSERT INTO autor_fts(rowid, nome) VALUES (NEW.id_autor, NEW.nome);
END;
CREATE TRIGGER IF NOT EXISTS trg_autor_fts_ad AFTER DELETE ON autor BEGIN
    INSERT INTO autor_fts(autor_fts, rowid, nome) VALUES ('delete', OLD.id_autor, OLD.nome);
END;
CREATE TRIGGER IF NOT EXISTS trg_autor_fts_au AFTER UPDATE OF nome ON autor BEGIN
    INSERT INTO autor_fts(autor_fts, rowid, nome) VALUES ('delete', OLD.id_autor, OLD.nome);
    INSERT INTO autor_fts(rowid, nome) VALUES (NEW.id_autor, NEW.nome);
END;

-- carga inicial dos índices textuais com os dados já existentes
INSERT INTO livro_fts(livro_fts) VALUES ('rebuild');
INSERT INTO autor_fts(autor_fts) VALUES ('rebuild');

-- atualiza estatísticas para o otimizador escolher bem os planos
ANALYZE;
