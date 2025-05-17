import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale

# Configuração da página
st.set_page_config(
    page_title="Dashboard Debito e Credito - Condomínio",
    page_icon="🏢",
    layout="wide"
)

# Configuração do estilo dos gráficos
def configurar_grafico(fig):
    fig.update_layout(
        font=dict(size=14),
        title_font=dict(size=20),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16)
    )
    return fig

# Configuração do locale para formatação de valores em reais
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Função para formatar valores em reais
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Carregando os dados
@st.cache_data
def load_data():
    df = pd.read_csv('extrato_completo_2024.csv')
    # Convertendo a coluna valor para float
    df['valor'] = df['valor'].str.replace('.', '').str.replace(',', '.').astype(float)
    # Convertendo a coluna data_operacao para datetime
    df['data_operacao'] = pd.to_datetime(df['data_operacao'])
    return df

# Carregando os dados
df = load_data()

# Título do dashboard
st.title("📊 Dashboard Debito e Credito - Condomínio")
st.markdown("---")

# Sidebar para filtros
st.sidebar.header("Filtros")

# Lista ordenada dos meses
meses_ordenados = [
    'JANEIRO', 'FEVEREIRO', 'MARCO', 'ABRIL', 'MAIO', 'JUNHO',
    'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
]

# Criando lista de meses com ano
df['mes_ano'] = df['mes'] + ' ' + df['data_operacao'].dt.strftime('%Y')
meses_com_ano = sorted(df['mes_ano'].unique(), key=lambda x: meses_ordenados.index(x.split()[0]))

# Filtro por mês
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", ["Todos"] + list(meses_com_ano))

# Filtro por tipo de transação
tipo_transacao = st.sidebar.multiselect(
    "Tipo de Transação",
    options=["Todos", "Débito", "Crédito"],
    default=["Todos"]
)

# Aplicando filtros
df_filtrado = df.copy()
if mes_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['mes_ano'] == mes_selecionado]
if "Todos" not in tipo_transacao:
    tipos_filtrados = []
    for tipo in tipo_transacao:
        if tipo == "Débito":
            tipos_filtrados.append("debito")
        elif tipo == "Crédito":
            tipos_filtrados.append("credito")
    df_filtrado = df_filtrado[df_filtrado['tipo'].isin(tipos_filtrados)]

# Métricas principais
col1, col2, col3 = st.columns(3)

# Total de débitos
total_debitos = df_filtrado[df_filtrado['tipo'] == 'debito']['valor'].sum()
col1.metric("Total de Débitos", format_currency(total_debitos))

# Total de créditos
total_creditos = df_filtrado[df_filtrado['tipo'] == 'credito']['valor'].sum()
col2.metric("Total de Créditos", format_currency(total_creditos))

# Saldo
saldo = total_creditos - total_debitos
delta_color = "inverse" if saldo < 0 else "normal"
col3.metric("Saldo", format_currency(saldo), delta=format_currency(saldo), delta_color=delta_color)

# Gráficos
st.markdown("---")
st.subheader("Análise de Movimentações")

# Gráfico de linha - Evolução do saldo
df_diario = df_filtrado.groupby('data_operacao').agg({
    'valor': lambda x: sum(x[df_filtrado['tipo'] == 'credito']) - sum(x[df_filtrado['tipo'] == 'debito'])
}).reset_index()

fig_evolucao = px.line(
    df_diario,
    x='data_operacao',
    y='valor',
    title='Evolução do Saldo Diário',
    labels={'valor': 'Saldo (R$)', 'data_operacao': 'Data'}
)
fig_evolucao = configurar_grafico(fig_evolucao)
st.plotly_chart(fig_evolucao, use_container_width=True)

# Gráfico de barras - Débitos vs Créditos por mês
df_mensal = df_filtrado.groupby(['mes', 'tipo'])['valor'].sum().reset_index()
fig_barras = px.bar(
    df_mensal,
    x='mes',
    y='valor',
    color='tipo',
    title='Débitos vs Créditos por Mês',
    labels={'valor': 'Valor (R$)', 'mes': 'Mês', 'tipo': 'Tipo'},
    color_discrete_map={'debito': '#FF0000', 'credito': '#00FF00'}
)
fig_barras = configurar_grafico(fig_barras)
st.plotly_chart(fig_barras, use_container_width=True)

# Maiores transações
st.markdown("---")
st.subheader("Maiores Transações")

# Top 10 maiores transações
top_transacoes = df_filtrado.nlargest(10, 'valor')[['data_operacao', 'descricao', 'valor', 'tipo']]
top_transacoes['data_operacao'] = top_transacoes['data_operacao'].dt.strftime('%d/%m/%Y')
top_transacoes['valor'] = top_transacoes['valor'].apply(format_currency)

