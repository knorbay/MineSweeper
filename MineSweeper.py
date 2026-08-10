import customtkinter as ctk
import tkinter as tk
import random
import os
import json
import time
from PIL import Image, ImageTk
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
win_music_playing = False
size = 10

NUMBER_COLORS = [
    "",
    "#1D4ED8",
    "#16A34A",
    "#DC2626",
    "#7C3AED",
    "#D97706",
    "#0D9488",
    "#1E293B",
    "#0F172A"
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
is_muted = False
highscores = {"Easy": None, "Medium": None, "Hard": None}

def resource_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

def load_highscores():
    global highscores
    try:
        path = resource_path("highscores.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                highscores = json.load(f)
    except Exception:
        highscores = {"Easy": None, "Medium": None, "Hard": None}

def save_highscores():
    try:
        path = resource_path("highscores.json")
        with open(path, "w") as f:
            json.dump(highscores, f)
    except Exception:
        pass

def reset_highscores():
    global highscores
    highscores = {"Easy": None, "Medium": None, "Hard": None}
    save_highscores()
    update_highscore_label()

def get_difficulty_name():
    if size == 10:
        return "Easy"
    elif size == 15:
        return "Medium"
    else:
        return "Hard"

def set_difficulty(new_size):
    global size
    if animation_running:
        return
    size = new_size 
    restart_game()

def calculate_board_geometry():
    global CELL_SIZE, GRID_SIZE, OFFSET_X, OFFSET_Y
    CELL_SIZE = max(20, min(540 // size, 48))
    GRID_SIZE = CELL_SIZE * size
    OFFSET_X = (580 - GRID_SIZE) // 2
    OFFSET_Y = (580 - GRID_SIZE) // 2

def draw_board():
    global tiles
    canvas.delete("all")
    tiles = []
    canvas.create_rectangle(
        OFFSET_X - 4, OFFSET_Y - 4, 
        OFFSET_X + GRID_SIZE + 4, OFFSET_Y + GRID_SIZE + 4,
        fill="#0B1220", outline="#31507A", width=2
    )
    for row in range(size):
        tile_row = []
        for col in range(size):
            x = OFFSET_X + col * CELL_SIZE
            y = OFFSET_Y + row * CELL_SIZE
            tile = canvas.create_rectangle(
                x, y, x + CELL_SIZE, y + CELL_SIZE,
                fill="#2E4A73", outline="#0B1220", width=1
            )
            tile_row.append(tile)
        tiles.append(tile_row)

def restart_game():
    global win_music_playing, animation_running
    if animation_running:
        return
    if win_music_playing:
        pygame.mixer.music.stop()
        play_game_music()
        win_music_playing = False
    calculate_board_geometry()
    load_images()
    global board, opened, minesplaced, flags
    global game_active, opened_count
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
    update_highscore_label()

def click(event):
    if not game_active or animation_running:
        return
    col = (event.x - OFFSET_X) // CELL_SIZE
    row = (event.y - OFFSET_Y) // CELL_SIZE
    if 0 <= col < size and 0 <= row < size:
        if not opened[row][col] and not flags[row][col]:
            if board[row][col] != -1 and not is_muted:
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
    flags = [[False] * size for _ in range(size)]
    return board, opened, minesplaced, flags

def check_win():
    global game_active, timer_running
    safe_cells = (size * size) - total_mines
    if opened_count == safe_cells:
        game_active = False
        timer_running = False
        elapsed = int(time.time() - start_time)
        diff_name = get_difficulty_name()
        if diff_name in highscores:
            curr = highscores[diff_name]
            if curr is None or elapsed < curr:
                highscores[diff_name] = elapsed
                save_highscores()
                update_highscore_label()
        show_win(elapsed)

def draw_flag(row, col):
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    canvas.delete(f"flag_{row}_{col}")
    if flags[row][col]:
        if not is_muted:
            flag_sound.play()
        canvas.create_image(x, y, image=flag_image, tags=f"flag_{row}_{col}")
    update_info()

def draw_cell(row, col):
    canvas.delete(f"flag_{row}_{col}")
    value = board[row][col]
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    
    if value == -1:
        canvas.itemconfig(tiles[row][col], fill="#F87171")
        canvas.create_image(x, y, image=bomb_image)
    else:
        canvas.itemconfig(tiles[row][col], fill="#D8E2F0")
        if value > 0:
            color = NUMBER_COLORS[value] if value <= 8 else "#0F172A"
            font_size = max(11, int(CELL_SIZE * 0.52))
            canvas.create_text(x, y, text=str(value), fill=color, font=("Segoe UI", font_size, "bold"))

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
        if size <= 10:
            sound_step = 2
        elif size <= 15:
            sound_step = 4
        else:
            sound_step = 6
        
        target_interval_ms = 300
        reveal_delay = max(40, target_interval_ms // sound_step)
        
        window.after(reveal_delay, lambda: reveal_next_mine(mines, 0, reveal_delay, sound_step))
    else:
        animation_running = False
        show_lose()

def reveal_next_mine(mines, index, delay, sound_step):
    global animation_running
    if index >= len(mines):
        animation_running = False
        show_lose()
        return
    r, c = mines[index]
    opened[r][c] = True
    draw_cell(r, c)
    show_explosion(r, c)
    
    if index % sound_step == 0 and not is_muted:
        explosion_sound.play()
        
    window.after(delay, lambda: reveal_next_mine(mines, index + 1, delay, sound_step))

def place_mines(minesplaced, board):
    global total_mines
    if size == 10:
        total_mines = random.randint(12, 16)
    elif size == 15:
        total_mines = random.randint(30, 40)
    else:
        total_mines = random.randint(60, 75)
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
    placed_flags = sum(row.count(True) for row in flags) if 'flags' in globals() else 0
    info_label.configure(text=f"MINES: {total_mines}")
    flag_label.configure(text=f"FLAGS: {placed_flags}/{total_mines}")

def update_highscore_label():
    diff_name = get_difficulty_name()
    best = highscores.get(diff_name)
    if best is not None:
        m = best // 60
        s = best % 60
        highscore_label.configure(text=f"BEST: {m:02}:{s:02}")
    else:
        highscore_label.configure(text="BEST: --:--")

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
    img_size = max(14, CELL_SIZE - 10)
    bomb = Image.open(resource_path("assets/bomb.png")).resize((img_size, img_size))
    bomb_image = ImageTk.PhotoImage(bomb)

    flag = Image.open(resource_path("assets/flag.png")).resize((img_size, img_size))
    flag_image = ImageTk.PhotoImage(flag)

    explosion = Image.open(resource_path("assets/explosion.png")).resize((CELL_SIZE, CELL_SIZE))
    explosion_image = ImageTk.PhotoImage(explosion)

def show_win(elapsed_seconds):
    global game_active, timer_running, win_music_playing
    game_active = False
    timer_running = False
    win_music_playing = True
    play_win_music()
    m = elapsed_seconds // 60
    s = elapsed_seconds % 60
    canvas.create_rectangle(110, 210, 470, 350, fill="#1E2F4D", outline="#22C55E", width=2)
    canvas.create_text(290, 250, text="YOU WIN!", fill="#22C55E", font=("Segoe UI", 32, "bold"))
    canvas.create_text(290, 295, text=f"Time: {m:02}:{s:02} - All mines cleared!", fill="#F8FAFC", font=("Segoe UI", 13))

def show_lose():
    global game_active, timer_running
    game_active = False
    timer_running = False
    btn_restart.configure(state="normal")
    canvas.create_rectangle(110, 220, 470, 340, fill="#1E2F4D", outline="#F87171", width=2)
    canvas.create_text(290, 260, text="GAME OVER", fill="#F87171", font=("Segoe UI", 32, "bold"))
    canvas.create_text(290, 305, text="You stepped on a mine!", fill="#F8FAFC", font=("Segoe UI", 14))

def load_sounds():
    global open_sound, flag_sound, explosion_sound, win_music
    open_sound = pygame.mixer.Sound(resource_path("assets/sounds/opencell_sound.mp3"))
    flag_sound = pygame.mixer.Sound(resource_path("assets/sounds/flag_sound.mp3"))
    explosion_sound = pygame.mixer.Sound(resource_path("assets/sounds/explosion.mp3"))
    win_music = pygame.mixer.Sound(resource_path(WIN_MUSIC))

def play_menu_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path("assets/sounds/menu_music.mp3"))
    pygame.mixer.music.set_volume(0 if is_muted else music_volume)
    pygame.mixer.music.play(-1)

def play_game_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path(random.choice(GAME_MUSICS)))
    pygame.mixer.music.set_volume(0 if is_muted else music_volume)
    pygame.mixer.music.play(-1)

def play_win_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(resource_path(WIN_MUSIC))
    pygame.mixer.music.set_volume(0 if is_muted else music_volume)
    pygame.mixer.music.play()

def update_sound_volume():
    vol = 0 if is_muted else sound_volume
    open_sound.set_volume(vol)
    flag_sound.set_volume(vol)
    explosion_sound.set_volume(vol)

def change_music_volume(value):
    global music_volume
    music_volume = value
    if not is_muted:
        pygame.mixer.music.set_volume(music_volume)

def change_sound_volume(value):
    global sound_volume
    sound_volume = value
    update_sound_volume()

def toggle_mute():
    global is_muted
    is_muted = not is_muted
    if is_muted:
        pygame.mixer.music.set_volume(0)
        btn_mute.configure(text="Unmute", fg_color="#F87171")
    else:
        pygame.mixer.music.set_volume(music_volume)
        btn_mute.configure(text="Mute", fg_color="#31507A")
    update_sound_volume()

def show_explosion(row, col):
    x = OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    explosion = canvas.create_image(x, y, image=explosion_image)
    window.after(250, lambda: canvas.delete(explosion))

def show_game():
    play_game_music()
    menu_frame.pack_forget()
    settings_frame.pack_forget()
    game_screen.pack(fill="both", expand=True)  

def show_settings(from_screen):
    global previous_screen
    previous_screen = from_screen
    menu_frame.pack_forget()
    game_screen.pack_forget()
    settings_frame.pack(fill="both", expand=True)

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
    timer_label.configure(text=f"{minutes:02}:{seconds:02}")
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
    logo = Image.open(resource_path("assets/icon.png"))
    logo_image = ctk.CTkImage(light_image=logo, dark_image=logo, size=(64, 64))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("MineSweeper")
window.geometry("1200x900")
window.minsize(900, 700)
window.resizable(True, True)

pygame.mixer.init()
load_highscores()
load_sounds()
load_logo()


menu_frame = ctk.CTkFrame(window, bg_color="#0B1220", fg_color="transparent")
game_screen = ctk.CTkFrame(window, bg_color="#0B1220", fg_color="transparent")
settings_frame = ctk.CTkFrame(window, bg_color="#0B1220", fg_color="transparent")

menu_card = ctk.CTkFrame(menu_frame,bg_color="#0B1220", fg_color="#1E2F4D", corner_radius=16, border_width=1, border_color="#31507A", width=420, height=480)
menu_card.pack_propagate(False)
menu_card.place(relx=0.5, rely=0.5, anchor="center")

title_frame = ctk.CTkFrame(menu_card, fg_color="transparent")
title_frame.pack(pady=(40, 40))

logo_label = ctk.CTkLabel(title_frame, text="", image=logo_image)
logo_label.pack(side="left", padx=(0, 12))

title = ctk.CTkLabel(
    title_frame,
    text="MineSweeper",
    font=("Segoe UI", 36, "bold"),
    text_color="#A7D8FF"
)
title.pack(side="left")

play_button = ctk.CTkButton(
    menu_card,
    text="Play Game",
    width=280,
    height=46,
    corner_radius=10,
    fg_color="#31507A",
    hover_color="#43699E",
    border_width=1,
    border_color="#8EC5FF",
    font=("Segoe UI", 16, "bold"),
    command=show_game
)
play_button.pack(pady=10)

settings_button = ctk.CTkButton(
    menu_card,
    text="Settings",
    width=280,
    height=46,
    corner_radius=10,
    fg_color="#31507A",
    hover_color="#43699E",
    border_width=1,
    border_color="#8EC5FF",
    font=("Segoe UI", 15, "bold"),
    command=lambda: show_settings("menu")
)
settings_button.pack(pady=10)

exit_button = ctk.CTkButton(
    menu_card,
    text="Exit",
    width=280,
    height=46,
    corner_radius=10,
    fg_color="#31507A",
    hover_color="#43699E",
    border_width=1,
    border_color="#8EC5FF",
    font=("Segoe UI", 15, "bold"),
    command=window.destroy
)
exit_button.pack(pady=10)

top_frame = ctk.CTkFrame(
    game_screen,
    fg_color="#162338",
    corner_radius=0,
    height=60
)
top_frame.pack(fill="x")

left_controls = ctk.CTkFrame(top_frame, fg_color="transparent")
left_controls.pack(side=tk.LEFT, padx=15, pady=10)

btn_restart = ctk.CTkButton(
    left_controls,
    text="Restart",
    command=restart_game,
    fg_color="#31507A",
    hover_color="#43699E",
    text_color="#F8FAFC",
    width=90,
    height=32,
    corner_radius=6,
    font=("Segoe UI", 12, "bold")
)
btn_restart.pack(side=tk.LEFT, padx=4)

btn_menu = ctk.CTkButton(
    left_controls,
    text="Main Menu",
    command=show_menu,
    fg_color="#31507A",
    hover_color="#43699E",
    text_color="#F8FAFC",
    width=100,
    height=32,
    corner_radius=6,
    font=("Segoe UI", 12, "bold")
)
btn_menu.pack(side=tk.LEFT, padx=4)

btn_settings = ctk.CTkButton(
    left_controls,
    text="Settings",
    command=lambda: show_settings("game"),
    fg_color="#31507A",
    hover_color="#43699E",
    text_color="#F8FAFC",
    width=90,
    height=32,
    corner_radius=6,
    font=("Segoe UI", 12, "bold")
)
btn_settings.pack(side=tk.LEFT, padx=4)

btn_mute = ctk.CTkButton(
    left_controls,
    text="Mute",
    command=toggle_mute,
    fg_color="#31507A",
    hover_color="#43699E",
    text_color="#F8FAFC",
    width=70,
    height=32,
    corner_radius=6,
    font=("Segoe UI", 12, "bold")
)
btn_mute.pack(side=tk.LEFT, padx=4)

right_controls = ctk.CTkFrame(top_frame, fg_color="transparent")
right_controls.pack(side=tk.RIGHT, padx=15, pady=10)

timer_label = ctk.CTkLabel(
    right_controls, 
    text="00:00", 
    font=("Segoe UI", 14, "bold"), 
    text_color="#F8FAFC",
    fg_color="#31507A",
    corner_radius=8,
    width=75,
    height=32
)
timer_label.pack(side=tk.RIGHT, padx=4)

info_label = ctk.CTkLabel(
    right_controls,
    text="MINES: 0",
    text_color="#F8FAFC",
    font=("Segoe UI", 12, "bold"),
    fg_color="#31507A",
    corner_radius=8,
    width=85,
    height=32
)
info_label.pack(side=tk.RIGHT, padx=4)

flag_label = ctk.CTkLabel(
    right_controls,
    text="FLAGS: 0/0",
    text_color="#F8FAFC",
    font=("Segoe UI", 12, "bold"),
    fg_color="#31507A",
    corner_radius=8,
    width=95,
    height=32
)
flag_label.pack(side=tk.RIGHT, padx=4)

highscore_label = ctk.CTkLabel(
    right_controls,
    text="BEST: --:--",
    text_color="#22C55E",
    font=("Segoe UI", 12, "bold"),
    fg_color="#31507A",
    corner_radius=8,
    width=100,
    height=32
)
highscore_label.pack(side=tk.RIGHT, padx=4)

difficulty_menu = ctk.CTkOptionMenu(
    right_controls,
    values=["Easy", "Medium", "Hard"],
    width=100,
    height=32,
    corner_radius=8,
    fg_color="#31507A",
    button_color="#43699E",
    button_hover_color="#527CB8",
    dropdown_fg_color="#1E2F4D",
    dropdown_hover_color="#31507A",
    dropdown_text_color="#F8FAFC",
    command=change_difficulty
)
difficulty_menu.pack(side=tk.RIGHT, padx=4)
difficulty_menu.set("Easy")

game_frame = ctk.CTkFrame(game_screen,bg_color="#0B1220", fg_color="transparent")
game_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(
    game_frame,
    width=580,
    height=580,
    bg="#0B1220",
    highlightthickness=0
)
canvas.pack(expand=True, pady=20)

settings_card = ctk.CTkFrame(settings_frame,bg_color="#0B1220", fg_color="#1E2F4D", border_width=1, border_color="#31507A", width=440, height=480)
settings_card.pack_propagate(False)
settings_card.place(relx=0.5, rely=0.5, anchor="center")

settings_title = ctk.CTkLabel(
    settings_card,
    text="Settings",
    font=("Segoe UI", 28, "bold"),
    text_color="#A7D8FF"
)
settings_title.pack(pady=(25, 15))

music_label = ctk.CTkLabel(
    settings_card,
    text="Music Volume",
    font=("Segoe UI", 14, "bold"),
    text_color="#A7D8FF"
)
music_label.pack(pady=(5, 2))

music_slider = ctk.CTkSlider(
    settings_card,
    width=260,
    from_=0,
    to=1,
    number_of_steps=20,
    button_color="#43699E",
    button_hover_color="#527CB8",
    command=change_music_volume
)
music_slider.set(music_volume)
music_slider.pack(pady=(0, 15))

sound_label = ctk.CTkLabel(
    settings_card,
    text="Sound Effects",
    font=("Segoe UI", 14, "bold"),
    text_color="#A7D8FF"
)
sound_label.pack(pady=(5, 2))

sound_slider = ctk.CTkSlider(
    settings_card,
    width=260,
    from_=0,
    to=1,
    number_of_steps=20,
    button_color="#43699E",
    button_hover_color="#527CB8",
    command=change_sound_volume
)
sound_slider.set(sound_volume)
sound_slider.pack(pady=(0, 15))

divider = ctk.CTkFrame(settings_card, height=1, width=320, fg_color="#31507A")
divider.pack(pady=15)

btn_reset_scores = ctk.CTkButton(
    settings_card,
    text="Reset Highscores",
    width=260,
    height=36,
    corner_radius=8,
    fg_color="#7F1D1D",
    hover_color="#991B1B",
    font=("Segoe UI", 13, "bold"),
    command=reset_highscores
)
btn_reset_scores.pack(pady=(5, 15))

back_button = ctk.CTkButton(
    settings_card,
    text="Save & Return",
    width=260,
    height=42,
    corner_radius=10,
    fg_color="#31507A",
    hover_color="#43699E",
    font=("Segoe UI", 14, "bold"),
    command=settings_return
)
back_button.pack(pady=(10, 20))

window.bind("<F5>", lambda event: restart_game())
window.bind("<Escape>", lambda event: show_menu())
window.bind("<F1>", lambda event: show_settings("game"))
window.bind("<r>", lambda event: restart_game())
window.bind("<R>", lambda event: restart_game())

canvas.bind("<Button-1>", click)
canvas.bind("<Button-3>", right_click)

menu_frame.pack(fill="both", expand=True)

update_sound_volume()
restart_game()
play_menu_music()

window.mainloop()
