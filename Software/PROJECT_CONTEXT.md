# PROJECT_CONTEXT.md

## AI Assistant Context File

### Project Overview
**System Name**: Photoluminescence (PL) Scanner for Solar Panel Inspection  
**Main Entry Point**: `PLRobot.py`  
**Repository**: https://github.com/JeperoJ/Photoluminescence-scanner  
**Working Directory**: `C:\Users\carle\Documents\GitHub\Photoluminescence-scanner\Software\`

This system performs automated scanning and imaging of photovoltaic (PV) panels using synchronized camera and gantry motion systems to detect defects through photoluminescence and electroluminescence imaging.

---

## System Architecture

### Hardware Components

#### 1. Camera System - FLI InGaAs (C-RED3)
- **Resolution**: 640×512 pixels
- **Frame Rate**: Configurable (default: 50 FPS)
- **Exposure**: Configurable (default: 1ms, variable `tintVal`)
- **Sensor Type**: InGaAs (Indium Gallium Arsenide) - Near-infrared sensitive
- **Calibration Features**:
  - Bad pixel correction
  - NUC (Non-Uniformity Correction) bias calibration
  - Adaptive bias (C-RED3 specific)
  - Anti-blooming (prevents pixel saturation bleed)
  - Auto-clip (dynamic range adjustment)

#### 2. Gantry System - Parallel X-Y Motion Control
- **Max Travel Distance**: ~2500mm total
  - `offsetBegin`: 500mm (from end stops to effective start)
  - `offsetEnd`: 100mm (from effective end to max travel)
  - **Effective Travel**: ~1900-2000mm
- **Speed**: Configurable (default: 5000 mm/min)
- **Communication**: Serial via GCode protocol
- **Dual-Axis**: Parallel X-Y synchronization with drift compensation
- **Drift Compensation**: 0.2448 mm/step (empirically determined)
  - Corrects for X and Y axes traveling different distances while ending simultaneously
  - Critical for stitching alignment

---

## Software Architecture

### Module Structure
```
Software/
??? PLRobot.py              # Main orchestration script
??? FLI_API/                # Camera SDK wrapper
?   ??? FliSdk_V2           # FLI SDK v2 interface
??? Acquisition/            # Image acquisition logic
?   ??? imageAcquisition    # Camera init, capture, bias correction
??? Stitching/              # Image stitching algorithms
?   ??? stitchImages        # PL/Geo/Multi/Continuous stitching
??? lib/                    # Core utilities
?   ??? ProcessInGaAs       # InGaAs sensor image processing
?   ??? imageAcquisition    # Camera initialization and capture
?   ??? gCodeHandler        # GCode serial communication
?   ??? stitchImages        # Stitching implementations
??? Images/                 # Output directory for scans
??? Calibration/            # Undistortion matrices (K, P, DIM)
??? PROJECT_CONTEXT.md      # This file
```

### Key Dependencies
- **OpenCV** (`cv2`) - Image processing and display
- **tifffile** - TIFF file I/O
- **NumPy** - Matrix operations (implied, for calibration matrices)
- **FLI_API** - Vendor SDK for camera control
- **pyserial** (implied) - Serial communication for GCode

---

## Workflow Pipeline

### Phase 1: Calibration
1. **Undistortion Calibration**
   - Load existing calibration matrices: `K` (camera matrix), `P` (projection matrix), `DIM` (dimensions)
   - Default path: `./Calibration/`
   - Matrices stored as NumPy `.npy` files

2. **Camera Initialization**
   ```python
   context = FliSdk_V2.Init()
   initCamera(context, frameRate, tintVal)
   ```
   - User prompted for bias correction method (NUC vs Adaptive)
   - Anti-blooming and auto-clip enabled
   - Optional: Live preview via `justShowImage()`

3. **Gantry Calibration**
   - Check end stops (M119 GCode)
   - Auto-recovery if triggered (move 30mm away)
   - Auto-home sequence
   - Wait for completion (M400)

### Phase 2: Scanning

#### Mode 1 - Multi-Step Scan (3-position stepped acquisition)
```python
scan(gcode_handler, context, savePath, frameRate, speed=5000, nsteps=3)
```
- **Process**:
  1. Divide travel distance by `nsteps` (default: 3)
  2. Create position array: `[[0,0], [dist,dist], [2*dist,2*dist], [3*dist,3*dist]]`
  3. For each position:
     - Move camera to X position
     - Move light bar along Y while capturing images
     - Save as `scan_{step}.tiff`
- **Image Calculation**: `nImages = int(dist_travel / (speed/60) * frameRate)`
- **Buffer**: `nImages + 5` (may be too small, noted in comments)

#### Mode 2 - Continuous Scan (single-pass continuous capture)
```python
scanContinuous(gcode_handler, context, savePath, frameRate, speed=5000)
```
- **Process**:
  1. Move to start position (200, 0)
  2. Simultaneously move both axes to (2100, 2000) while capturing
  3. Save as `scan_cont_{timestamp}.tiff`
- **Buffer**: `nImages + 400` (larger buffer for continuous capture)
- **Timestamp Format**: `YYYY-MM-DD_HH-MM`

#### Mode 3 - Electroluminescence (EL) Scan (incomplete)
```python
scanEL(gcode_handler, context, savePath, frameRate, speed=5000)
```
- **Status**: Partial implementation
- **Difference**: Only moves camera axis (1800mm travel)
- **Output**: `scan_EL_cont_{timestamp}.tiff`

### Phase 3: Processing & Stitching

#### Image Loading
- **RAW files**: `ProcessInGaAs.load_raw_image(path, 640, 512)`
- **TIFF files**: `tifffile.imread()` ? `int16_2_uint16()` conversion

#### Stitching Methods
1. **roughStitchPL** - Photoluminescence-based stitching
2. **roughStitchGeo** - Geometry-based stitching (uses speed, nsteps, FPS)
3. **multiStitch** - Combines multiple `GeoPL_stitched.png` images
4. **roughStitchCont** - Continuous scan stitching (uses drift compensation)

#### Output Files
- Individual stitches: `*_stitched.png`
- Geo+PL stitches: `*_GeoPL_stitched.png`
- Final continuous: `stitched_image_cont.png`

---

## Critical Technical Details

### Scan Calculations
```python
# Number of images to capture
nImages = int(dist_travel / (speed/60) * frameRate)

