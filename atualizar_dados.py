import mysql.connector
import pandas as pd

# Função para conectar ao banco de dados
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",   # Altere para o seu host
        user="root",        # Altere para seu usuário
        password="root842", # Altere para sua senha
        database="nf"       # Nome do banco de dados
    )

# Função para buscar TODOS os dados da base
def buscar_todos_dados():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Consulta SQL para obter TODOS os dados da base
    query = """
        SELECT nf.idnota_fiscal, nf.num_nota, nf.nome_empresa, nf.cnpj_empresa, 
               c.nome_cliente, nf.vl_icms, nf.vl_pis, nf.vl_confis, nf.vl_total_impostos, nf.data 
        FROM nota_fiscal nf
        JOIN cliente c ON nf.cliente_idcliente = c.idcliente
        ORDER BY nf.data DESC
    """

    cursor.execute(query)
    dados = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return dados

# Executar a função ao rodar o script
if __name__ == "__main__":
    dados = buscar_todos_dados()
    df = pd.DataFrame(dados)  # Converte os dados para um DataFrame do Pandas
    print(df)  # Exibe os dados no terminal para verificar

    print(f"🔄 {len(dados)} registros carregados com sucesso para o Power BI!")
