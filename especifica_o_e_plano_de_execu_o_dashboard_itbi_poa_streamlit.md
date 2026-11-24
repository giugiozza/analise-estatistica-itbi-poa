# Especificação Técnica e Plano de Implementação: Dashboard "Análise Estatística — ITBI Porto Alegre" (Streamlit / Python)

Este documento fornece diretrizes arquiteturais, visuais, estatísticas e um backlog granular de tarefas para o desenvolvimento fiel de um dashboard interativo de 3 abas em **Python + Streamlit**, baseado nas telas de referência fornecidas (`tela1.jpeg`, `tela2.jpeg`, `tela3.jpeg`).

## 1. Arquitetura Técnica e Stack Obrigatória (Python / Streamlit)

* **Restrição de Stack:** A aplicação **DEVE** ser construída exclusivamente em **Python 3.10+** utilizando **Streamlit (`>=1.32.0`)**. Não utilizar React, HTML standalone ou outros frameworks web externos.

* **Bibliotecas Obrigatórias:**

  * `streamlit`: Estrutura de layout (`st.set_page_config(layout="wide")`, `st.sidebar`, `st.tabs`, `st.columns`, `st.container(border=True)`).

  * `pandas` e `numpy`: Manipulação vetorial dos dados do ITBI e geração da Amostra Aleatória Simples (AAS) reprodutível (`np.random.default_rng(seed=42)`).

  * `scipy.stats`: Cálculo de densidade KDE (`gaussian_kde`), quantis da distribuição $t$-Student (`stats.t.ppf`) e Normal padrão (`stats.norm.ppf`), e $p$-valores dos testes de hipótese.

  * `plotly.graph_objects` e `plotly.figure_factory`: Renderização de todos os gráficos (Histograma + KDE, Barras Horizontais, Sparklines e Forest Plots de Intervalos de Confiança) via `st.plotly_chart(..., use_container_width=True, config={'displayModeBar': False})`.

* **Estrutura de Arquivos Recomendada:**

  * `app.py`: Ponto de entrada, injeção de CSS global, renderização da sidebar e navegação entre as 3 abas.

  * `data_loader.py`: Carregamento/geração sintética calibrada dos dados do ITBI POA ($N = 124.582$, Seed `42`) com `@st.cache_data` e funções de cálculo estatístico.

  * `charts.py`: Funções puras que retornam objetos `plotly.graph_objects.Figure` estilizados conforme a paleta de cada painel.

  * `styles.py`: Bloco de CSS customizado injetado via `st.markdown(..., unsafe_allow_html=True)` para ajustar bordas de containers, abas, badges e tabelas.

* **Formatação Numérica (Locale `pt-BR`):**

  * Implementar função auxiliar `fmt_br(valor, casas=1, prefixo="", sufixo="")` que converte ponto decimal em vírgula e ponto como separador de milhar (ex: `124.582`, `94,2 m²`, `72,4%`, `R$ 794,81`).

## 2. Design System e Customização CSS no Streamlit

Para superar a aparência padrão do Streamlit e atingir a fidelidade visual das imagens, injetar CSS em `styles.py`:

### 2.1. Paleta de Cores

* **Fundo Principal (`.stApp`):** `#FFFFFF` (Branco puro).

* **Fundo da Sidebar (`[data-testid="stSidebar"]`):** `#EDF1F5` com borda direita sutil `#E2E8F0`.

* **Cards / Containers (`[data-testid="stVerticalBlockBorderWrapper"]`):** Fundo `#FFFFFF`, borda `1px solid #D1D9E2`, `border-radius: 10px`, `padding: 16px`.

* **Cabeçalho de Tabelas / Caixas de Destaque (Hipóteses):** `#EEF2F6` (Cinza-azulado suave).

* **Tipografia Principal:** `#0F172A` (Azul-marinho escuro).

* **Tipografia Secundária / Abas Inativas:** `#64748B`.

* **Cores de Destaque por Contexto:**

  * **Azul Royal (Aba ativa, Controles de Filtro, Gráficos da População):** `#1849C6`.

  * **Verde-Petróleo / Teal (Gráficos da Amostra, Curva KDE, Intervalos de Confiança):** `#137C7E`.

  * **Verde Esmeralda (Badges positivos, Pill "Rejeitar** $H_0$**", Checkmarks "Sim"):** `#15803D` (Fundo badge suave: `#DCFCE7`).

