#!/usr/bin/env python3
"""
Extract architecture spec from a Python codebase.
Outputs: Mermaid diagrams, module overview, class/function summaries, and a high-level SPEC.md.
"""
import ast
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class FunctionInfo:
    name: str
    docstring: Optional[str]
    args: List[str]
    returns: Optional[str]
    decorators: List[str]
    lineno: int


@dataclass
class ClassInfo:
    name: str
    docstring: Optional[str]
    bases: List[str]
    methods: List[FunctionInfo]
    attributes: List[str]
    decorators: List[str]
    lineno: int


@dataclass
class ModuleInfo:
    path: str
    docstring: Optional[str]
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    constants: List[str]


@dataclass
class PackageInfo:
    name: str
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    subpackages: Dict[str, "PackageInfo"] = field(default_factory=dict)


def extract_function(node: ast.FunctionDef) -> FunctionInfo:
    """Extract function information from AST node."""
    args = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"
        args.append(arg_str)
    
    returns = None
    if node.returns:
        returns = ast.unparse(node.returns)
    
    decorators = [ast.unparse(d) for d in node.decorator_list]
    
    return FunctionInfo(
        name=node.name,
        docstring=ast.get_docstring(node),
        args=args,
        returns=returns,
        decorators=decorators,
        lineno=node.lineno,
    )


def extract_class(node: ast.ClassDef) -> ClassInfo:
    """Extract class information from AST node."""
    bases = [ast.unparse(b) for b in node.bases]
    methods = []
    attributes = []
    
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(extract_function(item))
        elif isinstance(item, ast.AnnAssign) and item.target:
            attr = ast.unparse(item.target)
            if item.annotation:
                attr += f": {ast.unparse(item.annotation)}"
            attributes.append(attr)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attributes.append(target.id)
    
    decorators = [ast.unparse(d) for d in node.decorator_list]
    
    return ClassInfo(
        name=node.name,
        docstring=ast.get_docstring(node),
        bases=bases,
        methods=methods,
        attributes=attributes,
        decorators=decorators,
        lineno=node.lineno,
    )


