import os
import os.path as op
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_admin as admin
from flask_admin.contrib.sqla import ModelView
import datetime
from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask_login import login_user, logout_user, login_required
from flask_admin import BaseView, expose
import datetime

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Create in-memory database
app.config['DATABASE_FILE'] = 'app_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


# Models
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    matricula = db.Column(db.String(7), unique=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, password, admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(
            password, app.config.get('BCRYPT_LOG_ROUNDS')
        ).decode('utf-8')
        self.registered_on = datetime.datetime.now()
        self.admin = admin

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {0}>'.format(self.email)


class Empregado(db.Model):
    __tablename__ = "empregado"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    matricula = db.Column(db.String(7), unique=True)
    nome = db.Column(db.String(100), unique=True)

    agencia_digital_id = db.Column(db.Integer, db.ForeignKey('agencia_digital.id'))
    agencia_digital = db.relationship("AgenciaDigital")

    def __repr__(self,):
        return self.matricula + ' - ' + self.nome


class Produto(db.Model):
    __tablename__ = "produto"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True)

    tipo_produto_id = db.Column(db.Integer, db.ForeignKey('tipo_produto.id'))
    tipo_produto = db.relationship("TipoProduto")

    def __repr__(self):
        return self.nome


class TipoAtendimento(db.Model):
    __tablename__ = "tipo_atendimento"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return self.nome


class AgenciaDigital(db.Model):
    __tablename__ = "agencia_digital"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return self.nome


class TipoProduto(db.Model):
    __tablename__ = "tipo_produto"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return self.nome