### 2.2. Ajustes de CSS Específicos do Streamlit

* Ocultar elementos nativos desnecessários: `#MainMenu {visibility: hidden;}`, `footer {visibility: hidden;}`, padding superior excessivo do `.block-container` (`padding-top: 2rem;`).

* **Estilização de `st.tabs`:**

  * Remover o destaque vermelho padrão do Streamlit (`[data-baseweb="tab-highlight"]`).

  * Aplicar `border-bottom: 3px solid #1849C6` e cor `#1849C6` na aba selecionada (`aria-selected="true"`), com fonte `16px` e `font-weight: 600`.

* **Estilização de Sliders (`st.slider`):**

  * Sobrescrever a cor primária no `.streamlit/config.toml` (`primaryColor = "#1849C6"`, `backgroundColor = "#FFFFFF"`, `secondaryBackgroundColor = "#EDF1F5"`, `textColor = "#0F172A"`).

## 3. Especificação Detalhada dos Componentes

### 3.1. Barra Lateral (`with st.sidebar:`)

* **Título:** `st.markdown("## Filtros")`

* **Filtro 1 — Ano de Referência:**

  * Label: `Ano de Referência` + texto dinâmico em negrito/médio `f"{ano_ini} - {ano_fim}"`.

  * Widget: `st.slider("", min_value=2020, max_value=2025, value=(2020, 2025), label_visibility="collapsed")`.

* **Filtro 2 — Tipo de Imóvel:**

  * Widget: `st.selectbox("Tipo de Imóvel", options=["Todos", "Apartamento", "Casa", "Box", "Terreno"], index=0)` (estilizar o valor `"Todos"` para parecer limpo/discreto como na imagem).

* **Seção Intermediária Dinâmica (Controlada pelo estado/aba ou exibida conforme contexto):**

  * *Nota de Implementação Streamlit:* Como `st.tabs` renderiza o conteúdo das 3 abas no mesmo ciclo de execução sem informar nativamente ao `st.sidebar` qual aba está clicada, utilize `st.radio` estilizado como abas horizontais (`horizontal=True`) com `st.session_state["aba_ativa"]` **OU** utilize `st.tabs` e controle o bloco da sidebar via `st.session_state`. **Recomendação:** Usar `st.radio` customizado via CSS como abas horizontais no topo garante 100% de sincronia instantânea entre a aba selecionada e o card contextual exibido na sidebar!

  * **Quando Aba = População:** Nenhum card extra na sidebar.

  * **Quando Aba = Amostra:** Renderizar `st.container(border=True)` com fundo branco:

    * Título: **Parâmetros da AAS**

    * Texto em Markdown:
      `Confiança: **95%**`  
      `Erro: **2%**`  
      `Seed: **42**`

  * **Quando Aba = Inferência e Comparação:** Renderizar `st.container(border=True)` com fundo branco:

    * Título: **Parâmetros de Teste / Inferência**

    * Widget 1: `alpha = st.selectbox("Nível de Significância (α):", [0.05, 0.01, 0.10], index=0)`

    * Widget 2: `conf_ic = st.slider("Confiança do IC:", min_value=80, max_value=99, value=95, format="%d%%")`

* **Rodapé da Sidebar:**

  * Espaçador vertical + HTML badge contornado (`border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 12px;`): `ⓘ Fonte: Dados Abertos POA`.

### 3.2. Cabeçalho Principal

* Renderizado via HTML/Markdown no topo da área principal:

  * Ícone SVG/Emoji de gráfico de barras + `<span style="font-size: 30px; font-weight: 700; color: #0F172A;">Análise Estatística — ITBI Porto Alegre</span>`.

* Barra de navegação horizontal com as 3 opções:

  1. `Painel 1: População`

  2. `Painel 2: Amostra`

  3. `Painel 3: Inferência e Comparação`

### 3.3. Painel 1: População (`tela1.jpeg`)

1. **Linha 1 — 4 Cards de KPI (`st.columns(4)`):**
   Cada coluna contém um `st.container(border=True)` com HTML interno padronizado para garantir alinhamento exato:

   * **Coluna 1:** Ícone DB azul + `População (N)` | Valor `124.582` | Rodapé: pill cinza `Total de registros` + mini gráfico SVG/Plotly sparkline verde + `+6.27%`.

   * **Coluna 2:** Ícone régua + `Área Média` | Valor `94,2 m²`.

   * **Coluna 3:** Ícone prédio + `Mediana da Área` | Valor `72,0 m²`.

   * **Coluna 4:** Ícone edifício + `Proporção de Apartamentos` | Valor `72,4%`.

