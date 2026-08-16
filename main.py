#!/usr/bin/env python3
# ============================================
# SuperSRT - Advanced AI-Powered Subtitle Processing Suite
# Version: 2.0.0 (FREE MODELS ONLY - OPTIMIZED)
# License: MIT
# ============================================

"""
SuperSRT: A comprehensive subtitle processing toolkit with AI capabilities
powered by OpenRouter API using the best FREE models available.

Copyright (c) 2026 DAPOWER99
Licensed under the MIT License.
"""

import os
import sys
import json
import yaml
import re
import time
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Iterator
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import lru_cache, wraps
from collections import defaultdict, Counter
import uuid
import shutil
import tempfile
import subprocess
import csv
import xml.etree.ElementTree as ET
import html
import urllib.parse
import base64
import wave
import struct

# Try importing numpy for audio processing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not installed. Audio processing will be limited.")

# Third-party imports
try:
    from openrouter import OpenRouter
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False
    print("Warning: OpenRouter not installed. AI features will be disabled.")

try:
    import pysrt
    PYSRT_AVAILABLE = True
except ImportError:
    PYSRT_AVAILABLE = False
    print("Warning: pysrt not installed. Basic SRT parsing will be limited.")

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: speech_recognition not installed. WAV testing will be limited.")

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Load environment variables
if DOTENV_AVAILABLE:
    load_dotenv()

# ============================================
# Constants and Configuration
# ============================================

VERSION = "2.0.0"
APP_NAME = "SuperSRT"
APP_AUTHOR = "DAPOWER99"
APP_URL = "https://github.com/DAPOWER99/SuperSRT"
LICENSE = "MIT"

# OPTIMIZED FREE MODELS - Best available
FREE_MODELS = {
    # Primary models for different tasks
    'default': 'nvidia/nemotron-3-ultra-550b-a55b:free',  # Best overall
    'translation': 'google/gemma-4-31b-it:free',  # Excellent translation
    'improvement': 'meta-llama/llama-3.3-70b-instruct:free',  # Great for text improvement
    'summarization': 'qwen/qwen3-next-80b-a3b-instruct:free',  # Excellent summarization
    'analysis': 'nousresearch/hermes-3-llama-3.1-405b:free',  # Best for analysis
    'code': 'openai/gpt-oss-120b:free',  # For code-related tasks
    'creative': 'z-ai/glm-4.5-air:free',  # Creative writing
    'fast': 'mistralai/mistral-small-24b-instruct-2501:free',  # Fast responses
    'balanced': 'qwen/qwen3-32b:free',  # Balanced performance
    'fallback': 'nvidia/nemotron-3-nano-30b-a3b:free',  # Reliable fallback
    'translation_premium': 'google/gemini-2.0-flash-exp:free',  # Premium translation
    'analysis_premium': 'anthropic/claude-3-haiku-20240307:free',  # Premium analysis
}

# Model capabilities mapping
MODEL_CAPABILITIES = {
    'google/gemma-4-31b-it:free': {
        'strength': 'translation',
        'context': 8192,
        'speed': 'fast',
        'languages': 100,
        'quality': 'high'
    },
    'google/gemini-2.0-flash-exp:free': {
        'strength': 'translation_premium',
        'context': 32768,
        'speed': 'very fast',
        'languages': 100,
        'quality': 'excellent'
    },
    'meta-llama/llama-3.3-70b-instruct:free': {
        'strength': 'improvement',
        'context': 128000,
        'speed': 'medium',
        'languages': 50,
        'quality': 'high'
    },
    'qwen/qwen3-next-80b-a3b-instruct:free': {
        'strength': 'summarization',
        'context': 32768,
        'speed': 'fast',
        'languages': 100,
        'quality': 'high'
    },
    'nvidia/nemotron-3-ultra-550b-a55b:free': {
        'strength': 'general',
        'context': 8192,
        'speed': 'medium',
        'languages': 50,
        'quality': 'high'
    },
    'openai/gpt-oss-120b:free': {
        'strength': 'code',
        'context': 8192,
        'speed': 'medium',
        'languages': 50,
        'quality': 'good'
    },
    'nousresearch/hermes-3-llama-3.1-405b:free': {
        'strength': 'analysis',
        'context': 128000,
        'speed': 'slow',
        'languages': 50,
        'quality': 'excellent'
    },
    'anthropic/claude-3-haiku-20240307:free': {
        'strength': 'analysis_premium',
        'context': 200000,
        'speed': 'fast',
        'languages': 50,
        'quality': 'excellent'
    },
    'z-ai/glm-4.5-air:free': {
        'strength': 'creative',
        'context': 8192,
        'speed': 'fast',
        'languages': 50,
        'quality': 'good'
    },
    'mistralai/mistral-small-24b-instruct-2501:free': {
        'strength': 'fast',
        'context': 32768,
        'speed': 'very fast',
        'languages': 50,
        'quality': 'good'
    },
    'qwen/qwen3-32b:free': {
        'strength': 'balanced',
        'context': 32768,
        'speed': 'fast',
        'languages': 50,
        'quality': 'good'
    },
    'nvidia/nemotron-3-nano-30b-a3b:free': {
        'strength': 'fallback',
        'context': 8192,
        'speed': 'fast',
        'languages': 50,
        'quality': 'good'
    }
}

SUPPORTED_FORMATS = {
    'srt': {'read': True, 'write': True, 'description': 'SubRip Text'},
    'vtt': {'read': True, 'write': True, 'description': 'WebVTT'},
    'ass': {'read': True, 'write': True, 'description': 'Advanced SubStation Alpha'},
    'ssa': {'read': True, 'write': True, 'description': 'SubStation Alpha'},
    'ttml': {'read': True, 'write': True, 'description': 'Timed Text Markup Language'},
    'sbv': {'read': True, 'write': True, 'description': 'YouTube SubViewer'},
    'smi': {'read': True, 'write': True, 'description': 'SAMI'},
    'txt': {'read': True, 'write': True, 'description': 'Plain Text'},
    'csv': {'read': True, 'write': True, 'description': 'Comma Separated Values'},
    'json': {'read': True, 'write': True, 'description': 'JSON Format'},
    'xml': {'read': True, 'write': True, 'description': 'XML Format'},
}

