# assistant_gui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import psutil
import ollama

MODEL_NAME = "qwen2.5-coder:1.5b"

SYSTEM_DIRECTIVE = """You are a high-tier AI engineer and systems assistant.
Persona Guidelines:
- Address the operator directly, sharply, and candidly.
- Specialize in Data Structures & Algorithms, full-stack architectures, performance optimization, and systems debugging.
- Output clean, production-ready code with concise, punchy technical rationale.
- Avoid generic corporate filler, apologies, or redundant pleasantries."""

class CyberWorkspace:
    def __init__(self, root):
        self.root = root
        self.root.title(f"POCKET COPILOT [{MODEL_NAME}]")
        self.root.geometry("1080x740")
        self.root.minsize(950, 600)
        self.root.configure(bg="#08090c")

        # Graceful cleanup hook for the window 'X' button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.messages = [{"role": "system", "content": SYSTEM_DIRECTIVE}]
        self.stop_stream_flag = threading.Event()
        self.telemetry_active = True

        # ================= TOP APP BAR =================
        top_bar = tk.Frame(root, bg="#0d1117", height=52, relief="flat")
        top_bar.pack(fill="x", side="top")

        left_brand = tk.Frame(top_bar, bg="#0d1117")
        left_brand.pack(side="left", padx=20, pady=10)

        tk.Label(
            left_brand, text="◆ POCKET COPILOT // TERMINAL CORE", 
            font=("Consolas", 11, "bold"), fg="#00e5ff", bg="#0d1117"
        ).pack(side="left")

        self.engine_tag = tk.Label(
            left_brand, text=f" [NODE: {MODEL_NAME}]", 
            font=("Consolas", 9), fg="#00ff66", bg="#0d1117"
        )
        self.engine_tag.pack(side="left", padx=(10, 0))

        btn_purge = tk.Button(
            top_bar, text="FLUSH CONTEXT", font=("Consolas", 8, "bold"),
            command=self.clear_chat, bg="#161b22", fg="#ff4444",
            activebackground="#21262d", activeforeground="#ff6666",
            relief="solid", bd=1, padx=12, pady=4, cursor="hand2"
        )
        btn_purge.pack(side="right", padx=20, pady=10)

        tk.Frame(root, bg="#1b1f27", height=1).pack(fill="x")

        # ================= MAIN BODY SPLIT =================
        main_body = tk.Frame(root, bg="#08090c")
        main_body.pack(fill="both", expand=True)

        # ---------------- LEFT SIDEBAR ----------------
        sidebar = tk.Frame(main_body, bg="#0c0e14", width=250, bd=1, relief="solid")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="// HARDWARE BUS", 
            font=("Consolas", 8, "bold"), fg="#484f58", bg="#0c0e14"
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.lbl_cpu = tk.Label(sidebar, text="CPU: --%", font=("Consolas", 9), fg="#8b949e", bg="#0c0e14")
        self.lbl_cpu.pack(anchor="w", padx=16, pady=2)

        self.lbl_ram = tk.Label(sidebar, text="RAM: --%", font=("Consolas", 9), fg="#8b949e", bg="#0c0e14")
        self.lbl_ram.pack(anchor="w", padx=16, pady=2)

        self.lbl_bat = tk.Label(sidebar, text="PWR: --%", font=("Consolas", 9), fg="#8b949e", bg="#0c0e14")
        self.lbl_bat.pack(anchor="w", padx=16, pady=2)

        tk.Frame(sidebar, bg="#1b1f27", height=1).pack(fill="x", padx=16, pady=16)

        tk.Label(
            sidebar, text="// WORKFLOW MODULES", 
            font=("Consolas", 8, "bold"), fg="#484f58", bg="#0c0e14"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        workflows = [
            ("DSA Complexity Check", "Analyze the time and space complexity of the following code and suggest algorithmic optimizations:"),
            ("FastAPI Route Boilerplate", "Generate a clean, modular FastAPI router boilerplate with validation and error handling:"),
            ("Bug Diagnosis", "Inspect this code segment for logic errors, edge cases, and memory leaks:"),
            ("React/Next.js Hook", "Write a clean, reusable custom TypeScript React hook for this use case:")
        ]

        for label, prompt_prefix in workflows:
            btn = tk.Button(
                sidebar, text=f"› {label}", font=("Consolas", 8),
                bg="#12151c", fg="#58a6ff", activebackground="#1f242c", activeforeground="#79c0ff",
                relief="flat", anchor="w", cursor="hand2", padx=8, pady=6,
                command=lambda p=prompt_prefix: self.inject_prompt(p)
            )
            btn.pack(fill="x", padx=14, pady=3)

        # ---------------- RIGHT WORKSPACE ----------------
        chat_pane = tk.Frame(main_body, bg="#08090c")
        chat_pane.pack(side="right", fill="both", expand=True)

        self.display = scrolledtext.ScrolledText(
            chat_pane, wrap=tk.WORD, font=("Consolas", 10),
            bg="#08090c", fg="#c9d1d9", insertbackground="#00e5ff",
            bd=0, padx=24, pady=20, highlightthickness=0
        )
        self.display.pack(fill="both", expand=True)
        self.display.config(state="disabled")

        self.display.tag_config("user_tag", foreground="#00e5ff", font=("Consolas", 10, "bold"))
        self.display.tag_config("user_body", foreground="#ffffff", font=("Consolas", 10))
        self.display.tag_config("ai_tag", foreground="#39d353", font=("Consolas", 10, "bold"))
        self.display.tag_config("ai_body", foreground="#c9d1d9", font=("Consolas", 10))
        self.display.tag_config("sys_note", foreground="#484f58", font=("Consolas", 9, "italic"))
        self.display.tag_config("abort_note", foreground="#ff4444", font=("Consolas", 9, "bold"))
        self.display.tag_config("div", foreground="#161b22")

        # ---------------- INPUT DOCK ----------------
        tk.Frame(chat_pane, bg="#1b1f27", height=1).pack(fill="x")

        dock = tk.Frame(chat_pane, bg="#0d1117", padx=16, pady=14)
        dock.pack(fill="x", side="bottom")

        self.input_box = tk.Text(
            dock, height=3, font=("Consolas", 10),
            bg="#161b22", fg="#f0f6fc", insertbackground="#00e5ff",
            bd=1, relief="solid", highlightthickness=0, padx=10, pady=8
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.input_box.bind("<Return>", self.handle_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)
        self.input_box.focus()

        # Action Buttons Dock (Transmit + Abort)
        btn_container = tk.Frame(dock, bg="#0d1117")
        btn_container.pack(side="right", fill="y")

        self.send_btn = tk.Button(
            btn_container, text="TRANSMIT\n[ENTER]", font=("Consolas", 8, "bold"),
            bg="#238636", fg="#ffffff", activebackground="#2ea043", activeforeground="#ffffff",
            relief="flat", width=12, cursor="hand2", command=self.dispatch_message
        )
        self.send_btn.pack(side="top", fill="both", expand=True, pady=(0, 4))

        self.stop_btn = tk.Button(
            btn_container, text="■ ABORT", font=("Consolas", 8, "bold"),
            bg="#21262d", fg="#6e7681", activebackground="#da3633", activeforeground="#ffffff",
            relief="flat", width=12, state="disabled", cursor="hand2", command=self.abort_generation
        )
        self.stop_btn.pack(side="bottom", fill="x")

        self.print_log("sys_note", f"[POCKET COPILOT ONLINE]: Operator verified. Neural bus synchronized with {MODEL_NAME}.\n")

        # Daemon telemetry thread
        threading.Thread(target=self.poll_telemetry, daemon=True).start()

    def on_close(self):
        """Terminates active threads and prevents zombie processes."""
        self.telemetry_active = False
        self.stop_stream_flag.set()
        self.root.destroy()

    def inject_prompt(self, template):
        self.input_box.delete("1.0", tk.END)
        self.input_box.insert(tk.END, template + " ")
        self.input_box.focus()

    def print_log(self, tag, text):
        self.display.config(state="normal")
        self.display.insert(tk.END, text, tag)
        self.display.see(tk.END)
        self.display.config(state="disabled")

    def append_user_message(self, content):
        self.display.config(state="normal")
        div_bar = "—" * 65 + "\n"
        self.display.insert(tk.END, div_bar, "div")
        self.display.insert(tk.END, "▲ OPERATOR\n", "user_tag")
        self.display.insert(tk.END, f"{content}\n\n", "user_body")
        self.display.see(tk.END)
        self.display.config(state="disabled")

    def start_ai_stream(self):
        self.display.config(state="normal")
        div_bar = "—" * 65 + "\n"
        self.display.insert(tk.END, div_bar, "div")
        self.display.insert(tk.END, f"▼ NEURAL AGENT // {MODEL_NAME}\n", "ai_tag")
        self.display.see(tk.END)
        self.display.config(state="disabled")

    def append_stream_token(self, token):
        self.display.config(state="normal")
        self.display.insert(tk.END, token, "ai_body")
        self.display.see(tk.END)
        self.display.config(state="disabled")

    def finish_ai_stream(self, was_aborted=False):
        self.display.config(state="normal")
        if was_aborted:
            self.display.insert(tk.END, "\n[STREAM ABORTED BY OPERATOR]\n\n", "abort_note")
        else:
            self.display.insert(tk.END, "\n\n")
        self.display.see(tk.END)
        self.display.config(state="disabled")

    def handle_enter(self, event):
        if not event.state & 0x1:
            self.dispatch_message()
            return "break"

    def clear_chat(self):
        self.messages = [self.messages[0]]
        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)
        self.display.config(state="disabled")
        self.print_log("sys_note", "[SYSTEM]: Local buffer flushed. Ready.\n")

    def abort_generation(self):
        self.stop_stream_flag.set()
        self.stop_btn.config(state="disabled", text="ABORTING...", bg="#21262d", fg="#6e7681")

    def dispatch_message(self):
        content = self.input_box.get("1.0", tk.END).strip()
        if not content:
            return

        self.input_box.delete("1.0", tk.END)
        self.append_user_message(content)
        self.messages.append({"role": "user", "content": content})

        self.stop_stream_flag.clear()
        self.send_btn.config(state="disabled", text="STREAMING...", bg="#21262d")
        self.stop_btn.config(state="normal", text="■ ABORT", bg="#da3633", fg="#ffffff")
        
        threading.Thread(target=self.infer_stream_thread, daemon=True).start()

    def infer_stream_thread(self):
        full_response = ""
        aborted = False
        try:
            self.root.after(0, self.start_ai_stream)

            response_stream = ollama.chat(
                model=MODEL_NAME,
                messages=self.messages,
                options={
                    "temperature": 0.3,
                    "num_ctx": 2048,
                },
                keep_alive="5m",
                stream=True
            )

            for chunk in response_stream:
                if self.stop_stream_flag.is_set():
                    aborted = True
                    break

                token = chunk.get("message", {}).get("content", "")
                if token:
                    full_response += token
                    self.root.after(0, lambda t=token: self.append_stream_token(t))

            if full_response.strip():
                self.messages.append({"role": "assistant", "content": full_response})
            
            self.root.after(0, lambda: self.finish_ai_stream(was_aborted=aborted))

        except Exception as e:
            err = f"Stream pipeline fault: {e}"
            self.root.after(0, lambda: self.print_log("sys_note", f"\n[FAULT]: {err}\n"))
        finally:
            def reset_buttons():
                self.send_btn.config(state="normal", text="TRANSMIT\n[ENTER]", bg="#238636")
                self.stop_btn.config(state="disabled", text="■ ABORT", bg="#21262d", fg="#6e7681")
            self.root.after(0, reset_buttons)

    def poll_telemetry(self):
        while self.telemetry_active:
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                bat = psutil.sensors_battery()
                pct = f"{bat.percent:.0f}%" if bat else "AC"
                plugged = " [AC]" if (bat and bat.power_plugged) else " [BAT]"

                def update_labels():
                    if not self.telemetry_active:
                        return
                    self.lbl_cpu.config(text=f"CPU: {cpu:>4.1f}%")
                    self.lbl_ram.config(text=f"RAM: {ram:>4.1f}%")
                    self.lbl_bat.config(text=f"PWR: {pct}{plugged}")

                self.root.after(0, update_labels)
            except Exception:
                pass
            time.sleep(1.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = CyberWorkspace(root)
    root.mainloop()