# Example: 2000mm travel, 5000 mm/min speed, 50 FPS
# nImages = int(2000 / (5000/60) * 50) = int(2000 / 83.33 * 50) = 1200 images
```

### Buffer Sizing
- **Multi-step**: `nImages + 5` ?? May cause buffer overflow
- **Continuous**: `nImages + 400` (safer margin)
- **EL scan**: `nImages + 400`

### Drift Compensation
- **Value**: 0.2448 mm/step
- **Cause**: X and Y axes travel different actual distances but complete simultaneously
- **Detection**: Stitched images align at start but misalign at end
- **Application**: Used in `roughStitchCont()` function

### File Naming Conventions
| Scan Type | Filename Pattern | Extension |
|-----------|------------------|-----------|
| Multi-step | `scan_{step_number}` | `.tiff` |
| Continuous PL | `scan_cont_{timestamp}` | `.tiff` |
| Continuous EL | `scan_EL_cont_{timestamp}` | `.tiff` |
| Stitched output | `*_stitched` | `.png` |
| Geo+PL stitched | `*_GeoPL_stitched` | `.png` |

---

## Known Issues & Limitations

### Active Issues
1. **Buffer Sizing**: Multi-step scan buffer (`nImages + 5`) may be too small
2. **Error Handling**: Bare `except:` clauses catch all exceptions
3. **String Comparison**: `if scantype==1:` should be `if scantype=="1":` (line 330)
4. **Incomplete Feature**: `scanEL()` function partially implemented
5. **Calibration Path**: Alternative calibration workflow commented out

### Design Decisions
- **Interactive Prompts**: All operations require user confirmation (blocking I/O)
- **Sequential Processing**: No parallel/async operations
- **File Discovery**: Latest scan uses `os.path.getctime()` (creation time)

### Safety Features
- End-stop checking with auto-recovery (max 2 attempts per axis)
- Emergency stop capability (`x` key during prompts)
- Gantry position verification before critical operations

---

## Configuration Parameters

### Default Values (in `main()`)
```python
speed = 5000              # Gantry speed (mm/min)
frameRate = 50            # Camera frame rate (FPS)
tintVal = 1               # Exposure time (ms)
nsteps = 3                # Number of steps for multi-step scan
drift = 0.2448            # Drift compensation (mm/step)
offsetBegin = 500         # Start offset (mm)
offsetEnd = 100           # End offset (mm)
dist_travel = 2000        # Effective travel distance (mm)
```

### Camera Dimensions
```python
width = 640               # Sensor width (pixels)
height = 512              # Sensor height (pixels)
```

---

## GCode Commands Used

| Command | Purpose |
|---------|---------|
| M120 | Enable end stops |
| M119 | Check end stop status |
| M400 | Wait for all moves to complete |
| M114 | Get current position |
| G0 X## Y## | Rapid positioning move |

---

## Future Enhancements (TODOs in code)

1. **Flat Correction**: Non-uniformity response correction (currently commented out)
   - Reference: HDR mode documentation (Andor)
2. **GUI Implementation**: `GUI()` function placeholder at end of `main()`
3. **Complete EL Scanning**: Finish `scanEL()` implementation
4. **Improved Calibration Workflow**: Re-enable checkerboard calibration path

---

## Troubleshooting Guide

### Stitching Alignment Issues
- **Symptom**: Images align at start but not at end
- **Solution**: Adjust `drift` parameter in `main()`

### Buffer Overflow
- **Symptom**: Missing frames at end of acquisition
- **Solution**: Increase buffer margin in `scan()` from `+5` to `+400`

### End Stop Triggered
- **Symptom**: "End stop triggered" during calibration
- **Solution**: Automatic recovery moves 30mm away (max 2 attempts)

### Camera Not Found
- **Symptom**: `FliSdk_V2.Init()` fails
- **Solution**: Check USB connection, ensure FLI drivers installed

---

## Version Information
- **Last Updated**: Initial context file creation
- **Python Version**: 3.x (inferred from syntax)
- **FLI SDK**: V2

---

## Notes for AI Assistants

### When Modifying This Code:
1. ? Maintain existing variable names (`gCode_handler` vs `gcode_handler`)
2. ? Preserve GCode command sequences (order matters)
3. ? Keep drift compensation calculations intact
4. ? Maintain buffer size calculations (critical for data integrity)
5. ?? Test any changes to timing-sensitive operations (gantry + camera sync)

### Common User Requests:
- Adding new scan patterns ? Reference `scan()` and `scanContinuous()` structure
- Adjusting image quality ? Modify `frameRate`, `tintVal`, or calibration steps
- Changing travel distances ? Update `offsetBegin`, `offsetEnd`, `dist_travel`
- Adding new stitching methods ? See `stitchImages` module

### Code Style Notes:
- Minimal inline comments (only for complex logic)
- User prompts are verbose and instructional
- Error handling uses simple print + sys.exit() pattern
- Function parameters use descriptive names with units in comments
