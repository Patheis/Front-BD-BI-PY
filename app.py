from flask import Flask, render_template, request, redirect, url_for, flash
import os
import xml.etree.ElementTree as ET
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Necessário para usar o flash no Flask

# Função para conectar ao banco de dados
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",  # Altere para o seu host
        user="root",       # Altere para o seu usuário
        password="root842",       # Altere para sua senha
        database="nf"      # O nome do seu banco de dados
    )

# Função para extrair os dados do XML
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
            "Nome Cliente": obter_dado_xml(root, namespaces, "dest", "xNome")
        }

        return dados
    except Exception as e:
        return None

# Função para extrair dados de uma tag do XML
def obter_dado_xml(root, namespaces, parent_tag, tag):
    """Função para extrair o dado de uma tag específica do XML dentro de um parent_tag."""  
    elemento = root.find(f".//nfe:{parent_tag}/nfe:{tag}", namespaces=namespaces)
    if elemento is not None:
        return elemento.text.strip()
    else:
        return '0'

# Função para verificar se a nota fiscal já existe
def verificar_nota_existente(cursor, num_nota):
    """Verifica se o número da nota fiscal já existe no banco de dados."""  
    cursor.execute("SELECT COUNT(*) FROM nota_fiscal WHERE num_nota = %s", (num_nota,))
    resultado = cursor.fetchone()
    return resultado[0] > 0

# Função para verificar se o cliente já existe
def verificar_cliente_existente(cursor, cpf):
    """Verifica se o cliente já existe no banco de dados"""
    cursor.execute("SELECT idcliente FROM cliente WHERE cpf = %s", (cpf,))
    resultado = cursor.fetchone()
    return resultado

# Rota principal para exibir o formulário
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar o upload do XML
@app.route('/upload', methods=['POST'])
def upload():
    if 'xmlFile' not in request.files:
        flash('Nenhum arquivo foi enviado!', 'error')
        return redirect(request.url)

    file = request.files['xmlFile']
    if file.filename == '':
        flash('Nenhum arquivo foi selecionado!', 'error')
        return redirect(request.url)

    if file and file.filename.endswith('.xml'):
        # Caminho para salvar o arquivo
        caminho_arquivo = os.path.join("uploads", file.filename)

        # Cria a pasta uploads se não existir
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        file.save(caminho_arquivo)

        # Extraindo dados do XML
        dados = extrair_dados(caminho_arquivo)
        if dados:
            # Conectando ao banco de dados
            conn = conectar_bd()
            cursor = conn.cursor()

            # Verificando se a nota fiscal já existe
            if verificar_nota_existente(cursor, dados["Numero da Nota"]):
                flash(f'Nota fiscal com número {dados["Numero da Nota"]} já existe!', 'error')
                return redirect(url_for('index'))

            # Verificando se o cliente já existe
            cliente_existente = verificar_cliente_existente(cursor, dados["CPF"])
            if not cliente_existente:
                # Se o cliente não existe, inserimos o novo cliente
                cursor.execute("""
                    INSERT INTO cliente (nome_cliente, cpf)
                    VALUES (%s, %s)
                """, (dados["Nome Cliente"], dados["CPF"]))
                conn.commit()
                # Pegamos o idcliente do cliente inserido
                cliente_id = cursor.lastrowid
            else:
                # Se o cliente já existe, usamos o id existente
                cliente_id = cliente_existente[0]

            # Inserir os dados da nota fiscal
            cursor.execute("""
                INSERT INTO nota_fiscal (num_nota, nome_empresa, cnpj_empresa, cliente_idcliente, vl_icms, vl_pis, vl_confis, vl_total_impostos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dados["Numero da Nota"],  # num_nota
                dados["Nome da Empresa"],  # nome_empresa
                dados["CNPJ"],             # cnpj_empresa
                cliente_id,                # cliente_idcliente
                dados["Valor ICMS"],       # vl_icms
                dados["Valor PIS"],        # vl_pis
                dados["Valor COFINS"],     # vl_confis
                dados["Valor da Nota"]     # vl_total_impostos
            ))
            conn.commit()

            cursor.close()
            conn.close()

            flash('Arquivo XML importado com sucesso!', 'success')
            return redirect(url_for('index'))

    flash('Erro ao carregar o arquivo XML!', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
