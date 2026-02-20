import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import subprocess
import platform
import os
import threading

# ייבוא מהספרייה המאוחדת — מקור יחיד לקוד
from jigsaw_puzzle_generator import (
    createPuzzlePieces, create_rectangular_pieces,
)


class PuzzleCreatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("יוצר פאזלים")
        self.root.geometry("1200x800")
        self.root.configure(padx=20, pady=20)

        self.root.bind('<Configure>', self.on_window_resize)

        self.image_path = None
        self.preview_image = None
        self.output_preview = None
        self.last_preview_path = None
        self._resize_after_id = None

        self.create_ui()

    def create_ui(self):
        # מסגרת ראשית
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # חלוקה לשני פאנלים - שמאלי וימני
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_panel.pack_propagate(False)

        # מסגרת ימנית עם scrollbar
        right_scroll_frame = ttk.Frame(main_frame)
        right_scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # הוספת scrollbar אנכי
        right_scrollbar = ttk.Scrollbar(right_scroll_frame)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # יצירת Canvas לתוכן הימני
        right_canvas = tk.Canvas(right_scroll_frame)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # חיבור ה-scrollbar ל-canvas
        right_scrollbar.config(command=right_canvas.yview)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        # מסגרת לתוכן בתוך ה-canvas
        right_panel = ttk.Frame(right_canvas)
        right_canvas.create_window((0, 0), window=right_panel, anchor='nw', tags='right_panel')

        # === פאנל שמאלי - הגדרות ===
        settings_frame = ttk.LabelFrame(left_panel, text="הגדרות")
        settings_frame.pack(fill=tk.X, pady=5)

        # כפתור בחירת תמונה
        select_btn = ttk.Button(settings_frame, text="בחר תמונה", command=self.select_image)
        select_btn.pack(pady=5)

        # תצוגה מקדימה של התמונה המקורית
        preview_frame = ttk.Frame(settings_frame)
        preview_frame.pack(pady=5)
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack()

        # תווית מידע על התמונה
        self.image_info_label = ttk.Label(settings_frame, text="")
        self.image_info_label.pack(pady=2)

        # סוג פאזל
        puzzle_type_frame = ttk.Frame(settings_frame)
        puzzle_type_frame.pack(fill=tk.X, pady=5)
        self.puzzle_type = tk.StringVar(value="classic")
        ttk.Radiobutton(puzzle_type_frame, text="פאזל קלאסי",
                         variable=self.puzzle_type, value="classic").pack(anchor=tk.W)
        ttk.Radiobutton(puzzle_type_frame, text="מלבנים פשוטים",
                         variable=self.puzzle_type, value="rectangular").pack(anchor=tk.W)

        # מספר שורות ועמודות
        grid_frame = ttk.Frame(settings_frame)
        grid_frame.pack(fill=tk.X, pady=5)

        ttk.Label(grid_frame, text="מספר שורות:").grid(row=0, column=0, padx=5, pady=5)
        self.rows_var = tk.StringVar(value="4")
        ttk.Entry(grid_frame, textvariable=self.rows_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(grid_frame, text="מספר עמודות:").grid(row=1, column=0, padx=5, pady=5)
        self.cols_var = tk.StringVar(value="6")
        ttk.Entry(grid_frame, textvariable=self.cols_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        # אפשרויות ייצוא
        export_frame = ttk.LabelFrame(left_panel, text="אפשרויות ייצוא")
        export_frame.pack(fill=tk.X, pady=5)

        self.export_format = tk.StringVar(value="png")
        ttk.Radiobutton(export_frame, text="PNG (עם שקיפות)",
                         variable=self.export_format, value="png").pack(anchor=tk.W)
        ttk.Radiobutton(export_frame, text="JPEG (איכות גבוהה)",
                         variable=self.export_format, value="jpeg").pack(anchor=tk.W)

        quality_frame = ttk.Frame(export_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="איכות:").pack(side=tk.LEFT)
        self.export_quality = tk.IntVar(value=95)
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100,
                                  variable=self.export_quality, orient="horizontal",
                                  command=self._update_quality_label)
        quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.quality_value_label = ttk.Label(quality_frame, text="95")
        self.quality_value_label.pack(side=tk.LEFT, padx=(0, 5))

        # בחירת תיקיית פלט
        output_frame = ttk.Frame(left_panel)
        output_frame.pack(fill=tk.X, pady=5)
        self.output_dir = tk.StringVar(value="puzzle_pieces")
        ttk.Label(output_frame, text="תיקיית פלט:").pack(anchor=tk.W)
        dir_entry_frame = ttk.Frame(output_frame)
        dir_entry_frame.pack(fill=tk.X)
        ttk.Entry(dir_entry_frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_entry_frame, text="...", width=3,
                   command=self._choose_output_dir).pack(side=tk.LEFT, padx=2)

        # כפתור יצירה
        self.create_btn = ttk.Button(left_panel, text="צור פאזל", command=self.create_puzzle)
        self.create_btn.pack(pady=10)

        # פס התקדמות
        self.progress = ttk.Progressbar(left_panel, mode='indeterminate')

        # תווית סטטוס
        self.status_label = ttk.Label(left_panel, text="")
        self.status_label.pack(pady=5)

        # כפתור פתיחת תיקייה
        self.open_folder_btn = ttk.Button(left_panel, text="פתח תיקיית פלט",
                                          command=lambda: self.open_output_folder(self.output_dir.get()))

        # === פאנל ימני - תצוגות ===
        preview_frame = ttk.LabelFrame(right_panel, text="תצוגה מקדימה של הפאזל")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.output_label = ttk.Label(preview_frame)
        self.output_label.pack(pady=5)

        # תצוגת החלקים
        pieces_frame = ttk.LabelFrame(right_panel, text="חלקי הפאזל")
        pieces_frame.pack(fill=tk.X, pady=5)

        # Canvas עם scrollbar לחלקים
        canvas_frame = ttk.Frame(pieces_frame)
        canvas_frame.pack(fill=tk.X, pady=5)

        self.pieces_canvas = tk.Canvas(canvas_frame, height=200)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal",
                                  command=self.pieces_canvas.xview)

        self.pieces_canvas.pack(fill=tk.X)
        scrollbar.pack(fill=tk.X)

        self.pieces_canvas.configure(xscrollcommand=scrollbar.set)

        # מסגרת לחלקים
        self.pieces_frame = ttk.Frame(self.pieces_canvas)
        self.canvas_window = self.pieces_canvas.create_window(
            (0, 0),
            window=self.pieces_frame,
            anchor='nw',
            tags='pieces_frame'
        )

        # קישור לשינוי גודל
        self.pieces_frame.bind('<Configure>', self.on_frame_configure)
        self.pieces_canvas.bind('<Configure>', self.on_canvas_configure)
        right_panel.bind('<Configure>', lambda e: self.on_right_panel_configure(e, right_canvas))

    def _update_quality_label(self, value):
        self.quality_value_label.config(text=str(int(float(value))))

    def _choose_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)

    def update_pieces_preview(self):
        """עדכון תצוגה מקדימה של החלקים"""
        for widget in self.pieces_frame.winfo_children():
            widget.destroy()

        pieces_dir = self.output_dir.get()
        if not os.path.exists(pieces_dir):
            return

        piece_files = sorted([f for f in os.listdir(pieces_dir)
                              if f.startswith("piece_") and not f.startswith("piece_outline")])

        grid_frame = ttk.Frame(self.pieces_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        col = 0
        cols_per_row = 8

        for i, piece_file in enumerate(piece_files):
            try:
                piece_path = os.path.join(pieces_dir, piece_file)
                piece_image = Image.open(piece_path)

                piece_image.thumbnail((80, 80))
                photo = ImageTk.PhotoImage(piece_image)

                piece_frame = ttk.Frame(grid_frame)
                piece_frame.grid(row=row, column=col, padx=2, pady=2)

                label = ttk.Label(piece_frame, image=photo)
                label.image = photo
                label.pack()

                ttk.Label(piece_frame, text=f"{i + 1}").pack()

                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1

            except Exception as e:
                print(f"Error loading piece {piece_file}: {str(e)}")

        self.pieces_frame.update_idletasks()
        self.pieces_canvas.configure(scrollregion=self.pieces_canvas.bbox("all"))

    def show_preview(self, image_path, label):
        """הצגת תמונה בתווית עם התאמה אוטומטית"""
        image = Image.open(image_path)

        if label == self.preview_label:
            max_width = 250
            max_height = 150
        else:
            max_width = max(200, self.root.winfo_width() - 400)
            max_height = max(200, int(self.root.winfo_height() * 0.6))

        img_ratio = image.size[0] / image.size[1]

        if image.size[0] > image.size[1]:
            new_width = min(max_width, image.size[0])
            new_height = int(new_width / img_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * img_ratio)
        else:
            new_height = min(max_height, image.size[1])
            new_width = int(new_height * img_ratio)
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / img_ratio)

        new_width = max(1, int(new_width))
        new_height = max(1, int(new_height))

        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)

        if label == self.preview_label:
            self.preview_image = photo
            label.config(image=self.preview_image)
        else:
            self.output_preview = photo
            label.config(image=self.output_preview)

    def select_image(self):
        self.image_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if self.image_path:
            self.show_preview(self.image_path, self.preview_label)
            # הצגת מידע על התמונה
            img = Image.open(self.image_path)
            w, h = img.size
            self.image_info_label.config(text=f"{w}x{h} px")
            self.status_label.config(text=f"נבחרה תמונה: {os.path.basename(self.image_path)}")

    def create_puzzle(self):
        if not self.image_path:
            messagebox.showerror("שגיאה", "נא לבחור תמונה תחילה")
            return

        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())

            if rows < 1 or cols < 1:
                raise ValueError
            if rows > 50 or cols > 50:
                messagebox.showerror("שגיאה", "מספר שורות/עמודות מקסימלי: 50")
                return
        except ValueError:
            messagebox.showerror("שגיאה", "נא להזין מספרים חיוביים בלבד")
            return

        # מעבר למצב "עובד" — פס התקדמות + חסימת כפתור
        self.create_btn.config(state='disabled')
        self.progress.pack(pady=5, fill=tk.X, before=self.status_label)
        self.progress.start(15)
        self.status_label.config(text="יוצר פאזל...")

        # הרצה ב-thread נפרד כדי לא לחסום את הממשק
        thread = threading.Thread(target=self._generate_puzzle, args=(rows, cols), daemon=True)
        thread.start()

    def _generate_puzzle(self, rows, cols):
        """יצירת הפאזל ב-thread נפרד"""
        try:
            output_dir = self.output_dir.get()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_prefix = f"{output_dir}/piece_"

            if self.puzzle_type.get() == "rectangular":
                create_rectangular_pieces(self.image_path, rows, cols, output_prefix)
            else:
                createPuzzlePieces(self.image_path, rows, cols, output_prefix)

            # עדכון UI ב-thread הראשי
            self.root.after(0, self._on_puzzle_complete, output_prefix)

        except Exception as e:
            self.root.after(0, self._on_puzzle_error, str(e))

    def _on_puzzle_complete(self, output_prefix):
        """קולבק לסיום יצירת הפאזל — רץ ב-main thread"""
        self.progress.stop()
        self.progress.pack_forget()
        self.create_btn.config(state='normal')

        preview_path = f"{output_prefix}outline_with_image.png"
        self.last_preview_path = preview_path
        self.show_preview(preview_path, self.output_label)

        self.update_pieces_preview()

        self.status_label.config(text="הפאזל נוצר בהצלחה!")
        self.open_folder_btn.pack(pady=5)

    def _on_puzzle_error(self, error_msg):
        """קולבק לשגיאה ביצירת הפאזל"""
        self.progress.stop()
        self.progress.pack_forget()
        self.create_btn.config(state='normal')
        messagebox.showerror("שגיאה", f"אירעה שגיאה ביצירת הפאזל: {error_msg}")
        self.status_label.config(text="אירעה שגיאה")

    def on_frame_configure(self, event=None):
        self.pieces_canvas.configure(scrollregion=self.pieces_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.pieces_canvas.itemconfig('pieces_frame', width=canvas_width)

    def on_right_panel_configure(self, event, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig('right_panel', width=event.width)

    def on_window_resize(self, event):
        if not hasattr(self, 'last_preview_path') or not self.last_preview_path:
            return
        # debounce — עדכון רק אחרי שהמשתמש סיים לשנות גודל
        if self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(200, self._do_resize_update)

    def _do_resize_update(self):
        self._resize_after_id = None
        if self.last_preview_path:
            self.show_preview(self.last_preview_path, self.output_label)

    def open_output_folder(self, folder_path):
        """פתיחת תיקיית הפלט במערכת ההפעלה"""
        if not os.path.exists(folder_path):
            return
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])


def main():
    root = tk.Tk()
    app = PuzzleCreatorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
