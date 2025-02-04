from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import xml.etree.ElementTree as ET
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Necessário para usar o flash no Flask

# Função para conectar ao banco de dados
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",   
        user="root",        
        password="root842", 
        database="nf"       
    )


# Rota principal para exibir o formulário e carregar os dados na tabela
@app.route('/')
def index():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT nf.idnota_fiscal, c.nome_cliente, nf.vl_total_impostos, nf.data 
    FROM nota_fiscal nf
    JOIN cliente c ON nf.cliente_idcliente = c.idcliente
    ORDER BY nf.data DESC
    """)

    
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', dados=dados)

# Rota para carregar os dados com filtros e limite (API AJAX)
@app.route('/api/consulta', methods=['GET'])
def api_consulta():
    nome = request.args.get('name', '').strip()
    data = request.args.get('date', '').strip()
    limite = int(request.args.get('limit', 50))  # Padrão: 50 registros

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Construindo a query dinâmica
    query = """
        SELECT nf.idnota_fiscal, c.nome_cliente, nf.vl_total_impostos, nf.data 
        FROM nota_fiscal nf
        JOIN cliente c ON nf.cliente_idcliente = c.idcliente
        WHERE 1=1
    """
    params = []

    if nome:
        query += " AND c.nome_cliente LIKE %s"
        params.append(f"%{nome}%")

    if data:
        query += " AND nf.data = %s"
        params.append(data)

    query += " ORDER BY nf.data DESC LIMIT %s"
    params.append(limite)

    cursor.execute(query, params)
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(dados)


def limpar_numero(valor):
    """Remove todos os caracteres não numéricos de uma string e converte o resultado para inteiro."""
    try:
        return int(''.join(filter(str.isdigit, valor)))
    except Exception:
        return 0

def extrair_dados(caminho):
    try:
        tree = ET.parse(caminho)
        root = tree.getroot()

        # Definir o namespace
        namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Extração dos dados da nota fiscal e do cliente
        dados = {
            "CNPJ": obter_dado_xml(root, namespaces, "emit", "CNPJ"),
            "Nome da Empresa": obter_dado_xml(root, namespaces, "emit", "xNome"),
            "Numero da Nota": obter_dado_xml(root, namespaces, "ide", "nNF"),
            "Valor ICMS": obter_dado_xml(root, namespaces, "ICMSTot", "vICMS"),
            "Valor da Nota": obter_dado_xml(root, namespaces, "ICMSTot", "vNF"),
            "Valor PIS": obter_dado_xml(root, namespaces, "ICMSTot", "vPIS"),
            "Valor COFINS": obter_dado_xml(root, namespaces, "ICMSTot", "vCOFINS"),
            "CPF": obter_dado_xml(root, namespaces, "dest", "CPF"),
            "Nome Cliente": obter_dado_xml(root, namespaces, "dest", "xNome"),
            "Data Emissao": obter_dado_xml(root, namespaces, "ide", "dEmi")  # Pegando a data
        }
        
        # Se "dEmi" não estiver disponível, tenta pegar "dhEmi" e cortar a parte da hora
        if dados["Data Emissao"] == "0":
            dhEmi = obter_dado_xml(root, namespaces, "ide", "dhEmi")
            if dhEmi != "0":
                dados["Data Emissao"] = dhEmi[:10]  # Pegando só a parte da data YYYY-MM-DD

        return dados
    except Exception as e:
        print("Erro ao extrair dados do XML:", e)
        return None


# Função para extrair dados de uma tag do XML
def obter_dado_xml(root, namespaces, parent_tag, tag):
    """Função para extrair o dado de uma tag específica do XML dentro de um parent_tag."""
    elemento = root.find(f".//nfe:{parent_tag}/nfe:{tag}", namespaces=namespaces)
    if elemento is not None and elemento.text:
        return elemento.text.strip()
    else:
        return '0'

# Verifica se a nota fiscal já existe
def verificar_nota_existente(cursor, num_nota):
    cursor.execute("SELECT COUNT(*) FROM nota_fiscal WHERE num_nota = %s", (num_nota,))
    resultado = cursor.fetchone()
    return resultado[0] > 0

# Verifica se o cliente já existe
def verificar_cliente_existente(cursor, cpf):
    cursor.execute("SELECT idcliente FROM cliente WHERE cpf = %s", (cpf,))
    resultado = cursor.fetchone()
    return resultado


# Rota para upload de XMLs
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('xmlFile')
    if not files or len(files) == 0:
        flash('Nenhum arquivo foi enviado!', 'error')
        return redirect(url_for('index'))

    # Cria a pasta 'uploads' se não existir
    upload_folder = "uploads"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    count_success = 0
    count_already_exists = 0
    count_errors = 0
    error_messages = []

    conn = conectar_bd()
    cursor = conn.cursor()

    for file in files:
        if file.filename == '' or not file.filename.endswith('.xml'):
            continue  # pula arquivos inválidos

        caminho_arquivo = os.path.join(upload_folder, file.filename)
        file.save(caminho_arquivo)

        # Extraindo dados do XML
        dados = extrair_dados(caminho_arquivo)
        if not dados:
            error_messages.append(f"Erro ao extrair dados do arquivo {file.filename}.")
            count_errors += 1
            continue

        # Verifica se a nota fiscal já existe
        if verificar_nota_existente(cursor, dados["Numero da Nota"]):
            error_messages.append(f"Nota fiscal com número {dados['Numero da Nota']} já existe (arquivo: {file.filename}).")
            count_already_exists += 1
            continue

        cpf_limpo = limpar_numero(dados["CPF"])
        cnpj_limpo = limpar_numero(dados["CNPJ"])

        # Verifica se o cliente já existe
        cliente_existente = verificar_cliente_existente(cursor, cpf_limpo)
        if not cliente_existente:
            cursor.execute("""
                INSERT INTO cliente (nome_cliente, cpf)
                VALUES (%s, %s)
            """, (dados["Nome Cliente"], cpf_limpo))
            conn.commit()
            cliente_id = cursor.lastrowid
        else:
            cliente_id = cliente_existente[0]

        # Insere os dados da nota fiscal
        cursor.execute("""
        INSERT INTO nota_fiscal (num_nota, nome_empresa, cnpj_empresa, cliente_idcliente, vl_icms, vl_pis, vl_confis, vl_total_impostos, data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
        dados["Numero da Nota"],
        dados["Nome da Empresa"],
        cnpj_limpo,
        cliente_id,
        dados["Valor ICMS"],
        dados["Valor PIS"],
        dados["Valor COFINS"],
        dados["Valor da Nota"],
        dados["Data Emissao"]  # Adicionando a data aqui
        ))

        conn.commit()
        count_success += 1

    cursor.close()
    conn.close()

    # Compor a mensagem final
    flash_msg = ""
    if count_success:
        flash_msg += f"{count_success} nota(s) importadas com sucesso. "
    if count_already_exists:
        flash_msg += f"{count_already_exists} nota(s) já existentes e não importadas. "
    if count_errors:
        flash_msg += f"{count_errors} arquivo(s) apresentaram erro na extração. "

    for msg in error_messages:
        flash(msg, 'error')

    flash(flash_msg, 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
