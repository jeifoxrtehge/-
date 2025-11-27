import pygame
import random
import math

pygame.init()

screen_width, screen_height = 1440, 810
screen = pygame.display.set_mode((screen_width, screen_height))
balls = []
bsize = 256

float_texts = []
font = pygame.font.Font(None, 48)
    
# 加载图片时添加错误处理
try:
    scaled_image = pygame.transform.scale(pygame.image.load('pic/whiteball.png'), (bsize, bsize))
except FileNotFoundError:
    # 如果图片不存在，创建一个白色圆形作为替代
    scaled_image = pygame.Surface((bsize, bsize), pygame.SRCALPHA)
    pygame.draw.circle(scaled_image, (255, 255, 255), (bsize//2, bsize//2), bsize//2)

try:
    gameback = pygame.transform.scale(pygame.image.load('pic/gameback.png'), (screen_width, screen_height))
except FileNotFoundError:
    # 如果背景图片不存在，使用灰色背景
    gameback = pygame.Surface((screen_width, screen_height))
    gameback.fill((128, 128, 128))

small_font = pygame.font.Font(None, 32) 
total_score = 0
max_progress = 100000000
ball_remain = 3
progress_bar = {
    'x': 40,
    'y': 40,
    'width': 1300,
    'height': 30,
    'border_color': (255, 255, 255),
    'bg_color': (50, 50, 50),
    'fill_color': (0, 255, 128)
}


cbsize = 64
colorball_images = [None]
for i in range(1, 10):
    cimage = pygame.transform.scale(pygame.image.load('pic/scoreball/%d.png' % i), (cbsize, cbsize))
    colorball_images.append( cimage )

gamearea = {
    'left': 70, 'top': 180,
    'right': 1088, 'bottom': 747
}
ghost_ball = None
scale_speed = 6
min_ghost_size = 30
max_ghost_size = 150
running = True
clock = pygame.time.Clock()

# 根据分数获取渐变颜色（分数越高越鲜艳）
def get_score_color(score):
    score = max(1, min(9, score))
    ratio = (score - 1) / 8 
    if ratio < 0.2: 
        r = int(100 + 100 * ratio * 5)
        g = int(150 + 50 * ratio * 5)
        b = 255
    elif ratio < 0.4:
        r = int(200 - 100 * (ratio - 0.2) * 5)
        g = 255
        b = int(255 - 150 * (ratio - 0.2) * 5)
    elif ratio < 0.6: 
        r = int(100 + 100 * (ratio - 0.4) * 5)
        g = 255
        b = int(100 - 100 * (ratio - 0.4) * 5)
    elif ratio < 0.8: 
        r = 255
        g = int(255 - 100 * (ratio - 0.6) * 5)
        b = int(50 + 50 * (ratio - 0.6) * 5)
    else:  
        r = 255
        g = int(150 - 100 * (ratio - 0.8) * 5)
        b = int(100 - 100 * (ratio - 0.8) * 5)
    return (r, g, b)


def draw_whiteball_count():
    global ball_remain
    ball_image = pygame.transform.scale(scaled_image, (bsize//2, bsize//2))
    icon_x = screen_width - 110 - ball_image.get_width()
    icon_y = progress_bar['y'] + 130
    screen.blit(ball_image, (icon_x, icon_y))
    count_text = f"x {ball_remain}"
    count_surface = font.render(count_text, True, (255, 255, 255))
    count_x = icon_x + ball_image.get_width() + 10
    count_y = icon_y + (ball_image.get_height() - count_surface.get_height()) // 2
    screen.blit(count_surface, (count_x, count_y))

def draw_progress():
    global total_score
    current_progress = min(total_score, max_progress)
    fill_width = (current_progress / max_progress) * progress_bar['width']
    
    pygame.draw.rect(screen, progress_bar['bg_color'], (
        progress_bar['x'], 
        progress_bar['y'], 
        progress_bar['width'], 
        progress_bar['height']
    ))
    
    pygame.draw.rect(screen, progress_bar['fill_color'], (
        progress_bar['x'], 
        progress_bar['y'], 
        fill_width, 
        progress_bar['height']
    ))
    
    pygame.draw.rect(screen, progress_bar['border_color'], (
        progress_bar['x'], 
        progress_bar['y'], 
        progress_bar['width'], 
        progress_bar['height']
    ), 3)

    
    score_text = f"{current_progress}/{max_progress}"
    score_surface = small_font.render(score_text, True, (255, 255, 255))
    score_rect = score_surface.get_rect(center=(
        progress_bar['x'] + progress_bar['width']//2, 
        progress_bar['y'] + progress_bar['height'] + 20 
    ))
    screen.blit(score_surface, score_rect)
    
    percent = (current_progress / max_progress) * 100
    percent_text = f"{percent:.1f}%"
    percent_surface = small_font.render(percent_text, True, (255, 255, 255))
    percent_rect = percent_surface.get_rect(
        topright=(progress_bar['x'] + progress_bar['width'] + 80, progress_bar['y'] + 5)
    )
    screen.blit(percent_surface, percent_rect)

# 碰撞检测和响应函数
def check_ball_collisions(balls):
    """检测所有球体之间的碰撞并处理"""
    global total_score  
    for i in range(len(balls)):
        ball1 = balls[i]
        # 球体1的属性：位置、半径、速度
        x1, y1 = ball1['rect'].center
        r1 = ball1['rect'].width // 2
        v1x, v1y = ball1['speed']
        
        for j in range(i + 1, len(balls)):
            ball2 = balls[j]
            # 球体2的属性
            x2, y2 = ball2['rect'].center
            r2 = ball2['rect'].width // 2
            v2x, v2y = ball2['speed']
            
            # 计算两球中心距离
            dx = x2 - x1
            dy = y2 - y1
            distance = math.hypot(dx, dy)
            min_distance = r1 + r2  # 最小距离（两球刚好接触）
            
            # 如果发生碰撞
            if distance < min_distance:
                # 1. 防止球体重叠：将球体分开到刚好接触的位置
                overlap = min_distance - distance
                # 计算分离方向的单位向量
                if distance == 0:
                    # 避免除以零，随机一个方向
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    distance = 1  # 避免除以零
                
                # 单位向量
                nx = dx / distance  # x方向法向量
                ny = dy / distance  # y方向法向量
                
                # 分离球体（根据半径比例分配重叠距离）
                ratio1 = r1 / min_distance
                ratio2 = r2 / min_distance
                
                # 移动球体
                ball1['rect'].centerx -= overlap * nx * ratio2
                ball1['rect'].centery -= overlap * ny * ratio2
                ball2['rect'].centerx += overlap * nx * ratio1
                ball2['rect'].centery += overlap * ny * ratio1
                
                # 2. 碰撞响应（动量守恒和动能守恒，弹性碰撞）
                # 相对速度
                v_relx = v2x - v1x
                v_rely = v2y - v1y
                
                # 相对速度在法向量上的投影
                v_rel_normal = v_relx * nx + v_rely * ny
                
                # 如果球体正在相互靠近（而不是分离）
                if v_rel_normal < 0:
                    # 弹性碰撞系数（1为完全弹性碰撞）
                    e = 0.8
                    
                    # 计算冲量大小
                    # 假设所有球体密度相同，质量与半径的立方成正比（体积）
                    m1 = r1 ** 3
                    m2 = r2 ** 3
                    
                    impulse = (2 * m1 * m2 * v_rel_normal) / (m1 + m2)
                    
                    # 应用冲量到速度
                    ball1['speed'][0] += (impulse / m1) * nx
                    ball1['speed'][1] += (impulse / m1) * ny
                    ball2['speed'][0] -= (impulse / m2) * nx
                    ball2['speed'][1] -= (impulse / m2) * ny

                    if ball1['type'] == 0 or ball2['type'] == 0:
                        score = ball1['type'] + ball2['type']
                        if score != 0:
                            total_score += score
                            text_x = (x1 + x2) // 2
                            text_y = (y1 + y2) // 2
                            text_color = get_score_color(score)
                            text_surface = font.render(f"+{score}", True, text_color)
                            shadow_surface = font.render(f"+{score}", True, (0, 0, 0))
                            float_texts.append({
                                'shadow': shadow_surface,
                                'text': text_surface,
                                'x': text_x,
                                'y': text_y,
                                'alpha': 255,
                                'life': 60
                            })

                    # 限制最大速度，防止球体速度过快
                    max_speed = 40
                    for ball in [ball1, ball2]:
                        speed_mag = math.hypot(ball['speed'][0], ball['speed'][1])
                        if speed_mag > max_speed:
                            scale = max_speed / speed_mag
                            ball['speed'][0] *= scale
                            ball['speed'][1] *= scale

for i in range(1, 10):
    img = colorball_images[i]
    balls.append({
        'image': img,
        'rect': img.get_rect(),
        'speed': [0, 0],
        'type' : i
    })

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_x, click_y = event.pos
            # 检查点击位置是否在游戏区域内
            if (gamearea['left'] <= click_x <= gamearea['right'] and
                gamearea['top'] <= click_y <= gamearea['bottom']):
                ghost_ball = {
                    'pos': (click_x, click_y),
                    'current_size': min_ghost_size,
                    'scale_dir': 1
                }
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and ghost_ball is not None:
            if ball_remain <= 0:
                continue
            ball_remain -= 1
            click_x, click_y = event.pos
            final_size = ghost_ball['current_size']
            final_ball_image = pygame.transform.scale(scaled_image, (int(final_size), int(final_size)))
            new_ball_rect = final_ball_image.get_rect(center=(click_x, click_y))
            
            # 确保新球完全在游戏区域内
            new_radius = final_size // 2
            if new_ball_rect.left < gamearea['left']:
                new_ball_rect.left = gamearea['left']
            if new_ball_rect.right > gamearea['right']:
                new_ball_rect.right = gamearea['right']
            if new_ball_rect.top < gamearea['top']:
                new_ball_rect.top = gamearea['top']
            if new_ball_rect.bottom > gamearea['bottom']:
                new_ball_rect.bottom = gamearea['bottom']
            
            new_ball_speed = [0, 0]
            while new_ball_speed[0] == 0 and new_ball_speed[1] == 0:
                new_ball_speed = [random.randint(-20, 20), random.randint(-20, 20)]
            
            balls.append({
                'image': final_ball_image,
                'rect': new_ball_rect,
                'speed': new_ball_speed,
                'type' : 0,
            })
            ghost_ball = None
    
    screen.fill((0, 0, 0))
    screen.blit(gameback, gameback.get_rect())

    if ghost_ball is not None:
        current_size = ghost_ball['current_size'] + ghost_ball['scale_dir'] * scale_speed
        if current_size >= max_ghost_size:
            current_size = max_ghost_size
            ghost_ball['scale_dir'] = -1
        elif current_size <= min_ghost_size:
            current_size = min_ghost_size
            ghost_ball['scale_dir'] = 1
        ghost_ball['current_size'] = current_size
        
        ghost_surface = pygame.transform.scale(scaled_image, (int(current_size), int(current_size)))
        ghost_surface.set_alpha(128)
        ghost_rect = ghost_surface.get_rect(center=ghost_ball['pos'])
        
        # 确保幽灵球在游戏区域内显示
        ghost_radius = current_size // 2
        if ghost_rect.left < gamearea['left']:
            ghost_rect.left = gamearea['left']
        if ghost_rect.right > gamearea['right']:
            ghost_rect.right = gamearea['right']
        if ghost_rect.top < gamearea['top']:
            ghost_rect.top = gamearea['top']
        if ghost_rect.bottom > gamearea['bottom']:
            ghost_rect.bottom = gamearea['bottom']
        
        screen.blit(ghost_surface, ghost_rect)

    # 更新所有球体位置
    for ball in balls:
        ball['rect'].x += ball['speed'][0]
        ball['rect'].y += ball['speed'][1]
        
        # 边界碰撞检测
        ball_radius = ball['rect'].width // 2
        
        # 左右边界
        if ball['rect'].left <= gamearea['left']:
            ball['rect'].left = gamearea['left']
            ball['speed'][0] = -ball['speed'][0] * 1  # 添加一点阻尼
        if ball['rect'].right >= gamearea['right']:
            ball['rect'].right = gamearea['right']
            ball['speed'][0] = -ball['speed'][0] * 1
        
        # 上下边界
        if ball['rect'].top <= gamearea['top']:
            ball['rect'].top = gamearea['top']
            ball['speed'][1] = -ball['speed'][1] * 1
        if ball['rect'].bottom >= gamearea['bottom']:
            ball['rect'].bottom = gamearea['bottom']
            ball['speed'][1] = -ball['speed'][1] * 1
    
    # 检测并处理球体之间的碰撞
    if len(balls) >= 2:
        check_ball_collisions(balls)
    
    # 绘制所有球体
    for ball in balls:
        screen.blit(ball['image'], ball['rect'])

    updated_float_texts = []
    for text_obj in float_texts:
        text_obj['y'] -= 2
        text_obj['alpha'] -= 4
        text_obj['life'] -= 1
        text_obj['text'].set_alpha(max(0, text_obj['alpha']))
        text_obj['shadow'].set_alpha(max(0, text_obj['alpha']))
        shadow_rect = text_obj['shadow'].get_rect(center=(text_obj['x']+2, text_obj['y']+2))
        text_rect = text_obj['text'].get_rect(center=(text_obj['x'], text_obj['y']))
        screen.blit(text_obj['shadow'], shadow_rect)
        screen.blit(text_obj['text'], text_rect)
        if text_obj['life'] > 0 and text_obj['alpha'] > 0:
            updated_float_texts.append(text_obj)
    float_texts = updated_float_texts

    draw_progress()
    draw_whiteball_count()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()