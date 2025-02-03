from flask import Flask, render_template, request, redirect, url_for, flash
import os
import xml.etree.ElementTree as ET
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Necessário para usar o flash no Flask

# Função para conectar ao banco de dados
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",   # Altere para o seu host
        user="root",        # Altere para o seu usuário
        password="root842", # Altere para sua senha
        database="nf"       # Nome do seu banco de dados
    )

def limpar_numero(valor):
    """
    Remove todos os caracteres não numéricos de uma string e converte o resultado para inteiro.
    """
    return int(''.join(filter(str.isdigit, valor)))


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
        print("Erro ao extrair dados do XML:", e)
        return None

# Função para extrair dados de uma tag do XML
def obter_dado_xml(root, namespaces, parent_tag, tag):
    """
    Função para extrair o dado de uma tag específica do XML dentro de um parent_tag.
    """
    elemento = root.find(f".//nfe:{parent_tag}/nfe:{tag}", namespaces=namespaces)
    if elemento is not None and elemento.text:
        return elemento.text.strip()
    else:
        return '0'

# Função para verificar se a nota fiscal já existe
def verificar_nota_existente(cursor, num_nota):
    """
    Verifica se o número da nota fiscal já existe no banco de dados.
    """
    cursor.execute("SELECT COUNT(*) FROM nota_fiscal WHERE num_nota = %s", (num_nota,))
    resultado = cursor.fetchone()
    return resultado[0] > 0

# Função para verificar se o cliente já existe
def verificar_cliente_existente(cursor, cpf):
    """
    Verifica se o cliente já existe no banco de dados.
    """
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
    # Verifica se o campo do arquivo existe na requisição
    if 'xmlFile' not in request.files:
        flash('Nenhum arquivo foi enviado!', 'error')
        return redirect(url_for('index'))

    file = request.files['xmlFile']
    
    # Verifica se o nome do arquivo não está vazio
    if file.filename == '':
        flash('Nenhum arquivo foi selecionado!', 'error')
        return redirect(url_for('index'))

    # Verifica se o arquivo possui a extensão .xml
    if file and file.filename.endswith('.xml'):
        # Define o caminho para salvar o arquivo
        caminho_arquivo = os.path.join("uploads", file.filename)

        # Cria a pasta 'uploads' se não existir
        if not os.path.exists('uploads'):
            os.makedirs('uploads')

        file.save(caminho_arquivo)

        # Extraindo dados do XML
        dados = extrair_dados(caminho_arquivo)
        if not dados:
            flash('Erro ao extrair dados do arquivo XML!', 'error')
            return redirect(url_for('index'))

        # Conectando ao banco de dados
        conn = conectar_bd()
        cursor = conn.cursor()

        # Verifica se a nota fiscal já existe
        if verificar_nota_existente(cursor, dados["Numero da Nota"]):
            flash(f'Nota fiscal com número {dados["Numero da Nota"]} já existe!', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))
        
        # Limpa o CPF extraído do XML
        cpf_limpo = limpar_numero(dados["CPF"])
          
        # Verifica se o cliente já existe
        cliente_existente = verificar_cliente_existente(cursor, dados["CPF"])
        if not cliente_existente:
            # Se o cliente não existir, insere um novo cliente
            cursor.execute("""
                INSERT INTO cliente (nome_cliente, cpf)
                VALUES (%s, %s)
            """, (dados["Nome Cliente"], cpf_limpo))
            conn.commit()
            # Obtém o id do cliente recém-inserido
            cliente_id = cursor.lastrowid
        else:
            # Se o cliente já existir, utiliza o id existente
            cliente_id = cliente_existente[0]
        
        # Limpa o CNPJ extraído do XML (para o campo BIGINT na tabela nota_fiscal)
        cnpj_limpo = limpar_numero(dados["CNPJ"])

        # Insere os dados da nota fiscal
        cursor.execute("""
            INSERT INTO nota_fiscal (num_nota, nome_empresa, cnpj_empresa, cliente_idcliente, vl_icms, vl_pis, vl_confis, vl_total_impostos)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados["Numero da Nota"],   # num_nota
            dados["Nome da Empresa"],   # nome_empresa
            cnpj_limpo,              # cnpj_empresa
            cliente_id,                 # cliente_idcliente
            dados["Valor ICMS"],        # vl_icms
            dados["Valor PIS"],         # vl_pis
            dados["Valor COFINS"],      # vl_confis
            dados["Valor da Nota"]      # vl_total_impostos
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
