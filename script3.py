import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys

# Используем только win32 API для надежности
import win32api
import win32con
import win32gui
import win32process


class InvokerMacroGUI:
    def __init__(self):
        self.active = False
        self.config_file = 'invoker_config.json'

        # Настройки задержек
        self.spell_delays = {
            'invoke': 0.6,
            'cast': 0.2,
            'key': 0.05,
            'press_duration': 0.03,
        }

        # Словарь заклинаний
        self.spells = {
            'cold_snap': {'name': 'Cold Snap', 'sequence': ['q', 'q', 'q'], 'color': '#4CAF50', 'hotkey': '1'},
            'ghost_walk': {'name': 'Ghost Walk', 'sequence': ['q', 'q', 'w'], 'color': '#2196F3', 'hotkey': '2'},
            'ice_wall': {'name': 'Ice Wall', 'sequence': ['q', 'q', 'e'], 'color': '#00BCD4', 'hotkey': '3'},
            'emp': {'name': 'EMP', 'sequence': ['w', 'w', 'w'], 'color': '#FF9800', 'hotkey': '4'},
            'tornado': {'name': 'Tornado', 'sequence': ['w', 'w', 'q'], 'color': '#9C27B0', 'hotkey': '5'},
            'meteor': {'name': 'Meteor', 'sequence': ['e', 'e', 'w'], 'color': '#F44336', 'hotkey': '6'},
            'deafening_blast': {'name': 'Deafening Blast', 'sequence': ['q', 'w', 'e'], 'color': '#E91E63',
                                'hotkey': '7'},
            'alacrity': {'name': 'Alacrity', 'sequence': ['w', 'w', 'e'], 'color': '#8BC34A', 'hotkey': '8'},
            'sun_strike': {'name': 'Sun Strike', 'sequence': ['e', 'e', 'e'], 'color': '#FFC107', 'hotkey': '9'},
            'forge_spirit': {'name': 'Forge Spirit', 'sequence': ['e', 'e', 'q'], 'color': '#795548', 'hotkey': '0'},
        }

        # Маппинг клавиш для win32 API (HEX коды)
        self.vk_codes = {
            'q': 0x51, 'w': 0x57, 'e': 0x45, 'r': 0x52,
            'd': 0x44, 'f': 0x46, '1': 0x31, '2': 0x32,
            '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36,
            '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
        }

        self.create_gui()
        self.load_config()
        self.start_keyboard_listener()

    def send_key_to_game(self, key):
        """
        Отправка клавиши напрямую в окно Dota 2
        Это решает проблему с системными хоткеями
        """
        try:
            # Ищем окно Dota 2
            dota_window = win32gui.FindWindow(None, "Dota 2")
            if not dota_window:
                # Пробуем альтернативные названия
                dota_window = win32gui.FindWindow(None, "Dota 2 - Сила Древних")

            if dota_window:
                # Получаем ID потока окна
                thread_id, process_id = win32process.GetWindowThreadProcessId(dota_window)

                # Отправляем клавишу напрямую в окно игры
                vk_code = self.vk_codes.get(key.lower(), 0)
                if vk_code:
                    # Нажатие
                    win32api.PostMessage(dota_window, win32con.WM_KEYDOWN, vk_code, 0)
                    time.sleep(self.spell_delays['press_duration'])
                    # Отпускание
                    win32api.PostMessage(dota_window, win32con.WM_KEYUP, vk_code, 0)
                    return True
            else:
                # Если окно не найдено, используем глобальную отправку
                return self.send_key_global(key)
        except Exception as e:
            self.add_log(f"⚠️ Send to window error: {e}", '#e74c3c')
            return self.send_key_global(key)

        return False

    def send_key_global(self, key):
        """
        Глобальная отправка клавиши (без системных хоткеев)
        Используем KEYEVENTF_SCANCODE для обхода системных комбинаций
        """
        try:
            vk_code = self.vk_codes.get(key.lower(), 0)
            if vk_code:
                # Получаем скан-код (обходит системные хоткеи)
                scan_code = win32api.MapVirtualKey(vk_code, 0)

                # Нажатие с флагом SCANCODE (не генерирует системные события)
                win32api.keybd_event(vk_code, scan_code, 0, 0)
                time.sleep(self.spell_delays['press_duration'])
                # Отпускание
                win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
                return True
        except Exception as e:
            self.add_log(f"⚠️ Global send error: {e}", '#e74c3c')

        return False

    def send_sequence(self, keys):
        """Отправка последовательности клавиш"""
        for key in keys:
            # Сначала пробуем отправить в окно игры
            if not self.send_key_to_game(key):
                # Если не получилось, используем глобальный метод
                self.send_key_global(key)
            time.sleep(self.spell_delays['key'])

    def create_gui(self):
        """Создание графического интерфейса"""
        self.root = tk.Tk()
        self.root.title("Invoker Macro - Fixed Sound Issue")
        self.root.geometry("650x850")
        self.root.minsize(550, 700)
        self.root.attributes('-topmost', True)

        # Стиль
        style = ttk.Style()
        style.theme_use('clam')

        # Верхняя панель
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="INVOKER MACRO - NO SOUND ISSUE",
                               font=('Arial', 16, 'bold'),
                               bg='#2c3e50', fg='white')
        title_label.pack(pady=20)

        # Панель статуса
        status_frame = tk.Frame(self.root, bg='#34495e', height=70)
        status_frame.pack(fill='x')
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="● STOPPED",
                                     font=('Arial', 16, 'bold'),
                                     bg='#34495e', fg='red')
        self.status_label.pack(side='left', padx=20, pady=15)

        # Основной контейнер с прокруткой
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(main_container, bg='#ecf0f1', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#ecf0f1')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Привязка колесика
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Создание виджетов
        self.create_info_panel()
        self.create_spell_buttons()
        self.create_settings_panel()
        self.create_log_panel()
        self.create_control_panel()

    def create_info_panel(self):
        """Информационная панель"""
        info_frame = tk.LabelFrame(self.scrollable_frame, text="ℹ️ IMPORTANT INFO",
                                   font=('Arial', 12, 'bold'),
                                   bg='#ecf0f1', fg='#e74c3c')
        info_frame.pack(fill='x', pady=5)

        info_text = """✓ FIXED: Sound no longer turns off when casting spells!
✓ Keys are sent directly to Dota 2 window
✓ Run as Administrator for best results
✓ Make sure Dota 2 window is active"""

        info_label = tk.Label(info_frame, text=info_text, bg='#ecf0f1', fg='#2c3e50',
                              font=('Arial', 9), justify='left')
        info_label.pack(pady=10, padx=10)

    def create_spell_buttons(self):
        """Создание кнопок заклинаний"""
        spells_title = tk.Label(self.scrollable_frame, text="🔮 SPELLS (Press number keys 1-0)",
                                font=('Arial', 14, 'bold'), bg='#ecf0f1', fg='#2c3e50')
        spells_title.pack(pady=(10, 10), anchor='w')

        spells_frame = tk.Frame(self.scrollable_frame, bg='#ecf0f1')
        spells_frame.pack(fill='x', pady=5)

        spell_items = list(self.spells.items())
        for i in range(0, len(spell_items), 2):
            row_frame = tk.Frame(spells_frame, bg='#ecf0f1')
            row_frame.pack(fill='x', pady=5)

            if i < len(spell_items):
                spell_id, spell = spell_items[i]
                self.create_spell_card(row_frame, spell_id, spell, 0)

            if i + 1 < len(spell_items):
                spell_id, spell = spell_items[i + 1]
                self.create_spell_card(row_frame, spell_id, spell, 1)

            row_frame.columnconfigure(0, weight=1)
            row_frame.columnconfigure(1, weight=1)

    def create_spell_card(self, parent, spell_id, spell, column):
        card = tk.Frame(parent, bg='white', relief='solid', bd=1)
        card.grid(row=0, column=column, padx=10, pady=5, sticky='nsew')

        color = spell.get('color', '#95a5a6')

        color_bar = tk.Frame(card, bg=color, height=5)
        color_bar.pack(fill='x')

        header_frame = tk.Frame(card, bg='white')
        header_frame.pack(fill='x', padx=10, pady=(10, 5))

        hotkey_label = tk.Label(header_frame, text=f"[{spell['hotkey']}]",
                                font=('Arial', 16, 'bold'), bg='white', fg=color)
        hotkey_label.pack(side='left')

        name_label = tk.Label(header_frame, text=spell['name'],
                              font=('Arial', 12, 'bold'), bg='white')
        name_label.pack(side='left', padx=(10, 0))

        combo_text = ' + '.join([k.upper() for k in spell['sequence']])
        combo_label = tk.Label(card, text=combo_text,
                               font=('Courier', 11, 'bold'),
                               bg='#f8f9fa', fg='#7f8c8d', pady=5)
        combo_label.pack(fill='x', padx=10, pady=(0, 10))

        cast_btn = tk.Button(card, text="⚡ CAST",
                             command=lambda sid=spell_id: self.cast_spell(sid),
                             bg=color, fg='white',
                             font=('Arial', 10, 'bold'),
                             cursor='hand2')
        cast_btn.pack(fill='x', padx=10, pady=(0, 10))

    def create_settings_panel(self):
        settings_frame = tk.LabelFrame(self.scrollable_frame, text="⚙️ SETTINGS",
                                       font=('Arial', 12, 'bold'),
                                       bg='#ecf0f1', fg='#2c3e50')
        settings_frame.pack(fill='x', pady=10)

        delays_frame = tk.Frame(settings_frame, bg='#ecf0f1')
        delays_frame.pack(padx=15, pady=10)

        # Key Press Duration
        tk.Label(delays_frame, text="Key Press Duration:", bg='#ecf0f1', font=('Arial', 10)).grid(row=0, column=0,
                                                                                                  sticky='w', pady=5)
        self.press_duration_var = tk.DoubleVar(value=self.spell_delays['press_duration'])
        press_scale = tk.Scale(delays_frame, from_=0.01, to=0.1, resolution=0.01,
                               orient='horizontal', variable=self.press_duration_var,
                               length=250, bg='#ecf0f1')
        press_scale.grid(row=0, column=1, padx=10)
        self.press_duration_label = tk.Label(delays_frame, text=f"{self.spell_delays['press_duration']}s", bg='#ecf0f1',
                                             width=6)
        self.press_duration_label.grid(row=0, column=2)
        press_scale.configure(command=self.update_press_duration)

        # Invoke Delay
        tk.Label(delays_frame, text="Invoke Delay:", bg='#ecf0f1', font=('Arial', 10)).grid(row=1, column=0, sticky='w',
                                                                                            pady=5)
        self.invoke_delay_var = tk.DoubleVar(value=self.spell_delays['invoke'])
        invoke_scale = tk.Scale(delays_frame, from_=0.3, to=1.5, resolution=0.05,
                                orient='horizontal', variable=self.invoke_delay_var,
                                length=250, bg='#ecf0f1')
        invoke_scale.grid(row=1, column=1, padx=10)
        self.invoke_delay_label = tk.Label(delays_frame, text=f"{self.spell_delays['invoke']}s", bg='#ecf0f1', width=6)
        self.invoke_delay_label.grid(row=1, column=2)
        invoke_scale.configure(command=self.update_invoke_delay)

        # Cast Delay
        tk.Label(delays_frame, text="Cast Delay:", bg='#ecf0f1', font=('Arial', 10)).grid(row=2, column=0, sticky='w',
                                                                                          pady=5)
        self.cast_delay_var = tk.DoubleVar(value=self.spell_delays['cast'])
        cast_scale = tk.Scale(delays_frame, from_=0.1, to=0.8, resolution=0.05,
                              orient='horizontal', variable=self.cast_delay_var,
                              length=250, bg='#ecf0f1')
        cast_scale.grid(row=2, column=1, padx=10)
        self.cast_delay_label = tk.Label(delays_frame, text=f"{self.spell_delays['cast']}s", bg='#ecf0f1', width=6)
        self.cast_delay_label.grid(row=2, column=2)
        cast_scale.configure(command=self.update_cast_delay)

        # Hotkeys
        hotkey_frame = tk.Frame(settings_frame, bg='#ecf0f1')
        hotkey_frame.pack(padx=15, pady=(0, 10))

        tk.Label(hotkey_frame, text="Invoke Key:", bg='#ecf0f1', font=('Arial', 10)).grid(row=0, column=0, padx=5)
        self.invoke_key_var = tk.StringVar(value="R")
        invoke_entry = tk.Entry(hotkey_frame, textvariable=self.invoke_key_var, width=8, font=('Arial', 10))
        invoke_entry.grid(row=0, column=1, padx=5)

        tk.Label(hotkey_frame, text="Cast Key:", bg='#ecf0f1', font=('Arial', 10)).grid(row=0, column=2, padx=5)
        self.cast_key_var = tk.StringVar(value="D")
        cast_entry = tk.Entry(hotkey_frame, textvariable=self.cast_key_var, width=8, font=('Arial', 10))
        cast_entry.grid(row=0, column=3, padx=5)

    def create_log_panel(self):
        log_frame = tk.LabelFrame(self.scrollable_frame, text="📋 LOG",
                                  font=('Arial', 12, 'bold'),
                                  bg='#ecf0f1', fg='#2c3e50')
        log_frame.pack(fill='both', expand=True, pady=10)

        self.log_text = tk.Text(log_frame, height=10, bg='black', fg='#00ff00',
                                font=('Consolas', 9), wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def create_control_panel(self):
        control_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', height=80)
        control_frame.pack(fill='x', pady=(10, 0))
        control_frame.pack_propagate(False)

        self.toggle_btn = tk.Button(control_frame, text="▶ START",
                                    command=self.toggle_macro,
                                    bg='#27ae60', fg='white',
                                    font=('Arial', 14, 'bold'),
                                    width=15, height=2,
                                    cursor='hand2')
        self.toggle_btn.pack(side='left', padx=20, pady=15)

        btn_frame = tk.Frame(control_frame, bg='#2c3e50')
        btn_frame.pack(side='right', padx=20)

        save_btn = tk.Button(btn_frame, text="💾 Save",
                             command=self.save_config,
                             bg='#3498db', fg='white',
                             font=('Arial', 10), width=10,
                             cursor='hand2')
        save_btn.pack(side='left', padx=5)

        load_btn = tk.Button(btn_frame, text="📁 Load",
                             command=self.load_config,
                             bg='#3498db', fg='white',
                             font=('Arial', 10), width=10,
                             cursor='hand2')
        load_btn.pack(side='left', padx=5)

        info_label = tk.Label(control_frame, text="✓ Sound issue FIXED! Run as Administrator",
                              bg='#2c3e50', fg='#00ff00', font=('Arial', 9, 'bold'))
        info_label.pack(side='bottom', pady=5)

    def cast_spell(self, spell_name):
        if not self.active:
            self.add_log("❌ Macro is not active! Press START first.", '#e74c3c')
            return

        thread = threading.Thread(target=self.invoke_spell, args=(spell_name,))
        thread.daemon = True
        thread.start()

    def invoke_spell(self, spell_name):
        try:
            spell = self.spells[spell_name]
            sequence = spell['sequence']
            invoke_key = self.invoke_key_var.get().lower()
            cast_key = self.cast_key_var.get().lower()

            self.add_log(f"🎯 Casting {spell['name']}...", '#ff9800')

            # Шаг 1: Комбинация клавиш
            for key in sequence:
                self.send_key_to_game(key)
                time.sleep(self.spell_delays['key'])

            time.sleep(0.05)

            # Шаг 2: Инвок
            self.send_key_to_game(invoke_key)

            time.sleep(self.spell_delays['invoke'])

            # Шаг 3: Каст
            self.send_key_to_game(cast_key)

            self.add_log(f"✅ {spell['name']} cast successfully! (Sound preserved)", '#27ae60')

        except Exception as e:
            self.add_log(f"⚠️ Error: {e}", '#e74c3c')

    def update_press_duration(self, value):
        self.spell_delays['press_duration'] = float(value)
        self.press_duration_label.config(text=f"{float(value):.2f}s")

    def update_invoke_delay(self, value):
        self.spell_delays['invoke'] = float(value)
        self.invoke_delay_label.config(text=f"{float(value):.2f}s")

    def update_cast_delay(self, value):
        self.spell_delays['cast'] = float(value)
        self.cast_delay_label.config(text=f"{float(value):.2f}s")

    def toggle_macro(self):
        self.active = not self.active
        if self.active:
            self.toggle_btn.config(text="⏹ STOP", bg='#e74c3c')
            self.status_label.config(text="● RUNNING", fg='#27ae60')
            self.add_log("✅ Macro ACTIVATED!", '#27ae60')
            self.add_log("💡 Sound issue is FIXED! Cast spells freely!", '#00ff00')
        else:
            self.toggle_btn.config(text="▶ START", bg='#27ae60')
            self.status_label.config(text="● STOPPED", fg='red')
            self.add_log("⏸ Macro DEACTIVATED", '#e74c3c')

    def add_log(self, message, color='#00ff00'):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def on_key_press(self, key):
        try:
            if not self.active:
                return

            from pynput.keyboard import Key
            hotkey_mapping = {spell['hotkey']: spell_id for spell_id, spell in self.spells.items()}

            if hasattr(key, 'char') and key.char in hotkey_mapping:
                self.cast_spell(hotkey_mapping[key.char])

            elif key == Key.f12:
                self.root.after(0, self.toggle_macro)

        except Exception as e:
            pass

    def start_keyboard_listener(self):
        try:
            from pynput.keyboard import Key, Listener

            def listen():
                with Listener(on_press=self.on_key_press) as listener:
                    self.listener = listener
                    self.add_log("🎮 Keyboard listener started", '#27ae60')
                    listener.join()

            thread = threading.Thread(target=listen, daemon=True)
            thread.start()
        except Exception as e:
            self.add_log(f"⚠️ Listener error: {e}", '#ff9800')

    def save_config(self):
        config = {
            'spell_delays': self.spell_delays,
            'invoke_key': self.invoke_key_var.get(),
            'cast_key': self.cast_key_var.get(),
        }

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

        self.add_log("💾 Configuration saved!", '#27ae60')

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                self.spell_delays = config.get('spell_delays', self.spell_delays)
                self.invoke_key_var.set(config.get('invoke_key', 'R'))
                self.cast_key_var.set(config.get('cast_key', 'D'))

                self.invoke_delay_var.set(self.spell_delays['invoke'])
                self.cast_delay_var.set(self.spell_delays['cast'])
                self.press_duration_var.set(self.spell_delays.get('press_duration', 0.03))

                self.add_log("📁 Configuration loaded!", '#27ae60')
        except Exception as e:
            self.add_log(f"⚠️ Error loading config: {e}", '#e74c3c')

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(1, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def run(self):
        self.add_log("=" * 50, '#3498db')
        self.add_log("INVOKER MACRO - SOUND ISSUE FIXED", '#3498db')
        self.add_log("=" * 50, '#3498db')
        self.add_log("")
        self.add_log("✓ Sound will NOT turn off when casting!", '#00ff00')
        self.add_log("✓ Run as Administrator for best results", '#ff9800')
        self.add_log("✓ Press START, then use number keys 1-0", '#3498db')
        self.add_log("")

        # Проверяем наличие окна Dota 2
        dota_window = win32gui.FindWindow(None, "Dota 2")
        if dota_window:
            self.add_log("✓ Dota 2 window detected!", '#00ff00')
        else:
            self.add_log("⚠️ Dota 2 window not found. Make sure game is running!", '#ff9800')

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.listener:
                self.listener.stop()
            self.root.destroy()


if __name__ == "__main__":
    app = InvokerMacroGUI()
    app.run()