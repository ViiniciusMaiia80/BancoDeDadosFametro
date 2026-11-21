-- =====================================================================
-- BIBLIOTECA FAMETRO - 02_triggers.sql
-- Regras de negócio automatizadas.
--
-- Como o SQLite não possui Stored Procedures, toda a automação é feita
-- por TRIGGERS. Uso no dia a dia (nenhuma "procedure" é necessária):
--   Emprestar : INSERT INTO emprestimo(id_exemplar, id_usuario) VALUES (..,..);
--   Devolver  : UPDATE emprestimo SET data_devolucao = date('now') WHERE id_emprestimo = ..;
--   Renovar   : INSERT INTO renovacao(id_emprestimo, numero) VALUES (.., <n+1>);
--   Reservar  : INSERT INTO reserva(id_livro, id_usuario) VALUES (..,..);
--   Pagar     : UPDATE multa SET status = 'paga' WHERE id_multa = ..;
--
-- Invariante do acervo mantida pelas triggers:
--   nº de exemplares 'reservado' de um livro <= nº de reservas 'ativa' do livro
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP TRIGGER IF EXISTS trg_emp_bi_valida;
DROP TRIGGER IF EXISTS trg_emp_ai_prazo;
DROP TRIGGER IF EXISTS trg_emp_ai_abertura;
DROP TRIGGER IF EXISTS trg_emp_ai_multa_historica;
DROP TRIGGER IF EXISTS trg_emp_bu_encerrado;
DROP TRIGGER IF EXISTS trg_emp_au_devolucao;
DROP TRIGGER IF EXISTS trg_ren_bi_valida;
DROP TRIGGER IF EXISTS trg_ren_ai_aplica;
DROP TRIGGER IF EXISTS trg_res_bi_valida;
DROP TRIGGER IF EXISTS trg_res_bu_status;
DROP TRIGGER IF EXISTS trg_res_au_libera;
DROP TRIGGER IF EXISTS trg_mul_au_pagamento;
DROP TRIGGER IF EXISTS trg_exe_bu_status;

-- ---------------------------------------------------------------------
-- EMPRÉSTIMO (abertura): valida todas as regras antes de gravar
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_emp_bi_valida
BEFORE INSERT ON emprestimo
WHEN NEW.data_devolucao IS NULL            -- só valida empréstimos novos (abertos)
BEGIN
    SELECT RAISE(ABORT, 'Usuario inativo')
     WHERE (SELECT ativo FROM usuario WHERE id_usuario = NEW.id_usuario) = 0;

    SELECT RAISE(ABORT, 'Exemplar indisponivel para emprestimo')
     WHERE (SELECT status FROM exemplar WHERE id_exemplar = NEW.id_exemplar)
           NOT IN ('disponivel', 'reservado');

    SELECT RAISE(ABORT, 'Exemplar reservado para outro usuario')
     WHERE (SELECT status FROM exemplar WHERE id_exemplar = NEW.id_exemplar) = 'reservado'
       AND NOT EXISTS (SELECT 1
                         FROM reserva r
                         JOIN exemplar e ON e.id_livro = r.id_livro
                        WHERE e.id_exemplar = NEW.id_exemplar
                          AND r.id_usuario  = NEW.id_usuario
                          AND r.status = 'ativa');

    SELECT RAISE(ABORT, 'Limite de emprestimos simultaneos atingido')
     WHERE (SELECT count(*) FROM emprestimo
             WHERE id_usuario = NEW.id_usuario AND data_devolucao IS NULL)
        >= (SELECT t.limite_emprestimos
              FROM usuario u JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
             WHERE u.id_usuario = NEW.id_usuario);

    SELECT RAISE(ABORT, 'Usuario com multa pendente')
     WHERE EXISTS (SELECT 1 FROM multa m
                     JOIN emprestimo e ON e.id_emprestimo = m.id_emprestimo
                    WHERE e.id_usuario = NEW.id_usuario AND m.status = 'pendente');

    SELECT RAISE(ABORT, 'Usuario com emprestimo em atraso')
     WHERE EXISTS (SELECT 1 FROM emprestimo
                    WHERE id_usuario = NEW.id_usuario
                      AND data_devolucao IS NULL
                      AND data_prevista < NEW.data_emprestimo);
END;

-- Define o prazo de devolução conforme o tipo de usuário
CREATE TRIGGER trg_emp_ai_prazo
AFTER INSERT ON emprestimo
WHEN NEW.data_prevista IS NULL
BEGIN
    UPDATE emprestimo
       SET data_prevista = date(NEW.data_emprestimo,
              '+' || (SELECT t.prazo_dias
                        FROM usuario u JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
                       WHERE u.id_usuario = NEW.id_usuario) || ' days')
     WHERE id_emprestimo = NEW.id_emprestimo;
END;

