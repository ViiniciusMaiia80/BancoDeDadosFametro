-- =====================================================================
-- BIBLIOTECA FAMETRO - 08_carga_volume.sql
-- Carga SINTÉTICA EM VOLUME, usada somente no comparativo de desempenho.
-- Determinística (hash em vez de random()) => resultados reprodutíveis.
-- Pré-requisito: 01, 02 e 03 executados (SEM os índices de 04).
--
-- Volume gerado:   +20.000 autores | +150.000 livros | ~255.000 exemplares
--                  +30.000 usuários | +3.000 empréstimos em aberto (maioria vencida)
--                  +500.000 empréstimos históricos (~30% devolvidos com atraso -> multas)
-- =====================================================================
PRAGMA foreign_keys = ON;
BEGIN;

-- ---------------------------------------------------------------- autores
INSERT INTO autor (id_autor, nome)
WITH nomes(v) AS (VALUES ('Ana'),('Beatriz'),('Camila'),('Daniela'),('Eduarda'),('Fernanda'),('Gabriela'),
      ('Helena'),('Isabela'),('Joana'),('Karina'),('Larissa'),('Mariana'),('Natália'),('Priscila'),
      ('Rafaela'),('Sofia'),('Taís'),('Vitória'),('Yasmin'),('Adriano'),('Bruno'),('Carlos'),('Davi'),
      ('Eduardo'),('Felipe'),('Gustavo'),('Henrique'),('Igor'),('João'),('Kauã'),('Lucas'),('Matheus'),
      ('Nathan'),('Otávio'),('Pedro'),('Rafael'),('Samuel'),('Thiago'),('Vinícius')),
     sobren(v) AS (VALUES ('Silva'),('Souza'),('Oliveira'),('Santos'),('Pereira'),('Lima'),('Costa'),
      ('Ferreira'),('Rodrigues'),('Almeida'),('Nascimento'),('Araújo'),('Ribeiro'),('Carvalho'),('Gomes'),
      ('Martins'),('Barbosa'),('Rocha'),('Dias'),('Monteiro'),('Cardoso'),('Teixeira'),('Moura'),
      ('Cavalcante'),('Batista')),
     a AS (SELECT n.v AS n1, s1.v AS s1, s2.v AS s2 FROM nomes n, sobren s1, sobren s2)
SELECT 1000 + ROW_NUMBER() OVER (ORDER BY s1, n1, s2), n1 || ' ' || s1 || ' ' || s2
  FROM a
 LIMIT 20000;

-- ----------------------------------------------------------------- livros
INSERT INTO livro (id_livro, isbn, titulo, ano_publicacao, edicao, id_editora, id_categoria)
WITH pref(v) AS (VALUES ('Fundamentos de'),('Introdução à'),('Manual de'),('Tratado de'),('Princípios de'),
      ('Elementos de'),('Curso de'),('Tópicos em'),('Guia Prático de'),('Teoria e Prática de'),
      ('Estudos de'),('Análise de'),('Noções de'),('Compêndio de'),('Lições de'),('Casos de'),
      ('Métodos de'),('Técnicas de'),('Atlas de'),('Dicionário de'),('Fundamentos da'),('Introdução ao'),
      ('Panorama de'),('Visão Geral de'),('Ensaios sobre'),('Questões de'),('Projetos de'),('Gestão de'),
      ('Práticas de'),('Avanços em')),
     assunto(v) AS (VALUES ('Direito Civil'),('Direito Penal'),('Direito Tributário'),('Anatomia Humana'),
      ('Fisiologia'),('Farmacologia'),('Patologia'),('Enfermagem Clínica'),('Saúde Coletiva'),
      ('Psicologia Social'),('Psicologia Clínica'),('Neurociências'),('Estruturas de Concreto'),
      ('Mecânica dos Solos'),('Hidráulica'),('Topografia'),('Termodinâmica'),('Cálculo Diferencial'),
      ('Álgebra Linear'),('Estatística'),('Marketing'),('Finanças Corporativas'),('Contabilidade de Custos'),
      ('Logística'),('Gestão de Pessoas'),('Empreendedorismo'),('Economia Brasileira'),('Banco de Dados'),
      ('Engenharia de Software'),('Redes de Computadores'),('Sistemas Operacionais'),
      ('Inteligência Artificial'),('Estruturas de Dados'),('Segurança da Informação'),('Compiladores'),
      ('Programação Web'),('Periodontia'),('Endodontia'),('Materiais Dentários'),('Radiologia'),
      ('Histologia'),('Bioquímica'),('Microbiologia'),('Imunologia'),('Epidemiologia'),('Bioética'),
      ('Metodologia Científica'),('Literatura Amazônica'),('Língua Portuguesa'),('Sociologia'),
      ('Filosofia do Direito'),('Ciência Política'),('Direito Constitucional'),('Direito do Trabalho'),
      ('Processo Civil'),('Cirurgia Geral'),('Pediatria'),('Ginecologia'),('Ortodontia'),('Genética')),
     compl(v) AS (VALUES ('Aplicada'),('Contemporânea'),('Avançada'),('Básica'),('Ilustrada'),('Comentada'),
      ('em Saúde'),('no Brasil'),('na Prática'),('Moderna'),('Integrada'),('Essencial'),('Clínica'),
      ('Experimental'),('Comparada'),('Crítica'),('Geral'),('Especial'),('Introdutória'),('Resumida')),
     vol(v) AS (VALUES (1),(2),(3),(4),(5)),
     t AS (SELECT p.v || ' ' || a.v || ' ' || c.v || ' - Vol. ' || vol.v AS titulo, vol.v AS vol
             FROM vol, pref p, assunto a, compl c),
     n AS (SELECT titulo, ROW_NUMBER() OVER (ORDER BY vol, titulo) AS i FROM t)
