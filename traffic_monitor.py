import tkinter as tk
from tkinter import ttk, scrolledtext, font
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import sys
import psutil
import os
from collections import defaultdict

running = False
monitor_connections = False


def monitor_bandwidth():
    old_sent = psutil.net_io_counters().bytes_sent
    old_recv = psutil.net_io_counters().bytes_recv
    
    while running:
        time.sleep(0.2)
        
        new_sent = psutil.net_io_counters().bytes_sent
        new_recv = psutil.net_io_counters().bytes_recv
        
        upload_speed = (new_sent - old_sent) / 1024
        download_speed = (new_recv - old_recv) / 1024
        
        old_sent = new_sent
        old_recv = new_recv
        
        upload_data.append(upload_speed)
        download_data.append(download_speed)
        
        if len(upload_data) > 50:
            upload_data.pop(0)
            download_data.pop(0)
        
        update_graph()


def start_monitor():
    global running, monitor_connections
    if not running:
        running = True
        monitor_connections = True
        # Update status indicator
        update_status_indicator(True)
        thread = threading.Thread(target=monitor_bandwidth, daemon=True)
        thread.start()
        
        # Thread untuk monitoring koneksi
        conn_thread = threading.Thread(target=monitor_network_connections, daemon=True)
        conn_thread.start()


def stop_monitor():
    global running, monitor_connections
    running = False
    monitor_connections = False
    update_status_indicator(False)


def update_graph():
    ax.clear()
    
    # Plot dengan warna gradient yang lebih vibrant
    ax.plot(upload_data, label="Upload", color="#FF6B9D", linewidth=3, marker='o', 
            markersize=4, markerfacecolor="#FF1744", markeredgewidth=0, alpha=0.9)
    ax.plot(download_data, label="Download", color="#00E5FF", linewidth=3, marker='o', 
            markersize=4, markerfacecolor="#00B8D4", markeredgewidth=0, alpha=0.9)
    
    # Fill area under curves untuk efek gradient
    if len(upload_data) > 0:
        ax.fill_between(range(len(upload_data)), upload_data, alpha=0.2, color="#FF6B9D")
        ax.fill_between(range(len(download_data)), download_data, alpha=0.2, color="#00E5FF")
    
    ax.set_ylabel("Speed (KB/s)", fontsize=11, fontweight='bold', color="#2C3E50")
    ax.set_xlabel("Time Window", fontsize=11, fontweight='bold', color="#2C3E50")
    ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=10, 
              fancybox=True, framealpha=0.9)
    ax.set_title("Real-Time Bandwidth Monitor", fontsize=13, fontweight='bold', 
                 color="#1A237E", pad=15)
    ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.8, color="#90A4AE")
    ax.set_facecolor('#F5F7FA')
    fig.patch.set_facecolor('#FFFFFF')
    
    # Styling untuk spines
    for spine in ax.spines.values():
        spine.set_edgecolor('#CFD8DC')
        spine.set_linewidth(1.5)
    
    canvas.draw()


def monitor_network_connections():
    """Monitor koneksi jaringan aktif, protokol, dan device yang terhubung"""
    while monitor_connections:
        try:
            connections = psutil.net_connections(kind='inet')
            
            # Kelompokkan berdasarkan protokol
            protocol_stats = defaultdict(int)
            remote_ips = set()
            connection_list = []
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    # Ambil protokol
                    protocol = "TCP" if conn.type == 1 else "UDP"
                    protocol_stats[protocol] += 1
                    
                    # Ambil remote address
                    if conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        local_port = conn.laddr.port
                        
                        remote_ips.add(remote_ip)
                        
                        # Coba dapatkan nama proses
                        try:
                            process = psutil.Process(conn.pid) if conn.pid else None
                            process_name = process.name() if process else "Tidak Diketahui"
                        except:
                            process_name = "Tidak Diketahui"
                        
                        # Translate status ke bahasa Indonesia
                        status_id = {
                            'ESTABLISHED': 'TERHUBUNG',
                            'LISTEN': 'MENDENGARKAN',
                            'TIME_WAIT': 'MENUNGGU',
                            'CLOSE_WAIT': 'MENUNGGU TUTUP'
                        }.get(conn.status, conn.status)
                        
                        connection_list.append({
                            'protocol': protocol,
                            'local_port': local_port,
                            'remote_ip': remote_ip,
                            'remote_port': remote_port,
                            'process': process_name,
                            'status': status_id
                        })
            
            # Update UI
            update_connection_display(protocol_stats, remote_ips, connection_list)
            
        except Exception as e:
            print(f"Error monitoring connections: {e}")
        
        time.sleep(2)  # Update setiap 2 detik


