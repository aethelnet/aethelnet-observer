"""
Knowledge Base Parser - Auto-Tagger for Any Text/Code Document

Supports: .md, .py, .vue, .js, .ts, .json, .yaml, .txt
Auto-detects: headings, code blocks, functions, classes, imports, TODOs, FIXMEs
"""

import os
import re
import ast
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ParsedBlock:
    """A parsed block with auto-detected type and tags."""
    content: str
    block_type: str  # heading, code, function, class, import, task, comment, text
    tags: List[str]  # #hashtags, @mentions, TODO, FIXME
    language: str    # python, javascript, markdown, etc.
    line_start: int
    line_end: int
    parent_path: Optional[str] = None  # For nested structures
    metadata: Dict = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class UniversalParser:
    """
    Auto-tagging parser for any text or code document.
    
    Usage:
        parser = UniversalParser()
        blocks = parser.parse_file('/path/to/file.py')
        # or
        blocks = parser.parse_content(content, language='python')
    """
    
    # File extension to language mapping
    LANG_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.vue': 'vue',
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.txt': 'text',
        '.sh': 'bash',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.hpp': 'cpp',
        '.cc': 'cpp',
        '.rs': 'rust',
        '.toml': 'toml',
        'makefile': 'makefile',
        'kconfig': 'kconfig',
    }
    
    # Patterns for auto-detection
    TAG_PATTERNS = {
        'hashtag': r'#(\w+)',
        'mention': r'@(\w+)',
        'todo': r'\bTODO[:\s](.+?)(?:\n|$)',
        'fixme': r'\bFIXME[:\s](.+?)(?:\n|$)',
        'note': r'\bNOTE[:\s](.+?)(?:\n|$)',
        'wikilink': r'\[\[([^\]]+)\]\]',
    }
    
    def __init__(self):
        self.blocks: List[ParsedBlock] = []
    
    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        return self.LANG_MAP.get(ext, 'text')
    
    def extract_tags(self, content: str) -> List[str]:
        """Extract all tags from content."""
        tags = []
        for tag_type, pattern in self.TAG_PATTERNS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if tag_type == 'hashtag':
                    tags.append(f'#{match}')
                elif tag_type == 'todo':
                    tags.append('TODO')
                elif tag_type == 'fixme':
                    tags.append('FIXME')
                elif tag_type == 'note':
                    tags.append('NOTE')
                elif tag_type == 'wikilink':
                    tags.append(f'[[{match}]]')
        return list(set(tags))
    
    def parse_file(self, file_path: str) -> List[ParsedBlock]:
        """Parse any file into tagged blocks."""
        if not os.path.isfile(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        language = self.detect_language(file_path)
        return self.parse_content(content, language)
    
    def parse_content(self, content: str, language: str = 'text') -> List[ParsedBlock]:
        """Parse content string into tagged blocks."""
        self.blocks = []
        
        if language == 'python':
            self._parse_python(content)
        elif language == 'markdown':
            self._parse_markdown(content)
        elif language in ('javascript', 'typescript'):
            self._parse_javascript(content)
        elif language == 'vue':
            self._parse_vue(content)
        elif language in ('c', 'cpp'):
            self._parse_c_cpp(content, language)
        elif language == 'rust':
            self._parse_rust(content)
        elif language == 'makefile':
            self._parse_makefile(content)
        else:
            # Fallback: Treat as generic text and extract tags
            self._parse_text_autotag(content, language)
        
        return self.blocks
    
    # ==========================================
    # Python Parser (AST-based)
    # ==========================================

    def _calculate_complexity(self, node) -> int:
        """
        Estimate Cyclomatic Complexity (McCabe).
        Start with 1. Add 1 for every branching node.
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.ExceptHandler, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _map_python_type_to_socket(self, py_type: str) -> str:
        """Map Python type strings to Blender-style Schema."""
        t = py_type.lower()
        if t == 'int': return 'SOCK_INT'
        if t == 'float': return 'SOCK_FLOAT'
        if t == 'str': return 'SOCK_STRING'
        if t == 'bool': return 'SOCK_BOOLEAN'
        if t == 'bool': return 'SOCK_BOOLEAN'
        if 'vec' in t or 'tuple' in t: return 'SOCK_VECTOR'
        if 'list' in t or 'dict' in t or 'any' in t: return 'SOCK_OBJECT'
        if 'signal' in t: return 'SOCK_SIGNAL' # Explicit Signal Type
        return 'SOCK_CUSTOM'
    
    def _parse_python(self, content: str):
        """Parse Python using AST for accurate structure detection."""
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to generic parsing if syntax error
            self._parse_generic(content, 'python')
            return
        
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                line = lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                imports.append(line.strip())
        
        if imports:
            self.blocks.append(ParsedBlock(
                content='\n'.join(imports),
                block_type='import',
                tags=['import'],
                language='python',
                line_start=1,
                line_end=len(imports),
                metadata={'count': len(imports)}
            ))
        
        # Extract functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                self._extract_python_function(node, lines)
            elif isinstance(node, ast.AsyncFunctionDef):
                self._extract_python_function(node, lines, is_async=True)
            elif isinstance(node, ast.ClassDef):
                self._extract_python_class(node, lines)
    
    def _extract_python_function(self, node, lines, is_async=False):
        """Extract function definition with docstring."""
        start = node.lineno
        end = node.end_lineno or start
        
        func_lines = lines[start-1:end]
        content = '\n'.join(func_lines)
        
        # Extract docstring
        docstring = ast.get_docstring(node) or ''
        
        tags = self.extract_tags(content)
        if is_async:
            tags.append('async')
        if docstring:
            tags.append('documented')
        

        # Extract Inputs (Args) with Types
        inputs = []
        for arg in node.args.args:
            arg_type = "Any"
            if arg.annotation:
                arg_type = ast.unparse(arg.annotation)
            inputs.append({
                "name": arg.arg, 
                "type": arg_type,
                "socket_type": self._map_python_type_to_socket(arg_type)
            })

        # Extract Output (Return Type)
        output_type = "None"
        if node.returns:
            output_type = ast.unparse(node.returns)
        outputs = [{
            "name": "return", 
            "type": output_type,
            "socket_type": self._map_python_type_to_socket(output_type)
        }]

        # Check for @signal decorator
        is_signal = any('signal' in ast.unparse(d).lower() for d in node.decorator_list)
        if is_signal:
            outputs.append({
                "name": "signal", 
                "type": "Signal", 
                "socket_type": "SOCK_SIGNAL"
            })

        self.blocks.append(ParsedBlock(
            content=content,
            block_type='function',
            tags=tags + (['signal'] if is_signal else []),
            language='python',
            line_start=start,
            line_end=end,
            metadata={
                'name': node.name,
                'args': [arg.arg for arg in node.args.args],
                'inputs': inputs,    # NEW: Structured Sockets
                'outputs': outputs,  # NEW: Structured Sockets
                'docstring': docstring[:200] if docstring else None,
                'decorators': [ast.unparse(d) for d in node.decorator_list] if node.decorator_list else [],
                'complexity': self._calculate_complexity(node)
            }
        ))
    
    def _extract_python_class(self, node, lines):
        """Extract class definition with methods."""
        start = node.lineno
        end = node.end_lineno or start
        
        class_lines = lines[start-1:end]
        content = '\n'.join(class_lines)
        
        docstring = ast.get_docstring(node) or ''
        
        # Get method names
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        tags = self.extract_tags(content)
        if docstring:
            tags.append('documented')
        
        self.blocks.append(ParsedBlock(
            content=content,
            block_type='class',
            tags=tags,
            language='python',
            line_start=start,
            line_end=end,
            metadata={
                'name': node.name,
                'methods': methods,
                'docstring': docstring[:200] if docstring else None,
                'bases': [ast.unparse(b) for b in node.bases] if node.bases else []
            }
        ))
    
    # ==========================================
    # Markdown Parser
    # ==========================================
    
    def _parse_markdown(self, content: str):
        """Parse Markdown into headings, code blocks, and text."""
        lines = content.split('\n')
        current_block = []
        current_type = 'text'
        current_start = 1
        in_code_block = False
        code_lang = ''
        
        for i, line in enumerate(lines, 1):
            # Code block detection
            if line.strip().startswith('```'):
                if in_code_block:
                    # End code block
                    current_block.append(line)
                    self.blocks.append(ParsedBlock(
                        content='\n'.join(current_block),
                        block_type='code',
                        tags=self.extract_tags('\n'.join(current_block)) + ([code_lang] if code_lang else []),
                        language=code_lang or 'code',
                        line_start=current_start,
                        line_end=i
                    ))
                    current_block = []
                    current_type = 'text'
                    in_code_block = False
                    code_lang = ''
                else:
                    # Start code block - flush previous
                    if current_block:
                        self._flush_markdown_block(current_block, current_type, current_start, i-1)
                    current_block = [line]
                    current_start = i
                    in_code_block = True
                    code_lang = line.strip()[3:].strip()
                continue
            
            if in_code_block:
                current_block.append(line)
                continue
            
            # Heading detection
            if line.strip().startswith('#'):
                # Flush previous block
                if current_block:
                    self._flush_markdown_block(current_block, current_type, current_start, i-1)
                
                level = len(re.match(r'^#+', line.strip()).group())
                self.blocks.append(ParsedBlock(
                    content=line,
                    block_type='heading',
                    tags=self.extract_tags(line) + [f'h{level}'],
                    language='markdown',
                    line_start=i,
                    line_end=i,
                    metadata={'level': level}
                ))
                current_block = []
                current_start = i + 1
                continue
            
            # Task detection
            if re.match(r'^[\s]*[-*]\s*\[[x ]\]', line):
                if current_block:
                    self._flush_markdown_block(current_block, current_type, current_start, i-1)
                
                is_complete = '[x]' in line.lower()
                self.blocks.append(ParsedBlock(
                    content=line,
                    block_type='task',
                    tags=['complete' if is_complete else 'pending'] + self.extract_tags(line),
                    language='markdown',
                    line_start=i,
                    line_end=i,
                    metadata={'complete': is_complete}
                ))
                current_block = []
                current_start = i + 1
                continue
            
            current_block.append(line)
        
        # Flush remaining
        if current_block:
            self._flush_markdown_block(current_block, current_type, current_start, len(lines))
    
    def _flush_markdown_block(self, block: List[str], block_type: str, start: int, end: int):
        """Flush accumulated markdown block."""
        content = '\n'.join(block).strip()
        if not content:
            return
        
        self.blocks.append(ParsedBlock(
            content=content,
            block_type=block_type,
            tags=self.extract_tags(content),
            language='markdown',
            line_start=start,
            line_end=end
        ))
    
    # ==========================================
    # JavaScript/TypeScript Parser
    # ==========================================
    
    def _parse_javascript(self, content: str):
        """Parse JavaScript/TypeScript using regex patterns."""
        lines = content.split('\n')
        
        # Pattern for imports
        import_pattern = r'^import\s+.+?(?:from\s+[\'"].*?[\'"];?|;)\s*$'
        imports = []
        
        for i, line in enumerate(lines, 1):
            if re.match(import_pattern, line.strip()):
                imports.append((i, line.strip()))
        
        if imports:
            self.blocks.append(ParsedBlock(
                content='\n'.join([imp[1] for imp in imports]),
                block_type='import',
                tags=['import'],
                language='javascript',
                line_start=imports[0][0],
                line_end=imports[-1][0],
                metadata={'count': len(imports)}
            ))
        
        # Pattern for functions
        func_pattern = r'((?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{)'
        arrow_pattern = r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
        
        for match in re.finditer(func_pattern, content):
            name = match.group(2)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0) + ' ... }',
                block_type='function',
                tags=self.extract_tags(match.group(0)),
                language='javascript',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name}
            ))
        
        for match in re.finditer(arrow_pattern, content):
            name = match.group(1)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0),
                block_type='function',
                tags=['arrow'] + self.extract_tags(match.group(0)),
                language='javascript',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name}
            ))
    
    # ==========================================
    # Vue Parser
    # ==========================================
    
    def _parse_vue(self, content: str):
        """Parse Vue SFC into template, script, style blocks."""
        # Template block
        template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        if template_match:
            start = content[:template_match.start()].count('\n') + 1
            end = content[:template_match.end()].count('\n') + 1
            self.blocks.append(ParsedBlock(
                content=template_match.group(0),
                block_type='template',
                tags=['vue', 'html'] + self.extract_tags(template_match.group(1)),
                language='vue',
                line_start=start,
                line_end=end
            ))
        
        # Script block
        script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        if script_match:
            start = content[:script_match.start()].count('\n') + 1
            end = content[:script_match.end()].count('\n') + 1
            script_content = script_match.group(1)
            
            # Check for setup syntax
            is_setup = 'setup' in script_match.group(0)
            tags = ['vue', 'script']
            if is_setup:
                tags.append('composition-api')
            
            self.blocks.append(ParsedBlock(
                content=script_match.group(0),
                block_type='script',
                tags=tags + self.extract_tags(script_content),
                language='typescript' if 'lang="ts"' in script_match.group(0) else 'javascript',
                line_start=start,
                line_end=end
            ))
        
        # Style block
        style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
        if style_match:
            start = content[:style_match.start()].count('\n') + 1
            end = content[:style_match.end()].count('\n') + 1
            is_scoped = 'scoped' in style_match.group(0)
            
            self.blocks.append(ParsedBlock(
                content=style_match.group(0),
                block_type='style',
                tags=['vue', 'css'] + (['scoped'] if is_scoped else []),
                language='css',
                line_start=start,
                line_end=end
            ))
    
    # ==========================================
    # Generic Parser
    # ==========================================
    
    def _parse_generic(self, content: str, language: str):
        """Generic line-by-line parser for unknown formats."""
        lines = content.split('\n')
        current_block = []
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            # Detect comments
            if line.strip().startswith(('#', '//', '/*', '--', ';')):
                if current_block:
                    self._flush_generic_block(current_block, 'text', language, current_start, i-1)
                    current_block = []
                
                self.blocks.append(ParsedBlock(
                    content=line,
                    block_type='comment',
                    tags=self.extract_tags(line),
                    language=language,
                    line_start=i,
                    line_end=i
                ))
                current_start = i + 1
                continue
            
            current_block.append(line)
        
        if current_block:
            self._flush_generic_block(current_block, 'text', language, current_start, len(lines))
    
    def _flush_generic_block(self, block: List[str], block_type: str, language: str, start: int, end: int):
        """Flush generic block."""
        content = '\n'.join(block).strip()
        if not content:
            return
        
        self.blocks.append(ParsedBlock(
            content=content,
            block_type=block_type,
            tags=self.extract_tags(content),
            language=language,
            line_start=start,
            line_end=end
        ))

    # ==========================================
    # System Parser (C/C++/Rust/Make)
    # ==========================================
    
    def _parse_c_cpp(self, content: str, language: str):
        """Parse C/C++ for structs, functions, and macros."""
        lines = content.split('\n')
        
        # Includes
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#include'):
                self.blocks.append(ParsedBlock(
                    content=line.strip(),
                    block_type='import',
                    tags=['include', 'header'],
                    language=language,
                    line_start=i,
                    line_end=i,
                    metadata={'include': line.strip().split()[-1]}
                ))

        # Defines (Macros)
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#define'):
                parts = line.strip().split()
                name = parts[1] if len(parts) > 1 else 'unknown'
                self.blocks.append(ParsedBlock(
                    content=line.strip(),
                    block_type='macro',
                    tags=['macro'],
                    language=language,
                    line_start=i,
                    line_end=i,
                    metadata={'name': name}
                ))

        # Godot Signals (Scavenger Logic)
        signal_pattern = r'ADD_SIGNAL\(\s*MethodInfo\(\s*[\'"](\w+)[\'"]'
        for match in re.finditer(signal_pattern, content):
            name = match.group(1)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=f"SIGNAL: {name}",
                block_type='signal',
                tags=['godot', 'signal'],
                language=language,
                line_start=line_start,
                line_end=line_start,
                metadata={
                    'name': name,
                    'socket_type': 'SOCK_SIGNAL' # Compatible with our SignalBus
                }
            ))

        # FFmpeg Filter Pads (Scavenger Logic)
        pad_pattern = r'static\s+const\s+AVFilterPad\s+(\w+)\[\]\s*=\s*\{'
        for match in re.finditer(pad_pattern, content):
            name = match.group(1)
            is_input = 'inputs' in name.lower()
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=f"STREAM PAD: {name}",
                block_type='stream_pad',
                tags=['ffmpeg', 'pipeline', 'input' if is_input else 'output'],
                language=language,
                line_start=line_start,
                line_end=line_start,
                metadata={
                    'name': name,
                    'socket_type': 'SOCK_STREAM', # Compatible with our Pipeline
                    'direction': 'input' if is_input else 'output'
                }
            ))

        # Structs/Classes
        # struct Name { or class Name : public Base {
        struct_pattern = r'(struct|class)\s+(\w+)[^{]*\{'
        for match in re.finditer(struct_pattern, content):
            name = match.group(2)
            kind = match.group(1)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            # Find matching brace
            # Simple heuristic: look for next } at start of line
            # robust pairing is hard with regex, we assume standard formatting
            end_match = re.search(r'\n\}\s*;', content[start_pos:])
            line_end = line_start
            block_content = match.group(0) + " ... };"
            
            if end_match:
                end_pos = start_pos + end_match.end()
                line_end = content[:end_pos].count('\n') + 1
                block_content = content[start_pos:end_pos]
            
            # Scavenger: Look for Signals INSIDE the class
            sockets = []
            
            # Godot Signals
            signal_matches = re.finditer(r'ADD_SIGNAL\(\s*MethodInfo\(\s*[\'"](\w+)[\'"]', block_content)
            for sm in signal_matches:
                sockets.append({
                    'name': sm.group(1),
                    'inputs': [],
                    'output': 'void', # Signals don't return values usually
                    'socket_type': 'SOCK_SIGNAL'
                })
                
            self.blocks.append(ParsedBlock(
                content=block_content,
                block_type='struct' if kind == 'struct' else 'class',
                tags=[kind] + self.extract_tags(block_content),
                language=language,
                line_start=line_start,
                line_end=line_end,
                metadata={
                    'name': name,
                    'sockets': sockets
                }
            ))

        # Functions
        # void name(...) {
        # logic: start of line, return type, name, parens, brace
        func_pattern = r'^(\w[\w\s\*&]+)\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            ret_type = match.group(1).strip()
            name = match.group(2)
            
            # Filtering keywords
            if ret_type in ['if', 'while', 'for', 'switch', 'else']:
                continue
                
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0) + " ... }",
                block_type='function',
                tags=['function'] + self.extract_tags(match.group(0)),
                language=language,
                line_start=line_start,
                line_end=line_start,  # We don't trace end for perf/complexity
                metadata={'name': name, 'return_type': ret_type}
            ))

    def _parse_rust(self, content: str):
        """Parse Rust for fns, impls, structs, traits."""
        
        # Functions: fn name(...) -> ... {
        func_pattern = r'((?:pub\s+)?(?:unsafe\s+)?(?:async\s+)?fn\s+(\w+)\s*<.*?>?\s*\()'
        for match in re.finditer(func_pattern, content):
            name = match.group(2)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0) + "... {",
                block_type='function',
                tags=['rust', 'fn'] + self.extract_tags(match.group(0)),
                language='rust',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name}
            ))
            
        # Structs/Enums: struct Name {
        struct_pattern = r'((?:pub\s+)?(?:struct|enum|trait)\s+(\w+))'
        for match in re.finditer(struct_pattern, content):
            kind_name = match.group(1).split()
            kind = kind_name[-2] # pub struct -> struct
            if 'pub' in kind_name: kind = kind_name[-1] # fallback logic
            if kind in ['pub', 'unsafe']: kind = kind_name[-1]
            
            name = match.group(2)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0) + " { ... }",
                block_type='struct',
                tags=['rust', kind],
                language='rust',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name, 'kind': kind}
            ))
            
        # Impls: impl Name {
        impl_pattern = r'impl(?:<.+?>)?\s+(\w+)'
        for match in re.finditer(impl_pattern, content):
            name = match.group(1)
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0) + " { ... }",
                block_type='impl',
                tags=['rust', 'impl'],
                language='rust',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name}
            ))

    def _parse_makefile(self, content: str):
        """Parse Makefile targets."""
        # target: deps
        target_pattern = r'^([\w\-\./]+):'
        for match in re.finditer(target_pattern, content, re.MULTILINE):
            name = match.group(1)
            if name == '.PHONY': continue
            
            start_pos = match.start()
            line_start = content[:start_pos].count('\n') + 1
            
            self.blocks.append(ParsedBlock(
                content=match.group(0),
                block_type='target',
                tags=['make', 'target'],
                language='makefile',
                line_start=line_start,
                line_end=line_start,
                metadata={'name': name}
            ))


# Singleton instance
_parser: Optional[UniversalParser] = None

def get_parser() -> UniversalParser:
    global _parser
    if _parser is None:
        _parser = UniversalParser()
    return _parser
