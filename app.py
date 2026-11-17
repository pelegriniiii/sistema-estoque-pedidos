from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"
# Mantém o mesmo caminho do banco usado na versão anterior.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///estoque.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(120), nullable=False)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String(20), default="Concluído", nullable=False)
    itens = db.relationship("ItemPedido", backref="pedido", cascade="all, delete-orphan")


class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    produto = db.relationship("Produto")


class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(200), nullable=False, default="")
    data = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    produto = db.relationship("Produto")


def registrar_movimentacao(produto, tipo, quantidade, descricao):
    db.session.add(MovimentacaoEstoque(
        produto_id=produto.id,
        tipo=tipo,
        quantidade=quantidade,
        descricao=descricao
    ))


@app.route("/")
def inicio():
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    total_produtos = len(produtos)
    total_unidades = sum(p.quantidade for p in produtos)
    estoque_baixo = [p for p in produtos if p.quantidade <= 5]
    pedidos_recentes = Pedido.query.order_by(Pedido.data_criacao.desc()).limit(5).all()
    return render_template(
        "index.html",
        produtos=produtos,
        total_produtos=total_produtos,
        total_unidades=total_unidades,
        estoque_baixo=estoque_baixo,
        pedidos_recentes=pedidos_recentes
    )


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form.get("nome", "").strip()
    preco_texto = request.form.get("preco", "").strip().replace(",", ".")
    quantidade_texto = request.form.get("quantidade", "").strip()

    if not nome or not preco_texto or not quantidade_texto:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("inicio"))

    try:
        preco = Decimal(preco_texto)
        quantidade = int(quantidade_texto)
        if preco < 0 or quantidade < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        flash("Informe preço e quantidade válidos, iguais ou maiores que zero.", "erro")
        return redirect(url_for("inicio"))

    produto = Produto(nome=nome, preco=preco, quantidade=quantidade, ativo=True)
    db.session.add(produto)
    db.session.flush()
    if quantidade:
        registrar_movimentacao(produto, "Entrada", quantidade, "Saldo inicial do cadastro")
    db.session.commit()
    flash("Produto cadastrado com sucesso!", "sucesso")
    return redirect(url_for("inicio"))


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    produto = Produto.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        preco_texto = request.form.get("preco", "").strip().replace(",", ".")
        quantidade_texto = request.form.get("quantidade", "").strip()

        if not nome or not preco_texto or not quantidade_texto:
            flash("Preencha todos os campos.", "erro")
            return redirect(url_for("editar", id=id))

        try:
            preco = Decimal(preco_texto)
            quantidade = int(quantidade_texto)
            if preco < 0 or quantidade < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            flash("Informe valores válidos.", "erro")
            return redirect(url_for("editar", id=id))

        diferenca = quantidade - produto.quantidade
        produto.nome = nome
        produto.preco = preco
        produto.quantidade = quantidade
        if diferenca > 0:
            registrar_movimentacao(produto, "Entrada", diferenca, "Ajuste pela edição do produto")
        elif diferenca < 0:
            registrar_movimentacao(produto, "Saída", abs(diferenca), "Ajuste pela edição do produto")
        db.session.commit()
        flash("Produto atualizado com sucesso!", "sucesso")
        return redirect(url_for("inicio"))

    return render_template("editar.html", produto=produto)


@app.route("/desativar/<int:id>", methods=["POST"])
def desativar(id):
    produto = Produto.query.get_or_404(id)
    produto.ativo = False
    db.session.commit()
    flash(f'Produto "{produto.nome}" desativado. O registro foi preservado.', "sucesso")
    return redirect(url_for("inicio"))