2. **Linha 2 — 2 Gráficos Lado a Lado (`st.columns(2)`):**

   * **Coluna 1 (`st.container(border=True)`):**

     * Título: **Distribuição da Área Construída (m²)**

     * Plotly `go.Figure()`: `go.Histogram(histnorm='probability density', marker_color='#1849C6', marker_line_color='white', marker_line_width=1)` + `go.Scatter(mode='lines', line=dict(color='#0F5E4D', width=2))` para a curva KDE (calculada via `scipy.stats.gaussian_kde`) + `fig.add_vline(x=115, line_dash="dash", line_color="#0F5E4D", line_width=2)`.

     * Eixo X: `[0, 340]` com ticks a cada `50`. Eixo Y: `[0, 0.18]` com ticks `0, 0.05, 0.1, 0.15`.

   * **Coluna 2 (`st.container(border=True)`):**

     * Título: **Distribuição por Tipo de Imóvel**

     * Plotly `go.Figure()`: `go.Bar(orientation='h', marker_color='#1849C6')` com categorias ordenadas de cima para baixo (`yaxis=dict(autorange="reversed")`): `Apartamento` (\~310), `Casa` (\~148), `Box` (\~45), `Terreno` (\~20).

3. **Linha 3 — Tabela Descritiva (`st.container(border=True)`):**

   * Título: **Estatísticas Descritivas da População**

   * Renderizar tabela HTML estilizada (`width: 100%; border-collapse: collapse;`) para controle total de alinhamento e bordas (melhor que `st.dataframe` para visual editorial):

     * Cabeçalho (`background: #EEF2F6`): `""` (esq) | `Área (m²)` (dir) | `Valor de transação` (dir).

     * Linhas:

       * `Média` | `94,2 m²` | `R$ 794,81`

       * `Mediana` | `72,0 m²` | `R$ 1.958,00`

       * `Desvio Padrão` | `8,8 m²` | `R$ 485,37`

       * `Mínimo` | `0 m²` | `R$ 883,20`

       * `Máximo` | `1.000 m²` | `R$ 33.778,00`

### 3.4. Painel 2: Amostra (`tela2.jpeg`)

1. **Linha 1 — 4 Cards de KPI (`st.columns(4)`):**

   * **Coluna 1:** Ícone barras + `Amostra AAS (n)` | Valor `2.385` | Rodapé: pill `Total de registros` + sparkline + badge verde `+0,15%`.

   * **Coluna 2:** Ícone régua + `Área Média Amostral` | Valor `93,8 m²` | Rodapé: linha sparkline ondulada em teal (`#137C7E`) ocupando a largura do card.

   * **Coluna 3:** Ícone prédio + `Mediana Amostral` | Valor `71,5 m²`.

   * **Coluna 4:** Ícone edifício + `Proporção de Apartamentos` | Valor `71,8%`.

2. **Linha 2 — 2 Gráficos Lado a Lado (`st.columns(2)`):**

   * **Coluna 1:** **Distribuição da Área Construída — Amostra (m²)** (mesma estrutura do Painel 1, porém barras do histograma em `#137C7E`).

   * **Coluna 2:** **Distribuição por Tipo de Imóvel — Amostra** (barras horizontais em `#137C7E`).

3. **Linha 3 — Tabela Descritiva (`st.container(border=True)`):**

   * Título: **Estatísticas Descritivas da Amostra (AAS)**

   * Cabeçalho: `Estatística` (esq) | `Área (m²)` (dir) | `Valor de transação` (dir).

   * Valores: Média (`93,8 m²` | `R$ 791,20`), Mediana (`71,5 m²` | `R$ 1.950,00`), Desvio Padrão (`8,7 m²` | `R$ 481,50`), Mínimo (`0 m²` | `R$ 960,00`), Máximo (`1.000 m²` | `R$ 31.500,00`).

### 3.5. Painel 3: Inferência e Comparação (`tela3.jpeg`)

