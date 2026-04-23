import csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "restaurants.csv"


class RestaurantFilterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🍽️ 智能餐馆筛选系统")
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        self.setup_window_style()

        self.all_restaurants = self.load_restaurants()
        self.filtered_restaurants = list(self.all_restaurants)
        self.available_tags = self.extract_tags()

        self.search_var = tk.StringVar()
        self.selected_tag_var = tk.StringVar(value="全部类型")
        self.status_var = tk.StringVar()
        self.detail_var = tk.StringVar(value="👈 请从左侧列表选择餐馆查看详情")

        self.build_ui()
        self.refresh_table()

    def extract_tags(self) -> list[str]:
        tags = set()
        for restaurant in self.all_restaurants:
            type_raw = restaurant.get("类型", "").strip()
            if type_raw:
                parts = type_raw.split(";")
                if len(parts) >= 3:
                    tag = parts[2].strip()
                elif len(parts) == 2:
                    tag = parts[1].strip()
                else:
                    tag = parts[0].strip()
                if tag:
                    tags.add(tag)
        return sorted(tags)

    def get_restaurant_tag(self, restaurant: dict) -> str:
        type_raw = restaurant.get("类型", "").strip()
        if type_raw:
            parts = type_raw.split(";")
            if len(parts) >= 3:
                return parts[2].strip()
            elif len(parts) == 2:
                return parts[1].strip()
            else:
                return parts[0].strip()
        return "未知"

    def setup_window_style(self) -> None:
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
                        background='#f5f7fa',
                        foreground='#2c3e50',
                        font=('Microsoft YaHei UI', 20))

        style.configure('TFrame', background='#f5f7fa')
        style.configure('TLabel', background='#f5f7fa', foreground='#2c3e50')
        style.configure('Header.TLabel',
                        background='#f5f7fa',
                        foreground='#1a252f',
                        font=('Microsoft YaHei UI', 20, 'bold'))

        style.configure('Search.TEntry',
                        fieldbackground='white',
                        foreground='#2c3e50',
                        padding=10,
                        font=('Microsoft YaHei UI', 20))

        style.configure('Action.TButton',
                        background='#3498db',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20, 'bold'),
                        padding=(18, 10))
        style.map('Action.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#21618c')],
                  foreground=[('active', 'white')])

        style.configure('Reset.TButton',
                        background='#95a5a6',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20),
                        padding=(18, 10))
        style.map('Reset.TButton',
                  background=[('active', '#7f8c8d'), ('pressed', '#616a6b')],
                  foreground=[('active', 'white')])

        style.configure('Treeview',
                        background='white',
                        foreground='#2c3e50',
                        fieldbackground='white',
                        rowheight=40,
                        font=('Microsoft YaHei UI', 20),
                        borderwidth=0)
        style.configure('Treeview.Heading',
                        background='#34495e',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20, 'bold'),
                        padding=10)
        style.map('Treeview',
                  background=[('selected', '#3498db')],
                  foreground=[('selected', 'white')])

        style.configure('Detail.TLabelframe',
                        background='#ffffff',
                        foreground='#2c3e50',
                        font=('Microsoft YaHei UI', 20, 'bold'))
        style.configure('Detail.TLabelframe.Label',
                        background='#ffffff',
                        foreground='#34495e',
                        font=('Microsoft YaHei UI', 20, 'bold'))

        style.configure('Status.TLabel',
                        background='#ecf0f1',
                        foreground='#7f8c8d',
                        font=('Microsoft YaHei UI', 20))

        self.root.configure(background='#f5f7fa')

        style.configure('TCombobox',
                        fieldbackground='white',
                        foreground='#2c3e50',
                        padding=8,
                        font=('Microsoft YaHei UI', 20))
        style.map('TCombobox',
                  fieldbackground=[('readonly', 'white')],
                  foreground=[('readonly', '#2c3e50')])

        self.root.option_add('*TCombobox*Listbox.font', ('Microsoft YaHei UI', 14))
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#3498db')
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')

        self.root.configure(background='#f5f7fa')

    def load_restaurants(self) -> list[dict[str, str]]:
        if not CSV_FILE.exists():
            messagebox.showerror("❌ 文件不存在", f"未找到数据文件：\n{CSV_FILE}")
            return []

        with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header_frame = ttk.Frame(self.root, padding=(20, 15, 20, 10))
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(header_frame, text="🍽️ 智能餐馆筛选系统",
                                style='Header.TLabel')
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        search_container = ttk.Frame(header_frame)
        search_container.grid(row=1, column=0, sticky="ew")
        search_container.columnconfigure(1, weight=1)

        ttk.Label(search_container, text="🔍 搜索:",
                  style='TLabel').grid(row=0, column=0, padx=(0, 10), sticky="w")

        search_entry = ttk.Entry(search_container, textvariable=self.search_var,
                                 style='Search.TEntry')
        search_entry.grid(row=0, column=1, sticky="ew", ipady=3)
        search_entry.bind("<KeyRelease>", self.on_search)
        search_entry.focus()

        btn_frame = ttk.Frame(search_container)
        btn_frame.grid(row=0, column=2, padx=(12, 0))

        ttk.Button(btn_frame, text="✨ 筛选", command=self.apply_filter,
                   style='Action.TButton').pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🔄 重置", command=self.reset_filter,
                   style='Reset.TButton').pack(side="left")

        filter_frame = ttk.Frame(self.root, padding=(20, 0, 20, 10))
        filter_frame.grid(row=0, column=0, sticky="ew")
        filter_frame.columnconfigure(1, weight=1)


        tag_frame = ttk.Frame(search_container)
        tag_frame.grid(row=0, column=3, padx=(15, 0))

        ttk.Label(tag_frame, text="🏷️ 类型:",
                  style='TLabel').pack(side="left", padx=(0, 8))

        tag_combo = ttk.Combobox(tag_frame, textvariable=self.selected_tag_var,
                                 values=["全部类型"] + self.available_tags,
                                 state="readonly", width=36,
                                 font=('Microsoft YaHei UI', 20))
        tag_combo.pack(side="left")

        tag_combo.bind("<<ComboboxSelected>>", self.on_tag_selected)

        main_frame = ttk.Frame(self.root, padding=(20, 0, 20, 15))
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        table_container = ttk.LabelFrame(main_frame, text="📋 餐馆列表", padding=8)
        table_container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns = ("名称", "地址", "电话", "类型")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.heading("名称", text="🏪 名称", anchor="w")
        self.tree.heading("地址", text="📍 地址", anchor="w")
        self.tree.heading("电话", text="📞 电话", anchor="center")
        self.tree.heading("类型", text="🏷️ 类型", anchor="center")
        self.tree.column("名称", width=200, minwidth=150, anchor="w")
        self.tree.column("地址", width=350, minwidth=280, anchor="w")
        self.tree.column("电话", width=120, minwidth=100, anchor="center")
        self.tree.column("类型", width=130, minwidth=100, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_double_click)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        detail_frame = ttk.LabelFrame(main_frame, text="ℹ️ 详细信息", padding=16,
                                      style='Detail.TLabelframe')
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(0, weight=1)

        detail_text_frame = ttk.Frame(detail_frame)
        detail_text_frame.grid(row=0, column=0, sticky="nsew")
        detail_text_frame.columnconfigure(0, weight=1)

        detail_label = ttk.Label(
            detail_text_frame,
            textvariable=self.detail_var,
            justify="left",
            anchor="nw",
            wraplength=380,
            font=('Microsoft YaHei UI', 20),
            background='white',
            padding=15,
        )
        detail_label.grid(row=0, column=0, sticky="nsew")

        status_bar = ttk.Frame(self.root, padding=(20, 10))
        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.columnconfigure(0, weight=1)

        status_label = ttk.Label(status_bar, textvariable=self.status_var,
                                 style='Status.TLabel')
        status_label.grid(row=0, column=0, sticky="w")

        tip_label = ttk.Label(status_bar, text="💡 提示: 双击可查看详细信息",
                              style='Status.TLabel')
        tip_label.grid(row=0, column=1, sticky="e")

    def on_tag_selected(self, event) -> None:
        self.apply_filter()

    def on_double_click(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.show_detail_dialog(item)

    def show_detail_dialog(self, item_id) -> None:
        row_index = int(item_id)
        if row_index < len(self.filtered_restaurants):
            restaurant = self.filtered_restaurants[row_index]
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"📍 {restaurant.get('名称', '')}")
            detail_window.geometry("500x400")
            detail_window.configure(bg='white')

            tag = self.get_restaurant_tag(restaurant)

            content = "\n".join([
                f"{'=' * 40}",
                f"🏪 名称: {restaurant.get('名称', '')}",
                f"{'=' * 40}",
                f"📍 地址: {restaurant.get('地址', '') or '暂无'}",
                f"📞 电话: {self.normalize_phone(restaurant.get('电话', ''))}",
                f"🏷️ 类型: {tag}",
                f"{'=' * 40}",
                f"🌐 位置信息:",
                f"   经度: {restaurant.get('经度', '') or '暂无'}",
                f"   纬度: {restaurant.get('纬度', '') or '暂无'}",
                f"{'=' * 40}",
                f"🗺️ 所在地区:",
                f"   {restaurant.get('所在省', '')} {restaurant.get('所在市', '')} {restaurant.get('所在区', '')}",
                f"{'=' * 40}",
            ])

            text_widget = tk.Text(detail_window, wrap="word", font=('Microsoft YaHei UI', 20),
                                  bg='white', fg='#2c3e50', bd=0, padx=18, pady=18)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")

            close_btn = ttk.Button(detail_window, text="关闭",
                                   command=detail_window.destroy,
                                   style='Action.TButton')
            close_btn.pack(pady=(0, 15))

    def on_search(self, _event: tk.Event) -> None:
        self.apply_filter()

    def apply_filter(self) -> None:
        keyword = self.search_var.get().strip().lower()
        selected_tag = self.selected_tag_var.get()

        filtered = self.all_restaurants

        if selected_tag and selected_tag != "全部类型":
            filtered = [
                item for item in filtered
                if self.get_restaurant_tag(item) == selected_tag
            ]

        if keyword:
            filtered = [
                item for item in filtered
                if keyword in item.get("名称", "").lower()
            ]

        self.filtered_restaurants = filtered
        self.refresh_table()

    def reset_filter(self) -> None:
        self.search_var.set("")
        self.selected_tag_var.set("全部类型")
        self.filtered_restaurants = list(self.all_restaurants)
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, restaurant in enumerate(self.filtered_restaurants):
            tags = ('evenrow',) if index % 2 == 0 else ('oddrow',)
            tag = self.get_restaurant_tag(restaurant)
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    restaurant.get("名称", ""),
                    restaurant.get("地址", ""),
                    self.normalize_phone(restaurant.get("电话", "")),
                    tag,
                ),
                tags=tags
            )

        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('oddrow', background='#f8f9fa')

        total = len(self.all_restaurants)
        current = len(self.filtered_restaurants)
        self.status_var.set(f"📊 共 {total} 家餐馆 | ✅ 当前显示 {current} 家")

        if current:
            first_id = self.tree.get_children()[0]
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)
            self.on_select()
        else:
            self.detail_var.set(
                "😕 没有找到匹配的餐馆\n\n💡 建议:\n• 尝试其他关键词\n• 更换类型筛选\n• 点击「重置」查看所有餐馆")

    def on_select(self, _event: tk.Event | None = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        row_index = int(selection[0])
        restaurant = self.filtered_restaurants[row_index]
        phone = self.normalize_phone(restaurant.get('电话', ''))
        tag = self.get_restaurant_tag(restaurant)

        info_lines = [
            f"🏪 名称: {restaurant.get('名称', '')}",
            f"",
            f"📍 地址: {restaurant.get('地址', '') or '暂无'}",
            f"",
            f"📞 电话: {phone}",
            f"",
            f"🏷️ 类型: {tag}",
            f"",
            f"🌐 坐标:",
            f"   经度: {restaurant.get('经度', '') or '暂无'}",
            f"   纬度: {restaurant.get('纬度', '') or '暂无'}",
            f"",
            f"🗺️ 地区:",
            f"   {restaurant.get('所在省', '')} {restaurant.get('所在市', '')} {restaurant.get('所在区', '')}",
        ]

        if phone and phone != "暂无":
            info_lines.extend([
                f"",
                f"━━━━━━━━━━━━━━━━━━━━",
                f"💡 点击号码可直接拨打",
            ])

        self.detail_var.set("\n".join(info_lines))

    @staticmethod
    def normalize_phone(phone: str) -> str:
        cleaned = phone.strip()
        return "暂无" if not cleaned or cleaned == "[]" else cleaned


def main() -> None:
    root = tk.Tk()

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = RestaurantFilterApp(root)
    if not app.all_restaurants:
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()

