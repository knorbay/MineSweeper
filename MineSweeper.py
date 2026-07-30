import customtkinter as ctk
import tkinter as tk
import random
import os
from PIL import Image, ImageTk
import time
import pygame
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_MUSICS = [
    "assets/sounds/game_music1.mp3",
    "assets/sounds/game_music2.mp3",
    "assets/sounds/game_music3.mp3",
    "assets/sounds/game_music4.mp3",
    "assets/sounds/game_music5.mp3",
    "assets/sounds/game_music6.mp3"
]
WIN_MUSIC = "assets/sounds/game_win.mp3"
win_music_playing=False
size = 10
NUMBER_COLORS = [
    "",
    "#2563EB",
    "#16A34A",
    "#DC2626",
    "#7C3AED",
    "#B45309",
    "#0891B2",
    "#111827",
    "#6B7280"
]
CELL_SIZE = 48
GRID_SIZE = 0
OFFSET_X = 0
OFFSET_Y = 0
start_time = None
timer_running = False
game_active = True
total_mines = 0
opened_count = 0
previous_screen = None
animation_running = False
music_volume = 0.3
sound_volume = 0.5
def resource_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)
def get_difficulty_name():
    if size == 10:
        return "Easy"
    elif size == 15:
        return "Medium"
    else:
        return "Hard"
def set_difficulty(new_size):
    global size
    size = new_size 
    restart_game()