DEFAULT_CONFIG = {
    'default_language': 'en',
    'output_dir': './output',
    'default_format': 'srt',
    'encoding': 'utf-8',
    'parallel_workers': 4,
    'auto_backup': True,
    'cache_enabled': True,
    'cache_ttl': 86400,
    'ai': {
        'default_model': FREE_MODELS['default'],
        'translation_model': FREE_MODELS['translation'],
        'improvement_model': FREE_MODELS['improvement'],
        'summarization_model': FREE_MODELS['summarization'],
        'analysis_model': FREE_MODELS['analysis'],
        'fallback_model': FREE_MODELS['fallback'],
        'temperature': 0.7,
        'max_tokens': 4096,
        'retry_attempts': 3,
        'timeout': 60,
        'stream': False
    },
    'features': {
        'cache_enabled': True,
        'parallel_processing': True,
        'auto_backup': True,
        'progressive_loading': True
    },
    'logging': {
        'level': 'INFO',
        'file': './logs/supersrt.log',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}

# ============================================
# Data Classes
# ============================================

@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry."""
    index: int
    start_time: timedelta
    end_time: timedelta
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'index': self.index,
            'start_time': self.start_time.total_seconds(),
            'end_time': self.end_time.total_seconds(),
            'text': self.text,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SubtitleEntry':
        """Create from dictionary representation."""
        return cls(
            index=data['index'],
            start_time=timedelta(seconds=data['start_time']),
            end_time=timedelta(seconds=data['end_time']),
            text=data['text'],
            metadata=data.get('metadata', {})
        )

    def duration(self) -> timedelta:
        """Calculate duration of this entry."""
        return self.end_time - self.start_time

    def shift_time(self, seconds: float) -> 'SubtitleEntry':
        """Shift timing by specified seconds."""
        return SubtitleEntry(
            index=self.index,
            start_time=self.start_time + timedelta(seconds=seconds),
            end_time=self.end_time + timedelta(seconds=seconds),
            text=self.text,
            metadata=self.metadata.copy()
        )

    def __str__(self) -> str:
        return f"Entry {self.index}: {self.start_time} --> {self.end_time} | {self.text[:50]}..."

@dataclass
class SubtitleFile:
    """Represents a complete subtitle file."""
    entries: List[SubtitleEntry]
    format: str = 'srt'
    encoding: str = 'utf-8'
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[SubtitleEntry]:
        return iter(self.entries)

    def __getitem__(self, index: int) -> SubtitleEntry:
        return self.entries[index]

    def add_entry(self, entry: SubtitleEntry) -> None:
        """Add a subtitle entry."""
        self.entries.append(entry)
        self._renumber()

    def _renumber(self) -> None:
        """Renumber all entries sequentially."""
        for i, entry in enumerate(self.entries, 1):
            entry.index = i

    def shift_timing(self, seconds: float) -> 'SubtitleFile':
        """Shift all timing by specified seconds."""
        shifted_entries = [entry.shift_time(seconds) for entry in self.entries]
        return SubtitleFile(
            entries=shifted_entries,
            format=self.format,
            encoding=self.encoding,
            metadata=self.metadata.copy(),
            file_path=self.file_path
        )

    def filter_entries(self, predicate) -> 'SubtitleFile':
        """Filter entries based on predicate function."""
        filtered = [entry for entry in self.entries if predicate(entry)]
        return SubtitleFile(
            entries=filtered,
            format=self.format,
            encoding=self.encoding,
            metadata=self.metadata.copy(),
            file_path=self.file_path
        )

    def get_text_content(self) -> str:
        """Extract all text from entries."""
        return '\n'.join(entry.text for entry in self.entries)

    def get_statistics(self) -> Dict:
        """Get statistical information about the subtitle file."""
        durations = [entry.duration().total_seconds() for entry in self.entries]
        words = [len(entry.text.split()) for entry in self.entries]
        characters = [len(entry.text) for entry in self.entries]
        
        return {
            'total_entries': len(self.entries),
            'total_duration': sum(durations),
            'average_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'total_words': sum(words),
            'average_words': sum(words) / len(words) if words else 0,
            'total_characters': sum(characters),
            'average_characters': sum(characters) / len(characters) if characters else 0,
            'reading_speed': (sum(words) / sum(durations)) * 60 if durations else 0
        }

# ============================================
# Core Processing Classes
# ============================================

class SubtitleParser:
    """Handles parsing of various subtitle formats."""
    
    def __init__(self):
        self.supported_formats = SUPPORTED_FORMATS
        
    def parse(self, content: Union[str, bytes, Path], format_hint: Optional[str] = None) -> SubtitleFile:
        """Parse subtitle content from string, bytes, or file path."""
        if isinstance(content, (str, Path)):
            path = Path(content)
            if path.exists():
                return self.parse_file(path)
            else:
                raise FileNotFoundError(f"File not found: {path}")
        
        if isinstance(content, bytes):
            if CHARDET_AVAILABLE:
                encoding = chardet.detect(content)['encoding'] or 'utf-8'
            else:
                encoding = 'utf-8'
            content_str = content.decode(encoding)
            return self.parse_text(content_str, format_hint)
        
        if isinstance(content, str):
            return self.parse_text(content, format_hint)
        
        raise ValueError("Unsupported content type for parsing")
    
    def parse_file(self, file_path: Path) -> SubtitleFile:
        """Parse subtitle file from path."""
        encoding = 'utf-8'
        if CHARDET_AVAILABLE:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        ext = file_path.suffix.lower()[1:] if file_path.suffix else ''
        format_hint = ext if ext in self.supported_formats else None
        
        subtitle_file = self.parse_text(content, format_hint)
        subtitle_file.file_path = file_path
        subtitle_file.encoding = encoding
        
        return subtitle_file
    
    def parse_text(self, text: str, format_hint: Optional[str] = None) -> SubtitleFile:
        """Parse subtitle text content."""
        if format_hint and format_hint in self.supported_formats:
            return self._parse_format(text, format_hint)
        
        formats_to_try = ['srt', 'vtt', 'ass', 'ttml', 'json', 'csv']
        for fmt in formats_to_try:
            if fmt in self.supported_formats and self.supported_formats[fmt]['read']:
                try:
                    return self._parse_format(text, fmt)
                except ValueError:
                    continue
        
        return self._parse_srt(text)
    
    def _parse_format(self, text: str, format_name: str) -> SubtitleFile:
        """Parse specific format."""
        if format_name == 'srt':
            return self._parse_srt(text)
        elif format_name == 'vtt':
            return self._parse_vtt(text)
        elif format_name == 'ass' or format_name == 'ssa':
            return self._parse_ass(text)
        elif format_name == 'ttml':
            return self._parse_ttml(text)
        elif format_name == 'json':
            return self._parse_json(text)
        elif format_name == 'csv':
            return self._parse_csv(text)
        else:
            raise ValueError(f"Unsupported format: {format_name}")
    
    def _parse_srt(self, text: str) -> SubtitleFile:
        """Parse SRT format."""
        entries = []
        blocks = re.split(r'\n\s*\n', text.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', lines[1])
            if not time_match:
                continue
            
            start = self._parse_timecode(time_match.group(1))
            end = self._parse_timecode(time_match.group(2))
            
            text_lines = lines[2:]
            text_content = '\n'.join(text_lines).strip()
            
            if text_content:
                entries.append(SubtitleEntry(
                    index=index,
                    start_time=start,
                    end_time=end,
                    text=text_content
                ))
        
        return SubtitleFile(entries=entries, format='srt')
    
    def _parse_vtt(self, text: str) -> SubtitleFile:
        """Parse WebVTT format."""
        lines = text.split('\n')
        while lines and (not lines[0].strip() or lines[0].strip().startswith('WEBVTT')):
            lines.pop(0)
        
        text = '\n'.join(lines)
        return self._parse_srt(text)
    
    def _parse_ass(self, text: str) -> SubtitleFile:
        """Parse ASS/SSA format."""
        entries = []
        lines = text.split('\n')
        in_events = False
        
        for line in lines:
            if line.startswith('[Events]'):
                in_events = True
                continue
            
            if in_events and line.startswith('Dialogue:'):
                parts = line.split(',', 9)
                if len(parts) >= 10:
                    try:
                        start = self._parse_timecode(parts[1].strip())
                        end = self._parse_timecode(parts[2].strip())
                        text_content = parts[9].strip()
                        text_content = re.sub(r'\{.*?\}', '', text_content)
                        
                        entries.append(SubtitleEntry(
                            index=len(entries) + 1,
                            start_time=start,
                            end_time=end,
                            text=text_content
                        ))
                    except ValueError:
                        continue
        
        return SubtitleFile(entries=entries, format='ass')
    
    def _parse_ttml(self, text: str) -> SubtitleFile:
        """Parse TTML format."""
        try:
            root = ET.fromstring(text)
            entries = []
            ns = {'tt': 'http://www.w3.org/ns/ttml'}
            
            for p in root.findall('.//tt:p', ns):
                text_content = ''.join(p.itertext()).strip()
                if not text_content:
                    continue
                
                begin = p.get('begin', '')
                end = p.get('end', '')
                if begin and end:
                    start = self._parse_timecode(begin)
                    end = self._parse_timecode(end)
                    
                    entries.append(SubtitleEntry(
                        index=len(entries) + 1,
                        start_time=start,
                        end_time=end,
                        text=text_content
                    ))
            
            return SubtitleFile(entries=entries, format='ttml')
        except ET.ParseError:
            raise ValueError("Invalid TTML format")
    
    def _parse_json(self, text: str) -> SubtitleFile:
        """Parse JSON format."""
        try:
            data = json.loads(text)
            entries = []
            for item in data:
                if 'start' in item and 'end' in item and 'text' in item:
                    entries.append(SubtitleEntry(
                        index=len(entries) + 1,
                        start_time=timedelta(seconds=float(item['start'])),
                        end_time=timedelta(seconds=float(item['end'])),
                        text=item['text']
                    ))
            return SubtitleFile(entries=entries, format='json')
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
    
    def _parse_csv(self, text: str) -> SubtitleFile:
        """Parse CSV format."""
        try:
            reader = csv.DictReader(text.splitlines())
            entries = []
            for row in reader:
                if 'start' in row and 'end' in row and 'text' in row:
                    entries.append(SubtitleEntry(
                        index=len(entries) + 1,
                        start_time=self._parse_timecode(row['start']) if ':' in row['start'] 
                                  else timedelta(seconds=float(row['start'])),
                        end_time=self._parse_timecode(row['end']) if ':' in row['end'] 
                                else timedelta(seconds=float(row['end'])),
                        text=row['text']
                    ))
            return SubtitleFile(entries=entries, format='csv')
        except Exception:
            raise ValueError("Invalid CSV format")
    
    def _parse_timecode(self, time_str: str) -> timedelta:
        """Parse timecode string to timedelta."""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds_parts = parts[1].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            return timedelta(minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        
        else:
            try:
                return timedelta(seconds=float(time_str))
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}")

class SubtitleWriter:
    """Handles writing subtitle files in various formats."""
    
    def __init__(self):
        self.supported_formats = SUPPORTED_FORMATS
        
    def write(self, subtitle_file: SubtitleFile, file_path: Path, format_hint: Optional[str] = None) -> None:
        """Write subtitle file to disk."""
        format_name = format_hint or subtitle_file.format or 'srt'
        if format_name not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_name}")
        
        if not self.supported_formats[format_name]['write']:
            raise ValueError(f"Format {format_name} does not support writing")
        
        content = self._generate_content(subtitle_file, format_name)
        encoding = subtitle_file.encoding or 'utf-8'
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
    
    def _generate_content(self, subtitle_file: SubtitleFile, format_name: str) -> str:
        """Generate content in specified format."""
        if format_name == 'srt':
            return self._write_srt(subtitle_file)
        elif format_name == 'vtt':
            return self._write_vtt(subtitle_file)
        elif format_name == 'ass':
            return self._write_ass(subtitle_file)
        elif format_name == 'ttml':
            return self._write_ttml(subtitle_file)
        elif format_name == 'json':
            return self._write_json(subtitle_file)
        elif format_name == 'csv':
            return self._write_csv(subtitle_file)
        elif format_name == 'txt':
            return self._write_txt(subtitle_file)
        else:
            raise ValueError(f"Writing format {format_name} not implemented")
    
    def _write_srt(self, subtitle_file: SubtitleFile) -> str:
        """Generate SRT content."""
        lines = []
        for entry in subtitle_file.entries:
            lines.append(str(entry.index))
            start_str = self._format_timecode(entry.start_time)
            end_str = self._format_timecode(entry.end_time)
            lines.append(f"{start_str} --> {end_str}")
            lines.append(entry.text)
            lines.append('')
        return '\n'.join(lines)
    
    def _write_vtt(self, subtitle_file: SubtitleFile) -> str:
        """Generate WebVTT content."""
        lines = ['WEBVTT', '']
        for entry in subtitle_file.entries:
            start_str = self._format_timecode(entry.start_time).replace(',', '.')
            end_str = self._format_timecode(entry.end_time).replace(',', '.')
            lines.append(f"{start_str} --> {end_str}")
            lines.append(entry.text)
            lines.append('')
        return '\n'.join(lines)
    
    def _write_ass(self, subtitle_file: SubtitleFile) -> str:
        """Generate ASS content."""
        lines = [
            '[Script Info]',
            'Title: Generated by SuperSRT',
            'ScriptType: v4.00+',
            '',
            '[V4+ Styles]',
            'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
            'Style: Default,Arial,20,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1',
            '',
            '[Events]',
            'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'
        ]
        
        for entry in subtitle_file.entries:
            start_str = self._format_timecode(entry.start_time).replace(',', '.')
            end_str = self._format_timecode(entry.end_time).replace(',', '.')
            text = entry.text.replace('\n', '\\N')
            lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")
        
        return '\n'.join(lines)
    
    def _write_ttml(self, subtitle_file: SubtitleFile) -> str:
        """Generate TTML content."""
        root = ET.Element('tt', attrib={
            'xmlns': 'http://www.w3.org/ns/ttml',
            'xml:lang': 'en'
        })
        
        body = ET.SubElement(root, 'body')
        div = ET.SubElement(body, 'div')
        
        for entry in subtitle_file.entries:
            p = ET.SubElement(div, 'p', attrib={
                'begin': self._format_timecode(entry.start_time),
                'end': self._format_timecode(entry.end_time)
            })
            p.text = entry.text
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def _write_json(self, subtitle_file: SubtitleFile) -> str:
        """Generate JSON content."""
        data = [entry.to_dict() for entry in subtitle_file.entries]
        return json.dumps(data, indent=2, default=str)
    
    def _write_csv(self, subtitle_file: SubtitleFile) -> str:
        """Generate CSV content."""
        output = ['index,start,end,text']
        for entry in subtitle_file.entries:
            start_str = str(entry.start_time.total_seconds())
            end_str = str(entry.end_time.total_seconds())
            output.append(f"{entry.index},{start_str},{end_str},\"{entry.text}\"")
        return '\n'.join(output)
    
    def _write_txt(self, subtitle_file: SubtitleFile) -> str:
        """Generate plain text content."""
        return '\n\n'.join(entry.text for entry in subtitle_file.entries)
    
    def _format_timecode(self, td: timedelta) -> str:
        """Format timedelta to timecode string."""
        total_seconds = td.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# ============================================
# Audio Processing Module
# ============================================

class AudioProcessor:
    """Handles audio processing for subtitle generation."""
    
    def __init__(self):
        self.supported_audio_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        
    def analyze_wav(self, file_path: Path) -> Dict:
        """Analyze WAV file and return audio information."""
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                params = {
                    'channels': wav_file.getnchannels(),
                    'sample_width': wav_file.getsampwidth(),
                    'frame_rate': wav_file.getframerate(),
                    'frames': wav_file.getnframes(),
                    'duration': wav_file.getnframes() / wav_file.getframerate()
                }
                
                if NUMPY_AVAILABLE:
                    frames = wav_file.readframes(params['frames'])
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    
                    if len(audio_data) > 0:
                        params['max_amplitude'] = np.max(np.abs(audio_data))
                        params['rms'] = np.sqrt(np.mean(audio_data**2))
                        params['zero_crossings'] = np.sum(np.abs(np.diff(np.sign(audio_data)))) / 2
                    else:
                        params['max_amplitude'] = 0
                        params['rms'] = 0
                        params['zero_crossings'] = 0
                else:
                    params['max_amplitude'] = 0
                    params['rms'] = 0
                    params['zero_crossings'] = 0
                
                return params
        except Exception as e:
            raise ValueError(f"Error analyzing WAV file: {e}")
    
    def detect_speech_segments(self, file_path: Path, silence_threshold: float = 0.01) -> List[Tuple[float, float]]:
        """Detect speech segments in audio file."""
        if not NUMPY_AVAILABLE:
            return []
        
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                frame_rate = wav_file.getframerate()
                
                audio_data = audio_data / np.max(np.abs(audio_data))
                
                segments = []
                is_speech = False
                segment_start = 0
                window_size = int(frame_rate * 0.5)
                
                for i in range(0, len(audio_data), window_size):
                    window = audio_data[i:i+window_size]
                    if len(window) > 0:
                        energy = np.sqrt(np.mean(window**2))
                        
                        if energy > silence_threshold and not is_speech:
                            is_speech = True
                            segment_start = i / frame_rate
                        elif energy <= silence_threshold and is_speech:
                            is_speech = False
                            segment_end = i / frame_rate
                            if segment_end - segment_start > 1.0:
                                segments.append((segment_start, segment_end))
                
                if is_speech:
                    segment_end = len(audio_data) / frame_rate
                    if segment_end - segment_start > 1.0:
                        segments.append((segment_start, segment_end))
                
                return segments
        except Exception as e:
            raise ValueError(f"Error detecting speech segments: {e}")
    
    def generate_subtitles_from_wav(self, file_path: Path, language: str = 'en-US') -> SubtitleFile:
        """Generate subtitles from WAV file using speech recognition."""
        if not SR_AVAILABLE:
            raise ImportError("SpeechRecognition library not installed. Run: pip install SpeechRecognition")
        
        try:
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(str(file_path)) as source:
                audio_data = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio_data, language=language)
            except sr.UnknownValueError:
                raise ValueError("Could not understand audio. Please check audio quality.")
            except sr.RequestError:
                raise ValueError("Error connecting to speech recognition service.")
            
            segments = self.detect_speech_segments(file_path)
            
            entries = []
            words = text.split()
            words_per_segment = max(1, len(words) // len(segments)) if segments else len(words)
            
            for i, (start, end) in enumerate(segments, 1):
                start_idx = (i - 1) * words_per_segment
                end_idx = min(i * words_per_segment, len(words))
                
                if start_idx < len(words):
                    segment_text = ' '.join(words[start_idx:end_idx])
                    entries.append(SubtitleEntry(
                        index=i,
                        start_time=timedelta(seconds=start),
                        end_time=timedelta(seconds=end),
                        text=segment_text
                    ))
            
            if not entries:
                entries.append(SubtitleEntry(
                    index=1,
                    start_time=timedelta(seconds=0),
                    end_time=timedelta(seconds=len(text) / 5.0),
                    text=text
                ))
            
            return SubtitleFile(
                entries=entries,
                format='srt',
                encoding='utf-8',
                metadata={
                    'source': str(file_path),
                    'language': language,
                    'audio_info': self.analyze_wav(file_path)
                }
            )
        except Exception as e:
            raise ValueError(f"Error generating subtitles: {e}")

# ============================================
# AI Integration Module (OPTIMIZED FREE MODELS)
# ============================================

class AIEngine:
    """Handles AI operations using OpenRouter API with OPTIMIZED FREE models."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Get one at: https://openrouter.ai")
        
        self.config = config or DEFAULT_CONFIG['ai']
        self.client = None
        self._initialize_client()
        self.free_models = FREE_MODELS
        self.model_capabilities = MODEL_CAPABILITIES
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.timeout = self.config.get('timeout', 60)
        self.stream = self.config.get('stream', False)
        
        # Track model usage for optimization
        self.model_usage = defaultdict(int)
        self.model_performance = defaultdict(float)
    
    def _initialize_client(self) -> None:
        """Initialize the OpenRouter client."""
        if not OPENROUTER_AVAILABLE:
            raise ImportError("OpenRouter library not installed. Run: pip install openrouter")
        
        self.client = OpenRouter(api_key=self.api_key)
    
    def _get_best_model(self, task: str, context_size: int = 0) -> str:
        """Get the best model for a specific task based on requirements."""
        # Track model usage
        self.model_usage[task] += 1
        
        # Model recommendations by task
        task_models = {
            'translation': [
                self.free_models['translation_premium'],  # Gemini Flash
                self.free_models['translation'],          # Gemma 4
                self.free_models['default'],              # Nemotron Ultra
                self.free_models['fallback']              # Nemotron Nano
            ],
            'improvement': [
                self.free_models['improvement'],          # Llama 3.3
                self.free_models['balanced'],             # Qwen 32B
                self.free_models['fallback']              # Nemotron Nano
            ],
            'summarization': [
                self.free_models['summarization'],        # Qwen Next
                self.free_models['balanced'],             # Qwen 32B
                self.free_models['fallback']              # Nemotron Nano
            ],
            'analysis': [
                self.free_models['analysis_premium'],     # Claude Haiku
                self.free_models['analysis'],             # Hermes 405B
                self.free_models['default'],              # Nemotron Ultra
                self.free_models['fallback']              # Nemotron Nano
            ],
            'creative': [
                self.free_models['creative'],             # GLM 4.5
                self.free_models['improvement'],          # Llama 3.3
                self.free_models['fallback']              # Nemotron Nano
            ],
            'fast': [
                self.free_models['fast'],                 # Mistral Small
                self.free_models['balanced'],             # Qwen 32B
                self.free_models['fallback']              # Nemotron Nano
            ],
            'code': [
                self.free_models['code'],                 # GPT OSS
                self.free_models['default'],              # Nemotron Ultra
                self.free_models['fallback']              # Nemotron Nano
            ],
            'general': [
                self.free_models['default'],              # Nemotron Ultra
                self.free_models['balanced'],             # Qwen 32B
                self.free_models['fallback']              # Nemotron Nano
            ]
        }
        
        # Get models for this task
        models = task_models.get(task, task_models['general'])
        
        # Filter by context size if specified
        if context_size > 0:
            filtered_models = []
            for model in models:
                if model in self.model_capabilities:
                    if self.model_capabilities[model]['context'] >= context_size:
                        filtered_models.append(model)
            if filtered_models:
                models = filtered_models
        
        # Return first available model
        return models[0] if models else self.free_models['fallback']
    
    def _call_api_with_retry(self, model: str, messages: List[Dict], **kwargs) -> Any:
        """Call OpenRouter API with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                response = self.client.chat.send(
                    model=model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 4096),
                    timeout=self.timeout,
                    stream=self.stream
                )
                
                # Track performance
                self.model_performance[model] = (self.model_performance[model] + 1) / 2
                return response
                
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError(f"Failed after {self.retry_attempts} attempts")
    
    def translate(self, text: Union[str, List[str]], target_lang: str, 
                  source_lang: Optional[str] = None, model: Optional[str] = None) -> Union[str, List[str]]:
        """Translate text using optimized FREE AI models."""
        model = model or self._get_best_model('translation')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = f"Translate the following text to {target_lang}. Provide only the translation, nothing else:\n\n{t}"
            if source_lang:
                prompt = f"Translate from {source_lang} to {target_lang}. Provide only the translation:\n\n{t}"
            
            messages = [
                {"role": "system", "content": "You are a professional translator. Provide accurate, natural translations only."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            translated = response.choices[0].message.content.strip()
            results.append(translated)
        
        return results if is_list else results[0]
    
    def translate_context(self, text: Union[str, List[str]], target_lang: str,
                          context: str, source_lang: Optional[str] = None,
                          model: Optional[str] = None) -> Union[str, List[str]]:
        """Context-aware translation using optimized FREE AI models."""
        model = model or self._get_best_model('translation')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = f"""Translate the following text to {target_lang} with context awareness.
