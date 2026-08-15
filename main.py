#!/usr/bin/env python3
# ============================================
# SuperSRT - Advanced AI-Powered Subtitle Processing Suite
# Version: 2.0.0
# ============================================

"""
SuperSRT: A comprehensive subtitle processing toolkit with AI capabilities
powered by OpenRouter API.
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
    import typer
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
        'default_model': 'nvidia/nemotron-3-nano-30b-a3b:free',
        'translation_model': 'openai/gpt-4o',
        'improvement_model': 'anthropic/claude-3.5-sonnet',
        'summarization_model': 'google/gemini-2.0-flash-exp',
        'temperature': 0.7,
        'max_tokens': 4096,
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
        """
        Parse subtitle content from string, bytes, or file path.
        
        Args:
            content: Content to parse (string, bytes, or file path)
            format_hint: Optional format hint
        
        Returns:
            SubtitleFile object
        """
        # Handle file path
        if isinstance(content, (str, Path)):
            path = Path(content)
            if path.exists():
                return self.parse_file(path)
            else:
                raise FileNotFoundError(f"File not found: {path}")
        
        # Handle bytes
        if isinstance(content, bytes):
            # Detect encoding if needed
            if CHARDET_AVAILABLE:
                encoding = chardet.detect(content)['encoding'] or 'utf-8'
            else:
                encoding = 'utf-8'
            content_str = content.decode(encoding)
            return self.parse_text(content_str, format_hint)
        
        # Handle string
        if isinstance(content, str):
            return self.parse_text(content, format_hint)
        
        raise ValueError("Unsupported content type for parsing")
    
    def parse_file(self, file_path: Path) -> SubtitleFile:
        """Parse subtitle file from path."""
        # Detect encoding
        encoding = 'utf-8'
        if CHARDET_AVAILABLE:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        # Read and parse
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        # Determine format from extension
        ext = file_path.suffix.lower()[1:] if file_path.suffix else ''
        format_hint = ext if ext in self.supported_formats else None
        
        subtitle_file = self.parse_text(content, format_hint)
        subtitle_file.file_path = file_path
        subtitle_file.encoding = encoding
        
        return subtitle_file
    
    def parse_text(self, text: str, format_hint: Optional[str] = None) -> SubtitleFile:
        """Parse subtitle text content."""
        # Try to detect format if not specified
        if format_hint and format_hint in self.supported_formats:
            return self._parse_format(text, format_hint)
        
        # Auto-detect format
        formats_to_try = ['srt', 'vtt', 'ass', 'ttml', 'json', 'csv']
        for fmt in formats_to_try:
            if fmt in self.supported_formats and self.supported_formats[fmt]['read']:
                try:
                    return self._parse_format(text, fmt)
                except ValueError:
                    continue
        
        # Default to SRT
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
            
            # Parse index
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            # Parse timecode
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', lines[1])
            if not time_match:
                continue
            
            start = self._parse_timecode(time_match.group(1))
            end = self._parse_timecode(time_match.group(2))
            
            # Parse text (remaining lines)
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
        # Remove header if present
        lines = text.split('\n')
        while lines and (not lines[0].strip() or lines[0].strip().startswith('WEBVTT')):
            lines.pop(0)
        
        # Parse like SRT but with different timecode format
        text = '\n'.join(lines)
        return self._parse_srt(text)  # VTT uses similar format
    
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
                parts = line.split(',', 9)  # Split into 10 parts
                if len(parts) >= 10:
                    try:
                        start = self._parse_timecode(parts[1].strip())
                        end = self._parse_timecode(parts[2].strip())
                        text_content = parts[9].strip()
                        # Remove formatting tags
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
                
                # Parse begin and end times
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
        # Handle milliseconds with comma or period
        time_str = time_str.replace(',', '.')
        
        # Check if it's in HH:MM:SS.mmm or MM:SS.mmm format
        parts = time_str.split(':')
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        
        elif len(parts) == 2:  # MM:SS.mmm
            minutes = int(parts[0])
            seconds_parts = parts[1].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            return timedelta(minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        
        else:
            # Try parsing as seconds
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
        # Determine format
        format_name = format_hint or subtitle_file.format or 'srt'
        if format_name not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_name}")
        
        if not self.supported_formats[format_name]['write']:
            raise ValueError(f"Format {format_name} does not support writing")
        
        # Generate content
        content = self._generate_content(subtitle_file, format_name)
        
        # Write to file
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
            lines.append('')  # Empty line between entries
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
        output = []
        output.append('index,start,end,text')
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
# AI Integration Module
# ============================================

class AIEngine:
    """Handles AI operations using OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.config = config or DEFAULT_CONFIG['ai']
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the OpenRouter client."""
        if not OPENROUTER_AVAILABLE:
            raise ImportError("OpenRouter library not installed")
        
        self.client = OpenRouter(api_key=self.api_key)
    
    def translate(self, text: Union[str, List[str]], target_lang: str, 
                  source_lang: Optional[str] = None, model: Optional[str] = None) -> Union[str, List[str]]:
        """Translate text using AI."""
        model = model or self.config.get('translation_model', 'openai/gpt-4o')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = f"Translate the following text to {target_lang}:"
            if source_lang:
                prompt = f"Translate from {source_lang} to {target_lang}:"
            
            messages = [
                {"role": "system", "content": "You are a professional translator. Provide accurate translations."},
                {"role": "user", "content": f"{prompt}\n\n{t}"}
            ]
            
            response = self.client.chat.send(
                model=model,
                messages=messages,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            translated = response.choices[0].message.content.strip()
            results.append(translated)
        
        return results if is_list else results[0]
    
    def improve_subtitles(self, text: Union[str, List[str]], style: Optional[str] = None,
                          tone: Optional[str] = None, model: Optional[str] = None) -> Union[str, List[str]]:
        """Improve subtitle text quality using AI."""
        model = model or self.config.get('improvement_model', 'anthropic/claude-3.5-sonnet')
        
        is_list = isinstance(text, list)
        texts = text if is_list else [text]
        
        results = []
        for t in texts:
            prompt = "Improve the following subtitle text:"
            if style:
                prompt += f" Style: {style}"
            if tone:
                prompt += f" Tone: {tone}"
            
            messages = [
                {"role": "system", "content": "You are a subtitle editor. Improve clarity, grammar, and readability."},
                {"role": "user", "content": f"{prompt}\n\n{t}"}
            ]
            
            response = self.client.chat.send(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            improved = response.choices[0].message.content.strip()
            results.append(improved)
        
        return results if is_list else results[0]
    
    def summarize_subtitles(self, text: str, length: str = 'short', 
                           model: Optional[str] = None) -> str:
        """Generate summary of subtitle content."""
        model = model or self.config.get('summarization_model', 'google/gemini-2.0-flash-exp')
        
        length_desc = {
            'short': 'brief (1-2 sentences per scene)',
            'medium': 'moderate (3-4 sentences per scene)',
            'long': 'detailed (5-7 sentences per scene)'
        }
        
        prompt = f"Summarize these subtitles in {length_desc.get(length, 'short')} length:\n\n{text}"
        
        messages = [
            {"role": "system", "content": "You are a content summarizer. Provide clear, concise summaries."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.send(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048
        )
        
        return response.choices[0].message.content.strip()
    
    def analyze_sentiment(self, text: str, model: Optional[str] = None) -> Dict:
        """Analyze sentiment of subtitle text."""
        model = model or self.config.get('analysis_model', 'mistralai/mixtral-8x7b-instruct')
        
        prompt = f"""Analyze the sentiment of the following text and provide a JSON response with:
        - sentiment: (positive/negative/neutral)
        - confidence: (0.0-1.0)
        - emotions: (list of emotions)
        - intensity: (1-10)
        
        Text: {text}"""
        
        messages = [
            {"role": "system", "content": "You are a sentiment analyst. Provide detailed sentiment analysis."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.send(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048
        )
        
        try:
            return json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            return {
                'sentiment': 'unknown',
                'confidence': 0.0,
                'emotions': [],
                'intensity': 0
            }
    
    def generate_subtitles(self, video_path: str, language: str, 
                          model: str = 'openai/whisper-large-v3') -> SubtitleFile:
        """Generate subtitles from audio/video using AI."""
        # This would require Whisper integration
        # Placeholder for future implementation
        raise NotImplementedError("Audio-to-subtitle generation coming soon")

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
        # Convert args and kwargs to a string representation
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
        
        # Check TTL
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
    # Remove invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra underscores and spaces
    safe = re.sub(r'[\s_]+', '_', safe)
    # Limit length
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

def timecode_to_seconds(timecode: str) -> float:
    """Convert timecode to seconds."""
    parts = timecode.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds.replace(',', '.'))
    elif len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds.replace(',', '.'))
    else:
        return float(timecode.replace(',', '.'))

def seconds_to_timecode(seconds: float) -> str:
    """Convert seconds to timecode."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