-- Empréstimo aberto: exemplar -> 'emprestado'; reserva do usuário -> 'atendida'
CREATE TRIGGER trg_emp_ai_abertura
AFTER INSERT ON emprestimo
WHEN NEW.data_devolucao IS NULL
BEGIN
    UPDATE exemplar SET status = 'emprestado' WHERE id_exemplar = NEW.id_exemplar;

    UPDATE reserva
       SET status = 'atendida'
     WHERE status = 'ativa'
       AND id_usuario = NEW.id_usuario
       AND id_livro = (SELECT id_livro FROM exemplar WHERE id_exemplar = NEW.id_exemplar);
END;

-- Carga histórica: empréstimo já inserido como devolvido também gera multa
CREATE TRIGGER trg_emp_ai_multa_historica
AFTER INSERT ON emprestimo
WHEN NEW.data_devolucao IS NOT NULL
BEGIN
    INSERT INTO multa (id_emprestimo, dias_atraso, valor, data_geracao)
    SELECT NEW.id_emprestimo, x.dias, x.dias * t.valor_multa_dia, NEW.data_devolucao
      FROM (SELECT CAST(julianday(NEW.data_devolucao) -
                        julianday(COALESCE(NEW.data_prevista,
                            date(NEW.data_emprestimo, '+' || (SELECT t2.prazo_dias
                                   FROM usuario u2 JOIN tipo_usuario t2 ON t2.id_tipo = u2.id_tipo
                                  WHERE u2.id_usuario = NEW.id_usuario) || ' days'))) AS INTEGER) AS dias) x
      JOIN usuario u      ON u.id_usuario = NEW.id_usuario
      JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
     WHERE x.dias > 0;
END;

-- Empréstimo encerrado não pode ser reaberto nem ter a devolução alterada
CREATE TRIGGER trg_emp_bu_encerrado
BEFORE UPDATE ON emprestimo
WHEN OLD.data_devolucao IS NOT NULL AND NEW.data_devolucao IS NOT OLD.data_devolucao
BEGIN
    SELECT RAISE(ABORT, 'Emprestimo ja encerrado: devolucao nao pode ser alterada');
END;

-- ---------------------------------------------------------------------
-- DEVOLUÇÃO: calcula multa automaticamente e libera o exemplar
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_emp_au_devolucao
AFTER UPDATE OF data_devolucao ON emprestimo
WHEN OLD.data_devolucao IS NULL AND NEW.data_devolucao IS NOT NULL
BEGIN
    -- multa = dias de atraso x valor diário do tipo de usuário
    INSERT INTO multa (id_emprestimo, dias_atraso, valor, data_geracao)
    SELECT NEW.id_emprestimo, x.dias, x.dias * t.valor_multa_dia, NEW.data_devolucao
      FROM (SELECT CAST(julianday(NEW.data_devolucao) - julianday(NEW.data_prevista) AS INTEGER) AS dias) x
      JOIN usuario u      ON u.id_usuario = NEW.id_usuario
      JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
     WHERE x.dias > 0;

    -- exemplar volta ao acervo: 'reservado' se houver fila de reservas, senão 'disponivel'
    UPDATE exemplar
       SET status = CASE
             WHEN (SELECT count(*) FROM reserva r
                    WHERE r.id_livro = exemplar.id_livro AND r.status = 'ativa')
                > (SELECT count(*) FROM exemplar e2
                    WHERE e2.id_livro = exemplar.id_livro AND e2.status = 'reservado')
             THEN 'reservado' ELSE 'disponivel' END
     WHERE id_exemplar = NEW.id_exemplar
       AND status = 'emprestado';
END;

-- ---------------------------------------------------------------------
-- RENOVAÇÃO
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_ren_bi_valida
BEFORE INSERT ON renovacao
BEGIN
    SELECT RAISE(ABORT, 'Emprestimo inexistente ou ja encerrado')
     WHERE NOT EXISTS (SELECT 1 FROM emprestimo
                        WHERE id_emprestimo = NEW.id_emprestimo AND data_devolucao IS NULL);

    -- impede duas renovações "simultâneas" com o mesmo número (corrida entre sessões)
    SELECT RAISE(ABORT, 'Numero de renovacao invalido ou renovacao concorrente')
     WHERE NEW.numero <> 1 + (SELECT count(*) FROM renovacao WHERE id_emprestimo = NEW.id_emprestimo);

    SELECT RAISE(ABORT, 'Limite de renovacoes atingido')
     WHERE NEW.numero > (SELECT t.max_renovacoes
                           FROM emprestimo e
                           JOIN usuario u      ON u.id_usuario = e.id_usuario
                           JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
                          WHERE e.id_emprestimo = NEW.id_emprestimo);

    SELECT RAISE(ABORT, 'Emprestimo em atraso nao pode ser renovado')
     WHERE (SELECT data_prevista FROM emprestimo WHERE id_emprestimo = NEW.id_emprestimo)
           < NEW.data_renovacao;

    SELECT RAISE(ABORT, 'Livro reservado por outro usuario')
     WHERE EXISTS (SELECT 1
                     FROM emprestimo em
                     JOIN exemplar ex ON ex.id_exemplar = em.id_exemplar
                     JOIN reserva  rs ON rs.id_livro = ex.id_livro AND rs.status = 'ativa'
                    WHERE em.id_emprestimo = NEW.id_emprestimo
                      AND rs.id_usuario <> em.id_usuario);

    SELECT RAISE(ABORT, 'Usuario com multa pendente')
     WHERE EXISTS (SELECT 1
                     FROM emprestimo em
                     JOIN emprestimo e2 ON e2.id_usuario = em.id_usuario
                     JOIN multa m ON m.id_emprestimo = e2.id_emprestimo AND m.status = 'pendente'
                    WHERE em.id_emprestimo = NEW.id_emprestimo);
