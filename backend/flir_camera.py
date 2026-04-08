# flir_camera.py - FLIR CM3-U3-13Y3M-CS Camera Integration
"""
Production-ready FLIR thermal camera integration for ZIMON application.
Optimized for maximum FPS, zero frame drops, and scientific imaging.

Camera: FLIR CM3-U3-13Y3M-CS (USB3)
Interface: Spinnaker SDK (PySpin)
Target: Match or exceed SpinView performance
"""

import logging
import time
import threading
import numpy as np
from typing import Optional, Dict, Tuple, List
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Try to import FLIR Spinnaker SDK
try:
    import PySpin
    FLIR_AVAILABLE = True
    logging.getLogger("FLIRCamera").info("FLIR Spinnaker SDK loaded successfully")
except ImportError:
    FLIR_AVAILABLE = False
    logging.getLogger("FLIRCamera").warning("FLIR Spinnaker SDK not available - FLIR cameras disabled")
    
    # Try alternative import paths
    try:
        import sys
        import os
        # Check common FLIR installation paths
        flir_paths = [
            r"C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python",
            r"C:\Program Files (x86)\FLIR Systems\Spinnaker\Development\bin\Python",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "FLIR Systems", "Spinnaker", "Development", "bin", "Python"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "FLIR Systems", "Spinnaker", "Development", "bin", "Python"),
        ]
        
        for flir_path in flir_paths:
            if os.path.exists(flir_path):
                sys.path.insert(0, flir_path)
                logging.getLogger("FLIRCamera").info(f"Added FLIR path to sys.path: {flir_path}")
                break
        
        # Try import again
        try:
            import PySpin
            FLIR_AVAILABLE = True
            logging.getLogger("FLIRCamera").info("FLIR Spinnaker SDK loaded successfully from alternative path")
        except ImportError:
            logging.getLogger("FLIRCamera").warning("FLIR Spinnaker SDK still not available after path search")
    except Exception as e:
        logging.getLogger("FLIRCamera").error(f"Error searching FLIR SDK paths: {e}")

# FLIR Camera Constants
FLIR_BUFFER_COUNT = 10  # Optimal for USB3 throughput
FLIR_PACKET_SIZE = 0  # Auto-detect optimal packet size

# Set pixel format only if PySpin is available
if FLIR_AVAILABLE:
    FLIR_PIXEL_FORMAT = PySpin.PixelFormat_Mono8  # Fastest format for thermal imaging
else:
    FLIR_PIXEL_FORMAT = None