def update_connection_display(protocol_stats, remote_ips, connection_list):
    """Update tampilan informasi koneksi"""
    try:
        # Clear text area
        connection_text.config(state='normal')
        connection_text.delete(1.0, tk.END)
        
        # Header dengan styling lebih menarik
        connection_text.insert(tk.END, "═" * 70 + "\n", "header")
        connection_text.insert(tk.END, "  NETWORK CONNECTIONS MONITOR\n", "header")
        connection_text.insert(tk.END, "═" * 70 + "\n\n", "header")
        
        # Protokol aktif
        connection_text.insert(tk.END, "📊 PROTOKOL AKTIF:\n", "section")
        for protocol, count in protocol_stats.items():
            connection_text.insert(tk.END, f"   ● {protocol}: ", "protocol")
            connection_text.insert(tk.END, f"{count} koneksi\n", "count")
        connection_text.insert(tk.END, "\n")
        
        # Device yang terhubung
        connection_text.insert(tk.END, f"🌐 DEVICE TERHUBUNG ({len(remote_ips)} IP):\n", "section")
        for ip in sorted(remote_ips)[:10]:  # Tampilkan max 10
            connection_text.insert(tk.END, f"   ● {ip}\n", "ip")
        if len(remote_ips) > 10:
            connection_text.insert(tk.END, f"   ... dan {len(remote_ips)-10} IP lainnya\n", "normal")
        connection_text.insert(tk.END, "\n")
        
        # Detail koneksi aktif
        connection_text.insert(tk.END, "🔗 KONEKSI AKTIF (10 Terakhir):\n", "section")
        connection_text.insert(tk.END, "─" * 70 + "\n", "divider")
        
        for i, conn in enumerate(connection_list[:10], 1):
            connection_text.insert(tk.END, 
                f"{i}. ", "number")
            connection_text.insert(tk.END, 
                f"[{conn['protocol']}] {conn['process']}\n", "bold")
            connection_text.insert(tk.END, 
                f"   Local: :{conn['local_port']} → Remote: {conn['remote_ip']}:{conn['remote_port']}\n", "detail")
            connection_text.insert(tk.END, 
                f"   Status: {conn['status']}\n\n", "status")
        
        connection_text.config(state='disabled')
        
    except Exception as e:
        print(f"Error updating display: {e}")


def update_status_indicator(is_active):
    """Update status indicator dengan animasi"""
    if is_active:
        status_dot.config(text="🟢", fg="#00E676")
        status_label.config(text="MONITORING ACTIVE | Network Traffic Monitor v2.0 | Python 3.11")
        animate_status_dot()
    else:
        status_dot.config(text="🔴", fg="#FF1744")
        status_label.config(text="READY | Network Traffic Monitor v2.0 | Python 3.11")


def animate_status_dot():
    """Animasi pulse untuk status dot"""
    if running:
        current_text = status_dot.cget("text")
        status_dot.config(text="🟢" if current_text == "🟢" else "🟢")
        root.after(1000, animate_status_dot)


def create_rounded_button(parent, text, command, bg_color, hover_color, icon):
    """Create modern rounded button with Canvas for true rounded corners"""
    # Container frame
    container = tk.Frame(parent, bg="white")
    
    # Canvas untuk rounded rectangle
    canvas = tk.Canvas(container, width=220, height=55, bg="white", 
                      highlightthickness=0, bd=0)
    canvas.pack()
    
    # Draw shadow (offset rounded rectangle)
    shadow_color = "#BDBDBD"
    canvas.create_rounded_rectangle = lambda x1, y1, x2, y2, r, **kwargs: \
        canvas.create_polygon(
            x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1,
            x2, y1, x2, y1+r, x2, y1+r, x2, y2-r,
            x2, y2-r, x2, y2, x2-r, y2, x2-r, y2,
            x1+r, y2, x1+r, y2, x1, y2, x1, y2-r,
            x1, y2-r, x1, y1+r, x1, y1+r, x1, y1,
            smooth=True, **kwargs)
    
    # Shadow
    shadow = canvas.create_rounded_rectangle(4, 4, 218, 53, 25, 
                                             fill=shadow_color, outline="")
    
    # Main button background
    btn_bg = canvas.create_rounded_rectangle(2, 2, 216, 51, 25, 
                                             fill=bg_color, outline="")
    
    # Button text
    btn_text = canvas.create_text(110, 27, text=f"{icon}  {text}", 
                                 fill="white", font=("Segoe UI", 12, "bold"))
    
    # Store colors and state
    canvas.bg_color = bg_color
    canvas.hover_color = hover_color
    canvas.btn_bg = btn_bg
    canvas.btn_text = btn_text
    canvas.is_hovered = False
    
    # Hover effects
    def on_enter(e):
        canvas.itemconfig(btn_bg, fill=hover_color)
        canvas.itemconfig(btn_text, font=("Segoe UI", 13, "bold"))
        canvas.is_hovered = True
    
    def on_leave(e):
        canvas.itemconfig(btn_bg, fill=bg_color)
        canvas.itemconfig(btn_text, font=("Segoe UI", 12, "bold"))
        canvas.is_hovered = False
    
    def on_click(e):
        # Visual feedback
        canvas.itemconfig(btn_bg, fill=hover_color)
        canvas.after(100, lambda: canvas.itemconfig(btn_bg, 
                    fill=hover_color if canvas.is_hovered else bg_color))
        command()
    
    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)
    
    return container


