import hashlib
import psycopg2
from psycopg2 import pool
from psycopg2 import IntegrityError
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Banco de Fatos Observados",
    page_icon="📋",
    layout="centered",
)


# ============================================================
# CONEXÃO COM POSTGRESQL / SUPABASE
# ============================================================

@st.cache_resource(show_spinner=False)
def obter_pool():
    return pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=5,
        dsn=st.secrets["DATABASE_URL"],
    )


def conectar_banco():
    return obter_pool().getconn()


def devolver_conexao(conn):
    if conn is not None:
        try:
            obter_pool().putconn(conn)
        except Exception:
            pass


def executar(query, params=()):
    conn = None

    try:
        conn = conectar_banco()

        with conn.cursor() as cursor:
            cursor.execute(query, params)

        conn.commit()
        return True

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise

    finally:
        devolver_conexao(conn)


def consultar(query, params=()):
    conn = None

    try:
        conn = conectar_banco()

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            resultado = cursor.fetchall()

        conn.rollback()
        return resultado

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise

    finally:
        devolver_conexao(conn)


def consultar_um(query, params=()):
    conn = None

    try:
        conn = conectar_banco()

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            resultado = cursor.fetchone()

        conn.rollback()
        return resultado

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise

    finally:
        devolver_conexao(conn)


# ============================================================
# BANCO DE DADOS
# ============================================================

