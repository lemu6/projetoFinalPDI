import os
import cv2
import numpy as np
import random

def create_dirs():
    os.makedirs("dataset/perfeito", exist_ok=True)
    os.makedirs("dataset/defeito", exist_ok=True)

def add_noise_and_gradient(img):
    """
    Adiciona um gradiente suave de iluminação e ruído gaussiano leve
    para simular fotos tiradas com celular em condições reais.
    """
    h, w, c = img.shape
    
    # 1. Gradiente de iluminação (vinheta / variação de luz)
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    X, Y = np.meshgrid(x, y)
    # Gradiente linear inclinado para simular uma fonte de luz lateral
    angle = random.uniform(0, 2 * np.pi)
    gradient = (X * np.cos(angle) + Y * np.sin(angle)) * 25.0
    gradient = np.stack([gradient]*3, axis=-1)
    
    # 2. Ruído Gaussiano
    noise = np.random.normal(0, 3, img.shape)
    
    # Aplicar e clipar
    noisy_img = img.astype(np.float32) + gradient + noise
    noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
    return noisy_img

def draw_cookie_base(w, h, size=250, shape="square", rotation=0, shift=(0, 0), broken=False):
    """
    Desenha a base do biscoito (forma, cor e rachaduras/quebras se broken=True).
    """
    # Imagem base branca (fundo)
    img = np.ones((h, w, 3), dtype=np.uint8) * 240 # cinza claro
    
    # Criar máscara para o biscoito
    cookie_mask = np.zeros((h, w), dtype=np.uint8)
    cx, cy = w // 2 + shift[0], h // 2 + shift[1]
    
    # Definir vértices do biscoito retangular
    half_s = size // 2
    pts = np.array([
        [cx - half_s, cy - half_s],
        [cx + half_s, cy - half_s],
        [cx + half_s, cy + half_s],
        [cx - half_s, cy + half_s]
    ], dtype=np.int32)
    
    # Se estiver quebrado, cortamos um pedaço da borda/canto
    if broken:
        # Escolhe um canto para quebrar
        corner = random.choice([0, 1, 2, 3])
        # Ponto de corte do canto
        cut_w = random.randint(40, 75)
        cut_h = random.randint(40, 75)
        if corner == 0: # Canto superior esquerdo
            pts[0] = [cx - half_s + cut_w, cy - half_s + cut_h]
        elif corner == 1: # Canto superior direito
            pts[1] = [cx + half_s - cut_w, cy - half_s + cut_h]
        elif corner == 2: # Canto inferior direito
            pts[2] = [cx + half_s - cut_w, cy + half_s - cut_h]
        elif corner == 3: # Canto inferior esquerdo
            pts[3] = [cx - half_s + cut_w, cy + half_s - cut_h]
            
    # Desenhar o polígono preenchido na máscara
    cv2.fillPoly(cookie_mask, [pts], 255)
    
    # Rotacionar a máscara se houver rotação
    if rotation != 0:
        M = cv2.getRotationMatrix2D((cx, cy), rotation, 1.0)
        cookie_mask = cv2.warpAffine(cookie_mask, M, (w, h))
        
    # Aplicar a cor do biscoito (marrom claro / bege)
    # RGB(222, 184, 135) - Burlywood
    cookie_color = [135, 184, 222] # OpenCV usa BGR
    img[cookie_mask == 255] = cookie_color
    
    return img, cookie_mask, (cx, cy)

def draw_holes(img, mask, cx, cy, rotation, shift, num_holes=9, hole_radius=6):
    """
    Desenha os furos clássicos do biscoito.
    """
    # Gerar coordenadas dos furos em um grid 3x3 relativo ao centro do biscoito
    # Para 9 furos ideais
    grid_offsets = [
        (-50, -50), (0, -50), (50, -50),
        (-50, 0),   (0, 0),   (50, 0),
        (-50, 50),  (0, 50),  (50, 50)
    ]
    
    # Se num_holes < 9, escolhemos uma subamostra aleatória para simular falha na fabricação
    if num_holes < 9:
        selected_offsets = random.sample(grid_offsets, num_holes)
    else:
        selected_offsets = grid_offsets
        
    # Cor do furo (marrom escuro / sombra)
    # BGR para marrom escuro: (45, 60, 90)
    hole_color = [35, 50, 80]
    
    # Desenhar os furos considerando a rotação e o shift
    h, w, _ = img.shape
    M = cv2.getRotationMatrix2D((cx, cy), rotation, 1.0)
    
    for ox, oy in selected_offsets:
        # Calcular posição absoluta original
        hx = cx + ox
        hy = cy + oy
        
        # Aplicar a mesma rotação ao ponto do furo
        point = np.array([hx, hy, 1.0])
        transformed_point = M.dot(point)
        thx, thy = int(transformed_point[0]), int(transformed_point[1])
        
        # Desenhar o furo (apenas se cair dentro da máscara do biscoito)
        if 0 <= thx < w and 0 <= thy < h:
            if mask[thy, thx] == 255:
                # Furo principal mais escuro
                cv2.circle(img, (thx, thy), hole_radius, hole_color, -1)
                # Adicionar uma leve borda sombreada para tridimensionalidade
                cv2.circle(img, (thx, thy), hole_radius + 2, [55, 75, 110], 1)

