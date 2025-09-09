import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk, UnidentifiedImageError
import os

# Inline the core functions
import numpy as np
import imageio

def is_animated_gif(image_path):
    """
    Check if the input is an animated GIF.
    Returns True if animated, False otherwise.
    """
    if not image_path.lower().endswith('.gif'):
        return False
    try:
        with Image.open(image_path) as img:
            if 'duration' in img.info or img.is_animated:
                return True
            return False
    except Exception:
        return False

def is_animated_webp(image_path):
    """
    Check if the input is an animated WebP.
    Returns True if animated, False otherwise.
    """
    if not image_path.lower().endswith('.webp'):
        return False
    try:
        import imageio.v3 as iio
        reader = iio.imread(image_path)
        return len(reader) > 1 if hasattr(reader, '__len__') else False
    except Exception:
        return False

def is_image_file(image_path):
    """
    Check if the file is an image format supported by PIL.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    ext = os.path.splitext(image_path)[1].lower()
    return ext in image_extensions

def resize_image(image_path, max_dim=512):
    """
    Resize the image to max dimension 512px while preserving aspect ratio.
    Returns a resized PIL Image and its dimensions.
    For WebP, uses PIL if possible.
    """
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')  # Ensure RGB mode for video compatibility
            width, height = img.size
            if max(width, height) <= max_dim:
                print(f"No resize needed: {width}x{height}")
                return img, width, height
            if width > height:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            else:
                new_height = max_dim
                new_width = int(width * (max_dim / height))
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized from {width}x{height} to {new_width}x{new_height}")
            return resized_img, new_width, new_height
    except UnidentifiedImageError:
        # Fallback for WebP if PIL lacks support
        import imageio.v3 as iio
        img = iio.imread(image_path)
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = img[:, :, :3]  # Remove alpha if present
        pil_img = Image.fromarray(img)
        width, height = pil_img.size
        if max(width, height) > max_dim:
            if width > height:
                new_width = max_dim
                new_height = int(height * (max_dim / width))
            else:
                new_height = max_dim
                new_width = int(width * (max_dim / height))
            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return pil_img, new_width, new_height
    except Exception as e:
        raise ValueError(f"Error resizing image: {e}")

def create_webm_video(resized_img, output_path, duration=5, fps=30):
    """
    Create a WebM video from the resized image (static loop).
    - Loops the static image for the given duration.
    - Muted: Includes silent Opus audio.
    """
    # Convert PIL Image to numpy array (HWC format for imageio)
    img_array = np.array(resized_img)
    
    # Calculate number of frames
    num_frames = int(duration * fps)
    
    # Create list of identical frames
    frames = [img_array] * num_frames
    
    # Write video with imageio (FFMPEG backend handles WebM/VP9)
    # Medium quality params: -crf 30 -c:v libvpx-vp9 -b:a 128k (silent audio)
    writer_params = {
        'format': 'FFMPEG',
        'pixelformat': 'yuv420p',  # Standard for VP9
        'ffmpeg_params': [
            '-crf', '30',  # Medium quality (lower = better, 23-28 high, 28-35 medium/low)
            '-c:v', 'libvpx-vp9',  # VP9 codec for WebM
            '-b:a', '128k',  # Audio bitrate (Opus default, silent)
            '-c:a', 'libopus'  # Opus audio (silent)
        ]
    }
    
    with imageio.get_writer(output_path, fps=fps, **writer_params) as writer:
        for frame in frames:
            writer.append_data(frame)
    
    print(f"Created WebM video: {output_path} ({duration}s at {fps} FPS, muted)")

def create_webm_from_video(input_path, output_path, max_dim=512, max_duration=2.99):
    """
    Create muted WebM from input video: extract frames up to max_duration, resize, re-encode without audio.
    """
    try:
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        orig_duration = meta.get('duration', 5.0)
        fps = meta.get('fps', 30)
        
        # Cap duration
        duration = min(orig_duration, max_duration)
        num_frames_to_process = int(duration * fps)
        
        # Resize function for frames
        def resize_frame(frame):
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame = frame[:, :, :3]  # Remove alpha
            pil_img = Image.fromarray(frame)
            width, height = pil_img.size
            if max(width, height) > max_dim:
                if width > height:
                    new_width = max_dim
                    new_height = int(height * (max_dim / width))
                else:
                    new_height = max_dim
                    new_width = int(width * (max_dim / height))
                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return np.array(pil_img)
        
        # Params for muted WebM (no audio)
        writer_params = {
            'format': 'FFMPEG',
            'pixelformat': 'yuv420p',
            'ffmpeg_params': [
                '-crf', '30',
                '-c:v', 'libvpx-vp9',
                '-an',  # No audio (muted)
                '-y'  # Overwrite output
            ]
        }
        
        frame_count = 0
        with imageio.get_writer(output_path, fps=fps, **writer_params) as writer:
            for frame in reader:
                if frame_count >= num_frames_to_process:
                    break
                resized_frame = resize_frame(frame)
                writer.append_data(resized_frame)
                frame_count += 1
        
        print(f"Created muted WebM from video: {output_path} ({duration}s at {fps} FPS, truncated from {orig_duration}s)")
        return duration, fps
    except Exception as e:
        raise ValueError(f"Error processing video: {e}")

def process_animated_image(image_path, output_path, max_dim=512, max_duration=2.99, user_fps=30):
    """
    Process animated GIF or WebP: extract frames up to max_duration, resize, create muted WebM.
    """
    try:
        reader = imageio.get_reader(image_path)
        meta = reader.get_meta_data()
        orig_duration = meta.get('duration', 5.0)
        fps = meta.get('fps', user_fps)
        
        # Cap duration
        duration = min(orig_duration, max_duration)
        num_frames_to_process = int(duration * fps)
        
        def resize_frame(frame):
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame = frame[:, :, :3]
            pil_img = Image.fromarray(frame)
            width, height = pil_img.size
            if max(width, height) > max_dim:
                if width > height:
                    new_width = max_dim
                    new_height = int(height * (max_dim / width))
                else:
                    new_height = max_dim
                    new_width = int(width * (max_dim / height))
                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return np.array(pil_img)
        
        # Params for muted WebM (silent audio)
        writer_params = {
            'format': 'FFMPEG',
            'pixelformat': 'yuv420p',
            'ffmpeg_params': [
                '-crf', '30',
                '-c:v', 'libvpx-vp9',
                '-b:a', '128k',
                '-c:a', 'libopus'  # Silent audio
            ]
        }
        
        frame_count = 0
        with imageio.get_writer(output_path, fps=fps, **writer_params) as writer:
            for frame in reader:
                if frame_count >= num_frames_to_process:
                    break
                resized_frame = resize_frame(frame)
                writer.append_data(resized_frame)
                frame_count += 1
        
        print(f"Created muted WebM from animated image: {output_path} ({duration}s at {fps} FPS, truncated from {orig_duration}s)")
    except Exception as e:
        raise ValueError(f"Error processing animated image: {e}")

class MediaToWebMGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Media to WebM Converter")
        self.root.geometry("600x500")
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value="output.webm")
        self.duration = tk.DoubleVar(value=5.0)
        self.max_dim = tk.IntVar(value=512)
        self.fps = tk.IntVar(value=30)
        self.resized_dims = tk.StringVar(value="No file selected")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Input section
        tk.Label(self.root, text="Input Media:").pack(pady=5)
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5)
        tk.Entry(input_frame, textvariable=self.input_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Browse", command=self.browse_input).pack(side=tk.LEFT, padx=5)
        
        # Output section
        tk.Label(self.root, text="Output WebM:").pack(pady=5)
        output_frame = tk.Frame(self.root)
        output_frame.pack(pady=5)
        tk.Entry(output_frame, textvariable=self.output_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(output_frame, text="Browse", command=self.browse_output).pack(side=tk.LEFT, padx=5)
        
        # Settings section
        settings_frame = tk.LabelFrame(self.root, text="Settings", padx=10, pady=10)
        settings_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(settings_frame, text="Duration (seconds):").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(settings_frame, textvariable=self.duration, width=10).grid(row=0, column=1)
        
        tk.Label(settings_frame, text="Max Dimension (px):").grid(row=1, column=0, sticky=tk.W)
        tk.Entry(settings_frame, textvariable=self.max_dim, width=10).grid(row=1, column=1)
        
        tk.Label(settings_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W)
        tk.Entry(settings_frame, textvariable=self.fps, width=10).grid(row=2, column=1)
        
        # Note on muting
        tk.Label(settings_frame, text="Note: All outputs are muted (no sound).", fg="red").grid(row=3, column=0, columnspan=2, sticky=tk.W)
        
        # Preview label
        tk.Label(self.root, text="Preview (Resized Dims):").pack(pady=5)
        tk.Label(self.root, textvariable=self.resized_dims, fg="blue").pack()
        
        # Convert button
        tk.Button(self.root, text="Convert to WebM", command=self.convert, bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=20)
        
        # Status log
        tk.Label(self.root, text="Status Log:").pack(pady=5)
        self.log = scrolledtext.ScrolledText(self.root, height=8, width=70)
        self.log.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
    
    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.root.update()
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select Input Media",
            filetypes=[
                ("Media files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.mp4 *.mov *.avi *.mkv *.wmv *.flv"),
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_path.set(filename)
            try:
                if is_image_file(filename):
                    resized_img, w, h = resize_image(filename, self.max_dim.get())
                    self.resized_dims.set(f"{w}x{h} (after resize)")
                    anim_type = ""
                    if filename.lower().endswith('.gif'):
                        anim_type = " (animated GIF)" if is_animated_gif(filename) else " (static GIF)"
                    elif filename.lower().endswith('.webp'):
                        anim_type = " (animated WebP)" if is_animated_webp(filename) else " (static WebP)"
                    else:
                        anim_type = " (static image)"
                    self.log_message(f"Selected: {os.path.basename(filename)} - Preview: {w}x{h}{anim_type}")
                    resized_img.close()  # Free memory
                else:
                    # Video: get first frame for preview
                    import imageio.v3 as iio
                    first_frame = iio.imread(filename)[0]
                    if len(first_frame.shape) == 3 and first_frame.shape[2] == 4:
                        first_frame = first_frame[:, :, :3]
                    pil_img = Image.fromarray(first_frame)
                    width, height = pil_img.size
                    if max(width, height) > self.max_dim.get():
                        ratio = self.max_dim.get() / max(width, height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    self.resized_dims.set(f"{pil_img.size[0]}x{pil_img.size[1]} (video frame after resize)")
                    self.log_message(f"Selected video: {os.path.basename(filename)} - Preview frame resized (will be muted)")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid file: {e}")
                self.resized_dims.set("Error loading file")
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save WebM As",
            defaultextension=".webm",
            filetypes=[("WebM files", "*.webm"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def convert(self):
        input_file = self.input_path.get().strip()
        output_file = self.output_path.get().strip()
        
        if not input_file:
            messagebox.showerror("Error", "Please select an input file.")
            return
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file.")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"Input file not found: {input_file}")
            return
        
        try:
            self.log_message("Starting conversion (output will be muted)...")
            self.root.update()
            
            max_dim = self.max_dim.get()
            user_fps = self.fps.get()
            user_duration = self.duration.get()
            static_max = 2.0
            anim_max = 2.99
            
            is_image = is_image_file(input_file)
            is_animated = False
            final_duration = user_duration
            final_fps = user_fps
            anim_status = ""
            
            if is_image:
                if input_file.lower().endswith(('.gif', '.webp')):
                    is_animated = is_animated_gif(input_file) if input_file.lower().endswith('.gif') else is_animated_webp(input_file)
                    if is_animated:
                        anim_status = " (animated image)"
                        if final_duration > anim_max:
                            self.log_message(f"Animated image detected: Capping duration to {anim_max} seconds (was {final_duration})")
                            final_duration = anim_max
                        process_animated_image(input_file, output_file, max_dim, final_duration, final_fps)
                    else:
                        anim_status = " (static image)"
                        if final_duration > static_max:
                            self.log_message(f"Static image detected: Capping duration to {static_max} seconds (was {final_duration})")
                            final_duration = static_max
                        resized_img, w, h = resize_image(input_file, max_dim)
                        self.resized_dims.set(f"{w}x{h} (processing)")
                        self.log_message(f"Resized to {w}x{h}")
                        create_webm_video(resized_img, output_file, final_duration, final_fps)
                        resized_img.close()
                else:
                    anim_status = " (static image)"
                    if final_duration > static_max:
                        self.log_message(f"Static image detected: Capping duration to {static_max} seconds (was {final_duration})")
                        final_duration = static_max
                    resized_img, w, h = resize_image(input_file, max_dim)
                    self.resized_dims.set(f"{w}x{h} (processing)")
                    self.log_message(f"Resized to {w}x{h}")
                    create_webm_video(resized_img, output_file, final_duration, final_fps)
                    resized_img.close()
            else:
                # Video: cap at 2.99s, mute
                anim_status = " (video, muted)"
                if user_duration > anim_max:
                    self.log_message(f"Video duration setting ignored; using input duration capped to {anim_max}s")
                final_duration, final_fps = create_webm_from_video(input_file, output_file, max_dim, anim_max)
                self.resized_dims.set(f"Frames processed (video)")
                self.log_message(f"Video processed: {final_duration}s at {final_fps} FPS{anim_status}")
            
            self.log_message(f"Success! Saved to: {output_file} ({final_duration}s duration{anim_status})")
            messagebox.showinfo("Success", f"Conversion complete! Duration used: {final_duration}s{anim_status} (muted audio)")
            
        except Exception as e:
            error_msg = f"Conversion failed: {e}"
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)

def main():
    root = tk.Tk()
    app = MediaToWebMGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()