def calculate_board_geometry():
    global CELL_SIZE, GRID_SIZE, OFFSET_X, OFFSET_Y

    CELL_SIZE = min(560 // size, 48)

    GRID_SIZE = CELL_SIZE * size

    OFFSET_X = (600 - GRID_SIZE) // 2
    OFFSET_Y = (600 - GRID_SIZE) // 2
def draw_board():
    global tiles
    canvas.delete("all")
    tiles = []
    for row in range(size):
        tile_row = []
        for col in range(size):
            x = OFFSET_X + col * CELL_SIZE
            y = OFFSET_Y + row * CELL_SIZE
            tile = canvas.create_rectangle(x,y,x + CELL_SIZE,y + CELL_SIZE,fill="#C9CED6",outline="#9A9A9A",width=2)
            tile_row.append(tile)
        tiles.append(tile_row)
def restart_game():
    global win_music_playing
    if win_music_playing:
        pygame.mixer.music.stop()
        play_game_music()
        win_music_playing = False
    calculate_board_geometry()
    load_images()
    global board, opened, minesplaced
    global game_active, opened_count,flags
    global start_time, timer_running
    game_active = True
    opened_count = 0
    board, opened, minesplaced, flags = create_board()
    draw_board()
    place_mines(minesplaced, board)
    start_time = time.time()
    timer_running = True
    update_timer()
    update_info()
def click(event):
    if not game_active or animation_running:
        return
    col = (event.x - OFFSET_X) // CELL_SIZE
    row = (event.y - OFFSET_Y) // CELL_SIZE
    if 0 <= col < size and 0 <= row < size:
        if not opened[row][col] and not flags[row][col]:
            if board[row][col] != -1:
                open_sound.play()
        opencell(col, row)
def opencell(col, row):
    global opened_count, game_active, timer_running
    if not (0 <= col < size and 0 <= row < size) or opened[row][col]:
        return
    if flags[row][col]:
        return
    opened[row][col] = True  
    opened_count += 1
    draw_cell(row, col)
    value = board[row][col]
    if value == -1:
        timer_running = False
        game_active = False
        show_explosion(row, col)
        reveal_all_mines()
        return
    if value == 0:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                opencell(col + dc, row + dr)
    if game_active:
        check_win()
def create_board():
    board = [[0] * size for _ in range(size)]
    opened = [[False] * size for _ in range(size)]
    minesplaced = [[False] * size for _ in range(size)]
    flags=[[False] * size for _ in range(size)]
    return board, opened, minesplaced , flags
def check_win():
    global game_active,timer_running
    safe_cells = (size * size) - total_mines
    if opened_count == safe_cells:
        game_active = False
        timer_running = False
        show_win()
def draw_flag(row, col):
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2

    canvas.delete(f"flag_{row}_{col}")

    if flags[row][col]:
        flag_sound.play()
        canvas.create_image(
            x,
            y,
            image=flag_image,
            tags=f"flag_{row}_{col}"
        )
def draw_cell(row, col):
    canvas.delete(f"flag_{row}_{col}")
    value = board[row][col]
    canvas.itemconfig(tiles[row][col], fill="#ECECEC")
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    if value == -1:
        canvas.create_image(
        x,
        y,
        image=bomb_image
    )
    elif value > 0:
        color = NUMBER_COLORS[value] if value <= 8 else "black"
        canvas.create_text(x, y, text=str(value), fill=color, font=("Arial", 12, "bold"))
def reveal_all_mines():
    global animation_running
    btn_restart.configure(state="disabled")
    animation_running = True

    mines = []

    for r in range(size):
        for c in range(size):

            if board[r][c] == -1 and not opened[r][c]:
                mines.append((r, c))
    if mines:
        window.after(120, lambda: reveal_next_mine(mines, 0))
def reveal_next_mine(mines, index):
    global animation_running
    
    if index >= len(mines):
        animation_running = False
        show_lose()
        return
    r, c = mines[index]
    opened[r][c] = True
    draw_cell(r, c)
    show_explosion(r, c)
    if index % 4 == 0:
        explosion_sound.play()
    window.after(
        60,
        lambda: reveal_next_mine(mines, index + 1)
    )
def place_mines(minesplaced, board):
    global total_mines
    if size == 10:
        total_mines = random.randint(size+2,size*2-4)
    elif size == 15:
        total_mines = random.randint(size*2,size*2+10)
    else:
        total_mines = random.randint(size*3,size*4-5)
    placed = 0
    while placed < total_mines:
        r = random.randint(0, size - 1)
        c = random.randint(0, size - 1)
        if not minesplaced[r][c]:
            minesplaced[r][c] = True
            board[r][c] = -1  
            placed += 1
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size and board[nr][nc] != -1:
                        board[nr][nc] += 1
def update_info():
    info_label.configure(
        text=f"Mines: {total_mines}"
    )
def right_click(event):
    if not game_active or animation_running:
        return
    col = (event.x - OFFSET_X) // CELL_SIZE
    row = (event.y - OFFSET_Y) // CELL_SIZE
    if not (0 <= row < size and 0 <= col < size):
        return
    if opened[row][col]:
        return
    flags[row][col] = not flags[row][col]

    draw_flag(row, col)
def load_images():
    global bomb_image, flag_image, explosion_image, background_image

    bomb = Image.open(resource_path("assets/bomb.png"))
    bomb = bomb.resize((CELL_SIZE - 8, CELL_SIZE - 8))
    bomb_image = ImageTk.PhotoImage(bomb)

    flag = Image.open(resource_path("assets/flag.png"))
    flag = flag.resize((CELL_SIZE - 8, CELL_SIZE - 8))
    flag_image = ImageTk.PhotoImage(flag)

    explosion = Image.open(resource_path("assets/explosion.png"))
    explosion = explosion.resize((CELL_SIZE , CELL_SIZE )) 
    explosion_image = ImageTk.PhotoImage(explosion)
def show_win():
    global game_active, timer_running, win_music_playing

    game_active = False
    timer_running = False
    win_music_playing = True
    play_win_music()

    canvas.create_rectangle(
        0,
        0,
        600,
        600,
        fill="#FFFFFF",
        stipple="gray50",
        outline=""
    )

    canvas.create_text(
        300,
        260,
        text="YOU WIN!",
        fill="#16A34A",
        font=("Segoe UI", 36, "bold")
    )

    canvas.create_text(
        300,
        310,
        text="All mines cleared!",
        fill="#111827",
        font=("Segoe UI", 16)
    )
def show_lose():
    global game_active, timer_running

    game_active = False
    timer_running = False

    btn_restart.configure(state="normal")

    canvas.create_rectangle(
        0, 0, 600, 600,
        stipple="gray50",
        outline=""
    )

    canvas.create_text(
        300,
        250,
        text="GAME OVER",
        fill="#DC2626",
        font=("Segoe UI", 34, "bold")
    )

    canvas.create_text(
        300,
        300,
        text="You stepped on a mine!",
        fill="white",
        font=("Segoe UI", 16)
    )
def load_sounds():
    global open_sound
    global flag_sound
    global explosion_sound
    global ui_click_sound
    global win_music
    open_sound = pygame.mixer.Sound(resource_path("assets/sounds/opencell_sound.mp3"))

    flag_sound = pygame.mixer.Sound(resource_path("assets/sounds/flag_sound.mp3"))

    explosion_sound = pygame.mixer.Sound(resource_path("assets/sounds/explosion.mp3"))

    win_music = pygame.mixer.Sound("assets/sounds/game_win.mp3")
    open_sound.set_volume(0.4)
    flag_sound.set_volume(0.2)
    explosion_sound.set_volume(0.4)
def play_menu_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path("assets/sounds/menu_music.mp3"))
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)
def play_game_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path(random.choice(GAME_MUSICS)))
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)
def play_win_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path(WIN_MUSIC))
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play()
def update_sound_volume():
    open_sound.set_volume(sound_volume)
    flag_sound.set_volume(sound_volume)
    explosion_sound.set_volume(sound_volume)
