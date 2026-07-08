import cv2
import numpy as np

def process_image(img_path, min_cookie_area=45000, min_solidity=0.95, min_hole_area=15, max_hole_area=400, expected_holes=9):
    """
    Executa o pipeline de PDI para inspecionar a qualidade de um biscoito.
    
    Retorna:
        - label_pred: "perfeito" ou "defeito"
        - info: dicionário com imagens intermediárias e métricas calculadas
    """
    # 1. Carregar a imagem
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Não foi possível carregar a imagem em: {img_path}")
        
    # Mantém cópias em RGB para visualização
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_draw = img_rgb.copy()
    
    # 2. Conversão para Tons de Cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Suavização (Filtro Gaussiano)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 4. Segmentação do Biscoito (Otsu)
    # Como o fundo é cinza claro (240) e o biscoito é marrom claro (~190), 
    # usamos THRESH_BINARY_INV para o biscoito ficar branco (255) e o fundo preto (0).
    _, thresh_cookie = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Operação Morfológica na máscara do biscoito para limpar pequenos ruídos no fundo
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cookie_mask = cv2.morphologyEx(thresh_cookie, cv2.MORPH_OPEN, kernel_clean)
    cookie_mask = cv2.morphologyEx(cookie_mask, cv2.MORPH_CLOSE, kernel_clean)
    
    # Encontrar contorno externo do biscoito
    contours, _ = cv2.findContours(cookie_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    cookie_contour = None
    cookie_area = 0
    solidity = 0.0
    is_broken = False
    
    if len(contours) > 0:
        # Pega o maior contorno (deve ser o biscoito)
        cookie_contour = max(contours, key=cv2.contourArea)
        cookie_area = cv2.contourArea(cookie_contour)
        
        # Calcular Solidez (área do contorno / área do fecho convexo)
        # Biscoitos quebrados têm reentrâncias e solidez menor.
        hull = cv2.convexHull(cookie_contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = cookie_area / hull_area
            
        if cookie_area < min_cookie_area:
            is_broken = True
        if solidity < min_solidity:
            is_broken = True
    else:
        is_broken = True
        
    # 5. Segmentação dos Furos
    # Furos são bem mais escuros que a massa do biscoito (~50 vs ~190).
    # Vamos criar uma máscara de pixels escuros apenas onde o biscoito existe.
    dark_mask = np.zeros_like(gray)
    dark_mask[(gray < 120) & (cookie_mask == 255)] = 255
    
    # Operação morfológica nos furos:
    # Usamos Abertura (Opening) para eliminar linhas finas (rachaduras) ou ruídos minúsculos.
    kernel_holes = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned_holes = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel_holes)
    
    # Encontrar os contornos dos furos
    hole_contours, _ = cv2.findContours(cleaned_holes, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_holes = []
    num_holes_detected = 0
    
    for hc in hole_contours:
        h_area = cv2.contourArea(hc)
        # Filtrar por área para ignorar ruídos ou rachaduras muito grandes/pequenas
        if min_hole_area <= h_area <= max_hole_area:
            valid_holes.append(hc)
            num_holes_detected += 1
            # Desenha os furos detectados em verde no painel de visualização
            cv2.drawContours(img_draw, [hc], -1, (0, 255, 0), 2)
            
    # Desenhar o contorno do biscoito em azul
    if cookie_contour is not None:
        cv2.drawContours(img_draw, [cookie_contour], -1, (255, 0, 0), 3)
        
    # 6. Classificação final
    # Critérios de perfeição:
    # - Não está quebrado (área suficiente e solidez alta)
    # - Tem exatamente expected_holes detectados
    
    has_correct_holes = (num_holes_detected == expected_holes)
    
    if not is_broken and has_correct_holes:
        label_pred = "perfeito"
    else:
        label_pred = "defeito"
        
    # Detalhar motivos da falha para fins de diagnóstico
    reasons = []
    if cookie_area < min_cookie_area:
        reasons.append(f"Área pequena ({int(cookie_area)}px < {min_cookie_area}px)")
    if solidity < min_solidity:
        reasons.append(f"Solidez baixa ({solidity:.3f} < {min_solidity})")
    if not has_correct_holes:
        reasons.append(f"Furos incorretos (detectados {num_holes_detected} de {expected_holes})")
        
    info = {
        "img_original": img_rgb,
        "img_gray": gray,
        "img_blur": blur,
        "img_thresh_cookie": cookie_mask,
        "img_holes_mask": cleaned_holes,
        "img_draw": img_draw,
        "cookie_area": cookie_area,
        "solidity": solidity,
        "num_holes": num_holes_detected,
        "reasons": ", ".join(reasons) if reasons else "Nenhum"
    }
    
    return label_pred, info
