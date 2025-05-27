import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import platform
from urllib.parse import urlparse

# Import the WebPageCapture class from your existing script
from screenshot import WebPageCapture

class WebCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Page Capture Tool")
        self.root.geometry("650x450")
        self.root.minsize(600, 400)
        
        # Set app icon (if available)
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("icon.ico")
            else:
                logo = tk.PhotoImage(file="icon.png")
                self.root.iconphoto(True, logo)
        except:
            pass  # Icon not available, continue without it
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TLabel", padding=5, font=("Helvetica", 11))
        self.style.configure("TButton", padding=5, font=("Helvetica", 11))
        self.style.configure("TEntry", padding=5, font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))
        
        # Create the main container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # App title
        title_label = ttk.Label(self.main_frame, text="Web Page Capture Tool", style="Header.TLabel")
        title_label.grid(column=0, row=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        # Create the form
        self._create_form()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            root, orient=tk.HORIZONTAL, length=100, mode='indeterminate'
        )
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
        
        # Capture instance
        self.capture = None
        
    def _create_form(self):
        """Create the input form elements"""
        # URL input
        ttk.Label(self.main_frame, text="Website URL:").grid(
            column=0, row=1, sticky=tk.W
        )
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.main_frame, width=50, textvariable=self.url_var)
        self.url_entry.grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        
        # Format selection
        ttk.Label(self.main_frame, text="Output Format:").grid(
            column=0, row=2, sticky=tk.W
        )
        self.format_var = tk.StringVar(value="png")
        
        format_frame = ttk.Frame(self.main_frame)
        format_frame.grid(column=1, row=2, sticky=tk.W, columnspan=2)
        
        ttk.Radiobutton(
            format_frame, text="PNG", variable=self.format_var, value="png",
            command=self._toggle_quality_visibility
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            format_frame, text="JPG", variable=self.format_var, value="jpg",
            command=self._toggle_quality_visibility
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            format_frame, text="PDF", variable=self.format_var, value="pdf",
            command=self._toggle_quality_visibility
        ).pack(side=tk.LEFT, padx=5)
        
        # Quality slider for JPG
        self.quality_label = ttk.Label(self.main_frame, text="JPEG Quality:")
        self.quality_label.grid(column=0, row=3, sticky=tk.W)
        
        quality_frame = ttk.Frame(self.main_frame)
        quality_frame.grid(column=1, row=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.quality_var = tk.IntVar(value=90)
        self.quality_slider = ttk.Scale(
            quality_frame, from_=10, to=100, orient=tk.HORIZONTAL,
            variable=self.quality_var, length=250
        )
        self.quality_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.quality_value_label = ttk.Label(quality_frame, text="90")
        self.quality_value_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Update quality label when slider moves
        self.quality_var.trace("w", self._update_quality_label)
        
        # Toggle visibility based on initial format
        self._toggle_quality_visibility()
        
        # Image dimensions
        ttk.Label(self.main_frame, text="Image Width:").grid(
            column=0, row=4, sticky=tk.W
        )
        
        # Width and height frame
        dim_frame = ttk.Frame(self.main_frame)
        dim_frame.grid(column=1, row=4, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        
        self.width_var = tk.IntVar(value=1920)
        width_entry = ttk.Entry(dim_frame, width=6, textvariable=self.width_var)
        width_entry.pack(side=tk.LEFT)
        
        ttk.Label(dim_frame, text="px   Height (optional):").pack(side=tk.LEFT, padx=(5, 5))
        
        self.height_var = tk.IntVar(value=0)  # 0 means full page
        height_entry = ttk.Entry(dim_frame, width=6, textvariable=self.height_var)
        height_entry.pack(side=tk.LEFT)
        
        ttk.Label(dim_frame, text="px  (0 = full page)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Output path
        ttk.Label(self.main_frame, text="Save Location:").grid(
            column=0, row=5, sticky=tk.W
        )
        
        path_frame = ttk.Frame(self.main_frame)
        path_frame.grid(column=1, row=5, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(path_frame, width=40, textvariable=self.output_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(
            path_frame, text="Browse...", command=self._browse_output
        )
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Timeout setting
        ttk.Label(self.main_frame, text="Timeout (sec):").grid(
            column=0, row=6, sticky=tk.W
        )
        
        self.timeout_var = tk.IntVar(value=30)
        timeout_entry = ttk.Entry(self.main_frame, width=6, textvariable=self.timeout_var)
        timeout_entry.grid(column=1, row=6, sticky=tk.W, padx=5, pady=5)
        
        # Capture button
        self.capture_button = ttk.Button(
            self.main_frame, text="Capture Webpage", command=self._start_capture
        )
        self.capture_button.grid(column=0, row=7, columnspan=3, pady=20)
        
        # Configure grid to expand properly
        self.main_frame.columnconfigure(1, weight=1)
        
    def _toggle_quality_visibility(self):
        """Show/hide quality slider based on format selection"""
        if self.format_var.get() == "jpg":
            self.quality_label.grid(column=0, row=3, sticky=tk.W)
            self.quality_slider.master.grid(column=1, row=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        else:
            self.quality_label.grid_remove()
            self.quality_slider.master.grid_remove()
            
    def _update_quality_label(self, *args):
        """Update the quality value label when slider changes"""
        try:
            self.quality_value_label.config(text=str(self.quality_var.get()))
        except:
            pass
            
    def _browse_output(self):
        """Open file dialog to select save location"""
        format_choice = self.format_var.get()
        
        # Set appropriate file type filters
        filetypes = [("All Files", "*.*")]
        if format_choice == "png":
            filetypes = [("PNG Images", "*.png"), ("All Files", "*.*")]
            default_ext = ".png"
        elif format_choice == "jpg":
            filetypes = [("JPEG Images", "*.jpg"), ("All Files", "*.*")]
            default_ext = ".jpg"
        elif format_choice == "pdf":
            filetypes = [("PDF Documents", "*.pdf"), ("All Files", "*.*")]
            default_ext = ".pdf"
            
        # Try to extract domain for default filename
        default_filename = ""
        try:
            url = self.url_var.get()
            if url:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                parsed = urlparse(url)
                if parsed.netloc:
                    default_filename = parsed.netloc.replace("www.", "")
        except:
            pass
            
        if not default_filename:
            default_filename = "webpage"
            
        filename = filedialog.asksaveasfilename(
            title="Save As",
            filetypes=filetypes,
            defaultextension=default_ext,
            initialfile=f"{default_filename}{default_ext}"
        )
        
        if filename:
            self.output_var.set(filename)
            
    def _start_capture(self):
        """Begin the webpage capture process"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        # Get form values
        format_choice = self.format_var.get()
        quality = self.quality_var.get()
        width = self.width_var.get()
        height = self.height_var.get() if self.height_var.get() > 0 else None
        output_path = self.output_var.get().strip() or None
        timeout = self.timeout_var.get()
        
        # Disable UI during capture
        self.capture_button.config(state="disabled")
        self.progress.start()
        self.status_var.set("Initializing capture...")
        self.root.update()
        
        # Run capture in a separate thread
        thread = threading.Thread(
            target=self._capture_thread,
            args=(url, format_choice, output_path, quality, width, height, timeout),
            daemon=True
        )
        thread.start()
        
    def _capture_thread(self, url, format_choice, output_path, quality, width, height, timeout):
        """Worker thread for capturing webpage"""
        try:
            self._update_status("Starting Chrome...")
            
            # Create new WebPageCapture instance
            capture = WebPageCapture(headless=True, timeout=timeout, wait_for_network=True)
            
            self._update_status(f"Loading {url}...")
            
            # Perform the capture
            result = capture.capture(
                url, format_choice, output_path, quality, width, height
            )
            
            # Always close the browser
            capture.close()
            
            # Update UI based on result
            if result:
                self._update_status(f"Saved to: {result}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", f"Screenshot saved to:\n{result}"
                ))
            else:
                self._update_status("Capture failed")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to capture webpage"
                ))
                
        except Exception as e:
            error_message = str(e)
            self._update_status(f"Error: {error_message}")
            self.root.after(0, lambda: messagebox.showerror("Error", error_message))
            
        # Reset UI state
        self.root.after(0, self._reset_ui)
        
    def _update_status(self, message):
        """Thread-safe status update"""
        self.root.after(0, lambda: self.status_var.set(message))
        
    def _reset_ui(self):
        """Reset UI after capture completes"""
        self.progress.stop()
        self.capture_button.config(state="normal")

def run_gui():
    """Launch the GUI application"""
    root = tk.Tk()
    app = WebCaptureGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