1. **Linha 1 — 2 Cards de Teste de Hipótese (`st.columns(2)`):**

   * **Coluna 1 (`st.container(border=True)`):**

     * Título: **Teste de Média: Área Construída (< 100 m²)**

     * Box HTML cinza (`background: #EEF2F6; border-radius: 6px; padding: 10px; text-align: center;`):
       `H₀: μ = 100 m²  |  H₁: μ < 100 m²`

     * **Gráfico Plotly Customizado (`go.Figure`):**

       * Eixo Y categórico (3 níveis de cima para baixo): `Média Amostra`, `95% Confidance` *(atualizar dinamicamente para `f"{conf_ic}% Confidance"`)*, `População Mean`.

       * Traço 1 (`y="Média Amostra"`): `go.Scatter(x=[93.8], mode="markers+text", text=["93,8 m²"], textposition="middle left", marker=dict(size=10, color="#137C7E"))`.

       * Traço 2 (`y="95% Confidance"`): Barra espessa horizontal simulada via `go.Scatter(x=[ic_inf, ic_sup], mode="lines", line=dict(color="#137C7E", width=22))` + marcador central vertical + anotação `94,4` à direita.

       * Traço 3 (`y="População Mean"`): `go.Scatter(x=[94.2], mode="markers", marker=dict(symbol="diamond", size=11, color="#137C7E"))` + linha pontilhada vertical conectando à média amostral.

       * Linha de Referência $H_0$: `fig.add_vline(x=100, line_dash="dash", line_color="#137C7E", line_width=2)` + anotação superior `100 m²` e badge retangular teal `100 m²`.

     * **Rodapé do Card (HTML Flexbox 3 colunas):**

       * Esquerda: `Estatística t: -15,42`

       * Centro: `Valor-p: < 0,001`

       * Direita: `<span style="background:#15803D; color:white; padding:4px 12px; border-radius:999px; font-weight:600;">Rejeitar H₀</span>` (se `p_valor < alpha`, senão `Não Rejeitar H₀` em cinza).

   * **Coluna 2 (`st.container(border=True)`):**

     * Título: **Teste de Proporção: Apartamentos (> 50%)**

     * Box HTML cinza: `H₀: p = 50%  |  H₁: p > 50%`

     * **Gráfico Plotly Customizado:**

       * Eixo Y: `Amostra Propor...`, `95% Confidance`, `População Prop..`.

       * Eixo X: `[30, 82]` com ticks `30%, 40%, 50%, 60%, 70%, 80%`.

       * Linha $H_0$ em `50` com rótulo `50%` no topo.

       * Ponto amostral `~71,8%`, barra IC `[~70,5% ; ~73,1%]`, ponto populacional `72,4%`.

     * **Rodapé do Card:** `Estatística z: 21,34` | `Valor-p: < 0,001` | Pill `Rejeitar H₀`.

2. **Linha 2 — Tabela Comparativa (`st.container(border=True)`):**

   * Título: **Comparação: Parâmetros da População vs. Estimativas Amostrais**

   * Tabela HTML de 5 colunas:

     * `Área Média (m²)` | `94,2 m²` | `93,8 m²` | `[93,2 m²; 94,4 m²]` | `✓ Sim` (cor `#15803D`, negrito)

     * `Mediana da Área (m²)` | `72,0 m²` | `71,5 m²` | `[70,9 m²; 72,1 m²]` | `✓ Sim`

     * `Proporção de Apts.` | `72,4%` | `71,8%` | `[70,2%; 73,4%]` | `✓ Sim`

## 4. Plano de Execução Granular (Backlog para a IA)

Execute cada etapa isoladamente e valide os critérios antes de prosseguir.

### Etapa 1: Setup do Projeto e Motor Estatístico (`data_loader.py`)

* **Tarefa 1.1:** Criar `.streamlit/config.toml` configurando `primaryColor = "#1849C6"`, `backgroundColor = "#FFFFFF"`, `secondaryBackgroundColor = "#EDF1F5"`, `textColor = "#0F172A"`, e `font = "sans serif"`.

* **Tarefa 1.2:** Implementar `data_loader.py` com `@st.cache_data` gerando o DataFrame populacional sintético calibrado ($N = 124.582$ registros entre `2020` e `2025`, com proporções de tipos de imóvel e distribuição assimétrica à direita de área construída e valor de transação que reproduzam exatamente as estatísticas das telas: média `94,2 m²`, mediana `72,0 m²`, DP `8,8 m²`, proporção de apartamentos `72,4%`).