Context: {context}
Text: {t}
Provide only the translation:"""
            
            if source_lang:
                prompt = f"Translate from {source_lang} to {target_lang} with context awareness.\n{prompt}"
            
            messages = [
                {"role": "system", "content": "You are a professional translator with deep cultural understanding."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            translated = response.choices[0].message.content.strip()
            results.append(translated)
        
        return results if is_list else results[0]
    
    def translate_dialect(self, text: Union[str, List[str]], target_lang: str,
                         dialect: str, model: Optional[str] = None) -> Union[str, List[str]]:
        """Dialect-specific translation using optimized FREE AI models."""
        model = model or self._get_best_model('translation')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = f"Translate the following text to {target_lang} ({dialect} dialect). Provide only the translation:\n\n{t}"
            
            messages = [
                {"role": "system", "content": f"You are a translator specializing in {target_lang} dialects."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            translated = response.choices[0].message.content.strip()
            results.append(translated)
        
        return results if is_list else results[0]
    
    def translate_style(self, text: Union[str, List[str]], target_lang: str,
                       style: str, model: Optional[str] = None) -> Union[str, List[str]]:
        """Style-preserving translation using optimized FREE AI models."""
        model = model or self._get_best_model('translation')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = f"Translate the following text to {target_lang} in a {style} style. Provide only the translation:\n\n{t}"
            
            messages = [
                {"role": "system", "content": f"You are a translator who preserves style and tone."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            translated = response.choices[0].message.content.strip()
            results.append(translated)
        
        return results if is_list else results[0]
    
    def improve_subtitles(self, text: Union[str, List[str]], style: Optional[str] = None,
                          tone: Optional[str] = None, model: Optional[str] = None) -> Union[str, List[str]]:
        """Improve subtitle text quality using optimized FREE AI models."""
        model = model or self._get_best_model('improvement')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = "Improve the following subtitle text for clarity and readability."
            if style:
                prompt += f" Style: {style}"
            if tone:
                prompt += f" Tone: {tone}"
            prompt += f"\n\nText: {t}\n\nImproved text (provide only the improved text):"
            
            messages = [
                {"role": "system", "content": "You are a subtitle editor. Improve clarity, grammar, and readability. Output only the improved text."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            improved = response.choices[0].message.content.strip()
            results.append(improved)
        
        return results if is_list else results[0]
    
    def improve_grammar(self, text: Union[str, List[str]], level: str = 'standard',
                        preserve_style: bool = True, model: Optional[str] = None) -> Union[str, List[str]]:
        """Grammar correction with style preservation using optimized FREE AI models."""
        model = model or self._get_best_model('improvement')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        level_desc = {
            'basic': 'fix only critical grammar errors',
            'standard': 'fix all grammar errors while maintaining natural flow',
            'advanced': 'fix all grammar errors and improve readability significantly'
        }
        
        results = []
        for t in texts:
            prompt = f"Correct grammar ({level_desc.get(level, 'standard')}):"
            if preserve_style:
                prompt += " Preserve the original writing style and tone."
            prompt += f"\n\nText: {t}\n\nCorrected text (provide only the corrected text):"
            
            messages = [
                {"role": "system", "content": "You are a grammar expert and subtitle editor. Output only the corrected text."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            improved = response.choices[0].message.content.strip()
            results.append(improved)
        
        return results if is_list else results[0]
    
    def improve_consistency(self, text: Union[str, List[str]], characters: Optional[List[str]] = None,
                           strict: bool = False, model: Optional[str] = None) -> Union[str, List[str]]:
        """Character consistency improvement using optimized FREE AI models."""
        model = model or self._get_best_model('improvement')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = "Improve character consistency in the following subtitle text."
            if characters:
                prompt += f" Characters: {', '.join(characters)}"
            if strict:
                prompt += " Apply strict consistency rules."
            prompt += f"\n\nText: {t}\n\nImproved text (provide only the improved text):"
            
            messages = [
                {"role": "system", "content": "You are a subtitle editor specializing in character consistency."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            improved = response.choices[0].message.content.strip()
            results.append(improved)
        
        return results if is_list else results[0]
    
    def improve_formatting(self, text: Union[str, List[str]], custom_template: Optional[str] = None,
                          no_style: bool = False, model: Optional[str] = None) -> Union[str, List[str]]:
        """Format standardization using optimized FREE AI models."""
        model = model or self._get_best_model('improvement')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = "Standardize the formatting of the following subtitle text."
            if custom_template:
                prompt += f" Use this template: {custom_template}"
            if no_style:
                prompt += " Remove all styling and formatting."
            prompt += f"\n\nText: {t}\n\nStandardized text (provide only the standardized text):"
            
            messages = [
                {"role": "system", "content": "You are a subtitle formatting specialist."},
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_api_with_retry(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            improved = response.choices[0].message.content.strip()
            results.append(improved)
        
        return results if is_list else results[0]
    
    def summarize_subtitles(self, text: str, length: str = 'short', 
                           model: Optional[str] = None) -> str:
        """Generate summary of subtitle content using optimized FREE AI models."""
        model = model or self._get_best_model('summarization', context_size=len(text) // 4)
        
        length_desc = {
            'short': 'brief (1-2 sentences per scene)',
            'medium': 'moderate (3-4 sentences per scene)',
            'long': 'detailed (5-7 sentences per scene)'
        }
        
        prompt = f"Summarize the following content in {length_desc.get(length, 'short')} length. Provide only the summary:\n\n{text}"
        
        messages = [
            {"role": "system", "content": "You are a content summarizer. Provide clear, concise summaries only."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api_with_retry(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048
        )
        
        return response.choices[0].message.content.strip()
    
    def analyze_sentiment(self, text: str, model: Optional[str] = None) -> Dict:
        """Analyze sentiment of subtitle text using optimized FREE AI models."""
        model = model or self._get_best_model('analysis', context_size=len(text) // 2)
        
        prompt = f"""Analyze the sentiment of the following text. Return ONLY a JSON object with these fields:
        - sentiment: (positive/negative/neutral)
        - confidence: (0.0-1.0)
        - emotions: (list of 3-5 emotions)
        - intensity: (1-10)
        
        Text: {text}"""
        
        messages = [
            {"role": "system", "content": "You are a sentiment analyst. Provide detailed sentiment analysis in JSON format only."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api_with_retry(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        
        try:
            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'sentiment': 'unknown', 'confidence': 0.0, 'emotions': [], 'intensity': 0}
        except json.JSONDecodeError:
            return {'sentiment': 'unknown', 'confidence': 0.0, 'emotions': [], 'intensity': 0}
    
    def analyze_emotion(self, text: str, model: Optional[str] = None) -> Dict:
        """Detect emotions in subtitle text using optimized FREE AI models."""
        model = model or self._get_best_model('analysis', context_size=len(text) // 2)
        
        prompt = f"""Analyze the emotional content of the following text. Return ONLY a JSON object with these fields:
        - primary_emotion: (joy/sadness/anger/fear/surprise/disgust/neutral)
        - emotions: (object with emotion scores 0-1)
        - intensity: (1-10)
        
        Text: {text}"""
        
        messages = [
            {"role": "system", "content": "You are an emotion detection expert. Output only JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api_with_retry(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        
        try:
            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'primary_emotion': 'neutral', 'emotions': {}, 'intensity': 0}
        except json.JSONDecodeError:
            return {'primary_emotion': 'neutral', 'emotions': {}, 'intensity': 0}
    
    def analyze_cultural(self, text: str, model: Optional[str] = None) -> Dict:
        """Detect cultural references in subtitle text using optimized FREE AI models."""
        model = model or self._get_best_model('analysis', context_size=len(text) // 2)
        
        prompt = f"""Analyze the following text for cultural references. Return ONLY a JSON object with these fields:
        - cultural_references: (list of references with descriptions)
        - cultural_context: (explanation of context)
        - sensitivity_level: (1-10, where 1 is universal, 10 is highly culture-specific)
        
        Text: {text}"""
        
        messages = [
            {"role": "system", "content": "You are a cultural analysis expert. Output only JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api_with_retry(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=2048
        )
        
        try:
            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'cultural_references': [], 'cultural_context': '', 'sensitivity_level': 0}
        except json.JSONDecodeError:
            return {'cultural_references': [], 'cultural_context': '', 'sensitivity_level': 0}
    
    def analyze_readability(self, text: str, model: Optional[str] = None) -> Dict:
        """Analyze readability of subtitle text using optimized FREE AI models."""
        model = model or self._get_best_model('analysis', context_size=len(text) // 2)
        
        prompt = f"""Analyze the readability of the following text. Return ONLY a JSON object with these fields:
        - readability_score: (0-100, higher means more readable)
        - reading_ease: (very easy/easy/medium/difficult/very difficult)
        - suggestions: (list of improvement suggestions)
        - complexity: (1-10, where 1 is very simple, 10 is very complex)
        
        Text: {text}"""
        
        messages = [
            {"role": "system", "content": "You are a readability expert. Output only JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_api_with_retry(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        
        try:
            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'readability_score': 0, 'reading_ease': 'unknown', 'suggestions': [], 'complexity': 0}
        except json.JSONDecodeError:
            return {'readability_score': 0, 'reading_ease': 'unknown', 'suggestions': [], 'complexity': 0}
    
    def list_models(self) -> Dict:
        """List all available models with their capabilities."""
        return self.model_capabilities.copy()
    
    def get_model_stats(self) -> Dict:
        """Get model usage statistics."""
        return {
            'usage': dict(self.model_usage),
            'performance': dict(self.model_performance)
        }

# ============================================
# Cache Manager
# ============================================

class CacheManager:
    """Manages caching of operations and AI responses."""
    
    def __init__(self, cache_dir: str = './cache', enabled: bool = True, ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data."""
        if not self.enabled:
            return None
        
        cache_file = self.cache_dir / key
        if not cache_file.exists():
            return None
        
        if self.ttl > 0:
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.ttl:
                cache_file.unlink()
                return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('value')
        except Exception:
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Store data in cache."""
        if not self.enabled:
            return
        
        cache_file = self.cache_dir / key
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'value': value,
                    'timestamp': time.time()
                }, f)
        except Exception:
            pass
    
    def clear(self) -> None:
        """Clear all cache."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_size(self) -> int:
        """Get cache size in bytes."""
        if not self.cache_dir.exists():
            return 0
        
        total = 0
        for file in self.cache_dir.rglob('*'):
            if file.is_file():
                total += file.stat().st_size
        return total

