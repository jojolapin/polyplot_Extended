import folium
from folium.plugins import BeautifyIcon
from pyproj import Transformer
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, scrolledtext
from shapely.geometry import Polygon
from geopy.distance import geodesic
import random
import re
import pyperclip
import webbrowser
import threading
import os
import math
from pathlib import Path

# Import external modules for KML and Converter
# from kml_creator import open_kml_generator_window
# from coordinate_converter import open_converter_window as open_converter_window_external

VERSION = "3.0.0"

# Modern color scheme
COLORS = {
    'primary': '#2563eb',  # Blue
    'primary_dark': '#1d4ed8',
    'secondary': '#10b981',  # Green
    'secondary_dark': '#059669',
    'background': '#f8fafc',  # Light gray
    'surface': '#ffffff',  # White
    'text': '#1f2937',  # Dark gray
    'text_light': '#6b7280',  # Medium gray
    'border': '#e5e7eb',  # Light border
    'error': '#ef4444',  # Red
    'warning': '#f59e0b',  # Orange
    'success': '#10b981'  # Green
}

parameters = {
    "distance_piquets": 2,
    "cout_piquet": 0,
    "cout_grillage": 0
}

COUNTRY_UTM_ZONES = {
    "Burkina Faso": 30,
    "United States": 17,
    "France": 31,
    "Germany": 32,
    "Brazil": 23,
    "India": 44,
    "Australia": 55,
    "Canada": 10,
    "Russia": 37,
    "China": 50,
    "South Africa": 35,
    "Argentina": 21,
    "Mexico": 14,
    "Egypt": 36
}


def utm_to_wgs84(x, y, zone=30, northern=True):
    transformer = Transformer.from_crs(
        f"+proj=utm +zone={zone} +ellps=WGS84 +north={int(northern)}",
        "EPSG:4326",
        always_xy=True
    )
    lon, lat = transformer.transform(x, y)
    return lat, lon


def latlon_to_utm(lat, lon, zone=30, northern=True):
    target_epsg = 32600 + zone if northern else 32700 + zone
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{target_epsg}", always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    return easting, northing


class ModernButton(ttk.Frame):
    """Custom modern button with hover effects"""

    def __init__(self, parent, text, command=None, style='primary', width=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.command = command
        self.style_type = style

        # Configure button appearance based on style
        if style == 'primary':
            bg_color = COLORS['primary']
            hover_color = COLORS['primary_dark']
            text_color = 'white'
        elif style == 'secondary':
            bg_color = COLORS['secondary']
            hover_color = COLORS['secondary_dark']
            text_color = 'white'
        elif style == 'outline':
            bg_color = COLORS['surface']
            hover_color = COLORS['background']
            text_color = COLORS['primary']
        else:
            bg_color = COLORS['background']
            hover_color = COLORS['border']
            text_color = COLORS['text']

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

        # Create button label
        self.button = tk.Label(
            self,
            text=text,
            bg=bg_color,
            fg=text_color,
            font=('Segoe UI', 10, 'normal'),
            cursor='hand2',
            padx=20,
            pady=8,
            relief='flat',
            borderwidth=1 if style == 'outline' else 0
        )

        if width:
            self.button.config(width=width)

        self.button.pack(fill='both', expand=True)

        # Bind events
        self.button.bind('<Button-1>', self._on_click)
        self.button.bind('<Enter>', self._on_enter)
        self.button.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.button.config(bg=self.hover_color)

    def _on_leave(self, event):
        self.button.config(bg=self.bg_color)


class ModernCard(ttk.Frame):
    """Modern card-style container"""

    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, **kwargs)

        # Configure card style
        style = ttk.Style()
        style.configure('Card.TFrame',
                        background=COLORS['surface'],
                        relief='flat',
                        borderwidth=1)

        self.configure(style='Card.TFrame', padding=20)

        if title:
            title_label = ttk.Label(
                self,
                text=title,
                font=('Segoe UI', 12, 'bold'),
                foreground=COLORS['text']
            )
            title_label.pack(anchor='w', pady=(0, 15))


class ProgressDialog:
    """Modern progress dialog"""

    def __init__(self, parent, title="Processing..."):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("300x120")
        self.window.transient(parent)
        self.window.grab_set()

        # Center the dialog
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.window.winfo_screenheight() // 2) - (120 // 2)
        self.window.geometry(f"300x120+{x}+{y}")

        # Progress frame
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill='both', expand=True)

        # Progress label
        self.label = ttk.Label(frame, text="Processing...", font=('Segoe UI', 10))
        self.label.pack(pady=(0, 10))

        # Progress bar
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 10))
        self.progress.start()

        # Cancel button
        self.cancel_button = ModernButton(frame, "Cancel", style='outline')
        self.cancel_button.pack()

    def update_text(self, text):
        self.label.config(text=text)

    def close(self):
        self.progress.stop()
        self.window.destroy()


