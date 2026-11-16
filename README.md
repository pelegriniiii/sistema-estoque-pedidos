# Estoque+ — Sistema de Gestão de Estoque e Pedidos

Sistema web desenvolvido em Python com Flask para auxiliar no cadastro de produtos, controle de estoque e gerenciamento de pedidos.

## Funcionalidades

- Cadastro e edição de produtos.
- Controle de entrada e saída de estoque.
- Registro e gerenciamento de pedidos.
- Baixa automática de estoque ao registrar pedidos.
- Cancelamento de pedidos com reposição de estoque.
- Histórico de movimentações.
- Alertas de estoque baixo.
- Painel inicial com informações gerais.

## Tecnologias utilizadas

- Python 3.12
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- JavaScript
- Pytest

## Requisitos

- Python 3.12 ou superior.
- Git.

## Como executar o projeto

1. Clone este repositório:

   `git clone https://github.com/pelegriniiii/sistema-estoque-pedidos.git`

2. Entre na pasta:

   `cd sistema-estoque-pedidos`

3. Crie um ambiente virtual:

   `python -m venv .venv`

4. Ative o ambiente virtual no Windows:

   `.venv\Scripts\Activate.ps1`

5. Instale as dependências:

   `pip install -r requirements.txt`

6. Execute a aplicação:

   `python app.py`

7. Acesse no navegador:

   `http://127.0.0.1:5000`

## Testes automatizados

O projeto utiliza Pytest para verificar o funcionamento das principais funcionalidades.

Para executar os testes:

`pytest -v`

Atualmente, o projeto possui 6 testes automatizados aprovados.

## Banco de dados

O sistema utiliza SQLite com Flask-SQLAlchemy para armazenar produtos, pedidos, itens dos pedidos e movimentações de estoque.

O banco de dados é criado localmente durante a execução da aplicação e não faz parte dos arquivos publicados no repositório.

## Objetivo

Desenvolver uma solução para facilitar o controle de produtos, movimentações de estoque e registro de pedidos, contribuindo para a organização e eficiência dos processos de gestão.