# ============================================
# Main Application Class
# ============================================

class SuperSRT:
    """Main SuperSRT application class."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self.parser = SubtitleParser()
        self.writer = SubtitleWriter()
        self.ai_engine = None
        self.cache_manager = CacheManager(
            cache_dir=os.getenv('CACHE_LOCATION', './cache'),
            enabled=self.config.get('cache_enabled', True),
            ttl=self.config.get('cache_ttl', 86400)
        )
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize AI if API key is available
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            try:
                self.ai_engine = AIEngine(api_key, self.config.get('ai', {}))
            except Exception as e:
                self.logger.warning(f"AI initialization failed: {e}")
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = self.config.get('logging', DEFAULT_CONFIG['logging'])
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        # Create logs directory
        log_file = Path(log_config.get('file', './logs/supersrt.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
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
    
    def translate_subtitles(self, subtitle_file: SubtitleFile, target_lang: str,
                           source_lang: Optional[str] = None, model: Optional[str] = None,
                           batch_size: int = 10) -> SubtitleFile:
        """Translate subtitle file to target language."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        # Extract all text
        texts = [entry.text for entry in subtitle_file.entries]
        
        # Process in batches
        translated_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            translated = self.ai_engine.translate(
                batch, target_lang, source_lang, model
            )
            translated_texts.extend(translated if isinstance(translated, list) else [translated])
        
        # Create new subtitle file with translated text
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
                'translated_to': target_lang
            },
            file_path=subtitle_file.file_path
        )
    
    def improve_subtitles(self, subtitle_file: SubtitleFile, style: Optional[str] = None,
                         tone: Optional[str] = None, model: Optional[str] = None,
                         batch_size: int = 10) -> SubtitleFile:
        """Improve subtitle quality using AI."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        # Extract all text
        texts = [entry.text for entry in subtitle_file.entries]
        
        # Process in batches
        improved_texts = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            improved = self.ai_engine.improve_subtitles(
                batch, style, tone, model
            )
            improved_texts.extend(improved if isinstance(improved, list) else [improved])
        
        # Create new subtitle file with improved text
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
                'improvement_tone': tone
            },
            file_path=subtitle_file.file_path
        )
    
    def summarize_subtitles(self, subtitle_file: SubtitleFile, length: str = 'short',
                           model: Optional[str] = None) -> str:
        """Generate summary of subtitle file."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        text = subtitle_file.get_text_content()
        return self.ai_engine.summarize_subtitles(text, length, model)
    
    def analyze_subtitles(self, subtitle_file: SubtitleFile, model: Optional[str] = None) -> Dict:
        """Analyze subtitle file content."""
        if not self.ai_engine:
            raise ValueError("AI engine not initialized. Check OpenRouter API key.")
        
        text = subtitle_file.get_text_content()
        return self.ai_engine.analyze_sentiment(text, model)
    
    def fix_timing(self, subtitle_file: SubtitleFile, shift: Optional[float] = None,
                  auto_detect: bool = False, target_fps: Optional[float] = None) -> SubtitleFile:
        """Fix timing issues in subtitle file."""
        if shift is not None:
            # Simple shift
            return subtitle_file.shift_timing(shift)
        
        if auto_detect:
            # Auto-detect timing issues (placeholder implementation)
            # In reality, this would analyze speech patterns, silence gaps, etc.
            self.logger.info("Auto-detecting timing issues...")
            # For now, just return the same file
            return subtitle_file
        
        if target_fps:
            # Convert FPS (placeholder implementation)
            self.logger.info(f"Converting to {target_fps} FPS...")
            return subtitle_file
        
        return subtitle_file
    
    def merge_subtitles(self, subtitle_files: List[SubtitleFile], 
                       order: str = 'timestamp') -> SubtitleFile:
        """Merge multiple subtitle files."""
        if order == 'timestamp':
            # Merge and sort by time
            all_entries = []
            for sf in subtitle_files:
                all_entries.extend(sf.entries)
            all_entries.sort(key=lambda x: x.start_time)
        else:
            # Just concatenate
            all_entries = []
            for sf in subtitle_files:
                all_entries.extend(sf.entries)
        
        # Renumber
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
            # Split by number of chunks
            entries_per_chunk = max(1, len(subtitle_file.entries) // chunks)
        elif lines_per_chunk:
            entries_per_chunk = lines_per_chunk
        else:
            raise ValueError("Either chunks or lines_per_chunk must be specified")
        
        result = []
        for i in range(0, len(subtitle_file.entries), entries_per_chunk):
            chunk_entries = subtitle_file.entries[i:i + entries_per_chunk]
            # Renumber entries in chunk
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
        
        # Find all subtitle files
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
                # Load
                sub = self.load_subtitle(file_path)
                
                # Apply operations
                if 'translate' in operations:
                    sub = self.translate_subtitles(sub, operations['translate']['target'])
                
                if 'improve' in operations:
                    sub = self.improve_subtitles(sub, 
                                                operations['improve'].get('style'),
                                                operations['improve'].get('tone'))
                
                if 'fix_timing' in operations:
                    sub = self.fix_timing(sub, 
                                         operations['fix_timing'].get('shift'),
                                         operations['fix_timing'].get('auto_detect', False))
                
                # Save
                output_file = output_path / file_path.name
                self.save_subtitle(sub, output_file)
                
                return file_path, sub, None
            
            except Exception as e:
                return file_path, None, e
        
        # Process in parallel
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
            # Remove entries matching pattern
            pattern = re.compile(remove_pattern, re.IGNORECASE)
            entries = [e for e in entries if not pattern.search(e.text)]
        
        if search_pattern:
            # Keep entries matching pattern
            pattern = re.compile(search_pattern, re.IGNORECASE)
            entries = [e for e in entries if pattern.search(e.text)]
        
        if replace_pattern:
            # Replace pattern in text
            pattern, replacement = replace_pattern.split('|', 1)
            pattern = re.compile(pattern)
            for entry in entries:
                entry.text = pattern.sub(replacement, entry.text)
        
        # Renumber
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

# ============================================
# CLI Interface
# ============================================

class CLI:
    """Command-line interface for SuperSRT."""
    
    def __init__(self):
        self.app = SuperSRT()
        self.console = Console() if RICH_AVAILABLE else None
        
        # Setup command parser
        self.parser = argparse.ArgumentParser(
            description='SuperSRT - Advanced AI-Powered Subtitle Processing Suite',
            epilog=f"Version {VERSION} | {APP_URL}"
        )
        self._setup_arguments()
    
    def _setup_arguments(self):
        """Setup command-line arguments."""
        subparsers = self.parser.add_subparsers(dest='command', help='Command to execute')
        
        # Translate command
        translate_parser = subparsers.add_parser('translate', help='Translate subtitles')
        translate_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        translate_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        translate_parser.add_argument('-t', '--target', required=True, help='Target language code')
        translate_parser.add_argument('-s', '--source', help='Source language code')
        translate_parser.add_argument('-m', '--model', help='AI model to use')
        translate_parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
        
        # Improve command
        improve_parser = subparsers.add_parser('improve', help='Improve subtitle quality')
        improve_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        improve_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        improve_parser.add_argument('--style', help='Style (conversational, formal, etc.)')
        improve_parser.add_argument('--tone', help='Tone (friendly, professional, etc.)')
        improve_parser.add_argument('-m', '--model', help='AI model to use')
        
        # Fix timing command
        timing_parser = subparsers.add_parser('fix-timing', help='Fix timing issues')
        timing_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
        timing_parser.add_argument('-o', '--output', required=True, help='Output subtitle file')
        timing_parser.add_argument('--shift', type=float, help='Shift timing by seconds')
        timing_parser.add_argument('--auto-detect', action='store_true', help='Auto-detect timing issues')
        timing_parser.add_argument('--target-fps', type=float, help='Target FPS')
        
        # Batch command
        batch_parser = subparsers.add_parser('batch', help='Batch process files')
        batch_parser.add_argument('-d', '--directory', required=True, help='Input directory')
        batch_parser.add_argument('-o', '--output', required=True, help='Output directory')
        batch_parser.add_argument('--translate', help='Target language for translation')
        batch_parser.add_argument('--improve', action='store_true', help='Improve subtitles')
        batch_parser.add_argument('--fix-timing', action='store_true', help='Fix timing')
        batch_parser.add_argument('-p', '--parallel', type=int, default=4, help='Parallel workers')
        
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
        summary_parser.add_argument('-m', '--model', help='AI model to use')
        
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
        
        # Version command
        version_parser = subparsers.add_parser('version', help='Show version information')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Show file information')
        info_parser.add_argument('-i', '--input', required=True, help='Input subtitle file')
    
    def run(self, args=None):
        """Run the CLI."""
        args = self.parser.parse_args(args)
        
        if not args.command:
            self.parser.print_help()
            return
        
        # Execute command
        command_map = {
            'translate': self._cmd_translate,
            'improve': self._cmd_improve,
            'fix-timing': self._cmd_fix_timing,
            'batch': self._cmd_batch,
            'stats': self._cmd_stats,
            'convert': self._cmd_convert,
            'summary': self._cmd_summary,
            'merge': self._cmd_merge,
            'split': self._cmd_split,
            'filter': self._cmd_filter,
            'version': self._cmd_version,
            'info': self._cmd_info,
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"Unknown command: {args.command}")
    
    def _cmd_translate(self, args):
        """Execute translate command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print(f"Translating to {args.target}...")
            translated = self.app.translate_subtitles(
                subtitle, args.target, args.source, args.model, args.batch_size
            )
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(translated, args.output)
            
            print("Translation completed successfully!")
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_improve(self, args):
        """Execute improve command."""
        try:
            print(f"Loading subtitle file: {args.input}")
            subtitle = self.app.load_subtitle(args.input)
            
            print("Improving subtitle quality...")
            improved = self.app.improve_subtitles(subtitle, args.style, args.tone, args.model)
            
            print(f"Saving to: {args.output}")
            self.app.save_subtitle(improved, args.output)
            
            print("Improvement completed successfully!")
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
    
    def _cmd_batch(self, args):
        """Execute batch command."""
        try:
            operations = {}
            if args.translate:
                operations['translate'] = {'target': args.translate}
            if args.improve:
                operations['improve'] = {}
            if args.fix_timing:
                operations['fix_timing'] = {'auto_detect': True}
            
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
                # Export implementation would go here
            
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
            
            print("Generating summary...")
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
    
    def _cmd_version(self, args):
        """Execute version command."""
        print(f"SuperSRT v{VERSION}")
        print(f"Author: {APP_AUTHOR}")
        print(f"URL: {APP_URL}")
        print(f"Python: {sys.version}")
    
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

# ============================================
# Main Entry Point
# ============================================

def main():
    """Main entry point."""
    cli = CLI()
    sys.exit(cli.run())

if __name__ == "__main__":
    main()
