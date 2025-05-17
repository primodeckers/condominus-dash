import csv
from collections import defaultdict

# Dicionários para armazenar os totais por mês
totais = defaultdict(lambda: {'debito': 0.0, 'credito': 0.0})

with open('extrato_completo_2024.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        valor_str = row['valor'].replace('.', '').replace(',', '.').replace('"', '')
        valor = float(valor_str)
        mes = row['mes']
        tipo = row['tipo'].strip().lower()
        if tipo == 'debito':
            totais[mes]['debito'] += valor
        elif tipo == 'credito':
            totais[mes]['credito'] += valor

# Exibe o resultado
for mes, valores in totais.items():
    print(f"{mes}: Débito = R$ {valores['debito']:.2f} | Crédito = R$ {valores['credito']:.2f}")
