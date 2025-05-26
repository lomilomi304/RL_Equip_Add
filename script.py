import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, Toplevel
from bs4 import BeautifulSoup
import os
import sys
import tempfile
import shutil

def get_icon_path():
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        temp_icon = os.path.join(tempfile.gettempdir(), "ico.ico")
        bundle_icon = os.path.join(sys._MEIPASS, "ico.ico")
        shutil.copyfile(bundle_icon, temp_icon)
        return temp_icon
    else:
        # Running as a script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.ico")

def get_sections(soup):
    sections = []
    for section in soup.find_all('section'):
        header = section.find(['h2', 'h1'], class_='section-header')
        content = section.find('div', class_='section-content')
        if header and content:
            sections.append((header.text.strip(), content))
    return sections

def add_equipment_card(soup, content_div, title, description, checkout, link, img_url):
    card = soup.new_tag('div', attrs={'class': 'item-card'})
    card_header = soup.new_tag('div', attrs={'class': 'card-header'})
    # Use user-provided image or placeholder
    img = soup.new_tag('img', attrs={
        'class': 'card-img',
        'src': img_url if img_url else '/sites/default/files/placeholder.png',
        'alt': title,
        'width': '100',
        'height': '100'
    })
    card_header.append(img)
    h3 = soup.new_tag('h3', attrs={'class': 'card-title'})
    h3.string = title
    card_header.append(h3)
    card.append(card_header)

    card_content = soup.new_tag('div', attrs={'class': 'card-content'})
    if description:
        desc_p = soup.new_tag('p', attrs={'class': 'card-info'})
        desc_strong = soup.new_tag('strong')
        desc_strong.string = 'Description:'
        desc_p.append(desc_strong)
        desc_p.append(' ' + description)
        card_content.append(desc_p)
    if checkout:
        checkout_p = soup.new_tag('p', attrs={'class': 'card-info'})
        checkout_strong = soup.new_tag('strong')
        checkout_strong.string = 'Checkout Period:'
        checkout_p.append(checkout_strong)
        checkout_p.append(' ' + checkout)
        card_content.append(checkout_p)
    if link:
        link_p = soup.new_tag('p')
        a = soup.new_tag('a', attrs={'class': 'check-btn', 'href': link})
        a.string = 'Check Availability'
        link_p.append(a)
        card_content.append(link_p)
    card.append(card_content)
    content_div.append(card)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)
        # Only load sections if no pasted HTML
        if not html_text.get("1.0", tk.END).strip():
            load_sections_from_file(file_path)

def load_sections_from_file(file_path):
    global soup, section_map
    with open(file_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    update_section_dropdown(soup)

def load_sections_from_text():
    global soup, section_map
    html = html_text.get("1.0", tk.END)
    soup = BeautifulSoup(html, 'html.parser')
    update_section_dropdown(soup)

def update_section_dropdown(soup_obj):
    global section_map
    sections = get_sections(soup_obj)
    section_map = {name: div for name, div in sections}
    section_dropdown['values'] = list(section_map.keys())
    if sections:
        section_dropdown.current(0)
    else:
        section_dropdown.set('')

def on_html_text_change(event=None):
    # If user pastes HTML, update dropdown
    if html_text.get("1.0", tk.END).strip():
        load_sections_from_text()
    elif file_entry.get():
        load_sections_from_file(file_entry.get())
    else:
        section_dropdown['values'] = []
        section_dropdown.set('')

def generate():
    # Use pasted HTML if present, else file
    html = html_text.get("1.0", tk.END).strip()
    if html:
        soup_obj = BeautifulSoup(html, 'html.parser')
    elif file_entry.get():
        with open(file_entry.get(), encoding='utf-8') as f:
            soup_obj = BeautifulSoup(f, 'html.parser')
    else:
        messagebox.showerror("Error", "Please provide HTML (file or paste).")
        return

    title = title_entry.get().strip()
    description = desc_entry.get().strip()
    checkout = checkout_entry.get().strip()
    link = link_entry.get().strip()
    img_url = img_entry.get().strip()
    section = section_var.get()
    if not (title and checkout and link and section):
        messagebox.showerror("Error", "Please fill in all required fields.")
        return

    # Find section-content div for the selected section
    sections = get_sections(soup_obj)
    section_map_local = {name: div for name, div in sections}
    content_div = section_map_local.get(section)
    if not content_div:
        messagebox.showerror("Error", "Section not found in HTML.")
        return

    add_equipment_card(soup_obj, content_div, title, description, checkout, link, img_url)

    # Show result in a new window
    show_html_window(str(soup_obj))

def show_html_window(html_code):
    win = Toplevel(root)
    win.title("Generated HTML")
    st = scrolledtext.ScrolledText(win, width=120, height=40, wrap=tk.WORD)
    st.pack(expand=True, fill='both')
    st.insert(tk.END, html_code)
    st.config(state='normal')
    # Optionally, add a button to copy to clipboard
    def copy_to_clipboard():
        win.clipboard_clear()
        win.clipboard_append(html_code)
        messagebox.showinfo("Copied", "HTML code copied to clipboard.")
    tk.Button(win, text="Copy to Clipboard", command=copy_to_clipboard).pack(pady=5)

# GUI setup
root = tk.Tk()
root.title("Equipment+")
# Set window icon
icon_path = get_icon_path()
root.iconbitmap(icon_path)

row = 0
tk.Label(root, text="HTML File:").grid(row=row, column=0, sticky='e')
file_entry = tk.Entry(root, width=50)
file_entry.grid(row=row, column=1)
tk.Button(root, text="Browse", command=select_file).grid(row=row, column=2)

row += 1
tk.Label(root, text="Or paste HTML:").grid(row=row, column=0, sticky='ne')
html_text = scrolledtext.ScrolledText(root, width=60, height=8, wrap=tk.WORD)
html_text.grid(row=row, column=1, columnspan=2, sticky='we')
html_text.bind("<KeyRelease>", on_html_text_change)

row += 1
tk.Label(root, text="Section:").grid(row=row, column=0, sticky='e')
section_var = tk.StringVar()
section_dropdown = ttk.Combobox(root, textvariable=section_var, state='readonly')
section_dropdown.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Label(root, text="Title:").grid(row=row, column=0, sticky='e')
title_entry = tk.Entry(root, width=50)
title_entry.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Label(root, text="Description:").grid(row=row, column=0, sticky='e')
desc_entry = tk.Entry(root, width=50)
desc_entry.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Label(root, text="Checkout Period:").grid(row=row, column=0, sticky='e')
checkout_entry = tk.Entry(root, width=50)
checkout_entry.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Label(root, text="Link:").grid(row=row, column=0, sticky='e')
link_entry = tk.Entry(root, width=50)
link_entry.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Label(root, text="Image Link:").grid(row=row, column=0, sticky='e')
img_entry = tk.Entry(root, width=50)
img_entry.grid(row=row, column=1, columnspan=2, sticky='we')

row += 1
tk.Button(root, text="Generate", command=generate).grid(row=row, column=0, columnspan=3, pady=10)

soup = None
section_map = {}

root.mainloop()