# Inisialisasi Tkinter GUI dengan styling modern
root = tk.Tk()
root.title("🌐 Network Traffic Monitor Pro v2.0")
root.geometry("1400x800")

# Gradient background simulation dengan multiple frames
bg_gradient = tk.Canvas(root, highlightthickness=0)
bg_gradient.pack(fill=tk.BOTH, expand=True)

# Create gradient effect
for i in range(800):
    # Gradient dari #E3F2FD ke #F5F5F5
    r = int(227 + (245 - 227) * i / 800)
    g = int(242 + (245 - 242) * i / 800)
    b = int(253 + (245 - 253) * i / 800)
    color = f'#{r:02x}{g:02x}{b:02x}'
    bg_gradient.create_line(0, i, 1400, i, fill=color, width=1)

# Main container on top of gradient
main_frame = tk.Frame(bg_gradient, bg='', highlightthickness=0)
bg_gradient.create_window(0, 0, window=main_frame, anchor='nw', width=1400, height=800)

# Header Frame dengan gradient
header_frame = tk.Frame(main_frame, bg="#1A237E", height=70)
header_frame.pack(fill=tk.X, side=tk.TOP)
header_frame.pack_propagate(False)

# Header dengan icon dan styling modern
header_label = tk.Label(header_frame, 
                        text="🌐 NETWORK TRAFFIC MONITOR PRO",
                        font=('Segoe UI', 22, 'bold'),
                        bg="#1A237E",
                        fg="#FFFFFF")
header_label.pack(pady=18)

# Subtitle
subtitle_label = tk.Label(header_frame,
                          text="Real-Time Network Analysis & Monitoring",
                          font=('Segoe UI', 10),
                          bg="#1A237E",
                          fg="#B3E5FC")
subtitle_label.pack()

# Main container dengan padding
main_container = tk.Frame(main_frame, bg='')
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# Frame kiri untuk grafik dengan glassmorphism effect
left_frame = tk.Frame(main_container, bg='')
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

# Graph card frame dengan shadow effect (simulasi dengan multiple frames)
shadow_frame = tk.Frame(left_frame, bg="#B0BEC5")
shadow_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

graph_card = tk.Frame(shadow_frame, bg="white", relief=tk.FLAT, borderwidth=0)
graph_card.pack(fill=tk.BOTH, expand=True)

# Graph title dengan icon
graph_title_frame = tk.Frame(graph_card, bg="white")
graph_title_frame.pack(pady=15)

graph_title = tk.Label(graph_title_frame,
                       text="📊 Bandwidth Statistics",
                       font=('Segoe UI', 14, 'bold'),
                       bg="white",
                       fg="#1A237E")
graph_title.pack()

# Matplotlib figure dengan styling (ukuran lebih kecil untuk beri ruang button)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
upload_data = []
download_data = []
canvas = FigureCanvasTkAgg(fig, master=graph_card)
canvas.get_tk_widget().pack(padx=15, pady=(10, 5), fill=tk.BOTH, expand=True)

# Frame untuk tombol dengan modern design - posisi lebih ke atas
btn_container = tk.Frame(graph_card, bg="white")
btn_container.pack(pady=(10, 15))

# Container untuk buttons dalam satu baris
btn_row = tk.Frame(btn_container, bg="white")
btn_row.pack()