def criar_banco():
    conn = None

    try:
        conn = conectar_banco()

        with conn.cursor() as cursor:

            # Tabela de Usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id BIGSERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL DEFAULT 'fiscalizador',
                    ativo BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)

            # Tabela de Pelotões
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pelotoes (
                    id BIGSERIAL PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE
                )
            """)

            # Tabela de Militares
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS militares (
                    id BIGSERIAL PRIMARY KEY,
                    qra TEXT NOT NULL,
                    posto_graduacao TEXT NOT NULL,
                    pelotao_id BIGINT NOT NULL
                    REFERENCES pelotoes(id)
                )
            """)

            # Tabela de Fatos Observados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fatos_observados (
                    id BIGSERIAL PRIMARY KEY,
                    militar_id BIGINT NOT NULL
                    REFERENCES militares(id),
                    usuario_id BIGINT NOT NULL
                    REFERENCES usuarios(id),
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    data_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Índices para acelerar as consultas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_militares_pelotao
                ON militares(pelotao_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fatos_militar
                ON fatos_observados(militar_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fatos_usuario
                ON fatos_observados(usuario_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fatos_data
                ON fatos_observados(data_registro)
            """)

        conn.commit()

    finally:
        devolver_conexao(conn)


# ============================================================
# USUÁRIOS INICIAIS
# ============================================================

def gerar_hash(senha):
    return hashlib.sha256(
        senha.encode("utf-8")
    ).hexdigest()


def criar_usuarios_iniciais():
    senha_padrao_hash = gerar_hash("123456")

    usuarios = [
        ("Administrador", "admin", "administrador"),
        ("Cad PM Alan", "alan", "fiscalizador"),
        ("Cad PM Ana Beatriz", "anabeatriz", "fiscalizador"),
        ("Cad PM Buosi", "buosi", "fiscalizador"),
        ("Cad PM Burgese", "burgese", "fiscalizador"),
        ("Cad PM Corte", "corte", "fiscalizador"),
        ("Cad PM Ganiprauskas", "ganiprauskas", "fiscalizador"),
        ("Cad PM Garcia", "garcia", "fiscalizador"),
        ("Cad PM Hamad", "hamad", "fiscalizador"),
        ("Cad PM Hélio", "helio", "fiscalizador"),
        ("Cad PM Jhonny Amaral", "jhonnyamaral", "fiscalizador"),
        ("Cad PM Lins", "lins", "fiscalizador"),
        ("Cad PM Luiz Santiago", "luizsantiago", "fiscalizador"),
        ("Cad PM Machado Marques", "machadomarques", "fiscalizador"),
        ("Cad PM Marques", "marques", "fiscalizador"),
        ("Cad PM Mello Araújo", "melloaraujo", "fiscalizador"),
        ("Cad PM Nobrega", "nobrega", "fiscalizador"),
        ("Cad PM Nogueira", "nogueira", "fiscalizador"),
        ("Cad PM Pardim", "pardim", "fiscalizador"),
        ("Cad PM Pedro Barros", "pedrobarros", "fiscalizador"),
        ("Cad PM Prestes", "prestes", "fiscalizador"),
        ("Cad PM Rafaela", "rafaela", "fiscalizador"),
        ("Cad PM Rhianny", "rhianny", "fiscalizador"),
        ("Cad PM Salgado", "salgado", "fiscalizador"),
        ("Cad PM Tasso", "tasso", "fiscalizador"),
        ("Cad PM Thiago Vieira", "thiagovieira", "fiscalizador"),
        ("Cad PM Topasso", "topasso", "fiscalizador"),
        ("Cad PM Vanessa", "vanessa", "fiscalizador"),
        ("Cad PM Vilela Alves", "vilelaalves", "fiscalizador"),
        ("Cad PM Vinicius Melo", "viniciusmelo", "fiscalizador"),
        ("Cad PM William Fabro", "williamfabro", "fiscalizador"),
    ]

    conn = None

    try:
        conn = conectar_banco()

        with conn.cursor() as cursor:
            for nome, login, perfil in usuarios:
                cursor.execute(
                    """
                    INSERT INTO usuarios
                        (nome, login, senha_hash, perfil)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (login) DO NOTHING
                    """,
                    (
                        nome,
                        login,
                        senha_padrao_hash,
                        perfil,
                    ),
                )

        conn.commit()

    finally:
        devolver_conexao(conn)


# ============================================================
# CACHE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def listar_usuarios():
    return consultar("""
        SELECT id, nome, login, perfil
        FROM usuarios
        ORDER BY nome ASC
    """)


@st.cache_data(ttl=60, show_spinner=False)
def listar_pelotoes():
    return consultar("""
        SELECT id, nome
        FROM pelotoes
        ORDER BY nome ASC
    """)


@st.cache_data(ttl=60, show_spinner=False)
def listar_militares(pelotao_id=None):

    if pelotao_id:
        return consultar(
            """
            SELECT
                m.id,
                m.posto_graduacao,
                m.qra,
                p.nome
            FROM militares m
            JOIN pelotoes p
                ON m.pelotao_id = p.id
            WHERE m.pelotao_id = %s
            ORDER BY m.qra ASC
            """,
            (pelotao_id,),
        )

    return consultar("""
        SELECT
            m.id,
            m.posto_graduacao,
            m.qra,
            p.nome
        FROM militares m
        JOIN pelotoes p
            ON m.pelotao_id = p.id
        ORDER BY p.nome ASC, m.qra ASC
    """)


@st.cache_data(ttl=60, show_spinner=False)
def listar_fatos(militar_id=None, pelotao_id=None):

    query = """
        SELECT
            f.id,
            f.tipo,
            f.descricao,
            f.data_registro,
            m.posto_graduacao,
            m.qra,
            p.nome,
            u.nome,
            f.usuario_id
        FROM fatos_observados f
        JOIN militares m
            ON f.militar_id = m.id
        JOIN pelotoes p
            ON m.pelotao_id = p.id
        JOIN usuarios u
            ON f.usuario_id = u.id
    """

    conditions = []
    params = []

    if militar_id:
        conditions.append("f.militar_id = %s")
        params.append(militar_id)

    elif pelotao_id:
        conditions.append("m.pelotao_id = %s")
        params.append(pelotao_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY f.data_registro DESC"

    return consultar(query, tuple(params))


def limpar_cache():
    listar_usuarios.clear()
    listar_pelotoes.clear()
    listar_militares.clear()
    listar_fatos.clear()


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def autenticar_usuario(login, senha):

    senha_hash = gerar_hash(senha)

    return consultar_um(
        """
        SELECT id, nome, login, perfil
        FROM usuarios
        WHERE login = %s
          AND senha_hash = %s
          AND ativo = TRUE
        """,
        (
            login,
            senha_hash,
        ),
    )


def atualizar_senha(usuario_id, nova_senha):

    try:
        nova_senha_hash = gerar_hash(nova_senha)

        executar(
            """
            UPDATE usuarios
            SET senha_hash = %s
            WHERE id = %s
            """,
            (
                nova_senha_hash,
                usuario_id,
            ),
        )

        return True, "Senha alterada com sucesso!"

    except Exception as e:
        return False, f"Erro ao alterar senha: {e}"


def resetar_senha_por_login(login):

    try:
        senha_padrao_hash = gerar_hash("123456")

        usuario = consultar_um(
            """
            SELECT id, nome
            FROM usuarios
            WHERE login = %s
            """,
            (login,),
        )

        if not usuario:
            return False, "Usuário não encontrado no sistema."

        executar(
            """
            UPDATE usuarios
            SET senha_hash = %s
            WHERE login = %s
            """,
            (
                senha_padrao_hash,
                login,
            ),
        )

        return (
            True,
            f"Senha do usuário **{usuario[1]}** "
            "redefinida para o padrão: **123456**",
        )

    except Exception as e:
        return False, f"Erro ao resetar senha: {e}"


# ============================================================
# PELOTÕES
# ============================================================

def salvar_pelotao(nome):

    try:
        executar(
            """
            INSERT INTO pelotoes (nome)
            VALUES (%s)
            """,
            (nome,),
        )

        limpar_cache()

        return True, "Pelotão cadastrado com sucesso!"

    except IntegrityError:
        return False, "Este pelotão já está cadastrado."

    except Exception as e:
        return False, f"Erro ao cadastrar: {e}"


def deletar_pelotao(pelotao_id):

    try:
        vinculados = consultar_um(
            """
            SELECT COUNT(*)
            FROM militares
            WHERE pelotao_id = %s
            """,
            (pelotao_id,),
        )[0]

        if vinculados > 0:
            return (
                False,
                f"Não é possível excluir: existem "
                f"{vinculados} subordinado(s) "
                "vinculado(s) a este pelotão.",
            )

        executar(
            """
            DELETE FROM pelotoes
            WHERE id = %s
            """,
            (pelotao_id,),
        )

        limpar_cache()

        return True, "Pelotão excluído com sucesso!"

    except Exception as e:
        return False, f"Erro ao excluir pelotão: {e}"


# ============================================================
# MILITARES / SUBORDINADOS
# ============================================================

def salvar_militar(qra, posto_graduacao, pelotao_id):

    try:
        executar(
            """
            INSERT INTO militares
                (qra, posto_graduacao, pelotao_id)
            VALUES (%s, %s, %s)
            """,
            (
                qra,
                posto_graduacao,
                pelotao_id,
            ),
        )

        limpar_cache()

        return True, "Subordinado cadastrado com sucesso!"

    except Exception as e:
        return False, f"Erro ao cadastrar subordinado: {e}"


def deletar_militar(militar_id):

    try:
        qtd_fatos = consultar_um(
            """
            SELECT COUNT(*)
            FROM fatos_observados
            WHERE militar_id = %s
            """,
            (militar_id,),
        )[0]

        if qtd_fatos > 0:
            return (
                False,
                f"Não é possível excluir: existem "
                f"{qtd_fatos} fato(s) registrado(s) "
                "para este subordinado.",
            )

        executar(
            """
            DELETE FROM militares
            WHERE id = %s
            """,
            (militar_id,),
        )

        limpar_cache()

        return True, "Subordinado excluído com sucesso!"

    except Exception as e:
        return False, f"Erro ao excluir subordinado: {e}"


# ============================================================
# FATOS OBSERVADOS
# ============================================================

def salvar_fato(
    militar_id,
    usuario_id,
    tipo,
    descricao,
):

    try:
        executar(
            """
            INSERT INTO fatos_observados
                (
                    militar_id,
                    usuario_id,
                    tipo,
                    descricao
                )
            VALUES (%s, %s, %s, %s)
            """,
            (
                militar_id,
                usuario_id,
                tipo,
                descricao,
            ),
        )

        limpar_cache()

        return (
            True,
            "Fato observado registrado com sucesso!",
        )

    except Exception as e:
        return (
            False,
            f"Erro ao registrar fato: {e}",
        )


def deletar_fato(fato_id):

    try:
        executar(
            """
            DELETE FROM fatos_observados
            WHERE id = %s
            """,
            (fato_id,),
        )

        limpar_cache()

        return (
            True,
            "Fato observado excluído com sucesso!",
        )

    except Exception as e:
        return (
            False,
            f"Erro ao excluir fato: {e}",
        )


# ============================================================
# LOGIN
# ============================================================

def tela_login():

    st.title("📋 Banco de Fatos Observados")
    st.subheader("Sistema de Registro de Condutas")
    st.divider()

    st.markdown("### 🔐 Acesso ao sistema")

    with st.form("form_login"):

        login = st.text_input(
            "Usuário",
            placeholder="Digite seu usuário",
        )

        senha = st.text_input(
            "Senha",
            type="password",
            placeholder="Digite sua senha",
        )

        entrar = st.form_submit_button(
            "ENTRAR",
            use_container_width=True,
            type="primary",
        )

    if entrar:

        if not login or not senha:
            st.error(
                "Informe o usuário e a senha."
            )

        else:

            usuario = autenticar_usuario(
                login.strip().lower(),
                senha,
            )

            if usuario:

                st.session_state["autenticado"] = True

                st.session_state["usuario"] = {
                    "id": usuario[0],
                    "nome": usuario[1],
                    "login": usuario[2],
                    "perfil": usuario[3],
                }

                st.session_state["pagina"] = "dashboard"

                st.rerun()

            else:
                st.error(
                    "Usuário ou senha incorretos."
                )

    st.divider()

    if st.button(
        "🔑 Esqueci minha senha",
        use_container_width=True,
    ):
        st.session_state["pagina"] = "esqueci_senha"
        st.rerun()


# ============================================================
# RECUPERAÇÃO DE SENHA
# ============================================================

def tela_esqueci_senha():

    st.title("🔑 Recuperação de Senha")
    st.divider()

    st.info(
        "Informe o seu usuário cadastrado. "
        "A solicitação será direcionada ao "
        "Administrador do sistema para que a "
        "senha seja redefinida para o padrão "
        "inicial (**123456**)."
    )

    with st.form("form_esqueci_senha"):

        login_rec = st.text_input(
            "Usuário Cadastrado",
            placeholder="Ex: alan, anabeatriz...",
        )

        solicitar = st.form_submit_button(
            "Solicitar Redefinição ao Administrador",
            type="primary",
            use_container_width=True,
        )

    if solicitar:

        if not login_rec.strip():

            st.warning(
                "Informe o seu usuário."
            )

        else:

            user_encontrado = consultar_um(
                """
                SELECT id, nome
                FROM usuarios
                WHERE login = %s
                """,
                (
                    login_rec.strip().lower(),
                ),
            )

            if user_encontrado:

                st.success(
                    f"Solicitação registrada para "
                    f"**{user_encontrado[1]}**. "
                    "Avise o Administrador (`admin`) "
                    "para efetivar o reset para a senha "
                    "padrão **123456**."
                )

            else:

                st.error(
                    "Usuário não encontrado na base de dados."
                )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Login",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "login"
        st.rerun()


# ============================================================
# TROCA DE SENHA
# ============================================================

def tela_trocar_senha():

    st.title("🔑 Alterar Minha Senha")
    st.divider()

    with st.form("form_trocar_senha"):

        senha_atual = st.text_input(
            "Senha Atual",
            type="password",
            placeholder="Digite sua senha atual",
        )

        nova_senha = st.text_input(
            "Nova Senha",
            type="password",
            placeholder="Digite a nova senha",
        )

        confirma_senha = st.text_input(
            "Confirmar Nova Senha",
            type="password",
            placeholder="Digite a nova senha novamente",
        )

        salvar = st.form_submit_button(
            "Salvar Nova Senha",
            type="primary",
            use_container_width=True,
        )

    if salvar:

        if (
            not senha_atual
            or not nova_senha
            or not confirma_senha
        ):

            st.warning(
                "Preencha todos os campos."
            )

        elif nova_senha != confirma_senha:

            st.error(
                "A nova senha e a confirmação não conferem."
            )

        else:

            usuario_id = st.session_state[
                "usuario"
            ]["id"]

            login_atual = st.session_state[
                "usuario"
            ]["login"]

            if autenticar_usuario(
                login_atual,
                senha_atual,
            ):

                sucesso, msg = atualizar_senha(
                    usuario_id,
                    nova_senha,
                )

                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

            else:

                st.error(
                    "A senha atual informada está incorreta."
                )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# CADASTRAR PELOTÃO
# ============================================================

def tela_cadastrar_pelotao():

    st.title("👥 Cadastrar Pelotão")
    st.divider()

    with st.form("form_cadastrar_pelotao"):

        nome_pelotao = st.text_input(
            "Nome do Pelotão",
            placeholder="Ex: 1º Pelotão",
        )

        salvar = st.form_submit_button(
            "Salvar Pelotão",
            type="primary",
            use_container_width=True,
        )

    if salvar:

        if nome_pelotao.strip():

            sucesso, msg = salvar_pelotao(
                nome_pelotao.strip()
            )

            if sucesso:
                st.success(msg)
            else:
                st.error(msg)

        else:

            st.warning(
                "Informe o nome do pelotão."
            )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# CONSULTAR PELOTÕES
# ============================================================

def tela_consultar_pelotao():

    st.title("👥 Pelotões Cadastrados")
    st.divider()

    pelotoes = listar_pelotoes()

    if pelotoes:

        for p in pelotoes:

            col1, col2 = st.columns([3, 1])

            with col1:

                st.markdown(
                    f"• **{p[1]}** "
                    f"*(ID: {p[0]})*"
                )

            with col2:

                if st.button(
                    "🗑️ Excluir",
                    key=f"del_pel_{p[0]}",
                    use_container_width=True,
                ):

                    sucesso, msg = deletar_pelotao(
                        p[0]
                    )

                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    else:

        st.info(
            "Nenhum pelotão cadastrado ainda."
        )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# CADASTRAR SUBORDINADO
# ============================================================

def tela_cadastrar_subordinado():

    st.title("👮 Cadastrar Subordinado")
    st.divider()

    pelotoes = listar_pelotoes()

    if not pelotoes:

        st.warning(
            "É necessário cadastrar ao menos "
            "um Pelotão antes de cadastrar "
            "subordinados."
        )

    else:

        opcoes_pelotao = {
            p[1]: p[0]
            for p in pelotoes
        }

        with st.form("form_cadastrar_subordinado"):

            pelotao_selecionado = st.selectbox(
                "Pelotão",
                list(opcoes_pelotao.keys()),
            )

            posto_grad = st.selectbox(
                "Posto / Graduação",
                [
                    "Cad PM",
                    "Sd 2ª Cl PM",
                    "Sd 1ª Cl PM",
                    "Cb PM",
                    "3º Sgt PM",
                    "2º Sgt PM",
                    "1º Sgt PM",
                    "Subten PM",
                    "2º Ten PM",
                    "1º Ten PM",
                    "Cap PM",
                ],
            )

            qra = st.text_input(
                "QRA (Nome de Guerra)",
                placeholder="Ex: Silva",
            )

            salvar = st.form_submit_button(
                "Salvar Subordinado",
                type="primary",
                use_container_width=True,
            )

        if salvar:

            if qra.strip():

                pelotao_id = opcoes_pelotao[
                    pelotao_selecionado
                ]

                sucesso, msg = salvar_militar(
                    qra.strip(),
                    posto_grad,
                    pelotao_id,
                )

                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

            else:

                st.warning(
                    "Informe o QRA (Nome de guerra)."
                )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# CONSULTAR SUBORDINADOS
# ============================================================

def tela_consultar_subordinado():

    st.title("👮 Subordinados Cadastrados")
    st.divider()

    militares = listar_militares()

    if militares:

        for m in militares:

            col1, col2 = st.columns([3, 1])

            with col1:

                st.markdown(
                    f"• **{m[1]} {m[2]}** "
                    f"— *{m[3]}*"
                )

            with col2:

                if st.button(
                    "🗑️ Excluir",
                    key=f"del_sub_{m[0]}",
                    use_container_width=True,
                ):

                    sucesso, msg = deletar_militar(
                        m[0]
                    )

                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    else:

        st.info(
            "Nenhum subordinado cadastrado ainda."
        )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# GERENCIAR SENHAS
# ============================================================

def tela_gerenciar_senhas():

    st.title("🛠️ Gerenciar Senhas de Usuários")
    st.divider()

    st.markdown(
        "Como Administrador, você pode redefinir "
        "a senha de qualquer usuário para o padrão "
        "inicial (**123456**)."
    )

    usuarios = listar_usuarios()

    if usuarios:

        opcoes_usuarios = {
            f"{u[1]} ({u[2]}) — Perfil: {u[3]}": u[2]
            for u in usuarios
        }

        user_sel = st.selectbox(
            "Selecione o Usuário para Resetar Senha",
            list(opcoes_usuarios.keys()),
        )

        login_alvo = opcoes_usuarios[
            user_sel
        ]

        if st.button(
            "🔄 Redefinir Senha para 123456",
            type="primary",
            use_container_width=True,
        ):

            sucesso, msg = resetar_senha_por_login(
                login_alvo
            )

            if sucesso:
                st.success(msg)
            else:
                st.error(msg)

    else:

        st.info(
            "Nenhum usuário encontrado."
        )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# REGISTRAR FATO
# ============================================================

def tela_registrar_fato():

    st.title("📝 Registrar Fato Observado")
    st.divider()

    pelotoes = listar_pelotoes()

    if not pelotoes:

        st.warning(
            "É necessário cadastrar ao menos "
            "um Pelotão primeiro."
        )

    else:

        opcoes_pelotao = {
            p[1]: p[0]
            for p in pelotoes
        }

        # Fica fora do formulário para que,
        # ao trocar o pelotão, a lista de militares
        # seja atualizada imediatamente.
        pelotao_selecionado = st.selectbox(
            "1. Selecione o Pelotão",
            list(opcoes_pelotao.keys()),
        )

        pelotao_id = opcoes_pelotao[
            pelotao_selecionado
        ]

        militares = listar_militares(
            pelotao_id
        )

        if not militares:

            st.info(
                f"Nenhum subordinado cadastrado "
                f"no {pelotao_selecionado}."
            )

        else:

            opcoes_militar = {
                f"{m[1]} {m[2]}": m[0]
                for m in militares
            }

            with st.form("form_registrar_fato"):

                militar_selecionado = st.selectbox(
                    "2. Selecione o Subordinado (QRA)",
                    list(opcoes_militar.keys()),
                )

                tipo_fato = st.radio(
                    "3. Classificação da Conduta",
                    [
                        "🔵 Elogiável / Positiva",
                        "🟡 Neutra / Observação",
                        "🔴 A Melhorar / Relevante",
                    ],
                )

                descricao = st.text_area(
                    "4. Fato Observado "
                    "(Descreva a conduta com clareza)",
                    placeholder=(
                        "Ex: Durante a instrução de "
                        "ordem unida, demonstrou "
                        "excepcional liderança e postura..."
                    ),
                    height=150,
                )

                registrar = st.form_submit_button(
                    "💾 Registrar Fato Observado",
                    type="primary",
                    use_container_width=True,
                )

            if registrar:

                if descricao.strip():

                    militar_id = opcoes_militar[
                        militar_selecionado
                    ]

                    usuario_id = st.session_state[
                        "usuario"
                    ]["id"]

                    sucesso, msg = salvar_fato(
                        militar_id,
                        usuario_id,
                        tipo_fato,
                        descricao.strip(),
                    )

                    if sucesso:
                        st.success(msg)
                    else:
                        st.error(msg)

                else:

                    st.warning(
                        "Escreva a descrição do fato "
                        "observado antes de salvar."
                    )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# CONSULTA GERAL DE FATOS
# ============================================================

def tela_consultar_fatos():

    st.title("🔍 Consulta Geral de Fatos")
    st.divider()

    pelotoes = listar_pelotoes()

    if not pelotoes:

        st.info(
            "Nenhum pelotão cadastrado para consulta."
        )

    else:

        opcoes_pelotao = {
            "Todos os Pelotões": None
        }

        for p in pelotoes:
            opcoes_pelotao[p[1]] = p[0]

        pelotao_sel = st.selectbox(
            "Filtrar por Pelotão",
            list(opcoes_pelotao.keys()),
        )

        pelotao_id = opcoes_pelotao[
            pelotao_sel
        ]

        militares = (
            listar_militares(pelotao_id)
            if pelotao_id
            else listar_militares()
        )

        opcoes_militar = {
            "Todos os Subordinados": None
        }

        for m in militares:

            opcoes_militar[
                f"{m[1]} {m[2]} ({m[3]})"
            ] = m[0]

        militar_sel = st.selectbox(
            "Filtrar por Subordinado",
            list(opcoes_militar.keys()),
        )

        militar_id = opcoes_militar[
            militar_sel
        ]

        st.divider()

        fatos = listar_fatos(
            militar_id=militar_id,
            pelotao_id=pelotao_id,
        )

        if fatos:

            elogiaveis = sum(
                1 for f in fatos
                if "🔵" in f[1]
            )

            neutras = sum(
                1 for f in fatos
                if "🟡" in f[1]
            )

            a_melhorar = sum(
                1 for f in fatos
                if "🔴" in f[1]
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "🔵 Elogiáveis",
                elogiaveis,
            )

            c2.metric(
                "🟡 Neutras",
                neutras,
            )

            c3.metric(
                "🔴 A Melhorar",
                a_melhorar,
            )

            st.markdown(
                "### 📋 Registros Encontrados"
            )

            usuario_atual = st.session_state[
                "usuario"
            ]

            for f in fatos:

                (
                    fato_id,
                    tipo,
                    desc,
                    data,
                    posto,
                    qra,
                    pel_nome,
                    autor,
                    autor_id,
                ) = f

                with st.expander(
                    f"{tipo} | {posto} {qra} "
                    f"({pel_nome}) — "
                    f"Data: {formatar_data(data)}"
                ):

                    st.markdown(
                        f"**Militar:** "
                        f"{posto} {qra} ({pel_nome})"
                    )

                    st.markdown(
                        f"**Registrado por:** {autor}"
                    )

                    st.markdown(
                        f"**Data:** {formatar_data_completa(data)}"
                    )

                    st.markdown(
                        f"**Descrição:**\n>{desc}"
                    )

                    if (
                        usuario_atual["perfil"]
                        == "administrador"
                        or usuario_atual["id"]
                        == autor_id
                    ):

                        st.divider()

                        if st.button(
                            "🗑️ Excluir Fato",
                            key=f"del_fato_{fato_id}",
                            type="secondary",
                        ):

                            sucesso, msg = deletar_fato(
                                fato_id
                            )

                            if sucesso:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        else:

            st.info(
                "Nenhum fato observado encontrado "
                "para os filtros selecionados."
            )

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# RELATÓRIO VISUAL
# ============================================================

def tela_relatorio_visual():

    st.title("📊 Relatório Visual por Militar")
    st.divider()

    pelotoes = listar_pelotoes()

    if not pelotoes:

        st.info(
            "Nenhum pelotão cadastrado."
        )

    else:

        opcoes_pelotao = {
            p[1]: p[0]
            for p in pelotoes
        }

        pelotao_sel = st.selectbox(
            "1. Selecione o Pelotão",
            list(opcoes_pelotao.keys()),
        )

        pelotao_id = opcoes_pelotao[
            pelotao_sel
        ]

        militares = listar_militares(
            pelotao_id
        )

        if not militares:

            st.info(
                f"Nenhum subordinado cadastrado "
                f"no {pelotao_sel}."
            )

        else:

            opcoes_militar = {
                f"{m[1]} {m[2]}":
                    (m[0], m[1], m[2])
                for m in militares
            }

            militar_sel = st.selectbox(
                "2. Selecione o Militar",
                list(opcoes_militar.keys()),
            )

            militar_id, posto, qra = (
                opcoes_militar[ militar_sel ]
            )

            fatos = listar_fatos(
                militar_id=militar_id
            )

            total_fatos = len(fatos)

            st.divider()

            st.markdown(
                f"### 🪪 Ficha Individual: "
                f"**{posto} {qra}**"
            )

            st.caption(
                f"Pelotão: {pelotao_sel} | "
                f"Total de Fatos Observados: "
                f"{total_fatos}"
            )

            if total_fatos == 0:

                st.info(
                    "Este militar ainda não possui "
                    "nenhum fato observado registrado."
                )

            else:

                elogiaveis = sum(
                    1 for f in fatos
                    if "🔵" in f[1]
                )

                neutras = sum(
                    1 for f in fatos
                    if "🟡" in f[1]
                )

                a_melhorar = sum(
                    1 for f in fatos
                    if "🔴" in f[1]
                )

                pct_elo = (
                    elogiaveis / total_fatos
                ) * 100

                pct_neu = (
                    neutras / total_fatos
                ) * 100

                pct_mel = (
                    a_melhorar / total_fatos
                ) * 100

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                col1.metric(
                    "Total",
                    total_fatos,
                )

                col2.metric(
                    "🔵 Elogiáveis",
                    elogiaveis,
                )

                col3.metric(
                    "🟡 Neutras",
                    neutras,
                )

                col4.metric(
                    "🔴 A Melhorar",
                    a_melhorar,
                )

                st.markdown("---")

                st.markdown(
                    "### 📈 Distribuição das Condutas"
                )

                st.markdown(
                    f"**🔵 Elogiável / Positiva:** "
                    f"{pct_elo:.1f}%"
                )

                st.progress(
                    pct_elo / 100
                )

                st.markdown(
                    f"**🟡 Neutra / Observação:** "
                    f"{pct_neu:.1f}%"
                )

                st.progress(
                    pct_neu / 100
                )

                st.markdown(
                    f"**🔴 A Melhorar / Relevante:** "
                    f"{pct_mel:.1f}%"
                )

                st.progress(
                    pct_mel / 100
                )

                st.markdown("---")

                st.markdown(
                    "### 📜 Linha do Tempo de Condutas"
                )

                for f in fatos:

                    tipo = f[1]
                    desc = f[2]
                    data = f[3]
                    autor = f[7]

                    st.markdown(
                        f"**{tipo}** — "
                        f"*{formatar_data(data)}* "
                        f"(Avaliador: {autor})"
                    )

                    st.info(desc)

    st.divider()

    if st.button(
        "⬅️ Voltar ao Dashboard",
        use_container_width=True,
    ):

        st.session_state["pagina"] = "dashboard"
        st.rerun()


# ============================================================
# FORMATAÇÃO DE DATAS
# ============================================================

def formatar_data(data):

    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")

    if data is None:
        return ""

    texto = str(data)

    if " " in texto:
        texto = texto.split(" ")[0]

    if "T" in texto:
        texto = texto.split("T")[0]

    partes = texto.split("-")

    if len(partes) == 3:
        return (
            f"{partes[2]}/"
            f"{partes[1]}/"
            f"{partes[0]}"
        )

    return texto


def formatar_data_completa(data):

    if hasattr(data, "strftime"):
        return data.strftime(
            "%d/%m/%Y %H:%M"
        )

    if data is None:
        return ""

    return str(data)


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    usuario = st.session_state[
        "usuario"
    ]

    st.title(
        "📋 Banco de Fatos Observados"
    )

    st.success(
        f"Bem-vindo, {usuario['nome']}!"
    )

    st.write(
        f"Perfil: **{usuario['perfil']}**"
    )

    st.divider()

    if usuario["perfil"] == "administrador":

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                "### 👥 PELOTÕES"
            )

            if st.button(
                "Cadastrar",
                key="cad_pelotao",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cad_pelotao"

                st.rerun()

            if st.button(
                "Consultar",
                key="cons_pelotao",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cons_pelotao"

                st.rerun()

        with col2:

            st.markdown(
                "### 👮 SUBORDINADOS"
            )

            if st.button(
                "Cadastrar",
                key="cad_sub",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cad_sub"

                st.rerun()

            if st.button(
                "Consultar",
                key="cons_sub",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cons_sub"

                st.rerun()

        with col3:

            st.markdown(
                "### 📝 FATOS & ANÁLISE"
            )

            if st.button(
                "Registrar fato",
                key="reg_fato",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "reg_fato"

                st.rerun()

            if st.button(
                "Consulta Geral",
                key="cons_fato",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cons_fato"

                st.rerun()

            if st.button(
                "📊 Relatório Visual",
                key="rel_visual",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "rel_visual"

                st.rerun()

        st.divider()

        if st.button(
            "🛠️ Painel Admin: "
            "Resetar Senhas de Usuários",
            use_container_width=True,
        ):

            st.session_state[
                "pagina"
            ] = "gerenciar_senhas"

            st.rerun()

    else:

        st.markdown(
            "### 📝 FATOS & ANÁLISE"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "Registrar fato",
                key="reg_fato",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "reg_fato"

                st.rerun()

        with col2:

            if st.button(
                "Consulta Geral",
                key="cons_fato",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "cons_fato"

                st.rerun()

        with col3:

            if st.button(
                "📊 Relatório Visual",
                key="rel_visual",
                use_container_width=True,
            ):

                st.session_state[
                    "pagina"
                ] = "rel_visual"

                st.rerun()

    st.divider()

    col_s1, col_s2 = st.columns(2)

    with col_s1:

        if st.button(
            "🔑 Trocar Senha",
            use_container_width=True,
        ):

            st.session_state[
                "pagina"
            ] = "trocar_senha"

            st.rerun()

    with col_s2:

        if st.button(
            "🚪 Sair",
            use_container_width=True,
        ):

            st.session_state.clear()
            st.rerun()


# ============================================================
# INICIALIZAÇÃO DO SISTEMA
# ============================================================

@st.cache_resource(show_spinner=False)
def inicializar_sistema():

    criar_banco()
    criar_usuarios_iniciais()

    return True


# Inicializa somente uma vez por execução
# do aplicativo, em vez de executar em
# todas as interações da tela.
inicializar_sistema()


# ============================================================
# ESTADO DA SESSÃO
# ============================================================

if "autenticado" not in st.session_state:

    st.session_state[
        "autenticado"
    ] = False


if "pagina" not in st.session_state:

    st.session_state[
        "pagina"
    ] = "login"


# ============================================================
# ROTEAMENTO
# ============================================================

if not st.session_state["autenticado"]:

    pagina_atual = st.session_state.get(
        "pagina",
        "login",
    )

    if pagina_atual == "esqueci_senha":

        tela_esqueci_senha()

    else:

        tela_login()

else:

    pagina = st.session_state.get(
        "pagina",
        "dashboard",
    )

    if pagina == "dashboard":

        dashboard()

    elif pagina == "trocar_senha":

        tela_trocar_senha()

    elif pagina == "gerenciar_senhas":

        if (
            st.session_state["usuario"]["perfil"]
            == "administrador"
        ):
            tela_gerenciar_senhas()

        else:
            st.error("Acesso negado.")

    elif pagina == "cad_pelotao":

        if (
            st.session_state["usuario"]["perfil"]
            == "administrador"
        ):
            tela_cadastrar_pelotao()

        else:
            st.error("Acesso negado.")

    elif pagina == "cons_pelotao":

        if (
            st.session_state["usuario"]["perfil"]
            == "administrador"
        ):
            tela_consultar_pelotao()

        else:
            st.error("Acesso negado.")

    elif pagina == "cad_sub":

        if (
            st.session_state["usuario"]["perfil"]
            == "administrador"
        ):
            tela_cadastrar_subordinado()

        else:
            st.error("Acesso negado.")

    elif pagina == "cons_sub":

        if (
            st.session_state["usuario"]["perfil"]
            == "administrador"
        ):
            tela_consultar_subordinado()

        else:
            st.error("Acesso negado.")

    elif pagina == "reg_fato":

        tela_registrar_fato()

    elif pagina == "cons_fato":

        tela_consultar_fatos()

    elif pagina == "rel_visual":

        tela_relatorio_visual()
