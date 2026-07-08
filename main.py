import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scripts.pipeline import process_image

def create_results_dir():
    os.makedirs("results", exist_ok=True)

def calculate_metrics(y_true, y_pred):
    """
    Calcula manualmente as métricas de classificação para a Matriz de Confusão.
    Consideramos 'perfeito' como a classe POSITIVA (1) e 'defeito' como NEGATIVA (0).
    """
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "perfeito" and p == "perfeito")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == "defeito" and p == "defeito")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == "defeito" and p == "perfeito")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "perfeito" and p == "defeito")
    
    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0 # Sensibilidade
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0 # Especificidade
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "Acurácia": accuracy,
        "Precisão": precision,
        "Sensibilidade (Recall)": recall,
        "Especificidade": specificity,
        "F1-Score": f1
    }

def save_step_visualization(img_path, info, output_name):
    """
    Salva uma figura com as etapas do processamento digital de imagens para o relatório.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    axes[0, 0].imshow(info["img_original"])
    axes[0, 0].set_title("1. Imagem Original (RGB)")
    axes[0, 0].axis("off")
    
    axes[0, 1].imshow(info["img_gray"], cmap="gray")
    axes[0, 1].set_title("2. Tons de Cinza")
    axes[0, 1].axis("off")
    
    axes[0, 2].imshow(info["img_blur"], cmap="gray")
    axes[0, 2].set_title("3. Suavização (Filtro Gaussiano)")
    axes[0, 2].axis("off")
    
    axes[1, 0].imshow(info["img_thresh_cookie"], cmap="gray")
    axes[1, 0].set_title("4. Segmentação Biscoito (Otsu)")
    axes[1, 0].axis("off")
    
    axes[1, 1].imshow(info["img_holes_mask"], cmap="gray")
    axes[1, 1].set_title("5. Segmentação dos Furos (Morfologia)")
    axes[1, 1].axis("off")
    
    axes[1, 2].imshow(info["img_draw"])
    axes[1, 2].set_title(f"6. Resultado (Furos: {info['num_holes']})")
    axes[1, 2].axis("off")
    
    plt.tight_layout()
    plt.savefig(f"results/{output_name}", dpi=150)
    plt.close()

def run_evaluation():
    create_results_dir()
    
    categories = ["perfeito", "defeito"]
    y_true = []
    y_pred = []
    
    detailed_results = []
    
    # Dicionários para guardar um exemplo de cada classe para visualizar
    saved_visualizations = {"perfeito": False, "defeito": False}
    
    print("="*60)
    print("INICIANDO AVALIAÇÃO DO SISTEMA DE INSPEÇÃO DE QUALIDADE")
    print("="*60)
    
    for category in categories:
        dir_path = f"dataset/{category}"
        if not os.path.exists(dir_path):
            print(f"Aviso: Diretório {dir_path} não encontrado!")
            continue
            
        files = [f for f in os.listdir(dir_path) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        print(f"Processando {len(files)} imagens na pasta '{category}'...")
        
        for file in sorted(files):
            file_path = os.path.join(dir_path, file)
            
            # Configurar parâmetros com base no tipo de imagem (sintética ou real)
            is_real = "real" in file.lower()
            if is_real:
                # Parâmetros calibrados para fotos reais de 1024x1024 com 25 furos
                params = {
                    "min_cookie_area": 250000,
                    "min_solidity": 0.90,
                    "min_hole_area": 80,
                    "max_hole_area": 400,
                    "expected_holes": 25
                }
            else:
                # Parâmetros padrão para imagens sintéticas de 500x500 com 9 furos
                params = {
                    "min_cookie_area": 45000,
                    "min_solidity": 0.95,
                    "min_hole_area": 15,
                    "max_hole_area": 400,
                    "expected_holes": 9
                }

            # Executar pipeline
            try:
                pred, info = process_image(file_path, **params)
            except Exception as e:
                print(f"Erro ao processar {file}: {e}")
                continue
                
            y_true.append(category)
            y_pred.append(pred)
            
            is_correct = (category == pred)
            status_symbol = "✔️" if is_correct else "❌"
            
            detailed_results.append({
                "filename": file,
                "true": category,
                "pred": pred,
                "correct": is_correct,
                "area": info["cookie_area"],
                "solidity": info["solidity"],
                "holes": info["num_holes"],
                "reasons": info["reasons"]
            })
            
            # Salvar visualização do primeiro exemplo de cada categoria
            if not saved_visualizations[category]:
                save_step_visualization(file_path, info, f"passo_a_passo_{category}.png")
                saved_visualizations[category] = True
                print(f"  [Visualização salva] results/passo_a_passo_{category}.png")
                
    # 3. Calcular e imprimir métricas
    metrics = calculate_metrics(y_true, y_pred)
    
    print("\n" + "="*50)
    print("RESULTADOS GERAIS")
    print("="*50)
    for k, v in metrics.items():
        if isinstance(v, int):
            print(f"{k:25}: {v}")
        else:
            print(f"{k:25}: {v*100:.2f}%")
            
    # 4. Imprimir tabela resumida de classificação
    print("\n" + "="*80)
    print(f"{'Arquivo':<25} | {'Real':<10} | {'Predição':<10} | {'Status':<6} | {'Furos':<6} | {'Área':<8} | {'Motivo Falha'}")
    print("-"*80)
    for res in detailed_results:
        status_str = "CORRETO" if res["correct"] else "ERRO"
        print(f"{res['filename']:<25} | {res['true']:<10} | {res['pred']:<10} | {status_str:<6} | {res['holes']:<6} | {int(res['area']):<8} | {res['reasons']}")
    print("="*80)
    
    # 5. Salvar relatório de métricas em arquivo de texto
    with open("results/metricas_inspecao.txt", "w") as f:
        f.write("=== MÉTRICAS DE AVALIAÇÃO DO PROJETO DE PDI ===\n\n")
        f.write(f"Total de Imagens analisadas: {len(y_true)}\n")
        f.write(f"Verdadeiros Positivos (TP) : {metrics['TP']}\n")
        f.write(f"Verdadeiros Negativos (TN) : {metrics['TN']}\n")
        f.write(f"Falsos Positivos (FP)      : {metrics['FP']}\n")
        f.write(f"Falsos Negativos (FN)      : {metrics['FN']}\n\n")
        f.write(f"Acurácia       : {metrics['Acurácia']*100:.2f}%\n")
        f.write(f"Precisão       : {metrics['Precisão']*100:.2f}%\n")
        f.write(f"Sensibilidade  : {metrics['Sensibilidade (Recall)']*100:.2f}%\n")
        f.write(f"Especificidade : {metrics['Especificidade']*100:.2f}%\n")
        f.write(f"F1-Score       : {metrics['F1-Score']*100:.2f}%\n")
        
    print("\nResultados e gráficos exportados com sucesso na pasta 'results/'!")

if __name__ == "__main__":
    run_evaluation()
