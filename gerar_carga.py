#!/usr/bin/env python3
"""Gera 03_dml_carga.sql (dados fictícios realistas, reprodutíveis: seed fixa).

Títulos/autores são obras reais de bibliografias universitárias; ISBNs são
FICTÍCIOS (formato 978-85 + dígito verificador válido). Alunos, docentes,
empréstimos, multas e reservas são sintéticos. As datas são expressões
relativas a date('now'), então a carga fica "atual" em qualquer dia de execução.
"""
import random, unicodedata, os

random.seed(2026)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03_dml_carga.sql")

def q(s):                      # literal SQL
    return "'" + str(s).replace("'", "''") + "'"

def dt(n):                     # n dias atrás
    return "date('now')" if n == 0 else f"date('now','-{n} days')"

def semacento(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace(" ", ".")

def isbn13(n):
    base = "97885" + f"{n:07d}"
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base))
    return base + str((10 - s % 10) % 10)

# ---------------------------------------------------------------- domínio
CURSOS = [("Direito", "DIR"), ("Medicina", "MED"), ("Enfermagem", "ENF"), ("Psicologia", "PSI"),
          ("Engenharia Civil", "ECIV"), ("Administração", "ADM"),
          ("Ciência da Computação", "CCOMP"), ("Odontologia", "ODO")]

CATEGORIAS = ["Direito", "Medicina", "Enfermagem e Saúde", "Psicologia", "Engenharia",
              "Administração e Economia", "Computação", "Odontologia", "Ciências Básicas",
              "Metodologia Científica", "Literatura Brasileira"]

AFINIDADE = {  # curso -> categorias mais consultadas por seus alunos
    "DIR": ["Direito", "Metodologia Científica", "Literatura Brasileira"],
    "MED": ["Medicina", "Ciências Básicas", "Enfermagem e Saúde"],
    "ENF": ["Enfermagem e Saúde", "Ciências Básicas", "Medicina"],
    "PSI": ["Psicologia", "Metodologia Científica", "Medicina"],
    "ECIV": ["Engenharia", "Ciências Básicas", "Administração e Economia"],
    "ADM": ["Administração e Economia", "Metodologia Científica", "Direito"],
    "CCOMP": ["Computação", "Ciências Básicas", "Engenharia"],
    "ODO": ["Odontologia", "Ciências Básicas", "Enfermagem e Saúde"],
}

# (título, [autores], categoria, editora, ano)
L = []
def add(cat, lista):
    for t, a, e, y in lista:
        L.append((t, a, cat, e, y))

