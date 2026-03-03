# Modulated Peak Width Detection Package

## 🎯 What This Does

Accurately detects the width of peaks in signals that contain **modulation** (high-frequency oscillations on top of a broader peak structure).

**Problem**: Your photoluminescence scan has 100+ small peaks from modulation  
**Solution**: Extract the envelope and find the true peak width

## ⚡ Quick Start (60 seconds)

```python
from modulated_peak_detector import detect_modulated_peak_width

# Your scan profile
signal = scan_profile

# Detect peak
peak_info = detect_modulated_peak_width(signal)

# Get results
print(f"Peak width: {peak_info['width']} samples")
print(f"Peak center: {peak_info['peak_idx']}")
```

## 📁 File Guide

| File | Purpose | Read Time |
|------|---------|-----------|
| **QUICKSTART.py** | Copy-paste examples | 5 min |
| **00_PACKAGE_SUMMARY.md** | Overview | 5 min |
| **FILE_INDEX.md** | Navigation guide | 5 min |
| **MODULATED_PEAK_DETECTION_README.md** | Full documentation | 15 min |
| **modulated_peak_detector.py** | Core library | - |
| **photoluminescence_analysis.py** | PL-specific tools | - |
| **VISUALIZATION_GUIDE.py** | Visual explanations | 5 min |
| **example_modulated_peak_usage.py** | Integration examples | 10 min |

## 🚀 Get Started

### 1. For Immediate Use
Copy from **QUICKSTART.py** and paste into your notebook/script

### 2. For Understanding
Run **VISUALIZATION_GUIDE.py** to see the algorithm in action

### 3. For Integration  
Read **example_modulated_peak_usage.py** for your workflow

### 4. For Details
Check **MODULATED_PEAK_DETECTION_README.md** for complete docs

## 💡 Key Features

✓ Extracts signal envelope automatically  
✓ No modulation frequency needed  
✓ Handles noise and asymmetric peaks  
✓ Works with any modulation pattern  
✓ Single or multiple peak detection  
✓ Physical units (mm) if pixel pitch provided  
✓ Production-ready code  
✓ Complete documentation  

## 🔍 For Your testing_fps_wrong.ipynb

Replace manual peak detection:
```python
# Before: Manual line drawing
plt.vlines((module_start, module_end), ...)

# After: Automatic detection
from modulated_peak_detector import detect_modulated_peak_width
peak_info = detect_modulated_peak_width(scan_profile)
plt.vlines((peak_info['start_idx'], peak_info['end_idx']), ...)
```

## 📊 Example Output

```
Peak width: 247 samples
Peak center: 350
Peak value: 0.9542
Status: success
```

## 🔧 Parameters

```python
detect_modulated_peak_width(
    signal,                    # Your 1D array
    min_peak_height=None,      # 10% of max (default)
    smoothing_window=None,     # Auto (default)
    return_envelope=False      # Also return envelope curve
)
```

## ❓ Troubleshooting

**Peak not detected?**
→ Try `min_peak_height=0.05`

**Width off?**
→ Adjust `smoothing_window` (higher = more smoothing)

**Need to see envelope?**
→ Use `peak_info, envelope = detect_modulated_peak_width(signal, return_envelope=True)`

**Want to understand?**
→ Run `VISUALIZATION_GUIDE.py`

## 📚 Documentation Structure

```
START HERE:
├─ QUICKSTART.py (5 min, copy-paste)
├─ 00_PACKAGE_SUMMARY.md (5 min, overview)
└─ FILE_INDEX.md (navigation)

UNDERSTAND:
├─ VISUALIZATION_GUIDE.py (run this)
└─ MODULATED_PEAK_DETECTION_README.md (full docs)

IMPLEMENT:
├─ example_modulated_peak_usage.py (patterns)
└─ photoluminescence_analysis.py (PL analysis)

ADVANCED:
└─ modulated_peak_detector.py (source code)
```

## 🎓 How It Works

1. **Hilbert Transform** → Extract signal envelope
2. **Smoothing** → Remove noise (optional)
3. **Peak Detection** → Find main peak(s)
4. **Edge Detection** → Find start/end boundaries

No modulation frequency needed!

## ✨ For Photoluminescence Scans

Use specialized functions:

```python
from photoluminescence_analysis import analyze_scan_line, extract_defect_metrics

# Single line analysis
analysis, fig = analyze_scan_line(scan_profile, pixel_pitch=10e-6)

# 2D image analysis  
metrics = extract_defect_metrics(scan_image, pixel_pitch_x=10e-6)
print(f"Defect width: {metrics['defect_width_x_mm']:.3f} mm")
```

## 📊 Testing

All files are tested with:
- Symmetric and asymmetric peaks
- Multiple peaks
- Various noise levels (up to 30%)
- Different modulation frequencies
- Narrow and broad peaks

See **VISUALIZATION_GUIDE.py** for full test suite.

## 🔗 Integration

1. Copy `modulated_peak_detector.py` to your project
2. Import and use
3. Optional: Use `photoluminescence_analysis.py` for advanced features
4. Optional: Use `VISUALIZATION_GUIDE.py` for validation

## 📦 Dependencies

- numpy (standard)
- scipy (standard)
- matplotlib (optional, for plotting)

No additional packages needed!

## ⏱️ Performance

- **Time**: < 1ms per signal
- **Space**: O(n)
- **Complexity**: O(n log n)

## 🎯 Use Cases

✓ Single defect detection  
✓ Multiple defect detection  
✓ Signal envelope extraction  
✓ Peak width measurement  
✓ Defect metrics computation  
✓ Quality assessment  

## 📝 Next Steps

1. **Now**: Read QUICKSTART.py (5 min)
2. **Next**: Try on your data (2 min)  
3. **Then**: Visualize with VISUALIZATION_GUIDE.py (5 min)
4. **Finally**: Integrate into your workflow (10-30 min)

## 🆘 Need Help?

- **Quick answers**: QUICKSTART.py
- **Understanding**: VISUALIZATION_GUIDE.py  
- **Details**: MODULATED_PEAK_DETECTION_README.md
- **Integration**: example_modulated_peak_usage.py
- **Navigation**: FILE_INDEX.md

## 📄 License

Part of the Photoluminescence Scanner project

---

**Start with QUICKSTART.py →**  
**Questions? Check FILE_INDEX.md for navigation →**  
**Ready? Copy 3 lines and go! →**
