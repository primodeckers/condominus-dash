import streamlit as st

# Configuração da página (DEVE ser a primeira chamada do Streamlit)
st.set_page_config(
    page_title="Debito/Credito - Ouro vermelho I - 2024",
    page_icon="🏢",
    layout="wide"
)

# Resto das importações
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import locale
from urllib.parse import urlencode
from auth import verificar_autenticacao, logout, obter_nome_usuario

# Verifica autenticação
if not verificar_autenticacao():
    st.stop()

# Título do dashboard
st.title("📊 Dashboard Debito e Credito - Condomínio")

# CSS personalizado para ajustar espaçamentos
st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        padding: 0.1rem 1rem;
        font-size: 0.8rem;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        margin-top: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
    }
    div[data-testid="stVerticalBlock"] > div:has(> div.stTabs) {
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Informações do usuário e botão de sair na sidebar
nome_usuario = obter_nome_usuario()
if nome_usuario:
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.markdown(f"### 👤 {nome_usuario}")
    with col2:
        if st.button("Sair", type="primary"):
            logout()
            st.stop()
    st.sidebar.markdown("---")

# Sidebar para filtros
st.sidebar.header("Filtros")

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
try:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

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

# Após aplicar os filtros em df_filtrado
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

# Métricas principais
col1, col2, col3 = st.columns(3)

# Total de débitos
total_debitos = df_filtrado[df_filtrado['tipo'] == 'debito']['valor'].sum()

# Total de débitos em vermelho
with col1:
    st.markdown(
        "<div style='background:#fff0f0; border:1px solid #FF0000; border-radius:5px; padding:20px; text-align:center; min-height:150px; display:flex; flex-direction:column; justify-content:center;'>"
        "<div style='color:#FF0000; font-size:1.1em; font-weight:bold; margin-bottom:8px;'>Total de Débitos</div>"
        f"<span style='color:#FF0000; font-size:2em; font-weight:bold;'>- {format_currency(total_debitos)}</span>"
        "</div>",
        unsafe_allow_html=True
    )

# Total de créditos
total_creditos = df_filtrado[df_filtrado['tipo'] == 'credito']['valor'].sum()

# Total de créditos em verde
with col2:
    st.markdown(
        "<div style='background:#f0fff0; border:1px solid #00B050; border-radius:5px; padding:20px; text-align:center; min-height:150px; display:flex; flex-direction:column; justify-content:center;'>"
        "<div style='color:#00B050; font-size:1.1em; font-weight:bold; margin-bottom:8px;'>Total de Créditos</div>"
        f"<span style='color:#00B050; font-size:2em; font-weight:bold;'>+ {format_currency(total_creditos)}</span>"
        "</div>",
        unsafe_allow_html=True
    )

# Saldo
saldo = total_creditos - total_debitos
delta_color = "inverse" if saldo < 0 else "normal"

# Saldo (mantém o st.metric para o delta)
with col3:
    cor = "#00B050" if saldo > 0.01 else "#FF0000" if saldo < -0.01 else "#808080"
    bg = "#f0fff0" if saldo > 0.01 else "#fff0f0" if saldo < -0.01 else "#f0f0f0"
    if saldo > 0.01:
        sinal = "+"
        extra = " <span style='font-size:1.2em;'>🡅</span>"
    elif saldo < -0.01:
        sinal = "-"
        extra = " <span style='font-size:1.2em;'>🡇</span>"
    else:
        sinal = ""
        extra = " <span style='font-size:1.2em;'>#</span>"
    st.markdown(
        f"<div style='background:{bg}; border:1px solid {cor}; border-radius:5px; padding:20px; text-align:center; min-height:150px; display:flex; flex-direction:column; justify-content:center;'>"
        f"<div style='color:{cor}; font-size:1.1em; font-weight:bold; margin-bottom:8px;'>Saldo</div>"
        f"<span style='color:{cor}; font-size:2em; font-weight:bold;'>{sinal} {format_currency(abs(saldo))}{extra}</span>"
        "</div>",
        unsafe_allow_html=True
    )

# Após o bloco das métricas principais (Total de Débitos, Créditos, Saldo)
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Gráficos

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

# Gráfico de linha - Evolução do saldo
df_diario = df_filtrado.groupby('data_operacao').agg({
    'valor': lambda x: sum(x[df_filtrado['tipo'] == 'credito']) - sum(x[df_filtrado['tipo'] == 'debito'])
}).reset_index()

fig_evolucao = px.line(
    df_diario,
    x='data_operacao',
    y='valor',
    labels={'valor': 'Saldo (R$)', 'data_operacao': 'Data'},
    markers=True
)
fig_evolucao.update_layout(title=" ")
fig_evolucao.update_traces(
    text=df_diario['valor'].apply(lambda x: f"R$ {x:,.2f}"),
    textposition="top center"
)
fig_evolucao.add_hline(y=0, line_dash="dash", line_color="gray")
fig_evolucao.update_traces(
    hovertemplate='Data: %{x}<br>Saldo: R$ %{y:,.2f}<extra></extra>'
)
fig_evolucao = configurar_grafico(fig_evolucao)

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

# Gráfico de tendência de Débitos e Créditos
df_tendencia = df_filtrado.groupby(['data_operacao', 'tipo'])['valor'].sum().reset_index()
fig_tendencia = px.line(
    df_tendencia,
    x='data_operacao',
    y='valor',
    color='tipo',
    title='Tendência de Débitos e Créditos',
    labels={'valor': 'Valor (R$)', 'data_operacao': 'Data', 'tipo': 'Tipo'},
    color_discrete_map={'debito': '#FF0000', 'credito': '#00FF00'},
    markers=True
)
fig_tendencia.update_traces(
    text=df_tendencia['valor'].apply(lambda x: f"R$ {x:,.2f}"),
    textposition="top center"
)
fig_tendencia.add_hline(y=0, line_dash="dash", line_color="gray")
fig_tendencia.update_traces(
    hovertemplate='Tipo: %{legendgroup}<br>Data: %{x}<br>Valor: R$ %{y:,.2f}<extra></extra>'
)
fig_tendencia = configurar_grafico(fig_tendencia)

# Gráfico de bolhas
df_bolhas = df_filtrado.copy()
df_bolhas['valor_abs'] = df_bolhas['valor'].abs()
fig_bolhas = px.scatter(
    df_bolhas,
    x='data_operacao',
    y='valor',
    size='valor_abs',
    color='tipo',
    hover_name='descricao',
    title='Movimentações por Data (Gráfico de Bolhas)',
    labels={'valor': 'Valor (R$)', 'data_operacao': 'Data', 'tipo': 'Tipo'},
    color_discrete_map={'debito': '#FF0000', 'credito': '#00FF00'},
    size_max=40,
    opacity=0.7
)
fig_bolhas.update_traces(
    hovertemplate='Data: %{x}<br>Valor: R$ %{y:,.2f}<br>Tipo: %{marker.color}<br>Descrição: %{hovertext}<extra></extra>'
)
fig_bolhas = configurar_grafico(fig_bolhas)

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

# Criação do gráfico Top 5 Maiores Débitos antes das tabs
if 'debito' in df_filtrado['tipo'].unique():
    top_debitos = df_filtrado[df_filtrado['tipo'] == 'debito'].nlargest(5, 'valor')
    fig_top_debitos = px.bar(
        top_debitos,
        x='valor',
        y='descricao',
        orientation='h',
        labels={'valor': 'Valor (R$)', 'descricao': 'Descrição'},
        color_discrete_sequence=['#FF0000'],
        title='Top 5 Maiores Débitos'
    )
    fig_top_debitos = configurar_grafico(fig_top_debitos)
    fig_top_debitos.update_layout(
        xaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#333',  # cor mais escura
            gridcolor='#cccccc'  # cor da grade
        ),
        yaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#333',
            gridcolor='#cccccc'
        )
    )
