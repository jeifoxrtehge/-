import pygame
import random
import math
import cv2  # 用于视频解码
import numpy as np  # 用于图像格式转换

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

# 加载KK按钮图片
kk_button_image = None
kk_button_size = (128, 128)  # 按钮大小
try:
    kk_button_image = pygame.transform.scale(pygame.image.load('pic/kkball.png'), kk_button_size)
except FileNotFoundError:
    # 替代图片：蓝色圆形按钮
    kk_button_image = pygame.Surface(kk_button_size, pygame.SRCALPHA)
    pygame.draw.circle(kk_button_image, (0, 128, 255), (kk_button_size[0]//2, kk_button_size[1]//2), kk_button_size[0]//2)
    # 添加文字标识
    kk_text = font.render("KK", True, (255, 255, 255))
    kk_text_rect = kk_text.get_rect(center=kk_button_image.get_rect().center)
    kk_button_image.blit(kk_text, kk_text_rect)

# 视频播放相关变量
video_capture = None
video_surface = None
video_playing = False
video_timer = 0
max_video_time = 10 * 60  # 10秒（60帧/秒）
video_rect = None  # 视频显示区域

small_font = pygame.font.Font(None, 32) 
total_score = 0
current_level = 1
ball_remain = 3
progress_bar = {
    'x': 40,
    'y': 40,
    'width': 1300,
    'height': 30,
    'border_color': (255, 255, 255),
    'bg_color': (50, 50, 50),  # 进度条背景色（未填充部分）
    'gradient_start': (255, 0, 0),  # 渐变起始色（红色）
    'gradient_end': (128, 0, 255)   # 渐变结束色（紫色）
}

# 关卡配置：每关的目标分值、初始白球数、彩球数量
level_configs = [
    # 关卡1-10：{目标分值, 初始白球数, 彩球数量, 彩球最大等级}
    {'target_score': 10, 'init_white_balls': 1, 'color_ball_count': 1},
    {'target_score': 100, 'init_white_balls': 2, 'color_ball_count': 2},
    {'target_score': 1000, 'init_white_balls': 3, 'color_ball_count': 3},
    {'target_score': 5000, 'init_white_balls': 4, 'color_ball_count': 4},
    {'target_score': 10000, 'init_white_balls': 4, 'color_ball_count': 5},
    {'target_score': 100000, 'init_white_balls': 4, 'color_ball_count': 6},
    {'target_score': 1000000, 'init_white_balls': 5, 'color_ball_count': 7},
    {'target_score': 10000000, 'init_white_balls': 5, 'color_ball_count': 8},
    {'target_score': 100000000, 'init_white_balls': 5, 'color_ball_count': 9},
    {'target_score': 1000000000, 'init_white_balls': 5, 'color_ball_count': 10}
]

# 道具解锁配置
unlock_config = {
    'speedup': 3,    # 第3关解锁加速道具
    'levelup': 4     # 第4关解锁升级道具
}

# 锁定图标（红色叉号）
lock_surface = pygame.Surface((bsize//4, bsize//4), pygame.SRCALPHA)
pygame.draw.line(lock_surface, (255, 0, 0), (10, 10), (lock_surface.get_width()-10, lock_surface.get_height()-10), 5)
pygame.draw.line(lock_surface, (255, 0, 0), (lock_surface.get_width()-10, 10), (10, lock_surface.get_height()-10), 5)

speedup_image = None
try:
    speedup_image = pygame.transform.scale(pygame.image.load('pic/speedupball.png'),  (bsize//2, bsize//2))
except FileNotFoundError:
    # 替代图片：紫色圆形
    speedup_image = pygame.Surface((bsize//2, bsize//2), pygame.SRCALPHA)
    pygame.draw.circle(speedup_image, (128, 0, 255), (bsize//4, bsize//4), bsize//4)
speedup_remain = 3
speedup_active = False
speedup_timer = 0
speed_multiplier = 2

levelup_image = None
try:
    levelup_image = pygame.transform.scale(pygame.image.load('pic/levelupball.png'),  (bsize//2, bsize//2))
except FileNotFoundError:
    # 替代图片：金色圆形
    levelup_image = pygame.Surface((bsize//2, bsize//2), pygame.SRCALPHA)
    pygame.draw.circle(levelup_image, (255, 215, 0), (bsize//4, bsize//4), bsize//4)
levelup_remain = 3

# 加载彩球图片时添加错误处理
cbsize = 64
colorball_images = [None]
# 先定义get_score_color函数的占位，避免加载图片时出错
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

for i in range(1, 10):
    try:
        cimage = pygame.transform.scale(pygame.image.load('pic/scoreball/%d.png' % i), (cbsize, cbsize))
    except FileNotFoundError:
        # 替代图片：根据等级生成渐变颜色的圆形
        cimage = pygame.Surface((cbsize, cbsize), pygame.SRCALPHA)
        color = get_score_color(i)
        pygame.draw.circle(cimage, color, (cbsize//2, cbsize//2), cbsize//2)
    colorball_images.append(cimage)

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

# KK按钮位置（右下角）
kk_button_rect = kk_button_image.get_rect()
kk_button_rect.bottomright = (screen_width - 110, screen_height - 90)  # 距离右下角20像素

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

def draw_speedup_count():
    global speedup_remain, current_level
    speedup_icon = speedup_image
    icon_x = screen_width - 110 - speedup_icon.get_width()
    icon_y = progress_bar['y'] + 270
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 检查是否解锁
    is_unlocked = current_level >= unlock_config['speedup']
    
    # 如果未解锁，绘制半透明图标和锁定标记
    if not is_unlocked:
        # 半透明图标
        locked_icon = speedup_icon.copy()
        locked_icon.set_alpha(100)
        screen.blit(locked_icon, (icon_x, icon_y))
        
        # 锁定标记
        lock_x = icon_x + (speedup_icon.get_width() - lock_surface.get_width()) // 2
        lock_y = icon_y + (speedup_icon.get_height() - lock_surface.get_height()) // 2
        screen.blit(lock_surface, (lock_x, lock_y))
        
    else:
        # 已解锁，正常绘制
        if (icon_x <= mouse_x <= icon_x + speedup_icon.get_width() and
            icon_y <= mouse_y <= icon_y + speedup_icon.get_height()):
            pygame.draw.rect(screen, (67, 12, 255, 30), (icon_x - 5, icon_y - 5, speedup_icon.get_width() + 10, speedup_icon.get_height() + 10), border_radius=10)
        screen.blit(speedup_icon, (icon_x, icon_y))
        count_text = f"x {speedup_remain}"
        count_surface = font.render(count_text, True, (255, 255, 255))
        count_x = icon_x + speedup_icon.get_width() + 10
        count_y = icon_y + (speedup_icon.get_height() - count_surface.get_height()) // 2
        screen.blit(count_surface, (count_x, count_y))

def draw_levelup_count():
    global levelup_remain, current_level
    levelup_icon = levelup_image
    icon_x = screen_width - 110 - levelup_icon.get_width()
    icon_y = progress_bar['y'] + 410
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 检查是否解锁
    is_unlocked = current_level >= unlock_config['levelup']
    
    # 如果未解锁，绘制半透明图标和锁定标记
    if not is_unlocked:
        # 半透明图标
        locked_icon = levelup_icon.copy()
        locked_icon.set_alpha(100)
        screen.blit(locked_icon, (icon_x, icon_y))
        
        # 锁定标记
        lock_x = icon_x + (levelup_icon.get_width() - lock_surface.get_width()) // 2
        lock_y = icon_y + (levelup_icon.get_height() - lock_surface.get_height()) // 2
        screen.blit(lock_surface, (lock_x, lock_y))
    
    else:
        # 已解锁，正常绘制
        if (icon_x <= mouse_x <= icon_x + levelup_icon.get_width() and
            icon_y <= mouse_y <= icon_y + levelup_icon.get_height()):
            pygame.draw.rect(screen, (67, 12, 255, 30), (icon_x - 5, icon_y - 5, levelup_icon.get_width() + 10, levelup_icon.get_height() + 10), border_radius=10)
        screen.blit(levelup_icon, (icon_x, icon_y))
        count_text = f"x {levelup_remain}"
        count_surface = font.render(count_text, True, (255, 255, 255))
        count_x = icon_x + levelup_icon.get_width() + 10
        count_y = icon_y + (levelup_icon.get_height() - count_surface.get_height()) // 2
        screen.blit(count_surface, (count_x, count_y))

def draw_gradient_rect(surface, rect, start_color, end_color):
    """绘制线性渐变矩形（水平方向）"""
    # 创建一个临时表面，用于绘制渐变
    temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    
    # 水平渐变：从左到右，从start_color过渡到end_color
    for x in range(rect.width):
        # 计算当前x位置的颜色比例（0.0~1.0）
        ratio = x / rect.width
        
        # 计算当前颜色
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        
        # 绘制垂直线（整个高度）
        pygame.draw.line(temp_surface, (r, g, b), (x, 0), (x, rect.height))
    
    # 将渐变表面绘制到目标位置，并应用圆角裁剪
    # 创建圆角掩码
    mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255), (0, 0, rect.width, rect.height), border_radius=15)
    
    # 应用掩码
    temp_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    # 绘制到目标表面
    surface.blit(temp_surface, (rect.x, rect.y))

def draw_progress():
    global total_score, current_level
    # 获取当前关卡配置
    current_config = level_configs[current_level - 1]
    max_progress = current_config['target_score']
    current_progress = min(total_score, max_progress)
    fill_width = (current_progress / max_progress) * progress_bar['width']
    
    # 进度条整体矩形
    bar_rect = pygame.Rect(
        progress_bar['x'],
        progress_bar['y'],
        progress_bar['width'],
        progress_bar['height']
    )
    
    # 1. 绘制进度条背景（深色，带圆角）
    pygame.draw.rect(screen, progress_bar['bg_color'], bar_rect, border_radius=15)
    
    # 2. 绘制完整的红到紫渐变层（整个进度条宽度）
    gradient_rect = bar_rect.copy()
    draw_gradient_rect(screen, gradient_rect, progress_bar['gradient_start'], progress_bar['gradient_end'])
    
    # 3. 绘制遮罩层（覆盖未完成的进度部分，保持背景色）
    if fill_width < progress_bar['width']:
        mask_rect = pygame.Rect(
            progress_bar['x'] + fill_width,  # 从已完成进度的末端开始
            progress_bar['y'],
            progress_bar['width'] - fill_width,  # 未完成的宽度
            progress_bar['height']
        )
        # 遮罩层使用背景色，带圆角（只显示右侧未完成部分）
        pygame.draw.rect(screen, progress_bar['bg_color'], mask_rect, border_radius=15)
        
        # 修复圆角衔接：左侧遮罩边缘不需要圆角
        if fill_width > 0:
            # 绘制一个无圆角的矩形覆盖遮罩的左侧边缘，确保与已完成部分平滑衔接
            pygame.draw.rect(screen, progress_bar['bg_color'], (
                progress_bar['x'] + fill_width - 2,  # 稍微向左延伸，避免缝隙
                progress_bar['y'],
                progress_bar['width'] - fill_width + 2,
                progress_bar['height']
            ))
    
    # 4. 绘制进度条边框（白色细边框，带圆角）
    pygame.draw.rect(screen, progress_bar['border_color'], bar_rect, 3, border_radius=15)

    # 5. 绘制文本（分数、百分比、关卡）
    # 分数文本（白色，带黑色阴影）
    score_text = f"{current_progress}/{max_progress}"
    score_surface = small_font.render(score_text, True, (255, 255, 255))
    score_shadow = small_font.render(score_text, True, (0, 0, 0))
    score_rect = score_surface.get_rect(center=(
        progress_bar['x'] + progress_bar['width']//2, 
        progress_bar['y'] + progress_bar['height'] + 20 
    ))
    screen.blit(score_shadow, (score_rect.x + 1, score_rect.y + 1))
    screen.blit(score_surface, score_rect)
    
    # 百分比文本（紫色，带黑色阴影）
    percent = (current_progress / max_progress) * 100
    percent_text = f"{percent:.1f}%"
    percent_surface = small_font.render(percent_text, True, (255, 255, 255))
    percent_shadow = small_font.render(percent_text, True, (0, 0, 0))
    percent_rect = percent_surface.get_rect(
        topright=(progress_bar['x'] + progress_bar['width'] + 80, progress_bar['y'] + 5)
    )
    screen.blit(percent_shadow, (percent_rect.x + 2, percent_rect.y + 2))
    screen.blit(percent_surface, percent_rect)
    
    # 关卡文本（金色，带黑色阴影）
    level_text = f"Level: {current_level}"
    level_surface = small_font.render(level_text, True, (255, 215, 0))
    level_shadow = small_font.render(level_text, True, (0, 0, 0))
    level_rect = level_surface.get_rect(
        topleft=(progress_bar['x'], progress_bar['y'] + progress_bar['height'] + 20)
    )
    screen.blit(level_shadow, (level_rect.x + 2, level_rect.y + 2))
    screen.blit(level_surface, level_rect)

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
                            lv = ball1.get('level', 0) + ball2.get('level', 0)
                            total_score += score * lv
                            text_x = (x1 + x2) // 2
                            text_y = (y1 + y2) // 2
                            text_color = get_score_color(score)
                            score_fmt = f"+{score}" + ("" if lv == 1 else f"x{lv}")
                            text_surface = font.render(score_fmt, True, text_color)
                            shadow_surface = font.render(score_fmt, True, (0, 0, 0))
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

def init_level(level):
    """初始化指定关卡"""
    global balls, total_score, ball_remain, speedup_remain, levelup_remain, float_texts
    global ghost_ball, speedup_active, speedup_timer
    
    # 重置游戏状态
    balls = []
    total_score = 0
    float_texts = []
    ghost_ball = None
    speedup_active = False
    speedup_timer = 0
    
    # 获取关卡配置
    config = level_configs[level - 1]
    ball_remain = config['init_white_balls']
    
    # 根据关卡解锁状态设置道具数量
    if level >= unlock_config['speedup']:
        speedup_remain = 3 + (level - 1) // 2  # 每2关增加1个加速道具
    else:
        speedup_remain = 0  # 未解锁时数量为0
    
    if level >= unlock_config['levelup']:
        levelup_remain = 3 + (level - 1) // 3  # 每3关增加1个升级道具
    else:
        levelup_remain = 0  # 未解锁时数量为0
    
    # 生成彩球（随机位置、随机类型、随机初始速度）
    color_ball_count = config['color_ball_count']
    
    for i in range(color_ball_count):
        # 随机选择彩球类型（1-9）
        ball_type = i + 1
        img = colorball_images[ball_type]
        
        # 随机位置（确保在游戏区域内，且不会超出边界）
        ball_radius = cbsize // 2
        x = random.randint(gamearea['left'] + ball_radius, gamearea['right'] - ball_radius)
        y = random.randint(gamearea['top'] + ball_radius, gamearea['bottom'] - ball_radius)
        
        # 随机初始速度（较小的速度，避免一开始就高速碰撞）
        speed_x = random.randint(-5, 5)
        speed_y = random.randint(-5, 5)
        # 确保速度不为零
        if speed_x == 0 and speed_y == 0:
            speed_x = random.choice([-3, 3])
        
        balls.append({
            'image': img,
            'rect': img.get_rect(center=(x, y)),
            'speed': [speed_x, speed_y],
            'type': ball_type,
        })
    
    # 绘制关卡开始提示
    level_start_text = f"Level {level} Start!"
    text_surface = font.render(level_start_text, True, (255, 215, 0))
    shadow_surface = font.render(level_start_text, True, (0, 0, 0))
    float_texts.append({
        'shadow': shadow_surface,
        'text': text_surface,
        'x': screen_width // 2,
        'y': screen_height // 2,
        'alpha': 255,
        'life': 120  # 显示2秒
    })
    
    # 检查是否解锁新道具，显示解锁提示
    if level == unlock_config['speedup']:
        unlock_text = "恭喜解锁 加速道具！"
        text_surface = font.render(unlock_text, True, (128, 0, 255))
        shadow_surface = font.render(unlock_text, True, (0, 0, 0))
        float_texts.append({
            'shadow': shadow_surface,
            'text': text_surface,
            'x': screen_width // 2,
            'y': screen_height // 2 + 60,
            'alpha': 255,
            'life': 180  # 显示3秒
        })
    elif level == unlock_config['levelup']:
        unlock_text = "恭喜解锁 升级道具！"
        text_surface = font.render(unlock_text, True, (255, 215, 0))
        shadow_surface = font.render(unlock_text, True, (0, 0, 0))
        float_texts.append({
            'shadow': shadow_surface,
            'text': text_surface,
            'x': screen_width // 2,
            'y': screen_height // 2 + 60,
            'alpha': 255,
            'life': 180  # 显示3秒
        })

def check_level_up():
    """检查是否升级关卡"""
    global current_level
    if current_level > 10:
        return
    
    current_config = level_configs[current_level - 1]
    if total_score >= current_config['target_score']:
        if current_level < 10:
            # 进入下一关
            current_level += 1
            init_level(current_level)
        else:
            # 通关提示
            clear_text = "恭喜！所有关卡已通关！"
            text_surface = font.render(clear_text, True, (255, 215, 0))
            shadow_surface = font.render(clear_text, True, (0, 0, 0))
            float_texts.append({
                'shadow': shadow_surface,
                'text': text_surface,
                'x': screen_width // 2,
                'y': screen_height // 2,
                'alpha': 255,
                'life': 300  # 显示5秒
            })

def start_video():
    """启动视频播放"""
    global video_capture, video_playing, video_timer, video_rect
    
    # 初始化视频捕获
    try:
        video_capture = cv2.VideoCapture('video/kk.mp4')
        if not video_capture.isOpened():
            print("无法打开视频文件")
            return False
    except Exception as e:
        print(f"视频加载错误: {e}")
        return False
    
    # 设置视频显示区域（游戏区域内，居中显示，保持宽高比）
    video_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 计算视频缩放比例，确保适应游戏区域
    gamearea_width = gamearea['right'] - gamearea['left']
    gamearea_height = gamearea['bottom'] - gamearea['top']
    
    scale = min(gamearea_width / video_width, gamearea_height / video_height) * 0.9  # 留10%边距
    new_video_width = int(video_width * scale)
    new_video_height = int(video_height * scale)
    
    # 居中显示
    video_x = gamearea['left'] + (gamearea_width - new_video_width) // 2
    video_y = gamearea['top'] + (gamearea_height - new_video_height) // 2
    video_rect = pygame.Rect(video_x, video_y, new_video_width, new_video_height)
    
    video_playing = True
    video_timer = max_video_time
    return True

def stop_video():
    """停止视频播放"""
    global video_capture, video_playing
    
    if video_capture:
        video_capture.release()
        video_capture = None
    video_playing = False
    
    # 随机奖励一种道具
    reward_random_item()

def reward_random_item():
    """随机奖励一种道具"""
    global ball_remain, speedup_remain, levelup_remain
    
    # 选择可奖励的道具（只选择已解锁的）
    available_items = []
    if True:  # 白球默认可用
        available_items.append('whiteball')
    if current_level >= unlock_config['speedup']:
        available_items.append('speedup')
    if current_level >= unlock_config['levelup']:
        available_items.append('levelup')
    
    if not available_items:
        return
    
    # 随机选择一种道具
    selected_item = random.choice(available_items)
    
    # 奖励道具
    if selected_item == 'whiteball':
        ball_remain += 1
        reward_text = "获得白球 +1！"
        reward_color = (255, 255, 255)
    elif selected_item == 'speedup':
        speedup_remain += 1
        reward_text = "获得加速道具 +1！"
        reward_color = (128, 0, 255)
    elif selected_item == 'levelup':
        levelup_remain += 1
        reward_text = "获得升级道具 +1！"
        reward_color = (255, 215, 0)
    
    # 显示奖励提示
    text_surface = font.render(reward_text, True, reward_color)
    shadow_surface = font.render(reward_text, True, (0, 0, 0))
    float_texts.append({
        'shadow': shadow_surface,
        'text': text_surface,
        'x': screen_width // 2,
        'y': screen_height // 2,
        'alpha': 255,
        'life': 120  # 显示2秒
    })

def draw_kk_button():
    """绘制KK按钮"""
    global kk_button_rect
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 按钮悬停效果
    if kk_button_rect.collidepoint(mouse_x, mouse_y):
        # 绘制高亮边框
        pygame.draw.circle(screen, (255, 255, 0), kk_button_rect.center, kk_button_rect.width//2 + 5, 3)
    
    # 绘制按钮图片
    screen.blit(kk_button_image, kk_button_rect)

def draw_video():
    """绘制视频和倒计时"""
    global video_capture, video_surface, video_timer
    
    if not video_playing or not video_capture:
        return
    
    # 读取视频帧
    ret, frame = video_capture.read()
    if ret:
        # 转换颜色空间（BGR -> RGB）
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 调整帧大小以适应显示区域
        frame_rgb = cv2.resize(frame_rgb, (video_rect.width, video_rect.height))
        # 转换为pygame表面
        video_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        # 绘制视频
        screen.blit(video_surface, video_rect)
    else:
        # 视频播放完毕或出错，重新开始播放
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    # 绘制倒计时
    remaining_time = video_timer // 60  # 转换为秒
    countdown_text = f"{remaining_time}s"
    # 创建带背景的倒计时文本
    text_surface = font.render(countdown_text, True, (255, 0, 0))
    text_rect = text_surface.get_rect()
    
    # 倒计时背景（黑色半透明）
    bg_rect = pygame.Rect(
        video_rect.right - text_rect.width - 20,
        video_rect.top + 10,
        text_rect.width + 20,
        text_rect.height + 10
    )
    pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), bg_rect, 2, border_radius=10)
    
    # 绘制倒计时文本
    text_pos = (
        bg_rect.centerx - text_rect.width//2,
        bg_rect.centery - text_rect.height//2
    )
    screen.blit(text_surface, text_pos)

# 初始化第一关
init_level(current_level)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click_x, click_y = event.pos
            
            # 优先检测KK按钮点击（视频未播放时）
            if not video_playing and kk_button_rect.collidepoint(click_x, click_y):
                start_video()
                continue
            
            # 检查点击位置是否在游戏区域内（视频未播放时）
            if not video_playing and (gamearea['left'] <= click_x <= gamearea['right'] and
                gamearea['top'] <= click_y <= gamearea['bottom']):
                ghost_ball = {
                    'pos': (click_x, click_y),
                    'current_size': min_ghost_size,
                    'scale_dir': 1
                }

            # 加速道具点击检测（只在解锁后有效，且视频未播放）
            if not video_playing and current_level >= unlock_config['speedup']:
                speedup_image_rect = speedup_image.get_rect(
                    topleft=(screen_width - 110 - speedup_image.get_width(), progress_bar['y'] + 270)
                )
                if speedup_image_rect.collidepoint(click_x, click_y):
                    if not speedup_active and speedup_remain > 0:
                        speedup_remain -= 1
                        speedup_active = True
                        speedup_timer = 10 * 60

            # 升级道具点击检测（只在解锁后有效，且视频未播放）
            if not video_playing and current_level >= unlock_config['levelup']:
                levelup_image_rect = levelup_image.get_rect(
                    topleft=(screen_width - 110 - levelup_image.get_width(), progress_bar['y'] + 410)
                )
                if levelup_image_rect.collidepoint(click_x, click_y):
                    if levelup_remain > 0:
                        levelup_remain -= 1
                        whiteballs = []
                        for ball in balls:
                            if ball.get('level') and ball['type'] == 0:  # 只升级白球
                                whiteballs.append(ball)
                        if whiteballs:
                            random.choice(whiteballs)['level'] += 1
                            # 显示升级提示
                            upgrade_text = "Lv +1"
                            text_surface = font.render(upgrade_text, True, (255, 215, 0))
                            shadow_surface = font.render(upgrade_text, True, (0, 0, 0))
                            float_texts.append({
                                'shadow': shadow_surface,
                                'text': text_surface,
                                'x': click_x,
                                'y': click_y - 30,
                                'alpha': 255,
                                'life': 60
                            })

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and ghost_ball is not None and not video_playing:
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
                'type': 0,
                'level': 1,
            })
            ghost_ball = None

    # 视频计时器更新
    if video_playing:
        video_timer -= 1
        if video_timer <= 0:
            stop_video()

    if speedup_active:
        speedup_timer -= 1
        if speedup_timer <= 0:
            speedup_active = False

    # 检查关卡升级（视频未播放时）
    if not video_playing:
        check_level_up()

    screen.fill((0, 0, 0))
    screen.blit(gameback, gameback.get_rect())

    # 绘制视频（如果正在播放）
    if video_playing:
        draw_video()
    else:
        # 视频未播放时，绘制游戏元素
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
            sm = speed_multiplier if speedup_active else 1
            ball['rect'].x += ball['speed'][0] * sm
            ball['rect'].y += ball['speed'][1] * sm
            
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
            if ball.get('level'):
                text = small_font.render(f"x{ball['level']}", True, (0, 0, 0))
                screen.blit(text, ( (ball['rect'].x + ball['rect'].right)//2 - 16, 
                                   (ball['rect'].y + ball['rect'].bottom) // 2 - 16)  )

    # 更新并绘制浮动文本
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

    # 绘制UI元素
    draw_progress()
    draw_whiteball_count()
    draw_speedup_count()
    draw_levelup_count()
    
    # 绘制KK按钮（始终显示在最上层）
    draw_kk_button()
    
    # 如果是最后一关且已通关，显示通关提示
    if current_level == 10 and total_score >= level_configs[9]['target_score'] and not video_playing:
        clear_text = "Mission Complete!"
        text_surface = font.render(clear_text, True, (255, 215, 0))
        text_rect = text_surface.get_rect(center=(screen_width//2, screen_height//2 - 50))
        screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(60)

# 清理资源
if video_capture:
    video_capture.release()
cv2.destroyAllWindows()
pygame.quit()