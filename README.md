# VideoMaker-Pro v1.0

## Automated Bulk Video Editor

VideoMaker-Pro is a Windows desktop application built with Python and Tkinter that automates the creation of long-form videos from scripts using pre-existing clips, text-to-speech APIs, and configurable branding elements.

## Features

### Core Functionality
- **Text-to-Speech Integration**: Supports MiniMax and Replicate TTS APIs
- **Brand Kit Management**: Configurable templates with intro clips, watermarks, and overlays
- **Video Processing Pipeline**: Automated assembly with FFmpeg
- **Queue Management**: Background processing with progress tracking
- **Transitions**: Smooth crossfade transitions between video segments

### Brand Kit Components
- Intro clips (3-7 second logo reveals)
- Auto intro with typewriter text effects
- Watermarks with configurable positioning
- Avatar overlays (animated talking heads)
- Subscribe call-to-action overlays
- Background music integration
- Color grading with LUT support
- Mask effects and overlays

### Video Processing Features
- Multiple aspect ratios (16:9 landscape, 9:16 portrait)
- Automatic clip sequencing or randomization
- Audio synchronization with video content
- Caption generation and styling
- Real-time progress tracking
- Error handling and retry mechanisms

## System Requirements

### Software Dependencies
- Python 3.7 or higher
- FFmpeg (must be installed separately)
- Windows 10 or higher

### Hardware Requirements
- Minimum 4GB RAM (8GB recommended)
- 1GB free disk space for temporary files
- Internet connection for TTS API access

## Installation

### 1. Install Python
Download and install Python 3.7+ from [python.org](https://python.org)

### 2. Install FFmpeg
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH
4. Verify installation by running `ffmpeg -version` in Command Prompt

### 3. Install VideoMaker-Pro
```bash
# Clone or download the project
git clone <repository-url>
cd videomaker-pro

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Configuration

### API Keys Setup
1. Open the **Configuration** tab
2. Enter your API keys:
   - **MiniMax**: Get from [minimax.chat](https://minimax.chat)
   - **Replicate**: Get from [replicate.com](https://replicate.com)
3. Click **Save Configuration**

### Brand Kit Creation
1. Go to the **Brand Kits** tab
2. Click **New Brand Kit**
3. Configure your brand assets:
   - Upload intro clip or background image
   - Add watermark (16:9 PNG with transparency)
   - Upload video clips for main content
   - Configure voice settings and overlays
4. Save your brand kit

## Usage

### Creating a Video
1. **Home Tab**: Enter your video details
   - **Title**: Your video title (used in intro)
   - **Script**: The text to be converted to speech
   - **Brand Kit**: Select from your configured brand kits
   - **Aspect Ratio**: Choose 16:9 or 9:16
   - **Output Filename**: Optional custom filename

2. **Generate Video**: Click the generate button
   - Processing happens in the background
   - Progress is shown in real-time
   - Completed videos are saved to the output folder

### Video Processing Pipeline
1. **TTS Generation**: Script converted to audio
2. **Intro Creation**: Typewriter effect with title
3. **Clip Assembly**: Video clips sequenced to match audio length
4. **Audio Sync**: TTS audio synchronized with video
5. **Overlays Added**: Watermarks, avatars, and CTAs applied
6. **Effects Applied**: LUTs, masks, and final processing
7. **Output Generated**: Final video saved to output directory

## Project Structure

```
videomaker-pro/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.json            # Application configuration
├── core/                   # Core processing modules
│   ├── video_processor.py  # Main video processing pipeline
│   ├── ffmpeg_utils.py     # FFmpeg wrapper utilities
│   └── config_manager.py   # Configuration management
├── models/                 # Data models
│   ├── brand_kit.py        # Brand kit configuration
│   └── video_project.py    # Video project management
├── processors/             # Specialized processors
│   ├── tts_processor.py    # Text-to-speech handling
│   ├── subtitle_generator.py # Subtitle generation
│   └── effect_processor.py # Video effects
├── gui/                    # User interface
│   ├── main_window.py      # Main application window
│   ├── config_panel.py     # Configuration interface
│   ├── brand_kit_panel.py  # Brand kit management
│   └── progress_dialog.py  # Progress tracking
├── queue/                  # Task management
│   ├── job_queue.py        # Job queuing system
│   └── task_manager.py     # Background task handling
├── services/               # External API integrations
│   ├── minimax_service.py  # MiniMax TTS integration
│   └── replicate_service.py # Replicate API integration
├── storage/                # File and asset management
│   ├── file_manager.py     # File operations
│   └── asset_manager.py    # Asset organization
└── utils/                  # Utility functions
    ├── helpers.py          # General helpers
    └── validators.py       # Input validation
```

## API Integration

### MiniMax TTS
- Supports multiple languages and voices
- High-quality speech synthesis
- Cost-effective for bulk processing

### Replicate Voice Cloning
- Custom voice model support
- Realistic voice cloning capabilities
- Advanced voice customization options

## Troubleshooting

### Common Issues

**FFmpeg Not Found**
- Ensure FFmpeg is installed and in system PATH
- Test with `ffmpeg -version` in Command Prompt

**API Errors**
- Verify API keys are correct
- Check internet connection
- Ensure API quotas are not exceeded

**Memory Issues**
- Reduce max concurrent jobs in configuration
- Process smaller video segments
- Ensure sufficient disk space for temporary files

**Video Quality Issues**
- Check source clip quality
- Verify aspect ratio settings
- Test with different video codecs

### Performance Optimization
- Use SSD storage for temporary files
- Increase available RAM
- Process videos during off-peak hours
- Use lower resolution clips for faster processing

## Future Enhancements (v2.0)

- AI-driven clip selection
- Automated script generation
- Advanced voice cloning
- Cloud processing support
- Batch video generation
- Enhanced transition effects
- Real-time preview
- Template marketplace

## Technical Support

For technical support and bug reports:
1. Check the troubleshooting section
2. Verify system requirements
3. Test with sample brand kits
4. Submit issues with detailed error logs

## License

This project is provided as-is for educational and commercial use. See license file for details.

## Acknowledgments

- FFmpeg team for video processing capabilities
- MiniMax for TTS API services
- Replicate for voice cloning technology
- Python community for excellent libraries and tools