END;

CREATE TRIGGER trg_ren_ai_aplica
AFTER INSERT ON renovacao
BEGIN
    UPDATE emprestimo
       SET data_prevista = date(NEW.data_renovacao,
              '+' || (SELECT t.prazo_dias
                        FROM usuario u JOIN tipo_usuario t ON t.id_tipo = u.id_tipo
                       WHERE u.id_usuario = emprestimo.id_usuario) || ' days')
     WHERE id_emprestimo = NEW.id_emprestimo;

    UPDATE renovacao
       SET nova_data_prevista = (SELECT data_prevista FROM emprestimo
                                  WHERE id_emprestimo = NEW.id_emprestimo)
     WHERE id_renovacao = NEW.id_renovacao;
END;

-- ---------------------------------------------------------------------
-- RESERVA
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_res_bi_valida
BEFORE INSERT ON reserva
WHEN NEW.status = 'ativa'
BEGIN
    SELECT RAISE(ABORT, 'Usuario inativo')
     WHERE (SELECT ativo FROM usuario WHERE id_usuario = NEW.id_usuario) = 0;

    SELECT RAISE(ABORT, 'Ha exemplar disponivel: realize o emprestimo')
     WHERE EXISTS (SELECT 1 FROM exemplar
                    WHERE id_livro = NEW.id_livro AND status = 'disponivel');

    SELECT RAISE(ABORT, 'Usuario ja esta com este livro emprestado')
     WHERE EXISTS (SELECT 1 FROM emprestimo em
                     JOIN exemplar ex ON ex.id_exemplar = em.id_exemplar
                    WHERE em.id_usuario = NEW.id_usuario
                      AND em.data_devolucao IS NULL
                      AND ex.id_livro = NEW.id_livro);
END;

CREATE TRIGGER trg_res_bu_status
BEFORE UPDATE OF status ON reserva
WHEN OLD.status <> 'ativa' AND NEW.status <> OLD.status
BEGIN
    SELECT RAISE(ABORT, 'Reserva ja finalizada');
END;

-- Reserva atendida/cancelada: libera exemplar retido se sobrar exemplar 'reservado'
CREATE TRIGGER trg_res_au_libera
AFTER UPDATE OF status ON reserva
WHEN OLD.status = 'ativa' AND NEW.status IN ('atendida', 'cancelada')
BEGIN
    UPDATE exemplar
       SET status = 'disponivel'
     WHERE id_exemplar = (SELECT id_exemplar FROM exemplar
                           WHERE id_livro = NEW.id_livro AND status = 'reservado'
                           ORDER BY id_exemplar LIMIT 1)
       AND (SELECT count(*) FROM reserva
             WHERE id_livro = NEW.id_livro AND status = 'ativa')
         < (SELECT count(*) FROM exemplar
             WHERE id_livro = NEW.id_livro AND status = 'reservado');
END;

-- ---------------------------------------------------------------------
-- MULTA: registra a data de pagamento
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_mul_au_pagamento
AFTER UPDATE OF status ON multa
WHEN NEW.status = 'paga' AND NEW.data_pagamento IS NULL
BEGIN
    UPDATE multa SET data_pagamento = date('now') WHERE id_multa = NEW.id_multa;
END;

-- ---------------------------------------------------------------------
-- EXEMPLAR: status coerente com os empréstimos em aberto
-- ---------------------------------------------------------------------
CREATE TRIGGER trg_exe_bu_status
BEFORE UPDATE OF status ON exemplar
WHEN NEW.status <> OLD.status
BEGIN
    SELECT RAISE(ABORT, 'Exemplar com emprestimo em aberto: registre a devolucao')
     WHERE OLD.status = 'emprestado'
       AND NEW.status <> 'emprestado'
       AND EXISTS (SELECT 1 FROM emprestimo
                    WHERE id_exemplar = OLD.id_exemplar AND data_devolucao IS NULL);

    SELECT RAISE(ABORT, 'Status emprestado so pode ser definido por um emprestimo')
     WHERE NEW.status = 'emprestado'
       AND NOT EXISTS (SELECT 1 FROM emprestimo
                        WHERE id_exemplar = OLD.id_exemplar AND data_devolucao IS NULL);
END;