else:
    fig_top_debitos = None

# Tabs de navegação

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Evolução do Saldo",
    "Débitos vs Créditos",
    "Tendência Débitos/Créditos",
    "Bolhas",
    "Composição Débitos",
    "Consulta Completa",
    "Distribuição por Categoria",
    "Maiores Transações",
    "Top 5 Maiores"
])

with tab1:
    st.plotly_chart(fig_evolucao, use_container_width=True, key="evolucao")
with tab2:
    st.plotly_chart(fig_barras, use_container_width=True, key="barras")
with tab3:
    st.plotly_chart(fig_tendencia, use_container_width=True, key="tendencia")
with tab4:
    st.plotly_chart(fig_bolhas, use_container_width=True, key="bolhas")
with tab5:
    st.plotly_chart(fig_debitos, use_container_width=True, key="debitos")
with tab6:
    st.subheader("Consulta Completa de Transações")
    termo_pesquisa = st.text_input("🔍 Pesquisar por descrição ou valor")
    if termo_pesquisa:
        df_consulta = df[
            df['descricao'].astype(str).str.contains(termo_pesquisa, case=False, na=False) |
            df['valor'].astype(str).str.contains(termo_pesquisa, case=False, na=False)
        ]
    else:
        df_consulta = df
    df_consulta = df_consulta[['data_operacao', 'descricao', 'doc', 'valor', 'tipo']].copy()
    df_consulta['data_operacao'] = df_consulta['data_operacao'].dt.strftime('%d/%m/%Y')
    df_consulta['valor'] = df_consulta['valor'].apply(format_currency)
    def colorir_tipo(valor):
        if valor == 'credito':
            return 'color: #00FF00'
        else:
            return 'color: #FF0000'
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
with tab7:
    st.plotly_chart(fig_pizza, use_container_width=True, key="pizza")