class Atendimento(db.Model):
    __tablename__ = "atendimento"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    agencia_digital_id = db.Column(db.Integer, db.ForeignKey('agencia_digital.id'))
    agencia_digital = db.relationship("AgenciaDigital")
    dt_atendimento = db.Column(db.DateTime(), nullable=False)
    empregado_id = db.Column(db.Integer, db.ForeignKey('empregado.id'))
    empregado = db.relationship("Empregado")
    co_agencia = db.Column(db.String(4), unique=False, nullable=False)
    cpf_cliente = db.Column(db.String(11), unique=False, nullable=False)
    nome_cliente = db.Column(db.String(200), unique=False, nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    produto = db.relationship("Produto")
    tipo_atendimento_id = db.Column(db.Integer, db.ForeignKey('tipo_atendimento.id'))
    tipo_atendimento = db.relationship("TipoAtendimento")
    valor = db.Column(db.Float, primary_key=False, nullable=False, default=0)
    quantidade = db.Column(db.Integer, primary_key=False, nullable=False, default=1)
    descricao_demanda = db.Column(db.Text, unique=False)
    operacional = db.Column(db.String(255), unique=False)


# Customized admin interface
class CustomView(ModelView):
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'


class AtendimentoView(ModelView):
    list_template = 'atendimento/list.html'
    create_template = 'atendimento/create.html'
    edit_template = 'atendimento/edit.html'


class UserAdmin(CustomView):
    column_searchable_list = ('name',)
    column_filters = ('name', 'email')

# Create admin with custom base template
admin = admin.Admin(
    app, 'Agência Digital',
    base_template='layout.html',
    template_mode='bootstrap3'
)

# Add views to CRUD
admin.add_view(UserAdmin(User, db.session, name='Usuários'))
admin.add_view(CustomView(Empregado, db.session))
admin.add_view(CustomView(Produto, db.session))
admin.add_view(CustomView(TipoProduto, db.session))
admin.add_view(CustomView(TipoAtendimento, db.session))
admin.add_view(CustomView(AgenciaDigital, db.session))
admin.add_view(AtendimentoView(Atendimento, db.session))


# Add custom views
class RelatorioView(BaseView):
    @expose('/')
    def index(self):
        dados = db.session.query(Produto).all()

        now = datetime.datetime.now().strftime("%Y-%m-%d")
        now = datetime.datetime.strptime('06072017', '%d%m%Y').date()

        producao_dia = db.session.query(
            Atendimento.dt_atendimento.label('data'),
            Produto.nome.label('nome'),
            db.func.sum(Atendimento.valor).label('valor'),
            db.func.sum(Atendimento.quantidade).label('quantidade'),
        ).outerjoin(Atendimento.produto
        ).outerjoin(Atendimento.tipo_atendimento
        #).filter(TipoAtendimento.nome=='Contratação'
        ).filter(Atendimento.dt_atendimento>now
        ).group_by(Atendimento.produto_id).all()

        return self.render('relatorio/index.html', dados=producao_dia)

admin.add_view(RelatorioView(name='Relatórios', endpoint='relatorios'))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    db.drop_all()
    db.create_all()

    srs_text = [
        {"nome":"SR Ipiranga"},
        {"nome":"SR Brasília Norte"},
        {"nome":"SR Campinas"},
        {"nome":"SR Rio Grande do Sul"},
        {"nome":"SR Sul de Goiás"}
    ]

    for entry in srs_text:
        tipo = AgenciaDigital()
        tipo.nome = entry['nome']
        db.session.add(tipo)

    empregados_text = [
        {"matricula":"c054271","nome":"Marcelle Christiane Silva Gordon","agencia_digital":"SR Ipiranga"},
        {"matricula":"c133652","nome":"Fernanda Silvério Bergamasco","agencia_digital":"SR Ipiranga"},
        {"matricula":"c090762","nome":"Rodrigo Prado de Jesus","agencia_digital":"SR Ipiranga"},
        {"matricula":"c076590","nome":"Diana de Paula Neves","agencia_digital":"SR Ipiranga"},
        {"matricula":"c072195","nome":"Luciana Queiroz Pinto Marques","agencia_digital":"SR Ipiranga"},
        {"matricula":"c099339","nome":"Maria de Fatima Ferreira","agencia_digital":"SR Ipiranga"},
        {"matricula":"c107332","nome":"Aline de Freitas Valim","agencia_digital":"SR Ipiranga"},
        {"matricula":"c128490","nome":"Edjane Sarai Oliveira Garcia","agencia_digital":"SR Ipiranga"},
        {"matricula":"c137557","nome":"Ana Natalia Paz de Andrade","agencia_digital":"SR Ipiranga"},
        {"matricula":"c125852","nome":"Susiane Felix Casagrande Nishizawa","agencia_digital":"SR Ipiranga"},
        {"matricula":"c140422","nome":"Vanessa Martins Luongo","agencia_digital":"SR Ipiranga"}
    ]

    for entry in empregados_text:
        empregado = Empregado()
        empregado.matricula = entry['matricula']
        empregado.nome = entry['nome']
        nome_agencia_digital = entry['agencia_digital']
        agencia_digital = db.session.query(AgenciaDigital).filter(AgenciaDigital.nome==nome_agencia_digital).first()
        empregado.agencia_digital = agencia_digital
        db.session.add(empregado)

    tipos_atendimento_text = [
        {"nome":"Atendimento"},
        {"nome":"Contratação"},
        {"nome":"Cancelamento"}
    ]

    for entry in tipos_atendimento_text:
        tipo = TipoAtendimento()
        tipo.nome = entry['nome']
        db.session.add(tipo)


    tipos_produto_text = [
        {"nome":"Serviços"},
        {"nome":"Crédito"},
        {"nome":"Investimentos"},
        {"nome":"Caixa Seguridade"}
    ]

    for entry in tipos_produto_text:
        tipo = TipoProduto()
        tipo.nome = entry['nome']
        db.session.add(tipo)

    produtos_text = [
        {"nome":"CDB","tipo":"Investimentos"},
        {"nome":"LCI","tipo":"Investimentos"},
        {"nome":"Fundos","tipo":"Investimentos"},
        {"nome":"Poupança","tipo":"Investimentos"},
        {"nome":"CROT","tipo":"Crédito"},
        {"nome":"Consignado","tipo":"Crédito"},
        {"nome":"CDC","tipo":"Crédito"},
        {"nome":"Crédito Pessoal","tipo":"Crédito"},
        {"nome":"Habitação","tipo":"Crédito"},
        {"nome":"Capitalização","tipo":"Caixa Seguridade"},
        {"nome":"Consórcio","tipo":"Caixa Seguridade"},
        {"nome":"Previdência","tipo":"Caixa Seguridade"},
        {"nome":"Seguro Auto","tipo":"Caixa Seguridade"},
        {"nome":"Prestamista","tipo":"Caixa Seguridade"},
        {"nome":"Seguro Vida","tipo":"Caixa Seguridade"},
        {"nome":"Seguro Residencial","tipo":"Caixa Seguridade"},
        {"nome":"Cartão de Crédito","tipo":"Serviços"},
        {"nome":"Assinatura Eletrônica","tipo":"Serviços"},
        {"nome":"Cartão de Débito","tipo":"Serviços"},
        {"nome":"Cesta de Serviços","tipo":"Serviços"},
        {"nome":"Débito Automático","tipo":"Serviços"},
        {"nome":"Limite de Canais","tipo":"Serviços"},
        {"nome":"Regularização de CPF","tipo":"Serviços"}
    ]

    for entry in produtos_text:
        nome_tipo = entry['tipo']
        tipo = db.session.query(TipoProduto).filter(TipoProduto.nome==nome_tipo).first()
        produto = Produto()
        produto.nome = entry['nome']
        produto.tipo_produto = tipo
        db.session.add(produto)

    db.session.commit()
    return


# Flask views
@app.route('/')
def index():
    return redirect(url_for("admin.index"))


if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True, host='0.0.0.0', port=5007)