@app.route("/estoque/<int:produto_id>", methods=["GET", "POST"])
def movimentar_estoque(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if request.method == "POST":
        tipo = request.form.get("tipo", "")
        descricao = request.form.get("descricao", "").strip()
        try:
            quantidade = int(request.form.get("quantidade", ""))
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            flash("A quantidade deve ser um número inteiro maior que zero.", "erro")
            return redirect(url_for("movimentar_estoque", produto_id=produto_id))

        if tipo == "Entrada":
            produto.quantidade += quantidade
        elif tipo == "Saída":
            if quantidade > produto.quantidade:
                flash("Estoque insuficiente para essa saída.", "erro")
                return redirect(url_for("movimentar_estoque", produto_id=produto_id))
            produto.quantidade -= quantidade
        else:
            flash("Selecione entrada ou saída.", "erro")
            return redirect(url_for("movimentar_estoque", produto_id=produto_id))

        registrar_movimentacao(produto, tipo, quantidade, descricao or "Movimentação manual")
        db.session.commit()
        flash("Estoque atualizado com sucesso!", "sucesso")
        return redirect(url_for("inicio"))

    return render_template("estoque.html", produto=produto)


@app.route("/pedidos")
def pedidos():
    lista = Pedido.query.order_by(Pedido.data_criacao.desc()).all()
    return render_template("pedidos.html", pedidos=lista)


@app.route("/pedidos/novo", methods=["GET", "POST"])
def novo_pedido():
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        ids = request.form.getlist("produto_id")
        quantidades = request.form.getlist("quantidade")

        if not cliente:
            flash("Informe o nome do cliente.", "erro")
            return redirect(url_for("novo_pedido"))

        itens_solicitados = {}
        try:
            for produto_id, quantidade_texto in zip(ids, quantidades):
                if not produto_id and not quantidade_texto:
                    continue
                if not produto_id or not quantidade_texto:
                    raise ValueError
                pid = int(produto_id)
                qtd = int(quantidade_texto)
                if qtd <= 0:
                    raise ValueError
                itens_solicitados[pid] = itens_solicitados.get(pid, 0) + qtd
        except ValueError:
            flash("Confira os produtos e informe quantidades inteiras maiores que zero.", "erro")
            return redirect(url_for("novo_pedido"))

        if not itens_solicitados:
            flash("Adicione pelo menos um produto ao pedido.", "erro")
            return redirect(url_for("novo_pedido"))

        produtos_pedido = {}
        for pid, qtd in itens_solicitados.items():
            produto = Produto.query.filter_by(id=pid, ativo=True).first()
            if not produto:
                flash("Um dos produtos selecionados não está disponível.", "erro")
                return redirect(url_for("novo_pedido"))
            if qtd > produto.quantidade:
                flash(f'Estoque insuficiente para "{produto.nome}". Disponível: {produto.quantidade}.', "erro")
                return redirect(url_for("novo_pedido"))
            produtos_pedido[pid] = (produto, qtd)

        pedido = Pedido(cliente=cliente)
        db.session.add(pedido)
        db.session.flush()

        for produto, qtd in produtos_pedido.values():
            db.session.add(ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantidade=qtd,
                preco_unitario=produto.preco
            ))
            produto.quantidade -= qtd
            registrar_movimentacao(produto, "Saída", qtd, f"Saída pelo pedido #{pedido.id}")

        db.session.commit()
        flash(f"Pedido #{pedido.id} registrado e estoque atualizado!", "sucesso")
        return redirect(url_for("pedidos"))

    return render_template("novo_pedido.html", produtos=produtos)


@app.route("/pedidos/<int:id>/cancelar", methods=["POST"])
def cancelar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if pedido.status == "Cancelado":
        flash("Esse pedido já está cancelado.", "erro")
        return redirect(url_for("pedidos"))

    for item in pedido.itens:
        produto = db.session.get(Produto, item.produto_id)
        if produto:
            produto.quantidade += item.quantidade
            registrar_movimentacao(
                produto, "Entrada", item.quantidade, f"Devolução do pedido cancelado #{pedido.id}"
            )

    pedido.status = "Cancelado"
    db.session.commit()
    flash(f"Pedido #{pedido.id} cancelado e itens devolvidos ao estoque.", "sucesso")
    return redirect(url_for("pedidos"))


@app.route("/movimentacoes")
def movimentacoes():
    lista = MovimentacaoEstoque.query.order_by(MovimentacaoEstoque.data.desc()).limit(200).all()
    return render_template("movimentacoes.html", movimentacoes=lista)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)