def draw_crack(img, mask, cx, cy):
    """
    Desenha uma rachadura escura no biscoito para simular um defeito estrutural.
    """
    h, w, _ = img.shape
    # Selecionar pontos inicial e final da rachadura
    start_pt = (cx - random.randint(40, 80), cy - random.randint(-40, 40))
    end_pt = (cx + random.randint(40, 80), cy - random.randint(-40, 40))
    
    # Gerar pontos intermediários para fazer um zigue-zague
    num_segments = 5
    pts = []
    for i in range(num_segments + 1):
        t = i / num_segments
        px = int(start_pt[0] + t * (end_pt[0] - start_pt[0]))
        py = int(start_pt[1] + t * (end_pt[1] - start_pt[1]))
        if i > 0 and i < num_segments:
            px += random.randint(-5, 5)
            py += random.randint(-15, 15)
        pts.append((px, py))
        
    # Desenhar a rachadura (apenas onde existe o biscoito)
    crack_color = [25, 35, 55] # cor escura da rachadura
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i+1]
        # Criar uma linha temporária e aplicar com a máscara
        temp_img = img.copy()
        cv2.line(temp_img, p1, p2, crack_color, thickness=random.randint(2, 4))
        # Mesclar apenas na região do biscoito
        img[mask == 255] = temp_img[mask == 255]

def generate_dataset(num_perfeitos=10, num_defeitos=10):
    create_dirs()
    print("Gerando dataset sintético...")
    
    # 1. Gerar Biscoitos Perfeitos
    for i in range(num_perfeitos):
        rotation = random.uniform(-15, 15) # rotações leves
        shift = (random.randint(-15, 15), random.randint(-15, 15)) # pequenos deslocamentos
        size = random.randint(230, 260) # pequenas variações de tamanho
        
        img, mask, (cx, cy) = draw_cookie_base(500, 500, size=size, rotation=rotation, shift=shift, broken=False)
        draw_holes(img, mask, cx, cy, rotation, shift, num_holes=9)
        img = add_noise_and_gradient(img)
        
        filepath = f"dataset/perfeito/cookie_perfeito_{i:02d}.jpg"
        cv2.imwrite(filepath, img)
        
    # 2. Gerar Biscoitos com Defeito
    # Vamos criar 3 categorias de defeito: quebrado, rachado, e com furos faltando
    for i in range(num_defeitos):
        rotation = random.uniform(-25, 25)
        shift = (random.randint(-20, 20), random.randint(-20, 20))
        size = random.randint(230, 260)
        
        # Escolher tipo de defeito aleatório
        defect_type = random.choice(["broken", "missing_holes", "crack", "combined"])
        
        broken = (defect_type in ["broken", "combined"])
        num_holes = 9
        if defect_type in ["missing_holes", "combined"]:
            num_holes = random.randint(3, 7) # Faltando furos
            
        img, mask, (cx, cy) = draw_cookie_base(500, 500, size=size, rotation=rotation, shift=shift, broken=broken)
        draw_holes(img, mask, cx, cy, rotation, shift, num_holes=num_holes)
        
        if defect_type == "crack" or (defect_type == "combined" and random.random() > 0.5):
            draw_crack(img, mask, cx, cy)
            
        img = add_noise_and_gradient(img)
        
        filepath = f"dataset/defeito/cookie_defeito_{i:02d}.jpg"
        cv2.imwrite(filepath, img)
        
    print(f"Dataset gerado! {num_perfeitos} imagens em perfeito/ e {num_defeitos} imagens em defeito/.")

if __name__ == "__main__":
    generate_dataset()
