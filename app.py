import hashlib
from pathlib import Path
import sqlite3
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Banco de Fatos Observados",
    page_icon="📋",
    layout="centered",
)

DB_PATH = Path("consta_que.db")


# ============================================================
# BANCO DE DADOS
# ============================================================


def conectar_banco():
  return sqlite3.connect(DB_PATH)


def criar_banco():
  conn = conectar_banco()
  cursor = conn.cursor()

  # Tabela de Usuários
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'fiscalizador',
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)

  # Tabela de Pelotões
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pelotoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

  # Tabela de Militares (Subordinados)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS militares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qra TEXT NOT NULL,
            posto_graduacao TEXT NOT NULL,
            pelotao_id INTEGER NOT NULL,
            FOREIGN KEY (pelotao_id) REFERENCES pelotoes (id)
        )
    """)

  # Tabela de Fatos Observados
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS fatos_observados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            militar_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (militar_id) REFERENCES militares (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

  conn.commit()
  conn.close()


def gerar_hash(senha):
  return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def criar_usuarios_iniciais():
  conn = conectar_banco()
  cursor = conn.cursor()

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

  for nome, login, perfil in usuarios:
    cursor.execute(
        """
            INSERT OR IGNORE INTO usuarios (nome, login, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """,
        (nome, login, senha_padrao_hash, perfil),
    )

  conn.commit()
  conn.close()


def autenticar_usuario(login, senha):
  conn = conectar_banco()
  cursor = conn.cursor()

  senha_hash = gerar_hash(senha)

  cursor.execute(
      """
        SELECT id, nome, login, perfil
        FROM usuarios
        WHERE login = ?
        AND senha_hash = ?
        AND ativo = 1
    """,
      (login, senha_hash),
  )

  usuario = cursor.fetchone()
  conn.close()
  return usuario


def atualizar_senha(usuario_id, nova_senha):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    nova_senha_hash = gerar_hash(nova_senha)
    cursor.execute(
        """
            UPDATE usuarios
            SET senha_hash = ?
            WHERE id = ?
        """,
        (nova_senha_hash, usuario_id),
    )
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"
  except Exception as e:
    return False, f"Erro ao alterar senha: {e}"


def resetar_senha_por_login(login):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE login = ?", (login,))
    user = cursor.fetchone()
    if not user:
      conn.close()
      return False, "Usuário não encontrado no sistema."

    senha_padrao_hash = gerar_hash("123456")
    cursor.execute(
        "UPDATE usuarios SET senha_hash = ? WHERE login = ?",
        (senha_padrao_hash, login),
    )
    conn.commit()
    conn.close()
    return (
        True,
        f"Senha do usuário **{user[1]}** redefinida para o padrão: **123456**",
    )
  except Exception as e:
    conn.close()
    return False, f"Erro ao resetar senha: {e}"


def listar_usuarios():
  conn = conectar_banco()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, nome, login, perfil FROM usuarios ORDER BY nome ASC"
  )
  usuarios = cursor.fetchall()
  conn.close()
  return usuarios


# --- Operações de Pelotões ---


def salvar_pelotao(nome):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pelotoes (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()
    return True, "Pelotão cadastrado com sucesso!"
  except sqlite3.IntegrityError:
    return False, "Este pelotão já está cadastrado."
  except Exception as e:
    return False, f"Erro ao cadastrar: {e}"


def listar_pelotoes():
  conn = conectar_banco()
  cursor = conn.cursor()
  cursor.execute("SELECT id, nome FROM pelotoes ORDER BY nome ASC")
  pelotoes = cursor.fetchall()
  conn.close()
  return pelotoes


def deletar_pelotao(pelotao_id):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM militares WHERE pelotao_id = ?", (pelotao_id,)
    )
    qtd_vinculados = cursor.fetchone()[0]

    if qtd_vinculados > 0:
      conn.close()
      return (
          False,
          f"Não é possível excluir: existem {qtd_vinculados} subordinado(s)"
          " vinculado(s) a este pelotão.",
      )

    cursor.execute("DELETE FROM pelotoes WHERE id = ?", (pelotao_id,))
    conn.commit()
    conn.close()
    return True, "Pelotão excluído com sucesso!"
  except Exception as e:
    return False, f"Erro ao excluir pelotão: {e}"


# --- Operações de Militares (Subordinados) ---


def salvar_militar(qra, posto_graduacao, pelotao_id):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO militares (qra, posto_graduacao, pelotao_id)
            VALUES (?, ?, ?)
        """,
        (qra, posto_graduacao, pelotao_id),
    )
    conn.commit()
    conn.close()
    return True, "Subordinado cadastrado com sucesso!"
  except Exception as e:
    return False, f"Erro ao cadastrar subordinado: {e}"


