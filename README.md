# Inspeção de Qualidade Automática de Biscoitos (PDI)

Este repositório contém a implementação do projeto final para a disciplina de **Processamento Digital de Imagens (PDI)** do curso de Ciência da Computação da **Universidade Federal do Piauí (UFPI)**.

O objetivo do sistema é analisar de forma automatizada a qualidade física e a integridade de biscoitos industriais (como *cream crackers*), classificando-os entre **Perfeito** ou **Defeito** com base em processamento digital de imagem clássico.

---

## 🛠️ O Pipeline de Processamento (PDI)

O algoritmo utiliza uma sequência linear de filtros e operações morfológicas:
1. **Conversão de Escala**: RGB para Tons de Cinza.
2. **Suavização Espacial**: Aplicação de um Filtro Gaussiano $5 \times 5$ para redução de ruído de textura e sensores.
3. **Segmentação (Otsu)**: Limiarização automática binarizada invertida para separar o objeto do fundo.
4. **Morfologia**: Operações de Abertura e Fechamento com elementos estruturantes elípticos de $5 \times 5$ para limpar o contorno da bolacha.
5. **Extração Geométrica**: Cálculo da **Área** e **Solidez** do contorno da bolacha (usando *convex hull*) para identificar rachaduras e quebras físicas.
6. **Inspeção de Furos**: Isolamento de regiões escuras internas, limpeza morfológica e filtragem por área para contagem precisa de furos.
7. **Classificação**: Validação lógica dos parâmetros.

---

## 📂 Estrutura do Projeto

```
trabalhoFinalPDI/
├── dataset/                  # Banco de imagens de teste (sintéticas e reais)
│   ├── perfeito/
│   └── defeito/
├── scripts/
│   ├── generate_synthetic.py # Gerador de amostras sintéticas sob ruído e rotação
│   └── pipeline.py           # Funções principais do pipeline de PDI
├── results/                  # Saídas, relatórios e gráficos gerados
│   ├── passo_a_passo_perfeito.png
│   ├── passo_a_passo_defeito.png
│   └── metricas_inspecao.txt
├── main.py                   # Script principal para execução em lote e avaliação
├── relatorio.tex             # Relatório acadêmico formatado no modelo SBC (LaTeX)
├── requirements.txt          # Dependências do Python
└── .gitignore                # Regras de exclusão do Git (ignora o venv)
```

---

## 🚀 Como Executar o Projeto

### 1. Clonar e Instalar as Dependências

Primeiro, clone o repositório no seu computador e crie um ambiente virtual do Python:

```bash
# Criar o ambiente virtual
python3 -m venv venv

# Ativar o ambiente virtual (macOS / Linux)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Rodar a Avaliação e Ver as Métricas

Para executar o pipeline em todo o dataset e gerar as matrizes e gráficos passo a passo:

```bash
python main.py
```

Os resultados e as imagens intermediárias serão salvos automaticamente na pasta `results/`.

---

## 📊 Resultados Obtidos

O sistema foi validado em um dataset de 22 imagens de teste (20 sintéticas com desvios e ruído, e 2 fotos fotográficas reais tiradas por celular), alcançando as seguintes métricas gerais:

* **Acurácia**: 100,00%
* **Precisão**: 100,00%
* **Sensibilidade (Recall)**: 100,00%
* **F1-Score**: 100,00%
