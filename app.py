import os
import os.path as op
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, Blueprint
import flask_admin as admin
from flask_admin.contrib.sqla import ModelView
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


class TipoProduto(db.Model):
    __tablename__ = "tipo_produto"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), unique=True)

    def __repr__(self):
        return self.nome


class Atendimento(db.Model):
    __tablename__ = "atendimento"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dt_atendimento = db.Column(db.DateTime())

    empregado_id = db.Column(db.Integer, db.ForeignKey('empregado.id'))
    empregado = db.relationship("Empregado")
    co_agencia = db.Column(db.String(4), unique=False)
    cpf_cliente = db.Column(db.String(11), unique=False)
    nome_cliente = db.Column(db.String(200), unique=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    produto = db.relationship("Produto")
    tipo_atendimento_id = db.Column(db.Integer, db.ForeignKey('tipo_atendimento.id'))
    tipo_atendimento = db.relationship("TipoAtendimento")
    valor = db.Column(db.Float, primary_key=False, nullable=True)
    quantidade = db.Column(db.Integer, primary_key=False, nullable=True)
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


# Flask views
@app.route('/')
def index():
    return render_template('main/home.html')


# Create admin with custom base template
admin = admin.Admin(
    app, 'Example: Layout-BS3',
    base_template='layout.html',
    template_mode='bootstrap3'
)

# Add views
admin.add_view(UserAdmin(User, db.session))
admin.add_view(CustomView(Empregado, db.session))
admin.add_view(CustomView(Produto, db.session))
admin.add_view(CustomView(TipoProduto, db.session))
admin.add_view(CustomView(TipoAtendimento, db.session))
admin.add_view(AtendimentoView(Atendimento, db.session))


def build_sample_db():
    """
    Populate a small db with some example entries.
    """
    db.drop_all()
    db.create_all()

    empregados_text = [
        {"matricula":"c054271","nome":"Marcelle Christiane Silva Gordon"},
        {"matricula":"c133652","nome":"Fernanda Silvério Bergamasco"},
        {"matricula":"c090762","nome":"Rodrigo Prado de Jesus"},
        {"matricula":"c076590","nome":"Diana de Paula Neves"},
        {"matricula":"c072195","nome":"Luciana Queiroz Pinto Marques"},
        {"matricula":"c099339","nome":"Maria de Fatima Ferreira"},
        {"matricula":"c107332","nome":"Aline de Freitas Valim"},
        {"matricula":"c128490","nome":"Edjane Sarai Oliveira Garcia"},
        {"matricula":"c137557","nome":"Ana Natalia Paz de Andrade"},
        {"matricula":"c125852","nome":"Susiane Felix Casagrande Nishizawa"},
        {"matricula":"c140422","nome":"Vanessa Martins Luongo"}
    ]

    for entry in empregados_text:
        empregado = Empregado()
        empregado.matricula = entry['matricula']
        empregado.nome = entry['nome']
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
        {"nome":"CDB"},
        {"nome":"LCI"},
        {"nome":"FUNDOS"},
        {"nome":"POUPANÇA"},
        {"nome":"CROT"},
        {"nome":"CONSIGNADO"},
        {"nome":"CDC"},
        {"nome":"CRÉDITO PESSOAL"},
        {"nome":"HABITAÇÃO"},
        {"nome":"CAPITALIZAÇÃO"},
        {"nome":"CONSÓRCIO"},
        {"nome":"PREVIDÊNCIA"},
        {"nome":"SEGURO AUTO"},
        {"nome":"PRESTAMISTA"},
        {"nome":"SEGURO VIDA"},
        {"nome":"SEGURO RESIDENCIAL"},
        {"nome":"CARTÃO DE CRÉDITO"},
        {"nome":"ASSINATURA ELETRÔNICA"},
        {"nome":"CARTÃO DE DÉBITO"},
        {"nome":"CESTA DE SERVIÇOS"},
        {"nome":"DÉBITO AUTOMÁTICO"},
        {"nome":"LIMITE DE CANAIS"},
        {"nome":"REGULARIZAÇÃO DE CPF"}
    ]

    for entry in produtos_text:
        produto = Produto()
        produto.nome = entry['nome']
        produto.tipo_produto_id = 1
        db.session.add(produto)


    db.session.commit()
    return

if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

    # Start app
    app.run(debug=True, host='0.0.0.0', port=5007)