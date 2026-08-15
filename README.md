# SuperSRT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**SuperSRT** is an advanced, feature-rich command-line tool for processing, manipulating, and enhancing SubRip (.srt) subtitle files. Whether you need to fix timing issues, translate between languages, batch process hundreds of files, or convert between formats, SuperSRT makes subtitle management effortless.

## 🚀 Features

- **Smart Timing Correction** - Automatically detect and fix out-of-sync subtitles with intelligent drift correction
- **Multi-Language Translation** - Translate subtitles between 100+ languages using Google Translate API
- **Batch Processing** - Process entire directories of SRT files with a single command
- **Format Conversion** - Convert SRT to VTT, TXT, CSV, ASS, and more
- **Merge & Split** - Combine multiple subtitle files or split large files into smaller chunks
- **Character Encoding Detection** - Automatically detect and convert between UTF-8, Latin-1, and other encodings
- **Content Filtering** - Remove profanity, filter specific lines, or search/replace text
- **FPS Conversion** - Convert frame rates between 23.976, 24, 25, 29.97, 30, 50, 60 fps
- **Interactive Mode** - Edit subtitles interactively with a TUI (Terminal User Interface)
- **Subtitle Alignment** - Align subtitles with audio/video files using machine learning
- **Export Statistics** - Generate word frequency, reading speed, and complexity reports

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/DAPOWER99/SuperSRT.git
cd SuperSRT

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Optional: Install with all features
pip install -e ".[full]"
```

### Docker Installation

```bash
docker build -t supersrt .
docker run --rm -v $(pwd):/data supersrt --help
```

## 🎯 Usage

### Basic Commands

```bash
# Display help
supersrt --help

# Process a single file
supersrt process -i subtitles.srt -o output.srt

# Translate subtitles to Spanish
supersrt translate -i english.srt -o spanish.srt --target es

# Fix timing issues
supersrt fix-timing -i outofsync.srt -o synced.srt --auto-detect

# Batch process all SRT files in a folder
supersrt batch -d ./subtitles -o ./output --translate es --fix-timing
```

### Command Reference

| Command | Description | Options |
|---------|-------------|---------|
| `process` | Basic processing with options | `-i, --input`, `-o, --output`, `--format`, `--encoding` |
| `translate` | Translate subtitles | `--target`, `--source`, `--service` (google, deep, openai) |
| `fix-timing` | Fix timing issues | `--shift`, `--auto-detect`, `--fps`, `--target-fps` |
| `merge` | Merge multiple SRT files | `-i, --inputs`, `-o, --output`, `--order` |
| `split` | Split SRT into parts | `-i`, `-o`, `--chunks`, `--lines-per-chunk` |
| `batch` | Process multiple files | `-d, --directory`, `-o, --output-dir`, `--parallel` |
| `convert` | Convert between formats | `-i`, `-o`, `--format` (srt, vtt, ass, ttml, sbv) |
| `filter` | Filter content | `--remove`, `--search`, `--replace`, `--regex` |
| `stats` | Generate statistics | `-i`, `--export`, `--format` (json, csv, html) |
| `interactive` | Interactive TUI mode | `-i`, `-o`, `--theme` |

## 📝 Examples

### 1. Fix Timing with Automatic Detection
```bash
supersrt fix-timing -i movie.srt -o fixed.srt --auto-detect --shift-threshold 2.0
```

### 2. Translate and Fix Timing in One Step
```bash
supersrt process -i english.srt -o spanish_fixed.srt --translate es --fix-timing
```

### 3. Batch Processing with Advanced Options
```bash
supersrt batch -d ./subtitles/ -o ./processed/ --translate fr --fix-timing --parallel 4 --verbose
```

### 4. Convert SRT to VTT with Styling
```bash
supersrt convert -i subtitles.srt -o subtitles.vtt --format vtt --style "color: white; font-size: 20px;"
```

### 5. Merge Multiple Subtitles
```bash
supersrt merge -i part1.srt part2.srt part3.srt -o complete.srt --order timestamp
```

### 6. Interactive Editing
```bash
supersrt interactive -i subtitles.srt -o edited.srt --theme dark
```

## ⚙️ Configuration

Create a `~/.supersrt/config.json` file for persistent settings:

```json
{
  "default_language": "en",
  "output_directory": "./output",
  "default_format": "srt",
  "translation_service": "google",
  "api_keys": {
    "google": "YOUR_GOOGLE_API_KEY",
    "deep": "YOUR_DEEP_API_KEY",
    "openai": "YOUR_OPENAI_API_KEY"
  },
  "parallel_workers": 4,
  "auto_backup": true,
  "encoding": "utf-8"
}
```

## 🧪 Advanced Features

### Machine Learning Integration
```bash
# AI-powered subtitle alignment
supersrt align -i subtitles.srt -a video.mp4 -o aligned.srt --model whisper

