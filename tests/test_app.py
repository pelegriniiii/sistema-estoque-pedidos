import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, db, Produto, Pedido


@pytest.fixture
def cliente():
	app.config["TESTING"] = True
	app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

	with app.app_context():
		db.create_all()

		produto = Produto(
			nome="Produto Teste",
			preco=10.00,
			quantidade=10,
			ativo=True
		)
		db.session.add(produto)
		db.session.commit()

		with app.test_client() as cliente_teste:
			yield cliente_teste

		db.session.remove()
		db.drop_all()


def test_pagina_inicial(cliente):
	resposta = cliente.get("/")
	assert resposta.status_code == 200


def test_entrada_e_saida_estoque(cliente):
	with app.app_context():
		produto = Produto.query.first()
		produto_id = produto.id

	cliente.post(
		f"/estoque/{produto_id}",
		data={
			"tipo": "Entrada",
			"quantidade": "5",
			"descricao": "Teste de entrada"
		}
	)

	with app.app_context():
		produto = db.session.get(Produto, produto_id)
		assert produto.quantidade == 15

	cliente.post(
		f"/estoque/{produto_id}",
		data={
			"tipo": "Saída",
			"quantidade": "3",
			"descricao": "Teste de saída"
		}
	)

	with app.app_context():
		produto = db.session.get(Produto, produto_id)
		assert produto.quantidade == 12


def test_criar_e_cancelar_pedido(cliente):
	with app.app_context():
		produto = Produto.query.first()
		produto_id = produto.id

	cliente.post(
		"/pedidos/novo",
		data={
			"cliente": "Cliente Teste",
			"produto_id": [str(produto_id)],
			"quantidade": ["2"]
		}
	)

	with app.app_context():
		produto = db.session.get(Produto, produto_id)
		pedido = Pedido.query.first()

		assert produto.quantidade == 8
		assert pedido is not None
		pedido_id = pedido.id

	cliente.post(f"/pedidos/{pedido_id}/cancelar")

	with app.app_context():
		produto = db.session.get(Produto, produto_id)
		pedido = db.session.get(Pedido, pedido_id)

		assert produto.quantidade == 10
		assert pedido.status == "Cancelado"


def test_impedir_saida_maior_que_estoque(cliente):
	with app.app_context():
		produto = Produto.query.first()
		produto_id = produto.id

	cliente.post(
		f"/estoque/{produto_id}",
		data={
			"tipo": "Saída",
			"quantidade": "20",
			"descricao": "Teste de estoque insuficiente"
		}
	)

	with app.app_context():
		produto = db.session.get(Produto, produto_id)
		assert produto.quantidade == 10
