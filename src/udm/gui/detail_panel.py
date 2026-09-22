"""Right-side detail panel — shows selected package info, metadata, and install button."""

from pathlib import Path
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from udm.config import resource_path
from udm.constants import LOGO_FILENAME
from udm.gui.icon_provider import get_tool_icon_pixmap
from udm.gui.theme import (
    BORDER, FG, FG_DIM, FG_MUTED,
)
from udm.gui.widgets import ActionButton

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

CATEGORY_BADGE_COLORS = {
    "Languages": ("#818cf8", "rgba(99, 102, 241, 0.22)"),
    "Compilers": ("#4ade80", "rgba(74, 222, 128, 0.20)"),
    "SDKs & Frameworks": ("#c084fc", "rgba(192, 132, 252, 0.20)"),
    "Databases": ("#22d3ee", "rgba(34, 211, 238, 0.20)"),
    "DevOps Tools": ("#38bdf8", "rgba(56, 189, 248, 0.20)"),
    "DevOps & Tools": ("#38bdf8", "rgba(56, 189, 248, 0.20)"),
    "Package Managers": ("#fb923c", "rgba(234, 88, 12, 0.20)"),
    "IDEs & Editors": ("#34d399", "rgba(52, 211, 153, 0.20)"),
    "Cloud CLIs": ("#93c5fd", "rgba(147, 197, 253, 0.20)"),
    "Mobile Development": ("#f87171", "rgba(248, 113, 113, 0.20)"),
    "Data Science": ("#f472b6", "rgba(244, 114, 182, 0.20)"),
    "AI / Data Science": ("#f472b6", "rgba(244, 114, 182, 0.20)"),
}

