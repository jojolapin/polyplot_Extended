import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pyproj import Transformer
import folium
import webbrowser
import pyperclip
from pathlib import Path
import csv

# Modern color scheme (matching main app)
COLORS = {
    'primary': '#2563eb',
    'primary_dark': '#1d4ed8',
    'secondary': '#10b981',
    'secondary_dark': '#059669',
    'background': '#f8fafc',
    'surface': '#ffffff',
    'text': '#1f2937',
    'text_light': '#6b7280',
    'border': '#e5e7eb',
    'error': '#ef4444',
    'warning': '#f59e0b',
    'success': '#10b981'
}

# Mapping of countries to approximate UTM zones
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
            font=('Segoe UI', 9, 'normal'),
            cursor='hand2',
            padx=16,
            pady=6,
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
                        relief='solid',
                        borderwidth=1)

        self.configure(style='Card.TFrame', padding=15)

        if title:
            title_label = ttk.Label(
                self,
                text=title,
                font=('Segoe UI', 11, 'bold'),
                foreground=COLORS['text']
            )
            title_label.pack(anchor='w', pady=(0, 10))


def utm_to_wgs84(easting, northing, zone=30, northern=True):
    """Convert UTM coordinates to WGS84 lat/lon"""
    transformer = Transformer.from_crs(
        f"+proj=utm +zone={zone} +ellps=WGS84 +north={int(northern)}",
        "EPSG:4326",
        always_xy=True
    )
    lon, lat = transformer.transform(easting, northing)
    return lat, lon


def latlon_to_utm(lat, lon, zone=30, northern=True):
    """Convert WGS84 lat/lon to UTM coordinates"""
    target_epsg = 32600 + zone if northern else 32700 + zone
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{target_epsg}", always_xy=True)
    easting, northing = transformer.transform(lon, lat)
    return easting, northing