def listar_militares(pelotao_id=None):
  conn = conectar_banco()
  cursor = conn.cursor()
  if pelotao_id:
    cursor.execute(
        """
            SELECT m.id, m.posto_graduacao, m.qra, p.nome
            FROM militares m
            JOIN pelotoes p ON m.pelotao_id = p.id
            WHERE m.pelotao_id = ?
            ORDER BY m.qra ASC
        """,
        (pelotao_id,),
    )
  else:
    cursor.execute("""
            SELECT m.id, m.posto_graduacao, m.qra, p.nome
            FROM militares m
            JOIN pelotoes p ON m.pelotao_id = p.id
            ORDER BY p.nome, m.qra ASC
        """)
  militares = cursor.fetchall()
  conn.close()
  return militares


def deletar_militar(militar_id):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM fatos_observados WHERE militar_id = ?",
        (militar_id,),
    )
    qtd_fatos = cursor.fetchone()[0]

    if qtd_fatos > 0:
      conn.close()
      return (
          False,
          f"Não é possível excluir: existem {qtd_fatos} fato(s) registrado(s)"
          " para este subordinado.",
      )

    cursor.execute("DELETE FROM militares WHERE id = ?", (militar_id,))
    conn.commit()
    conn.close()
    return True, "Subordinado excluído com sucesso!"
  except Exception as e:
    return False, f"Erro ao excluir subordinado: {e}"


# --- Operações de Fatos Observados ---


