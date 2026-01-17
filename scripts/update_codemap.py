"""
update_codemap.py — Automatic CODE_MAP generation with Call Graph Analysis
---------------------------------------------------------------------------
Scans all Python modules in scanner/ directory and generates an updated
docs/code_map.md with:
- Module structure (classes, functions, imports)
- Call dependencies (which function calls which)
- Internal vs. external call analysis
- Dependency statistics for refactoring insights
"""

import ast
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
SRC_DIR = Path("scanner")
DOC_PATH = Path("docs/code_map.md")

# Builtins to filter out from call graph
BUILTIN_FUNCS = {
    "len", "print", "range", "type", "str", "int", "float", "list",
    "dict", "set", "tuple", "max", "min", "sum", "any", "all", "zip",
    "map", "filter", "sorted", "enumerate", "open", "isinstance",
    "hasattr", "getattr", "setattr", "abs", "round", "next", "iter",
    "bool", "bytes", "format", "hash", "help", "id", "input", "ord",
    "chr", "repr", "reversed", "slice", "staticmethod", "classmethod",
    "property", "super", "vars", "dir", "locals", "globals"
}

# External libraries to recognize
EXTERNAL_LIBS = {
    "pd", "np", "requests", "yaml", "json", "os", "sys", "Path",
    "datetime", "time", "logging", "Logger"
}


def generate_header():
    """Generate document header with metadata."""
    return f"""# 📘 Code Map — Automatically Generated

**Repository:** schluchtenscheisser/spot-altcoin-scanner  
**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  
**Generator:** scripts/update_codemap.py

---

## 📋 Overview

This Code Map provides a comprehensive structural overview of the Spot Altcoin Scanner codebase, including:
- Module structure (classes, functions, variables)
- Import dependencies
- **Call Graph Analysis** (function dependencies)
- Coupling statistics (internal vs. external calls)

---

"""


