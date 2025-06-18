import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
import threading
from chaos_dna_crypto import get_sha256_key, encrypt, decrypt

class ImageCryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNA Chaos Image Encryption/Decryption")
        self.root.configure(bg="#0D0D0D")
        self.root.geometry("1100x700")
        self.root.resizable(False, False)

        # ===== Style Setup =====
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#1E1E1E", foreground="cyan", padding=10, font=("Consolas", 10))
        style.configure("TLabel", background="#0D0D0D", foreground="white", font=("Consolas", 12))

        # ===== Layout Frames =====
        self.left_panel = tk.Frame(root, width=50, bg="#0D0D0D")
        self.left_panel.pack(side="left", fill="y")
        self.right_panel = tk.Frame(root, width=50, bg="#0D0D0D")
        self.right_panel.pack(side="right", fill="y")
        self.center_panel = tk.Frame(root, bg="#0D0D0D")
        self.center_panel.pack(expand=True, fill="both")

        # Decorative Neon Bars
        self.create_glow_bar(self.left_panel)
        self.create_glow_bar(self.right_panel)

        # ===== Buttons and Canvas =====
        self.select_button = ttk.Button(self.center_panel, text="🖼️ Select Image", command=self.select_image)
        self.select_button.pack(pady=10)

        self.canvas = tk.Canvas(self.center_panel, width=900, height=300, bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(pady=10)

        self.progress = ttk.Progressbar(self.center_panel, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=10)

        self.encrypt_button = ttk.Button(self.center_panel, text="🔐 Encrypt", command=self.encrypt_image)
        self.decrypt_button = ttk.Button(self.center_panel, text="🔓 Decrypt", command=self.decrypt_image)
        self.encrypt_button.pack(pady=5)
        self.decrypt_button.pack(pady=5)

        self.fx = self.fy = self.fz = self.key_matrix = None
        self.original_img_np = self.encrypted_img_np = None

    def create_glow_bar(self, parent):
        canvas = tk.Canvas(parent, width=20, height=700, bg="#0D0D0D", highlightthickness=0)
        canvas.pack(pady=10)
        bar = canvas.create_rectangle(8, 0, 12, 100, fill="cyan", outline="")
        self.animate_bar(canvas, bar, 0, 2, 600)

    def animate_bar(self, canvas, bar, y, direction, max_height):
        y += direction
        if y >= max_height or y <= 0:
            direction *= -1
        canvas.coords(bar, 8, y, 12, y + 100)
        canvas.after(20, self.animate_bar, canvas, bar, y, direction, max_height)

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.img = Image.open(file_path).convert("RGB")
            self.original_img_np = np.array(self.img)
            self.show_images(self.img, None, None)
            messagebox.showinfo("Selected", "Image loaded successfully!")

    def show_images(self, orig, enc, dec):
        self.canvas.delete("all")

        imgs = [orig, enc, dec]
        titles = ["Original", "Encrypted", "Decrypted"]
        for idx, im in enumerate(imgs):
            if im is not None:
                im_resized = im.resize((250, 250))
                imtk = ImageTk.PhotoImage(im_resized)
                self.canvas.create_image(150 + idx*300, 150, image=imtk)
                self.canvas.image = imtk  # Keep reference alive
                self.canvas.create_text(150 + idx*300, 280, text=titles[idx], fill="cyan", font=("Consolas", 14))

    def run_progress(self, task):
        self.progress.start()
        thread = threading.Thread(target=task)
        thread.start()
        self.root.after(100, self.check_thread, thread)

    def check_thread(self, thread):
        if thread.is_alive():
            self.root.after(100, self.check_thread, thread)
        else:
            self.progress.stop()

    def encrypt_image(self):
        if self.original_img_np is None:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        def task():
            key = get_sha256_key(self.original_img_np)
            result = encrypt(self.original_img_np, key)
            self.encrypted_img_np, self.fx, self.fy, self.fz, self.key_matrix = result
            Image.fromarray(self.encrypted_img_np).save("encrypted_output.png")
            self.show_images(self.img, Image.fromarray(self.encrypted_img_np), None)
            messagebox.showinfo("Success", "Image encrypted and saved as encrypted_output.png")

        self.run_progress(task)

    def decrypt_image(self):
        if self.encrypted_img_np is None:
            messagebox.showwarning("No Encrypted Image", "Please encrypt an image first.")
            return

        def task():
            decrypted_np = decrypt(self.encrypted_img_np, self.fx, self.fy, self.fz, self.key_matrix)
            Image.fromarray(decrypted_np).save("decrypted_output.png")
            self.show_images(self.img, Image.fromarray(self.encrypted_img_np), Image.fromarray(decrypted_np))
            messagebox.showinfo("Success", "Image decrypted and saved as decrypted_output.png")

        self.run_progress(task)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCryptoApp(root)
    root.mainloop()