add("Direito", [
 ("Curso de Direito Constitucional", ["Gilmar Ferreira Mendes", "Paulo Gustavo Gonet Branco"], "Saraiva", 2023),
 ("Manual de Direito Civil", ["Flávio Tartuce"], "Método", 2023),
 ("Curso de Direito Penal", ["Rogério Greco"], "Impetus", 2022),
 ("Direito Administrativo Brasileiro", ["Hely Lopes Meirelles"], "Malheiros", 2016),
 ("Curso de Processo Civil", ["Luiz Guilherme Marinoni", "Sérgio Cruz Arenhart"], "Revista dos Tribunais", 2022),
 ("Curso de Direito do Trabalho", ["Maurício Godinho Delgado"], "LTr", 2023),
 ("Teoria Pura do Direito", ["Hans Kelsen"], "Martins Fontes", 2009),
 ("Introdução ao Estudo do Direito", ["Paulo Nader"], "Forense", 2021),
 ("Curso de Direito Tributário", ["Hugo de Brito Machado"], "Malheiros", 2021),
 ("Direito Empresarial", ["André Luiz Santa Cruz Ramos"], "Método", 2022),
 ("Lições Preliminares de Direito", ["Miguel Reale"], "Saraiva", 2002),
 ("Curso de Direito Processual Penal", ["Eugênio Pacelli"], "Atlas", 2021),
 ("Curso de Direito Civil Brasileiro", ["Maria Helena Diniz"], "Saraiva", 2022),
])
add("Medicina", [
 ("Tratado de Fisiologia Médica", ["Arthur C. Guyton", "John E. Hall"], "Elsevier", 2021),
 ("Atlas de Anatomia Humana", ["Frank H. Netter"], "Elsevier", 2019),
 ("Medicina Interna de Harrison", ["Dennis L. Kasper", "Anthony S. Fauci"], "AMGH", 2017),
 ("Robbins & Cotran Patologia", ["Vinay Kumar", "Abul K. Abbas"], "Elsevier", 2016),
 ("Farmacologia Básica e Clínica", ["Bertram G. Katzung"], "AMGH", 2017),
 ("Cecil Medicina", ["Lee Goldman", "Andrew I. Schafer"], "Elsevier", 2018),
 ("Microbiologia Médica", ["Patrick R. Murray"], "Elsevier", 2022),
 ("Parasitologia Humana", ["David Pereira Neves"], "Atheneu", 2016),
 ("Bioquímica Ilustrada de Harper", ["Victor W. Rodwell"], "AMGH", 2017),
 ("Porto Semiologia Médica", ["Celmo Celeno Porto"], "Guanabara Koogan", 2019),
 ("Imunologia Celular e Molecular", ["Abul K. Abbas", "Andrew H. Lichtman"], "Elsevier", 2019),
 ("Tratado de Infectologia", ["Ricardo Veronesi", "Roberto Focaccia"], "Atheneu", 2015),
])
add("Enfermagem e Saúde", [
 ("Fundamentos de Enfermagem", ["Patricia A. Potter", "Anne Griffin Perry"], "Elsevier", 2018),
 ("Tratado de Enfermagem Médico-Cirúrgica", ["Suzanne C. Smeltzer", "Brenda G. Bare"], "Guanabara Koogan", 2020),
 ("Diagnósticos de Enfermagem da NANDA-I", ["T. Heather Herdman", "Shigemi Kamitsuru"], "Artmed", 2021),
 ("Epidemiologia", ["Roberto Medronho"], "Atheneu", 2009),
 ("Tratado de Saúde Coletiva", ["Gastão Wagner de Sousa Campos"], "Hucitec", 2012),
 ("Farmacologia Clínica para Enfermagem", ["Karen Whalen"], "Artmed", 2016),
])
add("Psicologia", [
 ("Introdução à Psicologia de Hilgard", ["Rita L. Atkinson"], "Cengage", 2018),
 ("Desenvolvimento Humano", ["Diane E. Papalia", "Ruth Duskin Feldman"], "AMGH", 2013),
 ("DSM-5: Manual Diagnóstico e Estatístico de Transtornos Mentais", ["American Psychiatric Association"], "Artmed", 2014),
 ("Teorias da Personalidade", ["Calvin S. Hall", "Gardner Lindzey"], "LTC", 2000),
 ("A Interpretação dos Sonhos", ["Sigmund Freud"], "Companhia das Letras", 2019),
 ("Psicologia Social", ["David G. Myers"], "AMGH", 2014),
 ("Terapia Cognitivo-Comportamental: Teoria e Prática", ["Judith S. Beck"], "Artmed", 2022),
 ("Neurociências: Desvendando o Sistema Nervoso", ["Mark F. Bear", "Barry W. Connors"], "Artmed", 2017),
])
add("Engenharia", [
 ("Resistência dos Materiais", ["R. C. Hibbeler"], "Pearson", 2010),
 ("Estática: Mecânica para Engenharia", ["R. C. Hibbeler"], "Pearson", 2011),
 ("Mecânica dos Materiais", ["Ferdinand P. Beer", "E. Russell Johnston Jr."], "AMGH", 2011),
 ("Mecânica dos Fluidos", ["Franco Brunetti"], "Pearson", 2008),
 ("Concreto Armado Eu Te Amo", ["Manoel Henrique Campos Botelho"], "Blucher", 2015),
 ("Fundamentos de Engenharia Geotécnica", ["Braja M. Das"], "Cengage", 2014),
 ("Materiais de Construção", ["L. A. Falcão Bauer"], "LTC", 2019),
 ("Hidrologia: Ciência e Aplicação", ["Carlos E. M. Tucci"], "UFRGS", 2009),
 ("Instalações Elétricas", ["Hélio Creder"], "LTC", 2016),
 ("Topografia", ["Jorge Luiz Pinto de Campos"], "Oficina de Textos", 2018),
])
add("Administração e Economia", [
 ("Introdução à Teoria Geral da Administração", ["Idalberto Chiavenato"], "Atlas", 2014),
 ("Administração de Marketing", ["Philip Kotler", "Kevin Lane Keller"], "Pearson", 2012),
 ("Princípios de Administração Financeira", ["Lawrence J. Gitman"], "Pearson", 2010),
 ("Gestão de Pessoas", ["Idalberto Chiavenato"], "Atlas", 2020),
 ("Contabilidade Introdutória", ["Equipe de Professores da FEA-USP"], "Atlas", 2018),
 ("Estratégia Competitiva", ["Michael E. Porter"], "Campus", 2004),
 ("Administração da Produção", ["Nigel Slack", "Stuart Chambers"], "Atlas", 2018),
 ("Princípios de Economia", ["N. Gregory Mankiw"], "Cengage", 2019),
 ("Comportamento Organizacional", ["Stephen P. Robbins", "Timothy A. Judge"], "Pearson", 2020),
 ("Logística Empresarial", ["Ronald H. Ballou"], "Bookman", 2006),
])
add("Computação", [
 ("Algoritmos: Teoria e Prática", ["Thomas H. Cormen", "Charles E. Leiserson"], "Elsevier", 2012),
 ("Sistemas de Banco de Dados", ["Ramez Elmasri", "Shamkant B. Navathe"], "Pearson", 2018),
 ("Sistema de Banco de Dados", ["Abraham Silberschatz", "Henry F. Korth", "S. Sudarshan"], "Elsevier", 2020),
 ("Engenharia de Software", ["Ian Sommerville"], "Pearson", 2011),
 ("Redes de Computadores e a Internet", ["James F. Kurose", "Keith W. Ross"], "Pearson", 2021),
 ("Sistemas Operacionais Modernos", ["Andrew S. Tanenbaum", "Herbert Bos"], "Pearson", 2016),
 ("Arquitetura e Organização de Computadores", ["William Stallings"], "Pearson", 2017),
 ("Código Limpo", ["Robert C. Martin"], "Alta Books", 2009),
 ("Inteligência Artificial", ["Stuart Russell", "Peter Norvig"], "Elsevier", 2013),
 ("Estruturas de Dados e Algoritmos em Java", ["Michael T. Goodrich", "Roberto Tamassia"], "Bookman", 2013),
 ("Padrões de Projeto", ["Erich Gamma", "Richard Helm", "Ralph Johnson", "John Vlissides"], "Bookman", 2000),
 ("Compiladores: Princípios, Técnicas e Ferramentas", ["Alfred V. Aho", "Monica S. Lam"], "Pearson", 2008),
 ("Java: Como Programar", ["Paul Deitel", "Harvey Deitel"], "Pearson", 2016),
])
add("Odontologia", [
 ("Carranza Periodontia Clínica", ["Michael G. Newman", "Henry H. Takei"], "Elsevier", 2016),
 ("Ten Cate Histologia Oral", ["Antonio Nanci"], "Elsevier", 2019),
 ("Phillips Materiais Dentários", ["Kenneth J. Anusavice"], "Elsevier", 2013),
 ("Farmacologia e Terapêutica em Odontologia", ["Eduardo Dias de Andrade"], "Artes Médicas", 2014),
 ("Cohen Caminhos da Polpa", ["Kenneth M. Hargreaves", "Stephen Cohen"], "Elsevier", 2017),
 ("Radiologia Odontológica e Imaginologia", ["Luiz Casati Álvares", "Ricardo Tavano"], "Artes Médicas", 2019),
])
add("Ciências Básicas", [
 ("Princípios de Anatomia e Fisiologia", ["Gerard J. Tortora", "Bryan Derrickson"], "Guanabara Koogan", 2019),
 ("Histologia Básica", ["Luiz Carlos Junqueira", "José Carneiro"], "Guanabara Koogan", 2017),
 ("Cálculo, Volume 1", ["James Stewart"], "Cengage", 2017),
 ("Fundamentos de Física, Volume 1", ["David Halliday", "Robert Resnick", "Jearl Walker"], "LTC", 2016),
 ("Biologia Celular e Molecular", ["Carlos Alberto Soares"], "Rideel", 2010),
 ("Estatística Básica", ["Wilton de O. Bussab", "Pedro A. Morettin"], "Saraiva", 2017),
])
add("Metodologia Científica", [
 ("Fundamentos de Metodologia Científica", ["Marina de Andrade Marconi", "Eva Maria Lakatos"], "Atlas", 2017),
 ("Como Elaborar Projetos de Pesquisa", ["Antonio Carlos Gil"], "Atlas", 2017),
 ("Metodologia do Trabalho Científico", ["Antônio Joaquim Severino"], "Cortez", 2016),
 ("Metodologia da Pesquisa-Ação", ["Michel Thiollent"], "Cortez", 2011),
])
add("Literatura Brasileira", [
 ("Dom Casmurro", ["Machado de Assis"], "Penguin-Companhia", 2016),
 ("Memórias Póstumas de Brás Cubas", ["Machado de Assis"], "Penguin-Companhia", 2014),
 ("Vidas Secas", ["Graciliano Ramos"], "Record", 2013),
 ("Grande Sertão: Veredas", ["João Guimarães Rosa"], "Nova Fronteira", 2006),
 ("A Hora da Estrela", ["Clarice Lispector"], "Rocco", 1998),
 ("Capitães da Areia", ["Jorge Amado"], "Companhia das Letras", 2008),
 ("Dois Irmãos", ["Milton Hatoum"], "Companhia das Letras", 2000),
 ("Relato de um Certo Oriente", ["Milton Hatoum"], "Companhia das Letras", 2008),
])