* **Tarefa 1.3:** Implementar função `gerar_amostra_e_inferencia(df_filtrado, seed=42, conf_ic=95, alpha=0.05)` usando `np.random.default_rng(seed)` e `scipy.stats` para extrair a amostra ($n = 2.385$ no filtro completo) e calcular intervalos de confiança, estatística $t$, estatística $z$ e $p$-valores dinamicamente.

* *Validação da Etapa 1:* Executar script de teste unitário verificando que, com filtros padrão, os números gerados batem com `tela1.jpeg`, `tela2.jpeg` e `tela3.jpeg`.

### Etapa 2: Estilização Global e Shell de Navegação (`styles.py` e `app.py`)

* **Tarefa 2.1:** Criar `styles.py` com CSS customizado para:

  * Estilizar `st.container(border=True)` com borda `#D1D9E2` e raio `10px`.

  * Estilizar `st.radio(..., horizontal=True)` no topo da página para imitar perfeitamente abas horizontais com linha inferior contínua cinza e sublinhado azul `#1849C6` de `3px` na opção ativa.

  * Criar classes CSS utilitárias para tabelas HTML (`.itbi-table`), badges (`.badge-green`, `.badge-gray`) e cards de KPI (`.kpi-title`, `.kpi-value`).

* **Tarefa 2.2:** Montar `app.py` com `st.set_page_config(page_title="Análise Estatística — ITBI Porto Alegre", layout="wide")`, renderizar a sidebar com os filtros (`Ano de Referência` e `Tipo de Imóvel`), o bloco condicional baseado em `st.session_state["aba_ativa"]` e o badge fixo `Fonte: Dados Abertos POA`.

* *Validação da Etapa 2:* Rodar `streamlit run app.py` e confirmar que alternar entre as 3 abas muda instantaneamente o conteúdo da sidebar (vazio na Aba 1, "Parâmetros da AAS" na Aba 2, "Parâmetros de Teste / Inferência" na Aba 3).

### Etapa 3: Gráficos Plotly Reutilizáveis (`charts.py`)

* **Tarefa 3.1:** Implementar `plot_histograma_kde(serie, cor_barras, titulo_eixo_x)` usando `go.Histogram` + `scipy.stats.gaussian_kde` + `add_vline`, com fundo transparente (`paper_bgcolor='rgba(0,0,0,0)'`, `plot_bgcolor='rgba(0,0,0,0)'`) e margens compactas (`margin=dict(l=20, r=20, t=10, b=30)`).

* **Tarefa 3.2:** Implementar `plot_barras_horizontais(df_contagem, cor_barras)` com eixos limpos e ordem decrescente de frequência.

* **Tarefa 3.3:** Implementar `plot_sparkline(valores, cor, area=False)` para os mini-gráficos dentro dos cards de KPI da População e da Amostra.

* **Tarefa 3.4:** Implementar `plot_forest_inferencia(est_amostra, ic_inf, ic_sup, param_pop, h0_val, labels_y, formato_pct=False, conf_nivel=95)` para os dois gráficos de teste de hipótese do Painel 3.

* *Validação da Etapa 3:* Verificar visualmente cada gráfico isoladamente, garantindo ausência de barra de ferramentas flutuante do Plotly (`displayModeBar: False`) e proporções fiéis às imagens.

### Etapa 4: Montagem dos 3 Painéis e Validação Final

* **Tarefa 4.1:** Implementar a renderização completa do **Painel 1: População** em `app.py` (4 cards de KPI + 2 gráficos em `#1849C6` + tabela descritiva HTML).

* **Tarefa 4.2:** Implementar a renderização completa do **Painel 2: Amostra** (4 cards de KPI com sparkline no card de área + 2 gráficos em `#137C7E` + tabela descritiva HTML).

* **Tarefa 4.3:** Implementar a renderização completa do **Painel 3: Inferência e Comparação** (2 cards de teste de hipótese com caixas de fórmulas $H_0/H_1$, gráficos forest e rodapés reativos a `alpha` e `conf_ic` + tabela comparativa inferior com verificação automática `✓ Sim`).

* *Validação Final (QA):* Testar interatividade completa no navegador: mover o slider de anos (`2020-2025`), filtrar por `Apartamento`, alterar `Confiança do IC` de `95%` para `99%` no Painel 3 (observando o alargamento da barra teal no gráfico e atualização da tabela comparativa) e recolher/expandir a sidebar pelo botão `×` nativo do Streamlit.