class CoordinateConverterApp:
    """Enhanced Coordinate Converter with modern GUI"""

    def __init__(self, parent=None):
        # Create the converter window
        if parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
        else:
            self.window = tk.Tk()

        self.window.title("Coordinate Converter - UTM ↔ Lat/Lon (WGS84)")
        self.window.geometry("800x600")
        self.window.configure(bg=COLORS['background'])

        # Configure modern styles
        self.setup_styles()

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

        # Configure label styles
        style.configure('Title.TLabel',
                        background=COLORS['background'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 16, 'bold'))

        style.configure('Subtitle.TLabel',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 10, 'bold'))

        style.configure('Body.TLabel',
                        background=COLORS['surface'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 9))

        # Configure combobox styles
        style.configure('Modern.TCombobox',
                        font=('Segoe UI', 9))

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_container = ttk.Frame(self.window, style='Main.TFrame', padding=20)
        main_container.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(
            main_container,
            text="Coordinate Converter",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 20))

        # Configuration section
        config_card = ModernCard(main_container, title="Configuration")
        config_card.pack(fill='x', pady=(0, 15))

        self.setup_config_section(config_card)

        # Input/Output section
        content_frame = ttk.Frame(main_container, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True)

        # Input section
        input_card = ModernCard(content_frame, title="Input Coordinates")
        input_card.pack(side='left', fill='both', expand=True, padx=(0, 7))

        self.setup_input_section(input_card)

        # Output section
        output_card = ModernCard(content_frame, title="Converted Coordinates")
        output_card.pack(side='right', fill='both', expand=True, padx=(7, 0))

        self.setup_output_section(output_card)

        # Action buttons
        action_frame = ttk.Frame(main_container, style='Main.TFrame')
        action_frame.pack(fill='x', pady=(15, 0))

        self.setup_action_buttons(action_frame)

        # Status bar
        self.setup_status_bar(main_container)

    def setup_config_section(self, parent):
        """Setup configuration options"""
        config_frame = ttk.Frame(parent)
        config_frame.pack(fill='x')

        # Hemisphere selection
        hemisphere_frame = ttk.Frame(config_frame)
        hemisphere_frame.pack(side='left', padx=(0, 20))

        ttk.Label(hemisphere_frame, text="Hemisphere:", style='Body.TLabel').pack(anchor='w')

        hemisphere_inner = ttk.Frame(hemisphere_frame)
        hemisphere_inner.pack(fill='x', pady=(5, 0))

        self.hemisphere_var = tk.StringVar(value="Northern")
        ttk.Radiobutton(hemisphere_inner, text="Northern", variable=self.hemisphere_var,
                        value="Northern", style='Modern.TRadiobutton').pack(side='left', padx=(0, 10))
        ttk.Radiobutton(hemisphere_inner, text="Southern", variable=self.hemisphere_var,
                        value="Southern", style='Modern.TRadiobutton').pack(side='left')

        # Country/Zone selection
        country_frame = ttk.Frame(config_frame)
        country_frame.pack(side='left', fill='x', expand=True)

        ttk.Label(country_frame, text="Select Country/Region:", style='Body.TLabel').pack(anchor='w')

        self.country_combobox = ttk.Combobox(
            country_frame,
            values=list(COUNTRY_UTM_ZONES.keys()),
            state="readonly",
            style='Modern.TCombobox'
        )
        self.country_combobox.set("Burkina Faso")
        self.country_combobox.pack(fill='x', pady=(5, 0))

        # Manual zone entry
        zone_frame = ttk.Frame(config_frame)
        zone_frame.pack(side='right', padx=(20, 0))

        ttk.Label(zone_frame, text="Manual UTM Zone:", style='Body.TLabel').pack(anchor='w')

        self.manual_zone_var = tk.StringVar()
        self.manual_zone_entry = ttk.Entry(zone_frame, textvariable=self.manual_zone_var, width=10)
        self.manual_zone_entry.pack(pady=(5, 0))

        # Tooltip
        tooltip_label = ttk.Label(
            parent,
            text="💡 Enter coordinates one pair per line. Separate different groups with blank lines.",
            style='Body.TLabel',
            foreground=COLORS['text_light']
        )
        tooltip_label.pack(pady=(10, 0))

    def setup_input_section(self, parent):
        """Setup input text area"""
        # Instructions
        instruction_text = (
            "Supported formats:\n"
            "• Lat/Lon: 12.3456, -1.5234\n"
            "• UTM: 654321.0, 1234567.0\n"
            "• With brackets: [12.3456, -1.5234]\n"
            "• With parentheses: (654321, 1234567)"
        )

        instructions = ttk.Label(
            parent,
            text=instruction_text,
            style='Body.TLabel',
            justify='left'
        )
        instructions.pack(anchor='w', pady=(0, 10))

        # Text input area with scrollbar
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.input_area = tk.Text(
            text_frame,
            font=('Consolas', 9),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            selectbackground=COLORS['primary'],
            relief='solid',
            borderwidth=1,
            wrap='word',
            height=12
        )

        input_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.input_area.yview)
        self.input_area.configure(yscrollcommand=input_scrollbar.set)

        self.input_area.pack(side='left', fill='both', expand=True)
        input_scrollbar.pack(side='right', fill='y')

        # Sample data button
        sample_btn = ModernButton(
            parent,
            "Load Sample Data",
            command=self.load_sample_data,
            style='outline'
        )
        sample_btn.pack(pady=(10, 0), fill='x')

    def setup_output_section(self, parent):
        """Setup output text area"""
        # Output controls
        output_controls = ttk.Frame(parent)
        output_controls.pack(fill='x', pady=(0, 10))

        ttk.Label(output_controls, text="Converted results:", style='Body.TLabel').pack(side='left')

        # Precision control
        precision_frame = ttk.Frame(output_controls)
        precision_frame.pack(side='right')

        ttk.Label(precision_frame, text="Precision:", style='Body.TLabel').pack(side='left', padx=(0, 5))

        self.precision_var = tk.StringVar(value="6")
        precision_combo = ttk.Combobox(
            precision_frame,
            textvariable=self.precision_var,
            values=["2", "4", "6", "8"],
            width=3,
            state="readonly"
        )
        precision_combo.pack(side='left')

        # Text output area with scrollbar
        output_text_frame = ttk.Frame(parent)
        output_text_frame.pack(fill='both', expand=True)

        self.output_area = tk.Text(
            output_text_frame,
            font=('Consolas', 9),
            bg=COLORS['background'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            selectbackground=COLORS['primary'],
            relief='solid',
            borderwidth=1,
            wrap='word',
            height=12,
            state='disabled'
        )

        output_scrollbar = ttk.Scrollbar(output_text_frame, orient='vertical', command=self.output_area.yview)
        self.output_area.configure(yscrollcommand=output_scrollbar.set)

        self.output_area.pack(side='left', fill='both', expand=True)
        output_scrollbar.pack(side='right', fill='y')

        # Output actions
        output_actions = ttk.Frame(parent)
        output_actions.pack(fill='x', pady=(10, 0))

        copy_btn = ModernButton(
            output_actions,
            "Copy Results",
            command=self.copy_to_clipboard,
            style='secondary'
        )
        copy_btn.pack(side='left', padx=(0, 5))

        save_btn = ModernButton(
            output_actions,
            "Save to File",
            command=self.save_results,
            style='outline'
        )
        save_btn.pack(side='left')

    def setup_action_buttons(self, parent):
        """Setup main action buttons"""
        # Left side - file operations
        file_frame = ttk.Frame(parent)
        file_frame.pack(side='left')

        load_btn = ModernButton(
            file_frame,
            "Load from File",
            command=self.load_from_file,
            style='outline'
        )
        load_btn.pack(side='left', padx=(0, 5))

        clear_btn = ModernButton(
            file_frame,
            "Clear All",
            command=self.clear_all,
            style='outline'
        )
        clear_btn.pack(side='left')

        # Center - main convert button
        convert_btn = ModernButton(
            parent,
            "🔄 Convert Coordinates",
            command=self.convert_coords,
            style='primary'
        )
        convert_btn.pack(padx=20)

        # Right side - map operations
        map_frame = ttk.Frame(parent)
        map_frame.pack(side='right')

        map_btn = ModernButton(
            map_frame,
            "📍 View on Map",
            command=self.open_map,
            style='secondary'
        )
        map_btn.pack(side='left', padx=(0, 5))

        export_btn = ModernButton(
            map_frame,
            "💾 Export CSV",
            command=self.export_csv,
            style='outline'
        )
        export_btn.pack(side='left')

    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent, style='Main.TFrame')
        status_frame.pack(fill='x', pady=(15, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="Ready - Enter coordinates and click Convert",
            style='Body.TLabel',
            foreground=COLORS['text_light']
        )
        self.status_label.pack(side='left')

        # Conversion count
        self.count_label = ttk.Label(
            status_frame,
            text="",
            style='Body.TLabel',
            foreground=COLORS['text_light']
        )
        self.count_label.pack(side='right')

    def update_status(self, message, count=None):
        """Update status bar"""
        self.status_label.config(text=message)
        if count is not None:
            self.count_label.config(text=f"Converted: {count} coordinates")
        self.window.update_idletasks()

    def load_sample_data(self):
        """Load sample coordinate data"""
        sample_data = """Sample Locations
12.3456, -1.5234
12.3466, -1.5234
12.3466, -1.5244

UTM Coordinates
654321.0, 1234567.0
654331.0, 1234567.0
654331.0, 1234577.0"""

        self.input_area.delete("1.0", tk.END)
        self.input_area.insert("1.0", sample_data)
        self.update_status("Sample data loaded")

    def clear_all(self):
        """Clear all input and output"""
        if messagebox.askyesno("Confirm", "Clear all data?", parent=self.window):
            self.input_area.delete("1.0", tk.END)
            self.output_area.config(state='normal')
            self.output_area.delete("1.0", tk.END)
            self.output_area.config(state='disabled')
            self.update_status("Data cleared")

    def load_from_file(self):
        """Load coordinates from file"""
        file_path = filedialog.askopenfilename(
            title="Load Coordinates",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
            parent=self.window
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_area.delete("1.0", tk.END)
                self.input_area.insert("1.0", content)
                self.update_status(f"Loaded coordinates from {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}", parent=self.window)

    def save_results(self):
        """Save converted results to file"""
        content = self.output_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No results to save.", parent=self.window)
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            parent=self.window
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.update_status(f"Results saved to {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}", parent=self.window)

    def copy_to_clipboard(self):
        """Copy results to clipboard"""
        text = self.output_area.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.update_status("Results copied to clipboard")
            messagebox.showinfo("Success", "Results copied to clipboard!", parent=self.window)
        else:
            messagebox.showwarning("Warning", "No results to copy.", parent=self.window)

    def export_csv(self):
        """Export coordinates to CSV format"""
        try:
            coordinates = self.parse_and_convert_coordinates(export_mode=True)
            if not coordinates:
                messagebox.showwarning("Warning", "No coordinates to export.", parent=self.window)
                return

            file_path = filedialog.asksaveasfilename(
                title="Export to CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                parent=self.window
            )

            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Group', 'Original_X', 'Original_Y', 'Converted_X', 'Converted_Y', 'Type'])

                    for group_name, coords in coordinates.items():
                        for orig, conv, coord_type in coords:
                            writer.writerow([group_name, orig[0], orig[1], conv[0], conv[1], coord_type])

                self.update_status(f"CSV exported to {Path(file_path).name}")
                messagebox.showinfo("Success", f"Coordinates exported to:\n{file_path}", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{str(e)}", parent=self.window)

    def get_utm_zone_from_input(self, user_input):
        """Get UTM zone from country selection or manual entry"""
        manual_zone = self.manual_zone_var.get().strip()
        if manual_zone:
            try:
                return int(manual_zone)
            except ValueError:
                pass

        return COUNTRY_UTM_ZONES.get(user_input.strip(), 30)

    def detect_utm_zone(self, lon):
        """Automatically detect UTM zone from longitude"""
        return int((lon + 180) / 6) + 1

    def clean_input(self, line):
        """Clean coordinate input line"""
        return re.sub(r'[\[\]()]', '', line).strip()

    def parse_and_convert_coordinates(self, export_mode=False):
        """Parse input and convert coordinates"""
        input_text = self.input_area.get("1.0", tk.END).strip()
        if not input_text:
            return {} if export_mode else []

        is_northern = (self.hemisphere_var.get() == "Northern")
        user_zone = self.get_utm_zone_from_input(self.country_combobox.get().strip())
        precision = int(self.precision_var.get())

        results = {} if export_mode else []
        converted_count = 0

        # Split by blank lines to separate groups
        blocks = re.split(r'\n\s*\n', input_text)

        for block_idx, block in enumerate(blocks):
            lines = block.strip().splitlines()
            if not lines:
                continue

            first_line = lines[0].strip()
            # If the first line doesn't start with a digit, "(" or "[", treat it as the block name
            if not re.match(r'^[\(\[]?\s*-?\d', first_line):
                block_name = first_line
                coord_lines = lines[1:]
            else:
                block_name = f"Group {block_idx + 1}"
                coord_lines = lines

            block_results = [] if not export_mode else []
            group_coords = [] if export_mode else None

            if not export_mode:
                block_results.append(f"=== {block_name} ===")

            for line in coord_lines:
                cleaned_line = self.clean_input(line)
                if not re.search(r'\d', cleaned_line):
                    continue

                # Try comma separation first, then whitespace
                parts = cleaned_line.split(",")
                if len(parts) < 2:
                    parts = cleaned_line.split()
                if len(parts) < 2:
                    continue

                try:
                    val1, val2 = float(parts[0].strip()), float(parts[1].strip())
                except (ValueError, IndexError):
                    if not export_mode:
                        block_results.append(f"Error: Could not parse '{line}'")
                    continue

                # Determine coordinate type and convert
                if abs(val1) <= 90 and abs(val2) <= 180:
                    # Lat/Lon to UTM
                    zone_to_use = self.detect_utm_zone(val2)
                    easting, northing = latlon_to_utm(val1, val2, zone=zone_to_use, northern=is_northern)

                    if export_mode:
                        group_coords.append(((val1, val2), (easting, northing), "LatLon→UTM"))
                    else:
                        block_results.append(
                            f"({easting:.{precision}f}, {northing:.{precision}f}) [Zone {zone_to_use}{'N' if is_northern else 'S'}]")
                else:
                    # UTM to Lat/Lon
                    zone_to_use = user_zone if user_zone is not None else 30
                    lat_conv, lon_conv = utm_to_wgs84(val1, val2, zone=zone_to_use, northern=is_northern)

                    if export_mode:
                        group_coords.append(((val1, val2), (lat_conv, lon_conv), "UTM→LatLon"))
                    else:
                        block_results.append(f"({lat_conv:.{precision + 2}f}, {lon_conv:.{precision + 2}f}) [WGS84]")

                converted_count += 1

            if export_mode:
                if group_coords:
                    results[block_name] = group_coords
            else:
                if len(block_results) > 1:  # More than just the header
                    results.append("\n".join(block_results))

        return results if export_mode else (results, converted_count)

    def convert_coords(self):
        """Main coordinate conversion function"""
        try:
            self.update_status("Converting coordinates...")

            results, converted_count = self.parse_and_convert_coordinates()

            # Update output area
            self.output_area.config(state='normal')
            self.output_area.delete("1.0", tk.END)

            if results:
                self.output_area.insert(tk.END, "\n\n".join(results))
                self.update_status("Conversion completed successfully", converted_count)
            else:
                self.output_area.insert(tk.END, "No valid coordinates found to convert.")
                self.update_status("No valid coordinates found")

            self.output_area.config(state='disabled')

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Error during conversion:\n{str(e)}", parent=self.window)
            self.update_status("Conversion failed")

    def open_map(self):
        """Create and open map with converted coordinates"""
        try:
            coordinates = self.parse_and_convert_coordinates(export_mode=True)
            if not coordinates:
                messagebox.showwarning("Warning", "No coordinates to display on map.", parent=self.window)
                return

            # Create map
            all_coords = []
            for group_coords in coordinates.values():
                for _, (lat_or_x, lon_or_y), coord_type in group_coords:
                    if "LatLon" in coord_type:
                        all_coords.append((lat_or_x, lon_or_y))
                    else:
                        # This is a converted result, we need the original lat/lon
                        # For now, just use the converted result
                        all_coords.append((lat_or_x, lon_or_y))

            if not all_coords:
                messagebox.showwarning("Warning", "No valid coordinates for mapping.", parent=self.window)
                return

            # Calculate center
            center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
            center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)

            # Create map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

            # Add markers for each group
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue',
                      'darkgreen']

            for idx, (group_name, group_coords) in enumerate(coordinates.items()):
                color = colors[idx % len(colors)]

                for orig, conv, coord_type in group_coords:
                    if "→LatLon" in coord_type:
                        # Show converted lat/lon
                        lat, lon = conv
                        popup_text = f"""
                        <b>{group_name}</b><br>
                        Type: {coord_type}<br>
                        Original: ({orig[0]:.2f}, {orig[1]:.2f})<br>
                        Converted: ({lat:.6f}, {lon:.6f})
                        """
                    else:
                        # Show original lat/lon
                        lat, lon = orig
                        popup_text = f"""
                        <b>{group_name}</b><br>
                        Type: {coord_type}<br>
                        Coordinates: ({lat:.6f}, {lon:.6f})<br>
                        Converted: ({conv[0]:.2f}, {conv[1]:.2f})
                        """

                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_text, max_width=250),
                        icon=folium.Icon(color=color, icon='map-pin')
                    ).add_to(m)

            # Save and open map
            map_filename = "coordinate_converter_map.html"
            m.save(map_filename)
            webbrowser.open(map_filename)

            self.update_status(f"Map created with {len(all_coords)} points")

        except Exception as e:
            messagebox.showerror("Map Error", f"Error creating map:\n{str(e)}", parent=self.window)

    def run(self):
        """Start the application"""
        self.window.mainloop()


def open_converter_window():
    """Function to open converter window (for external calls)"""
    app = CoordinateConverterApp()
    app.run()


def main():
    """Main function"""
    app = CoordinateConverterApp()
    app.run()


if __name__ == "__main__":
    main()