# ---------------------------------------------------------------- entidades
editoras = sorted({b[3] for b in L})
autores = []
for b in L:
    for a in b[1]:
        if a not in autores:
            autores.append(a)
ed_id = {e: i + 1 for i, e in enumerate(editoras)}
au_id = {a: i + 1 for i, a in enumerate(autores)}
cat_id = {c: i + 1 for i, c in enumerate(CATEGORIAS)}
curso_id = {s: i + 1 for i, (_, s) in enumerate(CURSOS)}

livros = []            # (id, isbn, titulo, ano, edicao, ed, cat, pop)
for i, (t, a, c, e, y) in enumerate(L, 1):
    pop = random.choice([0.5, 0.8, 1, 1, 1, 1.3, 1.6, 2.2])
    ed = random.choice([1, 1, 1, 2, 3, 5])
    livros.append((i, isbn13(1000 + i * 37), t, y, ed, ed_id[e], cat_id[c], pop, a, c))

exemplares = []        # (id, id_livro, patrimonio, aquisicao_dias)
for lv in livros:
    n = random.choice([1, 2, 2, 3, 3, 4]) if lv[7] >= 1 else random.choice([1, 1, 2])
    for _ in range(n):
        eid = len(exemplares) + 1
        exemplares.append((eid, lv[0], f"FAM-{eid:05d}", random.randint(700, 2500)))