TOOL_META = {
    # ── Languages ──
    "python": {
        "version": "3.12.5",
        "size": "≈ 25 MB",
        "license": "PSF License",
        "website": "https://www.python.org",
        "docs": "https://docs.python.org/3",
        "source": "https://github.com/python/cpython",
        "description": "Python is a versatile, high-level programming language celebrated for its readable syntax, rich standard library, and ubiquitous presence in web, AI, data science, and automation.",
    },
    "python311": {
        "version": "3.11.9",
        "size": "≈ 25 MB",
        "license": "PSF License",
        "website": "https://www.python.org",
        "docs": "https://docs.python.org/3.11",
        "source": "https://github.com/python/cpython",
        "description": "Python 3.11 features significant performance optimizations, enhanced error tracebacks, and comprehensive library support.",
    },
    "nodejs": {
        "version": "20.17.0 (LTS)",
        "size": "≈ 30 MB",
        "license": "MIT",
        "website": "https://nodejs.org",
        "docs": "https://nodejs.org/docs",
        "source": "https://github.com/nodejs/node",
        "description": "Node.js is an open-source, cross-platform JavaScript runtime environment built on Chrome's V8 engine for building fast, scalable network applications.",
    },
    "typescript": {
        "version": "5.5.4",
        "size": "≈ 12 MB",
        "license": "Apache-2.0",
        "website": "https://www.typescriptlang.org",
        "docs": "https://www.typescriptlang.org/docs",
        "source": "https://github.com/microsoft/TypeScript",
        "description": "TypeScript is a strongly typed programming language that builds on JavaScript, giving you better tooling and static type safety at any scale.",
    },
    "rust": {
        "version": "1.81.0",
        "size": "≈ 250 MB",
        "license": "MIT / Apache-2.0",
        "website": "https://www.rust-lang.org",
        "docs": "https://doc.rust-lang.org",
        "source": "https://github.com/rust-lang/rust",
        "description": "Rust empowers everyone to build reliable and efficient software with fearless concurrency and memory safety without a garbage collector.",
    },
    "go": {
        "version": "1.23.1",
        "size": "≈ 65 MB",
        "license": "BSD-3-Clause",
        "website": "https://go.dev",
        "docs": "https://go.dev/doc",
        "source": "https://github.com/golang/go",
        "description": "Go is an open-source programming language supported by Google that makes it easy to build simple, secure, and highly scalable cloud software.",
    },
    "java": {
        "version": "21.0.4 (LTS)",
        "size": "≈ 190 MB",
        "license": "GPL-2.0 with Classpath Exception",
        "website": "https://adoptium.net",
        "docs": "https://docs.oracle.com/en/java",
        "source": "https://github.com/openjdk/jdk",
        "description": "Java is a popular, class-based, object-oriented language designed for cross-platform reliability, enterprise backend systems, and Android development.",
    },
    "java17": {
        "version": "17.0.12 (LTS)",
        "size": "≈ 180 MB",
        "license": "GPL-2.0 with Classpath Exception",
        "website": "https://adoptium.net",
        "docs": "https://docs.oracle.com/en/java/javase/17",
        "source": "https://github.com/openjdk/jdk",
        "description": "OpenJDK 17 LTS provides long-term stability and rock-solid backwards compatibility for production workloads.",
    },
    "csharp": {
        "version": "8.0.401 (.NET 8)",
        "size": "≈ 220 MB",
        "license": "MIT",
        "website": "https://dotnet.microsoft.com",
        "docs": "https://learn.microsoft.com/dotnet/csharp",
        "source": "https://github.com/dotnet/roslyn",
        "description": "C# is a modern, innovative, open-source, object-oriented language for building enterprise apps, games, cloud services, and cross-platform desktop software.",
    },
    "fsharp": {
        "version": "8.0 (.NET 8)",
        "size": "≈ 220 MB",
        "license": "MIT",
        "website": "https://fsharp.org",
        "docs": "https://learn.microsoft.com/dotnet/fsharp",
        "source": "https://github.com/dotnet/fsharp",
        "description": "F# is a functional-first, general-purpose programming language for writing succinct, robust, and performant code on the .NET platform.",
    },
    "kotlin": {
        "version": "2.0.20",
        "size": "≈ 80 MB",
        "license": "Apache-2.0",
        "website": "https://kotlinlang.org",
        "docs": "https://kotlinlang.org/docs",
        "source": "https://github.com/JetBrains/kotlin",
        "description": "Kotlin is a modern concise, safe, and fully Java-interoperable programming language widely endorsed for Android and multiplatform development.",
    },
    "scala": {
        "version": "3.5.0",
        "size": "≈ 45 MB",
        "license": "Apache-2.0",
        "website": "https://www.scala-lang.org",
        "docs": "https://docs.scala-lang.org",
        "source": "https://github.com/scala/scala3",
        "description": "Scala combines object-oriented and functional programming in one concise, high-level language with advanced type system features.",
    },
    "groovy": {
        "version": "4.0.22",
        "size": "≈ 35 MB",
        "license": "Apache-2.0",
        "website": "https://groovy-lang.org",
        "docs": "https://groovy-lang.org/documentation.html",
        "source": "https://github.com/apache/groovy",
        "description": "Apache Groovy is an agile and dynamic language for the Java Virtual Machine that seamlessly integrates with existing Java code.",
    },
    "clojure": {
        "version": "1.12.0",
        "size": "≈ 15 MB",
        "license": "EPL-1.0",
        "website": "https://clojure.org",
        "docs": "https://clojure.org/reference/documentation",
        "source": "https://github.com/clojure/clojure",
        "description": "Clojure is a dynamic, general-purpose programming language combining the approachability and interactive development of a Lisp with the robust JVM infrastructure.",
    },
    "dart": {
        "version": "3.5.2",
        "size": "≈ 210 MB",
        "license": "BSD-3-Clause",
        "website": "https://dart.dev",
        "docs": "https://dart.dev/guides",
        "source": "https://github.com/dart-lang/sdk",
        "description": "Dart is a client-optimized language for fast apps on any platform, powering Flutter multi-platform apps for mobile, web, and desktop.",
    },
    "swift": {
        "version": "6.0",
        "size": "≈ 450 MB",
        "license": "Apache-2.0",
        "website": "https://www.swift.org",
        "docs": "https://www.swift.org/documentation",
        "source": "https://github.com/swiftlang/swift",
        "description": "Swift is a general-purpose, fast, and safe programming language developed by Apple and open source contributors for iOS, macOS, servers, and beyond.",
    },
    "ruby": {
        "version": "3.3.4",
        "size": "≈ 35 MB",
        "license": "Ruby / BSD-2-Clause",
        "website": "https://www.ruby-lang.org",
        "docs": "https://ruby-doc.org",
        "source": "https://github.com/ruby/ruby",
        "description": "Ruby is a dynamic, open-source programming language with a focus on simplicity and productivity, featuring an elegant syntax that feels natural to read.",
    },
    "php": {
        "version": "8.3.11",
        "size": "≈ 30 MB",
        "license": "PHP-3.01",
        "website": "https://www.php.net",
        "docs": "https://www.php.net/docs.php",
        "source": "https://github.com/php/php-src",
        "description": "PHP is a popular general-purpose scripting language that is especially suited to web development and powers the majority of global web servers.",
    },
    "perl": {
        "version": "5.38.2",
        "size": "≈ 40 MB",
        "license": "Artistic-1.0 / GPL-1.0+",
        "website": "https://www.perl.org",
        "docs": "https://perldoc.perl.org",
        "source": "https://github.com/Perl/perl5",
        "description": "Perl is a highly capable, feature-rich programming language with over 35 years of development, renowned for text manipulation and sysadmin tooling.",
    },
    "lua": {
        "version": "5.4.6",
        "size": "≈ 2 MB",
        "license": "MIT",
        "website": "https://www.lua.org",
        "docs": "https://www.lua.org/docs.html",
        "source": "https://github.com/lua/lua",
        "description": "Lua is a powerful, efficient, lightweight, embeddable scripting language widely adopted in gaming engines, embedded devices, and extensible software.",
    },
    "luajit": {
        "version": "2.1.0",
        "size": "≈ 3 MB",
        "license": "MIT",
        "website": "https://luajit.org",
        "docs": "https://luajit.org",
        "source": "https://github.com/LuaJIT/LuaJIT",
        "description": "LuaJIT is a Just-In-Time Compiler for the Lua programming language, offering blistering performance on x86, ARM, and other architectures.",
    },
    "julia": {
        "version": "1.10.5",
        "size": "≈ 110 MB",
        "license": "MIT",
        "website": "https://julialang.org",
        "docs": "https://docs.julialang.org",
        "source": "https://github.com/JuliaLang/julia",
        "description": "Julia is a high-level, high-performance programming language for technical computing, with syntax familiar to users of other technical computing environments.",
    },
    "r": {
        "version": "4.4.1",
        "size": "≈ 85 MB",
        "license": "GPL-2.0 / GPL-3.0",
        "website": "https://www.r-project.org",
        "docs": "https://cran.r-project.org/manuals.html",
        "source": "https://github.com/wch/r-source",
        "description": "R is a free software environment for statistical computing and graphics, providing a wide variety of statistical and graphical techniques.",
    },
    "haskell": {
        "version": "9.6.6 (GHC)",
        "size": "≈ 350 MB",
        "license": "BSD-3-Clause",
        "website": "https://www.haskell.org",
        "docs": "https://www.haskell.org/documentation",
        "source": "https://gitlab.haskell.org/ghc/ghc",
        "description": "Haskell is an advanced, purely functional programming language featuring static typing, higher-order functions, laziness, and algebraic data types.",
    },
    "ocaml": {
        "version": "5.2.0",
        "size": "≈ 80 MB",
        "license": "LGPL-2.1",
        "website": "https://ocaml.org",
        "docs": "https://ocaml.org/docs",
        "source": "https://github.com/ocaml/ocaml",
        "description": "OCaml is an industrial-strength functional programming language with an emphasis on expressiveness, safety, and compiled native execution speed.",
    },
    "erlang": {
        "version": "27.0",
        "size": "≈ 120 MB",
        "license": "Apache-2.0",
        "website": "https://www.erlang.org",
        "docs": "https://www.erlang.org/docs",
        "source": "https://github.com/erlang/otp",
        "description": "Erlang is a programming language used to build massively scalable soft real-time systems with requirements on high availability.",
    },
    "elixir": {
        "version": "1.17.2",
        "size": "≈ 15 MB",
        "license": "Apache-2.0",
        "website": "https://elixir-lang.org",
        "docs": "https://hexdocs.pm/elixir",
        "source": "https://github.com/elixir-lang/elixir",
        "description": "Elixir is a dynamic, functional language designed for building scalable and maintainable applications running on the battle-tested Erlang BEAM VM.",
    },
    "zig": {
        "version": "0.13.0",
        "size": "≈ 45 MB",
        "license": "MIT",
        "website": "https://ziglang.org",
        "docs": "https://ziglang.org/documentation",
        "source": "https://github.com/ziglang/zig",
        "description": "Zig is a general-purpose programming language and toolchain for maintaining robust, optimal and reusable software without hidden control flow or macros.",
    },
    "nim": {
        "version": "2.0.8",
        "size": "≈ 65 MB",
        "license": "MIT",
        "website": "https://nim-lang.org",
        "docs": "https://nim-lang.org/documentation.html",
        "source": "https://github.com/nim-lang/Nim",
        "description": "Nim is a statically typed, compiled systems programming language that combines successful concepts from mature languages like Python, Ada, and Modula.",
    },
    "crystal": {
        "version": "1.13.1",
        "size": "≈ 60 MB",
        "license": "Apache-2.0",
        "website": "https://crystal-lang.org",
        "docs": "https://crystal-lang.org/reference",
        "source": "https://github.com/crystal-lang/crystal",
        "description": "Crystal has syntax inspired by Ruby, but compiles directly to efficient native code with static type checking.",
    },
    "vlang": {
        "version": "0.4.7",
        "size": "≈ 25 MB",
        "license": "MIT",
        "website": "https://vlang.io",
        "docs": "https://docs.vlang.io",
        "source": "https://github.com/vlang/v",
        "description": "V is a simple, fast, safe, compiled language for developing maintainable software with zero dependencies and lightning-fast compilation.",
    },
    "d_lang": {
        "version": "2.109.1",
        "size": "≈ 95 MB",
        "license": "BSL-1.0",
        "website": "https://dlang.org",
        "docs": "https://dlang.org/spec/spec.html",
        "source": "https://github.com/dlang/dmd",
        "description": "D is a general-purpose programming language with static typing, systems-level access, and C-like syntax combined with modern productivity features.",
    },
    "odin": {
        "version": "dev-2024-08",
        "size": "≈ 50 MB",
        "license": "BSD-3-Clause",
        "website": "https://odin-lang.org",
        "docs": "https://odin-lang.org/docs",
        "source": "https://github.com/odin-lang/Odin",
        "description": "Odin is a general-purpose, fast systems programming language designed for high performance, modern architectures, and joy of coding.",
    },
    "deno": {
        "version": "1.46.2",
        "size": "≈ 35 MB",
        "license": "MIT",
        "website": "https://deno.com",
        "docs": "https://docs.deno.com",
        "source": "https://github.com/denoland/deno",
        "description": "Deno is the next-generation JavaScript, TypeScript, and WebAssembly runtime with secure-by-default execution and built-in developer tools.",
    },
    "bun": {
        "version": "1.1.27",
        "size": "≈ 50 MB",
        "license": "MIT",
        "website": "https://bun.sh",
        "docs": "https://bun.sh/docs",
        "source": "https://github.com/oven-sh/bun",
        "description": "Bun is an all-in-one JavaScript runtime, bundler, test runner, and package manager designed for lightning-fast modern development.",
    },
    "solidity": {
        "version": "0.8.27",
        "size": "≈ 15 MB",
        "license": "GPL-3.0",
        "website": "https://soliditylang.org",
        "docs": "https://docs.soliditylang.org",
        "source": "https://github.com/ethereum/solidity",
        "description": "Solidity is an object-oriented, high-level language for implementing smart contracts on Ethereum and EVM-compatible blockchain platforms.",
    },

    # ── Compilers & Build Tools ──
    "gcc": {
        "version": "14.2.0",
        "size": "≈ 120 MB",
        "license": "GPL-3.0-or-later",
        "website": "https://gcc.gnu.org",
        "docs": "https://gcc.gnu.org/onlinedocs",
        "source": "https://gcc.gnu.org/git/gcc.git",
        "description": "The GNU Compiler Collection includes front ends for C, C++, Objective-C, Fortran, Ada, Go, and D, as well as libraries for these languages.",
    },
    "gpp": {
        "version": "14.2.0",
        "size": "≈ 125 MB",
        "license": "GPL-3.0-or-later",
        "website": "https://gcc.gnu.org",
        "docs": "https://gcc.gnu.org/onlinedocs",
        "source": "https://gcc.gnu.org/git/gcc.git",
        "description": "GNU C++ Compiler (g++) is part of the standard GCC distribution, optimizing modern C++20 and C++23 source code to highly efficient native machine binaries.",
    },
    "clang": {
        "version": "18.1.8",
        "size": "≈ 150 MB",
        "license": "Apache-2.0 with LLVM Exception",
        "website": "https://clang.llvm.org",
        "docs": "https://clang.llvm.org/docs",
        "source": "https://github.com/llvm/llvm-project",
        "description": "Clang is a C language family frontend for LLVM, delivering fast compilation, expressive diagnostics, and an extensible architecture.",
    },
    "cmake": {
        "version": "3.30.2",
        "size": "≈ 45 MB",
        "license": "BSD-3-Clause",
        "website": "https://cmake.org",
        "docs": "https://cmake.org/documentation",
        "source": "https://github.com/Kitware/CMake",
        "description": "CMake is the premier cross-platform build automation generator used to control the software compilation process using compiler-independent configuration files.",
    },
    "ninja": {
        "version": "1.12.1",
        "size": "≈ 2 MB",
        "license": "Apache-2.0",
        "website": "https://ninja-build.org",
        "docs": "https://ninja-build.org/manual.html",
        "source": "https://github.com/ninja-build/ninja",
        "description": "Ninja is a small build system with a focus on speed, specifically designed to run builds generated by CMake or Meson as fast as possible.",
    },

    # ── Package Managers ──
    "pip": {
        "version": "24.2",
        "size": "≈ 3 MB",
        "license": "MIT",
        "website": "https://pypi.org/project/pip",
        "docs": "https://pip.pypa.io",
        "source": "https://github.com/pypa/pip",
        "description": "The default package installer for Python, connecting directly to the Python Package Index (PyPI) to install and manage libraries.",
    },
    "npm": {
        "version": "10.8.2",
        "size": "≈ 8 MB",
        "license": "Artistic-2.0",
        "website": "https://www.npmjs.com",
        "docs": "https://docs.npmjs.com",
        "source": "https://github.com/npm/cli",
        "description": "npm is the default package manager for the JavaScript runtime environment Node.js and the world's largest software registry.",
    },
    "yarn": {
        "version": "1.22.22",
        "size": "≈ 2 MB",
        "license": "BSD-2-Clause",
        "website": "https://yarnpkg.com",
        "docs": "https://yarnpkg.com/getting-started",
        "source": "https://github.com/yarnpkg/yarn",
        "description": "Fast, reliable, and secure dependency management for JavaScript and Node.js projects.",
    },
    "pnpm": {
        "version": "9.9.0",
        "size": "≈ 6 MB",
        "license": "MIT",
        "website": "https://pnpm.io",
        "docs": "https://pnpm.io/motivation",
        "source": "https://github.com/pnpm/pnpm",
        "description": "Fast, disk space efficient package manager using hard links and symlinks to save gigabytes of space across projects.",
    },
    "cargo": {
        "version": "1.81.0",
        "size": "≈ 15 MB",
        "license": "MIT / Apache-2.0",
        "website": "https://doc.rust-lang.org/cargo",
        "docs": "https://doc.rust-lang.org/cargo",
        "source": "https://github.com/rust-lang/cargo",
        "description": "Cargo downloads your Rust package dependencies, compiles your code, runs tests, and uploads your packages to crates.io.",
    },
    "composer": {
        "version": "2.7.7",
        "size": "≈ 3 MB",
        "license": "MIT",
        "website": "https://getcomposer.org",
        "docs": "https://getcomposer.org/doc",
        "source": "https://github.com/composer/composer",
        "description": "Composer is a tool for dependency management in PHP, declaring and installing the libraries your project depends on.",
    },
    "uv": {
        "version": "0.4.7",
        "size": "≈ 18 MB",
        "license": "MIT / Apache-2.0",
        "website": "https://astral.sh/uv",
        "docs": "https://docs.astral.sh/uv",
        "source": "https://github.com/astral-sh/uv",
        "description": "An extremely fast Python package and project manager, written in Rust, designed as a drop-in replacement for pip and virtualenv.",
    },

    # ── Databases ──
    "postgres": {
        "version": "16.4",
        "size": "≈ 280 MB",
        "license": "PostgreSQL License",
        "website": "https://www.postgresql.org",
        "docs": "https://www.postgresql.org/docs",
        "source": "https://github.com/postgres/postgres",
        "description": "PostgreSQL is a powerful, open source object-relational database system with over 35 years of active development and proven architecture.",
    },
    "mysql": {
        "version": "8.4.2 (LTS)",
        "size": "≈ 320 MB",
        "license": "GPL-2.0",
        "website": "https://www.mysql.com",
        "docs": "https://dev.mysql.com/doc",
        "source": "https://github.com/mysql/mysql-server",
        "description": "MySQL is the world's most popular open source relational database, powering countless modern web applications and enterprises.",
    },
    "redis": {
        "version": "7.4.0",
        "size": "≈ 15 MB",
        "license": "RSALv2 / SSPLv1",
        "website": "https://redis.io",
        "docs": "https://redis.io/docs",
        "source": "https://github.com/redis/redis",
        "description": "Redis is the open source, in-memory data store used by millions of developers as a database, cache, streaming engine, and message broker.",
    },
    "mongodb": {
        "version": "7.0.12",
        "size": "≈ 400 MB",
        "license": "SSPL",
        "website": "https://www.mongodb.com",
        "docs": "https://www.mongodb.com/docs",
        "source": "https://github.com/mongodb/mongo",
        "description": "MongoDB is a source-available cross-platform document-oriented database program, using JSON-like documents with optional schemas.",
    },
    "sqlite": {
        "version": "3.46.1",
        "size": "≈ 3 MB",
        "license": "Public Domain",
        "website": "https://www.sqlite.org",
        "docs": "https://www.sqlite.org/docs.html",
        "source": "https://github.com/sqlite/sqlite",
        "description": "SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured SQL database engine.",
    },

    # ── DevOps & Tools ──
    "docker": {
        "version": "27.1.1",
        "size": "≈ 550 MB",
        "license": "Apache-2.0",
        "website": "https://www.docker.com",
        "docs": "https://docs.docker.com",
        "source": "https://github.com/docker",
        "description": "Docker simplifies and accelerates development workflows with integrated containerization, networking, and volume management.",
    },
    "git": {
        "version": "2.46.0",
        "size": "≈ 50 MB",
        "license": "GPL-2.0",
        "website": "https://git-scm.com",
        "docs": "https://git-scm.com/doc",
        "source": "https://github.com/git/git",
        "description": "Git is a free and open source distributed version control system designed to handle everything from small to very large projects with speed and efficiency.",
    },
    "vscode": {
        "version": "1.92.2",
        "size": "≈ 95 MB",
        "license": "MIT",
        "website": "https://code.visualstudio.com",
        "docs": "https://code.visualstudio.com/docs",
        "source": "https://github.com/microsoft/vscode",
        "description": "Visual Studio Code is a code editor redefined and optimized for building and debugging modern web and cloud applications.",
    },
    "flutter": {
        "version": "3.24.2",
        "size": "≈ 650 MB",
        "license": "BSD-3-Clause",
        "website": "https://flutter.dev",
        "docs": "https://docs.flutter.dev",
        "source": "https://github.com/flutter/flutter",
        "description": "Flutter transforms the frontend development process, allowing you to build, test, and deploy beautiful mobile, web, desktop, and embedded apps from a single codebase.",
    },
}


