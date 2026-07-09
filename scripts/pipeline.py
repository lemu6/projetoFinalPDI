import cv2
import numpy as np

def process_image(img_path, min_cookie_area=45000, min_solidity=0.95, min_hole_area=15, max_hole_area=400, expected_holes=9, is_real=False):
    """
    Executa o pipeline de PDI para inspecionar a qualidade de um biscoito.
    Suporta modo sintético e modo real com correções de iluminação.
    """
    # 1. Carregar a imagem
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Não foi possível carregar a imagem em: {img_path}")
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_draw = img_rgb.copy()
    
    # 2. Conversão para Tons de Cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if is_real:
        # A. CORREÇÃO DE ILUMINAÇÃO (Sombras e Gradientes)
        # Estima a iluminação de fundo usando um desfoque Gaussiano largo (maior que o biscoito)
        kernel_size = 251
        background = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        # Corrige dividindo a imagem pelo fundo estimado para normalizar a luz
        corrected = np.clip(gray.astype(float) / background.astype(float) * 230, 0, 255).astype(np.uint8)
        blur = cv2.GaussianBlur(corrected, (5, 5), 0)
    else:
        corrected = gray
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
    # 3. Segmentação do Biscoito (Otsu Global na imagem corrigida)
    _, thresh_cookie = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Limpeza morfológica da bolacha
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
        # Pega o maior contorno (bolacha)
        cookie_contour = max(contours, key=cv2.contourArea)
        cookie_area = cv2.contourArea(cookie_contour)
        
        # Calcular Solidez (área / fecho convexo)
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
        
    # 4. Segmentação dos Furos
    num_holes_detected = 0
    cleaned_holes = np.zeros_like(gray)
    
    if cookie_contour is not None:
        # Criar máscara isolada apenas para a bolacha selecionada
        single_cookie_mask = np.zeros_like(cookie_mask)
        cv2.drawContours(single_cookie_mask, [cookie_contour], -1, 255, -1)
        
        if is_real:
            # B. OTSU LOCAL: Isola furos com base no histograma local da bolacha
            local_biscuit = np.ones_like(gray) * 255
            local_biscuit[single_cookie_mask == 255] = gray[single_cookie_mask == 255]
            _, thresh_holes = cv2.threshold(local_biscuit, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            thresh_holes = np.zeros_like(gray)
            thresh_holes[(gray < 120) & (single_cookie_mask == 255)] = 255
            
        # Abertura nos furos para apagar linhas de rachadura e pequenas texturas
        kernel_holes = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned_holes = cv2.morphologyEx(thresh_holes, cv2.MORPH_OPEN, kernel_holes)
        
        # Encontrar contornos dos furos
        hole_contours, _ = cv2.findContours(cleaned_holes, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for hc in hole_contours:
            h_area = cv2.contourArea(hc)
            perimeter = cv2.arcLength(hc, True)
            # C. FILTRO DE CIRCULARIDADE (Para rejeitar letras da marca estampada)
            circularity = (4 * np.pi * h_area) / (perimeter ** 2) if perimeter > 0 else 0
            
            # Filtro baseado no tipo
            if is_real:
                # Na imagem real, filtramos por área e exigimos circularidade >= 0.60
                is_valid = (min_hole_area <= h_area <= max_hole_area) and (circularity >= 0.60)
            else:
                is_valid = (min_hole_area <= h_area <= max_hole_area)
                
            if is_valid:
                num_holes_detected += 1
                cv2.drawContours(img_draw, [hc], -1, (0, 255, 0), 2)
                
        # Desenhar borda da bolacha
        cv2.drawContours(img_draw, [cookie_contour], -1, (255, 0, 0), 3)
        
    # 5. Classificação final
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