# Estilização condicional para a coluna tipo
def colorir_tipo(valor):
    if valor == 'credito':
        return 'color: #00FF00'
    else:
        return 'color: #FF0000'

# Configuração do estilo da tabela
st.dataframe(
    top_transacoes.style
    .map(colorir_tipo, subset=['tipo'])
    .set_properties(**{
        'font-size': '16px',
        'padding': '10px',
        'text-align': 'left'
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('font-size', '18px'),
            ('padding', '12px'),
            ('background-color', '#f0f2f6'),
            ('font-weight', 'bold')
        ]}
    ]),
    use_container_width=True,
    height=400
)

# Análise de categorias
st.markdown("---")
st.subheader("Análise por Categorias")

# Identificando categorias principais
categorias = {
    'PAGAMENTO': 'Pagamentos',
    'PIX': 'Transferências PIX',
    'COBRANCA': 'Cobranças',
    'APL': 'Aplicações',
    'RESGATE': 'Resgates',
    'TARIFA': 'Tarifas',
    'SAQUE': 'Saques'
}

df_filtrado['categoria'] = df_filtrado['descricao'].apply(
    lambda x: next((v for k, v in categorias.items() if k in x), 'Outros')
)

# Gráfico de pizza por categoria
df_categorias = df_filtrado.groupby('categoria')['valor'].sum().reset_index()
fig_pizza = px.pie(
    df_categorias,
    values='valor',
    names='categoria',
    title='Distribuição por Categoria',
    height=600,
    width=800
)
fig_pizza = configurar_grafico(fig_pizza)
fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig_pizza, use_container_width=True)

# Novos gráficos
st.markdown("---")
st.subheader("Análises Adicionais")

# Gráfico de linha - Tendência de Débitos e Créditos
df_tendencia = df_filtrado.groupby(['data_operacao', 'tipo'])['valor'].sum().reset_index()
fig_tendencia = px.line(
    df_tendencia,
    x='data_operacao',
    y='valor',
    color='tipo',
    title='Tendência de Débitos e Créditos',
    labels={'valor': 'Valor (R$)', 'data_operacao': 'Data', 'tipo': 'Tipo'},
    color_discrete_map={'debito': '#FF0000', 'credito': '#00FF00'}
)
fig_tendencia = configurar_grafico(fig_tendencia)
st.plotly_chart(fig_tendencia, use_container_width=True)

# Gráfico de barras empilhadas - Composição dos Débitos por Categoria
df_debitos_categoria = df_filtrado[df_filtrado['tipo'] == 'debito'].groupby(['mes', 'categoria'])['valor'].sum().reset_index()
fig_debitos = px.bar(
    df_debitos_categoria,
    x='mes',
    y='valor',
    color='categoria',
    title='Composição dos Débitos por Categoria',
    labels={'valor': 'Valor (R$)', 'mes': 'Mês', 'categoria': 'Categoria'}
)
fig_debitos = configurar_grafico(fig_debitos)
st.plotly_chart(fig_debitos, use_container_width=True)

# Top 5 Maiores Transações
col1, col2 = st.columns(2)

# Top 5 Débitos
if 'debito' in df_filtrado['tipo'].unique():
    top_debitos = df_filtrado[df_filtrado['tipo'] == 'debito'].nlargest(5, 'valor')
    fig_top_debitos = px.bar(
        top_debitos,
        x='valor',
        y='descricao',
        orientation='h',
        title='Top 5 Maiores Débitos',
        labels={'valor': 'Valor (R$)', 'descricao': 'Descrição'},
        color_discrete_sequence=['#FF0000']
    )
    fig_top_debitos = configurar_grafico(fig_top_debitos)
    col1.plotly_chart(fig_top_debitos, use_container_width=True)
else:
    col1.markdown("### Top 5 Maiores Débitos")
    col1.info("Não há débitos no período selecionado")

# Top 5 Créditos
if 'credito' in df_filtrado['tipo'].unique():
    top_creditos = df_filtrado[df_filtrado['tipo'] == 'credito'].nlargest(5, 'valor')
    fig_top_creditos = px.bar(
        top_creditos,
        x='valor',
        y='descricao',
        orientation='h',
        title='Top 5 Maiores Créditos',
        labels={'valor': 'Valor (R$)', 'descricao': 'Descrição'},
        color_discrete_sequence=['#00FF00']
    )
    fig_top_creditos = configurar_grafico(fig_top_creditos)
    col2.plotly_chart(fig_top_creditos, use_container_width=True)