def get_tool_metadata(tool: dict) -> dict:
    """Return complete metadata for any tool, with comprehensive fallbacks."""
    key = tool.get("key", "").lower()
    name = tool.get("name", key.capitalize())
    cat = tool.get("category", "DevOps & Tools")
    desc = tool.get("description", "")

    # Look up in curated dict
    if key in TOOL_META:
        return TOOL_META[key]

    # Category-based intelligent defaults
    size_defaults = {
        "Languages": "≈ 60 MB",
        "Compilers": "≈ 90 MB",
        "Package Managers": "≈ 15 MB",
        "Databases": "≈ 250 MB",
        "IDEs & Editors": "≈ 120 MB",
        "Mobile Development": "≈ 500 MB",
        "Cloud CLIs": "≈ 45 MB",
        "DevOps & Tools": "≈ 35 MB",
        "AI / Data Science": "≈ 450 MB",
    }
    est_size = size_defaults.get(cat, "≈ 40 MB")

    clean_key = key.replace("_", "-")
    website = f"https://github.com/search?q={clean_key}"
    docs = f"https://devdocs.io/{clean_key}"
    source = f"https://github.com/{clean_key}"

    return {
        "version": "latest (stable)",
        "size": est_size,
        "license": "Open Source",
        "website": website,
        "docs": docs,
        "source": source,
        "description": f"{name} is an essential tool in {cat}. {desc}. It can be seamlessly installed, verified, and configured with DevInstaller.",
    }


