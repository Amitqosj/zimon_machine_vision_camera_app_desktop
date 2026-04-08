# FLIR SDK Installation Guide
# Step-by-step installation for FLIR CM3-U3-13Y3M-CS thermal camera

## 🔍 Current Status Check

### 1. Verify Current Installation
```powershell
# Check if FLIR Spinnaker is installed
Get-ChildItem -Path 'C:\Program Files' -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Name -like '*FLIR*'} | Select-Object Name

# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"
```

### 2. Check PySpin Availability
```python
python -c "try: import PySpin; print('✅ PySpin available'); except ImportError as e: print(f'❌ PySpin not available: {e}')"
```

## 📦 FLIR SDK Installation Steps

### Option 1: Download from FLIR Website (Recommended)
1. **Download FLIR Spinnaker SDK**
   - Go to: https://www.flir.com/support-center/downloads/spinnaker/
   - Download: Spinnaker SDK for Windows (64-bit)
   - Version: 1.26.0 or later

2. **Install with Python Bindings**
   - Run installer as Administrator
   - Select "Custom" installation
   - Ensure "Python Bindings" option is checked
   - Install to: `C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python`

3. **Verify Installation**
   ```powershell
   # Check if PySpin.dll exists
   dir "C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python" | findstr PySpin
   ```

### Option 2: Manual Installation
1. **Extract SDK Files**
   - Download Spinnaker SDK zip file
   - Extract to temporary folder
   - Copy Python bindings to system path

2. **Add to Python Path**
   ```powershell
   # Add FLIR Python path to environment
   $env:Path += ";C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python"
   
   # Or add permanently
   [System.Environment]::SetEnvironmentVariable('Path', $env:Path, 'Machine')
   ```

3. **Copy Required Files**
   ```powershell
   # Copy PySpin.py and PySpin.dll to Python site-packages
   copy "C:\FLIR_SDK\Python\PySpin.py" "C:\Python313\Lib\site-packages\"
   copy "C:\FLIR_SDK\bin\PySpin.dll" "C:\Python313\Lib\site-packages\"
   ```

## 🔧 Configuration After Installation

### 1. Update Python Path
```python
import sys
sys.path.insert(0, r"C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python")
```

### 2. Test Installation
```python
python -c "
try:
    import PySpin
    print('✅ FLIR SDK installed successfully')
    print(f'PySpin version: {PySpin.__version__}')
except ImportError as e:
    print(f'❌ FLIR SDK not available: {e}')
except Exception as e:
    print(f'❌ FLIR SDK error: {e}')
"
```

## 🚀 Quick Installation Script

### Automated Installation
```powershell
# Save as install_flir.ps1 and run as Administrator
$flirPath = "C:\Program Files\FLIR Systems\Spinnaker\Development\bin\Python"

# Check if already installed
if (Test-Path $flirPath) {
    Write-Host "✅ FLIR SDK already installed at $flirPath" -ForegroundColor Green
} else {
    Write-Host "❌ FLIR SDK not found at $flirPath" -ForegroundColor Red
    Write-Host "Please download and install FLIR Spinnaker SDK from:" -ForegroundColor Yellow
    Write-Host "https://www.flir.com/support-center/downloads/spinnaker/" -ForegroundColor Cyan
}
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue: "PySpin not available"
**Causes:**
- FLIR SDK not installed
- Python path not updated
- Wrong architecture (32-bit vs 64-bit)

**Solutions:**
1. Verify FLIR installation path
2. Check Python architecture (`python -c "import platform; print(platform.architecture())"`)
3. Reinstall FLIR SDK with Python bindings
4. Add FLIR path to PYTHONPATH environment variable

#### Issue: "FLIR camera not detected"
**Causes:**
- Camera not connected to USB3 port
- Driver not installed
- Camera in use by another application

**Solutions:**
1. Check Device Manager for FLIR camera
2. Try different USB3 port
3. Restart camera (unplug/replug)
4. Close other camera applications

#### Issue: "ImportError: DLL load failed"
**Causes:**
- Missing Visual C++ Redistributable
- Corrupted installation
- Architecture mismatch

**Solutions:**
1. Install Visual C++ Redistributable 2019+
2. Reinstall FLIR SDK as Administrator
3. Check Windows Event Viewer for errors

## 📋 Installation Verification Checklist

### ✅ Pre-Installation
- [ ] Windows 10/11 (64-bit)
- [ ] Administrator privileges
- [ ] FLIR CM3-U3-13Y3M-CS camera
- [ ] USB3 cable and port

### ✅ Installation
- [ ] Downloaded FLIR Spinnaker SDK 1.26.0+
- [ ] Ran installer as Administrator
- [ ] Selected Python bindings option
- [ ] Installation to default path

### ✅ Post-Installation
- [ ] PySpin.dll exists in installation path
- [ ] PySpin.py accessible from Python
- [ ] Python path includes FLIR directory
- [ ] Import test passes
- [ ] Camera detection test passes

## 🎯 Next Steps

### After Installation
1. **Install Requirements**: `pip install -r requirements.txt`
2. **Run Test**: `python test_flir_integration.py`
3. **Launch Application**: `python main.py`
4. **Verify Camera**: Check if FLIR camera appears in camera list

### Integration Verification
```python
# Test complete integration
python -c "
from backend.camera_interface import CameraController
controller = CameraController()
cameras = controller.list_cameras()
flir_cameras = [name for name in cameras if 'FLIR' in name]
print(f'Found {len(flir_cameras)} FLIR cameras: {flir_cameras}')
"
```

## 📞 Support Resources

### FLIR Documentation
- **SDK Manual**: Included with Spinnaker installation
- **API Reference**: FLIR Spinnaker API documentation
- **Camera Manual**: CM3-U3-13Y3M-CS user guide

### Community Support
- **FLIR Forums**: https://www.flir.com/support/forums/
- **Spinnaker GitHub**: https://github.com/FLIR/Spinnaker-Python
- **Stack Overflow**: Tag questions with `flir` and `spinnaker`

---

## 🏆 Installation Complete!

Once FLIR SDK is properly installed and PySpin is importable:
1. The ZIMON application will automatically detect FLIR cameras
2. FLIR cameras will have highest priority in camera selection
3. Full thermal imaging capabilities will be available
4. Production-ready performance optimization will be active

**Ready for thermal imaging integration!** 🎯
