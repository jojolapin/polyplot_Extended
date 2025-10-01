import folium
from folium.plugins import BeautifyIcon
from pyproj import Transformer
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog, scrolledtext
from shapely.geometry import Polygon
from geopy.distance import geodesic
import random
import re
import pyperclip
import webbrowser
from pathlib import Path
import xml.etree.ElementTree as ET

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


class ColorPicker(ttk.Frame):
    """Modern color picker widget"""

    def __init__(self, parent, label_text, initial_color="#80000000", **kwargs):
        super().__init__(parent, **kwargs)

        self.color = initial_color

        # Label
        ttk.Label(self, text=label_text, font=('Segoe UI', 9)).pack(side='left', padx=(0, 10))

        # Color preview
        self.color_frame = tk.Frame(self, width=30, height=20, relief='solid', borderwidth=1)
        self.color_frame.pack(side='left', padx=(0, 10))
        self.update_color_preview()

        # Pick button
        pick_btn = ModernButton(self, "Pick Color", command=self.pick_color, style='outline')
        pick_btn.pack(side='left')

        # Transparency slider
        ttk.Label(self, text="Opacity:", font=('Segoe UI', 9)).pack(side='left', padx=(10, 5))

        self.opacity_var = tk.DoubleVar(value=0.5)
        self.opacity_scale = ttk.Scale(
            self,
            from_=0.0,
            to=1.0,
            variable=self.opacity_var,
            orient='horizontal',
            length=100,
            command=self.update_opacity
        )
        self.opacity_scale.pack(side='left', padx=(0, 5))

        # Opacity label
        self.opacity_label = ttk.Label(self, text="50%", font=('Segoe UI', 9))
        self.opacity_label.pack(side='left')

    def update_color_preview(self):
        """Update color preview"""
        # Extract RGB from KML AABBGGRR format
        if len(self.color) == 9 and self.color.startswith('#'):
            bb = self.color[3:5]
            gg = self.color[5:7]
            rr = self.color[7:9]
            rgb_color = f"#{rr}{gg}{bb}"
        else:
            rgb_color = "#000000"

        self.color_frame.config(bg=rgb_color)

    def pick_color(self):
        """Open color picker dialog"""
        color = colorchooser.askcolor()[1]
        if color:
            self.set_color(color)

    def set_color(self, hex_color):
        """Set color and update preview"""
        opacity = int(self.opacity_var.get() * 255)
        self.color = self.convert_to_kml_color(hex_color, opacity)
        self.update_color_preview()

    def update_opacity(self, value):
        """Update opacity"""
        opacity_percent = int(float(value) * 100)
        self.opacity_label.config(text=f"{opacity_percent}%")

        # Update color with new opacity
        if len(self.color) == 9:
            opacity_hex = format(int(float(value) * 255), '02x')
            self.color = f"#{opacity_hex}{self.color[3:]}"

    def convert_to_kml_color(self, hex_color, opacity=128):
        """Convert hex color to KML AABBGGRR format"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "#80000000"

        rr = hex_color[0:2]
        gg = hex_color[2:4]
        bb = hex_color[4:6]
        aa = format(opacity, '02x')

        return f"#{aa}{bb}{gg}{rr}"

    def get_color(self):
        """Get current KML color"""
        return self.color


def convert_utm_to_latlon(easting, northing, zone=30):
    """Convert UTM to Lat/Lon"""
    transformer = Transformer.from_crs("EPSG:32630", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return lat, lon


class KMLGeneratorApp:
    """Enhanced KML Generator with modern GUI"""

    def __init__(self, parent=None):
        # Create the window
        if parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
        else:
            self.window = tk.Tk()

        self.window.title("KML Generator for Enclosures")
        self.window.geometry("900x700")
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
            text="KML Generator for Enclosures",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 20))

        # Content area
        content_frame = ttk.Frame(main_container, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True)

        # Left panel - Input
        left_panel = ModernCard(content_frame, title="Coordinate Input")
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.setup_input_panel(left_panel)

        # Right panel - Settings
        right_panel = ModernCard(content_frame, title="KML Settings")
        right_panel.pack(side='right', fill='y', padx=(10, 0))

        self.setup_settings_panel(right_panel)

        # Bottom panel - Actions
        bottom_panel = ttk.Frame(main_container, style='Main.TFrame')
        bottom_panel.pack(fill='x', pady=(20, 0))

        self.setup_action_panel(bottom_panel)

        # Status bar
        self.setup_status_bar(main_container)

    def setup_input_panel(self, parent):
        """Setup coordinate input panel"""
        # Instructions
        instructions = ttk.Label(
            parent,
            text="Enter coordinates for each enclosure.\nSeparate enclosures with blank lines.\nSupports both Lat/Lon and UTM formats (Zone 30 assumed for UTM).",
            style='Body.TLabel',
            justify='left'
        )
        instructions.pack(anchor='w', pady=(0, 10))

        # Text input area
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.coord_text = tk.Text(
            text_frame,
            font=('Consolas', 9),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            selectbackground=COLORS['primary'],
            relief='solid',
            borderwidth=1,
            wrap='word',
            height=15
        )

        # Scrollbar for text area
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.coord_text.yview)
        self.coord_text.configure(yscrollcommand=scrollbar.set)

        self.coord_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Input actions
        input_actions = ttk.Frame(parent)
        input_actions.pack(fill='x', pady=(10, 0))

        sample_btn = ModernButton(
            input_actions,
            "Load Sample",
            command=self.load_sample_data,
            style='outline'
        )
        sample_btn.pack(side='left', padx=(0, 5))

        load_btn = ModernButton(
            input_actions,
            "Load File",
            command=self.load_from_file,
            style='outline'
        )
        load_btn.pack(side='left', padx=(0, 5))

        clear_btn = ModernButton(
            input_actions,
            "Clear",
            command=self.clear_input,
            style='outline'
        )
        clear_btn.pack(side='left')

        validate_btn = ModernButton(
            input_actions,
            "Validate",
            command=self.validate_input,
            style='secondary'
        )
        validate_btn.pack(side='right')

    def setup_settings_panel(self, parent):
        """Setup KML settings panel"""
        # Style settings
        style_frame = ttk.LabelFrame(parent, text="Visual Style", padding=10)
        style_frame.pack(fill='x', pady=(0, 15))

        # Fill color picker
        self.fill_color_picker = ColorPicker(
            style_frame,
            "Fill Color:",
            "#80FF0000"  # Semi-transparent red
        )
        self.fill_color_picker.pack(fill='x', pady=(0, 10))

        # Outline color picker
        self.outline_color_picker = ColorPicker(
            style_frame,
            "Outline Color:",
            "#FF0000FF"  # Solid blue
        )
        self.outline_color_picker.pack(fill='x')

        # Animation settings
        animation_frame = ttk.LabelFrame(parent, text="Tour Animation", padding=10)
        animation_frame.pack(fill='x', pady=(0, 15))

        self.include_tour_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            animation_frame,
            text="Include flythrough tour",
            variable=self.include_tour_var
        ).pack(anchor='w', pady=(0, 5))

        # Tour duration
        duration_frame = ttk.Frame(animation_frame)
        duration_frame.pack(fill='x', pady=(0, 5))

        ttk.Label(duration_frame, text="Duration per enclosure (seconds):", style='Body.TLabel').pack(anchor='w')

        self.tour_duration_var = tk.DoubleVar(value=5.0)
        duration_scale = ttk.Scale(
            duration_frame,
            from_=1.0,
            to=15.0,
            variable=self.tour_duration_var,
            orient='horizontal'
        )
        duration_scale.pack(fill='x', pady=(2, 0))

        # Altitude setting
        altitude_frame = ttk.Frame(animation_frame)
        altitude_frame.pack(fill='x')

        ttk.Label(altitude_frame, text="Camera altitude (meters):", style='Body.TLabel').pack(anchor='w')

        self.altitude_var = tk.IntVar(value=800)
        altitude_scale = ttk.Scale(
            altitude_frame,
            from_=200,
            to=2000,
            variable=self.altitude_var,
            orient='horizontal'
        )
        altitude_scale.pack(fill='x', pady=(2, 0))

        # Export options
        export_frame = ttk.LabelFrame(parent, text="Export Options", padding=10)
        export_frame.pack(fill='x')

        self.include_ground_overlay_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            export_frame,
            text="Include ground overlay",
            variable=self.include_ground_overlay_var
        ).pack(anchor='w', pady=(0, 5))

        self.compress_coordinates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            export_frame,
            text="Compress coordinates",
            variable=self.compress_coordinates_var
        ).pack(anchor='w')

    def setup_action_panel(self, parent):
        """Setup action buttons panel"""
        action_frame = ttk.Frame(parent, style='Main.TFrame')
        action_frame.pack(fill='x')

        # Preview button
        preview_btn = ModernButton(
            action_frame,
            "🗺️ Preview on Map",
            command=self.preview_map,
            style='outline'
        )
        preview_btn.pack(side='left', padx=(0, 10))

        # Generate KML button
        generate_btn = ModernButton(
            action_frame,
            "📄 Generate KML",
            command=self.generate_kml,
            style='primary'
        )
        generate_btn.pack(side='right', padx=(10, 0))

        # Export options
        export_geojson_btn = ModernButton(
            action_frame,
            "📊 Export GeoJSON",
            command=self.export_geojson,
            style='secondary'
        )
        export_geojson_btn.pack(side='right')

    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent, style='Main.TFrame')
        status_frame.pack(fill='x', pady=(15, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="Ready - Enter coordinates and configure settings",
            style='Body.TLabel',
            foreground=COLORS['text_light']
        )
        self.status_label.pack(side='left')

        # Enclosure count
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
            self.count_label.config(text=f"Enclosures: {count}")
        self.window.update_idletasks()

    def load_sample_data(self):
        """Load sample coordinate data"""
        sample_data = """Farm Field 1
