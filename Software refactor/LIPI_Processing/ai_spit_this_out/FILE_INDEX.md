# Modulated Peak Width Detection - File Index

## Quick Navigation

### 🚀 **START HERE**
- **00_PACKAGE_SUMMARY.md** - Overview of the solution
- **QUICKSTART.py** - Copy-paste examples (3 lines to get started!)

### 📚 **Documentation**
- **MODULATED_PEAK_DETECTION_README.md** - Full technical documentation
  - How it works (Hilbert Transform)
  - Parameter tuning guide
  - Comparison with other methods
  - Troubleshooting

### 💻 **Code Files**

#### Core Library
- **modulated_peak_detector.py** - Main detection engine
  - `detect_modulated_peak_width()` - Detect single peak
  - `detect_multiple_modulated_peaks()` - Find multiple peaks
  - Helper functions for envelope extraction

#### Specialized Tools
- **photoluminescence_analysis.py** - High-level analysis for your use case
  - `analyze_scan_line()` - Detailed line profile analysis
  - `extract_defect_metrics()` - Complete 2D image analysis
  - `compare_scan_lines()` - Consistency checking

#### Examples & Guides
- **example_modulated_peak_usage.py** - Integration examples
- **VISUALIZATION_GUIDE.py** - Visual explanations with plots
  - See what Hilbert Transform does
  - Understand parameter impact
  - View edge case handling

### 📖 **How to Use This Package**

#### Step 1: Understand (5 minutes)
```
Read: 00_PACKAGE_SUMMARY.md
Run: VISUALIZATION_GUIDE.py (see visualizations)
```

#### Step 2: Try (2 minutes)
```
Copy from: QUICKSTART.py
Paste into: Your notebook/script
Run on: Your scan_profile
```

#### Step 3: Integrate (10-30 minutes)
```
Study: example_modulated_peak_usage.py
Adapt for: Your specific workflow
Use: photoluminescence_analysis.py for 2D images
```

#### Step 4: Tune (as needed)
```
Reference: MODULATED_PEAK_DETECTION_README.md (Parameter Tuning section)
Adjust: min_peak_height, smoothing_window
Iterate: Until results match your expectations
```

## File Structure

```
modulated_peak_detector/
│
├── Core Library
│   └── modulated_peak_detector.py           # Main detection engine
│
├── Specialized Analysis  
│   └── photoluminescence_analysis.py        # For PL/EL scan data
│
├── Documentation
│   ├── 00_PACKAGE_SUMMARY.md                # This package
│   ├── MODULATED_PEAK_DETECTION_README.md   # Full documentation
│   └── FILE_INDEX.md                        # This file
│
├── Examples & Guides
│   ├── QUICKSTART.py                        # Start here! Copy-paste code
│   ├── example_modulated_peak_usage.py      # Integration examples
│   └── VISUALIZATION_GUIDE.py               # Visual explanations
│
└── Requirements
    └── scipy, numpy                         # Standard libraries
```

## Use Cases & Which File to Read

### Use Case 1: "I just want to detect peak width"
```
1. Read: QUICKSTART.py (copy-paste)
2. Run: Your signal through detect_modulated_peak_width()
3. Done!
```

### Use Case 2: "I need to analyze a scan line from my photoluminescence data"
```
1. Read: QUICKSTART.py for basic understanding
2. Use: photoluminescence_analysis.analyze_scan_line()
3. Reference: example_modulated_peak_usage.py for integration
```

### Use Case 3: "I need to analyze a complete 2D scan image"
```
1. Read: 00_PACKAGE_SUMMARY.md (overview)
2. Use: photoluminescence_analysis.extract_defect_metrics()
3. Reference: VISUALIZATION_GUIDE.py for understanding
4. Study: MODULATED_PEAK_DETECTION_README.md for details
```

### Use Case 4: "I'm getting unexpected results, need to tune parameters"
```
1. Read: MODULATED_PEAK_DETECTION_README.md → Parameter Tuning
2. Try: Different min_peak_height and smoothing_window values
3. Visualize: Using code from VISUALIZATION_GUIDE.py
4. Reference: Troubleshooting section in README
```

### Use Case 5: "I want to understand how it works"
```
1. Read: 00_PACKAGE_SUMMARY.md → Key Concepts
2. Run: VISUALIZATION_GUIDE.py → See visualizations
3. Study: MODULATED_PEAK_DETECTION_README.md → Mathematical Details
4. Examine: Source code in modulated_peak_detector.py
```