ex_livro = {e[0]: e[1] for e in exemplares}
liv_exs = {}
for e in exemplares:
    liv_exs.setdefault(e[1], []).append(e[0])
liv_cat = {lv[0]: lv[9] for lv in livros}
liv_pop = {lv[0]: lv[7] for lv in livros}

# ---------------------------------------------------------------- usuários
NOMES = ["Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela", "Helena", "Isabela",
         "Joana", "Karina", "Larissa", "Mariana", "Natália", "Priscila", "Rafaela", "Sofia", "Taís",
         "Vitória", "Yasmin", "Adriano", "Bruno", "Carlos", "Davi", "Eduardo", "Felipe", "Gustavo",
         "Henrique", "Igor", "João", "Kauã", "Lucas", "Matheus", "Nathan", "Otávio", "Pedro",
         "Rafael", "Samuel", "Thiago", "Vinícius", "Wesley", "Yuri", "Ítalo", "Jéssica", "Raimundo", "Socorro"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Lima", "Costa", "Ferreira", "Rodrigues",
              "Almeida", "Nascimento", "Araújo", "Ribeiro", "Carvalho", "Gomes", "Martins", "Barbosa",
              "Rocha", "Dias", "Monteiro", "Cardoso", "Teixeira", "Moura", "Cavalcante", "Batista",
              "Menezes", "Freitas", "Nogueira", "Tavares", "Pinheiro", "Lopes", "Albuquerque", "Brandão",
              "Mendonça", "Amaral", "Farias", "Bentes", "Façanha", "Benevides", "Sampaio"]

TIPOS = [(1, "ALUNO", 3, 7, 2, 1.00), (2, "DOCENTE", 5, 15, 3, 0.50)]
tipo_prazo = {1: 7, 2: 15}