class _MetadataRow(QWidget):
    """A single icon + label + value row in the metadata grid."""
    def __init__(self, icon_file: str, label: str, value_widget: QWidget, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_path = ICONS_DIR / icon_file
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                icon_lbl.setPixmap(pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(label)
        name_lbl.setFixedWidth(86)
        name_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(name_lbl)

        layout.addWidget(value_widget, stretch=1)


class _LinkRow(QWidget):
    """A clickable link row with icon."""
    def __init__(self, icon_file: str, text: str, parent=None):
        super().__init__(parent)
        self._url = ""
        self._default_text = text
        self.setStyleSheet("background: transparent; border: none;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_path = ICONS_DIR / icon_file
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                icon_lbl.setPixmap(pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_lbl)

        self.text_lbl = QLabel(text)
        self.text_lbl.setStyleSheet("""
            QLabel {
                color: #38bdf8;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
            QLabel:hover {
                color: #7dd3fc;
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.text_lbl, stretch=1)

    def set_url(self, url: str, label: str = None):
        self._url = url.strip() if url else ""
        if label:
            self.text_lbl.setText(label)
        else:
            self.text_lbl.setText(self._default_text)
        self.setToolTip(self._url if self._url else "")
        self.setVisible(bool(self._url))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._url:
            QDesktopServices.openUrl(QUrl(self._url))
        super().mousePressEvent(event)


def _value_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #e2e8f0; font-size: 12px; background: transparent; border: none;")
    return lbl


class DetailPanel(QWidget):
    """Right-side detail panel showing selected package info — styled as a floating card."""

    install_requested = Signal(dict)
    uninstall_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("background: transparent; border: none;")

        self._current_tool = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(2, 6, 12, 6)
        outer_layout.setSpacing(0)

        # Floating Card Container
        self.card = QWidget()
        self.card.setObjectName("detailCard")
        self.card.setStyleSheet("""
            QWidget#detailCard {
                background-color: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.28);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(10)

        # ── Header: Icon + (Name, Badges, Subtitle) ──
        header = QWidget()
        header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.tool_icon = QLabel()
        self.tool_icon.setFixedSize(44, 44)
        self.tool_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tool_icon.setStyleSheet("background: transparent; border: none;")
        py_icon_path = ICONS_DIR / "python.png"
        if py_icon_path.exists():
            pix = QPixmap(str(py_icon_path))
            if not pix.isNull():
                self.tool_icon.setPixmap(pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        header_layout.addWidget(self.tool_icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        # Row 1: Tool Name
        self.tool_name = QLabel("Python 3.12")
        self.tool_name.setWordWrap(True)
        self.tool_name.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        title_col.addWidget(self.tool_name)

        # Row 2: Badges row (Installed, Popular) — dedicated row so badges NEVER truncate
        badges_row = QHBoxLayout()
        badges_row.setContentsMargins(0, 0, 0, 0)
        badges_row.setSpacing(6)

        self.installed_badge = QLabel("✓ Installed")
        self.installed_badge.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 9px;
            padding: 2px 8px;
            font-size: 10.5px;
            font-weight: 700;
        """)
        self.installed_badge.setVisible(False)
        badges_row.addWidget(self.installed_badge)

        self.popular_badge = QLabel("Popular")
        self.popular_badge.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border-radius: 9px;
            padding: 2px 8px;
            font-size: 10.5px;
            font-weight: 600;
            border: none;
        """)
        badges_row.addWidget(self.popular_badge)
        badges_row.addStretch()
        title_col.addLayout(badges_row)

        # Row 3: Subtitle
        self.tool_subtitle = QLabel("General-purpose programming language")
        self.tool_subtitle.setWordWrap(True)
        self.tool_subtitle.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent; border: none;")
        title_col.addWidget(self.tool_subtitle)

        header_layout.addLayout(title_col, stretch=1)
        self.content_layout.addWidget(header)

        # ── Description ──
        self.description = QLabel(
            "Python is a high-level, interpreted programming language known for its "
            "simplicity and wide range of applications in web development, data science, "
            "automation, and more."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
            line-height: 18px;
            background: transparent;
            border: none;
            padding-top: 2px;
        """)
        self.content_layout.addWidget(self.description)

        # ── Metadata grid ──
        self.meta_container = QWidget()
        self.meta_container.setStyleSheet("background: transparent; border: none;")
        self.meta_layout = QVBoxLayout(self.meta_container)
        self.meta_layout.setContentsMargins(0, 6, 0, 6)
        self.meta_layout.setSpacing(0)

        self.pkg_name_value = _value_label("python")
        self.meta_layout.addWidget(_MetadataRow("meta_pkg.png", "Package name", self.pkg_name_value))

        self.version_value = _value_label("3.12.5")
        self.meta_layout.addWidget(_MetadataRow("meta_gear.png", "Version", self.version_value))

        # Category compact pill
        cat_box = QWidget()
        cat_box.setStyleSheet("background: transparent; border: none;")
        cat_box_layout = QHBoxLayout(cat_box)
        cat_box_layout.setContentsMargins(0, 0, 0, 0)
        cat_box_layout.setSpacing(0)
        self.category_badge = QLabel("Languages")
        self.category_badge.setStyleSheet("""
            color: #818cf8;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0;
        """)
        cat_box_layout.addWidget(self.category_badge)
        cat_box_layout.addStretch()
        self.meta_layout.addWidget(_MetadataRow("meta_tag.png", "Category", cat_box))

        self.size_value = _value_label("≈ 25 MB")
        self.meta_layout.addWidget(_MetadataRow("meta_disk.png", "Size", self.size_value))

        self.license_value = _value_label("PSF License")
        self.license_value.setWordWrap(True)
        self.meta_layout.addWidget(_MetadataRow("meta_doc.png", "License", self.license_value))

        self.content_layout.addWidget(self.meta_container)

        # ── Links ──
        self.links_container = QWidget()
        self.links_container.setStyleSheet("background: transparent; border: none;")
        self.links_layout = QVBoxLayout(self.links_container)
        self.links_layout.setContentsMargins(0, 6, 0, 6)
        self.links_layout.setSpacing(0)

        self.link_website = _LinkRow("link_globe.png", "Official Website")
        self.link_website.set_url("https://www.python.org")
        self.links_layout.addWidget(self.link_website)

        self.link_docs = _LinkRow("link_book.png", "Documentation")
        self.link_docs.set_url("https://docs.python.org/3")
        self.links_layout.addWidget(self.link_docs)

        self.link_source = _LinkRow("link_code.png", "Source Code")
        self.link_source.set_url("https://github.com/python/cpython")
        self.links_layout.addWidget(self.link_source)

        self.content_layout.addWidget(self.links_container)

        self.content_layout.addStretch()

        self.scroll.setWidget(self.content)
        card_layout.addWidget(self.scroll, stretch=1)

        # ── Pinned Bottom Actions Container (Never Cut Off) ──
        self.action_container = QWidget()
        self.action_container.setObjectName("detailActions")
        self.action_container.setStyleSheet("""
            QWidget#detailActions {
                background-color: rgba(10, 15, 28, 0.75);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }
        """)
        self.actions_layout = QVBoxLayout(self.action_container)
        self.actions_layout.setContentsMargins(14, 10, 14, 12)
        self.actions_layout.setSpacing(6)

        self.install_btn = ActionButton("⬇  Install Python 3.12", "primary")
        self.install_btn.setFixedHeight(40)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #3b82f6);
                color: #ffffff;
                border: none;
                border-radius: 9px;
                padding: 6px 16px;
                font-size: 13.5px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #60a5fa);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1d4ed8, stop:1 #2563eb);
            }
        """)
        self.install_btn.clicked.connect(self._on_install)
        self.actions_layout.addWidget(self.install_btn)

        self.uninstall_btn = ActionButton("🗑️  Uninstall & Wipe Clean", "danger")
        self.uninstall_btn.setFixedHeight(36)
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 12.5px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.28);
                border-color: #ef4444;
                color: #fecaca;
            }
            QPushButton:pressed {
                background-color: rgba(220, 38, 38, 0.45);
            }
        """)
        self.uninstall_btn.clicked.connect(self._on_uninstall)
        self.uninstall_btn.setVisible(False)
        self.actions_layout.addWidget(self.uninstall_btn)

        card_layout.addWidget(self.action_container)
        outer_layout.addWidget(self.card)

    def set_tool(self, tool: dict, is_installed: bool = None):
        """Populate the detail panel with tool information."""
        self._current_tool = tool
        key = tool.get("key", "")
        name = "C++" if key == "gpp" else tool.get("name", "Unknown")
        desc = tool.get("description", "")
        cat = tool.get("category", "Other")

        # 1. High-DPI icon via icon_provider
        pix = get_tool_icon_pixmap(tool, size=46)
        if pix and not pix.isNull():
            self.tool_icon.setPixmap(pix)
            self.tool_icon.setText("")
        else:
            self.tool_icon.setPixmap(QPixmap())
            self.tool_icon.setText("📦")

        self.tool_name.setText(name)
        self.tool_subtitle.setText(desc)

        popular_keys = {
            "python", "python311", "nodejs", "node", "rust", "go", "docker", "git",
            "vscode", "typescript", "java", "csharp", "flutter", "postgres"
        }
        self.popular_badge.setVisible(key in popular_keys)

        # 2. Rich Metadata & Clickable Links
        meta = get_tool_metadata(tool)
        self.description.setText(meta.get("description", desc))

        detect_cmd = tool.get("detect_cmd", "")
        cmd_name = detect_cmd.split("--version")[0].strip().split()[-1] if detect_cmd else key
        self.pkg_name_value.setText(cmd_name or key)
        self.version_value.setText(meta.get("version", "latest"))

        cat_fg, _ = CATEGORY_BADGE_COLORS.get(cat, ("#94a3b8", "transparent"))
        self.category_badge.setText(cat)
        self.category_badge.setStyleSheet(f"""
            color: {cat_fg};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0;
        """)

        self.size_value.setText(meta.get("size", "—"))
        self.license_value.setText(meta.get("license", "—"))

        # Update URLs for clickable links
        self.link_website.set_url(meta.get("website", ""))
        self.link_docs.set_url(meta.get("docs", ""))
        self.link_source.set_url(meta.get("source", ""))

        if is_installed is not None:
            self.set_installed_state(is_installed)
        else:
            self.set_installed_state(False)

    def set_installed_state(self, is_installed: bool):
        """Update installed badge, install button, and uninstall button."""
        self.installed_badge.setVisible(bool(is_installed))
        if not self._current_tool:
            self.uninstall_btn.setVisible(False)
            return

        key = self._current_tool.get("key", "")
        name = "C++" if key == "gpp" else self._current_tool.get("name", "Unknown")

        if is_installed:
            self.uninstall_btn.setVisible(True)
            if key == "oracle_db_xe":
                self.uninstall_btn.setText("🗑️  Uninstall & Wipe Clean")
            elif key == "oracle_sql_developer":
                self.uninstall_btn.setText("🗑️  Uninstall & Clean")
            else:
                self.uninstall_btn.setText("🗑️  Uninstall")
            self.install_btn.setText(f"🔄  Reinstall {name}")
        else:
            self.uninstall_btn.setVisible(False)
            self.install_btn.setText(f"⬇  Install {name}")

    def _on_install(self):
        if self._current_tool:
            self.install_requested.emit(self._current_tool)

    def _on_uninstall(self):
        if self._current_tool:
            self.uninstall_requested.emit(self._current_tool)

