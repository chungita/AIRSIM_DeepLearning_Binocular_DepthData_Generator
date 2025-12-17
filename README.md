# AirSim Data Processing Toolkit

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Research-green)](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)

A comprehensive Python-based toolkit for processing, annotating, and analyzing AirSim simulation data. This toolkit provides a complete workflow from raw data processing to labeled dataset generation for computer vision and autonomous driving research.

> **Platform**: Currently designed for Windows 10/11 operating systems.  
> **Repository**: [https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)

## 🎯 Features

- **Multi-language Support**: Full support for Chinese and English interfaces
- **Data Generation**: Process raw AirSim data into depth maps, disparity maps, and organized image sequences
- **Image Annotation**: Manual and automatic annotation tools with YOLO and MOT format support
- **Visualization Tools**: Comprehensive viewers for images, labels, and tracking results
- **3D Tracking**: Object trajectory analysis with 3D coordinate support
- **Export Options**: Generate GIFs and videos from image sequences

## 🚀 Getting Started

### Prerequisites

#### Required Software
- **Windows 10 or 11** (Currently Windows only)
- **Unreal Engine 4 (UE4)** - Download from [Epic Games Launcher](https://www.unrealengine.com/)
- **AirSim** - Download and setup from [AirSim GitHub](https://github.com/microsoft/AirSim)

#### Python Dependencies
- Python 3.7+
- PyQt5
- NumPy
- OpenCV
- Other dependencies listed in `requirements.txt`

> **Important**: Make sure you have UE4 and AirSim properly installed and configured before using this toolkit to process simulation data.

### Installation

#### Step 1: Install UE4 and AirSim

1. Download and install **Unreal Engine 4** from [Epic Games Launcher](https://www.unrealengine.com/)
2. Download and setup **AirSim** following the [official documentation](https://github.com/microsoft/AirSim)
3. Configure AirSim in your UE4 environment

#### Step 2: Install Data Processing Toolkit

1. Clone or download this repository:
```bash
git clone https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator.git
cd AIRSIM_DeepLearning_Binocular_DepthData_Generator
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Launch the control panel:
```bash
python Control_Panel.py
```

### Initial Setup

Before processing data:

1. **Configure AirSim Settings**:
   - Copy the sample configuration file to your AirSim directory:
     ```bash
     # Windows: Copy to Documents folder
     copy "Airsim settings\settings.json" "%USERPROFILE%\Documents\AirSim\settings.json"
     ```
   - Or manually copy `Airsim settings/settings.json` to your AirSim settings directory
   - Location: `C:\Users\[YourUsername]\Documents\AirSim\settings.json`
   - **Important**: You must swap/replace the AirSim settings file with the one provided in this project before running simulations

2. **Collect Data**: Run your AirSim simulation in UE4 to collect raw data

3. **Prepare Data**: Copy your AirSim simulation output data to the `RawData/` folder

4. **Configure Processing**: Adjust parameters in `Tools&Settings/Settings.txt` according to your camera setup and data paths

## 📋 Tools Overview

### 1. Data Generator (`DataGenerator.py`)
- Process raw AirSim data
- Generate depth maps (DepthGT_*.pfm)
- Generate disparity maps (Disparity_*.pfm)
- Organize left/right camera images (Img0_*, Img1_*)
- Process semantic segmentation images (Seg_*)
- Copy results to output folder

### 2. Image Labeler (`Img_Labeler.py`)
- **Manual Mode**: Draw bounding boxes manually
- **Batch Mode**: Automatic color-based object detection
- Generate YOLO format labels
- Generate MOT format labels with 3D coordinates
- Save annotation statistics and results

### 3. Image Viewer (`PIC_Read.py`)
- View depth maps with customizable color mapping
- View disparity maps
- View original camera images
- Support for various image formats

### 4. Label Viewer (`Label_Show.py`)
- Visualize YOLO format annotations
- Visualize MOT format annotations
- Verify bounding box accuracy
- Class distribution analysis

### 5. Track Analyzer (`Track.py`)
- Display object trajectories
- 3D position tracking
- Multi-object tracking visualization
- Export tracking results

### 6. GIF Generator (`Gifer.py`)
- Create animated GIFs from image sequences
- Customizable frame rate and quality
- Batch processing support

### 7. Video Converter (`Video_Convertor.py`)
- Convert image sequences to video files
- Multiple video format support
- Configurable encoding settings

## 📁 Project Structure

```
DataGenerator/
├── Control_Panel.py          # Main control panel application
├── README.md                 # This file
├── RawData/                  # Raw AirSim data input folder
├── ProcessData/              # Processed images and depth data
├── Results/                  # Final output folder
│   ├── Img/                 # Final image output
│   ├── YOLO_Label/          # YOLO format label files
│   └── MOT_Label/           # MOT format label files
├── Airsim settings/
│   └── settings.json        # AirSim configuration (sample settings available)
└── Tools&Settings/
    ├── DataGenerator.py     # Data processing tool
    ├── Img_Labeler.py       # Image annotation tool
    ├── PIC_Read.py          # Image viewer
    ├── Label_Show.py        # Label viewer
    ├── Track.py             # Tracking analyzer
    ├── Gifer.py             # GIF generator
    ├── Video_Convertor.py   # Video converter
    ├── Settings.txt         # Main configuration file
    ├── Settings_Editor.py   # Settings editor GUI
    └── predefined_classes.txt # Object class definitions
```

## 🔧 Workflow

### Recommended Processing Order:

1. **Setup AirSim Settings**: Copy `Airsim settings/settings.json` to your AirSim directory (`Documents/AirSim/settings.json`)
2. **Run Simulation**: Launch UE4 with AirSim and collect simulation data
3. **Prepare Raw Data**: Copy collected AirSim data to the `RawData/` folder
4. **Check Processing Settings**: Verify parameters in `Tools&Settings/Settings.txt` (camera parameters, paths, etc.)
5. **Run Data Generator**: Process raw data and generate depth/disparity maps
6. **Annotate Images**: Use manual or automatic mode to label objects
7. **Verify Results**: Use viewers to confirm annotation quality
8. **Generate Output**: Export labels and create demo animations

## ⚙️ Configuration

### AirSim Configuration

The `Airsim settings/settings.json` file contains optimized AirSim configuration for this toolkit:
- **Stereo camera setup** with proper baseline and focal length
- **Depth and segmentation sensors** configuration
- **Image capture settings** for optimal data collection
- **Must be copied** to your AirSim directory before running simulations

**Setup Steps**:
1. Backup your existing AirSim settings (if any)
2. Copy `Airsim settings/settings.json` to `Documents/AirSim/settings.json`
3. Restart UE4/AirSim to apply the new settings
4. The toolkit's processing tools are calibrated to work with these camera parameters

### Processing Configuration

The main configuration file `Tools&Settings/Settings.txt` contains:
- Camera parameters (focal length, baseline, image dimensions)
- Input/output paths
- Processing settings
- Color thresholds for automatic annotation

Edit settings using:
- Built-in Settings Editor (accessible from Control Panel)
- Manual editing of `Settings.txt`

## 💡 Tips & Best Practices

- **Depth Map Issues**: Check MaxDepth setting if depth maps display abnormally
- **Poor Annotation**: Adjust color threshold parameters in settings
- **Batch Processing**: Test with a small range before processing large datasets
- **Backup**: Regularly backup important annotation results
- **Performance**: Close unused viewer windows to improve performance

## 🖥️ System Requirements

- **OS**: Windows 10/11 (Currently Windows only)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: Depends on dataset size (allow several GB for processed data)
- **Display**: 1920x1080 minimum resolution recommended

> **Note**: This toolkit is currently optimized for Windows operating systems. Linux and macOS support may be added in future releases.

## 🌐 Language Support

The toolkit supports both Chinese and English interfaces. Click the "🌐 Language" button in the Control Panel to switch between languages. All tools will launch with the selected language.

## 📝 Output Formats

### YOLO Format
```
<class_id> <x_center> <y_center> <width> <height>
```
All values are normalized (0.0 to 1.0)

### MOT Format
```
<frame_id>,<track_id>,<x>,<y>,<width>,<height>,<confidence>,<class_id>,<visibility>,<x_3d>,<y_3d>,<z_3d>
```
Includes 3D coordinates from depth information

## 🐛 Troubleshooting

- **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
- **File Not Found**: Check that paths in `Settings.txt` are correct
- **GUI Not Displaying**: Verify PyQt5 installation: `pip install PyQt5`
- **Depth Map Errors**: Ensure .pfm files are valid and not corrupted
- **Incorrect Depth Values**: Make sure you copied `Airsim settings/settings.json` to your AirSim directory before data collection
- **Missing Camera Images**: Verify that the AirSim settings file includes stereo camera configuration
- **No Data to Process**: Verify that AirSim simulation has been run and data has been collected
- **Processing Results Incorrect**: Check that your AirSim settings match the provided settings.json file
- **AirSim Configuration Issues**: Refer to the [AirSim documentation](https://microsoft.github.io/AirSim/) for setup help

## 📄 License

This project is provided as-is for research and educational purposes.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator/issues).

If you find this project helpful, please consider giving it a ⭐ on [GitHub](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)!

## 👥 Authors

- **chungita** - [GitHub Profile](https://chungita.com/)

## 📧 Contact

For questions or support, please open an issue in the [repository](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator/issues).

---

## 📌 Important Notes

- **AirSim Dependency**: This toolkit is specifically designed to process data collected from AirSim simulations running in Unreal Engine 4
- **Pre-requisites**: You must have UE4 and AirSim installed and configured before using this data processing toolkit
- **⚠️ Critical - Settings File**: You **MUST** copy `Airsim settings/settings.json` to your AirSim directory (`Documents/AirSim/settings.json`) before running simulations. The processing tools rely on specific camera configurations defined in this file
- **Data Source**: The toolkit processes simulation data from AirSim, not real-world data
- **Camera Calibration**: The depth calculation and stereo processing are calibrated to work with the camera parameters in the provided settings.json file

For more information about AirSim setup and usage, visit the [official AirSim documentation](https://microsoft.github.io/AirSim/).

## 🔗 Related Links

- **GitHub Repository**: [AIRSIM_DeepLearning_Binocular_DepthData_Generator](https://github.com/chungita/AIRSIM_DeepLearning_Binocular_DepthData_Generator)
- **AirSim Official**: [Microsoft AirSim](https://github.com/microsoft/AirSim)
- **Unreal Engine**: [Epic Games Unreal Engine](https://www.unrealengine.com/)
- **AirSim Documentation**: [https://microsoft.github.io/AirSim/](https://microsoft.github.io/AirSim/)

---

Mostly vibe coding, so there must be a lot of stupid writing.