12.3456, -1.5234
12.3466, -1.5234
12.3466, -1.5244
12.3456, -1.5244

Livestock Area
12.3500, -1.5300
12.3520, -1.5300
12.3520, -1.5320
12.3500, -1.5320

Storage Compound
654321.0, 1234567.0
654341.0, 1234567.0
654341.0, 1234587.0
654321.0, 1234587.0"""

        self.coord_text.delete("1.0", tk.END)
        self.coord_text.insert("1.0", sample_data)
        self.update_status("Sample data loaded")

    def clear_input(self):
        """Clear input data"""
        if messagebox.askyesno("Confirm", "Clear all input data?", parent=self.window):
            self.coord_text.delete("1.0", tk.END)
            self.update_status("Input cleared")

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
                self.coord_text.delete("1.0", tk.END)
                self.coord_text.insert("1.0", content)
                self.update_status(f"Loaded from {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}", parent=self.window)

    def validate_input(self):
        """Validate coordinate input"""
        try:
            enclosures = self.parse_input(self.coord_text.get("1.0", tk.END).strip())
            if enclosures:
                total_points = sum(len(coords) for coords in enclosures.values())
                messagebox.showinfo(
                    "Validation Result",
                    f"✓ Input is valid!\n\n"
                    f"Found {len(enclosures)} enclosure(s)\n"
                    f"Total points: {total_points}",
                    parent=self.window
                )
                self.update_status("Validation successful", len(enclosures))
            else:
                messagebox.showwarning("Validation Result", "No valid coordinate data found.", parent=self.window)
                self.update_status("Validation failed: No valid data")
        except Exception as e:
            messagebox.showerror("Validation Error", f"Input validation failed:\n{str(e)}", parent=self.window)
            self.update_status("Validation failed: Invalid format")

    def parse_input(self, entry_text):
        """Parse coordinate input"""
        try:
            # Split input by blank lines; each block is an enclosure
            raw_sets = re.split(r'\n\s*\n', entry_text.strip())
            points_sets = {}

            for raw_set in raw_sets:
                lines = raw_set.strip().split("\n")
                if not lines:
                    continue

                first_line = lines[0].strip()
                # If the first line doesn't start with coordinates, treat it as the name
                if not (first_line.startswith("(") or first_line.startswith("[") or first_line[0].isdigit()):
                    name = first_line
                    coord_lines = lines[1:]
                else:
                    name = f"Enclosure {len(points_sets) + 1}"
                    coord_lines = lines

                coords_list = []
                for line in coord_lines:
                    line = line.strip().replace("(", "").replace(")", "").replace("[", "").replace("]", "")
                    parts = line.split(",")
                    if len(parts) != 2:
                        continue
                    try:
                        val1 = float(parts[0].strip())
                        val2 = float(parts[1].strip())
                    except ValueError:
                        continue

                    # Check if coordinates are lat/lon or UTM
                    if abs(val1) <= 90 and abs(val2) <= 180:
                        coords_list.append((val1, val2))
                    else:
                        # Convert UTM to lat/lon
                        lat, lon = convert_utm_to_latlon(val1, val2, zone=30)
                        coords_list.append((lat, lon))

                if len(coords_list) >= 3:  # Need at least 3 points for a polygon
                    points_sets[name] = coords_list
                elif coords_list:
                    messagebox.showwarning(
                        "Warning",
                        f"Enclosure '{name}' has only {len(coords_list)} point(s). "
                        f"At least 3 points are required.",
                        parent=self.window
                    )

            return points_sets
        except Exception as e:
            raise Exception(f"Invalid format: {e}")

    def preview_map(self):
        """Create and open preview map"""
        try:
            enclosures = self.parse_input(self.coord_text.get("1.0", tk.END).strip())
            if not enclosures:
                messagebox.showwarning("Warning", "No valid enclosures to preview.", parent=self.window)
                return

            # Calculate center
            all_coords = []
            for coords in enclosures.values():
                all_coords.extend(coords)

            center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
            center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)

            # Create map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

            # Add enclosures
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']

            for idx, (name, coords) in enumerate(enclosures.items()):
                color = colors[idx % len(colors)]

                # Close the polygon
                polygon_coords = coords + [coords[0]]

                # Add polygon
                folium.Polygon(
                    locations=polygon_coords,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.3,
                    popup=folium.Popup(f"<b>{name}</b><br>Points: {len(coords)}", max_width=200)
                ).add_to(m)

                # Add markers for vertices
                for i, (lat, lon) in enumerate(coords):
                    folium.Marker(
                        [lat, lon],
                        popup=f"{name} - Point {i + 1}",
                        icon=folium.Icon(color=color, icon='map-pin')
                    ).add_to(m)

            # Save and open map
            map_filename = "kml_preview_map.html"
            m.save(map_filename)
            webbrowser.open(map_filename)

            self.update_status(f"Preview map created with {len(enclosures)} enclosures")

        except Exception as e:
            messagebox.showerror("Preview Error", f"Error creating preview:\n{str(e)}", parent=self.window)

    def generate_kml_content(self, enclosures, fill_color, outline_color, include_tour=True):
        """Generate KML content"""
        kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" 
     xmlns:gx="http://www.google.com/kml/ext/2.2">
<Document>
    <name>Enclosures</name>
    <description>Generated by PolyPlot KML Creator</description>
    <open>1</open>
'''

        kml_footer = '''
</Document>
</kml>
'''

        kml_body = ""

        # Add style definitions
        kml_body += f'''
    <Style id="enclosureStyle">
        <LineStyle>
            <color>{outline_color}</color>
            <width>3</width>
        </LineStyle>
        <PolyStyle>
            <color>{fill_color}</color>
            <outline>1</outline>
        </PolyStyle>
        <LabelStyle>
            <scale>1.2</scale>
        </LabelStyle>
    </Style>
'''

        # Add placemarks for each enclosure
        for name, coords in enclosures.items():
            kml_body += f'''
    <Placemark>
        <name>{name}</name>
        <description>
            <![CDATA[
            <b>Enclosure:</b> {name}<br/>
            <b>Points:</b> {len(coords)}<br/>
            <b>Created:</b> {self.get_timestamp()}
            ]]>
        </description>
        <styleUrl>#enclosureStyle</styleUrl>
        <Polygon>
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>
'''

            # Add coordinates
            for lat, lon in coords:
                kml_body += f"                        {lon:.8f},{lat:.8f},0\n"

            # Close the polygon
            first_lat, first_lon = coords[0]
            kml_body += f"                        {first_lon:.8f},{first_lat:.8f},0\n"

            kml_body += '''                    </coordinates>
                </LinearRing>
            </outerBoundaryIs>
        </Polygon>
    </Placemark>
'''

        # Add tour if requested
        if include_tour and enclosures:
            duration = self.tour_duration_var.get()
            altitude = self.altitude_var.get()

            kml_body += '''
    <gx:Tour>
        <name>Enclosures Flythrough</name>
        <description>Automated tour of all enclosures</description>
        <gx:Playlist>
'''

            for name, coords in enclosures.items():
                # Calculate center of enclosure
                avg_lat = sum(pt[0] for pt in coords) / len(coords)
                avg_lon = sum(pt[1] for pt in coords) / len(coords)

                kml_body += f'''
            <gx:FlyTo>
                <gx:duration>{duration}</gx:duration>
                <gx:flyToMode>smooth</gx:flyToMode>
                <Camera>
                    <longitude>{avg_lon:.8f}</longitude>
                    <latitude>{avg_lat:.8f}</latitude>
                    <altitude>{altitude}</altitude>
                    <tilt>45</tilt>
                    <range>1000</range>
                    <heading>0</heading>
                    <roll>0</roll>
                </Camera>
            </gx:FlyTo>
            <gx:Wait>
                <gx:duration>2</gx:duration>
            </gx:Wait>
'''

            kml_body += '''
        </gx:Playlist>
    </gx:Tour>
'''

        return kml_header + kml_body + kml_footer

    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_kml(self):
        """Generate KML file"""
        try:
            raw_text = self.coord_text.get("1.0", tk.END).strip()
            if not raw_text:
                messagebox.showerror("Error", "No coordinate data entered!", parent=self.window)
                return

            enclosures = self.parse_input(raw_text)
            if not enclosures:
                messagebox.showerror("Error", "No valid coordinate pairs found!", parent=self.window)
                return

            # Get style settings
            fill_color = self.fill_color_picker.get_color()
            outline_color = self.outline_color_picker.get_color()
            include_tour = self.include_tour_var.get()

            # Generate KML content
            kml_content = self.generate_kml_content(enclosures, fill_color, outline_color, include_tour)

            # Save file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".kml",
                filetypes=[("KML files", "*.kml"), ("All files", "*.*")],
                parent=self.window
            )

            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(kml_content)

                # Show success message
                messagebox.showinfo(
                    "Success",
                    f"KML file saved successfully!\n\n"
                    f"File: {Path(file_path).name}\n"
                    f"Enclosures: {len(enclosures)}\n"
                    f"Tour included: {'Yes' if include_tour else 'No'}",
                    parent=self.window
                )

                self.update_status(f"KML saved: {Path(file_path).name}", len(enclosures))

                # Ask if user wants to open the file
                if messagebox.askyesno("Open File", "Would you like to open the KML file?", parent=self.window):
                    webbrowser.open(file_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate KML:\n{str(e)}", parent=self.window)

    def export_geojson(self):
        """Export enclosures as GeoJSON"""
        try:
            raw_text = self.coord_text.get("1.0", tk.END).strip()
            if not raw_text:
                messagebox.showwarning("Warning", "No coordinate data to export.", parent=self.window)
                return

            enclosures = self.parse_input(raw_text)
            if not enclosures:
                messagebox.showwarning("Warning", "No valid enclosures to export.", parent=self.window)
                return

            # Create GeoJSON structure
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }

            for name, coords in enclosures.items():
                # Close the polygon for GeoJSON
                polygon_coords = coords + [coords[0]]

                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "points": len(coords),
                        "created": self.get_timestamp()
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[lon, lat] for lat, lon in polygon_coords]]
                    }
                }
                geojson["features"].append(feature)

            # Save file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".geojson",
                filetypes=[("GeoJSON files", "*.geojson"), ("JSON files", "*.json"), ("All files", "*.*")],
                parent=self.window
            )

            if file_path:
                import json
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(geojson, f, indent=2)

                messagebox.showinfo(
                    "Success",
                    f"GeoJSON file saved successfully!\n\n"
                    f"File: {Path(file_path).name}\n"
                    f"Features: {len(enclosures)}",
                    parent=self.window
                )

                self.update_status(f"GeoJSON saved: {Path(file_path).name}", len(enclosures))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export GeoJSON:\n{str(e)}", parent=self.window)

    def run(self):
        """Start the application"""
        self.window.mainloop()


def open_kml_generator_window():
    """Function to open KML generator window (for external calls)"""
    app = KMLGeneratorApp()
    app.run()


def main():
    """Main function"""
    app = KMLGeneratorApp()
    app.run()


if __name__ == "__main__":
    main()