import pygame
import requests
import sys

# -------- Transmission Function --------
def transmit(freq: int, ip: str, port: int) -> None:
    url = f"http://{ip}:{port}"

    # Send OPTIONS request
    try:
        response = requests.options(url)
        print("OPTIONS response:", response)
    except Exception as e:
        print("OPTIONS request failed:", e)

    # Send POST request
    headers = {'Content-Type': 'application/json'}
    data = freq

    print("Transmitting Data:", data)

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Transmission successful:", response.json())
        else:
            print("Transmission failed:", response.status_code, response.text)
    except Exception as e:
        print("POST request failed:", e)


# -------- Pygame Slider Script --------
pygame.init()

# Window
WIDTH, HEIGHT = 600, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Frequency Transmitter")

# Slider settings
slider_x = 100
slider_y = 100
slider_width = 400
slider_height = 8
handle_radius = 10

min_value = 10_000_000
max_value = 4_000_000_000
value = min_value
dragging = False

font = pygame.font.SysFont(None, 30)

def draw_slider():
    pygame.draw.rect(screen, (200, 200, 200), (slider_x, slider_y, slider_width, slider_height))
    handle_pos = slider_x + (value - min_value) / (max_value - min_value) * slider_width
    pygame.draw.circle(screen, (100, 100, 255), (int(handle_pos), slider_y + slider_height // 2), handle_radius)
    text_surface = font.render(f"{value:,}", True, (255, 255, 255))
    screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, slider_y - 40))

def update_value(mouse_x):
    global value
    ratio = max(0, min(1, (mouse_x - slider_x) / slider_width))
    new_value = int(min_value + ratio * (max_value - min_value))
    return new_value

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_pos = slider_x + (value - min_value) / (max_value - min_value) * slider_width
                if abs(event.pos[0] - handle_pos) <= handle_radius * 2:
                    dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False

        elif event.type == pygame.MOUSEMOTION and dragging:
            new_value = update_value(event.pos[0])
            if new_value != value:
                value = new_value
                transmit(value / 1.2, "192.168.2.69", 8080)  # Send automatically

    screen.fill((30, 30, 30))
    draw_slider()
    pygame.display.flip()