def extract_module_info(file_path: Path):
    """
    Analyze a Python module with AST and extract:
    - Functions, classes, imports, variables
    - Call relationships (which function calls which)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        print(f"⚠️  Failed to parse {file_path}: {e}")
        return None

    functions = []
    classes = []
    imports = []
    variables = []
    calls = defaultdict(set)
    current_function = None

    class CallVisitor(ast.NodeVisitor):
        """AST Visitor that detects function calls within other functions."""
        
        def visit_FunctionDef(self, node):
            nonlocal current_function
            prev = current_function
            current_function = node.name
            self.generic_visit(node)
            current_function = prev

        def visit_Call(self, node):
            if current_function:
                func_name = None
                
                # Direct function call: func()
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                
                # Method call: obj.method()
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                # Filter out builtins and add to call graph
                if func_name and func_name not in BUILTIN_FUNCS:
                    calls[current_function].add(func_name)
            
            self.generic_visit(node)

    # Visit the AST
    CallVisitor().visit(tree)

    # Extract top-level definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        
        elif isinstance(node, ast.Import):
            imports.extend([n.name for n in node.names])
        
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    variables.append(target.id)

    return {
        "functions": sorted(set(functions)),
        "classes": sorted(set(classes)),
        "imports": sorted(set(imports)),
        "variables": sorted(set(variables)),
        "calls": {k: sorted(v) for k, v in calls.items()},
    }


def scan_repository():
    """Scan all Python files in scanner/ and collect metadata."""
    modules = {}
    
    print(f"🔍 Scanning {SRC_DIR}/ for Python modules...")
    
    for py_file in SRC_DIR.rglob("*.py"):
        rel_path = py_file.relative_to(Path.cwd())
        info = extract_module_info(py_file)
        
        if info:
            modules[str(rel_path)] = info
            print(f"  ✓ {rel_path}")
    
    print(f"📊 Found {len(modules)} modules")
    return modules


def build_codemap(modules):
    """Build the complete Markdown documentation with call graph."""
    lines = [generate_header()]
    
    # Statistics
    total_modules = len(modules)
    total_classes = sum(len(m["classes"]) for m in modules.values())
    total_functions = sum(len(m["functions"]) for m in modules.values())
    
    lines.append("## 📊 Repository Statistics\n\n")
    lines.append(f"- **Total Modules:** {total_modules}\n")
    lines.append(f"- **Total Classes:** {total_classes}\n")
    lines.append(f"- **Total Functions:** {total_functions}\n")
    lines.append("\n---\n\n")
    
    # Module Overview
    lines.append("## 🧩 Module Structure\n\n")
    
    for module_path, info in sorted(modules.items()):
        lines.append(f"### 📄 `{module_path}`\n\n")
        
        if info["classes"]:
            lines.append(f"**Classes:** `{', '.join(info['classes'])}`\n\n")
        
        if info["functions"]:
            lines.append(f"**Functions:** `{', '.join(info['functions'])}`\n\n")
        else:
            lines.append("**Functions:** —\n\n")
        
        if info["variables"]:
            lines.append(f"**Module Variables:** `{', '.join(info['variables'][:10])}`")
            if len(info["variables"]) > 10:
                lines.append(f" _(+{len(info['variables'])-10} more)_")
            lines.append("\n\n")
        
        if info["imports"]:
            lines.append(f"**Imports:** `{', '.join(info['imports'][:8])}`")
            if len(info["imports"]) > 8:
                lines.append(f" _(+{len(info['imports'])-8} more)_")
            lines.append("\n\n")
        
        lines.append("---\n\n")
    
    # Call Graph Analysis
    lines.append("\n## 🔗 Function Dependencies (Call Graph)\n\n")
    lines.append("_This section shows which functions call which other functions, ")
    lines.append("helping identify coupling and refactoring opportunities._\n\n")
    
    stats = {}  # Module -> (internal_calls, external_calls)
    has_any_calls = False
    
    for module_path, info in sorted(modules.items()):
        if any(info["calls"].values()):
            has_any_calls = True
            
            lines.append(f"### 📄 {module_path}\n\n")
            lines.append("| Calling Function | Internal Calls | External Calls |\n")
            lines.append("|------------------|----------------|----------------|\n")
            
            # Get all functions defined in this module
            func_set = set(info["functions"])
            internal_total = 0
            external_total = 0
            
            for func, called_funcs in sorted(info["calls"].items()):
                if called_funcs:
                    # Separate internal (same module) from external calls
                    internal = sorted([c for c in called_funcs if c in func_set])
                    external = sorted([c for c in called_funcs if c not in func_set])
                    
                    internal_total += len(internal)
                    external_total += len(external)
                    
                    internal_str = ", ".join(f"`{c}`" for c in internal) if internal else "—"
                    external_str = ", ".join(f"`{c}`" for c in external) if external else "—"
                    
                    lines.append(f"| `{func}` | {internal_str} | {external_str} |\n")
            
            lines.append("\n")
            stats[module_path] = (internal_total, external_total)
    
    if not has_any_calls:
        lines.append("_No function calls detected across modules._\n\n")
    
    # Dependency Statistics
    if stats:
        lines.append("\n---\n\n")
        lines.append("## 📊 Coupling Statistics\n\n")
        lines.append("_Modules with high external call counts may benefit from refactoring._\n\n")
        lines.append("| Module | Internal Calls | External Calls | Total | Coupling |\n")
        lines.append("|--------|----------------|----------------|-------|----------|\n")
        
        for module_path, (internal, external) in sorted(
            stats.items(), 
            key=lambda x: (x[1][1] + x[1][0]), 
            reverse=True
        ):
            total = internal + external
            
            # Calculate coupling indicator
            if total == 0:
                coupling = "—"
            elif external == 0:
                coupling = "✅ Low"
            elif external / total < 0.3:
                coupling = "✅ Low"
            elif external / total < 0.6:
                coupling = "⚠️ Medium"
            else:
                coupling = "🔴 High"
            
            lines.append(f"| `{module_path}` | {internal} | {external} | {total} | {coupling} |\n")
        
        lines.append("\n**Interpretation:**\n")
        lines.append("- ✅ **Low coupling:** Module is self-contained, easy to maintain\n")
        lines.append("- ⚠️ **Medium coupling:** Some external dependencies, acceptable\n")
        lines.append("- 🔴 **High coupling:** Many external calls, consider refactoring\n\n")
    
    # Footer
    lines.append("\n---\n\n")
    lines.append("## 📚 Additional Documentation\n\n")
    lines.append("- **Specifications:** `docs/spec.md` (technical master spec)\n")
    lines.append("- **Development Guide:** `docs/dev_guide.md` (workflow)\n")
    lines.append("- **GPT Snapshot:** `docs/GPT_SNAPSHOT.md` (complete codebase)\n")
    lines.append("- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily outputs)\n\n")
    lines.append("---\n\n")
    lines.append(f"_Generated by GitHub Actions • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_\n")
    
    return "".join(lines)


def write_codemap(content: str):
    """Write the generated documentation to docs/code_map.md."""
    DOC_PATH.parent.mkdir(exist_ok=True)
    
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Code Map written to: {DOC_PATH.resolve()}")
    print(f"   Size: {len(content)} characters")


def main():
    """Main entry point."""
    print("=" * 70)
    print("🗺️  Code Map Generator — Call Graph Analysis")
    print("=" * 70)
    print()
    
    modules = scan_repository()
    
    if not modules:
        print("❌ No modules found!")
        return 1
    
    print()
    print("📝 Building Code Map with call graph analysis...")
    content = build_codemap(modules)
    
    print()
    write_codemap(content)
    
    print()
    print("✅ Done! Code Map now includes:")
    print("   • Module structure")
    print("   • Function dependencies (call graph)")
    print("   • Coupling statistics")
    print()
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())
