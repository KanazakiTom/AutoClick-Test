import customtkinter as ctk
import threading
import time
import json
import os
from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
from pynput.keyboard import Key, Controller as KeyboardController, Listener as KeyboardListener

class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.running = False
        self.stop_event = threading.Event()
        
        settings = self.load_settings()
        self.hotkey = settings.get("hotkey", "`")
        self.tap_key = settings.get("tap_key", "space")

        self.title("Stopped - Auto Clicker (Python)")
        self.attributes('-topmost', True)
        self.geometry("600x550")
        self.resizable(False, False)

        self._build_ui()
        
        self.listener = KeyboardListener(on_press=self.on_global_hotkey)
        self.listener.start()

    def load_settings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump({"hotkey": self.hotkey, "tap_key": self.tap_key}, f)

    def only_int(self, P):
        return P == "" or (P.isdigit() and int(P) >= 0)

    def _build_ui(self):
        ctk.set_appearance_mode("light")
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)
        vcmd = (self.register(self.only_int), '%P')

        # --- 1. Interval ---
        int_f = ctk.CTkFrame(main_frame, border_width=1, border_color="#cccccc")
        int_f.pack(fill='x', pady=5)
        ctk.CTkLabel(int_f, text="Click interval", font=("Segoe UI", 11, "bold")).pack(anchor='w', padx=10, pady=5)
        row1 = ctk.CTkFrame(int_f); row1.pack(padx=10, pady=5)
        self.hours = self._entry(row1, "0", vcmd); ctk.CTkLabel(row1, text="hours").pack(side='left', padx=(2,10))
        self.mins = self._entry(row1, "0", vcmd); ctk.CTkLabel(row1, text="mins").pack(side='left', padx=(2,10))
        self.secs = self._entry(row1, "0", vcmd); ctk.CTkLabel(row1, text="secs").pack(side='left', padx=(2,10))
        self.ms = self._entry(row1, "24", vcmd, 70); ctk.CTkLabel(row1, text="ms").pack(side='left', padx=2)

        # --- 2. Action Options ---
        opt_f = ctk.CTkFrame(main_frame, border_width=1, border_color="#cccccc")
        opt_f.pack(fill='x', pady=5)
        ctk.CTkLabel(opt_f, text="Action options", font=("Segoe UI", 11, "bold")).pack(anchor='w', padx=10, pady=5)
        self.action_var = ctk.StringVar(value="Mouse")
        m_row = ctk.CTkFrame(opt_f); m_row.pack(padx=10, fill='x')
        ctk.CTkRadioButton(m_row, text="Mouse button:", variable=self.action_var, value="Mouse", command=self._update_ui_states).pack(side='left')
        self.mouse_btn = ctk.CTkOptionMenu(m_row, values=["Left", "Right", "Middle"], width=90); self.mouse_btn.set("Left"); self.mouse_btn.pack(side='left', padx=10)
        self.click_type = ctk.CTkOptionMenu(m_row, values=["Single", "Double"], width=90); self.click_type.set("Single"); self.click_type.pack(side='left')
        k_row = ctk.CTkFrame(opt_f); k_row.pack(padx=10, pady=5, fill='x')
        ctk.CTkRadioButton(k_row, text="Keyboard button:", variable=self.action_var, value="Keyboard", command=self._update_ui_states).pack(side='left')
        self.kb_tap_btn = ctk.CTkButton(k_row, text=self.tap_key.upper(), width=100, command=self.change_tap_key)
        self.kb_tap_btn.pack(side='left', padx=10)

        # --- 3. Repeat ---
        rep_f = ctk.CTkFrame(main_frame, border_width=1, border_color="#cccccc")
        rep_f.pack(fill='x', pady=5)
        ctk.CTkLabel(rep_f, text="Action repeat", font=("Segoe UI", 11, "bold")).pack(anchor='w', padx=10, pady=5)
        self.rep_var = ctk.StringVar(value="until_stopped")
        rep_row = ctk.CTkFrame(rep_f); rep_row.pack(padx=10, pady=5, fill='x')
        ctk.CTkRadioButton(rep_row, text="Repeat", variable=self.rep_var, value="times", command=self._update_ui_states).pack(side='left')
        self.rep_times = ctk.CTkEntry(rep_row, width=60, validate='key', validatecommand=vcmd); self.rep_times.insert(0, "1"); self.rep_times.pack(side='left', padx=10)
        ctk.CTkRadioButton(rep_row, text="Repeat until stopped", variable=self.rep_var, value="until_stopped", command=self._update_ui_states).pack(side='left')

        # --- 4. Position ---
        self.pos_frame = ctk.CTkFrame(main_frame, border_width=1, border_color="#cccccc")
        self.pos_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(self.pos_frame, text="Cursor position", font=("Segoe UI", 11, "bold")).pack(anchor='w', padx=10, pady=5)
        self.pos_var = ctk.StringVar(value="current")
        p_row = ctk.CTkFrame(self.pos_frame); p_row.pack(padx=10, pady=5, fill='x')
        self.p1 = ctk.CTkRadioButton(p_row, text="Current location", variable=self.pos_var, value="current"); self.p1.pack(side='left')
        self.p2 = ctk.CTkRadioButton(p_row, text="Pick location", variable=self.pos_var, value="pick"); self.p2.pack(side='left', padx=10)
        self.x_ent = self._entry(p_row, "0", vcmd); self.y_ent = self._entry(p_row, "0", vcmd); self.y_ent.pack(side='left', padx=5)
        self.pick_btn = ctk.CTkButton(p_row, text="Pick location", width=110, command=self.pick_location); self.pick_btn.pack(side='left')

        # --- 5. Controls ---
        ctrl_f = ctk.CTkFrame(main_frame); ctrl_f.pack(pady=10)
        self.start_btn = ctk.CTkButton(ctrl_f, text=f"Start ({self.hotkey.upper()})", command=self.toggle_process)
        self.stop_btn = ctk.CTkButton(ctrl_f, text=f"Stop ({self.hotkey.upper()})", command=self.toggle_process, state="disabled")
        self.start_btn.pack(side='left', padx=5); self.stop_btn.pack(side='left', padx=5)
        ctk.CTkButton(ctrl_f, text="Hotkey setting", command=self.change_hotkey_setting).pack(side='left', padx=5)

        # --- 6. Status Notation (RESTORED) ---
        self.status_lbl = ctk.CTkLabel(main_frame, text="Status: Idle", font=("Segoe UI", 11))
        self.status_lbl.pack(pady=(10, 0))
        
        self.cps_lbl = ctk.CTkLabel(main_frame, text="CPS: 0.0", font=("Segoe UI", 16, "bold"), text_color="#001f3f")
        self.cps_lbl.pack(pady=5)
        
        self.hk_notation_lbl = ctk.CTkLabel(main_frame, text=f"Hotkey: {self.hotkey.upper()}", font=("Segoe UI", 14), text_color="#003366")
        self.hk_notation_lbl.pack()

        self._update_ui_states()

    def _entry(self, p, d, v, w=50):
        e = ctk.CTkEntry(p, width=w, validate='key', validatecommand=v); e.insert(0, d); e.pack(side='left'); return e

    def _update_ui_states(self):
        is_kb = self.action_var.get() == "Keyboard"
        self.cps_lbl.configure(text="TPS: 0.0" if is_kb else "CPS: 0.0")
        p_state = "disabled" if is_kb else "normal"
        self.pos_frame.configure(fg_color="#f0f0f0" if is_kb else "transparent")
        for w in [self.p1, self.p2, self.x_ent, self.y_ent, self.pick_btn]: w.configure(state=p_state)
        self.rep_times.configure(state="normal" if self.rep_var.get() == "times" else "disabled")

    def toggle_process(self):
        if self.running:
            self.running = False
            self.stop_event.set()
            self.title("Stopped - Auto Clicker (Python)")
            self.status_lbl.configure(text="Status: Idle")
            self.start_btn.configure(state="normal"); self.stop_btn.configure(state="disabled")
        else:
            self.running = True
            self.stop_event.clear()
            mode = self.action_var.get()
            self.title("Clicking..." if mode == "Mouse" else "Tapping...")
            self.status_lbl.configure(text=f"Status: {mode} Active")
            self.start_btn.configure(state="disabled"); self.stop_btn.configure(state="normal")
            threading.Thread(target=self.main_loop, daemon=True).start()

    def main_loop(self):
        m_ctrl = MouseController(); k_ctrl = KeyboardController()
        delay = (int(self.hours.get() or 0)*3600 + int(self.mins.get() or 0)*60 + int(self.secs.get() or 0) + int(self.ms.get() or 0)/1000.0)
        max_rep = float('inf') if self.rep_var.get() == "until_stopped" else int(self.rep_times.get() or 1)
        count = 0
        start_t = time.time()

        while self.running and count < max_rep:
            if self.action_var.get() == "Mouse":
                if self.pos_var.get() == "pick": m_ctrl.position = (int(self.x_ent.get()), int(self.y_ent.get()))
                btn = getattr(Button, self.mouse_btn.get().lower())
                m_ctrl.click(btn, 2 if self.click_type.get() == "Double" else 1)
            else:
                key = self.tap_key.lower()
                if len(key) > 1: key = getattr(Key, key, key)
                k_ctrl.press(key); k_ctrl.release(key)
            
            count += 1
            elapsed = time.time() - start_t
            if elapsed > 0.5:
                rate = round(count / elapsed, 1)
                prefix = "TPS" if self.action_var.get() == "Keyboard" else "CPS"
                self.cps_lbl.configure(text=f"{prefix}: {rate}")

            if self.stop_event.wait(timeout=max(0.001, delay)): break
        
        self.after(0, self._auto_stop)

    def _auto_stop(self):
        if self.running: self.toggle_process()

    def on_global_hotkey(self, key):
        k = str(key).replace("'", "").replace("Key.", "").lower()
        if k == self.hotkey.lower(): self.after(0, self.toggle_process)

    # --- SETTINGS WINDOWS (RESTORED UI WITH AUTO-FOCUS) ---
    def _open_setting_dialog(self, title, label_text, current_key, save_callback):
        self.attributes('-topmost', False) 
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("400x220")
        win.resizable(False, False)
        win.attributes('-topmost', True)
        win.focus_force() 
        win.grab_set() 

        self.temp_key = current_key

        ctk.CTkLabel(win, text=title, font=("Segoe UI", 18, "bold")).pack(pady=(20, 10))
        
        bg_frame = ctk.CTkFrame(win, fg_color="#e0e0e0", corner_radius=10)
        bg_frame.pack(pady=10, padx=40, fill='x')
        
        ctk.CTkLabel(bg_frame, text=label_text, font=("Segoe UI", 14)).pack(side='left', padx=(20, 10), pady=10)
        
        # Changed to show a "listening" state visually
        key_box = ctk.CTkLabel(bg_frame, text=current_key.upper(), font=("Segoe UI", 14, "bold"), 
                               fg_color="#d1e8ff", width=100, height=35, corner_radius=5,
                               text_color="#0078d7")
        key_box.pack(side='left', padx=10, pady=10)

        # The listener now starts IMMEDIATELY
        def _on_press(key):
            new_k = str(key).replace("'", "").replace("Key.", "").lower()
            # Allow user to see what they pressed before hitting OK
            self.temp_key = new_k
            key_box.configure(text=self.temp_key.upper())
            return False # Stops the listener after one key is caught

        listener_thread = KeyboardListener(on_press=_on_press)
        listener_thread.start()

        def handle_ok(event=None):
            if listener_thread.running:
                listener_thread.stop()
            save_callback(self.temp_key)
            win.destroy()
            self.attributes('-topmost', True)

        def handle_cancel(event=None):
            if listener_thread.running:
                listener_thread.stop()
            win.destroy()
            self.attributes('-topmost', True)

        # Bind Physical Keys for convenience
        win.bind("<Return>", handle_ok)
        win.bind("<Escape>", handle_cancel)

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=20)
        
        ctk.CTkButton(btn_row, text="Ok", width=120, command=handle_ok).pack(side='left', padx=10)
        ctk.CTkButton(btn_row, text="Cancel", width=120, fg_color="#5a9bd5", command=handle_cancel).pack(side='left', padx=10)

    def change_tap_key(self):
        self._open_setting_dialog("Keyboard Setting", "Tap Key", self.tap_key, self._set_tap)

    def change_hotkey_setting(self):
        self._open_setting_dialog("Hotkey Setting", "Start / Stop", self.hotkey, self._set_hk)

    def _set_tap(self, k): 
        self.tap_key = k; self.kb_tap_btn.configure(text=k.upper()); self.save_settings()
        
    def _set_hk(self, k): 
        self.hotkey = k
        self.start_btn.configure(text=f"Start ({k.upper()})")
        self.stop_btn.configure(text=f"Stop ({k.upper()})")
        self.hk_notation_lbl.configure(text=f"Hotkey: {k.upper()}")
        self.save_settings(); self.restart_listener()

    def restart_listener(self):
        self.listener.stop(); self.listener = KeyboardListener(on_press=self.on_global_hotkey); self.listener.start()

    def pick_location(self):
        self.iconify()
        def _c(x,y,b,p):
            if p:
                self.x_ent.delete(0,'end'); self.x_ent.insert(0,str(int(x)))
                self.y_ent.delete(0,'end'); self.y_ent.insert(0,str(int(y)))
                self.after(0, self.deiconify); return False
        MouseListener(on_click=_c).start()

if __name__ == "__main__":
    AutoClickerApp().mainloop()