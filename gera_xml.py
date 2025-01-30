import os
import random
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

def gerar_nfe_xml(num_nfes=10, output_dir="nfe_xmls"):
    """Gera múltiplos arquivos XML de NF-e fictícias."""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    compradores = [
        {"cpf": "123.456.789-01", "nome": "Cliente A"},
        {"cpf": "234.567.890-12", "nome": "Cliente B"},
        {"cpf": "345.678.901-23", "nome": "Cliente C"},
        {"cpf": "456.789.012-34", "nome": "Cliente D"},
        {"cpf": "567.890.123-45", "nome": "Cliente E"},
        {"cpf": "678.901.234-56", "nome": "Cliente F"},
        {"cpf": "789.012.345-67", "nome": "Cliente G"},
        {"cpf": "890.123.456-78", "nome": "Cliente H"},
        {"cpf": "901.234.567-89", "nome": "Cliente I"},
        {"cpf": "012.345.678-90", "nome": "Cliente J"}
    ]
    
    produtos = [f"Produto {i}" for i in range(1, 21)]  # 20 produtos fixos
    
    base_xml = """<nfeProc xmlns=\"http://www.portalfiscal.inf.br/nfe\" versao=\"4.00\">
<NFe xmlns=\"http://www.portalfiscal.inf.br/nfe\">
<infNFe versao=\"4.00\" Id=\"NFe{id_nfe}\">
<ide>
<cUF>52</cUF>
<cNF>{cNF}</cNF>
<natOp>6107 VENDA PRODUCAO ESTAO DESTINADA A NAO CONTRIBUINTE </natOp>
<mod>55</mod>
<serie>106</serie>
<nNF>{nNF}</nNF>
<dhEmi>{dhEmi}</dhEmi>
<tpNF>1</tpNF>
<idDest>2</idDest>
<cMunFG>5220108</cMunFG>
<tpImp>2</tpImp>
<tpEmis>1</tpEmis>
<finNFe>1</finNFe>
</ide>
<emit>
<CNPJ>78876950012340</CNPJ>
<xNome>SAO LOURENCO LTDA</xNome>
</emit>
<dest>
<CPF>{cpf}</CPF>
<xNome>{nome_dest}</xNome>
</dest>
<det nItem="1">
<prod>
<cProd>PROD-{produto_id}</cProd>
<xProd>{produto_nome}</xProd>
<NCM>61091000</NCM>
<qCom>1.0000</qCom>
<vUnCom>{preco}</vUnCom>
<vProd>{preco}</vProd>
</prod>
</det>
<total>
<ICMSTot>
<vBC>{vBC}</vBC>
<vICMS>{vICMS}</vICMS>
<vICMSDeson>0.00</vICMSDeson>
<vFCPUFDest>0.00</vFCPUFDest>
<vICMSUFDest>0.00</vICMSUFDest>
<vICMSUFRemet>0.00</vICMSUFRemet>
<vFCP>0.00</vFCP>
<vBCST>0.00</vBCST>
<vST>0.00</vST>
<vFCPST>0.00</vFCPST>
<vFCPSTRet>0.00</vFCPSTRet>
<vProd>{vProd}</vProd>
<vFrete>0.00</vFrete>
<vSeg>0.00</vSeg>
<vDesc>0.00</vDesc>
<vII>0.00</vII>
<vIPI>0.00</vIPI>
<vIPIDevol>0.00</vIPIDevol>
<vPIS>{vPIS}</vPIS>
<vCOFINS>{vCOFINS}</vCOFINS>
<vOutro>0.00</vOutro>
<vNF>{vNF}</vNF>
<vTotTrib>{vTotTrib}</vTotTrib>
</ICMSTot>
</total>
</infNFe>
</NFe>
</nfeProc>"""

    for i in range(num_nfes):
        id_nfe = random.randint(100000, 999999)
        cNF = random.randint(10000000, 99999999)
        nNF = random.randint(3000000, 3999999)
        
        # Gerar data aleatória entre 2023 e 2025
        data_inicio = datetime(2023, 1, 1)
        data_fim = datetime(2025, 12, 31)
        dhEmi = (data_inicio + timedelta(days=random.randint(0, (data_fim - data_inicio).days))).strftime("%Y-%m-%dT%H:%M:%S-03:00")
        
        comprador = random.choice(compradores)
        cpf = comprador["cpf"]
        nome_dest = comprador["nome"]
        
        produto_id = random.randint(1, 20)
        produto_nome = produtos[produto_id - 1]
        preco = round(random.uniform(50, 500), 2)
        vBC = round(random.uniform(200, 500), 2)
        vICMS = round(vBC * 0.07, 2)
        vProd = vBC
        vPIS = round(vBC * 0.015, 2)
        vCOFINS = round(vBC * 0.076, 2)
        vNF = vBC + vICMS + vPIS + vCOFINS
        vTotTrib = round(vBC * 0.15, 2)
        
        xml_content = base_xml.format(
            id_nfe=id_nfe,
            cNF=cNF,
            nNF=nNF,
            dhEmi=dhEmi,
            cpf=cpf,
            nome_dest=nome_dest,
            produto_id=produto_id,
            produto_nome=produto_nome,
            preco=preco,
            vBC=vBC,
            vICMS=vICMS,
            vProd=vProd,
            vPIS=vPIS,
            vCOFINS=vCOFINS,
            vNF=vNF,
            vTotTrib=vTotTrib
        )
        
        file_name = f"{output_dir}/NFe_{id_nfe}.xml"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"Arquivo gerado: {file_name}")

if __name__ == "__main__":
    gerar_nfe_xml(50)  # Gera 50 NF-es fictícias