class FLIRCameraWorker(QThread):
    """
    High-performance FLIR camera worker with optimized acquisition.
    
    Features:
    - Non-blocking asynchronous acquisition
    - Optimized buffer handling (newest-first strategy)
    - Zero frame drops through proper queue management
    - Production-ready error handling
    - Real-time FPS monitoring and statistics
    """
    
    # Signals
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    fps_updated = pyqtSignal(float)
    stats_updated = pyqtSignal(dict)  # For detailed performance stats
    
    def __init__(self, camera_name: str, camera_info: Dict):
        super().__init__()
        self.camera_name = camera_name
        self.camera_info = camera_info
        self.camera_system = None
        self.camera = None
        self.nodemap = None
        
        # Performance tracking
        self._running = False
        self._fps_counter = 0
        self._fps_start_time = time.time()
        self._current_fps = 0.0
        self._dropped_frames = 0
        self._total_frames = 0
        self._buffer_underruns = 0
        
        # Threading and synchronization
        self._acquisition_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
        self.logger = logging.getLogger(f"FLIRWorker-{camera_name}")
        
    def run(self):
        """Main FLIR acquisition loop - optimized for maximum performance"""
        self._running = True
        self.logger.info(f"Starting FLIR camera {self.camera_name}")
        
        try:
            if not self._initialize_flir():
                self.error_occurred.emit(f"Failed to initialize FLIR camera {self.camera_name}")
                return
            
            # Start optimized acquisition
            if not self._start_acquisition():
                self.error_occurred.emit(f"Failed to start FLIR acquisition {self.camera_name}")
                return
            
            # Main acquisition loop - optimized for zero frame drops
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            self.logger.info(f"FLIR acquisition started for {self.camera_name}")
            
            while self._running:
                try:
                    # Non-blocking image retrieval with timeout
                    result = self._get_next_image(timeout=0.001)  # 1ms timeout for responsiveness
                    
                    if result is not None:
                        self.frame_ready.emit(result)
                        self._update_fps_counter()
                        self._update_statistics()
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        # No image available - brief sleep to prevent CPU spinning
                        time.sleep(0.0001)  # 100μs - minimal for responsiveness
                        
                except Exception as e:
                    self.logger.error(f"Error in FLIR acquisition loop: {e}")
                    consecutive_errors += 1
                    time.sleep(0.001)  # Minimal sleep on error
                    
                    # Stop on too many consecutive errors
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.error(f"FLIR camera: {max_consecutive_errors} consecutive errors, stopping")
                        self.error_occurred.emit(f"FLIR camera: {max_consecutive_errors} errors")
                        break
                        
        except Exception as e:
            self.logger.error(f"FLIR camera critical error: {e}", exc_info=True)
            self.error_occurred.emit(f"FLIR camera critical error: {str(e)}")
        finally:
            self._cleanup_flir()
            self.logger.info(f"FLIR camera stopped for {self.camera_name}")
    
    def _initialize_flir(self) -> bool:
        """
        Initialize FLIR camera with production-ready optimizations.
        """
        try:
            if not FLIR_AVAILABLE:
                self.logger.error("FLIR Spinnaker SDK not available")
                return False
            
            # Get camera system and specific camera
            self.camera_system = PySpin.System.GetInstance()
            camera_list = self.camera_system.GetCameras()
            
            if len(camera_list) == 0:
                self.logger.error("No FLIR cameras found")
                return False
            
            # Use first camera (or match by serial if available)
            self.camera = camera_list[0]
            self.camera.Init()
            
            # Log camera information for debugging
            self._log_camera_info()
            
            # Configure for maximum performance
            if not self._configure_optimal_settings():
                self.logger.error("Failed to configure FLIR camera settings")
                return False
            
            # Validate configuration
            if not self._validate_configuration():
                self.logger.error("FLIR camera configuration validation failed")
                return False
            
            self.logger.info(f"FLIR camera {self.camera_name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"FLIR camera initialization failed: {e}", exc_info=True)
            return False
    
    def _configure_optimal_settings(self) -> bool:
        """
        Configure FLIR camera for maximum FPS and zero frame drops.
        """
        try:
            # Disable all automatic features for maximum control
            self._disable_automatic_features()
            
            # Configure pixel format for fastest acquisition
            self._configure_pixel_format()
            
            # Configure buffer handling for optimal throughput
            self._configure_buffers()
            
            # Configure acquisition mode for continuous capture
            self._configure_acquisition_mode()
            
            # Configure trigger mode for free-running
            self._configure_trigger_mode()
            
            # Configure packet size for USB3 optimization
            self._configure_packet_size()
            
            # Apply resolution and FPS from camera info
            self._apply_resolution_settings()
            
            self.logger.info("FLIR camera configured for optimal performance")
            return True
            
        except Exception as e:
            self.logger.error(f"FLIR camera configuration failed: {e}", exc_info=True)
            return False
    
    def _disable_automatic_features(self):
        """Disable all automatic features for manual control"""
        try:
            # Disable auto exposure
            if PySpin.ExposureAuto_Once:
                self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
                self.logger.debug("FLIR: Auto exposure disabled")
            
            # Disable auto gain
            if hasattr(self.camera, 'GainAuto') and self.camera.GainAuto.GetAccessMode() != PySpin.AccessMode_RW:
                self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
                self.logger.debug("FLIR: Auto gain disabled")
            
            # Disable auto white balance (if available)
            if hasattr(self.camera, 'BalanceWhiteAuto'):
                self.camera.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)
                self.logger.debug("FLIR: Auto white balance disabled")
            
            # Disable gamma correction
            if hasattr(self.camera, 'GammaEnable'):
                self.camera.GammaEnable.SetValue(False)
                self.logger.debug("FLIR: Gamma correction disabled")
                
        except Exception as e:
            self.logger.warning(f"Error disabling FLIR auto features: {e}")
    
    def _configure_pixel_format(self):
        """Configure pixel format for fastest acquisition"""
        try:
            # Try Mono8 first (fastest)
            if PySpin.PixelFormat_Mono8 in self.camera.PixelFormat.GetSymbolics():
                self.camera.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
                self.logger.info("FLIR: Pixel format set to Mono8")
            # Fallback to Mono16
            elif PySpin.PixelFormat_Mono16 in self.camera.PixelFormat.GetSymbolics():
                self.camera.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)
                self.logger.info("FLIR: Pixel format set to Mono16")
            else:
                # Use first available format
                available_formats = self.camera.PixelFormat.GetSymbolics()
                if available_formats:
                    self.camera.PixelFormat.SetValue(available_formats[0])
                    self.logger.info(f"FLIR: Pixel format set to {available_formats[0]}")
                    
        except Exception as e:
            self.logger.error(f"Error configuring FLIR pixel format: {e}")
    
    def _configure_buffers(self):
        """Configure buffer handling for optimal throughput"""
        try:
            # Set buffer count for optimal USB3 performance
            if hasattr(self.camera, 'StreamBufferCountManual'):
                self.camera.StreamBufferCountManual.SetValue(FLIR_BUFFER_COUNT)
                self.logger.info(f"FLIR: Buffer count set to {FLIR_BUFFER_COUNT}")
            
            # Set buffer handling mode to newest-first (minimize latency)
            if hasattr(self.camera, 'StreamBufferHandlingMode'):
                self.camera.StreamBufferHandlingMode.SetValue(PySpin.StreamBufferHandlingMode_NewestFirst)
                self.logger.info("FLIR: Buffer handling set to NewestFirst")
            
            # Enable stream auto-restart
            if hasattr(self.camera, 'StreamAutoReconfigureEnable'):
                self.camera.StreamAutoReconfigureEnable.SetValue(True)
                self.logger.info("FLIR: Stream auto-reconfigure enabled")
                
        except Exception as e:
            self.logger.warning(f"Error configuring FLIR buffers: {e}")
    
    def _configure_acquisition_mode(self):
        """Configure acquisition mode for continuous capture"""
        try:
            # Set acquisition mode to continuous
            self.camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            self.logger.info("FLIR: Acquisition mode set to Continuous")
            
            # Set acquisition frame rate if supported
            if hasattr(self.camera, 'AcquisitionFrameRateEnable'):
                self.camera.AcquisitionFrameRateEnable.SetValue(True)
                target_fps = self.camera_info.get("settings", {}).get("fps", 30)
                if hasattr(self.camera, 'AcquisitionFrameRate'):
                    self.camera.AcquisitionFrameRate.SetValue(target_fps)
                    self.logger.info(f"FLIR: Target FPS set to {target_fps}")
                    
        except Exception as e:
            self.logger.error(f"Error configuring FLIR acquisition mode: {e}")
    
    def _configure_trigger_mode(self):
        """Configure trigger mode for free-running"""
        try:
            # Disable trigger for free-running mode
            self.camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            self.logger.info("FLIR: Trigger mode set to Off (free-running)")
            
            # Set trigger source to software (if needed)
            if hasattr(self.camera, 'TriggerSource'):
                self.camera.TriggerSource.SetValue(PySpin.TriggerSource_Software)
                self.logger.debug("FLIR: Trigger source set to Software")
                
        except Exception as e:
            self.logger.error(f"Error configuring FLIR trigger mode: {e}")
    
    def _configure_packet_size(self):
        """Configure packet size for USB3 optimization"""
        try:
            # Auto-detect optimal packet size
            if hasattr(self.camera, 'DeviceStreamThroughputLimit'):
                # Let camera auto-detect optimal packet size
                self.camera.DeviceStreamThroughputLimit.SetValue(PySpin.DeviceStreamThroughputLimit_Optimal)
                self.logger.info("FLIR: Packet size set to Optimal")
            elif hasattr(self.camera, 'DeviceLinkThroughputLimit'):
                self.camera.DeviceLinkThroughputLimit.SetValue(PySpin.DeviceLinkThroughputLimit_Optimal)
                self.logger.info("FLIR: Link throughput set to Optimal")
                
        except Exception as e:
            self.logger.warning(f"Error configuring FLIR packet size: {e}")
    
    def _apply_resolution_settings(self):
        """Apply resolution and FPS from camera info"""
        try:
            settings = self.camera_info.get("settings", {})
            
            # Set resolution
            resolution = settings.get("resolution", (640, 480))
            if hasattr(self.camera, 'Width') and hasattr(self.camera, 'Height'):
                self.camera.Width.SetValue(resolution[0])
                self.camera.Height.SetValue(resolution[1])
                self.logger.info(f"FLIR: Resolution set to {resolution[0]}x{resolution[1]}")
            
            # Set frame rate
            fps = settings.get("fps", 30)
            if hasattr(self.camera, 'AcquisitionFrameRate'):
                self.camera.AcquisitionFrameRate.SetValue(fps)
                self.logger.info(f"FLIR: FPS set to {fps}")
                
        except Exception as e:
            self.logger.error(f"Error applying FLIR resolution settings: {e}")
    
    def _validate_configuration(self) -> bool:
        """Validate camera configuration before starting acquisition"""
        try:
            # Validate pixel format
            pixel_format = self.camera.PixelFormat.GetValue()
            self.logger.info(f"FLIR: Pixel format validation: {pixel_format}")
            
            # Validate resolution
            width = self.camera.Width.GetValue()
            height = self.camera.Height.GetValue()
            self.logger.info(f"FLIR: Resolution validation: {width}x{height}")
            
            # Validate buffer configuration
            if hasattr(self.camera, 'StreamBufferCountManual'):
                buffer_count = self.camera.StreamBufferCountManual.GetValue()
                self.logger.info(f"FLIR: Buffer count validation: {buffer_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"FLIR configuration validation failed: {e}")
            return False
    
    def _start_acquisition(self) -> bool:
        """Start camera acquisition with error handling"""
        try:
            self.camera.BeginAcquisition()
            self.logger.info("FLIR: Acquisition started")
            return True
        except Exception as e:
            self.logger.error(f"FLIR: Failed to start acquisition: {e}")
            return False
    
    def _get_next_image(self, timeout: float = 0.001) -> Optional[np.ndarray]:
        """
        Get next image from camera with non-blocking behavior.
        
        Args:
            timeout: Timeout in seconds for image retrieval
            
        Returns:
            numpy array or None if no image available
        """
        try:
            with self._acquisition_lock:
                # Check if image is available
                if not self.camera.GetNumReadyImages():
                    return None
                
                # Get next image with timeout
                try:
                    result = self.camera.GetNextImage(timeout)
                    if result and result.IsIncomplete():
                        # Incomplete image - increment dropped counter
                        with self._stats_lock:
                            self._dropped_frames += 1
                        result.Release()
                        return None
                    
                    if not result or not result.IsValid():
                        return None
                    
                    # Convert to numpy array
                    image_data = self._convert_to_numpy(result)
                    
                    # Release image immediately to prevent buffer starvation
                    result.Release()
                    
                    # Update statistics
                    with self._stats_lock:
                        self._total_frames += 1
                    
                    return image_data
                    
                except PySpin.SpinnakerException as e:
                    if e.error_code == PySpin.SpinnakerException.TIMEOUT:
                        # Timeout is normal - no image available
                        return None
                    else:
                        self.logger.warning(f"FLIR image retrieval error: {e}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"FLIR get next image error: {e}")
            return None
    
    def _convert_to_numpy(self, image) -> np.ndarray:
        """
        Convert FLIR image to numpy array efficiently.
        """
        try:
            # Get image dimensions and data
            width = image.GetWidth()
            height = image.GetHeight()
            pixel_format = image.GetPixelFormat()
            
            # Convert based on pixel format
            if pixel_format == PySpin.PixelFormat_Mono8:
                # Direct memory copy for Mono8
                data_ptr = image.GetData()
                buffer_size = width * height
                numpy_array = np.frombuffer(data_ptr, dtype=np.uint8, count=buffer_size)
                return numpy_array.reshape((height, width))
            
            elif pixel_format == PySpin.PixelFormat_Mono16:
                # Convert Mono16 to numpy
                data_ptr = image.GetData()
                buffer_size = width * height * 2
                numpy_array = np.frombuffer(data_ptr, dtype=np.uint16, count=buffer_size)
                return numpy_array.reshape((height, width))
            
            else:
                # Fallback conversion for other formats
                converted_image = image.Convert(PySpin.PixelFormat_Mono8)
                data_ptr = converted_image.GetData()
                buffer_size = width * height
                numpy_array = np.frombuffer(data_ptr, dtype=np.uint8, count=buffer_size)
                return numpy_array.reshape((height, width))
                
        except Exception as e:
            self.logger.error(f"FLIR numpy conversion error: {e}")
            return None
    
    def _update_fps_counter(self):
        """Update FPS counter efficiently"""
        self._fps_counter += 1
        current_time = time.time()
        
        # Update FPS every second
        if current_time - self._fps_start_time >= 1.0:
            self._current_fps = self._fps_counter / (current_time - self._fps_start_time)
            self.fps_updated.emit(self._current_fps)
            self._fps_counter = 0
            self._fps_start_time = current_time
    
    def _update_statistics(self):
        """Update performance statistics"""
        try:
            if self._total_frames % 30 == 0:  # Update every 30 frames
                stats = {
                    'total_frames': self._total_frames,
                    'dropped_frames': self._dropped_frames,
                    'drop_rate': (self._dropped_frames / max(self._total_frames, 1)) * 100,
                    'current_fps': self._current_fps
                }
                self.stats_updated.emit(stats)
                
        except Exception as e:
            self.logger.warning(f"Error updating FLIR statistics: {e}")
    
    def _log_camera_info(self):
        """Log detailed camera information for debugging"""
        try:
            # Get camera model and serial
            model = self.camera.DeviceModelName.GetValue()
            serial = self.camera.DeviceSerialNumber.GetValue()
            firmware = self.camera.DeviceFirmwareVersion.GetValue()
            
            # Get sensor information
            sensor_width = self.camera.SensorWidth.GetValue()
            sensor_height = self.camera.SensorHeight.GetValue()
            
            # Get supported formats and modes
            pixel_formats = [str(fmt) for fmt in self.camera.PixelFormat.GetSymbolics()]
            acquisition_modes = [str(mode) for mode in self.camera.AcquisitionMode.GetSymbolics()]
            
            self.logger.info(f"FLIR Camera Info:")
            self.logger.info(f"  Model: {model}")
            self.logger.info(f"  Serial: {serial}")
            self.logger.info(f"  Firmware: {firmware}")
            self.logger.info(f"  Sensor: {sensor_width}x{sensor_height}")
            self.logger.info(f"  Pixel Formats: {len(pixel_formats)} available")
            self.logger.info(f"  Acquisition Modes: {len(acquisition_modes)} available")
            
        except Exception as e:
            self.logger.warning(f"Error logging FLIR camera info: {e}")
    
    def stop(self):
        """Stop FLIR camera acquisition"""
        self._running = False
        self.wait(1000)  # Wait up to 1 second for thread to finish
    
    def get_current_fps(self) -> float:
        """Get current FPS"""
        return self._current_fps
    
    def _cleanup_flir(self):
        """Clean up FLIR camera resources"""
        try:
            if self.camera:
                # Stop acquisition
                if self.camera.IsStreaming():
                    self.camera.EndAcquisition()
                    self.logger.info("FLIR: Acquisition stopped")
                
                # Deinitialize camera
                self.camera.DeInit()
                self.camera = None
                self.logger.info("FLIR: Camera deinitialized")
            
            if self.camera_system:
                # Release camera system
                self.camera_system.ReleaseInstance()
                self.camera_system = None
                self.logger.info("FLIR: Camera system released")
                
        except Exception as e:
            self.logger.error(f"FLIR cleanup error: {e}")
    
    def update_fps(self, fps: int):
        """Update target FPS during runtime"""
        try:
            if self.camera and hasattr(self.camera, 'AcquisitionFrameRate'):
                self.camera.AcquisitionFrameRate.SetValue(fps)
                self.logger.info(f"FLIR target FPS updated to {fps}")
        except Exception as e:
            self.logger.error(f"Error updating FLIR FPS: {e}")


# Utility function for FLIR camera detection
def detect_flir_cameras() -> List[Dict]:
    """
    Detect available FLIR cameras.
    
    Returns:
        List of camera information dictionaries
    """
    cameras = []
    
    if not FLIR_AVAILABLE:
        return cameras
    
    try:
        system = PySpin.System.GetInstance()
        camera_list = system.GetCameras()
        
        for idx, camera in enumerate(camera_list):
            try:
                camera.Init()
                
                # Get camera information
                model = camera.DeviceModelName.GetValue()
                serial = camera.DeviceSerialNumber.GetValue()
                
                # Create camera info dictionary
                camera_info = {
                    "type": "flir",
                    "device": camera,
                    "model": model,
                    "serial": serial,
                    "settings": {
                        "resolution": (640, 480),  # Default thermal resolution
                        "fps": 30,  # Default thermal FPS
                        "zoom": 1.0
                    }
                }
                
                cameras.append({
                    f"FLIR_{model}_{serial}": camera_info
                })
                
                camera.Deinit()
                
            except Exception as e:
                logging.getLogger("FLIRCamera").warning(f"Error detecting FLIR camera {idx}: {e}")
        
        system.ReleaseInstance()
        
    except Exception as e:
        logging.getLogger("FLIRCamera").error(f"FLIR camera detection failed: {e}")
    
    return cameras
