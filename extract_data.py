import pdfplumber
import pandas as pd
import glob
import os
import re
from datetime import datetime

def is_date(text):
    try:
        if isinstance(text, str) and re.match(r'\d{2}/\d{2}/\d{4}', text):
            datetime.strptime(text, '%d/%m/%Y')
            return True
    except:
        pass
    return False

def find_all_dates(text):
    # Retorna todas as datas no formato dd/mm/yyyy
    if not isinstance(text, str):
        return []
    return re.findall(r'\d{2}/\d{2}/\d{4}', text)

def processar_pdf(pdf_path):
    dados = []
    registro_atual = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    # Filtra linhas totalmente vazias ou com apenas espaços
                    if not linha or not any(campo and str(campo).strip() for campo in linha):
                        continue
                    
                    # Remove campos extras e garante 5 colunas
                    nova_linha = linha[:5]
                    while len(nova_linha) < 5:
                        nova_linha.append("")
                    
                    # Remove quebras de linha nas descrições
                    if nova_linha[1]:
                        nova_linha[1] = str(nova_linha[1]).replace('\n', ' ').strip()

                    # Verifica se há mais de uma data na primeira coluna
                    datas_encontradas = find_all_dates(nova_linha[0])
                    if len(datas_encontradas) > 1:
                        # Separa a linha em múltiplos registros
                        for idx, data in enumerate(datas_encontradas):
                            registro = ["", "", "", "", ""]
                            registro[0] = data
                            # Tenta dividir os outros campos proporcionalmente (simples)
                            for i in range(1, 5):
                                if nova_linha[i]:
                                    partes = str(nova_linha[i]).split()
                                    if len(partes) >= len(datas_encontradas):
                                        registro[i] = partes[idx]
                                    else:
                                        registro[i] = nova_linha[i]
                            dados.append(registro)
                        registro_atual = None
                        continue
                    
                    # Verifica se é um novo registro (começa com data)
                    if is_date(nova_linha[0]):
                        # Se já existe um registro atual, salva ele
                        if registro_atual:
                            dados.append(registro_atual)
                        registro_atual = nova_linha
                    else:
                        # Se não é um novo registro, junta com o registro atual
                        if registro_atual:
                            # Junta todas as colunas (exceto data) ao registro atual, se houver informação
                            for i in range(1, 5):
                                if nova_linha[i]:
                                    if registro_atual[i]:
                                        registro_atual[i] = str(registro_atual[i]) + " " + str(nova_linha[i])
                                    else:
                                        registro_atual[i] = str(nova_linha[i])
    
    # Adiciona o último registro se existir
    if registro_atual:
        dados.append(registro_atual)
    
    # Cria o DataFrame com o cabeçalho correto
    colunas = ["data_operacao", "descricao", "doc", "valor", "tipo"]
    df = pd.DataFrame(dados, columns=colunas)
    
    # Remove linhas indesejadas (exemplo: "Saldo Anterior")
    df = df[~df.apply(lambda row: row.astype(str).str.contains("Saldo Anterior", case=False, na=False)).any(axis=1)]
    
    # Remove as 6 primeiras linhas do DataFrame (informações do extrato)
    df = df.iloc[6:]
    
    # Substitui os sinais por "credito" e "debito"
    df['tipo'] = df['tipo'].replace({'+': 'credito', '-': 'debito'})
    
    # Adiciona uma coluna com o mês do arquivo
    mes = os.path.basename(pdf_path).split('-')[1].split('.')[0]
    df['mes'] = mes
    
    return df

# Encontra todos os PDFs no diretório atual
pdf_files = glob.glob("files/extract_2024/*.pdf")

# Lista para armazenar todos os DataFrames
dfs = []

# Processa cada PDF
for pdf_file in pdf_files:
    print(f"Processando {pdf_file}...")
    df = processar_pdf(pdf_file)
    dfs.append(df)

# Combina todos os DataFrames
df_final = pd.concat(dfs, ignore_index=True)

# Ordena por data
df_final['data_operacao'] = pd.to_datetime(df_final['data_operacao'], format='%d/%m/%Y', errors='coerce')
df_final = df_final.sort_values('data_operacao')

# Salva o resultado final
csv_path = "files/extrato_completo_2024.csv"
df_final.to_csv(csv_path, index=False, encoding='utf-8-sig')

print(f"\nCSV completo gerado com sucesso em {csv_path}!")
print(f"Total de registros: {len(df_final)}")