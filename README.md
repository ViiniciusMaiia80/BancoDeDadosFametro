# BancoDeDadosFametro
Modelagem e Otimização do Sistema de Empréstimos da Biblioteca Fametro
# 📚 Modelagem e Otimização do Sistema de Empréstimos da Biblioteca Fametro

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)
![Banco de Dados](https://img.shields.io/badge/Database-Relacional%20(SQL)-blue)
![Normalização](https://img.shields.io/badge/Normalização-3FN-green)
![Nível](https://img.shields.io/badge/Nível-Intermediário-orange)

Projeto de arquitetura, implementação e otimização de um banco de dados relacional desenvolvido para solucionar gargalos de desempenho, concorrência em renovações e falhas no controle de multas da **Biblioteca da Fametro**.

---

## 🎯 Problema e Objetivo

A biblioteca enfrenta lentidão nas buscas ao acervo e dificuldades operacionais no cálculo de multas por atraso e no controle de disponibilidade durante renovações simultâneas. 

O **objetivo** deste projeto é projetar do zero um banco de dados íntegro, normalizado até a **3ª Forma Normal (3FN)** e altamente performático para gerenciar o acervo, perfis de usuários (alunos e docentes), empréstimos, reservas e penalidades financeiras.

---

## 🛠️ Requisitos e Funcionalidades Implementadas

* **Modelagem de Dados (3FN):** Estruturação conceitual (DER) e lógica eliminando redundâncias e garantindo integridade referencial por meio de chaves primárias (`PK`), chaves estrangeiras (`FK`) e restrições (`CHECK`, `UNIQUE`, `NOT NULL`).
* **Automação de Regras de Negócio:** 
  * *Triggers* e *Stored Procedures* para atualização automática do status de disponibilidade dos exemplares (`Disponível`, `Emprestado`, `Reservado`, `Manutenção`) no momento do empréstimo ou devolução.
  * Rotina automatizada para cálculo de multas diárias após o vencimento da data prevista de devolução.
* **Inteligência e Relatórios Gerenciais (`Views`):**
  * Visões consolidadas para acompanhamento de livros mais emprestados por curso.
  * Relatório de alunos e docentes com pendências financeiras ou exemplares em atraso.
* **Otimização de Consultas (`Indexes`):**
  * Criação de índices estratégicos nas colunas de busca recorrente (`título`, `autor` e `ISBN`) para redução expressiva do tempo de resposta (*query execution time*).

---

## 📂 Estrutura do Repositório

```text
biblioteca-fametro-db/
├── docs/
│   ├── DER_Conceitual.pdf          # Diagrama Entidade-Relacionamento
│   ├── Modelo_Logico.png           # Esquema relacional normalizado (3FN)
│   └── Relatorio_Performance.md    # Comparativo de tempos antes e depois dos índices
├── scripts/
│   ├── 01_ddl_criacao_tabelas.sql  # Criação do banco, tabelas, constraints e índices
│   ├── 02_triggers_procedures.sql  # Regras automatizadas de disponibilidade e multas
│   ├── 03_dml_carga_dados.sql      # Massa de dados fictícios realistas para testes
│   └── 04_dql_views_relatorios.sql # Consultas analíticas e Views gerenciais
└── README.md