def salvar_fato(militar_id, usuario_id, tipo, descricao):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO fatos_observados (militar_id, usuario_id, tipo, descricao)
            VALUES (?, ?, ?, ?)
        """,
        (militar_id, usuario_id, tipo, descricao),
    )
    conn.commit()
    conn.close()
    return True, "Fato observado registrado com sucesso!"
  except Exception as e:
    return False, f"Erro ao registrar fato: {e}"


def listar_fatos(militar_id=None, pelotao_id=None):
  conn = conectar_banco()
  cursor = conn.cursor()

  query = """
        SELECT f.id, f.tipo, f.descricao, f.data_registro, m.posto_graduacao, m.qra, p.nome, u.nome
        FROM fatos_observados f
        JOIN militares m ON f.militar_id = m.id
        JOIN pelotoes p ON m.pelotao_id = p.id
        JOIN usuarios u ON f.usuario_id = u.id
    """
  params = []
  conditions = []

  if militar_id:
    conditions.append("f.militar_id = ?")
    params.append(militar_id)
  elif pelotao_id:
    conditions.append("m.pelotao_id = ?")
    params.append(pelotao_id)

  if conditions:
    query += " WHERE " + " AND ".join(conditions)

  query += " ORDER BY f.data_registro DESC"
  cursor.execute(query, params)
  fatos = cursor.fetchall()
  conn.close()
  return fatos


def deletar_fato(fato_id):
  try:
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fatos_observados WHERE id = ?", (fato_id,))
    conn.commit()
    conn.close()
    return True, "Fato observado excluído com sucesso!"
  except Exception as e:
    return False, f"Erro ao excluir fato: {e}"


# ============================================================
# LOGIN E RECUPERAÇÃO DE SENHA
# ============================================================


def tela_login():
  st.title("📋 Banco de Fatos Observados")
  st.subheader("Sistema de Registro de Condutas")
  st.divider()

  st.markdown("### 🔐 Acesso ao sistema")

  login = st.text_input("Usuário", placeholder="Digite seu usuário")
  senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")

  entrar = st.button("ENTRAR", use_container_width=True, type="primary")

  if entrar:
    if not login or not senha:
      st.error("Informe o usuário e a senha.")
    else:
      usuario = autenticar_usuario(login.strip().lower(), senha)
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
        st.error("Usuário ou senha incorretos.")

  st.divider()
  if st.button("🔑 Esqueci minha senha", use_container_width=True):
    st.session_state["pagina"] = "esqueci_senha"
    st.rerun()


def tela_esqueci_senha():
  st.title("🔑 Recuperação de Senha")
  st.divider()
  st.info(
      "Informe o seu usuário cadastrado. A solicitação será direcionada ao"
      " Administrador do sistema para que a senha seja redefinida para o"
      " padrão inicial (**123456**)."
  )

  login_rec = st.text_input(
      "Usuário Cadastrado", placeholder="Ex: alan, anabeatriz..."
  )

  if st.button(
      "Solicitar Redefinição ao Administrador",
      type="primary",
      use_container_width=True,
  ):
    if not login_rec.strip():
      st.warning("Informe o seu usuário.")
    else:
      conn = conectar_banco()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT id, nome FROM usuarios WHERE login = ?",
          (login_rec.strip().lower(),),
      )
      user_encontrado = cursor.fetchone()
      conn.close()

      if user_encontrado:
        st.success(
            f"Solicitação registrada para **{user_encontrado[1]}**. Avise o"
            " Administrador (`admin`) para efetivar o reset para a senha"
            " padrão **123456**."
        )
      else:
        st.error("Usuário não encontrado na base de dados.")

  st.divider()
  if st.button("⬅️ Voltar ao Login", use_container_width=True):
    st.session_state["pagina"] = "login"
    st.rerun()


# ============================================================
# TELA DE TROCA DE SENHA (INTERNA)
# ============================================================


def tela_trocar_senha():
  st.title("🔑 Alterar Minha Senha")
  st.divider()

  senha_atual = st.text_input(
      "Senha Atual", type="password", placeholder="Digite sua senha atual"
  )
  nova_senha = st.text_input(
      "Nova Senha", type="password", placeholder="Digite a nova senha"
  )
  confirma_senha = st.text_input(
      "Confirmar Nova Senha",
      type="password",
      placeholder="Digite a nova senha novamente",
  )

  if st.button("Salvar Nova Senha", type="primary", use_container_width=True):
    if not senha_atual or not nova_senha or not confirma_senha:
      st.warning("Preencha todos os campos.")
    elif nova_senha != confirma_senha:
      st.error("A nova senha e a confirmação não conferem.")
    else:
      usuario_id = st.session_state["usuario"]["id"]
      login_atual = st.session_state["usuario"]["login"]

      if autenticar_usuario(login_atual, senha_atual):
        sucesso, msg = atualizar_senha(usuario_id, nova_senha)
        if sucesso:
          st.success(msg)
        else:
          st.error(msg)
      else:
        st.error("A senha atual informada está incorreta.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


# ============================================================
# TELAS DE PELOTÕES E SUBORDINADOS (EXCLUSIVO ADMIN)
# ============================================================


def tela_cadastrar_pelotao():
  st.title("👥 Cadastrar Pelotão")
  st.divider()

  nome_pelotao = st.text_input("Nome do Pelotão", placeholder="Ex: 1º Pelotão")

  if st.button("Salvar Pelotão", type="primary", use_container_width=True):
    if nome_pelotao.strip():
      sucesso, msg = salvar_pelotao(nome_pelotao.strip())
      if sucesso:
        st.success(msg)
      else:
        st.error(msg)
    else:
      st.warning("Informe o nome do pelotão.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


def tela_consultar_pelotao():
  st.title("👥 Pelotões Cadastrados")
  st.divider()

  pelotoes = listar_pelotoes()

  if pelotoes:
    for p in pelotoes:
      col1, col2 = st.columns([3, 1])
      with col1:
        st.markdown(f"• **{p[1]}** *(ID: {p[0]})*")
      with col2:
        if st.button(
            "🗑️ Excluir", key=f"del_pel_{p[0]}", use_container_width=True
        ):
          sucesso, msg = deletar_pelotao(p[0])
          if sucesso:
            st.success(msg)
            st.rerun()
          else:
            st.error(msg)
  else:
    st.info("Nenhum pelotão cadastrado ainda.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


def tela_cadastrar_subordinado():
  st.title("👮 Cadastrar Subordinado")
  st.divider()

  pelotoes = listar_pelotoes()

  if not pelotoes:
    st.warning(
        "É necessário cadastrar ao menos um Pelotão antes de cadastrar"
        " subordinados."
    )
  else:
    opcoes_pelotao = {p[1]: p[0] for p in pelotoes}
    pelotao_selecionado = st.selectbox("Pelotão", list(opcoes_pelotao.keys()))

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

    qra = st.text_input("QRA (Nome de Guerra)", placeholder="Ex: Silva")

    if st.button("Salvar Subordinado", type="primary", use_container_width=True):
      if qra.strip():
        pelotao_id = opcoes_pelotao[pelotao_selecionado]
        sucesso, msg = salvar_militar(qra.strip(), posto_grad, pelotao_id)
        if sucesso:
          st.success(msg)
        else:
          st.error(msg)
      else:
        st.warning("Informe o QRA (Nome de guerra).")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


def tela_consultar_subordinado():
  st.title("👮 Subordinados Cadastrados")
  st.divider()

  militares = listar_militares()

  if militares:
    for m in militares:
      col1, col2 = st.columns([3, 1])
      with col1:
        st.markdown(f"• **{m[1]} {m[2]}** — *{m[3]}*")
      with col2:
        if st.button(
            "🗑️ Excluir", key=f"del_sub_{m[0]}", use_container_width=True
        ):
          sucesso, msg = deletar_militar(m[0])
          if sucesso:
            st.success(msg)
            st.rerun()
          else:
            st.error(msg)
  else:
    st.info("Nenhum subordinado cadastrado ainda.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


# ============================================================
# TELA DE GERENCIAMENTO DE SENHAS (EXCLUSIVO ADMIN)
# ============================================================


def tela_gerenciar_senhas():
  st.title("🛠️ Gerenciar Senhas de Usuários")
  st.divider()
  st.markdown(
      "Como Administrador, você pode redefinir a senha de qualquer usuário"
      " para o padrão inicial (**123456**)."
  )

  usuarios = listar_usuarios()
  opcoes_usuarios = {f"{u[1]} ({u[2]}) — Perfil: {u[3]}": u[2] for u in usuarios}

  user_sel = st.selectbox(
      "Selecione o Usuário para Resetar Senha", list(opcoes_usuarios.keys())
  )
  login_alvo = opcoes_usuarios[user_sel]

  if st.button(
      "🔄 Redefinir Senha para 123456", type="primary", use_container_width=True
  ):
    sucesso, msg = resetar_senha_por_login(login_alvo)
    if sucesso:
      st.success(msg)
    else:
      st.error(msg)

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


# ============================================================
# TELAS DE FATOS OBSERVADOS
# ============================================================


def tela_registrar_fato():
  st.title("📝 Registrar Fato Observado")
  st.divider()

  pelotoes = listar_pelotoes()

  if not pelotoes:
    st.warning("É necessário cadastrar ao menos um Pelotão primeiro.")
  else:
    opcoes_pelotao = {p[1]: p[0] for p in pelotoes}
    pelotao_selecionado = st.selectbox(
        "1. Selecione o Pelotão", list(opcoes_pelotao.keys())
    )

    pelotao_id = opcoes_pelotao[pelotao_selecionado]
    militares = listar_militares(pelotao_id)

    if not militares:
      st.info(f"Nenhum subordinado cadastrado no {pelotao_selecionado}.")
    else:
      opcoes_militar = {f"{m[1]} {m[2]}": m[0] for m in militares}
      militar_selecionado = st.selectbox(
          "2. Selecione o Subordinado (QRA)", list(opcoes_militar.keys())
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
          "4. Fato Observado (Descreva a conduta com clareza)",
          placeholder="Ex: Durante a instrução de ordem unida, demonstrou excepcional liderança e postura...",
          height=150,
      )

      if st.button(
          "💾 Registrar Fato Observado",
          type="primary",
          use_container_width=True,
      ):
        if descricao.strip():
          militar_id = opcoes_militar[militar_selecionado]
          usuario_id = st.session_state["usuario"]["id"]

          sucesso, msg = salvar_fato(
              militar_id, usuario_id, tipo_fato, descricao.strip()
          )
          if sucesso:
            st.success(msg)
          else:
            st.error(msg)
        else:
          st.warning("Escreva a descrição do fato observado antes de salvar.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


def tela_consultar_fatos():
  st.title("🔍 Consulta Geral de Fatos")
  st.divider()

  pelotoes = listar_pelotoes()

  if not pelotoes:
    st.info("Nenhum pelotão cadastrado para consulta.")
  else:
    opcoes_pelotao = {"Todos os Pelotões": None}
    for p in pelotoes:
      opcoes_pelotao[p[1]] = p[0]

    pelotao_sel = st.selectbox(
        "Filtrar por Pelotão", list(opcoes_pelotao.keys())
    )
    pelotao_id = opcoes_pelotao[pelotao_sel]

    militares = (
        listar_militares(pelotao_id) if pelotao_id else listar_militares()
    )

    opcoes_militar = {"Todos os Subordinados": None}
    for m in militares:
      opcoes_militar[f"{m[1]} {m[2]} ({m[3]})"] = m[0]

    militar_sel = st.selectbox(
        "Filtrar por Subordinado", list(opcoes_militar.keys())
    )
    militar_id = opcoes_militar[militar_sel]

    st.divider()

    fatos = listar_fatos(militar_id=militar_id, pelotao_id=pelotao_id)

    if fatos:
      elogiáveis = sum(1 for f in fatos if "🔵" in f[1])
      neutras = sum(1 for f in fatos if "🟡" in f[1])
      a_melhorar = sum(1 for f in fatos if "🔴" in f[1])

      c1, c2, c3 = st.columns(3)
      c1.metric("🔵 Elogiáveis", elogiáveis)
      c2.metric("🟡 Neutras", neutras)
      c3.metric("🔴 A Melhorar", a_melhorar)

      st.markdown("### 📋 Registros Encontrados")

      for f in fatos:
        fato_id, tipo, desc, data, posto, qra, pel_nome, autor = (
            f[0],
            f[1],
            f[2],
            f[3],
            f[4],
            f[5],
            f[6],
            f[7],
        )
        data_fmt = data.split()[0] if " " in data else data

        with st.expander(
            f"{tipo} | {posto} {qra} ({pel_nome}) — Data: {data_fmt}"
        ):
          st.markdown(f"**Militar:** {posto} {qra} ({pel_nome})")
          st.markdown(f"**Registrado por:** {autor}")
          st.markdown(f"**Data:** {data}")
          st.markdown(f"**Descrição:**\n>{desc}")

          st.divider()
          if st.button("🗑️ Excluir Fato", key=f"del_fato_{fato_id}"):
            sucesso, msg = deletar_fato(fato_id)
            if sucesso:
              st.success(msg)
              st.rerun()
            else:
              st.error(msg)
    else:
      st.info("Nenhum fato observado encontrado para os filtros selecionados.")

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


# ============================================================
# TELAS DE RELATÓRIO VISUAL INDIVIDUAL
# ============================================================


def tela_relatorio_visual():
  st.title("📊 Relatório Visual por Militar")
  st.divider()

  pelotoes = listar_pelotoes()

  if not pelotoes:
    st.info("Nenhum pelotão cadastrado.")
  else:
    opcoes_pelotao = {p[1]: p[0] for p in pelotoes}
    pelotao_sel = st.selectbox(
        "1. Selecione o Pelotão", list(opcoes_pelotao.keys())
    )

    pelotao_id = opcoes_pelotao[pelotao_sel]
    militares = listar_militares(pelotao_id)

    if not militares:
      st.info(f"Nenhum subordinado cadastrado no {pelotao_sel}.")
    else:
      opcoes_militar = {f"{m[1]} {m[2]}": (m[0], m[1], m[2]) for m in militares}
      militar_sel = st.selectbox(
          "2. Selecione o Militar", list(opcoes_militar.keys())
      )

      militar_id, posto, qra = opcoes_militar[militar_sel]
      fatos = listar_fatos(militar_id=militar_id)
      total_fatos = len(fatos)

      st.divider()

      st.markdown(f"### 🪪 Ficha Individual: **{posto} {qra}**")
      st.caption(f"Pelotão: {pelotao_sel} | Total de Fatos Observados: {total_fatos}")

      if total_fatos == 0:
        st.info("Este militar ainda não possui nenhum fato observado registrado.")
      else:
        elogiáveis = sum(1 for f in fatos if "🔵" in f[1])
        neutras = sum(1 for f in fatos if "🟡" in f[1])
        a_melhorar = sum(1 for f in fatos if "🔴" in f[1])

        pct_elo = (elogiáveis / total_fatos) * 100
        pct_neu = (neutras / total_fatos) * 100
        pct_mel = (a_melhorar / total_fatos) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", total_fatos)
        col2.metric("🔵 Elogiáveis", elogiáveis)
        col3.metric("🟡 Neutras", neutras)
        col4.metric("🔴 A Melhorar", a_melhorar)

        st.markdown("---")
        st.markdown("### 📈 Distribuição das Condutas")

        st.markdown(f"**🔵 Elogiável / Positiva:** {pct_elo:.1f}%")
        st.progress(pct_elo / 100)

        st.markdown(f"**🟡 Neutra / Observação:** {pct_neu:.1f}%")
        st.progress(pct_neu / 100)

        st.markdown(f"**🔴 A Melhorar / Relevante:** {pct_mel:.1f}%")
        st.progress(pct_mel / 100)

        st.markdown("---")
        st.markdown("### 📜 Linha do Tempo de Condutas")

        for f in fatos:
          tipo, desc, data, autor = f[1], f[2], f[3], f[7]
          data_fmt = data.split()[0] if " " in data else data

          st.markdown(f"**{tipo}** — *{data_fmt}* (Avaliador: {autor})")
          st.info(desc)

  st.divider()
  if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
    st.session_state["pagina"] = "dashboard"
    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================


def dashboard():
  usuario = st.session_state["usuario"]

  st.title("📋 Banco de Fatos Observados")
  st.success(f"Bem-vindo, {usuario['nome']}!")
  st.write(f"Perfil: **{usuario['perfil']}**")
  st.divider()

  # Se for Administrador, exibe as opções completas (Pelotões, Subordinados e Fatos)
  if usuario["perfil"] == "administrador":
    col1, col2, col3 = st.columns(3)

    with col1:
      st.markdown("### 👥 PELOTÕES")
      if st.button("Cadastrar", key="cad_pelotao", use_container_width=True):
        st.session_state["pagina"] = "cad_pelotao"
        st.rerun()
      if st.button("Consultar", key="cons_pelotao", use_container_width=True):
        st.session_state["pagina"] = "cons_pelotao"
        st.rerun()

    with col2:
      st.markdown("### 👮 SUBORDINADOS")
      if st.button("Cadastrar", key="cad_sub", use_container_width=True):
        st.session_state["pagina"] = "cad_sub"
        st.rerun()
      if st.button("Consultar", key="cons_sub", use_container_width=True):
        st.session_state["pagina"] = "cons_sub"
        st.rerun()

    with col3:
      st.markdown("### 📝 FATOS & ANÁLISE")
      if st.button("Registrar fato", key="reg_fato", use_container_width=True):
        st.session_state["pagina"] = "reg_fato"
        st.rerun()
      if st.button("Consulta Geral", key="cons_fato", use_container_width=True):
        st.session_state["pagina"] = "cons_fato"
        st.rerun()
      if st.button(
          "📊 Relatório Visual", key="rel_visual", use_container_width=True
      ):
        st.session_state["pagina"] = "rel_visual"
        st.rerun()

    st.divider()
    if st.button(
        "🛠️ Painel Admin: Resetar Senhas de Usuários", use_container_width=True
    ):
      st.session_state["pagina"] = "gerenciar_senhas"
      st.rerun()

  else:
    # Se for Cadete Fiscalizador, exibe apenas os procedimentos de Fatos e Análise
    st.markdown("### 📝 FATOS & ANÁLISE")
    col1, col2, col3 = st.columns(3)
    with col1:
      if st.button("Registrar fato", key="reg_fato", use_container_width=True):
        st.session_state["pagina"] = "reg_fato"
        st.rerun()
    with col2:
      if st.button("Consulta Geral", key="cons_fato", use_container_width=True):
        st.session_state["pagina"] = "cons_fato"
        st.rerun()
    with col3:
      if st.button(
          "📊 Relatório Visual", key="rel_visual", use_container_width=True
      ):
        st.session_state["pagina"] = "rel_visual"
        st.rerun()

  st.divider()

  col_s1, col_s2 = st.columns(2)
  with col_s1:
    if st.button("🔑 Trocar Senha", use_container_width=True):
      st.session_state["pagina"] = "trocar_senha"
      st.rerun()
  with col_s2:
    if st.button("🚪 Sair", use_container_width=True):
      st.session_state.clear()
      st.rerun()


# ============================================================
# INICIALIZAÇÃO E ROTEAMENTO
# ============================================================

criar_banco()
criar_usuarios_iniciais()

if "autenticado" not in st.session_state:
  st.session_state["autenticado"] = False

if "pagina" not in st.session_state:
  st.session_state["pagina"] = "login"


if not st.session_state["autenticado"]:
  pagina_atual = st.session_state.get("pagina", "login")
  if pagina_atual == "esqueci_senha":
    tela_esqueci_senha()
  else:
    tela_login()
else:
  pagina = st.session_state.get("pagina", "dashboard")
  if pagina == "dashboard":
    dashboard()
  elif pagina == "trocar_senha":
    tela_trocar_senha()
  elif pagina == "gerenciar_senhas":
    # Proteção extra de rota para o admin
    if st.session_state["usuario"]["perfil"] == "administrador":
      tela_gerenciar_senhas()
    else:
      st.error("Acesso negado.")
  elif pagina == "cad_pelotao":
    if st.session_state["usuario"]["perfil"] == "administrador":
      tela_cadastrar_pelotao()
    else:
      st.error("Acesso negado.")
  elif pagina == "cons_pelotao":
    if st.session_state["usuario"]["perfil"] == "administrador":
      tela_consultar_pelotao()
    else:
      st.error("Acesso negado.")
  elif pagina == "cad_sub":
    if st.session_state["usuario"]["perfil"] == "administrador":
      tela_cadastrar_subordinado()
    else:
      st.error("Acesso negado.")
  elif pagina == "cons_sub":
    if st.session_state["usuario"]["perfil"] == "administrador":
      tela_consultar_subordinado()
    else:
      st.error("Acesso negado.")
  elif pagina == "reg_fato":
    tela_registrar_fato()
  elif pagina == "cons_fato":
    tela_consultar_fatos()
  elif pagina == "rel_visual":
    tela_relatorio_visual()