import csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "all_restaurants_combined.csv"
TAG_CANDIDATES = ("tag", "tags", "category")


def parse_rating(value: str) -> float:
    cleaned = (value or "").replace("星", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_review_count(value: str) -> int:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return int(digits) if digits else 0


class RestaurantAdvancedFilterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🍽️ 餐馆搜索与标签筛选")
        self.root.geometry("1180x700")
        self.root.minsize(940, 560)

        self.setup_window_style()

        self.all_restaurants = self.load_restaurants()
        self.tag_column = self.detect_tag_column()
        self.filtered_restaurants = list(self.all_restaurants)

        self.search_var = tk.StringVar()
        self.tag_var = tk.StringVar(value="全部")
        self.sort_var = tk.StringVar(value="评论数从高到低")
        self.status_var = tk.StringVar()
        self.detail_var = tk.StringVar(value="👈 请从左侧列表选择餐馆查看详情")

        self.build_ui()
        self.refresh_table()

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
                        padding=8,
                        font=('Microsoft YaHei UI', 20))

        style.configure('Action.TButton',
                        background='#3498db',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20, 'bold'),
                        padding=(15, 8))
        style.map('Action.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#21618c')],
                  foreground=[('active', 'white')])

        style.configure('Reset.TButton',
                        background='#95a5a6',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20),
                        padding=(15, 8))
        style.map('Reset.TButton',
                  background=[('active', '#7f8c8d'), ('pressed', '#616a6b')],
                  foreground=[('active', 'white')])

        style.configure('Treeview',
                        background='white',
                        foreground='#2c3e50',
                        fieldbackground='white',
                        rowheight=32,
                        font=('Microsoft YaHei UI', 20),
                        borderwidth=0)
        style.configure('Treeview.Heading',
                        background='#34495e',
                        foreground='white',
                        font=('Microsoft YaHei UI', 20, 'bold'),
                        padding=8)
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
                        padding=6,
                        font=('Microsoft YaHei UI', 20))
        style.map('TCombobox',
                  fieldbackground=[('readonly', 'white')],
                  foreground=[('readonly', '#2c3e50')])

        self.root.option_add('*TCombobox*Listbox.font', ('Microsoft YaHei UI', 20))
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

    def detect_tag_column(self) -> str | None:
        if not self.all_restaurants:
            return None

        columns = self.all_restaurants[0].keys()
        for column in TAG_CANDIDATES:
            if column in columns:
                return column
        return None

    def get_tag_options(self) -> list[str]:
        if not self.tag_column:
            return ["全部"]

        tags = {
            (row.get(self.tag_column, "") or "").strip()
            for row in self.all_restaurants
            if (row.get(self.tag_column, "") or "").strip()
        }
        return ["全部", *sorted(tags)]

    def build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header_frame = ttk.Frame(self.root, padding=(20, 15, 20, 10))
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(header_frame, text="🍽️ 餐馆搜索与标签筛选",
                                style='Header.TLabel')
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        search_container = ttk.Frame(header_frame)
        search_container.grid(row=1, column=0, sticky="ew")
        search_container.columnconfigure(1, weight=1)

        ttk.Label(search_container, text="🔍 搜索:",
                  style='TLabel').grid(row=0, column=0, padx=(0, 10), sticky="w")

        search_entry = ttk.Entry(search_container, textvariable=self.search_var,
                                 style='Search.TEntry')
        search_entry.grid(row=0, column=1, sticky="ew", ipady=2)
        search_entry.bind("<KeyRelease>", self.on_filters_changed)
        search_entry.focus()

        btn_frame = ttk.Frame(search_container)
        btn_frame.grid(row=0, column=4, padx=(12, 0))

        ttk.Button(btn_frame, text="✨ 应用", command=self.apply_filters,
                   style='Action.TButton').pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🔄 重置", command=self.reset_filters,
                   style='Reset.TButton').pack(side="left")

        filter_frame = ttk.Frame(self.root, padding=(20, 0, 20, 10))
        filter_frame.grid(row=0, column=0, sticky="ew")
        filter_frame.columnconfigure(1, weight=1)

        tag_label = "Tag：" if self.tag_column and self.tag_column.lower().startswith("tag") else "分类："
        tag_frame = ttk.Frame(search_container)
        tag_frame.grid(row=0, column=2, padx=(15, 0))

        ttk.Label(tag_frame, text=f"🏷️ {tag_label}",
                  style='TLabel').pack(side="left", padx=(0, 8))

        self.tag_combo = ttk.Combobox(tag_frame, textvariable=self.tag_var,
                                      values=self.get_tag_options(),
                                      state="readonly", width=20,
                                      font=('Microsoft YaHei UI', 20))
        self.tag_combo.pack(side="left")
        self.tag_combo.bind("<<ComboboxSelected>>", self.on_filters_changed)

        sort_frame = ttk.Frame(search_container)
        sort_frame.grid(row=0, column=3, padx=(15, 0))

        ttk.Label(sort_frame, text="📊 排序:",
                  style='TLabel').pack(side="left", padx=(0, 8))

        self.sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                       values=[
                                           "评论数从高到低",
                                           "评论数从低到高",
                                           "评分从高到低",
                                           "评分从低到高",
                                       ],
                                       state="readonly", width=18,
                                       font=('Microsoft YaHei UI', 20))
        self.sort_combo.pack(side="left")
        self.sort_combo.bind("<<ComboboxSelected>>", self.on_filters_changed)

        main_frame = ttk.Frame(self.root, padding=(20, 0, 20, 15))
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=4)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        table_container = ttk.LabelFrame(main_frame, text="📋 餐馆列表", padding=8)
        table_container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns = ("name", "tag", "rating", "review_count", "avg_price", "area")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.heading("name", text="🏪 名称", anchor="w")
        self.tree.heading("tag", text="🏷️ 标签/分类", anchor="center")
        self.tree.heading("rating", text="⭐ 评分", anchor="center")
        self.tree.heading("review_count", text="💬 评论数", anchor="center")
        self.tree.heading("avg_price", text="💰 人均", anchor="center")
        self.tree.heading("area", text="📍 区域", anchor="center")
        self.tree.column("name", width=240, minwidth=180, anchor="w")
        self.tree.column("tag", width=130, minwidth=100, anchor="center")
        self.tree.column("rating", width=80, minwidth=70, anchor="center")
        self.tree.column("review_count", width=100, minwidth=90, anchor="center")
        self.tree.column("avg_price", width=80, minwidth=70, anchor="center")
        self.tree.column("area", width=130, minwidth=100, anchor="center")
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
            wraplength=360,
            font=('Microsoft YaHei UI', 20),
            background='white',
            padding=12,
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

    def on_filters_changed(self, _event: tk.Event | None = None) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        keyword = self.search_var.get().strip().lower()
        selected_tag = self.tag_var.get().strip()

        filtered = []
        for item in self.all_restaurants:
            name = (item.get("name", "") or "").strip()
            tag_value = (item.get(self.tag_column, "") or "").strip() if self.tag_column else ""

            if keyword and keyword not in name.lower():
                continue
            if selected_tag and selected_tag != "全部" and tag_value != selected_tag:
                continue
            filtered.append(item)

        self.filtered_restaurants = self.sort_restaurants(filtered)
        self.refresh_table()

    def sort_restaurants(self, restaurants: list[dict[str, str]]) -> list[dict[str, str]]:
        sort_mode = self.sort_var.get()

        if sort_mode == "评论数从低到高":
            return sorted(restaurants, key=lambda item: parse_review_count(item.get("review_count", "")))
        if sort_mode == "评分从高到低":
            return sorted(restaurants, key=lambda item: parse_rating(item.get("rating", "")), reverse=True)
        if sort_mode == "评分从低到高":
            return sorted(restaurants, key=lambda item: parse_rating(item.get("rating", "")))

        return sorted(restaurants, key=lambda item: parse_review_count(item.get("review_count", "")), reverse=True)

    def reset_filters(self) -> None:
        self.search_var.set("")
        self.tag_var.set("全部")
        self.sort_var.set("评论数从高到低")
        self.filtered_restaurants = self.sort_restaurants(list(self.all_restaurants))
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, restaurant in enumerate(self.filtered_restaurants):
            tags = ('evenrow',) if index % 2 == 0 else ('oddrow',)
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    restaurant.get("name", ""),
                    restaurant.get(self.tag_column, "") if self.tag_column else "",
                    restaurant.get("rating", ""),
                    restaurant.get("review_count", ""),
                    restaurant.get("avg_price", ""),
                    restaurant.get("area", ""),
                ),
                tags=tags
            )

        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('oddrow', background='#f8f9fa')

        total = len(self.all_restaurants)
        current = len(self.filtered_restaurants)
        tag_name = self.tag_column if self.tag_column else "无标签列"
        self.status_var.set(f"📊 共 {total} 家餐馆 | ✅ 当前显示 {current} 家 | 筛选字段：{tag_name}")

        if current:
            first_id = self.tree.get_children()[0]
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)
            self.on_select()
        else:
            self.detail_var.set("😕 没有找到匹配的餐馆\n\n💡 建议:\n• 尝试其他关键词\n• 更换标签筛选\n• 点击「重置」查看所有餐馆")

    def on_select(self, _event: tk.Event | None = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        row_index = int(selection[0])
        restaurant = self.filtered_restaurants[row_index]
        tag_value = restaurant.get(self.tag_column, "") if self.tag_column else "暂无"

        info_lines = [
            f"🏪 名称: {restaurant.get('name', '')}",
            f"",
            f"🏷️ 标签/分类: {tag_value or '暂无'}",
            f"",
            f"⭐ 评分: {restaurant.get('rating', '') or '暂无'}",
            f"",
            f"💬 评论数: {restaurant.get('review_count', '') or '暂无'}",
            f"",
            f"💰 人均: {restaurant.get('avg_price', '') or '暂无'}",
            f"",
            f"📍 区域: {restaurant.get('area', '') or '暂无'}",
            f"",
            f"🍜 推荐菜: {restaurant.get('recommended_dishes', '') or '暂无'}",
            f"",
            f"🎫 团购: {restaurant.get('has_group_buy', '') or '暂无'}",
            f"",
            f"🎁 优惠: {restaurant.get('has_promotion', '') or '暂无'}",
            f"",
            f"🔗 详情链接: {restaurant.get('detail_url', '') or '暂无'}",
        ]

        self.detail_var.set("\n".join(info_lines))

    def on_double_click(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.show_detail_dialog(item)

    def show_detail_dialog(self, item_id) -> None:
        row_index = int(item_id)
        if row_index < len(self.filtered_restaurants):
            restaurant = self.filtered_restaurants[row_index]
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"📍 {restaurant.get('name', '')}")
            detail_window.geometry("600x500")
            detail_window.configure(bg='white')

            tag_value = restaurant.get(self.tag_column, "") if self.tag_column else "暂无"

            content = "\n".join([
                f"{'=' * 50}",
                f"🏪 名称: {restaurant.get('name', '')}",
                f"{'=' * 50}",
                f"🏷️ 标签/分类: {tag_value or '暂无'}",
                f"⭐ 评分: {restaurant.get('rating', '') or '暂无'}",
                f"💬 评论数: {restaurant.get('review_count', '') or '暂无'}",
                f"💰 人均: {restaurant.get('avg_price', '') or '暂无'}",
                f"📍 区域: {restaurant.get('area', '') or '暂无'}",
                f"{'=' * 50}",
                f"🍜 推荐菜: {restaurant.get('recommended_dishes', '') or '暂无'}",
                f"{'=' * 50}",
                f"🎫 团购: {restaurant.get('has_group_buy', '') or '暂无'}",
                f"🎁 优惠: {restaurant.get('has_promotion', '') or '暂无'}",
                f"{'=' * 50}",
                f"🔗 详情链接:",
                f"{restaurant.get('detail_url', '') or '暂无'}",
                f"{'=' * 50}",
            ])

            text_widget = tk.Text(detail_window, wrap="word", font=('Microsoft YaHei UI', 20),
                                  bg='white', fg='#2c3e50', bd=0, padx=15, pady=15)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", content)
            text_widget.config(state="disabled")

            close_btn = ttk.Button(detail_window, text="关闭",
                                   command=detail_window.destroy,
                                   style='Action.TButton')
            close_btn.pack(pady=(0, 15))


def main() -> None:
    root = tk.Tk()

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = RestaurantAdvancedFilterApp(root)
    if not app.all_restaurants:
        root.destroy()
        return
    app.reset_filters()
    root.mainloop()


if __name__ == "__main__":
    main()