def extract_module(file_path: Path) -> Optional[ModuleInfo]:
    """Extract module information from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return None
    
    imports = []
    classes = []
    functions = []
    constants = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
        elif isinstance(node, ast.ClassDef):
            classes.append(extract_class(node))
        elif isinstance(node, ast.FunctionDef):
            functions.append(extract_function(node))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
    
    return ModuleInfo(
        path=str(file_path),
        docstring=ast.get_docstring(tree),
        imports=imports,
        classes=classes,
        functions=functions,
        constants=constants,
    )


def scan_package(pkg_path: Path, pkg_name: str) -> PackageInfo:
    """Recursively scan a Python package."""
    pkg = PackageInfo(name=pkg_name)
    
    for item in sorted(pkg_path.iterdir()):
        if item.name.startswith((".", "__pycache__")):
            continue
        
        if item.is_file() and item.suffix == ".py":
            mod_name = item.stem
            mod_info = extract_module(item)
            if mod_info:
                pkg.modules[mod_name] = mod_info
        elif item.is_dir() and (item / "__init__.py").exists():
            subpkg = scan_package(item, item.name)
            pkg.subpackages[item.name] = subpkg
    
    return pkg


def generate_mermaid_class_diagram(pkg: PackageInfo, prefix: str = "") -> List[str]:
    """Generate Mermaid class diagram syntax."""
    lines = []
    
    for mod_name, mod_info in pkg.modules.items():
        for cls in mod_info.classes:
            full_name = f"{prefix}{mod_name}_{cls.name}" if prefix else f"{mod_name}_{cls.name}"
            safe_name = full_name.replace(".", "_")
            
            lines.append(f"    class {safe_name} {{")
            for attr in cls.attributes[:5]:  # Limit attributes
                safe_attr = attr.replace("<", "~").replace(">", "~").replace('"', "'")
                lines.append(f"        +{safe_attr}")
            for method in cls.methods[:10]:  # Limit methods
                args_str = ", ".join(a.split(":")[0] for a in method.args[:3])
                ret = f" {method.returns}" if method.returns else ""
                lines.append(f"        +{method.name}({args_str}){ret}")
            lines.append("    }")
            
            # Add inheritance
            for base in cls.bases:
                if base not in ("object", "ABC"):
                    safe_base = base.replace(".", "_")
                    lines.append(f"    {safe_base} <|-- {safe_name}")
    
    for subpkg_name, subpkg in pkg.subpackages.items():
        sub_prefix = f"{prefix}{subpkg_name}_" if prefix else f"{subpkg_name}_"
        lines.extend(generate_mermaid_class_diagram(subpkg, sub_prefix))
    
    return lines


def generate_mermaid_module_diagram(pkg: PackageInfo, indent: int = 0) -> List[str]:
    """Generate Mermaid flowchart for module structure."""
    lines = []
    ind = "    " * indent
    
    for mod_name, mod_info in pkg.modules.items():
        classes_str = ", ".join(c.name for c in mod_info.classes[:3])
        funcs_str = ", ".join(f.name for f in mod_info.functions[:3])
        label_parts = []
        if classes_str:
            label_parts.append(f"Classes: {classes_str}")
        if funcs_str:
            label_parts.append(f"Funcs: {funcs_str}")
        label = "<br>".join(label_parts) if label_parts else mod_name
        lines.append(f'{ind}{mod_name}["{mod_name}<br>{label}"]')
    
    for subpkg_name, subpkg in pkg.subpackages.items():
        lines.append(f"{ind}subgraph {subpkg_name}")
        lines.extend(generate_mermaid_module_diagram(subpkg, indent + 1))
        lines.append(f"{ind}end")
    
    return lines


def generate_dependency_diagram(pkg: PackageInfo, root_name: str) -> List[str]:
    """Generate Mermaid flowchart for internal dependencies."""
    lines = []
    all_imports: Dict[str, Set[str]] = {}
    
    def collect_imports(p: PackageInfo, prefix: str):
        for mod_name, mod_info in p.modules.items():
            full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
            internal_imports = set()
            for imp in mod_info.imports:
                if imp.startswith(root_name):
                    # Simplify to module level
                    parts = imp.split(".")
                    if len(parts) >= 2:
                        internal_imports.add(".".join(parts[:3]))
            all_imports[full_mod] = internal_imports
        
        for subpkg_name, subpkg in p.subpackages.items():
            sub_prefix = f"{prefix}.{subpkg_name}" if prefix else subpkg_name
            collect_imports(subpkg, sub_prefix)
    
    collect_imports(pkg, root_name)
    
    # Generate edges
    for mod, imports in all_imports.items():
        mod_safe = mod.replace(".", "_")
        lines.append(f"    {mod_safe}[{mod}]")
        for imp in imports:
            if imp != mod and imp in all_imports:
                imp_safe = imp.replace(".", "_")
                lines.append(f"    {mod_safe} --> {imp_safe}")
    
    return lines


def generate_spec_md(pkg: PackageInfo, root_name: str, output_dir: Path) -> str:
    """Generate SPEC.md high-level architecture document."""
    lines = [
        f"# {root_name.upper()} Architecture Specification",
        "",
        "## Overview",
        "",
        f"This document describes the high-level architecture of the `{root_name}` package.",
        "",
        "## Package Structure",
        "",
        "```",
    ]
    
    def print_tree(p: PackageInfo, indent: str = ""):
        for mod_name, mod_info in sorted(p.modules.items()):
            classes = [c.name for c in mod_info.classes]
            lines.append(f"{indent}{mod_name}.py  # {', '.join(classes) if classes else 'utilities'}")
        for subpkg_name, subpkg in sorted(p.subpackages.items()):
            lines.append(f"{indent}{subpkg_name}/")
            print_tree(subpkg, indent + "  ")
    
    print_tree(pkg)
    lines.append("```")
    lines.append("")
    
    # Collect all classes and their docs
    all_classes: List[Tuple[str, ClassInfo]] = []
    
    def collect_classes(p: PackageInfo, prefix: str):
        for mod_name, mod_info in p.modules.items():
            for cls in mod_info.classes:
                path = f"{prefix}.{mod_name}" if prefix else mod_name
                all_classes.append((path, cls))
        for subpkg_name, subpkg in p.subpackages.items():
            sub_prefix = f"{prefix}.{subpkg_name}" if prefix else subpkg_name
            collect_classes(subpkg, sub_prefix)
    
    collect_classes(pkg, root_name)
    
    lines.append("## Core Components")
    lines.append("")
    
    for path, cls in all_classes:
        lines.append(f"### `{cls.name}` ({path})")
        lines.append("")
        if cls.docstring:
            lines.append(cls.docstring.split("\n")[0])
        if cls.bases:
            lines.append(f"- **Inherits**: {', '.join(cls.bases)}")
        if cls.decorators:
            lines.append(f"- **Decorators**: {', '.join(cls.decorators)}")
        
        public_methods = [m for m in cls.methods if not m.name.startswith("_")]
        if public_methods:
            lines.append("- **Key Methods**:")
            for m in public_methods[:5]:
                doc = m.docstring.split("\n")[0] if m.docstring else ""
                lines.append(f"  - `{m.name}()`: {doc}")
        lines.append("")
    
    # Module docstrings
    lines.append("## Module Documentation")
    lines.append("")
    
    def collect_module_docs(p: PackageInfo, prefix: str):
        for mod_name, mod_info in p.modules.items():
            if mod_info.docstring:
                path = f"{prefix}.{mod_name}" if prefix else mod_name
                lines.append(f"### {path}")
                lines.append("")
                lines.append(mod_info.docstring.split("\n\n")[0])
                lines.append("")
        for subpkg_name, subpkg in p.subpackages.items():
            sub_prefix = f"{prefix}.{subpkg_name}" if prefix else subpkg_name
            collect_module_docs(subpkg, sub_prefix)
    
    collect_module_docs(pkg, root_name)
    
    lines.append("## Diagrams")
    lines.append("")
    lines.append("See accompanying diagram files:")
    lines.append("- `module_structure.mmd` - Package/module hierarchy")
    lines.append("- `class_diagram.mmd` - Class relationships")
    lines.append("- `dependencies.mmd` - Internal import dependencies")
    lines.append("- `dependency_graph.svg` - Visual dependency graph (pydeps)")
    lines.append("")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_architecture.py <package_path> <output_dir>")
        sys.exit(1)
    
    pkg_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pkg_name = pkg_path.name
    print(f"Scanning package: {pkg_name} at {pkg_path}")
    
    pkg = scan_package(pkg_path, pkg_name)
    
    # Generate module structure diagram
    module_lines = ["flowchart TB"]
    module_lines.extend(generate_mermaid_module_diagram(pkg))
    (output_dir / "module_structure.mmd").write_text("\n".join(module_lines))
    print(f"Generated: {output_dir / 'module_structure.mmd'}")
    
    # Generate class diagram
    class_lines = ["classDiagram"]
    class_lines.extend(generate_mermaid_class_diagram(pkg))
    (output_dir / "class_diagram.mmd").write_text("\n".join(class_lines))
    print(f"Generated: {output_dir / 'class_diagram.mmd'}")
    
    # Generate dependency diagram
    dep_lines = ["flowchart LR"]
    dep_lines.extend(generate_dependency_diagram(pkg, pkg_name))
    (output_dir / "dependencies.mmd").write_text("\n".join(dep_lines))
    print(f"Generated: {output_dir / 'dependencies.mmd'}")
    
    # Generate SPEC.md
    spec_content = generate_spec_md(pkg, pkg_name, output_dir)
    (output_dir / "SPEC.md").write_text(spec_content)
    print(f"Generated: {output_dir / 'SPEC.md'}")
    
    print(f"\nAll outputs written to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()