class ParametersWindow:
    """Modern parameters configuration window"""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Cost and Spacing Parameters")
        self.window.geometry("450x300")
        self.window.transient(parent)
        self.window.grab_set()

        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f"450x300+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Configuration Parameters",
            font=('Segoe UI', 16, 'bold'),
            foreground=COLORS['text']
        )
        title_label.pack(pady=(0, 20))

        # Parameters card
        params_card = ModernCard(main_frame)
        params_card.pack(fill='x', pady=(0, 20))

        # Distance parameter
        distance_frame = ttk.Frame(params_card)
        distance_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(distance_frame, text="Distance between posts (m):",
                  font=('Segoe UI', 10)).pack(anchor='w')
        self.distance_entry = ttk.Entry(distance_frame, font=('Segoe UI', 10))
        self.distance_entry.insert(0, str(parameters["distance_piquets"]))
        self.distance_entry.pack(fill='x', pady=(5, 0))

        # Post cost parameter
        piquet_frame = ttk.Frame(params_card)
        piquet_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(piquet_frame, text="Cost per post (FCFA):",
                  font=('Segoe UI', 10)).pack(anchor='w')
        self.piquet_entry = ttk.Entry(piquet_frame, font=('Segoe UI', 10))
        self.piquet_entry.insert(0, str(parameters["cout_piquet"]))
        self.piquet_entry.pack(fill='x', pady=(5, 0))

        # Mesh cost parameter
        grillage_frame = ttk.Frame(params_card)
        grillage_frame.pack(fill='x')

        ttk.Label(grillage_frame, text="Cost for 25m of mesh (FCFA):",
                  font=('Segoe UI', 10)).pack(anchor='w')
        self.grillage_entry = ttk.Entry(grillage_frame, font=('Segoe UI', 10))
        self.grillage_entry.insert(0, str(parameters["cout_grillage"]))
        self.grillage_entry.pack(fill='x', pady=(5, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')

        cancel_btn = ModernButton(button_frame, "Cancel",
                                  command=self.window.destroy, style='outline')
        cancel_btn.pack(side='right', padx=(10, 0))

        save_btn = ModernButton(button_frame, "Save Parameters",
                                command=self.save_parameters)
        save_btn.pack(side='right')

    def save_parameters(self):
        try:
            parameters["distance_piquets"] = float(self.distance_entry.get())
            parameters["cout_piquet"] = float(self.piquet_entry.get())
            parameters["cout_grillage"] = float(self.grillage_entry.get())
            messagebox.showinfo("Success", "Parameters saved successfully!")
            self.window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")


class PolyPlotApp:
    """Main PolyPlot application with modern GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"PolyPlot v{VERSION}")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['background'])

        # Configure modern styles
        self.setup_styles()

        # Global marker map
        self.global_point_map = {}

        # Cached summary information
        self.latest_summary_data = []
        self.latest_points_sets = []

        # Setup UI
        self.setup_ui()

        # Center window
        self.center_window()

    def setup_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()

        # Configure frame styles
        style.configure('Main.TFrame', background=COLORS['background'])
        style.configure('Card.TFrame', background=COLORS['surface'], relief='solid', borderwidth=1)
        style.configure('Sidebar.TFrame', background=COLORS['surface'])

        # Configure label styles
        style.configure('Title.TLabel',
                        background=COLORS['background'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 20, 'bold'))

        style.configure('Subtitle.TLabel',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 12, 'bold'))

        style.configure('Body.TLabel',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 10))

        # Configure entry styles
        style.configure('Modern.TEntry',
                        font=('Segoe UI', 10),
                        padding=8)

        # Configure checkbutton styles
        style.configure('Modern.TCheckbutton',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 10))

        # Treeview style for summary tables
        style.configure('Summary.Treeview',
                        background=COLORS['surface'],
                        fieldbackground=COLORS['surface'],
                        foreground=COLORS['text'],
                        rowheight=24,
                        font=('Segoe UI', 9))
        style.configure('Summary.Treeview.Heading',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 9, 'bold'))

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Setup the main user interface"""
        # Create menu bar
        self.create_menu()

        # Main container
        main_container = ttk.Frame(self.root, style='Main.TFrame', padding=20)
        main_container.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(
            main_container,
            text=f"PolyPlot v{VERSION}",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 20))

        # Create main content area
        content_frame = ttk.Frame(main_container, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True)

        # Left panel - Input
        left_panel = ModernCard(content_frame, title="Coordinate Input")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.setup_input_panel(left_panel)

        # Right panel - Options
        right_panel = ModernCard(content_frame, title="Map Options")
        right_panel.pack(side='right', fill='y', padx=(10, 0))

        self.setup_options_panel(right_panel)

        # Bottom panel - Actions
        bottom_panel = ttk.Frame(main_container, style='Main.TFrame')
        bottom_panel.pack(fill='x', pady=(20, 0))

        self.setup_action_panel(bottom_panel)

        # Status bar
        self.setup_status_bar()

    def create_menu(self):
        """Create modern menu bar"""
        menubar = tk.Menu(self.root, bg=COLORS['surface'], fg=COLORS['text'])
        self.root.config(menu=menubar)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['surface'], fg=COLORS['text'])
        tools_menu.add_command(label="Parameters", command=self.open_parameters)
        tools_menu.add_separator()
        tools_menu.add_command(label="Coordinate Converter", command=self.open_converter)
        tools_menu.add_command(label="KML Generator", command=self.open_kml_generator)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['surface'], fg=COLORS['text'])
        file_menu.add_command(label="Load Coordinates", command=self.load_coordinates)
        file_menu.add_command(label="Save Coordinates", command=self.save_coordinates)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['surface'], fg=COLORS['text'])
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def setup_input_panel(self, parent):
        """Setup coordinate input panel"""
        # Instructions
        instructions = ttk.Label(
            parent,
            text="Enter coordinates (one pair per line).\nSeparate enclosures with blank lines.\nSupports both Lat/Lon and UTM formats.",
            style='Body.TLabel',
            justify='left'
        )
        instructions.pack(anchor='w', pady=(0, 10))

        # Text input area
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.points_entry = tk.Text(
            text_frame,
            font=('Consolas', 10),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            selectbackground=COLORS['primary'],
            relief='solid',
            borderwidth=1,
            wrap='word'
        )

        # Scrollbar for text area
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.points_entry.yview)
        self.points_entry.configure(yscrollcommand=scrollbar.set)

        self.points_entry.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Context menu for text area
        self.create_context_menu(self.points_entry)

        # Sample data button
        sample_btn = ModernButton(
            parent,
            "Load Sample Data",
            command=self.load_sample_data,
            style='outline'
        )
        sample_btn.pack(pady=(10, 0), fill='x')

    def setup_options_panel(self, parent):
        """Setup map options panel"""
        # Coordinate conversion settings
        coord_frame = ttk.LabelFrame(parent, text="Coordinate Settings", padding=10)
        coord_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(coord_frame, text="Country preset:", style='Body.TLabel').pack(anchor='w')
        country_values = ['Custom'] + sorted(COUNTRY_UTM_ZONES.keys())
        self.country_var = tk.StringVar(value='Custom')
        country_combo = ttk.Combobox(
            coord_frame,
            textvariable=self.country_var,
            values=country_values,
            state='readonly'
        )
        country_combo.pack(fill='x', pady=(5, 10))
        country_combo.bind('<<ComboboxSelected>>', self.on_country_change)

        ttk.Label(coord_frame, text="UTM Zone:", style='Body.TLabel').pack(anchor='w')
        self.zone_var = tk.StringVar(value=str(COUNTRY_UTM_ZONES['Burkina Faso']))
        zone_combo = ttk.Combobox(
            coord_frame,
            textvariable=self.zone_var,
            values=[str(i) for i in range(1, 61)],
            state='readonly'
        )
        zone_combo.pack(fill='x', pady=(5, 10))
        zone_combo.bind('<<ComboboxSelected>>', self.on_zone_change)

        self.northern_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            coord_frame,
            text="Northern hemisphere",
            variable=self.northern_var,
            style='Modern.TCheckbutton',
            command=self.on_hemisphere_toggle
        ).pack(anchor='w')

        ttk.Label(
            coord_frame,
            text="Configure the default UTM zone used when converting coordinates.",
            style='Body.TLabel',
            wraplength=220
        ).pack(anchor='w', pady=(8, 0))

        # Map display options
        display_frame = ttk.LabelFrame(parent, text="Display Options", padding=10)
        display_frame.pack(fill='x', pady=(0, 15))

        self.show_markers_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            display_frame,
            text="Show point markers",
            variable=self.show_markers_var,
            style='Modern.TCheckbutton'
        ).pack(anchor='w', pady=2)

        self.show_popups_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show information popups",
            variable=self.show_popups_var,
            style='Modern.TCheckbutton'
        ).pack(anchor='w', pady=2)

        self.show_custom_icons_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            display_frame,
            text="Use custom icons",
            variable=self.show_custom_icons_var,
            style='Modern.TCheckbutton'
        ).pack(anchor='w', pady=2)

        self.random_colors_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Random surface colors",
            variable=self.random_colors_var,
            style='Modern.TCheckbutton'
        ).pack(anchor='w', pady=2)

        self.show_distance_markers_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            display_frame,
            text="Show distance markers",
            variable=self.show_distance_markers_var,
            style='Modern.TCheckbutton'
        ).pack(anchor='w', pady=2)

        # Export options
        export_frame = ttk.LabelFrame(parent, text="Export Options", padding=10)
        export_frame.pack(fill='x')

        export_map_btn = ModernButton(
            export_frame,
            "Export to KML",
            command=self.export_to_kml,
            style='secondary'
        )
        export_map_btn.pack(fill='x', pady=(0, 5))

        export_data_btn = ModernButton(
            export_frame,
            "Export Calculations",
            command=self.export_calculations,
            style='outline'
        )
        export_data_btn.pack(fill='x')

        # Summary card
        summary_card = ModernCard(parent, title="Enclosure Summary")
        summary_card.pack(fill='both', expand=True, pady=(15, 0))

        tree_frame = ttk.Frame(summary_card, style='Card.TFrame')
        tree_frame.pack(fill='both', expand=True)

        columns = ('name', 'area_ha', 'perimeter', 'posts', 'cost')
        self.summary_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            style='Summary.Treeview',
            selectmode='browse'
        )
        self.summary_tree.heading('name', text='Enclosure')
        self.summary_tree.heading('area_ha', text='Area (ha)')
        self.summary_tree.heading('perimeter', text='Perimeter (m)')
        self.summary_tree.heading('posts', text='Posts')
        self.summary_tree.heading('cost', text='Cost (FCFA)')

        self.summary_tree.column('name', width=110, anchor='w')
        self.summary_tree.column('area_ha', width=80, anchor='e')
        self.summary_tree.column('perimeter', width=100, anchor='e')
        self.summary_tree.column('posts', width=60, anchor='center')
        self.summary_tree.column('cost', width=100, anchor='e')

        summary_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=summary_scrollbar.set)
        self.summary_tree.pack(side='left', fill='both', expand=True)
        summary_scrollbar.pack(side='right', fill='y')

        self.summary_totals_var = tk.StringVar(value="No data loaded.")
        totals_label = ttk.Label(summary_card, textvariable=self.summary_totals_var, style='Body.TLabel')
        totals_label.pack(anchor='w', pady=(10, 0))

        copy_btn = ModernButton(summary_card, "Copy Summary", command=self.copy_summary, style='outline')
        copy_btn.pack(fill='x', pady=(10, 0))

    def setup_action_panel(self, parent):
        """Setup action buttons panel"""
        action_frame = ttk.Frame(parent, style='Main.TFrame')
        action_frame.pack(fill='x')

        # Clear button
        clear_btn = ModernButton(
            action_frame,
            "Clear All",
            command=self.clear_all,
            style='outline'
        )
        clear_btn.pack(side='left', padx=(0, 10))

        # Validate button
        validate_btn = ModernButton(
            action_frame,
            "Validate Input",
            command=self.validate_input,
            style='secondary'
        )
        validate_btn.pack(side='left', padx=(0, 10))

        # Generate map button
        generate_btn = ModernButton(
            action_frame,
            "Generate Map",
            command=self.generate_map,
            style='primary'
        )
        generate_btn.pack(side='right', padx=(10, 0))

        # Open map button
        open_btn = ModernButton(
            action_frame,
            "Open Last Map",
            command=self.open_last_map,
            style='outline'
        )
        open_btn.pack(side='right')

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = ttk.Frame(self.root, style='Main.TFrame')
        self.status_bar.pack(side='bottom', fill='x', padx=20, pady=(10, 20))

        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            style='Body.TLabel'
        )
        self.status_label.pack(side='left')

        # Copyright
        copyright_label = ttk.Label(
            self.status_bar,
            text="© JojoLapin",
            style='Body.TLabel'
        )
        copyright_label.pack(side='right')

    def create_context_menu(self, widget):
        """Create context menu for text widget"""
        context_menu = tk.Menu(widget, tearoff=0, bg=COLORS['surface'], fg=COLORS['text'])
        context_menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
        context_menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        context_menu.add_separator()
        context_menu.add_command(label="Select All", command=lambda: widget.tag_add('sel', '1.0', 'end'))

        def show_context_menu(event):
            context_menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_context_menu)

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def load_sample_data(self):
        """Load sample coordinate data"""
        sample_data = """Enclosure 1
12.3456, -1.5234
12.3466, -1.5234
12.3466, -1.5244
12.3456, -1.5244

Enclosure 2
12.3500, -1.5300
12.3510, -1.5300
12.3510, -1.5310
12.3500, -1.5310"""

        self.points_entry.delete("1.0", tk.END)
        self.points_entry.insert("1.0", sample_data)
        self.update_status("Sample data loaded")
        try:
            points_sets = self.parse_input(sample_data)
            self.update_summary(points_sets)
        except Exception:
            self.update_summary([])

    def clear_all(self):
        """Clear all input"""
        if messagebox.askyesno("Confirm", "Clear all input data?"):
            self.points_entry.delete("1.0", tk.END)
            self.update_status("Input cleared")
            self.update_summary([])

    def validate_input(self):
        """Validate coordinate input"""
        try:
            points_sets = self.parse_input(self.points_entry.get("1.0", tk.END))
            if points_sets:
                count = len(points_sets)
                total_points = sum(len(ps['points']) for ps in points_sets)
                messagebox.showinfo(
                    "Validation Result",
                    f"✓ Input is valid!\n\nFound {count} enclosure(s) with {total_points} total points."
                )
                self.update_status(f"Validation successful: {count} enclosures, {total_points} points")
                self.update_summary(points_sets)
            else:
                messagebox.showwarning("Validation Result", "No valid coordinate data found.")
                self.update_status("Validation failed: No valid data")
                self.update_summary([])
        except Exception as e:
            messagebox.showerror("Validation Error", f"Input validation failed:\n{str(e)}")
            self.update_status("Validation failed: Invalid format")
            self.update_summary([])

    def generate_map(self):
        """Generate map with progress dialog"""
        try:
            points_sets = self.parse_input(self.points_entry.get("1.0", tk.END))
            if not points_sets:
                messagebox.showwarning("Input Error", "No valid coordinate data found.")
                return

            self.update_summary(points_sets)

            # Create progress dialog
            progress = ProgressDialog(self.root, "Generating Map...")

            def generate_in_thread():
                try:
                    self.create_map(
                        points_sets,
                        self.show_markers_var.get(),
                        self.show_popups_var.get(),
                        self.show_custom_icons_var.get(),
                        self.random_colors_var.get(),
                        self.show_distance_markers_var.get()
                    )
                    progress.close()
                    self.update_status("Map generated successfully")
                except Exception as e:
                    progress.close()
                    messagebox.showerror("Error", f"Failed to generate map:\n{str(e)}")
                    self.update_status("Map generation failed")

            # Start generation in separate thread
            thread = threading.Thread(target=generate_in_thread)
            thread.daemon = True
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate map:\n{str(e)}")
            self.update_status("Map generation failed")

    def open_last_map(self):
        """Open the last generated map"""
        map_file = "polyplot_map.html"
        if os.path.exists(map_file):
            webbrowser.open(map_file)
            self.update_status("Map opened in browser")
        else:
            messagebox.showwarning("File Not Found", "No map file found. Generate a map first.")

    def load_coordinates(self):
        """Load coordinates from file"""
        file_path = filedialog.askopenfilename(
            title="Load Coordinates",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.points_entry.delete("1.0", tk.END)
                self.points_entry.insert("1.0", content)
                self.update_status(f"Coordinates loaded from {Path(file_path).name}")
                try:
                    points_sets = self.parse_input(content)
                    self.update_summary(points_sets)
                except Exception:
                    self.update_summary([])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")

    def save_coordinates(self):
        """Save coordinates to file"""
        content = self.points_entry.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No data to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Coordinates",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.update_status(f"Coordinates saved to {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def export_to_kml(self):
        """Export to KML format"""
        messagebox.showinfo("KML Export", "KML export functionality will open in a separate window.")
        # self.open_kml_generator()

    def export_calculations(self):
        """Export calculation results to CSV"""
        try:
            points_sets = self.parse_input(self.points_entry.get("1.0", tk.END))
            if not points_sets:
                messagebox.showwarning("Error", "No data to export.")
                return

            file_path = filedialog.asksaveasfilename(
                title="Export Calculations",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if file_path:
                import csv
                zone, northern = self.get_coordinate_settings()
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Enclosure', 'Area (m²)', 'Area (ha)', 'Perimeter (m)',
                                     'Posts Needed', 'Mesh Length (m)', 'Mesh Rolls', 'Total Cost (FCFA)'])

                    for point_set in points_sets:
                        name = point_set.get('name', 'Unnamed')
                        points = point_set['points']
                        metrics = self.calculate_metrics(points, zone, northern)
                        if not metrics:
                            continue

                        writer.writerow([
                            name,
                            f"{metrics['area_m2']:.2f}",
                            f"{metrics['area_ha']:.2f}",
                            f"{metrics['perimeter_m']:.2f}",
                            metrics['nombre_piquets'],
                            f"{metrics['longueur_grillage']:.2f}",
                            metrics['nombre_rouleaux'],
                            f"{metrics['cout_total']:.2f}"
                        ])

                self.update_status(f"Calculations exported to {Path(file_path).name}")
                messagebox.showinfo("Success", f"Calculations exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export calculations:\n{str(e)}")

    def open_parameters(self):
        """Open parameters window"""
        ParametersWindow(self.root)

    def open_converter(self):
        """Open coordinate converter"""
        try:
            # open_converter_window_external()
            messagebox.showinfo("Converter", "Coordinate converter functionality will be available in the next update.")
        except:
            messagebox.showinfo("Converter", "Coordinate converter functionality will be available in the next update.")

    def open_kml_generator(self):
        """Open KML generator"""
        try:
            # open_kml_generator_window()
            messagebox.showinfo("KML Generator", "KML generator functionality will be available in the next update.")
        except:
            messagebox.showinfo("KML Generator", "KML generator functionality will be available in the next update.")

    def show_about(self):
        """Show about dialog"""
        about_text = f"""PolyPlot v{VERSION}

A modern application for polygon mapping and analysis.

Features:
• Interactive map generation
• Cost and area calculations
• Multiple coordinate format support
• KML export capabilities
• Professional reporting

© JojoLapin
Built with Python and modern GUI principles"""

        messagebox.showinfo("About PolyPlot", about_text)

    def on_country_change(self, event=None):
        """Update UTM zone when a country preset is selected"""
        country = getattr(self, 'country_var', None)
        if not country:
            return

        selected = country.get()
        if selected in COUNTRY_UTM_ZONES:
            self.zone_var.set(str(COUNTRY_UTM_ZONES[selected]))
            self.update_status(f"UTM zone set to {self.zone_var.get()} for {selected}")
        else:
            self.update_status("Custom UTM zone selected")
        self.refresh_summary_from_input()

    def on_zone_change(self, event=None):
        """Handle updates when the UTM zone combobox changes"""
        try:
            zone_value = int(self.zone_var.get())
            self.update_status(f"UTM zone set to {zone_value}")
        except (TypeError, ValueError):
            self.update_status("Invalid UTM zone selection")
        self.refresh_summary_from_input()

    def on_hemisphere_toggle(self):
        """Handle hemisphere toggles"""
        hemisphere = "Northern" if self.northern_var.get() else "Southern"
        self.update_status(f"Hemisphere set to {hemisphere}")
        self.refresh_summary_from_input()

    def get_coordinate_settings(self):
        """Return the currently selected UTM zone and hemisphere"""
        zone = 30
        northern = True

        if hasattr(self, 'zone_var'):
            try:
                zone = int(self.zone_var.get())
            except (TypeError, ValueError):
                zone = 30

        if hasattr(self, 'northern_var'):
            northern = bool(self.northern_var.get())

        return zone, northern

    def calculate_metrics(self, points, zone, northern):
        """Calculate geometric and cost metrics for an enclosure"""
        if len(points) < 3:
            return None

        utm_points = [latlon_to_utm(lat, lon, zone, northern) for lat, lon in points]
        polygon_utm = Polygon(utm_points)
        area_m2 = polygon_utm.area
        area_ha = area_m2 / 10000
        perimeter_m = polygon_utm.length

        distance_piquets = parameters.get("distance_piquets", 0) or 0
        cout_piquet = parameters.get("cout_piquet", 0) or 0
        cout_grillage = parameters.get("cout_grillage", 0) or 0

        if distance_piquets > 0:
            nombre_piquets = max(1, math.ceil(perimeter_m / distance_piquets) + 1)
        else:
            nombre_piquets = 0

        nombre_rouleaux = max(0, math.ceil(perimeter_m / 25))
        longueur_grillage = nombre_rouleaux * 25
        cout_total = nombre_piquets * cout_piquet + nombre_rouleaux * cout_grillage

        centroid = polygon_utm.centroid
        lat_c, lon_c = utm_to_wgs84(centroid.x, centroid.y, zone, northern)

        return {
            "area_m2": area_m2,
            "area_ha": area_ha,
            "perimeter_m": perimeter_m,
            "nombre_piquets": nombre_piquets,
            "nombre_rouleaux": nombre_rouleaux,
            "longueur_grillage": longueur_grillage,
            "cout_total": cout_total,
            "centroid_lat": lat_c,
            "centroid_lon": lon_c
        }

    def update_summary(self, points_sets):
        """Update the enclosure summary table and totals"""
        if not hasattr(self, 'summary_tree') or not hasattr(self, 'summary_totals_var'):
            return

        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        self.latest_summary_data = []
        self.latest_points_sets = points_sets or []

        if not points_sets:
            self.summary_totals_var.set("No data loaded.")
            return

        zone, northern = self.get_coordinate_settings()

        total_area = 0
        total_perimeter = 0
        total_posts = 0
        total_cost = 0

        for idx, point_set in enumerate(points_sets, start=1):
            name = point_set.get('name', f"Enclosure {idx}")
            points = point_set.get('points', [])
            metrics = self.calculate_metrics(points, zone, northern)
            if not metrics:
                continue

            total_area += metrics['area_ha']
            total_perimeter += metrics['perimeter_m']
            total_posts += metrics['nombre_piquets']
            total_cost += metrics['cout_total']

            self.summary_tree.insert(
                '',
                'end',
                values=(
                    name,
                    f"{metrics['area_ha']:.2f}",
                    f"{metrics['perimeter_m']:.2f}",
                    metrics['nombre_piquets'],
                    f"{metrics['cout_total']:.2f}"
                )
            )

            self.latest_summary_data.append({
                "name": name,
                **metrics
            })

        if self.latest_summary_data:
            self.summary_totals_var.set(
                f"Total area: {total_area:.2f} ha | Perimeter: {total_perimeter:.2f} m | "
                f"Posts: {total_posts} | Cost: {total_cost:.2f} FCFA"
            )
            self.update_status(
                f"Summary updated for {len(self.latest_summary_data)} enclosure(s)"
            )
        else:
            self.summary_totals_var.set("No valid enclosures found.")

    def copy_summary(self):
        """Copy summary data to clipboard"""
        if not self.latest_summary_data:
            messagebox.showwarning("Summary", "No summary data available to copy.")
            return

        lines = [
            "Enclosure\tArea (m²)\tArea (ha)\tPerimeter (m)\tPosts\tMesh (m)\tMesh Rolls\tCost (FCFA)"
        ]

        total_area_m2 = 0
        total_area_ha = 0
        total_perimeter = 0
        total_posts = 0
        total_mesh = 0
        total_rolls = 0
        total_cost = 0

        for entry in self.latest_summary_data:
            lines.append(
                f"{entry['name']}\t{entry['area_m2']:.2f}\t{entry['area_ha']:.2f}\t{entry['perimeter_m']:.2f}\t"
                f"{entry['nombre_piquets']}\t{entry['longueur_grillage']:.2f}\t"
                f"{entry['nombre_rouleaux']}\t{entry['cout_total']:.2f}"
            )

            total_area_m2 += entry['area_m2']
            total_area_ha += entry['area_ha']
            total_perimeter += entry['perimeter_m']
            total_posts += entry['nombre_piquets']
            total_mesh += entry['longueur_grillage']
            total_rolls += entry['nombre_rouleaux']
            total_cost += entry['cout_total']

        lines.append(
            f"TOTAL\t{total_area_m2:.2f}\t{total_area_ha:.2f}\t{total_perimeter:.2f}\t"
            f"{total_posts}\t{total_mesh:.2f}\t{total_rolls}\t{total_cost:.2f}"
        )

        summary_text = "\n".join(lines)
        try:
            pyperclip.copy(summary_text)
            self.update_status("Summary copied to clipboard")
        except pyperclip.PyperclipException:
            messagebox.showerror("Clipboard Error", "Unable to access the system clipboard.")

    def refresh_summary_from_input(self):
        """Re-parse current input and refresh the summary table"""
        if not hasattr(self, 'points_entry'):
            return

        try:
            points_sets = self.parse_input(self.points_entry.get("1.0", tk.END), show_warnings=False)
            if points_sets:
                self.update_summary(points_sets)
            else:
                self.update_summary([])
        except Exception:
            self.update_summary([])

    def parse_input(self, entry_text, show_warnings=True):
        """Parse coordinate input with enhanced error handling"""
        try:
            # Split the input by blank lines; each block is an enclosure.
            raw_sets = re.split(r'\n\s*\n', entry_text.strip())
            points_sets = []
            zone, northern = self.get_coordinate_settings()

            for raw_set in raw_sets:
                lines = raw_set.strip().split("\n")
                if not lines:
                    continue

                first_line = lines[0].strip()
                # If the first line doesn't begin with a digit, "(" or "[", treat it as the enclosure name.
                if not re.match(r'^[\(\[]?\s*-?\d', first_line):
                    name = first_line
                    coord_lines = lines[1:]
                else:
                    name = f"Enclosure {len(points_sets) + 1}"
                    coord_lines = lines

                points = []
                for line_num, line in enumerate(coord_lines, 1):
                    clean_line = line.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
                    # Skip the line if it does not contain any digits.
                    if not re.search(r'\d', clean_line):
                        continue

                    # Try comma separation first, then whitespace
                    parts = clean_line.split(",")
                    if len(parts) != 2:
                        parts = clean_line.split()

                    if len(parts) != 2:
                        continue

                    try:
                        val1 = float(parts[0].strip())
                        val2 = float(parts[1].strip())
                    except ValueError:
                        continue

                    # If both values are within typical lat/lon ranges, assume lat/lon.
                    if abs(val1) <= 90 and abs(val2) <= 180:
                        points.append((val1, val2))
                    else:
                        # Convert from UTM to lat/lon
                        lat, lon = utm_to_wgs84(val1, val2, zone=zone, northern=northern)
                        points.append((lat, lon))

                if len(points) >= 3:  # Need at least 3 points for a polygon
                    points_sets.append({"name": name, "points": points})
                elif points and show_warnings:
                    # Show warning for insufficient points
                    messagebox.showwarning(
                        "Warning",
                        f"Enclosure '{name}' has only {len(points)} point(s). "
                        f"At least 3 points are required for a polygon."
                    )

            return points_sets
        except Exception as e:
            raise Exception(f"Invalid format in coordinate input: {str(e)}")

    def add_points_to_map(self, mymap, points, show_markers, show_popups, show_custom_icons,
                          random_colors, label_prefix, name=None, zone=30, northern=True,
                          show_distance_markers=False):
        """Add points to map with enhanced visualization"""
        if not points:
            return mymap

        wgs84_coordinates = {f"{label_prefix}{i + 1}": pt for i, pt in enumerate(points)}

        for marker_name, coords in wgs84_coordinates.items():
            if coords not in self.global_point_map:
                self.global_point_map[coords] = set()
            self.global_point_map[coords].add(marker_name)

        line_points = list(wgs84_coordinates.values())
        line_points.append(line_points[0])  # Close the polygon

        metrics = self.calculate_metrics(points, zone, northern)
        if not metrics:
            return mymap

        area_m2 = metrics['area_m2']
        area_ha = metrics['area_ha']
        perimeter_m = metrics['perimeter_m']
        nombre_piquets = metrics['nombre_piquets']
        longueur_grillage = metrics['longueur_grillage']
        nombre_rouleaux = metrics['nombre_rouleaux']
        cout_total = metrics['cout_total']
        lat_c = metrics['centroid_lat']
        lon_c = metrics['centroid_lon']

        # Draw polygon outline
        folium.PolyLine(
            locations=line_points,
            color=COLORS['primary'],
            weight=3,
            opacity=0.8
        ).add_to(mymap)

        # Create detailed popup
        popup_text = f"""
        <div style="font-family: Segoe UI, sans-serif; min-width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: {COLORS['primary']};">{name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Center:</b></td><td>({lat_c:.6f}, {lon_c:.6f})</td></tr>
                <tr><td><b>Area:</b></td><td>{area_m2:.2f} m² ({area_ha:.2f} ha)</td></tr>
                <tr><td><b>Perimeter:</b></td><td>{perimeter_m:.2f} m</td></tr>
                <tr><td><b>Posts needed:</b></td><td>{nombre_piquets}</td></tr>
                <tr><td><b>Mesh length:</b></td><td>{longueur_grillage:.2f} m</td></tr>
                <tr><td><b>Mesh rolls:</b></td><td>{nombre_rouleaux}</td></tr>
                <tr><td><b>Total cost:</b></td><td>{cout_total:.2f} FCFA</td></tr>
            </table>
        </div>
        """

        # Add center marker with info
        folium.Marker(
            [lat_c, lon_c],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mymap)

        # Optional distance markers
        if show_distance_markers:
            for i in range(len(line_points) - 1):
                start = line_points[i]
                end = line_points[i + 1]
                midpoint = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
                distance = geodesic(start, end).meters

                point1_names = self.global_point_map.get(tuple(start), set())
                point2_names = self.global_point_map.get(tuple(end), set())

                folium.Marker(
                    location=midpoint,
                    popup=folium.Popup(
                        f"<div style='font-family: Segoe UI, sans-serif;'>"
                        f"<b>Distance:</b> {distance:.2f} m<br>"
                        f"<b>Between:</b> {' or '.join(point1_names)} and {' or '.join(point2_names)}"
                        f"</div>",
                        max_width=250
                    ),
                    icon=BeautifyIcon(
                        icon="ruler",
                        border_color=COLORS['secondary'],
                        text_color=COLORS['secondary'],
                        background_color="white",
                        border_width=2,
                        inner_icon_style="font-size:10px;"
                    )
                ).add_to(mymap)

        # Add markers for each point
        for point, (lat, lon) in wgs84_coordinates.items():
            popup_content = f"""
            <div style="font-family: Segoe UI, sans-serif;">
                <h5 style="margin: 0 0 5px 0; color: {COLORS['primary']};">{point}</h5>
                <b>WGS84:</b> ({lat:.6f}, {lon:.6f})
            """

            associated_names = self.global_point_map.get((lat, lon), set()) - {point}
            if associated_names:
                popup_content += f"<br><b>Also known as:</b> {', '.join(associated_names)}"
            popup_content += "</div>"

            if show_markers:
                folium.Marker(
                    location=(lat, lon),
                    popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.Icon(color='blue', icon='map-pin')
                ).add_to(mymap)

            if show_custom_icons:
                custom_icon = BeautifyIcon(
                    icon="star",
                    inner_icon_style=f"color:{COLORS['warning']};font-size:14px;",
                    border_color=COLORS['primary'],
                    background_color="white"
                )
                folium.Marker(
                    location=(lat, lon),
                    popup=folium.Popup(popup_content, max_width=250),
                    icon=custom_icon
                ).add_to(mymap)

        # Add filled polygon if popups are enabled
        if show_popups:
            if random_colors:
                poly_fill_color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
            else:
                poly_fill_color = COLORS['secondary']

            folium.Polygon(
                locations=line_points,
                color=COLORS['primary'],
                fill=True,
                fill_color=poly_fill_color,
                fill_opacity=0.3,
                weight=2
            ).add_to(mymap)

        return mymap

    def create_map(self, points_sets, show_markers, show_popups, show_custom_icons,
                   random_colors, show_distance_markers):
        """Create interactive map with enhanced features"""
        if not points_sets:
            messagebox.showwarning("Input Error", "No points sets provided.")
            return

        self.global_point_map.clear()
        zone, northern = self.get_coordinate_settings()

        # Calculate map center from all points
        all_points = []
        for point_set in points_sets:
            all_points.extend(point_set['points'])

        if not all_points:
            messagebox.showerror("Error", "No valid points found.")
            return

        map_center = [
            sum(pt[0] for pt in all_points) / len(all_points),
            sum(pt[1] for pt in all_points) / len(all_points)
        ]

        # Create map with modern tiles
        mymap = folium.Map(
            location=map_center,
            zoom_start=16,
            tiles='OpenStreetMap'
        )

        # Add satellite imagery option
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(mymap)

        # Add each enclosure to the map
        for idx, point_set in enumerate(points_sets):
            points = point_set['points']
            name = point_set.get('name', f"Enclosure {idx + 1}")
            label_prefix = chr(65 + idx)  # A, B, C, etc.

            mymap = self.add_points_to_map(
                mymap, points, show_markers, show_popups, show_custom_icons,
                random_colors, label_prefix, name=name,
                zone=zone, northern=northern,
                show_distance_markers=show_distance_markers
            )

        # Add layer control
        folium.LayerControl().add_to(mymap)

        # Add scale
        from folium.plugins import MeasureControl
        try:
            mymap.add_child(MeasureControl())
        except:
            pass  # MeasureControl might not be available

        # Save map
        map_filename = "polyplot_map.html"
        mymap.save(map_filename)

        # Show success message
        messagebox.showinfo(
            "Success",
            f"Map generated successfully!\n\nFile: {map_filename}\n"
            f"Enclosures: {len(points_sets)}\n"
            f"Total points: {len(all_points)}"
        )

        # Automatically open the map
        if messagebox.askyesno("Open Map", "Would you like to open the map in your browser?"):
            webbrowser.open(map_filename)

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main function to run the application"""
    app = PolyPlotApp()
    app.run()


if __name__ == "__main__":
    main()