with tab8:
    st.subheader("Maiores Transações")
    top_transacoes = df_filtrado.nlargest(10, 'valor')[['data_operacao', 'descricao', 'valor', 'tipo']]
    top_transacoes['data_operacao'] = top_transacoes['data_operacao'].dt.strftime('%d/%m/%Y')
    top_transacoes['valor'] = top_transacoes['valor'].apply(format_currency)
    def colorir_tipo(valor):
        if valor == 'credito':
            return 'color: #00FF00'
        else:
            return 'color: #FF0000'
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
with tab9:
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
            labels={'valor': 'Valor (R$)', 'descricao': 'Descrição'},
            color_discrete_sequence=['#FF0000'],
            title='Top 5 Maiores Débitos'
        )
        fig_top_debitos = configurar_grafico(fig_top_debitos)
        fig_top_debitos.update_layout(
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor='#333',  # cor mais escura
                gridcolor='#cccccc'  # cor da grade
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor='#333',
                gridcolor='#cccccc'
            )
        )
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

# Análise de categorias




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
else:
    st.info("Não há dados suficientes para mostrar o calendário de transações")

# Rodapé
st.markdown("---")
st.markdown("Dashboard criado por Deckers com Streamlit | Última atualização: " + datetime.now().strftime("%d/%m/%Y"))

# Cálculo dos totais de créditos e débitos
total_creditos = df_filtrado[df_filtrado['tipo'] == 'credito']['valor'].sum()
total_debitos = df_filtrado[df_filtrado['tipo'] == 'debito']['valor'].sum()

# Impressão com símbolos coloridos (usando códigos ANSI para terminal)

st.markdown("""
    <style>
    /* Estiliza as abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        color: #333;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-size: 1.1em;
        font-weight: bold;
        margin-right: 2px;
        border: 1px solid #e0e0e0;
    }
    .stTabs [aria-selected="true"] {
        background: #00B050 !important;
        color: #fff !important;
        border-bottom: 2px solid #00B050 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #cce6cc;
        color: #222;
    }
    </style>
""", unsafe_allow_html=True)