## Key Functions at a Glance

### Simple (3-line) Usage
```python
from modulated_peak_detector import detect_modulated_peak_width
peak_info = detect_modulated_peak_width(signal)
print(peak_info['width'])  # Width in samples
```

### With Visualization
```python
from modulated_peak_detector import detect_modulated_peak_width
peak_info, envelope = detect_modulated_peak_width(signal, return_envelope=True)
# Use envelope for plotting
```

### For Photoluminescence Scans
```python
from photoluminescence_analysis import analyze_scan_line
analysis, fig = analyze_scan_line(scan_profile, pixel_pitch=10e-6)
print(analysis['width_physical'])  # Width in mm
```

### For 2D Images
```python
from photoluminescence_analysis import extract_defect_metrics
metrics = extract_defect_metrics(scan_image, pixel_pitch_x=10e-6)
print(metrics['defect_width_x_mm'])  # Width in mm
```

## Common Questions

**Q: Where do I start?**  
A: Read `00_PACKAGE_SUMMARY.md`, then copy-paste from `QUICKSTART.py`

**Q: What if peak isn't detected?**  
A: See Troubleshooting in `MODULATED_PEAK_DETECTION_README.md`

**Q: How do I adjust parameters?**  
A: Read Parameter Tuning section in `MODULATED_PEAK_DETECTION_README.md`

**Q: Can I see what the algorithm does?**  
A: Run `VISUALIZATION_GUIDE.py` to see step-by-step visualizations

**Q: How do I integrate into my workflow?**  
A: See `example_modulated_peak_usage.py` for integration patterns

**Q: What if I have multiple peaks?**  
A: Use `detect_multiple_modulated_peaks()` from `modulated_peak_detector.py`

**Q: Can it handle noisy data?**  
A: Yes! See "Edge Cases" in `VISUALIZATION_GUIDE.py`

## Dependencies

- `numpy` - Array operations
- `scipy` - Signal processing (Hilbert transform, find_peaks)
- `matplotlib` - Visualization (optional, for plotting)

No external specialized packages needed!

## Performance

- **Time Complexity**: O(n log n) due to FFT in Hilbert transform
- **Space Complexity**: O(n) for signal storage
- **Typical Runtime**: <1ms for 1000-sample signal on modern hardware

## Integration Checklist

- [ ] Copy `modulated_peak_detector.py` to your project
- [ ] Read `QUICKSTART.py` 
- [ ] Try basic example with your data
- [ ] Adjust parameters if needed (see README)
- [ ] Integrate into your pipeline
- [ ] Run `VISUALIZATION_GUIDE.py` to validate
- [ ] (Optional) Use `photoluminescence_analysis.py` for advanced features

## Support & Troubleshooting

1. **Peak not detected?**
   - See QUICKSTART.py → Troubleshooting Checklist
   - Try: `min_peak_height=0.05`

2. **Boundaries off?**
   - Adjust smoothing_window parameter
   - Increase if too narrow, decrease if too wide

3. **Want to understand better?**
   - Run VISUALIZATION_GUIDE.py
   - Read MODULATED_PEAK_DETECTION_README.md

4. **Questions about integration?**
   - Check example_modulated_peak_usage.py
   - See photoluminescence_analysis.py for your use case

## Files Summary Table

| File | Purpose | Read Time | Difficulty |
|------|---------|-----------|-----------|
| 00_PACKAGE_SUMMARY.md | Overview | 5 min | Easy |
| QUICKSTART.py | Copy-paste examples | 5 min | Easy |
| MODULATED_PEAK_DETECTION_README.md | Full docs | 15 min | Medium |
| modulated_peak_detector.py | Main code | - | Medium |
| photoluminescence_analysis.py | PL analysis | 10 min | Medium |
| example_modulated_peak_usage.py | Integration | 10 min | Medium |
| VISUALIZATION_GUIDE.py | Visual explanations | 5 min | Easy |

## Recommended Reading Order

1. **For quick start**: QUICKSTART.py → Try it → Done
2. **For full understanding**: 
   - 00_PACKAGE_SUMMARY.md
   - VISUALIZATION_GUIDE.py (run it)
   - MODULATED_PEAK_DETECTION_README.md
   - modulated_peak_detector.py (source)
3. **For integration**: example_modulated_peak_usage.py → photoluminescence_analysis.py

---

**Last Updated**: 2026-03-03  
**For**: Photoluminescence Scanner Project  
**Package Version**: 1.0
