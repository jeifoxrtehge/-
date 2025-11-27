import pygame
import random
import math

pygame.init()

screen_width, screen_height = 1440, 810
screen = pygame.display.set_mode((screen_width, screen_height))
balls = []
bsize = 256
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

# 碰撞检测和响应函数
def check_ball_collisions(balls):
    """检测所有球体之间的碰撞并处理"""
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
                    
                    # 限制最大速度，防止球体速度过快
                    max_speed = 40
                    for ball in [ball1, ball2]:
                        speed_mag = math.hypot(ball['speed'][0], ball['speed'][1])
                        if speed_mag > max_speed:
                            scale = max_speed / speed_mag
                            ball['speed'][0] *= scale
                            ball['speed'][1] *= scale

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
                'speed': new_ball_speed
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
            ball['speed'][0] = -ball['speed'][0] * 0.8  # 添加一点阻尼
        if ball['rect'].right >= gamearea['right']:
            ball['rect'].right = gamearea['right']
            ball['speed'][0] = -ball['speed'][0] * 0.8
        
        # 上下边界
        if ball['rect'].top <= gamearea['top']:
            ball['rect'].top = gamearea['top']
            ball['speed'][1] = -ball['speed'][1] * 0.8
        if ball['rect'].bottom >= gamearea['bottom']:
            ball['rect'].bottom = gamearea['bottom']
            ball['speed'][1] = -ball['speed'][1] * 0.8
    
    # 检测并处理球体之间的碰撞
    if len(balls) >= 2:
        check_ball_collisions(balls)
    
    # 绘制所有球体
    for ball in balls:
        screen.blit(ball['image'], ball['rect'])
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()