usuarios = []   # (id, matricula, nome, email, tipo, curso_sigla, ativo, cadastro_dias)
used_names = set()
def novo_nome():
    while True:
        n = f"{random.choice(NOMES)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
        if n not in used_names:
            used_names.add(n)
            return n

seq = 0
for _, sigla in CURSOS:
    for _ in range(40):
        seq += 1
        n = novo_nome()
        ano = random.choice([2022, 2023, 2023, 2024, 2024, 2025, 2026])
        usuarios.append((len(usuarios) + 1, f"{ano}{curso_id[sigla]:02d}{seq:04d}", n,
                         f"{semacento(n)}.{seq}@alunos.fametro.example", 1, sigla,
                         0 if random.random() < 0.02 else 1, random.randint(60, 1000)))
    for _ in range(4):
        seq += 1
        n = novo_nome()
        usuarios.append((len(usuarios) + 1, f"DOC{seq:04d}", "Prof. " + n,
                         f"{semacento(n)}.{seq}@docentes.fametro.example", 2, sigla, 1,
                         random.randint(300, 2500)))
alunos_por_curso = {s: [u for u in usuarios if u[5] == s and u[4] == 1] for _, s in CURSOS}
docs_por_curso = {s: [u for u in usuarios if u[5] == s and u[4] == 2] for _, s in CURSOS}
u_by_id = {u[0]: u for u in usuarios}

def escolhe_usuario(id_livro):
    cat = liv_cat[id_livro]
    pesos = [6 if cat in AFINIDADE[s] else 1 for _, s in CURSOS]
    sigla = random.choices([s for _, s in CURSOS], weights=pesos)[0]
    pool = docs_por_curso[sigla] if random.random() < 0.10 else alunos_por_curso[sigla]
    return random.choice(pool)

# ---------------------------------------------------------------- empréstimos
def duracao(prazo):
    r = random.random()
    if r < 0.60: return random.randint(1, prazo)
    if r < 0.82: return prazo
    return prazo + random.choice([1, 1, 2, 3, 4, 5, 7, 10, 14, 21, 30])

# 1) escolher exemplares que terão empréstimo ABERTO e livros com fila de reserva
todos_ex = [e[0] for e in exemplares]
livros_reserva = random.sample([lv[0] for lv in livros if len(liv_exs[lv[0]]) <= 2], 14)
ex_aberto = {}                           # exemplar -> (usuario, offset_inicio)
for lv in livros_reserva:
    for ex in liv_exs[lv]:
        ex_aberto[ex] = None
resto = [e for e in todos_ex if e not in ex_aberto and ex_livro[e] not in livros_reserva]
for ex in random.sample(resto, 40):
    ex_aberto[ex] = None

# 2) histórico fechado
fechados = []     # (inicio_off, fim_off, ex, usuario, prazo)

# define quem terá atraso (~30%)
ex_list = list(ex_aberto)
random.shuffle(ex_list)
open_offset = {}
for i, ex in enumerate(ex_list):
    if i < 16:     # atrasados (prazo aluno 7d, docente 15d) -> mais de 15 dias garante atraso para ambos
        open_offset[ex] = random.randint(18, 60)
    else:
        open_offset[ex] = random.randint(0, 6)   # em dia (aluno 7d)

for ex in todos_ex:
    pop = liv_pop[ex_livro[ex]]
    corte = open_offset.get(ex, -1)           # histórico deve terminar antes do aberto
    cur = random.randint(250, 540)
    tentativas = int(random.uniform(5, 15) * pop)
    for _ in range(tentativas):
        u = escolhe_usuario(ex_livro[ex])
        prazo = tipo_prazo[u[4]]
        inicio = cur - random.randint(0, 18)
        fim = inicio - duracao(prazo)
        if fim < max(corte + 1, 0) or inicio < 1:
            break
        fechados.append((inicio, fim, ex, u, prazo))
        cur = fim
fechados.sort(key=lambda r: -r[0])           # mais antigos primeiro

# multas previstas (espelho do que a trigger fará) -> para decidir pendentes/pagas
multas_prev = []   # (idx_emprestimo, id_usuario, dias)
for i, (ini, fim, ex, u, prazo) in enumerate(fechados, 1):
    dias = (ini - fim) - prazo                # duração do empréstimo - prazo
    if dias > 0:
        multas_prev.append((i, u[0], dias, fim))

