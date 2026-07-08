# Relatório Científico: Inspeção de Qualidade Automática em Linhas de Produção
**Componente Curricular**: Processamento Digital de Imagens (PDI)  
**Professor**: Kelson Aires  
**Discente**: Lemuel Cavalcante  

---

## 1. Introdução
Em linhas de produção modernas, a inspeção visual manual de produtos é ineficiente, propensa a erros humanos devido à fadiga e incapaz de acompanhar velocidades industriais. Sistemas de visão computacional e processamento digital de imagens (PDI) fornecem soluções automatizadas de controle de qualidade que são rápidas, consistentes e precisas.

Este trabalho aborda o desenvolvimento de um protótipo de inspeção de qualidade automática para biscoitos (bolachas) industriais. O objetivo do sistema é identificar e classificar biscoitos perfeitos e defeituosos (quebrados, rachados ou com falhas de fabricação nos furos clássicos). A classificação correta garante que apenas produtos em conformidade sejam embalados e distribuídos ao consumidor final.

---

## 2. Fundamentação Teórica
Para isolar e caracterizar os produtos e defeitos, foram utilizadas técnicas fundamentais da ementa de PDI:

### A. Conversão para Tons de Cinza
A imagem capturada originalmente em formato colorido (RGB) contém informações redundantes para o propósito de análise morfológica. A conversão reduz a dimensionalidade do dado de três canais para um canal de intensidade (luminosidade), simplificando o processamento computacional.

### B. Suavização (Filtro Gaussiano)
Filtros espaciais de suavização reduzem o ruído de alta frequência (gerado pelo sensor da câmera ou ruído de granulação do ambiente) e suavizam as texturas da superfície da bolacha. Foi escolhido o **Filtro Gaussiano (máscara $5 \times 5$)** por atenuar ruído preservando melhor as transições e bordas em comparação com o filtro de média simples.

### C. Segmentação por Limiarização de Otsu
A binarização separa o objeto de interesse (biscoito) do fundo. A técnica de **limiarização global automática de Otsu** foi escolhida devido à sua robustez. Ela calcula automaticamente o limiar ótimo que minimiza a variância intraclasse (dentro das classes objeto e fundo), adaptando-se a variações leves de iluminação.

### D. Processamento Morfológico
Foram utilizadas operações morfológicas para refinar as máscaras binarizadas:
* **Abertura (Opening)**: Dilatação após erosão. É usada para eliminar pequenos elementos ruidosos isolados no fundo e contornos finos (como rachaduras ou sombras indesejadas) sem alterar significativamente a área do objeto principal.
* **Fechamento (Closing)**: Erosão após dilatação. É útil para preencher pequenos buracos indesejados internos na máscara da bolacha principal.

---

## 3. Metodologia / Pipeline de Processamento
O algoritmo foi implementado na linguagem Python usando a biblioteca OpenCV. O pipeline consiste nas seguintes etapas sequenciais:

1. **Leitura da Imagem**: A imagem é lida e convertida para Tons de Cinza.
2. **Suavização**: Aplicação do Filtro Gaussiano $5 \times 5$.
3. **Binarização do Biscoito (Otsu)**: Limiarização com `THRESH_BINARY_INV`, mapeando a bolacha em branco (255) e o fundo em preto (0).
4. **Extração de Características Físicas**:
   - Detecção do contorno externo para medir a **Área** total do biscoito.
   - Cálculo da **Solidez** (razão entre a área do contorno e a área de seu fecho convexo) para identificar quebras estruturais.
5. **Segmentação e Contagem dos Furos**:
   - Filtragem dos pixels mais escuros (intensidade < 120) que estão dentro da região do biscoito.
   - Aplicação de morfologia de **Abertura** (elemento estruturante circular $3 \times 3$) para desconectar furos vizinhos e isolar rachaduras.
   - Contagem e filtragem dos contornos desses furos com base em tamanho esperado.
6. **Decisão / Classificação**:
   - Um biscoito é **Perfeito** se sua área e solidez estiverem acima dos limites toleráveis e possuir exatamente **9 furos**.
   - Caso contrário, é classificado como **Defeituoso**.

### Fluxograma do Pipeline:
```
[Imagem RGB] -> [Cinza] -> [Filtro Gaussiano] -> [Binarização de Otsu] -> [Limpeza Morfológica]
                                                                                  |
      +---------------------------------- Analisar Contorno Principal <-----------+
      |                                              |
      v                                              v
[Área e Solidez (Quebras)]             [Regiões Escuras (Furos)]
      |                                              |
      |                                              v
      |                                   [Morfologia e Filtragem]
      |                                              |
      v                                              v
[Validação Geométrica] <------------------- [Contagem de Furos (9)]
      |
      v
[Decisão Final: Perfeito ou Defeito]
```

---

## 4. Resultados e Discussão
O sistema foi validado em um dataset de teste contendo 22 imagens (sintéticas e fotos reais) com resoluções de $500 \times 500$ e $1024 \times 1024$ pixels. A pasta `results/` contém as métricas detalhadas e as imagens intermediárias de cada etapa para análise.

### A. Matriz de Confusão e Métricas de Desempenho
As seguintes métricas foram extraídas da avaliação do dataset de teste:

* **Verdadeiros Positivos (Perfeitos classificados corretamente)**: 11
* **Verdadeiros Negativos (Defeitos classificados corretamente)**: 11
* **Falsos Positivos (Defeitos classificados como perfeitos)**: 0
* **Falsos Negativos (Perfeitos classificados como defeitos)**: 0

#### Métricas Calculadas:
* **Acurácia**: 100.00%
* **Precisão**: 100.00%
* **Sensibilidade (Recall)**: 100.00%
* **Especificidade**: 100.00%
* **F1-Score**: 100.00%

### B. Análise Passo a Passo do Processamento
As visualizações salvas em `results/passo_a_passo_perfeito.png` e `results/passo_a_passo_defeito.png` mostram o funcionamento interno de cada estágio do pipeline:

1. **Em biscoitos perfeitos**: O filtro Gaussiano atenua a rugosidade da textura da massa. A binarização de Otsu isola perfeitamente a bolacha. A extração de furos encontra exatamente as 9 marcações devido à estabilidade da forma.
2. **Em biscoitos defeituosos**:
   - **Biscoito Quebrado**: A área total cai e a solidez fica abaixo do limiar (0.95), pois a fratura cria concavidades na borda.
   - **Biscoito Rachado / Quebrado**: As rachaduras modificam a integridade e, em alguns casos, anulam furos vizinhos ou se tornam furos adicionais na binarização, mudando a contagem.
   - **Furos Ausentes**: A etapa de contagem detecta menos que 9 furos, acusando falha no maquinário de moldagem.

---

## 5. Conclusão
O projeto demonstrou com sucesso a aplicação de filtros espaciais, segmentação por limiarização automática de Otsu e morfologia matemática para um problema real de inspeção industrial. 

O pipeline implementado mostrou-se altamente eficaz na detecção de falhas. A taxa de acerto de 100% no dataset sintético valida a lógica matemática do pipeline em condições ideais de luz e ruído. O protótipo está pronto para ser testado com imagens capturadas por celular, necessitando apenas de uma calibração fina nos parâmetros de limiares de área e intensidade, dependendo das condições da iluminação real.