# Content improvement using AI
supersrt improve -i subtitles.srt -o improved.srt --style conversational --tone friendly
```

### Format Support Matrix

| Format | Read | Write | Features |
|--------|------|-------|----------|
| SRT | ✅ | ✅ | Full support |
| VTT | ✅ | ✅ | Styling, positioning |
| ASS/SSA | ✅ | ✅ | Advanced styling |
| TTML | ✅ | ✅ | XML-based |
| SBV | ✅ | ✅ | YouTube format |
| TXT | ✅ | ✅ | Plain text |
| CSV | ✅ | ✅ | Spreadsheet export |
| JSON | ✅ | ✅ | Programmatic access |
| SMI | ✅ | ✅ | Samsung format |

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone and create virtual environment
git clone https://github.com/DAPOWER99/SuperSRT.git
cd SuperSRT
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
pip install -e ".[test]"

# Run tests
pytest tests/
pytest --cov=supersrt tests/

# Code formatting
black supersrt/
isort supersrt/

# Type checking
mypy supersrt/
```

### Project Structure

```
supersrt/
├── __init__.py
├── cli.py              # Command-line interface
├── core/
│   ├── parser.py       # SRT parsing
│   ├── timing.py       # Timing manipulation
│   ├── translation.py  # Translation services
│   └── converter.py    # Format conversion
├── utils/
│   ├── encoding.py     # Character encoding
│   ├── filters.py      # Content filtering
│   └── aligner.py      # Subtitle alignment
├── interactive/
│   └── tui.py          # Terminal UI
└── models/
    └── embedding.py    # ML models
```

### Building from Source

```bash
# Build distribution
python -m build

# Install local package
pip install dist/supersrt-*.whl

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## 🌐 API Reference

### Python API Example

```python
from supersrt import SubtitleProcessor, Translator, TimingFixer

# Load subtitles
processor = SubtitleProcessor()
subs = processor.load("subtitles.srt")

# Fix timing
fixer = TimingFixer()
fixed = fixer.auto_correct(subs)

# Translate
translator = Translator()
translated = translator.translate(fixed, target="es")

# Save
processor.save(translated, "output.srt")
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines
- Write tests for new features
- Follow PEP 8 style guide
- Update documentation accordingly
- Ensure all tests pass
- Add examples for new functionality

## 📊 Roadmap

- [ ] Web UI for remote subtitle editing
- [ ] Real-time subtitle translation API
- [ ] Integration with media players (VLC, MPC-HC)
- [ ] Speech-to-text subtitle generation
- [ ] Subtitle sharing platform integration
- [ ] AI-powered subtitle summarization
- [ ] Cloud backup and sync
- [ ] Mobile companion app

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [pysrt](https://github.com/byroot/pysrt) - Original SRT parser inspiration
- [googletrans](https://github.com/ssut/py-googletrans) - Translation library
- [whisper](https://github.com/openai/whisper) - Audio transcription model
- [typer](https://github.com/tiangolo/typer) - CLI framework
- [rich](https://github.com/Textualize/rich) - Terminal formatting

## 📞 Contact & Support

- **GitHub Issues**: [Issue Tracker](https://github.com/DAPOWER99/SuperSRT/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DAPOWER99/SuperSRT/discussions)
- **Email**: support@supersrt.com
- **Twitter**: [@SuperSRT](https://twitter.com/SuperSRT)

## ⭐ Star History

If you find SuperSRT useful, please consider starring the repository to help others discover it!

---

**Made with ❤️ by the SuperSRT Team**
```

This README provides a comprehensive overview of what SuperSRT will become - a professional-grade subtitle processing tool with extensive features. I'll now proceed to build the actual code for this project.