SELECT 1000 + i,
       '9788' || printf('%09d', 100000 + i),            -- 13 dígitos, único
       titulo,
       1990 + (i % 36),
       1 + (i % 5),
       1 + (i % 32),                                    -- editoras 1..32
       1 + (i % 11)                                     -- categorias 1..11
  FROM n
 WHERE i <= 150000;

-- ---------------------------------------------------------- livro x autor
INSERT INTO livro_autor (id_livro, id_autor, ordem)
SELECT l.id_livro,
       1001 + (((l.id_livro - 1000) * 7919) % 20000 + k.c) % 20000,
       k.c + 1
  FROM livro l
  JOIN (SELECT 0 AS c UNION ALL SELECT 1 UNION ALL SELECT 2) k
    ON k.c < 1 + ((l.id_livro - 1000) % 3)
 WHERE l.id_livro > 1000;

-- -------------------------------------------------------------- exemplares
INSERT INTO exemplar (id_exemplar, id_livro, patrimonio, data_aquisicao)
SELECT 1000 + ROW_NUMBER() OVER (ORDER BY l.id_livro, k.c),
       l.id_livro,
       'V' || printf('%08d', 1000 + ROW_NUMBER() OVER (ORDER BY l.id_livro, k.c)),
       date('now', '-' || (30 + (l.id_livro * 31) % 3000) || ' days')
  FROM livro l
  JOIN (SELECT 0 AS c UNION ALL SELECT 1 UNION ALL SELECT 2) k
    ON k.c < 1 + ((l.id_livro - 1000) % 2) + (((l.id_livro - 1000) % 5) = 0)
 WHERE l.id_livro > 1000;

-- --------------------------------------------------------------- usuários
INSERT INTO usuario (id_usuario, matricula, nome, email, id_tipo, id_curso, ativo, data_cadastro)
SELECT 1000 + n,
       'V' || printf('%07d', n),
       'Usuário Sintético ' || n,
       'v' || n || '@alunos.fametro.example',
       CASE WHEN n % 50 = 0 THEN 2 ELSE 1 END,
       1 + (n % 8),
       1,
       date('now', '-' || (60 + n % 1400) || ' days')
  FROM (WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 30000)
        SELECT n FROM s);

-- ----------------------------------------------------------------------
-- 3.000 empréstimos EM ABERTO (passam pelas validações das triggers).
-- Inseridos ANTES do histórico para a validação rodar sobre tabela pequena.
-- Usuários 1001..4000 (sem multas), exemplares 1001..4000, data = 0..29 dias atrás
-- (prazo do aluno = 7 dias => cerca de 3/4 ficam vencidos).
-- ----------------------------------------------------------------------
INSERT INTO emprestimo (id_exemplar, id_usuario, data_emprestimo)
SELECT 1000 + n, 1000 + n, date('now', '-' || ((n * 2654435761) % 4294967296 % 30) || ' days')
  FROM (WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 3000)
        SELECT n FROM s)
 WHERE (1000 + n) % 50 <> 0;               -- docentes ficam de fora (prazo diferente)

-- ----------------------------------------------------------------------
-- 500.000 empréstimos HISTÓRICOS (já devolvidos). Duração 1..10 dias para prazo
-- de 7 => ~30% devolvidos com atraso => a trigger gera as multas automaticamente.
-- ----------------------------------------------------------------------
INSERT INTO emprestimo (id_exemplar, id_usuario, data_emprestimo, data_prevista, data_devolucao)
WITH s(n) AS (WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r WHERE n < 500000)
              SELECT n FROM r),
     g AS (SELECT n,
                  1001 + ((n * 2654435761) % 4294967296) % (SELECT count(*) FROM exemplar WHERE id_exemplar > 1000) AS ex,
                  1001 + ((n * 2246822519 + 3266489917) % 4294967296) % 30000 AS us,
                  11 + ((n * 3266489917 + 668265263) % 4294967296) % 1500 AS dias_atras,
                  1 + ((n * 374761393 + 1274126177) % 4294967296) % 10 AS dur
             FROM s)
SELECT ex, us,
       date('now', '-' || dias_atras || ' days'),
       date('now', '-' || dias_atras || ' days', '+7 days'),
       date('now', '-' || dias_atras || ' days', '+' || dur || ' days')
  FROM g;

-- 98% das multas já foram pagas; 2% seguem pendentes (inadimplência)
UPDATE multa
   SET status = 'paga',
       data_pagamento = min(date(data_geracao, '+3 days'), date('now'))
 WHERE id_multa % 50 <> 0;

COMMIT;