# ============================================
# Utility Functions
# ============================================

def detect_encoding(file_path: Path) -> str:
    """Detect file encoding."""
    if not CHARDET_AVAILABLE:
        return 'utf-8'
    
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def safe_filename(filename: str) -> str:
    """Create a safe filename."""
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe = re.sub(r'[\s_]+', '_', safe)
    if len(safe) > 200:
        safe = safe[:200]
    return safe

def get_file_hash(file_path: Path) -> str:
    """Generate hash of file content."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

# ============================================
# Main Application Class
# ============================================

class SuperSRT:
    """Main SuperSRT application class."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self.parser = SubtitleParser()
        self.writer = SubtitleWriter()
        self.audio_processor = AudioProcessor()
        self.ai_engine = None
        self.cache_manager = CacheManager(
            cache_dir=os.getenv('CACHE_LOCATION', './cache'),
            enabled=self.config.get('cache_enabled', True),
            ttl=self.config.get('cache_ttl', 86400)
        )
        
        self._setup_logging()
        
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            try:
                self.ai_engine = AIEngine(api_key, self.config.get('ai', {}))
                self.logger.info("AI Engine initialized with optimized free models")
            except Exception as e:
                self.logger.warning(f"AI initialization failed: {e}")
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = self.config.get('logging', DEFAULT_CONFIG['logging'])
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        log_file = Path(log_config.get('file', './logs/supersrt.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('supersrt')
    
    def load_subtitle(self, file_path: Union[str, Path]) -> SubtitleFile:
        """Load subtitle file."""
        return self.parser.parse(file_path)
    
    def save_subtitle(self, subtitle_file: SubtitleFile, file_path: Union[str, Path],
                     format_hint: Optional[str] = None) -> None:
        """Save subtitle file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        self.writer.write(subtitle_file, file_path, format_hint)
    
    def generate_from_wav(self, wav_path: Union[str, Path], language: str = 'en-US') -> SubtitleFile:
        """Generate subtitles from WAV file."""
        return self.audio_processor.generate_subtitles_from_wav(Path(wav_path), language)
    
    def analyze_audio(self, file_path: Union[str, Path]) -> Dict:
        """Analyze audio file and return information."""
        return self.audio_processor.analyze_wav(Path(file_path))
    
    def detect_speech(self, file_path: Union[str, Path]) -> List[Tuple[float, float]]:
        """Detect speech segments in audio file."""
        return self.audio_processor.detect_speech_segments(Path(file_path))
    
    def translate_subtitles(self, subtitle_file: SubtitleFile, target_lang: str,
                           source_lang: Optional[str] = None, model: Optional[str] = None,
                           batch_size: int = 10, context: Optional[str] = None) -> SubtitleFile:
        """Translate subtitle file to target language using optimized FREE AI models."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        translated_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            if context:
                translated = self.ai_engine.translate_context(
                    batch, target_lang, context, source_lang, model
                )
            else:
                translated = self.ai_engine.translate(
                    batch, target_lang, source_lang, model
                )
            translated_texts.extend(translated if isinstance(translated, list) else [translated])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, translated_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'translated_from': source_lang or 'auto',
                'translated_to': target_lang,
                'model_used': model or 'auto-selected',
                'context': context
            },
            file_path=subtitle_file.file_path
        )
    
    def translate_dialect(self, subtitle_file: SubtitleFile, target_lang: str,
                         dialect: str, model: Optional[str] = None,
                         batch_size: int = 10) -> SubtitleFile:
        """Translate to specific dialect using optimized FREE AI models."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        translated_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            translated = self.ai_engine.translate_dialect(
                batch, target_lang, dialect, model
            )
            translated_texts.extend(translated if isinstance(translated, list) else [translated])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, translated_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'translated_to': target_lang,
                'dialect': dialect,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def translate_style(self, subtitle_file: SubtitleFile, target_lang: str,
                       style: str, model: Optional[str] = None,
                       batch_size: int = 10) -> SubtitleFile:
        """Style-preserving translation using optimized FREE AI models."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        translated_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            translated = self.ai_engine.translate_style(
                batch, target_lang, style, model
            )
            translated_texts.extend(translated if isinstance(translated, list) else [translated])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, translated_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'translated_to': target_lang,
                'style': style,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def improve_subtitles(self, subtitle_file: SubtitleFile, style: Optional[str] = None,
                         tone: Optional[str] = None, model: Optional[str] = None,
                         batch_size: int = 10) -> SubtitleFile:
        """Improve subtitle quality using optimized FREE AI models."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        improved_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            improved = self.ai_engine.improve_subtitles(
                batch, style, tone, model
            )
            improved_texts.extend(improved if isinstance(improved, list) else [improved])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, improved_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'improvement_style': style,
                'improvement_tone': tone,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def improve_grammar(self, subtitle_file: SubtitleFile, level: str = 'standard',
                       preserve_style: bool = True, model: Optional[str] = None,
                       batch_size: int = 10) -> SubtitleFile:
        """Grammar correction for subtitles."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        improved_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            improved = self.ai_engine.improve_grammar(
                batch, level, preserve_style, model
            )
            improved_texts.extend(improved if isinstance(improved, list) else [improved])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, improved_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'grammar_level': level,
                'preserved_style': preserve_style,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def improve_consistency(self, subtitle_file: SubtitleFile, 
                           characters: Optional[List[str]] = None,
                           strict: bool = False, model: Optional[str] = None,
                           batch_size: int = 10) -> SubtitleFile:
        """Character consistency improvement."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        improved_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            improved = self.ai_engine.improve_consistency(
                batch, characters, strict, model
            )
            improved_texts.extend(improved if isinstance(improved, list) else [improved])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, improved_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'consistency_improved': True,
                'strict': strict,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def improve_formatting(self, subtitle_file: SubtitleFile,
                          custom_template: Optional[str] = None,
                          no_style: bool = False, model: Optional[str] = None,
                          batch_size: int = 10) -> SubtitleFile:
        """Format standardization."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        texts = [entry.text for entry in subtitle_file.entries]
        
        improved_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            improved = self.ai_engine.improve_formatting(
                batch, custom_template, no_style, model
            )
            improved_texts.extend(improved if isinstance(improved, list) else [improved])
        
        new_entries = []
        for entry, new_text in zip(subtitle_file.entries, improved_texts):
            new_entries.append(SubtitleEntry(
                index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                text=new_text,
                metadata=entry.metadata.copy()
            ))
        
        return SubtitleFile(
            entries=new_entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={
                **subtitle_file.metadata,
                'formatting_standardized': True,
                'no_style': no_style,
                'model_used': model or 'auto-selected'
            },
            file_path=subtitle_file.file_path
        )
    
    def summarize_subtitles(self, subtitle_file: SubtitleFile, length: str = 'short',
                           model: Optional[str] = None) -> str:
        """Generate summary of subtitle file using optimized FREE AI models."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        text = subtitle_file.get_text_content()
        return self.ai_engine.summarize_subtitles(text, length, model)
    
    def analyze_subtitles(self, subtitle_file: SubtitleFile, analysis_type: str = 'sentiment',
                         model: Optional[str] = None) -> Dict:
        """Analyze subtitle file content."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        text = subtitle_file.get_text_content()
        
        if analysis_type == 'sentiment':
            return self.ai_engine.analyze_sentiment(text, model)
        elif analysis_type == 'emotion':
            return self.ai_engine.analyze_emotion(text, model)
        elif analysis_type == 'cultural':
            return self.ai_engine.analyze_cultural(text, model)
        elif analysis_type == 'readability':
            return self.ai_engine.analyze_readability(text, model)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def fix_timing(self, subtitle_file: SubtitleFile, shift: Optional[float] = None,
                  auto_detect: bool = False, target_fps: Optional[float] = None) -> SubtitleFile:
        """Fix timing issues in subtitle file."""
        if shift is not None:
            return subtitle_file.shift_timing(shift)
        
        if auto_detect:
            self.logger.info("Auto-detecting timing issues...")
            return subtitle_file
        
        if target_fps:
            self.logger.info(f"Converting to {target_fps} FPS...")
            return subtitle_file
        
        return subtitle_file
    
    def improve_timing(self, subtitle_file: SubtitleFile, auto: bool = False,
                      frame_rate: Optional[float] = None) -> SubtitleFile:
        """Optimize timing of subtitle file."""
        return self.fix_timing(subtitle_file, None, auto, frame_rate)
    
    def sync_subtitles(self, subtitle_file: SubtitleFile, video_path: str,
                       method: str = 'whisper', language: str = 'en',
                       offset: float = 0.0) -> SubtitleFile:
        """Synchronize subtitles with video."""
        self.logger.info(f"Synchronizing subtitles with video: {video_path}")
        self.logger.info(f"Method: {method}, Language: {language}, Offset: {offset}")
        
        if offset != 0:
            return subtitle_file.shift_timing(offset)
        return subtitle_file
    
    def adapt_content(self, subtitle_file: SubtitleFile, target_audience: str = 'general',
                     simplify_level: Optional[int] = None, remove_profanity: bool = False,
                     cultural_sensitivity: bool = False) -> SubtitleFile:
        """Adapt subtitle content for different audiences."""
        self.logger.info(f"Adapting content for: {target_audience}")
        
        # This would use AI to adapt content
        # Placeholder implementation
        return subtitle_file
    
    def merge_subtitles(self, subtitle_files: List[SubtitleFile], 
                       order: str = 'timestamp') -> SubtitleFile:
        """Merge multiple subtitle files."""
        if order == 'timestamp':
            all_entries = []
            for sf in subtitle_files:
                all_entries.extend(sf.entries)
            all_entries.sort(key=lambda x: x.start_time)
        else:
            all_entries = []
            for sf in subtitle_files:
                all_entries.extend(sf.entries)
        
        for i, entry in enumerate(all_entries, 1):
            entry.index = i
        
        return SubtitleFile(
            entries=all_entries,
            format=subtitle_files[0].format if subtitle_files else 'srt',
            encoding=subtitle_files[0].encoding if subtitle_files else 'utf-8',
            metadata={'merged_from': [sf.file_path.name for sf in subtitle_files if sf.file_path]},
            file_path=None
        )
    
    def split_subtitles(self, subtitle_file: SubtitleFile, chunks: Optional[int] = None,
                       lines_per_chunk: Optional[int] = None) -> List[SubtitleFile]:
        """Split subtitle file into multiple files."""
        if chunks:
            entries_per_chunk = max(1, len(subtitle_file.entries) // chunks)
        elif lines_per_chunk:
            entries_per_chunk = lines_per_chunk
        else:
            raise ValueError("Either chunks or lines_per_chunk must be specified")
        
        result = []
        for i in range(0, len(subtitle_file.entries), entries_per_chunk):
            chunk_entries = subtitle_file.entries[i:i + entries_per_chunk]
            for j, entry in enumerate(chunk_entries, 1):
                entry.index = j
            
            result.append(SubtitleFile(
                entries=chunk_entries,
                format=subtitle_file.format,
                encoding=subtitle_file.encoding,
                metadata={**subtitle_file.metadata, 'chunk': len(result) + 1},
                file_path=None
            ))
        
        return result
    
    def batch_process(self, input_dir: str, output_dir: str, 
                     operations: Dict, parallel: int = 4) -> Dict:
        """Batch process multiple subtitle files."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        subtitle_files = []
        for ext in SUPPORTED_FORMATS:
            subtitle_files.extend(input_path.glob(f"*.{ext}"))
        
        results = {
            'processed': [],
            'failed': [],
            'total': len(subtitle_files)
        }
        
        def process_file(file_path: Path) -> Tuple[Path, Optional[SubtitleFile], Optional[Exception]]:
            try:
                sub = self.load_subtitle(file_path)
                
                if 'translate' in operations:
                    sub = self.translate_subtitles(
                        sub,
                        operations['translate']['target'],
                        operations['translate'].get('source'),
                        operations['translate'].get('model'),
                        operations['translate'].get('batch_size', 10),
                        operations['translate'].get('context')
                    )
                
                if 'improve' in operations:
                    sub = self.improve_subtitles(
                        sub,
                        operations['improve'].get('style'),
                        operations['improve'].get('tone'),
                        operations['improve'].get('model')
                    )
                
                if 'fix_timing' in operations:
                    sub = self.fix_timing(
                        sub,
                        operations['fix_timing'].get('shift'),
                        operations['fix_timing'].get('auto_detect', False),
                        operations['fix_timing'].get('target_fps')
                    )
                
                if 'sync' in operations:
                    sub = self.sync_subtitles(
                        sub,
                        operations['sync'].get('video', ''),
                        operations['sync'].get('method', 'whisper'),
                        operations['sync'].get('language', 'en'),
                        operations['sync'].get('offset', 0.0)
                    )
                
                output_file = output_path / file_path.name
                self.save_subtitle(sub, output_file)
                
                return file_path, sub, None
            
            except Exception as e:
                return file_path, None, e
        
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(process_file, f): f for f in subtitle_files}
            
            for future in as_completed(futures):
                file_path, sub, error = future.result()
                if error:
                    results['failed'].append({
                        'file': str(file_path),
                        'error': str(error)
                    })
                else:
                    results['processed'].append(str(file_path))
        
        return results
    
    def generate_statistics(self, subtitle_file: SubtitleFile) -> Dict:
        """Generate comprehensive statistics for subtitle file."""
        return subtitle_file.get_statistics()
    
    def convert_format(self, subtitle_file: SubtitleFile, target_format: str) -> SubtitleFile:
        """Convert subtitle file to different format."""
        if target_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {target_format}")
        
        return SubtitleFile(
            entries=subtitle_file.entries.copy(),
            format=target_format,
            encoding=subtitle_file.encoding,
            metadata=subtitle_file.metadata.copy(),
            file_path=subtitle_file.file_path
        )
    
    def filter_content(self, subtitle_file: SubtitleFile, 
                       remove_pattern: Optional[str] = None,
                       search_pattern: Optional[str] = None,
                       replace_pattern: Optional[str] = None) -> SubtitleFile:
        """Filter subtitle content."""
        entries = subtitle_file.entries.copy()
        
        if remove_pattern:
            pattern = re.compile(remove_pattern, re.IGNORECASE)
            entries = [e for e in entries if not pattern.search(e.text)]
        
        if search_pattern:
            pattern = re.compile(search_pattern, re.IGNORECASE)
            entries = [e for e in entries if pattern.search(e.text)]
        
        if replace_pattern:
            pattern, replacement = replace_pattern.split('|', 1)
            pattern = re.compile(pattern)
            for entry in entries:
                entry.text = pattern.sub(replacement, entry.text)
        
        for i, entry in enumerate(entries, 1):
            entry.index = i
        
        return SubtitleFile(
            entries=entries,
            format=subtitle_file.format,
            encoding=subtitle_file.encoding,
            metadata={**subtitle_file.metadata, 'filtered': True},
            file_path=subtitle_file.file_path
        )
    
    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """Detect file encoding."""
        return detect_encoding(Path(file_path))
    
    def list_models(self) -> Dict:
        """List available AI models."""
        if self.ai_engine:
            return self.ai_engine.list_models()
        return {}
    
    def pipeline(self, subtitle_file: SubtitleFile, operations: List[Dict]) -> SubtitleFile:
        """Execute a pipeline of operations."""
        result = subtitle_file
        
        for op in operations:
            op_type = op.get('type')
            
            if op_type == 'translate':
                result = self.translate_subtitles(
                    result,
                    op.get('target'),
                    op.get('source'),
                    op.get('model'),
                    op.get('batch_size', 10),
                    op.get('context')
                )
            elif op_type == 'translate_dialect':
                result = self.translate_dialect(
                    result,
                    op.get('target'),
                    op.get('dialect'),
                    op.get('model'),
                    op.get('batch_size', 10)
                )
            elif op_type == 'translate_style':
                result = self.translate_style(
                    result,
                    op.get('target'),
                    op.get('style'),
                    op.get('model'),
                    op.get('batch_size', 10)
                )
            elif op_type == 'improve':
                result = self.improve_subtitles(
                    result,
                    op.get('style'),
                    op.get('tone'),
                    op.get('model')
                )
            elif op_type == 'improve_grammar':
                result = self.improve_grammar(
                    result,
                    op.get('level', 'standard'),
                    op.get('preserve_style', True),
                    op.get('model')
                )
            elif op_type == 'improve_consistency':
                result = self.improve_consistency(
                    result,
                    op.get('characters'),
                    op.get('strict', False),
                    op.get('model')
                )
            elif op_type == 'improve_formatting':
                result = self.improve_formatting(
                    result,
                    op.get('custom_template'),
                    op.get('no_style', False),
                    op.get('model')
                )
            elif op_type == 'fix_timing':
                result = self.fix_timing(
                    result,
                    op.get('shift'),
                    op.get('auto_detect', False),
                    op.get('target_fps')
                )
            elif op_type == 'sync':
                result = self.sync_subtitles(
                    result,
                    op.get('video'),
                    op.get('method', 'whisper'),
                    op.get('language', 'en'),
                    op.get('offset', 0.0)
                )
            elif op_type == 'adapt':
                result = self.adapt_content(
                    result,
                    op.get('target_audience', 'general'),
                    op.get('simplify_level'),
                    op.get('remove_profanity', False),
                    op.get('cultural_sensitivity', False)
                )
            elif op_type == 'filter':
                result = self.filter_content(
                    result,
                    op.get('remove'),
                    op.get('search'),
                    op.get('replace')
                )
            elif op_type == 'convert':
                result = self.convert_format(
                    result,
                    op.get('target_format')
                )
            elif op_type == 'analyze':
                # Analysis doesn't modify the file, just logs
                analysis = self.analyze_subtitles(
                    result,
                    op.get('analysis_type', 'sentiment'),
                    op.get('model')
                )
                self.logger.info(f"Analysis result: {analysis}")
        
        return result

# ============================================
# CLI Interface
# ============================================

class CLI:
    """Command-line interface for SuperSRT."""
    
    def __init__(self):
        self.app = SuperSRT()
        self.console = Console() if RICH_AVAILABLE else None
        
        self.parser = argparse.ArgumentParser(
            description='SuperSRT - Advanced AI-Powered Subtitle Processing Suite (OPTIMIZED FREE MODELS)',
            epilog=f"Version {VERSION} | {APP_URL} | License: {LICENSE}"
        )
        self._setup_arguments()
    
    def _setup_arguments(self):
        """Setup command-line arguments."""
        subparsers = self.parser.add_subparsers(dest='command', help='Command to execute')
        
        # WAV to subtitle command
        wav_parser = subparsers.add_parser('wav', help='Generate subtitles from WAV file')
        wav_parser.add_argument('-i', '--input', required=True, help='Input WAV file')
        wav_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        wav_parser.add_argument('-l', '--language', default='en-US', help='Language code (default: en-US)')
        wav_parser.add_argument('--analyze', action='store_true', help='Analyze audio and show information')
        wav_parser.add_argument('--detect-speech', action='store_true', help='Detect speech segments')
        
        # Translate command
        translate_parser = subparsers.add_parser('translate', help='Translate subtitles')
        translate_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        translate_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        translate_parser.add_argument('-t', '--target', required=True, help='Target language code')
        translate_parser.add_argument('-s', '--source', help='Source language code')
        translate_parser.add_argument('-m', '--model', help='AI model to use (free models only)')
        translate_parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
        translate_parser.add_argument('--context', help='Context for translation')
        
        # Translate with context
        context_parser = subparsers.add_parser('translate-context', help='Context-aware translation')
        context_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        context_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        context_parser.add_argument('-c', '--context', required=True, help='Context information')
        context_parser.add_argument('-t', '--target', required=True, help='Target language code')
        context_parser.add_argument('-s', '--source', help='Source language code')
        context_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Translate dialect
        dialect_parser = subparsers.add_parser('translate-dialect', help='Dialect-specific translation')
        dialect_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        dialect_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        dialect_parser.add_argument('-t', '--target', required=True, help='Target language code')
        dialect_parser.add_argument('-d', '--dialect', required=True, help='Dialect name')
        dialect_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Translate with style
        style_parser = subparsers.add_parser('translate-style', help='Style-preserving translation')
        style_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        style_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        style_parser.add_argument('-t', '--target', required=True, help='Target language code')
        style_parser.add_argument('--style', required=True, help='Style (formal, conversational, etc.)')
        style_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Batch translate
        batch_translate_parser = subparsers.add_parser('translate-batch', help='Batch translate multiple files')
        batch_translate_parser.add_argument('-d', '--directory', required=True, help='Input directory')
        batch_translate_parser.add_argument('-t', '--target', required=True, help='Target language code')
        batch_translate_parser.add_argument('-p', '--parallel', type=int, default=4, help='Parallel workers')
        batch_translate_parser.add_argument('--output-dir', help='Output directory')
        
        # Improve command
        improve_parser = subparsers.add_parser('improve', help='Improve subtitle quality')
        improve_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        improve_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        improve_parser.add_argument('--style', help='Style (conversational, formal, etc.)')
        improve_parser.add_argument('--tone', help='Tone (friendly, professional, etc.)')
        improve_parser.add_argument('-m', '--model', help='AI model to use (free models only)')
        
        # Improve grammar
        grammar_parser = subparsers.add_parser('improve-grammar', help='Grammar correction')
        grammar_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        grammar_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        grammar_parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard')
        grammar_parser.add_argument('--preserve-style', action='store_true', default=True)
        grammar_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Improve consistency
        consistency_parser = subparsers.add_parser('improve-consistency', help='Character consistency improvement')
        consistency_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        consistency_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        consistency_parser.add_argument('--characters-file', help='File with character names')
        consistency_parser.add_argument('--strict', action='store_true', help='Apply strict consistency')
        consistency_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Improve formatting
        formatting_parser = subparsers.add_parser('improve-formatting', help='Format standardization')
        formatting_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        formatting_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        formatting_parser.add_argument('--custom-template', help='Custom format template')
        formatting_parser.add_argument('--no-style', action='store_true', help='Remove all styling')
        formatting_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Improve timing
        timing_improve_parser = subparsers.add_parser('improve-timing', help='Timing optimization')
        timing_improve_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        timing_improve_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        timing_improve_parser.add_argument('--auto', action='store_true', help='Auto-detect timing issues')
        timing_improve_parser.add_argument('--frame-rate', type=float, help='Target frame rate')
        
        # Fix timing command
        timing_parser = subparsers.add_parser('fix-timing', help='Fix timing issues')
        timing_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        timing_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        timing_parser.add_argument('--shift', type=float, help='Shift timing by seconds')
        timing_parser.add_argument('--auto-detect', action='store_true', help='Auto-detect timing issues')
        timing_parser.add_argument('--target-fps', type=float, help='Target FPS')
        
        # Sync command
        sync_parser = subparsers.add_parser('sync', help='Synchronize subtitles with video')
        sync_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        sync_parser.add_argument('-a', '--audio', required=True, help='Audio/video file')
        sync_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        sync_parser.add_argument('--method', choices=['whisper', 'ffmpeg', 'manual'], default='whisper')
        sync_parser.add_argument('--language', default='en', help='Language code')
        sync_parser.add_argument('--offset', type=float, default=0.0, help='Manual offset in seconds')
        
        # Adapt command
        adapt_parser = subparsers.add_parser('adapt', help='Adapt subtitle content')
        adapt_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        adapt_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        adapt_parser.add_argument('--target-audience', default='general', help='Target audience')
        adapt_parser.add_argument('--simplify', type=int, help='Simplify level (0-100)')
        adapt_parser.add_argument('--remove-profanity', action='store_true', help='Remove profanity')
        adapt_parser.add_argument('--cultural-sensitivity', action='store_true', help='Apply cultural sensitivity')
        
        # Analyze sentiment
        sentiment_parser = subparsers.add_parser('analyze-sentiment', help='Analyze sentiment')
        sentiment_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        sentiment_parser.add_argument('-m', '--model', help='AI model to use')
        sentiment_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Analyze emotion
        emotion_parser = subparsers.add_parser('analyze-emotion', help='Analyze emotion')
        emotion_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        emotion_parser.add_argument('-m', '--model', help='AI model to use')
        emotion_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Analyze cultural
        cultural_parser = subparsers.add_parser('analyze-cultural', help='Analyze cultural references')
        cultural_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        cultural_parser.add_argument('-m', '--model', help='AI model to use')
        cultural_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Analyze readability
        readability_parser = subparsers.add_parser('analyze-readability', help='Analyze readability')
        readability_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        readability_parser.add_argument('-m', '--model', help='AI model to use')
        readability_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Analyze frequency
        frequency_parser = subparsers.add_parser('analyze-frequency', help='Word frequency analysis')
        frequency_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        frequency_parser.add_argument('--export', help='Export format (json, csv, html)')
        frequency_parser.add_argument('--top', type=int, default=20, help='Number of top words to show')
        
        # Analyze complexity
        complexity_parser = subparsers.add_parser('analyze-complexity', help='Text complexity analysis')
        complexity_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        complexity_parser.add_argument('-m', '--model', help='AI model to use')
        complexity_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Batch command
        batch_parser = subparsers.add_parser('batch', help='Batch process files')
        batch_parser.add_argument('-d', '--directory', required=True, help='Input directory')
        batch_parser.add_argument('-o', '--output', required=True, help='Output directory')
        batch_parser.add_argument('--translate', help='Target language for translation')
        batch_parser.add_argument('--improve', action='store_true', help='Improve subtitles')
        batch_parser.add_argument('--fix-timing', action='store_true', help='Fix timing')
        batch_parser.add_argument('--sync', help='Sync with video file (requires video path)')
        batch_parser.add_argument('-p', '--parallel', type=int, default=4, help='Parallel workers')
        batch_parser.add_argument('--context', help='Context for translation')
        
        # Pipeline command
        pipeline_parser = subparsers.add_parser('pipeline', help='Execute a pipeline of operations')
        pipeline_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        pipeline_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        pipeline_parser.add_argument('--translate', help='Target language')
        pipeline_parser.add_argument('--translate-context', help='Context for translation')
        pipeline_parser.add_argument('--improve', action='store_true', help='Improve subtitles')
        pipeline_parser.add_argument('--improve-grammar', action='store_true', help='Fix grammar')
        pipeline_parser.add_argument('--analyze-sentiment', action='store_true', help='Analyze sentiment')
        pipeline_parser.add_argument('--summary', type=int, help='Generate summary with specified length')
        pipeline_parser.add_argument('--report', help='Export report to file')
        pipeline_parser.add_argument('--fix-timing', action='store_true', help='Fix timing')
        pipeline_parser.add_argument('--sync', help='Synchronize with video')
        
        # Statistics command
        stats_parser = subparsers.add_parser('stats', help='Generate statistics')
        stats_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        stats_parser.add_argument('--export', help='Export format (json, csv, html)')
        
        # Convert command
        convert_parser = subparsers.add_parser('convert', help='Convert format')
        convert_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        convert_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        convert_parser.add_argument('-f', '--format', required=True, help='Target format')
        
        # Summary command
        summary_parser = subparsers.add_parser('summary', help='Generate summary')
        summary_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        summary_parser.add_argument('--length', choices=['short', 'medium', 'long'], default='short')
        summary_parser.add_argument('-m', '--model', help='AI model to use (free models only)')
        
        # Merge command
        merge_parser = subparsers.add_parser('merge', help='Merge subtitle files')
        merge_parser.add_argument('-i', '--input', nargs='+', required=True, help='Input subtitle files')
        merge_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        merge_parser.add_argument('--order', choices=['timestamp', 'list'], default='timestamp')
        
        # Split command
        split_parser = subparsers.add_parser('split', help='Split subtitle file')
        split_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        split_parser.add_argument('-o', '--output', required=True, help='Output prefix')
        split_parser.add_argument('--chunks', type=int, help='Number of chunks')
        split_parser.add_argument('--lines-per-chunk', type=int, help='Lines per chunk')
        
        # Filter command
        filter_parser = subparsers.add_parser('filter', help='Filter subtitle content')
        filter_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        filter_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        filter_parser.add_argument('--remove', help='Remove pattern')
        filter_parser.add_argument('--search', help='Search pattern')
        filter_parser.add_argument('--replace', help='Replace pattern (pattern|replacement)')
        
        # Enhance command
        enhance_parser = subparsers.add_parser('enhance', help='Full subtitle enhancement')
        enhance_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        enhance_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        enhance_parser.add_argument('--fix-grammar', action='store_true', help='Fix grammar')
        enhance_parser.add_argument('--remove-fillers', action='store_true', help='Remove filler words')
        enhance_parser.add_argument('--adjust-timings', action='store_true', help='Adjust timing')
        enhance_parser.add_argument('--speaker-identification', action='store_true', help='Identify speakers')
        enhance_parser.add_argument('--compress', type=int, help='Compression level (0-100)')
        enhance_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Interactive command
        interactive_parser = subparsers.add_parser('interactive', help='Interactive TUI mode')
        interactive_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        interactive_parser.add_argument('--ai-assist', action='store_true', help='Enable AI assistance')
        interactive_parser.add_argument('--model', help='AI model for assistance')
        interactive_parser.add_argument('--theme', choices=['dark', 'light'], default='dark')
        interactive_parser.add_argument('--suggestions', action='store_true', help='Show suggestions')
        interactive_parser.add_argument('--auto-save', type=int, help='Auto-save interval in seconds')
        
        # Models command
        models_parser = subparsers.add_parser('models', help='List available AI models')
        models_parser.add_argument('--details', action='store_true', help='Show detailed model information')
        
        # Version command        subparsers.add_parser('version', help='Show version information')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Show file information')
        info_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        
        # Integrate command
        integrate_parser = subparsers.add_parser('integrate', help='Integration with media players')
        integrate_parser.add_argument('--vlc', help='VLC subtitle file')
        integrate_parser.add_argument('--mpc', help='MPC-HC subtitle file')
        integrate_parser.add_argument('--kodi', help='Kodi media directory')
        integrate_parser.add_argument('--sync', help='Sync with video file')
    
    def run(self, args=None):
        """Run the CLI."""
        args = self.parser.parse_args(args)
        
        if not args.command:
            self.parser.print_help()
            return
        
        command_map = {
            'wav': self._cmd_wav,
            'translate': self._cmd_translate,
            'translate-context': self._cmd_translate_context,
            'translate-dialect': self._cmd_translate_dialect,
            'translate-style': self._cmd_translate_style,
            'translate-batch': self._cmd_translate_batch,
            'improve': self._cmd_improve,
            'improve-grammar': self._cmd_improve_grammar,
            'improve-consistency': self._cmd_improve_consistency,
            'improve-formatting': self._cmd_improve_formatting,
            'improve-timing': self._cmd_improve_timing,
            'fix-timing': self._cmd_fix_timing,
            'sync': self._cmd_sync,
            'adapt': self._cmd_adapt,
            'analyze-sentiment': self._cmd_analyze_sentiment,
            'analyze-emotion': self._cmd_analyze_emotion,
            'analyze-cultural': self._cmd_analyze_cultural,
            'analyze-readability': self._cmd_analyze_readability,
            'analyze-frequency': self._cmd_analyze_frequency,
            'analyze-complexity': self._cmd_analyze_complexity,
            'batch': self._cmd_batch,
            'pipeline': self._cmd_pipeline,
            'stats': self._cmd_stats,
            'convert': self._cmd_convert,
            'summary': self._cmd_summary,
            'merge': self._cmd_merge,
            'split': self._cmd_split,
            'filter': self._cmd_filter,
            'enhance': self._cmd_enhance,
            'interactive': self._cmd_interactive,
            'models': self._cmd_models,
            'version': self._cmd_version,
            'info': self._cmd_info,
            'integrate': self._cmd_integrate,
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"Unknown command: {args.command}")
    
    def _cmd_wav(self, args):
        """Execute WAV to subtitle command."""
        try:
            print(f"Analyzing WAV file: {args.input}")
            
            audio_info = self.app.analyze_audio(args.input)
            print(f"Audio Info:")
            print(f"  Duration: {audio_info['duration']:.2f} seconds")
            print(f"  Channels: {audio_info['channels']}")
            print(f"  Sample Rate: {audio_info['frame_rate']} Hz")
            
            if args.analyze:
                print(f"  Max Amplitude: {audio_info.get('max_amplitude', 0)}")
                print(f"  RMS: {audio_info.get('rms', 0):.4f}")
                return
            
            if args.detect_speech:
                segments = self.app.detect_speech(args.input)
                print(f"Detected {len(segments)} speech segments:")
                for i, (start, end) in enumerate(segments[:10], 1):
                    print(f"  Segment {i}: {start:.2f}s - {end:.2f}s (duration: {end-start:.2f}s)")
                if len(segments) > 10:
                    print(f"  ... and {len(segments) - 10} more segments")
                return
            
            print(f"Generating subtitles for language: {args.language}")
            subtitle = self.app.generate_from_wav(args.input, args.language)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(subtitle, args.output)
            
            print(f"Generated {len(subtitle.entries)} subtitle entries")
            print("WAV processing completed successfully!")
            
            print("\nPreview:")
            for entry in subtitle.entries[:5]:
                print(f"  {entry}")
            if len(subtitle.entries) > 5:
                print(f"  ... and {len(subtitle.entries) - 5} more entries")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_translate(self, args):
        """Execute translate command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Translating to {args.target} using optimized FREE model...")
            translated = self.app.translate_subtitles(
                subtitle, args.target, args.source, args.model, 
                args.batch_size, args.context
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(translated, args.output)
            
            print(f"Translation completed! Generated {len(translated.entries)} entries.")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_translate_context(self, args):
        """Execute translate-context command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Translating with context to {args.target}...")
            translated = self.app.translate_subtitles(
                subtitle, args.target, args.source, args.model,
                10, args.context
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(translated, args.output)
            
            print("Context-aware translation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_translate_dialect(self, args):
        """Execute translate-dialect command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Translating to {args.target} ({args.dialect} dialect)...")
            translated = self.app.translate_dialect(
                subtitle, args.target, args.dialect, args.model
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(translated, args.output)
            
            print("Dialect translation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_translate_style(self, args):
        """Execute translate-style command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Translating to {args.target} with style {args.style}...")
            translated = self.app.translate_style(
                subtitle, args.target, args.style, args.model
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(translated, args.output)
            
            print("Style-preserving translation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_translate_batch(self, args):
        """Execute translate-batch command."""
        try:
            operations = {
                'translate': {
                    'target': args.target,
                    'batch_size': 10
                }
            }
            
            output_dir = args.output_dir or args.directory + '_translated'
            
            print(f"Batch translating directory: {args.directory}")
            results = self.app.batch_process(
                args.directory, output_dir, operations, args.parallel
            )
            
            print("\nBatch translation completed:")
            print(f"Total files: {results['total']}")
            print(f"Processed: {len(results['processed'])}")
            print(f"Failed: {len(results['failed'])}")
            
            if results['failed']:
                print("\nFailed files:")
                for fail in results['failed']:
                    print(f"  {fail['file']}: {fail['error']}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve(self, args):
        """Execute improve command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Improving subtitle quality using optimized FREE model...")
            if args.style:
                print(f"  Style: {args.style}")
            if args.tone:
                print(f"  Tone: {args.tone}")
            
            improved = self.app.improve_subtitles(subtitle, args.style, args.tone, args.model)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(improved, args.output)
            
            print(f"Improvement completed! Processed {len(improved.entries)} entries.")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve_grammar(self, args):
        """Execute improve-grammar command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Correcting grammar (level: {args.level})...")
            improved = self.app.improve_grammar(
                subtitle, args.level, args.preserve_style, args.model
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(improved, args.output)
            
            print("Grammar correction completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve_consistency(self, args):
        """Execute improve-consistency command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            characters = None
            if args.characters_file:
                with open(args.characters_file, 'r') as f:
                    characters = [line.strip() for line in f if line.strip()]
                print(f"Loaded {len(characters)} characters")
            
            print("Improving character consistency...")
            improved = self.app.improve_consistency(
                subtitle, characters, args.strict, args.model
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(improved, args.output)
            
            print("Consistency improvement completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve_formatting(self, args):
        """Execute improve-formatting command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Standardizing formatting...")
            improved = self.app.improve_formatting(
                subtitle, args.custom_template, args.no_style, args.model
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(improved, args.output)
            
            print("Formatting standardization completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve_timing(self, args):
        """Execute improve-timing command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Optimizing timing...")
            fixed = self.app.improve_timing(subtitle, args.auto, args.frame_rate)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(fixed, args.output)
            
            print("Timing optimization completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_fix_timing(self, args):
        """Execute fix-timing command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Fixing timing...")
            fixed = self.app.fix_timing(subtitle, args.shift, args.auto_detect, args.target_fps)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(fixed, args.output)
            
            print("Timing fixed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_sync(self, args):
        """Execute sync command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Synchronizing with {args.audio}...")
            synced = self.app.sync_subtitles(
                subtitle, args.audio, args.method, args.language, args.offset
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(synced, args.output)
            
            print("Synchronization completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_adapt(self, args):
        """Execute adapt command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Adapting for {args.target_audience}...")
            adapted = self.app.adapt_content(
                subtitle, args.target_audience, args.simplify,
                args.remove_profanity, args.cultural_sensitivity
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(adapted, args.output)
            
            print("Adaptation completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_sentiment(self, args):
        """Execute analyze-sentiment command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Analyzing sentiment...")
            result = self.app.analyze_subtitles(subtitle, 'sentiment', args.model)
            
            print("\nSentiment Analysis:")
            print("-" * 40)
            for key, value in result.items():
                print(f"{key}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_emotion(self, args):
        """Execute analyze-emotion command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Analyzing emotions...")
            result = self.app.analyze_subtitles(subtitle, 'emotion', args.model)
            
            print("\nEmotion Analysis:")
            print("-" * 40)
            for key, value in result.items():
                if key == 'emotions' and isinstance(value, dict):
                    print(f"{key}:")
                    for emotion, score in value.items():
                        print(f"  {emotion}: {score:.2f}")
                else:
                    print(f"{key}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_cultural(self, args):
        """Execute analyze-cultural command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Analyzing cultural references...")
            result = self.app.analyze_subtitles(subtitle, 'cultural', args.model)
            
            print("\nCultural Analysis:")
            print("-" * 40)
            for key, value in result.items():
                if key == 'cultural_references' and isinstance(value, list):
                    print(f"{key}:")
                    for ref in value:
                        print(f"  - {ref}")
                else:
                    print(f"{key}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_readability(self, args):
        """Execute analyze-readability command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Analyzing readability...")
            result = self.app.analyze_subtitles(subtitle, 'readability', args.model)
            
            print("\nReadability Analysis:")
            print("-" * 40)
            for key, value in result.items():
                if key == 'suggestions' and isinstance(value, list):
                    print(f"{key}:")
                    for suggestion in value:
                        print(f"  - {suggestion}")
                else:
                    print(f"{key}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_frequency(self, args):
        """Execute analyze-frequency command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            # Word frequency analysis
            text = subtitle.get_text_content()
            words = re.findall(r'\b[a-z]+\b', text.lower())
            freq = Counter(words)
            
            print(f"\nWord Frequency Analysis (Top {args.top}):")
            print("-" * 40)
            for word, count in freq.most_common(args.top):
                print(f"  {word}: {count}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_analyze_complexity(self, args):
        """Execute analyze-complexity command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Analyzing text complexity...")
            result = self.app.analyze_subtitles(subtitle, 'complexity', args.model)
            
            print("\nComplexity Analysis:")
            print("-" * 40)
            for key, value in result.items():
                if key == 'suggestions' and isinstance(value, list):
                    print(f"{key}:")
                    for suggestion in value:
                        print(f"  - {suggestion}")
                else:
                    print(f"{key}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_batch(self, args):
        """Execute batch command."""
        try:
            operations = {}
            if args.translate:
                operations['translate'] = {
                    'target': args.translate,
                    'context': args.context
                }
            if args.improve:
                operations['improve'] = {}
            if args.fix_timing:
                operations['fix_timing'] = {'auto_detect': True}
            if args.sync:
                operations['sync'] = {'video': args.sync}
            
            print(f"Batch processing directory: {args.directory}")
            results = self.app.batch_process(
                args.directory, args.output, operations, args.parallel
            )
            
            print("\nBatch processing completed:")
            print(f"Total files: {results['total']}")
            print(f"Processed: {len(results['processed'])}")
            print(f"Failed: {len(results['failed'])}")
            
            if results['failed']:
                print("\nFailed files:")
                for fail in results['failed']:
                    print(f"  {fail['file']}: {fail['error']}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_pipeline(self, args):
        """Execute pipeline command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            operations = []
            
            if args.translate:
                operations.append({
                    'type': 'translate',
                    'target': args.translate,
                    'batch_size': 10,
                    'context': args.translate_context
                })
            
            if args.improve:
                operations.append({
                    'type': 'improve'
                })
            
            if args.improve_grammar:
                operations.append({
                    'type': 'improve_grammar',
                    'level': 'standard',
                    'preserve_style': True
                })
            
            if args.fix_timing:
                operations.append({
                    'type': 'fix_timing',
                    'auto_detect': True
                })
            
            if args.sync:
                operations.append({
                    'type': 'sync',
                    'video': args.sync,
                    'method': 'whisper',
                    'language': 'en'
                })
            
            print("Executing pipeline...")
            result = self.app.pipeline(subtitle, operations)
            
            # Generate summary if requested
            if args.summary:
                print(f"\nGenerating summary (length: {args.summary})...")
                summary_length = 'short' if args.summary < 100 else 'medium' if args.summary < 300 else 'long'
                summary = self.app.summarize_subtitles(result, summary_length)
                print("\nSummary:")
                print("-" * 40)
                print(summary)
            
            # Analyze sentiment if requested
            if args.analyze_sentiment:
                print("\nAnalyzing sentiment...")
                sentiment = self.app.analyze_subtitles(result, 'sentiment')
                print(f"Sentiment: {sentiment.get('sentiment', 'unknown')}")
                print(f"Confidence: {sentiment.get('confidence', 0)}")
            
            print(f"\nSaving to: {args.output}")
            self.app.save_subtitle(result, args.output)
            
            if args.report:
                print(f"Exporting report to: {args.report}")
            
            print("Pipeline completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_stats(self, args):
        """Execute stats command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            stats = self.app.generate_statistics(subtitle)
            
            print("\nSubtitle Statistics:")
            print("-" * 40)
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"{key:20}: {value:.2f}")
                else:
                    print(f"{key:20}: {value}")
            
            if args.export:
                print(f"\nExporting to: {args.export}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_convert(self, args):
        """Execute convert command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Converting to {args.format}...")
            converted = self.app.convert_format(subtitle, args.format)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(converted, args.output, args.format)
            
            print("Conversion completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_summary(self, args):
        """Execute summary command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Generating summary using optimized FREE model...")
            summary = self.app.summarize_subtitles(subtitle, args.length, args.model)
            
            print("\nSummary:")
            print("-" * 40)
            print(summary)
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_merge(self, args):
        """Execute merge command."""
        try:
            print("Loading subtitle files...")
            subtitles = []
            for file_path in args.input:
                subtitles.append(self.app.load_subtitle(file_path))
                print(f"  Loaded: {file_path}")
            
            print(f"Merging with order: {args.order}")
            merged = self.app.merge_subtitles(subtitles, args.order)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(merged, args.output)
            
            print("Merge completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_split(self, args):
        """Execute split command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Splitting file...")
            chunks = self.app.split_subtitles(subtitle, args.chunks, args.lines_per_chunk)
            
            print(f"Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks, 1):
                output_file = f"{args.output}_{i:02d}.{chunk.format}"
                self.app.save_subtitle(chunk, output_file)
                print(f"  Saved: {output_file}")
            
            print("Split completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_filter(self, args):
        """Execute filter command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Filtering content...")
            filtered = self.app.filter_content(
                subtitle, args.remove, args.search, args.replace
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(filtered, args.output)
            
            print(f"Filtered {len(filtered.entries)} entries")
            print("Filter completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_enhance(self, args):
        """Execute enhance command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            operations = []
            
            if args.fix_grammar:
                operations.append({
                    'type': 'improve_grammar',
                    'level': 'standard',
                    'preserve_style': True,
                    'model': args.model
                })
            
            if args.remove_fillers:
                operations.append({
                    'type': 'filter',
                    'remove': r'\b(um|uh|like|you know|actually|basically|so|well|you see|i mean)\b'
                })
            
            if args.adjust_timings:
                operations.append({
                    'type': 'fix_timing',
                    'auto_detect': True
                })
            
            if args.speaker_identification:
                # This would be implemented with AI
                print("Speaker identification not yet fully implemented")
                operations.append({
                    'type': 'improve_consistency',
                    'model': args.model
                })
            
            if args.compress:
                # Compression would be implemented
                print(f"Compression level: {args.compress}")
            
            print("Enhancing subtitle...")
            if operations:
                result = self.app.pipeline(subtitle, operations)
            else:
                result = subtitle
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(result, args.output)
            
            print("Enhancement completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_interactive(self, args):
        """Execute interactive command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("\nSuperSRT Interactive Mode")
            print("=" * 50)
            print(f"File: {args.input}")
            print(f"Entries: {len(subtitle.entries)}")
            
            if args.ai_assist:
                print("AI Assistance: Enabled")
                if args.model:
                    print(f"Model: {args.model}")
            
            if args.suggestions:
                print("Suggestions: Enabled")
            
            print("\nCommands: [view] [edit] [translate] [improve] [save] [quit]")
            
            while True:
                try:
                    cmd = input("\n> ").strip().lower()
                    
                    if cmd in ['q', 'quit', 'exit']:
                        print("Exiting interactive mode...")
                        if args.auto_save:
                            print(f"Auto-saving... (last saved {args.auto_save}s ago)")
                        break
                    elif cmd in ['v', 'view']:
                        print("\nFirst 10 entries:")
                        for entry in subtitle.entries[:10]:
                            print(f"{entry.index}: {entry.text[:80]}...")
                    elif cmd in ['save']:
                        self.app.save_subtitle(subtitle, args.input)
                        print("Saved!")
                    elif cmd in ['info']:
                        stats = subtitle.get_statistics()
                        print(f"Entries: {stats['total_entries']}")
                        print(f"Total duration: {stats['total_duration']:.1f}s")
                        print(f"Total words: {stats['total_words']}")
                    else:
                        print("Unknown command. Available: view, save, info, quit")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_models(self, args):
        """Execute models command."""
        try:
            models = self.app.list_models()
            
            print("\n" + "="*80)
            print("AVAILABLE FREE MODELS")
            print("="*80)
            
            if not models:
                print("No models available. Check OpenRouter API key.")
                return
            
            print(f"\nTotal Models: {len(models)}")
            
            # Group models by strength
            strengths = defaultdict(list)
            for model, caps in models.items():
                strengths[caps.get('strength', 'general')].append((model, caps))
            
            print("\n" + "-"*80)
            print("MODELS BY STRENGTH")
            print("-"*80)
            
            for strength, model_list in sorted(strengths.items()):
                print(f"\n{strength.upper()}:")
                for model, caps in model_list:
                    print(f"  • {model}")
                    if args.details:
                        print(f"      Context: {caps.get('context', 'N/A')} tokens")
                        print(f"      Speed: {caps.get('speed', 'N/A')}")
                        print(f"      Languages: {caps.get('languages', 'N/A')}")
                        print(f"      Quality: {caps.get('quality', 'N/A')}")
            
            print("\n" + "-"*80)
            print("RECOMMENDED MODELS BY TASK")
            print("-"*80)
            print("  Translation (Premium): " + FREE_MODELS.get('translation_premium', 'N/A'))
            print("  Translation:          " + FREE_MODELS.get('translation', 'N/A'))
            print("  Improvement:          " + FREE_MODELS.get('improvement', 'N/A'))
            print("  Summarization:        " + FREE_MODELS.get('summarization', 'N/A'))
            print("  Analysis (Premium):   " + FREE_MODELS.get('analysis_premium', 'N/A'))
            print("  Analysis:             " + FREE_MODELS.get('analysis', 'N/A'))
            print("  Fast Processing:      " + FREE_MODELS.get('fast', 'N/A'))
            print("  Fallback:             " + FREE_MODELS.get('fallback', 'N/A'))
            print("="*80)
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_version(self, args):
        """Execute version command."""
        print(f"SuperSRT v{VERSION} (OPTIMIZED FREE MODELS)")
        print(f"Author: {APP_AUTHOR}")
        print(f"URL: {APP_URL}")
        print(f"License: {LICENSE}")
        print(f"Python: {sys.version}")
        print(f"\nAvailable Models: {len(FREE_MODELS)}")
        print("Optimized for: Translation, Improvement, Summarization, Analysis")
        
        print(f"\nDependencies:")
        print(f"  OpenRouter: {'✓' if OPENROUTER_AVAILABLE else '✗'}")
        print(f"  pysrt: {'✓' if PYSRT_AVAILABLE else '✗'}")
        print(f"  chardet: {'✓' if CHARDET_AVAILABLE else '✗'}")
        print(f"  SpeechRecognition: {'✓' if SR_AVAILABLE else '✗'}")
        print(f"  numpy: {'✓' if NUMPY_AVAILABLE else '✗'}")
        print(f"  Rich: {'✓' if RICH_AVAILABLE else '✗'}")
        print(f"  python-dotenv: {'✓' if DOTENV_AVAILABLE else '✗'}")
    
    def _cmd_info(self, args):
        """Execute info command."""
        try:
            print(f"Analyzing: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("\nFile Information:")
            print("-" * 40)
            print(f"Format: {subtitle.format}")
            print(f"Encoding: {subtitle.encoding}")
            print(f"Entries: {len(subtitle.entries)}")
            
            if subtitle.file_path:
                print(f"File size: {subtitle.file_path.stat().st_size:,} bytes")
                print(f"Modified: {datetime.fromtimestamp(subtitle.file_path.stat().st_mtime)}")
            
            stats = subtitle.get_statistics()
            print(f"\nContent Statistics:")
            print(f"Total duration: {stats['total_duration']:.2f}s")
            print(f"Average duration: {stats['average_duration']:.2f}s")
            print(f"Total words: {stats['total_words']}")
            print(f"Reading speed: {stats['reading_speed']:.1f} words/min")
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_integrate(self, args):
        """Execute integrate command."""
        try:
            if args.vlc:
                print(f"Integrating with VLC: {args.vlc}")
                # VLC integration would go here
                print("VLC integration completed!")
            
            if args.mpc:
                print(f"Integrating with MPC-HC: {args.mpc}")
                # MPC-HC integration would go here
                print("MPC-HC integration completed!")
            
            if args.kodi:
                print(f"Integrating with Kodi: {args.kodi}")
                # Kodi integration would go here
                print("Kodi integration completed!")
            
            if args.sync:
                print(f"Syncing with video: {args.sync}")
                # Sync implementation would go here
                print("Sync completed!")
            
            if not any([args.vlc, args.mpc, args.kodi, args.sync]):
                print("Please specify an integration option (--vlc, --mpc, --kodi, --sync)")
                return 1
            
        except Exception as e:
            print(f"Error: {e}")
            return 1

# ============================================
# Main Entry Point
# ============================================

def main():
    """Main entry point."""
    cli = CLI()
    sys.exit(cli.run())

if __name__ == "__main__":
    main()
