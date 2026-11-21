-- =====================================================================
-- BIBLIOTECA FAMETRO - 01_ddl.sql
-- Criação do esquema relacional (3FN) com todas as constraints.
-- SGBD: SQLite 3.35+  |  Ordem de execução: 01 -> 02 -> 03 -> 04 -> 05
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS multa;
DROP TABLE IF EXISTS renovacao;
DROP TABLE IF EXISTS reserva;
DROP TABLE IF EXISTS emprestimo;
DROP TABLE IF EXISTS exemplar;
DROP TABLE IF EXISTS livro_autor;
DROP TABLE IF EXISTS livro;
DROP TABLE IF EXISTS autor;
DROP TABLE IF EXISTS editora;
DROP TABLE IF EXISTS categoria;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS tipo_usuario;
DROP TABLE IF EXISTS curso;

-- ---------------------------------------------------------------------
-- Tabelas de domínio
-- ---------------------------------------------------------------------
CREATE TABLE curso (
    id_curso   INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL UNIQUE,
    sigla      TEXT NOT NULL UNIQUE CHECK (length(sigla) BETWEEN 2 AND 10)
);

-- Regras de empréstimo dependem do TIPO do usuário (e não do usuário):
-- manter essas colunas aqui evita dependência transitiva (3FN).
CREATE TABLE tipo_usuario (
    id_tipo            INTEGER PRIMARY KEY,
    nome               TEXT    NOT NULL UNIQUE,          -- 'ALUNO', 'DOCENTE'
    limite_emprestimos INTEGER NOT NULL CHECK (limite_emprestimos > 0),
    prazo_dias         INTEGER NOT NULL CHECK (prazo_dias > 0),
    max_renovacoes     INTEGER NOT NULL CHECK (max_renovacoes >= 0),
    valor_multa_dia    NUMERIC NOT NULL CHECK (valor_multa_dia >= 0)
);

CREATE TABLE usuario (
    id_usuario    INTEGER PRIMARY KEY,
    matricula     TEXT    NOT NULL UNIQUE,
    nome          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    id_tipo       INTEGER NOT NULL REFERENCES tipo_usuario(id_tipo),
    id_curso      INTEGER NOT NULL REFERENCES curso(id_curso),
    ativo         INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0,1)),
    data_cadastro TEXT    NOT NULL DEFAULT (date('now'))
);

CREATE TABLE categoria (
    id_categoria INTEGER PRIMARY KEY,
    nome         TEXT NOT NULL UNIQUE
);

CREATE TABLE editora (
    id_editora INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL UNIQUE
);

CREATE TABLE autor (
    id_autor INTEGER PRIMARY KEY,
    nome     TEXT NOT NULL
);

-- ---------------------------------------------------------------------
-- Acervo
-- 'livro' = obra (título/ISBN);  'exemplar' = cópia física emprestável.
-- A unicidade do ISBN é garantida pelo UNIQUE INDEX ux_livro_isbn em
-- 04_indices.sql (executar sempre após o DDL e a carga).
-- ---------------------------------------------------------------------
CREATE TABLE livro (
    id_livro        INTEGER PRIMARY KEY,
    isbn            TEXT    NOT NULL CHECK (length(isbn) = 13 AND isbn NOT GLOB '*[^0-9]*'),
    titulo          TEXT    NOT NULL,
    ano_publicacao  INTEGER CHECK (ano_publicacao BETWEEN 1500 AND 2100),
    edicao          INTEGER NOT NULL DEFAULT 1 CHECK (edicao > 0),
    id_editora      INTEGER NOT NULL REFERENCES editora(id_editora),
    id_categoria    INTEGER NOT NULL REFERENCES categoria(id_categoria)
);

CREATE TABLE livro_autor (            -- relação N:N livro x autor
    id_livro INTEGER NOT NULL REFERENCES livro(id_livro) ON DELETE CASCADE,
    id_autor INTEGER NOT NULL REFERENCES autor(id_autor),
    ordem    INTEGER NOT NULL DEFAULT 1 CHECK (ordem > 0),
    PRIMARY KEY (id_livro, id_autor)
);

CREATE TABLE exemplar (
    id_exemplar     INTEGER PRIMARY KEY,
    id_livro        INTEGER NOT NULL REFERENCES livro(id_livro),
    patrimonio      TEXT    NOT NULL UNIQUE,
    status          TEXT    NOT NULL DEFAULT 'disponivel'
                    CHECK (status IN ('disponivel','emprestado','reservado','manutencao','perdido')),
    data_aquisicao  TEXT    NOT NULL DEFAULT (date('now'))
);

-- ---------------------------------------------------------------------
-- Movimentação
-- ---------------------------------------------------------------------
CREATE TABLE emprestimo (
    id_emprestimo   INTEGER PRIMARY KEY,
    id_exemplar     INTEGER NOT NULL REFERENCES exemplar(id_exemplar),
    id_usuario      INTEGER NOT NULL REFERENCES usuario(id_usuario),
    data_emprestimo TEXT    NOT NULL DEFAULT (date('now')),
    data_prevista   TEXT,                      -- preenchida por trigger (prazo do tipo de usuário)
    data_devolucao  TEXT,                      -- NULL = empréstimo em aberto
    CHECK (data_prevista  IS NULL OR data_prevista  >= data_emprestimo),
    CHECK (data_devolucao IS NULL OR data_devolucao >= data_emprestimo)
);

-- O número de renovações NÃO é armazenado em emprestimo (seria dado derivado).
-- UNIQUE(id_emprestimo, numero) impede duas renovações simultâneas com o mesmo número.
CREATE TABLE renovacao (
    id_renovacao        INTEGER PRIMARY KEY,
    id_emprestimo       INTEGER NOT NULL REFERENCES emprestimo(id_emprestimo) ON DELETE CASCADE,
    numero              INTEGER NOT NULL CHECK (numero > 0),
    data_renovacao      TEXT    NOT NULL DEFAULT (date('now')),
    nova_data_prevista  TEXT,                  -- preenchida por trigger
    UNIQUE (id_emprestimo, numero)
);

CREATE TABLE reserva (
    id_reserva    INTEGER PRIMARY KEY,
    id_livro      INTEGER NOT NULL REFERENCES livro(id_livro),
    id_usuario    INTEGER NOT NULL REFERENCES usuario(id_usuario),
    data_reserva  TEXT    NOT NULL DEFAULT (date('now')),
    status        TEXT    NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','atendida','cancelada'))
);

CREATE TABLE multa (
    id_multa        INTEGER PRIMARY KEY,
    id_emprestimo   INTEGER NOT NULL UNIQUE REFERENCES emprestimo(id_emprestimo),  -- 1 multa por empréstimo
    dias_atraso     INTEGER NOT NULL CHECK (dias_atraso > 0),
    valor           NUMERIC NOT NULL CHECK (valor >= 0),
    status          TEXT    NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','paga','cancelada')),
    data_geracao    TEXT    NOT NULL DEFAULT (date('now')),
    data_pagamento  TEXT
);

-- ---------------------------------------------------------------------
-- Índices de INTEGRIDADE (regras de negócio; não são de performance)
-- ---------------------------------------------------------------------
-- Um exemplar só pode ter UM empréstimo em aberto (evita empréstimos simultâneos)
CREATE UNIQUE INDEX ux_emprestimo_aberto_exemplar
    ON emprestimo(id_exemplar) WHERE data_devolucao IS NULL;
-- Um usuário só pode ter UMA reserva ativa por livro
CREATE UNIQUE INDEX ux_reserva_ativa_usuario_livro
    ON reserva(id_livro, id_usuario) WHERE status = 'ativa';
