"""
═══════════════════════════════════════════════════════════════
  PROJETO MIRAI - Backend
  Gestão Inteligente de Impacto Visual
═══════════════════════════════════════════════════════════════

Como rodar localmente:
  1. pip install -r requirements.txt
  2. python app.py
  3. Abrir http://localhost:5000 no navegador

Variáveis de ambiente (produção):
  SECRET_KEY  — chave JWT, obrigatória em produção
"""

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
import sqlite3
import os

# ────────────────────────────────────────────────────────────
#  CAMINHOS
# ────────────────────────────────────────────────────────────

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'docs')
DATABASE     = os.path.join(BASE_DIR, 'mirai.db')

# ────────────────────────────────────────────────────────────
#  CONFIGURAÇÃO
# ────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

app.config['SECRET_KEY']           = os.environ.get('SECRET_KEY', 'mirai-dev-secret-change-in-prod')
app.config['TOKEN_EXPIRATION_DAYS'] = 7

# Permite requisições do GitHub Pages e do localhost em dev
CORS(app, origins=[
    r'http://localhost(:\d+)?',
    r'http://127\.0\.0\.1(:\d+)?',
    r'https://.*\.github\.io',
], supports_credentials=False)


# ────────────────────────────────────────────────────────────
#  BANCO DE DADOS
# ────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    schema_path = os.path.join(BASE_DIR, 'schema.sql')
    conn = sqlite3.connect(DATABASE)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f'✓ Banco de dados pronto: {DATABASE}')


# ────────────────────────────────────────────────────────────
#  AUTENTICAÇÃO (JWT)
# ────────────────────────────────────────────────────────────

def gerar_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email':   email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            days=app.config['TOKEN_EXPIRATION_DAYS']
        ),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth  = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''

        if not token:
            return jsonify({'error': 'Token ausente'}), 401

        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Sessão expirada'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated


# ────────────────────────────────────────────────────────────
#  ROTAS DE PÁGINAS (desenvolvimento local)
# ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/login.html')
@app.route('/login')
def login_page():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/mirai.html')
@app.route('/mirai')
def mirai_page():
    return send_from_directory(FRONTEND_DIR, 'mirai.html')

@app.route('/register.html')
@app.route('/register')
def register_page():
    return send_from_directory(FRONTEND_DIR, 'register.html')


# ────────────────────────────────────────────────────────────
#  API - AUTENTICAÇÃO
# ────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def api_register():
    data     = request.get_json() or {}
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '')
    name     = (data.get('name')     or '').strip()

    if not email or '@' not in email:
        return jsonify({'error': 'E-mail inválido'}), 400
    if len(password) < 6:
        return jsonify({'error': 'A senha precisa ter no mínimo 6 caracteres'}), 400
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    db = get_db()
    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return jsonify({'error': 'E-mail já cadastrado'}), 409

    password_hash = generate_password_hash(password)
    cursor = db.execute(
        'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
        (email, password_hash, name)
    )
    db.commit()

    user_id = cursor.lastrowid
    token   = gerar_token(user_id, email)

    return jsonify({
        'message': 'Cadastro realizado com sucesso',
        'token':   token,
        'user':    {'id': user_id, 'email': email, 'name': name}
    }), 201


@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json() or {}
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '')

    if not email or not password:
        return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400

    db   = get_db()
    user = db.execute(
        'SELECT id, email, password_hash, name FROM users WHERE email = ?', (email,)
    ).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'E-mail ou senha inválidos'}), 401

    db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    db.commit()

    token = gerar_token(user['id'], user['email'])
    return jsonify({
        'token': token,
        'user':  {'id': user['id'], 'email': user['email'], 'name': user['name']}
    })


@app.route('/api/me', methods=['GET'])
@token_required
def api_me(current_user_id):
    db   = get_db()
    user = db.execute(
        'SELECT id, email, name, created_at, last_login FROM users WHERE id = ?',
        (current_user_id,)
    ).fetchone()

    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    return jsonify(dict(user))


@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify({'message': 'Logout efetuado'})


# ────────────────────────────────────────────────────────────
#  API - DADOS
# ────────────────────────────────────────────────────────────

@app.route('/api/indicadores', methods=['GET'])
@token_required
def api_indicadores(current_user_id):
    return jsonify({
        'ocorrencias':       847,
        'areas_afetadas_pct': 72,
        'municipios':        5568,
        'variacao_anual_pct': 8,
    })


# ────────────────────────────────────────────────────────────
#  ERROR HANDLERS
# ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Erro interno do servidor'}), 500


# ────────────────────────────────────────────────────────────
#  STARTUP — inicializa banco (funciona com gunicorn e direto)
# ────────────────────────────────────────────────────────────

with app.app_context():
    init_db()


# ────────────────────────────────────────────────────────────
#  MAIN
# ────────────────────────────────────────────────────────────

if __name__ == '__main__':

    print('╔════════════════════════════════════════════════╗')
    print('║   PROJETO MIRAI - Backend em execução          ║')
    print('║   http://localhost:5000                        ║')
    print('╚════════════════════════════════════════════════╝')

    app.run(debug=True, host='0.0.0.0', port=5000)