def change_music_volume(value):
    global music_volume
    music_volume = value
    pygame.mixer.music.set_volume(music_volume)
def change_sound_volume(value):
    global sound_volume
    sound_volume = value
    update_sound_volume()
def show_explosion(row, col):
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    explosion = canvas.create_image(
        x,
        y,
        image=explosion_image
    )
    window.after(
        300,
        lambda: canvas.delete(explosion)
    )
def load_background():
    global background_image

    background = Image.open(resource_path("assets/background.png"))
    background = background.resize((900, 670))
    background_image = ImageTk.PhotoImage(background)
def show_game():
    play_game_music()
    menu_frame.pack_forget()
    game_screen.pack(fill="both", expand=True)  


def show_settings(from_screen):
    global previous_screen

    previous_screen = from_screen

    menu_frame.pack_forget()
    game_screen.pack_forget()
    settings_frame.pack(fill="both", expand=True)

def back_to_menu():
    settings_frame.pack_forget()

    if previous_screen == "game":
        game_screen.pack(fill="both", expand=True)
    else:
        menu_frame.pack(fill="both", expand=True)

def show_menu():
    play_menu_music()
    game_screen.pack_forget()
    settings_frame.pack_forget()
    menu_frame.pack(fill="both", expand=True)
def settings_return():
    settings_frame.pack_forget()

    if previous_screen == "game":
        game_screen.pack(fill="both", expand=True)
    else:
        menu_frame.pack(fill="both", expand=True)
def update_timer():
    global timer_running

    if not timer_running:
        return

    elapsed = int(time.time() - start_time)

    minutes = elapsed // 60
    seconds = elapsed % 60

    timer_label.configure(
        text=f"⏱ {minutes:02}:{seconds:02}"
    )
    window.after(1000, update_timer)
def change_difficulty(choice):
    if choice == "Easy":
        set_difficulty(10)
    elif choice == "Medium":
        set_difficulty(15)
    elif choice == "Hard":
        set_difficulty(20)

def load_logo():
    global logo_image

    logo = Image.open("assets/icon.png")
    logo = logo.resize((60, 60))
    logo_image = ctk.CTkImage(light_image=logo, dark_image=logo, size=(60, 60))

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("MineSweeper")
window.geometry("900x670")
window.resizable(False, False)
pygame.mixer.init()
load_sounds()
load_logo()
load_background()

background_label = tk.Label(
    window,
    image=background_image,
    borderwidth=0
)
background_label.place(x=0, y=0, relwidth=1, relheight=1)
menu_frame = ctk.CTkFrame(window, fg_color="transparent")
game_screen = ctk.CTkFrame(window, fg_color="transparent")
settings_frame = ctk.CTkFrame(window, fg_color="transparent")

menu_frame.pack(fill="both", expand=True)


title_frame = ctk.CTkFrame(
    menu_frame,
    fg_color="transparent"
)
title_frame.pack(pady=(100,80))
logo_label = ctk.CTkLabel(
    title_frame,
    text="",
    image=logo_image,
)
logo_label.pack(side="left", padx=(0,15))
title = ctk.CTkLabel(
    title_frame,
    text="MineSweeper",
    font=("Segoe UI",42,"bold"),
    text_color="#173A72"
)
title.pack(side="left")

play_button = ctk.CTkButton(
    menu_frame,
    text="Play",
    width=220,
    height=42,
    corner_radius=8,
    fg_color="#173A72",
    hover_color="#0C2760",
    font=("Segoe UI", 15, "bold"),
    command=show_game
)
play_button.pack(pady=(0, 12))

settings_button = ctk.CTkButton(
    menu_frame,
    text="Settings",
    width=220,
    height=42,
    corner_radius=8,
    fg_color="#173A72",
    hover_color="#0C2760",
    font=("Segoe UI", 15, "bold"),
    command=lambda: show_settings("menu")
)
settings_button.pack(pady=(0, 12))