else:
    col2.markdown("### Top 5 Maiores Créditos")
    col2.info("Não há créditos no período selecionado")

# Gráfico de dispersão - Correlação entre Débitos e Créditos
if len(df_filtrado) > 0:
    df_diario_tipo = df_filtrado.groupby(['data_operacao', 'tipo'])['valor'].sum().reset_index()
    df_diario_pivot = df_diario_tipo.pivot(index='data_operacao', columns='tipo', values='valor').fillna(0)
    
    if 'debito' in df_diario_pivot.columns and 'credito' in df_diario_pivot.columns:
        fig_dispersao = px.scatter(
            df_diario_pivot.reset_index(),
            x='debito',
            y='credito',
            title='Correlação entre Débitos e Créditos',
            labels={'debito': 'Débitos (R$)', 'credito': 'Créditos (R$)'}
        )
        fig_dispersao = configurar_grafico(fig_dispersao)
        st.plotly_chart(fig_dispersao, use_container_width=True)
    else:
        st.info("Não há dados suficientes para mostrar a correlação entre débitos e créditos")
else:
    st.info("Não há dados no período selecionado")

# Gráfico de área - Saldo Acumulado
if len(df_filtrado) > 0 and 'debito' in df_diario_pivot.columns and 'credito' in df_diario_pivot.columns:
    df_saldo_acumulado = df_diario_pivot.copy()
    df_saldo_acumulado['saldo'] = df_saldo_acumulado['credito'] - df_saldo_acumulado['debito']
    df_saldo_acumulado['saldo_acumulado'] = df_saldo_acumulado['saldo'].cumsum()

    fig_saldo = px.area(
        df_saldo_acumulado.reset_index(),
        x='data_operacao',
        y='saldo_acumulado',
        title='Saldo Acumulado',
        labels={'saldo_acumulado': 'Saldo (R$)', 'data_operacao': 'Data'}
    )
    fig_saldo = configurar_grafico(fig_saldo)
    st.plotly_chart(fig_saldo, use_container_width=True)
else:
    st.info("Não há dados suficientes para mostrar o saldo acumulado")

# Gráfico de Calendário
if len(df_filtrado) > 0:
    df_calendario = df_filtrado.copy()
    df_calendario['dia'] = df_calendario['data_operacao'].dt.day
    df_calendario['mes_ano'] = df_calendario['data_operacao'].dt.strftime('%Y-%m')
    df_calendario_pivot = df_calendario.pivot_table(
        index='dia',
        columns='mes_ano',
        values='valor',
        aggfunc='sum'
    ).fillna(0)

    fig_calendario = px.imshow(
        df_calendario_pivot,
        title='Distribuição de Transações por Dia',
        labels={'x': 'Mês', 'y': 'Dia', 'color': 'Valor (R$)'},
        color_continuous_scale='RdYlGn'
    )
    fig_calendario = configurar_grafico(fig_calendario)
    st.plotly_chart(fig_calendario, use_container_width=True)
else:
    st.info("Não há dados suficientes para mostrar o calendário de transações")

# Rodapé
st.markdown("---")
st.subheader("Consulta Completa de Transações")

# Adicionando campo de pesquisa
termo_pesquisa = st.text_input("🔍 Pesquisar por descrição ou documento")

# Filtrando dados com base na pesquisa
if termo_pesquisa:
    df_consulta = df[
        df['descricao'].str.contains(termo_pesquisa, case=False) |
        df['doc'].str.contains(termo_pesquisa, case=False)
    ]
else:
    df_consulta = df

# Formatando a tabela
df_consulta = df_consulta[['data_operacao', 'descricao', 'doc', 'valor', 'tipo']].copy()
df_consulta['data_operacao'] = df_consulta['data_operacao'].dt.strftime('%d/%m/%Y')
df_consulta['valor'] = df_consulta['valor'].apply(format_currency)

# Estilização da tabela
def colorir_tipo(valor):
    if valor == 'credito':
        return 'color: #00FF00'
    else:
        return 'color: #FF0000'

# Exibindo a tabela com funcionalidades de pesquisa e ordenação
st.dataframe(
    df_consulta.style
    .map(colorir_tipo, subset=['tipo'])
    .set_properties(**{
        'font-size': '14px',
        'padding': '8px',
        'text-align': 'left'
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('font-size', '16px'),
            ('padding', '10px'),
            ('background-color', '#f0f2f6'),
            ('font-weight', 'bold')
        ]}
    ]),
    use_container_width=True,
    height=400
)

# Rodapé
st.markdown("---")
st.markdown("Dashboard criado com Streamlit | Última atualização: " + datetime.now().strftime("%d/%m/%Y"))