# Create modern rounded buttons
btn_start = create_rounded_button(btn_row, "START MONITORING", start_monitor,
                                  "#00C853", "#00E676", "▶")
btn_start.pack(side=tk.LEFT, padx=8)

btn_stop = create_rounded_button(btn_row, "STOP MONITORING", stop_monitor,
                                 "#D32F2F", "#FF1744", "⏹")
btn_stop.pack(side=tk.LEFT, padx=8)

# Frame kanan untuk informasi koneksi
right_frame = tk.Frame(main_container, bg='')
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

# Connection info card dengan shadow
shadow_frame_right = tk.Frame(right_frame, bg="#B0BEC5")
shadow_frame_right.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

info_card = tk.Frame(shadow_frame_right, bg="white", relief=tk.FLAT, borderwidth=0)
info_card.pack(fill=tk.BOTH, expand=True)

# Label judul dengan icon
title_frame = tk.Frame(info_card, bg="white")
title_frame.pack(pady=15)

title_label = tk.Label(title_frame,
                       text="🔗 Network Connections Info",
                       font=("Segoe UI", 14, "bold"),
                       bg="white",
                       fg="#1A237E")
title_label.pack()

# ScrolledText dengan styling modern
connection_text = scrolledtext.ScrolledText(info_card,
                                           width=60,
                                           height=40,
                                           font=("Consolas", 9),
                                           bg="#FAFAFA",
                                           fg="#263238",
                                           relief=tk.FLAT,
                                           borderwidth=0,
                                           padx=10,
                                           pady=10)
connection_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

# Konfigurasi tags untuk styling dengan warna lebih vibrant
connection_text.tag_config("header", font=("Consolas", 11, "bold"), foreground="#1A237E")
connection_text.tag_config("section", font=("Consolas", 10, "bold"), foreground="#D84315")
connection_text.tag_config("protocol", font=("Consolas", 9, "bold"), foreground="#6A1B9A")
connection_text.tag_config("count", font=("Consolas", 9, "bold"), foreground="#00897B")
connection_text.tag_config("ip", font=("Consolas", 9), foreground="#0277BD")
connection_text.tag_config("bold", font=("Consolas", 9, "bold"), foreground="#2E7D32")
connection_text.tag_config("detail", font=("Consolas", 9), foreground="#455A64")
connection_text.tag_config("status", font=("Consolas", 9, "bold"), foreground="#F57C00")
connection_text.tag_config("normal", font=("Consolas", 9), foreground="#37474F")
connection_text.tag_config("number", font=("Consolas", 9, "bold"), foreground="#C62828")
connection_text.tag_config("divider", font=("Consolas", 9), foreground="#90A4AE")

# Initial message dengan styling
connection_text.insert(tk.END, "\n\n   ⏳ Klik 'START MONITORING' untuk memulai...\n\n", "section")
connection_text.insert(tk.END, "   📡 Monitoring akan menampilkan:\n\n", "normal")
connection_text.insert(tk.END, "   ● Protokol aktif (TCP/UDP)\n", "protocol")
connection_text.insert(tk.END, "   ● Device yang terhubung\n", "ip")
connection_text.insert(tk.END, "   ● Detail koneksi real-time\n\n", "detail")
connection_text.config(state='disabled')

# Status bar dengan gradient
status_frame = tk.Frame(main_frame, bg="#263238", height=35)
status_frame.pack(fill=tk.X, side=tk.BOTTOM)
status_frame.pack_propagate(False)

# Status container
status_container = tk.Frame(status_frame, bg="#263238")
status_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=5)

# Status dot
status_dot = tk.Label(status_container,
                     text="🔴",
                     font=('Segoe UI', 12),
                     bg="#263238",
                     fg="#FF1744")
status_dot.pack(side=tk.LEFT, padx=5)

# Status label
status_label = tk.Label(status_container,
                       text="READY | Network Traffic Monitor v2.0 | Python 3.11",
                       font=('Segoe UI', 10),
                       bg="#263238",
                       fg="#ECEFF1")
status_label.pack(side=tk.LEFT, padx=10)

# Copyright/credit
credit_label = tk.Label(status_frame,
                       text="Powered by Python & Tkinter",
                       font=('Segoe UI', 9, 'italic'),
                       bg="#263238",
                       fg="#78909C")
credit_label.pack(side=tk.RIGHT, padx=15)


# Clean exit handler
def on_closing():
    global running, monitor_connections
    running = False
    monitor_connections = False
    time.sleep(0.3)
    os._exit(0)


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