users_com_multa = sorted({m[1] for m in multas_prev})
pend_users = set(random.sample([x for x in users_com_multa if u_by_id[x][6] == 1 and u_by_id[x][4] == 1], 26))
pend_ids = []
for i, uid, dias, fim in multas_prev:
    if uid in pend_users and fim <= 150:      # só as devoluções mais recentes (<=150d) ficam pendentes
        pend_ids.append(i)
# garante >=1 pendente por usuário pendente
for uid in pend_users:
    mine = [m for m in multas_prev if m[1] == uid]
    if not any(m[0] in pend_ids for m in mine):
        pend_ids.append(min(mine, key=lambda m: m[3])[0])
pend_users = {fechados[i - 1][3][0] for i in pend_ids}

# 3) empréstimos abertos: usuário único, ativo, sem multa pendente
elegiveis = [u for u in usuarios if u[6] == 1 and u[0] not in pend_users]
random.shuffle(elegiveis)
abertos = []      # (off, ex, usuario)
ocup = {}
for ex in sorted(ex_aberto, key=lambda e: -open_offset[e]):
    lv = ex_livro[ex]
    u = elegiveis.pop()
    abertos.append((open_offset[ex], ex, u))
    ocup.setdefault(lv, set()).add(u[0])

# ---------------------------------------------------------------- escrita
def batch(f, tabela, cols, rows, n=40):
    for i in range(0, len(rows), n):
        f.write(f"INSERT INTO {tabela} ({cols}) VALUES\n  " + ",\n  ".join(rows[i:i + n]) + ";\n")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("-- =====================================================================\n"
            "-- BIBLIOTECA FAMETRO - 03_dml_carga.sql  (GERADO por gerar_carga.py, seed fixa)\n"
            "-- Dados fictícios realistas. Títulos/autores reais; ISBNs, usuários e\n"
            "-- movimentações são sintéticos. Datas relativas a date('now').\n"
            "-- Pré-requisito: 01_ddl.sql e 02_triggers.sql já executados.\n"
            "-- =====================================================================\n"
            "PRAGMA foreign_keys = ON;\nBEGIN;\n\n")
    f.write("-- Cursos\n")
    batch(f, "curso", "id_curso, nome, sigla", [f"({i}, {q(n)}, {q(s)})" for i, (n, s) in enumerate(CURSOS, 1)])
    f.write("\n-- Tipos de usuário (regras de empréstimo)\n")
    batch(f, "tipo_usuario", "id_tipo, nome, limite_emprestimos, prazo_dias, max_renovacoes, valor_multa_dia",
          [f"({a}, {q(b)}, {c}, {d}, {e}, {g})" for a, b, c, d, e, g in TIPOS])
    f.write("\n-- Categorias\n")
    batch(f, "categoria", "id_categoria, nome", [f"({i}, {q(c)})" for i, c in enumerate(CATEGORIAS, 1)])
    f.write("\n-- Editoras\n")
    batch(f, "editora", "id_editora, nome", [f"({i}, {q(e)})" for i, e in enumerate(editoras, 1)])
    f.write("\n-- Autores\n")
    batch(f, "autor", "id_autor, nome", [f"({i}, {q(a)})" for i, a in enumerate(autores, 1)])
    f.write("\n-- Livros (obras)\n")
    batch(f, "livro", "id_livro, isbn, titulo, ano_publicacao, edicao, id_editora, id_categoria",
          [f"({l[0]}, {q(l[1])}, {q(l[2])}, {l[3]}, {l[4]}, {l[5]}, {l[6]})" for l in livros])
    f.write("\n-- Livro x Autor\n")
    la = []
    for l in livros:
        for o, a in enumerate(l[8], 1):
            la.append(f"({l[0]}, {au_id[a]}, {o})")
    batch(f, "livro_autor", "id_livro, id_autor, ordem", la)
    f.write("\n-- Exemplares (cópias físicas)\n")
    batch(f, "exemplar", "id_exemplar, id_livro, patrimonio, data_aquisicao",
          [f"({e[0]}, {e[1]}, {q(e[2])}, {dt(e[3])})" for e in exemplares])
    f.write("\n-- Usuários (alunos e docentes)\n")
    batch(f, "usuario", "id_usuario, matricula, nome, email, id_tipo, id_curso, ativo, data_cadastro",
          [f"({u[0]}, {q(u[1])}, {q(u[2])}, {q(u[3])}, {u[4]}, {curso_id[u[5]]}, {u[6]}, {dt(u[7])})" for u in usuarios])

    f.write(f"\n-- Histórico: {len(fechados)} empréstimos já devolvidos "
            "(a trigger trg_emp_ai_multa_historica gera as multas dos atrasos)\n")
    batch(f, "emprestimo", "id_emprestimo, id_exemplar, id_usuario, data_emprestimo, data_prevista, data_devolucao",
          [f"({i}, {ex}, {u[0]}, {dt(ini)}, {dt(ini - prazo)}, {dt(fim)})"
           for i, (ini, fim, ex, u, prazo) in enumerate(fechados, 1)], n=60)

    f.write("\n-- Multas: pendentes apenas para um grupo de alunos; as demais foram pagas\n")
    f.write("UPDATE multa\n   SET status = 'paga',\n"
            "       data_pagamento = min(date(data_geracao, '+' || ((id_multa % 6) + 1) || ' days'), date('now'))\n"
            " WHERE id_emprestimo NOT IN (" + ", ".join(map(str, sorted(pend_ids))) + ");\n")

    f.write(f"\n-- Empréstimos EM ABERTO ({len(abertos)}): validados pelas triggers; prazo calculado pela trigger\n")
    for off, ex, u in abertos:
        f.write(f"INSERT INTO emprestimo (id_exemplar, id_usuario, data_emprestimo) VALUES ({ex}, {u[0]}, {dt(off)});\n")

    # reservas ativas nos livros com todos os exemplares emprestados
    f.write("\n-- Reservas ATIVAS (livros sem exemplar disponível)\n")
    candidatos = [u for u in usuarios if u[6] == 1]
    n_res = 0
    for lv in livros_reserva:
        for u in random.sample([c for c in candidatos if c[0] not in ocup.get(lv, set())], random.randint(1, 3)):
            f.write(f"INSERT INTO reserva (id_livro, id_usuario, data_reserva) VALUES ({lv}, {u[0]}, {dt(random.randint(0, 12))});\n")
            n_res += 1

    f.write("\n-- Reservas finalizadas (histórico)\n")
    hist = []
    for _ in range(30):
        lv = random.choice(livros)[0]
        u = random.choice(candidatos)
        hist.append(f"({lv}, {u[0]}, {dt(random.randint(20, 400))}, {q(random.choice(['atendida', 'atendida', 'cancelada']))})")
    batch(f, "reserva", "id_livro, id_usuario, data_reserva, status", hist)

    # renovações: empréstimos abertos em dia, de livros sem reserva alheia
    f.write("\n-- Renovações (empréstimos em dia, livros sem fila de reserva)\n")
    ren = [(off, ex, u) for off, ex, u in abertos
           if off <= 6 and ex_livro[ex] not in livros_reserva]
    for k, (off, ex, u) in enumerate(ren[:12]):
        f.write(f"INSERT INTO renovacao (id_emprestimo, numero) "
                f"SELECT id_emprestimo, 1 FROM emprestimo WHERE id_exemplar = {ex} AND data_devolucao IS NULL;\n")
        if k < 4:
            f.write(f"INSERT INTO renovacao (id_emprestimo, numero) "
                    f"SELECT id_emprestimo, 2 FROM emprestimo WHERE id_exemplar = {ex} AND data_devolucao IS NULL;\n")

    # exemplares fora de circulação
    livres = [e for e in todos_ex if e not in ex_aberto and liv_exs[ex_livro[e]].index(e) > 0]
    manut = random.sample(livres, 5)
    perd = random.sample([e for e in livres if e not in manut], 3)
    f.write("\n-- Exemplares fora de circulação\n")
    f.write(f"UPDATE exemplar SET status = 'manutencao' WHERE id_exemplar IN ({', '.join(map(str, manut))});\n")
    f.write(f"UPDATE exemplar SET status = 'perdido' WHERE id_exemplar IN ({', '.join(map(str, perd))});\n")
    f.write("\nCOMMIT;\n")

print(f"livros={len(livros)} exemplares={len(exemplares)} usuarios={len(usuarios)} "
      f"fechados={len(fechados)} multas_prev={len(multas_prev)} pendentes={len(pend_ids)} "
      f"abertos={len(abertos)} reservas_ativas={n_res}")