exit_button = ctk.CTkButton(
    menu_frame,
    text="Exit",
    width=220,
    height=42,
    corner_radius=8,
    fg_color="#173A72",
    hover_color="#0C2760",
    font=("Segoe UI", 15, "bold"),
    command=window.destroy
)
exit_button.pack(pady=(0, 12))

separator = ctk.CTkFrame(
    menu_frame,
    width=250,
    height=2,
    fg_color="#DDDDDD"
)
separator.pack(pady=25)

top_frame = ctk.CTkFrame(
    game_screen,
    fg_color="#E5E7EB",
    corner_radius=0
)
top_frame.pack(fill="x")

btn_restart = ctk.CTkButton(
    top_frame,
    text="Restart",
    command=restart_game,
    fg_color="#173A72",
    hover_color="#0C2760",
    text_color="white",
    corner_radius=2,
    font=("Segoe UI", 11, "bold")
)
btn_restart.pack(side=tk.LEFT,padx=5, pady=10)

btn_menu = ctk.CTkButton(
    top_frame,
    text="Main Menu",
    command=show_menu,
    fg_color="#173A72",
    hover_color="#0C2760",
    text_color="white",
    corner_radius=2,
    font=("Segoe UI", 11, "bold")
)
btn_menu.pack(side=tk.LEFT, padx=5, pady=10)
btn_settings = ctk.CTkButton(
    top_frame,
    text="Settings",
    command=lambda: show_settings("game"),
    fg_color="#173A72",
    hover_color="#0C2760",
    text_color="white",
    corner_radius=2,
    font=("Segoe UI", 11, "bold")
)
btn_settings.pack(side=tk.LEFT, padx=5, pady=10)

difficulty_label = ctk.CTkLabel(
    top_frame,
    text="Difficulty:",
    font=("Segoe UI", 11, "bold"),
    text_color="#111827"
)
difficulty_label.pack(side=tk.LEFT, padx=(20, 5))

difficulty_menu = ctk.CTkOptionMenu(
    top_frame,
    values=["Easy", "Medium", "Hard"],
    width=120,
    height=30,
    corner_radius=6,
    fg_color="#173A72",
    button_color="#173A72",
    button_hover_color="#0C2760",
    dropdown_fg_color="white",
    dropdown_hover_color="#E5E7EB",
    dropdown_text_color="#111827",
    command=change_difficulty
)

difficulty_menu.pack(side=tk.LEFT)
difficulty_menu.set("Easy")

info_label = ctk.CTkLabel(
    top_frame,
    text="",
    text_color="#111827",
    font=("Segoe UI", 11, "bold")
)
info_label.pack(side=tk.LEFT, padx=20)

game_frame = ctk.CTkFrame(
    game_screen,
    fg_color="#F3F4F6",
    corner_radius=0
)
game_frame.pack(fill="both", expand=True)

title = ctk.CTkLabel(
    settings_frame,
    text="Settings",
    font=("Segoe UI", 28, "bold")
)
title.pack(pady=40)

music_label = ctk.CTkLabel(
    settings_frame,
    text="Music Volume",
    font=("Segoe UI", 18, "bold")
)
music_label.pack(pady=(20, 5))
music_slider = ctk.CTkSlider(
    settings_frame,
    width=220,
    from_=0,
    to=1,
    number_of_steps=20,
    command=change_music_volume
)
music_slider.set(music_volume)
music_slider.pack(pady=(0, 15))

sound_label = ctk.CTkLabel(
    settings_frame,
    text="Sound Effects",
    font=("Segoe UI", 18, "bold")
)
sound_label.pack(pady=(10, 5))
sound_slider = ctk.CTkSlider(
    settings_frame,
    width=220,
    from_=0,
    to=1,
    number_of_steps=20,
    command=change_sound_volume
)
sound_slider.set(sound_volume)
sound_slider.pack(pady=(0, 20))

back_button = ctk.CTkButton(
    settings_frame,
    text="Return",
    command=settings_return
)
back_button.pack(pady=5)

canvas = tk.Canvas(
    game_frame,
    width=600,
    height=600,
    bg="#ECEFF3",
    highlightthickness=0
)

canvas.pack(anchor="n", pady=20)

canvas.bind("<Button-1>", click)
canvas.bind("<Button-3>", right_click)
timer_label = ctk.CTkLabel(top_frame, text="⏱ 00:00")
timer_label.pack(side=tk.RIGHT, padx=20)
pygame.mixer.init()
load_sounds()
update_sound_volume()
restart_game()
play_menu_music()
window.mainloop()